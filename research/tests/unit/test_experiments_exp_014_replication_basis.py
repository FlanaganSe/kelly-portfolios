"""Experiment 014 varies the replicating basis and nothing else.

Every test here exists to make one of three things impossible: a silent drift in
the baseline this experiment measures a difference against, which would make
every difference it reports uninterpretable; a basis set edited after the fact,
which would let the most convenient comparator be presented as the only one
tried; and a placebo that is not a placebo, which is the only control separating
"the basis can express the exposure" from "the basis has more columns".
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from portfolio_edge.experiments.exp_013_us_products_union_frame import (
    ReplicationResult,
    UnionOutcome,
)
from portfolio_edge.experiments.exp_014_replication_basis import (
    CAVEAT_TABLE,
    CONTROL_BASIS_ID,
    BasisScore,
    BasisVariationError,
    declared_bases,
    default_specification_path,
    exp_013_is_unmodified,
    frozen_basis_fixture,
    reproduction_differences,
)
from portfolio_edge.experiments.specification import (
    JsonValue,
    Specification,
    load_specification,
    specification_from_mapping,
)

SPEC_DIR = Path(__file__).resolve().parents[2] / "experiments"


def _spec(name: str) -> Specification:
    return load_specification(SPEC_DIR / f"{name}.yaml")


def _as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def _as_sequence(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(default_specification_path())


# --------------------------------------------------------------------------- #
# The baseline this experiment measures against may not move silently
# --------------------------------------------------------------------------- #


def test_the_frozen_hashes_still_describe_the_files_on_disk(
    specification: Specification,
) -> None:
    """The whole experiment is a difference against Experiment 013. If Experiment
    002 or Experiment 013 has been edited, that difference measures the edit."""
    assert exp_013_is_unmodified(specification)["parameters_asserted_against_exp_013"] is True


def test_the_guard_fires_when_a_frozen_hash_no_longer_matches(
    specification: Specification,
) -> None:
    raw = json.loads(json.dumps(specification.canonical_form()))
    del raw["schema_version"]
    universe = raw["universe"]
    universe["frozen_inputs"]["exp_013_universe_sha256"] = "0" * 64
    edited = specification_from_mapping(raw)
    with pytest.raises(BasisVariationError, match="exp_013_universe_sha256 has changed"):
        exp_013_is_unmodified(edited)


def test_the_guard_fires_when_a_shared_parameter_is_edited(
    specification: Specification,
) -> None:
    raw = json.loads(json.dumps(specification.canonical_form()))
    del raw["schema_version"]
    raw["parameters"]["minimum_intended_loading"] = 0.20
    edited = specification_from_mapping(raw)
    with pytest.raises(BasisVariationError, match="minimum_intended_loading"):
        exp_013_is_unmodified(edited)


def test_every_shared_parameter_is_experiment_013s(specification: Specification) -> None:
    theirs = _as_mapping(_spec("exp_013_us_products_union_frame").parameters)
    ours = _as_mapping(specification.parameters)
    for key in (
        "minimum_intended_loading",
        "materiality_threshold_annual_percent",
        "hac_lags",
        "minimum_monthly_observations",
        "power_target",
        "rolling_window_months",
        "cash_series",
    ):
        assert ours[key] == theirs[key], key
    exp_013 = _spec("exp_013_us_products_union_frame")
    assert specification.seed == exp_013.seed == 20260812
    assert specification.inference.resamples == exp_013.inference.resamples == 10_000
    assert specification.sample_policy.start == exp_013.sample_policy.start == "2020-01"
    assert specification.sample_policy.end == exp_013.sample_policy.end == "2025-12"


def test_the_comparator_is_experiment_013s_and_is_not_a_variable(
    specification: Specification,
) -> None:
    ours = _as_mapping(
        _as_mapping(_as_mapping(specification.universe)["comparators"])["broad_market"]
    )
    theirs = _as_mapping(
        _as_mapping(
            _as_mapping(_spec("exp_013_us_products_union_frame").universe)["comparators"]
        )["broad_market"]
    )
    assert ours["ticker"] == theirs["ticker"] == "VTI"


def test_the_experiment_never_rebuilds_a_universe(specification: Specification) -> None:
    """A rebuilt universe would be a second variable and this experiment has one."""
    module = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "portfolio_edge"
        / "experiments"
        / "exp_014_replication_basis.py"
    ).read_text(encoding="utf-8")
    assert "write_universe" not in module
    assert "build_universe" not in module
    assert _as_mapping(specification.universe)["inherited_from"] == (
        "exp_013_us_products_union_frame"
    )


# --------------------------------------------------------------------------- #
# The bases were declared before any of them was scored
# --------------------------------------------------------------------------- #


def test_the_control_is_first_and_is_experiment_002s_basis(
    specification: Specification,
) -> None:
    bases = declared_bases(specification)
    assert bases[0].id == CONTROL_BASIS_ID
    assert bases[0].tickers == ("VTI", "VUG", "VTV", "VB")
    theirs = _as_mapping(
        _as_mapping(
            _as_mapping(_spec("exp_013_us_products_union_frame").universe)["comparators"]
        )["synthetic_combination"]
    )
    assert list(bases[0].tickers) == [str(value) for value in _as_sequence(theirs["basis"])]


def test_more_than_one_basis_is_declared_and_all_are_reported(
    specification: Specification,
) -> None:
    """Six bases, frozen in one file before any was scored. The point of freezing
    them is that the count of comparators tried cannot be revised downwards after
    seeing which one flatters the conclusion."""
    bases = declared_bases(specification)
    assert len(bases) >= 3
    assert len({basis.id for basis in bases}) == len(bases)
    for requirement in _as_sequence(specification.reporting_requirements):
        assert isinstance(requirement, str)
    assert any(
        "placebo" in str(requirement) for requirement in specification.reporting_requirements
    )


def test_a_basis_may_not_repeat_a_ticker(specification: Specification) -> None:
    raw = json.loads(json.dumps(specification.canonical_form()))
    del raw["schema_version"]
    raw["universe"]["comparators"]["bases"][1]["tickers"].append("VTI")
    with pytest.raises(BasisVariationError, match="repeats a ticker"):
        declared_bases(specification_from_mapping(raw))


def test_the_expressive_bases_add_small_value_which_is_the_flagged_defect(
    specification: Specification,
) -> None:
    bases = {basis.id: basis for basis in declared_bases(specification)}
    assert "VBR" not in bases[CONTROL_BASIS_ID].tickers
    for name in ("B_plus_small_value", "C_style_grid", "D_expressive"):
        assert "VBR" in bases[name].tickers, name
    assert "small value" in bases["B_plus_small_value"].cells
    # The minimal change is exactly one fund, so anything it moves is that fund.
    assert set(bases["B_plus_small_value"].tickers) - set(bases[CONTROL_BASIS_ID].tickers) == {
        "VBR"
    }


def test_the_maximally_expressive_basis_spans_the_five_declared_dimensions(
    specification: Specification,
) -> None:
    cells = set(declared_bases(specification)[3].cells)
    assert "total market" in cells
    assert {"small blend", "mid blend"} <= cells  # size
    assert {"large value", "mid value", "small value"} <= cells
    assert {"large growth", "mid growth", "small growth"} <= cells
    assert "profitability" in cells


# --------------------------------------------------------------------------- #
# The placebos, which are the only control on column count
# --------------------------------------------------------------------------- #


def test_each_placebo_has_as_many_columns_as_the_most_expressive_basis(
    specification: Specification,
) -> None:
    bases = declared_bases(specification)
    widest_expressive = max(
        len(basis.tickers) for basis in bases if "placebo" not in basis.role
    )
    placebos = [basis for basis in bases if "placebo" in basis.role]
    assert placebos, "the experiment is uninterpretable without a placebo"
    for placebo in placebos:
        assert len(placebo.tickers) == widest_expressive, placebo.id


def test_no_placebo_adds_a_cell_the_control_does_not_already_carry(
    specification: Specification,
) -> None:
    """This is what makes a placebo a placebo. If it added a cell it would be a
    second expressive basis wearing a control's label."""
    bases = {basis.id: basis for basis in declared_bases(specification)}
    control_cells = set(bases[CONTROL_BASIS_ID].cells)
    for basis in bases.values():
        if "placebo" not in basis.role:
            continue
        assert set(basis.cells) == control_cells, basis.id


