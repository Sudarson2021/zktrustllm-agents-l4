#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUT="$ROOT/artifacts/out/paper_258/media_capture"

mkdir -p "$OUT"

PORT="${PORT:-19001}"
DURATION_SEC="${DURATION_SEC:-5}"
COUNT="${COUNT:-200}"

PCAP="$OUT/loopback_udp_telemetry.pcapng"
SUMMARY="$OUT/packet_telemetry_summary.json"

if ! command -v tshark >/dev/null 2>&1; then
  python3 - <<PY
import json, pathlib, time
path = pathlib.Path("$SUMMARY")
path.write_text(json.dumps({
  "status": "SKIPPED_TOOL_MISSING",
  "tool": "tshark",
  "claim_boundary": "No packet-capture claim may be made from this run.",
  "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}, indent=2) + "\n")
PY
  echo "[SKIP] tshark not installed"
  exit 0
fi

cat > "$OUT/udp_sender.py" <<'PY_SENDER'
import json
import os
import pathlib
import socket
import time

port = int(os.environ.get("PORT", "19001"))
count = int(os.environ.get("COUNT", "200"))
interval = float(os.environ.get("INTERVAL", "0.01"))
out_dir = pathlib.Path(os.environ["OUT"])
manifest = out_dir / "udp_sender_manifest.json"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sent = []

for i in range(count):
    ts = time.time()
    payload = json.dumps({
        "seq": i,
        "ts": ts,
        "kind": "zktrustllm_l4_telemetry_smoke"
    }).encode("utf-8")
    sock.sendto(payload, ("127.0.0.1", port))
    sent.append({"seq": i, "ts": ts, "bytes": len(payload)})
    time.sleep(interval)

manifest.write_text(json.dumps({
    "status": "SENT",
    "dst": "127.0.0.1",
    "port": port,
    "sent_packets": len(sent),
    "first_ts": sent[0]["ts"] if sent else None,
    "last_ts": sent[-1]["ts"] if sent else None
}, indent=2) + "\n")
PY_SENDER

echo "[RUN] tshark capture on loopback UDP port $PORT"

rm -f "$PCAP"

set +e
tshark -i lo -f "udp port $PORT" -a duration:$((DURATION_SEC + 2)) -w "$PCAP" >/dev/null 2>"$OUT/tshark_capture.stderr.log" &
TSHARK_PID=$!

sleep 1

OUT="$OUT" PORT="$PORT" COUNT="$COUNT" python3 "$OUT/udp_sender.py" >"$OUT/udp_sender.stdout.log" 2>"$OUT/udp_sender.stderr.log"

wait "$TSHARK_PID"
CAP_RC=$?
set -e

python3 - <<PY
import json
import pathlib
import statistics
import subprocess
import time

out_dir = pathlib.Path("$OUT")
pcap = pathlib.Path("$PCAP")
summary = pathlib.Path("$SUMMARY")
sent_manifest = out_dir / "udp_sender_manifest.json"

result = {
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "experiment": "loopback_udp_direct_telemetry_packet_capture_smoke",
    "interface": "lo",
    "udp_port": int("$PORT"),
    "duration_sec_configured": int("$DURATION_SEC"),
    "claim_boundary": "This is direct telemetry packet-capture smoke evidence, not production O-RAN, not DTLS-RTP QoE, and not public-chain evidence.",
    "pcap_path": str(pcap),
    "capture_return_code": int("$CAP_RC")
}

if sent_manifest.exists():
    result["sender_manifest"] = json.loads(sent_manifest.read_text())

if not pcap.exists() or pcap.stat().st_size == 0:
    result["status"] = "CAPTURE_FAILED_OR_EMPTY"
    result["captured_packets"] = 0
    summary.write_text(json.dumps(result, indent=2) + "\n")
    raise SystemExit(0)

cmd = [
    "tshark",
    "-r",
    str(pcap),
    "-Y",
    "udp.dstport == " + str(int("$PORT")),
    "-T",
    "fields",
    "-e",
    "frame.time_epoch",
    "-e",
    "frame.len"
]

proc = subprocess.run(cmd, text=True, capture_output=True)

times = []
lengths = []

for line in proc.stdout.splitlines():
    parts = line.split()
    if len(parts) >= 2:
        try:
            times.append(float(parts[0]))
            lengths.append(int(parts[1]))
        except Exception:
            pass

interarrival = [b - a for a, b in zip(times, times[1:])]

result.update({
    "status": "CAPTURED" if times else "NO_FILTERED_PACKETS",
    "captured_packets": len(times),
    "capture_file_bytes": pcap.stat().st_size,
    "first_capture_ts": times[0] if times else None,
    "last_capture_ts": times[-1] if times else None,
    "capture_span_sec": (times[-1] - times[0]) if len(times) > 1 else 0,
    "mean_frame_len_bytes": statistics.mean(lengths) if lengths else None,
    "mean_interarrival_ms": statistics.mean(interarrival) * 1000 if interarrival else None,
    "stdev_interarrival_ms": statistics.pstdev(interarrival) * 1000 if len(interarrival) > 1 else None
})

summary.write_text(json.dumps(result, indent=2) + "\n")
PY

cat "$SUMMARY"
