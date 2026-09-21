# Evidence

Raw, unedited output of the actual pipeline, committed as text files so every
number in the README and the project description traces back to a
re-runnable command rather than a claim.

Each file is timestamped at generation (`_20260920T235953Z` = 2026-09-20
23:59:53 UTC) and produced by exactly the command in its own name:

| File | Command | What it proves |
|---|---|---|
| `screen_*.txt` | `python src/screen.py` | The naive-vs-priced ranking inversion — SMH/SOXL (17.7% gross) prices to Sharpe 0.05; XAU/XAUT (7.0% gross) is the one survivor |
| `mirage_index_*.txt` | `python src/mirage_index.py` | Full 18-pair public index: score, verdict, cost, consistency |
| `capacity_full_*.txt` | `python src/capacity.py` | Full size × hold capacity grid for the top 3 ranked pairs |
| `funding_regime_*.txt` | `python src/funding_regime.py` | Funding edge by regime — 7× weaker on weekends than US market hours |
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
