# Artifact Mapping (Paper ↔ Code)

Entry point:
  scripts/reproduce_all.sh

Output directory:
  artifacts/out/

Baselines:
- Oracle-only (no ZK):
    scripts/baselines/run_oracle_only.sh
    artifacts/out/baseline_oracle_only/
- No-IPFS evidence (local store):
    scripts/baselines/run_no_ipfs.sh
    artifacts/out/baseline_no_ipfs/

Scoring / reputation:
- Spec: docs/scoring.md
- Implementation: update this file later to point to the exact source file/function used in your repo.

Evidence vs media delivery (important):
- Live media delivery: DTLS/RTP/multicast plane
- Evidence storage: IPFS (CID) + on-chain commitments for auditability

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

## L4 AUTH_V1 Groth16 artifact path

Primary runner:
- `scripts/l4/run_auth_v1_groth16_repro.sh`

Summary note:
- `docs/l4/AUTH_V1_ARTIFACT_SUMMARY.md`

Key milestone tags:
- `l4-auth-v1-first-real-groth16-submit`
- `l4-auth-v1-groth16-negative-test`
- `l4-auth-v1-groth16-repro`
