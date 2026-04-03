const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const network = hre.network.name;

  console.log("Deploying L4 contracts with:", deployer.address);
  console.log("Network:", network);

  const AgentRegistry = await hre.ethers.getContractFactory("AgentRegistry");
  const agentRegistry = await AgentRegistry.deploy();
  await agentRegistry.waitForDeployment();
  const agentRegistryAddress = await agentRegistry.getAddress();

  const CapabilityManager = await hre.ethers.getContractFactory("CapabilityManager");
  const capabilityManager = await CapabilityManager.deploy();
  await capabilityManager.waitForDeployment();
  const capabilityManagerAddress = await capabilityManager.getAddress();

  const outDir = path.join(process.cwd(), "deployments");
  fs.mkdirSync(outDir, { recursive: true });

  const out = {
    network,
    deployedAt: new Date().toISOString(),
    deployer: deployer.address,
    agentRegistry: agentRegistryAddress,
    capabilityManager: capabilityManagerAddress
  };

  const outFile = path.join(outDir, `l4.${network}.json`);
  fs.writeFileSync(outFile, JSON.stringify(out, null, 2));

  console.log("\nL4 deployment complete");
  console.log("AgentRegistry     :", agentRegistryAddress);
  console.log("CapabilityManager :", capabilityManagerAddress);
  console.log("Saved ->", outFile);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
