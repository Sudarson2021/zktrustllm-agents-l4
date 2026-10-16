# Matched inference study: independent audit — 16 October 2026

The completed study supports a new, bounded comparison of configured inference blocks. It does **not** authenticate provider-side execution independently, validate the author oracle, demonstrate live O-RAN safety, or explain the historical LangGraph latency ratio. No further provider calls were made during this audit.

## Evidence verified

- Uploaded archive: `TNSM_12002_Matched_Ablation_Evidence_20261016T194059Z.tar.gz`.
- SHA-256: `7ea6792f45aa6663e98869e81626f69bb37c58c1c4de161691545c70780bdd95`.
- Full protocol SHA-256: `5e501822578b8c87537110d8e5d6ce22fc1d904a6f631721cc82d1b628cbba6e`.
- All internal manifest entries verify: pilot 01: 127; pilot 02: 128; full: 3,723.
- All 1,080 decoded raw-response hashes verify. The complete frozen analyzer reproduces the packaged analysis JSON exactly.
- A separately implemented, offline audit independently recomputes scores, timer partitions, R7 quantiles, pairing, 20,000 whole-scenario bootstrap draws, metadata completeness and failures. It does not import the frozen runner.
- The journal retains 240 starts and 240 completions, without replacement or interrupted trials, from 15:57:42 to 19:19:44 UTC on 16 October 2026.

Checksums establish internal byte correspondence and detect changes relative to retained commitments. Neither a checksum nor an API-returned response/model ID is a signed provider attestation or independent proof that historical execution occurred exactly as recorded. Evidence provenance is therefore reported with this explicit limit.

## Design and results

Six synthetic scenarios × ten repeats × four conditions = 240 trials. Each block shares its frozen input and retrieval. A/B have one/four assessors and no roles; C/D add the same four-role chain. Every condition makes fresh calls. Corresponding assessor request bodies match within blocks. Assessor count and provider diversity change together, and the role factor changes the entire chain.

| Condition | Calls/trial | Decision agreement | Pre-review action | Final action | NEVER recall | Median / P95 seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 1 | 52/60 | 55/60 | 59/60 | 19/20 | 4.266 / 8.069 |
| B | 4 | 54/60 | 51/60 | 58/60 | 18/20 | 24.514 / 50.916 |
| C | 5 | 52/60 | 55/60 | 59/60 | 19/20 | 67.514 / 93.998 |
| D | 8 | 59/60 | 48/60 | 58/60 | 18/20 | 93.144 / 130.990 |

Final action is after a common review-only guard. It preserves NEVER and otherwise imposes HUMAN, with execution false. High final action agreement and zero executions must not be reported as independent semantic understanding or measured deployment safety.

Primary contrasts retain 59 blocks with all planned responses HTTP 200. Block 7 is excluded for a Mistral read timeout. Refusals and invalid outputs remain in that prespecified population. All 60 trials remain in marginal timing and outcome descriptions. HTTP completion is not successful inference.

| Contrast | Mean paired seconds | Descriptive 95% six-cluster interval |
| --- | ---: | ---: |
| B−A | 23.622 | [18.410, 28.738] |
| D−C | 27.017 | [24.754, 29.491] |
| C−A | 63.052 | [58.923, 67.030] |
| D−B | 66.446 | [60.427, 72.888] |
| Interaction | 3.395 | [-0.632, 7.558] |

The intervals use only six designed scenario clusters. They do not establish reliable nominal coverage, significance or general O-RAN performance. The interaction interval does not prove that interaction is absent. Medians are all-trial descriptions; these contrasts are paired means on a different population.

The result is mixed: D improves decision agreement to 59/60, but NEVER recall drops from A's 19/20 to 18/20, and pre-review action agreement from 55/60 to 48/60. C does not improve decision agreement over A. No uniform semantic gain is claimed.

## Preserved failures and parser limitation

There are 1,079 HTTP-200 nodes and 1,035 schema/reference-valid nodes among 1,080 calls. The 45 invalid nodes comprise 33 Anthropic refusals, five JSON/schema failures, six reference-check failures and one read timeout. Reference checks establish citation-identifier consistency and selected action-language rules, not entailment or oracle truth.

Nine DeepSeek assessor responses terminate with `length`. Six empty-final-text responses invoke the frozen source's `reasoning_content` fallback. Four of those objects pass its parser/reference checks and participate in the prespecified results: 001_B, 004_D, 014_D and 016_B. Two fallback objects fail. Three other truncated partial-final-text objects fail. No private reasoning content is reproduced in the report, and no output was repaired or replaced. This is a source-parser limitation requiring disclosure, not a clean-completion result.

Three final candidates fail (007_D, 020_A, 058_B), all S4; their UNCERTAIN/HUMAN fallbacks remain in counts. D's other NEVER miss, 020_D, has the correct NON_COMPLIANT decision but lacks a supporting policy-clause identifier and reconciles to HUMAN. Non-execution does not erase that class error.

Post hoc subsets of all-final-valid (57 blocks), all-node-valid (36) and strict completion without truncation/fallback (32) have similar positive latency increments. They are selected after observing outcomes and are descriptive sensitivities only, not replacements for the primary analysis or proofs of unbiased effects. Exact values and every anomaly identifier are in `evidence/derived/matched_inference_audit.json`.

## Scope, reproducibility and remaining gaps

The timed interval includes prompt construction, assessment, aggregation, roles/adapter, common governance and intermediate persistence. It excludes retrieval generation, startup, final index/manifest persistence, human waiting and anchoring. It does not run n8n or LangGraph, live OPA, proofs, human review, a blockchain or an O-RAN executor. It does not measure their overhead.

The protocol predates the full run and records the pilot-informed 8,192-token role cap. Both pilots and failures remain intact and separate. Provider aliases and omitted defaults are documented, not treated as immutable snapshots. OpenAI/Anthropic/Mistral fingerprint fields are missing. Token metadata is reported without double-counting reasoning or cached subsets; Mistral has one missing usage record. No invoice-based dollar cost is claimed.

Run `python3 scripts/l4/tnsm_revision/audit_matched_inference_evidence.py` and `python3 scripts/l4/tnsm_revision/build_matched_inference_tables.py` from the repository root. `MATCHED_STUDY_REPRODUCIBILITY.md` gives frozen-analyzer extraction and reproduction steps.

Independent expert labels, production-derived/noisy telemetry, real rApp/A1/E2 integration and deployed approval-service verification remain absent. The historical 109.793/1.843 ratio stays qualified. The new results support a major-revision response; editorial acceptance and final coauthor approval are not certified by this audit.

The primary paired means condition on all-node HTTP completion. This selection is prespecified but can still bias contrasts relative to all attempted blocks; only the conditional complete-case estimand is claimed. The protocol flag `synthetic=false` denotes actual API returns rather than mock records, while all scenario inputs remain synthetic.
