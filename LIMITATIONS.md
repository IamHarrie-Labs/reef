# Limits of corrected model v2

- Funding evaluation is a short chronological holdout within captured history.
  It is not forward paper trading. Many correlated pairs were inspected.
- Returns use B-leg reference notional, not gross exposure or posted collateral.
  No portfolio margin, liquidation, collateral financing or dynamic hedge model.
- Fees are a stated 6bp per leg per side assumption, not account-specific fees.
- Snapshot book walks cannot guarantee fills; exits reuse the same book. Metadata
  shows snapshot timestamps separately from report generation timestamps.
- Funding cash estimates assume static notionals. Actual fixed-quantity positions
  require settlement mark prices; the outcome scorer requires those marks.
- Residual volatility uses hourly log returns and sqrt(time) scaling. Neither this
  approximation nor the funding-only confidence interval is a realised Sharpe.
- Confidence intervals condition on fixed beta, costs and volatility and ignore
  model-selection uncertainty. They are approximate, not certified error bounds.
- The local ledger is not immutable. Web queries are not appended to it. Old rows
  are retained but marked superseded by the scorer. No hit rate is asserted.
- Live LLM calls and the externally hosted artifact have not been verified in this
  repair. Prompts cannot enforce factual correctness; authoritative outputs are
  deterministic. Browser AI commentary is explicitly labelled supplementary.
- RWA contracts and clusters are not guaranteed economically interchangeable.
  Correlation/beta does not verify instrument identity or legal exposure.
- Legacy regime and decay utilities are exploratory. Shared legs invalidate an
  independent-pairs interpretation of their p-values. No 20x signal/noise claim.
