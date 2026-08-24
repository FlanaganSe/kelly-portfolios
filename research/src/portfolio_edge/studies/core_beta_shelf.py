"""The core beta shelf, audited on total cost of ownership rather than on fee.

Why this exists
---------------
[Experiment 009](../../../docs/research/factor-products.md) established the doctrine on
the funds holding *little* of the money: **a fee comparison is not a cost comparison**.
22 of 44 US factor products lost more than 0.50 pp/yr to a cheap replication against a
fee premium of at most 0.32. The four funds that hold essentially the whole recommended
portfolio had never been put through the same test — they were selected on expense
ratio and nothing else. This module is that test, on the quantities that are
*contractual* rather than statistical.

Everything here reads the committed manifest
``data-manifests/core_beta_shelf/ncen_costs.json``, which
:func:`build_ncen_manifest` writes from Form N-CEN. Rebuilding needs the network;
summarising does not, so the tables a document quotes are reproducible offline.

The three screens that decide what may be summarised
----------------------------------------------------
1. **A tracking difference is against the fund's own index, and the indices differ.**
   Ranking funds across categories on it would add lines measured against different
   benchmarks. :func:`comparable_tracking_group` names the only group on this shelf
   whose members share an index.
2. **A filed figure that cannot be true is dropped, and the drop is counted.** See
   :func:`portfolio_edge.data.ncen.tracking_difference_is_internally_consistent`.
3. **A multi-class series does not report its ETF class.** Only the *before*-expense
   difference is comparable across sponsors, so the ETF-class figure is derived as
   ``before - expense ratio`` and labelled derived wherever it appears.

Securities lending needs none of those screens: net income over net assets is the same
quantity for every filer, and it is the one line on this shelf that is small, certain,
free, and varies by more than an order of magnitude across funds holding the same
market.
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.ncen import (
    NcenSeriesRecord,
    fetch_ncen,
    ncen_filing_index,
    tracking_difference_is_internally_consistent,
)
from portfolio_edge.data.nport import throttle

__all__ = [
    "CORE_BETA_SHELF",
    "MANIFEST_RELATIVE_PATH",
    "NetCost",
    "ShelfCostSummary",
    "ShelfFund",
    "build_ncen_manifest",
    "comparable_tracking_group",
    "load_ncen_manifest",
    "manifest_path",
    "portfolio_net_cost_bp",
    "summarise",
    "workspace_root",
]

MANIFEST_RELATIVE_PATH: Final = Path("data-manifests") / "core_beta_shelf" / "ncen_costs.json"


@dataclass(frozen=True)
class ShelfFund:
    """One candidate, its category, and the registrant whose N-CEN carries it."""

    ticker: str
    category: str
    registrant_cik: int


CORE_BETA_SHELF: tuple[ShelfFund, ...] = (
    ShelfFund("VTI", "US total market", 36405),
    ShelfFund("ITOT", "US total market", 1100663),
    ShelfFund("SCHB", "US total market", 1454889),
    ShelfFund("SPTM", "US total market", 1064642),
    ShelfFund("VOO", "S&P 500", 36405),
    ShelfFund("IVV", "S&P 500", 1100663),
    ShelfFund("SPLG", "S&P 500", 1064642),
    ShelfFund("VEA", "Developed ex-US", 923202),
    ShelfFund("IEFA", "Developed ex-US", 1100663),
    ShelfFund("SCHF", "Developed ex-US", 1454889),
    ShelfFund("SPDW", "Developed ex-US", 1168164),
    ShelfFund("IDEV", "Developed ex-US", 1100663),
    ShelfFund("VWO", "Emerging", 857489),
    ShelfFund("IEMG", "Emerging", 930667),
    ShelfFund("SPEM", "Emerging", 1168164),
    ShelfFund("SCHE", "Emerging", 1454889),
    ShelfFund("EEM", "Emerging", 930667),
    ShelfFund("AVEM", "Emerging", 1710607),
    ShelfFund("VXUS", "Total international", 736054),
    ShelfFund("IXUS", "Total international", 1100663),
    ShelfFund("VEU", "Total international", 857489),
    ShelfFund("BND", "Aggregate bonds", 794105),
    ShelfFund("AGG", "Aggregate bonds", 1100663),
    ShelfFund("SCHZ", "Aggregate bonds", 1454889),
    ShelfFund("SPAB", "Aggregate bonds", 1064642),
)
"""The shelf as audited. **SPY is deliberately absent**: the SPDR S&P 500 ETF Trust is a
unit investment trust, files no management-investment series block, and so appears in no
N-CEN item this module reads. Its costs are in its own prospectus and nowhere here."""


def comparable_tracking_group() -> tuple[str, ...]:
    """The only funds on this shelf that track the **same** index as each other.

    VOO, IVV and SPLG all track the S&P 500, so their tracking differences are three
    measurements of one quantity and may be compared. Every other category on this shelf
    spans two to five distinct indices — CRSP, two S&P variants, FTSE, MSCI — and a
    difference between two of those is a statement about the index providers, not about
    the funds.
    """
    return ("VOO", "IVV", "SPLG")


@dataclass(frozen=True)
class ShelfCostSummary:
    """What the filings support about one fund, over every fiscal year on file."""

    ticker: str
    category: str
    fiscal_years: int
    latest_fiscal_year_end: str
    #: Securities lending net income over average net assets, basis points a year.
    lending_bp_latest: float | None
    lending_bp_median: float | None
    lending_bp_min: float | None
    lending_bp_max: float | None
    lends_securities: bool
    #: Item C.3.b.ii before fund fees, over the years that pass the consistency screen.
    tracking_before_expenses_median: float | None
    tracking_years_used: int
    tracking_years_dropped: int
    #: Item C.8, over every year on file.
    ever_had_expense_limitation: bool
    ever_waived: bool
    ever_recoupable: bool

    def derived_etf_tracking_difference(self, expense_ratio_percent: float) -> float | None:
        """``median before-expense difference - expense ratio``, in percent per year.

        Derived rather than filed, and labelled so wherever it is quoted. The filed
        after-expense figure is not usable across sponsors because Form N-CEN does not
        say which share class a multi-class fund answered for.
        """
        if self.tracking_before_expenses_median is None:
            return None
        return self.tracking_before_expenses_median - expense_ratio_percent


@dataclass(frozen=True)
class NetCost:
    """A fund's measured cost of ownership, in basis points a year.

    Two terms, and they are not the same kind of fact. The **expense ratio** is
    contractual: a filed number the fund is bound to. The **lending income** is
    measured over the fiscal years on file and is not promised — but its sign is
    certain, its rank across funds is stable over eight years, and it is the term the
    fee comparison leaves out. Both are reported; neither is presented as the other.
    """

    ticker: str
    expense_ratio_bp: float
    lending_bp: float | None

    @property
    def net_cost_bp(self) -> float:
        """``expense ratio - securities lending income``. Can be negative."""
        return self.expense_ratio_bp - (self.lending_bp or 0.0)


def portfolio_net_cost_bp(holdings: Sequence[tuple[NetCost, float]]) -> float:
    """Weight-average net cost of a named portfolio, in basis points a year.

    ``holdings`` are ``(fund, weight)`` with weights summing to one. This is the only
    quantity in the core-beta audit that may be summed across categories, because a fee
    and a lending yield are measured against the fund's own net assets rather than
    against an index — so adding them is not the benchmark switch that
    ``outperformance_horizon.aggregate()`` refuses.
    """
    total = sum(weight for _, weight in holdings)
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"holdings must sum to 1.0, got {total}")
    return sum(fund.net_cost_bp * weight for fund, weight in holdings)


def workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_RELATIVE_PATH


def load_ncen_manifest(root: Path) -> Mapping[str, object]:
    """Read the committed manifest. Offline, and the only input :func:`summarise` needs."""
    payload = manifest_path(root).read_text()
    loaded = json.loads(payload)
    if not isinstance(loaded, dict):
        raise ValueError("the core-beta manifest must be a JSON object")
    return loaded


def summarise(
    manifest: Mapping[str, object], *, shelf: Sequence[ShelfFund] = CORE_BETA_SHELF
) -> tuple[ShelfCostSummary, ...]:
    """One row per fund, in the shelf's declared order.

    A fund absent from the manifest is omitted rather than defaulted, because a missing
    filing and a filed zero are different facts and this repository has already been
    caught treating one as the other.

    ``shelf`` is an argument so that a second shelf built by the same machinery --
    :mod:`portfolio_edge.studies._fixed_income_tables` builds one for bond and TIPS
    funds -- summarises through this function rather than through a copy of it.
    """
    series = manifest.get("series")
    if not isinstance(series, dict):
        raise ValueError("the core-beta manifest carries no 'series' object")
    rows: list[ShelfCostSummary] = []
    for fund in shelf:
        entry = series.get(fund.ticker)
        if not isinstance(entry, dict):
            continue
        years = entry.get("years")
        if not isinstance(years, list) or not years:
            continue
        rows.append(_summarise_one(fund, years))
    return tuple(rows)


def _summarise_one(fund: ShelfFund, years: Sequence[Mapping[str, object]]) -> ShelfCostSummary:
    ordered = sorted(years, key=lambda year: str(year.get("fiscal_year_end", "")))
    # Only years in which the fund actually lent. BND answers Item C.6.a "No" in every
    # year on file and once wrote a zero into C.6.g anyway; averaging that in would read
    # as "lent and earned nothing", which is a different fact from "does not lend".
    lending = [
        value
        for year in ordered
        if str(year.get("isFundSecuritiesLending", "")).upper() == "Y"
        and isinstance(value := year.get("securities_lending_bp_of_net_assets"), (int, float))
    ]
    before: list[float] = []
    dropped = 0
    for year in ordered:
        pair = (
            _float(year.get("indexFundReturnDiffBeforeExpense")),
            _float(year.get("indexFundReturnDiffAfterExpense")),
        )
        if pair[0] is None and pair[1] is None:
            continue
        if pair[0] is not None and pair[1] is not None and pair[0] - pair[1] > 0.0:
            before.append(pair[0])
        else:
            dropped += 1
    latest = ordered[-1]
    return ShelfCostSummary(
        ticker=fund.ticker,
        category=fund.category,
        fiscal_years=len(ordered),
        latest_fiscal_year_end=str(latest.get("fiscal_year_end", "")),
        lending_bp_latest=(
            _float(latest.get("securities_lending_bp_of_net_assets")) if lending else None
        ),
        lending_bp_median=statistics.median(lending) if lending else None,
        lending_bp_min=min(lending) if lending else None,
        lending_bp_max=max(lending) if lending else None,
        lends_securities=str(latest.get("isFundSecuritiesLending", "")).upper() == "Y",
        tracking_before_expenses_median=statistics.median(before) if before else None,
        tracking_years_used=len(before),
        tracking_years_dropped=dropped,
        ever_had_expense_limitation=_any_flag(ordered, "isExpenseLimitationInPlace"),
        ever_waived=_any_flag(ordered, "isExpenseReducedOrWaived"),
        ever_recoupable=_any_flag(ordered, "isFeesWaivedRecoupable")
        or _any_flag(ordered, "isExpenseWaivedRecoupable"),
    )


def _any_flag(years: Sequence[Mapping[str, object]], field: str) -> bool:
    return any(str(year.get(field, "")).upper() == "Y" for year in years)


def _float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def build_ncen_manifest(
    cache: RawCache,
    *,
    shelf: Sequence[ShelfFund] = CORE_BETA_SHELF,
    purpose: str | None = None,
    regenerate: str | None = None,
) -> dict[str, object]:
    """Rebuild the manifest from EDGAR. Needs the network; nothing else here does.

    Every N-CEN a registrant has ever filed is read, not only the latest, because a
    registrant files one per fiscal-year group and the shelf spans eleven fiscal-year
    ends. The raw XML is hashed into the cache before it is parsed, so the manifest's
    ``sha256_raw`` identifies the exact bytes each row came from.

    ``shelf``, ``purpose`` and ``regenerate`` are arguments so the fixed-income shelf
    is built by this function rather than by a fork of it; the screens, units and notes
    are the same because the form is the same.
    """
    wanted = {fund.ticker: fund for fund in shelf}
    filings: dict[str, dict[str, object]] = {}
    per_ticker: dict[str, dict[str, NcenSeriesRecord]] = {}
    for cik in sorted({fund.registrant_cik for fund in shelf}):
        for ref in ncen_filing_index(cache, cik):
            throttle()
            records, entry = fetch_ncen(cache, ref)
            hit = False
            for record in records:
                for ticker in record.tickers:
                    if ticker in wanted:
                        per_ticker.setdefault(ticker, {})[record.fiscal_year_end] = record
                        hit = True
            if hit:
                filings[ref.accession] = {
                    "cik": cik,
                    "url": ref.document_url,
                    "filing_date": ref.filing_date,
                    "sha256_raw": entry.sha256,
                    "bytes": entry.size_bytes,
                    "retrieved_utc": entry.retrieved_utc,
                }
    return {
        "schema_version": "1",
        "purpose": purpose
        or (
            "Provenance for the core-beta shelf cost audit in "
            "docs/research/portfolio-recommendation.md and "
            "docs/research/structural-and-tax-edges.md. Form N-CEN Items C.3.b (index "
            "tracking difference), C.6 (securities lending) and C.8 (expense limitations "
            "and recoupment), per series per fiscal year, as filed."
        ),
        "regenerate": regenerate
        or (
            "cd research && uv run python -m portfolio_edge.studies.core_beta_shelf --build"
        ),
        "units": _UNITS,
        "notes": _NOTES,
        "series": {
            ticker: {
                "fund_name": next(iter(by_year.values())).fund_name,
                "series_id": next(iter(by_year.values())).series_id,
                "category": wanted[ticker].category,
                "years": [_year_row(record) for _, record in sorted(by_year.items())],
            }
            for ticker, by_year in sorted(per_ticker.items())
        },
        "filings": dict(sorted(filings.items())),
    }


_UNITS: Final = {
    "indexFundReturnDiffBeforeExpense": (
        "percent per year, fund total return less index return, before fund fees and expenses"
    ),
    "indexFundReturnDiffAfterExpense": (
        "percent per year, the same difference after fund fees and expenses (net asset value)"
    ),
    "mnthlyAvgNetAssets": "USD, monthly average net assets of the series",
    "netIncomeSecuritiesLending": "USD, net lending income accruing to the fund",
    "avgPortfolioSecuritiesValue": "USD, monthly average value of portfolio securities on loan",
    "securities_lending_bp_of_net_assets": (
        "derived: netIncomeSecuritiesLending / mnthlyAvgNetAssets, in basis points"
    ),
}

_NOTES: Final = (
    "Item C.3.b.ii asks for 'the annualized difference between the Fund's total return "
    "during the reporting period and the index's return'. It is FILER-REPORTED AND "
    "UNAUDITED and the filings show it.",
    "The item does not say WHICH SHARE CLASS a multi-class fund answers for. For every "
    "Vanguard series here the gap between the before- and after-expense figures is 9.5 to "
    "35.3 bp against an ETF-class expense ratio of 3 to 6, so the filed after-expense "
    "figure is not the ETF class's tracking difference. For a single-class ETF the same "
    "gap recovers the expense ratio to the filed rounding.",
    "BlackRock filed the before- and after-expense figures IDENTICALLY for every iShares "
    "fund here in its fiscal-2025 and fiscal-2026 N-CENs, which cannot be true of a fund "
    "that charges a fee. Those rows are kept as filed and excluded by the consistency "
    "screen.",
    "The consistency screen does not catch everything. Three values are inconsistent with "
    "the same fund's other years by an order of magnitude and still pass it, because the "
    "ordering is right: IDEV FY2023 (+9.58), SPTM FY2025 (-0.73) and SPAB FY2025 (-2.84). "
    "That is why a MEDIAN over fiscal years is reported and never a mean.",
    "EVERY FUND'S TRACKING DIFFERENCE IS AGAINST ITS OWN INDEX AND THE INDICES DIFFER. "
    "Only VOO, IVV and SPLG share one.",
    "Net lending income is Item C.6.g, after the agent's split, over Item C.2's monthly "
    "average net assets from the same filing. Both are series-level, so a multi-class "
    "fund's figure covers every class.",
    "Item C.8 records whether a waiver is RECOUPABLE. It records neither the waiver's "
    "expiry date nor its size; those are in the 497K fee table.",
    "AVEM files no indexFundInfo block because it is not an index fund.",
    "SPY is absent: the SPDR S&P 500 ETF Trust is a unit investment trust and files no "
    "management-investment series block.",
)


def _year_row(record: NcenSeriesRecord) -> dict[str, object]:
    return {
        "fiscal_year_end": record.fiscal_year_end,
        "accession": record.accession,
        "mnthlyAvgNetAssets": record.monthly_average_net_assets,
        "indexFundReturnDiffBeforeExpense": record.tracking_difference_before_expenses,
        "indexFundReturnDiffAfterExpense": record.tracking_difference_after_expenses,
        "isFundSecuritiesLending": "Y" if record.lends_securities else "N",
        "avgPortfolioSecuritiesValue": record.average_securities_on_loan,
        "netIncomeSecuritiesLending": record.net_securities_lending_income,
        "isExpenseLimitationInPlace": "Y" if record.expense_limitation_in_place else "N",
        "isExpenseReducedOrWaived": "Y" if record.expenses_waived else "N",
        "isFeesWaivedRecoupable": "Y" if record.waived_fees_recoupable else "N",
        "isExpenseWaivedRecoupable": "Y" if record.waived_expenses_recouped else "N",
        "securities_lending_bp_of_net_assets": record.securities_lending_bp,
        "tracking_difference_internally_consistent": (
            tracking_difference_is_internally_consistent(record)
        ),
    }


def _main() -> None:
    """``--build`` rewrites the manifest from EDGAR; the default prints the summary."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="refetch every N-CEN and rewrite")
    args = parser.parse_args()

    root = workspace_root()
    if args.build:
        manifest = build_ncen_manifest(RawCache())
        manifest_path(root).parent.mkdir(parents=True, exist_ok=True)
        manifest_path(root).write_text(json.dumps(manifest, indent=1) + "\n")
    for row in summarise(load_ncen_manifest(root)):
        print(
            f"{row.ticker:5} {row.category:20} FY{row.latest_fiscal_year_end} "
            f"lend {_fmt(row.lending_bp_latest)} bp (median {_fmt(row.lending_bp_median)}) "
            f"| TD before fees median {_fmt(row.tracking_before_expenses_median, 3)} "
            f"({row.tracking_years_used} used, {row.tracking_years_dropped} dropped) "
            f"| waiver {row.ever_had_expense_limitation} recoupable {row.ever_recoupable}"
        )


def _fmt(value: float | None, places: int = 2) -> str:
    return "  n/a" if value is None else f"{value:.{places}f}"


if __name__ == "__main__":
    _main()
