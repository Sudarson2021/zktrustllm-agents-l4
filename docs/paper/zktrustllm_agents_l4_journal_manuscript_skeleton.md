# ZKTrustLLM-Agents L4: Policy-Gated Agentic Automation, Audit Provenance, and Blockchain-Verifiable Trust Anchoring

## Abstract

This paper presents ZKTrustLLM-Agents L4, a policy-gated agentic automation and audit framework for secure 5G/O-RAN edge intelligence workflows. The system integrates automated experiment execution, KPI-driven decision making, human-approved remediation, hash-chained audit provenance, IPFS-based evidence anchoring, and smart-contract-based trust-plane validation. Unlike isolated automation scripts, the proposed framework provides an end-to-end evidence lifecycle in which experiment outputs are validated, transformed into audit artifacts, anchored through content-addressed storage, and verified through a local blockchain registry with negative-security testing. The implemented prototype demonstrates repeatable automation, policy-based governance boundaries, replay-resistant audit-anchor registration, and persistent local Hardhat validation. The results show that policy-gated agentic automation can support reproducible, auditable, and blockchain-verifiable research workflows for future secure 5G/O-RAN and multi-agent AI systems.

## Keywords

ZKTrustLLM; agentic AI; MCP; A2A; Zero Trust; IPFS; blockchain; audit ledger; smart contracts; 5G; O-RAN; DTLS; policy-gated automation.

## 1. Introduction

Future 5G/O-RAN and 6G systems require intelligent automation, but autonomous decision-making must be governed, auditable, and verifiable. In security-sensitive edge environments, it is not sufficient for an agentic AI system to execute experiments or make control-plane decisions. The system must also preserve evidence, expose governance boundaries, support reproducibility, and enable trust-plane verification.

This paper introduces ZKTrustLLM-Agents L4, a policy-gated automation and audit framework that connects experiment execution, KPI-based decisioning, human-approved remediation, hash-chained evidence, IPFS anchoring, and blockchain-based validation.

## 2. Contributions

The main contributions of this work are:

1. A policy-gated Level 4 agentic automation pipeline that connects MCP/A2A experiment execution, KPI decisioning, remediation, and reporting.
2. A hash-chained automation audit ledger that provides tamper-evident provenance across experiment, decision, remediation, governance, and reporting artifacts.
3. An IPFS and blockchain-ready anchoring workflow that binds the audit ledger to content-addressed evidence and compact trust-plane commitments.
4. A local smart-contract audit-anchor registry that validates anchor submission, commitment matching, and on-chain evidence retrieval.
5. Negative-security validation showing replay rejection and invalid zero-commitment rejection for the audit-anchor registry.
6. Persistent local Hardhat validation that moves beyond one-off ephemeral blockchain execution toward a long-running local trust-plane evaluation environment.

## 3. System Methodology

# Journal Methodology: Policy-Gated L4 Agentic Automation and Audit Anchoring

## 1. Methodological Overview

This work implements a Level 4 policy-gated agentic automation pipeline for ZKTrustLLM-Agents. The methodology moves beyond isolated experiment scripts by combining automated experiment execution, KPI-based decision making, human-approved remediation, audit-ledger construction, IPFS anchoring, and smart-contract-based trust-plane validation.

The implemented pipeline is structured as a closed-loop workflow. First, the automation suite executes the control-plane and media-plane experiments. Second, a KPI decision agent reads the generated evidence and recommends the next safe action. Third, a remediation executor performs the recommended action only after human approval. Fourth, governance and scheduler modules enforce explicit policy boundaries. Finally, the generated evidence is preserved in a hash-chained audit ledger, anchored through IPFS, and validated using a blockchain registry.

## 2. Automation Workflow

The automation workflow begins with Step 96, where the agentic automation suite executes the Level 4 evidence-generation pipeline. This includes MCP/A2A control-plane validation, semi-live control telemetry, multi-agent scaling telemetry, live RTP telemetry, DTLS-wrapped RTP telemetry, and optional network impairment experiments.

Step 97 introduces closed-loop KPI decision making. The decision agent reads JSON evidence artifacts and evaluates whether control-plane, media-plane, network, namespace, and automation outputs satisfy the expected thresholds. Based on this evaluation, it recommends a next action such as generating a supervisor report, rerunning a baseline, or repeating an impairment experiment.

