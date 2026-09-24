"""Log a batch of short-hold verdicts so self-scoring can actually mature.

    python src/log_batch.py              # 1d and 3d holds, every priced pair
    python src/log_batch.py --holds 1 3 7

Why this exists: `score.py` can only grade a verdict once its holding
period has elapsed. Every verdict logged during the build used the 30-day
default, so none could be graded inside the project's own timeline - the
self-scoring claim had no evidence behind it. Logging short holds fixes
that, and logging them *now* is what makes them gradeable later.

These go through `verdict.answer()`, the same path a real question takes,
so each row is a genuine verdict with its evidence frozen at log time -
not a synthetic entry written straight into the ledger.
"""
import argparse, os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import model, verdict, ledger

BATCH_TAG = "batch"


def priced_pairs():
    """Every pair with funding history, as (ticker_a, ticker_b) shorthand."""
    export = os.path.join(model.DATA, "web_export.json")
    if os.path.exists(export):
        d = json.load(open(export))
        return [(p["a"].replace("USDT", ""), p["b"].replace("USDT", ""))
                for p in d["pairs"]]
    cl = json.load(open(os.path.join(model.DATA, "clusters.json")))
    out = []
    for name, syms in cl.items():
        if name == "CONTROL":
            continue
        for i in range(len(syms)):
            for j in range(i + 1, len(syms)):
                out.append((syms[i].replace("USDT", ""), syms[j].replace("USDT", "")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--holds", type=int, nargs="+", default=[1, 3])
    ap.add_argument("--size", type=int, default=25_000)
    args = ap.parse_args()

    pairs = priced_pairs()
    print(f"Logging {len(pairs) * len(args.holds)} verdicts "
          f"({len(pairs)} pairs x holds {args.holds}) at ${args.size:,}\n")

    logged, skipped = 0, 0
    for a, b in pairs:
        for hold in args.holds:
            q = (f"Is the {a}/{b} yield real for ${args.size:,} "
                 f"over {hold} {'day' if hold == 1 else 'days'}?")
            ev, _text = verdict.answer(q)
            if ev.get("error"):
                print(f"  skip  {a}/{b:12s} {hold}d  - {ev['error'][:54]}")
                skipped += 1
                continue
            cell = ev.get("risk_adjusted") or {}
            call = f"{ev.get('verdict', '?'):11s}"
            print(f"  {call} {ev['pair']:14s} {hold}d  "
                  f"net {cell.get('net_bp', 0):8.1f}bp  "
                  f"sharpe {cell.get('sharpe', 0):6.2f}")
            logged += 1

    print(f"\n{logged} logged, {skipped} skipped -> {ledger.PATH}")
    print(f"Ledger now holds {len(ledger.read_all())} verdicts.")
    print("\nRun `python src/refresh.py --prices` then `python src/score.py` "
          "once these holding periods elapse.")


if __name__ == "__main__":
    main()
