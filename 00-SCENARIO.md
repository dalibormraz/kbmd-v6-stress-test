# Stress test kbmd V6.1 — scénář (psáno PŘED spuštěním)

> **Datum návrhu:** 2026-06-10 · **Testovaný systém:** kbmd 6.1.0 (AI-Native KB V6.1, walking skeleton)
> **Commit disciplína:** tento scénář je první commit repa; harness druhý; výsledky až po nich.
> **Vztah k V5 stress testu:** V5 test (200 iterací) byl simulace nad specifikací. Tento test spouští **reálný kód** — každá iterace je skutečné vykonání pipeline s artefakty na disku.

## 1. Cíle a NE-cíle

**Cíle:** (G1) robustnost pipeline (žádný pád), (G2) účinnost quality-gate (validace+lint chytí injektované vady), (G3) integrita lifecycle (kaskáda retraction, index invarianty) pod náhodnými sekvencemi operací, (G4) metodika „šablony za pochodu" (pravidlo 3×) v praxi, (G5) determinismus a výkon, (G6) první reálné LLM měření extrakce end-to-end.

**NE-cíle (poctivě):** Toto NENÍ benchmark kvality modelu (syntetické vstupy mají ground truth vepsanou v textu — reálné přepisy jsou těžší). NENÍ to měření proti expertním golden labels (to je M2 s reálnými daty). NENÍ to test souběhu (V6.1 je single-user).

## 2. Architektura testu

- **Mock provider pro iterace 1–384**: deterministický, vrací ground-truth extrakci s **injektovanými poruchami** dle plánu. Testuje se SYSTÉM (validace, lint-gate, retry, routing, lifecycle), ne model. Směšovat systémové a modelové metriky je chyba V5 éry — zde odděleno.
- **Reálný provider (claude-cli, haiku) pro iterace 385–400**: end-to-end extrakce bez mocku; měří se přesnost polí proti ground truth + cena + latence.
- **Seed 64001** — celý plán iterací je reprodukovatelný (`generator.py` je čistá funkce seedu).

## 3. Anatomie iterace

Každá iterace = vygenerovaný vstup (typ, velikost, jazyk, porucha) → `ingest` → `extract` (mock/real) → asserty → průběžné operace dle rozvrhu (§6).

### 3.1 Typy vstupů a distribuce

| Typ | Podíl | Šablona na startu? |
|---|---|---|
| meeting | 40 % | ✅ v1.0.0 |
| decision | 15 % | ✅ v1.0.0 |
| spec | 15 % | ✅ v1.0.0 |
| client_feedback | 10 % | ❌ — vznikne za pochodu |
| risk_review | 10 % | ❌ — vznikne za pochodu |
| interview | 10 % | ❌ — vznikne za pochodu |

Vstup bez šablony se pouze ingestne a počítá (outcome `no_template`) — extrakce „od oka" je zakázaná architekturou (LLM orchestrátor, ne autor).

### 3.2 Velikostní buckety

XS ~0.3 kB · S ~1.5 kB · M ~6 kB · L ~30 kB · **XL ~110 kB** (3 % iterací; >25k tokenů ⇒ musí spustit truncation pre-pass a označit `kbmd.summarized: true` v trace). Jazyk: cs 80 % / en 20 %. Vstupy obsahují záměrný šum (small talk, tangenty) — anti-schéma ho má ignorovat.

### 3.3 Poruchy mock providera (co má gate chytit)

| Porucha | Podíl | Očekávaný výsledek (assert A2) |
|---|---|---|
| none (čistá GT) | ~55 % | `ok`, 1 pokus |
| drop_required / bad_enum / bad_date / wrong_type (1. pokus vadný, 2. čistý) | ~24 % | `ok`, **2 pokusy** (retry s chybami v promptu) |
| invented_field (halucinované pole navíc) | 5 % | `ok`, 1 pokus, pole NESMÍ být ve výstupu |
| uncorrectable_missing / null_owner_action (vadné oba pokusy) | 8 % | `needs_review` → `wiki/inbox/` s důvodem |
| malformed_json (oba pokusy ne-JSON) | 4 % | `failed`, žádný výstupní soubor |
| XL + none (summarize trigger) | 3 % | `ok` + `summarized: true` v trace |

## 4. Asserty na každou iteraci

