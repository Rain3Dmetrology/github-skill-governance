# C Authorization Broker operator runbook

This runbook operates the sole C-class route currently designed for this
repository: an exact squash merge of one pull request. It is usable only after
PR-B1 is merged to `main` and the remote workflow has passed its negative
canaries. It is not a generic repository administration interface.

## Fixed safety properties

- Dispatch only `.github/workflows/c-merge-exact-pr.yml` from `main`.
- Supply one PR number, the exact current `main` SHA, and the exact PR head SHA.
- The prepare job has read-only repository access and prints the unique approval
  comment into its step summary.
- The consume job cannot start until the `c-authorization` Environment is
  approved. Only that job receives `contents: write`.
- Attempt 1 only; request age at consumption must not exceed 600 seconds.
- The Broker performs at most one conditional squash-merge request and verifies
  the resulting commit and parent. An ambiguous effect is never retried.
- The workflow contains no `secrets.*` or `vars.*` reference. No repository or
  Environment Secret is required.

## Preconditions

1. Confirm the target PR is open, non-draft, mergeable, and intended for
   `main`.
2. Confirm `governance-baseline` succeeded for the exact PR head SHA.
3. Confirm no other merge has changed `main` since recording the base SHA.
4. Confirm the Environment still has reviewer `Rain3Dmetrology`, a one-minute
   timer, administrator bypass disabled, and exactly one custom `main` branch
   policy.
5. Confirm the repository has zero tags, Releases, repository Actions Secrets,
   and Environment Secrets. These are governance inventory checks, not Broker
   credentials.

Read the exact inputs without changing remote state:

```bash
gh api repos/Rain3Dmetrology/github-skill-governance/commits/main --jq .sha
gh api repos/Rain3Dmetrology/github-skill-governance/pulls/PR_NUMBER --jq .head.sha
```

## Dispatch

Replace only the three uppercase placeholders with values read immediately
before dispatch:

```bash
gh workflow run c-merge-exact-pr.yml \
  --repo Rain3Dmetrology/github-skill-governance \
  --ref main \
  -f pr_number=PR_NUMBER \
  -f expected_base_sha=BASE_SHA \
  -f expected_head_sha=HEAD_SHA
```

Do not rerun a failed or cancelled workflow. A rerun is attempt 2 and must be
rejected. Start a fresh dispatch with freshly read SHAs.

Prepare failures print the Broker's structured JSON to both the job log and
step summary before returning a nonzero exit. Operators must retain the error
code and must not infer it from a generic job failure.

## Approve the exact request

1. Open the workflow run and wait for `prepare-c-authorization` to finish.
2. Open its step summary and copy the complete line shaped as
   `APPROVE-C1 sha256:<64-lowercase-hex>`.
3. Review the run inputs and confirm the displayed digest belongs to this run.
4. In **Review deployments**, approve only `c-authorization` and paste the
   copied line as the approval comment without changing any character.
5. Complete approval promptly; the run expires after ten minutes from creation.

The approval is invalid if the comment is missing, edited, attached to another
run, issued by another identity, or older than the time limit.

GitHub records the one-minute timer as a separate approval by
`github-actions[bot]`. The Broker requires exactly that trusted timer record
and exactly one maintainer approval; extra, missing, malformed, or cross-
Environment records fail before effect.

## Interpret the result

| State | Meaning | Operator action |
|---|---|---|
| `COMMITTED` | Exact effect and post-merge topology were verified | Perform independent readback and retain the run URL |
| `ABORTED_PRE_EFFECT` | No committed effect was reported | Fix the stated invariant, then create a new dispatch; never rerun |
| `RECOVERY_REQUIRED` | A mutation may have occurred but exact effect is not proven | Stop all retries and reconcile the PR, `main`, and merge commit read-only |

For `RECOVERY_REQUIRED`, preserve the run logs and inspect these endpoints
before deciding anything else:

```bash
gh api repos/Rain3Dmetrology/github-skill-governance/pulls/PR_NUMBER
gh api repos/Rain3Dmetrology/github-skill-governance/commits/main
gh api repos/Rain3Dmetrology/github-skill-governance/commits/EXPECTED_MERGE_SHA
```

## Independent closure evidence

Record the run ID, run attempt, approval digest, PR number, authorized base and
head SHAs, merge commit SHA, and the merge commit's sole parent. Re-read tag,
Release, repository Secret, and Environment Secret counts. Do not mark P1-C
complete until PR-B2 commits those receipts and Issue #1 is closed.

## Permission caveat

GitHub exposes Environment configuration and deployment branch policies to the
job-scoped token through `actions: read`. Listing Environment Secrets and
Variables requires an `Environments: read` repository permission that workflow
syntax does not expose for `GITHUB_TOKEN`. The Broker therefore does not pretend
to perform those two runtime inventory calls. Safety instead comes from the
byte-for-byte canonical workflow, which has no secret or variable expression;
inventory emptiness is checked separately during activation and closure.
