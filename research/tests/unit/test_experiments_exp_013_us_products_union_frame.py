"""Experiment 013 corrects Experiment 002's FRAME and nothing else.

Every test here exists to make one of two things impossible: a silent divergence
from Experiment 002's screen and thresholds, which would make the two audits
incomparable and so make "the frame was the problem" unfalsifiable; and a silent
re-introduction of the exclusion the experiment exists to remove.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.data.nport import FrameRow
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.experiments.exp_002_fund_exposure import (
    FACTOR_SPECIFICATIONS,
    PRIMARY_SPECIFICATION,
    FactorPanel,
    FundSeries,
    minimum_detectable_alpha,
)
from portfolio_edge.experiments.exp_002_universe import ProductFacts, UniverseError
from portfolio_edge.experiments.exp_009_exus_products import minimum_detectable_loading
from portfolio_edge.experiments.exp_013_universe import (
    CRITERION_ORDER,
    exp_002_screen_is_unmodified,
    screen_union_frame,
)
from portfolio_edge.experiments.exp_013_us_products_union_frame import (
    UsWindowPolicy,
    _exp_002_parameters,
    window_for,
)
from portfolio_edge.experiments.specification import JsonValue, Specification, load_specification

SPEC_DIR = Path(__file__).resolve().parents[2] / "experiments"


def _spec(name: str) -> Specification:
    return load_specification(SPEC_DIR / f"{name}.yaml")


def _as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def _as_sequence(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value


# --------------------------------------------------------------------------- #
# What must be identical to Experiment 002, and what is allowed to differ
# --------------------------------------------------------------------------- #


def test_the_two_screening_regexes_are_experiment_002s_byte_for_byte() -> None:
    """If these ever diverge the two audits stop being comparable silently."""
    old = _as_mapping(_as_mapping(_spec("exp_002_fund_exposure").parameters)["screening_patterns"])
    new = _as_mapping(
        _as_mapping(_spec("exp_013_us_products_union_frame").parameters)["screening_patterns"]
    )
    assert new["mandate_regex"] == old["mandate_regex"]
    assert new["exclusion_regex"] == old["exclusion_regex"]


def test_the_guard_on_experiment_002s_screen_passes_against_the_committed_file() -> None:
    exp_002_screen_is_unmodified(_exp_002_parameters())


def test_the_guard_fires_when_experiment_002s_screen_is_edited() -> None:
    parameters = dict(_exp_002_parameters())
    original = parameters["screening_patterns"]
    assert isinstance(original, Mapping)
    parameters["screening_patterns"] = {**original, "mandate_regex": r"\b(value)\b"}
    with pytest.raises(UniverseError, match="mandate pattern has changed"):
        exp_002_screen_is_unmodified(parameters)


def test_the_intended_factor_map_is_experiment_002s_key_for_key_and_sign_for_sign() -> None:
    """A fund must be graded against the same factor in both audits or the
    comparison of their verdicts means nothing."""
    old = _as_mapping(
        _as_mapping(_as_mapping(_spec("exp_002_fund_exposure").universe)["intended_factor_map"])[
            "mapping"
        ]
    )
    new = _as_mapping(
        _as_mapping(
            _as_mapping(_spec("exp_013_us_products_union_frame").universe)["intended_factor_map"]
        )["mapping"]
    )
    assert {key: dict(_as_mapping(value)) for key, value in old.items()} == {
        key: dict(_as_mapping(value)) for key, value in new.items()
    }


def test_every_falsifier_threshold_is_carried_over_unchanged() -> None:
    old = _as_mapping(_spec("exp_002_fund_exposure").parameters)
    new = _as_mapping(_spec("exp_013_us_products_union_frame").parameters)
    for key in (
        "minimum_intended_loading",
        "materiality_threshold_annual_percent",
        "minimum_net_assets_usd",
        "maximum_net_expense_ratio_percent",
        "hac_lags",
        "power_target",
        "rolling_window_months",
    ):
        assert new[key] == old[key], key
    assert new["minimum_intended_loading"] == 0.15
    assert new["materiality_threshold_annual_percent"] == 1.0
    assert new["minimum_net_assets_usd"] == 1_000_000_000
    assert new["maximum_net_expense_ratio_percent"] == 0.60
    shrinkage_old = _as_mapping(old["alpha_shrinkage"])
    shrinkage_new = _as_mapping(new["alpha_shrinkage"])
    assert shrinkage_new["sigma_true_annual_percent"] == shrinkage_old["sigma_true_annual_percent"]


def test_the_window_the_seed_and_the_inference_are_experiment_002s() -> None:
    """A common fund must be estimated on exactly the same months, or the claim
    that its numbers reproduce by construction is false."""
    old, new = _spec("exp_002_fund_exposure"), _spec("exp_013_us_products_union_frame")
    assert (new.sample_policy.start, new.sample_policy.end) == ("2020-01", "2025-12")
    assert (new.sample_policy.start, new.sample_policy.end) == (
        old.sample_policy.start,
        old.sample_policy.end,
    )
    for era in ("common_period", "first_half", "second_half", "covid_drawdown", "value_reversal"):
        old_era = next(item for item in old.sample_policy.eras if item.name == era)
        new_era = next(item for item in new.sample_policy.eras if item.name == era)
        assert (new_era.start, new_era.end) == (old_era.start, old_era.end), era
    assert new.seed == old.seed
    assert new.inference.resamples == old.inference.resamples
    assert new.inference.confidence_level == old.inference.confidence_level


def test_the_comparator_and_its_basis_are_unchanged() -> None:
    """Clause (c) is decided against this basis. Changing it would change every
    (c) verdict and make the shortfall column incomparable with Experiment 002's."""
    old = _as_mapping(_as_mapping(_spec("exp_002_fund_exposure").universe)["comparators"])
    new = _as_mapping(
        _as_mapping(_spec("exp_013_us_products_union_frame").universe)["comparators"]
    )
    assert _as_mapping(new["broad_market"])["ticker"] == _as_mapping(old["broad_market"])["ticker"]
    new_basis = list(_as_sequence(_as_mapping(new["synthetic_combination"])["basis"]))
    old_basis = list(_as_sequence(_as_mapping(old["synthetic_combination"])["basis"]))
    assert new_basis == old_basis
    assert new_basis == ["VTI", "VUG", "VTV", "VB"]


