# P1 C Broker PR-B1 local candidate evidence

- Observed: 2026-09-03 (Asia/Tokyo)
- Branch: `feat/p1-c-broker-workflow`
- Remote base: `7291ce8a508a6fdf079760cfec973d81d24a29d2`
- Scope: canonical workflow, exact validator freeze, runtime corrections,
  tests, bilingual status, operator runbook, and threat-model alignment
- Authority class: W candidate only; no commit, push, PR, dispatch, approval,
  merge, tag, Release, Ruleset, Secret, or Environment mutation is evidenced by
  this record

## Remote truth before the candidate

Read-only GitHub API responses proved:

- PR #11 merged at `2026-08-31T05:45:36Z` as
  `7291ce8a508a6fdf079760cfec973d81d24a29d2`;
- `main` equals that SHA with parent
  `ab877261534b563b68c04fb2cebb40749be0fa6c`;
- Environment ID `20905500070`, reviewer `Rain3Dmetrology` ID `79391663`,
  `prevent_self_review=false`, one-minute timer, and
  `can_admins_bypass=false`;
- custom deployment policies enabled, with exactly one `main` policy of type
  `branch`, ID `58680218`;
- repository Actions Secrets, Environment Secrets, Environment Variables,
  tags, and Releases all had count zero;
- GitHub listed exactly one active workflow,
  `.github/workflows/governance-baseline.yml`.

These are point-in-time observations, not durable guarantees.

## Candidate workflow

`.github/workflows/c-merge-exact-pr.yml` is frozen byte-for-byte by
`scripts/validate_governance.py`. Its only trigger is `workflow_dispatch` with
three closed inputs: PR number, exact base SHA, and exact head SHA.

The workflow contains two jobs:

1. `prepare` uses `contents: read`, constructs the canonical manifest, and
   displays the exact approval comment in the job summary.
2. `consume` waits on `c-authorization` and receives only `actions: read`,
   `checks: read`, `contents: write`, and `pull-requests: read`. It invokes the
   fixed Python Broker and preserves exit code 2 as `RECOVERY_REQUIRED`.

The workflow has one global concurrency group, no matrix, no reusable or local
Action, no artifact transport, no generic endpoint or body input, no
`secrets.*` or `vars.*` reference, and no release, tag, package, or deployment
command. Both checkout steps pin
`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` and disable credential
persistence.

## Production corrections made during review

### Workflow-run path shape

A live Actions run readback showed `path` as
`.github/workflows/governance-baseline.yml`, without an `@main` suffix. The
Broker and fake API fixture were corrected to require the same exact path shape;
`github.workflow_ref` separately remains bound to `refs/heads/main`.

### Check-run pull-request association

The exact successful PR #11 check-run returned `pull_requests: []`. The Broker
therefore does not treat that optional array as an invariant. Association is
proved transitively and without ambiguity: the target PR head must equal the
authorized head SHA, while the required check name, check head SHA, successful
conclusion, and GitHub Actions App ID `15368` must all match that same SHA.

### Environment inventory permission boundary

GitHub documents `actions: read` for Environment and deployment branch-policy
readback. It documents `Environments: read` for listing Environment Secrets and
Variables, but that scope is not available in workflow `GITHUB_TOKEN`
permissions. The runtime therefore does not claim an impossible inventory
check or introduce a PAT/App Secret. The canonical workflow instead contains no
secret or variable context, so those inventories cannot be injected into the
Broker. Empty inventories remain activation and closure evidence.

Primary references:

- [Workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions)
- [Deployment environments](https://docs.github.com/en/rest/deployments/environments)
- [Deployment branch policies](https://docs.github.com/en/rest/deployments/branch-policies)
- [Environment Secrets](https://docs.github.com/en/rest/actions/secrets#list-environment-secrets)
- [Environment Variables](https://docs.github.com/en/rest/actions/variables#list-environment-variables)
- [Workflow approval history](https://docs.github.com/en/rest/actions/workflow-runs#get-the-review-history-for-a-workflow-run)
- [Merge a pull request](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request)

## Local verification

```text
python -B -m unittest discover -s tests -p "test_*.py" -v
53 tests passed

python -B scripts/validate_governance.py --root .
ok: true; errors: 0

python -B -m py_compile scripts/c_authorization_broker.py scripts/validate_governance.py scripts/github_preflight.py
passed

actionlint v1.7.12 -shellcheck= -pyflakes= .github/workflows/c-merge-exact-pr.yml .github/workflows/governance-baseline.yml
passed with no findings

uvx zizmor==1.30.0 --pedantic .github/workflows/c-merge-exact-pr.yml .github/workflows/governance-baseline.yml
passed offline with no findings after permission-purpose comments were added

bash -n for both embedded Broker run blocks
passed

local workflow shell simulation
prepare exited 0 and emitted the exact approval summary; consume attempt 2
exited 1 as ABORTED_PRE_EFFECT without a network request

git diff --check
passed
```

PyYAML also parsed the candidate as a mapping. That is syntax evidence only;
the independent actionlint result is the GitHub Actions semantic evidence.

## Remaining gates

This candidate is not remotely active and has not run with a job-scoped write
token. Before any production claim:

1. refresh the Review Gate against the final diff;
2. obtain explicit human authorization for commit, push, and PR creation;
3. require the real `governance-baseline` check and a separately authorized
   human merge of PR-B1;
4. run negative, replay, stale-input, and permission canaries;
5. use one disposable no-side-effect PR for the positive exact-merge canary;
6. commit independent readback in PR-B2 and close Issue #1 only after all
   acceptance items are proven.
