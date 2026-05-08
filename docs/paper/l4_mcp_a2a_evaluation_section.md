# Level 4 Evaluation: MCP/A2A Reference-Bound Proof-Governed Coordination

## 1. Evaluation Objective

The Level 4 objective is to evaluate whether multi-agent coordination can be made more trustworthy and efficient by combining:

- A2A compact reference exchange,
- MCP structured context/tool access,
- blockchain-authenticated shared state,
- AUTH_V2.3 reference-bound zero-knowledge proof verification,
- agent-side and network-side KPI analysis.

The core research question is:

How can Agentic AI systems coordinate over authenticated blockchain state using compact references, while preserving proof-governed policy admissibility and measurable control-plane performance?

## 2. Level 4 Architecture

The Level 4 workflow extends the earlier ZKTrustLLM architecture from decision attestation to reference-bound multi-agent coordination.

The implemented workflow is:

1. An agent creates a proof-backed AUTH_V2.3 decision.
2. The decision is bound to a reference-aware coordination context.
3. A2A coordination exchanges compact references rather than full raw context.
4. MCP tools retrieve authenticated blockchain context behind the reference.
5. The receiving agent verifies that the reference, decision, policy, trust state, and proof-bound context are consistent.
6. Network-facing KPIs evaluate control-message size, response time, jitter, packet loss, containment time, interruption time, and recovery time.

This structure aligns with the Level 4 concept where blockchain acts as authenticated shared memory, MCP acts as structured context access, and A2A acts as the inter-agent coordination layer.

## 3. Relationship Between MCP, A2A, Blockchain, and ZK

MCP and A2A play complementary roles.

A2A provides the inter-agent coordination channel. In the Level 4 design, A2A messages carry compact authenticated references such as reference IDs, decision IDs, trace commitments, capability IDs, and context hashes.

MCP provides the context retrieval and tool-access layer. A receiving agent uses MCP tools to resolve the compact reference into authenticated blockchain context and verify the corresponding decision bundle.

Blockchain provides authenticated shared state. It stores decision records, policy commitments, reference bindings, proof-verification records, and coordination-relevant state.

AUTH_V2.3 provides reference-bound proof governance. It binds the agent decision to the MCP/A2A reference context using a reference context hash, coordination session ID, binding nonce, and trace commitment.

## 4. Evaluation Scenarios

The evaluation considers three scenarios.

### 4.1 Baseline Direct Agent

The baseline direct-agent scenario uses direct agent control without blockchain-authenticated state, MCP context retrieval, A2A reference verification, or proof-governed admissibility.

This scenario has the smallest control-message size, but it does not provide proof-governed policy admissibility, reference binding, or authenticated auditability.

### 4.2 L4 Raw Context

The L4 raw-context scenario uses Level 4 proof-governed coordination, but agents exchange expanded context payloads.

This scenario provides proof governance and stronger security properties, but it increases inter-agent control-message size.

### 4.3 L4 Reference MCP/A2A

The L4 reference scenario uses compact A2A references and MCP-based context resolution.

This is the target Level 4 design. It preserves proof-governed and reference-bound semantics while reducing inter-agent control-message size compared with L4 raw-context coordination.

## 5. Agent-Side KPIs

The agent-side KPIs are designed to evaluate whether agents can retrieve, verify, and act on authenticated context correctly.

The measured agent-side KPIs include:

- MCP context retrieval success rate,
- MCP tool invocation latency,
- MCP reference-bundle verification latency,
- A2A reference validity,
- policy admissibility observation,
- trust-aware action observation,
- reference reuse ratio,
- coordination compression gain,
- unauthorized/tampered rejection rate,
- invalid-context rejection rate.

The measured MCP context retrieval success rate was 1.0, with five successful MCP tool calls out of five. The average MCP tool invocation latency was 29.711 ms, the maximum tool invocation latency was 39.757 ms, and the reference-bundle verification latency was 32.298 ms.

## 6. AUTH_V2.3 Reference-Bound Proof Result

AUTH_V2.3 extends AUTH_V2.2 by adding explicit reference binding.

The proof binds:

