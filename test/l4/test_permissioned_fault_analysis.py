#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/l4/consensus/analyze_permissioned_faults.py"
SPEC = importlib.util.spec_from_file_location("permissioned_analysis", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def write_session(root: Path, session_id: str, repeats: int = 3) -> Path:
    session = root / session_id
    session.mkdir()

    def raft_rows(success: bool):
        return [
            {
                "latency_ms": 1.0 + index,
                "success": success,
                "expected_success": success,
            }
            for index in range(repeats)
        ]

    def qbft_rows(scenario: str):
        rows = []
        for index in range(repeats):
            payload = json.dumps(
                {"session_id": session_id, "scenario": scenario, "index": index},
                separators=(",", ":"),
            )
            rows.append(
                {
                    "payload": payload,
                    "commitment": "0x" + digest(payload),
                    "evidence_hash": "0x" + digest("evidence:" + payload),
                    "receipt_status": 1,
                    "event_valid": True,
                    "first_inclusion_latency_ms": 1000 + index,
                }
            )
        return rows

    data = {
        "schema": MODULE.SCHEMA,
        "session_id": session_id,
        "completed_at_utc": "2026-07-26T00:00:00Z",
        "publication_eligible": False,
        "smoke_or_dirty_run": True,
        "claim_boundary": {
            "byzantine_faults_measured": False,
            "raft_qbft_absolute_latency_directly_comparable": False,
        },
        "parameters": {"repeats": repeats, "warmups_excluded": 0},
        "git": {"clean": False, "commit": "a" * 40},
        "implementation_hashes": {
            "runner_sha256": "b" * 64,
            "analyzer_sha256": "c" * 64,
        },
        "raft": {
            "cluster_size": 3,
            "byzantine_faults_measured": False,
            "binary_sha256": "d" * 64,
            "lifecycle": {
                "leader_failover": {"recovery_ms": 500},
                "recovery": {"recovery_ms": 400},
            },
            "observations": {
                "baseline": raft_rows(True),
                "one_follower_offline": raft_rows(True),
                "post_leader_failover": raft_rows(True),
                "majority_loss": raft_rows(False),
                "recovered": raft_rows(True),
            },
        },
        "qbft": {
            "cluster_size": 4,
            "chain_id": 13371,
            "byzantine_faults_measured": False,
            "arbitrary_byzantine_messages_or_equivocation_injected": False,
            "binary_sha256": "e" * 64,
            "contract": {
                "security_probes": [
                    {"rejected": True},
                    {"rejected": True},
                    {"rejected": True},
                ]
            },
            "lifecycle": {"recovery": {"recovery_ms": 900}},
            "observations": {
                "baseline": qbft_rows("baseline"),
                "one_validator_offline": qbft_rows("one_validator_offline"),
                "two_validators_offline_block_probes": [
                    {"block_number": 12} for _ in range(repeats)
                ],
                "recovered": qbft_rows("recovered"),
            },
        },
    }
    benchmark = session / "benchmark.json"
    benchmark.write_text(json.dumps(data), encoding="utf-8")
    checksum = hashlib.sha256(benchmark.read_bytes()).hexdigest()
    (session / "SHA256SUMS.txt").write_text(
        f"{checksum}  benchmark.json\n", encoding="utf-8"
    )
    return benchmark


class PermissionedAnalysisTests(unittest.TestCase):
    def test_valid_smoke_sessions_aggregate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sessions = [
                MODULE.validate_session(
                    write_session(root, f"session-{index}"),
                    min_observations=3,
                    allow_smoke=True,
                )
                for index in range(3)
            ]
            summary = MODULE.aggregate(sessions)
            self.assertEqual(summary["session_count"], 3)
            self.assertEqual(summary["raft"]["baseline"]["n"], 9)
            self.assertEqual(summary["qbft"]["baseline"]["n"], 9)

    def test_payload_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            benchmark = write_session(Path(temporary), "tampered")
            data = json.loads(benchmark.read_text())
            data["qbft"]["observations"]["baseline"][0]["payload"] = "changed"
            benchmark.write_text(json.dumps(data), encoding="utf-8")
            checksum = hashlib.sha256(benchmark.read_bytes()).hexdigest()
            (benchmark.parent / "SHA256SUMS.txt").write_text(
                f"{checksum}  benchmark.json\n", encoding="utf-8"
            )
            with self.assertRaises(MODULE.EvidenceError):
                MODULE.validate_session(
                    benchmark, min_observations=3, allow_smoke=True
                )

    def test_qbft_progress_without_quorum_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            benchmark = write_session(Path(temporary), "progressed")
            data = json.loads(benchmark.read_text())
            data["qbft"]["observations"]["two_validators_offline_block_probes"][-1][
                "block_number"
            ] = 13
            benchmark.write_text(json.dumps(data), encoding="utf-8")
            checksum = hashlib.sha256(benchmark.read_bytes()).hexdigest()
            (benchmark.parent / "SHA256SUMS.txt").write_text(
                f"{checksum}  benchmark.json\n", encoding="utf-8"
            )
            with self.assertRaises(MODULE.EvidenceError):
                MODULE.validate_session(
                    benchmark, min_observations=3, allow_smoke=True
                )


if __name__ == "__main__":
    unittest.main()
