"""The valuation-conditioning arithmetic, against fixtures computed independently of it.

Five expectations below are worked out without calling the module under test.
:func:`test_hodrick_at_horizon_one_is_the_white_covariance` builds White's
heteroskedasticity-robust sandwich from ``numpy`` primitives and checks the 1B estimator
collapses onto it. :func:`test_hodrick_point_estimate_is_plain_least_squares` fits with
``numpy.linalg.lstsq``. :func:`test_hodrick_on_a_hand_worked_sample` carries a four-row
case through the sandwich on paper. :func:`test_stambaugh_bias_against_hand_arithmetic`
and :func:`test_out_of_sample_r2_against_hand_arithmetic` evaluate their formulae
directly. A fixture that disagrees with the implementation is a finding, not a tolerance
to loosen.
"""

from __future__ import annotations

import numpy as np
import pytest

from portfolio_edge.studies.valuation_conditioning import (
    ConditionalWeightRule,
    TiltCost,
    break_even_tax_rate,
    conditional_weight,
    derisking_regret_bp,
    excess_cape_yield,
    hodrick_1b_covariance,
    out_of_sample_r2,
    overlap_adjusted_observations,
    rescale_cape_for_price,
    stambaugh_bias,
    tilt_net_edge_bp,
)


def a_series(n: int = 400, seed: int = 20260822) -> tuple[np.ndarray, np.ndarray]:
    """A persistent predictor and a response, seeded so the fixtures are stable."""
    rng = np.random.default_rng(seed)
    x = np.empty(n)
    x[0] = 0.0
    for i in range(1, n):
        x[i] = 0.97 * x[i - 1] + rng.normal(0.0, 0.1)
    y = 0.05 * x + rng.normal(0.0, 0.5, size=n)
    return x, y


# --------------------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------------------


def test_overlap_adjusted_observations_is_the_block_count() -> None:
    assert overlap_adjusted_observations(1628, 120) == pytest.approx(13.5666667)
    assert overlap_adjusted_observations(120, 120) == 1.0


@pytest.mark.parametrize(("n", "h"), [(0, 12), (-1, 12), (100, 0), (100, -3)])
def test_overlap_adjusted_observations_rejects_nonsense(n: int, h: int) -> None:
    with pytest.raises(ValueError):
        overlap_adjusted_observations(n, h)


# --------------------------------------------------------------------------------------
# Hodrick 1B
# --------------------------------------------------------------------------------------


def test_hodrick_point_estimate_is_plain_least_squares() -> None:
    """1B changes the covariance and must never move the coefficient."""
    x, y = a_series()
    design = np.column_stack([np.ones(x.size), x])
    expected = np.linalg.lstsq(design, y, rcond=None)[0]
    result = hodrick_1b_covariance(
        y, x, horizon_periods=24, one_period_residuals=np.zeros(x.size) + 0.1
    )
    assert result.coefficients == pytest.approx(expected, rel=1e-12)


def test_hodrick_at_horizon_one_is_the_white_covariance() -> None:
    """At ``h = 1`` the backward sum is a single row, so 1B *is* White's sandwich."""
    x, y = a_series()
    design = np.column_stack([np.ones(x.size), x])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    residuals = y - design @ beta

    # White, built here from primitives rather than from anything in the repository.
    bread = np.linalg.inv(design.T @ design)
    meat = (design * residuals[:, None]).T @ (design * residuals[:, None])
    white_errors = np.sqrt(np.diag(bread @ meat @ bread))

    result = hodrick_1b_covariance(
        y, x, horizon_periods=1, one_period_residuals=residuals
    )
    assert result.standard_errors == pytest.approx(white_errors, rel=1e-10)
    assert result.independent_observations == float(x.size)


def test_hodrick_on_a_hand_worked_sample() -> None:
    """Four rows, horizon two, carried through the sandwich on paper."""
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([1.0, 3.0, 5.0, 7.0])  # exactly 1 + 2x
    residuals = np.array([0.5, -0.5, 1.0, -1.0])

    n = 4
    design = np.column_stack([np.ones(n), x])
    moment = design.T @ design / n  # [[1, 1.5], [1.5, 3.5]]
    moment_inv = np.linalg.inv(moment)
    # W_t for h = 2 is defined for t = 1, 2, 3: [2, 1], [2, 3], [2, 5].
    summed = np.array([[2.0, 1.0], [2.0, 3.0], [2.0, 5.0]])
    scores = summed * residuals[1:, None]
    spectral = scores.T @ scores / 3.0
    covariance = moment_inv @ spectral @ moment_inv / n
    expected = np.sqrt(np.diag(covariance))

    result = hodrick_1b_covariance(
        y, x, horizon_periods=2, one_period_residuals=residuals
    )
    assert result.standard_errors == pytest.approx(expected, rel=1e-12)
    assert result.coefficients == pytest.approx([1.0, 2.0], abs=1e-12)


