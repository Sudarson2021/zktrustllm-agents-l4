import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROOF_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.mock.json"
DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"

OUT_DIR = ROOT / "artifacts" / "out_l4"
PROVER_OUT = OUT_DIR / "prover_bundle.auth_v1.json"
VERIFIER_OUT = OUT_DIR / "verifier_bundle.auth_v1.json"

HEX_WITNESS_FIELDS = [
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
    proof = load_json(PROOF_FILE)
    dep = load_json(DEPLOY_FILE)

    pub_raw = proof["publicInputsRaw"]
    pub_field = proof["publicInputsField"]
    wit_raw = proof["privateWitnessRaw"]
    runtime = proof["runtime"]
    meta = proof["meta"]
    dig = proof["derivedDigests"]
    proof_info = proof["proof"]

    private_witness_field = {}
    for key in HEX_WITNESS_FIELDS:
        private_witness_field[key] = hex_to_dec_str(wit_raw[key])
    private_witness_field["actionCode"] = str(wit_raw["actionCode"])

    prover_bundle = {
        "schema": "auth_v1_prover_bundle",
        "meta": {
            "taskId": meta["taskId"],
            "targetAgent": meta["targetAgent"],
            "traceCID": meta["traceCID"],
            "sourceProofOutput": str(PROOF_FILE),
        },
        "circuit": {
            "name": "auth_v1",
            "mode": proof["verifierMode"],
        },
        "publicInputOrder": proof["publicInputOrder"],
        "publicInputsRaw": pub_raw,
        "publicInputsField": pub_field,
        "privateWitnessRaw": wit_raw,
        "privateWitnessField": private_witness_field,
        "derivedDigests": dig,
        "runtime": runtime,
        "proof": proof_info,
    }

    target_contract = dep.get("decisionAttestorZKV2", dep.get("decisionAttestorZK", ""))

    verifier_bundle = {
        "schema": "auth_v1_verifier_bundle",
        "meta": {
            "taskId": meta["taskId"],
            "targetAgent": meta["targetAgent"],
            "traceCID": meta["traceCID"],
            "sourceProofOutput": str(PROOF_FILE),
        },
        "target": {
            "network": "localhost",
            "contractName": "DecisionAttestorZK",
            "contractAddress": target_contract,
            "verifierMode": proof["verifierMode"],
        },
        "submission": {
            "method": "submitAgentDecisionZK",
            "args": {
                "agentId": runtime["agentId"],
                "capabilityIdHex": norm_hex(pub_raw["capabilityId"]),
                "contextHashHex": norm_hex(pub_raw["contextHash"]),
                "traceCommitmentHex": norm_hex(pub_raw["traceCommitment"]),
                "traceCID": runtime["traceCID"],
                "policyClass": runtime["policyClass"],
                "action": runtime["action"],
                "expiryBucket": int(pub_raw["expiryBucket"]),
                "proofBlobHex": norm_hex(proof_info["proofBlobHex"]),
            },
            "publicInputOrder": proof["publicInputOrder"],
            "proofDigest": norm_hex(proof_info["proofDigest"]),
        },
        "runtime": runtime,
        "derivedDigests": dig,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROVER_OUT, "w") as f:
        json.dump(prover_bundle, f, indent=2)

    with open(VERIFIER_OUT, "w") as f:
        json.dump(verifier_bundle, f, indent=2)

    print("Saved prover bundle   ->", PROVER_OUT)
    print("Saved verifier bundle ->", VERIFIER_OUT)

if __name__ == "__main__":
    main()
