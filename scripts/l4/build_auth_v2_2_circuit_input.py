import json
from pathlib import Path

ROOT = Path.cwd()
OUT_DIR = ROOT / "artifacts" / "out_l4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PAYLOAD_FILE = OUT_DIR / "proof_payload.auth_v2_2.json"
OUT_FILE = OUT_DIR / "circuit_input.auth_v2_2.json"

def main():
    with open(PAYLOAD_FILE, "r") as f:
        payload = json.load(f)

    public_input_order = [
        "agentKey",
        "capabilityId",
        "policyClassHash",
        "actionClass",
        "contextHash",
        "traceCommitment",
        "expiryBucket",
        "policyAdmissibilityFlag",
        "trustState",
    ]

    public_inputs = {k: payload[k] for k in public_input_order}

    circuit_input = {
        "scheme": "auth_v2_2",
        "relationVersion": payload["relationVersion"],
        "description": "First AUTH_V2.2 circuit input with trust-state-aware admissibility binding",
        "publicInputOrder": public_input_order,
        "publicInputs": public_inputs,
        "publicInputsHex": {
            k: hex(int(v)) if isinstance(v, int) else v
            for k, v in public_inputs.items()
        },
        "privateInputs": {
            "bindingNonce": payload["bindingNonce"],
            "agentId": payload["agentId"],
            "capabilityIdText": payload["capabilityIdText"],
            "policyClassText": payload["policyClassText"],
            "actionClassText": payload["actionClassText"],
            "trustStateText": payload["trustStateText"],
            "contextText": payload["contextText"],
        }
    }

    with open(OUT_FILE, "w") as f:
        json.dump(circuit_input, f, indent=2)

    print("Saved AUTH_V2.2 circuit input ->", OUT_FILE)
    print("relationVersion ->", payload["relationVersion"])
    print("Public input count ->", len(public_input_order))
    print("Ordered public inputs ->", public_input_order)
    print("trustState ->", payload["trustState"])
    print("policyAdmissibilityFlag ->", payload["policyAdmissibilityFlag"])

if __name__ == "__main__":
    main()
