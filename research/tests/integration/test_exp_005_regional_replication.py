"""End-to-end tests for Experiment 005, offline.

The real files cannot be committed, so the whole path -- cache, zip-or-CSV
extraction, two-table parsing, percent-to-decimal conversion, the hard sha256
pin on three files, the regional coverage check, era windowing, the holdout clip,
every regional statistic, the cross-region alignment and joint bootstrap, the
measured effective sample size, both multiple-testing families, the frozen
rejection rule, the artifacts and the ledger -- runs against synthetic files in
exactly the Ken French layout, seeded into the real cache under the real URLs.

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
from portfolio_edge.experiments.exp_005_regional_replication import (
    ENTRY_POINT,
    RegionalReplicationError,
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
FILES = {
    "us": (f"{BASE}/F-F_Research_Data_5_Factors_2x3_CSV.zip", "french_us_ff5", "1963-07"),
    "developed_ex_us": (
        f"{BASE}/Developed_ex_US_5_Factors_CSV.zip",
        "french_developed_ex_us_ff5",
        "1990-07",
    ),
    "emerging": (f"{BASE}/Emerging_5_Factors_CSV.zip", "french_emerging_ff5", "1989-07"),
}
FF5_COLUMNS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")

# Roughly the real dispersions, so the synthetic files exercise the same
# plausibility and discontinuity checks the real ones do.
_SIGMA = {"Mkt-RF": 4.5, "SMB": 3.0, "HML": 2.9, "RMW": 2.1, "CMA": 2.0, "RF": 0.1}
_MU = {"Mkt-RF": 0.50, "SMB": 0.29, "HML": 0.37, "RMW": 0.25, "CMA": 0.33, "RF": 0.40}


def _month_keys(start: str, end: str) -> list[str]:
    def index(period: str) -> int:
        year, month = period.split("-")
        return int(year) * 12 + int(month) - 1

    return [f"{i // 12:04d}{i % 12 + 1:02d}" for i in range(index(start), index(end) + 1)]


def synthetic_french_csv(*, start: str, end: str, seed: int) -> bytes:
    """A file in the real layout: prose preamble, monthly table, annual table."""
    generator = np.random.default_rng(seed)
    lines = [
        "This file was created using a synthetic fixture, not a Bloomberg database.",
        "Missing data are indicated by -99.99.",
        "",
        "," + ",".join(FF5_COLUMNS),
    ]
    for key in _month_keys(start, end):
        cells = [f"{generator.normal(_MU[c], _SIGMA[c]):>8.2f}" for c in FF5_COLUMNS]
        lines.append(key + "," + ",".join(cells))
    lines.extend(["", "  Annual Factors: January-December", "," + ",".join(FF5_COLUMNS)])
    for year in range(int(start[:4]) + 1, int(end[:4])):
        cells = [
            f"{generator.normal(12 * _MU[c], math.sqrt(12) * _SIGMA[c]):>8.2f}"
            for c in FF5_COLUMNS
        ]
        lines.append(f"{year}," + ",".join(cells))
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def independent_window(
    csv_bytes: bytes, column: str, *, start: str, end: str
) -> np.ndarray:
    """The decimal series for one column over one window, read straight off the text."""
    lines = csv_bytes.decode("utf-8").splitlines()
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
        headers={"content-type": "text/csv", "last-modified": "Thu, 30 Jul 2026 20:24:24 GMT"},
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
    for seed, (region, (url, dataset_id, start)) in enumerate(FILES.items()):
        csv_bytes = synthetic_french_csv(start=start, end="2026-06", seed=20260812 + seed)
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
    schema rather than declare it, and the cast keeps that assertion readable.
    """
    return result.diagnostics


def _regional(result: ExperimentResult) -> dict[str, Any]:
    return {
        f"{c['factor']}/{c['region']}/{c['era_role']}": c
        for c in diagnostics(result)["regional_cells"]
    }


def _pooled(result: ExperimentResult) -> dict[str, Any]:
    return {f"{c['factor']}/{c['era_role']}": c for c in diagnostics(result)["pooled_cells"]}


