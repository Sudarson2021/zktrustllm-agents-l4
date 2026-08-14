#!/usr/bin/env python3
"""Build two leakage-resistant, preregistered annotation packages."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any


EXPECTED_ORACLE_SHA256 = (
    "4854f1d42d7824ae48ae3b37d8402d468c9f11034aa26b0fd9e96a21e1196c6c"
)
EXPECTED_ROWS = 180
EXPECTED_SCENARIOS = ("S1", "S2", "S3", "S4", "S5", "S6")
EXPECTED_MODES = ("NO_RAG", "RAG", "AGENTIC_RAG")
DECISIONS = ("COMPLIANT", "NON_COMPLIANT", "UNCERTAIN")
ACTIONS = ("AUTOMATIC", "HUMAN", "PRIVILEGED", "NEVER")
ANALYSIS_SCRIPT = Path(__file__).with_name("analyze_human_labels.py")
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20260808
OUTPUT_COLUMNS = (
    "case_id",
    "retrieval_mode",
    "evidence_sha256",
    "scenario_json",
    "decision_label",
    "action_label",
    "confidence_1_to_5",
    "notes",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: JSONL row must be an object")
        rows.append(value)
    return rows


def validate_source(rows: list[dict[str, Any]], expected_rows: int) -> None:
    if len(rows) != expected_rows:
        raise ValueError(f"expected {expected_rows} oracle rows; found {len(rows)}")
    cells = [str(row.get("cell_id", "")) for row in rows]
    if not all(cells) or len(set(cells)) != len(cells):
        raise ValueError("oracle cell IDs must be present and unique")
    scenario_counts = Counter(str(row.get("scenario_id", "")).upper() for row in rows)
    mode_counts = Counter(str(row.get("retrieval_mode", "")).upper() for row in rows)
    expected_scenario_count = expected_rows // len(EXPECTED_SCENARIOS)
    expected_mode_count = expected_rows // len(EXPECTED_MODES)
    if scenario_counts != Counter({scenario: expected_scenario_count for scenario in EXPECTED_SCENARIOS}):
        raise ValueError(f"unexpected scenario balance: {dict(scenario_counts)}")
    if mode_counts != Counter({mode: expected_mode_count for mode in EXPECTED_MODES}):
        raise ValueError(f"unexpected retrieval-mode balance: {dict(mode_counts)}")
    for row in rows:
        if str(row.get("oracle_decision", "")).upper() not in DECISIONS:
            raise ValueError(f"invalid oracle decision in {row.get('cell_id')}")
        if str(row.get("oracle_action_class", "")).upper() not in ACTIONS:
            raise ValueError(f"invalid oracle action in {row.get('cell_id')}")
        scenario_text = str(row.get("scenario", ""))
        if not scenario_text or sha256_text(scenario_text) != row.get("scenario_sha256"):
            raise ValueError(f"scenario hash mismatch in {row.get('cell_id')}")


def balanced_subset(rows: list[dict[str, Any]], size: int, seed: int) -> list[dict[str, Any]]:
    if size != 30:
        raise ValueError("the publication protocol fixes the blinded subset at 30 cells")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row["scenario_id"]).upper(),
                str(row["retrieval_mode"]).upper(),
            )
        ].append(row)
    expected_strata = {
        (scenario, mode) for scenario in EXPECTED_SCENARIOS for mode in EXPECTED_MODES
    }
    if set(grouped) != expected_strata:
        raise ValueError("oracle does not contain all 18 scenario/mode strata")

    rng = random.Random(seed)
    selected = []
    # One observation per stratum gives 18 cells. Each scenario then receives
    # one additional observation from two modes; the omitted mode rotates so
    # the final design is 5/scenario and 10/retrieval mode.
    for scenario_index, scenario in enumerate(EXPECTED_SCENARIOS):
        omitted_extra = EXPECTED_MODES[scenario_index % len(EXPECTED_MODES)]
        for mode in EXPECTED_MODES:
            stratum = sorted(grouped[(scenario, mode)], key=lambda row: str(row["cell_id"]))
            rng.shuffle(stratum)
            take = 1 if mode == omitted_extra else 2
            selected.extend(stratum[:take])
    if len(selected) != size or len({row["cell_id"] for row in selected}) != size:
        raise ValueError("balanced selection did not produce 30 unique cells")
    if Counter(row["scenario_id"] for row in selected) != Counter(
        {scenario: 5 for scenario in EXPECTED_SCENARIOS}
    ):
        raise ValueError("selected subset is not balanced five-per-scenario")
    if Counter(row["retrieval_mode"] for row in selected) != Counter(
        {mode: 10 for mode in EXPECTED_MODES}
    ):
        raise ValueError("selected subset is not balanced ten-per-mode")
    return selected


DROP_KEYS = {
    "scenario_id",
    "scenario_title",
    "oracle_decision",
    "oracle_action_class",
    "expert_verified",
    "cell_id",
}


def scrub_identifiers(value: Any, scenario_id: str, case_id: str) -> Any:
    if isinstance(value, dict):
        return {
            key: scrub_identifiers(child, scenario_id, case_id)
            for key, child in value.items()
            if str(key).lower() not in DROP_KEYS
            and not str(key).lower().startswith("source_")
        }
    if isinstance(value, list):
        return [scrub_identifiers(child, scenario_id, case_id) for child in value]
    if isinstance(value, str):
        return re.sub(rf"\b{re.escape(scenario_id)}\b", case_id, value)
    return value


def blinded_case(row: dict[str, Any], case_id: str) -> dict[str, str]:
    scenario_id = str(row["scenario_id"]).upper()
    source = json.loads(str(row["scenario"]))
    evidence = scrub_identifiers(source, scenario_id, case_id)
    scenario_json = canonical_json(evidence)
    return {
        "case_id": case_id,
        "retrieval_mode": str(row["retrieval_mode"]).upper(),
        "evidence_sha256": sha256_text(scenario_json),
        "scenario_json": scenario_json,
        "decision_label": "",
        "action_label": "",
        "confidence_1_to_5": "",
        "notes": "",
    }


def annotation_instructions(annotator: str) -> str:
    return f"""# Independent O-RAN policy annotation instructions

