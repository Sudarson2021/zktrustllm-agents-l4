// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./generated/AuthV1Verifier.sol";

contract DecisionAttestorGroth16 {
    struct Groth16DecisionRecord {
        string agentId;
        bytes32 capabilityId;
        bytes32 contextHash;
        bytes32 traceCommitment;
        string traceCID;
        string policyClass;
        string action;
        uint256 expiryBucket;
        uint256 timestamp;
    }

    Verifier public verifier;
    uint256 public decisionCount;
    mapping(uint256 => Groth16DecisionRecord) public decisions;

    event Groth16DecisionSubmitted(
        uint256 indexed decisionId,
        string agentId,
        bytes32 capabilityId,
        bytes32 contextHash,
        bytes32 traceCommitment,
        string traceCID,
        string policyClass,
        string action,
        uint256 expiryBucket
    );

    constructor(address _verifier) {
        require(_verifier != address(0), "invalid verifier");
        verifier = Verifier(_verifier);
    }

    function verifierAddress() external view returns (address) {
        return address(verifier);
    }

    function _toProof(
        uint256[2] memory a,
        uint256[2][2] memory b,
        uint256[2] memory c
    ) internal pure returns (Verifier.Proof memory proof) {
        proof.a = Pairing.G1Point({
            X: a[0],
            Y: a[1]
        });

        proof.b = Pairing.G2Point({
            X: [b[0][0], b[0][1]],
            Y: [b[1][0], b[1][1]]
        });

        proof.c = Pairing.G1Point({
            X: c[0],
            Y: c[1]
        });
    }

    function checkProof(
        uint256[2] memory a,
        uint256[2][2] memory b,
        uint256[2] memory c,
        uint256[7] memory input
    ) external view returns (bool) {
        Verifier.Proof memory proof = _toProof(a, b, c);
        return verifier.verifyTx(proof, input);
    }

    function submitDecision(
        string memory agentId,
        bytes32 capabilityId,
        bytes32 contextHash,
        bytes32 traceCommitment,
        string memory traceCID,
        string memory policyClass,
        string memory action,
        uint256 expiryBucket,
        uint256[2] memory a,
        uint256[2][2] memory b,
        uint256[2] memory c,
        uint256[7] memory input
    ) external returns (uint256) {
        require(bytes(agentId).length > 0, "empty agentId");
        require(capabilityId != bytes32(0), "empty capabilityId");
        require(contextHash != bytes32(0), "empty contextHash");
        require(traceCommitment != bytes32(0), "empty traceCommitment");
        require(bytes(traceCID).length > 0, "empty traceCID");
        require(bytes(policyClass).length > 0, "empty policyClass");
        require(bytes(action).length > 0, "empty action");
        require(expiryBucket > 0, "invalid expiryBucket");

        Verifier.Proof memory proof = _toProof(a, b, c);
        bool ok = verifier.verifyTx(proof, input);
        require(ok, "groth16 verification failed");

        decisionCount += 1;
        uint256 id = decisionCount;

        decisions[id] = Groth16DecisionRecord({
            agentId: agentId,
            capabilityId: capabilityId,
            contextHash: contextHash,
            traceCommitment: traceCommitment,
            traceCID: traceCID,
            policyClass: policyClass,
            action: action,
            expiryBucket: expiryBucket,
            timestamp: block.timestamp
        });

        emit Groth16DecisionSubmitted(
            id,
            agentId,
            capabilityId,
            contextHash,
            traceCommitment,
            traceCID,
            policyClass,
            action,
            expiryBucket
        );

        return id;
    }
}
