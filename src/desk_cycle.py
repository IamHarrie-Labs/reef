"""One cycle of the live desk. Run hourly by .github/workflows/desk.yml.

    python src/desk_cycle.py

refresh (funding, books, recent candles) -> shadow desk (exit, marks, open)
-> Bitcoin anchor -> web export (so the site shows the anchor it just made). Each step is isolated so a failed fetch
leaves the previous cycle's data in place rather than a half-written state.
"""
import os, subprocess, sys, time

HERE = os.path.dirname(__file__)
STEPS = [
    ("refresh", ["refresh.py", "--funding", "--depth"]),
    ("prices", ["refresh.py", "--prices", "--recent"]),
    ("shadow", ["shadow.py"]),
    ("anchor", ["anchor.py"]),
    ("export", ["export_web.py"]),
]


def main():
    failed = []
    for name, args in STEPS:
        t = time.time()
        p = subprocess.run([sys.executable, os.path.join(HERE, args[0]), *args[1:]])
        print(f"[cycle] {name}: {'ok' if p.returncode == 0 else 'FAILED'} ({time.time() - t:.0f}s)", flush=True)
        if p.returncode:
            failed.append(name)
            if name in ("refresh", "shadow"):
                break  # never price or grade against a half-refreshed state
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
