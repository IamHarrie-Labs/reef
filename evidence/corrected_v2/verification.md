# Repair verification — 2026-09-21

- 20 accounting/integration regressions passed; 9 existing parser cases passed.
- All Python sources compile.
- screen, capacity, mirage_index, intervals, export_web and score ran successfully.
- Exploratory regime_test and edge_decay smoke checks passed; their old significance claims remain withdrawn.
- End-to-end exact-$12,345 CLI query passed with isolated temporary ledger and no remote calls.
- Local browser loaded 27 pairs and returned an UNFAVOURABLE SMH/SOXL result.
  The $12,345 request visibly disclosed pricing at its nearest $10,000 grid point.
- Hosted artifact and live LLM credentials were not exercised or redeployed.
- Existing recorder files and the historical ledger were not overwritten by this repair.

- Final export parity check passed: all 27 pairs and 1,442 priced grid cells agree with the calculator. The check is now in CI.
- Browser reload confirmed corrected UTF-8 display and regenerated evidence loading.
