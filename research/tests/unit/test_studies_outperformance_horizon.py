"""Tests for :mod:`portfolio_edge.studies.outperformance_horizon`.

The arithmetic is elementary and the numbers are the point, so they are pinned rather
than described. The structural tests exist to stop the budget from being aggregated
across benchmarks, which is the way this argument is usually inflated.
"""

from __future__ import annotations

import math

import pytest
from scipy.stats import norm

from portfolio_edge.studies.outperformance_horizon import (
    EDGE_BUDGET,
    Benchmark,
    Certainty,
    EdgeComponent,
    FactorTiltChain,
    aggregate,
    budget_for,
    detectable_edge_bp,
    horizon_for_confidence,
    probability_of_outperformance,
    probability_table,
)


def _component(**overrides: object) -> EdgeComponent:
    defaults: dict[str, object] = {
        "name": "example",
        "mechanism": "example mechanism",
        "benchmark": Benchmark.STATED_INDEX,
        "certainty": Certainty.PROBABILISTIC,
        "low_bp": 0.0,
        "central_bp": 10.0,
        "high_bp": 20.0,
        "tracking_error_bp": 100.0,
        "conditions": "none",
        "falsifier": "a falsifier",
    }
    defaults.update(overrides)
    return EdgeComponent(**defaults)  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# The horizon arithmetic
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("horizon", "expected"),
    [(10.0, 0.6536836), (20.0, 0.7119249), (30.0, 0.7532186), (50.0, 0.8116204)],
)
def test_fifty_basis_points_against_four_percent_tracking_error(
    horizon: float, expected: float
) -> None:
    """The load-bearing number: a 50 bp edge at 400 bp tracking error is a coin toss.

    After thirty years such an investor has only a 75% chance of being ahead. Nothing
    about that is a statement about markets; it is Phi(0.5 sqrt(30) / 4).
    """
    probability = probability_of_outperformance(
        edge_bp=50.0, tracking_error_bp=400.0, horizon_years=horizon
    )
    assert probability == pytest.approx(expected, rel=0.0, abs=1e-6)


@pytest.mark.parametrize(
    ("confidence", "expected_years"),
    [(0.90, 105.1120), (0.95, 173.1548), (0.99, 346.3612)],
)
def test_horizon_for_confidence_at_fifty_basis_points(
    confidence: float, expected_years: float
) -> None:
    """90% confidence in a 50 bp edge against 4% tracking error takes 105 years.

    T = (z s / e)**2, so the horizon is quadratic in the ratio of tracking error to
    edge. This is the arithmetic that makes "wait and see" useless as a validation
    strategy for anything but a contractual saving.
    """
    years = horizon_for_confidence(
        edge_bp=50.0, tracking_error_bp=400.0, confidence=confidence
    )
    assert years == pytest.approx(expected_years, rel=1e-5)
    assert probability_of_outperformance(
        edge_bp=50.0, tracking_error_bp=400.0, horizon_years=years
    ) == pytest.approx(confidence, rel=0.0, abs=1e-12)


def test_horizon_is_quadratic_in_the_tracking_error_to_edge_ratio() -> None:
    """Halving the edge quadruples the time; doubling the tracking error quadruples it."""
    base = horizon_for_confidence(edge_bp=50.0, tracking_error_bp=400.0, confidence=0.90)
    half_edge = horizon_for_confidence(edge_bp=25.0, tracking_error_bp=400.0, confidence=0.90)
    double_error = horizon_for_confidence(
        edge_bp=50.0, tracking_error_bp=800.0, confidence=0.90
    )
    assert half_edge == pytest.approx(4.0 * base, rel=1e-12)
    assert double_error == pytest.approx(4.0 * base, rel=1e-12)


