#!/usr/bin/env python3

import csv
import html
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "results/l4_repeated_run_statistics"
DOC_DIR = ROOT / "docs/l4/repeated_run_statistics"
PDF_DIR = ROOT / "results/l4_report_pdf"

OUT_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_JSON = OUT_DIR / "repeated_run_statistics_summary.json"
RUN_CSV = OUT_DIR / "repeated_run_media_observations.csv"
AGG_CSV = OUT_DIR / "repeated_run_aggregate_statistics.csv"
RESULT_MD = OUT_DIR / "repeated_run_statistics_summary.md"
DOC_MD = DOC_DIR / "L4_REPEATED_RUN_STATISTICS.md"
PDF = PDF_DIR / "zktrustllm_l4_repeated_run_statistics_steps96_107.pdf"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def load_json(path: Path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        return {}
    return {}


def nested_get(data, path, default=None):
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def extract_loss_pct(data):
    packet_loss = data.get("packetLoss", {}) if isinstance(data.get("packetLoss"), dict) else {}

    value = packet_loss.get("packet_loss_pct")
    if value is None:
        value = packet_loss.get("packetLossPct")
    if value is None:
        value = data.get("packetLossPct")

    if value is not None:
        return safe_float(value, 100.0)

    expected = packet_loss.get("expected_packets") or packet_loss.get("expectedPackets")
    lost = packet_loss.get("lost_packets") or packet_loss.get("lostPackets")

    if expected not in (None, 0, "0") and lost is not None:
        return (safe_float(lost) / safe_float(expected)) * 100.0

    return 100.0


def extract_jitter_ms(data):
    jitter = data.get("jitter", {}) if isinstance(data.get("jitter"), dict) else {}

    for key in ["avgJitterComponentMs", "avgJitterMs", "avg_jitter_ms"]:
        if key in jitter:
            return safe_float(jitter.get(key), 0.0)

    for key in ["avgJitterComponentMs", "avgJitterMs", "avg_jitter_ms"]:
        if key in data:
            return safe_float(data.get(key), 0.0)

    return 0.0


def extract_packets(data):
    for key in ["receivedPackets", "received_packets"]:
        if key in data:
            return safe_int(data.get(key), 0)

    packet_loss = data.get("packetLoss", {}) if isinstance(data.get("packetLoss"), dict) else {}
    return safe_int(packet_loss.get("received_packets") or packet_loss.get("receivedPackets"), 0)


def extract_bitrate(data):
    for key in ["avgBitrateKbps", "avg_bitrate_kbps"]:
        if key in data:
            return safe_float(data.get(key), 0.0)
    return 0.0


def pass_status(row):
    ok = (
        row["receivedPackets"] > 0
        and row["avgBitrateKbps"] > 0
        and row["packetLossPct"] <= 5.0
        and row["avgJitterMs"] <= 1000.0
    )
    return "PASS" if ok else "REVIEW"


def collect_step96_media_observations():
    base = ROOT / "results/l4_agentic_automation"
    rows = []

    for run_dir in sorted(base.glob("run_*")):
        if not run_dir.is_dir():
            continue

        run_id = run_dir.name.replace("run_", "")
        snapshot_dir = run_dir / "clean_media_snapshots"

        files = [
            ("plain_rtp", snapshot_dir / "clean_plain_rtp_media_summary.json"),
            ("dtls_rtp", snapshot_dir / "clean_dtls_rtp_media_summary.json"),
        ]

        for mode, path in files:
            data = load_json(path)
            exists = path.exists()

            row = {
                "runId": run_id,
                "mode": mode,
                "artifact": rel(path),
                "exists": exists,
                "receivedPackets": extract_packets(data) if exists else 0,
                "avgBitrateKbps": round(extract_bitrate(data), 6) if exists else 0.0,
                "packetLossPct": round(extract_loss_pct(data), 6) if exists else 100.0,
                "avgJitterMs": round(extract_jitter_ms(data), 6) if exists else 0.0,
            }
            row["status"] = pass_status(row) if exists else "MISSING"
            rows.append(row)

    return rows


def summarise_values(values):
    values = [safe_float(v) for v in values if v is not None]
    if not values:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "min": 0.0,
            "max": 0.0,
            "std": 0.0,
        }

    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "std": round(statistics.pstdev(values), 6) if len(values) > 1 else 0.0,
    }


