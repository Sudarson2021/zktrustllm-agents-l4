# ZKTrustLLM-Agents L4 Artifact Mapping

This document maps the journal manuscript claims to executable scripts and generated artifacts. It is intentionally conservative: a paper claim is only marked as supported when an output file exists and the validation script can verify it.

## Reproducibility entry points

| Purpose | Command | Output |
|---|---|---|
| Full paper-oriented validation wrapper | `bash scripts/reproduce_paper_258.sh` | `artifacts/out/paper_258/` |
| Original core local pipeline | `bash scripts/reproduce_all.sh` | `artifacts/out/` |
| Oracle-only baseline | `bash scripts/baselines/run_oracle_only.sh` | `artifacts/out/baseline_oracle_only/results.ndjson` |
| No-IPFS baseline | `bash scripts/baselines/run_no_ipfs.sh` | `artifacts/out/baseline_no_ipfs/tenants_results.ndjson` |
| AI single-agent/multi-model scenarios | `python3 scripts/l4/n8n/run_multi_model_tool_scenarios.py ...` | `runtime_artifacts/n8n/model_tool_scenarios/records.jsonl` |
| AI table builder | `python3 scripts/l4/metrics/build_n8n_model_tool_tables.py ...` | Markdown/CSV/LaTeX tables |
| Direct telemetry packet-capture smoke test | `bash scripts/l4/media/run_packet_capture_smoke.sh` | `artifacts/out/paper_258/media_capture/` |
| AUTH_V2.x timing boundary check | `bash scripts/l4/zk/collect_auth_v2_timing_guarded.sh` | `artifacts/out/paper_258/zk_timing/` |
| Claim validation report | `python3 scripts/l4/validation/validate_paper_258_claims.py` | `artifacts/out/paper_258/validation/claim_validation_report.md` |

## Paper claim boundary

| Manuscript claim | Evidence status | Required artifact |
|---|---|---|
| Reproducible orchestration via n8n | Supported only when exported workflow JSON, run records, and Git hash are present | `artifacts/out/n8n/`, `runtime_artifacts/n8n/` |
| 240-record local evidence matrix | Supported only if 6 variants × 4 profiles × 10 repeats are present in validated CSV/JSON | `artifacts/out/paper_258/validation/claim_validation_report.json` |
| Stage 3 runtime hooks for anchor gas and negative-security checks | Supported only if logs show anchor gas, replay rejection, zero-anchor rejection, and unauthorized-submitter rejection | Stage 3 JSON/CSV/log outputs |
| Stage 4 Sepolia audit micro-benchmark | Supported only if contract address, deploy tx, anchor tx, block number, and gas usage are recorded | Sepolia JSON output |
| Stage E/F live model evaluation | Supported only by COMPLETED rows with raw provider response hashes | `runtime_artifacts/n8n/model_tool_scenarios/records.jsonl` |
| Stage F/F multi-agent evaluation | Supported only by live chain records with per-agent raw outputs and hashes | `runtime_artifacts/n8n/multi_agent_ablations/records.jsonl` |
| Packet-capture or telemetry experiment | Supported only if pcap/pcapng and parsed summary exist | `artifacts/out/paper_258/media_capture/packet_telemetry_summary.json` |
| AUTH_V2.x prover timing | Full support only if direct AUTH_V2.x prover logs exist for all reported rows; otherwise report as bounded/partial | `artifacts/out/paper_258/zk_timing/auth_v2_timing_summary.json` |

## Permissioned-consensus fault evaluation

- Experiment protocol:
  `docs/l4/consensus/RAFT_QBFT_FAULT_EXPERIMENT.md`
- Client installer:
  `scripts/l4/consensus/permissioned/install_clients.sh`
- Real etcd/Raft and Besu/QBFT driver:
  `scripts/l4/consensus/permissioned/run_permissioned_fault_benchmark.js`
- Publication-session wrapper:
  `scripts/l4/consensus/permissioned/run_publication_session.sh`
- Evidence analyzer:
  `scripts/l4/consensus/analyze_permissioned_faults.py`
- Analysis tests:
  `test/l4/test_permissioned_fault_analysis.py`
- Raw publication evidence (copied only after strict validation):
  `runtime_artifacts/permissioned_faults/<session-id>/`
- Generated journal artifacts (after strict validation):
  `paper/l4_conference/derived_consensus/*permissioned_faults*`

## Evidence vs media delivery

- Live media delivery remains DTLS/RTP/multicast or configured telemetry/media profiles.
- IPFS/CID is used for audit evidence objects, not for live video streaming.
- Smart-contract anchoring stores compact commitments and rejection evidence; it does not prove physical network truth.

## Negative-security evidence

The artifact should preserve rejection evidence for:

1. duplicate/replay commitment;
2. zero commitment;
3. unauthorized submitter;
4. unsafe or forbidden action class;
5. claim-boundary overreach.

## Non-claims

The artifact does not claim:

- production-grade O-RAN deployment;
- Ethereum mainnet performance;
- semantic correctness of LLM reasoning;
- packet-capture QoE unless a packet-capture artifact is generated;
- complete AUTH_V2.x prover timing unless direct timing logs exist for every reported row.
