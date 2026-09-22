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