def aggregate_rows(rows):
    grouped = defaultdict(list)

    for row in rows:
        grouped[row["mode"]].append(row)

    output = []

    for mode, items in sorted(grouped.items()):
        pass_count = sum(1 for r in items if r["status"] == "PASS")
        total = len(items)

        agg = {
            "mode": mode,
            "observationCount": total,
            "passCount": pass_count,
            "passRatePct": round((pass_count / total) * 100.0, 3) if total else 0.0,
        }

        for metric in ["receivedPackets", "avgBitrateKbps", "packetLossPct", "avgJitterMs"]:
            stats = summarise_values([r[metric] for r in items if r["status"] != "MISSING"])
            for key, value in stats.items():
                agg[f"{metric}_{key}"] = value

        output.append(agg)

    return output


def collect_chain_state():
    step96 = load_json(ROOT / "results/l4_agentic_automation/agentic_automation_summary.json")
    step97 = load_json(ROOT / "results/l4_closed_loop_agent/closed_loop_kpi_decision.json")
    step98 = load_json(ROOT / "results/l4_remediation_executor/remediation_execution_plan.json")
    step100 = load_json(ROOT / "results/l4_policy_scheduler/policy_scheduler_summary.json")
    step101 = load_json(ROOT / "results/l4_automation_audit_ledger/automation_audit_ledger.json")
    step102 = load_json(ROOT / "results/l4_audit_anchor/audit_ledger_anchor_record.json")
    step103 = load_json(ROOT / "results/l4_onchain_anchor/onchain_audit_anchor_result.json")
    step104 = load_json(ROOT / "results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.json")
    step105 = load_json(ROOT / "results/l4_policy_onchain_validation/policy_onchain_validation_summary.json")

    decision = step97.get("decision", {}) if isinstance(step97.get("decision"), dict) else {}

    return {
        "step96OverallStatus": step96.get("overallStatus", "UNKNOWN"),
        "step97Decision": decision.get("primaryAction", step97.get("primaryAction", "UNKNOWN")),
        "step98Status": step98.get("status", "UNKNOWN"),
        "step100Status": step100.get("overallStatus", "UNKNOWN"),
        "step101EntryCount": step101.get("entryCount", "UNKNOWN"),
        "step101FinalLedgerHash": step101.get("finalLedgerHash", "UNKNOWN"),
        "step102IpfsStatus": nested_get(step102, ["ipfs", "status"], "UNKNOWN"),
        "step102IpfsCid": nested_get(step102, ["ipfs", "cid"], "UNKNOWN"),
        "step103GasUsed": step103.get("gasUsed", "UNKNOWN"),
        "step104OverallStatus": step104.get("overallStatus", "UNKNOWN"),
        "step105OverallStatus": step105.get("overallStatus", "UNKNOWN"),
    }


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def build_markdown(summary):
    lines = [
        "# Step 108 L4 Repeated-Run Statistics",
        "",
        "## Purpose",
        "",
        "This step analyses repeated evidence from the Level 4 automation chain, especially Step 96 archived automation runs.",
        "",
        "It strengthens the scientific evaluation by showing whether clean RTP and DTLS-RTP telemetry remain stable across repeated agentic automation executions.",
        "",
        "## Summary",
        "",
        f"- Created at: `{summary['createdAt']}`",
        f"- Step 96 run directories found: `{summary['step96RunDirectoryCount']}`",
        f"- Media observations found: `{summary['mediaObservationCount']}`",
        f"- Overall repeated-run status: **{summary['overallStatus']}**",
        "",
        "## Current Closed-Loop Chain State",
        "",
        "| Component | Value |",
        "|---|---|",
    ]

    for key, value in summary["chainState"].items():
        lines.append(f"| {key} | `{value}` |")

    lines.extend([
        "",
        "## Aggregate Media Statistics",
        "",
        "| Mode | Observations | Pass rate % | Bitrate mean kbps | Loss mean % | Jitter mean ms |",
        "|---|---:|---:|---:|---:|---:|",
    ])

    for row in summary["aggregateStatistics"]:
        lines.append(
            f"| {row['mode']} | {row['observationCount']} | {row['passRatePct']} | "
            f"{row.get('avgBitrateKbps_mean', 0)} | {row.get('packetLossPct_mean', 0)} | "
            f"{row.get('avgJitterMs_mean', 0)} |"
        )

    lines.extend([
        "",
        "## Observation-Level Evidence",
        "",
        "| Run ID | Mode | Packets | Bitrate kbps | Loss % | Jitter ms | Status |",
        "|---|---|---:|---:|---:|---:|---|",
    ])

    for row in summary["mediaObservations"]:
        lines.append(
            f"| {row['runId']} | {row['mode']} | {row['receivedPackets']} | "
            f"{row['avgBitrateKbps']} | {row['packetLossPct']} | {row['avgJitterMs']} | {row['status']} |"
        )

    lines.extend([
        "",
        "## Research Meaning",
        "",
        "Step 108 provides repeatability evidence for the Level 4 automation workflow. The project has already demonstrated policy-gated execution, KPI decisioning, remediation, audit-ledger construction, IPFS anchoring, and on-chain validation. This step adds stability evidence by analysing repeated clean-media snapshots produced by prior automation runs.",
        "",
        "This is important for journal evaluation because it helps show that the automation pipeline is not a single successful demonstration, but a repeatable scientific workflow.",
        "",
        "## Boundary",
        "",
        "This step does not rerun experiments, use sudo, push code, deploy contracts, or modify prior evidence. It reads existing artifacts and produces repeated-run statistics.",
        "",
        "## Generated Files",
        "",
        f"- Summary JSON: `{rel(SUMMARY_JSON)}`",
        f"- Observation CSV: `{rel(RUN_CSV)}`",
        f"- Aggregate CSV: `{rel(AGG_CSV)}`",
        f"- Markdown: `{rel(DOC_MD)}`",
        f"- PDF: `{rel(PDF)}`",
    ])

    return "\n".join(lines) + "\n"


