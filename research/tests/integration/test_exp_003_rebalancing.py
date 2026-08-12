"""End-to-end tests for Experiment 003, offline.

The real files cannot be committed, so the whole path -- cache, zip-or-CSV
extraction, two-table parsing, percent-to-decimal conversion, the hard sha256
pin, the ``Mkt-RF + RF`` reconstruction, the shared-risk-free check, the frozen
window, the five policies, the bootstrap, the frozen rejection rule, the
artifacts and the ledger -- runs against synthetic files in exactly the Ken
French layout, seeded into the real cache under the real URLs.

Expected values are computed **in this file, with plain NumPy, from the generated
text**, never by calling the code under test.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from portfolio_edge.data import french
from portfolio_edge.data.cache import CACHE_ENV_VAR, RawCache
from portfolio_edge.experiments.exp_003_rebalancing import (
    ENTRY_POINT,
    MONTHS_PER_YEAR,
    RebalancingError,
    build_registry,
    default_specification_path,
    load_panel,
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

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
URLS = {
    "french_us_ff5": BASE + "F-F_Research_Data_5_Factors_2x3_CSV.zip",
    "french_developed_ex_us_ff5": BASE + "Developed_ex_US_5_Factors_CSV.zip",
    "french_emerging_ff5": BASE + "Emerging_5_Factors_CSV.zip",
}
COLUMNS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
_SIGMA = {"Mkt-RF": 4.5, "SMB": 3.0, "HML": 2.9, "RMW": 2.1, "CMA": 2.0}
_MU = {"Mkt-RF": 0.55, "SMB": 0.20, "HML": 0.25, "RMW": 0.20, "CMA": 0.25}
START, END = "1990-07", "2026-06"


def _month_keys(start: str, end: str) -> list[str]:
    def index(period: str) -> int:
        year, month = period.split("-")
        return int(year) * 12 + int(month) - 1

    return [f"{i // 12:04d}{i % 12 + 1:02d}" for i in range(index(start), index(end) + 1)]


def synthetic_french_csv(*, seed: int, risk_free: Sequence[float]) -> bytes:
    """One region's file in the real layout, sharing the given US bill series.

    The shared ``RF`` column is the point: French subtracts the *same* US
    one-month bill from every region, and ``load_panel`` refuses the
    reconstruction if the three files disagree beyond their printing precision.
    """
    generator = np.random.default_rng(seed)
    keys = _month_keys(START, END)
    assert len(risk_free) == len(keys)
    lines = [
        "This file was created using a synthetic fixture, not a Bloomberg database.",
        "Missing data are indicated by -99.99.",
        "",
        "," + ",".join(COLUMNS),
    ]
    for key, rate in zip(keys, risk_free, strict=True):
        cells = [f"{generator.normal(_MU[c], _SIGMA[c]):>8.2f}" for c in COLUMNS[:-1]]
        lines.append(key + "," + ",".join([*cells, f"{rate:>8.2f}"]))
    lines.extend(["", "  Annual Factors: January-December", "," + ",".join(COLUMNS)])
    for year in range(int(START[:4]) + 1, int(END[:4])):
        cells = [
            f"{generator.normal(12 * _MU[c], math.sqrt(12) * _SIGMA[c]):>8.2f}"
            for c in COLUMNS[:-1]
        ]
        lines.append(f"{year}," + ",".join([*cells, "    4.00"]))
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def independent_total_returns(csv_bytes: bytes, *, start: str, end: str) -> np.ndarray:
    """``Mkt-RF + RF`` in decimal, read straight off the generated text."""
    lines = csv_bytes.decode("utf-8").splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith(","))
    names = lines[header_index].split(",")[1:]
    market, cash = names.index("Mkt-RF"), names.index("RF")
    first, last = start.replace("-", ""), end.replace("-", "")
    out: list[float] = []
    for line in lines[header_index + 1 :]:
        key = line.split(",", 1)[0].strip()
        if len(key) != 6 or not key.isdigit() or not first <= key <= last:
            continue
        cells = line.split(",")[1:]
        out.append((float(cells[market]) + float(cells[cash])) / 100.0)
    return np.asarray(out, dtype=np.float64)


def seed_cache(root: Path, dataset_id: str, csv_bytes: bytes) -> tuple[str, str]:
    """Store bytes under the real URL; return (raw sha256, normalised sha256)."""
    cache = RawCache(root)
    entry = cache.store(
        URLS[dataset_id],
        csv_bytes,
        headers={"content-type": "text/csv", "last-modified": "Thu, 30 Jul 2026 20:24:24 GMT"},
    )
    parsed = french.parse(cache, entry, dataset=french.get_dataset(dataset_id))
    return entry.sha256, parsed.table("monthly").sha256_normalized()


def synthetic_specification(
    hashes: dict[str, tuple[str, str]], *, resamples: int = 40
) -> Specification:
    """The committed specification, repointed at the synthetic files.

    Loading the real YAML rather than hand-rolling a mapping means these tests
    break if the committed specification's shape drifts away from what the
    experiment reads.
    """
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    for entry in raw["parameters"]["source_pin"]["tables"]:
        raw_hash, normalized_hash = hashes[str(entry["dataset_id"])]
        entry["expected_sha256_raw"] = raw_hash
        entry["expected_sha256_normalized"] = normalized_hash
        entry["committed_manifest"] = "data-manifests/does-not-exist-for-the-fixture.json"
    raw["inference"]["resamples"] = resamples
    return specification_from_mapping(raw, source_path=default_specification_path())


@pytest.fixture
def offline_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "cache"
    monkeypatch.setenv(CACHE_ENV_VAR, str(root))
    return root


@pytest.fixture
def sources(offline_cache: Path) -> dict[str, Any]:
    generator = np.random.default_rng(20260813)
    rates = np.round(np.abs(generator.normal(0.25, 0.15, size=len(_month_keys(START, END)))), 2)
    files = {
        dataset_id: synthetic_french_csv(seed=seed, risk_free=list(rates))
        for dataset_id, seed in (
            ("french_us_ff5", 1991),
            ("french_developed_ex_us_ff5", 1992),
            ("french_emerging_ff5", 1993),
        )
    }
    return {
        "bytes": files,
        "hashes": {
            dataset_id: seed_cache(offline_cache, dataset_id, payload)
            for dataset_id, payload in files.items()
        },
    }


def _context(tmp_path: Path) -> RunContext:
    return RunContext(
        run_id="fixture",
        seed=20260813,
        rng=np.random.default_rng(20260813),
        artifact_dir=tmp_path / "artifacts" / "fixture",
    )


def diagnostics(result: ExperimentResult) -> Any:
    """Navigate the diagnostics as plain data; the payload is deliberately JSON."""
    return result.diagnostics


# --------------------------------------------------------------------------- #
# The panel is the identity it claims to be
# --------------------------------------------------------------------------- #


def test_the_panel_is_mkt_rf_plus_rf_over_the_frozen_window(sources: dict[str, Any]) -> None:
    specification = synthetic_specification(sources["hashes"])
    panel = load_panel(specification)

    assert panel.months == 420
    assert panel.years == 35.0
    assert panel.periods[0] == "1991-01"
    assert panel.periods[-1] == "2025-12"
    assert panel.sleeves == ("us_equity", "developed_ex_us_equity", "emerging_equity")

    expected = {
        "us_equity": "french_us_ff5",
        "developed_ex_us_equity": "french_developed_ex_us_ff5",
        "emerging_equity": "french_emerging_ff5",
    }
    for sleeve, dataset_id in expected.items():
        independent = independent_total_returns(
            sources["bytes"][dataset_id], start="1991-01", end="2025-12"
        )
        assert panel.returns[:, panel.index_of(sleeve)] == pytest.approx(
            independent, rel=1e-12, abs=1e-15
        )


def test_a_disagreeing_risk_free_column_stops_the_reconstruction(
    offline_cache: Path,
) -> None:
    """The Mkt-RF + RF identity depends on one shared US bill. Prove it is checked."""
    generator = np.random.default_rng(4)
    keys = _month_keys(START, END)
    shared = np.round(np.abs(generator.normal(0.25, 0.15, size=len(keys))), 2)
    different = shared + 0.5
    hashes = {
        "french_us_ff5": seed_cache(
            offline_cache, "french_us_ff5", synthetic_french_csv(seed=1, risk_free=list(shared))
        ),
        "french_developed_ex_us_ff5": seed_cache(
            offline_cache,
            "french_developed_ex_us_ff5",
            synthetic_french_csv(seed=2, risk_free=list(different)),
        ),
        "french_emerging_ff5": seed_cache(
            offline_cache,
            "french_emerging_ff5",
            synthetic_french_csv(seed=3, risk_free=list(shared)),
        ),
    }
    with pytest.raises(RebalancingError, match="must not be combined"):
        load_panel(synthetic_specification(hashes))


def test_an_unrecognised_vintage_aborts_before_any_statistic(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    hashes = dict(sources["hashes"])
    hashes["french_emerging_ff5"] = ("0" * 64, hashes["french_emerging_ff5"][1])
    with pytest.raises(RebalancingError, match="new vintage, not a corrupted download"):
        run(synthetic_specification(hashes), _context(tmp_path))


# --------------------------------------------------------------------------- #
# The policy comparison
# --------------------------------------------------------------------------- #


@pytest.fixture
def result(tmp_path: Path, sources: dict[str, Any]) -> ExperimentResult:
    return run(synthetic_specification(sources["hashes"]), _context(tmp_path))


def test_buy_and_hold_matches_an_independent_computation(
    result: ExperimentResult, sources: dict[str, Any]
) -> None:
    """Recompute the benchmark's wealth path here, from the generated text."""
    panel = np.column_stack(
        [
            independent_total_returns(
                sources["bytes"][dataset_id], start="1991-01", end="2025-12"
            )
            for dataset_id in (
                "french_us_ff5",
                "french_developed_ex_us_ff5",
                "french_emerging_ff5",
            )
        ]
    )
    weights = np.array([0.60, 0.30, 0.10], dtype=np.float64)
    contribution = 0.05 / MONTHS_PER_YEAR

    values = weights.copy()
    for row in panel:
        wealth = float(np.sum(values))
        values = values + contribution * values / wealth
        values = values * (1.0 + row)
    expected = float(np.sum(values))

    gross = next(
        item
        for item in diagnostics(result)["policies"]
        if item["policy"] == "buy_and_hold" and item["cost_basis"] == CostBasis.GROSS.value
    )
    assert gross["terminal_wealth"] == pytest.approx(expected, rel=1e-12)
    assert gross["annual_transaction_cost_percent"] == 0.0
    assert gross["rebalance_count"] == 0


