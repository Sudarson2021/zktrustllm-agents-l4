#!/usr/bin/env node
"use strict";

/*
 * Real permissioned-consensus fault experiment.
 *
 * The runner starts:
 *   1. a three-member etcd/Raft cluster; and
 *   2. a four-validator Hyperledger Besu/QBFT EVM network.
 *
 * It records only directly observed crash/non-participation scenarios. Stopping
 * a QBFT validator does not emulate equivocation or arbitrary Byzantine
 * messages, so the output explicitly sets byzantine_faults_measured=false.
 */

const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn, spawnSync } = require("child_process");
const { ethers } = require("ethers");

const REPO_ROOT = path.resolve(__dirname, "../../../..");
const TOOLS_ROOT = path.resolve(
  process.env.TOOLS_ROOT || path.join(REPO_ROOT, ".tools", "permissioned")
);
const SESSION_ID =
  process.env.SESSION_ID || `permissioned-${new Date().toISOString().replace(/[:.]/g, "-")}`;
const OUTPUT_ROOT = path.resolve(
  process.env.OUTPUT_ROOT || path.join(REPO_ROOT, "evaluation_runs", "permissioned_faults")
);
const OUTPUT_DIR = path.join(OUTPUT_ROOT, SESSION_ID);
const RUNTIME_DIR = path.resolve(
  process.env.RUNTIME_ROOT ||
    path.join(REPO_ROOT, ".runtime", "permissioned", SESSION_ID)
);
const LOG_DIR = path.join(OUTPUT_DIR, "logs");

const REPEATS = integerEnv("REPEATS", 30, 2, 1000);
const WARMUPS = integerEnv("WARMUPS", 3, 0, 100);
const PROBE_INTERVAL_MS = integerEnv("PROBE_INTERVAL_MS", 1000, 100, 10000);
const STARTUP_TIMEOUT_MS = integerEnv("STARTUP_TIMEOUT_MS", 90000, 10000, 600000);
const RECOVERY_TIMEOUT_MS = integerEnv("RECOVERY_TIMEOUT_MS", 120000, 5000, 300000);
const ALLOW_DIRTY = process.env.ALLOW_DIRTY === "1";

const ETCD_BIN = path.join(TOOLS_ROOT, "etcd", "etcd");
const ETCDCTL_BIN = path.join(TOOLS_ROOT, "etcd", "etcdctl");
const BESU_BIN = path.join(TOOLS_ROOT, "besu", "bin", "besu");

// Public Hardhat development keys are used only inside the isolated local QBFT
// network. They must never be reused on a public network.
const ADMIN_PRIVATE_KEY =
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
const UNAUTH_PRIVATE_KEY =
  "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d";
const ADMIN_ADDRESS = "f39fd6e51aad88f6f4ce6ab8827279cfffb92266";
const UNAUTH_ADDRESS = "70997970c51812dc3a010c7d01b50e0d17dc79c8";

function integerEnv(name, fallback, minimum, maximum) {
  const raw = process.env[name] || String(fallback);
  if (!/^\d+$/.test(raw)) throw new Error(`${name} must be an integer`);
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new Error(`${name} must be in [${minimum}, ${maximum}]`);
  }
  return value;
}

function assertSafeSessionId(value) {
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$/.test(value)) {
    throw new Error("SESSION_ID must contain only letters, digits, dot, underscore, or hyphen");
  }
}

function sha256(data) {
  return crypto.createHash("sha256").update(data).digest("hex");
}

function sha256File(filePath) {
  return sha256(fs.readFileSync(filePath));
}

function roundMs(value) {
  return Math.round(value * 1000) / 1000;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function nowUtc() {
  return new Date().toISOString();
}

function elapsedMs(startNs) {
  return roundMs(Number(process.hrtime.bigint() - startNs) / 1e6);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || REPO_ROOT,
    encoding: "utf8",
    env: {
      ...process.env,
      XDG_CONFIG_HOME:
        process.env.XDG_CONFIG_HOME || path.join(RUNTIME_DIR, "xdg-config"),
      XDG_DATA_HOME:
        process.env.XDG_DATA_HOME || path.join(RUNTIME_DIR, "xdg-data"),
      XDG_CACHE_HOME:
        process.env.XDG_CACHE_HOME || path.join(RUNTIME_DIR, "xdg-cache"),
      NPM_CONFIG_CACHE:
        process.env.NPM_CONFIG_CACHE && process.env.NPM_CONFIG_CACHE !== "/root/.npm"
          ? process.env.NPM_CONFIG_CACHE
          : path.join(RUNTIME_DIR, "npm-cache"),
      ...(options.env || {})
    },
    timeout: options.timeout || 120000,
    maxBuffer: 20 * 1024 * 1024
  });
  return {
    ok: result.status === 0,
    status: result.status,
    signal: result.signal,
    stdout: (result.stdout || "").trim(),
    stderr: (result.stderr || "").trim(),
    error: result.error ? String(result.error.message || result.error) : null
  };
}

