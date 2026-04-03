from agents.common.utils import stable_hash, now_ts

def collect_context():
    payload = {
        "taskId": "task-0001",
        "groupId": "tenant-3",
        "gtkVersion": 12,
        "lossRate": 0.03,
        "delayMs": 18,
        "membershipChange": True,
        "suspicionScore": 0.35,
        "contextSummary": "Moderate delay increase with recent membership churn",
        "timestamp": now_ts()
    }
    payload["contextHash"] = stable_hash(payload)
    return payload

if __name__ == "__main__":
    print(collect_context())
