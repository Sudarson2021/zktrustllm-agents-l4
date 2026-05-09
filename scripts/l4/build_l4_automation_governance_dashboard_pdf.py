#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "results/l4_automation_governance"
PDF_DIR = ROOT / "results/l4_report_pdf"
DOC_DIR = ROOT / "docs/l4/automation_governance"

OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

STEP96 = ROOT / "results/l4_agentic_automation/agentic_automation_summary.json"
STEP97 = ROOT / "results/l4_closed_loop_agent/closed_loop_kpi_decision.json"
STEP98 = ROOT / "results/l4_remediation_executor/remediation_execution_plan.json"

MD = DOC_DIR / "L4_AUTOMATION_GOVERNANCE_DASHBOARD.md"
PDF = PDF_DIR / "zktrustllm_l4_automation_governance_dashboard_steps96_98.pdf"
JSON_OUT = OUT_DIR / "automation_governance_dashboard.json"


def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def nested(d, keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


s96 = load_json(STEP96) or {}
s97 = load_json(STEP97) or {}
s98 = load_json(STEP98) or {}

d97 = s97.get("decision", {}) if isinstance(s97.get("decision"), dict) else {}

dashboard = {
    "experiment": "step99_l4_automation_governance_dashboard",
    "createdAt": datetime.now().isoformat(timespec="seconds"),
    "automationChain": {
        "step96": {
            "name": "Agentic Automation Suite",
            "status": s96.get("overallStatus", "UNKNOWN"),
            "purpose": "Runs L4 control-plane, agent-scaling, RTP, DTLS-RTP, loopback impairment, and namespace impairment workflows."
        },
        "step97": {
            "name": "Closed-Loop KPI Decision Agent",
            "primaryAction": s97.get("primaryAction") or d97.get("primaryAction", "UNKNOWN"),
            "priority": s97.get("priority") or d97.get("priority", "UNKNOWN"),
            "purpose": "Reads KPI artifacts and recommends the next safe workflow action."
        },
        "step98": {
            "name": "Closed-Loop Remediation Executor",
            "status": s98.get("status", "UNKNOWN"),
            "mode": s98.get("mode", "UNKNOWN"),
            "purpose": "Executes the recommended remediation only after explicit human approval."
        }
    },
    "governanceBoundary": {
        "allowedWithNoPrivilege": [
            "read KPI JSON and CSV artifacts",
            "validate experiment outputs",
            "generate Markdown reports",
            "generate PDF reports",
            "create artifact manifests",
            "recommend next safe workflow action"
        ],
        "allowedOnlyWithHumanApproval": [
            "execute remediation workflow",
            "regenerate supervisor PDF",
            "rerun non-privileged experiments",
            "rerun privileged network experiments with explicit sudo approval"
        ],
        "neverAutomatic": [
            "git push",
            "modify Git history",
            "submit papers",
            "email supervisor",
            "deploy public systems",
            "delete research evidence",
            "run privileged commands without explicit approval"
        ]
    },
    "nextMilestone": {
        "step100": "Policy-gated autonomous scheduler with dry-run, approval gates, audit logs, and rollback notes.",
        "researchMeaning": "Moves the project from experiment automation to controlled agentic research operations."
    }
}

JSON_OUT.write_text(json.dumps(dashboard, indent=2))


md_lines = [
    "# Step 99 L4 Automation Governance Dashboard",
    "",
    "## Purpose",
    "",
    "This report explains the current state of the ZKTrustLLM-Agents Level 4 automation workflow.",
    "",
    "It connects Step 96, Step 97, and Step 98 into one supervisor-readable governance view.",
    "",
    "## Closed-Loop Automation Chain",
    "",
    "| Step | Component | Status / Decision | Research Meaning |",
    "|---|---|---|---|",
    f"| Step 96 | Agentic Automation Suite | {dashboard['automationChain']['step96']['status']} | Runs reproducible L4 experiments and validates outputs. |",
    f"| Step 97 | KPI Decision Agent | {dashboard['automationChain']['step97']['primaryAction']} | Converts KPI evidence into next-action recommendation. |",
    f"| Step 98 | Remediation Executor | {dashboard['automationChain']['step98']['status']} | Executes approved remediation/report generation with human approval. |",
    "",
    "## Automation Governance Boundary",
    "",
    "### Allowed without privileged execution",
]

for item in dashboard["governanceBoundary"]["allowedWithNoPrivilege"]:
    md_lines.append(f"- {item}")

md_lines += ["", "### Allowed only with human approval"]

for item in dashboard["governanceBoundary"]["allowedOnlyWithHumanApproval"]:
    md_lines.append(f"- {item}")

md_lines += ["", "### Never automatic"]

for item in dashboard["governanceBoundary"]["neverAutomatic"]:
    md_lines.append(f"- {item}")

md_lines += [
    "",
    "## Supervisor Progress Interpretation",
    "",
    "The project has moved from manual experiment execution toward a controlled closed-loop automation chain.",
    "",
    "The current workflow can run experiments, validate KPIs, decide the next safe action, and execute approved remediation. This is an important PhD milestone because the system now demonstrates evidence-driven agentic research automation rather than isolated scripts.",
    "",
    "## Next Milestone",
    "",
    "Step 100 should implement a policy-gated autonomous scheduler. The scheduler should keep dry-run as default, require approval gates for privileged actions, preserve audit logs, and generate rollback notes.",
    "",
    "## Generated Artifacts",
    "",
    f"- Governance JSON: `{JSON_OUT.relative_to(ROOT)}`",
    f"- Governance Markdown: `{MD.relative_to(ROOT)}`",
    f"- Governance PDF: `{PDF.relative_to(ROOT)}`",
]

MD.write_text("\n".join(md_lines))


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name="BodyJustify", parent=styles["BodyText"], alignment=TA_JUSTIFY, leading=14))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))

