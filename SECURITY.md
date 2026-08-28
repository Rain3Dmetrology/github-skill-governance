# Security Policy

## Current scope

This repository is in P0 and contains governance documents only. It does not
hold deployment credentials, release credentials, GitHub App keys, production
tokens, or write-capable automation.

## Report a vulnerability

Do not disclose credentials or exploitable details in a public Issue.

Once the GitHub repository is created, use GitHub Private Vulnerability
Reporting when it is enabled. Until then, contact the repository owner through
a private channel already known to you and reference only a non-sensitive
tracking identifier in public.

P1 must enable or document the private reporting route before any executable
script or workflow is accepted.

## Sensitive data

Never submit:

- API keys, PATs, private keys, cookies, or `.env` contents;
- private client, project, machine, or network identifiers;
- user-specific absolute filesystem paths;
- unredacted logs that contain authentication or personal data.

If a credential reaches Git history, treat it as compromised and rotate it.
Deleting the visible file is not sufficient.

## Permission boundary

P0 grants agents no merge, tag, Release, Ruleset, Secret, or deployment
permission. See ADR-0004 for the R/W/C model.
