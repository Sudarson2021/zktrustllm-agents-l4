# Step 105 Policy-Gated On-Chain Audit-Anchor Validation

## Purpose

Step 105 integrates the Step 103 and Step 104 on-chain audit-anchor validation into the policy-gated Level 4 automation workflow.

This step moves the project from manual smart-contract validation toward controlled, approval-gated agentic validation.

## Workflow

The policy-gated runner performs:

1. Reads `configs/l4_automation_policy.json`.
2. Checks whether `VALIDATE_ONCHAIN_AUDIT_ANCHOR_SECURITY` is allowed.
3. Runs dry-run mode by default.
4. Requires `--execute --approve-human` before running local Hardhat validation.
5. Executes Step 103 on-chain anchor submission on local Hardhat.
6. Executes Step 104 replay/negative-security validation on local Hardhat.
7. Produces JSON, Markdown, stdout, and stderr evidence.

## Safety Boundary

This step uses local Hardhat only.

It does not:

- deploy to public chain,
- use real funds,
- push code,
- submit papers,
- email supervisors,
- modify Git history,
- run privileged commands.

## Main Artifacts

- Runner:
  - `scripts/l4/run_policy_gated_onchain_anchor_validation.py`

- Policy:
  - `configs/l4_automation_policy.json`

- Summary JSON:
  - `results/l4_policy_onchain_validation/policy_onchain_validation_summary.json`

- Summary Markdown:
  - `results/l4_policy_onchain_validation/policy_onchain_validation_summary.md`

## Research Meaning

Step 105 connects the automation governance layer with the blockchain trust-plane validation layer.

The L4 workflow can now automatically plan on-chain audit-anchor validation, but execution remains gated by explicit human approval. This supports a strong PhD claim: the system is moving toward autonomous agentic research automation while preserving governance, auditability, and safety.
