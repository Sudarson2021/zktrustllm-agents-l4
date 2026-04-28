import json
from pathlib import Path
from web3 import Web3

ROOT = Path.cwd()
OUT_DIR = ROOT / "artifacts" / "out_l4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "proof_payload.auth_v2.json"

def keccak_text(text: str) -> str:
    return Web3.keccak(text=text).hex()

def main():
    payload = {
        "agentId": "policy-lkh-01",
        "agentKey": int(keccak_text("policy-lkh-01"), 16),
        "capabilityIdText": "cap-policy-01",
        "capabilityIdHex": keccak_text("cap-policy-01"),
        "capabilityId": int(keccak_text("cap-policy-01"), 16),
        "policyClassText": "policy-enforce",
        "policyClassHashHex": keccak_text("policy-enforce"),
        "policyClassHash": int(keccak_text("policy-enforce"), 16),
        "actionClassText": "isolate",
        "actionClass": 3,
        "actionClassHashHex": keccak_text("isolate"),
        "actionClassHash": int(keccak_text("isolate"), 16),
        "contextText": "ctx-policy",
        "contextHashHex": keccak_text("ctx-policy"),
        "contextHash": int(keccak_text("ctx-policy"), 16),
        "traceText": "trace-policy-01",
        "traceCommitmentHex": keccak_text("trace-policy-01"),
        "traceCommitment": int(keccak_text("trace-policy-01"), 16),
        "expiryBucket": 493128,
        "notes": {
            "purpose": "First AUTH_V2 control-plane-aware proof payload",
            "source": "Aligned with gateway positive case and policy-enforce/isolate path"
        }
    }

    with open(OUT_FILE, "w") as f:
        json.dump(payload, f, indent=2)

    print("Saved AUTH_V2 proof payload ->", OUT_FILE)
    print("agentId ->", payload["agentId"])
    print("policyClassText ->", payload["policyClassText"])
    print("actionClassText ->", payload["actionClassText"])
    print("expiryBucket ->", payload["expiryBucket"])

if __name__ == "__main__":
    main()
