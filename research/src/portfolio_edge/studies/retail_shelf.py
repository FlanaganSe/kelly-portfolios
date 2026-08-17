"""The four families a retail investor is pointed at first, and how to score them.

Why this module exists
----------------------
``docs/research/alternative-sleeves-audit.md`` audited catastrophe bonds, merger
arbitrage, closed-end funds, option-income funds and securities lending. Together
with the factor and managed-futures work it covers 69 factor ETFs, 15 managed-futures
ETFs, 8 capital-efficient overlays, commodities and gold. It had never opened the four
families a retail investor actually meets first: **dividend and dividend-growth funds,
REITs, buffer / defined-outcome funds, and spot bitcoin**. This module is the arithmetic
that scores them, and it is deliberately not the same arithmetic for all four.

**The instrument is chosen by the correlation, and choosing it wrongly is the mistake
this repository has already made twice.**

:mod:`portfolio_edge.studies.overlay_growth` states both halves. Equation (4),
``S_d > L rho sigma_p``, is a *first-order* admission condition at ``w = 0``; above
roughly ``|rho| = 0.5`` almost all of a sleeve's marginal contribution is alpha, the
first-order term is a small difference of large numbers, and the test mis-scores. That
is how a put-writing index with a measured CAPM alpha of ``-0.09%/yr`` read as a pass.
Equation (5) is the control that decides: at matched volatility the ``-V/2`` terms are
identical by construction, so **the higher Sharpe ratio wins and nothing else matters**.

The other error was the mirror image: commodities were called *rejected* by comparing a
Sharpe ratio of 0.27 against a correlation of 0.286, when the threshold ``L rho sigma_p``
was 0.067 and they cleared it by +0.107. The corrected verdict was "dominated, not
rejected".

So :func:`choose_instrument` is a function rather than a paragraph. A caller cannot score
a family here without the module recording which instrument it used and why, and
:class:`InstrumentChoice` carries that reason into every table.

    ============================  =========================================
    ``|rho| <= 0.5``              equation (4), :func:`admission` in
                                  :mod:`portfolio_edge.studies.factor_breadth`
    ``|rho| > 0.5``               equation (5), :func:`matched_volatility`
    ============================  =========================================

Dividend funds and REITs are long-only equity portfolios and sit far above the limit;
they are scored by equation (5) and equation (4) is not reported for them at all.
Bitcoin sits far below it and is scored by equation (4), with equation (5) beside it.
Buffer funds are equity in an option wrapper and sit above the limit, so they get
equation (5) plus the payoff decomposition in section 3, which is where their mechanism
actually is.

**What equation (5) does and does not settle.** It compares two portfolios held at the
same volatility, so it cannot be gamed by leverage and it needs no expected-return
forecast beyond the two realised means. It is still a *realised* comparison over one
window, and a window that cannot resolve the gap has not shown the gap is zero — which
is why every estimate here carries :func:`minimum_detectable_effect` beside it.

Nothing in this module reads market data or touches the cache;
:mod:`portfolio_edge.studies._retail_shelf_tables` is the one file that does.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.inference.hac import hac_mean, hac_ols
from portfolio_edge.studies.factor_breadth import (
    FIRST_ORDER_CORRELATION_LIMIT,
    MONTHS_PER_YEAR,
    minimum_detectable_effect,
)

__all__ = [
    "FIRST_ORDER_CORRELATION_LIMIT",
    "MONTHS_PER_YEAR",
    "BufferTerms",
    "FactorRegression",
    "Instrument",
    "InstrumentChoice",
    "MatchedVolatilityVerdict",
    "PiecewiseBeta",
    "buffer_cost_decomposition",
    "buffer_payoff",
    "choose_instrument",
    "factor_regression",
    "matched_volatility",
    "piecewise_beta",
    "sharpe_ratio",
]

_Z_TWO_SIDED_95: Final = 1.959963984540054


def _as_series(values: Sequence[float] | FloatArray, name: str = "series") -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {array.shape}")
    if array.size < 2:
        raise ValueError(f"{name} needs at least two observations, got {array.size}")
    if not np.all(np.isfinite(array)):
        raise ValueError(
            f"{name} contains a non-finite value. Missing months must be dropped by "
            "the caller, with the window it kept stated, rather than filled here."
        )
    return array


def sharpe_ratio(
    excess_returns: Sequence[float] | FloatArray, *, periods_per_year: int = MONTHS_PER_YEAR
) -> float:
    """Annualised arithmetic Sharpe ratio of an excess-return series.

    Arithmetic mean over sample standard deviation, both scaled to a year. Not
    geometric: equations (4) and (5) are both statements about the first moment of an
    excess return, and a geometric Sharpe would be a different quantity in the same
    slot.
    """
    values = _as_series(excess_returns, "excess_returns")
    volatility = float(np.std(values, ddof=1))
    if volatility <= 0.0:
        raise ValueError("excess returns have zero volatility; a Sharpe ratio is undefined")
    return float(np.mean(values)) / volatility * math.sqrt(periods_per_year)


# --------------------------------------------------------------------------------
# 1. Which instrument, and why
# --------------------------------------------------------------------------------

Instrument = Literal["admission_equation_4", "matched_volatility_equation_5"]


@dataclass(frozen=True)
class InstrumentChoice:
    """Which of the two scoring rules applies to a sleeve, and the reason.

    ``reason`` is written for a reader of the finished table, not for a log. It exists
    because the deliverable this module feeds is required to state, for every family,
    which instrument scored it and why — and a reason regenerated from the correlation
    each time cannot drift away from the number that produced it.
    """

    label: str
    correlation: float
    instrument: Instrument
    reason: str

    @property
    def first_order_admission_is_usable(self) -> bool:
        return self.instrument == "admission_equation_4"


def choose_instrument(*, label: str, correlation: float) -> InstrumentChoice:
    """Pick equation (4) or equation (5) from the sleeve's correlation to the base.

    The boundary is :data:`FIRST_ORDER_CORRELATION_LIMIT`, imported from
    :mod:`portfolio_edge.studies.factor_breadth` rather than restated, so the whole
    repository has one number for it.

    **Equation (5) is always admissible; equation (4) is not.** A caller who wants both
    may compute both, but at ``|rho| > 0.5`` the admission margin is a diagnostic and
    never a verdict, and this function refuses to describe it as one.
    """
    if not -1.0 <= correlation <= 1.0:
        raise ValueError(f"correlation must lie in [-1, 1], got {correlation}")
    if abs(correlation) <= FIRST_ORDER_CORRELATION_LIMIT:
        return InstrumentChoice(
            label=label,
            correlation=correlation,
            instrument="admission_equation_4",
            reason=(
                f"|rho| = {abs(correlation):.3f} is inside the "
                f"{FIRST_ORDER_CORRELATION_LIMIT:.1f} limit at which the first-order "
                "condition S_d > L rho sigma_p stops being a usable test, so equation "
                "(4) decides and the matched-volatility control is reported beside it"
            ),
        )
    return InstrumentChoice(
        label=label,
        correlation=correlation,
        instrument="matched_volatility_equation_5",
        reason=(
            f"|rho| = {abs(correlation):.3f} exceeds the "
            f"{FIRST_ORDER_CORRELATION_LIMIT:.1f} limit, where equation (4) is a small "
            "difference of large numbers and mis-scores a sleeve that is mostly the "
            "base in disguise — the put-writing failure. Equation (5) decides: at "
            "matched volatility the variance terms cancel and the higher Sharpe wins"
        ),
    )


# --------------------------------------------------------------------------------
# 2. Equation (5), on realised data, with its own detection floor
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchedVolatilityVerdict:
    """The sleeve against the base held at the same volatility — equation (5).

    ``growth_gap`` is ``sigma_target * (S_d - S_p)`` in pp/yr of geometric growth, and
    it is *exactly* the annualised mean of the paired series
    ``z_t = (sigma_target / sigma_d) d_t - (sigma_target / sigma_p) p_t``. That identity
    is what licenses a HAC standard error here: both legs are rescaled to the same
    sample volatility, so the ``-V/2`` terms in ``g = r + A - V/2`` are identical by
    construction and the growth difference collapses to a difference of means.

    ``resolved`` is the field to read before the sign. A gap below its own
    :func:`minimum_detectable_effect` is a statement about the window, not about the
    sleeve.
    """

    label: str
    months: int
    sleeve_sharpe: float
    base_sharpe: float
    sleeve_volatility: float
    base_volatility: float
    target_volatility: float
    growth_gap: float
    hac_standard_error: float
    t_statistic: float
    interval_low: float
    interval_high: float
    mde_80: float

    @property
    def sharpe_gap(self) -> float:
        return self.sleeve_sharpe - self.base_sharpe

    @property
    def wins(self) -> bool:
        """Whether the sleeve's Sharpe ratio beats the base's. Equation (5)'s verdict."""
        return self.sleeve_sharpe > self.base_sharpe

    @property
    def resolved(self) -> bool:
        """Whether the window could have detected a gap this size at 80% power."""
        return abs(self.growth_gap) > self.mde_80


