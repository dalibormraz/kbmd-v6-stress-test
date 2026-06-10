"""Deterministický generátor iterací stress testu (seed 64001).

plan(i) -> profil iterace; build_input(plan) -> (raw_text, ground_truth).
Čistá funkce seedu a čísla iterace — celý 400-iter plán je reprodukovatelný.
"""
import random
from typing import Dict, Any, List, Tuple

SEED = 64001

TYPES = ["meeting", "decision", "spec", "client_feedback", "risk_review", "interview"]
TYPE_W = [40, 15, 15, 10, 10, 10]
BASE_TEMPLATES = {"meeting", "decision", "spec"}

BUCKETS = ["XS", "S", "M", "L"]
BUCKET_W = [25, 35, 30, 10]
BUCKET_CHARS = {"XS": 300, "S": 1500, "M": 6000, "L": 30000, "XL": 110000}

PERTURB = ["none", "drop_required", "bad_enum", "bad_date", "wrong_type",
           "invented_field", "uncorrectable_missing", "null_owner_action", "malformed_json"]
PERTURB_W = [55, 8, 6, 5, 6, 5, 5, 3, 4]  # XL/none se vynucuje zvlášť (3 % iterací)

NAMES = ["Jana Dvořáková", "Petr Novák", "Klára Svobodová", "Michal Beneš", "Eva Horká",
         "Tomáš Malý", "Lucie Veselá", "Ondřej Král", "Marie Tichá", "Jakub Polák"]
PROJECTS = ["e-shop s keramikou", "rezervační systém", "interní wiki", "mobilní aplikace",
            "datový sklad", "kampaň podzim", "redesign webu", "fakturační modul"]
TOPICS = ["migrace dat", "platební brána", "harmonogram", "rozpočet", "grafika",
          "doprava zboží", "testování", "smlouva", "obsah webu", "školení týmu"]
SMALLTALK = [
    "Mimochodem, o víkendu bylo krásně, byli jsme na kole.",
    "Než začneme — slyšíte mě všichni dobře? Výborně.",
    "Káva dnes nějak nefunguje, omlouvám se za zívání.",
    "To počasí je letos fakt divoké, co?",
    "Chvilku jsem řešil parkování, promiňte za zpoždění.",
]
NOISE_PARA = ("Pak jsme se chvíli bavili obecně o trhu a trendech, nic konkrétního k projektu. "
              "Padlo pár historek z jiných zakázek, které sem nepatří. ")

ADVERSARIAL = ["empty", "xl_huge", "unicode_chaos", "frontmatter_bomb", "long_lines", "emoji_names"]

REAL_LLM_PLAN = (["meeting"] * 4 + ["decision"] * 3 + ["spec"] * 3
                 + ["client_feedback"] * 3 + ["risk_review"] * 3)  # 16 ks, iterace 385–400


def _rng(i: int) -> random.Random:
    return random.Random(SEED * 100003 + i)


def plan(i: int) -> Dict[str, Any]:
    r = _rng(i)
    p: Dict[str, Any] = {"iter": i}
    if 385 <= i <= 400:                       # fáze D — reálné LLM
        p.update(type=REAL_LLM_PLAN[i - 385], bucket="S", lang="cs",
                 perturb="none", segment="real")
        return p
    if 361 <= i <= 384:                       # adversarial blok
        p.update(type=r.choice(["meeting", "decision", "spec"]),
                 adversarial=ADVERSARIAL[(i - 361) % len(ADVERSARIAL)],
                 bucket="S", lang="cs", perturb="none", segment="adversarial")
        if p["adversarial"] == "xl_huge":
            p["bucket"] = "XL"
        return p
    typ = r.choices(TYPES, weights=TYPE_W)[0]
    perturb = r.choices(PERTURB, weights=PERTURB_W)[0]
    if perturb == "null_owner_action" and typ != "meeting":
        perturb = "drop_required"
    bucket = r.choices(BUCKETS, weights=BUCKET_W)[0]
    if r.random() < 0.03:
        bucket, perturb = "XL", "none"        # summarize trigger
    p.update(type=typ, bucket=bucket, lang="en" if r.random() < 0.2 else "cs",
             perturb=perturb, segment="standard")
    return p


