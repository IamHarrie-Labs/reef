"""Evaluate every frozen shadow record, including failures in the denominator.

The predictions are prospective; this evaluation protocol was added after
historical outcomes. Baselines use only settlements strictly before entry.
No bootstrap or independence-based significance claim is made.
"""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0, str(Path(__file__).parent))
import ledger, model, score

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'web/public/validation'
PROTOCOL = {
    'version': 'reef-consecutive-1',
    'selection': 'Every shadow ledger row, sorted by recorded timestamp and record key; no outcome-based selection or row cap.',
    'funding_baselines': ['zero funding', 'last settled rate strictly before entry, projected over the frozen hold with frozen signed weights'],
    'direction_baseline': 'always nonpositive paper net P&L',
    'economic_baseline': 'no trade: zero trading P&L, excluding idle-capital returns',
    'aggregation': 'Paired mean absolute errors on the same eligible records, plus equal-weight entry batches and pair/hold breakdowns.',
    'incomplete': 'Keep every pending, missed or incomplete record with its reason. Never impute an outcome.',
    'interpretation': 'Overlapping holds and shared instruments are dependent; no statistical significance or portfolio return is inferred.',
    'history_boundary': 'Historical predictions were recorded before paper outcomes; this evaluation protocol is retrospective for existing records.',
}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def portable(value):
    if isinstance(value,dict): return {str(k):portable(v) for k,v in value.items()}
    if isinstance(value,list): return [portable(v) for v in value]
    if isinstance(value,float) and not math.isfinite(value): return str(value)
    return value

