# Reef

Carry model + capacity curve for RWA perpetual pairs.

Prices a pair trade between two Bitget perpetual contracts tracking the same
underlying, and reports the size and holding period at which it still pays.

## The model

Three P&L components, only two of which scale with time:

| Component | Scales with holding period | Source |
|---|---|---|
| Funding carry | yes, linearly | `history-fund-rate`, 8h intervals |
| Residual spread drift (risk) | yes, as sqrt(t) | hourly closes, beta-hedged |
| Execution cost | **no — paid once** | live order book walk + taker fees |

That asymmetry is the point. A trade that loses money round-tripped every six
hours can make money held for a month, and the capacity curve is where those
two facts meet.

Risk is the residual spread, not funding volatility. A funding-only Sharpe
overstates these trades by roughly an order of magnitude.

## Files

- `src/model.py` — hedge ratio, funding edge, book walk, net carry
- `src/capacity.py` — capacity curve by size x holding period, pair ranking
- `src/screen.py` — naive yield screen vs fully-priced ranking
- `data/` — cached prices (83d hourly), 36 order books, 26 funding histories

## Findings

18 same-underlying pairs priced at $25k / 30-day hold:

- **1 of 18 clears Sharpe 0.5.** XAU/XAUT: 3.6% net, Sharpe 1.46, 68% sign consistency.
- The naive ranking and the fully-priced ranking are **inverted at the top**.
  Naive #1 (SMH/SOXL, 17.7% gross) prices to Sharpe 0.05 — its residual vol is
  76 bp/hr, so 30-day risk is 2048bp against 29bp of net carry.
  Naive #8 (XAU/XAUT, 7.0% gross) is the only real trade in the set.
- For XAU/XAUT the binding constraint is **holding period, not size**: breakeven
  is 13.1 days, and cost only rises 25.0 -> 37.1bp from $1k to $250k.

## Limits

Single depth snapshot taken during US regular hours (the most liquid window);
100 funding intervals (~33 days); hourly closes are not executable prices;
no borrow cost or margin requirement modelled; 83 days is one calm regime.

Weekend order books cannot be backfilled — they must be recorded live.
