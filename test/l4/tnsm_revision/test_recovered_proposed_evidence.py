import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT/'scripts/l4/tnsm_revision'
spec = importlib.util.spec_from_file_location('recovered', SCRIPTS/'audit_recovered_proposed_evidence.py')
recovered = importlib.util.module_from_spec(spec);spec.loader.exec_module(recovered)
from audit_retained_revision_evidence import ARCHIVES, archive_files


class RecoveredProposedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        inputs = ROOT/'paper/tnsm_revision_20261015/evidence/inputs'
        packages = {key:archive_files(inputs/name)[0] for key,name in ARCHIVES.items()}
        cls.oracle = [json.loads(line) for line in packages['oracle']['canonical_oracle_180.jsonl'].decode().splitlines()]
        cls.summary = json.loads(packages['clustered']['oracle_clustered_statistics.json'])
        cls.prompts = [json.loads(line) for line in packages['provenance']['r10_prompt_reconstruction.jsonl'].decode().splitlines()]
        cls.report = recovered.analyse(inputs/recovered.BUNDLE_NAME, cls.oracle, cls.summary, cls.prompts)

    def test_every_original_run_is_bound_to_the_released_reference(self):
        r = self.report
        self.assertEqual((r['successful_cells'],r['distinct_run_ids'],r['run_manifests']),(180,180,180))
        self.assertEqual((r['evidence_files'],r['run_manifest_entries_verified']),(3420,3240))
        self.assertEqual(r['hash_checks']['report_canonical_hashes_and_released_oracle_joins'],180)
        self.assertEqual(r['hash_checks']['providers_raw_response_hashes'],720)
        self.assertEqual(r['hash_checks']['roles_raw_response_hashes'],720)

    def test_raw_counts_and_clustered_intervals_reproduce_the_frozen_summary(self):
        expected = {'NO_RAG':(10,40,0,0,204), 'RAG':(50,50,40,10,235), 'AGENTIC_RAG':(60,58,50,19,230)}
        for mode, values in expected.items():
            row = self.report['by_mode'][mode]
            self.assertEqual(tuple(row[key] for key in ('decision_agreement_count','action_agreement_count','coverage_count','never_class_correct_count','provider_valid_count')),values)
            self.assertEqual(row['automatic_execution_enabled_count'],0)
            self.assertEqual(row['clustered_metrics'],self.summary['by_mode'][mode]['metrics'])

    def test_disjoint_timestamps_cover_all_cells_without_summing_parallel_calls(self):
        r = self.report
        for row in r['cells']:
            intervals = [row[key] for key in ('input_to_retrieval_s','retrieval_to_aggregate_s','aggregate_to_post_role_reflection_s','post_role_reflection_to_report_s')]
            self.assertAlmostEqual(sum(intervals),row['internal_report_wall_s'],places=7)
            self.assertGreaterEqual(row['index_minus_internal_s'],0)
        agentic = r['by_mode']['AGENTIC_RAG']['timing_s']
        self.assertEqual(agentic['aggregate_to_post_role_reflection_s']['n'],60)
        self.assertAlmostEqual(agentic['aggregate_to_post_role_reflection_s']['median'],79.6081255)
        self.assertEqual(agentic['summed_assessor_call_s']['n'],57)

    def test_manifest_tampering_and_traversal_are_rejected(self):
        for manifest in [b'000000  data.json\n',b'000000  ../data.json\n']:
            with self.subTest(manifest=manifest),self.assertRaises(ValueError):
                recovered.verify_manifest({'SHA256SUMS.txt':manifest,'data.json':b'changed'},'SHA256SUMS.txt')
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw,mode='w:gz') as archive:
            info = tarfile.TarInfo('symlink');info.type=tarfile.SYMTYPE;info.linkname='/tmp/other';archive.addfile(info)
        with self.assertRaisesRegex(ValueError,'non-regular'):
            recovered.read_archive(raw.getvalue())

    def test_changed_bundle_is_rejected_before_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'changed.tar.gz';path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'digest differs'):
                recovered.analyse(path,self.oracle,self.summary,self.prompts)


if __name__ == '__main__':
    unittest.main()
