"""End-to-end tests for Experiment 004, offline.

The real inputs cannot be committed, so the whole path — cache, workbook parsing,
sheet pinning, the hard sha256 pin, alignment, the burn-in split, the five
portfolio constructions, the cost columns, the paired bootstrap, every hostile
test, the frozen rejection rule, the artifacts and the ledger — runs against
synthetic files in exactly the vendors' layouts, seeded into a temporary cache
under the real URLs.

Expected values are computed **in this file, with plain NumPy, from the generated
inputs**, never by calling the code under test.
"""

from __future__ import annotations

import io
import math
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import openpyxl  # type: ignore[import-untyped]
import pytest
import yaml

from portfolio_edge.data import aqr, french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.experiments.exp_004_trend_marginal_value import (
    COMPARISON_IDS,
    ENTRY_POINT,
    TrendMarginalValueError,
    build_registry,
    certainty_equivalent_annual,
    default_specification_path,
    run,
)
from portfolio_edge.experiments.ledger import Ledger, LedgerEvent, RunStatus
from portfolio_edge.experiments.registry import RunContext
from portfolio_edge.experiments.result import CostBasis, ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import (
    Specification,
    specification_from_mapping,
)

BURN_IN_START = "1985-01"
SAMPLE_START = "1990-01"
SAMPLE_END = "2025-12"
DATA_END = "2026-05"

FF5_COLUMNS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
_SIGMA = {"Mkt-RF": 4.5, "SMB": 3.0, "HML": 2.9, "RMW": 2.1, "CMA": 2.0, "RF": 0.05}
_MU = {"Mkt-RF": 0.55, "SMB": 0.20, "HML": 0.25, "RMW": 0.25, "CMA": 0.20, "RF": 0.30}


# --------------------------------------------------------------------------- #
# Synthetic inputs in the real layouts
# --------------------------------------------------------------------------- #


def _months(start: str, end: str) -> list[str]:
    def index(period: str) -> int:
        year, month = period.split("-")
        return int(year) * 12 + int(month) - 1

    return [f"{i // 12:04d}-{i % 12 + 1:02d}" for i in range(index(start), index(end) + 1)]


