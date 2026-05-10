#!/usr/bin/env python3

import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "results/l4_supervisor_handoff_bundle"
FILES_DIR = OUT_DIR / "files"
DOC_DIR = ROOT / "docs/l4/supervisor_handoff"

OUT_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_JSON = OUT_DIR / "supervisor_handoff_manifest.json"
MANIFEST_CSV = OUT_DIR / "supervisor_handoff_manifest.csv"
MANIFEST_MD = DOC_DIR / "SUPERVISOR_HANDOFF_BUNDLE.md"
ZIP_PATH = OUT_DIR / "zktrustllm_l4_supervisor_handoff_bundle.zip"

ARTIFACTS = [
    {
        "category": "Main journal draft",
        "path": "results/l4_report_pdf/zktrustllm_agents_l4_journal_draft.pdf",
        "description": "Compiled LaTeX journal draft PDF for supervisor review.",
        "required": True,
    },
    {
        "category": "LaTeX source",
        "path": "docs/paper/zktrustllm_agents_l4_journal_draft.tex",
        "description": "LaTeX source of the journal draft.",
        "required": True,
    },
    {
        "category": "Manuscript skeleton",
        "path": "docs/paper/zktrustllm_agents_l4_journal_manuscript_skeleton.md",
        "description": "Full Markdown journal manuscript skeleton.",
        "required": True,
    },
    {
        "category": "Methodology",
        "path": "docs/paper/l4_journal_methodology_policy_gated_automation_audit_anchor.md",
        "description": "Journal-ready methodology section.",
        "required": True,
    },
    {
        "category": "Results narrative",
        "path": "docs/paper/l4_results_narrative_steps96_109.md",
        "description": "Journal-ready results narrative.",
        "required": True,
    },
    {
        "category": "Architecture and tables",
        "path": "docs/paper/l4_journal_ready_architecture_tables_steps96_105.md",
        "description": "Journal-ready architecture figure and table explanation.",
        "required": True,
    },
    {
        "category": "Architecture figure",
        "path": "results/l4_journal_ready/figures/figure_6_1_l4_policy_gated_agentic_automation_architecture.pdf",
        "description": "Journal-ready architecture figure in PDF format.",
        "required": True,
    },
    {
        "category": "Architecture figure",
        "path": "results/l4_journal_ready/figures/figure_6_1_l4_policy_gated_agentic_automation_architecture.png",
        "description": "Journal-ready architecture figure in PNG format.",
        "required": True,
    },
    {
        "category": "Milestone report",
        "path": "results/l4_report_pdf/zktrustllm_l4_supervisor_milestone_report_steps96_105.pdf",
        "description": "Supervisor milestone report covering Steps 96-105.",
        "required": True,
    },
    {
        "category": "Repeated-run statistics",
        "path": "docs/l4/repeated_run_statistics/L4_REPEATED_RUN_STATISTICS.md",
        "description": "Repeated-run statistics report.",
        "required": True,
    },
    {
        "category": "Repeated-run statistics",
        "path": "results/l4_report_pdf/zktrustllm_l4_repeated_run_statistics_steps96_107.pdf",
        "description": "Repeated-run statistics PDF.",
        "required": True,
    },
    {
        "category": "Audit ledger",
        "path": "docs/l4/automation_audit_ledger/AUTOMATION_AUDIT_LEDGER.md",
        "description": "Hash-chained automation audit ledger report.",
        "required": True,
    },
    {
        "category": "Audit ledger",
        "path": "results/l4_automation_audit_ledger/automation_audit_ledger.json",
        "description": "Machine-readable hash-chained audit ledger.",
        "required": True,
    },
    {
        "category": "IPFS/blockchain anchor",
        "path": "docs/l4/audit_anchor/AUDIT_LEDGER_ANCHOR_RECORD.md",
        "description": "IPFS and blockchain-ready anchor record.",
        "required": True,
    },
    {
        "category": "On-chain validation",
        "path": "docs/l4/onchain_anchor/ONCHAIN_AUDIT_ANCHOR_REGISTRY.md",
        "description": "Local Hardhat on-chain audit-anchor validation documentation.",
        "required": True,
    },
    {
        "category": "Negative security",
        "path": "docs/l4/onchain_anchor_negative/ONCHAIN_ANCHOR_NEGATIVE_SECURITY.md",
        "description": "Replay and invalid-commitment rejection validation.",
        "required": True,
    },
    {
        "category": "Persistent Hardhat",
        "path": "docs/l4/persistent_hardhat_anchor/PERSISTENT_HARDHAT_AUDIT_ANCHOR_VALIDATION.md",
        "description": "Persistent local Hardhat audit-anchor validation.",
        "required": True,
    },
    {
        "category": "Compile validation",
        "path": "docs/l4/latex_compile_validation/LATEX_COMPILE_VALIDATION.md",
        "description": "LaTeX compile validation report.",
        "required": True,
    },
]

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_name(path):
    return str(path).replace("/", "__")


