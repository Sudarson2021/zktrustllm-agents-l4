from agents.common.utils import stable_hash, now_ts

def evaluate_risk(context):
    result = {
        "taskId": context["taskId"],
        "riskScore": 0.74,
        "confidence": 0.82,
        "anomalyFlags": ["capability_replay_suspected"] if context["suspicionScore"] > 0.3 else [],
        "recommendedActionClass": "subgroup-isolation",
        "timestamp": now_ts()
    }
    result["traceCommitment"] = stable_hash(result)
    return result

if __name__ == "__main__":
    from agents.edge_telemetry.agent import collect_context
    print(evaluate_risk(collect_context()))