def _month_end(period: str) -> date:
    year, month = (int(part) for part in period.split("-"))
    following = date(year + month // 12, month % 12 + 1, 1)
    return following - timedelta(days=1)


def synthetic_aqr_workbook(periods: Sequence[str], values: np.ndarray) -> bytes:
    """A workbook in the vendor's layout: prose block, header row, month-end dates."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "TSMOM Factors"
    for line in (
        "A synthetic fixture, not an AQR download.",
        "",
        "This file contains the excess returns of the long/short TSMOM factors.",
        "Data are updated as they become available. The full history is reconstructed.",
        "",
    ):
        sheet.append([line])
    sheet.append([None, "TSMOM", "TSMOM^CM", "TSMOM^EQ", "TSMOM^FI", "TSMOM^FX"])
    for index, period in enumerate(periods):
        row = values[index]
        sheet.append([_month_end(period), *(float(item) for item in row)])
    for name in ("Definitions", "Data Sources", "Disclosures"):
        workbook.create_sheet(name).append([name])
    payload = io.BytesIO()
    workbook.save(payload)
    return payload.getvalue()


def synthetic_french_csv(periods: Sequence[str], columns: Mapping[str, np.ndarray]) -> bytes:
    lines = [
        "This file was created using a synthetic fixture, not a CRSP database.",
        "Missing data are indicated by -99.99.",
        "",
        "," + ",".join(FF5_COLUMNS),
    ]
    for index, period in enumerate(periods):
        cells = [f"{columns[name][index]:>8.4f}" for name in FF5_COLUMNS]
        lines.append(period.replace("-", "") + "," + ",".join(cells))
    lines.append("")
    lines.append("  Annual Factors: January-December")
    lines.append("," + ",".join(FF5_COLUMNS))
    for year in sorted({period[:4] for period in periods}):
        lines.append(year + "," + ",".join(["1.00"] * len(FF5_COLUMNS)))
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def synthetic_fred_csv(series_id: str, periods: Sequence[str], values: np.ndarray) -> bytes:
    lines = [f"observation_date,{series_id}"]
    for period, value in zip(periods, values, strict=True):
        lines.append(f"{period}-01,{value:.4f}")
    return ("\n".join(lines) + "\n").encode("utf-8")


@pytest.fixture(scope="module")
def generated() -> dict[str, Any]:
    """One deterministic panel, generated once and reused by every test here."""
    rng = np.random.default_rng(4004)
    periods = _months(BURN_IN_START, DATA_END)
    n = len(periods)

    french_columns = {
        name: rng.normal(_MU[name], _SIGMA[name], size=n) for name in FF5_COLUMNS
    }
    french_columns["RF"] = np.abs(french_columns["RF"])
    # A trend sleeve with a real crisis payoff: mildly positive on average and
    # explicitly short the market in the worst months, so the experiment has
    # something to find rather than only noise.
    market = french_columns["Mkt-RF"] / 100.0
    sleeve = rng.normal(0.004, 0.035, size=n) - 0.45 * np.where(market < -0.06, market, 0.0)
    sub = np.column_stack([sleeve] + [sleeve + rng.normal(0.0, 0.02, size=n) for _ in range(4)])

    cash_annual = np.clip(french_columns["RF"] * 12.0, 0.01, None)
    gs10 = cash_annual + np.abs(rng.normal(1.5, 0.4, size=n))
    return {
        "periods": periods,
        "french": french_columns,
        "sleeve": sleeve,
        "aqr_values": sub,
        "cash_annual": cash_annual,
        "gs10": gs10,
    }


@pytest.fixture
def sources(tmp_path: Path, generated: dict[str, Any]) -> dict[str, Any]:
    """Seed a fresh cache with every synthetic input under its real URL."""
    cache = RawCache(tmp_path / "cache")
    periods = generated["periods"]

    dataset = aqr.get_dataset("aqr_tsmom_factors")
    workbook = synthetic_aqr_workbook(periods, generated["aqr_values"])
    aqr_entry = cache.store(
        dataset.url,
        workbook,
        headers={"Content-Type": "application/vnd.ms-excel", "Last-Modified": "x"},
    )
    parsed = aqr.parse(cache, aqr_entry, dataset=dataset)

    french_dataset = french.get_dataset("french_us_ff5")
    french_entry = cache.store(
        french_dataset.url, synthetic_french_csv(periods, generated["french"])
    )

    for series_id, values in (
        ("TB3MS", generated["cash_annual"]),
        ("GS10", generated["gs10"]),
    ):
        cache.store(
            f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}",
            synthetic_fred_csv(series_id, periods, values),
        )
    return {
        "cache": cache,
        "aqr_sha": aqr_entry.sha256,
        "aqr_normalized": parsed.table.sha256_normalized(),
        "french_sha": french_entry.sha256,
        "root": tmp_path,
    }


def _cell(frame: Any, row: str, column: str) -> float:
    """Read one cell out of a result frame as a float, past pandas' wide stub type."""
    return float(str(frame.loc[row, column]))


def specification_for(sources: Mapping[str, Any], **overrides: Any) -> Specification:
    """The committed specification, repointed at the synthetic vintages."""
    raw = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    pin = raw["parameters"]["source_pin"]
    pin["aqr_tsmom"]["expected_sha256_raw"] = overrides.get(
        "aqr_sha", sources["aqr_sha"]
    )
    pin["aqr_tsmom"]["expected_sha256_normalized"] = overrides.get(
        "aqr_normalized", sources["aqr_normalized"]
    )
    pin["french_us_market"]["expected_sha256_raw"] = sources["french_sha"]
    for entry in pin.values():
        if isinstance(entry, dict):
            entry.pop("committed_manifest", None)
    raw["inference"]["resamples"] = overrides.get("resamples", 400)
    return specification_from_mapping(raw, source_path=default_specification_path())


@pytest.fixture
def executed(
    sources: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> tuple[Specification, ExperimentResult]:
    monkeypatch.setenv("PORTFOLIO_EDGE_CACHE_DIR", str(sources["cache"].root))
    specification = specification_for(sources)
    context = RunContext(
        run_id="test",
        seed=1,
        rng=np.random.default_rng(1),
        artifact_dir=sources["root"] / "artifacts",
    )
    return specification, run(specification, context)


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


def test_the_experiment_runs_and_reports_all_five_portfolios(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    rows = result.diagnostics["portfolio_statistics"]
    assert isinstance(rows, Sequence)
    full = [
        row
        for row in rows
        if isinstance(row, Mapping)
        and row["window"] == "full_period"
        and row["cost_basis"] == CostBasis.NET_PESSIMISTIC.value
    ]
    assert {str(row["portfolio"]) for row in full} == set(COMPARISON_IDS)
    # 1990-01..2025-12 is 432 months, exactly 36 whole calendar years.
    assert all(int(str(row["observations"])) == 432 for row in full)


def test_the_burn_in_is_used_only_to_warm_the_estimators(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    sample = result.diagnostics["sample"]
    assert isinstance(sample, Mapping)
    assert sample["reported_first_month"] == SAMPLE_START
    assert sample["reported_last_month"] == SAMPLE_END
    assert sample["burn_in_first_month"] == BURN_IN_START
    assert int(str(sample["burn_in_months"])) == 60


def test_the_holdout_is_never_read(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """The workbook reaches 2026-05; five months sit beyond the frozen boundary."""
    _, result = executed
    sample = result.diagnostics["sample"]
    assert isinstance(sample, Mapping)
    beyond = sample["months_available_beyond_the_holdout"]
    assert isinstance(beyond, Mapping)
    assert int(str(beyond["months_clipped"])) == 5
    assert beyond["sample_end"] == SAMPLE_END


def test_the_marginal_metric_matches_an_independent_computation(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """Recompute the headline number from the artifact's own frames."""
    _, result = executed
    frame = result.frames["portfolio_statistics"]
    full = frame[
        (frame["window"] == "full_period")
        & (frame["cost_basis"] == CostBasis.NET_PESSIMISTIC.value)
    ].set_index("portfolio")
    expected = _cell(
        full, "passive_plus_trend", "certainty_equivalent_percent_per_year"
    ) - _cell(full, "passive_plus_cash", "certainty_equivalent_percent_per_year")
    marginal = result.diagnostics["marginal_results"]
    assert isinstance(marginal, Sequence)
    primary = next(
        row
        for row in marginal
        if isinstance(row, Mapping)
        and row["treatment_portfolio"] == "passive_plus_trend"
        and row["window"] == "full_period"
    )
    assert float(str(primary["marginal_percentage_points_per_year"])) == pytest.approx(
        expected, abs=1e-9
    )


def test_the_risk_matched_comparator_really_is_risk_matched(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """Comparing against the fully invested portfolio would flatter the sleeve."""
    _, result = executed
    frame = result.frames["portfolio_statistics"]
    full = frame[
        (frame["window"] == "full_period")
        & (frame["cost_basis"] == CostBasis.NET_PESSIMISTIC.value)
    ].set_index("portfolio")
    with_trend = _cell(full, "passive_plus_trend", "annualised_volatility_percent")
    with_cash = _cell(full, "passive_plus_cash", "annualised_volatility_percent")
    passive = _cell(full, "passive_benchmark", "annualised_volatility_percent")
    # The two comparators sit within a percentage point of each other and both
    # below the fully invested benchmark, which is what "matched budget" means.
    assert abs(with_trend - with_cash) < 1.0
    assert with_cash < passive


def test_every_cost_column_is_reported_separately_and_never_averaged(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    frame = result.frames["portfolio_statistics"]
    bases = set(frame["cost_basis"].unique())
    assert bases == {
        CostBasis.GROSS.value,
        CostBasis.NET_OPTIMISTIC.value,
        CostBasis.NET_PESSIMISTIC.value,
    }
    trend = frame[
        (frame["portfolio"] == "trend_alone") & (frame["window"] == "full_period")
    ].set_index("cost_basis")
    gross = _cell(trend, CostBasis.GROSS.value, "geometric_annual_percent")
    optimistic = _cell(trend, CostBasis.NET_OPTIMISTIC.value, "geometric_annual_percent")
    pessimistic = _cell(trend, CostBasis.NET_PESSIMISTIC.value, "geometric_annual_percent")
    assert gross > optimistic > pessimistic


def test_every_hostile_test_the_specification_demands_is_present(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    hostile = result.diagnostics["hostile_tests"]
    assert isinstance(hostile, Mapping)
    for required in (
        "remove_the_best_trend_month",
        "remove_the_best_crisis",
        "delay_execution",
        "double_every_cost",
        "cap_leverage",
        "gaps_and_reversals",
        "change_the_volatility_lookback",
        "static_and_volatility_exposure_replica",
        "bond_leg_robustness_arm",
    ):
        assert required in hostile, required


def test_doubling_the_costs_never_improves_the_result(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    hostile = result.diagnostics["hostile_tests"]
    assert isinstance(hostile, Mapping)
    doubled = hostile["double_every_cost"]
    baseline = float(str(hostile["baseline_marginal_percentage_points_per_year"]))
    assert isinstance(doubled, Mapping)
    assert float(str(doubled["marginal_percentage_points_per_year"])) <= baseline + 1e-9


def test_the_volatility_lookback_grid_covers_the_frozen_alternatives(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    hostile = result.diagnostics["hostile_tests"]
    assert isinstance(hostile, Mapping)
    lookback = hostile["change_the_volatility_lookback"]
    assert isinstance(lookback, Mapping)
    rows = lookback["rows"]
    assert isinstance(rows, Sequence)
    declared = {
        float(str(row["lookback_days_declared"]))
        for row in rows
        if isinstance(row, Mapping)
    }
    assert declared == {60.0, 20.0, 120.0}
    for row in rows:
        assert isinstance(row, Mapping)
        assert float(str(row["monthly_centre_of_mass"])) == pytest.approx(
            float(str(row["lookback_days_declared"])) / 21.0
        )


def test_the_replica_that_drives_the_falsifier_excludes_the_intercept() -> None:
    """The bug this assertion exists to prevent.

    An OLS intercept is the part the exposures do not explain. A replica that keeps
    it pays the sleeve's whole alpha at a fraction of its volatility, beats the
    sleeve, and fires falsifier clause (d) on an artefact of the arithmetic rather
    than on any exposure a portfolio could hold.
    """
    source = (
        Path(__file__).resolve().parents[2]
        / "src/portfolio_edge/experiments/exp_004_trend_marginal_value.py"
    ).read_text(encoding="utf-8")
    assert "exposures_only = fitted - intercept" in source
    assert 'replace_sleeve("exposures_only_replica", replica_full)' in source


def test_the_replica_reports_both_readings_and_names_the_one_that_decides(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    hostile = result.diagnostics["hostile_tests"]
    assert isinstance(hostile, Mapping)
    replica = hostile["static_and_volatility_exposure_replica"]
    assert isinstance(replica, Mapping)
    assert "INTERCEPT REMOVED" in str(replica["replica_definition"])
    assert "clause (d)" in str(replica["replica_definition"])
    assert "fitted_including_intercept_marginal" in replica
    assert "category error" in str(replica["why_the_intercept_is_excluded"])


def test_a_leverage_cap_that_binds_on_the_comparator_is_flagged_as_invalid(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """A cap below the matched exposure de-risks the control and flatters the sleeve."""
    _, result = executed
    hostile = result.diagnostics["hostile_tests"]
    assert isinstance(hostile, Mapping)
    cap = hostile["cap_leverage"]
    assert isinstance(cap, Mapping)
    rows = cap["rows"]
    assert isinstance(rows, Sequence)
    for row in rows:
        assert isinstance(row, Mapping)
        binding = int(str(row["months_the_cap_binds_on_the_comparator"]))
        assert row["risk_match_broken"] is (binding > 0)
        if binding > 0:
            assert "NOT A VALID MARGINAL COMPARISON" in str(row["reading"])
        else:
            assert str(row["reading"]).startswith("VALID")


def test_the_crisis_table_reports_its_effective_sample_beside_every_figure(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    crisis = result.diagnostics["crisis_conditional"]
    assert isinstance(crisis, Mapping)
    rows = crisis["per_crisis"]
    assert isinstance(rows, Sequence)
    assert {str(row["crisis"]) for row in rows if isinstance(row, Mapping)} == {
        "dotcom",
        "gfc",
        "covid",
        "inflation_2022",
    }
    for row in rows:
        assert isinstance(row, Mapping)
        assert "effective_independent_blocks_at_12m" in row
    union = crisis["union"]
    assert isinstance(union, Mapping)
    # 25 + 16 + 2 + 10 months of frozen crisis windows.
    assert int(str(union["observations"])) == 53
    assert "power_warning" in union


def test_a_shallower_crisis_drawdown_is_reported_as_a_positive_reduction(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """Drawdowns are signed and non-positive; the wrong order flips every sign."""
    _, result = executed
    frame = result.frames["portfolio_statistics"]
    crisis = frame[
        (frame["window"] == "crisis_union")
        & (frame["cost_basis"] == CostBasis.NET_PESSIMISTIC.value)
    ].set_index("portfolio")
    treatment = _cell(crisis, "passive_plus_trend", "max_drawdown_percent")
    comparator = _cell(crisis, "passive_plus_cash", "max_drawdown_percent")

    diagnostics = result.diagnostics["crisis_conditional"]
    assert isinstance(diagnostics, Mapping)
    rows = diagnostics["per_crisis"]
    assert isinstance(rows, Sequence)
    for row in rows:
        assert isinstance(row, Mapping)
        column = row.get(CostBasis.NET_PESSIMISTIC.value)
        if not isinstance(column, Mapping):
            continue
        reduction = float(str(column["marginal_drawdown_reduction_percentage_points"]))
        window = column["window_compound_return_percent"]
        assert isinstance(window, Mapping)
        # Whenever the trend portfolio compounds better through a crisis window, the
        # reported reduction must not be negative.
        if float(str(window["passive_plus_trend"])) > float(
            str(window["passive_plus_cash"])
        ):
            assert reduction >= -1e-9, row["crisis"]
    assert (treatment > comparator) == (treatment - comparator > 0.0)


def test_the_tests_that_cannot_be_run_are_recorded_with_their_reasons(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """The Kim-Tse-Wald test is the most informative one and it is unavailable."""
    _, result = executed
    unavailable = result.diagnostics["unavailable_tests"]
    assert isinstance(unavailable, Sequence)
    names = {str(item["test"]) for item in unavailable if isinstance(item, Mapping)}
    assert any("Kim, Tse and Wald" in name for name in names)
    for item in unavailable:
        assert isinstance(item, Mapping)
        assert item["run"] is False
        assert len(str(item["reason"])) > 80


def test_the_result_carries_the_vendor_disclosure_and_the_survivorship_caveat(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    joined = " ".join(result.caveats)
    assert "NOT AN INDEPENDENT REPLICATION" in joined
    assert "7.7 percentage points" in joined
    assert "UNESTABLISHED" in joined
    assert "Kim, Tse and Wald" in joined
    disclosure = result.diagnostics["evaluation_disclosure"]
    assert isinstance(disclosure, Mapping)
    assert disclosure["is_independent_replication"] is False


def test_the_status_can_never_exceed_exploratory(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    assert result.status in {
        ResultStatus.EXPLORATORY,
        ResultStatus.UNRESOLVED,
        ResultStatus.REJECTED,
    }


def test_the_verdict_names_the_clauses_that_fired(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    verdict = result.diagnostics["verdict"]
    assert isinstance(verdict, Mapping)
    fired = verdict["falsifier_clauses_fired"]
    assert isinstance(fired, Sequence)
    if result.status is ResultStatus.REJECTED:
        assert fired
    else:
        assert not fired
    assert "precedence_note" in verdict


def test_the_multiple_testing_family_is_corrected_and_its_dependence_declared(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    correction = result.diagnostics["multiple_testing"]
    assert isinstance(correction, Mapping)
    assert correction["method"] == "holm-bonferroni"
    rows = correction["rows"]
    assert isinstance(rows, Sequence)
    for row in rows:
        assert isinstance(row, Mapping)
        assert float(str(row["holm_adjusted_p"])) >= float(str(row["p_uncorrected"])) - 1e-12
    assert "LOWER bound" in str(correction["dependence_warning"])


def test_an_unrecognised_vendor_vintage_aborts_instead_of_reporting_utility(
    sources: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """AQR reconstructs its whole history, so a new hash is a new history."""
    monkeypatch.setenv("PORTFOLIO_EDGE_CACHE_DIR", str(sources["cache"].root))
    specification = specification_for(sources, aqr_sha="0" * 64)
    context = RunContext(
        run_id="t", seed=1, rng=np.random.default_rng(1), artifact_dir=sources["root"] / "a"
    )
    with pytest.raises(TrendMarginalValueError, match="reconstructs the full history"):
        run(specification, context)


def test_a_parser_change_that_leaves_the_bytes_alone_is_caught(
    sources: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PORTFOLIO_EDGE_CACHE_DIR", str(sources["cache"].root))
    specification = specification_for(sources, aqr_normalized="0" * 64)
    context = RunContext(
        run_id="t", seed=1, rng=np.random.default_rng(1), artifact_dir=sources["root"] / "a"
    )
    with pytest.raises(TrendMarginalValueError, match="parser changed behaviour"):
        run(specification, context)


def test_the_run_is_ledgered_with_provenance_and_hashed_artifacts(
    sources: dict[str, Any], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PORTFOLIO_EDGE_CACHE_DIR", str(sources["cache"].root))
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        specification_for(sources),
        registry=build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
    )
    assert outcome.status is RunStatus.SUCCEEDED
    assert outcome.artifacts
    entries = list(ledger.read())
    events = [entry.event for entry in entries]
    assert LedgerEvent.STARTED in events
    assert LedgerEvent.SUCCEEDED in events
    assert all(entry.results_viewed is False for entry in entries)


def test_the_registry_resolves_the_committed_entry_point() -> None:
    registry = build_registry()
    assert ENTRY_POINT in registry


def test_a_certainty_equivalent_of_the_synthetic_passive_path_is_recomputable(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """The CE reported for one portfolio must be reproducible from its own frame."""
    _, result = executed
    frame = result.frames["portfolio_statistics"]
    row = frame[
        (frame["portfolio"] == "passive_benchmark")
        & (frame["window"] == "full_period")
        & (frame["cost_basis"] == CostBasis.GROSS.value)
    ].iloc[0]
    reported = float(row["certainty_equivalent_percent_per_year"])
    geometric = float(row["geometric_annual_percent"])
    volatility = float(row["annualised_volatility_percent"])
    # At gamma=3 the certainty equivalent sits below the geometric mean by
    # roughly (gamma-1)/2 times the annual variance.
    penalty = 0.5 * (3.0 - 1.0) * (volatility / 100.0) ** 2 * 100.0
    assert reported < geometric
    assert math.isclose(geometric - reported, penalty, rel_tol=0.6)
    assert certainty_equivalent_annual(np.array([1.0 + geometric / 100.0]), gamma=3.0) > 0.0
