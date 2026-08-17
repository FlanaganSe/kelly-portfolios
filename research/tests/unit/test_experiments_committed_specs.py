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
    "exp_005_regional_replication",
    "exp_006_regional_momentum",
    "exp_007_longonly_capture",
    "exp_008_managed_futures_products",
    "exp_009_exus_factor_products",
    "exp_010_marginal_sleeve_value",
    "exp_010b_growth_basis",
    "exp_011_overlay_stack",
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


def test_exp_002_freezes_the_numbers_its_decision_reads() -> None:
    """Loosening any of these cannot be a quiet edit: it breaks a test and moves
    the specification hash at the same time."""
    spec = load("exp_002_fund_exposure")
    parameters = as_mapping(spec.parameters)
    assert parameters["minimum_intended_loading"] == 0.15
    assert parameters["materiality_threshold_annual_percent"] == 1.0
    assert parameters["minimum_net_assets_usd"] == 1_000_000_000
    assert parameters["maximum_net_expense_ratio_percent"] == 0.60
    assert parameters["inception_on_or_before"] == "2016-12-31"
    assert parameters["hac_lags"] == 6
    # 2020-01..2025-12 is 72 months, exactly six whole years, which is what makes
    # the two calendar halves equal and complete.
    assert spec.sample_policy.start == "2020-01"
    assert spec.sample_policy.end == "2025-12"
    assert parameters["minimum_monthly_observations"] == 72


def test_exp_002_pins_the_shrinkage_arithmetic_and_its_annualisation_trap() -> None:
    """An alpha that is not shrunk, or shrunk with sqrt(12), invents manager skill."""
    shrinkage = as_mapping(
        as_mapping(load("exp_002_fund_exposure").parameters)["alpha_shrinkage"]
    )
    assert shrinkage["sigma_true_annual_percent"] == 1.25
    assert shrinkage["reference_standard_error_annual_percent"] == 3.36
    assert shrinkage["reference_shrinkage_factor"] == 0.121
    trap = str(shrinkage["annualisation_trap"])
    assert "TWELVE" in trap and "sqrt(12)" in trap
    assert "OWN HAC standard error" in str(shrinkage["worked_example"])


def test_exp_002_takes_excess_returns_over_the_same_bill_that_defines_the_market() -> None:
    """A three-month bill would push the maturity spread straight into every alpha."""
    parameters = as_mapping(load("exp_002_fund_exposure").parameters)
    assert parameters["cash_series"] == "french_rf_one_month_bill"
    assert list(as_sequence(parameters["cash_series_alternatives_tested"])) == [
        "TB3MS",
        "DGS3MO",
        "DFF",
    ]
    assert "same rate" in str(parameters["cash_series_rationale"])


def test_exp_002_screens_a_census_taken_at_the_start_of_the_window() -> None:
    """A universe assembled from today's listings is survivorship-contaminated."""
    universe = as_mapping(load("exp_002_fund_exposure").universe)
    frame = as_mapping(as_mapping(universe["screening_rule"])["frame"])
    assert "2019Q4" in str(frame["source"])
    assert "START of the observation window" in str(frame["frame_date_rationale"])
    assert "LOWER BOUND" in str(frame["known_frame_limitation"])


def test_exp_002_declares_the_intended_factor_per_mandate_before_estimating() -> None:
    """Otherwise a fund can be graded against whichever loading turned out largest."""
    universe = as_mapping(load("exp_002_fund_exposure").universe)
    mapping = as_mapping(as_mapping(universe["intended_factor_map"])["mapping"])
    assert as_mapping(mapping["value"]) == {"factor": "HML", "sign": 1}
    assert as_mapping(mapping["growth"]) == {"factor": "HML", "sign": -1}
    assert as_mapping(mapping["momentum"]) == {"factor": "UMD", "sign": 1}
    assert as_mapping(mapping["quality"]) == {"factor": "RMW", "sign": 1}
    # A size-and-style fund is graded on its STYLE leg: the plain size index is
    # separately in the universe, so the tilt is the only thing distinguishing them.
    assert as_mapping(mapping["small_cap_value"]) == {"factor": "HML", "sign": 1}
    assert as_mapping(mapping["mid_cap_growth"]) == {"factor": "HML", "sign": -1}
    assert "mandate_changed" not in set(mapping), (
        "the reserved mandate must stay out of the map so a fund that changed its "
        "objective fails the screen rather than being graded against a mandate it "
        "no longer has"
    )


