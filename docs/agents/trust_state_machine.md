# ZKTrustLLM-Agents Trust-State Machine

## Purpose
This document defines the initial trust-state machine for the L4 control plane.

The trust-state machine provides:
- a stable interpretation layer between verified evidence and policy action,
- bounded transitions,
- explicit links between trust state, required verification, and allowed mitigation classes.

---

# 1. Trust States

## 1.1 Trusted
Meaning:
- evidence is sufficient,
- authorization is valid,
- anomaly level is below threshold,
- no active restriction is required.

## 1.2 Degraded
Meaning:
- trust remains provisionally acceptable,
- but weak anomaly signals, missing confidence, or reduced consistency require caution.

## 1.3 Suspect
Meaning:
- evidence inconsistency or risk has become significant enough that normal progression should not continue without extra checks.

## 1.4 Restricted
Meaning:
- the entity or decision path may proceed only under tightly limited policy conditions, or only after secondary verification.

## 1.5 Quarantined
Meaning:
- the entity or path is not allowed to proceed in the normal workflow and must be isolated from ordinary control/action progression.

---

# 2. Allowed Actions by State

| Trust state | Typical allowed actions |
|---|---|
| Trusted | keep, rotate |
| Degraded | keep with caution, rotate, secondary verification |
| Suspect | isolate, escalate, restrict |
| Restricted | quarantine, subgroup isolation, explicit recovery path only |
| Quarantined | no normal action; supervised recovery or revocation only |

---

# 3. State Transitions

## 3.1 Trusted -> Degraded
- **Trigger:** weak anomaly indicators, reduced evidence sufficiency, timing irregularity, partial inconsistency
- **Evidence required:** bounded anomaly signal or confidence drop
- **ZK/policy check required:** not always mandatory; trust manager update required
- **Allowed action classes:** keep with caution, rotate, secondary verification
- **Audit event emitted:** degradation event

## 3.2 Degraded -> Trusted
- **Trigger:** anomaly cleared, consistency restored, capability still valid
- **Evidence required:** clean verification window and no active restriction
- **ZK/policy check required:** trust-state confirmation
- **Allowed action classes:** keep, rotate
- **Audit event emitted:** trust recovery event

## 3.3 Degraded -> Suspect
- **Trigger:** repeated anomaly threshold breach, contradictory outputs, failed admissibility check
- **Evidence required:** anomaly bundle or verified inconsistency summary
- **ZK/policy check required:** yes when action progression is still requested
- **Allowed action classes:** isolate, escalate, restrict
- **Audit event emitted:** suspect-state event

## 3.4 Suspect -> Restricted
- **Trigger:** policy violation risk, invalid scope, failed secondary verification, capability concern
- **Evidence required:** failed authorization or failed policy-admissibility evidence
- **ZK/policy check required:** yes
- **Allowed action classes:** subgroup isolation, strict restriction, quarantine readiness
- **Audit event emitted:** restriction event

## 3.5 Restricted -> Trusted
- **Trigger:** verified recovery, renewed capability, clean anomaly window, successful revalidation
- **Evidence required:** explicit revalidation record
- **ZK/policy check required:** yes for return-to-trust
- **Allowed action classes:** keep, rotate
- **Audit event emitted:** recovery and restoration event

## 3.6 Restricted -> Quarantined
- **Trigger:** repeated violation, malicious pattern confirmation, disallowed action attempt, unresolved contradiction
- **Evidence required:** high-confidence anomaly or policy-failure bundle
- **ZK/policy check required:** yes where applicable
- **Allowed action classes:** quarantine only
- **Audit event emitted:** quarantine event

---

# 4. Decision Inputs That Influence State

The following inputs may influence the trust-state transition logic:
- authorization validity
- capability scope validity
- context-hash consistency
- trace-binding consistency
- anomaly threshold status
- policy admissibility result
- freshness status
- inter-agent message integrity status

---

# 5. Link to Policy Action

## 5.1 Trusted
Usual action outcome:
- continue operation
- optional rotate for maintenance

## 5.2 Degraded
Usual action outcome:
- continue with extra verification
- tighten control
- reduce trust confidence

## 5.3 Suspect
Usual action outcome:
- isolate decision path
- prevent unrestricted progression
- force policy escalation

## 5.4 Restricted
Usual action outcome:
- limit scope
- subgroup isolation
- quarantine candidate

## 5.5 Quarantined
Usual action outcome:
- stop ordinary progression
- require supervised recovery or revocation logic

---

# 6. Required Audit Fields for Every Transition

Every trust-state transition should record:
- previous trust state
- new trust state
- taskId
- agentId
- contextHash
- policyClass
- trigger class
- timestamp
- traceCID or trace reference
- decision justification reference

---

# 7. Initial Rule Set for Implementation

## Rule R1
No action may be emitted from an unsigned or stale control message.

## Rule R2
No progression to Trusted may occur without capability validity.

## Rule R3
A failed authorization or failed policy admissibility check cannot leave the system in Trusted.

## Rule R4
Repeated anomaly threshold crossings escalate at least one level upward unless a stronger recovery rule applies.

## Rule R5
Quarantine is terminal for normal progression until explicit recovery logic is invoked.

---

# 8. Initial Recovery Logic

Recovery from Restricted or Quarantined should require:
1. revalidation of identity/capability,
2. clean anomaly window,
3. trace-linked justification for restoration,
4. policy approval for restoration,
5. audit anchoring of the recovery event.

---

# 9. Status
This trust-state machine is the first frozen decision model linking verified evidence to bounded policy action in the L4 control plane.
