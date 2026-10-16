import asyncio, copy, importlib.util, json, os, shutil, sys, tempfile, threading, unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
CODE=ROOT/'scripts/l4/tnsm_revision/matched_ablation'
sys.path.insert(0,str(CODE))
import study as s
import analyze as a

class MatchedStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=s.adapter();cls.ref=s.rows()[10]
    def frozen(self,root,phase='pilot'):
        return s.freeze(root,phase,synthetic=True)
    def test_preflight_never_contacts_network(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
            s.adapter();s.rows();s.environment()
    def test_pinned_source_rejects_a_changed_file(self):
        with patch.object(s,'SOURCE_SHA','0'*64):
            with self.assertRaises(s.ContractError):s.adapter()
    def test_input_hash_rejects_changed_reference(self):
        with patch.object(s,'INPUT_SHA','0'*64):
            with self.assertRaises(s.ContractError):s.rows()
    def test_no_oracle_labels_or_scenario_title_in_model_input(self):
        for row in s.rows():
            system,user=self.g.assessment_prompt(s.inference_run(row))
            data=json.loads(user)
            self.assertEqual(data['scenario'],'Frozen O-RAN security-policy configuration')
            for key in ['oracle_decision','oracle_action_class','scenario_title','expected_decision']:
                self.assertNotIn(key,user)
    def test_shared_assessment_request_is_identical_for_all_variants(self):
        run=s.inference_run(self.ref);system,user=self.g.assessment_prompt(run)
        requests=[s.request_body('openai','same-model',system,user,5000) for _ in s.VARIANTS]
        self.assertTrue(all(r==requests[0] for r in requests))
    def test_request_caps_and_sampling_fields_are_explicit(self):
        for p in s.PROVIDERS:
            b=s.request_body(p,'model','system','user',4500)
            self.assertEqual(b.get('max_tokens',b.get('max_output_tokens')),4500)
            self.assertNotIn('temperature',b);self.assertNotIn('top_p',b)
            self.assertNotIn('tools',b)
    def test_full_schedule_is_balanced_and_has_240_trials(self):
        trials=s.schedule('full',20261016)
        self.assertEqual(len(trials),240)
        self.assertEqual(Counter(t['variant'] for t in trials),{v:60 for v in s.VARIANTS})
        for v in s.VARIANTS:
            self.assertEqual(Counter(t['position'] for t in trials if t['variant']==v),{1:15,2:15,3:15,4:15})
        for b in range(1,61):
            block=[t for t in trials if t['block']==b]
            self.assertEqual(len({t['input_side_sha256'] for t in block}),1)
    def test_single_assessor_has_explicit_valid_quorum(self):
        value={'valid_json':True,'deterministic_validation':{'valid':True},'assessment':{'decision':'COMPLIANT','violations':[],'action_class':'HUMAN'}}
        result=s.aggregate(self.g,{'openai':value},('openai',))
        self.assertEqual(result['consensus_decision'],'COMPLIANT')
        result=s.aggregate(self.g,{'openai':value},s.PROVIDERS)
        self.assertEqual(result['consensus_decision'],'UNCERTAIN')
    def test_review_guard_preserves_never_and_blocks_every_execution(self):
        candidate={'decision':'NON_COMPLIANT','violations':[{'clause':'P-03'}],'action_class':'AUTOMATIC'}
        r=s.review_guard(self.g,candidate,{})
        self.assertEqual(r['enforced_action_class'],'NEVER');self.assertIs(r['execute'],False)
        for candidate in [None,{'decision':'COMPLIANT','violations':[],'action_class':'AUTOMATIC'}]:
            r=s.review_guard(self.g,candidate,{})
            self.assertEqual(r['enforced_action_class'],'HUMAN');self.assertEqual(r['network_actions'],0)
    def test_protocol_detects_edit_before_run(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';self.frozen(out)
            p=out/'protocol.json';p.write_text(p.read_text()+' ')
            with self.assertRaises(s.ContractError):s.check_protocol(out)
    def test_invalid_caps_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run'
            with self.assertRaises(s.ContractError):s.freeze(out,'pilot',assessor_tokens=0,synthetic=True)
            self.assertFalse(out.exists())
    def test_live_freeze_without_provider_configuration_is_blocked(self):
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{},clear=True):
            with self.assertRaises(s.ContractError):s.freeze(Path(t)/'run','pilot')
    def test_synthetic_cannot_be_run_as_live(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';self.frozen(out)
            with patch.object(s,'transport',side_effect=AssertionError('network')):
                with self.assertRaises(s.ContractError):asyncio.run(s.execute(out,live=True))
    def test_redaction_does_not_copy_provider_key(self):
        secret='fixture-private-provider-key-123456'
        with patch.dict(os.environ,{'OPENAI_API_KEY':secret}):
            self.assertNotIn(secret,s.redact('echo '+secret))
    def test_pilot_runs_all_planned_calls_and_is_not_publication_eligible(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';p=self.frozen(out)
            calls=[]
            original=s.synthetic_transport
            def record(provider,body,timeout):calls.append(provider);return original(provider,body,timeout)
            with patch.object(s,'synthetic_transport',record):asyncio.run(s.execute(out))
            self.assertEqual(len(calls),36)
            summary=a.summarize(out,10)
            self.assertFalse(summary['publication_eligible_for_bounded_full_study'])
            self.assertTrue(summary['synthetic'])
            self.assertEqual(sum(v['n'] for v in summary['variants'].values()),8)
            for spec in p['trials']:
                trial=json.loads((out/spec['trial_id']/'trial.json').read_text())
                self.assertAlmostEqual(sum(trial['stage_wall_ms'].values()),trial['decision_ready_wall_ms'])
                self.assertIs(trial['outcome']['execute'],False)
    def test_four_assessors_are_dispatched_concurrently(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';p=self.frozen(out)
            spec=next(x for x in p['trials'] if x['variant']=='B_FOUR_NO_ROLES')
            ref=next(x for x in s.rows() if x['cell_id']==spec['cell_id']);barrier=threading.Barrier(4)
            def simultaneous(provider,body,timeout):
                barrier.wait(timeout=5);return s.synthetic_transport(provider,body,timeout)
            r=asyncio.run(s.trial(self.g,p,ref,spec,out/spec['trial_id'],simultaneous))
            self.assertEqual(r['planned_calls_attempted'],4)
    def test_roles_are_sequential_and_receive_only_prior_role_artifacts(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';p=self.frozen(out)
            spec=next(x for x in p['trials'] if x['variant']=='C_ONE_ROLES');ref=next(x for x in s.rows() if x['cell_id']==spec['cell_id']);seen=[]
            def record(provider,body,timeout):
                user=json.loads(body.get('input') or body['messages'][-1]['content'])
                if 'role' in user:
                    self.assertEqual(set(user['prior_role_artifacts']),set(seen));seen.append(user['role'])
                return s.synthetic_transport(provider,body,timeout)
            asyncio.run(s.trial(self.g,p,ref,spec,out/spec['trial_id'],record))
            self.assertEqual(seen,list(s.ROLES))
    def test_manifest_rejects_tampering_and_unbound_files(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';self.frozen(out);s.seal(out)
            extra=out/'unbound';extra.write_text('bad')
            with self.assertRaises(s.ContractError):s.verify_seal(out)
            extra.unlink();(out/'protocol.json').write_text('{}')
            with self.assertRaises(s.ContractError):s.verify_seal(out)
    def test_nested_manifest_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';self.frozen(out);s.seal(out)
            nested=out/'nested'/'SHA256SUMS.txt';nested.parent.mkdir();nested.write_text('unbound')
            with self.assertRaises(s.ContractError):s.verify_seal(out)
    def test_nan_total_timer_and_changed_model_metadata_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';p=self.frozen(out)
            spec=next(x for x in p['trials'] if x['variant']=='A_ONE_NO_ROLES');ref=next(x for x in s.rows() if x['cell_id']==spec['cell_id'])
            asyncio.run(s.trial(self.g,p,ref,spec,out/spec['trial_id'],s.synthetic_transport))
            path=out/spec['trial_id']/'trial.json';original=path.read_text();record=json.loads(original)
            record['decision_ready_wall_ms']=float('nan');path.write_text(json.dumps(record))
            with self.assertRaises(s.ContractError):a.validate_trial(self.g,out,p,spec,ref)
            path.write_text(original)
            path=out/spec['trial_id']/'assessor_openai_result.json';record=json.loads(path.read_text());record['returned_model']='pretend-snapshot';path.write_text(json.dumps(record))
            with self.assertRaises(s.ContractError):a.validate_trial(self.g,out,p,spec,ref)
    def test_fatal_provider_error_is_retained_and_not_retried(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';p=self.frozen(out);spec=next(x for x in p['trials'] if x['variant']=='A_ONE_NO_ROLES');ref=next(x for x in s.rows() if x['cell_id']==spec['cell_id']);calls=[]
            def fail(provider,body,timeout):calls.append(provider);return {'status':401,'raw':'{}','headers':{},'request_wall_ms':1.0}
            with self.assertRaises(s.FatalProviderError):asyncio.run(s.trial(self.g,p,ref,spec,out/spec['trial_id'],fail))
            self.assertEqual(len(calls),1)
            self.assertTrue((out/spec['trial_id']/'assessor_openai_wire.json').is_file())
    def test_completed_or_interrupted_run_cannot_be_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'run';self.frozen(out);(out/'attempts.jsonl').write_text('{}\n')
            with self.assertRaises(s.ContractError):asyncio.run(s.execute(out))
    def test_r7_quantile(self):
        self.assertEqual(a.quantile([1,2,3,4],.5),2.5)
        self.assertEqual(a.quantile([2],.95),2)

if __name__=='__main__':unittest.main()
