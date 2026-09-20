"""Live snapshot recorder — depth + funding + mark price, on an interval.

Run unattended: `python src/recorder.py &`. Appends one JSON line per symbol
per snapshot to data/timeseries/<symbol>.jsonl. Safe to stop/restart; it just
resumes appending. This is the only data we cannot backfill after the fact —
everything else in this project was rebuilt from history in minutes.
"""
import json, os, sys, time, datetime as dt, urllib.request

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(DATA, "timeseries")
os.makedirs(OUT, exist_ok=True)

CL = json.load(open(os.path.join(DATA, "clusters.json")))
SYMS = sorted({s for c, sy in CL.items() if c != "CONTROL" for s in sy})
INTERVAL_S = int(os.environ.get("RECORDER_INTERVAL_S", 900))  # 15 min default


def get(url, timeout=15):
    try:
        return json.load(urllib.request.urlopen(url, timeout=timeout))
    except Exception as e:
        return {"code": "ERR", "msg": str(e)}


def snapshot_symbol(sym):
    depth = get(f"https://api.bitget.com/api/v2/mix/market/merge-depth"
                f"?symbol={sym}&productType=USDT-FUTURES&precision=scale0&limit=50")
    tick = get(f"https://api.bitget.com/api/v2/mix/market/ticker"
               f"?symbol={sym}&productType=USDT-FUTURES")
    row = {"ts": int(time.time() * 1000)}
    d = depth.get("data") or {}
    if d.get("asks") and d.get("bids"):
        row["asks"] = d["asks"][:20]
        row["bids"] = d["bids"][:20]
    t = (tick.get("data") or [{}])
    t = t[0] if isinstance(t, list) and t else (t if isinstance(t, dict) else {})
    for k in ("lastPr", "indexPrice", "markPrice", "fundingRate", "holdingAmount"):
        if k in t:
            row[k] = t[k]
    return row


def append(sym, row):
    with open(os.path.join(OUT, f"{sym}.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def main():
    n = 0
    print(f"[recorder] {len(SYMS)} symbols, every {INTERVAL_S}s, writing to {OUT}", flush=True)
    while True:
        t0 = time.time()
        ok = 0
        for s in SYMS:
            row = snapshot_symbol(s)
            if "asks" in row or "lastPr" in row:
                append(s, row)
                ok += 1
            time.sleep(0.12)  # be polite to the public endpoint
        n += 1
        print(f"[recorder] pass {n} @ {dt.datetime.utcnow():%Y-%m-%d %H:%M:%S}Z "
              f"— {ok}/{len(SYMS)} symbols ok — {time.time()-t0:.0f}s", flush=True)
        rest = INTERVAL_S - (time.time() - t0)
        if rest > 0:
            time.sleep(rest)


if __name__ == "__main__":
    main()
