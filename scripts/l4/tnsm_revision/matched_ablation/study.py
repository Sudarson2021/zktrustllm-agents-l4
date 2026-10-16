#!/usr/bin/env python3
"""New matched inference study. No gateway routes or executors are invoked."""
from __future__ import annotations
import argparse, ast, asyncio, copy, csv, hashlib, io, json, math, os, platform, random
import re, statistics, sys, time, types, urllib.error, urllib.request, uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

HERE = Path(__file__).resolve().parent
SOURCE_SHA = '952fbbf87d1fc59a9e600718c9cf5ff6d2bc5c3eb24a3673a5203322921ed65e'
INPUT_SHA = '4854f1d42d7824ae48ae3b37d8402d468c9f11034aa26b0fd9e96a21e1196c6c'
PROVIDERS = ('openai', 'anthropic', 'deepseek', 'mistral')
ROLES = ('planner', 'critic', 'recovery', 'arbiter')
ROLE_PROVIDER = dict(zip(ROLES, PROVIDERS))
VARIANTS = {'A_ONE_NO_ROLES': (('openai',), False),
            'B_FOUR_NO_ROLES': (PROVIDERS, False),
            'C_ONE_ROLES': (('openai',), True),
            'D_FOUR_ROLES': (PROVIDERS, True)}
ENDPOINTS = {'openai': 'https://api.openai.com/v1/responses',
             'anthropic': 'https://api.anthropic.com/v1/messages',
             'deepseek': 'https://api.deepseek.com/chat/completions',
             'mistral': 'https://api.mistral.ai/v1/chat/completions'}
KEY_NAMES = {'openai': 'OPENAI_API_KEY', 'anthropic': 'ANTHROPIC_API_KEY',
             'deepseek': 'DEEPSEEK_API_KEY', 'mistral': 'MISTRAL_API_KEY'}
FUNCTIONS = {'now_iso', 'canonical_json', 'sha256_text', 'sha256_json',
 'extract_json_object', 'response_text', 'response_channel', 'parse_assessment_response',
 'usage_from_payload', 'assessment_prompt', 'validate_assessment_against_bundle',
 'role_artifact_to_assessment', 'role_prompt', 'reconcile_final_action_class'}
CLASSES = {'Violation', 'Assessment', 'RoleArtifact'}
CONSTANTS = {'ACTION_RANK', 'SEVERITY_RANK', 'FORBIDDEN_ACTION_TERMS', 'NEVER_ACTION_CLAUSES'}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
def digest(value: bytes):
    return hashlib.sha256(value).hexdigest()
def file_sha(path):
    return digest(Path(path).read_bytes())
def object_sha(value):
    return digest(canonical(value).encode())
def harness_hashes():
    return {name:file_sha(HERE/name) for name in ['study.py','analyze.py','launch.py','bootstrap.py']}
def utc():
    return datetime.now(timezone.utc).isoformat()
def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n'); f.flush(); os.fsync(f.fileno())
def append_json(path, value):
    with Path(path).open('a', encoding='utf-8') as f:
        f.write(canonical(value) + '\n'); f.flush(); os.fsync(f.fileno())
def redact(text):
    for key in KEY_NAMES.values():
        secret = os.environ.get(key, '')
        if secret: text = text.replace(secret, '<REDACTED>')
    return text

class ContractError(Exception): pass
class FatalProviderError(Exception): pass
class HTTPException(Exception):
    def __init__(self, status_code, detail): super().__init__(detail)


