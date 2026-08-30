# P1 remote acceptance evidence

- Observed at: 2026-08-30 (Asia/Tokyo)
- Repository: `Rain3Dmetrology/github-skill-governance`
- Repository ID: `1350230486`
- Activation main revision: `b9b929f8454fb1c94167c20c26a7ed63d1a7dd44`
- Authenticated account observed by preflight: `Rain3Dmetrology`
- Observed repository permission: `admin`
- Preflight authorization claim: `false`

## Active Rulesets

| Control | Readback |
|---|---|
| All-tag Ruleset | ID `21839874`, target `tag`, match `~ALL`, `active` |
| Tag restrictions | creation, update, deletion, non-fast-forward |
| Main Ruleset | ID `21839880`, target `branch`, match `~DEFAULT_BRANCH`, `active` |
| Bypass actors | 0 in both Rulesets; current user bypass reports `never` |
| Main update path | pull request required |
| Merge method | squash only; linear history required |
| Review settings | 0 approvals, no code-owner approval, threads resolved |
| Unattributed Copilot extra approval | false; read back explicitly |
| Required check | strict `governance-baseline`, App ID `15368` |
| Ref protection | deletion and non-fast-forward changes blocked |

The effective-rules endpoint for `main` returned every main rule above with
Ruleset source ID `21839880`; this is not inferred only from the desired JSON.
The zero-approval setting records the single-maintainer limitation and does not
claim independent human approval.

## Safe negative proof

- PR: [#7](https://github.com/Rain3Dmetrology/github-skill-governance/pull/7)
- Head: `96a7db7c400c78a7857255d791a50205b2fc441f`
- Deliberate defect: one unknown top-level policy field
- Check:
  [`governance-baseline` failure](https://github.com/Rain3Dmetrology/github-skill-governance/actions/runs/33307530927/job/99246603479)
- GitHub merge state: `BLOCKED`
- Result: closed without merge; remote test branch deleted

No merge endpoint was called for the negative PR.

## Repository and Actions settings

| Control | Readback |
|---|---|
| Squash merge | enabled |
| Merge commit / rebase / auto-merge | disabled / disabled / disabled |
| Delete branch on merge / update branch | enabled / enabled |
| Actions policy | `selected`; SHA pinning required |
| Allowed Action | exact `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` |
| Blanket GitHub-owned / verified allow | false / false |
| Workflow token | default `read`; cannot approve PR reviews |
| Private Vulnerability Reporting | enabled |

## Absence checks

- Branches: only `main`; repository API reports it as protected
- Workflows: exactly 1 active workflow, the canonical `governance-baseline`
- Tags: 0
- Releases: 0
- Actions repository Secrets: 0
- Deployment environments: 0
- Release workflow or publisher: absent from the frozen canonical workflow
- Automated merge: disabled in repository settings and policy
- Repository-defined AI PR review workflow: absent

The repository API and tracked workflow can prove repository-visible state.
They cannot exhaustively enumerate every account-wide third-party GitHub App
installation. No account-wide absence claim is made.

## Residual risks and non-capabilities

1. The sole repository administrator can still edit or delete Rulesets. An
   organization policy, second trusted human, or separately governed App is
   required to reduce that control-plane residual.
2. Preflight proves identity, target, SHA, and observed permission but always
   reports `authorization_verified: false`. Issue #1 remains open for trusted,
   action-bound, fresh, atomically consumed C authorization.
3. No Skill has standing write, merge, tag, Release, Ruleset, Secret, or
   deployment authority. The legacy `github-release-management` Skill remains
   an evidence source only.
4. Version and release automation remains disabled until the P5 gate. This P1
   acceptance creates no tag or Release and does not activate `release-please`.

## Source basis

The primary-source rationale and revalidation triggers are recorded in
[`P1_PLATFORM_SOURCES_2026-08-29.md`](./P1_PLATFORM_SOURCES_2026-08-29.md).
This receipt is point-in-time evidence and must be refreshed after any relevant
GitHub platform, repository setting, Ruleset, workflow, or maintainer change.
