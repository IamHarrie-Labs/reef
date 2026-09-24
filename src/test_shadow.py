"""Offline end-to-end test of the shadow desk: open -> exit -> marks -> graded.

Uses cached books and the funding archive, with the mark-price endpoint and
the ledger stubbed, so it needs no network and writes nothing to data/.
"""
import os, sys, unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(__file__))
import model, shadow, score, anchor

DAY = 86_400_000


def fake_get(url):
    t = int(url.split("startTime=")[1].split("&")[0])
    return [[str(t), "100.0", "100.0", "100.0", "100.0"]]


class ShadowLoop(unittest.TestCase):
    def setUp(self):
        self.prices, self.books = model.load_prices(), model.load_books()
        self.window, self.archive = model.load_funding(), model.load_funding("archive")
        self.t0 = min(max(v) for k, v in self.archive.items() if k in self.books) - 2 * DAY + 1

    def test_open_close_grade(self):
        rows, positions, executions, marks = [], [], {}, {}
        with patch.object(shadow.ledger, "append", side_effect=rows.append):
            opened = shadow.open_batch(1, self.t0, self.prices, self.window, self.books, positions)
        self.assertGreater(opened, 10)
        self.assertEqual(len(rows), opened)
        closed, missed = shadow.close_due(self.t0 + DAY + 60_000, self.books, self.archive,
                                          positions, executions, marks)
        self.assertEqual((closed, missed), (opened, 0))
        with patch.object(shadow.refresh, "_get", side_effect=fake_get):
            self.assertGreater(shadow.backfill_marks(executions, self.archive, marks), 0)
        results = [score.grade_row(r, funding=self.archive, executions=executions,
                                   now_ms=self.t0 + 2 * DAY) for r in rows]
        graded = [g for g in results if g["status"] == "graded"]
        self.assertGreater(len(graded), len(rows) // 2, [g["status"] for g in results])
        for g in graded:
            self.assertIn("realised_cost_bp", g)
            self.assertGreater(g["realised_cost_bp"], 0)
        self.assertEqual(score.summarise(graded)["n_graded"], len(graded))

    def test_exit_after_grace_is_not_graded(self):
        rows, positions, executions = [], [], {}
        with patch.object(shadow.ledger, "append", side_effect=rows.append):
            shadow.open_batch(1, self.t0, self.prices, self.window, self.books, positions)
        shadow.close_due(self.t0 + DAY + score.EXIT_GRACE_MS + 1, self.books, self.archive,
                         positions, executions, {})
        self.assertTrue(all(e["status"] == "missed_exit_window" for e in executions.values()))
        g = score.grade_row(rows[0], funding=self.archive, executions=executions, now_ms=self.t0 + 2 * DAY)
        self.assertEqual(g["status"], "insufficient_execution_or_funding_data")

    def test_fill_price_walks_the_book(self):
        book = {"asks": [(100.0, 1.0), (101.0, 1.0)], "bids": [(99.0, 1.0)]}
        self.assertAlmostEqual(shadow.vwap(book["asks"], notional=150.0), 150.0 / (1 + 50 / 101))
        self.assertAlmostEqual(shadow.vwap(book["asks"], qty=2.0), 100.5)
        self.assertIsNone(shadow.vwap(book["bids"], qty=2.0))


class Anchoring(unittest.TestCase):
    def test_merkle_proof_round_trip(self):
        import hashlib
        leaves = [anchor.leaf({"i": i}) for i in range(7)]
        root, levels = anchor.merkle(leaves)
        for i, h in enumerate(leaves):
            node = h
            for step in anchor.proof(levels, i):
                pair = (step["hash"] + node) if step["side"] == "left" else (node + step["hash"])
                node = hashlib.sha256(bytes.fromhex(pair)).hexdigest()
            self.assertEqual(node, root)

    def test_leaf_changes_when_row_changes(self):
        self.assertNotEqual(anchor.leaf({"net_bp": 1.0}), anchor.leaf({"net_bp": 1.1}))


if __name__ == "__main__":
    unittest.main()
