# P0 Alternatives Evidence

- Assessment date: 2026-08-29
- Scope: repository-visible behavior at the cited revisions
- Method: qualitative architecture and scope comparison
- Excluded: runtime performance, adoption, popularity, and cost benchmarks

This note supports the bounded comparison in both README files. It does not
rank products or claim that one approach is universally better.

## This P0 baseline

Evidence in the current reviewed tree:

- `.github/governance/repo-policy.yaml` freezes license, release authority,
  README rules, and R/W/C permissions.
- `docs/P0_ACCEPTANCE.md` distinguishes local evidence from remote evidence.
- `docs/adr/0001` through `0004` record the four accepted decisions.
- No workflow, runtime script, tag, Release, host adapter, or automated gate is
  present in P0.

Therefore this baseline can be selected for a reviewable governance starting
point, but not for working CI enforcement or release automation today.

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