def last_rate_forecast(row, funding):
    ev = row['evidence']
    forecast = 0.0
    for name, leg in zip(ev['pair'].split('/'), ('a', 'b')):
        known = {int(t): rate for t, rate in funding.get(name+'USDT', {}).items() if int(t) < row['ts']}
        if len(known) < 3:
            return None
        times = sorted(known)[-100:]
        cadence = round(86400000 / model.intervals_per_day(times))
        last = times[-1]
        # A stale or irregular prior schedule is not a usable persistence baseline.
        if row['ts'] - last > cadence or any(b-a != cadence for a,b in zip(times, times[1:])):
            return None
        end = row['ts'] + int(ev['hold_days']*86400000)
        settlements = max(0, (end-last)//cadence - (row['ts']-last)//cadence)
        forecast -= ev['edge']['weights'][leg] * known[last] * settlements
    return forecast

def metrics(rows):
    common = [r for r in rows if r.get('last_rate_funding_bp') is not None and r.get('predicted_funding_bp') is not None]
    graded = [r for r in rows if r['status']=='graded']
    mean = lambda xs: statistics.mean(xs) if xs else None
    cost = [r for r in graded if r.get('realised_cost_bp') is not None and r.get('predicted_cost_bp') is not None]
    return {
        'n':len(rows), 'n_graded':len(graded), 'n_funding_comparison':len(common),
        'reef_funding_mae_bp':mean([abs(r['realised_funding_bp']-r['predicted_funding_bp']) for r in common]),
        'zero_funding_mae_bp':mean([abs(r['realised_funding_bp']) for r in common]),
        'last_rate_funding_mae_bp':mean([abs(r['realised_funding_bp']-r['last_rate_funding_bp']) for r in common]),
        'reef_beats_zero_n':sum(abs(r['realised_funding_bp']-r['predicted_funding_bp']) < abs(r['realised_funding_bp']) for r in common),
        'reef_beats_last_rate_n':sum(abs(r['realised_funding_bp']-r['predicted_funding_bp']) < abs(r['realised_funding_bp']-r['last_rate_funding_bp']) for r in common),
        'reef_direction_agreement':mean([(r['net_bp']>0)==(r['predicted_net_bp']>0) for r in graded]),
        'always_nonpositive_agreement':mean([r['net_bp']<=0 for r in graded]),
        'cost_mae_bp':mean([abs(r['realised_cost_bp']-r['predicted_cost_bp']) for r in cost]),
        'n_cost':len(cost), 'n_predicted_positive':sum(r['predicted_net_bp']>0 for r in graded),
        'n_observed_positive':sum(r['net_bp']>0 for r in graded),
        'mean_paper_net_bp':mean([r['net_bp'] for r in graded]), 'no_trade_net_bp':0,
    }

def evaluate(inputs, cutoff_ms, future_start_ms=None):
    funding = {s:{int(t):v for t,v in rates.items()} for s,rates in inputs['funding'].items()}
    rows = sorted((r for r in inputs['ledger'] if r.get('shadow') and r['ts']<=cutoff_ms), key=lambda r:(r['ts'],score.execution_key(r['ts'],r.get('evidence',{}).get('pair'),r.get('evidence',{}).get('hold_days'))))
    out=[]
    seen=set()
    for row in rows:
        ev=row.get('evidence',{})
        key=score.execution_key(row['ts'],ev.get('pair'),ev.get('hold_days'))
        if key in seen:
            raise ValueError('Duplicate record key; reconcile source ledger before evaluation')
        seen.add(key)
        result=score.grade_row(row,funding=funding,executions=inputs['executions'],now_ms=cutoff_ms)
        record={**result,'key':key,'recorded_ms':row['ts'],'hold_days':ev.get('hold_days')}
        execution=inputs['executions'].get(key,{})
        if result['status']=='insufficient_execution_or_funding_data' and execution.get('status')=='missed_exit_window':
            record['status']='missed_exit_window'
        if result['status']=='graded':
            source_times=[int(t) for group in ev.get('source_timestamps',{}).values() for t in group.values() if t is not None]
            if any(t>row['ts'] for t in source_times):
                record['status']='source_timestamp_after_entry'
            else:
                record['last_rate_funding_bp']=last_rate_forecast(row,funding)
        out.append(record)
    batches=defaultdict(list)
    groups=defaultdict(list)
    for r in out:
        batches[str(r['recorded_ms'])].append(r)
        groups[f"{r['pair']} | {r['hold_days']}d"].append(r)
    batch_results=[{'recorded_ms':int(k),**metrics(v)} for k,v in sorted(batches.items(),key=lambda x:int(x[0]))]
    usable=[b for b in batch_results if b['n_funding_comparison']]
    return {'schema':'reef-consecutive-validation-1','cutoff_ms':cutoff_ms,'protocol':PROTOCOL,
            'future_start_ms':future_start_ms,'future_cohort':metrics([r for r in out if future_start_ms is not None and r['recorded_ms']>future_start_ms]),
            'input_sha256':digest(inputs),'counts':dict(sorted(Counter(r['status'] for r in out).items())),
            'first_recorded_ms':rows[0]['ts'] if rows else None,'last_recorded_ms':rows[-1]['ts'] if rows else None,
            'summary':metrics(out),'n_batches':len(batches),'n_funding_batches':len(usable),
            'batch_equal_weight':{k:statistics.mean(b[k] for b in usable) if usable else None for k in ['reef_funding_mae_bp','zero_funding_mae_bp','last_rate_funding_mae_bp']},
            'batches':batch_results,'by_pair_hold':{k:metrics(v) for k,v in sorted(groups.items())},'records':out,
            'limits':['Paper fills, not executed orders or a portfolio simulation.',
                      'Bulk record chronology relies on captured ledger timestamps. Bitcoin proof timing is verified separately for the portable single case, not for every record in this report.',
                      'Prior-rate values are reconstructed from the captured exchange archive; individual rates are not independently authenticated.',
                      'Missing outcomes may bias complete-case results. Status counts include them.',
                      'Shared instruments, common entry batches and overlapping holds create dependence.',
                      'No-trade is an economic reference, not a funding forecast. Mean paper P&L is not portfolio performance.',
                      'Funding errors compare signed-reference-notional estimates with settlement-mark cash flows; mark changes contribute to the error.']}

def write(cutoff_ms=None):
    cutoff_ms=cutoff_ms or int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
    # Legacy non-finite descriptive fields (e.g. infinite break-even) become
    # strings in the portable input; financial scoring fields stay numeric.
    inputs=portable({'ledger':[r for r in ledger.read_all() if r.get('shadow')],'executions':score.load_executions(),'funding':model.load_funding('archive')})
    PUBLIC.mkdir(parents=True,exist_ok=True)
    protocol_path=PUBLIC/'protocol.json'
    if not protocol_path.exists():
        protocol_path.write_text(json.dumps({'future_start_ms':cutoff_ms,'protocol':PROTOCOL,'protocol_sha256':digest(PROTOCOL)},indent=2),encoding='utf-8')
    locked=json.loads(protocol_path.read_text(encoding='utf-8'))
    if locked['protocol_sha256']!=digest(PROTOCOL) or locked['protocol']!=PROTOCOL:
        raise ValueError('Protocol changed; publish a new protocol version instead of silently revising this cohort')
    report=evaluate(inputs,cutoff_ms,locked['future_start_ms'])
    (PUBLIC/'consecutive-cases.json').write_text(json.dumps(report,separators=(',',':'),allow_nan=False),encoding='utf-8')
    (PUBLIC/'consecutive-inputs.json').write_text(json.dumps(inputs,separators=(',',':'),allow_nan=False),encoding='utf-8')
    compact={k:v for k,v in report.items() if k not in ('records','by_pair_hold','batches')}
    compact['by_hold']={str(h):metrics([r for r in report['records'] if r['hold_days']==h]) for h in sorted({r['hold_days'] for r in report['records']})}
    (PUBLIC/'consecutive-summary.json').write_text(json.dumps(compact,separators=(',',':'),allow_nan=False),encoding='utf-8')
    print(json.dumps({'counts':report['counts'],'summary':report['summary'],'n_batches':report['n_batches'],'batch_equal_weight':report['batch_equal_weight']},indent=2))
    return compact

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.verify:
        report=json.loads((PUBLIC/'consecutive-cases.json').read_text())
        inputs=json.loads((PUBLIC/'consecutive-inputs.json').read_text())
        if evaluate(inputs,report['cutoff_ms'],report.get('future_start_ms'))!=report:
            raise ValueError('Report does not reproduce from its input bundle')
        print('Every status, baseline, aggregate and chronological record reproduces from the input bundle.')
    else: write()
