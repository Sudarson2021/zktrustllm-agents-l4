# AUTH_V2.1 Public and Private Inputs

## Purpose
This document defines the public/private input split for AUTH_V2.1.

The main extension beyond AUTH_V2 is the addition of:
- `policyAdmissibilityFlag`

---

## 1. Public Inputs

The first AUTH_V2.1 version should expose:

1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `actionClass`
5. `contextHash`
6. `traceCommitment`
7. `expiryBucket`
8. `policyAdmissibilityFlag`

## 2. Private Inputs

The first AUTH_V2.1 version should keep private:

- `bindingNonce`

Optional descriptive metadata may still be stored outside the proof as helper fields:
- `agentId`
- `capabilityIdText`
- `policyClassText`
- `actionClassText`
- `contextText`

---

## 3. Design Note

The main semantic upgrade is that the proof now exposes a bounded admissibility result.

The first implementation will use:
- `1` = admissible
- `0` = non-admissible

but the proof circuit will enforce:
- `policyAdmissibilityFlag == 1`

---

## 4. Status

This document freezes the AUTH_V2.1 public/private input split.
