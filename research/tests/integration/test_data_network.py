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

from portfolio_edge.data import (
    aqr,
    fred,
    french,
    goyal_welch,
    macrohistory,
    prices,
    shiller,
)
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


def test_the_aqr_workbook_downloads_parses_and_pins_its_sheet(cache: RawCache) -> None:
    """Shape and provenance only. AQR reconstructs its history on every update, so
    a test that pinned a value would fail for the wrong reason."""
    dataset = aqr.get_dataset("aqr_tsmom_factors")
    entry, parsed, manifests = aqr.load(cache, dataset)

    assert entry.http_status == 200
    assert entry.size_bytes > 0
    assert entry.last_modified, "the Last-Modified header is the only availability bound"
    assert parsed.data_sheet == dataset.data_sheet
    assert dataset.data_sheet in parsed.sheet_names
    assert parsed.table.frequency == "monthly"
    assert parsed.table.columns == dataset.expected_columns
    assert parsed.table.rows > 400

    report = validate_table(
        parsed.table,
        dataset_id="aqr_tsmom_factors_monthly",
        expected_columns=dataset.expected_columns,
        expected_frequency="monthly",
    )
    assert report.ok, report.summary()

    manifest = manifests[0]
    assert manifest.sha256_raw == entry.sha256
    assert any(w.startswith("SHEET PINNED:") for w in manifest.warnings)
    assert "not point-in-time" in manifest.revision_policy.lower()


def test_the_aqr_methodology_is_shipped_as_pictures_not_text(cache: RawCache) -> None:
    """The finding that decides how much this repository can say about the series.

    Definitions, Data Sources and Disclosures carry their content as embedded EMF
    drawings, so a cell reader sees nothing. The recovered text states the
    volatility model and the position-sizing rule and states no cost basis at all.
    """
    dataset = aqr.get_dataset("aqr_tsmom_factors")
    _, parsed, _ = aqr.load(cache, dataset)

    assert any("NOT machine-readable" in warning for warning in parsed.warnings)
    recovered = " ".join(text for _, text in parsed.narrative)
    assert recovered, "no drawing text was recovered; the workbook layout has changed"
    assert "volatility" in recovered.lower()


def test_the_commodity_series_downloads_and_is_an_excess_return_not_a_total_one(
    cache: RawCache,
) -> None:
    """The repository's only broad-commodity series, and it is excess of cash."""
    dataset = aqr.get_dataset("aqr_commodities_long_run")
    entry, parsed, manifests = aqr.load(cache, dataset)

    assert entry.http_status == 200
    assert parsed.table.frequency == "monthly"
    assert parsed.table.columns == dataset.expected_columns
    assert parsed.table.first_observation == "1877-02"
    assert parsed.table.rows > 1700

    basis = next(
        w for w in manifests[0].warnings if w.startswith("return basis claimed")
    )
    assert "NOT a total return" in basis


def test_the_credit_series_downloads_and_names_its_two_benchmarks(
    cache: RawCache,
) -> None:
    """CORP_XS and GOVT_XS are excess of *different* things. See AGENTS.md."""
    dataset = aqr.get_dataset("aqr_credit_risk_premium")
    entry, parsed, manifests = aqr.load(cache, dataset)

    assert entry.http_status == 200
    assert parsed.table.columns == ("CORP_XS", "GOVT_XS", "SP500_XS")
    assert parsed.table.first_observation == "1926-01"
    # A frozen paper vintage: it ends in 2014 and is not extended.
    assert parsed.table.last_observation == "2014-12"

    basis = next(
        w for w in manifests[0].warnings if w.startswith("return basis claimed")
    )
    assert "DURATION-MATCHED" in basis
    assert "two different benchmarks" in basis


def test_the_ice_bofa_total_return_family_is_capped_at_three_years(
    cache: RawCache,
) -> None:
    """The finding that sent this repository to Goyal-Welch for its bond leg.

    FRED serves these as real total-return index levels and, since April 2026,
    only over a trailing three-year window. If FRED ever restores the history
    this fails, which is the correct outcome: the registry entries claiming the
    cap would then be wrong and the bond leg could be reconsidered.
    """
    for series_id in ("BAMLCC0A0CMTRIV", "BAMLHYH0A0HYM2TRIV"):
        entry = fred.download(cache, series_id)
        table = fred.parse(cache, entry, series_id)

        assert entry.http_status == 200
        assert table.units == "index_level"
        assert table.frequency == "daily"
        assert table.rows < 800, (
            f"{series_id} returned {table.rows} rows; the three-year cap "
            "recorded in fred.SERIES may have been lifted"
        )
        assert table.first_observation is not None
        assert table.first_observation >= "2023-01-01"


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


