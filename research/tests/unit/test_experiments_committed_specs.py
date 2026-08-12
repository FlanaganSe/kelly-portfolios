"""The committed specifications must load, hash, and mean what they say."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from portfolio_edge.experiments.specification import (
    EvidenceClass,
    JsonValue,
    RunKind,
    Specification,
    load_specification,
    validate_specification,
)


def as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def as_sequence(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value

SPEC_DIR = Path(__file__).resolve().parents[2] / "experiments"
SPEC_NAMES = (
    "exp_001_factor_decay",
    "exp_002_fund_exposure",
    "exp_003_rebalancing",
    "exp_004_trend_marginal_value",
    "phase1_ff_reproduction",
)


def load(name: str) -> Specification:
    return load_specification(SPEC_DIR / f"{name}.yaml")


def test_every_committed_specification_is_present() -> None:
    found = sorted(path.stem for path in SPEC_DIR.glob("*.yaml"))
    assert found == sorted(SPEC_NAMES)


@pytest.mark.parametrize("name", SPEC_NAMES)
def test_specification_loads_validates_and_hashes(name: str) -> None:
    spec = load(name)
    validate_specification(spec)
    assert spec.experiment_family == name
    assert len(spec.spec_hash) == 64
    assert spec.spec_hash == load(name).spec_hash
    assert spec.sample_policy.eras
    assert spec.sample_policy.held_out
    assert spec.hostile_tests
    assert spec.reporting_requirements


def test_specification_hashes_are_distinct() -> None:
    hashes = {name: load(name).spec_hash for name in SPEC_NAMES}
    assert len(set(hashes.values())) == len(SPEC_NAMES)


def test_exp_001_falsifier_is_not_a_bare_95_percent_test() -> None:
    spec = load("exp_001_factor_decay")
    assert spec.run_kind is RunKind.EXPLORATORY
    falsifier = spec.falsifier.lower()
    assert "is explicitly not a falsifier" in falsifier
    assert "power" in falsifier
    assert "unresolved" in falsifier
    assert falsifier.count("(a)") == 1 and "(b)" in falsifier and "(c)" in falsifier
    assert isinstance(spec.parameters, Mapping)
    assert spec.parameters["materiality_threshold_annual_percent"] == 2.0
    era_names = {era.name for era in spec.sample_policy.eras}
    for required in (
        "hml_original_sample",
        "hml_first_post_publication",
        "hml_full_post_publication",
        "recent",
        "common_period",
    ):
        assert required in era_names


def test_exp_001_pins_its_source_vintages() -> None:
    """Without a pin the experiment would silently follow the next CRSP rebuild."""
    parameters = as_mapping(load("exp_001_factor_decay").parameters)
    entries = as_sequence(as_mapping(parameters["source_pin"])["series"])
    series = [as_mapping(item) for item in entries]
    assert len(series) == 2
    pins = {str(entry["dataset_id"]): entry for entry in series}
    assert pins["french_us_ff5"]["expected_sha256_raw"] == (
        "cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b"
    )
    assert pins["french_us_momentum"]["expected_sha256_raw"] == (
        "f405ee2d47a5c75ce05025f789733d0599879361e9836a553504240b89159871"
    )
    assert list(as_sequence(pins["french_us_ff5"]["factor_columns"])) == ["HML", "RMW", "CMA"]
    assert list(as_sequence(pins["french_us_momentum"]["factor_columns"])) == ["UMD"]


def test_exp_001_freezes_the_multiple_testing_family_before_the_run() -> None:
    """A family fixed after the fact is a family fitted to whatever survived."""
    parameters = as_mapping(load("exp_001_factor_decay").parameters)
    grid = as_mapping(parameters["primary_grid"])
    roles = [str(role) for role in as_sequence(grid["era_roles"])]
    assert roles == [
        "original_sample",
        "first_post_publication",
        "full_post_publication",
        "recent",
        "common_period",
    ]
    cells = as_mapping(grid["cells"])
    assert set(cells) == {"HML", "UMD", "RMW", "CMA"}
    for factor in cells:
        assert set(as_mapping(cells[factor])) == set(roles)
    # RMW and CMA share every era, so the 20 tests are not 20 independent ones.
    assert as_mapping(cells["RMW"]) == as_mapping(cells["CMA"])
    assert "LOWER BOUND" in str(grid["dependence_warning"])


def test_exp_001_carries_the_phase_1_volatility_band_it_inherited() -> None:
    """The Phase 1 gate is UNRESOLVED; this is the band that inheritance implies.

    Pinning the two numbers here means loosening or dropping them cannot be a
    quiet edit: it breaks a test and changes the specification hash at once.
    """
    parameters = as_mapping(load("exp_001_factor_decay").parameters)
    band = as_mapping(parameters["second_moment_uncertainty"])
    relative = as_mapping(band["relative_band_on_volatility"])
    assert relative["HML"] == 0.0303
    assert relative["RMW"] == 0.0509
    assert relative["CMA"] == 0.0
    assert "SYSTEMATIC" in str(band["consequence"])
    assert "never combined" in str(band["consequence"])


def test_exp_001_justifies_every_boundary_from_the_publication_record() -> None:
    parameters = as_mapping(load("exp_001_factor_decay").parameters)
    record = as_mapping(parameters["publication_record"])
    assert set(record) >= {"HML", "UMD", "RMW", "CMA"}
    expected_years = {"HML": 1993, "UMD": 1993, "RMW": 2015, "CMA": 2015}
    expected_boundaries = {
        "HML": "1994-01",
        "UMD": "1994-01",
        "RMW": "2014-01",
        "CMA": "2014-01",
    }
    for factor, year in expected_years.items():
        entry = as_mapping(record[factor])
        assert entry["publication_year_used"] == year
        assert entry["first_post_publication_boundary"] == expected_boundaries[factor]
        assert str(entry["boundary_justification"]).strip()
        assert as_sequence(entry["predecessor_evidence"]), (
            f"{factor} must record its predecessor evidence; no date here is clean"
        )
        assert str(entry["alternative_date_tested"]).strip()


def test_exp_001_declares_its_cost_illustration_as_a_column_not_a_haircut() -> None:
    parameters = as_mapping(load("exp_001_factor_decay").parameters)
    illustration = as_mapping(parameters["cost_illustration"])
    assert illustration["applied_to_results"] is False
    assert illustration["k_optimistic"] == 1.0
    assert illustration["k_pessimistic"] == 1.7
    turnover = as_mapping(illustration["one_sided_monthly_turnover_percent"])
    assert set(turnover) == {"HML", "UMD", "RMW", "CMA"}
    assert as_mapping(turnover["UMD"])["pessimistic"] == 91.5
    assert as_mapping(turnover["HML"])["pessimistic"] == 7.2
    assert "144%" in str(illustration["published_outcome_to_keep_in_view"])


def test_exp_001_requires_power_for_every_cell() -> None:
    """The single most important statistical requirement of this experiment."""
    parameters = as_mapping(load("exp_001_factor_decay").parameters)
    assert parameters["power_target"] == 0.80
    assert list(as_sequence(parameters["rolling_windows_months"])) == [12, 36, 60, 120]
    power = as_mapping(parameters["power"])
    assert power["reported_for_every_cell"] is True
    assert len(as_sequence(power["also_report"])) >= 3
    requirements = " ".join(
        str(item) for item in as_sequence(load("exp_001_factor_decay").reporting_requirements)
    )
    assert "80%-power" in requirements
    assert "Politis-White" in requirements


def test_exp_002_predeclares_a_screening_rule_and_records_every_fund() -> None:
    spec = load("exp_002_fund_exposure")
    assert spec.run_kind is RunKind.EXPLORATORY
    assert spec.evidence_class is EvidenceClass.FUND_IMPLEMENTATION_AUDIT
    universe = spec.universe
    assert isinstance(universe, Mapping)
    screen = universe["screening_rule"]
    assert isinstance(screen, Mapping)
    assert len(as_sequence(screen["criteria"])) >= 5
    assert screen["recorded_for_every_screened_fund"]
    assert 'no "and peers" clause' in str(screen["description"])
    assert "common_period" in {era.name for era in spec.sample_policy.eras}


def test_exp_003_is_confirmatory_and_passes_its_own_gate() -> None:
    spec = load("exp_003_rebalancing")
    assert spec.run_kind is RunKind.CONFIRMATORY
    validate_specification(spec)
    assert spec.seed is not None
    assert spec.consumes_final_holdout is False
    rule = spec.rebalance_rule
    assert isinstance(rule, Mapping)
    policies = as_sequence(rule["policies"])
    assert [as_mapping(policy)["id"] for policy in policies] == [
        "buy_and_hold",
        "annual_calendar",
        "monthly_calendar",
        "relative_threshold_25pct",
        "cash_flow_directed",
    ]
    costs = spec.cost_model
    assert isinstance(costs, Mapping)
    taxes = costs["taxes"]
    assert isinstance(taxes, Mapping)
    assert taxes["modelled"] is False
    assert "FORBIDDEN" in str(taxes["reason"])
    assert list(as_sequence(costs["reporting_columns"])) == [
        "gross",
        "net-optimistic",
        "net-pessimistic",
    ]


def test_exp_003_freezes_the_numbers_its_decision_reads() -> None:
    """Pinning them here means loosening one cannot be a quiet edit.

    A widened materiality threshold, a lowered gamma, or a cheapened cost
    assumption would each move the verdict without moving anything a reader sees.
    Changing any of them now breaks a test and changes the specification hash at
    the same time.
    """
    spec = load("exp_003_rebalancing")
    parameters = as_mapping(spec.parameters)
    assert parameters["materiality_threshold_annual_percent"] == 0.25
    assert parameters["drawdown_tolerance_percentage_points"] == 1.0
    assert parameters["crra_gamma"] == 3
    assert parameters["relative_threshold"] == 0.25

    metric = as_mapping(spec.primary_metric)
    assert metric["gamma"] == 3

    spread = as_mapping(as_mapping(spec.cost_model)["spread_and_commission"])
    assert as_mapping(spread["net_optimistic"])["one_way_bps"] == 2.0
    assert as_mapping(spread["net_pessimistic"])["one_way_bps"] == 8.0
    assert as_mapping(spec.cost_model)["default_reported_column"] == "net-pessimistic"

    # 420 months is exactly 35 whole calendar years, which is what makes the
    # annual certainty-equivalent blocks non-overlapping and complete.
    assert spec.sample_policy.start == "1991-01"
    assert spec.sample_policy.end == "2025-12"
    assert spec.inference.resamples == 20000
    assert spec.inference.confidence_level == 0.95


def test_exp_003_uses_developed_ex_us_and_not_the_file_that_contains_the_us() -> None:
    """The bug this experiment found, asserted so it cannot come back.

    ``Developed_5_Factors`` includes the United States at roughly half its weight.
    Using it beside a US sleeve would double-count half the US market and destroy
    the very comparison the experiment exists to make.
    """
    spec = load("exp_003_rebalancing")
    universe = as_mapping(spec.universe)
    sleeves = [as_mapping(item) for item in as_sequence(universe["sleeves"])]
    datasets = {str(item["dataset_id"]) for item in sleeves}
    assert datasets == {
        "french_us_ff5",
        "french_developed_ex_us_ff5",
        "french_emerging_ff5",
    }
    assert "french_developed_ff5" not in datasets
    assert all(item["construction"] == "Mkt-RF + RF" for item in sleeves)
    assert "INCLUDES the United States" in str(universe["data_integrity_finding"])

    weights = as_mapping(universe["starting_weights"])
    assert sum(float(str(value)) for value in weights.values()) == pytest.approx(1.0)


def test_exp_003_reports_the_investability_drag_without_applying_it() -> None:
    """An index-like series is not a fund, and the gap is a column, not a haircut."""
    drag = as_mapping(as_mapping(load("exp_003_rebalancing").cost_model)["index_to_fund_drag"])
    assert drag["applied_to_returns"] is False
    assert drag["reported_separately"] is True
    assert set(as_mapping(drag["expense_ratio_bp_per_year"])) == {
        "us_equity",
        "developed_ex_us_equity",
        "emerging_equity",
    }
    assert "ASSUMPTION" in str(drag["withholding_basis"])
    assert "cannot change their order" in str(drag["why_it_cannot_change_the_ranking"])


def test_exp_003_cash_flow_schedule_cannot_look_ahead() -> None:
    """Indexing a contribution to realised CPI would use tomorrow's information."""
    flows = as_mapping(as_mapping(load("exp_003_rebalancing").rebalance_rule)["cash_flows"])
    assert flows["indexation"] == "none"
    assert flows["annual_amount_fraction_of_initial_wealth"] == 0.05
    assert "unavailable at the start of the path" in str(flows["indexation_rationale"])


