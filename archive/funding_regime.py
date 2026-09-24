"""Is the funding edge regime-dependent, the way price divergence is?

Price divergence degrades 2.89x when the US market is closed. If funding does
the same, entry timing matters and the carry trade has a best hour of the week.

SUPERSEDED by `regime_test.py`. This script prints raw bp/interval figures
with no significance test and mixes gold's 4h funding cadence with the 8h
cadence of everything else in the same column - the same unit-mixing bug
that produced the retracted "23x funding decline" claim (DECISIONS.md D-13).
Kept only as the original exploratory script; `regime_test.py` is the
number to cite - it normalizes to bp/day and reports a sign test + bootstrap
CI instead of a bare ratio.
"""
import sys, os, json, datetime as dt, statistics as st
print("EXPLORATORY LEGACY ANALYSIS: not validated performance; shared pairs and overlapping windows are dependent.")
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity

def regime(ms):
    t = dt.datetime.utcfromtimestamp(ms / 1000)
    if t.weekday() >= 5: return "WEEKEND"
    return "RTH" if 13 <= t.hour < 20 else "OVERNIGHT"

prices, funding = model.load_prices(), model.load_funding()
CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
         for i in range(len(sy)) for j in range(i + 1, len(sy))]

print(f"{'PAIR':20s} {'RTH':>18s} {'OVERNIGHT':>18s} {'WEEKEND':>18s}")
print(f"{'':20s} " + " ".join(f"{'bp/int  (n)':>18s}" for _ in range(3)))
print("-" * 78)
agg = {}
for a, b in pairs:
    if a not in funding or b not in funding: continue
    beta, _ = model.hedge_ratio(prices, a, b)
    ks = sorted(set(funding[a]) & set(funding[b]))
    if len(ks) < 40: continue
    net = {}
    for k in ks:
        net.setdefault(regime(k), []).append(beta * funding[a][k] - funding[b][k])
    sign = 1 if st.mean([v for l in net.values() for v in l]) > 0 else -1
    cells = []
    for rg in ("RTH", "OVERNIGHT", "WEEKEND"):
        v = [x * sign for x in net.get(rg, [])]
        if len(v) < 3: cells.append(f"{'-':>18s}"); continue
        m = st.mean(v); agg.setdefault(rg, []).append(m)
        cells.append(f"{m:12.3f} ({len(v):3d})")
    print(f"{a.replace('USDT','')+'/'+b.replace('USDT',''):20s} " + " ".join(cells))

print("\n=== AGGREGATE: mean funding edge by regime (bp per 8h interval) ===")
base = st.mean(agg["RTH"])
for rg in ("RTH", "OVERNIGHT", "WEEKEND"):
    v = agg[rg]
    print(f"  {rg:10s} mean {st.mean(v):7.3f}  median {st.median(v):7.3f}  "
          f"vs RTH {st.mean(v)/base:5.2f}x   (n={len(v)} pairs)")

# Exploratory legacy regime analysis; not independent out-of-sample validation.
