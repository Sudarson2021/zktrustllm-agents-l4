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

## (b) Oracle statistics

The 180 cells comprise six scenarios, three retrieval modes, and ten repeats per
scenario-mode combination. The repeated cells are not 60 independent scenarios;
this explains why many percentages are multiples of one sixth. A read-only
analysis now extracts the retained final decision and enforced action for every
cell, reports repeat stability for all 18 scenario-mode groups, and adds
20,000-replicate whole-scenario percentile-bootstrap intervals for decision
accuracy, enforced-action accuracy, and coverage. Only six clusters are
available, so interval coverage is explicitly described as limited and
descriptive. Run the script against the frozen R10 directory before inserting
the numerical intervals.

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
