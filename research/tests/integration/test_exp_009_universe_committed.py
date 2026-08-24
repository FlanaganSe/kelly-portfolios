"""The committed ex-US universe must still mean what the frozen specification says.

Offline by design. This does not rebuild the universe and does not re-download
the censuses; it checks that the file in Git is internally consistent, that it
was screened with the thresholds the specification froze, and that the two things
this experiment exists to get right have not quietly stopped being true: that it
is the COMPLEMENT of Experiment 002's screen rather than an overlapping second
pass, and that its attrition measurement still separates a rename from a death.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from portfolio_edge.experiments.exp_002_universe import load_universe as load_us_universe
from portfolio_edge.experiments.exp_002_universe import (
    universe_path as us_universe_path,
)
from portfolio_edge.experiments.exp_009_exus_products import (
    screening_patterns_from_specification,
)
from portfolio_edge.experiments.exp_009_universe import (
    CRITERION_ORDER,
    GRADED_REGIONS,
    derive_mandate,
    derive_region,
    exp_002_screen_is_unmodified,
    load_extra_facts,
    load_product_facts,
    load_universe,
    product_facts_path,
    universe_path,
    us_overlap,
)
from portfolio_edge.experiments.specification import load_specification

WORKSPACE = Path(__file__).resolve().parents[2]
SPEC = WORKSPACE / "experiments" / "exp_009_exus_factor_products.yaml"


def as_mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, Mapping)
    return value


def test_the_universe_and_the_facts_are_committed() -> None:
    assert universe_path().is_file(), "the universe must be built before the audit"
    assert product_facts_path().is_file()


def test_the_universe_was_screened_with_the_thresholds_the_specification_froze() -> None:
    """A universe screened at other thresholds is a different experiment."""
    universe = load_universe()
    parameters = as_mapping(load_specification(SPEC).parameters)
    inputs = as_mapping(universe.inputs)
    committed = as_mapping(inputs["patterns"])
    frozen = screening_patterns_from_specification(load_specification(SPEC))

    assert inputs["minimum_net_assets_usd"] == parameters["minimum_net_assets_usd"]
    assert (
        inputs["maximum_net_expense_ratio_percent"]
        == parameters["maximum_net_expense_ratio_percent"]
    )
    assert committed["region_regex"] == frozen.region_regex
    assert committed["factor_regex"] == frozen.factor_regex
    assert committed["exclusion_regex"] == frozen.exclusion_regex
    assert committed["us_token_regex"] == frozen.us_token_regex
    assert [list(pair) for pair in frozen.mandate_patterns] == list(
        committed["mandate_patterns"]  # type: ignore[call-overload]
    )
    assert list(inputs["criteria_order"]) == list(CRITERION_ORDER)  # type: ignore[call-overload]
    assert list(inputs["graded_regions"]) == list(GRADED_REGIONS)  # type: ignore[call-overload]


def test_the_frame_is_the_union_of_both_censuses() -> None:
    """A 2019Q4-only frame would exclude every product this experiment is about."""
    universe = load_universe()
    assert universe.frame_quarter == "2019q4"
    assert universe.follow_up_quarter == "2025q4"
    assert universe.union_series_count > universe.frame_series_count
    assert universe.union_series_count > universe.follow_up_series_count
    assert universe.mandate_matches > 200, "a census, not a curated list"
    launched_after_2019 = [
        fund
        for fund in universe.passing
        if not fund.in_frame_census and fund.in_follow_up_census
    ]
    assert launched_after_2019, "the union frame exists precisely to admit these"


def test_every_match_is_recorded_including_the_rejections() -> None:
    """The multiple-testing denominator is the whole screen, so nothing is dropped."""
    universe = load_universe()
    assert len(universe.funds) == universe.mandate_matches
    failures = [fund for fund in universe.funds if not fund.passed]
    assert failures
    for fund in failures:
        assert fund.failed_criterion in CRITERION_ORDER
        assert fund.failure_detail


def test_the_passing_funds_satisfy_every_criterion_they_claim_to() -> None:
    universe = load_universe()
    parameters = as_mapping(load_specification(SPEC).parameters)
    floor = float(str(parameters["minimum_net_assets_usd"]))
    cap = float(str(parameters["maximum_net_expense_ratio_percent"]))
    patterns = screening_patterns_from_specification(load_specification(SPEC))
    factor_map = as_mapping(
        as_mapping(as_mapping(load_specification(SPEC).universe)["intended_factor_map"])["mapping"]
    )

    assert universe.passing
    for fund in universe.passing:
        name = fund.series_name_follow_up or fund.series_name_frame
        assert fund.net_assets_max >= floor
        assert fund.facts is not None
        assert fund.facts.net_expense_ratio_percent is not None
        assert fund.facts.net_expense_ratio_percent <= cap
        assert fund.derived_region in GRADED_REGIONS
        assert fund.derived_mandate in factor_map
        assert fund.derived_mandate == derive_mandate(name, patterns)
        assert fund.derived_region == derive_region(name, patterns)
        assert not us_overlap(name, patterns)
        assert fund.intended_factor in {"HML", "SMB", "RMW", "UMD"}
        assert fund.intended_sign in (-1, 1)
        assert fund.exchange_listed_now


def test_a_mandate_that_changed_inside_the_window_is_recorded_and_excluded() -> None:
    """A fund with no single mandate over the window has nothing to be graded against."""
    universe = load_universe()
    extras = load_extra_facts()
    excluded = {
        fund.ticker for fund in universe.funds if fund.failed_criterion == "mandate_stable"
    }
    assert excluded, "the iShares MSCI-to-STOXX transition should have caught some funds"
    for ticker in excluded:
        assert extras[ticker].mandate_change_tier == 1
        assert extras[ticker].mandate_change_note
    for fund in universe.passing:
        extra = extras.get(fund.ticker)
        assert extra is None or extra.mandate_change_tier != 1


def test_attrition_separates_a_rename_from_a_death() -> None:
    """The trap this repository already hit once, checked against the committed file."""
    report = load_universe().attrition
    assert report.qualifying_in_frame > 0
    assert report.renamed_out_of_the_pattern > 0, (
        "if no fund renamed out of the pattern the decomposition is untested on real "
        "data, and the whole point is that renames are common on this shelf"
    )
    assert report.naive_rate > report.death_rate
    assert (
        report.absent_from_follow_up_census
        + report.renamed_out_of_the_pattern
        + report.still_qualifying
        == report.qualifying_in_frame
    )
    assert report.launched_inside_the_window > 0


def test_the_ex_us_screen_is_the_complement_of_the_us_screen_not_an_overlap() -> None:
    """No fund may be audited by both experiments; they partition the same census."""
    assert us_universe_path().is_file()
    us_tickers = {fund.ticker for fund in load_us_universe().passing}
    ex_us_tickers = {fund.ticker for fund in load_universe().passing}
    assert ex_us_tickers
    assert not (us_tickers & ex_us_tickers)


def test_experiment_002s_screen_is_unchanged_so_its_published_numbers_stand() -> None:
    parameters = load_specification(
        WORKSPACE / "experiments" / "exp_002_fund_exposure.yaml"
    ).parameters
    assert isinstance(parameters, Mapping)
    exp_002_screen_is_unmodified(dict(parameters))


def test_every_recorded_fact_carries_a_source_and_a_date_read() -> None:
    """A fee without a date cannot be rechecked, and a fee without a URL cannot be found."""
    for ticker, facts in load_product_facts().items():
        assert facts.source_url.startswith("https://"), ticker
        assert facts.date_read == "2026-08-12", ticker
        assert facts.inception_date, ticker
        assert facts.stated_mandate, ticker
    extras = load_extra_facts()
    audited = {fund.ticker for fund in load_universe().passing}
    for ticker in audited:
        # Every AUDITED fund's facts come from an SEC filing with an accession
        # number, not a sponsor web page. VTI is the one carried-over exception
        # and it is not audited here.
        assert extras[ticker].source_form, ticker
        assert "accession" in extras[ticker].source_form.lower(), ticker
        assert extras[ticker].expense_detail, ticker


@pytest.mark.parametrize("ticker", ["VEA", "VWO", "VSS", "IEFA", "VTI"])
def test_the_comparators_and_replication_basis_have_recorded_facts(ticker: str) -> None:
    facts = load_product_facts()
    assert ticker in facts
    assert facts[ticker].net_expense_ratio_percent is not None


def test_the_conversion_trap_is_recorded_where_it_applies() -> None:
    """A mutual-fund-to-ETF conversion leaves pre-ETF filings on the same SEC series."""
    extras = load_extra_facts()
    converted = {
        ticker: extra.converted_from_mutual_fund
        for ticker, extra in extras.items()
        if extra.converted_from_mutual_fund
    }
    assert "DFIV" in converted
    assert "2021-09" in str(converted["DFIV"])