def matched_volatility(
    sleeve_excess: Sequence[float] | FloatArray,
    base_excess: Sequence[float] | FloatArray,
    *,
    label: str,
    target_volatility: float | None = None,
    periods_per_year: int = MONTHS_PER_YEAR,
    n_lags: int | None = None,
) -> MatchedVolatilityVerdict:
    """Score a sleeve against the base levered to the same volatility.

    Both series are **excess of the same cash rate** and must be aligned on the same
    months; ragged inputs are refused rather than pairwise-completed, because the
    comparison is meaningless across different windows.

    ``target_volatility`` defaults to the base's own realised annual volatility, which
    makes the comparison "the sleeve, levered or delevered to the base's risk, against
    the base as held". Any other target scales both legs identically and moves the gap
    proportionally, so the sign and the significance are invariant to it.

    This is the *substitution* form of equation (5): it asks whether holding the sleeve
    instead of the base would have raised growth. For a sleeve to be held *beside* the
    base at some weight, use
    :func:`portfolio_edge.studies.overlay_growth.matched_volatility_verdict`, which
    takes forecasts rather than a realised pair.
    """
    sleeve = _as_series(sleeve_excess, "sleeve_excess")
    base = _as_series(base_excess, "base_excess")
    if sleeve.size != base.size:
        raise ValueError(
            f"sleeve has {sleeve.size} observations and base has {base.size}; align "
            "them on a common window and state the window rather than comparing "
            "different periods"
        )
    scale = math.sqrt(periods_per_year)
    sleeve_volatility = float(np.std(sleeve, ddof=1)) * scale
    base_volatility = float(np.std(base, ddof=1)) * scale
    if sleeve_volatility <= 0.0 or base_volatility <= 0.0:
        raise ValueError("both series must have positive volatility to match them")
    target = base_volatility if target_volatility is None else float(target_volatility)
    if target <= 0.0:
        raise ValueError(f"target volatility must be positive, got {target}")

    paired = (target / sleeve_volatility) * sleeve - (target / base_volatility) * base
    estimate = hac_mean(paired, n_lags=n_lags)
    gap = float(periods_per_year) * estimate.mean
    error = float(periods_per_year) * estimate.standard_error
    return MatchedVolatilityVerdict(
        label=label,
        months=int(sleeve.size),
        sleeve_sharpe=sharpe_ratio(sleeve, periods_per_year=periods_per_year),
        base_sharpe=sharpe_ratio(base, periods_per_year=periods_per_year),
        sleeve_volatility=sleeve_volatility,
        base_volatility=base_volatility,
        target_volatility=target,
        growth_gap=gap,
        hac_standard_error=error,
        t_statistic=(
            estimate.mean / estimate.standard_error if estimate.standard_error > 0.0 else 0.0
        ),
        interval_low=gap - _Z_TWO_SIDED_95 * error,
        interval_high=gap + _Z_TWO_SIDED_95 * error,
        mde_80=minimum_detectable_effect(error),
    )


