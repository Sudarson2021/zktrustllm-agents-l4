#!/usr/bin/env python3
"""Reconstruct and hash-verify the R10 assessor prompts and request settings.

This stage is read-only and makes no provider call.  It uses each retained
report's input hash and prompt hash as acceptance tests: a configuration
serialization and a pre-run gateway prompt builder are accepted only when they
reproduce the retained values exactly.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

import audit_model_metadata as model_audit
import collect_gateway_model_provenance as gateway_probe
import export_frozen_oracle as oracle_export


SCHEMA = "zktrustllm.tnsm.r10_prompt_provenance.v1"
PROVIDERS = ("openai", "anthropic", "deepseek", "mistral")


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


def ast_hash(node: ast.AST) -> str:
    return sha256_text(ast.dump(node, include_attributes=False))


def function_node(source: str, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = ast.parse(source)
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one top-level {name} function; found {len(matches)}")
    return matches[0]


class ReconstructionHTTPException(Exception):
    """Non-network placeholder used by the isolated prompt function."""


def compile_prompt_builder(source: str) -> tuple[Callable[[dict[str, Any]], tuple[str, str]], str]:
    node = function_node(source, "assessment_prompt")
    segment = ast.get_source_segment(source, node)
    if not segment:
        raise ValueError("could not extract assessment_prompt source")
    namespace: dict[str, Any] = {
        "Any": Any,
        "HTTPException": ReconstructionHTTPException,
        "canonical_json": canonical_json,
    }
    exec(compile(segment, "<verified-assessment-prompt>", "exec"), namespace)
    return namespace["assessment_prompt"], ast_hash(node)


def string_values(value: Any, location: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield location, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from string_values(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from string_values(child, f"{location}[{index}]")


def configuration_candidates(
    scenario_path: Path, response_payload: Any
) -> dict[str, list[dict[str, Any]]]:
    raw = scenario_path.read_text(encoding="utf-8")
    configuration = json.loads(raw)
    candidates: list[tuple[str, str]] = [
        ("scenario_file:raw", raw),
        ("scenario_file:strip", raw.strip()),
        ("scenario_file:rstrip_newline", raw.rstrip("\r\n")),
    ]
    for sort_keys in (False, True):
        for ensure_ascii in (False, True):
            prefix = f"json_dumps:sort={str(sort_keys).lower()}:ascii={str(ensure_ascii).lower()}"
            candidates.extend(
                [
                    (
                        f"{prefix}:compact",
                        json.dumps(
                            configuration,
                            sort_keys=sort_keys,
                            separators=(",", ":"),
                            ensure_ascii=ensure_ascii,
                        ),
                    ),
                    (
                        f"{prefix}:default",
                        json.dumps(
                            configuration,
                            sort_keys=sort_keys,
                            ensure_ascii=ensure_ascii,
                        ),
                    ),
                    (
                        f"{prefix}:indent2",
                        json.dumps(
                            configuration,
                            sort_keys=sort_keys,
                            indent=2,
                            ensure_ascii=ensure_ascii,
                        ),
                    ),
                ]
            )
    for location, value in string_values(response_payload):
        candidates.append((f"response_string:{location}", value))

    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for origin, value in candidates:
        marker = (origin, value)
        if marker in seen:
            continue
        seen.add(marker)
        by_hash[sha256_text(value)].append(
            {"origin": origin, "value": value, "bytes": len(value.encode("utf-8"))}
        )
    return dict(by_hash)


def provider_branch(test: ast.AST) -> str | None:
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return None
    if not isinstance(test.ops[0], ast.Eq):
        return None
    left, right = test.left, test.comparators[0]
    if isinstance(left, ast.Name) and left.id == "provider" and isinstance(right, ast.Constant):
        return str(right.value)
    return None


def dict_fields(node: ast.AST) -> dict[str, str]:
    if not isinstance(node, ast.Dict):
        return {}
    output = {}
    for key, value in zip(node.keys, node.values):
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            output[key.value] = ast.unparse(value)
    return output


def request_decoding_inventory(source: str) -> tuple[dict[str, Any], str]:
    node = function_node(source, "call_provider")
    default_max_tokens: Any = None
    for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        if argument.arg == "max_tokens" and default is not None:
            default_max_tokens = ast.literal_eval(default)

    branches: dict[str, dict[str, str]] = {}
    chain = next(
        (
            item
            for item in ast.walk(node)
            if isinstance(item, ast.If) and provider_branch(item.test) is not None
        ),
        None,
    )
    while isinstance(chain, ast.If):
        provider = provider_branch(chain.test)
        if provider:
            for child in chain.body:
                if isinstance(child, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "body"
                    for target in child.targets
                ):
                    branches[provider] = dict_fields(child.value)
                    break
        chain = chain.orelse[0] if len(chain.orelse) == 1 and isinstance(chain.orelse[0], ast.If) else None

    if set(branches) != set(PROVIDERS):
        raise ValueError(f"call_provider branches incomplete: {sorted(branches)}")
    parameter_names = ("temperature", "top_p", "top_k")
    providers = {}
    for provider in PROVIDERS:
        fields = branches[provider]
        token_field = next(
            (name for name in ("max_tokens", "max_output_tokens", "max_completion_tokens") if name in fields),
            None,
        )
        providers[provider] = {
            "request_fields": sorted(fields),
            "max_token_field": token_field,
            "max_token_value": default_max_tokens if token_field and fields[token_field] == "max_tokens" else None,
            "temperature": "NOT_SENT" if "temperature" not in fields else fields["temperature"],
            "top_p": "NOT_SENT" if "top_p" not in fields else fields["top_p"],
            "top_k": "NOT_SENT" if "top_k" not in fields else fields["top_k"],
            "provider_default_values_claimed": False,
        }
        if any(name in fields for name in parameter_names):
            providers[provider]["provider_default_values_claimed"] = False
    return {
        "call_provider_default_max_tokens": default_max_tokens,
        "providers": providers,
        "interpretation": (
            "NOT_SENT means the request payload omitted the parameter; no provider-side default "
            "or deterministic decoding value is inferred. DeepSeek also omitted a maximum-token field."
        ),
    }, ast_hash(node)


def load_source_candidates(
    n8n_root: Path, strict_source_hashes: bool
) -> list[dict[str, Any]]:
    candidates = []
    for relative, expected_hash in gateway_probe.EXPECTED_SOURCE_HASHES.items():
        if not relative.endswith(".py") or relative == "scripts/update_env_v2.py":
            continue
        path = n8n_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"required source candidate not found: {path}")
        observed_hash = sha256_file(path)
        if strict_source_hashes and observed_hash != expected_hash:
            raise ValueError(
                f"{relative} SHA-256 mismatch: expected {expected_hash}, observed {observed_hash}"
            )
        source = path.read_text(encoding="utf-8")
        builder, prompt_function_hash = compile_prompt_builder(source)
        decoding, call_provider_hash = request_decoding_inventory(source)
        assess_hash = ast_hash(function_node(source, "assess"))
        candidates.append(
            {
                "path": relative,
                "source_sha256": observed_hash,
                "source_hash_matches_pin": observed_hash == expected_hash,
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "prompt_function_ast_sha256": prompt_function_hash,
                "call_provider_ast_sha256": call_provider_hash,
                "assess_function_ast_sha256": assess_hash,
                "builder": builder,
                "decoding": decoding,
            }
        )
    return candidates


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def reconstruct(
    n8n_root: Path,
    experiment_dir: Path,
    output_dir: Path,
    expected_successes: int = 180,
    strict_source_hashes: bool = True,
) -> dict[str, Any]:
    n8n_root = n8n_root.expanduser().resolve()
    experiment_dir = experiment_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    index_path = experiment_dir / "run_index_success_matrix.csv"
    observed_index_hash = sha256_file(index_path)
    if strict_source_hashes and observed_index_hash != oracle_export.EXPECTED_SUCCESS_INDEX_SHA256:
        raise ValueError("R10 success-index SHA-256 mismatch")
    with index_path.open(newline="", encoding="utf-8-sig") as handle:
        index_rows = list(csv.DictReader(handle))
    if len(index_rows) != expected_successes:
        raise ValueError(f"expected {expected_successes} successful cells; found {len(index_rows)}")

    source_candidates = load_source_candidates(n8n_root, strict_source_hashes)
    scenario_paths = {
        scenario_id: n8n_root / "scenarios" / "configs" / filename
        for scenario_id, (filename, _) in oracle_export.EXPECTED_SCENARIO_FILES.items()
    }
    if not strict_source_hashes and expected_successes != 180:
        scenario_paths = {
            str(row.get("scenario_id", "")): n8n_root / "scenarios" / "configs" / str(row.get("scenario_file", ""))
            for row in index_rows
            if row.get("scenario_file")
        } or scenario_paths

    source_match_counts = Counter()
    system_prompts: dict[str, dict[str, Any]] = {}
    provider_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    reconstruction_rows = []
    resolved_input_hashes: dict[str, tuple[str, dict[str, Any]]] = {}

    for row in index_rows:
        scenario_id = str(row.get("scenario_id", "")).upper()
        mode = str(row.get("retrieval_mode", "")).upper()
        repeat = int(row.get("repeat", "0"))
        response_path = model_audit.resolve_response_path(
            str(row.get("response_file", "")), experiment_dir, n8n_root
        )
        response_payload = json.loads(response_path.read_text(encoding="utf-8"))
        report = model_audit.find_report_for_row(
            response_payload, str(row.get("report_hash", "")), response_path
        )
        input_hash = str(report.get("input_hash", ""))
        prompt_hashes = {
            str(record.get("prompt_hash", ""))
            for provider, record in (report.get("providers") or {}).items()
            if provider in PROVIDERS
        }
        if len(prompt_hashes) != 1 or "" in prompt_hashes:
            raise ValueError(f"{scenario_id}/{mode}/R{repeat:02d}: provider prompt hashes disagree")
        retained_prompt_hash = next(iter(prompt_hashes))

        if input_hash not in resolved_input_hashes:
            scenario_path = scenario_paths.get(scenario_id)
            if not scenario_path or not scenario_path.is_file():
                raise FileNotFoundError(f"scenario source missing for {scenario_id}: {scenario_path}")
            if strict_source_hashes:
                expected_scenario_hash = oracle_export.EXPECTED_SCENARIO_FILES[scenario_id][1]
                if sha256_file(scenario_path) != expected_scenario_hash:
                    raise ValueError(f"scenario-file SHA-256 mismatch for {scenario_id}")
            matches = configuration_candidates(scenario_path, response_payload).get(input_hash, [])
            values = {candidate["value"] for candidate in matches}
            if len(values) != 1:
                raise ValueError(
                    f"{scenario_id}: input_hash {input_hash} resolves to {len(values)} configuration values"
                )
            value = next(iter(values))
            evidence = {
                "input_hash": input_hash,
                "bytes": len(value.encode("utf-8")),
                "origins": sorted({candidate["origin"] for candidate in matches}),
                "scenario_file": scenario_path.relative_to(n8n_root).as_posix(),
                "scenario_file_sha256": sha256_file(scenario_path),
            }
            resolved_input_hashes[input_hash] = (value, evidence)
        config_text, config_evidence = resolved_input_hashes[input_hash]

        run = {
            "scenario": report.get("scenario") or row.get("scenario_title"),
            "metadata_json": report.get("metadata") or {"retrieval_mode": mode},
            "retrieval_json": report.get("retrieval") or {},
            "input_text": config_text,
            "input_hash": input_hash,
        }
        matching_sources = []
        for source in source_candidates:
            system, user = source["builder"](run)
            candidate_hash = sha256_text(canonical_json({"system": system, "user": user}))
            if candidate_hash == retained_prompt_hash:
                matching_sources.append(source["path"])
                source_match_counts[source["path"]] += 1
                prompt_key = sha256_text(system)
                system_prompts[prompt_key] = {
                    "sha256": prompt_key,
                    "bytes": len(system.encode("utf-8")),
                    "retrieval_modes": sorted(
                        set(system_prompts.get(prompt_key, {}).get("retrieval_modes", [])) | {mode}
                    ),
                    "text": system,
                }
        if not matching_sources:
            raise ValueError(
                f"{scenario_id}/{mode}/R{repeat:02d}: no pinned source reproduced {retained_prompt_hash}"
            )

        for provider in PROVIDERS:
            provider_record = (report.get("providers") or {}).get(provider)
            if not isinstance(provider_record, dict):
                raise ValueError(f"{scenario_id}/{mode}/R{repeat:02d}: missing {provider}")
            provider_rows[provider].append(provider_record)
        reconstruction_rows.append(
            {
                "cell_id": f"{scenario_id}:{mode}:R{repeat:02d}",
                "run_id": str(report.get("run_id", "")),
                "report_hash": str(report.get("report_hash", "")),
                "input_hash": input_hash,
                "input_serialization_origins": config_evidence["origins"],
                "retained_prompt_hash": retained_prompt_hash,
                "matching_sources": sorted(matching_sources),
                "match": True,
            }
        )

    timestamps = [
        parse_time(str(record.get("created_at")))
        for records in provider_rows.values()
        for record in records
        if record.get("created_at")
    ]
    earliest_call = min(timestamps)
    complete_sources = [
        source
        for source in source_candidates
        if source_match_counts[source["path"]] == expected_successes
    ]
    pre_run_sources = [
        source for source in complete_sources if parse_time(source["mtime_utc"]) <= earliest_call
    ]
    if not pre_run_sources:
        raise ValueError("no pre-run source candidate reproduced all retained prompt hashes")
    selected = max(pre_run_sources, key=lambda source: parse_time(source["mtime_utc"]))

    provider_summary = {}
    for provider in PROVIDERS:
        records = provider_rows[provider]
        accessed = sorted(str(record.get("created_at")) for record in records if record.get("created_at"))
        provider_summary[provider] = {
            "records": len(records),
            "retained_model_ids": dict(sorted(Counter(str(record.get("model_id", "")) for record in records).items())),
            "accessed_at_range": [accessed[0], accessed[-1]],
            "provider_request_ids_present": sum(bool(record.get("provider_request_id")) for record in records),
            "raw_response_hashes_present": sum(bool(record.get("raw_response_hash")) for record in records),
            "identifier_boundary": (
                "model_id is the requested gateway alias; no separately returned immutable provider snapshot was retained."
            ),
            **selected["decoding"]["providers"][provider],
        }

    source_inventory = []
    for source in source_candidates:
        source_inventory.append(
            {key: value for key, value in source.items() if key not in {"builder", "decoding"}}
            | {
                "matched_cells": source_match_counts[source["path"]],
                "pre_run": parse_time(source["mtime_utc"]) <= earliest_call,
            }
        )
    expected_input_hashes = len(
        {str(row.get("scenario_id", "")).upper() for row in index_rows}
    )
    expected_system_prompts = len(
        {
            "NO_RAG" if str(row.get("retrieval_mode", "")).upper() == "NO_RAG" else "GROUNDED"
            for row in index_rows
        }
    )
    summary = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "experiment_id": oracle_export.EXPERIMENT_ID,
        "provider_calls_made": False,
        "successful_cells": len(reconstruction_rows),
        "provider_records": sum(len(rows) for rows in provider_rows.values()),
        "input_hashes_resolved": len(resolved_input_hashes),
        "prompt_hash_matches": sum(row["match"] for row in reconstruction_rows),
        "full_system_prompts_recovered": len(system_prompts),
        "selected_pre_run_source": {
            key: value for key, value in selected.items() if key not in {"builder", "decoding"}
        },
        "decoding": selected["decoding"],
        "providers": provider_summary,
        "immutable_provider_snapshot_exposed": False,
        "source_index_sha256": observed_index_hash,
        "publication_ready": (
            len(reconstruction_rows) == expected_successes
            and len(resolved_input_hashes) == expected_input_hashes
            and len(system_prompts) == expected_system_prompts
            and all(len(rows) == expected_successes for rows in provider_rows.values())
        ),
        "supervisor_comment_15_resolved_with_boundary": True,
        "claim_boundary": (
            "The reconstruction binds the full assessor prompts to every retained R10 prompt hash and identifies "
            "the request fields in a timestamped pre-run source with the same prompt, dispatch, and assessor-function "
            "ASTs. Model identifiers remain requested aliases, not immutable provider snapshots. Parameters marked "
            "NOT_SENT are omissions; provider default values and deterministic sampling are not claimed."
        ),
    }
    if not summary["publication_ready"]:
        raise ValueError(f"publication gate failed: {summary}")

    with (output_dir / "r10_prompt_reconstruction.jsonl").open("w", encoding="utf-8") as handle:
        for row in reconstruction_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    (output_dir / "resolved_input_serializations.json").write_text(
        json.dumps(
            [evidence for _, evidence in resolved_input_hashes.values()],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "system_prompts.json").write_text(
        json.dumps(sorted(system_prompts.values(), key=lambda row: row["sha256"]), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "source_match_inventory.json").write_text(
        json.dumps(source_inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "r10_model_prompt_provenance.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n8n-root", type=Path, required=True)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-successes", type=int, default=180)
    parser.add_argument("--no-strict-source-hashes", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = reconstruct(
        args.n8n_root,
        args.experiment_dir,
        args.output_dir,
        expected_successes=args.expected_successes,
        strict_source_hashes=not args.no_strict_source_hashes,
    )
    print(
        json.dumps(
            {
                "schema": summary["schema"],
                "provider_calls_made": summary["provider_calls_made"],
                "successful_cells": summary["successful_cells"],
                "provider_records": summary["provider_records"],
                "input_hashes_resolved": summary["input_hashes_resolved"],
                "prompt_hash_matches": summary["prompt_hash_matches"],
                "full_system_prompts_recovered": summary["full_system_prompts_recovered"],
                "selected_pre_run_source": summary["selected_pre_run_source"]["path"],
                "publication_ready": summary["publication_ready"],
                "supervisor_comment_15_resolved_with_boundary": summary[
                    "supervisor_comment_15_resolved_with_boundary"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
