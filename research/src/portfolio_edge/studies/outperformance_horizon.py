"""How long an edge takes to become visible, and the edge budget it is applied to.

Two ideas, deliberately kept in one module because separating them is how the
dishonest version of this argument is usually made.

**The horizon arithmetic.** If a portfolio's log return exceeds a benchmark's by
``e`` per year with tracking error ``s`` per year, and the annual relative returns are
independent, then the cumulative log relative return after ``T`` years is
``N(e T, s**2 T)`` and

    P(outperform) = Phi( e sqrt(T) / s ),   T(confidence) = ( z s / e )**2 .

The horizon scales with the **square** of the ratio ``s / e``. Halving the edge
quadruples the time. This is the single most important number in the study and it is
elementary.

**The certainty class.** ``s`` is not a property of the edge, it is a property of the
edge *relative to its benchmark*. A contractual saving — a lower fee on the same
index fund — has ``s`` of a few basis points, so it converts to near-certainty
immediately. A risk premium harvested by a factor tilt has ``s`` of several hundred
basis points against a broad index, so it does not converge inside a human lifetime.
Adding them into one number is exactly the mistake this module refuses to make: the
budget carries a benchmark and a certainty class per line, and the aggregate is only
computed within a benchmark.

The three benchmarks in :class:`Benchmark` are not interchangeable, and conflating them
is the most common way an edge budget is inflated. Beating *the average investor* is a
different and much easier claim than beating *the index*, and no line item may be
counted against both.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum

from scipy.stats import norm

BASIS_POINT = 1e-4


class Certainty(Enum):
    """Whether a line item is an identity or a bet."""

    DETERMINISTIC = "deterministic"
    """An accounting identity or a contractual saving. Realised with near-certainty
    against its own benchmark; its only uncertainty is in the size of the input, not in
    the sign of the outcome."""

    PROBABILISTIC = "probabilistic"
    """A risk premium, a forecast, or a policy whose payoff depends on the path. The
    sign of the realised outcome is not known in advance at any human horizon."""


class Benchmark(Enum):
    """What the line item is measured against. These never aggregate across classes."""

    STATED_INDEX = "stated_index"
    """A cheap investable index of the same asset class, measured gross of the
    investor's own costs. This is the hard benchmark and the one "beat the market"
    normally means."""

    AVERAGE_INVESTOR = "average_investor"
    """The dollar-weighted holdings or realised experience of the average investor in
    the same asset class. Easier, and a legitimate benchmark only if stated as such."""

    COUNTERFACTUAL_HOLDING = "counterfactual_holding"
    """The same investor's plausible alternative product or account choice. A saving
    against a decision they might otherwise have made, not a return against a market."""


@dataclass(frozen=True)
class EdgeComponent:
    """One line of the budget, with everything needed to audit or reject it."""

    name: str
    mechanism: str
    benchmark: Benchmark
    certainty: Certainty
    low_bp: float
    central_bp: float
    high_bp: float
    tracking_error_bp: float
    conditions: str
    falsifier: str

    def __post_init__(self) -> None:
        if not self.low_bp <= self.central_bp <= self.high_bp:
            raise ValueError(
                f"{self.name}: require low <= central <= high, got "
                f"{self.low_bp}, {self.central_bp}, {self.high_bp}"
            )
        if self.tracking_error_bp < 0.0:
            raise ValueError(f"{self.name}: tracking error cannot be negative")
        if self.certainty is Certainty.DETERMINISTIC and self.low_bp < 0.0:
            raise ValueError(
                f"{self.name}: a deterministic component cannot have a negative low "
                "estimate; if the sign is in doubt it is probabilistic"
            )
        if not self.falsifier.strip():
            raise ValueError(f"{self.name}: every component needs a falsifier")


@dataclass(frozen=True)
class AggregateEdge:
    """A budget total for one benchmark, with its combined tracking error."""

    benchmark: Benchmark
    components: int
    low_bp: float
    central_bp: float
    high_bp: float
    tracking_error_bp: float

    def probability_of_outperformance(self, horizon_years: float) -> float:
        return probability_of_outperformance(
            edge_bp=self.central_bp,
            tracking_error_bp=self.tracking_error_bp,
            horizon_years=horizon_years,
        )


def probability_of_outperformance(
    *, edge_bp: float, tracking_error_bp: float, horizon_years: float
) -> float:
    """``Phi(e sqrt(T) / s)``: probability the cumulative relative log return is positive.

    Assumes annual relative log returns are independent with constant mean and
    variance. Both assumptions flatter the answer: relative returns of real strategies
    are autocorrelated and their edge is itself estimated, and a point estimate of ``e``
    treated as known removes the dominant source of uncertainty. Read the output as an
    upper bound on attainable confidence.

    A zero tracking error is the contractual case and returns 1.0 for any positive edge,
    which is correct and is the whole reason cost reduction dominates this budget.
    """
    if horizon_years <= 0.0:
        raise ValueError(f"horizon_years must be positive, got {horizon_years}")
    if tracking_error_bp < 0.0:
        raise ValueError("tracking_error_bp cannot be negative")
    if tracking_error_bp == 0.0:
        return 1.0 if edge_bp > 0.0 else (0.0 if edge_bp < 0.0 else 0.5)
    return float(norm.cdf(edge_bp * math.sqrt(horizon_years) / tracking_error_bp))


def horizon_for_confidence(
    *, edge_bp: float, tracking_error_bp: float, confidence: float
) -> float:
    """Years until ``P(outperform)`` reaches ``confidence``: ``T = (z s / e)**2``."""
    if edge_bp <= 0.0:
        raise ValueError("edge_bp must be positive")
    if tracking_error_bp < 0.0:
        raise ValueError("tracking_error_bp cannot be negative")
    if not 0.5 <= confidence < 1.0:
        raise ValueError(f"confidence must lie in [0.5, 1), got {confidence}")
    z = float(norm.ppf(confidence))
    return (z * tracking_error_bp / edge_bp) ** 2


def detectable_edge_bp(
    *, tracking_error_bp: float, horizon_years: float, confidence: float
) -> float:
    """The smallest edge that reaches ``confidence`` within ``horizon_years``.

    ``e = z s / sqrt(T)``. Read the other way round, this says what an investor with a
    given tracking-error budget and lifetime could ever hope to demonstrate — which is
    usually far more than any plausible edge, and is why "wait and see" is not a
    validation strategy.
    """
    if horizon_years <= 0.0:
        raise ValueError("horizon_years must be positive")
    if not 0.5 <= confidence < 1.0:
        raise ValueError(f"confidence must lie in [0.5, 1), got {confidence}")
    return float(norm.ppf(confidence)) * tracking_error_bp / math.sqrt(horizon_years)


def terminal_wealth_ratio(*, edge_bp: float, horizon_years: float) -> float:
    """``exp(e T)``: terminal wealth with the edge, over terminal wealth without it.

    The one figure in this module that needs **no forecast of any market**. Both paths
    are the same portfolio exposed to the same returns; the edge is an addition to the
    log growth rate, so the market term cancels out of the ratio exactly and what
    survives depends only on the edge and the horizon.

    That is what makes a contractual edge worth quoting to an investor and a risk premium
    not. This ratio is realised with the certainty of its own inputs; the same
    calculation applied to a probabilistic line would be quoting a median as though it
    were a promise, so pair it with
    :func:`probability_of_outperformance` and never report it alone for a line whose
    ``Certainty`` is ``PROBABILISTIC``.

    Convention: ``edge_bp`` is a **log** growth rate in basis points a year, which is how
    :class:`EdgeComponent` and :mod:`tax_structure` both carry it. Compounding
    ``(1 + e)**T`` instead would understate this slightly and mix simple with log
    conventions in the same budget.
    """
    if horizon_years < 0.0:
        raise ValueError(f"horizon_years cannot be negative, got {horizon_years}")
    return math.exp(edge_bp * BASIS_POINT * horizon_years)


def aggregate(components: Iterable[EdgeComponent]) -> AggregateEdge:
    """Sum a set of components sharing one benchmark, combining tracking errors in quadrature.

    Raises if the components do not share a benchmark, because summing across benchmarks
    is the double-counting error this module is built to prevent. The quadrature rule
    assumes the components' relative returns are mutually independent, which is an
    **assumption** and an optimistic one: a factor tilt and a rebalancing policy applied
    to the same portfolio share the same equity beta and the same crisis.
    """
    items = list(components)
    if not items:
        raise ValueError("cannot aggregate an empty budget")
    benchmarks = {item.benchmark for item in items}
    if len(benchmarks) != 1:
        raise ValueError(
            "components must share one benchmark; got "
            + ", ".join(sorted(b.value for b in benchmarks))
        )
    return AggregateEdge(
        benchmark=items[0].benchmark,
        components=len(items),
        low_bp=sum(item.low_bp for item in items),
        central_bp=sum(item.central_bp for item in items),
        high_bp=sum(item.high_bp for item in items),
        tracking_error_bp=math.sqrt(sum(item.tracking_error_bp**2 for item in items)),
    )


# ``FactorTiltChain`` lived here and is deleted. It multiplied a gross long-short premium
# by a post-publication retention, a long-only capture fraction and a portfolio exposure.
# Two of those four terms are now known to be wrong rather than uncertain: a capture
# fraction *is* an HML loading, so multiplying one by a fund's loading discounts the same
# exposure twice, and the premium this budget quotes is already post-publication, so a
# retention factor decays it a second time. See
# ``docs/research/long-only-capture.md`` identity (C).
# :mod:`portfolio_edge.studies.value_tilt` replaces it.


def probability_table(
    *,
    edge_bp: float,
    tracking_error_bp: float,
    horizons: Sequence[float] = (5.0, 10.0, 20.0, 30.0, 50.0),
) -> list[tuple[float, float]]:
    """``[(horizon, probability), ...]`` for one edge and tracking error."""
    return [
        (
            horizon,
            probability_of_outperformance(
                edge_bp=edge_bp, tracking_error_bp=tracking_error_bp, horizon_years=horizon
            ),
        )
        for horizon in horizons
    ]


# --------------------------------------------------------------------------------------
# The budget itself
# --------------------------------------------------------------------------------------
#
# Every magnitude below is sourced in docs/research/expected-edge-decomposition.md next
# to the claim it supports. Nothing here is a forecast of a market; the deterministic
# lines are contractual arithmetic and the probabilistic lines are heavily shrunk priors
# whose sign is not known in advance.
#
# Tracking errors are the annual standard deviation of the line's return *against its own
# benchmark*, and they are estimates rather than measurements. They are stated because
# leaving them implicit is what makes a budget look decisive when it is not.

COST_REDUCTION = EdgeComponent(
    name="Fund cost reduction",
    mechanism=(
        "Hold a broad index fund at an asset-weighted 9 bp rather than the average "
        "actively managed equity dollar at 57-58 bp. Sharpe's arithmetic makes the "
        "gross returns equal in aggregate, so the fee difference is the whole edge."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    low_bp=40.0,
    central_bp=49.0,
    high_bp=59.0,
    tracking_error_bp=0.0,
    conditions=(
        "The investor would otherwise have held actively managed funds at the "
        "asset-weighted average fee. Nothing is available to an investor already in "
        "index funds."
    ),
    falsifier=(
        "Published asset-weighted expense ratios converge, or the active funds the "
        "investor would actually have held charge index-fund fees."
    ),
)

BEHAVIOURAL_TIMING = EdgeComponent(
    name="Timing / behaviour gap avoided",
    mechanism=(
        "Do not move money between funds in response to past performance. Measured as "
        "the difference between a fund's time-weighted return and its investors' "
        "dollar-weighted return, after removing the hindsight component."
    ),
    benchmark=Benchmark.AVERAGE_INVESTOR,
    certainty=Certainty.PROBABILISTIC,
    low_bp=5.0,
    central_bp=15.0,
    high_bp=60.0,
    tracking_error_bp=150.0,
    conditions=(
        "Available only to an investor who would otherwise have chased performance. "
        "The headline 120 bp vendor figure is mostly a hindsight artefact, not timing."
    ),
    falsifier=(
        "A dollar-weighted study that decomposes the gap into timing and hindsight "
        "components and attributes most of it to timing."
    ),
)

REBALANCING_POLICY = EdgeComponent(
    name="Rebalancing, net of diversification",
    mechanism=(
        "Hold constant weights rather than letting them drift, against a cap-weighted "
        "index of the same assets, which is itself the drifting portfolio. The edge is "
        "the excess growth rate less what buy-and-hold captures over the horizon."
    ),
    benchmark=Benchmark.STATED_INDEX,
    certainty=Certainty.PROBABILISTIC,
    low_bp=-62.9,
    central_bp=-38.7,
    high_bp=2.4,
    tracking_error_bp=27.0,
    conditions=(
        "This line's own falsifier has fired and the central value is the measured "
        "result, not the closed form. The equal-drift closed form gives +2.4 bp/yr and "
        "is retained as `high` because it is the ceiling this line can reach: it "
        "requires the components' true growth rates to differ by less than the "
        "portfolio's excess growth rate. Over 1991-2025 they did not. US against "
        "developed ex-US ran a drift gap of 4.34 pp/yr against a `gamma_star` of 12.5 "
        "bp, a factor of 35, and the extended closed form predicts -70.5 bp/yr against "
        "a realised -62.9. Central is the realised 60/30/10 portfolio figure over 420 "
        "months; low is the worst realised pair. The tracking error is the effective "
        "annual figure that reproduces P = 0.691 at 30 years; the true noise is "
        "O(sqrt(T)), not O(T)."
    ),
    falsifier=(
        "FIRED. A drift gap above the excess growth rate, measured at ~35x on the "
        "deciding pair (Experiment 003). The line is retained because the mechanism is "
        "exact and the sign reverses when drifts converge -- on 1963-2020 sixteen-country "
        "data the same arithmetic gives +17.9 bp/yr -- so this is a verdict about a "
        "35-year window in which one region ran away, not about the mechanism."
    ),
)

FACTOR_TILT = EdgeComponent(
    name="Factor tilt",
    mechanism=(
        "Move 20% of the portfolio out of a total-market fund and into a systematic "
        "value fund. What reaches the investor is the difference in the two funds' HML "
        "loadings times the premium, less the difference in their costs: "
        "0.20 x (0.537 - 0.025) x 4.74 pp/yr - 0.20 x 0.271 pp/yr. There is no capture "
        "term, because a capture fraction is itself an HML loading."
    ),
    benchmark=Benchmark.STATED_INDEX,
    certainty=Certainty.PROBABILISTIC,
    low_bp=-28.8,
    central_bp=43.1,
    high_bp=77.5,
    tracking_error_bp=311.8,
    conditions=(
        "Requires the factor to be true and to survive publication. The range is the "
        "premium and nothing else: -28.8 bp is the US post-publication premium's lower "
        "bound of -2.28 pp/yr and +77.5 bp the pooled premium's upper bound of +8.10. "
        "Only about half of the central figure survives into geometric growth, because "
        "the swap raises portfolio variance."
    ),
    falsifier=(
        "The tilt's realised premium net of its incremental cost is negative over a "
        "predeclared out-of-sample window, or the fund's HML loading falls materially "
        "below the +0.537 measured over 2020-01..2025-12."
    ),
)

SECURITIES_LENDING = EdgeComponent(
    name="Securities-lending pass-through",
    mechanism=(
        "The fund lends its holdings and returns the net revenue to shareholders, so a "
        "tracking fund can earn slightly more than the index itself. The decomposition "
        "is fund bp = loan fee x utilisation x keep rate, and utilisation is what "
        "separates large-cap from small-cap."
    ),
    benchmark=Benchmark.STATED_INDEX,
    certainty=Certainty.DETERMINISTIC,
    low_bp=0.1,
    central_bp=1.0,
    high_bp=3.0,
    tracking_error_bp=2.0,
    conditions=(
        "Broad total-market or all-cap developed equity, computed from fund filings. A "
        "pure S&P 500 mandate earns 0.1-0.3 bp; small-cap earns 3-10 bp and micro-cap "
        "far more, but the investor then also bears the segment's own risk. The income "
        "is ordinary income in a taxable account, and SPY cannot lend at all."
    ),
    falsifier=(
        "The fund's own annual report shows securities-lending income below the stated "
        "range as a fraction of average net assets, or the manager retains the split."
    ),
)

TAX_LOSS_HARVESTING = EdgeComponent(
    name="Tax-loss harvesting",
    mechanism=(
        "Realise losses at the individual-security level to offset gains elsewhere, "
        "deferring tax and arbitraging the short-term against the long-term rate."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    low_bp=0.0,
    central_bp=30.0,
    high_bp=90.0,
    tracking_error_bp=40.0,
    conditions=(
        "US taxable account with direct security ownership. A fund or index ETF cannot "
        "pass security-level losses through, so this is unavailable to an ETF holder. "
        "Requires realised gains elsewhere to absorb the losses, and decays towards "
        "zero within about five years unless new money keeps arriving."
    ),
    falsifier=(
        "A no-contribution portfolio whose measured after-liquidation tax alpha reaches "
        "zero, or an investor with no offsetting gains, or a flat capital-gains rate."
    ),
)

ASSET_LOCATION = EdgeComponent(
    name="Asset location",
    mechanism=(
        "Place tax-inefficient assets in tax-deferred accounts and tax-efficient ones "
        "in taxable accounts rather than holding the same mix in every account."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    low_bp=0.0,
    central_bp=10.0,
    high_bp=21.0,
    tracking_error_bp=10.0,
    conditions=(
        "Requires meaningful balances in more than one account type and a jurisdiction "
        "whose rates differ by asset class. No peer-reviewed source states a per-year "
        "figure at all; the high figure is an annualisation of a 30-year "
        "certainty-equivalent result and is an inference, not a published number."
    ),
    falsifier=(
        "A study measuring after-tax return against a uniform-location benchmark and "
        "finding no reliable advantage, or a jurisdiction with a single rate."
    ),
)

EDGE_BUDGET: tuple[EdgeComponent, ...] = (
    COST_REDUCTION,
    TAX_LOSS_HARVESTING,
    ASSET_LOCATION,
    BEHAVIOURAL_TIMING,
    REBALANCING_POLICY,
    SECURITIES_LENDING,
    FACTOR_TILT,
)
"""The committed budget. Add a line only with a source, a condition and a falsifier."""


def budget_for(benchmark: Benchmark) -> AggregateEdge:
    """Aggregate only the lines measured against ``benchmark``."""
    return aggregate(item for item in EDGE_BUDGET if item.benchmark is benchmark)
