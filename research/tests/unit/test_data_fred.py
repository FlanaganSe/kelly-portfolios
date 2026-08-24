"""FRED registry and parser: the cash series must not be silently swappable."""

from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_edge.data import fred
from portfolio_edge.data.cache import CacheEntry, RawArtifactMissing, RawCache

TB3MS_CSV = b"""observation_date,TB3MS
1934-01-01,0.72
1934-02-01,0.62
1934-03-01,.
1934-04-01,0.25
2026-07-01,3.73
"""


def _seed(cache: RawCache, series_id: str, body: bytes) -> CacheEntry:
    return cache.store(
        fred.series_url(series_id),
        body,
        headers={"Content-Type": "application/csv"},
        retrieved_utc="2026-08-12T00:00:00Z",
    )


def test_tb3ms_dgs3mo_and_dff_are_not_interchangeable() -> None:
    assert fred.check_interchangeable("TB3MS", "DGS3MO")
    assert fred.check_interchangeable("TB3MS", "DFF")
    assert fred.check_interchangeable("DGS3MO", "DFF")


def test_the_differences_name_maturity_frequency_and_construction() -> None:
    tb_vs_dff = " ".join(fred.check_interchangeable("TB3MS", "DFF"))
    assert "maturity differs" in tb_vs_dff
    assert "frequency differs" in tb_vs_dff
    assert "construction differs" in tb_vs_dff

    # Same maturity, same nominal instrument, still not the same measurement.
    tb_vs_dgs = " ".join(fred.check_interchangeable("TB3MS", "DGS3MO"))
    assert "maturity differs" not in tb_vs_dgs
    assert "construction differs" in tb_vs_dgs
    assert "day-count basis differs" in tb_vs_dgs


@pytest.mark.parametrize(
    ("left", "right"),
    [("TB3MS", "DGS3MO"), ("TB3MS", "DFF"), ("DGS3MO", "DFF"), ("DTB3", "DGS3MO")],
)
def test_require_interchangeable_raises(left: str, right: str) -> None:
    with pytest.raises(fred.SeriesNotInterchangeableError):
        fred.require_interchangeable(left, right)


def test_a_cash_rate_must_be_specified_before_it_is_chosen() -> None:
    monthly_bill = fred.CashRateRequirement(
        maturity_months=3.0,
        frequency="monthly",
        construction="secondary_market_discount_rate",
    )
    assert fred.resolve_cash_rate(monthly_bill).series_id == "TB3MS"

    daily_curve = fred.CashRateRequirement(
        maturity_months=3.0,
        frequency="daily",
        construction="constant_maturity_yield",
    )
    assert fred.resolve_cash_rate(daily_curve).series_id == "DGS3MO"


def test_an_unsatisfiable_requirement_is_refused() -> None:
    with pytest.raises(fred.SeriesNotInterchangeableError, match="no registered"):
        fred.resolve_cash_rate(
            fred.CashRateRequirement(
                maturity_months=1.0,
                frequency="monthly",
                construction="secondary_market_discount_rate",
            )
        )


def test_unregistered_series_are_refused_rather_than_fetched() -> None:
    with pytest.raises(fred.UnknownSeriesError, match="TB3MS"):
        fred.get_series("SOFR")


def test_every_registered_series_documents_its_revision_behaviour() -> None:
    for series in fred.SERIES.values():
        assert series.definition.strip()
        assert series.release_timing.strip()
        assert series.revision_behavior.strip()


def test_parsing_requires_a_cached_raw_artifact(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = CacheEntry(
        url=fred.series_url("TB3MS"),
        sha256="0" * 64,
        size_bytes=0,
        retrieved_utc="2026-08-12T00:00:00Z",
        http_status=200,
        headers=(),
    )
    with pytest.raises(RawArtifactMissing):
        fred.parse(cache, entry, "TB3MS")


def test_percent_is_converted_to_decimal_and_recorded(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    table = fred.parse(cache, _seed(cache, "TB3MS", TB3MS_CSV), "TB3MS")

    assert table.source_units == "percent_per_year"
    assert table.units == "decimal_per_year"
    assert table.values[0][0] == pytest.approx(0.0072)


def test_the_missing_token_becomes_missing_not_zero(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    table = fred.parse(cache, _seed(cache, "TB3MS", TB3MS_CSV), "TB3MS")

    assert table.values[2][0] is None
    assert any("missing token" in w for w in table.warnings)


def test_the_rate_is_flagged_as_a_rate_not_a_return(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    table = fred.parse(cache, _seed(cache, "TB3MS", TB3MS_CSV), "TB3MS")

    assert any("not a period return" in w for w in table.warnings)


def test_a_renamed_value_column_is_warned_about(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    body = TB3MS_CSV.replace(b"observation_date,TB3MS", b"observation_date,TB3MS_PC1")
    table = fred.parse(cache, _seed(cache, "TB3MS", body), "TB3MS")

    assert any("TB3MS_PC1" in w for w in table.warnings)


def test_a_changed_column_count_is_refused(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = _seed(cache, "TB3MS", b"observation_date,TB3MS,extra\n1934-01-01,0.72,x\n")
    with pytest.raises(fred.FredParseError):
        fred.parse(cache, entry, "TB3MS")


def test_the_manifest_says_the_data_are_not_point_in_time(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = _seed(cache, "TB3MS", TB3MS_CSV)
    manifest = fred.build_manifest(entry, fred.parse(cache, entry, "TB3MS"), "TB3MS")

    assert manifest.dataset_id == "fred_tb3ms"
    assert "not point-in-time" in manifest.revision_policy.lower()
    assert "alfred" in manifest.revision_policy.lower()
    assert any("not interchangeable" in w for w in manifest.warnings)
    assert manifest.availability_policy.strip()
