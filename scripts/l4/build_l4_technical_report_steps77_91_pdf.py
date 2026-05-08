#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path

from PIL import Image as PILImage
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

OUT_DIR = ROOT / "results" / "l4_report_pdf"
DOC_DIR = ROOT / "docs" / "report"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

PDF_OUT = OUT_DIR / "zktrustllm_l4_technical_report_steps77_91.pdf"
MD_OUT = DOC_DIR / "zktrustllm_l4_technical_report_steps77_91.md"

def load_json(path):
    p = ROOT / path
    if not p.exists():
        return {}
    return json.loads(p.read_text())

def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)

def para(text, style):
    return Paragraph(str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)

def add_table(story, data, col_widths=None):
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.15 * inch))

def add_image(story, path, caption, styles, max_width=6.4 * inch):
    p = ROOT / path
    if not p.exists():
        return

    try:
        with PILImage.open(p) as im:
            w, h = im.size
        ratio = h / w
        width = max_width
        height = width * ratio
        if height > 4.3 * inch:
            height = 4.3 * inch
            width = height / ratio
        story.append(Image(str(p), width=width, height=height))
        story.append(para(caption, styles["Caption"]))
        story.append(Spacer(1, 0.15 * inch))
    except Exception as exc:
        story.append(para(f"Could not render image {path}: {exc}", styles["Body"]))

def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.55 * inch, 0.35 * inch, "ZKTrustLLM-Agents Level 4 Technical Report")
    canvas.drawRightString(A4[0] - 0.55 * inch, 0.35 * inch, f"Page {doc.page}")
    canvas.restoreState()

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="TitleCenter",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=18,
    leading=22,
    spaceAfter=18,
))
styles.add(ParagraphStyle(
    name="Heading1Custom",
    parent=styles["Heading1"],
    fontSize=13,
    leading=16,
    spaceBefore=12,
    spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Heading2Custom",
    parent=styles["Heading2"],
    fontSize=11,
    leading=14,
    spaceBefore=10,
    spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Body",
    parent=styles["BodyText"],
    fontSize=9,
    leading=12,
    alignment=TA_JUSTIFY,
    spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="Caption",
    parent=styles["BodyText"],
    fontSize=8,
    leading=10,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#444444"),
    spaceAfter=8,
))

story = []

