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

  let deployment = {};
  if (fs.existsSync(deploymentPath)) {
    deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  }

  const Verifier = await ethers.getContractFactory(
    "contracts/l4/generated/AuthV2_3Verifier.sol:Verifier"
  );
  const verifier = await Verifier.deploy();
  await verifier.waitForDeployment();
  const verifierAddress = await verifier.getAddress();

  const Attestor = await ethers.getContractFactory("DecisionAttestorAuthV2_3");
  const attestor = await Attestor.deploy(verifierAddress);
  await attestor.waitForDeployment();
  const attestorAddress = await attestor.getAddress();

  deployment.authV2_3Groth16Verifier = verifierAddress;
  deployment.decisionAttestorAuthV2_3 = attestorAddress;
  deployment.authV2_3Network = network;
  deployment.authV2_3UpdatedAt = new Date().toISOString();

  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2) + "\n");

  console.log("AuthV2_3Groth16Verifier :", verifierAddress);
  console.log("DecisionAttestorAuthV2_3:", attestorAddress);
  console.log("Updated ->", deploymentPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
