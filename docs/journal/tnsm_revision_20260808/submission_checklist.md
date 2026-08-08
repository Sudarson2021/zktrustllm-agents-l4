# TNSM submission gate

Do not submit until every unchecked item is completed.

- [ ] Add the current journal `main.tex`, figures, bibliography, and supplement
  source to the revision branch.
- [ ] Integrate and adapt `main_text_dropins.tex`; search for stale `L4`,
  `Reviewer-Verifiable`, and mixed-orientation estimands.
- [ ] Run LangGraph on the identical frozen oracle and retain raw prompts,
  responses, hashes, timing, environment lock, and scoring output.
- [ ] Run one local open-weights model with the identical retrieval mode,
  scenarios, and scorer.
- [ ] Run and score all 30 prompt-injection cases; verify zero executed NEVER
  actions before reporting resistance.
- [ ] Obtain independent, blinded labels for the deterministic 30-cell subset;
  report pairwise kappa and the sampling rule.
- [ ] Capture exact provider-returned model IDs, access dates, decoding
  parameters, token limits, system prompts, and prompt hashes.
- [ ] Collect structured HTTP failure logs or state that the 53 failures remain
  unresolved; never attribute a cause without trace evidence.
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
- [ ] Confirm the institutional ethics determination for the independent-label
  exercise and update the availability/ethics statement.
- [ ] Upload the ICC Workshops paper as supplementary material.
- [ ] Ask Mohammad Shojafar for the requested final check only after this gate is
  fully green.
