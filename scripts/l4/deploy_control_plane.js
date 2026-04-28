const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const network = hre.network.name;
  const depFile = path.join(process.cwd(), "deployments", `l4.${network}.json`);

  let dep = {};
  if (fs.existsSync(depFile)) {
    dep = JSON.parse(fs.readFileSync(depFile, "utf8"));
  }

  const AgentRegistry = await hre.ethers.getContractFactory("contracts/l4/AgentRegistry.sol:AgentRegistry");
  const agentRegistry = await AgentRegistry.deploy();
  await agentRegistry.waitForDeployment();
  const agentRegistryAddress = await agentRegistry.getAddress();

  const CapabilityManager = await hre.ethers.getContractFactory("contracts/l4/CapabilityManager.sol:CapabilityManager");
  const capabilityManager = await CapabilityManager.deploy(agentRegistryAddress);
  await capabilityManager.waitForDeployment();
  const capabilityManagerAddress = await capabilityManager.getAddress();

  const PolicyRegistry = await hre.ethers.getContractFactory("contracts/l4/PolicyRegistry.sol:PolicyRegistry");
  const policyRegistry = await PolicyRegistry.deploy();
  await policyRegistry.waitForDeployment();
  const policyRegistryAddress = await policyRegistry.getAddress();

  dep.controlPlane = {
    ...(dep.controlPlane || {}),
    agentRegistry: agentRegistryAddress,
    capabilityManager: capabilityManagerAddress,
    policyRegistry: policyRegistryAddress,
    updatedAt: new Date().toISOString()
  };

  fs.mkdirSync(path.dirname(depFile), { recursive: true });
  fs.writeFileSync(depFile, JSON.stringify(dep, null, 2));

  console.log("AgentRegistry   :", agentRegistryAddress);
  console.log("CapabilityManager:", capabilityManagerAddress);
  console.log("PolicyRegistry  :", policyRegistryAddress);
  console.log("Updated ->", depFile);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
