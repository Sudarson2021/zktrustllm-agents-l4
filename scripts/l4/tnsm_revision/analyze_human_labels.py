#!/usr/bin/env python3
"""Validate blinded labels under the frozen, preregistered agreement protocol."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any


ORACLE_DECISIONS = {"COMPLIANT", "NON_COMPLIANT", "UNCERTAIN"}
BINARY_DECISIONS = ("CLEAR", "NOT_CLEAR")
ORACLE_DECISION_MAP = {
    "COMPLIANT": "CLEAR",
    "NON_COMPLIANT": "NOT_CLEAR",
    "UNCERTAIN": "NOT_CLEAR",
}
ACTION_ORDER = ("AUTOMATIC", "HUMAN", "PRIVILEGED", "NEVER")
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20260808
REQUIRED_SHEET_COLUMNS = {
    "case_id",
    "retrieval_mode",
    "evidence_sha256",
    "scenario_json",
    "decision_label",
    "action_label",
    "confidence_1_to_5",
    "notes",
}
REQUIRED_KEY_COLUMNS = {
    "case_id",
    "cell_id",
    "scenario_id",
    "retrieval_mode",
    "repeat",
    "source_scenario_sha256",
    "blinded_evidence_sha256",
    "oracle_decision",
    "oracle_action_class",
}
COMPARISONS = (
    ("oracle_vs_annotator_1", "Oracle", "Annotator 1"),
    ("oracle_vs_annotator_2", "Oracle", "Annotator 2"),
    ("annotator_1_vs_annotator_2", "Annotator 1", "Annotator 2"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cohen_kappa(
    left: list[str],
    right: list[str],
    labels: tuple[str, ...] | list[str] | None = None,
    weighting: str = "unweighted",
) -> dict[str, Any]:
    """Return ordinary or linear-weighted Cohen kappa with fixed categories."""
    if len(left) != len(right) or not left:
        raise ValueError("kappa inputs must have equal non-zero length")
    ordered = tuple(labels or sorted(set(left) | set(right)))
    if len(set(ordered)) != len(ordered) or not ordered:
        raise ValueError("kappa labels must be unique and non-empty")
    unknown = (set(left) | set(right)) - set(ordered)
    if unknown:
        raise ValueError(f"labels outside the declared scale: {sorted(unknown)}")
    if weighting not in {"unweighted", "linear"}:
        raise ValueError(f"unsupported kappa weighting: {weighting}")

    positions = {label: index for index, label in enumerate(ordered)}
    denominator = max(1, len(ordered) - 1)

    def agreement_weight(first: str, second: str) -> float:
        if weighting == "unweighted":
            return 1.0 if first == second else 0.0
        return 1.0 - abs(positions[first] - positions[second]) / denominator

    n = len(left)
    left_counts = Counter(left)
    right_counts = Counter(right)
    observed = sum(
        agreement_weight(first, second) for first, second in zip(left, right)
    ) / n
    expected = sum(
        agreement_weight(first, second)
        * (left_counts[first] / n)
        * (right_counts[second] / n)
        for first in ordered
        for second in ordered
    )
    exact_agreement = sum(first == second for first, second in zip(left, right)) / n
    if math.isclose(expected, 1.0, rel_tol=0.0, abs_tol=1e-15):
        kappa = None
        defined = False
    else:
        kappa = (observed - expected) / (1.0 - expected)
        defined = True
    return {
        "n": n,
        "weighting": weighting,
        "labels": list(ordered),
        "exact_agreement": exact_agreement,
        "weighted_observed_agreement": observed,
        "weighted_expected_agreement": expected,
        "cohen_kappa": kappa,
        "defined": defined,
    }


def confusion(
    left: list[str], right: list[str], labels: tuple[str, ...] | list[str]
) -> dict[str, dict[str, int]]:
    ordered = tuple(labels)
    matrix = {label: {other: 0 for other in ordered} for label in ordered}
    for first, second in zip(left, right):
        matrix[first][second] += 1
    return matrix


def percentile(values: list[float], probability: float) -> float:
    """R-7/NumPy-style linearly interpolated empirical percentile."""
    if not values:
        raise ValueError("cannot calculate a percentile of no values")
    ordered = sorted(values)
    location = (len(ordered) - 1) * probability
    lower = math.floor(location)
    upper = math.ceil(location)
    if lower == upper:
        return ordered[lower]
    fraction = location - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def scenario_cluster_bootstrap(
    left: list[str],
    right: list[str],
    clusters: list[str],
    labels: tuple[str, ...],
    weighting: str,
    seed: int,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> dict[str, Any]:
    if len(left) != len(right) or len(left) != len(clusters) or not left:
        raise ValueError("bootstrap vectors must have equal non-zero length")
    unique_clusters = sorted(set(clusters))
    indices = {
        cluster: [index for index, value in enumerate(clusters) if value == cluster]
        for cluster in unique_clusters
    }
    generator = random.Random(seed)
    estimates: list[float] = []
    undefined = 0
    for _ in range(replicates):
        selected = [generator.choice(unique_clusters) for _ in unique_clusters]
        sample_indices = [index for cluster in selected for index in indices[cluster]]
        result = cohen_kappa(
            [left[index] for index in sample_indices],
            [right[index] for index in sample_indices],
            labels,
            weighting,
        )
        if result["defined"]:
            estimates.append(float(result["cohen_kappa"]))
        else:
            undefined += 1
    interval = (
        [percentile(estimates, 0.025), percentile(estimates, 0.975)]
        if estimates
        else None
    )
    return {
        "method": "scenario-cluster bootstrap percentile interval",
        "confidence_level": 0.95,
        "cluster_variable": "scenario_id",
        "cluster_count": len(unique_clusters),
        "replicates_requested": replicates,
        "replicates_defined": len(estimates),
        "replicates_undefined": undefined,
        "seed": seed,
        "interval": interval,
        "small_cluster_boundary": (
            "Only six scenario clusters are available; this interval is descriptive "
            "and reliable finite-sample coverage is not asserted."
        ),
    }


def metric_bundle(
    oracle: list[str],
    annotator_1: list[str],
    annotator_2: list[str],
    clusters: list[str],
    labels: tuple[str, ...],
    weighting: str,
    seed_offset: int,
) -> dict[str, Any]:
    vectors = {
        "oracle": oracle,
        "annotator_1": annotator_1,
        "annotator_2": annotator_2,
    }
    comparisons: dict[str, Any] = {}
    for index, (key, _, _) in enumerate(COMPARISONS):
        first_name, second_name = key.split("_vs_")
        left = vectors[first_name]
        right = vectors[second_name]
        comparisons[key] = {
            "point": cohen_kappa(left, right, labels, weighting),
            "scenario_clustered_ci95": scenario_cluster_bootstrap(
                left,
                right,
                clusters,
                labels,
                weighting,
                BOOTSTRAP_SEED + seed_offset + index,
            ),
            "confusion_rows_left_columns_right": confusion(left, right, labels),
        }
    return {
        "n": len(oracle),
        "labels": list(labels),
        "weighting": weighting,
        "comparisons": comparisons,
        "label_counts": {
            name: dict(sorted(Counter(values).items()))
            for name, values in vectors.items()
        },
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def keyed(rows: list[dict[str, str]], path: Path) -> dict[str, dict[str, str]]:
    output = {}
    for row in rows:
        case_id = str(row.get("case_id", "")).strip()
        if not case_id or case_id in output:
            raise ValueError(f"{path}: blank or duplicate case_id {case_id!r}")
        output[case_id] = row
    return output


def load_key(path: Path, expected_sha256: str | None) -> dict[str, dict[str, str]]:
    observed = sha256_file(path)
    if expected_sha256 and observed != expected_sha256:
        raise ValueError(
            f"oracle-key SHA-256 mismatch: expected {expected_sha256}, observed {observed}"
        )
    rows = read_csv(path)
    if len(rows) != 30 or not rows or not REQUIRED_KEY_COLUMNS.issubset(rows[0]):
        raise ValueError(f"{path}: expected 30 rows and columns {sorted(REQUIRED_KEY_COLUMNS)}")
    output = keyed(rows, path)
    if len({row["cell_id"] for row in rows}) != 30:
        raise ValueError("oracle key must contain 30 unique source cells")
    if len({row["scenario_id"] for row in rows}) != 6:
        raise ValueError("oracle key must contain exactly six scenario clusters")
    for row in rows:
        row["oracle_decision"] = row["oracle_decision"].strip().upper()
        row["oracle_action_class"] = row["oracle_action_class"].strip().upper()
        if row["oracle_decision"] not in ORACLE_DECISIONS:
            raise ValueError(f"invalid oracle decision for {row['case_id']}")
        if row["oracle_action_class"] not in ACTION_ORDER:
            raise ValueError(f"invalid oracle action for {row['case_id']}")
    return output


def load_sheet(
    path: Path, oracle_key: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    if len(rows) != 30 or not rows or not REQUIRED_SHEET_COLUMNS.issubset(rows[0]):
        raise ValueError(f"{path}: expected 30 rows and columns {sorted(REQUIRED_SHEET_COLUMNS)}")
    output = keyed(rows, path)
    if set(output) != set(oracle_key):
        raise ValueError(f"{path}: case set differs from coordinator key")
    for case_id, row in output.items():
        decision = row["decision_label"].strip().upper()
        action = row["action_label"].strip().upper()
        confidence = row["confidence_1_to_5"].strip()
        if decision not in BINARY_DECISIONS:
            raise ValueError(f"{path}: invalid/incomplete binary decision for {case_id}")
        if action not in ACTION_ORDER:
            raise ValueError(f"{path}: invalid/incomplete action for {case_id}")
        if confidence not in {"1", "2", "3", "4", "5"}:
            raise ValueError(f"{path}: confidence must be 1--5 for {case_id}")
        scenario_json = row["scenario_json"]
        evidence_hash = sha256_text(scenario_json)
        if evidence_hash != row["evidence_sha256"]:
            raise ValueError(f"{path}: edited or corrupted scenario JSON for {case_id}")
        expected = oracle_key[case_id]
        if evidence_hash != expected["blinded_evidence_sha256"]:
            raise ValueError(f"{path}: evidence/key hash mismatch for {case_id}")
        if row["retrieval_mode"].strip().upper() != expected["retrieval_mode"].strip().upper():
            raise ValueError(f"{path}: retrieval mode changed for {case_id}")
        row["decision_label"] = decision
        row["action_label"] = action
        row["confidence_1_to_5"] = confidence
    return output


def load_declaration(path: Path, expected_code: str) -> dict[str, Any]:
    rows = read_csv(path)
    if len(rows) != 1:
        raise ValueError(f"{path}: expected one declaration row")
    row = rows[0]
    code = str(row.get("annotator_code", "")).strip()
    familiarity = str(row.get("oran_familiarity_yes_no", "")).strip().upper()
    independent = str(row.get("independent_completion_yes_no", "")).strip().upper()
    accessed = str(row.get("oracle_or_peer_labels_accessed_yes_no", "")).strip().upper()
    contributed = str(
        row.get("contributed_to_oracle_prompts_or_scenarios_yes_no", "")
    ).strip().upper()
    completed = str(row.get("completed_utc", "")).strip()
    if code != expected_code:
        raise ValueError(f"{path}: annotator code must remain {expected_code}")
    if familiarity != "YES":
        raise ValueError(f"{path}: O-RAN familiarity must be YES")
    if independent != "YES" or accessed != "NO" or contributed != "NO":
        raise ValueError(f"{path}: independence/contribution declaration does not pass")
    if not completed:
        raise ValueError(f"{path}: declaration is incomplete")
    return {
        "annotator_code": code,
        "oran_familiarity": True,
        "independent_completion": True,
        "oracle_or_peer_labels_accessed": False,
        "contributed_to_oracle_prompts_or_scenarios": False,
        "completed_utc": completed,
        "source_sha256": sha256_file(path),
    }


def load_preregistration(
    path: Path,
    expected_sha256: str,
    observed_key_sha256: str,
) -> dict[str, Any]:
    observed_sha256 = sha256_file(path)
    if observed_sha256 != expected_sha256:
        raise ValueError(
            "analysis-preregistration SHA-256 mismatch: "
            f"expected {expected_sha256}, observed {observed_sha256}"
        )
    plan = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema": "zktrustllm.tnsm.human_label_preregistration.v1",
        "registered_before_labels": True,
        "labels_received_at_registration": False,
        "oracle_key_sha256": observed_key_sha256,
        "analysis_script_sha256": sha256_file(Path(__file__).resolve()),
        "comparisons": [key for key, _, _ in COMPARISONS],
    }
    for key, value in required.items():
        if plan.get(key) != value:
            raise ValueError(f"preregistration field {key!r} differs from the frozen protocol")
    decision_plan = plan.get("primary_estimands", {}).get("binary_clearance_decision", {})
    action_plan = plan.get("primary_estimands", {}).get("ordinal_action_class", {})
    interval = plan.get("interval", {})
    if decision_plan.get("labels") != list(BINARY_DECISIONS):
        raise ValueError("preregistered binary decision labels differ")
    if decision_plan.get("oracle_mapping") != ORACLE_DECISION_MAP:
        raise ValueError("preregistered oracle decision mapping differs")
    if decision_plan.get("statistic") != "unweighted Cohen's kappa":
        raise ValueError("preregistered decision statistic differs")
    if action_plan.get("labels_in_order") != list(ACTION_ORDER):
        raise ValueError("preregistered action ordering differs")
    if action_plan.get("statistic") != "linear-weighted Cohen's kappa":
        raise ValueError("preregistered action statistic differs")
    if (
        interval.get("method") != "scenario-cluster bootstrap percentile interval"
        or interval.get("cluster") != "scenario_id"
        or interval.get("replicates") != BOOTSTRAP_REPLICATES
        or interval.get("seed") != BOOTSTRAP_SEED
    ):
        raise ValueError("preregistered interval procedure differs")
    if "Do not adjudicate" not in str(plan.get("disagreement_rule", "")):
        raise ValueError("preregistered disagreement rule is missing")
    return plan


def markdown_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Preregistered independent human-label agreement",
        "",
        f"- Cells: {summary['n_cells']}",
        f"- Scenario clusters: {summary['n_scenarios']}",
        f"- Frozen oracle revised after labels: {'yes' if summary['oracle_revision_count'] else 'no'}",
        f"- Publication-ready: {str(summary['publication_ready']).lower()}",
        "",
        "| Estimand | Comparison | Exact agreement | Kappa | Scenario-clustered 95% interval |",
        "|---|---|---:|---:|---:|",
    ]
    for estimand, block in summary["estimands"].items():
        for key, left_name, right_name in COMPARISONS:
            result = block["comparisons"][key]
            point = result["point"]
            interval = result["scenario_clustered_ci95"]["interval"]
            kappa = "undefined" if point["cohen_kappa"] is None else f"{point['cohen_kappa']:.3f}"
            interval_text = (
                "undefined"
                if interval is None
                else f"[{interval[0]:.3f}, {interval[1]:.3f}]"
            )
            lines.append(
                f"| {estimand.replace('_', ' ')} | {left_name} vs {right_name} | "
                f"{point['exact_agreement']:.3f} | {kappa} | {interval_text} |"
            )
    lines.extend(
        [
            "",
            "Decision uses unweighted Cohen's kappa after the preregistered fail-closed mapping "
            "COMPLIANT→CLEAR and NON_COMPLIANT/UNCERTAIN→NOT_CLEAR. Action uses linear-weighted "
            "Cohen's kappa on AUTOMATIC < HUMAN < PRIVILEGED < NEVER.",
            "",
            summary["statistical_boundary"],
            "",
            "All disagreements are reported in `disagreements.csv`; none are adjudicated and the "
            "frozen oracle is not revised.",
            "",
        ]
    )
    return "\n".join(lines)


def analyze(
    coordinator_key_path: Path,
    preregistration_path: Path,
    annotator_1_path: Path,
    annotator_2_path: Path,
    annotator_1_declaration_path: Path,
    annotator_2_declaration_path: Path,
    output_dir: Path,
    expected_key_sha256: str,
    expected_preregistration_sha256: str,
) -> dict[str, Any]:
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    coordinator_key_path = coordinator_key_path.expanduser().resolve()
    preregistration_path = preregistration_path.expanduser().resolve()
    oracle_key = load_key(coordinator_key_path, expected_key_sha256)
    preregistration = load_preregistration(
        preregistration_path,
        expected_preregistration_sha256,
        sha256_file(coordinator_key_path),
    )
    ann1 = load_sheet(annotator_1_path, oracle_key)
    ann2 = load_sheet(annotator_2_path, oracle_key)
    declaration_1 = load_declaration(annotator_1_declaration_path, "annotator_1")
    declaration_2 = load_declaration(annotator_2_declaration_path, "annotator_2")
    case_ids = sorted(oracle_key)

    oracle_decisions = [
        ORACLE_DECISION_MAP[oracle_key[case_id]["oracle_decision"]] for case_id in case_ids
    ]
    oracle_actions = [oracle_key[case_id]["oracle_action_class"] for case_id in case_ids]
    ann1_decisions = [ann1[case_id]["decision_label"] for case_id in case_ids]
    ann2_decisions = [ann2[case_id]["decision_label"] for case_id in case_ids]
    ann1_actions = [ann1[case_id]["action_label"] for case_id in case_ids]
    ann2_actions = [ann2[case_id]["action_label"] for case_id in case_ids]
    clusters = [oracle_key[case_id]["scenario_id"] for case_id in case_ids]

    estimands = {
        "binary_clearance_decision": metric_bundle(
            oracle_decisions,
            ann1_decisions,
            ann2_decisions,
            clusters,
            BINARY_DECISIONS,
            "unweighted",
            0,
        ),
        "ordinal_action_class": metric_bundle(
            oracle_actions,
            ann1_actions,
            ann2_actions,
            clusters,
            ACTION_ORDER,
            "linear",
            100,
        ),
    }

    completed_inventory = []
    disagreement_rows = []
    for index, case_id in enumerate(case_ids):
        key = oracle_key[case_id]
        labels_by_metric = {
            "binary_clearance_decision": {
                "oracle": oracle_decisions[index],
                "annotator_1": ann1_decisions[index],
                "annotator_2": ann2_decisions[index],
            },
            "ordinal_action_class": {
                "oracle": oracle_actions[index],
                "annotator_1": ann1_actions[index],
                "annotator_2": ann2_actions[index],
            },
        }
        completed_inventory.append(
            {
                "case_id": case_id,
                "cell_id": key["cell_id"],
                "scenario_id": key["scenario_id"],
                "retrieval_mode": key["retrieval_mode"],
                "oracle_decision_original": key["oracle_decision"],
                "oracle_decision_binary": oracle_decisions[index],
                "annotator_1_decision": ann1_decisions[index],
                "annotator_2_decision": ann2_decisions[index],
                "oracle_action": oracle_actions[index],
                "annotator_1_action": ann1_actions[index],
                "annotator_2_action": ann2_actions[index],
                "annotator_1_confidence": ann1[case_id]["confidence_1_to_5"],
                "annotator_2_confidence": ann2[case_id]["confidence_1_to_5"],
            }
        )
        for metric, values in labels_by_metric.items():
            for comparison, _, _ in COMPARISONS:
                first, second = comparison.split("_vs_")
                if values[first] != values[second]:
                    disagreement_rows.append(
                        {
                            "case_id": case_id,
                            "cell_id": key["cell_id"],
                            "scenario_id": key["scenario_id"],
                            "retrieval_mode": key["retrieval_mode"],
                            "estimand": metric,
                            "comparison": comparison,
                            "left_label": values[first],
                            "right_label": values[second],
                            "disposition": "REPORTED_NOT_ADJUDICATED",
                        }
                    )

    with (output_dir / "completed_label_inventory.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(completed_inventory[0]))
        writer.writeheader()
        writer.writerows(completed_inventory)
    disagreement_fields = (
        "case_id",
        "cell_id",
        "scenario_id",
        "retrieval_mode",
        "estimand",
        "comparison",
        "left_label",
        "right_label",
        "disposition",
    )
    with (output_dir / "disagreements.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=disagreement_fields)
        writer.writeheader()
        writer.writerows(disagreement_rows)

    comparison_results = [
        result
        for block in estimands.values()
        for result in block["comparisons"].values()
    ]
    publication_ready = all(
        result["point"]["defined"]
        and result["scenario_clustered_ci95"]["replicates_defined"] > 0
        for result in comparison_results
    )
    summary = {
        "schema": "zktrustllm.tnsm.human_label_agreement.v3",
        "generated_at": utc_now(),
        "n_cells": len(case_ids),
        "n_scenarios": len(set(clusters)),
        "estimands": estimands,
        "disagreement_rows": len(disagreement_rows),
        "disagreement_rule": preregistration["disagreement_rule"],
        "oracle_frozen": True,
        "oracle_revision_count": 0,
        "annotator_declarations": [declaration_1, declaration_2],
        "ethics_self_assessment_reference": preregistration[
            "ethics_self_assessment_reference"
        ],
        "supervisor_annotator_approval_reference": preregistration[
            "supervisor_annotator_approval_reference"
        ],
        "source_hashes": {
            "coordinator_key": sha256_file(coordinator_key_path),
            "analysis_preregistration": sha256_file(preregistration_path),
            "analysis_script": sha256_file(Path(__file__).resolve()),
            "annotator_1_labels": sha256_file(annotator_1_path),
            "annotator_2_labels": sha256_file(annotator_2_path),
            "annotator_1_declaration": sha256_file(annotator_1_declaration_path),
            "annotator_2_declaration": sha256_file(annotator_2_declaration_path),
        },
        "provider_calls_made": False,
        "publication_ready": publication_ready,
        "supervisor_comment_17_resolved": publication_ready,
        "statistical_boundary": (
            "The 30 cells are repeated observations within only six scenario clusters. "
            "All 95% intervals use a preregistered whole-scenario percentile bootstrap "
            "with 20,000 replicates; they are descriptive and reliable finite-sample "
            "coverage is not asserted."
        ),
        "claim_boundary": (
            "Agreement assesses consistency with two independent O-RAN-familiar professional "
            "judgements on a frozen synthetic subset; it does not establish production-network "
            "ground truth or standards certification."
        ),
    }
    (output_dir / "human_label_agreement.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "human_label_agreement.md").write_text(
        markdown_summary(summary), encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coordinator-key", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--annotator-1", type=Path, required=True)
    parser.add_argument("--annotator-2", type=Path, required=True)
    parser.add_argument("--annotator-1-declaration", type=Path, required=True)
    parser.add_argument("--annotator-2-declaration", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-key-sha256", required=True)
    parser.add_argument("--expected-preregistration-sha256", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = analyze(
        args.coordinator_key,
        args.preregistration,
        args.annotator_1,
        args.annotator_2,
        args.annotator_1_declaration,
        args.annotator_2_declaration,
        args.output_dir,
        expected_key_sha256=args.expected_key_sha256,
        expected_preregistration_sha256=args.expected_preregistration_sha256,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
