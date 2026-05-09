#!/usr/bin/env python3

import csv
import json
import math
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "l4_namespace_impairment"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO = ROOT / "media_samples" / "l4_test_video_30s.mp4"
PROXY = ROOT / "dtls_rtp" / "dtls_rtp_proxy"
PYTHON = Path(sys.executable).resolve()

NS_SENDER = "zkl4_sender"
NS_RECEIVER = "zkl4_receiver"
VETH_SENDER = "zkl4veth_s"
VETH_RECEIVER = "zkl4veth_r"
SENDER_IP = "10.93.0.1"
RECEIVER_IP = "10.93.0.2"

CAPTURE_SECONDS = 25
PLAIN_RTP_PORT = 5004
DTLS_PORT = 4444
DTLS_CLIENT_RTP_PORT = 6000
RECOVERED_RTP_PORT = 5006

RECEIVER_SCRIPT = OUT_DIR / "namespace_rtp_receiver.py"

SUMMARY_JSON = OUT_DIR / "namespace_impairment_summary.json"
SUMMARY_CSV = OUT_DIR / "namespace_impairment_summary.csv"
SUMMARY_MD = OUT_DIR / "namespace_impairment_summary.md"

FIG_LOSS = OUT_DIR / "figure_5_19_namespace_packet_loss.png"
FIG_BITRATE = OUT_DIR / "figure_5_20_namespace_bitrate.png"
FIG_JITTER = OUT_DIR / "figure_5_21_namespace_arrival_gap_jitter.png"

PROFILES = [
    {
        "name": "clean_baseline",
        "description": "No artificial impairment across namespace veth pair",
        "netem": None,
    },
    {
        "name": "delay_20ms",
        "description": "20 ms fixed veth delay",
        "netem": ["delay", "20ms"],
    },
    {
        "name": "delay_20ms_jitter_5ms",
        "description": "20 ms delay with 5 ms jitter",
        "netem": ["delay", "20ms", "5ms", "distribution", "normal"],
    },
    {
        "name": "delay_30ms_jitter_10ms_loss_1pct",
        "description": "30 ms delay, 10 ms jitter, 1% packet loss",
        "netem": ["delay", "30ms", "10ms", "distribution", "normal", "loss", "1%"],
    },
]


