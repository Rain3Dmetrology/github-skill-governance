# P0 Acceptance Record

- Repository: `Rain3Dmetrology/github-skill-governance`
- Scope: License, version authority, bilingual README contract, R/W/C boundary
- Date: 2026-08-29

## Local evidence

- [x] Standard Apache License 2.0 text exists.
- [x] Independent-rewrite and third-party provenance policy exists.
- [x] ADR-0001 freezes the open-source and independent-rewrite decision.
- [x] P0 source log records reviewed inputs, exclusions, method, and limits.
- [x] ADR-0002 freezes release-please as the sole future release authority.
- [x] ADR-0003 freezes the bilingual README contract.
- [x] ADR-0004 freezes R/W/C permission boundaries.
- [x] ADR-0005 separates connector capability, delegated task authority, and
  active automation authority without granting the legacy release Skill access.
- [x] ADR-0006 normalizes the R/W/C policy fields and defines a fail-closed
  validation contract for P1.
- [x] Both README files have reciprocal links and matching section/claim IDs.
- [x] Machine-readable repository policy and README contract exist.
- [x] A named semantic-review owner and the single-maintainer limitation exist.
- [x] Every P0 implemented claim maps to local evidence.
- [x] No repository-stored workflow, token, release script, AI-reviewer
  configuration, publisher credential, or release executor is present.

## Remote evidence

- Initial verification: `2026-08-29T03:12:24Z`
- Corrective audit snapshot: `2026-08-29T14:22:57Z`
- GitHub repository ID: `1350230486`
- Bootstrap commit: `3aa45680156bcd61b0ee04ff547595e3125270a9`
- P0 remote-acceptance merge: `072b5b40a5e7829ad6edc8f340268fae1a53f46d`

- [x] Public GitHub repository created under `Rain3Dmetrology`.
- [x] Default branch contains the reviewed P0 bootstrap commit as its root.
- [x] GitHub reports `Apache License 2.0` with key `apache-2.0`.
- [x] Repository reported 0 tag, 0 Release, 0 Actions workflow, 0 deploy key,
  and 0 Ruleset at the cited verification snapshots.
- [x] The merged `docs/p0-remote-acceptance` source branch was deleted; a
  subsequent branch-list read returned only `main`, which retained the commit
  and PR history.
- [x] At frozen revision `6c0c664`, the complete five-blob legacy repository
  tree had no observed credential signature; history and external runtime
  credentials were not inspected. The legacy Skill is denied all delegated
  write, tag, and Release authority by this repository policy.
- [x] Repository-level AI review, automatic merge, and automatic release were
  not observed; account-level app absence is not claimed.
- [x] GitHub Private Vulnerability Reporting returned `enabled: true`.
- [x] P1 tracking issues exist before P1 work begins:
  [least-privilege preflight #1](https://github.com/Rain3Dmetrology/github-skill-governance/issues/1)
  and [Rulesets/CODEOWNERS #2](https://github.com/Rain3Dmetrology/github-skill-governance/issues/2).

The remote facts above are historical snapshots, not continuously true
invariants. The detailed scope and visibility limits are recorded in
[`P0_REMOTE_INVENTORY_2026-08-29.md`](./evidence/P0_REMOTE_INVENTORY_2026-08-29.md).

P0 is locally complete only when all local evidence passes. It is remotely
complete only when every remote item is verified from GitHub and its snapshot
limits are stated.
