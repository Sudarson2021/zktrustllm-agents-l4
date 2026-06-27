--------------------------- MODULE ZKTrustLLMPolicyGate ---------------------------
EXTENDS Naturals, FiniteSets

CONSTANTS Agents, Actions, Commitments

ActionClass == {"AUTOMATIC", "HUMAN", "PRIVILEGED", "NEVER"}
Phase == {"OBSERVE", "REASON", "PROVE", "ANCHOR", "ACT", "BLOCK"}

VARIABLES phase,
          actionClass,
          humanApproved,
          privilegedApproved,
          proofValid,
          anchorCommitment,
          executed

vars == <<phase, actionClass, humanApproved, privilegedApproved,
          proofValid, anchorCommitment, executed>>

Init ==
  /\ phase = "OBSERVE"
  /\ actionClass \in ActionClass
  /\ humanApproved \in BOOLEAN
  /\ privilegedApproved \in BOOLEAN
  /\ proofValid \in BOOLEAN
  /\ anchorCommitment \in Commitments
  /\ anchorCommitment # 0
  /\ executed = FALSE

CanExecute ==
  /\ proofValid = TRUE
  /\ anchorCommitment # 0
  /\ actionClass # "NEVER"
  /\ IF actionClass = "AUTOMATIC" THEN TRUE
     ELSE IF actionClass = "HUMAN" THEN humanApproved
     ELSE IF actionClass = "PRIVILEGED" THEN humanApproved /\ privilegedApproved
     ELSE FALSE

Next ==
  \/ /\ phase = "OBSERVE"
     /\ phase' = "REASON"
     /\ UNCHANGED <<actionClass, humanApproved, privilegedApproved,
                    proofValid, anchorCommitment, executed>>

  \/ /\ phase = "REASON"
     /\ phase' = "PROVE"
     /\ UNCHANGED <<actionClass, humanApproved, privilegedApproved,
                    proofValid, anchorCommitment, executed>>

  \/ /\ phase = "PROVE"
     /\ phase' = "ANCHOR"
     /\ UNCHANGED <<actionClass, humanApproved, privilegedApproved,
                    proofValid, anchorCommitment, executed>>

  \/ /\ phase = "ANCHOR"
     /\ CanExecute
     /\ phase' = "ACT"
     /\ executed' = TRUE
     /\ UNCHANGED <<actionClass, humanApproved, privilegedApproved,
                    proofValid, anchorCommitment>>

  \/ /\ phase = "ANCHOR"
     /\ ~CanExecute
     /\ phase' = "BLOCK"
     /\ executed' = FALSE
     /\ UNCHANGED <<actionClass, humanApproved, privilegedApproved,
                    proofValid, anchorCommitment>>

NeverNotExecuted ==
  actionClass = "NEVER" => executed = FALSE

HumanRequiresApproval ==
  executed /\ actionClass = "HUMAN" => humanApproved

PrivilegedRequiresBoth ==
  executed /\ actionClass = "PRIVILEGED" => humanApproved /\ privilegedApproved

ProofRequired ==
  executed => proofValid

NonZeroAnchorRequired ==
  executed => anchorCommitment # 0

NoExecutionBeforeAct ==
  executed => phase = "ACT"

Spec ==
  Init /\ [][Next]_vars
=============================================================================
