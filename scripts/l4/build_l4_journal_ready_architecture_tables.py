#!/usr/bin/env python3

import csv
import html
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

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
    Image,
)

ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "results/l4_journal_ready"
FIG_DIR = OUT_DIR / "figures"
TABLE_DIR = OUT_DIR / "tables"
PDF_DIR = ROOT / "results/l4_report_pdf"
DOC_DIR = ROOT / "docs/paper"

for d in [OUT_DIR, FIG_DIR, TABLE_DIR, PDF_DIR, DOC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SUMMARY_JSON = OUT_DIR / "journal_ready_architecture_tables_summary.json"
DOC_MD = DOC_DIR / "l4_journal_ready_architecture_tables_steps96_105.md"
PDF_OUT = PDF_DIR / "zktrustllm_l4_journal_ready_architecture_tables_steps96_105.pdf"

FIG_PNG = FIG_DIR / "figure_6_1_l4_policy_gated_agentic_automation_architecture.png"
FIG_PDF = FIG_DIR / "figure_6_1_l4_policy_gated_agentic_automation_architecture.pdf"
FIG_SVG = FIG_DIR / "figure_6_1_l4_policy_gated_agentic_automation_architecture.svg"

WORKFLOW_CSV = TABLE_DIR / "table_6_1_l4_workflow_components.csv"
EVIDENCE_CSV = TABLE_DIR / "table_6_2_l4_audit_evidence_values.csv"
CONTRIBUTION_CSV = TABLE_DIR / "table_6_3_l4_journal_contribution_mapping.csv"
GOVERNANCE_CSV = TABLE_DIR / "table_6_4_l4_governance_boundary.csv"


def rel(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except Exception:
        return str(path)


def load_json(path):
    path = ROOT / path
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def nested(data, keys, default=None):
    cur = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def first_value(*values, default="N/A"):
    for v in values:
        if v is not None and v != "":
            return v
    return default


def short(value, n=14):
    if value is None:
        return "N/A"
    value = str(value)
    if len(value) <= n:
        return value
    return value[:n]


def status_from(data, keys, default="N/A"):
    return nested(data, keys, default)


def esc(text):
    return html.escape(str(text)).replace("\n", "<br/>")

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

    step97_decision = step97.get("decision", {}) if isinstance(step97.get("decision"), dict) else {}

    km = {
        "step96Status": status_from(step96, ["overallStatus"]),
        "step97Action": first_value(step97.get("primaryAction"), step97_decision.get("primaryAction")),
        "step98Status": status_from(step98, ["status"]),
        "step100Status": status_from(step100, ["overallStatus"]),
        "step101EntryCount": status_from(step101, ["entryCount"]),
        "step101FinalHash": status_from(step101, ["finalLedgerHash"]),
        "step102IpfsStatus": status_from(step102_anchor, ["ipfs", "status"]),
        "step102IpfsCid": status_from(step102_anchor, ["ipfs", "cid"]),
        "step102Commitment": first_value(
            status_from(step102_payload, ["anchorCommitmentHash"], None),
            status_from(step102_anchor, ["blockchainReadyAnchor", "anchorCommitmentHash"], None),
        ),
        "step103TxHash": status_from(step103, ["transactionHash"]),
        "step103GasUsed": status_from(step103, ["gasUsed"]),
        "step103AnchorId": status_from(step103, ["anchorId"]),
        "step103CommitmentMatches": status_from(step103, ["validation", "commitmentMatches"]),
        "step104Status": status_from(step104, ["overallStatus"]),
        "step104ReplayRejected": status_from(step104, ["validations", "duplicateReplayRejected"]),
        "step104ZeroRejected": status_from(step104, ["validations", "zeroCommitmentRejected"]),
        "step105Status": status_from(step105, ["overallStatus"]),
    }

    workflow_rows = [
        ["Step 96", "Agentic automation suite", km["step96Status"], "Runs MCP/A2A, media-plane, DTLS, impairment, and namespace experiments.", "results/l4_agentic_automation/agentic_automation_summary.json"],
        ["Step 97", "Closed-loop KPI decision agent", km["step97Action"], "Reads KPI artifacts and recommends the next safe action.", "results/l4_closed_loop_agent/closed_loop_kpi_decision.json"],
        ["Step 98", "Closed-loop remediation executor", km["step98Status"], "Executes approved remediation/report generation with human approval.", "results/l4_remediation_executor/remediation_execution_plan.json"],
        ["Step 99", "Automation governance dashboard", "JSON_PRESENT", "Summarises governance boundaries for supervisor review.", "results/l4_automation_governance/automation_governance_dashboard.json"],
        ["Step 100", "Policy-gated autonomous scheduler", km["step100Status"], "Connects KPI decisioning and remediation through policy gates.", "results/l4_policy_scheduler/policy_scheduler_summary.json"],
        ["Step 101", "Hash-chained audit ledger", f"{km['step101EntryCount']} entries", "Creates tamper-evident artifact provenance.", "results/l4_automation_audit_ledger/automation_audit_ledger.json"],
        ["Step 102", "IPFS/blockchain-ready anchor", km["step102IpfsStatus"], "Creates IPFS CID and blockchain-ready anchor commitment.", "results/l4_audit_anchor/audit_ledger_anchor_record.json"],
        ["Step 103", "On-chain audit-anchor registry", f"anchorId={km['step103AnchorId']}", "Stores the audit anchor in a local Hardhat smart-contract registry.", "results/l4_onchain_anchor/onchain_audit_anchor_result.json"],
        ["Step 104", "Negative-security validation", km["step104Status"], "Tests replay rejection and invalid zero-commitment rejection.", "results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.json"],
        ["Step 105", "Policy-gated on-chain validation", km["step105Status"], "Runs Step 103/104 validation through explicit approval gates.", "results/l4_policy_onchain_validation/policy_onchain_validation_summary.json"],
    ]

    evidence_rows = [
        ["Automation status", km["step96Status"], "Step 96"],
        ["KPI decision", km["step97Action"], "Step 97"],
        ["Scheduler status", km["step100Status"], "Step 100"],
        ["Audit ledger entries", km["step101EntryCount"], "Step 101"],
        ["Final ledger hash", km["step101FinalHash"], "Step 101"],
        ["IPFS status", km["step102IpfsStatus"], "Step 102"],
        ["IPFS CID", km["step102IpfsCid"], "Step 102"],
        ["Anchor commitment hash", km["step102Commitment"], "Step 102"],
        ["On-chain transaction hash", km["step103TxHash"], "Step 103"],
        ["On-chain gas used", km["step103GasUsed"], "Step 103"],
        ["Commitment match check", km["step103CommitmentMatches"], "Step 103"],
        ["Duplicate replay rejected", km["step104ReplayRejected"], "Step 104"],
        ["Zero commitment rejected", km["step104ZeroRejected"], "Step 104"],
        ["Policy-gated on-chain validation", km["step105Status"], "Step 105"],
    ]

    contribution_rows = [
        ["C1", "Policy-gated agentic experiment automation", "Steps 96-100", "Shows repeatable automation with human/supervisor governance boundaries."],
        ["C2", "Closed-loop KPI decision and remediation", "Steps 97-98", "Converts KPI evidence into safe next-action recommendations and approved execution."],
        ["C3", "Tamper-evident automation provenance", "Step 101", "Hash-chained audit ledger links experiment, decision, remediation, governance, and reports."],
        ["C4", "IPFS/blockchain-ready audit anchoring", "Step 102", "Binds the audit ledger to content addressing and a commitment hash."],
        ["C5", "Smart-contract audit-anchor validation", "Steps 103-104", "Stores anchor commitments and validates replay/invalid-commitment rejection."],
        ["C6", "Policy-gated blockchain validation", "Step 105", "Brings on-chain validation into the controlled automation workflow."],
    ]

    governance_rows = [
        ["Allowed automatically", "Read artifacts; validate JSON/CSV; generate reports; create manifests; recommend next action."],
        ["Allowed with human approval", "Execute remediation; regenerate reports; rerun non-privileged experiments."],
        ["Allowed with human and privileged approval", "Rerun tc/netem and namespace experiments requiring sudo."],
        ["Never automatic", "Git push; modify Git history; submit papers; email supervisor; deploy public-chain contracts; delete evidence; spend funds."],
    ]

    return {
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "keyMetrics": km,
        "workflowRows": workflow_rows,
        "evidenceRows": evidence_rows,
        "contributionRows": contribution_rows,
        "governanceRows": governance_rows,
    }


def write_csv(path, header, rows):
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

def add_box(ax, x, y, w, h, title, body):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.03,rounding_size=0.03",
        linewidth=1.2,
        facecolor="#f7f7f7",
        edgecolor="#222222",
    )
    ax.add_patch(box)
    ax.text(x + w/2, y + h - 0.08, title, ha="center", va="top", fontsize=10, fontweight="bold")
    wrapped = "\n".join(textwrap.wrap(body, width=32))
    ax.text(x + w/2, y + h/2 - 0.05, wrapped, ha="center", va="center", fontsize=8)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", linewidth=1.2),
    )


