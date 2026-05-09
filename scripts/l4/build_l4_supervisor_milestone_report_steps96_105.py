#!/usr/bin/env python3

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "results" / "l4_milestone_report"
PDF_DIR = ROOT / "results" / "l4_report_pdf"
DOC_DIR = ROOT / "docs" / "report"

OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_JSON = OUT_DIR / "supervisor_milestone_report_steps96_105_summary.json"
REPORT_MD = DOC_DIR / "zktrustllm_l4_supervisor_milestone_report_steps96_105.md"
REPORT_PDF = PDF_DIR / "zktrustllm_l4_supervisor_milestone_report_steps96_105.pdf"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def load_json(path: str):
    p = ROOT / path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def esc(value) -> str:
    return html.escape(str(value))


def nested(data, keys, default=None):
    cur = data
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def short_hash(value, n=12):
    if not value:
        return "N/A"
    return str(value)[:n]


def status_from_json(data, *paths):
    if data is None:
        return "MISSING"
    for path in paths:
        value = nested(data, path, None)
        if value is not None:
            return str(value)
    return "JSON_PRESENT"


def para(text, style):
    return Paragraph(esc(text), style)

def collect_state():
    step96 = load_json("results/l4_agentic_automation/agentic_automation_summary.json")
    step97 = load_json("results/l4_closed_loop_agent/closed_loop_kpi_decision.json")
    step98 = load_json("results/l4_remediation_executor/remediation_execution_plan.json")
    step99 = load_json("results/l4_automation_governance/automation_governance_dashboard.json")
    step100 = load_json("results/l4_policy_scheduler/policy_scheduler_summary.json")
    step101 = load_json("results/l4_automation_audit_ledger/automation_audit_ledger.json")
    step102_anchor = load_json("results/l4_audit_anchor/audit_ledger_anchor_record.json")
    step102_payload = load_json("results/l4_audit_anchor/audit_ledger_blockchain_ready_anchor.json")
    step103 = load_json("results/l4_onchain_anchor/onchain_audit_anchor_result.json")
    step104 = load_json("results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.json")
    step105 = load_json("results/l4_policy_onchain_validation/policy_onchain_validation_summary.json")

    decision = nested(step97 or {}, ["decision"], {}) if isinstance(nested(step97 or {}, ["decision"], {}), dict) else {}

    steps = [
        {
            "step": "96",
            "component": "Agentic automation suite",
            "status": status_from_json(step96, ["overallStatus"]),
            "evidence": "Runs MCP/A2A control tests, scaling, RTP, DTLS-RTP, loopback impairment, and namespace impairment.",
            "artifact": "results/l4_agentic_automation/agentic_automation_summary.json",
        },
        {
            "step": "97",
            "component": "Closed-loop KPI decision agent",
            "status": decision.get("primaryAction") or status_from_json(step97, ["primaryAction"]),
            "evidence": "Reads KPI evidence and recommends the next safe workflow action.",
            "artifact": "results/l4_closed_loop_agent/closed_loop_kpi_decision.json",
        },
        {
            "step": "98",
            "component": "Closed-loop remediation executor",
            "status": status_from_json(step98, ["status"]),
            "evidence": "Executes approved remediation or supervisor-report generation after human approval.",
            "artifact": "results/l4_remediation_executor/remediation_execution_plan.json",
        },
        {
            "step": "99",
            "component": "Automation governance dashboard",
            "status": status_from_json(step99, ["status"], ["overallStatus"]),
            "evidence": "Summarises the governance boundary for Steps 96-98.",
            "artifact": "results/l4_automation_governance/automation_governance_dashboard.json",
        },
        {
            "step": "100",
            "component": "Policy-gated autonomous scheduler",
            "status": status_from_json(step100, ["overallStatus"]),
            "evidence": "Connects KPI decision and remediation under an explicit automation policy.",
            "artifact": "results/l4_policy_scheduler/policy_scheduler_summary.json",
        },
        {
            "step": "101",
            "component": "Hash-chained automation audit ledger",
            "status": "FINAL_HASH_" + short_hash(nested(step101 or {}, ["finalLedgerHash"])),
            "evidence": "Creates a tamper-evident audit chain over automation artifacts.",
            "artifact": "results/l4_automation_audit_ledger/automation_audit_ledger.json",
        },
        {
            "step": "102",
            "component": "IPFS/blockchain-ready audit anchor",
            "status": status_from_json(step102_anchor, ["ipfs", "status"]),
            "evidence": "Anchors the audit ledger with IPFS CID and blockchain-ready commitment hash.",
            "artifact": "results/l4_audit_anchor/audit_ledger_anchor_record.json",
        },
        {
            "step": "103",
            "component": "On-chain audit-anchor registry",
            "status": "ANCHOR_ID_" + str(nested(step103 or {}, ["anchorId"], "N/A")),
            "evidence": "Stores the automation audit anchor in a local Hardhat smart-contract registry.",
            "artifact": "results/l4_onchain_anchor/onchain_audit_anchor_result.json",
        },
        {
            "step": "104",
            "component": "On-chain negative-security validation",
            "status": status_from_json(step104, ["overallStatus"]),
            "evidence": "Validates replay rejection and invalid zero-commitment rejection.",
            "artifact": "results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.json",
        },
        {
            "step": "105",
            "component": "Policy-gated on-chain validation",
            "status": status_from_json(step105, ["overallStatus"]),
            "evidence": "Runs Step 103 and Step 104 through a human-approved policy gate.",
            "artifact": "results/l4_policy_onchain_validation/policy_onchain_validation_summary.json",
        },
    ]

    state = {
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "title": "ZKTrustLLM-Agents L4 Supervisor Milestone Report: Automation, Audit, IPFS, and On-Chain Validation",
        "steps": steps,
        "keyMetrics": {
            "step96OverallStatus": status_from_json(step96, ["overallStatus"]),
            "step97PrimaryAction": decision.get("primaryAction") or "N/A",
            "step98Status": status_from_json(step98, ["status"]),
            "step100SchedulerStatus": status_from_json(step100, ["overallStatus"]),
            "step101EntryCount": nested(step101 or {}, ["entryCount"], "N/A"),
            "step101FinalLedgerHash": nested(step101 or {}, ["finalLedgerHash"], "N/A"),
            "step102IpfsStatus": nested(step102_anchor or {}, ["ipfs", "status"], "N/A"),
            "step102IpfsCid": nested(step102_anchor or {}, ["ipfs", "cid"], "N/A"),
            "step102CommitmentHash": nested(step102_payload or {}, ["anchorCommitmentHash"], "N/A"),
            "step103GasUsed": nested(step103 or {}, ["gasUsed"], "N/A"),
            "step103TxHash": nested(step103 or {}, ["transactionHash"], "N/A"),
            "step104OverallStatus": status_from_json(step104, ["overallStatus"]),
            "step105OverallStatus": status_from_json(step105, ["overallStatus"]),
        },
    }

    return state

