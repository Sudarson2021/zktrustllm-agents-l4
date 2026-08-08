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

## Later stages (run only after the preceding gate passes)

1. Export and validate the canonical frozen 180-row oracle.
2. Run the pinned LangGraph external baseline and retain raw responses.
3. Select a local open-weights model based on the recorded VRAM/RAM, freeze its
   model/revision/quantization hashes, and run one retrieval mode.
4. Generate and execute the deterministic 30-case prompt-injection suite.
5. Analyse all 233 attempt records to classify the 53 HTTP-500 failures using
   retained subcodes, trace identifiers, service logs, and retry outcomes.
6. Audit provider-returned model identifiers, access timestamps, decoding
   parameters, and full system prompts.
7. Generate the deterministic 30-cell human-label sheet; two independent
   O-RAN-literate annotators label it before oracle labels are revealed.
8. Compute agreement and Cohen's kappa, freeze all hashes, and pass the journal
   revision gate before editing result claims in LaTeX.

Exact commands for each later stage will be added only after the preceding
artifact is validated. This prevents running a plausible-looking experiment on
a reconstructed or differently encoded oracle.