Step 98 implements the remediation executor. This executor converts the Step 97 recommendation into a safe execution plan. It runs in dry-run mode by default and requires explicit human approval before executing any action. This preserves scientific control while still enabling partially autonomous remediation.

Step 100 extends this logic into a policy-gated autonomous scheduler. The scheduler connects Step 97 and Step 98 under an explicit automation policy. The policy defines actions that are allowed automatically, actions requiring human approval, actions requiring privileged approval, and actions that must never be automatic.

## 3. Audit-Ledger Construction

Step 101 introduces a hash-chained automation audit ledger. The ledger records key artifacts generated by the automation workflow and computes SHA-256 hashes for each artifact. Each entry is linked to the previous entry through a hash chain, creating tamper-evident provenance across the L4 automation process.

This audit ledger is important because it transforms experiment evidence from a set of independent files into a verifiable evidence chain. It supports reproducibility, supervisor review, and future journal evaluation by showing that the automation workflow can be audited after execution.

## 4. IPFS and Blockchain-Ready Anchoring

Step 102 anchors the audit ledger into an IPFS-ready and blockchain-ready commitment record. When IPFS is available, the ledger is added to IPFS and represented by a CID. The step also creates a canonical blockchain-ready anchor payload containing the ledger hash, ledger file SHA-256, IPFS CID, and anchor commitment hash.

This design follows the wider ZKTrustLLM trust-plane logic: large evidence artifacts remain off-chain, while compact commitments are made suitable for blockchain validation. The result is an audit architecture that avoids storing bulky evidence on-chain while still enabling commitment-bound verification.

## 5. On-Chain Registry Validation

Step 103 implements a local Hardhat smart-contract registry for audit-anchor storage. The registry stores the ledger hash, ledger SHA-256, IPFS CID, anchor type, anchor commitment hash, timestamp, and submitter address. The local Hardhat validation confirms that the audit anchor can be submitted and retrieved correctly.

Step 104 adds negative-security validation. It verifies that duplicate audit commitments are rejected and that zero commitments are rejected. This shows that the registry is not merely a passive storage contract; it enforces basic replay resistance and invalid-commitment rejection.

Step 105 integrates the on-chain validation into the policy-gated workflow. The validation can be executed only under explicit human approval, preserving the safety boundary between automation and blockchain actions.

Step 109 further strengthens this evaluation by validating the audit-anchor registry against a persistent local Hardhat JSON-RPC node. This is closer to a realistic long-running blockchain environment than a one-off ephemeral Hardhat execution while remaining safe and local.

## 6. Governance and Safety Boundary

The automation framework is intentionally conservative. It does not automatically push code, modify Git history, submit papers, email supervisors, deploy public-chain contracts, spend real funds, or delete research evidence. These actions remain outside the automatic control boundary.

The policy distinguishes between four categories:

1. Safe automatic actions, such as reading artifacts, validating JSON/CSV outputs, generating reports, and creating manifests.
2. Human-approved actions, such as executing remediation or regenerating reports.
3. Human-and-privileged-approved actions, such as running `tc netem` or namespace experiments requiring `sudo`.
4. Never-automatic actions, such as public deployment, paper submission, Git history modification, or evidence deletion.

## 7. Scientific Contribution

The implemented workflow contributes a practical architecture for policy-gated Level 4 agentic automation. It demonstrates that an AI-assisted research system can execute experiments, evaluate KPIs, recommend next actions, perform approved remediation, preserve tamper-evident evidence, anchor evidence through IPFS/blockchain-ready commitments, and validate trust-plane commitments through a smart-contract registry.

This provides a stronger contribution than a standalone blockchain or AI automation prototype. The novelty lies in the integration of automation, governance, auditability, content-addressed evidence, and blockchain-based trust-plane validation into one reproducible L4 research pipeline.

## 8. Current Boundary and Future Work

The current implementation is local and experimental. Hardhat is used for controlled blockchain validation, and IPFS is used locally for content addressing. Future work should extend the validation to repeated statistical runs, persistent local nodes over longer durations, controlled testnet dry-runs, and two-machine or testbed-based media-plane experiments.

