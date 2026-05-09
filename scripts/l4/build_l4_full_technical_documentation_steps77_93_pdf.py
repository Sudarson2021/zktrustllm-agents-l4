#!/usr/bin/env python3

import csv
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

OUT_PDF = ROOT / "results" / "l4_report_pdf" / "zktrustllm_l4_full_technical_documentation_steps77_93.pdf"
OUT_MD = ROOT / "docs" / "report" / "zktrustllm_l4_full_technical_documentation_steps77_93.md"

OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=18,
    leading=22,
    spaceAfter=12,
)

SUBTITLE = ParagraphStyle(
    "SubtitleCustom",
    parent=styles["Normal"],
    alignment=TA_CENTER,
    fontSize=10,
    leading=13,
    textColor=colors.HexColor("#444444"),
    spaceAfter=18,
)

H1 = ParagraphStyle(
    "H1Custom",
    parent=styles["Heading1"],
    fontSize=14,
    leading=18,
    spaceBefore=10,
    spaceAfter=8,
)

H2 = ParagraphStyle(
    "H2Custom",
    parent=styles["Heading2"],
    fontSize=11,
    leading=14,
    spaceBefore=8,
    spaceAfter=6,
)

BODY = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontSize=9,
    leading=12,
    alignment=TA_JUSTIFY,
    spaceAfter=6,
)

SMALL = ParagraphStyle(
    "SmallCustom",
    parent=styles["BodyText"],
    fontSize=7,
    leading=9,
    spaceAfter=4,
)

TABLE_TEXT = ParagraphStyle(
    "TableText",
    parent=styles["BodyText"],
    fontSize=7,
    leading=8,
)

TABLE_HEAD = ParagraphStyle(
    "TableHead",
    parent=styles["BodyText"],
    fontSize=7,
    leading=8,
    textColor=colors.white,
)


def esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def read_json(path):
    path = ROOT / path
    if not path.exists():
        return None
    return json.loads(path.read_text())


def p(text):
    return Paragraph(esc(text), BODY)


def h1(text):
    return Paragraph(esc(text), H1)


def h2(text):
    return Paragraph(esc(text), H2)


def small(text):
    return Paragraph(esc(text), SMALL)


