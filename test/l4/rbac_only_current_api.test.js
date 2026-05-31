const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ReputationManager current API", function () {
  it("allows the oracle/admin to post an automatic score and rejects non-oracle submitters", async function () {
    const [admin, nonOracle] = await ethers.getSigners();

    const MockVerifier = await ethers.getContractFactory("MockVerifier");
    const mock = await MockVerifier.deploy();
    await mock.waitForDeployment();

    const Rep = await ethers.getContractFactory("ReputationManager");
    const rep = await Rep.deploy(await mock.getAddress(), admin.address);
    await rep.waitForDeployment();

    const modelId = ethers.keccak256(ethers.toUtf8Bytes("vicuna-13b"));

    await (await rep.postAutoScore(modelId, 6000)).wait();

    const result = await rep.getReputationBP(modelId);
    const autoBP = Number(result[2]);

    expect(autoBP).to.equal(6000);

    await expect(
      rep.connect(nonOracle).postAutoScore(modelId, 7000)
    ).to.be.reverted;
  });
});
