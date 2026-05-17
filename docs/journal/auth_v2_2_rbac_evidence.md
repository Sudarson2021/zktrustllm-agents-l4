# AuthV2.2 RBAC Evidence

The publication-target contract `DecisionAttestorAuthV2_2` has been upgraded with OpenZeppelin `AccessControl`.

Implemented controls:
- `SUBMITTER_ROLE = keccak256("SUBMITTER_ROLE")`
- deployer receives `DEFAULT_ADMIN_ROLE`
- deployer receives `SUBMITTER_ROLE`
- `submitDecision(...)` is gated by `onlyRole(SUBMITTER_ROLE)`

Targeted tests:
- unauthorized submitter is rejected
- deployer has default admin and submitter roles
- admin can grant submitter role to another account

This closes the previous reviewer concern that trust-plane evidence submission was permissionless.
