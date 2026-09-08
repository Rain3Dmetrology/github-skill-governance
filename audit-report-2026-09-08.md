# Repository audit report — 2026-09-08

## Executive conclusion

The repository has strong fail-closed local contracts and P1 GitHub platform
controls, but it is **not yet a production C-grade authorization system**. The
remote Broker canary proved one-shot digest, expiry, replay, and exact-effect
readback behavior. Independent adversarial review also confirmed that ordinary
owner merge authority bypasses the Broker and that dispatch and approval use
the same identity.

P2 packaging can proceed as a read-only/dry-run, PR-only Skill. Production C
closure cannot proceed honestly until a distinct machine identity and separate
human approver are available.

## Scope and method

- Scope: 71 tracked files before this audit's changes.
- Dimensions: contract/data integrity; authorization/security; architecture;
  configuration/persistence.
- Evidence: source inspection, 62 deterministic tests, governance validator,
  remote GitHub API readback, and live negative/positive Broker canaries.
- Independent review: three parallel audit roles; two independently confirmed
  the critical/high authorization findings.
- Dependency audit: `pip-audit` unavailable, so dependency vulnerability
  scanning was downgraded and skipped. The runtime code currently uses only the
  Python standard library.
- Workflow linter: `actionlint` unavailable locally; GitHub's workflow parse and
  protected CI remain the remote syntax gate.

## Findings

| ID | Severity | Finding | Evidence | Status / action |
|---|---|---|---|---|
| AUD-2026-001 | Critical | Broker is not the exclusive `main` update route; the active Ruleset permits normal checked squash merges by an authorized writer | Observed Ruleset and source; independently confirmed | Open; requires dedicated App/machine actor and server-side exclusive routing |
| AUD-2026-002 | High | Dispatcher and Environment approver are the same owner identity; approval is not independent | Observed Environment and run approval history; independently confirmed | Open; requires separate actor and `prevent_self_review=true` |
| AUD-2026-003 | High | GitHub merge REST binds head SHA but not expected base atomically | Observed request body/API behavior; independently confirmed inference | Open residual; eliminate other writers or move to a serialized server-side primitive |
| AUD-2026-004 | High | A same-name GitHub Actions check was insufficiently bound to workflow source | Observed source; adversarial test | Resolved inside the Broker route: workflow ID/path/event/job/run are checked, manual dispatch is removed, and Broker refuses control-plane-changing PRs; ordinary owner bypass remains AUD-2026-001 |
| AUD-2026-005 | High | TTL used a timestamp captured before preflight and was not refreshed immediately before mutation | Observed source | Resolved: injected clock is refreshed immediately before the PUT; boundary test added |
| AUD-2026-006 | High | Immediate post-merge readback could misclassify normal GitHub convergence as recovery and discarded useful reconciliation detail | Live run `33827147183` plus source | Resolved: bounded read-only retries, one mutation maximum, typed recovery evidence |
| AUD-2026-007 | High | Typed or unexpected failures after mutation could be labelled `ABORTED_PRE_EFFECT` | Observed source; merge-gate review | Resolved: explicit mutation-attempt state and post-effect read-only reconciliation; post-attempt paths now end only in `COMMITTED`, `REJECTED_NO_EFFECT`, or `RECOVERY_REQUIRED` |
| AUD-2026-008 | Medium | Explicit `merged=false` plus proof of no effect was classified as ambiguous recovery | Observed source | Resolved: returns `github_merge_rejected / REJECTED_NO_EFFECT` only after no-effect proof |
| AUD-2026-009 | High | Receipts exist only in workflow logs/summary and manually committed evidence, not an independently controlled append-only journal | Observed workflow | Open; do not claim tamper-proof audit durability |
| AUD-2026-010 | High | No installable Skill package or verified host adapter exists | Observed repository | Assigned to P2; release/tag authority remains frozen |
| AUD-2026-011 | Medium | Large validator and Broker modules duplicate canonical configuration and workflow text | Observed source | Open technical debt; split only after behavior-preserving characterization tests |
| AUD-2026-012 | Medium | Runner/runtime are not pinned beyond action commit SHAs | Observed workflows | Open; record runtime and adopt a supported pinned execution profile before C production closure |
| AUD-2026-013 | High | A PR could add another module under `scripts/` and shadow the Broker's standard-library imports | Merge-gate review; adversarial path test | Resolved: workflow Python uses isolated mode and the Broker refuses every PR change under `.github/` or `scripts/` |

## Verified remote effect

Run `33827147183` submitted one exact squash request for PR #13. The job entered
`RECOVERY_REQUIRED` after an early readback could not yet prove the effect and
did not retry. Independent API readback proved merge commit
`a4d922c09ae5537f79fe7f30f1a47eaf09ab2f57` with exactly one parent,
authorized base `d74edaf3d24b0a05b64bdf7e523a8b372462be7b`.

Full canary evidence is in
[`docs/evidence/P1_C_REMOTE_CANARY_2026-09-04.md`](./docs/evidence/P1_C_REMOTE_CANARY_2026-09-04.md).

## Engineering decision

1. Keep Release/tag/Secret/Ruleset authority frozen.
2. Treat the current Broker as a tested single-owner confirmation route, not an
   account-compromise boundary.
3. Implement P2 as deterministic local validation and patch generation, with
   no standing GitHub write authority.
4. Require user-assisted identity setup before enabling production C closure:
   dedicated least-privilege GitHub App, separate human approver, protected
   validator source, and exclusive/serialized `main` update enforcement.
