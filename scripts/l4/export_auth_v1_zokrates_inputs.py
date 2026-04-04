import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WITNESS_FILE = ROOT / "artifacts" / "out_l4" / "witness_input.auth_v1.json"
TEMPLATE_FILE = ROOT / "configs" / "l4" / "auth_v1_circuit_template.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "zokrates_input.auth_v1.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    witness = load_json(WITNESS_FILE)
    template = load_json(TEMPLATE_FILE)

    public_order = template["publicInputOrder"]
    private_order = template["privateWitnessOrder"]

    named_pub = witness["namedPublicInputs"]
    named_priv = witness["namedPrivateWitness"]

    public_inputs = [named_pub[k] for k in public_order]
    private_witness = [named_priv[k] for k in private_order]
    flat_args = public_inputs + private_witness

    cli_example = "zokrates compute-witness -a " + " ".join(flat_args)

    out = {
        "schema": "auth_v1_zokrates_input",
        "meta": {
            "taskId": witness["meta"]["taskId"],
            "targetAgent": witness["meta"]["targetAgent"],
            "traceCID": witness["meta"]["traceCID"],
            "sourceWitnessFile": str(WITNESS_FILE),
            "sourceTemplateFile": str(TEMPLATE_FILE),
        },
        "circuitName": template["circuitName"],
        "proofSystemTarget": template["proofSystemTarget"],
        "publicInputOrder": public_order,
        "privateWitnessOrder": private_order,
        "publicInputs": public_inputs,
        "privateWitness": private_witness,
        "flatArguments": flat_args,
        "zokratesCliExample": cli_example,
        "counts": {
            "publicInputs": len(public_inputs),
            "privateWitness": len(private_witness),
            "totalArguments": len(flat_args),
        },
        "notes": {
            "argumentOrder": "public inputs first, then private witness values",
            "encoding": "decimal strings",
            "status": "bridge_placeholder_ready",
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved ZoKrates input export ->", OUT_FILE)
    print("Total arguments ->", len(flat_args))

if __name__ == "__main__":
    main()
