"""Carry model for same-underlying RWA perpetual pairs.

A pair trade is long one leg, short the other, beta-hedged. Its P&L has three
parts: funding collected each interval, mean reversion of the residual spread,
and execution cost paid once on entry and once on exit.

Funding cadence is NOT uniform. Most RWA contracts settle every 8h, but the
gold contracts (XAU, XAUT, PAXG) settle every 4h. The cadence is derived from
each pair's own funding timestamps rather than assumed - an earlier version
hardcoded 8h for every pair and understated gold's carry by half.

The first two scale with holding period. The third does not. That asymmetry is
the whole model: a trade that loses money round-tripped every 6 hours can make
money held for a month, and the capacity curve is where those two facts meet.
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


def funding_edge(funding, a, b, beta):
    """Net funding per interval for the better direction, in bp of leg-A notional.

    Positive funding means longs pay shorts. Long A / short B therefore nets
    (fundingB * beta - fundingA). We evaluate both directions and return the
    profitable one along with how often its sign held.
    """
    if a not in funding or b not in funding:
        return None
    ks = sorted(set(funding[a]) & set(funding[b]))
    if len(ks) < 30:
        return None
    net = [funding[b][k] * beta - funding[a][k] for k in ks]
    mean = st.mean(net)
    direction = "long A / short B" if mean > 0 else "short A / long B"
    if mean < 0:
        net = [-x for x in net]
        mean = -mean
    sd = st.pstdev(net) if len(net) > 2 else 0.0
    consistency = 100 * sum(1 for x in net if x > 0) / len(net)
    ipd = intervals_per_day(ks)
    return {
        "bp_per_interval": mean,
        "intervals_per_day": ipd,
        "funding_interval_h": 24 / ipd,
        "bp_per_day": mean * ipd,
        "annual_pct": mean * ipd * 365 / 100,
        "sd": sd,
        "consistency_pct": consistency,
        "direction": direction,
        "n_intervals": len(ks),
        "history_days": (ks[-1] - ks[0]) / 86_400_000,
        # funding Sharpe: per-interval mean/sd scaled to a year
        "sharpe": (mean / sd * math.sqrt(ipd * 365)) if sd > 0 else float("nan"),
    }


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
    """Entry + exit cost for the pair, in bp of leg-A notional. Paid once."""
    if a not in books or b not in books:
        return None
    nb = notional * abs(beta)
    legs = [walk_book(books[a], notional, "buy"), walk_book(books[a], notional, "sell"),
            walk_book(books[b], nb, "sell"),      walk_book(books[b], nb, "buy")]
    if any(x is None for x in legs):
        return None
    slip = sum(legs)
    fees = TAKER_BP * 2 * (1 + abs(beta))     # both legs, both sides
    return slip + fees


def net_carry(edge, cost_bp, hold_days):
    """Net bp and annualized % for holding `hold_days`, cost amortized once."""
    gross = edge["bp_per_day"] * hold_days
    net = gross - cost_bp
    return {
        "gross_bp": gross,
        "cost_bp": cost_bp,
        "net_bp": net,
        "annual_pct": net / 100 * (365 / hold_days),
        "breakeven_days": cost_bp / edge["bp_per_day"] if edge["bp_per_day"] > 0 else float("inf"),
    }
