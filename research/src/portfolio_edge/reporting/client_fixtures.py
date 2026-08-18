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
from portfolio_edge.studies.value_tilt import (
    TiltInputs,
    certainty_equivalent_contribution,
    marginal_growth_contribution,
    portfolio_tracking_error,
    sleeve_edge,
    substitution_variance_change,
    terminal_wealth_multiple,
    tilt_verdict,
    turnover_cost_percent,
    variance_drag,
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
            "portfolio_edge.studies.value_tilt",
        ],
        "asOf": "2026-08-17",
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

# ---------------------------------------------------------------- the value tilt

# `weight x (h_fund - h_incumbent) x premium - cost`, with no capture term anywhere.
# Two of the cases below are the tilts `docs/research/portfolio-recommendation.md` §5
# publishes, so the client's port reproduces printed figures and not only itself; the
# rest are corners the published pair never reaches — a zero and a unit weight, a zero
# and a negative delivered loading, a zero premium, perfect and negative correlation,
# and a fund quieter than the incumbent it replaces.
#
# The two published rows carry the loadings and second moments
# `studies/_value_tilt_tables` and `studies/_exus_value_tilt_tables` measure from the
# cache. They are transcribed rather than recomputed because this module reads no
# market data, in the tradition of `value_tilt` itself.

TILT_GAMMAS: tuple[float, ...] = (1.0, 2.0, 3.0, 5.0)

tilt_cases: list[tuple[str, TiltInputs]] = [
    # AVLV at 20% of portfolio out of VTI, pooled post-publication HML premium,
    # k = 1.7. §5 "Which value product, if any" prints +24.4 bp, 135 bp, +24.9 bp,
    # +26.0 bp and 1.078.
    (
        "AVLV 20% out of VTI, pooled premium, k = 1.7",
        TiltInputs(
            weight=0.20,
            fund_hml_loading=0.322028508346998,
            benchmark_hml_loading=0.0246971965235378,
            hml_premium=4.740625,
            fund_fee=0.15,
            benchmark_fee=0.03,
            fund_turnover_percent=7.0,
            benchmark_turnover_percent=3.0,
            turnover_coefficient=1.7,
            fund_volatility=17.181423095590738,
            benchmark_volatility=16.23770348459306,
            correlation=0.9194103780959881,
        ),
    ),
    # DFIV at 8% out of VEA on the common 2022-04..2025-12 window, developed-ex-US
    # post-publication premium, k = 1.7. §5 "The same question on the ex-US shelf"
    # prints +27.1 bp, 47.6 bp, +29.5 bp and +34.2 bp. DFIV is also the case in which
    # the fund is *less* volatile than the incumbent it replaces, so the substitution
    # variance change is negative and the drag is a credit.
    (
        "DFIV 8% out of VEA, common window, ex-US post-publication premium, k = 1.7",
        TiltInputs(
            weight=0.08,
            fund_hml_loading=0.6976037808578383,
            benchmark_hml_loading=-0.025186177492858675,
            hml_premium=5.071250000000001,
            fund_fee=0.27,
            benchmark_fee=0.03,
            fund_turnover_percent=6.0,
            benchmark_turnover_percent=4.0,
            turnover_coefficient=1.7,
            fund_volatility=15.781965234617221,
            benchmark_volatility=16.598108003208974,
            correlation=0.9337858710123662,
        ),
    ),
]

# The same AVLV swap across the weight range, including both endpoints. At w = 0
# nothing is bought and every portfolio-level figure must be exactly zero; at w = 1 the
# incumbent is gone and the sleeve edge is the portfolio edge.
for tilt_weight in (0.0, 0.05, 0.10, 0.30, 0.50, 1.0):
    tilt_cases.append(
        (
            f"AVLV at weight {tilt_weight:g}",
            TiltInputs(
                weight=tilt_weight,
                fund_hml_loading=0.322028508346998,
                benchmark_hml_loading=0.0246971965235378,
                hml_premium=4.740625,
                fund_fee=0.15,
                benchmark_fee=0.03,
                fund_turnover_percent=7.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.7,
                fund_volatility=17.181423095590738,
                benchmark_volatility=16.23770348459306,
                correlation=0.9194103780959881,
            ),
        )
    )