function mustRun(command, args, options = {}) {
  const result = run(command, args, options);
  if (!result.ok) {
    throw new Error(
      `${command} ${args.join(" ")} failed (${result.status}):\n${result.stderr || result.stdout}`
    );
  }
  return result;
}

async function waitFor(description, predicate, timeoutMs = STARTUP_TIMEOUT_MS, intervalMs = 250) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const value = await predicate();
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await sleep(intervalMs);
  }
  const suffix = lastError ? ` Last error: ${lastError.message}` : "";
  throw new Error(`Timed out waiting for ${description}.${suffix}`);
}

function gitMetadata() {
  const commit = mustRun("git", ["rev-parse", "HEAD"]).stdout;
  const status = mustRun("git", ["status", "--porcelain"]).stdout;
  if (status && !ALLOW_DIRTY) {
    throw new Error(
      "The Git worktree is dirty. Commit the experiment implementation before a publication run, " +
        "or set ALLOW_DIRTY=1 only for a non-publication smoke run."
    );
  }
  return {
    commit,
    clean: status.length === 0,
    dirty_paths: status ? status.split("\n") : []
  };
}

function hostMetadata() {
  const cpu = os.cpus()[0] || {};
  const java = run("java", ["-version"]);
  const node = run(process.execPath, ["--version"]);
  return {
    platform: os.platform(),
    release: os.release(),
    architecture: os.arch(),
    cpu_model: cpu.model || null,
    logical_cpus: os.cpus().length,
    total_memory_bytes: os.totalmem(),
    node_version: node.stdout || node.stderr,
    java_version: (java.stderr || java.stdout).split("\n")[0] || null
  };
}

async function stopChild(child, label) {
  if (!child || child.exitCode !== null) return;
  child.kill("SIGTERM");
  const exited = await Promise.race([
    new Promise((resolve) => child.once("exit", resolve)),
    sleep(5000).then(() => false)
  ]);
  if (exited === false && child.exitCode === null) {
    child.kill("SIGKILL");
    await Promise.race([
      new Promise((resolve) => child.once("exit", resolve)),
      sleep(3000)
    ]);
  }
  if (child.exitCode === null && child.signalCode === null) {
    throw new Error(`Could not stop ${label}`);
  }
}

class EtcdCluster {
  constructor() {
    this.root = path.join(RUNTIME_DIR, "etcd");
    this.endpoints = [23790, 23800, 23810].map((port) => `http://127.0.0.1:${port}`);
    this.members = [
      { name: "raft1", clientPort: 23790, peerPort: 23890 },
      { name: "raft2", clientPort: 23800, peerPort: 23900 },
      { name: "raft3", clientPort: 23810, peerPort: 23910 }
    ].map((member, index) => ({ ...member, index, child: null, starts: 0 }));
    this.initialCluster = this.members
      .map((member) => `${member.name}=http://127.0.0.1:${member.peerPort}`)
      .join(",");
  }

  startMember(index) {
    const member = this.members[index];
    if (
      member.child &&
      member.child.exitCode === null &&
      member.child.signalCode === null
    ) return;
    const dataDir = path.join(this.root, member.name);
    fs.mkdirSync(dataDir, { recursive: true });
    const logPath = path.join(LOG_DIR, `${member.name}.log`);
    const logFd = fs.openSync(logPath, "a");
    const args = [
      `--name=${member.name}`,
      `--data-dir=${dataDir}`,
      `--listen-client-urls=http://127.0.0.1:${member.clientPort}`,
      `--advertise-client-urls=http://127.0.0.1:${member.clientPort}`,
      `--listen-peer-urls=http://127.0.0.1:${member.peerPort}`,
      `--initial-advertise-peer-urls=http://127.0.0.1:${member.peerPort}`,
      `--initial-cluster=${this.initialCluster}`,
      `--initial-cluster-token=zktrustllm-${SESSION_ID}`,
      `--initial-cluster-state=${member.starts === 0 ? "new" : "existing"}`,
      "--logger=zap",
      "--log-level=info"
    ];
    member.child = spawn(ETCD_BIN, args, {
      cwd: REPO_ROOT,
      env: { ...process.env, ETCD_UNSUPPORTED_ARCH: "" },
      stdio: ["ignore", logFd, logFd]
    });
    fs.closeSync(logFd);
    member.starts += 1;
  }

