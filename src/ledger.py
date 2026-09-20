"""Append-only log of every verdict this tool has ever given.

The point: a research tool that grades its own predictions is rare, and the
grading only means something if the prediction was written down BEFORE the
outcome was known. `verdict.py` appends here before calling the LLM for
synthesis, so the logged evidence can't be adjusted after the fact.

`score.py` reads this file later and checks each verdict's implied forecast
(net_bp, sharpe direction) against what prices actually did afterward.
"""
import json, os

PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ledger.jsonl")


def append(row):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


def read_all():
    if not os.path.exists(PATH):
        return []
    return [json.loads(l) for l in open(PATH, encoding="utf-8") if l.strip()]
