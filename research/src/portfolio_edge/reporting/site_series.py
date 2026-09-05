"""Emit the site's portfolio series: the printed weight vectors rebuilt on two histories.

Run with::

    uv run python -m portfolio_edge.reporting.site_series

The site prints, for each of its four portfolios, what $10,000 became, the compound
growth, the worst fall in dollars and months, and a few calendar-year returns. Until
this module existed those numbers were typed into ``src/content/portfolios.ts`` from
experiment tables whose arms did not always hold the weights the page showed (the
cautious page summed to 100.1; the with-trend card quoted an arm no page displayed).

This module rebuilds each *printed* weight vector on Experiment 025's two scored
panels, using 025's own loaders and simulators, and writes one JSON file per window
to ``src/content/series/``. Before writing anything it re-simulates the research
arms the artifacts scored and refuses to emit if any worst fall or months-under-water
figure differs from the committed tables, so the site's series are provably the
artifacts' series.

What it is not
--------------
A descriptive re-emission. No hypothesis, no comparison, no status. Every holding
is a basis expression or an exposure vector, never a fund's price record; the bond
line is a modelled nominal ten-year Treasury standing in for TIPS; the trend line
on the 1990 panel is AQR's TSMOM index before trading costs. The ``basis`` paragraph
in each file says so in plain English, and the site must print it beside any dollar
figure it takes from here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MONTHS_PER_YEAR,
    BasisPanel,
    CostSettings,
    FundMapping,
    _at,
    _mapping,
    _text,
    constant_weight_path,
    workspace_root,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    FinancingRates,
    Wrapper,
    _cost_settings,
    read_rates,
    simulate_arm,
)
from portfolio_edge.experiments.exp_024_working_default import (
    _manifest_hashes,
    _read_weighted,
    build_primary_panel,
    read_arms,
)
from portfolio_edge.experiments.exp_025_cautious_constructions import (
    build_legs,
    default_specification_path,
    load_series,
    load_tournament_inputs,
    read_wrappers,
)
from portfolio_edge.experiments.ledger import (
    Ledger,
    LedgerEntry,
    LedgerEvent,
    Origin,
    RunStatus,
    code_version,
    environment_snapshot,
    new_run_id,
)
from portfolio_edge.experiments.periods import month_index
from portfolio_edge.experiments.result import ArtifactRecord
from portfolio_edge.experiments.runner import capture_git_state
from portfolio_edge.experiments.specification import JsonValue, load_specification

FloatArray = NDArray[np.float64]

START_DOLLARS: Final = 10_000.0
FAMILY: Final = "site_series"

#: The 025 run whose tables every emitted series is checked against.
EXP_025_RUN: Final = "00c0b8b0b1894993afdc07236e402451"
#: 016e, the final construction test (value lean and the cheap control on the 1990 panel).
EXP_016E_RUN: Final = "cd2fb4b964cf4f8b966432076906ad82"
#: 024, the working default (RSST 25 + ten-year 5) on both panels.
EXP_024_RUN: Final = "5f3c2db962fe420881d3aaba3e44df55"

#: 016f's basis tickers that are stock funds. On the 1929 panel every one of them is
#: the US market at 3 bp; the tilt cannot be built there.
STOCK_TICKERS: Final = frozenset({"VT", "VTI", "VXUS", "VTV", "AVDV", "IDMO", "AVES"})
TREND_TICKER: Final = "RSST"
BOND_TICKER: Final = "SCHP"


class SiteSeriesError(Exception):
    """The emitter refused: a weight vector, a panel or an artifact check did not hold."""


# --------------------------------------------------------------------------- #
# The printed portfolios
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class SitePortfolio:
    """One series the site prints: its id, label and weights in percent of capital."""

    id: str
    label: str
    weights: Mapping[str, float]
    #: False for a series the 1929 panel cannot build (the value tilt has no series there).
    on_long_panel: bool = True

    def __post_init__(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 100.0) > 1e-9:
            raise SiteSeriesError(f"{self.id}: weights sum to {total:.4f}, not 100")
        for ticker, weight in self.weights.items():
            if weight <= 0.0:
                raise SiteSeriesError(f"{self.id}: {ticker} has weight {weight}")


#: The four portfolios as printed, the retired 30% cautious version, and the two controls.
#: These are the vectors ``src/content/portfolios.ts`` prints; a vitest asserts equality.
SITE_PORTFOLIOS: Final[tuple[SitePortfolio, ...]] = (
    SitePortfolio(id="one-fund", label="One fund", weights={"VT": 100}),
    SitePortfolio(
        id="value-lean",
        label="Value lean",
        weights={"VTI": 49, "VXUS": 16, "VTV": 15, "AVDV": 10, "IDMO": 5, "AVES": 5},
        on_long_panel=False,
    ),
    SitePortfolio(
        id="with-trend",
        label="Plus trend",
        weights={
            "RSST": 25,
            "VTI": 19,
            "VXUS": 16,
            "VTV": 15,
            "AVDV": 10,
            "IDMO": 5,
            "AVES": 5,
            "SCHP": 5,
        },
    ),
    SitePortfolio(
        id="cautious",
        label="Cautious",
        weights={
            "SCHP": 50,
            "RSST": 15,
            "VTI": 9.5,
            "VXUS": 8,
            "VTV": 7.5,
            "AVDV": 5,
            "IDMO": 2.5,
            "AVES": 2.5,
        },
    ),
    SitePortfolio(
        id="cautious-30",
        label="Cautious, for a 30% fall",
        weights={
            "SCHP": 63,
            "RSST": 11,
            "VTI": 7.1,
            "VXUS": 5.9,
            "VTV": 5.6,
            "AVDV": 3.7,
            "IDMO": 1.9,
            "AVES": 1.8,
        },
    ),
    SitePortfolio(id="market", label="Plain world stock index", weights={"VTI": 65, "VXUS": 35}),
    SitePortfolio(id="sixty-forty", label="60/40", weights={"VTI": 39, "VXUS": 21, "SCHP": 40}),
)

#: Episodes the site quotes. Three are calendar years; the 2000-02 bear is a peak-to-trough
#: span, because no calendar year contains it.
EPISODES: Final[Mapping[str, tuple[str, str]]] = {
    "dotcom-2000-02": ("2000-04", "2002-09"),
    "gfc-2008": ("2008-01", "2008-12"),
    "covid-2020": ("2020-01", "2020-12"),
    "rates-2022": ("2022-01", "2022-12"),
}
EPISODE_DEFINITIONS: Final[Mapping[str, str]] = {
    "dotcom-2000-02": (
        "Cumulative return from the end of March 2000 to the end of September 2002, "
        "the 30 months from the market's peak to its trough; not a calendar year."
    ),
    "gfc-2008": "Calendar year 2008.",
    "covid-2020": "Calendar year 2020.",
    "rates-2022": "Calendar year 2022.",
}
SINCE: Final = "2009-01"


# --------------------------------------------------------------------------- #
# Artifact checks: the research arms this module must reproduce before it emits
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactCheck:
    """A worst fall and months under water as a committed artifact table prints them."""

    arm: str
    source: str
    max_drawdown_pct: float
    months_under_water: int


#: ``research/artifacts/<run>/tables.md``, the tournament panel's ``full`` drawdown row and
#: 024's tournament arm table. Read by eye from the committed files; cited per row.
TOURNAMENT_CHECKS: Final[tuple[ArtifactCheck, ...]] = (
    ArtifactCheck(
        arm="control_cheap",
        source=f"{EXP_025_RUN}/tables.md, drawdown by era, tournament, full",
        max_drawdown_pct=-52.69,
        months_under_water=63,
    ),
    ArtifactCheck(
        arm="control_cheap60_40",
        source=f"{EXP_025_RUN}/tables.md, drawdown by era, tournament, full",
        max_drawdown_pct=-27.18,
        months_under_water=37,
    ),
    ArtifactCheck(
        arm="published",
        source=f"{EXP_025_RUN}/tables.md, tournament arms",
        max_drawdown_pct=-49.69,
        months_under_water=42,
    ),
    ArtifactCheck(
        arm="rec25",
        source=f"{EXP_025_RUN}/tables.md, tournament arms",
        max_drawdown_pct=-50.27,
        months_under_water=42,
    ),
    ArtifactCheck(
        arm="ladder40",
        source=f"{EXP_025_RUN}/tables.md, tournament arms",
        max_drawdown_pct=-18.08,
        months_under_water=26,
    ),
    ArtifactCheck(
        arm="ladder30",
        source=f"{EXP_025_RUN}/tables.md, tournament arms",
        max_drawdown_pct=-15.84,
        months_under_water=31,
    ),
    ArtifactCheck(
        arm="working_default",
        source=f"{EXP_024_RUN}/tables.md, tournament arms",
        max_drawdown_pct=-47.38,
        months_under_water=42,
    ),
)

#: The primary (1929) panel: 025's arm table and 024's.
PRIMARY_CHECKS: Final[tuple[ArtifactCheck, ...]] = (
    ArtifactCheck(
        arm="control_cheap",
        source=f"{EXP_025_RUN}/tables.md, drawdown by era, primary, full",
        max_drawdown_pct=-83.67,
        months_under_water=184,
    ),
    ArtifactCheck(
        arm="published_trend30",
        source=f"{EXP_025_RUN}/tables.md, primary arms",
        max_drawdown_pct=-82.78,
        months_under_water=164,
    ),
    ArtifactCheck(
        arm="ladder40",
        source=f"{EXP_025_RUN}/tables.md, primary arms",
        max_drawdown_pct=-53.77,
        months_under_water=74,
    ),
    ArtifactCheck(
        arm="ladder30",
        source=f"{EXP_025_RUN}/tables.md, primary arms",
        max_drawdown_pct=-41.7,
        months_under_water=69,
    ),
    ArtifactCheck(
        arm="working_default",
        source=f"{EXP_024_RUN}/tables.md, primary arms",
        max_drawdown_pct=-81.0,
        months_under_water=163,
    ),
)

#: 024's working default in 025's primary-panel wrappers and 016f's tournament tickers.
WORKING_DEFAULT_PRIMARY: Final = (("CORE", "RSST_LIKE", "TSY10"), (0.70, 0.25, 0.05))
WORKING_DEFAULT_TOURNAMENT: Final = (
    ("RSST", "VTI", "VXUS", "VTV", "AVDV", "IDMO", "AVES", "TSY10"),
    (0.25, 0.19, 0.16, 0.15, 0.10, 0.05, 0.05, 0.05),
)


# --------------------------------------------------------------------------- #
# Weight translation
# --------------------------------------------------------------------------- #


def tournament_targets(
    weights: Mapping[str, float],
    *,
    mappings: Mapping[str, FundMapping],
    vt_proxy: Mapping[str, float],
) -> tuple[tuple[str, ...], FloatArray]:
    """Site tickers to 016f basis tickers on the 1990 panel.

    ``VT`` has no basis expression of its own and becomes the cheap control's mix;
    ``SCHP`` becomes the modelled ten-year ``TSY10``; every other ticker must be one
    016f mapped.
    """
    out: dict[str, float] = {}
    for ticker, percent in weights.items():
        fraction = percent / 100.0
        if ticker == "VT":
            for proxy_ticker, proxy_weight in vt_proxy.items():
                out[proxy_ticker] = out.get(proxy_ticker, 0.0) + fraction * proxy_weight
        elif ticker == BOND_TICKER:
            out["TSY10"] = out.get("TSY10", 0.0) + fraction
        else:
            out[ticker] = out.get(ticker, 0.0) + fraction
    for ticker in out:
        if ticker not in mappings:
            raise SiteSeriesError(f"016f's basis mapping has no ticker {ticker!r}")
    return tuple(out), np.array(list(out.values()), dtype=np.float64)


def primary_targets(weights: Mapping[str, float]) -> tuple[tuple[str, ...], FloatArray]:
    """Site tickers to 025's primary-panel wrappers: stocks to CORE, RSST to RSST_LIKE."""
    out: dict[str, float] = {}
    for ticker, percent in weights.items():
        fraction = percent / 100.0
        if ticker in STOCK_TICKERS:
            key = "CORE"
        elif ticker == TREND_TICKER:
            key = "RSST_LIKE"
        elif ticker == BOND_TICKER:
            key = "TSY10"
        else:
            raise SiteSeriesError(f"no primary-panel wrapper for {ticker!r}")
        out[key] = out.get(key, 0.0) + fraction
    return tuple(out), np.array(list(out.values()), dtype=np.float64)


