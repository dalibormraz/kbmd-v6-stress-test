---
template_id: decision
template_version: 1.0.0
owner: dalibor
status: production
created: 2026-06-10
applies_to:
  - "Jedno rozhodnutí s kontextem a alternativami (ADR-like)"
not_for:
  - "Průběžné poznámky ze schůzky → meeting"
routing:
  target: 01_DECISIONS
fields:
  - name: title
    type: str
    required: true
    description: "Krátký název rozhodnutí"
    example: "Hosting na Vercelu místo vlastního VPS"
  - name: date
    type: date
    required: true
    description: "Kdy rozhodnutí padlo"
    example: "2026-06-05"
  - name: what
    type: str
    required: true
    description: "Co přesně bylo rozhodnuto (1–3 věty)"
    example: "MVP poběží na Vercelu, free tier, custom doména."
  - name: context
    type: str
    required: true
    description: "Situace/problém, který si rozhodnutí vynutil"
    example: "Potřebujeme nasadit do 14 dnů a nemáme dev-ops kapacitu."
  - name: alternatives
    type: list[str]
    required: true
    description: "Zvažované alternativy; pokud žádné nezazněly, uveď ['žádné zvažovány']"
    example: "vlastní VPS u Hetzneru"
  - name: consequences
    type: list[str]
    required: false
    description: "Důsledky a dopady, pokud zazněly"
  - name: owner
    type: str
    required: true
    description: "Kdo rozhodnutí vlastní/učinil"
    example: "Dalibor"
  - name: priority
    type: str
    required: false
    enum: priority
    description: "MoSCoW priorita, pokud zazněla"
    example: "must"
required_sections:
  - "Kontext"
  - "Rozhodnutí"
  - "Alternativy"
  - "Důsledky"
sections_map:
  "Kontext": context
  "Rozhodnutí": what
  "Alternativy": alternatives
  "Důsledky": consequences
anti_schema:
  - "Nápady a brainstorming bez explicitní shody — to není rozhodnutí"
  - "Rozhodnutí nesmí být formulováno ostřeji, než zaznělo (žádné přitvrzování)"
  - "Citlivé obchodní podmínky (ceny, marže) jen pokud jsou nutné pro pochopení"
acceptance:
  - "WHEN je dokument typu decision, THEN alternatives obsahuje aspoň 1 položku (případně 'žádné zvažovány')"
  - "WHEN není jasný vlastník, THEN extrakce patří do needs-review, ne do KB"
  - "WHEN priority nezazněla, THEN je null (nedomýšlet)"
changelog:
  - "1.0.0 (2026-06-10): první produkční verze (V6.1)"
---

# Šablona: decision

Nejcennější znalost v bázi. Jeden dokument = jedno rozhodnutí (supersede řetěz
místo editace: nové rozhodnutí dostane `superseded_by` odkaz ze starého).

## Kompetenční otázky

- KO-1: Proč jsme se takhle rozhodli?
- KO-2: Co jsme zavrhli a proč?
- KO-3: Kdo za rozhodnutím stojí a od kdy platí?