def test_every_basis_constituent_has_a_committed_fee_and_a_declared_cell(
    specification: Specification,
) -> None:
    comparators = _as_mapping(_as_mapping(specification.universe)["comparators"])
    facts = _as_mapping(comparators["basis_constituent_facts"])
    declared = {
        str(_as_mapping(item)["ticker"]): _as_mapping(item)
        for item in _as_sequence(facts["constituents"])
    }
    used = {ticker for basis in declared_bases(specification) for ticker in basis.tickers}
    assert used == set(declared), used.symmetric_difference(set(declared))
    for ticker, block in declared.items():
        fee = block["fee_percent"]
        assert isinstance(fee, float | int) and 0.0 < float(fee) <= 0.60, ticker
        assert str(block["cell"]).strip()
        assert str(block["index"]).strip()


# --------------------------------------------------------------------------- #
# The control must reproduce Experiment 013 exactly, and the check must be able
# to fail
# --------------------------------------------------------------------------- #


def test_the_committed_fixture_is_experiment_013s_published_shelf() -> None:
    fixture = frozen_basis_fixture()
    funds = fixture["funds"]
    assert isinstance(funds, Mapping)
    assert len(funds) == 109
    assert fixture["basis"] == ["VTI", "VUG", "VTV", "VB"]
    assert fixture["status_counts"] == {"exploratory": 48, "rejected": 48, "unresolved": 13}
    assert fixture["source_spec_hash"] == (
        "79f4e7628a3aadf9aa4f6c8c6c32c59ff4e0144982e8063c01e55058f325c3ca"
    )
    for ticker in CAVEAT_TABLE:
        assert ticker in funds, ticker


