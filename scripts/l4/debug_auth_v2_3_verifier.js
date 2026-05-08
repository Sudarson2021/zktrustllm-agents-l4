const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

function loadJson(p) {
  if (!fs.existsSync(p)) {
    throw new Error(`Missing file: ${p}`);
  }
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function proofArgStandard(proofJson) {
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

function proofArgSwappedB(proofJson) {
  const p = proofJson.proof;
  return {
    a: {
      X: BigInt(p.a[0]),
      Y: BigInt(p.a[1]),
    },
    b: {
      X: [BigInt(p.b[0][1]), BigInt(p.b[0][0])],
      Y: [BigInt(p.b[1][1]), BigInt(p.b[1][0])],
    },
    c: {
      X: BigInt(p.c[0]),
      Y: BigInt(p.c[1]),
    },
  };
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
  if (!verifierAddress) {
    throw new Error("Missing authV2_3Groth16Verifier in deployment file");
  }

  const verifier = await ethers.getContractAt(
    "contracts/l4/generated/AuthV2_3Verifier.sol:Verifier",
    verifierAddress
  );

  const inputsFromPayload = payload.publicInputsOrder.map((key) =>
    BigInt(payload.publicInputs[key])
  );

  const inputsFromProof = proof.inputs.map((x) => BigInt(x));

  console.log("Verifier:", verifierAddress);
  console.log("Payload input count:", inputsFromPayload.length);
  console.log("Proof input count  :", inputsFromProof.length);

  console.log("\nPayload public input order:");
  payload.publicInputsOrder.forEach((key, i) => {
    console.log(`${i}: ${key} = ${inputsFromPayload[i].toString()}`);
  });

  console.log("\nCompare payload inputs with proof.inputs:");
  let allMatch = true;
  for (let i = 0; i < inputsFromPayload.length; i++) {
    const match = inputsFromPayload[i] === inputsFromProof[i];
    if (!match) allMatch = false;
    console.log(`${i}: match=${match} payload=${inputsFromPayload[i]} proof=${inputsFromProof[i]}`);
  }
  console.log("All public inputs match:", allMatch);

  try {
    const okStandardPayload = await verifier.verifyTx(
      proofArgStandard(proof),
      inputsFromPayload
    );
    console.log("\nverifyTx standard proof + payload inputs:", okStandardPayload);
  } catch (e) {
    console.log("\nverifyTx standard proof + payload inputs reverted:");
    console.log(e.shortMessage || e.message);
  }

  try {
    const okStandardProofInputs = await verifier.verifyTx(
      proofArgStandard(proof),
      inputsFromProof
    );
    console.log("verifyTx standard proof + proof.inputs:", okStandardProofInputs);
  } catch (e) {
    console.log("verifyTx standard proof + proof.inputs reverted:");
    console.log(e.shortMessage || e.message);
  }

  try {
    const okSwappedPayload = await verifier.verifyTx(
      proofArgSwappedB(proof),
      inputsFromPayload
    );
    console.log("verifyTx swapped-b proof + payload inputs:", okSwappedPayload);
  } catch (e) {
    console.log("verifyTx swapped-b proof + payload inputs reverted:");
    console.log(e.shortMessage || e.message);
  }

  try {
    const okSwappedProofInputs = await verifier.verifyTx(
      proofArgSwappedB(proof),
      inputsFromProof
    );
    console.log("verifyTx swapped-b proof + proof.inputs:", okSwappedProofInputs);
  } catch (e) {
    console.log("verifyTx swapped-b proof + proof.inputs reverted:");
    console.log(e.shortMessage || e.message);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