def test_hodrick_is_more_conservative_than_newey_west_at_a_long_overlap() -> None:
    """The finding the module exists to protect: at a long overlap the two disagree.

    Newey-West with a lag equal to the horizon is asked for as many autocovariances as
    the overlap is long, from a sample holding only a handful of independent windows. On
    a genuinely overlapping construction it reports the smaller standard error, and it is
    the one that is wrong.
    """
    from portfolio_edge.inference.hac import hac_ols

    rng = np.random.default_rng(11)
    n, horizon = 1200, 120
    noise = rng.normal(0.0, 1.0, size=n + horizon)
    x = np.empty(n)
    x[0] = 0.0
    for i in range(1, n):
        x[i] = 0.99 * x[i - 1] + rng.normal(0.0, 0.1)
    # Pure overlap and no predictability: y is a rolling sum of independent noise.
    y = np.array([noise[i : i + horizon].sum() for i in range(n)])
    residuals = noise[:n] - noise[:n].mean()

    newey = hac_ols(y, x, n_lags=horizon)
    hodrick = hodrick_1b_covariance(
        y, x, horizon_periods=horizon, one_period_residuals=residuals
    )
    assert hodrick.standard_errors[1] > newey.standard_errors[1]
    assert hodrick.independent_observations == pytest.approx(10.0)


def test_hodrick_rejects_a_length_mismatch_and_an_oversized_horizon() -> None:
    x, y = a_series(n=50)
    with pytest.raises(ValueError, match="length mismatch"):
        hodrick_1b_covariance(y, x[:-1], horizon_periods=2, one_period_residuals=x)
    with pytest.raises(ValueError, match="exceeds the sample"):
        hodrick_1b_covariance(y, x, horizon_periods=51, one_period_residuals=x)
    with pytest.raises(ValueError, match="must be positive"):
        hodrick_1b_covariance(y, x, horizon_periods=0, one_period_residuals=x)
    broken = x.copy()
    broken[3] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        hodrick_1b_covariance(y, broken, horizon_periods=2, one_period_residuals=x)


# --------------------------------------------------------------------------------------
# Stambaugh
# --------------------------------------------------------------------------------------


def test_stambaugh_bias_against_hand_arithmetic() -> None:
    """``-(sigma_uv / sigma_v**2) (1 + 3 phi) / T``, evaluated on paper."""
    # -(-0.004 / 0.0001) * (1 + 3 * 0.99) / 1000 = 40 * 3.97 / 1000 = 0.1588
    assert stambaugh_bias(
        innovation_covariance=-0.004,
        predictor_innovation_variance=0.0001,
        autoregressive_root=0.99,
        n_observations=1000,
    ) == pytest.approx(0.1588, rel=1e-12)


def test_stambaugh_bias_is_positive_for_a_valuation_ratio() -> None:
    """A persistent predictor whose innovation is negatively correlated with the return
    biases the fitted slope **upward**, which is why an uncorrected slope overstates."""
    bias = stambaugh_bias(
        innovation_covariance=-2.6e-5,
        predictor_innovation_variance=1.2e-3,
        autoregressive_root=0.9966,
        n_observations=1747,
    )
    assert bias > 0.0


def test_stambaugh_bias_vanishes_when_the_innovations_are_orthogonal() -> None:
    assert (
        stambaugh_bias(
            innovation_covariance=0.0,
            predictor_innovation_variance=0.01,
            autoregressive_root=0.9,
            n_observations=500,
        )
        == 0.0
    )


def test_stambaugh_bias_refuses_a_unit_root() -> None:
    with pytest.raises(ValueError, match="stationary"):
        stambaugh_bias(
            innovation_covariance=-0.001,
            predictor_innovation_variance=0.01,
            autoregressive_root=1.0,
            n_observations=500,
        )


