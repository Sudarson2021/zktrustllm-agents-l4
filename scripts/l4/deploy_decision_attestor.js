const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const network = hre.network.name;
  const depFile = path.join(process.cwd(), "deployments", `l4.${network}.json`);

  if (!fs.existsSync(depFile)) {
    throw new Error(`Missing deployment file: ${depFile}`);
  }

  const dep = JSON.parse(fs.readFileSync(depFile, "utf8"));

  const DecisionAttestor = await hre.ethers.getContractFactory("DecisionAttestor");
  const attestor = await DecisionAttestor.deploy(dep.agentRegistry, dep.capabilityManager);
  await attestor.waitForDeployment();

  const attestorAddress = await attestor.getAddress();
  dep.decisionAttestor = attestorAddress;
  dep.updatedAt = new Date().toISOString();

  fs.writeFileSync(depFile, JSON.stringify(dep, null, 2));

  console.log("DecisionAttestor :", attestorAddress);
  console.log("Updated ->", depFile);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
