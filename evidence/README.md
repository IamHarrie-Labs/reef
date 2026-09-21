# Evidence

Raw, unedited output of the actual pipeline, committed as text files so every
number in the README and the project description traces back to a
re-runnable command rather than a claim.

Each file is timestamped at generation (`_20260920T235953Z` = 2026-09-20
23:59:53 UTC) and produced by exactly the command in its own name:

| File | Command | What it proves |
|---|---|---|
| `screen_*.txt` | `python src/screen.py` | Naive gross-yield ranking vs fully-priced ranking |
| `intervals_*.txt` | `python src/intervals.py` | 95% CIs, Wilson intervals and autocorrelation-adjusted effective sample for every pair |
| `regime_test_*.txt` | `python src/regime_test.py` | Sign tests and bootstrap CIs on both regime claims |
| `edge_decay_*.txt` | `python src/edge_decay.py` | Edge persistence across two funding windows |
| `mirage_index_*.txt` | `python src/mirage_index.py` | Full public index for every priced pair: score, verdict, cost, consistency |
| `capacity_full_*.txt` | `python src/capacity.py` | Full size × hold capacity grid for the top 3 ranked pairs |
| `funding_regime_*.txt` | `python src/funding_regime.py` | Funding edge by regime, descriptive (tested in `regime_test_*.txt`) |
| `adverse_selection_*.txt` | `python src/adverse_selection.py` | Gap-vs-depth correlation from the live recorder — **see caveat below** |

## Regenerating

Every file here can be reproduced from the cached data in `data/`:

```bash
python src/screen.py
python src/mirage_index.py
python src/capacity.py
python src/funding_regime.py
python src/adverse_selection.py
```

Rerunning against a fresher `data/prices.json` / `data/funding/` /
`data/depth/` (see [`README.md`](../README.md) for how those are pulled)
will produce different numbers — that's expected, not a discrepancy. The
committed files are a dated snapshot, not a permanent ground truth.

## Honest caveat on `adverse_selection_*.txt`

At generation time the live recorder (`src/recorder.py`) had collected only
**8 snapshots per symbol**, all captured during one ~2-hour weekend window
(2026-09-19 06:42–08:30 UTC) before the network path to `api.bitget.com`
dropped. The script is correct and the mechanism works — but a correlation
computed on 8 points is noise, not a finding. The committed file's
`gap_depth_correlation` values (ranging from -0.66 to +0.92 across pairs)
should **not** be read as evidence of adversarial liquidity withdrawal yet.

The recorder is running continuously again (via `src/run_recorder.sh`, which
waits for network and auto-relaunches on failure) and is expected to have
several days of multi-regime data — including full weekend and US-hours
windows — well before this evidence is next regenerated. A future snapshot
of this file with `n` in the hundreds, spanning multiple regimes, is the one
to trust.

## Superseded snapshots

Files stamped **before `20260921T065300Z`** were generated while `model.py`
assumed every contract settles funding every 8 hours. Bitget's gold
contracts settle every 4, so gold figures in those files understate carry
by half — including an earlier "0 of 25 pairs clear the bar" result. They
are kept rather than deleted so the correction is auditable; see
`DECISIONS.md` D-15. Use the latest timestamp (recorded in `evidence/.latest`).
