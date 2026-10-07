# Reef website

React + TypeScript + Vite, with lucide-react icons.

```sh
cd web
npm ci
npm run dev
npm run build
npm run preview
```

- Home: `#/` — landscape hero, dated gross-vs-net comparison, workflow,
  evidence verdict definitions, research provenance and limitations.
- Research: `#/desk` — pair watchlist (filter by Supported / Unproven / Saved, search,
  sort), a selected-scenario answer before the watchlist, shared scenario controls,
  an optional four-step guided example and analysis tabs
  for overview, requirements, stresses and source data. Public scenario links
  preserve instrument, reference size and hold. Notebook questions are not included.
  Gross and net returns lead with percentages over the selected hold. Annualised
  estimates remain secondary in the detail panel. Percentage display converts
  exported basis points; it does not recompute the model.
- Method: `#/desk/method` — calculation stages and a plain-language glossary.
  This page remains usable when the evidence service is unavailable.
- Evidence: `#/desk/evidence` — timestamped case, paper-execution ledger,
  on-chain gold reference, verdict changes and expandable limitations.
- Data & privacy: `#/privacy` — local storage, submitted question processing,
  exports and service boundaries.

## Data

The site never prices anything in the browser. It reads `web_export.json`, written by
`python src/export_web.py`. In production it loads the newest of the bundled copy and
the live copy on `main` (refreshed hourly by `.github/workflows/desk.yml`), so the
page updates without a redeploy. `python src/test_export_consistency.py` checks that
every exported scenario matches the Python calculator.

## AI

Qwen explains a frozen evidence object through `api/investigate.js`, a server route that
holds the API key. It returns four fixed fields and any reply containing a digit is
rejected; the numbers on screen always come from the deterministic model. If the route is
unreachable or rejects a reply, the page shows the calculated result without commentary.
The notebook uses `/api/research` for validated task planning and evidence selection.
Comparisons, rankings, constraint questions and recorded stresses preserve context
across turns. Qwen can interpret the task and explain the returned evidence; a
scenario matcher and the recorded calculations remain available without it.
Nearest-scenario snapping is disclosed. Notes are saved locally and exportable.
Each submitted question and recent context are sent to the service and Qwen when
available. `REEF_QWEN_DISABLED=1 npm run dev` starts an offline research preview
without contacting Qwen. The older `/api/investigate` route remains compatible.

## Assets

The hero is an original landscape image (`public/reef-hero-landscape.webp`); no
third-party video is used. The approved Reef Seal is a vector asset in
`public/brand/reef-seal.svg`, shared across the navigation, mobile menu, footer,
favicon and touch icon. The wordmark and UI labels use sentence case.
Typography uses self-hosted Space Grotesk through Fontsource, with Arial/sans-serif
fallbacks and no font CDN requests. Its OFL license is included in `public/brand/`.
The landscape slowly zooms in and out. Reduced-motion
mode disables the zoom, entrance animations and optional smooth scrolling. Saved pairs,
guide preference and guest notebooks stay in local browser storage. Optional passkey accounts save explicitly selected notebooks to PostgreSQL. No trade connection is initiated. `app/institutional.css` supplies the shared legibility,
interaction and responsive presentation layer over the original design.

`archive/legacy.html` preserves the former single-page dashboard as a reference; it is
not part of the production build.

## Forward evidence and downloadable case

The shadow panel leads with execution-cost and funding-carry mean absolute errors,
then compares direction agreement with an always-nonpositive baseline on the same
records. The evidence page expands errors by pair.

The prediction-to-outcome case comes from `data/case_study.json`, embedded in the
export. Its download includes the complete records, funding histories and both
OpenTimestamps proofs. Build it deliberately with `python src/case_study.py --build`
after installing `requirements-proof.txt`; normal hourly exports retain the fixed
case. See `evidence/CASE_STUDY.md` for verification and limitations.

The research service is shared by Vite, Vercel and the Worker in
`web/research/core.mjs`. `node --test web/research/core.test.mjs` covers context,
comparisons, stress selection, unavailable instruments, rejected AI plans and
numeric prose guards using mocked upstream responses. It does not certify live
model accuracy. Financial figures are copied from Python cells, not recalculated
in JavaScript. A snapshot change requires a new notebook with results; an empty
notebook adopts the latest snapshot automatically. Starting a notebook retains
one previous notebook in this browser for restoration. Earlier questions are
expandable; the latest result stays open. Every result displays its own scenario
and snapshot. Notebook and scenario exports include visible JSON when a browser
blocks downloading.

