# Reef

Research whether an RWA perpetual pair's funding estimate survives execution costs.
Bitget hackathon: **Track 3 — AI Trading Desk, Open Theme**.

## Corrected model v2

The reference amount N is the B-leg notional. The base portfolio is **A=-beta*N,
B=+N**; the direction sign multiplies both positions. Negative beta can mean
both legs are long or both short. Funding, execution costs and residual risk
use these same weights. Returns are per N, **not return on collateral**.

- Beta is fitted to earlier prices, ending before the funding window starts.
- Funding is summed independently for each leg into complete UTC days. Days
  missing settlements are excluded; unequal settlement schedules are supported.
- Direction is selected on the first 60% of those days and frozen for the rest.
  The later window may have negative carry; the model does not flip it positive.
- Book costs are calculated in dollars per actual leg size, then divided by N.
  Exit costs reuse the entry snapshot as an explicit scenario assumption.
- The displayed Sharpe is a **modelled risk-adjusted estimate**, not a realised
  trading Sharpe. Square-root-time risk scaling is an assumption.

## Run offline

```sh
python src/test_accounting.py
python src/test_llm_parsing.py
python src/screen.py
python src/intervals.py
python src/export_web.py
cd web
npm ci
npm run dev
```

Open the local Vite URL printed by `npm run dev`. The home page links to the research dashboard. Build with `npm run build`; deploy the contents of `web/dist/`. Hash routes work on static hosting. The supplied CloudFront video and web fonts require internet access. The web grid discloses nearest
size/holding-period selections. The CLI prices the exact requested notional:

```sh
python src/verdict.py "Is SMH/SOXL worth $12345 over 30 days?"
```

The CLI uses optional Qwen parsing and commentary when configured; otherwise it
uses templates. The static website uses templates unless its host provides the
Claude sample capability. Numerical output and classifications are deterministic.
Prompt restrictions do not guarantee correct AI explanations; commentary is
supplementary and CLI numerical tokens are checked against evidence.

## Interpretation

- **UNFAVOURABLE:** point estimate fails the research threshold under assumptions.
- **UNPROVEN:** inadequate evidence or uncertainty crossing zero.
- **SUPPORTED:** clears the threshold and the approximate funding-only interval;
  this is conditional support, not proof of profitability.

Confidence intervals omit uncertainty in execution cost, beta, risk and selection
across pairs. Current data is short and correlated. See LIMITATIONS.md.

## Audit trail

CLI evidence is appended before explanation with model version, source timestamps,
weights and training boundaries. The local ledger is append-only by convention,
not tamper-proof. Browser queries are not persisted to this ledger.

Scoring requires actual signed fills, fees, complete funding coverage and mark
prices at settlements. Missing evidence stays unscored. Legacy model records are
marked superseded; they do not enter a hit rate. No trades are placed by Reef.

Earlier headline performance and survivor claims have been withdrawn. See
[evidence/corrected_v2](evidence/corrected_v2) for regenerated outputs and
[evidence/superseded_v1](evidence/superseded_v1) for preserved old narratives.
The formerly linked hosted artifact has not been redeployed by this local repair.
