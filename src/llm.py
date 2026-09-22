"""LLM synthesis layer - the one non-deterministic piece in this project.

Everything upstream (model.py, capacity.py) is arithmetic: OLS beta, book-walk
VWAP, funding differentials. The LLM's job starts only after that arithmetic
is done. It does two things, both explicitly scoped to reduce the chance of introducing a
number that isn't already in the evidence dict:

  1. Parse a free-text question into a structured request (pair, size, hold).
  2. Render the priced verdict as an explanation, citing only fields already
     present in the evidence - it is told, in the prompt, never to state a
     number it was not given.

Reads BITGET_QWEN_API_KEY (or ANTHROPIC_API_KEY as a fallback) from the
environment or a local .env file (gitignored, never printed). With no key
configured, both functions fall back to a deterministic template so the
pipeline still runs end to end without one.
"""
import json, os, re, urllib.request

QWEN_BASE = os.environ.get("BITGET_QWEN_BASE_URL", "https://hackathon.bitgetops.com/v1")
QWEN_MODEL = os.environ.get("BITGET_QWEN_MODEL", "qwen3.8-max")
QWEN_TIMEOUT = int(os.environ.get("BITGET_QWEN_TIMEOUT", "75"))


def _load_dotenv():
    path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()


def _key():
    return os.environ.get("BITGET_QWEN_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")


def available():
    return bool(_key())


