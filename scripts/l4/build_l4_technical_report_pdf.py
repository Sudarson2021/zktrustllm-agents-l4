#!/usr/bin/env python3

import html
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

PDF_OUT = OUT_DIR / "zktrustllm_l4_technical_report_steps77_87.pdf"
MD_OUT = DOC_DIR / "zktrustllm_l4_technical_report_steps77_87.md"


def load_json(path, default=None):
    path = ROOT / path
    if path.exists():
        return json.loads(path.read_text())
    return default if default is not None else {}


def esc(value):
    return html.escape(str(value))


def nested(data, *keys, default="N/A"):
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def pct(value):
    if value == "N/A" or value is None:
        return "N/A"
    return f"{value}%"


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.7 * inch, 0.45 * inch, "ZKTrustLLM-Agents L4 Technical Report")
    canvas.drawRightString(7.55 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def make_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TitleCenter",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=16,
    ))

    styles.add(ParagraphStyle(
        name="SubtitleCenter",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        leading=15,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name="Heading1Custom",
        parent=styles["Heading1"],
        fontSize=15,
        leading=19,
        spaceBefore=14,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="Heading2Custom",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="BodyCustom",
        parent=styles["BodyText"],
        fontSize=9.2,
        leading=12.5,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="SmallCustom",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="Caption",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#333333"),
        spaceBefore=4,
        spaceAfter=8,
    ))

    return styles


STYLES = make_styles()


def P(text, style="BodyCustom"):
    return Paragraph(esc(text), STYLES[style])


def PH(text, style="BodyCustom"):
    return Paragraph(text, STYLES[style])


def add_heading(story, text, level=1):
    story.append(P(text, "Heading1Custom" if level == 1 else "Heading2Custom"))


def paragraph(story, text):
    story.append(P(text, "BodyCustom"))


def add_table(story, title, headers, rows, col_widths=None):
    add_heading(story, title, level=2)

    data = []
    header_row = [PH(f"<b>{esc(h)}</b>", "SmallCustom") for h in headers]
    data.append(header_row)

    for row in rows:
        data.append([P(cell, "SmallCustom") for cell in row])

    if col_widths is None:
        usable_width = 7.0 * inch
        col_widths = [usable_width / len(headers)] * len(headers)

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EEF7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B7B7B7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))


def add_image(story, image_path, caption):
    path = ROOT / image_path
    if not path.exists():
        paragraph(story, f"Figure missing: {image_path}")
        return

    img = PILImage.open(path)
    width_px, height_px = img.size

    max_width = 6.6 * inch
    max_height = 4.2 * inch

    ratio = min(max_width / width_px, max_height / height_px)
    width = width_px * ratio
    height = height_px * ratio

    story.append(Image(str(path), width=width, height=height))
    story.append(P(caption, "Caption"))


def build_markdown():
    md = """# ZKTrustLLM-Agents Level 4 Technical Report

## Scope

This report documents the Level 4 workflow from Step 77 to Step 87.

The work aligns with the supervisor feedback that blockchain can act as authenticated shared state for Agentic AI, while A2A can simplify inter-agent communication through compact authenticated references and MCP can provide structured context access.

## Main Claim

Level 4 is defined as proof-governed multi-agent coordination over blockchain-authenticated shared state.

## Implemented Path

- Step 77: A2A reference-aware coordination
- Step 79: Proper MCP context server
- Step 80: MCP/A2A KPI analysis
- Step 81: AUTH_V2.3 reference-bound proof
- Step 82: Negative security tests
- Step 83: Network KPI telemetry-emulation
- Step 84: Journal-ready evaluation write-up
- Step 85: Benchmark result figures
- Step 86: Semi-live MCP/A2A control telemetry
- Step 87: Multi-agent scaling telemetry

## Key Results

- Step 86: L4-ref reduced semi-live control latency by 52.03% compared with L4 raw-context.
- Step 86: L4-ref reduced control-message size by 97.91% compared with L4 raw-context.
- Step 87: L4-ref reduced multi-agent latency by 52.40% to 58.50% compared with L4 raw-context.
- Step 87: L4-ref reduced multi-agent message size by 97.74% to 97.76% compared with L4 raw-context.

## Boundary

The current measurements are local blockchain/MCP/A2A control-plane measurements. They are not yet live VLC/DTLS/RTP media-plane measurements.
"""
    MD_OUT.write_text(md)


