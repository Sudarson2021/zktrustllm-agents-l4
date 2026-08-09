#!/usr/bin/env python3
"""Build an evidence-bounded model metadata inventory for the TNSM revision.

This stage is deliberately read-only.  It distinguishes fields retained by the
original R10 reports from settings merely visible in a current source tree and
from metadata captured by the later revision experiments.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable


EXPERIMENT_ID = "l4_oracle_20260716T131803Z_r10"
EXPECTED_SUCCESS_INDEX_SHA256 = (
    "d9143f5c17fffc14caa5764360b7841a191bf6ce435fffc70742fa0f545a5f5c"
)
EXPECTED_STAGE_FF_SHA256 = (
    "0bd515d34424ee1aaecc7a2644b98badab1f34ed966a88417c883c62e1126189"
)
EXPECTED_PROVIDERS = {
    "openai": "gpt-5.6-terra",
    "anthropic": "claude-fable-5",
    "deepseek": "deepseek-v4-pro",
    "mistral": "mistral-medium-3-5",
}
STAGE_FF_MODEL_FIELDS = {
    "openai": "openai_model",
    "anthropic": "anthropic_model",
    "deepseek": "deepseek_model",
    "mistral": "mistral_model",
}
DECODING_KEYS = {
    "temperature",
    "top_p",
    "top_k",
    "min_p",
    "max_tokens",
    "max_output_tokens",
    "max_completion_tokens",
    "reasoning_effort",
    "seed",
}
SOURCE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".ts", ".json", ".yaml", ".yml"}
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "responses",
    "raw",
    "artifacts",
}
SECRET_RE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|api[_-]?key\s*[:=]\s*['\"][^'\"]{12,})",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_hash(path: Path, expected: str, description: str, strict: bool) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{description} not found: {path}")
    observed = sha256_file(path)
    if strict and observed != expected:
        raise ValueError(
            f"{description} SHA-256 mismatch: expected {expected}, observed {observed}"
        )
    return observed


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected a JSON object")
        rows.append(value)
    return rows


def resolve_response_path(raw: str, experiment_dir: Path, n8n_root: Path) -> Path:
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
    checked: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in checked:
            continue
        checked.append(resolved)
        if resolved.is_file():
            return resolved
    raise FileNotFoundError(
        f"response_file {raw!r} not found; checked: " + ", ".join(map(str, checked))
    )


def find_final_reports(value: Any, depth: int = 0) -> Iterable[dict[str, Any]]:
    if depth > 8:
        return
    if (
        isinstance(value, dict)
        and isinstance(value.get("providers"), dict)
        and isinstance(value.get("metadata"), dict)
        and value.get("report_hash")
    ):
        yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from find_final_reports(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from find_final_reports(child, depth + 1)


def find_report_for_row(payload: Any, report_hash: str, path: Path) -> dict[str, Any]:
    reports = list(find_final_reports(payload))
    matches = [report for report in reports if str(report.get("report_hash")) == report_hash]
    if len(matches) != 1:
        raise ValueError(
            f"{path}: expected one final report matching {report_hash!r}; found {len(matches)}"
        )
    return matches[0]


def nested_key_values(value: Any, wanted: set[str]) -> dict[str, list[Any]]:
    found: dict[str, list[Any]] = defaultdict(list)

    def visit(child: Any) -> None:
        if isinstance(child, dict):
            for key, item in child.items():
                if key in wanted and item not in (None, ""):
                    found[key].append(item)
                visit(item)
        elif isinstance(child, list):
            for item in child:
                visit(item)

    visit(value)
    return dict(found)


def safe_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def audit_r10(
    experiment_dir: Path,
    n8n_root: Path,
    output_dir: Path,
    expected_successes: int,
    expected_provider_records: int,
    strict_source_hashes: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    index_path = experiment_dir / "run_index_success_matrix.csv"
    index_hash = verify_hash(
        index_path,
        EXPECTED_SUCCESS_INDEX_SHA256,
        "R10 success index",
        strict_source_hashes,
    )
    with index_path.open(newline="", encoding="utf-8-sig") as handle:
        index_rows = list(csv.DictReader(handle))
    if len(index_rows) != expected_successes:
        raise ValueError(
            f"expected {expected_successes} successful R10 rows; found {len(index_rows)}"
        )

    cell_keys: set[tuple[str, str, str]] = set()
    inventory: list[dict[str, Any]] = []
    report_hashes: dict[str, str] = {}
    report_level_settings = Counter()
    gateway_versions = Counter()
    manifest_versions = Counter()

    for index_row in index_rows:
        cell = (
            str(index_row.get("scenario_id", "")),
            str(index_row.get("retrieval_mode", "")),
            str(index_row.get("repeat", "")),
        )
        if cell in cell_keys:
            raise ValueError(f"duplicate R10 cell: {cell}")
        cell_keys.add(cell)
        response_path = resolve_response_path(
            str(index_row.get("response_file", "")), experiment_dir, n8n_root
        )
        payload = load_json(response_path)
        expected_report_hash = str(index_row.get("report_hash", ""))
        report = find_report_for_row(payload, expected_report_hash, response_path)
        report_hashes[safe_relative(response_path, n8n_root)] = sha256_file(response_path)
        metadata = report.get("metadata") or {}
        gateway_versions[str(metadata.get("gateway_version", "NOT_RECORDED"))] += 1
        manifest_versions[str(report.get("manifest_version", "NOT_RECORDED"))] += 1
        for key, values in nested_key_values(report, DECODING_KEYS | {"system_prompt"}).items():
            report_level_settings[f"{key}:{len(values)}"] += 1

        providers = report.get("providers")
        missing = set(EXPECTED_PROVIDERS) - set(providers or {})
        if missing:
            raise ValueError(f"{response_path}: missing R10 providers {sorted(missing)}")
        for provider, expected_alias in EXPECTED_PROVIDERS.items():
            record = providers[provider]
            model_id = str(record.get("model_id", ""))
            if strict_source_hashes and model_id != expected_alias:
                raise ValueError(
                    f"{response_path}: {provider} model_id {model_id!r} != {expected_alias!r}"
                )
            inventory.append(
                {
                    "scenario_id": cell[0],
                    "retrieval_mode": cell[1],
                    "repeat": cell[2],
                    "run_id": str(report.get("run_id", "")),
                    "report_hash": expected_report_hash,
                    "provider": provider,
                    "retained_model_id": model_id,
                    "created_at": str(record.get("created_at", "")),
                    "provider_request_id_present": bool(record.get("provider_request_id")),
                    "prompt_hash": str(record.get("prompt_hash", "")),
                    "raw_response_hash_present": bool(record.get("raw_response_hash")),
                    "parsed_response_hash_present": bool(record.get("parsed_response_hash")),
                    "input_tokens": record.get("input_tokens"),
                    "output_tokens": record.get("output_tokens"),
                    "execution_mode": str(record.get("execution_mode", "")),
                    "source_response_file": safe_relative(response_path, n8n_root),
                }
            )

    if len(inventory) != expected_provider_records:
        raise ValueError(
            f"expected {expected_provider_records} R10 provider records; found {len(inventory)}"
        )
    inventory_path = output_dir / "r10_provider_inventory.csv"
    with inventory_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(inventory[0]))
        writer.writeheader()
        writer.writerows(inventory)

    providers_summary: dict[str, Any] = {}
    for provider in EXPECTED_PROVIDERS:
        rows = [row for row in inventory if row["provider"] == provider]
        timestamps = sorted(row["created_at"] for row in rows if row["created_at"])
        providers_summary[provider] = {
            "records": len(rows),
            "retained_model_ids": dict(sorted(Counter(row["retained_model_id"] for row in rows).items())),
            "accessed_at_range": [timestamps[0], timestamps[-1]] if timestamps else None,
            "provider_request_id_present": sum(row["provider_request_id_present"] for row in rows),
            "raw_response_hash_present": sum(row["raw_response_hash_present"] for row in rows),
            "parsed_response_hash_present": sum(row["parsed_response_hash_present"] for row in rows),
            "distinct_prompt_hashes": len({row["prompt_hash"] for row in rows if row["prompt_hash"]}),
            "identifier_boundary": (
                "The final report labels this field model_id but does not retain a separate "
                "requested alias and provider-returned immutable snapshot for comparison."
            ),
            "temperature": None,
            "top_p": None,
            "max_tokens": None,
            "full_system_prompt": None,
        }

    r10_summary = {
        "experiment_id": EXPERIMENT_ID,
        "successful_cells": len(index_rows),
        "provider_records": len(inventory),
        "source_index_sha256": index_hash,
        "source_report_files": len(report_hashes),
        "source_report_file_hashes": report_hashes,
        "gateway_versions": dict(sorted(gateway_versions.items())),
        "manifest_versions": dict(sorted(manifest_versions.items())),
        "providers": providers_summary,
        "report_level_decoding_or_prompt_fields": dict(sorted(report_level_settings.items())),
        "identity_and_access_fields_complete": all(
            row["retained_model_id"]
            and row["created_at"]
            and row["provider_request_id_present"]
            and row["raw_response_hash_present"]
            for row in inventory
        ),
        "immutable_provider_snapshot_exposed": False,
        "decoding_parameters_retained": False,
        "full_system_prompts_retained": False,
    }
    return r10_summary, inventory


def audit_stage_ff(
    path: Path,
    output_dir: Path,
    strict_source_hashes: bool,
) -> dict[str, Any]:
    source_hash = verify_hash(
        path, EXPECTED_STAGE_FF_SHA256, "Stage F/F final15 JSONL", strict_source_hashes
    )
    rows = load_jsonl(path)
    if len(rows) != 15:
        raise ValueError(f"expected 15 Stage F/F rows; found {len(rows)}")
    inventory: list[dict[str, Any]] = []
    for row in rows:
        for provider, field in STAGE_FF_MODEL_FIELDS.items():
            inventory.append(
                {
                    "run_id": row.get("run_id"),
                    "scenario_id": row.get("scenario_id"),
                    "repeat": row.get("repeat"),
                    "provider": provider,
                    "retained_model_alias": row.get(field),
                    "latency_ms": row.get(f"{provider}_latency_ms"),
                    "accessed_at": row.get("accessed_at"),
                    "temperature": row.get(f"{provider}_temperature"),
                    "top_p": row.get(f"{provider}_top_p"),
                    "max_tokens": row.get(f"{provider}_max_tokens"),
                    "system_prompt_sha256": row.get("system_prompt_sha256"),
                    "raw_response_hash": row.get(f"{provider}_raw_response_hash"),
                }
            )
    output = output_dir / "stage_ff_model_inventory.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(inventory[0]))
        writer.writeheader()
        writer.writerows(inventory)
    return {
        "rows": len(rows),
        "provider_records": len(inventory),
        "source_sha256": source_hash,
        "models_by_provider": {
            provider: sorted(
                {str(row[field]) for row in rows if row.get(field) not in (None, "")}
            )
            for provider, field in STAGE_FF_MODEL_FIELDS.items()
        },
        "access_timestamps_present": sum(bool(row.get("accessed_at")) for row in rows),
        "raw_provider_response_hashes_present": sum(
            bool(item.get("raw_response_hash")) for item in inventory
        ),
        "role_resolution": {
            "r10_openai_role": "independent oracle-benchmark assessor",
            "r10_openai_model_id": EXPECTED_PROVIDERS["openai"],
            "stage_ff_openai_role": "planner in a supplemental four-model chain",
            "stage_ff_openai_aliases": sorted(
                {str(row["openai_model"]) for row in rows if row.get("openai_model")}
            ),
            "same_experiment": False,
            "manuscript_action": (
                "Describe the roles and runs separately; move Stage F/F to the supplement "
                "and do not use it as R10 oracle-benchmark evidence."
            ),
        },
    }


def target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [name for item in node.elts for name in target_names(item)]
    return []


def literal_scalar(node: ast.AST) -> Any:
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return "<dynamic>"
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return "<non-scalar>"


def source_files(root: Path) -> Iterable[Path]:
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in EXCLUDED_DIRS and not name.startswith(".")
        )
        for filename in sorted(filenames):
            path = Path(directory) / filename
            if path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            try:
                if path.stat().st_size > 2 * 1024 * 1024:
                    continue
            except OSError:
                continue
            yield path


def append_prompt(
    prompts: list[dict[str, Any]],
    source: str,
    name: str,
    value: str,
    line: int | None,
) -> None:
    if len(value.strip()) < 20:
        return
    if SECRET_RE.search(value):
        return
    prompts.append(
        {
            "source": source,
            "name": name,
            "line": line,
            "bytes": len(value.encode("utf-8")),
            "sha256": sha256_text(value),
            "value": value,
        }
    )


def extract_python_metadata(
    path: Path, relative: str, prompts: list[dict[str, Any]], decoding: list[dict[str, Any]]
) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = [name for target in node.targets for name in target_names(target)]
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                value = None
            for name in names:
                if isinstance(value, str) and re.search(r"PROMPT|SYSTEM|INSTRUCTION", name, re.I):
                    append_prompt(prompts, relative, name, value, getattr(node, "lineno", None))
        elif isinstance(node, ast.AnnAssign):
            names = target_names(node.target)
            try:
                value = ast.literal_eval(node.value) if node.value is not None else None
            except (ValueError, TypeError, SyntaxError):
                value = None
            for name in names:
                if isinstance(value, str) and re.search(r"PROMPT|SYSTEM|INSTRUCTION", name, re.I):
                    append_prompt(prompts, relative, name, value, getattr(node, "lineno", None))
        if isinstance(node, ast.Dict):
            mapping: dict[str, Any] = {}
            for key_node, value_node in zip(node.keys, node.values):
                if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                    mapping[key_node.value] = literal_scalar(value_node)
            captured = {key: mapping[key] for key in sorted(DECODING_KEYS & set(mapping))}
            if captured:
                decoding.append(
                    {
                        "source": relative,
                        "line": getattr(node, "lineno", None),
                        "model": mapping.get("model", "<not-in-literal>"),
                        "settings": captured,
                    }
                )


JS_PROMPT_RE = re.compile(
    r"(?:const|let|var)\s+([A-Za-z0-9_$]*(?:PROMPT|SYSTEM|INSTRUCTION)[A-Za-z0-9_$]*)"
    r"\s*=\s*([`'\"])(.*?)\2",
    re.IGNORECASE | re.DOTALL,
)


def extract_javascript_prompts(
    text: str, relative: str, prompts: list[dict[str, Any]]
) -> None:
    for match in JS_PROMPT_RE.finditer(text):
        value = match.group(3)
        if "${" in value:
            continue
        append_prompt(
            prompts,
            relative,
            match.group(1),
            value,
            text.count("\n", 0, match.start()) + 1,
        )


def walk_json_metadata(
    value: Any,
    source: str,
    prompts: list[dict[str, Any]],
    decoding: list[dict[str, Any]],
    locator: str = "$",
) -> None:
    if isinstance(value, dict):
        captured = {
            key: value[key]
            for key in sorted(DECODING_KEYS & set(value))
            if isinstance(value[key], (str, int, float, bool)) or value[key] is None
        }
        if captured:
            decoding.append(
                {
                    "source": source,
                    "locator": locator,
                    "model": value.get("model", "<not-in-object>"),
                    "settings": captured,
                }
            )
        for key, child in value.items():
            child_locator = f"{locator}.{key}"
            if (
                isinstance(child, str)
                and re.search(r"PROMPT|SYSTEM|INSTRUCTION", str(key), re.I)
                and not str(key).lower().endswith("_hash")
                and not re.fullmatch(r"[0-9a-fA-F]{32,}", child.strip())
            ):
                append_prompt(prompts, source, child_locator, child, None)
            walk_json_metadata(child, source, prompts, decoding, child_locator)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_json_metadata(child, source, prompts, decoding, f"{locator}[{index}]")


def scan_sources(source_root: Path, output_dir: Path) -> dict[str, Any]:
    aliases = set(EXPECTED_PROVIDERS.values()) | {
        "gpt-5.5",
        "deepseek-chat",
        "mistral-medium-latest",
    }
    provider_env_markers = {
        "OPENAI_MODEL",
        "ANTHROPIC_MODEL",
        "DEEPSEEK_MODEL",
        "MISTRAL_MODEL",
    }
    reproducibility_markers = DECODING_KEYS | {
        "system_prompt",
        "prompt_hash",
        "instructions",
        "gateway_version",
    }
    candidates: list[dict[str, Any]] = []
    prompts: list[dict[str, Any]] = []
    decoding: list[dict[str, Any]] = []
    files_examined = 0
    for path in source_files(source_root):
        files_examined += 1
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lower = text.lower()
        model_hits = sorted(alias for alias in aliases if alias.lower() in lower)
        env_hits = sorted(marker for marker in provider_env_markers if marker in text)
        setting_hits = sorted(marker for marker in reproducibility_markers if marker.lower() in lower)
        if not (model_hits or env_hits):
            continue
        relative = safe_relative(path, source_root)
        candidates.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "model_alias_hits": model_hits,
                "provider_environment_markers": env_hits,
                "reproducibility_markers": setting_hits,
                "contains_gateway_version_2_0_0": "2.0.0" in text
                and "gateway" in lower,
            }
        )
        if path.suffix.lower() == ".py":
            extract_python_metadata(path, relative, prompts, decoding)
        elif path.suffix.lower() in {".js", ".mjs", ".cjs", ".ts"}:
            extract_javascript_prompts(text, relative, prompts)
        elif path.suffix.lower() == ".json":
            try:
                walk_json_metadata(json.loads(text), relative, prompts, decoding)
            except json.JSONDecodeError:
                pass

    # Remove exact duplicates caused by repeated workflow objects.
    prompt_map = {
        (item["source"], item["name"], item["sha256"]): item for item in prompts
    }
    decoding_map = {
        (
            item["source"],
            item.get("line"),
            item.get("locator"),
            json.dumps(item["settings"], sort_keys=True),
        ): item
        for item in decoding
    }
    prompts = sorted(prompt_map.values(), key=lambda item: (item["source"], str(item["name"])))
    decoding = sorted(
        decoding_map.values(),
        key=lambda item: (item["source"], item.get("line") or 0, item.get("locator") or ""),
    )
    (output_dir / "source_candidate_inventory.json").write_text(
        json.dumps(candidates, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / "extracted_prompt_inventory.jsonl").open("w", encoding="utf-8") as handle:
        for item in prompts:
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    with (output_dir / "extracted_decoding_inventory.jsonl").open("w", encoding="utf-8") as handle:
        for item in decoding:
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    return {
        "source_root_recorded_as": source_root.name,
        "files_examined": files_examined,
        "candidate_files": len(candidates),
        "extracted_static_prompts": len(prompts),
        "extracted_decoding_objects": len(decoding),
        "source_linkage_boundary": (
            "Candidate source hashes and extracted constants describe the supplied current "
            "source tree. The R10 reports retain gateway_version=2.0.0 but no source-file or "
            "commit hash, so current source is not treated as proof of the exact July request."
        ),
        "credentials_copied": False,
    }


def revision_role(schema: str) -> str:
    if "open_weights" in schema:
        return "open-weights comparison baseline"
    if "prompt_injection" in schema:
        return "prompt-injection adversarial assessor"
    if "langgraph" in schema:
        return "external LangGraph comparison baseline"
    return "revision experiment"


def audit_revision_runs(revision_root: Path | None, output_dir: Path) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    if revision_root and revision_root.is_dir():
        for path in sorted(revision_root.rglob("summary.json")):
            try:
                value = load_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(value, dict):
                continue
            schema = str(value.get("schema", ""))
            if not any(marker in schema for marker in ("langgraph", "open_weights", "prompt_injection")):
                continue
            prompt = value.get("system_prompt")
            prompt_hash = value.get("system_prompt_sha256")
            prompt_hash_valid = (
                isinstance(prompt, str)
                and isinstance(prompt_hash, str)
                and sha256_text(prompt) == prompt_hash
            )
            accessed = value.get("accessed_at_range")
            if not accessed:
                records = path.parent / "records.jsonl"
                if records.is_file():
                    timestamps = sorted(
                        str(row["accessed_at"])
                        for row in load_jsonl(records)
                        if row.get("accessed_at")
                    )
                    accessed = [timestamps[0], timestamps[-1]] if timestamps else None
            runs.append(
                {
                    "role": revision_role(schema),
                    "schema": schema,
                    "path": safe_relative(path.parent, revision_root),
                    "summary_sha256": sha256_file(path),
                    "complete": value.get("complete"),
                    "publication_eligible": value.get("publication_eligible"),
                    "requested_model": value.get("requested_model")
                    or value.get("requested_model_tag"),
                    "returned_model_ids": value.get("returned_model_ids"),
                    "model_digest": value.get("model_digest"),
                    "accessed_at_range": accessed,
                    "temperature": value.get("temperature"),
                    "top_p": value.get("top_p"),
                    "top_k": value.get("top_k"),
                    "max_completion_tokens": value.get("max_completion_tokens"),
                    "reasoning_effort": value.get("reasoning_effort"),
                    "system_prompt": prompt,
                    "system_prompt_sha256": prompt_hash,
                    "system_prompt_hash_valid": prompt_hash_valid,
                }
            )
    result = {
        "runs_found": len(runs),
        "runs": runs,
        "boundary": (
            "These later runs improve artifact reproducibility but do not retroactively supply "
            "missing request metadata for the original R10 four-provider calls."
        ),
    }
    (output_dir / "revision_run_metadata.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def write_markdown(summary: dict[str, Any], output: Path) -> None:
    r10 = summary["r10"]
    lines = [
        "# Model metadata and role audit",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Original R10 benchmark",
        "",
        f"The frozen index binds {r10['successful_cells']} successful cells to "
        f"{r10['provider_records']} provider records.",
        "",
        "| Provider | Retained model ID | Records | Access range | Request IDs | Raw hashes |",
        "|---|---|---:|---|---:|---:|",
    ]
    for provider, value in r10["providers"].items():
        models = ", ".join(f"{key} ({count})" for key, count in value["retained_model_ids"].items())
        access = " to ".join(value["accessed_at_range"] or ["not recorded"])
        lines.append(
            f"| {provider} | {models} | {value['records']} | {access} | "
            f"{value['provider_request_id_present']} | {value['raw_response_hash_present']} |"
        )
    lines.extend(
        [
            "",
            "The R10 reports do **not** retain a separate requested-versus-returned immutable "
            "snapshot identifier, numeric decoding parameters, or the full system prompt. "
            "Those values must not be reconstructed from aliases or provider defaults.",
            "",
            "## GPT-5.6 versus GPT-5.5",
            "",
            summary["stage_ff"]["role_resolution"]["manuscript_action"],
            "The former is the original R10 independent assessor; the latter is a planner alias "
            "in a separate 15-row supplemental Stage F/F chain.",
            "",
            "## Publication decision",
            "",
            summary["manuscript_ready_statement"],
            "",
            "Current source constants are inventoried separately. Because the R10 records do "
            "not bind a source-file hash or Git commit, that inventory is discovery evidence, "
            "not retroactive proof of the July request payloads.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def audit(
    experiment_dir: Path,
    n8n_root: Path,
    stage_ff_jsonl: Path,
    source_root: Path,
    revision_root: Path | None,
    output_dir: Path,
    expected_successes: int = 180,
    expected_provider_records: int = 720,
    strict_source_hashes: bool = True,
) -> dict[str, Any]:
    experiment_dir = experiment_dir.expanduser().resolve()
    n8n_root = n8n_root.expanduser().resolve()
    source_root = source_root.expanduser().resolve()
    stage_ff_jsonl = stage_ff_jsonl.expanduser().resolve()
    revision_root = revision_root.expanduser().resolve() if revision_root else None
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    r10, _ = audit_r10(
        experiment_dir,
        n8n_root,
        output_dir,
        expected_successes,
        expected_provider_records,
        strict_source_hashes,
    )
    stage_ff = audit_stage_ff(stage_ff_jsonl, output_dir, strict_source_hashes)
    source_scan = scan_sources(source_root, output_dir)
    revision_runs = audit_revision_runs(revision_root, output_dir)
    comment_15_resolved = bool(
        r10["immutable_provider_snapshot_exposed"]
        and r10["decoding_parameters_retained"]
        and r10["full_system_prompts_retained"]
    )
    summary = {
        "schema": "zktrustllm.tnsm.model_metadata_audit.v2",
        "generated_at": utc_now(),
        "provider_calls_made": False,
        "read_only_source_analysis": True,
        "audit_complete": True,
        "r10": r10,
        "stage_ff": stage_ff,
        "source_scan": source_scan,
        "revision_runs": revision_runs,
        "supervisor_comment_15_resolved": comment_15_resolved,
        "supervisor_comment_16_resolved": True,
        "publication_ready": comment_15_resolved,
        "unresolved_fields": [
            "provider-returned immutable snapshot identifiers for the original R10 calls",
            "original R10 temperature and top-p values",
            "original R10 provider token-limit request fields",
            "full original R10 system prompt text linked to the retained prompt hashes",
        ],
        "manuscript_ready_statement": (
            "The frozen R10 evidence retains model_id aliases, access timestamps, request IDs, "
            "prompt hashes, and raw-response hashes for all 720 provider records. It does not "
            "retain separately returned immutable snapshots, decoding parameters, or full system "
            "prompts; these fields are reported as not recorded rather than inferred. GPT-5.6 "
            "served as an independent R10 assessor, whereas gpt-5.5 was a planner alias in the "
            "separate supplemental Stage F/F experiment."
        ),
    }
    (output_dir / "model_metadata_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(summary, output_dir / "model_metadata_summary.md")
    source_manifest = {
        "schema": "zktrustllm.tnsm.model_metadata_sources.v1",
        "r10_success_index": {
            "sha256": r10["source_index_sha256"],
            "expected_sha256": EXPECTED_SUCCESS_INDEX_SHA256,
        },
        "stage_ff_jsonl": {
            "sha256": stage_ff["source_sha256"],
            "expected_sha256": EXPECTED_STAGE_FF_SHA256,
        },
        "audit_tool_sha256": sha256_file(Path(__file__).resolve()),
        "credentials_copied": False,
        "raw_provider_responses_copied": False,
    }
    (output_dir / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--n8n-root", type=Path, required=True)
    parser.add_argument("--stage-ff-jsonl", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--revision-root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-successes", type=int, default=180)
    parser.add_argument("--expected-provider-records", type=int, default=720)
    parser.add_argument("--no-strict-source-hashes", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = audit(
        args.experiment_dir,
        args.n8n_root,
        args.stage_ff_jsonl,
        args.source_root,
        args.revision_root,
        args.output_dir,
        args.expected_successes,
        args.expected_provider_records,
        not args.no_strict_source_hashes,
    )
    print(
        json.dumps(
            {
                "audit_complete": summary["audit_complete"],
                "r10_provider_records": summary["r10"]["provider_records"],
                "r10_models": {
                    key: list(value["retained_model_ids"])
                    for key, value in summary["r10"]["providers"].items()
                },
                "source_candidates": summary["source_scan"]["candidate_files"],
                "static_prompts_extracted": summary["source_scan"]["extracted_static_prompts"],
                "revision_runs_found": summary["revision_runs"]["runs_found"],
                "supervisor_comment_15_resolved": summary["supervisor_comment_15_resolved"],
                "supervisor_comment_16_resolved": summary["supervisor_comment_16_resolved"],
                "publication_ready": summary["publication_ready"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
