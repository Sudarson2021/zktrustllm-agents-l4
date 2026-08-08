#!/usr/bin/env python3
"""Export the hash-bound R10 success matrix to a canonical 180-row JSONL.

The exporter never calls a provider and never changes the frozen R10 tree.  It
joins the authoritative oracle manifest, six scenario configurations, the
180-row success index, and each successful run's frozen retrieval evidence.
Only input-side material is placed in the baseline prompt; model assessments,
reconciliation results, policy decisions, and oracle labels are excluded from
the prompt to prevent target leakage.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import tempfile
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable

from preflight_experiments import validate_canonical_oracle


EXPERIMENT_ID = "l4_oracle_20260716T131803Z_r10"
EXPECTED_SUCCESS_INDEX_SHA256 = "d9143f5c17fffc14caa5764360b7841a191bf6ce435fffc70742fa0f545a5f5c"
EXPECTED_ORACLE_MANIFEST_SHA256 = "941acc1d787e2e6f9b031ea33ed8c3f2d098292bb575a9725bb9e1830d169f31"
EXPECTED_SCENARIO_FILES = {
    "S1": (
        "S1_compliant_baseline.json",
        "f6151bea3dfc978a7a6f1baffe8ce97deec9d33242167e80a09220f5fdbcdad4",
    ),
    "S2": (
        "S2_drb_integrity_disabled.json",
        "9308268a77a61c3e69979586f9cbeaf335f274b904ca3d099e0f0c5e007471d7",
    ),
    "S3": (
        "S3_legacy_o1_tls.json",
        "1f88d3e181f914b3abc0e53529670bd43ea15476a8cd3326fc0080ca884ca814",
    ),
    "S4": (
        "S4_unauthorised_xapp_actuation.json",
        "81c11bac275712da1290fdc9ce57a2a42eedcd5c8d5d8ce9a0a7fa414d28f980",
    ),
    "S5": (
        "S5_replayed_anchor.json",
        "c5b8f0db9bc8cc961b81e63480567929501f285063fbf90e28b962d4631df955",
    ),
    "S6": (
        "S6_insufficient_evidence.json",
        "c61304444cfcab1aff4ba7b910aa3dc107b8cbfa5eaf4e0309a73e142030b8a6",
    ),
}
EXPECTED_MODES = ("NO_RAG", "RAG", "AGENTIC_RAG")
VALID_DECISIONS = {"COMPLIANT", "NON_COMPLIANT", "UNCERTAIN"}
VALID_ACTIONS = {"AUTOMATIC", "HUMAN", "PRIVILEGED", "NEVER"}
DECISION_KEYS = (
    "oracle_decision",
    "ground_truth_decision",
    "expected_oracle_decision",
    "expected_decision",
    "decision",
)
ACTION_KEYS = (
    "oracle_action_class",
    "ground_truth_action_class",
    "expected_oracle_action_class",
    "expected_action_class",
    "action_class",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def nested_values(value: Any, keys: Iterable[str]) -> list[str]:
    wanted = set(keys)
    found: list[str] = []
    queue: deque[Any] = deque([value])
    while queue:
        current = queue.popleft()
        if isinstance(current, dict):
            for key, child in current.items():
                if key in wanted and isinstance(child, (str, int, float)):
                    found.append(str(child).upper())
                elif isinstance(child, (dict, list)):
                    queue.append(child)
        elif isinstance(current, list):
            queue.extend(current)
    return found


def extract_manifest_labels(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    candidates: dict[str, list[dict[str, Any]]] = {key: [] for key in EXPECTED_SCENARIO_FILES}
    queue: deque[Any] = deque([manifest])
    while queue:
        value = queue.popleft()
        if isinstance(value, dict):
            scenario_id = str(value.get("scenario_id", "")).upper()
            if scenario_id in candidates:
                candidates[scenario_id].append(value)
            queue.extend(child for child in value.values() if isinstance(child, (dict, list)))
        elif isinstance(value, list):
            queue.extend(value)

    labels: dict[str, dict[str, str]] = {}
    for scenario_id, records in candidates.items():
        decisions: set[str] = set()
        actions: set[str] = set()
        for record in records:
            decisions.update(value for value in nested_values(record, DECISION_KEYS) if value in VALID_DECISIONS)
            actions.update(value for value in nested_values(record, ACTION_KEYS) if value in VALID_ACTIONS)
        if len(decisions) != 1 or len(actions) != 1:
            raise ValueError(
                f"oracle manifest {scenario_id}: expected one decision/action; "
                f"found decisions={sorted(decisions)}, actions={sorted(actions)}"
            )
        labels[scenario_id] = {
            "oracle_decision": next(iter(decisions)),
            "oracle_action_class": next(iter(actions)),
        }
    return labels


def verify_hash(path: Path, expected: str, description: str, strict: bool) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{description} not found: {path}")
    observed = sha256_file(path)
    if strict and observed != expected:
        raise ValueError(
            f"{description} SHA-256 mismatch: expected {expected}, observed {observed}"
        )
    return observed


def load_sources(
    experiment_dir: Path,
    n8n_root: Path,
    strict_source_hashes: bool,
) -> tuple[list[dict[str, str]], dict[str, Any], dict[str, dict[str, Any]], dict[str, str]]:
    index_path = experiment_dir / "run_index_success_matrix.csv"
    hashes: dict[str, str] = {
        "run_index_success_matrix.csv": verify_hash(
            index_path,
            EXPECTED_SUCCESS_INDEX_SHA256,
            "R10 success index",
            strict_source_hashes,
        )
    }
    with index_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 180:
        raise ValueError(f"expected 180 successful index rows; found {len(rows)}")

    manifest_path = experiment_dir / "oracle_scenario_manifest.json"
    hashes["oracle_scenario_manifest.json"] = verify_hash(
        manifest_path,
        EXPECTED_ORACLE_MANIFEST_SHA256,
        "R10 oracle manifest",
        strict_source_hashes,
    )
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("oracle manifest must be a JSON object")
    labels = extract_manifest_labels(manifest)

    scenario_dir = n8n_root / "scenarios" / "configs"
    scenarios: dict[str, dict[str, Any]] = {}
    for scenario_id, (filename, expected_hash) in EXPECTED_SCENARIO_FILES.items():
        path = scenario_dir / filename
        observed = verify_hash(
            path,
            expected_hash,
            f"scenario {scenario_id}",
            strict_source_hashes,
        )
        value = load_json(path)
        if not isinstance(value, dict):
            raise ValueError(f"scenario {scenario_id} must be a JSON object")
        if str(value.get("scenario_id", scenario_id)).upper() != scenario_id:
            raise ValueError(f"scenario identifier mismatch in {path}")
        scenarios[scenario_id] = {
            "path": path,
            "sha256": observed,
            "configuration": value,
        }
        hashes[f"scenarios/configs/{filename}"] = observed
    return rows, manifest, scenarios, hashes


def resolve_path(raw: str, experiment_dir: Path, n8n_root: Path) -> Path:
    value = Path(raw).expanduser()
    candidates = [value] if value.is_absolute() else []
    candidates.extend(
        [
            experiment_dir / value,
            n8n_root / value,
            n8n_root / "runtime" / value,
            experiment_dir.parent.parent / value,
        ]
    )
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    raise FileNotFoundError(
        f"response_file {raw!r} not found; checked: " + ", ".join(map(str, seen))
    )


def is_final_report(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("metadata"), dict)
        and isinstance(value.get("retrieval"), dict)
        and isinstance(value.get("report_hash"), str)
        and bool(value.get("run_id"))
    )


def find_reports(value: Any, max_depth: int = 7) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    queue: deque[tuple[str, Any, int]] = deque([("$", value, 0)])
    while queue:
        pointer, current, depth = queue.popleft()
        if is_final_report(current):
            found.append((pointer, current))
            continue
        if depth >= max_depth:
            continue
        if isinstance(current, dict):
            for key, child in current.items():
                if isinstance(child, (dict, list)):
                    queue.append((f"{pointer}.{key}", child, depth + 1))
        elif isinstance(current, list):
            for index, child in enumerate(current):
                if isinstance(child, (dict, list)):
                    queue.append((f"{pointer}[{index}]", child, depth + 1))
    return found


def possible_report_paths(value: Any) -> list[str]:
    names = {"report_path", "report_file", "final_report_path", "final_report_file"}
    paths: list[str] = []
    queue: deque[Any] = deque([value])
    while queue:
        current = queue.popleft()
        if isinstance(current, dict):
            for key, child in current.items():
                if key in names and isinstance(child, str):
                    paths.append(child)
                elif isinstance(child, (dict, list)):
                    queue.append(child)
        elif isinstance(current, list):
            queue.extend(current)
    return paths


def load_final_report(
    response_path: Path,
    experiment_dir: Path,
    n8n_root: Path,
) -> tuple[dict[str, Any], Path, str]:
    value = load_json(response_path)
    reports = find_reports(value)
    report_path = response_path
    pointer = reports[0][0] if len(reports) == 1 else ""
    if not reports:
        for raw_path in possible_report_paths(value):
            candidate = resolve_path(raw_path, experiment_dir, n8n_root)
            candidate_value = load_json(candidate)
            candidate_reports = find_reports(candidate_value)
            if len(candidate_reports) == 1:
                reports = candidate_reports
                report_path = candidate
                pointer = candidate_reports[0][0]
                break
    if len(reports) != 1:
        raise ValueError(
            f"{response_path}: expected exactly one final report; found {len(reports)}"
        )
    return reports[0][1], report_path, pointer


def relative_source_path(path: Path, n8n_root: Path) -> str:
    try:
        return path.resolve().relative_to(n8n_root.resolve()).as_posix()
    except ValueError:
        return path.name


def filtered_query(query: Any) -> dict[str, Any]:
    if not isinstance(query, dict):
        return {}
    allowed = (
        "query_text",
        "queries",
        "matched_security_terms",
        "agentic_security_parameters",
        "input_identifiers",
    )
    return {key: query[key] for key in allowed if key in query}


def filtered_chunks(chunks: Any) -> list[dict[str, Any]]:
    if chunks is None:
        return []
    if not isinstance(chunks, list):
        raise ValueError("retrieval.chunks must be a list")
    allowed = (
        "chunk_id",
        "document",
        "document_hash",
        "page_start",
        "page_end",
        "clause",
        "text",
        "chunk_hash",
    )
    records: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f"retrieval.chunks[{index}] must be an object")
        record = {key: chunk[key] for key in allowed if key in chunk}
        if "text" not in record:
            raise ValueError(f"retrieval.chunks[{index}] has no text")
        records.append(record)
    return records


def index_cell_key(row: dict[str, str]) -> tuple[str, str, int]:
    scenario_id = str(row.get("scenario_id", "")).upper()
    mode = str(row.get("retrieval_mode", "")).upper()
    try:
        repeat = int(row.get("repeat", ""))
    except ValueError as error:
        raise ValueError(f"invalid repeat in index row: {row.get('repeat')!r}") from error
    return scenario_id, mode, repeat


def validate_index_matrix(
    rows: list[dict[str, str]],
    labels: dict[str, dict[str, str]],
) -> None:
    keys = [index_cell_key(row) for row in rows]
    if len(set(keys)) != 180:
        raise ValueError("success index does not contain 180 unique scenario/mode/repeat cells")
    expected = {
        (scenario_id, mode, repeat)
        for scenario_id in EXPECTED_SCENARIO_FILES
        for mode in EXPECTED_MODES
        for repeat in range(1, 11)
    }
    if set(keys) != expected:
        missing = sorted(expected - set(keys))
        extra = sorted(set(keys) - expected)
        raise ValueError(f"success matrix mismatch; missing={missing[:5]}, extra={extra[:5]}")
    for row in rows:
        scenario_id, _, _ = index_cell_key(row)
        if str(row.get("status", "")).upper() != "SUCCESS":
            raise ValueError(f"non-success row retained for {index_cell_key(row)}")
        if str(row.get("experiment_id", "")) != EXPERIMENT_ID:
            raise ValueError(f"unexpected experiment_id for {index_cell_key(row)}")
        expected_labels = labels[scenario_id]
        observed_decision = str(row.get("ground_truth_decision", "")).upper()
        observed_action = str(row.get("ground_truth_action_class", "")).upper()
        if observed_decision != expected_labels["oracle_decision"]:
            raise ValueError(f"index/oracle decision mismatch for {index_cell_key(row)}")
        if observed_action != expected_labels["oracle_action_class"]:
            raise ValueError(f"index/oracle action mismatch for {index_cell_key(row)}")


def report_metadata_value(report: dict[str, Any], key: str) -> Any:
    metadata = report.get("metadata")
    if isinstance(metadata, dict) and key in metadata:
        return metadata[key]
    return report.get(key)


def build_record(
    row: dict[str, str],
    labels: dict[str, dict[str, str]],
    scenarios: dict[str, dict[str, Any]],
    experiment_dir: Path,
    n8n_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    scenario_id, mode, repeat = index_cell_key(row)
    response_path = resolve_path(row["response_file"], experiment_dir, n8n_root)
    response_sha = sha256_file(response_path)
    report, report_path, report_pointer = load_final_report(
        response_path, experiment_dir, n8n_root
    )
    report_file_sha = sha256_file(report_path)

    run_id = str(row.get("run_id", ""))
    if str(report.get("run_id", "")) != run_id:
        raise ValueError(f"{index_cell_key(row)}: run_id mismatch between index and report")
    index_report_hash = str(row.get("report_hash", ""))
    if not index_report_hash or str(report.get("report_hash", "")) != index_report_hash:
        raise ValueError(f"{index_cell_key(row)}: report_hash mismatch")
    report_scenario = str(report_metadata_value(report, "scenario_id") or "").upper()
    report_mode = str(report_metadata_value(report, "retrieval_mode") or "").upper()
    if report_scenario != scenario_id:
        raise ValueError(f"{index_cell_key(row)}: report scenario mismatch {report_scenario!r}")
    if report_mode != mode:
        raise ValueError(f"{index_cell_key(row)}: report retrieval mode mismatch {report_mode!r}")

    expected = labels[scenario_id]
    metadata = report.get("metadata", {})
    if isinstance(metadata, dict):
        reported_decision = metadata.get("expected_oracle_decision")
        reported_action = metadata.get("expected_oracle_action_class")
        if reported_decision and str(reported_decision).upper() != expected["oracle_decision"]:
            raise ValueError(f"{index_cell_key(row)}: report/oracle decision mismatch")
        if reported_action and str(reported_action).upper() != expected["oracle_action_class"]:
            raise ValueError(f"{index_cell_key(row)}: report/oracle action mismatch")

    retrieval = report.get("retrieval")
    if not isinstance(retrieval, dict):
        raise ValueError(f"{index_cell_key(row)}: report lacks retrieval object")
    retrieval_mode = str(
        (retrieval.get("query") or {}).get("retrieval_mode")
        if isinstance(retrieval.get("query"), dict)
        else ""
    ).upper()
    if retrieval_mode and retrieval_mode != mode:
        raise ValueError(f"{index_cell_key(row)}: retrieval bundle mode mismatch")
    chunks = filtered_chunks(retrieval.get("chunks", []))
    query = filtered_query(retrieval.get("query") or report.get("query"))

    prompt_payload = {
        "schema": "zktrustllm.frozen_oracle_input.v1",
        "task": "Assess O-RAN security policy conformance and required action class.",
        "scenario_id": scenario_id,
        "scenario_title": row.get("scenario_title", ""),
        "configuration": scenarios[scenario_id]["configuration"],
        "retrieval_mode": mode,
        "retrieval_evidence": {
            "grounding_available": bool(retrieval.get("grounding_available")),
            "query": query if mode != "NO_RAG" else {},
            "chunks": chunks,
        },
    }
    prompt = canonical_json(prompt_payload)
    record = {
        "cell_id": f"{scenario_id}:{mode}:R{repeat:02d}",
        "scenario_id": scenario_id,
        "scenario_title": row.get("scenario_title", ""),
        "retrieval_mode": mode,
        "repeat": repeat,
        "scenario": prompt,
        "scenario_sha256": sha256_text(prompt),
        "oracle_decision": expected["oracle_decision"],
        "oracle_action_class": expected["oracle_action_class"],
        "expert_verified": str(row.get("expert_verified", "")).lower() == "true",
        "source_run_id": run_id,
        "source_report_hash": index_report_hash,
        "source_response_file": relative_source_path(response_path, n8n_root),
        "source_response_sha256": response_sha,
        "source_report_file": relative_source_path(report_path, n8n_root),
        "source_report_file_sha256": report_file_sha,
        "source_retrieval_bundle_hash": retrieval.get("bundle_hash"),
    }
    provenance = {
        "cell_id": record["cell_id"],
        "response_file": record["source_response_file"],
        "response_sha256": response_sha,
        "report_file": record["source_report_file"],
        "report_file_sha256": report_file_sha,
        "report_pointer": report_pointer,
        "report_hash": index_report_hash,
        "retrieval_bundle_hash": retrieval.get("bundle_hash"),
        "retrieval_chunk_count": len(chunks),
        "retrieval_grounding_available": bool(retrieval.get("grounding_available")),
    }
    return record, provenance


def probe_sources(
    rows: list[dict[str, str]],
    labels: dict[str, dict[str, str]],
    scenarios: dict[str, dict[str, Any]],
    experiment_dir: Path,
    n8n_root: Path,
) -> dict[str, Any]:
    selected: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        scenario_id, mode, repeat = index_cell_key(row)
        if repeat == 1:
            selected[(scenario_id, mode)] = row
    cells: list[dict[str, Any]] = []
    for key in sorted(selected, key=lambda item: (int(item[0][1:]), EXPECTED_MODES.index(item[1]))):
        record, provenance = build_record(
            selected[key], labels, scenarios, experiment_dir, n8n_root
        )
        cells.append(
            {
                **provenance,
                "scenario_id": record["scenario_id"],
                "retrieval_mode": record["retrieval_mode"],
                "scenario_sha256": record["scenario_sha256"],
            }
        )
    return {
        "schema": "zktrustllm.tnsm.oracle_export_probe.v1",
        "experiment_id": EXPERIMENT_ID,
        "representative_cell_count": len(cells),
        "labels_from_authoritative_manifest": labels,
        "cells": cells,
        "provider_calls_made": False,
    }


def export_oracle(
    experiment_dir: Path,
    n8n_root: Path,
    output_jsonl: Path,
    manifest_output: Path,
    probe_output: Path,
    strict_source_hashes: bool = True,
) -> dict[str, Any]:
    experiment_dir = experiment_dir.expanduser().resolve()
    n8n_root = n8n_root.expanduser().resolve()
    rows, oracle_manifest, scenarios, source_hashes = load_sources(
        experiment_dir, n8n_root, strict_source_hashes
    )
    labels = extract_manifest_labels(oracle_manifest)
    validate_index_matrix(rows, labels)

    probe = probe_sources(rows, labels, scenarios, experiment_dir, n8n_root)
    atomic_write_text(probe_output, json.dumps(probe, indent=2, sort_keys=True) + "\n")

    mode_order = {mode: index for index, mode in enumerate(EXPECTED_MODES)}
    ordered_rows = sorted(
        rows,
        key=lambda row: (
            int(index_cell_key(row)[0][1:]),
            mode_order[index_cell_key(row)[1]],
            index_cell_key(row)[2],
        ),
    )
    records: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    warnings: list[str] = []
    for row in ordered_rows:
        record, source = build_record(
            row, labels, scenarios, experiment_dir, n8n_root
        )
        records.append(record)
        provenance.append(source)
        if record["retrieval_mode"] == "NO_RAG" and source["retrieval_chunk_count"]:
            warnings.append(
                f"{record['cell_id']}: NO_RAG retained {source['retrieval_chunk_count']} chunks"
            )
        if record["retrieval_mode"] != "NO_RAG" and not source["retrieval_chunk_count"]:
            warnings.append(f"{record['cell_id']}: retrieval mode has zero chunks")

    jsonl_text = "".join(canonical_json(record) + "\n" for record in records)
    atomic_write_text(output_jsonl, jsonl_text)
    canonical_validation = validate_canonical_oracle(output_jsonl)
    if not canonical_validation["valid"]:
        raise ValueError(
            "canonical export failed its contract: "
            + "; ".join(canonical_validation["reasons"])
        )

    source_response_hashes = {
        source["response_file"]: source["response_sha256"] for source in provenance
    }
    source_report_hashes = {
        source["report_file"]: source["report_file_sha256"] for source in provenance
    }
    retrieval_counts = Counter(
        (record["retrieval_mode"], source["retrieval_chunk_count"])
        for record, source in zip(records, provenance)
    )
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    manifest = {
        "schema": "zktrustllm.tnsm.canonical_oracle_export.v1",
        "generated_at": generated_at,
        "experiment_id": EXPERIMENT_ID,
        "provider_calls_made": False,
        "frozen_source_modified": False,
        "target_leakage_controls": {
            "oracle_labels_excluded_from_prompt": True,
            "model_assessments_excluded_from_prompt": True,
            "reconciliation_and_policy_outputs_excluded_from_prompt": True,
            "only_scenario_configuration_and_frozen_retrieval_input_in_prompt": True,
        },
        "source_hashes": source_hashes,
        "source_response_hashes": dict(sorted(source_response_hashes.items())),
        "source_report_file_hashes": dict(sorted(source_report_hashes.items())),
        "canonical_jsonl": {
            "path": output_jsonl.name,
            "sha256": sha256_file(output_jsonl),
            "rows": len(records),
        },
        "canonical_validation": canonical_validation,
        "oracle_manifest_internal_hash": oracle_manifest.get("oracle_manifest_hash"),
        "oracle_version": oracle_manifest.get("oracle_version"),
        "expert_verified": oracle_manifest.get("expert_verified", False),
        "labels_from_authoritative_manifest": labels,
        "retrieval_chunk_count_distribution": {
            f"{mode}:{count}": frequency
            for (mode, count), frequency in sorted(retrieval_counts.items())
        },
        "warnings": warnings,
        "claim_boundary": (
            "This is a deterministic export of the frozen synthetic-policy oracle and its "
            "retained retrieval inputs. It is not independent expert verification or "
            "production O-RAN validation."
        ),
    }
    atomic_write_text(manifest_output, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--n8n-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--probe-output", type=Path, required=True)
    parser.add_argument(
        "--development-fixture",
        action="store_true",
        help="disable frozen source hash pins; forbidden for manuscript evidence",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = export_oracle(
        args.experiment_dir,
        args.n8n_root,
        args.output.expanduser().resolve(),
        args.manifest_output.expanduser().resolve(),
        args.probe_output.expanduser().resolve(),
        strict_source_hashes=not args.development_fixture,
    )
    compact = {
        "canonical_jsonl": result["canonical_jsonl"],
        "canonical_validation": result["canonical_validation"],
        "warnings": result["warnings"],
        "manifest": str(args.manifest_output.expanduser().resolve()),
        "probe": str(args.probe_output.expanduser().resolve()),
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