@pytest.mark.parametrize(
    ("tracking_error", "expected_years"),
    [(10.0, 0.0657), (50.0, 1.6422), (100.0, 6.5686), (200.0, 26.2744), (400.0, 105.0977)],
)
def test_tracking_error_not_edge_size_decides_whether_a_lifetime_is_enough(
    tracking_error: float, expected_years: float
) -> None:
    """The same 50 bp edge takes 24 days or 105 years depending only on its benchmark.

    A fee saving on the same index fund has a tracking error of a few basis points and
    is effectively certain within a year. A factor tilt with the same expected edge and
    400 bp of tracking error is not resolvable in a lifetime. Certainty class is a
    property of the pairing of edge and benchmark, never of the edge alone.
    """
    years = horizon_for_confidence(
        edge_bp=50.0, tracking_error_bp=tracking_error, confidence=0.90
    )
    assert years == pytest.approx(expected_years, rel=1e-3)


def test_zero_tracking_error_is_immediate_certainty() -> None:
    """A contractual saving against its own counterfactual has no dispersion at all."""
    assert probability_of_outperformance(
        edge_bp=50.0, tracking_error_bp=0.0, horizon_years=1.0
    ) == 1.0
    assert probability_of_outperformance(
        edge_bp=-50.0, tracking_error_bp=0.0, horizon_years=1.0
    ) == 0.0


@pytest.mark.parametrize(
    ("horizon", "expected_bp"),
    [(10.0, 162.1), (20.0, 114.6), (30.0, 93.6), (50.0, 72.5)],
)
def test_detectable_edge_is_far_larger_than_any_plausible_edge(
    horizon: float, expected_bp: float
) -> None:
    """Against 400 bp of tracking error, 30 years can only demonstrate a 94 bp edge.

    Read against the budget, this says that no probabilistic component in it is
    demonstrable from an investor's own experience. The evidence has to come from
    somewhere other than the investor's own track record.
    """
    edge = detectable_edge_bp(
        tracking_error_bp=400.0, horizon_years=horizon, confidence=0.90
    )
    assert edge == pytest.approx(expected_bp, rel=1e-3)


def test_probability_matches_the_normal_distribution_function_directly() -> None:
    """Independent restatement: P = Phi(e sqrt(T) / s), computed without the module."""
    for edge, error, horizon in ((25.0, 300.0, 17.0), (120.0, 950.0, 41.0)):
        assert probability_of_outperformance(
            edge_bp=edge, tracking_error_bp=error, horizon_years=horizon
        ) == pytest.approx(float(norm.cdf(edge * math.sqrt(horizon) / error)), rel=0.0, abs=1e-15)


def test_probability_table_is_monotone_in_horizon_for_a_positive_edge() -> None:
    table = probability_table(edge_bp=40.0, tracking_error_bp=250.0)
    assert [horizon for horizon, _ in table] == [5.0, 10.0, 20.0, 30.0, 50.0]
    values = [probability for _, probability in table]
    assert values == sorted(values)
    assert values[0] > 0.5


# --------------------------------------------------------------------------------------
# Budget structure: refusing the double count
# --------------------------------------------------------------------------------------


def test_components_from_different_benchmarks_cannot_be_aggregated() -> None:
    """Beating the index and beating the average investor are different claims."""
    with pytest.raises(ValueError, match="must share one benchmark"):
        aggregate(
            [
                _component(benchmark=Benchmark.STATED_INDEX),
                _component(benchmark=Benchmark.AVERAGE_INVESTOR),
            ]
        )


def test_a_deterministic_component_may_not_have_a_negative_low_estimate() -> None:
    with pytest.raises(ValueError, match="cannot have a negative low"):
        _component(certainty=Certainty.DETERMINISTIC, low_bp=-5.0)


def test_every_component_needs_a_falsifier() -> None:
    with pytest.raises(ValueError, match="needs a falsifier"):
        _component(falsifier="   ")


def test_component_bounds_must_be_ordered() -> None:
    with pytest.raises(ValueError, match="require low <= central <= high"):
        _component(low_bp=30.0, central_bp=10.0, high_bp=20.0)


