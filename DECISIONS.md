# Engineering decisions

Why the model and the demo are built the way they are, for the calls that
weren't obvious.

## Risk is the residual spread, not funding volatility

A pair trade's daily P&L has two live components: funding carry and
residual-spread drift. It's tempting to compute a Sharpe from funding alone
— funding is the return you're actually being paid. But the position is
*not* riding out funding-rate noise; it's riding out the beta-hedged price
spread between two instruments for the full holding period, and that
spread moves independently of funding.

Pricing SMH/SOXL on funding volatility alone gives a Sharpe of ~5.1.
Pricing it on residual-spread volatility — the risk that's actually being
carried — gives 0.05. That's roughly a 100× difference, not a rounding
error, and it inverts the trade's viability entirely. `capacity.py`'s
docstring states this directly: *"reporting a funding-only Sharpe would
overstate the trade by an order of magnitude."* Every Sharpe number in this
repo is computed against `resid_vol_hr`, scaled as √t, never against
funding's own standard deviation.

## Execution cost is amortized once, not charged per rebalance

`round_trip_cost()` walks the book once for entry and once for exit —
that's the whole cost model. It is **not** charged again for each 8h
funding interval, because the position isn't being closed and reopened
every interval; it's held. This is what makes the capacity curve
non-trivial: a trade that looks unprofitable at a 1-day hold (cost
dominates) can turn profitable at 30 days (carry accumulates linearly,
cost stays fixed). Get this amortization wrong in either direction and
every number in the capacity grid is wrong.

## Beta is fitted in-sample only, then held fixed out-of-sample

`hedge_ratio()` takes an optional `upto` cutoff and is always called with
the in-sample boundary when validating the model, never fitted on the same
data it's tested against. This is the standard walk-forward discipline for
avoiding a hedge ratio that's secretly overfit to the test window — and
it's why the leveraged-product betas (TQQQ 2.89, SOXS -3.72, TSLL 1.99)
recovering their true mechanical multiples out-of-sample was the check that
validated the whole pipeline, not just a nice-to-have.

## XAU/XAUT is the one pair that survives, and that's reported, not hidden

Screening 18 same-underlying pairs and finding that only gold clears
Sharpe 0.5 is an uncomfortable result for a *tokenized-equity* hackathon —
the surviving pair isn't even an equity. The alternative was to keep
hunting for a second survivor among the equity pairs, or to quietly drop
the finding. Neither happened. The result is reported as-is in the README,
the evidence files, and the project description, because the finding
itself — *17 of 18 apparent opportunities are priced illusions, and the
naive ranking points at exactly the wrong one* — is the actual contribution
here, independent of which specific pair happens to be the exception.

## The original hedge-survival concept ("SOLVENT") was abandoned, not softened

An earlier direction priced whether a spot-plus-futures hedge could survive
a margin call before its offsetting leg became liquid. It required a
tokenized-equity spot market on Bitget. A direct check of all 2,241 spot
symbols found zero RWA-linked instruments — the entire tradeable RWA
universe on this exchange is `USDT-FUTURES` perpetuals. Rather than
re-scope the concept around a synthetic spot leg (which would have made the
core mechanism fictional), it was dropped in favor of the perpetual-pair
carry model this repo actually implements. The empirical check that killed
an idea is more valuable than the idea, so it's documented here instead of
erased.

## The web demo ports the pricing model's *output*, not its code

`web/index.html` does not reimplement `model.py` or `capacity.py` in
JavaScript. `export_web.py` runs the real Python pipeline and exports a
precomputed grid (18 pairs × 8 sizes × 7 holds) as static JSON; the page
looks up the nearest grid point to a parsed query. This was a deliberate
trade: a from-scratch JS reimplementation risks silently diverging from the
validated model (different rounding, a transcription slip in the cost
formula), and there was no time to build a parallel test suite proving two
implementations agree. A precomputed, versioned export can't diverge from
the model that produced it, at the cost of the page only being able to
answer questions within the precomputed grid rather than arbitrary
size/hold combinations. The one thing genuinely re-implemented client-side
is the natural-language query parser (`llm.py`'s regex logic, ported
line-for-line, including its two bug fixes — see below) — because parsing
free text has no "wrong divergence" risk the way financial arithmetic does.

## Two parser bugs, caught by testing the demo against real phrasing

The size and hold-period regexes in `llm.py` were each wrong in ways that
only testing against actual example questions surfaced:

- `"3-day trade"` doesn't match `\d+\s*day` — a hyphen isn't whitespace —
  so it silently fell through to the 30-day default. Fixed by allowing
  `[\s-]*` between the number and the unit.
- A bare `\d+` size regex matched the `100` embedded in the ticker
  `NDX100`, treating "trust the QQQ/NDX100 spread" as a $100 position.
  Fixed by requiring a `$` prefix, a k/m suffix, or 4+ bare digits with no
  adjacent letters before a number counts as a size.

Both fixes are regression-tested in [`src/test_llm_parsing.py`](src/test_llm_parsing.py)
against nine phrasings including the two failure cases, "an hour" (no digit
at all), and a query with size/hold both unstated. CI runs it on every push.

## The self-scoring ledger logs before synthesis, not after

`verdict.py` calls `ledger.append()` immediately after pricing a query and
**before** calling the LLM for the natural-language explanation. If a
verdict were logged after synthesis, or if the evidence object were
mutable after logging, a later observer couldn't be sure the logged
prediction wasn't adjusted with hindsight. Logging first, then rendering,
makes `score.py`'s eventual grading meaningful: it's checking a prediction
that was fixed before the outcome existed, not after.
