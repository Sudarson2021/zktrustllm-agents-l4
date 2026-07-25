/*
 * Paired SHA-2 commitment benchmark for Ethereum Sepolia and IoTeX testnet.
 *
 * SHA-256 and SHA-512 are computed off chain over identical payload bytes and
 * their complete 32-byte and 64-byte digests are anchored by identical
 * HashCommitmentLedger runtime bytecode on both EVM networks. This isolates
 * digest anchoring from hash computation. The algorithm order is balanced
 * across repetitions to reduce block-position bias.
 *
 * Usage:
 *   REPEATS=30 WARMUPS=2 PAYLOAD_BYTES=1024 \
 *   npx hardhat run --config hardhat.consensus.config.js \
 *     scripts/l4/consensus/run_paired_sha2_benchmark.js
 */
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const hre = require("hardhat");

const { ethers } = hre;

const SCHEMA = "zktrustllm.sha2.paired_anchor_benchmark.v1";
const ALGORITHMS = {
  sha256: { id: 1, digestBytes: 32 },
  sha512: { id: 2, digestBytes: 64 }
};
const NETWORKS = {
  sepolia: {
    role: "gasper_pos",
    name: "Ethereum Sepolia",
    chainId: 11155111,
    consensus: "Ethereum Gasper proof-of-stake (permissioned Sepolia validators)",
    rpcEnv: "SEPOLIA_RPC_URL",
    privateKeyEnvs: ["SEPOLIA_PRIVATE_KEY", "DEPLOYER_PRIVATE_KEY"],
    explorer: "https://sepolia.etherscan.io"
  },
  iotex_testnet: {
    role: "roll_dpos_pbft",
    name: "IoTeX testnet",
    chainId: 4690,
    consensus: "IoTeX Roll-DPoS with PBFT-style finalisation",
    rpcEnv: "IOTEX_TESTNET_RPC_URL",
    defaultRpc: "https://babel-api.testnet.iotex.io",
    privateKeyEnvs: ["IOTEX_TESTNET_PRIVATE_KEY", "DEPLOYER_PRIVATE_KEY"],
    explorer: "https://testnet.iotexscan.io"
  }
};

function integerEnv(name, fallback, minimum, maximum) {
  const raw = process.env[name] || String(fallback);
  if (!/^\d+$/.test(raw)) {
    throw new Error(`${name} must be an integer; received ${JSON.stringify(raw)}`);
  }
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new Error(`${name} must be in [${minimum}, ${maximum}]; received ${value}`);
  }
  return value;
}

function privateKeyFor(spec) {
  for (const name of spec.privateKeyEnvs) {
    const raw = process.env[name] || "";
    if (/^0x[0-9a-fA-F]{64}$/.test(raw)) return raw;
    if (/^[0-9a-fA-F]{64}$/.test(raw)) return `0x${raw}`;
  }
  throw new Error(
    `${spec.name}: set ${spec.privateKeyEnvs.join(" or ")} to a funded test-only key`
  );
}

function rpcFor(spec) {
  const value = process.env[spec.rpcEnv] || spec.defaultRpc || "";
  if (!/^https?:\/\//.test(value)) {
    throw new Error(`${spec.name}: set ${spec.rpcEnv} to an HTTP(S) JSON-RPC URL`);
  }
  return value;
}

function sanitizedRpcOrigin(value) {
  const parsed = new URL(value);
  return `${parsed.protocol}//${parsed.host}`;
}

function hashHex(algorithm, value) {
  return `0x${crypto.createHash(algorithm).update(value).digest("hex")}`;
}

function sha256File(filePath) {
  return hashHex("sha256", fs.readFileSync(filePath)).slice(2);
}

function gitCommit() {
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    }).trim();
  } catch {
    return null;
  }
}

function elapsedMs(startNs) {
  return Number(process.hrtime.bigint() - startNs) / 1e6;
}

function roundMs(value) {
  return Math.round(value * 1000) / 1000;
}

