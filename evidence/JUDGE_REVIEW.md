# Reef: revised judge assessment

Critically reassessed on October 6, 2026 against Bitget AI Hackathon S2 Track 3, AI Trading
Desk. Official focus: feature depth, research quality, LUI fluency and
personalized thesis. The organizer gives subjective judging criteria, not
percentage weights. The equally weighted score below is our assessment.

Source: https://bitget-ai.gitbook.io/bitgetai_hackathons2

| Criterion | Score / 10 | Evidence and remaining deduction |
|---|---:|---|
| Feature depth | 8.5 | Real funding, books, solver, comparisons, recorded stresses, paper outcomes, oracle checks and timestamp proofs. Passkeys/cloud notebooks remain inactive without a database; newer book-retention deployment is not established. |
| Research quality | 8.5 | Reproducible estimates, explicit cost/risk assumptions, dated evidence and honest limitations. Short holdouts, dependent observations and hypothetical fills limit confidence; predictive benefit beyond simple baselines is unproven. |
| LUI fluency | 8.0 | Live Qwen and retained context work on tested requests, with a calculation-only fallback. The supported research vocabulary is bounded. Harder QA exposed silent unsupported-shock and pair-removal failures, subsequently corrected. Real trader questions remain untested. |
| Personalized thesis | 8.0 | A specific paired-RWA funding question, chosen size/hold, saved pairs and contextual notebooks. No observed trader sessions, actual portfolio constraints or account-specific fees establish deeper personalization. |

**Overall: 82.5, rounded to 83/100.** The earlier 88 was too generous about
product completeness and demonstrated user value. The subsequent fixes improve
the product, but prepared test protocols are not completed validation. No grand-prize
rank can be established without the competing field and accepted submission materials.

## What changed the score

The critical reassessment gives more weight to unfinished account activation and
missing independent trader evidence. The 6 October follow-up fixes hard-question
resolution and error recovery, adds a baseline to the fixed prospective case,
verifies its proofs online and removes all current npm audit advisories. The domain
now works over HTTPS. Database activation and actual trader sessions remain pending.

The language interface now completes a research task rather than resolving a
single scenario. Live testing exposed a Qwen reasoning-mode latency issue,
incorrect stress wording, a development fetch cancellation race and restored
context being overwritten. These were fixed and verified. The evidence makes
the model's limits and estimation errors inspectable instead of treating a
high direction-agreement rate as predictive skill.

## Role-specific judgment

- Blockchain engineering: timestamp commitments and content-hash replay have
  precise claims. They do not authenticate exchange origin, prove actual fills,
  or turn notebook exports into Bitcoin-anchored predictions.
- UI/UX: comparison, follow-up, error and mobile flows work. The comparison is
  intentionally wide and horizontally scrollable on a phone. Research tables
  still require familiarity with carry, hedge risk and reference notional.
- Ecosystem: the Bitget RWA thesis is specific and practical. Validation with
  three experienced traders is the largest remaining product maturity gap.
- Hackathon judging: the deployed desk, complete task and captioned walkthrough
  show a runnable product. Source publication and real participant results are
  still explicitly pending.

## Verification boundary

The 6 October follow-up ran 36 focused checks: 26 Node account/research/route,
six presentation/case and four Python evidence regressions. The proof verifier
passed online checks against both public explorers. All seven page/view routes
were checked at 375 px without document overflow. The saved operator demo is QA,
not an independent trader session; one turn used calculation-only fallback and
two follow-ups displayed live Qwen commentary. See `validation/OPERATOR_REVIEW.md`.

The paragraph below records the previous October 5 check, not a new run of all
Python regressions today.

Forty-six focused regressions pass: thirty-one Python and fifteen Node. Export
consistency matches twenty-seven pairs and thirteen hundred sixteen priced
cells after the latest data sync. Type checking and production builds pass.
The public proof bundle matches its local source byte-for-byte. Live comparison
planning and explanation completed in about five and a half seconds in one API
test; this is an observation, not an SLA.

The official guide lists September 27 as the submission deadline. This score
describes the current product and does not establish whether post-deadline
changes will count toward judging of the original submission.