# --------------------------------------------------------------------------- #
# Summary statistics on one monthly path
# --------------------------------------------------------------------------- #


def _month_before(period: str) -> str:
    index = month_index(period) - 1
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def wealth_path(total: FloatArray, *, start: float = START_DOLLARS) -> FloatArray:
    """Dollars month by month from ``start``, the base month included."""
    return np.concatenate([[start], start * np.cumprod(1.0 + np.asarray(total, dtype=np.float64))])


def _cagr_pct(first: float, last: float, months: int) -> float:
    growth = float((last / first) ** (MONTHS_PER_YEAR / months))
    return round((growth - 1.0) * 100.0, 2)


def worst_fall(values: FloatArray, dates: Sequence[str]) -> dict[str, JsonValue]:
    """The deepest peak-to-trough fall, with the months it took to climb back.

    ``monthsToRecover`` counts months from the peak month to the first month back at
    or above it, so a peak in October 2007 recovered in January 2013 is 63 months.
    ``null`` when the fall is still open at the end of the window.
    """
    running_peak = np.maximum.accumulate(values)
    drawdown = values / running_peak - 1.0
    trough = int(np.argmin(drawdown))
    peak = int(np.argmax(values[: trough + 1]))
    recovered: int | None = None
    for index in range(trough + 1, values.size):
        if values[index] >= values[peak]:
            recovered = index
            break
    fall = float(drawdown[trough])
    return {
        "pct": round(fall * 100.0, 1),
        "peak": dates[peak],
        "trough": dates[trough],
        "recovered": None if recovered is None else dates[recovered],
        "monthsToRecover": None if recovered is None else recovered - peak,
        "dollarsAtTrough": round(START_DOLLARS * (1.0 + fall)),
    }


