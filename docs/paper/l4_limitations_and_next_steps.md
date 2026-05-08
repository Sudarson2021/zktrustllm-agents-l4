# Level 4 Limitations and Next Steps

## Current Limitations

### 1. Localhost Blockchain Environment

The current prototype uses a localhost Hardhat chain. This is suitable for reproducibility, contract testing, and controlled experimentation, but does not represent public-chain or production consortium-chain latency.

### 2. Deterministic Telemetry-Emulation

The Step 83 network KPI results are deterministic telemetry-emulation results derived from measured MCP/A2A control values. They are not yet live VLC, DTLS, RTP, multicast, or network-emulator measurements.

### 3. Bounded AUTH_V2.3 Relation

AUTH_V2.3 currently demonstrates a bounded trust-state/action relation. It verifies a restricted trust state and isolate action. Future work should generalise the relation to multiple trust states and policy actions.

### 4. Single Reference-Bound Demonstration

The current result demonstrates one successful reference-bound decision path. Future experiments should scale to multiple agents, multiple references, and repeated coordination sessions.

### 5. Limited Adversarial Model

The negative-security tests cover tampered inputs, invalid references, and invalid context lookups. Future work should extend this to collusion, Sybil-style behaviour, stale-but-valid references, replay attempts, and malicious MCP/A2A tool responses.

## Next Steps

### Step 85: Live Network Telemetry Integration

Replace deterministic telemetry-emulation with live or emulated network traces.

Recommended measurements:

- DTLS/RTP jitter,
- packet loss,
- control response time,
- containment time,
- service interruption,
- recovery time.

### Step 86: Multi-Agent Scaling Experiment

Evaluate the system under multiple agents and repeated reference exchanges.

Recommended variables:

- number of agents,
- number of references,
- reference reuse ratio,
- MCP retrieval load,
- A2A coordination latency,
- verification throughput.

### Step 87: Extended AUTH_V2.4 Policy Matrix

Extend AUTH_V2.3 to support a wider policy matrix.

Example trust-state/action mappings:

- normal -> allow,
- watch -> monitor,
- restricted -> isolate,
- compromised -> revoke,
- recovery -> rekey.

### Step 88: Journal Paper Integration

Convert the Level 4 evaluation into the journal paper structure:

1. Introduction and motivation.
2. Related work.
3. System model and threat model.
4. Level 4 architecture.
5. AUTH_V2.3 proof relation.
6. MCP/A2A coordination model.
7. Evaluation and results.
8. Discussion and limitations.
9. Conclusion.
