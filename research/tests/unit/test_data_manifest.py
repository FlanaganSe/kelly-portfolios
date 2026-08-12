"""The manifest schema is a contract; these tests pin it."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portfolio_edge.data.cache import CacheEntry
from portfolio_edge.data.manifest import (
    DatasetManifest,
    manifest_from_table,
    read_manifest,
)
from portfolio_edge.data.table import ParsedTable

#: Exactly the fields fixed in docs/the-plan.md, plus the four documented
#: additions. A change here is a schema change and must be deliberate.
PLAN_FIELDS = (
    "dataset_id",
    "source_url",
    "retrieved_utc",
    "sha256_raw",
    "content_type",
    "source_last_modified",
    "parser_version",
    "frequency",
    "units",
    "first_observation",
    "last_observation",
    "rows",
    "availability_policy",
    "revision_policy",
    "license_or_terms_url",
    "warnings",
)

ADDED_FIELDS = ("sha256_normalized", "source_units", "unit_transform", "source_etag")


@pytest.fixture
def entry() -> CacheEntry:
    return CacheEntry(
        url="https://example.invalid/ff5.zip",
        sha256="a" * 64,
        size_bytes=10,
        retrieved_utc="2026-08-12T00:00:00Z",
        http_status=200,
        headers=(
            ("content-type", "application/x-zip-compressed"),
            ("last-modified", "Mon, 03 Aug 2026 19:17:07 GMT"),
            ("etag", '"abc"'),
        ),
    )


@pytest.fixture
def table() -> ParsedTable:
    return ParsedTable(
        table_id="monthly",
        banner="",
        columns=("Mkt-RF", "RF"),
        periods=("1963-07", "1963-08"),
        values=((-0.0039, 0.0027), (0.0508, 0.0025)),
        frequency="monthly",
        source_units="percent",
        units="decimal",
        unit_transform="value / 100",
        warnings=("units were inferred",),
    )


def test_manifest_carries_every_field_the_plan_requires(
    entry: CacheEntry, table: ParsedTable
) -> None:
    manifest = manifest_from_table(
        dataset_id="french_us_ff5_monthly",
        entry=entry,
        table=table,
        parser_version="french/1.0.0",
        availability_policy="a",
        revision_policy="b",
        license_or_terms_url="c",
    )
    payload = manifest.to_json_dict()
    for name in (*PLAN_FIELDS, *ADDED_FIELDS):
        assert name in payload, name


def test_manifest_has_no_undocumented_fields(
    entry: CacheEntry, table: ParsedTable
) -> None:
    manifest = manifest_from_table(
        dataset_id="d",
        entry=entry,
        table=table,
        parser_version="p",
        availability_policy="a",
        revision_policy="b",
        license_or_terms_url="c",
    )
    extra = set(manifest.to_json_dict()) - set(PLAN_FIELDS) - set(ADDED_FIELDS)
    assert extra == {"schema_version"}


def test_manifest_values_come_from_the_cache_entry_and_the_table(
    entry: CacheEntry, table: ParsedTable
) -> None:
    manifest = manifest_from_table(
        dataset_id="french_us_ff5_monthly",
        entry=entry,
        table=table,
        parser_version="french/1.0.0",
        availability_policy="a",
        revision_policy="b",
        license_or_terms_url="c",
    )
    assert manifest.source_url == entry.url
    assert manifest.sha256_raw == entry.sha256
    assert manifest.content_type == "application/x-zip-compressed"
    assert manifest.source_last_modified == "Mon, 03 Aug 2026 19:17:07 GMT"
    assert manifest.source_etag == '"abc"'
    assert manifest.sha256_normalized == table.sha256_normalized()
    assert manifest.rows == 2
    assert manifest.first_observation == "1963-07"
    assert manifest.last_observation == "1963-08"
    assert manifest.units == "decimal"
    assert manifest.source_units == "percent"


def test_table_warnings_are_carried_through_and_never_dropped(
    entry: CacheEntry, table: ParsedTable
) -> None:
    manifest = manifest_from_table(
        dataset_id="d",
        entry=entry,
        table=table,
        parser_version="p",
        availability_policy="a",
        revision_policy="b",
        license_or_terms_url="c",
        extra_warnings=("and one more",),
    )
    assert manifest.warnings == ("units were inferred", "and one more")


def test_manifest_round_trips_through_disk(
    tmp_path: Path, entry: CacheEntry, table: ParsedTable
) -> None:
    manifest = manifest_from_table(
        dataset_id="french_us_ff5_monthly",
        entry=entry,
        table=table,
        parser_version="p",
        availability_policy="a",
        revision_policy="b",
        license_or_terms_url="c",
    )
    path = manifest.write(tmp_path)

    assert path.name == "french_us_ff5_monthly.json"
    assert read_manifest(path) == manifest
    assert json.loads(path.read_text(encoding="utf-8"))["rows"] == 2


def test_canonical_json_is_order_independent(
    entry: CacheEntry, table: ParsedTable
) -> None:
    manifest = manifest_from_table(
        dataset_id="d",
        entry=entry,
        table=table,
        parser_version="p",
        availability_policy="a",
        revision_policy="b",
        license_or_terms_url="c",
    )
    reloaded = DatasetManifest.from_json_dict(manifest.to_json_dict())
    assert reloaded.sha256_manifest() == manifest.sha256_manifest()


def test_normalized_hash_distinguishes_units(
    entry: CacheEntry, table: ParsedTable
) -> None:
    """Percent and decimal versions of the same numbers must not share a digest."""
    as_percent = ParsedTable(
        table_id=table.table_id,
        banner=table.banner,
        columns=table.columns,
        periods=table.periods,
        values=table.values,
        frequency=table.frequency,
        source_units="percent",
        units="percent",
        unit_transform="identity",
    )
    assert as_percent.sha256_normalized() != table.sha256_normalized()