Public-chain deployment should remain approval-gated and should only be considered after security review, gas-cost analysis, and a clear research justification.

## 4. Journal-Ready Architecture and Tables

# L4 Journal-Ready Architecture Figure and Result Tables: Steps 96-105

## Purpose

This document converts the implemented Level 4 automation/audit/on-chain workflow into journal-ready architecture and evaluation material.

## Figure 6.1

- PNG: `results/l4_journal_ready/figures/figure_6_1_l4_policy_gated_agentic_automation_architecture.png`
- PDF: `results/l4_journal_ready/figures/figure_6_1_l4_policy_gated_agentic_automation_architecture.pdf`
- SVG: `results/l4_journal_ready/figures/figure_6_1_l4_policy_gated_agentic_automation_architecture.svg`

Suggested caption:

> Figure 6.1. Policy-gated Level 4 ZKTrustLLM-Agents automation architecture. The workflow links automated experiment execution, KPI-based decisioning, human-approved remediation, governance, hash-chained audit provenance, IPFS/blockchain-ready anchoring, local on-chain registry validation, and replay/invalid-anchor negative-security testing.

## Table 6.1: Workflow Components

| Step | Component | Status / Decision | Role | Evidence |
|---|---|---|---|---|
| Step 96 | Agentic automation suite | PASS | Runs MCP/A2A, media-plane, DTLS, impairment, and namespace experiments. | results/l4_agentic_automation/agentic_automation_summary.json |
| Step 97 | Closed-loop KPI decision agent | GENERATE_SUPERVISOR_REPORT | Reads KPI artifacts and recommends the next safe action. | results/l4_closed_loop_agent/closed_loop_kpi_decision.json |
| Step 98 | Closed-loop remediation executor | EXECUTED_PASS | Executes approved remediation/report generation with human approval. | results/l4_remediation_executor/remediation_execution_plan.json |
| Step 99 | Automation governance dashboard | JSON_PRESENT | Summarises governance boundaries for supervisor review. | results/l4_automation_governance/automation_governance_dashboard.json |
| Step 100 | Policy-gated autonomous scheduler | EXECUTED_PASS | Connects KPI decisioning and remediation through policy gates. | results/l4_policy_scheduler/policy_scheduler_summary.json |
| Step 101 | Hash-chained audit ledger | 14 entries | Creates tamper-evident artifact provenance. | results/l4_automation_audit_ledger/automation_audit_ledger.json |
| Step 102 | IPFS/blockchain-ready anchor | IPFS_ADD_PASS | Creates IPFS CID and blockchain-ready anchor commitment. | results/l4_audit_anchor/audit_ledger_anchor_record.json |
| Step 103 | On-chain audit-anchor registry | anchorId=0 | Stores the audit anchor in a local Hardhat smart-contract registry. | results/l4_onchain_anchor/onchain_audit_anchor_result.json |
| Step 104 | Negative-security validation | PASS | Tests replay rejection and invalid zero-commitment rejection. | results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.json |
| Step 105 | Policy-gated on-chain validation | EXECUTED_PASS | Runs Step 103/104 validation through explicit approval gates. | results/l4_policy_onchain_validation/policy_onchain_validation_summary.json |

## Table 6.2: Audit and On-Chain Evidence Values

| Evidence | Value | Source |
|---|---|---|
| Automation status | PASS | Step 96 |
| KPI decision | GENERATE_SUPERVISOR_REPORT | Step 97 |
| Scheduler status | EXECUTED_PASS | Step 100 |
| Audit ledger entries | 14 | Step 101 |
| Final ledger hash | 0db58b3f2c09e530c280dc6cd795a53df54e3337b4a46aa9c70fe6ea166c2567 | Step 101 |
| IPFS status | IPFS_ADD_PASS | Step 102 |
| IPFS CID | QmW7VeYs3fP5kk92JstT8tAEkQytgseH4SfhKRpcSwU112 | Step 102 |
| Anchor commitment hash | 50aa798c5968470f172f5e91cb9d80e25b6ac018d3acde55a424f32ec1c2c8ec | Step 102 |
| On-chain transaction hash | 0x3aa06732baa252f303eb24a6b20c118a6a3c665b7e8cbcb6dce0a2b9d3053277 | Step 103 |
| On-chain gas used | 320095 | Step 103 |
| Commitment match check | True | Step 103 |
| Duplicate replay rejected | True | Step 104 |
| Zero commitment rejected | True | Step 104 |
| Policy-gated on-chain validation | EXECUTED_PASS | Step 105 |

