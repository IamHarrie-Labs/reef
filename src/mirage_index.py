"""Reef index: one public score per RWA pair - what fraction of the
visible yield survives execution cost and residual risk.

    python src/mirage_index.py            # ranked table, all pairs
    python src/mirage_index.py --json      # machine-readable, for a page/UI

score = net Sharpe at $25k / 30d, clamped and mapped to 0-100 so it reads
like a trust score without hiding a failure behind an average: the raw
Sharpe, net bp, and cost bp are always printed alongside it.
"""
import json, os, sys, argparse
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity, intervals


def build(size=25_000, hold_days=30):
    prices, funding, books = model.load_prices(), model.load_funding(), model.load_books()
    CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
    pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]
    rows = []
    for a, b in pairs:
        r = capacity.analyse_pair(prices, funding, books, a, b)
        if not r:
            rows.append({"pair": f"{a.replace('USDT','')}/{b.replace('USDT','')}",
                         "status": "no_funding_history"})
            continue
        ra = capacity.risk_adjusted(r, size, hold_days)
        if not ra:
            rows.append({"pair": r["pair"], "status": "book_too_thin"})
            continue
        score = max(0, min(100, round(50 + ra["sharpe"] * 35)))
        ci = intervals.sharpe_interval(r, ra, funding, hold_days)
        rows.append({
            "pair": r["pair"], "status": "priced", "mirage_score": score,
            "ci_lo": round(ci["lo"], 2) if ci else None,
            "ci_hi": round(ci["hi"], 2) if ci else None,
            "n_eff": round(ci["n_eff"], 1) if ci else None,
            "funding_interval_h": round(r["edge"]["funding_interval_h"]),
            "history_days": round(r["edge"]["history_days"], 1),
            "gross_annual_pct": round(r["edge"]["annual_pct"], 1),
            "net_annual_pct": round(ra["annual_pct"], 1),
            "sharpe": round(ra["sharpe"], 2),
            "net_bp": round(ra["net_bp"], 1), "cost_bp": round(ra["cost_bp"], 1),
            "risk_bp": round(ra["risk_bp"], 0),
            "consistency_pct": round(r["edge"]["consistency_pct"], 0),
            "verdict": intervals.verdict_for(ra["sharpe"], ci),
            "n_funding_intervals": r["edge"]["n_intervals"],
        })
    rows.sort(key=lambda x: -(x.get("mirage_score", -1)))
    return {"size": size, "hold_days": hold_days,
            "data_asof": os.path.getmtime(os.path.join(model.DATA, "prices.json")),
            "rows": rows}


def render(idx):
    print(f"\nREEF INDEX - ${idx['size']:,.0f} / {idx['hold_days']:.0f}-day hold")
    print("Is the yield real, once cost and risk are priced in?")
    print("REAL = clears Sharpe 0.5 and its 95% interval excludes zero.")
    print("UNPROVEN = clears 0.5 on the point estimate only; the interval includes zero.\n")
    print(f"{'#':>3} {'PAIR':18s} {'SCORE':>5s} {'VERDICT':>9s} {'gross%':>7s} {'net%':>6s} "
          f"{'Sharpe':>7s} {'95% CI':>16s} {'cost bp':>8s} {'hist':>6s}")
    print("-" * 96)
    n = 1
    for r in idx["rows"]:
        if r["status"] != "priced":
            print(f"{'-':>3} {r['pair']:18s} {r['status']:>50s}")
            continue
        ci = (f"[{r['ci_lo']:+.2f}, {r['ci_hi']:+.2f}]"
              if r.get("ci_lo") is not None else "-")
        print(f"{n:>3} {r['pair']:18s} {r['mirage_score']:>5d} {r['verdict']:>9s} "
              f"{r['gross_annual_pct']:7.1f} {r['net_annual_pct']:6.1f} {r['sharpe']:7.2f} "
              f"{ci:>16s} {r['cost_bp']:8.1f} {r['history_days']:5.1f}d")
        n += 1
    priced = [r for r in idx["rows"] if r["status"] == "priced"]
    count = lambda v: sum(1 for r in priced if r["verdict"] == v)
    print(f"\n{count('REAL')} REAL, {count('UNPROVEN')} UNPROVEN, "
          f"{count('MIRAGE')} MIRAGE, of {len(priced)} priced pairs.")
    if count("UNPROVEN") and not count("REAL"):
        print("Every pair that clears the bar does so on an interval that includes "
              "zero.\nNone is evidence of an edge on this sample.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--size", type=float, default=25_000)
    ap.add_argument("--hold", type=float, default=30)
    args = ap.parse_args()
    idx = build(args.size, args.hold)
    if args.json:
        print(json.dumps(idx, indent=2, default=str))
    else:
        render(idx)
