#!/usr/bin/env python3
"""Validate a local hash primitive benchmark and derive paper artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path


EXPECTED_SCHEMA = "zktrustllm-hash-primitive-microbenchmark-v1"
ALGORITHMS = (
    ("keccak256", "Keccak-256"),
    ("sha256", "SHA-256"),
    ("sha512_local", "SHA-512 (Solidity)"),
)
EXPECTED_VECTORS = {
    "sha256_abc": (
        "0xba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    ),
    "sha512_empty": (
        "0xcf83e1357eefb8bdf1542850d66d8007"
        "d620e4050b5715dc83f4a921d36ce9ce"
        "47d0d13c5d85f2b0ff8318d2877eec2f"
        "63b931bd47417a81a538327af927da3e"
    ),
    "sha512_abc": (
        "0xddaf35a193617abacc417349ae2041311"
        "2e6fa4e89a97ea20a9eeee64b55d39a"
        "2192992a274fc1a836ba3c23a3feebbd"
        "454d4423643ce80e2a9ac94fa54ca49f"
    ),
}
KECCAK_ROUND_CONSTANTS = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)
KECCAK_ROTATIONS = (
    (0, 36, 3, 41, 18),
    (1, 44, 10, 45, 2),
    (62, 6, 43, 15, 61),
    (28, 55, 25, 21, 56),
    (27, 20, 39, 8, 14),
)


class GateError(ValueError):
    """Raised when benchmark evidence fails the publication gate."""


def _rotate_left_64(value: int, amount: int) -> int:
    mask = (1 << 64) - 1
    if amount == 0:
        return value & mask
    return ((value << amount) | (value >> (64 - amount))) & mask


def _keccak_f1600(state: list[int]) -> None:
    mask = (1 << 64) - 1
    for round_constant in KECCAK_ROUND_CONSTANTS:
        columns = [
            state[x]
            ^ state[x + 5]
            ^ state[x + 10]
            ^ state[x + 15]
            ^ state[x + 20]
            for x in range(5)
        ]
        deltas = [
            columns[(x - 1) % 5] ^ _rotate_left_64(columns[(x + 1) % 5], 1)
            for x in range(5)
        ]
        for y in range(5):
            for x in range(5):
                state[x + 5 * y] ^= deltas[x]

        permuted = [0] * 25
        for y in range(5):
            for x in range(5):
                new_x = y
                new_y = (2 * x + 3 * y) % 5
                permuted[new_x + 5 * new_y] = _rotate_left_64(
                    state[x + 5 * y], KECCAK_ROTATIONS[x][y]
                )

        for y in range(5):
            row = permuted[5 * y : 5 * y + 5]
            for x in range(5):
                state[x + 5 * y] = (
                    row[x] ^ ((~row[(x + 1) % 5]) & row[(x + 2) % 5])
                ) & mask
        state[0] ^= round_constant


def _keccak256(payload: bytes) -> bytes:
    rate = 136
    padded = bytearray(payload)
    padded.append(0x01)
    padded.extend(b"\x00" * ((rate - 1 - len(padded) % rate) % rate))
    padded.append(0x80)
    state = [0] * 25
    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for lane_index in range(rate // 8):
            lane = int.from_bytes(
                block[lane_index * 8 : lane_index * 8 + 8], "little"
            )
            state[lane_index] ^= lane
        _keccak_f1600(state)
    output = bytearray()
    for lane in state:
        output.extend(lane.to_bytes(8, "little"))
        if len(output) >= 32:
            return bytes(output[:32])
    raise AssertionError("unreachable")


def _digest(algorithm: str, payload: bytes) -> str:
    if algorithm == "keccak256":
        return "0x" + _keccak256(payload).hex()
    name = "sha256" if algorithm == "sha256" else "sha512"
    return "0x" + hashlib.new(name, payload).hexdigest()


def validate(raw: dict) -> list[dict]:
    if raw.get("schema_version") != EXPECTED_SCHEMA:
        raise GateError("unexpected schema version")
    claim = raw.get("claim_boundary", {})
    if claim.get("environment") != "local Hardhat EVM only":
        raise GateError("local-only claim boundary is missing")
    environment = raw.get("environment", {})
    expected_environment = {
        "chain_id": 31337,
        "git_dirty": False,
        "solidity": "0.8.20",
        "optimizer_enabled": True,
        "optimizer_runs": 200,
        "via_ir": True,
        "evm_target": "paris",
    }
    for key, expected in expected_environment.items():
        if environment.get(key) != expected:
            raise GateError(f"unexpected environment field {key}")
    if raw.get("sampling", {}).get("repetitions", 0) < 30:
        raise GateError("at least 30 repetitions are required")

    vectors = raw.get("validation_vectors", {})
    for name, expected in EXPECTED_VECTORS.items():
        vector = vectors.get(name, {})
        if (
            vector.get("expected") != expected
            or vector.get("observed") != expected
            or vector.get("pass") is not True
        ):
            raise GateError(f"cryptographic vector failed: {name}")

    summaries: list[dict] = []
    payloads = raw.get("payloads", [])
    if not payloads:
        raise GateError("no payload measurements")
    for payload_record in payloads:
        payload = bytes.fromhex(payload_record.get("payload_hex", "")[2:])
        if len(payload) != payload_record.get("payload_bytes"):
            raise GateError("payload length mismatch")
        if "0x" + hashlib.sha256(payload).hexdigest() != payload_record.get(
            "payload_sha256"
        ):
            raise GateError("payload SHA-256 mismatch")
        samples = payload_record.get("samples", {})
        for algorithm, label in ALGORITHMS:
            record = samples.get(algorithm, {})
            expected_digest = _digest(algorithm, payload)
            if record.get("digest") != expected_digest:
                raise GateError(f"digest mismatch: {algorithm}")
            values = record.get("primitive_gas_samples", [])
            if len(values) < 30 or any(
                not isinstance(value, int) or value <= 0 for value in values
            ):
                raise GateError(f"invalid primitive gas samples: {algorithm}")
            summaries.append(
                {
                    "payload_bytes": len(payload),
                    "algorithm": algorithm,
                    "label": label,
                    "n": len(values),
                    "median_primitive_gas": int(statistics.median(values)),
                    "minimum_primitive_gas": min(values),
                    "maximum_primitive_gas": max(values),
                    "deterministic": min(values) == max(values),
                }
            )
    return summaries


def _figure_tex(summaries: list[dict]) -> str:
    sizes = sorted({record["payload_bytes"] for record in summaries})
    plots = []
    for size in sizes:
        coordinates = " ".join(
            f"({{{label}}},{next(record['median_primitive_gas'] for record in summaries if record['payload_bytes'] == size and record['label'] == label)})"
            for _, label in ALGORITHMS
        )
        plots.append(
            "\\addplot+[draw=black!65] coordinates {" + coordinates + "};"
        )
    legend = ",".join(f"{size}-byte input" for size in sizes)
    return rf"""\begin{{figure}}[!t]
