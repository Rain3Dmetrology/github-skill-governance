# ADR-0002: Version and release authority

- Status: Accepted
- Date: 2026-08-29
- Scope: P0

## Context

A prompt-driven release Skill and release-please cannot both own version files,
tags, and GitHub Releases. Multiple owners create duplicate versions, moved
tags, partial releases, and unclear failure responsibility.

## Decision

1. The only planned normal-channel version authority is release-please.
2. Release-please will own version changes, changelog changes, the Release PR,
   the exact tag, and the Draft Release.
3. `release-consistency-gate` will remain read-only and return evidence plus
   PASS/WARN/BLOCK; it will never commit, tag, or publish.
4. `gh skill publish --dry-run` may validate compatibility after P3.
5. `gh skill publish --tag`, local `git tag`, `git push --tags`, and direct
   `gh release create` are forbidden in the normal channel.
6. P0 creates no version tag or Release. Release automation stays disabled
   until the P5 Saga and fault-injection tests pass.

## Public API used by SemVer

- Skill names, triggers, and promised behavior;
- script commands, arguments, structured output, and exit codes;
- governance schema fields;
- supported-host capabilities and install contracts;
- README claims marked as implemented.

## Consequences

- A release has one accountable owner.
- The repository cannot publish during P0–P4.
- An emergency release is a separate human-controlled break-glass procedure,
  not a hidden fallback inside a Skill.

## Verification

- `repo-policy.yaml` reports `release_owner_count: 1`.
- Every direct tag/release path is marked forbidden.
- No GitHub workflow, tag, Release, or release credential exists in P0.
