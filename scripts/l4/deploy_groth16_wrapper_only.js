const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const network = hre.network.name;
  const depFile = path.join(process.cwd(), "deployments", `l4.${network}.json`);
  const dep = JSON.parse(fs.readFileSync(depFile, "utf8"));

  if (!dep.authV1Groth16Verifier) {
    throw new Error("Missing authV1Groth16Verifier in deployment file");
  }

  const wrapperFQN = "contracts/l4/DecisionAttestorGroth16.sol:DecisionAttestorGroth16";
  const Wrapper = await hre.ethers.getContractFactory(wrapperFQN);
  const wrapper = await Wrapper.deploy(dep.authV1Groth16Verifier);
  await wrapper.waitForDeployment();

  const wrapperAddress = await wrapper.getAddress();
  dep.decisionAttestorGroth16 = wrapperAddress;

  fs.writeFileSync(depFile, JSON.stringify(dep, null, 2));
  console.log("Reused verifier        :", dep.authV1Groth16Verifier);
  console.log("DecisionAttestorGroth16:", wrapperAddress);
  console.log("Updated ->", depFile);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
