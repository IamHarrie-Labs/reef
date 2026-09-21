# Limitations

What Reef's numbers mean, what they don't, and what isn't built yet. Every
limitation here also applies to the equivalent claim in the project
description and the live demo.

## The market data is real; the sample is young

- Prices, funding rates, and order books are all pulled from Bitget's public
  `USDT-FUTURES` endpoints — nothing here is synthetic or simulated.
- The price history behind `capacity.py` and `screen.py` is **83 days of
  hourly closes** (2026-06-24 → 2026-09-16), split 60/40 in-sample /
  out-of-sample. That's one calm market regime. It has not seen a genuine
  stress event.
- Funding history is **~33 days** (100 intervals at 8h). The consistency
  percentages (e.g. XAU/XAUT's 68%) are a young sample, not a long-run rate.
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
  signal for beta-fitting and risk estimation over 83 days, but any single
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

The regime-dependence finding (signal-to-noise degrades ~20× from US market
hours to weekend, combining a 2.89× tracking-error increase with a 7×
funding-edge decrease) is measured from historical closes and funding
history — that part is solid. Whether that's *because* liquidity actively
withdraws when dislocations widen (an adversarial mechanism) is a live
question `adverse_selection.py` is built to answer, but as of the evidence
committed in this repo it has only 8 snapshots to work with. See
[`evidence/README.md`](evidence/README.md) for the exact caveat and what a
trustworthy answer will look like once the recorder has run for days.

## What isn't built

| Feature | Status | Why |
|---|---|---|
| Live recorder (`recorder.py`) | Running, self-healing (`run_recorder.sh`) | Needs continuous uptime to produce a trustworthy adverse-selection answer — see above |
| Self-scoring (`score.py`) | Built, all logged verdicts still pending | Verdicts are graded against realised prices only once their holding period elapses (14–30 days); none have matured yet |
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
