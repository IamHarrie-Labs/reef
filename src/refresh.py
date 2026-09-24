"""Refresh cached market data from Bitget's public endpoints.

    python src/refresh.py            # prices + funding + depth
    python src/refresh.py --prices   # just hourly candles
    python src/refresh.py --funding  # just funding-rate history
    python src/refresh.py --depth    # just order books (point-in-time)

Everything here is a public endpoint - no API key, no account. Prices and
funding are history and can be backfilled at any time; depth is a snapshot
of *now* and cannot, which is why `recorder.py` exists separately.

score.py can only grade a verdict once price history covers the period
after it was logged, so this must run before scoring matures.
"""
import argparse, json, math, os, sys, time, urllib.request
import datetime as dt
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import model, funding_archive

BASE = "https://api.bitget.com/api/v2/mix/market"
PT = "USDT-FUTURES"
HOUR_MS = 3_600_000


def _get(url, tries=4):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                d = json.load(r)
            if d.get("code") == "00000":
                return d.get("data")
        except Exception:
            pass
        time.sleep(0.6 * (attempt + 1))
    return None


def symbols():
    """Every symbol referenced by clusters.json, CONTROL included."""
    cl = json.load(open(os.path.join(model.DATA, "clusters.json")))
    return sorted({s for syms in cl.values() for s in syms})


# ------------------------------------------------------------- prices --

def fetch_candles(sym, max_pages=14):
    """Hourly closes, newest-first pagination, merged into {ts: close}."""
    out, end = {}, None
    for _ in range(max_pages):
        url = f"{BASE}/history-candles?symbol={sym}&productType={PT}&granularity=1H&limit=200"
        if end:
            url += f"&endTime={end}"
        rows = _get(url)
        if not rows:
            break
        first = int(rows[0][0])
        new = False
        for row in rows:
            k = int(row[0])
            if k not in out:
                out[k] = float(row[4])
                new = True
        if not new or end == first - 1:
            break
        end = first - 1
        time.sleep(0.15)
    return sym, out


def refresh_prices(max_pages=14):
    path = os.path.join(model.DATA, "prices.json")
    existing = {}
    if os.path.exists(path):
        existing = {s: {int(k): v for k, v in m.items()}
                    for s, m in json.load(open(path)).items()}
    syms = symbols()
    print(f"[prices] fetching {len(syms)} symbols...")
    merged, added = {}, 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for sym, fresh in ex.map(lambda s: fetch_candles(s, max_pages), syms):
            old = existing.get(sym, {})
            combined = dict(old)
            combined.update(fresh)
            added += len(combined) - len(old)
            merged[sym] = combined
            if combined:
                ks = sorted(combined)
                print(f"  {sym:18s} {len(combined):5d} bars  "
                      f"{dt.datetime.utcfromtimestamp(ks[0]/1000):%Y-%m-%d} -> "
                      f"{dt.datetime.utcfromtimestamp(ks[-1]/1000):%Y-%m-%d}")
            else:
                print(f"  {sym:18s} NO DATA")
    # keep any symbol we had before but couldn't refresh
    for sym, old in existing.items():
        merged.setdefault(sym, old)
    json.dump({s: {str(k): v for k, v in m.items()} for s, m in merged.items()},
              open(path, "w"))
    print(f"[prices] +{added} new bars -> {path}")


# ------------------------------------------------------------ funding --

def refresh_funding():
    d = os.path.join(model.DATA, "funding")
    os.makedirs(d, exist_ok=True)
    syms = symbols()
    print(f"[funding] fetching {len(syms)} symbols...")
    ok, archived = 0, 0
    for sym in syms:
        rows = _get(f"{BASE}/history-fund-rate?symbol={sym}&productType={PT}&pageSize=100")
        if not rows:
            print(f"  {sym:18s} no funding history")
            continue
        json.dump({"code": "00000", "data": rows},
                  open(os.path.join(d, f"{sym}.json"), "w"))
        archived += funding_archive.absorb(sym, rows)
        ok += 1
        time.sleep(0.1)
    print(f"[funding] {ok}/{len(syms)} written -> {d}")
    print(f"[funding] +{archived} new intervals archived -> data/funding_archive "
          f"(history the endpoint will stop serving)")


# -------------------------------------------------------------- depth --

def refresh_depth():
    d = os.path.join(model.DATA, "depth")
    os.makedirs(d, exist_ok=True)
    syms = symbols()
    print(f"[depth] snapshotting {len(syms)} books (point-in-time, not backfillable)...")
    ok = 0
    for sym in syms:
        book = _get(f"{BASE}/merge-depth?symbol={sym}&productType={PT}"
                    f"&precision=scale0&limit=max")
        if not book or not book.get("asks"):
            print(f"  {sym:18s} no book")
            continue
        json.dump({"code": "00000", "data": book},
                  open(os.path.join(d, f"{sym}.json"), "w"))
        ok += 1
        time.sleep(0.1)
    print(f"[depth] {ok}/{len(syms)} written -> {d}")
    print(f"[depth] snapshot taken {dt.datetime.utcnow():%Y-%m-%d %H:%M}Z "
          f"({'WEEKEND' if dt.datetime.utcnow().weekday() >= 5 else 'weekday'})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", action="store_true")
    ap.add_argument("--funding", action="store_true")
    ap.add_argument("--depth", action="store_true")
    ap.add_argument("--recent", action="store_true", help="only the latest candle pages")
    a = ap.parse_args()
    everything = not (a.prices or a.funding or a.depth)
    if a.prices or everything:
        refresh_prices(2 if a.recent else 14)
    if a.funding or everything:
        refresh_funding()
    if a.depth or everything:
        refresh_depth()
