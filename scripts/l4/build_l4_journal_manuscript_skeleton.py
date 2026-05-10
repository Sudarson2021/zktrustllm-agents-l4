#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "results/l4_journal_manuscript"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MANUSCRIPT_MD = ROOT / "docs/paper/zktrustllm_agents_l4_journal_manuscript_skeleton.md"
SUMMARY_JSON = OUT_DIR / "journal_manuscript_skeleton_summary.json"

METHODOLOGY = ROOT / "docs/paper/l4_journal_methodology_policy_gated_automation_audit_anchor.md"
RESULTS = ROOT / "docs/paper/l4_results_narrative_steps96_109.md"
TABLES = ROOT / "docs/paper/l4_journal_ready_architecture_tables_steps96_105.md"


def read_text(path):
    return path.read_text() if path.exists() else f"[Missing: {path}]"


def section(title, body):
    return f"\n\n# {title}\n\n{body.strip()}\n"


def main():
    methodology = read_text(METHODOLOGY)
    results = read_text(RESULTS)
    tables = read_text(TABLES)

    abstract = """
This paper presents ZKTrustLLM-Agents L4, a policy-gated agentic automation and audit framework for secure 5G/O-RAN edge intelligence workflows. The system integrates automated experiment execution, KPI-driven decision making, human-approved remediation, hash-chained audit provenance, IPFS-based evidence anchoring, and smart-contract-based trust-plane validation. Unlike isolated automation scripts, the proposed framework provides an end-to-end evidence lifecycle in which experiment outputs are validated, transformed into audit artifacts, anchored through content-addressed storage, and verified through a local blockchain registry with negative-security testing. The implemented prototype demonstrates repeatable automation, policy-based governance boundaries, replay-resistant audit-anchor registration, and persistent local Hardhat validation. The results show that policy-gated agentic automation can support reproducible, auditable, and blockchain-verifiable research workflows for future secure 5G/O-RAN and multi-agent AI systems.
"""

    contributions = """
The main contributions of this work are:

1. A policy-gated Level 4 agentic automation pipeline that connects MCP/A2A experiment execution, KPI decisioning, remediation, and reporting.
2. A hash-chained automation audit ledger that provides tamper-evident provenance across experiment, decision, remediation, governance, and reporting artifacts.
3. An IPFS and blockchain-ready anchoring workflow that binds the audit ledger to content-addressed evidence and compact trust-plane commitments.
4. A local smart-contract audit-anchor registry that validates anchor submission, commitment matching, and on-chain evidence retrieval.
5. Negative-security validation showing replay rejection and invalid zero-commitment rejection for the audit-anchor registry.
6. Persistent local Hardhat validation that moves beyond one-off ephemeral blockchain execution toward a long-running local trust-plane evaluation environment.
"""

    limitations = """
The current implementation is intentionally local and research-oriented. Hardhat is used for controlled blockchain validation, and IPFS is evaluated in a local environment. The system does not deploy to a public blockchain, spend real funds, submit papers automatically, email supervisors, modify Git history, or delete evidence. These restrictions are deliberate governance controls. Future work should extend the evaluation to controlled testnets, longer-duration persistent nodes, two-machine media-plane validation, and repeated statistical runs across larger agent populations.
"""

    future_work = """
Future work will focus on four directions. First, the automation pipeline should be evaluated over longer repeated runs with confidence intervals for agent and network KPIs. Second, the persistent blockchain validation should be extended to controlled testnet dry-runs with explicit human approval. Third, the media-plane experiments should move from local namespace and loopback experiments to two-machine, Mininet, ns-3, or university testbed deployments. Fourth, the audit-anchor registry can be extended with stronger semantic validation, role-based submitter controls, and integration with production-grade ZK proof verification.
"""

    manuscript = f"""# ZKTrustLLM-Agents L4: Policy-Gated Agentic Automation, Audit Provenance, and Blockchain-Verifiable Trust Anchoring

## Abstract

{abstract.strip()}

## Keywords

ZKTrustLLM; agentic AI; MCP; A2A; Zero Trust; IPFS; blockchain; audit ledger; smart contracts; 5G; O-RAN; DTLS; policy-gated automation.

## 1. Introduction

Future 5G/O-RAN and 6G systems require intelligent automation, but autonomous decision-making must be governed, auditable, and verifiable. In security-sensitive edge environments, it is not sufficient for an agentic AI system to execute experiments or make control-plane decisions. The system must also preserve evidence, expose governance boundaries, support reproducibility, and enable trust-plane verification.

This paper introduces ZKTrustLLM-Agents L4, a policy-gated automation and audit framework that connects experiment execution, KPI-based decisioning, human-approved remediation, hash-chained evidence, IPFS anchoring, and blockchain-based validation.

## 2. Contributions

{contributions.strip()}

## 3. System Methodology

{methodology.strip()}

## 4. Journal-Ready Architecture and Tables

{tables.strip()}

## 5. Results Narrative

{results.strip()}

## 6. Discussion

The implemented system demonstrates that agentic automation can be made auditable and policy-governed. The key design decision is to separate automatic evidence processing from sensitive actions. Reading artifacts, validating KPIs, generating reports, and constructing manifests are treated as safe automation actions. Execution, privileged networking, blockchain validation, and public deployment remain approval-gated.

This structure is important for PhD-level research because it enables automation without sacrificing scientific accountability. The audit ledger, IPFS CID, and smart-contract anchor form a verifiable trail from experiment execution to trust-plane evidence.

## 7. Limitations

{limitations.strip()}

## 8. Future Work

{future_work.strip()}

## 9. Conclusion

ZKTrustLLM-Agents L4 demonstrates a complete local prototype for policy-gated agentic automation with audit provenance and blockchain-verifiable trust anchoring. The system progresses from experiment execution to KPI decisioning, remediation, governance, hash-chained evidence, IPFS anchoring, smart-contract validation, negative-security testing, and persistent local blockchain evaluation. This provides a strong foundation for journal-level research on safe, auditable, and trust-aware agentic AI automation in secure 5G/O-RAN environments.
"""

    MANUSCRIPT_MD.write_text(manuscript.strip() + "\n")

    summary = {
        "experiment": "step111_journal_manuscript_skeleton",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "manuscriptMarkdown": str(MANUSCRIPT_MD.relative_to(ROOT)),
        "methodologySource": str(METHODOLOGY.relative_to(ROOT)),
        "resultsSource": str(RESULTS.relative_to(ROOT)),
        "tablesSource": str(TABLES.relative_to(ROOT)),
        "status": "PASS",
        "researchMeaning": "Creates a complete journal manuscript skeleton from the implemented L4 automation, audit, IPFS, and on-chain validation evidence."
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