  async startAll() {
    fs.mkdirSync(this.root, { recursive: true });
    this.members.forEach((_, index) => this.startMember(index));
    await this.waitHealthy(3);
  }

  etcdctl(args, timeout = 5000) {
    return run(
      ETCDCTL_BIN,
      [`--endpoints=${this.endpoints.join(",")}`, "--dial-timeout=700ms", "--command-timeout=1500ms", ...args],
      { env: { ETCDCTL_API: "3" }, timeout }
    );
  }

  healthyEndpoints() {
    let count = 0;
    for (const endpoint of this.endpoints) {
      const result = run(
        ETCDCTL_BIN,
        [`--endpoints=${endpoint}`, "--dial-timeout=500ms", "--command-timeout=800ms", "endpoint", "health"],
        { env: { ETCDCTL_API: "3" }, timeout: 3000 }
      );
      if (result.ok) count += 1;
    }
    return count;
  }

  async waitHealthy(expected) {
    return waitFor(`${expected} healthy etcd members`, () => this.healthyEndpoints() >= expected);
  }

  status() {
    const rows = [];
    for (const endpoint of this.endpoints) {
      const result = run(
        ETCDCTL_BIN,
        [
          `--endpoints=${endpoint}`,
          "--dial-timeout=500ms",
          "--command-timeout=800ms",
          "endpoint",
          "status",
          "--write-out=json"
        ],
        { env: { ETCDCTL_API: "3" }, timeout: 3000 }
      );
      if (result.ok) rows.push(...JSON.parse(result.stdout));
    }
    if (rows.length === 0) throw new Error("No reachable etcd endpoint returned status");
    return rows;
  }

  leaderIndex() {
    const rows = this.status();
    const leaderId = String(rows[0].Status.leader);
    const row = rows.find((item) => String(item.Status.header.member_id) === leaderId);
    if (!row) throw new Error(`Could not map etcd leader ${leaderId}`);
    const port = Number(new URL(row.Endpoint).port);
    const index = this.members.findIndex((member) => member.clientPort === port);
    if (index < 0) throw new Error(`Unknown etcd leader endpoint ${row.Endpoint}`);
    return index;
  }

  async stopMember(index) {
    const member = this.members[index];
    await stopChild(member.child, member.name);
  }

  async restartMember(index) {
    this.startMember(index);
  }

  put(scenario, index, expectSuccess = true) {
    const payload = JSON.stringify({
      session_id: SESSION_ID,
      family: "raft",
      scenario,
      index,
      nonce: crypto.randomBytes(8).toString("hex")
    });
    const key = `/zktrustllm/${SESSION_ID}/${scenario}/${index}-${sha256(payload).slice(0, 12)}`;
    const startedAtUtc = nowUtc();
    const startNs = process.hrtime.bigint();
    const result = this.etcdctl(["put", key, payload], 4000);
    const observation = {
      index,
      started_at_utc: startedAtUtc,
      latency_ms: elapsedMs(startNs),
      success: result.ok,
      expected_success: expectSuccess,
      key,
      value_sha256: sha256(payload),
      stdout: result.stdout,
      stderr: result.stderr,
      exit_status: result.status
    };
    if (result.ok !== expectSuccess) {
      throw new Error(
        `Raft ${scenario} observation ${index}: expected success=${expectSuccess}, observed ${result.ok}`
      );
    }
    return observation;
  }

  async collectWrites(scenario, count, expectSuccess = true) {
    const observations = [];
    for (let index = 0; index < count; index += 1) {
      observations.push(this.put(scenario, index, expectSuccess));
    }
    return observations;
  }

  async stopAll() {
    for (const member of [...this.members].reverse()) {
      await stopChild(member.child, member.name);
    }
  }
}

async function rpc(url, method, params = [], timeoutMs = 3000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
      signal: controller.signal
    });
    const body = await response.json();
    if (body.error) throw new Error(`${method}: ${JSON.stringify(body.error)}`);
    return body.result;
  } finally {
    clearTimeout(timeout);
  }
}

