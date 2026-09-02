"""The US/international split as a regret decision rather than an expected-return call.

``docs/research/search-coverage.md`` §6 asks that the split be resolved as a robustness
decision: regret across plausible futures rather than an expected-return winner that
history cannot identify. ``docs/research/valuation-and-the-allocation.md`` §5 has already
established the two facts that make a forecast unusable here. The cross-sectional relation
between relative valuation and relative return held for 120 years and is undetectable after
1990 on a design that could have found it, and a 10 pp shift needs 55 to 178 years to
demonstrate. What is left is a decision under stated priors, and this module writes it down
so that the split rests on a loss function and a scenario table instead of on a sentence.

Four ideas carry it.

**1. The return identity, with every input dated.** Over a horizon of ``T`` years the US
minus ex-US return differential decomposes as

    ``d = (y_US - y_X) + g + delta / T - c``

where ``y`` is the dividend yield, ``g`` the relative real per-share earnings growth, ``delta``
the change in the log of the relative valuation multiple over the horizon, and ``c`` the
currency leg's contribution to the unhedged ex-US dollar return. This is the decomposition
AQR uses for the realised 1990-2024 gap (4.7 pp/yr, of which 3.8 was ``delta``), turned
forward. Buybacks belong in ``g``, because a share repurchase raises per-share earnings and
does not appear in the dividend yield; the ``+1 pp`` growth scenario is where AQR puts the
US's century-average growth edge.

**2. Scenarios are predeclared, and the re-rating axis is anchored on a measured history.**
The relative multiple either holds, reverts halfway to its long-run median, reverts fully,
or re-rates further up by one standard deviation of the historical spread. The median and
the standard deviation come from the 150-year US-minus-panel log dividend-yield spread in
the Jordà-Schularick-Taylor panel, the only long cross-country valuation history in the
cache; the current reading is a CAPE ratio from a different source, so the anchor is an
assumption about comparability that :class:`Readings` states rather than hides.

**3. Terminal log wealth is the loss, and it is nearly linear in the split.** A constantly
rebalanced sleeve with US share ``s`` has log growth ``s d - var(s) / 2`` relative to the
ex-US level, and the variance term moves by about 2 bp/yr across the whole grid, because
the two markets are 77% correlated. Regret is therefore close to ``T |d| |s - s*|`` with
``s*`` at a grid corner, which has two consequences the surface makes visible: the
expected-regret split is a bang-bang bet on the sign of the expected differential, and the
minimax split is set by the scenario endpoints alone, exactly as
:func:`portfolio_edge.studies.trend_weight_regret.minimax_regret_weight` shows for the trend
weight. **Minimax replaces a forecast of the mean with a forecast of the endpoints.**

**4. Tracking error against the cap-weighted world is reported beside regret and never
added to it.** The two are different objects: regret is what a split costs in a future the
reader names, tracking error is what it costs in every future. The variance-minimising split
and the tracking-error-minimising split both sit at the cap weight, which is a measurement,
not a coincidence, and it is why the grid is centred where it is.

Nothing here is an experiment: no specification was frozen before the numbers were seen,
and the study is ``exploratory`` throughout. Because its scenario anchors, window and yield
readings are hypothesis-bearing choices, ``_global_split_regret_tables`` records each run in
the ledger through :class:`portfolio_edge.experiments.ledger.Ledger`. This module reads no
market data.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Literal

import numpy as np

__all__ = [
    "CURRENCY_LEGS",
    "EQUAL_PRIOR",
    "GROWTH_DIFFERENTIALS",
    "HORIZONS",
    "RERATING_STATES",
    "REVERSION_PRIOR",
    "SPLITS",
    "PriorSweepPoint",
    "Reading",
    "Readings",
    "RegretTable",
    "RelativeMoments",
    "ReratingPrior",
    "ReratingState",
    "Scenario",
    "bayes_split_sweep",
    "expected_differential",
    "growth_optimal_split",
    "implied_differential",
    "regret_table",
    "reversion_sweep_prior",
    "scenario_grid",
    "sleeve_log_growth",
    "tracking_error",
    "years_to_reach",
]

MONTHS_PER_YEAR: Final = 12

#: US share of the equity sleeve, the action grid. Regret is measured against the best
#: split *on this grid*, so the grid is part of the decision problem: an investor who would
#: never hold less than 40% US is not choosing among splits below it.
SPLITS: Final[tuple[float, ...]] = (0.80, 0.70, 0.65, 0.60, 0.55, 0.50, 0.40)

#: Horizons in years over which the re-rating is spread and terminal wealth is scored.
HORIZONS: Final[tuple[int, ...]] = (10, 30)

ReratingState = Literal["hold", "half", "full", "further"]

#: The four futures for the relative multiple, in the order the tables print them.
RERATING_STATES: Final[tuple[ReratingState, ...]] = ("hold", "half", "full", "further")

#: US minus ex-US real per-share earnings growth, decimal per year.
GROWTH_DIFFERENTIALS: Final[tuple[float, ...]] = (0.0, 0.01, -0.01)

#: The currency leg's contribution to the unhedged ex-US dollar return, decimal per year.
#: Zero is its measured mean; the sign convention is that ``+0.01`` helps ex-US.
CURRENCY_LEGS: Final[tuple[float, ...]] = (0.0, 0.01, -0.01)


# --------------------------------------------------------------------------------
# 1. The readings and the identity
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class Reading:
    """One dated input. ``as_of`` is the source's own date, not the retrieval date."""

    value: float
    as_of: str
    source: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Readings:
    """Every current input the identity needs, each with its date and source.

    ``relative_cape`` is US over developed ex-US inside one methodology.
    ``long_run_log_median`` and ``log_spread_sd`` describe the historical US-minus-panel
    log valuation spread the re-rating scenarios are anchored on. ``cap_weight_us`` is the
    US share of a cap-weighted global index, the neutral point tracking error is measured
    from.
    """

    us_dividend_yield: Reading
    ex_us_dividend_yield: Reading
    relative_cape: Reading
    long_run_log_median: Reading
    log_spread_sd: Reading
    cap_weight_us: Reading

    def __post_init__(self) -> None:
        if self.relative_cape.value <= 0.0:
            raise ValueError(f"relative CAPE must be positive, got {self.relative_cape.value}")
        if self.log_spread_sd.value < 0.0:
            raise ValueError("the spread's standard deviation cannot be negative")
        if not 0.0 < self.cap_weight_us.value < 1.0:
            raise ValueError(f"cap weight must lie in (0, 1), got {self.cap_weight_us.value}")

    @property
    def current_log_premium(self) -> float:
        """``log(relative CAPE)``: the US premium in the units the anchor is stated in."""
        return math.log(self.relative_cape.value)

    @property
    def yield_differential(self) -> float:
        """``y_US - y_X``, decimal per year; negative today."""
        return self.us_dividend_yield.value - self.ex_us_dividend_yield.value

    def rerating_log_change(self, state: ReratingState) -> float:
        """The change in the log relative multiple over the horizon under ``state``.

        Reversion is toward the long-run median of the spread; ``further`` adds one
        historical standard deviation to the current premium. The sign is the US's: a
        negative value is a US de-rating relative to ex-US.
        """
        gap = self.long_run_log_median.value - self.current_log_premium
        if state == "hold":
            return 0.0
        if state == "half":
            return 0.5 * gap
        if state == "full":
            return gap
        if state == "further":
            return self.log_spread_sd.value
        raise ValueError(f"unknown re-rating state {state!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class Scenario:
    """One cell of the predeclared grid."""

    rerating: ReratingState
    growth_differential: float
    currency_leg: float

    @property
    def label(self) -> str:
        return (
            f"{self.rerating}, growth {100 * self.growth_differential:+.0f} pp, "
            f"currency {100 * self.currency_leg:+.0f} pp"
        )


def scenario_grid(
    *,
    rerating: Sequence[ReratingState] = RERATING_STATES,
    growth: Sequence[float] = GROWTH_DIFFERENTIALS,
    currency: Sequence[float] = CURRENCY_LEGS,
) -> tuple[Scenario, ...]:
    """The full product, re-rating outermost so the tables group by it."""
    return tuple(
        Scenario(rerating=r, growth_differential=g, currency_leg=c)
        for r in rerating
        for g in growth
        for c in currency
    )


def implied_differential(readings: Readings, scenario: Scenario, *, horizon_years: float) -> float:
    """US minus ex-US log return per year implied by the identity, decimal.

    ``(y_US - y_X) + g + delta / T - c``. The re-rating is a log change spread evenly over
    the horizon; the yield and growth terms are small enough that their arithmetic and
    log versions agree to the second decimal of a basis point, so one set of units is used
    throughout rather than two.
    """
    if horizon_years <= 0.0:
        raise ValueError(f"horizon must be positive, got {horizon_years}")
    return (
        readings.yield_differential
        + scenario.growth_differential
        + readings.rerating_log_change(scenario.rerating) / horizon_years
        - scenario.currency_leg
    )


# --------------------------------------------------------------------------------
# 2. The sleeve's growth, its variance and its tracking error
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class RelativeMoments:
    """Annualised second moments of the two markets in dollars, with their window."""

    us_volatility: float
    ex_us_volatility: float
    correlation: float
    first_month: str
    last_month: str
    months: int

    def __post_init__(self) -> None:
        if self.us_volatility <= 0.0 or self.ex_us_volatility <= 0.0:
            raise ValueError("volatilities must be positive")
        if not -1.0 <= self.correlation <= 1.0:
            raise ValueError(f"correlation must lie in [-1, 1], got {self.correlation}")
        if self.months < 1:
            raise ValueError("a window needs at least one month")

    @property
    def covariance(self) -> float:
        return self.correlation * self.us_volatility * self.ex_us_volatility

    @property
    def relative_variance(self) -> float:
        """``var(r_US - r_X)``, the quantity every tracking error scales with."""
        return self.us_volatility**2 + self.ex_us_volatility**2 - 2.0 * self.covariance

    @property
    def relative_volatility(self) -> float:
        return math.sqrt(self.relative_variance)

    def sleeve_variance(self, split: float) -> float:
        """Variance of a sleeve holding ``split`` in US and the rest ex-US."""
        return (
            split**2 * self.us_volatility**2
            + (1.0 - split) ** 2 * self.ex_us_volatility**2
            + 2.0 * split * (1.0 - split) * self.covariance
        )

    @property
    def minimum_variance_split(self) -> float:
        """The split at which ``sleeve_variance`` is smallest, in closed form."""
        return (self.ex_us_volatility**2 - self.covariance) / self.relative_variance


def sleeve_log_growth(split: float, differential: float, moments: RelativeMoments) -> float:
    """Annual log growth of the rebalanced sleeve, relative to the ex-US level.

    ``s d - var(s) / 2``. The ex-US level itself is common to every split and so cancels
    in every regret; leaving it out keeps the function free of a forecast it does not need.
    """
    if not 0.0 <= split <= 1.0:
        raise ValueError(f"split must lie in [0, 1], got {split}")
    return split * differential - 0.5 * moments.sleeve_variance(split)


def tracking_error(split: float, moments: RelativeMoments, *, cap_weight_us: float) -> float:
    """Annualised tracking error of the split against the cap-weighted world, decimal.

    Exact for a two-asset sleeve: the active position is ``(s - w)`` long US and short
    ex-US, so its volatility is ``|s - w|`` times the relative volatility.
    """
    return abs(split - cap_weight_us) * moments.relative_volatility


def growth_optimal_split(expected_differential: float, moments: RelativeMoments) -> float:
    """The unconstrained growth-maximising split, **not** clipped to the grid.

    ``s* = s_minvar + E[d] / var(r_US - r_X)``. The slope is the reciprocal of the
    relative variance, about 85 points of split per percentage point of expected
    differential at the 1990-2026 moments, which is why the grid corner is the best split
    in nearly every scenario and why this number is reported: it says how far off the grid
    the log-wealth criterion wants to go, and therefore how little the criterion constrains.
    """
    return moments.minimum_variance_split + expected_differential / moments.relative_variance


# --------------------------------------------------------------------------------
# 3. Priors, kept visibly separate from every measurement
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class ReratingPrior:
    """A judgement over the four re-rating states; growth and currency stay uniform.

    The weights are a judgement and the only defensible thing to do with one is to write
    it down and show the answer's sensitivity to it, which :func:`bayes_split_sweep` does.
    """

    label: str
    weights: Mapping[ReratingState, float]

    def __post_init__(self) -> None:
        missing = [s for s in RERATING_STATES if s not in self.weights]
        if missing:
            raise ValueError(f"prior is missing states {missing}")
        if any(w < 0.0 for w in self.weights.values()):
            raise ValueError("prior weights cannot be negative")
        total = sum(self.weights.values())
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"prior weights must sum to 1, got {total}")

    def scenario_weights(self, scenarios: Sequence[Scenario]) -> tuple[float, ...]:
        """One weight per scenario: the state's weight shared equally within the state."""
        counts: dict[ReratingState, int] = {}
        for scenario in scenarios:
            counts[scenario.rerating] = counts.get(scenario.rerating, 0) + 1
        return tuple(self.weights[s.rerating] / counts[s.rerating] for s in scenarios)

    @property
    def reversion_weight(self) -> float:
        return self.weights["half"] + self.weights["full"]


