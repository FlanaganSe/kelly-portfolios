"""Unit tests for Experiment 016, the construction tournament.

Every expected value in this file is computed **in this file**, with plain NumPy
or by hand, and never by calling the code under test. Where a quantity has a
canonical implementation elsewhere in the package -- equal risk contribution,
Benjamini-Hochberg -- the local implementation is pinned against it rather than
against itself.

The two tests that matter most are the look-ahead test on
:func:`walk_forward_weights`, because an estimated arm that sees its own future
is not a result, and the drift test on the simulator, because a constant-weight
simulation that silently rebalances monthly at no charge is not a portfolio
anyone holds.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.core.portfolio import (
    equal_risk_contribution_weights,
    minimum_variance_weights,
    relative_risk_contributions,
)
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MDE_MULTIPLIER,
    MONTHS_PER_YEAR,
    ArmOutcome,
    BasisPanel,
    ConstructionTournamentError,
    CostSettings,
    FundMapping,
    GapStatistics,
    MappingShift,
    _apply_falsifier,
    _break_even,
    _build_mappings,
    _cost_settings,
    _read_contestants,
    _unit_scaled,
    _verified_erc,
    annualised_log_growth,
    constant_weight_path,
    default_specification_path,
    fund_excess_matrix,
    gap_statistics,
    ledoit_wolf_constant_correlation,
    minimum_detectable_effect,
    parse_basis_expression,
    walk_forward_weights,
    years_to_distinguish,
)
from portfolio_edge.experiments.specification import Specification, load_specification
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices

SPEC_PATH = default_specification_path()


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(SPEC_PATH)


# --------------------------------------------------------------------------- #
# The mapping grammar
# --------------------------------------------------------------------------- #


def test_basis_expression_parses_signs_and_coefficients() -> None:
    parsed = parse_basis_expression(
        "1.072 * us_mkt + 0.322 * us_hml - 0.394 * us_cma", where="test"
    )
    assert parsed == {"us_mkt": 1.072, "us_hml": 0.322, "us_cma": -0.394}


def test_basis_expression_rejects_an_unknown_series() -> None:
    with pytest.raises(ConstructionTournamentError, match="does not hold"):
        parse_basis_expression("1.0 * not_a_series", where="test")


def test_basis_expression_rejects_a_repeated_series() -> None:
    """Two coefficients on one leg would silently keep only the second."""
    with pytest.raises(ConstructionTournamentError, match="appears twice"):
        parse_basis_expression("1.0 * us_mkt + 0.5 * us_mkt", where="test")


def test_basis_expression_rejects_prose() -> None:
    with pytest.raises(ConstructionTournamentError, match="could not parse"):
        parse_basis_expression("the US market", where="test")


# --------------------------------------------------------------------------- #
# A tiny hand-built panel
# --------------------------------------------------------------------------- #


def _panel(months: int = 240, seed: int = 11) -> BasisPanel:
    """A synthetic panel with every basis series the module knows about."""
    rng = np.random.default_rng(seed)
    names = (
        "us_mkt",
        "us_smb",
        "us_hml",
        "us_rmw",
        "us_cma",
        "us_umd",
        "dxus_mkt",
        "dxus_smb",
        "dxus_hml",
        "dxus_rmw",
        "dxus_cma",
        "dxus_umd",
        "em_mkt",
        "em_hml",
        "trend",
    )
    series = {
        name: np.asarray(rng.normal(0.004, 0.04, months), dtype=np.float64) for name in names
    }
    return BasisPanel(
        periods=tuple(f"{2000 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(months)),
        series=series,
        cash=np.full(months, 0.002, dtype=np.float64),
        provenance=(),
        findings=(),
    )


def _costs() -> CostSettings:
    return CostSettings(
        equity_futures_basis=0.0062,
        trend_book_financing=0.0,
        round_trip_spread={"us_equity": 0.55, "developed_ex_us_equity": 1.18},
    )


def _mapping(
    ticker: str,
    coefficients: Mapping[str, float],
    *,
    fee_bp: float = 0.0,
    futures: float = 0.0,
    alpha: float | None = None,
) -> FundMapping:
    return FundMapping(
        ticker=ticker,
        coefficients=dict(coefficients),
        expense_ratio_bp=fee_bp,
        futures_notional=futures,
        spread_region="us_equity",
        alpha_less_pedestal_pp_yr=alpha,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=False,
        fee_assumed=False,
    )


# --------------------------------------------------------------------------- #
# fund_excess_matrix
# --------------------------------------------------------------------------- #


def test_fund_excess_is_the_declared_combination_less_fee_and_financing() -> None:
    panel = _panel(60)
    costs = _costs()
    mappings = {"W": _mapping("W", {"us_mkt": 1.072, "trend": 1.0}, fee_bp=99, futures=0.331)}
    got = fund_excess_matrix(
        panel, mappings, costs, tickers=["W"], shift=MappingShift()
    )[:, 0]
    expected = (
        1.072 * panel.column("us_mkt")
        + 1.0 * panel.column("trend")
        - (99 / 10_000.0 + 0.0062 * 0.331) / 12.0
    )
    assert np.allclose(got, expected, rtol=0, atol=1e-15)


def test_loading_perturbation_moves_magnitudes_and_leaves_market_betas_alone() -> None:
    panel = _panel(24)
    mappings = {"F": _mapping("F", {"us_mkt": 1.0, "us_hml": 0.5, "us_cma": -0.4})}
    shifted = fund_excess_matrix(
        panel, mappings, _costs(), tickers=["F"], shift=MappingShift(loading_delta=0.15)
    )[:, 0]
    expected = (
        1.0 * panel.column("us_mkt")
        + 0.65 * panel.column("us_hml")
        - 0.55 * panel.column("us_cma")
    )
    assert np.allclose(shifted, expected, rtol=0, atol=1e-15)


def test_trend_multiplier_scales_only_the_trend_leg() -> None:
    panel = _panel(24)
    mappings = {"W": _mapping("W", {"us_mkt": 1.0, "trend": 1.0})}
    shifted = fund_excess_matrix(
        panel, mappings, _costs(), tickers=["W"], shift=MappingShift(trend_multiplier=0.8)
    )[:, 0]
    expected = panel.column("us_mkt") + 0.8 * panel.column("trend")
    assert np.allclose(shifted, expected, rtol=0, atol=1e-15)


def test_haircuts_are_charged_inside_the_leg_not_to_the_annual_figure() -> None:
    """A haircut must not change a volatility or a correlation, only a mean."""
    panel = _panel(120)
    mappings = {"W": _mapping("W", {"us_mkt": 1.0, "trend": 1.0})}
    plain = fund_excess_matrix(panel, mappings, _costs(), tickers=["W"], shift=MappingShift())
    cut = fund_excess_matrix(
        panel, mappings, _costs(), tickers=["W"], shift=MappingShift(trend_haircut_pp_yr=3.0)
    )
    assert np.isclose(float(np.mean(plain - cut)) * 1200.0, 3.0)
    assert np.isclose(float(np.std(plain, ddof=1)), float(np.std(cut, ddof=1)))


def test_measured_alpha_is_charged_only_where_one_was_measured() -> None:
    panel = _panel(24)
    mappings = {
        "HAS": _mapping("HAS", {"us_mkt": 1.0}, alpha=-3.80),
        "NONE": _mapping("NONE", {"us_mkt": 1.0}, alpha=None),
    }
    charged = fund_excess_matrix(
        panel,
        mappings,
        _costs(),
        tickers=["HAS", "NONE"],
        shift=MappingShift(charge_measured_alpha=True),
    )
    plain = fund_excess_matrix(
        panel, mappings, _costs(), tickers=["HAS", "NONE"], shift=MappingShift()
    )
    assert np.allclose((plain - charged)[:, 0] * 1200.0, 3.80)
    assert np.allclose((plain - charged)[:, 1], 0.0)


# --------------------------------------------------------------------------- #
# The simulator
# --------------------------------------------------------------------------- #


def test_a_single_holding_reproduces_its_own_funded_return() -> None:
    panel = _panel(36)
    costs = _costs()
    mappings = {"A": _mapping("A", {"us_mkt": 1.0}, fee_bp=25)}
    path = constant_weight_path(
        panel,
        mappings,
        costs,
        tickers=["A"],
        targets=np.array([1.0]),
    )
    expected = panel.cash + panel.column("us_mkt") - 0.0025 / 12.0
    # The very first month pays the entry trade; the rest do not.
    assert np.allclose(path.total[1:], expected[1:], rtol=0, atol=1e-15)
    assert path.gross_notional == pytest.approx(1.0)


def test_weights_drift_between_rebalances() -> None:
    """Two assets, one flat and one rising: the weight must move."""
    months = 24
    panel = BasisPanel(
        periods=tuple(f"{2000 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(months)),
        series={
            "us_mkt": np.full(months, 0.01, dtype=np.float64),
            "dxus_mkt": np.zeros(months, dtype=np.float64),
        },
        cash=np.zeros(months, dtype=np.float64),
        provenance=(),
        findings=(),
    )
    mappings = {
        "UP": _mapping("UP", {"us_mkt": 1.0}),
        "FLAT": _mapping("FLAT", {"dxus_mkt": 1.0}),
    }
    path = constant_weight_path(
        panel,
        mappings,
        _costs(),
        tickers=["UP", "FLAT"],
        targets=np.array([0.5, 0.5]),
        rebalance_every=months * 2,
    )
    # By hand: wealth in each leg compounds independently from 0.5.
    up, flat = 0.5, 0.5
    expected = []
    for _ in range(months):
        total = up + flat
        expected.append((up * 1.01 + flat) / total - 1.0)
        up, flat = up * 1.01, flat
    assert np.allclose(path.total, expected, rtol=0, atol=1e-14)
    # A monthly-rebalanced portfolio would have returned exactly 0.5% every month.
    assert path.total[-1] > 0.005


def test_leverage_is_charged_the_declared_financing_spread() -> None:
    months = 12
    panel = BasisPanel(
        periods=tuple(f"2000-{i + 1:02d}" for i in range(months)),
        series={"us_mkt": np.zeros(months, dtype=np.float64)},
        cash=np.zeros(months, dtype=np.float64),
        provenance=(),
        findings=(),
    )
    mappings = {"A": _mapping("A", {"us_mkt": 1.0})}
    path = constant_weight_path(
        panel, mappings, _costs(), tickers=["A"], targets=np.array([1.5])
    )
    # Zero returns everywhere, so the first month is 0.62% on 0.5 of notional.
    assert path.total[0] == pytest.approx(-0.0062 * 0.5 / 12.0)
    # And then leverage CREEPS UP, because the loss came out of equity while the
    # borrowing did not move. That is the property that makes leverage hard to
    # hold, and a weight-renormalising simulator hides it.
    assert path.total[1] < path.total[0]


def test_annualised_log_growth_matches_hand_arithmetic() -> None:
    returns = np.array([0.01, -0.02, 0.03, 0.00], dtype=np.float64)
    expected = float(np.mean(np.log1p(returns))) * 12.0 * 100.0
    assert annualised_log_growth(returns) == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Weighting methods
# --------------------------------------------------------------------------- #


def test_verified_erc_agrees_with_the_canonical_solver() -> None:
    rng = np.random.default_rng(3)
    for _ in range(6):
        sample = rng.normal(size=(300, 5))
        covariance = np.cov(sample, rowvar=False, ddof=1)
        canonical = equal_risk_contribution_weights(covariance)
        assert np.allclose(_verified_erc(covariance), canonical, rtol=0, atol=1e-10)


def test_verified_erc_actually_equalises_risk_contributions() -> None:
    rng = np.random.default_rng(4)
    covariance = np.cov(rng.normal(size=(400, 7)), rowvar=False, ddof=1)
    weights = _verified_erc(_unit_scaled(covariance))
    contributions = relative_risk_contributions(weights, covariance)
    assert float(np.max(contributions) - np.min(contributions)) < 1e-10
    assert np.isclose(float(np.sum(weights)), 1.0)


def test_unit_scaling_does_not_change_any_weighting_answer() -> None:
    """Every method here is scale-invariant; the scaling is conditioning only."""
    rng = np.random.default_rng(5)
    covariance = np.cov(rng.normal(size=(300, 6)) * 0.04, rowvar=False, ddof=1)
    assert np.allclose(
        minimum_variance_weights(covariance, long_only=True),
        minimum_variance_weights(_unit_scaled(covariance), long_only=True),
        atol=1e-8,
    )


def test_ledoit_wolf_shrinks_towards_constant_correlation() -> None:
    rng = np.random.default_rng(6)
    returns = rng.normal(size=(80, 6))
    shrunk, intensity = ledoit_wolf_constant_correlation(returns)
    assert 0.0 <= intensity <= 1.0
    centred = returns - returns.mean(axis=0, keepdims=True)
    sample = (centred.T @ centred) / returns.shape[0]
    sigmas = np.sqrt(np.diag(sample))
    correlations = sample / np.outer(sigmas, sigmas)
    off = ~np.eye(6, dtype=bool)
    target = float(correlations[off].mean()) * np.outer(sigmas, sigmas)
    np.fill_diagonal(target, np.diag(sample))
    # The shrunk matrix is on the segment between the two, at the reported intensity.
    assert np.allclose(shrunk, intensity * target + (1.0 - intensity) * sample)
    # Variances survive shrinkage exactly; only correlations move.
    assert np.allclose(np.diag(shrunk), np.diag(sample))
    assert np.all(np.linalg.eigvalsh(shrunk) > 0.0)


def test_shrinkage_pulls_harder_on_a_shorter_window() -> None:
    """The target must be wrong for the intensity to be informative.

    On independent columns the constant-correlation target IS the truth, so full
    shrinkage is correct at any length and the comparison says nothing. This
    draws from a factor structure with heterogeneous correlations, where the
    target is wrong, and then the sample-error argument bites as it should.
    """
    rng = np.random.default_rng(7)
    loadings = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.2], dtype=np.float64)
    factor = rng.normal(size=(2000, 1))
    idiosyncratic = rng.normal(size=(2000, 6)) * 0.5
    sample = factor @ loadings[None, :] + idiosyncratic
    _, weak = ledoit_wolf_constant_correlation(sample)
    _, strong = ledoit_wolf_constant_correlation(sample[:40])
    assert strong > weak


def test_walk_forward_weights_cannot_see_their_own_future() -> None:
    """Mutating month t must not change the target applied at month t."""
    rng = np.random.default_rng(8)
    excess = rng.normal(0.005, 0.04, size=(200, 4))
    base, first, _ = walk_forward_weights(
        excess, method="inverse_volatility", minimum_months=120, reapply_every=12
    )
    tampered = excess.copy()
    tampered[150:, :] *= 5.0
    after, _, _ = walk_forward_weights(
        tampered, method="inverse_volatility", minimum_months=120, reapply_every=12
    )
    assert first == 120
    assert np.allclose(base[:151, :], after[:151, :])
    assert not np.allclose(base[160, :], after[160, :])


def test_walk_forward_weights_are_held_for_the_declared_period() -> None:
    rng = np.random.default_rng(9)
    excess = rng.normal(0.005, 0.04, size=(160, 3))
    targets, first, _ = walk_forward_weights(
        excess, method="equal_weight", minimum_months=120, reapply_every=12
    )
    assert np.allclose(targets[first : first + 12], targets[first])
    assert np.allclose(targets[:first], 0.0)


def test_walk_forward_refuses_a_window_it_cannot_fill() -> None:
    with pytest.raises(ConstructionTournamentError, match="estimation window"):
        walk_forward_weights(
            np.zeros((100, 3)), method="equal_weight", minimum_months=120, reapply_every=12
        )


# --------------------------------------------------------------------------- #
# Inference
# --------------------------------------------------------------------------- #


def test_minimum_detectable_effect_is_the_frozen_formula() -> None:
    rng = np.random.default_rng(10)
    difference = rng.normal(0.0, 0.01, 427)
    expected = (
        MDE_MULTIPLIER
        * 100.0
        * MONTHS_PER_YEAR
        * float(np.std(difference, ddof=1))
        / math.sqrt(difference.size)
    )
    assert minimum_detectable_effect(difference) == pytest.approx(expected)


def test_the_two_mde_statements_in_the_specification_agree() -> None:
    """`2.8016 sigma / sqrt(years)` and `1200 sd / sqrt(T)` are the same number."""
    rng = np.random.default_rng(12)
    difference = rng.normal(0.0, 0.008, 360)
    annual_sigma = float(np.std(difference, ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0
    years = difference.size / MONTHS_PER_YEAR
    assert minimum_detectable_effect(difference) == pytest.approx(
        MDE_MULTIPLIER * annual_sigma / math.sqrt(years)
    )


def test_the_specification_mde_table_is_arithmetic_on_its_own_window(
    specification: Specification,
) -> None:
    """The table was written before the data was touched; check it adds up."""
    assert isinstance(specification.parameters, Mapping)
    block = specification.parameters["minimum_detectable_effect"]
    assert isinstance(block, Mapping)
    years = float(str(block["window_years"]))
    multiplier = float(str(block["multiplier"]))
    table = block["floor_at_assumed_tracking_error"]
    assert isinstance(table, Mapping)
    for tracking_error, floor in table.items():
        expected = multiplier * float(tracking_error) / math.sqrt(years)
        assert float(str(floor)) == pytest.approx(expected, abs=0.005)


def test_gap_statistics_reproduce_a_hand_computed_gap() -> None:
    rng = np.random.default_rng(13)
    arm = rng.normal(0.008, 0.04, 300)
    benchmark = rng.normal(0.006, 0.04, 300)
    indices = stationary_bootstrap_indices(300, 12.0, 500, np.random.default_rng(1))
    stats = gap_statistics(arm, benchmark, indices=indices, confidence=0.95)
    difference = np.log1p(arm) - np.log1p(benchmark)
    assert stats.gap_pp_yr == pytest.approx(float(np.mean(difference)) * 1200.0)
    assert stats.tracking_error_pct == pytest.approx(
        float(np.std(difference, ddof=1)) * math.sqrt(12) * 100.0
    )
    assert stats.interval[0] <= stats.gap_pp_yr <= stats.interval[1]
    assert 0.0 < stats.p_value <= 1.0


def test_gap_statistics_refuse_mismatched_windows() -> None:
    indices = stationary_bootstrap_indices(10, 4.0, 20, np.random.default_rng(1))
    with pytest.raises(ConstructionTournamentError, match="same months"):
        gap_statistics(np.zeros(10), np.zeros(9), indices=indices, confidence=0.95)


def test_years_to_distinguish_inverts_the_detection_floor() -> None:
    """At the returned horizon, the design's own floor equals the gap."""
    rng = np.random.default_rng(14)
    difference = rng.normal(0.0006, 0.006, 427)
    gap = float(np.mean(difference)) * 1200.0
    years = years_to_distinguish(gap, difference)
    annual_sigma = float(np.std(difference, ddof=1)) * math.sqrt(12) * 100.0
    assert MDE_MULTIPLIER * annual_sigma / math.sqrt(years) == pytest.approx(abs(gap))


