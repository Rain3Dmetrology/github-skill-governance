# Engineering Skill and AI-native loop assessment

- Evaluated: 2026-08-31
- Community source: [`mattpocock/skills`](https://github.com/mattpocock/skills)
- Fixed community revision: `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`
- Community license: [MIT](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/LICENSE)
- Primary vendor source: [Anthropic AI-Native SDLC Playbook](https://academy.claude.com/courses/ai-native-sdlc-playbook)
- Reuse mode: ideas and failure scenarios only; independent wording and
  implementation

## Executive decision

Adopt the small-skill routing, tight feedback-loop, fixed-point review, and
versioned-artifact ideas. Do not install either repository wholesale and do not
install `claude-code-action` in the current phase.

The useful combined loop is:

```text
INTENT -> SPEC -> PLAN -> RED-CAPABLE LOOP -> IMPLEMENT
       -> DETERMINISTIC VERIFY -> INDEPENDENT REVIEW
       -> C AUTHORIZE -> EFFECT -> READBACK -> RECONCILE
       -> METRIC BREACH -> NEW INTENT
```

The last four states are local hardening. Neither an AI review nor a hook's
natural-language GO result is C authorization, and an apparently successful
command is not proof of external effect.

## `mattpocock/skills`: model-invoked set

The pinned [engineering index](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/README.md)
separates explicitly invoked setup/orchestration from narrowly triggered model
skills. That split is useful: installing and publishing remain explicit;
diagnosis, TDD, research, domain modeling, and review may be routed by task
shape.

| Skill pattern | Adopt | Adapt or reject |
|---|---|---|
| [`diagnosing-bugs`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/diagnosing-bugs/SKILL.md) | Require one already-run, red-capable, deterministic feedback command before a bug fix; minimise and preserve the regression case. | Production instrumentation remains a separate W/C decision; captured traces must be redacted and fixture-safe. |
| [`research`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/research/SKILL.md) | Prefer primary sources and commit one cited research note. | Background-agent use is an execution optimization, not an evidence class. The note remains independently reviewable. |
| [`tdd`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/tdd/SKILL.md) | Test public seams, use vertical red/green slices, reject tautological tests. | Freeze seams in the accepted spec/contract; do not interrupt autonomous work to reconfirm every already-frozen seam. |
| [`codebase-design`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/codebase-design/SKILL.md) | Small interface, deep implementation, injected adapters. This maps to pure Broker core plus one GitHub adapter. | Do not add hypothetical adapters. A second real host or transport is required before generalizing. |
| [`domain-modeling`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/domain-modeling/SKILL.md) | Keep capability, authority, receipt, effect, and recovery terms distinct and write irreversible trade-offs as ADRs. | Do not create an ADR for every small implementation choice. |
| [`code-review`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/code-review/SKILL.md) | Pin a merge-base and keep Standards and Spec reviews separate so one cannot hide the other. | Two axes are insufficient for privileged automation. Add Security/Authority, Tests/Evidence, and External Effect/Reconciliation. Blocking policy failures are still ranked above style findings. |
| [`resolving-merge-conflicts`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/resolving-merge-conflicts/SKILL.md) | Trace both sides to primary intent and verify after resolving. | Reject the unconditional “never abort” rule. Aborting is correct when the operation is wrong, the base is untrusted, or preserving both intents would invent behavior. |
| [`wizard`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/wizard/SKILL.md) | A human-owned, idempotent setup guide can reduce UI mistakes. | It must not be model-invoked for Secrets or C settings. The agent must not collect a production credential merely because hidden input is available. |
| [`prototype`](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/engineering/prototype/SKILL.md) | A throwaway branch may test a state model before production code. | It is evidence of a design exploration, not a test, release artifact, or authority source. |

## Anthropic AI-Native SDLC Playbook

Anthropic's [playbook introduction](https://academy.claude.com/courses/ai-native-sdlc-playbook/introduction)
uses a committed artifact chain across Plan, Design, Build, Test, Deploy, and
Maintain. `intent.md`, `spec.md`, `plan.md`, the diff/tests, review record, and
incident record become handoff and audit evidence. This is compatible with the
repository's receipt model if the artifacts have explicit status, subject SHA,
owner, and acceptance predicate.

The [CI/CD lesson](https://academy.claude.com/courses/ai-native-sdlc-playbook/ci-cd-integration-and-deployment)
recommends starting with read-only judgment work, then PR-only writes, sandboxed
agent jobs with short-lived scoped tokens and no standing production
credentials, allowlisted deployment MCP tools, environment-tiered autonomy, and
a rehearsed rollback. Those are architecture inputs, not a current install
instruction.

The [metrics-loop lesson](https://academy.claude.com/courses/ai-native-sdlc-playbook/closing-the-loop-on-metrics)
uses a deterministic control-band detector to invoke an agent, which writes a
new `intent.md`. Findings are triaged by a service owner, changes use the normal
PR gate, and only pre-approved runbooks may be invoked. That ordering is the
important control: detection may be automatic; commitment is still gated.

### Hooks are defense in depth, not the C authority

Anthropic's [hook-gate lesson](https://academy.claude.com/courses/ai-native-sdlc-playbook/hooks-as-approval-gates)
correctly recommends managed hooks, deny rules, sandbox enforcement, credential
stripping, controlled MCP sources, and minimum versions. Its simple example
checks a command substring and an environment variable. That is not sufficient
for this repository's C boundary because it does not bind a trusted approval to
the repository ID, run ID, exact subject SHA, operation, expiry, and one-shot
effect. The GitHub protected-Environment Broker remains authoritative; a hook
may only block earlier.

### Why `claude-code-action` is NO-GO now

Anthropic's current [GitHub Actions documentation](https://code.claude.com/docs/en/github-actions)
states that the official Claude GitHub App shares a permission set across
features, including read/write Actions, Checks, Contents, Issues, Pull Requests,
and Workflows, and GitHub cannot accept only a subset. The docs recommend a
custom App when a smaller permission set is required.

That permission surface directly conflicts with the current policy: no new AI
reviewer, no active agentic workflow, and no standing write authority before
the Broker is accepted. Therefore:

- do not install the official Claude GitHub App or Action in PR-B0, PR-B1, or
  P2a;
- do not add `ANTHROPIC_API_KEY`, subscription OAuth tokens, cloud-provider
  credentials, App private keys, or deployment MCP credentials now;
- if a later phase proves the need, start with a read-only `claude -p --bare`
  job, `dontAsk`, an explicit tool allowlist, egress deny-by-default, an exact
  Action SHA, no PR comments, and no repository write token;
- prefer GitHub OIDC/workload identity and a repository-specific service
  identity over a long-lived key when an organization actually requires
  Bedrock, Vertex AI, Microsoft Foundry, or the Anthropic API.

Anthropic's [non-interactive documentation](https://code.claude.com/docs/en/headless)
supports `claude -p`, structured output, explicit settings/MCP inputs, and bare
mode for reproducible CI. Bare mode is still a model runtime, not a deterministic
gate. Its output must be advisory and a deterministic script must decide the
machine result.

Claude Tag is currently described as a public beta for Slack in the loop
lesson. It is an intake adapter, not a trusted authorization channel, and is not
part of this repository's current stack.

## Metrics contract

The Playbook proposes the share of pipeline failures triaged without paging a
human as a leading indicator and DORA measures as lagging indicators. Current
[DORA guidance](https://dora.dev/guides/dora-metrics/) uses five measures, not
the older four-key shorthand: change lead time, deployment frequency, failed
deployment recovery time, change fail rate, and deployment rework rate.
Preserve the intent but tighten the definitions:

| Metric | Exact definition | Anti-gaming control | Phase |
|---|---|---|---|
| Autonomous triage rate | eligible failed CI runs with a machine-linked diagnosis and no human input before diagnosis / all eligible failed CI runs | Report eligibility exclusions, false diagnoses, and later human correction separately | P3+ |
| Time to red-capable loop | breach or failure timestamp to first deterministic command that reproduces the exact symptom | A summary-only model response does not count | P2+ |
| Proposal acceptance rate | agent proposals merged / proposals triaged | Also report dismissal reasons and denominator | P3+ |
| Repeat-incident rate | incidents of an already classified/evaluated failure / all incidents | Stable incident taxonomy and observation window | Deployment phase |
| C-gate wait time | authorization-issued timestamp minus request-ready timestamp | Separate waiting from execution and verification time | Broker activation |
| DORA outcomes | change lead time, deployment frequency, failed-deployment recovery time, change fail rate, deployment rework rate | Derive from linked SCM/deployment/incident events; do not assume every CI tool emits complete DORA metrics | Only after a production delivery path exists |

For the current public Skill governance repository, DORA is premature because
there is no deployment or release path. Local gate quality, Broker safety, PR
lead time, false-positive rate, and repeat failures are the relevant measures.

## Route placement

```text
R: inspect, research, diagnose, classify, generate intent/spec/plan
W: local candidate, branch, Draft PR, review comment, triage record
C: merge, tag, Release, Ruleset/Secret/Environment change, deployment, rollback
```

An automated control-band watcher stays R until it writes a shared artifact. It
may open a Draft PR only under task-scoped W policy. A rollback is a production
effect and remains C even when a pre-approved runbook exists; the runbook narrows
the operation but does not manufacture authorization.
