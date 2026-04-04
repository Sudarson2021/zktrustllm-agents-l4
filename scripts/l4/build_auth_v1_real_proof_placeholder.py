import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]

WITNESS_FILE = ROOT / "artifacts" / "out_l4" / "witness_input.auth_v1.json"
TEMPLATE_FILE = ROOT / "configs" / "l4" / "auth_v1_circuit_template.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.real.placeholder.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    witness = load_json(WITNESS_FILE)
    template = load_json(TEMPLATE_FILE)

    public_inputs = witness["publicInputs"]
    public_input_order = witness["publicOrder"]

    digest_material = json.dumps(
        {
            "circuitName": template["circuitName"],
            "publicInputs": public_inputs,
            "publicInputOrder": public_input_order,
            "privateWitness": witness["privateWitness"],
        },
        sort_keys=True,
    ).encode()

    proof_digest = Web3.keccak(digest_material).hex()

    out = {
        "schema": "auth_v1_real_proof_placeholder",
        "meta": {
            "taskId": witness["meta"]["taskId"],
            "targetAgent": witness["meta"]["targetAgent"],
            "traceCID": witness["meta"]["traceCID"],
            "sourceWitnessFile": str(WITNESS_FILE),
            "sourceTemplateFile": str(TEMPLATE_FILE),
        },
        "proofSystem": "groth16_placeholder",
        "circuitName": template["circuitName"],
        "publicInputOrder": public_input_order,
        "publicInputs": public_inputs,
        "proof": {
            "proofBlobHex": "0x",
            "proofPoints": {
                "a": ["0", "0"],
                "b": [["0", "0"], ["0", "0"]],
                "c": ["0", "0"]
            },
            "verifierCalldata": [],
            "note": "Placeholder only. Replace with real prover output later."
        },
        "derived": {
            "proofDigest": proof_digest,
            "boundedActionMap": template["boundedActionMap"],
        },
        "runtime": witness["runtime"],
        "proverNotes": {
            "status": "real-proof-schema-placeholder",
            "nextStep": "replace placeholder proof fields with actual Groth16 prover output",
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved real-proof placeholder ->", OUT_FILE)
    print("proofDigest ->", proof_digest)

if __name__ == "__main__":
    main()
