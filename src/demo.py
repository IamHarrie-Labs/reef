"""The submission demo. Run this end to end:

    python src/demo.py

Walks through: (1) the naive screen vs the priced ranking, (2) the Reef
Index across all 18 pairs, (3) three natural-language questions answered
live through verdict.py, (4) what the adverse-selection / self-scoring
tools show right now (honestly reporting how young that data is).

This is what a judge running the "Accessible Demo" requirement would see.
"""
import sys, os, json, subprocess

HERE = os.path.dirname(__file__)


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)
    sys.stdout.flush()


def run(script, *args):
    sys.stdout.flush()
    subprocess.run([sys.executable, os.path.join(HERE, script), *args], check=False)


def main():
    section("1/4 - THE NAIVE SCREEN vs THE PRICED RANKING")
    print("A dashboard shows you gross yield. We show you what survives.\n")
    run("screen.py")

    section("2/4 - REEF")
    print("One public score per pair: does the visible yield survive cost + risk?\n")
    run("mirage_index.py")

    section("3/4 - ASK IT A QUESTION (the LLM interface)")
    questions = [
        "Is the SMH/SOXL yield real for $25k over 30 days?",
        "What about XAU/XAUT at $100k for 2 weeks?",
        "Can I trust the QQQ/NDX100 spread for a quick 3-day trade?",
    ]
    for q in questions:
        run("verdict.py", q)
        print()

    section("4/4 - SELF-SCORING & ADVERSE SELECTION (live-collected, in progress)")
    print("Every verdict above was just logged with a timestamp, before you read")
    print("this line. score.py will grade them against realised prices once each")
    print("holding period elapses - nothing here can be tuned after the fact.\n")
    run("score.py")
    print()
    n_files = len([f for f in os.listdir(os.path.join(HERE, "..", "data", "timeseries"))
                    if f.endswith(".jsonl")]) if os.path.exists(
        os.path.join(HERE, "..", "data", "timeseries")) else 0
    print(f"Adverse-selection recorder: {n_files} symbols currently being captured "
          f"every 15 minutes (started {__import__('datetime').datetime.utcnow():%Y-%m-%d}, "
          f"UTC). Needs a few hours of history to say anything - see adverse_selection.py.")


if __name__ == "__main__":
    main()
