#!/usr/bin/env python3
"""Verify and summarize a NEW ablation; synthetic and pilot data are ineligible."""
import argparse, csv, io, json, math, random, statistics
from collections import Counter,defaultdict
from pathlib import Path
import study as s

def quantile(values,p):
    v=sorted(values);x=(len(v)-1)*p;lo=math.floor(x);hi=math.ceil(x)
    return v[lo]*(hi-x)+v[hi]*(x-lo) if hi!=lo else v[lo]

def validate_trial(g,root,protocol,spec,reference):
    folder=root/spec['trial_id'];r=json.loads((folder/'trial.json').read_text())
    for k,v in spec.items():
        if r.get(k)!=v:raise s.ContractError('trial identity mismatch')
    if r['protocol_sha256']!=s.file_sha(root/'protocol.json'):raise s.ContractError('trial protocol mismatch')
    if r['phase']!=protocol['phase'] or r['synthetic']!=protocol['synthetic']:raise s.ContractError('trial mode mismatch')
    run=s.inference_run(reference);providers,has_roles=s.VARIANTS[spec['variant']]
    names=['assessor_'+p for p in providers]+(['role_'+p for p in s.ROLES] if has_roles else [])
    if r['planned_calls_attempted']!=len(names):raise s.ContractError('wrong number of model calls')
    results={}; previous={}; aggregate=None; synthetics=False
    for name in names:
        result=json.loads((folder/(name+'_result.json')).read_text())
        wire=json.loads((folder/(name+'_wire.json')).read_text())
        request=json.loads((folder/(name+'_request.json')).read_text())
        if result['http_status']!=wire['status'] or result['request_wall_ms']!=wire['request_wall_ms']:raise s.ContractError('node transport mismatch')
        if not math.isfinite(wire['request_wall_ms']) or wire['request_wall_ms']<0:raise s.ContractError('invalid node timer')
        raw=wire['body'];sha=s.digest(raw.encode())
        if sha!=wire['retained_response_sha256']:raise s.ContractError('retained response hash mismatch')
        if not wire['redacted'] and sha!=wire['raw_response_sha256']:raise s.ContractError('raw response hash mismatch')
        if result['raw_response_sha256']!=wire['raw_response_sha256']:raise s.ContractError('node hash mismatch')
        if name.startswith('assessor_'):
            provider=name.removeprefix('assessor_');system,user=g.assessment_prompt(run);cap=protocol['assessor_tokens']
        else:
            if aggregate is None:
                aggregate=s.aggregate(g,results,providers);run['aggregate_json']=aggregate
                if aggregate!=json.loads((folder/'aggregate.json').read_text()):raise s.ContractError('aggregate mismatch')
            role=name.removeprefix('role_');provider=s.ROLE_PROVIDER[role];system,user=g.role_prompt(role,run,previous);cap=protocol['role_tokens']
        if request!=s.request_body(provider,protocol['environment']['models'][provider],system,user,cap):
            raise s.ContractError('request contract mismatch')
        # Re-parse retained payloads to avoid trusting a reported semantic count.
        valid=False;assessment=None;artifact=None;payload=None
        try:
            if wire['status']!=200 or wire['redacted']:raise ValueError('unusable response')
            payload=json.loads(raw);text=g.response_text(provider,payload)
            synthetics |= payload.get('model')=='SYNTHETIC_FIXTURE'
            if name.startswith('assessor_'):a=g.parse_assessment_response(text)
            else:
                parsed_role=g.RoleArtifact.model_validate(g.extract_json_object(text))
                if parsed_role.role!=role:raise ValueError('role mismatch')
                artifact=parsed_role
                a=g.role_artifact_to_assessment(artifact)
            assessment=a.model_dump(); valid=True
        except Exception:pass
        if not wire['redacted']:
            if assessment!=result['assessment'] or valid!=result['valid_json']:raise s.ContractError('parsed output mismatch')
            if (artifact.model_dump() if artifact is not None else None)!=result['artifact']:raise s.ContractError('role artifact mismatch')
            if isinstance(payload,dict):
                if result['returned_model']!=payload.get('model') or result['system_fingerprint']!=payload.get('system_fingerprint'):
                    raise s.ContractError('returned model metadata mismatch')
                if result.get('usage')!=payload.get('usage'):raise s.ContractError('token usage mismatch')
            if result['requested_model']!=request['model'] or result['provider']!=provider:raise s.ContractError('requested model mismatch')
            if valid and g.validate_assessment_against_bundle(a,run['retrieval_json'])['valid']!=result['deterministic_validation']['valid']:
                raise s.ContractError('grounding validation mismatch')
        if name.startswith('assessor_'):results[provider]=result
        else:previous[role]={'artifact':result['artifact'],'valid_json':result['valid_json'],
          'deterministic_validation':{'valid':result['deterministic_validation']['valid']}}
    if aggregate is None:
        aggregate=s.aggregate(g,results,providers)
        if aggregate!=json.loads((folder/'aggregate.json').read_text()):raise s.ContractError('aggregate mismatch')
    candidate=None;candidate_valid=False
    if has_roles:
        arb=json.loads((folder/'role_arbiter_result.json').read_text())
        if arb['valid_json'] and arb['deterministic_validation']['valid']:candidate=arb['assessment'];candidate_valid=True
    else:
        candidate=s.without_roles(g,aggregate);candidate_valid=bool(aggregate['valid_provider_count']>=math.ceil(.75*len(providers)))
    if r['valid_final_candidate']!=candidate_valid:raise s.ContractError('final validity mismatch')
    if r['outcome']!=s.review_guard(g,candidate,aggregate):raise s.ContractError('policy outcome mismatch')
    if r['outcome']['execute'] is not False or r['outcome']['network_actions']!=0:raise s.ContractError('non-review-only outcome')
    t=r['timing_boundaries_ns']
    if len(t)!=5 or any(b<a for a,b in zip(t,t[1:])):raise s.ContractError('nonmonotonic timing')
    if not math.isfinite(r['decision_ready_wall_ms']) or r['decision_ready_wall_ms']<0:raise s.ContractError('invalid total timer')
    for k,x,y in zip(['assessment','aggregation','role_or_adapter','governance'],t,t[1:]):
        if not math.isfinite(r['stage_wall_ms'][k]) or abs(r['stage_wall_ms'][k]-(y-x)/1e6)>1e-6:raise s.ContractError('phase timer mismatch')
    if abs(sum(r['stage_wall_ms'].values())-r['decision_ready_wall_ms'])>1e-6:raise s.ContractError('overlapping/incomplete stages')
    if abs(r['decision_ready_wall_ms']-(t[-1]-t[0])/1e6)>1e-6:raise s.ContractError('total timer mismatch')
    actual_nodes=[json.loads((folder/(name+'_result.json')).read_text()) for name in names]
    if r['nodes']!=actual_nodes or r['transport_complete']!=all(x['http_status']==200 for x in actual_nodes):raise s.ContractError('node coverage mismatch')
    return r,synthetics

