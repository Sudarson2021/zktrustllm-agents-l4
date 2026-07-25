#!/usr/bin/env python3
"""Validate measured SHA-2 anchor sessions and derive manuscript artifacts.

The publication gate requires three sessions with at least 30 repetitions each.
Every digest is recomputed from the retained payload before gas or latency is
reported. No measured value is embedded in this source file.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "zktrustllm.sha2.paired_anchor_benchmark.v1"
NETWORKS = {
    "sepolia": {"chain_id": 11155111, "role": "gasper_pos"},
    "iotex_testnet": {"chain_id": 4690, "role": "roll_dpos_pbft"},
}
ALGORITHMS = {
    "sha256": {"id": 1, "digest_bytes": 32},
    "sha512": {"id": 2, "digest_bytes": 64},
}
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 2_026_072_5


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"{path}: cannot load JSON: {error}")
    if not isinstance(value, dict):
        fail(f"{path}: top-level JSON must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.name


def quantile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        fail("cannot calculate a quantile from an empty sample")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def describe(values: Iterable[float]) -> dict[str, float | int]:
    sample = [float(value) for value in values]
    if not sample:
        fail("cannot describe an empty sample")
    return {
        "n": len(sample),
        "min": min(sample),
        "median": statistics.median(sample),
        "p95": quantile(sample, 0.95),
        "max": max(sample),
        "mean": statistics.fmean(sample),
        "sample_sd": statistics.stdev(sample) if len(sample) > 1 else 0.0,
    }


def hierarchical_median_ci(
    values_by_session: dict[str, list[float]], seed: int
) -> list[float]:
    session_ids = sorted(values_by_session)
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample: list[float] = []
        for _session in session_ids:
            selected = values_by_session[rng.choice(session_ids)]
            sample.extend(rng.choice(selected) for _ in range(len(selected)))
        estimates.append(statistics.median(sample))
    return [quantile(estimates, 0.025), quantile(estimates, 0.975)]


def validate_security_probes(path: Path, network: str, value: dict[str, Any]) -> None:
    probes = value.get("security_probes")
    if not isinstance(probes, dict):
        fail(f"{path}: {network} security probes missing")
    for key in ("duplicate", "wrong_length", "unauthorized"):
        probe = probes.get(key)
        if (
            not isinstance(probe, dict)
            or probe.get("rejected") is not True
            or probe.get("expected_error_verified") is not True
        ):
            fail(f"{path}: {network} {key} rejection was not verified")


def validate_session(
    path: Path, value: dict[str, Any], minimum_repeats: int
) -> dict[str, Any]:
    if value.get("schema") != SCHEMA:
        fail(f"{path}: expected schema {SCHEMA!r}")
    if value.get("run_status") != "completed":
        fail(f"{path}: run_status must be completed")
    session_id = value.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        fail(f"{path}: session_id missing")
    design = value.get("design")
    if not isinstance(design, dict):
        fail(f"{path}: design metadata missing")
    if design.get("paired_across_networks") is not True:
        fail(f"{path}: benchmark is not paired across networks")
    if design.get("balanced_algorithm_order") is not True:
        fail(f"{path}: algorithm order was not declared balanced")
    repeats = design.get("repeats")
    payload_bytes = design.get("payload_bytes")
    if not isinstance(repeats, int) or repeats < minimum_repeats:
        fail(f"{path}: publication gate requires at least {minimum_repeats} repeats")
    if not isinstance(payload_bytes, int) or payload_bytes <= 0:
        fail(f"{path}: invalid payload size")

    implementation = value.get("implementation")
    if not isinstance(implementation, dict):
        fail(f"{path}: implementation metadata missing")
    artifact_hash = implementation.get("artifact_bytecode_keccak256")
    if not isinstance(artifact_hash, str) or not artifact_hash.startswith("0x"):
        fail(f"{path}: artifact bytecode hash missing")

    algorithm_meta = value.get("algorithms")
    if not isinstance(algorithm_meta, dict) or set(algorithm_meta) != set(ALGORITHMS):
        fail(f"{path}: expected exactly {sorted(ALGORITHMS)} algorithm metadata")
    for algorithm, expected in ALGORITHMS.items():
        if algorithm_meta[algorithm].get("digest_bytes") != expected["digest_bytes"]:
            fail(f"{path}: {algorithm} digest width mismatch")

    networks = value.get("networks")
    if not isinstance(networks, dict) or set(networks) != set(NETWORKS):
        fail(f"{path}: expected exactly {sorted(NETWORKS)} networks")
    deployed_hashes = set()
    for network, expected in NETWORKS.items():
        network_value = networks[network]
        if network_value.get("chain_id") != expected["chain_id"]:
            fail(f"{path}: {network} chain ID mismatch")
        if network_value.get("role") != expected["role"]:
            fail(f"{path}: {network} consensus role mismatch")
        deployment = network_value.get("deployment")
        if not isinstance(deployment, dict):
            fail(f"{path}: {network} deployment evidence missing")
        if not deployment.get("transaction_hash") or not deployment.get("address"):
            fail(f"{path}: {network} deployment transaction/address missing")
        deployed_hashes.add(deployment.get("deployed_code_keccak256"))
        validate_security_probes(path, network, network_value)
    if len(deployed_hashes) != 1 or None in deployed_hashes:
        fail(f"{path}: deployed runtime bytecode differs between networks")

    pairs = value.get("measured_pairs")
    if not isinstance(pairs, list) or len(pairs) != repeats:
        fail(f"{path}: measured_pairs count does not equal repeats")
    order_counts = {("sha256", "sha512"): 0, ("sha512", "sha256"): 0}
    seen_pair_ids = set()
    transaction_hashes = {
        network: {algorithm: set() for algorithm in ALGORITHMS}
        for network in NETWORKS
    }
    for pair in pairs:
        pair_id = pair.get("pair_id")
        if not pair_id or pair_id in seen_pair_ids:
            fail(f"{path}: missing or duplicate pair_id")
        seen_pair_ids.add(pair_id)
        try:
            payload = base64.b64decode(pair["payload_base64"], validate=True)
        except (KeyError, ValueError) as error:
            fail(f"{path}: {pair_id} invalid payload: {error}")
        if len(payload) != payload_bytes or pair.get("payload_bytes") != payload_bytes:
            fail(f"{path}: {pair_id} payload size mismatch")
        expected_digests = {
            "sha256": "0x" + hashlib.sha256(payload).hexdigest(),
            "sha512": "0x" + hashlib.sha512(payload).hexdigest(),
        }
        if pair.get("digests") != expected_digests:
            fail(f"{path}: {pair_id} retained digests do not match payload")
        order = tuple(pair.get("algorithm_order", []))
        if order not in order_counts:
            fail(f"{path}: {pair_id} invalid algorithm order")
        order_counts[order] += 1
        evidence_ids = pair.get("evidence_ids")
        if not isinstance(evidence_ids, dict) or set(evidence_ids) != set(ALGORITHMS):
            fail(f"{path}: {pair_id} evidence identifiers missing")
        observations = pair.get("observations")
        if not isinstance(observations, dict) or set(observations) != set(NETWORKS):
            fail(f"{path}: {pair_id} network observations missing")
        for network in NETWORKS:
            network_observations = observations[network]
            if (
                not isinstance(network_observations, dict)
                or set(network_observations) != set(ALGORITHMS)
            ):
                fail(f"{path}: {pair_id}/{network} algorithm observations missing")
            for algorithm, expected in ALGORITHMS.items():
                observation = network_observations[algorithm]
                if observation.get("receipt_status") != 1:
                    fail(f"{path}: {pair_id}/{network}/{algorithm} receipt failed")
                if observation.get("hash_event_verified") is not True:
                    fail(f"{path}: {pair_id}/{network}/{algorithm} event unverified")
                if observation.get("algorithm_id") != expected["id"]:
                    fail(f"{path}: {pair_id}/{network}/{algorithm} ID mismatch")
                if observation.get("digest_bytes") != expected["digest_bytes"]:
                    fail(f"{path}: {pair_id}/{network}/{algorithm} width mismatch")
                if observation.get("digest") != expected_digests[algorithm]:
                    fail(f"{path}: {pair_id}/{network}/{algorithm} digest mismatch")
                if observation.get("evidence_id") != evidence_ids[algorithm]:
                    fail(f"{path}: {pair_id}/{network}/{algorithm} evidence ID mismatch")
                transaction_hash = observation.get("transaction_hash")
                if (
                    not isinstance(transaction_hash, str)
                    or not transaction_hash.startswith("0x")
                    or transaction_hash in transaction_hashes[network][algorithm]
                ):
                    fail(f"{path}: {pair_id}/{network}/{algorithm} transaction invalid")
                transaction_hashes[network][algorithm].add(transaction_hash)
                gas = observation.get("gas_used")
                latency = observation.get("first_inclusion_latency_ms")
                if not isinstance(gas, str) or not gas.isdigit() or int(gas) <= 0:
                    fail(f"{path}: {pair_id}/{network}/{algorithm} gas invalid")
                if not isinstance(latency, (int, float)) or latency <= 0:
                    fail(f"{path}: {pair_id}/{network}/{algorithm} latency invalid")
    if abs(order_counts[("sha256", "sha512")] - order_counts[("sha512", "sha256")]) > 1:
        fail(f"{path}: algorithm order is not balanced")
    return value


def rounded(value: Any, digits: int = 3) -> Any:
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, dict):
        return {key: rounded(item, digits) for key, item in value.items()}
    if isinstance(value, list):
        return [rounded(item, digits) for item in value]
    return value


def build_summary(sessions: list[dict[str, Any]], inputs: list[Path]) -> dict[str, Any]:
    metrics: dict[str, dict[str, dict[str, dict[str, list[float]]]]] = {
        metric: {
            network: {algorithm: {} for algorithm in ALGORITHMS}
            for network in NETWORKS
        }
        for metric in ("gas", "latency")
    }
    for session in sessions:
        session_id = session["session_id"]
        for network in NETWORKS:
            for algorithm in ALGORITHMS:
                metrics["gas"][network][algorithm][session_id] = []
                metrics["latency"][network][algorithm][session_id] = []
        for pair in session["measured_pairs"]:
            for network in NETWORKS:
                for algorithm in ALGORITHMS:
                    observation = pair["observations"][network][algorithm]
                    metrics["gas"][network][algorithm][session_id].append(
                        float(observation["gas_used"])
                    )
                    metrics["latency"][network][algorithm][session_id].append(
                        float(observation["first_inclusion_latency_ms"])
                    )

    network_stats: dict[str, Any] = {}
    seed_offset = 0
    for network in NETWORKS:
        network_stats[network] = {
            "name": sessions[0]["networks"][network]["name"],
            "chain_id": sessions[0]["networks"][network]["chain_id"],
            "consensus": sessions[0]["networks"][network]["consensus"],
            "algorithms": {},
        }
        for algorithm in ALGORITHMS:
            gas_by_session = metrics["gas"][network][algorithm]
            latency_by_session = metrics["latency"][network][algorithm]
            gas = describe(sum(gas_by_session.values(), []))
            latency = describe(sum(latency_by_session.values(), []))
            gas["median_hierarchical_bootstrap_95_ci"] = hierarchical_median_ci(
                gas_by_session, BOOTSTRAP_SEED + seed_offset
            )
            latency["median_hierarchical_bootstrap_95_ci"] = hierarchical_median_ci(
                latency_by_session, BOOTSTRAP_SEED + 20 + seed_offset
            )
            network_stats[network]["algorithms"][algorithm] = {
                "digest_bytes": ALGORITHMS[algorithm]["digest_bytes"],
                "anchor_gas": gas,
                "first_inclusion_latency_ms": latency,
            }
            seed_offset += 1
        gas256 = network_stats[network]["algorithms"]["sha256"]["anchor_gas"]["median"]
        gas512 = network_stats[network]["algorithms"]["sha512"]["anchor_gas"]["median"]
        network_stats[network]["sha512_minus_sha256_median_anchor_gas"] = gas512 - gas256

    return rounded(
        {
            "schema": "zktrustllm.sha2.paired_anchor_analysis.v1",
            "paper_ready": True,
            "session_count": len(sessions),
            "pair_count": sum(len(session["measured_pairs"]) for session in sessions),
            "payload_bytes": sessions[0]["design"]["payload_bytes"],
            "methods": {
                "quantile": "R-7 linear interpolation",
                "confidence_interval": (
                    "95% two-level hierarchical bootstrap of the median; sessions "
                    f"and within-session pairs resampled; {BOOTSTRAP_REPLICATES} replicates"
                ),
                "bootstrap_seed": BOOTSTRAP_SEED,
            },
            "networks": network_stats,
            "integrity": {
                "payload_digests_recomputed": True,
                "identical_runtime_bytecode": True,
                "all_receipts_successful": True,
                "all_events_verified": True,
                "all_security_probes_rejected": True,
            },
            "inputs": {evidence_label(path): sha256_file(path) for path in inputs},
            "claim_boundary": (
                "Precomputed full-digest anchoring only. Gas compares 32-byte SHA-256 "
                "and 64-byte SHA-512 event payloads; latency remains client/RPC/testnet "
                "dependent. No hash-throughput, cryptographic-strength, consensus-"
                "superiority, mainnet, or economic-finality claim is made."
            ),
        }
    )


def fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def latex_table(summary: dict[str, Any]) -> str:
    labels = {
        "sepolia": "Ethereum Sepolia (Gasper PoS)",
        "iotex_testnet": "IoTeX testnet (Roll-DPoS/PBFT)",
    }
    rows = []
    for network in ("sepolia", "iotex_testnet"):
        algorithms = summary["networks"][network]["algorithms"]
        gas256 = algorithms["sha256"]["anchor_gas"]["median"]
        gas512 = algorithms["sha512"]["anchor_gas"]["median"]
        lat256 = algorithms["sha256"]["first_inclusion_latency_ms"]["median"]
        lat512 = algorithms["sha512"]["first_inclusion_latency_ms"]["median"]
        rows.append(
            f"{labels[network]} & {int(gas256):,} & {int(gas512):,} & "
            f"{int(gas512 - gas256):,} & {fmt(lat256)} & {fmt(lat512)} \\\\"
        )
    return "\n".join(
        [
            "% AUTO-GENERATED from validated public-testnet benchmark evidence.",
            "\\begin{table*}[!t]",
            "\\centering",
            "\\caption{Measured anchoring of precomputed full SHA-2 digests. Gas reflects "
            "32-byte SHA-256 versus 64-byte SHA-512 digest anchoring; hashing itself is "
            "performed off chain for both rows. Latency is submission to first inclusion.}",
            "\\label{tab:sha2-network}",
            "\\begin{tabular}{lrrrrr}",
            "\\toprule",
            "Network (consensus) & SHA-256 gas & SHA-512 gas & $\\Delta$ gas & "
            "SHA-256 latency (ms) & SHA-512 latency (ms) \\\\",
            "\\midrule",
            *rows,
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table*}",
            "",
        ]
    )


def latex_figure(summary: dict[str, Any]) -> str:
    sepolia = summary["networks"]["sepolia"]["algorithms"]
    iotex = summary["networks"]["iotex_testnet"]["algorithms"]
    return f"""% AUTO-GENERATED from validated public-testnet benchmark evidence.