def calendar_years(total: FloatArray, periods: Sequence[str]) -> dict[str, float]:
    """Compound return of every calendar year the window holds in full, in percent."""
    by_year: dict[str, list[float]] = {}
    for period, value in zip(periods, total, strict=True):
        by_year.setdefault(period[:4], []).append(float(value))
    return {
        year: round((float(np.prod([1.0 + r for r in returns])) - 1.0) * 100.0, 1)
        for year, returns in by_year.items()
        if len(returns) == MONTHS_PER_YEAR
    }


def _span_return(total: FloatArray, periods: Sequence[str], start: str, end: str) -> float | None:
    keep = [i for i, p in enumerate(periods) if start <= p <= end]
    if not keep or periods[keep[0]] != start or periods[keep[-1]] != end:
        return None
    return round((float(np.prod(1.0 + total[keep])) - 1.0) * 100.0, 1)


def summarise(total: FloatArray, periods: Sequence[str]) -> dict[str, JsonValue]:
    """Every figure the site prints for one path, rounded as the schema says."""
    total = np.asarray(total, dtype=np.float64)
    if total.size != len(periods):
        raise SiteSeriesError(f"{total.size} returns against {len(periods)} periods")
    values = wealth_path(total)
    dates = [_month_before(periods[0]), *periods]
    years = calendar_years(total, periods)
    best = max(years.items(), key=lambda kv: kv[1]) if years else None
    worst = min(years.items(), key=lambda kv: kv[1]) if years else None
    since: dict[str, JsonValue] | None = None
    keep = [i for i, p in enumerate(periods) if p >= SINCE]
    if keep and periods[keep[0]] == SINCE:
        sub_total = total[keep]
        sub_values = wealth_path(sub_total)
        sub_dates = [_month_before(SINCE), *(periods[i] for i in keep)]
        fall = worst_fall(sub_values, sub_dates)
        since = {
            "start": SINCE,
            "final": round(float(sub_values[-1])),
            "cagrPct": _cagr_pct(START_DOLLARS, float(sub_values[-1]), len(keep)),
            "worstFallPct": fall["pct"],
        }
    return {
        "final": round(float(values[-1])),
        "cagrPct": _cagr_pct(START_DOLLARS, float(values[-1]), total.size),
        "worstFall": worst_fall(values, dates),
        "bestYear": None if best is None else {"year": int(best[0]), "pct": best[1]},
        "worstYear": None if worst is None else {"year": int(worst[0]), "pct": worst[1]},
        "calendarYears": dict(years),
        "episodes": {
            name: _span_return(total, periods, start, end)
            for name, (start, end) in EPISODES.items()
        },
        "since2009": since,
    }


