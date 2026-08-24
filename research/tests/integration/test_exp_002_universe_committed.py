"""The committed product universe must still mean what the frozen specification says.

Offline by design. This does not rebuild the universe and does not re-download
the censuses; it checks that the file in Git is internally consistent, that it
was screened with the thresholds the specification actually froze, and that the
things this experiment exists to prevent have not quietly happened -- a curated
list, a universe of survivors, or a rejection that was dropped rather than
recorded.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from portfolio_edge.experiments.exp_002_universe import (
    CRITERION_ORDER,
    load_product_facts,
    load_universe,
    product_facts_path,
    universe_path,
)
from portfolio_edge.experiments.specification import JsonValue, load_specification

SPEC = Path(__file__).resolve().parents[2] / "experiments" / "exp_002_fund_exposure.yaml"


def as_mapping(value: JsonValue | object) -> Mapping[str, object]:
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
    patterns = as_mapping(parameters["screening_patterns"])

    assert inputs["minimum_net_assets_usd"] == parameters["minimum_net_assets_usd"]
    assert (
        inputs["maximum_net_expense_ratio_percent"]
        == parameters["maximum_net_expense_ratio_percent"]
    )
    assert inputs["inception_on_or_before"] == parameters["inception_on_or_before"]
    assert inputs["mandate_pattern"] == patterns["mandate_regex"]
    assert inputs["exclusion_pattern"] == patterns["exclusion_regex"]
    assert list(inputs["criteria_order"]) == list(CRITERION_ORDER)  # type: ignore[call-overload]


def test_the_frame_is_the_census_at_the_start_of_the_window_not_the_end() -> None:
    universe = load_universe()
    assert universe.frame_quarter == "2019q4"
    assert universe.follow_up_quarter == "2025q4"
    assert universe.frame_series_count > 5000, "a census, not a curated list"
    assert universe.mandate_matches > 500


def test_every_mandate_match_is_recorded_including_the_rejections() -> None:
    """The multiple-testing denominator is the whole screen, so nothing is dropped."""
    universe = load_universe()
    assert len(universe.funds) == universe.mandate_matches
    failures = [fund for fund in universe.funds if not fund.passed]
    assert failures, "a screen with no recorded rejection is not a screen"
    for fund in failures:
        assert fund.failed_criterion in CRITERION_ORDER
        assert fund.failure_detail.strip(), (
            f"{fund.series_name} was rejected without a stated reason"
        )


def test_the_passing_funds_satisfy_every_criterion_they_claim_to() -> None:
    universe = load_universe()
    parameters = as_mapping(load_specification(SPEC).parameters)
    minimum = float(str(parameters["minimum_net_assets_usd"]))
    maximum_fee = float(str(parameters["maximum_net_expense_ratio_percent"]))
    cutoff = str(parameters["inception_on_or_before"])

    assert universe.passing, "the audit has nothing to do if nothing passed"
    for fund in universe.passing:
        assert fund.ticker
        assert fund.class_id.startswith("C")
        assert fund.net_assets_frame is not None and fund.net_assets_frame >= minimum
        assert fund.facts is not None
        assert fund.facts.net_expense_ratio_percent is not None
        assert fund.facts.net_expense_ratio_percent <= maximum_fee
        assert fund.facts.inception_date is not None
        assert fund.facts.inception_date <= cutoff
        assert fund.intended_factor in {"HML", "SMB", "RMW", "UMD", "CMA"}
        assert fund.intended_sign in (-1, 1)
        assert fund.exchange_listed_now is True


def test_attrition_is_measured_rather_than_assumed_away() -> None:
    """The number that says how contaminated a universe assembled today would be."""
    attrition = as_mapping(load_universe().attrition)
    gone = int(str(attrition["series_present_in_frame_and_absent_at_follow_up"]))
    started = int(str(attrition["mandate_qualifying_series_in_frame"]))
    born = int(str(attrition["series_absent_from_frame_and_present_at_follow_up"]))
    assert started > 0
    assert gone > 0, (
        "zero attrition over six years would mean the follow-up census was not "
        "actually read"
    )
    assert 0.0 < float(str(attrition["attrition_rate"])) < 1.0
    assert born > 0
    assert "LOWER BOUND" in str(attrition["interpretation"])


def test_a_fund_that_died_inside_the_window_still_passed_the_screen() -> None:
    """The screen must not select on survival, even accidentally.

    Nothing in the criteria mentions survival, so a passing fund that stopped
    filing is expected and permitted. Asserting the field exists and is a boolean
    keeps a future edit from turning "still trading" into a hidden criterion.
    """
    for fund in load_universe().passing:
        assert isinstance(fund.still_filing_at_follow_up, bool)


def test_every_recorded_fact_carries_a_source_url_and_a_date_read() -> None:
    """A fee or an index can change; a number without a date cannot be rechecked."""
    for ticker, facts in load_product_facts().items():
        assert facts.source_url.startswith("https://"), ticker
        assert facts.date_read.count("-") == 2, ticker
        assert facts.index_name, ticker
        assert facts.stated_mandate, ticker


def test_a_fund_that_changed_its_mandate_is_recorded_and_excluded() -> None:
    """It has no single stated mandate over the window, so there is nothing to grade.

    Recorded rather than dropped: a silently missing fund is indistinguishable
    from a fund nobody looked for.
    """
    import json

    payload = json.loads(product_facts_path().read_text(encoding="utf-8"))
    changes = payload["mandate_changes"]
    tier_one = [item for item in changes if item["tier"] == 1]
    assert tier_one, "the mandate-change register must not be empty"
    universe = load_universe()
    passing = {fund.ticker for fund in universe.passing}
    for item in tier_one:
        for ticker in str(item["ticker"]).split(","):
            assert ticker.strip() not in passing, (
                f"{ticker} changed its stated mandate on {item['date']} and must "
                "not be graded against a mandate it no longer has"
            )
            assert item["date"]
            assert str(item["source_url"]).startswith("https://")
    tier_two = [item for item in changes if item["tier"] == 2]
    assert tier_two, (
        "index and methodology changes that leave the mandate intact must still be "
        "registered, because they are what the stability test is looking for"
    )


@pytest.mark.parametrize("ticker", ["VTI", "VUG", "VTV", "VB"])
def test_the_comparator_and_replication_basis_have_recorded_facts(ticker: str) -> None:
    """The benchmark is priced too; a zero expense ratio would flatter the product."""
    facts = load_product_facts()
    assert ticker in facts
    assert facts[ticker].net_expense_ratio_percent is not None
