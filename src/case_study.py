"""Portable case evidence. Build selects the earliest eligible completed shadow row.

Verification recomputes accounting and both Merkle inclusions, then uses the
OpenTimestamps library to verify the detached proof against the included Bitcoin
header. --online checks that header's height/hash with two public block explorers.
An offline header check alone does not establish membership in the canonical chain.
"""
import argparse
import base64
import datetime as dt
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.request
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
import anchor, ledger, model, score

PATH = os.path.join(model.DATA, 'case_study.json')
PUBLIC = os.path.join(model.DATA, '..', 'web', 'public', 'case-studies')
EXPLORERS = ('https://blockstream.info/api', 'https://blockchain.info')


def utc(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).isoformat()


def fetch_text(url):
    # Windows may resolve an unreachable IPv6 address first. curl's IPv4 option
    # avoids that failure; arguments are passed directly, without a shell.
    if os.name == 'nt' and shutil.which('curl.exe'):
        return subprocess.check_output(['curl.exe', '-4', '--fail', '--silent', '--show-error',
                                        '--connect-timeout', '12', '--max-time', '30', url],
                                       text=True, timeout=35).strip()
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode().strip()


def hash_at(origin, height):
    if origin == 'https://blockchain.info':
        blocks = json.loads(fetch_text(f'{origin}/block-height/{height}?format=json'))['blocks']
        canonical = [item for item in blocks if item.get('main_chain') and item['height'] == height]
        if len(canonical) != 1:
            raise ValueError('Explorer did not identify one canonical block')
        return canonical[0]['hash']
    return fetch_text(f'{origin}/block-height/{height}')


def header_at(height):
    hashes = [hash_at(origin, height) for origin in EXPLORERS]
    if hashes[0] != hashes[1]:
        raise ValueError('Block explorers disagree on the block hash')
    return {'height': height, 'hash': hashes[0],
            'hex': fetch_text(f'{EXPLORERS[0]}/block/{hashes[0]}/header'),
            'sources': list(EXPLORERS)}


def inclusion(obj, leaves, kind, key, root):
    indices = [i for i, item in enumerate(leaves) if item['kind'] == kind and item['id'] == key and item['hash'] == anchor.leaf(obj)]
    if not indices:
        raise ValueError('No matching anchored leaf')
    actual, levels = anchor.merkle([item['hash'] for item in leaves])
    if actual != root:
        raise ValueError('Leaf list does not match the anchor root')
    return {'leaf': anchor.leaf(obj), 'path': anchor.proof(levels, indices[0])}


def verify_inclusion(obj, evidence, root):
    node = anchor.leaf(obj)
    if node != evidence['leaf']:
        raise ValueError('Object changed after anchoring')
    for step in evidence['path']:
        if step['side'] not in ('left', 'right'):
            raise ValueError('Invalid Merkle path direction')
        raw = step['hash'] + node if step['side'] == 'left' else node + step['hash']
        node = hashlib.sha256(bytes.fromhex(raw)).hexdigest()
    if node != root:
        raise ValueError('Invalid Merkle inclusion')


def verify_timestamp(evidence, online=False):
    from opentimestamps.core.serialize import StreamDeserializationContext
    from opentimestamps.core.timestamp import DetachedTimestampFile
    from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
    header = evidence['bitcoin_header']
    raw = bytes.fromhex(header['hex'])
    if len(raw) != 80 or hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex() != header['hash']:
        raise ValueError('Invalid Bitcoin header hash')
    if online:
        for origin in EXPLORERS:
            if hash_at(origin, header['height']) != header['hash']:
                raise ValueError('Header is not at the stated canonical height')
    detached = DetachedTimestampFile.deserialize(StreamDeserializationContext(io.BytesIO(base64.b64decode(evidence['ots_base64'], validate=True))))
    root_bytes = (evidence['root'] + '\n').encode()
    if detached.file_hash_op.hash_fd(io.BytesIO(root_bytes)) != detached.timestamp.msg:
        raise ValueError('Timestamp is for a different root file')
    block = SimpleNamespace(hashMerkleRoot=raw[36:68], nTime=int.from_bytes(raw[68:72], 'little'))
    for message, attestation in detached.timestamp.all_attestations():
        if isinstance(attestation, BitcoinBlockHeaderAttestation) and attestation.height == header['height']:
            return attestation.verify_against_blockheader(message, block) * 1000
    raise ValueError('Proof has no attestation for this Bitcoin height')


