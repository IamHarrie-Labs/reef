"""Capacity curve: how much size a carry trade survives, and for how long.

Execution cost rises with notional as you walk the book. Funding carry does
not. So every pair has a size beyond which the trade stops paying, and a
holding period below which it never starts. This computes both.

Risk is the residual spread, not funding volatility. A beta-hedged pair still
drifts, and over a holding period that drift dominates. Reporting a funding-only
Sharpe would overstate the trade by an order of magnitude.
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import model

SIZES = [1_000, 2_500, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000]
HOLDS = [1, 3, 7, 14, 30, 60, 90]


def analyse_pair(prices, funding, books, a, b, split=None):
    beta, n_fit = model.hedge_ratio(prices, a, b, upto=split)
    edge = model.funding_edge(funding, a, b, beta)
    if not edge:
        return None
    rvol_h, n_res = model.residual_vol(prices, a, b, beta, after=split)
    curve = []
    for size in SIZES:
        cost = model.round_trip_cost(books, a, b, size, beta)
        curve.append((size, cost))
    return {"pair": f"{a.replace('USDT','')}/{b.replace('USDT','')}", "a": a, "b": b,
            "beta": beta, "edge": edge, "resid_vol_hr": rvol_h,
            "n_fit": n_fit, "n_resid": n_res, "curve": curve}


def risk_adjusted(r, size, hold_days):
    """Net return and a Sharpe that prices residual drift as the real risk."""
    cost = dict(r["curve"]).get(size)
    if cost is None:
        return None
    nc = model.net_carry(r["edge"], cost, hold_days)
    # residual spread risk accumulates as sqrt(time)
    risk_bp = r["resid_vol_hr"] * math.sqrt(hold_days * 24)
    sharpe = (nc["net_bp"] / risk_bp * math.sqrt(365 / hold_days)) if risk_bp > 0 else float("nan")
    return {**nc, "risk_bp": risk_bp, "sharpe": sharpe}


def max_viable(r, hold_days):
    """Largest notional whose net carry is still positive at this holding period."""
    best = None
    for size, cost in r["curve"]:
        if cost is None:
            continue
        if r["edge"]["bp_per_day"] * hold_days - cost > 0:
            best = size
    return best


def render(r):
    e = r["edge"]
    print(f"\n{'='*78}\n{r['pair']}   beta {r['beta']:.3f}   "
          f"residual vol {r['resid_vol_hr']:.1f} bp/hr\n{'='*78}")
    print(f"  funding edge : {e['bp_per_day']:.2f} bp/day  ({e['annual_pct']:.1f}% ann gross)")
    print(f"  direction    : {e['direction']}")
    print(f"  consistency  : {e['consistency_pct']:.0f}% same-sign over {e['n_intervals']} intervals")
    print(f"\n  CAPACITY CURVE - net annualised %, by size and holding period")
    hdr = "  " + " ".join(f"{str(h)+'d':>8s}" for h in HOLDS)
    print(f"  {'size':>9s} {'cost bp':>8s} |{hdr}")
    print("  " + "-" * (22 + 9 * len(HOLDS)))
    for size, cost in r["curve"]:
        if cost is None:
            print(f"  {size:>9,} {'BOOK X':>8s} |")
            continue
        cells = []
        for h in HOLDS:
            ra = risk_adjusted(r, size, h)
            cells.append(f"{ra['annual_pct']:8.1f}" if ra else f"{'-':>8s}")
        print(f"  {size:>9,} {cost:8.1f} |  " + " ".join(cells))
    print(f"\n  breakeven hold : {model.net_carry(e, r['curve'][0][1], 30)['breakeven_days']:.1f} days at $1k")
    for h in (14, 30, 90):
        mv = max_viable(r, h)
        print(f"  max viable @{h:>3}d : {('$'+format(mv,',')) if mv else 'none'}")


if __name__ == "__main__":
    prices, funding, books = model.load_prices(), model.load_funding(), model.load_books()
    import json
    CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
    pairs = [(c, sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]
    results = []
    for _, a, b in pairs:
        r = analyse_pair(prices, funding, books, a, b)
        if r:
            results.append(r)
    results.sort(key=lambda r: -(risk_adjusted(r, 25_000, 30) or {"sharpe": -99})["sharpe"])
    print(f"\nRanked by risk-adjusted return at $25k / 30d hold  (n={len(results)} pairs)")
    print(f"{'PAIR':22s} {'ann%':>7s} {'net bp':>8s} {'risk bp':>8s} {'Sharpe':>7s} {'consist':>8s}")
    print("-" * 68)
    for r in results:
        ra = risk_adjusted(r, 25_000, 30)
        if not ra:
            print(f"{r['pair']:22s} {'book too thin':>40s}")
            continue
        print(f"{r['pair']:22s} {ra['annual_pct']:7.1f} {ra['net_bp']:8.1f} "
              f"{ra['risk_bp']:8.0f} {ra['sharpe']:7.2f} {r['edge']['consistency_pct']:7.0f}%")
    for r in results[:3]:
        render(r)
