"""Score recorded executions only. Never substitute residual returns for net P&L.

execution evidence requires per-leg signed qty, entry_price, exit_price,
entry_ts, exit_ts, fees_usdt, and settlement_marks {timestamp: mark_price}.
No fills means insufficient data, not a fabricated hit rate.

Executions come either inline on a ledger row or from the shadow desk's store
(data/shadow/executions.json), joined by ledger timestamp, pair and hold. The
ledger itself stays append-only: an outcome never rewrites its prediction.
"""
import datetime as dt
import json
import math
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
import model, ledger

EXECUTIONS = os.path.join(model.DATA, "shadow", "executions.json")
EXIT_GRACE_MS = 3 * 3_600_000  # a scheduled job exits within 3h of the hold ending


def execution_key(ts, pair, hold):
    return f"{ts}:{pair}:{hold}"


def load_executions():
    if not os.path.exists(EXECUTIONS):
        return {}
    with open(EXECUTIONS, encoding="utf-8") as f:
        return json.load(f)


def grade_row(row, prices=None, funding=None, now_ms=None, executions=None):
    ev = row.get('evidence', {})
    result = {'pair': ev.get('pair'), 'status': 'not_priced'}
    if 'error' in ev or 'risk_adjusted' not in ev:
        return result
    if ev.get('model_version') != '2.0':
        return {**result, 'status': 'superseded_model'}
    end = row['ts'] + int(ev['hold_days']*86_400_000)
    now = now_ms if now_ms is not None else int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
    if now < end:
        return {**result, 'status': 'pending', 'matures_ms': end}
    record = (executions or {}).get(execution_key(row['ts'], ev['pair'], ev['hold_days']))
    execution = row.get('execution') or (record or {}).get('execution')
    if not execution or funding is None:
        return {**result, 'status': 'insufficient_execution_or_funding_data'}
    price_pnl = fees = carry = slippage = 0.0
    for name, key in zip(ev['pair'].split('/'), ('a','b')):
        symbol = name+'USDT'
        leg = execution.get(symbol, {})
        required = ('qty','entry_price','exit_price','entry_ts','exit_ts','fees_usdt','settlement_marks')
        if any(k not in leg for k in required):
            return {**result, 'status': 'insufficient_execution_data'}
        q, entry, exit = leg['qty'], leg['entry_price'], leg['exit_price']
        if not all(math.isfinite(v) for v in (q,entry,exit,leg['fees_usdt'])) or min(entry,exit)<=0 or leg['fees_usdt']<0:
            return {**result, 'status': 'invalid_execution_data'}
        weight = ev['edge']['weights'][key]
        if not math.isclose(q*entry, ev['size']*weight, rel_tol=1e-6, abs_tol=1e-6):
            return {**result, 'status': 'execution_does_not_match_frozen_position'}
        if leg['entry_ts'] != row['ts'] or not end <= leg['exit_ts'] <= end + EXIT_GRACE_MS:
            return {**result, 'status': 'incomplete_execution_window'}
        rates = funding.get(symbol, {})
        if len(rates)<3 or min(rates)>row['ts'] or max(rates)<end:
            return {**result, 'status': 'insufficient_funding_coverage'}
        cadence = round(86_400_000/model.intervals_per_day(rates))
        ts = sorted(rates)
        if any(y-x != cadence for x,y in zip(ts,ts[1:]) if y>row['ts'] and x<end):
            return {**result, 'status': 'funding_gap'}
        for t, bp in rates.items():
            if row['ts'] < t <= end:
                mark = leg['settlement_marks'].get(str(t))
                if mark is None or not math.isfinite(mark) or mark<=0:
                    return {**result, 'status': 'missing_settlement_mark'}
                carry -= q*mark*bp/1e4
        price_pnl += q*(exit-entry)
        fees += leg['fees_usdt']
        if 'entry_mid' in leg and 'exit_mid' in leg:
            slippage += q*(entry-leg['entry_mid']) + q*(leg['exit_mid']-exit)
    net = price_pnl+carry-fees
    ra = ev['risk_adjusted']
    out = {**result, 'status': 'graded', 'price_pnl_usdt': price_pnl,
           'funding_usdt': carry, 'fees_usdt': fees, 'net_usdt': net,
           'net_bp': net/ev['size']*1e4, 'predicted_net_bp': ra['net_bp'],
           'realised_funding_bp': carry/ev['size']*1e4, 'predicted_funding_bp': ra.get('gross_bp'),
           'verdict': ev.get('verdict'), 'hold_days': ev['hold_days'],
           'execution_type': (record or {}).get('execution_type', 'recorded'),
           'note': 'One realised return does not validate an expected Sharpe or confidence interval.'}
    if slippage:
        out['realised_cost_bp'] = (slippage+fees)/ev['size']*1e4
        out['predicted_cost_bp'] = ra.get('cost_bp')
    return out


def summarise(graded):
    """Aggregate what the graded rows say about the model's parts, not a hit rate."""
    if not graded:
        return None
    mean = lambda xs: sum(xs)/len(xs) if xs else None
    cost = [g for g in graded if 'realised_cost_bp' in g]
    sign_ok = [(g['net_bp'] > 0) == (g['predicted_net_bp'] > 0) for g in graded]
    return {
        'n_graded': len(graded),
        'mean_predicted_net_bp': mean([g['predicted_net_bp'] for g in graded]),
        'mean_realised_net_bp': mean([g['net_bp'] for g in graded]),
        'net_sign_agreement': sum(sign_ok)/len(sign_ok),
        'n_with_cost_breakdown': len(cost),
        'mean_predicted_cost_bp': mean([g['predicted_cost_bp'] for g in cost]),
        'mean_realised_cost_bp': mean([g['realised_cost_bp'] for g in cost]),
        'mean_abs_cost_error_bp': mean([abs(g['realised_cost_bp']-g['predicted_cost_bp']) for g in cost]),
        'mean_predicted_funding_bp': mean([g['predicted_funding_bp'] for g in graded if g.get('predicted_funding_bp') is not None]),
        'mean_realised_funding_bp': mean([g['realised_funding_bp'] for g in graded]),
    }


if __name__ == '__main__':
    funding = model.load_funding('archive')
    executions = load_executions()
    results = [grade_row(row, funding=funding, executions=executions) for row in ledger.read_all()]
    for r in results:
        print(json.dumps(r))
    counts = {}
    for r in results:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    print('\nstatus counts:', json.dumps(counts))
    s = summarise([r for r in results if r['status'] == 'graded'])
    if s:
        print('graded summary:', json.dumps(s, indent=2))
