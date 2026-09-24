"""Offline test of the on-chain gold check: RPC responses are mocked, nothing
touches the network. Verifies decoding, basis math and the multi-RPC fallback.

Uses build_payload(), never run() - run() writes data/onchain/gold_basis.json
for real, and this test must not overwrite the live desk's actual output.
"""
import os, sys, unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(__file__))
import onchain_gold as og

XAU_ADDR = og.FEEDS["XAU/USD"]
PAXG_ADDR = og.FEEDS["PAXG/USD"]


def encode_latest_round_data(answer, updated_at, decimals_scale=8):
    def word(n):
        return f"{n & (2**256 - 1):064x}"
    round_id, started_at, answered_in_round = 1, updated_at, 1
    scaled = int(round(answer * 10 ** decimals_scale))
    return "0x" + word(round_id) + word(scaled) + word(started_at) + word(updated_at) + word(answered_in_round)


class Decoding(unittest.TestCase):
    def test_reads_price_and_freshness(self):
        now = 1_700_000_000
        with patch.object(og, "eth_call", side_effect=lambda addr, data:
                          f"0x{'0' * 63}8" if data == og.DECIMALS else encode_latest_round_data(4275.82, now)):
            feed = og.read_feed(XAU_ADDR)
        self.assertAlmostEqual(feed["price"], 4275.82, places=2)
        self.assertEqual(feed["updated_at_ms"], now * 1000)

    def test_negative_answer_decodes_signed(self):
        with patch.object(og, "eth_call", side_effect=lambda addr, data:
                          f"0x{'0' * 63}8" if data == og.DECIMALS else encode_latest_round_data(-1.5, 1)):
            feed = og.read_feed(XAU_ADDR)
        self.assertLess(feed["price"], 0)

    def test_falls_back_across_rpcs(self):
        calls = []
        def flaky(url, to, data):
            calls.append(url)
            if url == og.RPCS[0]:
                raise TimeoutError("first RPC down")
            return f"0x{'0' * 63}8" if data == og.DECIMALS else encode_latest_round_data(1.0, 1)
        with patch.object(og, "_rpc_call", side_effect=flaky):
            og.read_feed(XAU_ADDR)
        self.assertEqual(calls[0], og.RPCS[0])
        self.assertIn(og.RPCS[1], calls)

    def test_all_rpcs_down_raises(self):
        with patch.object(og, "_rpc_call", side_effect=TimeoutError("down")):
            with self.assertRaises(RuntimeError):
                og.eth_call(XAU_ADDR, og.DECIMALS)


class BitgetReference(unittest.TestCase):
    def test_prefers_live_ticker_over_cached_close(self):
        with patch.object(og, "bitget_live_ticker", return_value={"price": 1.0, "ts_ms": 1, "source": "live_ticker"}), \
             patch.object(og, "bitget_last_close", return_value={"price": 2.0, "ts_ms": 2, "source": "hourly_candle"}):
            self.assertEqual(og.bitget_reference("XAUUSDT")["source"], "live_ticker")

    def test_falls_back_to_cached_close_when_ticker_unreachable(self):
        with patch.object(og, "bitget_live_ticker", return_value=None), \
             patch.object(og, "bitget_last_close", return_value={"price": 2.0, "ts_ms": 2, "source": "hourly_candle"}):
            ref = og.bitget_reference("XAUUSDT")
        self.assertEqual(ref["source"], "hourly_candle")

    def test_live_ticker_decodes_mark_price(self):
        with patch.object(og.refresh, "_get", return_value=[{"markPrice": "4257.85", "ts": "1700000000000"}]):
            t = og.bitget_live_ticker("XAUUSDT")
        self.assertEqual(t["price"], 4257.85)
        self.assertEqual(t["ts_ms"], 1700000000000)

    def test_live_ticker_none_when_fields_missing(self):
        with patch.object(og.refresh, "_get", return_value=[{"markPrice": None, "ts": None}]):
            self.assertIsNone(og.bitget_live_ticker("XAUUSDT"))
        with patch.object(og.refresh, "_get", return_value=None):
            self.assertIsNone(og.bitget_live_ticker("XAUUSDT"))


class BasisMath(unittest.TestCase):
    def setUp(self):
        self.now = 1_700_000_000_000

    def fake_feeds(self, xau=4275.82, paxg=4270.35, xau_age_s=100, paxg_age_s=100):
        return {
            "XAU/USD": {"price": xau, "decimals": 8, "updated_at_ms": self.now - xau_age_s * 1000},
            "PAXG/USD": {"price": paxg, "decimals": 8, "updated_at_ms": self.now - paxg_age_s * 1000},
        }

    def test_basis_matches_hand_calc(self):
        with patch.object(og, "read_feed", side_effect=lambda addr: self.fake_feeds()[
                          "XAU/USD" if addr == XAU_ADDR else "PAXG/USD"]), \
             patch.object(og, "bitget_reference", return_value={"price": 4257.85, "ts_ms": self.now, "source": "hourly_candle"}):
            payload = og.build_payload(now_ms=self.now)
        row = next(r for r in payload["rows"] if r["symbol"] == "XAUUSDT")
        expected_bp = (4257.85 - 4275.82) / 4275.82 * 1e4
        self.assertAlmostEqual(row["basis_bp"], round(expected_bp, 1), places=1)
        self.assertEqual(row["status"], "ok")

    def test_stale_feed_is_flagged_not_hidden(self):
        with patch.object(og, "read_feed", side_effect=lambda addr: self.fake_feeds(
                          xau_age_s=og.STALE_AFTER_S + 60)["XAU/USD" if addr == XAU_ADDR else "PAXG/USD"]), \
             patch.object(og, "bitget_reference", return_value={"price": 4257.85, "ts_ms": self.now, "source": "hourly_candle"}):
            payload = og.build_payload(now_ms=self.now)
        row = next(r for r in payload["rows"] if r["symbol"] == "XAUUSDT")
        self.assertEqual(row["status"], "stale")
        self.assertIn("basis_bp", row)  # still reported, just labelled - never hidden

    def test_missing_bitget_price_reports_unavailable_not_zero(self):
        with patch.object(og, "read_feed", side_effect=lambda addr: self.fake_feeds()[
                          "XAU/USD" if addr == XAU_ADDR else "PAXG/USD"]), \
             patch.object(og, "bitget_reference", return_value=None):
            payload = og.build_payload(now_ms=self.now)
        self.assertTrue(all(r["status"] == "unavailable" for r in payload["rows"]))
        self.assertFalse(any("basis_bp" in r for r in payload["rows"]))

    def test_xaut_checked_against_xau_not_its_own_feed(self):
        self.assertEqual(og.BITGET_TO_FEED["XAUTUSDT"], "XAU/USD")
        self.assertNotIn("XAUT/USD", og.FEEDS)

    def test_run_writes_file_and_matches_build_payload(self):
        import tempfile, json
        with patch.object(og, "read_feed", side_effect=lambda addr: self.fake_feeds()[
                          "XAU/USD" if addr == XAU_ADDR else "PAXG/USD"]), \
             patch.object(og, "bitget_reference", return_value={"price": 4257.85, "ts_ms": self.now, "source": "hourly_candle"}):
            with tempfile.TemporaryDirectory() as td:
                out = os.path.join(td, "sub", "gold_basis.json")
                with patch.object(og, "OUT", out):
                    written = og.run()
                self.assertTrue(os.path.exists(out))
                with open(out, encoding="utf-8") as f:
                    on_disk = json.load(f)
                self.assertEqual(on_disk["rows"], written["rows"])


if __name__ == "__main__":
    unittest.main()
