# Reef UI and workflow review

Date: 6 October 2026. Scope: landing, onboarding, research desk, notebook,
methodology, evidence record and data/privacy page.

## Implemented

| Before | After |
| --- | --- |
| Hero and statistics with little explanation | Clear research action, real gross/net example, three-step workflow, verdict definitions and evidence boundaries |
| Tiny, light interface text and redundant navigation | Local regular/medium typography, larger research labels, consistent navigation, active page states and shared footer |
| No explicit first-use path | Dismissible and reopenable guide: frame a scenario, inspect, challenge and export |
| Scenario controls buried in the selected pair | Shared size/hold toolbar before the watchlist, with dated coverage and unpriced counts |
| Many analyses repeated in a long selected-pair panel | Overview, requirements, stress tests and source tabs; full reasoning and chart values remain available |
| Full forward-test ledger repeated under research | Dedicated Evidence page with section shortcuts, paper outcomes, case, on-chain check and expandable limitations |
| Every notebook turn open in a nested scrolling area | Latest result open, earlier turns expandable, visible question label and each result’s own scenario/snapshot |
| Starting a notebook replaced the current record | One previous notebook retained locally and recoverable, including after route changes or reload |
| Downloads could appear to do nothing in embedded browsers | Visible JSON fallback for scenario and notebook exports |
| “Live desk” applied to historical exported calculations | Explicit UTC snapshot date and relative age; source book timestamps remain inspectable |
| No shareable selected scenario | Instrument, reference size and hold in the URL; share action excludes notebook questions |
| Unused fonts downloaded from two third-party sources | System font fallbacks and no font CDN requests; original landscape remains static |

Financial cells, thresholds, accounting and research service arithmetic were not
changed by this presentation update. The UI preserves the distinction between
base verdicts and stress point estimates.

## Verification

- Production TypeScript/Vite/Worker build passed.
- 44 Python model/evidence regressions passed, including proof/tampering checks.
- 15 Node research/API tests passed, including context preservation, unchanged
  Python cells, unavailable model fallback and snapshot mismatch rejection.
- Browser checks covered desktop (1440px), tablet (768px), mobile (375px) and
  narrow mobile (320px). Root horizontal overflow was resolved on the 320px desk;
  wide comparison tables scroll within their own regions.
- Tested landing example to matching instrument/scenario; search with no results
  and recovery; pair selection; accessible tab arrow keys; mobile navigation
  Escape and focus return; comparison, funding reversal and shorter-hold follow-up;
  parsed notebook/scenario exports; source inspection and limitation disclosure.
- Core palette contrast: body 11.28:1, secondary text 5.98:1 on cream and 5.61:1
  on the analysis panel; verdict text 5.63–6.25:1; input border 3.56:1.

These are implementation and browser checks, not a complete accessibility
certification or evidence of usability with institutional customers. The desk
still presents historical research, assumes exit depth from the entry snapshot
in base estimates and does not simulate liquidation or place orders.

Production deployment: `dpl_5AqTyHU4WZjHrWukejEw3GreQSEj`, published to
https://reef-research-desk.vercel.app. Its Vercel TypeScript/Vite/Worker build
passed. The Evidence page shows all paper rows included in its export and
explicitly distinguishes that subset from the larger aggregate history.

Production smoke checks confirmed the final asset `index-Cp-0D2pj.js`, no root overflow at the mobile viewport, the portable case-study fallback and scenario retention through navigation/reload. A production comparison returned validated Qwen commentary using snapshot `2026-10-05 23:19Z`; its export is `evidence/ui/production-notebook.json`.

Production screenshots: `landing-desktop.png`, `desk-desktop.png`, `desk-mobile.png` and `evidence-mobile.png` in `evidence/ui/`.
