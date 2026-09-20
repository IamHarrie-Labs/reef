"""Grade every verdict this tool has ever given against what prices did next.

Each ledger row is a prediction written down BEFORE the outcome, with a
timestamp and the evidence it was based on. This reads price history for
the period after each verdict and checks whether net carry over the stated
hold_days actually came in positive when the verdict said REAL (or negative
when it said MIRAGE).

Needs price history to extend past a verdict's timestamp by hold_days. Early
in the project's life most verdicts won't have matured yet - that's reported
honestly as "pending", not skipped silently.
"""
import json, os, sys, math, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import model, ledger


def actual_net_bp(prices, a, b, beta, t0, hold_days):
    """Realised beta-hedged return from t0 to t0+hold_days, in bp, using
    whatever cached price history covers that window."""
    t1 = t0 + int(hold_days * 86_400_000)
    ka = sorted(k for k in prices.get(a, {}) if t0 <= k <= t1)
    kb = sorted(k for k in prices.get(b, {}) if t0 <= k <= t1)
    if len(ka) < 2 or len(kb) < 2:
        return None, "insufficient_price_history_for_window"
    ra = math.log(prices[a][ka[-1]] / prices[a][ka[0]])
    rb = math.log(prices[b][kb[-1]] / prices[b][kb[0]])
    return (rb - beta * ra) * 1e4, None


def grade_row(row, prices):
    ev = row.get("evidence", {})
    if "pair" not in ev or "error" in ev:
        return {"question": row["question"], "status": "not_priced"}
    a_name, b_name = ev["pair"].split("/")
    a, b = a_name + "USDT", b_name + "USDT"
    t0 = row["ts"]
    hold = ev["hold_days"]
    now = int(dt.datetime.utcnow().timestamp() * 1000)
    if t0 + hold * 86_400_000 > now:
        return {"question": row["question"], "pair": ev["pair"], "status": "pending",
                "matures": dt.datetime.utcfromtimestamp((t0 + hold * 86_400_000) / 1000).isoformat()}
    realised_bp, err = actual_net_bp(prices, a, b, ev["beta"], t0, hold)
    if err:
        return {"question": row["question"], "pair": ev["pair"], "status": err}
    predicted = row["evidence"]["risk_adjusted"]
    called_real = predicted["sharpe"] > 0.5
    was_real = realised_bp > 0
    return {
        "question": row["question"], "pair": ev["pair"], "status": "graded",
        "called": "REAL" if called_real else "MIRAGE",
        "predicted_net_bp": round(predicted["net_bp"], 1),
        "realised_residual_bp": round(realised_bp, 1),
        "correct": called_real == was_real,
    }


if __name__ == "__main__":
    rows = ledger.read_all()
    if not rows:
        print("No verdicts logged yet. Run src/verdict.py at least once first.")
        sys.exit(0)
    prices = model.load_prices()
    results = [grade_row(r, prices) for r in rows]
    print(f"{len(rows)} verdicts logged.\n")
    for r in results:
        print(json.dumps(r, indent=2))
    graded = [r for r in results if r["status"] == "graded"]
    if graded:
        correct = sum(1 for r in graded if r["correct"])
        print(f"\n{correct}/{len(graded)} graded verdicts correct "
              f"({100*correct/len(graded):.0f}% hit rate).")
    pending = sum(1 for r in results if r["status"] == "pending")
    if pending:
        print(f"{pending} verdict(s) still pending (holding period not yet elapsed).")