# ------------------------------------------------------------- ground truth

def _date(r: random.Random) -> str:
    return "2026-%02d-%02d" % (r.randint(1, 6), r.randint(1, 28))


def make_gt(p: Dict[str, Any]) -> Dict[str, Any]:
    r = _rng(p["iter"] + 7_000_000)
    typ = p["type"]
    proj = r.choice(PROJECTS)
    topic = r.choice(TOPICS)
    ppl = r.sample(NAMES, k=r.randint(2, 4))
    d = _date(r)
    if typ == "meeting":
        return {
            "title": "Schůzka: %s — %s" % (proj, topic),
            "date": d, "participants": ppl,
            "summary": "Řešili jsme %s pro projekt %s; shoda na dalším postupu a rozdělení úkolů." % (topic, proj),
            "decisions": [{"what": "Pro %s použijeme variantu %s" % (topic, r.choice("ABC")),
                           "why": "nejlepší poměr cena/termín", "owner": ppl[0]}][: r.randint(0, 2) + (p["perturb"] != "malformed_json")],
            "actions": [{"what": "Připravit podklady k %s" % topic, "owner": ppl[1], "due": "do konce týdne"},
                        {"what": "Ověřit kapacitu dodavatele", "owner": ppl[0], "due": None}][: r.randint(1, 2)],
            "open_questions": ["Kdo schválí rozpočet za %s?" % topic][: r.randint(0, 1)],
            "risks": ["Možné zpoždění kvůli dovoleným"][: r.randint(0, 1)],
        }
    if typ == "decision":
        return {
            "title": "Rozhodnutí: %s pro %s" % (topic, proj),
            "date": d,
            "what": "Pro %s v projektu %s zvolena varianta %s." % (topic, proj, r.choice("AB")),
            "context": "Tlačí nás termín a omezený rozpočet; potřebujeme řešení do 14 dnů.",
            "alternatives": ["varianta C (dražší)", "odložit o kvartál"][: r.randint(1, 2)],
            "consequences": ["nutná úprava harmonogramu"][: r.randint(0, 1)],
            "owner": ppl[0],
            "priority": r.choice(["must", "should", "could", None]),
        }
    if typ == "spec":
        return {
            "title": "Zadání: %s — %s" % (proj, topic),
            "date": d,
            "goal": "Postavit %s pro %s tak, aby to zvládl běžný uživatel bez školení." % (topic, proj),
            "acceptance_criteria": ["WHEN uživatel dokončí akci, THEN systém potvrdí výsledek",
                                    "WHEN vstup chybí, THEN formulář ukáže srozumitelnou chybu"][: r.randint(1, 2)],
            "constraints": ["rozpočet do 200 tis. Kč"][: r.randint(0, 1)],
            "out_of_scope": ["mobilní aplikace"][: r.randint(0, 1)],
            "owner": ppl[0],
            "priority": r.choice(["must", "should", None]),
        }
    if typ == "client_feedback":
        return {
            "title": "Zpětná vazba: %s" % proj,
            "date": d, "source_person": ppl[0],
            "sentiment": r.choice(["positive", "neutral", "negative"]),
            "points": ["Líbí se přehlednost nového návrhu", "Vadí pomalé načítání na mobilu"][: r.randint(1, 2)],
            "requests": ["Přidat export do PDF"][: r.randint(0, 1)],
        }
    if typ == "risk_review":
        return {
            "title": "Revize rizik: %s" % proj,
            "date": d, "project": proj,
            "risks": [{"what": "Zpoždění dodávky %s" % topic, "severity": r.choice(["low", "medium", "high"]),
                       "mitigation": "týdenní kontrola stavu", "owner": ppl[0]}][: r.randint(1, 1)],
            "decisions_needed": ["Schválit rezervu v rozpočtu"][: r.randint(0, 1)],
        }
    # interview
    return {
        "title": "Rozhovor: %s (%s)" % (ppl[0], proj),
        "date": d, "interviewee": ppl[0], "role": "vedoucí provozu",
        "insights": ["Nejvíc času ztrácí ruční přepisování objednávek",
                     "Tým si vede vlastní tabulky mimo systém"][: r.randint(1, 2)],
        "follow_ups": ["Domluvit stínování provozu na půl dne"][: r.randint(0, 1)],
    }


