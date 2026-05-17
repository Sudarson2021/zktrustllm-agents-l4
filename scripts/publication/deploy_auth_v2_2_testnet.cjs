const hre = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  console.log("Network:", hre.network.name);
  console.log("Deployer:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Balance:", hre.ethers.formatEther(balance), "ETH");

  const Verifier = await hre.ethers.getContractFactory(
    "contracts/l4/generated/AuthV2_2Verifier.sol:Verifier"
  );
  const verifier = await Verifier.deploy();
  await verifier.waitForDeployment();

  const verifierAddress = await verifier.getAddress();
  const verifierReceipt = await verifier.deploymentTransaction().wait();

  console.log("Verifier:", verifierAddress);
  console.log("Verifier deploy tx:", verifier.deploymentTransaction().hash);
  console.log("Verifier deploy gas:", verifierReceipt.gasUsed.toString());

  const Attestor = await hre.ethers.getContractFactory("DecisionAttestorAuthV2_2");
  const attestor = await Attestor.deploy(verifierAddress);
  await attestor.waitForDeployment();

  const attestorAddress = await attestor.getAddress();
  const attestorReceipt = await attestor.deploymentTransaction().wait();

  console.log("Attestor:", attestorAddress);
  console.log("Attestor deploy tx:", attestor.deploymentTransaction().hash);
  console.log("Attestor deploy gas:", attestorReceipt.gasUsed.toString());

  const submitterRole = await attestor.SUBMITTER_ROLE();
  const hasRole = await attestor.hasRole(submitterRole, deployer.address);

  const out = {
    network: hre.network.name,
    deployer: deployer.address,
    verifierAddress,
    verifierDeployTx: verifier.deploymentTransaction().hash,
    verifierDeployGas: verifierReceipt.gasUsed.toString(),
    attestorAddress,
    attestorDeployTx: attestor.deploymentTransaction().hash,
    attestorDeployGas: attestorReceipt.gasUsed.toString(),
    submitterRole,
    deployerHasSubmitterRole: hasRole,
    generatedAt: new Date().toISOString()
  };

  fs.mkdirSync("artifacts/publication/testnet", { recursive: true });
  fs.writeFileSync(
    `artifacts/publication/testnet/auth_v2_2_${hre.network.name}.json`,
    JSON.stringify(out, null, 2)
  );

  console.log(JSON.stringify(out, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