# --------------------------------------------------------------------------------------
# Out of sample
# --------------------------------------------------------------------------------------


def test_out_of_sample_r2_against_hand_arithmetic() -> None:
    realised = [1.0, 2.0, 3.0, 4.0]
    model = [1.5, 2.5, 2.0, 4.5]
    benchmark = [2.5, 2.5, 2.5, 2.5]
    # model SSE = 0.25 + 0.25 + 1.00 + 0.25 = 1.75
    # bench SSE = 2.25 + 0.25 + 0.25 + 2.25 = 5.00
    score = out_of_sample_r2(realised, model, benchmark)
    assert score.r2_out_of_sample == pytest.approx(1.0 - 1.75 / 5.0)
    assert score.mean_model_error == pytest.approx((-0.5 - 0.5 + 1.0 - 0.5) / 4.0)
    assert score.mean_benchmark_error == pytest.approx(0.0)


def test_out_of_sample_r2_is_negative_when_the_mean_forecasts_better() -> None:
    """Goyal and Welch's whole point, and the sign that settles the question."""
    score = out_of_sample_r2([1.0, 2.0, 3.0], [10.0, -5.0, 8.0], [2.0, 2.0, 2.0])
    assert score.r2_out_of_sample < 0.0


def test_out_of_sample_r2_reports_independent_forecasts() -> None:
    score = out_of_sample_r2(
        np.zeros(240), np.ones(240), np.full(240, 2.0), horizon_periods=120
    )
    assert score.independent_forecasts == pytest.approx(2.0)


def test_out_of_sample_r2_rejects_an_exact_benchmark() -> None:
    with pytest.raises(ValueError, match="undefined"):
        out_of_sample_r2([1.0, 2.0], [1.0, 2.0], [1.0, 2.0])


# --------------------------------------------------------------------------------------
# The rule
# --------------------------------------------------------------------------------------


def test_conditional_weight_holds_the_base_at_the_median() -> None:
    rule = ConditionalWeightRule(base_weight=0.80, sensitivity=0.4)
    assert conditional_weight(rule, 0.5) == pytest.approx(0.80)
    # sensitivity 0.4 spans +/- 0.20, because the percentile is +/- 0.5 from its median.
    assert conditional_weight(rule, 0.75) == pytest.approx(0.90)
    assert conditional_weight(rule, 0.0) == pytest.approx(0.60)
    assert conditional_weight(rule, 1.0) == pytest.approx(1.00)


def test_conditional_weight_clips_to_the_admissible_range() -> None:
    rule = ConditionalWeightRule(base_weight=0.80, sensitivity=1.6, floor=0.10, cap=0.95)
    assert conditional_weight(rule, 1.0) == 0.95
    assert conditional_weight(rule, 0.0) == 0.10


def test_conditional_weight_rejects_an_inverted_response() -> None:
    """A negative sensitivity is how a valuation rule is published with its sign flipped.

    The orientation belongs in the *signal* — high percentile means cheap — so that the
    error is visible at the call site rather than absorbed into a coefficient.
    """
    with pytest.raises(ValueError, match="sensitivity is the magnitude"):
        ConditionalWeightRule(base_weight=0.80, sensitivity=-0.4)


def test_conditional_weight_rule_validates_its_bounds() -> None:
    with pytest.raises(ValueError, match="floor <= cap"):
        ConditionalWeightRule(base_weight=0.5, sensitivity=0.1, floor=0.6, cap=0.4)
    with pytest.raises(ValueError, match="outside"):
        ConditionalWeightRule(base_weight=0.99, sensitivity=0.1, floor=0.1, cap=0.9)


@pytest.mark.parametrize("percentile", [-0.01, 1.01])
def test_conditional_weight_rejects_a_percentile_outside_the_unit_interval(
    percentile: float,
) -> None:
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        conditional_weight(ConditionalWeightRule(0.8, 0.4), percentile)


# --------------------------------------------------------------------------------------
# What acting on it costs
# --------------------------------------------------------------------------------------


def test_tilt_net_edge_against_hand_arithmetic() -> None:
    """Execution on all the turnover, tax on the half of it that is a sale."""
    cost = TiltCost(
        annual_turnover=0.0858,
        spread_and_commission_bp=10.0,
        effective_capital_gains_rate=0.15,
    )
    # execution = 0.0858 * 10 = 0.858 bp; tax = 0.5 * 0.0858 * 0.15 * 10000 = 64.35 bp
    assert tilt_net_edge_bp(gross_edge_bp=49.4910, cost=cost) == pytest.approx(
        49.4910 - 0.858 - 64.35, rel=1e-12
    )