def _replication(ticker: str, shortfall: float) -> ReplicationResult:
    return ReplicationResult(
        ticker=ticker,
        basis=("VTI", "VB"),
        weights=(0.25, 0.75),
        months=72,
        tracking_difference_vs_combination=-shortfall,
        tracking_error_vs_combination=4.0,
        tracking_difference_vs_market=1.0,
        tracking_error_vs_market=5.0,
        fee_premium_over_basis=0.0,
        implementation_shortfall=shortfall,
    )


def _outcome(ticker: str, status: str) -> UnionOutcome:
    return UnionOutcome(
        ticker=ticker,
        series_name=ticker,
        mandate="value",
        intended_factor="HML",
        intended_sign=1,
        months=72,
        first_month="2020-01",
        last_month="2025-12",
        visible_to_exp_002_frame=True,
        in_exp_002_audit=True,
        status=status,
    )


def _tiny_fixture() -> dict[str, JsonValue]:
    return {
        "source_run_id": "test",
        "source_spec_hash": "test",
        "funds": {
            "AAA": {
                "implementation_shortfall_pp": 1.0,
                "tracking_difference_vs_combination_pp": -1.0,
                "weights": [0.25, 0.75],
                "status": "rejected",
            }
        },
    }


def test_the_reproduction_check_passes_on_an_exact_match() -> None:
    report = reproduction_differences(
        {"AAA": _replication("AAA", 1.0)},
        {"AAA": _outcome("AAA", "rejected")},
        fixture=_tiny_fixture(),
    )
    assert report["reproduced_to_zero_difference"] is True
    assert float(str(report["largest_absolute_shortfall_difference_pp"])) == 0.0