def build_bundle():
    if FILES_DIR.exists():
        shutil.rmtree(FILES_DIR)
    FILES_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    missing_required = []

    for item in ARTIFACTS:
        source = ROOT / item["path"]
        exists = source.exists()
        copied_to = ""

        if exists:
            target = FILES_DIR / safe_name(item["path"])
            shutil.copy2(source, target)
            copied_to = str(target.relative_to(ROOT))
            size_bytes = target.stat().st_size
            sha256 = sha256_file(target)
        else:
            size_bytes = 0
            sha256 = ""
            if item["required"]:
                missing_required.append(item["path"])

        rows.append({
            "category": item["category"],
            "description": item["description"],
            "required": item["required"],
            "exists": exists,
            "sourcePath": item["path"],
            "bundlePath": copied_to,
            "sizeBytes": size_bytes,
            "sha256": sha256,
        })

    with MANIFEST_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "experiment": "step114_supervisor_handoff_bundle",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "artifactCount": len(rows),
        "copiedArtifactCount": sum(1 for r in rows if r["exists"]),
        "missingRequiredCount": len(missing_required),
        "missingRequired": missing_required,
        "overallStatus": "PASS" if not missing_required else "REVIEW_REQUIRED",
        "manifestJson": str(MANIFEST_JSON.relative_to(ROOT)),
        "manifestCsv": str(MANIFEST_CSV.relative_to(ROOT)),
        "manifestMarkdown": str(MANIFEST_MD.relative_to(ROOT)),
        "zipBundle": str(ZIP_PATH.relative_to(ROOT)),
    }

    MANIFEST_JSON.write_text(json.dumps({
        **summary,
        "artifacts": rows,
    }, indent=2) + "\n")

    lines = [
        "# Step 114 Supervisor Handoff Bundle",
        "",
        "## Purpose",
        "",
        "This bundle collects the main supervisor/journal artifacts for the ZKTrustLLM-Agents L4 automation, audit, IPFS, and on-chain validation milestone.",
        "",
        "## Bundle Summary",
        "",
        f"- Created at: `{summary['createdAt']}`",
        f"- Artifact count: `{summary['artifactCount']}`",
        f"- Copied artifact count: `{summary['copiedArtifactCount']}`",
        f"- Missing required artifacts: `{summary['missingRequiredCount']}`",
        f"- Overall status: **{summary['overallStatus']}**",
        f"- ZIP bundle: `{summary['zipBundle']}`",
        "",
        "## Included Artifacts",
        "",
        "| Category | Exists | Source | Bundle path |",
        "|---|---:|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row['category']} | {row['exists']} | `{row['sourcePath']}` | `{row['bundlePath']}` |"
        )

    lines.extend([
        "",
        "## Research Meaning",
        "",
        "Step 114 creates a clean supervisor handoff package. It allows the supervisor to inspect the current milestone without navigating the whole repository.",
        "",
        "The package includes the compiled journal draft, LaTeX source, methodology, results narrative, architecture figure, repeated-run statistics, audit ledger, IPFS anchor, on-chain validation, negative-security validation, persistent Hardhat validation, and LaTeX compile validation.",
        "",
        "## Safety Boundary",
        "",
        "This step only copies existing files and creates a ZIP bundle. It does not rerun experiments, deploy contracts, push code, submit papers, email anyone, or modify Git history.",
        "",
    ])

    MANIFEST_MD.write_text("\n".join(lines) + "\n")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(MANIFEST_JSON, MANIFEST_JSON.relative_to(OUT_DIR.parent))
        z.write(MANIFEST_CSV, MANIFEST_CSV.relative_to(OUT_DIR.parent))
        z.write(MANIFEST_MD, MANIFEST_MD.relative_to(OUT_DIR.parent))
        for copied in FILES_DIR.glob("*"):
            z.write(copied, copied.relative_to(OUT_DIR.parent))

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    build_bundle()