def test_break_even_interpolates_the_crossing_exactly() -> None:
    # A gap falling by 0.5 per unit of haircut, crossing zero at 3.0.
    points = [(x, 1.5 - 0.5 * x) for x in (0.0, 1.0, 2.0, 3.0, 4.0)]
    assert _break_even(points) == pytest.approx(3.0)
    assert _break_even([(0.0, 1.0), (1.0, 0.5)]) is None


# --------------------------------------------------------------------------- #
# The falsifier
# --------------------------------------------------------------------------- #


def _outcome(**overrides: object) -> ArmOutcome:
    defaults: dict[str, object] = {
        "name": "arm",
        "role": "candidate",
        "benchmark": "control_capweight",
        "growth_pp_yr": 10.0,
        "volatility_pct": 15.0,
        "sharpe": 0.6,
        "max_drawdown_pct": -50.0,
        "time_under_water_months": 40,
        "gross_notional": 1.0,
        "weighted_fee_bp": 10.0,
        "annual_turnover_pct": 0.04,
        "n_funds": 5,
        "months": 427,
        "window": ("1990-11", "2026-05"),
    }
    defaults.update(overrides)
    return ArmOutcome(**defaults)  # type: ignore[arg-type]


def _stats(gap: float, mde: float) -> GapStatistics:
    return GapStatistics(
        gap_pp_yr=gap,
        interval=(gap - 1.0, gap + 1.0),
        mde_pp_yr=mde,
        mde_bootstrap_pp_yr=mde,
        p_value=0.01,
        tracking_error_pct=2.0,
        months=427,
        years_to_distinguish=10.0,
    )