## Table 6.3: Journal Contribution Mapping

| Contribution | Claim | Evidence Steps | Journal Meaning |
|---|---|---|---|
| C1 | Policy-gated agentic experiment automation | Steps 96-100 | Shows repeatable automation with human/supervisor governance boundaries. |
| C2 | Closed-loop KPI decision and remediation | Steps 97-98 | Converts KPI evidence into safe next-action recommendations and approved execution. |
| C3 | Tamper-evident automation provenance | Step 101 | Hash-chained audit ledger links experiment, decision, remediation, governance, and reports. |
| C4 | IPFS/blockchain-ready audit anchoring | Step 102 | Binds the audit ledger to content addressing and a commitment hash. |
| C5 | Smart-contract audit-anchor validation | Steps 103-104 | Stores anchor commitments and validates replay/invalid-commitment rejection. |
| C6 | Policy-gated blockchain validation | Step 105 | Brings on-chain validation into the controlled automation workflow. |

## Table 6.4: Governance Boundary

| Boundary Class | Actions |
|---|---|
| Allowed automatically | Read artifacts; validate JSON/CSV; generate reports; create manifests; recommend next action. |
| Allowed with human approval | Execute remediation; regenerate reports; rerun non-privileged experiments. |
| Allowed with human and privileged approval | Rerun tc/netem and namespace experiments requiring sudo. |
| Never automatic | Git push; modify Git history; submit papers; email supervisor; deploy public-chain contracts; delete evidence; spend funds. |

## Key Result Summary

- Step 96 automation status: `PASS`
- Step 100 scheduler status: `EXECUTED_PASS`
- Step 101 final ledger hash: `0db58b3f2c09e530c280dc6cd795a53df54e3337b4a46aa9c70fe6ea166c2567`
- Step 102 IPFS CID: `QmW7VeYs3fP5kk92JstT8tAEkQytgseH4SfhKRpcSwU112`
- Step 102 commitment hash: `50aa798c5968470f172f5e91cb9d80e25b6ac018d3acde55a424f32ec1c2c8ec`
- Step 103 transaction hash: `0x3aa06732baa252f303eb24a6b20c118a6a3c665b7e8cbcb6dce0a2b9d3053277`
- Step 103 gas used: `320095`
- Step 104 negative-security status: `PASS`
- Step 105 policy-gated validation status: `EXECUTED_PASS`

## Paper-Ready Interpretation

The implemented system demonstrates a controlled Level 4 agentic automation workflow. It does not only execute experiments; it validates KPIs, recommends actions, executes approved remediation, preserves tamper-evident audit evidence, anchors evidence through IPFS and blockchain-ready commitments, and validates the commitment through a local smart-contract registry with negative-security testing.

## Generated Files

- Summary JSON: `results/l4_journal_ready/journal_ready_architecture_tables_summary.json`
- Markdown: `docs/paper/l4_journal_ready_architecture_tables_steps96_105.md`
- PDF: `results/l4_report_pdf/zktrustllm_l4_journal_ready_architecture_tables_steps96_105.pdf`
- Workflow CSV: `results/l4_journal_ready/tables/table_6_1_l4_workflow_components.csv`
- Evidence CSV: `results/l4_journal_ready/tables/table_6_2_l4_audit_evidence_values.csv`
- Contribution CSV: `results/l4_journal_ready/tables/table_6_3_l4_journal_contribution_mapping.csv`
- Governance CSV: `results/l4_journal_ready/tables/table_6_4_l4_governance_boundary.csv`

## 5. Results Narrative

# Results Narrative: L4 Automation, Audit, IPFS, and On-Chain Validation

The Level 4 automation pipeline progressed from manual experiment execution to a policy-gated closed-loop workflow.

Step 96 demonstrated that the agentic automation suite can execute and validate the main L4 experiment chain. The suite completed with PASS status and generated machine-readable evidence for control-plane, agent-scaling, RTP, DTLS-RTP, impairment, namespace, and automation outputs.

