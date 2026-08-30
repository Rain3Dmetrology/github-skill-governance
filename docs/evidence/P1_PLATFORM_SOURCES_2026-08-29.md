# P1 platform-source record — 2026-08-29

- Scope: GitHub Rulesets, Actions permissions, merge settings, and private
  vulnerability reporting for a public user-owned repository
- Source policy: GitHub official documentation, official REST API, and the
  official `actions/checkout` repository only
- API version used for design: `2026-03-10`

## Primary sources

- [Managing rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets)
- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [Repository Rules REST API](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10)
- [Actions permissions REST API](https://docs.github.com/en/rest/actions/permissions?apiVersion=2026-03-10)
- [Managing GitHub Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
- [Update a repository](https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10#update-a-repository)
- [Configuring private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository)
- [`actions/checkout` v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1)

## Live facts used by P1

GitHub's API reported `actions/checkout` v7.0.1 as the latest release, published
2026-07-20. Its lightweight tag resolves to commit
`3d3c42e5aac5ba805825da76410c181273ba90b1`; the commit verification response
was `verified: true` with reason `valid`.

The target repository is public and user-owned. Rulesets are available, but
there is no organization team or second maintainer to satisfy independent
approval. P1 therefore requires a PR and deterministic check with zero required
approvals, records the limitation, and configures no bypass actor.

## Revalidation triggers

Re-run this research and update the desired-state files when any of the
following changes:

- GitHub plan or repository visibility;
- repository owner or default branch;
- required check name or GitHub App identity;
- allowed Action revision;
- maintainer count or independent-review policy;
- P5 release-authority activation.
