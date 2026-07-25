#!/usr/bin/env python3
"""Derive paper artifacts from measured PoS/Roll-DPoS benchmark sessions.

The default publication gate requires at least three independent sessions and
30 matched transaction pairs per session. All reported values are calculated
from benchmark.json evidence; this script contains no experimental constants.

Usage:
  python3 scripts/l4/consensus/analyze_pos_rolldpos.py \
    --out paper/l4_conference/derived_consensus \
    runtime_artifacts/consensus_comparison/session-1/benchmark.json \
    runtime_artifacts/consensus_comparison/session-2/benchmark.json \
    runtime_artifacts/consensus_comparison/session-3/benchmark.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "zktrustllm.pos_rolldpos.paired_benchmark.v1"
EXPECTED_NETWORKS = {
    "sepolia": {"chain_id": 11155111, "role": "pos"},
    "iotex_testnet": {"chain_id": 4690, "role": "roll_dpos"},
}
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 2_026_072_1


def fail(message: str) -> None:
    raise ValueError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.name


def quantile(values: Iterable[float], probability: float) -> float:
    """R-7/NumPy-linear quantile, implemented without external dependencies."""
    ordered = sorted(float(value) for value in values)
    if not ordered:
        fail("cannot calculate a quantile from an empty sample")
    if not 0 <= probability <= 1:
        fail(f"invalid quantile probability: {probability}")
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
        "q1": quantile(sample, 0.25),
        "median": statistics.median(sample),
        "q3": quantile(sample, 0.75),
        "p95": quantile(sample, 0.95),
        "max": max(sample),
        "mean": statistics.fmean(sample),
        "sample_sd": statistics.stdev(sample) if len(sample) > 1 else 0.0,
    }


def hierarchical_median_ci(
    values_by_session: dict[str, list[float]], seed: int
) -> list[float]:
    """Two-level bootstrap: resample sessions, then observations in sessions."""
    session_ids = sorted(values_by_session)
    if not session_ids:
        fail("hierarchical bootstrap received no sessions")
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled_values: list[float] = []
        for _session_index in session_ids:
            selected_id = rng.choice(session_ids)
            selected_values = values_by_session[selected_id]
            sampled_values.extend(
                rng.choice(selected_values) for _ in range(len(selected_values))
            )
        estimates.append(statistics.median(sampled_values))
    return [quantile(estimates, 0.025), quantile(estimates, 0.975)]


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"{path}: cannot load JSON: {error}")
    if not isinstance(value, dict):
        fail(f"{path}: top-level JSON must be an object")
    return value


def validate_security_probes(path: Path, network: str, value: dict[str, Any]) -> None:
    probes = value.get("security_probes")
    if not isinstance(probes, dict):
        fail(f"{path}: {network} security_probes missing")
    if probes.get("method", "").startswith("read-only eth_call") is False:
        fail(f"{path}: {network} security-probe method is not bounded as eth_call")
    for key in ("replay", "zero", "unauthorized"):
        probe = probes.get(key)
        if (
            not isinstance(probe, dict)
            or probe.get("rejected") is not True
            or probe.get("expected_error_verified") is not True
        ):
            fail(f"{path}: {network} {key} rejection was not observed")


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
    if not isinstance(design, dict) or design.get("paired_concurrent_submission") is not True:
        fail(f"{path}: benchmark is not a paired concurrent-submission design")
    repeats = design.get("repeats")
    if not isinstance(repeats, int) or repeats < minimum_repeats:
        fail(
            f"{path}: {repeats!r} repeats; publication gate requires "
            f"at least {minimum_repeats}"
        )

    implementation = value.get("implementation")
    if not isinstance(implementation, dict):
        fail(f"{path}: implementation metadata missing")
    artifact_hash = implementation.get("artifact_bytecode_keccak256")
    if not isinstance(artifact_hash, str) or not artifact_hash.startswith("0x"):
        fail(f"{path}: artifact bytecode hash missing")

    networks = value.get("networks")
    if not isinstance(networks, dict) or set(networks) != set(EXPECTED_NETWORKS):
        fail(f"{path}: expected exactly {sorted(EXPECTED_NETWORKS)}")
    deployed_hashes = set()
    for network, expected in EXPECTED_NETWORKS.items():
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
        block_sample = network_value.get("block_sample", {}).get("blocks", [])
        if not isinstance(block_sample, list) or len(block_sample) < 20:
            fail(f"{path}: {network} requires at least 20 consecutive block headers")
        previous_number = None
        for block in block_sample:
            number = block.get("number")
            if previous_number is not None and number != previous_number + 1:
                fail(f"{path}: {network} block sample is not consecutive")
            previous_number = number
    if len(deployed_hashes) != 1 or None in deployed_hashes:
        fail(f"{path}: deployed runtime bytecode differs between networks")

    measured_pairs = value.get("measured_pairs")
    if not isinstance(measured_pairs, list) or len(measured_pairs) != repeats:
        fail(f"{path}: measured_pairs count does not equal repeats")
    seen_pair_ids = set()
    transaction_hashes = {network: set() for network in EXPECTED_NETWORKS}
    for pair in measured_pairs:
        pair_id = pair.get("pair_id")
        if not pair_id or pair_id in seen_pair_ids:
            fail(f"{path}: missing or duplicate pair_id")
        seen_pair_ids.add(pair_id)
        observations = pair.get("observations")
        if not isinstance(observations, dict) or set(observations) != set(EXPECTED_NETWORKS):
            fail(f"{path}: {pair_id} does not contain both network observations")
        matched_commitment = pair.get("matched_commitment")
        matched_evidence_hash = pair.get("matched_evidence_hash")
        if not isinstance(matched_commitment, str) or not matched_commitment.startswith("0x"):
            fail(f"{path}: {pair_id} matched commitment missing")
        if not isinstance(matched_evidence_hash, str) or not matched_evidence_hash.startswith("0x"):
            fail(f"{path}: {pair_id} matched evidence hash missing")
        for network in EXPECTED_NETWORKS:
            observation = observations[network]
            if observation.get("pair_id") != pair_id:
                fail(f"{path}: {pair_id}/{network} pair ID mismatch")
            if observation.get("phase") != "measurement":
                fail(f"{path}: {pair_id}/{network} is not a measurement")
            if observation.get("receipt_status") != 1:
                fail(f"{path}: {pair_id}/{network} transaction did not succeed")
            if observation.get("anchor_event_verified") is not True:
                fail(f"{path}: {pair_id}/{network} anchor event not verified")
            if observation.get("commitment") != matched_commitment:
                fail(f"{path}: {pair_id}/{network} commitment is not matched")
            if observation.get("evidence_hash") != matched_evidence_hash:
                fail(f"{path}: {pair_id}/{network} evidence hash is not matched")
            transaction_hash = observation.get("transaction_hash")
            if not isinstance(transaction_hash, str) or not transaction_hash.startswith("0x"):
                fail(f"{path}: {pair_id}/{network} transaction hash missing")
            if transaction_hash in transaction_hashes[network]:
                fail(f"{path}: {network} duplicate transaction hash")
            transaction_hashes[network].add(transaction_hash)
            latency = observation.get("first_inclusion_latency_ms")
            if not isinstance(latency, (int, float)) or latency <= 0:
                fail(f"{path}: {pair_id}/{network} invalid inclusion latency")
            gas = observation.get("gas_used")
            if not isinstance(gas, str) or not gas.isdigit() or int(gas) <= 0:
                fail(f"{path}: {pair_id}/{network} invalid gas value")

    return value


def block_gaps(session: dict[str, Any], network: str) -> list[float]:
    blocks = session["networks"][network]["block_sample"]["blocks"]
    gaps = []
    for previous, current in zip(blocks, blocks[1:]):
        gap = current["timestamp_unix_s"] - previous["timestamp_unix_s"]
        if gap <= 0:
            fail(
                f"{session['session_id']}: {network} has a non-positive block timestamp gap"
            )
        gaps.append(float(gap))
    return gaps


def rounded(value: Any, digits: int = 3) -> Any:
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, dict):
        return {key: rounded(item, digits) for key, item in value.items()}
    if isinstance(value, list):
        return [rounded(item, digits) for item in value]
    return value


def fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def build_summary(sessions: list[dict[str, Any]], inputs: list[Path]) -> dict[str, Any]:
    latency_by_network: dict[str, dict[str, list[float]]] = {
        network: {} for network in EXPECTED_NETWORKS
    }
    gas_by_network: dict[str, dict[str, list[float]]] = {
        network: {} for network in EXPECTED_NETWORKS
    }
    blocks_by_network: dict[str, dict[str, list[float]]] = {
        network: {} for network in EXPECTED_NETWORKS
    }
    paired_difference_by_session: dict[str, list[float]] = {}
    paired_ratio_by_session: dict[str, list[float]] = {}

    for session in sessions:
        session_id = session["session_id"]
        paired_difference_by_session[session_id] = []
        paired_ratio_by_session[session_id] = []
        for network in EXPECTED_NETWORKS:
            latency_by_network[network][session_id] = []
            gas_by_network[network][session_id] = []
            blocks_by_network[network][session_id] = block_gaps(session, network)
        for pair in session["measured_pairs"]:
            pos = pair["observations"]["sepolia"]
            dpos = pair["observations"]["iotex_testnet"]
            pos_latency = float(pos["first_inclusion_latency_ms"])
            dpos_latency = float(dpos["first_inclusion_latency_ms"])
            latency_by_network["sepolia"][session_id].append(pos_latency)
            latency_by_network["iotex_testnet"][session_id].append(dpos_latency)
            gas_by_network["sepolia"][session_id].append(float(pos["gas_used"]))
            gas_by_network["iotex_testnet"][session_id].append(float(dpos["gas_used"]))
            paired_difference_by_session[session_id].append(dpos_latency - pos_latency)
            paired_ratio_by_session[session_id].append(pos_latency / dpos_latency)

    network_stats: dict[str, Any] = {}
    for index, network in enumerate(EXPECTED_NETWORKS):
        latency_values = sum(latency_by_network[network].values(), [])
        gas_values = sum(gas_by_network[network].values(), [])
        block_values = sum(blocks_by_network[network].values(), [])
        network_stats[network] = {
            "name": sessions[0]["networks"][network]["name"],
            "consensus": sessions[0]["networks"][network]["consensus"],
            "chain_id": sessions[0]["networks"][network]["chain_id"],
            "first_inclusion_latency_ms": {
                **describe(latency_values),
                "median_hierarchical_bootstrap_95_ci": hierarchical_median_ci(
                    latency_by_network[network], BOOTSTRAP_SEED + index
                ),
            },
            "anchor_gas": describe(gas_values),
            "consecutive_block_interval_s": {
                **describe(block_values),
                "median_hierarchical_bootstrap_95_ci": hierarchical_median_ci(
                    blocks_by_network[network], BOOTSTRAP_SEED + 10 + index
                ),
            },
            "all_security_probes_rejected": True,
        }

    all_differences = sum(paired_difference_by_session.values(), [])
    all_ratios = sum(paired_ratio_by_session.values(), [])
    summary = {
        "schema": "zktrustllm.pos_rolldpos.analysis.v1",
        "paper_ready": True,
        "session_count": len(sessions),
        "matched_pair_count": sum(len(session["measured_pairs"]) for session in sessions),
        "methods": {
            "quantile": "R-7 linear interpolation",
            "confidence_interval": (
                "95% two-level hierarchical bootstrap of the median; sessions and "
                f"within-session pairs resampled; {BOOTSTRAP_REPLICATES} replicates"
            ),
            "bootstrap_seed": BOOTSTRAP_SEED,
            "primary_metric": "client-observed submission-to-first-inclusion latency",
        },
        "networks": network_stats,
        "paired_effect": {
            "iotex_minus_sepolia_latency_ms": {
                **describe(all_differences),
                "median_hierarchical_bootstrap_95_ci": hierarchical_median_ci(
                    paired_difference_by_session, BOOTSTRAP_SEED + 20
                ),
            },
            "sepolia_over_iotex_latency_ratio": {
                **describe(all_ratios),
                "median_hierarchical_bootstrap_95_ci": hierarchical_median_ci(
                    paired_ratio_by_session, BOOTSTRAP_SEED + 21
                ),
            },
        },
        "integrity": {
            "identical_runtime_bytecode_across_networks_and_sessions": True,
            "all_receipts_successful": True,
            "all_anchor_events_verified": True,
            "all_security_probes_rejected": True,
        },
        "inputs": {
            evidence_label(path): sha256_file(path) for path in inputs
        },
        "claim_boundary": (
            "Public-testnet observations for one isolated EVM audit-anchor micro-benchmark. "
            "Sepolia uses a permissioned test validator set. Latency includes RPC/client "
            "overhead and first inclusion only; it is not economic finality. Results do not "
            "establish mainnet throughput, decentralization, or production O-RAN performance."
        ),
    }
    return rounded(summary)


def latex_table(summary: dict[str, Any]) -> str:
    rows = []
    labels = {
        "sepolia": "Ethereum Sepolia (Gasper PoS)",
        "iotex_testnet": "IoTeX testnet (Roll-DPoS)",
    }
    for network in ("sepolia", "iotex_testnet"):
        stats = summary["networks"][network]
        latency = stats["first_inclusion_latency_ms"]
        latency_ci = latency["median_hierarchical_bootstrap_95_ci"]
        block = stats["consecutive_block_interval_s"]
        gas = stats["anchor_gas"]
        security = "3/3" if stats["all_security_probes_rejected"] else "CHECK"
        rows.append(
            f"{labels[network]} & {stats['chain_id']} & "
            f"{int(gas['median'])} & "
            f"{fmt(latency['median'])} [{fmt(latency_ci[0])}, {fmt(latency_ci[1])}] & "
            f"{fmt(latency['p95'])} & {fmt(block['median'])} & {security} \\\\"
        )
    return "\n".join(
        [
            "% AUTO-GENERATED from measured benchmark.json evidence; do not hand-edit.",
            "\\begin{table*}[!t]",
            "\\centering",
            "\\caption{Paired public-testnet consensus sensitivity of the identical "
            "Stage3AnomalyLedger bytecode. Latency is client-observed submission to first "
            "inclusion, not economic finality; brackets are hierarchical-bootstrap 95\\% "
            "confidence intervals for the median.}",
            "\\label{tab:pos-rolldpos}",
            "\\begin{adjustbox}{width=\\textwidth}",
            "\\begin{tabular}{lrrrrrr}",
            "\\toprule",
            "Network (consensus) & Chain ID & Anchor gas & Median latency (ms) & "
            "P95 latency (ms) & Block interval (s) & Rejections \\\\ ",
            "\\midrule",
            *rows,
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{adjustbox}",
            "\\end{table*}",
            "",
        ]
    )


def latex_figure(summary: dict[str, Any]) -> str:
    pos = summary["networks"]["sepolia"]["first_inclusion_latency_ms"]
    dpos = summary["networks"]["iotex_testnet"]["first_inclusion_latency_ms"]
    return f"""% AUTO-GENERATED from measured benchmark.json evidence; do not hand-edit.
