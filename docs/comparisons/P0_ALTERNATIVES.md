# P0 Alternatives Evidence

- Assessment date: 2026-08-29
- Scope: repository-visible behavior at the cited revisions
- Method: qualitative architecture and scope comparison
- Excluded: runtime performance, adoption, popularity, and cost benchmarks

This note supports the bounded comparison in both README files. It does not
rank products or claim that one approach is universally better.

## This P0 baseline

P0 remains the accepted foundation. The current P1 candidate adds reviewable
enforcement artifacts without changing the P0 release boundary:

- `.github/governance/repo-policy.yaml` freezes license, release authority,
  README rules, and R/W/C permissions.
- `docs/P0_ACCEPTANCE.md` distinguishes local evidence from remote evidence.
- `docs/adr/0001` through `0006` record the accepted baseline and correction
  decisions.
- `scripts/`, `tests/`, CODEOWNERS, and one read-only workflow implement the P1
  candidate; `docs/P1_ACCEPTANCE.md` prevents desired state from being reported
  as active platform enforcement before remote receipts exist.
- No tag, Release, host adapter, release credential, or publisher is present.

Therefore this repository can be selected for a reviewable governance and
enforcement path, but not for verified multi-host distribution or release
automation today.

## Legacy release prompt

Reviewed source:

- Repository: [`Rain3Dmetrology/github-release-management`](https://github.com/Rain3Dmetrology/github-release-management)
- Frozen revision: [`6c0c6641df245f172e5c1c163385ad9638c520a3`](https://github.com/Rain3Dmetrology/github-release-management/tree/6c0c6641df245f172e5c1c163385ad9638c520a3)
- License at that revision: [Business Source License 1.1](https://github.com/Rain3Dmetrology/github-release-management/blob/6c0c6641df245f172e5c1c163385ad9638c520a3/LICENSE)
- Provenance boundary: [`P0_SOURCE_LOG.md`](../provenance/P0_SOURCE_LOG.md)

At that revision, release policy and write commands are expressed in the Skill
instruction surface, while the repository contains no workflow, test suite, or
deterministic release script. The README comparison is limited to those
repository-visible facts; it does not assess an unobserved private process.

## Unmanaged per-agent copies

This row describes an operating pattern, not a named product. For this
comparison, an unmanaged copy means each operator independently selects and
copies content, with no shared desired-state manifest, pinned installation
record, or reconciliation service.

The stated trade-off follows from that definition: central setup is not
required, while revision selection and reconciliation remain operator tasks.
No claim is made about runtime quality or suitability when reproducibility is
not required.

## Reassessment rule

Recheck this comparison whenever a cited repository revision changes or this
repository ships deterministic enforcement. Update the assessment date,
evidence, and both localized README rows in the same change.