def build_figure(state):
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")

    ax.text(
        7,
        7.65,
        "ZKTrustLLM-Agents L4 Policy-Gated Agentic Automation, Audit, IPFS, and On-Chain Validation Architecture",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
    )

    boxes = {
        "b1": (0.6, 5.8, 2.2, 0.9, "Step 96\nAutomation Suite", "Runs MCP/A2A, RTP, DTLS, impairment and namespace experiments"),
        "b2": (3.2, 5.8, 2.2, 0.9, "Step 97\nKPI Decision Agent", "Validates KPIs and recommends the next safe action"),
        "b3": (5.8, 5.8, 2.2, 0.9, "Step 100\nPolicy Scheduler", "Checks action against explicit automation policy"),
        "b4": (8.4, 5.8, 2.2, 0.9, "Step 98\nRemediation Executor", "Executes only approved safe remediation/report generation"),
        "b5": (11.0, 5.8, 2.2, 0.9, "Step 99\nGovernance Dashboard", "Supervisor-readable automation boundary and governance view"),
        "b6": (2.0, 3.7, 2.4, 0.9, "Step 101\nAudit Ledger", "Hash-chained provenance over automation artifacts"),
        "b7": (5.3, 3.7, 2.4, 0.9, "Step 102\nIPFS + Commitment", "CID plus blockchain-ready anchor commitment"),
        "b8": (8.6, 3.7, 2.4, 0.9, "Step 103\nOn-Chain Registry", "Stores audit anchor in local Hardhat registry"),
        "b9": (11.4, 3.7, 2.0, 0.9, "Step 104\nNegative Security", "Rejects replay and invalid zero commitment"),
        "b10": (4.2, 1.6, 2.7, 0.9, "Step 105\nPolicy-Gated Chain Validation", "Runs Step 103/104 through approval-gated workflow"),
        "b11": (7.6, 1.6, 2.7, 0.9, "Step 106/107\nSupervisor + Journal Output", "Converts evidence into milestone and paper-ready reports"),
    }

    for b in boxes.values():
        add_box(ax, *b)

    arrow(ax, 2.8, 6.25, 3.2, 6.25)
    arrow(ax, 5.4, 6.25, 5.8, 6.25)
    arrow(ax, 8.0, 6.25, 8.4, 6.25)
    arrow(ax, 10.6, 6.25, 11.0, 6.25)

    arrow(ax, 1.7, 5.8, 2.8, 4.6)
    arrow(ax, 4.4, 4.15, 5.3, 4.15)
    arrow(ax, 7.7, 4.15, 8.6, 4.15)
    arrow(ax, 11.0, 4.15, 11.4, 4.15)

    arrow(ax, 9.8, 3.7, 5.5, 2.5)
    arrow(ax, 12.4, 3.7, 6.0, 2.5)
    arrow(ax, 6.9, 2.05, 7.6, 2.05)

    ax.text(
        7,
        0.75,
        "Human-in-the-loop safety boundary: no automatic git push, public-chain deployment, paper submission, supervisor email, evidence deletion, or real-fund transaction.",
        ha="center",
        va="center",
        fontsize=9,
        style="italic",
    )

    fig.tight_layout()
    fig.savefig(FIG_PNG, dpi=220, bbox_inches="tight")
    fig.savefig(FIG_PDF, bbox_inches="tight")
    fig.savefig(FIG_SVG, bbox_inches="tight")
    plt.close(fig)


