"""Confidence intervals on the headline numbers.

Every Sharpe and consistency figure elsewhere in this project is a point
estimate from ~100 funding intervals. Reporting those without an interval
invites the reader to treat 0.21 and 0.51 as different when the data
cannot separate them. This computes what the sample actually supports.

    python src/intervals.py
    python src/intervals.py --hold 30 --size 25000

Three things are done properly rather than by default:

1. Consistency is a binomial proportion, so it gets a **Wilson score
   interval** - not a normal approximation, which misbehaves near 0 and 1
   and at small n.

2. Funding intervals are autocorrelated (an 8h rate is not independent of
   the one before it), so the naive standard error understates uncertainty.
   The effective sample size is adjusted by the lag-1 autocorrelation,
   n_eff = n * (1 - r) / (1 + r), and the interval uses n_eff.

3. The Sharpe interval propagates uncertainty in the **funding edge only**.
   Residual volatility and execution cost are held at their point
   estimates. That makes every interval here a partial estimate of the
   uncertainty - the real intervals are wider than what's printed.
"""
import argparse, json, math, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity

Z = 1.959963985  # 95% two-sided normal quantile


def wilson(successes, n, z=Z):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def lag1_autocorr(xs):
    n = len(xs)
    if n < 3:
        return 0.0
    m = st.mean(xs)
    denom = sum((x - m) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    num = sum((xs[i] - m) * (xs[i - 1] - m) for i in range(1, n))
    return num / denom


def effective_n(xs):
    """n adjusted for lag-1 autocorrelation. Positive autocorrelation
    shrinks the effective sample; negative is clamped to n."""
    n = len(xs)
    r = lag1_autocorr(xs)
    if r <= 0:
        return float(n), r
    return n * (1 - r) / (1 + r), r


def net_series(funding, a, b, beta):
    """Per-interval net funding for the profitable direction, in bp."""
    edge = model.funding_edge(funding, a, b, beta)
    return edge["validation_series"] if edge else None


def sharpe_interval(r, ra, funding, hold):
    """95% Sharpe interval for one priced pair, funding-edge uncertainty only.

    `r` is capacity.analyse_pair() output, `ra` is capacity.risk_adjusted().
    Returns dict(lo, hi, n, n_eff, r1) or None. Shared by the CLI below,
    reef_index.py and export_web.py so every surface computes it the
    same way.
    """
    a, b = r["a"], r["b"]
    net = net_series(funding, a, b, r["beta"])
    if not net or not ra:
        return None
    n = len(net)
    n_eff, r1 = effective_n(net)
    se = st.pstdev(net) / math.sqrt(n_eff) if n_eff > 0 else float("nan")
    ipd = r["edge"]["intervals_per_day"]
    ann = math.sqrt(365 / hold)

    def sharpe_for(edge):
        gross = edge * ipd * hold
        return ((gross - ra["cost_bp"]) / ra["risk_bp"] * ann) if ra["risk_bp"] > 0 else float("nan")

    mean_bp = st.mean(net)
    return {"lo": sharpe_for(mean_bp - Z * se), "hi": sharpe_for(mean_bp + Z * se),
            "n": n, "n_eff": n_eff, "r1": r1}


def verdict_for(sharpe, ci, bar=0.5):
    """SUPPORTED only when the point estimate clears the bar AND the interval
    excludes zero. A point estimate that clears the bar on an interval
    spanning zero is UNPROVEN - it is not evidence of an edge."""
    if sharpe is None or sharpe != sharpe or sharpe <= bar:
        return "UNFAVOURABLE"
    if ci is None or ci["lo"] <= 0:
        return "UNPROVEN"
    return "SUPPORTED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hold", type=float, default=30)
    ap.add_argument("--size", type=float, default=25_000)
    ap.add_argument("--archive", action="store_true",
                    help="use the accumulated funding archive instead of the latest window")
    args = ap.parse_args()

    src = "archive" if args.archive else "window"
    prices, books = model.load_prices(), model.load_books()
    funding = model.load_funding(source=src)
    if not funding:
        print("No funding data for source=%s. Run: python src/funding_archive.py" % src)
        return
    CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
    pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]

    print(f"95% confidence intervals, ${args.size:,.0f} / {args.hold:.0f}-day hold, "
          f"funding source: {src}")
    print("Uncertainty from the funding edge only; cost and residual vol held "
          "at point estimates,\nthese approximate intervals omit other sources of "
          "uncertainty.\n")
    print(f"{'PAIR':18s} {'Sharpe':>7s} {'95% CI':>18s} {'consist':>8s} "
          f"{'Wilson 95%':>16s} {'n':>5s} {'n_eff':>7s} {'r1':>6s}")
    print("-" * 92)

    rows, clears_point, clears_upper = [], 0, 0
    for a, b in pairs:
        r = capacity.analyse_pair(prices, funding, books, a, b)
        if not r:
            continue
        ra = capacity.risk_adjusted(r, args.size, args.hold)
        if not ra:
            continue
        net = net_series(funding, a, b, r["beta"])
        if not net:
            continue

        n = len(net)
        n_eff, r1 = effective_n(net)
        mean_bp = st.mean(net)
        sd_bp = st.pstdev(net)
        se = sd_bp / math.sqrt(n_eff) if n_eff > 0 else float("nan")

        # propagate the edge interval through net carry -> Sharpe
        cost_bp = ra["cost_bp"]
        risk_bp = ra["risk_bp"]
        ann = math.sqrt(365 / args.hold)

        def sharpe_for(edge_per_interval):
            gross = edge_per_interval * r["edge"]["intervals_per_day"] * args.hold
            return ((gross - cost_bp) / risk_bp * ann) if risk_bp > 0 else float("nan")

        lo_s = sharpe_for(mean_bp - Z * se)
        hi_s = sharpe_for(mean_bp + Z * se)

        successes = sum(1 for x in net if x > 0)
        w_lo, w_hi = wilson(successes, n)

        if ra["sharpe"] > 0.5:
            clears_point += 1
        if hi_s > 0.5:
            clears_upper += 1

        rows.append((r["pair"], ra["sharpe"], lo_s, hi_s,
                     r["edge"]["consistency_pct"], w_lo * 100, w_hi * 100,
                     n, n_eff, r1))

    rows.sort(key=lambda x: -x[1])
    for name, sh, lo, hi, cons, wlo, whi, n, neff, r1 in rows:
        print(f"{name:18s} {sh:7.2f} {f'[{lo:+.2f}, {hi:+.2f}]':>18s} "
              f"{cons:7.0f}% {f'[{wlo:.0f}%, {whi:.0f}%]':>16s} "
              f"{n:5d} {neff:7.1f} {r1:+6.2f}")

    if not rows:
        print("No pair could be priced.")
        return

    print("\n" + "=" * 92)
    print(f"Pairs whose POINT estimate clears Sharpe 0.5      : {clears_point}/{len(rows)}")
    print(f"Pairs whose UPPER 95% bound reaches Sharpe 0.5    : {clears_upper}/{len(rows)}")
    print()
    if clears_point == 0 and clears_upper > 0:
        print(f"No pair clears the bar on its point estimate, but {clears_upper} "
              f"cannot be ruled out\nat 95%. 'Nothing clears the bar' is the "
              f"honest reading; 'nothing could ever\nclear it' is not what this "
              f"sample supports.")
    elif clears_upper == 0:
        print("No pair reaches Sharpe 0.5 even at its upper 95% bound. On this "
              "sample the\nabsence of a viable trade is not a matter of "
              "insufficient data.")

    med_r1 = st.median([x[9] for x in rows])
    med_ratio = st.median([x[8] / x[7] for x in rows])
    print(f"\nMedian lag-1 autocorrelation of net funding: {med_r1:+.2f}")
    print(f"Median effective sample retained           : {med_ratio * 100:.0f}% of n")
    if med_r1 > 0.1:
        print("Positive autocorrelation: consecutive funding intervals carry "
              "overlapping\ninformation, so the naive standard error would have "
              "understated these intervals.")


if __name__ == "__main__":
    main()
