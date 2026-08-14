#!/usr/bin/env python3
"""Produce a fail-closed completion gate for the TNSM revision."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "docs" / "journal" / "tnsm_revision_20260808"


def load(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--journal-source", type=Path)
    parser.add_argument("--external-baseline", type=Path)
    parser.add_argument("--open-weights", type=Path)
    parser.add_argument("--injection-score", type=Path)
    parser.add_argument("--human-labels", type=Path)
    parser.add_argument("--model-metadata-audit", type=Path)
    parser.add_argument("--zenodo-doi", default="")
    parser.add_argument("--headshot", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline = load(args.external_baseline)
    open_weights = load(args.open_weights)
    injection = load(args.injection_score)
    humans = load(args.human_labels)
    metadata = load(args.model_metadata_audit)
    open_weights_overall = (
        open_weights.get("overall")
        if open_weights and isinstance(open_weights.get("overall"), dict)
        else {}
    )
    open_weights_safety_metrics_present = all(
        key in open_weights_overall
        for key in (
            "policy_bypass_count",
            "unsafe_execution_count",
            "guardrail_bypass_count",
            "unauthorized_automatic_execution_count",
        )
    )
    required_package_files = [
        PACKAGE / "main_text_dropins.tex",
        PACKAGE / "references_additions.bib",
        PACKAGE / "cover_letter.md",
        PACKAGE / "submission_checklist.md",
        PACKAGE / "verified_audit_results_20260814.json",
        PACKAGE / "figures" / "human_gate_state_machine.tex",
        PACKAGE / "figures" / "five_stage_pipeline.tex",
        PACKAGE / "figures" / "composite_oracle_results.tex",
        PACKAGE / "figures" / "composite_cost_stress.tex",
    ]
    gates = {
        "revision_package_present": all(path.is_file() for path in required_package_files),
        "current_journal_source_present": bool(args.journal_source and args.journal_source.is_file()),
        "external_baseline_180_live": bool(
            baseline
            and baseline.get("publication_eligible") is True
            and baseline.get("input_rows") == 180
        ),
        "open_weights_single_mode_live": bool(
            open_weights
            and open_weights.get("schema") == "zktrustllm.tnsm.open_weights_baseline.v2"
            and open_weights.get("publication_eligible") is True
            and open_weights.get("input_rows") == 180
            and open_weights.get("selected_rows") == 60
            and open_weights.get("retrieval_mode") == "AGENTIC_RAG"
            and bool(open_weights.get("model_digest"))
            and open_weights_safety_metrics_present
        ),
        "injection_suite_30_fail_closed": bool(
            injection
            and injection.get("schema")
            == "zktrustllm.tnsm.prompt_injection_score.v2"
            and injection.get("scored_cases") == 30
            and injection.get("publication_ready") is True
            and injection.get("pass_fail_closed") is True
            and injection.get("end_to_end_unsafe_execution_count") == 0
        ),
        "human_label_subset_30_complete": bool(
            humans and humans.get("n") == 30 and humans.get("publication_ready") is True
        ),
        "model_metadata_publication_ready": bool(
            metadata and metadata.get("publication_ready") is True
        ),
        "zenodo_doi_minted": bool(
            re.fullmatch(r"10\.5281/zenodo\.\d+", args.zenodo_doi.strip(), re.IGNORECASE)
        ),
        "three_author_headshots_present": len(args.headshot) == 3
        and all(path.is_file() for path in args.headshot),
    }
    report = {
        "schema": "zktrustllm.tnsm.revision_gate.v1",
        "submission_ready": all(gates.values()),
        "gates": gates,
        "blocking_gates": [name for name, passed in gates.items() if not passed],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["submission_ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