def adapter():
    """Compile only hash-pinned pure functions/classes, not the gateway module."""
    from pydantic import BaseModel, Field, ValidationError, field_validator
    source = HERE / 'gateway_reference.py.txt'
    if file_sha(source) != SOURCE_SHA: raise ContractError('gateway reference hash mismatch')
    tree = ast.parse(source.read_text())
    nodes = []; found = set()
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in FUNCTIONS:
            nodes.append(n); found.add(n.name)
        elif isinstance(n, ast.ClassDef) and n.name in CLASSES:
            nodes.append(n); found.add(n.name)
        elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in CONSTANTS:
            nodes.append(n); found.add(n.targets[0].id)
    if found != FUNCTIONS | CLASSES | CONSTANTS: raise ContractError('source selection mismatch')
    name = '_tnsm_pinned_pure_gateway'
    module = types.ModuleType(name); sys.modules[name] = module
    ns = module.__dict__
    ns.update({'Any': Any, 'Literal': Literal, 'BaseModel': BaseModel, 'Field': Field,
      'ValidationError': ValidationError, 'field_validator': field_validator,
      'HTTPException': HTTPException, 'json': json, 're': re, 'hashlib': hashlib,
      'datetime': datetime, 'timezone': timezone, 'Counter': Counter})
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), ns)
    return module


def environment():
    import importlib.metadata
    model = {p: os.environ.get(p.upper() + '_MODEL', '').strip() for p in PROVIDERS}
    configured = {p: bool(model[p] and len(os.environ.get(KEY_NAMES[p], ''))>=12 and all(33<=ord(c)<=126 for c in os.environ.get(KEY_NAMES[p], ''))) for p in PROVIDERS}
    try: pv = importlib.metadata.version('pydantic')
    except importlib.metadata.PackageNotFoundError: pv = None
    return {'python': platform.python_version(), 'pydantic': pv, 'platform': platform.platform(),
      'models': model, 'provider_configured': configured, 'gateway_image_id':os.environ.get('TNSM_GATEWAY_IMAGE_ID'),
      'provider_availability_tested': False, 'provider_calls_made': 0}