def test_exp_002_records_what_changed_when_the_frozen_fields_were_made_concrete() -> None:
    """A change made before a result is a different thing from one made after."""
    log = [
        as_mapping(item)
        for item in as_sequence(
            as_mapping(load("exp_002_fund_exposure").parameters)["concretisation_log"]
        )
    ]
    assert len(log) >= 6
    assert all(item["made_before_any_result"] is True for item in log)
    joined = " ".join(str(item["change"]) + str(item["reason"]) for item in log)
    assert "N-PORT" in joined
    assert "0002" in joined, "the return-source change must cite the decision record"
    assert "survivorship" in joined


def test_exp_002_keeps_a_low_alpha_t_statistic_out_of_the_falsifier() -> None:
    """"t below two" over 72 months measures the window, not the fund."""
    spec = load("exp_002_fund_exposure")
    assert "is NOT a falsifier" in spec.falsifier
    assert "no fund is rejected solely because its" in str(spec.rejection_rule)
    requirements = " ".join(str(item) for item in as_sequence(spec.reporting_requirements))
    assert "minimum detectable alpha at 80% power" in requirements
    assert "Raw and shrunk alpha side by side" in requirements
    assert "data contract" in requirements


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


def test_exp_004_pins_the_workbook_sheet_and_the_vintages_it_reads() -> None:
    """A manifest that does not pin the sheet is not reproducible."""
    parameters = as_mapping(load("exp_004_trend_marginal_value").parameters)
    pin = as_mapping(parameters["source_pin"])
    aqr_pin = as_mapping(pin["aqr_tsmom"])
    assert aqr_pin["sheet"] == "TSMOM Factors"
    assert aqr_pin["column"] == "TSMOM"
    assert aqr_pin["expected_sha256_raw"] == (
        "33470930e2269c0d97be4732ec2d9c27ddbc69ac8133b059a263e27400263eeb"
    )
    assert as_mapping(pin["french_us_market"])["expected_sha256_raw"] == (
        "cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b"
    )
    # AQR and Ken French rewrite history in place, so they abort; FRED appends.
    assert "ABORTS" in str(pin["pin_policy"])


def test_exp_004_freezes_the_numbers_its_decision_reads() -> None:
    """Loosening any of these cannot be a quiet edit: it breaks a test and moves
    the specification hash at the same time."""
    spec = load("exp_004_trend_marginal_value")
    parameters = as_mapping(spec.parameters)
    assert parameters["materiality_threshold_annual_percent"] == 0.30
    assert parameters["crra_gamma"] == 3
    assert parameters["sleeve_weight"] == 0.15
    assert parameters["equity_weight"] == 0.60
    assert parameters["exposure_cap"] == 1.5
    assert parameters["volatility_lookback_days"] == 60
    assert list(as_sequence(parameters["volatility_lookback_alternatives_days"])) == [20, 120]
    assert parameters["cash_series"] == "TB3MS"
    # 1990-01..2025-12 is 432 months, exactly 36 whole years, which is what makes
    # the calendar-year certainty equivalent complete.
    assert spec.sample_policy.start == "1990-01"
    assert spec.sample_policy.end == "2025-12"
    assert spec.inference.resamples == 20000

    crises = [as_mapping(item) for item in as_sequence(parameters["crisis_windows"])]
    assert [str(item["name"]) for item in crises] == [
        "dotcom",
        "gfc",
        "covid",
        "inflation_2022",
    ]


def test_exp_004_records_what_changed_when_the_frozen_fields_were_made_concrete() -> None:
    """A change made before a result is a different thing from one made after."""
    parameters = as_mapping(load("exp_004_trend_marginal_value").parameters)
    log = [as_mapping(item) for item in as_sequence(parameters["concretisation_log"])]
    assert len(log) >= 4
    assert all(item["made_before_any_result"] is True for item in log)
    joined = " ".join(str(item["change"]) + str(item["reason"]) for item in log)
    assert "0002" in joined, "the benchmark change must cite the decision record"
    assert "monthly" in joined