def test_a_negative_gap_is_rejected_by_clause_a() -> None:
    outcome = _outcome()
    outcome.gap = _stats(-0.5, 0.4)
    outcome.adjusted_p = 0.01
    _apply_falsifier(outcome, q=0.10, sharpe_of_levered_control=0.1)
    assert outcome.status == "rejected" and outcome.clause.startswith("(a)")


def test_clause_b_does_not_reach_an_unlevered_arm() -> None:
    """An unlevered arm has no leverage to which a gain could be attributed."""
    outcome = _outcome(gross_notional=1.0, sharpe=0.4)
    outcome.gap = _stats(2.0, 0.5)
    outcome.adjusted_p = 0.01
    outcome.perturbation_range = (1.0, 3.0)
    _apply_falsifier(outcome, q=0.10, sharpe_of_levered_control=0.9)
    assert outcome.status == "exploratory"


def test_clause_b_rejects_a_levered_arm_the_levered_control_matches() -> None:
    outcome = _outcome(gross_notional=1.4, sharpe=0.4)
    outcome.gap = _stats(2.0, 0.5)
    outcome.adjusted_p = 0.01
    _apply_falsifier(outcome, q=0.10, sharpe_of_levered_control=0.9)
    assert outcome.status == "rejected" and outcome.clause.startswith("(b)")