def rows():
    p = HERE / 'canonical_oracle_180.jsonl'
    if file_sha(p) != INPUT_SHA: raise ContractError('frozen input hash mismatch')
    all_rows = [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
    if len(all_rows) != 180 or len({r['cell_id'] for r in all_rows}) != 180:
        raise ContractError('invalid reference population')
    selected = [r for r in all_rows if r['retrieval_mode'] == 'AGENTIC_RAG']
    expected = {(f'S{s}', repeat) for s in range(1, 7) for repeat in range(1, 11)}
    if {(r['scenario_id'], r['repeat']) for r in selected} != expected or len(selected) != 60:
        raise ContractError('invalid Agentic-RAG population')
    return selected


def inference_run(row):
    """No reference labels are included in the model-facing structure."""
    payload = json.loads(row['scenario'])
    if set(payload) != {'configuration', 'retrieval_evidence', 'retrieval_mode', 'scenario_id', 'scenario_title', 'schema', 'task'}:
        raise ContractError('unexpected frozen input keys')
    config = canonical(payload['configuration'])
    if payload['retrieval_mode'] != 'AGENTIC_RAG': raise ContractError('unexpected input mode')
    evidence = copy.deepcopy(payload['retrieval_evidence'])
    evidence['bundle_hash'] = object_sha(evidence)
    return {'scenario': 'Frozen O-RAN security-policy configuration', 'input_text': config,
      'input_hash': digest(config.encode()), 'retrieval_json': evidence,
      'metadata_json': {'retrieval_mode': 'AGENTIC_RAG'}}


def schedule(phase, seed):
    source = rows()
    if phase == 'pilot': source = [r for r in source if r['scenario_id'] in {'S2', 'S4'} and r['repeat'] == 1]
    rng = random.Random(seed); rng.shuffle(source)
    # Four Williams sequences balance position and first-order carryover in full blocks.
    base = [(0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1)]
    names = list(VARIANTS); rng.shuffle(names)
    orders = (base * math.ceil(len(source) / 4))[:len(source)]; rng.shuffle(orders)
    trials = []
    for block, (row, order) in enumerate(zip(source, orders), 1):
        for position, number in enumerate(order, 1):
            trials.append({'trial_id': f'{block:03d}_{names[number]}', 'block': block,
              'position': position, 'variant': names[number], 'cell_id': row['cell_id'],
              'scenario_id': row['scenario_id'], 'repeat': row['repeat'],
              'input_side_sha256': object_sha(json.loads(row['scenario']))})
    return trials


def freeze(output, phase, assessor_tokens=5000, role_tokens=4500, seed=20261016, synthetic=False):
    env = environment()
    if not synthetic and not all(env['provider_configured'].values()):
        raise ContractError('all four provider keys/model aliases must be configured; no call made')
    if not isinstance(assessor_tokens, int) or not 256 <= assessor_tokens <= 8192:
        raise ContractError('invalid assessor output cap')
    if not isinstance(role_tokens, int) or not 256 <= role_tokens <= 8192:
        raise ContractError('invalid role output cap')
    adapter(); trials = schedule(phase, seed)
    calls = sum(len(VARIANTS[t['variant']][0]) + 4 * VARIANTS[t['variant']][1] for t in trials)
    assessment_calls = sum(len(VARIANTS[t['variant']][0]) for t in trials)
    cap = assessment_calls * assessor_tokens + (calls - assessment_calls) * role_tokens
    protocol = {'schema': 'tnsm.matched_inference.v1', 'created_at': utc(), 'phase': phase,
      'synthetic': synthetic, 'seed': seed, 'environment': env, 'source_sha256': SOURCE_SHA,
      'input_sha256': INPUT_SHA, 'study_code_sha256': file_sha(__file__), 'harness_sha256':harness_hashes(), 'trials': trials,
      'trial_count': len(trials), 'planned_provider_calls': calls,
      'maximum_requested_output_tokens_sum': cap, 'assessor_tokens': assessor_tokens,
      'role_tokens': role_tokens, 'timeout_seconds': 180, 'attempts_per_call': 1,
      'inter_trial_pause_seconds': 1.0, 'automatic_execution': False,
      'sampling_fields': 'NOT_SENT; provider defaults are not inferred',
      'timing': 'Prompt construction to common reconciliation/review-only guard; includes node artifact persistence. Frozen retrieval, final trial/index/manifest persistence, startup, operator waiting and external anchoring excluded.',
      'policy': 'Pinned reconcile_final_action_class plus common NEVER-preserving review-only guard; no OPA, proof, gateway route or executor is invoked.',
      'aggregation': 'Common prespecified consensus rule with expected count equal to configured assessor set; agreement >=0.75, valid count >=ceil(0.75*N); union of cited violations retained only for NON_COMPLIANT consensus.',
      'changes_from_historical': ['Shared new harness, no n8n/LangGraph overhead estimate',
         'Frozen input-side Agentic-RAG evidence; retrieval generation excluded',
         'Single-assessor branch generalized explicitly; role-free candidate derives from aggregate',
         'OpenAI store=false; explicit DeepSeek max_tokens cap',
         'Prompt metadata excludes fresh IDs, timing and raw-response hashes',
         'All four role calls attempted, including after invalid intermediate output',
         'New dates/aliases; historical latency gap is not retrospectively identified'],
      'analysis_plan': {'bootstrap_replicates':20000,'bootstrap_seed':20261016,'resampling_unit':'whole scenario; retain all complete paired blocks in a resampled scenario','primary_latency_population':'blocks with all four variants and all planned HTTP responses 200; report exclusions','semantic_population':'all completed planned trials; report missing trials and structural validity separately','estimands':'mean paired added-assessor effects at each role setting, role-chain effects at each assessor setting, and their interaction','variant_descriptions':'median and R7 P95 wall time; marginal phase medians are not additive','interval_boundary':'six scenario clusters only; descriptive intervals, no reliable nominal coverage claim'},
      'claim_boundary': 'Conditional component-block effects on six author-designed synthetic scenarios; no expert correctness, live O-RAN validation, framework attribution or production safety.'}
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'protocol.json', protocol)
    (output/'PROTOCOL_SHA256.txt').write_text(file_sha(output/'protocol.json') + '\n')
    return protocol


