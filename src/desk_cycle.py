"""One cycle of the live desk. Run hourly by .github/workflows/desk.yml.

    python src/desk_cycle.py

refresh (funding, books, recent candles) -> shadow desk (exit, marks, open)
-> on-chain gold check (Chainlink, independent of Bitget) -> Bitcoin anchor
-> web export (so the site shows the anchor it just made). Each step is
isolated so a failed fetch leaves the previous cycle's data in place rather
than a half-written state.
"""
import os, subprocess, sys, time

HERE = os.path.dirname(__file__)
STEPS = [
    ("refresh", ["refresh.py", "--funding", "--depth"]),
    ("prices", ["refresh.py", "--prices", "--recent"]),
    ("shadow", ["shadow.py"]),
    ("onchain", ["onchain_gold.py"]),
    ("anchor", ["anchor.py"]),
    ("export", ["export_web.py"]),
]
# A failure here aborts the cycle before it writes anything - never price or
# grade against a half-refreshed state. Every other step degrades on its own
# (onchain_gold.py writes "unavailable" rather than a fabricated 0; anchor.py
# just anchors next cycle) and must not block the commit that follows.
CRITICAL = {"refresh", "shadow", "export"}


def main():
    failed = []
    for name, args in STEPS:
        t = time.time()
        p = subprocess.run([sys.executable, os.path.join(HERE, args[0]), *args[1:]])
        print(f"[cycle] {name}: {'ok' if p.returncode == 0 else 'FAILED'} ({time.time() - t:.0f}s)", flush=True)
        if p.returncode:
            failed.append(name)
            if name in CRITICAL:
                break
    critical_failed = [f for f in failed if f in CRITICAL]
    return 1 if critical_failed else 0


if __name__ == "__main__":
    sys.exit(main())
