"""Export a compact evidence grid for the web demo - every number the
artifact's query box and index table are allowed to show, precomputed by
the real (Python) pipeline so the browser never re-derives anything.
"""
import json, os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import model, capacity, mirage_index

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
            row[str(hold)] = None if not ra else {
                "annual_pct": round(ra["annual_pct"], 2), "net_bp": round(ra["net_bp"], 1),
                "cost_bp": round(ra["cost_bp"], 1), "risk_bp": round(ra["risk_bp"], 0),
                "sharpe": round(ra["sharpe"], 3),
            }
        grid[str(size)] = row
    sc = score_by_pair.get(name)
    out_pairs.append({
        "pair": name, "a": a, "b": b, "beta": round(r["beta"], 3),
        "edge": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r["edge"].items()},
        "resid_vol_bp_per_hr": round(r["resid_vol_hr"], 2),
        "n_fit": r["n_fit"], "n_resid": r["n_resid"],
        "mirage_score": sc["mirage_score"] if sc else None,
        "verdict": sc["verdict"] if sc else None,
        "grid": grid,
    })

out_pairs.sort(key=lambda p: -(p["mirage_score"] or -1))

payload = {
    "generated_utc": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%MZ"),
    "sizes": capacity.SIZES, "holds": capacity.HOLDS,
    "n_pairs_priced": len(out_pairs),
    "n_pairs_no_funding": len(pairs) - len(out_pairs),
    "pairs": out_pairs,
}
outpath = os.path.join(model.DATA, "web_export.json")
json.dump(payload, open(outpath, "w"), indent=None, separators=(",", ":"))
print(f"wrote {outpath}  ({os.path.getsize(outpath):,} bytes, {len(out_pairs)} pairs)")