def summarize(root,bootstrap_replicates=20000):
    n=s.verify_seal(root);protocol=json.loads((root/'protocol.json').read_text())
    if s.file_sha(root/'protocol.json')!=(root/'PROTOCOL_SHA256.txt').read_text().strip():raise s.ContractError('protocol hash mismatch')
    if protocol['study_code_sha256']!=s.file_sha(s.__file__):raise s.ContractError('analysis code input version mismatch')
    if protocol['harness_sha256']!=s.harness_hashes():raise s.ContractError('harness code identity mismatch')
    if protocol['source_sha256']!=s.SOURCE_SHA or protocol['input_sha256']!=s.INPUT_SHA:raise s.ContractError('source/input identity mismatch')
    if protocol['trials']!=s.schedule(protocol['phase'],protocol['seed']):raise s.ContractError('schedule mismatch')
    references={r['cell_id']:r for r in s.rows()};g=s.adapter();byvariant=defaultdict(list);blocks=defaultdict(dict);missing=[];synthetics=False
    for spec in protocol['trials']:
        if not (root/spec['trial_id']/'trial.json').exists():missing.append(spec['trial_id']);continue
        r,syn=validate_trial(g,root,protocol,spec,references[spec['cell_id']]);synthetics|=syn
        byvariant[r['variant']].append(r);blocks[r['block']][r['variant']]=r
    summaries={}
    for name in s.VARIANTS:
        records=byvariant[name];a=[x['decision_ready_wall_ms']/1000 for x in records]
        decision=action=pre_review_action=finalvalid=never_total=never_hit=false_never=0
        for r in records:
            ref=references[r['cell_id']];decision+=r['outcome']['decision']==ref['oracle_decision'];action+=r['outcome']['enforced_action_class']==ref['oracle_action_class'];finalvalid+=r['valid_final_candidate']
            pre_review_action+=r['outcome']['reconciliation']['reconciled_action_class']==ref['oracle_action_class']
            never_total+=ref['oracle_action_class']=='NEVER'
            never_hit+=ref['oracle_action_class']=='NEVER' and r['outcome']['enforced_action_class']=='NEVER'
            false_never+=ref['oracle_action_class']!='NEVER' and r['outcome']['enforced_action_class']=='NEVER'
        summaries[name]={'n':len(records),'decision_agreement_count':decision,'enforced_action_agreement_count':action,
          'pre_review_reconciled_action_agreement_count':pre_review_action,
          'oracle_never_denominator':never_total,'oracle_never_hits':never_hit,'false_never_count':false_never,
          'valid_final_candidates':finalvalid,'http_complete_trials':sum(x['transport_complete'] for x in records),
          'median_seconds':statistics.median(a) if a else None,'p95_seconds':quantile(a,.95) if a else None,
          'timing_population':'all completed trials, including transport/output failures; inspect HTTP counts',
          'stage_medians_seconds':{k:statistics.median(x['stage_wall_ms'][k]/1000 for x in records) for k in ['assessment','aggregation','role_or_adapter','governance']} if records else {}}
    contrasts={'added_assessors_roles_off':lambda v:v['B_FOUR_NO_ROLES']-v['A_ONE_NO_ROLES'],
      'added_assessors_roles_on':lambda v:v['D_FOUR_ROLES']-v['C_ONE_ROLES'],
      'role_chain_one_assessor':lambda v:v['C_ONE_ROLES']-v['A_ONE_NO_ROLES'],
      'role_chain_four_assessors':lambda v:v['D_FOUR_ROLES']-v['B_FOUR_NO_ROLES'],
      'interaction':lambda v:(v['D_FOUR_ROLES']-v['B_FOUR_NO_ROLES'])-(v['C_ONE_ROLES']-v['A_ONE_NO_ROLES'])}
    clusters=defaultdict(list);excluded=[]
    for block,values in blocks.items():
        if set(values)!=set(s.VARIANTS) or not all(r['transport_complete'] for r in values.values()):excluded.append(block);continue
        first=next(iter(values.values()));clusters[first['scenario_id']].append({k:r['decision_ready_wall_ms']/1000 for k,r in values.items()})
    effects={};rng=random.Random(20261016);cluster_ids=sorted(clusters)
    for name,formula in contrasts.items():
        vals=[formula(v) for k in cluster_ids for v in clusters[k]]
        result={'complete_http_blocks':len(vals),'mean_paired_seconds':statistics.mean(vals) if vals else None,'descriptive_cluster_interval':None}
        if len(cluster_ids)==6:
            draws=[]
            for _ in range(bootstrap_replicates):
                values=[formula(v) for c in rng.choices(cluster_ids,k=6) for v in clusters[c]]
                draws.append(statistics.mean(values))
            result['descriptive_cluster_interval']=[quantile(draws,.025),quantile(draws,.975)]
        effects[name]=result
    eligible=(protocol['phase']=='full' and not protocol['synthetic'] and not synthetics and not missing
      and len(protocol['trials'])==240 and len(cluster_ids)==6 and not any(r['response_redactions'] for rs in byvariant.values() for r in rs))
    identities={}
    for provider in s.PROVIDERS:
        nodes=[n for records in byvariant.values() for r in records for n in r['nodes'] if n['provider']==provider]
        identities[provider]={'attempted_calls':len(nodes),
          'requested_models':sorted({n['requested_model'] for n in nodes}),
          'returned_models':sorted({n['returned_model'] for n in nodes if isinstance(n['returned_model'],str)}),
          'missing_returned_model_count':sum(n['returned_model'] is None for n in nodes),
          'system_fingerprints':sorted({n['system_fingerprint'] for n in nodes if isinstance(n['system_fingerprint'],str)}),
          'missing_system_fingerprint_count':sum(n['system_fingerprint'] is None for n in nodes),
          'usage_records_present':sum(isinstance(n.get('usage'),dict) and bool(n['usage']) for n in nodes)}
    return {'schema':'tnsm.matched_analysis.v1','publication_eligible_for_bounded_full_study':eligible,
      'phase':protocol['phase'],'synthetic':protocol['synthetic'] or synthetics,
      'manifest_entries_verified':n,'missing_trials':missing,'variants':summaries,'paired_effects':effects,'provider_identity_observations':identities,
      'excluded_from_primary_http_complete_block_effects':excluded,'scenario_clusters':len(cluster_ids),
      'scope':'New common-harness inference/role-block comparison. No historical latency-gap decomposition, orchestration-overhead estimate, expert validation or O-RAN actuation. Six-cluster intervals are descriptive.',
      'protocol_sha256':s.file_sha(root/'protocol.json')}

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--report-dir',type=Path,required=True);args=p.parse_args()
    if args.report_dir.resolve().is_relative_to(args.input.resolve()):raise SystemExit('Analysis must be outside the sealed run directory.')
    summary=summarize(args.input);args.report_dir.mkdir(parents=True,exist_ok=False)
    s.write_json(args.report_dir/'analysis.json',summary)
    with (args.report_dir/'variants.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['variant','n','decision_matches','action_matches','valid_final_candidates','HTTP_complete','median_seconds','p95_seconds'])
        for k,v in summary['variants'].items():w.writerow([k]+[v[x] for x in ['n','decision_agreement_count','enforced_action_agreement_count','valid_final_candidates','http_complete_trials','median_seconds','p95_seconds']])
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
