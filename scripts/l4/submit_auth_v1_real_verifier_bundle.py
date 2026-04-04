import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BUNDLE_FILE = ROOT / "artifacts" / "out_l4" / "verifier_bundle.auth_v1.real.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "submission_preflight.auth_v1.real.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    bundle = load_json(BUNDLE_FILE)

    ready_now = bundle["status"]["readyForCurrentDeployedContract"]

    preflight = {
        "schema": "auth_v1_real_submission_preflight",
        "timestamp": int(time.time()),
        "sourceBundle": str(BUNDLE_FILE),
        "readyForCurrentDeployedContract": ready_now,
        "currentTarget": bundle["target"],
        "runtimeArgs": bundle["runtimeArgs"],
        "proofSystem": bundle["proofSystem"],
        "derived": bundle["derived"],
    }

    if not ready_now:
        preflight["submitted"] = False
        preflight["reason"] = bundle["target"]["currentReason"]
        preflight["nextStep"] = "Deploy a Groth16-capable wrapper/verifier that accepts proof points and public inputs"
    else:
        preflight["submitted"] = False
        preflight["reason"] = "Submission path not yet implemented in this script"
        preflight["nextStep"] = "Wire actual Web3 submission to the future Groth16-capable wrapper"

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(preflight, f, indent=2)

    print("Saved submission preflight ->", OUT_FILE)
    print("readyForCurrentDeployedContract ->", ready_now)
    print("submitted ->", preflight["submitted"])
    print("reason ->", preflight["reason"])

if __name__ == "__main__":
    main()
