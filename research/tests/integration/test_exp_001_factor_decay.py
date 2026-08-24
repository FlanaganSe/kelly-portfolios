"""End-to-end tests for Experiment 001, offline.

The real files cannot be committed, so the whole path -- cache, zip-or-CSV
extraction, two-table parsing, percent-to-decimal conversion, the hard sha256
pin, era windowing, the holdout clip, every statistic, the multiple-testing
correction, the frozen rejection rule, the artifacts and the ledger -- runs
against synthetic files in exactly the Ken French layout, seeded into the real
cache under the real URLs.

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
from portfolio_edge.experiments.exp_001_factor_decay import (
    ENTRY_POINT,
    FactorDecayError,
    build_registry,
    default_specification_path,
    run,
)
from portfolio_edge.experiments.ledger import Ledger, LedgerEvent, RunStatus
from portfolio_edge.experiments.registry import RunContext
from portfolio_edge.experiments.result import ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import (
    Specification,
    specification_from_mapping,
)

FF5_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_5_Factors_2x3_CSV.zip"
)
MOM_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip"
)
FF5_COLUMNS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")

# Roughly the real dispersions, so the synthetic files exercise the same
# plausibility and discontinuity checks the real ones do.
_SIGMA = {"Mkt-RF": 4.5, "SMB": 3.0, "HML": 2.9, "RMW": 2.1, "CMA": 2.0, "RF": 0.1, "Mom": 4.2}
_MU = {"Mkt-RF": 0.50, "SMB": 0.29, "HML": 0.37, "RMW": 0.25, "CMA": 0.33, "RF": 0.40, "Mom": 0.65}


def _month_keys(start: str, end: str) -> list[str]:
    def index(period: str) -> int:
        year, month = period.split("-")
        return int(year) * 12 + int(month) - 1

    return [f"{i // 12:04d}{i % 12 + 1:02d}" for i in range(index(start), index(end) + 1)]


def synthetic_french_csv(
    *, columns: Sequence[str], start: str, end: str, seed: int
) -> bytes:
    """A file in the real layout: prose preamble, monthly table, annual table."""
    generator = np.random.default_rng(seed)
    keys = _month_keys(start, end)
    lines = [
        "This file was created using a synthetic fixture, not a CRSP database.",
        "Missing data are indicated by -99.99.",
        "",
        "," + ",".join(columns),
    ]
    for key in keys:
        cells = [f"{generator.normal(_MU[c], _SIGMA[c]):>8.2f}" for c in columns]
        lines.append(key + "," + ",".join(cells))
    lines.extend(["", "  Annual Factors: January-December", "," + ",".join(columns)])
    for year in range(int(start[:4]) + 1, int(end[:4])):
        cells = [
            f"{generator.normal(12 * _MU[c], math.sqrt(12) * _SIGMA[c]):>8.2f}" for c in columns
        ]
        lines.append(f"{year}," + ",".join(cells))
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def independent_window(
    csv_bytes: bytes, column: str, *, start: str, end: str
) -> np.ndarray:
    """The decimal series for one column over one window, read straight off the text."""
    text = csv_bytes.decode("utf-8")
    lines = text.splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith(","))
    names = lines[header_index].split(",")[1:]
    position = names.index(column)
    first, last = start.replace("-", ""), end.replace("-", "")
    out: list[float] = []
    for line in lines[header_index + 1 :]:
        key = line.split(",", 1)[0].strip()
        if len(key) != 6 or not key.isdigit() or not first <= key <= last:
            continue
        out.append(float(line.split(",")[1:][position]) / 100.0)
    return np.asarray(out, dtype=np.float64)


def seed_cache(root: Path, url: str, dataset_id: str, csv_bytes: bytes) -> tuple[str, str]:
    """Store bytes under the real URL; return (raw sha256, normalised sha256)."""
    cache = RawCache(root)
    entry = cache.store(
        url,
        csv_bytes,
        headers={"content-type": "text/csv", "last-modified": "Mon, 03 Aug 2026 19:17:07 GMT"},
    )
    parsed = french.parse(cache, entry, dataset=french.get_dataset(dataset_id))
    return entry.sha256, parsed.table("monthly").sha256_normalized()


def synthetic_specification(
    *,
    ff5: tuple[str, str],
    momentum: tuple[str, str],
    resamples: int = 100,
) -> Specification:
    """The committed specification, repointed at the synthetic files.

    Loading the real YAML rather than hand-rolling a mapping means these tests
    break if the committed specification's shape drifts away from what the
    experiment reads.
    """
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    series = raw["parameters"]["source_pin"]["series"]
    series[0]["expected_sha256_raw"], series[0]["expected_sha256_normalized"] = ff5
    series[0]["committed_manifest"] = "data-manifests/does-not-exist-for-the-fixture.json"
    series[1]["expected_sha256_raw"], series[1]["expected_sha256_normalized"] = momentum
    series[1]["committed_manifest"] = "data-manifests/does-not-exist-for-the-fixture.json"
    raw["inference"]["resamples"] = resamples
    return specification_from_mapping(raw, source_path=default_specification_path())


@pytest.fixture
def offline_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "cache"
    monkeypatch.setenv(CACHE_ENV_VAR, str(root))
    return root


@pytest.fixture
def sources(offline_cache: Path) -> dict[str, Any]:
    ff5_bytes = synthetic_french_csv(
        columns=FF5_COLUMNS, start="1963-07", end="2026-06", seed=20260812
    )
    mom_bytes = synthetic_french_csv(
        columns=("Mom",), start="1927-01", end="2026-06", seed=20260813
    )
    return {
        "ff5_bytes": ff5_bytes,
        "mom_bytes": mom_bytes,
        "ff5": seed_cache(offline_cache, FF5_URL, "french_us_ff5", ff5_bytes),
        "momentum": seed_cache(offline_cache, MOM_URL, "french_us_momentum", mom_bytes),
    }


def _context(tmp_path: Path) -> RunContext:
    return RunContext(
        run_id="fixture",
        seed=20260811,
        rng=np.random.default_rng(20260811),
        artifact_dir=tmp_path / "artifacts" / "fixture",
    )


def diagnostics(result: ExperimentResult) -> Any:
    """Navigate the diagnostics as plain data.

    The diagnostics payload is deliberately ``JsonValue``: it is written to an
    artifact, so its type is "whatever JSON can hold". These tests assert its
    schema rather than declare it, and the cast keeps that assertion readable.
    """
    return result.diagnostics


def _cells(result: ExperimentResult) -> dict[str, Any]:
    return {f"{c['factor']}/{c['era_role']}": c for c in diagnostics(result)["cells"]}


# --------------------------------------------------------------------------- #
# The happy path
# --------------------------------------------------------------------------- #


def test_the_experiment_runs_and_matches_an_independent_computation(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(
        ff5=sources["ff5"], momentum=sources["momentum"]
    )
    result = run(specification, _context(tmp_path))
    cells = _cells(result)

    assert len(cells) == 20, "the predeclared family is 4 factors x 5 era roles"

    expected = independent_window(
        sources["ff5_bytes"], "HML", start="1994-01", end="2025-12"
    )
    cell = cells["HML/full_post_publication"]
    assert cell["observations"] == expected.size == 384
    assert cell["mean_percent_per_month"] == pytest.approx(100.0 * float(np.mean(expected)))
    assert cell["annualised_premium_percent"] == pytest.approx(
        1200.0 * float(np.mean(expected))
    )
    assert cell["annualised_volatility_percent"] == pytest.approx(
        100.0 * math.sqrt(12.0) * float(np.std(expected, ddof=1))
    )

    umd = cells["UMD/original_sample"]
    momentum = independent_window(sources["mom_bytes"], "Mom", start="1965-01", end="1989-12")
    assert umd["observations"] == momentum.size == 300
    assert umd["mean_percent_per_month"] == pytest.approx(100.0 * float(np.mean(momentum)))


def test_the_holdout_is_never_read(tmp_path: Path, sources: dict[str, Any]) -> None:
    """The files run to 2026-06; the frozen sample policy ends 2025-12."""
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    for cell in diagnostics(result)["cells"]:
        assert cell["last_observation"] <= "2025-12"
    for cell in diagnostics(result)["alternative_publication_dates"]:
        assert cell["last_observation"] <= "2025-12"
    withheld = diagnostics(result)["sample_policy"]["months_available_beyond_holdout"]
    assert withheld["HML"] == 6 and withheld["UMD"] == 6


def test_umd_reaches_back_to_1927_and_the_five_factors_do_not(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """Which is exactly why a common period exists: the samples do not align."""
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    cells = _cells(result)
    assert cells["UMD/original_sample"]["first_observation"] == "1965-01"
    assert cells["RMW/original_sample"]["first_observation"] == "1963-07"
    for factor in ("HML", "UMD", "RMW", "CMA"):
        assert cells[f"{factor}/common_period"]["observations"] == 144


def test_every_cell_reports_a_minimum_detectable_effect_and_an_interval(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    for cell in diagnostics(result)["cells"]:
        assert cell["mde_one_sided_percent_per_year"] > 0.0
        assert cell["mde_two_sided_percent_per_year"] > cell["mde_one_sided_percent_per_year"]
        assert 0.0 < cell["power_at_materiality"] < 1.0
        sources_used = {b["block_length_source"] for b in cell["bootstraps"]}
        assert sources_used == {"frozen", "predeclared-neighbour", "politis-white-automatic"}
        frozen = [
            b
            for b in cell["bootstraps"]
            if b["statistic"] == "annualised_premium_percent"
            and b["block_length_source"] == "frozen"
        ]
        assert len(frozen) == 1 and frozen[0]["block_length"] == 12.0


def test_hml_and_rmw_carry_the_phase_1_band_and_cma_does_not(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    cells = _cells(result)
    hml = cells["HML/full_post_publication"]["second_moment_band"]
    rmw = cells["RMW/full_post_publication"]["second_moment_band"]
    cma = cells["CMA/full_post_publication"]["second_moment_band"]
    umd = cells["UMD/full_post_publication"]["second_moment_band"]
    assert hml["relative_band_on_volatility"] == pytest.approx(0.0303)
    assert rmw["relative_band_on_volatility"] == pytest.approx(0.0509)
    assert cma is None
    assert umd["measured"] is False
    band = diagnostics(result)["second_moment_band_effects"]
    assert "CANNOT flip" in str(band["description"])


def test_the_correction_covers_the_whole_family_and_reports_both_readings(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    grid = diagnostics(result)["grid_inference"]
    assert grid["family_size"] == 20
    assert grid["alpha"] == 0.10
    for row in grid["cells"]:
        assert row["benjamini_hochberg_adjusted_p"] >= row["one_sided_p_uncorrected"] - 1e-12
        assert row["holm_bonferroni_adjusted_p"] >= row["benjamini_hochberg_adjusted_p"] - 1e-12


def test_correlations_are_computed_only_over_the_common_period(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    correlations = diagnostics(result)["correlations_common_period"]
    assert correlations["window"] == "2014-01..2025-12"
    assert correlations["observations"] == 144
    matrix = np.asarray(correlations["matrix"], dtype=np.float64)
    assert matrix.shape == (4, 4)
    assert np.allclose(np.diag(matrix), 1.0)
    assert np.allclose(matrix, matrix.T)


def test_the_result_carries_the_gross_and_not_investable_caveat(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    joined = " ".join(result.caveats)
    assert "UPPER BOUND" in joined
    assert "UNRESOLVED, not passed" in joined
    assert "cannot implement most of them at all" in joined
    assert "no tradable form" in joined
    assert result.status in {
        ResultStatus.EXPLORATORY,
        ResultStatus.UNRESOLVED,
        ResultStatus.REJECTED,
    }
    assert "works" not in result.summary.lower()


def test_the_equal_weighted_hostile_test_is_recorded_as_not_run_with_its_reason(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    entry = diagnostics(result)["hostile_tests"]["equal_weighted_source_portfolios"]
    assert entry["run"] is False
    assert "distributes no equal-weighted variant" in str(entry["reason"])


def test_shifted_boundaries_refuse_to_read_past_the_holdout(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    result = run(specification, _context(tmp_path))
    rows = diagnostics(result)["hostile_tests"]["shift_era_boundaries_24_months"]["rows"]
    forward = [
        row["shifted"]["+24"]
        for row in rows
        if row["cell"].endswith("full_post_publication")
    ]
    assert forward, "the full post-publication eras all end at the sample end"
    for entry in forward:
        assert "refused" in entry


# --------------------------------------------------------------------------- #
# The pin
# --------------------------------------------------------------------------- #


def test_an_unrecognised_vintage_aborts_instead_of_reporting_premia(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(
        ff5=("0" * 64, sources["ff5"][1]), momentum=sources["momentum"]
    )
    with pytest.raises(FactorDecayError, match="new vintage, not a corrupted download"):
        run(specification, _context(tmp_path))


def test_a_parser_change_that_leaves_the_bytes_alone_is_caught(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(
        ff5=sources["ff5"], momentum=(sources["momentum"][0], "0" * 64)
    )
    with pytest.raises(FactorDecayError, match="the parser changed behaviour"):
        run(specification, _context(tmp_path))


# --------------------------------------------------------------------------- #
# The ledger
# --------------------------------------------------------------------------- #


def test_the_run_is_ledgered_with_provenance_and_hashed_artifacts(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(ff5=sources["ff5"], momentum=sources["momentum"])
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
        dataset_manifest_hashes=("fixture-manifest-hash",),
    )
    assert outcome.status is RunStatus.SUCCEEDED
    assert outcome.seed == specification.seed

    entries = list(ledger.read())
    events = [entry.event for entry in entries]
    assert events == [LedgerEvent.STARTED, LedgerEvent.SUCCEEDED]
    succeeded = entries[-1]
    assert succeeded.spec_hash == specification.spec_hash
    assert succeeded.artifacts, "a successful run must record its artifacts"
    for record in succeeded.artifacts:
        path = tmp_path / "artifacts" / record.path
        assert path.is_file() and path.stat().st_size == record.size_bytes

    ledger.record_results_viewed(outcome.run_id)
    assert list(ledger.read())[-1].results_viewed is True


def test_the_registry_resolves_the_committed_entry_point() -> None:
    registry = build_registry()
    assert registry.names() == (ENTRY_POINT,)
    raw = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    assert raw["entry_point"] == ENTRY_POINT
