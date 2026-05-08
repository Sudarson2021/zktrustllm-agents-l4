# L4 Supervisor Alignment: Blockchain-Anchored Authenticated State for Agentic AI

## Core Research Direction

This project frames blockchain as an authenticated shared state layer for AI and Agentic AI coordination.

The progression is:

1. Level 1: Blockchain as authenticated record.
2. Level 2: AI consumes authenticated blockchain state.
3. Level 3: Agentic AI creates new proof-backed blockchain records.
4. Level 4: Multiple agents coordinate by exchanging compact references to authenticated blockchain state.

## Main L4 Research Question

How can blockchain act as an authenticated shared memory layer for multi-agent AI systems, allowing agents to coordinate through compact references to trusted records rather than repeatedly exchanging large, sensitive, or unverifiable messages?

## Supervisor-Aligned Contribution

The Level 4 contribution is a reference-aware A2A coordination model.

Instead of Agent A sending full raw context to Agent B, Agent A sends:

- decisionId
- referenceId
- blockRef
- capabilityId
- policyClassHash
- traceCommitment
- CID hash
- proofRef

Agent B verifies the referenced authenticated state before acting.

## Important Practical Boundary

Blockchain is not placed in the real-time media path.

- Live media remains DTLS/RTP/multicast.
- IPFS stores audit evidence only.
- Blockchain stores authenticated decisions, commitments, references, and proof verification records.
