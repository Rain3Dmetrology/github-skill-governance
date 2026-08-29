# ADR-0006: Normalized permission schema

- Status: Accepted
- Date: 2026-08-29
- Scope: P0 correction
- Supersedes: ADR-0004 Decision-table R/W examples and machine-field
  verification wording only

## Context

The P0 policy used `allowed_by_default` for R and W but
`allowed_for_agents_by_default` plus `delegable_per_action` for C. A validator
would need class-specific interpretation, and a missing or unknown field could
silently become permissive. Two examples were also misclassified: writing a
local report changes filesystem state, and GitHub Issues do not have a normal
draft state.

## Decision

Every permission class uses the same required fields:

- `default_decision`: `allow` or `deny`;
- `delegation_mode`: `standing`, `task-scoped`, or `per-action`;
- `requires`: a list, including an empty list when no extra evidence is needed;
- `examples`: non-normative examples that match the class definition.

Unknown classes, unknown enum values, missing fields, or contradictory fields
must fail closed. R cannot write a file or shared state. Local patches and
normal Issues are W. Merge, tag, Release, Ruleset, Secret, and deployment
changes remain C.

## Consequences

- One validator can process R, W, and C without class-specific aliases.
- Policy readers can distinguish response-only analysis from local writes.
- P1 must ship a schema and negative fixtures before platform enforcement is
  considered complete.

## Verification

- `repo-policy.yaml` schema version 2 uses the normalized fields for all three
  classes; executable unknown-field rejection remains a P1 deliverable.
- P1 tracking issue #1 owns the executable preflight and fail-closed checks.
