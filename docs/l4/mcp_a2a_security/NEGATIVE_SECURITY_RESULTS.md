# Level 4 MCP/A2A Negative Security Results

## Purpose

This document summarises the negative-security tests for the Level 4 proof-governed MCP/A2A coordination workflow.

The goal is to show that the system accepts valid proof-bound references but rejects tampered, malformed, or invalid coordination paths.

## AUTH_V2.3 Negative Tests

AUTH_V2.3 negative tests check whether tampered public inputs are rejected by the verifier and attestor.

Tested cases include:

- tampered `actionClass`,
- tampered `policyAdmissibilityFlag`,
- tampered `trustState`,
- tampered `referenceContextHash`,
- tampered `coordinationSessionId`,
- tampered `proofOutput`,
- wrong public input length.

Measured result:

- valid proof path accepted,
- negative cases tested: `7`,
- negative cases passed: `7`,
- unauthorized/tampered rejection rate: `1.0`.

Result file:

- `results/l4_auth_v2_3_negative/auth_v2_3_negative_summary.json`

## MCP/A2A Negative Tests

MCP/A2A negative tests check invalid context and invalid reference handling through the MCP tool layer.

Tested cases include:

- invalid AUTH_V2.2 decision lookup,
- invalid A2A reference lookup,
- invalid A2A reference validity check,
- invalid reference-bundle verification.

Expected result:

- invalid decision/reference context is rejected or marked invalid.

Result file:

- `results/l4_mcp_a2a_security/mcp_a2a_negative_summary.json`

## Research Meaning

These tests strengthen the Level 4 claim.

The system does not only accept valid MCP/A2A reference-bound proof paths; it also rejects tampered proof inputs and invalid reference/context lookups.

This supports the security argument that Level 4 coordination is proof-governed, reference-bound, and resistant to malformed coordination attempts.
