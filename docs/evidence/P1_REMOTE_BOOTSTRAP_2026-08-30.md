# P1 remote bootstrap evidence

- Observed at: 2026-08-30 (Asia/Tokyo)
- Repository: `Rain3Dmetrology/github-skill-governance`
- Repository ID: `1350230486`
- Bootstrap main revision: `4388f987267fb6578c379975cdc0e079cbab9482`
- Bootstrap PR: [#5](https://github.com/Rain3Dmetrology/github-skill-governance/pull/5)

## Check identity

- Check: `governance-baseline`
- Result: `success`
- GitHub App slug: `github-actions`
- GitHub App ID: `15368`
- Event: `push`
- Head SHA: `4388f987267fb6578c379975cdc0e079cbab9482`
- Run:
  [33291774391 / 99204534886](https://github.com/Rain3Dmetrology/github-skill-governance/actions/runs/33291774391/job/99204534886)

The App ID was read from the target repository check run after merge. It was
not copied from documentation or guessed.

## Repository settings readback

| Control | Observed value |
|---|---|
| Squash merge | enabled |
| Merge commit | disabled |
| Rebase merge | disabled |
| Auto-merge | disabled |
| Delete branch on merge | enabled |
| Update branch | enabled |
| Squash title/message | `PR_TITLE` / `PR_BODY` |

## Actions settings readback

| Control | Observed value |
|---|---|
| Actions enabled | true |
| Allowed actions | `selected` |
| SHA pinning required | true |
| GitHub-owned blanket allow | false |
| Verified blanket allow | false |
| Exact pattern | `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` |
| Default workflow permission | `read` |
| Workflow review approval | false |

## Disabled Ruleset readback

| Ruleset | ID | Target | Match | Enforcement | Bypass actors |
|---|---:|---|---|---|---:|
| `p1-freeze-all-tags-until-p5` | `21839874` | tag | `~ALL` | disabled | 0 |
| `p1-main-governance` | `21839880` | branch | `~DEFAULT_BRANCH` | disabled | 0 |

The main Ruleset was intentionally created without an App binding in its
disabled bootstrap form. The reviewed activation payload binds
`governance-baseline` to App ID `15368` and explicitly disables extra approval
for unattributed changes, matching the single-maintainer limitation.

## Other remote state

- Private Vulnerability Reporting: `enabled: true`
- Tags: 0
- Releases: 0
- Actions repository Secrets: 0
- Deployment environments: 0

## Boundary

This is a point-in-time bootstrap receipt, not proof that either Ruleset is
active. It contains no credential value and grants no Skill write, tag, merge,
Ruleset, Secret, deployment, or Release authority. Issue #1 remains open for a
non-reusable, action-bound C-authorization mechanism.
