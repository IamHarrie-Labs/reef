# Reef submission description

Live at https://getreef.xyz · code at https://github.com/IamHarrie-Labs/reef. Validation figures describe the frozen October 6 evaluation.

## Part 1 · Thesis

I built Reef to answer a practical question: how much of a funding yield is left after paying to enter and exit both positions, and what price risk remains?

A positive funding differential is only part of the calculation. The answer changes with position size, order-book depth, fees and holding period. Even a hedged pair can move against the trader. I wanted these assumptions visible in the same place as the result.

Reef estimates the hedge from earlier prices, separates the funding history used to choose direction from the history used to evaluate carry, and prices the selected size against captured order books. It also estimates the remaining spread risk. When a setup does not qualify, the solver shows the funding, holding period or tested size that would change the result under fixed assumptions.

My hypothesis is that traders make better research decisions when they can question the assumptions behind a yield and check the answer themselves.

## Part 2 · Target user and product value

I am initially targeting experienced retail and professional traders researching pairs of Bitget equity, ETF, index or gold perpetuals. The intended user is cautious about leverage, screens opportunities several times a week, and considers positions of roughly $10,000 to $100,000 in reference notional for one day to several weeks. 

Their question is specific: does this funding-carry setup deserve further research at my size and holding period?

For example, they can compare QQQ/TQQQ with SMH/SOXL at $25,000 for 30 days, then ask what happens if execution costs rise by half. Reef retains the scenario and shows the assumptions behind each answer. The notebook keeps the research together for export and later review. Research does not require connecting a wallet or giving Reef trading-account access.

## Part 3 · Validation data and key metrics

Observed model evaluation: the frozen October 6 report includes all 933 scheduled paper records in the captured September 24 to October 5 dataset. Of these, 430 could be graded. Another 376 missed their exit window, 52 lacked execution or funding data, and 75 were pending at the cutoff. The missed exits had one cause: the exit window was 3 hours, but GitHub's scheduler ran the desk a median 5.3 hours apart (maximum 9.7). On October 7 I widened the window to 10 hours, which covers every observed gap. The missed records stay in the report as missed; none were rewritten.

On the same 430 cases, mean absolute funding error was 4.45 basis points for Reef, 4.81 for predicting zero funding and 8.01 for continuing the last settled rate. Giving each entry batch equal weight also favoured Reef. Holds overlap and share instruments, so this is not yet a statistically significant advantage.

Net-outcome direction agreement was 98.84%, the same as always predicting a nonpositive outcome, so Reef shows no direction edge over that baseline. Mean absolute execution-cost error was 17.43 basis points. All outcomes are paper fills against live books, not executed trades.

Product testing so far is my own end-to-end walkthrough: comparisons, follow-ups, scenario changes and rejection of unsupported stresses. Independent traders have not tested it yet.

Targeted validation: I plan to start with three experienced perpetual-futures traders completing an uncoached task. A subsequent ten-user pilot will target eight completing a comparison, stress test and export within five minutes, with four returning within seven days. I will also check whether they can explain the result's main limitation. Completing the research task defines activation. Reef does not execute trades, so I am not claiming volume or revenue.

## Part 4 · Progress

The research interface is built, with Explore, Analyse and Notebook views, comparisons, stress scenarios, a requirements solver and exports. The evidence tools include paper-outcome scoring, the consecutive-case comparison and a portable case with Bitcoin timestamp proofs. Those proofs establish when recorded content existed; they do not authenticate exchange data or prove available liquidity.

Accounts use passkeys, and notebooks save to Neon PostgreSQL. Database checks pass for saving and reopening, separation between users, conflicting-edit rejection and trash restoration. A live desk on GitHub Actions refreshes data, runs the paper trades, checks the on-chain gold basis, anchors the record to Bitcoin and republishes the site.

The stack uses Python, React, TypeScript, Vite, Vercel and Neon PostgreSQL. The existing collector runs through GitHub Actions. Bitget public futures REST APIs supply candles, funding history, order books and settlement marks. Qwen uses the Bitget hackathon inference endpoint. OpenTimestamps supplies Bitcoin commitments, and Ethereum Chainlink feeds provide a separate gold-price reference.

Next: sessions with independent traders, and re-running the baseline evaluation once the 10-hour exit window has produced a full set of graded trades.

## Part 5 · My take on AI Trading

I want to be able to check an AI's answer before risking money on it. In Reef, Qwen helps interpret the question and explain the selected evidence. Python supplies the financial figures. If the explanation fails validation or the model is unavailable, the calculated result remains visible.

The useful part of this approach is the follow-up conversation: what changes if funding reverses, costs rise or the holding period gets shorter? It helps a trader examine a decision while keeping the calculation open to inspection. I would want much stronger evidence of decision quality and risk control before adding autonomous execution.
