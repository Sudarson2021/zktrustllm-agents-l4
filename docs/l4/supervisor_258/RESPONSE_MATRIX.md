# Supervisor Comment Response Matrix - [258] ZKTrustLLM-Agents L4 Journal Paper

This document maps each supervisor comment to the concrete manuscript, figure, table, formal-verification, and evaluation upgrades required for the next journal version.

| No. | Supervisor comment | Required upgrade | Paper output | Repo / evaluation output |
|---:|---|---|---|---|
| 1 | Formal verification tool should validate Table II observations. | Add TLA+ / TLC model checking and Solidity invariant tests. | Formal verification subsection and revised Table II. | TLA+ model, Hardhat invariant tests, verification logs. |
| 2 | Stronger visual and numerical validation. | Add repeated-run KPI tables, ablation plots, gas/proof/latency measurements. | Quantitative results section. | n8n CSV/JSON evidence, figures, Markdown tables. |
| 3 | Figure 1 should better represent architecture. | Replace generic diagram with O-RAN + agentic loop + evidence/trust-plane architecture. | New Fig. 1. | O-RAN L4 architecture figure. |
| 4 | Add visual threat examples. | Add replay, unsafe escalation, evidence tampering, and compromised xApp examples. | Threat-response figure. | Threat-response evaluation artifacts. |
| 5 | Explain agentic AI components. | Define Telemetry, Reasoning, Policy, Proof, and Audit/Anchor agents. | Agentic AI subsection. | Agent-role matrix. |
| 6 | Consider CCG/control reasoning mechanisms. | Present OBSERVE -> REASON -> PROVE -> ANCHOR -> ACT as controlled cyclic governance. | Reasoning/control-loop subsection. | n8n workflow mirrors this loop. |
| 7 | Clearer comparison against existing approaches. | Replace descriptive comparison with measurable criteria. | Strengthened Table I. | Quantitative novelty matrix. |
| 8 | Justify smart-contract role. | Explain what the contract can/cannot do between tenant/customer and provider/MNO. | Smart-contract boundary subsection. | Contract-boundary table. |
| 9 | Include blockchain consensus/test modes. | Compare Hardhat, Sepolia, permissioned PoA/IBFT-style, BFT-style, and Fabric-style modes. | Consensus/test-mode table. | scripts/l4/consensus_modes. |
| 10 | Compare access-control algorithms. | Compare OwnerOnly, RBAC, capability-based, ABAC/policy registry, and ZK-bound access. | Access-control comparison table. | scripts/l4/access_control. |
| 11 | Consider Open RAN MNO policy. | Place policy in SMO/Non-RT RIC and show A1 delivery to Near-RT RIC/xApps. | O-RAN policy-placement figure. | Open RAN policy architecture artifact. |
| 12 | Add ZK ablation. | Compare Full L4, No-ZK, Oracle-only, RBAC-only, No-IPFS, and No-policy-gate. | Ablation subsection and figure. | scripts/l4/ablation and n8n matrix. |
| 13 | Add computational complexity. | Add complexity for hashing, policy check, proof generation, verification, anchoring, and consensus. | Complexity-analysis section. | Complexity note. |
| 14 | Add demo KPIs. | Add reason latency, proof time, gas, jitter, loss, A2A size, anchor gas, and queue state. | Demo KPI table. | n8n KPI extractor output. |
| 15 | Strengthen Table I. | Convert Table I into a quantitative comparison matrix. | Revised Table I. | N8N scientific novelty matrix. |

## Required Evidence Principle

Every reported result should be backed by:
1. run identifier,
2. timestamp,
3. Git commit hash,
4. experiment variant,
5. impairment profile,
6. raw log,
7. parsed KPI JSON,
8. evidence hash,
9. paper-ready table or figure.

## Target Scientific Claim

ZKTrustLLM-Agents L4 is a reproducible, policy-gated, evidence-preserving evaluation framework for accountable autonomous O-RAN security workflows.
