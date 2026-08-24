"""Experiment 009: the arithmetic and the screen rules that decide the ex-US audit.

Three of these tests exist because getting them wrong would quietly invalidate
the comparison with Experiment 002 rather than break anything:

* a rename is not a death, and differencing name-qualified identifier sets says
  it is;
* an SEC fund series survives a mutual-fund-to-ETF conversion, so a window that
  is not cut at inception audits a product nobody could have bought;
* a fund with a hole in its filed history is two time series, and a HAC standard
  error computed across the hole assumes a lag structure that does not exist.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.data.nport import FrameRow
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.experiments.exp_002_fund_exposure import (
    FactorPanel,
    FundSeries,
    minimum_detectable_alpha,
)
from portfolio_edge.experiments.exp_002_universe import ProductFacts, UniverseError
from portfolio_edge.experiments.exp_009_exus_products import (
    PANEL_DATASETS,
    contiguous_window,
    minimum_detectable_loading,
    screening_patterns_from_specification,
    shelf_depth,
)
from portfolio_edge.experiments.exp_009_universe import (
    CRITERION_ORDER,
    EXP_002_EXCLUSION_REGEX,
    EXP_002_MANDATE_REGEX,
    GRADED_REGIONS,
    ExtraFacts,
    ScreenedExUsFund,
    ScreeningPatterns,
    attrition,
    derive_mandate,
    derive_region,
    exp_002_screen_is_unmodified,
    screen_union_frame,
    us_overlap,
)
from portfolio_edge.experiments.specification import load_specification

WORKSPACE = Path(__file__).resolve().parents[2]


def patterns() -> ScreeningPatterns:
    """The real frozen screen, read from the committed specification."""
    return screening_patterns_from_specification(
        load_specification(WORKSPACE / "experiments" / "exp_009_exus_factor_products.yaml")
    )


# --------------------------------------------------------------------------- #
# The mechanical screen
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Avantis International Small Cap Value ETF", "small_cap_value"),
        ("Dimensional International Small Cap Value ETF", "small_cap_value"),
        ("iShares MSCI EAFE Small-Cap ETF", "small_cap"),
        ("Schwab Fundamental International Small Equity ETF", "small_cap"),
        ("iShares MSCI EAFE Value ETF", "value"),
        ("iShares MSCI EAFE Growth ETF", "growth"),
        ("Invesco S&P International Developed Momentum ETF", "momentum"),
        ("Dimensional International High Profitability ETF", "quality"),
        ("iShares MSCI Emerging Markets Min Vol Factor ETF", "min_vol"),
        ("Hartford Multifactor Developed Markets (ex-US) ETF", "multifactor"),
        ("FlexShares Morningstar Developed Markets ex-US Factor Tilt Index Fund", "multifactor"),
        ("VANGUARD FTSE DEVELOPED MARKETS INDEX FUND", None),
    ],
)
def test_the_mandate_is_derived_from_the_name_in_a_fixed_order(
    name: str, expected: str | None
) -> None:
    """"International Small Cap Value" is small-cap VALUE, not small-cap and not value.

    The pattern list is ordered and the first match wins. If the order were
    reversed, every small-value product on the shelf would be graded on SMB
    instead of HML, which is the single most consequential mislabelling available
    here: it would delete the ex-US small-value result entirely.
    """
    assert derive_mandate(name, patterns()) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("iShares MSCI EAFE Value ETF", "developed_ex_us"),
        ("Avantis Emerging Markets Value ETF", "emerging"),
        ("VANGUARD FTSE ALL-WORLD EX-US SMALL-CAP INDEX FUND", "world_ex_us"),
        ("Vanguard Total International Stock Index Fund", "world_ex_us"),
        ("Dimensional World ex. U.S. Core Equity 2 ETF", "world_ex_us"),
    ],
)
def test_the_region_is_derived_from_the_name(name: str, expected: str) -> None:
    assert derive_region(name, patterns()) == expected


def test_only_two_regions_are_graded_because_only_two_files_exist() -> None:
    """A world-ex-US fund holds both regions in unobservable proportions."""
    assert GRADED_REGIONS == ("developed_ex_us", "emerging")
    assert set(GRADED_REGIONS) < set(PANEL_DATASETS)


@pytest.mark.parametrize(
    ("name", "overlaps"),
    [
        ("Hartford Multifactor Developed Markets (ex-US) ETF", False),
        ("FlexShares Morningstar Developed Markets ex-US Factor Tilt Index Fund", False),
        ("Non-U.S. Intrinsic Value Fund", False),
        ("VANGUARD FTSE ALL-WORLD EX-US SMALL-CAP INDEX FUND", False),
        ("Global X Adaptive U.S. Factor ETF", True),
        ("iShares MSCI World Small-Cap ETF", True),
        ("Capital Group Global Growth Equity ETF", True),
        ("iShares MSCI Global Min Vol Factor ETF", True),
    ],
)
def test_the_ex_us_qualifier_is_stripped_before_the_us_token_is_looked_for(
    name: str, overlaps: bool
) -> None:
    """Without stripping, "(ex-US)" in a fund's own name excludes it from the ex-US audit.

    This is not hypothetical: RODM and TLTD both carry ``ex-US`` in their official
    names and both are ex-US products. A naive US-token test removes exactly the
    funds the experiment is about, and does it silently.
    """
    assert us_overlap(name, patterns()) is overlaps


def _row(series_id: str, name: str, assets: float | None) -> FrameRow:
    return FrameRow(
        accession=f"acc-{series_id}",
        series_id=series_id,
        series_name=name,
        report_date="2019-09-30",
        net_assets=assets,
        is_last_filing=False,
    )


def _facts(ticker: str, expense: float | None) -> ProductFacts:
    return ProductFacts(
        ticker=ticker,
        net_expense_ratio_percent=expense,
        gross_expense_ratio_percent=expense,
        inception_date="2015-01-01",
        index_name="an index",
        index_provider="a provider",
        stated_mandate="value",
        source_url="https://www.sec.gov/Archives/edgar/data/1/2/x.htm",
        date_read="2026-08-12",
    )


def _extra(ticker: str, tier: int) -> ExtraFacts:
    return ExtraFacts(
        ticker=ticker,
        index_region_words="MSCI World ex USA",
        stated_region="developed_ex_us",
        converted_from_mutual_fund=None,
        mandate_change_tier=tier,
        mandate_change_note="a change" if tier else "",
        expense_detail="Total 0.30%",
        source_form="497K",
    )


def test_the_screen_records_the_first_criterion_failed_in_the_fixed_order() -> None:
    """A fund fails for one recorded reason, and the funnel adds up."""
    frame = {
        "S1": _row("S1", "iShares MSCI EAFE Value ETF", 5e9),
        "S2": _row("S2", "iShares MSCI World Small-Cap ETF", 5e9),
        "S3": _row("S3", "Vanguard International Value Dividend ETF", 5e9),
        "S4": _row("S4", "Tiny International Value ETF", 1e8),
        "S5": _row("S5", "Pricey International Value ETF", 5e9),
        "S6": _row("S6", "iShares MSCI EAFE Min Vol Factor ETF", 5e9),
        "S7": _row("S7", "VANGUARD FTSE ALL-WORLD EX-US SMALL-CAP INDEX FUND", 5e9),
        "S8": _row("S8", "Changed International Value ETF", 5e9),
    }
    tickers = {sid: [(f"C{sid}", sid.replace("S", "T"))] for sid in frame}
    flags = {ticker: (True, f"{ticker} security") for sid in frame for _, ticker in tickers[sid]}
    facts = {
        "T1": _facts("T1", 0.31),
        "T5": _facts("T5", 0.95),
        "T8": _facts("T8", 0.30),
    }
    screened, matches = screen_union_frame(
        frame=frame,
        follow_up={},
        class_tickers=tickers,
        exchange_flags=flags,
        facts=facts,
        extra_facts={"T8": _extra("T8", 1)},
        patterns=patterns(),
        minimum_net_assets=5e8,
        maximum_expense_ratio=0.60,
        intended_factor_map={"value": ("HML", 1), "small_cap": ("SMB", 1)},
    )
    assert matches == len(frame)
    outcome = {fund.series_id: fund.failed_criterion for fund in screened}
    assert outcome == {
        "S1": None,
        "S2": "us_overlap",
        "S3": "exclusion_regex",
        "S4": "minimum_net_assets",
        "S5": "maximum_expense_ratio",
        "S6": "mandate_in_map",
        "S7": "region_in_map",
        "S8": "mandate_stable",
    }
    assert set(outcome) == {row.series_id for row in frame.values()}
    assert all(criterion in CRITERION_ORDER for criterion in outcome.values() if criterion)


def test_the_asset_floor_uses_the_largest_of_the_two_censuses() -> None:
    """A fund that launched small and grew is on this shelf; most of it did."""
    frame = {"S1": _row("S1", "Avantis International Small Cap Value ETF", 1e7)}
    follow_up = {"S1": _row("S1", "Avantis International Small Cap Value ETF", 9e9)}
    screened, _ = screen_union_frame(
        frame=frame,
        follow_up=follow_up,
        class_tickers={"S1": [("C1", "AVDV")]},
        exchange_flags={"AVDV": (True, "AVDV")},
        facts={"AVDV": _facts("AVDV", 0.36)},
        extra_facts={},
        patterns=patterns(),
        minimum_net_assets=5e8,
        maximum_expense_ratio=0.60,
        intended_factor_map={"small_cap_value": ("HML", 1)},
    )
    assert screened[0].passed
    assert screened[0].net_assets_max == pytest.approx(9e9)


def test_a_fund_present_only_in_the_later_census_is_still_screened() -> None:
    """Every product this experiment is about launched after the 2019 census."""
    follow_up = {"S1": _row("S1", "Dimensional International Small Cap Value ETF", 3e9)}
    screened, matches = screen_union_frame(
        frame={},
        follow_up=follow_up,
        class_tickers={"S1": [("C1", "DISV")]},
        exchange_flags={"DISV": (True, "DISV")},
        facts={"DISV": _facts("DISV", 0.42)},
        extra_facts={},
        patterns=patterns(),
        minimum_net_assets=5e8,
        maximum_expense_ratio=0.60,
        intended_factor_map={"small_cap_value": ("HML", 1)},
    )
    assert matches == 1
    assert screened[0].passed
    assert screened[0].in_follow_up_census and not screened[0].in_frame_census


# --------------------------------------------------------------------------- #
# The rename trap
# --------------------------------------------------------------------------- #


def test_a_rename_is_not_a_death() -> None:
    """The trap this repository already hit once, in one test.

    Three series start inside the mandate pattern. One liquidates, one merely
    drops the word "Factor" from its name while filing every quarter, and one is
    unchanged. Differencing the two name-qualified sets of identifiers calls both
    of the first two deaths and reports 67% attrition. Only one fund died.
    """
    frame = {
        "DEAD": _row("DEAD", "Doomed International Value ETF", 1e9),
        "RENAMED": _row("RENAMED", "iShares Edge MSCI Intl Value Factor ETF", 2e9),
        "ALIVE": _row("ALIVE", "iShares MSCI EAFE Value ETF", 3e9),
    }
    follow_up = {
        "RENAMED": _row("RENAMED", "iShares International Equity ETF", 2.5e9),
        "ALIVE": _row("ALIVE", "iShares MSCI EAFE Value ETF", 4e9),
        "BORN": _row("BORN", "Avantis International Small Cap Value ETF", 5e9),
    }
    report = attrition(frame, follow_up, patterns())

    assert report.qualifying_in_frame == 3
    assert report.absent_from_follow_up_census == 1
    assert report.renamed_out_of_the_pattern == 1
    assert report.still_qualifying == 1
    assert report.launched_inside_the_window == 1
    assert report.death_rate == pytest.approx(1 / 3)
    assert report.naive_rate == pytest.approx(2 / 3)
    assert report.naive_rate > report.death_rate
    assert report.net_assets_of_absent_series_usd == pytest.approx(1e9)
    assert report.net_assets_of_renamed_series_usd == pytest.approx(2e9)


# --------------------------------------------------------------------------- #
# The guard on Experiment 002
# --------------------------------------------------------------------------- #


def test_experiment_002s_screen_is_still_what_experiment_009_complements() -> None:
    """If exp_002's regexes move, the two audits stop being comparable."""
    committed = load_specification(
        WORKSPACE / "experiments" / "exp_002_fund_exposure.yaml"
    )
    assert isinstance(committed.parameters, dict | type(committed.parameters))
    exp_002_screen_is_unmodified(dict(committed.parameters))  # type: ignore[arg-type]


