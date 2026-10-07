# Operator research demonstration, 6 October 2026

This is engineering QA, not an independent trader session and not adoption evidence. The browser run used a separate local origin on port 5178 to preserve the user's production guest notebook. Financial evidence was frozen at 2026-10-05 21:53Z; Qwen requests used the configured live model.

## Actual sequence

1. “Help me compare QQQ/TQQQ and SMH/SOXL using 10000 USDT for two weeks. Which assumption is the problem?” Both pairs resolved at $10,000 and 14 days. Planning used Qwen; verified commentary was unavailable, so the numeric result and fallback disclosure remained visible.
2. “What if costs double?” The unsupported shock was rejected. The original turn and context remained intact.
3. “Use the recorded stress where execution costs rise by half.” Both pairs, size and hold remained intact; the selected stress changed. Live Qwen explanation was shown.
4. “Remove SMH/SOXL from this comparison and use a 7-day hold.” QQQ/TQQQ remained, at $10,000 and seven days, with the execution-cost stress preserved. Live Qwen explanation was shown.
5. “Funding falls 30 percent” was rejected with Edit question. The three successful turns remained intact. The visible JSON export contained all three turns and the final context.

The result is saved in `operator-demo.json`. Unsupported questions are listed separately because failed requests do not create research turns. A completed browser file download was not verified.

## Verification

- 26 Node account/research/route checks, six presentation/case checks and four Python evidence checks pass: 36 total.
- The fixed case verifier passes online canonical-height checks against two public explorers and recomputes accounting and timestamp inclusion.
- Tailwind 4 migration removes the seven remaining build dependency audit findings. The full and runtime npm audits report zero advisories.
- All seven page/view routes were inspected at 375 px. No document overflow was observed. Desktop notebook and evidence presentation were visually inspected.
- getreef.xyz returns HTTPS 200 and publicly resolves. Accounts still return disabled because PostgreSQL is absent.
- After deployment, getreef.xyz rejected “What if costs double?” with HTTP 400. “Remove SMH/SOXL and use 10000 USDT for 7 days” returned QQQ/TQQQ, $10,000, seven days and the existing execution-cost stress, with live Qwen planning and commentary. The actual response is in `production-check.json`.

## Still requiring external participation

- Database provider selection, provisioning and any provider terms. No database was created and no paid plan selected.
- Real PostgreSQL persistence checks using `web/accounts/check-database.mjs`, then person-confirmed passkey enrollment, cross-device reopening and recovery checks.
- Three qualified traders: recruitment copy, screening, observer protocol, pending results sheet and reproducible answer key are prepared. No outreach was sent and no feedback invented.
- Longer prospective evidence and demonstrated improvement over baselines. The fixed negative case does not establish an edge over always predicting a nonpositive outcome.
