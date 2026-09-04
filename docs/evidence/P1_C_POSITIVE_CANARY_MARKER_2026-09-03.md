# P1 C Broker positive canary marker

This file is the deliberately minimal payload for the first live Broker
acceptance pull request. Its merge is not evidence by itself; the workflow run,
Environment approval, exact request digest, merge response, commit topology,
and independent remote readback must agree before the canary is credited.

- Intended route: `merge-exact-pr`
- Intended merge method: `squash`
- Authorized base: recorded immediately before workflow dispatch
- Authorized head: this pull request's immutable head SHA
- Publication, tag, Release, Secret, Ruleset, and deployment effects: none

The closure evidence is recorded separately after the live run completes.
