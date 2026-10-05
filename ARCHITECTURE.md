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
   onchain_gold read Chainlink XAU/USD and PAXG/USD via eth_call (no key/library)
                · basis vs Bitget's own price for XAU, XAUT, PAXG
   anchor.py    Merkle root over ledger + executions → OpenTimestamps → Bitcoin
   export_web   re-price every pair, grade shadow executions (score.py), solve.py
                requirements, verdict-change feed, on-chain basis → web/web_export.json
   commit       "[skip ci]" push to main; the site reads the newest export directly
```

The production browser picks whichever is newer: the export bundled at deploy
time, or the live one on `main`. Development uses the local export. The browser
never recomputes a financial number.

## Conversational research

`web/research/core.mjs` is shared by the Vercel `/api/research` route, Vite and
the Worker. Questions resolve to tracked pairs, a recorded size and hold, an
operation, and an optional recorded stress. Qwen may interpret the operation
through a strict plan; validation prevents it substituting instruments, stress
or ranking scope. A deterministic matcher provides a fallback. Comparisons and
rankings select existing Python cells without repricing them.

The service rejects a request when its snapshot identity differs from the
notebook's identity. Recent context preserves comparisons and follow-ups.
Qwen's optional three-field explanation is rejected if it contains digits.
This guards numerical output, not the truth of prose. Stress point estimates
do not acquire a newly computed confidence interval or verdict.

The browser keeps up to twelve turns locally and exports dated JSON notes.
Notebook turns are not appended to the anchored prediction ledger. Submitted
questions and recent context go to the service and, when enabled, Qwen.
The older `/api/investigate` route remains for compatibility.

## Future paper-fill replay

`book_evidence.py` stores complete captured books as compressed, canonical JSON
addressed by SHA-256. New shadow positions and executions bind their entry and
exit book hashes. Replay verifies book identity, timestamp, mid and depth-walk
price. This establishes reproducibility of hypothetical fills against retained
inputs; it does not authenticate exchange origin or prove an actual order fill.
Legacy executions have no retained books and cannot pass this replay.
