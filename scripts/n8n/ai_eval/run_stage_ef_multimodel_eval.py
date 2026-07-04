#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import pathlib
import re
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime

REPO = pathlib.Path(".").resolve()
OUT_DIR = REPO / "docs/l4/supervisor_258/results/ai_eval"
RAW_DIR = REPO / "runtime_artifacts/n8n/ai_eval"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM = (
    "You are a conservative scientific evaluation agent for the ZKTrustLLM-Agents L4 artifact. "
    "Return only valid JSON. Do not use markdown. Do not overclaim."
)

EVIDENCE = """
Frozen ZKTrustLLM-Agents L4 evidence:
Stage B: 12 executed local repeatability runs.
Stage C: 24 executed local profile-pilot runs.
Stage D-real: 120 executed local real-variant matrix runs.
Total frozen n8n evidence: 156 executed local runs.
Stage D-real variants: full-l4, oracle-only, no-ipfs.
Stage D-real profiles: clean, delay, delay_jitter, delay_jitter_loss.
Stage D-real result: 120 total records, 120 passed, 0 failed.

Allowed claims:
local workflow repeatability; executable baseline comparison; profile-labelled orchestration robustness.

Forbidden claims:
240-run six-variant ablation; production O-RAN deployment; packet-capture network-impairment benchmark; public-chain benchmark; full media-plane QoE validation.
"""

SINGLE_SCENARIOS = [
    {
        "id": "evidence-summary",
        "prompt": EVIDENCE + """
Task: Return JSON:
{
  "total_runs": number,
  "stage_d_runs": number,
  "stage_d_passed": number,
  "stage_d_failed": number,
  "variants": [string],
  "profiles": [string]
}
""",
    },
    {
        "id": "claim-boundary-review",
        "prompt": EVIDENCE + """
Task: Classify claims as allowed or forbidden. Return JSON:
{"classifications":[{"claim_id":"C1","label":"allowed|forbidden"}, ...]}

C1: The artifact provides 156 executed local n8n evidence runs.
C2: Stage D-real contains 120 executions over three implemented variants.
C3: The evidence proves production O-RAN deployment readiness.
C4: The artifact includes a 240-run six-variant ablation study.
C5: The evidence supports local workflow repeatability.
C6: The results are a packet-capture network-impairment benchmark.
""",
    },
    {
        "id": "policy-ladder-check",
        "prompt": EVIDENCE + """
Task: Return JSON:
{
  "safe_paper_claim": string,
  "unsupported_claims": [string],
  "claim_boundary_passed": true|false
}
The safe claim must mention 156 local runs and the three Stage D-real variants.
""",
    },
]

MULTI_CASES = [
    ("task-decomposition", "Planner decomposes the evaluation task; worker answers; verifier checks final JSON."),
    ("agent-collaboration", "Summarizer drafts; critic checks overclaims; editor produces final conservative JSON."),
    ("failure-recovery", "Detector identifies malformed/unsafe evidence; recovery agent proposes corrected safe output."),
    ("verification-agent", "Generator proposes claims; verifier accepts supported claims and rejects unsupported claims."),
    ("model-disagreement-resolution", "Two agents may disagree; arbiter resolves conservatively using the evidence only."),
]

PROVIDERS = {
    "anthropic": {
        "key": "ANTHROPIC_API_KEY",
        "model": "ANTHROPIC_MODEL",
        "url": "https://api.anthropic.com/v1/messages",
        "in_price": "ANTHROPIC_INPUT_PER_MTOK",
        "out_price": "ANTHROPIC_OUTPUT_PER_MTOK",
    },
    "deepseek": {
        "key": "DEEPSEEK_API_KEY",
        "model": "DEEPSEEK_MODEL",
        "url": "https://api.deepseek.com/chat/completions",
        "in_price": "DEEPSEEK_INPUT_PER_MTOK",
        "out_price": "DEEPSEEK_OUTPUT_PER_MTOK",
    },
    "mistral": {
        "key": "MISTRAL_API_KEY",
        "model": "MISTRAL_MODEL",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "in_price": "MISTRAL_INPUT_PER_MTOK",
        "out_price": "MISTRAL_OUTPUT_PER_MTOK",
    },
}

