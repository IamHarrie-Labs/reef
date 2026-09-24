"""Compare Bitget's gold-linked perps against an on-chain price, not another CEX.

    python src/onchain_gold.py

XAU (a Bitget-native gold contract), XAUT (Tether Gold, an ERC-20) and PAXG
(Pax Gold, an ERC-20) all claim to track one ounce of gold. This checks that
claim against the two things actually on a chain: PAXG has its own Chainlink
price feed, backed by the token's own attested reserves; gold generally has a
separate Chainlink XAU/USD feed sourced from bullion markets, independent of
any exchange. XAUT has no token-specific feed on mainnet, so it is compared
against the same XAU/USD reference as XAU.

The call is a raw eth_call to each feed's latestRoundData() - no ABI library,
no API key, no wallet. Any Ethereum JSON-RPC endpoint can serve it, and the
proxy addresses are Chainlink's own published mainnet directory, not typed
from memory (see FEEDS below and its source comment).

This is a sanity check, not a trading signal: an ounce of gold quoted on an
Ethereum oracle and a gold perpetual on Bitget clear through unrelated books,
funding models and hours. A basis is expected. What matters is whether it
stays small and stable, or drifts - the second would mean one of the three
Bitget "gold" contracts has decoupled from gold itself.
"""
import argparse, datetime as dt, json, os, sys, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(__file__))
import model, refresh

# Chainlink's mainnet feed directory: https://reference-data-directory.vercel.app/feeds-mainnet.json
# (also published at docs.chain.link/data-feeds/price-feeds/addresses). Not hand-typed.
FEEDS = {
    "XAU/USD": "0x214eD9Da11D2fbe465a6fc601a91E62EbEc1a0D6",
    "PAXG/USD": "0x9944D86CEB9160aF5C5feB251FD671923323f8C3",
}
# XAUT has no Chainlink feed of its own on mainnet; it is checked against XAU/USD too.
BITGET_TO_FEED = {"XAUUSDT": "XAU/USD", "XAUTUSDT": "XAU/USD", "PAXGUSDT": "PAXG/USD"}

RPCS = [
    "https://ethereum-rpc.publicnode.com",
    "https://rpc.ankr.com/eth",
    "https://1rpc.io/eth",
]
LATEST_ROUND_DATA = "0xfeaf968c"
DECIMALS = "0x313ce567"
STALE_AFTER_S = 6 * 3600  # Chainlink's own gold-feed heartbeat is ~1h; 6h is a generous staleness bar
OUT = os.path.join(model.DATA, "onchain", "gold_basis.json")


def _rpc_call(url, to, data):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": to, "data": data}, "latest"]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json",
                                                           "User-Agent": "reef-onchain-gold/1"})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.load(r)
    if "error" in d:
        raise RuntimeError(d["error"])
    return d["result"]


def eth_call(to, data):
    last = None
    for rpc in RPCS:
        try:
            return _rpc_call(rpc, to, data)
        except Exception as e:
            last = e
    raise RuntimeError(f"every RPC failed: {last}")


def read_feed(addr):
    decimals = int(eth_call(addr, DECIMALS), 16)
    raw = eth_call(addr, LATEST_ROUND_DATA)
    words = [raw[2 + 64 * i: 2 + 64 * (i + 1)] for i in range(5)]
    answer = int(words[1], 16)
    if answer >= 2 ** 255:
        answer -= 2 ** 256
    updated_at = int(words[3], 16)
    return {"price": answer / 10 ** decimals, "decimals": decimals, "updated_at_ms": updated_at * 1000}


def bitget_live_ticker(symbol):
    """Live mark price, same moment as the oracle read. None if unreachable -
    the cached hourly close (bitget_last_close) is the fallback, not a retry
    that could block the desk cycle on a slow endpoint."""
    row = refresh._get(f"{refresh.BASE}/ticker?symbol={symbol}&productType={refresh.PT}")
    if not row:
        return None
    row = row[0] if isinstance(row, list) else row
    price = row.get("markPrice") or row.get("lastPr")
    ts = row.get("ts")
    if not price or not ts:
        return None
    return {"price": float(price), "ts_ms": int(ts), "source": "live_ticker"}


def bitget_last_close(symbol):
    """Most recent cached hourly candle close - up to ~1h behind the oracle read."""
    prices = model.load_prices().get(symbol, {})
    if not prices:
        return None
    t = max(prices)
    return {"price": prices[t], "ts_ms": t, "source": "hourly_candle"}


def bitget_reference(symbol):
    return bitget_live_ticker(symbol) or bitget_last_close(symbol)


def build_payload(now_ms=None):
    now_ms = now_ms if now_ms is not None else int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
    feeds, feed_errors = {}, {}
    for name, addr in FEEDS.items():
        try:
            feeds[name] = read_feed(addr)
        except Exception as e:
            feed_errors[name] = str(e)

    rows = []
    for symbol, feed_name in BITGET_TO_FEED.items():
        feed = feeds.get(feed_name)
        bg = bitget_reference(symbol)
        if not feed or not bg:
            rows.append({"symbol": symbol, "reference_feed": feed_name, "status": "unavailable",
                        "error": feed_errors.get(feed_name, "no cached Bitget price")})
            continue
        stale = (now_ms - feed["updated_at_ms"]) / 1000 > STALE_AFTER_S
        basis_bp = (bg["price"] - feed["price"]) / feed["price"] * 1e4
        rows.append({
            "symbol": symbol, "reference_feed": feed_name, "status": "stale" if stale else "ok",
            "bitget_price": bg["price"], "bitget_ts_ms": bg["ts_ms"], "bitget_source": bg["source"],
            "onchain_price": feed["price"], "onchain_updated_ms": feed["updated_at_ms"],
            "onchain_age_s": round((now_ms - feed["updated_at_ms"]) / 1000),
            "basis_bp": round(basis_bp, 1),
        })

    return {"generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%MZ"),
            "source": "Chainlink price feeds on Ethereum mainnet, read directly via eth_call",
            "rows": rows}


def run():
    payload = build_payload()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.parse_args()
    payload = run()
    print(f"On-chain gold check ({payload['generated_utc']})\n")
    print(f"{'SYMBOL':10s} {'REF FEED':10s} {'BITGET':>10s} {'ON-CHAIN':>10s} {'BASIS':>9s} {'ORACLE AGE':>11s}  STATUS")
    print("-" * 76)
    for r in payload["rows"]:
        if r["status"] == "unavailable":
            print(f"{r['symbol']:10s} {r['reference_feed']:10s} {'--':>10s} {'--':>10s} {'--':>9s} {'--':>11s}  {r['error']}")
            continue
        print(f"{r['symbol']:10s} {r['reference_feed']:10s} {r['bitget_price']:10.2f} {r['onchain_price']:10.2f} "
              f"{r['basis_bp']:+8.1f}bp {r['onchain_age_s']:>10}s  {r['status']}")
    if os.environ.get("REEF_ONCHAIN_REQUIRED") and any(r["status"] == "unavailable" for r in payload["rows"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
