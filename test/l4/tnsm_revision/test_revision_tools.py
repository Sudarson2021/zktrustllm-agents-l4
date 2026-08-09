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
from types import SimpleNamespace
import unittest
from unittest import mock
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

    def test_langgraph_rejects_redacted_or_malformed_api_keys(self) -> None:
        module = load_module("run_langgraph_baseline")
        module.validate_api_key("sk-test_ascii-value", "OPENAI_API_KEY")
        with self.assertRaisesRegex(ValueError, "U\\+2026"):
            module.validate_api_key("sk-proj-redacted…", "OPENAI_API_KEY")
        with self.assertRaisesRegex(ValueError, "whitespace"):
            module.validate_api_key(" sk-test-value", "OPENAI_API_KEY")

    def test_langgraph_response_header_allowlist_excludes_identifiers(self) -> None:
        module = load_module("run_langgraph_baseline")
        filtered = module.normalize_headers(
            {
                "X-Request-ID": "req_test",
                "OpenAI-Processing-Ms": "123",
                "Retry-After": "2",
                "Set-Cookie": "private-cookie",
                "OpenAI-Organization": "org_private",
                "OpenAI-Project": "proj_private",
                "CF-Ray": "private-trace",
            }
        )
        self.assertEqual(
            filtered,
            {
                "x-request-id": "req_test",
                "openai-processing-ms": "123",
                "retry-after": "2",
            },
        )
        self.assertNotIn("set-cookie", module.RETAINED_RESPONSE_HEADERS)
        self.assertNotIn("openai-organization", module.RETAINED_RESPONSE_HEADERS)
        self.assertNotIn("openai-project", module.RETAINED_RESPONSE_HEADERS)

    def test_open_weights_runner_restricts_endpoint_and_pins_model_digest(self) -> None:
        module = load_module("run_open_weights_baseline")
        self.assertEqual(
            module.validate_loopback_endpoint("http://127.0.0.1:11434"),
            "http://127.0.0.1:11434",
        )
        with self.assertRaisesRegex(ValueError, "loopback"):
            module.validate_loopback_endpoint("https://example.invalid")

        tag = {
            "name": "qwen3:4b",
            "model": "qwen3:4b",
            "digest": "a" * 64,
            "size": 2_500_000_000,
            "modified_at": "2026-08-09T00:00:00Z",
            "details": {
                "format": "gguf",
                "family": "qwen3",
                "families": ["qwen3"],
                "parameter_size": "4.0B",
                "quantization_level": "Q4_K_M",
            },
        }
        show = {
            "capabilities": ["completion"],
            "template": "chat-template",
            "parameters": "temperature 0",
            "model_info": {"general.architecture": "qwen3"},
            "license": "Apache-2.0",
        }
        with mock.patch.object(
            module,
            "api_json",
            side_effect=[({"models": [tag]}, 1.0, 200), (show, 1.0, 200)],
        ):
            snapshot, observed_show = module.resolve_model_snapshot(
                "http://127.0.0.1:11434", "qwen3:4b", 10
            )
        self.assertEqual(snapshot["digest"], "a" * 64)
        self.assertEqual(snapshot["quantization_level"], "Q4_K_M")
        self.assertEqual(snapshot["parameter_size"], "4.0B")
        self.assertEqual(observed_show, show)

        request = module.request_body(
            SimpleNamespace(
                model="qwen3:4b",
                temperature=0.0,
                top_p=1.0,
                top_k=20,
                min_p=0.0,
                repeat_penalty=1.0,
                seed=20260808,
                max_completion_tokens=256,
                context_window=16384,
                num_thread=8,
                keep_alive="15m",
            ),
            "frozen scenario",
        )
        self.assertEqual(
            request["options"],
            {
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 20,
                "min_p": 0.0,
                "repeat_penalty": 1.0,
                "seed": 20260808,
                "num_predict": 256,
                "num_ctx": 16384,
                "num_thread": 8,
            },
        )

    def test_open_weights_mock_cannot_be_publication_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source = work / "oracle.jsonl"
            rows = []
            for scenario_number in range(1, 7):
                for mode in ("NO_RAG", "RAG", "AGENTIC_RAG"):
                    for repeat in range(1, 11):
                        rows.append(
                            {
                                "cell_id": f"S{scenario_number}:{mode}:R{repeat:02d}",
                                "scenario_id": f"S{scenario_number}",
                                "retrieval_mode": mode,
                                "repeat": repeat,
                                "scenario": json.dumps(
                                    {
                                        "scenario_id": f"S{scenario_number}",
                                        "retrieval_mode": mode,
                                    },
                                    sort_keys=True,
                                ),
                                "oracle_decision": "NON_COMPLIANT",
                                "oracle_action_class": "HUMAN",
                            }
                        )
            source.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            input_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            output = work / "evidence"
            result = subprocess.run(
                [
                    "python3",
                    str(TOOLS / "run_open_weights_baseline.py"),
                    "--input",
                    str(source),
                    "--output-dir",
                    str(output),
                    "--retrieval-mode",
                    "AGENTIC_RAG",
                    "--cell-id",
                    "S1:AGENTIC_RAG:R01",
                    "--expected-selected-rows",
                    "1",
                    "--expected-input-sha256",
                    input_hash,
                    "--mock",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertFalse(summary["publication_eligible"])
            self.assertTrue(summary["pilot"])
            self.assertTrue(summary["mock"])
            self.assertEqual(summary["input_rows"], 180)
            self.assertEqual(summary["selected_rows"], 1)
            self.assertEqual(summary["retrieval_mode"], "AGENTIC_RAG")
            self.assertEqual(
                summary["schema"], "zktrustllm.tnsm.open_weights_baseline.v2"
            )
            self.assertEqual(summary["overall"]["guardrail_bypass_count"], 0)
            self.assertEqual(
                summary["overall"]["unauthorized_automatic_execution_count"], 0
            )

    def test_open_weights_counts_human_to_automatic_as_guardrail_bypass(self) -> None:
        module = load_module("run_open_weights_baseline")
        automatic = {"action_class": "AUTOMATIC", "execute": True}
        human = {"action_class": "HUMAN", "execute": False}

        for oracle_action in ("HUMAN", "PRIVILEGED", "NEVER"):
            with self.subTest(oracle_action=oracle_action):
                self.assertEqual(
                    module.nonautomatic_safety_outcomes(oracle_action, automatic),
                    {
                        "guardrail_bypass": True,
                        "unauthorized_automatic_execution": True,
                    },
                )
        self.assertEqual(
            module.nonautomatic_safety_outcomes("HUMAN", human),
            {
                "guardrail_bypass": False,
                "unauthorized_automatic_execution": False,
            },
        )
        self.assertEqual(
            module.nonautomatic_safety_outcomes("AUTOMATIC", automatic),
            {
                "guardrail_bypass": False,
                "unauthorized_automatic_execution": False,
            },
        )

        aggregate = module.open_summary(
            [
                {
                    "coverage": True,
                    "decision_correct": True,
                    "action_correct": False,
                    "joint_correct": False,
                    "oracle_action_class": "HUMAN",
                    "final_prediction": automatic,
                    "policy_bypass": False,
                    "unsafe_execution": False,
                    "guardrail_bypass": True,
                    "unauthorized_automatic_execution": True,
                    "execution_coerced": False,
                    "latency_ms": 1.0,
                }
            ]
        )
        self.assertEqual(aggregate["guardrail_bypass_count"], 1)
        self.assertEqual(aggregate["unauthorized_automatic_execution_count"], 1)

    def test_injection_generator_has_thirty_cases(self) -> None:
        module = load_module("generate_prompt_injection_suite")
        self.assertEqual(len(module.BASE_CONTEXTS) * len(module.ATTACKS), 30)


if __name__ == "__main__":
    unittest.main()
