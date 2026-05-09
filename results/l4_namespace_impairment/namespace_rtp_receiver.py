#!/usr/bin/env python3

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
