"""Signed-notional carry estimates, in basis points of B-leg reference N.

Base portfolio: A=-beta*N, B=N; direction multiplies both signed weights.
Inverse relationships may require same-side positions. Expected income is
historical held-out funding, not a forecast of spread convergence. Residual
price volatility is a separate risk approximation. Book walks are snapshots.
Funding schedules are inferred per instrument and aggregated on complete days.
"""
import json, math, os, statistics as st

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
INTERVALS_PER_DAY = 3          # fallback only - 8h; real cadence is derived per pair
TAKER_BP = 6.0                 # per leg, per side


def _load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def load_prices():
    return {s: {int(k): v for k, v in m.items()} for s, m in _load("prices.json").items()}


def load_funding(source="window"):
    """Funding history in bp per interval, {symbol: {ts: bp}}.

    source="window"  - the latest 100 intervals the endpoint serves. Default,
                       so headline numbers stay comparable across refreshes.
    source="archive" - every interval ever captured, accumulated across
                       refreshes by funding_archive.py. Longer than any
                       single window the endpoint can return.
    """
    d = os.path.join(DATA, "funding_archive" if source == "archive" else "funding")
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in os.listdir(d):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(d, fn), encoding="utf-8") as f:
            rows = json.load(f).get("data") or []
        out[fn[:-5]] = {int(r["fundingTime"]): float(r["fundingRate"]) * 1e4 for r in rows}
    return out


def load_books():
    out = {}
    d = os.path.join(DATA, "depth")
    for fn in os.listdir(d):
        with open(os.path.join(d, fn), encoding="utf-8") as f:
            b = json.load(f).get("data") or {}
        if not b.get("asks"):
            continue
        out[fn[:-5]] = {
            "asks": [(float(p), float(q)) for p, q in b["asks"]],
            "bids": [(float(p), float(q)) for p, q in b["bids"]],
            "timestamp": b.get("ts"),
        }
    return out


def hedge_ratio(prices, a, b, upto=None):
    """OLS beta of b's returns on a's, fitted on data at or before `upto`."""
    ks = sorted(set(prices.get(a, {})) & set(prices.get(b, {})))
    sxx = sxy = 0.0
    n = 0
    for i in range(1, len(ks)):
        t0, t1 = ks[i - 1], ks[i]
        if t1 - t0 > 3_700_000:
            continue
        if upto and t1 > upto:
            break
        ra = math.log(prices[a][t1] / prices[a][t0])
        rb = math.log(prices[b][t1] / prices[b][t0])
        sxx += ra * ra
        sxy += ra * rb
        n += 1
    return (sxy / sxx if sxx > 0 else 1.0), n


def residual_vol(prices, a, b, beta, after=None):
    """Std of the beta-hedged residual return, in bp per hour."""
    ks = sorted(set(prices.get(a, {})) & set(prices.get(b, {})))
    res = []
    for i in range(1, len(ks)):
        t0, t1 = ks[i - 1], ks[i]
        if t1 - t0 > 3_700_000 or (after and t1 <= after):
            continue
        ra = math.log(prices[a][t1] / prices[a][t0]) * 1e4
        rb = math.log(prices[b][t1] / prices[b][t0]) * 1e4
        res.append(rb - beta * ra)
    return (st.pstdev(res) if len(res) > 2 else 0.0), len(res)