def test_exactly_two_criteria_are_declared_as_changed() -> None:
    """The claim "only the frame moved" is written down where it can be checked."""
    parameters = _as_mapping(_spec("exp_013_us_products_union_frame").parameters)
    changes = _as_mapping(parameters["screen_changes_from_exp_002"])
    changed = list(_as_sequence(changes["changed"]))
    assert [str(_as_mapping(item)["id"]) for item in changed] == ["frame", "inception_cutoff"]
    assert "CHANGED" not in str(changes["not_changed"])


def test_the_inception_cutoff_is_gone_and_the_sample_length_replaces_it() -> None:
    """Admitting post-2019 launches and then excluding them for being post-2019
    launches would be the same exclusion under another name."""
    old = _as_mapping(_spec("exp_002_fund_exposure").parameters)
    new = _as_mapping(_spec("exp_013_us_products_union_frame").parameters)
    assert old["inception_on_or_before"] == "2016-12-31"
    assert "inception_on_or_before" not in new
    assert old["minimum_monthly_observations"] == 72
    assert new["minimum_monthly_observations"] == 36
    assert "inception_cutoff" not in CRITERION_ORDER


def test_the_falsifier_keeps_all_four_clauses_and_refuses_to_punish_a_short_window() -> None:
    falsifier = _spec("exp_013_us_products_union_frame").falsifier
    for clause in ("(a)", "(b)", "(c)", "(d)"):
        assert clause in falsifier
    assert "0.15" in falsifier and "0.50" in falsifier and "1.0 percentage" in falsifier
    assert "SHORT HISTORY IS ALSO NOT A FALSIFIER" in falsifier
    assert "`unresolved`" in falsifier


# --------------------------------------------------------------------------- #
# The screen on the union frame
# --------------------------------------------------------------------------- #


def _row(series_id: str, name: str, assets: float | None) -> FrameRow:
    return FrameRow(
        accession=f"acc-{series_id}",
        series_id=series_id,
        series_name=name,
        report_date="2019-09-30",
        net_assets=assets,
        is_last_filing=False,
    )


def _facts(
    ticker: str, expense: float | None, *, mandate: str = "value", inception: str = "2015-01-01"
) -> ProductFacts:
    return ProductFacts(
        ticker=ticker,
        net_expense_ratio_percent=expense,
        gross_expense_ratio_percent=expense,
        inception_date=inception,
        index_name="an index",
        index_provider="a provider",
        stated_mandate=mandate,
        source_url="https://www.sec.gov/Archives/edgar/data/1/2/x.htm",
        date_read="2026-08-17",
    )


MANDATE = r"\b(value|growth|momentum|quality|small[- ]?cap|mid[- ]?cap|multi-?factor|factor)\b"
EXCLUSION = r"\b(bond|dividend|international|emerging)\b"
FACTOR_MAP = {"value": ("HML", 1), "small_cap": ("SMB", 1)}


