# Reef decision workflow update

Reviewed and implemented on 6 October 2026.

## Changes

- A selected-scenario summary leads with the holding-period return, evidence
  verdict, plain-language reason and a link to the relevant analysis.
- Gross and net percentages use the selected hold throughout the watchlist,
  detail panel and landing-page example. Annualised values remain secondary.
- Notebook comparisons distinguish base financial figures from stressed point
  estimates. Stress percentages convert recorded basis points; no stressed
  verdict or confidence interval is invented.
- Saved notebook context persists across watchlist changes. The next question’s
  instruments, size, hold and stress appear in the summary and above the input.
  Explicit actions adopt the watchlist or show a notebook pair in the watchlist.
  A completed question does not silently change the watchlist controls.
- An optional four-step example covers the selected result, requirements,
  a user-submitted stress question and an export. Starting its notebook retains
  the previous notebook. Existing input drafts are retained.

## Validation

- Production build and TypeScript checks passed.
- Fifteen research route/core regression tests passed.
- Three display tests passed: percentage units/sign/small values; verdict reasons
  for positive-but-unfavourable and zero estimates; uncertainty/unpriced states.
- Browser walkthrough completed the guided example, submitted its prepared
  question, checked the stress response, opened the export and restored the
  previous notebook. Local preview used the deterministic matcher with Qwen
  disabled; the model service itself was unchanged.
- Changing the watchlist hold retained the notebook context. A notebook follow-up
  changed its own hold without changing the watchlist. Both explicit context
  actions worked, and earlier results retained their original scenario.
- An unpriced pair displayed the execution limitation and a smaller-size action.
- Responsive checks at 320, 375, 768 and 1440 pixels found no page overflow.
  The main holding-period return was visible in the first 320 × 740 viewport.

These are implementation and expert-review checks. They do not establish
real-user task-completion rates or certify financial model accuracy.

## October 6 refinements

Scenario inputs now precede the selected result. The watchlist and analysis no longer repeat a second large return and verdict. The overview keeps the gross-to-net calculation visible, with calculation details, reasoning and the holding-period chart behind separate disclosures. Requirements, stresses and source data remain separate tabs.

Validation: production build and TypeScript passed; all three display tests passed. Browser checks verified the 30-to-7-day scenario update, independent saved notebook context, expandable chart and calculation details, and the Requirements, Stress tests and Source data tabs. A 375-pixel desk and landing check showed no document overflow. Hero zoom and ticker transforms changed across observations; explicit ticker pause reported a paused animation. The complete transparent archive artwork was inspected on its white section.

## Mobile refinement

Phone watchlists now show pair, net return, verdict and save action in an unboxed list. Mobile sort controls reuse the desktop sort state. Desktop retains the full comparison table. Form text is 16 pixels on phones and smaller tablets; analysis and list controls provide 44-pixel targets. The scenario panel is more compact. Tablet navigation switches to the menu before links crowd the header. Workflow cards use normal scrolling on short landscape screens.

Checked 320, 375, 430 and 768 pixel viewports and 844-by-390 landscape. No document overflow was observed on Landing, Research, Method, Evidence or Privacy. Checked menu navigation, search, sorting, save and unsave, pair selection, scenario updates and calculation disclosures. Archive artwork remains complete. Desktop table rendering was rechecked. Production build, TypeScript and all three presentation tests passed. These checks use browser viewport emulation; physical iOS/Android device testing and real-user testing remain separate validation work.

## Pair-label boundaries

Ticker items now use their label's intrinsic width rather than a fixed 170-pixel box. Checked all pair labels for overflow, including ZHIPU/ZHIPUHKD, MINIMAX/MINIMAXHKD, XIAOMI/XIAOMIHKD and TENCENT/TENCENTHKD. None extended beyond its text box. Long selected-pair headings wrap within the analysis panel; MINIMAX/MINIMAXHKD was inspected at 320 pixels without document or heading overflow. Production build and TypeScript passed.

## Three-view workspace, 6 October 2026

The desk now separates Explore, Analyse and Notebook. The selected pair, reference size and holding period travel in URL parameters. A pair selection opens Analyse; navigation and browser Back preserve the mounted notebook and unsent question. Account access appears in the desktop and mobile headers, with an honest unavailable state until infrastructure is connected.

Verification: production build passed; 22 account, research and presentation checks passed. Browser checks at 375, 768 and 1280 pixels found no document overflow. Switching between views preserved a temporary question draft and the existing four-turn notebook. The temporary draft was cleared after verification. Browser Back restored the previous view. Real passkey enrollment remains untested pending the configured database and permanent domain.

Domain research: Spaceship showed usereef.online, getreef.online and reefdesk.online available at $0.98 first-year registration, $0.20 ICANN fee, $15.08 renewal plus fees. The introductory promotion is one per household. Taxes and checkout totals were not verified; no domain was purchased.
