# Reef submission description

Reef is live at getreef.xyz and the code is at github.com/IamHarrie-Labs/reef. The validation figures below come from the evaluation frozen on October 6.

## Part 1 · Thesis

I built Reef to answer one practical question. After a trader pays to enter and exit both positions in a pair, how much of the funding yield is left, and how much price risk do they still carry?

A positive funding differential is only part of the calculation. The real answer depends on position size, order-book depth, fees and the holding period. A hedged pair can still move against the trader. I wanted these assumptions to appear in the same place as the result.

Reef estimates the hedge ratio from earlier prices. It chooses the funding direction using one part of the history and then evaluates the carry on a later part it has not seen. It prices the chosen size against real order books and estimates the spread risk that remains after hedging. When a setup does not qualify, a solver shows which funding rate, holding period or size would change the result.

My hypothesis is that traders make better research decisions when they can question the assumptions behind a yield and check the answer for themselves.

## Part 2 · Target user and product value

Reef is for experienced retail and professional traders who research pairs of Bitget equity, ETF, index or gold perpetuals. The typical user is careful with leverage and screens opportunities several times a week. They consider positions of roughly $10,000 to $100,000 held for anywhere from one day to several weeks.

The question they bring is specific. They want to know whether a funding-carry setup deserves more research at their size and holding period.

For example, a trader can compare QQQ/TQQQ with SMH/SOXL at $25,000 for 30 days. They can then ask what happens if execution costs rise by half. Reef keeps the scenario from the first question and shows the assumptions behind each answer. The notebook keeps the whole session together so the trader can export it and review it later. Using Reef does not require a wallet or access to a trading account.

## Part 3 · Validation data and key metrics

The October 6 report includes all 933 scheduled paper records collected between September 24 and October 5. Reef could grade 430 of them. Another 376 missed their exit window, 52 lacked execution or funding data, and 75 had not finished by the cutoff.

The missed exits had a single cause. The exit window was 3 hours, but GitHub's scheduler ran the desk a median of 5.3 hours apart, with a longest gap of 9.7 hours. On October 7 I widened the window to 10 hours, which covers every gap observed so far. The records that missed their exit stay in the report as missed, and none of them were rewritten.

Across the 430 graded cases, Reef's mean absolute funding error was 4.45 basis points. Predicting zero funding gave 4.81 basis points, and repeating the last settled rate gave 8.01. Reef also came out ahead when each entry batch was given equal weight. Because the holds overlap and share instruments, this lead is not yet statistically significant.

Reef predicted the direction of the net outcome correctly 98.84% of the time. Always predicting a loss or zero gives exactly the same score, so Reef shows no edge on direction. The mean absolute error on execution cost was 17.43 basis points. Every outcome is a paper fill priced against live order books, and no real trades were placed.

So far the product has been tested only in my own end-to-end walkthrough. It covered comparisons, follow-up questions, scenario changes and the rejection of unsupported stress tests. Independent traders have not used it yet.

My next validation step is a session with three experienced perpetual-futures traders, each completing a task without coaching. After that, a ten-person pilot will aim for eight people to finish a comparison, a stress test and an export within five minutes, and for four of them to come back within seven days. I will also check whether each person can explain the main limitation of the result they saw. A user counts as activated when they complete the research task. Reef does not execute trades, so I am not claiming any trading volume or revenue.

## Part 4 · Progress

The research interface is built. It has Explore, Analyse and Notebook views, along with comparisons, stress scenarios, a requirements solver and exports. The evidence tools score paper outcomes, compare consecutive cases and include a portable case study with Bitcoin timestamp proofs. These proofs only show when a record existed. They cannot confirm that the exchange data is authentic or that the liquidity was really available.

Users sign in with passkeys, and their notebooks are saved to Neon PostgreSQL. Database tests pass for saving and reopening notebooks, keeping users separate, rejecting conflicting edits and restoring deleted items. A live desk on GitHub Actions refreshes the market data and runs the paper trades. It also checks gold prices on-chain, anchors the record to Bitcoin and republishes the site.

Reef is built with Python, React, TypeScript and Vite, and it is hosted on Vercel with Neon PostgreSQL. Bitget's public futures APIs provide candles, funding history, order books and settlement prices. Qwen runs through the Bitget hackathon inference endpoint. OpenTimestamps provides the Bitcoin timestamps, and Chainlink feeds on Ethereum give an independent gold price.

The next steps are sessions with independent traders and a new baseline evaluation once the 10-hour exit window has produced a full set of graded trades.

## Part 5 · My take on AI Trading

Before I risk money on an AI's answer, I want to be able to check it. In Reef, Qwen helps interpret the question and explains the evidence that Python selected. Every financial figure comes from the Python model. If Qwen's explanation fails validation or the model is unavailable, the calculated result still appears on screen.

The most useful part of this approach is the follow-up conversation. A trader can ask what changes if funding reverses, if costs rise or if the holding period gets shorter. Each answer can be traced back to its calculation. I would want much stronger evidence of good decisions and sound risk control before letting an AI execute trades on its own.
