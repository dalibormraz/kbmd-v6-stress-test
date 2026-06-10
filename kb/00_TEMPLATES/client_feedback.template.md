---
template_id: client_feedback
template_version: 1.0.0
owner: dalibor
status: production
created: 2026-06-10
applies_to:
  - "Zpětná vazba od klienta (mail, call, zpráva)"
not_for:
  - "Formální zadání → spec"
routing:
  target: 04_PEOPLE
fields:
  - name: title
    type: str
    required: true
    description: "Krátký název zpětné vazby"
    example: "Zpětná vazba: redesign webu"
  - name: date
    type: date
    required: true
    description: "Kdy zazněla"
    example: "2026-03-12"
  - name: source_person
    type: str
    required: true
    description: "Kdo zpětnou vazbu dal"
    example: "Klára Svobodová"
  - name: sentiment
    type: str
    required: true
    enum: sentiment
    description: "Celkové vyznění, jen pokud je z textu zřejmé"
    example: "negative"
  - name: points
    type: list[str]
    required: true
    description: "Konkrétní body zpětné vazby (pochvaly i výtky)"
    example: "Vadí pomalé načítání na mobilu"
  - name: requests
    type: list[str]
    required: false
    description: "Explicitní požadavky klienta z toho plynoucí"
    example: "Přidat export do PDF"
required_sections:
  - "Body"
  - "Požadavky"
sections_map:
  "Body": points
  "Požadavky": requests
anti_schema:
  - "Nehodnotit oprávněnost zpětné vazby — jen zachytit"
  - "Sentiment nedomýšlet z jediného slova; když není zřejmý, patří extrakce do needs-review"
  - "Osobní stížnosti na konkrétní lidi parafrázovat bez jmen třetích stran"
acceptance:
  - "WHEN klient něco explicitně žádá, THEN je to v requests, ne jen v points"
  - "WHEN vyznění není z textu zřejmé, THEN sentiment je null (→ needs-review, je povinný)"
changelog:
  - "1.0.0 (2026-06-10): vyrobeno ZA POCHODU ve stress testu — trigger pravidla 3× po iteraci 37 (vzorky: iterace 6, 9, 37 v raw/notes/); recept dle V6.0/04-METODOLOGIE"
---

# Šablona: client_feedback (vyrobena za pochodu)

Auditní stopa: typ `client_feedback` se ve stress běhu objevil potřetí v iteraci 37 →
trigger pravidla 3×. Šablona vyrobena z nahromaděných vzorků v needs-review frontě
(kompetenční otázky: Co klientovi vadí/líbí se? Co konkrétně žádá? Jak je naladěný?).
