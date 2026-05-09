// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title L4AutomationAuditAnchorRegistry
/// @notice Records ZKTrustLLM L4 automation audit-ledger anchors.
/// @dev This is a local/testnet research registry for auditability evaluation.
contract L4AutomationAuditAnchorRegistry {
    struct AnchorRecord {
        bytes32 ledgerHash;
        bytes32 ledgerSha256;
        bytes32 anchorCommitmentHash;
        string ipfsCid;
        string anchorType;
        uint256 timestamp;
        address submitter;
    }

    uint256 public anchorCount;

    mapping(uint256 => AnchorRecord) public anchors;
    mapping(bytes32 => bool) public commitmentSeen;

    event AuditAnchorSubmitted(
        uint256 indexed anchorId,
        bytes32 indexed anchorCommitmentHash,
        bytes32 ledgerHash,
        bytes32 ledgerSha256,
        string ipfsCid,
        string anchorType,
        address indexed submitter,
        uint256 timestamp
    );

    function submitAnchor(
        bytes32 ledgerHash,
        bytes32 ledgerSha256,
        bytes32 anchorCommitmentHash,
        string calldata ipfsCid,
        string calldata anchorType
    ) external returns (uint256 anchorId) {
        require(anchorCommitmentHash != bytes32(0), "empty commitment");
        require(!commitmentSeen[anchorCommitmentHash], "commitment already anchored");

        anchorId = anchorCount;
        anchorCount += 1;

        anchors[anchorId] = AnchorRecord({
            ledgerHash: ledgerHash,
            ledgerSha256: ledgerSha256,
            anchorCommitmentHash: anchorCommitmentHash,
            ipfsCid: ipfsCid,
            anchorType: anchorType,
            timestamp: block.timestamp,
            submitter: msg.sender
        });

        commitmentSeen[anchorCommitmentHash] = true;

        emit AuditAnchorSubmitted(
            anchorId,
            anchorCommitmentHash,
            ledgerHash,
            ledgerSha256,
            ipfsCid,
            anchorType,
            msg.sender,
            block.timestamp
        );
    }

    function getAnchor(uint256 anchorId) external view returns (AnchorRecord memory) {
        require(anchorId < anchorCount, "anchor not found");
        return anchors[anchorId];
    }
}
