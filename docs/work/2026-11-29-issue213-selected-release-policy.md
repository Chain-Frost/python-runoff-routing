# Issue #213 — proposed selected software release policy

This is inert preparation, not release activation. Candidate integration baseline
`4e79515d5ef91f7e5ead792f8e619dee8eb9d6c1` includes the accepted rainfall converter (#253), direct STM codec (#252),
and subsequent research additions. Source project version remains the development
bootstrap. The existing first-project workflow remains consumed/disabled.

The [publishing guide](../PUBLISHING.md#proposed-next-bounded-software-release-213)
describes the proposed calendar version selection, explicit source/run/tag binding,
existing-project Trusted Publisher and owner-reviewed deployment. The proposal uses
a separate manual filename and reuses existing release checks and artifact handling,
including isolated wheel/sdist base/extras installs and the source/wheel probe.
The draft does not create tags, modify a publisher, enable a workflow, stamp source
metadata, start upload or approve a new release. Static tests guard the inert
proposal. Actual execution and exact artifact/security review are deferred to a
separately approved activation and chosen integrated release revision.

The RORB-to-TUFLOW source, wheel and native acceptance is already recorded in #249.
The downstream adapter depends on a public released version containing that API.
