# ADR-0010: Package README governance as an offline read-first Skill

- Status: accepted for P2a
- Date: 2026-09-08

## Context

The frozen README contract was enforced only inside this repository. Reusing
it by copying prompts would drift, mix semantic judgment with deterministic
checks, and tempt cross-repository standing write authority.

## Decision

Ship one self-contained Agent Skill containing instructions, a versioned JSON
contract, standard-library validator, read-only remediation planner, and paired
drafting templates.

The script never writes the target or uses the network. Structural PASS always
leaves semantic review unattested. An editing agent may change only the two
README files when the surrounding task explicitly grants W authority. PR
creation or merge and every tag, Release, deployment, Secret, or repository
control change remain outside the Skill.

Extra repository-specific section IDs are allowed only with locale parity.
This preserves existing documentation instead of forcing every project into a
minimal template.

## Consequences

- The package works without Python dependencies or a GitHub credential.
- Deterministic gates catch drift but cannot prove comparative truth or
  translation quality.
- Templates intentionally fail until placeholders are replaced.
- Directory-layout canaries prove path portability only; live product-host
  compatibility requires separate evidence tied to product versions.
