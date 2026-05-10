# Results Narrative: L4 Automation, Audit, IPFS, and On-Chain Validation

The Level 4 automation pipeline progressed from manual experiment execution to a policy-gated closed-loop workflow.

Step 96 demonstrated that the agentic automation suite can execute and validate the main L4 experiment chain. The suite completed with PASS status and generated machine-readable evidence for control-plane, agent-scaling, RTP, DTLS-RTP, impairment, namespace, and automation outputs.

Step 97 introduced closed-loop KPI decisioning. The KPI agent analysed the generated evidence and recommended `GENERATE_SUPERVISOR_REPORT`, indicating that the checked control-plane, media-plane, impairment, namespace, and automation artifacts passed the expected validation thresholds.

Step 98 executed the recommended remediation action after explicit human approval. This produced the full technical documentation PDF and demonstrated controlled remediation rather than uncontrolled autonomous execution.

Step 99 and Step 100 formalised the governance boundary. The automation governance dashboard and policy-gated scheduler define which actions can be automatic, which require human approval, and which must never be automatic.

Step 101 created a hash-chained automation audit ledger containing 14 evidence entries. The final ledger hash was:

`0db58b3f2c09e530c280dc6cd795a53df54e3337b4a46aa9c70fe6ea166c2567`

Step 102 anchored this ledger using IPFS and a blockchain-ready commitment payload. The IPFS CID was:

`QmW7VeYs3fP5kk92JstT8tAEkQytgseH4SfhKRpcSwU112`

The blockchain-ready anchor commitment hash was:

`50aa798c5968470f172f5e91cb9d80e25b6ac018d3acde55a424f32ec1c2c8ec`

Step 103 submitted this anchor to a local Hardhat smart-contract registry. The registry stored the audit evidence and validated that the stored values matched the submitted ledger hash, ledger SHA-256, IPFS CID, and anchor commitment.

Step 104 added negative-security validation. The registry rejected duplicate commitment replay and rejected zero-commitment submission. This confirms that the trust-plane registry includes basic replay protection and invalid-anchor rejection.

Step 105 integrated on-chain validation into the policy-gated automation workflow, requiring explicit human approval before local Hardhat validation.

Step 109 extended the blockchain validation to a persistent local Hardhat JSON-RPC process. The persistent validation passed, with chain ID `31337`, transaction hash:

`0x0cfb7dde504ad4ce100b6ba219458135fb0dfc2f616d0d4722afc0c9af768ab6`

and gas usage:

`320095`

Overall, the results show that the L4 system is now more than a collection of scripts. It is an integrated, policy-gated, auditable, and blockchain-verifiable agentic automation pipeline.