def test_exp_004_declares_the_bond_leg_as_modelled_and_not_research_grade() -> None:
    proxy = as_mapping(as_mapping(load("exp_004_trend_marginal_value").parameters)["bond_proxy"])
    assert proxy["research_grade"] is False
    assert "robustness arm only" in str(proxy["used_as"])
    assert "MODELLED" in str(proxy["warning"])


def test_exp_005_inherits_exp_001_era_boundaries_without_moving_one() -> None:
    """Experiment 005 adds regions. Moving a boundary would make it a different test.

    Comparing the two committed specifications directly means a boundary cannot
    drift in either file without breaking this test.
    """
    exp_001 = {
        era.name: (era.start, era.end)
        for era in load("exp_001_factor_decay").sample_policy.eras
    }
    exp_005 = load("exp_005_regional_replication")
    inherited = {era.name: (era.start, era.end) for era in exp_005.sample_policy.eras}
    assert set(inherited) <= set(exp_001), (
        "exp_005 must not invent an era exp_001 does not define"
    )
    for name, window in inherited.items():
        assert window == exp_001[name], f"{name} moved between exp_001 and exp_005"
    # The original-sample eras are excluded on purpose: they begin 1963-07, which
    # precedes both regional files, so a regional cell there would be a different
    # window rather than a replication.
    assert not any("original_sample" in name for name in inherited)
    assert exp_005.sample_policy.end == "2025-12"
    assert exp_005.consumes_final_holdout is False


def test_exp_005_freezes_both_branches_of_a_decisive_falsifier() -> None:
    """Branch (b) must close the programme rather than defer it, in writing."""
    spec = load("exp_005_regional_replication")
    assert spec.run_kind is RunKind.EXPLORATORY
    assert spec.evidence_class is EvidenceClass.PUBLIC_SERIES_EVALUATION
    falsifier = spec.falsifier
    for clause in ("(a1)", "(a2)", "(a3)", "(a4)", "(a5)"):
        assert clause in falsifier
    assert "BRANCH (b)" in falsifier
    assert "CLOSED on public data" in falsifier
    assert "not a request for more research" in falsifier
    parameters = as_mapping(spec.parameters)
    assert parameters["materiality_threshold_annual_percent"] == 2.0
    assert parameters["power_target"] == 0.80
    assert parameters["benjamini_hochberg_alpha"] == 0.10
    rule = str(spec.rejection_rule)
    assert "`unresolved`" in rule and "exactly what would fire" in rule


def test_exp_005_pools_with_declared_equal_weights_and_a_joint_bootstrap() -> None:
    """Independent per-region resampling is the error the design exists to avoid."""
    parameters = as_mapping(load("exp_005_regional_replication").parameters)
    pooling = as_mapping(parameters["pooling"])
    assert pooling["weights"] == "equal"
    weights = as_mapping(pooling["weight_values"])
    assert set(weights) == {"us", "developed_ex_us", "emerging"}
    assert sum(float(str(value)) for value in weights.values()) == pytest.approx(1.0)

    bootstrap = as_mapping(parameters["cross_region_bootstrap"])
    assert "THE SAME row of indices" in str(bootstrap["method"])
    assert "labelled invalid" in str(bootstrap["the_error_it_avoids"])


def test_exp_005_declares_the_effective_sample_size_as_the_decisive_measurement() -> None:
    parameters = as_mapping(load("exp_005_regional_replication").parameters)
    sample = as_mapping(parameters["effective_sample_size"])
    definitions = [as_mapping(item) for item in as_sequence(sample["definitions_all_reported"])]
    assert [str(item["id"]) for item in definitions] == [
        "effective_regions",
        "effective_region_months_iid",
        "effective_region_months_hac",
        "naive_region_months",
    ]
    assert "CONVENTIONAL pooled MDE_80" in str(sample["which_one_the_falsifier_reads"])
    assert "a fortiori" in str(sample["which_one_the_falsifier_reads"])


