const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const root = process.cwd();
  const artifactPath = path.join(
    root,
    "artifacts",
    "contracts",
    "l4",
    "generated",
    "AuthV2_2Verifier.sol",
    "Verifier.json"
  );

  if (!fs.existsSync(artifactPath)) {
    throw new Error(`Missing verifier artifact: ${artifactPath}. Run npx hardhat compile first.`);
  }

  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  const [deployer] = await hre.ethers.getSigners();

  const factory = new hre.ethers.ContractFactory(
    artifact.abi,
    artifact.bytecode,
    deployer
  );

  const verifier = await factory.deploy();
  await verifier.waitForDeployment();

  const address = await verifier.getAddress();

  const deploymentPath = path.join(root, "deployments", "l4.localhost.json");
  let deployment = {};
  if (fs.existsSync(deploymentPath)) {
    deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  }

  deployment.network = "localhost";
  deployment.updatedAt = new Date().toISOString();
  deployment.authV2_2Groth16Verifier = address;

  fs.mkdirSync(path.dirname(deploymentPath), { recursive: true });
  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2) + "\n");

  const outDir = path.join(root, "artifacts", "out", "paper_258", "zk_timing");
  fs.mkdirSync(outDir, { recursive: true });

  const manifest = {
    status: "DEPLOYED",
    network: "localhost",
    contract: "AuthV2_2Verifier",
    address,
    deployer: await deployer.getAddress(),
    blockNumber: await hre.ethers.provider.getBlockNumber(),
    artifactPath,
    deploymentPath,
    timestampUtc: new Date().toISOString(),
    claimBoundary:
      "Local ephemeral Hardhat deployment used only for AUTH_V2.2 verifier timing and functional smoke validation."
  };

  fs.writeFileSync(
    path.join(outDir, "auth_v2_2_local_deploy_manifest.json"),
    JSON.stringify(manifest, null, 2) + "\n"
  );

  console.log(JSON.stringify(manifest, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
