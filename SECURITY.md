# Security Policy

## Current scope

This repository has accepted P1 platform enforcement and contains governance
documents, validators, tests, and one read-only CI workflow. PR-B0 also defines
a dormant, one-route C-authorization executor, but no workflow invokes it and
the required protected Environment does not yet exist. The repository holds no
deployment credentials, release credentials, GitHub App keys, production
tokens, or active write-capable automation. An interactive connector may have
broader technical capability, but that capability is not standing authority
delegated to a Skill.

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
authority. The dormant merge route is constrained by ADR-0009 and remains
unusable until the protected Environment, canonical workflow, negative tests,
and per-action approval loop are activated and verified in separate stages. See
ADR-0004 and ADR-0005 for the R/W/C and delegation models.
