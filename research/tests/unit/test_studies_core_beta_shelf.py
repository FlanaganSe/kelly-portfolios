"""The core-beta shelf summary, pinned against the committed manifest.

The manifest is the record of what Form N-CEN filed. These tests pin the figures the
documents quote, and — more importantly — the three rules that decide which filed
figures may be quoted at all.
"""

from __future__ import annotations

import pytest

from portfolio_edge.studies.core_beta_shelf import (
    CORE_BETA_SHELF,
    NetCost,
    ShelfCostSummary,
    comparable_tracking_group,
    load_ncen_manifest,
    portfolio_net_cost_bp,
    summarise,
    workspace_root,
)

SUMMARY: dict[str, ShelfCostSummary] = {
    row.ticker: row for row in summarise(load_ncen_manifest(workspace_root()))
}


def test_every_declared_fund_is_in_the_manifest() -> None:
    assert set(SUMMARY) == {fund.ticker for fund in CORE_BETA_SHELF}
    for row in SUMMARY.values():
        assert row.fiscal_years >= 6, f"{row.ticker} has only {row.fiscal_years} years on file"


def test_the_total_market_fund_out_earns_the_sp500_fund_on_lending_at_every_sponsor() -> None:
    """The one contractual difference between a total-market and an S&P 500 fund.

    Both cost 3 bp at Vanguard and at BlackRock, both distribute no capital gain, and
    both track their own index to within a basis point. What separates them is the
    completion tail's lending demand, and it is the same sign at all three sponsors that
    run both funds. The gap is under a basis point a year, which is the point: the most
    argued retail fund choice is worth less than a third of an expense ratio.
    """
    pairs = (("VTI", "VOO"), ("ITOT", "IVV"), ("SCHB", "SPLG"))
    for total_market, sp500 in pairs:
        broad, narrow = SUMMARY[total_market], SUMMARY[sp500]
        assert broad.lending_bp_median is not None
        assert narrow.lending_bp_median is not None
        assert broad.lending_bp_median > narrow.lending_bp_median, (
            f"{total_market} does not out-earn {sp500} on lending"
        )
        assert broad.lending_bp_median - narrow.lending_bp_median < 2.0

    assert SUMMARY["VTI"].lending_bp_median == pytest.approx(1.84, abs=5e-3)
    assert SUMMARY["VOO"].lending_bp_median == pytest.approx(0.06, abs=5e-3)


def test_lending_income_spans_two_orders_of_magnitude_across_the_shelf() -> None:
    """0.06 bp to 9.9 bp a year, and the spread is regional rather than size-related.

    It is the largest cross-fund cost difference on the shelf that is *certain*, and it
    runs the opposite way from the fee: the dearest emerging fund audited here, EEM at
    72 bp, earns less lending income than IEMG at 9 bp.
    """
    medians = {t: row.lending_bp_median for t, row in SUMMARY.items()}
    assert medians["IEMG"] is not None and medians["EEM"] is not None
    assert medians["IEMG"] > medians["EEM"]
    assert medians["IEMG"] == pytest.approx(9.87, abs=5e-3)
    assert medians["VOO"] is not None
    assert medians["IEMG"] / medians["VOO"] > 100.0

    # BND does not lend at all, which is a different fact from lending for nothing.
    assert SUMMARY["BND"].lends_securities is False
    assert SUMMARY["BND"].lending_bp_median is None
    assert SUMMARY["AGG"].lends_securities is True


def test_only_the_three_sp500_funds_may_be_compared_on_tracking_difference() -> None:
    """And once compared they are indistinguishable, which is the finding.

    Each fund's difference is against its own index. Only VOO, IVV and SPLG share one,
    so only they can be ranked on it, and their derived ETF-class figures sit inside 3 bp
    of each other — inside the 0.01 percentage point the filings are rounded to.
    """
    assert comparable_tracking_group() == ("VOO", "IVV", "SPLG")
    expense_ratios = {"VOO": 0.03, "IVV": 0.03, "SPLG": 0.02}
    derived = {
        ticker: SUMMARY[ticker].derived_etf_tracking_difference(ratio)
        for ticker, ratio in expense_ratios.items()
    }
    for ticker, value in derived.items():
        assert value is not None, ticker
        assert -0.05 < value < 0.0, f"{ticker} derived tracking difference {value}"
    spread = max(v for v in derived.values() if v is not None) - min(
        v for v in derived.values() if v is not None
    )
    assert spread < 0.03


def test_the_consistency_screen_drops_the_years_that_cannot_be_true() -> None:
    """BlackRock filed one number twice, and the screen is what keeps it out of a median.

    IVV loses three of eight fiscal years and AGG three of eight — the years where the
    before- and after-expense differences are filed as equal, or transposed. Vanguard's
    filings lose none. This is a data-quality property of the filer, not of the fund, and
    a page that ranked funds on the filed after-expense number would be ranking filers.
    """
    assert SUMMARY["IVV"].tracking_years_dropped == 3
    assert SUMMARY["AGG"].tracking_years_dropped == 3
    assert SUMMARY["IDEV"].tracking_years_dropped == 2
    for ticker in ("VTI", "VOO", "VEA", "VWO", "VXUS", "VEU", "BND"):
        assert SUMMARY[ticker].tracking_years_dropped == 0, ticker

    # AVEM is not an index fund, so it files no tracking difference at all.
    assert SUMMARY["AVEM"].tracking_before_expenses_median is None
    assert SUMMARY["AVEM"].tracking_years_used == 0
    assert SUMMARY["AVEM"].lending_bp_median is not None


