from agents.common.utils import now_ts

def decide_action(risk_result):
    risk = risk_result["riskScore"]

    if risk >= 0.9:
        action = "quarantine"
    elif risk >= 0.7:
        action = "isolate"
    elif risk >= 0.5:
        action = "rekey"
    else:
        action = "keep"

    return {
        "taskId": risk_result["taskId"],
        "action": action,
        "reasonCode": "risk-threshold-policy",
        "timestamp": now_ts()
    }

if __name__ == "__main__":
    from agents.edge_telemetry.agent import collect_context
    from agents.trust_risk.agent import evaluate_risk
    print(decide_action(evaluate_risk(collect_context())))
