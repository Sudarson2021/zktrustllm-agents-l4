// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AgentRegistry {
    enum Role {
        EdgeTelemetryAgent,
        TrustRiskAgent,
        PolicyLKHAgent
    }

    enum Status {
        Active,
        Suspended,
        Revoked
    }

    struct AgentRecord {
        bool exists;
        string agentId;
        address agentAddress;
        Role role;
        Status status;
        uint64 registeredAt;
        uint64 updatedAt;
        bytes32 metadataHash;
    }

    address public owner;

    mapping(bytes32 => AgentRecord) private agentByIdHash;
    mapping(address => bytes32) private idHashByAddress;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    event AgentRegistered(
        bytes32 indexed agentIdHash,
        string agentId,
        address agentAddress,
        Role role,
        bytes32 metadataHash
    );

    event AgentSuspended(bytes32 indexed agentIdHash, string agentId);
    event AgentRevoked(bytes32 indexed agentIdHash, string agentId);
    event AgentReactivated(bytes32 indexed agentIdHash, string agentId);
    event AgentMetadataUpdated(bytes32 indexed agentIdHash, string agentId, bytes32 metadataHash);

    modifier onlyOwner() {
        require(msg.sender == owner, "AgentRegistry: not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "AgentRegistry: zero owner");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }

    function registerAgent(
        string memory agentId,
        address agentAddress,
        Role role,
        bytes32 metadataHash
    ) external onlyOwner {
        require(bytes(agentId).length > 0, "AgentRegistry: empty agentId");
        require(agentAddress != address(0), "AgentRegistry: zero address");
        require(isRoleAllowed(role), "AgentRegistry: invalid role");

        bytes32 agentIdHash = keccak256(bytes(agentId));
        require(!agentByIdHash[agentIdHash].exists, "AgentRegistry: agentId exists");
        require(idHashByAddress[agentAddress] == bytes32(0), "AgentRegistry: address already assigned");

        uint64 nowTs = uint64(block.timestamp);

        agentByIdHash[agentIdHash] = AgentRecord({
            exists: true,
            agentId: agentId,
            agentAddress: agentAddress,
            role: role,
            status: Status.Active,
            registeredAt: nowTs,
            updatedAt: nowTs,
            metadataHash: metadataHash
        });

        idHashByAddress[agentAddress] = agentIdHash;

        emit AgentRegistered(agentIdHash, agentId, agentAddress, role, metadataHash);
    }

    function suspendAgent(string memory agentId) external onlyOwner {
        bytes32 agentIdHash = keccak256(bytes(agentId));
        AgentRecord storage record = agentByIdHash[agentIdHash];

        require(record.exists, "AgentRegistry: unknown agent");
        require(record.status != Status.Revoked, "AgentRegistry: already revoked");

        record.status = Status.Suspended;
        record.updatedAt = uint64(block.timestamp);

        emit AgentSuspended(agentIdHash, record.agentId);
    }

    function revokeAgent(string memory agentId) external onlyOwner {
        bytes32 agentIdHash = keccak256(bytes(agentId));
        AgentRecord storage record = agentByIdHash[agentIdHash];

        require(record.exists, "AgentRegistry: unknown agent");

        record.status = Status.Revoked;
        record.updatedAt = uint64(block.timestamp);

        emit AgentRevoked(agentIdHash, record.agentId);
    }

    function reactivateAgent(string memory agentId) external onlyOwner {
        bytes32 agentIdHash = keccak256(bytes(agentId));
        AgentRecord storage record = agentByIdHash[agentIdHash];

        require(record.exists, "AgentRegistry: unknown agent");
        require(record.status == Status.Suspended, "AgentRegistry: not suspended");

        record.status = Status.Active;
        record.updatedAt = uint64(block.timestamp);

        emit AgentReactivated(agentIdHash, record.agentId);
    }

    function updateMetadataHash(string memory agentId, bytes32 metadataHash) external onlyOwner {
        bytes32 agentIdHash = keccak256(bytes(agentId));
        AgentRecord storage record = agentByIdHash[agentIdHash];

        require(record.exists, "AgentRegistry: unknown agent");

        record.metadataHash = metadataHash;
        record.updatedAt = uint64(block.timestamp);

        emit AgentMetadataUpdated(agentIdHash, record.agentId, metadataHash);
    }

    function getAgent(
        string memory agentId
    )
        external
        view
        returns (
            bool exists,
            string memory storedAgentId,
            address agentAddress,
            Role role,
            Status status,
            uint64 registeredAt,
            uint64 updatedAt,
            bytes32 metadataHash
        )
    {
        bytes32 agentIdHash = keccak256(bytes(agentId));
        AgentRecord storage record = agentByIdHash[agentIdHash];

        return (
            record.exists,
            record.agentId,
            record.agentAddress,
            record.role,
            record.status,
            record.registeredAt,
            record.updatedAt,
            record.metadataHash
        );
    }

    function isActiveAgent(string memory agentId) public view returns (bool) {
        bytes32 agentIdHash = keccak256(bytes(agentId));
        AgentRecord storage record = agentByIdHash[agentIdHash];
        return record.exists && record.status == Status.Active;
    }

    function isRoleAllowed(Role role) public pure returns (bool) {
        return
            role == Role.EdgeTelemetryAgent ||
            role == Role.TrustRiskAgent ||
            role == Role.PolicyLKHAgent;
    }

    function getAgentIdHashByAddress(address agentAddress) external view returns (bytes32) {
        return idHashByAddress[agentAddress];
    }

    function getAgentByAddress(
        address agentAddress
    )
        external
        view
        returns (
            bool exists,
            string memory storedAgentId,
            address storedAgentAddress,
            Role role,
            Status status,
            uint64 registeredAt,
            uint64 updatedAt,
            bytes32 metadataHash
        )
    {
        bytes32 agentIdHash = idHashByAddress[agentAddress];
        AgentRecord storage record = agentByIdHash[agentIdHash];

        return (
            record.exists,
            record.agentId,
            record.agentAddress,
            record.role,
            record.status,
            record.registeredAt,
            record.updatedAt,
            record.metadataHash
        );
    }
}