function deterministicPayload(sessionId, phase, index, length) {
  const chunks = [];
  let counter = 0;
  while (Buffer.concat(chunks).length < length) {
    chunks.push(
      crypto
        .createHash("sha512")
        .update(`${sessionId}:${phase}:${index}:${counter}`)
        .digest()
    );
    counter += 1;
  }
  return Buffer.concat(chunks).subarray(0, length);
}

async function safeClientVersion(provider) {
  try {
    return await provider.send("web3_clientVersion", []);
  } catch {
    return null;
  }
}

async function buildContext(key, spec) {
  const rpcUrl = rpcFor(spec);
  const provider = new ethers.JsonRpcProvider(rpcUrl, spec.chainId, {
    staticNetwork: true
  });
  const network = await provider.getNetwork();
  if (Number(network.chainId) !== spec.chainId) {
    throw new Error(
      `${spec.name}: expected chain ID ${spec.chainId}, received ${network.chainId}`
    );
  }
  const signer = new ethers.Wallet(privateKeyFor(spec), provider);
  const balance = await provider.getBalance(signer.address);
  if (balance === 0n) {
    throw new Error(
      `${spec.name}: ${signer.address} has zero testnet balance; fund it before running`
    );
  }
  return {
    key,
    spec,
    provider,
    signer,
    rpcOrigin: sanitizedRpcOrigin(rpcUrl),
    clientVersion: await safeClientVersion(provider),
    startingBalanceWei: balance.toString()
  };
}

function receiptGasPrice(receipt, transaction) {
  return (receipt.gasPrice ?? transaction.gasPrice ?? 0n).toString();
}

async function deployLedger(context, artifact) {
  const factory = new ethers.ContractFactory(
    artifact.abi,
    artifact.bytecode,
    context.signer
  );
  const startNs = process.hrtime.bigint();
  const contract = await factory.deploy(context.signer.address);
  const transaction = contract.deploymentTransaction();
  const receipt = await transaction.wait(1);
  const address = await contract.getAddress();
  const deployedCode = await context.provider.getCode(address);
  if (receipt.status !== 1 || deployedCode === "0x") {
    throw new Error(`${context.spec.name}: HashCommitmentLedger deployment failed`);
  }
  return {
    contract,
    evidence: {
      address,
      transaction_hash: receipt.hash,
      block_number: receipt.blockNumber,
      first_inclusion_latency_ms: roundMs(elapsedMs(startNs)),
      gas_used: receipt.gasUsed.toString(),
      effective_gas_price_wei: receiptGasPrice(receipt, transaction),
      deployed_code_keccak256: ethers.keccak256(deployedCode),
      explorer_url: `${context.spec.explorer}/address/${address}`
    }
  };
}

function findHashEvent(contract, receipt) {
  for (const log of receipt.logs) {
    try {
      const parsed = contract.interface.parseLog(log);
      if (parsed && parsed.name === "HashAnchored") return parsed;
    } catch {
      // Ignore unrelated logs.
    }
  }
  return null;
}

async function submitDigest(
  context,
  contract,
  pairId,
  phase,
  algorithm,
  evidenceId,
  digest
) {
  const submittedAtUtc = new Date().toISOString();
  const startNs = process.hrtime.bigint();
  const transaction = await contract.anchorDigest(
    evidenceId,
    ALGORITHMS[algorithm].id,
    digest,
    { gasLimit: 180000n }
  );
  const acceptedMs = roundMs(elapsedMs(startNs));
  const receipt = await transaction.wait(1);
  const includedMs = roundMs(elapsedMs(startNs));
  const event = findHashEvent(contract, receipt);
  if (receipt.status !== 1 || !event) {
    throw new Error(`${context.spec.name}: ${pairId}/${algorithm} failed`);
  }
  if (
    event.args.evidenceId !== evidenceId ||
    Number(event.args.algorithmId) !== ALGORITHMS[algorithm].id ||
    event.args.digest.toLowerCase() !== digest.toLowerCase() ||
    event.args.submitter.toLowerCase() !== context.signer.address.toLowerCase()
  ) {
    throw new Error(`${context.spec.name}: ${pairId}/${algorithm} event mismatch`);
  }
  return {
    network: context.key,
    pair_id: pairId,
    phase,
    algorithm,
    algorithm_id: ALGORITHMS[algorithm].id,
    digest_bytes: ALGORITHMS[algorithm].digestBytes,
    evidence_id: evidenceId,
    digest,
    submitted_at_utc: submittedAtUtc,
    transaction_hash: receipt.hash,
    explorer_url: `${context.spec.explorer}/tx/${receipt.hash}`,
    rpc_acceptance_latency_ms: acceptedMs,
    first_inclusion_latency_ms: includedMs,
    gas_used: receipt.gasUsed.toString(),
    effective_gas_price_wei: receiptGasPrice(receipt, transaction),
    block_number: receipt.blockNumber,
    block_hash: receipt.blockHash,
    receipt_status: receipt.status,
    hash_event_verified: true
  };
}