def build_markdown(state):
    km = state["keyMetrics"]
    lines = [
        "# " + state["title"],
        "",
        "## Purpose",
        "",
        "This milestone report explains the current Level 4 ZKTrustLLM-Agents automation chain from Step 96 to Step 105.",
        "",
        "It is designed for supervisor review and future journal writing. The report connects agentic automation, KPI-based decision making, policy-gated execution, audit-ledger construction, IPFS anchoring, and local on-chain validation.",
        "",
        "## High-Level Architecture",
        "",
        "The implemented workflow follows a layered pipeline:",
        "",
        "1. Experiment automation: Step 96 executes and validates Level 4 control-plane and media-plane experiments.",
        "2. KPI decisioning: Step 97 reads KPI artifacts and recommends the next safe action.",
        "3. Remediation execution: Step 98 executes approved remediation/report generation only after human approval.",
        "4. Governance: Step 99 and Step 100 formalise automation boundaries, policy gates, and rollback notes.",
        "5. Auditability: Step 101 builds a hash-chained audit ledger over the automation artifacts.",
        "6. Evidence anchoring: Step 102 creates IPFS and blockchain-ready commitments.",
        "7. Trust-plane validation: Step 103 and Step 104 validate smart-contract anchor storage and negative-security behaviour.",
        "8. Policy-gated blockchain validation: Step 105 integrates the on-chain validation process into the approval-gated automation workflow.",
        "",
        "## Milestone Summary",
        "",
        "| Step | Component | Status / Decision | Evidence |",
        "|---|---|---|---|",
    ]

    for item in state["steps"]:
        lines.append(
            f"| Step {item['step']} | {item['component']} | {item['status']} | `{item['artifact']}` |"
        )

    lines += [
        "",
        "## Key Evidence Values",
        "",
        f"- Step 96 automation status: `{km['step96OverallStatus']}`",
        f"- Step 97 recommended action: `{km['step97PrimaryAction']}`",
        f"- Step 98 remediation status: `{km['step98Status']}`",
        f"- Step 100 scheduler status: `{km['step100SchedulerStatus']}`",
        f"- Step 101 audit ledger entries: `{km['step101EntryCount']}`",
        f"- Step 101 final ledger hash: `{km['step101FinalLedgerHash']}`",
        f"- Step 102 IPFS status: `{km['step102IpfsStatus']}`",
        f"- Step 102 IPFS CID: `{km['step102IpfsCid']}`",
        f"- Step 102 blockchain-ready commitment hash: `{km['step102CommitmentHash']}`",
        f"- Step 103 transaction hash: `{km['step103TxHash']}`",
        f"- Step 103 gas used: `{km['step103GasUsed']}`",
        f"- Step 104 negative-security status: `{km['step104OverallStatus']}`",
        f"- Step 105 policy-gated validation status: `{km['step105OverallStatus']}`",
        "",
        "## Scientific Meaning",
        "",
        "The project has moved beyond isolated scripts into a closed-loop, evidence-driven automation framework. It can now run experiments, evaluate KPIs, recommend actions, execute approved remediation, preserve audit evidence, anchor evidence through IPFS/blockchain-ready commitments, and validate those commitments through a local smart-contract registry.",
        "",
        "This is a strong PhD milestone because it demonstrates a practical Level 4 agentic-AI automation pipeline with governance, auditability, and trust-plane validation.",
        "",
        "## Governance Boundary",
        "",
        "The automation remains intentionally controlled. It does not automatically push code, modify Git history, submit papers, email supervisors, deploy public-chain contracts, spend real funds, or delete evidence. Sensitive actions remain human-approved and policy-gated.",
        "",
        "## Recommended Next Steps",
        "",
        "1. Step 106: Use this report as the supervisor milestone report.",
        "2. Step 107: Produce a journal-ready architecture figure and table set for Steps 96-105.",
        "3. Step 108: Add repeated-run statistics for Step 96 automation and Step 105 validation.",
        "4. Step 109: Extend the on-chain anchor workflow to a persistent local Hardhat node or controlled testnet dry-run.",
        "5. Step 110: Draft the journal methodology section around policy-gated agentic automation and audit anchoring.",
        "",
        "## Generated Files",
        "",
        f"- Summary JSON: `{rel(SUMMARY_JSON)}`",
        f"- Markdown report: `{rel(REPORT_MD)}`",
        f"- PDF report: `{rel(REPORT_PDF)}`",
    ]

    REPORT_MD.write_text("\n".join(lines) + "\n")