def check_protocol(output):
    p = output/'protocol.json'; protocol = json.loads(p.read_text())
    if file_sha(p) != (output/'PROTOCOL_SHA256.txt').read_text().strip(): raise ContractError('protocol changed')
    if protocol['study_code_sha256'] != file_sha(__file__): raise ContractError('study code changed')
    if protocol['harness_sha256'] != harness_hashes(): raise ContractError('harness code changed')
    if protocol['source_sha256'] != SOURCE_SHA or protocol['input_sha256'] != INPUT_SHA:
        raise ContractError('source/input binding changed')
    rows(); adapter()
    if protocol['trials'] != schedule(protocol['phase'], protocol['seed']): raise ContractError('schedule changed')
    if not protocol['synthetic'] and environment() != protocol['environment']:
        raise ContractError('runtime/model configuration changed; freeze a new study')
    return protocol


def request_body(provider, model, system, user, tokens):
    if provider == 'openai':
        return {'model': model, 'instructions': system, 'input': user, 'max_output_tokens': tokens, 'store': False}
    if provider == 'anthropic':
        return {'model': model, 'system': system, 'messages': [{'role': 'user', 'content': user}], 'max_tokens': tokens}
    return {'model': model, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
       'max_tokens': tokens, 'response_format': {'type': 'json_object'}, **({'stream': False} if provider == 'deepseek' else {})}


def transport(provider, body, timeout):
    key = os.environ.get(KEY_NAMES[provider], '').strip()
    if not key or len(key) < 12 or any(ord(c) < 33 or ord(c) > 126 for c in key):
        raise ContractError('missing or malformed provider key; no call made')
    headers = {'Content-Type': 'application/json'}
    if provider == 'anthropic': headers.update({'x-api-key': key, 'anthropic-version': '2023-06-01'})
    else: headers['Authorization'] = 'Bearer ' + key
    req = urllib.request.Request(ENDPOINTS[provider], data=canonical(body).encode(), headers=headers, method='POST')
    begin = time.perf_counter_ns()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(); status = response.status
            response_headers = {k.lower(): v for k,v in response.headers.items() if k.lower() in {'x-request-id','request-id','date','openai-processing-ms'}}
    except urllib.error.HTTPError as error:
        raw = error.read(); status = error.code; response_headers = {}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {'status': None, 'raw': canonical({'transport_error': redact(str(error))}),
          'request_wall_ms': (time.perf_counter_ns()-begin)/1e6, 'headers': {}}
    return {'status': status, 'raw': raw.decode('utf-8', errors='replace'),
      'request_wall_ms': (time.perf_counter_ns()-begin)/1e6, 'headers': response_headers}


def synthetic_transport(provider, body, timeout):
    # Plumbing fixture; deliberately not derived from oracle labels.
    content = {'decision':'COMPLIANT','violations':[], 'corrected_configuration_patch':'',
      'proposed_action':'review configuration','action_class':'HUMAN','confidence':0.5,
      'claim_boundary_ok':True,'uncertainties':[]}
    user = body.get('input') or body.get('messages', [])[-1]['content']
    parsed = json.loads(user)
    if 'role' in parsed:
        content.update({'role':parsed['role'], 'findings':[], 'needs_recovery':False})
    text = canonical(content)
    if provider == 'openai': payload = {'output_text':text}
    elif provider == 'anthropic': payload = {'content':[{'type':'text','text':text}]}
    else: payload = {'choices':[{'message':{'content':text}}]}
    payload.update({'model':'SYNTHETIC_FIXTURE', 'usage':{}})
    return {'status':200, 'raw':canonical(payload),'request_wall_ms':0.0, 'headers':{}}


