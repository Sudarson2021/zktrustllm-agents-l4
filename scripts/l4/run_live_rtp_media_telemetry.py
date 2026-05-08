#!/usr/bin/env python3

import csv
import json
import socket
import statistics
import subprocess
import time
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
VIDEO = ROOT / "media_samples" / "l4_test_video_30s.mp4"
OUT_DIR = ROOT / "results" / "l4_live_rtp_media"

EVENTS_CSV = OUT_DIR / "rtp_packet_events.csv"
SUMMARY_JSON = OUT_DIR / "rtp_media_summary.json"
SUMMARY_MD = OUT_DIR / "rtp_media_summary.md"

FIG_JITTER = OUT_DIR / "figure_5_10_live_rtp_jitter.png"
FIG_BITRATE = OUT_DIR / "figure_5_11_live_rtp_bitrate.png"
FIG_SEQ = OUT_DIR / "figure_5_12_live_rtp_sequence_progress.png"

RTP_HOST = "127.0.0.1"
RTP_PORT = 5004
CAPTURE_SECONDS = 25


def parse_rtp_header(packet: bytes):
    if len(packet) < 12:
        return None

    version = packet[0] >> 6
    if version != 2:
        return None

    return {
        "sequence": int.from_bytes(packet[2:4], "big"),
        "timestamp": int.from_bytes(packet[4:8], "big"),
        "ssrc": int.from_bytes(packet[8:12], "big"),
        "packet_bytes": len(packet),
        "payload_bytes": max(0, len(packet) - 12),
    }


def start_sender():
    if not VIDEO.exists():
        raise FileNotFoundError(f"Missing video: {VIDEO}")

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-re",
        "-stream_loop",
        "-1",
        "-i",
        str(VIDEO),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-tune",
        "zerolatency",
        "-f",
        "rtp",
        f"rtp://{RTP_HOST}:{RTP_PORT}",
    ]

    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def capture_packets():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((RTP_HOST, RTP_PORT))
    sock.settimeout(0.5)

    start = time.perf_counter()
    events = []

    last_arrival = None
    last_rtp_ts = None

    while time.perf_counter() - start < CAPTURE_SECONDS:
        try:
            packet, _ = sock.recvfrom(65535)
        except socket.timeout:
            continue

        now = time.perf_counter()
        parsed = parse_rtp_header(packet)
        if not parsed:
            continue

        arrival_ms = (now - start) * 1000.0
        jitter_component_ms = 0.0

        if last_arrival is not None and last_rtp_ts is not None:
            arrival_delta_ms = (now - last_arrival) * 1000.0
            rtp_delta_ms = ((parsed["timestamp"] - last_rtp_ts) & 0xFFFFFFFF) / 90.0
            jitter_component_ms = abs(arrival_delta_ms - rtp_delta_ms)

        last_arrival = now
        last_rtp_ts = parsed["timestamp"]

        events.append({
            "arrival_ms": round(arrival_ms, 3),
            "sequence": parsed["sequence"],
            "rtp_timestamp": parsed["timestamp"],
            "ssrc": parsed["ssrc"],
            "packet_bytes": parsed["packet_bytes"],
            "payload_bytes": parsed["payload_bytes"],
            "jitter_component_ms": round(jitter_component_ms, 6),
        })

    sock.close()
    return events


def estimate_loss(events):
    if len(events) < 2:
        return {
            "expected_packets": len(events),
            "received_packets": len(events),
            "lost_packets": 0,
            "packet_loss_pct": 0.0,
        }

    seqs = [e["sequence"] for e in events]
    first = seqs[0]
    last = seqs[-1]

    if last >= first:
        expected = last - first + 1
    else:
        expected = (65535 - first + 1) + last + 1

    received_unique = len(set(seqs))
    lost = max(0, expected - received_unique)
    loss_pct = (lost / expected * 100.0) if expected else 0.0

    return {
        "expected_packets": expected,
        "received_packets": received_unique,
        "lost_packets": lost,
        "packet_loss_pct": round(loss_pct, 6),
    }


def bitrate_windows(events, window_seconds=1.0):
    if not events:
        return []

    max_ms = max(e["arrival_ms"] for e in events)
    windows = []
    current = 0.0

    while current <= max_ms:
        end = current + window_seconds * 1000.0
        bytes_in_window = sum(
            e["packet_bytes"] for e in events
            if current <= e["arrival_ms"] < end
        )
        bitrate_kbps = (bytes_in_window * 8.0) / 1000.0 / window_seconds
        windows.append({
            "window_start_s": round(current / 1000.0, 3),
            "bitrate_kbps": round(bitrate_kbps, 3),
        })
        current = end

    return windows


