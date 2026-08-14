#!/usr/bin/env python3
"""Add repeat-determinism diagnostics and scenario-clustered oracle intervals."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
from typing import Any, Callable

from export_frozen_oracle import (
    EXPECTED_MODES,
    extract_manifest_labels,
    index_cell_key,
    load_final_report,
    load_sources,
    resolve_path,
    validate_index_matrix,
)


BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20260808


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    location = (len(ordered) - 1) * probability
    lower = math.floor(location)
    upper = math.ceil(location)
    if lower == upper:
        return ordered[lower]
    fraction = location - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def cluster_accuracy_interval(
    records: list[dict[str, Any]],
    correct: Callable[[dict[str, Any]], bool],
    seed: int,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> list[float]:
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        clusters[record["scenario_id"]].append(record)
    cluster_ids = sorted(clusters)
    if len(cluster_ids) != 6:
        raise ValueError(f"expected six scenario clusters, observed {len(cluster_ids)}")
    generator = random.Random(seed)
    estimates = []
    for _ in range(replicates):
        sample = [
            record
            for _ in cluster_ids
            for record in clusters[generator.choice(cluster_ids)]
        ]
        estimates.append(sum(correct(record) for record in sample) / len(sample))
    return [percentile(estimates, 0.025), percentile(estimates, 0.975)]


def final_labels(report: dict[str, Any]) -> tuple[str, str]:
    reflection = report.get("reflection")
    policy = report.get("policy")
    reflection = reflection if isinstance(reflection, dict) else {}
    policy = policy if isinstance(policy, dict) else {}
    decision = str(
        reflection.get("final_decision")
        or policy.get("decision")
        or report.get("final_decision")
        or ""
    ).upper()
    action = str(
        policy.get("enforced_action_class")
        or reflection.get("final_action_class")
        or report.get("enforced_action_class")
        or ""
    ).upper()
    if decision not in {"COMPLIANT", "NON_COMPLIANT", "UNCERTAIN"}:
        raise ValueError(f"invalid/missing final decision {decision!r}")
    if action not in {"AUTOMATIC", "HUMAN", "PRIVILEGED", "NEVER"}:
        raise ValueError(f"invalid/missing enforced action {action!r}")
    return decision, action


def summarize_mode(mode: str, records: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    if len(records) != 60:
        raise ValueError(f"{mode}: expected 60 successful records, observed {len(records)}")
    decision_correct = lambda record: record["decision"] == record["oracle_decision"]
    action_correct = lambda record: record["action"] == record["oracle_action"]
    covered = lambda record: record["decision"] != "UNCERTAIN"
    scenario_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        scenario_groups[record["scenario_id"]].append(record)
    repeat_consistency = []
    for scenario_id, group in sorted(scenario_groups.items()):
        decision_counts = Counter(record["decision"] for record in group)
        action_counts = Counter(record["action"] for record in group)
        repeat_consistency.append(
            {
                "scenario_id": scenario_id,
                "repeats": len(group),
                "decision_counts": dict(sorted(decision_counts.items())),
                "action_counts": dict(sorted(action_counts.items())),
                "decision_repeat_stable": len(decision_counts) == 1,
                "action_repeat_stable": len(action_counts) == 1,
            }
        )
    metrics = {}
    for index, (name, predicate) in enumerate(
        (
            ("decision_accuracy", decision_correct),
            ("enforced_action_accuracy", action_correct),
            ("coverage", covered),
        )
    ):
        numerator = sum(predicate(record) for record in records)
        metrics[name] = {
            "numerator": numerator,
            "denominator": len(records),
            "estimate": numerator / len(records),
            "scenario_cluster_bootstrap_ci95": cluster_accuracy_interval(
                records, predicate, seed + index
            ),
        }
    return {
        "mode": mode,
        "cells": len(records),
        "scenario_clusters": len(scenario_groups),
        "metrics": metrics,
        "repeat_consistency": repeat_consistency,
        "decision_stable_scenario_mode_groups": sum(
            row["decision_repeat_stable"] for row in repeat_consistency
        ),
        "action_stable_scenario_mode_groups": sum(
            row["action_repeat_stable"] for row in repeat_consistency
        ),
    }


def analyze(
    experiment_dir: Path,
    n8n_root: Path,
    strict_source_hashes: bool = True,
) -> dict[str, Any]:
    experiment_dir = experiment_dir.expanduser().resolve()
    n8n_root = n8n_root.expanduser().resolve()
    rows, oracle_manifest, _, source_hashes = load_sources(
        experiment_dir, n8n_root, strict_source_hashes
    )
    labels = extract_manifest_labels(oracle_manifest)
    validate_index_matrix(rows, labels)
    records = []
    for row in rows:
        scenario_id, mode, repeat = index_cell_key(row)
        response_path = resolve_path(row["response_file"], experiment_dir, n8n_root)
        report, _, _ = load_final_report(response_path, experiment_dir, n8n_root)
        decision, action = final_labels(report)
        records.append(
            {
                "cell_id": f"{scenario_id}:{mode}:R{repeat:02d}",
                "scenario_id": scenario_id,
                "retrieval_mode": mode,
                "repeat": repeat,
                "decision": decision,
                "action": action,
                "oracle_decision": str(row["ground_truth_decision"]).upper(),
                "oracle_action": str(row["ground_truth_action_class"]).upper(),
            }
        )
    by_mode = {
        mode: summarize_mode(
            mode,
            [record for record in records if record["retrieval_mode"] == mode],
            BOOTSTRAP_SEED + 10 * index,
        )
        for index, mode in enumerate(EXPECTED_MODES)
    }
    stable_decision_groups = sum(
        block["decision_stable_scenario_mode_groups"] for block in by_mode.values()
    )
    stable_action_groups = sum(
        block["action_stable_scenario_mode_groups"] for block in by_mode.values()
    )
    return {
        "schema": "zktrustllm.tnsm.oracle_clustered_statistics.v1",
        "generated_at": utc_now(),
        "provider_calls_made": False,
        "successful_cells": len(records),
        "scenario_clusters": 6,
        "retrieval_modes": 3,
        "repeats_per_scenario_mode": 10,
        "by_mode": by_mode,
        "repeat_determinism": {
            "scenario_mode_groups": 18,
            "decision_stable_groups": stable_decision_groups,
            "action_stable_groups": stable_action_groups,
            "boundary": (
                "Repeat stability is an observed property of these retained responses, not a "
                "guarantee that hosted model endpoints are deterministic across future calls."
            ),
        },
        "source_hashes": source_hashes,
        "interval_method": {
            "method": "scenario-cluster bootstrap percentile interval",
            "confidence_level": 0.95,
            "cluster": "scenario_id",
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": BOOTSTRAP_SEED,
            "boundary": (
                "Only six scenario clusters are available. Intervals are descriptive and "
                "reliable finite-sample coverage is not asserted. Ten repeats improve "
                "repeatability assessment but do not create 60 independent scenarios."
            ),
        },
    }


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Frozen-oracle clustered statistics",
        "",
        "| Mode | Metric | Estimate | Scenario-clustered 95% interval |",
        "|---|---|---:|---:|",
    ]
    for mode, block in result["by_mode"].items():
        for metric, values in block["metrics"].items():
            interval = values["scenario_cluster_bootstrap_ci95"]
            lines.append(
                f"| {mode} | {metric.replace('_', ' ')} | {values['estimate']:.3f} | "
                f"[{interval[0]:.3f}, {interval[1]:.3f}] |"
            )
    determinism = result["repeat_determinism"]
    lines.extend(
        [
            "",
            "## Repeat-determinism statement",
            "",
            f"Across 18 scenario-by-mode groups (10 repeats each), final decisions were "
            f"repeat-stable in {determinism['decision_stable_groups']}/18 groups and enforced "
            f"actions in {determinism['action_stable_groups']}/18 groups. Consequently, many "
            "cell-level percentages are multiples of one sixth and must not be interpreted as "
            "60 independent scenario outcomes.",
            "",
            determinism["boundary"],
            "",
            result["interval_method"]["boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def write_inventory(path: Path, result: dict[str, Any]) -> None:
    rows = [
        {"retrieval_mode": mode, **row}
        for mode, block in result["by_mode"].items()
        for row in block["repeat_consistency"]
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = (
            "retrieval_mode",
            "scenario_id",
            "repeats",
            "decision_counts",
            "action_counts",
            "decision_repeat_stable",
            "action_repeat_stable",
        )
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "decision_counts": json.dumps(row["decision_counts"], sort_keys=True),
                    "action_counts": json.dumps(row["action_counts"], sort_keys=True),
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--n8n-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--no-strict-source-hashes", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    result = analyze(
        args.experiment_dir,
        args.n8n_root,
        strict_source_hashes=not args.no_strict_source_hashes,
    )
    (output_dir / "oracle_clustered_statistics.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "oracle_clustered_statistics.md").write_text(
        markdown(result), encoding="utf-8"
    )
    write_inventory(output_dir / "repeat_consistency.csv", result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
