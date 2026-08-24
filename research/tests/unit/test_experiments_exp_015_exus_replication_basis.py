"""Experiment 015 varies the ex-US replicating basis and nothing else.

Every test here exists to make one of four things impossible: a silent drift in
the baseline this experiment measures a difference against, which would make
every difference it reports uninterpretable; a basis set edited after the fact,
which would let the most convenient comparator be presented as the only one
tried; a placebo that is not a placebo, which is the only control separating
"the basis can express the exposure" from "the basis has more columns"; and a
basis-invariant quantity recomputed per basis, which would mean the experiment
is no longer varying one thing.

The fourth is specific to the ex-US shelf and is new here: coverage is frozen in
the specification rather than discovered, because Experiment 009 drops a basis
constituent that does not cover a fund's months, and on this shelf that decides
two of the five clause (c) rejections.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from portfolio_edge.experiments.exp_009_exus_products import ExUsOutcome, ReplicationResult
from portfolio_edge.experiments.exp_009_universe import load_product_facts
from portfolio_edge.experiments.exp_015_exus_replication_basis import (
    CLAUSE_C_TABLE,
    CONTROL_BASIS_ID,
    COVERAGE_DIAGNOSTIC_FIRST_MONTH,
    COVERAGE_DIAGNOSTIC_FUNDS,
    EMERGING_PRODUCTS,
    BasisScore,
    ExUsBasisVariationError,
    _assert_declared_coverage,
    _pairings,
    _score_basis,
    declared_bases,
    declared_coverage,
    default_specification_path,
    exp_009_is_unmodified,
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
    """The whole experiment is a difference against Experiment 009. If Experiment
    002 or Experiment 009 has been edited, that difference measures the edit."""
    assert exp_009_is_unmodified(specification)["parameters_asserted_against_exp_009"] is True


def test_the_guard_fires_when_a_frozen_hash_no_longer_matches(
    specification: Specification,
) -> None:
    raw = json.loads(json.dumps(specification.canonical_form()))
    del raw["schema_version"]
    raw["universe"]["frozen_inputs"]["exp_009_universe_sha256"] = "0" * 64
    with pytest.raises(ExUsBasisVariationError, match="exp_009_universe_sha256 has changed"):
        exp_009_is_unmodified(specification_from_mapping(raw))


def test_the_guard_fires_when_the_committed_product_facts_move(
    specification: Specification,
) -> None:
    """Every basis constituent's FEE is read from that file, so an edit there
    would change a clause (c) figure without changing a single ticker."""
    raw = json.loads(json.dumps(specification.canonical_form()))
    del raw["schema_version"]
    raw["universe"]["frozen_inputs"]["exp_009_product_facts_sha256"] = "0" * 64
    with pytest.raises(
        ExUsBasisVariationError, match="exp_009_product_facts_sha256 has changed"
    ):
        exp_009_is_unmodified(specification_from_mapping(raw))


def test_the_guard_fires_when_a_shared_parameter_is_edited(
    specification: Specification,
) -> None:
    raw = json.loads(json.dumps(specification.canonical_form()))
    del raw["schema_version"]
    raw["parameters"]["minimum_intended_loading"] = 0.20
    with pytest.raises(ExUsBasisVariationError, match="minimum_intended_loading"):
        exp_009_is_unmodified(specification_from_mapping(raw))


def test_every_shared_parameter_and_era_is_experiment_009s(
    specification: Specification,
) -> None:
    exp_009 = _spec("exp_009_exus_factor_products")
    theirs = _as_mapping(exp_009.parameters)
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
    assert specification.seed == exp_009.seed == 20260812
    assert specification.inference.resamples == exp_009.inference.resamples == 10_000
    assert specification.sample_policy.start == exp_009.sample_policy.start == "2019-07"
    assert specification.sample_policy.end == exp_009.sample_policy.end == "2025-12"
    assert {(era.name, era.start, era.end) for era in specification.sample_policy.eras} == {
        (era.name, era.start, era.end) for era in exp_009.sample_policy.eras
    }


def test_the_comparators_are_experiment_009s_and_are_not_variables(
    specification: Specification,
) -> None:
    ours = _as_mapping(_as_mapping(specification.universe)["comparators"])
    theirs = _as_mapping(
        _as_mapping(_spec("exp_009_exus_factor_products").universe)["comparators"]
    )
    for key, other in (
        ("developed_ex_us_market", "developed_ex_us_market"),
        ("emerging_market", "emerging_market"),
        ("us_pedestal", "us_pedestal"),
    ):
        assert _as_mapping(ours[key])["ticker"] == _as_mapping(theirs[other])["ticker"]


def test_the_experiment_never_rebuilds_a_universe(specification: Specification) -> None:
    """A rebuilt universe would be a second variable and this experiment has one."""
    module = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "portfolio_edge"
        / "experiments"
        / "exp_015_exus_replication_basis.py"
    ).read_text(encoding="utf-8")
    assert "write_universe" not in module
    assert "build_universe" not in module
    assert _as_mapping(specification.universe)["inherited_from"] == (
        "exp_009_exus_factor_products"
    )


# --------------------------------------------------------------------------- #
# The bases were declared before any of them was scored
# --------------------------------------------------------------------------- #


def test_the_control_is_first_and_is_experiment_009s_basis(
    specification: Specification,
) -> None:
    bases = declared_bases(specification)
    assert bases[0].id == CONTROL_BASIS_ID
    assert bases[0].tickers == ("VEA", "VWO", "VSS", "EFV", "EFG")
    theirs = _as_mapping(
        _as_mapping(
            _as_mapping(_spec("exp_009_exus_factor_products").universe)["comparators"]
        )["synthetic_combination"]
    )
    assert list(bases[0].tickers) == [str(value) for value in _as_sequence(theirs["basis"])]


def test_more_than_one_basis_is_declared_and_all_are_reported(
    specification: Specification,
) -> None:
    bases = declared_bases(specification)
    assert len(bases) >= 5
    assert len({basis.id for basis in bases}) == len(bases)
    assert any(
        "placebo" in str(requirement) for requirement in specification.reporting_requirements
    )


def test_a_basis_may_not_repeat_a_ticker(specification: Specification) -> None:
    raw = json.loads(json.dumps(specification.canonical_form()))
    del raw["schema_version"]
    raw["universe"]["comparators"]["bases"][1]["tickers"].append("VEA")
    with pytest.raises(ExUsBasisVariationError, match="repeats a ticker"):
        declared_bases(specification_from_mapping(raw))


def test_the_expressive_bases_add_the_cells_the_frozen_basis_cannot_express(
    specification: Specification,
) -> None:
    bases = {basis.id: basis for basis in declared_bases(specification)}
    control = bases[CONTROL_BASIS_ID]
    assert "AVDV" not in control.tickers
    assert set(bases["B_plus_developed_small_value"].tickers) - set(control.tickers) == {
        "AVDV"
    }
    assert "developed ex-US small value" in bases["B_plus_developed_small_value"].cells
    # The frozen basis carries ONE emerging fund for a whole asset class.
    assert sum(1 for cell in control.cells if cell.startswith("emerging")) == 1
    assert sum(
        1 for cell in bases["C_plus_emerging_blocks"].cells if cell.startswith("emerging")
    ) == 3


def test_the_maximally_expressive_basis_spans_every_region_by_style_cell(
    specification: Specification,
) -> None:
    cells = set(
        {basis.id: basis for basis in declared_bases(specification)}[
            "D_expressive_ex_us"
        ].cells
    )
    assert {
        "developed ex-US market",
        "developed ex-US large value",
        "developed ex-US large growth",
        "developed ex-US small value",
        "developed ex-US quality",
        "developed ex-US momentum",
        "ex-US small blend",
        "emerging market",
        "emerging small blend",
        "emerging multifactor tilt",
    } == cells


# --------------------------------------------------------------------------- #
# The placebos, which are the only control on column count
# --------------------------------------------------------------------------- #


def test_every_expressive_basis_has_a_column_count_matched_placebo(
    specification: Specification,
) -> None:
    """Decision 0003's obligation, made structural. Experiment 014 matched one
    placebo to its widest basis; here every expressive basis has its own."""
    bases = declared_bases(specification)
    placebo_widths = [len(basis.tickers) for basis in bases if basis.is_placebo]
    assert placebo_widths, "the experiment is uninterpretable without a placebo"
    for basis in bases[1:]:
        if basis.is_placebo:
            continue
        assert len(basis.tickers) in placebo_widths, basis.id


def test_no_placebo_adds_a_cell_the_control_does_not_already_carry(
    specification: Specification,
) -> None:
    """This is what makes a placebo a placebo. If it added a cell it would be a
    second expressive basis wearing a control's label."""
    bases = {basis.id: basis for basis in declared_bases(specification)}
    control_cells = set(bases[CONTROL_BASIS_ID].cells)
    placebos = [basis for basis in bases.values() if basis.is_placebo]
    assert placebos
    for basis in placebos:
        assert set(basis.cells) == control_cells, basis.id
        assert len(basis.tickers) > len(bases[CONTROL_BASIS_ID].tickers), basis.id


