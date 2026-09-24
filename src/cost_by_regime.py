"""Execution cost by market regime, from the live recorder's book series.

`archive/depth_regime.py` compares two one-off snapshots and is confounded: the RTH
baseline and the closed-market snapshot were taken days apart, so any
difference mixes regime with whatever else moved in between. This script
avoids that by using `recorder.py`'s continuous capture - every book comes
from the same process, on the same cadence, so regimes are compared
within one series instead of across two isolated moments.

    python src/cost_by_regime.py
    python src/cost_by_regime.py --size 25000

Reports median round-trip cost per regime, per pair, with n. Until the
recorder has covered both an open and a closed window, it says so rather
than reporting a one-sided number.
"""
import argparse, json, os, sys, glob, statistics as st
import datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import model

TS_DIR = os.path.join(model.DATA, "timeseries")
BUCKET_MS = 5 * 60 * 1000


def regime(ms):
    t = dt.datetime.utcfromtimestamp(ms / 1000)
    if t.weekday() >= 5:
        return "WEEKEND"
    return "RTH" if 13 <= t.hour < 20 else "OVERNIGHT"


def load_buckets(sym):
    """{bucket: row} for rows that carry a usable book."""
    path = os.path.join(TS_DIR, f"{sym}.jsonl")
    if not os.path.exists(path):
        return {}
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("asks") and r.get("bids"):
            out.setdefault(r["ts"] // BUCKET_MS, r)
    return out


def as_book(row):
    return {"asks": [(float(p), float(q)) for p, q in row["asks"]],
            "bids": [(float(p), float(q)) for p, q in row["bids"]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=float, default=25_000)
    args = ap.parse_args()

    prices = model.load_prices()
    CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
    pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]

    print(f"Round-trip execution cost by regime, ${args.size:,.0f} notional")
    print(f"Source: recorder book series in data/timeseries/\n")
    print(f"{'PAIR':20s} {'REGIME':10s} {'n':>4s} {'median bp':>10s} "
          f"{'min':>8s} {'max':>8s}")
    print("-" * 64)

    seen_regimes = set()
    any_rows = False
    for a, b in pairs:
        ba, bb = load_buckets(a), load_buckets(b)
        common = sorted(set(ba) & set(bb))
        if not common:
            continue
        beta, _ = model.hedge_ratio(prices, a, b)
        by_regime = {}
        for bucket in common:
            row_a, row_b = ba[bucket], bb[bucket]
            books = {a: as_book(row_a), b: as_book(row_b)}
            cost = model.round_trip_cost(books, a, b, args.size, beta)
            if cost is None:
                continue
            by_regime.setdefault(regime(row_a["ts"]), []).append(cost)
        if not by_regime:
            continue
        name = f"{a.replace('USDT','')}/{b.replace('USDT','')}"
        first = True
        for rg in ("RTH", "OVERNIGHT", "WEEKEND"):
            v = by_regime.get(rg, [])
            if not v:
                continue
            seen_regimes.add(rg)
            any_rows = True
            print(f"{(name if first else ''):20s} {rg:10s} {len(v):>4d} "
                  f"{st.median(v):>10.1f} {min(v):>8.1f} {max(v):>8.1f}")
            first = False
        if not first:
            print()

    if not any_rows:
        print("No pair has a usable book series yet.")
        print("The recorder needs to run (src/run_recorder.sh) and capture "
              "books for both legs of at least one pair.")
        return

    print("=" * 64)
    if len(seen_regimes) < 2:
        only = next(iter(seen_regimes))
        print(f"Only one regime captured so far ({only}). A cost comparison "
              f"needs at least two.")
        print("The recorder is still accumulating; rerun once it has crossed "
              "a US market open or close.")
    else:
        print(f"Regimes captured: {', '.join(sorted(seen_regimes))}")
        print("Compare medians within a pair - across pairs the absolute "
              "level reflects\nthat pair's liquidity, not the regime.")


if __name__ == "__main__":
    main()
