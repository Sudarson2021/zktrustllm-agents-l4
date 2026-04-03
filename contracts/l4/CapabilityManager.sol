// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CapabilityManager {
    struct Capability {
        bytes32 capabilityId;
        bytes32 agentKey;
        bytes32 scopeHash;
        string policyClass;
        uint256 issuedAt;
        uint256 expiresAt;
        bool revoked;
    }

    mapping(bytes32 => Capability) private capabilities;
    mapping(address => bool) public admins;

    event CapabilityIssued(bytes32 indexed capabilityId, bytes32 indexed agentKey, string policyClass, uint256 expiresAt);
    event CapabilityRevoked(bytes32 indexed capabilityId);

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

    function issueCapability(
        bytes32 _capabilityId,
        bytes32 _agentKey,
        bytes32 _scopeHash,
        string memory _policyClass,
        uint256 _ttlSeconds
    ) external onlyAdmin {
        require(capabilities[_capabilityId].issuedAt == 0, "capability exists");

        capabilities[_capabilityId] = Capability({
            capabilityId: _capabilityId,
            agentKey: _agentKey,
            scopeHash: _scopeHash,
            policyClass: _policyClass,
            issuedAt: block.timestamp,
            expiresAt: block.timestamp + _ttlSeconds,
            revoked: false
        });

        emit CapabilityIssued(_capabilityId, _agentKey, _policyClass, block.timestamp + _ttlSeconds);
    }

    function revokeCapability(bytes32 _capabilityId) external onlyAdmin {
        require(capabilities[_capabilityId].issuedAt != 0, "not found");
        capabilities[_capabilityId].revoked = true;
        emit CapabilityRevoked(_capabilityId);
    }

    function isValid(bytes32 _capabilityId) external view returns (bool) {
        Capability memory c = capabilities[_capabilityId];
        return c.issuedAt != 0 && !c.revoked && block.timestamp <= c.expiresAt;
    }

    function getCapability(bytes32 _capabilityId) external view returns (Capability memory) {
        return capabilities[_capabilityId];
    }
}