def run(cmd, check=True, capture=False):
    print("+", " ".join(str(x) for x in cmd))
    if capture:
        return subprocess.run(
            cmd,
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    return subprocess.run(cmd, check=check)


def sudo(cmd):
    return ["sudo"] + [str(x) for x in cmd]


def write_receiver_script():
    code = r'''#!/usr/bin/env python3

import argparse
import csv
import json
import socket
import struct
import time
from pathlib import Path


def parse_rtp_packet(data):
    if len(data) < 12:
        return None

    version = data[0] >> 6
    if version != 2:
        return None

    cc = data[0] & 0x0F
    extension = (data[0] >> 4) & 0x01
    header_len = 12 + (cc * 4)

    if len(data) < header_len:
        return None

    if extension:
        if len(data) < header_len + 4:
            return None
        ext_len_words = struct.unpack("!H", data[header_len + 2:header_len + 4])[0]
        header_len += 4 + (ext_len_words * 4)
        if len(data) < header_len:
            return None

    sequence = struct.unpack("!H", data[2:4])[0]
    timestamp = struct.unpack("!I", data[4:8])[0]
    ssrc = struct.unpack("!I", data[8:12])[0]

    return {
        "sequence": sequence,
        "rtp_timestamp": timestamp,
        "ssrc": ssrc,
        "packet_bytes": len(data),
        "payload_bytes": max(0, len(data) - header_len),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--seconds", required=True, type=float)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    sock.settimeout(0.2)

    rows = []
    start = time.monotonic()
    end = start + args.seconds

    while time.monotonic() < end:
        try:
            data, _addr = sock.recvfrom(65535)
        except socket.timeout:
            continue

        parsed = parse_rtp_packet(data)
        if parsed is None:
            continue

        arrival_ms = (time.monotonic() - start) * 1000.0
        parsed["arrival_ms"] = round(arrival_ms, 6)
        rows.append(parsed)

    sock.close()

    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "arrival_ms",
                "sequence",
                "rtp_timestamp",
                "ssrc",
                "packet_bytes",
                "payload_bytes",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(json.dumps({"packets": len(rows), "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
'''
    RECEIVER_SCRIPT.write_text(code)
    RECEIVER_SCRIPT.chmod(0o755)


def start_process(cmd, stdout_path, stderr_path):
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    out = stdout_path.open("w")
    err = stderr_path.open("w")
    proc = subprocess.Popen([str(x) for x in cmd], stdout=out, stderr=err, text=True)
    return proc, out, err


def stop_process(proc, out=None, err=None):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    if out:
        out.close()
    if err:
        err.close()


def percentile(values, pct):
    if not values:
        return 0.0
    xs = sorted(values)
    k = (len(xs) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs[int(k)]
    return xs[f] * (c - k) + xs[c] * (k - f)


def compute_sequence_loss(seqs):
    """Estimate RTP loss using the smallest circular arc covering observed sequence numbers.

    This avoids false 65536-packet loss when netem jitter reorders packets around
    the first observed sequence number.
    """
    if not seqs:
        return 0, 0, 0.0

    unique = sorted(set(int(x) % 65536 for x in seqs))

    if len(unique) == 1:
        return 1, 0, 0.0

    gaps = []
    for i in range(len(unique)):
        cur = unique[i]
        nxt = unique[(i + 1) % len(unique)]
        if i == len(unique) - 1:
            gap = (nxt + 65536) - cur - 1
        else:
            gap = nxt - cur - 1
        gaps.append(gap)

    largest_gap = max(gaps)
    expected = 65536 - largest_gap
    lost = max(0, expected - len(unique))
    loss_pct = (lost / expected * 100.0) if expected else 0.0

    return expected, lost, loss_pct


def compute_metrics(events_csv, profile, mode, description):
    rows = []
    with Path(events_csv).open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    received = len(rows)

    if received == 0:
        return {
            "profile": profile,
            "description": description,
            "mode": mode,
            "receivedPackets": 0,
            "expectedPackets": 0,
            "lostPackets": 0,
            "packetLossPct": 100.0,
            "avgBitrateKbps": 0.0,
            "avgJitterMs": 0.0,
            "p50JitterMs": 0.0,
            "p95JitterMs": 0.0,
            "maxJitterMs": 0.0,
            "medianArrivalGapMs": 0.0,
            "status": "no_packets",
        }

    arrivals = [float(r["arrival_ms"]) for r in rows]
    seqs = [int(r["sequence"]) for r in rows]
    total_bytes = sum(int(r["packet_bytes"]) for r in rows)

    expected, lost, loss_pct = compute_sequence_loss(seqs)

    gaps = []
    for i in range(1, len(arrivals)):
        gap = arrivals[i] - arrivals[i - 1]
        if gap >= 0:
            gaps.append(gap)

    median_gap = statistics.median(gaps) if gaps else 0.0
    jitter_components = [abs(g - median_gap) for g in gaps]

    avg_jitter = statistics.mean(jitter_components) if jitter_components else 0.0
    p50_jitter = percentile(jitter_components, 50)
    p95_jitter = percentile(jitter_components, 95)
    max_jitter = max(jitter_components) if jitter_components else 0.0

    bitrate_kbps = (total_bytes * 8.0) / CAPTURE_SECONDS / 1000.0

    return {
        "profile": profile,
        "description": description,
        "mode": mode,
        "receivedPackets": received,
        "expectedPackets": expected,
        "lostPackets": lost,
        "packetLossPct": round(loss_pct, 6),
        "avgBitrateKbps": round(bitrate_kbps, 6),
        "avgJitterMs": round(avg_jitter, 6),
        "p50JitterMs": round(p50_jitter, 6),
        "p95JitterMs": round(p95_jitter, 6),
        "maxJitterMs": round(max_jitter, 6),
        "medianArrivalGapMs": round(median_gap, 6),
        "status": "measured_from_namespace_packet_events",
    }


def cleanup_namespaces():
    for ns in [NS_SENDER, NS_RECEIVER]:
        run(sudo(["ip", "netns", "del", ns]), check=False)


def setup_namespaces():
    cleanup_namespaces()

    run(sudo(["ip", "netns", "add", NS_SENDER]))
    run(sudo(["ip", "netns", "add", NS_RECEIVER]))

    run(sudo(["ip", "link", "add", VETH_SENDER, "type", "veth", "peer", "name", VETH_RECEIVER]))
    run(sudo(["ip", "link", "set", VETH_SENDER, "netns", NS_SENDER]))
    run(sudo(["ip", "link", "set", VETH_RECEIVER, "netns", NS_RECEIVER]))

    run(sudo(["ip", "-n", NS_SENDER, "addr", "add", f"{SENDER_IP}/24", "dev", VETH_SENDER]))
    run(sudo(["ip", "-n", NS_RECEIVER, "addr", "add", f"{RECEIVER_IP}/24", "dev", VETH_RECEIVER]))

    run(sudo(["ip", "-n", NS_SENDER, "link", "set", "lo", "up"]))
    run(sudo(["ip", "-n", NS_RECEIVER, "link", "set", "lo", "up"]))
    run(sudo(["ip", "-n", NS_SENDER, "link", "set", VETH_SENDER, "up"]))
    run(sudo(["ip", "-n", NS_RECEIVER, "link", "set", VETH_RECEIVER, "up"]))

    run(sudo(["ip", "netns", "exec", NS_SENDER, "ping", "-c", "1", "-W", "2", RECEIVER_IP]))
    run(sudo(["ip", "netns", "exec", NS_RECEIVER, "ping", "-c", "1", "-W", "2", SENDER_IP]))


def clear_netem():
    run(sudo(["ip", "netns", "exec", NS_SENDER, "tc", "qdisc", "del", "dev", VETH_SENDER, "root"]), check=False)
    run(sudo(["ip", "netns", "exec", NS_RECEIVER, "tc", "qdisc", "del", "dev", VETH_RECEIVER, "root"]), check=False)


def apply_profile(profile):
    clear_netem()

    if not profile["netem"]:
        print(f"[netem] clean profile: {profile['name']}")
        return

    args = profile["netem"]

    run(sudo(["ip", "netns", "exec", NS_SENDER, "tc", "qdisc", "replace", "dev", VETH_SENDER, "root", "netem"] + args))
    run(sudo(["ip", "netns", "exec", NS_RECEIVER, "tc", "qdisc", "replace", "dev", VETH_RECEIVER, "root", "netem"] + args))

    print(f"[netem] applied profile: {profile['name']}")


def run_plain(profile):
    name = profile["name"]
    print(f"\n=== Namespace plain RTP under {name} ===")

    events = OUT_DIR / f"{name}_plain_rtp_packet_events.csv"

    receiver_cmd = sudo([
        "ip", "netns", "exec", NS_RECEIVER,
        str(PYTHON), str(RECEIVER_SCRIPT),
        "--host", "0.0.0.0",
        "--port", str(PLAIN_RTP_PORT),
        "--seconds", str(CAPTURE_SECONDS),
        "--out", str(events),
    ])

    ffmpeg_cmd = sudo([
        "ip", "netns", "exec", NS_SENDER,
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "warning",
        "-re",
        "-stream_loop", "-1",
        "-i", str(VIDEO),
        "-an",
        "-c:v", "copy",
        "-f", "rtp",
        f"rtp://{RECEIVER_IP}:{PLAIN_RTP_PORT}",
    ])

    recv_proc, recv_out, recv_err = start_process(
        receiver_cmd,
        OUT_DIR / f"{name}_plain_receiver_stdout.log",
        OUT_DIR / f"{name}_plain_receiver_stderr.log",
    )

    time.sleep(1)

    ff_proc, ff_out, ff_err = start_process(
        ffmpeg_cmd,
        OUT_DIR / f"{name}_plain_ffmpeg_stdout.log",
        OUT_DIR / f"{name}_plain_ffmpeg_stderr.log",
    )

    recv_proc.wait(timeout=CAPTURE_SECONDS + 15)

    stop_process(ff_proc, ff_out, ff_err)
    stop_process(recv_proc, recv_out, recv_err)

    summary = compute_metrics(events, name, "plain_rtp_namespace", profile["description"])
    (OUT_DIR / f"{name}_plain_rtp_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def run_dtls(profile):
    name = profile["name"]
    print(f"\n=== Namespace DTLS-wrapped RTP under {name} ===")

    events = OUT_DIR / f"{name}_dtls_rtp_packet_events.csv"

    run(["./dtls_rtp/build.sh"])

    receiver_cmd = sudo([
        "ip", "netns", "exec", NS_RECEIVER,
        str(PYTHON), str(RECEIVER_SCRIPT),
        "--host", "0.0.0.0",
        "--port", str(RECOVERED_RTP_PORT),
        "--seconds", str(CAPTURE_SECONDS),
        "--out", str(events),
    ])

    server_cmd = sudo([
        "ip", "netns", "exec", NS_RECEIVER,
        str(PROXY),
        "server",
        "0.0.0.0",
        str(DTLS_PORT),
        "127.0.0.1",
        str(RECOVERED_RTP_PORT),
    ])

    client_cmd = sudo([
        "ip", "netns", "exec", NS_SENDER,
        str(PROXY),
        "client",
        RECEIVER_IP,
        str(DTLS_PORT),
        "127.0.0.1",
        str(DTLS_CLIENT_RTP_PORT),
    ])

    ffmpeg_cmd = sudo([
        "ip", "netns", "exec", NS_SENDER,
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "warning",
        "-re",
        "-stream_loop", "-1",
        "-i", str(VIDEO),
        "-an",
        "-c:v", "copy",
        "-f", "rtp",
        f"rtp://127.0.0.1:{DTLS_CLIENT_RTP_PORT}",
    ])

    recv_proc, recv_out, recv_err = start_process(
        receiver_cmd,
        OUT_DIR / f"{name}_dtls_receiver_stdout.log",
        OUT_DIR / f"{name}_dtls_receiver_stderr.log",
    )

    server_proc, server_out, server_err = start_process(
        server_cmd,
        OUT_DIR / f"{name}_dtls_server_stdout.log",
        OUT_DIR / f"{name}_dtls_server_stderr.log",
    )

    time.sleep(1)

    client_proc, client_out, client_err = start_process(
        client_cmd,
        OUT_DIR / f"{name}_dtls_client_stdout.log",
        OUT_DIR / f"{name}_dtls_client_stderr.log",
    )

    time.sleep(2)

    ff_proc, ff_out, ff_err = start_process(
        ffmpeg_cmd,
        OUT_DIR / f"{name}_dtls_ffmpeg_stdout.log",
        OUT_DIR / f"{name}_dtls_ffmpeg_stderr.log",
    )

    recv_proc.wait(timeout=CAPTURE_SECONDS + 20)

    stop_process(ff_proc, ff_out, ff_err)
    stop_process(client_proc, client_out, client_err)
    stop_process(server_proc, server_out, server_err)
    stop_process(recv_proc, recv_out, recv_err)

    summary = compute_metrics(events, name, "dtls_rtp_namespace", profile["description"])
    (OUT_DIR / f"{name}_dtls_rtp_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def write_outputs(rows):
    summary = {
        "experiment": "step93_network_namespace_plain_vs_dtls",
        "topology": {
            "senderNamespace": NS_SENDER,
            "receiverNamespace": NS_RECEIVER,
            "senderIp": SENDER_IP,
            "receiverIp": RECEIVER_IP,
            "vethSender": VETH_SENDER,
            "vethReceiver": VETH_RECEIVER,
        },
        "measurementNote": "Jitter is computed from packet arrival-gap variation. This is safer for H.264 RTP packet ordering than raw RTP timestamp-delta jitter.",
        "captureSeconds": CAPTURE_SECONDS,
        "profiles": PROFILES,
        "rows": rows,
        "files": {
            "summaryJson": str(SUMMARY_JSON.relative_to(ROOT)),
            "summaryCsv": str(SUMMARY_CSV.relative_to(ROOT)),
            "summaryMarkdown": str(SUMMARY_MD.relative_to(ROOT)),
            "packetLossFigure": str(FIG_LOSS.relative_to(ROOT)),
            "bitrateFigure": str(FIG_BITRATE.relative_to(ROOT)),
            "arrivalGapJitterFigure": str(FIG_JITTER.relative_to(ROOT)),
        },
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    with SUMMARY_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "profile",
                "description",
                "mode",
                "receivedPackets",
                "expectedPackets",
                "lostPackets",
                "packetLossPct",
                "avgBitrateKbps",
                "avgJitterMs",
                "p50JitterMs",
                "p95JitterMs",
                "maxJitterMs",
                "medianArrivalGapMs",
                "status",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    md = []
    md.append("# Step 93 Network Namespace: Plain RTP vs DTLS-Wrapped RTP\n")
    md.append("## Purpose\n")
    md.append("This experiment reproduces the Step 91 media-plane impairment matrix using two Linux network namespaces connected by a veth pair.\n")
    md.append("## Namespace Topology\n")
    md.append(f"- Sender namespace: `{NS_SENDER}` with IP `{SENDER_IP}`\n")
    md.append(f"- Receiver namespace: `{NS_RECEIVER}` with IP `{RECEIVER_IP}`\n")
    md.append(f"- Sender veth: `{VETH_SENDER}`\n")
    md.append(f"- Receiver veth: `{VETH_RECEIVER}`\n")
    md.append("## Measurement Note\n")
    md.append("Jitter is computed from packet arrival-gap variation to avoid misleading raw RTP timestamp artefacts from H.264 packet ordering.\n")
    md.append("## Results\n")
    md.append("| Profile | Mode | Packets | Loss % | Bitrate kbps | Avg jitter ms | P50 jitter ms | P95 jitter ms |\n")
    md.append("|---|---|---:|---:|---:|---:|---:|---:|\n")
    for r in rows:
        md.append(
            f"| {r['profile']} | {r['mode']} | {r['receivedPackets']} | "
            f"{r['packetLossPct']} | {r['avgBitrateKbps']} | {r['avgJitterMs']} | "
            f"{r['p50JitterMs']} | {r['p95JitterMs']} |\n"
        )
    md.append("\n## Research Meaning\n")
    md.append("Step 93 strengthens Step 91 by moving the impairment experiment from localhost loopback to an isolated two-namespace topology. This is closer to a real two-node media-plane path and is more suitable for journal evaluation.\n")
    md.append("\n## Boundary\n")
    md.append("This is still a single-machine namespace test. The next stage should reproduce the same matrix across two physical machines, a university testbed, Mininet, or ns-3.\n")
    SUMMARY_MD.write_text("".join(md))

    make_figures(rows)

    print(json.dumps(summary, indent=2))
    print(f"Saved: {SUMMARY_JSON}")


def grouped_bar(rows, metric, ylabel, out_png):
    profiles = [p["name"] for p in PROFILES]
    plain = []
    dtls = []

    for profile in profiles:
        plain_row = next(r for r in rows if r["profile"] == profile and r["mode"] == "plain_rtp_namespace")
        dtls_row = next(r for r in rows if r["profile"] == profile and r["mode"] == "dtls_rtp_namespace")
        plain.append(float(plain_row[metric]))
        dtls.append(float(dtls_row[metric]))

    x = list(range(len(profiles)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([i - width / 2 for i in x], plain, width, label="Plain RTP namespace")
    ax.bar([i + width / 2 for i in x], dtls, width, label="DTLS-wrapped RTP namespace")
    ax.set_xticks(x)
    ax.set_xticklabels(profiles, rotation=20, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(ylabel + " under namespace impairment")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    fig.savefig(out_png, dpi=200)
    fig.savefig(out_png.with_suffix(".pdf"))
    fig.savefig(out_png.with_suffix(".svg"))
    plt.close(fig)


def make_figures(rows):
    grouped_bar(rows, "packetLossPct", "Packet loss (%)", FIG_LOSS)
    grouped_bar(rows, "avgBitrateKbps", "Average bitrate (kbps)", FIG_BITRATE)
    grouped_bar(rows, "avgJitterMs", "Arrival-gap jitter (ms)", FIG_JITTER)


def validate_rows(rows):
    bad = []
    for r in rows:
        if int(r["receivedPackets"]) <= 0:
            bad.append((r["profile"], r["mode"], "no packets"))
        if float(r["avgBitrateKbps"]) <= 0:
            bad.append((r["profile"], r["mode"], "zero bitrate"))
        if float(r["avgJitterMs"]) > 1000:
            bad.append((r["profile"], r["mode"], "jitter unrealistic"))

    if bad:
        print("Validation failed:")
        for item in bad:
            print(item)
        raise SystemExit("STOP: Step 93 produced invalid namespace metrics. Inspect logs before committing.")

    print("OK: Step 93 namespace metrics are valid enough to document and commit.")


def main():
    if not VIDEO.exists():
        raise SystemExit(f"Missing video sample: {VIDEO}")

    if shutil.which("ffmpeg") is None:
        raise SystemExit("Missing ffmpeg")

    if shutil.which("tc") is None:
        raise SystemExit("Missing tc/iproute2")

    write_receiver_script()

    print("[preflight] requesting sudo once for namespace and tc/netem commands")
    run(["sudo", "-v"])

    rows = []

    try:
        setup_namespaces()

        for profile in PROFILES:
            apply_profile(profile)
            rows.append(run_plain(profile))
            rows.append(run_dtls(profile))

        clear_netem()
        validate_rows(rows)
        write_outputs(rows)

    finally:
        print("[cleanup] clearing netem and deleting namespaces")
        clear_netem()
        cleanup_namespaces()


if __name__ == "__main__":
    main()