def test_no_vanguard_fund_carries_an_expense_limitation_and_two_schwab_funds_recoup() -> None:
    """Item C.8 is where the forward cost of a waiver at zero becomes visible.

    A waiver line reading `(0.00)%` costs nothing today and can be withdrawn without any
    fee increase being announced, and a *recoupable* one can be clawed back out of future
    years. Vanguard runs none of the seven funds here under an expense limitation at all;
    Schwab's international pair is the only place on this shelf where a waiver has been
    both used and marked recoupable.
    """
    for ticker in ("VTI", "VOO", "VEA", "VWO", "VXUS", "VEU", "BND"):
        assert SUMMARY[ticker].ever_had_expense_limitation is False, ticker
        assert SUMMARY[ticker].ever_waived is False, ticker
        assert SUMMARY[ticker].ever_recoupable is False, ticker

    recoupable = {t for t, row in SUMMARY.items() if row.ever_recoupable}
    assert recoupable == {"SCHF", "SCHE"}


def test_a_manifest_without_a_series_object_raises_rather_than_returning_nothing() -> None:
    with pytest.raises(ValueError, match="no 'series' object"):
        summarise({"filings": {}})


EXPENSE_RATIO_BP = {
    "VTI": 3.0, "ITOT": 3.0, "SCHB": 3.0, "SPTM": 3.0,
    "VOO": 3.0, "IVV": 3.0, "SPLG": 2.0,
    "VEA": 3.0, "IEFA": 7.0, "SCHF": 3.0, "SPDW": 3.0, "IDEV": 4.0,
    "VWO": 6.0, "IEMG": 9.0, "SPEM": 7.0, "SCHE": 6.0, "EEM": 72.0, "AVEM": 33.0,
    "VXUS": 5.0, "IXUS": 7.0, "VEU": 4.0,
    "BND": 3.0, "AGG": 3.0, "SCHZ": 3.0, "SPAB": 3.0,
}  # fmt: skip
"""497K fee tables read 2026-08-17; each date is in docs/research/portfolio-recommendation.md."""


def _net_cost(ticker: str) -> NetCost:
    return NetCost(
        ticker=ticker,
        expense_ratio_bp=EXPENSE_RATIO_BP[ticker],
        lending_bp=SUMMARY[ticker].lending_bp_median,
    )


def _portfolio(us: str, developed: str, emerging: str, bonds: str) -> float:
    return portfolio_net_cost_bp(
        [
            (_net_cost(us), 0.60),
            (_net_cost(developed), 0.14),
            (_net_cost(emerging), 0.06),
            (_net_cost(bonds), 0.20),
        ]
    )


def test_the_fee_ranking_and_the_cost_ranking_are_different_rankings() -> None:
    """IEMG costs 9 bp and VWO 6, and IEMG is the cheaper fund to own.

    This is the doctrine Experiment 009 established on the factor shelf, arriving on the
    shelf that holds the money. Lending income pays IEMG's whole fee and 0.87 bp besides,
    while VWO's pays 4.33 of its 6. Same direction at State Street: SPDW's 3 bp fee is
    more than covered. Nothing about this is a return claim — both terms are measured
    against the fund's own net assets.
    """
    assert _net_cost("IEMG").net_cost_bp < _net_cost("VWO").net_cost_bp
    assert _net_cost("IEMG").expense_ratio_bp > _net_cost("VWO").expense_ratio_bp
    assert _net_cost("IEMG").net_cost_bp == pytest.approx(9.0 - 9.87, abs=5e-3)
    assert _net_cost("SPDW").net_cost_bp < 0.0
    # And the dearest fund audited stays the dearest by a wide margin.
    assert _net_cost("EEM").net_cost_bp > 60.0


def test_the_recommended_four_lose_to_the_cheapest_combination_by_under_a_basis_point() -> None:
    """1.36 bp/yr against 0.76 — the whole fund-selection decision is 0.60 bp/yr.

    Set that against the same page's 84 bp/yr turnover hurdle and its 49 bp fee line and
    the ordering of decisions is settled: which of these funds you hold is roughly two
    orders of magnitude smaller than whether you trade the account they sit in.
    """
    recommended = _portfolio("VTI", "VEA", "VWO", "BND")
    cheapest = _portfolio("ITOT", "SPDW", "IEMG", "SPAB")
    dearest = _portfolio("SPTM", "IEFA", "SCHE", "BND")
    assert recommended == pytest.approx(1.357, abs=5e-4)
    assert cheapest == pytest.approx(0.760, abs=5e-4)
    assert dearest == pytest.approx(3.119, abs=5e-4)
    assert recommended - cheapest == pytest.approx(0.597, abs=1e-3)
    assert dearest - cheapest < 2.5

    # Two substitutions that are not close, and are the only ones that are not.
    assert _portfolio("VTI", "VEA", "EEM", "BND") - recommended > 3.0
    assert _portfolio("VTI", "VEA", "AVEM", "BND") - recommended > 1.0


def test_holdings_that_do_not_sum_to_one_raise() -> None:
    with pytest.raises(ValueError, match=r"must sum to 1\.0"):
        portfolio_net_cost_bp([(_net_cost("VTI"), 0.5)])
