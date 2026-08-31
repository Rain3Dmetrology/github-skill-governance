# P1 Acceptance Record

- Repository: `Rain3Dmetrology/github-skill-governance`
- Issues: [#1](https://github.com/Rain3Dmetrology/github-skill-governance/issues/1),
  [#2](https://github.com/Rain3Dmetrology/github-skill-governance/issues/2)
- State: platform enforcement accepted; Broker PR-B0 contract in progress and
  remote C authorization still inactive
- Date: 2026-08-30

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
  falsely implemented by accepting a reusable string. The staged acceptance
  record is [`P1_C_BROKER_ACCEPTANCE.md`](./P1_C_BROKER_ACCEPTANCE.md).

## GitHub platform enforcement

- [x] `governance-baseline` succeeds on the merged `main` revision.
- [x] Actions is `selected`, full-SHA pinning is required, and only the exact
  checkout revision is allowed.
- [x] The default workflow token is read-only and cannot approve reviews.
- [x] Only squash merge is enabled; auto-merge is disabled; merged branches are
  deleted; update-branch is enabled.
- [x] Private Vulnerability Reporting returns `enabled: true`.
- [x] The `main` Ruleset is active with no bypass actor and its required check is
  bound to the App ID observed on the target check run.
- [x] The all-tag (`~ALL`) Ruleset is active with no bypass actor and blocks
  every tag creation, update, deletion, and non-fast-forward change until P5.
- [x] A safe negative PR produces a failed required check and blocked merge
  state, then is closed without merge.
- [x] GitHub still reports zero tag and zero Release.

P1 platform enforcement is accepted because every deterministic and platform
control above is checked and linked to point-in-time remote evidence. The
unchecked C-authorization broker criterion is a deliberately unshipped
capability tracked by Issue #1; no automated C executor may activate until it
is solved. Platform acceptance does not grant release authority.

PR-B0 may add a dormant, locally tested executor and the desired protected
Environment contract. Neither is activation: the Environment requires a later,
adjacent C authorization, and the canonical C workflow must remain absent until
that Environment is independently read back.

## Local candidate receipt

- Unit tests: 26 passed on Python 3.14, including negative policy-state,
  all-tag Ruleset, YAML-equivalent workflow rewrites, new permission scope,
  local Action, extensionless release executor, credential, release-command,
  identity, repository-ID, SHA, permission, and shell-injection cases.
- Live read-only preflight: account `Rain3Dmetrology`, repository ID
  `1350230486`, default branch `main`, activation target
  `b9b929f8454fb1c94167c20c26a7ed63d1a7dd44`, observed permission `admin`.
- The live preflight made four `GET` requests through argument-array
  `gh api` calls, performed no mutation, and explicitly returned
  `authorization_verified: false`.

## Remote bootstrap receipt

- PR [#5](https://github.com/Rain3Dmetrology/github-skill-governance/pull/5)
  merged the bootstrap revision; its `push`-triggered `main` check
  [`governance-baseline`](https://github.com/Rain3Dmetrology/github-skill-governance/actions/runs/33291774391/job/99204534886)
  succeeded on `4388f987267fb6578c379975cdc0e079cbab9482` and reported
  GitHub Actions App ID `15368`.
- Actions and merge settings were read back at their least-privilege P1 values;
  Private Vulnerability Reporting remained enabled.
- Tag Ruleset `21839874` and main Ruleset `21839880` were created and read back
  as `disabled`. This activation candidate records the observed App ID and the
  reviewed active payload before either Ruleset is activated.
- Full point-in-time fields are recorded in
  [`P1_REMOTE_BOOTSTRAP_2026-08-30.md`](./evidence/P1_REMOTE_BOOTSTRAP_2026-08-30.md).

## Remote enforcement receipt

- The all-tag Ruleset `21839874` and main Ruleset `21839880` were activated in
  that order and read back with zero bypass actors.
- Effective `main` rules report PR-only updates, linear history, squash-only
  merges, resolved review threads, deletion and non-fast-forward protection,
  and strict `governance-baseline` binding to App ID `15368`.
- Negative PR [#7](https://github.com/Rain3Dmetrology/github-skill-governance/pull/7)
  produced a failed
  [`governance-baseline`](https://github.com/Rain3Dmetrology/github-skill-governance/actions/runs/33307530927/job/99246603479)
  and `mergeStateStatus: BLOCKED`, then closed without merge and deleted its
  temporary branch.
- The complete readback is in
  [`P1_REMOTE_ACCEPTANCE_2026-08-30.md`](./evidence/P1_REMOTE_ACCEPTANCE_2026-08-30.md).
