"""Check shipped web evidence against the calculator without changing data."""
import json
from pathlib import Path
import model, capacity, intervals


def main():
    root = Path(__file__).resolve().parent.parent
    web = json.loads((root/'web/web_export.json').read_text(encoding='utf-8'))
    data = json.loads((root/'data/web_export.json').read_text(encoding='utf-8'))
    assert web == data, 'Website and data exports differ'
    assert web['model_version'] == '2.0'
    prices, funding, books = model.load_prices(), model.load_funding(), model.load_books()
    checked = 0
    for pair in web['pairs']:
        r = capacity.analyse_pair(prices, funding, books, pair['a'], pair['b'])
        assert r is not None, pair['pair']
        assert pair['beta'] == r['beta']
        assert pair['price_train_end'] == r['split']
        for size in web['sizes']:
            for hold in web['holds']:
                cell = pair['grid'][str(size)][str(hold)]
                ra = capacity.risk_adjusted(r, size, hold)
                if ra is None:
                    assert cell is None
                    continue
                ci = intervals.sharpe_interval(r, ra, funding, hold)
                for key, digits in [('cost_bp',1),('net_bp',1),('annual_pct',2),('risk_bp',0),('sharpe',3)]:
                    assert cell[key] == round(ra[key],digits), (pair['pair'],size,hold,key)
                assert cell['verdict'] == intervals.verdict_for(ra['sharpe'],ci)
                checked += 1
    print(f'PASS: {len(web["pairs"])} pairs, {checked} priced grid cells; exports and calculator agree.')

if __name__ == '__main__':
    main()
