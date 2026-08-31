# P1 C Authorization Broker review pack

- Review date: 2026-08-31
- Branch: `feat/p1-c-authorization-broker`
- Baseline `main`: `af399df2b35ee48be3e583b2a67e4d1aeb5e57c1`
- Scope: PR-B0 dormant contract, executor, tests, threat model, and research
- Review decision: W-ready for commit, push, and pull request; C activation is
  not authorized by this record

## Intent and authority boundary

The change creates no active write workflow, Environment, Secret, tag, or
Release. It freezes one future C route: squash-merge one exact pull request in
this repository after a protected GitHub Environment approval. Local changes,
commit, push, and pull-request creation are W actions. PR merge, Environment
mutation, and workflow activation remain separate C actions requiring fresh,
adjacent human authorization.

## Review dimensions

| Dimension | Result | Evidence |
|---|---|---|
| Spec | Pass | Closed JSON Schema, CLI contract, ADR-0009, and acceptance record agree on one route and terminal states |
| Standards | Pass | Standard-library implementation; no dependency, shell, local action, reusable workflow, or unpinned Action added |
| Security and authority | Pass with residuals | Exact repository/run/workflow/PR/base/head/check/reviewer/Environment binding; ten-minute expiry; attempt 1 only; one PUT; no Secret |
| Tests | Pass locally | 50 unit tests plus governance validation, diff whitespace check, and Python compilation |
| Effect and reconciliation | Pass locally | Success requires merge response/readback agreement, exact squash-parent base, and exact `main` tip; ambiguous mutation is never retried |

## Finding resolved during review

The first candidate proved the merge commit was the current `main` tip but did
not prove its parent was the authorized base SHA. Because GitHub's merge API
locks the PR head SHA rather than the base SHA, a concurrent base advance could
otherwise cross the preflight-to-effect boundary. The executor now fetches the
merge commit and requires exactly one parent equal to `expected_base_sha`.
A negative regression test proves a different parent produces
`RECOVERY_REQUIRED`.

## Commands and results

```text
python -m unittest discover -s tests -p 'test_*.py'
Ran 50 tests ... OK

python scripts/validate_governance.py --root .
ok=true; errors=0

git diff --check
exit 0

python -m py_compile scripts/c_authorization_broker.py scripts/validate_governance.py scripts/github_preflight.py
exit 0
```

The test output is local implementation evidence. It is not a claim that the
GitHub Environment approval API or live merge route has passed a remote canary.

## Unresolved residuals and activation blockers

1. The repository has one trusted maintainer. Self-review is therefore allowed;
   this is two separate human actions, not independent two-person approval.
2. The `c-authorization` Environment does not exist. Its creation and any
   mutation require a separately authorized C action and exact API readback.
3. The GitHub UI administrator-bypass control has not been inspected or set.
4. The canonical Broker workflow remains intentionally absent, so there is no
   production write capability and no live API canary yet.
5. GitHub API response shapes can drift. Activation remains blocked until
   negative, replay, ambiguous-result, and positive remote canaries pass.
6. A `mergeable: null` response fails closed and requires a fresh dispatch once
   GitHub finishes computing mergeability; it is operational friction, not an
   authorization bypass.
7. The executor is one deep module with a small CLI and injectable API adapter.
   It should be split only if a second independently useful route or adapter is
   accepted; premature abstraction would expand the privileged surface.

## Decision

No blocking local defect remains after the exact-base-parent fix. PR-B0 may be
committed, pushed, and opened for remote checks. This decision does not approve
the PR merge, Environment creation, Broker workflow activation, any release
operation, or any permission change to `github-release-management`.
