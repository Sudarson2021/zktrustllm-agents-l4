#!/usr/bin/env python3
"""Categorise HTTP/workflow failures without inferring causes from bare 500s."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def load(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        for key in ("attempts", "records", "rows"):
            if isinstance(value.get(key), list):
                return [row for row in value[key] if isinstance(row, dict)]
        return [value]
    raise ValueError("expected JSON object/list or JSONL")


def classify(row: dict[str, Any]) -> tuple[str, int | None, str]:
    status = None
    for node in walk(row):
        if isinstance(node, dict):
            for key in ("status_code", "http_status", "statusCode"):
                candidate = node.get(key)
                if isinstance(candidate, int):
                    status = candidate
                elif isinstance(candidate, str) and candidate.isdigit():
                    status = int(candidate)
    text = json.dumps(row, sort_keys=True).lower()
    if status == 429 or "rate limit" in text or "too many requests" in text:
        return "rate_limit", status, text[:500]
    if "timeout" in text or "timed out" in text:
        return "timeout", status, text[:500]
    if status in (401, 403):
        return "authentication_or_authorisation", status, text[:500]
    if status is not None and 500 <= status <= 599:
        # A bare server code identifies the boundary, not the upstream cause.
        return "unresolved_http_5xx", status, text[:500]
    if status is not None and 400 <= status <= 499:
        return "other_http_4xx", status, text[:500]
    if "connection" in text or "dns" in text or "socket" in text:
        return "network", status, text[:500]
    return "unknown", status, text[:500]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load(args.input)
    details = []
    counts: Counter[str] = Counter()
    for index, row in enumerate(rows):
        category, status, excerpt = classify(row)
        counts[category] += 1
        details.append({"index": index, "category": category, "http_status": status, "evidence_excerpt": excerpt})
    unresolved = counts["unresolved_http_5xx"] + counts["unknown"]
    summary = {
        "schema": "zktrustllm.tnsm.http_failure_analysis.v1",
        "attempt_records": len(rows),
        "category_counts": dict(sorted(counts.items())),
        "root_cause_resolved": unresolved == 0,
        "method_note": "Bare HTTP 5xx codes are retained as unresolved boundary failures and are not attributed to rate limiting, provider timeout, or n8n without supporting fields.",
        "details": details,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "details"}, indent=2))


if __name__ == "__main__":
    main()
