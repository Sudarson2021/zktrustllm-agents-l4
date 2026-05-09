#!/usr/bin/env python3

from datetime import datetime
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
OUT_DIR = ROOT / "results" / "l4_report_pdf"
DOCS_DIR = ROOT / "docs" / "report"

OUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

PDF = OUT_DIR / "zktrustllm_l4_integrated_history_automation_report_steps_foundation_to_93.pdf"
MD = DOCS_DIR / "zktrustllm_l4_integrated_history_automation_report_steps_foundation_to_93.md"

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="TitleCenter",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=20,
    leading=24,
    spaceAfter=18,
))

styles.add(ParagraphStyle(
    name="Section",
    parent=styles["Heading1"],
    fontSize=15,
    leading=18,
    spaceBefore=14,
    spaceAfter=8,
))

styles.add(ParagraphStyle(
    name="Subsection",
    parent=styles["Heading2"],
    fontSize=12,
    leading=15,
    spaceBefore=10,
    spaceAfter=6,
))

styles.add(ParagraphStyle(
    name="BodyJustify",
    parent=styles["BodyText"],
    alignment=TA_JUSTIFY,
    fontSize=9.5,
    leading=13,
    spaceAfter=6,
))

styles.add(ParagraphStyle(
    name="Small",
    parent=styles["BodyText"],
    fontSize=8,
    leading=10,
))

def p(text, style="BodyJustify"):
    return Paragraph(text, styles[style])

def heading(text):
    return Paragraph(text, styles["Section"])

def subheading(text):
    return Paragraph(text, styles["Subsection"])

def table(data, widths=None):
    if widths is None:
        widths = [1.6 * inch for _ in data[0]]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
    ]))
    return t

story = []

story.append(p("ZKTrustLLM-Agents Level 4", "TitleCenter"))
story.append(p("Integrated Full Technical Documentation and Agentic AI Automation Roadmap", "TitleCenter"))
story.append(p(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "Small"))
story.append(Spacer(1, 12))

story.append(heading("1. Executive Summary"))
story.append(p(
    "This report integrates the earlier ZKTrustLLM-Agents L4 foundation with the later "
    "MCP/A2A, media-plane, DTLS-RTP, impairment, and network namespace validation steps. "
    "It is intended as a supervisor-ready full-picture document and as a planning base "
    "for the next stage of agentic AI automation."
))

story.append(heading("2. Full Project Picture"))
story.append(table([
    ["Layer", "Implemented Work", "Research Meaning"],
    ["Control-plane semantics", "Roles, policies, actions, trust states, gateway schema", "Defines the bounded meaning of L4 decisions"],
    ["Contract state", "AgentRegistry, CapabilityManager, PolicyRegistry", "Creates authenticated control-plane state"],
    ["Proof pipeline", "AUTH_V2, AUTH_V2.1, AUTH_V2.2", "Enables Groth16 proof-governed admissible decisions"],
    ["MCP/A2A coordination", "MCP server, A2A references, bundle verification", "Allows agents to coordinate through compact authenticated references"],
    ["Control telemetry", "Semi-live MCP/A2A latency and multi-agent scaling", "Measures coordination cost and scalability"],
    ["Media-plane baseline", "Live RTP telemetry", "Connects control-plane research to packet-level media delivery"],
    ["Secure media-plane", "DTLS-wrapped RTP validation", "Adds protected media delivery baseline"],
    ["Network stress", "Loopback tc netem impairment", "Measures behaviour under delay, jitter, loss"],
    ["Namespace realism", "Two Linux network namespaces over veth", "Moves closer to two-node deployment while staying reproducible"],
    ["Automation roadmap", "Validator, orchestrator, report compiler, feedback tracker", "Prepares full agentic AI-assisted research workflow"],
], [1.4*inch, 2.3*inch, 2.5*inch]))

story.append(heading("3. Earlier Foundation: AUTH_V2 to AUTH_V2.2"))
story.append(p(
    "The earlier foundation implemented the L4 control-plane contracts and the progressive "
    "zero-knowledge proof pipeline. AUTH_V2 bound the request to control-plane fields. "
    "AUTH_V2.1 added policy admissibility. AUTH_V2.2 added trust-state/action admissibility "
    "for the concrete Restricted -> Isolate path."
))
story.append(table([
    ["Proof Stage", "Added Capability", "Strongest Claim"],
    ["AUTH_V2", "Control-plane request binding", "Proof binds agent, capability, policy, action, context, expiry, and trace commitment"],
    ["AUTH_V2.1", "Policy admissibility flag", "Proof verifies only when policyAdmissibilityFlag == 1"],
    ["AUTH_V2.2", "Trust-state/action pair", "Proof validates Restricted -> Isolate as a bounded admissible action"],
], [1.2*inch, 2.6*inch, 2.6*inch]))

