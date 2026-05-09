#!/usr/bin/env python3

"""
ZKTrustLLM-Agents L4 Full Agentic Automation Suite.

Purpose:
- Run the major Level 4 control-plane and media-plane experiments.
- Validate generated JSON and KPI outputs.
- Produce a machine-readable automation manifest.
- Produce a supervisor-readable Markdown progress report.
- Keep privileged network experiments optional through --include-privileged.

This is the first step toward a minimally supervised agentic experiment workflow.
"""

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "l4_agentic_automation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR = OUT_DIR / f"run_{RUN_ID}"
RUN_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR = RUN_DIR / "clean_media_snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_JSON = OUT_DIR / "agentic_automation_summary.json"
SUMMARY_MD = OUT_DIR / "agentic_automation_summary.md"
MANIFEST_CSV = OUT_DIR / "agentic_automation_artifact_manifest.csv"

PYTHON = sys.executable


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(label, cmd, timeout=1800, allow_fail=False):
    stdout_path = RUN_DIR / f"{label}.stdout.log"
    stderr_path = RUN_DIR / f"{label}.stderr.log"

    start = time.time()
    print(f"\n=== {label} ===")
    print("+ " + " ".join(str(x) for x in cmd))

    with stdout_path.open("w") as out, stderr_path.open("w") as err:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            stdout=out,
            stderr=err,
            text=True,
            timeout=timeout,
        )

    duration = round(time.time() - start, 3)

    result = {
        "label": label,
        "cmd": cmd,
        "returncode": proc.returncode,
        "durationSeconds": duration,
        "stdout": rel(stdout_path),
        "stderr": rel(stderr_path),
        "ok": proc.returncode == 0,
    }

    if proc.returncode != 0 and not allow_fail:
        result["error"] = f"Command failed with return code {proc.returncode}"
        print(f"FAILED: {label} returncode={proc.returncode}")
    else:
        print(f"OK: {label} duration={duration}s returncode={proc.returncode}")

    return result


def binary_exists(name):
    return shutil.which(name) is not None


def validate_json_file(path: Path):
    if not path.exists():
        return {"path": rel(path), "ok": False, "error": "missing"}
    try:
        with path.open() as f:
            data = json.load(f)
        return {"path": rel(path), "ok": True, "data": data}
    except Exception as e:
        return {"path": rel(path), "ok": False, "error": str(e)}


