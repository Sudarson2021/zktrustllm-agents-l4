# TNSM-2026-12002 major revision

This revision narrows the contribution to auditable governance of untrusted model recommendations under the released experimental conditions. It includes the main and supplementary LaTeX source, unchanged retained-data archives, derived replay results, formal check logs, editable figures and a factual point-by-point response draft.

The starting point is the TNSM artifact branch `tnsm-supervisor-revision-step1-20260808-1837`, commit `6f63fed2e20e467fa3139623c83648ca9baf4b73`. The repository default branch is older. The full main/supplement source was recovered from the authors' Overleaf archive; it is not asserted to be the exact private source of the October working PDF. `SOURCE_PROVENANCE.json` identifies the source and unchanged experiment archives by SHA-256. Historical workflows and raw records are preserved.

## Completed changes

- Main IV-A/Table II distinguishes implemented, simulated, finite-model and future components. VI-D/Table IV documents all six author-designed cases and experimental policy rules.
- Abstract, semantic table and Fig. 4 consistently report agreement with the frozen oracle. There are six scenarios, not 180 independent incidents. All reference action classes are HUMAN or NEVER.
- VII-C/Table IX exposes the baseline differences: calls, prompts, budgets, sampling, timing boundaries, dates and governance. No causal framework comparison is claimed.
- VII-J/Table XIII adds a paired retained-output replay, plus a timing decomposition of all 180 benchmark reports and one separate archived S2 demonstration. This is not new inference or a measurement of component overhead.
- V and the supplement specify six exact invariants, reproduce the original finite model, add a zero-input probe and retain three expected mutation counterexamples.
- VII-A expands operator review and unverified deployment obligations. A separate inactive V2 callback export rejects string Boolean coercion; local payload tests are included.
- Editable TikZ figures replace supplementary screenshots. Fig. S1 is a functional map generated from archived JSON, with a complete edge-level draw.io diagram and node inventory. It is not an AI-detector figure or execution proof.
- `RESPONSE_TO_REVIEWERS.md` answers all eight R1 and three R2 comments. The supervisor's former Table IV request is distinct from R2.3, which concerns safety versus semantics.
- `SUPERVISOR_ALIGNMENT.md` maps the original photographed instructions to exact manuscript changes and response positions. It now identifies the completed matched inference-block study and the remaining independent-expert/live-deployment limits. Supplement III now explains Figure S1's JSON/generator provenance and disclosed AI assistance; the operational-timescale paragraph cites ETSI TS 103 982 V14.0.0.

## Important corrections

The proposed Agentic-RAG NEVER-class recall is **19/20 = 95.0%**, not the previous 100% entry. It is final-action-class recall, not the execution-flag rate. The audit reconstructs this count from preserved repeat-stability histograms and rejects unstable decision marginals that would make the joint count unidentified.

The original **180 proposed-workflow run packages have been recovered and independently reanalysed**. The immutable input `evidence/inputs/TNSM_12002_Original_Evidence_Recovery.tar.gz` has SHA-256 `f842c0308d6e52904de71bb8886a044d733d474dde688ac906fbab0277ccb63d`. The original release/sidecar checksums and all 180 run manifests pass: 3,240 bound evidence files plus 180 manifests. Every recovered canonical report hash joins the previously released frozen oracle export. Reanalysis reproduces decision/action agreement, 95% NEVER recall, coverage, clustered intervals and recorded latency statistics. This is internal integrity and retained-result reproducibility, not independent provider authentication or validation of oracle correctness.

The historical DOI (10.5281/zenodo.21939774) remains a versioned source snapshot and does not include this newly recovered bundle or revision scripts. The verified v1.2.0 archive at https://doi.org/10.5281/zenodo.23425828 supplies both, plus the completed matched study. Recovery did not reconstruct missing records or rerun historical requests. A separate, newly collected inference study is documented below.

The archived baseline `unsafe_execution` field means `oracle_action_class == NEVER and final_prediction.execute == true`. No executor is invoked by either baseline runner. Qwen's nine such flags are erroneous output declarations, not observed executions. The broader non-automatic-reference count is 38. A replay with execution disabled changes these counts to zero while leaving decision agreement 38/60 and action agreement 11/60. LangGraph remains 150/180 and 120/180, with zero declarations. Original fields are unchanged; corrected interpretations are derived separately.

The original formal initialisation excludes a zero commitment. It checks 320 reachable states. A separate zero-input probe checks 480 states; three broken guards trigger their expected invariant violations. These are finite-model results, not deployed code refinement, liveness, authentication or cryptographic proof verification. Duplicate-commitment history is not modelled.

The live demonstration's ANCHORED status/local hash chain is separate from the public-testnet experiment. Its retained report marks external-chain evidence MISSING. The revision does not infer an external receipt for that decision from the separate testnet measurements.

## Reproduce without model credentials

Run from the repository root with Python 3.10+ and Node.js available:

```bash
python3 scripts/l4/tnsm_revision/audit_retained_revision_evidence.py
python3 scripts/l4/tnsm_revision/audit_recovered_proposed_evidence.py
python3 scripts/l4/tnsm_revision/build_workflow_map.py
python3 -m unittest discover -s test/l4/tnsm_revision -p 'test_*.py' -v
node test/l4/tnsm_revision/test_review_payload_v2.cjs
```

The completed checks comprise 47 revision/audit Python tests, 25 isolated matched-harness tests and 14 callback cases. The original 43 tests are supplemented by four independent matched-audit regressions. The archive audit rejects traversal and malformed/checksum-mismatched archives; validates all five internal manifests; joins 180 LangGraph and 60 Qwen records to the 180-cell frozen reference; verifies raw-response hashes; and reconstructs native guards before replay. It sends no provider requests and performs no actuation. Its outputs are `evidence/derived/retained_output_audit.json` and `retained_output_ablation.csv`.