def test_the_pairing_of_a_placebo_to_its_partner_is_derived_from_column_count() -> None:
    """Derived rather than restated, so a placebo cannot drift away from the
    partner it is supposed to bound."""

    def _score(name: str, role: str, count: int) -> BasisScore:
        return BasisScore(
            declaration=declared_bases(
                load_specification(default_specification_path())
            )[0].__class__(
                id=name,
                role=role,
                tickers=tuple(f"T{i}" for i in range(count)),
                cells=("x",),
                why="test",
            ),
            replications={},
            outcomes={},
        )

    scores = [
        _score("A_frozen", "control", 2),
        _score("B", "expressive", 3),
        _score("B_placebo", "placebo", 3),
    ]
    assert _pairings(scores) == {"B": "B_placebo"}


def test_every_basis_constituent_has_a_committed_fee_matching_the_facts_file(
    specification: Specification,
) -> None:
    """The fee is not restated here, it is checked against Experiment 009's own
    committed product facts, whose sha256 this experiment freezes."""
    comparators = _as_mapping(_as_mapping(specification.universe)["comparators"])
    facts_block = _as_mapping(comparators["basis_constituent_facts"])
    declared = {
        str(_as_mapping(item)["ticker"]): _as_mapping(item)
        for item in _as_sequence(facts_block["constituents"])
    }
    used = {ticker for basis in declared_bases(specification) for ticker in basis.tickers}
    assert used == set(declared), used.symmetric_difference(set(declared))
    committed = load_product_facts()
    for ticker, block in declared.items():
        fee = block["fee_percent"]
        assert isinstance(fee, float | int)
        assert committed[ticker].net_expense_ratio_percent == pytest.approx(float(fee)), ticker
        assert str(block["cell"]).strip()
        assert str(block["index"]).strip()


