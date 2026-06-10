---
template_id: spec
template_version: 1.0.0
owner: dalibor
status: production
created: 2026-06-10
applies_to:
  - "Zadání / požadavek / funkční specifikace"
not_for:
  - "Rozhodnutí o směru → decision"
routing:
  target: 02_SPECS
fields:
  - name: title
    type: str
    required: true
    description: "Název požadavku/zadání"
    example: "Rezervační formulář na webu"
  - name: date
    type: date
    required: true
    description: "Kdy zadání vzniklo/zaznělo"
    example: "2026-06-04"
  - name: goal
    type: str
    required: true
    description: "Co se má postavit a proč (2–4 věty)"
    example: "Formulář pro rezervaci termínu, propojený s kalendářem."
  - name: acceptance_criteria
    type: list[str]
    required: true
    description: "Ověřitelná kritéria hotovosti (EARS styl kde to jde)"
    example: "WHEN uživatel odešle formulář, THEN přijde potvrzovací e-mail"
  - name: constraints
    type: list[str]
    required: false
    description: "Omezení (rozpočet, technologie, termíny), pokud zazněla"
  - name: out_of_scope
    type: list[str]
    required: false
    description: "Co explicitně NENÍ součástí zadání"
  - name: owner
    type: str
    required: false
    description: "Kdo zadání vlastní"
  - name: priority
    type: str
    required: false
    enum: priority
    description: "MoSCoW priorita, pokud zazněla"
required_sections:
  - "Cíl"
  - "Akceptační kritéria"
  - "Omezení"
  - "Mimo rozsah"
sections_map:
  "Cíl": goal
  "Akceptační kritéria": acceptance_criteria
  "Omezení": constraints
  "Mimo rozsah": out_of_scope
anti_schema:
  - "Implementační detaily, které nezazněly jako požadavek, nedomýšlet"
  - "Odhady pracnosti a cen extrahovat jen pokud explicitně zazněly"
acceptance:
  - "WHEN existuje spec dokument, THEN má aspoň 1 ověřitelné akceptační kritérium"
  - "WHEN kritérium nelze ověřit (vágní), THEN patří do open textu cíle, ne do acceptance_criteria"
changelog:
  - "1.0.0 (2026-06-10): první produkční verze (V6.1)"
---

# Šablona: spec

Most mezi domluvou a buildem. Akceptační kritéria jsou „testy" zadání —
preferuj EARS formulace (WHEN/THEN), jsou strojově lintovatelné.