Saved notebooks retain their context when the watchlist changes. The summary
shows the next question’s instruments, size, hold and stress; the input repeats
that context and offers explicit actions to use the watchlist for the next question
or show a notebook instrument in the watchlist. A completed question does not
overwrite the watchlist’s controls. Guided examples start
a new notebook with the previous record retained, preserve an existing input
draft, and require the user to submit the prepared question. Completion provides
an export action beside the result. From `web`, run the display checks with
`node --experimental-strip-types --test scripts/research-presentation.test.ts`
(Node 22+). They check percentage units and verdict explanations, including
positive-but-unfavourable estimates.

## Landing artwork

The landing page combines the original landscape with two original generated Reef sculptures: layered evidence island and paper archive. Optimized WebP assets live in `public/art`; masters and final built-in generation prompts are documented in `../design/reef-landing/README.md`. Product diagrams use accessible HTML and link to the actual desk and method. Page copy uses sentence case without em dashes; dynamic commentary is formatted for display without changing stored evidence.

Typography: self-hosted Space Grotesk headings, Poppins body and controls, Instrument Serif italic accents. The landing workflow uses native sticky cards with ordinary vertical scrolling; reduced-motion users see a normal list. Coverage links are built from actual exported pairs and scroll automatically on a dark green strip, without heading, count or boxed cards. Motion pauses on hover or keyboard focus. Reduced-motion users receive a normal scrollable list. The archive section uses a white surface and the complete transparent cutout with a slowly orbiting marker that respects reduced-motion preferences.

## Research desk hierarchy

Scenario controls precede the selected result. The result presents one holding-period estimate, verdict and reason. The overview keeps the gross-to-net calculation visible; detailed metrics, reasoning and the holding-period chart expand on request. Requirements, stress tests and source data retain their own tabs. Saved notebook context remains independent of watchlist changes.

## Mobile presentation

Phones use a dedicated watchlist with pair, net return, verdict and save action visible together. Sorting, search and market filters use the same state as the desktop table. Controls use at least 44-pixel touch targets and 16-pixel form text. Smaller tablets use the navigation menu. Short landscape screens use an ordinary workflow list instead of sticky stacking. Comparison tables remain independently scrollable, with sticky row headings in the research notebook.

Responsive checks cover 320, 375, 430 and 768 pixels, plus 844-by-390 landscape. Landing, research, method, evidence and privacy pages were inspected; no document overflow was observed. Browser checks cover navigation, pair selection, sorting, searching, saving, scenario changes and expanding calculation details. These are browser viewport checks, not physical-device or real-user testing.

## Optional accounts

Passkey authentication and named cloud notebooks are configured on `https://getreef.xyz` with Neon PostgreSQL. Real database save/reopen, owner isolation, conflicting writes and trash restoration have passed; person-confirmed passkey enrollment and cross-device browser checks remain pending. Email recovery is not configured. See [account setup](accounts/README.md) for migrations, fixed-domain requirements and activation checks. Guest notebooks retain up to 200 turns; earlier results are never silently removed to make space. Cloud notebooks enforce version checks and owner-scoped access.

## Research workspace navigation

The CSS build now uses Tailwind 4's PostCSS plugin. Its full dependency audit reports zero advisories as of 6 October 2026. Browser checks are still required after future framework updates.

The research resolver recognizes explicit dollar/USDT amounts and removes named pairs from existing comparisons. Unsupported percentages, doubled costs/risk, combined shocks and multiple scenario alternatives ask for a supported or unambiguous question instead of returning an unchanged calculation. Request errors offer Edit question; temporary service errors offer Retry question. Cloud draft failures explicitly warn users to save or export.

Explore, Analyse and Notebook are separate views under `#/desk?panel=...`. Selecting a pair opens Analyse. Scenario controls and the watchlist belong to Explore; calculation details belong to Analyse; questions and account saving belong to Notebook. View changes preserve mounted notebook state and in-flight research. Browser Back and direct links restore the selected view. A header sign-in entry opens account controls; when infrastructure is missing it explains that passkey access is not yet available.
