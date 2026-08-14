# Supervisor status against critical items (a)--(d)

Date: 14 August 2026

## (a) Zero-knowledge decision

Decision: retitle unless a new generalized 240-row proof run is authorised and
completed. The read-only audit of the frozen matrix finds no per-row proof
outcome or proof/public-input binding. Full-L4 and No-IPFS have 40/40 missing
prover-time records each; the other four variants mark the prover as not
invoked. The retained constant verifier-gas field is not proof-validity
evidence. Current support is therefore 0/240 row-bound successful
verifications. The revision title is:

> Auditable Policy-Governed LLM-Agent Control for O-RAN Edge Security

The zero-knowledge index term and title claim will be removed. AUTH_V2.2 will be
reported only as a bounded component experiment, including `verifyTx=false`,
unless a new row-bound experiment supersedes it.

The completed audit archive is
`tnsm_zk_240_coverage_audit_20260814T181044Z.tar.gz` (SHA-256
`f806b0e22f85b90ac851dde9c279dd37e29e50c47da0a595829f989c00c09f48`).
Its source matrix has SHA-256
`95e2e6de5c55735de874e8817df70553b8cc1ea816d3d03eef78061695707f68`;
the audited circuit has SHA-256
`27814e144f577660002d7338dae993f8e0b84c3ffe9405782e7c1843e15e165a`.

## (b) Oracle statistics

The 180 cells comprise six scenarios, three retrieval modes, and ten repeats per
scenario-mode combination. The repeated cells are not 60 independent scenarios;
this explains why many percentages are multiples of one sixth. A read-only
analysis now extracts the retained final decision and enforced action for every
cell, reports repeat stability for all 18 scenario-mode groups, and adds
20,000-replicate whole-scenario percentile-bootstrap intervals for decision
accuracy, enforced-action accuracy, and coverage. Only six clusters are
available, so interval coverage is explicitly described as limited and
descriptive. The completed run found decision-repeat stability in 18/18
scenario-mode groups and action-repeat stability in 16/18; the two action
instabilities were Agentic RAG on S2 and S4.

Agentic RAG obtained 100.0% decision accuracy (descriptive clustered 95% CI
100.0--100.0%), 96.7% enforced-action accuracy (93.3--100.0%), and 83.3%
coverage (50.0--100.0%). RAG obtained 83.3% (50.0--100.0%), 83.3%
(50.0--100.0%), and 66.7% (33.3--100.0%), respectively. No RAG obtained
16.7% (0.0--50.0%), 66.7% (33.3--100.0%), and 0.0% (0.0--0.0%),
respectively. These intervals resample the six whole-scenario clusters with
20,000 replicates and seed 20260808; reliable finite-sample coverage is not
asserted.

The completed statistics archive is
`tnsm_oracle_clustered_statistics_20260814T181044Z.tar.gz` (SHA-256
`e173a9bbe9a9c3538964a58b05b88bd084f90d1f9f0b8bcb895d34a65fce903c`).

Scenario expansion is not claimed as completed. Any new scenarios will be a
separately versioned benchmark extension and will not modify the frozen R10
oracle.

## (c) External baseline

Completed. The SHA-bound LangGraph baseline used the same 180 frozen cells and
returned 180/180 HTTP-200 responses. In each retrieval mode, decision accuracy
was 83.3%, enforced-action accuracy 66.7%, joint accuracy 50.0%, NEVER recall
100.0%, with zero policy bypasses and zero unsafe executions. The total recorded
API cost was USD 0.856704. These results will replace the qualitative novelty
tick table.

## (d) Required manuscript corrections

- `L4` is removed rather than retroactively defined; variant labels become
  `Full system` and `No ZK` where retained.
- Stage E/F and Stage F/F move to the supplement with a two-sentence pointer.
- The n8n screenshot is replaced by the vector HUMAN-gate state transition.
- The Sepolia/IoTeX gas difference is reported descriptively. Identical bytecode
  and payloads do not establish identical chain execution rules, and retained
  receipts lack opcode traces/fork configuration needed for causal attribution.
- GPT-5.6 is the R10 assessor; GPT-5.5 is a separate Stage F/F planner alias.
  Stage F/F moves to the supplement, and the roles are stated explicitly.

## Human validation and authorship

No eligible independent annotators are currently available. Following the
supervisor's stated fallback, the human-label exercise is deferred and recorded
as planned future validation rather than a submission result. No participant
was recruited, no human labels were collected, and no ethics or kappa result is
claimed. The Stage 8 v2 packages are superseded and remain undistributed. The
v3 preregistration is retained only to protect the frozen-oracle rule in a
future study.

No author-list addition is proposed for annotation. Annotators will be
acknowledged. The current three authors must each explicitly approve the final
revised version before submission; record those confirmations outside the
public artifact.
