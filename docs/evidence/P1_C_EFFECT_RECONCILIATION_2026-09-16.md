# P1 C Broker effect reconciliation evidence

- Repository: `Rain3Dmetrology/github-skill-governance` (`1350230486`)
- Broker run: [34992442354](https://github.com/Rain3Dmetrology/github-skill-governance/actions/runs/34992442354)
- Pull request: [#17](https://github.com/Rain3Dmetrology/github-skill-governance/pull/17)
- Authorized base/workflow SHA: `0004a82c293184c6fb572011e9a79b3ef7811e2c`
- Authorized head SHA: `4a383a44da24eb4f98f55a13668230ee7a73e1d0`
- Approval digest: `sha256:6ed0f377d936f2c54dee1b4f0c9298f7805e66f7c9d798ef97f3544a66168e26`
- Squash result: `0810703f23751bb294759260144e4df19f12d2b3`
- Frozen GitHub REST API version: `2026-03-10`

## Observed defect

The prepare job succeeded and the protected Environment recorded the exact
approval. GitHub accepted the Broker's sole merge request and returned the
exact squash SHA, but the consume job ended with:

```json
{
  "errors": [{
    "code": "effect_verification_failed",
    "message": "GitHub reported a merge but readback could not prove the exact effect."
  }],
  "recovery": {
    "reported_merge_sha": "0810703f23751bb294759260144e4df19f12d2b3",
    "verification_state": "RECOVERY_REQUIRED"
  },
  "state": "RECOVERY_REQUIRED"
}
```

No second merge request was sent. Independent API readback proved that PR #17
was merged at `2026-09-15T16:04:47Z`, `main` equalled the reported SHA, and the
squash commit had exactly one parent: the authorized base.

The defect was not a transient cache. With the same repository and token,
GitHub REST API `2026-03-10` returned `merged: true`, a real `merged_at`, and
`merge_commit_sha: null`; version `2022-11-28` returned the SHA. Both versions
are currently supported according to GitHub's
[API version policy](https://docs.github.com/en/rest/about-the-rest-api/api-versions).
GitHub's published
[breaking-change summary](https://docs.github.com/en/rest/about-the-rest-api/breaking-changes?apiVersion=2026-03-10)
does not document this field behavior, so the evidence establishes observed
API behavior, not a claimed platform guarantee.

## Durability regression found after PR #18

PR #18 implemented a fail-closed correction that used the current `main` tip
as the null-SHA candidate. Its exact-head squash result was
`a043db402b1ace01f51dba428079440911b3d677`, with the PR #17 squash as its sole
parent. The new-main CI run
[34995347106](https://github.com/Rain3Dmetrology/github-skill-governance/actions/runs/34995347106)
passed.

The mandatory post-merge replay then returned
`merge_commit_association_invalid`: the current tip was now PR #18 rather than
PR #17. No mutation was attempted. This proves that a tip-only fallback was
safe but not durable after later commits, so PR #18 was insufficient.

A live GraphQL query provided the immutable PR #17 `mergeCommit` SHA, exact
base/head OIDs, repository identity, merged state, and sole parent. A live REST
compare then proved that commit remained an ancestor of the new `main` with
`status: ahead`, `behind_by: 0`, and the merge commit as the merge base.

## Correction

The REST Broker remains pinned to `2026-03-10`. When and only when an otherwise
valid merged pull omits `merge_commit_sha`, read-only verification now:

1. reads GitHub GraphQL
   [`PullRequest.mergeCommit`](https://docs.github.com/en/graphql/reference/pulls#pullrequest)
   with the exact repository and PR number;
2. requires the GraphQL PR, repository, base/head OIDs, merged state, merge
   commit, and sole parent to match the authorization;
3. calls GitHub's read-only
   [list-pulls-associated-with-commit endpoint](https://docs.github.com/en/rest/commits/commits#list-pull-requests-associated-with-a-commit);
4. requires exactly one association matching the authorized PR number,
   repository IDs, base ref/SHA, head SHA, closed state, and merge timestamp;
5. independently verifies the commit has exactly one parent equal to the
   authorized base; and
6. uses GitHub's
   [compare endpoint](https://docs.github.com/en/rest/commits/commits#compare-two-commits)
   to prove the commit remains in `main`, then re-reads `main` to reject a
   changing verification snapshot.

Any missing, duplicate, malformed, or mismatched association stays
`RECOVERY_REQUIRED`. This adds no mutation path and does not relax the exact
head, exact base, workflow, check, approval, TTL, or Environment controls.

## Verification

- 33 Broker tests pass, including the fixed GraphQL query transport, positive
  null-SHA fallback, later-main durability, missing GraphQL evidence,
  unrelated-PR, and divergent-history rejection.
- 86 repository tests pass.
- Governance validation reports zero errors.
- The final corrected local Broker ran `verify` against run `34992442354` after
  PR #18 advanced `main` and
  returned `VERIFIED_COMMITTED` with the exact base, head, merge SHA, PR, run,
  and repository ID.
- Tag, Release, repository Secret, Environment Secret, and Environment
  Variable inventories remained zero after the PR #18 merge.

The underlying production blockers remain unchanged: the dispatcher and
approver share one owner identity, the Broker is not the exclusive `main`
route, and GitHub's synchronous merge endpoint has no atomic expected-base
precondition.
