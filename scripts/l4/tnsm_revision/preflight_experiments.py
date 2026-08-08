#!/usr/bin/env python3
"""Inventory the frozen R10 oracle experiment and local compute environment.

This command is deliberately read-only.  It records file hashes, structural
schemas, tool versions, hardware capacity, and only the *presence* of provider
environment variables.  It never prints credentials and never calls a model.

The resulting report is the first gate for the TNSM follow-up experiments: no
baseline, open-weights, or injection run should start until the frozen R10
source has been mapped to a canonical, hashed 180-row JSONL file.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


EXPECTED_SCENARIOS = {
    "S1": "S1_compliant_baseline.json",
    "S2": "S2_drb_integrity_disabled.json",
    "S3": "S3_legacy_o1_tls.json",
    "S4": "S4_unauthorised_xapp_actuation.json",
    "S5": "S5_replayed_anchor.json",
    "S6": "S6_insufficient_evidence.json",
}
EXPECTED_MODES = {"NO_RAG", "RAG", "AGENTIC_RAG"}
EXPECTED_DECISIONS = {"COMPLIANT", "NON_COMPLIANT", "UNCERTAIN"}
EXPECTED_ACTIONS = {"AUTOMATIC", "HUMAN", "PRIVILEGED", "NEVER"}
API_ENV_VARS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "MISTRAL_API_KEY",
    "COHERE_API_KEY",
)
CANDIDATE_SUFFIXES = {".json", ".jsonl", ".ndjson", ".csv", ".yaml", ".yml"}
CANDIDATE_TERMS = (
    "attempt",
    "cell",
    "oracle",
    "record",
    "result",
    "scenario",
    "success",
    "summary",
    "manifest",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: list[str], cwd: Path | None = None, timeout: int = 20) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False, "output": None}
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        output = result.stdout.strip()
        return {
            "available": True,
            "exit_code": result.returncode,
            "output": output[:4000] if output else None,
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"available": True, "error": type(error).__name__, "output": None}


def memory_total_mib() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def cpu_model() -> str | None:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except (OSError, IndexError):
        return None
    return platform.processor() or None


def git_snapshot(repo_root: Path) -> dict[str, Any]:
    if not (repo_root / ".git").exists():
        return {"is_git_repository": False}
    commit = run_command(["git", "rev-parse", "HEAD"], cwd=repo_root)
    branch = run_command(["git", "branch", "--show-current"], cwd=repo_root)
    status = run_command(["git", "status", "--porcelain"], cwd=repo_root)
    status_lines = (status.get("output") or "").splitlines()
    return {
        "is_git_repository": True,
        "commit": commit.get("output"),
        "branch": branch.get("output"),
        "dirty": bool(status_lines),
        "changed_path_count": len(status_lines),
    }


def gpu_snapshot() -> dict[str, Any]:
    query = run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total",
            "--format=csv,noheader,nounits",
        ]
    )
    rows: list[dict[str, Any]] = []
    if query.get("exit_code") == 0 and query.get("output"):
        for line in str(query["output"]).splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) == 3:
                try:
                    memory_mib: int | None = int(parts[2])
                except ValueError:
                    memory_mib = None
                rows.append(
                    {"name": parts[0], "driver_version": parts[1], "memory_mib": memory_mib}
                )
    return {"nvidia_smi_available": bool(query.get("available")), "gpus": rows}


def tool_snapshot() -> dict[str, Any]:
    probes = {
        "python3": ["python3", "--version"],
        "git": ["git", "--version"],
        "docker": ["docker", "--version"],
        "docker_compose": ["docker", "compose", "version"],
        "ollama": ["ollama", "--version"],
        "curl": ["curl", "--version"],
    }
    values: dict[str, Any] = {}
    for name, command in probes.items():
        result = run_command(command)
        values[name] = {
            "available": bool(result.get("available") and result.get("exit_code") == 0),
            "version": (result.get("output") or "").splitlines()[0]
            if result.get("output")
            else None,
        }
    return values


def inspect_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        return {"json_type": "object", "top_level_keys": sorted(map(str, value.keys()))}
    if isinstance(value, list):
        keys: set[str] = set()
        for row in value[:200]:
            if isinstance(row, dict):
                keys.update(map(str, row.keys()))
        return {"json_type": "array", "row_count": len(value), "row_keys": sorted(keys)}
    return {"json_type": type(value).__name__}


def inspect_jsonl(path: Path) -> dict[str, Any]:
    count = 0
    keys: set[str] = set()
    parse_errors = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            count += 1
            if count <= 300:
                try:
                    value = json.loads(line)
                    if isinstance(value, dict):
                        keys.update(map(str, value.keys()))
                except json.JSONDecodeError:
                    parse_errors += 1
    return {"row_count": count, "row_keys": sorted(keys), "sample_parse_errors": parse_errors}


def inspect_csv(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        count = sum(1 for _ in reader)
        return {"row_count": count, "columns": reader.fieldnames or []}


def structural_inspection(path: Path) -> dict[str, Any]:
    try:
        if path.suffix == ".json":
            return inspect_json(path)
        if path.suffix in {".jsonl", ".ndjson"}:
            return inspect_jsonl(path)
        if path.suffix == ".csv":
            return inspect_csv(path)
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as error:
        return {"inspection_error": f"{type(error).__name__}: {error}"}
    return {}


def candidate_score(relative: str, size: int) -> tuple[int, int, str]:
    lowered = relative.lower()
    score = sum(3 for term in CANDIDATE_TERMS if term in Path(lowered).name)
    score += sum(1 for term in CANDIDATE_TERMS if term in lowered)
    if lowered.endswith((".jsonl", ".ndjson")):
        score += 8
    if "analysis_oracle_final" in lowered:
        score += 6
    if "raw" in Path(lowered).parts:
        score -= 4
    return (-score, size, relative)


def discover_candidates(base: Path, max_candidates: int, hash_max_bytes: int) -> list[dict[str, Any]]:
    if not base.is_dir():
        return []
    found: list[tuple[str, Path, int]] = []
    for root, directories, files in os.walk(base):
        root_path = Path(root)
        relative_depth = len(root_path.relative_to(base).parts)
        directories[:] = [name for name in directories if not name.startswith(".")]
        if relative_depth >= 7:
            directories[:] = []
        for name in files:
            path = root_path / name
            relative = path.relative_to(base).as_posix()
            lowered = relative.lower()
            if path.suffix.lower() not in CANDIDATE_SUFFIXES:
                continue
            if not any(term in lowered for term in CANDIDATE_TERMS):
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            found.append((relative, path, size))
    found.sort(key=lambda item: candidate_score(item[0], item[2]))
    records: list[dict[str, Any]] = []
    for relative, path, size in found[:max_candidates]:
        record: dict[str, Any] = {
            "relative_path": relative,
            "bytes": size,
            "sha256": sha256_file(path) if size <= hash_max_bytes else None,
            "hash_skipped": size > hash_max_bytes,
        }
        record.update(structural_inspection(path))
        records.append(record)
    return records


def scenario_snapshot(n8n_root: Path) -> dict[str, Any]:
    scenario_dir = n8n_root / "scenarios" / "configs"
    records: list[dict[str, Any]] = []
    missing: list[str] = []
    for scenario_id, filename in EXPECTED_SCENARIOS.items():
        path = scenario_dir / filename
        if not path.is_file():
            missing.append(filename)
            continue
        records.append(
            {
                "scenario_id": scenario_id,
                "relative_path": path.relative_to(n8n_root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                **structural_inspection(path),
            }
        )
    return {
        "directory": str(scenario_dir.resolve()),
        "expected_count": 6,
        "found_count": len(records),
        "missing": missing,
        "files": records,
    }


def validate_canonical_oracle(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"provided": False, "valid": False, "reasons": ["--oracle-jsonl was not provided"]}
    if not path.is_file():
        return {"provided": True, "path": str(path), "valid": False, "reasons": ["file not found"]}

    reasons: list[str] = []
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    reasons.append(f"line {line_number}: expected an object")
                    continue
                rows.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        reasons.append(f"parse error: {type(error).__name__}: {error}")

    required = {
        "cell_id",
        "scenario_id",
        "retrieval_mode",
        "repeat",
        "oracle_decision",
        "oracle_action_class",
    }
    cell_ids: list[str] = []
    decisions: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    modes: Counter[str] = Counter()
    scenario_ids: Counter[str] = Counter()
    repeats: Counter[int] = Counter()
    for index, row in enumerate(rows, 1):
        missing = sorted(required - row.keys())
        if missing:
            reasons.append(f"row {index}: missing {', '.join(missing)}")
        if not (row.get("scenario") or row.get("prompt")):
            reasons.append(f"row {index}: missing scenario or prompt")
        cell_ids.append(str(row.get("cell_id", "")))
        decision = str(row.get("oracle_decision", "")).upper()
        action = str(row.get("oracle_action_class", "")).upper()
        mode = str(row.get("retrieval_mode", "")).upper()
        scenario_id = str(row.get("scenario_id", "")).upper()
        try:
            repeat = int(row.get("repeat", -1))
        except (TypeError, ValueError):
            repeat = -1
        decisions[decision] += 1
        actions[action] += 1
        modes[mode] += 1
        scenario_ids[scenario_id] += 1
        repeats[repeat] += 1

    if len(rows) != 180:
        reasons.append(f"expected 180 rows; found {len(rows)}")
    if len(set(cell_ids)) != len(cell_ids) or "" in cell_ids:
        reasons.append("cell_id values must be non-empty and unique")
    if set(modes) != EXPECTED_MODES or any(value != 60 for value in modes.values()):
        reasons.append(f"expected 60 rows per mode for {sorted(EXPECTED_MODES)}")
    if set(scenario_ids) != set(EXPECTED_SCENARIOS) or any(
        value != 30 for value in scenario_ids.values()
    ):
        reasons.append("expected 30 rows for each scenario S1-S6")
    if set(repeats) != set(range(1, 11)) or any(value != 18 for value in repeats.values()):
        reasons.append("expected repeats 1-10 with 18 rows per repeat")
    if not set(decisions).issubset(EXPECTED_DECISIONS):
        reasons.append(f"unexpected oracle decisions: {sorted(set(decisions) - EXPECTED_DECISIONS)}")
    if not set(actions).issubset(EXPECTED_ACTIONS):
        reasons.append(f"unexpected oracle actions: {sorted(set(actions) - EXPECTED_ACTIONS)}")

    return {
        "provided": True,
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "rows": len(rows),
        "valid": not reasons,
        "reasons": reasons[:30],
        "mode_counts": dict(sorted(modes.items())),
        "scenario_counts": dict(sorted(scenario_ids.items())),
        "repeat_counts": {str(key): value for key, value in sorted(repeats.items())},
        "decision_counts": dict(sorted(decisions.items())),
        "action_counts": dict(sorted(actions.items())),
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    verdict = report["verdict"]
    system = report["system"]
    git = report["git"]
    lines = [
        "# TNSM experiment preflight",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "This is a read-only inventory. It made no provider calls and recorded no secret values.",
        "",
        "## Gate status",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Gate", "Status"],
            [
                ["Frozen experiment directory", "PASS" if verdict["experiment_directory_found"] else "BLOCKED"],
                ["Frozen summary", "PASS" if verdict["frozen_summary_found"] else "BLOCKED"],
                ["Six scenario sources", "PASS" if verdict["six_scenarios_found"] else "BLOCKED"],
                ["Canonical 180-row oracle", "PASS" if verdict["canonical_oracle_valid"] else "BLOCKED"],
                ["Ready for live experiment", "YES" if verdict["ready_for_live_experiment"] else "NO"],
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Frozen source",
            "",
            f"- Experiment: `{report['paths']['experiment_dir']}`",
            f"- Summary: `{report['paths']['summary_file']}`",
            f"- n8n root: `{report['paths']['n8n_root']}`",
            f"- Git branch/commit: `{git.get('branch')}` / `{git.get('commit')}`",
            f"- Git worktree dirty: `{git.get('dirty')}` ({git.get('changed_path_count', 0)} paths)",
            "",
            "## Compute",
            "",
        ]
    )
    gpu_names = ", ".join(
        f"{gpu['name']} ({gpu.get('memory_mib')} MiB)" for gpu in system["gpu"]["gpus"]
    ) or "No NVIDIA GPU reported"
    lines.extend(
        markdown_table(
            ["Item", "Value"],
            [
                ["OS", system["platform"]],
                ["CPU", system.get("cpu_model")],
                ["Logical CPUs", system.get("logical_cpu_count")],
                ["RAM", f"{system.get('memory_total_mib')} MiB"],
                ["GPU", gpu_names],
                ["Free disk at experiment", f"{system.get('experiment_free_mib')} MiB"],
            ],
        )
    )
    lines.extend(["", "## Tool and credential-presence checks", ""])
    tool_rows = [
        [name, "yes" if value["available"] else "no", value.get("version") or ""]
        for name, value in report["tools"].items()
    ]
    lines.extend(markdown_table(["Tool", "Available", "Version"], tool_rows))
    lines.extend(["", "Only presence is shown; no credential value was read into the report.", ""])
    lines.extend(
        markdown_table(
            ["Environment variable", "Present"],
            [[name, "yes" if present else "no"] for name, present in report["api_environment_present"].items()],
        )
    )
    lines.extend(["", "## Scenario sources", ""])
    scenario_rows = [
        [row["scenario_id"], row["relative_path"], row["bytes"], row["sha256"]]
        for row in report["scenarios"]["files"]
    ]
    lines.extend(markdown_table(["ID", "Path", "Bytes", "SHA-256"], scenario_rows))
    if report["scenarios"]["missing"]:
        lines.extend(["", "Missing: " + ", ".join(report["scenarios"]["missing"])])

    lines.extend(["", "## Candidate frozen data files", ""])
    candidate_rows: list[list[Any]] = []
    for row in report["candidate_files"][:60]:
        shape = row.get("row_count")
        keys = row.get("row_keys") or row.get("columns") or row.get("top_level_keys") or []
        candidate_rows.append(
            [
                row["relative_path"],
                row["bytes"],
                "" if shape is None else shape,
                ", ".join(map(str, keys[:12])),
                row.get("sha256") or "hash skipped",
            ]
        )
    lines.extend(markdown_table(["Path", "Bytes", "Rows", "Keys/columns", "SHA-256"], candidate_rows))

    canonical = report["canonical_oracle"]
    lines.extend(["", "## Canonical oracle validation", ""])
    if canonical["provided"]:
        lines.extend(
            [
                f"- Path: `{canonical.get('path')}`",
                f"- SHA-256: `{canonical.get('sha256')}`",
                f"- Rows: `{canonical.get('rows')}`",
                f"- Valid: `{canonical.get('valid')}`",
            ]
        )
    else:
        lines.append("No canonical oracle JSONL was provided yet.")
    if canonical.get("reasons"):
        lines.extend(["", "Blocking reasons:"] + [f"- {reason}" for reason in canonical["reasons"]])
    lines.extend(["", "## Next action", "", verdict["next_action"], ""])
    return "\n".join(lines)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.expanduser().resolve()
    experiment_dir = args.experiment_dir.expanduser().resolve()
    if args.n8n_root:
        n8n_root = args.n8n_root.expanduser().resolve()
    else:
        n8n_root = experiment_dir.parents[2] if len(experiment_dir.parents) >= 3 else experiment_dir
    summary_file = experiment_dir / "analysis_oracle_final" / "summary_by_mode.csv"
    scenarios = scenario_snapshot(n8n_root)
    candidates = discover_candidates(
        experiment_dir,
        max_candidates=args.max_candidates,
        hash_max_bytes=args.hash_max_mib * 1024 * 1024,
    )
    canonical = validate_canonical_oracle(args.oracle_jsonl.expanduser().resolve() if args.oracle_jsonl else None)
    experiment_found = experiment_dir.is_dir()
    summary_found = summary_file.is_file()
    scenarios_found = scenarios["found_count"] == 6
    canonical_valid = bool(canonical["valid"])
    ready = experiment_found and summary_found and scenarios_found and canonical_valid
    if not experiment_found:
        next_action = "Locate the frozen R10 experiment directory; do not run any model experiment."
    elif not scenarios_found:
        next_action = "Locate all six frozen scenario JSON files; do not reconstruct them from the paper."
    elif not canonical_valid:
        next_action = (
            "Send `preflight.md` and `preflight.json` for schema mapping. The next command will export "
            "a canonical 180-row oracle from the hashed frozen files; do not hand-edit or rerun R10."
        )
    else:
        next_action = "The frozen input gate passes; proceed to the external LangGraph baseline."

    usage = shutil.disk_usage(experiment_dir if experiment_found else repo_root)
    report = {
        "schema": "zktrustllm.tnsm.experiment_preflight.v1",
        "generated_at": utc_now(),
        "read_only": True,
        "provider_calls_made": False,
        "paths": {
            "repo_root": str(repo_root),
            "n8n_root": str(n8n_root),
            "experiment_dir": str(experiment_dir),
            "summary_file": str(summary_file),
        },
        "git": git_snapshot(repo_root),
        "system": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_model": cpu_model(),
            "logical_cpu_count": os.cpu_count(),
            "memory_total_mib": memory_total_mib(),
            "experiment_free_mib": usage.free // (1024 * 1024),
            "gpu": gpu_snapshot(),
        },
        "tools": tool_snapshot(),
        "api_environment_present": {name: bool(os.environ.get(name)) for name in API_ENV_VARS},
        "scenarios": scenarios,
        "candidate_files": candidates,
        "canonical_oracle": canonical,
        "verdict": {
            "experiment_directory_found": experiment_found,
            "frozen_summary_found": summary_found,
            "six_scenarios_found": scenarios_found,
            "canonical_oracle_valid": canonical_valid,
            "ready_for_live_experiment": ready,
            "next_action": next_action,
        },
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=Path.home()
        / "Downloads"
        / "deploy"
        / "n8n_l4_parallel"
        / "runtime"
        / "experiments"
        / "l4_oracle_20260716T131803Z_r10",
    )
    parser.add_argument("--n8n-root", type=Path)
    parser.add_argument("--oracle-jsonl", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/out/tnsm_revision/preflight"),
    )
    parser.add_argument("--max-candidates", type=int, default=200)
    parser.add_argument("--hash-max-mib", type=int, default=256)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "preflight.json"
    markdown_path = output_dir / "preflight.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    compact = {
        "preflight_json": str(json_path),
        "preflight_markdown": str(markdown_path),
        "verdict": report["verdict"],
    }
    print(json.dumps(compact, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
