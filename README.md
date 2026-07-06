# ZKTrustLLM-Agents L4

Proof-governed agentic zero-trust control and reproducible evaluation for O-RAN edge security.

This repository contains artifact support for the ZKTrustLLM-Agents L4 journal manuscript. The goal is to make each major paper claim traceable to scripts, logs, hashes, generated tables, and explicit claim boundaries.

## Scope

ZKTrustLLM-Agents L4 evaluates governed autonomous O-RAN security workflows. It separates O-RAN governance, bounded telemetry/reasoning/policy/proof/audit agents, and evidence/trust/reproducibility functions.

The artifact focuses on reproducibility, policy gating, audit anchoring, negative-security rejection checks, and bounded AI-assisted workflow evaluation.

## Quick start

Run:

    bash scripts/reproduce_paper_258.sh

Outputs are written to:

    artifacts/out/paper_258/

## Main commands

- Paper-level validation wrapper: bash scripts/reproduce_paper_258.sh
- Core local reproduction: bash scripts/reproduce_all.sh
- Oracle-only baseline: bash scripts/baselines/run_oracle_only.sh
- No-IPFS baseline: bash scripts/baselines/run_no_ipfs.sh
- Packet-capture/direct telemetry smoke test: bash scripts/l4/media/run_packet_capture_smoke.sh
- AUTH_V2.x timing boundary check: bash scripts/l4/zk/collect_auth_v2_timing_guarded.sh
- Paper claim validation: python3 scripts/l4/validation/validate_paper_258_claims.py

## Claim boundary

This repository supports local scientific validation. It does not claim production-grade O-RAN deployment, Ethereum mainnet performance, semantic correctness of LLM reasoning, live media QoE unless a packet-capture experiment is explicitly run, or complete AUTH_V2.x prover timing unless direct timing logs exist for every reported row.

## API-key handling

For live AI evaluation, copy config/n8n/ai_eval.env.example to .env.ai_eval, fill keys locally, and source it. Never commit .env.ai_eval or raw logs containing provider credentials.

## Paper-to-code mapping

See ARTIFACTS.md.

## Evidence classes

The artifact separates direct runtime evidence, public-testnet evidence, configured profile evidence, reproducibility evidence, and claim-boundary evidence. Configured media-profile values must not be reported as packet-capture measurements.
