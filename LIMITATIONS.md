# Limitations

What Reef's numbers mean, what they don't, and what isn't built yet. Every
limitation here also applies to the equivalent claim in the project
description and the live demo.

## The market data is real; the sample is young

- Prices, funding rates, and order books are all pulled from Bitget's public
  `USDT-FUTURES` endpoints — nothing here is synthetic or simulated.
- The price history behind `capacity.py` and `screen.py` is **117 days of
  hourly closes** (2026-05-26 → 2026-09-20), split 60/40 in-sample /
  out-of-sample. That's one calm market regime. It has not seen a genuine
  stress event.
- Funding history is **100 intervals** — the most the endpoint serves — but
  that is **33 days for equity contracts (8h settlement) and only 16.5 days
  for gold (4h settlement)**. The top two pairs by Sharpe are both gold, so
  the headline rests on the shortest history in the book. Consistency
  percentages are a young sample, not a long-run rate.
- `data/funding_archive/` accumulates every window seen, so history grows
  past the endpoint's limit while refreshes keep running (median 114
  intervals at the time of writing). Headline numbers still use the latest
  single window, so they remain comparable across refreshes.
- The order book behind every cost estimate is **one snapshot per pair**,
  taken during US regular trading hours — the most liquid window. Weekend
  and overnight execution costs are almost certainly higher than what's
  priced. See `adverse_selection.py` and its evidence file for the live
  attempt to measure this directly instead of assuming it.

## What the model does not account for

- **No borrow cost or margin requirement.** The capacity curve prices
  execution cost and residual-spread risk only. A real position also pays
  funding on collateral and may be margin-constrained before it's
  cost-constrained.
- **Hourly closes are not executable prices.** They're the best available
  signal for beta-fitting and risk estimation over 117 days, but any single
  hour's close could differ from what a market order actually fills at.
- **No slippage model beyond the single book walk.** `round_trip_cost()`
  walks the live book once; it does not model how the book itself might
  move in response to the order, or how it behaves in the regime where the
  trade is actually being considered (see above).
- **Beta is linear and static.** `hedge_ratio()` fits one OLS beta on
  in-sample data and holds it fixed for the out-of-sample test and for
  every live query. A regime-dependent or time-varying hedge ratio was not
  attempted.

## The adverse-selection question is open, not answered

The regime-dependence finding is tested in `regime_test.py` and holds:
tracking error relative to volatility is 2.58× higher on weekends (25 of 28
pairs, p = 2.7 × 10⁻⁵), and funding edge is 2.57 bp/day lower (20 of 28
pairs, p = 0.036). An earlier version combined two untested ratios into a
"~20× signal-to-noise" figure; one of those ratios had a near-zero
denominator and is retracted (`DECISIONS.md` D-13), so no combined multiple
is claimed. Whether that's *because* liquidity actively
withdraws when dislocations widen (an adversarial mechanism) is a live
question `adverse_selection.py` is built to answer, but as of the evidence
committed in this repo it has only 8 snapshots to work with. See
[`evidence/README.md`](evidence/README.md) for the exact caveat and what a
trustworthy answer will look like once the recorder has run for days.

## What isn't built

| Feature | Status | Why |
|---|---|---|
| Live recorder (`recorder.py`) | Running, self-healing (`run_recorder.sh`) | Needs continuous uptime to produce a trustworthy adverse-selection answer — see above |
| Self-scoring (`score.py`) | Built, no grades yet | 52 short-hold verdicts (1 and 3 days) were logged to mature on 2026-09-22 and 09-24; longer-hold verdicts mature from 10-03. Until then self-scoring is a mechanism, not a result |
| Agent Hub paper-trading integration | Not attempted | Bitget's Demo environment (`SUSDT-FUTURES`) carries only 3 crypto contracts (SBTC/SETH/SXRP) — no tokenized-equity instrument exists there to paper-trade against |
| Tokenized-equity spot leg | Not possible | 0 of 2,241 Bitget spot symbols are RWA-linked; the entire tradeable universe here is on `USDT-FUTURES` perpetuals |
| Margin/liquidation simulation (the original "SOLVENT" hedge-survival concept) | Abandoned | Requires a spot leg that doesn't exist on this exchange; see `DECISIONS.md` |
| Multi-exchange comparison | Not attempted | All data and pricing is Bitget-only |

## What the LLM does and doesn't do

The LLM (Claude via the artifact's `sample` capability, or Qwen via
`llm.py` when a key is configured) parses a natural-language question into
a structured query and explains an already-priced verdict in prose. It is
explicitly instructed, in its own system prompt, to use only numbers
present in the evidence object it's given — it does not compute, round, or
introduce a figure. The pricing math (`model.py`, `capacity.py`) is pure
deterministic arithmetic and runs identically with or without an LLM
available; the template fallback in `llm.py` proves this by construction.
