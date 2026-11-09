# First implementation handoff: S0 and S1

Work in Chain-Frost/python-runoff-routing on a new topic branch after the planning scaffold is accepted. Read AGENTS.md, the development/compatibility/regression contracts and issues #2/#3. Do not start the numerical solver, Monte Carlo, ARR generator or graphical editor in this workpack.

## Deliver

1. Inventory the actual supplied/reference binaries and sample files locally. Record SHA-256, version/banner and provenance. Do not add executables, manuals or unapproved data to Git.
2. Agree a versioned capture manifest with the friend's ensemble workflow. Import its original inputs, outputs and effective settings rather than rebuilding that workflow unnecessarily.
3. Add an explicit, local Windows CMD capture adapter with timeout, isolated outputs, complete output/log validation and immutable input hashes. GUI captures may be manually produced; retain their effective settings and version separately. Ordinary tests must not launch either binary.
4. Probe loss-model flags and the supplied example inconsistency, code-11 output, timestep labels, print identities and multi-ISA parameter indexing. Record unresolved GUI/CMD differences.
5. Implement source-aware readers for the S2 subset of .cat/.catg/.dat/.stm and CMD .par, plus retained .out results. Identify unsupported GUI .par/dialect/feature cases explicitly. Preserve exact computation order, source locations and area/gauge/ISA mappings.
6. Return typed models and deterministic inspect/validate diagnostics; no solver claims. Add synthetic grammar/error tests and approved reference fixtures. Do not silently rewrite originals or populate numerical expected outputs from the new implementation.

## Acceptance report

Record the exact commit, Python/tool versions, OS, source and installed-wheel checks, collected/skipped/native case counts, engine hashes, input/output hashes and every unresolved limitation. Run local hygiene, Ruff, strict Pyright and focused tests. Native evidence must come from Windows; Linux passes do not replace it. Keep the PR unmerged and stages open until their gates are met.

## Stop boundary

Do not implement extra features merely to make a complicated sample pass. Classify unsupported features and retain them for S3. Do not change tolerances, expected outputs, GitHub Actions settings, release configuration or repository visibility without the applicable explicit approval. End with an updated work record and one concrete next action.