def esc(text):
    return html.escape(str(text)).replace("\n", "<br/>")


def para(text, style):
    return Paragraph(esc(text), style)


def write_pdf(summary):
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="RepeatTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=20,
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        name="RepeatHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="RepeatBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name="RepeatTableHead",
        parent=styles["BodyText"],
        fontSize=8,
        leading=9,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="RepeatTableCell",
        parent=styles["BodyText"],
        fontSize=7,
        leading=8,
    ))

    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="ZKTrustLLM L4 Repeated-Run Statistics",
    )

    story = []

    story.append(para("ZKTrustLLM-Agents L4 Repeated-Run Statistics", styles["RepeatTitle"]))
    story.append(para("Steps 96-107 Automation Stability Evidence", styles["RepeatBody"]))
    story.append(Spacer(1, 10))

    story.append(para("Purpose", styles["RepeatHeading"]))
    story.append(para(
        "This report analyses repeated Step 96 automation run artifacts and summarises the current Step 96-105 closed-loop automation state.",
        styles["RepeatBody"],
    ))

    story.append(para("Closed-Loop Chain State", styles["RepeatHeading"]))

    state_rows = [["Component", "Value"]]
    for key, value in summary["chainState"].items():
        state_rows.append([key, str(value)])

    state_table = Table(
        [[para(c, styles["RepeatTableHead"]) for c in state_rows[0]]] +
        [[para(c, styles["RepeatTableCell"]) for c in r] for r in state_rows[1:]],
        colWidths=[2.3 * inch, 4.7 * inch],
        repeatRows=1,
    )
    state_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(state_table)

    story.append(Spacer(1, 10))
    story.append(para("Aggregate Media Statistics", styles["RepeatHeading"]))

    agg_rows = [["Mode", "Obs.", "Pass %", "Bitrate mean", "Loss mean", "Jitter mean"]]
    for row in summary["aggregateStatistics"]:
        agg_rows.append([
            row["mode"],
            str(row["observationCount"]),
            str(row["passRatePct"]),
            str(row.get("avgBitrateKbps_mean", 0)),
            str(row.get("packetLossPct_mean", 0)),
            str(row.get("avgJitterMs_mean", 0)),
        ])

    agg_table = Table(
        [[para(c, styles["RepeatTableHead"]) for c in agg_rows[0]]] +
        [[para(c, styles["RepeatTableCell"]) for c in r] for r in agg_rows[1:]],
        colWidths=[1.1 * inch, 0.55 * inch, 0.75 * inch, 1.2 * inch, 1.0 * inch, 1.1 * inch],
        repeatRows=1,
    )
    agg_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(agg_table)

    story.append(PageBreak())
    story.append(para("Observation-Level Evidence", styles["RepeatHeading"]))

    obs_rows = [["Run ID", "Mode", "Packets", "Bitrate", "Loss", "Jitter", "Status"]]
    for row in summary["mediaObservations"]:
        obs_rows.append([
            row["runId"],
            row["mode"],
            str(row["receivedPackets"]),
            str(row["avgBitrateKbps"]),
            str(row["packetLossPct"]),
            str(row["avgJitterMs"]),
            row["status"],
        ])

    obs_table = Table(
        [[para(c, styles["RepeatTableHead"]) for c in obs_rows[0]]] +
        [[para(c, styles["RepeatTableCell"]) for c in r] for r in obs_rows[1:]],
        colWidths=[1.25 * inch, 0.9 * inch, 0.8 * inch, 0.9 * inch, 0.75 * inch, 0.85 * inch, 0.75 * inch],
        repeatRows=1,
    )
    obs_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(obs_table)

    story.append(Spacer(1, 10))
    story.append(para("Research Meaning", styles["RepeatHeading"]))
    story.append(para(
        "Step 108 strengthens the journal evaluation by adding repeatability evidence to the Level 4 policy-gated automation chain.",
        styles["RepeatBody"],
    ))

    doc.build(story)


