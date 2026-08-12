"""Live end-to-end checks against the primary sources.

All of these hit the network and are marked ``network``. They are not the default
test path: the offline parser tests in ``tests/unit/test_data_french.py`` run
against frozen slices of these same files and are what CI should depend on.

These tests assert *shape and provenance*, never specific numbers. Ken French
rebuilds his history from each new CRSP vintage and FRED revises in place, so a
test that pinned a value would fail for the wrong reason. What must not change is
that the file downloads, parses into separate tables, converts units explicitly,
and produces a manifest that records the vintage.

Run with::

    uv run pytest -m network
"""

from __future__ import annotations

from pathlib import Path

import pytest
import requests

from portfolio_edge.data import fred, french, prices
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.validation import validate_table

pytestmark = pytest.mark.network


@pytest.fixture(scope="module")
def cache() -> RawCache:
    """The real cache, so repeated runs do not re-download."""
    return RawCache()


@pytest.mark.parametrize("dataset_id", sorted(french.DATASETS))
def test_every_registered_french_file_downloads_and_parses(
    cache: RawCache, dataset_id: str
) -> None:
    dataset = french.get_dataset(dataset_id)
    entry, parsed, manifests = french.load(cache, dataset)

    assert entry.http_status == 200
    assert entry.size_bytes > 0
    assert entry.content_type
    assert entry.last_modified, "the Last-Modified header is the only availability bound"
    assert len(entry.sha256) == 64
    assert parsed.tables
    assert len(manifests) == len(parsed.tables)
    for manifest in manifests:
        assert manifest.sha256_raw == entry.sha256
        assert manifest.rows > 0
        assert manifest.first_observation
        assert manifest.warnings


def test_ff5_has_a_monthly_and_an_annual_table(cache: RawCache) -> None:
    dataset = french.get_dataset("french_us_ff5")
    _, parsed, _ = french.load(cache, dataset)

    assert [t.table_id for t in parsed.tables] == ["monthly", "annual"]
    monthly = parsed.table("monthly")
    assert monthly.columns == ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
    assert monthly.first_observation == "1963-07"
    assert monthly.units == "decimal"
    # Monthly equity factor returns live well inside +/-100%.
    assert all(
        v is None or abs(v) < 1.0 for row in monthly.values for v in row
    )


def test_ff5_monthly_passes_validation(cache: RawCache) -> None:
    dataset = french.get_dataset("french_us_ff5")
    _, parsed, _ = french.load(cache, dataset)
    report = validate_table(
        parsed.table("monthly"),
        dataset_id="french_us_ff5_monthly",
        expected_columns=("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"),
        expected_frequency="monthly",
    )
    assert report.ok, report.summary()


def test_momentum_starts_in_1927_and_is_a_single_column(cache: RawCache) -> None:
    dataset = french.get_dataset("french_us_momentum")
    _, parsed, _ = french.load(cache, dataset)

    monthly = parsed.table("monthly")
    assert monthly.columns == ("Mom",)
    assert monthly.first_observation == "1927-01"
    report = validate_table(
        monthly, expected_columns=("Mom",), expected_frequency="monthly"
    )
    assert report.ok, report.summary()


def test_the_emerging_file_really_does_carry_sentinels(cache: RawCache) -> None:
    """A live check that the sentinel path is exercised by real data, not only
    by the fixture."""
    dataset = french.get_dataset("french_emerging_ff5")
    _, parsed, _ = french.load(cache, dataset)

    monthly = parsed.table("monthly")
    assert any("sentinel" in w.lower() for w in monthly.warnings)
    assert any(v is None for row in monthly.values for v in row)


def test_a_cached_file_is_not_downloaded_twice(cache: RawCache) -> None:
    dataset = french.get_dataset("french_us_ff5")
    first = french.download(cache, dataset)
    second = french.download(cache, dataset)
    assert first == second


def test_fred_tb3ms_downloads_parses_and_validates(cache: RawCache) -> None:
    entry = fred.download(cache, "TB3MS")
    table = fred.parse(cache, entry, "TB3MS")
    manifest = fred.build_manifest(entry, table, "TB3MS")

    assert entry.http_status == 200
    assert "csv" in entry.content_type.lower()
    assert table.first_observation == "1934-01-01"
    assert table.units == "decimal_per_year"
    assert manifest.dataset_id == "fred_tb3ms"
    assert "not point-in-time" in manifest.revision_policy.lower()

    report = validate_table(
        table, expected_columns=("TB3MS",), expected_frequency="monthly"
    )
    assert report.ok, report.summary()


def test_the_three_cash_rates_all_download_and_stay_distinct(cache: RawCache) -> None:
    tables = {}
    for series_id in ("TB3MS", "DGS3MO", "DFF"):
        entry = fred.download(cache, series_id)
        tables[series_id] = fred.parse(cache, entry, series_id)

    assert tables["TB3MS"].frequency == "monthly"
    assert tables["DGS3MO"].frequency == "daily"
    assert tables["DFF"].frequency == "daily"
    # Same nominal maturity, materially different histories.
    assert tables["TB3MS"].rows != tables["DGS3MO"].rows
    with pytest.raises(fred.SeriesNotInterchangeableError):
        fred.require_interchangeable("TB3MS", "DGS3MO")


def test_stooq_is_recorded_as_reachable_or_not(tmp_path: Path) -> None:
    """Stooq refuses non-browser clients, and not consistently.

    Measured on 2026-08-12: ``curl`` gets HTTP 200 with a JavaScript
    proof-of-work interstitial ("This site requires JavaScript to verify your
    browser"), while ``requests`` gets HTTP 404 for the same URL. Both are
    refusals. The assertion is that the adapter either produces a series or fails
    loudly; it must never turn a challenge page into prices.
    """
    adapter = prices.StooqDailyAdapter()
    try:
        series = adapter.fetch(RawCache(tmp_path), "SPY.US")
    except requests.HTTPError:
        return
    except prices.ExploratorySourceUnavailable as exc:
        assert "HTML" in str(exc) or "no rows" in str(exc)
        return
    assert series.research_grade is False
    assert series.table.rows > 0
    with pytest.raises(prices.NonResearchGradeSeriesError):
        prices.require_research_grade(series)


def test_yahoo_either_returns_bars_or_refuses_the_client(tmp_path: Path) -> None:
    """Yahoo answered HTTP 429 to every ``requests`` call on 2026-08-12.

    curl with the same URL and headers got HTTP 200, which points at TLS or
    HTTP/2 client fingerprinting rather than anything this adapter controls. The
    offline parser test in tests/unit/test_data_prices.py runs against a real
    captured response, so the parsing path is covered either way.
    """
    adapter = prices.YahooChartAdapter(range_="1mo")
    try:
        series = adapter.fetch(RawCache(tmp_path), "VTI")
    except (requests.HTTPError, prices.ExploratorySourceUnavailable):
        return
    assert series.research_grade is False
    assert series.table.rows > 0
    with pytest.raises(prices.NonResearchGradeSeriesError):
        prices.require_research_grade(series)
