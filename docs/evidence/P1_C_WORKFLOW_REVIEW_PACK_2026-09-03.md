# PR-B1 Review Pack

## Intent

- Requested change: add the only canonical, protected-Environment-gated route
  for one exact squash merge after PR-B0 and Environment activation.
- Non-goals: no AI reviewer, generic administration route, auto-merge, tag,
  Release, package publish, deployment, Secret, GitHub App, PAT, or legacy
  `github-release-management` mutation authority.
- Driving issue: [#1](https://github.com/Rain3Dmetrology/github-skill-governance/issues/1).
- Base revision: `7291ce8a508a6fdf079760cfec973d81d24a29d2`.

## Diff Summary

- Files changed: 20, including this Review Pack.
- Behavior changed: PR-B1 adds one `workflow_dispatch` workflow with a read-only
  prepare job and one `c-authorization`-gated consume job. The Broker accepts
  only the exact PR/base/head tuple and performs at most one conditional squash
  merge followed by exact-effect verification.
- Contract changed: the Environment and CLI states advance from workflow absent
  to workflow candidate; the validator now requires exactly two canonical
  workflows.
- Runtime corrections: live GitHub evidence corrected the workflow-run `path`
  shape and removed reliance on the empty check-run `pull_requests` array.
- Permission correction: impossible `GITHUB_TOKEN` Environment
  Secret/Variable inventory calls were removed; the canonical workflow instead
  forbids all `secrets.*` and `vars.*` references.
- Generated files: none.
- Candidate payload digest excluding this Review Pack:
  `sha256:a9242a5883b4d1029fc630503989ab0404e0d28837f62f5dc275f7f61cfcd5a3`.

## Risks

- Blocking: none in local evidence.
- Non-blocking: `contents: write` is the narrowest GitHub permission accepted by
  the pull-request merge endpoint, but it is broader than one API route. The
  byte-for-byte workflow, fixed executor, exact workflow SHA, protected `main`,
  and all-tag Ruleset are compensating controls.
- Non-blocking: an unrelated manual merge can still race after preflight.
  Post-effect parent verification detects this but cannot undo the commit;
  terminal state becomes `RECOVERY_REQUIRED` and forbids retry.
- Non-blocking: one maintainer can dispatch and approve. This is a two-action
  self-approval control, not independent two-person review.
- Non-blocking: Environment Secret and Variable counts cannot be enumerated by
  the job-scoped token. The workflow cannot reference those contexts, and
  external inventory readback remains mandatory at activation and closure.
- Sensitive surfaces: GitHub Actions permissions, Environment approval,
  `GITHUB_TOKEN`, merge API, canonical workflow, runtime evidence parser, and
  governance validator.

## Verification

- Command: `python -B -m unittest discover -s tests -p "test_*.py" -v`
  - Result: pass, 53 tests.
  - Evidence: positive exact merge, wrong digest/reviewer/environment, expiry,
    replay, workflow identity, repository/base/head/check drift, Environment
    drift, ambiguous effect, no-retry reconciliation, canonical workflow
    mutation, Secret/Variable expression injection, and legacy regression tests.
- Command: `python -B scripts/validate_governance.py --root .`
  - Result: pass, zero findings across 68 candidate tracked files after this
    Review Pack is included.
- Command: `python -B -m py_compile ...`
  - Result: pass for all three Python entry points.
- Command: `actionlint v1.7.12 ...`
  - Result: pass for both workflows with no findings.
- Command: `uvx zizmor==1.30.0 --pedantic ...`
  - Result: offline scan pass with no findings; online-only audits were not
    claimed.
- Command: PyYAML parse plus Git Bash `bash -n` and local workflow shell
  simulation.
  - Result: pass; prepare emits the approval summary, and consume attempt 2
    exits 1 as `ABORTED_PRE_EFFECT` without network access.
- Command: deterministic prepare CLI twice plus `git diff --check`.
  - Result: identical digest/output and no whitespace errors.
- Remote readback: PR #11 merged; `main` and Environment exact; one existing
  workflow; zero repository/Environment Secrets, Environment Variables, tags,
  and Releases.
  - Result: prerequisites observed. These are point-in-time facts only.

## Open Questions

- Question: can the live job-scoped `GITHUB_TOKEN` read every intended
  Environment endpoint and merge through the active Ruleset on this repository?
  - Needed before: production claim. This can only be answered by the planned
    remote negative and positive canaries after PR-B1 is independently merged.
- Question: does GitHub preserve the exact approval comment and single-record
  history in this account's live Environment flow?
  - Needed before: positive canary. Official schema supports it, but repository-
    specific behavior still requires readback.

## Decision

- State: `approved`.
- Approval granted for: commit the final PR-B1 candidate, push branch
  `feat/p1-c-broker-workflow`, and create a pull request targeting `main`.
- Explicitly not approved by that action: PR merge, workflow dispatch,
  Environment approval, canary merge, tag/Release, Ruleset/Secret mutation, or
  any change to `github-release-management`.
- Human decision: authorized in the current thread on 2026-09-03.
