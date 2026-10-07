# Consecutive paper-case validation

The evaluation includes every scheduled shadow prediction in the captured ledger, sorted by timestamp and key. It does not choose winners, profitable cases or a fixed-size sample. Individual trader questions are not included in the downloadable inputs.

## Current frozen evaluation

933 records across 29 entry batches: 430 graded, 376 missed exit windows, 52 missing execution or funding data, and 75 pending. Statuses depend on the report's evaluation cutoff. They do not imply the collector has just refreshed the underlying observations.

All 430 graded cases have enough prior funding history for the paired baseline comparison:

| Mean absolute funding error | Per case | Equal weight per entry batch |
|---|---:|---:|
| Reef | 4.4521 bp | 4.4613 bp |
| Zero funding | 4.8092 bp | 4.6987 bp |
| Last settled rate continued | 8.0110 bp | 7.3079 bp |

Reef beats zero funding in 192 cases and last-rate continuation in 233. A lower average error need not mean winning most cases. Its net-direction agreement is 98.8372%, exactly matching always predicting a nonpositive outcome. All 430 frozen net estimates are nonpositive; five paper outcomes are positive. Mean execution-cost absolute error is 17.4346 bp.

These are descriptive comparisons, not statistical significance, realized trades or portfolio returns. Shared instruments and overlapping holds create dependence. The high missing-outcome fraction may bias complete-case metrics. No-trade means zero trading P&L excluding idle-capital returns. Historical forecasts were recorded prospectively, but this evaluation protocol was chosen after those outcomes.

## Reproduce

Run `python src/prospective_validation.py` to evaluate local captured data. Run `python src/prospective_validation.py --verify` to reproduce every metric from the published input bundle. Downloadable JSON files live in `web/public/validation/`. Full results include every record, every reason for non-grading, batches and pair/hold breakdowns. Portable source inputs encode legacy infinite descriptive fields as strings. The input hash covers that portable representation.

## Subsequent cases

`web/public/validation/protocol.json` fixes the protocol and future-cohort timestamp boundary. Subsequent evaluations keep post-boundary cases in a separate cohort. The builder refuses a silent change to the protocol. This file does not itself provide independent timestamp proof or external preregistration.

The local export pipeline and existing hourly workflow have been updated to regenerate and stage these artifacts. Those source/workflow changes still need publication to the remote repository before the existing hosted collector will use them. A Vercel deployment publishes the current frozen report, not future observations. Future outcomes cannot be produced until the holding periods finish and the collector captures complete exits and funding marks.

Bulk Bitcoin proof timing has not been verified for every row. The original portable case retains its separate proof verifier. Replaying the series establishes arithmetic consistency, not exchange authenticity or completeness of all possible recorded predictions.