# --------------------------------------------------------------- raw text

def _noise(r: random.Random, target_chars: int, base_len: int) -> str:
    out = []
    while base_len + sum(len(x) for x in out) < target_chars:
        out.append(r.choice(SMALLTALK) + " " + NOISE_PARA)
    return "\n\n".join(out)


def build_raw(p: Dict[str, Any], gt: Dict[str, Any]) -> str:
    r = _rng(p["iter"] + 13_000_000)
    typ, lines = p["type"], []
    adv = p.get("adversarial")
    if adv == "empty":
        return ""
    title_line = "%s — %s" % (gt["title"], gt["date"])
    lines.append(title_line)
    lines.append("")
    if typ == "meeting":
        lines.append("Přítomni: %s." % ", ".join(gt["participants"]))
        lines.append(r.choice(SMALLTALK))
        lines.append("%s: %s" % (gt["participants"][0], gt["summary"]))
        for dec in gt.get("decisions", []):
            lines.append("%s: Navrhuji — %s. Důvod: %s. Bereme to jako rozhodnutí, vlastním ho já."
                         % (dec.get("owner") or gt["participants"][0], dec["what"], dec.get("why") or "dohoda"))
        for a in gt.get("actions", []):
            due = (" Termín: %s." % a["due"]) if a.get("due") else ""
            lines.append("%s: Beru si úkol: %s.%s" % (a["owner"], a["what"], due))
        for q in gt.get("open_questions", []):
            lines.append("Otevřená otázka, nikdo si ji nevzal: %s" % q)
        for rk in gt.get("risks", []):
            lines.append("Zaznělo riziko: %s." % rk)
    elif typ == "decision":
        lines.append("Kontext: %s" % gt["context"])
        lines.append("Rozhodnutí (%s, vlastník %s): %s" % (gt["date"], gt["owner"], gt["what"]))
        lines.append("Zvažované alternativy: %s." % "; ".join(gt["alternatives"]))
        for c in gt.get("consequences", []):
            lines.append("Důsledek: %s." % c)
        if gt.get("priority"):
            lines.append("Priorita dle MoSCoW: %s." % gt["priority"])
    elif typ == "spec":
        lines.append("Cíl zadání: %s" % gt["goal"])
        for ac in gt["acceptance_criteria"]:
            lines.append("Akceptační kritérium: %s." % ac)
        for c in gt.get("constraints", []):
            lines.append("Omezení: %s." % c)
        for o in gt.get("out_of_scope", []):
            lines.append("Mimo rozsah: %s." % o)
        lines.append("Zadání vlastní: %s." % gt["owner"])
        if gt.get("priority"):
            lines.append("Priorita: %s." % gt["priority"])
    elif typ == "client_feedback":
        lines.append("Od: %s (klient). Vyznění celkově: %s." % (gt["source_person"], gt["sentiment"]))
        for pt in gt["points"]:
            lines.append("Bod zpětné vazby: %s." % pt)
        for rq in gt.get("requests", []):
            lines.append("Požadavek klienta: %s." % rq)
    elif typ == "risk_review":
        lines.append("Projekt: %s" % gt["project"])
        for rk in gt["risks"]:
            lines.append("Riziko: %s. Závažnost: %s. Mitigace: %s. Vlastník: %s."
                         % (rk["what"], rk["severity"], rk["mitigation"], rk["owner"]))
        for dn in gt.get("decisions_needed", []):
            lines.append("Potřebné rozhodnutí: %s." % dn)
    else:  # interview
        lines.append("Rozhovor s: %s, role: %s." % (gt["interviewee"], gt["role"]))
        for ins in gt["insights"]:
            lines.append("Postřeh: %s." % ins)
        for f in gt.get("follow_ups", []):
            lines.append("Navazující krok: %s." % f)

    body = "\n".join(lines)
    if adv == "unicode_chaos":
        body = "🧪🔥 ｛ＴＥＳＴ｝ ‮RTL‬ العربية 中文測試 ́̂̃\n" + body + "\n𝔘𝔫𝔦𝔠𝔬𝔡𝔢 ✓ émoji 👍"
    if adv == "frontmatter_bomb":
        body = "---\ntitle: [neuzavřený seznam v RAW souboru\n---\n" + body
    if adv == "long_lines":
        body += "\n" + ("x" * 5000)
    if adv == "emoji_names":
        body = body.replace(gt["title"], gt["title"] + " 🚀")
    target = BUCKET_CHARS[p["bucket"]]
    noise = _noise(r, target, len(body))
    return body + ("\n\n" + noise if noise else "") + "\n"


