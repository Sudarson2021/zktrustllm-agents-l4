import json
from pathlib import Path
from web3 import Web3

ROOT = Path.cwd()
OUT_DIR = ROOT / "artifacts" / "out_l4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "proof_payload.auth_v2.json"

BN128_SCALAR_FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617

def keccak_text(text: str) -> str:
    return Web3.keccak(text=text).hex()

def keccak_int(text: str) -> int:
    return int(keccak_text(text), 16) % BN128_SCALAR_FIELD

def main():
    payload = {
        "relationVersion": "auth_v2_relation_v0",
        "agentId": "policy-lkh-01",
        "agentKey": keccak_int("policy-lkh-01"),
        "capabilityIdText": "cap-policy-01",
        "capabilityIdHex": keccak_text("cap-policy-01"),
        "capabilityId": keccak_int("cap-policy-01"),
        "policyClassText": "policy-enforce",
        "policyClassHashHex": keccak_text("policy-enforce"),
        "policyClassHash": keccak_int("policy-enforce"),
        "actionClassText": "isolate",
        "actionClass": 3,
        "contextText": "ctx-policy",
        "contextHashHex": keccak_text("ctx-policy"),
        "contextHash": keccak_int("ctx-policy"),
        "expiryBucket": 493128,
        "bindingNonce": 20260428
    }

    trace_commitment = (
        payload["agentKey"]
        + payload["capabilityId"]
        + payload["policyClassHash"]
        + payload["actionClass"]
        + payload["contextHash"]
        + payload["expiryBucket"]
        + payload["bindingNonce"]
    ) % BN128_SCALAR_FIELD

    payload["traceCommitment"] = trace_commitment
    payload["traceCommitmentHex"] = hex(trace_commitment)

    payload["notes"] = {
        "purpose": "First AUTH_V2 control-plane-aware proof payload",
        "source": "Aligned with gateway positive case and relation v0 arithmetic binding"
    }

    with open(OUT_FILE, "w") as f:
        json.dump(payload, f, indent=2)

    print("Saved AUTH_V2 proof payload ->", OUT_FILE)
    print("relationVersion ->", payload["relationVersion"])
    print("agentId ->", payload["agentId"])
    print("policyClassText ->", payload["policyClassText"])
    print("actionClassText ->", payload["actionClassText"])
    print("bindingNonce ->", payload["bindingNonce"])
    print("traceCommitment ->", payload["traceCommitment"])

if __name__ == "__main__":
    main()
