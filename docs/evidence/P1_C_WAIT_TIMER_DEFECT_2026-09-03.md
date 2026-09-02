# P1 C Broker wait-timer compatibility defect

- Observed run: `33660227703`
- Target PR: `#13`
- Authorized base: `306fecf26fdcd641d36b06c6858db63a9f94cf2e`
- Authorized head: `d457350a627b22a5d20c6671aee3c20ed9e523b9`
- Result: `ABORTED_PRE_EFFECT`

GitHub's approval-history endpoint returned two records after the configured
one-minute timer elapsed: one automatic approval from `github-actions[bot]`
with comment `1 minute wait timer`, followed by the maintainer's deployment
approval. The original Broker required the entire history to contain one
record, so every approved run would fail closed as
`approval_history_ambiguous`.

The correction distinguishes and validates both records. It requires exactly
one trusted timer record, exactly one maintainer record, and the same positive
Environment ID on both. Missing, duplicate, malformed, wrong-actor, wrong-
Environment, and wrong-comment variants remain pre-effect failures.

Independent readback after the discovery proved that `main` remained
`306fecf26fdcd641d36b06c6858db63a9f94cf2e` and PR `#13` remained open and
unmerged. This document records the defect and proposed correction; it does not
claim that the correction is remotely active or that the positive canary has
passed.
