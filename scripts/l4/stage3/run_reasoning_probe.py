#!/usr/bin/env python3
import argparse
import hashlib
import json
import time

def trust_state_from_profile(profile: str) -> str:
    if "loss_1pct" in profile or "jitter_10ms" in profile:
        return "Restricted"
    if "jitter_5ms" in profile:
        return "Watch"
    return "Trusted"

def action_from_state(state: str) -> str:
    if state == "Trusted":
        return "AUTOMATIC"
    if state == "Watch":
        return "AUTOMATIC"
    if state == "Restricted":
        return "HUMAN"
    return "NEVER"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--repeat", required=True)
    args = ap.parse_args()

    # Deterministic policy-reasoning micro-benchmark.
    # This is a control-plane reasoning probe, not an LLM semantic benchmark.
    start = time.perf_counter_ns()

    state = None
    action = None
    digest = None

    for _ in range(1000):
        state = trust_state_from_profile(args.profile)
        action = action_from_state(state)
        payload = {
            "variant": args.variant,
            "profile": args.profile,
            "repeat": args.repeat,
            "trust_state": state,
            "action_class": action,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()

    end = time.perf_counter_ns()
    latency_ms = (end - start) / 1_000_000.0

    ref_bytes = len(digest.encode())

    print(f"KPI_REASON_LATENCY_MS={latency_ms:.6f}")
    print(f"KPI_A2A_REFERENCE_BYTES={ref_bytes}")
    print(f"KPI_TRUST_STATE={state}")
    print(f"KPI_ACTION_CLASS={action}")
    print("KPI_REASONING_SOURCE=stage3_deterministic_policy_probe")

if __name__ == "__main__":
    main()
