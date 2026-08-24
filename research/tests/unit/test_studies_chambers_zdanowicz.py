"""Tests for :mod:`portfolio_edge.studies.chambers_zdanowicz`.

These pin the arithmetic that settles open question 2 of
``docs/research/portfolio-edge-research-framework.md``: whether the rebalanced
portfolio's higher expected log wealth is "an arbitrary nonlinear transformation of
wealth" or a substantive claim. The tests establish, exactly and without simulation,
that the two policies have identical expected terminal wealth and that the rebalanced
one has strictly lower terminal-wealth variance and a strictly higher median.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.chambers_zdanowicz import (
    asymptotic_rebalanced_rate,
    certificate_of_deposit_example,
    continuous_terminal_wealth_moments,
    enumerate_binomial_comparison,
    exhibit_five,
    expected_terminal_wealth_held,
    expected_terminal_wealth_rebalanced,
)
from portfolio_edge.studies.volatility_harvesting import (
    excess_growth_two_asset,
    rebalancing_advantage,
)

# --------------------------------------------------------------------------------------
# The framework's committed fixture
# --------------------------------------------------------------------------------------


def test_expected_terminal_wealth_is_identical_for_both_policies() -> None:
    """The framework fixture: 16 paths, E[W_T] = 1.050625 for both, to machine precision.

    Independently derived: each asset has mean simple return
    0.5 * 0.25 + 0.5 * (-0.20) = 0.025 per period, so both policies are worth
    1.025**2 = 1.050625 after two periods. Chambers and Zdanowicz's long-rebalanced /
    short-buy-and-hold trade therefore has exactly zero expected profit, and this
    reproduction is what makes the *rest* of the argument about the log advantage
    rather than about the arithmetic.
    """
    result = enumerate_binomial_comparison(up_return=0.25, down_return=-0.20, periods=2)
    assert result.paths == 16
    assert result.expected_terminal_wealth_rebalanced == pytest.approx(
        1.050625, rel=0.0, abs=1e-15
    )
    assert result.expected_terminal_wealth_held == pytest.approx(1.050625, rel=0.0, abs=1e-15)
    assert result.expected_profit_of_long_rebalanced_short_held == pytest.approx(
        0.0, rel=0.0, abs=1e-15
    )


def test_the_single_asset_in_the_fixture_has_exactly_zero_growth() -> None:
    """sqrt(1.25 * 0.80) = 1 exactly, so the rebalanced portfolio's whole growth is excess.

    This is why the fixture isolates the effect: sum_i w_i g_i = 0, so the rebalanced
    portfolio's expected log growth *is* the diversification return.
    """
    assert math.sqrt(1.25 * 0.80) == pytest.approx(1.0, rel=0.0, abs=1e-15)
    result = enumerate_binomial_comparison(up_return=0.25, down_return=-0.20, periods=1)
    assert result.log_growth_rate_rebalanced == pytest.approx(0.0123463063, rel=0.0, abs=1e-9)
    assert result.log_growth_rate_held == result.log_growth_rate_rebalanced


def test_rebalanced_log_growth_is_constant_while_buy_and_hold_decays_with_horizon() -> None:
    """The exact mechanism, on a lattice: holding loses its bonus as the horizon lengthens.

    The rebalanced portfolio's per-period expected log growth is 1.23463% at every
    horizon. Buy-and-hold starts equal at one period — where the policies coincide — and
    falls away monotonically, so the advantage of *rebalancing as a policy* grows from
    nothing rather than being present from the start. It is 1.45 bp per period at two
    periods and 6.52 bp at six.
    """
    expected_hold = {
        1: 0.0123463063,
        2: 0.0122010218,
        3: 0.0120641658,
        4: 0.0119346855,
        5: 0.0118117410,
        6: 0.0116946454,
    }
    previous = math.inf
    for periods, expected in expected_hold.items():
        result = enumerate_binomial_comparison(
            up_return=0.25, down_return=-0.20, periods=periods
        )
        assert result.log_growth_rate_rebalanced == pytest.approx(
            0.0123463063, rel=0.0, abs=1e-9
        )
        assert result.log_growth_rate_held == pytest.approx(expected, rel=0.0, abs=1e-9)
        assert result.log_growth_rate_held <= previous
        previous = result.log_growth_rate_held
        assert result.expected_terminal_wealth_rebalanced == pytest.approx(
            result.expected_terminal_wealth_held, rel=0.0, abs=1e-14
        )


def test_rebalancing_strictly_reduces_terminal_wealth_variance_on_the_lattice() -> None:
    """Same mean, smaller variance. That is the entire content of the log advantage."""
    result = enumerate_binomial_comparison(up_return=0.25, down_return=-0.20, periods=4)
    assert result.variance_terminal_wealth_rebalanced < result.variance_terminal_wealth_held


def test_enumeration_refuses_an_unmanageable_lattice() -> None:
    with pytest.raises(ValueError, match="is refused above 8 periods"):
        enumerate_binomial_comparison(up_return=0.25, down_return=-0.20, periods=9)


def test_enumeration_refuses_a_total_loss() -> None:
    with pytest.raises(ValueError, match="strictly positive wealth relative"):
        enumerate_binomial_comparison(up_return=0.25, down_return=-1.0, periods=2)


# --------------------------------------------------------------------------------------
# The general identity, which is stronger than the lattice
# --------------------------------------------------------------------------------------


def test_expected_terminal_wealth_identity_holds_for_any_equal_mean_assets() -> None:
    """(1 + w'mu)**T = sum_i w_i (1 + mu_i)**T when all mu_i coincide, for any T and w."""
    for periods in (1, 5, 30, 100):
        for weight in (0.1, 0.5, 0.9):
            weights = [weight, 1.0 - weight]
            means = [0.07, 0.07]
            assert expected_terminal_wealth_rebalanced(
                weights=weights, mean_simple_returns=means, periods=periods
            ) == pytest.approx(
                expected_terminal_wealth_held(
                    weights=weights, mean_simple_returns=means, periods=periods
                ),
                rel=1e-14,
            )


def test_buy_and_hold_strictly_wins_on_expected_wealth_when_means_differ() -> None:
    """Convexity of x -> (1 + x)**T. This sharpens Chambers and Zdanowicz, not softens it.

    With means of 10% and 2% over 30 periods, buy-and-hold has expected terminal wealth
    9.6304 against the rebalanced portfolio's 5.7435 — a 68% advantage. An investor whose
    objective really is expected terminal wealth should never rebalance.
    """
    weights = [0.5, 0.5]
    means = [0.10, 0.02]
    held = expected_terminal_wealth_held(
        weights=weights, mean_simple_returns=means, periods=30
    )
    rebalanced = expected_terminal_wealth_rebalanced(
        weights=weights, mean_simple_returns=means, periods=30
    )
    assert held == pytest.approx(9.6303819265, rel=0.0, abs=1e-9)
    assert rebalanced == pytest.approx(5.7434911729, rel=0.0, abs=1e-9)
    assert held > rebalanced


# --------------------------------------------------------------------------------------
# The continuous-time version: mean-preserving contraction
# --------------------------------------------------------------------------------------


def test_continuous_expected_terminal_wealth_is_exactly_equal_for_both_policies() -> None:
    """E[V_T] = e**(mu T) for both, exactly, at every horizon and every correlation.

    Independently derived: E[e**X_i] = e**(g_i T + sigma**2 T / 2) = e**(mu T), so the
    buy-and-hold mixture has mean e**(mu T); and the constant-weight portfolio has
    arithmetic drift w'mu = mu. The Chambers-Zdanowicz equality is therefore not an
    artefact of a two-period binomial lattice.
    """
    for correlation in (-0.5, 0.0, 0.5, 0.99):
        for horizon in (1.0, 30.0, 200.0):
            moments = continuous_terminal_wealth_moments(
                arithmetic_drift=0.07,
                volatility=0.2,
                correlation=correlation,
                horizon_years=horizon,
            )
            assert moments.expected_terminal_wealth == pytest.approx(
                math.exp(0.07 * horizon), rel=0.0, abs=1e-12
            )


def test_rebalancing_is_a_mean_preserving_contraction() -> None:
    """Var(hold) - Var(reb) >= 0 by AM-GM, with equality only at rho = 1."""
    for correlation in (-0.5, 0.0, 0.5, 0.9):
        moments = continuous_terminal_wealth_moments(
            arithmetic_drift=0.07, volatility=0.2, correlation=correlation, horizon_years=30.0
        )
        assert moments.variance_reduction > 0.0
        assert moments.median_rebalanced > moments.median_held
    perfect = continuous_terminal_wealth_moments(
        arithmetic_drift=0.07, volatility=0.2, correlation=1.0, horizon_years=30.0
    )
    assert perfect.variance_reduction == pytest.approx(0.0, rel=0.0, abs=1e-9)


def test_thirty_year_variance_reduction_is_pinned() -> None:
    """mu = 7%, sigma = 20%, rho = 0, T = 30: same mean 8.1662, variance 54.82 vs 77.36."""
    moments = continuous_terminal_wealth_moments(
        arithmetic_drift=0.07, volatility=0.2, correlation=0.0, horizon_years=30.0
    )
    assert moments.expected_terminal_wealth == pytest.approx(8.1661699126, rel=0.0, abs=1e-9)
    assert moments.variance_rebalanced == pytest.approx(54.8240864778, rel=0.0, abs=1e-8)
    assert moments.variance_held == pytest.approx(77.3600425816, rel=0.0, abs=1e-8)
    assert moments.median_rebalanced == pytest.approx(6.0496474644, rel=0.0, abs=1e-8)
    assert moments.median_held == pytest.approx(5.6610064415, rel=0.0, abs=1e-6)
    # A 29% variance reduction bought with no reduction in expected wealth at all.
    assert moments.variance_reduction / moments.variance_held == pytest.approx(
        0.29131, rel=1e-4
    )


def test_continuous_moments_agree_with_a_seeded_simulation() -> None:
    """Independent check of the closed-form mean, variance and median of both policies."""
    rng = np.random.default_rng(20260812)
    paths, horizon, sigma, mu = 500_000, 30.0, 0.2, 0.07
    growth = mu - sigma**2 / 2.0
    logs = rng.standard_normal((paths, 2)) * sigma * math.sqrt(horizon) + growth * horizon
    held = 0.5 * np.exp(logs[:, 0]) + 0.5 * np.exp(logs[:, 1])
    rebalanced = np.exp(logs.mean(axis=1) + 0.25 * sigma**2 * horizon)

    moments = continuous_terminal_wealth_moments(
        arithmetic_drift=mu, volatility=sigma, correlation=0.0, horizon_years=horizon
    )
    standard_error = float(np.std(held, ddof=1)) / math.sqrt(paths)
    assert abs(float(np.mean(held)) - moments.expected_terminal_wealth) < 4.0 * standard_error
    assert float(np.median(held)) == pytest.approx(moments.median_held, rel=5e-3)
    assert float(np.median(rebalanced)) == pytest.approx(moments.median_rebalanced, rel=5e-3)


def test_log_advantage_equals_the_excess_growth_rate_net_of_the_holding_bonus() -> None:
    """The disputed quantity is exactly the rebalancing residual computed elsewhere.

    At sigma = 20%, rho = 0 the median 30-year advantage is 56.4 bp/yr and the mean is
    18.3 bp/yr. Whichever of those a reader prefers, both are the same order as an
    expense ratio, and neither is an arbitrage.
    """
    gamma = excess_growth_two_asset(volatility_a=0.2, volatility_b=0.2, correlation=0.0)
    advantage = rebalancing_advantage(excess_growth=gamma, horizon_years=30.0)
    assert advantage.mean == pytest.approx(0.00183145, rel=0.0, abs=1e-8)
    assert advantage.median == pytest.approx(0.00564368, rel=0.0, abs=1e-8)


# --------------------------------------------------------------------------------------
# Exhibit 5, reproduced and then extended past where the authors stopped
# --------------------------------------------------------------------------------------

# Chambers and Zdanowicz (2014), Exhibit 5, "Mean Ret." columns, as printed.
PRINTED_EXHIBIT_FIVE: dict[int, tuple[float, float, float]] = {
    1: (0.0250, 0.0250, 1.0250),
    2: (0.0187, 0.0187, 1.0506),
    3: (0.0166, 0.0164, 1.0769),
    4: (0.0156, 0.0152, 1.1038),
    5: (0.0150, 0.0145, 1.1314),
    6: (0.0145, 0.0140, 1.1597),
    7: (0.0142, 0.0136, 1.1887),
    8: (0.0140, 0.0132, 1.2184),
    9: (0.0138, 0.0129, 1.2489),
    10: (0.0137, 0.0127, 1.2801),
    11: (0.0136, 0.0125, 1.3121),
    12: (0.0135, 0.0123, 1.3499),
}


def test_exhibit_five_reproduces_the_published_table_except_two_entries() -> None:
    """Recomputed exactly from the stated inputs; 34 of 36 printed figures agree.

    Two do not, and both are the paper's arithmetic rather than ours:

    * the 12-period expected value is printed as $1.3499, but the paper's own text says
      the expected value "grows at the same fixed compound growth rate of 2.5% per year"
      and 1.025**12 = $1.34489;
    * the 4-period buy-and-hold mean return is printed as 1.52%, and recomputation gives
      1.5271%, which rounds to 1.53%.

    Neither changes any conclusion. They are recorded because a fixture that disagrees
    with our own computation is a finding, not a tolerance to loosen.
    """
    disagreements = 0
    for periods, (rebalanced, held, value) in PRINTED_EXHIBIT_FIVE.items():
        row = exhibit_five(periods=periods)
        assert row.rebalanced_mean_annualised_rate == pytest.approx(
            rebalanced, rel=0.0, abs=5e-5
        )
        if abs(row.held_mean_annualised_rate - held) > 5e-5:
            disagreements += 1
            assert periods == 4
            assert row.held_mean_annualised_rate == pytest.approx(0.01527068, rel=0.0, abs=1e-8)
        if abs(row.expected_value - value) > 5e-5:
            disagreements += 1
            assert periods == 12
            assert row.expected_value == pytest.approx(1.025**12, rel=0.0, abs=1e-12)
            assert row.expected_value == pytest.approx(1.3448888, rel=0.0, abs=1e-7)
    assert disagreements == 2


def test_the_two_period_headline_figures_are_annualised_rates_not_expected_log_wealth() -> None:
    """1.874% and 1.867% are E[W**(1/T)] - 1. Expected log wealth is 1.235% and 1.220%.

    The research framework currently describes the paper's headline pair as "expected
    log wealth", which is a mislabel. Both metrics rank the policies identically and
    both favour rebalancing, so the framework's conclusion survives, but the figures
    quoted beside it belong to a different statistic.
    """
    row = exhibit_five(periods=2)
    assert row.rebalanced_mean_annualised_rate == pytest.approx(0.018740, rel=0.0, abs=1e-6)
    assert row.held_mean_annualised_rate == pytest.approx(0.01866599, rel=0.0, abs=1e-8)
    assert row.rebalanced_log_growth == pytest.approx(0.0123463063, rel=0.0, abs=1e-9)
    assert row.held_log_growth == pytest.approx(0.0122010218, rel=0.0, abs=1e-9)
    assert row.rebalanced_log_growth != pytest.approx(
        row.rebalanced_mean_annualised_rate, rel=0.0, abs=1e-4
    )


def test_exhibit_five_agrees_with_full_path_enumeration_where_both_are_feasible() -> None:
    """The O(T**2) recombining computation must equal the 4**T enumeration."""
    for periods in range(1, 8):
        row = exhibit_five(periods=periods)
        enumerated = enumerate_binomial_comparison(
            up_return=0.25, down_return=-0.20, periods=periods
        )
        assert row.rebalanced_log_growth == pytest.approx(
            enumerated.log_growth_rate_rebalanced, rel=0.0, abs=1e-12
        )
        assert row.held_log_growth == pytest.approx(
            enumerated.log_growth_rate_held, rel=0.0, abs=1e-12
        )


def test_rebalanced_log_growth_is_horizon_invariant_while_holding_decays_to_zero() -> None:
    """The decisive extension. Their 12-period gap of 12 bp grows without bound.

    Log wealth is additive, so the rebalanced portfolio's expected log growth is exactly
    1.2346% per period at every horizon. The held portfolio's falls monotonically towards
    max_i g_i, which is exactly 0% here because sqrt(1.25 * 0.80) = 1. The paper stops at
    12 periods, where the annualised-rate gap is 0.118 pp; at 3,000 periods it is 1.034
    pp and still rising towards the full 1.2423%.
    """
    previous = math.inf
    for periods in (1, 12, 100, 400, 3_000):
        row = exhibit_five(periods=periods)
        assert row.rebalanced_log_growth == pytest.approx(0.0123463063, rel=0.0, abs=1e-9)
        assert row.held_log_growth < previous
        previous = row.held_log_growth
    # ln(1.25) = -ln(0.80), so the outer terms of g_p cancel exactly and
    # g_p = 0.5 ln(1.025) = 0.01234630629519 with no residual from the up and down legs.
    assert 0.5 * math.log(1.025) == pytest.approx(0.0123463063, rel=0.0, abs=1e-10)
    assert asymptotic_rebalanced_rate() == pytest.approx(
        math.expm1(0.5 * math.log(1.025)), rel=0.0, abs=1e-15
    )
    assert asymptotic_rebalanced_rate() == pytest.approx(0.0124228366, rel=0.0, abs=1e-9)

    # The two lattice gaps, derived independently of the O(T**2) table.
    #
    # The rebalanced side needs no lattice at all: the 50/50 portfolio's per-period
    # multiplier is iid over {1.25, 1.025, 0.80} with probabilities {1/4, 1/2, 1/4}, and
    # W**(1/T) is the PRODUCT of the m_t**(1/T), so independence gives
    # E[W**(1/T)] = (E[m**(1/T)])**T exactly. The held side is the mean of two
    # independent binomial wealth relatives; at T = 12 it is a 13 x 13 sum over exact
    # powers of 1.25 and 0.80, which shares no code with the log-space table.
    assert _rebalanced_rate_by_independence(12) == pytest.approx(
        exhibit_five(periods=12).rebalanced_mean_annualised_rate, rel=1e-12
    )
    assert _rebalanced_rate_by_independence(3_000) == pytest.approx(
        exhibit_five(periods=3_000).rebalanced_mean_annualised_rate, rel=1e-12
    )
    assert _held_rate_by_enumeration(12) == pytest.approx(
        exhibit_five(periods=12).held_mean_annualised_rate, rel=1e-12
    )
    assert _rebalanced_rate_by_independence(12) - _held_rate_by_enumeration(12) == pytest.approx(
        0.001180176412, rel=0.0, abs=5e-12
    )
    assert exhibit_five(periods=12).rate_gap == pytest.approx(0.001180176412, rel=0.0, abs=5e-12)
    # 0.010339142 at 3,000 periods, not the 0.0103387 previously pinned here: the old
    # literal was a rounding that happened to sit inside its own 1e-6 tolerance.
    assert exhibit_five(periods=3_000).rate_gap == pytest.approx(
        0.010339142421, rel=0.0, abs=5e-12
    )
    # The held portfolio's limit is exactly zero: it converges on a single zero-growth asset.
    assert exhibit_five(periods=3_000).held_log_growth < 0.0021


def _rebalanced_rate_by_independence(periods: int) -> float:
    """``E[W**(1/T)] - 1 = (E[m**(1/T)])**T - 1`` for the rebalanced 50/50 portfolio."""
    root = 1.0 / periods
    per_period = 0.25 * 1.25**root + 0.5 * 1.025**root + 0.25 * 0.80**root
    return float(per_period**periods) - 1.0


def _held_rate_by_enumeration(periods: int) -> float:
    """``E[W**(1/T)] - 1`` for buy-and-hold, summed over the two binomial counts."""
    relatives = [1.25**i * 0.80 ** (periods - i) for i in range(periods + 1)]
    weights = [math.comb(periods, i) for i in range(periods + 1)]
    total = sum(
        weights[i] * weights[j] * (0.5 * (relatives[i] + relatives[j])) ** (1.0 / periods)
        for i in range(periods + 1)
        for j in range(periods + 1)
    )
    return float(total) / 4.0**periods - 1.0


def test_exhibit_five_refuses_an_unmanageable_horizon() -> None:
    with pytest.raises(ValueError, match="O\\(T\\*\\*2\\) table"):
        exhibit_five(periods=3_001)


# --------------------------------------------------------------------------------------
# The authors' own deciding example, priced under both objectives
# --------------------------------------------------------------------------------------


def test_certificate_of_deposit_example_prices_the_disagreement() -> None:
    """$20,258 certain against a gamble worth $24,980 in expectation and $19,990 in log.

    Both computations are correct and they disagree. A log-utility investor pays $268.12
    per $10,000 — 1.32% of the certain terminal wealth — to decline a gamble whose
    expected value is 23.3% higher. The authors present this example as settling the
    question in favour of expected wealth; what it actually does is show that the two
    objectives are genuinely different, which is a preference, not a proof.
    """
    result = certificate_of_deposit_example()
    assert result.certain_terminal_wealth == pytest.approx(20_258.1651538, rel=0.0, abs=1e-6)
    assert result.risky_expected_terminal_wealth == pytest.approx(
        24_980.0974959, rel=0.0, abs=1e-6
    )
    assert result.risky_log_certainty_equivalent == pytest.approx(
        19_990.0462710, rel=0.0, abs=1e-6
    )
    assert result.expected_wealth_prefers_the_gamble
    assert result.log_utility_prefers_the_certain_deposit
    assert result.certain_terminal_wealth - result.risky_log_certainty_equivalent == (
        pytest.approx(268.1188827, rel=0.0, abs=1e-6)
    )
    assert result.risky_expected_terminal_wealth / result.certain_terminal_wealth == (
        pytest.approx(1.23309, rel=1e-5)
    )
    # The gamble's log certainty equivalent is the geometric mean of its two outcomes.
    assert result.risky_log_certainty_equivalent == pytest.approx(
        math.sqrt(10_000.0 * 10_000.0 * 1.08**18), rel=0.0, abs=1e-6
    )
