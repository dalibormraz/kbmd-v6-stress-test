---
template_id: risk_review
template_version: 1.0.0
owner: dalibor
status: production
created: 2026-06-10
applies_to:
  - "Revize rizik projektu (pravidelná či ad-hoc)"
not_for:
  - "Jednotlivé riziko zmíněné na schůzce → meeting.risks"
routing:
  target: 06_RISKS
fields:
  - name: title
    type: str
    required: true
    description: "Název revize"
    example: "Revize rizik: datový sklad"
  - name: date
    type: date
    required: true
    description: "Datum revize"
    example: "2026-04-02"
  - name: project
    type: str
    required: true
    description: "Projekt, ke kterému se revize vztahuje"
    example: "datový sklad"
  - name: risks
    type: list[entry]
    required: true
    description: "Identifikovaná rizika"
    entry_fields:
      - name: what
        type: str
        required: true
        description: "Popis rizika"
      - name: severity
        type: str
        required: true
        enum: severity
        description: "Závažnost dle sdílené škály"
      - name: mitigation
        type: str
        required: false
        description: "Dohodnutá mitigace, pokud zazněla"
      - name: owner
        type: str
        required: false
        description: "Kdo riziko hlídá"
  - name: decisions_needed
    type: list[str]
    required: false
    description: "Rozhodnutí, která je kvůli rizikům potřeba učinit"
required_sections:
  - "Rizika"
  - "Potřebná rozhodnutí"
sections_map:
  "Rizika": risks
  "Potřebná rozhodnutí": decisions_needed
anti_schema:
  - "Riziko bez závažnosti neodhadovat — chybějící severity = needs-review"
  - "Nezaměňovat rizika (nejistota) s problémy (už nastaly)"
acceptance:
  - "WHEN je zachyceno riziko, THEN má severity z enumu severity"
  - "WHEN mitigace nezazněla, THEN je null (nedomýšlet)"
changelog:
  - "1.0.0 (2026-06-10): vyrobeno ZA POCHODU ve stress testu — trigger pravidla 3× po iteraci 25 (vzorky: iterace 2, 10, 25); recept dle V6.0/04-METODOLOGIE"
---

# Šablona: risk_review (vyrobena za pochodu)

Auditní stopa: trigger 3× po iteraci 25; do té doby se vstupy hromadily jako
`no_template` v raw vrstvě. Využívá existující sdílený enum `severity` —
žádný nový číselník nebyl potřeba (anti-bloat).