Package: `{annotator}`

## Independence and scope

Complete all 30 cases independently. Do not consult the other annotator, the
project repository, manuscript results, source cell identifiers, or an oracle
answer key. Use only the configuration and frozen evidence in `CASEBOOK.md` or
`blinded_cases.csv`. Do not infer standards clauses or operational facts that
are not supplied. This is a synthetic-policy annotation exercise, not a
production-network assessment.

Before starting, confirm with the study coordinator that the institution's
ethics and data-protection requirements for this professional-judgement task
have been satisfied. The package does not request a name or email address.

## Binary clearance-decision label

- `CLEAR`: supplied evidence supports policy conformity and clearance.
- `NOT_CLEAR`: supplied evidence shows a violation or is missing, conflicting,
  or insufficient. This fail-closed class combines the frozen oracle's
  `NON_COMPLIANT` and `UNCERTAIN` outcomes.

## Action label

- `AUTOMATIC`: an explicit proposed action can execute without further human
  or privileged approval under the supplied evidence.
- `HUMAN`: manual review/approval is required. Use this when evidence is
  insufficient or no safely executable action is established.
- `PRIVILEGED`: execution requires a specifically authorised elevated role.
- `NEVER`: the proposed/requested action is explicitly prohibited and must not
  execute.

For the preregistered ordinal analysis, the restriction order is
`AUTOMATIC < HUMAN < PRIVILEGED < NEVER`. Do not use that ordering to infer a
label; apply the definitions above to each case.

## Completion procedure

1. Read each case in `CASEBOOK.md`.
2. Enter exactly one decision and one action label in `blinded_cases.csv`.
3. Enter confidence as an integer from 1 (low) to 5 (high).
4. Keep notes concise and based only on supplied evidence.
5. Complete `annotator_declaration.csv`.
6. Return only the completed CSV files to the coordinator. Do not exchange
   labels with the other annotator before both submissions are frozen.

