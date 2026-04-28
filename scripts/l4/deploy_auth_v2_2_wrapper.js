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

  const Verifier = await hre.ethers.getContractFactory("contracts/l4/generated/AuthV2_2Verifier.sol:Verifier");
  const verifier = await Verifier.deploy();
  await verifier.waitForDeployment();
  const verifierAddress = await verifier.getAddress();

  const Wrapper = await hre.ethers.getContractFactory("contracts/l4/DecisionAttestorAuthV2_2.sol:DecisionAttestorAuthV2_2");
  const wrapper = await Wrapper.deploy(verifierAddress);
  await wrapper.waitForDeployment();
  const wrapperAddress = await wrapper.getAddress();

  dep.authV2_2Groth16Verifier = verifierAddress;
  dep.decisionAttestorAuthV2_2 = wrapperAddress;
  dep.updatedAt = new Date().toISOString();

  fs.mkdirSync(path.dirname(depFile), { recursive: true });
  fs.writeFileSync(depFile, JSON.stringify(dep, null, 2));

  console.log("AuthV2_2Groth16Verifier :", verifierAddress);
  console.log("DecisionAttestorAuthV2_2:", wrapperAddress);
  console.log("Updated ->", depFile);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
