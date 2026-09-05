"""Regenerates every table in ``docs/research/untested-tilt-candidates.md``.

Kept separate from :mod:`portfolio_edge.studies.untested_tilts` so the arithmetic stays
pure and testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies.untested_tilts

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen, no experiment is registered for them, and nothing below may promote a sleeve.

The question it answers
-----------------------
Four tilt candidates were never priced against the recommended portfolio: AVDV
(developed-ex-US small value), AVUV (US small value), MTUM (US momentum) and QVAL
(Alpha Architect's concentrated US value, which is not on the shelf at all). Each is
scored the only way a portfolio holding can be scored — on delivered exposure over the
incumbent it would displace, on cost, and on what it adds given what is already owned.

Two design choices carry the whole study.

**Every comparison is on one window.** ``src/content/shelf.ts`` publishes AVDV on 75
months, DFIV on 51 and MTUM on 72, and
``docs/research/loading-comparability-and-wrapper-exposure.md`` shows that ranking such a
set orders launch dates as much as funds. Every fund here is therefore refitted, and the
crux comparison — small-cap against large-cap international value — is run on *two*
matched windows precisely because the answer changes between them.

**A delivered exposure is estimated from the difference series.** Rather than fitting the
candidate and the incumbent separately and subtracting two coefficients whose standard
errors do not combine, the *difference* of the two funds' filed returns is regressed on
the factor panel directly. The coefficients are then the delivered exposures and the
intercept is the extra return, each with a standard error that means something.

Sources, all already used by registered experiments:

* Form N-PORT Item B.5, per share class, via :mod:`portfolio_edge.data.nport`.
* Ken French's US and developed-ex-US FF5 and momentum files, for the factor panels and
  for the one-month bill that defines every excess return here.
* Fee, turnover and standardised after-tax returns from each fund's own Form 497K, quoted
  in ``docs/research/untested-tilt-candidates.md`` with its filing date.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from portfolio_edge.data.cache import RawCache
from portfolio_edge.inference.hac import hac_ols
from portfolio_edge.studies._loading_windows_tables import (
    HAC_LAGS,
    Fund,
    Panel,
    fund_returns,
    load_french_panel,
)
from portfolio_edge.studies.loading_windows import (
    LoadingEstimate,
    Window,
    minimum_detectable_loading,
    month_index,
    period_from_index,
)
from portfolio_edge.studies.untested_tilts import (
    TURNOVER_COEFFICIENT_HIGH,
    TURNOVER_COEFFICIENT_LOW,
    AfterTaxReturns,
    FundCost,
    annualise_monthly,
    edge_standard_error,
    effective_bets_of_pair,
    incremental_cost_bracket,
    incremental_distribution_tax_drag,
    marginal_tilt,
    portfolio_return_change,
    sleeve_edge,
    tracking_error_from_monthly,
)

FACTORS: Final[tuple[str, ...]] = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD")

#: The five factors a tilt is priced on. ``Mkt-RF`` is a control, not a tilt: a candidate
#: that buys market beta buys it more cheaply somewhere else.
PRICED: Final[tuple[str, ...]] = ("HML", "SMB", "RMW", "CMA", "UMD")

#: Series and class identifiers from ``https://www.sec.gov/files/company_tickers_mf.json``,
#: so a share class cannot be silently re-pointed at a different product.
#:
#: ``inception`` is given wherever the fund's *first filed month is a stub*. A fund that
#: commenced on the 24th files an Item B.5 return covering a quarter of a month, and
#: regressing that against a whole month of factor returns attenuates every coefficient and
#: contaminates every correlation. The three Avantis funds and RSST are the cases here;
#: their dates are from their own filings, and dropping the stub is what makes AVDV's
#: window reproduce the shelf's published 75 months exactly.
FUNDS: Final[tuple[Fund, ...]] = (
    Fund(ticker="VTI", series_id="S000002848", class_id="C000007808"),
    Fund(ticker="VTV", series_id="S000002840", class_id="C000007778"),
    Fund(ticker="AVUV", series_id="S000066459", class_id="C000214354", inception="2019-09-24"),
    Fund(ticker="MTUM", series_id="S000040316", class_id="C000125223"),
    Fund(ticker="QVAL", series_id="S000046016", class_id="C000143786"),
    Fund(ticker="RPV", series_id="S000060792", class_id="C000197608"),
    Fund(ticker="SPMO", series_id="S000050154", class_id="C000158243"),
    Fund(ticker="VXUS", series_id="S000002932", class_id="C000094038"),
    Fund(ticker="VEA", series_id="S000004386", class_id="C000051262"),
    Fund(ticker="AVDV", series_id="S000066457", class_id="C000214352", inception="2019-09-24"),
    Fund(ticker="DISV", series_id="S000075153", class_id="C000233989"),
    Fund(ticker="DFIV", series_id="S000070904", class_id="C000225168"),
    Fund(ticker="AVIV", series_id="S000072997", class_id="C000229746"),
    Fund(ticker="IVLU", series_id="S000049573", class_id="C000156614"),
    Fund(ticker="EFV", series_id="S000004438", class_id="C000012201"),
    Fund(ticker="IDMO", series_id="S000034746", class_id="C000106969"),
    Fund(ticker="AVES", series_id="S000072996", class_id="C000229745", inception="2021-09-28"),
    Fund(ticker="RSST", series_id="S000081720", class_id="C000244698", inception="2023-09-05"),
)

#: Loadings this study must reproduce before any of its own numbers may be read. Each is
#: from ``src/content/shelf.ts`` with the window that shelf publishes. Reproducing them is
#: what separates "a different answer" from "a different method".
PUBLISHED: Final[
    tuple[tuple[str, str, str, str, Mapping[str, float]], ...]
] = (
    ("AVDV", "exus", "2019-10", "2025-12", {"HML": 0.510, "SMB": 0.671, "RMW": 0.386}),
    ("DISV", "exus", "2022-04", "2025-12", {"HML": 0.495, "SMB": 0.431}),
    ("DFIV", "exus", "2021-10", "2025-12", {"HML": 0.662, "SMB": -0.114}),
    ("AVIV", "exus", "2021-10", "2025-12", {"HML": 0.489, "SMB": -0.285}),
    ("IVLU", "exus", "2019-08", "2025-12", {"HML": 0.475}),
    ("IDMO", "exus", "2019-08", "2025-12", {"UMD": 0.540, "HML": 0.218, "SMB": -0.164}),
    ("VTI", "us", "2020-01", "2025-12", {"HML": 0.025}),
    ("VTV", "us", "2020-01", "2025-12", {"HML": 0.337}),
    ("AVUV", "us", "2020-01", "2025-12", {"HML": 0.537, "SMB": 0.877}),
    ("MTUM", "us", "2020-01", "2025-12", {"UMD": 0.444}),
    ("RPV", "us", "2020-01", "2025-12", {"HML": 0.710, "SMB": 0.200}),
    # SPMO IS DELIBERATELY ABSENT. The shelf publishes a UMD loading of +0.414 for it with
    # `window: null` -- no window, no interval, no alpha. A loading with no window cannot be
    # reproduced and cannot be compared with another fund's, which is the rule
    # `src/lib/loadings.ts` enforces by throwing. SPMO is therefore FITTED HERE FROM ITS OWN
    # FILINGS on a stated window rather than checked against an unreproducible number.
)

#: Post-publication premia, pp/yr, exactly as ``studies._stacking_tables`` carries them.
#: Nothing here estimates one. ``own-panel`` is each region's own figure, ``pooled``
#: applies the three-region pooled figure everywhere, ``half`` is a continued-decay
#: scenario and ``null`` sets every premium to zero.
PREMIA: Final[Mapping[str, Mapping[str, Mapping[str, float]]]] = {
    "own-panel": {
        "us": {"HML": 1.57, "SMB": 0.33, "RMW": 0.0, "CMA": 0.0, "UMD": 4.19},
        "exus": {"HML": 5.07125, "SMB": 0.49, "RMW": 1.681, "CMA": 0.533, "UMD": 8.351},
    },
    "pooled": {
        region: {"HML": 4.740625, "SMB": 0.33, "RMW": 2.53, "CMA": 0.20, "UMD": 7.33}
        for region in ("us", "exus")
    },
    "half": {
        "us": {"HML": 0.785, "SMB": 0.165, "RMW": 0.0, "CMA": 0.0, "UMD": 2.095},
        "exus": {"HML": 2.535625, "SMB": 0.245, "RMW": 0.8405, "CMA": 0.2665, "UMD": 4.1755},
    },
    "null": {region: dict.fromkeys(PRICED, 0.0) for region in ("us", "exus")},
}

#: Published MDE80 for each premium, pp/yr, from the pages that measured it. Three of the
#: five are larger than the premium beside them, which is the fact that decides MTUM.
PREMIUM_MDE80: Final[Mapping[str, Mapping[str, float]]] = {
    "us": {"HML": 5.03, "SMB": 2.47, "RMW": 2.62, "CMA": 2.62, "UMD": 7.27},
    "exus": {"HML": 3.67, "SMB": 2.83, "RMW": 2.62, "CMA": 2.62, "UMD": 5.21},
}

#: Fee, securities lending and turnover, each from the source named beside it. A ``None``
#: lending figure means Form N-CEN was never read for that fund, and
#: ``untested_tilts.FundCost.net_cost_bp`` raises rather than substituting the fee.
COSTS: Final[Mapping[str, FundCost]] = {
    # Fee and turnover: Vanguard Form 497K, 2026-04-28. Lending: Form N-CEN, already on
    # the shelf.
    "VTI": FundCost(ticker="VTI", fee_bp=3.0, securities_lending_bp=1.84, turnover_percent=3.0),
    "VTV": FundCost(ticker="VTV", fee_bp=3.0, securities_lending_bp=0.295, turnover_percent=8.0),
    # Vanguard Form 497K, 2026-02-27; lending from Form N-CEN, on the shelf.
    "VXUS": FundCost(
        ticker="VXUS", fee_bp=5.0, securities_lending_bp=3.57, turnover_percent=4.0
    ),
    # Avantis Form 497K, 2025-12-31.
    "AVDV": FundCost(ticker="AVDV", fee_bp=36.0, securities_lending_bp=5.970, turnover_percent=4.0),
    "AVUV": FundCost(ticker="AVUV", fee_bp=25.0, securities_lending_bp=0.461, turnover_percent=6.0),
    # iShares Form 497K, 2025-11-28.
    "MTUM": FundCost(
        ticker="MTUM", fee_bp=15.0, securities_lending_bp=None, turnover_percent=116.0
    ),
    # Alpha Architect Form 497K, 2026-02-01.
    "QVAL": FundCost(
        ticker="QVAL", fee_bp=28.0, securities_lending_bp=None, turnover_percent=332.0
    ),
    # Invesco: fee from the shelf; turnover as Experiment 002 read it. No lending figure.
    "IDMO": FundCost(
        ticker="IDMO", fee_bp=25.0, securities_lending_bp=2.411, turnover_percent=105.0
    ),
    # Invesco Form 497K dated 2025-08-28; lending from Form N-CEN, eight fiscal years.
    "RPV": FundCost(ticker="RPV", fee_bp=35.0, securities_lending_bp=1.130, turnover_percent=42.0),
    # Invesco Form 497K dated 2025-12-19; lending from Form N-CEN, seven fiscal years.
    "SPMO": FundCost(
        ticker="SPMO", fee_bp=13.0, securities_lending_bp=0.071, turnover_percent=44.0
    ),
}

#: Form N-1A's standardised after-tax table, at the highest historical individual federal
#: rates. Every row here is the ten- or five-year column ending 2024-12, because that is
#: the one period all six funds' current filings share; the ``period`` field is checked at
#: subtraction time and a mismatch raises.
AFTER_TAX: Final[Mapping[str, AfterTaxReturns]] = {
    "VTI": AfterTaxReturns(
        ticker="VTI",
        period="5 years to 2024-12",
        before_tax=13.80,
        after_tax_on_distributions=13.38,
    ),
    "VXUS": AfterTaxReturns(
        ticker="VXUS",
        period="5 years to 2024-12",
        before_tax=4.32,
        after_tax_on_distributions=3.53,
    ),
    "MTUM": AfterTaxReturns(
        ticker="MTUM",
        period="5 years to 2024-12",
        before_tax=11.77,
        after_tax_on_distributions=11.46,
    ),
    "AVUV": AfterTaxReturns(
        ticker="AVUV",
        period="5 years to 2024-12",
        before_tax=14.12,
        after_tax_on_distributions=13.68,
    ),
    "AVDV": AfterTaxReturns(
        ticker="AVDV",
        period="5 years to 2024-12",
        before_tax=6.35,
        after_tax_on_distributions=5.57,
    ),
    # Vanguard Form 497K dated 2025-04-29, the vintage whose table ends 2024-12. The
    # 2026-04-28 filing's table ends 2025-12 and would not subtract against these rows;
    # `incremental_distribution_tax_drag` raises rather than letting it.
    "VTV": AfterTaxReturns(
        ticker="VTV",
        period="5 years to 2024-12",
        before_tax=9.93,
        after_tax_on_distributions=9.26,
    ),
    # Invesco Form 497K dated 2025-08-28.
    "RPV": AfterTaxReturns(
        ticker="RPV",
        period="5 years to 2024-12",
        before_tax=7.99,
        after_tax_on_distributions=7.37,
    ),
    # Invesco Form 497K dated 2025-12-19.
    "SPMO": AfterTaxReturns(
        ticker="SPMO",
        period="5 years to 2024-12",
        before_tax=19.23,
        after_tax_on_distributions=18.86,
    ),
}

#: The recommended portfolio's active positions, as weights of capital against the cheap
#: incumbent each one displaces. VTI at 25% and VXUS at 25% carry no active position and
#: are the benchmark, not a sleeve.
HELD: Final[Mapping[str, float]] = {"RSST": 0.25, "VTV": 0.15, "IDMO": 0.05, "AVES": 0.05}

#: Which cheap fund each active position is measured against.
INCUMBENT: Final[Mapping[str, str]] = {
    "RSST": "VTI",
    "VTV": "VTI",
    "IDMO": "VXUS",
    "AVES": "VXUS",
    "AVDV": "VXUS",
    "AVUV": "VTI",
    "MTUM": "VTI",
    "QVAL": "VTI",
    "RPV": "VTV",
    "SPMO": "VTI",
}

@dataclass(frozen=True, slots=True, kw_only=True)
class Case:
    """One candidate, the incumbent it displaces, the panel and the window it is fitted on.

    A candidate appears twice where two fundings are plausible: AVUV funded out of the US
    core is a different proposition from AVUV replacing the US value line already held,
    and the second is much the weaker of the two.
    """

    label: str
    ticker: str
    incumbent: str
    panel: str
    first: str
    last: str
    weight: float
    """The weight the owning page prices it at, as a fraction of portfolio capital."""
    displaces: str | None = None
    """An active position this candidate would *replace* rather than sit beside.

    A replacement must not be scored against a held portfolio that still contains what it
    replaces: the candidate's active leg is then negatively correlated with a position
    that would no longer exist, and the marginal verdict measures a portfolio nobody would
    hold. Where this is set, that member is dropped from the held set first.
    """


#: The four candidates, plus the two active positions already held that they are scored
#: against. Windows are the longest the pair shares; the run-finder narrows them further
#: where a fund's filings have a hole.
CASES: Final[tuple[Case, ...]] = (
    Case(label="AVDV over VXUS", ticker="AVDV", incumbent="VXUS", panel="exus",
         first="2019-10", last="2026-03", weight=0.05),
    Case(label="AVUV over VTI", ticker="AVUV", incumbent="VTI", panel="us",
         first="2019-10", last="2026-03", weight=0.15),
    Case(label="AVUV replacing VTV", ticker="AVUV", incumbent="VTV", panel="us",
         first="2019-10", last="2026-03", weight=0.15, displaces="VTV"),
    Case(label="MTUM over VTI", ticker="MTUM", incumbent="VTI", panel="us",
         first="2019-10", last="2026-03", weight=0.05),
    Case(label="QVAL over VTI", ticker="QVAL", incumbent="VTI", panel="us",
         first="2020-01", last="2026-03", weight=0.05),
    Case(label="RPV replacing VTV", ticker="RPV", incumbent="VTV", panel="us",
         first="2019-10", last="2026-03", weight=0.15, displaces="VTV"),
    Case(label="SPMO over VTI", ticker="SPMO", incumbent="VTI", panel="us",
         first="2019-10", last="2026-03", weight=0.05),
    Case(label="VTV over VTI (held)", ticker="VTV", incumbent="VTI", panel="us",
         first="2019-10", last="2026-03", weight=0.15),
    Case(label="IDMO over VXUS (held)", ticker="IDMO", incumbent="VXUS", panel="exus",
         first="2019-10", last="2026-03", weight=0.05),
)

#: The candidates. The remaining cases are active positions the portfolio already holds and
#: are fitted only so that the held edge is measured rather than assumed.
CANDIDATE_CASES: Final[tuple[Case, ...]] = CASES[:7]

#: AVES's edge per dollar of sleeve, pp/yr, carried from
#: ``docs/research/stacking-and-effective-breadth.md`` §2 rather than re-derived: its
#: incumbent there is IEMG, which this study does not fit.
AVES_EDGE: Final = 1.408

#: The trend leg's assumed net excess return over cash, pp/yr. An assumption in every
#: page of this repository that uses it, and the middle of the four scenarios
#: ``_stacking_tables`` carries.
TREND_EDGE: Final = 1.0


class UntestedTiltsError(RuntimeError):
    """A source did not carry what this study needs, and guessing was refused."""


def periods_between(first: str, last: str) -> tuple[str, ...]:
    """Every month from ``first`` to ``last`` inclusive, ``YYYY-MM``."""
    start, end = month_index(first), month_index(last)
    if end < start:
        raise ValueError(f"{first}..{last} ends before it begins")
    return tuple(period_from_index(start + offset) for offset in range(end - start + 1))


@dataclass(frozen=True, slots=True, kw_only=True)
class Regression:
    """One fund-or-difference regressed on one panel over one window."""

    label: str
    panel: str
    window: Window
    months: int
    alpha: float
    """The intercept, percentage points a year."""
    alpha_standard_error: float
    loadings: Mapping[str, LoadingEstimate]

    @property
    def alpha_interval(self) -> tuple[float, float]:
        half = 1.959963984540054 * self.alpha_standard_error
        return self.alpha - half, self.alpha + half

    @property
    def alpha_minimum_detectable(self) -> float:
        """The smallest extra return this window could have found at 80% power."""
        return minimum_detectable_loading(self.alpha_standard_error)

    def delivered(self) -> dict[str, float]:
        """The five priced loadings as a plain mapping, market beta excluded."""
        return {factor: self.loadings[factor].value for factor in PRICED}


def load_returns(cache: RawCache) -> dict[str, dict[str, float]]:
    """Every fund's filed Item B.5 monthly total return, ``{ticker: {YYYY-MM: decimal}}``."""
    return {fund.ticker: fund_returns(cache, fund) for fund in FUNDS}