`PACKAGE_SHA256SUMS.txt` freezes the blank package as distributed. It is
expected to stop matching after you enter labels; the coordinator will hash
the two completed CSV files separately on receipt.
"""


def preregistration_plan(
    oracle_key_sha256: str,
    ethics_reference: str,
    annotator_approval_reference: str,
) -> dict[str, Any]:
    return {
        "schema": "zktrustllm.tnsm.human_label_preregistration.v1",
        "registered_at": utc_now(),
        "registered_before_labels": True,
        "labels_received_at_registration": False,
        "oracle_key_sha256": oracle_key_sha256,
        "analysis_script": ANALYSIS_SCRIPT.name,
        "analysis_script_sha256": sha256_file(ANALYSIS_SCRIPT),
        "ethics_self_assessment_reference": ethics_reference,
        "supervisor_annotator_approval_reference": annotator_approval_reference,
        "primary_estimands": {
            "binary_clearance_decision": {
                "labels": ["CLEAR", "NOT_CLEAR"],
                "oracle_mapping": {
                    "COMPLIANT": "CLEAR",
                    "NON_COMPLIANT": "NOT_CLEAR",
                    "UNCERTAIN": "NOT_CLEAR",
                },
                "statistic": "unweighted Cohen's kappa",
            },
            "ordinal_action_class": {
                "labels_in_order": list(ACTIONS),
                "statistic": "linear-weighted Cohen's kappa",
            },
        },
        "comparisons": [
            "oracle_vs_annotator_1",
            "oracle_vs_annotator_2",
            "annotator_1_vs_annotator_2",
        ],
        "interval": {
            "method": "scenario-cluster bootstrap percentile interval",
            "confidence_level": 0.95,
            "cluster": "scenario_id",
            "clusters": 6,
            "resample_whole_clusters": True,
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": BOOTSTRAP_SEED,
            "undefined_replicates": "exclude and report count",
            "small_cluster_boundary": (
                "Only six scenario clusters are available; intervals are descriptive "
                "and finite-sample coverage is not asserted."
            ),
        },
        "disagreement_rule": (
            "Report every pairwise disagreement and confusion matrix. Do not adjudicate, "
            "repair, relabel, or revise the frozen oracle in response to annotations."
        ),
        "invalid_input_rule": (
            "Missing, out-of-vocabulary, edited-evidence, or incomplete-declaration inputs "
            "fail closed; they are not imputed."
        ),
        "authorship_boundary": (
            "Annotators are acknowledged for professional judgement and are not added as "
            "authors solely for annotation."
        ),
    }


def casebook(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Blinded casebook",
        "",
        "Use the accompanying instructions and record labels only in `blinded_cases.csv`.",
        "",
    ]
    for row in rows:
        pretty = json.dumps(json.loads(row["scenario_json"]), indent=2, ensure_ascii=False)
        lines.extend(
            [
                f"## {row['case_id']} — {row['retrieval_mode']}",
                "",
                f"Evidence SHA-256: `{row['evidence_sha256']}`",
                "",
                "```json",
                pretty,
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, str]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_annotator_package(
    output_dir: Path, annotator: str, rows: list[dict[str, str]]
) -> dict[str, Any]:
    package = output_dir / annotator
    package.mkdir(parents=True, exist_ok=False)
    write_csv(package / "blinded_cases.csv", rows, OUTPUT_COLUMNS)
    (package / "CASEBOOK.md").write_text(casebook(rows), encoding="utf-8")
    (package / "ANNOTATION_INSTRUCTIONS.md").write_text(
        annotation_instructions(annotator), encoding="utf-8"
    )
    write_csv(
        package / "annotator_declaration.csv",
        [
            {
                "annotator_code": annotator,
                "oran_familiarity_yes_no": "",
                "independent_completion_yes_no": "",
                "oracle_or_peer_labels_accessed_yes_no": "",
                "contributed_to_oracle_prompts_or_scenarios_yes_no": "",
                "completed_utc": "",
            }
        ],
        (
            "annotator_code",
            "oran_familiarity_yes_no",
            "independent_completion_yes_no",
            "oracle_or_peer_labels_accessed_yes_no",
            "contributed_to_oracle_prompts_or_scenarios_yes_no",
            "completed_utc",
        ),
    )
    files = sorted(path for path in package.iterdir() if path.is_file())
    checksum_path = package / "PACKAGE_SHA256SUMS.txt"
    checksum_path.write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in files),
        encoding="utf-8",
    )
    return {
        "directory": annotator,
        "case_order": [row["case_id"] for row in rows],
        "files": {path.name: sha256_file(path) for path in files},
        "contains_oracle_labels": False,
        "contains_source_cell_ids": False,
    }


def build_packages(
    source_path: Path,
    output_dir: Path,
    size: int = 30,
    seed: int = 20260808,
    strict_source_hash: bool = True,
    ethics_reference: str = "",
    annotator_approval_reference: str = "",
) -> dict[str, Any]:
    source_path = source_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    ethics_reference = ethics_reference.strip()
    annotator_approval_reference = annotator_approval_reference.strip()
    if not ethics_reference:
        raise ValueError("an ethics self-assessment reference is required before packaging")
    if not annotator_approval_reference:
        raise ValueError("a supervisor annotator-approval reference is required before packaging")
    source_hash = sha256_file(source_path)
    if strict_source_hash and source_hash != EXPECTED_ORACLE_SHA256:
        raise ValueError(
            f"canonical oracle SHA-256 mismatch: expected {EXPECTED_ORACLE_SHA256}, observed {source_hash}"
        )
    rows = load_rows(source_path)
    validate_source(rows, EXPECTED_ROWS if strict_source_hash else len(rows))
    selected = balanced_subset(rows, size, seed)
    output_dir.mkdir(parents=True, exist_ok=False)

    case_rng = random.Random(seed ^ 0x258C0DE)
    case_numbers = list(range(1, size + 1))
    case_rng.shuffle(case_numbers)
    mapped = []
    coordinator_rows = []
    for row, number in zip(selected, case_numbers):
        case_id = f"CASE-{number:03d}"
        blinded = blinded_case(row, case_id)
        mapped.append(blinded)
        coordinator_rows.append(
            {
                "case_id": case_id,
                "cell_id": str(row["cell_id"]),
                "scenario_id": str(row["scenario_id"]).upper(),
                "retrieval_mode": str(row["retrieval_mode"]).upper(),
                "repeat": str(row["repeat"]),
                "source_scenario_sha256": str(row["scenario_sha256"]),
                "blinded_evidence_sha256": blinded["evidence_sha256"],
                "oracle_decision": str(row["oracle_decision"]).upper(),
                "oracle_action_class": str(row["oracle_action_class"]).upper(),
            }
        )

    order_one = list(mapped)
    order_two = list(mapped)
    random.Random(seed ^ 0xA11).shuffle(order_one)
    random.Random(seed ^ 0xA22).shuffle(order_two)
    package_one = write_annotator_package(output_dir, "annotator_1", order_one)
    package_two = write_annotator_package(output_dir, "annotator_2", order_two)

    coordinator = output_dir / "coordinator_DO_NOT_SHARE"
    coordinator.mkdir()
    coordinator_rows.sort(key=lambda row: row["case_id"])
    write_csv(
        coordinator / "oracle_key.csv",
        coordinator_rows,
        tuple(coordinator_rows[0]),
    )
    oracle_key_sha256 = sha256_file(coordinator / "oracle_key.csv")
    preregistration = preregistration_plan(
        oracle_key_sha256,
        ethics_reference,
        annotator_approval_reference,
    )
    (coordinator / "analysis_preregistration.json").write_text(
        json.dumps(preregistration, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (coordinator / "DO_NOT_SHARE.md").write_text(
        "# Coordinator-only material\n\nThis directory contains oracle labels and source cell IDs. "
        "Do not provide it, the full Stage 8A archive, or its hashes to either annotator.\n",
        encoding="utf-8",
    )

    manifest = {
        "schema": "zktrustllm.tnsm.human_label_package.v3",
        "generated_at": utc_now(),
        "source_path": source_path.name,
        "source_sha256": source_hash,
        "source_rows": len(rows),
        "selection_seed": seed,
        "selected_rows": len(mapped),
        "scenario_counts": dict(sorted(Counter(row["scenario_id"] for row in coordinator_rows).items())),
        "retrieval_mode_counts": dict(sorted(Counter(row["retrieval_mode"] for row in coordinator_rows).items())),
        "repeat_counts": dict(sorted(Counter(row["repeat"] for row in coordinator_rows).items())),
        "annotator_packages": [package_one, package_two],
        "annotator_orders_differ": package_one["case_order"] != package_two["case_order"],
        "oracle_key_sha256": oracle_key_sha256,
        "analysis_preregistration_sha256": sha256_file(
            coordinator / "analysis_preregistration.json"
        ),
        "analysis_script_sha256": preregistration["analysis_script_sha256"],
        "ethics_self_assessment_reference": ethics_reference,
        "supervisor_annotator_approval_reference": annotator_approval_reference,
        "provider_calls_made": False,
        "labels_authored_by_generator": False,
        "publication_ready_for_distribution": True,
        "statistical_boundary": (
            "The 30 cells are balanced across six scenario classes and three retrieval modes but remain clustered "
            "repeated observations of six scenario configurations. The preregistered analysis reports "
            "scenario-cluster-bootstrap intervals and explicitly disclaims reliable finite-sample coverage "
            "with only six clusters."
        ),
        "ethics_boundary": (
            "The University ethics self-assessment must be lodged before distribution. No names, email addresses, "
            "experience duration, or opinions about individuals are requested or retained."
        ),
    }
    (coordinator / "sampling_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--size", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260808)
    parser.add_argument("--no-strict-source-hash", action="store_true")
    parser.add_argument("--ethics-reference", required=True)
    parser.add_argument("--annotator-approval-reference", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_packages(
        args.input,
        args.output_dir,
        size=args.size,
        seed=args.seed,
        strict_source_hash=not args.no_strict_source_hash,
        ethics_reference=args.ethics_reference,
        annotator_approval_reference=args.annotator_approval_reference,
    )
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "source_sha256": result["source_sha256"],
                "selected_rows": result["selected_rows"],
                "scenario_counts": result["scenario_counts"],
                "retrieval_mode_counts": result["retrieval_mode_counts"],
                "annotator_orders_differ": result["annotator_orders_differ"],
                "provider_calls_made": result["provider_calls_made"],
                "publication_ready_for_distribution": result[
                    "publication_ready_for_distribution"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
