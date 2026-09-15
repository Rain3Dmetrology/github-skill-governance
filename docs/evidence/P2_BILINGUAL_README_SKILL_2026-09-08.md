# P2 bilingual README Skill evidence

- Date: 2026-09-08
- Immutable canary date: 2026-09-16
- Package: `skills/bilingual-readme-governance`
- Package version: `1.0.0`
- Source commit: `0e015e8229904d6233d1fe870c33072462fea79a`
- Exact package tree OID: `7839d1e7962766193e7af2711166b0b3f2ed75b3`
- Network used by canaries: no
- Target mutation by `validate` or `plan`: no

## Canary matrix

| Target | Route | Expected | Observed |
|---|---|---|---|
| This repository | packaged `validate` | PASS | PASS |
| Arbitrary sandbox repository | packaged `validate` then `plan` | PASS and byte-identical | PASS and byte-identical |
| Draft templates | packaged `validate` | FAIL until placeholders are replaced | FAIL |
| Missing Chinese locale | packaged `validate` | FAIL | FAIL |
| Repository path escape | packaged `validate` | FAIL | FAIL |
| Section and claim mismatch | packaged `validate` | FAIL | FAIL |
| Codex-style copied Skill directory | archive from source commit, isolated Python execution | PASS | PASS |
| Claude-style copied Skill directory | archive from source commit, isolated Python execution | PASS | PASS |

The two copied-directory runs are filesystem portability tests. They do not
attest that a particular Codex or Claude product version invoked the Skill.
Both copies were extracted from the source commit above, not from the mutable
working tree. The Skill tree OID remained unchanged after this evidence-only
update.

## Verification commands

```text
python3 -I -m unittest discover -s tests -p 'test_*.py'
python3 -I skills/bilingual-readme-governance/scripts/readme_governance.py validate --root .
python3 -I skills/bilingual-readme-governance/scripts/readme_governance.py plan --root .
python3 <skill-creator>/scripts/quick_validate.py skills/bilingual-readme-governance
python3 -I scripts/validate_governance.py --root .
```

Observed on the immutable source commit: 83 tests passed; the repository
governance validator reported zero errors across 86 tracked candidate files;
the packaged README validator and Skill quick validator passed.

## Semantic review receipt

- Reviewer: task-scoped Codex agent. A separate agent cross-check found and
  drove fixes for multiple deterministic bypasses. Its final rerun after the
  last shortcut-reference fix was interrupted by an account usage limit, so
  this is not an independent final attestation, independent human approval, or
  a claim about the maintainer's personal review.
- Scope: maximum-value sentence, reason to choose, comparison and date,
  disadvantages, mitigations, evidence, language parity, and license notice.
- Result: task-agent accepted for P2a with the independent-final-review and
  host-certification limitations retained.
- Preserved: Apache-2.0 license link, third-party notices, P0/P1 evidence,
  security boundaries, and disabled Release authority.

No tag, Release, Secret, deployment, AI reviewer, auto-merge, direct-main
write, or standing cross-repository permission is introduced by this package.
