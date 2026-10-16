"""Regression coverage for the separately implemented retained-study audit."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SPEC=importlib.util.spec_from_file_location('matched_audit',ROOT/'scripts/l4/tnsm_revision/audit_matched_inference_evidence.py')
MODULE=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)

class MatchedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report,cls.rows=MODULE.audit(MODULE.PAPER/'evidence/inputs/TNSM_12002_Matched_Ablation_Evidence_20261016T194059Z.tar.gz')

    def test_retains_failures_and_distinct_analysis_populations(self):
        self.assertEqual(len(self.rows),240)
        self.assertEqual(self.report['excluded_primary_blocks'],[7])
        self.assertEqual(self.report['full_calls'],1080)
        self.assertEqual(sum(v['valid_nodes'] for v in self.report['variants'].values()),1035)
        self.assertEqual(self.report['invalid_node_categories'],{
            'provider_refusal':33,'transport_failure':1,'schema_or_json_failure':5,'reference_check_failure':6})
        self.assertEqual(self.report['paired_effects']['interaction']['primary_n'],59)
        self.assertEqual(self.report['paired_effects']['interaction']['post_hoc_strict_completion_n'],32)

    def test_does_not_conflate_decision_gain_with_never_recall(self):
        a=self.report['variants']['A_ONE_NO_ROLES'];d=self.report['variants']['D_FOUR_ROLES']
        self.assertGreater(d['decision_agreement_count'],a['decision_agreement_count'])
        self.assertLess(d['oracle_never_hits'],a['oracle_never_hits'])
        self.assertLess(d['pre_review_reconciled_action_agreement_count'],a['pre_review_reconciled_action_agreement_count'])
        self.assertEqual(sum(n['valid'] for n in self.report['reasoning_fallback_nodes']),4)

    def test_modified_uploaded_archive_is_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'changed.tar.gz';p.write_bytes(b'changed evidence')
            with self.assertRaisesRegex(ValueError,'archive identity changed'):
                MODULE.audit(p)

    def test_r7_tail_quantile_is_interpolated(self):
        self.assertAlmostEqual(MODULE.quantile([10,1,4,2],.95),9.1)

if __name__=='__main__':unittest.main()
