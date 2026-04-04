import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
ZOKRATES_INPUT_FILE = ROOT / "artifacts" / "out_l4" / "zokrates_input.auth_v1.json"
ADAPTER_FILE = ROOT / "artifacts" / "out_l4" / "prover_adapter.auth_v1.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "zokrates_proof.auth_v1.placeholder.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    zk_input = load_json(ZOKRATES_INPUT_FILE)
    adapter = load_json(ADAPTER_FILE)

    digest_material = json.dumps(
        {
            "proofSystem": "zokrates_groth16_placeholder",
            "circuitName": zk_input["circuitName"],
            "publicInputs": zk_input["publicInputs"],
            "publicInputOrder": zk_input["publicInputOrder"],
        },
        sort_keys=True,
    ).encode()

    proof_digest = Web3.keccak(digest_material).hex()

    out = {
        "schema": "auth_v1_zokrates_proof_placeholder",
        "meta": {
            "taskId": zk_input["meta"]["taskId"],
            "targetAgent": zk_input["meta"]["targetAgent"],
            "traceCID": zk_input["meta"]["traceCID"],
            "sourceZoKratesInputFile": str(ZOKRATES_INPUT_FILE),
            "sourceProverAdapterFile": str(ADAPTER_FILE),
        },
        "proofSystem": "zokrates_groth16_placeholder",
        "circuitName": zk_input["circuitName"],
        "publicInputOrder": zk_input["publicInputOrder"],
        "publicInputs": zk_input["publicInputs"],
        "zokratesProof": {
            "proof": {
                "a": ["0", "0"],
                "b": [["0", "0"], ["0", "0"]],
                "c": ["0", "0"]
            },
            "inputs": zk_input["publicInputs"],
            "note": "Placeholder only. Replace with actual ZoKrates proof.json content later."
        },
        "verifierCalldata": [],
        "derived": {
            "proofDigest": proof_digest,
            "expectedSubmissionMethod": adapter["submissionContractMethod"],
        },
        "runtime": adapter["runtime"],
        "status": {
            "bridgeMode": "placeholder",
            "nextStep": "replace zokratesProof with actual ZoKrates proof output and generated calldata",
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved ZoKrates proof placeholder ->", OUT_FILE)
    print("proofDigest ->", proof_digest)

if __name__ == "__main__":
    main()