def test_a_gap_inside_its_own_floor_is_unresolved_not_rejected() -> None:
    """Decision 0009 clause 1, enforced rather than remembered."""
    outcome = _outcome()
    outcome.gap = _stats(2.49, 3.33)
    outcome.adjusted_p = 0.01
    outcome.perturbation_range = (1.5, 3.5)
    _apply_falsifier(outcome, q=0.10, sharpe_of_levered_control=None)
    assert outcome.status == "unresolved"
    assert outcome.clause.startswith("(c)") and "3.33" in outcome.clause


def test_a_sign_change_on_the_perturbation_grid_is_unresolved() -> None:
    outcome = _outcome()
    outcome.gap = _stats(1.6, 1.3)
    outcome.adjusted_p = 0.02
    outcome.perturbation_range = (-0.4, 2.5)
    _apply_falsifier(outcome, q=0.10, sharpe_of_levered_control=None)
    assert outcome.status == "unresolved" and outcome.clause.startswith("(e)")


def test_a_surviving_arm_reaches_exploratory_and_no_further() -> None:
    outcome = _outcome()
    outcome.gap = _stats(1.6, 1.3)
    outcome.adjusted_p = 0.02
    outcome.perturbation_range = (1.2, 2.0)
    _apply_falsifier(outcome, q=0.10, sharpe_of_levered_control=None)
    assert outcome.status == "exploratory"