def get_nested(d, keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def validate_media_summary(path: Path, max_loss=50.0, max_jitter=1000.0):
    item = validate_json_file(path)
    checks = []

    if not item["ok"]:
        return {"path": rel(path), "ok": False, "checks": [{"name": "json", "ok": False, "detail": item.get("error")}]}

    d = item["data"]
    packets = int(d.get("receivedPackets", 0))
    bitrate = float(d.get("avgBitrateKbps", 0.0))
    loss = float(get_nested(d, ["packetLoss", "packet_loss_pct"], 0.0))
    jitter = float(get_nested(d, ["jitter", "avgJitterComponentMs"], 0.0))

    checks.append({"name": "received_packets_positive", "ok": packets > 0, "value": packets})
    checks.append({"name": "bitrate_positive", "ok": bitrate > 0, "value": bitrate})
    checks.append({"name": "packet_loss_reasonable", "ok": loss <= max_loss, "value": loss})
    checks.append({"name": "jitter_reasonable", "ok": jitter <= max_jitter, "value": jitter})

    return {"path": rel(path), "ok": all(c["ok"] for c in checks), "checks": checks}


def validate_matrix_summary(path: Path, max_jitter=1000.0):
    item = validate_json_file(path)
    checks = []

    if not item["ok"]:
        return {"path": rel(path), "ok": False, "checks": [{"name": "json", "ok": False, "detail": item.get("error")}]}

    d = item["data"]
    rows = d.get("rows", [])

    checks.append({"name": "has_rows", "ok": len(rows) > 0, "value": len(rows)})

    for idx, r in enumerate(rows):
        packets = int(r.get("receivedPackets", 0))
        bitrate = float(r.get("avgBitrateKbps", 0.0))
        jitter = float(r.get("avgJitterMs", 0.0))
        checks.append({"name": f"row_{idx}_packets_positive", "ok": packets > 0, "value": packets})
        checks.append({"name": f"row_{idx}_bitrate_positive", "ok": bitrate > 0, "value": bitrate})
        checks.append({"name": f"row_{idx}_jitter_reasonable", "ok": jitter <= max_jitter, "value": jitter})

    return {"path": rel(path), "ok": all(c["ok"] for c in checks), "checks": checks}


def collect_artifacts():
    patterns = [
        "results/l4_mcp_server/*.json",
        "results/l4_live_telemetry/*",
        "results/l4_multi_agent_scaling/*",
        "results/l4_live_rtp_media/*",
        "results/l4_dtls_rtp_media/*",
        "results/l4_network_impairment/*",
        "results/l4_namespace_impairment/*",
        "docs/l4/**/*.md",
        "docs/report/*.md",
        "docs/roadmap/*.md",
        "docs/progress/*.md",
    ]

    rows = []
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if not path.is_file():
                continue
            rows.append({
                "path": rel(path),
                "sizeBytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })

    rows.sort(key=lambda x: x["path"])

    with MANIFEST_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "sizeBytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    return rows


def write_markdown(summary):
    lines = []
    lines.append("# Step 96 L4 Agentic Automation Suite Summary\n")
    lines.append(f"- Run ID: `{summary['runId']}`")
    lines.append(f"- Started: `{summary['startedAt']}`")
    lines.append(f"- Finished: `{summary['finishedAt']}`")
    lines.append(f"- Overall status: **{summary['overallStatus']}**")
    lines.append(f"- Privileged network experiments included: `{summary['includePrivileged']}`\n")

    lines.append("## Executed Steps\n")
    lines.append("| Step | Status | Duration s | Output logs |")
    lines.append("|---|---:|---:|---|")
    for r in summary["executedSteps"]:
        status = "PASS" if r["ok"] else "FAIL"
        lines.append(f"| {r['label']} | {status} | {r['durationSeconds']} | `{r['stdout']}`, `{r['stderr']}` |")

    lines.append("\n## Validation Results\n")
    lines.append("| Artifact | Status | Key checks |")
    lines.append("|---|---:|---|")
    for v in summary["validations"]:
        status = "PASS" if v["ok"] else "FAIL"
        check_text = "; ".join(
            f"{c['name']}={c.get('value', c.get('detail', ''))} ({'ok' if c['ok'] else 'bad'})"
            for c in v.get("checks", [])[:6]
        )
        lines.append(f"| `{v['path']}` | {status} | {check_text} |")

    lines.append("\n## Research Meaning\n")
    lines.append(
        "Step 96 converts the previously manual Level 4 workflow into a repeatable "
        "agentic automation suite. It orchestrates proof-governed MCP/A2A control-plane "
        "tests, scaling experiments, live RTP media-plane validation, DTLS-wrapped RTP "
        "validation, and optional network impairment experiments."
    )

    lines.append("\n## Supervisor-Ready Progress View\n")
    lines.append("- Control-plane automation: MCP/A2A tool calls, reference verification, and KPI extraction.")
    lines.append("- Agent scaling automation: repeated multi-agent MCP/A2A coordination measurements.")
    lines.append("- Media-plane automation: RTP and DTLS-wrapped RTP packet telemetry.")
    lines.append("- Network automation: optional `tc netem` and namespace-based impairment matrices.")
    lines.append("- Documentation automation: JSON, CSV, Markdown, figures, and artifact manifests.")

    lines.append("\n## Next Step: Step 97\n")
    lines.append(
        "Implement a closed-loop decision agent that reads current KPI summaries, compares "
        "them against thresholds, and automatically decides whether to run baseline RTP, "
        "DTLS-RTP, impairment, namespace, or report-generation workflows."
    )

    lines.append("\n## Artifact Manifest\n")
    lines.append(f"- Manifest CSV: `{rel(MANIFEST_CSV)}`")
    lines.append(f"- Run logs folder: `{rel(RUN_DIR)}`")

    SUMMARY_MD.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-privileged",
        action="store_true",
        help="Run sudo/tc/netns experiments for Step 91 and Step 93.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue executing later steps even if one step fails.",
    )
    args = parser.parse_args()

    started = now_iso()
    executed = []
    validations = []

    preflight = {
        "python": sys.version.split()[0],
        "root": str(ROOT),
        "binaries": {
            "ffmpeg": binary_exists("ffmpeg"),
            "ffprobe": binary_exists("ffprobe"),
            "tc": binary_exists("tc"),
            "ip": binary_exists("ip"),
            "cvlc": binary_exists("cvlc"),
        },
        "requiredFiles": {
            "dtlsProxySource": (ROOT / "dtls_rtp" / "dtls_rtp_proxy.c").exists(),
            "mediaSample": (ROOT / "media_samples" / "l4_test_video_30s.mp4").exists(),
        },
    }

    (RUN_DIR / "preflight.json").write_text(json.dumps(preflight, indent=2))

    required_missing = []
    for name in ["ffmpeg", "ffprobe"]:
        if not preflight["binaries"][name]:
            required_missing.append(name)

    if required_missing:
        print(f"Missing required binaries: {required_missing}")
        sys.exit(1)

    steps = [
        {
            "label": "step79_mcp_tool_test",
            "cmd": [PYTHON, "scripts/l4/test_mcp_l4_server.py"],
            "timeout": 900,
            "enabled": (ROOT / "scripts/l4/test_mcp_l4_server.py").exists(),
        },
        {
            "label": "step86_semi_live_control_telemetry",
            "cmd": [PYTHON, "scripts/l4/run_l4_semi_live_control_telemetry.py"],
            "timeout": 900,
            "enabled": (ROOT / "scripts/l4/run_l4_semi_live_control_telemetry.py").exists(),
        },
        {
            "label": "step87_multi_agent_scaling",
            "cmd": [PYTHON, "scripts/l4/run_l4_multi_agent_scaling_telemetry.py"],
            "timeout": 1200,
            "enabled": (ROOT / "scripts/l4/run_l4_multi_agent_scaling_telemetry.py").exists(),
        },
        {
            "label": "step89_live_rtp_media",
            "cmd": [PYTHON, "scripts/l4/run_live_rtp_media_telemetry.py"],
            "timeout": 900,
            "enabled": (ROOT / "scripts/l4/run_live_rtp_media_telemetry.py").exists(),
        },
        {
            "label": "step90_build_dtls_proxy",
            "cmd": ["./dtls_rtp/build.sh"],
            "timeout": 300,
            "enabled": (ROOT / "dtls_rtp/build.sh").exists(),
        },
        {
            "label": "step90_dtls_rtp_media",
            "cmd": [PYTHON, "scripts/l4/run_dtls_rtp_media_telemetry.py"],
            "timeout": 900,
            "enabled": (ROOT / "scripts/l4/run_dtls_rtp_media_telemetry.py").exists(),
        },
        {
            "label": "step90_recompute_arrival_jitter",
            "cmd": [PYTHON, "scripts/l4/recompute_dtls_rtp_arrival_jitter.py"],
            "timeout": 300,
            "enabled": (ROOT / "scripts/l4/recompute_dtls_rtp_arrival_jitter.py").exists(),
        },
        {
            "label": "step91_loopback_network_impairment",
            "cmd": [PYTHON, "scripts/l4/run_step91_network_impairment_matrix.py"],
            "timeout": 3600,
            "enabled": args.include_privileged and (ROOT / "scripts/l4/run_step91_network_impairment_matrix.py").exists(),
        },
        {
            "label": "step93_namespace_network_impairment",
            "cmd": [PYTHON, "scripts/l4/run_step93_namespace_impairment_matrix.py"],
            "timeout": 3600,
            "enabled": args.include_privileged and (ROOT / "scripts/l4/run_step93_namespace_impairment_matrix.py").exists(),
        },
    ]

    snapshot_paths = {}

    for step in steps:
        if not step["enabled"]:
            executed.append({
                "label": step["label"],
                "cmd": step["cmd"],
                "returncode": None,
                "durationSeconds": 0,
                "stdout": "",
                "stderr": "",
                "ok": True,
                "skipped": True,
            })
            print(f"SKIP: {step['label']}")
            continue

        result = run_cmd(
            step["label"],
            step["cmd"],
            timeout=step["timeout"],
            allow_fail=args.continue_on_error,
        )
        executed.append(result)

        # Snapshot clean standalone media results before privileged impairment
        # experiments overwrite the latest RTP/DTLS result folders.
        if result["ok"] and step["label"] == "step89_live_rtp_media":
            src = ROOT / "results/l4_live_rtp_media/rtp_media_summary.json"
            if src.exists():
                dst = SNAPSHOT_DIR / "clean_plain_rtp_media_summary.json"
                shutil.copy2(src, dst)
                snapshot_paths["plain_rtp_clean"] = dst

        if result["ok"] and step["label"] == "step90_recompute_arrival_jitter":
            src = ROOT / "results/l4_dtls_rtp_media/dtls_rtp_media_summary.json"
            if src.exists():
                dst = SNAPSHOT_DIR / "clean_dtls_rtp_media_summary.json"
                shutil.copy2(src, dst)
                snapshot_paths["dtls_rtp_clean"] = dst

        if not result["ok"] and not args.continue_on_error:
            break

    json_validations = [
        ROOT / "results/l4_mcp_server/mcp_tool_test_results.json",
        ROOT / "results/l4_live_telemetry/semi_live_control_summary.json",
        ROOT / "results/l4_multi_agent_scaling/multi_agent_scaling_summary.json",
    ]

    for path in json_validations:
        if path.exists():
            v = validate_json_file(path)
            validations.append({
                "path": v["path"],
                "ok": v["ok"],
                "checks": [{"name": "json_valid", "ok": v["ok"], "detail": v.get("error", "valid")}],
            })

    media_validations = [
        snapshot_paths.get("plain_rtp_clean", ROOT / "results/l4_live_rtp_media/rtp_media_summary.json"),
        snapshot_paths.get("dtls_rtp_clean", ROOT / "results/l4_dtls_rtp_media/dtls_rtp_media_summary.json"),
    ]

    for path in media_validations:
        if path.exists():
            validations.append(validate_media_summary(path))

    matrix_validations = [
        ROOT / "results/l4_network_impairment/network_impairment_summary.json",
        ROOT / "results/l4_namespace_impairment/namespace_impairment_summary.json",
    ]

    for path in matrix_validations:
        if path.exists():
            validations.append(validate_matrix_summary(path))

    artifacts = collect_artifacts()

    failed_steps = [x for x in executed if not x.get("ok", False)]
    failed_validations = [x for x in validations if not x.get("ok", False)]

    overall = "PASS" if not failed_steps and not failed_validations else "REVIEW_REQUIRED"

    summary = {
        "experiment": "step96_l4_agentic_automation_suite",
        "runId": RUN_ID,
        "startedAt": started,
        "finishedAt": now_iso(),
        "includePrivileged": args.include_privileged,
        "overallStatus": overall,
        "executedSteps": executed,
        "validations": validations,
        "artifactCount": len(artifacts),
        "artifactManifestCsv": rel(MANIFEST_CSV),
        "runDirectory": rel(RUN_DIR),
        "nextRecommendedStep": "Step 97 closed-loop KPI-driven agentic decision controller",
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))
    write_markdown(summary)

    print(json.dumps({
        "experiment": summary["experiment"],
        "runId": summary["runId"],
        "overallStatus": summary["overallStatus"],
        "summaryJson": rel(SUMMARY_JSON),
        "summaryMarkdown": rel(SUMMARY_MD),
        "artifactManifestCsv": rel(MANIFEST_CSV),
        "runDirectory": rel(RUN_DIR),
    }, indent=2))

    if overall != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
