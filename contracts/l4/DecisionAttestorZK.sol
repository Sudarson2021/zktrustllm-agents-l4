// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IAuthorizationVerifier {
    function verifyAuthorizationProof(
        bytes32 agentKey,
        bytes32 capabilityId,
        bytes32 policyClassHash,
        bytes32 contextHash,
        bytes32 traceCommitment,
        bytes32 actionHash,
        uint256 expiryBucket,
        bytes calldata proofBlob
    ) external view returns (bool);
}

interface IAgentRegistryZK {
    function isRegistered(string memory _agentId) external view returns (bool);
    function agentKey(string memory _agentId) external pure returns (bytes32);
}

interface ICapabilityManagerZK {
    struct Capability {
        bytes32 capabilityId;
        bytes32 agentKey;
        bytes32 scopeHash;
        string policyClass;
        uint256 issuedAt;
        uint256 expiresAt;
        bool revoked;
    }

    function isValid(bytes32 _capabilityId) external view returns (bool);
    function getCapability(bytes32 _capabilityId) external view returns (Capability memory);
}

contract DecisionAttestorZK {
    struct ZKDecisionRecord {
        string agentId;
        bytes32 capabilityId;
        bytes32 contextHash;
        bytes32 traceCommitment;
        string traceCID;
        string policyClass;
        string action;
        uint256 expiryBucket;
        uint256 submittedAt;
    }

    IAgentRegistryZK public agentRegistry;
    ICapabilityManagerZK public capabilityManager;
    IAuthorizationVerifier public verifier;

    uint256 public zkDecisionCount;
    mapping(uint256 => ZKDecisionRecord) public zkDecisions;

    event ZKDecisionSubmitted(
        uint256 indexed decisionId,
        string agentId,
        bytes32 indexed capabilityId,
        string policyClass,
        string action,
        bytes32 traceCommitment,
        string traceCID,
        uint256 expiryBucket
    );

    constructor(address _agentRegistry, address _capabilityManager, address _verifier) {
        agentRegistry = IAgentRegistryZK(_agentRegistry);
        capabilityManager = ICapabilityManagerZK(_capabilityManager);
        verifier = IAuthorizationVerifier(_verifier);
    }

    function _verifyProof(
        bytes32 agentKey_,
        bytes32 capabilityId_,
        string memory policyClass_,
        bytes32 contextHash_,
        bytes32 traceCommitment_,
        string memory action_,
        uint256 expiryBucket_,
        bytes calldata proofBlob_
    ) internal view returns (bool) {
        return verifier.verifyAuthorizationProof(
            agentKey_,
            capabilityId_,
            keccak256(bytes(policyClass_)),
            contextHash_,
            traceCommitment_,
            keccak256(bytes(action_)),
            expiryBucket_,
            proofBlob_
        );
    }

    function _storeDecision(
        string memory agentId_,
        bytes32 capabilityId_,
        bytes32 contextHash_,
        bytes32 traceCommitment_,
        string memory traceCID_,
        string memory policyClass_,
        string memory action_,
        uint256 expiryBucket_
    ) internal returns (uint256) {
        uint256 newId = zkDecisionCount + 1;
        zkDecisionCount = newId;

        zkDecisions[newId] = ZKDecisionRecord({
            agentId: agentId_,
            capabilityId: capabilityId_,
            contextHash: contextHash_,
            traceCommitment: traceCommitment_,
            traceCID: traceCID_,
            policyClass: policyClass_,
            action: action_,
            expiryBucket: expiryBucket_,
            submittedAt: block.timestamp
        });

        emit ZKDecisionSubmitted(
            newId,
            agentId_,
            capabilityId_,
            policyClass_,
            action_,
            traceCommitment_,
            traceCID_,
            expiryBucket_
        );

        return newId;
    }

    function submitAgentDecisionZK(
        string memory _agentId,
        bytes32 _capabilityId,
        bytes32 _contextHash,
        bytes32 _traceCommitment,
        string memory _traceCID,
        string memory _policyClass,
        string memory _action,
        uint256 _expiryBucket,
        bytes calldata _proofBlob
    ) external returns (uint256) {
        require(agentRegistry.isRegistered(_agentId), "agent not registered");
        require(capabilityManager.isValid(_capabilityId), "capability invalid");

        bytes32 computedAgentKey = agentRegistry.agentKey(_agentId);
        ICapabilityManagerZK.Capability memory cap = capabilityManager.getCapability(_capabilityId);

        require(cap.agentKey == computedAgentKey, "capability not owned by agent");

        bool ok = _verifyProof(
            computedAgentKey,
            _capabilityId,
            _policyClass,
            _contextHash,
            _traceCommitment,
            _action,
            _expiryBucket,
            _proofBlob
        );
        require(ok, "authorization proof failed");

        return _storeDecision(
            _agentId,
            _capabilityId,
            _contextHash,
            _traceCommitment,
            _traceCID,
            _policyClass,
            _action,
            _expiryBucket
        );
    }
}
