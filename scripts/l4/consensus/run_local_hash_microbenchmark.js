"use strict";

const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const hre = require("hardhat");

const ALGORITHMS = [
  { id: "keccak256", label: "Keccak-256", method: "measureKeccak256" },
  { id: "sha256", label: "SHA-256", method: "measureSha256" },
  { id: "sha512_local", label: "SHA-512 (Solidity)", method: "measureSha512Local" }
];

function positiveInteger(name, fallback) {
  const value = Number(process.env[name] || fallback);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error(`${name} must be a positive integer`);
  }
  return value;
}

function deterministicPayload(size) {
  return Buffer.from(Array.from({ length: size }, (_, index) => (17 + index * 31) & 0xff));
}

function sha2(name, payload) {
  return `0x${crypto.createHash(name).update(payload).digest("hex")}`;
}

function sourceSha256(relativePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(relativePath)).digest("hex");
}

async function measure(benchmark, algorithm, payload) {
  const [digest, primitiveGas] = await benchmark[algorithm.method].staticCall(payload);
  return {
    digest: hre.ethers.hexlify(digest),
    primitive_gas: Number(primitiveGas)
  };
}

async function main() {
  const repetitions = positiveInteger("REPEATS", 30);
  const warmups = positiveInteger("WARMUPS", 3);
  const payloadSizes = String(process.env.PAYLOAD_BYTES || "32,1024")
    .split(",")
    .map((value) => Number(value.trim()));
  if (
    payloadSizes.length < 1 ||
    payloadSizes.some((value) => !Number.isInteger(value) || value <= 0)
  ) {
    throw new Error("PAYLOAD_BYTES must be a comma-separated list of positive integers");
  }

  const sessionId =
    process.env.SESSION_ID ||
    `local-hardhat-${new Date().toISOString().replace(/[:.]/g, "-")}`;
  if (!/^[A-Za-z0-9._-]+$/.test(sessionId)) {
    throw new Error("SESSION_ID contains unsafe characters");
  }
  const outputDir = path.join(
    "runtime_artifacts",
    "hash_microbenchmark",
    sessionId
  );
  if (fs.existsSync(outputDir)) {
    throw new Error(`refusing to overwrite existing session: ${outputDir}`);
  }
  const gitStatus = execFileSync(
    "git",
    ["status", "--porcelain", "--untracked-files=normal"],
    { encoding: "utf8" }
  ).trim();

  const factory = await hre.ethers.getContractFactory("HashPrimitiveMicrobenchmark");
  const benchmark = await factory.deploy();
  await benchmark.waitForDeployment();
  const address = await benchmark.getAddress();
  const network = await hre.ethers.provider.getNetwork();
  const runtimeCode = await hre.ethers.provider.getCode(address);

  const abc = hre.ethers.toUtf8Bytes("abc");
  const empty = new Uint8Array();
  const vectors = {
    sha256_abc: {
      expected: "0xba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
      observed: (await measure(benchmark, ALGORITHMS[1], abc)).digest
    },
    sha512_empty: {
      expected:
        "0xcf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce" +
        "47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
      observed: (await measure(benchmark, ALGORITHMS[2], empty)).digest
    },
    sha512_abc: {
      expected:
        "0xddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a" +
        "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
      observed: (await measure(benchmark, ALGORITHMS[2], abc)).digest
    }
  };
  for (const [name, vector] of Object.entries(vectors)) {
    vector.pass = vector.expected === vector.observed;
    if (!vector.pass) throw new Error(`FIPS/vector gate failed: ${name}`);
  }

  const payloadResults = [];
  for (const payloadSize of payloadSizes) {
    const payload = deterministicPayload(payloadSize);
    const expected = {
      keccak256: hre.ethers.keccak256(payload),
      sha256: sha2("sha256", payload),
      sha512_local: sha2("sha512", payload)
    };

    for (let i = 0; i < warmups; ++i) {
      for (const algorithm of ALGORITHMS) {
        await measure(benchmark, algorithm, payload);
      }
    }

    const samples = Object.fromEntries(
      ALGORITHMS.map((algorithm) => [
        algorithm.id,
        { label: algorithm.label, digest: null, primitive_gas_samples: [] }
      ])
    );
    for (let repetition = 0; repetition < repetitions; ++repetition) {
      const offset = repetition % ALGORITHMS.length;
      const balancedOrder = ALGORITHMS.slice(offset).concat(ALGORITHMS.slice(0, offset));
      for (const algorithm of balancedOrder) {
        const observation = await measure(benchmark, algorithm, payload);
        if (observation.digest !== expected[algorithm.id]) {
          throw new Error(
            `digest mismatch for ${algorithm.id} at payload ${payloadSize}`
          );
        }
        samples[algorithm.id].digest = observation.digest;
        samples[algorithm.id].primitive_gas_samples.push(observation.primitive_gas);
      }
    }

    payloadResults.push({
      payload_bytes: payloadSize,
      payload_hex: `0x${payload.toString("hex")}`,
      payload_sha256: sha2("sha256", payload),
      samples
    });
  }

  const packageJson = require(path.resolve("package.json"));
  const output = {
    schema_version: "zktrustllm-hash-primitive-microbenchmark-v1",
    session_id: sessionId,
    generated_at_utc: new Date().toISOString(),
    claim_boundary: {
      environment: "local Hardhat EVM only",
      measurement: "gasleft delta around the isolated primitive path",
      sha512: "FIPS-gated pure-Solidity microbenchmark; not the deployable anchor path",
      deployment: "SHA-512 is computed off chain and the full 64-byte digest is anchored",
      excluded_claims: [
        "public-testnet hash latency",
        "economic cost",
        "consensus performance",
        "production SHA-512 execution"
      ]
    },
    environment: {
      git_commit: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
      git_dirty: gitStatus.length > 0,
      git_status_porcelain: gitStatus,
      node_version: process.version,
      hardhat_version: packageJson.devDependencies.hardhat,
      platform: `${os.platform()} ${os.release()} ${os.arch()}`,
      cpu_model: os.cpus()[0]?.model || "unknown",
      chain_id: Number(network.chainId),
      solidity: "0.8.20",
      optimizer_enabled: true,
      optimizer_runs: 200,
      via_ir: true,
      evm_target: "paris"
    },
    contract: {
      address,
      runtime_code_hash: hre.ethers.keccak256(runtimeCode),
      source_path: "contracts/l4/HashPrimitiveMicrobenchmark.sol",
      source_sha256: sourceSha256("contracts/l4/HashPrimitiveMicrobenchmark.sol")
    },
    sampling: {
      warmups,
      repetitions,
      order: "balanced cyclic rotation per repetition",
      payload_construction: "deterministic byte i = (17 + 31*i) mod 256"
    },
    validation_vectors: vectors,
    payloads: payloadResults
  };

  fs.mkdirSync(outputDir, { recursive: true });
  const benchmarkPath = path.join(outputDir, "benchmark.json");
  const json = `${JSON.stringify(output, null, 2)}\n`;
  fs.writeFileSync(benchmarkPath, json);
  const checksum = crypto.createHash("sha256").update(json).digest("hex");
  fs.writeFileSync(path.join(outputDir, "SHA256SUMS.txt"), `${checksum}  benchmark.json\n`);
  process.stdout.write(`${benchmarkPath}\n`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
