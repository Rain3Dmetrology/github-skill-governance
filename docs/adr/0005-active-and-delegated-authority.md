# ADR-0005: Active authority, delegated authority, and connector capability

- Status: Accepted
- Date: 2026-08-29
- Scope: P0 correction
- Supersedes: ADR-0002 verification item 1; ADR-0004 decision rules 4 and 6

## Context

The original P0 wording conflated three different facts:

1. a connector or account can technically call an API;
2. a human has delegated a bounded action in the current task; and
3. an automation is the active owner of a standing capability.

It also described `release-please` as the sole future authority while a machine
field could be read as if that authority were already active. These ambiguities
are fail-open when a connector exposes administration across several
repositories.

## Decision

1. No version or release automation is active through P4. The active version
   authority is `null`; `release-please` remains the only planned normal-channel
   authority and cannot activate before the P5 gate.
2. `Rain3Dmetrology` is the accountable human maintainer. That identity is not
   an automated release executor and does not give a Skill standing authority.
3. An interactive connector may expose more technical capability than the
   current task delegates. Capability is never treated as authorization.
4. Each GitHub mutation must remain inside the current explicit task, declare
   R/W/C class, identify the repository and ref, and pass the required
   preflight. C actions remain per-action commitments.
5. No Skill stores raw credentials or infers write, merge, tag, Release,
   Ruleset, Secret, or deployment authority from connector availability.
6. This ADR is not an authorization receipt and grants no current or future
   mutation. Every C action requires fresh adjacent authorization and fresh
   preflight evidence; point-in-time receipts must identify the repository,
   ref, action, and result.
7. The legacy `github-release-management` Skill receives no delegated write,
   tag, or Release authority. An interactive task actor's capability does not
   attach to that Skill. It stays an evidence source until a later independently
   reviewed migration decision.

## Consequences

- Cross-repository interactive use can remain convenient without converting a
  broadly capable connector into an ambient release credential.
- Compromise of the interactive account still has a larger technical blast
  radius than a repository-scoped GitHub App. This is an accepted residual risk
  for P0/P1 and must be reduced before unattended writes are introduced.
- The repository must record both a named semantic-review owner and the
  single-maintainer limitation instead of implying independent review.

## Verification

- `repo-policy.yaml` separates active and planned version/release authority.
- `owners.yaml` records the human owner, self-review model, and Skill denials.
- P0 remote evidence distinguishes repository-visible automation from
  account-level installation visibility.
- No raw credential or release executor is stored in this repository.
