# Step 100 Rollback / Recovery Note

## Purpose

This note records how to recover from the latest policy-gated scheduler run.

## Run

- Run ID: `20260509_181355`
- Status: `EXECUTED_PASS`
- Primary action: `GENERATE_SUPERVISOR_REPORT`

## Recovery Guidance

This scheduler run does not modify Git history, push code, deploy services, submit papers, or delete evidence.

If generated reports are not desired, they can be regenerated safely from the existing scripts.

If experiment outputs were overwritten during an approved remediation, restore known-good tracked outputs using:

```bash
git restore results/l4_live_rtp_media || true
git restore results/l4_dtls_rtp_media || true
git restore results/l4_live_telemetry || true
git restore results/l4_mcp_server || true
git restore results/l4_multi_agent_scaling || true
git restore results/l4_network_impairment || true
git restore results/l4_namespace_impairment || true
```

Temporary compiled binaries can be removed using:

```bash
rm -f dtls_rtp/dtls_rtp_proxy
rm -f abi.json out.r1cs out.wtns
```
