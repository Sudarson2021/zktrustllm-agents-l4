const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("HashPrimitiveMicrobenchmark", function () {
  let benchmark;

  beforeEach(async function () {
    benchmark = await (await ethers.getContractFactory("HashPrimitiveMicrobenchmark")).deploy();
    await benchmark.waitForDeployment();
  });

  async function measured(functionName, utf8) {
    const payload = ethers.toUtf8Bytes(utf8);
    const [digest, primitiveGas] = await benchmark[functionName].staticCall(payload);
    return { digest: ethers.hexlify(digest), primitiveGas };
  }

  it("passes the FIPS 180-4 SHA-512 empty-string vector", async function () {
    const result = await measured("measureSha512Local", "");
    expect(result.digest).to.equal(
      "0xcf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce" +
      "47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
    );
  });

  it("passes SHA-256 and SHA-512 abc vectors", async function () {
    const sha256 = await measured("measureSha256", "abc");
    const sha512 = await measured("measureSha512Local", "abc");
    expect(sha256.digest).to.equal(
      "0xba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    );
    expect(sha512.digest).to.equal(
      "0xddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a" +
      "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"
    );
  });

  it("returns canonical Keccak-256", async function () {
    const result = await measured("measureKeccak256", "abc");
    expect(result.digest).to.equal(ethers.keccak256(ethers.toUtf8Bytes("abc")));
  });

  it("reports positive primitive-path gas without changing state", async function () {
    const methods = ["measureKeccak256", "measureSha256", "measureSha512Local"];
    for (const method of methods) {
      const result = await measured(method, "ZKTrustLLM-Agents-L4");
      expect(result.primitiveGas).to.be.greaterThan(0n);
    }
  });
});
