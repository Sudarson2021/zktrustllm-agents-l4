#!/usr/bin/env python3
"""Offline, independently computed audit of the fixed 16 October 2026 study.

Never imports the frozen runner, calls providers, or changes the input archive.
The separately rerun frozen analyzer checks prompt reconstruction and parsing.
This audit independently checks the archive, manifests, treatment matching,
scoring, quantiles, paired contrasts, bootstrap intervals, and response metadata.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import statistics
import tarfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / 'paper/tnsm_revision_20261015'
ARCHIVE_SHA = '7ea6792f45aa6663e98869e81626f69bb37c58c1c4de161691545c70780bdd95'
PROTOCOL_SHA = '5e501822578b8c87537110d8e5d6ce22fc1d904a6f631721cc82d1b628cbba6e'
VARIANTS = ['A_ONE_NO_ROLES', 'B_FOUR_NO_ROLES', 'C_ONE_ROLES', 'D_FOUR_ROLES']
CONTRASTS = [
    ('added_assessors_roles_off', (0, 1, 0, 0), (-1, 0, 0, 0)),
    ('added_assessors_roles_on', (0, 0, 0, 1), (0, 0, -1, 0)),
    ('role_chain_one_assessor', (0, 0, 1, 0), (-1, 0, 0, 0)),
    ('role_chain_four_assessors', (0, 0, 0, 1), (0, -1, 0, 0)),
    ('interaction', (1, 0, 0, 1), (0, -1, -1, 0)),
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def quantile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    left = math.floor(position)
    right = math.ceil(position)
    return ordered[left] + (ordered[right] - ordered[left]) * (position - left)


def flat_tokens(value, prefix=''):
    result = {}
    if isinstance(value, dict):
        for key, item in value.items():
            name = f'{prefix}.{key}' if prefix else key
            if isinstance(item, dict):
                result.update(flat_tokens(item, name))
            elif type(item) is int and key.endswith('tokens'):
                result[name] = item
    return result


def audit(archive):
    raw = archive.read_bytes()
    require(sha(raw) == ARCHIVE_SHA, 'Uploaded archive identity changed')
    files = {}
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as tar:
        members = tar.getmembers()
        require(len(members) < 20000 and sum(m.size for m in members) < 300_000_000, 'Archive bounds exceeded')
        for member in members:
            path = PurePosixPath(member.name)
            require(not path.is_absolute() and '..' not in path.parts, 'Unsafe archive path')
            require(member.isfile() or member.isdir(), 'Links and special archive members are disallowed')
            require(member.name not in seen, 'Duplicate archive member')
            seen.add(member.name)
            if member.isfile():
                files[member.name] = tar.extractfile(member).read()
    read = lambda name: json.loads(files[name])
    manifest_counts = {}
    for name in ['pilot_01', 'pilot_02', 'full_01']:
        manifest = {}
        for line in files[f'{name}/SHA256SUMS.txt'].decode().splitlines():
            digest, relative = line.split('  ', 1)
            path = PurePosixPath(relative)
            require(not path.is_absolute() and '..' not in path.parts, 'Unsafe manifest path')
            require(relative not in manifest and relative != 'SHA256SUMS.txt', 'Duplicate/self manifest entry')
            require(sha(files[f'{name}/{relative}']) == digest, 'Bound evidence changed')
            manifest[relative] = digest
        actual = {p[len(name) + 1:] for p in files if p.startswith(name + '/') and p != f'{name}/SHA256SUMS.txt'}
        require(actual == set(manifest), 'Unbound study files')
        manifest_counts[name] = len(manifest)
    prefix = 'scripts/l4/tnsm_revision/matched_ablation/'
    protocol = read('full_01/protocol.json')
    pilot = read('pilot_02/protocol.json')
    require(sha(files['full_01/protocol.json']) == PROTOCOL_SHA, 'Frozen full protocol changed')
    require(files['full_01/PROTOCOL_SHA256.txt'].decode().strip() == PROTOCOL_SHA, 'Protocol sidecar mismatch')
    require(protocol['phase'] == 'full' and protocol['synthetic'] is False, 'Not the full live-API study')
    for key in ['environment', 'assessor_tokens', 'role_tokens', 'source_sha256', 'input_sha256', 'harness_sha256']:
        require(protocol[key] == pilot[key], 'Full/pilot contract mismatch: ' + key)
    for name, digest in protocol['harness_sha256'].items():
        require(sha(files[prefix + name]) == digest, 'Packaged harness hash mismatch')
    require(sha(files[prefix + 'gateway_reference.py.txt']) == protocol['source_sha256'], 'Reference source hash mismatch')
    require(sha(files[prefix + 'canonical_oracle_180.jsonl']) == protocol['input_sha256'], 'Oracle input hash mismatch')
    references = {r['cell_id']: r for r in map(json.loads, files[prefix + 'canonical_oracle_180.jsonl'].decode().splitlines())}
    frozen = read('full_01_analysis/analysis.json')
    trials, nodes, issues, truncated, fallback_nodes = [], [], [], [], []
    providers = defaultdict(list)
    blocks = defaultdict(dict)
    identifiers = defaultdict(list)
    all_final_valid = set()
    all_node_valid = set()
    strict_valid = set()
    raw_hashes_checked = 0
    for spec in protocol['trials']:
        directory = 'full_01/' + spec['trial_id'] + '/'
        trial = read(directory + 'trial.json')
        require(all(trial[k] == v for k, v in spec.items()), 'Trial identity mismatch')
        require(trial['protocol_sha256'] == PROTOCOL_SHA, 'Trial protocol mismatch')
        require(trial['outcome']['execute'] is False and trial['outcome']['network_actions'] == 0, 'Execution was not disabled')
        require(trial['outcome']['enforced_action_class'] in {'HUMAN', 'NEVER'}, 'Unexpected review-only route')
        ticks = trial['timing_boundaries_ns']
        require(len(ticks) == 5 and all(b >= a for a, b in zip(ticks, ticks[1:])), 'Invalid disjoint timer')
        require(abs(trial['decision_ready_wall_ms'] - (ticks[-1] - ticks[0]) / 1e6) < 1e-6, 'Wall timer mismatch')
        require(abs(sum(trial['stage_wall_ms'].values()) - trial['decision_ready_wall_ms']) < 1e-6, 'Overlapping/missing stages')
        ref = references[trial['cell_id']]
        counts = {'decision': trial['outcome']['decision'] == ref['oracle_decision'],
                  'pre': trial['outcome']['reconciliation']['reconciled_action_class'] == ref['oracle_action_class'],
                  'action': trial['outcome']['enforced_action_class'] == ref['oracle_action_class']}
        trial['_scoring'] = counts
        trial['_oracle'] = {k: ref[k] for k in ['oracle_decision', 'oracle_action_class']}
        trial['_seconds'] = (ticks[-1] - ticks[0]) / 1e9
        trial_nodes = []
        for name in sorted(p for p in files if p.startswith(directory) and p.endswith('_result.json')):
            result = read(name)
            wire = read(name.replace('_result.json', '_wire.json'))
            request = read(name.replace('_result.json', '_request.json'))
            require(sha(wire['body'].encode()) == wire['retained_response_sha256'], 'Retained response digest mismatch')
            require(not wire['redacted'] and wire['raw_response_sha256'] == wire['retained_response_sha256'], 'Response redaction/unverifiable hash')
            require(result['raw_response_sha256'] == wire['raw_response_sha256'], 'Result/wire hash mismatch')
            require(result['http_status'] == wire['status'], 'HTTP metadata mismatch')
            raw_hashes_checked += 1
            body = json.loads(wire['body'])
            choice = (body.get('choices') or [{}])[0]
            message = choice.get('message') or {}
            stop = body.get('stop_reason') or body.get('status') or choice.get('finish_reason')
            provider = result['provider']
            valid = bool(result['valid_json'] and result['deterministic_validation']['valid'])
            fallback = provider == 'deepseek' and not bool((message.get('content') or '').strip()) and bool((message.get('reasoning_content') or '').strip())
            node = {'trial': trial['trial_id'], 'variant': trial['variant'], 'scenario_id': trial['scenario_id'],
                    'node': PurePosixPath(name).name.removesuffix('_result.json'), 'provider': provider,
                    'http_status': result['http_status'], 'stop_reason': stop,
                    'schema_valid': result['valid_json'], 'reference_checks_valid': result['deterministic_validation']['valid'],
                    'valid': valid, 'reasoning_channel_fallback': fallback,
                    'returned_model': result['returned_model'], 'requested_model': request['model'],
                    'system_fingerprint': result.get('system_fingerprint'), 'usage': body.get('usage'),
                    'service_tier': body.get('service_tier') or (body.get('usage') or {}).get('service_tier'),
                    'request_wall_ms': result['request_wall_ms']}
            identifiers[provider].append(body.get('id'))
            if stop == 'refusal': category = 'provider_refusal'
            elif result['http_status'] != 200: category = 'transport_failure'
            elif not result['valid_json']: category = 'schema_or_json_failure'
            elif not result['deterministic_validation']['valid']: category = 'reference_check_failure'
            else: category = None
            if category:
                issues.append({**{k: node[k] for k in ['trial', 'variant', 'scenario_id', 'node', 'provider', 'http_status', 'stop_reason']},
                               'category': category, 'reference_errors': result['deterministic_validation'].get('errors', []),
                               'transport_error': body.get('transport_error')})
            if stop == 'length': truncated.append({k: node[k] for k in ['trial', 'node', 'provider', 'valid', 'reasoning_channel_fallback']})
            if fallback: fallback_nodes.append({k: node[k] for k in ['trial', 'node', 'provider', 'valid', 'stop_reason']})
            nodes.append(node); providers[provider].append(node); trial_nodes.append(node)
        require(len(trial_nodes) == trial['planned_calls_attempted'], 'Trial node count mismatch')
        require(sum(n['valid'] for n in trial_nodes) == trial['valid_node_outputs'], 'Trial validity count mismatch')
        trial['_nodes'] = trial_nodes
        blocks[trial['block']][trial['variant']] = trial
        trials.append(trial)
    require(len(trials) == 240 and len(nodes) == 1080 and len(blocks) == 60, 'Wrong study population')
    require(Counter(t['variant'] for t in trials) == Counter({v: 60 for v in VARIANTS}), 'Condition imbalance')
    require(Counter(t['scenario_id'] for t in trials) == Counter({f'S{i}': 40 for i in range(1, 7)}), 'Scenario imbalance')
    for v in VARIANTS:
        require(Counter(t['position'] for t in trials if t['variant'] == v) == Counter({i: 15 for i in range(1, 5)}), 'Position imbalance')
    for block, values in blocks.items():
        require(set(values) == set(VARIANTS), 'Incomplete matched block')
        require(len({t['input_side_sha256'] for t in values.values()}) == 1, 'Unmatched input-side payload')
        bodies = [read('full_01/' + values[v]['trial_id'] + '/assessor_openai_request.json') for v in VARIANTS]
        require(all(x == bodies[0] for x in bodies), 'Shared OpenAI assessor prompt/body mismatch')
        for p in ['anthropic', 'deepseek', 'mistral']:
            left = read('full_01/' + values[VARIANTS[1]]['trial_id'] + f'/assessor_{p}_request.json')
            right = read('full_01/' + values[VARIANTS[3]]['trial_id'] + f'/assessor_{p}_request.json')
            require(left == right, 'Shared four-assessor request mismatch')
        if all(t['valid_final_candidate'] for t in values.values()): all_final_valid.add(block)
        if all(n['valid'] for t in values.values() for n in t['_nodes']): all_node_valid.add(block)
        if all(n['valid'] and n['stop_reason'] not in {'length', 'refusal'} and not n['reasoning_channel_fallback'] for t in values.values() for n in t['_nodes']): strict_valid.add(block)
    summaries = {}
    for variant in VARIANTS:
        selected = [t for t in trials if t['variant'] == variant]
        seconds = [t['_seconds'] for t in selected]
        summary = {'n': len(selected), 'decision_agreement_count': sum(t['_scoring']['decision'] for t in selected),
                   'pre_review_reconciled_action_agreement_count': sum(t['_scoring']['pre'] for t in selected),
                   'enforced_action_agreement_count': sum(t['_scoring']['action'] for t in selected),
                   'oracle_never_denominator': sum(t['_oracle']['oracle_action_class'] == 'NEVER' for t in selected),
                   'oracle_never_hits': sum(t['_oracle']['oracle_action_class'] == 'NEVER' and t['outcome']['enforced_action_class'] == 'NEVER' for t in selected),
                   'false_never_count': sum(t['_oracle']['oracle_action_class'] != 'NEVER' and t['outcome']['enforced_action_class'] == 'NEVER' for t in selected),
                   'valid_final_candidates': sum(t['valid_final_candidate'] for t in selected),
                   'http_complete_trials': sum(t['transport_complete'] for t in selected),
                   'median_seconds': statistics.median(seconds), 'p95_seconds': quantile(seconds, .95),
                   'mean_stage_seconds': {stage: statistics.mean(t['stage_wall_ms'][stage] / 1000 for t in selected) for stage in selected[0]['stage_wall_ms']},
                   'valid_nodes': sum(t['valid_node_outputs'] for t in selected),
                   'planned_nodes': sum(t['planned_calls_attempted'] for t in selected),
                   'decision_confusion': dict(Counter(t['_oracle']['oracle_decision'] + ' -> ' + t['outcome']['decision'] for t in selected)),
                   'scenario_decision_agreement': {scenario: sum(t['_scoring']['decision'] for t in selected if t['scenario_id'] == scenario) for scenario in sorted({t['scenario_id'] for t in selected})}}
        for key, value in summary.items():
            if key not in frozen['variants'][variant]: continue
            observed = frozen['variants'][variant][key]
            require(abs(value - observed) < 1e-9 if isinstance(value, float) else value == observed, 'Independent summary mismatch: ' + key)
        summaries[variant] = summary
    primary = {b: ts for b, ts in blocks.items() if all(t['transport_complete'] for t in ts.values())}
    excluded = sorted(set(blocks) - set(primary))
    require(excluded == [7] == frozen['excluded_from_primary_http_complete_block_effects'], 'Wrong primary exclusion')
    rng = random.Random(20261016)
    contrasts = {}
    for name, positive, negative in CONTRASTS:
        weights = [a + b for a, b in zip(positive, negative)]
        def effects(blockset):
            return [sum(w * ts[v]['_seconds'] for w, v in zip(weights, VARIANTS)) for ts in blockset.values()]
        values = effects(primary)
        mean = statistics.mean(values)
        clusters = defaultdict(list)
        for b, ts in primary.items():
            clusters[next(iter(ts.values()))['scenario_id']].append(sum(w * ts[v]['_seconds'] for w, v in zip(weights, VARIANTS)))
        cluster_ids = sorted(clusters)
        sums = {k: sum(v) for k, v in clusters.items()}
        counts = {k: len(v) for k, v in clusters.items()}
        draws = []
        for _ in range(20000):
            selected = rng.choices(cluster_ids, k=6)
            draws.append(sum(sums[k] for k in selected) / sum(counts[k] for k in selected))
        interval = [quantile(draws, .025), quantile(draws, .975)]
        original = frozen['paired_effects'][name]
        require(abs(mean - original['mean_paired_seconds']) < 1e-9, 'Independent paired mean mismatch')
        require(all(abs(a - b) < 1e-9 for a, b in zip(interval, original['descriptive_cluster_interval'])), 'Independent bootstrap mismatch')
        contrasts[name] = {'primary_n': len(primary), 'mean_paired_seconds': mean,
                           'descriptive_95_percent_cluster_interval': interval,
                           'post_hoc_all_final_valid_n': len(all_final_valid),
                           'post_hoc_all_final_valid_mean_seconds': statistics.mean(effects({b: blocks[b] for b in all_final_valid})),
                           'post_hoc_all_node_valid_n': len(all_node_valid),
                           'post_hoc_all_node_valid_mean_seconds': statistics.mean(effects({b: blocks[b] for b in all_node_valid})),
                           'post_hoc_strict_completion_n': len(strict_valid),
                           'post_hoc_strict_completion_mean_seconds': statistics.mean(effects({b: blocks[b] for b in strict_valid}))}
    provider_summary = {}
    for provider, selected in providers.items():
        usage = Counter(); present = Counter()
        for node in selected:
            fields = flat_tokens(node['usage']); usage.update(fields); present.update(fields.keys())
        ids = [x for x in identifiers[provider] if isinstance(x, str)]
        provider_summary[provider] = {'calls': len(selected), 'http_200': sum(n['http_status'] == 200 for n in selected),
             'schema_valid': sum(n['schema_valid'] for n in selected), 'reference_checks_valid': sum(n['valid'] for n in selected),
             'stop_reasons': dict(Counter(n['stop_reason'] or 'MISSING' for n in selected)),
             'service_tiers_observed': dict(Counter(n['service_tier'] or 'MISSING' for n in selected)),
             'returned_models': sorted({n['returned_model'] for n in selected if n['returned_model']}),
             'system_fingerprints_present': sum(bool(n['system_fingerprint']) for n in selected),
             'response_ids_present': len(ids), 'unique_response_ids': len(set(ids)),
             'reported_token_fields': {k: {'sum': v, 'records_present': present[k]} for k, v in sorted(usage.items())}}
    journal = [json.loads(x) for x in files['full_01/attempts.jsonl'].decode().splitlines()]
    require(Counter(x['event'] for x in journal) == Counter({'started': 240, 'completed': 240}), 'Interrupted/extra journal events')
    require([x['trial_id'] for x in journal if x['event'] == 'started'] == [t['trial_id'] for t in protocol['trials']], 'Executed order differs from frozen order')
    first, last = journal[0]['at'], journal[-1]['at']
    report = {'schema': 'tnsm.independent_matched_audit.v1', 'archive_sha256': ARCHIVE_SHA,
              'protocol_sha256': PROTOCOL_SHA, 'manifest_entries': manifest_counts,
              'full_trials': len(trials), 'full_calls': len(nodes), 'oracle_scenarios': 6,
              'live_api_inputs_are_synthetic': True, 'all_results_and_prespecified_intervals_reproduced': True,
              'first_trial_start_utc': first, 'last_trial_completed_utc': last,
              'journal_elapsed_seconds': (datetime.fromisoformat(last) - datetime.fromisoformat(first)).total_seconds(),
              'collector_environment': protocol['environment'], 'variants': summaries, 'paired_effects': contrasts,
              'provider_response_audit': provider_summary, 'invalid_nodes': issues,
              'invalid_node_categories': dict(Counter(x['category'] for x in issues)),
              'truncated_nodes': truncated, 'reasoning_fallback_nodes': fallback_nodes,
              'response_hashes_verified': raw_hashes_checked, 'excluded_primary_blocks': excluded,
              'post_hoc_selection_warning': 'Validity-selected subsets are outcome-dependent descriptive sensitivities, not replacements for the prespecified HTTP-complete population. They neither repair outputs nor preserve the full target population.',
              'original_analysis_flag_boundary': 'Minimum completeness/provenance gate only; not independent provider authentication, semantic correctness, expert validation, operational safety, coauthor approval or acceptance.',
              'validation_boundary': 'Reference checks establish identifier equality and selected action-language rules, not semantic entailment of a citation.',
              'scientific_scope': 'New common-harness component-block comparison on six author-designed scenarios. Count and provider diversity change together; whole-chain effect only. No framework-overhead estimate or retrospective decomposition of historical latency. No O-RAN actuation; execution disabled by design.'}
    rows = []
    for t in trials:
        rows.append({k: t[k] for k in ['trial_id', 'block', 'position', 'variant', 'scenario_id', 'repeat', 'cell_id', 'valid_final_candidate', 'valid_node_outputs', 'planned_calls_attempted', 'transport_complete']} |
                    {'seconds': t['_seconds'], **t['_oracle'], 'decision': t['outcome']['decision'],
                     'pre_review_action': t['outcome']['reconciliation']['reconciled_action_class'],
                     'enforced_action': t['outcome']['enforced_action_class']})
    return report, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=PAPER / 'evidence/inputs/TNSM_12002_Matched_Ablation_Evidence_20261016T194059Z.tar.gz')
    parser.add_argument('--output-dir', type=Path, default=PAPER / 'evidence/derived')
    args = parser.parse_args()
    report, rows = audit(args.archive)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'matched_inference_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    with (args.output_dir / 'matched_inference_trials.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({'archive_sha256': ARCHIVE_SHA, 'full_trials': report['full_trials'], 'full_calls': report['full_calls'],
                      'manifest_entries': report['manifest_entries'], 'independent_reproduction': True,
                      'invalid_node_categories': report['invalid_node_categories'],
                      'truncated_nodes': len(report['truncated_nodes']), 'reasoning_channel_fallbacks': len(report['reasoning_fallback_nodes'])}, indent=2))


if __name__ == '__main__':
    main()