def table(rows, col_widths=None):
    data = []
    for r, row in enumerate(rows):
        style = TABLE_HEAD if r == 0 else TABLE_TEXT
        data.append([Paragraph(esc(cell), style) for cell in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#999999")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def add_image(story, rel_path, caption, max_w=6.4 * inch, max_h=3.2 * inch):
    path = ROOT / rel_path
    if not path.exists():
        story.append(small(f"Figure missing: {rel_path}"))
        return

    with PILImage.open(path) as im:
        w, h = im.size

    scale = min(max_w / w, max_h / h)
    img = Image(str(path), width=w * scale, height=h * scale)
    story.append(img)
    story.append(small(caption))
    story.append(Spacer(1, 8))


def md_table(rows):
    if not rows:
        return ""
    out = []
    out.append("| " + " | ".join(rows[0]) + " |")
    out.append("|" + "|".join(["---"] * len(rows[0])) + "|")
    for row in rows[1:]:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(out)


def load_csv_rows(rel_path, limit=None):
    path = ROOT / rel_path
    if not path.exists():
        return []
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    return rows if limit is None else rows[:limit]


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def make_doc():
    story = []
    md = []

    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    story.append(Paragraph("ZKTrustLLM-Agents Level 4 Technical Documentation", TITLE))
    story.append(
        Paragraph(
            "Steps 77-93: proof-governed MCP/A2A coordination, live RTP media telemetry, DTLS-wrapped RTP validation, impairment testing, and namespace-based media-plane evaluation",
            SUBTITLE,
        )
    )
    story.append(Paragraph(f"Generated: {generated}", SUBTITLE))
    story.append(Spacer(1, 12))

    md.append("# ZKTrustLLM-Agents Level 4 Technical Documentation")
    md.append("")
    md.append(f"Generated: {generated}")
    md.append("")
    md.append("Coverage: Steps 77-93.")

    story.append(h1("1. Executive Summary"))
    summary_text = (
        "This report documents the Level 4 ZKTrustLLM-Agents project progress. "
        "The work has evolved from proof-governed MCP/A2A agent coordination into live media-plane validation. "
        "The project now contains measured evidence for semi-live MCP/A2A control-plane latency, multi-agent scaling, plain RTP media delivery, DTLS-wrapped RTP protection, loopback impairment, and Linux network namespace impairment. "
        "The result is a stronger research foundation for supervisor review and future journal-level evaluation."
    )
    story.append(p(summary_text))
    md.append("## 1. Executive Summary")
    md.append(summary_text)

    story.append(h1("2. Research Architecture"))
    arch_rows = [
        ["Plane", "Role", "Implemented Evidence"],
        [
            "Media plane",
            "Carries RTP/H.264 traffic and measures packet delivery behaviour.",
            "Step 89 plain RTP, Step 90 DTLS-wrapped RTP, Step 91 loopback impairment, Step 93 namespace impairment.",
        ],
        [
            "Control plane",
            "Runs MCP/A2A coordination and compact reference exchange between agents.",
            "Step 86 semi-live MCP/A2A timings and Step 87 multi-agent scaling.",
        ],
        [
            "Trust plane",
            "Uses blockchain-authenticated state, reference-bound decisions, and proof-governed policy admissibility.",
            "AUTH_V2.3, reference bundle verification, negative-security rejection, and policy binding.",
        ],
        [
            "Evidence plane",
            "Keeps reproducible artifacts, CSV logs, JSON summaries, figures, and report material.",
            "ARTIFACTS.md, results folders, paper tables, report PDFs, and generated figures.",
        ],
    ]
    story.append(table(arch_rows, [1.0 * inch, 2.25 * inch, 3.0 * inch]))
    md.append("\n## 2. Research Architecture\n")
    md.append(md_table(arch_rows))

    story.append(h1("3. Step-by-Step Project Progress"))
    step_rows = [
        ["Step", "Main Contribution", "Research Meaning"],
        ["77", "A2A reference-aware coordination", "Introduced compact inter-agent reference exchange."],
        ["79", "Proper MCP Level 4 context server", "Structured tool access to authenticated blockchain state."],
        ["80", "MCP/A2A KPI analysis", "Defined measurable control-plane KPIs."],
        ["81", "AUTH_V2.3 reference-bound proof", "Bound proof-governed decisions to references and policy context."],
        ["82", "Negative-security tests", "Validated rejection of invalid policy or reference states."],
        ["83", "Network KPI telemetry emulation", "Created deterministic network KPI baseline."],
        ["84", "Journal evaluation write-up", "Converted prototype outputs into paper-ready evaluation material."],
        ["85", "Benchmark result figures", "Added visual result figures for agent scaling and utility."],
        ["86", "Semi-live MCP/A2A control telemetry", "Measured actual local MCP/A2A control-loop timings."],
        ["87", "Multi-agent scaling telemetry", "Measured performance as agent count increased from 5 to 25."],
        ["88", "Technical report PDF through Step 87", "Produced supervisor-ready progress report."],
        ["89", "Live RTP media-plane telemetry", "Measured actual RTP packets, bitrate, jitter, and loss."],
        ["90", "DTLS-wrapped RTP validation", "Added secured RTP tunnel/proxy validation."],
        ["91", "Loopback network impairment", "Compared plain RTP vs DTLS-RTP under tc netem impairment."],
        ["92", "Technical report through Step 91", "Updated report to include media-plane validation."],
        ["93", "Linux network namespace impairment", "Reproduced impairment matrix using two isolated network stacks."],
    ]
    story.append(table(step_rows, [0.55 * inch, 2.35 * inch, 3.35 * inch]))
    md.append("\n## 3. Step-by-Step Project Progress\n")
    md.append(md_table(step_rows))

    story.append(PageBreak())

    story.append(h1("4. Key Measured Results"))

    story.append(h2("4.1 Step 86 Semi-Live MCP/A2A Control-Plane Telemetry"))
    step86_rows = [
        ["Metric", "Result"],
        ["L4 raw-context average control response", "72.793 ms"],
        ["L4-ref MCP/A2A average control response", "34.918 ms"],
        ["L4-ref latency reduction vs raw-context", "52.03%"],
        ["L4-ref control-message reduction vs raw-context", "97.91%"],
        ["Interpretation", "Compact reference exchange reduces control latency and message size while preserving proof-governed verification."],
    ]
    story.append(table(step86_rows, [2.6 * inch, 3.6 * inch]))
    md.append("\n### 4.1 Step 86 Semi-Live MCP/A2A Control-Plane Telemetry\n")
    md.append(md_table(step86_rows))

    story.append(h2("4.2 Step 87 Multi-Agent Scaling"))
    step87_rows = [
        ["Agents", "Latency reduction vs raw", "Message reduction vs raw", "Throughput gain vs raw"],
        ["5", "53.14%", "97.75%", "113.51%"],
        ["10", "53.67%", "97.76%", "116.03%"],
        ["15", "58.50%", "97.75%", "139.83%"],
        ["20", "54.69%", "97.74%", "120.75%"],
        ["25", "52.40%", "97.74%", "110.02%"],
    ]
    story.append(table(step87_rows, [0.8 * inch, 1.75 * inch, 1.75 * inch, 1.75 * inch]))
    md.append("\n### 4.2 Step 87 Multi-Agent Scaling\n")
    md.append(md_table(step87_rows))

    story.append(h2("4.3 Step 89 Live Plain RTP Media-Plane Baseline"))
    step89 = read_json("results/l4_live_rtp_media/rtp_media_summary.json")
    if step89:
        loss = step89.get("packetLoss", {})
        jitter = step89.get("jitter", {})
        step89_rows = [
            ["KPI", "Result"],
            ["Received packets", fmt(step89.get("receivedPackets"))],
            ["Average bitrate kbps", fmt(step89.get("avgBitrateKbps"))],
            ["Packet loss %", fmt(loss.get("packet_loss_pct"))],
            ["Average jitter ms", fmt(jitter.get("avgJitterComponentMs"))],
            ["P50 jitter ms", fmt(jitter.get("p50JitterComponentMs"))],
            ["Max jitter ms", fmt(jitter.get("maxJitterComponentMs"))],
        ]
    else:
        step89_rows = [["KPI", "Result"], ["Step 89 summary", "Missing JSON summary"]]
    story.append(table(step89_rows, [2.5 * inch, 3.0 * inch]))
    md.append("\n### 4.3 Step 89 Live Plain RTP Media-Plane Baseline\n")
    md.append(md_table(step89_rows))

    story.append(h2("4.4 Step 90 DTLS-Wrapped RTP Media-Plane Validation"))
    step90 = read_json("results/l4_dtls_rtp_media/dtls_rtp_media_summary.json")
    if step90:
        loss = step90.get("packetLoss", {})
        jitter = step90.get("jitter", {})
        step90_rows = [
            ["KPI", "Result"],
            ["Recovered RTP packets", fmt(step90.get("receivedPackets"))],
            ["Average bitrate kbps", fmt(step90.get("avgBitrateKbps"))],
            ["Packet loss %", fmt(loss.get("packet_loss_pct"))],
            ["Average arrival-gap jitter ms", fmt(jitter.get("avgJitterComponentMs"))],
            ["P50 jitter ms", fmt(jitter.get("p50JitterComponentMs"))],
            ["Max jitter ms", fmt(jitter.get("maxJitterComponentMs"))],
        ]
    else:
        step90_rows = [["KPI", "Result"], ["Step 90 summary", "Missing JSON summary"]]
    story.append(table(step90_rows, [2.5 * inch, 3.0 * inch]))
    md.append("\n### 4.4 Step 90 DTLS-Wrapped RTP Media-Plane Validation\n")
    md.append(md_table(step90_rows))

    story.append(PageBreak())

    story.append(h2("4.5 Step 91 Loopback Network Impairment"))
    step91 = read_json("results/l4_network_impairment/network_impairment_summary.json")
    if step91:
        rows = [["Profile", "Mode", "Packets", "Loss %", "Bitrate kbps", "Avg jitter ms", "P95 jitter ms"]]
        for r in step91.get("rows", []):
            rows.append(
                [
                    r.get("profile", ""),
                    r.get("mode", ""),
                    fmt(r.get("receivedPackets")),
                    fmt(r.get("packetLossPct")),
                    fmt(r.get("avgBitrateKbps")),
                    fmt(r.get("avgJitterMs")),
                    fmt(r.get("p95JitterMs")),
                ]
            )
    else:
        rows = [["Profile", "Mode", "Packets", "Loss %", "Bitrate kbps", "Avg jitter ms", "P95 jitter ms"], ["Missing", "Missing", "", "", "", "", ""]]
    story.append(table(rows, [1.2 * inch, 1.25 * inch, 0.65 * inch, 0.7 * inch, 0.9 * inch, 0.85 * inch, 0.85 * inch]))
    md.append("\n### 4.5 Step 91 Loopback Network Impairment\n")
    md.append(md_table(rows))

    story.append(h2("4.6 Step 93 Linux Network Namespace Impairment"))
    step93 = read_json("results/l4_namespace_impairment/namespace_impairment_summary.json")
    if step93:
        rows = [["Profile", "Mode", "Packets", "Loss %", "Bitrate kbps", "Avg jitter ms", "P95 jitter ms"]]
        for r in step93.get("rows", []):
            rows.append(
                [
                    r.get("profile", ""),
                    r.get("mode", ""),
                    fmt(r.get("receivedPackets")),
                    fmt(r.get("packetLossPct")),
                    fmt(r.get("avgBitrateKbps")),
                    fmt(r.get("avgJitterMs")),
                    fmt(r.get("p95JitterMs")),
                ]
            )
    else:
        rows = [["Profile", "Mode", "Packets", "Loss %", "Bitrate kbps", "Avg jitter ms", "P95 jitter ms"], ["Missing", "Missing", "", "", "", "", ""]]
    story.append(table(rows, [1.2 * inch, 1.25 * inch, 0.65 * inch, 0.7 * inch, 0.9 * inch, 0.85 * inch, 0.85 * inch]))
    md.append("\n### 4.6 Step 93 Linux Network Namespace Impairment\n")
    md.append(md_table(rows))

    story.append(PageBreak())

    story.append(h1("5. Result Figures"))
    figure_items = [
        ("results/l4_multi_agent_scaling/figure_5_7_multi_agent_scaling_latency.png", "Figure 5.7 - Multi-agent coordination latency."),
        ("results/l4_multi_agent_scaling/figure_5_8_multi_agent_control_bytes.png", "Figure 5.8 - Multi-agent control message bytes."),
        ("results/l4_multi_agent_scaling/figure_5_9_multi_agent_throughput.png", "Figure 5.9 - Multi-agent throughput."),
        ("results/l4_live_rtp_media/figure_5_10_live_rtp_jitter.png", "Figure 5.10 - Live RTP jitter."),
        ("results/l4_live_rtp_media/figure_5_11_live_rtp_bitrate.png", "Figure 5.11 - Live RTP bitrate."),
        ("results/l4_dtls_rtp_media/figure_5_14_plain_vs_dtls_packet_loss.png", "Figure 5.14 - Plain RTP vs DTLS-RTP packet loss."),
        ("results/l4_dtls_rtp_media/figure_5_15_plain_vs_dtls_bitrate.png", "Figure 5.15 - Plain RTP vs DTLS-RTP bitrate."),
        ("results/l4_network_impairment/figure_5_16_plain_vs_dtls_impairment_packet_loss.png", "Figure 5.16 - Loopback impairment packet loss."),
        ("results/l4_network_impairment/figure_5_17_plain_vs_dtls_impairment_bitrate.png", "Figure 5.17 - Loopback impairment bitrate."),
        ("results/l4_network_impairment/figure_5_18_plain_vs_dtls_impairment_jitter.png", "Figure 5.18 - Loopback impairment arrival-gap jitter."),
        ("results/l4_namespace_impairment/figure_5_19_namespace_packet_loss.png", "Figure 5.19 - Namespace packet loss."),
        ("results/l4_namespace_impairment/figure_5_20_namespace_bitrate.png", "Figure 5.20 - Namespace bitrate."),
        ("results/l4_namespace_impairment/figure_5_21_namespace_arrival_gap_jitter.png", "Figure 5.21 - Namespace arrival-gap jitter."),
    ]

    for idx, (path, caption) in enumerate(figure_items):
        add_image(story, path, caption)
        if idx in {3, 7, 10}:
            story.append(PageBreak())

    story.append(h1("6. Supervisor Feedback Alignment"))
    feedback_rows = [
        ["Supervisor/Research Need", "Implemented Response", "Evidence"],
        [
            "Move beyond deterministic emulation.",
            "Added semi-live MCP/A2A timings and live media-plane telemetry.",
            "Steps 86, 89.",
        ],
        [
            "Evaluate MCP/A2A at Level 4.",
            "Measured compact reference coordination against raw-context coordination.",
            "Steps 86 and 87.",
        ],
        [
            "Connect control-plane work with media-plane behaviour.",
            "Added RTP packet capture, packet loss, jitter, and bitrate metrics.",
            "Steps 89 and 90.",
        ],
        [
            "Add secured media validation.",
            "Built DTLS-wrapped RTP tunnel/proxy and measured recovered RTP.",
            "Step 90.",
        ],
        [
            "Evaluate under network stress.",
            "Used Linux tc netem for delay, jitter, and packet-loss impairment.",
            "Step 91.",
        ],
        [
            "Improve realism beyond localhost.",
            "Reproduced impairment matrix using two Linux network namespaces and veth.",
            "Step 93.",
        ],
        [
            "Prepare journal-ready evaluation.",
            "Generated result tables, figures, reports, and artifact mappings.",
            "Steps 84, 88, 92, 94.",
        ],
    ]
    story.append(table(feedback_rows, [1.6 * inch, 2.35 * inch, 2.25 * inch]))
    md.append("\n## 6. Supervisor Feedback Alignment\n")
    md.append(md_table(feedback_rows))

    story.append(h1("7. Artifact Map"))
    artifact_rows = [
        ["Category", "Main Paths"],
        ["Control telemetry", "results/l4_live_telemetry/"],
        ["Multi-agent scaling", "results/l4_multi_agent_scaling/"],
        ["Plain RTP media", "results/l4_live_rtp_media/"],
        ["DTLS-RTP media", "results/l4_dtls_rtp_media/"],
        ["Loopback impairment", "results/l4_network_impairment/"],
        ["Namespace impairment", "results/l4_namespace_impairment/"],
        ["Technical reports", "results/l4_report_pdf/ and docs/report/"],
        ["Paper write-up", "docs/paper/l4_mcp_a2a_evaluation_section.md and docs/paper/l4_results_tables.md"],
        ["Artifact register", "ARTIFACTS.md"],
    ]
    story.append(table(artifact_rows, [1.7 * inch, 4.5 * inch]))
    md.append("\n## 7. Artifact Map\n")
    md.append(md_table(artifact_rows))

    story.append(PageBreak())

    story.append(h1("8. Agentic AI Automation Roadmap From Here"))
    roadmap_rows = [
        ["Next Step", "Goal", "Expected Output"],
        [
            "Step 95",
            "Closed-loop policy-to-media experiment.",
            "Trigger media impairment response from MCP/A2A policy output.",
        ],
        [
            "Step 96",
            "Agentic AI control automation.",
            "Automated agent reads telemetry, selects policy action, and logs decision.",
        ],
        [
            "Step 97",
            "Supervisor feedback tracker.",
            "Machine-readable feedback register linking comments to implementation evidence.",
        ],
        [
            "Step 98",
            "Two-machine or testbed validation.",
            "Repeat namespace results across two physical devices or 5GIC/6GIC testbed.",
        ],
        [
            "Step 99",
            "Paper-ready result consolidation.",
            "Clean tables, final figures, limitations, and journal evaluation section.",
        ],
        [
            "Step 100",
            "Agentic L4 journal prototype.",
            "Multi-agent L4 workflow with MCP/A2A, ZK proof governance, and secured media-plane response.",
        ],
    ]
    story.append(table(roadmap_rows, [0.8 * inch, 2.3 * inch, 3.1 * inch]))
    md.append("\n## 8. Agentic AI Automation Roadmap From Here\n")
    md.append(md_table(roadmap_rows))

    story.append(h1("9. Current Research Claim"))
    claim = (
        "The Level 4 prototype demonstrates that proof-governed agentic coordination can combine MCP-based access to authenticated state, A2A compact reference exchange, reference-bound proof semantics, and secured RTP media-plane telemetry. "
        "The evaluation now includes control-plane latency, multi-agent scaling, live RTP delivery, DTLS-wrapped RTP protection, controlled impairment, and namespace-separated media paths."
    )
    story.append(p(claim))
    md.append("\n## 9. Current Research Claim\n")
    md.append(claim)

    story.append(h1("10. Recommended Supervisor Discussion Points"))
    discussion_rows = [
        ["Topic", "Suggested Discussion"],
        ["Novelty", "Emphasize compact reference-based MCP/A2A coordination linked to secured media-plane validation."],
        ["Evaluation strength", "Show progression from deterministic telemetry to semi-live, live RTP, DTLS-RTP, impairment, and namespaces."],
        ["Limitations", "Current tests are single-machine; next validation should use two machines, Mininet, ns-3, or testbed."],
        ["Journal direction", "Position Step 95 onward as agentic closed-loop media control under proof-governed trust decisions."],
        ["Figures", "Use Step 87, Step 91, and Step 93 figures as core evaluation visuals."],
    ]
    story.append(table(discussion_rows, [1.5 * inch, 4.7 * inch]))
    md.append("\n## 10. Recommended Supervisor Discussion Points\n")
    md.append(md_table(discussion_rows))

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="ZKTrustLLM-Agents L4 Technical Documentation Steps 77-93",
    )

    doc.build(story)

    OUT_MD.write_text("\n\n".join(md) + "\n")

    print(f"Saved Markdown: {OUT_MD}")
    print(f"Saved PDF     : {OUT_PDF}")


if __name__ == "__main__":
    make_doc()
