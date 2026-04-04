import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "artifacts" / "out_l4" / "prover_adapter.auth_v1.json"

REQUIRED_TOP = [
    "schema",
    "meta",
    "proofSystem",
    "circuit",
    "sources",
    "witnessExport",
    "expectedProofArtifact",
    "verifierTarget",
    "submissionContractMethod",
    "submissionArgsShape",
    "runtime",
    "derivedDigests",
    "migrationPlan",
    "nextImplementationTasks",
]

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def require_keys(obj, keys, name):
    missing = [k for k in keys if k not in obj]
    if missing:
        raise KeyError(f"Missing keys in {name}: {missing}")

def main():
    data = load_json(INPUT_FILE)

    require_keys(data, REQUIRED_TOP, "top-level")

    if data["schema"] != "auth_v1_real_prover_adapter":
        raise ValueError(f"Unexpected schema: {data['schema']}")

    pub_order = data["circuit"]["publicInputOrder"]
    priv_order = data["circuit"]["privateWitnessOrder"]

    named_pub = data["witnessExport"]["namedPublicInputs"]
    named_priv = data["witnessExport"]["namedPrivateWitness"]
    list_pub = data["witnessExport"]["publicInputs"]
    list_priv = data["witnessExport"]["privateWitness"]

    if len(pub_order) != len(list_pub):
        raise ValueError(f"Public input length mismatch: order={len(pub_order)} values={len(list_pub)}")

    if len(priv_order) != len(list_priv):
        raise ValueError(f"Private witness length mismatch: order={len(priv_order)} values={len(list_priv)}")

    for key in pub_order:
        if key not in named_pub:
            raise KeyError(f"Missing named public input: {key}")

    for key in priv_order:
        if key not in named_priv:
            raise KeyError(f"Missing named private witness: {key}")

    if data["submissionContractMethod"] != "submitAgentDecisionZK":
        raise ValueError(
            f"Unexpected submission contract method: {data['submissionContractMethod']}"
        )

    if data["proofSystem"]["adapterStatus"] != "skeleton_ready":
        raise ValueError(
            f"Unexpected adapter status: {data['proofSystem']['adapterStatus']}"
        )

    print("AUTH_V1 real prover adapter validated successfully")
    print("Validated file ->", INPUT_FILE)
    print("Submission method ->", data["submissionContractMethod"])
    print("Public inputs ->", len(pub_order))
    print("Private witness values ->", len(priv_order))

if __name__ == "__main__":
    main()
