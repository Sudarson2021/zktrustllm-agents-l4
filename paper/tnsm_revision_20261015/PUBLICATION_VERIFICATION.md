# Verified v1.2.0 experiment archive and final citation update

The author published GitHub release `tnsm-artifact-v1.2.0` and verified Zenodo record **23425828**, version **1.2.0**, DOI **10.5281/zenodo.23425828**, concept DOI **10.5281/zenodo.21939773** on 16 October 2026.

The download was 34,969,945 bytes and passed Zenodo's reported transfer checksum. Its SHA-256 was `204512d3717d0599996c5f6e03bd21fb34425e51c14485364ef7d2917316f4f2`. A read-only comparison on the author's `clws00176` host matched **all 1,648 tracked files** against commit `f0a0e6fee0fc3b70b4c6520abeae6b9f637ffdf5`, including the original recovered 180-run bundle, new matched-study bundle and three archived R1 PDFs. Both evidence-bundle SHA-256 values matched the previously retained originals.

These publication checks are supported by author-executed commands and pasted terminal outputs. The assistant did not independently download the Zenodo ZIP. The metadata and script outputs are retained on the author's host in `~/Downloads/TNSM_12002_Zenodo_v1.2.0_verification/record.json` and `archive_verification.json`. `ARTIFACT_PUBLICATION.json` records the results and source of verification explicitly. The web retrieval tool could not access the record during this update; no successful assistant-side retrieval is claimed.

The published tag/Zenodo archive identifies the experiment snapshot. The later submission-document commit adds its verified DOI to the manuscript, supplement, reviewer response and repository citation metadata. Its PDFs therefore differ from the pre-DOI R1 PDFs inside the archive. No measured result, oracle label, provider response, pilot, failure or frozen protocol is changed by this documentation update. Cite the version DOI for the released experiment evidence; do not claim that the later PDF bytes were part of the already verified ZIP.

The GitHub `published` webhook returned 409 and the adjacent `released` event 202. Those codes alone were not used to declare success; the actual v1.2.0 record, file transfer and source-content comparison established publication. No redelivery or duplicate deposit was required.

## Supervisor review clarification

The recalled supervisor review corresponds to the 18 July 2026 S2 human-approval demonstration. The preserved callback uses `reviewer_id=supervisor-demo-reviewer`, claimed role `mno_approver`, and approval only for a bounded simulated-action ledger. It does not identify a particular supervisor or document independent labels for six scenarios. The 14 August status record explicitly defers independent human-label validation. The original oracle manifest sets `expert_verified=false`, `oracle_verified=true`, and has no expert reviewers for all six scenarios. Independent expert validation therefore remains a limitation. No informal review is converted into an unperformed annotation study.

## Recheck against the immutable experiment commit

For future checks after the citation update, compare the Zenodo ZIP to the Git objects at `f0a0e6fee0fc3b70b4c6520abeae6b9f637ffdf5`, rather than the later document worktree. The original author comparison required a clean worktree at that commit. A new temporary worktree at that immutable commit reproduces the original procedure without reverting document changes. Do not move the published tag.

Sources:

- https://doi.org/10.5281/zenodo.23425828
- https://github.com/Sudarson2021/zktrustllm-agents-l4/releases/tag/tnsm-artifact-v1.2.0
- https://github.com/Sudarson2021/zktrustllm-agents-l4/blob/tnsm-artifact-v1.2.0/docs/l4/supervisor_258/evidence/final_paper_n8n_20260718/live_run/review_request.json
- https://github.com/Sudarson2021/zktrustllm-agents-l4/blob/tnsm-artifact-v1.2.0/docs/journal/tnsm_revision_20260808/SUPERVISOR_STATUS_20260814.md
