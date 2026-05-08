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
PROXY = ROOT / "dtls_rtp" / "dtls_rtp_proxy"

PLAIN_SUMMARY = ROOT / "results" / "l4_live_rtp_media" / "rtp_media_summary.json"

OUT_DIR = ROOT / "results" / "l4_dtls_rtp_media"
EVENTS_CSV = OUT_DIR / "dtls_rtp_packet_events.csv"
SUMMARY_JSON = OUT_DIR / "dtls_rtp_media_summary.json"
SUMMARY_MD = OUT_DIR / "dtls_rtp_media_summary.md"

FIG_JITTER = OUT_DIR / "figure_5_13_dtls_rtp_jitter.png"
FIG_JITTER_PDF = OUT_DIR / "figure_5_13_dtls_rtp_jitter.pdf"
FIG_JITTER_SVG = OUT_DIR / "figure_5_13_dtls_rtp_jitter.svg"

FIG_LOSS = OUT_DIR / "figure_5_14_plain_vs_dtls_packet_loss.png"
FIG_LOSS_PDF = OUT_DIR / "figure_5_14_plain_vs_dtls_packet_loss.pdf"
FIG_LOSS_SVG = OUT_DIR / "figure_5_14_plain_vs_dtls_packet_loss.svg"

FIG_BITRATE = OUT_DIR / "figure_5_15_plain_vs_dtls_bitrate.png"
FIG_BITRATE_PDF = OUT_DIR / "figure_5_15_plain_vs_dtls_bitrate.pdf"
FIG_BITRATE_SVG = OUT_DIR / "figure_5_15_plain_vs_dtls_bitrate.svg"

RTP_CLIENT_IN_HOST = "127.0.0.1"
RTP_CLIENT_IN_PORT = 6000

DTLS_HOST = "127.0.0.1"
DTLS_PORT = 4444

RECOVERED_RTP_HOST = "127.0.0.1"
RECOVERED_RTP_PORT = 5006

CAPTURE_SECONDS = 25
PROXY_DURATION_SECONDS = 28



def signed_rtp_ts_delta_ms(curr_ts, prev_ts, clock_rate=90000):
    """
    Return signed RTP timestamp delta in ms.

    This avoids treating timestamp decreases as huge uint32 wraparound values.
    For H.264 RTP with B-frames, RTP timestamps can appear non-monotonic
    in packet capture order, so negative deltas should not be used for
    one-way jitter estimation.
    """
    delta = int(curr_ts) - int(prev_ts)

    # Convert possible uint32 wrap into signed range
    if delta > 2**31:
        delta -= 2**32
    elif delta < -(2**31):
        delta += 2**32

    return (delta / clock_rate) * 1000.0


def parse_rtp_packet(data: bytes):
    if len(data) < 12:
        return None
    version = data[0] >> 6
    if version != 2:
        return None
    sequence = int.from_bytes(data[2:4], "big")
    timestamp = int.from_bytes(data[4:8], "big")
    ssrc = int.from_bytes(data[8:12], "big")
    return {
        "sequence": sequence,
        "rtp_timestamp": timestamp,
        "ssrc": ssrc,
        "packet_bytes": len(data),
        "payload_bytes": max(0, len(data) - 12),
    }


def seq_distance(prev_seq, cur_seq):
    return (cur_seq - prev_seq) % 65536


def compute_packet_loss(sequences):
    if not sequences:
        return {
            "expected_packets": 0,
            "received_packets": 0,
            "lost_packets": 0,
            "packet_loss_pct": 0.0,
        }

    expected = 1
    lost = 0
    prev = sequences[0]

    for cur in sequences[1:]:
        diff = seq_distance(prev, cur)
        if diff == 0:
            pass
        elif diff == 1:
            expected += 1
        else:
            lost += diff - 1
            expected += diff
        prev = cur

    received = len(sequences)
    loss_pct = (lost / expected * 100.0) if expected else 0.0

    return {
        "expected_packets": expected,
        "received_packets": received,
        "lost_packets": lost,
        "packet_loss_pct": round(loss_pct, 6),
    }


def percentile(values, pct):
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(round((pct / 100.0) * (len(values) - 1)))
    return values[idx]


