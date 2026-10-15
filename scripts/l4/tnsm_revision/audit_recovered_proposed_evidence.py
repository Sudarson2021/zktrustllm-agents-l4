#!/usr/bin/env python3
"""Verify the recovered R10 reports and reanalyse their recorded outcomes.

No provider calls, actuation or changes to historical files are performed.
Archive members are read in memory. Historical absolute manifest paths are
mapped only through the explicit experiment-root prefix, never opened on disk.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import statistics
import sys
import tarfile

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from export_frozen_oracle import filtered_chunks, filtered_query
from analyze_oracle_clustered import summarize_mode, BOOTSTRAP_SEED

ROOT = HERE.parents[2]
PAPER = ROOT / 'paper/tnsm_revision_20261015'
EXPERIMENT = 'l4_oracle_20260716T131803Z_r10'
BUNDLE_NAME = 'TNSM_12002_Original_Evidence_Recovery.tar.gz'
BUNDLE_SHA256 = 'f842c0308d6e52904de71bb8886a044d733d474dde688ac906fbab0277ccb63d'
MODES = ('NO_RAG', 'RAG', 'AGENTIC_RAG')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def read_archive(data):
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            require(not path.is_absolute() and '..' not in path.parts, 'unsafe archive path')
            if member.isdir():
                continue
            require(member.isfile(), 'non-regular archive member')
            name = str(path)
            require(name not in files, 'duplicate archive member')
            require(member.size <= 16 * 1024 * 1024, 'oversized archive member')
            files[name] = archive.extractfile(member).read()
    return files


def verify_manifest(files, manifest_name, root='', absolute_prefix=None):
    checked = set()
    for line in files[manifest_name].decode().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.lstrip('*')
        if absolute_prefix and name.startswith(absolute_prefix):
            name = name[len(absolute_prefix):]
        path = PurePosixPath(name)
        require(not path.is_absolute() and '..' not in path.parts, 'unsafe manifest target')
        target = str(PurePosixPath(root) / path)
        require(target not in checked, 'duplicate manifest target')
        require(target in files and sha(files[target]) == digest, 'checksum mismatch: ' + target)
        checked.add(target)
    return checked


def csv_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode())))


def percentile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def timing_intervals(report, external_seconds):
    timestamps = [report['created_at'], report['retrieval']['created_at'],
                  report['aggregate']['created_at'], report['reflection']['created_at'],
                  report['reported_at']]
    times = [datetime.fromisoformat(value) for value in timestamps]
    intervals = [(end-start).total_seconds() for start, end in zip(times, times[1:])]
    require(min(intervals) >= 0, 'non-monotonic stage timestamps')
    internal = (times[-1]-times[0]).total_seconds()
    require(abs(sum(intervals)-internal) < 1e-8, 'stage interval sum')
    require(external_seconds >= internal, 'index duration shorter than report duration')
    assessor_durations = [x['latency_ms'] for x in report['providers'].values()]
    role_durations = [x['latency_ms'] for x in report['role_chain'].values()]
    return dict(zip(('input_to_retrieval_s', 'retrieval_to_aggregate_s',
                     'aggregate_to_post_role_reflection_s', 'post_role_reflection_to_report_s'), intervals)) | {
        'index_wall_s': external_seconds, 'internal_report_wall_s': internal,
        'index_minus_internal_s': external_seconds-internal,
        'parallel_assessor_wall_s': report['aggregate']['parallel_wall_latency_ms']/1000,
        'summed_assessor_call_s': sum(assessor_durations)/1000 if all(x is not None for x in assessor_durations) else None,
        'summed_role_call_s': sum(role_durations)/1000 if all(x is not None for x in role_durations) else None,
        'role_phase_fraction_of_internal': intervals[2]/internal,
    }


def analyse(bundle, oracle, retained_summary, prompt_provenance):
    data = bundle.read_bytes()
    require(sha(data) == BUNDLE_SHA256, 'recovery bundle digest differs from user-recorded SHA-256')
    outer = read_archive(data)
    require(len(outer) == 9, 'recovery bundle file inventory')
    release = EXPERIMENT + '_RELEASE_SHA256SUMS.txt'
    checked_release = verify_manifest(outer, release)
    nested = {}
    for part in ('successful_evidence', 'portable_analysis_v2', 'final_analysis'):
        name = EXPERIMENT + '_' + part + '.tar.gz'
        sidecar = name + '.sha256'
        lines = outer[sidecar].decode().splitlines()
        require(len(lines) == 1, 'unexpected sidecar inventory')
        digest, target = lines[0].split(maxsplit=1)
        require(PurePosixPath(target.lstrip('*')).name == name, 'sidecar filename mismatch')
        require(sha(outer[name]) == digest, 'archive sidecar mismatch')
        nested[part] = read_archive(outer[name])
    evidence = nested['successful_evidence']
    portable_root = EXPERIMENT + '_portable_analysis_v2/'
    portable = {name.removeprefix(portable_root): value for name, value in nested['portable_analysis_v2'].items()}
    bound_portable = verify_manifest(portable, 'PORTABLE_SHA256SUMS.txt')
    require(set(portable)-bound_portable == {'PORTABLE_SHA256SUMS.txt'}, 'unbound portable files')
    expected_absolute = '/home/sk02352/Downloads/deploy/n8n_l4_parallel/runtime/experiments/' + EXPERIMENT + '/'
    final = nested['final_analysis']
    # FINAL_BENCHMARK's script paths refer to the separately packaged scripts.
    benchmark_files = {name.removeprefix('experiment/'): value for name, value in portable.items()}
    bound_analysis = verify_manifest(benchmark_files, 'analysis_oracle_final/ANALYSIS_SHA256SUMS.txt', absolute_prefix=expected_absolute)
    bound_benchmark = verify_manifest(benchmark_files, 'FINAL_BENCHMARK_SHA256SUMS.txt', absolute_prefix=expected_absolute)
    for name, value in final.items():
        portable_name = 'experiment/' + name
        require(portable_name in portable, 'unbound final-analysis file: ' + name)
        require(value == portable[portable_name], 'analysis archives disagree: ' + name)

    bound_runs = set()
    manifests = [name for name in evidence if name.endswith('/SHA256SUMS.txt')]
    require(len(manifests) == 180, 'run manifest count')
    for manifest in manifests:
        root = str(PurePosixPath(manifest).parent)
        checked = verify_manifest(evidence, manifest, root)
        require(len(checked) == 18, 'per-run manifest inventory')
        bound_runs.update(checked)
    require(set(evidence)-bound_runs == set(manifests), 'unbound run evidence')
    listed = {str(PurePosixPath(line)) for line in outer[EXPERIMENT+'_successful_evidence.list'].decode().splitlines() if line.strip()}
    require({str(PurePosixPath(name).parent) for name in manifests} == listed, 'evidence-list/run mismatch')

    index = csv_rows(portable['experiment/run_index_success_matrix.csv'])
    archived_metrics = {row['run_id']: row for row in csv_rows(portable['experiment/analysis_oracle_final/run_metrics.csv'])}
    frozen = {row['cell_id']: row for row in oracle}
    provenance = {row['cell_id']: row for row in prompt_provenance}
    require(len(index) == len(archived_metrics) == len(frozen) == len(provenance) == 180, 'population count')
    seen_cells, seen_runs = set(), set()
    records, cells = [], []
    hash_checks = Counter()
    for row in index:
        sid, mode, repeat, run_id = row['scenario_id'], row['retrieval_mode'], int(row['repeat']), row['run_id']
        cell_id = f'{sid}:{mode}:R{repeat:02d}'
        require(cell_id not in seen_cells and run_id not in seen_runs, 'duplicate cell or run')
        seen_cells.add(cell_id); seen_runs.add(run_id)
        ref = frozen[cell_id]
        root = 'runtime/evidence/' + run_id
        report = json.loads(evidence[root+'/final_report.json'])
        metadata = report['metadata']
        require(sha(canonical({k:v for k,v in report.items() if k != 'report_hash'})) == report['report_hash'], 'canonical report hash')
        require(report['report_hash'] == row['report_hash'] == ref['source_report_hash'], 'released oracle/report hash join')
        require(run_id == report['run_id'] == ref['source_run_id'], 'released oracle/run join')
        require(metadata['experiment_id'] == EXPERIMENT, 'experiment identity')
        require((metadata['scenario_id'], metadata['retrieval_mode'], int(metadata['repeat'])) == (sid, mode, repeat), 'metadata cell join')
        require(row['status'] == 'SUCCESS' and report['execution_mode'] == 'LIVE', 'run status')
        require(metadata['expert_verified'] is False, 'unexpected expert-verification claim')
        for column, key in [('ground_truth_decision','oracle_decision'), ('ground_truth_action_class','oracle_action_class')]:
            require(row[column] == metadata[column] == ref[key], 'frozen label join')
        retrieval = report['retrieval']
        require(json.loads(evidence[root+'/retrieval_bundle.json']) == retrieval, 'retrieval file/report mismatch')
        require(retrieval['bundle_hash'] == ref['source_retrieval_bundle_hash'], 'released retrieval hash join')
        exported_input = json.loads(ref['scenario'])
        require(exported_input['retrieval_evidence']['chunks'] == filtered_chunks(retrieval['chunks']), 'released retrieval content mismatch')
        query = {} if mode == 'NO_RAG' else filtered_query(retrieval.get('query') or report['query'])
        require(exported_input['retrieval_evidence']['query'] == query, 'released retrieval query mismatch')
        for component, field in [('retrieval','bundle_hash'), ('aggregate','aggregate_hash'),
                                 ('reflection','reflection_hash'), ('policy','policy_hash'),
                                 ('verification','verification_hash'), ('anchor','anchor_hash')]:
            value = report[component]
            require(sha(canonical({k:v for k,v in value.items() if k != field})) == value[field], 'component self-hash: '+component)
            hash_checks[component+'_canonical_hashes'] += 1
        hash_checks['report_canonical_hashes_and_released_oracle_joins'] += 1
        provider_valid = role_valid = 0
        for family, section in [('providers','providers'), ('roles','role_chain')]:
            require(len(report[section]) == 4, 'provider/role inventory')
            for name, result in report[section].items():
                result_path = root+'/'+family+'/'+name+'/result.json'
                require(json.loads(evidence[result_path]) == result, 'embedded result mismatch')
                require(sha(evidence[root+'/'+family+'/'+name+'/raw_response.txt']) == result['raw_response_hash'], 'raw response hash')
                hash_checks[family+'_raw_response_hashes'] += 1
                field = 'assessment' if family == 'providers' else 'artifact'
                if result.get('parsed_response_hash'):
                    require(sha(canonical(result[field])) == result['parsed_response_hash'], 'parsed response hash')
                    hash_checks[family+'_parsed_response_hashes'] += 1
                valid = result['valid_json'] is True and result['deterministic_validation']['valid'] is True
                if family == 'providers':
                    provider_valid += valid and result['provider_call_succeeded'] is True
                    require(result['prompt_hash'] == provenance[cell_id]['retained_prompt_hash'], 'retained prompt provenance join')
                    require(report['input_hash'] == metadata['config_sha256'] == provenance[cell_id]['input_hash'], 'retained input-hash join')
                else:
                    role_valid += valid
        decision, action = report['reflection']['final_decision'], report['policy']['enforced_action_class']
        require(decision == report['policy']['decision'], 'reflection/policy decision mismatch')
        automatic = report['policy']['automatic_execution_enabled']
        require(type(automatic) is bool, 'execution flag type')
        timing = timing_intervals(report, float(row['wall_clock_sec']))
        record = {'cell_id':cell_id, 'scenario_id':sid, 'retrieval_mode':mode, 'repeat':repeat,
                  'run_id':run_id, 'report_hash':report['report_hash'], 'decision':decision, 'action':action,
                  'oracle_decision':ref['oracle_decision'], 'oracle_action':ref['oracle_action_class'],
                  'automatic_execution_enabled':automatic, 'provider_valid_count':provider_valid,
                  'role_valid_count':role_valid, **timing}
        archived = archived_metrics[run_id]
        for key, actual in [('final_decision', decision), ('enforced_action_class', action),
                            ('provider_valid_count',str(provider_valid)), ('role_valid_count',str(role_valid))]:
            require(archived[key] == actual, 'archived run metric differs: '+key)
        require(float(archived['wall_clock_sec']) == timing['index_wall_s'], 'archived wall duration differs')
        records.append(record); cells.append(cell_id)
    require(seen_cells == set(frozen), 'incomplete cell coverage')
    require({str(PurePosixPath(name).parent).split('/')[-1] for name in manifests} == seen_runs, 'orphan evidence run')
    by_mode = {}
    for index, mode in enumerate(MODES):
        group = [row for row in records if row['retrieval_mode'] == mode]
        clustered = summarize_mode(mode, group, BOOTSTRAP_SEED + 10*index)
        require(clustered == retained_summary['by_mode'][mode], 'raw report/retained clustered summary mismatch')
        reference_never = [row for row in group if row['oracle_action'] == 'NEVER']
        timings = {}
        for key in timing:
            available = [row[key] for row in group if row[key] is not None]
            timings[key] = {'n':len(available), 'median':statistics.median(available) if available else None,
                            'p95':percentile(available, .95) if available else None}
        by_mode[mode] = {'cells':len(group), 'decision_agreement_count':sum(row['decision']==row['oracle_decision'] for row in group),
                         'action_agreement_count':sum(row['action']==row['oracle_action'] for row in group),
                         'never_reference_count':len(reference_never), 'never_class_correct_count':sum(row['action']=='NEVER' for row in reference_never),
                         'coverage_count':sum(row['decision']!='UNCERTAIN' for row in group),
                         'automatic_execution_enabled_count':sum(row['automatic_execution_enabled'] for row in group),
                         'provider_valid_count':sum(row['provider_valid_count'] for row in group), 'provider_records':240,
                         'role_valid_count':sum(row['role_valid_count'] for row in group), 'role_records':240,
                         'clustered_metrics':clustered['metrics'], 'timing_s':timings}
    return {'schema':'zktrustllm.tnsm.recovered_proposed_audit.v1', 'experiment_id':EXPERIMENT,
            'recovery_bundle_sha256':sha(data), 'bundle_bytes':len(data), 'outer_files':len(outer),
            'release_manifest_entries_verified':len(checked_release),
            'portable_manifest_entries_verified':len(bound_portable), 'final_analysis_manifest_entries_verified':len(bound_analysis),
            'benchmark_manifest_entries_verified':len(bound_benchmark), 'evidence_files':len(evidence),
            'run_manifests':len(manifests), 'run_manifest_entries_verified':len(bound_runs),
            'successful_cells':len(records), 'distinct_run_ids':len(seen_runs), 'hash_checks':dict(hash_checks),
            'raw_metrics_and_clustered_intervals_match_retained_summary':True, 'by_mode':by_mode, 'cells':records,
            'scope':'Internal integrity and deterministic reanalysis of retained LIVE-labelled records; not independent provider authentication, expert validation, new inference, matched framework overhead or O-RAN deployment validation.',
            'timing_scope':'Disjoint report-timestamp intervals for all 180 successful cells; indexed end-to-end duration is a separate recorded timer. Marginal stage medians do not sum to the median total. Parallel provider durations overlap.',
            'provider_calls_made':0, 'network_actuation':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=PAPER/'evidence/inputs'/BUNDLE_NAME)
    parser.add_argument('--output-dir', type=Path, default=PAPER/'evidence/derived')
    args = parser.parse_args()
    # The companion audit verifies the five previously retained input manifests.
    from audit_retained_revision_evidence import archive_files, ARCHIVES
    inputs = PAPER/'evidence/inputs'
    packages = {key:archive_files(inputs/name)[0] for key,name in ARCHIVES.items()}
    oracle = [json.loads(line) for line in packages['oracle']['canonical_oracle_180.jsonl'].decode().splitlines()]
    summary = json.loads(packages['clustered']['oracle_clustered_statistics.json'])
    provenance = [json.loads(line) for line in packages['provenance']['r10_prompt_reconstruction.jsonl'].decode().splitlines()]
    report = analyse(args.bundle, oracle, summary, provenance)
    args.output_dir.mkdir(exist_ok=True, parents=True)
    (args.output_dir/'recovered_proposed_audit.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    with (args.output_dir/'recovered_proposed_cells.csv').open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=list(report['cells'][0]), lineterminator='\n');writer.writeheader();writer.writerows(report['cells'])
    with (args.output_dir/'recovered_proposed_timing.csv').open('w', newline='') as output:
        writer = csv.writer(output, lineterminator='\n');writer.writerow(['retrieval_mode','interval','n','median','p95'])
        for mode in MODES:
            for interval, values in report['by_mode'][mode]['timing_s'].items():
                writer.writerow([mode,interval,values['n'],values['median'],values['p95']])
    print(json.dumps({key:value for key,value in report.items() if key not in {'cells','by_mode'}},indent=2))


if __name__ == '__main__':
    main()
