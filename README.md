# GitHub Skill Governance

<!-- readme-contract:section:language-switch -->
English | [简体中文](./README.zh-CN.md)
<!-- /readme-contract:section:language-switch -->

<!-- readme-contract:section:value-proposition -->
Establish an auditable, bilingual governance baseline before any reusable agent
Skill receives GitHub write or release authority.
<!-- /readme-contract:section:value-proposition -->

> Status: **P1 platform enforcement active**. GitHub readback and a blocked
> negative PR prove the required check, main protection, and all-tag freeze.
> PR-B0 now freezes a dormant exact-PR Broker contract; no protected
> Environment or write workflow is active, and Release authority remains
> disabled.

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
`release-please`; it is deliberately disabled through P4.

<!-- readme-contract:claim:claim.readme-contract-frozen -->
English and Simplified Chinese README files share stable section and claim IDs
instead of relying on line-by-line translation.

<!-- readme-contract:claim:claim.permission-boundaries-frozen -->
Repository operations are classified as read-only (R), reversible write (W),
or external commitment (C); agents receive no C permission by default.

<!-- readme-contract:claim:claim.p1-platform-enforcement -->
P1 platform controls are active: `main` requires the strict governance check
through a pull request, and every tag name is frozen until P5. This does not
grant any Skill standing mutation or release authority.

<!-- readme-contract:claim:claim.c-authorization-broker-bootstrap -->
The repository now contains a dormant, one-route C-authorization contract and
locally tested executor for an exact squash merge. It is not remotely active:
the protected Environment and canonical workflow are separate later gates.
<!-- /readme-contract:section:why-this-repo -->

<!-- readme-contract:section:quick-start -->
## Quick start

P1 is enforced governance, not an installer or publisher:

```text
1. Run: python3 -m unittest discover -s tests -p 'test_*.py'
2. Run: python3 scripts/validate_governance.py --root .
3. Inspect: python3 scripts/github_preflight.py --help
4. Inspect: python3 scripts/c_authorization_broker.py --help
5. Review docs/P1_C_BROKER_ACCEPTANCE.md before changing enforced controls
```

Do not install an AI reviewer or enable release automation from this revision.
<!-- /readme-contract:section:quick-start -->

<!-- readme-contract:section:comparison-and-tradeoffs -->
## Comparison and trade-offs

<!-- readme-contract:claim:claim.p0-alternatives-comparison -->
Assessment date: **2026-08-30**. This is a scope and architecture comparison,
not a performance benchmark.

