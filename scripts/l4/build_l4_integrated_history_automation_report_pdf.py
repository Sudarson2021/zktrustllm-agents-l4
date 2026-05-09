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
    fontSize=18,
    leading=23,
    spaceAfter=14,
))

styles.add(ParagraphStyle(
    name="Section",
    parent=styles["Heading1"],
    fontSize=14,
    leading=18,
    spaceBefore=12,
    spaceAfter=7,
))

styles.add(ParagraphStyle(
    name="Subsection",
    parent=styles["Heading2"],
    fontSize=11,
    leading=14,
    spaceBefore=8,
    spaceAfter=5,
))

styles.add(ParagraphStyle(
    name="BodyJustify",
    parent=styles["BodyText"],
    alignment=TA_JUSTIFY,
    fontSize=9.2,
    leading=12.5,
    spaceAfter=5,
))

styles.add(ParagraphStyle(
    name="SmallMono",
    parent=styles["BodyText"],
    fontName="Courier",
    fontSize=7.5,
    leading=9,
    spaceAfter=4,
))

styles.add(ParagraphStyle(
    name="Small",
    parent=styles["BodyText"],
    fontSize=8,
    leading=10,
    spaceAfter=4,
))

def clean_text(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

def p(text, style="BodyJustify"):
    return Paragraph(clean_text(text), styles[style])

def heading(text):
    return Paragraph(clean_text(text), styles["Section"])

def subheading(text):
    return Paragraph(clean_text(text), styles["Subsection"])

def make_table(data, widths):
    safe = [[clean_text(str(c)) for c in row] for row in data]
    t = Table(safe, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
    ]))
    return t

def add_markdown_file(story, path: Path, title: str):
    story.append(PageBreak())
    story.append(heading(title))

    if not path.exists():
        story.append(p(f"Missing file: {path}", "Small"))
        return

    lines = path.read_text(errors="ignore").splitlines()
    buffer = []

    def flush():
        nonlocal buffer
        if buffer:
            text = " ".join(x.strip() for x in buffer if x.strip())
            if text:
                story.append(p(text))
            buffer = []

    in_code = False
    code_lines = []

    for line in lines:
        raw = line.rstrip()

        if raw.startswith("```"):
            flush()
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                if code_lines:
                    story.append(Paragraph(clean_text("\n".join(code_lines)), styles["SmallMono"]))
                    story.append(Spacer(1, 4))
            continue

        if in_code:
            code_lines.append(raw)
            continue

        if raw.startswith("# "):
            flush()
            story.append(heading(raw[2:].strip()))
        elif raw.startswith("## "):
            flush()
            story.append(subheading(raw[3:].strip()))
        elif raw.startswith("### "):
            flush()
            story.append(subheading(raw[4:].strip()))
        elif raw.startswith("- "):
            flush()
            story.append(p("• " + raw[2:].strip()))
        elif raw.startswith("|"):
            flush()
            story.append(p(raw, "SmallMono"))
        elif not raw.strip():
            flush()
        else:
            buffer.append(raw)

    flush()

story = []

story.append(p("ZKTrustLLM-Agents Level 4", "TitleCenter"))
story.append(p("Integrated Full Technical Documentation and Agentic AI Automation Roadmap", "TitleCenter"))
story.append(p(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "Small"))
story.append(Spacer(1, 12))

story.append(heading("1. Executive Summary"))
story.append(p(
    "This report integrates the earlier ZKTrustLLM-Agents L4 foundation with the later "
    "MCP/A2A, reference-bound proof, media-plane, DTLS-RTP, impairment, and Linux network "
    "namespace validation steps. It is intended as a supervisor-ready full-picture document "
    "and as a planning base for the next stage of agentic AI automation."
))

story.append(heading("2. Full Project Picture"))
story.append(make_table([
    ["Layer", "Implemented Work", "Research Meaning"],
    ["Control-plane semantics", "Roles, policies, actions, trust states, gateway schema", "Defines the bounded meaning of L4 decisions"],
    ["Contract state", "AgentRegistry, CapabilityManager, PolicyRegistry", "Creates authenticated control-plane state"],
    ["Proof pipeline", "AUTH_V2, AUTH_V2.1, AUTH_V2.2", "Enables Groth16 proof-governed admissible decisions"],
    ["MCP/A2A coordination", "MCP server, A2A references, reference bundle verification", "Allows agents to coordinate through compact authenticated references"],
    ["Control telemetry", "Semi-live MCP/A2A latency and multi-agent scaling", "Measures coordination cost and scalability"],
    ["Media-plane baseline", "Live RTP telemetry", "Connects control-plane research to packet-level media delivery"],
    ["Secure media-plane", "DTLS-wrapped RTP validation", "Adds protected media delivery baseline"],
    ["Network stress", "Loopback tc netem impairment", "Measures behaviour under delay, jitter, and loss"],
    ["Namespace realism", "Two Linux network namespaces over veth", "Moves closer to two-node deployment while staying reproducible"],
    ["Automation roadmap", "Validator, orchestrator, report compiler, feedback tracker", "Prepares full agentic AI-assisted research workflow"],
], [1.35*inch, 2.35*inch, 2.55*inch]))

