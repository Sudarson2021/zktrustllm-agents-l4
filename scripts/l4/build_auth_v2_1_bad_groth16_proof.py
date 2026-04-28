import json
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "runtime_artifacts" / "l4" / "auth_v2_1" / "proof.frozen.json"
OUT = ROOT / "runtime_artifacts" / "l4" / "auth_v2_1" / "proof.bad.json"

with open(SRC, "r") as f:
    proof = json.load(f)

orig = int(proof["proof"]["a"][0], 16)
bad = orig ^ 1

proof["proof"]["a"][0] = hex(bad)

with open(OUT, "w") as f:
    json.dump(proof, f, indent=2)

print("Saved bad AUTH_V2.1 proof ->", OUT)
print("Original a[0] ->", hex(orig))
print("Tampered a[0] ->", proof["proof"]["a"][0])