def markdown_table(header, rows):
    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def build_markdown(state):
    km = state["keyMetrics"]

    lines = [
        "# L4 Journal-Ready Architecture Figure and Result Tables: Steps 96-105",
        "",
        "## Purpose",
        "",
        "This document converts the implemented Level 4 automation/audit/on-chain workflow into journal-ready architecture and evaluation material.",
        "",
        "## Figure 6.1",
        "",
        f"- PNG: `{rel(FIG_PNG)}`",
        f"- PDF: `{rel(FIG_PDF)}`",
        f"- SVG: `{rel(FIG_SVG)}`",
        "",
        "Suggested caption:",
        "",
        "> Figure 6.1. Policy-gated Level 4 ZKTrustLLM-Agents automation architecture. The workflow links automated experiment execution, KPI-based decisioning, human-approved remediation, governance, hash-chained audit provenance, IPFS/blockchain-ready anchoring, local on-chain registry validation, and replay/invalid-anchor negative-security testing.",
        "",
        "## Table 6.1: Workflow Components",
        "",
        markdown_table(["Step", "Component", "Status / Decision", "Role", "Evidence"], state["workflowRows"]),
        "",
        "## Table 6.2: Audit and On-Chain Evidence Values",
        "",
        markdown_table(["Evidence", "Value", "Source"], state["evidenceRows"]),
        "",
        "## Table 6.3: Journal Contribution Mapping",
        "",
        markdown_table(["Contribution", "Claim", "Evidence Steps", "Journal Meaning"], state["contributionRows"]),
        "",
        "## Table 6.4: Governance Boundary",
        "",
        markdown_table(["Boundary Class", "Actions"], state["governanceRows"]),
        "",
        "## Key Result Summary",
        "",
        f"- Step 96 automation status: `{km['step96Status']}`",
        f"- Step 100 scheduler status: `{km['step100Status']}`",
        f"- Step 101 final ledger hash: `{km['step101FinalHash']}`",
        f"- Step 102 IPFS CID: `{km['step102IpfsCid']}`",
        f"- Step 102 commitment hash: `{km['step102Commitment']}`",
        f"- Step 103 transaction hash: `{km['step103TxHash']}`",
        f"- Step 103 gas used: `{km['step103GasUsed']}`",
        f"- Step 104 negative-security status: `{km['step104Status']}`",
        f"- Step 105 policy-gated validation status: `{km['step105Status']}`",
        "",
        "## Paper-Ready Interpretation",
        "",
        "The implemented system demonstrates a controlled Level 4 agentic automation workflow. It does not only execute experiments; it validates KPIs, recommends actions, executes approved remediation, preserves tamper-evident audit evidence, anchors evidence through IPFS and blockchain-ready commitments, and validates the commitment through a local smart-contract registry with negative-security testing.",
        "",
        "## Generated Files",
        "",
        f"- Summary JSON: `{rel(SUMMARY_JSON)}`",
        f"- Markdown: `{rel(DOC_MD)}`",
        f"- PDF: `{rel(PDF_OUT)}`",
        f"- Workflow CSV: `{rel(WORKFLOW_CSV)}`",
        f"- Evidence CSV: `{rel(EVIDENCE_CSV)}`",
        f"- Contribution CSV: `{rel(CONTRIBUTION_CSV)}`",
        f"- Governance CSV: `{rel(GOVERNANCE_CSV)}`",
    ]

    DOC_MD.write_text("\n".join(lines) + "\n")