class BesuCluster {
  constructor(artifact) {
    this.artifact = artifact;
    this.root = path.join(RUNTIME_DIR, "besu");
    this.configRoot = path.join(this.root, "networkFiles");
    this.genesisPath = path.join(this.configRoot, "genesis.json");
    this.nodes = [0, 1, 2, 3].map((index) => ({
      index,
      name: `qbft${index + 1}`,
      rpcPort: integerEnv("BESU_RPC_BASE_PORT", 18545, 1024, 65000) + index,
      p2pPort: 30303 + index,
      child: null,
      keyPath: null,
      pubkey: null
    }));
    this.provider = null;
    this.admin = null;
    this.contract = null;
    this.deployment = null;
  }

  writeGenesisConfig() {
    fs.mkdirSync(this.root, { recursive: true });
    const configPath = path.join(this.root, "qbftConfigFile.json");
    const config = {
      genesis: {
        config: {
          chainId: 13371,
          berlinBlock: 0,
          londonBlock: 0,
          qbft: {
            blockperiodseconds: 1,
            epochlength: 30000,
            requesttimeoutseconds: 4
          }
        },
        nonce: "0x0",
        timestamp: "0x58ee40ba",
        gasLimit: "0x1fffffffffffff",
        difficulty: "0x1",
        mixHash: "0x63746963616c2d62797465636f64652d686173682d65766964656e63652d3031",
        coinbase: "0x0000000000000000000000000000000000000000",
        baseFeePerGas: "0x0",
        alloc: {
          [ADMIN_ADDRESS]: { balance: "0x3635c9adc5dea00000" },
          [UNAUTH_ADDRESS]: { balance: "0x3635c9adc5dea00000" }
        }
      },
      blockchain: {
        nodes: {
          generate: true,
          count: 4
        }
      }
    };
    fs.writeFileSync(configPath, `${JSON.stringify(config, null, 2)}\n`);
    return configPath;
  }

  generateNetwork() {
    const configPath = this.writeGenesisConfig();
    mustRun(BESU_BIN, [
      "operator",
      "generate-blockchain-config",
      `--config-file=${configPath}`,
      `--to=${this.configRoot}`,
      "--private-key-file-name=key"
    ]);
    const keyRoot = path.join(this.configRoot, "keys");
    const keyDirs = fs
      .readdirSync(keyRoot, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => path.join(keyRoot, entry.name))
      .sort();
    if (keyDirs.length !== 4) {
      throw new Error(`Besu operator generated ${keyDirs.length} validator key directories, expected 4`);
    }
    this.nodes.forEach((node, index) => {
      node.keyPath = path.join(keyDirs[index], "key");
      node.pubkey = fs.readFileSync(path.join(keyDirs[index], "key.pub"), "utf8").trim().replace(/^0x/, "");
      if (!/^[0-9a-fA-F]{128}$/.test(node.pubkey)) {
        throw new Error(`Invalid Besu public key for ${node.name}`);
      }
    });
  }

  bootnodeUrl() {
    const node = this.nodes[0];
    return `enode://${node.pubkey}@127.0.0.1:${node.p2pPort}`;
  }

  startNode(index) {
    const node = this.nodes[index];
    if (
      node.child &&
      node.child.exitCode === null &&
      node.child.signalCode === null
    ) return;
    const dataPath = path.join(this.root, node.name);
    fs.mkdirSync(dataPath, { recursive: true });
    const logFd = fs.openSync(path.join(LOG_DIR, `${node.name}.log`), "a");
    const args = [
      `--data-path=${dataPath}`,
      `--genesis-file=${this.genesisPath}`,
      `--node-private-key-file=${node.keyPath}`,
      "--network-id=13371",
      `--p2p-port=${node.p2pPort}`,
      "--p2p-host=127.0.0.1",
      "--rpc-http-enabled=true",
      "--rpc-http-host=127.0.0.1",
      `--rpc-http-port=${node.rpcPort}`,
      "--rpc-http-api=ETH,NET,WEB3,QBFT,ADMIN",
      "--host-allowlist=*",
      "--rpc-http-cors-origins=all",
      "--min-gas-price=0",
      "--logging=INFO"
    ];
    if (index !== 0) args.push(`--bootnodes=${this.bootnodeUrl()}`);
    node.child = spawn(BESU_BIN, args, {
      cwd: REPO_ROOT,
      env: {
        ...process.env,
        BESU_OPTS: process.env.BESU_OPTS || "-Xms256m -Xmx768m"
      },
      stdio: ["ignore", logFd, logFd]
    });
    fs.closeSync(logFd);
  }

