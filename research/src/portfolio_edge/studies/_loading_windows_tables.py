"""Regenerates every table in ``docs/research/loading-comparability-and-wrapper-exposure.md``.

Kept separate from :mod:`portfolio_edge.studies.loading_windows` so the study stays pure
and testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies.loading_windows

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen, no experiment is registered for them, and nothing below may promote a sleeve.
What it does is measure two things the repository had recorded as unmeasurable or had
published in a form that cannot be read:

1. **A stacked wrapper's delivered trend exposure.** RSST's own monthly total return is
   filed in Item B.5 of Form N-PORT, so it can be regressed like any other fund. RSSB —
   same sponsor, same wrapper, bonds instead of trend — is the negative control, and the
   design is only worth anything if RSSB comes back near zero.
2. **The US value shelf and the managed-futures shelf on matched windows.** Every
   published loading was fitted on the fund's own filed history, so the windows differ and
   the published numbers cannot be ranked against one another. Each is first reproduced on
   its own window, which is what proves the method, and then refitted on the window every
   fund shares.

Sources, all already used by registered experiments:

* Form N-PORT Item B.5, per share class, via :mod:`portfolio_edge.data.nport`.
* AQR's Time Series Momentum factor workbook, the series Experiments 004 and 008 used,
  pinned to the same raw hash Experiment 008 froze.
* Ken French's US and developed-ex-US FF5 and momentum files, for the factor panels and
  for the one-month bill that defines every excess return here.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from portfolio_edge.data import aqr, french, nport
from portfolio_edge.data.cache import RawCache
from portfolio_edge.studies.loading_windows import (
    LoadingEstimate,
    Window,
    common_window,
    estimate_loadings,
    rank,
    rolling_windows,
    window_ending,
)

#: Experiments 008, 009 and 013 all fix six lags, and every reproduction below is against
#: one of those three. Changing it here would make a "reproduction" a different estimator.
HAC_LAGS: Final = 6

#: The last month of the frozen common period in Experiments 008, 009 and 013.
PUBLISHED_LAST_MONTH: Final = "2025-12"

#: AQR reconstructs its whole history on each update, so an unrecognised hash is a new
#: vintage rather than a corrupt download. Experiment 008 froze this one and aborts on a
#: mismatch; this study does the same, for the same reason.
AQR_EXPECTED_SHA256: Final = "33470930e2269c0d97be4732ec2d9c27ddbc69ac8133b059a263e27400263eeb"

FF5_FACTORS: Final = ("Mkt-RF", "SMB", "HML", "RMW", "CMA")


@dataclass(frozen=True, slots=True, kw_only=True)
class Fund:
    """One share class, and where to find its filings."""

    ticker: str
    series_id: str
    class_id: str
    inception: str | None = None
    """Commencement of operations, ``YYYY-MM-DD``, from the fund's own prospectus.

    Present only where the first filed month is a *stub*: a fund that began trading on the
    5th files an Item B.5 return covering three quarters of a month, and regressing that
    against a whole month of factor returns attenuates every coefficient. Where it is
    given, the first whole calendar month after it is the floor.
    """


#: The wrappers and the trend funds they are compared with. Series and class identifiers
#: come from the SEC's own ticker map where it carries them; MATE and CTAP are absent from
#: that file and are resolved from the quarterly N-PORT census by registered series name,
#: which is the fact ``docs/research/trend-marginal-value.md`` records.
RSST: Final = Fund(
    ticker="RSST",
    series_id="S000081720",
    class_id="C000244698",
    inception="2023-09-05",
)
RSSB: Final = Fund(ticker="RSSB", series_id="S000079703", class_id="C000240950")
DBMF: Final = Fund(ticker="DBMF", series_id="S000072813", class_id="C000229357")

TREND_FUNDS: Final[tuple[Fund, ...]] = (
    DBMF,
    Fund(ticker="CTA", series_id="S000075092", class_id="C000233897"),
    Fund(ticker="KMLM", series_id="S000070143", class_id="C000223083"),
    Fund(ticker="FMF", series_id="S000037848", class_id="C000116776"),
    Fund(ticker="WTMF", series_id="S000026387", class_id="C000079238"),
)

#: Published TSMOM loadings and month counts from ``src/content/shelf.ts``, which carries
#: Experiment 008's results. Reproducing these is the check that the method is the method.
PUBLISHED_TREND: Final[Mapping[str, tuple[float, int]]] = {
    "DBMF": (0.671, 54),
    "CTA": (0.475, 46),
    "KMLM": (0.245, 60),
    "FMF": (0.303, 78),
    "WTMF": (0.099, 76),
}

VALUE_FUNDS: Final[tuple[Fund, ...]] = (
    Fund(ticker="VTV", series_id="S000002840", class_id="C000007778"),
    Fund(ticker="AVLV", series_id="S000072998", class_id="C000229747"),
    Fund(ticker="DFLV", series_id="S000078987", class_id="C000239809"),
    Fund(ticker="DFUV", series_id="S000075030", class_id="C000233732"),
    Fund(ticker="AVUV", series_id="S000066459", class_id="C000214354"),
    Fund(ticker="DFSV", series_id="S000075151", class_id="C000233987"),
    Fund(ticker="DFAT", series_id="S000070901", class_id="C000225165"),
    Fund(ticker="RPV", series_id="S000060792", class_id="C000197608"),
    Fund(ticker="VBR", series_id="S000002847", class_id="C000007804"),
)

#: Published HML loadings and month counts from ``src/content/shelf.ts`` (Experiment 013).
PUBLISHED_VALUE_HML: Final[Mapping[str, tuple[float, int]]] = {
    "VTV": (0.337, 72),
    "AVLV": (0.322, 51),
    "DFLV": (0.637, 36),
    "DFUV": (0.515, 43),
    "AVUV": (0.537, 72),
    "DFSV": (0.442, 46),
    "DFAT": (0.433, 54),
    "RPV": (0.710, 72),
    "VBR": (0.410, 72),
}

#: Three ex-US products, on Experiment 009's own panel, used only to check that the
#: window-from-month-count derivation holds outside the US audit too.
EXUS_CHECKS: Final[tuple[tuple[Fund, int, Mapping[str, float]], ...]] = (
    (
        Fund(ticker="AVDV", series_id="S000066457", class_id="C000214352"),
        75,
        {"HML": 0.510, "SMB": 0.671, "RMW": 0.386},
    ),
    (
        Fund(ticker="DISV", series_id="S000075153", class_id="C000233989"),
        45,
        {"HML": 0.495, "SMB": 0.431},
    ),
    (
        Fund(ticker="IVLU", series_id="S000049573", class_id="C000156614"),
        77,
        {"HML": 0.475},
    ),
)

#: Newer stacked wrappers. Their filed histories are counted and reported; none is long
#: enough to regress, and reporting the count instead of an estimate is the finding.
YOUNG_WRAPPERS: Final[tuple[Fund, ...]] = (
    Fund(ticker="MATE", series_id="S000097969", class_id="C000267520"),
    Fund(ticker="CTAP", series_id="S000096492", class_id="C000265327", inception="2025-12-08"),
    Fund(ticker="JPFP", series_id="S000101300", class_id="", inception="2026-05-27"),
)

#: A three-parameter regression on fewer than this many months reports a window, not a
#: fund. Experiments 009 and 013 both use 36; this study will not estimate below it.
MINIMUM_MONTHS: Final = 36


class LoadingWindowsError(RuntimeError):
    """A source did not carry what this study needs, and guessing was refused."""


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


def fund_returns(cache: RawCache, fund: Fund) -> dict[str, float]:
    """One share class' filed monthly total returns, ``{YYYY-MM: decimal}``.

    A launch stub is dropped where the fund's commencement date is known and it did not
    trade the whole of its first filed month. Nothing else is removed, and nothing is
    filled in: a month with no filed return is simply absent.
    """
    refs = [
        ref
        for ref in nport.filing_index(cache, fund.series_id)
        if ref.form_type.startswith("NPORT-P")
    ]
    filings = []
    for ref in refs:
        filings.append(nport.fetch_filing(cache, ref))
        nport.throttle()
    if not filings:
        return {}
    table = nport.build_return_table(
        filings, class_id=fund.class_id, table_id=f"nport_{fund.ticker.lower()}_monthly"
    )
    series = {
        period: float(row[0])
        for period, row in zip(table.periods, table.values, strict=True)
        if row[0] is not None
    }
    if fund.inception is not None:
        floor = _first_whole_month(fund.inception)
        series = {period: value for period, value in series.items() if period >= floor}
    return series


def _first_whole_month(inception: str) -> str:
    """The first calendar month the fund traded in full, from ``YYYY-MM-DD``.

    A fund that commenced on the 1st traded its first month in full; any later day makes
    that month a stub whose beta is attenuated by the fraction of the month it did not
    exist. This is Experiment 013's launch-cut rule, applied to a wrapper.
    """
    year, month, day = int(inception[:4]), int(inception[5:7]), int(inception[8:10])
    if day == 1:
        return f"{year:04d}-{month:02d}"
    index = year * 12 + month  # already the following month, zero-based
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


@dataclass(frozen=True, slots=True, kw_only=True)
class Panel:
    """A factor panel and its cash rate, keyed by ``YYYY-MM``."""

    name: str
    rows: Mapping[str, Mapping[str, float]]
    factors: tuple[str, ...]


def load_french_panel(cache: RawCache, region: str) -> Panel:
    """FF5 plus momentum for ``region``, on one month grid, in decimals."""
    ff5 = french.get_dataset(f"french_{region}_ff5")
    parsed = french.parse(cache, cache.require(ff5.url), dataset=ff5)
    monthly = next(table for table in parsed.tables if table.frequency == "monthly")
    momentum_set = french.get_dataset(f"french_{region}_momentum")
    momentum_parsed = french.parse(cache, cache.require(momentum_set.url), dataset=momentum_set)
    momentum_table = next(table for table in momentum_parsed.tables if table.frequency == "monthly")
    momentum = {
        str(period)[:7]: row[0]
        for period, row in zip(momentum_table.periods, momentum_table.values, strict=True)
        if row[0] is not None
    }
    rows: dict[str, dict[str, float]] = {}
    for period, row in zip(monthly.periods, monthly.values, strict=True):
        label = str(period)[:7]
        if label not in momentum or any(value is None for value in row):
            continue
        entry = {
            name: float(value)
            for name, value in zip(monthly.columns, row, strict=True)
            if value is not None
        }
        entry["UMD"] = float(momentum[label])
        rows[label] = entry
    return Panel(name=region, rows=rows, factors=(*FF5_FACTORS, "UMD"))


def load_tsmom(cache: RawCache) -> dict[str, float]:
    """AQR's TSMOM factor, pinned to the hash Experiment 008 froze."""
    dataset = aqr.get_dataset("aqr_tsmom_factors")
    entry = cache.require(dataset.url)
    if entry.sha256 != AQR_EXPECTED_SHA256:
        raise LoadingWindowsError(
            f"the AQR workbook now hashes to {entry.sha256}, not the "
            f"{AQR_EXPECTED_SHA256} Experiment 008 froze. AQR rebuilds its whole history "
            "on every update, so this is a new vintage; freeze it deliberately rather "
            "than reporting a loading against an unrecognised file."
        )
    parsed = aqr.parse(cache, entry, dataset=dataset)
    column = parsed.table.column("TSMOM")
    return {
        str(period)[:7]: float(value)
        for period, value in zip(parsed.table.periods, column, strict=True)
        if value is not None
    }