# ------------------------------------------------- mock provider responses

DROPPABLE = {
    "meeting": ["summary", "participants"],
    "decision": ["what", "context", "owner", "alternatives"],
    "spec": ["goal", "acceptance_criteria"],
    "client_feedback": ["source_person", "sentiment", "points"],
    "risk_review": ["project", "risks"],
    "interview": ["interviewee", "insights"],
}
ENUM_FIELD = {"decision": "priority", "spec": "priority",
              "client_feedback": "sentiment"}
LISTY = {"meeting": "actions", "decision": "alternatives", "spec": "acceptance_criteria",
         "client_feedback": "points", "risk_review": "risks", "interview": "insights"}


def mock_responses(p: Dict[str, Any], gt: Dict[str, Any]) -> Tuple[List[Any], str]:
    """-> (queue odpovědí pro MockProvider, očekávaný outcome ok|needs_review|failed)"""
    import copy
    r = _rng(p["iter"] + 23_000_000)
    clean = copy.deepcopy(gt)
    mode = p["perturb"]
    if mode == "none":
        return [clean], "ok"
    if mode == "invented_field":
        bad = copy.deepcopy(gt)
        bad["halucinovane_pole"] = "tohle ve vstupu není"
        return [bad], "ok"                       # strip → validní na 1. pokus
    if mode == "drop_required":
        bad = copy.deepcopy(gt)
        bad.pop(r.choice(DROPPABLE[p["type"]]), None)
        return [bad, clean], "ok"
    if mode == "bad_enum":
        fld = ENUM_FIELD.get(p["type"])
        if not fld:                               # typ bez enumu → degraduj na drop
            bad = copy.deepcopy(gt); bad.pop(r.choice(DROPPABLE[p["type"]]), None)
            return [bad, clean], "ok"
        bad = copy.deepcopy(gt); bad[fld] = "extra-mega"
        return [bad, clean], "ok"
    if mode == "bad_date":
        bad = copy.deepcopy(gt); bad["date"] = "3.6.2026"
        return [bad, clean], "ok"
    if mode == "wrong_type":
        bad = copy.deepcopy(gt); bad[LISTY[p["type"]]] = "tohle má být seznam"
        return [bad, clean], "ok"
    if mode == "uncorrectable_missing":
        bad = copy.deepcopy(gt); bad.pop(r.choice(DROPPABLE[p["type"]]), None)
        return [bad, copy.deepcopy(bad)], "needs_review"
    if mode == "null_owner_action":
        bad = copy.deepcopy(gt)
        bad["actions"] = [{"what": "Úkol bez vlastníka", "owner": None, "due": None}]
        return [bad, copy.deepcopy(bad)], "needs_review"
    if mode == "malformed_json":
        return [{"__raw__": "Tady bohužel žádný JSON není, jen vata."},
                {"__raw__": "A na druhý pokus zase nic — { rozbité"}], "failed"
    raise ValueError(mode)
