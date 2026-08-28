# ADR-0004: R/W/C permission boundaries

- Status: Accepted
- Date: 2026-08-29
- Scope: P0

## Context

Authentication only proves that a tool can reach GitHub. It does not prove that
the current account, repository, target SHA, or permission is appropriate for
the requested action. Agent instructions cannot enforce platform permissions.

## Decision

| Class | Meaning | Examples | Default agent access |
|---|---|---|---|
| R | Read-only analysis; no shared-state mutation | Inspect files/diffs/checks/logs, produce local reports | Allowed |
| W | Reversible and reviewable write | Local patch, draft PR, draft Issue, review suggestion | Denied unless task-scoped authorization exists |
| C | External commitment or permission-sensitive mutation | Create a public repository, merge, tag, Release, Ruleset/Secret change, production deploy | Denied by default; executable only after explicit per-action human authorization |

Additional rules:

1. Every operation declares its class before execution.
2. W requires task-scoped authorization and an audit record.
3. C is delegable one action at a time only after explicit human authorization
   adjacent to that action and fresh deterministic preflight evidence.
4. No Skill, MCP server, or long-lived token receives broad C authority.
5. The existing release Skill receives no write or release permission.
6. The user authorization for this initial public repository bootstrap covers
   only creating and pushing the reviewed P0 repository. It does not grant C
   capability to future automation or to later release operations.

## Consequences

- AI can assist without silently acquiring release authority.
- High-risk actions retain a clear human commitment boundary.
- GitHub Rulesets and least-privilege workflow permissions must enforce the
  written policy in P1.

## Verification

- `repo-policy.yaml` defines R, W, and C plus default authorization.
- Every automated C capability is false in P0.
- P0 contains no secret, release workflow, GitHub App, or PAT configuration.
