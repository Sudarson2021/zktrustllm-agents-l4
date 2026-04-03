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

  const MockAuthorizationVerifier = await hre.ethers.getContractFactory("MockAuthorizationVerifier");
  const verifier = await MockAuthorizationVerifier.deploy();
  await verifier.waitForDeployment();
  const verifierAddress = await verifier.getAddress();

  const DecisionAttestorZK = await hre.ethers.getContractFactory("DecisionAttestorZK");
  const zkAttestor = await DecisionAttestorZK.deploy(
    dep.agentRegistry,
    dep.capabilityManager,
    verifierAddress
  );
  await zkAttestor.waitForDeployment();
  const zkAttestorAddress = await zkAttestor.getAddress();

  dep.mockAuthorizationVerifier = verifierAddress;
  dep.decisionAttestorZK = zkAttestorAddress;
  dep.updatedAt = new Date().toISOString();

  fs.writeFileSync(depFile, JSON.stringify(dep, null, 2));

  console.log("MockAuthorizationVerifier :", verifierAddress);
  console.log("DecisionAttestorZK       :", zkAttestorAddress);
  console.log("Updated ->", depFile);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