story.append(para("ZKTrustLLM-Agents Level 4 Technical Report", styles["TitleCenter"]))
story.append(para("Steps 77-91: MCP/A2A Reference-Bound Coordination, ZK Proofs, Control-Plane Telemetry, RTP Media Validation, DTLS Protection, and Network Impairment Evaluation", styles["Body"]))
story.append(para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Body"]))
story.append(Spacer(1, 0.2 * inch))

story.append(para("1. Executive Summary", styles["Heading1Custom"]))
story.append(para(
    "This report consolidates the Level 4 ZKTrustLLM-Agents workflow from Step 77 to Step 91. "
    "The work progresses from blockchain-authenticated A2A references and MCP context retrieval to AUTH_V2.3 reference-bound proof verification, negative-security testing, control-plane telemetry, multi-agent scaling, live RTP media-plane measurement, DTLS-wrapped RTP validation, and network impairment evaluation.",
    styles["Body"],
))
story.append(para(
    "The main research direction is to show how Agentic AI systems can coordinate through compact references to authenticated blockchain state while preserving proof-governed decision semantics and measurable network/media-plane behaviour.",
    styles["Body"],
))

story.append(para("2. Step Timeline and Artifact Map", styles["Heading1Custom"]))
timeline = [
    ["Step", "Main contribution", "Primary evidence"],
    ["77", "A2A reference-aware coordination", "Reference registry and compact inter-agent reference exchange"],
    ["79", "MCP Level 4 context server", "Structured tools for blockchain-authenticated state retrieval"],
    ["80", "MCP/A2A KPI analysis", "Agent/control KPI summary"],
    ["81", "AUTH_V2.3 reference-bound proof", "Groth16-style proof-bound decision submission"],
    ["82", "Negative-security tests", "Tampered input and invalid-context rejection"],
    ["83", "Network KPI telemetry-emulation", "Control response, jitter, packet loss, interruption estimates"],
    ["84", "Journal evaluation write-up", "Paper-ready Level 4 evaluation sections and tables"],
    ["85", "Benchmark result figures", "Agent scaling and utility figures"],
    ["86", "Semi-live control telemetry", "Measured MCP/A2A local control-loop timing"],
    ["87", "Multi-agent scaling telemetry", "5-25 agent scaling evidence"],
    ["88", "Technical report PDF", "Supervisor-ready report up to Step 87"],
    ["89", "Live RTP media-plane telemetry", "Packet continuity, RTP jitter, bitrate"],
    ["90", "DTLS-wrapped RTP validation", "Secured RTP tunnel/proxy baseline"],
    ["91", "Network impairment evaluation", "Plain RTP vs DTLS-RTP under tc/netem stress"],
]
add_table(story, timeline, [0.55 * inch, 2.25 * inch, 3.2 * inch])

story.append(PageBreak())

# Load result files
semi_live = load_json("results/l4_live_telemetry/semi_live_control_summary.json")
multi_agent = load_json("results/l4_multi_agent_scaling/multi_agent_scaling_summary.json")
plain_rtp = load_json("results/l4_live_rtp_media/rtp_media_summary.json")
dtls_rtp = load_json("results/l4_dtls_rtp_media/dtls_rtp_media_summary.json")
impairment = load_json("results/l4_network_impairment/network_impairment_summary.json")
auth_neg = load_json("results/l4_auth_v2_3_negative/auth_v2_3_negative_summary.json")
mcp_neg = load_json("results/l4_mcp_a2a_security/mcp_a2a_negative_summary.json")

story.append(para("3. Security Validation Evidence", styles["Heading1Custom"]))
security_table = [
    ["Layer", "Metric", "Result", "Interpretation"],
    ["AUTH_V2.3", "Negative cases", fmt(auth_neg.get("negativeCaseCount")), "Tampered proof-bound inputs tested"],
    ["AUTH_V2.3", "Passed negative cases", fmt(auth_neg.get("negativeCasesPassed")), "Tampered proof paths rejected"],
    ["AUTH_V2.3", "Tampered rejection rate", fmt(auth_neg.get("unauthorizedOrTamperedRejectionRate")), "Verifier/attestor rejects invalid public inputs"],
    ["MCP/A2A", "Invalid-context rejection rate", fmt(mcp_neg.get("invalidContextRejectionRate")), "Invalid A2A references rejected"],
]
add_table(story, security_table, [1.0 * inch, 1.35 * inch, 1.1 * inch, 2.55 * inch])

story.append(para("4. Semi-Live MCP/A2A Control-Plane Telemetry", styles["Heading1Custom"]))
control_summary = semi_live.get("summary", {})
control_table = [["Mode", "Runs", "Success", "Avg ms", "P50 ms", "P95 ms", "Jitter std", "Avg bytes"]]
for mode, r in control_summary.items():
    if mode == "comparison":
        continue
    control_table.append([
        mode,
        fmt(r.get("runs")),
        fmt(r.get("successRate")),
        fmt(r.get("avgControlResponseMs")),
        fmt(r.get("p50ControlResponseMs")),
        fmt(r.get("p95ControlResponseMs")),
        fmt(r.get("jitterStdMs")),
        fmt(r.get("avgControlMessageBytes")),
    ])
add_table(story, control_table)

comparison = control_summary.get("comparison", {})
story.append(para(
    f"Step 86 reports L4-ref latency reduction versus L4 raw-context of {fmt(comparison.get('l4RefLatencyReductionVsRawPct'))}% and control-message reduction of {fmt(comparison.get('l4RefMessageReductionVsRawPct'))}%.",
    styles["Body"],
))
add_image(story, "results/l4_live_telemetry/figure_5_5_semi_live_control_latency.png", "Figure 5.5: Semi-live MCP/A2A control latency.", styles)
add_image(story, "results/l4_live_telemetry/figure_5_6_semi_live_control_summary.png", "Figure 5.6: Semi-live control summary.", styles)

story.append(PageBreak())

story.append(para("5. Multi-Agent Scaling Telemetry", styles["Heading1Custom"]))
multi_rows = multi_agent.get("summary", [])
if isinstance(multi_rows, dict):
    multi_rows = multi_rows.get("rows", [])
scaling_table = [["Mode", "Agents", "Success", "Total ms", "Per-agent ms", "Bytes", "Agents/s"]]
if isinstance(multi_rows, list):
    for r in multi_rows[:20]:
        scaling_table.append([
            fmt(r.get("mode")),
            fmt(r.get("agentCount") or r.get("agents")),
            fmt(r.get("successRate")),
            fmt(r.get("avgTotalLatencyMs")),
            fmt(r.get("avgLatencyPerAgentMs")),
            fmt(r.get("avgControlMessageBytes")),
            fmt(r.get("avgAgentsPerSecond")),
        ])
else:
    scaling_table.append(["See result JSON", "-", "-", "-", "-", "-", "-"])
add_table(story, scaling_table)

story.append(para(
    "Step 87 measures how Level 4 MCP/A2A coordination behaves across 5, 10, 15, 20, and 25 agents. "
    "The key result is that compact reference exchange significantly reduces control-message size and improves throughput compared with raw-context exchange.",
    styles["Body"],
))
add_image(story, "results/l4_multi_agent_scaling/figure_5_7_multi_agent_scaling_latency.png", "Figure 5.7: Multi-agent scaling latency.", styles)
add_image(story, "results/l4_multi_agent_scaling/figure_5_8_multi_agent_control_bytes.png", "Figure 5.8: Multi-agent control-message size.", styles)
add_image(story, "results/l4_multi_agent_scaling/figure_5_9_multi_agent_throughput.png", "Figure 5.9: Multi-agent throughput.", styles)

story.append(PageBreak())

story.append(para("6. Live RTP Media-Plane Telemetry", styles["Heading1Custom"]))
rtp_loss = plain_rtp.get("packetLoss", {})
rtp_jitter = plain_rtp.get("jitter", {})
rtp_table = [
    ["KPI", "Result", "Interpretation"],
    ["Capture duration", fmt(plain_rtp.get("captureSeconds")), "Live RTP capture window"],
    ["Received packets", fmt(plain_rtp.get("receivedPackets")), "Captured RTP packets"],
    ["Expected packets", fmt(rtp_loss.get("expected_packets")), "Expected from RTP sequence continuity"],
    ["Lost packets", fmt(rtp_loss.get("lost_packets")), "Sequence-gap loss"],
    ["Packet loss %", fmt(rtp_loss.get("packet_loss_pct")), "Media-plane packet loss"],
    ["Average bitrate kbps", fmt(plain_rtp.get("avgBitrateKbps")), "RTP throughput"],
    ["Average jitter ms", fmt(rtp_jitter.get("avgJitterComponentMs")), "RTP timing variation"],
    ["P50 jitter ms", fmt(rtp_jitter.get("p50JitterComponentMs")), "Median timing variation"],
    ["Max jitter ms", fmt(rtp_jitter.get("maxJitterComponentMs")), "Largest observed deviation"],
]
add_table(story, rtp_table, [1.7 * inch, 1.3 * inch, 3.0 * inch])
add_image(story, "results/l4_live_rtp_media/figure_5_10_live_rtp_jitter.png", "Figure 5.10: Live RTP jitter.", styles)
add_image(story, "results/l4_live_rtp_media/figure_5_11_live_rtp_bitrate.png", "Figure 5.11: Live RTP bitrate.", styles)
add_image(story, "results/l4_live_rtp_media/figure_5_12_live_rtp_sequence_progress.png", "Figure 5.12: RTP sequence progression.", styles)

story.append(PageBreak())

story.append(para("7. DTLS-Wrapped RTP Media-Plane Validation", styles["Heading1Custom"]))
dtls_loss = dtls_rtp.get("packetLoss", {})
dtls_jitter = dtls_rtp.get("jitter", {})
dtls_table = [
    ["KPI", "Result", "Interpretation"],
    ["Recovered RTP packets", fmt(dtls_rtp.get("receivedPackets")), "Packets recovered after DTLS tunnel"],
    ["Expected packets", fmt(dtls_loss.get("expected_packets")), "Expected sequence continuity"],
    ["Lost packets", fmt(dtls_loss.get("lost_packets")), "Sequence-gap loss"],
    ["Packet loss %", fmt(dtls_loss.get("packet_loss_pct")), "DTLS-wrapped RTP loss"],
    ["Average bitrate kbps", fmt(dtls_rtp.get("avgBitrateKbps")), "Recovered media throughput"],
    ["Average jitter ms", fmt(dtls_jitter.get("avgJitterComponentMs")), "Arrival-gap timing variation"],
    ["P50 jitter ms", fmt(dtls_jitter.get("p50JitterComponentMs")), "Median timing variation"],
    ["Max jitter ms", fmt(dtls_jitter.get("maxJitterComponentMs")), "Largest observed deviation"],
]
add_table(story, dtls_table, [1.7 * inch, 1.3 * inch, 3.0 * inch])
story.append(para(
    "Step 90 validates a DTLS tunnel/proxy baseline for RTP. It is not WebRTC DTLS-SRTP, but it demonstrates that RTP packets can be protected, recovered, and measured after DTLS transport.",
    styles["Body"],
))
add_image(story, "results/l4_dtls_rtp_media/figure_5_13_dtls_rtp_jitter.png", "Figure 5.13: DTLS-wrapped RTP jitter.", styles)
add_image(story, "results/l4_dtls_rtp_media/figure_5_14_plain_vs_dtls_packet_loss.png", "Figure 5.14: Plain RTP vs DTLS packet loss.", styles)
add_image(story, "results/l4_dtls_rtp_media/figure_5_15_plain_vs_dtls_bitrate.png", "Figure 5.15: Plain RTP vs DTLS bitrate.", styles)

story.append(PageBreak())

story.append(para("8. Network Impairment Evaluation: Plain RTP vs DTLS-RTP", styles["Heading1Custom"]))
story.append(para(
    "Step 91 compares plain RTP and DTLS-wrapped RTP under controlled loopback impairment using Linux tc netem. "
    "Profiles include clean baseline, fixed delay, delay with jitter, and delay with jitter plus packet loss. "
    "Jitter is reported as packet arrival-gap jitter to avoid misleading raw RTP timestamp artefacts.",
    styles["Body"],
))

imp_rows = impairment.get("rows", [])
imp_table = [["Profile", "Mode", "Packets", "Loss %", "Bitrate kbps", "Avg jitter", "P50", "P95"]]
for r in imp_rows:
    imp_table.append([
        fmt(r.get("profile")),
        fmt(r.get("mode")),
        fmt(r.get("receivedPackets")),
        fmt(r.get("packetLossPct")),
        fmt(r.get("avgBitrateKbps")),
        fmt(r.get("avgJitterMs")),
        fmt(r.get("p50JitterMs")),
        fmt(r.get("p95JitterMs")),
    ])
add_table(story, imp_table)

add_image(story, "results/l4_network_impairment/figure_5_16_plain_vs_dtls_impairment_packet_loss.png", "Figure 5.16: Packet loss under impairment.", styles)
add_image(story, "results/l4_network_impairment/figure_5_17_plain_vs_dtls_impairment_bitrate.png", "Figure 5.17: Bitrate under impairment.", styles)
add_image(story, "results/l4_network_impairment/figure_5_18_plain_vs_dtls_impairment_jitter.png", "Figure 5.18: Arrival-gap jitter under impairment.", styles)

story.append(PageBreak())

story.append(para("9. Journal-Ready Interpretation", styles["Heading1Custom"]))
story.append(para(
    "The Level 4 implementation now contains a complete evaluation ladder: proof-bound decision generation, negative-security rejection, MCP/A2A reference verification, semi-live control-plane telemetry, multi-agent scaling, live RTP media-plane measurement, DTLS-wrapped RTP validation, and impairment testing. "
    "This supports a journal-level argument that blockchain-authenticated shared state can be used by Agentic AI systems through compact A2A references and MCP tools, while media-plane KPIs can be measured under secure and impaired delivery conditions.",
    styles["Body"],
))
story.append(para(
    "The current limitations are also clear: the experiments run on localhost, the DTLS design is a controlled tunnel/proxy rather than WebRTC DTLS-SRTP, and future validation should move to two-machine, network namespace, Mininet, ns-3, or 5GIC testbed scenarios.",
    styles["Body"],
))

story.append(para("10. Recommended Next Steps", styles["Heading1Custom"]))
next_steps = [
    ["Priority", "Next step", "Reason"],
    ["1", "Two-machine RTP/DTLS validation", "Move beyond localhost loopback"],
    ["2", "Network namespace or Mininet replication", "Cleaner impairment isolation and reproducibility"],
    ["3", "Integrate LKH policy triggers with media experiments", "Connect proof-governed control decisions to media-plane response"],
    ["4", "Add repeated trials and confidence intervals", "Strengthen statistical validity"],
    ["5", "Prepare journal Results section", "Use Step 86-91 tables and figures directly"],
]
add_table(story, next_steps, [0.6 * inch, 2.2 * inch, 3.1 * inch])

doc = SimpleDocTemplate(
    str(PDF_OUT),
    pagesize=A4,
    rightMargin=0.5 * inch,
    leftMargin=0.5 * inch,
    topMargin=0.55 * inch,
    bottomMargin=0.55 * inch,
)
doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)

md = f"""# ZKTrustLLM-Agents Level 4 Technical Report: Steps 77-91

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PDF: `{PDF_OUT.relative_to(ROOT)}`

## Coverage

- Step 77: A2A reference-aware coordination
- Step 79: MCP Level 4 context server
- Step 80: MCP/A2A KPI analysis
- Step 81: AUTH_V2.3 reference-bound proof
- Step 82: Negative-security tests
- Step 83: Network KPI telemetry-emulation
- Step 84: Journal evaluation write-up
- Step 85: Benchmark result figures
- Step 86: Semi-live MCP/A2A control-plane telemetry
- Step 87: Multi-agent scaling telemetry
- Step 88: Technical report PDF
- Step 89: Live RTP media-plane telemetry
- Step 90: DTLS-wrapped RTP media-plane validation
- Step 91: Network impairment evaluation

## Main PDF Output

`results/l4_report_pdf/zktrustllm_l4_technical_report_steps77_91.pdf`
"""
MD_OUT.write_text(md)

print(f"Saved Markdown: {MD_OUT}")
print(f"Saved PDF     : {PDF_OUT}")
