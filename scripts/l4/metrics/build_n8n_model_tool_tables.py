#!/usr/bin/env python3
"""Build paper-ready tables from live multi-model n8n scenario records.

Input is the JSONL written by scripts/l4/n8n/run_multi_model_tool_scenarios.py.
The script does not invent missing values: skipped providers are reported in the
coverage file but excluded from the live-results LaTeX table.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


LIVE_PREFIX = "COMPLETED"


def safe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def mean(values: List[float]) -> Optional[float]:
    return statistics.mean(values) if values else None


def p50(values: List[float]) -> Optional[float]:
    return statistics.median(values) if values else None


def p95(values: List[float]) -> Optional[float]:
    if not values:
        return None
    values = sorted(values)
    index = int(round(0.95 * (len(values) - 1)))
    return values[index]


def pct(numer: int, denom: int) -> Optional[float]:
    if denom == 0:
        return None
    return 100.0 * numer / denom


def fmt(value: Optional[float], digits: int = 1) -> str:
    if value is None:
        return "--"
    return f"{value:.{digits}f}"


def load_records(path: pathlib.Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not path.exists():
        raise SystemExit(f"Input JSONL not found: {path}")
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                records.append(row)
        except Exception as exc:
            raise SystemExit(f"Invalid JSONL at {path}:{lineno}: {exc}") from exc
    return records


def group_records(records: List[Dict[str, Any]]) -> Dict[Tuple[str, str, str], List[Dict[str, Any]]]:
    groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for r in records:
        groups[(str(r.get("provider", "unknown")), str(r.get("model", "unknown")), str(r.get("tool_scenario", "unknown")))].append(r)
    return groups


def summarise_group(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    requested = len(rows)
    live = [r for r in rows if str(r.get("status", "")).startswith(LIVE_PREFIX)]
    latencies = [safe_float(r.get("latency_ms")) for r in live]
    latencies = [v for v in latencies if v is not None]
    output_chars = [safe_float(r.get("output_chars")) for r in live]
    output_chars = [v for v in output_chars if v is not None]
    out_tokens = [safe_float(r.get("output_tokens")) for r in live]
    out_tokens = [v for v in out_tokens if v is not None]

    return {
        "requested_runs": requested,
        "live_runs": len(live),
        "skipped_no_api_key": sum(1 for r in rows if r.get("status") == "SKIPPED_NO_API_KEY"),
        "failed_runs": requested - len(live) - sum(1 for r in rows if r.get("status") == "SKIPPED_NO_API_KEY"),
        "validator_pass_runs": sum(1 for r in live if r.get("validator_pass") is True),
        "json_parse_runs": sum(1 for r in live if r.get("json_parse_ok") is True),
        "schema_ok_runs": sum(1 for r in live if r.get("schema_ok") is True),
        "claim_boundary_match_runs": sum(1 for r in live if r.get("claim_boundary_ok_matches_expected") is True),
        "action_ladder_violations": sum(int(r.get("action_ladder_violation_count") or 0) for r in live),
        "mean_latency_ms": mean(latencies),
        "p50_latency_ms": p50(latencies),
        "p95_latency_ms": p95(latencies),
        "mean_output_chars": mean(output_chars),
        "mean_output_tokens": mean(out_tokens),
    }


def build_summaries(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for (provider, model, tool), rows in sorted(group_records(records).items()):
        summary = summarise_group(rows)
        summary.update({"provider": provider, "model": model, "tool_scenario": tool})
        live_runs = int(summary["live_runs"])
        summary["validator_pass_pct"] = pct(int(summary["validator_pass_runs"]), live_runs)
        summary["json_parse_pct"] = pct(int(summary["json_parse_runs"]), live_runs)
        summary["schema_ok_pct"] = pct(int(summary["schema_ok_runs"]), live_runs)
        summary["claim_boundary_match_pct"] = pct(int(summary["claim_boundary_match_runs"]), live_runs)
        out.append(summary)
    return out


def write_csv(path: pathlib.Path, summaries: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "provider", "model", "tool_scenario", "requested_runs", "live_runs", "skipped_no_api_key", "failed_runs",
        "validator_pass_runs", "validator_pass_pct", "json_parse_pct", "schema_ok_pct", "claim_boundary_match_pct",
        "action_ladder_violations", "mean_latency_ms", "p50_latency_ms", "p95_latency_ms", "mean_output_chars", "mean_output_tokens",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in summaries:
            writer.writerow({k: s.get(k) for k in fields})


def write_markdown(path: pathlib.Path, summaries: List[Dict[str, Any]], total_records: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Multi-Model n8n Tool-Scenario Results",
        "",
        f"Generated at: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}",
        f"Input records: {total_records}",
        "",
        "Only live rows with raw provider responses are paper evidence. `SKIPPED_NO_API_KEY` rows document missing credentials and are not reported as model results.",
        "",
        "| Provider | Model | Tool scenario | Live runs | Validator pass % | JSON % | Schema % | Claim-boundary match % | Ladder violations | Mean latency ms | p95 latency ms | Mean output tokens |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        if int(s["live_runs"]) == 0:
            continue
        lines.append(
            "| {provider} | `{model}` | {tool} | {live} | {pass_pct} | {json_pct} | {schema_pct} | {boundary_pct} | {violations} | {mean_lat} | {p95_lat} | {mean_tokens} |".format(
                provider=s["provider"],
                model=s["model"],
                tool=s["tool_scenario"],
                live=s["live_runs"],
                pass_pct=fmt(s.get("validator_pass_pct")),
                json_pct=fmt(s.get("json_parse_pct")),
                schema_pct=fmt(s.get("schema_ok_pct")),
                boundary_pct=fmt(s.get("claim_boundary_match_pct")),
                violations=s["action_ladder_violations"],
                mean_lat=fmt(s.get("mean_latency_ms"), 1),
                p95_lat=fmt(s.get("p95_latency_ms"), 1),
                mean_tokens=fmt(s.get("mean_output_tokens"), 1),
            )
        )
    if all(int(s["live_runs"]) == 0 for s in summaries):
        lines.append("| No live provider results yet | -- | -- | 0 | -- | -- | -- | -- | -- | -- | -- | -- |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_escape(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
    )


def write_latex(path: pathlib.Path, summaries: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    live_summaries = [s for s in summaries if int(s["live_runs"]) > 0 and s["provider"] != "offline-rule"]
    lines = [
        r"\begin{table*}[!t]",
        r"\centering",
        r"\caption{n8n Multi-Model Tool-Scenario Validation}",
        r"\label{tab:n8n_multimodel_tools}",
        r"\begin{adjustbox}{width=\textwidth}",
        r"\begin{tabular}{llcrrrrr}",
        r"\toprule",
        r"Provider & Model & Tool scenario & Runs & Pass (\%) & JSON (\%) & Boundary (\%) & p95 latency (ms) \\",
        r"\midrule",
    ]
    if not live_summaries:
        lines.extend([
            r"\multicolumn{8}{l}{Live Claude, DeepSeek, and Mistral rows are generated by scripts/l4/n8n/run\_multi\_model\_tool\_scenarios.py after API keys are configured.} \\",
        ])
    else:
        for s in live_summaries:
            lines.append(
                f"{latex_escape(s['provider'])} & {latex_escape(s['model'])} & {latex_escape(s['tool_scenario'])} & "
                f"{s['live_runs']} & {fmt(s.get('validator_pass_pct'))} & {fmt(s.get('json_parse_pct'))} & "
                f"{fmt(s.get('claim_boundary_match_pct'))} & {fmt(s.get('p95_latency_ms'), 1)} \\\\"
            )
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{adjustbox}",
        r"\end{table*}",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_coverage(path: pathlib.Path, summaries: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Multi-Model Scenario Coverage",
        "",
        "| Provider | Model | Tool | Requested | Live | Skipped no key | Failed |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['provider']} | `{s['model']}` | {s['tool_scenario']} | {s['requested_runs']} | {s['live_runs']} | {s['skipped_no_api_key']} | {s['failed_runs']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="runtime_artifacts/n8n/model_tool_scenarios/records.jsonl")
    p.add_argument("--out-dir", default="runtime_artifacts/n8n/model_tool_scenarios")
    p.add_argument("--paper-table", default="paper/l4_conference/tables/table_multimodel_tool_scenarios.tex")
    p.add_argument("--require-live-providers", nargs="*", default=[])
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    input_path = pathlib.Path(args.input)
    out_dir = pathlib.Path(args.out_dir)
    records = load_records(input_path)
    summaries = build_summaries(records)

    write_csv(out_dir / "n8n_multimodel_tool_summary.csv", summaries)
    write_markdown(out_dir / "n8n_multimodel_tool_summary.md", summaries, len(records))
    write_coverage(out_dir / "n8n_multimodel_tool_coverage.md", summaries)
    write_latex(pathlib.Path(args.paper_table), summaries)

    missing_live = []
    for provider in args.require_live_providers:
        live_count = sum(int(s["live_runs"]) for s in summaries if s["provider"] == provider)
        if live_count == 0:
            missing_live.append(provider)
    if missing_live:
        print(f"[error] missing live provider results: {', '.join(missing_live)}", file=sys.stderr)
        print("[hint] configure API keys and rerun before using the table as paper evidence", file=sys.stderr)
        return 3

    print(f"[ok] wrote {out_dir / 'n8n_multimodel_tool_summary.csv'}")
    print(f"[ok] wrote {out_dir / 'n8n_multimodel_tool_summary.md'}")
    print(f"[ok] wrote {out_dir / 'n8n_multimodel_tool_coverage.md'}")
    print(f"[ok] wrote {args.paper_table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