def test_the_reproduction_check_fails_on_the_smallest_possible_difference() -> None:
    """The tolerance is zero on purpose. The same functions run over the same
    bytes, so a difference of 1e-12 is a defect and not a rounding artefact."""
    report = reproduction_differences(
        {"AAA": _replication("AAA", 1.0 + 1e-12)},
        {"AAA": _outcome("AAA", "rejected")},
        fixture=_tiny_fixture(),
    )
    assert report["reproduced_to_zero_difference"] is False
    assert float(str(report["largest_absolute_shortfall_difference_pp"])) > 0.0


def test_the_reproduction_check_fails_on_a_changed_status() -> None:
    report = reproduction_differences(
        {"AAA": _replication("AAA", 1.0)},
        {"AAA": _outcome("AAA", "exploratory")},
        fixture=_tiny_fixture(),
    )
    assert report["reproduced_to_zero_difference"] is False
    assert report["status_changes"] == ["AAA: rejected -> exploratory"]


def test_the_reproduction_check_notices_a_missing_fund() -> None:
    report = reproduction_differences({}, {}, fixture=_tiny_fixture())
    assert report["reproduced_to_zero_difference"] is False
    assert report["funds_in_fixture_absent_here"] == ["AAA"]


# --------------------------------------------------------------------------- #
# A fund is never in its own basis, and the set that affects grows with the basis
# --------------------------------------------------------------------------- #


def test_a_fund_inside_its_own_basis_is_recorded_as_degenerate(
    specification: Specification,
) -> None:
    """For such a fund the 'implementation shortfall' is the realised style return
    of the window, not an implementation cost, and the set of them changes with
    the basis -- so a status change on one is a change in what is measured."""
    control = declared_bases(specification)[0]
    score = BasisScore(
        declaration=control,
        replications={
            "VB": _replication("VB", 2.89),
            "AVUV": _replication("AVUV", -4.92),
        },
        outcomes={"VB": _outcome("VB", "rejected"), "AVUV": _outcome("AVUV", "exploratory")},
    )
    assert score.degenerate() == ["VB"]


def test_the_degenerate_set_grows_with_the_basis(specification: Specification) -> None:
    bases = {basis.id: basis for basis in declared_bases(specification)}
    audited = set(frozen_basis_fixture()["funds"])  # type: ignore[arg-type]
    control_degenerate = audited & set(bases[CONTROL_BASIS_ID].tickers)
    for name in ("B_plus_small_value", "C_style_grid", "D_expressive"):
        assert control_degenerate < audited & set(bases[name].tickers), name


# --------------------------------------------------------------------------- #
# What the experiment is not allowed to claim
# --------------------------------------------------------------------------- #


def test_the_specification_says_which_direction_a_richer_basis_cuts(
    specification: Specification,
) -> None:
    block = _as_mapping(_as_mapping(specification.parameters)["look_ahead_direction"])
    assert "HARDER test" in str(block["statement"])
    assert "in sample" in str(block["statement"])
    assert str(block["asymmetry"]).strip()


def test_nothing_may_be_promoted_under_any_basis(specification: Specification) -> None:
    assert "0002" in str(specification.notes)
    assert "exploratory" in str(specification.rejection_rule)
    assert specification.run_kind.value == "exploratory"
    assert specification.consumes_final_holdout is False


def test_the_prior_look_at_these_numbers_is_declared(specification: Specification) -> None:
    """A scratch script computed four of these bases before the specification was
    frozen. The effective number of looks cannot be reconstructed afterwards, so
    it is on the record rather than in nobody's memory."""
    block = _as_mapping(_as_mapping(specification.parameters)["prior_exploration"])
    assert block["declared_before_this_run"] is True
    assert "cannot be reconstructed" in str(block["statement"])