\\begin{{figure}}[!t]
\\centering
\\begin{{tikzpicture}}
\\begin{{axis}}[
  width=\\columnwidth,height=5.0cm,ybar,bar width=12pt,
  ylabel={{First-inclusion latency (ms)}},
  symbolic x coords={{Sepolia,IoTeX}},xtick=data,
  xticklabels={{Sepolia (Gasper PoS),IoTeX (Roll-DPoS/PBFT)}},
  x tick label style={{font=\\scriptsize,align=center}},
  legend style={{at={{(0.5,1.02)}},anchor=south,legend columns=2,font=\\scriptsize}},
  ymin=0,nodes near coords,nodes near coords style={{font=\\tiny}},
  enlarge x limits=0.35,ymajorgrids,grid style={{black!10}}
]
\\addplot+[fill=blue!55] coordinates {{(Sepolia,{fmt(pos['median'])}) (IoTeX,{fmt(dpos['median'])})}};
\\addplot+[fill=orange!70] coordinates {{(Sepolia,{fmt(pos['p95'])}) (IoTeX,{fmt(dpos['p95'])})}};
\\legend{{Median,P95}}
\\end{{axis}}
\\end{{tikzpicture}}
\\caption{{Measured client-observed first-inclusion latency for matched,
concurrently submitted audit-anchor transactions. Public-testnet load and
RPC/client overhead are included; economic finality is not measured. Raft and
QBFT are compared structurally in Fig.~\\ref{{fig:consensus-protocols}} but are
omitted here because no corresponding measured deployment evidence exists.}}
\\label{{fig:pos-rolldpos-latency}}
\\end{{figure}}
"""


def latex_results(summary: dict[str, Any]) -> str:
    pos = summary["networks"]["sepolia"]["first_inclusion_latency_ms"]
    dpos = summary["networks"]["iotex_testnet"]["first_inclusion_latency_ms"]
    ratio = summary["paired_effect"]["sepolia_over_iotex_latency_ratio"]
    gas_pos = summary["networks"]["sepolia"]["anchor_gas"]
    gas_dpos = summary["networks"]["iotex_testnet"]["anchor_gas"]
    ratio_ci = ratio["median_hierarchical_bootstrap_95_ci"]
    return (
        "% AUTO-GENERATED from measured benchmark.json evidence; do not hand-edit.\n"
        f"Across {summary['matched_pair_count']} matched transaction pairs collected in "
        f"{summary['session_count']} independent sessions, median client-observed "
        f"first-inclusion latency was {fmt(pos['median'])}~ms on Ethereum Sepolia and "
        f"{fmt(dpos['median'])}~ms on IoTeX testnet (Table~\\ref{{tab:pos-rolldpos}}). "
        f"The median paired Sepolia-to-IoTeX latency ratio was {fmt(ratio['median'])} "
        f"(hierarchical-bootstrap 95\\% CI: {fmt(ratio_ci[0])}--{fmt(ratio_ci[1])}). "
        f"The median anchor execution gas was {int(gas_pos['median'])} and "
        f"{int(gas_dpos['median'])}, respectively; gas-price values are not converted "
        "into a cross-asset economic comparison. All three read-only rejection probes "
        "(duplicate, zero, and unauthorised submitter) reverted on both deployed "
        "contracts. These values describe public-testnet first inclusion for the isolated "
        "audit-anchor transaction and do not imply mainnet finality or production O-RAN "
        "performance.\n"
    )


def write_outputs(summary: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "summary.json": json.dumps(summary, indent=2, sort_keys=True) + "\n",
        "table_pos_rolldpos.tex": latex_table(summary),
        "fig_pos_rolldpos_latency.tex": latex_figure(summary),
        "results_pos_rolldpos.tex": latex_results(summary),
    }
    for name, content in outputs.items():
        (out_dir / name).write_text(content, encoding="utf-8")
    manifest = {
        "schema": "zktrustllm.pos_rolldpos.derivation_manifest.v1",
        "input_hashes": summary["inputs"],
        "output_hashes": {
            name: sha256_file(out_dir / name) for name in sorted(outputs)
        },
        "derivation": (
            "Deterministic calculation from validated measured evidence; no simulation "
            "or manually entered result values."
        ),
    }
    (out_dir / "DERIVATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+", help="measured benchmark.json files")
    parser.add_argument("--out", type=Path, required=True, help="paper-artifact output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    resolved_inputs = [path.resolve() for path in args.inputs]
    if len(resolved_inputs) < 3:
        fail(
            f"received {len(resolved_inputs)} sessions; publication gate requires "
            "at least 3"
        )
    sessions = [
        validate_session(path, load_json(path), 30)
        for path in resolved_inputs
    ]
    session_ids = [session["session_id"] for session in sessions]
    if len(session_ids) != len(set(session_ids)):
        fail("duplicate session_id values are not allowed")
    try:
        started_times = [
            dt.datetime.fromisoformat(session["started_at_utc"].replace("Z", "+00:00"))
            for session in sessions
        ]
    except (KeyError, AttributeError, ValueError) as error:
        fail(f"invalid or missing session start timestamp: {error}")
    if len(started_times) != len(set(started_times)):
        fail("session start timestamps must be distinct")
    artifact_hashes = {
        session["implementation"]["artifact_bytecode_keccak256"] for session in sessions
    }
    source_hashes = {
        session["implementation"]["contract_source_sha256"] for session in sessions
    }
    if len(artifact_hashes) != 1 or len(source_hashes) != 1:
        fail("contract source/bytecode differs across sessions")
    script_hashes = {
        session["implementation"].get("benchmark_script_sha256") for session in sessions
    }
    git_commits = {session.get("git_commit") for session in sessions}
    if len(script_hashes) != 1 or None in script_hashes:
        fail("benchmark script differs across sessions")
    if len(git_commits) != 1 or None in git_commits:
        fail("Git commit differs across sessions")
    deployed_hashes = {
        session["networks"][network]["deployment"]["deployed_code_keccak256"]
        for session in sessions
        for network in EXPECTED_NETWORKS
    }
    if len(deployed_hashes) != 1:
        fail("deployed runtime bytecode differs across sessions")
    for network in EXPECTED_NETWORKS:
        rpc_origins = {session["networks"][network].get("rpc_origin") for session in sessions}
        if len(rpc_origins) != 1 or None in rpc_origins:
            fail(f"{network} RPC origin differs across sessions")

    summary = build_summary(sessions, resolved_inputs)
    write_outputs(summary, args.out)
    print(
        f"OK: {summary['matched_pair_count']} matched pairs in "
        f"{summary['session_count']} sessions -> {args.out}"
    )


if __name__ == "__main__":
    main()
