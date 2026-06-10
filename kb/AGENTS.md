# AGENTS.md — manuál této znalostní báze pro AI agenty

Tahle složka je AI-Native Knowledge Base (kbmd V6.1). Než cokoli uděláš, přečti `INDEX.md`.

## Struktura

| Cesta | Co to je | Smíš zapisovat? |
|---|---|---|
| `INDEX.md` | navigace (jen published) | NE — generuje `kbmd index` |
| `raw/` | imutabilní vstupy (přepisy, poznámky, importy) | jen přidávat nové; NIKDY neměnit obsah existujících |
| `00_TEMPLATES/` | extrakční kontrakty (vlastní člověk) | NE bez explicitního zadání vlastníka |
| `00_ENUMS/` | sdílené číselníky | NE bez explicitního zadání |
| `01_DECISIONS/ … 06_RISKS/` | destilovaná znalost | přes `kbmd extract`, ručně jen po dohodě |
| `wiki/inbox/` | needs-review fronta | sem patří vše nejisté |
| `observability/` | JSONL traces | jen append přes nástroje |

## Pravidla práce

1. **Navigace:** čti `INDEX.md` → otevři celý soubor. Negrepuj naslepo, nehádej obsah.
2. **Extrakce jen podle šablony.** O tom, co je podstatné, rozhoduje šablona (kontrakt), ne ty.
   Co ve vstupu není, je `null` — nikdy nedomýšlej fakta, jména, termíny.
3. **Lifecycle:** nový dokument = `status: draft`. Do `published` povyšuje člověk
   (`kbmd promote`). Na published dokumenty se smí odkazovat, na ostatní ne.
4. **Nejistota → `wiki/inbox/`** s `needs_review_reason`. Nikdy tichý zápis nejisté informace.
5. **Fakta se invalidují, nemažou:** zastaralý dokument dostane `superseded_by`, stažený zdroj
   se řeší `kbmd retract` (kaskáda do karantény).
6. **Kontrola:** po každém zápisu spusť `kbmd lint` (nebo aspoň zkontroluj povinná
   frontmatter pole: template, template_version, status, source, extracted_at, valid_from).

## Ruční nouzový režim (bez kbmd CLI)

Báze je čitelná a udržovatelná i bez nástroje: extrahuj podle šablony v `00_TEMPLATES/`
(pole + anti-schéma + akceptační kritéria jsou v jejím frontmatter), ulož do správné složky
s frontmatter dle bodu 6, přidej řádek do `INDEX.md` (odkaz — souhrn (datum)).
