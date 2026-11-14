"""Optional Python-only batch comparison against an owner-approved offline corpus.

Edit CORPUS_ROOT and optionally CASE_IDS. This script never launches RORB,
and it does not copy private reference data into the source repository.
"""

import json
from pathlib import Path
from typing import cast

from runoff_routing.legacy_inputs import LegacyInputError
from runoff_routing.offline_reference import CorpusError, compare_corpus_case
from runoff_routing.reach_routing import RoutingDomainError

REPO = Path(__file__).absolute().parents[1]
CORPUS_ROOT = REPO / ".local" / "native-corpus"
CASE_IDS: tuple[str, ...] = ()


def select_case_ids(catalogue: dict[str, object]) -> tuple[str, ...]:
    """Cover every catalogue profile by default, including GUI and failed captures.

    A compared result is not an accepted native-parity result. The comparator
    must explicitly report unsupported, invalid or incomplete profiles rather
    than silently excluding them from campaign coverage.
    """
    if catalogue.get("schema_version") != 1:
        message = "Uncharacterised offline corpus catalogue schema"
        raise ValueError(message)
    records: object = catalogue.get("cases")
    if not isinstance(records, list) or not records:
        message = "Offline corpus catalogue has no case list"
        raise ValueError(message)
    ids: list[str] = []
    for item in cast("list[object]", records):
        if not isinstance(item, dict):
            message = "Invalid offline catalogue case record"
            raise TypeError(message)
        key: object = cast("dict[str, object]", item).get("case_id")
        if not isinstance(key, str) or not key.strip():
            message = "Offline catalogue contains an invalid case_id"
            raise ValueError(message)
        ids.append(key)
    if len(ids) != len(set(ids)):
        message = "Offline catalogue contains duplicate case identifiers"
        raise ValueError(message)
    if CASE_IDS:
        missing = set(CASE_IDS).difference(ids)
        if missing:
            message = f"Requested case identifiers are absent from the corpus: {sorted(missing)}"
            raise ValueError(message)
        return CASE_IDS
    return tuple(ids)


def main() -> None:
    """Print machine-readable complete-run summaries, including rejected cases."""
    catalogue = json.loads((CORPUS_ROOT / "catalogue.json").read_text(encoding="utf-8"))
    ids = select_case_ids(catalogue)
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