The recovered-evidence audit additionally verifies the nine-file recovery bundle, 37 portable-manifest entries, 20 analysis-manifest entries and 14 benchmark-manifest entries using explicit path mapping. It verifies every original report, retrieval bundle, embedded provider/role record, 720 assessor and 720 role raw-response hashes, metadata/index/reference joins and 180 prompt-provenance joins. It regenerates the unchanged 20,000-replicate whole-scenario intervals. Outputs are `recovered_proposed_audit.json`, `recovered_proposed_cells.csv` and `recovered_proposed_timing.csv`.

All 180 reports provide disjoint timestamp intervals. Their aggregate-to-reflection phase medians are 57.698/75.637/79.608 s for No RAG/RAG/Agentic RAG; this phase contains the role chain and surrounding processing. Marginal phase medians do not sum to the median total. The original success-index timer is separate, and missing individual provider-call durations are not imputed. This remains descriptive stage attribution, not a matched framework/component ablation.

The figure generator checks the frozen export's 54 nodes (45 computational and 9 documentation) and full computational-node membership. The editable draw.io file includes all 49 exported edges. The compact TikZ figure is a functional grouping and does not reproduce every graph edge.

For formal checks, obtain `tla2tools.jar` from the official TLA+ tools release v1.7.4, which contains TLC 2.19, then verify SHA-256 `936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88`:

```bash
python3 scripts/l4/tnsm_revision/run_formal_revision_checks.py --jar /absolute/path/to/tla2tools.jar
```

Source: https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4

This runner uses temporary copies for mutations and never changes the original model. It exits successfully only if the two unmutated runs pass and all three negative controls fail on the intended invariant. Fresh logs contain runtime-specific paths/timestamps, so their byte hashes can differ while state counts and expected outcomes remain the reproducible checks.

## Compile the manuscript

Requires a TeX installation with IEEEtran dependencies, TikZ/PGFPlots, latexmk and pdfLaTeX. The supplied IEEEtran class retains its upstream licence header. From this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error main-clean.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary-clean.tex
```

`main.pdf` and `supplementary_material.pdf` mark revisions in blue; the clean wrappers suppress revision colour. All figures are native vector diagrams/charts with editable source. The submission directory contains the three current marked PDFs and their checksums. Clean counterparts are included in the delivery package. The current main manuscript has 16 pages and the supplement 17 pages; reconcile any private source changes before submission.

The public-testnet table uses two panels at the manuscript's footnote size, rather than shrinking its text. Reference metadata have been checked against publisher/Crossref records. The acknowledgment identifies the actual AI assistance used for revision text, scripts and reconstructed figures.

## Remaining validation

The planned expert protocol treats action classes as nominal. Its archived linear-weighted action statistic requires an amended, frozen analysis plan before new labels are collected; no protocol amendment or expert study has been completed.

The matched inference-block study is complete; independent expert annotation, live rApp/A1/E2 integration and real operational-telemetry/noise validation remain absent. The revised claims state these limits explicitly. Intended deliberative tasks still require task-specific deadline validation. Approval authentication, exact action binding, expiry, concurrent/replayed decisions, revocation and privileged approval need deployed gateway tests. The V2 export is inactive and does not establish those guarantees.

The authors should review the final source, references and response, reconcile later private Overleaf edits, and submit the marked manuscript and separate response by the decision letter's 6 December 2026 deadline. No journal-portal submission has been performed.

## New matched inference study: 16 October 2026

See `MATCHED_STUDY_AUDIT.md` and `MATCHED_STUDY_REPRODUCIBILITY.md`. The unchanged author archive supplies 240 trials and 1,080 calls. Its SHA-256 is `7ea6792f45aa6663e98869e81626f69bb37c58c1c4de161691545c70780bdd95`. The frozen analyzer reproduces exactly; an independent audit verifies manifests, matching, counts, quantiles, pairing and descriptive bootstrap intervals. New main VII-K/Tables XIV–XV and Supplement S11/Tables S16–S18 report the measured contrasts, mixed semantic results, 33 refusals, nine length terminations, six reference failures and one timeout. Four length-terminated reasoning-channel fallback objects were accepted by the frozen parser and are explicitly disclosed.

```bash
python3 scripts/l4/tnsm_revision/audit_matched_inference_evidence.py
python3 scripts/l4/tnsm_revision/build_matched_inference_tables.py
python3 -m unittest discover -s test/l4/tnsm_revision/matched_ablation -p 'test_*.py' -v
```

These commands make no provider requests. Do not change a frozen protocol or reuse a completed run name. Pilot results stay separate. The new study is a common-harness inference-block comparison, not a full n8n/LangGraph or operational O-RAN experiment.

The earlier `FINAL_ALIGNMENT_REVIEW_20261016.md` records a review before these new observations. The current `SUBMISSION_READINESS.md` supersedes its document counts and remaining-ablation status. The published v1.1.0 tag at `977a746e3b6f49ccb158b7dcd998c25872d729ec` remains unchanged. The experiment snapshot is now published as v1.2.0 at https://doi.org/10.5281/zenodo.23425828, commit f0a0e6f. The author matched all 1,648 archived files to that commit.

## Final verified-DOI document update

`PUBLICATION_VERIFICATION.md` and `ARTIFACT_PUBLICATION.json` record the author's download and full source comparison. The main, supplement and response now cite verified artifact version 1.2.0. These later citation updates do not replace the archived experiment snapshot or its earlier R1 PDFs. The final document checks are in `evidence/derived/doi_document_validation.json`; the previous `matched_document_validation.json` remains the pre-DOI build record.