doc = SimpleDocTemplate(str(PDF), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
story = []

story.append(Paragraph("ZKTrustLLM-Agents L4 Automation Governance Dashboard", styles["TitleCenter"]))
story.append(Paragraph("Steps 96-98 Closed-Loop Automation Summary", styles["Heading2"]))
story.append(Paragraph(f"Generated: {dashboard['createdAt']}", styles["Small"]))
story.append(Spacer(1, 12))

story.append(Paragraph("1. Purpose", styles["Heading1"]))
story.append(Paragraph(
    "This report documents the governance boundary and scientific meaning of the current Level 4 automation workflow. "
    "It connects the agentic automation suite, KPI decision agent, and remediation executor into a single supervisor-readable view.",
    styles["BodyJustify"]
))

story.append(Spacer(1, 10))
story.append(Paragraph("2. Closed-Loop Automation Chain", styles["Heading1"]))

table_data = [
    ["Step", "Component", "Status / Decision", "Meaning"],
    ["96", "Agentic automation suite", dashboard["automationChain"]["step96"]["status"], "Runs L4 experiments"],
    ["97", "KPI decision agent", dashboard["automationChain"]["step97"]["primaryAction"], "Recommends next action"],
    ["98", "Remediation executor", dashboard["automationChain"]["step98"]["status"], "Executes approved plan"],
]

table = Table(table_data, colWidths=[0.6*inch, 1.7*inch, 1.7*inch, 2.2*inch])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]))
story.append(table)

story.append(Spacer(1, 14))
story.append(Paragraph("3. Governance Boundary", styles["Heading1"]))

for heading, key in [
    ("Allowed without privileged execution", "allowedWithNoPrivilege"),
    ("Allowed only with human approval", "allowedOnlyWithHumanApproval"),
    ("Never automatic", "neverAutomatic"),
]:
    story.append(Paragraph(heading, styles["Heading2"]))
    for item in dashboard["governanceBoundary"][key]:
        story.append(Paragraph(f"- {item}", styles["BodyText"]))
    story.append(Spacer(1, 6))

story.append(PageBreak())
story.append(Paragraph("4. Supervisor Progress Interpretation", styles["Heading1"]))
story.append(Paragraph(
    "The project has now reached a meaningful closed-loop automation milestone. "
    "Step 96 executes the L4 workflow, Step 97 evaluates KPI evidence and recommends a next action, "
    "and Step 98 executes only safe approved remediation. This demonstrates a controlled form of agentic research automation.",
    styles["BodyJustify"]
))

story.append(Spacer(1, 10))
story.append(Paragraph("5. Next Milestone: Step 100", styles["Heading1"]))
story.append(Paragraph(
    "The next milestone should implement a policy-gated autonomous scheduler. The scheduler should run in dry-run mode by default, "
    "use approval gates for privileged or irreversible actions, preserve audit logs, and generate rollback notes.",
    styles["BodyJustify"]
))

story.append(Spacer(1, 10))
story.append(Paragraph("6. Generated Artifacts", styles["Heading1"]))
story.append(Paragraph(f"Governance JSON: {JSON_OUT.relative_to(ROOT)}", styles["Small"]))
story.append(Paragraph(f"Governance Markdown: {MD.relative_to(ROOT)}", styles["Small"]))
story.append(Paragraph(f"Governance PDF: {PDF.relative_to(ROOT)}", styles["Small"]))

doc.build(story)

print(f"Saved JSON: {JSON_OUT}")
print(f"Saved Markdown: {MD}")
print(f"Saved PDF: {PDF}")
