# P0 remote inventory — 2026-08-29

- Snapshot completed: `2026-08-29T14:22:57Z`
- Actor: authenticated interactive GitHub session for `Rain3Dmetrology`
- Method: GitHub REST and GraphQL reads through GitHub CLI
- Scope: repository-visible controls for the governance and legacy release
  repositories; this is a point-in-time audit, not a continuous guarantee

## Repository state

| Fact | `github-skill-governance` | `github-release-management` |
|---|---:|---:|
| Repository ID | `1350230486` | `1319410184` |
| Default branch | `main` | `main` |
| Observed main SHA | `072b5b40a5e7829ad6edc8f340268fae1a53f46d` | `6c0c6641df245f172e5c1c163385ad9638c520a3` |
| Rulesets | 0 | 0 |
| Actions workflows | 0 | 0 |
| Repository hooks | 0 | 0 |
| Deploy keys | 0 | 0 |
| Environments | 0 | 0 |
| Repository collaborators | owner only | owner only |
| Repository auto-merge | disabled | disabled |

The governance repository allowed all Actions at the platform setting, did not
require action SHA pinning, and kept the default workflow token read-only with
PR-review approval disabled. Those settings are P1 work; the absence of a
workflow means they did not provide a repository release path at this snapshot.

## AI review, automatic merge, and automatic release

- PR #3 had zero reviews, zero comments, and zero status checks.
- Neither repository contained an Actions workflow, repository webhook, bot
  collaborator, deploy key, or environment.
- Repository auto-merge was disabled, and no repository-level automatic
  release configuration was observed.

Therefore the bounded conclusion is: **no repository-level AI PR reviewer,
automatic merge, or automatic release mechanism was observed at this
snapshot**. It is not evidence that every account-level third-party GitHub App
is absent. The available OAuth/API path could not exhaustively enumerate all
account installations.

The interactive OpenAI GitHub connector itself has broad technical access to
repositories selected by the account owner. No evidence showed it acting as an
automatic reviewer on PR #3. ADR-0005 treats this as connector capability, not
standing authority delegated to a Skill.

## P0 cleanup and legacy scan receipts

At `2026-08-29T14:34:03Z`:

- `DELETE /repos/Rain3Dmetrology/github-skill-governance/git/refs/heads/docs/p0-remote-acceptance`
  completed successfully. A subsequent
  `GET /repos/Rain3Dmetrology/github-skill-governance/branches` returned only
  `main`. The stale local remote-tracking ref was then removed.
- `GET /repos/Rain3Dmetrology/github-release-management/git/trees/6c0c6641df245f172e5c1c163385ad9638c520a3?recursive=1`
  returned `truncated: false` and five blobs: `.gitignore`, `CHANGELOG.md`,
  `LICENSE`, `README.md`, and `SKILL.md`.
- Those five blobs were decoded in memory and scanned for common GitHub PAT,
  AWS access key, private-key header, and assigned key/token/secret/password
  signatures. The result contained zero matching paths. Secret values were
  never printed or persisted.

The legacy scan is intentionally narrow: it covers the complete frozen tree at
that revision, not unreachable Git objects, all Git history, the maintainer's
machine, account secrets, or credentials supplied at runtime. It supports only
the claim that no credential signature was observed in the reviewed tree.

## Security controls observed

- Secret scanning, push protection, and Dependabot security updates were
  enabled on the governance repository.
- Secret-scanning non-provider patterns and validity checks were disabled.
- Private Vulnerability Reporting returned `enabled: true`.

## Limits and follow-up

This inventory intentionally records counts and policy-relevant facts only. It
does not record credentials, personal filesystem paths, token values, private
repository names, or unrelated account installations. Re-run the inventory
after P1 and attach the active Ruleset IDs, Actions settings, required-check
name, and reverified Private Vulnerability Reporting status.
