<div align="center">

# Reef

### Is this tokenized-equity yield real, or does it only look real?

[![CI](https://github.com/IamHarrie-Labs/reef/actions/workflows/ci.yml/badge.svg)](https://github.com/IamHarrie-Labs/reef/actions/workflows/ci.yml)
[![Pairs priced: 25](https://img.shields.io/badge/pairs_priced-25-555555)](evidence/)
[![Clearing Sharpe 0.5: 0](https://img.shields.io/badge/clearing_Sharpe_0.5-0_of_25-8b2f27)](#the-headline-result)
[![Verdicts logged: 73](https://img.shields.io/badge/verdicts_logged-73-555555)](data/ledger.jsonl)
[![Parser tests: 9 passing](https://img.shields.io/badge/parser_tests-9_passing-555555)](src/test_llm_parsing.py)

Bitget lists **321 perpetual contracts flagged `isRwa: YES`** — tokenized US equities, ETFs, indices and leveraged products, trading 24/7 against underlyings that close for two days a week. A funding-yield screen shows a wall of attractive numbers. Reef prices each one against real execution cost and residual risk, and tells you which survive.

Built for Bitget AI Base Camp Hackathon S2 · Track 3, AI Trading Desk · Open Theme.

**[Live demo](https://claude.ai/code/artifact/6c4715c5-1b92-40f2-a7dd-2246c66afb1f)** · [Verify it yourself](#verify-it-yourself-in-60-seconds) · [The finding](#the-finding-the-one-edge-that-cleared-the-bar-decayed) · [Evidence](evidence/) · [Decisions](DECISIONS.md) · [Limitations](LIMITATIONS.md)

</div>

---

## Verify it yourself in 60 seconds

No API key, no account, no network. Every number in this README regenerates from cached data committed in this repository:

```bash
git clone --depth 1 https://github.com/IamHarrie-Labs/reef && cd reef

python src/test_llm_parsing.py   # 9 parser regression tests, ~1s
python src/screen.py             # naive yield ranking vs fully-priced ranking
python src/edge_decay.py         # the winner's-curse result, both funding windows
python src/mirage_index.py       # all 25 pairs scored
```

Ask it something in plain English:

```bash
python src/verdict.py "Is SMH/SOXL real for $25k over 30 days?"
```

Every verdict prints the complete evidence object first — **every number the explanation is permitted to use** — then the verdict. The LLM never sees a figure it can restate incorrectly, because it is handed the arithmetic already done.

## Contents

- [The problem](#the-problem)
- [What Reef is](#what-reef-is)
- [The headline result](#the-headline-result)
- [The finding: the one edge that cleared the bar decayed](#the-finding-the-one-edge-that-cleared-the-bar-decayed)
- [Who this is for](#who-this-is-for)
- [Explore without running anything](#explore-without-running-anything)
- [Regime dependence](#regime-dependence)
- [The model](#the-model)
- [Architecture](#architecture)
- [Engineering decisions & the hard problems](#engineering-decisions--the-hard-problems)
- [What's real, and what I deliberately did not claim](#whats-real-and-what-i-deliberately-did-not-claim)
- [Run it](#run-it)
- [Project layout](#project-layout)

## The problem

A trader looking at RWA perpetual funding rates is shown gross yield and nothing else. The tooling around that number is thin in four specific ways:

- **Cost is invisible.** A 30% gross annualised yield on a pair whose round-trip execution costs 115bp is not a 30% trade, and no screen says so.
- **Risk is mismeasured.** Funding volatility is not the risk being carried — the beta-hedged price spread is, and it is roughly two orders of magnitude larger.
- **Capacity is unstated.** A yield that exists at $1,000 may not exist at $100,000, and the book decides that, not the funding rate.
- **Nothing is graded.** A screen that recommended a trade last month has no record of whether it was right, and no incentive to keep one.

## What Reef is

A pricing engine that takes a plain-English question about an RWA perpetual pair and returns a verdict with every number it used. The loop:

<div align="center">

**`ASK → PRICE → FREEZE → EXPLAIN → GRADE`**

</div>

1. **Ask** — free text in. A rule-based parser (LLM-assisted when a key is configured) resolves the pair, notional and holding period.
2. **Price** — deterministic arithmetic only: OLS hedge ratio fitted in-sample, funding differential in both directions, beta-hedged residual volatility, and a live order-book walk for execution cost.
3. **Freeze** — the verdict is appended to an immutable ledger **before** any language model sees it, so a later grade checks a prediction fixed before its outcome existed.
4. **Explain** — the LLM receives the finished evidence object and a system prompt restricting it to fields already present. It cannot compute, re-round, or introduce a figure.
5. **Grade** — once a verdict's holding period elapses, `score.py` scores it against realised prices. 52 verdicts at 1- and 3-day holds are currently maturing.

## The headline result

**0 of 25 pairs clear Sharpe 0.5.**

The best is SMH/SOXL at **0.21** — a 30.1% gross annualised funding yield, 16.1% net, and still not worth taking once 2,159bp of 30-day residual-spread risk is priced against it.

Every one of the 52 verdicts logged at 1- and 3-day holds priced **MIRAGE**. That is the model's core asymmetry working rather than failing: execution cost is paid once, so a holding period too short for carry to accumulate past it can never be viable, however attractive the gross yield.

## The finding: the one edge that cleared the bar decayed

Two days before writing this, on a funding window ending 2026-09-16, exactly one pair passed: **XAU/XAUT at Sharpe 1.44**.

Bitget's funding endpoint serves only the most recent 100 intervals, so every refresh rolls the window forward and becomes an **unplanned out-of-sample test**. On the window ending 09-21 — same pair, same model, same hedge ratio, nothing re-fitted:

| | earlier window | current window |
|---|---:|---:|
| Gross annualised | 7.0% | 3.9% (**56% retained**) |
| Funding consistency | 68% | 57% |
| Residual vol | 2.66 bp/hr | 2.69 bp/hr (unchanged) |
| **Sharpe** | **1.44** | **0.21** |

The carry decayed. The risk did not.

And critically — **the rest of the book held**. Median gross edge retained across all 18 comparable pairs was **99%**, with 12 of 18 keeping more than 80%. The pair that decayed hardest was the one the model had selected.

That is the winner's curse, measured live on this project's own headline result. The pair that looked best was the one most flattered by sampling noise, and it regressed. Reproduce it with [`src/edge_decay.py`](src/edge_decay.py) — both funding windows ship in the repo (`data/funding` and `data/funding_prev`, the latter recovered from git history).

The windows overlap by about two weeks, so this is **not** a clean independent test. But a pair whose edge halves across a *partly overlapping* window was never carrying a stable edge.

## Who this is for

Retail and semi-professional RWA-perp traders sizing **$1k–$250k**, holding days to a couple of months, who look at a funding-rate screen and cannot tell which numbers survive opening the position.

Not a market-maker (this does not quote or provide liquidity) and not an institutional desk (no portfolio margin, no prime brokerage). The person this is built for is the one currently making the call by eyeballing a gross-yield column.

## Explore without running anything

| Open | Ask / look for | What it establishes |
|---|---|---|
| [Live demo](https://claude.ai/code/artifact/6c4715c5-1b92-40f2-a7dd-2246c66afb1f) | "Is SMH/SOXL real for $25k over 30 days?" | The best-scoring pair in the book still prices to Sharpe 0.21 — a 30% gross yield not worth taking |
| Same page | Click **XAU/XAUT** in the index | The pair that cleared the bar two days earlier and no longer does |
| Same page | Capacity-curve panel | Net return by size × holding period, drawn to scale |
| [`evidence/edge_decay_*.txt`](evidence/) | — | 99% median edge retained across the book, 56% for the one selected pair |
| [`evidence/funding_regime_*.txt`](evidence/) | — | Funding edge collapsing 23× from US market hours to weekend |

## Regime dependence

- **Funding edge collapses when the underlying market is shut.** RTH 0.843 bp/interval → weekend 0.036, a **23× decline** (n=28 pairs). Overnight sits at 0.850, level with RTH — so the effect is specifically the *weekend*, not "market closed" generally.
- **Tracking error rises 2.89×** from RTH to weekend (÷ own volatility), 26 of 27 pairs weekend-worst.
- The hackathon's framing — that round-the-clock trading is the opportunity — is the **opposite** of what this data shows for these instruments. Signal falls and noise rises at the same time.

## The model

Three P&L components. Only two scale with holding period:

| Component | Scales with holding period | Source |
|---|---|---|
| Funding carry | yes, linearly | `history-fund-rate`, 8h intervals |
| Residual spread drift (risk) | yes, as √t | hourly closes, beta-hedged |
| Execution cost | **no — paid once** | live order-book walk + taker fees |

That asymmetry is the whole point: a trade that loses money round-tripped every six hours can make money held for a month, and the capacity curve is where those two facts meet.

Risk is the residual spread, **not** funding volatility — pricing SMH/SOXL on funding volatility alone flatters it by roughly two orders of magnitude against the 0.21 it earns once residual-spread risk is charged. See [`DECISIONS.md`](DECISIONS.md).

## Architecture

```mermaid
flowchart LR
    Q["Natural-language question"] --> P["Parse\n(rules, LLM-assisted)"]
    P --> C["capacity.analyse_pair()\ndeterministic"]
    C --> H["hedge_ratio()\nOLS beta, in-sample fit"]
    C --> F["funding_edge()\nboth directions"]
    C --> R["residual_vol()\nbeta-hedged, out-of-sample"]
    C --> W["round_trip_cost()\nlive book walk + fees"]
    H --> L["ledger.append()\nBEFORE synthesis"]
    F --> L
    R --> L
    W --> L
    L --> S["LLM synthesis\nscoped to evidence only"]
    S --> V["Verdict: REAL or MIRAGE\n+ every number shown"]
```

The pricing math is pure deterministic arithmetic and runs identically with or without an LLM — `llm.py`'s template fallback proves this by construction.

The web demo does **not** reimplement the model in JavaScript. `export_web.py` runs the real Python pipeline and exports a precomputed grid the page looks up against, so the browser cannot silently diverge from the validated model.

## Engineering decisions & the hard problems

Full write-ups in [`DECISIONS.md`](DECISIONS.md). The ones that changed the result:

| Decision | Why it mattered |
|---|---|
| Risk priced on residual spread, not funding volatility | Changed SMH/SOXL's Sharpe by ~2 orders of magnitude. Getting this wrong makes every trade look viable. |
| Execution cost amortized once, not per interval | Makes the capacity curve non-trivial — the same trade flips viability between a 1-day and 30-day hold. |
| Hedge ratio fitted in-sample only, held fixed out-of-sample | Leveraged products recovering their true multiples out-of-sample (TQQQ 2.89, SOXS −3.72, TSLL 1.99) is what validated the pipeline. |
| Ledger written before LLM synthesis | A grade only means something if the prediction was frozen before the outcome existed. |
| The original hedge-survival concept was killed by a data check | All 2,241 Bitget spot symbols checked: zero RWA-linked. The concept required a spot leg that does not exist, so it was dropped rather than faked. |

## What's real, and what I deliberately did not claim

Full detail in [`LIMITATIONS.md`](LIMITATIONS.md).

**Real:** every price, funding rate and order book comes from Bitget's public endpoints. Nothing is synthetic or simulated. 117 days of hourly closes, 100 funding intervals, 25 pairs priced. The winner's-curse result is a genuine measurement on two real windows.

**Deliberately not claimed:**

- **No headline is a profitable strategy.** 0 of 25 pairs clear the bar. This tool finds that most apparent edges are not real; it does not claim to have found one that is.
- **The edge-decay windows overlap** by ~2 weeks. Directional evidence, not an independent test.
- **Execution cost rests on one book snapshot per pair**, taken during US regular hours — the most liquid window. Closed-market cost is measured separately in `cost_by_regime.py` and is still accumulating.
- **The adverse-selection question is open, not answered.** At the committed snapshot it had 8 data points. A correlation on 8 points is noise, and the evidence file says so rather than reporting a number.
- **Self-scoring has produced no grades yet.** 73 verdicts are logged; the 52 short-hold ones mature 09-22 and 09-24. Until then the self-scoring claim is a mechanism, not a result.
- **No confidence intervals** are reported on the headline Sharpe figures. With ~5 weeks of funding history they would be wide.

## Run it

```bash
# Everything below runs against cached data — no network required
python src/screen.py             # naive vs priced ranking
python src/mirage_index.py       # full public index, 25 pairs
python src/capacity.py           # capacity curve, all pairs
python src/edge_decay.py         # winner's-curse result across funding windows
python src/funding_regime.py     # regime dependence
python src/verdict.py "Is XAU/XAUT real for $50k over 2 weeks?"
python src/demo.py               # full walkthrough

python src/test_llm_parsing.py   # 9 regression tests (CI runs these on push)
```

Live data (needs network):

```bash
python src/refresh.py            # refresh prices, funding, depth
sh src/run_recorder.sh &         # continuous book capture, self-healing
python src/cost_by_regime.py     # execution cost by regime, from recorder series
python src/score.py              # grade matured verdicts
```

## Project layout

```
src/
  model.py, capacity.py         deterministic pricing model
  screen.py, mirage_index.py    naive-vs-priced ranking, public index
  llm.py, verdict.py            NL parsing + synthesis, orchestration
  ledger.py, score.py, log_batch.py   self-scoring
  edge_decay.py                 out-of-sample edge persistence
  funding_regime.py             regime dependence
  adverse_selection.py          gap-vs-depth (needs recorder data)
  cost_by_regime.py             execution cost by regime
  depth_regime.py               open-vs-closed book comparison
  recorder.py, run_recorder.sh  live capture, self-healing wrapper
  refresh.py, export_web.py     data refresh, precomputed grid
  test_llm_parsing.py           regression tests
web/index.html                  the live demo
data/                           prices, funding (+ prior window), depth, timeseries
evidence/                       committed, re-runnable pipeline output
DECISIONS.md, LIMITATIONS.md    why it is built this way, and what it is not
```
