#!/usr/bin/env python3
import json
import os
import pathlib
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

REPO = pathlib.Path(__file__).resolve().parents[3]
EVAL_SCRIPT = REPO / "scripts/n8n/ai_eval/run_stage_ef_multimodel_eval.py"

HOST = "127.0.0.1"
PORT = int(os.getenv("AI_EVAL_SERVER_PORT", "8766"))

ALLOWED_MODES = {"single", "multi", "both"}
ALLOWED_PROVIDERS = {"anthropic", "deepseek", "mistral"}

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
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw)

def safe_int(value, default, minimum=1, maximum=100):
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
                "service": "ZKTrustLLM-Agents Stage E/F AI evaluation server",
                "repo": str(REPO),
                "eval_script_exists": EVAL_SCRIPT.exists(),
                "anthropic_model": os.getenv("ANTHROPIC_MODEL", ""),
                "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
                "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY")),
                "mistral_key_set": bool(os.getenv("MISTRAL_API_KEY")),
            })
            return

        json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path not in {"/run_stage_ef", "/run_claude_pilot"}:
            json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})
            return

        try:
            body = parse_body(self)
        except Exception as e:
            json_response(self, 400, {"ok": False, "error": f"Invalid JSON body: {e}"})
            return

        if path == "/run_claude_pilot":
            mode = "single"
            providers = ["anthropic"]
            single_repeats = 1
            multi_repeats = 1
            out_prefix = body.get("out_prefix", "stage_e_claude_fable5_n8n_pilot")
        else:
            mode = body.get("mode", "both")
            if mode not in ALLOWED_MODES:
                json_response(self, 400, {"ok": False, "error": f"Invalid mode: {mode}"})
                return

            providers_raw = body.get("providers", ["anthropic"])
            if isinstance(providers_raw, str):
                providers = [p.strip() for p in providers_raw.split(",") if p.strip()]
            else:
                providers = [str(p).strip() for p in providers_raw if str(p).strip()]

            bad = [p for p in providers if p not in ALLOWED_PROVIDERS]
            if bad:
                json_response(self, 400, {"ok": False, "error": f"Invalid providers: {bad}"})
                return

            single_repeats = safe_int(body.get("single_repeats", 1), 1, 1, 50)
            multi_repeats = safe_int(body.get("multi_repeats", 1), 1, 1, 50)
            out_prefix = body.get("out_prefix", "")

        cmd = [
            sys.executable,
            str(EVAL_SCRIPT),
            "--mode", mode,
            "--providers", ",".join(providers),
            "--single-repeats", str(single_repeats),
            "--multi-repeats", str(multi_repeats),
        ]

        if out_prefix:
            cmd += ["--out-prefix", out_prefix]

        env = os.environ.copy()

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(REPO),
                env=env,
                text=True,
                capture_output=True,
                timeout=3600,
            )
        except subprocess.TimeoutExpired:
            json_response(self, 504, {
                "ok": False,
                "error": "Stage E/F evaluation timed out",
                "cmd": cmd,
            })
            return

        payload = {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "cmd": cmd,
            "stdout": proc.stdout[-12000:],
            "stderr": proc.stderr[-12000:],
            "claim_boundary": (
                "This evaluates AI-model/tool and multi-agent orchestration behaviour around the local "
                "ZKTrustLLM-Agents L4 n8n artifact. It is not production O-RAN deployment, "
                "packet-capture network benchmarking, public-chain benchmarking, or full media-plane QoE validation."
            ),
        }

        json_response(self, 200 if proc.returncode == 0 else 500, payload)

def main():
    if not EVAL_SCRIPT.exists():
        raise SystemExit(f"Missing evaluator script: {EVAL_SCRIPT}")

    server = HTTPServer((HOST, PORT), Handler)
    print(f"Stage E/F AI evaluation server running at http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  GET  /health")
    print("  POST /run_claude_pilot")
    print("  POST /run_stage_ef")
    server.serve_forever()

if __name__ == "__main__":
    main()
