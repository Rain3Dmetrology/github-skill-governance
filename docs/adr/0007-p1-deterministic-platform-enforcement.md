# ADR-0007: P1 deterministic platform enforcement

- Status: Accepted
- Date: 2026-08-29
- Scope: P1

## Context

P0 made policy reviewable but could not stop a direct push, an unpinned Action,
or a mutation executed against the wrong repository. Adding more AI reviewers
would not make these controls deterministic. The repository is also maintained
by one GitHub account, so a one-approval rule or required code-owner review
would lock out the only maintainer while still not creating independent review.

## Decision

1. A stdlib-only validator and unit tests become the required
   `governance-baseline` check. The check validates policy structure, bilingual
   README contracts, evidence links, CODEOWNERS, secret-shaped tracked content,
   a single frozen canonical workflow, and the continued absence of a release
   executor including extensionless tracked executables.
2. GitHub Actions receives only `contents: read`, cannot approve pull requests,
   may use only the verified full commit SHA for `actions/checkout`, and may not
   call a local Action. Equivalent YAML rewrites and extra workflows fail
   closed instead of being interpreted by partial text matching.
3. `main` requires a pull request, linear squash history, resolved review
   threads, a strict required check, and protection against deletion and
   non-fast-forward updates. No bypass actor is configured.
4. Required approvals remain zero and code-owner review is not platform-
   required while there is one maintainer. CODEOWNERS names the accountable
   owner and routes review, but P1 does not misrepresent self-review as
   independent approval.
5. A tag Ruleset matches `~ALL` and blocks creation, update, deletion, and
   non-fast-forward changes for every tag until P5. No user, connector,
   workflow, or legacy Skill has a bypass.
6. The GitHub preflight is read-only. It verifies host, authenticated account,
   repository full name and numeric ID, default branch, target SHA, operation
   class, and observed permission. It always reports
   `authorization_verified: false`: it is identity-and-permission evidence,
   never authorization. An arbitrary receipt string is deliberately not
   accepted because a read-only process cannot prove trusted issuance,
   action-binding, freshness, or atomic single-use consumption. ADR-0004 and
   ADR-0005 remain the normative human-authorization contract; Issue #1 stays
   open until a signed, server-consumed authorization broker exists.
7. Private Vulnerability Reporting must remain enabled. Auto-merge, AI review,
   release automation, repository Secrets, and deployment environments remain
   out of P1.

## Activation order

1. Merge the scripts, tests, CODEOWNERS, and workflow through the existing
   human-controlled path.
2. Observe one successful `governance-baseline` run on `main` and read its
   actual GitHub App ID; do not guess the `integration_id`.
3. Commit a reviewed follow-up desired state containing that exact App ID and
   active Ruleset payloads; do not POST the bootstrap files as active policy.
4. Restrict merge methods and Actions permissions.
5. Create both Rulesets disabled, read them back, then activate the all-tag
   Ruleset and finally the `main` Ruleset.
6. Record effective rules and a safe negative PR receipt before P1 is complete.

## Consequences

- P1 materially reduces accidental and agent-driven writes without granting a
  publisher credential.
- A repository administrator can still edit or delete Rulesets. Removing that
  control-plane residual risk requires an organization, a second trusted human,
  or a separately governed GitHub App; none is silently invented in P1.
- The required check's App binding is added only after the target repository
  produces a real check run.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*.py'` passes.
- `python3 scripts/validate_governance.py --root .` returns PASS JSON.
- GitHub API receipts prove the final Actions settings, PVR status, merge
  settings, active Ruleset IDs, effective `main` rules, and zero tag/Release.
- A deliberately invalid, harmless PR reaches a failed required check and a
  blocked merge state, then is closed without merging.
- `P1_PLATFORM_SOURCES_2026-08-29.md` records the primary-source basis and
  revalidation triggers for these platform decisions.
