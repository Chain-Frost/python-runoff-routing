# S6-P3 preburst and loss preparation — work record

**Status:** draft source-only implementation; 100 km² catchment is an illustrative, explicitly fictitious geometry. **Parent:** [S6 #8](https://github.com/Chain-Frost/python-runoff-routing/issues/8); dependencies: draft PRs #38, #48, #49.

Pure separate records and functions implement exact legacy ARR Data Hub preburst depth/ratio, explicit ratio × once-ARF-adjusted rainfall, separate burst-only and complete-storm IL/CL approaches, original source/coordinate agreement, user-supplied preburst temporal sequences, and auditable mass conservation. No extra runtime packages, RORB executable calls, rainfall source download or generated goldens. Numerical outputs are experimental and have **no** hydrological acceptance status.

The supplied RORBwin 6.52 release notes establish explicit preburst controls, GSAM/Jordan defaults and preburst ratio treatment. These actual GUI defaults are **not** reproduced. A separate numerical RORBwin campaign must compare full source/effective rainfall sequences and loss/excess before discharge or stage acceptance.

Local test and replay evidence is documented on the implementation PR. Original BoM/FLTwest exports remain private; only synthetic public tests. Synthetic loss inputs 21 mm storm IL, 2 mm/h CL, and 0.054 preburst ratio for Margaret River were **invented**, not drawn from a live Data Hub response. The source-format discriminator prevents silently using legacy losses on a modern 2026v1 export.

**Next:** full regional loss/2026 source fixture, 6.52 native storm/preburst input export and comparison; avoid judging RORBwin behaviour solely by the old pre-2018 forum post.
