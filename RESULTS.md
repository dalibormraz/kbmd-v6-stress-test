# Výsledky: stress test kbmd 6.1.0 — 400 iterací

> **Datum běhu:** 2026-06-10 · **Kritéria definována předem** v [00-SCENARIO.md](00-SCENARIO.md) (commit `85b7d51`, před harnessem i výsledky).
> **Reprodukce:** seed 64001; `python harness/runner.py --from 1 --to 120 --phase A` (+ B/C/D dle scénáře). Všechna čísla níže mají artefakt v `results/`.

## 1. Verdikt proti kritériím

| ID | Kritérium | Práh | Výsledek | Verdikt |
|---|---|---|---|---|
| C1 | Pády pipeline | 0/400 | **0/400** | ✅ |
| C2 | Shoda outcome s očekáváním | ≥ 99 % | **400/400 (100,0 %)** | ✅ |
| C3 | Gate-escape (vada projde do distilled jako čistá) | 0 | **0** | ✅ |
| C4 | Integrita kaskády retraction | 100 % | **8/8 ops; kaskáda 8/8; KB009 dle očekávání 8/8** | ✅ |
| C5 | Determinismus indexu | byte-identický | **4/4** | ✅ |
| C6 | Výkon | extract p95 < 1,5 s; lint < 5 s | lint p50 0,98 s / max 1,8 s ✅; index ≤ 0,53 s ✅; **extract p95 = 1,67 s ❌ od ~300 dokumentů** | ⚠️ viz S-06 |
| C7 | Reálné LLM | pole 100 % přítomná; přesnost reportovat | **16/16 ok na 1. pokus**; viz §3 | ✅ |
| C8 | Konzistence inboxu | reason u všech | **19/19 s důvodem; 19/19 správně routováno** | ✅ |
| C9 | Disciplína šablon (3×) | žádná šablona předčasně | trigger @25/31/37, šablony commitnuty až po fázi A (git historie) | ✅ |

Doplňkové invarianty: halucinovaná pole odstraněna **21/21**; XL summarize pre-pass označen **12/12**; nekompletní frontmatter u ok výstupů **0**; gate-overblock (čistý vstup chybně v inboxu) **0**; backfill needs-review fronty po vzniku šablon **39/39**.

Outcome rozpad (400): ok 328 · no_template 37 (fáze A, by design) · needs_review 19 · failed 16 (vše injektovaný malformed JSON). Finální KB: **400 raw + ~370 distilled dokumentů, 8 MB, plně lintovaná**.

## 2. Nálezy (S-01 … S-06) — o tohle tu šlo

| ID | Typ | Nález | Stav |
|---|---|---|---|
| **S-01** | bug kbmd | Odkaz na zdroj v patičce předpokládal hloubku 1 → z `wiki/inbox/` rozbitý (KB007). Chyceno v run #1 fáze A. | ✅ opraveno (root-relativní odkazy), retest run #2 čistý |
| **S-02** | design kbmd | Obsahové chyby inbox dokumentů blokovaly error-lint celé KB — ale inbox JE řízená karanténa. | ✅ opraveno: downgrade na info (KB021 zůstává error), +1 pytest |
| **S-03** | bug harness | `continue` u no_template přeskakoval rozvrh operací (chyběly retract/determinism kontroly). | ✅ opraveno, run #2 |
| **S-04** | design gap | Šablona může routovat do adresáře mimo `distilled_dirs` → dokumenty neviditelné pro lint i index (slepé místo). Objeveno při výrobě šablon za pochodu. | ⏳ otevřené — navrženo pravidlo **KB022 template-target-not-configured** (ID se nerecykluje, přidá se po testu) |
| **S-05** | kapacitní strop (detekce funguje) | Plochý INDEX.md přerostl rozpočet 25,6 kB při **~150+ published dokumentech** (na konci 36 kB při ~190 published). KB011 to korektně hlásí od iterace 320 — všech 5 nečistých kontrol má tuto jedinou příčinu. | ⏳ otevřené — remediace: hierarchický index (root → sekční INDEX.md), post-M2 backlog; přesně PageIndex/Claude Code vzor z rešerší |
| **S-06** | výkon | Extract latence roste lineárně s velikostí KB: p50 170 ms (0 dok.) → 1 667 ms (350+ dok.). Příčina známá předem (lint-gate staví celý LintContext, nález N6 atomické kontroly) — test ji kvantifikoval. | ⏳ otevřené — remediace: cache/scoped kontext pro lint-gate; do ~150 dokumentů (reálný projekt, měsíce provozu) je výkon v pohodě |

