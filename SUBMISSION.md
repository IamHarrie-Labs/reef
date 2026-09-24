# Submission pack

Copy-ready text for the hackathon form, the X post and the demo video.
Numbers marked *live* change hourly. Re-read them from the site before you paste.

---

## Project name

Reef

## One-liner

Reef checks whether a Bitget RWA funding yield survives real execution costs and risk. When it doesn't, Reef says what would have to change, and grades its own predictions against the live book.

## Links

- Live desk: https://reef-research-desk.vercel.app
- Code: https://github.com/IamHarrie-Labs/reef
- Track: 3 — AI Trading Desk (Open theme)

---

## Project description

**The problem.** Bitget lists perpetual futures on real-world assets: tokenized stocks, ETFs, indices and gold. Pairs of them pay a funding differential that looks like steady carry on a screen. The screen leaves out three things: what it costs to enter and exit through the actual order book, the price risk the hedge still carries, and whether the funding sample is long enough to mean anything. A yield that ignores them is a headline, not an opportunity.

**What Reef does.** Ask a question in plain English, like "Is SMH/SOXL worth $25k over 30 days?" Reef prices the trade the way a desk would:
- It fits the hedge ratio on earlier prices only.
- It picks the trade direction on the first 60% of the funding history, then evaluates it on the untouched 40%.
- It walks both live order books at your actual size.
- It prices the residual risk of the hedge.

The verdict is **Supported** only when the risk-adjusted estimate clears 0.5 and its 95% confidence interval excludes zero. If the estimate clears 0.5 but the interval crosses zero, the verdict is **Unproven**. Everything else is **Unfavourable**.

**What makes it different.**
1. *It says what would make it work.* For every pair, size and holding period, Reef inverts the verdict and reports:
   - the funding rate needed;
   - the shortest hold that works;
   - the largest size that works;
   - which constraint binds: cost, risk, or noise in the evidence.

   Some trades only need patience. Some need 10× today's funding, because their residual risk grows as fast as their carry.
2. *It grades itself against the live exchange.* Every 8 hours a shadow desk freezes a prediction for every pair, records a hypothetical fill by walking the live Bitget book, exits against the book when the hold ends, and records the mark price at each funding settlement. It then compares predicted cost and carry with what the later book actually delivered. No orders are placed.
3. *Its predictions are provably frozen.* Every prediction and every execution is hashed into a Merkle root and stamped to Bitcoin with OpenTimestamps. Anyone can verify, without trusting us, that a prediction existed before its outcome.
4. *It's a live desk.* An hourly job refreshes funding, books and candles, advances the shadow desk, re-prices every pair and anchors the record. A feed shows which verdicts moved and why.

**Result (live).** Across 27 priced pairs at $25k / 30 days, none is Supported today. A small number are Unproven: the estimate is positive, but the sample can't yet separate it from zero. The rest are Unfavourable. SMH/SOXL is the widest gap: a positive headline yield becomes a double-digit annualised loss once the book is walked. Reef's value is in telling those apart, and in showing exactly which assumption would have to change.

**Built with.** Python for the deterministic model (no numerical libraries needed), React + Vite for the site, Vercel, GitHub Actions for the hourly desk, Qwen via the Bitget hackathon endpoint, and OpenTimestamps.

**Honest limits.**
- The funding holdout is short: 13 complete days for most pairs, 7 for gold.
- Shadow fills are hypothetical.
- The confidence interval covers funding uncertainty only.
- Returns are per reference notional, not return on margin.

Every limit is listed in `LIMITATIONS.md`. Every model correction made during the build, and why old numbers were withdrawn, is in `DECISIONS.md`.

---

## Role of the LLM in your project

Qwen (qwen3.8-max via the Bitget hackathon endpoint) has two narrow jobs:

1. **Understanding the question.** It turns free text into a structured request: which pair, what size, what holding period. Its output is validated against the list of instruments Reef actually tracks, and size and hold must be finite and positive. If Qwen is unavailable or returns something invalid, a deterministic parser takes over.
2. **Explaining frozen evidence.** After the deterministic model has priced the trade and written the prediction to the ledger, Qwen explains what the evidence means in four fixed fields: the finding, the binding constraint, what would change the answer, and the next thing to check.

The LLM **never produces a number**. Every figure on screen comes from the Python model. The server route rejects any Qwen reply that contains a digit, a missing field or an extra field, and shows the deterministic result instead. In the command-line path, every number in Qwen's prose is checked against the evidence object before it is shown.

We made this choice on purpose. In trading, a fluent model that invents a plausible number is worse than no model at all. Reef uses the LLM for what it's good at, reading intent and explaining reasoning, and keeps the arithmetic, the verdict and the audit trail deterministic, reproducible and anchored to Bitcoin.

---

## X post (you post this, from your account)

> Most "yield" on RWA perps is a headline.
>
> Built Reef for #BitgetHackathon: it walks the real @Bitget order book, prices hedge risk, and tells you whether a funding yield survives — and if not, what would have to change.
>
> It also grades itself live: every prediction is shadow-traded against the book and stamped to Bitcoin before the outcome exists.
>
> 🔗 reef-research-desk.vercel.app
> @Bitget_AI

Shorter alternative:

> Reef: an AI trading desk that says "no" to fake yield — with receipts.
> Live Bitget books · shadow-traded predictions · proofs anchored to Bitcoin.
> #BitgetHackathon @Bitget_AI
> reef-research-desk.vercel.app

---

## Demo video script (about 2.5 minutes)

Record at 1080p. Use the live site. Speak plainly.

| Time | Screen | Say |
|---|---|---|
| 0:00 | Landing page, hero card | "This pair advertises a positive yield. After walking the real order book and pricing the hedge's risk, it's a loss. Reef is built to catch that." |
| 0:15 | Click *Open the desk* | "Reef prices 27 real-world-asset pairs on Bitget: tokenized stocks, ETFs and gold. It refreshes every hour." |
| 0:30 | Type "Is SMH/SOXL worth $25k over 30 days?" and submit | "I ask in plain English. Qwen reads the question. Every number that comes back is from a deterministic model." |
| 0:45 | Scroll the right panel: Investigator, then Failure path | "Gross carry, minus a round trip through the actual book, minus residual risk. Here's exactly where it breaks." |
| 1:00 | *What would make it work* card | "Most tools stop at no. Reef inverts the answer. This one needs ten times today's funding, and holding longer won't save it, because the risk grows as fast as the carry." |
| 1:15 | Click QQQ/SQQQ in the watchlist | "This one is different: at $25k it becomes viable after about 53 days. That's something a trader can act on." |
| 1:30 | Qwen interpretation panel | "Qwen explains the finding, what binds, and what would change it. It isn't allowed to write a single digit; if it tries, the reply is rejected." |
| 1:45 | Scroll to *The shadow desk* | "Every 8 hours Reef shadow-trades every pair against the live book, then grades itself: predicted cost against what the book actually charged." |
| 2:05 | Open `data/anchors` on GitHub, then opentimestamps.org | "Each prediction is hashed and stamped to Bitcoin before its outcome exists. You don't have to trust us; you can verify it." |
| 2:20 | *What changed* feed | "And because it's live, verdicts move. This pair went from Unfavourable to Unproven as its funding widened. Reef: look past the headline yield." |

Tips: before recording, run the desk workflow manually so "updated" reads minutes ago. If the shadow desk has graded trades by then, linger on the predicted-vs-realised numbers. They are the strongest ten seconds in the video.
