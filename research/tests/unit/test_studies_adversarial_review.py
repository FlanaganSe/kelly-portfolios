"""Tests for the adversarial-review arithmetic.

Every fixture below is computed independently of the implementation — by hand, by a
closed form the implementation does not use, or by simulating the quantity the closed
form is supposed to summarise.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.adversarial_review import (
    contribution_equivalent,
    difference_floor,
    empirical_bayes_alphas,
    premium_at_volatility,
    restate_to_arithmetic_gross,
    subperiod_floor,
)


class TestRestateToArithmeticGross:
    def test_reproduces_the_trend_premium_correction_by_hand(self) -> None:
        """The session's own numbers, corrected by hand.

        A 1.80 pp/yr geometric forecast net of a 1.50% fee, on a 12.38% volatility
        series, is ``1.80 + 1.50 + 0.5 * 12.38**2 / 100 = 4.0644`` on an arithmetic
        gross basis. Against a realised 10.98 that is a haircut of 6.9156, not 9.18.
        """
        result = restate_to_arithmetic_gross(
            stated_geometric_net=1.80,
            volatility=12.38,
            fee=1.50,
            realised_arithmetic_gross=10.98,
        )
        assert result.variance_drag_added_back == pytest.approx(0.7664, abs=1e-4)
        assert result.arithmetic_gross == pytest.approx(4.0664, abs=1e-3)
        assert result.implied_haircut == pytest.approx(6.9136, abs=1e-3)
        assert result.stated_haircut == pytest.approx(9.18, abs=1e-9)
        assert result.haircut_overstatement == pytest.approx(2.2664, abs=1e-3)

    def test_a_zero_fee_and_zero_volatility_forecast_is_unchanged(self) -> None:
        result = restate_to_arithmetic_gross(
            stated_geometric_net=3.0, volatility=0.0, fee=0.0,
            realised_arithmetic_gross=10.0,
        )
        assert result.arithmetic_gross == pytest.approx(3.0)
        assert result.implied_haircut == pytest.approx(result.stated_haircut)

    def test_variance_drag_matches_a_simulated_lognormal(self) -> None:
        """``sigma**2 / 2`` is the gap a simulated series actually shows."""
        rng = np.random.default_rng(20260822)
        sigma_monthly = 0.12 / math.sqrt(12)
        draws = rng.normal(0.0, sigma_monthly, size=4_000_000)
        arithmetic = float(np.mean(np.expm1(draws))) * 12 * 100
        geometric = float(np.mean(draws)) * 12 * 100
        assert arithmetic - geometric == pytest.approx(0.5 * 12.0**2 / 100.0, abs=0.05)

    @pytest.mark.parametrize(("volatility", "fee"), [(-1.0, 0.0), (10.0, -0.5)])
    def test_rejects_negative_inputs(self, volatility: float, fee: float) -> None:
        with pytest.raises(ValueError):
            restate_to_arithmetic_gross(
                stated_geometric_net=1.0, volatility=volatility, fee=fee,
                realised_arithmetic_gross=5.0,
            )


class TestSubperiodFloor:
    def test_halving_the_sample_multiplies_the_floor_by_root_two(self) -> None:
        assert subperiod_floor(1.0, full_months=400, subperiod_months=200) == pytest.approx(
            math.sqrt(2.0)
        )

    def test_the_tilt_arm_post_gfc(self) -> None:
        """0.4693 pp/yr on 427 months becomes 0.6757 on the 206 post-GFC months.

        Independently: ``0.4693 * sqrt(427 / 206) = 0.4693 * 1.43965 = 0.67562``.
        """
        assert subperiod_floor(
            0.4693, full_months=427, subperiod_months=206
        ) == pytest.approx(0.6756, abs=1e-3)

    def test_the_full_sample_is_its_own_subperiod(self) -> None:
        assert subperiod_floor(2.0, full_months=100, subperiod_months=100) == pytest.approx(2.0)

    def test_rejects_a_subperiod_longer_than_the_sample(self) -> None:
        with pytest.raises(ValueError, match="exceeds"):
            subperiod_floor(1.0, full_months=100, subperiod_months=101)

    def test_rejects_nonpositive_months(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            subperiod_floor(1.0, full_months=100, subperiod_months=0)


class TestDifferenceFloor:
    def test_it_is_twice_the_full_floor(self) -> None:
        assert difference_floor(3.3286) == pytest.approx(6.6572)

    def test_it_matches_the_root_sum_of_two_half_sample_errors(self) -> None:
        """Derived a second way: two halves, each with ``sqrt(2)`` the full error."""
        full = 1.0
        half = subperiod_floor(full, full_months=428, subperiod_months=214)
        assert math.hypot(half, half) == pytest.approx(difference_floor(full))

    def test_rejects_a_negative_floor(self) -> None:
        with pytest.raises(ValueError):
            difference_floor(-1.0)


class TestEmpiricalBayesAlphas:
    def test_shrinks_the_session_alphas_by_hand(self) -> None:
        """AVLV, DFIV, IDMO, AVES, VEA with their HAC standard errors.

        By hand: ``mean(a**2) = (0.1369 + 14.44 + 0.1764 + 2.7556 + 0.0) / 5 = 3.50178``
        and ``mean(s**2) = (3.545689 + 1.580049 + 3.636649 + 2.56 + 0.289444) / 5
        = 2.3223662``, so ``tau**2 = 1.1794138`` and DFIV keeps
        ``1.1794138 / (1.1794138 + 1.580049) = 0.4274070`` of -3.80, i.e. -1.6241466.
        (Carrying the shrinkage to six places instead and multiplying gives -1.624173;
        that is the fixture's own rounding, not a disagreement with the code.)
        """
        result = empirical_bayes_alphas(
            [-0.37, -3.80, 0.42, -1.66, 0.00],
            [1.883, 1.257, 1.907, 1.600, 0.538],
        )
        assert result.prior_variance == pytest.approx(1.1794138, abs=1e-6)
        assert result.shrinkage[1] == pytest.approx(0.4274070, abs=1e-7)
        assert result.shrunk[1] == pytest.approx(-1.6241466, abs=1e-6)
        charge = result.portfolio_charge([0.15, 0.10, 0.05, 0.05, 0.10])
        assert charge == pytest.approx(-0.1973033, abs=1e-6)

    def test_a_noiseless_estimate_keeps_all_of_itself(self) -> None:
        result = empirical_bayes_alphas([2.0, -2.0], [0.0, 0.0])
        assert result.shrinkage == pytest.approx(np.array([1.0, 1.0]))
        assert result.shrunk == pytest.approx(np.array([2.0, -2.0]))

    def test_pure_noise_shrinks_to_zero(self) -> None:
        """When every estimate is smaller than its own error, the prior collapses."""
        result = empirical_bayes_alphas([0.1, -0.1, 0.05], [3.0, 3.0, 3.0])
        assert result.prior_variance == pytest.approx(0.0)
        assert result.shrunk == pytest.approx(np.zeros(3))

    def test_shrinkage_is_monotone_in_precision(self) -> None:
        result = empirical_bayes_alphas([3.0, 3.0, 3.0], [0.5, 1.0, 2.0])
        assert result.shrinkage[0] > result.shrinkage[1] > result.shrinkage[2]

    def test_recovers_the_truth_better_than_face_value_in_simulation(self) -> None:
        """The claim the estimator makes: lower total squared error than no shrinkage.

        Ten funds, true alphas drawn from a prior with variance 1, observed with
        heteroskedastic noise. Shrinkage must beat face value on mean squared error,
        which is the entire argument against a threshold rule.
        """
        rng = np.random.default_rng(7)
        errors_shrunk = 0.0
        errors_raw = 0.0
        for _ in range(400):
            truth = rng.normal(0.0, 1.0, size=10)
            noise = rng.uniform(0.5, 2.5, size=10)
            observed = truth + rng.normal(0.0, noise)
            result = empirical_bayes_alphas(observed.tolist(), noise.tolist())
            errors_shrunk += float(np.sum((result.shrunk - truth) ** 2))
            errors_raw += float(np.sum((observed - truth) ** 2))
        assert errors_shrunk < errors_raw

    def test_rejects_mismatched_shapes(self) -> None:
        with pytest.raises(ValueError, match="shape mismatch"):
            empirical_bayes_alphas([1.0, 2.0], [1.0])

    def test_rejects_empty_and_nonfinite(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            empirical_bayes_alphas([], [])
        with pytest.raises(ValueError, match="finite"):
            empirical_bayes_alphas([float("nan")], [1.0])

    def test_rejects_negative_standard_errors(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            empirical_bayes_alphas([1.0], [-1.0])

    def test_portfolio_charge_rejects_a_wrong_length_weight_vector(self) -> None:
        result = empirical_bayes_alphas([1.0, 2.0], [1.0, 1.0])
        with pytest.raises(ValueError, match="weights has shape"):
            result.portfolio_charge([1.0])


class TestPremiumAtVolatility:
    def test_restates_the_century_trend_book_at_the_vendor_volatility(self) -> None:
        """0.580 Sharpe at 12.38% volatility is 7.180 pp/yr."""
        assert premium_at_volatility(0.580, 12.38) == pytest.approx(7.1804, abs=1e-4)

    def test_it_is_the_inverse_of_a_sharpe_ratio(self) -> None:
        assert premium_at_volatility(10.98 / 12.38, 12.38) == pytest.approx(10.98)

    def test_rejects_nonpositive_volatility(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            premium_at_volatility(1.0, 0.0)


class TestContributionEquivalent:
    def test_matches_a_month_by_month_simulation(self) -> None:
        """Compound both legs explicitly and check the terminal wealths agree."""
        edge, growth, months = 0.79, 10.0, 360
        contribution = contribution_equivalent(
            edge_pp_yr=edge, growth_pp_yr=growth, months=months
        )
        slow, fast = 1.0, 1.0
        base = (1.0 + growth / 100.0) ** (1.0 / 12.0)
        quick = (1.0 + (growth + edge) / 100.0) ** (1.0 / 12.0)
        for _ in range(months):
            slow = slow * base + contribution
            fast = fast * quick
        assert slow == pytest.approx(fast, rel=1e-9)

    def test_a_zero_edge_needs_no_contribution(self) -> None:
        assert contribution_equivalent(
            edge_pp_yr=0.0, growth_pp_yr=8.0, months=240
        ) == pytest.approx(0.0, abs=1e-12)

    def test_a_bigger_edge_needs_a_bigger_contribution(self) -> None:
        small = contribution_equivalent(edge_pp_yr=0.2, growth_pp_yr=8.0, months=240)
        large = contribution_equivalent(edge_pp_yr=2.0, growth_pp_yr=8.0, months=240)
        assert 0.0 < small < large

    def test_handles_zero_growth(self) -> None:
        """The degenerate annuity branch: at 0% growth the annuity is just ``months``."""
        value = contribution_equivalent(edge_pp_yr=1.0, growth_pp_yr=0.0, months=120)
        wealth = 1.0 + value * 120
        assert wealth == pytest.approx(1.01 ** 10, rel=1e-9)

    def test_rejects_nonpositive_months(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            contribution_equivalent(edge_pp_yr=1.0, growth_pp_yr=8.0, months=0)
