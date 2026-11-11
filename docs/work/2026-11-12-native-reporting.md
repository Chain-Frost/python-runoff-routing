# Native and physical volume statistics

| Field | Value |
| --- | --- |
| Status | Draft pure helper; native numerical acceptance open |
| Updated | 2026-11-12 |
| Owner | Unassigned |
| Delivery branch | feat/native-reporting-conventions |
| Tracking | [S2 issue #4](https://github.com/Chain-Frost/python-runoff-routing/issues/4) |

The proposed native_reporting.py helper uses printed discharge and time tokens, and a version-qualified profile label. It returns the inclusive-sample-sum candidate, physical-horizon trapezoidal integral, endpoint difference and printing-precision bounds. It does not infer historical physical correctness or use private data.

Linux/Python 3.13.5: 12 focused synthetic pytest cases passed; Python compilation passed. The 21-sample 2 m3/s at h=0.5 h example yields 75,600 versus 72,000 m3.

NOT RUN: Windows/Python 3.14, Ruff 0.16.6, strict Pyright, full repo suite, wheel/out-of-tree import, private native corpus and RORB. No concurrent S1/S2 integration branch modified.

Next: validate exact head on Windows/Python 3.14 and hand independent statistics to the integration author. Keep S2 numerical parity and nonlinear stopping behavior open.
