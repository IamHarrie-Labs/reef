# Decisions

Material engineering decisions taken during the build, and why. Several
were forced by something that actually broke, and three changed a headline
result.

> **Read D-15 first.** A funding-cadence bug understated gold's carry by
> half until late in the build. D-05, D-06 and D-07 record the reasoning as
> it happened, including numbers that D-15 later corrected; each carries a
> note where that applies.

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
looked like the one real trade in the book.

> *Corrected by D-15.* 1.46 was itself computed with gold's funding
> cadence wrong. Corrected, the same window gives 4.21.

---

## D-06 · Refreshing data invalidated the headline result, and that was kept

**Context.** Bitget's funding endpoint serves only the most recent 100
intervals. Refreshing rolls the window forward, so every refresh is an
unplanned out-of-sample test.

**Finding.** On the window ending 09-21 — same pair, same model, nothing
refitted — XAU/XAUT retained 56% of its gross edge and consistency fell
68% → 57%. Residual vol was unchanged at ~2.7 bp/hr: the carry decayed, the
risk did not. The rest of the book held at 99% median edge retention.

> *Corrected by D-15.* As first recorded, Sharpe fell 1.44 → **0.21**,
> dropping XAU/XAUT below the bar and leaving 0 of 25 pairs clearing it.
> Both figures carried the cadence bug. Corrected, it falls **4.21 → 1.75**:
> a large decay, but it still clears 0.5. The 56% retention figure is a
> ratio and is unaffected. "The one edge that cleared the bar decayed below
> it" was an artifact; "the top-ranked pair decayed hardest" is not.

**Decision.** The earlier funding window was recovered from git history
into `data/funding_prev` and both windows ship in the repo, so
`edge_decay.py` can be re-run by anyone. The README was rewritten around
the decay rather than around the result it replaced.

**Rejected.** Pinning the project to the older window. The pair that
decayed hardest was the one the model had ranked first — the shape of the
winner's curse, and more useful than the point estimate it undercut.

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

> *Qualified by D-15.* Gold settles every 4 hours, so its r₁ is measured
> at a 4h lag while the equities' is at 8h — not a like-for-like
> comparison. At a matched 8h lag gold is +0.32 to +0.41 and equity pairs
> range from −0.09 to +0.20. Gold is more persistent, by much less than
> this table suggests. The `n_eff` values remain correct: they describe the
> samples as they exist.

**Decision.** `intervals.py` adjusts to `n_eff = n·(1−r)/(1+r)` before
computing any interval, and uses a **Wilson score interval** for
consistency, which is a binomial proportion and misbehaves under a normal
approximation near its bounds.

**Consequence.** XAU/XAUT's Sharpe 95% CI is **[−0.38, +3.87]** (corrected
per D-15). Its point estimate clears the bar; its interval includes zero.
The pairs at the top of the ranking are the ones with the least
information behind them, which is why the top one decayed hardest in D-06.

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

---

## D-13 · The "23× funding decline" was retracted after testing it

**Context.** The README reported that funding edge falls from 0.843 bp/interval
during US hours to 0.036 on weekends — "a 23× decline". It was a ratio of two
means, never tested.

**Finding.** `regime_test.py` runs a paired comparison across 28 pairs. The
*effect* is real: the difference is **+0.81 bp/interval, 95% CI [+0.42,
+1.23]**, 20 of 28 pairs agree, exact sign-test p = 0.036. But the *ratio*'s
bootstrap 95% interval is **−137× to +171×**. The weekend mean sits near zero,
so resampling a handful of pairs swings the denominator across zero and the
ratio across infinity. "23×" was never an effect size; it was a division by
a number close to nothing.

**Decision.** The README now reports the difference with its interval, and the
retraction is stated inline where the old number used to be — not silently
replaced. `regime_test.py` prints an explicit warning whenever a ratio's
denominator is within 25% of zero relative to its numerator.

**Rejected.** Keeping "23×" because the direction was right. A correct
direction attached to a meaningless magnitude still misleads, and "23×" is
exactly the kind of number that gets repeated.

---

## D-14 · A cited number had no reproducing script, and was also stale

**Found by.** Writing `regime_test.py` and searching for the code behind the
README's "tracking error rises 2.89×, 26 of 27 pairs".

**Cause.** It came from an exploration script that was never committed, run
on the original 83-day price history. The README's opening section claims
every number regenerates from committed data. For this one it did not.

