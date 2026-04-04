import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "artifacts" / "out_l4" / "circuit_input.auth_v1.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "witness_input.auth_v1.json"

PUBLIC_ORDER = [
    "agentKey",
    "capabilityId",
    "policyClassHash",
    "contextHash",
    "traceCommitment",
    "actionHash",
    "expiryBucket",
]

PRIVATE_ORDER = [
    "scopeHash",
    "capabilitySalt",
    "actionCode",
    "domainSepCapability",
    "domainSepAction",
]

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    data = load_json(INPUT_FILE)

    pub_field = data["public_inputs_field"]
    wit_field = data["private_witness_field"]

    out = {
        "schema": "auth_v1_witness_input",
        "meta": data["meta"],
        "publicOrder": PUBLIC_ORDER,
        "privateOrder": PRIVATE_ORDER,
        "publicInputs": [pub_field[k] for k in PUBLIC_ORDER],
        "privateWitness": [wit_field[k] for k in PRIVATE_ORDER],
        "namedPublicInputs": {k: pub_field[k] for k in PUBLIC_ORDER},
        "namedPrivateWitness": {k: wit_field[k] for k in PRIVATE_ORDER},
        "runtime": data["runtime"],
        "derivedDigests": data["derivedDigests"],
        "proverNotes": {
            "intendedCircuit": "auth_v1",
            "fieldEncoding": "decimal strings",
            "usage": "feed this into future witness generator / prover adapter"
        }
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved witness export ->", OUT_FILE)

if __name__ == "__main__":
    main()
