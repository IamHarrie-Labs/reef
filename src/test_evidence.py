"""Regression checks for descriptive baselines, accounting and portable proofs."""
import copy
import json
import os
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(__file__))
import anchor, case_study, score


class EvidenceTests(unittest.TestCase):
    def test_direction_baseline_does_not_reward_only_negative_predictions(self):
        rows = [{'pair': 'A/B', 'hold_days': 1, 'verdict': 'UNFAVOURABLE',
                 'predicted_net_bp': -2, 'net_bp': actual, 'predicted_funding_bp': 1,
                 'realised_funding_bp': 3, 'predicted_cost_bp': 2,
                 'realised_cost_bp': 5} for actual in (-1, 0, 4)]
        summary = score.summarise(rows)
        self.assertEqual(summary['net_sign_agreement'], 2/3)
        self.assertEqual(summary['always_nonpositive_agreement'], 2/3)
        self.assertEqual(summary['n_predicted_positive'], 0)
        self.assertEqual(summary['n_observed_positive'], 1)
        self.assertEqual(summary['mean_abs_cost_error_bp'], 3)
        self.assertEqual(summary['mean_abs_funding_error_bp'], 2)
        rows[-1]['predicted_net_bp'] = 2
        self.assertEqual(score.summarise(rows)['net_sign_agreement'], 1)
        self.assertEqual(score.summarise(rows)['always_nonpositive_agreement'], 2/3)

    def test_merkle_tampering(self):
        objects = [{'value': 1}, {'value': 2}, {'value': 3}]
        leaves = [{'kind': 'ledger', 'id': str(i), 'hash': anchor.leaf(obj)} for i, obj in enumerate(objects)]
        root, _ = anchor.merkle([item['hash'] for item in leaves])
        proof = case_study.inclusion(objects[2], leaves, 'ledger', '2', root)
        case_study.verify_inclusion(objects[2], proof, root)
        with self.assertRaises(ValueError):
            case_study.verify_inclusion({'value': 4}, proof, root)
        with self.assertRaises(ValueError):
            case_study.verify_inclusion(objects[2], proof, '00'*32)

    def test_case_recomputed_and_tampering_rejected(self):
        with open(case_study.PATH, encoding='utf-8') as stream:
            bundle = json.load(stream)
        filename = 'reef-case-' + bundle['key'].replace(':', '-').replace('/', '-') + '.json'
        with open(os.path.join(case_study.PUBLIC, filename), encoding='utf-8') as stream:
            self.assertEqual(bundle, json.load(stream))
        self.assertTrue(case_study.verify(bundle)['proofs_and_accounting_valid'])
        mutations = [lambda b: b['prediction']['evidence'].__setitem__('size', 1),
                     lambda b: b['execution_record']['execution'][next(iter(b['execution_record']['execution']))].__setitem__('exit_price', 1),
                     lambda b: b['result'].__setitem__('net_bp', 0),
                     lambda b: b['timeline'].__setitem__('maturity_ms', 0),
                     lambda b: b['prediction_anchor']['bitcoin_header'].__setitem__('hash', '00'*32),
                     lambda b: b['prediction_anchor'].__setitem__('ots_base64', b['outcome_anchor']['ots_base64'])]
        for mutate in mutations:
            changed = copy.deepcopy(bundle)
            mutate(changed)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                case_study.verify(changed)

    def test_online_header_disagreement_rejected(self):
        with open(case_study.PATH, encoding='utf-8') as stream:
            bundle = json.load(stream)
        with patch.object(case_study, 'fetch_text', return_value='00'*32), self.assertRaises(ValueError):
            case_study.verify(bundle, online=True)


if __name__ == '__main__':
    unittest.main()
