# ADR-0003: Bilingual README contract

- Status: Accepted
- Date: 2026-08-29
- Scope: P0

## Context

A single README containing complete English and Chinese copies doubles page
length and provides navigation rather than a real language switch. Two files
improve reading but drift unless their shared facts are machine-checkable.

## Decision

1. `README.md` is the English default for a general public repository.
2. `README.zh-CN.md` is the Simplified Chinese view.
3. Both files use reciprocal relative links at the top.
4. Both files contain the same stable section IDs and claim IDs in the same
   order; prose can be naturally localized instead of translated line by line.
5. Implemented claims need evidence. Planned claims need a GitHub Issue.
6. Comparative claims need a date and evidence. Quantitative claims need a
   reproducible benchmark.
7. The first screen contains the project name, one verifiable value sentence,
   language switch, and Quick Start entry.
8. A human owner reviews semantic equivalence, value, comparison fairness, and
   limitations. CI will verify structure and evidence in P2.

## Consequences

- Readers can switch languages without loading duplicated prose.
- Translation freedom is preserved while product facts remain aligned.
- Marketing statements cannot silently become shipped capabilities.
- P0 freezes the contract but does not yet implement the checker.

## Verification

- `.github/governance/readme-contract.json` parses as JSON.
- Both README files contain every required section and identical claim IDs.
- Reciprocal language links resolve locally.