EQUAL_PRIOR: Final = ReratingPrior(
    label="equal",
    weights={"hold": 0.25, "half": 0.25, "full": 0.25, "further": 0.25},
)

#: Tilted toward reversion: seven parts in ten on the two reversion states, one in ten on
#: further re-rating. The tilt is the size of the re-rating decomposition's own claim, that
#: a premium built from multiple expansion is the kind a reversal takes back.
REVERSION_PRIOR: Final = ReratingPrior(
    label="reversion-tilted",
    weights={"hold": 0.20, "half": 0.35, "full": 0.35, "further": 0.10},
)


def reversion_sweep_prior(reversion_weight: float) -> ReratingPrior:
    """Put ``reversion_weight`` on reversion, split equally between half and full, and the
    rest equally between hold and further. The one-parameter family the sensitivity uses."""
    if not 0.0 <= reversion_weight <= 1.0:
        raise ValueError(f"reversion weight must lie in [0, 1], got {reversion_weight}")
    rest = 1.0 - reversion_weight
    return ReratingPrior(
        label=f"reversion {reversion_weight:.2f}",
        weights={
            "hold": 0.5 * rest,
            "half": 0.5 * reversion_weight,
            "full": 0.5 * reversion_weight,
            "further": 0.5 * rest,
        },
    )


