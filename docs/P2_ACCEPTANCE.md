# P2 bilingual README Skill acceptance

- Issue: [#9](https://github.com/Rain3Dmetrology/github-skill-governance/issues/9)
- Scope: one self-contained, offline Agent Skill for bilingual README
  governance
- Authority: read-only by default; task-scoped README writes only; no standing
  GitHub or C authority

## Package

- [x] `SKILL.md` contains precise invocation and R/W/C routing.
- [x] `agents/openai.yaml` contains valid UI metadata and no tool dependency.
- [x] The standard-library validator and contract travel inside the Skill.
- [x] Paired English and Simplified Chinese templates are drafting aids and
  fail validation until their placeholders are replaced.

## Deterministic contract

- [x] Canonical reciprocal language links are required.
- [x] Required section IDs and all optional section/claim IDs have locale
  parity.
- [x] The value proposition is early, one paragraph, and length bounded.
- [x] Comparison requires a non-empty table, ISO assessment date, and evidence
  link.
- [x] Limitations and mitigations require non-empty tables.
- [x] Local links must remain inside the repository and resolve to files.
- [x] External links are inventoried but explicitly not fetched.
- [x] Deterministic PASS still reports semantic review as required and
  unattested.

## Safety and portability

- [x] `validate` and `plan` are offline and perform no mutation.
- [x] `plan` reports the only later W scope as the two README files.
- [x] Merge, tag, Release, deployment, Secret, direct-main, and repository
  control effects are explicitly forbidden.
- [x] An arbitrary sandbox repository passes without byte changes.
- [x] Missing locale, path escape, broken structure, placeholder, parity, and
  empty-marketing-shell cases fail closed.
- [x] The Skill executes after copy into isolated Codex-style and Claude-style
  directory layouts.
- [x] This repository passes the same packaged validator.

## Semantic review

- [x] The maintainer-owned repository text was reviewed for value, choice,
  fair comparison, limitations, mitigations, evidence, and license retention.
- [x] Directory-layout portability is not represented as live product-host
  certification.
- [x] Rollback before merge is closing the PR; no post-merge rollback claim is
  made.

Exact package content and test evidence are recorded in
[`P2_BILINGUAL_README_SKILL_2026-09-08.md`](./evidence/P2_BILINGUAL_README_SKILL_2026-09-08.md).
