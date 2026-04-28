// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./AgentRegistry.sol";

contract CapabilityManager {
    enum ActionClass {
        Keep,
        Rekey,
        Rotate,
        Isolate,
        Quarantine
    }

    enum CapabilityStatus {
        Valid,
        Revoked
    }

    struct CapabilityRecord {
        bool exists;
        bytes32 capabilityId;
        string agentId;
        address agentAddress;
        string policyClass;
        ActionClass actionClass;
        bytes32 scopeHash;
        bytes32 contextHash;
        uint64 issuedAt;
        uint64 expiry;
        CapabilityStatus status;
    }

    address public owner;
    AgentRegistry public immutable agentRegistry;

    mapping(bytes32 => CapabilityRecord) private capabilityById;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    event CapabilityIssued(
        bytes32 indexed capabilityId,
        string agentId,
        address agentAddress,
        string policyClass,
        ActionClass actionClass,
        bytes32 scopeHash,
        bytes32 contextHash,
        uint64 expiry
    );

    event CapabilityRevoked(bytes32 indexed capabilityId);

    modifier onlyOwner() {
        require(msg.sender == owner, "CapabilityManager: not owner");
        _;
    }

    constructor(address agentRegistryAddress) {
        require(agentRegistryAddress != address(0), "CapabilityManager: zero registry");
        owner = msg.sender;
        agentRegistry = AgentRegistry(agentRegistryAddress);
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "CapabilityManager: zero owner");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }

    function issueCapability(
        bytes32 capabilityId,
        string memory agentId,
        address agentAddress,
        string memory policyClass,
        ActionClass actionClass,
        bytes32 scopeHash,
        bytes32 contextHash,
        uint64 expiry
    ) external onlyOwner {
        require(capabilityId != bytes32(0), "CapabilityManager: zero capabilityId");
        require(!capabilityById[capabilityId].exists, "CapabilityManager: capability exists");
        require(bytes(agentId).length > 0, "CapabilityManager: empty agentId");
        require(agentAddress != address(0), "CapabilityManager: zero agent address");
        require(bytes(policyClass).length > 0, "CapabilityManager: empty policyClass");
        require(expiry > block.timestamp, "CapabilityManager: expiry not future");

        require(agentRegistry.isActiveAgent(agentId), "CapabilityManager: agent not active");

        (
            bool exists,
            ,
            address storedAgentAddress,
            ,
            ,
            ,
            ,
            
        ) = agentRegistry.getAgent(agentId);

        require(exists, "CapabilityManager: unknown agent");
        require(storedAgentAddress == agentAddress, "CapabilityManager: agent address mismatch");

        capabilityById[capabilityId] = CapabilityRecord({
            exists: true,
            capabilityId: capabilityId,
            agentId: agentId,
            agentAddress: agentAddress,
            policyClass: policyClass,
            actionClass: actionClass,
            scopeHash: scopeHash,
            contextHash: contextHash,
            issuedAt: uint64(block.timestamp),
            expiry: expiry,
            status: CapabilityStatus.Valid
        });

        emit CapabilityIssued(
            capabilityId,
            agentId,
            agentAddress,
            policyClass,
            actionClass,
            scopeHash,
            contextHash,
            expiry
        );
    }

    function revokeCapability(bytes32 capabilityId) external onlyOwner {
        CapabilityRecord storage record = capabilityById[capabilityId];

        require(record.exists, "CapabilityManager: unknown capability");
        require(record.status != CapabilityStatus.Revoked, "CapabilityManager: already revoked");

        record.status = CapabilityStatus.Revoked;

        emit CapabilityRevoked(capabilityId);
    }

    function isCapabilityValid(bytes32 capabilityId) public view returns (bool) {
        CapabilityRecord storage record = capabilityById[capabilityId];

        return
            record.exists &&
            record.status == CapabilityStatus.Valid &&
            block.timestamp < record.expiry;
    }

    function isCapabilityUsableFor(
        bytes32 capabilityId,
        string memory policyClass,
        ActionClass actionClass,
        bytes32 contextHash
    ) external view returns (bool) {
        CapabilityRecord storage record = capabilityById[capabilityId];

        return
            isCapabilityValid(capabilityId) &&
            keccak256(bytes(record.policyClass)) == keccak256(bytes(policyClass)) &&
            record.actionClass == actionClass &&
            record.contextHash == contextHash;
    }

    function getCapability(
        bytes32 capabilityId
    )
        external
        view
        returns (
            bool exists,
            bytes32 storedCapabilityId,
            string memory agentId,
            address agentAddress,
            string memory policyClass,
            ActionClass actionClass,
            bytes32 scopeHash,
            bytes32 contextHash,
            uint64 issuedAt,
            uint64 expiry,
            CapabilityStatus status
        )
    {
        CapabilityRecord storage record = capabilityById[capabilityId];

        return (
            record.exists,
            record.capabilityId,
            record.agentId,
            record.agentAddress,
            record.policyClass,
            record.actionClass,
            record.scopeHash,
            record.contextHash,
            record.issuedAt,
            record.expiry,
            record.status
        );
    }

    function expireCapabilityView(bytes32 capabilityId) external view returns (bool) {
        CapabilityRecord storage record = capabilityById[capabilityId];
        require(record.exists, "CapabilityManager: unknown capability");
        return block.timestamp >= record.expiry;
    }

    function isActionClassAllowed(ActionClass actionClass) external pure returns (bool) {
        return
            actionClass == ActionClass.Keep ||
            actionClass == ActionClass.Rekey ||
            actionClass == ActionClass.Rotate ||
            actionClass == ActionClass.Isolate ||
            actionClass == ActionClass.Quarantine;
    }
}