def test_the_screen_records_the_first_criterion_failed_in_the_fixed_order() -> None:
    """A fund fails for one recorded reason, and the funnel adds up."""
    frame = {
        "S1": _row("S1", "Big US Value ETF", 5e9),
        "S2": _row("S2", "US Value Dividend ETF", 5e9),
        "S3": _row("S3", "Unlisted US Value Fund", 5e9),
        "S4": _row("S4", "Tiny US Value ETF", 1e8),
        "S5": _row("S5", "Pricey US Value ETF", 5e9),
        "S6": _row("S6", "US Min Vol Factor ETF", 5e9),
    }
    tickers = {sid: [(f"C{sid}", sid.replace("S", "T"))] for sid in frame}
    flags = {
        ticker: (sid != "S3", f"{ticker} security")
        for sid in frame
        for _, ticker in tickers[sid]
    }
    facts = {
        "T1": _facts("T1", 0.20),
        "T3": _facts("T3", 0.20),
        "T5": _facts("T5", 0.95),
        "T6": _facts("T6", 0.15, mandate="min_volatility"),
    }
    screened, matches = screen_union_frame(
        frame=frame,
        follow_up={},
        class_tickers=tickers,
        exchange_flags=flags,
        facts=facts,
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        minimum_net_assets=1e9,
        maximum_expense_ratio=0.60,
        intended_factor_map=FACTOR_MAP,
    )
    assert matches == len(frame)
    outcome = {fund.series_id: fund.failed_criterion for fund in screened}
    assert outcome == {
        "S1": None,
        "S2": "exclusion_regex",
        "S3": "exchange_traded",
        "S4": "minimum_net_assets",
        "S5": "maximum_expense_ratio",
        "S6": "mandate_in_map",
    }
    assert all(criterion in CRITERION_ORDER for criterion in outcome.values() if criterion)


def test_a_post_2019_launch_now_passes_where_experiment_002_could_not_see_it() -> None:
    """AVUV listed 2019-09 and DFSV in 2022. This is the whole experiment."""
    follow_up = {"S1": _row("S1", "Avantis U.S. Small Cap Value ETF", 18e9)}
    screened, matches = screen_union_frame(
        frame={},
        follow_up=follow_up,
        class_tickers={"S1": [("C1", "AVUV")]},
        exchange_flags={"AVUV": (True, "AVUV")},
        facts={"AVUV": _facts("AVUV", 0.25, inception="2019-09-24")},
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        minimum_net_assets=1e9,
        maximum_expense_ratio=0.60,
        intended_factor_map=FACTOR_MAP,
    )
    assert matches == 1
    assert screened[0].passed
    assert screened[0].in_exp_002_frame is False


def test_the_asset_floor_uses_the_largest_of_the_two_censuses() -> None:
    """A fund that launched small and grew is most of the population being added."""
    frame = {"S1": _row("S1", "Avantis U.S. Large Cap Value ETF", 1e7)}
    follow_up = {"S1": _row("S1", "Avantis U.S. Large Cap Value ETF", 8e9)}
    screened, _ = screen_union_frame(
        frame=frame,
        follow_up=follow_up,
        class_tickers={"S1": [("C1", "AVLV")]},
        exchange_flags={"AVLV": (True, "AVLV")},
        facts={"AVLV": _facts("AVLV", 0.15)},
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        minimum_net_assets=1e9,
        maximum_expense_ratio=0.60,
        intended_factor_map=FACTOR_MAP,
    )
    assert screened[0].passed
    assert screened[0].net_assets_max == pytest.approx(8e9)
    assert screened[0].in_exp_002_frame is True


def test_a_fund_that_died_inside_the_window_is_still_screened() -> None:
    """The union must not quietly become a survivorship screen: a series present
    in 2019Q4 and absent in 2025Q4 is retained, which is the property Experiment
    002's start-of-window frame was protecting."""
    frame = {"S1": _row("S1", "Dead US Value ETF", 3e9)}
    screened, _ = screen_union_frame(
        frame=frame,
        follow_up={},
        class_tickers={"S1": [("C1", "DEAD")]},
        exchange_flags={"DEAD": (True, "DEAD")},
        facts={"DEAD": _facts("DEAD", 0.20)},
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        minimum_net_assets=1e9,
        maximum_expense_ratio=0.60,
        intended_factor_map=FACTOR_MAP,
    )
    assert screened[0].passed
    assert screened[0].in_follow_up_census is False


def test_a_missing_fee_fails_the_screen_visibly_rather_than_silently() -> None:
    """A gathering gap must look like a gathering gap. Experiment 002 had to
    correct exactly this once, before any return was read."""
    frame = {"S1": _row("S1", "Unresearched US Value ETF", 3e9)}
    screened, _ = screen_union_frame(
        frame=frame,
        follow_up={},
        class_tickers={"S1": [("C1", "UNK")]},
        exchange_flags={"UNK": (True, "UNK")},
        facts={},
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        minimum_net_assets=1e9,
        maximum_expense_ratio=0.60,
        intended_factor_map=FACTOR_MAP,
    )
    assert screened[0].failed_criterion == "maximum_expense_ratio"
    assert "no net expense ratio was verified" in screened[0].failure_detail