story.append(heading("3. Key Implementation Timeline"))
story.append(make_table([
    ["Phase", "Main Work"],
    ["Foundation", "L4 control-plane architecture, contracts, gateway validation"],
    ["AUTH_V2", "Request-binding Groth16 proof"],
    ["AUTH_V2.1", "Policy-admissibility-aware proof"],
    ["AUTH_V2.2", "Trust-state/action admissible pair proof for Restricted -> Isolate"],
    ["Steps 77-83", "MCP/A2A reference coordination, negative tests, deterministic KPI evaluation"],
    ["Steps 84-88", "Journal write-up, figures, semi-live control telemetry, multi-agent scaling, report PDF"],
    ["Step 89", "Live RTP media-plane telemetry"],
    ["Step 90", "DTLS-wrapped RTP validation"],
    ["Step 91", "Plain RTP vs DTLS-RTP impairment matrix"],
    ["Step 92", "Updated technical report through Step 91"],
    ["Step 93", "Linux network namespace sender-receiver validation"],
    ["Step 94", "Full technical documentation through Step 93"],
    ["Step 95", "Integrated history and automation roadmap"],
], [1.2*inch, 5.0*inch]))

story.append(heading("4. Current Research Claim"))
story.append(p(
    "The project now supports a coherent full-stack Level 4 prototype in which proof-governed "
    "agent decisions can be represented through contract-backed control-plane state, exchanged "
    "between agents through MCP/A2A reference coordination, measured through semi-live control-plane "
    "KPIs, and connected to RTP/DTLS media-plane behaviour under controlled network impairment."
))

story.append(heading("5. Recommended Next Step"))
story.append(p(
    "The next engineering step should be Step 96: a full result validator. This validator should "
    "check JSON validity, CSV existence, packet counts, bitrate, jitter, packet loss, Git cleanliness, "
    "and the presence of current Markdown/PDF reports. This will make future agentic automation safer."
))

add_markdown_file(
    story,
    ROOT / "docs" / "report" / "l4_early_foundation_auth_v2_to_v2_2.md",
    "Appendix A: Earlier Foundation AUTH_V2 to AUTH_V2.2",
)

add_markdown_file(
    story,
    ROOT / "docs" / "report" / "l4_full_project_timeline_steps_foundation_to_93.md",
    "Appendix B: Full Project Timeline",
)

add_markdown_file(
    story,
    ROOT / "docs" / "roadmap" / "AGENTIC_AI_AUTOMATION_ROADMAP.md",
    "Appendix C: Agentic AI Automation Roadmap",
)

add_markdown_file(
    story,
    ROOT / "docs" / "progress" / "SUPERVISOR_FEEDBACK_TRACKER.md",
    "Appendix D: Supervisor Feedback Tracker",
)

doc = SimpleDocTemplate(
    str(PDF),
    pagesize=A4,
    rightMargin=36,
    leftMargin=36,
    topMargin=42,
    bottomMargin=42,
)

doc.build(story)

MD.write_text("""# ZKTrustLLM-Agents L4 Integrated Full Technical Documentation

This Markdown file accompanies the integrated full technical documentation PDF.

PDF:

`results/l4_report_pdf/zktrustllm_l4_integrated_history_automation_report_steps_foundation_to_93.pdf`

Coverage:

- earlier AUTH_V2 to AUTH_V2.2 foundation,
- control-plane contracts,
- gateway validation,
- MCP/A2A reference coordination,
- semi-live telemetry,
- multi-agent scaling,
- RTP media-plane validation,
- DTLS-wrapped RTP validation,
- network impairment,
- Linux namespace validation,
- supervisor feedback alignment,
- agentic AI automation roadmap.

Recommended next step:

Step 96 - implement a full result validator.
""")

print(f"Saved Markdown: {MD}")
print(f"Saved PDF     : {PDF}")
