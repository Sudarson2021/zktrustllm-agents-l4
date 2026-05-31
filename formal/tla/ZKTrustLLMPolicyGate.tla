--------------------------- MODULE ZKTrustLLMPolicyGate ---------------------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Agents, Actions

ActionClass == {"AUTOMATIC", "HUMAN", "PRIVILEGED", "NEVER"}
Phase == {"OBSERVE", "REASON", "PROVE", "ANCHOR", "ACT", "BLOCK"}

VARIABLES phase, class, humanApproved, privilegedApproved,
          proofValid, anchorCommitment, executed

Init ==
  /\ phase = "OBSERVE"
  /\ class \in ActionClass
  /\ humanApproved \in BOOLEAN
  /\ privilegedApproved \in BOOLEAN
  /\ proofValid \in BOOLEAN
  /\ anchorCommitment # 0
  /\ executed = FALSE

CanExecute ==
  /\ proofValid = TRUE
  /\ anchorCommitment # 0
  /\ class # "NEVER"
  /\ IF class = "AUTOMATIC" THEN TRUE
     ELSE IF class = "HUMAN" THEN humanApproved
     ELSE IF class = "PRIVILEGED" THEN humanApproved /\ privilegedApproved
     ELSE FALSE

Next ==
  \/ /\ phase = "OBSERVE" /\ phase' = "REASON"
     /\ UNCHANGED <<class, humanApproved, privilegedApproved, proofValid, anchorCommitment, executed>>
  \/ /\ phase = "REASON" /\ phase' = "PROVE"
     /\ UNCHANGED <<class, humanApproved, privilegedApproved, proofValid, anchorCommitment, executed>>
  \/ /\ phase = "PROVE" /\ phase' = "ANCHOR"
     /\ UNCHANGED <<class, humanApproved, privilegedApproved, proofValid, anchorCommitment, executed>>
  \/ /\ phase = "ANCHOR" /\ CanExecute /\ phase' = "ACT" /\ executed' = TRUE
     /\ UNCHANGED <<class, humanApproved, privilegedApproved, proofValid, anchorCommitment>>
  \/ /\ phase = "ANCHOR" /\ ~CanExecute /\ phase' = "BLOCK" /\ executed' = FALSE
     /\ UNCHANGED <<class, humanApproved, privilegedApproved, proofValid, anchorCommitment>>

NeverNotExecuted == class = "NEVER" => executed = FALSE
HumanRequiresApproval == executed /\ class = "HUMAN" => humanApproved
PrivilegedRequiresBoth == executed /\ class = "PRIVILEGED" => humanApproved /\ privilegedApproved
ProofRequired == executed => proofValid
NonZeroAnchorRequired == executed => anchorCommitment # 0

Spec == Init /\ [][Next]_<<phase, class, humanApproved, privilegedApproved, proofValid, anchorCommitment, executed>>
=============================================================================
