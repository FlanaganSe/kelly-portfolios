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
