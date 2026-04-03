import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACE_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.cid.json"

def main():
    if not TRACE_FILE.exists():
        raise FileNotFoundError(f"Missing trace bundle: {TRACE_FILE}")

    result = subprocess.run(
        ["ipfs", "add", "-q", str(TRACE_FILE)],
        capture_output=True,
        text=True,
        check=True
    )

    cid = result.stdout.strip().splitlines()[-1]

    out = {
        "traceFile": str(TRACE_FILE),
        "cid": cid
    }

    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Pinned trace bundle ->", cid)
    print("Saved CID record ->", OUT_FILE)

if __name__ == "__main__":
    main()