- agent identity,
- capability ID,
- policy class hash,
- action class,
- context hash,
- trace commitment,
- expiry bucket,
- policy admissibility flag,
- trust state,
- reference context hash,
- coordination session ID,
- proof output.

The successful AUTH_V2.3 localhost result produced:

- decision ID: 1,
- proof output: 1,
- policy admissibility flag: 1,
- trust state: 3,
- action class: 3,
- gas used: 671779,
- reference context hash: 13910625391943923264185798681093047247761942130660331693554321209527545263200,
- coordination session ID: 12343182470573131826629052782455202610058935007512043442711127914022411250849.

This demonstrates that the decision is not only proof-backed and trust-state-aware, but also bound to the MCP/A2A coordination context.

## 7. Negative-Security Results

The negative-security tests demonstrate that invalid or tampered coordination paths are rejected.

AUTH_V2.3 negative tests covered:

- tampered action class,
- tampered policy admissibility flag,
- tampered trust state,
- tampered reference context hash,
- tampered coordination session ID,
- tampered proof output,
- wrong verifier input length.

The AUTH_V2.3 negative-security result was:

- negative cases tested: 7,
- negative cases passed: 7,
- unauthorized/tampered rejection rate: 1.0.

MCP/A2A negative tests covered:

- invalid AUTH_V2.2 decision lookup,
- invalid A2A reference lookup,
- invalid A2A reference validity check,
- invalid reference-bundle verification.

The MCP/A2A invalid-context result was:

- negative cases tested: 4,
- negative cases passed: 4,
- invalid-context rejection rate: 1.0.

These results show that the design accepts valid reference-bound proof paths while rejecting malformed, tampered, or invalid coordination attempts.

## 8. Network-Facing KPI Results

The Step 83 evaluation introduced a deterministic network KPI telemetry-emulation layer. These results are not yet live VLC/DTLS/RTP measurements, but they provide a reproducible network-facing evaluation framework derived from measured MCP/A2A control values.

The measured/derived inputs were:

- raw A2A message bytes: 1239,
- reference A2A message bytes: 680,
- MCP average tool invocation latency: 29.711 ms,
- MCP bundle verification latency: 32.298 ms,
- AUTH_V2.3 gas used: 671779,
- AUTH_V2.3 tampered rejection rate: 1.0,
- MCP/A2A invalid-context rejection rate: 1.0.

The L4 reference mode achieved:

- 45.12% control-message reduction compared with L4 raw-context coordination,
- 15.31% lower control-response time compared with L4 raw-context coordination,
- 16.73% lower jitter compared with L4 raw-context coordination,
- 20.81% lower packet loss compared with L4 raw-context coordination,
- 23.35% lower service interruption compared with the baseline direct-agent scenario.

These results suggest that compact authenticated references can reduce inter-agent control-message overhead while preserving proof-governed and reference-bound decision semantics.

## 9. Interpretation

The main observation is that L4 reference-based coordination improves the balance between security and efficiency.

Compared with baseline direct-agent control, L4 introduces additional proof and verification overhead, but provides stronger security properties:

- blockchain-authenticated state,
- proof-governed policy admissibility,
- reference-bound decision context,
- tampered input rejection,
- invalid-context rejection,
- auditable coordination state.

Compared with L4 raw-context coordination, L4 reference-based coordination reduces inter-agent control-message size and improves the emulated network-facing KPIs.

Therefore, the Level 4 result should be presented as a security-efficiency trade-off: the system introduces bounded control-plane overhead to obtain stronger trust, auditability, and policy-governed multi-agent coordination.

## 10. Limitations

The current Step 83 network KPI values are deterministic telemetry-emulation results. They are derived from measured MCP/A2A values but are not yet collected from live VLC, DTLS, RTP, multicast, or network-emulator experiments.

The current implementation uses a localhost Hardhat environment. Therefore, gas values and transaction confirmation behaviour should be interpreted as reproducibility and contract-cost indicators, not as public-chain latency measurements.

The current proof relation is intentionally bounded. AUTH_V2.3 demonstrates a reference-bound proof path for a restricted trust state and isolate action. Future versions should generalise to additional trust states, actions, and policy classes.

## 11. Next Experimental Step

The next step is to replace deterministic telemetry-emulation with live or emulated network measurements.

The recommended next experiment is:

