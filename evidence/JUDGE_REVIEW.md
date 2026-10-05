# Reef: revised judge assessment

Assessed on October 5, 2026 against Bitget AI Hackathon S2 Track 3, AI Trading
Desk. Official focus: feature depth, research quality, LUI fluency and
personalized thesis. The organizer gives subjective judging criteria, not
percentage weights. The equally weighted score below is our assessment.

Source: https://bitget-ai.gitbook.io/bitgetai_hackathons2

| Criterion | Score / 10 | Evidence and remaining deduction |
|---|---:|---|
| Feature depth | 9.0 | Real Bitget funding, books and prices; shared model; solver; paired comparisons; recorded stresses; shadow desk; gold oracle check; portable timestamp proof. Future full-book retention is implemented and tested, but its remote hourly job awaits source publication. |
| Research quality | 8.8 | Untouched funding evaluation, explicit cost/risk accounting, conditional intervals, frozen snapshot identity, solver conditions, baseline-aware errors and an independently checked historical case. Short funding samples, dependent paper observations and possible incorrect AI prose still limit conclusions. |
| LUI fluency | 8.6 | Live Qwen plans and explanations now work; pairs, stress and hold survive follow-ups and browser reload. Unsupported requests fail without deleting previous turns. The scope remains a bounded research grammar and recorded scenario grid; unsupported questions require reformulation. |
| Personalized thesis | 8.8 | A clear target user and research question, custom reference size/hold, saved pairs, conversational comparisons and exportable dated notes. No observed trader adoption or portfolio-level personalization has been established. |

**Overall: 88/100**, compared with the earlier 78/100. This is a strong,
distinctive research-workbench entry. It is not an honest ten-out-of-ten claim
and does not establish a grand-prize rank without reviewing the competing field.

## What changed the score

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

Forty-six focused regressions pass: thirty-one Python and fifteen Node. Export
consistency matches twenty-seven pairs and thirteen hundred sixteen priced
cells after the latest data sync. Type checking and production builds pass.
The public proof bundle matches its local source byte-for-byte. Live comparison
planning and explanation completed in about five and a half seconds in one API
test; this is an observation, not an SLA.

The official guide lists September 27 as the submission deadline. This score
describes the current product and does not establish whether post-deadline
changes will count toward judging of the original submission.