tilt_cases.extend(
    [
        # A swap that buys no exposure at all: the edge is exactly minus the
        # incremental cost, whatever the premium is.
        (
            "zero delivered loading",
            TiltInputs(
                weight=0.20,
                fund_hml_loading=0.35,
                benchmark_hml_loading=0.35,
                hml_premium=4.740625,
                fund_fee=0.25,
                benchmark_fee=0.03,
                fund_turnover_percent=6.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.7,
                fund_volatility=20.0,
                benchmark_volatility=16.0,
                correlation=0.85,
            ),
        ),
        # An incumbent with more value exposure than the fund bought to replace it.
        (
            "negative delivered loading",
            TiltInputs(
                weight=0.25,
                fund_hml_loading=0.12,
                benchmark_hml_loading=0.41,
                hml_premium=4.740625,
                fund_fee=0.20,
                benchmark_fee=0.05,
                fund_turnover_percent=25.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.7,
                fund_volatility=22.5,
                benchmark_volatility=17.75,
                correlation=0.89,
            ),
        ),
        # A premium of zero is the honest reading of an era Experiment 007 marks
        # UNSTABLE: the exposure is bought and only the cost is paid.
        (
            "zero premium",
            TiltInputs(
                weight=0.20,
                fund_hml_loading=0.5368,
                benchmark_hml_loading=0.0246971965235378,
                hml_premium=0.0,
                fund_fee=0.25,
                benchmark_fee=0.03,
                fund_turnover_percent=6.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.7,
                fund_volatility=26.9562,
                benchmark_volatility=17.7483,
                correlation=0.8346,
            ),
        ),
        # Perfect correlation: the sleeve tracking error collapses to the difference of
        # the two volatilities, and the variance change is exact and linear in weight.
        (
            "correlation 1.0, fund more volatile",
            TiltInputs(
                weight=0.20,
                fund_hml_loading=0.5368,
                benchmark_hml_loading=0.0246971965235378,
                hml_premium=4.740625,
                fund_fee=0.25,
                benchmark_fee=0.03,
                fund_turnover_percent=6.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.7,
                fund_volatility=26.9562,
                benchmark_volatility=17.7483,
                correlation=1.0,
            ),
        ),
        # The degenerate case the sqrt guard exists for: equal volatilities at rho = 1
        # leave no tracking error whatever, and floating point can push the variance
        # fractionally below zero.
        (
            "correlation 1.0, volatilities equal",
            TiltInputs(
                weight=0.40,
                fund_hml_loading=0.44,
                benchmark_hml_loading=0.02,
                hml_premium=3.45,
                fund_fee=0.30,
                benchmark_fee=0.03,
                fund_turnover_percent=9.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.0,
                fund_volatility=17.7483,
                benchmark_volatility=17.7483,
                correlation=1.0,
            ),
        ),
        (
            "correlation 0.0",
            TiltInputs(
                weight=0.15,
                fund_hml_loading=0.5368,
                benchmark_hml_loading=0.0246971965235378,
                hml_premium=4.740625,
                fund_fee=0.25,
                benchmark_fee=0.03,
                fund_turnover_percent=6.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.7,
                fund_volatility=26.9562,
                benchmark_volatility=17.7483,
                correlation=0.0,
            ),
        ),
        (
            "correlation -1.0",
            TiltInputs(
                weight=0.35,
                fund_hml_loading=0.5368,
                benchmark_hml_loading=0.0246971965235378,
                hml_premium=4.740625,
                fund_fee=0.25,
                benchmark_fee=0.03,
                fund_turnover_percent=6.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.7,
                fund_volatility=26.9562,
                benchmark_volatility=17.7483,
                correlation=-1.0,
            ),
        ),
        # A quieter fund bought for less than the incumbent charges: the incremental
        # cost is negative and so is the variance change, so both corrections are
        # credits and the growth contribution exceeds the arithmetic edge.
        (
            "fund quieter and cheaper than the incumbent",
            TiltInputs(
                weight=0.20,
                fund_hml_loading=0.30,
                benchmark_hml_loading=0.02,
                hml_premium=4.740625,
                fund_fee=0.02,
                benchmark_fee=0.05,
                fund_turnover_percent=3.0,
                benchmark_turnover_percent=25.0,
                turnover_coefficient=1.7,
                fund_volatility=13.75,
                benchmark_volatility=16.0,
                correlation=0.94,
            ),
        ),
        # k at the patient floor rather than the pessimistic column, and a fund whose
        # sort is an index reconstitution, so trading cost rather than fee dominates.
        (
            "RPV 20% out of VTI, k = 1.0",
            TiltInputs(
                weight=0.20,
                fund_hml_loading=0.7098,
                benchmark_hml_loading=0.0246971965235378,
                hml_premium=4.740625,
                fund_fee=0.35,
                benchmark_fee=0.03,
                fund_turnover_percent=42.0,
                benchmark_turnover_percent=3.0,
                turnover_coefficient=1.0,
                fund_volatility=23.8688,
                benchmark_volatility=17.7483,
                correlation=0.8214,
            ),
        ),
        # No trading cost at all on either side, so the incremental cost is the fee
        # difference alone.
        (
            "zero turnover on both legs",
            TiltInputs(
                weight=0.10,
                fund_hml_loading=0.6372,
                benchmark_hml_loading=0.0246971965235378,
                hml_premium=1.566,
                fund_fee=0.21,
                benchmark_fee=0.03,
                fund_turnover_percent=0.0,
                benchmark_turnover_percent=0.0,
                turnover_coefficient=1.7,
                fund_volatility=13.7539,
                benchmark_volatility=12.56,
                correlation=0.8114,
            ),
        ),
    ]
)