# --------------------------------------------------------------------------- #
# The happy path
# --------------------------------------------------------------------------- #


def test_the_experiment_runs_and_matches_an_independent_computation(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    regional = _regional(result)
    assert len(regional) == 27, "3 factors x 3 regions x 3 era roles"

    expected = independent_window(
        sources["bytes"]["emerging"], "HML", start="1994-01", end="2025-12"
    )
    cell = regional["HML/emerging/full_post_publication"]
    assert cell["observations"] == expected.size == 384
    assert cell["annualised_premium_percent"] == pytest.approx(
        1200.0 * float(np.mean(expected))
    )
    assert cell["annualised_volatility_percent"] == pytest.approx(
        100.0 * math.sqrt(12.0) * float(np.std(expected, ddof=1))
    )

    rmw = regional["RMW/developed_ex_us/first_post_publication"]
    assert rmw["start"] == "2014-01" and rmw["end"] == "2019-12"
    assert rmw["observations"] == 72


def test_the_pooled_premium_is_the_equal_weighted_composite_of_the_three_regions(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    columns = [
        independent_window(sources["bytes"][region], "CMA", start="2014-01", end="2025-12")
        for region in FILES
    ]
    composite = np.mean(np.column_stack(columns), axis=1)
    pooled = _pooled(result)["CMA/full_post_publication"]
    assert pooled["months"] == 144
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
        # Not bounded above by 3: it is a sample statistic, and regions that
        # correlate negatively in a finite sample return more than k. That is
        # why it carries a joint-bootstrap interval rather than a bare point.
        assert sample["effective_regions"] > 0.0, key
        assert sample["effective_region_months_iid"] == pytest.approx(
            cell["months"] * sample["effective_regions"]
        )
        assert sample["inflation_avoided_iid"] == pytest.approx(
            sample["naive_region_months_if_independent"]
            / sample["effective_region_months_iid"]
        )
        intervals = {item["statistic"]: item for item in cell["panel_intervals"]}
        assert set(intervals) == {
            "effective_regions",
            "pooled_mde_one_sided_percent_per_year",
        }, key
        for statistic, interval in intervals.items():
            low, high = interval["two_sided_90"]
            assert low <= high, (key, statistic)
        assert intervals["effective_regions"]["point_estimate"] == pytest.approx(
            sample["effective_regions"]
        )
        assert intervals["pooled_mde_one_sided_percent_per_year"][
            "point_estimate"
        ] == pytest.approx(cell["mde_one_sided_percent_per_year"])

    columns = [
        independent_window(sources["bytes"][region], "HML", start="1994-01", end="2025-12")
        for region in FILES
    ]
    panel = np.column_stack(columns) * 100.0
    composite = np.mean(panel, axis=1)
    expected = float(np.mean(np.var(panel, axis=0, ddof=1))) / float(
        np.var(composite, ddof=1)
    )
    sample = _pooled(result)["HML/full_post_publication"]["effective_sample_size"]
    assert sample["effective_regions"] == pytest.approx(expected)


def test_the_joint_and_the_invalid_independent_intervals_are_both_reported(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    for cell in diagnostics(result)["pooled_cells"]:
        schemes = {b["scheme"] for b in cell["bootstraps"]}
        assert "cross-region-joint" in schemes
        assert "per-region-independent-INVALID" in schemes
        invalid = [b for b in cell["bootstraps"] if not b["valid"]]
        assert len(invalid) == 1
    rows = diagnostics(result)["hostile_tests"]["independent_versus_joint_resampling"]["rows"]
    assert len(rows) == 9
    assert all(row["narrowing_factor"] is not None for row in rows)


def test_the_regional_coverage_claim_is_checked_against_the_data(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """Experiment 001's stated reason for skipping the regions is tested, not repeated."""
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    check = diagnostics(result)["regional_coverage_check"]
    assert "FALSE for every era" in str(check["verdict"])
    assert check["checked_against"] == "the loaded series, not this text"
    assert all(row["covered"] for row in check["rows"])
    head_room = {
        (row["region"], row["factor"], row["era"]): row["months_of_head_room"]
        for row in check["rows"]
    }
    # 1990-07 to 1994-01 is 42 months of head room for developed-ex-US on HML.
    assert head_room[("developed_ex_us", "HML", "hml_full_post_publication")] == 42
    assert head_room[("emerging", "HML", "hml_full_post_publication")] == 54
    # The check is per factor as well as per region: a file whose RMW column
    # starts later than its HML column must not hide behind the earlier one.
    assert len(check["rows"]) == 27


def test_a_region_that_starts_after_an_era_aborts_instead_of_truncating(
    tmp_path: Path, offline_cache: Path
) -> None:
    """A silently truncated regional window looks exactly like a shorter one."""
    pins: dict[str, tuple[str, str]] = {}
    for seed, (region, (url, dataset_id, start)) in enumerate(FILES.items()):
        # Push the emerging file past HML's 1994-01 boundary.
        first = "1999-01" if region == "emerging" else start
        pins[region] = seed_cache(
            offline_cache,
            url,
            dataset_id,
            synthetic_french_csv(start=first, end="2026-06", seed=1 + seed),
        )
    with pytest.raises(RegionalReplicationError, match="silently truncated"):
        run(synthetic_specification(pins), _context(offline_cache.parent))


def test_the_holdout_is_never_read(tmp_path: Path, sources: dict[str, Any]) -> None:
    """The files run to 2026-06; the frozen sample policy ends 2025-12."""
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    for cell in diagnostics(result)["regional_cells"]:
        assert cell["last_observation"] <= "2025-12"
    for cell in diagnostics(result)["pooled_cells"]:
        assert cell["last_observation"] <= "2025-12"
    withheld = diagnostics(result)["sample_policy"]["months_available_beyond_holdout"]
    assert set(withheld) == {"us", "developed_ex_us", "emerging"}
    assert all(value == 6 for value in withheld.values())


def test_only_the_us_cells_carry_a_measured_second_moment_band(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """The regional files were never gated, which is weaker than a band of zero."""
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    regional = _regional(result)
    assert regional["HML/us/full_post_publication"]["second_moment_band"][
        "relative_band_on_volatility"
    ] == pytest.approx(0.0303)
    assert regional["RMW/us/full_post_publication"]["second_moment_band"][
        "relative_band_on_volatility"
    ] == pytest.approx(0.0509)
    assert regional["CMA/us/full_post_publication"]["second_moment_band"] is None
    for region in ("developed_ex_us", "emerging"):
        for factor in ("HML", "RMW", "CMA"):
            band = regional[f"{factor}/{region}/full_post_publication"]["second_moment_band"]
            assert band["measured"] is False
            assert "never gated" in str(band["note"])


def test_both_multiple_testing_families_are_reported_corrected_and_uncorrected(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    families = {family["family"]: family for family in diagnostics(result)["inference"]}
    assert families["regional_cells"]["family_size"] == 27
    assert families["pooled_cells"]["family_size"] == 9
    for family in families.values():
        assert family["alpha"] == 0.10
        for row in family["cells"]:
            assert row["benjamini_hochberg_adjusted_p"] >= row["one_sided_p_uncorrected"] - 1e-12
            assert (
                row["holm_bonferroni_adjusted_p"]
                >= row["benjamini_hochberg_adjusted_p"] - 1e-12
            )


def test_umd_is_recorded_as_not_covered_and_points_at_the_experiment_that_covers_it(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    """UMD is outside this frozen universe; the reason once given for that was false.

    The specification recorded that no regional momentum file existed. That was
    true of this repository and false of the data, and Experiment 006 corrected
    it by acquiring the three files. This experiment must say so rather than
    repeat the original claim.
    """
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    entry = diagnostics(result)["umd_not_covered"]
    assert entry["covered"] is False
    assert entry["superseded_by"] == "exp_006_regional_momentum"
    assert "NOT about the data" in str(entry["reason"])
    assert "french_us_momentum" in entry["registered_french_datasets"]
    assert {
        "french_developed_ex_us_momentum",
        "french_emerging_momentum",
    } <= set(entry["registered_french_datasets"])


def test_every_factor_receives_a_closed_status_and_a_named_branch(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    verdicts = {v["factor"]: v for v in diagnostics(result)["verdicts"]}
    assert set(verdicts) == {"HML", "RMW", "CMA"}
    for verdict in verdicts.values():
        assert verdict["status"] in {item.value for item in ResultStatus}
        assert verdict["falsifier_branch"]
        assert verdict["reasoning"]
        if verdict["status"] == ResultStatus.UNRESOLVED.value:
            assert verdict["what_would_fire"], "an `unresolved` must say what would fire"


def test_the_result_carries_the_gross_pooled_and_ungated_caveats(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    joined = " ".join(result.caveats)
    assert "UPPER BOUND" in joined
    assert "NEVER gated" in joined
    assert "UMD is NOT covered" in joined
    assert "NOT three independent samples" in joined
    assert "works" not in result.summary.lower()
    assert result.status in {
        ResultStatus.EXPLORATORY,
        ResultStatus.UNRESOLVED,
        ResultStatus.REJECTED,
    }


def test_the_episode_test_names_the_us_years_rather_than_fitting_one(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    result = run(synthetic_specification(sources["pins"]), _context(tmp_path))
    rows = {
        row["cell"]: row
        for row in diagnostics(result)["hostile_tests"]["episode_sharing_across_regions"][
            "rows"
        ]
    }
    hml = rows["HML/pooled/full_post_publication"]
    assert hml["named_episode_from_exp_001"]["year"] == "2000"
    assert set(hml["named_episode_from_exp_001"]["per_region"]) == set(FILES)
    assert isinstance(hml["regions_share_the_same_best_year"], bool)
    assert rows["RMW/pooled/full_post_publication"]["named_episode_from_exp_001"]["year"] == "2021"
    assert rows["CMA/pooled/full_post_publication"]["named_episode_from_exp_001"] is None


# --------------------------------------------------------------------------- #
# The pin
# --------------------------------------------------------------------------- #


def test_an_unrecognised_vintage_aborts_instead_of_reporting_premia(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    pins = dict(sources["pins"])
    pins["emerging"] = ("0" * 64, pins["emerging"][1])
    with pytest.raises(RegionalReplicationError, match="new vintage, not a corrupted download"):
        run(synthetic_specification(pins), _context(tmp_path))


def test_a_parser_change_that_leaves_the_bytes_alone_is_caught(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    pins = dict(sources["pins"])
    pins["developed_ex_us"] = (pins["developed_ex_us"][0], "0" * 64)
    with pytest.raises(RegionalReplicationError, match="the parser changed behaviour"):
        run(synthetic_specification(pins), _context(tmp_path))


# --------------------------------------------------------------------------- #
# The ledger
# --------------------------------------------------------------------------- #


def test_the_run_is_ledgered_with_provenance_and_hashed_artifacts(
    tmp_path: Path, sources: dict[str, Any]
) -> None:
    specification = synthetic_specification(sources["pins"])
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
    assert [entry.event for entry in entries] == [
        LedgerEvent.STARTED,
        LedgerEvent.SUCCEEDED,
    ]
    succeeded = entries[-1]
    assert succeeded.spec_hash == specification.spec_hash
    assert succeeded.artifacts
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


def test_the_three_pinned_files_are_the_three_regions_and_not_the_developed_file() -> None:
    """`Developed_5_Factors` includes the US; pooling it would double-count half of it."""
    raw = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    series: Sequence[Any] = raw["parameters"]["source_pin"]["series"]
    datasets = {entry["dataset_id"] for entry in series}
    assert datasets == {
        "french_us_ff5",
        "french_developed_ex_us_ff5",
        "french_emerging_ff5",
    }
    assert "french_developed_ff5" not in datasets