def test_the_one_constituent_above_the_graded_expense_cap_is_declared(
    specification: Specification,
) -> None:
    """EWX at 0.65% is dearer than the 0.60% cap this audit applies to GRADED
    products. It is the only emerging small-cap fund with a usable window, so it
    is admitted as a building block -- and that has to be said out loud rather
    than noticed by a reader adding up the fees."""
    comparators = _as_mapping(_as_mapping(specification.universe)["comparators"])
    bases = {basis.id: basis for basis in declared_bases(specification)}
    assert "EWX" in bases["C_plus_emerging_blocks"].tickers
    assert "0.60%" in bases["C_plus_emerging_blocks"].why
    assert "building block" in bases["C_plus_emerging_blocks"].why
    facts_block = _as_mapping(comparators["basis_constituent_facts"])
    fees = {
        str(_as_mapping(item)["ticker"]): float(str(_as_mapping(item)["fee_percent"]))
        for item in _as_sequence(facts_block["constituents"])
    }
    assert [ticker for ticker, fee in fees.items() if fee > 0.60] == ["EWX"]


# --------------------------------------------------------------------------- #
# Coverage is frozen, not discovered
# --------------------------------------------------------------------------- #


def test_every_constituent_has_a_frozen_first_month_of_coverage(
    specification: Specification,
) -> None:
    declared = declared_coverage(specification)
    used = {ticker for basis in declared_bases(specification) for ticker in basis.tickers}
    assert used <= set(declared)
    # Only these three carry a 2019-07 filing, which is why GWX and RODM see a
    # reduced basis under every basis in the experiment.
    assert {ticker for ticker, month in declared.items() if month == "2019-07"} == {
        "VEA",
        "EWX",
        "MFEM",
    }


def test_the_coverage_assertion_fails_when_the_filings_disagree(
    specification: Specification,
) -> None:
    class _Series:
        def __init__(self, first: str) -> None:
            self.periods = (first,)

    good = {
        ticker: _Series(month) for ticker, month in declared_coverage(specification).items()
    }
    assert _assert_declared_coverage(specification, good)["agree"] is True  # type: ignore[arg-type]
    bad = dict(good)
    bad["VEA"] = _Series("2019-08")
    with pytest.raises(ExUsBasisVariationError, match="filings begin 2019-08"):
        _assert_declared_coverage(specification, bad)  # type: ignore[arg-type]


