"""Offline parser tests against frozen slices of the real Ken French files.

Every fixture under ``tests/fixtures`` is a verbatim slice of a real download:
original CRLF line endings, original spacing, original prose header. Nothing was
retyped, so a test that passes here is a statement about the actual file format.

These are the default tests. The live download lives in
``tests/integration/test_data_french_network.py`` behind the ``network`` marker.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_edge.data import french
from portfolio_edge.data.cache import CacheEntry, RawArtifactMissing, RawCache

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _seed(cache: RawCache, fixture: str, url: str) -> CacheEntry:
    return cache.store(
        url,
        (FIXTURES / fixture).read_bytes(),
        headers={
            "Content-Type": "application/x-zip-compressed",
            "Last-Modified": "Mon, 03 Aug 2026 19:17:07 GMT",
            "ETag": '"545631ad7c23dd1:0"',
        },
        retrieved_utc="2026-08-12T00:00:00Z",
    )


@pytest.fixture
def ff5(tmp_path: Path) -> tuple[RawCache, CacheEntry, french.FrenchFile]:
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_us_ff5")
    entry = _seed(cache, "french_ff5_sample.csv", dataset.url)
    return (cache, entry, french.parse(cache, entry, dataset=dataset))


def test_parsing_requires_a_cached_raw_artifact(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = CacheEntry(
        url=french.get_dataset("french_us_ff5").url,
        sha256="0" * 64,
        size_bytes=0,
        retrieved_utc="2026-08-12T00:00:00Z",
        http_status=200,
        headers=(),
    )
    with pytest.raises(RawArtifactMissing):
        french.parse(cache, entry)


def test_both_tables_are_found_and_kept_separate(
    ff5: tuple[RawCache, CacheEntry, french.FrenchFile],
) -> None:
    _, _, parsed = ff5
    assert [t.table_id for t in parsed.tables] == ["monthly", "annual"]
    assert parsed.table("monthly").frequency == "monthly"
    assert parsed.table("annual").frequency == "annual"
    assert parsed.table("monthly").rows == 24
    assert parsed.table("annual").rows == 8


def test_table_boundaries_are_not_line_numbers(tmp_path: Path) -> None:
    """Injecting extra header prose must not move the parsed tables."""
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_us_ff5")
    raw = (FIXTURES / "french_ff5_sample.csv").read_bytes()
    padded = b"An extra line the source added this month.\r\n" * 3 + raw
    entry = cache.store(dataset.url + "#padded", padded)

    parsed = french.parse(cache, entry, dataset=dataset)
    assert [t.table_id for t in parsed.tables] == ["monthly", "annual"]
    assert parsed.table("monthly").first_observation == "1963-07"


def test_period_labels_come_from_yyyymm_keys(
    ff5: tuple[RawCache, CacheEntry, french.FrenchFile],
) -> None:
    _, _, parsed = ff5
    monthly = parsed.table("monthly")
    assert monthly.first_observation == "1963-07"
    assert monthly.last_observation == "1965-06"
    assert parsed.table("annual").first_observation == "1964"


def test_columns_are_read_from_the_header_row(
    ff5: tuple[RawCache, CacheEntry, french.FrenchFile],
) -> None:
    _, _, parsed = ff5
    assert parsed.table("monthly").columns == (
        "Mkt-RF",
        "SMB",
        "HML",
        "RMW",
        "CMA",
        "RF",
    )


def test_percent_is_converted_to_decimal_explicitly(
    ff5: tuple[RawCache, CacheEntry, french.FrenchFile],
) -> None:
    _, _, parsed = ff5
    monthly = parsed.table("monthly")
    assert monthly.source_units == "percent"
    assert monthly.units == "decimal"
    assert monthly.unit_transform == "value / 100"
    # 196307 Mkt-RF is -0.39 in the file.
    assert monthly.values[0][0] == pytest.approx(-0.0039)
    # 1964 Mkt-RF is 12.59 in the annual table.
    assert parsed.table("annual").values[0][0] == pytest.approx(0.1259)


def test_the_unit_conversion_is_always_warned_about(
    ff5: tuple[RawCache, CacheEntry, french.FrenchFile],
) -> None:
    _, _, parsed = ff5
    joined = " ".join(parsed.table("monthly").warnings)
    assert "percent" in joined.lower()
    assert "divided by 100" in joined


def test_units_are_not_assumed_without_a_declaration(tmp_path: Path) -> None:
    """Parsing without the registry leaves an unlabelled table untransformed."""
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_us_ff5")
    entry = _seed(cache, "french_ff5_sample.csv", dataset.url)

    parsed = french.parse(cache, entry)
    monthly = parsed.table("monthly")
    assert monthly.units == "unknown"
    assert monthly.unit_transform == "identity"
    assert monthly.values[0][0] == pytest.approx(-0.39)


def test_the_prose_header_is_preserved(
    ff5: tuple[RawCache, CacheEntry, french.FrenchFile],
) -> None:
    _, _, parsed = ff5
    assert "202606 CRSP database" in parsed.preamble
    assert "Annual Factors" in parsed.table("annual").banner


def test_the_copyright_footer_is_reported_not_parsed(
    ff5: tuple[RawCache, CacheEntry, french.FrenchFile],
) -> None:
    _, _, parsed = ff5
    assert any("Copyright" in w for w in parsed.warnings)
    assert all("Copyright" not in p for p in parsed.table("annual").periods)


def test_zip_and_plain_csv_give_the_same_table(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_us_ff5")
    from_zip = french.parse(
        cache, _seed(cache, "french_ff5_sample.zip", "zip://x"), dataset=dataset
    )
    from_csv = french.parse(
        cache, _seed(cache, "french_ff5_sample.csv", "csv://x"), dataset=dataset
    )

    assert from_zip.member_name == "F-F_Research_Data_5_Factors_2x3.csv"
    assert from_csv.member_name == "<uncompressed>"
    assert (
        from_zip.table("monthly").sha256_normalized()
        == from_csv.table("monthly").sha256_normalized()
    )


def test_sentinels_become_missing_not_data(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_emerging_ff5")
    entry = _seed(cache, "french_emerging_5_factors_sample.csv", dataset.url)
    parsed = french.parse(cache, entry, dataset=dataset)

    monthly = parsed.table("monthly")
    assert monthly.column("RMW") == (None,) * monthly.rows
    assert monthly.column("CMA") == (None,) * monthly.rows
    # The columns that are present are still parsed: 198907 Mkt-RF is 0.60.
    assert monthly.values[0][0] == pytest.approx(0.006)


def test_sentinel_conversion_is_counted_in_the_warnings(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_emerging_ff5")
    entry = _seed(cache, "french_emerging_5_factors_sample.csv", dataset.url)
    parsed = french.parse(cache, entry, dataset=dataset)

    sentinel_warnings = [
        w for w in parsed.table("monthly").warnings if "sentinel" in w.lower()
    ]
    assert len(sentinel_warnings) == 1
    assert "48 cells" in sentinel_warnings[0]


def test_a_two_line_annual_banner_is_handled(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_us_momentum")
    entry = _seed(cache, "french_momentum_sample.csv", dataset.url)
    parsed = french.parse(cache, entry, dataset=dataset)

    annual = parsed.table("annual")
    assert annual.banner.splitlines() == ["Annual Factors:", "January-December"]
    assert parsed.table("monthly").columns == ("Mom",)


def test_mixed_unit_tables_in_one_file_are_classified_separately(
    tmp_path: Path,
) -> None:
    """The 25-portfolio file holds returns, firm counts, market caps and ratios."""
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_us_25_portfolios_5x5")
    entry = _seed(cache, "french_25_portfolios_5x5_sample.csv", dataset.url)
    parsed = french.parse(cache, entry, dataset=dataset)

    by_id = {t.table_id: t for t in parsed.tables}
    returns = by_id["average_value_weighted_returns_monthly"]
    firms = by_id["number_of_firms_in_portfolios_monthly"]
    caps = by_id["average_market_cap_monthly"]

    assert (returns.units, returns.unit_transform) == ("decimal", "value / 100")
    assert (firms.units, firms.unit_transform) == ("count", "identity")
    # Market cap has no stated currency or scale, so it is not converted.
    assert (caps.units, caps.unit_transform) == ("unknown", "identity")
    assert any("unknown" in w for w in caps.warnings)

    ratios = [t for t in parsed.tables if t.units == "ratio"]
    assert ratios and all(t.unit_transform == "identity" for t in ratios)


def test_multiple_tables_trigger_a_file_level_warning(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    dataset = french.get_dataset("french_us_25_portfolios_5x5")
    entry = _seed(cache, "french_25_portfolios_5x5_sample.csv", dataset.url)
    parsed = french.parse(cache, entry, dataset=dataset)

    assert any("separate tables" in w for w in parsed.warnings)


def test_a_file_with_no_date_keyed_rows_is_refused(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = cache.store("x://empty", b"Copyright 2026\r\n,Mkt-RF\r\nnope,1.0\r\n")
    with pytest.raises(french.FrenchParseError):
        french.parse(cache, entry)


def test_manifests_are_built_per_table(
    ff5: tuple[RawCache, CacheEntry, french.FrenchFile],
) -> None:
    _, entry, parsed = ff5
    dataset = french.get_dataset("french_us_ff5")
    manifests = french.build_manifests(dataset, entry, parsed)

    ids = [m.dataset_id for m in manifests]
    assert ids == ["french_us_ff5_monthly", "french_us_ff5_annual"]
    monthly = manifests[0]
    assert monthly.sha256_raw == entry.sha256
    assert monthly.sha256_normalized == parsed.table("monthly").sha256_normalized()
    assert monthly.rows == 24
    assert monthly.first_observation == "1963-07"
    assert monthly.parser_version == french.PARSER_VERSION
    assert monthly.source_last_modified == "Mon, 03 Aug 2026 19:17:07 GMT"
    assert "not point-in-time" in monthly.revision_policy.lower()
    assert any("202606 CRSP" in w for w in monthly.warnings)


def test_unknown_dataset_id_lists_the_known_ones() -> None:
    with pytest.raises(KeyError, match="french_us_ff5"):
        french.get_dataset("french_us_ff6")
