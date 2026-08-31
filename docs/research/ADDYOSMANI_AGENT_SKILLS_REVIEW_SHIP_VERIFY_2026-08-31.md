# Review / ship / verify research note

- Evaluated: 2026-08-31
- Upstream repository: [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills)
- Evaluated revision: `d2c37ef6225dd8726cdd369a8030307f48592d26`
- Evaluated release: [`0.6.8`](https://github.com/addyosmani/agent-skills/releases/tag/0.6.8)
- Upstream license: [MIT](https://github.com/addyosmani/agent-skills/blob/0.6.8/LICENSE)
- Reuse mode here: ideas and failure scenarios only; independent wording and
  implementation

## Provenance statement

This is a personal open-source skills repository maintained by Addy Osmani. His
[biography](https://addyosmani.com/bio/) describes his Google engineering
leadership role, while his [personal-site disclaimer](https://addyosmani.com/about/)
states that the views are personal. It is therefore evidence informed by a
Google engineering leader, not an official Google Skill collection or Google
endorsement.

## What is useful

The repository supplies a concise lifecycle router, a multi-dimensional review
model, a standing Definition of Done, independent specialist review patterns,
and rollback-before-GO discipline. Relevant upstream artifacts include the
[`review` command](https://github.com/addyosmani/agent-skills/blob/0.6.8/.claude/commands/review.md),
[`ship` command](https://github.com/addyosmani/agent-skills/blob/0.6.8/.claude/commands/ship.md),
[`code-review-and-quality` Skill](https://github.com/addyosmani/agent-skills/blob/0.6.8/skills/code-review-and-quality/SKILL.md),
[`definition-of-done`](https://github.com/addyosmani/agent-skills/blob/0.6.8/references/definition-of-done.md),
and [`orchestration-patterns`](https://github.com/addyosmani/agent-skills/blob/0.6.8/references/orchestration-patterns.md).

These ideas improve this repository's loop as follows:

```text
DEFINE -> PLAN -> BUILD -> VERIFY -> REVIEW
       -> AUTHORIZE -> SHIP -> VERIFY EFFECT -> RECONCILE
```

The added `AUTHORIZE`, `VERIFY EFFECT`, and `RECONCILE` states are essential.
Code quality review is evidence; it is not authority. A successful command is
not proof of its external effect, and a timeout after a mutation is not an
ordinary failure.

## What is deliberately not adopted

| Upstream pattern | Decision | Reason |
|---|---|---|
| LLM-generated `/ship` GO/NO-GO | Advisory evidence only | It does not issue or atomically consume trusted C authorization. |
| User acceptance of a reported critical risk | Rejected for security, authorization, and data-integrity gates | A human may accept a product trade-off, but cannot make a failed invariant true. |
| Floating major action versions or unpinned current CLI | Rejected | Mutable dependencies violate deterministic governance. |
| Generic auto-merge or generic rollback push | Rejected | Merge is C; rollback after merge is another reviewed PR and another C action. |
| Persona-selected policy override | Rejected | A persona cannot replace CODEOWNERS, policy, exact repository identity, or server-side approval. |
| A tag treated as immutable authority | Rejected | Git refs are movable unless separately protected and verified. |

## Official Google cross-check

The adopted principles were checked against primary Google engineering sources,
not inferred from the personal repository alone:

- Google's [review standard](https://google.github.io/eng-practices/review/reviewer/standard.html)
  prioritizes net code-health improvement rather than perfection.
- [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
  supports correctness, design, complexity, tests, naming, comments, style, and
  documentation as separate review dimensions.
- [Small CL guidance](https://google.github.io/eng-practices/review/developer/small-cls.html)
  supports narrow, independently reviewable PRs such as PR-B0/B1/B2.
- Google SRE's [release engineering](https://sre.google/sre-book/release-engineering/)
  separates repeatable build/release mechanics from ad hoc human execution.
- The SRE Workbook's [canarying guidance](https://sre.google/workbook/canarying-releases/)
  supports a bounded canary before broader rollout.
- Google Cloud Deploy documents [manual approval](https://cloud.google.com/deploy/docs/create-pipeline-targets#require_manual_approval_for_a_deployment)
  and [deployment verification](https://cloud.google.com/deploy/docs/verify-deployment)
  as distinct controls, matching this repository's authorization/effect split.
- [SLSA provenance](https://slsa.dev/spec/v1.2/provenance) and
  [artifact verification](https://slsa.dev/spec/v1.2/verifying-artifacts) support
  binding evidence to exact subjects rather than trusting names alone.

## Resulting stack decision

Use the upstream package as a pattern library, not as a privileged dependency.
No upstream workflow or command receives GitHub write capability. The local
stack keeps one-level orchestration, fans out independent read-only reviewers,
requires a standing Definition of Done plus per-operation acceptance predicate,
and routes every C effect through a narrow, separately activated Broker.

This separation preserves the useful low-friction review experience without
turning an AI quality report into repository authority.
