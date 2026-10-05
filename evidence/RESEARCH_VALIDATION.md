# Research notebook verification

These are engineering checks, not participant feedback or evidence of demand.

## Verified locally

- Fifteen Node tests cover comparison cell identity, conversational context,
  ranking, explicit scenario snapping, aliases, unsupported requests, validated
  Qwen plans, invalid numerical prose, fallback, Vercel and Worker routes.
  Qwen responses in these tests are mocked; no external model is contacted.
- Twenty accounting, five shadow-desk, two book-retention and four portable-proof
  regressions pass. Retention tests archive synthetic books in temporary test
  directories and independently replay their hypothetical entry/exit walks.
- Export consistency checks match the calculator across twenty-seven pairs and
  fourteen hundred twenty-eight priced grid cells before sync, and thirteen
  hundred sixteen after syncing the latest hourly data. Counts depend on depth.
- Type checking and the production website build pass.

## Authorized live Qwen check

On October 5, 2026, the user authorized sending the QQQ/TQQQ versus SMH/SOXL
comparison, $25k reference size, thirty-day hold and corresponding model evidence
to the configured Qwen endpoint. Tests used the local snapshot `2026-10-05 12:23Z`.
Qwen returned a valid comparison plan in multiple attempts. Both result cells
matched the Python export exactly. Explanation requests timed out at twenty
seconds and, on subsequent attempts, thirty-five seconds. One attempt also
timed out during planning. Subsequent investigation found that reasoning mode
was enabled by default. With `enable_thinking:false`, the full local comparison
returned valid planning and explanation in about nine seconds. A production
API test returned HTTP 200, valid planning and explanation in about five and a
half seconds, with financial cells unchanged.

The explanation budget is now thirty-five seconds, the client budget fifty-five
seconds, and requested output is shorter. Regression tests and the production
build pass after these changes. Fallback results remain available. This confirms
live planning and fallback behavior. Live explanation now works on tested
requests; these timings are observations, not a latency guarantee.

## Browser and deployment checks

The production site was deployed to its existing Vercel project. Browser checks
covered comparison, funding reversal, seven-day follow-up, solver conditions,
unsupported-shock error retention, and saved comparison context after reload.
Mobile and tablet checks at 375 and 768 pixels showed no document overflow.
Desktop checks used 1280 pixels. A development cancellation race and initial
notebook context reset were corrected during these checks.

Stress commentary incorrectly claiming recomputed support or confidence
intervals was observed and prompted a targeted guard and regression test.
This guard does not establish that every other prose statement is correct.
The export includes an inspectable JSON preview for browsers that block the
download. A portable historical proof is loaded independently if the hourly
export lacks the new case-study field.

The production export preview was parsed as JSON: four turns, both compared
pairs, seven-day hold and funding reversal matched the on-screen context. Its
contents are saved in `demo/notebook.json`. The ninety-second captioned MP4 in
`demo/` was rendered from six actual production captures and fully decoded
without errors. It is an edited walkthrough, not continuous screen footage.
The public historical proof download returned HTTP 200 and matched the local
verified bundle byte-for-byte (SHA-256
`ff04ad9cc0a0c73b550085f2b8cc6523e12c014bfdd743116bf474044002e4ed`).

The runtime npm audit reports zero advisories. Five high-severity advisories
remain in the Tailwind development/build dependency chain; no compatible patch
was available in its current major version. No forced major upgrade was made.

## Still pending

- Three real trader sessions under `VALIDATION.md`; no results have been claimed.
- Public GitHub source publication: automatic review rejected the push of the
  source and generated evidence commit pending specific disclosure approval.
  Consequently the remote hourly job does not yet have the new book-retention
  code. Existing records have not been retroactively given book evidence.
- The next scheduled shadow cycle after source publication. Local replay tests
  do not establish a completed production cycle.

## Review sequence

Compare QQQ/TQQQ with SMH/SOXL at $25k for 30 days. Ask what happens if funding
reverses, then change the hold to seven days. Confirm both pairs and the stress
remain in context, and that each displayed number matches the frozen export.
Ask what would need to change, remove the stress, and export the notebook.
Check that unsupported shocks produce an error while retaining previous turns.

The notebook is a dated research artifact. It is not an anchored prediction,
an actual trade, or proof that model commentary is factually correct.
