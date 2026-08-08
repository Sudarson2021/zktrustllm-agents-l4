#!/usr/bin/env python3
"""Select a deterministic, label-stratified 30-cell oracle subset."""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("JSONL rows must be objects")
            rows.append(value)
    return rows


def value(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if row.get(key) not in (None, ""):
            return str(row[key])
    return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260808)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = load_rows(args.input)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source:
        cell_id = value(row, "cell_id", "id")
        label = value(row, "oracle_action_class", "oracle_action", "action_class").upper()
        if not cell_id or not label:
            raise ValueError("every input row needs cell_id and oracle action label")
        grouped[label].append(row)
    if args.size > len(source) or not grouped:
        raise ValueError("requested subset is larger than the source")
    rng = random.Random(args.seed)
    for rows in grouped.values():
        rows.sort(key=lambda row: value(row, "cell_id", "id"))
        rng.shuffle(rows)

    labels = sorted(grouped)
    allocation = {label: args.size // len(labels) for label in labels}
    for label in labels[: args.size % len(labels)]:
        allocation[label] += 1
    for label in labels:
        if allocation[label] > len(grouped[label]):
            raise ValueError(f"not enough {label} rows for allocation {allocation[label]}")

    selected = []
    for label in labels:
        for row in grouped[label][: allocation[label]]:
            selected.append(
                {
                    "cell_id": value(row, "cell_id", "id"),
                    "scenario_sha256": value(row, "scenario_sha256", "prompt_sha256"),
                    "oracle_label": label,
                    "annotator_1": "",
                    "annotator_2": "",
                }
            )
    selected.sort(key=lambda row: row["cell_id"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)
    print(json.dumps({"output": str(args.output), "rows": len(selected), "allocation": allocation}, indent=2))


if __name__ == "__main__":
    main()
