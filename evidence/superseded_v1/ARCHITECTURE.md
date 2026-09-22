# Architecture

## The one rule

> **The model decides what a number means. It never decides what the number is.**

Every figure in a Reef verdict — hedge ratio, funding edge, residual
volatility, execution cost, net carry, Sharpe — is produced by
deterministic arithmetic before any language model is invoked. The LLM
receives a finished evidence object and a system prompt restricting it to
fields already present in that object. It cannot compute, re-round, or
introduce a figure.

This is testable rather than asserted: `llm.py` ships a template renderer
that produces a correct verdict with no model available at all. If the
pricing depended on the LLM, that fallback could not exist.

## The dominant mechanism

```
natural-language question
  → parser resolves pair, notional, holding period
    → deterministic pricing: beta, funding edge, residual vol, book walk
      → verdict frozen into an append-only ledger
        → LLM explains the frozen evidence, bounded to its fields
          → verdict returned with every number it used
            → score.py grades it once the holding period elapses
```

And the model underneath it, in one line:

```
net = (funding carry × days) − (execution cost, paid once)
risk = residual spread volatility × √days
```

Two components scale with time and one does not. That asymmetry is the
entire product: it is why a trade can be unviable at a 1-day hold and
viable at 30, and why the capacity curve has a shape rather than a level.

## Component map

| Module | Owns | Never touches |
|---|---|---|
| `model.py` | hedge ratio, funding edge, residual vol, book walk, net carry | presentation, LLM, I/O beyond `data/` |
| `capacity.py` | size × hold grid, risk-adjusted return, max viable size | raw data fetching |
| `screen.py` | naive-vs-priced ranking | pricing logic (delegates to `capacity`) |
| `mirage_index.py` | the public 0–100 score and REAL/MIRAGE verdict | pricing logic |
| `intervals.py` | Wilson intervals, autocorrelation-adjusted `n_eff`, Sharpe CIs | point-estimate pricing |
| `edge_decay.py` | cross-window edge persistence | fitting anything new |
| `llm.py` | query parsing, prose synthesis | **any arithmetic on a price** |
| `verdict.py` | orchestration, evidence assembly | pricing, synthesis |
| `ledger.py` | append-only verdict log | reading outcomes |
| `score.py` | grading matured verdicts against realised prices | writing verdicts |
| `recorder.py` | live book/funding/mark capture | analysis |
| `refresh.py` | backfillable history (prices, funding, depth) | analysis |

Read that table by its gaps. `llm.py` has no access to pricing functions —
it is handed a dict. `score.py` cannot write to the ledger it grades.
`ledger.py` cannot read outcomes, so it has nothing to be biased by.

## What is backfillable and what is not

This distinction drives the whole data layer:

| Data | Backfillable? | Implication |
|---|---|---|
| Hourly closes | yes | `refresh.py` can rebuild 117 days on demand |
| Funding history | **partially** | The endpoint serves only the most recent 100 intervals. The window rolls — which is why every refresh is an unplanned out-of-sample test (see `DECISIONS.md` D-06) |
| Order-book depth | **no** | A book is a snapshot of *now*. `recorder.py` exists solely because a book at 03:00 UTC last Tuesday cannot be recovered at any price |

`data/funding_prev` holds an earlier funding window recovered from git
history, so the decay comparison stays reproducible after the live window
has rolled past it.

## The verdict path, in detail

1. **Parse** — `llm.parse_query()`. Rule-based by default; LLM-assisted
   when a key is configured, falling back to rules on any failure. Two
   historical bugs here are regression-tested (`DECISIONS.md` D-09).

2. **Resolve** — `verdict.resolve_pair()`. A single named ticker is
   resolved to its cluster-mate from `data/clusters.json`.

3. **Price** — `capacity.analyse_pair()`. Beta fitted in-sample, funding
   edge evaluated in both directions with the profitable one selected,
   residual volatility measured out-of-sample, execution cost from a book
   walk at the requested notional.

4. **Freeze** — `ledger.append()`. Timestamped, with the complete evidence
   object. This happens *before* step 5 and is the reason a later grade
   means anything.

5. **Explain** — `llm.synthesize()`. The evidence object is serialised
   into the prompt; the system message forbids any figure not present in
   it. On no key, or any error, the deterministic template renders instead.

6. **Grade** — `score.py`, later. Reconstructs the realised beta-hedged
   return over the verdict's stated window and checks the call. Verdicts
   whose holding period has not elapsed report `pending` rather than being
   silently skipped.

## The web demo

`web/index.html` is a static page. It performs **no pricing arithmetic**.

`export_web.py` runs the real Python pipeline and writes a precomputed
grid — every priced pair × 8 notionals × 7 holding periods — to
`web_export.json`. The page parses a question (parser ported
line-for-line from `llm.py`), snaps the request to the nearest grid point,
discloses the snap in the UI, and renders the result. Live explanation
comes from the artifact's `sample` capability, under the same
evidence-bounded prompt as the CLI.

The consequence is that the browser cannot silently disagree with the
model, and the cost is that it can only answer questions inside the grid.
That trade is `DECISIONS.md` D-08.

## Verification surface

| Claim | Check |
|---|---|
| Parser handles real phrasing | `python src/test_llm_parsing.py` — 9 cases, CI-gated |
| Pricing runs on cached data | `python src/capacity.py` |
| Headline ranking | `python src/screen.py` |
| Edge decay across windows | `python src/edge_decay.py` |
| Intervals and effective sample | `python src/intervals.py` |
| Whole pipeline still runs | `.github/workflows/ci.yml` on every push |

Everything above runs offline against committed data. Nothing in the
verification surface requires a key, an account, or a network call.
