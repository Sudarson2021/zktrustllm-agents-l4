#!/usr/bin/env python3
"""Audit model-run records for snapshot and decoding reproducibility metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


REQUIRED = (
    "returned_model_id",
    "accessed_at",
    "temperature",
    "top_p",
    "max_tokens",
    "system_prompt_sha256",
)
MUTABLE_MARKERS = ("latest", "medium", "pro", "chat")


def json_values(path: Path) -> Iterable[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    yield value
    else:
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
        elif isinstance(value, dict):
            yield value


def model_fields(record: dict[str, Any]) -> list[tuple[str, Any]]:
    fields = []
    for key in ("requested_model", "model", "provider_model", "model_id"):
        if record.get(key) not in (None, ""):
            fields.append((key, record[key]))
    fields.extend(
        (key, value)
        for key, value in record.items()
        if key.endswith("_model") and value not in (None, "")
    )
    # Preserve order but avoid reporting the same key twice.
    return list(dict.fromkeys(fields))


def candidate_records(value: Any, locator: str = "$") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        if model_fields(value) or value.get("returned_model_id"):
            yield locator, value
        for key, child in value.items():
            yield from candidate_records(child, f"{locator}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from candidate_records(child, f"{locator}[{index}]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    files = []
    for path in args.paths:
        if path.is_dir():
            files.extend(sorted(item for item in path.rglob("*.json*") if item.is_file()))
        else:
            files.append(path)
    findings = []
    seen = set()
    for path in files:
        try:
            values = list(json_values(path))
        except (OSError, json.JSONDecodeError) as error:
            findings.append({"path": str(path), "locator": "$", "error": str(error), "missing": list(REQUIRED)})
            continue
        for root_index, root in enumerate(values):
            for locator, record in candidate_records(root, f"$[{root_index}]"):
                models = model_fields(record) or [("returned_model_id", record.get("returned_model_id"))]
                for model_key, requested_model in models:
                    finding_locator = f"{locator}.{model_key}"
                    key = (str(path), finding_locator)
                    if key in seen:
                        continue
                    seen.add(key)
                    prefix = model_key[: -len("_model")] if model_key.endswith("_model") else ""
                    returned = (
                        record.get(f"{prefix}_returned_model_id") if prefix else None
                    ) or record.get("returned_model_id")
                    values = {
                        "returned_model_id": returned,
                        "accessed_at": record.get("accessed_at") or record.get("timestamp_utc"),
                        "temperature": record.get("temperature"),
                        "top_p": record.get("top_p"),
                        "max_tokens": record.get("max_tokens"),
                        "system_prompt_sha256": record.get("system_prompt_sha256"),
                    }
                    missing = [field for field in REQUIRED if values[field] is None]
                    mutable = bool(returned) and any(marker in str(returned).lower() for marker in MUTABLE_MARKERS)
                    findings.append(
                        {
                            "path": str(path),
                            "locator": finding_locator,
                            "requested_model": requested_model,
                            "returned_model_id": returned,
                            "missing": missing,
                            "returned_id_appears_mutable": mutable,
                            "ready": not missing and not mutable,
                        }
                    )
    summary = {
        "schema": "zktrustllm.tnsm.model_metadata_audit.v1",
        "files_scanned": len(set(files)),
        "candidate_records": len(findings),
        "ready_records": sum(bool(row.get("ready")) for row in findings),
        "publication_ready": bool(findings) and all(bool(row.get("ready")) for row in findings),
        "required_fields": list(REQUIRED),
        "findings": findings,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "findings"}, indent=2))
    if not summary["publication_ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
