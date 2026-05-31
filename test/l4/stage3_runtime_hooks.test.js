const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Stage3 runtime KPI hooks", function () {
  it("emits direct KPI lines for anchor gas and negative-security controls", async function () {
    const [admin, attacker] = await ethers.getSigners();

    const Ledger = await ethers.getContractFactory("Stage3AnomalyLedger");
    const ledger = await Ledger.deploy(admin.address);
    await ledger.waitForDeployment();

    const commitment = ethers.keccak256(
      ethers.toUtf8Bytes("stage3-commitment-anchor")
    );

    const evidenceHash = ethers.keccak256(
      ethers.toUtf8Bytes("stage3-ipfs-cid-or-evidence-root")
    );

    const tx = await ledger.commit(commitment, evidenceHash);
    const receipt = await tx.wait();

    console.log(`KPI_ANCHOR_GAS=${receipt.gasUsed.toString()}`);

    await expect(
      ledger.commit(commitment, evidenceHash)
    ).to.be.revertedWithCustomError(ledger, "DuplicateCommitment");

    console.log("KPI_REPLAY_REJECTED=true");

    await expect(
      ledger.commit(ethers.ZeroHash, evidenceHash)
    ).to.be.revertedWithCustomError(ledger, "ZeroCommitment");

    console.log("KPI_ZERO_ANCHOR_REJECTED=true");

    const attackerCommitment = ethers.keccak256(
      ethers.toUtf8Bytes("stage3-attacker-commitment")
    );

    await expect(
      ledger.connect(attacker).commit(attackerCommitment, evidenceHash)
    ).to.be.reverted;

    console.log("KPI_UNAUTHORIZED_SUBMITTER_REJECTED=true");
  });
});
