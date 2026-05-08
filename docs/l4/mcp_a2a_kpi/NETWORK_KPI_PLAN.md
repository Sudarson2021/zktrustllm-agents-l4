# Network KPI Plan for MCP/A2A Level 4

## Purpose

This document defines the network-facing KPIs required to evaluate Level 4 MCP/A2A orchestration in a 5G/6G multimedia context.

## Current Status

The current implementation measures agent/control-plane KPIs:

- A2A reference validity,
- A2A reference gas,
- MCP context retrieval success rate,
- MCP tool invocation latency,
- MCP bundle verification latency,
- reference-vs-raw message size,
- coordination compression gain.

The next step is to add media/network telemetry.

## Required Network KPIs

| KPI | Measurement method | Required instrumentation |
|---|---|---|
| Control response time | mitigation applied timestamp - event detected timestamp | event logs and policy action logs |
| Control message size | bytes per MCP/A2A/control message | JSON payload size logging |
| Control-plane overhead ratio | L4 control bytes / baseline control bytes | baseline and L4 control logs |
| Jitter during control event | RTP/VLC jitter during action window | VLC/RTP logs or network emulator |
| Packet loss during orchestration | packet loss during proof/control action window | RTP/UDP counters or emulator |
| Containment time | isolate/rekey completed timestamp - trust alarm timestamp | action execution logs |
| Service continuity impact | interruption time, frame loss, rebuffering | VLC playback logs |
| Recovery time | stable time after control action - action applied time | post-action network/media logs |

## Proposed Experiment

The recommended next experiment is:

1. Run baseline media/control session without L4.
2. Run L4-raw session where agents exchange expanded context.
3. Run L4-ref session where agents exchange compact references.
4. Use MCP to resolve authenticated context.
5. Compare control message size, response time, jitter, packet loss, containment time, and service continuity.

## Expected Result

L4-ref is expected to reduce control message size and redundant inter-agent payload exchange compared with L4-raw, while preserving stronger auditability and policy admissibility.

The live media path remains off-chain, so jitter and packet-loss impact should remain bounded.
