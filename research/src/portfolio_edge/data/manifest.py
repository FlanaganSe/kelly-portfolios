"""Dataset manifests: the committed record of which bytes produced which table.

A manifest is small, human-readable JSON committed to ``research/data-manifests/``.
The raw bytes it describes are not committed; they live in the content-addressed
cache outside Git.

The two claims a manifest makes, kept apart on purpose
------------------------------------------------------
``sha256_raw`` and ``sha256_normalized`` are *identity* claims. They pin exactly
which file was downloaded and exactly which derived table came out of it, so a
result can be recomputed and a silent source change becomes a digest mismatch
rather than a shifted number.

They are not *availability* claims. A hash cannot show that the file represents
what was publicly available at any earlier date. Ken French rebuilds the entire
factor history from the current CRSP vintage, and FRED serves only the latest
vintage of a revised series; neither publishes an archive this code can read. So
``availability_policy`` states when a row could first have been known, and
``revision_policy`` states whether earlier rows can still change. Those two
fields, not the digests, are what a look-ahead check must consult.

The schema is the one fixed in ``docs/the-plan.md`` plus four additions, each
recording something the plan requires but the listed fields cannot hold:

``sha256_normalized``
    The plan requires hashing both the raw and the normalised representation.
``source_units`` and ``unit_transform``
    ``units`` alone cannot say both what the file contained and what the derived
    table contains, and the percent-to-decimal step must be explicit.
``source_etag``
    The plan requires recording the response headers actually returned;
    ``content_type`` and ``source_last_modified`` cover two of the three.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from portfolio_edge.data.cache import CacheEntry
from portfolio_edge.data.table import ParsedTable

__all__ = [
    "MANIFEST_SCHEMA_VERSION",
    "DatasetManifest",
    "manifest_from_table",
    "read_manifest",
]

#: Bump when a field is added, removed or given a new meaning.
MANIFEST_SCHEMA_VERSION: Final = "1"

_FIELD_ORDER: Final = (
    "schema_version",
    "dataset_id",
    "source_url",
    "retrieved_utc",
    "sha256_raw",
    "sha256_normalized",
    "content_type",
    "source_last_modified",
    "source_etag",
    "parser_version",
    "frequency",
    "units",
    "source_units",
    "unit_transform",
    "first_observation",
    "last_observation",
    "rows",
    "availability_policy",
    "revision_policy",
    "license_or_terms_url",
    "warnings",
)


@dataclass(frozen=True)
class DatasetManifest:
    """Provenance record for one derived table.

    Attributes:
        dataset_id: Stable identifier, e.g. ``french_us_ff5_monthly``.
        source_url: The URL actually requested.
        retrieved_utc: When the raw bytes were fetched, not when parsed.
        sha256_raw: Digest of the downloaded bytes, verbatim.
        sha256_normalized: Digest of the derived table's canonical form.
        content_type: The ``Content-Type`` the server returned.
        source_last_modified: The ``Last-Modified`` the server returned, if any.
            For Ken French this is the only published upper bound on when a row
            became available.
        source_etag: The ``ETag`` the server returned, if any.
        parser_version: Bumped whenever parsing behaviour changes, so a manifest
            written by an older parser is recognisable as such.
        units: Units of the derived table.
        source_units: Units in the raw file.
        unit_transform: The exact operation between the two.
        availability_policy: When an observation could first have been known.
        revision_policy: Whether past observations can still change, and whether
            historical vintages exist.
        warnings: Everything inferred, guessed, or found wrong. Never pruned.
    """

    dataset_id: str
    source_url: str
    retrieved_utc: str
    sha256_raw: str
    sha256_normalized: str
    content_type: str
    source_last_modified: str | None
    source_etag: str | None
    parser_version: str
    frequency: str
    units: str
    source_units: str
    unit_transform: str
    first_observation: str | None
    last_observation: str | None
    rows: int
    availability_policy: str
    revision_policy: str
    license_or_terms_url: str
    warnings: tuple[str, ...]
    schema_version: str = MANIFEST_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        """Return the manifest as an ordered plain dictionary."""
        payload: dict[str, object] = {}
        for name in _FIELD_ORDER:
            value = getattr(self, name)
            payload[name] = list(value) if isinstance(value, tuple) else value
        return payload

    def canonical_json(self) -> bytes:
        """Deterministic JSON bytes, for hashing a manifest into a ledger entry."""
        return json.dumps(
            self.to_json_dict(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def sha256_manifest(self) -> str:
        return hashlib.sha256(self.canonical_json()).hexdigest()

    def write(self, directory: Path, *, filename: str | None = None) -> Path:
        """Write ``<dataset_id>.json`` into ``directory`` and return the path."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (filename or f"{self.dataset_id}.json")
        path.write_text(
            json.dumps(self.to_json_dict(), indent=2) + "\n", encoding="utf-8"
        )
        return path

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, object]) -> DatasetManifest:
        def text(name: str) -> str:
            return str(payload[name])

        def optional(name: str) -> str | None:
            value = payload.get(name)
            return None if value is None else str(value)

        raw_warnings = payload.get("warnings", [])
        warnings = (
            tuple(str(item) for item in raw_warnings)
            if isinstance(raw_warnings, list)
            else ()
        )
        return cls(
            dataset_id=text("dataset_id"),
            source_url=text("source_url"),
            retrieved_utc=text("retrieved_utc"),
            sha256_raw=text("sha256_raw"),
            sha256_normalized=text("sha256_normalized"),
            content_type=text("content_type"),
            source_last_modified=optional("source_last_modified"),
            source_etag=optional("source_etag"),
            parser_version=text("parser_version"),
            frequency=text("frequency"),
            units=text("units"),
            source_units=text("source_units"),
            unit_transform=text("unit_transform"),
            first_observation=optional("first_observation"),
            last_observation=optional("last_observation"),
            rows=int(str(payload["rows"])),
            availability_policy=text("availability_policy"),
            revision_policy=text("revision_policy"),
            license_or_terms_url=text("license_or_terms_url"),
            warnings=warnings,
            schema_version=str(payload.get("schema_version", MANIFEST_SCHEMA_VERSION)),
        )


def read_manifest(path: Path) -> DatasetManifest:
    """Load a manifest written by :meth:`DatasetManifest.write`."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} does not contain a manifest object")
    return DatasetManifest.from_json_dict(payload)


def manifest_from_table(
    *,
    dataset_id: str,
    entry: CacheEntry,
    table: ParsedTable,
    parser_version: str,
    availability_policy: str,
    revision_policy: str,
    license_or_terms_url: str,
    extra_warnings: Sequence[str] = (),
) -> DatasetManifest:
    """Build a manifest from a cache entry and the table parsed out of it.

    The warnings on the table are carried through unchanged and ``extra_warnings``
    are appended; nothing is filtered. A quiet manifest means the parser found
    nothing to say, never that a warning was tidied away.
    """
    return DatasetManifest(
        dataset_id=dataset_id,
        source_url=entry.url,
        retrieved_utc=entry.retrieved_utc,
        sha256_raw=entry.sha256,
        sha256_normalized=table.sha256_normalized(),
        content_type=entry.content_type,
        source_last_modified=entry.last_modified,
        source_etag=entry.etag,
        parser_version=parser_version,
        frequency=table.frequency,
        units=table.units,
        source_units=table.source_units,
        unit_transform=table.unit_transform,
        first_observation=table.first_observation,
        last_observation=table.last_observation,
        rows=table.rows,
        availability_policy=availability_policy,
        revision_policy=revision_policy,
        license_or_terms_url=license_or_terms_url,
        warnings=(*table.warnings, *extra_warnings),
    )
