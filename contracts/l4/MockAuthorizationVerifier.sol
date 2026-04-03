// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MockAuthorizationVerifier {
    function verifyAuthorizationProof(
        bytes32 agentKey,
        bytes32 capabilityId,
        bytes32 policyClassHash,
        bytes32 contextHash,
        bytes32 traceCommitment,
        bytes32 actionHash,
        uint256 expiryBucket,
        bytes calldata proofBlob
    ) external pure returns (bool) {
        agentKey; capabilityId; policyClassHash; contextHash; traceCommitment; actionHash; expiryBucket; proofBlob;
        return true;
    }
}
