# Issue #213 — normal manual software release policy

Owner direction: keep the release process simple. Supersedes the earlier draft
proposal for a separate workflow filename. Reuse the existing `publish.yml`,
`pypi` environment and Trusted Publisher registration, without new variables or
manual version/SHA/CI inputs. The normal publisher is manually dispatched on main
and requires the protected deployment approval. Keep the historical implementation
disabled until the reviewed replacement is merged. No publication was attempted.

Integrated preparation base: `8c8a36fd88ea71b29311028719dc11a63ac0e828`. Reuse the existing calendar allocator
for the next release (Perth release day, maximum of prior tags/PyPI versions).
The draft selects the exact dispatch commit and its successful main-push quality
run automatically, requires both selected Python lanes and the aggregate, builds
and checks wheel/sdist and separately pinned writer, verifies complete installed
regression records and publishes only the transferred checked artifacts. The tag
job creates an unused version identity before upload; GitHub Release follows
successful upload. No final scientific acceptance claim. See [Publishing](../PUBLISHING.md).

The previous draft head `df3fb3818e8221d71c07dd8d7331d086d1f01269` had zero Codex findings but failed one Ruff
formatting check. Replaced the obsolete draft-only template tests with updated
publisher guards in the existing policy test file. The current-main research
work-register entry is preserved. Historical one-shot configuration tests remain
as historical quality-policy guards; no change to normal CI lanes.

Review and CI on the revised draft remain pending; no local checkout, actionlint
or hosted publishing workflow execution has been claimed. The live environment
and current PyPI publisher must be checked before the first normal publication.
This does not require repeating already accepted native rainfall export tests.
After a verified public release, the ryan-tools consumers may migrate to the
released API under ryan-tools #346.