def series_record(
    portfolio: SitePortfolio, total: FloatArray, periods: Sequence[str]
) -> dict[str, JsonValue]:
    values = wealth_path(total)
    rounded = [round(float(v)) for v in values]
    summary = summarise(total, periods)
    summary["final"] = rounded[-1]
    return {
        "id": portfolio.id,
        "label": portfolio.label,
        "weights": dict(portfolio.weights),
        "values": rounded,
        "dates": [_month_before(periods[0]), *periods],
        "summary": summary,
    }


# --------------------------------------------------------------------------- #
# The two panels
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Panels:
    """Everything the emitter needs, loaded once."""

    primary: BasisPanel
    wrappers: Mapping[str, Wrapper]
    rates: FinancingRates
    primary_costs: CostSettings
    primary_arms: Mapping[str, tuple[tuple[str, ...], tuple[float, ...]]]
    tournament: BasisPanel
    mappings: Mapping[str, FundMapping]
    tournament_costs: CostSettings
    tournament_arms: Mapping[str, tuple[tuple[str, ...], tuple[float, ...]]]
    cheap: Mapping[str, float]
    cheap60_40: Mapping[str, float]
    manifests: tuple[str, ...]
    spec_hash: str
    tournament_spec_hash: str


def load_panels(specification_path: Path | None = None) -> Panels:
    """025's primary and tournament panels from the pinned caches; never downloads."""
    specification = load_specification(specification_path or default_specification_path())
    raw, fii10, cpi, provenance, findings = load_series(specification)
    legs = build_legs(raw, fii10, cpi, specification, provenance=provenance, findings=findings)
    wrappers = read_wrappers(specification)
    rates = read_rates(specification)
    arms = read_arms(specification)
    inputs = load_tournament_inputs(specification, legs.core)

    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "tournament_panel", where="parameters"), where="tournament")
    controls = _mapping(_at(block, "controls", where="tournament_panel"), where="controls")
    cheap_tickers, cheap_weights = _read_weighted(
        _mapping(_at(controls, "cheap", where="controls"), where="cheap"), where="controls.cheap"
    )
    mix_tickers, mix_weights = _read_weighted(
        _mapping(_at(controls, "cheap60_40", where="controls"), where="cheap60_40"),
        where="controls.cheap60_40",
    )
    tournament_arms: dict[str, tuple[tuple[str, ...], tuple[float, ...]]] = {}
    for name, entry in _mapping(_at(block, "arms", where="tournament_panel"), where="arms").items():
        arm = _mapping(entry, where=f"arms.{name}")
        tournament_arms[name] = _read_weighted(
            _mapping(_at(arm, "weights", where=name), where="weights"), where=f"arms.{name}"
        )
    tournament_spec = load_specification(
        workspace_root() / _text(block, "specification_path", where="tournament_panel")
    )
    manifests = tuple(
        sorted({*_manifest_hashes(specification), *_manifest_hashes(tournament_spec)})
    )
    return Panels(
        primary=build_primary_panel(legs.core),
        wrappers=wrappers,
        rates=rates,
        primary_costs=_cost_settings(specification, rates),
        primary_arms={n: (a.tickers, a.weights) for n, a in arms.items()},
        tournament=inputs.panel,
        mappings=inputs.mappings,
        tournament_costs=inputs.costs,
        tournament_arms=tournament_arms,
        cheap=dict(zip(cheap_tickers, cheap_weights, strict=True)),
        cheap60_40=dict(zip(mix_tickers, mix_weights, strict=True)),
        manifests=manifests,
        spec_hash=specification.spec_hash,
        tournament_spec_hash=inputs.specification_hash,
    )


