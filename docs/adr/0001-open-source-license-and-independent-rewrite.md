# ADR-0001: Open-source license and independent-rewrite boundary

- Status: Accepted
- Date: 2026-08-29
- Scope: P0

## Context

The earlier `Rain3Dmetrology/github-release-management` repository uses the
Business Source License 1.1. That license explicitly is not an open-source
license during its restricted period. The new repository is intended to be a
general-purpose open-source governance stack.

Changing the old repository's license would also require a verified rights and
provenance review. P0 must not depend on that unresolved question.

## Decision

1. Create a separate repository named `github-skill-governance`.
2. License original repository content under Apache License 2.0.
3. Do not copy source text, scripts, or README prose from the BSL repository.
4. Treat the old repository only as a requirements and failure-scenario input.
5. Require `THIRD_PARTY_NOTICES.md` for every future incorporated dependency or
   text source.
6. Block release when provenance or license compatibility is unknown.
7. Record reviewed inputs, exclusions, and drafting method in
   `docs/provenance/P0_SOURCE_LOG.md`.

This is an independently drafted implementation policy, not a formal legal
clean-room procedure or certification. The project did not use a documented
two-team isolation process, and this ADR must not be cited as proof that every
possible copyright or provenance question has been legally resolved.

## Consequences

- The new repository starts with an explicit open-source and provenance
  boundary.
- Useful ideas from the old repository must be independently re-expressed and
  backed by tests before implementation.
- Existing history, stars, and releases are not migrated.
- This record does not decide ownership of the old repository's content.

## Verification

- `LICENSE` contains the standard Apache License 2.0 text.
- `THIRD_PARTY_NOTICES.md` records the deliberate-copying policy and its limits.
- `docs/provenance/P0_SOURCE_LOG.md` identifies reviewed inputs and exclusions.
- `repo-policy.yaml` sets `text_or_code_copy_allowed: false` for the old repo.
