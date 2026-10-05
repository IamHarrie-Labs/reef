# Submission pack

Copy-ready text for the form, X post and demo video. Live figures change hourly;
read them from the same snapshot immediately before recording or submitting.

## Project name and track

**Reef** · Track 3 — AI Trading Desk (Open theme)

- Live desk: https://reef-research-desk.vercel.app
- Code: https://github.com/IamHarrie-Labs/reef

## One-liner

Reef checks whether a Bitget RWA funding yield survives execution costs and hedge
risk, shows what would need to change, and compares frozen estimates with later
hypothetical execution — with downloadable Bitcoin timestamp proofs.

## Project description

**Who it serves.** Experienced perpetual-futures traders researching a two-legged
Bitget RWA carry setup before opening it. Their question is specific: at this
size and holding period, does the setup deserve further investigation?

**The problem.** A funding differential can look attractive while hiding entry
and exit costs, residual price risk, and a short or noisy funding sample. A gross
yield alone cannot answer whether the trade is worth researching.

**What Reef does.** Ask “Compare QQQ/TQQQ with SMH/SOXL at $25k over 30 days,” then follow up with “What if funding reverses?” Reef fits the hedge
ratio on earlier prices, chooses direction on the first 60% of funding history,
evaluates carry on the untouched 40%, walks captured books at the selected size,
and estimates residual spread volatility. Supported means the modelled
risk-adjusted estimate exceeds 0.5 and its approximate, funding-only 95% interval
excludes zero. Unproven clears the point threshold but not the interval test;
Unfavourable does not clear the point threshold. These are conditional research
verdicts, not realised trading Sharpe or promises of returns.

**What makes it different.**

1. **It explains the condition for a different answer.** The solver reports
   required carry, the shortest qualifying hold, the largest supported tested
   size, and the constraint that binds. Under fixed assumptions, some scenarios
   stay below the annualised risk-adjusted threshold even at longer holds.
2. **It exposes its estimation errors.** The shadow desk freezes one-day
   predictions every eight hours and three-day predictions daily, records
   hypothetical entry/exit fills against real Bitget books, and captures funding
   settlement marks. The evidence page leads with mean absolute cost and funding
   errors, including a breakdown by pair. Net direction agreement appears beside
   the same-sample baseline of always predicting a nonpositive outcome. A high
   agreement rate alone is not proof of skill; the current predominantly negative
   sample makes that baseline essential.
3. **It offers one complete, downloadable case.** The case is the earliest
   eligible completed shadow record by timestamp and record key, not a profitable
   or especially accurate example. It includes the frozen prediction, completed
   paper execution, archived funding observations, marks, Merkle paths, original
   OpenTimestamps proofs and Bitcoin headers. A verifier recomputes the accounting
   and checks the prediction block time against maturity. Online verification
   checks canonical block hashes with two public explorers.
4. **It keeps researching.** An hourly job refreshes data, advances the shadow
   desk, reprices scenarios and publishes verdict changes. The gold sanity check
   compares Bitget observations with Ethereum Chainlink feeds.

**What the evidence establishes.** Cost and funding prediction errors are
inspectable, and the selected prediction was committed to Bitcoin before its
holding period ended, using the block header's approximate timestamp. The case
shows a loss, which is useful evidence for a desk built to interrogate yield.
Timestamp proofs bind recorded content; they do not authenticate exchange data
or guarantee executable fills. Legacy records lack original full books, so this case reproduces accounting
rather than its original depth walk. Future shadow fills retain complete captured
books with content hashes and a fill-replay verifier.

**Built with.** Python, React + Vite, Vercel, GitHub Actions, Qwen via the Bitget
hackathon endpoint, and OpenTimestamps.

**Limits.** Shadow fills are hypothetical; returns use reference notional rather
than collateral; fees are assumptions; liquidation is not simulated. The
confidence interval covers funding uncertainty under fixed beta, cost and
volatility. Repeated holds and shared legs are dependent observations. Actual
three-person target-user validation remains pending; the protocol is in
VALIDATION.md. All limitations and model corrections are public.

## Role of the LLM

The website supports a research notebook: comparisons, ranking, solver conditions
and four recorded stresses. Qwen resolves a task into a validated plan, then
explains the selected evidence. Follow-ups preserve pairs, reference size, hold
and stress. Financial figures are selected from a single dated Python export.
Invalid plans fall back to the scenario matcher. Interpretation prose containing
digits or an invalid schema is discarded while calculated evidence stays visible.
The guard constrains numeric invention; it does not prove prose correctness.

The notebook is locally saved and exportable. Submitted questions and recent
context go to the research service and Qwen when available. Notebook turns are
separate from the Bitcoin-anchored prediction ledger.
The separate CLI path uses validated Qwen parsing with a deterministic fallback,
records its model evidence in the ledger, then requests an explanation. Browser
questions do not append new predictions to that ledger. All displayed financial
figures and verdicts come from Python, not the language model.

## X post — publish from your account

> Built Reef for #BitgetHackathon: a research desk for @Bitget RWA funding carry.
> Actual book costs, hedge risk, and what would need to change.
> Hypothetical execution, visible estimation errors, downloadable Bitcoin proofs.
> reef-research-desk.vercel.app @Bitget_AI

## Demo video — about 2.5 minutes

Record at 1080p. Read live numbers from the selected snapshot; do not assume a
particular pair is Supported or quote a fixed count from an older recording.

| Time | Screen | Say |
|---|---|---|
| 0:00 | Landing page | “A trader sees a positive funding yield. What survives entry and exit costs, and how much hedge risk remains? That is the question Reef answers.” |
| 0:15 | Research question | “Here is SMH/SOXL, $25k, 30 days. Compare it with QQQ/TQQQ at the same size and hold. The notebook keeps this context as we ask what changes if funding reverses.” |
| 0:35 | Investigator and solver | “This is the binding constraint. Here is the carry needed, shortest qualifying hold and largest tested size. These conditions hold the other assumptions fixed.” |
| 0:55 | Supported or Unproven filter | “Apply the same test across pairs. Supported requires both the point threshold and a funding-only interval above zero. Other uncertainty remains.” |
| 1:10 | Live Qwen interpretation | “Qwen explains the evidence. It plans the research task and explains the selected evidence. Follow-ups keep the scenario. Financial figures come from Python, and the export includes the entire notebook.” |
| 1:25 | Shadow desk | “We record hypothetical fills, then compare estimates with later books and funding marks. These are the cost and funding errors. Direction agreement is shown beside an always-nonpositive baseline.” |
| 1:45 | Case study, timeline and comparison | “This is the earliest eligible completed record. We did not select it for profit or agreement. The estimate and paper outcome differ; you can inspect both.” |
| 2:00 | Download bundle and verifier output | “Download the records, marks and proofs. This command recomputes the result and checks that the prediction's Bitcoin block time precedes maturity. Bitcoin timestamps are approximate.” |
| 2:20 | Case limitations, closing | “The proof binds recorded content. Fills remain hypothetical, and original full books were not retained per record. Reef makes the evidence, errors and limits visible before you trade.” |

Before recording, verify the downloadable bundle, read the current snapshot and
confirm the live site contains these changes. Do not claim the planned user
sessions have happened. Prefer a visible verifier result to an unexecuted
command or a directory of unexplained proof files.
