# Original 180-run evidence verification — TNSM-2026-12002

Verified on 15 October 2026. The uploaded recovery bundle is byte-identical to the SHA-256 recorded on the author's computer:

`f842c0308d6e52904de71bb8886a044d733d474dde688ac906fbab0277ccb63d`

Bundle: `TNSM_12002_Original_Evidence_Recovery.tar.gz` (5,574,012 bytes). Its original successful-evidence archive contains 3,420 regular files, including 180 manifests and 180 final reports. No historical file was modified, no provider request was issued and no network action was performed.

## Integrity and provenance checks

| Check | Result |
| --- | --- |
| User-recorded outer bundle SHA-256 | Exact match |
| Original release manifest | 5/5 entries verified |
| Three original archive checksum sidecars | All verified |
| Portable / analysis / benchmark manifests | 37 / 20 / 14 entries verified |
| Original run manifests | 180/180 verified; 18 bound files per run, 3,240 total |
| Canonical report hashes and previously released frozen-reference joins | 180/180 match |
| Unique scenario–mode–repeat cells and run IDs | 180/180; six scenarios × three modes × ten repeats |
| Retrieval, aggregate, reflection, policy, verification and anchor self-hashes | 180/180 per component |
| Assessor / role raw-payload hashes | 720/720 and 720/720 match |
| Non-null assessor / role parsed-artifact hashes | 710/710 and 720/720 match |
| Frozen input-side retrieval and prompt-provenance joins | All 180 cells match |
| Raw decision/action counts and whole-scenario bootstrap intervals | Reproduce retained results with unchanged seed and 20,000 replicates |

The 720 assessor payload files include failed or invalid responses. Under the archived validity predicate, valid assessor records are 204/240, 235/240 and 230/240 across the three modes; role validity is 240/240 per mode. Missing parsed hashes are not imputed.

## Results independently recomputed from the original reports

| Mode | Cells | Decision agreement | Action agreement | Coverage | NEVER recall | Recorded median / P95 (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| No RAG | 60 | 10/60 (16.7%) | 40/60 (66.7%) | 0/60 | 0/20 | 80.453 / 108.753 |
| RAG | 60 | 50/60 (83.3%) | 50/60 (83.3%) | 40/60 | 10/20 | 100.152 / 150.769 |
| Agentic RAG | 60 | 60/60 (100.0%) | 58/60 (96.7%) | 50/60 | **19/20 (95.0%)** | 109.793 / 164.747 |

The corrected NEVER recall is 95%, independently of the execute flag. All 180 reports have automatic execution disabled. These semantic scores are agreement with the frozen synthetic oracle, not independently validated O-RAN correctness.

## Timing analysis added after recovery

All 180 reports have monotonic timestamps for four disjoint internal intervals. Their per-run sum equals the internal report duration. There are 60 complete timestamp records per mode.

| Mode | Input→retrieval | Retrieval→aggregate | Aggregate→reflection | Reflection→report | Internal report | Indexed timer |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| No RAG | 0.011 | 20.220 | 57.698 | 0.036 | 80.363 | 80.453 |
| RAG | 0.394 | 24.197 | 75.637 | 0.036 | 100.058 | 100.152 |
| Agentic RAG | 3.062 | 26.224 | 79.608 | 0.036 | 109.711 | 109.793 |

Values are marginal medians in seconds. They do not sum to the median total. The aggregate-to-reflection phase contains the role chain and surrounding processing; its median per-run fraction of internal duration is 73.4%, 76.5% and 75.4%. Individual provider-call durations overlap, and complete four-call sums are available for 58/58/57 runs; missing durations are not replaced with zero. These observations do not identify causal component/framework overhead in the unequal LangGraph comparison.

## Reproduce

From the full revision repository root:

```bash
python3 scripts/l4/tnsm_revision/audit_recovered_proposed_evidence.py
python3 -m unittest discover -s test/l4/tnsm_revision -p 'test_*.py' -v
```

Outputs are `evidence/derived/recovered_proposed_audit.json`, `recovered_proposed_cells.csv` and `recovered_proposed_timing.csv` under `paper/tnsm_revision_20261015`. The immutable input bundle is in that directory's `evidence/inputs` folder. The audit uses explicit in-memory path mapping for the original absolute checksum paths; it never opens those historical paths on the reviewer's machine.

## Scope and publication

The earlier missing-file gap is resolved for the original 180 report packages. Their canonical hashes agree with the frozen export previously released with DOI https://doi.org/10.5281/zenodo.21939774. The old DOI ZIP does not contain this newly recovered bundle or new audit code; publish an accessible, versioned revision artifact before claiming that the new package is publicly available.

Hash consistency and reanalysis establish internal integrity and reproducibility of retained results. They do not independently authenticate provider services, prove telemetry truth, validate the six-scenario oracle against experts, demonstrate matched inference-time causality, establish production O-RAN safety or constitute journal acceptance.