def write_outputs(events):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with EVENTS_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "arrival_ms",
                "sequence",
                "rtp_timestamp",
                "ssrc",
                "packet_bytes",
                "payload_bytes",
                "jitter_component_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(events)

    loss = estimate_loss(events)
    jitter_values = [
        e["jitter_component_ms"]
        for e in events
        if e["jitter_component_ms"] > 0
    ]
    bitrates = bitrate_windows(events)

    total_bytes = sum(e["packet_bytes"] for e in events)
    avg_bitrate_kbps = round((total_bytes * 8.0) / 1000.0 / CAPTURE_SECONDS, 3)

    summary = {
        "experiment": "step89_live_rtp_media_plane_telemetry",
        "importantNote": "This is live RTP media-plane telemetry over localhost. It is not yet DTLS-secured.",
        "video": str(VIDEO.relative_to(ROOT)),
        "rtpHost": RTP_HOST,
        "rtpPort": RTP_PORT,
        "captureSeconds": CAPTURE_SECONDS,
        "receivedPackets": len(events),
        "totalBytes": total_bytes,
        "avgBitrateKbps": avg_bitrate_kbps,
        "packetLoss": loss,
        "jitter": {
            "samples": len(jitter_values),
            "avgJitterComponentMs": round(statistics.mean(jitter_values), 6) if jitter_values else 0.0,
            "p50JitterComponentMs": round(statistics.median(jitter_values), 6) if jitter_values else 0.0,
            "maxJitterComponentMs": round(max(jitter_values), 6) if jitter_values else 0.0,
        },
        "files": {
            "eventsCsv": str(EVENTS_CSV.relative_to(ROOT)),
            "summaryJson": str(SUMMARY_JSON.relative_to(ROOT)),
            "summaryMarkdown": str(SUMMARY_MD.relative_to(ROOT)),
            "figureJitter": str(FIG_JITTER.relative_to(ROOT)),
            "figureBitrate": str(FIG_BITRATE.relative_to(ROOT)),
            "figureSequence": str(FIG_SEQ.relative_to(ROOT)),
        },
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    SUMMARY_MD.write_text(
        "\n".join([
            "# Step 89 Live RTP Media-Plane Telemetry Summary",
            "",
            "> This experiment measures live RTP media-plane telemetry over localhost. It is not yet DTLS-secured.",
            "",
            "## Summary",
            "",
            f"- Capture duration: {CAPTURE_SECONDS} seconds",
            f"- RTP endpoint: {RTP_HOST}:{RTP_PORT}",
            f"- Received packets: {len(events)}",
            f"- Average bitrate: {avg_bitrate_kbps} kbps",
            f"- Expected packets: {loss['expected_packets']}",
            f"- Lost packets: {loss['lost_packets']}",
            f"- Packet loss: {loss['packet_loss_pct']}%",
            f"- Average jitter component: {summary['jitter']['avgJitterComponentMs']} ms",
            f"- P50 jitter component: {summary['jitter']['p50JitterComponentMs']} ms",
            f"- Max jitter component: {summary['jitter']['maxJitterComponentMs']} ms",
            "",
            "## Research Meaning",
            "",
            "This step adds live RTP media-plane measurement to the Level 4 workflow. Previous steps measured MCP/A2A control-plane latency and scaling. Step 89 begins measuring RTP-level media behaviour, including packet continuity, jitter, and bitrate.",
            "",
            "## Boundary",
            "",
            "This is RTP media-plane validation only. DTLS-secured media-plane validation should be added next after this baseline is stable.",
            "",
        ])
    )

    if events:
        x = [e["arrival_ms"] / 1000.0 for e in events]
        jitter = [e["jitter_component_ms"] for e in events]
        seq = [e["sequence"] for e in events]

        plt.figure(figsize=(8, 4.5))
        plt.plot(x, jitter)
        plt.xlabel("Time (s)")
        plt.ylabel("Jitter component (ms)")
        plt.title("Figure 5.10: Live RTP Jitter Component")
        plt.tight_layout()
        plt.savefig(FIG_JITTER)
        plt.savefig(FIG_JITTER.with_suffix(".pdf"))
        plt.savefig(FIG_JITTER.with_suffix(".svg"))
        plt.close()

        bw_x = [b["window_start_s"] for b in bitrates]
        bw_y = [b["bitrate_kbps"] for b in bitrates]

        plt.figure(figsize=(8, 4.5))
        plt.plot(bw_x, bw_y, marker="o")
        plt.xlabel("Time window start (s)")
        plt.ylabel("Bitrate (kbps)")
        plt.title("Figure 5.11: Live RTP Bitrate over Time")
        plt.tight_layout()
        plt.savefig(FIG_BITRATE)
        plt.savefig(FIG_BITRATE.with_suffix(".pdf"))
        plt.savefig(FIG_BITRATE.with_suffix(".svg"))
        plt.close()

        plt.figure(figsize=(8, 4.5))
        plt.plot(x, seq)
        plt.xlabel("Time (s)")
        plt.ylabel("RTP sequence number")
        plt.title("Figure 5.12: Live RTP Sequence Progress")
        plt.tight_layout()
        plt.savefig(FIG_SEQ)
        plt.savefig(FIG_SEQ.with_suffix(".pdf"))
        plt.savefig(FIG_SEQ.with_suffix(".svg"))
        plt.close()

    return summary


def main():
    print("Starting RTP sender...")
    sender = start_sender()
    time.sleep(2.0)

    try:
        print("Capturing RTP packets...")
        events = capture_packets()
    finally:
        sender.terminate()
        try:
            sender.wait(timeout=3)
        except subprocess.TimeoutExpired:
            sender.kill()

    summary = write_outputs(events)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
