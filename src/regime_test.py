"""Significance tests for the two regime-dependence claims.

The README makes two claims about what happens when the US market closes:

  1. Funding edge falls (reported as RTH 0.843 -> weekend 0.036 bp/interval)
  2. Tracking error, relative to volatility, rises

Both were first reported as bare ratios of means. This tests them.

    python src/regime_test.py

The unit of analysis is the **pair**, not the interval: each pair
contributes one RTH value and one WEEKEND value, and the comparison is
paired. Three statistics per claim:

  - **Sign test** (exact binomial): in how many pairs does the effect go the
    claimed way? Robust to outliers and makes no distributional assumption.
  - **Bootstrap CI on the paired difference** (RTH - WEEKEND): stable.
  - **Bootstrap CI on the ratio of means**: reported because the README
    quotes a ratio, but see the warning printed when the denominator sits
    near zero - a ratio against ~0 is not a meaningful effect size.

This also ports the tracking-error analysis into the repo. It previously
existed only as an exploration script outside version control, which meant
the README cited a number nothing in the repository could reproduce.
"""
import json, math, os, random, sys, statistics as st
import datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import model

random.seed(20260921)
BOOT = 4000
Z = 1.959963985


def regime(ms):
    t = dt.datetime.utcfromtimestamp(ms / 1000)
    if t.weekday() >= 5:
        return "WEEKEND"
    return "RTH" if 13 <= t.hour < 20 else "OVERNIGHT"


def pairs_from_clusters():
    CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
    return [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
            for i in range(len(sy)) for j in range(i + 1, len(sy))]


# ---------------------------------------------------------------- stats --

def binom_two_sided(k, n):
    """Exact two-sided sign-test p-value: P(X at least this extreme | p=0.5)."""
    if n == 0:
        return float("nan")
    k = max(k, n - k)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def boot_ci(xs, ys, stat):
    """Paired bootstrap over pairs. Returns (lo, hi) at 95%."""
    n = len(xs)
    vals = []
    for _ in range(BOOT):
        idx = [random.randrange(n) for _ in range(n)]
        v = stat([xs[i] for i in idx], [ys[i] for i in idx])
        if v == v and not math.isinf(v):
            vals.append(v)
    if len(vals) < BOOT * 0.5:
        return (float("nan"), float("nan")), len(vals)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]), len(vals)


def mean_diff(a, b):
    return st.mean(a) - st.mean(b)


def mean_ratio(a, b):
    mb = st.mean(b)
    return st.mean(a) / mb if mb != 0 else float("inf")


def report(label, rth, wknd, higher_is, unit):
    """higher_is: which regime the claim says should be larger."""
    n = len(rth)
    diffs = [r - w for r, w in zip(rth, wknd)]
    if higher_is == "RTH":
        k = sum(1 for d in diffs if d > 0)
    else:
        k = sum(1 for d in diffs if d < 0)
    p = binom_two_sided(k, n)

    (dlo, dhi), _ = boot_ci(rth, wknd, mean_diff)
    (rlo, rhi), n_ok = boot_ci(rth, wknd, mean_ratio)

    m_r, m_w = st.mean(rth), st.mean(wknd)
    print(f"\n{label}")
    print("-" * 78)
    print(f"  pairs (n)                     : {n}")
    print(f"  mean RTH / mean WEEKEND       : {m_r:.4f} / {m_w:.4f} {unit}")
    print(f"  claim direction               : {higher_is} higher")
    print(f"  sign test                     : {k}/{n} pairs agree, "
          f"exact two-sided p = {p:.2g}")
    print(f"  difference RTH - WEEKEND      : {m_r - m_w:+.4f}  "
          f"95% CI [{dlo:+.4f}, {dhi:+.4f}]")
    ratio = m_r / m_w if m_w != 0 else float("inf")
    if rlo == rlo:
        print(f"  ratio RTH / WEEKEND           : {ratio:.2f}x  "
              f"95% CI [{rlo:.2f}x, {rhi:.2f}x]")
    else:
        print(f"  ratio RTH / WEEKEND           : {ratio:.2f}x  "
              f"95% CI undefined ({n_ok}/{BOOT} resamples finite)")

    denom_near_zero = abs(m_w) < 0.25 * abs(m_r)
    excludes_zero = (dlo > 0) or (dhi < 0)
    print("  verdict                       : ", end="")
    if excludes_zero and p < 0.05:
        print("SUPPORTED - difference CI excludes zero and sign test is significant")
    elif excludes_zero or p < 0.05:
        print("PARTIAL - one test supports it, the other does not")
    else:
        print("NOT SUPPORTED at 95%")
    if denom_near_zero:
        print("  warning                       : denominator is near zero, so the "
              "ratio is\n                                  unstable and should not "
              "be quoted as an effect size.\n                                  "
              "Report the difference instead.")
    return {"n": n, "k": k, "p": p, "diff": (m_r - m_w, dlo, dhi),
            "ratio": (ratio, rlo, rhi), "near_zero": denom_near_zero}


