"""End-to-end tests for Experiment 006, offline.

The real files cannot be committed, so the whole path -- cache, zip-or-CSV
extraction, two-table parsing, percent-to-decimal conversion, the hard sha256,
row-count and first-observation pins on three momentum files, the `Mom`/`WML`
rename, the coverage check, era windowing, the holdout clip, every regional
statistic, the cross-region alignment and joint bootstrap, the measured effective
sample size, the crash test, both multiple-testing families, the frozen rejection
rule, the artifacts and the ledger -- runs against synthetic files in exactly the
Ken French momentum layout, seeded into the real cache under the real URLs.

Expected values are computed **in this file, with plain NumPy, from the generated
text**, never by calling the code under test.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from portfolio_edge.data import french
from portfolio_edge.data.cache import CACHE_ENV_VAR, RawCache
from portfolio_edge.experiments.exp_006_regional_momentum import (
    ENTRY_POINT,
    NAMED_CRASH_YEAR,
    RegionalMomentumError,
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

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"

#: region -> (url, dataset id, column name, first month, monthly row count)
FILES: dict[str, tuple[str, str, str, str, int]] = {
    "us": (
        f"{BASE}/F-F_Momentum_Factor_CSV.zip",
        "french_us_momentum",
        "Mom",
        "1927-01",
        1194,
    ),
    "developed_ex_us": (
        f"{BASE}/Developed_ex_US_Mom_Factor_CSV.zip",
        "french_developed_ex_us_momentum",
        "WML",
        "1990-11",
        428,
    ),
    "emerging": (
        f"{BASE}/Emerging_MOM_Factor_CSV.zip",
        "french_emerging_momentum",
        "WML",
        "1990-01",
        438,
    ),
}

# Roughly momentum's real dispersion, so the synthetic files exercise the same
# plausibility and discontinuity checks the real ones do.
_MU = 0.55
_SIGMA = 4.5


def _month_keys(start: str, end: str) -> list[str]:
    def index(period: str) -> int:
        year, month = period.split("-")
        return int(year) * 12 + int(month) - 1

    return [f"{i // 12:04d}{i % 12 + 1:02d}" for i in range(index(start), index(end) + 1)]


def synthetic_momentum_csv(*, start: str, end: str, column: str, seed: int) -> bytes:
    """A file in the real momentum layout: preamble, monthly table, annual table."""
    generator = np.random.default_rng(seed)
    lines = [
        "This file was created using a synthetic fixture, not a Bloomberg database.",
        "",
        "Missing data are indicated by -99.99.",
        "",
        "",
        "",
        f",{column}",
    ]
    for key in _month_keys(start, end):
        lines.append(f"{key}    ,{generator.normal(_MU, _SIGMA):>8.2f}")
    lines.extend(["", "  Annual Factors: January-December", f",{column}"])
    for year in range(int(start[:4]) + 1, int(end[:4])):
        value = generator.normal(12 * _MU, math.sqrt(12) * _SIGMA)
        lines.append(f"{year}    ,{value:>8.2f}")
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def independent_window(
    csv_bytes: bytes, column: str, *, start: str, end: str
) -> np.ndarray:
    """The decimal series for one column over one window, read straight off the text."""
    lines = csv_bytes.decode("utf-8").splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith(f",{column}"))
    first, last = start.replace("-", ""), end.replace("-", "")
    out: list[float] = []
    for line in lines[header_index + 1 :]:
        key = line.split(",", 1)[0].strip()
        if len(key) != 6 or not key.isdigit() or not first <= key <= last:
            continue
        out.append(float(line.split(",")[1]) / 100.0)
    return np.asarray(out, dtype=np.float64)


def seed_cache(root: Path, url: str, dataset_id: str, csv_bytes: bytes) -> tuple[str, str]:
    """Store bytes under the real URL; return (raw sha256, normalised sha256)."""
    cache = RawCache(root)
    entry = cache.store(
        url,
        csv_bytes,
        headers={"content-type": "text/csv", "last-modified": "Thu, 30 Jul 2026 20:24:26 GMT"},
    )
    parsed = french.parse(cache, entry, dataset=french.get_dataset(dataset_id))
    return entry.sha256, parsed.table("monthly").sha256_normalized()


def synthetic_specification(
    pins: dict[str, tuple[str, str]], *, resamples: int = 100
) -> Specification:
    """The committed specification, repointed at the synthetic files.

    Loading the real YAML rather than hand-rolling a mapping means these tests
    break if the committed specification's shape drifts away from what the
    experiment reads.
    """
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    for entry in raw["parameters"]["source_pin"]["series"]:
        raw_hash, normalized = pins[entry["region"]]
        entry["expected_sha256_raw"] = raw_hash
        entry["expected_sha256_normalized"] = normalized
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
    payload: dict[str, Any] = {"bytes": {}, "pins": {}}
    for seed, (region, (url, dataset_id, column, start, _)) in enumerate(FILES.items()):
        csv_bytes = synthetic_momentum_csv(
            start=start, end="2026-06", column=column, seed=20260812 + seed
        )
        payload["bytes"][region] = csv_bytes
        payload["pins"][region] = seed_cache(offline_cache, url, dataset_id, csv_bytes)
    return payload


def _context(tmp_path: Path) -> RunContext:
    return RunContext(
        run_id="fixture",
        seed=20260812,
        rng=np.random.default_rng(20260812),
        artifact_dir=tmp_path / "artifacts" / "fixture",
    )


def diagnostics(result: ExperimentResult) -> Any:
    """Navigate the diagnostics as plain data.

    The diagnostics payload is deliberately ``JsonValue``: it is written to an
    artifact, so its type is "whatever JSON can hold". These tests assert its
    schema rather than declare it.
    """
    return result.diagnostics


def _regional(result: ExperimentResult) -> dict[str, Any]:
    return {
        f"{c['region']}/{c['era_role']}": c for c in diagnostics(result)["regional_cells"]
    }


def _pooled(result: ExperimentResult) -> dict[str, Any]:
    return {c["era_role"]: c for c in diagnostics(result)["pooled_cells"]}


# --------------------------------------------------------------------------- #
# The happy path
# --------------------------------------------------------------------------- #


def test_the_experiment_runs_and_matches_an_independent_computation(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    regional = _regional(result)
    assert len(regional) == 9, "1 factor x 3 regions x 3 era roles"
    assert {cell["factor"] for cell in diagnostics(result)["regional_cells"]} == {"UMD"}

    expected = independent_window(
        sources["bytes"]["emerging"], "WML", start="1994-01", end="2025-12"
    )
    cell = regional["emerging/full_post_publication"]
    assert cell["observations"] == expected.size == 384
    assert cell["annualised_premium_percent"] == pytest.approx(
        1200.0 * float(np.mean(expected))
    )
    assert cell["annualised_volatility_percent"] == pytest.approx(
        100.0 * math.sqrt(12.0) * float(np.std(expected, ddof=1))
    )

    first = regional["developed_ex_us/first_post_publication"]
    assert first["start"] == "1994-01" and first["end"] == "2003-12"
    assert first["observations"] == 120


def test_the_us_column_is_mom_and_the_international_columns_are_wml(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """The rename is the only reason a single-factor pool across three files works."""
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    by_region = {row["region"]: row for row in diagnostics(result)["sources"]}
    assert by_region["us"]["source_column"] == "Mom"
    assert by_region["developed_ex_us"]["source_column"] == "WML"
    assert by_region["emerging"]["source_column"] == "WML"
    assert {row["renamed_to"] for row in diagnostics(result)["sources"]} == {"UMD"}
    assert all(row["frequency"] == "monthly" for row in diagnostics(result)["sources"])
    assert all(
        row["gated_against_a_printed_table"] is False
        for row in diagnostics(result)["sources"]
    )


def test_the_pooled_premium_is_the_equal_weighted_composite_of_the_three_regions(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    columns = [
        independent_window(
            sources["bytes"][region], FILES[region][2], start="1994-01", end="2025-12"
        )
        for region in FILES
    ]
    composite = np.mean(np.column_stack(columns), axis=1)
    pooled = _pooled(result)["full_post_publication"]
    assert pooled["months"] == 384
    assert pooled["months_dropped_by_intersection"] == 0
    assert pooled["annualised_premium_percent"] == pytest.approx(
        1200.0 * float(np.mean(composite))
    )
    assert pooled["annualised_volatility_percent"] == pytest.approx(
        100.0 * math.sqrt(12.0) * float(np.std(composite, ddof=1))
    )
    assert pooled["weights"] == pytest.approx([1 / 3, 1 / 3, 1 / 3])


def test_the_measured_effective_sample_size_is_reported_for_every_pooled_cell(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """The decisive output of the experiment, checked independently."""
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    for key, cell in _pooled(result).items():
        sample = cell["effective_sample_size"]
        assert sample["naive_region_months_if_independent"] == 3 * cell["months"], key
        assert sample["effective_regions"] > 0.0, key
        assert sample["effective_region_months_iid"] == pytest.approx(
            cell["months"] * sample["effective_regions"]
        )
        intervals = {item["statistic"]: item for item in cell["panel_intervals"]}
        assert set(intervals) == {
            "effective_regions",
            "pooled_mde_one_sided_percent_per_year",
        }, key

    columns = [
        independent_window(
            sources["bytes"][region], FILES[region][2], start="1994-01", end="2025-12"
        )
        for region in FILES
    ]
    panel = np.column_stack(columns) * 100.0
    composite = np.mean(panel, axis=1)
    expected = float(np.mean(np.var(panel, axis=0, ddof=1))) / float(
        np.var(composite, ddof=1)
    )
    sample = _pooled(result)["full_post_publication"]["effective_sample_size"]
    assert sample["effective_regions"] == pytest.approx(expected)


def test_the_joint_and_the_invalid_independent_intervals_are_both_reported(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    for cell in diagnostics(result)["pooled_cells"]:
        schemes = {b["scheme"] for b in cell["bootstraps"]}
        assert "cross-region-joint" in schemes
        assert "per-region-independent-INVALID" in schemes
        assert len([b for b in cell["bootstraps"] if not b["valid"]]) == 1
    rows = diagnostics(result)["hostile_tests"]["independent_versus_joint_resampling"]["rows"]
    assert len(rows) == 3
    assert all(row["narrowing_factor"] is not None for row in rows)


def test_the_crash_test_names_2009_in_advance_and_reports_every_component(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """The momentum-specific test must be reported whatever it finds."""
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    rows = diagnostics(result)["hostile_tests"]["do_the_regions_crash_together"]["rows"]
    assert len(rows) == 3
    for row in rows:
        assert row["named_crash_year_from_daniel_moskowitz"]["year"] == NAMED_CRASH_YEAR
        assert set(row["worst_calendar_year_by_region"]) == set(FILES)
        assert isinstance(row["regions_crash_together"], bool)
        assert len(row["worst_pooled_months"]) == 10
        assert row["tail_correlation_null"]["n_synthetic_panels"] == 200
        # The synthetic panels are zero-mean noise with the measured covariance,
        # so the null must reproduce the measured all-month correlation closely.
        assert row["tail_correlation_null"]["synthetic_mean_all_month_correlation"] == (
            pytest.approx(row["mean_pairwise_correlation_all_months"], abs=0.08)
        )
        # The composite is the sum of the regions, so selecting on its worst
        # decile conditions on a collider and pushes the within-tail sample
        # correlation DOWN. The null must therefore sit BELOW the unconditional
        # figure, which is why the measured tail correlation is uninterpretable
        # without it.
        assert (
            row["tail_correlation_null"]["synthetic_mean_tail_correlation"]
            < row["mean_pairwise_correlation_all_months"]
        )
        # The own-decile rate conditions on nothing and is the cleaner reading.
        assert row["all_regions_in_own_worst_decile_rate_if_independent"] == (
            pytest.approx(0.001)
        )
        assert 0.0 <= row["all_regions_in_own_worst_decile_rate"] <= 1.0

    full = next(row for row in rows if row["cell"].endswith("umd_full_post_publication"))
    for region, rate in full["unconditional_monthly_negative_rate_by_region"].items():
        assert 0.0 <= rate <= 1.0, region


def test_the_cost_schedule_is_a_function_of_turnover_and_names_no_long_only_figure(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """The error this block exists to prevent: one cost number attached to momentum."""
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    cost = diagnostics(result)["cost_sensitivity"]
    schedule = cost["schedule"]
    assert len(schedule) == 9
    for row in schedule:
        turnover = row["one_sided_monthly_turnover_percent"]
        assert row["cost_percent_per_year_at_k_1_0"] == pytest.approx(
            12.0 * 1.0 * turnover / 100.0
        )
        assert row["cost_percent_per_year_at_k_1_7"] == pytest.approx(
            12.0 * 1.7 * turnover / 100.0
        )
        assert row["inside_retail_implementability_limit"] is (turnover <= 50.0)
    assert cost["academic_long_short_factor"]["one_sided_monthly_turnover_percent"] == [
        27.5,
        91.5,
    ]
    assert cost["long_only_implementation"]["one_sided_monthly_turnover_percent"] is None
    assert "order of magnitude" in cost["long_only_implementation"]["why_none"]


def test_the_falsifier_is_applied_to_the_full_post_publication_cell_only(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    verdicts = diagnostics(result)["verdicts"]
    assert len(verdicts) == 1
    verdict = verdicts[0]
    assert verdict["factor"] == "UMD"
    assert verdict["status"] in {status.value for status in ResultStatus}
    assert result.status.value == verdict["status"]
    clauses = " ".join(verdict["clauses_passed"] + verdict["clauses_failed"])
    for label in ("(a1)", "(a2)", "(a3)", "(a4)", "(a5)"):
        assert label in clauses
    if verdict["status"] == ResultStatus.UNRESOLVED.value:
        assert verdict["what_would_fire"]


def test_both_multiple_testing_families_are_reported_separately(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    families = {family["family"]: family for family in diagnostics(result)["inference"]}
    assert set(families) == {"regional_cells", "pooled_cells"}
    assert families["regional_cells"]["family_size"] == 9
    assert families["pooled_cells"]["family_size"] == 3
    for family in families.values():
        for cell in family["cells"]:
            assert (
                cell["one_sided_p_uncorrected"]
                <= cell["benjamini_hochberg_adjusted_p"] + 1e-12
            )
            assert (
                cell["benjamini_hochberg_adjusted_p"]
                <= cell["holm_bonferroni_adjusted_p"] + 1e-12
            )


def test_the_holdout_is_not_read_and_the_months_beyond_it_are_counted(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    policy = diagnostics(result)["sample_policy"]
    assert policy["end"] == "2025-12"
    assert policy["months_available_beyond_holdout"] == {
        "us": 6,
        "developed_ex_us": 6,
        "emerging": 6,
    }
    for cell in diagnostics(result)["regional_cells"]:
        assert cell["last_observation"] <= "2025-12"


def test_the_coverage_check_reads_the_data_and_records_the_head_room(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    coverage = diagnostics(result)["regional_coverage_check"]
    assert coverage["checked_against"] == "the loaded series, not this text"
    assert all(row["covered"] for row in coverage["rows"])
    head_room = {
        row["region"]: row["months_of_head_room"]
        for row in coverage["rows"]
        if row["era_start"] == "1994-01"
    }
    assert head_room["developed_ex_us"] == 38, "1990-11 to 1994-01"
    assert head_room["emerging"] == 48, "1990-01 to 1994-01"


def test_the_second_moment_is_reported_as_unmeasured_in_every_region(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """Ungated is weaker than a band of zero and must never read as agreement."""
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    status = diagnostics(result)["second_moment_status"]
    assert status["gated_against_a_printed_table"] == dict.fromkeys(FILES, False)
    assert "UNMEASURED" in status["statement"]
    for cell in diagnostics(result)["regional_cells"]:
        band = cell["second_moment_band"]
        assert band is None or band.get("measured") is False
    for cell in diagnostics(result)["pooled_cells"]:
        assert cell["sharpe_systematic_band_from_us_leg"] is None
        assert cell["mde_systematic_band_from_us_leg"] is None


def test_the_carhart_alternative_date_is_reported_beside_the_primary_era(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    alternative = diagnostics(result)["hostile_tests"][
        "carhart_alternative_publication_date"
    ]
    assert alternative["window"] == "1998-01..2025-12"
    assert alternative["months"] == 336
    columns = [
        independent_window(
            sources["bytes"][region], FILES[region][2], start="1998-01", end="2025-12"
        )
        for region in FILES
    ]
    composite = np.mean(np.column_stack(columns), axis=1)
    assert alternative["pooled_premium_percent_per_year"] == pytest.approx(
        1200.0 * float(np.mean(composite))
    )


# --------------------------------------------------------------------------- #
# Refusals
# --------------------------------------------------------------------------- #


def test_a_changed_source_vintage_aborts_rather_than_reporting_a_premium(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    pins = dict(sources["pins"])
    pins["emerging"] = ("0" * 64, pins["emerging"][1])
    with pytest.raises(RegionalMomentumError, match="new vintage"):
        run(synthetic_specification(pins), _context(tmp_path))


def test_a_changed_parser_aborts_rather_than_reporting_a_premium(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    pins = dict(sources["pins"])
    pins["us"] = (pins["us"][0], "0" * 64)
    with pytest.raises(RegionalMomentumError, match="parser changed behaviour"):
        run(synthetic_specification(pins), _context(tmp_path))


def test_a_region_that_starts_after_an_era_aborts_rather_than_truncating(
    tmp_path: Path, offline_cache: Path
) -> None:
    """A silently truncated regional window looks exactly like a shorter one."""
    pins: dict[str, tuple[str, str]] = {}
    for seed, (region, (url, dataset_id, column, start, _)) in enumerate(FILES.items()):
        begin = "1999-01" if region == "emerging" else start
        pins[region] = seed_cache(
            offline_cache,
            url,
            dataset_id,
            synthetic_momentum_csv(
                start=begin, end="2026-06", column=column, seed=20260812 + seed
            ),
        )
    specification = synthetic_specification(pins)
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    for entry in raw["parameters"]["source_pin"]["series"]:
        region = entry["region"]
        entry["expected_sha256_raw"], entry["expected_sha256_normalized"] = pins[region]
        entry["committed_manifest"] = "data-manifests/does-not-exist-for-the-fixture.json"
        if region == "emerging":
            entry["expected_first_observation"] = "1999-01"
            entry["expected_rows"] = 330
    raw["inference"]["resamples"] = 100
    specification = specification_from_mapping(raw, source_path=default_specification_path())
    with pytest.raises(RegionalMomentumError, match="silently truncated"):
        run(specification, _context(tmp_path))


def test_a_wrong_row_count_aborts(tmp_path: Path, sources: dict[str, Any]) -> None:
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    for entry in raw["parameters"]["source_pin"]["series"]:
        region = entry["region"]
        entry["expected_sha256_raw"], entry["expected_sha256_normalized"] = sources["pins"][
            region
        ]
        entry["committed_manifest"] = "data-manifests/does-not-exist-for-the-fixture.json"
        if region == "us":
            entry["expected_rows"] = 1
    raw["inference"]["resamples"] = 100
    specification = specification_from_mapping(raw, source_path=default_specification_path())
    with pytest.raises(RegionalMomentumError, match="not the pinned"):
        run(specification, _context(tmp_path))


# --------------------------------------------------------------------------- #
# Through the runner and the ledger
# --------------------------------------------------------------------------- #


def test_the_runner_writes_artifacts_and_a_ledger_entry(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        synthetic_specification(sources["pins"]),
        registry=build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
    )
    assert outcome.status is RunStatus.SUCCEEDED
    assert outcome.result is not None
    assert outcome.spec_hash == synthetic_specification(sources["pins"]).spec_hash

    written = {Path(record.path).name for record in outcome.artifacts}
    assert {"result.json", "summary.md", "manifest.json"} <= written

    entries = list(ledger.read())
    assert [entry.event for entry in entries] == [
        LedgerEvent.STARTED,
        LedgerEvent.SUCCEEDED,
    ]
    assert entries[-1].spec_hash == outcome.spec_hash
    assert entries[-1].experiment_family == "exp_006_regional_momentum"

    ledger.record_results_viewed(outcome.run_id, notes="fixture")
    assert list(ledger.read())[-1].results_viewed is True


def test_the_registry_resolves_the_committed_entry_point() -> None:
    registry = build_registry()
    assert registry.names() == (ENTRY_POINT,)
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    assert raw["entry_point"] == ENTRY_POINT


def test_the_summary_and_caveats_refuse_the_forbidden_claims(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    prose = " ".join([result.summary, *result.caveats]).lower()
    for forbidden in (" works", "optimal", "validated", "guarantee"):
        assert forbidden not in prose
    assert "gross" in prose
    assert "unmeasured" in prose
    assert "not investable" in prose
    for estimate in result.estimates:
        assert estimate.interval is not None or estimate.uncertainty_unavailable_reason
