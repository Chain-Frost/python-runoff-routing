"""Optional Python-only batch comparison against an owner-approved offline corpus.

Edit CORPUS_ROOT and optionally CASE_IDS. This script never launches RORB,
and it does not copy private reference data into the source repository.
"""

import json
from pathlib import Path

from runoff_routing.legacy_inputs import LegacyInputError
from runoff_routing.offline_reference import CorpusError, compare_corpus_case
from runoff_routing.reach_routing import RoutingDomainError

REPO = Path(__file__).absolute().parents[1]
CORPUS_ROOT = REPO / ".local" / "native-corpus"
CASE_IDS: tuple[str, ...] = ()


def main() -> None:
    """Print machine-readable complete-run summaries, including rejected cases."""
    catalogue = json.loads((CORPUS_ROOT / "catalogue.json").read_text(encoding="utf-8"))
    ids = CASE_IDS or tuple(
        case["case_id"] for case in catalogue["cases"] if case.get("engine", {}).get("kind") == "RORB_CMD"
    )
    results: list[dict[str, object]] = []
    for case_id in ids:
        try:
            result = compare_corpus_case(CORPUS_ROOT, case_id)
            results.append(json.loads(result.to_json()))
        except (CorpusError, LegacyInputError, RoutingDomainError, OSError, KeyError, TypeError, ValueError) as exc:
            results.append({"case_id": case_id, "status": "invalid", "reason": str(exc)})
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
