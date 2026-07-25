import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.l4.consensus.analyze_hash_microbenchmark import (
    GateError,
    _keccak256,
    validate,
    write_outputs,
)


def _fixture():
    payload = bytes((17 + index * 31) & 0xFF for index in range(32))
    return {
        "schema_version": "zktrustllm-hash-primitive-microbenchmark-v1",
        "claim_boundary": {
            "environment": "local Hardhat EVM only",
            "sha512": "FIPS-gated pure-Solidity microbenchmark; not the deployable anchor path",
        },
        "environment": {
            "chain_id": 31337,
            "git_dirty": False,
            "solidity": "0.8.20",
            "optimizer_enabled": True,
            "optimizer_runs": 200,
            "via_ir": True,
            "evm_target": "paris",
        },
        "sampling": {"repetitions": 30},
        "validation_vectors": {
            "sha256_abc": {
                "expected": "0xba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                "observed": "0xba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                "pass": True,
            },
            "sha512_empty": {
                "expected": "0xcf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
                "observed": "0xcf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
                "pass": True,
            },
            "sha512_abc": {
                "expected": "0xddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
                "observed": "0xddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
                "pass": True,
            },
        },
        "payloads": [
            {
                "payload_bytes": 32,
                "payload_hex": "0x" + payload.hex(),
                "payload_sha256": "0x" + hashlib.sha256(payload).hexdigest(),
                "samples": {
                    "keccak256": {
                        "digest": "0x" + _keccak256(payload).hex(),
                        "primitive_gas_samples": [59] * 30,
                    },
                    "sha256": {
                        "digest": "0x" + hashlib.sha256(payload).hexdigest(),
                        "primitive_gas_samples": [395] * 30,
                    },
                    "sha512_local": {
                        "digest": "0x" + hashlib.sha512(payload).hexdigest(),
                        "primitive_gas_samples": [142642] * 30,
                    },
                },
            }
        ],
    }


class HashMicrobenchmarkAnalysisTest(unittest.TestCase):
    def test_keccak_reference_vector(self):
        self.assertEqual(
            _keccak256(b"abc").hex(),
            "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
        )

    def test_validates_and_writes_deterministic_artifacts(self):
        raw = _fixture()
        self.assertEqual(len(validate(raw)), 3)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "benchmark.json"
            source.write_text(json.dumps(raw), encoding="utf-8")
            out = root / "out"
            write_outputs(source, out)
            first = (out / "fig_hash_primitive_microbenchmark.tex").read_bytes()
            write_outputs(source, out)
            self.assertEqual(
                first, (out / "fig_hash_primitive_microbenchmark.tex").read_bytes()
            )

    def test_rejects_failed_fips_vector(self):
        raw = copy.deepcopy(_fixture())
        raw["validation_vectors"]["sha512_abc"]["pass"] = False
        with self.assertRaisesRegex(GateError, "cryptographic vector failed"):
            validate(raw)

    def test_rejects_digest_tampering(self):
        raw = copy.deepcopy(_fixture())
        raw["payloads"][0]["samples"]["sha256"]["digest"] = "0x" + "00" * 32
        with self.assertRaisesRegex(GateError, "digest mismatch"):
            validate(raw)

    def test_rejects_public_testnet_label(self):
        raw = copy.deepcopy(_fixture())
        raw["claim_boundary"]["environment"] = "Sepolia"
        with self.assertRaisesRegex(GateError, "local-only claim boundary"):
            validate(raw)


if __name__ == "__main__":
    unittest.main()
