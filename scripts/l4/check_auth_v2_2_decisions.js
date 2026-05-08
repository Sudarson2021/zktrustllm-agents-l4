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

  const attestorAddress = deployment.decisionAttestorAuthV2_2;

  if (!attestorAddress) {
    throw new Error("Missing decisionAttestorAuthV2_2 in deployment file");
  }

  const attestor = await ethers.getContractAt(
    "DecisionAttestorAuthV2_2",
    attestorAddress
  );

  const count = await attestor.decisionCount();

  console.log("DecisionAttestorAuthV2_2:", attestorAddress);
  console.log("AUTH_V2.2 decisionCount:", count.toString());

  if (count > 0n) {
    const decision = await attestor.getDecision(count);
    console.log("Latest decision:");
    console.log("  decisionId          :", count.toString());
    console.log("  agentId             :", decision[0]);
    console.log("  capabilityId        :", decision[1]);
    console.log("  policyClassHash     :", decision[2]);
    console.log("  actionClass         :", decision[3].toString());
    console.log("  contextHash         :", decision[4]);
    console.log("  traceCommitment     :", decision[5]);
    console.log("  expiryBucket        :", decision[6].toString());
    console.log("  admissibilityFlag   :", decision[7].toString());
    console.log("  trustState          :", decision[8].toString());
    console.log("  timestamp           :", decision[9].toString());
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
