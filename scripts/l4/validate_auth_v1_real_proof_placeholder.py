import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.real.placeholder.json"

REQUIRED_TOP = [
    "schema",
    "meta",
    "proofSystem",
    "circuitName",
    "publicInputOrder",
    "publicInputs",
    "proof",
    "derived",
    "runtime",
    "proverNotes",
]

REQUIRED_PROOF = [
    "proofBlobHex",
    "proofPoints",
    "verifierCalldata",
    "note",
]

REQUIRED_DERIVED = [
    "proofDigest",
    "boundedActionMap",
]

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def require_keys(obj, keys, name):
    missing = [k for k in keys if k not in obj]
    if missing:
        raise KeyError(f"Missing keys in {name}: {missing}")

def norm_hex(x: str) -> str:
    x = x.lower()
    if not x.startswith("0x"):
        x = "0x" + x
    return x

def main():
    data = load_json(INPUT_FILE)

    require_keys(data, REQUIRED_TOP, "top-level")
    require_keys(data["proof"], REQUIRED_PROOF, "proof")
    require_keys(data["derived"], REQUIRED_DERIVED, "derived")

    if len(data["publicInputOrder"]) != len(data["publicInputs"]):
        raise ValueError(
            f"public input length mismatch: order={len(data['publicInputOrder'])}, values={len(data['publicInputs'])}"
        )

    digest_material = json.dumps(
        {
            "circuitName": data["circuitName"],
            "publicInputs": data["publicInputs"],
            "publicInputOrder": data["publicInputOrder"],
            "proofSystem": data["proofSystem"],
        },
        sort_keys=True,
    ).encode()

    recomputed = norm_hex(Web3.keccak(digest_material).hex())
    stored = norm_hex(data["derived"]["proofDigest"])

    if stored != recomputed:
        raise ValueError(f"proofDigest mismatch: expected {recomputed}, got {stored}")

    data["derived"]["proofDigest"] = stored
    data["proof"]["proofBlobHex"] = norm_hex(data["proof"]["proofBlobHex"])

    with open(INPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("AUTH_V1 real-proof placeholder validated successfully")
    print("Normalized file ->", INPUT_FILE)
    print("proofDigest ->", stored)

if __name__ == "__main__":
    main()
