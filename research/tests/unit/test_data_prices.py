"""Price adapters are exploratory, and the guard must actually refuse."""

from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_edge.data import prices
from portfolio_edge.data.cache import CacheEntry, RawCache

STOOQ_CSV = b"""Date,Open,High,Low,Close,Volume
2024-01-02,470.0,472.5,468.1,469.3,1000000
2024-01-03,469.0,470.0,465.0,466.2,1100000
2024-01-04,466.5,468.0,464.0,465.1,900000
"""

# The bytes this endpoint actually returned on 2026-08-12, abbreviated.
STOOQ_CHALLENGE = (
    b'<!DOCTYPE html><html><head><meta charset="utf-8">'
    b'<meta name="robots" content="noindex,nofollow"></head><body><noscript>'
    b"This site requires JavaScript to verify your browser.</noscript>"
    b'<script nonce="x">(async()=>{})()</script></body></html>'
)


def _seed(cache: RawCache, body: bytes, content_type: str) -> CacheEntry:
    adapter = prices.StooqDailyAdapter()
    return cache.store(
        adapter.url_for("SPY.US"),
        body,
        headers={"Content-Type": content_type},
        retrieved_utc="2026-08-12T00:00:00Z",
    )


def test_the_adapter_satisfies_the_protocol() -> None:
    assert isinstance(prices.StooqDailyAdapter(), prices.PriceAdapter)


def test_no_adapter_in_this_repository_is_research_grade() -> None:
    assert prices.StooqDailyAdapter().research_grade is False


def test_a_confirmatory_experiment_cannot_consume_an_exploratory_series(
    tmp_path: Path,
) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.StooqDailyAdapter()
    series = adapter.parse(cache, _seed(cache, STOOQ_CSV, "text/csv"), "SPY.US")

    with pytest.raises(prices.NonResearchGradeSeriesError, match="confirmatory"):
        prices.require_research_grade(series)


def test_research_grade_series_pass_the_guard(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.StooqDailyAdapter()
    series = adapter.parse(cache, _seed(cache, STOOQ_CSV, "text/csv"), "SPY.US")
    upgraded = prices.PriceSeries(
        symbol=series.symbol,
        provider_id="hypothetical_documented_vendor",
        series_kind="fund_nav",
        table=series.table,
        adjustment="documented total-return methodology",
        currency="USD",
        entry=series.entry,
        research_grade=True,
    )
    assert prices.require_research_grade(upgraded) is upgraded


def test_exploratory_use_is_recorded_on_the_series(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.StooqDailyAdapter()
    series = adapter.parse(cache, _seed(cache, STOOQ_CSV, "text/csv"), "SPY.US")

    allowed = prices.allow_exploratory(series)
    assert allowed.research_grade is False
    assert any("exploratory" in note for note in allowed.notes)


def test_every_series_is_stamped_with_a_kind(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.StooqDailyAdapter()
    series = adapter.parse(cache, _seed(cache, STOOQ_CSV, "text/csv"), "SPY.US")

    assert series.series_kind == "exchange_close_price"
    assert series.table.columns == ("Open", "High", "Low", "Close", "Volume")
    assert series.table.periods == ("2024-01-02", "2024-01-03", "2024-01-04")


def test_the_javascript_interstitial_is_not_parsed_as_prices(tmp_path: Path) -> None:
    """Stooq answered HTTP 200 with this HTML on 2026-08-12."""
    cache = RawCache(tmp_path)
    adapter = prices.StooqDailyAdapter()
    entry = _seed(cache, STOOQ_CHALLENGE, "text/html; charset=utf-8")

    with pytest.raises(prices.ExploratorySourceUnavailable, match="HTML, not CSV"):
        adapter.parse(cache, entry, "SPY.US")


def test_the_refused_response_is_still_cached_under_its_hash(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = _seed(cache, STOOQ_CHALLENGE, "text/html; charset=utf-8")
    assert cache.read(entry) == STOOQ_CHALLENGE


def test_a_schema_change_is_warned_about(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.StooqDailyAdapter()
    body = STOOQ_CSV.replace(b"Close,Volume", b"AdjClose,Volume")
    series = adapter.parse(cache, _seed(cache, body, "text/csv"), "SPY.US")

    assert any("schema has changed" in w for w in series.table.warnings)


def test_the_manifest_records_the_exploratory_status(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.StooqDailyAdapter()
    series = adapter.parse(cache, _seed(cache, STOOQ_CSV, "text/csv"), "SPY.US")
    manifest = prices.build_manifest(series)

    assert manifest.dataset_id == "stooq_spy_us"
    assert any("research_grade=False" in w for w in manifest.warnings)
    assert any("EXPLORATORY" in w for w in manifest.warnings)
    assert "unknown" in manifest.availability_policy.lower()
    assert "unknown" in manifest.revision_policy.lower()


YAHOO_FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "yahoo_chart_vti_1mo.json"
)


def _seed_yahoo(cache: RawCache) -> CacheEntry:
    adapter = prices.YahooChartAdapter(range_="1mo")
    return cache.store(
        adapter.url_for("VTI"),
        YAHOO_FIXTURE.read_bytes(),
        headers={"Content-Type": "application/json;charset=utf-8"},
        retrieved_utc="2026-08-12T00:00:00Z",
    )


def test_the_yahoo_adapter_satisfies_the_protocol() -> None:
    assert isinstance(prices.YahooChartAdapter(), prices.PriceAdapter)


def test_yahoo_is_not_research_grade_either() -> None:
    assert prices.YahooChartAdapter().research_grade is False


def test_a_real_yahoo_response_parses_into_daily_bars(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.YahooChartAdapter(range_="1mo")
    series = adapter.parse(cache, _seed_yahoo(cache), "VTI")

    assert series.table.columns == (
        "open",
        "high",
        "low",
        "close",
        "adjclose",
        "volume",
    )
    assert series.table.frequency == "daily"
    assert series.table.rows > 10
    assert series.currency == "USD"
    first = series.table.first_observation
    assert first is not None and len(first) == 10


def test_yahoo_series_cannot_reach_a_confirmatory_experiment(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.YahooChartAdapter(range_="1mo")
    series = adapter.parse(cache, _seed_yahoo(cache), "VTI")

    with pytest.raises(prices.NonResearchGradeSeriesError):
        prices.require_research_grade(series)


def test_the_yahoo_warning_names_yfinance(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.YahooChartAdapter(range_="1mo")
    series = adapter.parse(cache, _seed_yahoo(cache), "VTI")

    assert any("yfinance" in w for w in series.table.warnings)
    assert "recomputed" in series.adjustment


def test_a_yahoo_error_payload_is_refused(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.YahooChartAdapter()
    entry = cache.store(
        adapter.url_for("NOPE"),
        b'{"chart":{"result":null,"error":{"code":"Not Found"}}}',
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(prices.ExploratorySourceUnavailable):
        adapter.parse(cache, entry, "NOPE")


def test_a_non_json_yahoo_response_is_refused(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    adapter = prices.YahooChartAdapter()
    entry = cache.store(adapter.url_for("VTI"), b"Too Many Requests")
    with pytest.raises(prices.ExploratorySourceUnavailable, match="did not return JSON"):
        adapter.parse(cache, entry, "VTI")