def expected_differential(
    readings: Readings,
    prior: ReratingPrior,
    *,
    horizon_years: float,
    scenarios: Sequence[Scenario] | None = None,
) -> float:
    """``E[d]`` under the prior, decimal per year."""
    grid = scenario_grid() if scenarios is None else tuple(scenarios)
    weights = prior.scenario_weights(grid)
    return float(
        sum(
            w * implied_differential(readings, s, horizon_years=horizon_years)
            for w, s in zip(weights, grid, strict=True)
        )
    )


# --------------------------------------------------------------------------------
# 4. The regret table
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class RegretTable:
    """Everything one horizon decides, so that a split cannot be quoted without its cost.

    ``regret`` is in terminal log wealth over the horizon: ``T (g* - g(s))``, where ``g*``
    is the best split's growth in that scenario. Divide by ``horizon_years`` for the annual
    figure; ``1 - exp(-regret)`` is the share of terminal wealth given up.
    """

    horizon_years: float
    splits: tuple[float, ...]
    scenarios: tuple[Scenario, ...]
    differentials: tuple[float, ...]
    growth: tuple[tuple[float, ...], ...]
    regret: tuple[tuple[float, ...], ...]
    best_split: tuple[float, ...]
    max_regret: tuple[float, ...]
    minimax_split: float
    minimax_regret: float
    tracking_error: tuple[float, ...]

    def column(self, scenario: Scenario) -> int:
        return self.scenarios.index(scenario)

    def row(self, split: float) -> int:
        return self.splits.index(split)

    def regret_at(self, split: float, scenario: Scenario) -> float:
        return self.regret[self.row(split)][self.column(scenario)]

    def expected_regret(self, prior: ReratingPrior) -> tuple[float, ...]:
        weights = prior.scenario_weights(self.scenarios)
        return tuple(float(np.dot(row, weights)) for row in self.regret)

    def bayes_split(self, prior: ReratingPrior) -> float:
        """The grid split with the smallest expected regret; ties go to the first listed."""
        expected = self.expected_regret(prior)
        return self.splits[int(np.argmin(expected))]

    def worst_scenario(self, split: float) -> Scenario:
        row = self.regret[self.row(split)]
        return self.scenarios[int(np.argmax(row))]


