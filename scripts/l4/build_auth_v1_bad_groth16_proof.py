import json
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "artifacts" / "out_l4" / "zokrates_docker" / "proof.frozen.json"
OUT = ROOT / "artifacts" / "out_l4" / "zokrates_docker" / "proof.bad.json"

with open(SRC, "r") as f:
    proof = json.load(f)

orig = int(proof["proof"]["a"][0], 16)
bad = orig ^ 1  # flip last bit

proof["proof"]["a"][0] = hex(bad)

with open(OUT, "w") as f:
    json.dump(proof, f, indent=2)

print("Saved bad proof ->", OUT)
print("Original a[0]   ->", hex(orig))
print("Tampered a[0]   ->", proof["proof"]["a"][0])
