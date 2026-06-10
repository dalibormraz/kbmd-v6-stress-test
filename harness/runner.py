"""Stress runner: vykonává iterace dle generator.plan, loguje asserty a operace.

Spouštět pythonem z venv, kde je nainstalované kbmd 6.1.0:
  .../kbmd-cli/.venv/bin/python harness/runner.py --from 1 --to 120 --kb kb
Fáze D: --provider claude-cli --model haiku
"""
import argparse
import json
import random
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import generator  # noqa: E402

from kbmd.config import KB  # noqa: E402
from kbmd.extract import run_extract  # noqa: E402
from kbmd.indexer import build_index, write_index  # noqa: E402
from kbmd.initcmd import run_ingest  # noqa: E402
from kbmd.lifecycle import promote, retract_raw  # noqa: E402
from kbmd.lint import run_lint  # noqa: E402
from kbmd.providers import MockProvider, ClaudeCLIProvider  # noqa: E402
from kbmd.templates import list_templates  # noqa: E402
from kbmd import fm  # noqa: E402

RESULTS = HERE.parent / "results"
TMP = HERE / "tmp"


def jappend(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def norm(s: str) -> set:
    import re
    return set(w for w in re.findall(r"[a-zá-ž0-9]+", str(s).lower()) if len(w) > 2)


def fuzzy(a, b) -> bool:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return a == b
    return len(na & nb) / max(1, min(len(na), len(nb))) >= 0.5


def score_fields(meta: dict, gt: dict) -> dict:
    """Fáze D: srovnání extrahovaných polí s GT (metoda popsaná v RESULTS)."""
    out = {}
    for k, v in gt.items():
        got = meta.get(k)
        if v in (None, [], ""):
            continue
        if isinstance(v, str):
            out[k] = bool(got) and (got == v if k in ("date", "sentiment", "priority") else fuzzy(got, v))
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            keyf = "what" if "what" in v[0] else next(iter(v[0]))
            hits = 0
            for item in v:
                if any(isinstance(g, dict) and fuzzy(g.get(keyf, ""), item.get(keyf, "")) for g in (got or [])):
                    hits += 1
            out[k] = {"recall": hits / len(v), "gt_n": len(v), "out_n": len(got or [])}
        elif isinstance(v, list):
            hits = sum(1 for item in v if any(fuzzy(g, item) for g in (got or [])))
            out[k] = {"recall": hits / len(v), "gt_n": len(v), "out_n": len(got or [])}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, required=True)
    ap.add_argument("--to", dest="end", type=int, required=True)
    ap.add_argument("--kb", default="kb")
    ap.add_argument("--provider", default="mock", choices=["mock", "claude-cli"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--backfill", action="store_true",
                    help="na startu zpětně extrahuj raw vstupy, které dřív neměly šablonu")
    ap.add_argument("--phase", default="?")
    args = ap.parse_args()

    kb = KB(Path(args.kb))
    TMP.mkdir(exist_ok=True)
    it_log = RESULTS / "iterations.jsonl"
    ops_log = RESULTS / "ops.jsonl"
    no_template_counts = {}
    crashes = 0

    def full_lint_ms():
        t = time.perf_counter()
        rep = run_lint(kb, min_level="error")
        return rep, int((time.perf_counter() - t) * 1000)

    if args.backfill:
        tpls = set(list_templates(kb))
        backfilled = 0
        for raw in kb.raw_files():
            meta = kb.read_meta(raw)
            if meta.get("processed") or meta.get("retracted"):
                continue
            typ = meta.get("stress_type")
            if typ in tpls:
                gt = meta.get("stress_gt")
                res = run_extract(kb, kb.rel(raw), typ, MockProvider(responses=[gt]))
                backfilled += 1
                jappend(ops_log, {"op": "backfill", "raw": kb.rel(raw), "outcome": res.outcome,
                                  "phase": args.phase})
        print("backfill: %d vstupů z fronty zpracováno" % backfilled)

    for i in range(args.start, args.end + 1):
        p = generator.plan(i)
        rec = {"iter": i, "phase": args.phase, **{k: p.get(k) for k in
               ("type", "bucket", "lang", "perturb", "segment", "adversarial")}}
        t_iter = time.perf_counter()
        try:
            gt = generator.make_gt(p)
            raw_text = generator.build_raw(p, gt)
            src = TMP / ("iter-%04d-%s.md" % (i, p["type"]))
            src.write_text(raw_text, encoding="utf-8")
            raw_path = run_ingest(kb, src, bucket="transcripts" if p["type"] == "meeting" else "notes")
            rmeta = kb.read_meta(raw_path)
            rmeta["stress_type"] = p["type"]
            rmeta["stress_gt"] = gt
            kb.write_meta(raw_path, rmeta)

            tpls = set(list_templates(kb))
            if p["type"] not in tpls:
                no_template_counts[p["type"]] = no_template_counts.get(p["type"], 0) + 1
                rec.update(outcome="no_template", expected="no_template", match=True)
                jappend(it_log, rec)
                _scheduled_ops(kb, i, args.phase, ops_log)   # S-03: ops běží vždy
                continue

            if args.provider == "mock":
                responses, expected = generator.mock_responses(p, gt)
                provider = MockProvider(responses=responses)
            else:
                provider = ClaudeCLIProvider(model=args.model)
                expected = "ok"

            t0 = time.perf_counter()
            res = run_extract(kb, kb.rel(raw_path), p["type"], provider)
            dur = int((time.perf_counter() - t0) * 1000)
            rec.update(outcome=res.outcome, expected=expected, match=res.outcome == expected,
                       attempts=res.attempts, extract_ms=dur, lint_errors=res.findings_errors,
                       kb_docs=len(kb.distilled_docs()))

            # A3/A4/A6 asserty
            if res.outcome == "ok":
                rel = kb.rel(res.output_path)
                rec["output"] = rel
                rec["routing_ok"] = not rel.startswith("wiki/inbox")
                rec["gate_escape"] = res.findings_errors > 0
                meta, _ = fm.read_file(res.output_path)
                rec["fm_complete"] = all(meta.get(k) for k in
                                         ("template", "template_version", "status", "source",
                                          "extracted_at", "valid_from"))
                if p["perturb"] == "invented_field":
                    rec["invented_stripped"] = "halucinovane_pole" not in meta
                if p["bucket"] == "XL":
                    rec["summarized"] = bool(res.trace.get("kbmd.summarized"))
                if args.provider == "claude-cli":
                    rec["field_scores"] = score_fields(meta, gt)
                    rec["cost_usd"] = res.trace.get("cost_usd")
                    rec["tokens_in"] = res.trace.get("gen_ai.usage.input_tokens")
                # 50% promote
                if random.Random(i).random() < 0.5:
                    try:
                        promote(kb, rel, to="published")
                        rec["promoted"] = True
                    except Exception as e:
                        rec["promoted"] = False
                        rec["promote_error"] = str(e)[:200]
            elif res.outcome == "needs_review":
                rel = kb.rel(res.output_path)
                rec["output"] = rel
                rec["routing_ok"] = rel.startswith("wiki/inbox")
                meta, _ = fm.read_file(res.output_path)
                rec["has_reason"] = bool(meta.get("needs_review_reason"))
            jappend(it_log, rec)
            _scheduled_ops(kb, i, args.phase, ops_log)
        except Exception:
            crashes += 1
            rec.update(outcome="crash", match=False, traceback=traceback.format_exc()[-1500:])
            jappend(it_log, rec)
        rec["iter_ms"] = int((time.perf_counter() - t_iter) * 1000)

    print("Fáze %s hotová (%d–%d). Pády: %d. No-template fronta: %s"
          % (args.phase, args.start, args.end, crashes, no_template_counts))
    for typ, n in sorted(no_template_counts.items()):
        if n >= 3:
            print("TEMPLATE NEEDED: %s (%d vzorků) — pravidlo 3× splněno" % (typ, n))
    return 0


def _scheduled_ops(kb: KB, i: int, phase: str, ops_log: Path) -> None:
    """Rozvrh operací dle scénáře §6 — běží nezávisle na outcome iterace (S-03)."""
    if i % 20 == 0:
        t = time.perf_counter()
        write_index(kb)
        idx_ms = int((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        rep = run_lint(kb, min_level="error")
        lint_ms = int((time.perf_counter() - t) * 1000)
        jappend(ops_log, {"op": "index+lint", "iter": i, "phase": phase,
                          "index_ms": idx_ms, "lint_ms": lint_ms,
                          "lint_errors": len(rep.errors),
                          "errors_sample": [f.format_text() for f in rep.errors[:5]],
                          "kb_docs": len(kb.distilled_docs())})
    if i % 50 == 0:
        _retract_op(kb, i, phase, ops_log)
    if i % 100 == 0:
        a, b = build_index(kb), build_index(kb)
        jappend(ops_log, {"op": "determinism", "iter": i, "phase": phase,
                          "identical": a == b})


def _retract_op(kb: KB, i: int, phase: str, ops_log: Path) -> None:
    r = random.Random(i * 31 + 7)
    candidates = []
    for raw in kb.raw_files():
        m = kb.read_meta(raw)
        if m.get("extractions") and not m.get("retracted"):
            candidates.append(kb.rel(raw))
    if not candidates:
        jappend(ops_log, {"op": "retract", "iter": i, "phase": phase, "skipped": "no candidates"})
        return
    target = r.choice(candidates)
    deps_published_in_index = []
    idx = kb.index_path.read_text(encoding="utf-8") if kb.index_path.is_file() else ""
    msg, quarantined = retract_raw(kb, target, reason="stress: retraction op @iter %d" % i)
    all_quarantined = True
    for q in quarantined:
        meta, _ = fm.read_file(kb.root / q)
        if meta.get("status") != "quarantined":
            all_quarantined = False
        if q in idx:
            deps_published_in_index.append(q)
    rep_before = run_lint(kb, min_level="error")
    kb009_before = any(f.rule_id == "KB009" for f in rep_before.findings)
    write_index(kb)
    rep_after = run_lint(kb, min_level="error")
    jappend(ops_log, {
        "op": "retract", "iter": i, "phase": phase, "raw": target,
        "quarantined_n": len(quarantined), "cascade_ok": all_quarantined,
        "kb009_expected": bool(deps_published_in_index),
        "kb009_fired_before_index": kb009_before,
        "errors_after_index": len(rep_after.errors),
        "errors_sample": [f.format_text() for f in rep_after.errors[:5]],
    })


if __name__ == "__main__":
    sys.exit(main())
