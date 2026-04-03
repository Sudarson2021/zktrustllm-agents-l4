import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.edge_telemetry.agent import collect_context
from agents.trust_risk.agent import evaluate_risk
from agents.policy_lkh.agent import decide_action
from agents.common.utils import stable_hash, now_ts

OUT_DIR = ROOT / "artifacts" / "out_l4" / "traces"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "trace_bundle.task-0001.json"

def main():
    context = collect_context()
    risk = evaluate_risk(context)
    action = decide_action(risk)

    trace_inputs = {
        "taskId": context["taskId"],
        "context": context,
        "risk": risk,
        "action": action,
        "timestamp": now_ts()
    }

    prompt_hash = stable_hash({
        "sender": "edge-telemetry-01",
        "receiver": "trust-risk-01",
        "taskId": context["taskId"],
        "contextSummary": context["contextSummary"]
    })

    response_hash = stable_hash({
        "sender": "trust-risk-01",
        "receiver": "policy-lkh-01",
        "taskId": risk["taskId"],
        "recommendedActionClass": risk["recommendedActionClass"],
        "riskScore": risk["riskScore"]
    })

    trace_commitment = stable_hash(trace_inputs)

    bundle = {
        "taskId": context["taskId"],
        "contextHash": context["contextHash"],
        "promptHash": prompt_hash,
        "responseHash": response_hash,
        "traceCommitment": trace_commitment,
        "anomalyFlags": risk["anomalyFlags"],
        "policyAction": action["action"],
        "timestamp": now_ts(),
        "fullTrace": trace_inputs
    }

    with open(OUT_FILE, "w") as f:
        json.dump(bundle, f, indent=2)

    print("Saved trace bundle ->", OUT_FILE)

if __name__ == "__main__":
    main()