async def call_node(g, protocol, folder, stage, provider, system, user, call_transport):
    tokens = protocol['assessor_tokens'] if stage.startswith('assessor') else protocol['role_tokens']
    body = request_body(provider, protocol['environment']['models'][provider], system, user, tokens)
    write_json(folder/(stage+'_request.json'),body)
    wire = await asyncio.to_thread(call_transport, provider, body, protocol['timeout_seconds'])
    raw = wire['raw']; safe = redact(raw)
    write_json(folder/(stage+'_wire.json'), {'status':wire['status'],'headers':wire['headers'],
      'request_wall_ms':wire['request_wall_ms'],'raw_response_sha256':digest(raw.encode()),
      'retained_response_sha256':digest(safe.encode()),'redacted':safe!=raw,'body':safe})
    result = {'provider':provider, 'valid_json':False, 'assessment':None, 'artifact':None,
      'http_status':wire['status'],'request_wall_ms':wire['request_wall_ms'],
      'deterministic_validation':{'valid':False}, 'raw_response_sha256':digest(raw.encode()),
      'requested_model':body['model'], 'returned_model':None, 'system_fingerprint':None,
      'input_tokens':None, 'output_tokens':None, 'response_redacted':safe!=raw}
    try:
        if wire['status'] != 200: raise ValueError('non-200 response')
        payload=json.loads(raw); text=g.response_text(provider,payload)
        result.update({'returned_model':payload.get('model'), 'system_fingerprint':payload.get('system_fingerprint'),
          'usage':payload.get('usage'), **g.usage_from_payload(provider,payload)})
        if stage.startswith('assessor'):
            a=g.parse_assessment_response(text)
        else:
            artifact=g.RoleArtifact.model_validate(g.extract_json_object(text))
            if artifact.role != stage.removeprefix('role_'): raise ValueError('role mismatch')
            a=g.role_artifact_to_assessment(artifact);result['artifact']=artifact.model_dump()
        result['assessment']=a.model_dump();result['valid_json']=True
        result['deterministic_validation']=g.validate_assessment_against_bundle(a,protocol['_retrieval'])
    except Exception as error:
        result['error']=redact(str(error))
    write_json(folder/(stage+'_result.json'),json.loads(redact(canonical(result))))
    if wire['status'] in {400,401,403,404,422}:
        raise FatalProviderError(f'{provider} HTTP {wire["status"]}; evidence saved; no automatic retry')
    return result


def aggregate(g, results, expected):
    valid={p:r for p,r in results.items() if r['valid_json'] and r['deterministic_validation']['valid']}
    counts=Counter(r['assessment']['decision'] for r in valid.values())
    top=counts.most_common(); agreement=(top[0][1]/len(valid)) if valid else 0.0
    decision=top[0][0] if top and len(valid)>=math.ceil(.75*len(expected)) and agreement>=.75 else 'UNCERTAIN'
    union={}
    for provider in expected:
        if provider not in valid: continue
        for v in valid[provider]['assessment']['violations']:
            key=(v['retrieved_chunk_id'],v['parameter'],v['severity'])
            item=union.setdefault(key,{**v,'supporting_providers':[]}); item['supporting_providers'].append(provider)
    violations=list(union.values()) if decision=='NON_COMPLIANT' else []
    action=max((r['assessment']['action_class'] for r in valid.values()),key=lambda x:g.ACTION_RANK[x],default='HUMAN')
    return {'consensus_decision':decision,'decision_counts':dict(counts),'agreement_rate':agreement,
      'conservative_action_class':action,'violations':violations,'valid_provider_count':len(valid),
      'provider_count':len(results),'expected_provider_count':len(expected),
      'missing_providers':sorted(set(expected)-set(results)), 'invalid_providers':sorted(set(results)-set(valid))}