story.append(heading("4. Later Level 4 Progress: Steps 77-93"))
story.append(table([
    ["Step", "Main Output"],
    ["77", "A2A reference-aware coordination"],
    ["79", "Proper MCP L4 context server"],
    ["80", "MCP/A2A KPI analysis"],
    ["81", "AUTH_V2.3/reference-bound proof direction"],
    ["82", "Negative-security validation"],
    ["83", "Deterministic network KPI telemetry"],
    ["84", "Journal-ready evaluation write-up"],
    ["85", "Benchmark result figures"],
    ["86", "Semi-live MCP/A2A control telemetry"],
    ["87", "Multi-agent scaling telemetry"],
    ["88", "Technical report PDF for Steps 77-87"],
    ["89", "Live RTP media-plane telemetry"],
    ["90", "DTLS-wrapped RTP media-plane validation"],
    ["91", "Plain RTP vs DTLS-RTP network impairment"],
    ["92", "Updated technical report through Step 91"],
    ["93", "Linux network namespace plain RTP vs DTLS-RTP validation"],
], [0.8*inch, 5.6*inch]))

story.append(PageBreak())

story.append(heading("5. Supervisor Feedback Alignment"))
story.append(table([
    ["Supervisor Need", "Implemented Evidence", "Status"],
    ["Explain MCP/A2A over L4", "Steps 79-87 documentation and telemetry", "Done"],
    ["Use agent KPIs", "Step 86 and Step 87 control-plane measurements", "Done"],
    ["Use network KPIs", "Steps 89-93 RTP/DTLS/impairment results", "Done"],
    ["Move beyond emulation", "Semi-live control telemetry and live RTP validation", "Done"],
    ["Add secure media validation", "DTLS-wrapped RTP tunnel/proxy baseline", "Done"],
    ["Test under stress", "tc netem loopback and namespace experiments", "Done"],
    ["Prepare for future automation", "Step 95 automation roadmap", "In progress"],
], [1.8*inch, 3.4*inch, 1.0*inch]))

story.append(heading("6. Current Research Claim"))
story.append(p(
    "The project now supports a coherent full-stack Level 4 prototype in which "
    "proof-governed agent decisions can be represented through contract-backed control-plane "
    "state, exchanged between agents through MCP/A2A reference coordination, measured through "
    "semi-live control-plane KPIs, and connected to RTP/DTLS media-plane behaviour under "
    "controlled network impairment."
))

story.append(heading("7. Forward Agentic AI Automation Plan"))
story.append(table([
    ["Automation Step", "Target Script", "Purpose"],
    ["Step 96", "validate_l4_results.py", "Validate all JSON, CSV, packet, bitrate, jitter, and report artifacts"],
    ["Step 97", "run_l4_full_experiment_suite.py", "Run all reproducible experiments from one command"],
    ["Step 98", "supervisor_feedback_tracker.py", "Map feedback to project artifacts and status"],
    ["Step 99", "build_l4_master_report.py", "Automatically compile Markdown/PDF/paper tables"],
    ["Step 100", "run_two_machine_or_mininet_validation.py", "Move beyond single-machine namespace topology"],
], [1.0*inch, 2.4*inch, 2.8*inch]))

story.append(heading("8. Recommended Next Steps"))
story.append(p(
    "The next engineering step should be Step 96: a full result validator. This should check "
    "that all major result files exist, JSON files parse successfully, packet counts are positive, "
    "bitrate is positive, jitter is within realistic bounds, Git status is clean, and the latest "
    "PDF report exists."
))
story.append(p(
    "After that, Step 97 should create a full experiment-suite runner that can execute the "
    "control-plane, media-plane, impairment, and namespace workflows in a structured order. "
    "This will make the project easier to reproduce and easier to present in supervisor meetings."
))

story.append(heading("9. Practical Continuation Command"))
story.append(p(
    "Recommended continuation point:"
))
story.append(p(
    "<font name='Courier'>cd ~/zktrustllm-agents-l4<br/>"
    "git checkout l4-step95-integrated-history-automation-report<br/>"
    "source .venv/bin/activate<br/>"
    "python scripts/l4/build_l4_integrated_history_automation_report_pdf.py<br/>"
    "git status</font>",
    "Small"
))

doc = SimpleDocTemplate(
    str(PDF),
    pagesize=A4,
    rightMargin=36,
    leftMargin=36,
    topMargin=42,
    bottomMargin=42,
)

doc.build(story)

md = """# ZKTrustLLM-Agents L4 Integrated Full Technical Documentation

This report integrates the earlier AUTH_V2 to AUTH_V2.2 foundation with the later Steps 77-93 implementation.

Main PDF:

`results/l4_report_pdf/zktrustllm_l4_integrated_history_automation_report_steps_foundation_to_93.pdf`

Main coverage:

- control-plane semantics,
- Solidity contracts,
- gateway validation,
- AUTH_V2 / AUTH_V2.1 / AUTH_V2.2,
- MCP/A2A reference coordination,
- semi-live control telemetry,
- multi-agent scaling,
- RTP media-plane validation,
- DTLS-wrapped RTP validation,
- network impairment,
- Linux namespace validation,
- supervisor feedback alignment,
- forward agentic AI automation roadmap.

Recommended next step:

Step 96 - implement a full result validator.
"""

MD.write_text(md)

print(f"Saved Markdown: {MD}")
print(f"Saved PDF     : {PDF}")
