#!/usr/bin/env python3
"""Validate and summarize real etcd/Raft and Besu/QBFT fault evidence.

The default gate is publication-oriented: three independent clean sessions,
at least 30 retained observations per condition, and at least three excluded
warm-ups.  The analyzer never compares absolute etcd and EVM latencies because
the two systems execute different workloads.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "zktrustllm.permissioned-consensus-fault-evidence.v3"


class EvidenceError(ValueError):
    """Raised when an evidence gate fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise EvidenceError("Cannot summarize an empty sample")
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def stats(values: Iterable[float]) -> dict[str, float | int]:
    sample = [float(value) for value in values]
    if not sample:
        raise EvidenceError("Cannot summarize an empty sample")
    return {
        "n": len(sample),
        "median": statistics.median(sample),
        "p95": percentile(sample, 0.95),
        "mean": statistics.fmean(sample),
        "stdev": statistics.stdev(sample) if len(sample) > 1 else 0.0,
        "min": min(sample),
        "max": max(sample),
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def verify_manifest(benchmark_path: Path) -> None:
    manifest_path = benchmark_path.parent / "SHA256SUMS.txt"
    require(manifest_path.is_file(), f"{benchmark_path}: missing SHA256SUMS.txt")
    entries: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, separator, relative = line.partition("  ")
        require(bool(separator), f"{manifest_path}: malformed checksum line")
        entries[relative] = digest
    require("benchmark.json" in entries, f"{manifest_path}: benchmark.json is not hash-bound")
    require(
        entries["benchmark.json"] == sha256_file(benchmark_path),
        f"{benchmark_path}: checksum mismatch",
    )


def validate_qbft_commit(observation: dict[str, Any], context: str) -> None:
    payload = observation["payload"]
    expected_commitment = "0x" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
    expected_evidence = "0x" + hashlib.sha256(
        ("evidence:" + payload).encode("utf-8")
    ).hexdigest()
    require(
        observation["commitment"].lower() == expected_commitment,
        f"{context}: commitment does not bind retained payload",
    )
    require(
        observation["evidence_hash"].lower() == expected_evidence,
        f"{context}: evidence hash does not bind retained payload",
    )
    require(observation["receipt_status"] == 1, f"{context}: failed EVM receipt")
    require(observation["event_valid"] is True, f"{context}: invalid anchor event")
    require(
        float(observation["first_inclusion_latency_ms"]) >= 0,
        f"{context}: negative latency",
    )


def validate_session(
    benchmark_path: Path,
    *,
    min_observations: int,
    allow_smoke: bool,
) -> dict[str, Any]:
    verify_manifest(benchmark_path)
    data = json.loads(benchmark_path.read_text(encoding="utf-8"))
    prefix = str(benchmark_path)
    require(data.get("schema") == SCHEMA, f"{prefix}: unexpected schema")
    require(bool(data.get("session_id")), f"{prefix}: missing session ID")
    require(data.get("completed_at_utc"), f"{prefix}: incomplete run")
    require(data["claim_boundary"]["byzantine_faults_measured"] is False,
            f"{prefix}: invalid Byzantine-fault claim")
    require(
        data["claim_boundary"]["raft_qbft_absolute_latency_directly_comparable"] is False,
        f"{prefix}: invalid cross-workload latency claim",
    )
    if not allow_smoke:
        require(data["git"]["clean"] is True, f"{prefix}: dirty Git worktree")
        require(data["publication_eligible"] is True, f"{prefix}: run is not publication eligible")
        require(data["smoke_or_dirty_run"] is False, f"{prefix}: smoke run supplied")
        require(data["parameters"]["warmups_excluded"] >= 3, f"{prefix}: fewer than three warm-ups")

    require(
        data["parameters"]["repeats"] >= min_observations,
        f"{prefix}: repeats below {min_observations}",
    )

    raft = data["raft"]
    require(raft["cluster_size"] == 3, f"{prefix}: Raft cluster is not three members")
    require(raft["byzantine_faults_measured"] is False, f"{prefix}: invalid Raft fault claim")
    for scenario in (
        "baseline",
        "one_follower_offline",
        "post_leader_failover",
        "recovered",
    ):
        rows = raft["observations"][scenario]
        require(len(rows) >= min_observations, f"{prefix}: Raft {scenario} sample too small")
        require(all(row["success"] is True for row in rows), f"{prefix}: Raft {scenario} failure")
        require(
            all(float(row["latency_ms"]) >= 0 for row in rows),
            f"{prefix}: Raft {scenario} has negative latency",
        )
    raft_loss = raft["observations"]["majority_loss"]
    require(len(raft_loss) >= min_observations, f"{prefix}: Raft majority-loss sample too small")
    require(
        all(row["success"] is False and row["expected_success"] is False for row in raft_loss),
        f"{prefix}: Raft accepted a write without majority quorum",
    )
    require(
        float(raft["lifecycle"]["leader_failover"]["recovery_ms"]) >= 0,
        f"{prefix}: invalid Raft failover time",
    )

    qbft = data["qbft"]
    require(qbft["cluster_size"] == 4, f"{prefix}: QBFT cluster is not four validators")
    require(qbft["chain_id"] == 13371, f"{prefix}: unexpected QBFT chain ID")
    require(
        qbft["configuration"].get("transaction_nonce_management")
        == "ethers.NonceManager with sequential confirmed submissions",
        f"{prefix}: deterministic QBFT nonce management not recorded",
    )
    require(qbft["byzantine_faults_measured"] is False, f"{prefix}: invalid QBFT fault claim")
    require(
        qbft["arbitrary_byzantine_messages_or_equivocation_injected"] is False,
        f"{prefix}: invalid Byzantine-injection claim",
    )
    require(
        all(probe["rejected"] is True for probe in qbft["contract"]["security_probes"]),
        f"{prefix}: contract negative-security probe failed",
    )
    for scenario in ("baseline", "one_validator_offline", "recovered"):
        rows = qbft["observations"][scenario]
        require(len(rows) >= min_observations, f"{prefix}: QBFT {scenario} sample too small")
        for index, row in enumerate(rows):
            validate_qbft_commit(row, f"{prefix}: QBFT {scenario}[{index}]")
    stalled = qbft["observations"]["two_validators_offline_block_probes"]
    require(len(stalled) >= min_observations, f"{prefix}: QBFT stall-probe sample too small")
    require(
        len({int(row["block_number"]) for row in stalled}) == 1,
        f"{prefix}: QBFT produced blocks with only 2/4 validators",
    )
    recovery = qbft["lifecycle"]["recovery"]
    require(
        recovery.get("method")
        == "operator-assisted active-validator restart after quorum restoration",
        f"{prefix}: missing or unexpected QBFT recovery procedure",
    )
    require(
        recovery.get("round_timeout_reset") is True,
        f"{prefix}: QBFT round-timeout reset was not recorded",
    )
    require(
        recovery.get("restarted_validators")
        == ["qbft1", "qbft2", "qbft3"],
        f"{prefix}: unexpected QBFT recovery validator set",
    )
    require(
        float(recovery["recovery_ms"]) >= 0,
        f"{prefix}: invalid QBFT recovery time",
    )
    return data


def aggregate(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    raft_scenarios = (
        "baseline",
        "one_follower_offline",
        "post_leader_failover",
        "recovered",
    )
    qbft_scenarios = ("baseline", "one_validator_offline", "recovered")
    raft_summary = {
        scenario: stats(
            row["latency_ms"]
            for session in sessions
            for row in session["raft"]["observations"][scenario]
        )
        for scenario in raft_scenarios
    }
    qbft_summary = {
        scenario: stats(
            row["first_inclusion_latency_ms"]
            for session in sessions
            for row in session["qbft"]["observations"][scenario]
        )
        for scenario in qbft_scenarios
    }
    raft_summary["leader_failover_recovery"] = stats(
        session["raft"]["lifecycle"]["leader_failover"]["recovery_ms"]
        for session in sessions
    )
    raft_summary["cluster_recovery"] = stats(
        session["raft"]["lifecycle"]["recovery"]["recovery_ms"] for session in sessions
    )
    qbft_summary["quorum_recovery"] = stats(
        session["qbft"]["lifecycle"]["recovery"]["recovery_ms"] for session in sessions
    )
    return {
        "schema": "zktrustllm.permissioned-consensus-fault-summary.v3",
        "session_count": len(sessions),
        "session_ids": [session["session_id"] for session in sessions],
        "git_commit": sessions[0]["git"]["commit"],
        "claim_boundary": sessions[0]["claim_boundary"],
        "raft": raft_summary,
        "qbft": qbft_summary,
        "quorum_loss": {
            "raft_failed_writes": sum(
                len(session["raft"]["observations"]["majority_loss"]) for session in sessions
            ),
            "raft_total_writes": sum(
                len(session["raft"]["observations"]["majority_loss"]) for session in sessions
            ),
            "qbft_stalled_probes": sum(
                len(session["qbft"]["observations"]["two_validators_offline_block_probes"])
                for session in sessions
            ),
            "qbft_total_probes": sum(
                len(session["qbft"]["observations"]["two_validators_offline_block_probes"])
                for session in sessions
            ),
        },
    }


def fmt(value: float) -> str:
    if value >= 100:
        return f"{value:.1f}"
    return f"{value:.2f}"


def write_csv(out_dir: Path, summary: dict[str, Any]) -> None:
    path_out = out_dir / "summary_permissioned_faults.csv"
    with path_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["family", "condition", "n", "median_ms", "p95_ms", "mean_ms", "stdev_ms"])
        for family in ("raft", "qbft"):
            for condition, values in summary[family].items():
                writer.writerow(
                    [
                        family,
                        condition,
                        values["n"],
                        f"{values['median']:.6f}",
                        f"{values['p95']:.6f}",
                        f"{values['mean']:.6f}",
                        f"{values['stdev']:.6f}",
                    ]
                )


def write_latex(out_dir: Path, summary: dict[str, Any]) -> None:
    raft = summary["raft"]
    qbft = summary["qbft"]
    loss = summary["quorum_loss"]
    table = rf"""% Generated by analyze_permissioned_faults.py; do not edit manually.
\begin{{table*}}[!t]
\centering
\caption{{Measured permissioned-consensus crash/non-participation experiment. Latencies are compared only within each implementation because etcd key/value replication and EVM contract execution are different workloads.}}
\label{{tab:permissioned-fault-results}}
\footnotesize
\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{llrrrr}}
\toprule
Implementation & Condition & $n$ & Median (ms) & P95 (ms) & Outcome \\
\midrule
etcd/Raft & Healthy baseline & {raft['baseline']['n']} & {fmt(raft['baseline']['median'])} & {fmt(raft['baseline']['p95'])} & writes committed \\
etcd/Raft & One follower offline & {raft['one_follower_offline']['n']} & {fmt(raft['one_follower_offline']['median'])} & {fmt(raft['one_follower_offline']['p95'])} & writes committed \\
etcd/Raft & After leader failover & {raft['post_leader_failover']['n']} & {fmt(raft['post_leader_failover']['median'])} & {fmt(raft['post_leader_failover']['p95'])} & writes committed \\
etcd/Raft & Majority unavailable & {loss['raft_total_writes']} & -- & -- & {loss['raft_failed_writes']}/{loss['raft_total_writes']} writes rejected/timed out \\
\addlinespace
Besu/QBFT & Healthy baseline & {qbft['baseline']['n']} & {fmt(qbft['baseline']['median'])} & {fmt(qbft['baseline']['p95'])} & anchors included \\
Besu/QBFT & One validator offline (3/4 active) & {qbft['one_validator_offline']['n']} & {fmt(qbft['one_validator_offline']['median'])} & {fmt(qbft['one_validator_offline']['p95'])} & anchors included \\
Besu/QBFT & Two validators offline (2/4 active) & {loss['qbft_total_probes']} & -- & -- & {loss['qbft_stalled_probes']}/{loss['qbft_total_probes']} no-progress probes \\
Besu/QBFT & Recovered four-validator cluster & {qbft['recovered']['n']} & {fmt(qbft['recovered']['median'])} & {fmt(qbft['recovered']['p95'])} & anchors included \\
\bottomrule
\end{{tabular}}
\end{{table*}}
"""
    (out_dir / "table_permissioned_faults.tex").write_text(table, encoding="utf-8")

    text = rf"""% Generated by analyze_permissioned_faults.py; do not edit manually.
Across {summary['session_count']} independent clean sessions, the real three-member
etcd/Raft cluster committed all {raft['one_follower_offline']['n']} retained writes
with one follower offline and rejected or timed out all
{loss['raft_failed_writes']}/{loss['raft_total_writes']} retained writes after
majority loss.  Its observed leader-failover recovery time was
{fmt(raft['leader_failover_recovery']['median'])}\,ms (median across sessions).
The real four-validator Besu/QBFT network included all
{qbft['one_validator_offline']['n']} retained audit-anchor transactions with one
validator stopped, produced no block-height change in
{loss['qbft_stalled_probes']}/{loss['qbft_total_probes']} retained probes with
only two validators active.  After quorum restoration and the documented
operator-assisted restart that reset the backed-off QBFT round timers, block
production resumed after a median
{fmt(qbft['quorum_recovery']['median'])}\,ms.
These interventions measure process crash/non-participation and quorum loss;
they do not inject equivocation, forged votes, or arbitrary Byzantine messages.
Absolute Raft and QBFT latencies are not ranked because the measured workloads
differ.
"""
    (out_dir / "results_permissioned_faults.tex").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmarks", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-sessions", type=int, default=3)
    parser.add_argument("--min-observations", type=int, default=30)
    parser.add_argument(
        "--allow-smoke",
        action="store_true",
        help="Permit dirty/non-publication runs; never use generated values in a manuscript.",
    )
    args = parser.parse_args()

    require(
        len(args.benchmarks) >= args.min_sessions,
        f"Need at least {args.min_sessions} independent sessions",
    )
    sessions = [
        validate_session(
            benchmark,
            min_observations=args.min_observations,
            allow_smoke=args.allow_smoke,
        )
        for benchmark in args.benchmarks
    ]
    session_ids = [session["session_id"] for session in sessions]
    require(len(set(session_ids)) == len(session_ids), "Session IDs must be distinct")
    commits = {session["git"]["commit"] for session in sessions}
    require(len(commits) == 1, "All sessions must use the same Git commit")
    runner_hashes = {
        session["implementation_hashes"]["runner_sha256"] for session in sessions
    }
    require(len(runner_hashes) == 1, "Runner implementation changed between sessions")
    analyzer_hashes = {
        session["implementation_hashes"]["analyzer_sha256"] for session in sessions
    }
    require(len(analyzer_hashes) == 1, "Analyzer implementation changed between sessions")
    require(
        len({session["raft"]["binary_sha256"] for session in sessions}) == 1,
        "etcd binary changed between sessions",
    )
    require(
        len({session["qbft"]["binary_sha256"] for session in sessions}) == 1,
        "Besu binary changed between sessions",
    )

    summary = aggregate(sessions)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary_permissioned_faults.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(args.out, summary)
    write_latex(args.out, summary)
    print(f"Validated {len(sessions)} sessions; wrote {args.out}")


if __name__ == "__main__":
    main()