def test_exp_005_uses_developed_ex_us_and_records_why_umd_is_absent() -> None:
    spec = load("exp_005_regional_replication")
    universe = as_mapping(spec.universe)
    regions = [as_mapping(item) for item in as_sequence(universe["regions"])]
    assert {str(item["dataset_id"]) for item in regions} == {
        "french_us_ff5",
        "french_developed_ex_us_ff5",
        "french_emerging_ff5",
    }
    assert [bool(item["gated_against_a_printed_table"]) for item in regions] == [
        True,
        False,
        False,
    ], "only the US file was ever gated against a printed table"
    assert "INCLUDES the United States" in str(universe["region_non_overlap"])
    assert "one momentum file" in str(universe["umd_is_not_covered"])
    assert list(as_sequence(universe["factors"])) == ["HML", "RMW", "CMA"]


def test_exp_005_tests_the_claim_exp_001_made_about_regional_coverage() -> None:
    """The claim is checked against the data at run time, not restated as prose."""
    parameters = as_mapping(load("exp_005_regional_replication").parameters)
    check = as_mapping(parameters["regional_data_availability_check"])
    assert "shorter than the post-publication windows" in str(check["claim_under_test"])
    assert "FALSE for the eras that matter" in str(check["finding"])
    assert "ABORTS" in str(check["enforcement"])


def test_exp_005_carries_the_us_band_and_calls_the_regional_files_unmeasured() -> None:
    """Ungated is weaker than a band of zero, and must not be read as agreement."""
    parameters = as_mapping(load("exp_005_regional_replication").parameters)
    band = as_mapping(parameters["second_moment_uncertainty"])
    us = as_mapping(band["us_band"])
    assert us["HML"] == 0.0303
    assert us["RMW"] == 0.0509
    assert us["CMA"] == 0.0
    assert band["regional_bands"] == "unmeasured"
    assert "weaker statement than a band of zero" in str(band["regional_statement"])


def test_exp_005_pins_all_three_regional_vintages() -> None:
    parameters = as_mapping(load("exp_005_regional_replication").parameters)
    series = [
        as_mapping(item)
        for item in as_sequence(as_mapping(parameters["source_pin"])["series"])
    ]
    assert len(series) == 3
    pins = {str(entry["region"]): entry for entry in series}
    assert pins["us"]["expected_sha256_raw"] == (
        "cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b"
    )
    assert pins["developed_ex_us"]["expected_sha256_raw"] == (
        "54ffd319a49811548eb4bdcaae6eaedfdd2cf13da2d3ae2e23fb5c43185f563d"
    )
    assert pins["emerging"]["expected_sha256_raw"] == (
        "ea71c1f51d1788c2eeea42ead56897175c5ca24ac4abe40a59346128b1ac51b8"
    )
    # Both regional files must begin before every post-publication boundary,
    # which is the whole reason this experiment is possible.
    assert pins["developed_ex_us"]["expected_first_observation"] == "1990-07"
    assert pins["emerging"]["expected_first_observation"] == "1989-07"


def test_exp_006_inherits_exp_001_era_boundaries_without_moving_one() -> None:
    """Experiment 006 adds regions to UMD. Moving a boundary would make it a different test.

    Comparing the two committed specifications directly means a boundary cannot
    drift in either file without breaking this test, exactly as for exp_005.
    """
    exp_001 = {
        era.name: (era.start, era.end)
        for era in load("exp_001_factor_decay").sample_policy.eras
    }
    exp_006 = load("exp_006_regional_momentum")
    inherited = {era.name: (era.start, era.end) for era in exp_006.sample_policy.eras}
    assert set(inherited) <= set(exp_001), (
        "exp_006 must not invent an era exp_001 does not define"
    )
    for name, window in inherited.items():
        assert window == exp_001[name], f"{name} moved between exp_001 and exp_006"
    assert set(inherited) == {
        "umd_first_post_publication",
        "umd_full_post_publication",
        "recent",
    }
    # The original-sample era is excluded on purpose: it begins 1965-01, which
    # precedes every regional momentum file.
    assert not any("original_sample" in name for name in inherited)
    assert exp_006.sample_policy.end == "2025-12"
    assert exp_006.consumes_final_holdout is False


def test_exp_006_carhart_alternative_matches_exp_001s_predeclared_era() -> None:
    """The hostile test's window is exp_001's, not a number invented here."""
    from portfolio_edge.experiments.exp_006_regional_momentum import (
        CARHART_ALTERNATIVE_END,
        CARHART_ALTERNATIVE_START,
    )

    era = next(
        item
        for item in load("exp_001_factor_decay").sample_policy.eras
        if item.name == "umd_post_carhart_alternative"
    )
    assert (era.start, era.end) == (CARHART_ALTERNATIVE_START, CARHART_ALTERNATIVE_END)


