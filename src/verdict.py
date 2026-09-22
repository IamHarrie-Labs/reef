"""The demo: ask a question in plain English, get a priced, evidence-backed
verdict, logged so it can be graded later against what actually happened.

    python src/verdict.py "Is the SMH/SOXL yield real for $25k over 30 days?"

Pipeline: llm.parse_query -> capacity.analyse_pair (deterministic) ->
ledger.append (before synthesis, so the logged prediction can't be tuned
after the fact) -> llm.synthesize.
"""
import json, os, sys, time, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
import model, capacity, llm, ledger, intervals


def resolve_pair(a_hint, b_hint, clusters):
    """If the user named one ticker, find its cluster-mate automatically."""
    if a_hint and b_hint:
        for c, syms in clusters.items():
            if c != "CONTROL" and a_hint != b_hint and a_hint in syms and b_hint in syms:
                ordered = [x for x in syms if x in (a_hint,b_hint)]
                return ordered[0], ordered[1]
        return None, None
    if not a_hint:
        return None, None
    for c, syms in clusters.items():
        if c == "CONTROL" or a_hint not in syms:
            continue
        others = [s for s in syms if s != a_hint]
        if others:
            return a_hint, others[0]
    return a_hint, None


def answer(question):
    q = llm.parse_query(question)
    with open(os.path.join(model.DATA, "clusters.json"), encoding="utf-8") as handle:
        CL = json.load(handle)
    a, b = resolve_pair(q["a"], q["b"], CL)

    if not a or not b:
        ev = {"error": f"Could not resolve a tradeable pair from: {question!r} "
                        f"(parsed a={q['a']}, b={q['b']})", "parsed_by": q["parsed_by"]}
        ledger.append({"ts": int(time.time() * 1000), "question": question, "query": q,
                        "evidence": ev, "verdict_text": None})
        return ev, llm.synthesize(ev)

    prices, funding, books = model.load_prices(), model.load_funding(), model.load_books()
    r = capacity.analyse_pair(prices, funding, books, a, b)
    if not r:
        ev = {"error": f"No funding history for {a}/{b}", "pair": f"{a}/{b}"}
        ledger.append({"ts": int(time.time() * 1000), "question": question, "query": q,
                        "evidence": ev, "verdict_text": None})
        return ev, llm.synthesize(ev)

    size, hold = q["size"], q["hold_days"]
    ra = capacity.risk_adjusted(r, size, hold)
    if not ra:
        ev = {"error": f"Book too thin to price {a}/{b} at ${size:,.0f}", "pair": r["pair"]}
        ledger.append({"ts": int(time.time() * 1000), "question": question, "query": q,
                        "evidence": ev, "verdict_text": None})
        return ev, llm.synthesize(ev)

    evidence = {
        "model_version": "2.0", "return_basis": r["return_basis"],
        "verdict": intervals.verdict_for(ra["sharpe"], intervals.sharpe_interval(r, ra, funding, hold)),
        "ci": intervals.sharpe_interval(r, ra, funding, hold),
        "price_train_end": r["split"],
        "pair": r["pair"], "beta": r["beta"], "size": size, "hold_days": hold,
        "edge": r["edge"], "residual_vol_bp_per_hr": round(r["resid_vol_hr"], 2),
        "risk_adjusted": ra,
        "breakeven_days": model.net_carry(r["edge"], ra["cost_bp"], hold)["breakeven_days"],
        "n_funding_intervals": r["edge"]["n_intervals"], "n_price_bars_fit": r["n_fit"],
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_timestamps": {"prices": {x: max(prices[x]) for x in (a,b)},
                              "funding": {x: max(funding[x]) for x in (a,b)},
                              "books": {x: books[x].get("timestamp") for x in (a,b)}},
        "parsed_by": q["parsed_by"],
    }
    ledger_row = {"ts": int(time.time() * 1000), "question": question, "query": q,
                  "evidence": evidence}
    ledger.append(ledger_row)
    text = llm.synthesize(evidence)
    return evidence, text


def main():
    question = " ".join(sys.argv[1:]) or "Is the SMH/SOXL yield real for $25k over 30 days?"
    print(f"Q: {question}\n")
    ev, text = answer(question)
    print("--- evidence (every number the answer below is allowed to use) ---")
    print(json.dumps(ev, indent=2, default=str))
    print(f"\n--- verdict (LLM: {'live, ' + llm.QWEN_MODEL if llm.available() else 'template fallback'}) ---")
    print(text)


if __name__ == "__main__":
    main()
