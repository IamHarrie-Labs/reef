# Reef

**Look past the headline yield. See what holds up.**

**Live desk → [reef-research-desk.vercel.app](https://reef-research-desk.vercel.app)** · [Evidence](https://reef-research-desk.vercel.app/#/desk/evidence) · [Decisions](DECISIONS.md) · [Limitations](LIMITATIONS.md) · [Architecture](ARCHITECTURE.md)

[![ci](https://github.com/IamHarrie-Labs/reef/actions/workflows/ci.yml/badge.svg)](https://github.com/IamHarrie-Labs/reef/actions/workflows/ci.yml) [![live desk](https://github.com/IamHarrie-Labs/reef/actions/workflows/desk.yml/badge.svg)](https://github.com/IamHarrie-Labs/reef/actions/workflows/desk.yml)

Bitget AI Base Camp Hackathon S2 · Track 3, AI Trading Desk · Open theme

---

Bitget lists perpetual futures on real-world assets: tokenized equities, ETFs, indices and gold. Pairs of them (SMH against SOXL, gold against tokenized gold) pay a funding differential that looks like free carry on a screen.

Reef asks whether that carry survives once you **walk the actual order book, pay fees both ways, and carry the residual price risk of the hedge**, and it answers from evidence rather than vibes.

| Example, $25k held 30 days (snapshot 1 Oct 2026) | Headline yield | After execution costs | Verdict |
|---|---:|---:|---|
| QQQ / TQQQ | +23.2% | **+14.0%** | **Supported** (95% CI [0.26, 2.91], Sharpe 1.59) |
| SMH / SOXL | +5.7% | −34.6% | Unfavourable |

**Across 27 priced pairs at $25k / 30 days, a small handful clear the bar (1 on 1 Oct, 2 on 4 Oct), a few more are unproven, and most are unfavourable.** The desk refreshes hourly and the Supported set changes with it — the live site is the source of truth, not this page. What stays constant: a pair is only Supported if it survives its own 95% confidence interval, and the 1 Oct example above also survives a 50%-higher-risk stress test.

## Who uses it

Reef is for experienced perpetual-futures traders comparing a two-legged Bitget
RWA carry setup before opening it. The decision is concrete: at this reference
size and hold, does the setup deserve further research, and which assumption
would have to change? It does not manage margin or place an order.

## What makes it different

1. **It answers "what would make it work", not just "no."** For every pair, size and hold, Reef inverts the verdict. It reports the funding rate the trade would need, the shortest hold that clears both tests, the largest size that does, and which constraint binds: cost, residual risk, or noise in the evidence. That's exactly how QQQ/TQQQ went from "no" to **Supported** — not luck, a condition the solver already named. QQQ/SQQQ is close behind: viable at $10k past ~40 days. For some scenarios, the annualised risk-adjusted estimate remains below the threshold even over longer holds under fixed assumptions; the solver reports the required carry rather than promising that patience fixes it. ([`solve.py`](src/solve.py))

2. **It grades itself against live books.** Every 8 hours the shadow desk freezes a prediction for every pair, records a hypothetical fill by walking the live Bitget book, exits against the book when the hold ends, and fetches the exchange's mark price at each funding settlement in between. That tests the one thing a backtest can't: does the predicted execution cost show up in a later book? No orders are ever placed. ([`shadow.py`](src/shadow.py), [`score.py`](src/score.py))

3. **Its records have independently checkable timestamp proofs.** Every ledger row and every shadow execution is hashed into a Merkle root and stamped to **Bitcoin** with OpenTimestamps. A confirmed proof establishes that the root existed by its Bitcoin block. A before-outcome claim additionally requires that block time to precede the holding-period endpoint; Bitcoin timestamps are approximate. Anyone can check the proof at [opentimestamps.org](https://opentimestamps.org) without trusting this repo. ([`anchor.py`](src/anchor.py), [`data/anchors`](data/anchors))

4. **The AI explains; it never calculates.** The research notebook resolves comparisons, constraints, ranking and recorded stress tests through a shared server service. Follow-ups preserve instruments, size, hold and stress. Qwen interprets the task through a validated plan and explains the selected evidence; the scenario matcher keeps research available when Qwen is unavailable. The CLI uses validated Qwen parsing with a deterministic fallback. Every number comes from the deterministic Python model. A Qwen reply containing any digit is rejected before display, and it must fill a fixed schema: finding, trade-off and next check in the notebook; binding constraint and what would change it in the older single-scenario route. ([`api/investigate.js`](api/investigate.js), [`llm.py`](src/llm.py))

5. **It checks gold against gold, on-chain.** XAU, XAUT and PAXG all claim to track one ounce of gold. Every cycle Reef reads Chainlink's gold price feeds directly from Ethereum by contract call (`eth_call`, no key, no library) and compares them with Bitget's own price for each contract — a reference independent of Bitget and of Reef's own model. ([`onchain_gold.py`](src/onchain_gold.py))

6. **It is a live desk, not a snapshot.** A GitHub Actions job runs every hour: it refreshes funding, books and candles, advances the shadow desk, checks the on-chain gold basis, re-prices every pair, anchors the record, and publishes. The site reads the newest export directly, and a feed shows which verdicts moved and why. ([`desk.yml`](.github/workflows/desk.yml))

## How a verdict is made

```
question ─► research task + retained context (validated Qwen plan; rules fallback)
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

Cached calculations and regression tests need no exchange key or account. The on-chain check and online timestamp verification require network access:

```bash
git clone https://github.com/IamHarrie-Labs/reef && cd reef
python src/test_accounting.py     # 20 accounting tests: signed weights, dollar costs, scoring
python src/test_shadow.py         # shadow desk and Bitcoin anchor, end to end
python src/solve.py               # what would make each pair supported
python src/reef_index.py          # every pair, verdict and 95% interval
python src/onchain_gold.py        # gold contracts vs Chainlink, direct eth_call
python src/verdict.py "Is SMH/SOXL worth \$25k over 30 days?"
```

Check a ledger row’s inclusion, then verify the root timestamp. Compare the confirmed block time with that row’s holding-period endpoint before making a before-outcome claim:

```bash
pip install opentimestamps-client
python src/anchor.py --verify "<ts>:<pair>:<hold>"   # Merkle proof for one ledger row
ots verify data/anchors/<id>.root.txt.ots             # the root is in Bitcoin
```

Run the site locally:

```bash
python src/export_web.py && cd web && npm ci && npm run dev
```

## A complete research conversation

1. Ask: “Compare QQQ/TQQQ with SMH/SOXL at $25k for 30 days.”
2. Follow up: “What if funding reverses?”
3. Change the horizon: “Now use a 7-day hold.”
4. Ask: “What would need to change?”
5. Export the notebook with its questions, resolved scenarios, dated cells and
   interpretations. Notes stay in browser storage; submitted questions and recent
   context are sent to the research service and, when available, Qwen.

Comparisons use one frozen export. Stress results are labelled separately from
base verdicts; no stressed confidence interval or verdict is claimed. If a newer
snapshot replaces the current evidence, the saved notebook remains exportable
and asks the user to start a new notebook before making another comparison.
Notebook turns are not appended to the prediction ledger or Bitcoin-anchored.

The shadow scheduler now retains complete **captured** entry and exit books for
future fills. Content-addressed compressed snapshots are referenced by hashes
in frozen predictions and execution records. Reproduce a future completed fill:

```sh
python src/book_evidence.py --replay "<timestamp>:<pair>:<hold>"
```

Legacy fills still lack original books; no old record is retroactively presented
as replayable. The archive binds captured content, not exchange authenticity.

## Forward evidence with a baseline

The evidence page leads with mean absolute execution-cost and funding-carry
errors. It also shows net direction agreement beside the same-sample baseline
of always predicting a nonpositive outcome, plus positive prediction/outcome
counts. Zero counts as nonpositive. These are descriptive comparisons: repeated
holds and pairs with shared legs are dependent observations.

The [portable case study](evidence/CASE_STUDY.md) uses the earliest eligible
completed shadow record, without selecting for agreement or profit. Download
its bundle from the evidence page or use `data/case_study.json`, then run:

```sh
python -m pip install -r requirements-proof.txt
python src/case_study.py --verify data/case_study.json --online
```

This recomputes the result and verifies the prediction and outcome proofs.
Original full books were not retained per record, so recorded fills cannot
independently establish available depth. Actual target-user validation remains
pending; [the protocol](VALIDATION.md) records no invented participant results.

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
src/onchain_gold.py           gold perps vs Chainlink, read directly from Ethereum
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
