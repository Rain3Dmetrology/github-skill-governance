# P1 C Authorization Broker acceptance record

- Started: 2026-08-31
- Issue: [#1](https://github.com/Rain3Dmetrology/github-skill-governance/issues/1)
- Current state: PR-B0, Environment activation, and PR-B1 are active on
  `main`; the remote canary completed one exact merge, but production C-grade
  exclusivity and independent approval are not yet enforceable

This record separates architecture, installation, remote activation, effect,
and post-effect evidence. An unchecked item is not an implied pass.

## PR-B0 — contract and dormant implementation

- [x] Closed machine-readable request contract is tracked at
  `.github/governance/c-authorization-broker.schema.json`; typed receipt fields
  and terminal states are frozen in
  `.github/governance/c-authorization-broker-cli.json` and tested as a public
  CLI contract.
- [x] Desired `c-authorization` Environment payload is tracked and declares no
  Secrets.
- [x] ADR-0009 and the threat model freeze one exact `merge-exact-pr` route.
- [x] Standard-library executor performs no mutation unless injected with a
  valid GitHub approval history and every bound invariant.
- [x] Local positive and negative tests pass.
- [x] Existing P0/P1 tests and governance validation still pass.
- [x] No new active workflow, Environment, Secret, tag, or Release exists.

Local commands and point-in-time remote inventories are recorded in
[`P1_C_BROKER_LOCAL_CANDIDATE_2026-08-31.md`](./evidence/P1_C_BROKER_LOCAL_CANDIDATE_2026-08-31.md).
The pre-commit risk review and its resolved base-race finding are recorded in
[`P1_C_BROKER_REVIEW_PACK_2026-08-31.md`](./evidence/P1_C_BROKER_REVIEW_PACK_2026-08-31.md).

## Environment activation — separate C authorization

- [x] The maintainer provides fresh adjacent authorization for the exact
  Environment mutation.
- [x] API readback matches repository ID `1350230486`, reviewer ID `79391663`,
  wait timer 1, self-review allowed, and one custom `main` branch policy.
- [x] Environment Secret and Variable counts are zero.
- [x] The maintainer confirms in the GitHub UI that administrator bypass is
  disabled.
- [x] Replace ineffective `protected_branches=true` with one custom deployment
  branch policy matching only branch `main`.

The API mutations, UI assertion, reviewer restoration, and branch-scope
remediation are recorded in
[`P1_C_ENVIRONMENT_ACTIVATION_2026-08-31.md`](./evidence/P1_C_ENVIRONMENT_ACTIVATION_2026-08-31.md).
The correction diff, runtime hardening, and W-action decision are recorded in
[`P1_C_ENVIRONMENT_REVIEW_PACK_2026-08-31.md`](./evidence/P1_C_ENVIRONMENT_REVIEW_PACK_2026-08-31.md).

## PR-B1 — canonical route workflow

- [x] One canonical `workflow_dispatch` workflow is added after the protected
  Environment exists.
- [x] The workflow has one Environment-gated consume job, no matrix, no reusable
  or local action, and no generic API input.
- [x] Permissions are exact per job; only the consume job has the single write
  permission needed for the merge route.
- [x] The workflow and validator were merged through a separately authorized C
  action; the Broker was not credited with its own bootstrap merge.

The operator procedure and no-retry recovery path are frozen in
[`C_AUTHORIZATION_BROKER.md`](./runbooks/C_AUTHORIZATION_BROKER.md). Checked
PR-B1 items above describe the bootstrap boundary. Local and point-in-time
pre-activation evidence is recorded in
[`P1_C_WORKFLOW_LOCAL_CANDIDATE_2026-09-03.md`](./evidence/P1_C_WORKFLOW_LOCAL_CANDIDATE_2026-09-03.md).

## Remote negative and replay tests

- [x] Unapproved run waits and produces no mutation.
- [x] Wrong approval digest fails before effect.
- [x] Wrong base or head SHA fails before effect.
- [x] Expired run fails before effect.
- [x] Run attempt 2 fails before effect.
- [x] A new dispatch with identical PR inputs requires a new approval.
- [x] Ambiguous transport result is reconciled and never blindly retried in
  deterministic fault-injection tests; a live ambiguous network effect was
  deliberately not induced.

## Positive canary and closure

- [x] One no-side-effect acceptance PR is squash-merged through the Broker.
- [x] Independent readback proves the exact PR, head SHA, merge commit, and new
  `main` SHA.
- [x] Authorization, execution, and independent verification agree. The first
  in-job readback correctly entered `RECOVERY_REQUIRED` until GitHub's
  eventually consistent state became provable; it was not retried.
- [x] Tag count, Release count, repository Secret count, and Environment Secret
  count remain zero.
- [ ] Remote evidence and reconciliation hardening are committed by PR-B2.
- [ ] Issue #1 is closed only after the production blockers below are removed;
  remote canary success alone is insufficient.

## Production blockers

The current route is a tested single-owner confirmation mechanism, not a
production C-grade authorization boundary:

1. The owner can dispatch and approve the same run, so the approval is not
   independent. An agent holding that owner's token is not separated from the
   approver identity.
2. The active `main` Ruleset permits an ordinary squash merge after the status
   check; it does not make the Broker the exclusive update principal.
3. GitHub's pull-request merge REST endpoint binds the expected head SHA but
   has no atomic expected-base precondition. Exact-parent readback detects a
   race after effect but cannot prevent it while another writer can update
   `main`.
4. The Broker now binds the check to the canonical workflow ID/path/event and
   rejects PRs that change any path under `.github/` or `scripts/`.
   This protects the check root inside the Broker route, but ordinary owner
   merge authority can still bypass that route.

Closure requires a distinct least-privilege GitHub App or machine identity,
separate human approval with `prevent_self_review=true`, and a Ruleset or queue
that serializes every `main` update through that identity. Until then, agents
must not receive standing owner credentials and this Broker must not be
presented as protection against account compromise.

Remote runs, exact SHAs, and zero-side-effect inventories are recorded in
[`P1_C_REMOTE_CANARY_2026-09-04.md`](./evidence/P1_C_REMOTE_CANARY_2026-09-04.md).
