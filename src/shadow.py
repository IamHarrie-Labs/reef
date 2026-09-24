"""Shadow desk: paper execution against live Bitget books, graded by score.py.

    python src/shadow.py            # close due positions, then open due batches
    python src/shadow.py --status   # what is open, closed and graded

Every batch freezes a prediction in the ledger through the same code path a
typed question uses (verdict.build_evidence), then records hypothetical fills
by walking the live order book at that moment. When the hold ends it exits
against the book at that time, fetches the exchange's mark price at every
funding settlement in between, and stores the execution for score.py.

These are shadow fills, not trades: no order is placed and the book is not
moved by our size. What they test is the part of the model a backtest cannot:
whether the predicted execution cost and funding carry show up when the
trade is actually walked through a later book.
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity, verdict, ledger, refresh
from score import EXECUTIONS, EXIT_GRACE_MS, execution_key

SHADOW = os.path.join(model.DATA, "shadow")
OPEN = os.path.join(SHADOW, "open.json")
STATE = os.path.join(SHADOW, "state.json")
MARKS = os.path.join(SHADOW, "marks.json")
SIZE = 25_000
BATCH_EVERY_H = {1: 8, 3: 24}  # hold_days -> hours between batches
DAY_MS = 86_400_000


def _read(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def mid(book):
    return (book["asks"][0][0] + book["bids"][0][0]) / 2


def vwap(levels, notional=None, qty=None):
    """Average fill price for a USDT notional or a contract quantity. None if too thin."""
    rem_n, rem_q, spent, got = notional, qty, 0.0, 0.0
    for p, q in levels:
        take_q = q
        if rem_n is not None:
            take_q = min(q, rem_n / p)
            rem_n -= take_q * p
        else:
            take_q = min(q, rem_q)
            rem_q -= take_q
        spent += take_q * p
        got += take_q
        if (rem_n is not None and rem_n <= 1e-9) or (rem_q is not None and rem_q <= 1e-12):
            return spent / got
    return None


def mark_at(sym, t, cache):
    key = str(t)
    if key in cache.get(sym, {}):
        return cache[sym][key]
    rows = refresh._get(f"{refresh.BASE}/history-mark-candles?symbol={sym}&productType={refresh.PT}"
                        f"&granularity=1m&startTime={t}&endTime={t + 60_000}&limit=5")
    for row in rows or []:
        if int(row[0]) == t:
            cache.setdefault(sym, {})[key] = float(row[1])
            return cache[sym][key]
    return None


def open_batch(hold, now_ms, prices, funding, books, positions):
    with open(os.path.join(model.DATA, "clusters.json"), encoding="utf-8") as f:
        CL = json.load(f)
    pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]
    opened = 0
    for a, b in pairs:
        r = capacity.analyse_pair(prices, funding, books, a, b)
        ra = capacity.risk_adjusted(r, SIZE, hold) if r else None
        if not ra:
            continue
        ev = verdict.build_evidence(r, ra, SIZE, hold, prices, funding, books, "shadow-scheduler")
        legs = {}
        for sym, key in ((a, "a"), (b, "b")):
            w = ev["edge"]["weights"][key]
            side = "asks" if w > 0 else "bids"
            px = vwap(books[sym][side], notional=SIZE * abs(w))
            if px is None:
                legs = None
                break
            legs[sym] = {"qty": SIZE * w / px, "entry_price": px, "entry_mid": mid(books[sym]),
                         "entry_ts": now_ms, "entry_book_ts": books[sym].get("timestamp")}
        if not legs:
            continue
        ledger.append({"ts": now_ms, "question": f"[shadow desk] {ev['pair']} at ${SIZE:,} for {hold} days",
                       "query": {"a": a, "b": b, "size": SIZE, "hold_days": hold,
                                 "parsed_by": "shadow-scheduler"},
                       "evidence": ev, "shadow": True})
        positions.append({"id": execution_key(now_ms, ev["pair"], hold), "ledger_ts": now_ms,
                          "pair": ev["pair"], "hold_days": hold, "end_ms": now_ms + hold * DAY_MS,
                          "verdict": ev["verdict"], "legs": legs})
        opened += 1
    return opened


def close_due(now_ms, books, funding, positions, executions, marks):
    still_open, closed, missed = [], 0, 0
    for pos in positions:
        if now_ms < pos["end_ms"]:
            still_open.append(pos)
            continue
        if now_ms > pos["end_ms"] + EXIT_GRACE_MS:
            executions[pos["id"]] = {"execution_type": "shadow", "status": "missed_exit_window",
                                     "pair": pos["pair"], "hold_days": pos["hold_days"]}
            missed += 1
            continue
        execution = {}
        for sym, leg in pos["legs"].items():
            if sym not in books:
                break
            q = leg["qty"]
            px = vwap(books[sym]["bids" if q > 0 else "asks"], qty=abs(q))
            if px is None:
                break
            execution[sym] = {**leg, "exit_price": px, "exit_mid": mid(books[sym]), "exit_ts": now_ms,
                              "exit_book_ts": books[sym].get("timestamp"),
                              "fees_usdt": abs(q) * (leg["entry_price"] + px) * model.TAKER_BP / 1e4,
                              "settlement_marks": {}}
        if len(execution) != len(pos["legs"]):
            still_open.append(pos)  # retry next cycle while inside the grace window
            continue
        executions[pos["id"]] = {"execution_type": "shadow", "status": "closed",
                                 "pair": pos["pair"], "hold_days": pos["hold_days"],
                                 "execution": execution}
        closed += 1
    positions[:] = still_open
    return closed, missed


def backfill_marks(executions, funding, marks):
    """Fetch the mark price at each funding settlement inside every closed hold."""
    filled = 0
    for rec in executions.values():
        for sym, leg in (rec.get("execution") or {}).items():
            end = leg["entry_ts"] + rec["hold_days"] * DAY_MS
            for t in funding.get(sym, {}):
                if leg["entry_ts"] < t <= end and str(t) not in leg["settlement_marks"]:
                    m = mark_at(sym, t, marks)
                    if m is not None:
                        leg["settlement_marks"][str(t)] = m
                        filled += 1
    return filled


def run(now_ms=None):
    now_ms = now_ms or int(time.time() * 1000)
    prices, books = model.load_prices(), model.load_books()
    funding_window, funding_archive = model.load_funding(), model.load_funding("archive")
    positions = _read(OPEN, [])
    executions = _read(EXECUTIONS, {})
    marks = _read(MARKS, {})
    state = _read(STATE, {})

    closed, missed = close_due(now_ms, books, funding_archive, positions, executions, marks)
    filled = backfill_marks(executions, funding_archive, marks)
    opened = {}
    for hold, every_h in BATCH_EVERY_H.items():
        last = state.get(f"last_batch_{hold}d", 0)
        if now_ms - last >= every_h * 3_600_000 - 10 * 60_000:
            opened[hold] = open_batch(hold, now_ms, prices, funding_window, books, positions)
            state[f"last_batch_{hold}d"] = now_ms

    _write(OPEN, positions)
    _write(EXECUTIONS, executions)
    _write(MARKS, marks)
    _write(STATE, state)
    print(f"[shadow] opened {opened or 'none'}, closed {closed}, missed {missed}, "
          f"marks filled {filled}, open now {len(positions)}")


def status():
    positions, executions = _read(OPEN, []), _read(EXECUTIONS, {})
    by = {}
    for rec in executions.values():
        by[rec.get("status")] = by.get(rec.get("status"), 0) + 1
    print(f"open positions: {len(positions)}")
    print(f"executions: {json.dumps(by)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    status() if args.status else run()