  async startAll() {
    this.generateNetwork();
    this.nodes.forEach((_, index) => this.startNode(index));
    await waitFor("all Besu JSON-RPC endpoints", async () => {
      let ready = 0;
      for (const node of this.nodes) {
        try {
          const chainId = await rpc(`http://127.0.0.1:${node.rpcPort}`, "eth_chainId");
          if (Number(BigInt(chainId)) === 13371) ready += 1;
        } catch {
          // Continue polling.
        }
      }
      return ready === 4;
    });
    await this.waitForBlockAdvance();
    this.provider = new ethers.JsonRpcProvider(`http://127.0.0.1:${this.nodes[0].rpcPort}`, 13371, {
      staticNetwork: true
    });
    this.admin = new ethers.Wallet(ADMIN_PRIVATE_KEY, this.provider);
  }

  async blockNumber() {
    return Number(BigInt(await rpc(`http://127.0.0.1:${this.nodes[0].rpcPort}`, "eth_blockNumber")));
  }

  async waitForBlockAdvance(timeoutMs = STARTUP_TIMEOUT_MS) {
    const before = await this.blockNumber().catch(() => 0);
    return waitFor(
      "QBFT block production",
      async () => (await this.blockNumber()) > before,
      timeoutMs,
      250
    );
  }

  async stopNode(index) {
    await stopChild(this.nodes[index].child, this.nodes[index].name);
  }

  async restartNode(index) {
    this.startNode(index);
    await waitFor(`${this.nodes[index].name} JSON-RPC`, async () => {
      try {
        return Number(BigInt(await rpc(`http://127.0.0.1:${this.nodes[index].rpcPort}`, "eth_chainId"))) === 13371;
      } catch {
        return false;
      }
    });
  }

  async deploy() {
    const factory = new ethers.ContractFactory(
      this.artifact.abi,
      this.artifact.bytecode,
      this.admin
    );
    const startedAtUtc = nowUtc();
    const startNs = process.hrtime.bigint();
    const contract = await factory.deploy(this.admin.address, { gasLimit: 4000000n });
    const tx = contract.deploymentTransaction();
    const receipt = await tx.wait(1);
    const address = await contract.getAddress();
    const runtimeCode = await this.provider.getCode(address);
    if (receipt.status !== 1 || runtimeCode === "0x") throw new Error("QBFT contract deployment failed");
    this.contract = contract;
    this.deployment = {
      started_at_utc: startedAtUtc,
      first_inclusion_latency_ms: elapsedMs(startNs),
      address,
      transaction_hash: receipt.hash,
      block_number: receipt.blockNumber,
      block_hash: receipt.blockHash,
      gas_used: receipt.gasUsed.toString(),
      runtime_code_keccak256: ethers.keccak256(runtimeCode)
    };
    return this.deployment;
  }

  parseAnchor(receipt) {
    for (const log of receipt.logs) {
      try {
        const parsed = this.contract.interface.parseLog(log);
        if (parsed && parsed.name === "Stage3Anchored") return parsed;
      } catch {
        // Ignore unrelated logs.
      }
    }
    return null;
  }

  async commit(scenario, index) {
    const payload = JSON.stringify({
      session_id: SESSION_ID,
      family: "qbft",
      scenario,
      index,
      nonce: crypto.randomBytes(8).toString("hex")
    });
    const commitment = `0x${sha256(payload)}`;
    const evidenceHash = `0x${sha256(`evidence:${payload}`)}`;
    const startedAtUtc = nowUtc();
    const startNs = process.hrtime.bigint();
    const tx = await this.contract.commit(commitment, evidenceHash, { gasLimit: 180000n });
    const receipt = await tx.wait(1);
    const event = this.parseAnchor(receipt);
    if (receipt.status !== 1 || !event) {
      throw new Error(`QBFT ${scenario} observation ${index} did not produce a valid receipt/event`);
    }
    if (
      event.args.commitment.toLowerCase() !== commitment.toLowerCase() ||
      event.args.evidenceHash.toLowerCase() !== evidenceHash.toLowerCase()
    ) {
      throw new Error(`QBFT ${scenario} observation ${index} event mismatch`);
    }
    return {
      index,
      started_at_utc: startedAtUtc,
      first_inclusion_latency_ms: elapsedMs(startNs),
      payload,
      commitment,
      evidence_hash: evidenceHash,
      transaction_hash: receipt.hash,
      block_number: receipt.blockNumber,
      block_hash: receipt.blockHash,
      gas_used: receipt.gasUsed.toString(),
      receipt_status: receipt.status,
      event_valid: true
    };
  }