def test_the_jst_macrohistory_workbook_downloads_and_pivots(cache: RawCache) -> None:
    """Shape and provenance only.

    Each JST release rebuilds and revises the full history, so pinning a value
    here would fail for the wrong reason. What must hold is that the file
    downloads, that the panel pivots to one table per variable with ISO-3
    countries as columns, and that the two countries with no returns and the
    source's own interpolation flags both survive into the warnings.
    """
    dataset = macrohistory.get_dataset("jst_macrohistory_r6")
    entry, parsed, manifests = macrohistory.load(cache, dataset)

    assert entry.http_status == 200
    assert entry.size_bytes > 0
    assert entry.last_modified, "the Last-Modified header is the only availability bound"
    assert len(parsed.countries) == 18
    assert set(macrohistory.RETURN_COUNTRIES) <= set(parsed.countries)

    equity = parsed.table("equity_total_return")
    assert equity.frequency == "annual"
    assert equity.periods[0] == "1870"
    assert equity.columns == parsed.countries
    report = validate_table(
        equity,
        dataset_id="jst_macrohistory_r6_equity_total_return_annual",
        expected_columns=parsed.countries,
        expected_frequency="annual",
    )
    assert report.ok, report.summary()

    # Canada and Ireland are in the file and carry no returns; the panel is 16.
    for iso in ("CAN", "IRL"):
        index = equity.columns.index(iso)
        assert all(row[index] is None for row in equity.values)

    flagged = {(variable, iso) for variable, iso, _ in parsed.interpolated}
    assert ("eq_tr", "PRT") in flagged
    assert ("eq_tr", "ESP") in flagged

    assert len(manifests) == len(parsed.tables)
    for manifest in manifests:
        assert manifest.sha256_raw == entry.sha256
        assert "not point-in-time" in manifest.revision_policy.lower()
        assert any("Rate of Return on Everything" in w for w in manifest.warnings)


def test_the_shiller_workbook_downloads_from_its_current_home(cache: RawCache) -> None:
    """The URL this repository had recorded returned 404; this one does not.

    The maintained copy is on shillerdata.com behind a CDN link with a ``?ver=``
    token. The assertion is that the legacy .xls reads, that October decodes as
    month ten, and that the file's own footnotes are captured rather than parsed
    as data.
    """
    dataset = shiller.get_dataset("shiller_ie_data")
    entry, parsed, manifests = shiller.load(cache, dataset)

    assert entry.http_status == 200
    assert entry.last_modified, "the Last-Modified header is the only availability bound"
    assert parsed.sheet_names == ("Disclaimer", "Data")
    table = parsed.table
    assert table.frequency == "monthly"
    assert table.periods[0] == "1871-01"
    assert "1871-10" in table.periods
    assert table.columns[0] == "P"
    assert "CAPE" in table.columns
    assert parsed.disclaimer
    report = validate_table(
        table,
        dataset_id="shiller_ie_data_monthly",
        expected_columns=table.columns,
        expected_frequency="monthly",
    )
    assert report.ok, report.summary()

    (manifest,) = manifests
    assert manifest.sha256_raw == entry.sha256
    assert "not point-in-time" in manifest.revision_policy.lower()


@pytest.mark.parametrize("dataset_id", sorted(goyal_welch.DATASETS))
def test_a_goyal_welch_workbook_downloads_and_parses(
    cache: RawCache, dataset_id: str
) -> None:
    """Also a check on the acquisition itself.

    The recorded URL for this dataset had 404'd and the dataset was written off.
    It had moved to Google Drive. This test is what would notice it moving again,
    and it asserts the weakness the move introduced: the Drive endpoint returns
    no Last-Modified, so there is no observable availability bound but the
    retrieval timestamp.
    """
    dataset = goyal_welch.get_dataset(dataset_id)
    entry, parsed, manifests = goyal_welch.load(cache, dataset)

    assert entry.http_status == 200
    assert entry.size_bytes > 0
    assert "spreadsheetml" in entry.content_type
    assert entry.last_modified is None

    assert [t.table_id for t in parsed.tables] == ["monthly", "quarterly", "annual"]
    monthly = parsed.table("monthly")
    assert monthly.periods[0] == "1871-01"
    assert monthly.rows > 1800
    assert parsed.table("annual").periods[0] == "1871"
    report = validate_table(
        monthly,
        dataset_id=f"{dataset_id}_monthly",
        expected_columns=monthly.columns,
        expected_frequency="monthly",
    )
    assert report.ok, report.summary()

    for manifest in manifests:
        assert manifest.sha256_raw == entry.sha256
        assert manifest.source_last_modified is None
        assert "not point-in-time" in manifest.revision_policy.lower()


def test_the_quarterly_sheet_really_is_quarter_end(cache: RawCache) -> None:
    """The quarterly period label is derived, so it is checked against the file.

    Labelling a quarter by its last month is only right if the quarterly row is
    the quarter-end observation. It is: the quarterly index level for 1871Q1
    equals the monthly index level for 1871-03 in the file itself.
    """
    dataset = goyal_welch.get_dataset("goyal_welch_predictors")
    _, parsed, _ = goyal_welch.load(cache, dataset)
    monthly = parsed.table("monthly")
    quarterly = parsed.table("quarterly")

    for period in ("1871-03", "1990-06", "2020-12"):
        month = monthly.values[monthly.periods.index(period)][
            monthly.columns.index("Index")
        ]
        quarter = quarterly.values[quarterly.periods.index(period)][
            quarterly.columns.index("Index")
        ]
        assert month == pytest.approx(quarter), period
