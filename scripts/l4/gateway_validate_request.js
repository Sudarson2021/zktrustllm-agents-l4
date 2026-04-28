const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

const POLICY = {
  CONTEXT_COLLECT: 0,
  TRUST_EVALUATE: 1,
  POLICY_ENFORCE: 2,
};

const ACTION = {
  KEEP: 0,
  REKEY: 1,
  ROTATE: 2,
  ISOLATE: 3,
  QUARANTINE: 4,
};

const TRUST = {
  TRUSTED: 0,
  DEGRADED: 1,
  SUSPECT: 2,
  RESTRICTED: 3,
  QUARANTINED: 4,
};

function hashUtf8(x) {
  return hre.ethers.keccak256(hre.ethers.toUtf8Bytes(x));
}

async function loadContracts() {
  const depFile = path.join(process.cwd(), "deployments", "l4.localhost.json");
  const dep = JSON.parse(fs.readFileSync(depFile, "utf8"));

  if (!dep.controlPlane) {
    throw new Error("Missing controlPlane deployment block in deployments/l4.localhost.json");
  }

  const agentRegistry = await hre.ethers.getContractAt(
    "contracts/l4/AgentRegistry.sol:AgentRegistry",
    dep.controlPlane.agentRegistry
  );

  const capabilityManager = await hre.ethers.getContractAt(
    "contracts/l4/CapabilityManager.sol:CapabilityManager",
    dep.controlPlane.capabilityManager
  );

  const policyRegistry = await hre.ethers.getContractAt(
    "contracts/l4/PolicyRegistry.sol:PolicyRegistry",
    dep.controlPlane.policyRegistry
  );

  return { agentRegistry, capabilityManager, policyRegistry, dep };
}

async function validateRequest(contracts, req) {
  const { agentRegistry, capabilityManager, policyRegistry } = contracts;

  const active = await agentRegistry.isActiveAgent(req.agentId);
  if (!active) {
    return { ok: false, code: "REJECT_IDENTITY", detail: "agent is not active" };
  }

  const agent = await agentRegistry.getAgent(req.agentId);
  const exists = agent[0];
  const storedAgentAddress = agent[2];
  const role = Number(agent[3]);

  if (!exists) {
    return { ok: false, code: "REJECT_IDENTITY", detail: "agent does not exist" };
  }

  const rolePolicyOk = await policyRegistry.isRoleAllowedForPolicy(role, req.policyClassEnum);
  if (!rolePolicyOk) {
    return { ok: false, code: "REJECT_POLICY_ROLE", detail: "role not allowed for policy class" };
  }

  const capValid = await capabilityManager.isCapabilityValid(req.capabilityId);
  if (!capValid) {
    return { ok: false, code: "REJECT_CAPABILITY", detail: "capability invalid, revoked, or expired" };
  }

  const cap = await capabilityManager.getCapability(req.capabilityId);
  const capExists = cap[0];
  const capAgentId = cap[2];
  const capAgentAddress = cap[3];

  if (!capExists) {
    return { ok: false, code: "REJECT_CAPABILITY", detail: "capability record missing" };
  }

  if (capAgentId !== req.agentId || capAgentAddress.toLowerCase() !== storedAgentAddress.toLowerCase()) {
    return { ok: false, code: "REJECT_CAPABILITY_OWNER", detail: "capability not owned by declared agent" };
  }

  const usable = await capabilityManager.isCapabilityUsableFor(
    req.capabilityId,
    req.policyClassString,
    req.actionClassEnum,
    req.contextHash
  );

  if (!usable) {
    return { ok: false, code: "REJECT_CAPABILITY_SCOPE", detail: "capability does not match policy/action/context" };
  }

  const trustActionOk = await policyRegistry.isActionAllowedForTrustState(
    req.trustStateEnum,
    req.actionClassEnum
  );

  if (!trustActionOk) {
    return { ok: false, code: "REJECT_TRUST_ACTION", detail: "action not allowed for trust state" };
  }

  return { ok: true, code: "ACCEPT", detail: "request accepted" };
}

async function main() {
  const contracts = await loadContracts();

  const positiveReq = {
    label: "positive-case",
    agentId: "policy-lkh-01",
    capabilityId: hashUtf8("cap-policy-01"),
    policyClassString: "policy-enforce",
    policyClassEnum: POLICY.POLICY_ENFORCE,
    actionClassEnum: ACTION.ISOLATE,
    trustStateEnum: TRUST.RESTRICTED,
    contextHash: hashUtf8("ctx-policy"),
  };

  const negativeReq = {
    label: "negative-case",
    agentId: "trust-risk-01",
    capabilityId: hashUtf8("cap-risk-01"),
    policyClassString: "policy-enforce",
    policyClassEnum: POLICY.POLICY_ENFORCE,
    actionClassEnum: ACTION.ISOLATE,
    trustStateEnum: TRUST.RESTRICTED,
    contextHash: hashUtf8("ctx-risk"),
  };

  const positiveRes = await validateRequest(contracts, positiveReq);
  const negativeRes = await validateRequest(contracts, negativeReq);

  console.log("=== Gateway Validation Demo ===");
  console.log();
  console.log("[positive-case]");
  console.log(positiveRes);
  console.log();
  console.log("[negative-case]");
  console.log(negativeRes);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
