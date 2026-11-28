# PyRORB publication preparation

**Status: preliminary publication complete; final MVP release remains gated.** [preliminary v26.11.24.1](https://github.com/Chain-Frost/pyrorb/releases/tag/v26.11.24.1) was published from the exact #220 merge `72d0d72154da7f63e5e7c907e1efce435afcac17`. [successful upload, release and publisher-disable run](https://github.com/Chain-Frost/pyrorb/actions/runs/45392180579) passed. #215 preparation, #230 metadata separation and #233 reader transfer are merged. [Issue #213](https://github.com/Chain-Frost/pyrorb/issues/213) owns remaining release work under [#10](https://github.com/Chain-Frost/pyrorb/issues/10).

The first-project implementation of `publish.yml` was consumed and disabled.
The owner has selected a normal manual replacement at the **same filename** in #254.
Do not enable the historical workflow or reuse its vacancy trigger or old enable variable.
After the replacement is reviewed and merged, enable the updated workflow once.
The [old inert template](../packaging/pypi/publish.yml.in) is historical only.

## Agreed identity

| Surface | Value |
| --- | --- |
| Display name | PyRORB |
| GitHub repository | `Chain-Frost/pyrorb` |
| Distribution name | `pyrorb` (PyPI normalises `PyRORB` to the same name) |
| Python import namespace | `runoff_routing` |
| Existing module CLI entry points | `python -m runoff_routing.<module>` |
| Publishing workflow filename | `publish.yml` |
| Publishing environment | `pypi` |

The project name does not require an import rename or a new CLI executable. Serialized format identifiers, fixture bytes and established provenance domains remain unchanged. The [quickstart](QUICKSTART.md) documents the available module commands.

## Final MVP release gates

The development checkout retains `0.0.0.dev0`. The preliminary release used the owner-approved Australia/Perth YY.M.D.N convention; the normal workflow uses the same version allocator for a selected bounded software release. Final scientific MVP scope remains separate.

The canonical reader ownership transfer under [#231](https://github.com/Chain-Frost/pyrorb/issues/231) removes the final GitHub archive requirement; the six reader modules are part of the PyRORB distribution. The owner retains the reviewed PR-only PyRomb writer in `requirements-catg.txt`, explicitly installed outside uploaded metadata. No `ryan-rorb-readers` distribution, ryan-tools release or separate reader publisher is needed for PyRORB. PyPI rejects direct URL requirements in uploaded metadata, including extras and inactive markers.

Qualify the migrated canonical source, wheel and sdist reader APIs (including merged #203 site binding), all remaining published extras (MCP, dev and research), and the separately installed PyRomb writer. Preserve the existing numerical and source contracts. Do not execute the superseded standalone reader publisher. Ryan-tools dependency reversal [ryan-tools #340](https://github.com/Chain-Frost/ryan-tools/issues/340) is complete through [merged ryan-tools PR #344](https://github.com/Chain-Frost/ryan-tools/pull/344); [downstream main-push CI](https://github.com/Chain-Frost/ryan-tools/actions/runs/45960809675) and the normal [ryan-tools v26.11.27.1](https://github.com/Chain-Frost/ryan-tools/releases/tag/v26.11.27.1) publication passed. #231 and downstream #337 are closed. No standalone reader upload; the normal PyRORB release remains gated by exact-main quality and owner approval.

The preliminary run qualified and uploaded its exact wheel/sdist, including isolated installs and protected OIDC upload. For the final MVP, select the integrated revision and supported claims; review dependency APIs/extras, licence/provenance, contents and exact artifact metadata, clean index-backed installation, source/installed-wheel evidence and supported platform/interpreter boundaries. Ordinary PRs run Python 3.11; main runs 3.11 and 3.14 before release; 3.12/3.13 remain supported. Obtain separate owner approval for any new reviewed publishing policy and release. The [compatibility qualifications](COMPATIBILITY.md), [feature matrix](CMD_FEATURE_MATRIX.md) and [status](STATUS.md) define the bounded numerical scope.

## Normal manual release (#254)

The owner selected the simplest route: reuse the existing PyPI Trusted Publisher
(`Chain-Frost` / `pyrorb` / `publish.yml` / `pypi`) and the calendar
YY.M.D.N version allocator. No new publisher, secret, enable variable or manual version,
commit or CI-run input is needed. The existing publisher registration and protected
`pypi` environment must still be present; no new setup is expected. See
[PyPI publisher identity](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

After the reviewed replacement is merged and the current main has passed both Python
3.11 and 3.14 quality checks:

1. In GitHub Actions, enable the **updated** Publish PyRORB workflow once if it remains
   disabled from the historical release. Never enable the old implementation.
2. Run the workflow on main. It selects the current exact main commit, requires its
   successful main-push quality and allocates the next available calendar version
   using Australia/Perth and both existing tags and PyPI versions.
3. Review the build receipt and approve the existing protected pypi deployment.

The build uses existing wheel/sdist metadata and installed-package checks, including
the new rainfall export API, base and all published extras and the separately pinned
writer. Full source/installed-wheel probe records must agree. Only the checked
distribution pair reaches the protected OIDC upload job. The workflow creates a new
tag at the checked main commit before the upload; if main moves or protection,
identity or version checks fail, upload stops. A GitHub Release follows successful
PyPI upload. No automatic trigger or repeat upload on rerun. A failed upload may
leave a reserved tag; inspect both the tag and PyPI before a fresh manual dispatch.
Do not delete or reuse published version identities. The first-project variable
is not used by the replacement.

The next bounded software release includes merged #252 direct-depth STM and #253
rainfall export. Main at preparation was `8c8a36fd88ea71b29311028719dc11a63ac0e828`. Its exact future integrated
revision is selected at dispatch after successful main CI. Final scientific or full-CMD
MVP acceptance is not implied. Subsequent ryan-tools migration requires the verified
published API, not a Git URL.

## Offline readiness check

[`check_release.py`](../repo-scripts/check_release.py) reads files only. It uses `packaging` to parse requirements and versions and never contacts an index, installs a dependency, launches a native engine or uploads a file. Install release tooling in a development environment:

```sh
python -m pip install build packaging twine
```

A source-only preflight reports the current blockers. This illustrative tag is expected to fail against the unchanged bootstrap version; it is not a selected version or release instruction:

```sh
python repo-scripts/check_release.py --tag v0.1.0a1
```

After an explicitly selected version and dependency update, build into a **new, empty directory outside the repository** and inspect that exact pair. Replace `../pyrorb-release-artifacts` if it already exists; do not mix older builds with a candidate or silently clear another working directory.

```sh
python -m build --outdir ../pyrorb-release-artifacts
python -m twine check --strict ../pyrorb-release-artifacts/*
python repo-scripts/check_release.py --tag v0.1.0a1 --dist ../pyrorb-release-artifacts
```

The checker enforces:

- Normalised distribution name `pyrorb`, an explicitly non-bootstrap version, no PyPI-ineligible local version suffix, and the exact `v<version>` tag spelling.
- No direct-URL requirement in **any** source dependency group or built `Requires-Dist`, regardless of extra or environment marker.
- Exactly one wheel and one `.tar.gz` sdist with no other entries in the upload directory.
- Both artifact filenames and internal `METADATA`/`PKG-INFO` agree with the selected name/tag; built versions agree with source. The wheel's `.dist-info` directory must match the wheel filename's distribution/version identity, allowing equivalent historical name/version normalisation.
- Exactly one supported core `Metadata-Version` (currently defined through 2.6), `Name` and `Version` in each built artifact. Missing/duplicate/unsupported versions and detected malformed metadata headers are blocked; unknown future formats must be reviewed before admission.
- Static release identity/dependency fields and declared extras matching source. Parsed PEP 508 `Requires-Dist` entries in **each** artifact must also match the source dependency inventory (including optional-extra and environment markers) after name/extra normalisation; matching wheel and sdist metadata cannot mask shared dependency drift.

The source-only mode explicitly reports that artifacts were not checked. The source-to-artifact comparison is deliberately conservative about marker representation; review any backend-specific marker transformations during final package qualification rather than bypassing a mismatch. Archive metadata is inspected without extracting files. This is a bounded packaging gate: it does not check whether named dependencies exist on PyPI, qualify dependency behaviour, validate the licence, prove reproducibility, inspect every package member or replace [source/installed-wheel acceptance](REGRESSION_DATASET.md#portable-offline-vm-target-installation). `twine check --strict` adds distribution metadata and long-description validation. A later clean install must actually resolve the selected published dependencies.

## Historical one-shot automated PyPI test release (#220, completed)

The one-shot release was eligible only for the first-attempt successful main quality run of the exact #220 squash merge with its original four Python lanes, protected `pypi` environment, configured Trusted Publisher, explicit enable variable and first-project vacancy. The successful publishing run built and independently installed the wheel/sdist, created the selected tag, uploaded with OIDC, created the GitHub Release after upload and disabled the publisher. The earlier first-project activation procedure is historical; do not execute it. Subsequent main merges were permanently ineligible under that historical implementation. The replacement is manual only; no general publication-on-main policy is authorised.

The approved identity was PyRORB / Chain-Frost / pyrorb / publish.yml / pypi. The historical protected environment required the sole owner reviewer and exactly the main branch. The manual replacement reuses this identity, not the first-project trigger. The workflow source and protected deployment require review before publication. The original preparation and workflow history remain available in #215/#220 and the dated work records.

## Authoritative references

- [PyPI: using a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/) describes OIDC, environment matching and job-scoped `id-token: write`.
- [PyPI: creating a project through OIDC](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) describes pending publishers and first publication.
- [PyPA publishing action](https://github.com/pypa/gh-action-pypi-publish) documents separate build/upload jobs, Linux support and artifact publishing.
- [GitHub: `workflow_dispatch`](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch) describes manual workflow execution and default-branch availability.
- [GitHub: secure use](https://docs.github.com/en/actions/reference/security/secure-use) describes least privilege, pinned action revisions and safe handling of workflow inputs.
- [Setuptools: direct URL dependencies](https://setuptools.pypa.io/en/latest/userguide/dependency_management.html#direct-url-dependencies) explains why direct Git/archive requirements are excluded from uploaded metadata.


The environment and deployment-branch-policy REST reads require only the existing
job-scoped `actions: read` permission; no administration permission is requested.
See GitHub's [environment endpoint](https://docs.github.com/en/rest/deployments/environments#get-an-environment)
and [deployment policy endpoint](https://docs.github.com/en/rest/deployments/branch-policies#list-deployment-branch-policies).
A protected-branches-only policy is insufficient because it can include branches
other than `main`. API failures or incomplete policy inventories block release.