def primary_total(panels: Panels, tickers: Sequence[str], targets: FloatArray) -> FloatArray:
    """Monthly rebalancing, 025's primary-panel clock."""
    return simulate_arm(
        panels.primary,
        panels.wrappers,
        panels.rates,
        panels.primary_costs,
        tickers=tickers,
        targets=targets,
    ).total


def tournament_total(panels: Panels, tickers: Sequence[str], targets: FloatArray) -> FloatArray:
    """Annual rebalancing, 016f's clock."""
    return constant_weight_path(
        panels.tournament,
        panels.mappings,
        panels.tournament_costs,
        tickers=tickers,
        targets=targets,
    ).total


# --------------------------------------------------------------------------- #
# Verification against the committed artifacts
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckRow:
    panel: str
    arm: str
    expected_pct: float
    observed_pct: float
    expected_months: int
    observed_months: int
    source: str

    @property
    def matches(self) -> bool:
        return (
            abs(self.observed_pct - self.expected_pct) < 0.005 + 1e-9
            and self.observed_months == self.expected_months
        )


def _artifact_style(total: FloatArray) -> tuple[float, int]:
    """Max drawdown and months under water exactly as the experiments compute them."""
    summary = drawdown_summary(np.cumprod(1.0 + total))
    return round(summary.max_drawdown * 100.0, 2), summary.max_time_under_water


