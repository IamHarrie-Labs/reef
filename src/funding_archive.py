"""Accumulate funding history across refreshes, beyond what the endpoint serves.

Bitget's `history-fund-rate` returns only the most recent 100 intervals -
about five weeks. That window is the single biggest limitation on every
number in this project, and it cannot be backfilled: once an interval rolls
off the end, the endpoint will not return it again.

The only fix is to keep what each refresh sees. This merges every window
into `data/funding_archive/`, keyed by funding timestamp, so the history
grows by one interval every eight hours for as long as refreshes keep
running.

    python src/funding_archive.py            # absorb all known windows, report coverage
    python src/funding_archive.py --status   # coverage only

`refresh.py` calls `absorb()` on every funding pull, so the archive grows
automatically. The first run also seeds it from `data/funding_prev`, the
earlier window recovered from git history.
"""
import argparse, json, os, sys
import datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import model

ARCHIVE = os.path.join(model.DATA, "funding_archive")
SOURCES = ["funding_prev", "funding"]
INTERVAL_MS = 8 * 3_600_000


def _read(path):
    try:
        return json.load(open(path, encoding="utf-8")).get("data") or []
    except Exception:
        return []


def absorb(symbol, rows):
    """Merge `rows` for one symbol into the archive. Returns intervals added."""
    os.makedirs(ARCHIVE, exist_ok=True)
    path = os.path.join(ARCHIVE, f"{symbol}.json")
    merged = {str(r["fundingTime"]): r for r in _read(path)}
    before = len(merged)
    for r in rows:
        merged.setdefault(str(r["fundingTime"]), r)
    ordered = sorted(merged.values(), key=lambda r: int(r["fundingTime"]))
    json.dump({"code": "00000", "data": ordered}, open(path, "w"))
    return len(merged) - before


def absorb_directory(name):
    d = os.path.join(model.DATA, name)
    if not os.path.isdir(d):
        return 0, 0
    added, files = 0, 0
    for fn in os.listdir(d):
        if fn.endswith(".json"):
            added += absorb(fn[:-5], _read(os.path.join(d, fn)))
            files += 1
    return files, added


def coverage():
    """Per-symbol archive span, and how it compares to a single window."""
    rows = []
    if not os.path.isdir(ARCHIVE):
        return rows
    for fn in sorted(os.listdir(ARCHIVE)):
        if not fn.endswith(".json"):
            continue
        ts = sorted(int(r["fundingTime"]) for r in _read(os.path.join(ARCHIVE, fn)))
        if not ts:
            continue
        expected = (ts[-1] - ts[0]) // INTERVAL_MS + 1
        rows.append((fn[:-5], len(ts), ts[0], ts[-1], expected - len(ts)))
    return rows


def report():
    rows = coverage()
    if not rows:
        print("Archive is empty.")
        return
    print(f"\n{'SYMBOL':18s} {'intervals':>10s} {'vs window':>10s} "
          f"{'from':>12s} {'to':>12s} {'gaps':>5s}")
    print("-" * 72)
    for sym, n, t0, t1, gaps in rows:
        f = lambda ms: dt.datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d")
        print(f"{sym:18s} {n:>10d} {n / 100:>9.2f}x {f(t0):>12s} {f(t1):>12s} {gaps:>5d}")
    ns = sorted(r[1] for r in rows)
    print(f"\n{len(rows)} symbols. Median {ns[len(ns) // 2]} intervals "
          f"({ns[len(ns) // 2] / 100:.2f}x a single endpoint window).")
    if any(r[4] for r in rows):
        print("Gaps are intervals missing between the archive's first and last "
              "timestamp -\nusually a refresh that didn't run long enough "
              "ago to catch them.")
    print("\nThe archive grows by one interval every 8 hours while refreshes run. "
          "Every\nmetric in this project can read it with "
          "model.load_funding(source='archive').")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if not args.status:
        for name in SOURCES:
            files, added = absorb_directory(name)
            if files:
                print(f"absorbed data/{name:14s} {files:3d} symbols, "
                      f"+{added} new intervals")
    report()


if __name__ == "__main__":
    main()
