// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/// @title HashCommitmentLedger
/// @notice Isolated benchmark ledger for SHA-256 and SHA-512 evidence digests.
/// @dev SHA-256 and SHA-512 are hash functions, not encryption algorithms.
///      The primary benchmark anchors digests computed off chain so that the
///      comparison changes only the digest width (32 versus 64 bytes). The
///      computeSha256AndAnchor entry point separately measures the EVM SHA-256
///      precompile path. The EVM has no standard SHA-512 precompile.
contract HashCommitmentLedger is AccessControl {
    bytes32 public constant ANCHOR_ROLE = keccak256("ANCHOR_ROLE");

    uint8 public constant SHA256_ID = 1;
    uint8 public constant SHA512_ID = 2;

    mapping(bytes32 => bool) public seenEvidenceIds;

    event HashAnchored(
        bytes32 indexed evidenceId,
        uint8 indexed algorithmId,
        bytes digest,
        address indexed submitter
    );

    error ZeroEvidenceId();
    error DuplicateEvidenceId();
    error UnsupportedHashAlgorithm(uint8 algorithmId);
    error InvalidDigestLength(uint8 algorithmId, uint256 actual, uint256 expected);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ANCHOR_ROLE, admin);
    }

    /// @notice Anchors a precomputed SHA-256 or SHA-512 digest.
    /// @dev This is the apples-to-apples network benchmark path. It does not
    ///      claim that the EVM computed the supplied digest.
    function anchorDigest(
        bytes32 evidenceId,
        uint8 algorithmId,
        bytes calldata digest
    ) external onlyRole(ANCHOR_ROLE) {
        _validateDigest(algorithmId, digest.length);
        _anchor(evidenceId, algorithmId, digest);
    }

    /// @notice Computes SHA-256 through the EVM precompile and anchors it.
    /// @dev This path is reported separately from precomputed-digest anchoring.
    function computeSha256AndAnchor(
        bytes32 evidenceId,
        bytes calldata payload
    ) external onlyRole(ANCHOR_ROLE) returns (bytes32 digest) {
        digest = sha256(payload);
        _anchor(evidenceId, SHA256_ID, abi.encodePacked(digest));
    }

    function _validateDigest(uint8 algorithmId, uint256 actualLength) private pure {
        uint256 expectedLength;
        if (algorithmId == SHA256_ID) {
            expectedLength = 32;
        } else if (algorithmId == SHA512_ID) {
            expectedLength = 64;
        } else {
            revert UnsupportedHashAlgorithm(algorithmId);
        }
        if (actualLength != expectedLength) {
            revert InvalidDigestLength(algorithmId, actualLength, expectedLength);
        }
    }

    function _anchor(
        bytes32 evidenceId,
        uint8 algorithmId,
        bytes memory digest
    ) private {
        if (evidenceId == bytes32(0)) {
            revert ZeroEvidenceId();
        }
        if (seenEvidenceIds[evidenceId]) {
            revert DuplicateEvidenceId();
        }
        seenEvidenceIds[evidenceId] = true;
        emit HashAnchored(evidenceId, algorithmId, digest, msg.sender);
    }
}