def build_pdf():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)

    a2a = load_json("results/l4_a2a_reference/a2a_reference_latest_decision.json")
    mcp = load_json("results/l4_mcp_server/mcp_tool_test_results.json")
    kpi = load_json("results/l4_mcp_a2a_kpi/kpi_summary.json")
    auth23 = load_json("results/l4_auth_v2_3/reference_bound_decision.json")
    auth_neg = load_json("results/l4_auth_v2_3_negative/auth_v2_3_negative_summary.json")
    mcp_neg = load_json("results/l4_mcp_a2a_security/mcp_a2a_negative_summary.json")
    net = load_json("results/l4_network_kpis/network_kpi_summary.json")
    semi = load_json("results/l4_live_telemetry/semi_live_control_summary.json")
    scale = load_json("results/l4_multi_agent_scaling/multi_agent_scaling_summary.json")

    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.65 * inch,
    )

    story = []

    story.append(PH("ZKTrustLLM-Agents Level 4 Technical Report", "TitleCenter"))
    story.append(PH("MCP/A2A Reference-Bound Proof-Governed Coordination over Blockchain-Authenticated Shared State", "SubtitleCenter"))
    story.append(PH("Prepared for journal write-up and supervisor review", "SubtitleCenter"))
    story.append(PH(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "SubtitleCenter"))
    story.append(Spacer(1, 16))

    add_heading(story, "Executive Summary")
    paragraph(story, "This technical report documents the Level 4 ZKTrustLLM-Agents workflow from Step 77 to Step 87. The work responds directly to the supervisor feedback that blockchain can serve as an authenticated record for network configurations, handover signalling, admission control, multimedia types, and agent decisions. It also addresses the idea that two Agentic AI agents can simplify message exchange by using short references to authenticated blockchain records rather than transmitting full raw context.")
    paragraph(story, "At Level 4, the system is framed as proof-governed multi-agent coordination over blockchain-authenticated shared state. A2A provides compact inter-agent reference exchange, MCP provides structured context and tool access, blockchain provides authenticated shared memory, and AUTH_V2.3 binds decisions to reference-aware coordination context through a zero-knowledge proof relation.")

    add_table(
        story,
        "Table 1: Level 4 Research Claim",
        ["Component", "Role in Level 4"],
        [
            ["Blockchain", "Authenticated shared state for decisions, references, and audit records."],
            ["A2A", "Compact inter-agent reference exchange."],
            ["MCP", "Structured context/tool access to authenticated blockchain state."],
            ["AUTH_V2.3", "Reference-bound proof relation for policy-admissible decisions."],
            ["Agent KPIs", "Measure coordination, retrieval, admissibility, rejection, and scalability."],
            ["Network KPIs", "Measure control overhead, latency, message size, jitter, and throughput."],
        ],
        [1.35 * inch, 5.65 * inch],
    )

    add_heading(story, "Supervisor Alignment")
    add_table(
        story,
        "Table 2: Mapping Supervisor Comments to Implemented Work",
        ["Supervisor Direction", "Implemented Alignment"],
        [
            ["Blockchain as authenticated record", "A2A references and AUTH_V2.2/AUTH_V2.3 decisions are anchored to blockchain state."],
            ["AI uses reliable blockchain information", "MCP server exposes blockchain-authenticated context to agents through structured tools."],
            ["Agentic AI creates new authenticated records", "AUTH_V2.3 creates a new proof-backed reference-bound decision record."],
            ["Agents exchange short references", "A2AReferenceRegistry stores compact references to authenticated decision records."],
            ["Detailed MCP/A2A analysis with KPIs", "Steps 80, 83, 86, and 87 produce agent KPIs, network KPIs, figures, and tables."],
        ],
        [2.3 * inch, 4.7 * inch],
    )

    add_heading(story, "Implementation Chronicle")
    add_table(
        story,
        "Table 3: Step-by-Step Research Workflow",
        ["Step", "Contribution", "Main Evidence"],
        [
            ["77", "A2A reference-aware coordination", "A2A registry, reference registration, decision ID binding."],
            ["79", "Proper MCP context server", "Read-only MCP tools over Level 4 blockchain state."],
            ["80", "MCP/A2A KPI analysis", "KPI summary JSON, CSV, Markdown."],
            ["81", "AUTH_V2.3 reference-bound proof", "Circuit, verifier, attestor, proof submission."],
            ["82", "Negative security tests", "Tampered inputs and invalid contexts rejected."],
            ["83", "Network KPI telemetry-emulation", "Deterministic control KPI comparison."],
            ["84", "Journal-ready write-up", "Evaluation section, result tables, limitations."],
            ["85", "Benchmark figures", "Figures 5.3 and 5.4."],
            ["86", "Semi-live control telemetry", "Measured local MCP/A2A timing over 20 runs."],
            ["87", "Multi-agent scaling telemetry", "Measured scaling across 5 to 25 agents."],
        ],
        [0.6 * inch, 2.4 * inch, 4.0 * inch],
    )

    add_heading(story, "Level 4 Architecture")
    paragraph(story, "The Level 4 architecture separates the system into four cooperating layers: authenticated blockchain state, reference-based A2A coordination, MCP context/tool resolution, and proof-governed decision admissibility. The central design decision is that agents do not need to exchange full raw evidence or decision payloads. Instead, they exchange compact references and resolve the underlying authenticated state through MCP.")
    add_table(
        story,
        "Table 4: Level 4 Execution Flow",
        ["Stage", "Description"],
        [
            ["S1", "Agent observes a trust or policy event."],
            ["S2", "AUTH_V2.2 or AUTH_V2.3 creates a proof-backed decision."],
            ["S3", "Decision is stored as blockchain-authenticated shared state."],
            ["S4", "A2A reference is registered and exchanged between agents."],
            ["S5", "Receiving agent uses MCP to resolve and verify the referenced context."],
            ["S6", "Action is accepted only if proof, policy, trust state, and reference bundle are valid."],
        ],
        [0.7 * inch, 6.3 * inch],
    )

    add_heading(story, "Implemented Artifacts")
    add_table(
        story,
        "Table 5: Main Artifact Map",
        ["Category", "Artifacts"],
        [
            ["A2A", "A2AReferenceRegistry, deployment scripts, reference registration outputs."],
            ["MCP", "mcp_l4/server.py, MCP tool test, MCP reference-bundle verification."],
            ["Proof", "circuits/auth_v2_3.zok, AuthV2_3Verifier.sol, DecisionAttestorAuthV2_3.sol."],
            ["Security", "AUTH_V2.3 negative tests, MCP/A2A invalid-context tests."],
            ["KPI", "Step 80 KPI summary, Step 83 network KPI summary, Step 86 semi-live telemetry, Step 87 scaling telemetry."],
            ["Figures", "Figures 5.3 to 5.9 across benchmark, semi-live, and multi-agent scaling results."],
        ],
        [1.2 * inch, 5.8 * inch],
    )

    add_heading(story, "Agent KPI Results")
    add_table(
        story,
        "Table 6: MCP and A2A Agent KPIs",
        ["KPI", "Measured Value"],
        [
            ["MCP tools listed", nested(mcp, "listedTools", default=[]) and str(len(mcp.get("listedTools", [])))],
            ["MCP successful calls", f"{mcp.get('successfulToolCalls', 'N/A')}/{mcp.get('toolCallCount', 'N/A')}"],
            ["MCP context retrieval success rate", mcp.get("mcpContextRetrievalSuccessRate", "N/A")],
            ["MCP average invocation latency ms", mcp.get("averageToolInvocationLatencyMs", "N/A")],
            ["MCP max invocation latency ms", mcp.get("maxToolInvocationLatencyMs", "N/A")],
            ["A2A reference valid", a2a.get("valid", "N/A")],
            ["A2A reference registration gas", a2a.get("gasUsed", "N/A")],
            ["KPI compression gain percent", nested(kpi, "message_size", "coordinationCompressionGainPercent")],
        ],
        [3.7 * inch, 3.3 * inch],
    )

    add_heading(story, "AUTH_V2.3 Reference-Bound Proof Result")
    add_table(
        story,
        "Table 7: AUTH_V2.3 Positive Path",
        ["Metric", "Value"],
        [
            ["Decision ID", auth23.get("decisionId", "N/A")],
            ["Verifier", auth23.get("authV2_3Groth16Verifier", "N/A")],
            ["Attestor", auth23.get("decisionAttestorAuthV2_3", "N/A")],
            ["Gas used", auth23.get("gasUsed", "N/A")],
            ["Proof output", auth23.get("proofOutput", "N/A")],
            ["Relation version", auth23.get("relationVersion", "N/A")],
            ["Trust state", auth23.get("trustState", "N/A")],
            ["Action class", auth23.get("actionClass", "N/A")],
        ],
        [2.2 * inch, 4.8 * inch],
    )

    add_heading(story, "Negative Security Results")
    add_table(
        story,
        "Table 8: Negative Security Test Results",
        ["Test Group", "Cases", "Passed", "Rejection Rate"],
        [
            [
                "AUTH_V2.3 tampered proof/public inputs",
                auth_neg.get("negativeCaseCount", "N/A"),
                auth_neg.get("negativeCasesPassed", "N/A"),
                auth_neg.get("unauthorizedOrTamperedRejectionRate", "N/A"),
            ],
            [
                "MCP/A2A invalid context",
                mcp_neg.get("negativeCaseCount", "N/A"),
                mcp_neg.get("negativeCasesPassed", "N/A"),
                mcp_neg.get("invalidContextRejectionRate", "N/A"),
            ],
        ],
        [2.6 * inch, 1.1 * inch, 1.1 * inch, 2.2 * inch],
    )

    add_heading(story, "Network KPI Telemetry-Emulation")
    net_rows = []
    for scenario, values in net.get("scenarioSummary", {}).items():
        net_rows.append([
            scenario,
            values.get("controlMessageBytes", "N/A"),
            values.get("avgControlResponseTimeMs", "N/A"),
            values.get("avgJitterDuringControlEventMs", "N/A"),
            values.get("avgPacketLossDuringOrchestrationPct", "N/A"),
            values.get("referenceBound", "N/A"),
        ])
    add_table(
        story,
        "Table 9: Step 83 Network KPI Scenario Summary",
        ["Scenario", "Bytes", "Response ms", "Jitter ms", "Loss %", "Reference-bound"],
        net_rows,
        [1.7 * inch, 0.8 * inch, 1.1 * inch, 1.0 * inch, 0.8 * inch, 1.6 * inch],
    )

    add_heading(story, "Semi-Live Control-Plane Telemetry")
    semi_rows = []
    for mode, values in semi.get("summary", {}).items():
        if mode == "comparison":
            continue
        semi_rows.append([
            mode,
            values.get("runs", "N/A"),
            values.get("successRate", "N/A"),
            values.get("avgControlResponseMs", "N/A"),
            values.get("p95ControlResponseMs", "N/A"),
            values.get("jitterStdMs", "N/A"),
            values.get("avgControlMessageBytes", "N/A"),
        ])
    add_table(
        story,
        "Table 10: Step 86 Semi-Live Control-Plane Results",
        ["Mode", "Runs", "Success", "Avg ms", "P95 ms", "Jitter", "Avg bytes"],
        semi_rows,
        [1.7 * inch, 0.6 * inch, 0.8 * inch, 0.9 * inch, 0.9 * inch, 0.8 * inch, 1.3 * inch],
    )

    semi_comp = semi.get("summary", {}).get("comparison", {})
    add_table(
        story,
        "Table 11: Step 86 L4-ref Improvement",
        ["Metric", "Value"],
        [
            ["L4-ref latency reduction vs raw-context", pct(semi_comp.get("l4RefLatencyReductionVsRawPct", "N/A"))],
            ["L4-ref message reduction vs raw-context", pct(semi_comp.get("l4RefMessageReductionVsRawPct", "N/A"))],
        ],
        [4.5 * inch, 2.5 * inch],
    )

    add_heading(story, "Multi-Agent Scaling Telemetry")
    scale_rows = []
    comparisons = scale.get("summary", {}).get("comparisons", {})
    for agent_label, values in comparisons.items():
        scale_rows.append([
            agent_label.replace("_agents", ""),
            pct(values.get("l4RefLatencyReductionVsRawPct", "N/A")),
            pct(values.get("l4RefMessageReductionVsRawPct", "N/A")),
            pct(values.get("l4RefThroughputGainVsRawPct", "N/A")),
        ])
    add_table(
        story,
        "Table 12: Step 87 Multi-Agent Scaling Improvement",
        ["Agents", "Latency Reduction", "Message Reduction", "Throughput Gain"],
        scale_rows,
        [1.0 * inch, 2.0 * inch, 2.0 * inch, 2.0 * inch],
    )

    add_heading(story, "Result Figures")
    paragraph(story, "Figures 5.3 to 5.9 consolidate benchmark, semi-live, and multi-agent scaling evidence. The benchmark figures support supervisor-facing communication. The semi-live and multi-agent figures provide measured local control-plane evidence for the Level 4 approach.")
    story.append(PageBreak())

    add_heading(story, "Figure Set: Benchmark and Telemetry Results")
    add_image(story, "results/l4_benchmark_figures/figure_5_3_agent_scaling_latency.png", "Figure 5.3: Agent scaling latency benchmark.")
    add_image(story, "results/l4_benchmark_figures/figure_5_4_decision_utility_positions.png", "Figure 5.4: Decision utility across agent positions.")
    add_image(story, "results/l4_live_telemetry/figure_5_5_semi_live_control_latency.png", "Figure 5.5: Semi-live control-plane latency.")
    add_image(story, "results/l4_live_telemetry/figure_5_6_semi_live_control_summary.png", "Figure 5.6: Semi-live control-plane summary.")
    add_image(story, "results/l4_multi_agent_scaling/figure_5_7_multi_agent_scaling_latency.png", "Figure 5.7: Multi-agent scaling latency.")
    add_image(story, "results/l4_multi_agent_scaling/figure_5_8_multi_agent_control_bytes.png", "Figure 5.8: Multi-agent control-message size.")
    add_image(story, "results/l4_multi_agent_scaling/figure_5_9_multi_agent_throughput.png", "Figure 5.9: Multi-agent coordination throughput.")

    story.append(PageBreak())
    add_heading(story, "Discussion")
    paragraph(story, "The results show that L4-ref MCP/A2A coordination provides a measurable reduction in inter-agent message size and improves coordination latency compared with raw-context exchange. Step 86 shows that the compact reference path reduces semi-live control response latency by 52.03% and message size by 97.91% compared with L4 raw-context. Step 87 extends this observation across 5 to 25 agents, where L4-ref reduces latency by 52.40% to 58.50% and message size by approximately 97.74% to 97.76%.")
    paragraph(story, "These results strengthen the central claim that blockchain-authenticated shared state can simplify multi-agent coordination. Rather than exchanging full raw evidence or policy context, agents exchange compact references and retrieve authenticated context through MCP. The proof-governed layer ensures that only admissible and reference-bound decisions are accepted.")

    add_heading(story, "Limitations")
    add_table(
        story,
        "Table 13: Current Limitations",
        ["Limitation", "Meaning"],
        [
            ["Localhost blockchain", "The current experiment uses Hardhat localhost and does not yet represent production chain latency."],
            ["Semi-live control-plane only", "Step 86 and Step 87 measure local MCP/A2A control-plane timing, not live media-plane traffic."],
            ["No live VLC/DTLS/RTP yet", "Packet loss, jitter, frame continuity, and media interruption must be measured in a future live test."],
            ["Bounded proof relation", "AUTH_V2.3 currently demonstrates a bounded trust-state/action relation."],
            ["Small-scale agent counts", "Scaling is evaluated up to 25 agents; larger workloads should be evaluated next."],
        ],
        [2.2 * inch, 4.8 * inch],
    )

    add_heading(story, "Recommended Next Steps")
    add_table(
        story,
        "Table 14: Future Work Roadmap",
        ["Next Step", "Purpose"],
        [
            ["Live DTLS/RTP/VLC validation", "Measure real media-plane jitter, loss, interruption, and recovery."],
            ["Network emulation", "Use tc/netem to introduce delay, jitter, and packet loss."],
            ["Policy generalisation", "Extend AUTH_V2.3 beyond Restricted -> Isolate to multiple trust states and actions."],
            ["Batch/aggregate proofs", "Reduce proof overhead for larger multi-agent workloads."],
            ["Journal paper integration", "Convert this report into the evaluation, implementation, and results sections."],
        ],
        [2.4 * inch, 4.6 * inch],
    )

    add_heading(story, "Conclusion")
    paragraph(story, "The Level 4 workflow demonstrates a state-of-the-art direction for proof-governed Agentic AI coordination over blockchain-authenticated shared state. The implemented A2A reference model, MCP context server, AUTH_V2.3 reference-bound proof, negative-security tests, KPI analysis, and measured scaling telemetry together provide a coherent research foundation for a journal-level extension of ZKTrustLLM-Agents.")

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


def main():
    build_markdown()
    build_pdf()
    print(f"Saved Markdown: {MD_OUT}")
    print(f"Saved PDF     : {PDF_OUT}")


if __name__ == "__main__":
    main()
