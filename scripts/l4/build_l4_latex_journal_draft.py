#!/usr/bin/env python3

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "results/l4_latex_journal_draft"
PDF_DIR = ROOT / "results/l4_report_pdf"
DOC_DIR = ROOT / "docs/paper"

OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

TEX = DOC_DIR / "zktrustllm_agents_l4_journal_draft.tex"
BIB = DOC_DIR / "zktrustllm_agents_l4_references_todo.bib"
NOTE = OUT_DIR / "latex_journal_draft_compile_note.md"
SUMMARY_JSON = OUT_DIR / "latex_journal_draft_summary.json"

FIGURE = "results/l4_journal_ready/figures/figure_6_1_l4_policy_gated_agentic_automation_architecture.pdf"


def load_json(rel_path):
    path = ROOT / rel_path
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def nested(data, keys, default="N/A"):
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def tex_escape(value):
    s = str(value)
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(ch, ch) for ch in s)


def tt(value):
    return r"\texttt{" + tex_escape(value) + "}"


def build_latex():
    step96 = load_json("results/l4_agentic_automation/agentic_automation_summary.json")
    step97 = load_json("results/l4_closed_loop_agent/closed_loop_kpi_decision.json")
    step98 = load_json("results/l4_remediation_executor/remediation_execution_plan.json")
    step100 = load_json("results/l4_policy_scheduler/policy_scheduler_summary.json")
    step101 = load_json("results/l4_automation_audit_ledger/automation_audit_ledger.json")
    step102 = load_json("results/l4_audit_anchor/audit_ledger_anchor_record.json")
    step102_payload = load_json("results/l4_audit_anchor/audit_ledger_blockchain_ready_anchor.json")
    step103 = load_json("results/l4_onchain_anchor/onchain_audit_anchor_result.json")
    step104 = load_json("results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.json")
    step105 = load_json("results/l4_policy_onchain_validation/policy_onchain_validation_summary.json")
    step108 = load_json("results/l4_repeated_run_statistics/repeated_run_statistics_summary.json")
    step109 = load_json("results/l4_persistent_hardhat_anchor/persistent_hardhat_anchor_result.json")

    decision = step97.get("decision", {}) if isinstance(step97.get("decision"), dict) else {}

    values = {
        "step96_status": step96.get("overallStatus", "N/A"),
        "step97_decision": step97.get("primaryAction") or decision.get("primaryAction", "N/A"),
        "step98_status": step98.get("status", "N/A"),
        "step100_status": step100.get("overallStatus", "N/A"),
        "step101_entries": step101.get("entryCount", "N/A"),
        "step101_hash": step101.get("finalLedgerHash", "N/A"),
        "step102_ipfs": nested(step102, ["ipfs", "status"]),
        "step102_cid": nested(step102, ["ipfs", "cid"]),
        "step102_commitment": step102_payload.get("anchorCommitmentHash", "N/A"),
        "step103_tx": step103.get("transactionHash", "N/A"),
        "step103_gas": step103.get("gasUsed", "N/A"),
        "step104_status": step104.get("overallStatus", "N/A"),
        "step105_status": step105.get("overallStatus", "N/A"),
        "step108_status": step108.get("overallStatus", "N/A"),
        "step108_obs": step108.get("mediaObservationCount", "N/A"),
        "step109_status": step109.get("overallStatus", "N/A"),
        "step109_chain": step109.get("chainId", "N/A"),
        "step109_tx": nested(step109, ["validSubmission", "transactionHash"]),
    }

    rows = [
        ("Step 96", "Agentic automation suite", values["step96_status"], "Runs MCP/A2A, RTP, DTLS-RTP, impairment, and namespace validation."),
        ("Step 97", "Closed-loop KPI decision agent", values["step97_decision"], "Converts KPI evidence into next-action recommendations."),
        ("Step 98", "Remediation executor", values["step98_status"], "Executes approved remediation/report generation."),
        ("Step 100", "Policy-gated scheduler", values["step100_status"], "Connects KPI decisioning and remediation through policy gates."),
        ("Step 101", "Hash-chained audit ledger", f"{values['step101_entries']} entries", "Creates tamper-evident automation provenance."),
        ("Step 102", "IPFS/blockchain-ready anchor", values["step102_ipfs"], "Binds audit evidence to IPFS and compact commitments."),
        ("Step 103", "On-chain anchor registry", "ANCHOR_SUBMITTED", "Stores the audit anchor in a local Hardhat registry."),
        ("Step 104", "Negative-security validation", values["step104_status"], "Validates replay and invalid-commitment rejection."),
        ("Step 105", "Policy-gated on-chain validation", values["step105_status"], "Executes local Hardhat validation under explicit approval."),
        ("Step 108", "Repeated-run statistics", values["step108_status"], "Analyses repeated clean media snapshots."),
        ("Step 109", "Persistent local Hardhat validation", values["step109_status"], "Validates audit anchoring on a persistent local JSON-RPC node."),
    ]

    lines = []
    lines.append(r"\documentclass[10pt]{article}")
    lines.append(r"\usepackage[a4paper,margin=0.8in]{geometry}")
    lines.append(r"\usepackage{graphicx}")
    lines.append(r"\usepackage{booktabs}")
    lines.append(r"\usepackage{longtable}")
    lines.append(r"\usepackage{array}")
    lines.append(r"\usepackage{xcolor}")
    lines.append(r"\usepackage{hyperref}")
    lines.append(r"\usepackage{caption}")
    lines.append(r"\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}")
    lines.append(r"\title{ZKTrustLLM-Agents L4: Policy-Gated Agentic Automation, Audit Provenance, and Blockchain-Verifiable Trust Anchoring}")
    lines.append(r"\author{Sudarson Karmaker \\ University of Surrey}")
    lines.append(r"\date{\today}")
    lines.append(r"\begin{document}")
    lines.append(r"\maketitle")

    lines.append(r"\begin{abstract}")
    lines.append(
        "This paper presents ZKTrustLLM-Agents L4, a policy-gated agentic automation and audit framework for secure 5G/O-RAN edge intelligence workflows. "
        "The framework integrates automated experiment execution, KPI-driven decision making, human-approved remediation, hash-chained audit provenance, IPFS-based evidence anchoring, and smart-contract-based trust-plane validation. "
        "The implemented prototype demonstrates repeatable automation, policy-based governance boundaries, replay-resistant audit-anchor registration, repeated-run statistics, and persistent local Hardhat validation. "
        "The results show that policy-gated agentic automation can support reproducible, auditable, and blockchain-verifiable research workflows for future secure 5G/O-RAN and multi-agent AI systems."
    )
    lines.append(r"\end{abstract}")

    lines.append(r"\textbf{Keywords---} ZKTrustLLM, agentic AI, MCP, A2A, Zero Trust, IPFS, blockchain, audit ledger, smart contracts, 5G, O-RAN, DTLS, policy-gated automation.")

    lines.append(r"\section{Introduction}")
    lines.append(
        "Future 5G/O-RAN and 6G systems require intelligent automation, but autonomous decision-making must be governed, auditable, and verifiable. "
        "In security-sensitive edge environments, it is not sufficient for an agentic AI system to execute experiments or make control-plane decisions. "
        "The system must also preserve evidence, expose governance boundaries, support reproducibility, and enable trust-plane verification. "
        "ZKTrustLLM-Agents L4 addresses this requirement by connecting experiment execution, KPI-based decisioning, human-approved remediation, hash-chained evidence, IPFS anchoring, and blockchain-based validation."
    )

    lines.append(r"\section{Contributions}")
    lines.append(r"\begin{enumerate}")
    lines.append(r"\item A policy-gated Level 4 agentic automation pipeline connecting MCP/A2A experiment execution, KPI decisioning, remediation, and reporting.")
    lines.append(r"\item A hash-chained automation audit ledger providing tamper-evident provenance across experiment, decision, remediation, governance, and reporting artifacts.")
    lines.append(r"\item An IPFS and blockchain-ready anchoring workflow binding the audit ledger to content-addressed evidence and compact trust-plane commitments.")
    lines.append(r"\item A local smart-contract audit-anchor registry validating anchor submission, commitment matching, and on-chain evidence retrieval.")
    lines.append(r"\item Negative-security validation showing duplicate replay rejection and invalid zero-commitment rejection.")
    lines.append(r"\item Persistent local Hardhat validation moving beyond one-off ephemeral blockchain execution toward long-running local trust-plane evaluation.")
    lines.append(r"\end{enumerate}")

    lines.append(r"\section{System Architecture}")
    lines.append(
        "The proposed system is organised as a closed-loop automation chain. "
        "The automation suite generates evidence, the KPI decision agent recommends safe next actions, the remediation executor performs approved actions, the scheduler enforces policy gates, and the audit layer preserves and anchors the resulting evidence."
    )

    if (ROOT / FIGURE).exists():
        lines.append(r"\begin{figure*}[t]")
        lines.append(r"\centering")
        lines.append(r"\includegraphics[width=0.95\textwidth]{" + FIGURE + r"}")
        lines.append(r"\caption{Policy-gated Level 4 ZKTrustLLM-Agents automation architecture. The workflow links automated experiment execution, KPI-based decisioning, human-approved remediation, governance, hash-chained audit provenance, IPFS/blockchain-ready anchoring, local on-chain registry validation, and replay/invalid-anchor negative-security testing.}")
        lines.append(r"\label{fig:l4_architecture}")
        lines.append(r"\end{figure*}")

    lines.append(r"\section{Methodology}")
    lines.append(
        "The methodology follows a controlled automation design. "
        "Safe operations, including artifact reading, JSON/CSV validation, manifest generation, and report creation, are allowed automatically. "
        "Remediation execution and blockchain validation require explicit human approval. "
        "Privileged network experiments require both human and privileged approval. "
        "Actions such as Git history modification, public-chain deployment, paper submission, supervisor email, evidence deletion, and fund-spending are never automatic."
    )

    lines.append(r"\section{Implementation Evidence}")
    lines.append(r"\begin{longtable}{p{0.12\linewidth} p{0.25\linewidth} p{0.20\linewidth} p{0.34\linewidth}}")
    lines.append(r"\caption{Implemented L4 workflow components and evidence roles.}\\")
    lines.append(r"\toprule")
    lines.append(r"Step & Component & Status / Decision & Role \\")
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")
    lines.append(r"\toprule")
    lines.append(r"Step & Component & Status / Decision & Role \\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    for step, component, status, role in rows:
        lines.append(f"{tex_escape(step)} & {tex_escape(component)} & {tex_escape(status)} & {tex_escape(role)} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")

    lines.append(r"\section{Key Results}")
    lines.append(r"\begin{longtable}{p{0.36\linewidth} p{0.56\linewidth}}")
    lines.append(r"\caption{Audit, IPFS, and on-chain validation evidence.}\\")
    lines.append(r"\toprule")
    lines.append(r"Evidence & Value \\")
    lines.append(r"\midrule")
    evidence = [
        ("Step 96 automation status", values["step96_status"]),
        ("Step 97 recommended action", values["step97_decision"]),
        ("Step 100 scheduler status", values["step100_status"]),
        ("Step 101 audit ledger entries", values["step101_entries"]),
        ("Step 101 final ledger hash", values["step101_hash"]),
        ("Step 102 IPFS status", values["step102_ipfs"]),
        ("Step 102 IPFS CID", values["step102_cid"]),
        ("Step 102 anchor commitment", values["step102_commitment"]),
        ("Step 103 transaction hash", values["step103_tx"]),
        ("Step 103 gas used", values["step103_gas"]),
        ("Step 104 negative-security status", values["step104_status"]),
        ("Step 108 repeated-run observations", values["step108_obs"]),
        ("Step 109 persistent Hardhat chain ID", values["step109_chain"]),
        ("Step 109 persistent validation tx", values["step109_tx"]),
    ]
    for k, v in evidence:
        lines.append(f"{tex_escape(k)} & {tt(v)} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")

    lines.append(r"\section{Security and Governance Analysis}")
    lines.append(
        "The trust-plane registry enforces non-zero commitments and rejects duplicate audit commitments. "
        "The negative-security tests confirm that replayed audit anchors and zero commitments are rejected, while the valid stored anchor remains unchanged. "
        "Governance is enforced through the automation policy, which separates safe automatic actions from approval-gated actions and never-automatic actions."
    )

    lines.append(r"\section{Limitations}")
    lines.append(
        "The current implementation is local and research-oriented. "
        "Hardhat is used for controlled blockchain validation, and IPFS is evaluated locally. "
        "The system does not deploy to a public blockchain, spend real funds, submit papers automatically, email supervisors, modify Git history, or delete evidence. "
        "These restrictions are deliberate governance controls."
    )

    lines.append(r"\section{Future Work}")
    lines.append(
        "Future work will extend the pipeline through longer repeated runs, confidence intervals for agent and network KPIs, controlled testnet dry-runs, two-machine media-plane validation, and stronger smart-contract access control. "
        "The audit-anchor registry can also be extended with semantic verification and integration with production-grade ZK proof verification."
    )

    lines.append(r"\section{Conclusion}")
    lines.append(
        "ZKTrustLLM-Agents L4 demonstrates a complete local prototype for policy-gated agentic automation with audit provenance and blockchain-verifiable trust anchoring. "
        "The system progresses from experiment execution to KPI decisioning, remediation, governance, hash-chained evidence, IPFS anchoring, smart-contract validation, negative-security testing, repeated-run statistics, and persistent local blockchain evaluation."
    )

    lines.append(r"\section*{References To Add}")
    lines.append(r"\begin{itemize}")
    lines.append(r"\item Official IPFS/content-addressing reference.")
    lines.append(r"\item Ethereum / Solidity smart-contract reference.")
    lines.append(r"\item Hardhat local blockchain development reference.")
    lines.append(r"\item 5G/O-RAN security and Zero Trust references.")
    lines.append(r"\item MCP/A2A agent communication references.")
    lines.append(r"\item DTLS/RTP secure media transport references.")
    lines.append(r"\end{itemize}")
    lines.append(r"\end{document}")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile", action="store_true", help="Try to compile the generated LaTeX using pdflatex.")
    args = parser.parse_args()

    latex = build_latex()
    TEX.write_text(latex)

    BIB.write_text(
        "% TODO: Replace these placeholders with authoritative BibTeX entries before submission.\n"
        "% Add references for IPFS, Ethereum/Solidity, Hardhat, O-RAN, Zero Trust, DTLS/RTP, MCP, and A2A.\n"
    )

    compiled_pdf = None
    compile_status = "NOT_REQUESTED"

    if args.compile:
        if shutil.which("pdflatex") is None:
            compile_status = "PDFLATEX_NOT_FOUND"
        else:
            cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory",
                str(PDF_DIR),
                str(TEX),
            ]
            proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (OUT_DIR / "pdflatex_stdout.log").write_text(proc.stdout)
            (OUT_DIR / "pdflatex_stderr.log").write_text(proc.stderr)
            compile_status = "PASS" if proc.returncode == 0 else "FAIL"
            candidate = PDF_DIR / "zktrustllm_agents_l4_journal_draft.pdf"
            if candidate.exists():
                compiled_pdf = str(candidate.relative_to(ROOT))

    NOTE.write_text(
        "# Step 112 LaTeX Journal Draft Compile Note\n\n"
        f"- LaTeX draft: `{TEX.relative_to(ROOT)}`\n"
        f"- BibTeX placeholder file: `{BIB.relative_to(ROOT)}`\n"
        f"- Compile status: `{compile_status}`\n"
        f"- Compiled PDF: `{compiled_pdf}`\n\n"
        "Manual compile command:\n\n"
        "```bash\n"
        "pdflatex -interaction=nonstopmode -output-directory results/l4_report_pdf docs/paper/zktrustllm_agents_l4_journal_draft.tex\n"
        "```\n"
    )

    summary = {
        "experiment": "step112_latex_journal_draft",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "latexDraft": str(TEX.relative_to(ROOT)),
        "bibPlaceholder": str(BIB.relative_to(ROOT)),
        "compileNote": str(NOTE.relative_to(ROOT)),
        "compileStatus": compile_status,
        "compiledPdf": compiled_pdf,
        "status": "PASS" if compile_status in {"NOT_REQUESTED", "PASS"} else "REVIEW_REQUIRED",
        "researchMeaning": "Converts the L4 journal manuscript skeleton into a LaTeX journal draft suitable for later IEEE/Elsevier formatting."
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
