"""Naive screen vs full model - the demo.

A naive screener ranks pairs by gross funding yield, which is what any
dashboard can show. The full model prices execution cost and residual drift.
The two rankings disagree almost completely, and that disagreement is the
product.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity

prices, funding, books = model.load_prices(), model.load_funding(), model.load_books()
CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
         for i in range(len(sy)) for j in range(i + 1, len(sy))]

rows = []
for a, b in pairs:
    r = capacity.analyse_pair(prices, funding, books, a, b)
    if not r:
        continue
    ra = capacity.risk_adjusted(r, 25_000, 30)
    if not ra:
        continue
    rows.append({"pair": r["pair"], "gross": r["edge"]["annual_pct"],
                 "net": ra["annual_pct"], "sharpe": ra["sharpe"],
                 "consist": r["edge"]["consistency_pct"],
                 "cost": ra["cost_bp"], "risk": ra["risk_bp"]})

naive = sorted(rows, key=lambda x: -x["gross"])
full = sorted(rows, key=lambda x: -x["sharpe"])

print("What a naive yield screen shows you        vs   what survives the full model")
print("-" * 82)
print(f"{'#':>2} {'PAIR':18s} {'gross%':>8s}   |  {'PAIR':18s} {'net%':>7s} {'Sharpe':>7s}")
print("-" * 82)
for i in range(min(8, len(rows))):
    n, f = naive[i], full[i]
    print(f"{i+1:>2} {n['pair']:18s} {n['gross']:8.1f}   |  {f['pair']:18s} {f['net']:7.1f} {f['sharpe']:7.2f}")

print("\nTop naive pick, fully priced:")
top = naive[0]
print(f"  {top['pair']}: {top['gross']:.1f}% gross -> {top['net']:.1f}% net "
      f"(cost {top['cost']:.0f}bp, risk {top['risk']:.0f}bp, Sharpe {top['sharpe']:.2f}, "
      f"consistency {top['consist']:.0f}%)")
survivors = [r for r in rows if r["sharpe"] > 0.5]
print(f"\nPairs with Sharpe > 0.5 at $25k / 30d: {len(survivors)}/{len(rows)}")
for s in survivors:
    print(f"  {s['pair']}  net {s['net']:.1f}%  Sharpe {s['sharpe']:.2f}  consistency {s['consist']:.0f}%")
