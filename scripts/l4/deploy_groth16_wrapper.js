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

  const verifierFQN = "contracts/l4/generated/AuthV1Verifier.sol:Verifier";
  const wrapperFQN = "contracts/l4/DecisionAttestorGroth16.sol:DecisionAttestorGroth16";

  const AuthV1Verifier = await hre.ethers.getContractFactory(verifierFQN);
  const verifier = await AuthV1Verifier.deploy();
  await verifier.waitForDeployment();
  const verifierAddress = await verifier.getAddress();

  const DecisionAttestorGroth16 = await hre.ethers.getContractFactory(wrapperFQN);
  const wrapper = await DecisionAttestorGroth16.deploy(verifierAddress);
  await wrapper.waitForDeployment();
  const wrapperAddress = await wrapper.getAddress();

  dep.authV1Groth16Verifier = verifierAddress;
  dep.decisionAttestorGroth16 = wrapperAddress;

  fs.mkdirSync(path.dirname(depFile), { recursive: true });
  fs.writeFileSync(depFile, JSON.stringify(dep, null, 2));

  console.log("AuthV1Groth16Verifier  :", verifierAddress);
  console.log("DecisionAttestorGroth16:", wrapperAddress);
  console.log("Updated ->", depFile);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
