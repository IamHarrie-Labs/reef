# Reproduce the case study

The evidence page offers a single downloadable JSON file. The repository copy is
`data/case_study.json`. It contains the frozen ledger row, completed hypothetical
execution, archived funding observations for both legs, settlement mark prices,
two Merkle inclusion paths, original detached OpenTimestamps files (base64), and
Bitcoin block headers. No exchange account or API key is needed.

## Selection rule

Sort shadow records by recorded timestamp and record key. Select the first
completed, gradeable record whose prediction and completed execution match
confirmed anchors, and whose prediction's Bitcoin header time precedes the
holding-period endpoint. This rule does not consider profit, agreement or size
of error. The bundle records how many earlier records were ineligible.

The case stays fixed as the live desk advances. Rebuild deliberately with
`python src/case_study.py --build` (requires internet access).

## Verify

From the repository root, with Python 3.11 or later:

```sh
python -m pip install -r requirements-proof.txt
python src/case_study.py --verify data/case_study.json --online
```

Replace the path with the downloaded bundle to verify that exact file. The
command recomputes signed-position accounting, compares all reported outcomes,
checks both objects against their Merkle roots, and uses the OpenTimestamps
library to verify each root against its included Bitcoin header. It requires
the prediction block timestamp to precede maturity. `--online` additionally
checks each block hash at its stated height against Blockstream and Blockchain.com.
Without that flag the command checks the bundled headers, not canonical chain
membership. These explorers are external references, not a local consensus node.

To use a separate OpenTimestamps client, decode each `ots_base64` field to a
`.root.txt.ots` file and write its `root` plus a newline to the matching
`.root.txt` file. Verify with `ots verify` or at https://opentimestamps.org.

## Practical limits

Bitcoin header timestamps are approximate chain times, not precise wall-clock
certificates. The anchors bind recorded content; they do not authenticate the
exchange observations or establish that a fill would have been available.
Original full books were not retained per record, so this bundle cannot replay
the original depth walk. Entry/exit prices, quantities, fee assumptions and
settlement marks remain inspectable, and the arithmetic is reproducible.

One realised net P&L includes residual price movement. It does not validate a
historical carry expectation, an expected Sharpe, or the funding-only interval.
