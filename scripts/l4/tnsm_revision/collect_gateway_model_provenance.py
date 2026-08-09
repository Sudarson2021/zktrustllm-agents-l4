#!/usr/bin/env python3
"""Collect a secret-safe provenance bundle for the deployed R10 gateway source."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any


EXPECTED_SOURCE_HASHES = {
    "gateway/app.py": "952fbbf87d1fc59a9e600718c9cf5ff6d2bc5c3eb24a3673a5203322921ed65e",
    "runtime/workflow_backups/gateway_app_before_action_reconciliation_20260716T000456Z.py": "35cc16a5919a0defb5ec7ff85698bc7b092e74b2d1ddab40d9984e42a0e7d865",
    "runtime/workflow_backups/gateway_app_before_action_reconciliation_20260716T000850Z.py": "35cc16a5919a0defb5ec7ff85698bc7b092e74b2d1ddab40d9984e42a0e7d865",
    "runtime/workflow_backups/gateway_app_before_clause_fix_20260715T233154Z.py": "f06280e0564736a17df130d17f1109e2d99aa6d3cb344e260afe02e5ad034003",
    "runtime/workflow_backups/gateway_app_before_deepseek_channel_fix_20260715T234855Z.py": "b64b59890f0c05d95b8136408addfd59e16c362208cfff006b7f0a90aaf0cc46",
    "runtime/workflow_backups/gateway_app_before_policy_variable_fix_20260716T003006Z.py": "e3f2fa548616574f8a02271affc8a4aa17a26212f7f8627aad0f160adf3eeb71",
    "scripts/update_env_v2.py": "12ce47773fb257571d96443691064857ef158f3e50521f744b9e4cee90d8ca5b",
}
EXPERIMENT_FILES = (
    "protocol.json",
    "live_preflight.json",
    "final_attempt_summary.json",
)
SENSITIVE_KEY_RE = re.compile(
    r"(?:api[_-]?key|password|passphrase|authorization|credential|private[_-]?key|"
    r"client[_-]?secret|access[_-]?token|refresh[_-]?token)$",
    re.IGNORECASE,
)
TOKEN_LITERAL_RE = re.compile(
    r"\b(?:sk-(?:proj-|ant-)?|gh[pousr]_|hf_|xai-)[A-Za-z0-9_-]{12,}\b"
)
ASSIGNMENT_SECRET_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|password|passphrase|authorization|credential|"
    r"private[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token)\b"
    r"\s*[:=]\s*)(['\"])(.*?)(\2)"
)
PEM_RE = re.compile(
    r"-----BEGIN [^-]*(?:PRIVATE KEY|SECRET)[^-]*-----.*?"
    r"-----END [^-]*(?:PRIVATE KEY|SECRET)[^-]*-----",
    re.DOTALL | re.IGNORECASE,
)
SAFE_ENV_RE = re.compile(
    r"^(?:(?:OPENAI|ANTHROPIC|DEEPSEEK|MISTRAL)_MODEL|"
    r"(?:OPENAI|ANTHROPIC|DEEPSEEK|MISTRAL|LLM|PROVIDER)_"
    r"(?:MAX_(?:OUTPUT_|COMPLETION_)?TOKENS|TEMPERATURE|TOP_P|TOP_K|"
    r"REASONING_EFFORT|SEED))$"
)
RELEVANT_NAME_RE = re.compile(
    r"(?:OPENAI|ANTHROPIC|DEEPSEEK|MISTRAL|MODEL|PROMPT|SYSTEM|TEMPERATURE|"
    r"TOP_P|TOP_K|MAX_.*TOKENS|REASONING|GATEWAY_VERSION)",
    re.IGNORECASE,
)
PROMPT_NAME_RE = re.compile(r"(?:PROMPT|SYSTEM|INSTRUCTION)", re.IGNORECASE)
REQUEST_KEYS = {
    "model",
    "input",
    "messages",
    "system",
    "instructions",
    "temperature",
    "top_p",
    "top_k",
    "max_tokens",
    "max_output_tokens",
    "max_completion_tokens",
    "reasoning",
    "seed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def redact_text(value: str) -> tuple[str, int]:
    redactions = 0

    def replace_token(match: re.Match[str]) -> str:
        nonlocal redactions
        redactions += 1
        return "<REDACTED_TOKEN>"

    def replace_assignment(match: re.Match[str]) -> str:
        nonlocal redactions
        redactions += 1
        return f"{match.group(1)}{match.group(2)}<REDACTED>{match.group(4)}"

    def replace_pem(_: re.Match[str]) -> str:
        nonlocal redactions
        redactions += 1
        return "<REDACTED_PRIVATE_MATERIAL>"

    value = TOKEN_LITERAL_RE.sub(replace_token, value)
    value = ASSIGNMENT_SECRET_RE.sub(replace_assignment, value)
    value = PEM_RE.sub(replace_pem, value)
    return value, redactions


def sanitize_json(value: Any) -> tuple[Any, int]:
    redactions = 0
    if isinstance(value, dict):
        output = {}
        for key, child in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                output[key] = "<REDACTED>"
                redactions += 1
            else:
                output[key], count = sanitize_json(child)
                redactions += count
        return output, redactions
    if isinstance(value, list):
        output = []
        for child in value:
            item, count = sanitize_json(child)
            output.append(item)
            redactions += count
        return output, redactions
    if isinstance(value, str):
        return redact_text(value)
    return value, 0


def target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [ast.unparse(node)]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [name for item in node.elts for name in target_names(item)]
    return []


def literal_or_expression(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return {"expression": ast.unparse(node)}


def enclosing_function(tree: ast.AST) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                mapping[id(child)] = node.name
    return mapping


def python_inventory(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    owners = enclosing_function(tree)
    environment_reads: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    payloads: list[dict[str, Any]] = []
    prompts: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = ast.unparse(node.func)
            if function.endswith(("getenv", "environ.get")) and node.args:
                name = literal_or_expression(node.args[0])
                default = literal_or_expression(node.args[1]) if len(node.args) > 1 else None
                if isinstance(name, str) and RELEVANT_NAME_RE.search(name):
                    environment_reads.append(
                        {
                            "name": name,
                            "default": default,
                            "line": getattr(node, "lineno", None),
                            "function": owners.get(id(node)),
                        }
                    )
        if isinstance(node, ast.Assign):
            names = [name for target in node.targets for name in target_names(target)]
            for name in names:
                if RELEVANT_NAME_RE.search(name):
                    assignments.append(
                        {
                            "name": name,
                            "value": literal_or_expression(node.value),
                            "line": getattr(node, "lineno", None),
                            "function": owners.get(id(node)),
                        }
                    )
                try:
                    prompt_value = ast.literal_eval(node.value)
                except (ValueError, TypeError, SyntaxError):
                    prompt_value = None
                if (
                    isinstance(prompt_value, str)
                    and PROMPT_NAME_RE.search(name)
                    and len(prompt_value.strip()) >= 20
                ):
                    prompts.append(
                        {
                            "name": name,
                            "line": getattr(node, "lineno", None),
                            "function": owners.get(id(node)),
                            "sha256": sha256_text(prompt_value),
                            "value": prompt_value,
                        }
                    )
        if isinstance(node, ast.AnnAssign):
            names = target_names(node.target)
            for name in names:
                if RELEVANT_NAME_RE.search(name) and node.value is not None:
                    assignments.append(
                        {
                            "name": name,
                            "value": literal_or_expression(node.value),
                            "line": getattr(node, "lineno", None),
                            "function": owners.get(id(node)),
                        }
                    )
        if isinstance(node, ast.Dict):
            mapping: dict[str, Any] = {}
            for key_node, value_node in zip(node.keys, node.values):
                if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                    mapping[key_node.value] = literal_or_expression(value_node)
            selected = {key: mapping[key] for key in REQUEST_KEYS & set(mapping)}
            if selected and ("model" in selected or len(selected) >= 2):
                payloads.append(
                    {
                        "line": getattr(node, "lineno", None),
                        "function": owners.get(id(node)),
                        "fields": dict(sorted(selected.items())),
                    }
                )

    def unique(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        output = []
        for item in items:
            marker = json.dumps(item, sort_keys=True)
            if marker not in seen:
                seen.add(marker)
                output.append(item)
        return sorted(output, key=lambda item: (item.get("line") or 0, json.dumps(item, sort_keys=True)))

    return {
        "environment_reads": unique(environment_reads),
        "relevant_assignments": unique(assignments),
        "provider_request_payloads": unique(payloads),
        "static_prompts": unique(prompts),
    }


def env_allowlist(n8n_root: Path) -> dict[str, Any]:
    files = []
    values: dict[str, dict[str, str]] = {}
    for path in sorted(n8n_root.glob(".env*")):
        if not path.is_file():
            continue
        relative = path.name
        files.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "contents_copied": False,
            }
        )
        safe: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            if SAFE_ENV_RE.fullmatch(key):
                clean = value.strip().strip("'\"")
                if TOKEN_LITERAL_RE.search(clean):
                    raise ValueError(f"safe allowlist unexpectedly matched a credential value: {key}")
                safe[key] = clean
        if safe:
            values[relative] = dict(sorted(safe.items()))
    return {"environment_files": files, "allowlisted_values": values}


def write_sanitized_source(
    source: Path, relative: str, output_dir: Path
) -> tuple[dict[str, Any], Path]:
    text = source.read_text(encoding="utf-8", errors="strict")
    sanitized, redactions = redact_text(text)
    if TOKEN_LITERAL_RE.search(sanitized) or PEM_RE.search(sanitized):
        raise ValueError(f"credential-like material remains after redaction: {source}")
    destination = output_dir / "sanitized_sources" / f"{relative}.txt"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(sanitized, encoding="utf-8")
    stat = source.stat()
    return (
        {
            "path": relative,
            "original_sha256": sha256_file(source),
            "sanitized_sha256": sha256_file(destination),
            "bytes": stat.st_size,
            "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "redaction_count": redactions,
        },
        destination,
    )


def collect(
    n8n_root: Path,
    experiment_dir: Path,
    output_dir: Path,
    strict_source_hashes: bool = True,
) -> dict[str, Any]:
    n8n_root = n8n_root.expanduser().resolve()
    experiment_dir = experiment_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    source_manifest = []
    ast_inventory = {}
    for relative, expected in EXPECTED_SOURCE_HASHES.items():
        path = n8n_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"required source file not found: {path}")
        observed = sha256_file(path)
        if strict_source_hashes and observed != expected:
            raise ValueError(
                f"{relative} SHA-256 mismatch: expected {expected}, observed {observed}"
            )
        record, _ = write_sanitized_source(path, relative, output_dir)
        record["expected_sha256"] = expected
        record["hash_matches_stage7a"] = observed == expected
        source_manifest.append(record)
        if path.suffix == ".py":
            ast_inventory[relative] = python_inventory(path)

    experiment_manifest = []
    for filename in EXPERIMENT_FILES:
        path = experiment_dir / filename
        if not path.is_file():
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        sanitized, redactions = sanitize_json(value)
        destination = output_dir / "sanitized_experiment" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(sanitized, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        experiment_manifest.append(
            {
                "path": filename,
                "original_sha256": sha256_file(path),
                "sanitized_sha256": sha256_file(destination),
                "redaction_count": redactions,
                "raw_provider_responses_copied": False,
            }
        )

    environment = env_allowlist(n8n_root)
    (output_dir / "python_ast_inventory.json").write_text(
        json.dumps(ast_inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "environment_allowlist.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema": "zktrustllm.tnsm.gateway_model_provenance.v1",
        "generated_at": utc_now(),
        "provider_calls_made": False,
        "source_files": source_manifest,
        "experiment_files": experiment_manifest,
        "environment": environment,
        "credentials_copied": False,
        "raw_provider_responses_copied": False,
        "claim_boundary": (
            "This bundle identifies and sanitizes the current deployed source and pre-run "
            "backups. Hash agreement with Stage 7A establishes source continuity, but the R10 "
            "reports did not retain a source hash or commit; settings are not attributed to R10 "
            "until prompt/configuration consistency is independently demonstrated."
        ),
    }
    (output_dir / "gateway_model_provenance.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n8n-root", type=Path, required=True)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--no-strict-source-hashes", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = collect(
        args.n8n_root,
        args.experiment_dir,
        args.output_dir,
        strict_source_hashes=not args.no_strict_source_hashes,
    )
    primary = next(row for row in result["source_files"] if row["path"] == "gateway/app.py")
    inventory = json.loads(
        (args.output_dir.expanduser().resolve() / "python_ast_inventory.json").read_text(
            encoding="utf-8"
        )
    )["gateway/app.py"]
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "provider_calls_made": result["provider_calls_made"],
                "gateway_source_sha256": primary["original_sha256"],
                "gateway_hash_matches_stage7a": primary["hash_matches_stage7a"],
                "source_files": len(result["source_files"]),
                "experiment_files": len(result["experiment_files"]),
                "environment_files": len(result["environment"]["environment_files"]),
                "allowlisted_environment_files": len(
                    result["environment"]["allowlisted_values"]
                ),
                "environment_reads": len(inventory["environment_reads"]),
                "request_payloads": len(inventory["provider_request_payloads"]),
                "static_prompts": len(inventory["static_prompts"]),
                "credentials_copied": result["credentials_copied"],
                "raw_provider_responses_copied": result["raw_provider_responses_copied"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
