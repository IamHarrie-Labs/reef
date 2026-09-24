"""Export a compact evidence grid for the web demo - every number the
artifact's query box and index table are allowed to show, precomputed by
the real (Python) pipeline so the browser never re-derives anything.
"""
import json, os, sys, datetime as dt, math
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity, mirage_index, intervals, ledger, score

prices, funding, books = model.load_prices(), model.load_funding(), model.load_books()
CL = json.load(open(os.path.join(model.DATA, "clusters.json")))
pairs = [(sy[i], sy[j]) for c, sy in CL.items() if c != "CONTROL"
         for i in range(len(sy)) for j in range(i + 1, len(sy))]

idx = mirage_index.build()
score_by_pair = {r["pair"]: r for r in idx["rows"] if r["status"] == "priced"}

out_pairs = []
for a, b in pairs:
    r = capacity.analyse_pair(prices, funding, books, a, b)
    if not r:
        continue
    name = r["pair"]
    grid = {}
    for size in capacity.SIZES:
        row = {}
        for hold in capacity.HOLDS:
            ra = capacity.risk_adjusted(r, size, hold)
            ci = intervals.sharpe_interval(r, ra, funding, hold) if ra else None
            stresses = None if not ra else {
                "half_funding": round(ra["gross_bp"] * 0.5 - ra["cost_bp"], 1),
                "funding_reversal": round(-ra["gross_bp"] - ra["cost_bp"], 1),
                "cost_plus_50": round(ra["gross_bp"] - ra["cost_bp"] * 1.5, 1),
                "risk_plus_50_sharpe": round(ra["net_bp"] / (ra["risk_bp"] * 1.5) * math.sqrt(365 / hold), 3) if ra["risk_bp"] > 0 else None,
            }
            row[str(hold)] = None if not ra else {
                "annual_pct": round(ra["annual_pct"], 2), "net_bp": round(ra["net_bp"], 1),
                "gross_bp": round(ra["gross_bp"], 1),
                "cost_bp": round(ra["cost_bp"], 1), "risk_bp": round(ra["risk_bp"], 0),
                "breakeven_days": round(ra["breakeven_days"], 1) if math.isfinite(ra["breakeven_days"]) else None,
                "sharpe": round(ra["sharpe"], 3),
                # interval and verdict computed here, never in the browser (D-08)
                "ci_lo": round(ci["lo"], 3) if ci else None,
                "ci_hi": round(ci["hi"], 3) if ci else None,
                "verdict": intervals.verdict_for(ra["sharpe"], ci),
                "stress": stresses,
            }
        grid[str(size)] = row
    sc = score_by_pair.get(name)
    out_pairs.append({
        "pair": name, "a": a, "b": b, "beta": r["beta"],
        "price_train_end": r["split"],
        "source_timestamps": {"prices": {x:max(prices[x]) for x in (a,b)},
                              "funding": {x:max(funding[x]) for x in (a,b)},
                              "books": {x:books[x].get("timestamp") for x in (a,b)}},
        "edge": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r["edge"].items()},
        "resid_vol_bp_per_hr": round(r["resid_vol_hr"], 2),
        "n_fit": r["n_fit"], "n_resid": r["n_resid"],
        "mirage_score": sc["mirage_score"] if sc else None,
        "verdict": sc["verdict"] if sc else None,
        "ci_lo": sc.get("ci_lo") if sc else None,
        "ci_hi": sc.get("ci_hi") if sc else None,
        "n_eff": sc.get("n_eff") if sc else None,
        "history_days": sc.get("history_days") if sc else None,
        "funding_interval_h": sc.get("funding_interval_h") if sc else None,
        "max_viable_by_hold": {str(h): capacity.max_viable(r, h) for h in capacity.HOLDS},
        "grid": grid,
    })

out_pairs.sort(key=lambda p: -(p["mirage_score"] or -1))

ledger_rows = [r for r in ledger.read_all() if r.get("evidence", {}).get("model_version") == "2.0"]
funding_archive = model.load_funding("archive")
verification_rows = []
latest_by_pair = {}
for row in ledger_rows:
    key = row.get("evidence", {}).get("pair")
    if key in latest_by_pair:
        del latest_by_pair[key]
    latest_by_pair[key] = row
for row in list(latest_by_pair.values())[-12:]:
    graded = score.grade_row(row, funding=funding_archive)
    ev = row.get("evidence", {})
    verification_rows.append({
        "recorded_ts": row.get("ts"), "question": row.get("question"),
        "pair": ev.get("pair"), "hold_days": ev.get("hold_days"),
        "predicted_net_bp": ev.get("risk_adjusted", {}).get("net_bp"),
        "status": graded.get("status"), "matures_ms": graded.get("matures_ms"),
        "actual_net_bp": graded.get("net_bp"),
    })

payload = {
    "model_version": "2.0",
    "return_basis": "B-leg reference notional, not collateral ROI",
    "estimate_type": "historical funding holdout plus snapshot costs; not realised Sharpe",
    "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%MZ"),
    "sizes": capacity.SIZES, "holds": capacity.HOLDS,
    "n_pairs_priced": len(out_pairs),
    "n_pairs_no_funding": len(pairs) - len(out_pairs),
    "verification_ledger": verification_rows,
    "pairs": out_pairs,
}
outpath = os.path.join(model.DATA, "web_export.json")
json.dump(payload, open(outpath, "w"), indent=None, separators=(",", ":"))
print(f"wrote {outpath}  ({os.path.getsize(outpath):,} bytes, {len(out_pairs)} pairs)")

from pathlib import Path
Path("web/web_export.json").write_text(json.dumps(payload), encoding="utf-8")
