import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('audit',ROOT/'scripts/l4/tnsm_revision/audit_retained_revision_evidence.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class RevisionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit.analyse(ROOT/'paper/tnsm_revision_20261015/evidence/inputs')

    def test_retained_qwen_labels_are_not_execution_events(self):
        q=self.report['systems']['qwen']['ablations']
        self.assertEqual(q['native_class_guard']['never_execute_true_declaration_count'],9)
        self.assertEqual(q['native_class_guard']['nonautomatic_oracle_execute_true_declaration_count'],38)
        self.assertFalse(q['native_class_guard']['actual_network_executions_measured'])

    def test_review_only_ablation_preserves_semantic_outputs(self):
        for name,s in self.report['systems'].items():
            native=s['ablations']['native_class_guard'];inhibited=s['ablations']['native_guard_with_automatic_execution_disabled']
            self.assertEqual(native['decision_agreement_count'],inhibited['decision_agreement_count'],name)
            self.assertEqual(native['action_agreement_count'],inhibited['action_agreement_count'],name)
            self.assertEqual(inhibited['execute_true_declaration_count'],0,name)

    def test_guard_does_not_treat_a_model_automatic_class_as_oracle_truth(self):
        wrong={'decision':'COMPLIANT','action_class':'AUTOMATIC','execute':True}
        self.assertTrue(audit.structural_guard(wrong)['execute'])
        self.assertFalse(audit.review_only(wrong)['execute'])
        self.assertEqual(wrong['execute'],True)

    def test_guard_rejects_string_execute_flags(self):
        with self.assertRaises(ValueError):
            audit.structural_guard({'decision':'UNCERTAIN','action_class':'HUMAN','execute':'false'})

    def test_frozen_reference_does_not_test_all_action_classes(self):
        self.assertEqual(self.report['oracle_action_counts'],{'HUMAN':120,'NEVER':60})
        self.assertEqual(self.report['scenario_count'],6)

    def test_proposed_never_recall_matches_retained_histograms_and_manuscript(self):
        modes=self.report['proposed_metrics_from_retained_summary']
        self.assertEqual(modes['AGENTIC_RAG']['never_class_correct_count'],19)
        self.assertEqual(modes['AGENTIC_RAG']['never_reference_count'],20)
        self.assertEqual(modes['AGENTIC_RAG']['never_action_recall'],.95)
        self.assertEqual(modes['RAG']['never_action_recall'],.5)
        self.assertEqual(modes['NO_RAG']['never_action_recall'],0)
        text=(ROOT/'paper/tnsm_revision_20261015/main.tex').read_text()
        proposed_row=text.split('Proposed system & Agentic RAG / 60')[1].split('\\\\')[0]
        self.assertIn('95.0\\%',proposed_row)
        self.assertNotIn('100.0\\% & 109.793',proposed_row)

    def test_summary_joint_score_refuses_unstable_decision_marginals(self):
        group={'by_mode':{'TEST':{'repeat_consistency':[{'scenario_id':'S1','repeats':2,
            'decision_counts':{'COMPLIANT':1,'UNCERTAIN':1},'action_counts':{'HUMAN':2}}]}}}
        with self.assertRaisesRegex(ValueError,'joint count unavailable'):
            audit.proposed_metrics_from_summary(group,{'S1':('COMPLIANT','HUMAN')})

    def test_timing_intervals_do_not_sum_overlapping_provider_calls(self):
        t=self.report['live_trace_timing']
        self.assertAlmostEqual(t['internal_report_wall_s'],108.938646,places=6)
        self.assertGreater(t['summed_assessor_call_s'],t['parallel_assessor_wall_s'])
        self.assertAlmostEqual(t['disjoint_wall_intervals_s']['aggregate_to_post_role_reflection'],77.572908,places=6)

    def test_archive_traversal_and_checksum_tampering_fail(self):
        for member_name,body,manifest in [('../escape',b'x',b''),('record.json',b'changed',b'000000 record.json\n')]:
            with self.subTest(member_name=member_name),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'input.tar.gz'
                with tarfile.open(p,'w:gz') as t:
                    for n,b in [(member_name,body),('SHA256SUMS.txt',manifest)]:
                        info=tarfile.TarInfo(n);info.size=len(b);t.addfile(info,io.BytesIO(b))
                with self.assertRaises(ValueError):audit.archive_files(p)

if __name__=='__main__':unittest.main()
