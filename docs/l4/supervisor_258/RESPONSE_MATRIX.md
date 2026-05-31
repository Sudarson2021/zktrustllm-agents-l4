# Supervisor Comment Response Matrix - [258] ZKTrustLLM-Agents L4 Journal Paper

## Required upgrades

1. Formal verification of Table II observations
- Add TLA+ / TLC policy-loop model.
- Add Solidity invariant tests for replay, zero anchor, unauthorized submitter, and policy admissibility.

2. Stronger Figure 1
- Replace generic workflow with O-RAN + agentic loop + evidence/trust plane architecture.
- Place MNO policy in SMO / Non-RT RIC and map policy delivery through A1.

3. Threat visual examples
- Add replay attack, evidence tampering, unsafe escalation, compromised xApp.

4. Agentic AI components
- Define Telemetry Agent, Reasoning Agent, Policy Agent, Proof Agent, Audit/Anchor Agent.

5. Quantitative comparison
- Replace descriptive Table I with measurable criteria and ablation variants.

6. Smart contract boundary
- Explain what the contract can and cannot do between tenant/customer and MNO/provider.

7. Consensus/test modes
- Compare Hardhat, Sepolia, permissioned PoA/IBFT, CometBFT/Fabric-style modes.

8. Access-control comparison
- Compare OwnerOnly, RBAC, Capability-based, ABAC/policy registry, and ZK-bound access.

9. Open RAN MNO policy architecture
- Add standard O-RAN policy placement figure.

10. ZK ablation
- Full vs No-ZK vs Oracle-only vs RBAC-only vs No-IPFS vs No-policy-gate.

11. Complexity
- Add O(n*b), O(c), O(1) verification/storage analysis.

12. Demo KPIs
- Include reason latency, prover time, gas, jitter, loss, anchor gas, queue status.

13. Strengthened Table I
- Convert to quantitative comparison table.
