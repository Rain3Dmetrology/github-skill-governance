# ADR-0009: GitHub-native single-use C authorization

- Status: Accepted architecture; remote activation pending
- Date: 2026-08-31
- Issue: [#1](https://github.com/Rain3Dmetrology/github-skill-governance/issues/1)

## Context

P1 established deterministic repository controls and a read-only identity
preflight. It deliberately did not make a credential, chat message, issue
comment, or reusable receipt into authorization. The remaining requirement is a
trusted C-authorization mechanism that is fresh, bound to one exact action, and
consumed together with that action.

An approval attached only to a workflow run is insufficient. The approver must
be able to see and approve a digest that commits to the repository, workflow,
run, operation, PR, base and head revisions, policy, and expiry. A rerun must
not reuse the approval.

## Decision

Use a protected GitHub Environment named `c-authorization` as the trusted
authorization surface. GitHub's deployment review is the issuance event. A
standard-library-only executor verifies the server-side approval history and
performs one allowlisted operation.

The first and only supported route is `merge-exact-pr`:

- repository ID `1350230486` and full name are fixed;
- base branch is `main` and both base and PR head SHA are bound;
- the required `governance-baseline` check must succeed from GitHub Actions App
  ID `15368`;
- the PR must be open, non-draft, and mergeable;
- the merge method is always squash;
- the executor issues at most one mutation request;
- readback proves that the squash commit has exactly the authorized base SHA as
  its parent, closing the preflight-to-merge race;
- a transport-ambiguous result is reconciled by readback and becomes
  `RECOVERY_REQUIRED` when the effect cannot be proven.

The future canonical workflow path is
`.github/workflows/c-merge-exact-pr.yml`. It is intentionally absent in PR-B0.
The closed request manifest is
`.github/governance/c-authorization-broker.schema.json`; the workflow revision
must equal the expected `main` base SHA, which transitively binds the executor
and repository policy at the approved revision.

The exact approval comment is `APPROVE-C1 sha256:<request-digest>`. The digest
uses canonical JSON and includes `run_id` and `run_attempt`. Only attempt 1 is
accepted, and the request expires after 600 seconds.

There is no generic API route, arbitrary endpoint, arbitrary request body,
shell fragment, matrix, reusable action, or second C operation behind the same
approval. Tags, Releases, Rulesets, Secrets, visibility, and deployments remain
outside this route and remain denied.

## Permission and activation boundary

Creating or changing the Environment is itself a C action and requires fresh,
adjacent human authorization. Installing code on a feature branch and opening a
PR is W. Merging each PR is C.

Activation is deliberately split:

1. **PR-B0** freezes the contract, desired Environment state, threat model,
   dormant executor, and local tests. It adds no active C workflow.
2. After PR-B0 is accepted, the maintainer separately authorizes creation of
   the Environment. Exact API readback and the UI-only administrator-bypass
   setting are verified before proceeding.
3. **PR-B1** adds one canonical `workflow_dispatch` workflow only after the
   protected Environment exists.
4. Negative, replay, stale-input, and positive canaries are run remotely.
5. **PR-B2** records evidence. Issue #1 closes only after one exact PR has been
   merged through the Broker and the effect has been independently read back.

A workflow must never reference an absent Environment: GitHub could otherwise
create an unprotected Environment implicitly.

## Single-maintainer residual

The repository currently has one maintainer. `prevent_self_review` is therefore
`false`; setting it to `true` would make the owner unable to approve their own
dispatch. This is a two-action self-approval control, not independent
two-person review. The approval digest, short expiry, server history, exact
route, and post-effect verification reduce but do not eliminate owner-account
compromise risk.

Administrator bypass must be disabled in the GitHub UI. The desired-state REST
payload does not assert that UI-only control, so it remains a mandatory manual
readback item rather than a fabricated machine guarantee.

## Secrets and legacy release Skill

This Broker route requires no repository or Environment Secret. It uses the
job-scoped `GITHUB_TOKEN` only after Environment approval. It does not grant the
existing `github-release-management` Skill write, tag, or Release authority and
does not modify that repository.

## Rejected alternatives

- **Reusable signed approval string:** transferable and separable from the
  effect; server-side single consumption would require a new durable service.
- **Issue or PR comment as authorization:** easy to replay and not protected by
  an Environment gate.
- **Generic privileged workflow:** a standing repository administration
  backdoor with an unbounded mutation surface.
- **LLM GO/NO-GO report:** useful review evidence, but not a trusted issuance or
  atomic consumption mechanism.
- **Long-lived PAT in a Secret:** unnecessary privilege and a second credential
  lifecycle for a route that GitHub can execute with a job-scoped token.

## Consequences

The route is intentionally narrow and operationally slower than auto-merge.
Every C action is inspectable, action-bound, expiring, and separately approved.
New C operations require a new ADR, exact workflow, permission set, threat
model update, and remote negative tests; they are not added as parameters to
this executor.
