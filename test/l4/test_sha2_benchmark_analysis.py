#!/usr/bin/env python3
"""Offline tests for the SHA-2 public-testnet evidence gate."""
import base64
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "scripts" / "l4" / "consensus" / "analyze_sha2_benchmark.py"


def fixture(session_index: int, repeats: int = 30) -> dict:
    session_id = f"sha2-test-{session_index}"
    code_hash = "0x" + "12" * 32

    def network(name: str, role: str, chain_id: int) -> dict:
        return {
            "role": role,
            "name": name,
            "chain_id": chain_id,
            "consensus": name,
            "rpc_origin": f"https://{role}.example",
            "deployment": {
                "transaction_hash": "0x" + "34" * 32,
                "address": "0x" + "56" * 20,
                "deployed_code_keccak256": code_hash,
            },
            "security_probes": {
                "method": "read-only eth_call",
                "duplicate": {"rejected": True, "expected_error_verified": True},
                "wrong_length": {"rejected": True, "expected_error_verified": True},
                "unauthorized": {"rejected": True, "expected_error_verified": True},
            },
        }

    measured_pairs = []
    for index in range(repeats):
        pair_id = f"{session_id}-measurement-{index:03d}"
        payload = hashlib.sha512(pair_id.encode()).digest() * 2
        payload = payload[:128]
        digests = {
            "sha256": "0x" + hashlib.sha256(payload).hexdigest(),
            "sha512": "0x" + hashlib.sha512(payload).hexdigest(),
        }
        ids = {
            "sha256": "0x" + hashlib.sha256(f"{pair_id}:256".encode()).hexdigest(),
            "sha512": "0x" + hashlib.sha256(f"{pair_id}:512".encode()).hexdigest(),
        }
        observations = {}
        for network_index, network_key in enumerate(("sepolia", "iotex_testnet")):
            observations[network_key] = {}
            for algorithm_index, (algorithm, algorithm_id, digest_bytes) in enumerate(
                (("sha256", 1, 32), ("sha512", 2, 64))
            ):
                serial = (
                    session_index * 100_000
                    + index * 100
                    + network_index * 10
                    + algorithm_index
                )
                observations[network_key][algorithm] = {
                    "network": network_key,
                    "pair_id": pair_id,
                    "phase": "measurement",
                    "algorithm": algorithm,
                    "algorithm_id": algorithm_id,
                    "digest_bytes": digest_bytes,
                    "evidence_id": ids[algorithm],
                    "digest": digests[algorithm],
                    "transaction_hash": "0x" + f"{serial + 1:064x}",
                    "first_inclusion_latency_ms": (
                        12_000 if network_key == "sepolia" else 3_000
                    )
                    + index
                    + algorithm_index,
                    "gas_used": str(36_000 + digest_bytes * 20 + network_index),
                    "receipt_status": 1,
                    "hash_event_verified": True,
                }
        measured_pairs.append(
            {
                "pair_id": pair_id,
                "phase": "measurement",
                "payload_bytes": len(payload),
                "payload_base64": base64.b64encode(payload).decode(),
                "algorithm_order": (
                    ["sha256", "sha512"] if index % 2 == 0 else ["sha512", "sha256"]
                ),
                "evidence_ids": ids,
                "digests": digests,
                "observations": observations,
            }
        )

    return {
        "schema": "zktrustllm.sha2.paired_anchor_benchmark.v1",
        "run_status": "completed",
        "session_id": session_id,
        "started_at_utc": f"2026-07-25T{session_index:02d}:00:00.000Z",
        "git_commit": "ab" * 20,
        "design": {
            "paired_across_networks": True,
            "balanced_algorithm_order": True,
            "repeats": repeats,
            "payload_bytes": 128,
        },
        "implementation": {
            "artifact_bytecode_keccak256": code_hash,
            "contract_source_sha256": "78" * 32,
            "benchmark_script_sha256": "9a" * 32,
        },
        "algorithms": {
            "sha256": {"digest_bytes": 32},
            "sha512": {"digest_bytes": 64},
        },
        "networks": {
            "sepolia": network("Ethereum Sepolia", "gasper_pos", 11155111),
            "iotex_testnet": network(
                "IoTeX testnet", "roll_dpos_pbft", 4690
            ),
        },
        "measured_pairs": measured_pairs,
    }


class Sha2BenchmarkAnalysisTest(unittest.TestCase):
    def run_analysis(
        self, work: Path, inputs: list[Path]
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(ANALYZER), "--out", str(work / "derived"), *map(str, inputs)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_sessions(self, work: Path) -> list[Path]:
        inputs = []
        for index in range(3):
            path = work / f"session-{index}.json"
            path.write_text(json.dumps(fixture(index)), encoding="utf-8")
            inputs.append(path)
        return inputs

    def test_gate_and_deterministic_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            result = self.run_analysis(work, self.write_sessions(work))
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(
                (work / "derived" / "summary_sha2.json").read_text()
            )
            self.assertTrue(summary["paper_ready"])
            self.assertEqual(summary["session_count"], 3)
            self.assertEqual(summary["pair_count"], 90)
            self.assertTrue(summary["integrity"]["payload_digests_recomputed"])
            for name in (
                "DERIVATION_MANIFEST_SHA2.json",
                "summary_sha2.json",
                "table_sha2_network.tex",
                "fig_sha2_anchor_gas.tex",
                "results_sha2_network.tex",
            ):
                self.assertTrue((work / "derived" / name).is_file(), name)

    def test_rejects_tampered_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            inputs = self.write_sessions(work)
            value = json.loads(inputs[1].read_text())
            value["measured_pairs"][0]["digests"]["sha512"] = "0x" + "ff" * 64
            inputs[1].write_text(json.dumps(value), encoding="utf-8")
            result = self.run_analysis(work, inputs)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("digests do not match payload", result.stderr)

    def test_rejects_wrong_chain_and_too_few_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            inputs = self.write_sessions(work)
            value = json.loads(inputs[0].read_text())
            value["networks"]["iotex_testnet"]["chain_id"] = 1
            inputs[0].write_text(json.dumps(value), encoding="utf-8")
            result = self.run_analysis(work, inputs)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("chain ID mismatch", result.stderr)

            one = self.run_analysis(work, [inputs[1]])
            self.assertNotEqual(one.returncode, 0)
            self.assertIn("at least 3", one.stderr)


if __name__ == "__main__":
    unittest.main()
