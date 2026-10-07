# Research desk review, 6 October 2026

## Changes

Removed repeated step numbers, repeated section headings and the duplicate scenario summary. Explore, Analyse and Notebook each have one primary heading. Notebook results show return, verdict and the limiting assumption first; calculation details expand on request. Older snapshots have a read-only state. Guided examples remain accessible across views. Restoring a cloud notebook no longer copies its private contents into the shared guest backup. Guest storage failures show an export warning.

## Verified

- Production build succeeds. All 25 account, research, routing and presentation tests pass.
- Browser checks: search, save/unsave pairs, saved filter, scenario selection, requirements, stress results, source inspection, keyboard tab navigation, share URL, notebook JSON export preview and scenario JSON export preview.
- Latest notebook result details expand and collapse without repeating the percentage as a second basis-point result.
- Desktop and 375 px mobile views have no document overflow in Explore, Analyse or Notebook.
- A live production research request comparing QQQ/TQQQ with SMH/SOXL returned both calculated scenarios and Qwen planning/commentary for the current 6 October snapshot.
- Existing guest notebook turns were preserved during checks.

## Not active or not fully verified

- Neon PostgreSQL is connected on the free plan and production account discovery is enabled on `getreef.xyz`. Real database save/reopen, account isolation, stale writes and trash restoration passed. Person-confirmed enrollment, sign-in, cross-device saving and backup restoration still require validation. See `validation/database-activation-20261006.md`.
- Email recovery is not configured.
- getreef.xyz is registered with Vercel nameservers and has authoritative DNS records, but public resolvers still returned NXDOMAIN during this review. HTTPS on that domain was therefore not verified.
- The in-app browser did not report a completed download. Correct JSON export previews were verified; downloaded files were not.
- Guided example completion and new blockchain proof validation were not exercised during this review.
- A compatible dependency update fixes the source-map-js advisory. Seven audit findings remain in Tailwind 3's build dependency chain (five high, two moderate); the available removal requires a Tailwind 4 migration. These packages process repository CSS and file patterns during development/build, rather than notebook requests. A migration and visual regression check remain outstanding.

These checks establish the listed behavior, not a guarantee that every possible path is free of defects.
