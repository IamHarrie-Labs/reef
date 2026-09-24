# Reef

**Look past the headline yield. See what holds up.**

**Live desk → [reef-research-desk.vercel.app](https://reef-research-desk.vercel.app)** · [Evidence](https://reef-research-desk.vercel.app/#/desk/evidence) · [Decisions](DECISIONS.md) · [Limitations](LIMITATIONS.md) · [Architecture](ARCHITECTURE.md)

[![ci](https://github.com/IamHarrie-Labs/reef/actions/workflows/ci.yml/badge.svg)](https://github.com/IamHarrie-Labs/reef/actions/workflows/ci.yml) [![live desk](https://github.com/IamHarrie-Labs/reef/actions/workflows/desk.yml/badge.svg)](https://github.com/IamHarrie-Labs/reef/actions/workflows/desk.yml)

Bitget AI Base Camp Hackathon S2 · Track 3, AI Trading Desk · Open theme

---

Bitget lists perpetual futures on real-world assets: tokenized equities, ETFs, indices and gold. Pairs of them (SMH against SOXL, gold against tokenized gold) pay a funding differential that looks like free carry on a screen.

Reef asks whether that carry survives once you **walk the actual order book, pay fees both ways, and carry the residual price risk of the hedge**, and it answers from evidence rather than vibes.

| Example, $25k held 30 days | Headline yield | After cost and risk | Verdict |
|---|---:|---:|---|
| SMH / SOXL | +5.9% | **−29.1%** | Unfavourable |
| XAU / XAUT | +7.2% | +3.9% | Unproven (interval crosses zero) |

**Across 27 priced pairs at $25k / 30 days: 0 supported, 2 unproven, 25 unfavourable.** The desk refreshes hourly, so these figures change. The live site is the source of truth.

## What makes it different

1. **It answers "what would make it work", not just "no."** For every pair, size and hold, Reef inverts the verdict. It reports the funding rate the trade would need, the shortest hold that clears both tests, the largest size that does, and which constraint binds: cost, residual risk, or noise in the evidence. QQQ/SQQQ at $25k becomes viable after about **53 days**. SMH/SOXL would need **10×** today's funding, and holding longer never helps, because its residual risk grows as fast as its carry. ([`solve.py`](src/solve.py))

2. **It grades itself against live books.** Every 8 hours the shadow desk freezes a prediction for every pair, records a hypothetical fill by walking the live Bitget book, exits against the book when the hold ends, and fetches the exchange's mark price at each funding settlement in between. That tests the one thing a backtest can't: does the predicted execution cost show up in a later book? No orders are ever placed. ([`shadow.py`](src/shadow.py), [`score.py`](src/score.py))

3. **Its predictions are provably frozen before their outcomes.** Every ledger row and every shadow execution is hashed into a Merkle root and stamped to **Bitcoin** with OpenTimestamps. A prediction under a confirmed root existed before that block. Anyone can check the proof at [opentimestamps.org](https://opentimestamps.org) without trusting this repo. ([`anchor.py`](src/anchor.py), [`data/anchors`](data/anchors))

4. **The AI explains; it never calculates.** Qwen parses questions and interprets frozen evidence through a private server route. Every number comes from the deterministic Python model. A Qwen reply containing any digit is rejected before display, and it must fill a fixed four-field schema: finding, binding constraint, what would change it, next check. ([`api/investigate.js`](api/investigate.js), [`llm.py`](src/llm.py))

5. **It is a live desk, not a snapshot.** A GitHub Actions job runs every hour: it refreshes funding, books and candles, advances the shadow desk, re-prices every pair, anchors the record, and publishes. The site reads the newest export directly, and a feed shows which verdicts moved and why. ([`desk.yml`](.github/workflows/desk.yml))

## How a verdict is made

```
question ─► parser (Qwen, validated against known symbols; rules fallback)
         ─► signed pair: A = −β·N, B = +N, β fitted on earlier prices only
         ─► funding holdout: direction chosen on the first 60% of complete days,
             evaluated on the untouched 40%
         ─► cost: walk both books at the actual size, fees in dollars
         ─► risk: residual spread volatility, √t
         ─► verdict: SUPPORTED only if Sharpe > 0.5 AND its 95% interval excludes zero
         ─► ledger (append-only, Bitcoin-anchored) ─► explanation
```

| Verdict | Meaning |
|---|---|
| **Supported** | Clears the 0.5 bar, and the autocorrelation-adjusted 95% interval excludes zero. Conditional support, not a promise. |
| **Unproven** | Clears the bar on the point estimate, but the interval crosses zero. Not evidence of an edge. |
| **Unfavourable** | Does not clear the bar after cost and risk. |

## Verify it yourself

No API key, no account, no network required:

```bash
git clone https://github.com/IamHarrie-Labs/reef && cd reef
python src/test_accounting.py     # 20 accounting tests: signed weights, dollar costs, scoring
python src/test_shadow.py         # shadow desk and Bitcoin anchor, end to end
python src/solve.py               # what would make each pair supported
python src/reef_index.py          # every pair, verdict and 95% interval
python src/verdict.py "Is SMH/SOXL worth \$25k over 30 days?"
```

Check that a specific prediction was frozen before its outcome:

```bash
pip install opentimestamps-client
python src/anchor.py --verify "<ts>:<pair>:<hold>"   # Merkle proof for one ledger row
ots verify data/anchors/<id>.root.txt.ots             # the root is in Bitcoin
```

Run the site locally:

```bash
python src/export_web.py && cd web && npm ci && npm run dev
```

## What Reef does not claim

- **Shadow fills are hypothetical.** They walk real books and use real mark prices, but our size never moves the book.
- **Few settlement days.** Funding evidence is a short chronological holdout: 13 complete days for 24 pairs, 7 for the three gold pairs. The hourly desk keeps extending it.
- **Anchoring proves timing, not correctness.** It shows when a row existed. It does not stop a row being withheld before the first anchor.
- **The confidence interval covers funding uncertainty only.** Beta, cost and model-selection uncertainty are excluded, so the true interval is wider.
- **Returns are per reference notional, not return on margin.** Liquidation and collateral are not simulated.

Full list: [LIMITATIONS.md](LIMITATIONS.md). The two model bugs caught and corrected during the build, and why the old numbers were withdrawn rather than quietly replaced, are in [DECISIONS.md](DECISIONS.md) (D-15, D-17).

## Repository

```
src/model.py, capacity.py     signed-portfolio carry, cost and risk model
src/solve.py                  what would make each pair supported
src/shadow.py, score.py       forward test against live books; grading
src/anchor.py                 Merkle root of the record, stamped to Bitcoin
src/desk_cycle.py             one hourly cycle (run by .github/workflows/desk.yml)
src/llm.py, verdict.py        question parsing, frozen evidence, explanation
src/export_web.py             the only thing the website reads
api/investigate.js            Qwen route with the no-digits evidence guard
web/app/                      landing page and research desk (React + Vite)
data/                         market data, ledger, shadow executions, anchors
archive/                      superseded exploratory scripts, kept for history
```

MIT licensed. Research, not advice. Reef never places an order.
