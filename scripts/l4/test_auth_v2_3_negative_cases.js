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
  return {
    a: {
      X: BigInt(p.a[0]),
      Y: BigInt(p.a[1]),
    },
    b: {
      X: [BigInt(p.b[0][0]), BigInt(p.b[0][1])],
      Y: [BigInt(p.b[1][0]), BigInt(p.b[1][1])],
    },
    c: {
      X: BigInt(p.c[0]),
      Y: BigInt(p.c[1]),
    },
  };
}

function cloneInputs(inputs) {
  return inputs.map((x) => BigInt(x));
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

  const verifierAddress = deployment.authV2_3Groth16Verifier;
  const attestorAddress = deployment.decisionAttestorAuthV2_3;

  if (!verifierAddress || !attestorAddress) {
    throw new Error("Missing AUTH_V2.3 verifier or attestor address in deployment file");
  }

  const verifierCode = await ethers.provider.getCode(verifierAddress);
  const attestorCode = await ethers.provider.getCode(attestorAddress);

  if (verifierCode === "0x" || attestorCode === "0x") {
    throw new Error(
      "No AUTH_V2.3 contract code found on localhost. Redeploy AUTH_V2.3 before running this test."
    );
  }

  const verifier = await ethers.getContractAt(
    "contracts/l4/generated/AuthV2_3Verifier.sol:Verifier",
    verifierAddress
  );

  const attestor = await ethers.getContractAt(
    "DecisionAttestorAuthV2_3",
    attestorAddress
  );

  const validInputs = proof.inputs.map((x) => BigInt(x));

  if (validInputs.length !== 12) {
    throw new Error(`Expected 12 verifier inputs, got ${validInputs.length}`);
  }

  const validVerifier = await verifier.verifyTx(proofArg(proof), validInputs);

  let validSubmitStatic = false;
  try {
    const staticDecisionId = await attestor.submitDecision.staticCall(
      payload.agentId,
      proofArg(proof),
      validInputs
    );
    validSubmitStatic = staticDecisionId > 0n;
  } catch (e) {
    validSubmitStatic = false;
  }

  const cases = [];

  async function runCase(name, mutateFn, expectedReason) {
    const tampered = cloneInputs(validInputs);
    mutateFn(tampered);

    let verifierAccepted = null;
    let verifierError = null;

    try {
      verifierAccepted = await verifier.verifyTx(proofArg(proof), tampered);
    } catch (e) {
      verifierAccepted = false;
      verifierError = e.shortMessage || e.message;
    }

    let attestorRejected = false;
    let attestorError = null;

    try {
      await attestor.submitDecision.staticCall(
        payload.agentId,
        proofArg(proof),
        tampered
      );
      attestorRejected = false;
    } catch (e) {
      attestorRejected = true;
      attestorError = e.shortMessage || e.reason || e.message;
    }

    const passed = verifierAccepted === false && attestorRejected === true;

    cases.push({
      name,
      expectedReason,
      verifierAccepted,
      verifierError,
      attestorRejected,
      attestorError,
      passed,
    });
  }

  await runCase(
    "tampered_action_class",
    (x) => { x[3] = 2n; },
    "Changing actionClass breaks the proof-bound public input"
  );

  await runCase(
    "tampered_policy_admissibility_flag",
    (x) => { x[7] = 0n; },
    "Changing policyAdmissibilityFlag breaks the proof-bound public input"
  );

  await runCase(
    "tampered_trust_state",
    (x) => { x[8] = 2n; },
    "Changing trustState breaks the proof-bound public input"
  );

  await runCase(
    "tampered_reference_context_hash",
    (x) => { x[9] = x[9] + 1n; },
    "Changing referenceContextHash breaks the reference-bound proof"
  );

  await runCase(
    "tampered_coordination_session_id",
    (x) => { x[10] = x[10] + 1n; },
    "Changing coordinationSessionId breaks the reference-bound proof"
  );

  await runCase(
    "tampered_proof_output",
    (x) => { x[11] = 0n; },
    "Changing public proof output breaks the verifier relation"
  );

  let wrongLengthRejected = false;
  let wrongLengthError = null;

  try {
    const wrongLengthInputs = validInputs.slice(0, 11);
    await attestor.submitDecision.staticCall(
      payload.agentId,
      proofArg(proof),
      wrongLengthInputs
    );
    wrongLengthRejected = false;
  } catch (e) {
    wrongLengthRejected = true;
    wrongLengthError = e.shortMessage || e.reason || e.message;
  }

  cases.push({
    name: "wrong_input_length",
    expectedReason: "AUTH_V2.3 verifier/attestor requires exactly 12 public inputs",
    verifierAccepted: null,
    verifierError: null,
    attestorRejected: wrongLengthRejected,
    attestorError: wrongLengthError,
    passed: wrongLengthRejected,
  });

  const negativeTotal = cases.length;
  const negativePassed = cases.filter((c) => c.passed).length;
  const rejectionRate = negativeTotal ? negativePassed / negativeTotal : 0;

  const output = {
    experiment: "auth_v2_3_negative_security_tests",
    network,
    authV2_3Groth16Verifier: verifierAddress,
    decisionAttestorAuthV2_3: attestorAddress,
    validPath: {
      verifierAccepted: validVerifier,
      attestorStaticAccepted: validSubmitStatic,
      inputCount: validInputs.length,
      relationVersion: payload.relationVersion,
      proofOutput: validInputs[11].toString(),
    },
    negativeCaseCount: negativeTotal,
    negativeCasesPassed: negativePassed,
    unauthorizedOrTamperedRejectionRate: rejectionRate,
    cases,
  };

  const outDir = path.join(
    __dirname,
    "..",
    "..",
    "results",
    "l4_auth_v2_3_negative"
  );

  fs.mkdirSync(outDir, { recursive: true });

  const outFile = path.join(outDir, "auth_v2_3_negative_summary.json");
  fs.writeFileSync(outFile, JSON.stringify(output, null, 2) + "\n");

  console.log(JSON.stringify(output, null, 2));
  console.log("Saved:", outFile);

  if (!validVerifier || !validSubmitStatic || rejectionRate !== 1) {
    throw new Error("AUTH_V2.3 negative-security test did not fully pass");
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
