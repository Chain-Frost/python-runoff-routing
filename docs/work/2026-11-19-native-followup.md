# Native CMD follow-up of existing-project differences - 19 November 2026

This bounded investigation follows the [five-set validation](2026-11-19-anonymised-site-e-validation.md) and [initial four-set receipt](2026-11-19-anonymised-site-validation.md). It tests nine selected mismatching events, one positive control and two output-binding cases. It does not reclassify all earlier differences.

## Result

Seven of the nine selected archive differences disappear when using the precision retained in the saved parameter files instead of the rounded values printed in reports. Python agrees with fresh CMD for every readable same-input comparison in this cohort, within the existing printed-precision budget. No routing implementation change or tolerance relaxation was needed.

| Cases | Finding |
| --- | --- |
| N01-N03 | Saved loss precision reproduces the archived series; rounded report losses do not. |
| N04, N06-N08 | Saved routing-coefficient precision reproduces the archived series. |
| N05 | Fresh CMD and Python agree. Fresh CMD versus archive differs at one of 201 ordinates by 0.0001 cubic metres per second; the printed peak and peak index agree. Retained as unresolved. |
| N09 | Saved coefficient reduces the difference substantially. Fresh CMD versus archive peak difference is about +0.00509%; maximum ordinate difference is 0.0012 cubic metres per second. Retained as unresolved. |
| N10 | Positive control reproduces the archived printed series. |
| N11 | Original catchment has no print command; native CMD also emits no hydrograph. Adding a separately labelled diagnostic print produces matching Python/CMD output, including a positive-flow storm. |
| N12 | Current catchment and fresh native run have two named prints; archive has one unnamed print. Python matches the two current native series. Historical physical-site binding remains unavailable. |

For N09, two additional predictions and native trials used coefficients 6.4115 and 6.4125, fixed before execution as the half-unit bounds around saved 6.412. All 201 archived samples intersect the endpoint envelope including printed intervals. This supports coefficient precision as a possible explanation, but neither identifies a historical coefficient nor establishes a strict archive-series match. No coefficient was fitted to the hydrograph.

## Identity and method

Native runtime banner: RORB CMD 6.44, updated 12 March 2019. Executable SHA-256: `10999ca29f9516c6a7abd26df37cafd433a1cd4ae70d7ac61aa7213845c5ab6f`. Python numerical source: `9c2a87bafdf53f1b1eadc08cd7a1414387551176`, Windows Python 3.14.4. Some historical reports use RORBwin 6.52; these are separate engine profiles, not authenticated same-engine reruns.

Thirty native launches completed with exit code zero, under frozen plans and a 30-launch cap. Each launch used an isolated directory, a 30-second timeout and captured inputs, output, logs and receipts. The first 24 launches pair report-rounded and saved-precision settings for 12 cases. Six further trials cover diagnostic printing, zero-length reach admission and coefficient sensitivity. Executables and manuals are not redistributed.

We start with the working assumption that the saved CATG/PAR produced the archived output. Saved numeric tuples were selected using their compatibility with printed parameter intervals, independently of fresh hydrograph agreement. This is an explicit projection of the observed saved-file layout, not a general GUI PAR importer. Intermediate edits remain possible; reproduction supports consistency rather than proving historical activity. Storm selection follows report-declared paths. Original numerical catchment records are retained; Python's previously documented diagnostic admission scaffold remains distinct from native original-CATG execution.

Native CMD tables use `Hyd001`, while the shared reader generates legend identifiers such as `Hyd0001`. The initial analysis stopped on that identifier mismatch; those negative receipts remain preserved. Authoritative `analysis-v2.jsonl` binds unique numeric printed ordinals and retains strict physical labels. It does not infer physical sites by position. CMD and archived GUI raw first clocks differ; complete ordered sample comparison retains both clocks without rewriting them or claiming raw-clock identity.

## Other confirmed gaps

CMD accepts an original project with a zero-length terminal natural reach that the Python typed input boundary rejects. A separate authored probe derived from an existing public baseline confirms the narrow behaviour: adding a zero-length terminal natural reach copies all 201 printed ordinates exactly, with positive flow, while Python admission rejects the length. This does not establish support for every zero-length reach position, storage or reach type.

The no-print result and changed print labels explain unavailable comparisons rather than numerical routing failures. The single-last-digit residual and coefficient sensitivity remain recorded without promoting either to a confirmed Python defect or an archive pass.

## Custody and limits

Private raw inputs, archived/fresh reports, frozen plans, predictions, scripts, hashes and both failed and corrected analysis receipts are retained in the authorised private investigations repository. Public records contain anonymised findings only. Existing goldens, source files and numerical tolerances were not changed. This is a targeted follow-up, not validation of all models, saved GUI parameter semantics, storage controls or rainfall reconstruction paths.

