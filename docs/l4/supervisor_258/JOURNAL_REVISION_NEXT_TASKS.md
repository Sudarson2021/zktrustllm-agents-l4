# Journal Revision Next Tasks after n8n Scientific Evaluation Layer

## A. Formal Verification

- Run TLA+ / TLC model checking for `formal/tla/ZKTrustLLMPolicyGate.tla`.
- Add a result table showing each invariant and PASS/FAIL status.
- Add Solidity invariant tests for replay, zero anchor, unauthorized submitter, and invalid policy action.

## B. Scientific Evaluation

- Run n8n workflow for 6 variants x 4 profiles x 10 repeats = 240 ablation records.
- Generate `n8n_all_runs.csv`.
- Generate `n8n_evaluation_summary.md`.
- Convert summary into paper tables.

## C. Figures

- Figure 1: O-RAN + L4 agentic architecture.
- Figure 2: threat-response workflow examples.
- Figure 3: ZK ablation overhead.
- Figure 4: demo KPI dashboard summary.
- Figure 5: Open RAN MNO policy placement.

## D. Tables

- Table I: quantitative novelty comparison.
- Table II: formal verification results.
- Table III: demo KPIs.
- Table IV: ablation study.
- Table V: access-control comparison.
- Table VI: blockchain/test-mode comparison.
- Table VII: threat-response validation.

## E. Paper Text

- Add n8n-orchestrated evaluation subsection.
- Add agentic AI component subsection.
- Add smart-contract boundary subsection.
- Add computational complexity subsection.
- Add Open RAN MNO policy subsection.
- Add limitations: local Hardhat is not production consensus; IPFS needs pinning; ZK proves bounded admissibility, not semantic correctness of LLM reasoning.
