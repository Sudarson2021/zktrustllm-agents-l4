# Matched inference-time ablation: terminal workflow

This is a new experiment, not recovered measurements. Read PROTOCOL.md first.
Use the separate worktree already created at
`~/Downloads/TNSM_12002_matched_ablation_20261016`. Existing services stay up.

Run one stage at a time and inspect its output before proceeding. Never paste
API keys, full Docker environments, .env files or authenticated headers into
chat. The launcher obtains only the required provider fields privately.

1. Install the checksum-verified package into that worktree without overwriting
   existing files. Save it and its recorded checksum with the study materials.

```bash
python3 "$HOME/Downloads/TNSM_12002_Matched_Ablation_Tools.zip" \
  --repo "$HOME/Downloads/TNSM_12002_matched_ablation_20261016"
```

2. Run the preflight below. It creates an isolated temporary container and
   checks source/input binding, parsing dependencies, configured models and
   image identity. It makes no provider call and does not prove availability.

```bash
cd "$HOME/Downloads/TNSM_12002_matched_ablation_20261016"
python3 scripts/l4/tnsm_revision/matched_ablation/launch.py preflight
```

Stop here and review the output. All providers should be configured. A missing
dependency, image permission or model configuration is a setup issue; preserve
the output, fix it deliberately, and repeat preflight. Do not guess replacements
for the historical model names or change old evidence.

The following commands are reference stages, **not one combined script**.
Freezing costs no provider usage; run --live makes billable hosted API calls.
Pilot defaults: 36 calls, sum of output request caps 172,000 tokens, plus input.

3. Freeze a pilot only after reviewing caps and model aliases:

```bash
python3 scripts/l4/tnsm_revision/matched_ablation/launch.py freeze \
  --name pilot_01 --phase pilot
```

4. After explicit budget review, run the frozen pilot:

```bash
python3 scripts/l4/tnsm_revision/matched_ablation/launch.py run \
  --name pilot_01 --live
```

5. Verify and analyze it:

```bash
python3 scripts/l4/tnsm_revision/matched_ablation/launch.py analyze \
  --name pilot_01
```

Default outputs are under
`artifacts/out/tnsm_matched_ablation_20261016/pilot_01` and `pilot_01_analysis`.
Read analysis.json, variants.csv, the frozen protocol and raw usage. Pilot
eligibility is always false. Check JSON/schema/grounding failures, actual
provider identifiers and any truncation before choosing full-run settings.

6. If a pilot fails, preserve its entire directory. Do not edit its protocol
   or erase attempts. Use pilot_02 for a deliberately revised protocol and
   document changes. Fixes must precede a new full freeze.
7. Only after the pilot audit and cost review, freeze full_01 --phase full.
   The full defaults imply 240 trials/1,080 calls and a sum of requested
   output caps of 5,160,000 tokens, plus input. It is a separate data collection.
   Use the same launch.py freeze/run/analyze subcommands with --name full_01;
   pass --phase full only to freeze and --live only to run. No full command
   is executed by installing or preflighting this package.
8. Preserve and audit full evidence, then revise all three paper documents.
   Do not claim completion based only on tooling, a pilot or synthetic tests.

Optional offline verification uses local Python with Pydantic 2; it does not
need provider keys:

```bash
python3 -m unittest discover \
  -s test/l4/tnsm_revision/matched_ablation -p 'test_*.py' -v
```

The launcher uses the existing image to avoid installing packages on the host.
Its Docker behavior is unit-tested with subprocess mocks; the real Linux/Docker
launch and provider compatibility must be confirmed on the user's machine.
Neither is established by a synthetic test.
