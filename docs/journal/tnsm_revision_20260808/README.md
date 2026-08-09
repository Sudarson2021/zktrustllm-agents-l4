# IEEE TNSM supervisor revision package

Prepared on 2026-08-08 from the uploaded 14-page journal PDF and the measured
evidence on `evidence/permissioned-raft-qbft-measured` and
`evidence/final-paper-n8n-20260718`.

This package deliberately distinguishes a manuscript edit from a new empirical
claim. Text and figures below are ready to integrate, but the current journal
`main.tex` and the frozen 180-cell oracle records are not present in the
repository. Consequently, the PDF itself has not been silently reconstructed
or overwritten, and no missing experiment has been represented as completed.

## Recommended framing decision

Drop the undefined, project-specific `L4` label from the title and prose rather
than retroactively assigning it a meaning that was not used in the evaluated
system. Use:

> **ZKTrustLLM-Agents: Proof-Governed Auditable Zero-Trust Control for O-RAN
> Edge Security**

Rename `Full L4` to `Full system`, `No-ZK L4` to `No-ZK`, and `bounded agentic
L4 control plane` to `proof-governed agentic control plane`. If the authors
instead retain `L4`, they must supply a normative, consistently used definition
and explain why it is not an O-RAN or autonomy-level standard.

## Comment-by-comment disposition

| # | Supervisor request | Disposition | Artifact / remaining evidence |
|---:|---|---|---|
| 1 | Define L4 | **Draft ready** | Recommended removal and replacement map above. |
| 2 | Consolidate claim boundaries | **Draft ready** | One authoritative subsection in `main_text_dropins.tex`; retain only figure-specific cautions. |
| 3 | Rewrite abstract | **Draft ready** | Eight-sentence abstract in `main_text_dropins.tex`; consensus detail removed. |
| 4 | Reconsider title | **Draft ready** | `Auditable` title above. |
| 5 | Add operational “so what” | **Draft ready** | Non-RT RIC/A1 paragraph in `main_text_dropins.tex`. |
| 6 | External oracle baseline | **Completed; artifact validation passed** | The 180-cell digest-bound LangGraph run completed with 180 HTTP-200 responses; retain its publication archive. |
| 7 | O-RAN WG11 and 3GPP citations | **Draft ready** | Current WG11 versions plus exact public ETSI PAS/O-RAN document identifiers and 3GPP TS 33.501 V18.11.0 are in `references_additions.bib`. |
| 8 | Open-weights run | **Completed; artifact validation passed** | The digest-pinned Qwen3-4B Q4_K_M run completed on all 60 `AGENTIC_RAG` cells with 60 HTTP-200 responses; retain its publication archive. |
| 9 | Published [7]–[9] | **Checked** | [8] and [9] have DOI-backed versions; [7] reports IEEE Network acceptance but no DOI was located. See `references_additions.bib`. |
| 10 | Prompt injection | **Two-layer harness ready** | The 30-case live runner separately measures assessor compromise and deterministic control-plane containment; pilot and full execution remain required. |
| 11 | Explain gas difference | **Code/text fixed** | Generated consensus text now treats cross-chain gas as descriptive because no opcode traces were retained. |
| 12 | Caveat three-cluster bootstrap | **Code/text fixed** | Generated interval is labelled descriptive; nominal coverage is not asserted. |
| 13 | Align estimand orientation | **Code fixed** | Difference is now Sepolia minus IoTeX, aligned with the ratio. |
| 14 | Root-cause HTTP 500s | **Experiment complete** | All 53 records expose only the local webhook's generic HTTP-500 boundary; 53/53 response paths were overwritten by successful retries, so provider-versus-n8n attribution remains unresolved. All 39 affected cells recovered. |
| 15 | Model snapshots/decoding/prompts | **Stage 7A ready** | The provenance audit inventories all 720 R10 provider records, current source constants, and later reproducibility runs while reporting missing original fields as not recorded. |
| 16 | GPT-5.6/GPT-5.5 inconsistency | **Stage 7A ready** | The audit formally separates the GPT-5.6 R10 independent assessor from the GPT-5.5 planner in the separate supplemental Stage F/F chain. |
| 17 | Human oracle validation | **Execution required** | Deterministic 30-cell sampler and Cohen’s-kappa analyser are ready; independent O-RAN-literate labels are required. |
| 18 | Move Stage E/F and F/F | **Draft ready** | Two-sentence main-text pointer supplied; tables remain evidence for a supplement. |
| 19 | Replace Fig. 3 | **Figure ready** | Vector HUMAN-gate state transition in `figures/human_gate_state_machine.tex`. |
| 20 | Simplify Fig. 2 | **Figure ready** | Five-stage vector schematic in `figures/five_stage_pipeline.tex`; full n8n canvas should move to the supplement. |
| 21 | Merge small figures | **Figure ready** | Two composite PGFPlots figures replace six low-density figures. |
| 22 | Cut complexity table | **Draft ready** | Delete unmeasured asymptotic section/Table III; do not replace it with an unsupported scaling claim. |
| 23 | Replace novelty tick table | **Partially resolved** | Delete Table XII. A quantitative external-baseline table template is supplied, but population requires item 6. |
| 24 | Zenodo DOI | **Author action** | `CITATION.cff` and `.zenodo.json` are prepared. Author must create the release/deposit and insert the minted DOI. |
| 25 | Cover letter | **Draft ready** | `cover_letter.md`; the percentage of new material must be computed from the final source. |
| 26 | Bios/photos/page count | **Text ready / author action** | Biography text is supplied; author-approved headshots and final 14-page compile are required. |
| 27 | Availability/ethics statement | **Draft ready / confirm** | Statement supplied. Confirm institutional treatment of the proposed independent-label exercise before submission. |
| 28 | Reduce repeated “bounded” | **Edit map ready** | Use `language_cleanup.md` after integrating the current source. |

## Integration order

1. Add the current journal LaTeX source and frozen 180-cell benchmark to a
   revision branch.
2. Apply `main_text_dropins.tex`, the bibliography entries, and four vector
   figures; remove the old screenshots/tick table/complexity table and move
   Stage E/F–F/F to a supplement.
3. Run the external baseline, open-weights model, injection suite, metadata
   audit, HTTP analysis, and independent-label analysis.
4. Insert only results generated by retained machine-readable evidence.
5. Compile, render every page, check the 14-page limit, then freeze a release
   and mint the Zenodo DOI.

## Commands

```bash
bash scripts/l4/tnsm_revision/run_preflight.sh
python scripts/l4/tnsm_revision/run_langgraph_baseline.py --help
python scripts/l4/tnsm_revision/run_open_weights_baseline.py --help
python scripts/l4/tnsm_revision/generate_prompt_injection_suite.py --help
python scripts/l4/tnsm_revision/run_prompt_injection_experiment.py --help
python scripts/l4/tnsm_revision/score_prompt_injection.py --help
python scripts/l4/tnsm_revision/make_human_label_subset.py --help
python scripts/l4/tnsm_revision/analyze_human_labels.py --help
python scripts/l4/tnsm_revision/audit_model_metadata.py --help
python scripts/l4/tnsm_revision/analyze_http_failures.py --help
```

Use `EXPERIMENT_RUNBOOK.md` and stop after the first failed gate. The first
preflight is read-only and makes no provider call.
