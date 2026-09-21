"""Did the edges this tool found actually survive?

Bitget's funding endpoint returns only the most recent 100 intervals, so
every refresh rolls the window forward. That makes each refresh an
unplanned out-of-sample test: the same pair, the same model, a later
window. An edge that was real should persist. An edge that was a sampling
artifact should decay.

    python src/edge_decay.py

Compares the funding edge computed on two windows:
    data/funding_prev   earlier window (recovered from git history)
    data/funding        current window

This is the honest version of a backtest. Nothing here was re-fitted or
re-selected - the pairs, the hedge ratios, and the model are identical
across both runs. Only the funding window moved.
"""
import json, os, sys, statistics as st
import datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity

PREV_DIR = os.path.join(model.DATA, "funding_prev")


def load_funding_from(directory):
    out = {}
    if not os.path.isdir(directory):
        return out
    for fn in os.listdir(directory):
        if not fn.endswith(".json"):
            continue
        try:
            rows = json.load(open(os.path.join(directory, fn), encoding="utf-8")).get("data") or []
        except Exception:
            continue
        out[fn[:-5]] = {int(r["fundingTime"]): float(r["fundingRate"]) * 1e4 for r in rows}
    return out


def window_of(funding):
    ks = [k for m in funding.values() for k in m]
    if not ks:
        return "?", "?"
    return (dt.datetime.utcfromtimestamp(min(ks) / 1000).strftime("%Y-%m-%d"),
            dt.datetime.utcfromtimestamp(max(ks) / 1000).strftime("%Y-%m-%d"))


def main():
    if not os.path.isdir(PREV_DIR):
        print("No earlier funding window found at data/funding_prev/.")
        print("Recover one from git history to enable this comparison.")
        return

    prices, books = model.load_prices(), model.load_books()
    f_prev, f_now = load_funding_from(PREV_DIR), model.load_funding()
    CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
    pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]

    pa, pb = window_of(f_prev)
    na, nb = window_of(f_now)
    print(f"Funding edge decay, same pairs and same model, two windows\n")
    print(f"  EARLIER : {pa} -> {pb}")
    print(f"  CURRENT : {na} -> {nb}\n")
    print(f"{'PAIR':20s} {'gross% then':>12s} {'gross% now':>11s} "
          f"{'retained':>9s} {'consist then':>13s} {'now':>6s} "
          f"{'Sharpe then':>12s} {'now':>7s}")
    print("-" * 96)

    rows, survived_then, survived_now = [], 0, 0
    for a, b in pairs:
        r_prev = capacity.analyse_pair(prices, f_prev, books, a, b)
        r_now = capacity.analyse_pair(prices, f_now, books, a, b)
        if not r_prev or not r_now:
            continue
        ra_prev = capacity.risk_adjusted(r_prev, 25_000, 30)
        ra_now = capacity.risk_adjusted(r_now, 25_000, 30)
        if not ra_prev or not ra_now:
            continue
        g_then, g_now = r_prev["edge"]["annual_pct"], r_now["edge"]["annual_pct"]
        retained = (g_now / g_then) if g_then > 0 else float("nan")
        if ra_prev["sharpe"] > 0.5:
            survived_then += 1
        if ra_now["sharpe"] > 0.5:
            survived_now += 1
        rows.append((r_now["pair"], g_then, g_now, retained,
                     r_prev["edge"]["consistency_pct"], r_now["edge"]["consistency_pct"],
                     ra_prev["sharpe"], ra_now["sharpe"]))

    rows.sort(key=lambda x: -x[1])
    for name, g_then, g_now, ret, c_then, c_now, s_then, s_now in rows:
        flag = "  <-- was the only survivor" if s_then > 0.5 and s_now <= 0.5 else ""
        print(f"{name:20s} {g_then:12.1f} {g_now:11.1f} "
              f"{(ret * 100 if ret == ret else float('nan')):8.0f}% "
              f"{c_then:12.0f}% {c_now:5.0f}% {s_then:12.2f} {s_now:7.2f}{flag}")

    if not rows:
        print("No pair could be priced on both windows.")
        return

    rets = [r[3] for r in rows if r[3] == r[3] and r[1] > 0]
    print("\n" + "=" * 96)
    print(f"Pairs priced on both windows      : {len(rows)}")
    print(f"Cleared Sharpe 0.5 in EARLIER     : {survived_then}")
    print(f"Cleared Sharpe 0.5 in CURRENT     : {survived_now}")
    if rets:
        print(f"Median gross edge retained        : {st.median(rets) * 100:.0f}%")
        print(f"Pairs that kept >80% of the edge  : "
              f"{sum(1 for r in rets if r > 0.8)}/{len(rets)}")
    print("\nThe windows overlap by roughly two weeks, so these are not "
          "independent samples.\nA pair whose edge nearly vanished across a "
          "partly-overlapping window was\nnever carrying a stable edge to "
          "begin with.")


if __name__ == "__main__":
    main()
