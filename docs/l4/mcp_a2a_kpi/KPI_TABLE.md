# KPI Table for MCP/A2A over Level 4

## Agent KPIs

| KPI | Definition | Current status | Expected direction |
|---|---|---|---|
| MCP context retrieval success rate | successful MCP tool/context calls / total MCP tool/context calls | Measured | Should approach 1.0 in controlled setup |
| MCP tool invocation latency | time to call MCP tool and receive response | Measured | Should remain bounded |
| MCP reference-bundle verification latency | time to verify A2A reference against source AUTH_V2.2 decision | Measured | Should remain bounded |
| A2A reference validity | whether reference exists and is valid | Measured | Should be true for valid references |
| Policy admissibility observation | whether accepted decision has admissibility flag = 1 | Measured | Should be true for accepted proof-backed decisions |
| Trust-aware action precision | whether trust state maps to intended action class | Measured for AUTH_V2.2 path | Should be high |
| Reference reuse ratio | reference-only A2A messages / total A2A messages | Derived single-run | Should increase in mature L4 |
| Coordination compression gain | 1 - reference-message-bytes / raw-message-bytes | Derived | L4-ref should outperform L4-raw |
| Unauthorized rejection rate | invalid requests rejected / total invalid requests | Future negative-test KPI | Should approach 1.0 |
| Agent agreement rate | consistent agent outputs / total agent runs | Future multi-agent KPI | Should improve with shared authenticated state |

## Network KPIs

| KPI | Definition | Current status | Expected direction |
|---|---|---|---|
| A2A control message size | size of inter-agent coordination message | Derived | L4-ref should be smaller than L4-raw |
| Control-plane overhead ratio | L4 control bytes / baseline control bytes | Derived/planned | Should remain bounded |
| Control response time | mitigation applied time - event detected time | Future telemetry KPI | Should remain below mitigation budget |
| Control-channel utilisation | control traffic / available control bandwidth | Future telemetry KPI | Should scale better with L4-ref |
| Jitter during control event | jitter while orchestration/control action occurs | Future network KPI | Should remain bounded |
| Packet loss during orchestration | packet loss during proof/control action window | Future network KPI | Should remain small |
| Containment time | isolation/rekey done time - trust alarm time | Future network KPI | Should be bounded |
| Service continuity impact | interruption, frame loss, or rebuffering during action | Future media KPI | Should remain acceptable |
| Recovery time | stable time after control action - action applied time | Future network KPI | Should be bounded |

## Strongest KPI Set for Journal Reporting

Recommended minimum KPI set:

1. MCP context retrieval success rate
2. MCP tool invocation latency
3. MCP reference-bundle verification latency
4. A2A reference validity
5. A2A reference registration gas
6. Coordination compression gain
7. Reference reuse ratio
8. Policy admissibility observation
9. Trust-aware action precision
10. Control-plane overhead ratio
