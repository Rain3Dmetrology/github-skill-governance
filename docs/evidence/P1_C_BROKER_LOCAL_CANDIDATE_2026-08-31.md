# P1-C Broker PR-B0 local candidate evidence

- Evidence date: 2026-08-31
- Baseline `main`: `af399df2b35ee48be3e583b2a67e4d1aeb5e57c1`
- Candidate branch: `feat/p1-c-authorization-broker`
- Scope: contracts, desired state, dormant executor, tests, threat model, and
  research only; no Broker workflow

## Local verification

Commands:

```text
python -m unittest discover -s tests -p 'test_*.py'
python scripts/validate_governance.py --root .
git diff --check
python -m py_compile scripts/c_authorization_broker.py scripts/validate_governance.py scripts/github_preflight.py
```

Observed result:

- 49 tests passed;
- governance validation passed with the complete candidate tracked-file set and
  0 errors;
- diff whitespace validation passed;
- all three Python scripts compiled;
- the deterministic `prepare` example produced canonical JSON, a
  `sha256:<64-lowercase-hex>` digest, and the exact
  `APPROVE-C1 sha256:<digest>` approval comment;
- the redaction test output contained no injected credential, authorization
  header, or local absolute path.

The tests cover canonical field binding, unknown manifest rejection, exact
reviewer/comment/Environment approval, one-record approval history, run event,
attempt, branch, workflow path and SHA drift, 600-second expiry, Environment
configuration drift, repository/base/head identity, draft and mergeability,
required-check App identity and PR association, one exact squash merge,
ambiguous-effect reconciliation without mutation retry, response/readback SHA
agreement, exact `main` tip verification, stable CLI fields and exit codes, and
redaction.

## Point-in-time remote readback

Read-only `gh api` calls returned:

| Surface | Observed |
|---|---|
| Repository ID | `1350230486` |
| Default branch | `main` |
| `main` SHA | `af399df2b35ee48be3e583b2a67e4d1aeb5e57c1` |
| Environments | 0 |
| Actions Secrets | 0 |
| Active Workflows | one: `.github/workflows/governance-baseline.yml` |
| Auto-merge | false |
| Squash merge | true |
| Tags | 0 |
| Releases | 0 |

No remote mutation was performed. In particular, the
`c-authorization` Environment and `.github/workflows/c-merge-exact-pr.yml`
do not exist remotely.

## Honest boundary

This evidence accepts PR-B0 as a dormant candidate only. It does not prove
trusted issuance, remote single consumption, or a merge effect. Those require
the separately authorized Environment activation, PR-B1 canonical workflow,
negative/replay runs, and a positive Broker canary recorded by PR-B2.
