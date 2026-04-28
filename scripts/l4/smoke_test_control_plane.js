const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const depFile = path.join(process.cwd(), "deployments", "l4.localhost.json");
  const dep = JSON.parse(fs.readFileSync(depFile, "utf8"));
  const addrs = dep.controlPlane;

  const [deployer, a1, a2, a3] = await hre.ethers.getSigners();

  const agentRegistry = await hre.ethers.getContractAt(
    "contracts/l4/AgentRegistry.sol:AgentRegistry",
    addrs.agentRegistry
  );

  const capabilityManager = await hre.ethers.getContractAt(
    "contracts/l4/CapabilityManager.sol:CapabilityManager",
    addrs.capabilityManager
  );

  const policyRegistry = await hre.ethers.getContractAt(
    "contracts/l4/PolicyRegistry.sol:PolicyRegistry",
    addrs.policyRegistry
  );

  // Roles:
  // 0 = EdgeTelemetryAgent
  // 1 = TrustRiskAgent
  // 2 = PolicyLKHAgent
  await (await agentRegistry.registerAgent("edge-telemetry-01", a1.address, 0, hre.ethers.ZeroHash)).wait();
  await (await agentRegistry.registerAgent("trust-risk-01", a2.address, 1, hre.ethers.ZeroHash)).wait();
  await (await agentRegistry.registerAgent("policy-lkh-01", a3.address, 2, hre.ethers.ZeroHash)).wait();

  const now = Math.floor(Date.now() / 1000);
  const expiry = now + 3600;

  // ActionClass:
  // 0 Keep, 1 Rekey, 2 Rotate, 3 Isolate, 4 Quarantine
  await (await capabilityManager.issueCapability(
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("cap-edge-01")),
    "edge-telemetry-01",
    a1.address,
    "context-collect",
    0,
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("scope-edge")),
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("ctx-edge")),
    expiry
  )).wait();

  await (await capabilityManager.issueCapability(
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("cap-risk-01")),
    "trust-risk-01",
    a2.address,
    "trust-evaluate",
    2,
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("scope-risk")),
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("ctx-risk")),
    expiry
  )).wait();

  await (await capabilityManager.issueCapability(
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("cap-policy-01")),
    "policy-lkh-01",
    a3.address,
    "policy-enforce",
    3,
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("scope-policy")),
    hre.ethers.keccak256(hre.ethers.toUtf8Bytes("ctx-policy")),
    expiry
  )).wait();

  console.log("edge active ->", await agentRegistry.isActiveAgent("edge-telemetry-01"));
  console.log("risk active ->", await agentRegistry.isActiveAgent("trust-risk-01"));
  console.log("policy active ->", await agentRegistry.isActiveAgent("policy-lkh-01"));

  console.log(
    "role EdgeTelemetryAgent allowed for ContextCollect ->",
    await policyRegistry.isRoleAllowedForPolicy(0, 0)
  );
  console.log(
    "role TrustRiskAgent allowed for TrustEvaluate ->",
    await policyRegistry.isRoleAllowedForPolicy(1, 1)
  );
  console.log(
    "role PolicyLKHAgent allowed for PolicyEnforce ->",
    await policyRegistry.isRoleAllowedForPolicy(2, 2)
  );

  console.log(
    "Restricted allows Isolate ->",
    await policyRegistry.isActionAllowedForTrustState(3, 3)
  );
  console.log(
    "Quarantined allows Quarantine ->",
    await policyRegistry.isActionAllowedForTrustState(4, 4)
  );

  const capEdge = hre.ethers.keccak256(hre.ethers.toUtf8Bytes("cap-edge-01"));
  console.log("cap-edge valid ->", await capabilityManager.isCapabilityValid(capEdge));
}
main().catch((err) => {
  console.error(err);
  process.exit(1);
});