def test_every_policy_is_reported_on_every_cost_basis(result: ExperimentResult) -> None:
    reported = {
        (item["policy"], item["cost_basis"]) for item in diagnostics(result)["policies"]
    }
    policies = {
        "buy_and_hold",
        "annual_calendar",
        "monthly_calendar",
        "relative_threshold_25pct",
        "cash_flow_directed",
    }
    bases = {"gross", "net-optimistic", "net-pessimistic"}
    assert reported == {(p, b) for p in policies for b in bases}


def test_costs_only_ever_reduce_wealth(result: ExperimentResult) -> None:
    by_key = {
        (item["policy"], item["cost_basis"]): item for item in diagnostics(result)["policies"]
    }
    for policy in {key[0] for key in by_key}:
        gross = by_key[(policy, "gross")]["terminal_wealth"]
        optimistic = by_key[(policy, "net-optimistic")]["terminal_wealth"]
        pessimistic = by_key[(policy, "net-pessimistic")]["terminal_wealth"]
        assert pessimistic <= optimistic <= gross + 1e-12


def test_rebalancing_policies_hold_the_target_more_tightly_than_buy_and_hold(
    result: ExperimentResult,
) -> None:
    by_key = {
        (item["policy"], item["cost_basis"]): item for item in diagnostics(result)["policies"]
    }
    held = by_key[("buy_and_hold", "gross")]["max_weight_deviation_pp"]
    for policy in ("annual_calendar", "monthly_calendar", "relative_threshold_25pct"):
        assert by_key[(policy, "gross")]["max_weight_deviation_pp"] < held


