# Decisions

Material engineering decisions taken during the build, and why. Several
were forced by something that actually broke, and two reversed a headline
result.

---

## D-01 · Risk is the residual spread, not funding volatility

**Context.** A pair trade's P&L has two live components: funding carry and
beta-hedged residual-spread drift. Funding is the return being paid, so a
Sharpe computed from funding's own mean and standard deviation is the
obvious first construction.

**Finding.** It is wrong by about two orders of magnitude. SMH/SOXL prices
to a funding-only Sharpe around 5.1. The position is not riding out
funding-rate noise — it is carrying the beta-hedged price spread for the
full holding period, and that spread moves independently of funding.
Priced against residual-spread risk, the same trade earns **0.21**.

**Decision.** Every Sharpe in this project is computed against
`resid_vol_hr`, scaled as √t. `capacity.py` states this in its module
docstring so the constraint travels with the code.

**Rejected.** Reporting both and letting the reader choose. A funding-only
Sharpe has no defensible interpretation here; publishing it alongside the
correct number would have laundered it as a legitimate alternative.

---

## D-02 · Execution cost is amortized once, not charged per interval

**Context.** `round_trip_cost()` walks the order book for entry and exit.
The question was whether that cost recurs across a multi-interval hold.

**Decision.** It is charged exactly once. The position is held, not closed
and reopened each funding interval.

**Why it matters.** This single choice is what makes the capacity curve
non-trivial. Carry accumulates linearly while cost stays fixed, so the
same pair can be unviable at a 1-day hold and viable at 30. Charge cost
per interval and every trade dies; charge it never and every trade lives.
The 52 short-hold verdicts logged at 1 and 3 days all priced MIRAGE —
that is this asymmetry visible in the output.

---

## D-03 · The hedge ratio is fitted in-sample and never refitted

**Context.** `hedge_ratio()` takes an optional `upto` cutoff.

**Decision.** Beta is fitted on in-sample data only and held fixed for the
out-of-sample test and for every live query.

**Confirmation.** The leveraged products recovered their true mechanical
multiples out-of-sample — TQQQ 2.89, SOXS −3.72, TSLL 1.99, SOXL ~3. A
hedge ratio secretly overfit to the test window would not reproduce the
instruments' actual leverage. This was the check that validated the
pipeline, not a convenience.

---

## D-04 · The original hedge-survival concept was killed by a data check

**Context.** The project began as a margin-survival tool: could a
spot-plus-futures hedge survive a margin call before its offsetting leg
became liquid? It required a tokenized-equity spot market on Bitget.

**Finding.** All 2,241 Bitget spot symbols were enumerated. **Zero** are
RWA-linked. The entire tradeable RWA universe on this exchange is
`USDT-FUTURES` perpetuals.

**Decision.** The concept was dropped and replaced with the perpetual-pair
carry model this repo implements.

**Rejected.** Re-scoping around a synthetic or assumed spot leg. The
mechanism being demonstrated would then have been fictional, which is the
failure mode this project exists to detect in other people's numbers.

---

## D-05 · A funding-only Sharpe of 24.9 was the first sign something was wrong

**Found by.** XAU/XAUT reporting a funding Sharpe near 25 while every
instinct said a 7% gross yield on a gold pair is not a 25-Sharpe trade.

**Cause.** See D-01 — the denominator was funding volatility, which for a
persistent funding stream is tiny.

**Consequence.** Fixing the denominator dropped it to 1.46, which still
looked like the one real trade in the book. It took two further
measurements (D-06, D-07) to establish that even 1.46 was an artifact.

---

## D-06 · Refreshing data invalidated the headline result, and that was kept

**Context.** Bitget's funding endpoint serves only the most recent 100
intervals. Refreshing rolls the window forward, so every refresh is an
unplanned out-of-sample test.

**Finding.** On the window ending 2026-09-16, XAU/XAUT was the one pair
clearing Sharpe 0.5, at 1.44. On the window ending 09-21 — same pair, same
model, nothing refitted — it retained 56% of its gross edge, consistency
fell 68% → 57%, and Sharpe dropped to **0.21**. Residual vol was unchanged
at ~2.7 bp/hr: the carry decayed, the risk did not. The rest of the book
held at 99% median edge retention.

**Decision.** The earlier funding window was recovered from git history
into `data/funding_prev` and both windows ship in the repo, so
`edge_decay.py` can be re-run by anyone. The README was rewritten around
the decay rather than around the result it replaced.

**Rejected.** Reporting the 1.44 figure with a footnote, or pinning the
project to the older window. The pair that decayed hardest was the one the
model had selected — that is the winner's curse, and it is a more useful
finding than the trade it destroyed.

---

## D-07 · Effective sample size, not nominal, after autocorrelation

**Context.** Every headline number rests on 100 funding intervals. The
naive standard error assumes those are independent.

**Finding.** They are not, and the dependence is concentrated exactly where
it does the most damage. Lag-1 autocorrelation of net funding:

