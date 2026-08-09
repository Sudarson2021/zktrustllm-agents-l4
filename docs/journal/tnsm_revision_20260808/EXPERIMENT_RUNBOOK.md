# IEEE TNSM experiment runbook

This runbook executes the supervisor-requested additions without changing the
frozen R10 benchmark. Each stage has a stop condition. Do not skip a failed
gate and do not copy values manually into an output artifact.

## Stage 1 — frozen-data and compute preflight

The paper's R10 benchmark is recorded as 6 scenarios × 3 retrieval modes × 10
repeats = 180 successful cells, with 233 total attempts and 53 retained HTTP
500 failures. Repository evidence points to this external experiment directory:

```text
$HOME/Downloads/deploy/n8n_l4_parallel/runtime/experiments/l4_oracle_20260716T131803Z_r10
```

From the GitHub repository checkout, run:

```bash
cd "$HOME/zktrustllm-agents-l4"
git status --short --branch
bash scripts/l4/tnsm_revision/run_preflight.sh
```

The script is read-only. It hashes candidate frozen files, reports structural
keys/row counts, records CPU/RAM/GPU/tool versions, and records only whether API
environment variables exist. It never prints key values and never calls a
provider.

If either location differs on the current host, override it explicitly:

```bash
cd "$HOME/zktrustllm-agents-l4"
EXPERIMENT_DIR="/absolute/path/to/runtime/experiments/l4_oracle_20260716T131803Z_r10" \
N8N_ROOT="/absolute/path/to/n8n_l4_parallel" \
bash scripts/l4/tnsm_revision/run_preflight.sh
```

Stop after Stage 1 and retain the generated `preflight.json`, `preflight.md`,
and `SHA256SUMS.txt`. A canonical 180-row JSONL must be exported from the
identified frozen records before any live baseline is run. The export must be
machine-generated and contain these fields:

```text
cell_id, scenario_id, retrieval_mode, repeat, scenario (or prompt),
oracle_decision, oracle_action_class
```

Allowed oracle decisions are `COMPLIANT`, `NON_COMPLIANT`, and `UNCERTAIN`;
allowed action classes are `AUTOMATIC`, `HUMAN`, `PRIVILEGED`, and `NEVER`.
The canonical matrix must contain 60 rows per retrieval mode, 30 per scenario,
and 18 per repeat number (1–10).

### Stage 1 pass condition

`preflight.md` must show the experiment directory, frozen summary, and all six
scenario sources as `PASS`. The canonical-oracle gate is expected to remain
`BLOCKED` on the first run; the inventory will determine the exact, auditable
export command for Stage 2.

## Stage 2 — canonical frozen-oracle export

After the Stage 1 inventory matches the pinned R10 hashes, run:

```bash
cd "$HOME/zktrustllm-agents-l4"
bash scripts/l4/tnsm_revision/run_oracle_export.sh
```

The exporter verifies the 180-row success-index hash, the authoritative oracle
manifest hash, and all six scenario hashes. It joins each cell to its retained
response/report and includes only scenario configuration and mode-specific
frozen retrieval inputs in the baseline prompt. Oracle labels, model outputs,
reconciliation results, and policy outcomes are excluded from the prompt.

The command then validates the 6 × 3 × 10 matrix, creates a SHA-256 manifest,
and packages the result in `~/Downloads`. It makes no provider call and does not
modify the frozen R10 directory.

### Stage 2 pass condition

The final preflight must report `Canonical 180-row oracle: PASS` and `Ready for
live experiment: YES`. Retain and upload the generated Stage 2 archive before
running a model.

## Stage 3 — external LangGraph baseline pilot

Run the guarded three-cell pilot only after the Stage 2 archive passes every
hash check. The pilot selects one frozen cell from each retrieval mode and
covers COMPLIANT/HUMAN, NON_COMPLIANT/HUMAN, and NON_COMPLIANT/NEVER oracle
targets. It makes three paid provider requests, excluding automatic retries.

```bash
cd "$HOME/zktrustllm-agents-l4"
MODE=pilot bash scripts/l4/tnsm_revision/run_langgraph_external_baseline.sh
```

The wrapper pins LangGraph, the canonical input hash, model and decoding
parameters, strict output schema, prompt, pricing snapshot, and selected cell
IDs. It stores append-only attempt and record JSONL files plus raw requests,
raw responses, response headers, request IDs, returned model identifiers,
system fingerprints, token usage, latency, file hashes, summary JSON/CSV, and a
package freeze. API-key values are neither printed nor written. A failed run is
resumable by repeating the same command.

The default model is `gpt-5.6-terra`, matching the OpenAI assessor family in
the frozen experiment. Provider documentation does not expose a dated snapshot
for this alias, so the artifact retains the returned model identifier and
system fingerprint and states that limitation.

### Stage 3 pilot pass condition

Upload the generated `tnsm_stage3_langgraph_pilot_*.tar.gz` before attempting
the full matrix. The pilot must have three completed records, three HTTP
successes, schema coverage for all three cells, no unsafe execution, matching
configuration/input hashes, and no unexpected model-ID substitution. Do not
interpret accuracy from three cells.

The full run is deliberately locked. After the pilot has been independently
checked, it can be enabled with both `MODE=full` and
`CONFIRM_FULL_180=YES`; neither flag should be used before that check.

## Later stages (run only after the preceding gate passes)

1. Run the approved full 180-cell LangGraph baseline and retain raw responses.
2. Select a local open-weights model based on the recorded VRAM/RAM, freeze its
   model/revision/quantization hashes, and run one retrieval mode.
3. Generate and execute the deterministic 30-case prompt-injection suite.
4. Analyse all 233 attempt records to classify the 53 HTTP-500 failures using
   retained subcodes, trace identifiers, service logs, and retry outcomes.
5. Audit provider-returned model identifiers, access timestamps, decoding
   parameters, and full system prompts.
6. Generate the deterministic 30-cell human-label sheet; two independent
   O-RAN-literate annotators label it before oracle labels are revealed.
7. Compute agreement and Cohen's kappa, freeze all hashes, and pass the journal
   revision gate before editing result claims in LaTeX.

Exact commands for each later stage will be added only after the preceding
artifact is validated. This prevents running a plausible-looking experiment on
a reconstructed or differently encoded oracle.