def test_aggregation_sums_edges_and_combines_tracking_errors_in_quadrature() -> None:
    """Central estimates add; tracking errors add in quadrature under independence.

    The independence assumption is optimistic and is stated as such in the module: two
    sleeves of the same equity portfolio share a beta and a crisis.
    """
    total = aggregate(
        [
            _component(central_bp=30.0, low_bp=0.0, high_bp=60.0, tracking_error_bp=300.0),
            _component(central_bp=40.0, low_bp=10.0, high_bp=70.0, tracking_error_bp=400.0),
        ]
    )
    assert total.components == 2
    assert total.central_bp == 70.0
    assert total.low_bp == 10.0
    assert total.high_bp == 130.0
    assert total.tracking_error_bp == pytest.approx(500.0, rel=0.0, abs=1e-12)
    assert total.probability_of_outperformance(30.0) == pytest.approx(
        float(norm.cdf(70.0 * math.sqrt(30.0) / 500.0)), rel=0.0, abs=1e-15
    )


def test_aggregating_nothing_is_refused() -> None:
    with pytest.raises(ValueError, match="empty budget"):
        aggregate([])


# --------------------------------------------------------------------------------------
# The factor chain
# --------------------------------------------------------------------------------------


def test_factor_tilt_chain_multiplies_out_to_a_small_number() -> None:
    """6.6%/yr gross long-short becomes 21 bp/yr of portfolio edge, before any doubt.

    Harvey, Liu and Zhu's structural prior for a *true* factor is 0.55%/month, which is
    6.6%/yr at their imposed 15% volatility, in sample and gross. McLean and Pontiff's
    post-publication decay leaves 42% of it. A long-only implementation captures some
    fraction of a long-short premium that no source in the research framework
    establishes — 40% is an assumption, not a measurement. A 30% portfolio-level factor
    exposure and a 12 bp incremental fee over a broad index fund finish the chain.

    The output is 21.2 bp/yr against several hundred basis points of tracking error, so
    by the horizon arithmetic above it is undemonstrable within a lifetime. That is the
    honest status of factor tilting in this budget: plausible, small, and unverifiable
    from the investor's own experience.
    """
    chain = FactorTiltChain(
        gross_long_short_premium_bp=660.0,
        post_publication_retention=0.42,
        long_only_capture=0.40,
        portfolio_exposure=0.30,
        incremental_fee_bp=12.0,
        incremental_trading_cost_bp=0.0,
    )
    assert chain.net_edge_bp == pytest.approx(21.264, rel=0.0, abs=1e-3)
    assert horizon_for_confidence(
        edge_bp=chain.net_edge_bp, tracking_error_bp=400.0, confidence=0.90
    ) > 500.0


def test_factor_tilt_chain_turns_negative_on_plausible_pessimistic_inputs() -> None:
    """Halve the capture fraction and the tilt costs more than it earns.

    Every multiplier in the chain is disputed, and the product crosses zero well inside
    the range of defensible inputs. A budget line whose sign is not robust cannot be
    counted as an edge.
    """
    chain = FactorTiltChain(
        gross_long_short_premium_bp=660.0,
        post_publication_retention=0.42,
        long_only_capture=0.20,
        portfolio_exposure=0.20,
        incremental_fee_bp=20.0,
        incremental_trading_cost_bp=10.0,
    )
    assert chain.net_edge_bp < 0.0


# --------------------------------------------------------------------------------------
# The committed budget
# --------------------------------------------------------------------------------------


def test_every_budget_line_declares_a_mechanism_condition_and_falsifier() -> None:
    """A line without all three is an assertion, not a budget entry."""
    assert len(EDGE_BUDGET) == 7
    names = [item.name for item in EDGE_BUDGET]
    assert len(set(names)) == len(names)
    for item in EDGE_BUDGET:
        assert len(item.mechanism) > 40
        assert len(item.conditions) > 40
        assert len(item.falsifier) > 30


