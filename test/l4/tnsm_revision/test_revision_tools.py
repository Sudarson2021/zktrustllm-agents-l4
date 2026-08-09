#!/usr/bin/env python3
"""Offline unit tests for the TNSM completion gates."""
from __future__ import annotations

import importlib.util
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "scripts" / "l4" / "tnsm_revision"


def load_module(name: str):
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RevisionToolsTest(unittest.TestCase):
    def test_frozen_oracle_export_excludes_target_leakage(self) -> None:
        module = load_module("export_frozen_oracle")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            n8n_root = root / "n8n"
            experiment = n8n_root / "runtime" / "experiments" / module.EXPERIMENT_ID
            scenarios_dir = n8n_root / "scenarios" / "configs"
            responses_dir = experiment / "responses"
            scenarios_dir.mkdir(parents=True)
            responses_dir.mkdir(parents=True)

            labels = {
                "S1": ("COMPLIANT", "HUMAN"),
                "S2": ("NON_COMPLIANT", "HUMAN"),
                "S3": ("NON_COMPLIANT", "HUMAN"),
                "S4": ("NON_COMPLIANT", "NEVER"),
                "S5": ("NON_COMPLIANT", "NEVER"),
                "S6": ("UNCERTAIN", "HUMAN"),
            }
            manifest_scenarios = []
            for scenario_id, (filename, _) in module.EXPECTED_SCENARIO_FILES.items():
                configuration = {"scenario_id": scenario_id, "component": "O-RAN"}
                (scenarios_dir / filename).write_text(
                    json.dumps(configuration) + "\n", encoding="utf-8"
                )
                decision, action = labels[scenario_id]
                manifest_scenarios.append(
                    {
                        "scenario_id": scenario_id,
                        "oracle_decision": decision,
                        "oracle_action_class": action,
                    }
                )
            (experiment / "oracle_scenario_manifest.json").write_text(
                json.dumps({"scenarios": manifest_scenarios, "expert_verified": False}) + "\n",
                encoding="utf-8",
            )

            fieldnames = [
                "experiment_id",
                "phase",
                "scenario_id",
                "scenario_title",
                "retrieval_mode",
                "repeat",
                "ground_truth_decision",
                "ground_truth_action_class",
                "expert_verified",
                "run_id",
                "report_hash",
                "execution_mode",
                "workflow_status",
                "wall_clock_sec",
                "timestamp_utc",
                "response_file",
                "status",
                "error",
            ]
            index_rows = []
            for scenario_id, (decision, action) in labels.items():
                for mode in module.EXPECTED_MODES:
                    for repeat in range(1, 11):
                        run_id = f"{scenario_id}-{mode}-{repeat}"
                        report_hash = hashlib.sha256(run_id.encode()).hexdigest()
                        chunks = [] if mode == "NO_RAG" else [
                            {
                                "chunk_id": "c1",
                                "document": "synthetic",
                                "text": "frozen evidence",
                                "chunk_hash": hashlib.sha256(b"frozen evidence").hexdigest(),
                            }
                        ]
                        report = {
                            "run_id": run_id,
                            "report_hash": report_hash,
                            "metadata": {
                                "scenario_id": scenario_id,
                                "retrieval_mode": mode,
                                "expected_oracle_decision": decision,
                                "expected_oracle_action_class": action,
                            },
                            "retrieval": {
                                "bundle_hash": hashlib.sha256((run_id + "bundle").encode()).hexdigest(),
                                "grounding_available": bool(chunks),
                                "query": {"retrieval_mode": mode, "query_text": "security"},
                                "chunks": chunks,
                            },
                            "providers": {"model": {"assessment": {"decision": decision}}},
                            "policy": {"decision": decision, "enforced_action_class": action},
                        }
                        response = responses_dir / f"{run_id}.json"
                        response.write_text(json.dumps(report) + "\n", encoding="utf-8")
                        index_rows.append(
                            {
                                "experiment_id": module.EXPERIMENT_ID,
                                "phase": "oracle",
                                "scenario_id": scenario_id,
                                "scenario_title": scenario_id,
                                "retrieval_mode": mode,
                                "repeat": repeat,
                                "ground_truth_decision": decision,
                                "ground_truth_action_class": action,
                                "expert_verified": "false",
                                "run_id": run_id,
                                "report_hash": report_hash,
                                "execution_mode": "LIVE",
                                "workflow_status": "ANCHORED",
                                "wall_clock_sec": "1.0",
                                "timestamp_utc": "2026-01-01T00:00:00Z",
                                "response_file": f"responses/{response.name}",
                                "status": "SUCCESS",
                                "error": "",
                            }
                        )
            with (experiment / "run_index_success_matrix.csv").open(
                "w", newline="", encoding="utf-8"
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(index_rows)

            output = root / "canonical.jsonl"
            export_manifest = root / "export_manifest.json"
            probe = root / "probe.json"
            result = module.export_oracle(
                experiment,
                n8n_root,
                output,
                export_manifest,
                probe,
                strict_source_hashes=False,
            )
            self.assertEqual(result["canonical_jsonl"]["rows"], 180)
            self.assertTrue(result["canonical_validation"]["valid"])
            first = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
            prompt = json.loads(first["scenario"])
            self.assertNotIn("oracle_decision", prompt)
            self.assertNotIn("providers", prompt)
            self.assertNotIn("policy", prompt)
            self.assertEqual(prompt["retrieval_mode"], "NO_RAG")
            self.assertEqual(prompt["retrieval_evidence"]["chunks"], [])

    def test_canonical_oracle_contract(self) -> None:
        module = load_module("preflight_experiments")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "oracle.jsonl"
            rows = []
            for scenario_number in range(1, 7):
                for mode in ("NO_RAG", "RAG", "AGENTIC_RAG"):
                    for repeat in range(1, 11):
                        rows.append(
                            {
                                "cell_id": f"S{scenario_number}-{mode}-{repeat}",
                                "scenario_id": f"S{scenario_number}",
                                "retrieval_mode": mode,
                                "repeat": repeat,
                                "scenario": "frozen synthetic scenario",
                                "oracle_decision": "NON_COMPLIANT",
                                "oracle_action_class": "HUMAN",
                            }
                        )
            source.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            result = module.validate_canonical_oracle(source)
            self.assertTrue(result["valid"], result["reasons"])
            self.assertEqual(result["rows"], 180)
            self.assertEqual(result["mode_counts"]["AGENTIC_RAG"], 60)

    def test_kappa(self) -> None:
        module = load_module("analyze_human_labels")
        perfect = module.cohen_kappa(["A", "B", "A"], ["A", "B", "A"])
        self.assertEqual(perfect["cohen_kappa"], 1.0)
        self.assertEqual(perfect["agreement"], 1.0)

    def test_bare_500_remains_unresolved(self) -> None:
        module = load_module("analyze_http_failures")
        category, status, _ = module.classify({"http_status": 500})
        self.assertEqual(category, "unresolved_http_5xx")
        self.assertEqual(status, 500)

    def test_langgraph_mock_is_not_publication_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source = work / "oracle.jsonl"
            output = work / "result.json"
            source.write_text(
                json.dumps(
                    {
                        "cell_id": "c1",
                        "scenario_id": "S4",
                        "retrieval_mode": "NO_RAG",
                        "repeat": 1,
                        "scenario": "synthetic test",
                        "oracle_decision": "NON_COMPLIANT",
                        "oracle_action_class": "NEVER",
                        "mock_response": {
                            "decision": "NON_COMPLIANT",
                            "action_class": "NEVER",
                            "execute": False,
                            "rationale": "test",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "python3",
                    str(TOOLS / "run_langgraph_baseline.py"),
                    "--input",
                    str(source),
                    "--output",
                    str(output),
                    "--mock",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(summary["publication_eligible"])
            self.assertTrue(summary["pilot"])
            self.assertTrue(summary["complete"])
            self.assertEqual(summary["selected_rows"], 1)
            self.assertEqual(summary["overall"]["unsafe_execution_count"], 0)
            self.assertEqual(summary["overall"]["policy_bypass_count"], 0)

            evidence = work / "result_evidence"
            record = json.loads(
                (evidence / "records.jsonl").read_text(encoding="utf-8").strip()
            )
            self.assertEqual(record["client_request_id"], "mock")
            self.assertEqual(record["requested_model"], "mock")
            self.assertEqual(record["final_prediction"]["action_class"], "NEVER")

    def test_langgraph_fail_closed_coerces_nonautomatic_execution(self) -> None:
        module = load_module("run_langgraph_baseline")
        parsed = module.parse_candidate(
            json.dumps(
                {
                    "decision": "NON_COMPLIANT",
                    "action_class": "NEVER",
                    "execute": True,
                    "rationale": "synthetic adversarial response",
                }
            )
        )
        self.assertTrue(parsed["execute"])
        prediction, coerced = module.fail_closed_prediction(True, parsed)
        self.assertTrue(coerced)
        self.assertFalse(prediction["execute"])
        self.assertEqual(prediction["action_class"], "NEVER")
        self.assertIn("untrusted data", module.SYSTEM_PROMPT)
        self.assertFalse(module.OUTPUT_SCHEMA["additionalProperties"])

    def test_injection_generator_has_thirty_cases(self) -> None:
        module = load_module("generate_prompt_injection_suite")
        self.assertEqual(len(module.BASE_CONTEXTS) * len(module.ATTACKS), 30)


if __name__ == "__main__":
    unittest.main()