def test_exp_006_reuses_exp_005s_falsifier_pooling_and_joint_bootstrap() -> None:
    spec = load("exp_006_regional_momentum")
    assert spec.run_kind is RunKind.EXPLORATORY
    assert spec.evidence_class is EvidenceClass.PUBLIC_SERIES_EVALUATION
    falsifier = spec.falsifier
    for clause in ("(a1)", "(a2)", "(a3)", "(a4)", "(a5)"):
        assert clause in falsifier
    assert "BRANCH (b)" in falsifier
    assert "CLOSED on public data" in falsifier
    assert "not a request for more research" in falsifier

    parameters = as_mapping(spec.parameters)
    assert parameters["materiality_threshold_annual_percent"] == 2.0
    assert parameters["power_target"] == 0.80
    assert parameters["benjamini_hochberg_alpha"] == 0.10

    pooling = as_mapping(parameters["pooling"])
    assert pooling["weights"] == "equal"
    weights = as_mapping(pooling["weight_values"])
    assert set(weights) == {"us", "developed_ex_us", "emerging"}
    assert sum(float(str(value)) for value in weights.values()) == pytest.approx(1.0)

    bootstrap = as_mapping(parameters["cross_region_bootstrap"])
    assert "THE SAME row of indices" in str(bootstrap["method"])
    assert "labelled invalid" in str(bootstrap["the_error_it_avoids"])

    sample = as_mapping(parameters["effective_sample_size"])
    definitions = [as_mapping(item) for item in as_sequence(sample["definitions_all_reported"])]
    assert [str(item["id"]) for item in definitions] == [
        "effective_regions",
        "effective_region_months_iid",
        "effective_region_months_hac",
        "naive_region_months",
    ]
    assert "CONVENTIONAL pooled MDE_80" in str(sample["which_one_the_falsifier_reads"])


def test_exp_006_pins_three_regional_momentum_vintages_and_their_columns() -> None:
    parameters = as_mapping(load("exp_006_regional_momentum").parameters)
    series = [
        as_mapping(item)
        for item in as_sequence(as_mapping(parameters["source_pin"])["series"])
    ]
    assert len(series) == 3
    pins = {str(entry["region"]): entry for entry in series}
    assert set(pins) == {"us", "developed_ex_us", "emerging"}
    # The US file calls the column Mom and both international files call it WML.
    assert str(pins["us"]["source_column"]) == "Mom"
    assert str(pins["developed_ex_us"]["source_column"]) == "WML"
    assert str(pins["emerging"]["source_column"]) == "WML"
    # Both non-US momentum files must begin before UMD's 1994-01 boundary, which
    # is the whole reason this experiment is possible.
    assert str(pins["developed_ex_us"]["expected_first_observation"]) == "1990-11"
    assert str(pins["emerging"]["expected_first_observation"]) == "1990-01"
    assert int(str(pins["developed_ex_us"]["expected_rows"])) == 428
    assert int(str(pins["emerging"]["expected_rows"])) == 438


def test_exp_006_calls_every_momentum_second_moment_unmeasured() -> None:
    """No momentum file in any region was ever gated against a printed table."""
    parameters = as_mapping(load("exp_006_regional_momentum").parameters)
    band = as_mapping(parameters["second_moment_uncertainty"])
    assert band["regional_bands"] == "unmeasured"
    assert "numerical placeholder" in str(band["unmeasured_not_zero"])
    assert "NO momentum file, in ANY region" in str(band["unmeasured_not_zero"])
    universe = as_mapping(load("exp_006_regional_momentum").universe)
    regions = [as_mapping(item) for item in as_sequence(universe["regions"])]
    assert [bool(item["gated_against_a_printed_table"]) for item in regions] == [
        False,
        False,
        False,
    ]
    assert list(as_sequence(universe["factors"])) == ["UMD"]
    assert "FALSE OF THE DATA" in str(universe["what_experiment_005_got_wrong"])