\\begin{{figure}}[!t]
\\centering
\\begin{{tikzpicture}}
\\begin{{axis}}[
  width=\\columnwidth,height=5.2cm,ybar,bar width=11pt,
  ylabel={{Median anchor gas}},
  symbolic x coords={{Sepolia,IoTeX}},xtick=data,
  xticklabels={{Sepolia\\\\(Gasper PoS),IoTeX\\\\(Roll-DPoS/PBFT)}},
  x tick label style={{font=\\scriptsize,align=center}},
  scaled y ticks=false,
  yticklabel style={{/pgf/number format/fixed,/pgf/number format/1000 sep={{,}}}},
  legend style={{at={{(0.5,1.02)}},anchor=south,legend columns=2,font=\\scriptsize}},
  ymin=0,nodes near coords,
  nodes near coords style={{font=\\tiny,/pgf/number format/1000 sep={{,}}}},
  enlarge x limits=0.32,ymajorgrids,grid style={{black!10}}
]
\\addplot+[fill=blue!60] coordinates {{
  (Sepolia,{int(sepolia['sha256']['anchor_gas']['median'])})
  (IoTeX,{int(iotex['sha256']['anchor_gas']['median'])})
}};
\\addplot+[fill=orange!75] coordinates {{
  (Sepolia,{int(sepolia['sha512']['anchor_gas']['median'])})
  (IoTeX,{int(iotex['sha512']['anchor_gas']['median'])})
}};
\\legend{{SHA-256 (32-byte digest),SHA-512 (64-byte digest)}}
\\end{{axis}}
\\end{{tikzpicture}}
\\caption{{Measured gas for anchoring precomputed complete SHA-256 and SHA-512
digests using identical EVM runtime bytecode. This is a digest-width/anchoring
comparison, not an on-chain hash-throughput comparison.}}
\\label{{fig:sha2-anchor-gas}}
\\end{{figure}}
"""


def latex_results(summary: dict[str, Any]) -> str:
    fragments = []
    for network, label in (
        ("sepolia", "Ethereum Sepolia"),
        ("iotex_testnet", "IoTeX testnet"),
    ):
        stats = summary["networks"][network]
        algorithms = stats["algorithms"]
        fragments.append(
            f"On {label}, the median gas was "
            f"{int(algorithms['sha256']['anchor_gas']['median']):,} for SHA-256 and "
            f"{int(algorithms['sha512']['anchor_gas']['median']):,} for SHA-512 "
            f"(difference {int(stats['sha512_minus_sha256_median_anchor_gas']):,})."
        )
    return (
        "% AUTO-GENERATED from validated public-testnet benchmark evidence.\n"
        f"Across {summary['pair_count']} payload pairs in {summary['session_count']} "
        f"sessions, every retained SHA-256 and SHA-512 digest was recomputed from the "
        f"{summary['payload_bytes']}-byte payload before analysis. "
        + " ".join(fragments)
        + " Both algorithms were computed off chain and only their complete digests "
        "were anchored, so the gas difference is attributed to digest width and EVM "
        "event/calldata handling rather than cryptographic throughput. First-inclusion "
        "latency remains testnet-, RPC-, and load-dependent.\n"
    )


def write_outputs(summary: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "summary_sha2.json": json.dumps(summary, indent=2, sort_keys=True) + "\n",
        "table_sha2_network.tex": latex_table(summary),
        "fig_sha2_anchor_gas.tex": latex_figure(summary),
        "results_sha2_network.tex": latex_results(summary),
    }
    for name, content in outputs.items():
        (out_dir / name).write_text(content, encoding="utf-8")
    manifest = {
        "schema": "zktrustllm.sha2.derivation_manifest.v1",
        "input_hashes": summary["inputs"],
        "output_hashes": {
            name: sha256_file(out_dir / name) for name in sorted(outputs)
        },
        "derivation": (
            "Deterministic derivation from validated measured evidence; retained "
            "payloads are rehashed before any result is emitted."
        ),
    }
    (out_dir / "DERIVATION_MANIFEST_SHA2.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+", help="measured benchmark.json files")
    parser.add_argument("--out", type=Path, required=True, help="derived-artifact directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inputs = [path.resolve() for path in args.inputs]
    if len(inputs) < 3:
        fail("publication gate requires at least 3 independent sessions")
    sessions = [validate_session(path, load_json(path), 30) for path in inputs]
    session_ids = [session["session_id"] for session in sessions]
    if len(session_ids) != len(set(session_ids)):
        fail("duplicate session_id values are not allowed")
    try:
        started = [
            dt.datetime.fromisoformat(session["started_at_utc"].replace("Z", "+00:00"))
            for session in sessions
        ]
    except (KeyError, AttributeError, ValueError) as error:
        fail(f"invalid session timestamp: {error}")
    if len(started) != len(set(started)):
        fail("session start timestamps must be distinct")
    for key in (
        "artifact_bytecode_keccak256",
        "contract_source_sha256",
        "benchmark_script_sha256",
    ):
        values = {session["implementation"].get(key) for session in sessions}
        if len(values) != 1 or None in values:
            fail(f"implementation field {key} differs across sessions")
    git_commits = {session.get("git_commit") for session in sessions}
    if len(git_commits) != 1 or None in git_commits:
        fail("Git commit differs across sessions")
    if len({session["design"]["payload_bytes"] for session in sessions}) != 1:
        fail("payload size differs across sessions")
    for network in NETWORKS:
        origins = {session["networks"][network].get("rpc_origin") for session in sessions}
        if len(origins) != 1 or None in origins:
            fail(f"{network} RPC origin differs across sessions")
    deployed_hashes = {
        session["networks"][network]["deployment"].get("deployed_code_keccak256")
        for session in sessions
        for network in NETWORKS
    }
    if len(deployed_hashes) != 1 or None in deployed_hashes:
        fail("deployed runtime bytecode differs across sessions")
    summary = build_summary(sessions, inputs)
    write_outputs(summary, args.out)
    print(
        f"OK: {summary['pair_count']} payload pairs in "
        f"{summary['session_count']} sessions -> {args.out}"
    )


if __name__ == "__main__":
    main()
