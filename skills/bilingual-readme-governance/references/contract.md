# Bilingual README contract v1

The deterministic validator proves structure, parity, selected evidence
signals, and local-link integrity. It does not prove that prose or comparisons
are true.

## Required pair

- `README.md` is English.
- `README.zh-CN.md` is Simplified Chinese.
- Each file links directly to the other within the first six non-empty lines;
  a link in code or outside the `language-switch` section does not count.
- Both use paired markers shaped as
  `<!-- readme-contract:section:SECTION-ID -->` and
  `<!-- /readme-contract:section:SECTION-ID -->`.

Both locales require these IDs: `language-switch`, `value-proposition`,
`why-this-repo`, `quick-start`, `comparison-and-tradeoffs`,
`current-limitations`, `mitigations`, `compatibility`, `evidence`, `roadmap`,
`security`, and `license`. Extra IDs are allowed only when present in both
locales.

## Content gates

- Value: one paragraph within the first 12 non-empty lines; no more than 25
  English words or 45 Chinese characters, with exactly one sentence terminator.
- Comparison: a visible non-empty table, a visible real ISO calendar date, and
  at least one visible non-anchor text evidence link. Images and unused link
  definitions do not satisfy the evidence gate.
- Limitations and mitigations: each contains a non-empty Markdown table.
- Evidence: contains at least one link.
- Inline Markdown, reference-style, image, and HTML `href`/`src` links are
  checked outside code spans and fences. Repository-relative links must use
  exact path casing, remain inside the repository, and resolve to files.
  Unsafe URI schemes fail; external links are inventoried but not fetched.
- Canonical README files must be regular files no larger than one megabyte;
  symbolic links are rejected before reading.
- Claim IDs: any `readme-contract:claim:...` markers have exact locale parity.

## Semantic gate

A human or task-scoped reviewing agent must separately verify that the value
sentence is specific, advantages and disadvantages are fair, mitigations are
credible, claims match evidence, both locales preserve meaning, and existing
repository/legal content was not silently dropped. Record that reviewer and
the exact revision in the PR or evidence note.

## Authority boundary

The bundled commands are read-only. Editing the README pair is a reversible
repository write and requires task-scoped authorization. Merge, tag, Release,
deployment, Secret, and repository-control changes are outside this Skill.
