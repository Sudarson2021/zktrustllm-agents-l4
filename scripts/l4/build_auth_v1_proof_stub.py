import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "artifacts" / "out_l4" / "circuit_input.auth_v1.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.mock.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def norm_hex(x: str) -> str:
    x = x.lower()
    if not x.startswith("0x"):
        x = "0x" + x
    return x

def main():
    data = load_json(INPUT_FILE)

    pub_raw = data["public_inputs_raw"]
    pub_field = data["public_inputs_field"]
    wit_raw = data["private_witness_raw"]
    meta = data["meta"]
    runtime = data["runtime"]
    dig = data["derivedDigests"]

    agent_key = Web3.to_bytes(hexstr=norm_hex(pub_raw["agentKey"]))
    capability_id = Web3.to_bytes(hexstr=norm_hex(pub_raw["capabilityId"]))
    policy_class_hash = Web3.to_bytes(hexstr=norm_hex(pub_raw["policyClassHash"]))
    context_hash = Web3.to_bytes(hexstr=norm_hex(pub_raw["contextHash"]))
    trace_commitment = Web3.to_bytes(hexstr=norm_hex(pub_raw["traceCommitment"]))
    action_hash = Web3.to_bytes(hexstr=norm_hex(pub_raw["actionHash"]))
    expiry_bucket = int(pub_raw["expiryBucket"])

    # This matches the current V2 verifier logic:
    # verifier checks keccak256(proofBlob) == keccak256(abi.encode(public inputs))
    proof_blob_bytes = Web3().codec.encode(
        ["bytes32", "bytes32", "bytes32", "bytes32", "bytes32", "bytes32", "uint256"],
        [
            agent_key,
            capability_id,
            policy_class_hash,
            context_hash,
            trace_commitment,
            action_hash,
            expiry_bucket,
        ],
    )

    proof_blob_hex = "0x" + proof_blob_bytes.hex()
    proof_digest = Web3.keccak(proof_blob_bytes).hex()

    out = {
        "schema": "auth_v1_mock_proof_output",
        "meta": {
            "taskId": meta["taskId"],
            "targetAgent": meta["targetAgent"],
            "traceCID": meta["traceCID"],
            "sourceCircuitInput": str(INPUT_FILE),
        },
        "verifierMode": "mock_v2_structured_digest",
        "publicInputOrder": data["prover_notes"]["publicInputOrder"],
        "publicInputsRaw": pub_raw,
        "publicInputsField": pub_field,
        "privateWitnessRaw": wit_raw,
        "derivedDigests": dig,
        "proof": {
            "proofBlobHex": proof_blob_hex,
            "proofDigest": proof_digest,
            "note": "Mock prover artifact; replace with real Groth16/ZoKrates proof output later",
        },
        "runtime": runtime,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved mock proof output ->", OUT_FILE)
    print("Proof digest ->", proof_digest)

if __name__ == "__main__":
    main()
