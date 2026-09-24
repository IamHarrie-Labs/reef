---
name: reef-pricer
description: Answer a plain-English question about whether a Bitget RWA (real-world-asset) perpetual pair's funding yield is real, once execution cost and residual spread risk are priced in. Use when the user asks things like "is the XAU/XAUT carry real", "can I trust this funding yield", "what's the Sharpe on SMH/SOXL at $50k for 2 weeks", or names any Bitget RWA/equity-linked perp pair together with a size or holding period. Returns a SUPPORTED / UNPROVEN / UNFAVOURABLE verdict with a 95% confidence interval, backed by evidence computed entirely outside the model (never invented by it).
---

# Reef pricer

Reef is a deterministic carry/risk/cost pricing engine for Bitget RWA perpetual
pairs (tokenized equities, indices, and gold), plus an LLM layer that explains
— but never computes — the verdict. This skill runs the real pipeline and
reports only what it returns.

## The one rule

**Every number in your answer must come from the JSON evidence block the
script prints.** Do not compute, estimate, or restate a Sharpe ratio,
percentage, or confidence interval yourself, and do not soften or round past
what's printed. If the evidence has no number for something the user asked
(e.g. a pair Reef doesn't track), say so — do not fill the gap with a guess.
This mirrors the project's own architecture rule (see `DECISIONS.md`, D-08):
the model decides what a number *means*, everything downstream only *reports*
it.

## How to run it

From the repository root:

```bash
python src/verdict.py "Is the XAU/XAUT yield real for $25k over 30 days?"
```

The question can name one or two tickers, a dollar size, and a holding
period in plain English — the parser resolves a single named ticker to its
paired instrument automatically (e.g. naming `XAU` alone resolves to
`XAU/XAUT`). Output has two parts:

1. `--- evidence ---` — a JSON block: `pair`, `beta`, `edge` (gross funding
   figures, cadence, sample size), `risk_adjusted` (net bp, cost bp, risk bp,
   Sharpe), `breakeven_days`, `n_funding_intervals`, `generated_at_utc`. Treat
   this as the complete and only source of truth.
2. `--- verdict ---` — a human-readable explanation synthesized from that
   evidence (template-based if no LLM key is configured, `BITGET_QWEN_API_KEY`
   otherwise).

To see the full ranked index across every tracked pair instead of one
question:

```bash
python src/reef_index.py
```

To see the 95% confidence interval and effective-sample-size detail behind
any Sharpe figure (why SUPPORTED requires the interval to exclude zero, not just
the point estimate to clear 0.5):

```bash
python src/intervals.py
```

## Interpreting the verdict

- **SUPPORTED** — net Sharpe clears 0.5 on its point estimate *and* the 95%
  confidence interval excludes zero. Evidence of an edge, on this sample.
- **UNPROVEN** — clears 0.5 on the point estimate, but the interval includes
  zero. Not evidence of an edge — could easily be sampling noise.
- **UNFAVOURABLE** — doesn't clear 0.5. The visible yield doesn't survive execution
  cost and risk.

Two things worth surfacing to the user if relevant, because they are easy to
misread as bugs but are documented, deliberate properties of the data:

- Funding history comes from a **rolling 100-interval window** — Bitget's API
  doesn't serve more. Gold contracts (XAU/XAUT/PAXG) settle funding every 4h,
  everything else every 8h, so the same 100 intervals cover ~16.5 days of
  gold history vs ~33 days for equities (see `DECISIONS.md` D-15).
- A pair that was SUPPORTED or UNPROVEN in one run can look different after a data
  refresh, purely because the funding window has rolled forward — this is
  expected sampling variation, not a broken model (`DECISIONS.md` D-06).

## What this skill must not do

- Never invent a pair, price, or Sharpe value not present in the evidence
  JSON.
- Never state a verdict word (SUPPORTED/UNPROVEN/UNFAVOURABLE) other than the one the
  script printed.
- Never average, extrapolate, or "round up" a number across pairs or holding
  periods the user didn't ask about.
- If `src/verdict.py` errors or reports `"error"` in the evidence (unresolved
  pair, no funding history, book too thin), report that directly — don't
  substitute a plausible-sounding guess.
