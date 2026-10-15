# TNSM-2026-12002 major revision

This revision narrows the contribution to auditable governance of untrusted model recommendations under the released experimental conditions. It includes the main and supplementary LaTeX source, unchanged retained-data archives, derived replay results, formal check logs, editable figures and a factual point-by-point response draft.

The starting point is the TNSM artifact branch `tnsm-supervisor-revision-step1-20260808-1837`, commit `6f63fed2e20e467fa3139623c83648ca9baf4b73`. The repository default branch is older. The full main/supplement source was recovered from the authors' Overleaf archive; it is not asserted to be the exact private source of the October working PDF. `SOURCE_PROVENANCE.json` identifies the source and unchanged experiment archives by SHA-256. Historical workflows and raw records are preserved.

## Completed changes

- Main IV-A/Table II distinguishes implemented, simulated, finite-model and future components. VI-D/Table IV documents all six author-designed cases and experimental policy rules.
- Abstract, semantic table and Fig. 4 consistently report agreement with the frozen oracle. There are six scenarios, not 180 independent incidents. All reference action classes are HUMAN or NEVER.
- VII-C/Table IX exposes the baseline differences: calls, prompts, budgets, sampling, timing boundaries, dates and governance. No causal framework comparison is claimed.
- VII-J/Table XIII adds a paired retained-output replay, plus a timing decomposition of one archived S2 trace. This is not new inference or a measurement of component overhead.
- V and the supplement specify six exact invariants, reproduce the original finite model, add a zero-input probe and retain three expected mutation counterexamples.
- VII-A expands operator review and unverified deployment obligations. A separate inactive V2 callback export rejects string Boolean coercion; local payload tests are included.
- Editable TikZ figures replace supplementary screenshots. Fig. S1 is a functional map generated from archived JSON, with a complete edge-level draw.io diagram and node inventory. It is not an AI-detector figure or execution proof.
- `RESPONSE_TO_REVIEWERS.md` answers all eight R1 and three R2 comments. The supervisor's former Table IV request is distinct from R2.3, which concerns safety versus semantics.

## Important corrections

The proposed Agentic-RAG NEVER-class recall is **19/20 = 95.0%**, not the previous 100% entry. It is final-action-class recall, not the execution-flag rate. The audit reconstructs this count from preserved repeat-stability histograms and rejects unstable decision marginals that would make the joint count unidentified.

The original 180 proposed-workflow per-run report/manifest packages have **not been recovered in this revision archive**. Proposed-workflow metrics are checked against retained aggregate/repeat-stability summaries, not independently recomputed from those missing raw packages. The raw LangGraph/Qwen baseline records and frozen reference are included. The historical DOI (10.5281/zenodo.21939774) is a versioned source snapshot; it must not be represented as containing these new revision scripts. A self-contained revision repository ZIP is supplied separately, pending public publication. No missing data are reconstructed or claimed as a new experiment.

The archived baseline `unsafe_execution` field means `oracle_action_class == NEVER and final_prediction.execute == true`. No executor is invoked by either baseline runner. Qwen's nine such flags are erroneous output declarations, not observed executions. The broader non-automatic-reference count is 38. A replay with execution disabled changes these counts to zero while leaving decision agreement 38/60 and action agreement 11/60. LangGraph remains 150/180 and 120/180, with zero declarations. Original fields are unchanged; corrected interpretations are derived separately.

The original formal initialisation excludes a zero commitment. It checks 320 reachable states. A separate zero-input probe checks 480 states; three broken guards trigger their expected invariant violations. These are finite-model results, not deployed code refinement, liveness, authentication or cryptographic proof verification. Duplicate-commitment history is not modelled.

The live demonstration's ANCHORED status/local hash chain is separate from the public-testnet experiment. Its retained report marks external-chain evidence MISSING. The revision does not infer an external receipt for that decision from the separate testnet measurements.

## Reproduce without model credentials

Run from the repository root with Python 3.10+ and Node.js available:

```bash
python3 scripts/l4/tnsm_revision/audit_retained_revision_evidence.py
python3 scripts/l4/tnsm_revision/build_workflow_map.py
python3 -m unittest discover -s test/l4/tnsm_revision -p test_major_revision_evidence.py -v
python3 -m unittest discover -s test/l4/tnsm_revision -p test_revision_tools.py -v
node test/l4/tnsm_revision/test_review_payload_v2.cjs
```

The nine new evidence tests and 29 existing revision-tool tests pass, together with 14 callback cases. The archive audit rejects traversal and malformed/checksum-mismatched archives; validates all five internal manifests; joins 180 LangGraph and 60 Qwen records to the 180-cell frozen reference; verifies raw-response hashes; and reconstructs native guards before replay. It sends no provider requests and performs no actuation. Its outputs are `evidence/derived/retained_output_audit.json` and `retained_output_ablation.csv`.

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

`main.pdf` and `supplementary_material.pdf` mark revisions in blue; the clean wrappers suppress revision colour. All figures are native vector diagrams/charts with editable source. Compiled PDFs are delivery/build outputs rather than Git-tracked files. The current main manuscript has 14 pages and the supplement 14 pages; reconcile any private source changes and venue page requirements before submission.

The public-testnet table uses two panels at the manuscript's footnote size, rather than shrinking its text. Reference metadata have been checked against publisher/Crossref records. The acknowledgment identifies the actual AI assistance used for revision text, scripts and reconstructed figures.

## Remaining validation

The planned expert protocol treats action classes as nominal. Its archived linear-weighted action statistic requires an amended, frozen analysis plan before new labels are collected; no protocol amendment or expert study has been completed.

No independent expert annotation, new hosted-model inference, matched inference-time ablation, live rApp/A1/E2 integration or real operational-telemetry/noise validation was performed. The revised claims state these limits explicitly. Intended deliberative tasks still require task-specific deadline validation. Approval authentication, exact action binding, expiry, concurrent/replayed decisions, revocation and privileged approval need deployed gateway tests. The V2 export is inactive and does not establish those guarantees.

The authors should review the final source, references and response, reconcile later private Overleaf edits, and submit the marked manuscript and separate response by the decision letter's 6 December 2026 deadline. No journal-portal submission has been performed.
