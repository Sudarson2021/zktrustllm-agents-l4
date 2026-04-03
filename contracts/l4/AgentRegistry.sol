// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AgentRegistry {
    struct Agent {
        string agentId;
        address owner;
        bytes32 pubKeyHash;
        string role;
        string modelClass;
        uint8 trustTier;
        bool isActive;
        uint256 registeredAt;
    }

    mapping(bytes32 => Agent) private agents;
    mapping(address => bool) public admins;

    event AgentRegistered(bytes32 indexed agentKey, string agentId, address owner);
    event AgentRevoked(bytes32 indexed agentKey, string agentId);
    event AgentMetadataUpdated(bytes32 indexed agentKey, string role, string modelClass, uint8 trustTier);

    modifier onlyAdmin() {
        require(admins[msg.sender], "not admin");
        _;
    }

    constructor() {
        admins[msg.sender] = true;
    }

    function setAdmin(address who, bool enabled) external onlyAdmin {
        admins[who] = enabled;
    }

    function agentKey(string memory agentId) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(agentId));
    }

    function registerAgent(
        string memory _agentId,
        address _owner,
        bytes32 _pubKeyHash,
        string memory _role,
        string memory _modelClass,
        uint8 _trustTier
    ) external onlyAdmin {
        bytes32 key = agentKey(_agentId);
        require(agents[key].registeredAt == 0, "already registered");

        agents[key] = Agent({
            agentId: _agentId,
            owner: _owner,
            pubKeyHash: _pubKeyHash,
            role: _role,
            modelClass: _modelClass,
            trustTier: _trustTier,
            isActive: true,
            registeredAt: block.timestamp
        });

        emit AgentRegistered(key, _agentId, _owner);
    }

    function revokeAgent(string memory _agentId) external onlyAdmin {
        bytes32 key = agentKey(_agentId);
        require(agents[key].registeredAt != 0, "not found");
        agents[key].isActive = false;
        emit AgentRevoked(key, _agentId);
    }

    function updateAgentMetadata(
        string memory _agentId,
        string memory _role,
        string memory _modelClass,
        uint8 _trustTier
    ) external onlyAdmin {
        bytes32 key = agentKey(_agentId);
        require(agents[key].registeredAt != 0, "not found");

        agents[key].role = _role;
        agents[key].modelClass = _modelClass;
        agents[key].trustTier = _trustTier;

        emit AgentMetadataUpdated(key, _role, _modelClass, _trustTier);
    }

    function isRegistered(string memory _agentId) external view returns (bool) {
        bytes32 key = agentKey(_agentId);
        return agents[key].registeredAt != 0 && agents[key].isActive;
    }

    function getAgent(string memory _agentId) external view returns (Agent memory) {
        return agents[agentKey(_agentId)];
    }
}
