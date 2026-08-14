#!/usr/bin/env python3
"""Audit whether the frozen 240-row matrix supports row-bound ZK verification."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


PROOF_OUTCOME_COLUMNS = {
    "verifytx",
    "verify_tx",
    "proof_verified",
    "proof_valid",
    "verification_result",
}
ROW_BINDING_COLUMNS = {
    "proof_sha256",
    "proof_hash",
    "public_inputs_sha256",
    "public_input_hash",
    "witness_sha256",
    "calldata_sha256",
    "trace_commitment",
    "action_class",
    "policy_admissibility_flag",
    "trust_state",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(matrix_path: Path, circuit_path: Path) -> dict[str, Any]:
    matrix_path = matrix_path.expanduser().resolve()
    circuit_path = circuit_path.expanduser().resolve()
    with matrix_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
        columns = list(reader.fieldnames or [])
    if len(rows) != 240:
        raise ValueError(f"expected frozen 240-row matrix, observed {len(rows)}")
    if len({row.get("run_id", "") for row in rows}) != 240:
        raise ValueError("matrix run_id values are blank or non-unique")

    normalized_columns = {column.lower(): column for column in columns}
    outcome_columns = sorted(
        normalized_columns[name] for name in PROOF_OUTCOME_COLUMNS if name in normalized_columns
    )
    binding_columns = sorted(
        normalized_columns[name] for name in ROW_BINDING_COLUMNS if name in normalized_columns
    )
    variant_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        variant_rows[row.get("variant", "")].append(row)
    by_variant = {}
    for variant, records in sorted(variant_rows.items()):
        by_variant[variant] = {
            "rows": len(records),
            "prover_time_source_counts": dict(
                sorted(Counter(row.get("prover_time_source", "") for row in records).items())
            ),
            "prover_time_present_rows": sum(
                bool(row.get("prover_time_ms", "").strip()) for row in records
            ),
            "hardhat_test_outcome_counts": {
                f"passing={passing or 'blank'},failing={failing or 'blank'}": count
                for (passing, failing), count in sorted(
                    Counter(
                        (
                            row.get("hardhat_passing_tests", ""),
                            row.get("hardhat_failing_tests", ""),
                        )
                        for row in records
                    ).items()
                )
            },
        }

    circuit = circuit_path.read_text(encoding="utf-8")
    literal_constraints = {
        "policy_admissibility_flag_equals_1": "assert(policyAdmissibilityFlag == 1);" in circuit,
        "trust_state_equals_3": "assert(trustState == 3);" in circuit,
        "action_class_equals_3": "assert(actionClass == 3);" in circuit,
        "additive_trace_commitment": "assert(computed == traceCommitment);" in circuit,
    }
    row_bound_verified_rows = 0
    supports_all_240 = bool(outcome_columns and binding_columns and row_bound_verified_rows == 240)
    return {
        "schema": "zktrustllm.tnsm.zk_240_coverage_audit.v1",
        "generated_at": utc_now(),
        "provider_or_chain_calls_made": False,
        "matrix": {
            "path": matrix_path.name,
            "sha256": sha256_file(matrix_path),
            "rows": len(rows),
            "variants": dict(sorted(Counter(row["variant"] for row in rows).items())),
            "proof_outcome_columns": outcome_columns,
            "row_binding_columns": binding_columns,
            "verifier_gas_counts": dict(
                sorted(Counter(row.get("verifier_gas", "") for row in rows).items())
            ),
            "by_variant": by_variant,
        },
        "circuit": {
            "path": circuit_path.name,
            "sha256": sha256_file(circuit_path),
            "literal_constraints": literal_constraints,
            "semantic_boundary": (
                "AUTH_V2.2 proves only the encoded admissible/trusted/action-class-3 relation "
                "and an additive commitment for supplied field values; the matrix contains no "
                "row-level public inputs or proof outcome with which to bind that relation."
            ),
        },
        "row_bound_verified_rows": row_bound_verified_rows,
        "verify_all_240_supported_by_retained_evidence": supports_all_240,
        "decision": "RETITLE_OR_EXECUTE_NEW_ROW_BOUND_240_RUN",
        "manuscript_ready_statement": (
            "The frozen 240-row matrix contains no per-row proof outcome or proof/public-input "
            "binding. Full-L4 and No-IPFS each have 40/40 missing prover-time records, while the "
            "remaining four variants record the prover as not invoked. A constant verifier-gas "
            "field does not establish proof validity. Consequently, retained evidence supports "
            "0/240 row-bound successful verifications and cannot support a zero-knowledge title "
            "claim. Either execute and retain a new generalized row-bound 240-row proof run, or "
            "retitle and describe AUTH_V2.2 only as a bounded component experiment."
        ),
    }


def markdown(result: dict[str, Any]) -> str:
    matrix = result["matrix"]
    lines = [
        "# Frozen 240-row ZK coverage audit",
        "",
        f"- Matrix rows: {matrix['rows']}",
        f"- Per-row proof-outcome columns: {len(matrix['proof_outcome_columns'])}",
        f"- Per-row proof/public-input binding columns: {len(matrix['row_binding_columns'])}",
        f"- Row-bound successful verifications supported: {result['row_bound_verified_rows']}/240",
        f"- Decision: `{result['decision']}`",
        "",
        "| Variant | Rows | Prover-time present | Prover evidence | Hardhat outcome |",
        "|---|---:|---:|---|---|",
    ]
    for variant, block in matrix["by_variant"].items():
        lines.append(
            f"| {variant} | {block['rows']} | {block['prover_time_present_rows']} | "
            f"{json.dumps(block['prover_time_source_counts'], sort_keys=True)} | "
            f"{json.dumps(block['hardhat_test_outcome_counts'], sort_keys=True)} |"
        )
    lines.extend(["", result["manuscript_ready_statement"], ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    result = audit(args.matrix, args.circuit)
    (output_dir / "zk_240_coverage_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "zk_240_coverage_audit.md").write_text(
        markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
