import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CIRCUIT_FILE = ROOT / "circuits" / "auth_v1.zok"
TEMPLATE_FILE = ROOT / "configs" / "l4" / "auth_v1_circuit_template.json"
WITNESS_FILE = ROOT / "artifacts" / "out_l4" / "witness_input.auth_v1.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def parse_circuit_params(text: str):
    m = re.search(r"def\s+main\s*\((.*?)\)\s*\{", text, re.DOTALL)
    if not m:
        raise ValueError("Could not locate def main(...) in circuit")

    raw = m.group(1)
    parts = [p.strip() for p in raw.split(",") if p.strip()]

    public_params = []
    private_params = []

    for p in parts:
        p = " ".join(p.split())
        if p.startswith("private field "):
            name = p.replace("private field ", "").strip()
            private_params.append(name)
        elif p.startswith("field "):
            name = p.replace("field ", "").strip()
            public_params.append(name)
        else:
            raise ValueError(f"Unrecognized parameter format: {p}")

    return public_params, private_params

def main():
    if not CIRCUIT_FILE.exists():
        raise FileNotFoundError(f"Missing circuit file: {CIRCUIT_FILE}")
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"Missing template file: {TEMPLATE_FILE}")
    if not WITNESS_FILE.exists():
        raise FileNotFoundError(f"Missing witness file: {WITNESS_FILE}")

    circuit_text = CIRCUIT_FILE.read_text()
    template = load_json(TEMPLATE_FILE)
    witness = load_json(WITNESS_FILE)

    circuit_public, circuit_private = parse_circuit_params(circuit_text)

    expected_public = template["publicInputOrder"]
    expected_private = template["privateWitnessOrder"]

    if circuit_public != expected_public:
        raise ValueError(
            f"Public parameter order mismatch.\n"
            f"Circuit : {circuit_public}\n"
            f"Template: {expected_public}"
        )

    if circuit_private != expected_private:
        raise ValueError(
            f"Private parameter order mismatch.\n"
            f"Circuit : {circuit_private}\n"
            f"Template: {expected_private}"
        )

    witness_public = witness["publicOrder"]
    witness_private = witness["privateOrder"]

    if witness_public != expected_public:
        raise ValueError(
            f"Witness public order mismatch.\n"
            f"Witness : {witness_public}\n"
            f"Template: {expected_public}"
        )

    if witness_private != expected_private:
        raise ValueError(
            f"Witness private order mismatch.\n"
            f"Witness : {witness_private}\n"
            f"Template: {expected_private}"
        )

    if len(witness["publicInputs"]) != len(expected_public):
        raise ValueError(
            f"Public input count mismatch: {len(witness['publicInputs'])} vs {len(expected_public)}"
        )

    if len(witness["privateWitness"]) != len(expected_private):
        raise ValueError(
            f"Private witness count mismatch: {len(witness['privateWitness'])} vs {len(expected_private)}"
        )

    print("AUTH_V1 circuit interface validated successfully")
    print("Circuit file ->", CIRCUIT_FILE)
    print("Public params ->", len(expected_public), expected_public)
    print("Private params ->", len(expected_private), expected_private)

if __name__ == "__main__":
    main()
