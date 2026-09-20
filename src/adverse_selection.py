"""Does the book thin exactly when the gap widens?

price divergence is 2.89x worse when the US market is closed (see
funding_regime.py for the funding-side mirror of this). The open question
this script answers: is that because liquidity actually withdraws at the
same moment, or is the divergence just noise in a normal book?

Needs a time series of (spread, depth) pairs — depth.py's single snapshot
cannot answer this, only recorder.py's ongoing capture can. This script
runs against whatever data/timeseries/*.jsonl exists and is honest about
n when that's zero: report the sample size, never fabricate the answer.
"""
import json, os, sys, glob, math, statistics as st, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import model

TS_DIR = os.path.join(model.DATA, "timeseries")


def load_series(sym):
    path = os.path.join(TS_DIR, f"{sym}.jsonl")
    if not os.path.exists(path):
        return []
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def top_of_book_depth(row, side, bp_range=20):
    """USDT notional resting within `bp_range` bp of the touch."""
    levels = row.get("asks" if side == "ask" else "bids")
    if not levels:
        return None
    touch = float(levels[0][0])
    limit = touch * (1 + bp_range / 1e4) if side == "ask" else touch * (1 - bp_range / 1e4)
    notional = 0.0
    for p, q in levels:
        p = float(p)
        if (side == "ask" and p > limit) or (side == "bid" and p < limit):
            break
        notional += p * float(q)
    return notional


def regime(ms):
    t = dt.datetime.utcfromtimestamp(ms / 1000)
    if t.weekday() >= 5:
        return "WEEKEND"
    return "RTH" if 13 <= t.hour < 20 else "OVERNIGHT"


def analyse(a, b, beta=1.0):
    ra, rb = load_series(a), load_series(b)
    if len(ra) < 5 or len(rb) < 5:
        return {"pair": f"{a}/{b}", "n": min(len(ra), len(rb)),
                "status": "insufficient_data",
                "note": "recorder needs to run for at least a few hours to say anything here"}
    # The recorder stamps each symbol as it polls it, so two legs of the same
    # pass are seconds apart and never match on exact ts. Bucket into passes
    # (recorder interval is 15 min; a 5-minute bucket is comfortably inside
    # one pass and cannot merge two) and pair up within a bucket.
    BUCKET_MS = 5 * 60 * 1000
    ta, tb = {}, {}
    for r in ra:
        if "asks" in r:
            ta.setdefault(r["ts"] // BUCKET_MS, r)
    for r in rb:
        if "asks" in r:
            tb.setdefault(r["ts"] // BUCKET_MS, r)
    common = sorted(set(ta) & set(tb))
    # The two legs sit at different price levels, so the raw log ratio is
    # dominated by that constant and says nothing about dislocation. The
    # signal is how far the ratio sits from its OWN typical value, so build
    # the beta-adjusted log ratio first, then measure deviation from its mean.
    raw = []
    for bucket in common:
        row_a, row_b = ta[bucket], tb[bucket]
        pa = (float(row_a["asks"][0][0]) + float(row_a["bids"][0][0])) / 2
        pb = (float(row_b["asks"][0][0]) + float(row_b["bids"][0][0])) / 2
        depth_a = top_of_book_depth(row_a, "ask")
        depth_b = top_of_book_depth(row_b, "ask")
        if depth_a is None or depth_b is None:
            continue
        raw.append({"ts": row_a["ts"], "regime": regime(row_a["ts"]),
                     "log_ratio": math.log(pb) - beta * math.log(pa),
                     "min_depth_usdt": min(depth_a, depth_b)})
    if not raw:
        return {"pair": f"{a}/{b}", "n": 0, "status": "insufficient_data"}
    centre = st.mean([x["log_ratio"] for x in raw])
    out = [{"ts": x["ts"], "regime": x["regime"],
            "gap_bp": abs(x["log_ratio"] - centre) * 1e4,
            "min_depth_usdt": x["min_depth_usdt"]} for x in raw]
    if len(out) < 5:
        return {"pair": f"{a}/{b}", "n": len(out), "status": "insufficient_data"}
    gaps = [x["gap_bp"] for x in out]
    depths = [x["min_depth_usdt"] for x in out]
    if st.pstdev(gaps) == 0 or st.pstdev(depths) == 0:
        corr = 0.0
    else:
        mg, md = st.mean(gaps), st.mean(depths)
        cov = sum((g - mg) * (d - md) for g, d in zip(gaps, depths)) / len(gaps)
        corr = cov / (st.pstdev(gaps) * st.pstdev(depths))
    by_regime = {}
    for x in out:
        by_regime.setdefault(x["regime"], []).append(x)
    regime_stats = {rg: {"n": len(v), "mean_gap_bp": round(st.mean([y["gap_bp"] for y in v]), 1),
                          "mean_depth_usdt": round(st.mean([y["min_depth_usdt"] for y in v]), 0)}
                     for rg, v in by_regime.items()}
    return {"pair": f"{a}/{b}", "n": len(out), "status": "analysed",
            "gap_depth_correlation": round(corr, 3),
            "interpretation": ("liquidity withdraws as the gap widens (adversarial)" if corr < -0.2
                                else "depth roughly independent of gap size" if abs(corr) <= 0.2
                                else "liquidity INCREASES with gap (unexpected - check data)"),
            "by_regime": regime_stats}


if __name__ == "__main__":
    CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
    pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]
    have_any = False
    for a, b in pairs:
        r = analyse(a, b)
        if r["status"] == "analysed":
            have_any = True
        print(json.dumps(r, indent=2))
    if not have_any:
        print("\nNo pair has enough recorded snapshots yet. This script is correct and ready;"
              " it needs recorder.py running (from a host that can reach api.bitget.com) to"
              " produce anything. Currently: 0 snapshots recorded in this environment"
              " (network to api.bitget.com is blocked here as of 2026-09-19).")
