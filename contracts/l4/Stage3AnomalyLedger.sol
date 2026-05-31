// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/// @title Stage3AnomalyLedger
/// @notice Minimal isolated runtime-hook contract for scientific KPI extraction.
/// @dev This is not the production ledger. It is a micro-benchmark/test hook used
///      to emit direct evidence for anchor gas, duplicate-replay rejection,
///      zero-commitment rejection, and unauthorized submitter rejection.
contract Stage3AnomalyLedger is AccessControl {
    bytes32 public constant ANCHOR_ROLE = keccak256("ANCHOR_ROLE");

    mapping(bytes32 => bool) public seenCommitments;

    event Stage3Anchored(
        bytes32 indexed commitment,
        bytes32 indexed evidenceHash,
        address indexed submitter
    );

    error ZeroCommitment();
    error DuplicateCommitment();

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ANCHOR_ROLE, admin);
    }

    function commit(bytes32 commitment, bytes32 evidenceHash)
        external
        onlyRole(ANCHOR_ROLE)
    {
        if (commitment == bytes32(0)) {
            revert ZeroCommitment();
        }

        if (seenCommitments[commitment]) {
            revert DuplicateCommitment();
        }

        seenCommitments[commitment] = true;

        emit Stage3Anchored(commitment, evidenceHash, msg.sender);
    }
}
