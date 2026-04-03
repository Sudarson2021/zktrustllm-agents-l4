import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.common.utils import now_ts, stable_hash

TRACE_CID_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.cid.json"
TRACE_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "anomaly_bundle.task-0001.json"

def main():
    if not TRACE_CID_FILE.exists():
        raise FileNotFoundError(f"Missing CID record: {TRACE_CID_FILE}")
    if not TRACE_FILE.exists():
        raise FileNotFoundError(f"Missing trace bundle: {TRACE_FILE}")

    with open(TRACE_CID_FILE, "r") as f:
        cid_data = json.load(f)

    with open(TRACE_FILE, "r") as f:
        trace_data = json.load(f)

    anomaly = {
        "taskId": trace_data["taskId"],
        "severity": "medium",
        "flags": trace_data.get("anomalyFlags", []),
        "linkedTraceCID": cid_data["cid"],
        "traceCommitment": trace_data["traceCommitment"],
        "recommendedMitigation": trace_data["policyAction"],
        "timestamp": now_ts()
    }
    anomaly["anomalyCommitment"] = stable_hash(anomaly)

    with open(OUT_FILE, "w") as f:
        json.dump(anomaly, f, indent=2)

    print("Saved anomaly bundle ->", OUT_FILE)

if __name__ == "__main__":
    main()