| Pair | r₁ | n_eff |
|---|---:|---:|
| XAU/PAXG | +0.65 | 21 |
| XAU/XAUT | +0.53 | 30 |
| XAUT/PAXG | +0.50 | 33 |
| every non-gold pair | ≈ 0 | 80–100 |

Every gold pair is heavily autocorrelated; no equity-RWA pair is. Median
r₁ across the book is +0.03.

**Decision.** `intervals.py` adjusts to `n_eff = n·(1−r)/(1+r)` before
computing any interval, and uses a **Wilson score interval** for
consistency, which is a binomial proportion and misbehaves under a normal
approximation near its bounds.

**Consequence.** XAU/XAUT's Sharpe 95% CI is **[−0.85, +1.27]**. It never
had the precision to support the 1.44 point estimate. The statistics
predict the decay that D-06 observed — two independent lines of evidence
reaching the same conclusion.

**Rejected.** Reporting point estimates alone. With 5 weeks of funding
history, a point estimate invites the reader to distinguish 0.21 from 0.51
when the sample cannot.

---

## D-08 · The web demo ships the model's output, not a second implementation

**Context.** The live demo needed to answer queries in the browser.

**Decision.** `export_web.py` runs the real Python pipeline and exports a
precomputed grid (pairs × 8 sizes × 7 holds) as static JSON. The page
looks up the nearest grid point. No pricing arithmetic runs in JavaScript.

**Why.** A from-scratch JS reimplementation can silently diverge — a
different rounding rule, a transcribed cost formula — and there was no
parallel test suite to prove two implementations agree. A versioned export
cannot diverge from the model that produced it.

**Cost of the decision.** The page can only answer questions inside the
precomputed grid; arbitrary size/hold combinations snap to the nearest
point, and the UI says so when it does.

**Exception.** The natural-language parser *is* reimplemented client-side,
ported line-for-line from `llm.py`. Parsing free text has no
wrong-divergence risk of the kind financial arithmetic does.

---

## D-09 · Two parser bugs, found by testing against real phrasing

**Found by.** Running the demo against the example questions rather than
reading the regexes.

**Bug 1.** `"3-day trade"` did not match `\d+\s*day` — a hyphen is not
whitespace — so it silently fell through to the 30-day default. A wrong
answer with no error.

**Bug 2.** A bare `\d+` size pattern matched the `100` inside the ticker
`NDX100`, so *"trust the QQQ/NDX100 spread"* was priced as a $100
position.

**Decision.** Hyphens allowed between number and unit; a size must carry a
`$` prefix, a k/m suffix, or 4+ bare digits with no adjacent letters. Both
are regression-tested in [`src/test_llm_parsing.py`](src/test_llm_parsing.py)
across nine phrasings including "an hour" (no digit at all) and a query
stating neither size nor hold. CI runs it on every push.

**Rejected.** Fixing them inline without a test. Both were silent
wrong-answer bugs, which is the class most worth pinning down.

---

## D-10 · The ledger is written before the model speaks

**Decision.** `verdict.py` calls `ledger.append()` immediately after
pricing and **before** invoking the LLM for its explanation.

**Why.** `score.py` grades logged verdicts against realised prices once
their holding periods elapse. That grade only means something if the
prediction was fixed before the outcome existed. Logging after synthesis,
or leaving the evidence object mutable, would leave no way for a reader to
rule out hindsight.

**Consequence.** 52 short-hold verdicts (1 and 3 days) were logged
deliberately so self-scoring could mature inside the project's own
timeline — every verdict logged during the build had used the 30-day
default and none could have been graded before submission.

---

## D-11 · The adverse-selection result was withheld rather than published thin

**Context.** `adverse_selection.py` asks whether order-book depth
withdraws exactly when the price gap widens.

**Finding.** At the committed snapshot the recorder had 8 usable snapshots
per symbol, from a single ~2-hour window, after the network path to
`api.bitget.com` dropped. Correlations on that sample ranged from −0.66 to
+0.92 across pairs.

**Decision.** The evidence file reports `n` and states plainly that a
correlation on 8 points is noise, not a finding. `src/run_recorder.sh` now
waits for network, launches the recorder, and relaunches it on failure, so
the sample accumulates unattended.

**Rejected.** Publishing the −0.66 as evidence of adversarial liquidity
withdrawal. It is the result the project would most like to be true, which
is exactly why it needed the larger sample before being claimed.

---

## D-12 · An earlier open-vs-closed cost comparison is published as confounded

**Context.** Two order-book snapshots existed: one during US regular hours
and one with the market shut.

**Finding.** Closed-market cost came out *lower* (0.93× median), the
opposite of the assumption stated in `LIMITATIONS.md`. But the two
snapshots were taken **4.5 days apart**, so the comparison mixes regime
with everything else that moved in between.

**Decision.** `depth_regime.py` ships with the result and a printed caveat
that it is directional only. `cost_by_regime.py` was written to do it
properly, using the recorder's continuous series so regimes are compared
within one process on one cadence.

**Rejected.** Reporting 0.93× as a measured closed-market discount. A
surprising result from a confounded comparison is the one most likely to
be wrong.
