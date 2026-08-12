"""The committed managed-futures universe must still mean what the spec froze.

Offline by design. This does not rebuild the universe and does not re-download the
censuses; it checks that the file in Git is internally consistent, that it was
screened with the thresholds the specification actually froze, and that the things
this experiment exists to prevent have not quietly happened -- a hand-picked list,
a universe of survivors, or a rejection that was dropped rather than recorded.

The last of those is the reason this file exists. The project owner named KMLM,
DBMF and CTA. If the screen had admitted exactly those three, the screen would be a
description of the request rather than a rule.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from portfolio_edge.experiments.exp_008_universe import (
    CRITERION_ORDER,
    load_product_facts,
    load_universe,
    product_facts_path,
    universe_path,
)
from portfolio_edge.experiments.specification import JsonValue, load_specification

SPEC = (
    Path(__file__).resolve().parents[2]
    / "experiments"
    / "exp_008_managed_futures_products.yaml"
)

#: The tickers the project owner asked about. Named here so that the test can assert
#: the screen was NOT built around them.
REQUESTED = ("KMLM", "DBMF", "CTA")


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
    order = inputs["criteria_order"]
    assert isinstance(order, list)
    assert order == list(CRITERION_ORDER)
    frozen_order = parameters["criteria_order"]
    assert isinstance(frozen_order, Sequence)
    assert order == [str(item) for item in frozen_order][: len(CRITERION_ORDER)]


def test_the_frame_is_a_union_of_the_two_censuses_and_says_so() -> None:
    """A single late frame would delete every fund that died inside the window."""
    universe = load_universe()
    assert universe.frame_quarter == "2019q4"
    assert universe.follow_up_quarter == "2025q4"
    assert universe.union_series_count > universe.frame_series_count
    assert universe.union_series_count > universe.follow_up_series_count
    assert any("UNION" in note for note in universe.notes)


def test_every_screened_series_records_its_outcome_and_the_funnel_adds_up() -> None:
    universe = load_universe()
    assert len(universe.products) == universe.mandate_matches
    passed = [item for item in universe.products if item.passed]
    failed = [item for item in universe.products if not item.passed]
    assert len(passed) + len(failed) == len(universe.products)
    for item in passed:
        assert item.failed_criterion is None
    for item in failed:
        assert item.failed_criterion in CRITERION_ORDER
        assert item.failure_detail.strip(), f"{item.series_name} failed without a reason"


def test_the_screen_admits_funds_the_owner_did_not_name(
) -> None:
    """The screen is a rule, not a description of the request.

    All three requested tickers pass, and so do two the owner never mentioned. If
    the passing set were exactly the requested set, nothing here would be a screen.
    """
    universe = load_universe()
    passing = {item.ticker for item in universe.passing}
    assert set(REQUESTED) <= passing
    assert passing - set(REQUESTED), "the screen admitted only the funds that were asked about"


def test_the_funds_the_owner_named_are_all_present_in_the_screen_record() -> None:
    universe = load_universe()
    recorded = {item.ticker for item in universe.products}
    for ticker in REQUESTED:
        assert ticker in recorded


def test_no_passing_fund_lacks_a_fee_an_inception_or_a_source() -> None:
    universe = load_universe()
    for item in universe.passing:
        assert item.facts is not None, f"{item.ticker} passed without prospectus facts"
        assert item.facts.net_expense_ratio_percent is not None
        assert item.facts.inception_date is not None
        assert item.facts.source_url.startswith("http")
        assert item.facts.date_read


def test_every_passing_fund_clears_the_frozen_thresholds_it_was_screened_on() -> None:
    universe = load_universe()
    parameters = as_mapping(load_specification(SPEC).parameters)
    ceiling = float(str(parameters["maximum_net_expense_ratio_percent"]))
    floor = float(str(parameters["minimum_net_assets_usd"]))
    cutoff = str(parameters["inception_on_or_before"])
    for item in universe.passing:
        assert item.facts is not None
        assert item.facts.net_expense_ratio_percent is not None
        assert item.facts.net_expense_ratio_percent <= ceiling
        assert item.net_assets_maximum is not None and item.net_assets_maximum >= floor
        assert item.facts.inception_date is not None and item.facts.inception_date <= cutoff
        assert item.intended_target == "aqr_tsmom"


def test_the_asset_floor_was_applied_to_the_larger_of_the_two_observations() -> None:
    universe = load_universe()
    for item in universe.products:
        observed = [
            value
            for value in (item.net_assets_frame, item.net_assets_follow_up)
            if value is not None
        ]
        if observed:
            assert item.net_assets_maximum == pytest.approx(max(observed))
        else:
            assert item.net_assets_maximum is None


def test_funds_that_died_inside_the_window_are_in_the_record() -> None:
    """The union frame's entire purpose, asserted against the committed file."""
    universe = load_universe()
    dead = [
        item
        for item in universe.products
        if item.in_frame_quarter and not item.in_follow_up_quarter
    ]
    assert dead, "no 2019 managed-futures series is absent at follow-up, which cannot be right"
    attrition = as_mapping(universe.attrition)
    gone = attrition["series_present_in_frame_and_absent_from_follow_up_census"]
    assert isinstance(gone, int) and gone >= 1
    assert "LOWER BOUND" in str(attrition["interpretation"])


def test_the_after_tax_tables_are_committed_for_every_passing_fund() -> None:
    """Managed futures are tax-inefficient and N-PORT cannot show it, so the
    prospectus table is the only measure. A passing fund without one would leave the
    tax question silently unanswered rather than answered badly."""
    universe = load_universe()
    _, taxes = load_product_facts()
    for item in universe.passing:
        assert item.ticker in taxes, f"{item.ticker} has no committed after-tax table"
        block = taxes[item.ticker]
        assert block.rows
        assert block.as_of
        assert "highest" in block.methodology.lower()


def test_the_facts_file_states_why_no_threshold_reads_the_after_tax_figures() -> None:
    """The disclosure is load-bearing: the figures were seen before any return."""
    import json

    payload = json.loads(product_facts_path().read_text(encoding="utf-8"))
    assert "after seeing the quantity" in payload["why_no_threshold_uses_these"]
    assert "in NO clause of Experiment 008's frozen falsifier" in (
        payload["why_no_threshold_uses_these"]
    )
