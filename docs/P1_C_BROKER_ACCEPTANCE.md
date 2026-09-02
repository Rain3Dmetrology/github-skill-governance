# P1 C Authorization Broker acceptance record

- Started: 2026-08-31
- Issue: [#1](https://github.com/Rain3Dmetrology/github-skill-governance/issues/1)
- Current state: PR-B0 and Environment activation merged; PR-B1 canonical
  workflow candidate is local only and not active on `main`

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
- [ ] The workflow and validator are merged through a separately authorized C
  action; the Broker is not credited with its own bootstrap merge.

The operator procedure and no-retry recovery path are frozen in
[`C_AUTHORIZATION_BROKER.md`](./runbooks/C_AUTHORIZATION_BROKER.md). Checked
PR-B1 items above describe this feature-branch candidate; they do not prove
remote activation or canary success. Local and point-in-time remote evidence is
recorded in
[`P1_C_WORKFLOW_LOCAL_CANDIDATE_2026-09-03.md`](./evidence/P1_C_WORKFLOW_LOCAL_CANDIDATE_2026-09-03.md).

## Remote negative and replay tests

- [ ] Unapproved run waits and produces no mutation.
- [ ] Wrong approval digest fails before effect.
- [ ] Wrong base or head SHA fails before effect.
- [ ] Expired run fails before effect.
- [ ] Run attempt 2 fails before effect.
- [ ] A new dispatch with identical PR inputs requires a new approval.
- [ ] Ambiguous transport result is reconciled and never blindly retried.

## Positive canary and closure

- [ ] One no-side-effect acceptance PR is squash-merged through the Broker.
- [ ] Independent readback proves the exact PR, head SHA, merge commit, and new
  `main` SHA.
- [ ] Authorization, execution, verification, and consumption receipts agree.
- [ ] Tag count, Release count, repository Secret count, and Environment Secret
  count remain zero.
- [ ] Remote evidence is committed by PR-B2.
- [ ] Issue #1 is closed only after all items above are checked.

## Explicit residual

The only maintainer may dispatch and approve the same run. This is not
independent two-person review. Until another trusted maintainer exists, the
control is accepted only as two separate human actions protected by an exact
digest, short expiry, server audit history, and a one-route executor.