def test_exp_006_predeclares_the_crash_test_and_names_its_year() -> None:
    """Momentum crashes are state-dependent, so the test must be named in advance."""
    parameters = as_mapping(load("exp_006_regional_momentum").parameters)
    crash = as_mapping(parameters["crash_state_dependence"])
    assert str(crash["named_crash_year"]) == "2009"
    assert "Daniel and Moskowitz" in str(crash["why"])
    assert "state-dependent" in str(crash["why"])
    assert "does not enter the falsifier" in str(crash["consequence"])


def test_exp_006_reports_cost_as_a_schedule_and_refuses_a_long_only_turnover() -> None:
    """Applying long-short turnover to a long-only product is the error being fixed."""
    parameters = as_mapping(load("exp_006_regional_momentum").parameters)
    cost = as_mapping(parameters["cost_sensitivity"])
    assert cost["applied_to_results"] is False
    assert cost["k_optimistic"] == 1.0
    assert cost["k_pessimistic"] == 1.7
    which = as_mapping(cost["which_turnover_belongs_to_what"])
    academic = as_mapping(which["academic_long_short_factor"])
    turnover = as_mapping(academic["turnover_one_sided_monthly_percent"])
    assert turnover["optimistic"] == 27.5
    assert turnover["pessimistic"] == 91.5
    long_only = as_mapping(which["long_only_implementation"])
    assert long_only["turnover_one_sided_monthly_percent"] == "UNMEASURED"
    assert "ORDER OF MAGNITUDE" in str(long_only["basis"])
    assert "MUST NOT" in str(long_only["forbidden"])


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


def test_exp_010b_changes_the_deciding_metric_and_nothing_else() -> None:
    """The re-judgement must differ from exp_010 in the metric and in nothing else.

    Decision record 0008 makes geometric growth the basis every threshold is
    decided on. Its whole evidential value here rests on the two specifications
    being otherwise identical: if the window, the universe, the costs or the seed
    also moved, the change in verdict would not be attributable to the metric.
    Comparing the two committed files directly means neither can drift.
    """
    base = load("exp_010_marginal_sleeve_value")
    rejudged = load("exp_010b_growth_basis")

    assert rejudged.entry_point == base.entry_point
    assert rejudged.seed == base.seed, "a different seed would draw a different bootstrap"
    assert rejudged.sample_policy == base.sample_policy
    assert rejudged.universe != base.universe, "only the control's prose may differ"
    assert rejudged.cost_model == base.cost_model
    assert rejudged.rebalance_rule == base.rebalance_rule
    assert rejudged.data_sources == base.data_sources
    assert rejudged.evidence_class is base.evidence_class
    assert rejudged.run_kind is base.run_kind
    assert rejudged.spec_hash != base.spec_hash

    original = as_mapping(base.parameters)
    parameters = as_mapping(rejudged.parameters)
    assert original.get("decision_gamma") is None, (
        "exp_010 must not name a deciding gamma; it decided on crra_gamma, which is "
        "what the fallback in the module means"
    )
    assert parameters["decision_gamma"] == 1
    assert parameters["crra_gamma"] == 3 == original["crra_gamma"]
    assert parameters["materiality_threshold_annual_percent"] == 0.30 == (
        original["materiality_threshold_annual_percent"]
    )
    assert parameters["reference_weight"] == original["reference_weight"]
    assert parameters["weight_cap"] == original["weight_cap"]
    assert parameters["source_pin"] == original["source_pin"]

    metric = as_mapping(rejudged.primary_metric)
    assert metric["gamma"] == 1
    assert "geometric growth" in str(metric["name"])
    assert str(metric["reported_beside_it_and_deciding_nothing"]).strip()

    rejudgement = as_mapping(parameters["rejudgement"])
    assert rejudgement["supersedes"] == "exp_010_marginal_sleeve_value"
    assert rejudgement["superseded_specification_hash"] == base.spec_hash
    assert rejudgement["data_already_examined"] is True
    assert rejudgement["adds_no_new_trial"] is True
    assert "AFTER" in str(rejudgement["when_it_was_decided"])


def test_exp_010b_restates_every_falsifier_clause_on_the_growth_basis() -> None:
    """A clause left reading the certainty equivalent would decide on de-risking."""
    falsifier = load("exp_010b_growth_basis").falsifier
    for clause in ("(a)", "(b)", "(c)", "(d)", "(u1)", "(u2)", "(u3)", "(u4)", "(u5)"):
        assert clause in falsifier
    assert "GEOMETRIC GROWTH gain" in falsifier
    assert "growth rate contains zero" in falsifier
    assert "marginal GROWTH is positive" in falsifier
    # The only surviving mention of the certainty equivalent is the one that says
    # the clause used to read it.
    assert "certainty-equivalent gain" not in falsifier


