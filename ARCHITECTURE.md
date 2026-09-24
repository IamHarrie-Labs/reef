# Architecture v2

Question -> validated parser -> signed portfolio -> historical estimation ->
snapshot cost scenario -> shared verdict -> append evidence -> explanation.

`model.py` defines weights, complete-day settlement sums, chronological funding
selection, and dollar costs. `capacity.py` enforces chronological beta fitting
and exposes exact-notional calculation plus a sampled capacity grid.
`intervals.py` owns the approximate funding uncertainty and shared verdict.
`export_web.py` writes the same grid to data/ and web/; the browser never prices.
`verdict.py` retains full beta precision, actual source timestamps and exact size.
`score.py` evaluates supplied executions and settlement marks; it cannot infer
actual fills from candles. Historical records without v2 accounting are excluded.

Research utilities are exploratory, not an independent trading backtest.
CI runs financial regression tests, parser tests and offline pipeline smoke checks.

## The live desk (hourly)

```
.github/workflows/desk.yml ─► src/desk_cycle.py
   refresh.py   funding (39 symbols) → funding_archive, order books, recent candles
   shadow.py    exit matured holds against today's book · backfill settlement marks
                · open new 1-day (every 8h) and 3-day (every 24h) holds, predictions
                  frozen via verdict.build_evidence
   export_web   re-price every pair, grade shadow executions (score.py), solve.py
                requirements, verdict-change feed → web/web_export.json
   anchor.py    Merkle root over ledger + executions → OpenTimestamps → Bitcoin
   commit       "[skip ci]" push to main; the site reads the newest export directly
```

The browser picks whichever is newer: the export bundled at deploy time, or
the live one on `main`. It never recomputes a number. `api/investigate.js`
reads the same live snapshot, so Qwen explains exactly what the visitor sees.
