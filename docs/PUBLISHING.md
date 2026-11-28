# PyRORB publication preparation

**Status: preliminary publication complete; final MVP release remains gated.** [preliminary v26.11.24.1](https://github.com/Chain-Frost/pyrorb/releases/tag/v26.11.24.1) was published from the exact #220 merge `72d0d72154da7f63e5e7c907e1efce435afcac17`. [successful upload, release and publisher-disable run](https://github.com/Chain-Frost/pyrorb/actions/runs/45392180579) passed. #215 preparation, #230 metadata separation and #233 reader transfer are merged. [Issue #213](https://github.com/Chain-Frost/pyrorb/issues/213) owns remaining release work under [#10](https://github.com/Chain-Frost/pyrorb/issues/10).

The [workflow template](../packaging/pypi/publish.yml.in) is an inert proposal for a separate manual publisher, not an activated workflow. The one-shot workflow was consumed and its disable job succeeded. **Do not reactivate or rerun it, set its enable variable, recreate the pending publisher or use its old trigger.** Future release requires separately approved policy and exact-candidate qualification.

## Agreed identity

| Surface | Value |
| --- | --- |
| Display name | PyRORB |
| GitHub repository | `Chain-Frost/pyrorb` |
| Distribution name | `pyrorb` (PyPI normalises `PyRORB` to the same name) |
| Python import namespace | `runoff_routing` |
| Existing module CLI entry points | `python -m runoff_routing.<module>` |
| Historical one-shot workflow filename | `publish.yml` |
| Historical publishing environment | `pypi` |

The project name does not require an import rename or a new CLI executable. Serialized format identifiers, fixture bytes and established provenance domains remain unchanged. The [quickstart](QUICKSTART.md) documents the available module commands.

## Final MVP release gates

The development checkout retains `0.0.0.dev0`. The preliminary release used the owner-approved Australia/Perth YY.M.D.N convention; a later version and supported final-MVP scope require explicit selection.

The canonical reader ownership transfer under [#231](https://github.com/Chain-Frost/pyrorb/issues/231) removes the final GitHub archive requirement; the six reader modules are part of the PyRORB distribution. The owner retains the reviewed PR-only PyRomb writer in `requirements-catg.txt`, explicitly installed outside uploaded metadata. No `ryan-rorb-readers` distribution, ryan-tools release or separate reader publisher is needed for PyRORB. PyPI rejects direct URL requirements in uploaded metadata, including extras and inactive markers.

Qualify the migrated canonical source, wheel and sdist reader APIs (including merged #203 site binding), all remaining published extras (MCP, dev and research), and the separately installed PyRomb writer. Preserve the existing numerical and source contracts. Do not execute the superseded standalone reader publisher. Ryan-tools dependency reversal [ryan-tools #340](https://github.com/Chain-Frost/ryan-tools/issues/340) is complete through [merged ryan-tools PR #344](https://github.com/Chain-Frost/ryan-tools/pull/344); [downstream main-push CI](https://github.com/Chain-Frost/ryan-tools/actions/runs/45960809675) and the normal [ryan-tools v26.11.27.1](https://github.com/Chain-Frost/ryan-tools/releases/tag/v26.11.27.1) publication passed. #231 and downstream #337 are closed. No standalone reader upload or PyRORB reactivation; final PyRORB release remains separately gated.

The preliminary run qualified and uploaded its exact wheel/sdist, including isolated installs and protected OIDC upload. For the final MVP, select the integrated revision and supported claims; review dependency APIs/extras, licence/provenance, contents and exact artifact metadata, clean index-backed installation, source/installed-wheel evidence and supported platform/interpreter boundaries. Ordinary PRs run Python 3.11; main runs 3.11 and 3.14 before release; 3.12/3.13 remain supported. Obtain separate owner approval for any new reviewed publishing policy and release. The [compatibility qualifications](COMPATIBILITY.md), [feature matrix](CMD_FEATURE_MATRIX.md) and [status](STATUS.md) define the bounded numerical scope.

## Proposed next bounded software release (#213)

The merged rainfall export (#253, `440410d18502b1966804047b1be6696717a263f6`) and
direct-depth STM codec (#252) motivate a follow-up calendar release. Proposed content is
the already integrated bounded software, not a final scientific or full-CMD MVP declaration.
Candidate version: the next available YY.M.D.N on the approved Australia/Perth release day;
select the actual tag and exact main revision only after integrated quality and policy review.
At preparation, main was `4e79515d5ef91f7e5ead792f8e619dee8eb9d6c1`; the rainfall-export main run was superseded by
[the newer main quality run](https://github.com/Chain-Frost/pyrorb/actions/runs/46165157428).
Do not publish an earlier passing PR tree in place of the final selected main.

The inert template proposes a **new** `publish-selected.yml` workflow (manual dispatch
only). Do not enable, replace or rerun the consumed one-shot `publish.yml`. Activation
requires a separate reviewed PR updating the workflow allowlist and policy tests,
explicit owner approval, and a normal Trusted Publisher on the existing PyPI project:
owner `Chain-Frost`, repository `pyrorb`, workflow filename `publish-selected.yml`,
environment `pypi`. Do not create a pending publisher for the existing project.
Confirm the existing environment still requires the sole owner reviewer, disallows
admin bypass, and permits exactly the `main` branch. The old enable variable is not used.
The new `PYPI_PUBLISH_ENABLED` variable stays unset/false until an approved release.

The owner selects a new unused calendar tag at the exact reviewed current main commit
(a lightweight tag, with normal repository tag protections), and dispatches on main
with `release_tag`, `source_sha` and `quality_run_id`. The template verifies the
selected successful main-push run and both Python 3.11/3.14 lanes plus aggregate,
builds and validates the version-stamped distributions outside the checkout, installs
base and all published extras independently from wheel and sdist, installs the reviewed
writer separately, and compares complete source/installed-wheel reports. The upload
job obtains OIDC only after environment approval and rechecks main/tag, protection
rules, existing project and unused version. Only a successful upload permits a
GitHub Release. No automatic dispatch on merge, tag or successful CI. No re-run of
a partially uploaded version; inspect PyPI files and preserve receipts first. Reconfirm
action pins and review actual hosted security controls at activation. This draft has
not executed the proposed workflow or qualified final release artifacts.

After a verified index-backed release containing the exporter, the downstream
ryan-tools compatibility PR may set the minimum released PyRORB version, preserve
the script's established caller interface, and delegate parsing/interval CSV generation
to `runoff_routing.tuflow_rainfall`. No direct Git dependency or duplicated parser.
The prior native report replay and controlled HPC consumption qualify only their
documented layouts/configuration. See [rainfall export](TUFLOW_RAINFALL_EXPORT.md).

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

The one-shot release was eligible only for the first-attempt successful main quality run of the exact #220 squash merge with its original four Python lanes, protected `pypi` environment, configured Trusted Publisher, explicit enable variable and first-project vacancy. The successful publishing run built and independently installed the wheel/sdist, created the selected tag, uploaded with OIDC, created the GitHub Release after upload and disabled the publisher. The earlier first-project activation procedure is historical; do not execute it. Subsequent main merges are permanently ineligible under this workflow. No general publication-on-main policy is authorised.

The approved identity was PyRORB / Chain-Frost / pyrorb / publish.yml / pypi. The historical protected environment required the sole owner reviewer and exactly the main branch. Future publishing requires separately approved review, not reuse of the first-project trigger. The original preparation and workflow history remain available in #215/#220 and the dated work records.

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