**Decision.** The analysis was ported into `regime_test.py` and re-run on the
current 117-day history. It now reads **2.58×, 95% CI ~2.1–3.1×, 25 of 28
pairs, p = 2.7 × 10⁻⁵** — the strongest result in the project, and slightly
smaller than the stale figure. The out-of-sample discipline from D-03 is
applied: beta fitted on the first 60% of each pair's history, the ratio
measured on the remaining 40%.

**Rejected.** Leaving the old figure because it was close. A number the repo
cannot reproduce contradicts the repo's central claim about itself,
regardless of how close it happens to be.

---

## D-15 · Gold settles funding every 4 hours; the model assumed 8 for everything

**Found by.** Building the funding archive (`funding_archive.py`). Its
coverage report flags gaps between an archive's first and last timestamp,
assuming an 8-hour cadence. Three symbols showed **negative** gaps — more
intervals than an 8-hour cadence could fit in their span. All three were
gold: XAU, XAUT, PAXG.

**Cause.** `model.py` hardcoded `INTERVALS_PER_DAY = 3`. Timestamp spacing
in the funding data, and the exchange's own contract spec (`fundInterval`),
both confirm gold settles every **4h** while the other 36 contracts settle
every 8h. Every gold figure converting per-interval funding to per-day or
annualised terms was **understated by exactly half**. Gold's 100-interval
history also spans 16.5 days, not the ~5 weeks previously stated.

**What it changed.**

| | Under the bug | Corrected |
|---|---:|---:|
| XAU/XAUT Sharpe, current window | 0.21 | **1.75** |
| XAU/XAUT Sharpe, earlier window | 1.44 | **4.21** |
| XAU/PAXG Sharpe | −0.31 | **0.78** |
| Pairs clearing Sharpe 0.5 | 0 of 25 | **2 of 25** |
| Funding regime test | mixed 4h and 8h units | normalised to bp/day |

**Decision.** Cadence is derived per pair from the median spacing of its
own funding timestamps (`model.intervals_per_day`), so it needs no network
and matches the data actually being priced. The edge dict now carries
`intervals_per_day`, `funding_interval_h` and `history_days`, and
`intervals.py` and `regime_test.py` use the pair's own cadence.

**What it did not change.** The 56% edge retention in D-06 is a ratio and
survives. The regime test's sign test is per-pair and scale-invariant, so
its 20/28 and p = 0.036 are unchanged; the difference moves from a
mixed-unit figure to **+2.57 bp/day [+1.38, +3.86]**. The tracking-error
result (D-14) never touched funding.

**Not rewritten.** 52 short-hold verdicts in `data/ledger.jsonl` were
logged before the fix, and their gold evidence carries the understated
carry. The ledger is append-only by design (D-10) — editing frozen
predictions to match later knowledge is exactly what it exists to prevent.
Their verdict labels are unaffected: at a 1–3 day hold, even corrected gold
carry is far below its ~25bp round-trip cost, so they remain MIRAGE.

**Rejected.** Hardcoding `4` for gold. The next contract Bitget lists on a
different cadence would reintroduce the same bug silently. Deriving it from
the data cannot drift from the data.

**The lesson.** Four earlier decisions in this file — D-05, D-06, D-07 and
the headline "0 of 25" — were reasoned carefully from numbers that were
wrong at the source. Rigour applied downstream of a bad constant produces
confident, well-documented, wrong conclusions. The bug was caught by a
consistency check built for a different purpose, not by re-examining the
conclusions.

## D-16: the LLM gets a Skill, not a license

**Context.** The reference repos surveyed for this hackathon (Night Shift,
Morrow) package their tools as things another agent — not just a human at a
terminal — can pick up and use correctly. Reef's LLM layer (`llm.py`) was
already scoped to explain evidence rather than compute it (D-08), but that
scoping lived only in a prompt string, invisible to anyone who didn't read
`llm.py`.

**Decision.** Added `.claude/skills/reef-pricer/SKILL.md`, a Claude Skill
that wraps `verdict.py`. It states the same rule D-08 enforces in code —
every number in an answer must come from the evidence JSON, nothing
invented, nothing rounded past what's printed — as an explicit,
machine-readable constraint on whichever model picks the skill up, not just
a comment for a human reader.

**Rejected.** A thin CLI wrapper with no skill manifest. That would run the
same script but drop the constraint the moment someone other than the
original author (or a model without the surrounding context) invoked it.
The manifest is the artifact that survives being copied out of this repo.