# --------------------------------------------------------------------------- #
# The committed specification
# --------------------------------------------------------------------------- #


def test_specification_path_is_committed() -> None:
    assert isinstance(SPEC_PATH, Path) and SPEC_PATH.is_file()


def test_every_contestant_resolves_to_a_declared_mapping(
    specification: Specification,
) -> None:
    mappings = _build_mappings(specification)
    for name, contestant in _read_contestants(specification).items():
        for ticker in contestant.tickers:
            assert ticker in mappings, f"{name} holds unmapped {ticker!r}"


def test_the_levered_control_matches_the_proposal_gross_notional(
    specification: Specification,
) -> None:
    """A leverage-matched control that is not matched is not a control."""
    mappings = _build_mappings(specification)
    contestants = _read_contestants(specification)
    proposal = contestants["proposal_rsst"]
    gross = sum(
        weight * mappings[ticker].gross_notional
        for ticker, weight in zip(proposal.tickers, proposal.weights, strict=True)
    )
    levered = contestants["control_capweight_levered"].capital_leverage
    assert gross == pytest.approx(levered, abs=5e-4)


def test_unlevered_arms_sum_to_one_and_levered_arms_say_so(
    specification: Specification,
) -> None:
    contestants = _read_contestants(specification)
    for name in ("control_capweight", "control_seventy_thirty_cash", "proposal_rsst"):
        assert contestants[name].capital_leverage == pytest.approx(1.0, abs=1e-9), name
    assert contestants["fund_overlay_30"].capital_leverage == pytest.approx(1.30)
    assert contestants["control_capweight_levered"].capital_leverage > 1.3