def test_the_report_states_what_it_is_and_is_not(result: ExperimentResult) -> None:
    assert diagnostics(result)["pretax"] is True
    assert "PRETAX" in result.summary
    assert any("no constant tax haircut is" in caveat for caveat in result.caveats)
    assert any("DIAGNOSTICS" in caveat for caveat in result.caveats)
    statement = str(diagnostics(result)["diversification_return_statement"])
    assert "was NOT used as evidence" in statement
    assert (
        diagnostics(result)["investability_drag"]["applied_to_any_reported_return"] is False
    )
    for era in diagnostics(result)["eras"].values():
        assert era["IS_A_DIAGNOSTIC_NOT_AN_INDEPENDENT_OBSERVATION"] is True


def test_every_reported_estimate_carries_units_and_uncertainty(
    result: ExperimentResult,
) -> None:
    """Enforced by ``Estimate`` at construction; asserted so the intent is visible."""
    assert result.estimates
    for estimate in result.estimates:
        assert estimate.units.strip()
        assert estimate.interval is not None or estimate.uncertainty_unavailable_reason.strip()


def test_the_two_period_identity_check_runs_inside_the_experiment(
    result: ExperimentResult,
) -> None:
    assert diagnostics(result)["hostile_tests"]["two_period_identity"]["agrees"] is True