# --------------------------------------------------------------------------------
# 3. Is the record a strategy, or a set of loadings?
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class FactorRegression:
    """One sleeve's excess return on a set of factors, with HAC standard errors.

    ``alpha`` is annualised; the loadings are not, because a loading is dimensionless.
    ``mde_80`` is the smallest annual alpha the window could have detected at 80% power
    and it is the number to read first: on a six-year window it is several percent a
    year, so an alpha of "zero" is very often an alpha of "unmeasurable".

    The point of the exercise is the *loadings*, not the alpha. This repository's own
    standing result is that exposure is measurable and alpha is not, and a fund whose
    record is fully explained by its loadings is a packaging decision rather than a
    return source.
    """

    label: str
    factor_names: tuple[str, ...]
    months: int
    alpha: float
    alpha_standard_error: float
    alpha_t_statistic: float
    alpha_mde_80: float
    loadings: tuple[float, ...]
    loading_standard_errors: tuple[float, ...]
    loading_t_statistics: tuple[float, ...]
    r_squared: float
    n_lags: int

    @property
    def alpha_resolved(self) -> bool:
        return abs(self.alpha) > self.alpha_mde_80

    def loading(self, name: str) -> float:
        return self.loadings[self.factor_names.index(name)]


def factor_regression(
    sleeve_excess: Sequence[float] | FloatArray,
    factors: Sequence[Sequence[float] | FloatArray],
    *,
    label: str,
    factor_names: Sequence[str],
    periods_per_year: int = MONTHS_PER_YEAR,
    n_lags: int | None = None,
) -> FactorRegression:
    """Regress an excess return on factor returns with Newey-West standard errors.

    ``factors`` is a sequence of already-aligned factor series, one per name. The
    intercept is added here, so no caller passes a column of ones and none can
    accidentally pass two.
    """
    response = _as_series(sleeve_excess, "sleeve_excess")
    names = tuple(str(name) for name in factor_names)
    if len(factors) != len(names):
        raise ValueError(f"{len(factors)} factor series but {len(names)} names")
    columns = [
        _as_series(series, f"factor {name}")
        for series, name in zip(factors, names, strict=True)
    ]
    for name, column in zip(names, columns, strict=True):
        if column.size != response.size:
            raise ValueError(
                f"factor {name} has {column.size} observations and the sleeve has "
                f"{response.size}; align them on a common window first"
            )
    design = np.column_stack(columns)
    result = hac_ols(response, design, n_lags=n_lags, add_constant=True)
    scale = float(periods_per_year)
    alpha = scale * float(result.coefficients[0])
    alpha_error = scale * float(result.standard_errors[0])
    total = float(np.sum((response - np.mean(response)) ** 2))
    residual = float(np.sum(result.residuals**2))
    return FactorRegression(
        label=label,
        factor_names=names,
        months=int(response.size),
        alpha=alpha,
        alpha_standard_error=alpha_error,
        alpha_t_statistic=float(result.t_statistics[0]),
        alpha_mde_80=minimum_detectable_effect(alpha_error),
        loadings=tuple(float(value) for value in result.coefficients[1:]),
        loading_standard_errors=tuple(float(value) for value in result.standard_errors[1:]),
        loading_t_statistics=tuple(float(value) for value in result.t_statistics[1:]),
        r_squared=1.0 - residual / total if total > 0.0 else float("nan"),
        n_lags=int(result.n_lags),
    )