def _chat(system, user, max_tokens=600):
    """Minimal OpenAI-compatible chat call over stdlib urllib. No SDK dependency."""
    key = _key()
    body = json.dumps({
        "model": QWEN_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"{QWEN_BASE}/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=QWEN_TIMEOUT) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"]


# ---------------------------------------------------------------- parsing --

_KNOWN = None


def _known_symbols():
    global _KNOWN
    if _KNOWN is None:
        with open(os.path.join(os.path.dirname(__file__), "..", "data", "clusters.json"), encoding="utf-8") as handle:
            cl = json.load(handle)
        _KNOWN = sorted({s[:-4] for c, sy in cl.items() if c != "CONTROL" for s in sy})
    return _KNOWN


def parse_query(text):
    """Free text -> {a, b, size, hold_days}. Rule-based fallback always runs;
    the LLM path is used only to resolve ambiguous or colloquial phrasing."""
    if available():
        try:
            return _parse_query_llm(text)
        except Exception:
            pass
    return _parse_query_rules(text)


def _parse_query_rules(text):
    u = text.upper()
    tickers = [t for t in _known_symbols() if re.search(rf"\b{re.escape(t)}\b", u)]
    # A size must be $-prefixed, or a bare number with a k/m suffix that isn't
    # part of a ticker (NDX100, SP500, ...): require no letter immediately
    # before the digits in that second case, and require the suffix in both
    # cases so "100" inside "NDX100" is never mistaken for a dollar amount.
    # A size must be $-prefixed, a bare number with a k/m suffix, or a bare
    # number of 4+ digits (a plausible dollar figure) - and never preceded by
    # a letter, so "100" inside "NDX100" or a 1-3 digit day-count is never
    # mistaken for a dollar amount.
    size_m = re.search(r"\$\s?([\d,]+(?:\.\d+)?)\s*([kKmM])?|"
                        r"(?<![A-Za-z])([\d,]+(?:\.\d+)?)\s*([kKmM])\b|"
                        r"(?<![A-Za-z])(\d{4,})(?![A-Za-z\d])", text)
    size = 25_000
    if size_m:
        if size_m.group(1) is not None:
            val, suf = size_m.group(1), size_m.group(2)
        elif size_m.group(3) is not None:
            val, suf = size_m.group(3), size_m.group(4)
        else:
            val, suf = size_m.group(5), None
        mult = {"k": 1e3, "K": 1e3, "m": 1e6, "M": 1e6}.get(suf, 1)
        size = float(val.replace(",", "")) * mult
    hold_m = re.search(r"(\d+)[\s-]*(day|d\b|week|wk|month)", text, re.I)
    if hold_m:
        n, unit = int(hold_m.group(1)), hold_m.group(2).lower()
    else:
        # "a week", "an hour" etc. carry no digit - treat the article as 1.
        hold_m = re.search(r"\ban?\s+(day|week|wk|month)\b", text, re.I)
        n, unit = (1, hold_m.group(1).lower()) if hold_m else (None, None)
    hold_days = 30
    if unit:
        hold_days = n * (7 if "wk" in unit or "week" in unit else 30 if "month" in unit else 1)
    return {"a": tickers[0] + "USDT" if len(tickers) > 0 else None,
            "b": tickers[1] + "USDT" if len(tickers) > 1 else None,
            "size": size, "hold_days": hold_days, "raw": text, "parsed_by": "rules"}


def _parse_query_llm(text):
    syms = ", ".join(_known_symbols())
    sys_p = (f"Extract a trading query into strict JSON: "
             f'{{"a": "<TICKER>", "b": "<TICKER or null>", "size": <number>, "hold_days": <number>}}. '
             f"Tickers must come only from this list: {syms}. "
             f"If the user names one ticker, set b to null. Default size 25000, default hold_days 30 "
             f"if not stated. Reply with JSON only, no prose.")
    out = _chat(sys_p, text, max_tokens=150)
    d = json.loads(re.search(r"\{.*\}", out, re.S).group())
    a = d.get("a"); b = d.get("b")
    if a not in _known_symbols() or (b is not None and b not in _known_symbols()):
        raise ValueError("Unsupported instrument")
    import math
    if any(not math.isfinite(float(d.get(k) or default)) or float(d.get(k) or default) <= 0 for k, default in (("size",25000),("hold_days",30))):
        raise ValueError("Invalid size or holding period")
    return {"a": (a + "USDT") if a else None, "b": (b + "USDT") if b else None,
            "size": float(d.get("size") or 25_000), "hold_days": float(d.get("hold_days") or 30),
            "raw": text, "parsed_by": "llm"}


# -------------------------------------------------------------- synthesis --

def synthesize(evidence):
    """evidence -> natural-language verdict. Checks numeric tokens against evidence; the
    system prompt restricts the model to fields present in `evidence`."""
    if available():
        try:
            return _synthesize_llm(evidence)
        except Exception as e:
            return _synthesize_template(evidence) + f"\n\n[LLM synthesis failed, showed template: {e}]"
    return _synthesize_template(evidence)


def _synthesize_llm(evidence):
    sys_p = ("You explain a priced pair-trade verdict to a retail trader. "
             "You are given a JSON evidence object that is the ONLY source of numbers you may state. "
             "Do not compute, round differently, or introduce any figure not present in the JSON. "
             "If a field is null, say it is unavailable rather than guessing. "
             "Write 4-6 sentences: what the gross yield looked like, what happened once cost and risk "
             "were priced in, and the one-line verdict. Plain language, no hedging filler.")
    text = _chat(sys_p, json.dumps(evidence, indent=2), max_tokens=400)
    # Model prose is supplementary; reject new numerical tokens and conflicting labels.
    allowed = set(re.findall(r"-?\d+(?:\.\d+)?", json.dumps(evidence)))
    stated = set(re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", "")))
    if not stated <= allowed or any(v in text.upper() and v != evidence.get("verdict") for v in ("SUPPORTED", "UNPROVEN", "UNFAVOURABLE")):
        raise ValueError("Explanation did not pass evidence validation")
    return _synthesize_template(evidence) + "\n\nAI commentary (not a validated financial claim):\n" + text


def _synthesize_template(e):
    if e.get("error"):
        return f"Could not price this pair: {e['error']}"
    edge, ra = e["edge"], e["risk_adjusted"]
    lines = [
        f"{e['pair']} shows {edge['annual_pct']:.1f}% gross annualised funding edge "
        f"({edge['consistency_pct']:.0f}% same-sign over {edge['n_intervals']} complete days), "
        f"direction: {edge['direction']}.",
        f"At ${e['size']:,.0f} held {e['hold_days']:.0f} days: round-trip cost {ra['cost_bp']:.1f}bp, "
        f"residual-spread risk {ra['risk_bp']:.0f}bp, net {ra['net_bp']:.1f}bp "
        f"({ra['annual_pct']:.1f}% net annualised), Sharpe {ra['sharpe']:.2f}.",
        f"Breakeven holding period: {e['breakeven_days']:.1f} days.",
    ]
    lines.append(f"Verdict: {e['verdict']} under the stated assumptions.")
    lines.append("Historical estimate per B-leg reference notional; not realised performance or collateral ROI.")
    return "\n".join(lines) + (
        "\n\n[template renderer - no LLM key configured; set BITGET_QWEN_API_KEY or ANTHROPIC_API_KEY]"
        if not available() else "")
