#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path(".").resolve()
CSV = ROOT / "docs" / "l4" / "supervisor_258" / "results" / "n8n_all_runs_240runs_duration.csv"
OUT = ROOT / "docs" / "l4" / "supervisor_258" / "results" / "stage2_kpi_completeness_report.md"

TARGETS = [
    "prover_time_ms",
    "anchor_gas",
    "rtp_jitter_ms",
    "rtp_loss_pct",
    "dtls_rtp_jitter_ms",
    "dtls_rtp_loss_pct",
    "reason_latency_ms",
    "replay_rejected",
    "zero_anchor_rejected",
    "unauthorized_submitter_rejected",
    "post_auto_score_gas",
    "hardhat_passing_tests",
    "hardhat_failing_tests",
]

with CSV.open() as f:
    rows = list(csv.DictReader(f))

lines = []
lines.append("# Stage 2 KPI Completeness Report")
lines.append("")
lines.append(f"Total clean records: {len(rows)}")
lines.append("")
lines.append("| KPI | Non-null records | Coverage | Interpretation |")
lines.append("|---|---:|---:|---|")

for key in TARGETS:
    count = sum(1 for r in rows if r.get(key) not in ("", "None", None))
    pct = (count / len(rows) * 100.0) if rows else 0.0

    if key in {"rtp_jitter_ms", "rtp_loss_pct", "dtls_rtp_jitter_ms", "dtls_rtp_loss_pct"}:
        interpretation = "Configured impairment-profile KPI; replace later with packet-capture evidence."
    elif key == "unauthorized_submitter_rejected":
        interpretation = "Populated for RBAC-only runs where the current-API test confirms non-oracle rejection."
    elif key in {"prover_time_ms"}:
        interpretation = "Populated for ablation rows where prover is intentionally not invoked; direct prover logs still needed for full ZK rows."
    elif key in {"anchor_gas", "reason_latency_ms", "replay_rejected", "zero_anchor_rejected"}:
        interpretation = "Missing until direct runtime hooks or negative-security logs are added."
    elif key in {"post_auto_score_gas", "hardhat_passing_tests", "hardhat_failing_tests"}:
        interpretation = "Extracted from Hardhat logs where available."
    else:
        interpretation = "Derived from available run evidence."

    lines.append(f"| {key} | {count}/{len(rows)} | {pct:.2f}% | {interpretation} |")

lines.append("")
lines.append("## Scientific interpretation")
lines.append("")
lines.append("The Stage 2 extraction layer extends the n8n workflow-validation dataset into a scientific KPI-tracking dataset. It currently provides complete configured media impairment coverage, Hardhat gas/test KPIs, and RBAC unauthorized-submitter rejection evidence. Missing values are intentionally preserved for KPIs that require direct runtime hooks, including anchor gas, reasoning latency, replay rejection, zero-anchor rejection, and full ZK prover timing.")
lines.append("")
lines.append("## Reviewer-safety note")
lines.append("")
lines.append("Configured media-profile values should not be described as packet-capture measurements. They are scenario-control parameters until replaced by tshark, VLC, tc/netem, or O-RAN telemetry measurements.")

OUT.write_text("\n".join(lines) + "\n")
print(f"[ok] wrote {OUT}")
