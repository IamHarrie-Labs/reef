"""Does execution cost actually rise when the US market is closed?

Every cost number elsewhere in this project comes from one order-book
snapshot taken during US regular trading hours - the most liquid window.
LIMITATIONS.md says outright that weekend and overnight costs are
"almost certainly higher than what's priced". This measures it instead of
assuming it.

Two snapshots, same pairs, same book-walk code:
  data/depth                          RTH      (US market open)
  data/depth_closed_<ts>              CLOSED   (US market shut)

    python src/depth_regime.py

Books cannot be backfilled, so this comparison only exists because both
snapshots were captured live. A single pair of snapshots is two points in
time, not a distribution - read the caveat at the end of the output.
"""
import json, os, sys, glob, statistics as st
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity

SIZES = [1_000, 5_000, 25_000, 100_000, 250_000]


def load_books_from(directory):
    out = {}
    for path in glob.glob(os.path.join(directory, "*.json")):
        sym = os.path.basename(path)[:-5]
        try:
            book = json.load(open(path, encoding="utf-8")).get("data") or {}
        except Exception:
            continue
        if not book.get("asks") or not book.get("bids"):
            continue
        out[sym] = {
            "asks": [(float(p), float(q)) for p, q in book["asks"]],
            "bids": [(float(p), float(q)) for p, q in book["bids"]],
        }
    return out


def find_closed_dir():
    hits = sorted(glob.glob(os.path.join(model.DATA, "depth_closed_*")))
    return hits[-1] if hits else None


def main():
    closed_dir = find_closed_dir()
    if not closed_dir:
        print("No closed-market snapshot found (data/depth_closed_*).")
        print("Capture one while the US market is shut:  python src/refresh.py --depth")
        return

    rth = load_books_from(os.path.join(model.DATA, "depth"))
    closed = load_books_from(closed_dir)
    prices, funding = model.load_prices(), model.load_funding()
    CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
    pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
             for i in range(len(sy)) for j in range(i + 1, len(sy))]

    label = os.path.basename(closed_dir).replace("depth_closed_", "")
    print(f"Round-trip execution cost, bp of leg-A notional")
    print(f"  RTH    : data/depth              (US market open)")
    print(f"  CLOSED : {os.path.basename(closed_dir)}  (US market shut)\n")
    print(f"{'PAIR':18s} {'SIZE':>9s} {'RTH bp':>8s} {'CLOSED bp':>10s} "
          f"{'DELTA':>8s} {'RATIO':>7s}")
    print("-" * 66)

    ratios_by_size = {}
    rows = 0
    for a, b in pairs:
        if a not in rth or b not in rth or a not in closed or b not in closed:
            continue
        beta, _ = model.hedge_ratio(prices, a, b)
        name = f"{a.replace('USDT','')}/{b.replace('USDT','')}"
        printed_pair = False
        for size in SIZES:
            c_rth = model.round_trip_cost(rth, a, b, size, beta)
            c_cls = model.round_trip_cost(closed, a, b, size, beta)
            if c_rth is None or c_cls is None:
                continue
            ratio = c_cls / c_rth if c_rth > 0 else float("nan")
            ratios_by_size.setdefault(size, []).append(ratio)
            print(f"{(name if not printed_pair else ''):18s} {size:>9,} "
                  f"{c_rth:8.1f} {c_cls:10.1f} {c_cls - c_rth:+8.1f} {ratio:7.2f}x")
            printed_pair = True
            rows += 1
        if printed_pair:
            print()

    if not rows:
        print("No pair had a usable book in both snapshots.")
        return

    print("=" * 66)
    print(f"{'SIZE':>9s} {'n':>4s} {'median cost ratio (CLOSED / RTH)':>38s}")
    print("-" * 66)
    all_ratios = []
    for size in SIZES:
        v = ratios_by_size.get(size, [])
        if not v:
            continue
        all_ratios += v
        print(f"{size:>9,} {len(v):>4d} {st.median(v):>37.2f}x")
    print(f"\nOverall median across {len(all_ratios)} pair-size combinations: "
          f"{st.median(all_ratios):.2f}x")

    print("\nCaveat: two snapshots, not two distributions. This says what the "
          "book looked like\nat one open moment and one closed moment - it is "
          "directional evidence, not a\nmeasured cost premium. recorder.py is "
          "accumulating the series that would\nsupport a real distribution.")


if __name__ == "__main__":
    main()
