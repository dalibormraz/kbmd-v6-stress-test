---
template_id: meeting
template_version: 1.0.0
owner: dalibor
status: production
created: 2026-06-10
applies_to:
  - "Schůzka / call s klientem nebo týmem (30 min – 4 h)"
not_for:
  - "Formální rozhodnutí s alternativami → decision"
  - "Zadání / požadavky → spec"
routing:
  target: 03_MEETINGS
fields:
  - name: title
    type: str
    required: true
    description: "Krátký název schůzky"
    example: "Kickoff webu pro klienta"
  - name: date
    type: date
    required: true
    description: "Datum konání (z vstupu, ne dnešní)"
    example: "2026-06-03"
  - name: participants
    type: list[str]
    required: true
    description: "Účastníci jménem; jen ti, kdo skutečně mluvili/byli zmíněni jako přítomní"
    example: "Jana Dvořáková"
  - name: summary
    type: str
    required: true
    description: "2–4 věty: o čem schůzka byla a co je hlavní výstup"
    example: "Domluven rozsah MVP a termín první ukázky."
  - name: decisions
    type: list[entry]
    required: false
    description: "Rozhodnutí-kandidáti, která na schůzce padla"
    entry_fields:
      - name: what
        type: str
        required: true
        description: "Co bylo rozhodnuto"
      - name: why
        type: str
        required: false
        description: "Důvod, pokud zazněl"
      - name: owner
        type: str
        required: false
        description: "Kdo rozhodnutí vlastní"
  - name: actions
    type: list[entry]
    required: false
    description: "Úkoly s vlastníkem; úkol bez vlastníka patří do open_questions"
    entry_fields:
      - name: what
        type: str
        required: true
        description: "Co se má udělat"
      - name: owner
        type: str
        required: true
        description: "Kdo to udělá"
      - name: due
        type: str
        required: false
        description: "Termín, pokud zazněl (volný text)"
  - name: open_questions
    type: list[str]
    required: false
    description: "Nezodpovězené otázky a úkoly bez vlastníka"
  - name: risks
    type: list[str]
    required: false
    description: "Rizika explicitně zmíněná na schůzce"
required_sections:
  - "Souhrn"
  - "Rozhodnutí"
  - "Úkoly"
  - "Otevřené otázky"
sections_map:
  "Souhrn": summary
  "Rozhodnutí": decisions
  "Úkoly": actions
  "Otevřené otázky": open_questions
anti_schema:
  - "Small talk, počasí, technické problémy s připojením — nezachycovat"
  - "Spekulace bez vlastníka neformulovat jako rozhodnutí"
  - "Osobní/citlivé údaje (zdraví, rodina, platy) — nezachycovat"
  - "Doslovné citace delší než 1 věta — parafrázovat"
  - "Termíny a čísla, která ve vstupu nezazněla, NIKDY nedomýšlet"
acceptance:
  - "WHEN na schůzce padl úkol, THEN má řádek v actions s owner, NEBO je v open_questions"
  - "WHEN je vyplněno decisions[].what, THEN jde o explicitní shodu ze vstupu, ne o návrh extraktoru"
  - "WHEN údaj (termín, číslo, jméno) není ve vstupu, THEN je pole null"
changelog:
  - "1.0.0 (2026-06-10): první produkční verze (V6.1)"
---

# Šablona: meeting

Zachytává schůzky a cally. Smysl: za 3 měsíce musí extrakt odpovědět na
„co jsme si řekli, kdo má co udělat a co zůstalo otevřené" — bez čtení přepisu.

## Kompetenční otázky (KO)

- KO-1: Co jsme klientovi/sobě slíbili a do kdy?
- KO-2: Kdo má jaký úkol?
- KO-3: Jaká rozhodnutí padla a proč?
- KO-4: Co zůstalo nedořešené?

## Golden samples

Viz `00_EVALS/meeting/` (vzniká s prvními reálnými extrakcemi; min. 2 vzorky před povýšením šablony).
