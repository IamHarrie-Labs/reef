# Limits of corrected model v2

- Funding evaluation is a short chronological holdout within captured history:
  13 complete days for 24 pairs, 7 for the three gold pairs. Many correlated
  pairs were inspected. The hourly desk extends it every cycle.
- The shadow desk (D-18) is forward paper execution, not trading. Fills walk
  real Bitget books and use real mark prices, but our size never moves the
  book, and exits may be up to 3 hours after the hold ends. A single graded
  hold's net P&L is dominated by residual price noise; cost and funding
  comparisons are the informative part.
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
- The ledger is append-only by code and, from the first anchor onward, provably
  so: roots are stamped to Bitcoin (D-19). Rows logged before anchoring began
  are proven only from their first anchor. Web queries are not appended to it.
  Old rows are retained but marked superseded by the scorer.
- Qwen commentary is live on the site through a server route. Prompts cannot
  enforce factual correctness, so replies containing any digit are rejected and
  every number shown comes from the deterministic model.
- The route's rate limit is per serverless instance, not global; it slows casual
  abuse of the API key rather than enforcing a quota.
- The desk runs on GitHub Actions' hourly schedule, which GitHub treats as
  best-effort; a delayed or skipped cycle shows as a later "updated" time.
- solve.py (D-20) holds cost, residual risk and measurement noise fixed; a
  required carry is conditional on those, not a forecast that funding will rise.
- The on-chain gold check (D-21) is a sanity check, not a trading signal. An
  oracle and a Bitget perpetual clear through unrelated books and hours, so a
  non-zero basis is normal; the check reports its magnitude, not a verdict.
  XAUT has no Chainlink feed of its own on mainnet and is compared against
  the general XAU/USD feed instead of a token-specific one. A stale oracle
  (no update within its own published heartbeat, 24h for both feeds, times
  1.25) is flagged, not hidden; an unreachable RPC reports "unavailable",
  never a fabricated 0 bp.
- RWA contracts and clusters are not guaranteed economically interchangeable.
  Correlation/beta does not verify instrument identity or legal exposure.
- Legacy regime and decay utilities are exploratory. Shared legs invalidate an
  independent-pairs interpretation of their p-values. No 20x signal/noise claim.