  async collectCommits(scenario, count) {
    const observations = [];
    for (let index = 0; index < count; index += 1) {
      observations.push(await this.commit(scenario, index));
    }
    return observations;
  }

  async rejectionProbes() {
    const duplicatePayload = `security:${SESSION_ID}:duplicate`;
    const commitment = `0x${sha256(duplicatePayload)}`;
    const evidenceHash = `0x${sha256(`evidence:${duplicatePayload}`)}`;
    const accepted = await this.contract.commit(commitment, evidenceHash, { gasLimit: 180000n });
    await accepted.wait(1);

    async function rejected(label, action) {
      try {
        await action();
        return { probe: label, rejected: false, error: null };
      } catch (error) {
        return { probe: label, rejected: true, error: String(error.shortMessage || error.message) };
      }
    }

    const unauthorized = new ethers.Wallet(UNAUTH_PRIVATE_KEY, this.provider);
    return [
      await rejected("duplicate_commitment", () =>
        this.contract.commit.staticCall(commitment, evidenceHash)
      ),
      await rejected("zero_commitment", () =>
        this.contract.commit.staticCall(ethers.ZeroHash, evidenceHash)
      ),
      await rejected("unauthorized_submitter", () =>
        this.contract.connect(unauthorized).commit.staticCall(
          `0x${sha256(`security:${SESSION_ID}:unauthorized`)}`,
          evidenceHash
        )
      )
    ];
  }

  async stalledBlockProbes(count) {
    const observations = [];
    for (let index = 0; index < count; index += 1) {
      const startedAtUtc = nowUtc();
      const blockNumber = await this.blockNumber();
      observations.push({ index, started_at_utc: startedAtUtc, block_number: blockNumber });
      if (index + 1 < count) await sleep(PROBE_INTERVAL_MS);
    }
    const first = observations[0].block_number;
    const last = observations[observations.length - 1].block_number;
    if (last !== first) {
      throw new Error(`QBFT advanced from block ${first} to ${last} with only 2/4 validators active`);
    }
    return observations;
  }

  async stopAll() {
    for (const node of [...this.nodes].reverse()) {
      await stopChild(node.child, node.name);
    }
  }
}

async function collectRaft() {
  const cluster = new EtcdCluster();
  try {
    await cluster.startAll();
    for (let index = 0; index < WARMUPS; index += 1) {
      cluster.put("warmup", index, true);
    }
    const baseline = await cluster.collectWrites("baseline", REPEATS);

    const initialLeader = cluster.leaderIndex();
    const follower = [0, 1, 2].find((index) => index !== initialLeader);
    await cluster.stopMember(follower);
    await sleep(1000);
    const followerOffline = await cluster.collectWrites("one_follower_offline", REPEATS);
    await cluster.restartMember(follower);
    await cluster.waitHealthy(3);

    const leader = cluster.leaderIndex();
    const failoverStartUtc = nowUtc();
    const failoverStartNs = process.hrtime.bigint();
    await cluster.stopMember(leader);
    let failoverAttempts = 0;
    await waitFor(
      "Raft leader failover and first committed write",
      () => {
        failoverAttempts += 1;
        return cluster.put("leader_failover_probe", failoverAttempts, true);
      },
      RECOVERY_TIMEOUT_MS,
      200
    ).catch((error) => {
      // waitFor expects a false predicate during the election, but put() is strict.
      throw error;
    });
    const leaderFailover = {
      stopped_member: cluster.members[leader].name,
      started_at_utc: failoverStartUtc,
      recovery_ms: elapsedMs(failoverStartNs),
      attempts: failoverAttempts,
      replacement_leader: cluster.members[cluster.leaderIndex()].name
    };
    const postLeaderFailover = await cluster.collectWrites("post_leader_failover", REPEATS);
    await cluster.restartMember(leader);
    await cluster.waitHealthy(3);

    const currentLeader = cluster.leaderIndex();
    const stoppedForMajorityLoss = [0, 1, 2].filter((index) => index !== currentLeader);
    for (const index of stoppedForMajorityLoss) await cluster.stopMember(index);
    await sleep(1500);
    const majorityLoss = await cluster.collectWrites("majority_loss", REPEATS, false);

    const recoveryStartUtc = nowUtc();
    const recoveryStartNs = process.hrtime.bigint();
    for (const index of stoppedForMajorityLoss) await cluster.restartMember(index);
    await cluster.waitHealthy(3);
    const recovery = {
      started_at_utc: recoveryStartUtc,
      recovery_ms: elapsedMs(recoveryStartNs),
      healthy_members: cluster.healthyEndpoints()
    };
    const recovered = await cluster.collectWrites("recovered", REPEATS);

    return {
      implementation: "etcd/Raft",
      cluster_size: 3,
      fault_model_measured: "process crash/non-participation and quorum loss",
      byzantine_faults_measured: false,
      binary_version: mustRun(ETCD_BIN, ["--version"]).stdout.split("\n")[0],
      binary_sha256: sha256File(ETCD_BIN),
      etcdctl_sha256: sha256File(ETCDCTL_BIN),
      configuration: {
        client_endpoints: cluster.endpoints,
        peer_ports: cluster.members.map((member) => member.peerPort)
      },
      lifecycle: { initial_leader: cluster.members[initialLeader].name, leader_failover: leaderFailover, recovery },
      observations: {
        baseline,
        one_follower_offline: followerOffline,
        post_leader_failover: postLeaderFailover,
        majority_loss: majorityLoss,
        recovered
      }
    };
  } finally {
    await cluster.stopAll();
  }
}

