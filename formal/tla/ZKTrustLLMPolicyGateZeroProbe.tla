------------------- MODULE ZKTrustLLMPolicyGateZeroProbe -------------------
EXTENDS ZKTrustLLMPolicyGate

\* Revision sensitivity check. The published original Init excludes zero,
\* so NonZeroAnchorRequired cannot test a reachable zero-commitment input.
\* This separate initialisation admits zero; original Init/Next are unchanged.
ZeroProbeInit ==
  /\ phase = "OBSERVE"
  /\ actionClass \in ActionClass
  /\ humanApproved \in BOOLEAN
  /\ privilegedApproved \in BOOLEAN
  /\ proofValid \in BOOLEAN
  /\ anchorCommitment \in Commitments
  /\ executed = FALSE

ZeroProbeSpec == ZeroProbeInit /\ [][Next]_vars
=============================================================================
