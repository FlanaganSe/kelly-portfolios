"""Regenerates the cross-engine stress table in ``docs/research/alternative-sleeves-audit.md``.

Kept separate from :mod:`portfolio_edge.studies.stress_dependence` so the study stays pure
and testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies._stress_dependence_tables

**Everything this prints is `exploratory`.** No specification was frozen before the
numbers were seen; the stress windows are the ones
``docs/research/evidence-base.md`` already lists and were chosen by eye from history; and
several legs are vendor series that their author reconstructs on every release. The output
is a *dependence map* — which engines fall together — not an estimate of any premium.

The panel, and what each leg actually is
-----------------------------------------
The base is US equity, Ken French ``Mkt-RF``, and cash is the same file's ``RF``. Using
one file for both avoids the cash-series substitution :mod:`portfolio_edge.data.fred`
exists to block. Every engine below is an **excess return over cash**, so the rows are
comparable and none of them is a total return.

===========================  ==========================================  ==================
Leg                          Source                                       Coverage
===========================  ==========================================  ==================
``equity``                   French ``Mkt-RF``                            1926-07 onward
``treasury``                 Goyal-Welch ``ltr`` minus ``Rfree``          1926-01…2025-12
``credit_unhedged``          Goyal-Welch ``corpr`` minus ``Rfree``        1926-01…2025-12
``credit_duration_hedged``   AQR ``CORP_XS``                              1926-01…2014-12
``commodity``                AQR equal-weight commodity excess            1877-02…2025-05
``trend``                    AQR ``TSMOM``                                1985-01…2026-05
``gold``                     World Bank Pink Sheet, minus cash and carry  1968-01 onward
``bab``                      AQR ``BAB`` US leg                           1930-12…2026-05
``bitcoin``                  FRED ``CBBTCUSD`` month-end, minus cash      2015-01 onward
===========================  ==========================================  ==================

Four of those need their trap stated at the point of use, not in a footnote:

* **``credit_duration_hedged`` is the only true duration-hedged credit series held.**
  AQR defines ``CORP_XS`` as the corporate total return less a *duration-matched*
  government return, so adding cash to it does not produce a corporate bond total return
  and it may never be summed with ``treasury``. It also ends in 2014-12, so it sees
  1929-32, 1973-74, 1987, 1998, 2000-02 and 2008-09 and sees **none** of 2020 or 2022.
* **``credit_unhedged`` is not a credit engine.** ``corpr`` and ``ltr`` are not
  duration-matched, so ``corpr - RF`` is credit *plus* roughly twenty years of duration.
  It is printed beside the hedged leg precisely so the difference is visible.
* **``gold`` before 1971-08 is an administered peg**, and a US person could not legally
  own bullion until 1974-12-31. :data:`GOLD_FIRST_MONTH` starts the leg in 1975-01 for
  that reason, and the excluded window is reported rather than silently dropped.
  The Pink Sheet is a monthly *average* of daily fixes, which understates volatility and
  biases a Sharpe ratio upward; see :mod:`portfolio_edge.studies._gold_sleeve_tables`.
* **``bitcoin`` is one venue's daily print**, not the CME CF rate an ETP prices against,
  and its 2015 start means it has never been observed through a US recession-scale equity
  bear market other than 2022 and the three weeks of 2020.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np

from portfolio_edge.data import aqr, fred, french, goyal_welch, worldbank
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.studies.gold_sleeve import pro_rata_marginal_value
from portfolio_edge.studies.stress_dependence import (
    EpisodeReturn,
    convexity,
    engine_summary,
    episode_returns,
    tail_dependence,
)

FloatArray = np.typing.NDArray[np.float64]

#: The named episodes in ``docs/research/evidence-base.md``, as month ranges. These are
#: **chosen by eye from history** and are an analytical choice, not a discovery. They are
#: kept here as a single constant so that every row of every table uses the same ones and
#: a reader can change one definition and re-run.
STRESS_WINDOWS: Final[dict[str, tuple[str, str]]] = {
    "1929-32 crash": ("1929-09", "1932-06"),
    "1937-38": ("1937-03", "1938-03"),
    "1973-74": ("1973-01", "1974-09"),
    "late-1970s inflation": ("1977-01", "1981-12"),
    "1987 crash": ("1987-09", "1987-11"),
    "1998 LTCM": ("1998-07", "1998-09"),
    "2000-02 dot-com": ("2000-04", "2002-09"),
    "2008-09 GFC": ("2007-11", "2009-02"),
    "2020 Q1 covid": ("2020-01", "2020-03"),
    "2022 rate shock": ("2022-01", "2022-09"),
}

#: The gold leg starts here: the first full month after private US bullion ownership
#: became legal on 1974-12-31 (PL 93-373). Before 1971-08-15 the price was a peg.
GOLD_FIRST_MONTH: Final = "1975-01"

#: Bitcoin's first month with a complete pair of month-end prints in ``CBBTCUSD``.
BITCOIN_FIRST_MONTH: Final = "2015-01"

#: Annual cost of holding gold through a retail vehicle, charged as ``c / 12`` monthly.
#: 25 bp is the fee of the cheapest US physically-backed trusts; it is an **assumption**
#: and the only free parameter in gold's total return.
GOLD_CARRY: Final = 0.0025

#: Fraction of months in each tail of the base distribution.
TAIL_QUANTILE: Final = 0.10


def _column(periods: Sequence[str], values: Sequence[float | None]) -> dict[str, float]:
    return {p: v for p, v in zip(periods, values, strict=True) if v is not None}


def _require(cache: RawCache, url: str, label: str) -> CacheEntry:
    entry = cache.entry_for(url)
    if entry is None:
        raise RuntimeError(
            f"{label} is not cached. This module never downloads, so a stress table can "
            f"never be the thing that silently pulls a new vintage."
        )
    return entry


def load_panel() -> tuple[dict[str, dict[str, float]], dict[str, float], dict[str, str]]:
    """Every engine as a month-keyed mapping of excess returns, the cash rate, and digests.

    Returns mappings rather than arrays because the legs have wildly different coverage
    and every table below intersects a different subset of them. Intersecting once, up
    front, would silently shorten every row to bitcoin's 137 months.

    The cash leg is the Ken French ``RF``, returned separately because a sleeve-sizing
    question needs **total** returns and every engine here is an excess.
    """
    cache = RawCache()
    digests: dict[str, str] = {}

    french_dataset = french.get_dataset("french_us_ff3")
    entry = _require(cache, french_dataset.url, "the Ken French three-factor file")
    digests["french_us_ff3"] = entry.sha256
    market = french.parse(cache, entry, dataset=french_dataset).table("monthly")
    equity = _column(market.periods, market.column("Mkt-RF"))
    cash = _column(market.periods, market.column("RF"))

    goyal_dataset = goyal_welch.get_dataset("goyal_welch_predictors")
    gw_entry = _require(cache, goyal_dataset.url, "the Goyal-Welch predictor file")
    digests["goyal_welch_predictors"] = gw_entry.sha256
    parsed = goyal_welch.parse(cache, gw_entry, dataset=goyal_dataset)
    monthly = next(t for t in parsed.tables if t.table_id == "monthly")
    ltr = _column(monthly.periods, monthly.column("ltr"))
    corpr = _column(monthly.periods, monthly.column("corpr"))
    gw_cash = _column(monthly.periods, monthly.column("Rfree"))

    engines: dict[str, dict[str, float]] = {
        "equity": equity,
        "treasury": {p: ltr[p] - gw_cash[p] for p in ltr if p in gw_cash},
        "credit_unhedged": {p: corpr[p] - gw_cash[p] for p in corpr if p in gw_cash},
    }

    for dataset_id, column, name in (
        ("aqr_credit_risk_premium", "CORP_XS", "credit_duration_hedged"),
        (
            "aqr_commodities_long_run",
            "Excess return of equal-weight commodities portfolio",
            "commodity",
        ),
        ("aqr_tsmom_factors", "TSMOM", "trend"),
        ("aqr_bab_equity_factors", "USA", "bab"),
    ):
        dataset = aqr.get_dataset(dataset_id)
        aqr_entry = _require(cache, dataset.url, f"the AQR {dataset_id} workbook")
        digests[dataset_id] = aqr_entry.sha256
        table = aqr.parse(cache, aqr_entry, dataset=dataset).table
        engines[name] = _column(table.periods, table.column(column))

    gold_dataset = worldbank.get_dataset("worldbank_pinksheet_gold_monthly")
    gold_entry = _require(cache, gold_dataset.url, "the World Bank Pink Sheet")
    digests["worldbank_pinksheet_gold"] = gold_entry.sha256
    gold_table = worldbank.parse(cache, gold_entry, dataset=gold_dataset)
    levels = dict(worldbank.monthly_series(gold_table, "Gold"))
    engines["gold"] = _excess_from_levels(levels, cash, first=GOLD_FIRST_MONTH, carry=GOLD_CARRY)

    btc_entry = _require(cache, fred.series_url("CBBTCUSD"), "the FRED bitcoin series")
    digests["fred_cbbtcusd"] = btc_entry.sha256
    btc_table = fred.parse(cache, btc_entry, "CBBTCUSD")
    engines["bitcoin"] = _excess_from_levels(
        _month_end(btc_table.periods, btc_table.values), cash, first=BITCOIN_FIRST_MONTH, carry=0.0
    )
    return engines, cash, digests


def _month_end(
    periods: Sequence[str], values: Sequence[Sequence[float | None]]
) -> dict[str, float]:
    """Last calendar-day print in each month. The market does not close, so this is not
    the last business day, and a month whose last print is stale would be visible as a
    gap in the pairwise differencing below rather than carried forward."""
    last: dict[str, tuple[str, float]] = {}
    for period, row in zip(periods, values, strict=True):
        value = row[0]
        if value is None:
            continue
        month = period[:7]
        previous = last.get(month)
        if previous is None or period > previous[0]:
            last[month] = (period, float(value))
    return {month: price for month, (_, price) in last.items()}


def _excess_from_levels(
    levels: Mapping[str, float],
    cash: Mapping[str, float],
    *,
    first: str,
    carry: float,
) -> dict[str, float]:
    """``price return - carry/12 - cash``. Exact for an asset with no distribution."""
    months = sorted(m for m in levels if m >= first)
    out: dict[str, float] = {}
    for earlier, later in itertools.pairwise(months):
        if _gap(earlier, later) != 1 or later not in cash:
            continue
        out[later] = levels[later] / levels[earlier] - 1.0 - carry / 12.0 - cash[later]
    return out


def _gap(earlier: str, later: str) -> int:
    return (int(later[:4]) * 12 + int(later[5:7])) - (int(earlier[:4]) * 12 + int(earlier[5:7]))


#: The engines a small-weight sizing question is actually asked about. Trend is here
#: because it is the incumbent overlay; bitcoin because the investor asked; gold and
#: duration-hedged credit because they are the two candidates this page admits.
SIZING_ENGINES: Final = ("trend", "gold", "credit_duration_hedged", "commodity", "bitcoin")

#: Weights a retail investor would plausibly consider for a satellite sleeve.
SIZING_WEIGHTS: Final = (0.01, 0.02, 0.05, 0.10)

ENGINE_ORDER: Final = (
    "treasury",
    "credit_unhedged",
    "credit_duration_hedged",
    "commodity",
    "trend",
    "gold",
    "bab",
    "bitcoin",
)


def main() -> None:  # pragma: no cover - reporting entry point
    engines, cash, digests = load_panel()
    equity = engines["equity"]
    print("source digests (prefix):")
    for name, digest in sorted(digests.items()):
        print(f"  {name:32s} {digest[:8]}")

    print("\n== 1. Unconditional, each engine on its own longest window (excess of cash)")
    print(
        "| engine | window | months | geo/yr | vol/yr | Sharpe | max DD vs cash "
        "| rho to equity |"
    )
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for name in ENGINE_ORDER:
        months = sorted(set(engines[name]) & set(equity))
        if len(months) < 24:
            print(f"| {name} | — | {len(months)} | insufficient overlap | | | | |")
            continue
        series = np.array([engines[name][m] for m in months])
        base = np.array([equity[m] for m in months])
        s = engine_summary(series, base=base)
        print(
            f"| {name} | {months[0]}…{months[-1]} | {s.months} | {s.geometric_return:+.2%} | "
            f"{s.volatility:.2%} | {s.sharpe:+.2f} | {s.max_drawdown:.1%} | "
            f"{s.correlation_to_base:+.3f} |"
        )

    print(f"\n== 2. Behaviour in the worst {TAIL_QUANTILE:.0%} of equity months")
    print(
        "'offset at 10%' is 0.10 * (engine mean - equity mean) in the lower tail: what "
        "swapping a tenth of the equity base for this engine adds back in the average "
        "worst-decile month. 'same for cash' is the identical swap into T-bills, on the "
        "identical months, and it is the comparison that decides whether an engine is "
        "buying tail protection or only buying volatility."
    )
    print(
        "| engine | months | n low | equity mean (low) | engine mean (low) | hit rate "
        "| worst | offset at 10% | same for cash | rho low | rho high | rho full |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for name in ENGINE_ORDER:
        months = sorted(set(engines[name]) & set(equity))
        series = np.array([engines[name][m] for m in months])
        base = np.array([equity[m] for m in months])
        try:
            t = tail_dependence(base, series, quantile=TAIL_QUANTILE)
        except ValueError as exc:
            print(f"| {name} | {len(months)} | — | {exc} | | | | | | |")
            continue
        print(
            f"| {name} | {len(months)} | {t.months_low} | {t.base_mean_low:+.2%} | "
            f"{t.mean_low:+.2%} | {t.hit_rate_low:.0%} | {t.worst_low:+.1%} | "
            f"{0.10 * (t.mean_low - t.base_mean_low):+.2%} | "
            f"{-0.10 * t.base_mean_low:+.2%} | "
            f"{t.correlation_low:+.3f} | {t.correlation_high:+.3f} | {t.correlation_full:+.3f} |"
        )

    print("\n== 3. Convexity: engine = a + b*equity + k*min(equity, 0), Newey-West t")
    print("| engine | months | alpha/mo | t | up beta | down beta | kappa | t |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for name in ENGINE_ORDER:
        months = sorted(set(engines[name]) & set(equity))
        series = np.array([engines[name][m] for m in months])
        base = np.array([equity[m] for m in months])
        try:
            c = convexity(base, series)
        except ValueError as exc:
            print(f"| {name} | {len(months)} | {exc} | | | | | |")
            continue
        print(
            f"| {name} | {c.months} | {c.alpha:+.3%} | {c.alpha_t:+.2f} | "
            f"{c.up_beta:+.3f} | {c.down_beta:+.3f} | {c.kappa:+.3f} | {c.kappa_t:+.2f} |"
        )

    print("\n== 4. Named episodes: cumulative excess return, and coverage")
    header = "| episode | " + " | ".join(ENGINE_ORDER) + " |"
    print("| episode | equity | " + " | ".join(ENGINE_ORDER) + " |")
    print("| --- | " + " | ".join(["---:"] * (len(ENGINE_ORDER) + 1)) + " |")
    del header
    equity_months = sorted(equity)
    equity_rows = {
        r.window: r
        for r in episode_returns(
            equity_months, [equity[m] for m in equity_months], windows=STRESS_WINDOWS
        )
    }
    engine_rows: dict[str, dict[str, EpisodeReturn]] = {}
    for name in ENGINE_ORDER:
        months = sorted(engines[name])
        engine_rows[name] = {
            r.window: r
            for r in episode_returns(
                months, [engines[name][m] for m in months], windows=STRESS_WINDOWS
            )
        }
    for window in STRESS_WINDOWS:
        cells = [_cell(equity_rows[window])]
        cells += [_cell(engine_rows[name][window]) for name in ENGINE_ORDER]
        print(f"| {window} | " + " | ".join(cells) + " |")
    print(
        "\n'—' means the panel does not reach the window at all. A '*' marks partial "
        "coverage: the number beside it is not the episode."
    )

    print("\n== 5. Pro-rata sleeve sizing: realised marginal growth and drawdown")
    print(
        "Funding rule: sell the equity base pro rata. This is Experiment 010's rule and "
        "the least favourable one for a diversifier. No trading cost is charged; the "
        "gold leg already carries its 25 bp carry and no other leg carries a fee."
    )
    print("| engine | months | w | marginal growth pp/yr | base max DD | blend max DD |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for name in SIZING_ENGINES:
        months = sorted(set(engines[name]) & set(equity) & set(cash))
        base_total = np.array([equity[m] + cash[m] for m in months])
        sleeve_total = np.array([engines[name][m] + cash[m] for m in months])
        cash_total = np.array([cash[m] for m in months])
        base_dd = engine_summary(base_total).max_drawdown
        for weight in SIZING_WEIGHTS:
            value = pro_rata_marginal_value(
                base_total, sleeve_total, cash_total, weight=weight
            )
            blend = (1.0 - weight) * base_total + weight * sleeve_total
            print(
                f"| {name} | {len(months)} | {weight:.0%} | "
                f"{value.realised_marginal_growth * 100:+.3f} | {base_dd:.1%} | "
                f"{engine_summary(blend).max_drawdown:.1%} |"
            )


def _cell(row: EpisodeReturn) -> str:  # pragma: no cover - reporting entry point
    if not row.covered:
        return "—"
    mark = "*" if row.partial else ""
    return f"{row.cumulative_return:+.1%}{mark}"


if __name__ == "__main__":  # pragma: no cover - reporting entry point
    main()
