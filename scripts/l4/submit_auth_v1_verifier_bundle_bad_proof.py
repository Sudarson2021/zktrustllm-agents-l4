import json
import os
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")
DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

BUNDLE_FILE = ROOT / "artifacts" / "out_l4" / "verifier_bundle.auth_v1.json"
ATT_ART = ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestorZK.sol" / "DecisionAttestorZK.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def mutate_hex(hex_str: str) -> str:
    x = hex_str.lower()
    if not x.startswith("0x"):
        raise ValueError("Expected 0x-prefixed hex")
    tail = x[-1]
    flipped = "0" if tail != "0" else "1"
    return x[:-1] + flipped

def main():
    bundle = load_json(BUNDLE_FILE)
    att_art = load_json(ATT_ART)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local chain")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    target = bundle["target"]
    sub = bundle["submission"]
    args = sub["args"]

    attestor = w3.eth.contract(
        address=Web3.to_checksum_address(target["contractAddress"]),
        abi=att_art["abi"]
    )

    bad_proof_blob = mutate_hex(args["proofBlobHex"])

    try:
        attestor.functions.submitAgentDecisionZK(
            args["agentId"],
            Web3.to_bytes(hexstr=args["capabilityIdHex"]),
            Web3.to_bytes(hexstr=args["contextHashHex"]),
            Web3.to_bytes(hexstr=args["traceCommitmentHex"]),
            args["traceCID"],
            args["policyClass"],
            args["action"],
            int(args["expiryBucket"]),
            Web3.to_bytes(hexstr=bad_proof_blob)
        ).call({"from": account.address})

        raise SystemExit("ERROR: malformed verifier bundle proof was unexpectedly accepted")

    except Exception as e:
        msg = str(e)
        print("Expected verifier-bundle rejection captured")
        print(msg)

        if "authorization proof failed" not in msg:
            raise SystemExit(f"Unexpected error reason: {msg}")

if __name__ == "__main__":
    main()
