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
The question box itself matches a tracked pair, size and hold in the browser and snaps to
the nearest precomputed scenario, which it discloses.

## Assets

The hero is an original landscape image (`public/reef-hero-landscape.webp`); no
third-party video is used. Fonts load from external CDNs and need network access.
Reduced-motion mode disables the hero drift and entrance animations. Saved pairs stay in
local browser storage. No trade or account connection is ever initiated.

`archive/legacy.html` preserves the former single-page dashboard as a reference; it is
not part of the production build.