# --------------------------------------------------------------------------- #
# The window a young fund is estimated on
# --------------------------------------------------------------------------- #


def _panel(periods: tuple[str, ...]) -> FactorPanel:
    size = len(periods)
    return FactorPanel(
        periods=periods,
        factors={
            name: np.zeros(size) for name in ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD")
        },
        risk_free=np.zeros(size),
        provenance={},
    )


def _table() -> ParsedTable:
    return ParsedTable(
        table_id="t",
        banner="test",
        columns=("total_return",),
        periods=(),
        values=(),
        frequency="monthly",
        source_units="decimal",
        units="decimal",
        unit_transform="identity",
        warnings=(),
    )


def _series(periods: tuple[str, ...]) -> FundSeries:
    return FundSeries(
        ticker="X",
        series_id="S000000001",
        class_id="C000000001",
        periods=periods,
        returns=np.zeros(len(periods)),
        missing_months=(),
        filing_count=12,
        amendment_count=0,
        filings_held_out=0,
        warnings=(),
        table=_table(),
        first_filing_sha256="0" * 64,
    )


ALL_MONTHS = tuple(
    f"{year}-{month:02d}" for year in (2020, 2021, 2022) for month in range(1, 13)
)
POLICY = UsWindowPolicy(start="2020-01", end="2022-12")


def test_a_fund_that_covers_the_window_start_keeps_every_month() -> None:
    """This is what makes an incumbent's numbers reproduce Experiment 002's: the
    launch rules must not touch a fund whose history reaches the window start."""
    window = window_for(
        _series(ALL_MONTHS), _panel(ALL_MONTHS), policy=POLICY, inception="2004-01-26"
    )
    assert window.first == "2020-01"
    assert window.months == len(ALL_MONTHS)


def test_the_first_filed_month_of_a_late_starter_is_dropped_without_any_external_fact() -> None:
    """A fund that listed inside the window files a part-month return for its
    launch month. Regressed on a whole month of factors its beta is attenuated."""
    late = tuple(period for period in ALL_MONTHS if period >= "2021-09")
    window = window_for(_series(late), _panel(ALL_MONTHS), policy=POLICY, inception=None)
    assert window.first == "2021-10"
    assert window.months == len(late) - 1


def test_the_later_of_the_two_launch_cuts_wins() -> None:
    """A conversion date can be later than the first filed month, and is: the ETF
    class of a converted fund can carry a return for a month before it existed."""
    late = tuple(period for period in ALL_MONTHS if period >= "2021-05")
    without = window_for(_series(late), _panel(ALL_MONTHS), policy=POLICY, inception=None)
    with_date = window_for(
        _series(late), _panel(ALL_MONTHS), policy=POLICY, inception="2021-06-14"
    )
    assert without.first == "2021-06"
    assert with_date.first == "2021-07"
    assert with_date.months < without.months


def test_a_fund_that_listed_on_the_first_keeps_its_launch_month_when_the_date_is_known() -> None:
    late = tuple(period for period in ALL_MONTHS if period >= "2021-09")
    window = window_for(
        _series(late), _panel(ALL_MONTHS), policy=POLICY, inception="2021-09-01"
    )
    # The stub rule still removes 2021-09 because the filed history starts late
    # and no external fact is needed to see that; the inception date only ever
    # moves the floor LATER. One observation is the price of that conservatism.
    assert window.first == "2021-10"


def test_the_window_never_reaches_before_the_frozen_start_or_past_the_frozen_end() -> None:
    wide = ("2019-01", "2019-02", *ALL_MONTHS, "2023-01")
    window = window_for(
        _series(wide), _panel(("2019-01", "2019-02", *ALL_MONTHS, "2023-01")),
        policy=POLICY,
        inception=None,
    )
    assert window.first == "2020-01"
    assert window.last == "2022-12"


# --------------------------------------------------------------------------- #
# The statistics are Experiment 002's, reused rather than rewritten
# --------------------------------------------------------------------------- #


def test_the_minimum_detectable_loading_is_the_same_algebra_as_the_alpha_one() -> None:
    assert minimum_detectable_loading(0.05) == pytest.approx(minimum_detectable_alpha(0.05))
    # (z_{0.975} + z_{0.80}) * SE = 2.80159 * 0.05.
    assert minimum_detectable_loading(0.05) == pytest.approx(0.1400793, abs=1e-6)


def test_the_primary_specification_is_the_six_factor_one() -> None:
    assert PRIMARY_SPECIFICATION == "FF5+UMD"
    assert FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION] == (
        "Mkt-RF",
        "SMB",
        "HML",
        "RMW",
        "CMA",
        "UMD",
    )