1. Run a baseline DTLS/RTP or UDP multimedia session.
2. Run L4 raw-context coordination.
3. Run L4 reference-based MCP/A2A coordination.
4. Collect real control response time, jitter, packet loss, containment time, service interruption, and recovery time.
5. Compare baseline, L4 raw-context, and L4 reference modes.

This will move the evaluation from control-plane reproducibility to multimedia network validation.

## 12. Research Claim

The Level 4 prototype supports the following research claim:

A proof-governed MCP/A2A coordination architecture can enable Agentic AI systems to coordinate using compact references to blockchain-authenticated shared state, while preserving policy admissibility, reference-bound decision semantics, auditability, and measurable control-plane performance.


## 13. Benchmark Figure Analysis

Following supervisor feedback, two additional benchmark figures were added to make the Level 4 result presentation clearer.

### Figure 5.3: Agent Scaling of Level 4 Coordination

Figure 5.3 compares coordination latency under increasing agent numbers.

The evaluated methods are:

- Direct agent baseline,
- Heuristic policy agent,
- L4 raw-context coordination,
- Proposed L4-ref MCP/A2A coordination.

The result shows that L4 raw-context coordination has higher scaling cost because larger context payloads are exchanged between agents. The proposed L4-ref MCP/A2A method reduces this cost by exchanging compact authenticated references and resolving context through MCP.

### Figure 5.4: Decision Utility across Agent Positions

Figure 5.4 compares decision utility across representative agent positions.

The proposed L4-ref MCP/A2A method achieves the highest and most stable utility because agent decisions are supported by authenticated blockchain state, MCP context retrieval, compact A2A reference exchange, AUTH_V2.3 reference-bound proof verification, and negative-security rejection guarantees.

### Interpretation

The benchmark figures support the security-efficiency argument of the Level 4 design.

The direct-agent baseline has lower simple control overhead but lacks proof governance and authenticated state verification. L4 raw-context coordination improves trust but increases coordination cost. The proposed L4-ref MCP/A2A design provides a stronger balance by reducing raw coordination overhead while preserving proof-governed and reference-bound decision semantics.

The current figures are deterministic benchmark/emulation figures. They should be replaced or extended with live DTLS/RTP/VLC telemetry in the next experimental stage.

## 14. Semi-Live Control-Plane Telemetry

Step 86 adds semi-live measured MCP/A2A control-plane telemetry. Unlike the deterministic Step 83 telemetry-emulation, this experiment measures actual repeated local MCP tool invocation and control-loop timings.

The experiment compares:

- baseline direct-agent control,
- L4 raw-context MCP/A2A coordination,
- proposed L4-ref MCP/A2A coordination.

The measured KPIs include control response time, p50 and p95 response time, control-loop jitter, control-message size, and success rate.

Across 20 runs per mode, the L4 raw-context path achieved an average control response time of 72.793 ms, while the proposed L4-ref MCP/A2A path achieved an average control response time of 34.918 ms. This corresponds to a 52.03% latency reduction compared with L4 raw-context coordination.

The measured average control-message size also decreased from 3477.25 bytes in the L4 raw-context path to 72.55 bytes in the L4-ref MCP/A2A path, corresponding to a 97.91% control-message reduction.

This step strengthens the evaluation by moving from deterministic emulation toward live measured control-plane behaviour. However, the results are still not live VLC/DTLS/RTP media measurements. They should be interpreted as semi-live control-plane telemetry and used as a bridge toward full multimedia/network validation.

## 15. Multi-Agent Scaling Telemetry

Step 87 extends the semi-live control-plane evaluation by measuring MCP/A2A coordination under increasing agent counts.

The experiment evaluates 5, 10, 15, 20, and 25 agents, with three repetitions per setting. The compared modes are baseline direct-agent control, L4 raw-context coordination, and proposed L4-ref MCP/A2A coordination.

The measured KPIs include total coordination latency, latency per agent, p50 and p95 latency, jitter, control-message size, accepted agents per second, and success rate.

The purpose of this experiment is to show how compact reference-based coordination scales compared with raw-context coordination. In the raw-context mode, each agent triggers MCP retrieval of the source decision, A2A reference, and reference bundle. In the proposed L4-ref mode, each agent exchanges a compact reference and verifies the authenticated bundle through MCP.

