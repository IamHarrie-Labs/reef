"""What would have to be true for a pair to be SUPPORTED?

    python src/solve.py                     # every pair at $25k / 30 days
    python src/solve.py --size 5000 --hold 14

The verdict answers "is it supported today". This inverts it: holding cost,
residual risk and today's measurement noise fixed, how much daily funding
carry would the trade need, what is the shortest hold that works, and what is
the largest tested size that works. Two conditions define SUPPORTED
(intervals.verdict_for), so two requirements are solved and the larger binds:

  point    : (m*h - cost) / risk * sqrt(365/h) > 0.5
  interval : (m - z*se)*h - cost > 0

m is carry in bp/day of reference notional, h the hold in days, se the
autocorrelation-adjusted standard error of the funding holdout.

Residual risk grows with sqrt(h) while carry grows with h, so the point
Sharpe tends to a ceiling m*sqrt(365/24)/rv as h grows. When that ceiling is
below 0.5, no holding period helps - more funding is the only lever.
"""
import argparse, json, math, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity, intervals

BAR = 0.5
MAX_HOLD = 365


def _noise(r, funding):
    net = intervals.net_series(funding, r["a"], r["b"], r["beta"])
    if not net:
        return None
    n_eff, _ = intervals.effective_n(net)
    return st.pstdev(net) / math.sqrt(n_eff) if n_eff > 0 else None


def _supported(m, se, cost, rv_hr, h):
    risk = rv_hr * math.sqrt(24 * h)
    if risk <= 0:
        return False
    point = (m * h - cost) / risk * math.sqrt(365 / h)
    return point > BAR and (m - intervals.Z * se) * h - cost > 0


def requirements(r, ra, hold, funding, se=None):
    se = _noise(r, funding) if se is None else se
    if se is None or not ra:
        return None
    m, cost, risk = r["edge"]["bp_per_day"], ra["cost_bp"], ra["risk_bp"]
    ann = math.sqrt(365 / hold)
    need_cost = cost / hold
    need_risk = BAR * risk / ann / hold
    need_point = need_cost + need_risk
    need_interval = need_cost + intervals.Z * se
    need = max(need_point, need_interval)
    if need_interval > need_point:
        binding = "evidence"
    else:
        binding = "risk" if need_risk > need_cost else "cost"
    min_hold = next((h for h in range(1, MAX_HOLD + 1)
                     if _supported(m, se, cost, r["resid_vol_hr"], h)), None)
    ceiling = m * math.sqrt(365 / 24) / r["resid_vol_hr"] if r["resid_vol_hr"] > 0 else None
    return {
        "bp_per_day_now": round(m, 3),
        "bp_per_day_needed": round(need, 3),
        "multiple": round(need / m, 2) if m > 0 else None,
        "binding": binding,
        "min_hold_days": min_hold,
        "sharpe_ceiling": round(ceiling, 3) if ceiling is not None else None,
    }


def max_supported_size(r, hold, funding, se=None):
    se = _noise(r, funding) if se is None else se
    if se is None:
        return None
    best = None
    for size in capacity.SIZES:
        cost = model.round_trip_cost(r["books"], r["a"], r["b"], size, r["beta"])
        if cost is not None and _supported(r["edge"]["bp_per_day"], se, cost, r["resid_vol_hr"], hold):
            best = size
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=float, default=25_000)
    ap.add_argument("--hold", type=float, default=30)
    args = ap.parse_args()
    prices, funding, books = model.load_prices(), model.load_funding(), model.load_books()
    CL = json.load(open(os.path.join(model.DATA, "clusters.json"), encoding="utf-8"))
    pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]
    print(f"What would make each pair SUPPORTED at ${args.size:,.0f} / {args.hold:.0f} days\n")
    print(f"{'PAIR':20s} {'bp/day now':>11s} {'needed':>8s} {'x now':>7s} {'binds':>9s} "
          f"{'min hold':>9s} {'max size':>10s}")
    print("-" * 80)
    for a, b in pairs:
        r = capacity.analyse_pair(prices, funding, books, a, b)
        ra = capacity.risk_adjusted(r, args.size, args.hold) if r else None
        req = requirements(r, ra, args.hold, funding) if ra else None
        if not req:
            continue
        mx = max_supported_size(r, args.hold, funding)
        mult = f"{req['multiple']:.1f}x" if req["multiple"] else "flip"
        print(f"{r['pair']:20s} {req['bp_per_day_now']:11.2f} {req['bp_per_day_needed']:8.2f} "
              f"{mult:>7s} {req['binding']:>9s} "
              f"{(str(req['min_hold_days']) + 'd') if req['min_hold_days'] else 'none':>9s} "
              f"{('$' + format(mx, ',')) if mx else 'none':>10s}")
    print("\n'flip' = today's carry is negative in the frozen direction; no multiple of it helps.")
    print("'binds' = which requirement is larger: execution cost, residual risk, or evidence (noise).")


if __name__ == "__main__":
    main()
