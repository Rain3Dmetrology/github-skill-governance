# ADR-0008: P1 platform enforcement accepted

- Status: Accepted
- Date: 2026-08-30
- Scope: P1 remote activation

## Context

ADR-0007 defined a three-state activation sequence so reviewed desired state
could not be confused with effective GitHub state. The target workflow has now
run successfully under the selected-actions policy. Both Rulesets were updated
from disabled to active and read back through the repository API. A deliberate,
harmless invalid-policy PR failed the required check and GitHub reported its
merge state as blocked.

## Decision

1. Accept P1 GitHub platform enforcement for repository ID `1350230486`.
2. Bind strict `governance-baseline` to the observed GitHub Actions App ID
   `15368`; do not accept the same context from a different App.
3. Keep the all-tag Ruleset active with `~ALL`, zero bypass actors, and creation,
   update, deletion, and non-fast-forward restrictions until P5.
4. Keep the main Ruleset active with PR-only updates, squash-only linear
   history, resolved review threads, deletion and non-fast-forward protection,
   and zero bypass actors.
5. Record zero required approvals honestly. CODEOWNERS routes accountability but
   a single maintainer cannot produce independent approval of their own PR.
6. Keep Issue #1 open. Identity preflight is not an authorization broker, no
   reusable receipt is accepted, and no automated C executor may activate.
7. Keep release automation, tags, Releases, repository Secrets, deployment
   environments, automated merge, and AI-review workflows out of P1.

## Evidence

- Bootstrap and check identity:
  [`P1_REMOTE_BOOTSTRAP_2026-08-30.md`](../evidence/P1_REMOTE_BOOTSTRAP_2026-08-30.md)
- Active readback and negative proof:
  [`P1_REMOTE_ACCEPTANCE_2026-08-30.md`](../evidence/P1_REMOTE_ACCEPTANCE_2026-08-30.md)
- Negative PR: [#7](https://github.com/Rain3Dmetrology/github-skill-governance/pull/7)

## Consequences

- A missing or failed governance check blocks normal merging to `main`.
- Every tag name is frozen at the GitHub control plane, not only version-style
  tags.
- Repository administrators remain technically able to change the control
  plane. This accepted residual is explicit and must not be described as a
  cryptographic or organization-level guarantee.
- P2 may start only from this accepted state; P1 acceptance grants no release or
  unattended mutation authority.