def test_the_two_funding_arms_hold_the_identical_portfolio(
    specification: Specification,
) -> None:
    """The whole point of running both is that only the benchmark differs."""
    contestants = _read_contestants(specification)
    pro_rata, cash = contestants["fund_prorata_30"], contestants["fund_cash_30"]
    assert dict(zip(pro_rata.tickers, pro_rata.weights, strict=True)) == dict(
        zip(cash.tickers, cash.weights, strict=True)
    )
    assert pro_rata.benchmark != cash.benchmark


def test_rsst_and_mate_carry_their_filed_notionals(specification: Specification) -> None:
    mappings = _build_mappings(specification)
    assert mappings["RSST"].coefficients["us_mkt"] == pytest.approx(1.072)
    assert mappings["MATE"].coefficients["us_mkt"] == pytest.approx(1.1587)
    assert mappings["MATE_FLOOR"].coefficients["us_mkt"] == pytest.approx(1.0)
    for ticker in ("RSST", "MATE", "MATE_FLOOR", "JPFP"):
        assert mappings[ticker].coefficients["trend"] == pytest.approx(1.0)


def test_jpfp_differs_from_rsst_by_its_fee_and_nothing_else(
    specification: Specification,
) -> None:
    """Its structure is an assumption, and the assumption is RSST's."""
    mappings = _build_mappings(specification)
    assert mappings["JPFP"].coefficients == mappings["RSST"].coefficients
    assert mappings["JPFP"].futures_notional == mappings["RSST"].futures_notional
    assert mappings["JPFP"].structure_assumed
    assert not mappings["RSST"].structure_assumed
    assert mappings["RSST"].expense_ratio_bp - mappings["JPFP"].expense_ratio_bp == 40.0


def test_only_rsst_carries_a_measured_tax_drag(specification: Specification) -> None:
    """`not measured` and `0.00` are different claims and must stay different."""
    mappings = _build_mappings(specification)
    measured = {
        ticker
        for ticker, mapping in mappings.items()
        if mapping.distribution_tax_drag_pp_yr is not None
    }
    assert measured == {"RSST"}


def test_only_aves_carries_an_assumed_fee(specification: Specification) -> None:
    mappings = _build_mappings(specification)
    assumed = {ticker for ticker, mapping in mappings.items() if mapping.fee_assumed}
    assert "AVES" in assumed
    assert "MATE" not in assumed


def test_the_costs_come_from_the_specification_not_from_the_code(
    specification: Specification,
) -> None:
    costs = _cost_settings(specification)
    assert costs.equity_futures_basis == pytest.approx(0.0062)
    assert costs.trend_book_financing == 0.0
    assert costs.spread_for("us_equity") == pytest.approx(0.55)


def test_the_correction_is_false_discovery_and_not_family_wise(
    specification: Specification,
) -> None:
    """Decision 0009 clause 2: a screening pass gets Benjamini-Hochberg."""
    correction = specification.inference.multiple_testing_correction.lower()
    assert "benjamini" in correction
    assert "holm" in correction  # it says explicitly that Holm is not used
    assert "not holm" in correction.replace("-", " ")