def test_zero_cash_flow_makes_the_directed_policy_the_benchmark(
    result: ExperimentResult,
) -> None:
    """The specification predicts this exactly; the hostile test must show it."""
    zero = diagnostics(result)["hostile_tests"]["zero_cash_flow"]
    assert zero["cash_flow_directed"] == pytest.approx(0.0, abs=1e-12)


# --------------------------------------------------------------------------- #
# The runner and the ledger
# --------------------------------------------------------------------------- #


def test_the_run_is_ledgered_with_artifacts(tmp_path: Path, sources: dict[str, Any]) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        synthetic_specification(sources["hashes"]),
        registry=build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
    )

    assert outcome.status is RunStatus.SUCCEEDED
    assert outcome.result is not None
    assert outcome.result.status in {
        ResultStatus.REJECTED,
        ResultStatus.UNRESOLVED,
        ResultStatus.WALK_FORWARD_TESTED,
    }
    assert outcome.artifacts

    entries = ledger.read()
    assert [entry.event for entry in entries] == [LedgerEvent.STARTED, LedgerEvent.SUCCEEDED]
    assert all(entry.run_kind.value == "confirmatory" for entry in entries)
    assert all(entry.consumes_final_holdout is False for entry in entries)
    assert entries[-1].seed == 20260813


def test_a_failed_run_is_ledgered_before_the_error_escapes(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    hashes = dict(sources["hashes"])
    hashes["french_us_ff5"] = ("f" * 64, hashes["french_us_ff5"][1])
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(RebalancingError):
        run_experiment(
            synthetic_specification(hashes),
            registry=build_registry(),
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
        )
    entries = ledger.read()
    assert [entry.event for entry in entries] == [LedgerEvent.STARTED, LedgerEvent.FAILED]
    assert entries[-1].failure_reason is not None


def test_the_entry_point_name_matches_the_committed_specification() -> None:
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    assert raw["entry_point"] == ENTRY_POINT
    assert ENTRY_POINT in build_registry()
