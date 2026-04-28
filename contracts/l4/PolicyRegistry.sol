// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./AgentRegistry.sol";
import "./CapabilityManager.sol";

contract PolicyRegistry {
    enum PolicyClass {
        ContextCollect,
        TrustEvaluate,
        PolicyEnforce
    }

    enum TrustState {
        Trusted,
        Degraded,
        Suspect,
        Restricted,
        Quarantined
    }

    address public owner;

    mapping(uint8 => mapping(uint8 => bool)) private roleAllowedForPolicy;
    mapping(uint8 => mapping(uint8 => bool)) private actionAllowedForTrustState;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event RolePolicyRuleSet(uint8 indexed role, uint8 indexed policyClass, bool allowed);
    event TrustActionRuleSet(uint8 indexed trustState, uint8 indexed actionClass, bool allowed);

    modifier onlyOwner() {
        require(msg.sender == owner, "PolicyRegistry: not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);

        _seedInitialRolePolicyRules();
        _seedInitialTrustActionRules();
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "PolicyRegistry: zero owner");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }

    function setRolePolicyRule(
        AgentRegistry.Role role,
        PolicyClass policyClass,
        bool allowed
    ) external onlyOwner {
        roleAllowedForPolicy[uint8(role)][uint8(policyClass)] = allowed;
        emit RolePolicyRuleSet(uint8(role), uint8(policyClass), allowed);
    }

    function setTrustActionRule(
        TrustState trustState,
        CapabilityManager.ActionClass actionClass,
        bool allowed
    ) external onlyOwner {
        actionAllowedForTrustState[uint8(trustState)][uint8(actionClass)] = allowed;
        emit TrustActionRuleSet(uint8(trustState), uint8(actionClass), allowed);
    }

    function isRoleAllowedForPolicy(
        AgentRegistry.Role role,
        PolicyClass policyClass
    ) external view returns (bool) {
        return roleAllowedForPolicy[uint8(role)][uint8(policyClass)];
    }

    function isActionAllowedForTrustState(
        TrustState trustState,
        CapabilityManager.ActionClass actionClass
    ) external view returns (bool) {
        return actionAllowedForTrustState[uint8(trustState)][uint8(actionClass)];
    }

    function isPolicyClassAllowedForAgentRole(
        AgentRegistry.Role role,
        PolicyClass policyClass
    ) external view returns (bool) {
        return roleAllowedForPolicy[uint8(role)][uint8(policyClass)];
    }

    function _seedInitialRolePolicyRules() internal {
        roleAllowedForPolicy[uint8(AgentRegistry.Role.EdgeTelemetryAgent)][uint8(PolicyClass.ContextCollect)] = true;
        roleAllowedForPolicy[uint8(AgentRegistry.Role.TrustRiskAgent)][uint8(PolicyClass.TrustEvaluate)] = true;
        roleAllowedForPolicy[uint8(AgentRegistry.Role.PolicyLKHAgent)][uint8(PolicyClass.PolicyEnforce)] = true;

        emit RolePolicyRuleSet(uint8(AgentRegistry.Role.EdgeTelemetryAgent), uint8(PolicyClass.ContextCollect), true);
        emit RolePolicyRuleSet(uint8(AgentRegistry.Role.TrustRiskAgent), uint8(PolicyClass.TrustEvaluate), true);
        emit RolePolicyRuleSet(uint8(AgentRegistry.Role.PolicyLKHAgent), uint8(PolicyClass.PolicyEnforce), true);
    }

    function _seedInitialTrustActionRules() internal {
        // Trusted
        actionAllowedForTrustState[uint8(TrustState.Trusted)][uint8(CapabilityManager.ActionClass.Keep)] = true;
        actionAllowedForTrustState[uint8(TrustState.Trusted)][uint8(CapabilityManager.ActionClass.Rotate)] = true;

        // Degraded
        actionAllowedForTrustState[uint8(TrustState.Degraded)][uint8(CapabilityManager.ActionClass.Keep)] = true;
        actionAllowedForTrustState[uint8(TrustState.Degraded)][uint8(CapabilityManager.ActionClass.Rekey)] = true;
        actionAllowedForTrustState[uint8(TrustState.Degraded)][uint8(CapabilityManager.ActionClass.Rotate)] = true;

        // Suspect
        actionAllowedForTrustState[uint8(TrustState.Suspect)][uint8(CapabilityManager.ActionClass.Rekey)] = true;
        actionAllowedForTrustState[uint8(TrustState.Suspect)][uint8(CapabilityManager.ActionClass.Rotate)] = true;
        actionAllowedForTrustState[uint8(TrustState.Suspect)][uint8(CapabilityManager.ActionClass.Isolate)] = true;

        // Restricted
        actionAllowedForTrustState[uint8(TrustState.Restricted)][uint8(CapabilityManager.ActionClass.Rekey)] = true;
        actionAllowedForTrustState[uint8(TrustState.Restricted)][uint8(CapabilityManager.ActionClass.Rotate)] = true;
        actionAllowedForTrustState[uint8(TrustState.Restricted)][uint8(CapabilityManager.ActionClass.Isolate)] = true;
        actionAllowedForTrustState[uint8(TrustState.Restricted)][uint8(CapabilityManager.ActionClass.Quarantine)] = true;

        // Quarantined
        actionAllowedForTrustState[uint8(TrustState.Quarantined)][uint8(CapabilityManager.ActionClass.Quarantine)] = true;

        emit TrustActionRuleSet(uint8(TrustState.Trusted), uint8(CapabilityManager.ActionClass.Keep), true);
        emit TrustActionRuleSet(uint8(TrustState.Trusted), uint8(CapabilityManager.ActionClass.Rotate), true);

        emit TrustActionRuleSet(uint8(TrustState.Degraded), uint8(CapabilityManager.ActionClass.Keep), true);
        emit TrustActionRuleSet(uint8(TrustState.Degraded), uint8(CapabilityManager.ActionClass.Rekey), true);
        emit TrustActionRuleSet(uint8(TrustState.Degraded), uint8(CapabilityManager.ActionClass.Rotate), true);

        emit TrustActionRuleSet(uint8(TrustState.Suspect), uint8(CapabilityManager.ActionClass.Rekey), true);
        emit TrustActionRuleSet(uint8(TrustState.Suspect), uint8(CapabilityManager.ActionClass.Rotate), true);
        emit TrustActionRuleSet(uint8(TrustState.Suspect), uint8(CapabilityManager.ActionClass.Isolate), true);

        emit TrustActionRuleSet(uint8(TrustState.Restricted), uint8(CapabilityManager.ActionClass.Rekey), true);
        emit TrustActionRuleSet(uint8(TrustState.Restricted), uint8(CapabilityManager.ActionClass.Rotate), true);
        emit TrustActionRuleSet(uint8(TrustState.Restricted), uint8(CapabilityManager.ActionClass.Isolate), true);
        emit TrustActionRuleSet(uint8(TrustState.Restricted), uint8(CapabilityManager.ActionClass.Quarantine), true);

        emit TrustActionRuleSet(uint8(TrustState.Quarantined), uint8(CapabilityManager.ActionClass.Quarantine), true);
    }
}
