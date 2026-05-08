// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IDecisionAttestorAuthV2_2 {
    function decisionCount() external view returns (uint256);

    function getDecision(uint256 id)
        external
        view
        returns (
            string memory agentId,
            bytes32 capabilityId,
            bytes32 policyClassHash,
            uint256 actionClass,
            bytes32 contextHash,
            bytes32 traceCommitment,
            uint256 expiryBucket,
            uint256 policyAdmissibilityFlag,
            uint256 trustState,
            uint256 timestamp
        );
}

/**
 * @title A2AReferenceRegistry
 * @notice Level 4 reference-aware coordination registry.
 * @dev Agent A creates a proof-backed AUTH_V2.2 decision.
 *      Agent B receives only a compact reference to that decision.
 *      The registry verifies that the reference is bound to the authenticated on-chain decision.
 */
contract A2AReferenceRegistry {
    struct A2AReferenceRecord {
        bool exists;
        string senderAgentId;
        string receiverAgentId;
        uint256 sourceDecisionId;
        uint256 sourceBlockNumber;
        bytes32 capabilityId;
        bytes32 policyClassHash;
        uint256 actionClass;
        bytes32 contextHash;
        bytes32 traceCommitment;
        bytes32 cidHash;
        bytes32 proofRef;
        uint256 expiryBucket;
        uint256 expiresAt;
        uint256 createdAt;
    }

    IDecisionAttestorAuthV2_2 public immutable decisionAttestor;
    uint256 public referenceCount;

    mapping(uint256 => A2AReferenceRecord) private referencesById;
    mapping(bytes32 => bool) public usedReferenceHash;

    event A2AReferenceRegistered(
        uint256 indexed referenceId,
        string senderAgentId,
        string receiverAgentId,
        uint256 indexed sourceDecisionId,
        uint256 sourceBlockNumber,
        bytes32 capabilityId,
        bytes32 policyClassHash,
        uint256 actionClass,
        bytes32 contextHash,
        bytes32 traceCommitment,
        bytes32 cidHash,
        bytes32 proofRef,
        uint256 expiryBucket,
        uint256 expiresAt
    );

    constructor(address decisionAttestorAddress) {
        require(decisionAttestorAddress != address(0), "A2ARef: zero attestor");
        decisionAttestor = IDecisionAttestorAuthV2_2(decisionAttestorAddress);
    }

    function registerReference(
        string memory senderAgentId,
        string memory receiverAgentId,
        uint256 sourceDecisionId,
        bytes32 capabilityId,
        bytes32 policyClassHash,
        uint256 actionClass,
        bytes32 contextHash,
        bytes32 traceCommitment,
        bytes32 cidHash,
        bytes32 proofRef,
        uint256 expiryBucket,
        uint256 expiresAt
    ) external returns (uint256) {
        require(bytes(senderAgentId).length > 0, "A2ARef: empty sender");
        require(bytes(receiverAgentId).length > 0, "A2ARef: empty receiver");
        require(sourceDecisionId > 0, "A2ARef: zero decision");
        require(sourceDecisionId <= decisionAttestor.decisionCount(), "A2ARef: unknown decision");
        require(expiresAt > block.timestamp, "A2ARef: expired reference");
        require(cidHash != bytes32(0), "A2ARef: zero cidHash");
        require(proofRef != bytes32(0), "A2ARef: zero proofRef");

        (
            string memory storedAgentId,
            bytes32 storedCapabilityId,
            bytes32 storedPolicyClassHash,
            uint256 storedActionClass,
            bytes32 storedContextHash,
            bytes32 storedTraceCommitment,
            uint256 storedExpiryBucket,
            ,
            ,
            uint256 storedTimestamp
        ) = decisionAttestor.getDecision(sourceDecisionId);

        require(storedTimestamp != 0, "A2ARef: missing source decision");
        require(
            keccak256(bytes(storedAgentId)) == keccak256(bytes(senderAgentId)),
            "A2ARef: sender mismatch"
        );
        require(storedCapabilityId == capabilityId, "A2ARef: capability mismatch");
        require(storedPolicyClassHash == policyClassHash, "A2ARef: policy mismatch");
        require(storedActionClass == actionClass, "A2ARef: action mismatch");
        require(storedContextHash == contextHash, "A2ARef: context mismatch");
        require(storedTraceCommitment == traceCommitment, "A2ARef: trace mismatch");
        require(storedExpiryBucket == expiryBucket, "A2ARef: expiry bucket mismatch");

        bytes32 referenceHash = keccak256(
            abi.encodePacked(
                block.chainid,
                senderAgentId,
                receiverAgentId,
                sourceDecisionId,
                capabilityId,
                policyClassHash,
                actionClass,
                contextHash,
                traceCommitment,
                cidHash,
                proofRef,
                expiryBucket,
                expiresAt
            )
        );

        require(!usedReferenceHash[referenceHash], "A2ARef: duplicate reference");

        usedReferenceHash[referenceHash] = true;
        referenceCount += 1;

        uint256 referenceId = referenceCount;

        referencesById[referenceId] = A2AReferenceRecord({
            exists: true,
            senderAgentId: senderAgentId,
            receiverAgentId: receiverAgentId,
            sourceDecisionId: sourceDecisionId,
            sourceBlockNumber: block.number,
            capabilityId: capabilityId,
            policyClassHash: policyClassHash,
            actionClass: actionClass,
            contextHash: contextHash,
            traceCommitment: traceCommitment,
            cidHash: cidHash,
            proofRef: proofRef,
            expiryBucket: expiryBucket,
            expiresAt: expiresAt,
            createdAt: block.timestamp
        });

        emit A2AReferenceRegistered(
            referenceId,
            senderAgentId,
            receiverAgentId,
            sourceDecisionId,
            block.number,
            capabilityId,
            policyClassHash,
            actionClass,
            contextHash,
            traceCommitment,
            cidHash,
            proofRef,
            expiryBucket,
            expiresAt
        );

        return referenceId;
    }

    function isReferenceValid(uint256 referenceId) external view returns (bool) {
        A2AReferenceRecord storage r = referencesById[referenceId];
        return r.exists && block.timestamp < r.expiresAt;
    }

    function getReference(uint256 referenceId)
        external
        view
        returns (
            bool exists,
            string memory senderAgentId,
            string memory receiverAgentId,
            uint256 sourceDecisionId,
            uint256 sourceBlockNumber,
            bytes32 capabilityId,
            bytes32 policyClassHash,
            uint256 actionClass,
            bytes32 contextHash,
            bytes32 traceCommitment,
            bytes32 cidHash,
            bytes32 proofRef,
            uint256 expiryBucket,
            uint256 expiresAt,
            uint256 createdAt
        )
    {
        A2AReferenceRecord storage r = referencesById[referenceId];

        return (
            r.exists,
            r.senderAgentId,
            r.receiverAgentId,
            r.sourceDecisionId,
            r.sourceBlockNumber,
            r.capabilityId,
            r.policyClassHash,
            r.actionClass,
            r.contextHash,
            r.traceCommitment,
            r.cidHash,
            r.proofRef,
            r.expiryBucket,
            r.expiresAt,
            r.createdAt
        );
    }
}
