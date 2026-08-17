"""Emit ground-truth fixtures for the TypeScript client ports.

Run with ``uv run python -m portfolio_edge.reporting.client_fixtures``. Every value it
prints comes from this workspace's own study modules, so a TypeScript test that matches
them is checked against something calculated independently of the code under test.

Redirect it to ``src/lib/fixtures/research-ground-truth.json`` in the client. Decision
0007 requires that path to exist and requires the client's ports to be tested against it.
"""

from __future__ import annotations

import json

from scipy.stats import norm

from portfolio_edge.studies.outperformance_horizon import (
    detectable_edge_bp,
    horizon_for_confidence,
    probability_of_outperformance,
    terminal_wealth_ratio,
)
from portfolio_edge.studies.tax_structure import (
    DEVELOPED_EX_US,
    EMERGING_MARKETS,
    REGIMES,
    SHELTER_CANDIDATES,
    TOP_BRACKET,
    Account,
    Disposal,
    after_tax_path,
    fill_shelter_bp,
    form_1116_threshold_assets,
    international_split_best_case_bp,
    international_split_versus_single_fund,
    location_breakeven_rate,
    shelter_priority_bp,
)

out: dict[str, object] = {
    "_provenance": {
        "generatedBy": "research/src/portfolio_edge/reporting/client_fixtures.py",
        "regenerate": (
            "cd research && uv run python -m portfolio_edge.reporting.client_fixtures "
            "> ../src/lib/fixtures/research-ground-truth.json"
        ),
        "sourceModules": [
            "portfolio_edge.studies.outperformance_horizon",
            "portfolio_edge.studies.tax_structure",
        ],
        "asOf": "2026-08-12",
        "purpose": (
            "Expected values for the TypeScript ports in src/lib/. Computed by the Python "
            "research workspace, so a passing test checks the port against something "
            "calculated independently of it. Do not hand-edit; regenerate."
        ),
    }
}

# ---------------------------------------------------------------- horizon arithmetic

prob_cases = []
for edge_bp, te_bp in (
    (109.0, 46.0),
    (89.0, 41.0),
    (24.4, 401.0),
    (15.2, 140.0),
    (5.6, 140.0),
    (1.8, 140.0),
    (-7.8, 140.0),
    (68.0, 251.0),
    (37.0, 251.0),
    (90.0, 251.0),
    (49.0, 0.0),
):
    for years in (1.0, 3.0, 5.0, 10.0, 30.0, 50.0):
        prob_cases.append(
            {
                "edgeBp": edge_bp,
                "trackingErrorBp": te_bp,
                "horizonYears": years,
                "expected": probability_of_outperformance(
                    edge_bp=edge_bp, tracking_error_bp=te_bp, horizon_years=years
                ),
            }
        )
out["probabilityOfOutperformance"] = prob_cases

horizon_cases = []
for edge_bp, te_bp in ((109.0, 46.0), (89.0, 41.0), (15.2, 140.0), (68.0, 251.0), (90.0, 251.0)):
    for confidence in (0.75, 0.90, 0.95, 0.99):
        horizon_cases.append(
            {
                "edgeBp": edge_bp,
                "trackingErrorBp": te_bp,
                "confidence": confidence,
                "expected": horizon_for_confidence(
                    edge_bp=edge_bp, tracking_error_bp=te_bp, confidence=confidence
                ),
            }
        )
out["horizonForConfidence"] = horizon_cases

detectable_cases = []
for te_bp in (46.0, 140.0, 251.0, 401.0):
    for years in (10.0, 30.0, 50.0):
        for confidence in (0.90, 0.95):
            detectable_cases.append(
                {
                    "trackingErrorBp": te_bp,
                    "horizonYears": years,
                    "confidence": confidence,
                    "expected": detectable_edge_bp(
                        tracking_error_bp=te_bp, horizon_years=years, confidence=confidence
                    ),
                }
            )
out["detectableEdgeBp"] = detectable_cases

# exp(e T): what an edge is worth as a multiple of the same portfolio without it.
# Needs no market forecast, because the market term cancels out of the ratio.
out["terminalWealthRatio"] = [
    {
        "edgeBp": edge_bp,
        "horizonYears": years,
        "expected": terminal_wealth_ratio(edge_bp=edge_bp, horizon_years=years),
    }
    for edge_bp in (109.0, 86.0, 24.4, 15.2, 90.0, 68.0, -7.8, 0.0)
    for years in (1.0, 10.0, 20.0, 30.0, 40.0)
]

# normal cdf / ppf spot values, so the TS special functions are pinned directly
out["normalCdf"] = [
    {"x": x, "expected": float(norm.cdf(x))}
    for x in (
        -4.0,
        -3.0,
        -2.5758293035489004,
        -1.959963984540054,
        -1.0,
        -0.5,
        0.0,
        0.5,
        1.0,
        1.2815515655446004,
        2.0,
        3.0,
        4.0,
        6.0,
    )
]
out["normalPpf"] = [
    {"p": p, "expected": float(norm.ppf(p))}
    for p in (0.5, 0.75, 0.9, 0.95, 0.975, 0.99, 0.995, 0.999)
]

# ---------------------------------------------------------------- regimes

