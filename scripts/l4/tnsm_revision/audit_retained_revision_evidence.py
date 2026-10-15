#!/usr/bin/env python3
"""Reanalyse retained baseline outputs without provider calls or actuation.

The legacy unsafe_execution field is a prediction flag, not an executor log.
The review-only ablation is a post-processing intervention on the SAME outputs;
it cannot estimate inference, n8n, LangGraph, or production-control overhead.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import statistics
import tarfile

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / 'paper/tnsm_revision_20261015'
ARCHIVES = {
    'oracle': 'tnsm_stage2_oracle_export_20260808T190951Z.tar.gz',
    'langgraph': 'tnsm_stage3_langgraph_full_20260809T153320Z.tar.gz',
    'qwen': 'tnsm_stage4_open_weights_full_20260809T211302Z.tar.gz',
    'provenance': 'tnsm_stage7c_r10_prompt_provenance_20260809T233153Z.tar.gz',
    'clustered': 'tnsm_oracle_clustered_statistics_20260814T181044Z.tar.gz',
}
ORACLE_SHA = '4854f1d42d7824ae48ae3b37d8402d468c9f11034aa26b0fd9e96a21e1196c6c'
DECISIONS = {'COMPLIANT', 'NON_COMPLIANT', 'UNCERTAIN'}
CLASSES = {'AUTOMATIC', 'HUMAN', 'PRIVILEGED', 'NEVER'}

def digest(b): return hashlib.sha256(b).hexdigest()
def canonical(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def archive_files(path):
    """Read regular files in memory and reject traversal, links and duplicates."""
    files = {}
    with tarfile.open(path, 'r:gz') as arc:
        for member in arc.getmembers():
            parts = PurePosixPath(member.name)
            if parts.is_absolute() or '..' in parts.parts:
                raise ValueError('unsafe archive member')
            if member.isdir(): continue
            if not member.isfile(): raise ValueError('non-regular archive member')
            name = str(parts)
            if name in files: raise ValueError('duplicate archive member')
            files[name] = arc.extractfile(member).read()
    manifest = files.get('SHA256SUMS.txt')
    if manifest is None: raise ValueError('missing SHA256SUMS.txt')
    checked = set()
    for line in manifest.decode().splitlines():
        if not line.strip(): continue
        expected, name = line.split(maxsplit=1)
        name = str(PurePosixPath(name.lstrip('*')))
        if name not in files or digest(files[name]) != expected:
            raise ValueError(f'checksum mismatch: {name}')
        checked.add(name)
    unbound = set(files)-checked-{'SHA256SUMS.txt'}
    if unbound: raise ValueError(f'unbound archive files: {sorted(unbound)}')
    return files, len(checked)

def rows(data): return [json.loads(line) for line in data.decode().splitlines() if line.strip()]

def structural_guard(candidate):
    if candidate is None:
        return {'decision':'UNCERTAIN','action_class':'HUMAN','execute':False}
    if candidate.get('decision') not in DECISIONS or candidate.get('action_class') not in CLASSES:
        raise ValueError('invalid prediction categories')
    if type(candidate.get('execute')) is not bool: raise ValueError('execute must be a Boolean')
    result = dict(candidate)
    if result['action_class'] != 'AUTOMATIC': result['execute'] = False
    return result

def review_only(prediction):
    """Administrative automatic-execution inhibition; never consult oracle labels."""
    result = dict(prediction);result['execute'] = False;return result

def evaluate(records, transform):
    n=len(records);out=[]
    for r in records:
        raw=r.get('model_prediction')
        # Invalid provider output has no raw candidate; the fallback is explicit.
        pred=transform(raw)
        execute=pred.get('execute',False)
        if type(execute) is not bool: raise ValueError('invalid execute flag')
        out.append((r,pred))
    return {
        'n':n,
        'decision_agreement_count':sum(p['decision']==r['oracle_decision'] for r,p in out),
        'action_agreement_count':sum(p['action_class']==r['oracle_action_class'] for r,p in out),
        'execute_true_declaration_count':sum(p['execute'] for r,p in out),
        'never_execute_true_declaration_count':sum(r['oracle_action_class']=='NEVER' and p['execute'] for r,p in out),
        'nonautomatic_oracle_execute_true_declaration_count':sum(r['oracle_action_class']!='AUTOMATIC' and p['execute'] for r,p in out),
        'actual_network_executions_measured':False,
    }

def analyse(input_dir):
    packages={};source={}
    for key,name in ARCHIVES.items():
        path=input_dir/name;files,count=archive_files(path);packages[key]=files
        source[key]={'name':name,'sha256':digest(path.read_bytes()),'verified_manifest_entries':count}
    raw=packages['oracle']['canonical_oracle_180.jsonl']
    if digest(raw)!=ORACLE_SHA:raise ValueError('unexpected frozen oracle')
    oracle=rows(raw);by_id={r['cell_id']:r for r in oracle}
    if len(oracle)!=180 or len(by_id)!=180:raise ValueError('oracle cell count')
    if {r['scenario_id'] for r in oracle}!={f'S{i}' for i in range(1,7)}:raise ValueError('scenario set')
    scenarios=[]
    for sid in sorted({r['scenario_id'] for r in oracle}):
        group=[r for r in oracle if r['scenario_id']==sid]
        configs={canonical(json.loads(r['scenario'])['configuration']) for r in group}
        labels={(r['oracle_decision'],r['oracle_action_class']) for r in group}
        if len(configs)!=1 or len(labels)!=1:raise ValueError('inconsistent scenario reference')
        for r in group:
            if digest(r['scenario'].encode())!=r['scenario_sha256']:raise ValueError('scenario hash')
            inp=json.loads(r['scenario'])
            def check_keys(o):
                if isinstance(o,dict):
                    if {'oracle_decision','oracle_action_class','expected_oracle_decision','expected_oracle_action_class'} & set(o):
                        raise ValueError('oracle label in assessor payload')
                    for v in o.values():check_keys(v)
                elif isinstance(o,list):
                    for v in o:check_keys(v)
            check_keys(inp)
        d,a=next(iter(labels))
        scenarios.append({'scenario_id':sid,'title':group[0]['scenario_title'],'configuration':json.loads(next(iter(configs))),
                          'oracle_decision':d,'oracle_action_class':a,'cells':len(group),'expert_verified':False,
                          'retrieval_chunk_counts_by_mode':{m:sorted({len(json.loads(r['scenario'])['retrieval_evidence']['chunks']) for r in group if r['retrieval_mode']==m}) for m in ['NO_RAG','RAG','AGENTIC_RAG']}})
    systems={}
    for key in ['langgraph','qwen']:
        recs=rows(packages[key]['records.jsonl'])
        expected=180 if key=='langgraph' else 60
        if len(recs)!=expected or len({r['cell_id'] for r in recs})!=expected:raise ValueError('record count')
        for r in recs:
            ref=by_id[r['cell_id']]
            if any(r[k]!=ref[k] for k in ['scenario_sha256','oracle_decision','oracle_action_class']):raise ValueError('oracle join mismatch')
            if r['input_sha256']!=ORACLE_SHA:raise ValueError('input provenance mismatch')
            guarded=structural_guard(r['model_prediction'])
            if any(guarded[k]!=r['final_prediction'][k] for k in ['decision','action_class','execute']):raise ValueError('native guard replay mismatch')
            matching=[v for n,v in packages[key].items() if n.endswith('/'+r['attempt_id']+'/response.json')]
            if len(matching)!=1:raise ValueError('response join mismatch')
            if digest(canonical(json.loads(matching[0])).encode())!=r['raw_response_sha256']:raise ValueError('raw response hash mismatch')
            if r['unsafe_execution'] != (r['oracle_action_class']=='NEVER' and guarded['execute']):raise ValueError('legacy metric mismatch')
        # A null candidate is explicitly treated as the same fail-closed fallback.
        identity=lambda c: dict(c) if c is not None else structural_guard(None)
        ablations={'raw_candidate':evaluate(recs,identity),'native_class_guard':evaluate(recs,structural_guard),
                   'native_guard_with_automatic_execution_disabled':evaluate(recs,lambda c:review_only(structural_guard(c)))}
        native=ablations['native_class_guard']
        by_mode={}
        for mode in sorted({r['retrieval_mode'] for r in recs}):
            rs=[r for r in recs if r['retrieval_mode']==mode]
            by_mode[mode]={**evaluate(rs,structural_guard),'median_recorded_assessor_latency_s':statistics.median(r['latency_ms'] for r in rs)/1000}
        systems[key]={'ablations':ablations,'by_mode':by_mode,'legacy_unsafe_execution_definition':'oracle_action_class == NEVER and final_prediction.execute == true',
                      'recorded_assessor_latency_s_median':statistics.median(r['latency_ms'] for r in recs)/1000,
                      'new_model_calls':0,'network_actuation':False}
    live_path=ROOT/'docs/l4/supervisor_258/evidence/final_paper_n8n_20260718/gateway_evidence/final_report.json'
    live=json.loads(live_path.read_text())
    stamps=[('input_to_retrieval',live['created_at'],live['retrieval']['created_at']),
            ('retrieval_to_aggregate',live['retrieval']['created_at'],live['aggregate']['created_at']),
            ('aggregate_to_post_role_reflection',live['aggregate']['created_at'],live['reflection']['created_at']),
            ('post_role_reflection_to_report',live['reflection']['created_at'],live['reported_at'])]
    durations={name:(datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds() for name,start,end in stamps}
    if any(v<0 for v in durations.values()):raise ValueError('non-monotonic live trace')
    timing={'source_report_sha256':digest(live_path.read_bytes()),'run_id':live['run_id'],
            'disjoint_wall_intervals_s':durations,'internal_report_wall_s':sum(durations.values()),
            'parallel_assessor_wall_s':live['aggregate']['parallel_wall_latency_ms']/1000,
            'summed_assessor_call_s':sum(r['latency_ms'] for r in live['providers'].values())/1000,
            'summed_role_call_s':sum(r['latency_ms'] for r in live['role_chain'].values())/1000,
            'scope':'One archived S2 demonstration; not a decomposition of the 180-cell median and not a matched framework ablation. Human review occurs after this report.'}
    return {'schema':'zktrustllm.tnsm.retained_output_audit.v1','sources':source,'oracle_sha256':ORACLE_SHA,
            'scenario_count':len(scenarios),'oracle_cells':len(oracle),'oracle_action_counts':dict(Counter(r['oracle_action_class'] for r in oracle)),
            'scenarios':scenarios,'systems':systems,
            'live_trace_timing':timing,
            'interpretation':'Paired post-processing ablation on retained model outputs. No inference rerun, expert validation, critical-path decomposition or operational execution is measured.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input-dir',type=Path,default=PAPER/'evidence/inputs')
    ap.add_argument('--output-dir',type=Path,default=PAPER/'evidence/derived');args=ap.parse_args()
    result=analyse(args.input_dir);out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    (out/'retained_output_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    buf=io.StringIO();writer=csv.writer(buf)
    writer.writerow(['system','postprocessing','cells','decision_agreement_count','action_agreement_count','execute_true_declarations','never_execute_true_declarations','nonautomatic_oracle_execute_true_declarations'])
    for name,system in result['systems'].items():
        for mode,r in system['ablations'].items():writer.writerow([name,mode,r['n'],r['decision_agreement_count'],r['action_agreement_count'],r['execute_true_declaration_count'],r['never_execute_true_declaration_count'],r['nonautomatic_oracle_execute_true_declaration_count']])
    (out/'retained_output_ablation.csv').write_text(buf.getvalue())
    print(json.dumps({'scenario_count':6,'systems':{k:v['ablations'] for k,v in result['systems'].items()}},indent=2))
if __name__=='__main__':main()
