# GitHub Skill Governance

<!-- readme-contract:section:language-switch -->
English | [简体中文](./README.zh-CN.md)
<!-- /readme-contract:section:language-switch -->

<!-- readme-contract:section:value-proposition -->
Govern reusable agent skills with explicit permissions, evidence-backed documentation, and a release path that cannot be mistaken for a prompt.
<!-- /readme-contract:section:value-proposition -->

> Status: **P0 governance baseline**. This repository does not yet run CI,
> publish releases, install skills, or grant any agent release authority.

<!-- readme-contract:section:why-this-repo -->
## Why this repository

A monolithic prompt can mix instructions, GitHub writes, version decisions,
and release commands. This repository separates human commitments,
deterministic checks, and agent assistance so that every later automation can
be tested and revoked.

<!-- readme-contract:claim:claim.independent-rewrite-policy -->
The P0 baseline is a new Apache-2.0 repository governed by an
independent-rewrite policy. Its source log records inputs and exclusions; this
is not a formal legal clean-room certification.

<!-- readme-contract:claim:claim.release-authority-frozen -->
Version and release ownership is frozen to one future authority,
`release-please`; it is deliberately disabled during P0.

<!-- readme-contract:claim:claim.readme-contract-frozen -->
English and Simplified Chinese README files share stable section and claim IDs
instead of relying on line-by-line translation.

<!-- readme-contract:claim:claim.permission-boundaries-frozen -->
Repository operations are classified as read-only (R), reversible write (W),
or external commitment (C); agents receive no C permission by default.
<!-- /readme-contract:section:why-this-repo -->

<!-- readme-contract:section:quick-start -->
## Quick start

P0 is a governance review, not an installer:

```text
1. Read .github/governance/repo-policy.yaml
2. Review docs/adr/0001 through 0004
3. Compare README.md and README.zh-CN.md section/claim IDs
4. Confirm every P0 item in docs/P0_ACCEPTANCE.md
```

Do not install an AI reviewer or enable release automation from this baseline.
<!-- /readme-contract:section:quick-start -->

<!-- readme-contract:section:comparison-and-tradeoffs -->
## Comparison and trade-offs

<!-- readme-contract:claim:claim.p0-alternatives-comparison -->
Assessment date: **2026-08-29**. This is a scope and architecture comparison,
not a performance benchmark.

| Approach | Choose it when | Do not choose it when | Current trade-off | Evidence |
|---|---|---|---|---|
| This P0 governance baseline | You need license, release-authority, bilingual README, and permission contracts before automation | You need an enforced CI gate or working release path today | The boundary is reviewable now; enforcement is planned, not shipped | [P0 policy and acceptance](./docs/comparisons/P0_ALTERNATIVES.md#this-p0-baseline) |
| One human-supervised release prompt | A trusted maintainer needs a manually supervised checklist and accepts its repository license | You need an OSI-open reusable core, deterministic gates, or verified multi-host use | Lower setup; policy and write commands remain in the same instruction surface | [Reviewed legacy snapshot](./docs/comparisons/P0_ALTERNATIVES.md#legacy-release-prompt) |
| Unmanaged per-agent copies | The content is temporary and no shared desired state is required | The same revision must be reproduced or audited across hosts | No central setup; each operator owns revision tracking and reconciliation | [Defined comparison scope](./docs/comparisons/P0_ALTERNATIVES.md#unmanaged-per-agent-copies) |

The earlier `github-release-management` repository remains a requirements and
failure-scenario reference, not a dependency or production release executor.
<!-- /readme-contract:section:comparison-and-tradeoffs -->

<!-- readme-contract:section:current-limitations -->
## Current limitations

| Limitation | User impact |
|---|---|
| P0 contains policy and documentation only | No automated gate currently blocks a bad pull request |
| Release automation is disabled | There is no supported tag or GitHub Release path yet |
| Host adapters and smoke tests are absent | No agent platform is currently claimed as verified |
| GitHub Rulesets are not configured in P0 | The repository policy is frozen but not yet platform-enforced |
<!-- /readme-contract:section:current-limitations -->

<!-- readme-contract:section:mitigations -->
## Mitigations

| Limitation | Immediate mitigation | Permanent path | Status |
|---|---|---|---|
| No automated gates | Treat all P0 files as human-reviewed policy | P1 Rulesets and deterministic checks | Not started |
| No release path | Do not create tags or Releases | P5 Draft-first release Saga | Disabled by policy |
| No verified hosts | Do not claim platform compatibility | P6 exact-SHA two-host canary | Not started |
| No enforced branch protection | Avoid direct pushes after bootstrap | P1 required checks and CODEOWNERS | Not started |

Future work will receive GitHub issues before implementation; until then it is
not presented as a shipped capability.
<!-- /readme-contract:section:mitigations -->

<!-- readme-contract:section:compatibility -->
## Compatibility

No runtime or agent host is verified in P0. The planned package format is the
open Agent Skills directory convention, but compatibility claims require an
exact-revision install and smoke-test receipt.
<!-- /readme-contract:section:compatibility -->

<!-- readme-contract:section:evidence -->
## Evidence

| Claim ID | Evidence |
|---|---|
| `claim.independent-rewrite-policy` | `LICENSE`, `THIRD_PARTY_NOTICES.md`, `P0_SOURCE_LOG.md`, ADR-0001 |
| `claim.release-authority-frozen` | `repo-policy.yaml`, ADR-0002 |
| `claim.readme-contract-frozen` | `readme-contract.json`, ADR-0003, both README files |
| `claim.permission-boundaries-frozen` | `repo-policy.yaml`, ADR-0004 |
| `claim.p0-alternatives-comparison` | `P0_ALTERNATIVES.md`, assessed 2026-08-29 |

Machine-readable claim mapping lives in [`docs/claims.yaml`](./docs/claims.yaml).
<!-- /readme-contract:section:evidence -->

<!-- readme-contract:section:roadmap -->
## Roadmap

| Phase | Entry condition | Outcome required before the next phase |
|---|---|---|
| P0 | Repository bootstrap authorized | License, version authority, README contract, and R/W/C boundaries frozen |
| P1 | P0 accepted | GitHub platform enforcement and least-privilege checks |
| P2 | P1 enforced | Deterministic README, release-state, and distribution validators |
| P3+ | Prior phase evidence exists | Core Skills, Draft release Saga, then two-host canary |

Only P0 is current. Later phases are decision gates, not delivery claims.
<!-- /readme-contract:section:roadmap -->

<!-- readme-contract:section:security -->
## Security

Do not submit credentials, private client names, internal paths, or production
tokens. See [`SECURITY.md`](./SECURITY.md). P0 grants no agent merge, tag,
release, Ruleset, Secret, or deployment permission.
<!-- /readme-contract:section:security -->

<!-- readme-contract:section:license -->
## License

Apache License 2.0. See [`LICENSE`](./LICENSE) and
[`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md).
<!-- /readme-contract:section:license -->