def test_the_coverage_diagnostic_is_declared_and_is_not_a_verdict(
    specification: Specification,
) -> None:
    block = _as_mapping(_as_mapping(specification.parameters)["coverage_versus_span"])
    assert "SECOND-VARIABLE DIAGNOSTIC" in str(block["diagnostic"])
    assert "cannot produce a status" in str(block["diagnostic"])
    assert COVERAGE_DIAGNOSTIC_FUNDS == ("GWX", "RODM")
    assert COVERAGE_DIAGNOSTIC_FIRST_MONTH == "2019-08"


# --------------------------------------------------------------------------- #
# The basis-invariant quantities are computed once and reused
# --------------------------------------------------------------------------- #


def test_scoring_a_basis_never_recomputes_a_basis_invariant_quantity() -> None:
    """If a loading, an alpha, an interval or a pedestal were recomputed per
    basis they could differ between bases, and the experiment would no longer be
    varying one thing. They are computed once and passed in."""
    source = inspect.getsource(_score_basis)
    for forbidden in (
        "_fit_all_specifications",
        "_fit_on",
        "_bootstrap_interval",
        "_pedestal",
        "load_regional_panel",
    ):
        assert forbidden not in source, forbidden
    parameters = inspect.signature(_score_basis).parameters
    for required in ("all_fits", "half_fits", "intervals"):
        assert required in parameters, required


# --------------------------------------------------------------------------- #
# The control must reproduce Experiment 009 exactly, and the check must be able
# to fail
# --------------------------------------------------------------------------- #


def test_the_committed_fixture_is_experiment_009s_published_shelf() -> None:
    fixture = frozen_basis_fixture()
    funds = fixture["funds"]
    assert isinstance(funds, Mapping)
    assert len(funds) == 25
    assert fixture["basis"] == ["VEA", "VWO", "VSS", "EFV", "EFG"]
    assert fixture["status_counts"] == {"exploratory": 12, "rejected": 8, "unresolved": 5}
    assert fixture["source_spec_hash"] == (
        "e99e2a6e27fbf301a351ed7863820a3f5fb56e99a7183f30321444721d899687"
    )
    for ticker in (*CLAUSE_C_TABLE, *EMERGING_PRODUCTS):
        assert ticker in funds, ticker
    # MFEM has no replication under ANY basis: Experiment 009 requires the
    # region's comparator to cover the window and VWO does not cover its first
    # month. That is recorded, not silently dropped.
    assert isinstance(funds["MFEM"], Mapping)
    assert funds["MFEM"]["replication_fitted"] is False


def _replication(ticker: str, shortfall: float) -> ReplicationResult:
    return ReplicationResult(
        ticker=ticker,
        basis=("VEA", "VSS"),
        weights=(0.25, 0.75),
        months=77,
        tracking_difference_vs_combination=-shortfall,
        tracking_error_vs_combination=4.0,
        tracking_difference_vs_regional_market=1.0,
        tracking_error_vs_regional_market=5.0,
        tracking_difference_vs_french_market=1.0,
        fee_premium_over_basis=0.0,
        implementation_shortfall=shortfall,
    )


def _outcome(ticker: str, status: str) -> ExUsOutcome:
    return ExUsOutcome(
        ticker=ticker,
        series_name=ticker,
        region="developed_ex_us",
        mandate="value",
        intended_factor="HML",
        intended_sign=1,
        months=77,
        first_month="2019-08",
        last_month="2025-12",
        status=status,
    )