def without_roles(g, agg):
    value={'decision':agg['consensus_decision'], 'violations':agg['violations'],
      'corrected_configuration_patch':'','proposed_action':'Review aggregate evidence',
      'action_class':agg['conservative_action_class'], 'confidence':agg['agreement_rate'],
      'claim_boundary_ok':True,'uncertainties':[]}
    if value['decision']=='NON_COMPLIANT' and not value['violations']: value['decision']='UNCERTAIN'
    return g.Assessment.model_validate(value).model_dump()


def review_guard(g, candidate, agg):
    if candidate is None: candidate={'decision':'UNCERTAIN','violations':[],'action_class':'HUMAN'}
    reconciliation=g.reconcile_final_action_class(candidate,agg)
    return {'decision':candidate['decision'] if candidate else 'UNCERTAIN',
      'enforced_action_class':'NEVER' if reconciliation['reconciled_action_class']=='NEVER' else 'HUMAN',
      'execute':False,'reconciliation':reconciliation,'network_actions':0,
      'policy_engine':'PINNED_RECONCILIATION_PLUS_COMMON_REVIEW_ONLY_GUARD_V1'}


async def trial(g, protocol, row, spec, folder, call_transport):
    folder.mkdir(parents=True,exist_ok=False)
    run=inference_run(row); p={**protocol,'_retrieval':run['retrieval_json']}
    expected, roles=VARIANTS[spec['variant']]; times=[time.perf_counter_ns()]
    system,user=g.assessment_prompt(run)
    results=await asyncio.gather(*(call_node(g,p,folder,'assessor_'+provider,provider,system,user,call_transport) for provider in expected),return_exceptions=True)
    fatal=next((r for r in results if isinstance(r,BaseException)),None)
    if fatal: raise fatal
    assessed=dict(zip(expected,results));times.append(time.perf_counter_ns())
    agg=aggregate(g,assessed,expected);run['aggregate_json']=agg
    write_json(folder/'aggregate.json',agg);times.append(time.perf_counter_ns())
    role_results={};candidate=None;candidate_valid=False
    if roles:
        previous={}
        for role in ROLES:
            system,user=g.role_prompt(role,run,previous)
            r=await call_node(g,p,folder,'role_'+role,ROLE_PROVIDER[role],system,user,call_transport)
            role_results[role]=r
            previous[role]={'artifact':r['artifact'],'valid_json':r['valid_json'],
              'deterministic_validation':{'valid':r['deterministic_validation']['valid']}}
        arbiter=role_results['arbiter']
        if arbiter['valid_json'] and arbiter['deterministic_validation']['valid']:
            candidate=arbiter['assessment'];candidate_valid=True
    else:
        candidate=without_roles(g,agg)
        candidate_valid=bool(agg['valid_provider_count']>=math.ceil(.75*len(expected)))
    times.append(time.perf_counter_ns())
    outcome=review_guard(g,candidate,agg);times.append(time.perf_counter_ns())
    nodes=list(assessed.values())+list(role_results.values())
    report={'schema':'tnsm.matched_trial.v1', **spec,'phase':protocol['phase'],'synthetic':protocol['synthetic'],
      'protocol_sha256':file_sha(folder.parent/'protocol.json'), 'created_at':utc(),
      'source_sha256':SOURCE_SHA,'planned_calls_attempted':len(nodes),
      'transport_complete':all(n['http_status']==200 for n in nodes),
      'response_redactions':sum(n['response_redacted'] for n in nodes),
      'valid_node_outputs':sum(n['valid_json'] and n['deterministic_validation']['valid'] for n in nodes),
      'valid_final_candidate':candidate_valid,'outcome':outcome,
      'timing_boundaries_ns':times,
      'stage_wall_ms':dict(zip(['assessment','aggregation','role_or_adapter','governance'],[(b-a)/1e6 for a,b in zip(times,times[1:])])),
      'decision_ready_wall_ms':(times[-1]-times[0])/1e6,
      'node_request_wall_sum_ms':sum(n['request_wall_ms'] for n in nodes),
      'token_usage_complete':all(n['input_tokens'] is not None and n['output_tokens'] is not None for n in nodes),
      'nodes':nodes}
    write_json(folder/'trial.json',report)
    return report