def test_break_even_tax_rate_zeroes_the_net_edge() -> None:
    """Round trip: at the break-even rate the net edge is exactly zero."""
    turnover = 0.0858
    gross = 49.4910
    rate = break_even_tax_rate(
        gross_edge_bp=gross,
        cost=TiltCost(turnover, 10.0, 0.0),
    )
    assert rate == pytest.approx(0.1134, abs=5e-4)
    assert tilt_net_edge_bp(
        gross_edge_bp=gross, cost=TiltCost(turnover, 10.0, rate)
    ) == pytest.approx(0.0, abs=1e-9)


def test_break_even_tax_rate_is_zero_when_execution_alone_consumes_the_edge() -> None:
    assert (
        break_even_tax_rate(
            gross_edge_bp=5.0, cost=TiltCost(1.0, 10.0, 0.0)
        )
        == 0.0
    )


def test_tilt_cost_refuses_a_statutory_rate_dressed_as_an_effective_one() -> None:
    with pytest.raises(ValueError, match="embedded gain fraction"):
        TiltCost(0.1, 10.0, 1.0)
    with pytest.raises(ValueError, match="cannot be negative"):
        TiltCost(-0.1, 10.0, 0.15)


def test_derisking_regret_scales_with_the_premium_the_investor_supplies() -> None:
    """``w * p``, and the investor supplies ``p`` rather than being handed a forecast."""
    assert derisking_regret_bp(
        weight_reduction=0.15, realised_excess_return=5.0
    ) == pytest.approx(75.0)
    assert derisking_regret_bp(
        weight_reduction=0.15, realised_excess_return=0.0
    ) == pytest.approx(0.0)
    # A cut that turns out to have helped is a negative regret, not an error.
    assert derisking_regret_bp(weight_reduction=0.15, realised_excess_return=-2.0) < 0.0


# --------------------------------------------------------------------------------------
# Level arithmetic
# --------------------------------------------------------------------------------------


def test_excess_cape_yield_is_the_earnings_yield_less_the_real_rate() -> None:
    # Shiller's 2026-08 row: CAPE 41.177621, DFII10 2.35% on 2026-08-20.
    assert excess_cape_yield(cape=41.177621, real_yield_percent=2.35) == pytest.approx(
        100.0 / 41.177621 - 2.35, rel=1e-12
    )
    assert excess_cape_yield(cape=41.177621, real_yield_percent=2.35) == pytest.approx(
        0.0785, abs=5e-4
    )


def test_excess_cape_yield_rejects_a_non_positive_cape() -> None:
    with pytest.raises(ValueError, match="cape must be positive"):
        excess_cape_yield(cape=0.0, real_yield_percent=2.0)


def test_rescale_cape_reconciles_the_workbook_with_an_independent_reading() -> None:
    """Shiller's 2026-08 row is an August 1st close; the market moved after it.

    Scaling the workbook's 41.178 by the index's move from its 7,600.50 August 1st close
    to 7,674.37 on 2026-08-21 gives 41.58, which is what GuruFocus published for August
    2026. The agreement is the check that the staleness is a price effect and not a
    different construction. multpl.com's 41.96 for the same date is *not* reproduced by
    this scaling, so the three readings do not share one denominator and no page may
    quote them interchangeably.
    """
    scaled = rescale_cape_for_price(
        cape=41.177621, index_at_cape=7600.50, index_now=7674.37
    )
    assert scaled == pytest.approx(41.578, abs=5e-3)
    assert scaled < 41.96


def test_rescale_cape_is_the_identity_at_an_unchanged_price() -> None:
    assert rescale_cape_for_price(
        cape=41.177621, index_at_cape=7600.50, index_now=7600.50
    ) == pytest.approx(41.177621, rel=1e-12)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cape": 0.0, "index_at_cape": 100.0, "index_now": 100.0},
        {"cape": 40.0, "index_at_cape": 0.0, "index_now": 100.0},
        {"cape": 40.0, "index_at_cape": 100.0, "index_now": -1.0},
    ],
)
def test_rescale_cape_rejects_non_positive_inputs(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        rescale_cape_for_price(**kwargs)
