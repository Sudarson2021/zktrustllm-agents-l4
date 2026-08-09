#!/usr/bin/env python3
"""Audit the frozen R10 HTTP failures without inventing an upstream cause.

The tool binds its analysis to the frozen failed/success CSV indexes, follows
only linked response files inside the supplied experiment tree, extracts a
small allowlist of diagnostic fields, redacts credential-like strings, and
reconstructs eventual retry outcomes by scenario/mode/repeat cell.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import re
import statistics
import tempfile
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


EXPERIMENT_ID = "l4_oracle_20260716T131803Z_r10"
EXPECTED_FAILED_INDEX_SHA256 = (
    "c2c59625a7467d2bbefabb64102e8064cb7d5438383af1dd1aa02787388048b6"
)
EXPECTED_SUCCESS_INDEX_SHA256 = (
    "d9143f5c17fffc14caa5764360b7841a191bf6ce435fffc70742fa0f545a5f5c"
)
EXPECTED_FINAL_SUMMARY_SHA256 = (
    "707ae31e6d53d56c610e35f0944d2c840384852aa786b5230af646ea795b2eed"
)
EXPECTED_FAILURES = 53
EXPECTED_SUCCESSES = 180
MAX_LINKED_RESPONSE_BYTES = 8 * 1024 * 1024

DIAGNOSTIC_KEYS = {
    "cause",
    "code",
    "description",
    "error",
    "error_code",
    "error_type",
    "execution_id",
    "http_status",
    "message",
    "model",
    "name",
    "node",
    "node_name",
    "node_type",
    "provider",
    "reason",
    "request_id",
    "status",
    "status_code",
    "statuscode",
    "subcode",
    "trace_id",
    "type",
    "workflow_status",
}
IDENTIFIER_KEYS = {"execution_id", "request_id", "trace_id"}
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{12,}"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;\"']+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def redact(value: str) -> tuple[str, int]:
    result = value.replace("\x00", " ")
    count = 0
    for pattern in SECRET_PATTERNS:
        result, replacements = pattern.subn("[REDACTED_SECRET]", result)
        count += replacements
    result = re.sub(r"\s+", " ", result).strip()
    return result[:1000], count


def parse_status(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and 100 <= value <= 599:
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit() and 100 <= int(stripped) <= 599:
            return int(stripped)
        match = re.search(r"(?<!\d)([1-5]\d\d)(?!\d)", stripped)
        if match:
            return int(match.group(1))
    return None


def diagnostic_facts(value: Any, limit: int = 80) -> tuple[list[dict[str, str]], int]:
    facts: list[dict[str, str]] = []
    redactions = 0
    queue: deque[tuple[str, Any, int]] = deque([("$", value, 0)])
    while queue and len(facts) < limit:
        pointer, current, depth = queue.popleft()
        if depth > 8:
            continue
        if isinstance(current, dict):
            for key, child in current.items():
                normalized = str(key).lower().replace("-", "_")
                child_pointer = f"{pointer}.{key}"
                if normalized in DIAGNOSTIC_KEYS and isinstance(
                    child, (str, int, float, bool)
                ):
                    raw = str(child)
                    if normalized in IDENTIFIER_KEYS:
                        rendered = f"sha256:{sha256_text(raw)}"
                    else:
                        rendered, count = redact(raw)
                        redactions += count
                    facts.append(
                        {"path": child_pointer, "key": normalized, "value": rendered}
                    )
                elif isinstance(child, (dict, list)):
                    queue.append((child_pointer, child, depth + 1))
        elif isinstance(current, list):
            for index, child in enumerate(current):
                if isinstance(child, (dict, list)):
                    queue.append((f"{pointer}[{index}]", child, depth + 1))
    return facts, redactions


def scalar_values(value: Any, wanted_key: str, limit: int = 20) -> list[str]:
    found: list[str] = []
    queue: deque[Any] = deque([value])
    while queue and len(found) < limit:
        current = queue.popleft()
        if isinstance(current, dict):
            for key, child in current.items():
                if key == wanted_key and isinstance(child, (str, int, float)):
                    found.append(str(child))
                elif isinstance(child, (dict, list)):
                    queue.append(child)
        elif isinstance(current, list):
            queue.extend(current)
    return found


def status_from_evidence(row: dict[str, Any], facts: list[dict[str, str]]) -> int | None:
    # Preserve the client-observed workflow boundary when the index records it.
    # Nested provider/node status values remain in diagnostic_facts for causal
    # classification but must not silently replace an observed HTTP 500.
    for key in ("http_status", "status_code", "status", "workflow_status", "error"):
        candidate = parse_status(row.get(key))
        if candidate is not None:
            return candidate
    for fact in facts:
        if fact["key"] in {"http_status", "status_code", "statuscode", "status"}:
            candidate = parse_status(fact["value"])
            if candidate is not None:
                return candidate
    return None


def classify_evidence(
    status: int | None, evidence_text: str, facts: list[dict[str, str]]
) -> tuple[str, str, list[str]]:
    text = evidence_text.lower()
    matches: list[str] = []

    def has(pattern: str, label: str) -> bool:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.append(label)
            return True
        return False

    if status == 429 or has(
        r"rate.?limit|too many requests|resource_exhausted|quota[_ ]exceeded",
        "explicit rate-limit evidence",
    ):
        return "provider_rate_limit", "high", matches
    if status in (401, 403) or has(
        r"invalid[_ -]?api[_ -]?key|unauthori[sz]ed|authentication failed",
        "explicit authentication/authorization evidence",
    ):
        return "authentication_or_authorisation", "high", matches
    if status == 504 or has(
        r"timed? out|timeout|deadline exceeded|etimedout|gateway timeout",
        "explicit timeout evidence",
    ):
        return "timeout", "high", matches
    if has(
        r"job stalled|worker (?:lost|crash|unavailable)|queue unavailable|redis (?:error|unavailable)|bullmq",
        "explicit queue/worker evidence",
    ):
        return "n8n_queue_or_worker", "high", matches
    if has(
        r"econnreset|econnrefused|enotfound|socket hang up|connection reset|dns failure|empty reply",
        "explicit transport evidence",
    ):
        return "network_or_transport", "high", matches

    keys = {fact["key"] for fact in facts}
    provider_marker = bool(
        {"provider", "subcode", "error_type"} & keys
        or re.search(r"openai|anthropic|deepseek|mistral|provider api", text)
    )
    if status is not None and 500 <= status <= 599 and provider_marker and has(
        r"server[_ ]error|internal[_ ]server[_ ]error|api[_ ]error|upstream",
        "provider-marked upstream 5xx evidence",
    ):
        return "provider_upstream_5xx", "high", matches
    node_keys_present = bool({"node", "node_name", "node_type"} & keys)
    node_specific_text = has(
        r"nodeexecutionerror|error (?:in|at) node|node [^.;]{0,80} failed|workflow execution failed at",
        "explicit n8n node evidence",
    )
    if node_keys_present or node_specific_text:
        return "n8n_workflow_or_node", "high", matches
    has(
        r"error in workflow|problem executing workflow|127\.0\.0\.1:5678/webhook",
        "generic n8n webhook boundary only",
    )
    if status is not None and 500 <= status <= 599:
        return "unresolved_http_5xx", "unresolved", matches
    if status is not None and 400 <= status <= 499:
        return "other_http_4xx", "medium", matches
    return "unknown", "unresolved", matches


def classify(row: dict[str, Any]) -> tuple[str, int | None, str]:
    """Compatibility helper used by unit tests and one-off JSON diagnostics."""
    facts, _ = diagnostic_facts(row)
    status = status_from_evidence(row, facts)
    text, _ = redact(canonical_json(row))
    category, _, _ = classify_evidence(status, text, facts)
    return category, status, text[:500]


def parse_timestamp(value: str) -> dt.datetime | None:
    raw = value.strip()
    if not raw:
        return None
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def cell_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("scenario_id", "")).upper(),
        str(row.get("retrieval_mode", "")).upper(),
        str(row.get("repeat", "")),
    )


def portable_path(path: Path, experiment_dir: Path, n8n_root: Path) -> str:
    resolved = path.resolve()
    for base, prefix in ((experiment_dir.resolve(), "experiment"), (n8n_root.resolve(), "n8n")):
        try:
            return f"{prefix}/{resolved.relative_to(base).as_posix()}"
        except ValueError:
            continue
    return path.name


def resolve_linked_path(
    raw: str, experiment_dir: Path, n8n_root: Path
) -> tuple[Path | None, list[str]]:
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
    allowed_roots = (experiment_dir.resolve(), n8n_root.resolve())
    checked: list[str] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if not any(resolved == root or resolved.is_relative_to(root) for root in allowed_roots):
            continue
        label = portable_path(resolved, experiment_dir, n8n_root)
        if label in checked:
            continue
        checked.append(label)
        if resolved.is_file():
            return resolved, checked
    return None, checked


def load_linked_response(path: Path) -> tuple[Any, str, str | None]:
    if path.stat().st_size > MAX_LINKED_RESPONSE_BYTES:
        return {}, "size_limited", "linked file exceeds 8 MiB diagnostic read limit"
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(text), "json", None
    except json.JSONDecodeError:
        rendered, _ = redact(text)
        return {"message": rendered}, "text", None


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def burst_summary(timestamps: list[dt.datetime], gap_seconds: float = 60.0) -> dict[str, Any]:
    ordered = sorted(timestamps)
    if not ordered:
        return {"timestamped_failures": 0, "burst_count": 0, "max_burst_size": 0}
    bursts: list[list[dt.datetime]] = [[ordered[0]]]
    for timestamp in ordered[1:]:
        if (timestamp - bursts[-1][-1]).total_seconds() <= gap_seconds:
            bursts[-1].append(timestamp)
        else:
            bursts.append([timestamp])
    return {
        "timestamped_failures": len(ordered),
        "gap_threshold_sec": gap_seconds,
        "burst_count": len(bursts),
        "max_burst_size": max(map(len, bursts)),
        "burst_size_distribution": dict(sorted(Counter(map(len, bursts)).items())),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def manuscript_statement(summary: dict[str, Any]) -> str:
    total = summary["failed_attempts"]
    unique = summary["failed_unique_cells"]
    recovered = summary["eventually_recovered_unique_cells"]
    unresolved = summary["unresolved_attempts"]
    categories = summary["root_cause_category_counts"]
    shared_success = summary["linked_response_evidence"][
        "shared_paths_with_success_retry"
    ]
    matched_success = summary["linked_response_evidence"][
        "matches_success_report_hash"
    ]
    if unresolved == total:
        cause = (
            "All retained failure rows expose only an HTTP-500 response from the "
            "local n8n webhook with the generic body `Error in workflow`; they "
            "contain no failure-time provider subcode, request/trace identifier, "
            "timeout exception, or n8n node/worker error. "
            f"Moreover, {shared_success}/{total} linked response paths are reused "
            "by later successful retries and "
            f"{matched_success}/{total} currently contain the successful report "
            "hash, so those payloads are excluded from causal diagnosis. The "
            "underlying provider-side versus n8n-internal root cause is unresolved."
        )
    else:
        resolved = ", ".join(
            f"{name}={count}"
            for name, count in categories.items()
            if name not in {"unresolved_http_5xx", "unknown"}
        )
        cause = (
            f"Diagnostic fields support these attempt-level categories: {resolved}. "
            f"{unresolved} attempt(s) remain unresolved and are not causally attributed."
        )
    recovery = (
        f"The {total} failed attempts affected {unique} unique benchmark cells; "
        f"{recovered}/{unique} cells subsequently produced a retained successful "
        "response under the same frozen scenario/mode/repeat key."
    )
    return f"{cause} {recovery} Failed attempts remain outside accuracy denominators."


def analyze(
    experiment_dir: Path,
    n8n_root: Path,
    output_dir: Path,
    *,
    expected_failures: int = EXPECTED_FAILURES,
    expected_successes: int = EXPECTED_SUCCESSES,
    strict_source_hashes: bool = True,
) -> dict[str, Any]:
    experiment_dir = experiment_dir.resolve()
    n8n_root = n8n_root.resolve()
    failed_path = experiment_dir / "run_index_failed_attempts.csv"
    success_path = experiment_dir / "run_index_success_matrix.csv"
    final_summary_path = experiment_dir / "final_attempt_summary.json"
    for path in (failed_path, success_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    source_hashes = {
        "run_index_failed_attempts.csv": sha256_file(failed_path),
        "run_index_success_matrix.csv": sha256_file(success_path),
    }
    if final_summary_path.is_file():
        source_hashes["final_attempt_summary.json"] = sha256_file(final_summary_path)
    expected_hashes = {
        "run_index_failed_attempts.csv": EXPECTED_FAILED_INDEX_SHA256,
        "run_index_success_matrix.csv": EXPECTED_SUCCESS_INDEX_SHA256,
        "final_attempt_summary.json": EXPECTED_FINAL_SUMMARY_SHA256,
    }
    hash_matches = {
        name: source_hashes.get(name) == expected
        for name, expected in expected_hashes.items()
    }
    if strict_source_hashes and not all(hash_matches.values()):
        mismatches = [name for name, matches in hash_matches.items() if not matches]
        raise ValueError(f"frozen source SHA-256 mismatch/missing: {mismatches}")

    failures = load_csv(failed_path)
    successes = load_csv(success_path)
    if len(failures) != expected_failures:
        raise ValueError(f"expected {expected_failures} failed attempts; found {len(failures)}")
    if len(successes) != expected_successes:
        raise ValueError(f"expected {expected_successes} successful cells; found {len(successes)}")
    success_by_cell = {cell_key(row): row for row in successes}
    if len(success_by_cell) != len(successes):
        raise ValueError("successful index contains duplicate scenario/mode/repeat cells")

    details: list[dict[str, Any]] = []
    redaction_count = 0
    response_found = response_missing = response_json = response_text = 0
    response_shared_with_success = response_matches_success_report = 0
    causally_eligible_responses = excluded_response_facts = 0
    diagnostic_key_counts: Counter[str] = Counter()
    excluded_diagnostic_key_counts: Counter[str] = Counter()
    failure_times: list[dt.datetime] = []
    by_cell: defaultdict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for index, row in enumerate(failures):
        key = cell_key(row)
        success = success_by_cell.get(key)
        row_facts, redactions = diagnostic_facts(row)
        redaction_count += redactions
        linked: dict[str, Any] = {
            "provided": bool(row.get("response_file", "").strip()),
            "found": False,
        }
        response_facts: list[dict[str, str]] = []
        raw_response_file = row.get("response_file", "").strip()
        raw_success_response_file = (
            str(success.get("response_file", "")).strip() if success else ""
        )
        success_response_path = None
        if raw_success_response_file:
            success_response_path, _ = resolve_linked_path(
                raw_success_response_file, experiment_dir, n8n_root
            )
        if raw_response_file:
            response_path, checked = resolve_linked_path(
                raw_response_file, experiment_dir, n8n_root
            )
            linked["checked_paths"] = checked
            if response_path is not None:
                response_found += 1
                payload, payload_format, read_error = load_linked_response(response_path)
                response_facts, response_redactions = diagnostic_facts(payload)
                redaction_count += response_redactions
                shared_with_success = bool(
                    success_response_path is not None
                    and response_path.resolve() == success_response_path.resolve()
                )
                success_report_hash = (
                    str(success.get("report_hash", "")).strip() if success else ""
                )
                matches_success_report = bool(
                    shared_with_success
                    and success_report_hash
                    and success_report_hash in scalar_values(payload, "report_hash")
                )
                causal_eligible = not shared_with_success
                if shared_with_success:
                    response_shared_with_success += 1
                    excluded_response_facts += len(response_facts)
                    excluded_diagnostic_key_counts.update(
                        fact["key"] for fact in response_facts
                    )
                else:
                    causally_eligible_responses += 1
                if matches_success_report:
                    response_matches_success_report += 1
                linked.update(
                    {
                        "found": True,
                        "path": portable_path(response_path, experiment_dir, n8n_root),
                        "bytes": response_path.stat().st_size,
                        "sha256": sha256_file(response_path),
                        "format": payload_format,
                        "read_error": read_error,
                        "shared_path_with_success_retry": shared_with_success,
                        "matches_success_report_hash": matches_success_report,
                        "causal_diagnostic_eligible": causal_eligible,
                        "provenance": (
                            "eventual_success_artifact"
                            if matches_success_report
                            else (
                                "shared_cell_path_with_success_retry"
                                if shared_with_success
                                else "failure_specific_path"
                            )
                        ),
                        "exclusion_reason": (
                            "The failed and successful indexes reuse this cell-scoped "
                            "path; its current contents cannot be attributed to the "
                            "earlier failed attempt."
                            if shared_with_success
                            else None
                        ),
                    }
                )
                if payload_format == "json":
                    response_json += 1
                elif payload_format == "text":
                    response_text += 1
            else:
                response_missing += 1

        eligible_response_facts = (
            response_facts
            if linked.get("causal_diagnostic_eligible", False)
            else []
        )
        facts = row_facts + eligible_response_facts
        diagnostic_key_counts.update(fact["key"] for fact in facts)
        status = status_from_evidence(row, facts)
        evidence_text = " ".join(fact["value"] for fact in facts)
        category, confidence, matches = classify_evidence(status, evidence_text, facts)
        failure_time = parse_timestamp(str(row.get("timestamp_utc", "")))
        success_time = (
            parse_timestamp(str(success.get("timestamp_utc", ""))) if success else None
        )
        if failure_time is not None:
            failure_times.append(failure_time)
        recovery_delay = None
        if failure_time is not None and success_time is not None:
            difference = (success_time - failure_time).total_seconds()
            if difference >= 0:
                recovery_delay = difference
        safe_error, count = redact(str(row.get("error", "")))
        redaction_count += count
        detail = {
            "schema": "zktrustllm.tnsm.http_failure_record.v3",
            "failure_index": index,
            "source_row_sha256": sha256_text(canonical_json(row)),
            "scenario_id": key[0],
            "retrieval_mode": key[1],
            "repeat": key[2],
            "run_id_sha256": sha256_text(str(row.get("run_id", ""))),
            "timestamp_utc": row.get("timestamp_utc", ""),
            "surface_http_status": status,
            "root_cause_category": category,
            "attribution_confidence": confidence,
            "attribution_evidence": matches,
            "error_excerpt": safe_error[:500],
            "diagnostic_facts": facts,
            "linked_response": linked,
            "eventually_succeeded": success is not None,
            "success_run_id_sha256": (
                sha256_text(str(success.get("run_id", ""))) if success else None
            ),
            "success_timestamp_utc": success.get("timestamp_utc", "") if success else None,
            "recovery_delay_sec": recovery_delay,
        }
        details.append(detail)
        by_cell[key].append(detail)

    recovery_rows: list[dict[str, Any]] = []
    for key, attempts in sorted(by_cell.items()):
        attempts.sort(key=lambda item: str(item["timestamp_utc"]))
        for ordinal, item in enumerate(attempts, 1):
            item["failure_ordinal_within_cell"] = ordinal
            item["failures_for_cell"] = len(attempts)
        delays = [
            float(item["recovery_delay_sec"])
            for item in attempts
            if item["recovery_delay_sec"] is not None
        ]
        recovery_rows.append(
            {
                "scenario_id": key[0],
                "retrieval_mode": key[1],
                "repeat": key[2],
                "failed_attempts": len(attempts),
                "eventually_succeeded": any(item["eventually_succeeded"] for item in attempts),
                "last_failure_to_success_sec": min(delays) if delays else "",
            }
        )

    category_counts = Counter(item["root_cause_category"] for item in details)
    unresolved = category_counts["unresolved_http_5xx"] + category_counts["unknown"]
    recovered_cells = sum(bool(row["eventually_succeeded"]) for row in recovery_rows)
    recovery_delays = [
        float(item["recovery_delay_sec"])
        for item in details
        if item["recovery_delay_sec"] is not None
    ]
    summary: dict[str, Any] = {
        "schema": "zktrustllm.tnsm.http_failure_analysis.v3",
        "experiment_id": EXPERIMENT_ID,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "provider_calls_made": False,
        "read_only_source_analysis": True,
        "frozen_source_hashes": source_hashes,
        "frozen_source_hash_matches": hash_matches,
        "strict_source_hashes": strict_source_hashes,
        "failed_attempts": len(failures),
        "successful_cells": len(successes),
        "total_retained_attempts": len(failures) + len(successes),
        "pre_retry_failure_fraction": len(failures) / (len(failures) + len(successes)),
        "failed_unique_cells": len(by_cell),
        "eventually_recovered_unique_cells": recovered_cells,
        "eventual_cell_recovery_rate": recovered_cells / len(by_cell) if by_cell else None,
        "root_cause_category_counts": dict(sorted(category_counts.items())),
        "unresolved_attempts": unresolved,
        "root_cause_resolved": unresolved == 0,
        "linked_response_evidence": {
            "paths_provided": sum(bool(row.get("response_file", "").strip()) for row in failures),
            "files_found": response_found,
            "files_missing": response_missing,
            "json_files": response_json,
            "text_files": response_text,
            "shared_paths_with_success_retry": response_shared_with_success,
            "matches_success_report_hash": response_matches_success_report,
            "causally_eligible_files": causally_eligible_responses,
            "excluded_diagnostic_fact_count": excluded_response_facts,
            "diagnostic_key_counts": dict(sorted(diagnostic_key_counts.items())),
            "excluded_success_artifact_key_counts": dict(
                sorted(excluded_diagnostic_key_counts.items())
            ),
        },
        "temporal_bursts": burst_summary(failure_times),
        "recovery_delay_sec": {
            "count": len(recovery_delays),
            "median": statistics.median(recovery_delays) if recovery_delays else None,
            "p95": percentile(recovery_delays, 0.95),
            "min": min(recovery_delays) if recovery_delays else None,
            "max": max(recovery_delays) if recovery_delays else None,
        },
        "privacy": {
            "raw_linked_responses_copied": False,
            "run_and_request_identifiers_hashed": True,
            "credential_like_values_redacted": redaction_count,
        },
        "analysis_complete": (
            len(failures) == expected_failures
            and len(successes) == expected_successes
            and len(details) == expected_failures
            and (all(hash_matches.values()) if strict_source_hashes else True)
        ),
        "method_note": (
            "A bare HTTP 5xx identifies the observed workflow boundary only. "
            "Provider, timeout, n8n node, queue/worker, or transport attribution is "
            "made only when a failure-specific retained diagnostic field supplies "
            "explicit evidence. Cell-scoped response files shared with a later "
            "successful retry are inventoried but excluded from causal classification."
        ),
    }
    summary["manuscript_ready_statement"] = manuscript_statement(summary)

    output_dir.mkdir(parents=True, exist_ok=False)
    atomic_write_text(
        output_dir / "http_failure_records.jsonl",
        "".join(canonical_json(row) + "\n" for row in details),
    )
    atomic_write_text(
        output_dir / "http_failure_summary.json",
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
    )
    category_rows = [
        {
            "root_cause_category": category,
            "attempt_count": count,
            "fraction_of_failed_attempts": count / len(failures),
            "fraction_of_all_attempts": count / (len(failures) + len(successes)),
        }
        for category, count in sorted(category_counts.items())
    ]
    write_csv(
        output_dir / "failure_category_summary.csv",
        [
            "root_cause_category",
            "attempt_count",
            "fraction_of_failed_attempts",
            "fraction_of_all_attempts",
        ],
        category_rows,
    )
    write_csv(
        output_dir / "retry_recovery_by_cell.csv",
        [
            "scenario_id",
            "retrieval_mode",
            "repeat",
            "failed_attempts",
            "eventually_succeeded",
            "last_failure_to_success_sec",
        ],
        recovery_rows,
    )
    markdown = "\n".join(
        [
            "# Frozen R10 HTTP-failure analysis",
            "",
            f"- Frozen failed index: {'PASS' if hash_matches['run_index_failed_attempts.csv'] else 'FAIL'}",
            f"- Frozen success index: {'PASS' if hash_matches['run_index_success_matrix.csv'] else 'FAIL'}",
            f"- Failed attempts: {len(failures)} / {len(failures) + len(successes)} "
            f"({100 * summary['pre_retry_failure_fraction']:.1f}% before retry)",
            f"- Failed unique cells: {len(by_cell)}",
            f"- Eventually recovered cells: {recovered_cells} / {len(by_cell)}",
            f"- Root-cause categories: `{json.dumps(dict(sorted(category_counts.items())))}`",
            f"- Linked response files found: {response_found}",
            f"- Linked paths reused by successful retries: {response_shared_with_success}",
            f"- Linked files matching successful report hashes: {response_matches_success_report}",
            f"- Failure-specific linked files eligible for causal diagnosis: {causally_eligible_responses}",
            f"- Root cause fully resolved: {'YES' if summary['root_cause_resolved'] else 'NO'}",
            "",
            "## Manuscript-ready statement",
            "",
            summary["manuscript_ready_statement"],
            "",
            "## Interpretation boundary",
            "",
            summary["method_note"],
            "",
        ]
    )
    atomic_write_text(output_dir / "http_failure_summary.md", markdown)
    source_manifest = {
        "schema": "zktrustllm.tnsm.http_failure_source_manifest.v2",
        "experiment_id": EXPERIMENT_ID,
        "experiment_directory_name": experiment_dir.name,
        "n8n_root_name": n8n_root.name,
        "source_hashes": source_hashes,
        "source_hash_matches": hash_matches,
        "source_files_modified": False,
        "provider_calls_made": False,
        "analyzer_sha256": sha256_file(Path(__file__).resolve()),
    }
    atomic_write_text(
        output_dir / "source_manifest.json",
        json.dumps(source_manifest, indent=2, sort_keys=True) + "\n",
    )
    return summary


def load(path: Path) -> list[dict[str, Any]]:
    """Retain the original JSON/JSONL one-off loader for compatibility."""
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        for key in ("attempts", "records", "rows"):
            if isinstance(value.get(key), list):
                return [row for row in value[key] if isinstance(row, dict)]
        return [value]
    raise ValueError("expected JSON object/list or JSONL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path)
    parser.add_argument("--n8n-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--expected-failures", type=int, default=EXPECTED_FAILURES)
    parser.add_argument("--expected-successes", type=int, default=EXPECTED_SUCCESSES)
    parser.add_argument("--no-strict-source-hashes", action="store_true")
    parser.add_argument("--input", type=Path, help="legacy one-off JSON/JSONL mode")
    parser.add_argument("--output", type=Path, help="legacy one-off JSON output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.input or args.output:
        if not args.input or not args.output:
            raise SystemExit("legacy mode requires both --input and --output")
        rows = load(args.input)
        details = []
        counts: Counter[str] = Counter()
        for index, row in enumerate(rows):
            category, status, excerpt = classify(row)
            counts[category] += 1
            details.append(
                {
                    "index": index,
                    "category": category,
                    "http_status": status,
                    "evidence_excerpt": excerpt,
                }
            )
        unresolved = counts["unresolved_http_5xx"] + counts["unknown"]
        result = {
            "schema": "zktrustllm.tnsm.http_failure_analysis.v1",
            "attempt_records": len(rows),
            "category_counts": dict(sorted(counts.items())),
            "root_cause_resolved": unresolved == 0,
            "method_note": (
                "Bare HTTP 5xx codes are retained as unresolved boundary failures "
                "and are not attributed without supporting fields."
            ),
            "details": details,
        }
        atomic_write_text(args.output, json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({key: value for key, value in result.items() if key != "details"}, indent=2))
        return
    if not args.experiment_dir or not args.n8n_root or not args.output_dir:
        raise SystemExit(
            "frozen R10 mode requires --experiment-dir, --n8n-root, and --output-dir"
        )
    result = analyze(
        args.experiment_dir,
        args.n8n_root,
        args.output_dir,
        expected_failures=args.expected_failures,
        expected_successes=args.expected_successes,
        strict_source_hashes=not args.no_strict_source_hashes,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
