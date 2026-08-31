# C Authorization Broker threat model

- Model date: 2026-08-31
- Scope: exact squash merge of one pull request in this repository
- Phase: PR-B0, dormant implementation; no active write workflow

## Assets and trust boundaries

Protected assets are the `main` branch, repository settings, tag namespace,
Releases, Secrets, and the meaning of a human C authorization. GitHub's
Environment review and workflow-run approval history are trusted as the
authorization issuer and audit source. Repository files, workflow inputs, PR
content, generated summaries, and model output are untrusted until checked.

The job-scoped `GITHUB_TOKEN` is capability, not authorization. The consume job
may receive write capability only after the Environment gate, but it still must
verify the exact approval comment and every bound invariant before use.

## State and effect model

```text
PLANNED
  -> WAITING_FOR_GITHUB_ENVIRONMENT_REVIEW
  -> AUTHORIZATION_VERIFIED
  -> PREFLIGHT_VERIFIED
  -> EFFECT_ATTEMPTED
       -> COMMITTED
       -> ABORTED_PRE_EFFECT
       -> RECOVERY_REQUIRED
  -> EFFECT_VERIFIED
```

`RECOVERY_REQUIRED` is distinct from ordinary failure. A timeout or truncated
response after the mutation may have produced an effect. The executor must
read the PR and base branch before deciding; it must never blindly retry.

Receipts are typed and kept separate:

1. **review receipt** — advisory review findings, no authority;
2. **authorization receipt** — GitHub approval history and bound digest;
3. **execution receipt** — exactly one attempted allowlisted mutation;
4. **verification receipt** — independent readback of the external effect;
5. **consumption record** — run ID, attempt, digest, terminal effect state.

## Threats and controls

| Threat | Required control | Fail state |
|---|---|---|
| Forged or copied approval | Fetch GitHub approval history; match Environment plus reviewer login and numeric ID | `ABORTED_PRE_EFFECT` |
| Approval for different parameters | Comment must equal `APPROVE-C1 sha256:<canonical digest>` | `ABORTED_PRE_EFFECT` |
| Same-run replay | Digest binds run ID and attempt; attempt must equal 1 | `ABORTED_PRE_EFFECT` |
| Old approval | Run age and manifest expiry are at most 600 seconds | `ABORTED_PRE_EFFECT` |
| Environment timer removed or changed | Require exactly one one-minute wait-timer rule in live API readback | `ABORTED_PRE_EFFECT` |
| Another branch or tag gains Environment access | Require custom policies plus exactly one `main` policy typed as `branch` | `ABORTED_PRE_EFFECT` |
| Administrator bypass, Secret, or Variable drift | Require explicit bypass=false and empty Environment inventories before effect | `ABORTED_PRE_EFFECT` |
| PR or main changes while waiting | Re-fetch repository, base SHA, PR head/base/state, and check suite after approval; prove the squash commit's sole parent is the authorized base | `ABORTED_PRE_EFFECT` or `RECOVERY_REQUIRED` |
| Multiple effects behind one approval | One fixed route and at most one mutation request; no matrix or reusable/local action | validator failure |
| Generic API escalation | No endpoint, method, shell, GraphQL, or free-form JSON input | input rejection |
| Workflow supply-chain substitution | Canonical workflow, exact workflow SHA, pinned official actions only, standard-library executor | validator failure |
| Check spoofing | Match required check name, success state, exact head SHA, and App ID `15368` | `ABORTED_PRE_EFFECT` |
| Secret or token disclosure | No Secret; never print token or authorization header; receipts contain no local absolute path | test/validator failure |
| Ambiguous mutation response | One mutation attempt, then read-only reconciliation; no automatic retry | `RECOVERY_REQUIRED` |
| Environment drift | Exact API readback plus manual administrator-bypass assertion before workflow activation | activation blocked |
| Missing Environment auto-created unprotected | Broker workflow remains absent until protected Environment exists | activation blocked |
| Owner account compromise | Short TTL, exact digest, server audit, narrow route, no standing release capability | accepted residual |

## Non-goals

The Broker does not authorize tag creation, Release publication, deployment,
visibility changes, Ruleset or Secret mutation, arbitrary repository writes, or
cross-repository administration. It is not an AI reviewer, auto-merge system,
release manager, or replacement for the required governance check.

## Acceptance evidence required before activation

- local canonicalization, invariant-change, approval, expiry, replay, drift,
  ambiguous-effect, and redaction tests pass;
- desired Environment state is applied only after adjacent user authorization;
- Environment API readback matches the fixed reviewer and protected-branch
  policy, and the maintainer manually confirms administrator bypass is disabled;
- wrong comment, wrong head SHA, stale run, and rerun all fail without mutation;
- exactly one canary PR is squash-merged by the approved route;
- a separate read-only job confirms the PR merge commit and `main` SHA;
- tag, Release, repository Secret, and Environment Secret inventories remain
  empty.