def test_exp_011_records_that_it_cannot_be_made_confirmatory_later() -> None:
    """The freeze note is the load-bearing fact and it lives in the file, not in prose."""
    spec = load("exp_011_overlay_stack")
    assert spec.run_kind is RunKind.EXPLORATORY
    assert spec.evidence_class is EvidenceClass.VENDOR_SERIES_EVALUATION
    disclosure = as_mapping(as_mapping(spec.parameters)["evaluation_disclosure"])
    assert disclosure["is_confirmatory"] is False
    assert disclosure["is_independent_replication"] is False
    assert "before this file was written" in str(disclosure["order_of_operations"])
    text = (SPEC_DIR / "exp_011_overlay_stack.yaml").read_text(encoding="utf-8")
    assert "NOT CONFIRMATORY AND CANNOT BE MADE CONFIRMATORY LATER" in text


def test_exp_011_names_the_leverage_matched_control_as_the_primary_benchmark() -> None:
    """Comparing an overlay with unlevered equity flatters it by what the risk earns."""
    benchmark = as_mapping(load("exp_011_overlay_stack").benchmark)
    assert as_mapping(benchmark["primary"])["id"] == "equity_levered_150"
    assert as_mapping(benchmark["secondary"])["id"] == "equity_only"
    assert "MAY NEVER BE ADDED" in str(benchmark["aggregation_rule"])


def test_exp_011_charges_financing_to_the_control_it_is_compared_against() -> None:
    cost_model = as_mapping(load("exp_011_overlay_stack").cost_model)
    assert "LEVERAGE-MATCHED CONTROLS ON THE SAME TERMS" in str(cost_model["charged_uniformly"])
    fees = as_mapping(cost_model["sleeve_fee_annual_percent"])
    assert fees["trend"] == 1.45
    assert fees["commodity"] == 0.0
    assert cost_model["borrow_spread_annual_percent"] == 0.59


def test_exp_011_pins_four_source_vintages_and_aborts_on_a_hash_change() -> None:
    pin = as_mapping(as_mapping(load("exp_011_overlay_stack").parameters)["source_pin"])
    assert pin["abort_on_hash_change"] is True
    series = [as_mapping(item) for item in as_sequence(pin["series"])]
    assert {str(item["name"]) for item in series} == {
        "equity",
        "treasury",
        "credit",
        "commodity",
        "trend",
        "cash",
    }
    assert {str(item["dataset_id"]) for item in series} == {
        "french_us_ff3",
        "goyal_welch_predictors",
        "aqr_commodities_long_run",
        "aqr_tsmom_factors",
    }
    for item in series:
        assert len(str(item["expected_sha256_raw"])) == 64
        assert len(str(item["expected_sha256_normalized"])) == 64


def test_exp_011_keeps_the_commodity_leg_excess_of_cash() -> None:
    """Adding a cash rate to it would invent a collateralised total return."""
    universe = as_mapping(load("exp_011_overlay_stack").universe)
    entry = next(
        as_mapping(item)
        for item in as_sequence(universe["series"])
        if as_mapping(item)["id"] == "commodity"
    )
    assert "NOT a collateralised total return" in str(entry["basis"])


def test_exp_011_carries_a_sleeve_that_is_expected_to_fail_the_admission_bar() -> None:
    """A stack that only reports the sleeves it kept is not a test."""
    parameters = as_mapping(load("exp_011_overlay_stack").parameters)
    weights = {
        str(as_mapping(item)["name"]): as_sequence(as_mapping(item)["weights"])
        for item in as_sequence(parameters["portfolios"])
    }
    assert set(weights) == {
        "equity_only",
        "equity_plus_trend_50",
        "equity_plus_treasury_trend",
        "equity_plus_all_three",
        "equity_levered_135",
        "equity_levered_150",
    }
    assert "commodity" in as_sequence(parameters["sleeves"])
    assert "commodity" not in as_sequence(parameters["portfolio_sleeve_order"])