# --------------------------------------------------------------------------- #
# Fits
# --------------------------------------------------------------------------- #


def _contiguous_tail(months: Sequence[str], window: Window | None) -> tuple[str, ...]:
    """The longest contiguous run inside ``window``, ending as late as the data allows."""
    inside = [
        month
        for month in sorted(months)
        if window is None or window.first <= month <= window.last
    ]
    if not inside:
        return ()
    run: list[str] = [inside[-1]]
    for month in reversed(inside[:-1]):
        previous = run[0]
        if int(month[:4]) * 12 + int(month[5:7]) + 1 == int(previous[:4]) * 12 + int(previous[5:7]):
            run.insert(0, month)
        else:
            break
    return tuple(run)


def fit_on_panel(
    *,
    fund: Fund,
    returns: Mapping[str, float],
    panel: Panel,
    months: Sequence[str],
) -> dict[str, LoadingEstimate]:
    """FF5 + momentum, fund excess return over the one-month bill in the same file."""
    chosen = tuple(months)
    design = {
        name: [panel.rows[month][name] for month in chosen] for name in panel.factors
    }
    return estimate_loadings(
        ticker=fund.ticker,
        benchmark=f"french-{panel.name}",
        periods=chosen,
        excess_returns=[returns[month] - panel.rows[month]["RF"] for month in chosen],
        design=design,
        n_lags=HAC_LAGS,
    )


