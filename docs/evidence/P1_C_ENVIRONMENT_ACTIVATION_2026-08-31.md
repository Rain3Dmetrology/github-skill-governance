# P1 C Environment activation evidence

- Evidence date: 2026-08-31
- Repository: `Rain3Dmetrology/github-skill-governance`
- Repository ID: `1350230486`
- Environment: `c-authorization`
- Environment ID: `20905500070`
- Activation state: complete; canonical Broker workflow remains absent

## Authorization and mutation

The maintainer requested that the Environment configuration be completed and
reported that GitHub's enabled wait-timer control requires at least one minute.
The applied REST mutation was limited to:

- wait timer: 1 minute;
- prevent self-review: false;
- one required reviewer: `Rain3Dmetrology`, user ID `79391663`;
- deployment branch policy: protected branches only, no custom policies;
- no Environment Secret or Variable creation.

The earlier zero-minute desired value was not applied. It is corrected to the
effective one-minute rule in the tracked contract, validator, Broker readback,
and tests.

## API readback

The post-write readback returned:

- Environment ID `20905500070` and exact name `c-authorization`;
- exactly one `required_reviewers` rule with the expected user and
  `prevent_self_review=false`;
- exactly one `wait_timer` rule with `wait_timer=1`;
- one protected-branch policy with `protected_branches=true` and
  `custom_branch_policies=false`;
- Environment Secret count 0;
- Environment Variable count 0.

## UI assertion and reviewer restoration

The maintainer deselected **Allow administrators to bypass configured
protection rules** and saved the protection rules in the GitHub UI. That save
also removed the required-reviewer rule. API readback proved both changes. The
exact reviewer was restored with the same authorized REST configuration; a
second readback proved `can_admins_bypass=false` remained effective and the
required reviewer was again present.

## Branch-scope remediation

The GitHub UI reports that no classic branch protection rule exists and that
all branches are therefore allowed under `protected_branches=true`. The
repository's Ruleset protection does not satisfy this Environment option. The
maintainer then authorized completion with Playwright or another appropriate
tool. The supported REST API was used because an isolated Playwright session
could not inherit the authenticated Chrome session.

Final readback proves:

- `protected_branches=false` and `custom_branch_policies=true`;
- exactly one deployment branch policy exists;
- policy ID `58680218`, name `main`, type `branch`;
- the required reviewer, one-minute timer, and
  `can_admins_bypass=false` remained effective.

The Environment activation has no remaining blocker. The Broker remains
dormant because its canonical workflow is intentionally absent until PR-B1.

No Broker workflow, tag, Release, Secret, or legacy release-Skill permission was
created by this activation step.
