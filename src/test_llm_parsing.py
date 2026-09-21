"""Regression tests for llm.py's rule-based query parser.

Both cases here were real bugs, caught by testing the demo against actual
phrasing rather than by inspection — see DECISIONS.md. Run directly:

    python src/test_llm_parsing.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import llm

CASES = [
    # (question, expected_size, expected_hold_days)
    ("Can I trust the QQQ/NDX100 spread for a quick 3-day trade?", 25_000, 3),
    ("Is the SMH/SOXL yield real for $25k over 30 days?", 25_000, 30),
    ("What about XAU/XAUT at $100k for 2 weeks?", 100_000, 14),
    ("Is TSLA/TSLL worth it for a month?", 25_000, 30),
    ("SP500 vs QQQ for $5000 over a week", 5_000, 7),
    ("50000 on MSFT/MSFU for 10 days", 50_000, 10),
    ("GOOGL vs GGLL, an hour", 25_000, 30),
    ("Just checking AAPL/AAPU", 25_000, 30),
    ("NDX100 vs SP500 for a day", 25_000, 1),
]


def run():
    failures = []
    for question, exp_size, exp_hold in CASES:
        r = llm._parse_query_rules(question)
        ok_size = abs(r["size"] - exp_size) < 1
        ok_hold = abs(r["hold_days"] - exp_hold) < 1
        status = "OK  " if (ok_size and ok_hold) else "FAIL"
        print(f"{status} size={r['size']:>10,.0f} (want {exp_size:>9,}) "
              f"hold={r['hold_days']:>3} (want {exp_hold:>2})  "
              f"a={r['a']} b={r['b']}  | {question}")
        if not (ok_size and ok_hold):
            failures.append(question)
    print()
    if failures:
        print(f"{len(failures)}/{len(CASES)} FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print(f"ALL {len(CASES)} PASS")


if __name__ == "__main__":
    run()
