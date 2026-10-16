# TNSM-2026-12002: new matched inference-block study

Prepared 16 October 2026. **Protocol and tooling, not completed experiments.**
Pilot, synthetic and interrupted runs must not be reported as the completed
full study. No measured effect size is supplied with this protocol.

## Question and scope

Under a common runner, how do the configured assessor set and a four-role
inference chain change decision-ready wall time on frozen Agentic-RAG inputs?
This is a new 2-by-2 component-block experiment. It does not identify the cause
of the historical approximately 109.8 s versus 1.5–1.8 s difference, measure
n8n versus LangGraph orchestration overhead, or reproduce full deployment
latency. Historical comparisons must retain their qualified interpretation.

| Condition | Assessment stage | Role stage | Calls per trial |
| --- | --- | --- | ---: |
| A_ONE_NO_ROLES | OpenAI only | None; deterministic adapter | 1 |
| B_FOUR_NO_ROLES | OpenAI, Anthropic, DeepSeek and Mistral, parallel | None; deterministic adapter | 4 |
| C_ONE_ROLES | OpenAI only | Planner, critic, recovery, arbiter, sequential | 5 |
| D_FOUR_ROLES | The same four parallel assessors | The same four sequential roles | 8 |

The role providers are OpenAI, Anthropic, DeepSeek and Mistral, respectively.
The assessor factor jointly changes provider diversity and number of calls;
it is not an estimate of model count independent of provider identity. The
role factor removes/adds the whole chain, not an individual role. D is the
richest inference condition in this experiment, **not the complete proposed
system**. No individual-role causal claim follows from this design.

## Frozen evidence and source binding

The input snapshot is the canonical 180-cell reference retained in the
revision artifact. Only its 60 Agentic-RAG cells enter this study: six
author-designed scenarios, ten repeats per scenario. The same cell, including
its frozen retrieval evidence, is used by all four conditions in a block.

* Input SHA-256:
  `4854f1d42d7824ae48ae3b37d8402d468c9f11034aa26b0fd9e96a21e1196c6c`
* Gateway reference SHA-256:
  `952fbbf87d1fc59a9e600718c9cf5ff6d2bc5c3eb24a3673a5203322921ed65e`
* Uploaded provenance archive SHA-256:
  `724b943a5eea534f5cc85fc18a3f4e5994f52700c4563dd9fad552ceebe182cc`

The gateway reference is the unredacted source recovered by the supplied
allowlisted probe; its file hash matches the user's gateway source hash.
The input snapshot originates in
`paper/tnsm_revision_20261015/evidence/inputs/tnsm_stage2_oracle_export_20260808T190951Z.tar.gz`.
Checksums establish correspondence and detect subsequent changes. They do
not independently certify historical execution time or scientific validity.

The runner extracts only explicitly named pure prompt, schema, parsing,
validation and reconciliation definitions by AST after checking the entire
source hash. It never imports or starts the gateway application. It never
calls its policy, proof, anchoring, human-review or execution routes. It does
not mount the original gateway data or alter existing n8n workflows.

The model-facing input contains the original configuration and normative
retrieval evidence. Oracle decisions/action labels and revealing scenario
titles are excluded. Scenario IDs inside the original configuration remain.
No oracle label is consulted to generate synthetic test responses or live
responses. Scoring against the reference occurs only during analysis.

Retrieval generation is excluded. This design tests conditional reasoning
on a fixed bundle; it neither measures retrieval quality nor adds telemetry
realism. Repeated cells do not constitute 60 independently sampled scenarios.

## Matching and declared adaptations

Every condition makes fresh inference requests. Shared assessor request
bodies are identical within a block, including model alias, evidence,
prompts and output cap. Outputs are not replayed or shared. Role prompts
retain the pinned source template but their aggregate/prior-role context
naturally depends on the condition and fresh outputs.

The original aggregator assumes four providers. Simply disabling three
would make its completeness check fail. Here a prespecified common rule uses
the configured provider count N: at least ceil(0.75 N) valid grounded
assessments and at least 0.75 agreement among valid assessments. Otherwise
the decision is UNCERTAIN. A deterministic union of cited violations is
retained only when consensus is NON_COMPLIANT. This is an explicit new
comparator adaptation, not an unchanged run of the original aggregator.

The role-free adapter turns that aggregate into the pinned Assessment
schema. The role chain always attempts all four calls, including after an
invalid intermediate output; this differs from historical routes that can
abort early. A structurally valid final candidate is reported separately
from its decision: a valid UNCERTAIN outcome is still possible. This is not
semantic correctness or equivalence of all historical validation checks.

All conditions use the same pinned action-class reconciliation followed by
a review-only guard. The guard preserves NEVER and maps other action classes
to HUMAN; execute is always false. This does not execute live OPA, proofs,
blockchain anchoring or human approval. Zero executions are imposed by this
design and are not a measured deployment-safety achievement.

OpenAI requests add store=false. DeepSeek requests add an explicit max_tokens
cap, supported by its official chat-completion API documentation:
<https://api-docs.deepseek.com/api/create-chat-completion/>.
These are declared differences from historical payloads. Sampling, seed,
reasoning, service-tier and cache-control fields are not sent. Provider
defaults are not inferred. Usage and response metadata are retained when
returned; missing fields remain missing.

## Model and environment identity

The launcher reads only the four model aliases and four corresponding API
keys from the running gateway container, privately. Keys travel through a
stdin pipe into a separate container using the same image ID. They are not
printed, placed in Docker command arguments or written to a configuration
file. The new container has read-only code and a new writable results
directory. No original gateway state/data directory is mounted.