def start_process(cmd, name, stdout_path, stderr_path):
    stdout_f = open(stdout_path, "w")
    stderr_f = open(stderr_path, "w")
    proc = subprocess.Popen(
        cmd,
        stdout=stdout_f,
        stderr=stderr_f,
        cwd=str(ROOT),
    )
    return proc, stdout_f, stderr_f


def terminate_process(proc, stdout_f=None, stderr_f=None):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
    if stdout_f:
        stdout_f.close()
    if stderr_f:
        stderr_f.close()


def capture_recovered_rtp():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((RECOVERED_RTP_HOST, RECOVERED_RTP_PORT))
    sock.settimeout(1.0)

    start = time.monotonic()
    events = []
    sequences = []
    total_bytes = 0

    prev_arrival_ms = None
    prev_rtp_timestamp = None

    while time.monotonic() - start < CAPTURE_SECONDS:
        try:
            data, _addr = sock.recvfrom(4096)
        except socket.timeout:
            continue

        arrival_ms = (time.monotonic() - start) * 1000.0
        parsed = parse_rtp_packet(data)
        if not parsed:
            continue

        jitter_component = 0.0
        if prev_arrival_ms is not None and prev_rtp_timestamp is not None:
            arrival_delta = arrival_ms - prev_arrival_ms
            # Step 89 used 90 kHz RTP timestamp conversion for H.264 video stream.
            rtp_delta_ms = ((parsed["rtp_timestamp"] - prev_rtp_timestamp) % (2**32)) / 90.0
            jitter_component = abs(arrival_delta - rtp_delta_ms)

        prev_arrival_ms = arrival_ms
        prev_rtp_timestamp = parsed["rtp_timestamp"]

        sequences.append(parsed["sequence"])
        total_bytes += parsed["packet_bytes"]

        events.append({
            "arrival_ms": round(arrival_ms, 3),
            "sequence": parsed["sequence"],
            "rtp_timestamp": parsed["rtp_timestamp"],
            "ssrc": parsed["ssrc"],
            "packet_bytes": parsed["packet_bytes"],
            "payload_bytes": parsed["payload_bytes"],
            "jitter_component_ms": round(jitter_component, 6),
        })

    sock.close()
    return events, sequences, total_bytes


def write_events(events):
    with EVENTS_CSV.open("w", newline="") as f:
        fieldnames = [
            "arrival_ms",
            "sequence",
            "rtp_timestamp",
            "ssrc",
            "packet_bytes",
            "payload_bytes",
            "jitter_component_ms",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)


