"""Score recorded executions only. Never substitute residual returns for net P&L.

execution evidence requires per-leg signed qty, entry_price, exit_price,
entry_ts, exit_ts, fees_usdt, and settlement_marks {timestamp: mark_price}.
No fills means insufficient data, not a fabricated hit rate.
"""
import datetime as dt
import math
import model, ledger


def grade_row(row, prices=None, funding=None, now_ms=None):
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
    execution = row.get('execution')
    if not execution or funding is None:
        return {**result, 'status': 'insufficient_execution_or_funding_data'}
    price_pnl = fees = carry = 0.0
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
        if leg['entry_ts'] != row['ts'] or leg['exit_ts'] != end:
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
    net = price_pnl+carry-fees
    return {**result, 'status': 'graded', 'price_pnl_usdt': price_pnl,
            'funding_usdt': carry, 'fees_usdt': fees, 'net_usdt': net,
            'net_bp': net/ev['size']*1e4, 'predicted_net_bp': ev['risk_adjusted']['net_bp'],
            'note': 'One realised return does not validate an expected Sharpe or confidence interval.'}


if __name__ == '__main__':
    import json
    funding = model.load_funding('archive')
    for row in ledger.read_all():
        print(json.dumps(grade_row(row, funding=funding)))