def test_a_change_to_experiment_002s_screen_aborts_experiment_009() -> None:
    with pytest.raises(UniverseError, match="mandate pattern has changed"):
        exp_002_screen_is_unmodified(
            {"screening_patterns": {"mandate_regex": "value", "exclusion_regex": "x"}}
        )
    with pytest.raises(UniverseError, match="exclusion pattern has changed"):
        exp_002_screen_is_unmodified(
            {
                "screening_patterns": {
                    "mandate_regex": EXP_002_MANDATE_REGEX,
                    "exclusion_regex": "x",
                }
            }
        )


def test_the_two_screens_are_complements_and_cannot_both_admit_a_fund() -> None:
    """exp_002 excludes every region word; exp_009 requires one. No fund is in both."""
    import re

    exp_009 = patterns()
    for name in (
        "iShares MSCI EAFE Value ETF",
        "Avantis Emerging Markets Value ETF",
        "Dimensional International Small Cap Value ETF",
        "Invesco S&P International Developed Momentum ETF",
    ):
        assert re.search(exp_009.region_regex, name, re.IGNORECASE)
        assert re.search(EXP_002_MANDATE_REGEX, name, re.IGNORECASE)
        # exp_002 would have taken it on the mandate pattern and then thrown it
        # out on the exclusion pattern. That is the hole this experiment fills.
        assert re.search(EXP_002_EXCLUSION_REGEX, name, re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Windows
# --------------------------------------------------------------------------- #


def test_the_longest_contiguous_run_is_taken_and_ties_go_to_the_later_one() -> None:
    """A gap makes two time series. HAC across the gap invents a lag structure."""
    assert contiguous_window(["2021-01", "2021-02", "2021-03"]) == (
        "2021-01",
        "2021-02",
        "2021-03",
    )
    assert contiguous_window(
        ["2020-01", "2020-02", "2021-01", "2021-02", "2021-03"]
    ) == ("2021-01", "2021-02", "2021-03")
    assert contiguous_window(["2020-01", "2020-02", "2021-01", "2021-02"]) == (
        "2021-01",
        "2021-02",
    )
    assert contiguous_window([]) == ()


def test_the_window_is_cut_at_the_funds_own_inception() -> None:
    """An SEC series survives a mutual-fund-to-ETF conversion; the product does not.

    DFIV's series carries Tax-Managed DFA International Value Portfolio filings
    from years before the ETF listed on 2021-09-13. Those months are a different
    product at a different fee, and using them would audit a fund nobody could
    have bought.
    """
    from portfolio_edge.experiments.exp_009_exus_products import _window_for

    periods = tuple(
        f"{year}-{month:02d}" for year in (2020, 2021, 2022) for month in range(1, 13)
    )
    panel = _flat_panel(periods)
    series = FundSeries(
        ticker="DFIV",
        series_id="S000012345",
        class_id="C000012345",
        periods=periods,
        returns=np.zeros(len(periods)),
        missing_months=(),
        filing_count=12,
        amendment_count=0,
        filings_held_out=0,
        warnings=(),
        table=panel_table(),
        first_filing_sha256="0" * 64,
    )
    uncut = _window_for(
        series, panel, region="developed_ex_us", start="2020-01", end="2022-12"
    )
    cut = _window_for(
        series,
        panel,
        region="developed_ex_us",
        start="2020-01",
        end="2022-12",
        inception="2021-09-13",
    )
    first_of_month = _window_for(
        series,
        panel,
        region="developed_ex_us",
        start="2020-01",
        end="2022-12",
        inception="2021-09-01",
    )
    assert uncut.first == "2020-01"
    assert uncut.months == 36
    # DFIV listed on the 13th, so September 2021 is a part-month stub and the
    # first WHOLE month the product existed for is October.
    assert cut.first == "2021-10"
    assert cut.months == 15
    # A fund that opened on the first has no stub and keeps its inception month.
    assert first_of_month.first == "2021-09"
    assert first_of_month.months == 16


def _flat_panel(periods: tuple[str, ...]) -> FactorPanel:
    size = len(periods)
    return FactorPanel(
        periods=periods,
        factors={
            name: np.zeros(size)
            for name in ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD")
        },
        risk_free=np.zeros(size),
        provenance={},
    )


def panel_table() -> ParsedTable:
    return ParsedTable(
        table_id="stub",
        banner="stub",
        columns=("total_return",),
        periods=(),
        values=(),
        frequency="monthly",
        source_units="percent",
        units="decimal",
        unit_transform="value / 100",
        warnings=(),
    )


# --------------------------------------------------------------------------- #
# Reported statistics
# --------------------------------------------------------------------------- #


def test_the_minimum_detectable_loading_is_the_same_algebra_as_the_alpha_one() -> None:
    """``(z_{0.975} + z_{0.80}) * SE = 2.8016 * SE``, computed by hand."""
    assert minimum_detectable_loading(0.10) == pytest.approx(0.28016, abs=1e-4)
    assert minimum_detectable_loading(0.10) == minimum_detectable_alpha(0.10)


def test_shelf_depth_counts_only_passing_funds_and_names_them() -> None:
    """An exposure available from one product is a concentration risk, not a choice."""
    funds = (
        _screened("AVDV", "developed_ex_us", "small_cap_value", passed=True),
        _screened("DISV", "developed_ex_us", "small_cap_value", passed=True),
        _screened("IMTM", "developed_ex_us", "momentum", passed=True),
        _screened("AVES", "emerging", "value", passed=True),
        _screened("NOPE", "developed_ex_us", "momentum", passed=False),
    )
    depth = shelf_depth(funds)
    assert depth == {
        "developed_ex_us": {
            "momentum": {"products": 1, "tickers": ["IMTM"]},
            "small_cap_value": {"products": 2, "tickers": ["AVDV", "DISV"]},
        },
        "emerging": {"value": {"products": 1, "tickers": ["AVES"]}},
    }


def _screened(ticker: str, region: str, mandate: str, *, passed: bool) -> ScreenedExUsFund:
    return ScreenedExUsFund(
        ticker=ticker,
        series_id=f"S-{ticker}",
        class_id=f"C-{ticker}",
        series_name_frame="",
        series_name_follow_up=f"{ticker} ETF",
        security_name=ticker,
        passed=passed,
        failed_criterion=None if passed else "minimum_net_assets",
        failure_detail="",
        net_assets_frame=None,
        net_assets_follow_up=1e9,
        net_assets_max=1e9,
        in_frame_census=False,
        in_follow_up_census=True,
        final_filing_flag_seen=False,
        exchange_listed_now=True,
        derived_mandate=mandate,
        derived_region=region,
        intended_factor="HML",
        intended_sign=1,
        facts=None,
    )
