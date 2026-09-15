# P1 C Broker remote canary evidence

- Repository: `Rain3Dmetrology/github-skill-governance` (`1350230486`)
- Environment: `c-authorization` (`20905500070`)
- Authorized base/workflow SHA: `d74edaf3d24b0a05b64bdf7e523a8b372462be7b`
- Canary PR: [#13](https://github.com/Rain3Dmetrology/github-skill-governance/pull/13)
- Authorized head SHA: `e9726ac66c53eb5f85ec51ab19d2fc5265cadb48`
- Exact squash result: `a4d922c09ae5537f79fe7f30f1a47eaf09ab2f57`

This record distinguishes remotely observed facts from guarantees that the
current single-owner GitHub configuration cannot enforce.

## Negative canaries

| Run | Test | Remote terminal evidence | Effect readback |
|---|---|---|---|
| `33660080446` | No approval | Stayed at the protected Environment; cancelled without executing consume | PR open; `main` unchanged |
| `33661258459` attempt 1 | Wrong approval digest | `approval_comment_mismatch / ABORTED_PRE_EFFECT` | PR open; `main` unchanged |
| `33662080839` attempt 1 | Stale expected base | `workflow_base_sha_mismatch / ABORTED_PRE_EFFECT` | PR open; `main` unchanged |
| `33662080839` attempt 2 | Replayed attempt | `run_attempt_rejected / ABORTED_PRE_EFFECT` | PR open; `main` unchanged |
| `33765882520` | Wrong expected head | `head_sha_mismatch / ABORTED_PRE_EFFECT` | PR open; `main` unchanged |
| `33766150230` | Approval after TTL | `run_expired / ABORTED_PRE_EFFECT` | PR open; `main` unchanged |

A fresh dispatch with otherwise identical PR inputs generated run
`33827147183` and digest
`sha256:be114f0ff59f2a25fe93f0ce690133c7c101fd9464f96b834d0fccb9a42cf535`.
The earlier digest was therefore not reusable.

The ambiguous-transport/no-retry path is covered by deterministic injected
fault tests. It was not induced against GitHub because intentionally making a
real merge response ambiguous would itself create an uncontrolled C effect.

## Positive canary and recovery

Run `33827147183` received exactly one maintainer approval carrying its exact
digest, plus the GitHub Actions one-minute timer record. GitHub accepted the
single squash merge request. The first in-job readback returned
`effect_verification_failed / RECOVERY_REQUIRED`, so no retry was made.

Independent readback then proved:

- PR #13 is closed and merged from exact head
  `e9726ac66c53eb5f85ec51ab19d2fc5265cadb48`;
- `main` equals merge commit
  `a4d922c09ae5537f79fe7f30f1a47eaf09ab2f57`;
- that commit has exactly one parent, the authorized base
  `d74edaf3d24b0a05b64bdf7e523a8b372462be7b`;
- the required `governance-baseline` check on the authorized head succeeded
  under GitHub Actions App ID `15368`;
- repository Secrets, Environment Secrets, Environment Variables, tags, and
  Releases remained at zero.

The recovery state was correct because the job could not yet prove the
effect. The eventual readback delay is addressed by bounded read-only retries;
the mutation remains one-shot.

Update on 2026-09-16: PR #17 proved that bounded retries alone were not
sufficient under REST API `2026-03-10`, where an otherwise complete merged-PR
response returned `merge_commit_sha: null`. The mutation still remained
one-shot and independent readback proved the commit. The compatibility fix and
live read-only reconciliation are recorded in
[`P1_C_EFFECT_RECONCILIATION_2026-09-16.md`](./P1_C_EFFECT_RECONCILIATION_2026-09-16.md).

## Security conclusion

This canary proves exact digest validation, expiry, replay rejection,
one-mutation behavior, and eventual exact-effect reconciliation for the tested
route. It does **not** prove that the Broker is the exclusive path to `main` or
that approval is independent: the sole owner can still use ordinary GitHub
merge authority, dispatch the run, and approve the Environment.

Production C-grade enforcement therefore remains blocked on a distinct
least-privilege machine identity, a separate human approver with
`prevent_self_review=true`, and server-side restriction of `main` updates to
the governed route. No tag, Release, Secret, or legacy release-Skill authority
was granted by this canary.
