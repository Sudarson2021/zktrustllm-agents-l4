#!/usr/bin/env python3
"""Offline unit tests for the TNSM completion gates."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "scripts" / "l4" / "tnsm_revision"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RevisionToolsTest(unittest.TestCase):
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
                    "--expected-rows",
                    "1",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(summary["publication_eligible"])
            self.assertEqual(summary["unsafe_execution_count"], 0)
            self.assertFalse(summary["complete_180_matrix"])

    def test_injection_generator_has_thirty_cases(self) -> None:
        module = load_module("generate_prompt_injection_suite")
        self.assertEqual(len(module.BASE_CONTEXTS) * len(module.ATTACKS), 30)


if __name__ == "__main__":
    unittest.main()