@dataclass(frozen=True)
class PiecewiseBeta:
    """Up-market and down-market beta from one regression, so their gap has an error.

    Fitted as ``y = a + b m + c m 1{m < 0}``, so ``up = b``, ``down = b + c``, and the
    asymmetry is ``c`` with its own standard error. Two separate subsample regressions
    would give the same two betas and no test of the difference, which is the quantity
    that decides whether a payoff is asymmetric.

    The sign convention is the one the audit page already uses for put-writing: **up
    beta 0.45, down beta 0.86 means you get 45% of the upside and 86% of the
    downside**, and a structure sold as protection has to show the opposite ordering.
    """

    label: str
    months: int
    up_beta: float
    down_beta: float
    asymmetry: float
    asymmetry_standard_error: float
    asymmetry_t_statistic: float
    alpha: float
    alpha_standard_error: float
    down_months: int

    @property
    def protects(self) -> bool:
        """Whether the down-market beta is the *smaller* of the two."""
        return self.down_beta < self.up_beta


def piecewise_beta(
    sleeve_excess: Sequence[float] | FloatArray,
    market_excess: Sequence[float] | FloatArray,
    *,
    label: str,
    periods_per_year: int = MONTHS_PER_YEAR,
    n_lags: int | None = None,
) -> PiecewiseBeta:
    """Up- and down-market betas of a sleeve on the market, with HAC errors.

    "Down" means the *market's* excess return was negative in that month, which is a
    conditioning set the reader can reproduce. It is not the same as conditioning on a
    drawdown window, and
    ``docs/research/capital-efficiency-and-breadth.md`` §4 measures how far the two can
    diverge — a factor of three for trend. Neither is wrong and neither may be quoted
    without its conditioning set.
    """
    sleeve = _as_series(sleeve_excess, "sleeve_excess")
    market = _as_series(market_excess, "market_excess")
    if sleeve.size != market.size:
        raise ValueError(
            f"sleeve has {sleeve.size} observations and market has {market.size}"
        )
    down = market < 0.0
    if not (2 <= int(np.sum(down)) <= sleeve.size - 2):
        raise ValueError(
            "need at least two up months and two down months to fit a piecewise beta; "
            f"this window has {int(np.sum(down))} down months of {sleeve.size}"
        )
    design = np.column_stack([market, np.where(down, market, 0.0)])
    result = hac_ols(sleeve, design, n_lags=n_lags, add_constant=True)
    up_beta = float(result.coefficients[1])
    asymmetry = float(result.coefficients[2])
    return PiecewiseBeta(
        label=label,
        months=int(sleeve.size),
        up_beta=up_beta,
        down_beta=up_beta + asymmetry,
        asymmetry=asymmetry,
        asymmetry_standard_error=float(result.standard_errors[2]),
        asymmetry_t_statistic=float(result.t_statistics[2]),
        alpha=float(periods_per_year) * float(result.coefficients[0]),
        alpha_standard_error=float(periods_per_year) * float(result.standard_errors[0]),
        down_months=int(np.sum(down)),
    )


