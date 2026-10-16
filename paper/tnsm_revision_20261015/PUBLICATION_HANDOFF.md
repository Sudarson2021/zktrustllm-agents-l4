# Import and publish the prepared matched-study revision

This is a new prepared v1.2.0. The old v1.1.0 release/tag and DOI identify a historical snapshot and are not overwritten. The package contains the final five PDFs, all tracked repository source/evidence, a Git bundle, an Overleaf source ZIP and checksums. No journal or remote publication has been performed in this audit.

## 1. Verify and extract the downloaded package

Run the downloaded ZIP's adjacent `.sha256` check, then extract it into a new directory under `~/Downloads`. Do not paste terminal prompts or console output into a command. Commands below assume the extracted directory is `~/Downloads/TNSM_12002_Matched_Revision_Package`.

```bash
(
set -euo pipefail
cd "$HOME/Downloads/TNSM_12002_Matched_Revision_Package"
sha256sum -c SHA256SUMS.txt
)
```

## 2. Import into the existing Git repository without changing the published branch

```bash
(
set -euo pipefail
REPO="$HOME/Downloads/TNSM_12002_R1_publication_20261016/repository"
PKG="$HOME/Downloads/TNSM_12002_Matched_Revision_Package"
DEST="$HOME/Downloads/TNSM_12002_R1_matched_final_20261016"
test ! -e "$DEST"
git -C "$REPO" bundle verify "$PKG/TNSM_12002_Matched_Revision.bundle"
git -C "$REPO" fetch "$PKG/TNSM_12002_Matched_Revision.bundle" \
  refs/heads/revision/tnsm-12002-matched-results-20261016
git -C "$REPO" worktree add \
  -b revision/tnsm-12002-matched-results-20261016 "$DEST" FETCH_HEAD
git -C "$DEST" status --short --branch
git -C "$DEST" rev-parse HEAD
)
```

The prerequisite is the already published commit `977a746e3b6f49ccb158b7dcd998c25872d729ec`. The package manifest gives the new exact head. If a branch/directory already exists, inspect it; do not force overwrite it. The full `repository/` snapshot is also supplied for offline inspection, but it has no `.git` history and should not be mistaken for the worktree created above.

## 3. Reproduce the evidence without paid calls

```bash
(
set -euo pipefail
cd "$HOME/Downloads/TNSM_12002_R1_matched_final_20261016"
python3 scripts/l4/tnsm_revision/audit_matched_inference_evidence.py
python3 scripts/l4/tnsm_revision/build_matched_inference_tables.py
python3 -m unittest discover -s test/l4/tnsm_revision -p 'test_*.py' -v
python3 -m unittest discover -s test/l4/tnsm_revision/matched_ablation -p 'test_*.py' -v
node test/l4/tnsm_revision/test_review_payload_v2.cjs
)
```

See `MATCHED_STUDY_REPRODUCIBILITY.md` for exact frozen-analyzer reproduction. Do not execute `launch.py run --live` for this step. All required observations are retained.

## 4. Review the exact documents before publishing

The current three marked PDFs are in `paper/tnsm_revision_20261015/submission/`; clean main and supplement are in the package's `documents/`. The main is 16 pages, supplement 17 and response six. Obtain coauthor approval and reconcile any later private Overleaf changes. `MATCHED_STUDY_AUDIT.md`, `SUPERVISOR_ALIGNMENT.md` and `SUBMISSION_READINESS.md` identify remaining limits.

Publish the review branch when ready:

```bash
(
set -euo pipefail
cd "$HOME/Downloads/TNSM_12002_R1_matched_final_20261016"
test -z "$(git status --porcelain)"
git push --set-upstream origin HEAD
)
```

## 5. Prepare a fresh release, preserving the old tag

Only after reviewing the new head, create a new tag and a draft release. No force flags are used. Inspect any existing v1.2.0 release instead of recreating it.

```bash
(
set -euo pipefail
cd "$HOME/Downloads/TNSM_12002_R1_matched_final_20261016"
test -z "$(git status --porcelain)"
git tag -a tnsm-artifact-v1.2.0 \
  -m "TNSM R1: audited 240-trial matched inference-block study"
git push origin refs/tags/tnsm-artifact-v1.2.0
SUB="paper/tnsm_revision_20261015/submission"
gh release create tnsm-artifact-v1.2.0 \
  --repo Sudarson2021/zktrustllm-agents-l4 --verify-tag --draft \
  --title "TNSM Reproducibility Artifact v1.2.0 — Matched Study R1" \
  --notes-file paper/tnsm_revision_20261015/MATCHED_STUDY_AUDIT.md \
  "$SUB/TNSM_12002_Manuscript_Marked.pdf" \
  "$SUB/TNSM_12002_Supplement_Marked.pdf" \
  "$SUB/TNSM_12002_R1_Response_to_Reviewers.pdf" \
  "$SUB/SHA256SUMS.txt"
)
```

After the draft is checked, publish it through GitHub or a separate explicit `gh release edit` operation. The raw matched archive, audit scripts and three marked PDFs are tracked in the tagged source, so they are part of that source snapshot rather than only release attachments.

## 6. Verify Zenodo before changing the paper's citation

A published GitHub release does not by itself confirm a new Zenodo DOI. The previous integration had a timeout and the last verified record was v1.0.0. Check the actual new Zenodo record, its version, concept DOI, GitHub relation, archived filename and contents. The concept DOI is `10.5281/zenodo.21939773`; the historical v1.0.0 version DOI is `10.5281/zenodo.21939774`. Neither is a newly verified v1.2.0 version DOI.

Download the new archived source and confirm it contains the matched evidence archive (SHA-256 `7ea6792f45aa6663e98869e81626f69bb37c58c1c4de161691545c70780bdd95`), the new audit code and the three correct submission PDFs. Only then record the actual new version DOI. If automatic archiving fails, inspect the Zenodo integration/record status before retrying; do not create an unrelated duplicate deposit or assume that a GitHub asset was archived.

For later document changes, rebuild and verify from source, commit a new reviewed revision, then use a fresh version/tag and archive version. Editing a DOI string or reusing a published tag does not create a new archived scientific version. The supplied builders regenerate tables from retained evidence and the response PDF from editable Markdown; no new inference is needed for ordinary prose/layout changes.
