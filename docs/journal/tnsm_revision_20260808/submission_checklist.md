# TNSM submission gate

Do not submit until every unchecked item is completed.

- [ ] Add the current journal `main.tex`, figures, bibliography, and supplement
  source to the revision branch.
- [ ] Integrate and adapt `main_text_dropins.tex`; search for stale `L4`,
  `Reviewer-Verifiable`, and mixed-orientation estimands.
- [x] Run LangGraph on the identical frozen oracle and retain raw prompts,
  responses, hashes, timing, environment lock, and scoring output.
- [x] Run one local open-weights model with the identical retrieval mode,
  scenarios, and scorer.
- [x] Run and score all 30 prompt-injection cases; verify zero executed NEVER
  actions before reporting resistance.
- [x] Defer independent human validation because no eligible annotators are
  available; preserve the preregistration for a future study and report no
  labels, kappa, or ethics-reference result in this submission.
- [x] Report captured model aliases, access dates, submitted decoding fields,
  token limits, system prompts, and prompt hashes, while stating that immutable
  snapshots and unspecified server defaults were not exposed.
- [x] Collect structured HTTP failure logs or state that the 53 failures remain
  unresolved; never attribute a cause without trace evidence.
- [x] Complete the frozen 240-row ZK evidence audit and retitle after finding
  0/240 retained row-bound successful verifications.
- [x] Compute 20,000-replicate whole-scenario intervals and report 18/18
  decision-stable and 16/18 action-stable scenario-mode groups with the
  six-cluster limitation.
- [ ] Replace Fig. 2/3 and six small plots with the supplied vector/composite
  figures; move full workflow screenshots to the supplement.
- [ ] Remove the asymptotic complexity section/Table III and qualitative novelty
  Table XII; move Stage E/F and F/F tables to the supplement.
- [ ] Rebuild and visually inspect every manuscript and supplement page at
  single-column print scale.
- [ ] Confirm the final main-text page count is at or below the applicable
  TNSM limit and that biographies are handled according to the current template
  and submission instructions.
- [ ] Obtain author-approved headshots and verify biography facts.
- [ ] Compute the journal-over-conference percentage and complete the six-gap
  cover-letter list.
- [ ] Create a tagged GitHub release, deposit it on Zenodo, insert the DOI into
  the paper, `CITATION.cff`, `.zenodo.json`, README, and cover letter, then
  verify the archived checksums.
- [ ] Confirm that the manuscript states no human-label exercise was conducted,
  no human-participant data were collected, and expert validation is future
  work. Do not include kappa, annotator, consent, or ethics-reference claims.
- [ ] Upload the ICC Workshops paper as supplementary material.
- [ ] Ask Mohammad Shojafar for the requested final check only after this gate is
  fully green.