# ------------------------------------------------------------- claim 1 --

def funding_by_regime(prices, funding):
    rth, wknd = [], []
    for a, b in pairs_from_clusters():
        if a not in funding or b not in funding:
            continue
        beta, _ = model.hedge_ratio(prices, a, b)
        ks = sorted(set(funding[a]) & set(funding[b]))
        if len(ks) < 40:
            continue
        # Normalise to bp/day. Gold settles every 4h and equities every 8h, so a
        # per-interval mean compares two different units across pairs.
        ipd = model.intervals_per_day(ks)
        net = {}
        for k in ks:
            net.setdefault(regime(k), []).append(
                (funding[b][k] * beta - funding[a][k]) * ipd)
        allv = [v for l in net.values() for v in l]
        sign = 1 if st.mean(allv) > 0 else -1
        if len(net.get("RTH", [])) < 3 or len(net.get("WEEKEND", [])) < 3:
            continue
        rth.append(st.mean([x * sign for x in net["RTH"]]))
        wknd.append(st.mean([x * sign for x in net["WEEKEND"]]))
    return rth, wknd


# ------------------------------------------------------------- claim 2 --

def tracking_by_regime(prices):
    """Tracking error / own volatility, per regime, per pair.

    Beta is fitted on the first 60% of the joint history and held fixed;
    the ratio is measured on the remaining 40%, so the hedge is never
    evaluated on the data it was fitted to.
    """
    rth, wknd = [], []
    for a, b in pairs_from_clusters():
        pa, pb = prices.get(a, {}), prices.get(b, {})
        ks = sorted(set(pa) & set(pb))
        if len(ks) < 400:
            continue
        split = ks[int(len(ks) * 0.6)]
        beta, _ = model.hedge_ratio(prices, a, b, upto=split)
        buckets = {}
        for i in range(1, len(ks)):
            t0, t1 = ks[i - 1], ks[i]
            if t1 <= split or t1 - t0 > 3_700_000:
                continue
            if pa[t0] <= 0 or pb[t0] <= 0:
                continue
            ra = math.log(pa[t1] / pa[t0]) * 1e4
            rb = math.log(pb[t1] / pb[t0]) * 1e4
            buckets.setdefault(regime(t1), []).append((ra, rb - beta * ra))
        vals = {}
        for rg in ("RTH", "WEEKEND"):
            v = buckets.get(rg, [])
            if len(v) < 20:
                break
            vol = st.pstdev([x[0] for x in v])
            te = st.pstdev([x[1] for x in v])
            if vol <= 0:
                break
            vals[rg] = te / vol
        if len(vals) == 2:
            rth.append(vals["RTH"])
            wknd.append(vals["WEEKEND"])
    return rth, wknd


def main():
    prices, funding = model.load_prices(), model.load_funding()
    print(f"Regime significance tests - paired over pairs, {BOOT} bootstrap resamples")
    print("=" * 78)

    f_rth, f_wknd = funding_by_regime(prices, funding)
    r1 = report("CLAIM 1  Funding edge is lower on weekends than during US hours",
                f_rth, f_wknd, higher_is="RTH", unit="bp/day")

    t_rth, t_wknd = tracking_by_regime(prices)
    r2 = report("CLAIM 2  Tracking error / vol is higher on weekends than during US hours",
                t_rth, t_wknd, higher_is="WEEKEND", unit="(ratio)")

    print("\n" + "=" * 78)
    print("How to quote these:")
    for name, r in (("Funding edge", r1), ("Tracking error", r2)):
        d, lo, hi = r["diff"]
        ratio, rlo, rhi = r["ratio"]
        if r["near_zero"]:
            print(f"  {name}: difference {d:+.3f} (95% CI [{lo:+.3f}, {hi:+.3f}]); "
                  f"{r['k']}/{r['n']} pairs, p={r['p']:.2g}. Do not quote the ratio.")
        else:
            print(f"  {name}: {1/ratio if ratio else float('nan'):.2f}x "
                  f"weekend vs RTH; {r['k']}/{r['n']} pairs, p={r['p']:.2g}.")


if __name__ == "__main__":
    main()
