const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

function loadJson(p) {
  if (!fs.existsSync(p)) {
    throw new Error(`Missing file: ${p}`);
  }
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function proofArg(proofJson) {
  const p = proofJson.proof;
  return [
    [p.a[0], p.a[1]],
    [[p.b[0][0], p.b[0][1]], [p.b[1][0], p.b[1][1]]],
    [p.c[0], p.c[1]]
  ];
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

  const payloadPath = path.join(
    __dirname,
    "..",
    "..",
    "runtime_artifacts",
    "l4",
    "auth_v2_3",
    "proof_payload.auth_v2_3.frozen.json"
  );

  const proofPath = path.join(
    __dirname,
    "..",
    "..",
    "runtime_artifacts",
    "l4",
    "auth_v2_3",
    "proof.frozen.json"
  );

  const deployment = loadJson(deploymentPath);
  const payload = loadJson(payloadPath);
  const proof = loadJson(proofPath);

  const attestorAddress = deployment.decisionAttestorAuthV2_3;
  if (!attestorAddress) {
    throw new Error("Missing decisionAttestorAuthV2_3 in deployment file");
  }

  const attestor = await ethers.getContractAt(
    "DecisionAttestorAuthV2_3",
    attestorAddress
  );

  const inputs = payload.publicInputsOrder.map((key) =>
    BigInt(payload.publicInputs[key])
  );

  if (inputs.length !== 11) {
    throw new Error(`Expected 11 AUTH_V2.3 public inputs, got ${inputs.length}`);
  }

  console.log("AUTH_V2.3 Verifier:", deployment.authV2_3Groth16Verifier);
  console.log("AUTH_V2.3 Attestor:", attestorAddress);
  console.log("Input count:", inputs.length);

  const staticOk = await attestor.submitDecision.staticCall(
    payload.agentId,
    proofArg(proof),
    inputs
  );

  console.log("Preflight submitDecision() ->", staticOk.toString());

  const tx = await attestor.submitDecision(
    payload.agentId,
    proofArg(proof),
    inputs
  );

  const receipt = await tx.wait();

  const decisionCount = await attestor.decisionCount();
  const decision = await attestor.getDecision(decisionCount);

  const out = {
    network,
    decisionAttestorAuthV2_3: attestorAddress,
    authV2_3Groth16Verifier: deployment.authV2_3Groth16Verifier,
    txHash: receipt.hash,
    gasUsed: receipt.gasUsed.toString(),
    decisionId: decisionCount.toString(),
    agentId: decision[0],
    agentKey: decision[1].toString(),
    capabilityId: decision[2].toString(),
    policyClassHash: decision[3].toString(),
    actionClass: decision[4].toString(),
    contextHash: decision[5].toString(),
    traceCommitment: decision[6].toString(),
    expiryBucket: decision[7].toString(),
    policyAdmissibilityFlag: decision[8].toString(),
    trustState: decision[9].toString(),
    referenceContextHash: decision[10].toString(),
    coordinationSessionId: decision[11].toString(),
    timestamp: decision[12].toString(),
    relationVersion: payload.relationVersion,
    referenceBinding: payload.referenceBinding
  };

  const outDir = path.join(
    __dirname,
    "..",
    "..",
    "results",
    "l4_auth_v2_3"
  );

  fs.mkdirSync(outDir, { recursive: true });

  const outFile = path.join(outDir, "reference_bound_decision.json");
  fs.writeFileSync(outFile, JSON.stringify(out, null, 2) + "\n");

  console.log(JSON.stringify(out, null, 2));
  console.log("Saved:", outFile);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
