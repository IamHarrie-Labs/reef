"""Hand-calculated accounting and validation regressions; offline."""
import unittest, math
import model, capacity, intervals, score, llm
D=86_400_000

def book(mid=100, spread=0, qty=100000):
    return {'asks':[(mid+spread/2,qty)],'bids':[(mid-spread/2,qty)]}

def funding(a=1,b=0, days=30, step_a=8,step_b=8):
    return {'AUSDT':{h*3600000:a for h in range(0,days*24+1,step_a)},
            'BUSDT':{h*3600000:b for h in range(0,days*24+1,step_b)}}

class Accounting(unittest.TestCase):
    def test_hedge_and_residual(self):
        p={'A':{},'B':{}}
        for h in range(100):
            p['A'][h*3600000]=100*math.exp(.001*h)
            p['B'][h*3600000]=100*math.exp(.002*h)
        beta,n=model.hedge_ratio(p,'A','B')
        self.assertAlmostEqual(beta,2)
        self.assertAlmostEqual(model.residual_vol(p,'A','B',beta)[0],0)
    def test_funding_weights(self):
        e=model.funding_edge(funding(), 'AUSDT','BUSDT',2)
        self.assertEqual(e['weights'],{'a':-2,'b':1})
        self.assertEqual(e['bp_per_day'],6)
    def test_inverse_same_side(self):
        e=model.funding_edge(funding(), 'AUSDT','BUSDT',-2)
        self.assertEqual(e['weights'],{'a':-2,'b':-1})
    def test_unequal_cadences(self):
        rows=model.funding_days(funding(1,1,step_a=4,step_b=8),'AUSDT','BUSDT',1)
        self.assertEqual(rows[0][1],3)
    def test_missing_settlement_rejects_day(self):
        f=funding(); del f['AUSDT'][D+8*3600000]
        self.assertNotIn(D,[t for t,v in model.funding_days(f,'AUSDT','BUSDT',1)])
    def test_direction_not_reselected(self):
        f=funding()
        for t in f['AUSDT']:
            if t>=18*D:f['AUSDT'][t]=-10
        e=model.funding_edge(f,'AUSDT','BUSDT',1)
        self.assertEqual(e['direction_sign'],1)
        self.assertLess(e['bp_per_day'],0)
    def test_dollar_weighted_cost(self):
        books={'A':book(spread=.2),'B':book(spread=.4)}
        # A: 2*$1000*2*(10bp slip+6bp fee); B: $1000*2*(20+6)bp
        self.assertAlmostEqual(model.round_trip_cost(books,'A','B',1000,2),116)
    def test_thin_book(self):
        self.assertIsNone(model.round_trip_cost({'A':book(qty=1),'B':book()},'A','B',1000,1))
    def test_invalid_size(self):
        with self.assertRaises(ValueError):model.round_trip_cost({},'A','B',-1,1)
    def test_invalid_hold(self):
        with self.assertRaises(ValueError):model.net_carry({'bp_per_day':1},20,0)
    def test_verdicts(self):
        self.assertEqual(intervals.verdict_for(1,{'lo':-.1}), 'UNPROVEN')
        self.assertEqual(intervals.verdict_for(1,{'lo':.1}), 'SUPPORTED')
        self.assertEqual(intervals.verdict_for(-1,None), 'UNFAVOURABLE')
    def fixture(self):
        ev={'model_version':'2.0','pair':'A/B','size':1000,'hold_days':1,
            'edge':{'weights':{'a':-2,'b':1}},'risk_adjusted':{'net_bp':0}}
        row={'ts':D,'evidence':ev,'execution':{}}
        for s,q in [('AUSDT',-20),('BUSDT',10)]:
            row['execution'][s]={'qty':q,'entry_price':100,'exit_price':100,'entry_ts':D,'exit_ts':2*D,
              'fees_usdt':1,'settlement_marks':{str(t):100 for t in (D+8*3600000,D+16*3600000,2*D)}}
        return row
    def test_realised_net(self):
        r=score.grade_row(self.fixture(),funding=funding(),now_ms=3*D)
        self.assertEqual(r['status'],'graded')
        self.assertAlmostEqual(r['funding_usdt'],.6)
        self.assertAlmostEqual(r['net_usdt'],-1.4)
    def test_missing_fill(self):
        row=self.fixture();del row['execution']
        self.assertEqual(score.grade_row(row,now_ms=3*D)['status'],'insufficient_execution_or_funding_data')
    def test_missing_mark(self):
        row=self.fixture();row['execution']['AUSDT']['settlement_marks']={}
        self.assertEqual(score.grade_row(row,funding=funding(),now_ms=3*D)['status'],'missing_settlement_mark')
    def test_short_window(self):
        row=self.fixture();row['execution']['AUSDT']['exit_ts']-=1
        self.assertEqual(score.grade_row(row,funding=funding(),now_ms=3*D)['status'],'incomplete_execution_window')
    def test_legacy_is_not_graded(self):
        row=self.fixture();del row['evidence']['model_version']
        self.assertEqual(score.grade_row(row,now_ms=3*D)['status'],'superseded_model')

class Integration(unittest.TestCase):
    def test_split_and_exact_notional(self):
        from unittest.mock import patch
        p=model.load_prices(); f=model.load_funding(); books=model.load_books()
        r=capacity.analyse_pair(p,f,books,'XAUUSDT','XAUTUSDT')
        self.assertLess(r['split'],r['edge']['validation_start'])
        train=[t for t in set(p['XAUUSDT']) & set(p['XAUTUSDT']) if t<=r['split']]
        self.assertGreater(len(train),30)
        ra=capacity.risk_adjusted(r,12345,30)
        self.assertEqual(ra['cost_bp'],model.round_trip_cost(books,r['a'],r['b'],12345,r['beta']))
    def test_cli_evidence_frozen_before_explanation(self):
        from unittest.mock import patch
        import verdict
        events=[]
        with patch.object(llm,'available',return_value=False), patch.object(verdict.ledger,'append',side_effect=lambda row:events.append(('log',row))), patch.object(llm,'synthesize',side_effect=lambda ev: events.append(('explain',ev)) or 'template'):
            ev,text=verdict.answer('XAU/XAUT at $12345 over 30 days')
        self.assertEqual([x[0] for x in events],['log','explain'])
        self.assertEqual(ev['size'],12345)
        self.assertEqual(ev['model_version'],'2.0')
        self.assertEqual(ev['verdict'],intervals.verdict_for(ev['risk_adjusted']['sharpe'],ev['ci']))
    def test_pair_order_canonical(self):
        import verdict
        self.assertEqual(verdict.resolve_pair('B','A',{'x':['A','B']}),('A','B'))
        self.assertEqual(verdict.resolve_pair('B','C',{'x':['A','B']}),(None,None))
    def test_llm_numeric_invention_rejected(self):
        from unittest.mock import patch
        with patch.object(llm,'_chat',return_value='Profit will be 999999 percent.'):
            with self.assertRaises(ValueError):llm._synthesize_llm({'verdict':'UNPROVEN','number':1})

if __name__=='__main__': unittest.main()