def test_the_falsifier_carries_no_fixed_percentage_point_bar(
    specification: Specification,
) -> None:
    """Decision 0010 clause 4: the demoted constants may not be operative.

    They may be NAMED -- this falsifier names them in order to say it is not
    using them -- but no lettered clause may contain one.
    """
    falsifier = specification.falsifier
    clauses = falsifier[falsifier.index("(a)") :]
    assert "2.0 pp" not in clauses
    assert "0.30 pp" not in clauses
    assert "pp/yr" not in clauses, "a lettered clause carries a fixed bar"
    assert "minimum detectable effect" in falsifier
    assert "unresolved" in falsifier


def test_every_era_lies_inside_the_sample_window(specification: Specification) -> None:
    policy = specification.sample_policy
    for era in policy.eras:
        assert policy.start <= era.start <= era.end <= policy.end
        assert era.rationale.strip()


def test_the_source_pin_names_a_committed_manifest_for_every_file(
    specification: Specification,
) -> None:
    assert isinstance(specification.parameters, Mapping)
    pin = specification.parameters["source_pin"]
    assert isinstance(pin, Mapping)
    files = pin["files"]
    assert isinstance(files, Sequence)
    root = SPEC_PATH.resolve().parents[1]
    for entry in files:
        assert isinstance(entry, Mapping)
        manifest = root / str(entry["committed_manifest"])
        assert manifest.is_file(), manifest
        assert len(str(entry["expected_sha256_raw"])) == 64
        assert len(str(entry["expected_sha256_normalized"])) == 64


# --------------------------------------------------------------------------- #
# End to end, on a synthetic panel
# --------------------------------------------------------------------------- #


def _synthetic_panel_like_the_real_one(months: int = 427) -> BasisPanel:
    """A panel with the real one's shape: correlated regions, a diversifying trend."""
    rng = np.random.default_rng(2026)
    world = rng.normal(0.006, 0.038, months)
    series = {
        "us_mkt": world + rng.normal(0.001, 0.018, months),
        "dxus_mkt": world + rng.normal(-0.001, 0.020, months),
        "em_mkt": world * 1.2 + rng.normal(0.000, 0.032, months),
        "trend": rng.normal(0.006, 0.030, months),
    }
    for name in (
        "us_smb",
        "us_hml",
        "us_rmw",
        "us_cma",
        "us_umd",
        "dxus_smb",
        "dxus_hml",
        "dxus_rmw",
        "dxus_cma",
        "dxus_umd",
        "em_hml",
    ):
        series[name] = rng.normal(0.002, 0.025, months)
    return BasisPanel(
        periods=tuple(
            f"{1990 + (10 + i) // 12:04d}-{(10 + i) % 12 + 1:02d}" for i in range(months)
        ),
        series={name: np.asarray(values, dtype=np.float64) for name, values in series.items()},
        cash=np.full(months, 0.002, dtype=np.float64),
        provenance=(),
        findings=("synthetic",),
    )


