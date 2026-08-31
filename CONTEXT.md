# Domain context

This glossary defines governance terms used by code, schemas, Skills, ADRs, and
receipts. It describes the domain, not an implementation.

| Term | Canonical meaning | Not equivalent to |
|---|---|---|
| Capability | What an identity, token, connector, or tool can technically do | delegated authority |
| Authority | A policy-recognized right to decide or perform an operation | possession of a credential |
| R | Read-only analysis with no shared-state change | writing a report into the repository |
| W | Reversible, reviewable shared-state change under task-scoped authority | merge, release, or permission change |
| C | External commitment or permission-sensitive change requiring per-action human authorization | a normal continuation of W |
| Review receipt | Advisory findings about quality, spec, security, or tests | C authorization |
| Authorization receipt | Evidence that a trusted issuer approved one bound request | proof that an effect occurred |
| Execution receipt | Evidence that the allowlisted operation was attempted | verified external state |
| Verification receipt | Independent readback of the external effect | the executor's success message |
| Consumption record | Run, attempt, digest, and terminal effect state for one authorization | a reusable approval token |
| Acceptance predicate | Machine-evaluable facts that must hold for a transition | a general statement that work looks good |
| Gate | A transition that evaluates an acceptance predicate and may block | an AI recommendation |
| Effect | A mutation visible outside the current process | a planned or attempted operation |
| `ABORTED_PRE_EFFECT` | The request failed before any C mutation was attempted | ordinary post-effect failure |
| `RECOVERY_REQUIRED` | A C mutation may have occurred but readback cannot prove the state | safe retry permission |
| Reconciliation | Read-only evidence gathering after an ambiguous effect | repeating the mutation |
| Standing Definition of Done | Repository-wide completion conditions | operation-specific acceptance evidence |
| Operation acceptance | Exact repo, revision, policy, check, authority, and effect conditions for one request | standing Definition of Done alone |
| Control-band breach | A deterministic monitoring rule crossed its versioned threshold | permission for remediation |
| Intent artifact | Versioned statement of problem, outcome, constraints, owner, and open questions | implementation plan or C authorization |

## Invariants

- Capability never implies authority.
- Review never implies authorization.
- Attempt never implies effect.
- A timeout after a mutation never implies no effect.
- A reusable string is not single-use authorization.
- A pre-approved runbook narrows an operation; it does not turn a C action into
  R or W.
- Every automated loop must have a bounded input, a deterministic gate, a
  terminal or recovery state, and an auditable handoff artifact.