def intervals_per_day(timestamps):
    """Funding settlements per day, from the median spacing of timestamps.

    Median rather than mean so a single missing interval doesn't shift it.
    Falls back to 8h only when there's too little data to measure.
    """
    ts = sorted(timestamps)
    if len(ts) < 3:
        return INTERVALS_PER_DAY
    gaps = sorted(ts[i] - ts[i - 1] for i in range(1, len(ts)))
    median_h = gaps[len(gaps) // 2] / 3_600_000
    if median_h <= 0:
        return INTERVALS_PER_DAY
    return 24 / median_h


def funding_days(funding, a, b, beta):
    """Complete UTC days; sum each leg independently (including unequal cadences).

    Base signed notionals per $1 reference: A=-beta, B=+1.
    Missing settlements invalidate a day rather than silently becoming zero.
    """
    if not funding.get(a) or not funding.get(b):
        return []
    day = 86_400_000
    start = max(min(funding[a]), min(funding[b])) // day + 1
    end = min(max(funding[a]), max(funding[b])) // day
    expected = {x: round(intervals_per_day(funding[x])) for x in (a, b)}
    rows = []
    for d in range(start, end):
        vals = {x: [v for t, v in funding[x].items() if d*day <= t < (d+1)*day] for x in (a,b)}
        if any(len(vals[x]) != expected[x] for x in (a,b)):
            continue
        rows.append((d*day, beta*sum(vals[a])-sum(vals[b])))
    return rows


def funding_edge(funding, a, b, beta):
    """Choose direction on first 60% of complete days; evaluate remaining days.

    This is a historical funding holdout estimate, not realised trading P&L.
    """
    rows = funding_days(funding, a, b, beta)
    cut = int(len(rows)*0.6)
    if cut < 3 or len(rows)-cut < 3:
        return None
    sign = 1 if st.mean(v for _,v in rows[:cut]) >= 0 else -1
    net = [sign*v for _,v in rows[cut:]]
    mean = st.mean(net)
    weights = {"a": -sign*beta, "b": sign}
    side = lambda w: "long" if w > 0 else "short" if w < 0 else "flat"
    return {"bp_per_interval": mean, "intervals_per_day": 1,
            "funding_interval_h": 24, "bp_per_day": mean,
            "annual_pct": mean*365/100, "sd": st.pstdev(net),
            "consistency_pct": 100*sum(v>0 for v in net)/len(net),
            "direction": f"{side(weights['a'])} A / {side(weights['b'])} B",
            "direction_sign": sign, "weights": weights,
            "n_intervals": len(net), "history_days": len(net),
            "sample_unit": "complete UTC day", "validation_series": net,
            "direction_train_end": rows[cut-1][0],
            "validation_start": rows[cut][0], "validation_end": rows[-1][0],
            "settlements_per_day": {x: intervals_per_day(funding[x]) for x in (a,b)}}


def walk_book(book, notional, side):
    """VWAP slippage vs mid, in bp, to fill `notional` USDT. None if book too thin."""
    best_ask, best_bid = book["asks"][0][0], book["bids"][0][0]
    mid = (best_ask + best_bid) / 2
    levels = book["asks"] if side == "buy" else book["bids"]
    rem, spent, qty = notional, 0.0, 0.0
    for p, q in levels:
        take = min(rem, p * q)
        spent += take
        qty += take / p
        rem -= take
        if rem <= 1e-9:
            break
    if rem > 1e-6 or qty <= 0:
        return None
    return abs(spent / qty - mid) / mid * 1e4


def round_trip_cost(books, a, b, notional, beta):
    """Snapshot round trip in bp of reference notional N (B=N, A=|beta|N).

    Both exits reuse today's book as an explicit scenario assumption.
    """
    if not math.isfinite(notional) or notional <= 0 or not math.isfinite(beta):
        raise ValueError("Notional must be positive and beta finite")
    dollars = 0.0
    for symbol, weight in ((a, abs(beta)), (b, 1.0)):
        if weight == 0:
            continue
        if symbol not in books:
            return None
        leg_notional = notional*weight
        for side in ("buy", "sell"):
            slip = walk_book(books[symbol], leg_notional, side)
            if slip is None:
                return None
            dollars += leg_notional*(slip+TAKER_BP)/1e4
    return dollars/notional*1e4


def net_carry(edge, cost_bp, hold_days):
    """Net bp and annualized % for holding `hold_days`, cost amortized once."""
    if not math.isfinite(hold_days) or hold_days <= 0:
        raise ValueError("Holding days must be positive and finite")
    gross = edge["bp_per_day"] * hold_days
    net = gross - cost_bp
    return {
        "gross_bp": gross,
        "cost_bp": cost_bp,
        "net_bp": net,
        "annual_pct": net / 100 * (365 / hold_days),
        "breakeven_days": cost_bp / edge["bp_per_day"] if edge["bp_per_day"] > 0 else float("inf"),
    }
