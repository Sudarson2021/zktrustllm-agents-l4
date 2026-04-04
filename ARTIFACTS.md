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

## L4 AUTH_V1 Groth16 artifact path

Primary runner:
- `scripts/l4/run_auth_v1_groth16_repro.sh`

Summary note:
- `docs/l4/AUTH_V1_ARTIFACT_SUMMARY.md`

Key milestone tags:
- `l4-auth-v1-first-real-groth16-submit`
- `l4-auth-v1-groth16-negative-test`
- `l4-auth-v1-groth16-repro`
