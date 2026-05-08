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

  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));

  const registryAddress = deployment.a2aReferenceRegistry;
  const expectedAttestor = deployment.decisionAttestorAuthV2_2;

  if (!registryAddress) {
    throw new Error("Missing a2aReferenceRegistry in deployment file");
  }

  if (!expectedAttestor) {
    throw new Error("Missing decisionAttestorAuthV2_2 in deployment file");
  }

  const registry = await ethers.getContractAt(
    "A2AReferenceRegistry",
    registryAddress
  );

  const actualAttestor = await registry.decisionAttestor();
  const referenceCount = await registry.referenceCount();

  console.log("A2AReferenceRegistry:", registryAddress);
  console.log("Expected AUTH_V2.2 :", expectedAttestor);
  console.log("Actual AUTH_V2.2   :", actualAttestor);
  console.log("Reference count    :", referenceCount.toString());

  if (actualAttestor.toLowerCase() !== expectedAttestor.toLowerCase()) {
    throw new Error("A2A registry is not connected to expected AUTH_V2.2 attestor");
  }

  console.log("OK: A2A registry is correctly connected to AUTH_V2.2");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
