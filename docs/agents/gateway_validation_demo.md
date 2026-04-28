# Gateway Validation Demo

## Purpose
This document defines the first end-to-end gateway validation demo for the L4 ZKTrustLLM-Agents control plane.

The demo shows how a gateway-style request can be checked against:
- `AgentRegistry.sol`
- `CapabilityManager.sol`
- `PolicyRegistry.sol`

without yet extending the Groth16 path.

---

## 1. Preconditions

Before running the demo:
1. localhost Hardhat node must be running
2. control-plane contracts must be deployed
3. smoke test must have already registered demo agents and issued demo capabilities

Relevant scripts:
- `scripts/l4/deploy_control_plane.js`
- `scripts/l4/smoke_test_control_plane.js`

---

## 2. Validation Goals

The gateway demo should answer:
- is the sender active
- is the sender role allowed for the requested policy class
- is the capability valid
- is the capability usable for the requested policy/action/context
- is the requested action allowed for the declared trust state

---

## 3. Positive Case

The positive case uses:
- agent: `policy-lkh-01`
- capability: `cap-policy-01`
- policy class: `policy-enforce`
- action class: `isolate`
- trust state: `Restricted`
- context: `ctx-policy`

Expected result:
- `ACCEPT`

Reason:
- the sender is active
- the role is allowed for `policy-enforce`
- the capability is valid
- the capability matches policy/action/context
- `Restricted -> isolate` is allowed by `PolicyRegistry.sol`

---

## 4. Negative Case

The negative case uses:
- agent: `trust-risk-01`
- capability: `cap-risk-01`
- policy class: `policy-enforce`
- action class: `isolate`
- trust state: `Restricted`
- context: `ctx-risk`

Expected result:
- rejection

Preferred rejection class:
- `REJECT_POLICY_ROLE`

Reason:
- `TrustRiskAgent` is not allowed to operate under `policy-enforce`

---

## 5. Initial Rejection Codes

The first demo should use explicit outcomes:
- `ACCEPT`
- `REJECT_IDENTITY`
- `REJECT_POLICY_ROLE`
- `REJECT_CAPABILITY`
- `REJECT_CAPABILITY_OWNER`
- `REJECT_CAPABILITY_SCOPE`
- `REJECT_TRUST_ACTION`

---

## 6. Current Scope

This demo is intentionally off-chain and contract-assisted.

It does not yet:
- verify message signatures
- validate payload hashes
- prove policy admissibility in zero knowledge
- execute media-path actions

---

## 7. Status

This document freezes the first gateway validation demo for the L4 ZKTrustLLM-Agents control plane.
