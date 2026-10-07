# Trader validation — results pending

Target user: an experienced perpetual-futures trader who already understands
funding, paired positions, hedge ratios and execution costs, and wants to decide
whether a Bitget RWA carry setup deserves further investigation. Reef provides
research before placing a trade; it does not manage margin or execute orders.

No participant sessions have been reported for this exercise. Do not claim
three validated users, time saved, adoption, or improved trading outcomes until
the sessions below have actually happened.

The recruitment copy, detailed observer protocol and pending results sheet are in `evidence/validation/`. Run `node web/scripts/prepare-validation.mjs PATH_TO_EXACT_EXPORT` to prepare a frozen snapshot and observer answer key. The key is calculated evidence, not participant feedback. Include an independently worded participant question before showing suggested follow-ups.

## Recruit three people

Choose three people who fit that target user, preferably including someone
unfamiliar with Reef. Give them the task below without a walkthrough. Use the
same snapshot when comparing their answers; download it first because verdicts
change hourly. Ask permission before recording a session.

## Send this task

Open https://getreef.xyz/#/desk.

You are comparing QQQ/TQQQ and SMH/SOXL at $25,000 reference notional for 30 days. Use Reef
to decide whether the setup deserves further investigation. You do not need to
place a trade.

1. Ask the notebook to compare those pairs and state each base verdict.
2. Ask “What if funding reverses?” then “Now use a 7-day hold.” Check that both
   pairs and the selected stress remain in context. Explain which constraint
   prevents or supports each base scenario: execution cost, residual
   price risk, or uncertainty in the funding sample.
3. Find what would need to change for the setup to clear the threshold.
4. Name one assumption that could make the estimate misleading.
5. Export the research notebook and locate the prediction-to-outcome case study.

Tell us what you concluded and what, if anything, was confusing. Which part
would you use in your existing research process? What tool would it replace,
if any? If none, say none. Could you reach the same answer with your current
tools, and what would that process involve?

## Observe and record

Start the timer when the user opens the desk; stop when they state their answer.
Do not coach them. Record any hints separately. Allow at most ten minutes;
record incomplete sessions as incomplete. Judge the answer against the frozen
snapshot, not today's live result.

| Participant | Relevant experience | Snapshot UTC | Time | Tasks completed / 5 | Hints | What was confusing | Exact feedback | Would use / why |
|---|---|---|---|---|---|---|---|---|
| P1 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| P2 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| P3 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

Completion requires the participant to identify the selected scenario's verdict,
explain its actual constraint, find the solver condition, name a real limitation,
and locate/download the evidence. “It looks good” is not task completion.
Report the three observations individually; this small sample cannot establish
population-level demand or investment performance. Keep verbatim feedback
separate from our interpretation.
