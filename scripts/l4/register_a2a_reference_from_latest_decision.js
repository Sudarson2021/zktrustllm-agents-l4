const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

function keccakText(text) {
  return hre.ethers.keccak256(hre.ethers.toUtf8Bytes(text));
}

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
  const registryAddress = deployment.a2aReferenceRegistry;

  if (!attestorAddress) {
    throw new Error("Missing decisionAttestorAuthV2_2 in deployment file");
  }

  if (!registryAddress) {
    throw new Error("Missing a2aReferenceRegistry in deployment file");
  }

  const attestor = await ethers.getContractAt(
    "DecisionAttestorAuthV2_2",
    attestorAddress
  );

  const registry = await ethers.getContractAt(
    "A2AReferenceRegistry",
    registryAddress
  );

  const count = await attestor.decisionCount();

  if (count === 0n) {
    throw new Error("No AUTH_V2.2 decisions found");
  }

  const sourceDecisionId = count;
  const decision = await attestor.getDecision(sourceDecisionId);

  const senderAgentId = decision[0];
  const receiverAgentId = "policy-lkh-agent-01";

  const capabilityId = decision[1];
  const policyClassHash = decision[2];
  const actionClass = decision[3];
  const contextHash = decision[4];
  const traceCommitment = decision[5];
  const expiryBucket = decision[6];

  const cidHash = keccakText("ipfs://bafy-l4-a2a-reference-demo");
  const proofRef = keccakText(
    `auth-v2-2-proof-ref-decision-${sourceDecisionId.toString()}`
  );

  const latestBlock = await ethers.provider.getBlock("latest");
  const expiresAt = BigInt(latestBlock.timestamp + 3600);

  const tx = await registry.registerReference(
    senderAgentId,
    receiverAgentId,
    sourceDecisionId,
    capabilityId,
    policyClassHash,
    actionClass,
    contextHash,
    traceCommitment,
    cidHash,
    proofRef,
    expiryBucket,
    expiresAt
  );

  const receipt = await tx.wait();

  const referenceId = await registry.referenceCount();
  const record = await registry.getReference(referenceId);
  const valid = await registry.isReferenceValid(referenceId);

  const out = {
    network,
    a2aReferenceRegistry: registryAddress,
    decisionAttestorAuthV2_2: attestorAddress,
    sourceDecisionId: sourceDecisionId.toString(),
    referenceId: referenceId.toString(),
    txHash: receipt.hash,
    gasUsed: receipt.gasUsed.toString(),
    valid,
    senderAgentId,
    receiverAgentId,
    sourceBlockNumber: record[4].toString(),
    capabilityId,
    policyClassHash,
    actionClass: actionClass.toString(),
    contextHash,
    traceCommitment,
    cidHash,
    proofRef,
    expiryBucket: expiryBucket.toString(),
    expiresAt: expiresAt.toString()
  };

  const outDir = path.join(
    __dirname,
    "..",
    "..",
    "artifacts",
    "out",
    "l4_a2a_reference"
  );

  fs.mkdirSync(outDir, { recursive: true });

  const outFile = path.join(outDir, "a2a_reference_latest_decision.json");
  fs.writeFileSync(outFile, JSON.stringify(out, null, 2) + "\n");

  console.log(JSON.stringify(out, null, 2));
  console.log("Saved:", outFile);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
