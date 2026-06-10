# Stress KB V6.1

AI-Native Knowledge Base (kbmd V6.1). Navigace: [INDEX.md](INDEX.md) · pravidla pro agenty: [AGENTS.md](AGENTS.md)

## Workflow

```
kbmd ingest <soubor>                       # vstup do raw/ (immutable, sha256)
kbmd extract <raw> --template meeting      # extrakce dle kontraktu -> draft
kbmd lint                                  # kontrola celé báze
kbmd promote <dokument> --to published     # po lidské revizi
kbmd index                                 # přegenerovat INDEX.md
kbmd retract <raw|dokument> --reason "..." # stažení + kaskáda do karantény
```

## Ruční režim (bez CLI)

Báze je obyčejný markdown + git — funguje i bez kbmd (postup v AGENTS.md §Ruční nouzový režim).