def fit_on_trend(
    *,
    fund: Fund,
    returns: Mapping[str, float],
    tsmom: Mapping[str, float],
    cash: Mapping[str, float],
    months: Sequence[str],
    market: Mapping[str, float] | None = None,
) -> dict[str, LoadingEstimate]:
    """Excess fund return on the AQR TSMOM index, optionally with the market beside it.

    Experiment 008 regressed standalone trend funds on TSMOM alone, because a standalone
    trend fund has no equity leg to hold constant. A *stacked* wrapper does: RSST is one
    dollar of US equity plus one dollar of trend, so omitting the market would push its
    equity return into whatever the trend index happened to do in the same months. The
    market term is the difference between measuring a wrapper and measuring a fund.
    """
    chosen = tuple(months)
    design: dict[str, list[float]] = {}
    if market is not None:
        design["MKT"] = [market[month] for month in chosen]
    design["TSMOM"] = [tsmom[month] for month in chosen]
    return estimate_loadings(
        ticker=fund.ticker,
        benchmark="aqr-tsmom",
        periods=chosen,
        excess_returns=[returns[month] - cash[month] for month in chosen],
        design=design,
        n_lags=HAC_LAGS,
    )


def reproduction_gap(estimate: LoadingEstimate, published: float) -> float:
    """How far a refit lands from the number the shelf publishes."""
    return abs(estimate.value - published)


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


