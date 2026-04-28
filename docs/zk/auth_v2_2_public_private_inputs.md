# AUTH_V2.2 Public and Private Inputs

## Purpose
This document defines the public/private input split for AUTH_V2.2.

The main extension beyond AUTH_V2.1 is the addition of:
- `trustState`

---

## 1. Public Inputs

The first AUTH_V2.2 version should expose:

1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `actionClass`
5. `contextHash`
6. `traceCommitment`
7. `expiryBucket`
8. `policyAdmissibilityFlag`
9. `trustState`

---

## 2. Private Inputs

The first AUTH_V2.2 version should keep private:

- `bindingNonce`

Optional descriptive metadata may remain outside the proof:
- `agentId`
- `capabilityIdText`
- `policyClassText`
- `actionClassText`
- `contextText`
- `trustStateText`

---

## 3. Design Note

The first AUTH_V2.2 implementation uses:
- `policyAdmissibilityFlag == 1`
- `trustState == 3`
- `actionClass == 3`

So the first verified bounded pair is:
- `Restricted -> Isolate`

---

## 4. Status

This document freezes the AUTH_V2.2 public/private input split.
