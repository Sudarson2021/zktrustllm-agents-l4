#!/usr/bin/env python3
import json
import pathlib
import subprocess
import html
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

REPO_DIR = pathlib.Path("/home/sk02352/zktrustllm-agents-l4").resolve()
PORT = 8765

ALLOWED_VARIANTS = {"full-l4", "oracle-only", "no-ipfs", "no-zk", "rbac-only", "no-policy-gate"}
ALLOWED_PROFILES = {"clean", "delay", "delay_jitter", "delay_jitter_loss"}

OUT_DIR = REPO_DIR / "artifacts" / "out" / "n8n"
OUT_DIR.mkdir(parents=True, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/run":
            return self.handle_run()
        if self.path == "/save_reflection":
            return self.handle_save_reflection()
        self._send(404, {"error": "Supported endpoints: /run, /save_reflection"})

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode())

    def handle_run(self):
        try:
            data = self.read_json()
        except Exception as e:
            self._send(400, {"error": f"Invalid JSON: {e}"})
            return

        variant = data.get("variant")
        profile = data.get("profile")
        repeat = str(data.get("repeat", "1"))
        run_id = data.get("run_id")

        if variant not in ALLOWED_VARIANTS:
            self._send(400, {"error": "Invalid variant", "variant": variant})
            return

        if profile not in ALLOWED_PROFILES:
            self._send(400, {"error": "Invalid profile", "profile": profile})
            return

        if not run_id or "/" in run_id or ".." in run_id:
            self._send(400, {"error": "Invalid run_id", "run_id": run_id})
            return

        cmd = ["bash", "scripts/n8n/run_one_eval.sh", variant, profile, repeat, run_id]

        result = subprocess.run(
            cmd,
            cwd=str(REPO_DIR),
            capture_output=True,
            text=True,
            timeout=1800
        )

        manifest_path = OUT_DIR / "runs" / run_id / "manifest.json"

        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
        else:
            manifest = {
                "run_id": run_id,
                "variant": variant,
                "profile": profile,
                "repeat": repeat,
                "status": "NO_MANIFEST",
                "exit_code": result.returncode
            }

        self._send(200, {
            "runner_status": "ok",
            "return_code": result.returncode,
            "manifest": manifest,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:]
        })

    def handle_save_reflection(self):
        try:
            data = self.read_json()
        except Exception as e:
            self._send(400, {"error": f"Invalid JSON: {e}"})
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = OUT_DIR / f"reviewer_reflection_{ts}.json"
        html_path = OUT_DIR / f"reviewer_reflection_{ts}.html"

        json_path.write_text(json.dumps(data, indent=2))

        reflection = data.get("reviewer_reflection", {})
        supervisor_summary = reflection.get("supervisor_summary", "")
        reviewer_warning = reflection.get("reviewer_warning", "")
        recommended_next_step = reflection.get("recommended_next_step", "")
        overclaiming_risks = reflection.get("overclaiming_risks", [])

        html_page = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>ZKTrustLLM-Agents L4 Reviewer Reflection</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.5; }}
.card {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 18px; }}
pre {{ background: #f6f6f6; padding: 12px; overflow-x: auto; }}
</style>
</head>
<body>
<h1>ZKTrustLLM-Agents L4 Reviewer Reflection</h1>

<div class="card">
<h2>Supervisor Summary</h2>
<p>{html.escape(str(supervisor_summary))}</p>
</div>

<div class="card">
<h2>Reviewer Warning</h2>
<p>{html.escape(str(reviewer_warning))}</p>
</div>

<div class="card">
<h2>Recommended Next Step</h2>
<p>{html.escape(str(recommended_next_step))}</p>
</div>

<div class="card">
<h2>Overclaiming Risks</h2>
<ul>
{''.join(f"<li>{html.escape(str(r))}</li>" for r in overclaiming_risks)}
</ul>
</div>

<div class="card">
<h2>Full JSON Evidence</h2>
<pre>{html.escape(json.dumps(data, indent=2))}</pre>
</div>

</body>
</html>
"""
        html_path.write_text(html_page)

        self._send(200, {
            "save_status": "ok",
            "json_path": str(json_path),
            "html_path": str(html_path)
        })

if __name__ == "__main__":
    print(f"Starting local ZKTrustLLM n8n runner on http://127.0.0.1:{PORT}")
    print(f"Repo: {REPO_DIR}")
    print("Endpoints: POST /run, POST /save_reflection")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
