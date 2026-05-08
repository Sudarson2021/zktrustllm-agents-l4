const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const { ethers } = hre;
  const network = hre.network.name;

  const deploymentPath = path.join(
    __dirname,
    "..",
    "..",
    "deployments",
    `l4.${network}.json`
  );

  if (!fs.existsSync(deploymentPath)) {
    throw new Error(`Missing deployment file: ${deploymentPath}`);
  }

  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));

  const decisionAttestorAuthV2_2 =
    deployment.decisionAttestorAuthV2_2 ||
    deployment.DecisionAttestorAuthV2_2 ||
    deployment.contracts?.decisionAttestorAuthV2_2?.address ||
    deployment.contracts?.DecisionAttestorAuthV2_2?.address;

  if (!decisionAttestorAuthV2_2) {
    console.error("Available deployment keys:", Object.keys(deployment));
    throw new Error(
      "Missing decisionAttestorAuthV2_2 address in deployments/l4.localhost.json"
    );
  }

  const code = await ethers.provider.getCode(decisionAttestorAuthV2_2);
  if (code === "0x") {
    throw new Error(
      `No contract code found at decisionAttestorAuthV2_2 address: ${decisionAttestorAuthV2_2}. ` +
      "Start the same localhost deployment chain or redeploy the L4 stack first."
    );
  }

  const A2AReferenceRegistry = await ethers.getContractFactory(
    "A2AReferenceRegistry"
  );

  const registry = await A2AReferenceRegistry.deploy(decisionAttestorAuthV2_2);
  await registry.waitForDeployment();

  const registryAddress = await registry.getAddress();

  deployment.a2aReferenceRegistry = registryAddress;
  deployment.a2aReferenceRegistrySourceAttestor = decisionAttestorAuthV2_2;
  deployment.a2aReferenceRegistryNetwork = network;
  deployment.a2aReferenceRegistryUpdatedAt = new Date().toISOString();

  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2) + "\n");

  console.log("A2AReferenceRegistry deployed:", registryAddress);
  console.log("Source AUTH_V2.2 attestor:", decisionAttestorAuthV2_2);
  console.log("Updated deployment file:", deploymentPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