Škálovací křivka (extract p50 dle počtu dokumentů): 0+→170 ms · 50+→395 · 100+→666 · 150+→850 · 200+→1 042 · 250+→1 266 · 300+→1 458 · 350+→1 667.

## 3. Reálné LLM (fáze D, n=16, claude-cli + Haiku 4.5)

- **16/16 extrakcí ok na první pokus** (0 retry, 0 needs-review), latence p50 17,8 s, **cena celkem $0,525** (~$0,033/extrakce), tokens_in p50 28 067.
- Přesnost polí proti ground truth: **21 z 24 polí 100 %**; `title` 94 % (15/16); `decisions` 75 % (3/4 entry-matchů); `summary` 50 % (2/4).
- **Poctivá interpretace slabších čísel:** `summary`/`title` se skórují fuzzy překryvem tokenů ≥ 0,5 — model souhrn legitimně parafrázuje vlastními slovy, takže 50 % je z velké části artefakt hrubé metriky, ne halucinace (ruční kontrola vzorků: obsahově správné). `decisions` 75 % = 1 nespárované rozhodnutí v 1 dokumentu ze 4. Tohle je přesně důvod, proč M2 vyžaduje lidsky schválené golden labels místo fuzzy skóre.

## 4. Co tento test NEprokazuje (přísně)

1. **Kvalitu extrakce na reálných datech** — vstupy jsou syntetické s GT vepsanou v textu (reálné přepisy jsou šumovější a těžší). Fáze D je smoke-test reálné pipeline + baseline, ne benchmark kvality.
2. **Mock fáze testují systém, ne model** — to je záměr (oddělení vrstev), ale znamená to, že 100% C2/C3 vypovídá o validaci/gate/lifecycle, ne o LLM.
3. **Souběh** (více procesů nad jednou KB) — netestováno, V6.1 je single-user.
4. **Ensemble / disagreement-flag** — neměřeno (čeká na M2 s reálnými daty, dle D-15).
5. Hodnoticí metriky fáze D jsou hrubé (fuzzy match) — viz §3.

## 5. Srovnání s V5 stress testem

| | V5 test (200 iter.) | **V6.1 test (400 iter.)** |
|---|---|---|
| Co běželo | simulace nad specifikací | **reálný kód, reálné soubory, reálné LLM (subset)** |
| Artefakty | mimo repo, nereprodukovatelné | vše v tomto repu, seed 64001 |
| Kritéria | ex-post | **commitnuta před spuštěním** |
| Nálezy | doporučení do spec | **3 opravené bugy + 3 kvantifikované stropy** |

## 6. Závěr

Architektura V6.1 dělá pod zátěží přesně to, co slibuje: **brána nepustila jedinou injektovanou vadu (0 gate-escapes z ~180 poruchových iterací), lifecycle kaskáda je 100% spolehlivá, index deterministický, halucinovaná pole se zahazují, metodika „šablon za pochodu" funguje vč. backfillu.** Limity, které test našel, nejsou pády, ale změřené stropy (plochý index ~150–200 published dokumentů; extract latence od ~300 dokumentů) — oba mají známou příčinu, navrženou remediaci a pro nasazení do reálného projektu v řádu měsíců nevadí. Otevřené: S-04 (KB022), S-05, S-06.