- **A1 No-crash:** žádná neodchycená výjimka.
- **A2 Outcome match:** skutečný outcome == očekávaný dle poruchy (tabulka §3.3).
- **A3 Routing:** `ok` → soubor v cílové složce šablony se statusem `draft` a kompletním frontmatter; `needs_review` → v inboxu s `needs_review_reason`; `failed`/`no_template` → žádný distilled výstup.
- **A4 Gate-escape:** `ok` výstup musí mít 0 error nálezů lintu (špína nesmí projít do distilled jako čistá).
- **A5 Trace:** každá extrakce zapsala JSONL trace s povinnými poli.

## 5. Šablony za pochodu (G4)

Pravidlo 3× (metodologie V6.0 §4): jakmile se typ bez šablony objeví potřetí, fáze se zastaví a **operátor vyrobí šablonu** podle receptu (04-METODOLOGIE: vzorky → kompetenční otázky → pole ≤9 → anti-schéma → akceptace) z nahromaděných raw vzorků. Poté **backfill**: nahromaděné vstupy se zpětně extrahují (týdenní smyčka v malém). Audit trail: trigger log + commit šablony PŘED fází, která ji používá. Operátor = Claude (přiznáno); vzorky = syntetické (přiznáno).

## 6. Rozvrh operací (vetkáno mezi iterace)

- po `ok` extrakci: 50% šance `promote --to published`
- každých 20 iterací: `index` + **plný lint** → po regeneraci 0 errors (jinak nález)
- každých 50 iterací: `retract` náhodného zpracovaného raw → assert: všichni dependenti `quarantined`; KB009 PŘED `index` křičí, PO něm čisto
- každých 100 iterací: determinismus — `build_index()` 2× → byte-identické
- měří se: latence extract/lint/index (p50/p95), velikost KB v čase

## 7. Fáze

| Fáze | Iterace | Provider | Obsah |
|---|---|---|---|
| **A** | 1–120 | mock | 3 základní šablony; neznámé typy se hromadí → trigger report |
| **B** | 121–280 | mock | +3 šablony vyrobené za pochodu; na startu backfill fronty z fáze A |
| **C** | 281–384 | mock | plný mix + **adversarial blok 361–384**: prázdný soubor, 110k+ XL, unicode chaos (emoji/RTL/CJK), frontmatter-bomba v raw, 5k-znakové řádky |
| **D** | 385–400 | **claude-cli (haiku)** | 16 reálných extrakcí (4 meeting, 3 decision, 3 spec, 3 client_feedback, 3 risk_review); přesnost polí vs. GT, cena, latence |

## 8. Kritéria úspěchu (definována TEĎ, před during)

| ID | Kritérium | Práh |
|---|---|---|
| **C1** | Pády pipeline | **0** ze 400 |
| **C2** | Shoda outcome s očekáváním (A2) | ≥ 99 % (každý nesoulad jednotlivě rozebrat) |
| **C3** | Gate-escape: injektovaná vada projde do distilled jako čistá | **0** (tvrdé selhání testu) |
| **C4** | Integrita kaskády retraction | 100 % dependentů v karanténě + lint invariant |
| **C5** | Determinismus indexu | byte-identický při každé kontrole |
| **C6** | Výkon | mock extract p95 < 1.5 s; plný lint < 5 s na finální KB; **měří se trend vs. velikost KB** (podezření N6: lint-gate čte celou KB → očekávám růst, chci křivku) |
| **C7** | Reálné LLM (fáze D) | povinná pole přítomná 100 %; přesnost polí REPORTOVAT s n=16 (baseline, bez slibu prahu — první měření) |
| **C8** | Konzistence inboxu | každý inbox dokument má důvod; žádný published v inboxu |
| **C9** | Disciplína šablon | žádná šablona nevyrobena před 3. vzorkem (audit z logu) |

## 9. Taxonomie selhání (pro log)

`crash` · `outcome_mismatch` · `gate_escape` · `gate_overblock` (čistý výstup poslán do inboxu) · `routing_error` · `cascade_miss` · `index_drift` · `perf_over_budget` · `llm_field_miss` / `llm_invented` (jen fáze D).

## 10. Artefakty (vše v tomto repu)

`results/iterations.jsonl` (každá iterace 1 řádek) · `results/ops.jsonl` (operace a latence) · `results/summary-phase{A,B,C,D}.md` · `kb/` (finální stav KB vč. traces) · `harness/` (generator+runner, seed v kódu) · `RESULTS.md` (závěrečné zhodnocení proti C1–C9).
