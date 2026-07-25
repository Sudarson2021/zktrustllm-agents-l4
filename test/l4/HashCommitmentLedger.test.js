const { expect } = require("chai");
const { ethers } = require("hardhat");
const crypto = require("crypto");

describe("HashCommitmentLedger", function () {
  async function deployFixture() {
    const [admin, outsider] = await ethers.getSigners();
    const factory = await ethers.getContractFactory("HashCommitmentLedger");
    const ledger = await factory.deploy(admin.address);
    await ledger.waitForDeployment();
    return { ledger, admin, outsider };
  }

  function digest(name, payload) {
    return `0x${crypto.createHash(name).update(payload).digest("hex")}`;
  }

  it("anchors full SHA-256 and SHA-512 digests", async function () {
    const { ledger, admin } = await deployFixture();
    const payload = Buffer.from("zktrustllm-hash-comparison");
    const sha256 = digest("sha256", payload);
    const sha512 = digest("sha512", payload);
    const id256 = ethers.id("sha256-evidence");
    const id512 = ethers.id("sha512-evidence");

    await expect(ledger.anchorDigest(id256, 1, sha256))
      .to.emit(ledger, "HashAnchored")
      .withArgs(id256, 1, sha256, admin.address);
    await expect(ledger.anchorDigest(id512, 2, sha512))
      .to.emit(ledger, "HashAnchored")
      .withArgs(id512, 2, sha512, admin.address);
  });

  it("computes SHA-256 on chain through the precompile path", async function () {
    const { ledger, admin } = await deployFixture();
    const payload = ethers.toUtf8Bytes("bounded-evidence-payload");
    const expected = digest("sha256", Buffer.from(payload));
    const evidenceId = ethers.id("precompile-evidence");

    await expect(ledger.computeSha256AndAnchor(evidenceId, payload))
      .to.emit(ledger, "HashAnchored")
      .withArgs(evidenceId, 1, expected, admin.address);
  });

  it("rejects wrong digest lengths and unknown algorithms", async function () {
    const { ledger } = await deployFixture();
    await expect(
      ledger.anchorDigest(ethers.id("short"), 1, "0x1234")
    ).to.be.revertedWithCustomError(ledger, "InvalidDigestLength");
    await expect(
      ledger.anchorDigest(ethers.id("unknown"), 9, `0x${"11".repeat(32)}`)
    ).to.be.revertedWithCustomError(ledger, "UnsupportedHashAlgorithm");
  });

  it("rejects duplicate, zero, and unauthorised evidence", async function () {
    const { ledger, outsider } = await deployFixture();
    const digest32 = `0x${"22".repeat(32)}`;
    const evidenceId = ethers.id("duplicate");

    await ledger.anchorDigest(evidenceId, 1, digest32);
    await expect(
      ledger.anchorDigest(evidenceId, 1, digest32)
    ).to.be.revertedWithCustomError(ledger, "DuplicateEvidenceId");
    await expect(
      ledger.anchorDigest(ethers.ZeroHash, 1, digest32)
    ).to.be.revertedWithCustomError(ledger, "ZeroEvidenceId");
    await expect(
      ledger.connect(outsider).anchorDigest(ethers.id("outsider"), 1, digest32)
    ).to.be.revertedWithCustomError(
      ledger,
      "AccessControlUnauthorizedAccount"
    );
  });
});
