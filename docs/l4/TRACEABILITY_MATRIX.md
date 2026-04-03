# Traceability Matrix: ZKTrustLLM (L2) -> ZKTrustLLM-Agents (L4)

| L2 Component | L4 Extension | Reason |
|---|---|---|
| Media plane | Media plane unchanged | Preserve DTLS/RTP hot-path isolation |
| Evidence plane | Add trace bundles, anomaly bundles, rollback records | Extend auditability for multi-agent control |
| Trust plane | Add AgentRegistry, CapabilityManager, DecisionAttestor, AnomalyLedger | Support identity, least privilege, attestation, anomaly history |
| submitFeedbackZK | Keep as L2 reference path | Maintain continuity and reproducibility |
| PolicyRegistry | Extend for bounded LKH mitigations | Safe mapping from trust/risk to actions |
| No agent layer | Add agentic control plane | Core L4 contribution |