async function collectQbft(artifact) {
  const cluster = new BesuCluster(artifact);
  try {
    await cluster.startAll();
    const deployment = await cluster.deploy();
    const rejectionProbes = await cluster.rejectionProbes();
    if (!rejectionProbes.every((probe) => probe.rejected)) {
      throw new Error("One or more QBFT contract negative-security probes did not reject");
    }
    for (let index = 0; index < WARMUPS; index += 1) {
      await cluster.commit("warmup", index);
    }
    const baseline = await cluster.collectCommits("baseline", REPEATS);

    await cluster.stopNode(3);
    await cluster.waitForBlockAdvance(RECOVERY_TIMEOUT_MS);
    const oneValidatorOffline = await cluster.collectCommits("one_validator_offline", REPEATS);

    await cluster.stopNode(2);
    await sleep(2000);
    const twoValidatorsOffline = await cluster.stalledBlockProbes(REPEATS);

    const recoveryStartUtc = nowUtc();
    const recoveryStartNs = process.hrtime.bigint();
    // After >1/3 validator loss, Besu QBFT round timeouts back off
    // exponentially. Restore quorum and restart the three active validators
    // to reset their round timers, following Besu's documented procedure.
    await cluster.stopNode(0);
    await cluster.stopNode(1);
    await cluster.restartNode(0);
    await cluster.restartNode(1);
    await cluster.restartNode(2);
    await cluster.waitForBlockAdvance(RECOVERY_TIMEOUT_MS);
    const recovery = {
      started_at_utc: recoveryStartUtc,
      recovery_ms: elapsedMs(recoveryStartNs),
      method:
        "operator-assisted active-validator restart after quorum restoration",
      round_timeout_reset: true,
      restarted_validators: ["qbft1", "qbft2", "qbft3"],
      active_validators_when_progress_resumed: 3
    };
    await cluster.restartNode(3);
    await cluster.waitForBlockAdvance(RECOVERY_TIMEOUT_MS);
    const recovered = await cluster.collectCommits("recovered", REPEATS);

    return {
      implementation: "Hyperledger Besu/QBFT",
      chain_id: 13371,
      cluster_size: 4,
      validator_threshold: "at least 3 of 4 participating validators",
      fault_model_measured: "validator process crash/non-participation and quorum loss",
      byzantine_faults_measured: false,
      arbitrary_byzantine_messages_or_equivocation_injected: false,
      binary_version: mustRun(BESU_BIN, ["--version"]).stdout.split("\n")[0],
      binary_sha256: sha256File(BESU_BIN),
      configuration: {
        block_period_seconds: 1,
        request_timeout_seconds: 4,
        epoch_length: 30000,
        rpc_ports: cluster.nodes.map((node) => node.rpcPort),
        p2p_ports: cluster.nodes.map((node) => node.p2pPort)
      },
      contract: {
        name: "Stage3AnomalyLedger",
        source_sha256: sha256File(path.join(REPO_ROOT, "contracts", "l4", "Stage3AnomalyLedger.sol")),
        creation_bytecode_keccak256: ethers.keccak256(artifact.bytecode),
        deployed: deployment,
        security_probes: rejectionProbes
      },
      lifecycle: { recovery },
      observations: {
        baseline,
        one_validator_offline: oneValidatorOffline,
        two_validators_offline_block_probes: twoValidatorsOffline,
        recovered
      }
    };
  } finally {
    await cluster.stopAll();
  }
}

