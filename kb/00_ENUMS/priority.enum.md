---
enum_id: priority
owner: dalibor
version: 1.0.0
values:
  - value: must
    description: "Bez toho to nejde — blokuje cíl"
  - value: should
    description: "Důležité, ale dá se krátkodobě obejít"
  - value: could
    description: "Nice-to-have, dělá se při volné kapacitě"
  - value: wont
    description: "Vědomě teď ne (zaznamenat proč)"
---

# Enum: priority (MoSCoW)

Sdílená klasifikace priorit napříč šablonami. Hodnoty neměnit bez migrace —
přidání hodnoty je minor bump, odebrání/přejmenování major.