def para(text, style):
    return Paragraph(esc(text), style)


def small_table(header, rows, col_widths):
    data = [[para(x, STYLES["TableHead"]) for x in header]]
    for row in rows:
        data.append([para(x, STYLES["TableCell"]) for x in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def build_pdf(state):
    story = []

    story.append(para("ZKTrustLLM-Agents L4 Journal-Ready Architecture and Result Tables", STYLES["RptTitle"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(para("Steps 96-105: Policy-Gated Agentic Automation, Audit Ledger, IPFS Anchor, and On-Chain Validation", STYLES["Subtitle"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(para("Purpose", STYLES["RptHeading2"]))
    story.append(para(
        "This report converts the implemented Level 4 automation and audit chain into journal-ready material: one architecture figure, workflow component table, evidence table, contribution mapping table, and governance-boundary table.",
        STYLES["Body"],
    ))
    story.append(Spacer(1, 0.15 * inch))

    story.append(para("Figure 6.1. Policy-Gated Agentic Automation Architecture", STYLES["RptHeading2"]))
    story.append(Image(str(FIG_PNG), width=7.2 * inch, height=4.1 * inch))
    story.append(Spacer(1, 0.1 * inch))
    story.append(para(
        "Caption: Policy-gated Level 4 ZKTrustLLM-Agents automation architecture linking automated experiment execution, KPI-based decisioning, human-approved remediation, governance, hash-chained audit provenance, IPFS/blockchain-ready anchoring, local on-chain registry validation, and replay/invalid-anchor negative-security testing.",
        STYLES["Caption"],
    ))
    story.append(PageBreak())

    story.append(para("Table 6.1. Workflow Components", STYLES["RptHeading2"]))
    story.append(small_table(
        ["Step", "Component", "Status", "Role"],
        [r[:4] for r in state["workflowRows"]],
        [0.75 * inch, 1.45 * inch, 1.15 * inch, 3.65 * inch],
    ))
    story.append(PageBreak())

    story.append(para("Table 6.2. Audit and On-Chain Evidence Values", STYLES["RptHeading2"]))
    story.append(small_table(
        ["Evidence", "Value", "Source"],
        state["evidenceRows"],
        [2.05 * inch, 3.65 * inch, 1.1 * inch],
    ))
    story.append(PageBreak())

    story.append(para("Table 6.3. Journal Contribution Mapping", STYLES["RptHeading2"]))
    story.append(small_table(
        ["ID", "Claim", "Evidence", "Journal Meaning"],
        state["contributionRows"],
        [0.45 * inch, 1.8 * inch, 1.15 * inch, 3.5 * inch],
    ))
    story.append(Spacer(1, 0.2 * inch))

    story.append(para("Table 6.4. Governance Boundary", STYLES["RptHeading2"]))
    story.append(small_table(
        ["Boundary Class", "Actions"],
        state["governanceRows"],
        [1.9 * inch, 5.0 * inch],
    ))

    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=A4,
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
    )
    doc.build(story)


def main():
    state = collect_state()

    write_csv(WORKFLOW_CSV, ["step", "component", "status_or_decision", "role", "evidence_path"], state["workflowRows"])
    write_csv(EVIDENCE_CSV, ["evidence", "value", "source"], state["evidenceRows"])
    write_csv(CONTRIBUTION_CSV, ["contribution_id", "claim", "evidence_steps", "journal_meaning"], state["contributionRows"])
    write_csv(GOVERNANCE_CSV, ["boundary_class", "actions"], state["governanceRows"])

    build_figure(state)
    build_markdown(state)
    build_pdf(state)

    summary = {
        "experiment": "step107_journal_ready_architecture_tables",
        "createdAt": state["createdAt"],
        "figurePng": rel(FIG_PNG),
        "figurePdf": rel(FIG_PDF),
        "figureSvg": rel(FIG_SVG),
        "workflowCsv": rel(WORKFLOW_CSV),
        "evidenceCsv": rel(EVIDENCE_CSV),
        "contributionCsv": rel(CONTRIBUTION_CSV),
        "governanceCsv": rel(GOVERNANCE_CSV),
        "markdown": rel(DOC_MD),
        "pdf": rel(PDF_OUT),
        "keyMetrics": state["keyMetrics"],
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps({
        "experiment": summary["experiment"],
        "figurePng": summary["figurePng"],
        "markdown": summary["markdown"],
        "pdf": summary["pdf"],
        "summaryJson": rel(SUMMARY_JSON),
    }, indent=2))


if __name__ == "__main__":
    STYLES = getSampleStyleSheet()
    STYLES.add(ParagraphStyle(
        name="RptTitle",
        parent=STYLES["Title"],
        alignment=TA_CENTER,
        fontSize=15,
        leading=18,
        spaceAfter=8,
    ))
    STYLES.add(ParagraphStyle(
        name="Subtitle",
        parent=STYLES["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        spaceAfter=8,
    ))
    STYLES.add(ParagraphStyle(
        name="RptHeading2",
        parent=STYLES["Heading2"],
        fontSize=11,
        leading=14,
        spaceBefore=8,
        spaceAfter=6,
    ))
    STYLES.add(ParagraphStyle(
        name="Body",
        parent=STYLES["BodyText"],
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
    ))
    STYLES.add(ParagraphStyle(
        name="Caption",
        parent=STYLES["BodyText"],
        fontSize=8,
        leading=10,
        alignment=TA_JUSTIFY,
    ))
    STYLES.add(ParagraphStyle(
        name="TableHead",
        parent=STYLES["BodyText"],
        fontSize=7,
        leading=8,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    ))
    STYLES.add(ParagraphStyle(
        name="TableCell",
        parent=STYLES["BodyText"],
        fontSize=6.5,
        leading=8,
    ))

    main()
