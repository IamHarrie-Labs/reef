# Fifteen-minute trader session

Status: protocol prepared; participant results pending.

## Before starting

Run `node web/scripts/prepare-validation.mjs` to create a frozen export and an observer answer key. Use the same snapshot across sessions. The live desk refreshes hourly; record the on-screen snapshot and regenerate the answer key from that exact export if it differs. Do not mark an answer wrong using a different snapshot. The supplied answer key uses the local export and is not automatically the current production snapshot.

Ask: “May I take anonymous notes? May I record the screen?” Recording is optional. Explain that Reef is under test, not the participant. Get separate agreement before publishing a quote. Give no walkthrough. Ask the participant to think aloud. Help only after they are stuck for one minute; log the hint and mark that task assisted.

## Tasks

1. Open https://getreef.xyz/desk. You are investigating QQQ/TQQQ and SMH/SOXL at $25,000 reference notional for 30 days. Decide which, if either, deserves more research. Explain your reasoning and one assumption you would check before relying on it. Allow five minutes.
2. Ask your own follow-up question. Do not read a prepared example to them. Record the exact wording, response and whether they found the answer useful. Allow two minutes.
3. Now consider funding reversing, then a seven-day hold. Ask them what changed and whether the same instruments and stress stayed selected. Ask whether the displayed base verdict also describes the stressed result. Allow two minutes.
4. Find what would have to change for one of these setups to qualify. Export the notebook, then find the recorded prediction-to-outcome example. Allow two minutes.
5. If accounts are activated, save a notebook, sign out and reopen it on another device. The participant confirms their passkey themselves. Otherwise record “blocked: accounts unavailable”; do not count this as a successful test.

## Closing questions

- What was confusing or misleading?
- What decision would this help you make in your current process?
- What would you use instead? Could it reach the same answer?
- What information is missing before you would use this again?
- Would you return next week? Why or why not?

## Scoring and interpretation

For each task record unassisted complete, assisted complete, incomplete, or blocked. A correct main answer names the actual verdict and binding constraint, distinguishes reference notional from collateral return, and names one real limitation. A stress answer must not imply a recomputed confidence interval or verdict. A saved notebook is successful only after it reopens with the same turns and context.

Record elapsed seconds from opening the desk to the first decision, exact questions, hints and misunderstandings. A task that exceeds its limit stays incomplete. Keep factual observation, verbatim feedback and interpretation in separate columns. Do not convert three sessions into claims about the entire market or improved trading performance.

Report all three sessions, including unsuccessful ones. State the snapshot used, who qualified, what changed after feedback, and whether the same task was retested. Do not report “time saved” without measuring the participant's existing process on a comparable task.
