# Boundary-language cleanup

After the current `main.tex` is added, keep the complete limitation statement
only in the Claim Boundary subsection. Preserve a short caption warning only
where a reader could confuse simulated actuation with production actuation, or
first inclusion with economic finality.

Suggested replacements for repetitive prose:

| Repeated wording | Use when accurate |
|---|---|
| bounded agentic L4 control plane | proof-governed agentic control plane |
| bounded evidence | fixed evidence bundle; hash-addressed evidence |
| bounded action | policy-admissible action; ladder-constrained action |
| bounded evaluation | frozen evaluation; scoped evaluation |
| bounded deployment | evaluated deployment; test deployment |
| bounded result | artifact-specific result; measured result |
| reviewer-verifiable | auditable; reproducible from released evidence |

Delete negative-claim sentences from the introduction, background, design, and
ordinary results paragraphs when they merely duplicate the Claim Boundary.
Retain positive, precise statements of what was measured. Run this final check:

```bash
rg -n -i 'bounded|does not|not claim|out.of.scope|limited to|only establishes' paper supplement
```
