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

## Correction

The Broker remains pinned to `2026-03-10`. When and only when an otherwise
valid merged pull omits `merge_commit_sha`, read-only verification now:

1. reads the current `main` tip as the candidate effect;
2. calls GitHub's read-only
   [list-pulls-associated-with-commit endpoint](https://docs.github.com/en/rest/commits/commits#list-pull-requests-associated-with-a-commit);
3. requires exactly one association matching the authorized PR number,
   repository IDs, base ref/SHA, head SHA, closed state, and merge timestamp;
4. verifies the candidate commit has exactly one parent equal to the
   authorized base; and
5. verifies the candidate is still the current `main` tip.

Any missing, duplicate, malformed, or mismatched association stays
`RECOVERY_REQUIRED`. This adds no mutation path and does not relax the exact
head, exact base, workflow, check, approval, TTL, or Environment controls.

## Verification

- 31 Broker tests pass, including positive null-SHA fallback and unrelated-PR
  rejection.
- 84 repository tests pass.
- Governance validation reports zero errors.
- The corrected local Broker ran `verify` against run `34992442354` and
  returned `VERIFIED_COMMITTED` with the exact base, head, merge SHA, PR, run,
  and repository ID.
- Tag, Release, repository Secret, Environment Secret, and Environment
  Variable inventories remained zero after the PR #17 merge.

The underlying production blockers remain unchanged: the dispatcher and
approver share one owner identity, the Broker is not the exclusive `main`
route, and GitHub's synchronous merge endpoint has no atomic expected-base
precondition.
