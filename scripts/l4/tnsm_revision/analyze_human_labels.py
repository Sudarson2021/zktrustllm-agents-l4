#!/usr/bin/env python3
"""Calculate independent-label agreement and Cohen's kappa."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def cohen_kappa(left: list[str], right: list[str]) -> dict[str, float]:
    if len(left) != len(right) or not left:
        raise ValueError("kappa inputs must have equal non-zero length")
    labels = sorted(set(left) | set(right))
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum(
        (left_counts[label] / len(left)) * (right_counts[label] / len(right))
        for label in labels
    )
    kappa = 1.0 if expected == 1.0 and observed == 1.0 else (observed - expected) / (1.0 - expected)
    return {"agreement": observed, "expected_agreement": expected, "cohen_kappa": kappa}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"cell_id", "oracle_label", "annotator_1", "annotator_2"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"CSV needs columns {sorted(required)}")
    for row in rows:
        for key in required:
            row[key] = str(row[key]).strip().upper() if key != "cell_id" else str(row[key]).strip()
        if not all(row[key] for key in required):
            raise ValueError(f"incomplete labels for {row['cell_id'] or '<blank cell>'}")
    oracle = [row["oracle_label"] for row in rows]
    ann1 = [row["annotator_1"] for row in rows]
    ann2 = [row["annotator_2"] for row in rows]
    summary = {
        "schema": "zktrustllm.tnsm.human_label_agreement.v1",
        "n": len(rows),
        "oracle_vs_annotator_1": cohen_kappa(oracle, ann1),
        "oracle_vs_annotator_2": cohen_kappa(oracle, ann2),
        "annotator_1_vs_annotator_2": cohen_kappa(ann1, ann2),
        "label_counts": {
            "oracle": dict(sorted(Counter(oracle).items())),
            "annotator_1": dict(sorted(Counter(ann1).items())),
            "annotator_2": dict(sorted(Counter(ann2).items())),
        },
        "publication_ready": len(rows) == 30,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