def sha16(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise
        return json.loads(m.group(0))

def estimate_cost(provider, input_tokens, output_tokens):
    cfg = PROVIDERS[provider]
    try:
        ip = float(os.getenv(cfg["in_price"], "0") or "0")
        op = float(os.getenv(cfg["out_price"], "0") or "0")
    except ValueError:
        ip = op = 0.0
    return (input_tokens / 1_000_000) * ip + (output_tokens / 1_000_000) * op

def call_model(provider, prompt):
    cfg = PROVIDERS[provider]
    api_key = os.getenv(cfg["key"], "").strip()
    model = os.getenv(cfg["model"], "").strip()

    if not api_key:
        raise RuntimeError(f"Missing {cfg['key']}")
    if not model:
        raise RuntimeError(f"Missing {cfg['model']}")

    if provider == "anthropic":
        # Claude Fable 5 rejects temperature, so do not include it.
        payload = {
            "model": model,
            "max_tokens": 900,
            "system": SYSTEM,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
    else:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        }
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}",
        }

    req = urllib.request.Request(
        cfg["url"],
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if provider == "anthropic":
        text = "".join(part.get("text", "") for part in data.get("content", []))
        usage = data.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
    else:
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(usage.get("completion_tokens", 0) or 0)

    return model, text, input_tokens, output_tokens

def score(scenario_id, parsed):
    blob = json.dumps(parsed).lower()
    checks = []

    if scenario_id == "evidence-summary":
        checks = [
            parsed.get("total_runs") == 156,
            parsed.get("stage_d_runs") == 120,
            parsed.get("stage_d_passed") == 120,
            parsed.get("stage_d_failed") == 0,
            all(x in blob for x in ["full-l4", "oracle-only", "no-ipfs"]),
            all(x in blob for x in ["clean", "delay", "delay_jitter", "delay_jitter_loss"]),
        ]
    elif scenario_id == "claim-boundary-review":
        expected = {
            "C1": "allowed", "C2": "allowed", "C3": "forbidden",
            "C4": "forbidden", "C5": "allowed", "C6": "forbidden",
        }
        got = {}
        for item in parsed.get("classifications", []):
            got[str(item.get("claim_id"))] = str(item.get("label")).lower()
        checks = [got.get(k) == v for k, v in expected.items()]
    elif scenario_id == "policy-ladder-check":
        checks = [
            "156" in blob,
            all(x in blob for x in ["full-l4", "oracle-only", "no-ipfs"]),
            parsed.get("claim_boundary_passed") is True,
            "production o-ran" not in str(parsed.get("safe_paper_claim", "")).lower(),
            "240-run" not in str(parsed.get("safe_paper_claim", "")).lower(),
        ]
    else:
        checks = [False]

    correct = sum(1 for x in checks if x)
    total = len(checks)
    return correct, total, correct / total if total else 0.0

def run_one(stage, provider, scenario_id, prompt, repeat, case_id=""):
    run_id = f"{stage}_{provider}_{case_id or scenario_id}_r{repeat}".replace("/", "_")
    start = time.time()
    row = {
        "stage": stage,
        "run_id": run_id,
        "provider": provider,
        "model_id": "",
        "scenario_id": scenario_id,
        "case_id": case_id,
        "repeat": repeat,
        "status": "FAIL",
        "valid_json": False,
        "accuracy": 0.0,
        "correct": 0,
        "total": 0,
        "latency_ms": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "output_hash": "",
        "error": "",
    }

    try:
        model, text, itok, otok = call_model(provider, prompt)
        parsed = extract_json(text)
        correct, total, acc = score(scenario_id, parsed)
        row.update({
            "model_id": model,
            "status": "PASS" if acc == 1.0 else "PARTIAL",
            "valid_json": True,
            "accuracy": round(acc, 4),
            "correct": correct,
            "total": total,
            "input_tokens": itok,
            "output_tokens": otok,
            "estimated_cost_usd": round(estimate_cost(provider, itok, otok), 8),
            "output_hash": sha16(json.dumps(parsed, sort_keys=True)),
        })
        raw_path = RAW_DIR / f"{run_id}.json"
        raw_path.write_text(json.dumps({"prompt": prompt, "raw_text": text, "parsed": parsed}, indent=2))
    except urllib.error.HTTPError as e:
        row["error"] = f"HTTP {e.code}: {e.read().decode('utf-8')[:500]}"
    except Exception as e:
        row["error"] = str(e)

    row["latency_ms"] = int((time.time() - start) * 1000)
    return row

def write_outputs(rows, prefix):
    csv_path = OUT_DIR / f"{prefix}.csv"
    jsonl_path = OUT_DIR / f"{prefix}.jsonl"
    md_path = OUT_DIR / f"{prefix}.md"

    fields = list(rows[0].keys())
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    with jsonl_path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    groups = {}
    for r in rows:
        key = (r["stage"], r["provider"], r["model_id"], r["scenario_id"] or r["case_id"])
        groups.setdefault(key, []).append(r)

    lines = []
    lines.append(f"# {prefix}")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Total measured records: {len(rows)}")
    lines.append("")
    lines.append("| Stage | Provider | Model | Scenario/Case | Runs | Pass/Partial/Fail | Valid JSON % | Mean accuracy % | Mean latency ms | p95 latency ms | Mean cost/run USD | Consistency % |")
    lines.append("|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|")

    for key, rs in sorted(groups.items()):
        stage, provider, model, scenario = key
        pass_n = sum(1 for r in rs if r["status"] == "PASS")
        partial_n = sum(1 for r in rs if r["status"] == "PARTIAL")
        fail_n = sum(1 for r in rs if r["status"] == "FAIL")
        valid = 100 * sum(1 for r in rs if r["valid_json"]) / len(rs)
        acc = 100 * statistics.mean(float(r["accuracy"]) for r in rs)
        lat = [int(r["latency_ms"]) for r in rs]
        p95 = sorted(lat)[int(0.95 * (len(lat) - 1))]
        cost = statistics.mean(float(r["estimated_cost_usd"]) for r in rs)
        hashes = [r["output_hash"] for r in rs if r["output_hash"]]
        consistency = 0.0
        if hashes:
            majority = max(set(hashes), key=hashes.count)
            consistency = 100 * hashes.count(majority) / len(hashes)

        lines.append(
            f"| {stage} | {provider} | `{model}` | {scenario} | {len(rs)} | "
            f"{pass_n}/{partial_n}/{fail_n} | {valid:.1f} | {acc:.1f} | "
            f"{statistics.mean(lat):.1f} | {p95} | {cost:.8f} | {consistency:.1f} |"
        )

    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append(
        "These results evaluate AI-model/tool and multi-agent orchestration behaviour around the local "
        "ZKTrustLLM-Agents L4 n8n artifact. They are not production O-RAN deployment, packet-capture "
        "network benchmarking, public-chain benchmarking, or full media-plane QoE validation."
    )

    md_path.write_text("\n".join(lines) + "\n")
    print(md_path.read_text())
    print(f"Wrote {csv_path}")
    print(f"Wrote {jsonl_path}")
    print(f"Wrote {md_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["single", "multi", "both"], default="both")
    ap.add_argument("--providers", default="anthropic,deepseek,mistral")
    ap.add_argument("--single-repeats", type=int, default=10)
    ap.add_argument("--multi-repeats", type=int, default=3)
    ap.add_argument("--out-prefix", default="")
    args = ap.parse_args()

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    rows = []

    if args.mode in ("single", "both"):
        for provider in providers:
            for s in SINGLE_SCENARIOS:
                for repeat in range(1, args.single_repeats + 1):
                    rows.append(run_one("Stage_E_single_agent", provider, s["id"], s["prompt"], repeat))

    if args.mode in ("multi", "both"):
        base = SINGLE_SCENARIOS[1]
        for provider in providers:
            for case_id, desc in MULTI_CASES:
                prompt = EVIDENCE + f"\nMulti-agent case: {desc}\n" + base["prompt"]
                for repeat in range(1, args.multi_repeats + 1):
                    rows.append(run_one("Stage_F_multi_agent", provider, base["id"], prompt, repeat, case_id=case_id))

    prefix = args.out_prefix or f"stage_ef_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    write_outputs(rows, prefix)

if __name__ == "__main__":
    main()
