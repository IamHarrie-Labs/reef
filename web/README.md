# Reef website

React + TypeScript + Vite, with lucide-react icons.

```sh
cd web
npm ci
npm run dev
npm run build
npm run preview
```

- Home: `#/` — landing page: headline-vs-priced comparison and a live stats strip.
- Research: `#/desk` — pair watchlist (filter by Supported / Unproven / Saved, search,
  sort), scenario controls, evidence investigator, "what would make it work",
  stress tests, capacity chart, shadow desk, on-chain gold check, verdict-change feed.
- Method: `#/desk/method`.
- Evidence: `#/desk/evidence` — limitations, the full shadow ledger, and links for
  verifying the Bitcoin anchors yourself.

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
third-party video is used. Fonts load from external CDNs and need network access.
Reduced-motion mode disables the hero drift and entrance animations. Saved pairs stay in
local browser storage. No trade or account connection is ever initiated.

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
in JavaScript. A snapshot change requires a new notebook.