def test_exp_004_declares_itself_a_vendor_series_evaluation() -> None:
    spec = load("exp_004_trend_marginal_value")
    assert spec.evidence_class is EvidenceClass.VENDOR_SERIES_EVALUATION
    parameters = spec.parameters
    assert isinstance(parameters, Mapping)
    disclosure = parameters["evaluation_disclosure"]
    assert isinstance(disclosure, Mapping)
    assert disclosure["is_vendor_series_evaluation"] is True
    assert disclosure["is_independent_replication"] is False
    assert "NOT an independent replication" in str(disclosure["statement"])

    hostile = " ".join(str(item).lower() for item in spec.hostile_tests)
    for required in (
        "best trend month",
        "best crisis",
        "delay execution",
        "double every cost",
        "cap leverage",
        "gaps",
        "volatility lookback",
        "pre-publication and post-publication",
        "attribute returns",
    ):
        assert required in hostile


def test_phase1_targets_table_4_and_pins_its_vintage() -> None:
    spec = load("phase1_ff_reproduction")
    assert spec.run_kind is RunKind.CONFIRMATORY
    assert spec.evidence_class is EvidenceClass.SOURCE_REPRODUCTION
    parameters = as_mapping(spec.parameters)

    targets = as_sequence(parameters["published_targets"])
    gating = [t for t in (as_mapping(item) for item in targets) if t["gating"] is True]
    assert len(gating) == 1, "exactly one printed table decides this gate"
    primary = gating[0]
    # Table 1 of Fama and French (2015) is the 25 test portfolios. The factor
    # summary statistics are Table 4. Freezing the wrong number would target the
    # wrong numbers.
    assert primary["table"] == "Table 4"
    assert primary["observations"] == 606
    assert set(as_mapping(primary["factors"])) == {"Mkt-RF", "SMB", "HML", "RMW", "CMA"}

    pin = as_mapping(parameters["source_pin"])
    assert pin["expected_sha256_raw"] == (
        "cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b"
    )
    assert [era.name for era in spec.sample_policy.eras] == [
        "ff2015_jfe_published",
        "ff2013_working_paper",
    ]


def test_phase1_gate_tolerance_is_the_one_that_was_predeclared() -> None:
    """A widened tolerance is the failure mode this gate exists to prevent.

    Pinning the numbers here means loosening them cannot be a quiet edit: it
    breaks a test and changes the specification hash at the same time.
    """
    parameters = as_mapping(load("phase1_ff_reproduction").parameters)
    tolerances = as_mapping(parameters["tolerances"])
    gate = as_mapping(tolerances["gate"])
    assert gate["mean_percent_per_month"] == 0.02
    assert gate["std_dev_percent_per_month"] == 0.05
    assert gate["t_statistic"] == 0.30
    exact = as_mapping(tolerances["print_exact_diagnostic"])
    assert exact["mean_percent_per_month"] == 0.005
    assert as_mapping(tolerances["implementation_error"])["mean_percent_per_month"] == 0.10


def test_committed_specifications_do_not_spend_the_final_holdout() -> None:
    for name in SPEC_NAMES:
        assert load(name).consumes_final_holdout is False
