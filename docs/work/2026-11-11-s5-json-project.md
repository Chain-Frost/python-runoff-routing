# S5-P0 JSON-only project boundary

- **Date:** 2026-11-11.
- **Issue:** [S5-P0 #35](https://github.com/Chain-Frost/python-runoff-routing/issues/35), child of [S5 #7](https://github.com/Chain-Frost/python-runoff-routing/issues/7).
- **Scope:** one independent, versioned JSON project manifest over immutable S1 RunModel, explicit rainfall-method metadata, hash-pinned project-relative legacy RORB file inputs and opaque hash-verified external rainfall/curve assets.
- **Source branch:** separate topic branch from live main; no changes to S1/S2/S6 authors' branches. No new dependency.
- **Owner decision:** every TOML requirement is deferred. No TOML code or acceptance tests in this workpack.
- **Validation policy:** Linux/Python 3.13 is supplementary. Windows/Python 3.14, Ruff 0.16.6, strict Pyright, public synthetic tests, build and outside-checkout wheel smoke are required; log exact-head results before promoting code quality.
- **Boundary:** projects are structurally valid only; S2 numerical parity, native execution and ARR-compliant rainfall generation remain **NOT ASSESSED**.
- **Next:** after source quality, demonstrate imported original RORB and embedded S1 JSON model identity under independent native evidence, then connect a validated S2 run/compare path as a separate PR. Keep historic and ARR 2026 rainfall profiles explicitly distinct; never silently select a policy.
- **No merges/releases/visibility changes/new hosted automation**. Issue #7 remains open after this narrow preparatory slice.
