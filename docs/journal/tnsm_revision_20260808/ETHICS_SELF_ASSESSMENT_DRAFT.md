# University ethics self-assessment draft

Use this text as a factual starting point in the University of Surrey Ethics RM
application. Answer the portal's questions accurately and preserve the issued
reference/letter. Do not recruit or distribute annotation packages until the
portal states that no review is required or a favourable ethical opinion has
been issued.

Official route: <https://my.surrey.ac.uk/research/ethics>

## Project title

Independent professional validation of a frozen synthetic O-RAN security-policy
oracle

## Purpose

Two colleagues familiar with O-RAN will independently classify 30 synthetic
technical cases. The aim is to measure whether the frozen benchmark task is
well-defined and whether its pre-existing labels agree with independent
professional judgement. The frozen oracle will not be changed in response to
their labels. Disagreements will be reported, not adjudicated.

## Participants and recruitment

Two adult colleagues acting in a professional technical capacity will be
invited individually after supervisor approval. Neither will be a manuscript
co-author or a contributor to the oracle, prompts, or scenario design.
Participation is voluntary. No employment, academic, or supervisory consequence
will follow from accepting, declining, or withdrawing.

## Task and time commitment

Each participant receives a separately ordered blinded package containing 30
synthetic O-RAN policy cases and fixed label definitions. They return a completed
CSV and a coded declaration. No interview, observation, personal-opinion
question, deception, special-category-data collection, or production-network
activity is involved.

## Data minimisation

The research dataset stores only a pseudonymous code (`annotator_1` or
`annotator_2`), a single yes/no confirmation of O-RAN familiarity, independence
and non-contribution confirmations, technical labels, confidence scores, and
optional case-related notes. It does not collect names, email addresses, years
of experience, employer details, demographic characteristics, health data, or
opinions about individuals. Contact details used for invitation remain in
ordinary University correspondence and are not copied into the research
dataset or public artifact.

## Risks and mitigations

The activity is minimal risk and concerns only synthetic technical artefacts.
Case orders differ, oracle labels and peer labels are hidden, and participants
are asked not to discuss cases until both submissions are frozen. The policy
data contain no subscriber or operational network data. Invalid or incomplete
submissions are excluded rather than imputed.

## Consent and withdrawal

Provide a short participant information statement explaining purpose,
voluntariness, task, data fields, intended publication, and coordinator contact.
Record informed consent before annotation. A participant may withdraw before
the coordinator freezes and aggregates both returned sheets. After anonymous
aggregation, individual withdrawal may no longer be technically possible; state
the exact cutoff in the participant information.

## Storage, access, and dissemination

Completed files are stored on University-approved access-controlled storage.
Only the study team accesses individual coded sheets. The article reports
aggregate agreement, clustered intervals, and disagreements by case code. If
the artifact is deposited publicly, include only the minimum coded technical
labels and exclude correspondence or direct identifiers. Follow the retention
period approved in Ethics RM and the project's data-management plan.

## Analysis fixed before data collection

The oracle key and analyzer are SHA-256 bound before labels are received.
Unweighted Cohen's kappa is used for the binary clearance decision;
linear-weighted Cohen's kappa is used for the ordinal action scale. Oracle versus
each annotator and annotator versus annotator are reported with whole-scenario
cluster-bootstrap intervals. All disagreements are reported. The oracle is not
revised.
