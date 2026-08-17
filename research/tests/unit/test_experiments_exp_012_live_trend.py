"""Offline tests for Experiment 012: the census screen, the index, and the comparison.

Nothing here touches the network. The N-PORT frame rows and the fund return histories
are constructed in this file, and every expected value is written out as a closed form
rather than read back from the module under test.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.data.nport import FrameRow
from portfolio_edge.experiments.exp_012_live_trend import (
    FundReturns,
    LiveTrendError,
    ScreenedSeries,
    build_live_index,
    build_panel,
    default_specification_path,
    load_census,
    screen_census,
    vendor_comparison,
    write_census,
)
from portfolio_edge.experiments.specification import (
    EvidenceClass,
    JsonValue,
    RunKind,
    load_specification,
)

MANDATE = (
    r"\b(managed\s+futures|trend|cta|systematic\s+macro|time[-\s]series\s+momentum"
    r"|mlm\s+index)\b"
)
EXCLUSION = r"\b(equit\w*|credit|bond\w*|allocation)\b"


def as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def as_sequence(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value


def row(series_id: str, name: str, assets: float | None = 1.0e8) -> FrameRow:
    return FrameRow(
        accession=f"acc-{series_id}",
        series_id=series_id,
        series_name=name,
        report_date="2019-09-30",
        net_assets=assets,
        is_last_filing=False,
    )


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


def test_the_screen_matches_the_mandate_and_ignores_everything_else() -> None:
    frame = {
        "S1": row("S1", "Acme Managed Futures Strategy Fund"),
        "S2": row("S2", "Acme Total Bond Market Index Fund"),
    }
    screened = screen_census(
        frame=frame,
        follow_up={},
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        not_a_futures_programme={},
    )
    assert [item.series_id for item in screened] == ["S1"]
    assert screened[0].admitted


def test_a_series_the_exclusion_pattern_catches_is_kept_with_its_reason() -> None:
    """A rejection that is not written down cannot supply a denominator."""
    frame = {"S1": row("S1", "Acme Equity Trend Fund")}
    screened = screen_census(
        frame=frame,
        follow_up={},
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        not_a_futures_programme={},
    )
    assert len(screened) == 1
    assert not screened[0].admitted
    assert screened[0].rejected_by == "exclusion_pattern"
    assert "exclusion pattern" in screened[0].reason


def test_a_named_non_futures_programme_is_rejected_with_the_written_reason() -> None:
    frame = {"S1": row("S1", "Fidelity Trend Fund")}
    screened = screen_census(
        frame=frame,
        follow_up={},
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        not_a_futures_programme={"S1": "a 1958 US large-cap growth fund"},
    )
    assert screened[0].rejected_by == "not_a_futures_programme"
    assert screened[0].reason == "a 1958 US large-cap growth fund"


def test_the_frame_is_a_union_and_the_later_name_wins() -> None:
    """A fund renamed between censuses is screened under the name it files today."""
    screened = screen_census(
        frame={
            "S1": row("S1", "Old Managed Futures Fund", 1.0e8),
            "S2": row("S2", "Dead CTA Fund"),
        },
        follow_up={"S1": row("S1", "New Managed Futures Fund", 5.0e8)},
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        not_a_futures_programme={},
    )
    by_id = {item.series_id: item for item in screened}
    assert set(by_id) == {"S1", "S2"}
    assert by_id["S1"].series_name == "New Managed Futures Fund"
    assert by_id["S1"].net_assets_maximum == pytest.approx(5.0e8)
    # The fund present only in the first census is retained: dropping it would be
    # exactly the survivorship screen this design exists to avoid.
    assert by_id["S2"].in_frame_quarter and not by_id["S2"].in_follow_up_quarter


def test_a_committed_census_round_trips(tmp_path: Path) -> None:
    payload: dict[str, JsonValue] = {
        "schema_version": "1",
        "series": [
            ScreenedSeries(
                series_id="S1",
                series_name="Acme Managed Futures Fund",
                admitted=True,
                rejected_by="",
                reason="",
                in_frame_quarter=True,
                in_follow_up_quarter=False,
                net_assets_frame=1.0e8,
                net_assets_follow_up=None,
                net_assets_maximum=1.0e8,
            ).to_json()
        ],
    }
    location = tmp_path / "census.json"
    write_census(payload, location)
    assert json.loads(location.read_text(encoding="utf-8"))["schema_version"] == "1"
    restored = load_census(location)
    assert restored[0].series_id == "S1"
    assert restored[0].admitted
    assert restored[0].net_assets_follow_up is None


def test_a_missing_census_names_the_command_that_builds_it(tmp_path: Path) -> None:
    with pytest.raises(LiveTrendError, match="--build-census"):
        load_census(tmp_path / "absent.json")


# --------------------------------------------------------------------------- #
# The index
# --------------------------------------------------------------------------- #


def fund(series_id: str, returns: Mapping[str, float]) -> FundReturns:
    return FundReturns(
        series_id=series_id,
        series_name=f"fund {series_id}",
        class_ids=("C1",),
        returns=dict(returns),
        filing_count=1,
        amendment_count=0,
        is_final_filing_seen=False,
        class_dispersion=0.0,
        warnings=(),
    )


def test_the_index_is_the_mean_of_the_funds_that_filed_that_month() -> None:
    funds = [
        fund("S1", {"2020-01": 0.02, "2020-02": 0.04}),
        fund("S2", {"2020-01": 0.00, "2020-02": 0.00}),
    ]
    index = build_live_index(funds, start="2020-01", end="2020-02", minimum_funds=2)
    assert index.periods == ("2020-01", "2020-02")
    assert index.total_return == pytest.approx([0.01, 0.02])
    assert index.fund_count == (2, 2)


def test_a_fund_that_dies_contributes_until_it_dies_and_no_further() -> None:
    """The property a CTA peer-group index does not have, asserted rather than claimed."""
    funds = [
        fund("alive", {"2020-01": 0.10, "2020-02": 0.10, "2020-03": 0.10}),
        fund("dead", {"2020-01": -0.10, "2020-02": -0.10}),
    ]
    index = build_live_index(funds, start="2020-01", end="2020-03", minimum_funds=1)
    assert index.fund_count == (2, 2, 1)
    assert index.total_return == pytest.approx([0.0, 0.0, 0.10])


def test_thin_months_are_truncated_from_the_ends_rather_than_filtered_out() -> None:
    funds = [
        fund("early", {"2020-01": 0.01, "2020-02": 0.01, "2020-03": 0.01}),
        fund("late", {"2020-02": 0.03, "2020-03": 0.03, "2020-04": 0.03}),
    ]
    index = build_live_index(funds, start="2020-01", end="2020-04", minimum_funds=2)
    assert index.periods == ("2020-02", "2020-03")


def test_a_hole_in_the_middle_is_refused_rather_than_spliced() -> None:
    """Splicing would join two different fund populations into one series."""
    funds = [
        fund("a", {"2020-01": 0.01, "2020-03": 0.01}),
        fund("b", {"2020-01": 0.01, "2020-03": 0.01}),
    ]
    with pytest.raises(LiveTrendError, match="splice"):
        build_live_index(funds, start="2020-01", end="2020-03", minimum_funds=2)


def test_an_empty_window_is_refused() -> None:
    with pytest.raises(LiveTrendError, match="cannot be formed"):
        build_live_index(
            [fund("a", {"2020-01": 0.01})], start="2020-01", end="2020-01", minimum_funds=5
        )


# --------------------------------------------------------------------------- #
# The panel
# --------------------------------------------------------------------------- #


def test_the_panel_subtracts_cash_from_the_fund_total_return_exactly_once() -> None:
    """The funds hold their margin in bills; leaving the yield in would double-count it."""
    index = build_live_index(
        [fund("a", {"2020-01": 0.02, "2020-02": 0.03})],
        start="2020-01",
        end="2020-02",
        minimum_funds=1,
    )
    panel = build_panel(
        index,
        market={"2020-01": 0.01, "2020-02": -0.01},
        cash={"2020-01": 0.001, "2020-02": 0.002},
    )
    assert panel.sleeves == ("equity", "trend")
    assert panel.column("equity") == pytest.approx([0.01, -0.01])
    assert panel.column("trend") == pytest.approx([0.019, 0.028])
    assert panel.cash == pytest.approx([0.001, 0.002])


def test_a_panel_with_no_shared_month_is_refused() -> None:
    index = build_live_index(
        [fund("a", {"2020-01": 0.02})], start="2020-01", end="2020-01", minimum_funds=1
    )
    with pytest.raises(LiveTrendError, match="share no month"):
        build_panel(index, market={"1999-01": 0.0}, cash={"1999-01": 0.0})


# --------------------------------------------------------------------------- #
# The decisive comparison
# --------------------------------------------------------------------------- #


def test_a_vendor_series_that_is_the_live_one_plus_a_constant_shows_that_constant() -> None:
    """The construction the alpha is meant to detect, built exactly."""
    rng = np.random.default_rng(11)
    live = rng.normal(0.004, 0.03, size=120)
    shift = 0.005
    result = vendor_comparison(live, live + shift)
    assert result.alpha == pytest.approx(shift * 12.0)
    assert result.beta == pytest.approx(1.0)
    assert result.mean_difference == pytest.approx(shift * 12.0)
    # At beta exactly one the volatility-matched difference is the raw difference.
    assert result.volatility_matched_difference == pytest.approx(shift * 12.0)
    assert result.correlation == pytest.approx(1.0)


def test_a_vendor_series_that_is_the_live_one_scaled_shows_beta_and_no_alpha() -> None:
    """A pure exposure difference must not read as an overstatement."""
    rng = np.random.default_rng(12)
    live = rng.normal(0.004, 0.03, size=120)
    result = vendor_comparison(live, 1.5 * live)
    assert result.beta == pytest.approx(1.5)
    assert result.alpha == pytest.approx(0.0, abs=1e-12)
    # The raw difference is NOT zero -- it is half the live mean -- which is exactly
    # why the volatility-matched figure is reported beside it.
    assert result.volatility_matched_difference == pytest.approx(0.0, abs=1e-12)
    assert result.mean_difference == pytest.approx(0.5 * float(np.mean(live)) * 12.0)


def test_the_comparison_refuses_two_series_of_different_lengths() -> None:
    with pytest.raises(LiveTrendError, match="months"):
        vendor_comparison(np.zeros(10), np.zeros(11))


def test_the_reported_moments_are_the_plain_annualised_ones() -> None:
    live = np.array([0.01, -0.01] * 30, dtype=np.float64)
    result = vendor_comparison(live, live)
    assert result.live_moments["arithmetic_excess_return"] == pytest.approx(0.0, abs=1e-15)
    # An alternating +/-1% series has sample sd = sqrt(60 * 0.0004 / 118) per the
    # two-value identity, annualised by sqrt(12).
    expected = math.sqrt(30 * (0.02) ** 2 / (2 * 59)) * math.sqrt(12.0)
    assert result.live_moments["volatility"] == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# The frozen specification
# --------------------------------------------------------------------------- #


def test_the_specification_is_exploratory_and_says_why() -> None:
    spec = load_specification(default_specification_path())
    assert spec.run_kind is RunKind.EXPLORATORY
    assert spec.evidence_class is EvidenceClass.FUND_IMPLEMENTATION_AUDIT
    assert spec.consumes_final_holdout is False


def test_the_trend_leg_carries_a_zero_fee_because_item_b5_already_deducted_one() -> None:
    """If this ever becomes non-zero the fee is charged twice and nothing says so."""
    spec = load_specification(default_specification_path())
    fees = as_mapping(as_mapping(spec.cost_model)["sleeve_fee_annual_percent"])
    assert fees["trend"] == 0.0
    assert "twice" in str(as_mapping(spec.cost_model)["sleeve_fee_basis"])


def test_the_specification_states_both_survivorship_holes() -> None:
    spec = load_specification(default_specification_path())
    survivorship = as_mapping(as_mapping(spec.parameters)["survivorship"])
    assert "NEITHER" in str(survivorship["hole_two"])
    assert "flatter" in str(survivorship["direction"])


def test_the_weights_are_experiment_011s_so_the_two_read_line_for_line() -> None:
    spec = load_specification(default_specification_path())
    portfolios = {
        str(as_mapping(item)["name"]): [
            float(str(value)) for value in as_sequence(as_mapping(item)["weights"])
        ]
        for item in as_sequence(as_mapping(spec.parameters)["portfolios"])
    }
    assert portfolios["equity_plus_trend_50"] == [1.0, 0.50]
    assert portfolios["equity_levered_150"] == [1.50, 0.0]
    assert portfolios["equity_only"] == [1.0, 0.0]


def test_the_screen_patterns_are_experiment_008s_verbatim() -> None:
    """Rewriting them here after seeing what they caught would launder the provenance."""
    from portfolio_edge.experiments.exp_008_universe import universe_path

    spec = load_specification(default_specification_path())
    screen = as_mapping(as_mapping(spec.parameters)["screen"])
    committed = json.loads(universe_path().read_text(encoding="utf-8"))["inputs"]
    assert screen["mandate_pattern"] == committed["mandate_pattern"]
    assert screen["exclusion_pattern"] == committed["exclusion_pattern"]
