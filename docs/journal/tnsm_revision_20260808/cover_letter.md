Dear Editor-in-Chief,

Please consider our manuscript, “Auditable Policy-Governed LLM-Agent Control
for O-RAN Edge Security,” for publication in *IEEE
Transactions on Network and Service Management*.

The manuscript addresses a network/service-management problem at the
intersection of O-RAN security operations, agentic AI, policy governance, and
auditable evidence. It presents an architecture in which model outputs are
untrusted proposals: an external policy ladder governs action admissibility,
evidence is cryptographically bound, sensitive actions require human approval,
and the released artifacts support independent reproduction of the reported
measurements.

This submission substantially extends our ICC Workshops paper [22]. The journal
version adds the following six categories of new material from Section I-A of
the submitted manuscript:

1. **No agentic control governance:** this work adds five agents and the
   four-class AUTOMATIC--HUMAN--PRIVILEGED--NEVER ladder with fail-closed
   rejection.
2. **No formal verification:** an executable TLA+/TLC policy-gate model now
   exhaustively checks six safety invariants over all 320 reachable states of
   the configured finite abstraction.
3. **Local-chain evidence only:** an evidence-gated, paired, three-session
   public-testnet study now executes identical bytecode and 90 matched pairs on
   Ethereum Sepolia (Gasper PoS) and IoTeX testnet (Roll-DPoS), complemented by
   three clean sessions on real three-member etcd/Raft and four-validator
   Besu/QBFT clusters and a validated SHA-2 hash-primitive comparison.
4. **No semantic LLM evaluation:** a 180-cell frozen synthetic-policy oracle
   benchmark now compares No RAG, RAG, and Agentic RAG under a fixed claim
   boundary.
5. **No runtime negative-security evidence:** replay, zero-anchor, and
   unauthorised-submitter rejection is now evidenced in local hooks and on both
   public testnets, with explicit claim-boundary validation.
6. **No human-governed live execution:** a live n8n supervisor run now
   demonstrates a HUMAN gate terminating in a side-effect-free simulated ledger
   update, cross-bound to machine-verifiable report and action hashes, plus a
   reviewer-oriented reproducibility hardening layer.

After the final source is frozen, we will report the approximate proportion of
new material as **[XX%]**, calculated from newly added text, figures, tables,
experiments, and artifact content. The conference paper is uploaded as
supplementary material for transparent comparison.

The principal evidence includes exhaustive checking of six safety invariants
over 320 reachable states; a frozen 180-cell oracle evaluation; 90 matched
public-testnet transaction pairs across three sessions; and a human-gated n8n
demonstration. The manuscript explicitly limits these findings to the released
artifacts, synthetic oracle, public testnets, and simulated actuation path.

The manuscript is original, is not under review elsewhere, and all authors have
approved its submission. **[Confirm these statements before signing.]** The
code, data, workflows, and machine-readable evidence will be archived at
Zenodo DOI **[insert DOI]**, with the development repository retained on
GitHub.

Thank you for your consideration.

Sincerely,

Sudarson Karmaker, on behalf of all authors
Institute for Communication Systems, University of Surrey
**[corresponding-author email]**
