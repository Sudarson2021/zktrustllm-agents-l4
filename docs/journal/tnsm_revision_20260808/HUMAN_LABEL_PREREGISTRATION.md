# Human-label agreement preregistration

This document fixes the analysis before either completed label sheet is
received. The machine-readable, run-specific registration is generated as
`coordinator_DO_NOT_SHARE/analysis_preregistration.json` and binds the exact
oracle-key CSV and analyzer script by SHA-256.

## Eligibility and governance

- Lodge the University ethics self-assessment before recruitment or data
  collection and retain its reference.
- Obtain written supervisor approval of both named annotators before invitation.
- Each annotator must answer yes to O-RAN familiarity and independent completion,
  and no to access to oracle/peer labels and contribution to the oracle, prompts,
  or scenario design.
- No name, email address, years of experience, or opinion about an individual is
  stored in the research artifact.
- Annotators are acknowledged, not made authors solely for annotation.

## Frozen estimands

The decision estimand is binary. Annotators label `CLEAR` or `NOT_CLEAR`.
The frozen three-class oracle is mapped before analysis as follows:

- `COMPLIANT` to `CLEAR`;
- `NON_COMPLIANT` to `NOT_CLEAR`;
- `UNCERTAIN` to `NOT_CLEAR`.

This fail-closed mapping is not an oracle revision. Decision agreement uses
unweighted Cohen's kappa.

Action agreement uses linear-weighted Cohen's kappa on the preregistered ordinal
scale `AUTOMATIC < HUMAN < PRIVILEGED < NEVER`.

For both estimands, report exactly these comparisons:

1. frozen oracle versus annotator 1;
2. frozen oracle versus annotator 2;
3. annotator 1 versus annotator 2.

Each point estimate receives a 95% percentile interval from 20,000 bootstrap
resamples of whole `scenario_id` clusters using seed `20260808`. Undefined
bootstrap replicates are excluded and counted. Because there are only six
scenario clusters, these intervals are descriptive and reliable finite-sample
coverage is not asserted.

## Disagreement and invalid-input rules

Every pairwise disagreement and confusion matrix is reported. There is no
adjudication, correction, relabelling, or oracle revision after labels are seen.
Missing labels, labels outside the registered categories, edited evidence, or
incomplete declarations fail validation and are not imputed.

The old Stage 8A v2 packages predate this protocol and must not be distributed.
