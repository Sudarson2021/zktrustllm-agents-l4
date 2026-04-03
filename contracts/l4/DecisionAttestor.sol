// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IAgentRegistryLite {
    function isRegistered(string memory _agentId) external view returns (bool);
    function agentKey(string memory _agentId) external pure returns (bytes32);
}

interface ICapabilityManagerLite {
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

contract DecisionAttestor {
    struct DecisionRecord {
        string agentId;
        bytes32 capabilityId;
        bytes32 contextHash;
        bytes32 traceCommitment;
        string traceCID;
        string policyClass;
        string action;
        uint256 submittedAt;
    }

    IAgentRegistryLite public agentRegistry;
    ICapabilityManagerLite public capabilityManager;
    uint256 public decisionCount;

    mapping(uint256 => DecisionRecord) public decisions;

    event DecisionSubmitted(
        uint256 indexed decisionId,
        string agentId,
        bytes32 indexed capabilityId,
        string policyClass,
        string action,
        bytes32 traceCommitment,
        string traceCID
    );

    constructor(address _agentRegistry, address _capabilityManager) {
        agentRegistry = IAgentRegistryLite(_agentRegistry);
        capabilityManager = ICapabilityManagerLite(_capabilityManager);
    }

    function _sameString(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function submitAgentDecisionMock(
        string memory _agentId,
        bytes32 _capabilityId,
        bytes32 _contextHash,
        bytes32 _traceCommitment,
        string memory _traceCID,
        string memory _policyClass,
        string memory _action
    ) external returns (uint256) {
        require(agentRegistry.isRegistered(_agentId), "agent not registered");
        require(capabilityManager.isValid(_capabilityId), "capability invalid");

        ICapabilityManagerLite.Capability memory cap = capabilityManager.getCapability(_capabilityId);

        require(cap.capabilityId == _capabilityId, "capability mismatch");
        require(cap.agentKey == agentRegistry.agentKey(_agentId), "capability not owned by agent");
        require(_sameString(cap.policyClass, _policyClass), "policy class mismatch");

        decisionCount += 1;
        decisions[decisionCount] = DecisionRecord({
            agentId: _agentId,
            capabilityId: _capabilityId,
            contextHash: _contextHash,
            traceCommitment: _traceCommitment,
            traceCID: _traceCID,
            policyClass: _policyClass,
            action: _action,
            submittedAt: block.timestamp
        });

        emit DecisionSubmitted(
            decisionCount,
            _agentId,
            _capabilityId,
            _policyClass,
            _action,
            _traceCommitment,
            _traceCID
        );

        return decisionCount;
    }
}
