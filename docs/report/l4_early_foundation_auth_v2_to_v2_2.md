# ZKTrustLLM-Agents L4 Earlier Foundation: AUTH_V2 to AUTH_V2.2

## Purpose

This document incorporates the earlier implementation history into the current Level 4 project documentation.

The earlier foundation established the control-plane, gateway, contract, and proof pipeline that later Steps 77-93 build upon.

## Earlier Project Foundation

The earlier L4 work implemented:

- documented Level 4 control-plane architecture,
- Solidity control-plane contracts,
- gateway-assisted validation,
- AUTH_V2 Groth16 proof path,
- AUTH_V2.1 policy-admissibility proof path,
- AUTH_V2.2 trust-state-aware admissible-action proof path,
- positive proof verification and on-chain decision submission,
- negative rejection flows for tampered or invalid proofs,
- stable Git checkpointing for safe continuation.

## Core Contracts

The earlier contract layer included:

| Contract | Role |
|---|---|
| AgentRegistry.sol | Registers and manages active/suspended/revoked agents |
| CapabilityManager.sol | Issues and validates short-lived bounded capabilities |
| PolicyRegistry.sol | Stores role-policy and trust-state/action admissibility rules |
| DecisionAttestorAuthV2.sol | Stores AUTH_V2 proof-backed decisions |
| DecisionAttestorAuthV2_1.sol | Stores AUTH_V2.1 policy-admissible decisions |
| DecisionAttestorAuthV2_2.sol | Stores AUTH_V2.2 trust-state-aware decisions |

## Gateway Validation

The gateway validation stage checked:

- whether the agent is registered,
- whether the capability is valid,
- whether the role-policy pairing is allowed,
- whether the trust-state/action pairing is admissible.

The positive validation path accepted:

- agent: `policy-lkh-01`
- policy class: `policy-enforce`
- action class: `isolate`
- trust state: `Restricted`

The negative validation path rejected role-policy mismatch using:

- `REJECT_POLICY_ROLE`

## AUTH_V2

AUTH_V2 introduced the first control-plane-aware proof binding.

It bound:

- `agentKey`
- `capabilityId`
- `policyClassHash`
- `actionClass`
- `contextHash`
- `traceCommitment`
- `expiryBucket`

with private witness:

- `bindingNonce`

## AUTH_V2.1

AUTH_V2.1 added policy admissibility.

New public field:

- `policyAdmissibilityFlag`

Core condition:

- `policyAdmissibilityFlag == 1`

This made the proof explicitly policy-aware.

## AUTH_V2.2

AUTH_V2.2 added trust-state awareness.

New public field:

- `trustState`

Implemented admissible pair:

- `Restricted -> Isolate`

Core constraints:

- `policyAdmissibilityFlag == 1`
- `trustState == 3`
- `actionClass == 3`

## Strongest Earlier Claim

The strongest earlier implementation claim was:

The repository supports trust-state-aware, policy-admissibility-aware, bounded Groth16 decision submission for the concrete admissible path `Restricted -> Isolate`.

## Why This Matters for the Current Project

The later Steps 77-93 build on this foundation.

The earlier work provides:

- proof-governed decision semantics,
- on-chain attestation,
- bounded trust-state/action logic,
- contract-backed authorization context,
- reproducible checkpointing.

The later work extends this into:

- MCP context retrieval,
- A2A reference-based coordination,
- reference-bound proof validation,
- semi-live control-plane telemetry,
- multi-agent scaling,
- live RTP media-plane telemetry,
- DTLS-wrapped RTP validation,
- network impairment testing,
- Linux network namespace validation.