def regret_table(
    readings: Readings,
    moments: RelativeMoments,
    *,
    horizon_years: float,
    splits: Sequence[float] = SPLITS,
    scenarios: Sequence[Scenario] | None = None,
) -> RegretTable:
    """Growth and regret over ``splits x scenarios`` at one horizon, and the minimax split.

    Max regret is taken over every scenario rather than over an interval's endpoints,
    because the scenario set is a finite predeclared table; with growth nearly linear in
    the split the maximum sits at the most extreme differential of each sign anyway.
    """
    action = tuple(float(s) for s in splits)
    if not action:
        raise ValueError("splits must not be empty")
    if len(set(action)) != len(action):
        raise ValueError("splits must be distinct")
    grid = scenario_grid() if scenarios is None else tuple(scenarios)
    if not grid:
        raise ValueError("scenarios must not be empty")

    differentials = tuple(
        implied_differential(readings, s, horizon_years=horizon_years) for s in grid
    )
    growth = tuple(
        tuple(sleeve_log_growth(s, d, moments) for d in differentials) for s in action
    )
    best_growth = tuple(max(growth[i][j] for i in range(len(action))) for j in range(len(grid)))
    best_split = tuple(
        action[int(np.argmax([growth[i][j] for i in range(len(action))]))]
        for j in range(len(grid))
    )
    regret = tuple(
        tuple(horizon_years * (best_growth[j] - row[j]) for j in range(len(grid)))
        for row in growth
    )
    max_regret = tuple(max(row) for row in regret)
    minimax_index = int(np.argmin(max_regret))
    return RegretTable(
        horizon_years=float(horizon_years),
        splits=action,
        scenarios=grid,
        differentials=differentials,
        growth=growth,
        regret=regret,
        best_split=best_split,
        max_regret=max_regret,
        minimax_split=action[minimax_index],
        minimax_regret=max_regret[minimax_index],
        tracking_error=tuple(
            tracking_error(s, moments, cap_weight_us=readings.cap_weight_us.value)
            for s in action
        ),
    )


