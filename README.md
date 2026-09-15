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
> The protected `c-authorization` Environment and Broker workflow are active;
> remote canaries proved the tested one-shot route. It is not yet an exclusive,
> independent production C boundary. The P2 bilingual README Skill is packaged
> as an offline, read-first tool; Release authority remains disabled.

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
The repository contains an active one-route C-authorization contract and
exact-squash executor. Remote canaries prove its tested behavior, while the
single-owner identity and non-exclusive main route remain explicit blockers to
a production C-grade claim.

<!-- readme-contract:claim:claim.p2-bilingual-readme-skill -->
The self-contained `bilingual-readme-governance` Skill validates this README
pair and arbitrary sandbox repositories offline, emits a non-mutating
remediation plan, and keeps semantic truth review separate from structural
conformance.
<!-- /readme-contract:section:why-this-repo -->

<!-- readme-contract:section:quick-start -->
## Quick start

P1 is enforced governance and P2 adds one offline Skill, not a publisher:

```text
1. Run: python3 -m unittest discover -s tests -p 'test_*.py'
2. Run: python3 -I scripts/validate_governance.py --root .
3. Inspect: python3 scripts/github_preflight.py --help
4. Inspect: python3 scripts/c_authorization_broker.py --help
5. Review docs/P1_C_BROKER_ACCEPTANCE.md before changing enforced controls
6. Follow docs/runbooks/C_AUTHORIZATION_BROKER.md; never retry a recovery state
7. Run: python3 -I skills/bilingual-readme-governance/scripts/readme_governance.py validate --root .
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
| This governance repository | You need license, release-authority, bilingual README, and permission contracts before automation | You need an already verified multi-host package or working release path today | P1 controls are active and Broker canaries passed, but independent identity, exclusive mutation routing, multi-host distribution, and release remain unshipped | [Current policy and acceptance](./docs/comparisons/P0_ALTERNATIVES.md#this-p0-baseline) |
| One human-supervised release prompt | A trusted maintainer needs a manually supervised checklist and accepts its repository license | You need an OSI-open reusable core, deterministic gates, or verified multi-host use | Lower setup; policy and write commands remain in the same instruction surface | [Reviewed legacy snapshot](./docs/comparisons/P0_ALTERNATIVES.md#legacy-release-prompt) |
| Unmanaged per-agent copies | The content is temporary and no shared desired state is required | The same revision must be reproduced or audited across hosts | No central setup; each operator owns revision tracking and reconciliation | [Defined comparison scope](./docs/comparisons/P0_ALTERNATIVES.md#unmanaged-per-agent-copies) |

The earlier `github-release-management` repository remains a requirements and
failure-scenario reference, not a dependency or production release executor.
<!-- /readme-contract:section:comparison-and-tradeoffs -->

<!-- readme-contract:section:current-limitations -->
## Current limitations

| Limitation | User impact |
|---|---|
| Broker is not the exclusive `main` route and uses one owner identity | It is a tested confirmation mechanism, not protection against owner-token compromise |
| Release automation is disabled | There is no supported tag or GitHub Release path yet |
| Live host invocation is not attested | Directory-layout canaries passed, but no claim is made about every Codex or Claude product version |
| One maintainer owns review | CODEOWNERS routes review but cannot provide independent approval |
<!-- /readme-contract:section:current-limitations -->

<!-- readme-contract:section:mitigations -->
## Mitigations

| Limitation | Immediate mitigation | Permanent path | Status |
|---|---|---|---|
| Broker identity and route are not independent | Keep agent credentials task-scoped; do not call this a production C boundary | Dedicated least-privilege GitHub App, separate approver, `prevent_self_review=true`, and server-side exclusive routing | Remote canaries passed; Issue #1 remains open |
| No release path | Do not create tags or Releases | P5 Draft-first release Saga | Disabled by policy |
| Live host invocation not attested | Use the standalone offline command | Add product-version canaries without giving the Skill credentials | Directory-layout smoke tests passed |
| No independent reviewer | Record maintainer self-review honestly; require zero approvals | Add a second trusted human before enforcing independent approval | Open limitation |

Future work will receive GitHub issues before implementation; until then it is
not presented as a shipped capability.
<!-- /readme-contract:section:mitigations -->

<!-- readme-contract:section:compatibility -->
## Compatibility

The package follows the Agent Skills directory convention and passes the
bundled structural validator. Exact package content was copied into isolated
Codex-style and Claude-style Skill directories and executed there; this proves
path portability, not live product invocation or universal host compatibility.
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
| `claim.c-authorization-broker-bootstrap` | Broker schema, executor, canonical workflow, runbook, `P1_C_BROKER_ACCEPTANCE.md`, ADR-0009, threat model |
| `claim.p0-alternatives-comparison` | `P0_ALTERNATIVES.md`, assessed 2026-08-30 |
| `claim.p2-bilingual-readme-skill` | Packaged Skill, offline validator, P2 acceptance, cross-repository and directory-layout canaries, ADR-0010 |

Machine-readable claim mapping lives in [`docs/claims.yaml`](./docs/claims.yaml).
<!-- /readme-contract:section:evidence -->

<!-- readme-contract:section:roadmap -->
## Roadmap

| Phase | Entry condition | Outcome required before the next phase |
|---|---|---|
| P0 | Repository bootstrap authorized | License, version authority, README contract, and R/W/C boundaries frozen |
| P1 | P0 accepted | GitHub platform enforcement and least-privilege checks; accepted |
| P1-C | P1 enforced | Canary-verified single-owner route; independent identity and exclusive routing still block production closure |
| P2a | P1-C canary verified | Deterministic cross-repository bilingual README Skill; implemented offline, read-first, and PR-scoped |
| P2b+ | P2a evidence exists | Release-state and distribution validators, then Core Skills and release Saga |

P0 and P1 platform enforcement are accepted. P1-C is canary-verified but not
production-closed; P2a is implemented with local and directory-layout evidence.
P2b and later phases remain decision gates, not delivery claims.
<!-- /readme-contract:section:roadmap -->

<!-- readme-contract:section:security -->
## Security

Do not submit credentials, private client names, internal paths, or production
tokens. See [`SECURITY.md`](./SECURITY.md). P1 delegates no standing merge,
tag, release, Ruleset, Secret, or deployment authority to any Skill. A human-
authorized task actor may execute only the explicitly scoped C actions defined
by ADR-0005. The active Broker receives a job-scoped write token only after
Environment approval and exposes one exact squash-merge operation. It does not
give any Skill standing C authority, and it is not an independent control while
the dispatcher and approver share the owner identity.
<!-- /readme-contract:section:security -->

<!-- readme-contract:section:license -->
## License

Apache License 2.0. See [`LICENSE`](./LICENSE) and
[`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md).
<!-- /readme-contract:section:license -->
