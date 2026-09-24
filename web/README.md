# Reef website

React + TypeScript + Vite, with Tailwind and lucide-react.

```sh
cd web
npm ci
npm run dev
npm run build
npm run preview
```

- Home: `#/` — fixed navigation and a full-viewport video hero.
- Research: `#/desk` — the corrected pricing snapshot, filtering, sorting,
  local saved pairs, research questions, scenario controls and capacity curve.
- Method: `#/desk/method`.
- Evidence: `#/desk/evidence` — limitations and downloadable snapshot.

Deploy `dist/` as a static website. Hash navigation does not require server rewrites.
The Vite evidence plugin serves `web_export.json` in development and copies the
same file into the production build. Refresh the snapshot with
`python src/export_web.py` from the repository root, then rebuild the site.

The landing uses the exact video and font URLs from the supplied design brief.
No generated images or fake backers are used. External assets need network access;
video failure leaves readable copy on the cream background. Reduced-motion mode
pauses the video and disables entrance animations.

Browser questions use a local parser, not a live LLM. The dashboard displays
exported calculations and discloses rounding to the nearest scenario. Favorites
stay in local browser storage. No trade or account connection is initiated.
`archive/legacy.html` preserves the former single-page dashboard as a reference; it is
not an entry in the new production build.
