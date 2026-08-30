# P1 Acceptance Record

- Repository: `Rain3Dmetrology/github-skill-governance`
- Issues: [#1](https://github.com/Rain3Dmetrology/github-skill-governance/issues/1),
  [#2](https://github.com/Rain3Dmetrology/github-skill-governance/issues/2)
- State: in progress
- Date: 2026-08-29

## Deterministic repository controls

- [x] Governance validator and all positive/negative unit tests pass.
- [x] Repository policy conforms to its strict JSON Schema contract.
- [x] English and Chinese README contracts, claims, and evidence pass.
- [x] CODEOWNERS maps governance, workflow, script, and test surfaces.
- [x] The only external Action is an exact verified `actions/checkout` SHA and
  checkout persistence is disabled.
- [x] Workflow inventory is exactly one frozen canonical file; local Actions,
  YAML-equivalent rewrites, and extra workflows fail closed.
- [x] No AI reviewer, auto-merge, publisher, release workflow, tag, Release,
  repository Secret, or deployment environment is introduced.

## Read-only identity preflight

- [x] The preflight verifies authenticated account, repository name and numeric
  ID, default branch, expected target SHA, operation class, and observed
  permission.
- [x] Missing or mismatched identity, SHA, or permission fails closed.
- [x] Commands use argument arrays, never `shell=True`, and output no token or
  authorization value. Credential type is reported as `opaque-not-inspected`,
  not guessed from token prefixes or scopes.
- [x] Every result declares `authorization_verified: false` and
  `purpose: identity-and-permission-evidence-only`; preflight success cannot be
  treated as delegated C authority.
- [ ] Fresh, adjacent, action-bound C authorization is backed by trusted
  issuance and atomic single-use consumption. This is Issue #1 and is not
  falsely implemented by accepting a reusable string.

## GitHub platform enforcement

- [ ] `governance-baseline` succeeds on the merged `main` revision.
- [ ] Actions is `selected`, full-SHA pinning is required, and only the exact
  checkout revision is allowed.
- [ ] The default workflow token is read-only and cannot approve reviews.
- [ ] Only squash merge is enabled; auto-merge is disabled; merged branches are
  deleted; update-branch is enabled.
- [ ] Private Vulnerability Reporting returns `enabled: true`.
- [ ] The `main` Ruleset is active with no bypass actor and its required check is
  bound to the App ID observed on the target check run.
- [ ] The all-tag (`~ALL`) Ruleset is active with no bypass actor and blocks
  every tag creation, update, deletion, and non-fast-forward change until P5.
- [ ] A safe negative PR produces a failed required check and blocked merge
  state, then is closed without merge.
- [ ] GitHub still reports zero tag and zero Release.

P1 is complete only after every item is checked and the point-in-time remote
receipt is linked here. Completion does not grant release authority.

## Local candidate receipt

- Unit tests: 25 passed on Python 3.14, including negative policy-state,
  all-tag Ruleset, YAML-equivalent workflow rewrites, new permission scope,
  local Action, extensionless release executor, credential, release-command,
  identity, repository-ID, SHA, permission, and shell-injection cases.
- Live read-only preflight: account `Rain3Dmetrology`, repository ID
  `1350230486`, default branch `main`, target
  `359bb44e4f5189993602c4ddbf16c512fdb31b18`, observed permission `admin`.
- The live preflight made four `GET` requests through argument-array
  `gh api` calls, performed no mutation, and explicitly returned
  `authorization_verified: false`.
