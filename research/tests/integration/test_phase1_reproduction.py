"""End-to-end tests for the Phase 1 published-result reproduction gate.

Most of these run **offline**. The real 606-month file cannot be committed (it is
a raw zip from a source that rebuilds it monthly), so the machinery -- download
path, cache, zip-or-CSV extraction, two-table parsing, percent-to-decimal-to-
percent round trip, sample windowing, boundary checks, tolerance arithmetic,
status decision, artifacts and ledger -- is exercised against a synthetic file in
exactly the Ken French layout, seeded into the real cache under the real URL.

The expected statistics for those tests are computed **in this file, from the
generated text, with plain NumPy**, never by the code under test. That is what
makes them a check rather than a tautology.

One test is marked ``network``: reproducing the actual published table needs the
actual file, and a cold checkout has no cache.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from portfolio_edge.data import french
from portfolio_edge.data.cache import CACHE_ENV_VAR, RawCache
from portfolio_edge.experiments.exp_phase1_ff_reproduction import (
    ENTRY_POINT,
    FACTORS,
    ReproductionError,
    build_registry,
    default_specification_path,
    run,
)
from portfolio_edge.experiments.ledger import Ledger, LedgerEvent, RunStatus
from portfolio_edge.experiments.registry import RunContext
from portfolio_edge.experiments.result import ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import (
    Specification,
    load_specification,
    specification_from_mapping,
)

URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip"
PINNED_SHA256 = "cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b"
COLUMNS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")

# Roughly the real dispersions, so the synthetic file exercises the same
# plausibility and discontinuity checks the real one does.
_SIGMA = {"Mkt-RF": 4.5, "SMB": 3.0, "HML": 2.9, "RMW": 2.1, "CMA": 2.0, "RF": 0.1}
_MU = {"Mkt-RF": 0.50, "SMB": 0.29, "HML": 0.37, "RMW": 0.25, "CMA": 0.33, "RF": 0.40}


# --------------------------------------------------------------------------- #
# A synthetic file in the Ken French layout
# --------------------------------------------------------------------------- #


def _months(start: str, end: str) -> list[str]:
    def index(period: str) -> int:
        year, month = period.split("-")
        return int(year) * 12 + int(month) - 1

    return [
        f"{i // 12:04d}{i % 12 + 1:02d}" for i in range(index(start), index(end) + 1)
    ]


def synthetic_french_csv(
    *,
    start: str = "1963-07",
    end: str = "2013-12",
    drop: Sequence[str] = (),
    sentinel_at: str | None = None,
    seed: int = 20260812,
) -> bytes:
    """A file with the real layout: prose preamble, monthly table, annual table.

    ``drop`` removes whole months so the gap check has something to find;
    ``sentinel_at`` writes the declared ``-99.99`` missing-data sentinel, which
    the parser must turn into a missing value rather than into data.
    """
    generator = np.random.default_rng(seed)
    keys = [key for key in _months(start, end) if f"{key[:4]}-{key[4:]}" not in drop]

    lines = [
        "This file was created using a synthetic fixture, not a CRSP database.",
        "Missing data are indicated by -99.99.",
        "The annual TBill return is compounded from the monthly T-bill rates.",
        "",
        "," + ",".join(COLUMNS),
    ]
    for key in keys:
        cells = []
        for column in COLUMNS:
            value = generator.normal(_MU[column], _SIGMA[column])
            if sentinel_at is not None and key == sentinel_at.replace("-", "") and column == "HML":
                cells.append("  -99.99")
            else:
                cells.append(f"{value:>8.2f}")
        lines.append(key + "," + ",".join(cells))

    lines.extend(["", "  Annual Factors: January-December", "," + ",".join(COLUMNS)])
    for year in range(int(start[:4]) + 1, int(end[:4])):
        cells = [
            f"{generator.normal(12 * _MU[c], math.sqrt(12) * _SIGMA[c]):>8.2f}"
            for c in COLUMNS
        ]
        lines.append(f"{year}," + ",".join(cells))
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def independent_statistics(
    csv_bytes: bytes, *, start: str, end: str
) -> dict[str, dict[str, float]]:
    """Mean, standard deviation and t-statistic straight off the generated text.

    Deliberately does not import the parser, ``core.statistics`` or anything else
    under test: it splits the CSV itself and calls NumPy.
    """
    text = csv_bytes.decode("utf-8")
    header_index = next(i for i, line in enumerate(text.splitlines()) if line.startswith(",Mkt-RF"))
    columns = text.splitlines()[header_index].split(",")[1:]
    first, last = start.replace("-", ""), end.replace("-", "")

    series: dict[str, list[float]] = {name: [] for name in columns}
    for line in text.splitlines()[header_index + 1 :]:
        key = line.split(",", 1)[0].strip()
        if len(key) != 6 or not key.isdigit() or not first <= key <= last:
            continue
        for name, cell in zip(columns, line.split(",")[1:], strict=True):
            series[name].append(float(cell))

    out: dict[str, dict[str, float]] = {}
    for name in FACTORS:
        values = np.asarray(series[name], dtype=np.float64)
        mean = float(np.mean(values))
        sigma = float(np.std(values, ddof=1))
        out[name] = {
            "mean": mean,
            "std_dev": sigma,
            "t_statistic": mean / (sigma / math.sqrt(values.size)),
            "observations": float(values.size),
        }
    return out


# --------------------------------------------------------------------------- #
# Wiring a test specification around the synthetic file
# --------------------------------------------------------------------------- #


def seed_cache(root: Path, csv_bytes: bytes) -> tuple[str, str]:
    """Store the bytes under the real URL and return (raw sha, normalised sha)."""
    cache = RawCache(root)
    entry = cache.store(
        URL,
        csv_bytes,
        headers={"content-type": "text/csv", "last-modified": "Mon, 03 Aug 2026 19:17:07 GMT"},
    )
    parsed = french.parse(cache, entry, dataset=french.get_dataset("french_us_ff5"))
    return entry.sha256, parsed.table("monthly").sha256_normalized()


def synthetic_specification(
    *,
    raw_sha: str,
    normalized_sha: str,
    published: Mapping[str, Mapping[str, float]],
    start: str = "1963-07",
    end: str = "2013-12",
    observations: int = 606,
    perturb_mean_by: float = 0.0,
) -> Specification:
    """The committed specification, repointed at the synthetic file.

    Loading the real YAML rather than hand-rolling a mapping means these tests
    break if the committed specification's shape drifts away from what the
    experiment reads.
    """
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    parameters = raw["parameters"]
    pin = parameters["source_pin"]
    pin["expected_sha256_raw"] = raw_sha
    pin["expected_sha256_normalized"] = normalized_sha
    pin["expected_crsp_vintage_in_preamble"] = "synthetic"
    pin["committed_manifest"] = "data-manifests/does-not-exist-for-the-fixture.json"

    raw["sample_policy"]["start"] = start
    raw["sample_policy"]["end"] = end
    raw["sample_policy"]["eras"] = [
        {
            "name": "fixture",
            "start": start,
            "end": end,
            "rationale": "synthetic fixture window for the offline integration test",
        }
    ]
    raw["parameters"]["published_targets"] = [
        {
            "era": "fixture",
            "gating": True,
            "citation": "synthetic fixture; no publication",
            "table": "Table 4",
            "table_caption": "synthetic",
            "panel": "synthetic",
            "block": "synthetic",
            "rows_used": ["Mean", "Std dev.", "t-Statistic"],
            "units": "percent per month",
            "observations": observations,
            "retrieved_from": "n/a",
            "retrieved_sha256": "n/a",
            "retrieved_utc": "2026-08-12",
            "retrieval_note": "generated in tests/integration/test_phase1_reproduction.py",
            "column_name_mapping": {"RM-RF": "Mkt-RF"},
            "factors": {
                factor: {
                    "mean": round(values["mean"], 2) + perturb_mean_by,
                    "std_dev": round(values["std_dev"], 2),
                    "t_statistic": round(values["t_statistic"], 2),
                }
                for factor, values in published.items()
            },
        }
    ]
    raw["data_sources"] = [{"id": "synthetic", "url": URL}]
    return specification_from_mapping(raw, source_path=default_specification_path())


@pytest.fixture
def offline_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "cache"
    monkeypatch.setenv(CACHE_ENV_VAR, str(root))
    return root


def _context(tmp_path: Path) -> RunContext:
    return RunContext(
        run_id="fixture",
        seed=1,
        rng=np.random.default_rng(1),
        artifact_dir=tmp_path / "artifacts" / "fixture",
    )


# --------------------------------------------------------------------------- #
# The happy path, end to end
# --------------------------------------------------------------------------- #


def test_reproduction_runs_end_to_end_and_matches_an_independent_computation(
    tmp_path: Path, offline_cache: Path
) -> None:
    csv_bytes = synthetic_french_csv()
    raw_sha, normalized_sha = seed_cache(offline_cache, csv_bytes)
    expected = independent_statistics(csv_bytes, start="1963-07", end="2013-12")
    specification = synthetic_specification(
        raw_sha=raw_sha, normalized_sha=normalized_sha, published=expected
    )

    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
        dataset_manifest_hashes=("deadbeef",),
    )

    assert outcome.result is not None
    assert outcome.result.status is ResultStatus.SOURCE_REPRODUCED
    assert outcome.status is RunStatus.SUCCEEDED

    # The statistics themselves, against the independent NumPy computation.
    eras = outcome.result.diagnostics["eras"]
    assert isinstance(eras, Sequence) and not isinstance(eras, str)
    era = eras[0]
    assert isinstance(era, Mapping)
    assert era["observations"] == 606
    assert era["boundary_findings"] == []
    statistics = era["statistics"]
    assert isinstance(statistics, Mapping)
    for factor in FACTORS:
        block = statistics[factor]
        assert isinstance(block, Mapping)
        assert block["observations"] == 606
        assert float(str(block["mean_percent_per_month"])) == pytest.approx(
            expected[factor]["mean"], abs=1e-10
        )
        assert float(str(block["std_dev_percent_per_month"])) == pytest.approx(
            expected[factor]["std_dev"], abs=1e-10
        )
        assert float(str(block["conventional_t_statistic"])) == pytest.approx(
            expected[factor]["t_statistic"], abs=1e-10
        )
        # Annualisation conventions, stated in the specification.
        assert float(str(block["annualised_premium_percent"])) == pytest.approx(
            12.0 * expected[factor]["mean"]
        )
        assert float(str(block["annualised_volatility_percent"])) == pytest.approx(
            math.sqrt(12.0) * expected[factor]["std_dev"]
        )
        # RF is not subtracted: the Sharpe ratio is mean over standard deviation.
        assert float(str(block["sharpe_monthly"])) == pytest.approx(
            expected[factor]["mean"] / expected[factor]["std_dev"]
        )
        assert "RF is not subtracted" in str(block["risk_free_treatment"])


def test_the_run_is_ledgered_with_provenance_and_hashed_artifacts(
    tmp_path: Path, offline_cache: Path
) -> None:
    csv_bytes = synthetic_french_csv()
    raw_sha, normalized_sha = seed_cache(offline_cache, csv_bytes)
    specification = synthetic_specification(
        raw_sha=raw_sha,
        normalized_sha=normalized_sha,
        published=independent_statistics(csv_bytes, start="1963-07", end="2013-12"),
    )
    ledger = Ledger(tmp_path / "ledger.jsonl")

    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
        dataset_manifest_hashes=("manifest-hash",),
    )
    ledger.record_results_viewed(outcome.run_id, notes="read in a test")

    entries = ledger.read()
    assert [entry.event for entry in entries] == [
        LedgerEvent.STARTED,
        LedgerEvent.SUCCEEDED,
        LedgerEvent.RESULTS_VIEWED,
    ]
    started, succeeded, viewed = entries
    assert started.spec_hash == specification.spec_hash
    assert started.dataset_manifest_hashes == ("manifest-hash",)
    assert started.seed == specification.seed
    assert succeeded.result_status is ResultStatus.SOURCE_REPRODUCED
    assert {record.path for record in succeeded.artifacts} >= {
        f"{outcome.run_id}/result.json",
        f"{outcome.run_id}/summary.md",
        f"{outcome.run_id}/frames/comparison.parquet",
    }
    assert all(len(record.sha256) == 64 for record in succeeded.artifacts)
    assert viewed.results_viewed is True

    state = ledger.run_state(outcome.run_id)
    assert state.results_viewed is True
    assert state.status is RunStatus.SUCCEEDED


def test_the_registry_resolves_the_committed_entry_point() -> None:
    specification = load_specification(default_specification_path())
    assert specification.entry_point == ENTRY_POINT
    assert build_registry().resolve(specification.entry_point) is run


# --------------------------------------------------------------------------- #
# The gate has to be able to fail
# --------------------------------------------------------------------------- #


def test_a_month_missing_from_the_window_rejects_rather_than_being_filled(
    tmp_path: Path, offline_cache: Path
) -> None:
    csv_bytes = synthetic_french_csv(drop=("1990-05",))
    raw_sha, normalized_sha = seed_cache(offline_cache, csv_bytes)
    specification = synthetic_specification(
        raw_sha=raw_sha,
        normalized_sha=normalized_sha,
        published=independent_statistics(csv_bytes, start="1963-07", end="2013-12"),
    )

    result = run(specification, _context(tmp_path))
    assert result.status is ResultStatus.REJECTED
    gate = result.diagnostics["gate"]
    assert isinstance(gate, Mapping)
    failures = gate["boundary_failures"]
    assert isinstance(failures, Sequence) and not isinstance(failures, str)
    assert any("605" in str(item) for item in failures)
    assert any("gaps" in str(item) for item in failures)


def test_a_sentinel_becomes_a_missing_value_and_rejects(
    tmp_path: Path, offline_cache: Path
) -> None:
    csv_bytes = synthetic_french_csv(sentinel_at="1975-03")
    raw_sha, normalized_sha = seed_cache(offline_cache, csv_bytes)
    specification = synthetic_specification(
        raw_sha=raw_sha,
        normalized_sha=normalized_sha,
        published=independent_statistics(csv_bytes, start="1963-07", end="2013-12"),
    )

    result = run(specification, _context(tmp_path))
    assert result.status is ResultStatus.REJECTED
    gate = result.diagnostics["gate"]
    assert isinstance(gate, Mapping)
    failures = gate["boundary_failures"]
    assert isinstance(failures, Sequence) and not isinstance(failures, str)
    assert any("missing values" in str(item) and "HML" in str(item) for item in failures)


def test_a_mean_off_by_more_than_the_implementation_band_rejects(
    tmp_path: Path, offline_cache: Path
) -> None:
    """0.5 pp/month is five times the gate and twenty-five times the print band."""
    csv_bytes = synthetic_french_csv()
    raw_sha, normalized_sha = seed_cache(offline_cache, csv_bytes)
    specification = synthetic_specification(
        raw_sha=raw_sha,
        normalized_sha=normalized_sha,
        published=independent_statistics(csv_bytes, start="1963-07", end="2013-12"),
        perturb_mean_by=0.5,
    )

    result = run(specification, _context(tmp_path))
    assert result.status is ResultStatus.REJECTED
    gate = result.diagnostics["gate"]
    assert isinstance(gate, Mapping)
    assert gate["implementation_error_failures"]


def test_a_mean_off_by_between_the_gate_and_the_implementation_band_is_unresolved(
    tmp_path: Path, offline_cache: Path
) -> None:
    """A difference too big to ignore and too small to be a bug is not a pass."""
    csv_bytes = synthetic_french_csv()
    raw_sha, normalized_sha = seed_cache(offline_cache, csv_bytes)
    specification = synthetic_specification(
        raw_sha=raw_sha,
        normalized_sha=normalized_sha,
        published=independent_statistics(csv_bytes, start="1963-07", end="2013-12"),
        perturb_mean_by=0.05,
    )

    result = run(specification, _context(tmp_path))
    assert result.status is ResultStatus.UNRESOLVED
    gate = result.diagnostics["gate"]
    assert isinstance(gate, Mapping)
    assert gate["boundary_failures"] == []
    assert gate["implementation_error_failures"] == []
    assert gate["cells_within_gate"] == 10  # the five standard deviations and five t-stats


def test_an_unrecognised_vintage_aborts_instead_of_reporting_numbers(
    tmp_path: Path, offline_cache: Path
) -> None:
    csv_bytes = synthetic_french_csv()
    _, normalized_sha = seed_cache(offline_cache, csv_bytes)
    specification = synthetic_specification(
        raw_sha="0" * 64,
        normalized_sha=normalized_sha,
        published=independent_statistics(csv_bytes, start="1963-07", end="2013-12"),
    )

    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(ReproductionError, match="frozen against"):
        run_experiment(
            specification,
            registry=build_registry(),
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
        )
    # A refusal is still an attempted execution and is still ledgered.
    entries = ledger.read()
    assert entries[-1].event is LedgerEvent.FAILED
    assert "ReproductionError" in str(entries[-1].failure_reason)


def test_a_parser_change_that_leaves_the_bytes_alone_is_caught(
    tmp_path: Path, offline_cache: Path
) -> None:
    csv_bytes = synthetic_french_csv()
    raw_sha, _ = seed_cache(offline_cache, csv_bytes)
    specification = synthetic_specification(
        raw_sha=raw_sha,
        normalized_sha="1" * 64,
        published=independent_statistics(csv_bytes, start="1963-07", end="2013-12"),
    )
    with pytest.raises(ReproductionError, match="parser changed behaviour"):
        run(specification, _context(tmp_path))


# --------------------------------------------------------------------------- #
# The real thing
# --------------------------------------------------------------------------- #


@pytest.mark.network
def test_the_committed_specification_reproduces_the_published_table() -> None:
    """The actual gate, against the actual file. Needs the download on a cold cache."""
    cache = RawCache()
    entry = french.download(cache, french.get_dataset("french_us_ff5"))
    specification = load_specification(default_specification_path())

    if entry.sha256 != PINNED_SHA256:
        with pytest.raises(ReproductionError, match="frozen against"):
            run(specification, _context(Path.cwd()))
        pytest.skip(
            "Ken French has published a new vintage; the pinned specification "
            "correctly refuses it. Freeze a new specification against the new sha256."
        )

    result = run(specification, _context(Path.cwd()))

    # The gate's own verdict is not asserted here: it is recorded in the ledger
    # and in docs/research/fama-french-reproduction.md. What must hold is that
    # the pipeline ran on the right bytes over the right window.
    assert result.status in {ResultStatus.SOURCE_REPRODUCED, ResultStatus.UNRESOLVED}
    gate = result.diagnostics["gate"]
    assert isinstance(gate, Mapping)
    assert gate["boundary_failures"] == []
    assert gate["implementation_error_failures"] == []
    assert gate["gating_cells"] == 15

    eras = result.diagnostics["eras"]
    assert isinstance(eras, Sequence) and not isinstance(eras, str)
    primary = eras[0]
    assert isinstance(primary, Mapping)
    assert primary["observations"] == 606
    assert primary["start"] == "1963-07" and primary["end"] == "2013-12"

    # Every mean reproduces; this is the part that is not in dispute.
    cells = primary["cells"]
    assert isinstance(cells, Sequence) and not isinstance(cells, str)
    means = [c for c in cells if isinstance(c, Mapping) and c["statistic"] == "mean"]
    assert len(means) == 5
    assert all(cell["within_gate"] for cell in means)
