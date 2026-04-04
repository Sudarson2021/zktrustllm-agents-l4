import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "configs" / "l4" / "test_vectors_auth_v1.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "proof_payload.auth_v1.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    data = load_json(INPUT_FILE)

    payload = {
        "schema": "auth_v1_proof_payload",
        "meta": {
            "taskId": data["meta"]["taskId"],
            "targetAgent": data["meta"]["targetAgent"],
            "generatedAt": data["meta"]["generatedAt"],
            "traceCID": data["meta"]["traceCID"],
        },
        "publicInputs": data["publicInputs"],
        "witnessPlaceholders": data["witnessPlaceholders"],
        "derivedDigests": data["derivedDigests"],
        "runtime": data["currentRuntimeValues"],
        "proverHints": {
            "circuitName": "auth_v1",
            "proofSystem": "planned_groth16_or_equivalent",
            "currentStage": "pre-prover-payload",
            "expectedBoundedActionSet": {
                "keep": 1,
                "rekey": 2,
                "rotate": 3,
                "isolate": 4,
                "quarantine": 5,
            },
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(payload, f, indent=2)

    print("Saved proof payload ->", OUT_FILE)

if __name__ == "__main__":
    main()
