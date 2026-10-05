"""Retain complete captured books for future hypothetical fill replay.

Content hashes bind the parsed snapshot used by the model. They do not certify
the exchange source or establish that actual orders would receive these fills.
"""
import gzip
import hashlib
import json
import math
import os
import re
import sys
sys.path.insert(0, os.path.dirname(__file__))
import model

BOOKS = os.path.join(model.DATA, 'shadow', 'books')


def canonical(book):
    return json.dumps(book, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def store(book, directory=BOOKS):
    raw = canonical(book)
    digest = hashlib.sha256(raw).hexdigest()
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, digest + '.json.gz')
    if not os.path.exists(path):
        temporary = path + '.tmp'
        with open(temporary, 'wb') as stream:
            stream.write(gzip.compress(raw, mtime=0))
        os.replace(temporary, path)
    return digest


def load(digest, directory=BOOKS):
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('Invalid book content hash')
    with gzip.open(os.path.join(directory, digest + '.json.gz'), 'rb') as stream:
        raw = stream.read()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('Book snapshot changed after recording')
    return json.loads(raw)


def replay(record, directory=BOOKS):
    import shadow  # delayed import avoids a cycle with the recorder
    checked = 0
    for symbol, leg in record.get('execution', {}).items():
        for phase in ('entry', 'exit'):
            digest = leg.get(phase + '_book_sha256')
            if not digest:
                raise ValueError('Original book unavailable for this legacy execution')
            book = load(digest, directory)
            if book.get('timestamp') != leg.get(phase + '_book_ts'):
                raise ValueError('Book timestamp differs from the execution record')
            q = leg['qty']
            side = ('asks' if q > 0 else 'bids') if phase == 'entry' else ('bids' if q > 0 else 'asks')
            price = shadow.vwap(book[side], qty=abs(q))
            if price is None or not math.isclose(price, leg[phase + '_price'], rel_tol=1e-10, abs_tol=1e-9):
                raise ValueError(f'{symbol} {phase} fill cannot be reproduced from its book')
            if not math.isclose(shadow.mid(book), leg[phase + '_mid'], rel_tol=1e-12):
                raise ValueError('Recorded mid price differs from the captured book')
            checked += 1
    if not checked:
        raise ValueError('No executions to replay')
    return {'book_walks_replayed': checked, 'source_authenticated': False, 'fills_hypothetical': True}


if __name__ == '__main__':
    import argparse
    import score
    parser = argparse.ArgumentParser()
    parser.add_argument('--replay', required=True, metavar='EXECUTION_KEY')
    args = parser.parse_args()
    try:
        print(json.dumps(replay(score.load_executions()[args.replay]), indent=2))
    except (ValueError, KeyError, FileNotFoundError) as error:
        parser.exit(1, f'Cannot replay: {error}\n')
