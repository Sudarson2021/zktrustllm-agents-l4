import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

WITNESS_FILE = ROOT / "artifacts" / "out_l4" / "witness_input.auth_v1.json"
TEMPLATE_FILE = ROOT / "configs" / "l4" / "auth_v1_circuit_template.json"
PROOF_PLACEHOLDER_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.real.placeholder.json"
VERIFIER_BUNDLE_FILE = ROOT / "artifacts" / "out_l4" / "verifier_bundle.auth_v1.json"

OUT_FILE = ROOT / "artifacts" / "out_l4" / "prover_adapter.auth_v1.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    witness = load_json(WITNESS_FILE)
    template = load_json(TEMPLATE_FILE)
    proof_placeholder = load_json(PROOF_PLACEHOLDER_FILE)
    verifier_bundle = load_json(VERIFIER_BUNDLE_FILE)

    out = {
        "schema": "auth_v1_real_prover_adapter",
        "meta": {
            "taskId": witness["meta"]["taskId"],
            "targetAgent": witness["meta"]["targetAgent"],
            "traceCID": witness["meta"]["traceCID"],
        },
        "proofSystem": {
            "current": "groth16_placeholder",
            "planned": template["proofSystemTarget"],
            "adapterStatus": "skeleton_ready",
        },
        "circuit": {
            "name": template["circuitName"],
            "publicInputOrder": template["publicInputOrder"],
            "privateWitnessOrder": template["privateWitnessOrder"],
            "relations": template["relations"],
            "boundedActionMap": template["boundedActionMap"],
        },
        "sources": {
            "witnessInputFile": str(WITNESS_FILE),
            "circuitTemplateFile": str(TEMPLATE_FILE),
            "proofPlaceholderFile": str(PROOF_PLACEHOLDER_FILE),
            "verifierBundleFile": str(VERIFIER_BUNDLE_FILE),
        },
        "witnessExport": {
            "publicInputs": witness["publicInputs"],
            "privateWitness": witness["privateWitness"],
            "namedPublicInputs": witness["namedPublicInputs"],
            "namedPrivateWitness": witness["namedPrivateWitness"],
        },
        "expectedProofArtifact": {
            "schema": "auth_v1_real_proof",
            "requiredFields": [
                "proofSystem",
                "circuitName",
                "publicInputOrder",
                "publicInputs",
                "proof",
                "derived",
                "runtime",
                "meta",
            ],
            "proofShape": {
                "proofBlobHex": "hex string or verifier-compatible proof blob",
                "proofPoints": {
                    "a": ["field element", "field element"],
                    "b": [["field element", "field element"], ["field element", "field element"]],
                    "c": ["field element", "field element"],
                },
                "verifierCalldata": ["toolchain-generated calldata items"],
            },
        },
        "verifierTarget": verifier_bundle["target"],
        "submissionContractMethod": verifier_bundle["submission"]["method"],
        "submissionArgsShape": list(verifier_bundle["submission"]["args"].keys()),
        "runtime": witness["runtime"],
        "derivedDigests": witness["derivedDigests"],
        "migrationPlan": {
            "replacePlaceholderProofOnly": True,
            "preserveBundleWorkflow": True,
            "preservePublicInputOrder": True,
            "preservePrivateWitnessOrder": True,
            "preserveDecisionAttestorZKOuterInterface": True,
        },
        "nextImplementationTasks": [
            "map witness_input.auth_v1.json into the chosen prover's witness format",
            "implement circuit auth_v1 using the template field order",
            "generate a real proof artifact matching the expected proof schema",
            "generate verifier calldata or proof blob for on-chain verification",
            "replace MockAuthorizationVerifierV2 with a generated verifier contract",
            "re-run positive and negative verifier-bundle submission tests",
        ],
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved prover adapter ->", OUT_FILE)

if __name__ == "__main__":
    main()
