"""Optional Python-only S2 comparison against a neighbouring private corpus.

Edit CORPUS_ROOT and CASE_IDS before running; no native programs are invoked.
"""

import json
from pathlib import Path

from runoff_routing.offline_reference import compare_corpus_case

REPO = Path(__file__).absolute().parents[1]
CORPUS_ROOT = REPO.parent / "runoff-routing-investigations" / "tests" / "fixtures" / "rorb" / "native-corpus"
CASE_IDS: tuple[str, ...] = ("review-design-baseline", "review-ensemble-tp9", "zero-loss-ensemble-tp9-f1")


def main() -> None:
    """Run retained data comparisons; preserve the complete ordinate evidence."""
    reports = [compare_corpus_case(CORPUS_ROOT, case_id) for case_id in CASE_IDS]
    summaries = [json.loads(report.to_json()) for report in reports]
    print(json.dumps(summaries, indent=2, sort_keys=True))
    # No corpus or output is copied into the public source repository.


if __name__ == "__main__":
    main()
