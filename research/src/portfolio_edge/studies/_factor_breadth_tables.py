"""Regenerates the measured tables behind :mod:`portfolio_edge.studies.factor_breadth`.

Kept separate from the study so the study stays pure and testable and only this file
touches the cache. Run it with

    uv run python -m portfolio_edge.studies._factor_breadth_tables

**This is a scoping script, not a frozen experiment.** No specification was frozen
before its numbers were seen, so nothing it prints may promote a sleeve or settle a
decision; it exists to say whether an experiment is worth commissioning, and the
resolution table in ``docs/research/evidence-base.md`` §1 is what decides that.

Nine candidate series are assembled, seven of them families this repository has never
examined.

============================  ==========================================================
``bab_us``                    AQR betting-against-beta, US leg. Vendor reconstruction
``qmj_us``                    AQR quality-minus-junk, US leg. Vendor reconstruction
``st_reversal``               Ken French ``ST_Rev``
``lt_reversal``               Ken French ``LT_Rev``
``net_issuance``              ``Lo 10 - Hi 10`` of Portfolios_Formed_on_NI. Built here
``buyback``                   ``< 0`` minus ``Hi 10`` of the same file. Built here
``accruals``                  ``Lo 10 - Hi 10`` of Portfolios_Formed_on_AC. Built here
``low_beta_decile``           ``Lo 10 - Hi 10`` of Portfolios_Formed_on_BETA. Built here
``vme_asset_allocation``      AQR VME ``VAL^AA`` and ``MOM^AA``, equally weighted
============================  ==========================================================

The incumbents — the US market, the five French factors already tested, and the AQR
trend series that is the programme's only engine with a financed wrapper — are loaded
alongside, because "does this add breadth" is a question about the correlation to what
is already held and cannot be answered from the candidate alone.

**Post-earnings-announcement drift is absent and that is a finding, not an omission.**
Neither the Ken French library nor AQR's public data sets publish an earnings-surprise
sort at any frequency, and constructing one needs a point-in-time analyst-estimate or
Compustat quarterly-announcement panel that this repository does not hold. It is
listed in the output as unobtainable rather than silently dropped.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data import aqr, french, nport
from portfolio_edge.data.cache import RawCache, default_cache_root
from portfolio_edge.inference.multiple_testing import (
    benjamini_hochberg,
    holm_bonferroni,
)
from portfolio_edge.studies.factor_breadth import (
    MONTHS_PER_YEAR,
    PremiumEstimate,
    admission,
    average_pairwise_correlation,
    common_window,
    correlation_matrix,
    decile_spread,
    exact_effective_breadth,
    premium,
)
from portfolio_edge.studies.overlay_growth import effective_breadth

#: Name fragments searched in the SEC N-PORT 2025Q4 census to answer "does a retail
#: vehicle exist", keyed by the candidate engine each would implement. A hit proves a
#: registered fund with that phrase in its series name existed at that census; it does
#: NOT prove the fund implements the academic spread, and the census carries no
#: expense ratio, so no cost in this repository comes from it.
#:
#: The long-short and long-only rows are kept apart because they are different
#: claims. A long-only minimum-volatility fund is not BAB: it holds no short leg, no
#: leverage, and its correlation to equity is near one, so it cannot be the sleeve
#: equation (4) admitted. ``CONTRARIAN`` was tried for long-term reversal and is
#: excluded: it returns eight discretionary stock-picking funds and nothing that
#: implements a -60 to -13 month sort.
VEHICLE_SEARCH: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    ("bab_us / low_beta_decile", "long/short", ("ANTI-BETA", "ANTI BETA")),
    ("bab_us / low_beta_decile", "long-only proxy", ("MIN VOL", "LOW VOLATILITY")),
    ("qmj_us", "long/short", ("QUALITY LONG/SHORT", "QUALITY MINUS")),
    ("qmj_us", "long-only proxy", ("QUALITY FACTOR",)),
    ("net_issuance / buyback", "long-only proxy", ("BUYBACK",)),
    ("st_reversal", "either", ("REVERSAL",)),
    ("lt_reversal", "either", ("LONG-TERM REVERSAL", "LONG TERM REVERSAL")),
    ("accruals", "either", ("ACCRUAL", "EARNINGS QUALITY")),
    ("multi-style", "long/short", ("STYLE PREMIA", "ALTERNATIVE RISK PREMIA")),
    ("trend (the incumbent)", "long/short", ("MANAGED FUTURES", "RETURN STACKED")),
)

#: Post-publication windows open on the first January **after** the year of journal
#: publication, which is exactly the convention
#: ``research/experiments/exp_001_factor_decay.yaml`` froze for HML, UMD, RMW and CMA.
#: The alternative date is the earlier working paper or predecessor result, reported
#: beside the primary and never instead of it, because for four of these families the
#: anomaly was public years before the journal printed it.
PUBLICATION: Final[dict[str, tuple[str, str, str, str]]] = {
    # key: (primary post-publication start, primary citation, alternative, citation)
    "bab_us": (
        "2015-01",
        "Frazzini and Pedersen (2014), Journal of Financial Economics 111, 1-25",
        "2011-01",
        "SSRN working paper, 2010",
    ),
    "qmj_us": (
        "2020-01",
        "Asness, Frazzini and Pedersen (2019), Review of Accounting Studies 24, 34-112",
        "2014-01",
        "SSRN working paper 2312432, 2013",
    ),
    "st_reversal": (
        "1991-01",
        "Jegadeesh (1990), Journal of Finance 45, 881-898",
        "1986-01",
        "Rosenberg, Reid and Lanstein (1985), Journal of Portfolio Management 11, 9-16",
    ),
    "lt_reversal": (
        "1986-01",
        "De Bondt and Thaler (1985), Journal of Finance 40, 793-805",
        "1986-01",
        "no earlier public predecessor identified",
    ),
    "accruals": (
        "1997-01",
        "Sloan (1996), The Accounting Review 71, 289-315",
        "1997-01",
        "no earlier public predecessor identified",
    ),
    "net_issuance": (
        "2009-01",
        "Pontiff and Woodgate (2008), Journal of Finance 63, 921-945",
        "1996-01",
        "Loughran and Ritter (1995) and Ikenberry, Lakonishok and Vermaelen (1995)",
    ),
    "buyback": (
        "2009-01",
        "Pontiff and Woodgate (2008), Journal of Finance 63, 921-945",
        "1996-01",
        "Ikenberry, Lakonishok and Vermaelen (1995), JFE 39, 181-208",
    ),
    "low_beta_decile": (
        "1973-01",
        "Black, Jensen and Scholes (1972), in Studies in the Theory of Capital Markets",
        "2015-01",
        "Frazzini and Pedersen (2014), the levered restatement",
    ),
    "vme_asset_allocation": (
        "2014-01",
        "Asness, Moskowitz and Pedersen (2013), Journal of Finance 68, 929-985",
        "2010-01",
        "SSRN working paper, 2009",
    ),
}

#: The seven families the brief commissioned, which is the multiple-testing family.
#: ``buyback`` and ``vme_asset_allocation`` are reported but excluded from the
#: correction: the first is the same sort as ``net_issuance`` read at a different
#: breakpoint and correcting for it twice would inflate the penalty on a test that is
#: not independent, and the second is not one of the seven.
COMMISSIONED: Final = (
    "bab_us",
    "qmj_us",
    "st_reversal",
    "lt_reversal",
    "net_issuance",
    "accruals",
    "low_beta_decile",
)

#: Every family named in the brief that no free source publishes, with the reason.
UNOBTAINABLE: Final[dict[str, str]] = {
    "post_earnings_announcement_drift": (
        "Neither the Ken French library nor AQR's public data sets publish an "
        "earnings-surprise sort. Constructing one needs a point-in-time panel of "
        "announcement dates and analyst estimates (IBES or Compustat quarterly), "
        "which this repository does not hold and which is not free. Not tested."
    ),
}


@dataclass(frozen=True)
class Series:
    """One aligned monthly series with the provenance a reader must carry with it."""

    key: str
    label: str
    periods: tuple[str, ...]
    values: FloatArray
    source: str
    constructed_here: bool

    def on(self, window: Sequence[str]) -> FloatArray:
        index = {period: position for position, period in enumerate(self.periods)}
        return np.asarray(
            [self.values[index[period]] for period in window], dtype=np.float64
        )

    def since(self, start: str) -> tuple[tuple[str, ...], FloatArray]:
        keep = [i for i, period in enumerate(self.periods) if period >= start]
        return (
            tuple(self.periods[i] for i in keep),
            np.asarray([self.values[i] for i in keep], dtype=np.float64),
        )

    def before(self, start: str) -> tuple[tuple[str, ...], FloatArray]:
        keep = [i for i, period in enumerate(self.periods) if period < start]
        return (
            tuple(self.periods[i] for i in keep),
            np.asarray([self.values[i] for i in keep], dtype=np.float64),
        )


def _clean(
    periods: Sequence[str], column: Sequence[float | None]
) -> tuple[tuple[str, ...], FloatArray]:
    """Drop months where the column is missing, keeping the periods that remain.

    Dropping rather than filling, and the dropped span is printed, because these files
    are ragged at the front by construction: AQR's international BAB legs start decades
    after the US one, and the French sorted files carry the -99.99 sentinel wherever a
    bucket had no firms.
    """
    kept = [
        (period, float(value))
        for period, value in zip(periods, column, strict=True)
        if value is not None and math.isfinite(value)
    ]
    return (
        tuple(period for period, _ in kept),
        np.asarray([value for _, value in kept], dtype=np.float64),
    )


def load_series() -> dict[str, Series]:
    """Assemble every candidate and incumbent series from the cache."""
    cache = RawCache(default_cache_root())
    out: dict[str, Series] = {}

    def add(
        key: str,
        label: str,
        periods: Sequence[str],
        values: FloatArray,
        source: str,
        *,
        constructed_here: bool = False,
    ) -> None:
        out[key] = Series(
            key=key,
            label=label,
            periods=tuple(periods),
            values=np.asarray(values, dtype=np.float64),
            source=source,
            constructed_here=constructed_here,
        )

    # ---- AQR vendor series -------------------------------------------------
    for key, dataset_id, column, label in (
        ("bab_us", "aqr_bab_equity_factors", "USA", "BAB (betting against beta), US"),
        ("qmj_us", "aqr_qmj_factors", "USA", "QMJ (quality minus junk), US"),
        ("trend", "aqr_tsmom_factors", "TSMOM", "Time-series momentum (trend)"),
    ):
        dataset = aqr.get_dataset(dataset_id)
        _, parsed, _ = aqr.load(cache, dataset)
        periods, values = _clean(parsed.table.periods, parsed.table.column(column))
        add(key, label, periods, values, f"AQR {dataset.filename}, sheet {dataset.data_sheet!r}")

    vme = aqr.get_dataset("aqr_vme_factors")
    _, parsed_vme, _ = aqr.load(cache, vme)
    aa_periods = common_window(
        [
            _clean(parsed_vme.table.periods, parsed_vme.table.column("VAL^AA"))[0],
            _clean(parsed_vme.table.periods, parsed_vme.table.column("MOM^AA"))[0],
        ]
    )
    val_map = dict(
        zip(*_clean(parsed_vme.table.periods, parsed_vme.table.column("VAL^AA")), strict=True)
    )
    mom_map = dict(
        zip(*_clean(parsed_vme.table.periods, parsed_vme.table.column("MOM^AA")), strict=True)
    )
    add(
        "vme_asset_allocation",
        "VME value+momentum, non-equity asset classes",
        aa_periods,
        np.asarray([0.5 * (val_map[p] + mom_map[p]) for p in aa_periods]),
        "AQR Value-and-Momentum-Everywhere, VAL^AA and MOM^AA, equally weighted",
        constructed_here=True,
    )

    # ---- Ken French published factors -------------------------------------
    for key, dataset_id, table_id, column, label in (
        ("st_reversal", "french_us_st_reversal", "monthly", "ST_Rev", "Short-term reversal"),
        ("lt_reversal", "french_us_lt_reversal", "monthly", "LT_Rev", "Long-term reversal"),
    ):
        factor_file = french.get_dataset(dataset_id)
        _, parsed_f, _ = french.load(cache, factor_file)
        table = parsed_f.table(table_id)
        periods, values = _clean(table.periods, table.column(column))
        add(
            key, label, periods, values, f"Ken French {factor_file.filename}, column {column}"
        )

    ff5 = french.get_dataset("french_us_ff5")
    _, parsed_ff5, _ = french.load(cache, ff5)
    ff5_monthly = parsed_ff5.table("monthly")
    for key, column, label in (
        ("market", "Mkt-RF", "US market excess return"),
        ("smb", "SMB", "SMB (size)"),
        ("hml", "HML", "HML (value)"),
        ("rmw", "RMW", "RMW (profitability)"),
        ("cma", "CMA", "CMA (investment)"),
    ):
        periods, values = _clean(ff5_monthly.periods, ff5_monthly.column(column))
        add(key, label, periods, values, f"Ken French {ff5.filename}, column {column}")

    mom = french.get_dataset("french_us_momentum")
    _, parsed_mom, _ = french.load(cache, mom)
    mom_monthly = parsed_mom.table("monthly")
    periods, values = _clean(mom_monthly.periods, mom_monthly.column("Mom"))
    add("umd", "UMD (momentum)", periods, values, f"Ken French {mom.filename}, column Mom")

    # ---- Spreads this repository builds from sorted portfolios -------------
    for key, dataset_id, long_leg, short_leg, label in (
        (
            "net_issuance",
            "french_us_portfolios_formed_on_ni",
            "Lo 10",
            "Hi 10",
            "Net share issuance, low minus high decile",
        ),
        (
            "buyback",
            "french_us_portfolios_formed_on_ni",
            "< 0",
            "Hi 10",
            "Net repurchasers minus highest-issuance decile",
        ),
        (
            "accruals",
            "french_us_portfolios_formed_on_ac",
            "Lo 10",
            "Hi 10",
            "Accruals, low minus high decile",
        ),
        (
            "low_beta_decile",
            "french_us_portfolios_formed_on_beta",
            "Lo 10",
            "Hi 10",
            "Prior beta, low minus high decile (UNLEVERED)",
        ),
    ):
        sort_file = french.get_dataset(dataset_id)
        _, parsed_p, _ = french.load(cache, sort_file)
        table = parsed_p.table("value_weighted_returns_monthly")
        low_periods, low_values = _clean(table.periods, table.column(long_leg))
        high_periods, high_values = _clean(table.periods, table.column(short_leg))
        window = common_window([low_periods, high_periods])
        low_map = dict(zip(low_periods, low_values, strict=True))
        high_map = dict(zip(high_periods, high_values, strict=True))
        add(
            key,
            label,
            window,
            decile_spread(
                [low_map[p] for p in window], [high_map[p] for p in window]
            ),
            f"Ken French {sort_file.filename}, {long_leg!r} minus {short_leg!r}, "
            "value-weighted; BUILT HERE, no such factor file is published",
            constructed_here=True,
        )

    return out


def _row(estimate: PremiumEstimate, extra: str = "") -> str:
    flag = "" if estimate.resolved else "  UNRESOLVED"
    return (
        f"{estimate.label:<44}{estimate.months:>6}"
        f"{100 * estimate.annualised_premium:>9.2f}"
        f"{100 * estimate.interval_low:>9.2f}{100 * estimate.interval_high:>9.2f}"
        f"{100 * estimate.mde_80:>8.2f}"
        f"{100 * estimate.annualised_volatility:>8.2f}"
        f"{estimate.sharpe:>7.2f}"
        f"{estimate.t_statistic:>7.2f}"
        f"{estimate.p_value_one_sided:>9.4f}"
        f"{flag}{extra}"
    )


_HEADER: Final = (
    f"{'series':<44}{'n':>6}{'prem':>9}{'lo95':>9}{'hi95':>9}"
    f"{'MDE80':>8}{'vol':>8}{'S':>7}{'t':>7}{'p(1s)':>9}"
)


def main() -> None:  # pragma: no cover - reporting entry point
    series = load_series()

    print("=" * 118)
    print("1. FULL SAMPLE, annualised, percent per year. Gross long-short, no costs.")
    print("=" * 118)
    print(_HEADER)
    full: dict[str, PremiumEstimate] = {}
    for key, item in series.items():
        full[key] = premium(item.values, label=f"{item.label}")
        span = f"   {item.periods[0]}..{item.periods[-1]}"
        print(_row(full[key], span))

    print()
    print("=" * 118)
    print("2. POST-PUBLICATION, primary date = first January after journal publication")
    print("=" * 118)
    print(_HEADER)
    post: dict[str, PremiumEstimate] = {}
    pre: dict[str, PremiumEstimate] = {}
    for key in PUBLICATION:
        if key not in series:
            continue
        start, citation, alternative, alt_citation = PUBLICATION[key]
        item = series[key]
        _, before = item.before(start)
        _, after = item.since(start)
        if before.size >= 24:
            pre[key] = premium(before, label=f"{item.label} pre {start}")
            print(_row(pre[key]))
        post[key] = premium(after, label=f"{item.label} post {start}")
        print(_row(post[key], f"   {citation}"))
        if alternative != start:
            _, alt = item.since(alternative)
            print(
                _row(
                    premium(alt, label=f"  ^ alternative post {alternative}"),
                    f"   {alt_citation}",
                )
            )

    print()
    print("=" * 118)
    print("3. MULTIPLE TESTING across the seven commissioned families")
    print("=" * 118)
    for name, estimates in (("full sample", full), ("post-publication", post)):
        keys = [key for key in COMMISSIONED if key in estimates]
        p_values = [estimates[key].p_value_one_sided for key in keys]
        holm = holm_bonferroni(p_values, alpha=0.05)
        bh = benjamini_hochberg(p_values, alpha=0.05)
        print(f"-- {name}, k = {len(keys)}")
        print(f"{'family':<30}{'p raw':>10}{'Holm':>8}{'BH':>8}")
        for position, key in enumerate(keys):
            print(
                f"{key:<30}{p_values[position]:>10.4f}"
                f"{'pass' if holm.rejected[position] else 'no':>8}"
                f"{'pass' if bh.rejected[position] else 'no':>8}"
            )

    print()
    print("=" * 118)
    print("4. BREADTH: correlation matrix on the common window")
    print("=" * 118)
    order = [
        "market",
        "trend",
        "bab_us",
        "qmj_us",
        "st_reversal",
        "lt_reversal",
        "net_issuance",
        "accruals",
        "low_beta_decile",
        "hml",
        "rmw",
        "cma",
        "umd",
        "smb",
    ]
    order = [key for key in order if key in series]
    window = common_window([series[key].periods for key in order])
    print(f"common window {window[0]}..{window[-1]}, n = {len(window)}")
    print("(vme_asset_allocation is excluded: its legs stop in 2025-01, sixteen months")
    print(" before the workbook's last row, and their volatility falls from 13.1% to")
    print(" 4.2% after 2014. That is a vendor construction change, not a return.)")
    aligned = [series[key].on(window) for key in order]
    matrix = correlation_matrix(aligned)
    print(f"{'':<22}" + "".join(f"{key[:8]:>9}" for key in order))
    for i, key in enumerate(order):
        print(f"{key:<22}" + "".join(f"{matrix[i][j]:>9.2f}" for j in range(len(order))))

    print()
    print("5. EFFECTIVE BREADTH for candidate sets. Equicorrelated k/(1+(k-1)rho_dd)")
    print("   against the exact 1' R^-1 1, which does not average the matrix away.")
    for name, keys in (
        ("trend alone", ["trend"]),
        ("trend + BAB", ["trend", "bab_us"]),
        ("trend + BAB + QMJ", ["trend", "bab_us", "qmj_us"]),
        ("trend + BAB + STR", ["trend", "bab_us", "st_reversal"]),
        ("trend + BAB + STR + accruals", ["trend", "bab_us", "st_reversal", "accruals"]),
        (
            "trend + all seven commissioned",
            ["trend", *[k for k in COMMISSIONED if k in series]],
        ),
        (
            "the seven commissioned alone",
            [k for k in COMMISSIONED if k in series],
        ),
    ):
        keys = [key for key in keys if key in series]
        if len(keys) == 1:
            print(f"  {name:<34}k = 1  rho_dd = -       equi 1.00   exact 1.00")
            continue
        sub_window = common_window([series[key].periods for key in keys])
        sub = correlation_matrix([series[key].on(sub_window) for key in keys])
        rho = average_pairwise_correlation(sub)
        print(
            f"  {name:<34}k = {len(keys)}  rho_dd = {rho:+.3f}  "
            f"equi {effective_breadth(count=len(keys), mutual_correlation=rho):>5.2f}   "
            f"exact {exact_effective_breadth(sub):>5.2f}   (n = {len(sub_window)})"
        )

    print()
    print("=" * 118)
    print("6. ADMISSION  S_d > L rho sigma_p, base = US equity on each candidate's window")
    print("=" * 118)
    print(
        f"{'series':<44}{'rho_eq':>8}{'S_d':>8}{'bar@1.0':>9}{'margin':>9}"
        f"{'bar@1.5':>9}{'margin':>9}  verdict"
    )
    market = series["market"]
    for key in [*COMMISSIONED, "buyback", "vme_asset_allocation", "trend"]:
        if key not in series:
            continue
        item = series[key]
        shared = common_window([item.periods, market.periods])
        candidate = item.on(shared)
        base = market.on(shared)
        rho = float(np.corrcoef(candidate, base)[0][1])
        base_volatility = float(np.std(base, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
        sharpe = premium(candidate, label=key).sharpe
        verdicts = [
            admission(
                label=key,
                sharpe=sharpe,
                correlation=rho,
                base_volatility=base_volatility,
                base_exposure=exposure,
            )
            for exposure in (1.0, 1.5)
        ]
        note = (
            "clears both"
            if all(v.clears for v in verdicts)
            else "clears L=1.0 only"
            if verdicts[0].clears
            else "fails both"
        )
        if not verdicts[0].usable:
            note = f"NOT SCOREABLE (|rho| > 0.5): {note}"
        print(
            f"{item.label:<44}{rho:>8.2f}{sharpe:>8.2f}"
            f"{verdicts[0].threshold:>9.3f}{verdicts[0].margin:>9.3f}"
            f"{verdicts[1].threshold:>9.3f}{verdicts[1].margin:>9.3f}  {note}"
        )

    print()
    print("=" * 118)
    print("7. IS THERE A VEHICLE? SEC N-PORT structured data set, 2025Q4 census.")
    print("   Net assets as filed, in $m. A hit is a registered fund whose SERIES NAME")
    print("   contains the phrase; it is not proof the fund implements the spread, and")
    print("   the census carries no expense ratio, so no fee below comes from it.")
    print("=" * 118)
    cache = RawCache(default_cache_root())
    frame, _ = nport.load_frame(cache, "2025q4")
    names = [
        (str(row.series_name), row.net_assets)
        for row in frame.values()
        if getattr(row, "series_name", None)
    ]
    for engine, kind, phrases in VEHICLE_SEARCH:
        hits = [
            (name, assets)
            for name, assets in names
            if any(phrase in name.upper() for phrase in phrases)
        ]
        hits.sort(key=lambda item: -(item[1] or 0.0))
        if not hits:
            print(
                f"  {engine:<26}{kind:<16}NONE — no registered series names any of "
                f"{list(phrases)}"
            )
            continue
        largest = ", ".join(
            f"{name} (${(assets or 0.0) / 1e6:,.0f}m)" for name, assets in hits[:2]
        )
        print(f"  {engine:<26}{kind:<16}{len(hits):>3} series; largest: {largest}")

    print()
    print("8. NOT OBTAINABLE FROM ANY FREE SOURCE HELD HERE")
    for key, reason in UNOBTAINABLE.items():
        print(f"  {key}: {reason}")

    print()
    print("9. PROVENANCE")
    for key in order:
        item = series[key]
        built = "  [BUILT HERE]" if item.constructed_here else ""
        print(f"  {key:<24}{item.periods[0]}..{item.periods[-1]}  {item.source}{built}")


if __name__ == "__main__":  # pragma: no cover
    main()