def make_figures(events, dtls_summary, plain_summary):
    if events:
        xs = [e["arrival_ms"] / 1000.0 for e in events]
        jitters = [e["jitter_component_ms"] for e in events]

        plt.figure(figsize=(8, 4.5))
        plt.plot(xs, jitters, linewidth=1)
        plt.xlabel("Time (s)")
        plt.ylabel("Jitter component (ms)")
        plt.title("Figure 5.13: DTLS-wrapped RTP jitter")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIG_JITTER, dpi=200)
        plt.savefig(FIG_JITTER_PDF)
        plt.savefig(FIG_JITTER_SVG)
        plt.close()

    labels = ["Plain RTP", "DTLS-wrapped RTP"]
    losses = [
        plain_summary["packetLoss"]["packet_loss_pct"],
        dtls_summary["packetLoss"]["packet_loss_pct"],
    ]

    plt.figure(figsize=(7, 4.5))
    plt.bar(labels, losses)
    plt.ylabel("Packet loss (%)")
    plt.title("Figure 5.14: Plain RTP vs DTLS-wrapped RTP packet loss")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG_LOSS, dpi=200)
    plt.savefig(FIG_LOSS_PDF)
    plt.savefig(FIG_LOSS_SVG)
    plt.close()

    bitrates = [
        plain_summary["avgBitrateKbps"],
        dtls_summary["avgBitrateKbps"],
    ]

    plt.figure(figsize=(7, 4.5))
    plt.bar(labels, bitrates)
    plt.ylabel("Average bitrate (kbps)")
    plt.title("Figure 5.15: Plain RTP vs DTLS-wrapped RTP bitrate")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG_BITRATE, dpi=200)
    plt.savefig(FIG_BITRATE_PDF)
    plt.savefig(FIG_BITRATE_SVG)
    plt.close()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not VIDEO.exists():
        raise SystemExit(f"Missing video file: {VIDEO}")
    if not PROXY.exists():
        raise SystemExit(f"Missing DTLS RTP proxy binary: {PROXY}")
    if not PLAIN_SUMMARY.exists():
        raise SystemExit(f"Missing Step 89 plain RTP summary: {PLAIN_SUMMARY}")

    plain_summary = json.loads(PLAIN_SUMMARY.read_text())

    server_stdout = OUT_DIR / "dtls_server_stdout.log"
    server_stderr = OUT_DIR / "dtls_server_stderr.log"
    client_stdout = OUT_DIR / "dtls_client_stdout.log"
    client_stderr = OUT_DIR / "dtls_client_stderr.log"
    ffmpeg_stdout = OUT_DIR / "ffmpeg_dtls_rtp_stdout.log"
    ffmpeg_stderr = OUT_DIR / "ffmpeg_dtls_rtp_stderr.log"

    server_cmd = [
        str(PROXY),
        "server",
        DTLS_HOST,
        str(DTLS_PORT),
        RECOVERED_RTP_HOST,
        str(RECOVERED_RTP_PORT),
    ]

    client_cmd = [
        str(PROXY),
        "client",
        DTLS_HOST,
        str(DTLS_PORT),
        RTP_CLIENT_IN_HOST,
        str(RTP_CLIENT_IN_PORT),
    ]

    ffmpeg_cmd = [
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
        "copy",
        "-f",
        "rtp",
        f"rtp://{RTP_CLIENT_IN_HOST}:{RTP_CLIENT_IN_PORT}?pkt_size=1200",
    ]

    print("Starting DTLS RTP server proxy...")
    server_proc, server_out, server_err = start_process(server_cmd, "dtls-server", server_stdout, server_stderr)
    time.sleep(0.8)

    print("Starting DTLS RTP client proxy...")
    client_proc, client_out, client_err = start_process(client_cmd, "dtls-client", client_stdout, client_stderr)
    time.sleep(1.2)

    print("Starting FFmpeg RTP sender into DTLS client proxy...")
    ffmpeg_proc, ffmpeg_out, ffmpeg_err = start_process(ffmpeg_cmd, "ffmpeg", ffmpeg_stdout, ffmpeg_stderr)
    time.sleep(0.8)

    try:
        print("Capturing recovered DTLS-wrapped RTP packets...")
        events, sequences, total_bytes = capture_recovered_rtp()
    finally:
        terminate_process(ffmpeg_proc, ffmpeg_out, ffmpeg_err)
        terminate_process(client_proc, client_out, client_err)
        terminate_process(server_proc, server_out, server_err)

    write_events(events)

    loss = compute_packet_loss(sequences)
    jitter_values = [e["jitter_component_ms"] for e in events[1:]]
    avg_bitrate_kbps = (total_bytes * 8.0) / CAPTURE_SECONDS / 1000.0

    dtls_summary = {
        "experiment": "step90_dtls_wrapped_rtp_media_plane_telemetry",
        "importantNote": "This is DTLS-wrapped RTP media-plane telemetry over localhost. It is a DTLS tunnel/proxy baseline, not WebRTC DTLS-SRTP.",
        "video": str(VIDEO.relative_to(ROOT)),
        "dtlsProxy": str(PROXY.relative_to(ROOT)),
        "rtpClientInput": f"{RTP_CLIENT_IN_HOST}:{RTP_CLIENT_IN_PORT}",
        "dtlsEndpoint": f"{DTLS_HOST}:{DTLS_PORT}",
        "recoveredRtpEndpoint": f"{RECOVERED_RTP_HOST}:{RECOVERED_RTP_PORT}",
        "captureSeconds": CAPTURE_SECONDS,
        "receivedPackets": len(events),
        "totalBytes": total_bytes,
        "avgBitrateKbps": round(avg_bitrate_kbps, 3),
        "packetLoss": loss,
        "jitter": {
            "samples": len(jitter_values),
            "avgJitterComponentMs": round(statistics.mean(jitter_values), 6) if jitter_values else 0.0,
            "p50JitterComponentMs": round(percentile(jitter_values, 50), 6) if jitter_values else 0.0,
            "maxJitterComponentMs": round(max(jitter_values), 6) if jitter_values else 0.0,
        },
        "comparisonWithPlainRtpStep89": {
            "plainPacketLossPct": plain_summary["packetLoss"]["packet_loss_pct"],
            "dtlsPacketLossPct": loss["packet_loss_pct"],
            "plainAvgBitrateKbps": plain_summary["avgBitrateKbps"],
            "dtlsAvgBitrateKbps": round(avg_bitrate_kbps, 3),
            "plainAvgJitterMs": plain_summary["jitter"]["avgJitterComponentMs"],
            "dtlsAvgJitterMs": round(statistics.mean(jitter_values), 6) if jitter_values else 0.0,
        },
        "files": {
            "eventsCsv": str(EVENTS_CSV.relative_to(ROOT)),
            "summaryJson": str(SUMMARY_JSON.relative_to(ROOT)),
            "summaryMarkdown": str(SUMMARY_MD.relative_to(ROOT)),
            "figureJitter": str(FIG_JITTER.relative_to(ROOT)),
            "figureLoss": str(FIG_LOSS.relative_to(ROOT)),
            "figureBitrate": str(FIG_BITRATE.relative_to(ROOT)),
        },
    }

    SUMMARY_JSON.write_text(json.dumps(dtls_summary, indent=2) + "\n")

    SUMMARY_MD.write_text(
        "# Step 90 DTLS-Wrapped RTP Media-Plane Telemetry Summary\n\n"
        "> This experiment measures RTP media packets protected by a local DTLS tunnel/proxy. "
        "It is not WebRTC DTLS-SRTP.\n\n"
        "## Summary\n\n"
        f"- Capture duration: {CAPTURE_SECONDS} seconds\n"
        f"- RTP client input: {RTP_CLIENT_IN_HOST}:{RTP_CLIENT_IN_PORT}\n"
        f"- DTLS endpoint: {DTLS_HOST}:{DTLS_PORT}\n"
        f"- Recovered RTP endpoint: {RECOVERED_RTP_HOST}:{RECOVERED_RTP_PORT}\n"
        f"- Received packets: {len(events)}\n"
        f"- Average bitrate: {round(avg_bitrate_kbps, 3)} kbps\n"
        f"- Expected packets: {loss['expected_packets']}\n"
        f"- Lost packets: {loss['lost_packets']}\n"
        f"- Packet loss: {loss['packet_loss_pct']}%\n"
        f"- Average jitter component: {dtls_summary['jitter']['avgJitterComponentMs']} ms\n"
        f"- P50 jitter component: {dtls_summary['jitter']['p50JitterComponentMs']} ms\n"
        f"- Max jitter component: {dtls_summary['jitter']['maxJitterComponentMs']} ms\n\n"
        "## Comparison with Step 89 Plain RTP\n\n"
        f"- Plain RTP packet loss: {plain_summary['packetLoss']['packet_loss_pct']}%\n"
        f"- DTLS-wrapped RTP packet loss: {loss['packet_loss_pct']}%\n"
        f"- Plain RTP average bitrate: {plain_summary['avgBitrateKbps']} kbps\n"
        f"- DTLS-wrapped RTP average bitrate: {round(avg_bitrate_kbps, 3)} kbps\n"
        f"- Plain RTP average jitter: {plain_summary['jitter']['avgJitterComponentMs']} ms\n"
        f"- DTLS-wrapped RTP average jitter: {dtls_summary['jitter']['avgJitterComponentMs']} ms\n\n"
        "## Research Meaning\n\n"
        "This step adds the first secured media-plane validation layer after the plain RTP baseline. "
        "It allows packet loss, jitter, and bitrate to be compared before and after DTLS protection.\n"
    )

    make_figures(events, dtls_summary, plain_summary)

    print(json.dumps(dtls_summary, indent=2))


if __name__ == "__main__":
    main()