def build_pdf(state):
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=16,
    )

    h1 = ParagraphStyle(
        "Heading1Custom",
        parent=styles["Heading1"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
    )

    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )

    small = ParagraphStyle(
        "SmallCustom",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        spaceAfter=4,
    )

    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=state["title"],
    )

    story = []

    story.append(Paragraph(esc(state["title"]), title_style))
    story.append(para("Created: " + state["createdAt"], small))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Purpose", h1))
    story.append(para(
        "This supervisor milestone report documents the ZKTrustLLM-Agents Level 4 automation chain from Step 96 to Step 105. It connects agentic experiment automation, KPI-driven decision making, policy-gated remediation, governance, hash-chained audit evidence, IPFS anchoring, and local on-chain validation.",
        body,
    ))

    story.append(Paragraph("2. Full Process Architecture", h1))
    arch_rows = [
        ["Layer", "Implemented Steps", "Role"],
        ["Automation", "Step 96", "Runs L4 experiments and validates outputs."],
        ["Decision", "Step 97", "Reads KPI artifacts and recommends next action."],
        ["Remediation", "Step 98", "Executes approved actions after human approval."],
        ["Governance", "Steps 99-100", "Defines policy gates, approval boundaries, and rollback notes."],
        ["Audit", "Step 101", "Creates hash-chained evidence over automation artifacts."],
        ["Anchor", "Step 102", "Creates IPFS and blockchain-ready commitment evidence."],
        ["Trust Plane", "Steps 103-104", "Stores anchor on local Hardhat and validates replay rejection."],
        ["Policy-Gated Chain", "Step 105", "Runs on-chain validation through approval-gated automation."],
    ]
    story.append(make_table(arch_rows, [1.3 * inch, 1.25 * inch, 4.2 * inch]))

    story.append(Paragraph("3. Step-by-Step Progress", h1))
    step_rows = [["Step", "Component", "Status / Decision", "Evidence artifact"]]
    for item in state["steps"]:
        step_rows.append([
            "Step " + item["step"],
            item["component"],
            item["status"],
            item["artifact"],
        ])
    story.append(make_table(step_rows, [0.65 * inch, 1.8 * inch, 1.45 * inch, 2.85 * inch]))

    story.append(PageBreak())
    story.append(Paragraph("4. Key Evidence Values", h1))
    km = state["keyMetrics"]
    evidence_rows = [["Evidence", "Value"]]
    for key, value in km.items():
        evidence_rows.append([key, str(value)])
    story.append(make_table(evidence_rows, [2.3 * inch, 4.45 * inch]))

    story.append(Paragraph("5. Scientific Contribution", h1))
    contributions = [
        "The project now demonstrates a Level 4 agentic automation workflow rather than independent scripts.",
        "The automation chain is KPI-aware, policy-gated, approval-gated, and supervisor-auditable.",
        "The audit ledger gives the automation process a tamper-evident evidence chain.",
        "The IPFS and blockchain-ready anchor connects the automation layer to the ZKTrustLLM evidence/trust-plane design.",
        "The local Hardhat registry and negative-security tests show replay-resistant anchor validation.",
    ]
    for c in contributions:
        story.append(para("- " + c, body))

    story.append(Paragraph("6. Governance Boundary", h1))
    story.append(para(
        "The automation does not automatically push code, modify Git history, submit papers, email supervisors, deploy public-chain contracts, spend real funds, or delete evidence. Sensitive actions remain explicitly human-approved and policy-gated.",
        body,
    ))

    story.append(Paragraph("7. Recommended Next Steps", h1))
    next_rows = [
        ["Next Step", "Purpose"],
        ["Step 107", "Create journal-ready architecture figures and result tables for Steps 96-105."],
        ["Step 108", "Add repeated-run statistics and confidence intervals for automation and on-chain validation."],
        ["Step 109", "Move from ephemeral Hardhat runs to a persistent local node or controlled testnet dry-run."],
        ["Step 110", "Draft journal methodology and evaluation sections around policy-gated agentic automation."],
    ]
    story.append(make_table(next_rows, [1.0 * inch, 5.75 * inch]))

    doc.build(story)


def make_table(rows, widths):
    table = Table([[Paragraph(esc(str(cell)), ParagraphStyle("tbl", fontSize=7.4, leading=9)) for cell in row] for row in rows], colWidths=widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def main():
    state = collect_state()
    SUMMARY_JSON.write_text(json.dumps(state, indent=2) + "\n")
    build_markdown(state)
    build_pdf(state)

    print(json.dumps({
        "experiment": "step106_supervisor_milestone_report_automation_audit_chain",
        "summaryJson": rel(SUMMARY_JSON),
        "markdown": rel(REPORT_MD),
        "pdf": rel(REPORT_PDF),
        "stepCount": len(state["steps"]),
    }, indent=2))


if __name__ == "__main__":
    main()
