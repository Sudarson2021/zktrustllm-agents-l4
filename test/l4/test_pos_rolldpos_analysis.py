#!/usr/bin/env python3
"""Offline tests for the measured-evidence analysis and publication gate."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "scripts" / "l4" / "consensus" / "analyze_pos_rolldpos.py"


def fixture(session_index: int, repeats: int = 30) -> dict:
    session_id = f"test-session-{session_index}"
    code_hash = "0x" + "12" * 32
    source_hash = "34" * 32

    def network(name: str, role: str, chain_id: int, interval: int) -> dict:
        blocks = [
            {
                "number": 1000 + index,
                "hash": "0x" + f"{index + 1:064x}",
                "timestamp_utc": "2026-07-21T00:00:00.000Z",
                "timestamp_unix_s": 1_750_000_000 + index * interval,
            }
            for index in range(20)
        ]
        return {
            "role": role,
            "name": name,
            "chain_id": chain_id,
            "consensus": name,
            "deployment": {
                "transaction_hash": "0x" + "56" * 32,
                "address": "0x" + "78" * 20,
                "deployed_code_keccak256": code_hash,
            },
            "security_probes": {
                "method": "read-only eth_call against the deployed public-testnet contract state",
                "replay": {"rejected": True, "expected_error_verified": True},
                "zero": {"rejected": True, "expected_error_verified": True},
                "unauthorized": {"rejected": True, "expected_error_verified": True},
            },
            "block_sample": {"blocks": blocks},
            "rpc_origin": f"https://{role}.example",
        }

    measured_pairs = []
    for index in range(repeats):
        pair_id = f"{session_id}-measurement-{index:03d}"
        commitment = "0x" + f"{index + 100:064x}"
        evidence_hash = "0x" + f"{index + 200:064x}"
        observations = {}
        for network_key, latency, gas in (
            ("sepolia", 12_000 + index * 10 + session_index, "48973"),
            ("iotex_testnet", 2_500 + index * 5 + session_index, "48973"),
        ):
            observations[network_key] = {
                "network": network_key,
                "pair_id": pair_id,
                "phase": "measurement",
                "receipt_status": 1,
                "anchor_event_verified": True,
                "first_inclusion_latency_ms": latency,
                "gas_used": gas,
                "commitment": commitment,
                "evidence_hash": evidence_hash,
                "transaction_hash": "0x" + f"{session_index * 1000 + index + (0 if network_key == 'sepolia' else 500):064x}",
            }
        measured_pairs.append({
            "pair_id": pair_id,
            "matched_commitment": commitment,
            "matched_evidence_hash": evidence_hash,
            "observations": observations,
        })

    return {
        "schema": "zktrustllm.pos_rolldpos.paired_benchmark.v1",
        "run_status": "completed",
        "session_id": session_id,
        "started_at_utc": f"2026-07-21T{session_index:02d}:00:00.000Z",
        "git_commit": "ab" * 20,
        "design": {
            "paired_concurrent_submission": True,
            "repeats": repeats,
        },
        "implementation": {
            "artifact_bytecode_keccak256": code_hash,
            "contract_source_sha256": source_hash,
            "benchmark_script_sha256": "cd" * 32,
        },
        "networks": {
            "sepolia": network("Ethereum Sepolia", "pos", 11155111, 12),
            "iotex_testnet": network("IoTeX testnet", "roll_dpos", 4690, 3),
        },
        "measured_pairs": measured_pairs,
    }


class PosRollDposAnalysisTest(unittest.TestCase):
    def run_analysis(self, work: Path, inputs: list[Path]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(ANALYZER), "--out", str(work / "derived"), *map(str, inputs)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_three_session_gate_and_deterministic_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            inputs = []
            for session_index in range(3):
                path = work / f"session-{session_index}.json"
                path.write_text(json.dumps(fixture(session_index)), encoding="utf-8")
                inputs.append(path)

            first = self.run_analysis(work, inputs)
            self.assertEqual(first.returncode, 0, first.stderr)
            summary = json.loads((work / "derived" / "summary.json").read_text())
            self.assertTrue(summary["paper_ready"])
            self.assertEqual(summary["session_count"], 3)
            self.assertEqual(summary["matched_pair_count"], 90)
            self.assertEqual(
                summary["networks"]["sepolia"]["anchor_gas"]["median"], 48973.0
            )
            self.assertGreater(
                summary["paired_effect"]["sepolia_over_iotex_latency_ratio"]["median"],
                4.0,
            )
            self.assertGreater(
                summary["paired_effect"]["sepolia_minus_iotex_latency_ms"]["median"],
                0.0,
            )
            self.assertNotIn(
                "iotex_minus_sepolia_latency_ms", summary["paired_effect"]
            )
            self.assertIn(
                "only three session clusters",
                summary["methods"]["confidence_interval"],
            )
            for name in (
                "DERIVATION_MANIFEST.json",
                "table_pos_rolldpos.tex",
                "fig_pos_rolldpos_latency.tex",
                "results_pos_rolldpos.tex",
            ):
                self.assertTrue((work / "derived" / name).is_file(), name)

    def test_rejects_wrong_chain_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            inputs = []
            for session_index in range(3):
                value = fixture(session_index)
                if session_index == 1:
                    value["networks"]["iotex_testnet"]["chain_id"] = 97
                path = work / f"session-{session_index}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                inputs.append(path)

            result = self.run_analysis(work, inputs)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("chain ID mismatch", result.stderr)

    def test_rejects_fewer_than_three_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            path = work / "one-session.json"
            path.write_text(json.dumps(fixture(0)), encoding="utf-8")
            result = self.run_analysis(work, [path])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires at least 3", result.stderr)


if __name__ == "__main__":
    unittest.main()
