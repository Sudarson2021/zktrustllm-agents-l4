#!/usr/bin/env python3

import csv
import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "l4_dtls_rtp_media"

EVENTS_CSV = OUT_DIR / "dtls_rtp_packet_events.csv"
SUMMARY_JSON = OUT_DIR / "dtls_rtp_media_summary.json"
SUMMARY_MD = OUT_DIR / "dtls_rtp_media_summary.md"

FIG_JITTER = OUT_DIR / "figure_5_13_dtls_rtp_jitter.png"
FIG_JITTER_PDF = OUT_DIR / "figure_5_13_dtls_rtp_jitter.pdf"
FIG_JITTER_SVG = OUT_DIR / "figure_5_13_dtls_rtp_jitter.svg"


def main():
    if not EVENTS_CSV.exists():
        raise SystemExit(f"Missing events CSV: {EVENTS_CSV}")
    if not SUMMARY_JSON.exists():
        raise SystemExit(f"Missing summary JSON: {SUMMARY_JSON}")

    with EVENTS_CSV.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not rows:
        raise SystemExit("No RTP rows found. Do not commit this result.")

    if "jitter_component_ms" not in fieldnames:
        fieldnames.append("jitter_component_ms")

    arrivals = [float(r["arrival_ms"]) for r in rows]

    arrival_gaps = [
        arrivals[i] - arrivals[i - 1]
        for i in range(1, len(arrivals))
        if arrivals[i] >= arrivals[i - 1]
    ]

    if not arrival_gaps:
        raise SystemExit("No valid arrival gaps found.")

    median_gap = statistics.median(arrival_gaps)

    jitter_components = [0.0]
    for i in range(1, len(arrivals)):
        gap = arrivals[i] - arrivals[i - 1]
        if gap < 0:
            component = 0.0
        else:
            component = abs(gap - median_gap)
        jitter_components.append(component)

    for row, component in zip(rows, jitter_components):
        row["jitter_component_ms"] = f"{component:.6f}"

    with EVENTS_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    samples = jitter_components[1:]
    avg_jitter = round(statistics.mean(samples), 6)
    p50_jitter = round(statistics.median(samples), 6)
    max_jitter = round(max(samples), 6)

    summary = json.loads(SUMMARY_JSON.read_text())

    summary["jitter"] = {
        "metric": "arrival_gap_jitter_component_ms",
        "samples": len(samples),
        "medianArrivalGapMs": round(median_gap, 6),
        "avgJitterComponentMs": avg_jitter,
        "p50JitterComponentMs": p50_jitter,
        "maxJitterComponentMs": max_jitter,
        "note": "Computed from RTP packet arrival-gap variation. This avoids false artefacts from non-monotonic H.264 RTP timestamps."
    }

    if "comparisonWithPlainRtpStep89" in summary:
        summary["comparisonWithPlainRtpStep89"]["dtlsAvgJitterMs"] = avg_jitter

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    md = f"""# Step 90 DTLS-Wrapped RTP Media-Plane Telemetry Summary

> This experiment measures RTP media packets protected by a local DTLS tunnel/proxy. It is not WebRTC DTLS-SRTP.

## Summary

- Capture duration: {summary.get("captureSeconds")} seconds
- RTP client input: {summary.get("rtpClientInput")}
- DTLS endpoint: {summary.get("dtlsEndpoint")}
- Recovered RTP endpoint: {summary.get("recoveredRtpEndpoint")}
- Received packets: {summary.get("receivedPackets")}
- Average bitrate: {summary.get("avgBitrateKbps")} kbps
- Expected packets: {summary.get("packetLoss", {}).get("expected_packets")}
- Lost packets: {summary.get("packetLoss", {}).get("lost_packets")}
- Packet loss: {summary.get("packetLoss", {}).get("packet_loss_pct")}%
- Jitter metric: arrival-gap jitter component
- Median arrival gap: {summary["jitter"]["medianArrivalGapMs"]} ms
- Average jitter component: {avg_jitter} ms
- P50 jitter component: {p50_jitter} ms
- Max jitter component: {max_jitter} ms

## Comparison with Step 89 Plain RTP

- Plain RTP packet loss: {summary.get("comparisonWithPlainRtpStep89", {}).get("plainPacketLossPct")}%
- DTLS-wrapped RTP packet loss: {summary.get("comparisonWithPlainRtpStep89", {}).get("dtlsPacketLossPct")}%
- Plain RTP average bitrate: {summary.get("comparisonWithPlainRtpStep89", {}).get("plainAvgBitrateKbps")} kbps
- DTLS-wrapped RTP average bitrate: {summary.get("comparisonWithPlainRtpStep89", {}).get("dtlsAvgBitrateKbps")} kbps
- Plain RTP average jitter: {summary.get("comparisonWithPlainRtpStep89", {}).get("plainAvgJitterMs")} ms
- DTLS-wrapped RTP arrival-gap jitter: {avg_jitter} ms

## Research Meaning

This step adds the first secured media-plane validation layer after the plain RTP baseline. The DTLS handshake succeeds, recovered RTP packets are captured, and packet-loss/jitter/bitrate KPIs are measured after DTLS protection.

## Boundary

This is a DTLS tunnel/proxy baseline for RTP media-plane validation. It is not WebRTC DTLS-SRTP.
"""
    SUMMARY_MD.write_text(md)

    plt.figure(figsize=(8, 4))
    plt.plot(list(range(len(jitter_components))), jitter_components)
    plt.xlabel("Recovered RTP packet index")
    plt.ylabel("Arrival-gap jitter component (ms)")
    plt.title("Figure 5.13: DTLS-Wrapped RTP Arrival-Gap Jitter")
    plt.tight_layout()
    plt.savefig(FIG_JITTER)
    plt.savefig(FIG_JITTER_PDF)
    plt.savefig(FIG_JITTER_SVG)
    plt.close()

    print(json.dumps({
        "status": "ok",
        "packets": summary.get("receivedPackets"),
        "avgBitrateKbps": summary.get("avgBitrateKbps"),
        "avgArrivalGapJitterMs": avg_jitter,
        "p50ArrivalGapJitterMs": p50_jitter,
        "maxArrivalGapJitterMs": max_jitter,
        "summaryJson": str(SUMMARY_JSON),
        "summaryMarkdown": str(SUMMARY_MD),
        "jitterFigure": str(FIG_JITTER)
    }, indent=2))


if __name__ == "__main__":
    main()
