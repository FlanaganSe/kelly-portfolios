"""The committed union-frame universe must still mean what its specification says.

Offline by design. This does not rebuild the universe and does not re-download the
censuses; it checks that the file in Git is internally consistent, that it was
screened with the thresholds the specification froze, and that the two things this
experiment exists to get right have not quietly stopped being true: that the
corrected frame is a strict SUPERSET of Experiment 002's screen rather than a
different screen, and that the only criteria which moved are the two that were
declared.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from portfolio_edge.experiments.exp_002_universe import load_universe as load_exp_002_universe
from portfolio_edge.experiments.exp_002_universe import (
    product_facts_path as exp_002_facts_path,
)
from portfolio_edge.experiments.exp_013_universe import (
    CRITERION_ORDER,
    exp_002_screen_is_unmodified,
    load_extra_facts,
    load_product_facts,
    load_universe,
    product_facts_path,
    universe_path,
)
from portfolio_edge.experiments.exp_013_us_products_union_frame import _exp_002_parameters
from portfolio_edge.experiments.specification import load_specification

WORKSPACE = Path(__file__).resolve().parents[2]
SPEC = WORKSPACE / "experiments" / "exp_013_us_products_union_frame.yaml"


def as_mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, Mapping)
    return value


def test_the_universe_and_the_facts_are_committed() -> None:
    assert universe_path().is_file(), "the universe must be built before the audit"
    assert product_facts_path().is_file()


def test_experiment_002s_screen_is_still_the_one_this_experiment_re_frames() -> None:
    exp_002_screen_is_unmodified(_exp_002_parameters())


def test_the_universe_was_screened_with_the_thresholds_the_specification_froze() -> None:
    """A universe screened at other thresholds is a different experiment."""
    universe = load_universe()
    parameters = as_mapping(load_specification(SPEC).parameters)
    patterns = as_mapping(parameters["screening_patterns"])
    inputs = as_mapping(universe.inputs)

    assert inputs["minimum_net_assets_usd"] == parameters["minimum_net_assets_usd"]
    assert (
        inputs["maximum_net_expense_ratio_percent"]
        == parameters["maximum_net_expense_ratio_percent"]
    )
    assert inputs["mandate_pattern"] == patterns["mandate_regex"]
    assert inputs["exclusion_pattern"] == patterns["exclusion_regex"]
    assert list(inputs["criteria_order"]) == list(CRITERION_ORDER)  # type: ignore[call-overload]
    assert inputs["inception_cutoff"] is None


def test_the_frame_is_the_union_of_both_censuses() -> None:
    """A 2019Q4-only frame excludes by construction every product that launched,
    converted or began filing after 2019, which is the defect being corrected."""
    universe = load_universe()
    assert universe.frame_quarter == "2019q4"
    assert universe.follow_up_quarter == "2025q4"
    assert universe.union_series_count > universe.frame_series_count
    assert universe.union_series_count > universe.follow_up_series_count
    assert any(not fund.in_frame_census for fund in universe.passing)


def test_the_union_frame_still_retains_funds_that_died_inside_the_window() -> None:
    """The union must not become a survivorship screen. Retaining series that are
    in 2019Q4 and gone by 2025Q4 is the property Experiment 002's start-of-window
    frame was protecting, and it survives the correction."""
    universe = load_universe()
    dead = [fund for fund in universe.funds if fund.in_frame_census and not fund.in_follow_up_census]
    assert dead, "a frame that carries no dead series has selected on survival"


def test_the_screen_is_a_strict_superset_of_experiment_002s() -> None:
    """The single most important check on this page's claim.

    If a fund Experiment 002 audited failed here, the difference between the two
    audits would not be the frame, and every comparison of their verdicts would be
    confounded. Nothing may TIGHTEN.
    """
    old = {fund.ticker for fund in load_exp_002_universe().passing}
    new = {fund.ticker for fund in load_universe().passing}
    assert old <= new, f"funds Experiment 002 passed and this screen does not: {sorted(old - new)}"
    assert new - old, "the corrected frame is supposed to admit funds; it admitted none"


def test_every_shared_fact_is_experiment_002s_verbatim() -> None:
    """A fee or a stated mandate must not differ between the two audits for a fund
    they share, or a difference in verdict could be a difference in facts."""
    import json

    old = json.loads(exp_002_facts_path().read_text(encoding="utf-8"))["funds"]
    new = json.loads(product_facts_path().read_text(encoding="utf-8"))["funds"]
    shared = sorted(set(old) & set(new))
    assert shared
    for ticker in shared:
        for field in (
            "net_expense_ratio_percent",
            "gross_expense_ratio_percent",
            "inception_date",
            "stated_mandate",
            "index_name",
            "source_url",
        ):
            assert new[ticker][field] == old[ticker][field], f"{ticker}.{field}"
        assert new[ticker]["carried_from_exp_002"] is True


def test_every_criterion_recorded_is_one_the_order_declares() -> None:
    universe = load_universe()
    for fund in universe.funds:
        assert fund.failed_criterion is None or fund.failed_criterion in CRITERION_ORDER
        assert fund.passed == (fund.failed_criterion is None)


def test_every_passing_fund_carries_a_verified_fee_and_a_mapped_mandate() -> None:
    universe = load_universe()
    facts = load_product_facts()
    assert universe.passing
    for fund in universe.passing:
        assert fund.facts is not None
        assert fund.facts.net_expense_ratio_percent is not None
        assert fund.facts.net_expense_ratio_percent <= 0.60
        assert fund.intended_factor in {"HML", "SMB", "RMW", "UMD"}
        assert fund.intended_sign in (-1, 1)
        assert facts[fund.ticker].stated_mandate == fund.facts.stated_mandate


def test_minimum_volatility_products_are_recorded_and_not_graded() -> None:
    """The union frame admits large minimum-volatility products for the first time.
    Adding a mandate to the map after seeing which funds the frame admits would be
    exactly the discretionary edit this experiment exists to avoid."""
    universe = load_universe()
    facts = load_product_facts()
    minimum_volatility = [
        fund
        for fund in universe.funds
        if facts.get(fund.ticker) is not None
        and facts[fund.ticker].stated_mandate == "min_volatility"
    ]
    assert minimum_volatility
    for fund in minimum_volatility:
        assert not fund.passed
        assert fund.failed_criterion == "mandate_in_map"


def test_a_converted_fund_records_the_etf_date_separately_from_the_prospectus_one() -> None:
    """A converted fund's stated inception is its predecessor mutual fund's, and
    using it would audit a fund nobody could have bought at that fee."""
    extras = load_extra_facts()
    converted = [item for item in extras.values() if item.converted_from_mutual_fund]
    for item in converted:
        assert item.etf_inception_date is not None, item.ticker
