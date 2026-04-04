import json
import os
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]

DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"
BUNDLE_FILE = ROOT / "artifacts" / "out_l4" / "groth16_bundle.auth_v1.real.json"
VERIFIER_ARTIFACT = ROOT / "artifacts" / "contracts" / "l4" / "generated" / "AuthV1Verifier.sol" / "Verifier.json"

RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    dep = load_json(DEPLOY_FILE)
    bundle = load_json(BUNDLE_FILE)
    artifact = load_json(VERIFIER_ARTIFACT)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to {RPC_URL}")

    verifier = w3.eth.contract(
        address=Web3.to_checksum_address(dep["authV1Groth16Verifier"]),
        abi=artifact["abi"]
    )

    p = bundle["solidityProof"]
    proof_tuple = (p["a"], p["b"], p["c"])

    print("Verifier address ->", dep["authV1Groth16Verifier"])
    print("Input count ->", len(p["input"]))

    try:
        result = verifier.functions.verifyTx(
            proof_tuple,
            p["input"]
        ).call()
        print("Direct verifier call result ->", result)
    except Exception as e:
        print("Direct verifier call raised:")
        print(repr(e))

if __name__ == "__main__":
    main()
