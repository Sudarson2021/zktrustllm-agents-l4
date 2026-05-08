// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IAuthV2_3Verifier {
    struct G1Point {
        uint256 X;
        uint256 Y;
    }

    struct G2Point {
        uint256[2] X;
        uint256[2] Y;
    }

    struct Proof {
        G1Point a;
        G2Point b;
        G1Point c;
    }

    function verifyTx(Proof calldata proof, uint256[11] calldata input)
        external
        view
        returns (bool);
}

/**
 * @title DecisionAttestorAuthV2_3
 * @notice Stores AUTH_V2.3 reference-bound proof-backed agent decisions.
 * @dev AUTH_V2.3 extends AUTH_V2.2 by adding referenceContextHash and coordinationSessionId.
 */
contract DecisionAttestorAuthV2_3 {
    struct Decision {
        string agentId;
        uint256 agentKey;
        uint256 capabilityId;
        uint256 policyClassHash;
        uint256 actionClass;
        uint256 contextHash;
        uint256 traceCommitment;
        uint256 expiryBucket;
        uint256 policyAdmissibilityFlag;
        uint256 trustState;
        uint256 referenceContextHash;
        uint256 coordinationSessionId;
        uint256 timestamp;
    }

    IAuthV2_3Verifier public immutable verifier;
    uint256 public decisionCount;

    mapping(uint256 => Decision) private decisions;

    event DecisionSubmittedAuthV2_3(
        uint256 indexed decisionId,
        string agentId,
        uint256 agentKey,
        uint256 capabilityId,
        uint256 policyClassHash,
        uint256 actionClass,
        uint256 contextHash,
        uint256 traceCommitment,
        uint256 expiryBucket,
        uint256 policyAdmissibilityFlag,
        uint256 trustState,
        uint256 referenceContextHash,
        uint256 coordinationSessionId,
        uint256 timestamp
    );

    constructor(address verifierAddress) {
        require(verifierAddress != address(0), "AUTH_V2_3: zero verifier");
        verifier = IAuthV2_3Verifier(verifierAddress);
    }

    function submitDecision(
        string calldata agentId,
        IAuthV2_3Verifier.Proof calldata proof,
        uint256[11] calldata input
    ) external returns (uint256) {
        require(bytes(agentId).length > 0, "AUTH_V2_3: empty agentId");
        require(verifier.verifyTx(proof, input), "AUTH_V2_3: invalid proof");

        require(input[3] == 3, "AUTH_V2_3: action must be isolate");
        require(input[7] == 1, "AUTH_V2_3: policy not admissible");
        require(input[8] == 3, "AUTH_V2_3: trust state must be restricted");
        require(input[9] != 0, "AUTH_V2_3: zero reference context");
        require(input[10] != 0, "AUTH_V2_3: zero coordination session");

        decisionCount += 1;
        uint256 decisionId = decisionCount;

        decisions[decisionId] = Decision({
            agentId: agentId,
            agentKey: input[0],
            capabilityId: input[1],
            policyClassHash: input[2],
            actionClass: input[3],
            contextHash: input[4],
            traceCommitment: input[5],
            expiryBucket: input[6],
            policyAdmissibilityFlag: input[7],
            trustState: input[8],
            referenceContextHash: input[9],
            coordinationSessionId: input[10],
            timestamp: block.timestamp
        });

        emit DecisionSubmittedAuthV2_3(
            decisionId,
            agentId,
            input[0],
            input[1],
            input[2],
            input[3],
            input[4],
            input[5],
            input[6],
            input[7],
            input[8],
            input[9],
            input[10],
            block.timestamp
        );

        return decisionId;
    }

    function getDecision(uint256 decisionId)
        external
        view
        returns (
            string memory agentId,
            uint256 agentKey,
            uint256 capabilityId,
            uint256 policyClassHash,
            uint256 actionClass,
            uint256 contextHash,
            uint256 traceCommitment,
            uint256 expiryBucket,
            uint256 policyAdmissibilityFlag,
            uint256 trustState,
            uint256 referenceContextHash,
            uint256 coordinationSessionId,
            uint256 timestamp
        )
    {
        Decision storage d = decisions[decisionId];

        return (
            d.agentId,
            d.agentKey,
            d.capabilityId,
            d.policyClassHash,
            d.actionClass,
            d.contextHash,
            d.traceCommitment,
            d.expiryBucket,
            d.policyAdmissibilityFlag,
            d.trustState,
            d.referenceContextHash,
            d.coordinationSessionId,
            d.timestamp
        );
    }
}
