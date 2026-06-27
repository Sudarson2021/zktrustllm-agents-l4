# How to Use the AuthV2.2 Evidence Section in the Paper

Use this LaTeX section file:

`docs/journal/public_testnet_frozen_authv22_section.tex`

Recommended placement:
- After the local Hardhat evaluation subsection.
- Before limitations/future work.
- Reference it as the public-testnet and frozen-proof evidence boundary.

Evidence now safely claimed:
- Sepolia public testnet deployment of AuthV2.2 verifier.
- Sepolia public testnet deployment of RBAC-controlled AuthV2.2 attestor.
- Deployment transaction hashes and gas usage.
- Deployer holds `SUBMITTER_ROLE`.
- Frozen AuthV2.2 positive proof.
- Frozen AuthV2.2 negative mutated proof.
- Frozen AuthV2.2 proof payload.
- Positive ZoKrates verification passes.
- Negative ZoKrates verification fails.

Still not claimed:
- Mainnet deployment.
- Production deployment.
- Full policy-matrix ZK coverage.
- Complete end-to-end O-RAN testbed deployment.
