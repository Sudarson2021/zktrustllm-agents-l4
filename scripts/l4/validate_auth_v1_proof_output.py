import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.mock.json"

REQUIRED_TOP = [
    "schema",
    "meta",
    "verifierMode",
    "publicInputOrder",
    "publicInputsRaw",
    "publicInputsField",
    "privateWitnessRaw",
    "derivedDigests",
    "proof",
    "runtime",
]

REQUIRED_PROOF = [
    "proofBlobHex",
    "proofDigest",
    "note",
]

REQUIRED_DERIVED = [
    "capabilityWitnessDigestDraft",
    "actionWitnessDigestDraft",
    "publicInputDigest",
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
    int(x[2:], 16)
    return x

def main():
    data = load_json(INPUT_FILE)

    require_keys(data, REQUIRED_TOP, "top-level")
    require_keys(data["proof"], REQUIRED_PROOF, "proof")
    require_keys(data["derivedDigests"], REQUIRED_DERIVED, "derivedDigests")

    proof_blob_hex = norm_hex(data["proof"]["proofBlobHex"])
    proof_digest = norm_hex(data["proof"]["proofDigest"])
    public_input_digest = norm_hex(data["derivedDigests"]["publicInputDigest"])

    proof_blob_bytes = Web3.to_bytes(hexstr=proof_blob_hex)
    recomputed_digest = Web3.keccak(proof_blob_bytes).hex()

    if proof_digest != recomputed_digest:
        raise ValueError(
            f"proofDigest mismatch: expected {recomputed_digest}, got {proof_digest}"
        )

    if data["verifierMode"] == "mock_v2_structured_digest":
        if proof_digest != public_input_digest:
            raise ValueError(
                f"mock_v2 digest mismatch: proofDigest {proof_digest} != publicInputDigest {public_input_digest}"
            )

    data["proof"]["proofBlobHex"] = proof_blob_hex
    data["proof"]["proofDigest"] = proof_digest
    data["derivedDigests"]["publicInputDigest"] = public_input_digest

    with open(INPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("AUTH_V1 proof output validated successfully")
    print("Normalized file ->", INPUT_FILE)
    print("proofDigest ->", proof_digest)

if __name__ == "__main__":
    main()