def _tiny_fixture(*, fitted: bool = True) -> dict[str, JsonValue]:
    return {
        "source_run_id": "test",
        "source_spec_hash": "test",
        "funds": {
            "AAA": {
                "replication_fitted": fitted,
                "implementation_shortfall_pp": 1.0,
                "tracking_difference_vs_combination_pp": -1.0,
                "basis_used": ["VEA", "VSS"],
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


def test_the_reproduction_check_fails_when_a_basis_column_set_moves() -> None:
    """A fund whose basis lost or gained a column is not the same comparison,
    even when the shortfall happens to agree."""
    moved = replace(_replication("AAA", 1.0), basis=("VEA",), weights=(1.0,))
    report = reproduction_differences(
        {"AAA": moved},
        {"AAA": _outcome("AAA", "rejected")},
        fixture=_tiny_fixture(),
    )
    assert report["reproduced_to_zero_difference"] is False


def test_the_reproduction_check_fails_when_a_replication_appears_or_vanishes() -> None:
    report = reproduction_differences(
        {}, {"AAA": _outcome("AAA", "rejected")}, fixture=_tiny_fixture()
    )
    assert report["reproduced_to_zero_difference"] is False
    assert report["replication_presence_changes"] == ["AAA"]


def test_the_reproduction_check_notices_a_missing_fund() -> None:
    report = reproduction_differences({}, {}, fixture=_tiny_fixture())
    assert report["reproduced_to_zero_difference"] is False
    assert report["funds_in_fixture_absent_here"] == ["AAA"]


# --------------------------------------------------------------------------- #
# A fund is never in its own basis, and coverage is not span
# --------------------------------------------------------------------------- #


def test_a_fund_inside_its_own_basis_is_recorded_as_degenerate(
    specification: Specification,
) -> None:
    """For such a fund the 'implementation shortfall' is the realised style return
    of the window, not an implementation cost."""
    control = declared_bases(specification)[0]
    score = BasisScore(
        declaration=control,
        replications={"EFV": _replication("EFV", -1.19), "GWX": _replication("GWX", 1.24)},
        outcomes={
            "EFV": _outcome("EFV", "exploratory"),
            "GWX": _outcome("GWX", "rejected"),
        },
    )
    assert score.degenerate() == ["EFV"]


def test_a_fund_whose_basis_lost_a_column_to_coverage_is_named(
    specification: Specification,
) -> None:
    """Span is what the basis can express; coverage is which columns were there
    at all. On this shelf the second decides GWX."""
    control = declared_bases(specification)[0]
    score = BasisScore(
        declaration=control,
        replications={
            "GWX": ReplicationResult(
                ticker="GWX",
                basis=("VEA",),
                weights=(1.0,),
                months=78,
                tracking_difference_vs_combination=-1.61,
                tracking_error_vs_combination=5.71,
                tracking_difference_vs_regional_market=0.0,
                tracking_error_vs_regional_market=0.0,
                tracking_difference_vs_french_market=0.0,
                fee_premium_over_basis=0.37,
                implementation_shortfall=1.24,
            )
        },
        outcomes={"GWX": _outcome("GWX", "rejected")},
    )
    assert score.reduced() == {"GWX": ["VWO", "VSS", "EFV", "EFG"]}


def test_the_degenerate_set_grows_with_the_basis(specification: Specification) -> None:
    bases = {basis.id: basis for basis in declared_bases(specification)}
    audited = set(frozen_basis_fixture()["funds"])  # type: ignore[arg-type]
    control_degenerate = audited & set(bases[CONTROL_BASIS_ID].tickers)
    assert control_degenerate == {"EFV", "EFG"}
    for name in ("B_plus_developed_small_value", "D_expressive_ex_us"):
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


def test_the_specification_names_the_panel_rule(specification: Specification) -> None:
    """Experiment 009's fifth conclusion: an ex-US loading without its panel named
    is not a number."""
    block = _as_mapping(_as_mapping(specification.parameters)["regional_panels"])
    assert "panel" in str(block["note"])
    assert "not a number" in str(block["note"])
    assert "OWN region" in str(_as_mapping(specification.benchmark)["factor_model"])


def test_the_specification_records_that_alpha_is_unmeasurable_here(
    specification: Specification,
) -> None:
    block = _as_mapping(_as_mapping(specification.parameters)["alpha_shrinkage"])
    assert "3.23" in str(block["transferred_not_measured"])
    assert "no alpha is a promotion criterion" in str(block["transferred_not_measured"])


def test_nothing_may_be_promoted_under_any_basis(specification: Specification) -> None:
    assert "0002" in str(specification.notes)
    assert "exploratory" in str(specification.rejection_rule)
    assert specification.run_kind.value == "exploratory"
    assert specification.consumes_final_holdout is False


def test_the_prior_look_at_these_numbers_is_declared(specification: Specification) -> None:
    block = _as_mapping(_as_mapping(specification.parameters)["prior_exploration"])
    assert block["declared_before_this_run"] is True
    assert "seven bases declared here" in str(block["statement"])
