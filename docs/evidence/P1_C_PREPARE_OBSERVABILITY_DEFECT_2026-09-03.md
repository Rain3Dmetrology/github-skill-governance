# P1 C Broker prepare-failure observability defect

- Observed run: `33661258459`, attempt `2`
- Target PR: `#13`
- Workflow revision: `2f85a323a590fa795f1107f4ecd0d80ca32f97d6`
- Remote outcome: prepare failed; consume skipped; pending deployments `0`

The Broker correctly rejected attempt 2 before an Environment approval or
effect. However, the workflow step used `set -e`, so the shell exited
immediately after the Broker wrote its structured failure JSON to a temporary
file. The job log exposed only exit code `1`, not the machine-readable
`run_attempt_rejected` reason.

The correction captures the prepare exit code, prints the result file to the
job log and step summary, and then returns the original exit code. Successful
preparation still parses and displays the exact approval digest. No permission,
trigger, Environment, or mutation route changes.

This document records the observed defect and proposed correction. Remote
attempt-2 evidence must be repeated after the correction reaches `main` before
the observability acceptance item is credited.