Preflight and freeze make no provider call. A configured alias is not proof
of provider availability, entitlement or an immutable model snapshot. The
live pilot tests availability. Record requested aliases, returned model IDs,
fingerprints, response IDs, dates and raw usage where available. Returned
aliases/fingerprints do not authenticate hidden weights. Inspect the analysis
identity observations for missing fields and drift before writing claims.

The frozen protocol binds source/input hashes, all four harness code hashes,
Python/Pydantic versions, platform, image ID, model aliases, call matrix,
caps, timeout, matching rules and analysis plan. A later mismatch blocks a
run; do not patch a frozen protocol to bypass that check.

## Pilot, full sample, order and cost

Pilot: S2 and S4, repeat 1, all four conditions; eight trials and 36 calls.
The pilot checks API/schema compatibility and practical usage. It is not a
latency result for the full population and must not be pooled into the full
study. If pilot findings require a code or cap change, document the reason
and freeze a new full protocol before collecting full data.

Full: all 60 cells, four conditions each; 240 trials, 1,080 calls (600
assessor and 480 role calls). Blocks are shuffled with seed 20261016. Four
Williams sequences balance condition position and first-order carryover
within blocks; each condition occupies each position 15 times. Balance
does not remove arbitrary temporal load, provider routing or cache effects.
There is a one-second pause between trials outside the measured interval.

Default requested caps are 5,000 output tokens per assessor and 4,500 per
role. The sums of requested maxima are 172,000 tokens for the pilot and
5,160,000 for the full study. These are **not expected usage, total billing
limits or dollar estimates**; input tokens and provider-specific billing also
apply. Caps can be lowered before freezing, using identical caps across all
conditions. Inspect real pilot usage and current account pricing before
authorizing the full run. Do not use made-up zero-cost or historical pricing.

No inference is triggered without the explicit run --live command. One
attempt is made per call; no automatic provider retries are performed.
Requests have a 180-second timeout. HTTP 400/401/403/404/422 stop the study
after retaining evidence. Other failures remain in the output; subsequent
planned trials continue. Resolve configuration/schema failures in a new
named pilot, preserving the failed attempt. Do not silently replace failures
or select a convenient successful subset. Automatic resumption is disabled.

## Timers and records

The primary interval starts immediately before assessment-prompt construction
and ends after common reconciliation/review-only gating. Its disjoint phases
are assessment, aggregation, role-chain-or-adapter and governance. Assessment
wall time covers parallel calls once, not the sum of their durations. Node
request times are retained separately. The phase sum must equal the total.

The interval includes request/result node-file persistence and aggregation
persistence. It excludes frozen-retrieval preparation, final trial/index/
manifest persistence, startup, operator waiting and external anchoring. This
boundary must appear in any results caption; do not relabel it full
end-to-end O-RAN response time.

Each node retains its unauthenticated request body, decoded response body,
status, allowlisted response headers, request timer, parsed schema, grounding
validation, requested/returned model metadata and raw usage. Response hashes
refer to decoded UTF-8 text (replacement decoding for invalid UTF-8), not an
independent capture of network bytes. Exact provider-key matches are
redacted; response redaction makes a run ineligible for the full-study gate.
No provider authorization header is retained. Do not publish private
provider error information without inspecting it.

The run journal records started/completed/interrupted trials. SHA256SUMS.txt
binds all retained files. The analyzer checks manifests, frozen contracts,
requests, parsed outputs, metadata, aggregate/reconciliation results and
disjoint timers. Preserve a partial run even if it cannot support estimates.

## Prespecified analysis

Report all planned/completed/missing trials, all HTTP outcomes, structural
validity, response redactions and model/usage metadata completeness. Variant
median and R7 P95 wall times use all completed trials, including failure
paths. Report HTTP-complete counts beside them; failures can appear fast.
Marginal phase medians must not be added as though they were a single trial.

Primary paired effects use blocks with all four conditions completed and all
planned HTTP responses 200; output validity is reported separately. Report
exclusions rather than silently dropping them. Estimate mean paired
differences B-A, D-C, C-A and D-B, and interaction (D-B)-(C-A). An all-completed
trial median is descriptive, not the same population as these contrasts.
Do not call an HTTP-200 completion a semantically successful response.

Descriptive 95% percentile intervals use 20,000 whole-scenario bootstrap
resamples, seed 20261016, retaining all paired repeats within selected
scenarios. Intervals are produced only with all six scenario clusters
represented. Six designed scenarios are insufficient for a reliable claim
of nominal coverage or general O-RAN generalization. No significance claim
or p-value is prespecified.

Decision agreement and both pre-review reconciled and final enforced
action-class agreement are scored relative to the author reference. Include
NEVER hits/denominator, false NEVER counts and valid-final-candidate counts.
Fail-closed fallback participates in these all-completed-trial counts and
must not be described as semantic understanding. The common review-only
guard makes zero execution inevitable. Independent expert validation and
live O-RAN integration remain unavailable and must remain limitations.

The machine field publication_eligible_for_bounded_full_study is only a
minimum completeness/provenance gate. It does not grant scientific validity,
independent expert validation, final coauthor approval or journal acceptance.
Inspect all outputs and identity drift before drafting conclusions. Report
non-improvement and failures as faithfully as positive effects.

## Reviewer response after actual completion

Use future tense until the full evidence has been audited. Then report the
actual date, aliases/returned identifiers, sample/call counts, exclusions,
caps, timing boundary, estimates and descriptive intervals. Explain that the
new common-harness experiment isolates two component blocks within its
defined population. Keep the historical LangGraph comparison qualified and
do not assert that this new experiment explains its old latency ratio.
Update the manuscript, supplement, tables/figures and point-by-point response
together, marking manuscript changes blue. Preserve expert/live-O-RAN
limitations, and publish a fresh artifact version rather than rewriting an
already published release or DOI record's files.