def difference(
    returns: Mapping[str, Mapping[str, float]], weights: Mapping[str, float]
) -> dict[str, float]:
    """A weighted combination of funds' returns, on the months every one of them filed."""
    months = set.intersection(*(set(returns[ticker]) for ticker in weights))
    return {
        month: sum(weight * returns[ticker][month] for ticker, weight in weights.items())
        for month in months
    }


def longest_contiguous_run(months: Sequence[str]) -> tuple[str, ...]:
    """The longest gapless run inside ``months``, latest such run winning a tie.

    Not decoration. QVAL files no Form N-PORT for the quarter ending 2021-09-30, so its
    history has a three-month hole, and a Newey-West covariance laid across a hole treats
    two months a quarter apart as neighbours. ``loading_windows.require_contiguous``
    refuses such a run outright; this picks the longest piece that is not one.
    """
    if not months:
        return ()
    ordered = sorted(months)
    runs: list[list[str]] = [[ordered[0]]]
    for month in ordered[1:]:
        if month_index(month) - month_index(runs[-1][-1]) == 1:
            runs[-1].append(month)
        else:
            runs.append([month])
    longest = runs[0]
    for run in runs[1:]:
        if len(run) >= len(longest):
            longest = run
    return tuple(longest)


def regress(
    *,
    label: str,
    panel: Panel,
    panel_name: str,
    series: Mapping[str, float],
    first: str,
    last: str,
    subtract_cash: bool,
) -> Regression:
    """FF5 plus momentum, Newey-West at :data:`HAC_LAGS` lags.

    ``subtract_cash`` is true for a fund's own excess return and false for a *difference*
    of two funds, where the cash leg has already cancelled. Getting that wrong shifts the
    intercept by the whole bill rate, so it is a required argument rather than a default.

    The window is narrowed to the longest gapless run the series actually covers, and the
    :class:`Regression` reports that run rather than the range asked for.
    """
    months = longest_contiguous_run(
        [
            month
            for month in periods_between(first, last)
            if month in series and month in panel.rows
        ]
    )
    if len(months) < 24:
        raise UntestedTiltsError(
            f"{label}: only {len(months)} months in {first}..{last}; a six-parameter "
            "regression on that is a statement about the window, not the fund"
        )
    cash = [panel.rows[month]["RF"] if subtract_cash else 0.0 for month in months]
    response = np.array(
        [series[month] - rate for month, rate in zip(months, cash, strict=True)],
        dtype=np.float64,
    )
    design = np.column_stack(
        [[panel.rows[month][factor] for month in months] for factor in FACTORS]
    )
    fit = hac_ols(response, design, n_lags=HAC_LAGS, add_constant=True)
    window = Window(months[0], months[-1])
    return Regression(
        label=label,
        panel=panel_name,
        window=window,
        months=len(months),
        alpha=annualise_monthly(float(fit.coefficients[0])),
        alpha_standard_error=annualise_monthly(float(fit.standard_errors[0])),
        loadings={
            factor: LoadingEstimate(
                ticker=label,
                factor=factor,
                benchmark=f"french-{panel_name}",
                value=float(fit.coefficients[position + 1]),
                standard_error=float(fit.standard_errors[position + 1]),
                window=window,
            )
            for position, factor in enumerate(FACTORS)
        },
    )


