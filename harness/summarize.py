"""Agregace výsledků stress testu -> markdown souhrn fáze / celkový."""
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"


def load(name):
    p = RESULTS / name
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").strip().split("\n") if l]


def pct(xs, q):
    if not xs:
        return 0
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def main(phase_filter=None):
    iters = load("iterations.jsonl")
    ops = load("ops.jsonl")
    if phase_filter:
        iters = [r for r in iters if r.get("phase") == phase_filter]
        ops = [o for o in ops if o.get("phase") == phase_filter]
    n = len(iters)
    out = []
    title = "fáze %s" % phase_filter if phase_filter else "CELKEM"
    out.append("## Souhrn — %s (n=%d iterací)" % (title, n))
    oc = Counter(r.get("outcome") for r in iters)
    out.append("- outcome: %s" % dict(oc))
    crashes = oc.get("crash", 0)
    out.append("- **C1 pády: %d**" % crashes)
    judged = [r for r in iters if r.get("outcome") != "crash"]
    matches = sum(1 for r in judged if r.get("match"))
    out.append("- **C2 shoda s očekáváním: %d/%d (%.1f %%)**" % (matches, len(judged), 100.0 * matches / max(1, len(judged))))
    mism = [r for r in judged if not r.get("match")]
    for r in mism[:10]:
        out.append("  - mismatch iter %s: %s≠%s (perturb=%s, typ=%s)" % (r["iter"], r.get("outcome"), r.get("expected"), r.get("perturb"), r.get("type")))
    escapes = [r for r in iters if r.get("gate_escape")]
    out.append("- **C3 gate-escapes: %d**" % len(escapes))
    overblock = [r for r in iters if r.get("outcome") == "needs_review" and r.get("perturb") == "none"]
    out.append("- gate-overblock (čistý vstup v inboxu): %d" % len(overblock))
    fm_bad = [r for r in iters if r.get("fm_complete") is False]
    out.append("- nekompletní frontmatter u ok výstupů: %d" % len(fm_bad))
    inv = [r for r in iters if r.get("perturb") == "invented_field" and r.get("outcome") == "ok"]
    inv_ok = sum(1 for r in inv if r.get("invented_stripped"))
    out.append("- halucinovaná pole odstraněna: %d/%d" % (inv_ok, len(inv)))
    xl = [r for r in iters if r.get("bucket") == "XL" and r.get("outcome") == "ok"]
    out.append("- XL summarize pre-pass označen: %d/%d" % (sum(1 for r in xl if r.get("summarized")), len(xl)))
    nr = [r for r in iters if r.get("outcome") == "needs_review"]
    out.append("- **C8** needs_review s důvodem: %d/%d; routing do inboxu ok: %d/%d"
               % (sum(1 for r in nr if r.get("has_reason")), len(nr),
                  sum(1 for r in nr if r.get("routing_ok")), len(nr)))
    ext = [r["extract_ms"] for r in iters if r.get("extract_ms") is not None]
    if ext:
        out.append("- **C6** extract ms: p50=%d p95=%d max=%d (n=%d)" % (pct(ext, .5), pct(ext, .95), max(ext), len(ext)))
    # škálování: extract_ms vs. velikost KB
    bydocs = defaultdict(list)
    for r in iters:
        if r.get("extract_ms") is not None and r.get("kb_docs"):
            bydocs[r["kb_docs"] // 50 * 50].append(r["extract_ms"])
    if bydocs:
        out.append("- škálování extract p50 dle velikosti KB: " +
                   ", ".join("%d+ dokumentů→%d ms" % (k, pct(v, .5)) for k, v in sorted(bydocs.items())))
    il = [o for o in ops if o.get("op") == "index+lint"]
    if il:
        out.append("- **C6** plný lint ms: p50=%d max=%d; index ms: p50=%d max=%d (n=%d kontrol)"
                   % (pct([o["lint_ms"] for o in il], .5), max(o["lint_ms"] for o in il),
                      pct([o["index_ms"] for o in il], .5), max(o["index_ms"] for o in il), len(il)))
        bad = [o for o in il if o.get("lint_errors")]
        out.append("- lint po index regeneraci: %d/%d kontrol s 0 errors%s"
                   % (len(il) - len(bad), len(il), "" if not bad else " — VADNÉ: %s" % [o["iter"] for o in bad]))
    rt = [o for o in ops if o.get("op") == "retract" and not o.get("skipped")]
    if rt:
        cascade_ok = sum(1 for o in rt if o.get("cascade_ok"))
        kb009_ok = sum(1 for o in rt if (not o.get("kb009_expected")) or o.get("kb009_fired_before_index"))
        clean_after = sum(1 for o in rt if o.get("errors_after_index") == 0)
        out.append("- **C4** retrakce: %d ops; kaskáda ok %d/%d; KB009 dle očekávání %d/%d; čisto po indexu %d/%d"
                   % (len(rt), cascade_ok, len(rt), kb009_ok, len(rt), clean_after, len(rt)))
    det = [o for o in ops if o.get("op") == "determinism"]
    if det:
        out.append("- **C5** determinismus indexu: %d/%d identických" % (sum(1 for o in det if o.get("identical")), len(det)))
    # fáze D
    real = [r for r in iters if r.get("field_scores")]
    if real:
        out.append("### Reálné LLM (fáze D, n=%d)" % len(real))
        out.append("- cena celkem: $%.3f; tokens_in p50=%s" % (
            sum(r.get("cost_usd") or 0 for r in real), pct([r.get("tokens_in") or 0 for r in real], .5)))
        agg = defaultdict(list)
        for r in real:
            for k, v in r["field_scores"].items():
                agg[k].append(v if isinstance(v, bool) else v.get("recall"))
        for k in sorted(agg):
            vals = agg[k]
            ok = sum(1 for v in vals if v is True) + sum(v for v in vals if isinstance(v, float))
            out.append("- pole `%s`: %.0f %% (n=%d)" % (k, 100.0 * ok / len(vals), len(vals)))
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
