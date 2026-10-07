import unittest
from unittest.mock import patch
import prospective_validation as pv

def row(ts=4*28800000):
    return {'ts':ts,'shadow':True,'evidence':{'pair':'A/B','hold_days':1,'edge':{'weights':{'a':-2,'b':1}}}}

class ValidationTests(unittest.TestCase):
    def test_baseline_ignores_entry_and_future_rates(self):
        r=row(); rates={t:1 for t in (28800000,57600000,86400000)}
        funding={'AUSDT':{**rates,r['ts']:999,r['ts']+1:999},'BUSDT':rates}
        self.assertEqual(pv.last_rate_forecast(r,funding),3)

    def test_missing_prior_history_is_not_zero(self):
        self.assertIsNone(pv.last_rate_forecast(row(),{}))

    def test_all_statuses_and_order_preserved(self):
        inputs={'ledger':[row(20),row(10)],'executions':{},'funding':{}}
        with patch.object(pv.score,'grade_row',return_value={'pair':'A/B','status':'pending'}):
            report=pv.evaluate(inputs,30)
        self.assertEqual([r['recorded_ms'] for r in report['records']],[10,20])
        self.assertEqual(report['counts'],{'pending':2})
        self.assertEqual(report['summary']['n_graded'],0)
        self.assertIsNone(report['summary']['reef_funding_mae_bp'])

    def test_duplicate_keys_fail(self):
        inputs={'ledger':[row(),row()],'executions':{},'funding':{}}
        with patch.object(pv.score,'grade_row',return_value={'pair':'A/B','status':'pending'}):
            with self.assertRaisesRegex(ValueError,'Duplicate'):pv.evaluate(inputs,10**12)

    def test_paired_errors_exclude_unavailable_baseline(self):
        base={'status':'graded','net_bp':-5,'predicted_net_bp':-2,'predicted_funding_bp':1,'realised_funding_bp':3}
        m=pv.metrics([{**base,'last_rate_funding_bp':2},{**base,'last_rate_funding_bp':None}])
        self.assertEqual(m['n_funding_comparison'],1)
        self.assertEqual((m['reef_funding_mae_bp'],m['zero_funding_mae_bp'],m['last_rate_funding_mae_bp']),(2,3,1))
        self.assertEqual(m['always_nonpositive_agreement'],m['reef_direction_agreement'])

    def test_future_cohort_does_not_relabel_historical_rows(self):
        inputs={'ledger':[row(10),row(20)],'executions':{},'funding':{}}
        with patch.object(pv.score,'grade_row',return_value={'pair':'A/B','status':'pending'}):
            report=pv.evaluate(inputs,30,future_start_ms=10)
        self.assertEqual(report['summary']['n'],2)
        self.assertEqual(report['future_cohort']['n'],1)

    def test_missed_exit_remains_in_denominator(self):
        r=row();key=pv.score.execution_key(r['ts'],'A/B',1)
        inputs={'ledger':[r],'executions':{key:{'status':'missed_exit_window'}},'funding':{}}
        with patch.object(pv.score,'grade_row',return_value={'pair':'A/B','status':'insufficient_execution_or_funding_data'}):
            report=pv.evaluate(inputs,10**12)
        self.assertEqual(report['counts'],{'missed_exit_window':1})
        self.assertEqual(report['summary']['n'],1)

    def test_future_source_timestamp_cannot_be_graded(self):
        r=row();r['evidence']['source_timestamps']={'funding':{'AUSDT':r['ts']+1}}
        inputs={'ledger':[r],'executions':{},'funding':{}}
        with patch.object(pv.score,'grade_row',return_value={'pair':'A/B','status':'graded','net_bp':-1,'predicted_net_bp':-1}):
            report=pv.evaluate(inputs,10**12)
        self.assertEqual(report['counts'],{'source_timestamp_after_entry':1})
        self.assertEqual(report['summary']['n_graded'],0)

    def test_entry_batches_receive_equal_weight_despite_different_sizes(self):
        second=row(10);second['evidence']['pair']='C/D'
        inputs={'ledger':[row(10),second,row(20)],'executions':{},'funding':{}}
        def grade(r,**kwargs):
            return {'pair':r['evidence']['pair'],'status':'graded','net_bp':-1,'predicted_net_bp':-1,'predicted_funding_bp':1 if r['ts']==10 else 9,'realised_funding_bp':0}
        with patch.object(pv.score,'grade_row',side_effect=grade),patch.object(pv,'last_rate_forecast',return_value=0):
            report=pv.evaluate(inputs,30)
        self.assertAlmostEqual(report['summary']['reef_funding_mae_bp'],11/3)
        self.assertEqual(report['batch_equal_weight']['reef_funding_mae_bp'],5)

if __name__=='__main__':unittest.main()