# --------------------------------------------------------------------------------
# 5. Sensitivity to the prior
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class PriorSweepPoint:
    reversion_weight: float
    expected_differential: float
    unconstrained_split: float
    bayes_split: float


def bayes_split_sweep(
    table: RegretTable,
    readings: Readings,
    moments: RelativeMoments,
    *,
    reversion_weights: Sequence[float],
) -> tuple[PriorSweepPoint, ...]:
    """The expected-regret split as the prior weight on reversion moves.

    Two answers per point, because they say different things. ``bayes_split`` is the grid
    answer, which steps between corners where ``E[d]`` changes sign. ``unconstrained_split``
    is the closed-form growth optimum, which moves continuously and is what "points of
    split per unit of prior weight" is measured on; that it leaves the grid almost at once
    is the finding, not a defect of the grid.
    """
    points = []
    for weight in reversion_weights:
        prior = reversion_sweep_prior(weight)
        expected = expected_differential(
            readings, prior, horizon_years=table.horizon_years, scenarios=table.scenarios
        )
        points.append(
            PriorSweepPoint(
                reversion_weight=float(weight),
                expected_differential=expected,
                unconstrained_split=growth_optimal_split(expected, moments),
                bayes_split=table.bayes_split(prior),
            )
        )
    return tuple(points)


# --------------------------------------------------------------------------------
# 6. Implementation by contributions only
# --------------------------------------------------------------------------------


def years_to_reach(
    *,
    current_us_share: float,
    target_us_share: float,
    contribution_rate: float,
    share_of_contributions: float = 1.0,
) -> float:
    """Years of contributions, growth ignored, to move the sleeve from one split to another.

    Every contributed dollar that reaches the equity sleeve goes to the side that is
    under-weight against the target; ``share_of_contributions`` is the fraction of the
    year's contribution ``contribution_rate x balance`` that does so, the rest holding the
    remainder of the vector at its targets. With ``a`` the under-weight side's current
    share and ``t`` its target, ``a / (1 + k) + k / (1 + k) = t`` gives
    ``k = (t - a) / (1 - t)`` in units of the starting balance, and the years are
    ``k / (rate x share)``. Zero when the target is already held.
    """
    for name, value in (
        ("current_us_share", current_us_share),
        ("target_us_share", target_us_share),
    ):
        if not 0.0 < value < 1.0:
            raise ValueError(f"{name} must lie in (0, 1), got {value}")
    if contribution_rate <= 0.0 or share_of_contributions <= 0.0:
        raise ValueError("contribution rate and share must be positive")
    if math.isclose(current_us_share, target_us_share, abs_tol=1e-12):
        return 0.0
    if target_us_share < current_us_share:
        held, target = 1.0 - current_us_share, 1.0 - target_us_share
    else:
        held, target = current_us_share, target_us_share
    added = (target - held) / (1.0 - target)
    return added / (contribution_rate * share_of_contributions)


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._global_split_regret_tables import main

    main()
