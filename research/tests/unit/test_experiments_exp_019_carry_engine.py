"""Unit tests for Experiment 019, carry as a second financed engine.

Every expected value here is computed in this file by hand or with plain NumPy,
never by calling the code under test on the same inputs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

import portfolio_edge.experiments.exp_019_carry_engine as module
from portfolio_edge.experiments.exp_016_construction_tournament import (
    BasisPanel,
    CostSettings,
)
from portfolio_edge.experiments.exp_019_carry_engine import (
    CARRY_VARIANTS,
    CarryEngineError,
    arm_notional,
    carry_variants,
    correlation_table,
    default_specification_path,
    read_arms,
    read_panels,
    read_rates,
    read_wrappers,
    simulate_arm,
    sum_rule_residual,
    wrapper_excess,
)
from portfolio_edge.experiments.specification import (
    JsonValue,
    Specification,
    load_specification,
    validate_specification,
)

SPEC_PATH = default_specification_path()


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(SPEC_PATH)


def _panel(
    months: int, *, legs: Mapping[str, Sequence[float]], cash: Sequence[float]
) -> BasisPanel:
    return BasisPanel(
        periods=tuple(f"{2000 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(months)),
        series={k: np.asarray(v, dtype=np.float64) for k, v in legs.items()},
        cash=np.asarray(cash, dtype=np.float64),
        provenance=(),
        findings=(),
    )


def _mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


# --------------------------------------------------------------------------- #
# The committed specification says what the design says
# --------------------------------------------------------------------------- #


def test_the_specification_is_frozen_as_the_design_states(specification: Specification) -> None:
    validate_specification(specification)
    assert specification.experiment_family == "exp_019_carry_engine"
    assert specification.entry_point == module.ENTRY_POINT
    parameters = _mapping(specification.parameters)
    carry = _mapping(parameters["carry_leg"])
    assert carry["column"] == "All Macro Carry"
    assert carry["target_volatility_percent"] == 12.38
    assert carry["delivered_loading_sensitivity"] == 0.681
    trend = _mapping(parameters["trend_book"])
    assert trend["target_volatility_percent"] == 12.38
    fees = _mapping(_mapping(specification.cost_model)["wrapper_expense_ratio_basis_points"])
    assert fees["RSSY_LIKE"] == 99 and fees["RSST_LIKE"] == 99 and fees["CORE"] == 3
    haircuts = _mapping(_mapping(specification.cost_model)["carry_leg_haircut_pp_yr"])
    assert haircuts["cost_1pp"] == 1.0 and haircuts["cost_2pp"] == 2.0
    # The prediction is written down before the run, as a bracket.
    assert "PREDICTION IS THEREFORE A BRACKET" in Path(SPEC_PATH).read_text(encoding="utf-8")
    pins = {
        str(_mapping(item)["id"]): _mapping(item)
        for item in _mapping(parameters["source_pin"])["files"]  # type: ignore[union-attr]
    }
    assert pins["aqr_century_factor_premia"]["expected_sha256_raw"] == (
        "0bf8ba978e64964282ead98a6a25691218d4517d07c98c89e2716706f6f0a127"
    )
    # The trend book and its sources are Experiment 018's, pinned to the same digests.
    exp_018 = load_specification(SPEC_PATH.with_name("exp_018_defensive_engines.yaml"))
    other = {
        str(_mapping(item)["id"]): _mapping(item)
        for item in _mapping(_mapping(exp_018.parameters)["source_pin"])["files"]  # type: ignore[union-attr]
    }
    for shared in (
        "french_us_ff3",
        "goyal_welch_predictors",
        "aqr_commodities_long_run",
        "aqr_tsmom_factors",
    ):
        assert pins[shared]["expected_sha256_raw"] == other[shared]["expected_sha256_raw"], shared
    other_trend = _mapping(_mapping(exp_018.parameters)["trend_book"])
    for key in (
        "instruments",
        "lookback_months",
        "volatility_window_months",
        "per_position_volatility_target",
        "position_cap",
        "minimum_live_instruments",
        "target_volatility_percent",
    ):
        assert trend[key] == other_trend[key], key


def test_the_eight_crisis_episodes_are_experiment_018s(specification: Specification) -> None:
    exp_018 = load_specification(SPEC_PATH.with_name("exp_018_defensive_engines.yaml"))
    mine = _mapping(_mapping(specification.parameters)["crisis_episodes"])
    theirs = _mapping(_mapping(exp_018.parameters)["crisis_episodes"])
    for kind in ("deflationary_or_growth", "inflation_or_rate"):
        assert mine[kind] == theirs[kind]


def test_every_panel_names_a_known_carry_variant(specification: Specification) -> None:
    panels = read_panels(specification)
    assert {p.id for p in panels} >= {
        "primary",
        "four_class_subwindow",
        "secondary",
        "post_publication_check",
        "carry_cost_1pp",
        "carry_cost_2pp",
        "carry_loading_0681",
        "carry_shifted_one_month",
    }
    for panel in panels:
        assert panel.carry_source in CARRY_VARIANTS
    assert next(p for p in panels if p.id == "four_class_subwindow").start == "1974-02"
    assert next(p for p in panels if p.id == "post_publication_check").start == "2013-09"


# --------------------------------------------------------------------------- #
# Notional derivation, one row per arm, by hand
# --------------------------------------------------------------------------- #


EXPECTED_NOTIONAL = {
    # arm: (gross, equity, trend, carry, cash)
    "base_trend30": (0.70 + 0.30 * 2.072, 0.70 + 0.30 * 1.072, 0.30, 0.0, 0.0),
    "base_no_trend": (1.0, 1.0, 0.0, 0.0, 0.0),
    "carry30_no_trend": (0.70 + 0.30 * 2.0, 1.0, 0.0, 0.30, 0.0),
    "trend30_carrystack10": (
        0.60 + 0.30 * 2.072 + 0.10 * 2.0,
        0.60 + 0.30 * 1.072 + 0.10,
        0.30,
        0.10,
        0.0,
    ),
    "trend30_carrystack20": (
        0.50 + 0.30 * 2.072 + 0.20 * 2.0,
        0.50 + 0.30 * 1.072 + 0.20,
        0.30,
        0.20,
        0.0,
    ),
    "trend15_carry15": (
        0.70 + 0.15 * 2.072 + 0.15 * 2.0,
        0.70 + 0.15 * 1.072 + 0.15,
        0.15,
        0.15,
        0.0,
    ),
    "trend30_carry30": (
        0.40 + 0.30 * 2.072 + 0.30 * 2.0,
        0.40 + 0.30 * 1.072 + 0.30,
        0.30,
        0.30,
        0.0,
    ),
}


def test_every_arm_derives_the_notional_the_design_states(specification: Specification) -> None:
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    assert set(arms) == set(EXPECTED_NOTIONAL)
    for name, arm in arms.items():
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        gross, equity, trend, carry, cash = EXPECTED_NOTIONAL[name]
        assert notional.gross == pytest.approx(gross, abs=1e-12), name
        assert notional.equity == pytest.approx(equity, abs=1e-12), name
        assert notional.trend == pytest.approx(trend, abs=1e-12), name
        assert notional.carry == pytest.approx(carry, abs=1e-12), name
        assert notional.cash == pytest.approx(cash, abs=1e-12), name
    # The stacks keep the reference's equity notional; the substitution does not.
    reference = arm_notional(arms["base_trend30"].tickers, arms["base_trend30"].weights, wrappers)
    for name in ("trend30_carrystack10", "trend30_carrystack20", "trend30_carry30"):
        arm = arms[name]
        assert arm_notional(arm.tickers, arm.weights, wrappers).equity == pytest.approx(
            reference.equity
        )
    assert arm_notional(
        arms["trend15_carry15"].tickers, arms["trend15_carry15"].weights, wrappers
    ).equity == pytest.approx(1.0108)


def test_a_wrapper_financing_anything_but_equity_is_refused(tmp_path: Path) -> None:
    text = Path(SPEC_PATH).read_text(encoding="utf-8")
    old = "      financed: {equity: 0.25}\n"
    assert text.count(old) == 1
    altered = tmp_path / "altered.yaml"
    altered.write_text(text.replace(old, "      financed: {equity: 0.25, carry: 1.0}\n"))
    with pytest.raises(CarryEngineError, match="finances 'carry'"):
        read_wrappers(load_specification(altered))


# --------------------------------------------------------------------------- #
# Costs accrue against the holder
# --------------------------------------------------------------------------- #


def test_the_rssy_like_wrapper_pays_its_fee_and_the_basis_on_a_quarter_of_equity(
    specification: Specification,
) -> None:
    wrappers = read_wrappers(specification)
    rates = read_rates(specification)
    assert rates.equity == 62.0
    panel = _panel(3, legs={"equity": [0.0] * 3, "carry": [0.0] * 3}, cash=[0.0] * 3)
    excess = wrapper_excess(panel, wrappers["RSSY_LIKE"], rates)
    expected = -(99.0 + 0.25 * 62.0) / 10_000.0 / 12.0
    assert excess == pytest.approx(np.full(3, expected))
    # Ten points of the wrapper in place of ten points of core cost 11.15 bp/yr, certain:
    # (99 + 0.25 x 62 - 3) x 0.10. The specification's mechanism note says 11.45, an
    # arithmetic slip of 0.3 bp recorded in the synthesis rather than edited after the run.
    core = wrapper_excess(panel, wrappers["CORE"], rates)
    certain_cost_bp = -(excess[0] - core[0]) * 12.0 * 10_000.0 * 0.10
    assert certain_cost_bp == pytest.approx(11.15)


def test_carry_stack_arm_two_period_fixture(specification: Specification) -> None:
    """60% CORE + 30% RSST_LIKE + 10% RSSY_LIKE over two months, spreads off."""
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    rates = read_rates(specification)
    arm = arms["trend30_carrystack10"]
    costs = CostSettings(
        equity_futures_basis=rates.equity / 10_000.0,
        trend_book_financing=0.0,
        round_trip_spread={"us_equity": 0.0},
    )
    equity = [0.02, -0.03]
    trend = [-0.005, 0.012]
    carry = [0.008, -0.004]
    cash = [0.003, 0.002]
    panel = _panel(2, legs={"equity": equity, "trend": trend, "carry": carry}, cash=cash)
    path = simulate_arm(
        panel, wrappers, rates, costs, tickers=arm.tickers, targets=np.asarray(arm.weights)
    )
    expected = []
    for t in range(2):
        core = equity[t] - 3.0 / 120_000.0
        rsst = 1.072 * equity[t] + trend[t] - (99.0 + 0.331 * 62.0) / 120_000.0
        rssy = equity[t] + carry[t] - (99.0 + 0.25 * 62.0) / 120_000.0
        expected.append(cash[t] + 0.60 * core + 0.30 * rsst + 0.10 * rssy)
    assert path.total == pytest.approx(np.asarray(expected), abs=1e-12)


# --------------------------------------------------------------------------- #
# The carry variants and the descriptive tables
# --------------------------------------------------------------------------- #


def test_carry_variants_are_the_frozen_hostile_reruns() -> None:
    months = [f"{1990 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(5)]
    base = dict(zip(months, [0.01, -0.02, 0.03, 0.0, 0.005], strict=True))
    out = carry_variants(base, haircuts_pp_yr={"cost_1pp": 1.0, "cost_2pp": 2.0}, loading=0.681)
    assert set(out) == set(CARRY_VARIANTS)
    assert out["published"] == base
    assert out["cost_1pp"][months[0]] == pytest.approx(0.01 - 0.01 / 12.0)
    assert out["cost_2pp"][months[1]] == pytest.approx(-0.02 - 0.02 / 12.0)
    assert out["loading_0681"][months[2]] == pytest.approx(0.03 * 0.681)
    # The shift moves every observation one month later and drops the first.
    assert months[0] not in out["shifted_one_month"]
    assert out["shifted_one_month"][months[1]] == pytest.approx(0.01)
    assert out["shifted_one_month"][months[4]] == pytest.approx(0.0)
    # Means are preserved by the shift, within the dropped month.
    assert sum(out["shifted_one_month"].values()) == pytest.approx(sum(base.values()) - 0.005)


def test_correlation_table_matches_numpy_on_the_worst_decile() -> None:
    rng = np.random.default_rng(7)
    equity = rng.normal(0.006, 0.05, 200)
    trend = rng.normal(0.004, 0.035, 200) - 0.2 * equity
    carry = rng.normal(0.005, 0.03, 200) + 0.1 * equity
    table = correlation_table(
        {"equity": equity, "trend": trend, "carry": carry}, equity=equity, tail=0.10
    )
    full = _mapping(table["correlation_full"])
    worst = _mapping(table["correlation_worst_decile_of_equity"])
    assert table["worst_decile_months"] == 20
    assert full["equity_trend"] == pytest.approx(np.corrcoef(equity, trend)[0, 1], abs=5e-4)
    assert full["trend_carry"] == pytest.approx(np.corrcoef(trend, carry)[0, 1], abs=5e-4)
    low = np.argsort(equity)[:20]
    assert worst["equity_carry"] == pytest.approx(
        np.corrcoef(equity[low], carry[low])[0, 1], abs=5e-4
    )
    legs = _mapping(table["legs"])
    assert _mapping(legs["carry"])["full_pp_yr"] == pytest.approx(
        float(np.mean(carry)) * 1200.0, abs=5e-3
    )


def test_sum_rule_residual_is_the_stated_identity() -> None:
    assert sum_rule_residual(3.0, 2.0, 1.2) == pytest.approx(-0.2)
    assert sum_rule_residual(3.2, 2.0, 1.2) == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# The whole experiment on a short synthetic history
# --------------------------------------------------------------------------- #


def _synthetic_raw_series() -> module.RawSeries:
    rng = np.random.default_rng(20260902)
    months = [f"{1985 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(240)]
    equity = rng.normal(0.006, 0.045, 240)
    bond = rng.normal(0.002, 0.025, 240)
    cash = np.full(240, 0.003)

    def series(values: NDArray[np.float64]) -> dict[str, float]:
        return {m: float(v) for m, v in zip(months, values, strict=True)}

    carry = rng.normal(0.004, 0.02, 240)
    return module.RawSeries(
        equity=series(equity),
        cash=series(cash),
        ltr=series(bond + cash),
        corpr=series(bond + cash + rng.normal(0.0005, 0.01, 240)),
        gw_rfree=series(cash),
        commodity=series(rng.normal(0.002, 0.05, 240)),
        tsmom=series(rng.normal(0.008, 0.035, 240)),
        carry=series(carry),
        carry_components={
            "Equity indices Carry": series(rng.normal(0.003, 0.03, 240)),
            "Currencies Carry": series(rng.normal(0.003, 0.03, 240)),
        },
        provenance=({"id": "synthetic"},),
        findings=("synthetic",),
    )


def test_the_whole_experiment_runs_and_reports_what_the_contract_requires(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, specification: Specification
) -> None:
    import re

    from portfolio_edge.experiments.ledger import Ledger, RunStatus
    from portfolio_edge.experiments.result import ResultStatus
    from portfolio_edge.experiments.runner import run_experiment

    # The synthetic history is 20 years, so the declared 1974-02 and 2013-09
    # panel starts are dropped and the panels intersect on what exists.
    text = Path(SPEC_PATH).read_text(encoding="utf-8")
    altered = tmp_path / "altered.yaml"
    altered.write_text(re.sub(r'(carry_source: \w+\n)      start: "\d{4}-\d{2}"\n', r"\1", text))
    spec = load_specification(altered)
    assert all(p.start is None for p in read_panels(spec))
    monkeypatch.setattr(module, "load_series", lambda _spec: _synthetic_raw_series())
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        spec,
        registry=module.build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
    )
    assert outcome.status is RunStatus.SUCCEEDED
    result = outcome.result
    assert result is not None
    assert result.status in {ResultStatus.EXPLORATORY, ResultStatus.UNRESOLVED}

    panels = result.diagnostics["panels"]
    assert isinstance(panels, Sequence)
    by_id = {str(_mapping(p)["id"]): _mapping(p) for p in panels}
    assert {"primary", "secondary", "carry_cost_2pp", "carry_shifted_one_month"} <= set(by_id)
    arms = read_arms(specification)
    for panel in by_id.values():
        rows = panel["arms"]
        assert isinstance(rows, Sequence)
        for raw_row in rows:
            row = _mapping(raw_row)
            assert str(row["arm"]) in arms
            notional = _mapping(row["notional"])
            assert {"gross", "equity", "trend", "carry", "cash"} <= set(notional)
            assert row["max_drawdown_pct"] is not None
            assert isinstance(row["episodes"], Mapping)
            for control, raw_comparison in _mapping(row["comparisons"]).items():
                comparison = _mapping(raw_comparison)
                if comparison["identical_construction"]:
                    assert comparison["status"] == "not-scored", (row["arm"], control)
                    continue
                # A gap never appears without its floor, its control or its status.
                assert comparison["gap_pp_yr"] is not None
                assert comparison["mde_80pc_power_pp_yr"] is not None
                assert comparison["control_definition"]
                assert comparison["status"] in {"exploratory", "unresolved", "rejected"}
        correlations = _mapping(panel["correlations"])
        full = _mapping(correlations["correlation_full"])
        assert {"equity_trend", "equity_carry", "trend_carry"} == set(full)
        assert isinstance(panel["correlations_by_era"], Sequence)
        sum_rule = _mapping(panel["sum_rule"])
        assert sum_rule["residual_pp_yr"] is not None
        # With monthly rebalancing and no debt the overlay adds as a sum, up to
        # the 3 bp of core the second wrapper displaces and drift.
        assert abs(float(str(sum_rule["residual_pp_yr"]))) < 0.15

    # The hostile re-runs are read as differences against the primary panel.
    hostile = _mapping(result.diagnostics["hostile_reruns"])
    assert {
        "carry_cost_1pp",
        "carry_cost_2pp",
        "carry_loading_0681",
        "carry_shifted_one_month",
    } <= set(hostile)
    stack = _mapping(_mapping(_mapping(hostile["carry_cost_2pp"])["arms"])["trend30_carrystack10"])
    # A 2 pp/yr haircut on 0.10 of carry notional moves the paired gap by about -0.20.
    assert float(str(stack["change_vs_reference_pp_yr"])) == pytest.approx(-0.20, abs=0.02)
    loading = _mapping(
        _mapping(_mapping(hostile["carry_loading_0681"])["arms"])["carry30_no_trend"]
    )
    assert str(loading["status_vs_cheap"]) in {"exploratory", "unresolved", "rejected"}

    gaps = {e.name for e in result.estimates if e.name.startswith("arithmetic_gap[")}
    floors = {
        e.name.replace("minimum_detectable_effect[", "arithmetic_gap[")
        for e in result.estimates
        if e.name.startswith("minimum_detectable_effect[")
    }
    assert gaps and gaps == floors
    tables = result.diagnostics["markdown_tables"]
    assert isinstance(tables, str)
    for name in arms:
        assert f"`{name}`" in tables
    assert "Carry components" in tables
    assert "1974-02" in str(result.diagnostics["freeze_note"])
    assert isinstance(result.diagnostics["carry_components_primary"], Mapping)
    assert len(ledger.read()) >= 2
