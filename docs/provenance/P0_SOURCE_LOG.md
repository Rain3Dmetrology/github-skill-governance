# P0 Source and Provenance Log

- Record date: 2026-08-29
- Scope: initial P0 governance baseline
- Policy: independent rewrite; no formal legal clean-room certification

## Inputs reviewed

| Input | Pinned identity | Permitted use in P0 | Excluded use |
|---|---|---|---|
| User-supplied initial SPEC, `GitHub仓库自动化管理Skill组合_spec可执行清单_v1_0.md` | SHA-256 `be437528af7505f901d2eed6089db52b09559a7fbbc4bf33570bfa7290964f60` | Requirements, terminology, and scenarios | No claim that its third-party passages were relicensed into this repository |
| Reviewed SPEC v3.0, `GitHub通用Skill仓库自动化治理_最终可执行SPEC_v3_0.md` | SHA-256 `9bb8d0c4fc088cbc49c267d1532a531fbbdafce3df2c20b4cea33f79a7c16fee` | Requirements and P0 acceptance design | Not shipped as executable code or as a dependency |
| [`Rain3Dmetrology/github-release-management`](https://github.com/Rain3Dmetrology/github-release-management) | Commit `6c0c6641df245f172e5c1c163385ad9638c520a3` | Failure scenarios and requirements only | No source code, Skill instructions, README prose, changelog prose, or release script imported |
| [Agent Skills specification](https://agentskills.io/specification) | Public web specification reviewed on 2026-08-29 | Planned package and compatibility requirements | No implementation copied in P0 |
| [GitHub documentation](https://docs.github.com/) | Public documentation reviewed on 2026-08-29 | Platform behavior for README files, Rulesets, reusable workflows, tokens, and Releases | No GitHub-owned example workflow copied in P0 |
| [Business Source License 1.1](https://mariadb.com/bsl11/) and the legacy repository license | Version 1.1 / legacy commit above | License-boundary decision | No BSL-covered repository content imported |
| [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) | 2.0.0 | Planned version semantics | No release implementation in P0 |
| [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) | 1.1.0 | Changelog format guidance | No upstream prose copied beyond names and standard terms |
| [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt) | Version 2.0 standard legal text | Repository `LICENSE`; a locally installed standard copy was used | License text is not treated as original project-authored prose |

## Drafting method

1. Requirements and failure cases were extracted as functional constraints.
2. P0 policy, README prose, ADRs, and schemas were independently drafted for
   this repository; there was no automated file import or copy operation from
   the legacy repository.
3. No legacy `SKILL.md`, README, script, changelog, or git history was copied.
4. The repository contains no P0 runtime implementation, workflow, release
   command, or third-party source-code dependency.
5. A second reviewer challenged permission semantics, provenance claims, and
   unsupported comparison language before remote publication.

## Known limitations

This record documents the process used for P0. It does not establish a formal
two-team legal clean-room procedure, does not certify the copyright status of
every upstream idea, and is not a substitute for a rights review when future
work incorporates third-party code or protected text.

If future work incorporates third-party material, update
`THIRD_PARTY_NOTICES.md` and this log with the exact upstream revision,
license, files, modifications, and compatibility decision before release.