# --------------------------------------------------------------------------------
# 4. Buffer and defined-outcome funds: the payoff, and what the cap costs
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class BufferTerms:
    """One defined-outcome period: a buffer, a cap, and the dividend that is forgone.

    All figures are per outcome period, not per year, and the two are the same thing
    only for a twelve-month period.

    ``forgone_dividend_yield`` is not an optional refinement, which is why it has no
    default. A buffer fund holds FLEX options on the reference asset's **price**, so
    the shareholder receives none of its dividends. That is a certain, recurring cost
    that does not appear in the cap or the buffer and is invisible in any comparison
    against a price index. Making it a required argument is the same device
    :class:`portfolio_edge.studies.gold_sleeve.GoldCarry` uses for storage: a caller
    cannot obtain a payoff from this module without stating what the wrapper gives up.
    """

    buffer: float
    cap: float
    forgone_dividend_yield: float
    fee: float = 0.0
    period_years: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.buffer < 1.0:
            raise ValueError(f"buffer must lie in [0, 1), got {self.buffer}")
        if self.cap <= 0.0:
            raise ValueError(f"cap must be positive, got {self.cap}")
        if self.forgone_dividend_yield < 0.0:
            raise ValueError(
                f"forgone dividend yield must be non-negative, got "
                f"{self.forgone_dividend_yield}"
            )
        if self.period_years <= 0.0:
            raise ValueError(f"period_years must be positive, got {self.period_years}")


