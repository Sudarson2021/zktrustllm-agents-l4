#!/usr/bin/env python3

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

LEDGER_JSON = ROOT / "results/l4_automation_audit_ledger/automation_audit_ledger.json"

OUT_DIR = ROOT / "results/l4_audit_anchor"
DOC_DIR = ROOT / "docs/l4/audit_anchor"

OUT_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

ANCHOR_JSON = OUT_DIR / "audit_ledger_anchor_record.json"
ANCHOR_MD = DOC_DIR / "AUDIT_LEDGER_ANCHOR_RECORD.md"
ANCHOR_TX_JSON = OUT_DIR / "audit_ledger_blockchain_ready_anchor.json"
IPFS_STDOUT = OUT_DIR / "ipfs_add_stdout.log"
IPFS_STDERR = OUT_DIR / "ipfs_add_stderr.log"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def run_ipfs_add(path: Path):
    ipfs_bin = shutil.which("ipfs")
    if not ipfs_bin:
        return {
            "attempted": False,
            "status": "IPFS_BINARY_NOT_FOUND",
            "cid": None,
            "reason": "ipfs command not found on PATH.",
        }

    cmd = [ipfs_bin, "add", "-Q", str(path)]

    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )

    IPFS_STDOUT.write_text(proc.stdout or "")
    IPFS_STDERR.write_text(proc.stderr or "")

    if proc.returncode != 0:
        return {
            "attempted": True,
            "status": "IPFS_ADD_FAILED",
            "cid": None,
            "returnCode": proc.returncode,
            "reason": (proc.stderr or "").strip()[:500],
        }

    cid = (proc.stdout or "").strip()

    return {
        "attempted": True,
        "status": "IPFS_ADD_PASS",
        "cid": cid,
        "returnCode": proc.returncode,
        "stdoutLog": rel(IPFS_STDOUT),
        "stderrLog": rel(IPFS_STDERR),
    }


def build_blockchain_ready_anchor(anchor_record):
    payload = {
        "anchorType": "ZKTrustLLM_L4_AUTOMATION_AUDIT_LEDGER_ANCHOR",
        "createdAt": anchor_record["createdAt"],
        "ledgerHash": anchor_record["ledger"]["finalLedgerHash"],
        "ledgerSha256": anchor_record["ledger"]["ledgerFileSha256"],
        "ledgerPath": anchor_record["ledger"]["ledgerPath"],
        "ipfsCid": anchor_record["ipfs"].get("cid"),
        "ipfsStatus": anchor_record["ipfs"].get("status"),
        "researchMeaning": "Blockchain-ready commitment for the Step 101 hash-chained L4 automation audit ledger.",
    }

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["anchorCommitmentHash"] = sha256_bytes(canonical)

    return payload


def write_markdown(anchor_record, tx_payload):
    lines = [
        "# Step 102 IPFS / Blockchain-Ready Audit Ledger Anchor",
        "",
        "## Purpose",
        "",
        "This step anchors the Step 101 hash-chained automation audit ledger into an IPFS-ready and blockchain-ready commitment record.",
        "",
        "## Anchor Summary",
        "",
        f"- Created at: `{anchor_record['createdAt']}`",
        f"- Ledger path: `{anchor_record['ledger']['ledgerPath']}`",
        f"- Ledger final hash: `{anchor_record['ledger']['finalLedgerHash']}`",
        f"- Ledger file SHA-256: `{anchor_record['ledger']['ledgerFileSha256']}`",
        f"- IPFS status: `{anchor_record['ipfs']['status']}`",
        f"- IPFS CID: `{anchor_record['ipfs'].get('cid')}`",
        f"- Blockchain-ready commitment hash: `{tx_payload['anchorCommitmentHash']}`",
        "",
        "## Research Meaning",
        "",
        "Step 102 connects the automation governance layer to the ZKTrustLLM evidence/trust-plane design.",
        "",
        "The automation ledger can now be referenced by a content-addressed IPFS CID when IPFS is available, and by a blockchain-ready commitment hash even when IPFS is unavailable.",
        "",
        "This strengthens the PhD claim that the L4 agentic automation process is not only executable, but also auditable, reproducible, and commitment-bound.",
        "",
        "## Safety Boundary",
        "",
        "This step does not send a blockchain transaction by default.",
        "",
        "It creates an anchor record and a blockchain-ready commitment payload. Actual on-chain submission should remain a separate, approval-gated step.",
        "",
        "## Generated Files",
        "",
        f"- Anchor JSON: `{rel(ANCHOR_JSON)}`",
        f"- Blockchain-ready anchor JSON: `{rel(ANCHOR_TX_JSON)}`",
        f"- Anchor Markdown: `{rel(ANCHOR_MD)}`",
    ]

    ANCHOR_MD.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ipfs",
        action="store_true",
        help="Attempt ipfs add for the Step 101 ledger JSON.",
    )
    args = parser.parse_args()

    if not LEDGER_JSON.exists():
        raise SystemExit(f"Missing Step 101 ledger JSON: {LEDGER_JSON}")

    ledger = json.loads(LEDGER_JSON.read_text())

    ipfs_result = run_ipfs_add(LEDGER_JSON) if args.ipfs else {
        "attempted": False,
        "status": "IPFS_NOT_REQUESTED",
        "cid": None,
        "reason": "Run with --ipfs to attempt ipfs add.",
    }

    anchor_record = {
        "experiment": "step102_ipfs_blockchain_ready_audit_anchor",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "ledger": {
            "ledgerPath": rel(LEDGER_JSON),
            "ledgerFileSha256": sha256_file(LEDGER_JSON),
            "finalLedgerHash": ledger.get("finalLedgerHash"),
            "entryCount": ledger.get("entryCount"),
            "missingArtifacts": ledger.get("missingArtifacts", []),
        },
        "ipfs": ipfs_result,
        "governanceBoundary": {
            "doesNotPushCode": True,
            "doesNotDeploy": True,
            "doesNotSubmitPapers": True,
            "doesNotSendBlockchainTransaction": True,
            "onChainSubmissionRequiresSeparateApproval": True,
        },
    }

    tx_payload = build_blockchain_ready_anchor(anchor_record)

    ANCHOR_JSON.write_text(json.dumps(anchor_record, indent=2))
    ANCHOR_TX_JSON.write_text(json.dumps(tx_payload, indent=2))
    write_markdown(anchor_record, tx_payload)

    print(json.dumps({
        "experiment": anchor_record["experiment"],
        "ledgerFinalHash": anchor_record["ledger"]["finalLedgerHash"],
        "ipfsStatus": anchor_record["ipfs"]["status"],
        "ipfsCid": anchor_record["ipfs"].get("cid"),
        "anchorCommitmentHash": tx_payload["anchorCommitmentHash"],
        "anchorJson": rel(ANCHOR_JSON),
        "blockchainReadyAnchorJson": rel(ANCHOR_TX_JSON),
        "anchorMarkdown": rel(ANCHOR_MD),
    }, indent=2))


if __name__ == "__main__":
    main()