def active_leg(
    returns: Mapping[str, Mapping[str, float]], ticker: str, months: Sequence[str]
) -> np.ndarray:
    """The candidate's monthly return less the incumbent it displaces, over ``months``."""
    incumbent = INCUMBENT[ticker]
    return np.array(
        [returns[ticker][month] - returns[incumbent][month] for month in months],
        dtype=np.float64,
    )


def common_months(
    returns: Mapping[str, Mapping[str, float]],
    tickers: Sequence[str],
    first: str,
    last: str,
) -> tuple[str, ...]:
    """The months inside ``first..last`` that every ticker and its incumbent filed."""
    needed = set(tickers) | {INCUMBENT[t] for t in tickers if t in INCUMBENT}
    return longest_contiguous_run(
        [
            month
            for month in periods_between(first, last)
            if all(month in returns[ticker] for ticker in needed)
        ]
    )


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


def _rule(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def _print_regression(report: Regression, factors: Sequence[str] = PRICED) -> None:
    low, high = report.alpha_interval
    print(
        f"  {report.label:<18} n={report.months:>3} {report.window.label} "
        f"extra return {report.alpha:+6.2f} [{low:+6.2f},{high:+6.2f}] "
        f"smallest detectable {report.alpha_minimum_detectable:5.2f}"
    )
    body = "  ".join(
        f"{factor} {report.loadings[factor].value:+.3f}" for factor in factors
    )
    print(f"{'':<21}{body}")


def main() -> None:  # pragma: no cover - a reporting entry point
    cache = RawCache()
    panels = {
        "us": load_french_panel(cache, "us"),
        "exus": load_french_panel(cache, "developed_ex_us"),
    }
    returns = load_returns(cache)

    _rule("0. The method, proved on the published windows before it is used")
    worst = 0.0
    for ticker, panel_name, first, last, expected in PUBLISHED:
        report = regress(
            label=ticker,
            panel=panels[panel_name],
            panel_name=panel_name,
            series=returns[ticker],
            first=first,
            last=last,
            subtract_cash=True,
        )
        gaps = {
            factor: abs(report.loadings[factor].value - value)
            for factor, value in expected.items()
        }
        worst = max(worst, max(gaps.values()))
        detail = "  ".join(f"{f} {report.loadings[f].value:+.3f}" for f in expected)
        print(f"  {ticker:<6} {report.window.label} n={report.months:>3}  {detail}")
    print(f"  largest gap to the published shelf across all of them: {worst:.4f}")

    _rule("1. The crux: does large-cap international value's negative return reach small?")
    for first, last, label in (
        ("2021-10", "2026-04", "the window DFIV and AVIV impose"),
        ("2019-10", "2026-03", "the longest window the older funds share"),
    ):
        print(f"\n  -- {first}..{last}: {label}")
        for ticker in ("VXUS", "VEA", "IVLU", "EFV", "DFIV", "AVIV", "AVDV", "DISV"):
            if min(returns[ticker]) > first:
                print(f"  {ticker:<18} does not file before {min(returns[ticker])}")
                continue
            _print_regression(
                regress(
                    label=ticker,
                    panel=panels["exus"],
                    panel_name="exus",
                    series=returns[ticker],
                    first=first,
                    last=last,
                    subtract_cash=True,
                )
            )
        for small, large in (("AVDV", "DFIV"), ("AVDV", "AVIV"), ("AVDV", "IVLU"), ("AVDV", "EFV")):
            if min(returns[large]) > first:
                continue
            _print_regression(
                regress(
                    label=f"{small}-{large}",
                    panel=panels["exus"],
                    panel_name="exus",
                    series=difference(returns, {small: 1.0, large: -1.0}),
                    first=first,
                    last=last,
                    subtract_cash=False,
                )
            )

    print("\n  The same two funds, with no factor model at all:")
    for small, large in (("AVDV", "DFIV"), ("AVDV", "AVIV")):
        months = common_months(returns, [small, large], "2021-10", "2026-04")
        values = np.array([returns[small][m] - returns[large][m] for m in months])
        half_width = 1.96 * float(values.std(ddof=1)) / math.sqrt(len(values))
        print(
            f"  {small}-{large}: n={len(months)} mean difference "
            f"{annualise_monthly(float(values.mean())):+.2f} "
            f"+-{annualise_monthly(half_width):.2f} pp/yr"
        )

    _rule("2. Each candidate's delivered exposure over the incumbent it would displace")
    deltas: dict[str, Regression] = {}
    for case in CASES:
        report = regress(
            label=case.label,
            panel=panels[case.panel],
            panel_name=case.panel,
            series=difference(returns, {case.ticker: 1.0, case.incumbent: -1.0}),
            first=case.first,
            last=case.last,
            subtract_cash=False,
        )
        deltas[case.label] = report
        _print_regression(report)
        for factor in PRICED:
            print(f"{'':<21}{factor} {report.loadings[factor].format()}")

    _rule("3. What each candidate costs, from its own filings")
    costs: dict[str, tuple[float, float]] = {}
    for case in CASES:
        low, high = incremental_cost_bracket(
            fund=COSTS[case.ticker], incumbent=COSTS[case.incumbent]
        )
        costs[case.label] = (low, high)
        fund = COSTS[case.ticker]
        basis = "net of lending" if fund.lending_was_read else "fee only, lending unread"
        print(
            f"  {case.label:<22} fee {fund.fee_bp:5.1f} bp ({basis}), turnover "
            f"{fund.turnover_percent:5.1f}%/yr against {case.incumbent}'s "
            f"{COSTS[case.incumbent].turnover_percent}% -> incremental cost "
            f"{low:.3f} to {high:.3f} pp/yr, k={TURNOVER_COEFFICIENT_LOW} to "
            f"{TURNOVER_COEFFICIENT_HIGH}"
        )
    print("\n  Distribution tax drag over the incumbent, Form N-1A standardised:")
    for ticker, incumbent in (
        ("AVDV", "VXUS"),
        ("AVUV", "VTI"),
        ("MTUM", "VTI"),
        ("VTV", "VTI"),
        ("RPV", "VTI"),
        ("RPV", "VTV"),
        ("SPMO", "VTI"),
    ):
        drag = incremental_distribution_tax_drag(
            fund=AFTER_TAX[ticker], incumbent=AFTER_TAX[incumbent]
        )
        print(
            f"  {ticker:<6} {AFTER_TAX[ticker].distribution_drag:+.2f} against "
            f"{incumbent}'s {AFTER_TAX[incumbent].distribution_drag:+.2f} "
            f"-> {drag:+.2f} pp/yr, {AFTER_TAX[ticker].period}"
        )
    print(
        "  QVAL: no after-tax table was read for it here, so its distribution drag is "
        "unmeasured. Its 332%/yr turnover already decides it without one."
    )

    _rule("4. The sleeve edge, across four premium scenarios")
    edges: dict[str, dict[str, tuple[float, float]]] = {}
    errors: dict[str, float] = {}
    for case in CASES:
        delivered = deltas[case.label].delivered()
        low, high = costs[case.label]
        errors[case.label] = edge_standard_error(
            delivered=delivered, minimum_detectable_premia=PREMIUM_MDE80[case.panel]
        )
        edges[case.label] = {}
        print(
            f"\n  {case.label}, premium standard error {errors[case.label]:.2f} pp/yr, "
            f"n={deltas[case.label].months} {deltas[case.label].window.label}"
        )
        for scenario, table in PREMIA.items():
            worst = sleeve_edge(
                delivered=delivered, premia=table[case.panel], incremental_cost=high
            )
            best = sleeve_edge(
                delivered=delivered, premia=table[case.panel], incremental_cost=low
            )
            edges[case.label][scenario] = (worst, best)
            print(f"    {scenario:<10} {worst:+6.3f} to {best:+6.3f} pp/yr per dollar of sleeve")

    _rule("5. Residual appraisal against the held active-position proxy")
    print("  Residual alpha removes exposure explained by this proxy; it is not funded return.")
    print("  Its uncertainty is not estimated here. The proxy is not the complete portfolio.")
    held_edges = {
        "VTV": edges["VTV over VTI (held)"]["own-panel"][0],
        "IDMO": edges["IDMO over VXUS (held)"]["own-panel"][0],
        "AVES": AVES_EDGE,
        "RSST": TREND_EDGE,
    }
    print(
        "  Held active edges, pp/yr per dollar of sleeve: "
        + ", ".join(f"{k} {v:+.3f}" for k, v in held_edges.items())
        + "  (AVES and the trend leg are carried, not fitted here)"
    )
    for label, members, first, last in (
        ("with the trend wrapper", tuple(HELD), "2023-10", "2026-03"),
        ("without it, on more months", ("VTV", "IDMO", "AVES"), "2021-10", "2026-03"),
    ):
        print(f"\n  -- {label}")
        for case in CANDIDATE_CASES:
            standing = tuple(member for member in members if member != case.displaces)
            months = common_months(returns, (*standing, case.ticker), first, last)
            held = sum(
                HELD[member] * active_leg(returns, member, months) for member in standing
            )
            held_error = tracking_error_from_monthly(float(np.std(held, ddof=1)))
            held_edge = sum(HELD[member] * held_edges[member] for member in standing)
            candidate = np.array(
                [returns[case.ticker][m] - returns[case.incumbent][m] for m in months]
            )
            candidate_error = tracking_error_from_monthly(float(np.std(candidate, ddof=1)))
            correlation = float(np.corrcoef(candidate, held)[0, 1])
            verdict = marginal_tilt(
                ticker=case.label,
                weight=case.weight,
                candidate_edge=edges[case.label]["own-panel"][0],
                candidate_tracking_error=candidate_error,
                held_edge=held_edge,
                held_tracking_error=held_error,
                correlation_to_held=correlation,
            )
            print(
                f"  {case.label:<22} n={len(months):>3} own tracking error "
                f"{candidate_error:5.2f} rho to held {correlation:+.3f} funded edge "
                f"{edges[case.label]['own-panel'][0]:+6.3f} residual alpha {verdict.alpha:+6.3f} "
                f"({verdict.appraisal_ratio:+.3f} per unit of residual risk)"
            )

    _rule("6. Momentum in two regions is fewer than two bets")
    months = common_months(returns, ("MTUM", "IDMO"), "2019-08", "2026-03")
    mtum = np.array([returns["MTUM"][m] - returns["VTI"][m] for m in months])
    idmo = np.array([returns["IDMO"][m] - returns["VXUS"][m] for m in months])
    correlation = float(np.corrcoef(mtum, idmo)[0, 1])
    print(
        f"  MTUM over VTI against IDMO over VXUS, n={len(months)} "
        f"{months[0]}..{months[-1]}: rho {correlation:+.3f} "
        f"+-{1.96 / math.sqrt(len(months)):.3f}, worth "
        f"{effective_bets_of_pair(correlation):.2f} independent bets out of 2"
    )
    print("\n  Every candidate's active leg against every held active leg, pairwise:")
    columns = ("VTV", "IDMO", "AVES", "RSST")
    print(f"  {'':<6}" + "".join(f"{column:>10}" for column in columns))
    for row in ("AVDV", "AVUV", "MTUM", "QVAL", "RPV", "SPMO"):
        cells = []
        for column in columns:
            shared = common_months(returns, (row, column), "2019-07", "2026-05")
            if len(shared) < 24:
                cells.append(f"{'-':>10}")
                continue
            pair = np.corrcoef(
                active_leg(returns, row, shared), active_leg(returns, column, shared)
            )
            cells.append(f"{float(pair[0, 1]):>+10.3f}")
        print(f"  {row:<6}" + "".join(cells))
    print(
        "  Overlap describes shared exposure. It does not by itself determine funded return "
        "or log growth."
    )

    _rule("7. Funded factor-tilt arithmetic contribution, percentage points per year")
    print("  Centre is the own-panel premia at the worse end of the cost bracket. The")
    print("  range is a +/-1.96 premium-error sensitivity, not a full confidence interval.")
    print("  It excludes loading, cost and residual-appraisal uncertainty. The null column")
    print("  is what the candidate costs if every premium turns out to be zero.")
    print("  Excludes incremental market beta times market premium, intercept and taxes.")
    print("  Growth and allocation value require the complete portfolio return path.")
    for case in CANDIDATE_CASES:
        funded_edge = edges[case.label]["own-panel"][0]
        error = errors[case.label]
        for weight in sorted({case.weight, 0.05, 0.10}):
            centre = portfolio_return_change(weight=weight, edge=funded_edge)
            low = portfolio_return_change(weight=weight, edge=funded_edge - 1.96 * error)
            high = portfolio_return_change(weight=weight, edge=funded_edge + 1.96 * error)
            null = portfolio_return_change(
                weight=weight, edge=edges[case.label]["null"][0]
            )
            print(
                f"  {case.label:<22} at {weight:>5.1%}: {centre:+.3f}% a year "
                f"[{low:+.3f}%, {high:+.3f}%], {null:+.3f}% if every premium is zero"
            )