def verify(bundle, online=False):
    row, execution, prediction = bundle['prediction'], bundle['execution_record'], bundle['prediction_anchor']
    key = anchor.row_key(row)
    verify_inclusion(row, prediction['inclusion'], prediction['root'])
    block_ms = verify_timestamp(prediction, online)
    end = row['ts'] + int(row['evidence']['hold_days'] * 86_400_000)
    if not row['ts'] <= block_ms < end:
        raise ValueError('Bitcoin header time does not fall between recording and maturity')
    outcome = bundle['outcome_anchor']
    verify_inclusion(execution, outcome['inclusion'], outcome['root'])
    outcome_block_ms = verify_timestamp(outcome, online)
    if outcome_block_ms < max(leg['exit_ts'] for leg in execution['execution'].values()):
        raise ValueError('Outcome block timestamp precedes the recorded exit')
    funding = {symbol: {int(t): value for t, value in rates.items()} for symbol, rates in bundle['funding'].items()}
    grade = score.grade_row(row, funding=funding, executions={key: execution}, now_ms=max(end, outcome_block_ms))
    if grade['status'] != 'graded':
        raise ValueError(f"Accounting is incomplete: {grade['status']}")
    for field in ('net_bp', 'realised_cost_bp', 'realised_funding_bp', 'net_usdt', 'fees_usdt', 'price_pnl_usdt', 'funding_usdt'):
        if not math.isclose(grade[field], bundle['result'][field], rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError(f'Reported accounting differs: {field}')
    expected = {'recorded_ms': row['ts'], 'bitcoin_ms': block_ms, 'maturity_ms': end,
                'exit_ms': max(leg['exit_ts'] for leg in execution['execution'].values()),
                'outcome_bitcoin_ms': outcome_block_ms}
    if bundle['timeline'] != expected:
        raise ValueError('Reported timeline differs from the proof and records')
    for name, predicted, observed in bundle['comparison']:
        fields = {'Execution cost': ('predicted_cost_bp', 'realised_cost_bp'),
                  'Funding carry': ('predicted_funding_bp', 'realised_funding_bp'),
                  'Net P&L': ('predicted_net_bp', 'net_bp')}[name]
        if [predicted, observed] != [grade[fields[0]], grade[fields[1]]]:
            raise ValueError('Reported comparison differs from accounting')
    return {'key': key, 'proofs_and_accounting_valid': True, 'block_time_precedes_maturity': True,
            'canonical_height_checked_online': online, 'bitcoin_utc': utc(block_ms),
            'maturity_utc': utc(end), 'net_bp': grade['net_bp']}


def build():
    funding, executions = model.load_funding('archive'), score.load_executions()
    headers = {}
    index = [item for item in anchor._index() if item.get('bitcoin_block')]
    def package(obj, kind, key):
        for item in index:
            with open(os.path.join(anchor.ANCHORS, item['id'] + '.leaves.json'), encoding='utf-8') as stream:
                leaves = json.load(stream)
            try:
                inc = inclusion(obj, leaves, kind, key, item['root'])
            except ValueError:
                continue
            height = item['bitcoin_block']
            if height not in headers:
                headers[height] = header_at(height)
            with open(os.path.join(anchor.ANCHORS, item['id'] + '.root.txt.ots'), 'rb') as stream:
                proof = base64.b64encode(stream.read()).decode()
            return {'id': item['id'], 'root': item['root'], 'inclusion': inc,
                    'ots_base64': proof, 'bitcoin_header': headers[height]}
        raise ValueError('No confirmed anchor matches the object')
    skipped = 0
    for row in sorted((r for r in ledger.read_all() if r.get('shadow')), key=lambda r: (r['ts'], anchor.row_key(r))):
        grade = score.grade_row(row, funding=funding, executions=executions)
        if grade['status'] != 'graded':
            skipped += 1
            continue
        key, ev = anchor.row_key(row), row['evidence']
        execution = executions[key]
        try:
            prediction, outcome = package(row, 'ledger', key), package(execution, 'execution', key)
            block_ms = verify_timestamp(prediction)
            end = row['ts'] + int(ev['hold_days'] * 86_400_000)
            if not row['ts'] <= block_ms < end:
                raise ValueError('Not anchored before maturity')
        except ValueError:
            skipped += 1
            continue
        # Include complete archived histories for these two symbols: the scorer's
        # coverage and cadence checks remain reproducible, including boundary rates.
        bundle = {'schema': 'reef-case-study-1', 'key': key,
                  'selection': 'Earliest completed shadow record by (recorded timestamp, record key) with matching confirmed prediction and outcome proofs, and a Bitcoin header time before maturity.',
                  'earlier_ineligible_records': skipped, 'prediction': row, 'execution_record': execution,
                  'prediction_anchor': prediction, 'outcome_anchor': outcome,
                  'funding': {symbol: funding[symbol] for symbol in execution['execution']},
                  'result': grade,
                  'timeline': {'recorded_ms': row['ts'], 'bitcoin_ms': block_ms, 'maturity_ms': end,
                               'exit_ms': max(leg['exit_ts'] for leg in execution['execution'].values()),
                               'outcome_bitcoin_ms': verify_timestamp(outcome)},
                  'comparison': [[name, grade[p], grade[o]] for name, p, o in (
                      ('Execution cost', 'predicted_cost_bp', 'realised_cost_bp'),
                      ('Funding carry', 'predicted_funding_bp', 'realised_funding_bp'),
                      ('Net P&L', 'predicted_net_bp', 'net_bp'))],
                  'limits': ['Hypothetical fills; no orders or market impact.',
                             'Original full entry and exit books were not retained per record; recorded fills cannot independently establish available depth.',
                             'Funding histories and settlement marks are exchange-source observations, not authenticated by Bitcoin.',
                             'The prediction timestamp binds its content; the outcome timestamp binds the recorded execution, not its factual correctness.',
                             'Bitcoin header timestamps are approximate chain times, not precise wall-clock certificates.',
                             'One realised P&L does not validate expected Sharpe or a funding-only confidence interval.']}
        bundle['verification'] = verify(bundle, online=True)
        with open(PATH, 'w', encoding='utf-8') as stream:
            json.dump(bundle, stream, indent=2, allow_nan=False)
        os.makedirs(PUBLIC, exist_ok=True)
        filename = 'reef-case-' + key.replace(':', '-').replace('/', '-') + '.json'
        with open(os.path.join(PUBLIC, filename), 'w', encoding='utf-8') as stream:
            json.dump(bundle, stream, indent=2, allow_nan=False)
        return bundle['verification']
    raise ValueError('No eligible completed record')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--verify', metavar='JSON')
    parser.add_argument('--online', action='store_true')
    parser.add_argument('--library-path')
    args = parser.parse_args()
    if args.library_path:
        sys.path.insert(0, args.library_path)
    if not args.build and not args.verify:
        parser.error('Choose --build or --verify JSON')
    try:
        if args.build:
            result = build()
        else:
            with open(args.verify, encoding='utf-8') as stream:
                result = verify(json.load(stream), args.online)
        print(json.dumps(result, indent=2))
    except (ValueError, ImportError) as error:
        parser.exit(1, f'Verification failed: {error}\n')
