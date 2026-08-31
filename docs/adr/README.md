# Architecture Decision Records

| ADR | Decision | Status |
|---|---|---|
| [0001](./0001-open-source-license-and-independent-rewrite.md) | Apache-2.0 independent-rewrite boundary | Accepted |
| [0002](./0002-version-and-release-authority.md) | release-please is the only future normal-channel release authority | Accepted |
| [0003](./0003-bilingual-readme-contract.md) | Two README files with section/claim parity | Accepted |
| [0004](./0004-rwc-permission-boundaries.md) | R/W/C permissions and human C boundary | Accepted |
| [0005](./0005-active-and-delegated-authority.md) | Separate active authority, delegated authority, and connector capability | Accepted |
| [0006](./0006-normalized-permission-schema.md) | One fail-closed schema for R/W/C permissions | Accepted |
| [0007](./0007-p1-deterministic-platform-enforcement.md) | Deterministic CI, preflight, and GitHub platform controls | Accepted |
| [0008](./0008-p1-platform-enforcement-accepted.md) | P1 remote platform enforcement accepted with explicit residuals | Accepted |
| [0009](./0009-github-native-single-use-c-authorization.md) | Protected GitHub Environment plus exact-digest, single-route C authorization | Accepted architecture; activation pending |

Accepted ADRs are immutable decisions. A later change creates a new ADR that
supersedes the old one; it does not silently rewrite history.
