# Security Policy

## Current scope

This repository has accepted P1 platform enforcement and contains governance
documents, validators, tests, one read-only CI workflow, and one active,
Environment-gated C-authorization workflow. The `c-authorization` Environment
and canonical exact-squash workflow are active, and remote negative, replay,
and positive canaries have exercised the one-route Broker. The current
single-owner approval and non-exclusive `main` route remain explicit blockers
to a production C-grade authorization boundary.

The repository holds no deployment or release credentials, GitHub App keys, or
production tokens. The Broker receives a job-scoped `GITHUB_TOKEN` only after
Environment approval and exposes no tag or Release operation. An interactive
connector may have broader technical capability, but that capability is not
standing authority delegated to a Skill.

## Report a vulnerability

Do not disclose credentials or exploitable details in a public Issue.

Use [GitHub Private Vulnerability Reporting](https://github.com/Rain3Dmetrology/github-skill-governance/security/advisories/new).
The repository API returned `enabled: true` on 2026-08-30. If GitHub makes that
route unavailable, contact the repository owner through a private channel
already known to you and reference only a non-sensitive tracking identifier in
public.

P1 verified that the private route remained enabled before accepting the
executable validator and workflow; later phases must revalidate it.

## Sensitive data

Never submit:

- API keys, PATs, private keys, cookies, or `.env` contents;
- private client, project, machine, or network identifiers;
- user-specific absolute filesystem paths;
- unredacted logs that contain authentication or personal data.

If a credential reaches Git history, treat it as compromised and rotate it.
Deleting the visible file is not sufficient.

## Permission boundary

P1 grants no Skill standing merge, tag, Release, Ruleset, Secret, or deployment
authority. The active merge route is constrained by ADR-0009: every dispatch
binds one exact repository, workflow revision, pull request, base, head, check,
reviewer, approval digest, and expiry before one squash-merge request is
allowed. It does not create tags or Releases and grants the legacy
`github-release-management` Skill no authority.

The route is not production-closed while the dispatcher and approver share one
owner identity, `prevent_self_review` remains false, and ordinary owner merges
can bypass the Broker. Production closure requires a distinct least-privilege
identity, independent approval, and exclusive serialization of `main` updates.
See ADR-0004, ADR-0005, ADR-0009, and `docs/P1_C_BROKER_ACCEPTANCE.md` for the
R/W/C model, activation evidence, and remaining blockers.
