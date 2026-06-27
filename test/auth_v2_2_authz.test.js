const { expect } = require("chai");
const { ethers } = require("hardhat");

async function deployAuthV22Fixture() {
  const [admin, outsider, submitter] = await ethers.getSigners();

  const Verifier = await ethers.getContractFactory(
    "contracts/l4/generated/AuthV2_2Verifier.sol:Verifier"
  );
  const verifier = await Verifier.deploy();
  await verifier.waitForDeployment();

  const Attestor = await ethers.getContractFactory("DecisionAttestorAuthV2_2");
  const attestor = await Attestor.deploy(await verifier.getAddress());
  await attestor.waitForDeployment();

  return { admin, outsider, submitter, verifier, attestor };
}

describe("DecisionAttestorAuthV2_2 — role-based authorization", function () {
  it("rejects submitDecision from an account without SUBMITTER_ROLE", async function () {
    const { outsider, attestor } = await deployAuthV22Fixture();

    const submitterRole = await attestor.SUBMITTER_ROLE();

    await expect(
      attestor.connect(outsider).submitDecision(
        "agent-1",
        ethers.ZeroHash,
        ethers.ZeroHash,
        0n,
        ethers.ZeroHash,
        ethers.ZeroHash,
        0n,
        0n,
        0n,
        [0n, 0n],
        [[0n, 0n], [0n, 0n]],
        [0n, 0n],
        [0n, 0n, 0n, 0n, 0n, 0n, 0n, 0n, 0n]
      )
    )
      .to.be.revertedWithCustomError(attestor, "AccessControlUnauthorizedAccount")
      .withArgs(outsider.address, submitterRole);
  });

  it("admin holds DEFAULT_ADMIN_ROLE and SUBMITTER_ROLE by default", async function () {
    const { admin, attestor } = await deployAuthV22Fixture();

    const defaultAdminRole = await attestor.DEFAULT_ADMIN_ROLE();
    const submitterRole = await attestor.SUBMITTER_ROLE();

    expect(await attestor.hasRole(defaultAdminRole, admin.address)).to.equal(true);
    expect(await attestor.hasRole(submitterRole, admin.address)).to.equal(true);
  });

  it("admin can grant SUBMITTER_ROLE to another account", async function () {
    const { submitter, attestor } = await deployAuthV22Fixture();

    const submitterRole = await attestor.SUBMITTER_ROLE();

    await attestor.grantRole(submitterRole, submitter.address);

    expect(await attestor.hasRole(submitterRole, submitter.address)).to.equal(true);
  });
});