\centering
\begin{{tikzpicture}}
\begin{{axis}}[
  width=\columnwidth,
  height=5.6cm,
  ybar,
  bar width=7pt,
  ymode=log,
  log basis y=10,
  ymin=10,
  ylabel={{Primitive-path gas (log scale)}},
  symbolic x coords={{Keccak-256,SHA-256,SHA-512 (Solidity)}},
  xtick=data,
  x tick label style={{rotate=20,anchor=east,font=\scriptsize}},
  tick label style={{font=\scriptsize}},
  label style={{font=\scriptsize}},
  legend style={{font=\scriptsize,at={{(0.5,1.02)}},anchor=south,legend columns=-1}},
  grid=major,
  major grid style={{black!12}}
]
{chr(10).join(plots)}
\legend{{{legend}}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Local Hardhat EVM hash-primitive microbenchmark. Values are
\texttt{{gasleft()}} deltas around the isolated hash path under Solidity 0.8.20,
optimizer 200, \texttt{{viaIR=true}}, and the Paris EVM target. The SHA-512 bar
is a FIPS-vector-gated pure-Solidity reference, not the deployable evidence
path. It is not a public-testnet latency, fee, finality, or consensus result.}}
\label{{fig:hash-primitive-microbenchmark}}
\end{{figure}}
"""


def _table_tex(summaries: list[dict]) -> str:
    rows = []
    for record in summaries:
        deterministic = "yes" if record["deterministic"] else "no"
        rows.append(
            f"{record['label']} & {record['payload_bytes']:,} & "
            f"{record['median_primitive_gas']:,} & {record['n']} & "
            f"{deterministic} \\\\"
        )
    return r"""\begin{table}[!t]
\centering
\caption{Validated local hash-primitive measurements.}
\label{tab:hash-primitive-microbenchmark}
\small
\begin{tabular}{lrrrr}
\toprule
Primitive & Bytes & Median gas & $n$ & Fixed \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""


def _results_tex(summaries: list[dict]) -> str:
    sizes = sorted({record["payload_bytes"] for record in summaries})
    sentences = []
    for size in sizes:
        values = {
            record["algorithm"]: record["median_primitive_gas"]
            for record in summaries
            if record["payload_bytes"] == size
        }
        sentences.append(
            f"For the {size:,}-byte input, the median primitive-path deltas "
            f"were {values['keccak256']:,} gas for Keccak-256, "
            f"{values['sha256']:,} gas for the SHA-256 precompile path, and "
            f"{values['sha512_local']:,} gas for the pure-Solidity SHA-512 "
            "reference."
        )
    return (
        "The local hash publication gate passed all retained-payload digest "
        "checks and the SHA-256/SHA-512 validation vectors. "
        + " ".join(sentences)
        + " All 30 calls per algorithm/input cell returned the same delta "
        "because the bytecode, input, and local EVM state were fixed. These "
        "values characterise this isolated execution path; they are not "
        "public-testnet latency, monetary cost, finality, or consensus "
        "measurements.\n"
    )


def write_outputs(source: Path, output_dir: Path) -> None:
    raw_bytes = source.read_bytes()
    raw = json.loads(raw_bytes)
    summaries = validate(raw)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "summary_hash_microbenchmark.json": json.dumps(
            {
                "source": str(source),
                "source_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "claim_boundary": raw["claim_boundary"],
                "environment": raw["environment"],
                "summaries": summaries,
            },
            indent=2,
        )
        + "\n",
        "fig_hash_primitive_microbenchmark.tex": _figure_tex(summaries),
        "table_hash_primitive_microbenchmark.tex": _table_tex(summaries),
        "results_hash_primitive_microbenchmark.tex": _results_tex(summaries),
    }
    manifest = {}
    for filename, content in outputs.items():
        (output_dir / filename).write_text(content, encoding="utf-8")
        manifest[filename] = hashlib.sha256(content.encode()).hexdigest()
    manifest_content = json.dumps(
        {
            "generator": "scripts/l4/consensus/analyze_hash_microbenchmark.py",
            "source": str(source),
            "source_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "outputs": manifest,
        },
        indent=2,
    ) + "\n"
    (output_dir / "HASH_MICROBENCHMARK_MANIFEST.json").write_text(
        manifest_content, encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    write_outputs(args.source, args.out)


if __name__ == "__main__":
    main()