def verify(panels: Panels) -> list[CheckRow]:
    """Re-simulate every checked research arm on both panels and compare to the tables."""
    rows: list[CheckRow] = []

    def tournament_arm(name: str) -> FloatArray:
        if name == "control_cheap":
            weights: Mapping[str, float] = panels.cheap
        elif name == "control_cheap60_40":
            weights = panels.cheap60_40
        elif name == "working_default":
            weights = dict(zip(*WORKING_DEFAULT_TOURNAMENT, strict=True))
        else:
            weights = dict(zip(*panels.tournament_arms[name], strict=True))
        return tournament_total(panels, tuple(weights), np.array(list(weights.values())))

    def primary_arm(name: str) -> FloatArray:
        if name == "control_cheap":
            weights: Mapping[str, float] = {"CORE": 1.0}
        elif name == "working_default":
            weights = dict(zip(*WORKING_DEFAULT_PRIMARY, strict=True))
        else:
            weights = dict(zip(*panels.primary_arms[name], strict=True))
        return primary_total(panels, tuple(weights), np.array(list(weights.values())))

    for panel_id, checks, simulate in (
        ("1990", TOURNAMENT_CHECKS, tournament_arm),
        ("1929", PRIMARY_CHECKS, primary_arm),
    ):
        for check in checks:
            observed_pct, observed_months = _artifact_style(simulate(check.arm))
            rows.append(
                CheckRow(
                    panel=panel_id,
                    arm=check.arm,
                    expected_pct=check.max_drawdown_pct,
                    observed_pct=observed_pct,
                    expected_months=check.months_under_water,
                    observed_months=observed_months,
                    source=check.source,
                )
            )
    return rows