def _print_estimate(label: str, estimate: LoadingEstimate) -> None:
    print(f"  {label:<26s} {estimate.format()}")


def main() -> None:  # pragma: no cover - a reporting entry point
    cache = RawCache()
    us = load_french_panel(cache, "us")
    exus = load_french_panel(cache, "developed_ex_us")
    tsmom = load_tsmom(cache)
    cash = {month: row["RF"] for month, row in us.rows.items()}
    market = {month: row["Mkt-RF"] for month, row in us.rows.items()}

    print("=" * 78)
    print("1. A stacked wrapper's trend loading, from its own filings")
    print("=" * 78)
    wrapper_returns = {
        fund.ticker: fund_returns(cache, fund) for fund in (RSST, RSSB, DBMF)
    }
    rsst_months = _contiguous_tail(
        [m for m in wrapper_returns["RSST"] if m in tsmom and m in us.rows], None
    )
    print(f"RSST filed months used: {len(rsst_months)} {rsst_months[0]}..{rsst_months[-1]}")
    rsst = fit_on_trend(
        fund=RSST,
        returns=wrapper_returns["RSST"],
        tsmom=tsmom,
        cash=cash,
        months=rsst_months,
        market=market,
    )
    _print_estimate("RSST trend", rsst["TSMOM"])
    _print_estimate("RSST equity beta", rsst["MKT"])

    halves = (rsst_months[: len(rsst_months) // 2], rsst_months[len(rsst_months) // 2 :])
    for label, half in zip(("first half", "second half"), halves, strict=True):
        piece = fit_on_trend(
            fund=RSST,
            returns=wrapper_returns["RSST"],
            tsmom=tsmom,
            cash=cash,
            months=half,
            market=market,
        )
        _print_estimate(f"RSST trend, {label}", piece["TSMOM"])

    print()
    print("The negative control: same sponsor, same wrapper, bonds instead of trend")
    rssb_months = _contiguous_tail(
        [m for m in wrapper_returns["RSSB"] if m in tsmom and m in us.rows], None
    )
    rssb = fit_on_trend(
        fund=RSSB,
        returns=wrapper_returns["RSSB"],
        tsmom=tsmom,
        cash=cash,
        months=rssb_months,
        market=market,
    )
    _print_estimate("RSSB trend", rssb["TSMOM"])
    _print_estimate("RSSB equity beta", rssb["MKT"])

    print()
    print("RSST against a held trend fund rather than against a vendor index")
    shared = tuple(m for m in rsst_months if m in wrapper_returns["DBMF"])
    dbmf_excess = {m: wrapper_returns["DBMF"][m] - cash[m] for m in shared}
    on_dbmf = estimate_loadings(
        ticker="RSST",
        benchmark="dbmf-excess",
        periods=shared,
        excess_returns=[wrapper_returns["RSST"][m] - cash[m] for m in shared],
        design={"MKT": [market[m] for m in shared], "DBMF": [dbmf_excess[m] for m in shared]},
        n_lags=HAC_LAGS,
    )
    _print_estimate("RSST on DBMF", on_dbmf["DBMF"])
    _print_estimate("RSST equity beta", on_dbmf["MKT"])
    dbmf_here = fit_on_trend(
        fund=DBMF, returns=wrapper_returns["DBMF"], tsmom=tsmom, cash=cash, months=shared
    )
    _print_estimate("DBMF trend, same months", dbmf_here["TSMOM"])

    print()
    print("Younger wrappers: filed months, and no estimate")
    for fund in YOUNG_WRAPPERS:
        series = fund_returns(cache, fund) if fund.class_id else {}
        print(
            f"  {fund.ticker:<6s} {len(series)} filed month(s)"
            + (f" {min(series)}..{max(series)}" if series else " — no Form N-PORT at all")
            + f"; {MINIMUM_MONTHS} needed, so no loading is reported"
        )

    print()
    print("=" * 78)
    print("2. The managed-futures shelf: published windows, then matched windows")
    print("=" * 78)
    trend_returns = {fund.ticker: fund_returns(cache, fund) for fund in TREND_FUNDS}
    own: dict[str, LoadingEstimate] = {}
    for fund in TREND_FUNDS:
        published, months = PUBLISHED_TREND[fund.ticker]
        window = window_ending(PUBLISHED_LAST_MONTH, months)
        chosen = _contiguous_tail(
            [m for m in trend_returns[fund.ticker] if m in tsmom], window
        )
        estimate = fit_on_trend(
            fund=fund,
            returns=trend_returns[fund.ticker],
            tsmom=tsmom,
            cash=cash,
            months=chosen,
        )["TSMOM"]
        own[fund.ticker] = estimate
        gap = reproduction_gap(estimate, published)
        print(f"  {fund.ticker:<6s} published {published:+.3f}  refit {estimate.format()}")
        print(f"         reproduction gap {gap:.4f}")

    matched = common_window([estimate.window for estimate in own.values()])
    print(f"\n  Common window across the five: {matched.label} ({matched.months} months)")
    matched_estimates = [
        fit_on_trend(
            fund=fund,
            returns=trend_returns[fund.ticker],
            tsmom=tsmom,
            cash=cash,
            months=[m for m in matched.periods() if m in trend_returns[fund.ticker] and m in tsmom],
        )["TSMOM"]
        for fund in TREND_FUNDS
    ]
    for estimate in rank(matched_estimates):
        _print_estimate(estimate.ticker, estimate)

    # The wrapper-comparable window. RSST is the binding constraint at one end and the
    # slowest filer at the other, so this is the intersection of RSST's window with every
    # trend fund's filed history -- not RSST's window trimmed per fund, which would put
    # each fund on a different set of months and lose the comparability being bought.
    shared_trend = set(rsst["TSMOM"].window.periods()) & set(tsmom)
    for fund in TREND_FUNDS:
        shared_trend &= set(trend_returns[fund.ticker])
    trend_run = _contiguous_tail(sorted(shared_trend), None)
    print(
        f"\n  The wrapper-comparable window instead: {trend_run[0]}..{trend_run[-1]} "
        f"({len(trend_run)} months), where RSST and all five trend funds overlap"
    )
    comparable = [
        fit_on_trend(
            fund=fund,
            returns=trend_returns[fund.ticker],
            tsmom=tsmom,
            cash=cash,
            months=trend_run,
        )["TSMOM"]
        for fund in TREND_FUNDS
    ]
    comparable.append(
        fit_on_trend(
            fund=RSST,
            returns=wrapper_returns["RSST"],
            tsmom=tsmom,
            cash=cash,
            months=trend_run,
            market=market,
        )["TSMOM"]
    )
    for estimate in sorted(comparable, key=lambda item: item.value, reverse=True):
        _print_estimate(estimate.ticker, estimate)

    print()
    print("=" * 78)
    print("3. The US value shelf: published windows, then the matched window")
    print("=" * 78)
    value_returns = {fund.ticker: fund_returns(cache, fund) for fund in VALUE_FUNDS}
    published_windows: list[Window] = []
    for fund in VALUE_FUNDS:
        published, months = PUBLISHED_VALUE_HML[fund.ticker]
        window = window_ending(PUBLISHED_LAST_MONTH, months)
        published_windows.append(window)
        chosen = _contiguous_tail(
            [m for m in value_returns[fund.ticker] if m in us.rows], window
        )
        estimate = fit_on_panel(
            fund=fund, returns=value_returns[fund.ticker], panel=us, months=chosen
        )["HML"]
        print(f"  {fund.ticker:<6s} published {published:+.3f}  refit {estimate.format()}")
        print(f"         reproduction gap {reproduction_gap(estimate, published):.4f}")

    matched_value = common_window(published_windows)
    print(
        f"\n  Matched window: {matched_value.label} ({matched_value.months} months), the "
        "intersection of the nine published windows"
    )
    matched_value_estimates = [
        fit_on_panel(
            fund=fund,
            returns=value_returns[fund.ticker],
            panel=us,
            months=matched_value.periods(),
        )["HML"]
        for fund in VALUE_FUNDS
    ]
    for estimate in rank(matched_value_estimates):
        _print_estimate(estimate.ticker, estimate)

    print()
    print("  VTV's own rolling 36-month HML loading, to size the instability:")
    vtv_months = _contiguous_tail([m for m in value_returns["VTV"] if m in us.rows], None)
    rolling = [
        fit_on_panel(
            fund=VALUE_FUNDS[0],
            returns=value_returns["VTV"],
            panel=us,
            months=window.periods(),
        )["HML"]
        for window in rolling_windows(vtv_months, 36)
    ]
    low = min(rolling, key=lambda item: item.value)
    high = max(rolling, key=lambda item: item.value)
    print(f"    {len(rolling)} windows, {low.value:.3f} ({low.window.label}) to "
          f"{high.value:.3f} ({high.window.label})")

    print()
    print("=" * 78)
    print("4. The window-from-month-count derivation, checked outside the US audit")
    print("=" * 78)
    for fund, months, expected in EXUS_CHECKS:
        window = window_ending(PUBLISHED_LAST_MONTH, months)
        series = fund_returns(cache, fund)
        chosen = _contiguous_tail([m for m in series if m in exus.rows], window)
        fitted = fit_on_panel(fund=fund, returns=series, panel=exus, months=chosen)
        for factor, published in expected.items():
            estimate = fitted[factor]
            print(
                f"  {fund.ticker:<6s} {factor:<4s} published {published:+.3f} "
                f"refit {estimate.value:+.3f} on {estimate.window.label} "
                f"(gap {reproduction_gap(estimate, published):.4f})"
            )

    print()
    print(json.dumps({"hac_lags": HAC_LAGS, "aqr_sha256": AQR_EXPECTED_SHA256}))


if __name__ == "__main__":  # pragma: no cover - a reporting entry point
    main()