out["regimes"] = [
    {
        "label": r.label,
        "asOf": r.as_of,
        "ordinaryIncome": r.ordinary_income,
        "longTermCapitalGain": r.long_term_capital_gain,
        "netInvestmentIncome": r.net_investment_income,
        "ordinary": r.ordinary,
        "capitalGain": r.capital_gain,
        "qualifiedDividend": r.qualified_dividend,
        "section1256Blended": r.section_1256_blended,
    }
    for r in REGIMES
]

# ---------------------------------------------------------------- shelter candidates

out["shelterCandidates"] = [
    {
        "label": c.label,
        "dividendYield": c.dividend_yield,
        "qualifiedFraction": c.qualified_fraction,
        "foreignWithholdingRate": c.foreign_withholding_rate,
    }
    for c in SHELTER_CANDIDATES
]

cost_cases = []
for regime in REGIMES:
    for candidate in SHELTER_CANDIDATES:
        for utilisation in (1.0, 0.5, 0.0):
            cost_cases.append(
                {
                    "regime": regime.label,
                    "candidate": candidate.label,
                    "foreignCreditUtilisation": utilisation,
                    "taxableCostBp": candidate.taxable_cost_bp(
                        regime, foreign_credit_utilisation=utilisation
                    ),
                    "shelteredCostBp": candidate.sheltered_cost_bp(),
                }
            )
out["candidateCosts"] = cost_cases

out["shelterPriority"] = [
    {
        "regime": regime.label,
        "foreignCreditUtilisation": 1.0,
        "ranking": [
            {"label": label, "priorityBp": value}
            for label, value in shelter_priority_bp(SHELTER_CANDIDATES, regime=regime)
        ],
    }
    for regime in REGIMES
]

# ------------------------------------------------- the split the recommendation makes

out["internationalSplit"] = [
    {
        "regime": regime.label,
        "usWeight": 0.60,
        "developedWeight": 0.30,
        "emergingWeight": 0.10,
        "capacities": [
            {
                "capacity": capacity,
                "splitSavingBp": result.split_saving_bp,
                "singleFundSavingBp": result.single_fund_saving_bp,
                "gainBp": result.gain_bp,
            }
            for capacity, result in (
                (
                    capacity,
                    international_split_versus_single_fund(regime=regime, capacity=capacity),
                )
                for capacity in (0.0, 0.10, 0.30, 0.40, 0.60, 1.00)
            )
        ],
        "bestCaseCapacity": international_split_best_case_bp(regime=regime)[0],
        "bestCaseGainBp": international_split_best_case_bp(regime=regime)[1],
    }
    for regime in REGIMES
]

out["shelterFill"] = [
    {
        "sleeves": [
            {"label": label, "weight": weight, "priorityBp": priority}
            for label, weight, priority in sleeves
        ],
        "capacity": capacity,
        "savingBp": fill_shelter_bp(sleeves, capacity=capacity),
    }
    for sleeves in (
        (("cheap", 0.5, 10.0), ("dear", 0.5, 30.0)),
        (("a", 0.6, 26.18), ("b", 0.3, 46.1032), ("c", 0.1, 28.3124)),
    )
    for capacity in (0.0, 0.25, 0.5, 1.0, 4.0)
]

# ---------------------------------------------------------------- foreign sleeves

out["foreignSleeves"] = [
    {
        "label": s.label,
        "dividendYield": s.dividend_yield,
        "withholdingRate": s.withholding_rate,
        "forfeitedBp": s.forfeited_bp,
        "breakevenQualifiedRate": location_breakeven_rate(
            international=s, domestic_dividend_yield=0.0110
        ),
        "form1116SingleAssets": form_1116_threshold_assets(foreign_tax_limit=300.0, sleeve=s),
        "form1116JointAssets": form_1116_threshold_assets(foreign_tax_limit=600.0, sleeve=s),
    }
    for s in (DEVELOPED_EX_US, EMERGING_MARKETS)
]

# ---------------------------------------------------------------- deferral hurdle

# The cost of realising a share of standing gain each year, against never realising it,
# and against dying holding it. This is the 84.1 / 78.1 / 162.21 bp family.
deferral_cases = []
for years in (10, 20, 30):
    for realised in (0.0, 0.05, 0.10, 0.25, 0.50, 1.0):
        path = after_tax_path(
            regime=TOP_BRACKET,
            account=Account.TAXABLE,
            pretax_log_growth=0.07,
            years=years,
            dividend_yield=0.0,
            realised_gain_fraction=realised,
            disposal=Disposal.LIQUIDATE,
        )
        deferral_cases.append(
            {
                "years": years,
                "realisedGainFraction": realised,
                "pretaxLogGrowth": 0.07,
                "terminalWealth": path.terminal_wealth,
                "terminalBasis": path.terminal_basis,
                "cumulativeTaxPaid": path.cumulative_tax_paid,
                "annualisedLogGrowth": path.annualised_log_growth,
            }
        )
out["deferralPaths"] = deferral_cases

step_up_cases = []
for years in (10, 20, 30):
    for disposal in (Disposal.LIQUIDATE, Disposal.STEP_UP):
        path = after_tax_path(
            regime=TOP_BRACKET,
            account=Account.TAXABLE,
            pretax_log_growth=0.07,
            years=years,
            disposal=disposal,
        )
        step_up_cases.append(
            {
                "years": years,
                "disposal": disposal.value,
                "terminalWealth": path.terminal_wealth,
                "annualisedLogGrowth": path.annualised_log_growth,
            }
        )
out["disposalPaths"] = step_up_cases

print(json.dumps(out, indent=2))
