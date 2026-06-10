---
template_id: interview
template_version: 1.0.0
owner: dalibor
status: production
created: 2026-06-10
applies_to:
  - "Rozhovor s uživatelem / expertem / stakeholderem"
not_for:
  - "Pracovní schůzka s úkoly → meeting"
routing:
  target: 04_PEOPLE
fields:
  - name: title
    type: str
    required: true
    description: "Název rozhovoru"
    example: "Rozhovor: Eva Horká (interní wiki)"
  - name: date
    type: date
    required: true
    description: "Datum rozhovoru"
    example: "2026-02-18"
  - name: interviewee
    type: str
    required: true
    description: "S kým se mluvilo"
    example: "Eva Horká"
  - name: role
    type: str
    required: false
    description: "Role/pozice dotazovaného, pokud zazněla"
    example: "vedoucí provozu"
  - name: insights
    type: list[str]
    required: true
    description: "Klíčové postřehy a zjištění (parafráze, ne citace)"
    example: "Nejvíc času ztrácí ruční přepisování objednávek"
  - name: follow_ups
    type: list[str]
    required: false
    description: "Dohodnuté navazující kroky"
required_sections:
  - "Postřehy"
  - "Navazující kroky"
sections_map:
  "Postřehy": insights
  "Navazující kroky": follow_ups
anti_schema:
  - "Žádné doslovné citace delší než věta — parafrázovat (ochrana dotazovaného)"
  - "Osobní/citlivé sdělení mimo téma rozhovoru nezachycovat"
  - "Vlastní interpretace tazatele neoznačovat za postřeh dotazovaného"
acceptance:
  - "WHEN je zachycen postřeh, THEN je to parafráze výroku dotazovaného, ne názor tazatele"
  - "WHEN role nezazněla, THEN je null"
changelog:
  - "1.0.0 (2026-06-10): vyrobeno ZA POCHODU ve stress testu — trigger pravidla 3× po iteraci 31 (vzorky: iterace 4, 29, 31); recept dle V6.0/04-METODOLOGIE"
---

# Šablona: interview (vyrobena za pochodu)

Auditní stopa: trigger 3× po iteraci 31. Anti-schéma cílí na největší riziko
tohoto typu: vkládání interpretací tazatele do úst dotazovanému.
