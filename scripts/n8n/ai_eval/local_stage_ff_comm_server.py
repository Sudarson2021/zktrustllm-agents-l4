#!/usr/bin/env python3
import json
import os
import pathlib
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

REPO = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts/n8n/ai_eval/run_stage_ff_four_model_comm.py"

HOST = "127.0.0.1"
PORT = int(os.getenv("STAGE_FF_SERVER_PORT", "8767"))

def json_response(handler, status, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

def parse_body(handler):
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length == 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))

def safe_int(value, default, minimum=1, maximum=20):
    try:
        value = int(value)
    except Exception:
        return default
    return max(minimum, min(maximum, value))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            json_response(self, 200, {
                "ok": True,
                "service": "Stage F/F four-model intercommunication server",
                "repo": str(REPO),
                "script_exists": SCRIPT.exists(),
                "openai_model": os.getenv("OPENAI_MODEL", ""),
                "anthropic_model": os.getenv("ANTHROPIC_MODEL", ""),
                "deepseek_model": os.getenv("DEEPSEEK_MODEL", ""),
                "mistral_model": os.getenv("MISTRAL_MODEL", ""),
                "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
                "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
                "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY")),
                "mistral_key_set": bool(os.getenv("MISTRAL_API_KEY")),
            })
            return

        json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/run_stage_ff":
            json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})
            return

        try:
            body = parse_body(self)
        except Exception as e:
            json_response(self, 400, {"ok": False, "error": f"Invalid JSON body: {e}"})
            return

        repeats = safe_int(body.get("repeats", 1), 1, 1, 20)
        out_prefix = str(body.get("out_prefix", "")).strip()

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--repeats", str(repeats),
        ]

        if out_prefix:
            cmd += ["--out-prefix", out_prefix]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(REPO),
                env=os.environ.copy(),
                text=True,
                capture_output=True,
                timeout=7200,
            )
        except subprocess.TimeoutExpired:
            json_response(self, 504, {
                "ok": False,
                "error": "Stage F/F four-model communication run timed out",
                "cmd": cmd,
            })
            return

        payload = {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "cmd": cmd,
            "stdout": proc.stdout[-16000:],
            "stderr": proc.stderr[-16000:],
            "claim_boundary": (
                "This Stage F/F workflow evaluates inter-AI model communication around the local "
                "ZKTrustLLM-Agents L4 evidence artifact. It is not production O-RAN deployment validation, "
                "packet-capture network benchmarking, public-chain benchmarking, full media-plane QoE validation, "
                "or a 240-run six-variant ablation."
            ),
        }

        json_response(self, 200 if proc.returncode == 0 else 500, payload)

def main():
    if not SCRIPT.exists():
        raise SystemExit(f"Missing script: {SCRIPT}")

    server = HTTPServer((HOST, PORT), Handler)
    print(f"Stage F/F four-model communication server running at http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  GET  /health")
    print("  POST /run_stage_ff")
    server.serve_forever()

if __name__ == "__main__":
    main()
