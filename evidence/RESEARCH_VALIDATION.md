# Research notebook verification

These are engineering checks, not participant feedback or evidence of demand.

## Verified locally

- Fourteen Node tests cover comparison cell identity, conversational context,
  ranking, explicit scenario snapping, aliases, unsupported requests, validated
  Qwen plans, invalid numerical prose, fallback, Vercel and Worker routes.
  Qwen responses in these tests are mocked; no external model is contacted.
- Twenty accounting, five shadow-desk, two book-retention and four portable-proof
  regressions pass. Retention tests archive synthetic books in temporary test
  directories and independently replay their hypothetical entry/exit walks.
- Export consistency checks match the calculator across twenty-seven pairs and
  fourteen hundred twenty-eight priced grid cells in the current local snapshot.
- Type checking and the production website build pass.

## Authorized live Qwen check

On October 5, 2026, the user authorized sending the QQQ/TQQQ versus SMH/SOXL
comparison, $25k reference size, thirty-day hold and corresponding model evidence
to the configured Qwen endpoint. Tests used the local snapshot `2026-10-05 12:23Z`.
Qwen returned a valid comparison plan in multiple attempts. Both result cells
matched the Python export exactly. Explanation requests timed out at twenty
seconds and, on subsequent attempts, thirty-five seconds. One attempt also
timed out during planning. No live explanation passed the guard in this session.

The explanation budget is now thirty-five seconds, the client budget fifty-five
seconds, and requested output is shorter. Regression tests and the production
build pass after these changes. Fallback results remain available. This confirms
live planning and fallback behavior, not reliable live explanation quality.

## Still pending

- Reliable live Qwen explanation remains unverified because of endpoint timeouts.
  The initial authorization block was resolved by explicit user approval.
- Final browser and responsive-layout verification of this revision: browser
  access encountered an automatic approval-review timeout.
- Three real trader sessions under `VALIDATION.md`; no results have been claimed.
- Deployment of these local changes and the next scheduled shadow cycle. Existing
  records have not been retroactively given order-book evidence.

## Review sequence

Compare QQQ/TQQQ with SMH/SOXL at $25k for 30 days. Ask what happens if funding
reverses, then change the hold to seven days. Confirm both pairs and the stress
remain in context, and that each displayed number matches the frozen export.
Ask what would need to change, remove the stress, and export the notebook.
Check that unsupported shocks produce an error while retaining previous turns.

The notebook is a dated research artifact. It is not an anchored prediction,
an actual trade, or proof that model commentary is factually correct.
