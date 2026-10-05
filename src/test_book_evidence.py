import copy
import gzip
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(__file__))
import book_evidence, model, shadow


class BookEvidenceTests(unittest.TestCase):
    def test_archive_replay_and_tampering(self):
        book = {'timestamp': 123, 'asks': [[101, 10], [102, 10]], 'bids': [[99, 10], [98, 10]]}
        with tempfile.TemporaryDirectory() as directory:
            digest = book_evidence.store(book, directory)
            self.assertEqual(digest, book_evidence.store(copy.deepcopy(book), directory))
            leg = {'qty': 15, 'entry_price': shadow.vwap(book['asks'], qty=15),
                   'exit_price': shadow.vwap(book['bids'], qty=15),
                   'entry_mid': 100, 'exit_mid': 100, 'entry_book_ts': 123, 'exit_book_ts': 123,
                   'entry_book_sha256': digest, 'exit_book_sha256': digest}
            record = {'execution': {'ABCUSDT': leg}}
            self.assertEqual(book_evidence.replay(record, directory)['book_walks_replayed'], 2)
            bad = copy.deepcopy(record);bad['execution']['ABCUSDT']['entry_price'] = 101
            with self.assertRaises(ValueError):book_evidence.replay(bad, directory)
            with open(os.path.join(directory, digest + '.json.gz'), 'wb') as stream:
                stream.write(gzip.compress(b'{}'))
            with self.assertRaises(ValueError):book_evidence.load(digest, directory)
            with self.assertRaises(ValueError):book_evidence.load('../outside', directory)

    def test_future_shadow_positions_bind_entry_and_exit_books(self):
        prices, books = model.load_prices(), model.load_books()
        window, archive = model.load_funding(), model.load_funding('archive')
        start = min(max(v) for k, v in archive.items() if k in books) - 2 * shadow.DAY_MS + 1
        with tempfile.TemporaryDirectory() as directory:
            retain = lambda book: book_evidence.store(book, directory)
            rows, positions, executions = [], [], {}
            with patch.object(shadow.ledger, 'append', side_effect=rows.append):
                shadow.open_batch(1, start, prices, window, books, positions, book_recorder=retain)
            self.assertGreater(len(rows), 10)
            self.assertEqual(set(rows[0]['book_evidence']), set(positions[0]['legs']))
            shadow.close_due(start + shadow.DAY_MS + 60000, books, archive, positions, executions, {}, book_recorder=retain)
            for record in executions.values():
                self.assertEqual(book_evidence.replay(record, directory)['book_walks_replayed'], 4)


if __name__ == '__main__':unittest.main()
