# kbmd-v6-stress-test

Stress test **kbmd 6.1.0** (AI-Native Knowledge Base V6.1 — první implementační release): **400 iterací reálného vykonání pipeline** (ingest → extract → lint-gate → lifecycle → index).

Na rozdíl od [kbmd-v5-stress-test](https://github.com/dalibormraz/kbmd-v5-stress-test) (simulace nad specifikací) tady běží skutečný kód a každé číslo má artefakt v tomto repu.

| Soubor | Obsah |
|---|---|
| [00-SCENARIO.md](00-SCENARIO.md) | scénář, asserty a kritéria úspěchu — psáno a commitnuto PŘED spuštěním |
| [harness/](harness/) | generátor vstupů (seed 64001) + runner |
| [kb/](kb/) | testovaná knowledge base (finální stav vč. JSONL traces) |
| [results/](results/) | iterations.jsonl, ops.jsonl, souhrny fází |
| [RESULTS.md](RESULTS.md) | závěrečné vyhodnocení proti kritériím C1–C9 |
