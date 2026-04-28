// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./generated/AuthV2_1Verifier.sol";

contract DecisionAttestorAuthV2_1 {
    struct AuthV2_1DecisionRecord {
        string agentId;
        bytes32 capabilityId;
        bytes32 policyClassHash;
        uint256 actionClass;
        bytes32 contextHash;
        bytes32 traceCommitment;
        uint256 expiryBucket;
        uint256 policyAdmissibilityFlag;
        uint256 timestamp;
    }

    Verifier public verifier;
    uint256 public decisionCount;
    mapping(uint256 => AuthV2_1DecisionRecord) private decisions;

    event AuthV2_1DecisionSubmitted(
        uint256 indexed decisionId,
        string agentId,
        bytes32 capabilityId,
        bytes32 policyClassHash,
        uint256 actionClass,
        bytes32 contextHash,
        bytes32 traceCommitment,
        uint256 expiryBucket,
        uint256 policyAdmissibilityFlag
    );

    constructor(address verifierAddress_) {
        require(verifierAddress_ != address(0), "AuthV2_1: zero verifier");
        verifier = Verifier(verifierAddress_);
    }

    function verifierAddress() external view returns (address) {
        return address(verifier);
    }

    function _toProof(
        uint256[2] memory a,
        uint256[2][2] memory b,
        uint256[2] memory c
    ) internal pure returns (Verifier.Proof memory proof) {
        proof.a = Pairing.G1Point({X: a[0], Y: a[1]});
        proof.b = Pairing.G2Point({X: [b[0][0], b[0][1]], Y: [b[1][0], b[1][1]]});
        proof.c = Pairing.G1Point({X: c[0], Y: c[1]});
    }

    function checkProof(
        uint256[2] memory a,
        uint256[2][2] memory b,
        uint256[2] memory c,
        uint256[8] memory input
    ) public view returns (bool) {
        Verifier.Proof memory proof = _toProof(a, b, c);
        return verifier.verifyTx(proof, input);
    }

    function submitDecision(
        string memory agentId,
        bytes32 capabilityId,
        bytes32 policyClassHash,
        uint256 actionClass,
        bytes32 contextHash,
        bytes32 traceCommitment,
        uint256 expiryBucket,
        uint256 policyAdmissibilityFlag,
        uint256[2] memory a,
        uint256[2][2] memory b,
        uint256[2] memory c,
        uint256[8] memory input
    ) external returns (uint256) {
        require(checkProof(a, b, c, input), "AuthV2_1: invalid proof");

        decisionCount += 1;
        uint256 id = decisionCount;

        decisions[id] = AuthV2_1DecisionRecord({
            agentId: agentId,
            capabilityId: capabilityId,
            policyClassHash: policyClassHash,
            actionClass: actionClass,
            contextHash: contextHash,
            traceCommitment: traceCommitment,
            expiryBucket: expiryBucket,
            policyAdmissibilityFlag: policyAdmissibilityFlag,
            timestamp: block.timestamp
        });

        emit AuthV2_1DecisionSubmitted(
            id,
            agentId,
            capabilityId,
            policyClassHash,
            actionClass,
            contextHash,
            traceCommitment,
            expiryBucket,
            policyAdmissibilityFlag
        );

        return id;
    }

    function getDecision(
        uint256 id
    )
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
            uint256 timestamp
        )
    {
        AuthV2_1DecisionRecord storage d = decisions[id];
        return (
            d.agentId,
            d.capabilityId,
            d.policyClassHash,
            d.actionClass,
            d.contextHash,
            d.traceCommitment,
            d.expiryBucket,
            d.policyAdmissibilityFlag,
            d.timestamp
        );
    }
}
