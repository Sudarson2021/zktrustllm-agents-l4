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

## L4 A2A Reference-Aware Coordination

This extension implements the supervisor-aligned Level 4 direction: blockchain as authenticated shared memory for multi-agent AI coordination.

Main artifacts:

- Supervisor alignment note: `docs/l4/a2a_reference/SUPERVISOR_ALIGNMENT.md`
- A2A compact reference schema: `schemas/a2a_reference_message.json`
- A2A registry contract: `contracts/l4/A2AReferenceRegistry.sol`
- Deployment script: `scripts/l4/deploy_a2a_reference_registry.js`
- Registry verification script: `scripts/l4/check_a2a_reference_registry.js`
- AUTH_V2.2 decision checker: `scripts/l4/check_auth_v2_2_decisions.js`
- A2A registration demo: `scripts/l4/register_a2a_reference_from_latest_decision.js`
- Demo result: `results/l4_a2a_reference/a2a_reference_latest_decision.json`
- Runtime AUTH_V2.2 proof files: `runtime_artifacts/l4/auth_v2_2/`

Demonstrated result:

- AUTH_V2.2 proof-backed decision count: 1
- A2A reference count: 1
- A2A reference validity: true
- A2A reference registration gas: 440349

Research meaning:

Agent A creates a proof-backed authenticated decision on-chain. Agent B can then rely on a compact reference to that decision instead of receiving the full raw decision, policy, or evidence payload. This demonstrates blockchain-anchored authenticated state as a coordination substrate for Level 4 agent-to-agent interaction.

## L4 Proper MCP Context Server

This section adds a proper read-only MCP server for Level 4 proof-governed coordination.

Main artifacts:

- MCP server: `mcp_l4/server.py`
- MCP server README: `mcp_l4/README.md`
- MCP client test: `scripts/l4/test_mcp_l4_server.py`
- MCP test result: `results/l4_mcp_server/mcp_tool_test_results.json`
- MCP bundle verification result: `results/l4_mcp_server/mcp_reference_bundle_verification.json`
- MCP integration analysis: `docs/l4/mcp_a2a_kpi/PROPER_MCP_INTEGRATION.md`
- MCP Python requirements: `requirements-l4-mcp.txt`

Measured result:

- MCP tools listed: 5
- successful MCP tool calls: 5/5
- MCP context retrieval success rate: 1.0
- average tool invocation latency: 29.711 ms
- maximum tool invocation latency: 39.757 ms
- reference bundle validity: true
- reference bundle verification latency: 32.298 ms

Research meaning:

A2A provides compact inter-agent reference exchange. MCP provides structured access to the authenticated blockchain context behind those references. The implemented MCP tools allow an agent to retrieve and verify AUTH_V2.2 decisions and A2A references without directly receiving full raw decision or evidence payloads.