| Approach | Choose it when | Do not choose it when | Current trade-off | Evidence |
|---|---|---|---|---|
| This governance repository | You need license, release-authority, bilingual README, and permission contracts before automation | You need an already verified multi-host package or working release path today | P1 controls are enforced and a one-route Broker is dormant; remote C authorization, multi-host distribution, and release remain unshipped | [Current policy and acceptance](./docs/comparisons/P0_ALTERNATIVES.md#this-p0-baseline) |
| One human-supervised release prompt | A trusted maintainer needs a manually supervised checklist and accepts its repository license | You need an OSI-open reusable core, deterministic gates, or verified multi-host use | Lower setup; policy and write commands remain in the same instruction surface | [Reviewed legacy snapshot](./docs/comparisons/P0_ALTERNATIVES.md#legacy-release-prompt) |
| Unmanaged per-agent copies | The content is temporary and no shared desired state is required | The same revision must be reproduced or audited across hosts | No central setup; each operator owns revision tracking and reconciliation | [Defined comparison scope](./docs/comparisons/P0_ALTERNATIVES.md#unmanaged-per-agent-copies) |

The earlier `github-release-management` repository remains a requirements and
failure-scenario reference, not a dependency or production release executor.
<!-- /readme-contract:section:comparison-and-tradeoffs -->

<!-- readme-contract:section:current-limitations -->
## Current limitations

| Limitation | User impact |
|---|---|
| C Broker is a dormant local contract only | No C-class mutation can be dispatched until Environment activation and remote canaries pass |
| Release automation is disabled | There is no supported tag or GitHub Release path yet |
| Host adapters and smoke tests are absent | No agent platform is currently claimed as verified |
| One maintainer owns review | CODEOWNERS routes review but cannot provide independent approval |
<!-- /readme-contract:section:current-limitations -->

<!-- readme-contract:section:mitigations -->
## Mitigations

| Limitation | Immediate mitigation | Permanent path | Status |
|---|---|---|---|
| Broker not remotely active | Keep C actions manually and adjacently authorized; reject reusable receipt strings | Protected Environment, canonical one-route workflow, replay tests, and effect readback | PR-B0; Issue #1 remains open |
| No release path | Do not create tags or Releases | P5 Draft-first release Saga | Disabled by policy |
| No verified hosts | Do not claim platform compatibility | P6 exact-SHA two-host canary | Not started |
| No independent reviewer | Record maintainer self-review honestly; require zero approvals | Add a second trusted human before enforcing independent approval | Open limitation |

Future work will receive GitHub issues before implementation; until then it is
not presented as a shipped capability.
<!-- /readme-contract:section:mitigations -->

<!-- readme-contract:section:compatibility -->
## Compatibility

No runtime or agent host is verified in P1. The planned package format is the
open Agent Skills directory convention, but compatibility claims require an
exact-revision install and smoke-test receipt.
<!-- /readme-contract:section:compatibility -->

<!-- readme-contract:section:evidence -->
## Evidence

| Claim ID | Evidence |
|---|---|
| `claim.independent-rewrite-policy` | `LICENSE`, `THIRD_PARTY_NOTICES.md`, `P0_SOURCE_LOG.md`, ADR-0001 |
| `claim.release-authority-frozen` | `repo-policy.yaml`, ADR-0002, ADR-0005 |
| `claim.readme-contract-frozen` | `readme-contract.json`, ADR-0003, both README files |
| `claim.permission-boundaries-frozen` | `repo-policy.yaml`, `owners.yaml`, ADR-0004, ADR-0005, ADR-0006 |
| `claim.p1-platform-enforcement` | `P1_ACCEPTANCE.md`, ADR-0008, active remote receipt |
| `claim.c-authorization-broker-bootstrap` | Broker schema and executor, `P1_C_BROKER_ACCEPTANCE.md`, ADR-0009, threat model |
| `claim.p0-alternatives-comparison` | `P0_ALTERNATIVES.md`, assessed 2026-08-30 |

Machine-readable claim mapping lives in [`docs/claims.yaml`](./docs/claims.yaml).
<!-- /readme-contract:section:evidence -->

<!-- readme-contract:section:roadmap -->
## Roadmap

| Phase | Entry condition | Outcome required before the next phase |
|---|---|---|
| P0 | Repository bootstrap authorized | License, version authority, README contract, and R/W/C boundaries frozen |
| P1 | P0 accepted | GitHub platform enforcement and least-privilege checks; accepted |
| P1-C | P1 enforced | Activate and remotely verify the exact-PR C Broker; Issue #1 |
| P2a | P1-C verified | Deterministic cross-repository bilingual README Skill, dry-run and PR-only |
| P2b+ | P2a evidence exists | Release-state and distribution validators, then Core Skills and release Saga |

P0 and P1 platform enforcement are accepted. P1-C, P2, and later phases remain
decision gates, not delivery claims.
<!-- /readme-contract:section:roadmap -->

<!-- readme-contract:section:security -->
## Security

Do not submit credentials, private client names, internal paths, or production
tokens. See [`SECURITY.md`](./SECURITY.md). P1 delegates no standing merge,
tag, release, Ruleset, Secret, or deployment authority to any Skill. A human-
authorized task actor may execute only the explicitly scoped C actions defined
by ADR-0005. The dormant Broker code does not change that boundary.
<!-- /readme-contract:section:security -->

<!-- readme-contract:section:license -->
## License

Apache License 2.0. See [`LICENSE`](./LICENSE) and
[`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md).
<!-- /readme-contract:section:license -->