def main():
    media_rows = collect_step96_media_observations()
    agg = aggregate_rows(media_rows)
    chain_state = collect_chain_state()

    run_ids = sorted({r["runId"] for r in media_rows})
    missing_count = sum(1 for r in media_rows if r["status"] == "MISSING")
    review_count = sum(1 for r in media_rows if r["status"] == "REVIEW")

    overall_status = "PASS"
    if missing_count:
        overall_status = "REVIEW_MISSING_OBSERVATIONS"
    if review_count:
        overall_status = "REVIEW_KPI_VARIATION"

    summary = {
        "experiment": "step108_repeated_run_statistics",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "step96RunDirectoryCount": len(run_ids),
        "mediaObservationCount": len(media_rows),
        "overallStatus": overall_status,
        "chainState": chain_state,
        "aggregateStatistics": agg,
        "mediaObservations": media_rows,
        "outputs": {
            "summaryJson": rel(SUMMARY_JSON),
            "observationCsv": rel(RUN_CSV),
            "aggregateCsv": rel(AGG_CSV),
            "summaryMarkdown": rel(RESULT_MD),
            "documentationMarkdown": rel(DOC_MD),
            "pdf": rel(PDF),
        },
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    write_csv(
        RUN_CSV,
        media_rows,
        [
            "runId",
            "mode",
            "artifact",
            "exists",
            "receivedPackets",
            "avgBitrateKbps",
            "packetLossPct",
            "avgJitterMs",
            "status",
        ],
    )

    agg_fieldnames = [
        "mode",
        "observationCount",
        "passCount",
        "passRatePct",
        "receivedPackets_count",
        "receivedPackets_mean",
        "receivedPackets_median",
        "receivedPackets_min",
        "receivedPackets_max",
        "receivedPackets_std",
        "avgBitrateKbps_count",
        "avgBitrateKbps_mean",
        "avgBitrateKbps_median",
        "avgBitrateKbps_min",
        "avgBitrateKbps_max",
        "avgBitrateKbps_std",
        "packetLossPct_count",
        "packetLossPct_mean",
        "packetLossPct_median",
        "packetLossPct_min",
        "packetLossPct_max",
        "packetLossPct_std",
        "avgJitterMs_count",
        "avgJitterMs_mean",
        "avgJitterMs_median",
        "avgJitterMs_min",
        "avgJitterMs_max",
        "avgJitterMs_std",
    ]

    write_csv(AGG_CSV, agg, agg_fieldnames)

    markdown = build_markdown(summary)
    RESULT_MD.write_text(markdown)
    DOC_MD.write_text(markdown)

    write_pdf(summary)

    print(json.dumps({
        "experiment": summary["experiment"],
        "overallStatus": summary["overallStatus"],
        "step96RunDirectoryCount": summary["step96RunDirectoryCount"],
        "mediaObservationCount": summary["mediaObservationCount"],
        "summaryJson": rel(SUMMARY_JSON),
        "summaryMarkdown": rel(RESULT_MD),
        "pdf": rel(PDF),
    }, indent=2))


if __name__ == "__main__":
    main()
