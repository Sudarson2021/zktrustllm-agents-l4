import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAYLOAD_FILE = ROOT / "artifacts" / "out_l4" / "proof_payload.auth_v1.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "circuit_input.auth_v1.json"

HEX_FIELDS_PUBLIC = [
    "agentKey",
    "capabilityId",
    "policyClassHash",
    "contextHash",
    "traceCommitment",
    "actionHash",
]

HEX_FIELDS_WITNESS = [
    "scopeHash",
    "capabilitySalt",
    "domainSepCapability",
    "domainSepAction",
]

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def norm_hex(x: str) -> str:
    x = x.lower()
    if not x.startswith("0x"):
        x = "0x" + x
    return x

def hex_to_dec_str(x: str) -> str:
    return str(int(norm_hex(x), 16))

def main():
    data = load_json(PAYLOAD_FILE)

    pub = data["publicInputs"]
    wit = data["witnessPlaceholders"]
    meta = data["meta"]
    runtime = data["runtime"]
    dig = data["derivedDigests"]

    public_inputs_field = {k: hex_to_dec_str(pub[k]) for k in HEX_FIELDS_PUBLIC}
    public_inputs_field["expiryBucket"] = str(pub["expiryBucket"])

    private_witness_field = {k: hex_to_dec_str(wit[k]) for k in HEX_FIELDS_WITNESS}
    private_witness_field["actionCode"] = str(wit["actionCode"])

    out = {
        "schema": "auth_v1_circuit_input",
        "meta": {
            "taskId": meta["taskId"],
            "targetAgent": meta["targetAgent"],
            "traceCID": meta["traceCID"],
            "sourcePayload": str(PAYLOAD_FILE),
        },
        "public_inputs_raw": {
            "agentKey": norm_hex(pub["agentKey"]),
            "capabilityId": norm_hex(pub["capabilityId"]),
            "policyClassHash": norm_hex(pub["policyClassHash"]),
            "contextHash": norm_hex(pub["contextHash"]),
            "traceCommitment": norm_hex(pub["traceCommitment"]),
            "actionHash": norm_hex(pub["actionHash"]),
            "expiryBucket": pub["expiryBucket"],
        },
        "public_inputs_field": public_inputs_field,
        "private_witness_raw": {
            "scopeHash": norm_hex(wit["scopeHash"]),
            "capabilitySalt": norm_hex(wit["capabilitySalt"]),
            "domainSepCapability": norm_hex(wit["domainSepCapability"]),
            "domainSepAction": norm_hex(wit["domainSepAction"]),
            "actionCode": wit["actionCode"],
        },
        "private_witness_field": private_witness_field,
        "runtime": runtime,
        "derivedDigests": dig,
        "prover_notes": {
            "intendedCircuit": "auth_v1",
            "fieldEncoding": "decimal strings for compatibility with common circuit toolchains",
            "publicInputOrder": [
                "agentKey",
                "capabilityId",
                "policyClassHash",
                "contextHash",
                "traceCommitment",
                "actionHash",
                "expiryBucket",
            ],
            "privateWitnessOrder": [
                "scopeHash",
                "capabilitySalt",
                "actionCode",
                "domainSepCapability",
                "domainSepAction",
            ],
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved circuit input ->", OUT_FILE)

if __name__ == "__main__":
    main()