def test_the_whole_experiment_runs_and_reports_what_the_contract_requires(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Every reporting requirement that can be checked mechanically, checked."""
    import portfolio_edge.experiments.exp_016_construction_tournament as module
    from portfolio_edge.experiments.ledger import Ledger, LedgerEvent, RunStatus
    from portfolio_edge.experiments.result import ResultStatus
    from portfolio_edge.experiments.runner import run_experiment

    monkeypatch.setattr(
        module, "load_basis_panel", lambda _spec: _synthetic_panel_like_the_real_one()
    )
    specification = load_specification(SPEC_PATH)
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        specification,
        registry=module.build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
    )
    assert outcome.status is RunStatus.SUCCEEDED
    result = outcome.result
    assert result is not None
    # A screen may not promote its own finding, whatever it finds.
    assert result.status in {ResultStatus.EXPLORATORY, ResultStatus.UNRESOLVED}

    arms = result.diagnostics["arms"]
    assert isinstance(arms, Sequence)
    rows = {str(row["arm"]): row for row in arms if isinstance(row, Mapping)}
    assert set(rows) == set(_read_contestants(specification))

    for name, row in rows.items():
        if row["growth_gap_pp_yr"] is None:
            assert row["status"] == "not-scored", name
            continue
        # The reporting contract: a gap never appears without its floor, its
        # benchmark, its perturbation range or its gross notional.
        assert row["mde_80pc_power_pp_yr"] is not None, name
        assert row["benchmark"], name
        assert row["perturbation_gap_range_pp_yr"] is not None, name
        assert row["gross_notional"] is not None, name
        assert row["years_to_distinguish_at_80pc_power"] is not None, name
        assert row["status"] in {"exploratory", "unresolved", "rejected"}, name

    # An after-tax cell is `not measured` unless a fund published a drag.
    for name, row in rows.items():
        if row["after_tax_growth_gap_pp_yr"] is None:
            assert row["after_tax_note"] == "not measured", name

    # Every estimate carries units, and every gap is paired with an MDE estimate.
    gaps = {e.name for e in result.estimates if e.name.startswith("growth_gap[")}
    floors = {
        e.name.replace("minimum_detectable_effect[", "growth_gap[")
        for e in result.estimates
        if e.name.startswith("minimum_detectable_effect[")
    }
    assert gaps == floors
    assert all(estimate.units.strip() for estimate in result.estimates)

    # The ledger recorded the attempt from both ends.
    events = [entry.event for entry in ledger.read()]
    assert LedgerEvent.STARTED in events and LedgerEvent.SUCCEEDED in events

    # The committed artifacts are the summary and the manifest.
    written = {record.path.split("/")[-1] for record in outcome.artifacts}
    assert {"summary.md", "manifest.json"} <= written


def test_the_identical_funding_pair_produces_the_identical_wealth_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Two arms, one portfolio, two benchmarks, two answers."""
    import portfolio_edge.experiments.exp_016_construction_tournament as module
    from portfolio_edge.experiments.ledger import Ledger
    from portfolio_edge.experiments.runner import run_experiment

    monkeypatch.setattr(
        module, "load_basis_panel", lambda _spec: _synthetic_panel_like_the_real_one()
    )
    outcome = run_experiment(
        load_specification(SPEC_PATH),
        registry=module.build_registry(),
        ledger=Ledger(tmp_path / "ledger.jsonl"),
        artifact_root=tmp_path / "artifacts",
    )
    assert outcome.result is not None
    arms = outcome.result.diagnostics["arms"]
    assert isinstance(arms, Sequence)
    rows = {str(row["arm"]): row for row in arms if isinstance(row, Mapping)}
    pro_rata, cash = rows["fund_prorata_30"], rows["fund_cash_30"]
    assert pro_rata["growth_pp_yr"] == cash["growth_pp_yr"]
    assert pro_rata["max_drawdown_pct"] == cash["max_drawdown_pct"]
    assert pro_rata["growth_gap_pp_yr"] != cash["growth_gap_pp_yr"]
    assert pro_rata["benchmark"] != cash["benchmark"]


def test_a_financing_override_replaces_the_basis_everywhere_it_is_charged() -> None:
    """The one load-bearing cost nobody can observe has to be sweepable."""
    panel = _panel(24)
    costs = _costs()
    mappings = {"W": _mapping("W", {"us_mkt": 1.0, "trend": 1.0}, futures=0.5)}
    plain = fund_excess_matrix(panel, mappings, costs, tickers=["W"], shift=MappingShift())
    swept = fund_excess_matrix(
        panel,
        mappings,
        costs,
        tickers=["W"],
        shift=MappingShift(financing_basis_annual_percent=2.31),
    )
    # 0.62% -> 2.31% on 0.5 of futures notional, charged monthly.
    assert np.allclose((plain - swept), (0.0231 - 0.0062) * 0.5 / 12.0)


def test_a_financing_override_reaches_portfolio_level_borrowing_too() -> None:
    months = 12
    panel = BasisPanel(
        periods=tuple(f"2000-{i + 1:02d}" for i in range(months)),
        series={"us_mkt": np.zeros(months, dtype=np.float64)},
        cash=np.zeros(months, dtype=np.float64),
        provenance=(),
        findings=(),
    )
    mappings = {"A": _mapping("A", {"us_mkt": 1.0})}
    costs = MappingShift(financing_basis_annual_percent=2.31).applied_to(_costs())
    path = constant_weight_path(
        panel, mappings, costs, tickers=["A"], targets=np.array([1.5])
    )
    assert path.total[0] == pytest.approx(-0.0231 * 0.5 / 12.0)


def test_the_financing_band_specification_brackets_its_own_point_estimate() -> None:
    """A band that does not contain the number it is testing is not a band."""
    specification = load_specification(
        SPEC_PATH.with_name("exp_016c_financing_band.yaml")
    )
    assert isinstance(specification.parameters, Mapping)
    block = specification.parameters["financing_basis_band"]
    assert isinstance(block, Mapping)
    grid = [float(str(value)) for value in block["annual_percent"]]  # type: ignore[union-attr]
    point = _cost_settings(specification).equity_futures_basis * 100.0
    assert min(grid) <= point <= max(grid)
    assert min(grid) == pytest.approx(point)
    assert max(grid) == pytest.approx(2.31)
    watch = [str(name) for name in block["watch_arms"]]  # type: ignore[union-attr]
    contestants = _read_contestants(specification)
    assert all(name in contestants for name in watch)