def render_checks(rows: Sequence[CheckRow]) -> str:
    lines = [
        "| panel | research arm | artifact worst fall (months) | rebuilt | match |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.panel} | `{row.arm}` | {row.expected_pct:.2f} ({row.expected_months}) | "
            f"{row.observed_pct:.2f} ({row.observed_months}) | {'yes' if row.matches else 'NO'} |"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# The files
# --------------------------------------------------------------------------- #

BASIS_1990: Final = (
    "These are simulated portfolios built from index data, not the records of real funds. "
    "Each fund is stood in for by the mix of market and style indexes it tracks, less its "
    "fee and a trading charge, from November 1990 to May 2026, rebalanced once a year. "
    "The plain world stock index is 65% US stocks and 35% stocks outside the US on the same "
    "basis, and the 60/40 line puts 40% of that mix into bonds. The one-fund portfolio uses "
    "that same 65/35 mix to stand in for VT. The trend part is an index of trend-following "
    "returns before trading costs; the fund that supplies it, RSST, has its own record only "
    "from September 2023. The bond part is a plain ten-year US government bond standing in "
    "for the inflation-protected bonds the portfolio holds, because no inflation-protected "
    "series exists before 2003. Dollar figures are before tax, in the dollars of each year."
)

BASIS_1929: Final = (
    "These are simulated portfolios built from index data, not the records of real funds, "
    "over January 1929 to May 2025, rebalanced every month. On this long history every "
    "stock fund is the whole US stock market at a fee of 0.03% a year, so the one-fund "
    "portfolio and the plain stock index are the same line and the value lean cannot be "
    "shown at all; the international and value parts have no series this far back. The "
    "trend part is a simple trend-following rule run on four markets, before trading costs; "
    "the fund that supplies it, RSST, has its own record only from September 2023. The bond "
    "part is a plain ten-year US government bond standing in for the inflation-protected "
    "bonds the portfolio holds, because no inflation-protected series exists before 2003. "
    "Dollar figures over 96 years are before tax and in the dollars of each year, so they "
    "run into the millions; the compound growth a year and the size of the 1929 to 1932 "
    "fall are the numbers to read."
)


def _window(periods: Sequence[str]) -> dict[str, JsonValue]:
    return {
        "start": periods[0],
        "end": periods[-1],
        "months": len(periods),
        "label": f"{periods[0][:4]} to {periods[-1][:4]}",
    }


def build_file(panels: Panels, *, window: str, generated_at: str) -> dict[str, JsonValue]:
    """One of the two files, every printed portfolio rebuilt on the named panel."""
    series: list[JsonValue] = []
    if window == "1990":
        periods = panels.tournament.periods
        for portfolio in SITE_PORTFOLIOS:
            tickers, targets = tournament_targets(
                portfolio.weights, mappings=panels.mappings, vt_proxy=panels.cheap
            )
            total = tournament_total(panels, tickers, targets)
            series.append(series_record(portfolio, total, periods))
        basis = BASIS_1990
        experiments = ["exp_016e", "exp_016f", "exp_024", "exp_025"]
    elif window == "1929":
        periods = panels.primary.periods
        for portfolio in SITE_PORTFOLIOS:
            if not portfolio.on_long_panel:
                continue
            tickers, targets = primary_targets(portfolio.weights)
            total = primary_total(panels, tickers, targets)
            series.append(series_record(portfolio, total, periods))
        basis = BASIS_1929
        experiments = ["exp_018", "exp_024", "exp_025"]
    else:
        raise SiteSeriesError(f"unknown window {window!r}")
    return {
        "generatedAt": generated_at,
        "window": _window(periods),
        "basis": basis,
        "episodeDefinitions": dict(EPISODE_DEFINITIONS),
        "provenance": {
            "experiments": experiments,
            "artifacts": [EXP_016E_RUN, EXP_024_RUN, EXP_025_RUN],
            "specificationHashes": {
                "exp_025": panels.spec_hash,
                "exp_016f": panels.tournament_spec_hash,
            },
            "manifests": list(panels.manifests),
            "generatedBy": "research/src/portfolio_edge/reporting/site_series.py",
        },
        "start": int(START_DOLLARS),
        "series": series,
    }


def default_output_dir() -> Path:
    return workspace_root().parent / "src" / "content" / "series"


def write_files(
    panels: Panels, *, out_dir: Path, generated_at: str
) -> tuple[tuple[Path, dict[str, JsonValue]], ...]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[tuple[Path, dict[str, JsonValue]]] = []
    for window in ("1990", "1929"):
        payload = build_file(panels, window=window, generated_at=generated_at)
        path = out_dir / f"portfolios-{window}.json"
        path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
        written.append((path, payload))
    return tuple(written)


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def render_numbers(payload: Mapping[str, JsonValue]) -> str:
    """The headline numbers of one file, as a Markdown table."""
    window = payload["window"]
    assert isinstance(window, Mapping)
    lines = [
        f"| series ({window['label']}) | $10,000 became | growth a year | worst fall | "
        "peak to trough to recovered (months) | at the trough | 2000-02 | 2008 | 2020 | 2022 |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    series = payload["series"]
    assert isinstance(series, Sequence)
    for item in series:
        assert isinstance(item, Mapping)
        summary = item["summary"]
        assert isinstance(summary, Mapping)
        fall = summary["worstFall"]
        assert isinstance(fall, Mapping)
        episodes = summary["episodes"]
        assert isinstance(episodes, Mapping)

        def pct(value: JsonValue) -> str:
            return "--" if value is None else f"{float(str(value)):+.1f}%"

        lines.append(
            f"| `{item['id']}` | ${int(str(summary['final'])):,} | {summary['cagrPct']}% | "
            f"{fall['pct']}% | {fall['peak']} / {fall['trough']} / {fall['recovered']} "
            f"({fall['monthsToRecover']}) | ${int(str(fall['dollarsAtTrough'])):,} | "
            f"{pct(episodes['dotcom-2000-02'])} | {pct(episodes['gfc-2008'])} | "
            f"{pct(episodes['covid-2020'])} | {pct(episodes['rates-2022'])} |"
        )
    return "\n".join(lines)


def _artifact_record(path: Path, root: Path) -> ArtifactRecord:
    data = path.read_bytes()
    return ArtifactRecord(
        path=path.relative_to(root).as_posix(),
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        kind="json",
    )


def record_in_ledger(
    ledger: Ledger, *, panels: Panels, written: Sequence[Path], origin: Origin
) -> LedgerEntry:
    """One ``succeeded`` line with no specification hash.

    A descriptive re-emission tests no hypothesis, so it carries no ``spec_hash`` and
    does not enter the distinct-specification bound; it is a run of code, and the
    ledger records what was actually run.
    """
    root = workspace_root().parent
    git = capture_git_state()
    entry = LedgerEntry(
        run_id=new_run_id(),
        experiment_family=FAMILY,
        timestamp_utc=datetime.now(UTC).isoformat(),
        event=LedgerEvent.SUCCEEDED,
        status=RunStatus.SUCCEEDED,
        git_commit=git.commit,
        worktree_dirty=git.dirty,
        diff_sha256=git.diff_sha256,
        spec_hash=None,
        dataset_manifest_hashes=panels.manifests,
        code_version=code_version(),
        environment=environment_snapshot(),
        parameters={
            "portfolios": {p.id: dict(p.weights) for p in SITE_PORTFOLIOS},
            "windows": {
                "1990": f"{panels.tournament.periods[0]}..{panels.tournament.periods[-1]}",
                "1929": f"{panels.primary.periods[0]}..{panels.primary.periods[-1]}",
            },
            "exp_025_specification_hash": panels.spec_hash,
            "exp_016f_specification_hash": panels.tournament_spec_hash,
        },
        artifacts=tuple(_artifact_record(p, root) for p in written),
        parent_run_id=EXP_025_RUN,
        origin=origin,
        notes=(
            "Descriptive re-emission of Experiment 025's scored arms at the site's printed "
            "weights, for src/content/series/. Not a hypothesis test and not a new "
            "specification; carries no spec_hash and adds nothing to the trial bound. Every "
            "checked research arm reproduced the committed tables before the files were written."
        ),
    )
    return ledger.append(entry)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.reporting.site_series",
        description="Rebuild the site's printed portfolios on 025's two panels and emit JSON.",
    )
    parser.add_argument("--specification", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--no-ledger", action="store_true", help="do not append a ledger line")
    parser.add_argument(
        "--origin", choices=[item.value for item in Origin], default=Origin.AI.value
    )
    arguments = parser.parse_args(argv)

    panels = load_panels(arguments.specification)
    rows = verify(panels)
    print("Verification against the committed artifact tables:\n")
    print(render_checks(rows))
    failed = [row for row in rows if not row.matches]
    if failed:
        print(f"\n{len(failed)} research arm(s) did not reproduce; nothing written.")
        return 1

    generated_at = datetime.now(UTC).date().isoformat()
    out_dir = arguments.out_dir if arguments.out_dir is not None else default_output_dir()
    written = write_files(panels, out_dir=out_dir, generated_at=generated_at)
    for path, payload in written:
        print(f"\nWrote {path}\n")
        print(render_numbers(payload))
    if not arguments.no_ledger:
        entry = record_in_ledger(
            Ledger(arguments.ledger),
            panels=panels,
            written=[p for p, _ in written],
            origin=Origin(arguments.origin),
        )
        print(f"\nledger: {entry.run_id} ({FAMILY}, no spec_hash)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