The measured result shows that L4-ref MCP/A2A reduces latency by 52.40% to 58.50% compared with L4 raw-context coordination across 5 to 25 agents. It also reduces control-message size by approximately 97.74% to 97.76% across all tested agent counts.

The throughput gain of the L4-ref mode ranges from 110.02% to 139.83% compared with the raw-context mode. This supports the claim that compact authenticated references improve multi-agent coordination scalability while preserving proof-governed, blockchain-authenticated decision semantics.

These results remain semi-live control-plane measurements. They are not yet live VLC/DTLS/RTP media-plane measurements.

## 16. Live RTP Media-Plane Telemetry

Step 89 extends the Level 4 evaluation from control-plane telemetry to live RTP media-plane measurement.

The experiment streams a deterministic 30-second H.264 test video over RTP on localhost and captures RTP packets using a Python UDP receiver. The receiver extracts RTP sequence numbers, RTP timestamps, packet sizes, and packet arrival times.

The measured RTP media-plane results show 2328 received packets, 2328 expected packets, 0 lost packets, and 0.0% packet loss during the 25-second capture window. The average bitrate was 833.605 kbps. The average jitter component was 0.229169 ms, with a p50 jitter component of 0.069357 ms and a maximum jitter component of 4.163946 ms.

These results provide the first live media-plane validation layer for the Level 4 architecture. Earlier steps established proof-governed MCP/A2A control-plane behaviour, reference-bound decision verification, negative-security rejection, and multi-agent scaling. Step 89 adds direct RTP packet-level evidence, which is necessary for connecting agentic control decisions to multimedia delivery behaviour.

This step is intentionally limited to RTP media-plane telemetry. The next experimental step should add DTLS-secured RTP validation, so that the media-plane KPIs can be compared under unsecured RTP and DTLS-protected RTP transport.

## 17. DTLS-Wrapped RTP Media-Plane Validation

Step 90 extends the Step 89 plain RTP media-plane baseline by adding DTLS protection around RTP delivery.

The experiment uses a local DTLS tunnel/proxy. FFmpeg sends RTP packets to a DTLS client proxy. The client protects each RTP packet as a DTLS record and sends it to a DTLS server proxy. The server recovers the RTP packet and forwards it to a local RTP receiver for packet-level telemetry.

The DTLS handshake completed successfully using the PSK identity `zktrustllm-l4-client`. The recovered RTP receiver captured 769 packets during the measurement window, with 0 lost packets and 0.0% packet loss. The measured recovered bitrate was 102.17 kbps.

For jitter, the result uses arrival-gap jitter rather than raw RTP timestamp-delta jitter. This is necessary because H.264 RTP timestamps can appear non-monotonic in packet capture order due to frame ordering. Arrival-gap jitter gives a safer media-plane timing metric for this controlled DTLS tunnel baseline.

This step is important because it provides the first secured media-plane validation layer for the Level 4 workflow. Earlier steps measured proof-governed MCP/A2A control behaviour, negative-security rejection, multi-agent scaling, and plain RTP delivery. Step 90 shows that RTP packets can also be carried through a DTLS-protected tunnel and measured after recovery.

## 18. Network-Impairment Evaluation: Plain RTP vs DTLS-Wrapped RTP

Step 91 extends the media-plane evaluation by introducing controlled network impairment.

The experiment compares plain RTP and DTLS-wrapped RTP under multiple loopback impairment profiles. The impairment profiles include clean baseline delivery, fixed delay, delay with jitter, and delay with jitter plus packet loss.

The measured KPIs include RTP packet continuity, packet loss, bitrate, and arrival-gap jitter. Arrival-gap jitter is used because raw RTP timestamp deltas can produce misleading artefacts for H.264 packet streams.

This step is important because the previous media-plane experiments validated RTP delivery under clean localhost conditions. Step 91 moves the evaluation closer to realistic network behaviour by adding delay, jitter, and loss.

The results are stored in `results/l4_network_impairment/` and can support the journal-level claim that the Level 4 workflow connects proof-governed MCP/A2A control decisions with measurable secure multimedia delivery behaviour.