def seal(output):
    files=sorted(p for p in output.rglob('*') if p.is_file() and p!=output/'SHA256SUMS.txt')
    (output/'SHA256SUMS.txt').write_text(''.join(f'{file_sha(p)}  {p.relative_to(output).as_posix()}\n' for p in files))
def verify_seal(output):
    entries={}
    for line in (output/'SHA256SUMS.txt').read_text().splitlines():
        sha,name=line.split('  ',1);p=output/name
        if not p.resolve().is_relative_to(output.resolve()) or p.is_symlink() or name in entries or p==output/'SHA256SUMS.txt': raise ContractError('unsafe or duplicate manifest path')
        if file_sha(p)!=sha:raise ContractError('changed evidence: '+name)
        entries[name]=sha
    actual={p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file() and p!=output/'SHA256SUMS.txt'}
    if actual!=set(entries): raise ContractError('unbound evidence files')
    return len(entries)


async def execute(output, live=False):
    protocol=check_protocol(output);g=adapter()
    if protocol['synthetic'] == live: raise ContractError('live/synthetic mode mismatch')
    if (output/'attempts.jsonl').exists(): raise ContractError('execution already started; automatic resumption is intentionally disabled')
    indexed={r['cell_id']:r for r in rows()}
    transport_fn=transport if live else synthetic_transport
    try:
        for spec in protocol['trials']:
            append_json(output/'attempts.jsonl',{'trial_id':spec['trial_id'],'event':'started','at':utc()})
            try:
                result=await trial(g,protocol,indexed[spec['cell_id']],spec,output/spec['trial_id'],transport_fn)
                append_json(output/'attempts.jsonl',{'trial_id':spec['trial_id'],'event':'completed','at':utc()})
                print(canonical({'trial':spec['trial_id'],'ms':round(result['decision_ready_wall_ms'],2),'http_complete':result['transport_complete'],'valid_final_candidate':result['valid_final_candidate']}),flush=True)
            except BaseException as error:
                append_json(output/'attempts.jsonl',{'trial_id':spec['trial_id'],'event':'interrupted','error':redact(str(error)),'at':utc()})
                raise
            if live:await asyncio.sleep(protocol['inter_trial_pause_seconds'])
    finally:seal(output)


def main():
    ap=argparse.ArgumentParser(description=__doc__);sp=ap.add_subparsers(dest='command',required=True)
    sp.add_parser('preflight')
    f=sp.add_parser('freeze');f.add_argument('--output',type=Path,required=True);f.add_argument('--phase',choices=['pilot','full'],required=True)
    f.add_argument('--assessor-tokens',type=int,default=5000);f.add_argument('--role-tokens',type=int,default=4500);f.add_argument('--synthetic',action='store_true')
    r=sp.add_parser('run');r.add_argument('--output',type=Path,required=True);r.add_argument('--live',action='store_true')
    args=ap.parse_args()
    if args.command=='preflight':
        adapter();rows();e=environment();print(json.dumps({**e,'source_hash_matches':True,'input_hash_matches':True,'gateway_routes_invoked':0,'network_actions':0},indent=2))
    elif args.command=='freeze':
        p=freeze(args.output,args.phase,args.assessor_tokens,args.role_tokens,synthetic=args.synthetic)
        print(json.dumps({k:p[k] for k in ['phase','synthetic','trial_count','planned_provider_calls','maximum_requested_output_tokens_sum']},indent=2))
    else:asyncio.run(execute(args.output,args.live))

if __name__=='__main__':
    try:main()
    except (ContractError,FatalProviderError) as e:raise SystemExit(redact(str(e)))