def test_budget_totals_by_benchmark_are_pinned() -> None:
    """The three totals, and the fact that they are never added together.

    Against the index the honest central estimate is 24.4 bp with a range spanning zero.
    Against the investor's own counterfactual it is 89 bp and almost all of it is
    contractual. The gap between those two rows is the practical finding of the study.
    """
    index = budget_for(Benchmark.STATED_INDEX)
    assert index.components == 3
    assert index.central_bp == pytest.approx(24.4, rel=0.0, abs=1e-9)
    assert index.low_bp == pytest.approx(-29.9, rel=0.0, abs=1e-9)
    assert index.high_bp == pytest.approx(101.0, rel=0.0, abs=1e-9)
    assert index.tracking_error_bp == pytest.approx(400.9152, rel=1e-6)

    counterfactual = budget_for(Benchmark.COUNTERFACTUAL_HOLDING)
    assert counterfactual.components == 3
    assert counterfactual.central_bp == pytest.approx(89.0, rel=0.0, abs=1e-9)
    assert counterfactual.tracking_error_bp == pytest.approx(41.231, rel=1e-4)

    average = budget_for(Benchmark.AVERAGE_INVESTOR)
    assert average.components == 1
    assert average.central_bp == pytest.approx(15.0, rel=0.0, abs=1e-9)


@pytest.mark.parametrize(
    ("benchmark", "expected"),
    [
        (Benchmark.STATED_INDEX, [0.5763, 0.6073, 0.6306, 0.6665]),
        (Benchmark.AVERAGE_INVESTOR, [0.6241, 0.6726, 0.7081, 0.7602]),
        (Benchmark.COUNTERFACTUAL_HOLDING, [1.0, 1.0, 1.0, 1.0]),
    ],
)
def test_attainable_probability_by_benchmark_and_horizon(
    benchmark: Benchmark, expected: list[float]
) -> None:
    """The deliverable, in one assertion.

    Beating the index is a 63% proposition after thirty years and does not improve much
    with waiting. Beating the portfolio the investor would otherwise have held is
    effectively certain, because most of that edge is contractual rather than statistical.
    """
    total = budget_for(benchmark)
    actual = [total.probability_of_outperformance(h) for h in (10.0, 20.0, 30.0, 50.0)]
    for value, target in zip(actual, expected, strict=True):
        assert value == pytest.approx(target, rel=0.0, abs=1e-4)


def test_the_index_relative_budget_range_spans_zero() -> None:
    """Low -29.9 bp, high +101 bp. A budget whose sign is not robust is not an edge."""
    index = budget_for(Benchmark.STATED_INDEX)
    assert index.low_bp < 0.0 < index.high_bp
    assert horizon_for_confidence(
        edge_bp=index.central_bp, tracking_error_bp=index.tracking_error_bp, confidence=0.90
    ) == pytest.approx(444.0, rel=1e-2)


def test_the_counterfactual_budget_reaches_high_confidence_within_months() -> None:
    """Contractual savings convert to near-certainty on a timescale a human can use."""
    total = budget_for(Benchmark.COUNTERFACTUAL_HOLDING)
    years = horizon_for_confidence(
        edge_bp=total.central_bp, tracking_error_bp=total.tracking_error_bp, confidence=0.99
    )
    assert years == pytest.approx(1.155, rel=1e-2)
    assert years * 12.0 < 15.0


def test_deterministic_lines_dominate_the_counterfactual_budget() -> None:
    """All three counterfactual lines are deterministic; two of three index lines are not."""
    counterfactual = [
        item for item in EDGE_BUDGET if item.benchmark is Benchmark.COUNTERFACTUAL_HOLDING
    ]
    assert all(item.certainty is Certainty.DETERMINISTIC for item in counterfactual)
    index = [item for item in EDGE_BUDGET if item.benchmark is Benchmark.STATED_INDEX]
    probabilistic = [item for item in index if item.certainty is Certainty.PROBABILISTIC]
    assert sum(item.central_bp for item in probabilistic) == pytest.approx(23.4, abs=1e-9)


def test_rebalancing_earns_less_than_a_small_cap_round_trip_costs() -> None:
    """2.4 bp/yr against a 2.72 bp published one-way spread on VB, as of 2026-08-10.

    Booked as a test because it is the decision the framework's rebalancing section leaves
    open: the policy's expected gain is smaller than the cost of executing it in the very
    sleeves where the excess growth rate is largest.
    """
    rebalancing = next(item for item in EDGE_BUDGET if item.name.startswith("Rebalancing"))
    small_cap_one_way_spread_bp = 2.72
    assert rebalancing.central_bp < small_cap_one_way_spread_bp