function writeChecksums() {
  const files = [];
  function visit(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const full = path.join(directory, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile() && entry.name !== "SHA256SUMS.txt") files.push(full);
    }
  }
  visit(OUTPUT_DIR);
  files.sort();
  const lines = files.map(
    (filePath) => `${sha256File(filePath)}  ${path.relative(OUTPUT_DIR, filePath)}`
  );
  fs.writeFileSync(path.join(OUTPUT_DIR, "SHA256SUMS.txt"), `${lines.join("\n")}\n`);
}

async function main() {
  assertSafeSessionId(SESSION_ID);
  for (const binary of [ETCD_BIN, ETCDCTL_BIN, BESU_BIN]) {
    if (!fs.existsSync(binary)) {
      throw new Error(`Missing ${binary}; run npm run install:permissioned first`);
    }
  }
  if (fs.existsSync(OUTPUT_DIR)) throw new Error(`Output directory already exists: ${OUTPUT_DIR}`);
  if (fs.existsSync(RUNTIME_DIR)) throw new Error(`Runtime directory already exists: ${RUNTIME_DIR}`);
  fs.mkdirSync(LOG_DIR, { recursive: true });
  fs.mkdirSync(RUNTIME_DIR, { recursive: true });

  const git = gitMetadata();
  const startedAtUtc = nowUtc();
  console.log(`[${startedAtUtc}] compiling Stage3AnomalyLedger`);
  mustRun(path.join(REPO_ROOT, "node_modules", ".bin", "hardhat"), ["compile", "--config", "hardhat.consensus.config.js"], {
    timeout: 300000
  });
  const artifactPath = path.join(
    REPO_ROOT,
    ".hardhat-consensus",
    "artifacts",
    "contracts",
    "l4",
    "Stage3AnomalyLedger.sol",
    "Stage3AnomalyLedger.json"
  );
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));

  const evidence = {
    schema: "zktrustllm.permissioned-consensus-fault-evidence.v2",
    session_id: SESSION_ID,
    started_at_utc: startedAtUtc,
    completed_at_utc: null,
    publication_eligible: git.clean && REPEATS >= 30 && WARMUPS >= 3,
    smoke_or_dirty_run: !git.clean || REPEATS < 30 || WARMUPS < 3,
    claim_boundary: {
      raft_qbft_absolute_latency_directly_comparable: false,
      reason: "etcd key/value replication and EVM contract execution are different workloads",
      byzantine_faults_measured: false,
      qbft_fault_interpretation:
        "stopped validators measure crash/non-participation and quorum loss, not equivocation or arbitrary Byzantine messages"
    },
    parameters: {
      repeats: REPEATS,
      warmups_excluded: WARMUPS,
      probe_interval_ms: PROBE_INTERVAL_MS,
      startup_timeout_ms: STARTUP_TIMEOUT_MS,
      recovery_timeout_ms: RECOVERY_TIMEOUT_MS
    },
    git,
    host: hostMetadata(),
    implementation_hashes: {
      runner_sha256: sha256File(__filename),
      analyzer_sha256: sha256File(
        path.join(REPO_ROOT, "scripts", "l4", "consensus", "analyze_permissioned_faults.py")
      ),
      package_json_sha256: sha256File(path.join(REPO_ROOT, "package.json")),
      artifact_json_sha256: sha256File(artifactPath)
    },
    raft: null,
    qbft: null
  };

  try {
    console.log(`[${nowUtc()}] running real three-member etcd/Raft scenarios`);
    evidence.raft = await collectRaft();
    console.log(`[${nowUtc()}] running real four-validator Besu/QBFT scenarios`);
    evidence.qbft = await collectQbft(artifact);
    evidence.completed_at_utc = nowUtc();
    fs.writeFileSync(path.join(OUTPUT_DIR, "benchmark.json"), `${JSON.stringify(evidence, null, 2)}\n`);
    writeChecksums();
    console.log(`[${evidence.completed_at_utc}] completed: ${OUTPUT_DIR}`);
  } catch (error) {
    evidence.completed_at_utc = nowUtc();
    evidence.failure = {
      message: String(error.message || error),
      stack: String(error.stack || "")
    };
    fs.writeFileSync(path.join(OUTPUT_DIR, "failure.json"), `${JSON.stringify(evidence, null, 2)}\n`);
    writeChecksums();
    throw error;
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