async function runNetworkPair(
  context,
  contract,
  pairId,
  phase,
  algorithmOrder,
  evidenceIds,
  digests
) {
  const observations = {};
  for (const algorithm of algorithmOrder) {
    observations[algorithm] = await submitDigest(
      context,
      contract,
      pairId,
      phase,
      algorithm,
      evidenceIds[algorithm],
      digests[algorithm]
    );
  }
  return observations;
}

async function matchedPair(
  contexts,
  contracts,
  sessionId,
  phase,
  index,
  payloadBytes
) {
  const pairId = `${sessionId}-${phase}-${String(index).padStart(3, "0")}`;
  const payload = deterministicPayload(sessionId, phase, index, payloadBytes);
  const digests = {
    sha256: hashHex("sha256", payload),
    sha512: hashHex("sha512", payload)
  };
  const evidenceIds = {
    sha256: ethers.id(`${pairId}:sha256`),
    sha512: ethers.id(`${pairId}:sha512`)
  };
  const order = index % 2 === 0
    ? ["sha256", "sha512"]
    : ["sha512", "sha256"];
  const [sepolia, iotex] = await Promise.all([
    runNetworkPair(
      contexts.sepolia,
      contracts.sepolia,
      pairId,
      phase,
      order,
      evidenceIds,
      digests
    ),
    runNetworkPair(
      contexts.iotex_testnet,
      contracts.iotex_testnet,
      pairId,
      phase,
      order,
      evidenceIds,
      digests
    )
  ]);
  return {
    pair_id: pairId,
    phase,
    payload_bytes: payloadBytes,
    payload_base64: payload.toString("base64"),
    algorithm_order: order,
    evidence_ids: evidenceIds,
    digests,
    observations: {
      sepolia,
      iotex_testnet: iotex
    }
  };
}

function extractRevertData(error) {
  return error?.data ?? error?.error?.data ?? error?.info?.error?.data ?? null;
}

async function rejectionProbe(label, expectedError, contract, callback) {
  try {
    await callback();
    return { label, rejected: false, expected_error_verified: false };
  } catch (error) {
    let actualError = error?.revert?.name ?? null;
    const revertData = extractRevertData(error);
    if (!actualError && revertData) {
      try {
        actualError = contract.interface.parseError(revertData)?.name ?? null;
      } catch {
        actualError = null;
      }
    }
    if (actualError !== expectedError) {
      throw new Error(
        `${label}: expected ${expectedError}, received ${actualError || "unparsed error"}`
      );
    }
    return {
      label,
      rejected: true,
      expected_error: expectedError,
      actual_error: actualError,
      expected_error_verified: true,
      rpc_method: "eth_call"
    };
  }
}

