# Submission readiness review — 15 October 2026

**Status: prepared major-revision draft, subject to the evidence and author checks below.** The supplied decision is major revision, not acceptance or a request for a camera-ready article. The revision deadline in that letter is 6 December 2026. No journal submission was performed.

## Corrections from the final review

| Finding | Completed correction | Evidence and scope |
| --- | --- | --- |
| Proposed Agentic-RAG NEVER recall was overstated as 100% | Main Table VIII and nearby explanation now give **19/20 = 95%**; supplement and response agree | Derived from the archived final-class repeat histograms: S4 has nine NEVER and one HUMAN, S5 ten NEVER; this is not an execute-flag rate |
| Zero unsafe flags could be mistaken for semantic correctness | Semantic agreement, policy routing, output declarations and the single observed simulated write are separated | The retained-output replay changes execution declarations without changing semantic scores; no baseline executor is invoked |
| Original proposed raw-run coverage was unclear | Main VI-E, supplementary claim map/S10, README and response explicitly identify the missing per-run packages | The frozen reference and 240 baseline records are retained; proposed metrics are checked against retained summaries, not all original raw runs |
| Public-testnet table was reduced to very small text | Main Table X is split into two panels at footnote size | Numerical entries and denominator remain unchanged; small mathematical subscripts are distinct from body text |
| Nominal approval classes were treated as ordinal in a future protocol | Main VII-K and supplement S7.4 require amendment and freezing before collecting labels | No protocol amendment, new expert labels or completed human study is claimed; original protocol remains archival |
| Several bibliography entries mixed early-access and final metadata | Final volume, page, year and DOI fields corrected for Long, Boateng, Safety Copilot, multi-layer defence and Salmi | Publisher/Crossref records; no change to experimental results |
| Revision assistance lacked an explicit disclosure | Main acknowledgment identifies OpenAI Codex, affected sections and assistance with text, scripts and reconstructed figures | No new experimental responses or expert labels generated; authors retain final responsibility |
| Clean and marked builds broke paragraphs at different pages | Both build modes now issue equivalent colour commands | Exact page-by-page extracted text and character coordinates match; colour is the manuscript revision difference |
| Supplementary reference omitted one author | Main-paper citation in supplement now lists all four authors in manuscript order | Main and supplement title blocks agree |

## Completed verification

- Four PDF builds: marked/clean main **14 pages**; marked/clean supplement **14 pages**. No unresolved references, LaTeX warnings or overfull boxes. Every marked page and all three rendered Word documents inspected. Clean counterparts have identical text and character geometry. Figures use editable vector sources; the PDFs contain no raster images.
- **38 Python tests**: 29 existing revision-tool tests and nine evidence tests. **14 JavaScript payload cases**: two valid and twelve malformed inputs. No inference or network actuation performed by these checks.
- Five retained archive manifests verified; 180 LangGraph and 60 Qwen records joined to the canonical 180-cell oracle. Original records and hashes remain unchanged.
- Five formal cases independently rerun: original 320-state and zero-input 480-state models pass; three deliberate mutations trigger the expected safety invariant. This remains a finite abstraction, not implementation verification.
- All eight Reviewer 1 and three Reviewer 2 comments have a response tied to completed changes. R2.3 concerns safety versus semantics; the supervisor's former Table IV instruction is separate.

## Remaining evidence and author checks

1. **Recover and release the original proposed-workflow per-run reports/manifests before claiming full raw reproducibility.** A historical terminal record names `l4_oracle_20260716T131803Z_r10_successful_evidence.tar.gz` (approximately 5.2 MB) and records 180 final reports and 180 manifests. A related archive is `l4_oracle_20260716T131803Z_r10_portable_analysis_v2.tar.gz`. Those filenames are recovery clues, not evidence that either archive has been inspected in this revision. The present manuscript makes the narrower retained-summary verification claim explicitly.
2. Reconcile the recovered source with the authors' latest private Overleaf version and obtain final coauthor approval of text, author order, funding, references and disclosures. Verify author ORCIDs in the submission system. These confirmations are not represented as completed.
3. Independent expert validation, a matched inference-time ablation and production-derived telemetry/live A1/E2 integration remain absent. The revision uses the narrower-claim and qualified-comparison options offered in R2.1–R2.2. Acceptance of those options is the editor/reviewers' decision.
4. The separate callback V2 export is inactive. Authentication, exact action/evidence binding, expiry, replay/conflict handling, revocation and privileged approval require gateway implementation and deployment tests before operational use.
5. Publish the reviewed revision artifact at an accessible, versioned location and verify its link before uploading a response that claims public access to it. The older DOI release is not the new revision archive. GitHub integration returned HTTP 403 when branch creation was attempted; no remote revision branch or pull request was created. The delivered full repository ZIP, incremental Git bundle and binary patch preserve the local work.

## Journal and disclosure checks

The TNSM author page states an abstract range of 75–200 words and a 16-page maximum including figures, references and biographies. This main manuscript has 14 pages and an approximately 175-word abstract (word-count conventions differ slightly for hyphenated terms). The page limit check is not an acceptance decision. The cover-letter draft identifies the ICC Workshops predecessor and journal extensions, consistent with the journal's prior-publication instructions.

Primary policy sources checked on 15 October 2026:

- TNSM policies/guidelines: https://www.comsoc.org/publications/journals/ieee-tnsm/policies-guidelines
- IEEE submission/peer-review and AI-content disclosure policy: https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/
- Historical versioned artifact metadata: https://zenodo.org/api/records/21939774

The historical DOI record lists a repository-source ZIP. Inspection of that tag did not recover the original 180 proposed per-run packages. The new self-contained archive includes the tracked repository and retained revision inputs, but does not resolve that missing-data boundary.