def buffer_payoff(price_return: float, terms: BufferTerms) -> float:
    """Gross return of a cap-and-buffer structure held for one **full** outcome period.

    Exactly, and this is the definition every figure below rests on::

        r >= 0            ->  min(r, cap)
        -buffer <= r < 0  ->  0
        r < -buffer       ->  r + buffer

    Equivalently ``r + max(0, min(buffer, -r)) - max(0, r - cap)``: the reference
    asset's price return, **plus** a long put spread struck at 0 and ``-buffer``,
    **minus** a short call struck at ``cap``. :func:`buffer_cost_decomposition` reports
    those two legs separately, because their difference is what the investor paid.

    Two things this is not, both of which the prospectuses say and marketing does not.
    It is a *price* return, so the reference asset's dividends are not in it. And it is
    the payoff at the **end** of the outcome period: an investor buying or selling
    part-way through owns a partially-consumed option package whose realised protection
    can be anything, which is why every figure in this module is stated per full
    period.
    """
    if price_return >= 0.0:
        return min(price_return, terms.cap)
    if price_return >= -terms.buffer:
        return 0.0
    return price_return + terms.buffer


@dataclass(frozen=True)
class BufferCostDecomposition:
    """What the option package delivered and what it cost, over a stated distribution.

    Every field is a mean over the supplied price returns, in decimal per outcome
    period. The reader's question — "was the cap worth the buffer?" — is
    ``net_option_value``: the protection received minus the upside sold. It is a
    **realised** quantity over the window supplied, not a valuation, and it says
    nothing about whether the terms were fair when they were struck.

    ``total_shortfall`` adds the two costs the option package does not contain: the
    forgone dividend and the fee. It is the honest comparison against simply holding
    the reference asset's total return, and it is the number the prospectus's own cap
    disclosure cannot show.
    """

    label: str
    periods: int
    mean_price_return: float
    mean_buffer_payoff: float
    mean_protection_received: float
    mean_upside_sold: float
    capped_fraction: float
    buffer_used_fraction: float
    buffer_exceeded_fraction: float
    forgone_dividend_yield: float
    fee: float

    @property
    def net_option_value(self) -> float:
        """Protection received minus upside sold, per outcome period."""
        return self.mean_protection_received - self.mean_upside_sold

    @property
    def total_shortfall(self) -> float:
        """Mean net return minus the reference asset's mean total return.

        Negative means the structure lost to simply holding the thing it references.
        """
        return self.net_option_value - self.forgone_dividend_yield - self.fee


def buffer_cost_decomposition(
    price_returns: Sequence[float] | FloatArray,
    terms: BufferTerms,
    *,
    label: str,
) -> BufferCostDecomposition:
    """Price the cap against a stated distribution of full-period price returns.

    ``price_returns`` must be **full-outcome-period** price returns of the reference
    asset — for a twelve-month buffer, twelve-month price returns. Overlapping windows
    are the usual source and they are fine for a mean, but they are heavily
    autocorrelated and any standard error computed on them must be HAC or block
    bootstrapped; this function returns means only, so that no caller can obtain an
    interval from it that the overlap has invalidated.
    """
    values = _as_series(price_returns, "price_returns")
    payoffs = np.array([buffer_payoff(float(value), terms) for value in values])
    protection = np.maximum(0.0, np.minimum(terms.buffer, -values))
    upside_sold = np.maximum(0.0, values - terms.cap)
    return BufferCostDecomposition(
        label=label,
        periods=int(values.size),
        mean_price_return=float(np.mean(values)),
        mean_buffer_payoff=float(np.mean(payoffs)),
        mean_protection_received=float(np.mean(protection)),
        mean_upside_sold=float(np.mean(upside_sold)),
        capped_fraction=float(np.mean(values > terms.cap)),
        buffer_used_fraction=float(np.mean(values < 0.0)),
        buffer_exceeded_fraction=float(np.mean(values < -terms.buffer)),
        forgone_dividend_yield=terms.forgone_dividend_yield,
        fee=terms.fee,
    )