async function runSecurityProbes(context, contract, lastPair) {
  const digest32 = lastPair.digests.sha256;
  const usedId = lastPair.evidence_ids.sha256;
  const attacker = ethers.Wallet.createRandom().connect(context.provider);
  const duplicate = await rejectionProbe(
    "duplicate_evidence_id",
    "DuplicateEvidenceId",
    contract,
    () => contract.anchorDigest.staticCall(usedId, 1, digest32)
  );
  const wrongLength = await rejectionProbe(
    "invalid_sha512_length",
    "InvalidDigestLength",
    contract,
    () => contract.anchorDigest.staticCall(ethers.id(`${lastPair.pair_id}:bad`), 2, digest32)
  );
  const unauthorized = await rejectionProbe(
    "unauthorized_submitter",
    "AccessControlUnauthorizedAccount",
    contract,
    () => contract
      .connect(attacker)
      .anchorDigest.staticCall(ethers.id(`${lastPair.pair_id}:attacker`), 1, digest32)
  );
  return {
    method: "read-only eth_call against deployed public-testnet state",
    duplicate,
    wrong_length: wrongLength,
    unauthorized
  };
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

async function main() {
  const repeats = integerEnv("REPEATS", 30, 10, 500);
  const warmups = integerEnv("WARMUPS", 2, 0, 20);
  const payloadBytes = integerEnv("PAYLOAD_BYTES", 1024, 1, 16384);
  const startedAtUtc = new Date().toISOString();
  const sessionId =
    process.env.SESSION_ID || startedAtUtc.replace(/[:.]/g, "-");
  if (!/^[A-Za-z0-9._-]+$/.test(sessionId)) {
    throw new Error("SESSION_ID contains unsupported characters");
  }
  const outRoot =
    process.env.HASH_CONSENSUS_OUT_DIR ||
    path.join("runtime_artifacts", "hash_consensus_comparison");
  const outDir = path.join(outRoot, sessionId);
  if (fs.existsSync(outDir)) {
    throw new Error(`output directory already exists: ${outDir}`);
  }
  fs.mkdirSync(outDir, { recursive: true });

  const artifact = await hre.artifacts.readArtifact("HashCommitmentLedger");
  const contractSource = path.join(
    "contracts",
    "l4",
    "HashCommitmentLedger.sol"
  );
  const scriptPath = path.join(
    "scripts",
    "l4",
    "consensus",
    "run_paired_sha2_benchmark.js"
  );
  const artifactBytecodeKeccak = ethers.keccak256(artifact.bytecode);

  const [sepoliaContext, iotexContext] = await Promise.all([
    buildContext("sepolia", NETWORKS.sepolia),
    buildContext("iotex_testnet", NETWORKS.iotex_testnet)
  ]);
  const contexts = {
    sepolia: sepoliaContext,
    iotex_testnet: iotexContext
  };
  const [sepoliaDeployment, iotexDeployment] = await Promise.all([
    deployLedger(contexts.sepolia, artifact),
    deployLedger(contexts.iotex_testnet, artifact)
  ]);
  if (
    sepoliaDeployment.evidence.deployed_code_keccak256 !==
    iotexDeployment.evidence.deployed_code_keccak256
  ) {
    throw new Error("deployed runtime bytecode differs between networks");
  }
  const contracts = {
    sepolia: sepoliaDeployment.contract,
    iotex_testnet: iotexDeployment.contract
  };

  const warmupPairs = [];
  for (let index = 0; index < warmups; index += 1) {
    warmupPairs.push(
      await matchedPair(
        contexts,
        contracts,
        sessionId,
        "warmup",
        index,
        payloadBytes
      )
    );
  }
  const measuredPairs = [];
  for (let index = 0; index < repeats; index += 1) {
    const pair = await matchedPair(
      contexts,
      contracts,
      sessionId,
      "measurement",
      index,
      payloadBytes
    );
    measuredPairs.push(pair);
    console.log(
      `KPI_SHA2_PAIR=${index} ` +
      `SEPOLIA_SHA256_GAS=${pair.observations.sepolia.sha256.gas_used} ` +
      `SEPOLIA_SHA512_GAS=${pair.observations.sepolia.sha512.gas_used} ` +
      `IOTEX_SHA256_GAS=${pair.observations.iotex_testnet.sha256.gas_used} ` +
      `IOTEX_SHA512_GAS=${pair.observations.iotex_testnet.sha512.gas_used}`
    );
  }
  const lastPair = measuredPairs[measuredPairs.length - 1];
  const [sepoliaSecurity, iotexSecurity, endingSepolia, endingIotex] =
    await Promise.all([
      runSecurityProbes(contexts.sepolia, contracts.sepolia, lastPair),
      runSecurityProbes(contexts.iotex_testnet, contracts.iotex_testnet, lastPair),
      contexts.sepolia.provider.getBalance(contexts.sepolia.signer.address),
      contexts.iotex_testnet.provider.getBalance(contexts.iotex_testnet.signer.address)
    ]);

  const benchmark = {
    schema: SCHEMA,
    run_status: "completed",
    session_id: sessionId,
    started_at_utc: startedAtUtc,
    finished_at_utc: new Date().toISOString(),
    git_commit: gitCommit(),
    design: {
      paired_across_networks: true,
      balanced_algorithm_order: true,
      repeats,
      warmups,
      payload_bytes: payloadBytes,
      confirmations_waited: 1,
      primary_metric: "EVM gas used to anchor a precomputed full digest",
      secondary_metric: "client-observed submission-to-first-inclusion latency",
      computation_boundary:
        "SHA-256 and SHA-512 are computed by Node.js before submission. Network results measure complete-digest anchoring, not hash throughput.",
      finality_boundary:
        "One receipt inclusion is observed; economic finality is not measured."
    },
    implementation: {
      contract: "HashCommitmentLedger",
      contract_source: contractSource,
      contract_source_sha256: sha256File(contractSource),
      benchmark_script: scriptPath,
      benchmark_script_sha256: sha256File(scriptPath),
      artifact_bytecode_keccak256: artifactBytecodeKeccak,
      solidity: "0.8.20",
      optimizer_enabled: true,
      optimizer_runs: 200,
      via_ir: true
    },
    algorithms: {
      sha256: {
        standard: "NIST FIPS 180-4",
        digest_bytes: 32,
        computation: "off-chain Node.js crypto",
        evm_note: "standard SHA-256 precompile exists; not used by primary anchor comparison"
      },
      sha512: {
        standard: "NIST FIPS 180-4",
        digest_bytes: 64,
        computation: "off-chain Node.js crypto",
        evm_note: "no standard EVM SHA-512 precompile"
      }
    },
    networks: {
      sepolia: {
        role: NETWORKS.sepolia.role,
        name: NETWORKS.sepolia.name,
        chain_id: NETWORKS.sepolia.chainId,
        consensus: NETWORKS.sepolia.consensus,
        rpc_origin: contexts.sepolia.rpcOrigin,
        rpc_client_version: contexts.sepolia.clientVersion,
        signer: contexts.sepolia.signer.address,
        starting_balance_wei: contexts.sepolia.startingBalanceWei,
        ending_balance_wei: endingSepolia.toString(),
        deployment: sepoliaDeployment.evidence,
        security_probes: sepoliaSecurity
      },
      iotex_testnet: {
        role: NETWORKS.iotex_testnet.role,
        name: NETWORKS.iotex_testnet.name,
        chain_id: NETWORKS.iotex_testnet.chainId,
        consensus: NETWORKS.iotex_testnet.consensus,
        rpc_origin: contexts.iotex_testnet.rpcOrigin,
        rpc_client_version: contexts.iotex_testnet.clientVersion,
        signer: contexts.iotex_testnet.signer.address,
        starting_balance_wei: contexts.iotex_testnet.startingBalanceWei,
        ending_balance_wei: endingIotex.toString(),
        deployment: iotexDeployment.evidence,
        security_probes: iotexSecurity
      }
    },
    warmup_pairs: warmupPairs,
    measured_pairs: measuredPairs,
    claim_boundary:
      "Measured values apply only to precomputed SHA-2 digest anchoring by identical EVM runtime bytecode on the named testnets. They do not compare cryptographic security, CPU hash throughput, consensus superiority, mainnet performance, or economic finality."
  };
  const benchmarkPath = path.join(outDir, "benchmark.json");
  writeJson(benchmarkPath, benchmark);
  const digest = sha256File(benchmarkPath);
  fs.writeFileSync(
    path.join(outDir, "SHA256SUMS.txt"),
    `${digest}  benchmark.json\n`
  );
  console.log(`KPI_SHA2_BENCHMARK=${benchmarkPath}`);
  console.log(`KPI_SHA2_BENCHMARK_SHA256=${digest}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
