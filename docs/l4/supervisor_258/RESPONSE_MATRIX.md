# Supervisor Comment Response Matrix - [258] ZKTrustLLM-Agents L4 Journal Paper

This document maps each supervisor comment to the concrete manuscript, figure, table, formal-verification, and evaluation upgrades required for the next journal version.

## Comment-to-Action Matrix

| No. | Supervisor comment | Required upgrade | Paper output | Repo / evaluation output |
|---:|---|---|---|---|
| 1 | Formal verification tool should validate Table II observations. | Add TLA+ / TLC model checking and Solidity invariant tests. | New formal verification subsection and revised Table II. | `formal/tla/ZKTrustLLMPolicyGate.tla`, Hardhat invariant tests, verification logs. |
| 2 | Stronger visual and numerical scientific validation. | Add repeated-run KPI tables, ablation plots, gas/proof/latency measurements. | Results section with quantitative KPIs. | n8n-run CSV/JSON evidence, figures, Markdown tables. |
| 3 | Figure 1 should better represent architecture, workflow, and components. | Replace generic diagram with O-RAN + agentic loop + evidence/trust-plane architecture. | New Fig. 1. | `figures/l4/revision/fig1_oran_l4_architecture.*` |
| 4 | Add visual threat examples. | Add threat-response diagrams for replay, unsafe action, evidence tampering, compromised xApp. | New threat-model figure. | `figures/l4/revision/fig2_threat_response_examples.*` |
| 5 | Explain how many agentic AI components are used and their roles. | Define Telemetry, Reasoning, Policy, Proof, and Audit/Anchor agents. | New agentic AI subsection. | Agent-role table and n8n evaluation mapping. |
| 6 | Consider CCG-series or similar reasoning/control mechanisms. | Present OBSERVE -> REASON -> PROVE -> ANCHOR -> ACT as controlled cyclic governance. | Reasoning/control-loop subsection. | n8n workflow mirrors this loop. |
| 7 | Clear comparison against existing approaches. | Replace descriptive comparison with measurable criteria. | Strengthened Table I. | Quantitative novelty matrix. |
| 8 | Justify smart-contract role between customer and provider. | Explain what contract can/cannot do in the MNO/customer scenario. | Smart-contract boundary subsection. | Contract role evidence table. |
| 9 | Include test modes for other blockchain consensus algorithms. | Compare local Hardhat, public testnet, permissioned PoA/IBFT-style, BFT-style, Fabric-style modes. | Consensus/test-mode table. | `scripts/l4/consensus_modes/` |
| 10 | Compare access-control algorithms. | Compare OwnerOnly, RBAC, capability-based, ABAC/policy registry, ZK-bound access. | Access-control comparison table. | `scripts/l4/access_control/` |
| 11 | Open RAN MNO policy insufficient. | Add architecture showing policy inside SMO/Non-RT RIC and A1 path to Near-RT RIC/xApps. | New O-RAN policy-placement figure. | `figures/l4/revision/fig_openran_policy_placement.*` |
| 12 | Ablation study for ZK component. | Compare Full L4, No-ZK, Oracle-only, RBAC-only, No-IPFS, No-policy-gate. | ZK ablation subsection and figure. | `scripts/l4/ablation/`, n8n run matrix. |
| 13 | Computational complexity. | Add complexity of hashing, policy check, proof generation, verification, anchoring, consensus confirmation. | Complexity-analysis section. | `docs/l4/supervisor_258/COMPLEXITY_ANALYSIS.md` |
| 14 | Add demo KPIs. | Add reason latency, proof time, gas, jitter, loss, A2A size, anchor gas, queue state. | Demo KPI table. | n8n KPI extractor output. |
| 15 | Table I needs quantitative validation. | Convert Table I into numerical novelty/comparison matrix. | Revised Table I. | `N8N_SCIENTIFIC_NOVELTY_MATRIX.md` |

## Target Scientific Claim

ZKTrustLLM-Agents L4 is not merely a dashboard or automation demo. It is a reproducible, policy-gated, evidence-preserving evaluation framework for accountable autonomous O-RAN security workflows.

## Required Evaluation Principle

Every result must be supported by:

1. raw log,
2. parsed KPI JSON,
3. run identifier,
4. Git commit hash,
5. impairment profile or baseline variant,
6. evidence hash,
7. table/figure output,
8. paper-ready interpretation.