Step 97 introduced closed-loop KPI decisioning. The KPI agent analysed the generated evidence and recommended `GENERATE_SUPERVISOR_REPORT`, indicating that the checked control-plane, media-plane, impairment, namespace, and automation artifacts passed the expected validation thresholds.

Step 98 executed the recommended remediation action after explicit human approval. This produced the full technical documentation PDF and demonstrated controlled remediation rather than uncontrolled autonomous execution.

Step 99 and Step 100 formalised the governance boundary. The automation governance dashboard and policy-gated scheduler define which actions can be automatic, which require human approval, and which must never be automatic.

Step 101 created a hash-chained automation audit ledger containing 14 evidence entries. The final ledger hash was:

`0db58b3f2c09e530c280dc6cd795a53df54e3337b4a46aa9c70fe6ea166c2567`

Step 102 anchored this ledger using IPFS and a blockchain-ready commitment payload. The IPFS CID was:

`QmW7VeYs3fP5kk92JstT8tAEkQytgseH4SfhKRpcSwU112`

The blockchain-ready anchor commitment hash was:

`50aa798c5968470f172f5e91cb9d80e25b6ac018d3acde55a424f32ec1c2c8ec`

Step 103 submitted this anchor to a local Hardhat smart-contract registry. The registry stored the audit evidence and validated that the stored values matched the submitted ledger hash, ledger SHA-256, IPFS CID, and anchor commitment.

Step 104 added negative-security validation. The registry rejected duplicate commitment replay and rejected zero-commitment submission. This confirms that the trust-plane registry includes basic replay protection and invalid-anchor rejection.

Step 105 integrated on-chain validation into the policy-gated automation workflow, requiring explicit human approval before local Hardhat validation.

Step 109 extended the blockchain validation to a persistent local Hardhat JSON-RPC process. The persistent validation passed, with chain ID `31337`, transaction hash:

`0x0cfb7dde504ad4ce100b6ba219458135fb0dfc2f616d0d4722afc0c9af768ab6`

and gas usage:

`320095`

Overall, the results show that the L4 system is now more than a collection of scripts. It is an integrated, policy-gated, auditable, and blockchain-verifiable agentic automation pipeline.

## 6. Discussion

The implemented system demonstrates that agentic automation can be made auditable and policy-governed. The key design decision is to separate automatic evidence processing from sensitive actions. Reading artifacts, validating KPIs, generating reports, and constructing manifests are treated as safe automation actions. Execution, privileged networking, blockchain validation, and public deployment remain approval-gated.

This structure is important for PhD-level research because it enables automation without sacrificing scientific accountability. The audit ledger, IPFS CID, and smart-contract anchor form a verifiable trail from experiment execution to trust-plane evidence.

## 7. Limitations

The current implementation is intentionally local and research-oriented. Hardhat is used for controlled blockchain validation, and IPFS is evaluated in a local environment. The system does not deploy to a public blockchain, spend real funds, submit papers automatically, email supervisors, modify Git history, or delete evidence. These restrictions are deliberate governance controls. Future work should extend the evaluation to controlled testnets, longer-duration persistent nodes, two-machine media-plane validation, and repeated statistical runs across larger agent populations.

## 8. Future Work

Future work will focus on four directions. First, the automation pipeline should be evaluated over longer repeated runs with confidence intervals for agent and network KPIs. Second, the persistent blockchain validation should be extended to controlled testnet dry-runs with explicit human approval. Third, the media-plane experiments should move from local namespace and loopback experiments to two-machine, Mininet, ns-3, or university testbed deployments. Fourth, the audit-anchor registry can be extended with stronger semantic validation, role-based submitter controls, and integration with production-grade ZK proof verification.

## 9. Conclusion

ZKTrustLLM-Agents L4 demonstrates a complete local prototype for policy-gated agentic automation with audit provenance and blockchain-verifiable trust anchoring. The system progresses from experiment execution to KPI decisioning, remediation, governance, hash-chained evidence, IPFS anchoring, smart-contract validation, negative-security testing, and persistent local blockchain evaluation. This provides a strong foundation for journal-level research on safe, auditable, and trust-aware agentic AI automation in secure 5G/O-RAN environments.