out["valueTilt"] = {
    "gammas": list(TILT_GAMMAS),
    "cases": [
        {
            "label": label,
            "inputs": {
                "weight": tilt.weight,
                "fundHmlLoading": tilt.fund_hml_loading,
                "benchmarkHmlLoading": tilt.benchmark_hml_loading,
                "hmlPremium": tilt.hml_premium,
                "fundFee": tilt.fund_fee,
                "benchmarkFee": tilt.benchmark_fee,
                "fundTurnoverPercent": tilt.fund_turnover_percent,
                "benchmarkTurnoverPercent": tilt.benchmark_turnover_percent,
                "turnoverCoefficient": tilt.turnover_coefficient,
                "fundVolatility": tilt.fund_volatility,
                "benchmarkVolatility": tilt.benchmark_volatility,
                "correlation": tilt.correlation,
            },
            "deliveredLoading": tilt.delivered_loading,
            "incrementalCost": tilt.incremental_cost,
            "sleeveTrackingError": tilt.sleeve_tracking_error,
            "sleeveEdge": sleeve_edge(tilt),
            "portfolioTrackingError": portfolio_tracking_error(tilt),
            "substitutionVarianceChange": substitution_variance_change(tilt),
            "marginalGrowthContribution": marginal_growth_contribution(tilt),
            "varianceDrag": [
                {"gamma": gamma, "expected": variance_drag(tilt, gamma=gamma)}
                for gamma in TILT_GAMMAS
            ],
            "certaintyEquivalentContribution": [
                {
                    "gamma": gamma,
                    "expected": certainty_equivalent_contribution(tilt, gamma=gamma),
                }
                for gamma in TILT_GAMMAS
            ],
            "verdict": {
                "gamma": 3.0,
                "years": 30.0,
                "weight": verdict.weight,
                "deliveredLoading": verdict.delivered_loading,
                "hmlPremium": verdict.hml_premium,
                "incrementalCost": verdict.incremental_cost,
                "sleeveEdgePercent": verdict.sleeve_edge_percent,
                "portfolioEdgeBasisPoints": verdict.portfolio_edge_basis_points,
                "portfolioTrackingErrorBasisPoints": (
                    verdict.portfolio_tracking_error_basis_points
                ),
                "growthContributionPercent": verdict.growth_contribution_percent,
                "certaintyEquivalentPercent": verdict.certainty_equivalent_percent,
                "terminalWealthMultiple30y": verdict.terminal_wealth_multiple_30y,
            },
        }
        for label, tilt, verdict in (
            (label, tilt, tilt_verdict(tilt)) for label, tilt in tilt_cases
        )
    ],
    # `k * turnover` basis points in percent per year, over the range
    # `portfolio_edge.core.costs` calibrates and the turnover rates the shelf files.
    "turnoverCost": [
        {
            "oneSidedTurnoverPercent": turnover,
            "coefficient": coefficient,
            "expected": turnover_cost_percent(
                one_sided_turnover_percent=turnover, coefficient=coefficient
            ),
        }
        for turnover in (0.0, 3.0, 4.0, 5.0, 6.0, 7.0, 9.0, 25.0, 42.0, 105.0)
        for coefficient in (0.0, 1.0, 1.7)
    ],
    # `exp(g T)` against the untilted portfolio, on growth contributions of both signs.
    "terminalWealthMultiple": [
        {
            "growthContribution": growth,
            "years": years,
            "expected": terminal_wealth_multiple(
                growth_contribution=growth, years=years
            ),
        }
        for growth in (-0.2024, -0.0432, 0.0, 0.2140, 0.2494, 0.2949, 0.56)
        for years in (0.0, 1.0, 10.0, 30.0, 50.0)
    ],
}

print(json.dumps(out, indent=2))
