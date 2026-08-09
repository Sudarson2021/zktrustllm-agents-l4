#!/usr/bin/env python3
"""Validate independent annotations and calculate cell/scenario-level kappa."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


DECISIONS = {"COMPLIANT", "NON_COMPLIANT", "UNCERTAIN"}
ACTIONS = {"AUTOMATIC", "HUMAN", "PRIVILEGED", "NEVER"}
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


def cohen_kappa(left: list[str], right: list[str]) -> dict[str, float]:
    if len(left) != len(right) or not left:
        raise ValueError("kappa inputs must have equal non-zero length")
    labels = sorted(set(left) | set(right))
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum(
        (left_counts[label] / len(left)) * (right_counts[label] / len(right))
        for label in labels
    )
    if expected == 1.0:
        kappa = 1.0 if observed == 1.0 else 0.0
    else:
        kappa = (observed - expected) / (1.0 - expected)
    return {
        "agreement": observed,
        "expected_agreement": expected,
        "cohen_kappa": kappa,
    }


def confusion(left: list[str], right: list[str]) -> dict[str, dict[str, int]]:
    labels = sorted(set(left) | set(right))
    matrix = {label: {other: 0 for other in labels} for label in labels}
    for first, second in zip(left, right):
        matrix[first][second] += 1
    return matrix


def metric_bundle(oracle: list[str], ann1: list[str], ann2: list[str]) -> dict[str, Any]:
    return {
        "n": len(oracle),
        "oracle_vs_annotator_1": cohen_kappa(oracle, ann1),
        "oracle_vs_annotator_2": cohen_kappa(oracle, ann2),
        "annotator_1_vs_annotator_2": cohen_kappa(ann1, ann2),
        "confusion_oracle_rows_annotator_1_columns": confusion(oracle, ann1),
        "confusion_oracle_rows_annotator_2_columns": confusion(oracle, ann2),
        "label_counts": {
            "oracle": dict(sorted(Counter(oracle).items())),
            "annotator_1": dict(sorted(Counter(ann1).items())),
            "annotator_2": dict(sorted(Counter(ann2).items())),
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
    for row in rows:
        row["oracle_decision"] = row["oracle_decision"].strip().upper()
        row["oracle_action_class"] = row["oracle_action_class"].strip().upper()
        if row["oracle_decision"] not in DECISIONS:
            raise ValueError(f"invalid oracle decision for {row['case_id']}")
        if row["oracle_action_class"] not in ACTIONS:
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
        if decision not in DECISIONS:
            raise ValueError(f"{path}: invalid/incomplete decision for {case_id}")
        if action not in ACTIONS:
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
    independent = str(row.get("independent_completion_yes_no", "")).strip().upper()
    accessed = str(row.get("oracle_or_peer_labels_accessed_yes_no", "")).strip().upper()
    experience = str(row.get("oran_experience_years", "")).strip()
    completed = str(row.get("completed_utc", "")).strip()
    if code != expected_code:
        raise ValueError(f"{path}: annotator code must remain {expected_code}")
    if independent != "YES" or accessed != "NO":
        raise ValueError(f"{path}: independence declaration does not pass")
    try:
        experience_value = float(experience)
    except ValueError as exc:
        raise ValueError(f"{path}: O-RAN experience must be numeric") from exc
    if experience_value <= 0 or not completed:
        raise ValueError(f"{path}: declaration is incomplete")
    return {
        "annotator_code": code,
        "oran_experience_years": experience_value,
        "independent_completion": True,
        "oracle_or_peer_labels_accessed": False,
        "completed_utc": completed,
        "source_sha256": sha256_file(path),
    }


def majority(values: list[str]) -> str:
    counts = Counter(values)
    maximum = max(counts.values())
    winners = sorted(label for label, count in counts.items() if count == maximum)
    return winners[0] if len(winners) == 1 else "MIXED"


def scenario_level(
    case_ids: list[str],
    oracle_key: dict[str, dict[str, str]],
    ann1: dict[str, dict[str, str]],
    ann2: dict[str, dict[str, str]],
    oracle_field: str,
    annotation_field: str,
) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    for case_id in case_ids:
        groups[oracle_key[case_id]["scenario_id"]].append(case_id)
    oracle_labels = []
    first_labels = []
    second_labels = []
    details = []
    for scenario_id in sorted(groups):
        cases = groups[scenario_id]
        oracle_values = {oracle_key[case_id][oracle_field] for case_id in cases}
        if len(oracle_values) != 1:
            raise ValueError(f"oracle is not stable within {scenario_id}")
        oracle_value = next(iter(oracle_values))
        first = majority([ann1[case_id][annotation_field] for case_id in cases])
        second = majority([ann2[case_id][annotation_field] for case_id in cases])
        oracle_labels.append(oracle_value)
        first_labels.append(first)
        second_labels.append(second)
        details.append(
            {
                "scenario_id": scenario_id,
                "cells": len(cases),
                "oracle": oracle_value,
                "annotator_1_majority": first,
                "annotator_2_majority": second,
            }
        )
    return {"metrics": metric_bundle(oracle_labels, first_labels, second_labels), "details": details}


def markdown_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Independent human-label agreement",
        "",
        f"- Cells: {summary['n_cells']}",
        f"- Scenario clusters: {summary['n_scenarios']}",
        f"- Publication-ready: {str(summary['publication_ready']).lower()}",
        "",
        "| Estimand | Comparison | Agreement | Cohen's kappa |",
        "|---|---|---:|---:|",
    ]
    for estimand in ("decision", "action", "joint_decision_action"):
        block = summary["cell_level"][estimand]
        for key, label in (
            ("oracle_vs_annotator_1", "Oracle vs annotator 1"),
            ("oracle_vs_annotator_2", "Oracle vs annotator 2"),
            ("annotator_1_vs_annotator_2", "Annotator 1 vs annotator 2"),
        ):
            result = block[key]
            lines.append(
                f"| {estimand.replace('_', ' ')} | {label} | {result['agreement']:.3f} | {result['cohen_kappa']:.3f} |"
            )
    lines.extend(
        [
            "",
            "Cell-level results are descriptive because the 30 cells are repeated observations within six scenario classes. ",
            "The JSON artifact also reports six-scenario majority-label sensitivity results.",
            "",
        ]
    )
    return "\n".join(lines)


def analyze(
    coordinator_key_path: Path,
    annotator_1_path: Path,
    annotator_2_path: Path,
    annotator_1_declaration_path: Path,
    annotator_2_declaration_path: Path,
    output_dir: Path,
    expected_key_sha256: str | None = None,
) -> dict[str, Any]:
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    oracle_key = load_key(coordinator_key_path, expected_key_sha256)
    ann1 = load_sheet(annotator_1_path, oracle_key)
    ann2 = load_sheet(annotator_2_path, oracle_key)
    declaration_1 = load_declaration(annotator_1_declaration_path, "annotator_1")
    declaration_2 = load_declaration(annotator_2_declaration_path, "annotator_2")
    case_ids = sorted(oracle_key)

    oracle_decisions = [oracle_key[case_id]["oracle_decision"] for case_id in case_ids]
    oracle_actions = [oracle_key[case_id]["oracle_action_class"] for case_id in case_ids]
    ann1_decisions = [ann1[case_id]["decision_label"] for case_id in case_ids]
    ann2_decisions = [ann2[case_id]["decision_label"] for case_id in case_ids]
    ann1_actions = [ann1[case_id]["action_label"] for case_id in case_ids]
    ann2_actions = [ann2[case_id]["action_label"] for case_id in case_ids]
    join = lambda left, right: [f"{a}/{b}" for a, b in zip(left, right)]

    cell_level = {
        "decision": metric_bundle(oracle_decisions, ann1_decisions, ann2_decisions),
        "action": metric_bundle(oracle_actions, ann1_actions, ann2_actions),
        "joint_decision_action": metric_bundle(
            join(oracle_decisions, oracle_actions),
            join(ann1_decisions, ann1_actions),
            join(ann2_decisions, ann2_actions),
        ),
    }
    scenario_sensitivity = {
        "decision": scenario_level(
            case_ids,
            oracle_key,
            ann1,
            ann2,
            "oracle_decision",
            "decision_label",
        ),
        "action": scenario_level(
            case_ids,
            oracle_key,
            ann1,
            ann2,
            "oracle_action_class",
            "action_label",
        ),
    }

    completed_inventory = []
    for case_id in case_ids:
        key = oracle_key[case_id]
        completed_inventory.append(
            {
                "case_id": case_id,
                "cell_id": key["cell_id"],
                "scenario_id": key["scenario_id"],
                "retrieval_mode": key["retrieval_mode"],
                "oracle_decision": key["oracle_decision"],
                "annotator_1_decision": ann1[case_id]["decision_label"],
                "annotator_2_decision": ann2[case_id]["decision_label"],
                "oracle_action": key["oracle_action_class"],
                "annotator_1_action": ann1[case_id]["action_label"],
                "annotator_2_action": ann2[case_id]["action_label"],
                "annotator_1_confidence": ann1[case_id]["confidence_1_to_5"],
                "annotator_2_confidence": ann2[case_id]["confidence_1_to_5"],
            }
        )
    with (output_dir / "completed_label_inventory.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(completed_inventory[0]))
        writer.writeheader()
        writer.writerows(completed_inventory)

    summary = {
        "schema": "zktrustllm.tnsm.human_label_agreement.v2",
        "generated_at": utc_now(),
        "n_cells": len(case_ids),
        "n_scenarios": len({row["scenario_id"] for row in oracle_key.values()}),
        "cell_level": cell_level,
        "scenario_level_majority_sensitivity": scenario_sensitivity,
        "annotator_declarations": [declaration_1, declaration_2],
        "source_hashes": {
            "coordinator_key": sha256_file(coordinator_key_path),
            "annotator_1_labels": sha256_file(annotator_1_path),
            "annotator_2_labels": sha256_file(annotator_2_path),
        },
        "provider_calls_made": False,
        "publication_ready": len(case_ids) == 30,
        "supervisor_comment_17_resolved": len(case_ids) == 30,
        "statistical_boundary": (
            "The 30 cell-level observations are clustered repeated cells from six scenario configurations. "
            "Cell-level agreement and kappa are descriptive. Six-scenario majority-label results are reported "
            "as a small-cluster sensitivity analysis and also have limited precision."
        ),
        "claim_boundary": (
            "Agreement validates consistency with two independent O-RAN-literate professional judgements on a "
            "synthetic frozen subset; it does not establish production-network ground truth or standards certification."
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
    parser.add_argument("--annotator-1", type=Path, required=True)
    parser.add_argument("--annotator-2", type=Path, required=True)
    parser.add_argument("--annotator-1-declaration", type=Path, required=True)
    parser.add_argument("--annotator-2-declaration", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-key-sha256")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = analyze(
        args.coordinator_key,
        args.annotator_1,
        args.annotator_2,
        args.annotator_1_declaration,
        args.annotator_2_declaration,
        args.output_dir,
        expected_key_sha256=args.expected_key_sha256,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
