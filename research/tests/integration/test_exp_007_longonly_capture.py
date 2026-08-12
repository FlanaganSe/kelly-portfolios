"""End-to-end tests for Experiment 007, offline.

The real files cannot be committed, so the whole path -- cache, zip-or-CSV
extraction, multi-table parsing, percent-to-decimal conversion, the sha256 pin on
eleven tables, the committed-manifest check, era windowing, the holdout clip, the
reconstruction identities that are clause (0), every capture definition, the
joint ratio bootstrap, the corner, the microcap shares, the regional legs, the
cost column, the frozen rejection rule, the artifacts and the ledger -- runs
against synthetic files in exactly the Ken French layout, seeded into a
throwaway cache under the real URLs.

The synthetic factor files are built BY THE IDENTITIES THEMSELVES and then
rounded to the source's two decimal places, so the fixture exercises clause (0)
against genuine rounding rather than against a contrived residual. Expected
values are computed in this file with plain NumPy, never by calling the code
under test.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from portfolio_edge.data import french
from portfolio_edge.data.cache import CACHE_ENV_VAR, RawCache
from portfolio_edge.data.manifest import manifest_from_table
from portfolio_edge.experiments import exp_007_longonly_capture as module
from portfolio_edge.experiments.exp_007_longonly_capture import (
    ENTRY_POINT,
    LongOnlyCaptureError,
    build_registry,
    run,
)
from portfolio_edge.experiments.ledger import Ledger, LedgerEvent, RunStatus
from portfolio_edge.experiments.registry import RunContext
from portfolio_edge.experiments.result import ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import specification_from_mapping

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"

#: The committed specifications, resolved from this file rather than from
#: ``default_specification_path``. The workspace root is monkeypatched below so
#: that the experiment reads throwaway manifests, and the real YAML would then be
#: unreachable through the function that reads it.
SPEC_DIR = Path(__file__).resolve().parents[2] / "experiments"
REAL_SPEC = SPEC_DIR / "exp_007_longonly_capture.yaml"

VALUE_6 = ("SMALL LoBM", "ME1 BM2", "SMALL HiBM", "BIG LoBM", "ME2 BM2", "BIG HiBM")
MOM_6 = ("SMALL LoPRIOR", "ME1 PRIOR2", "SMALL HiPRIOR", "BIG LoPRIOR", "ME2 PRIOR2", "BIG HiPRIOR")
CELLS_25 = tuple(
    ["SMALL LoBM", "ME1 BM2", "ME1 BM3", "ME1 BM4", "SMALL HiBM"]
    + [f"ME{size} BM{value}" for size in (2, 3, 4) for value in range(1, 6)]
    + ["BIG LoBM", "ME5 BM2", "ME5 BM3", "ME5 BM4", "BIG HiBM"]
)
SIZE_COLUMNS = (
    "<= 0",
    "Lo 30",
    "Med 40",
    "Hi 30",
    "Lo 20",
    "Qnt 2",
    "Qnt 3",
    "Qnt 4",
    "Hi 20",
    "Lo 10",
    "2-Dec",
    "3-Dec",
    "4-Dec",
    "5-Dec",
    "6-Dec",
    "7-Dec",
    "8-Dec",
    "9-Dec",
    "Hi 10",
)


def _month_keys(start: str, end: str) -> list[str]:
    def index(period: str) -> int:
        year, month = period.split("-")
        return int(year) * 12 + int(month) - 1

    return [f"{i // 12:04d}{i % 12 + 1:02d}" for i in range(index(start), index(end) + 1)]


def _cells(values: Sequence[float] | np.ndarray) -> str:
    return ",".join(f"{float(value):>8.2f}" for value in values)


def _portfolio_file(
    *,
    columns: Sequence[str],
    keys: Sequence[str],
    values: np.ndarray,
    counts: np.ndarray | None = None,
    caps: np.ndarray | None = None,
    preamble: str,
    returns_banner: str = "Average Value Weighted Returns -- Monthly",
) -> bytes:
    """A portfolio file: prose, monthly returns, annual returns, counts, caps.

    Every real portfolio file carries the count and market-cap tables, and their
    presence is what stops ``monthly`` from being a unique frequency and
    therefore what makes the parser name the tables from their banners. A fixture
    without them would be parsed into differently named tables from the real
    file, which is precisely the drift these tests exist to catch.
    """
    lines = [preamble, "", "Missing data are indicated by -99.99 or -999.", ""]
    lines.append(f"  {returns_banner}")
    lines.append("," + ",".join(columns))
    for key, row in zip(keys, values, strict=True):
        lines.append(key + "," + _cells(row))
    lines.extend(
        ["", f"  {returns_banner.replace('Monthly', 'Annual')}", "," + ",".join(columns)]
    )
    for year in range(int(keys[0][:4]) + 1, int(keys[-1][:4])):
        lines.append(f"{year}," + _cells(values[: len(columns)].sum(axis=0)))
    firms = counts if counts is not None else np.full((len(keys), len(columns)), 100.0)
    lines.extend(["", "  Number of Firms in Portfolios", "," + ",".join(columns)])
    for key, row in zip(keys, firms, strict=True):
        lines.append(key + "," + ",".join(f"{value:>8.0f}" for value in row))
    sizes = caps if caps is not None else np.full((len(keys), len(columns)), 1000.0)
    lines.extend(["", "  Average Market Cap", "," + ",".join(columns)])
    for key, row in zip(keys, sizes, strict=True):
        lines.append(key + "," + ",".join(f"{value:>10.2f}" for value in row))
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _factor_file(
    *, columns: Sequence[str], keys: Sequence[str], values: np.ndarray, preamble: str
) -> bytes:
    """A factor file: an UNLABELLED monthly table, exactly as the real ones are."""
    lines = [preamble, "", "Missing data are indicated by -99.99 or -999.", ""]
    lines.append("," + ",".join(columns))
    for key, row in zip(keys, values, strict=True):
        lines.append(key + "," + _cells(row))
    lines.extend(["", "  Annual Factors: January-December", "," + ",".join(columns)])
    for year in range(int(keys[0][:4]) + 1, int(keys[-1][:4])):
        lines.append(f"{year}," + _cells(values[: len(columns)].sum(axis=0)))
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _round2(values: np.ndarray) -> np.ndarray:
    """What the source does to every number it prints."""
    return np.asarray(np.round(values, 2), dtype=np.float64)


def _build(seed: int = 20260812) -> dict[str, Any]:
    """Every synthetic file, with the factor columns built from the portfolios."""
    generator = np.random.default_rng(seed)
    keys = _month_keys("1926-07", "2026-06")
    n = len(keys)
    keys_1963 = _month_keys("1963-07", "2026-06")
    keys_1927 = _month_keys("1927-01", "2026-06")
    keys_1990 = _month_keys("1990-07", "2026-06")
    keys_1989 = _month_keys("1989-07", "2026-06")

    def portfolios(rows: int, columns: int, mus: np.ndarray) -> np.ndarray:
        common = generator.normal(0.5, 4.2, size=(rows, 1))
        return _round2(common + generator.normal(mus, 2.5, size=(rows, columns)))

    # US 2x3 value-weighted: growth low, value high, small higher still.
    six = portfolios(n, 6, np.asarray([0.15, 0.35, 0.65, 0.10, 0.28, 0.45]))
    market = _round2(0.5 + generator.normal(0.0, 0.4, size=n) + six.mean(axis=1) * 0.05)
    rf = _round2(np.abs(generator.normal(0.30, 0.08, size=n)))

    hml = _round2(0.5 * (six[:, 2] + six[:, 5]) - 0.5 * (six[:, 0] + six[:, 3]))
    smb = _round2(six[:, :3].mean(axis=1) - six[:, 3:].mean(axis=1))
    ff3 = np.column_stack([market - rf, smb, hml, rf])

    # The five-factor file's SMB is deliberately a DIFFERENT series.
    smb5 = _round2(smb + generator.normal(0.0, 0.6, size=n))
    index_1963 = keys.index("196307")
    ff5 = np.column_stack(
        [
            (market - rf)[index_1963:],
            smb5[index_1963:],
            hml[index_1963:],
            _round2(generator.normal(0.25, 1.8, size=n - index_1963)),
            _round2(generator.normal(0.30, 1.6, size=n - index_1963)),
            rf[index_1963:],
        ]
    )

    momentum_n = len(keys_1927)
    six_mom = portfolios(momentum_n, 6, np.asarray([-0.20, 0.30, 0.85, -0.10, 0.25, 0.70]))
    mom = _round2(
        0.5 * (six_mom[:, 2] + six_mom[:, 5]) - 0.5 * (six_mom[:, 0] + six_mom[:, 3])
    )

    twenty_five = portfolios(n, 25, np.linspace(0.10, 0.70, 25))
    counts = np.tile(
        np.concatenate([np.full(5, 600.0), np.full(15, 200.0), np.full(5, 40.0)]), (n, 1)
    )
    caps = np.tile(
        np.concatenate([np.full(5, 200.0), np.full(15, 5000.0), np.full(5, 200000.0)]), (n, 1)
    )

    size_portfolios = portfolios(n, len(SIZE_COLUMNS), np.full(len(SIZE_COLUMNS), 0.45))

    regional_n = len(keys_1990)
    six_dev = portfolios(regional_n, 6, np.asarray([0.10, 0.30, 0.60, 0.08, 0.25, 0.42]))
    dev_market = _round2(0.45 + generator.normal(0.0, 0.4, size=regional_n))
    dev_hml = _round2(
        0.5 * (six_dev[:, 2] + six_dev[:, 5]) - 0.5 * (six_dev[:, 0] + six_dev[:, 3])
    )
    dev_ff5 = np.column_stack(
        [
            dev_market - rf[-regional_n:],
            _round2(six_dev[:, :3].mean(axis=1) - six_dev[:, 3:].mean(axis=1)),
            dev_hml,
            _round2(generator.normal(0.2, 1.7, size=regional_n)),
            _round2(generator.normal(0.2, 1.6, size=regional_n)),
            rf[-regional_n:],
        ]
    )

    emerging_n = len(keys_1989)
    six_emg = portfolios(emerging_n, 6, np.asarray([0.05, 0.35, 0.75, 0.05, 0.30, 0.55]))
    emg_market = _round2(0.50 + generator.normal(0.0, 0.6, size=emerging_n))
    emg_hml = _round2(
        0.5 * (six_emg[:, 2] + six_emg[:, 5]) - 0.5 * (six_emg[:, 0] + six_emg[:, 3])
    )
    emg_ff5 = np.column_stack(
        [
            emg_market - rf[-emerging_n:],
            _round2(six_emg[:, :3].mean(axis=1) - six_emg[:, 3:].mean(axis=1)),
            emg_hml,
            _round2(generator.normal(0.2, 2.0, size=emerging_n)),
            _round2(generator.normal(0.2, 1.9, size=emerging_n)),
            rf[-emerging_n:],
        ]
    )

    ff5_columns = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
    return {
        "arrays": {
            "six": six,
            "market": market,
            "rf": rf,
            "hml": hml,
            "keys": keys,
            "index_1963": index_1963,
            "twenty_five": twenty_five,
            "counts": counts,
            "caps": caps,
        },
        "files": {
            "6_Portfolios_2x3_CSV.zip": (
                "french_us_6_portfolios_2x3",
                _portfolio_file(
                    columns=VALUE_6,
                    keys=keys,
                    values=six,
                    preamble="Synthetic 6 portfolios on ME and BEME.",
                ),
            ),
            "25_Portfolios_5x5_CSV.zip": (
                "french_us_25_portfolios_5x5",
                _portfolio_file(
                    columns=CELLS_25,
                    keys=keys,
                    values=twenty_five,
                    counts=counts,
                    caps=caps,
                    preamble="Synthetic 25 portfolios on ME and BEME.",
                ),
            ),
            "6_Portfolios_ME_Prior_12_2_CSV.zip": (
                "french_us_6_portfolios_me_prior_12_2",
                _portfolio_file(
                    columns=MOM_6,
                    keys=keys_1927,
                    values=six_mom,
                    preamble="Synthetic 6 portfolios on ME and prior return.",
                ),
            ),
            "Portfolios_Formed_on_ME_CSV.zip": (
                "french_us_portfolios_formed_on_me",
                _portfolio_file(
                    columns=SIZE_COLUMNS,
                    keys=keys,
                    values=size_portfolios,
                    preamble="Synthetic size portfolios.",
                    returns_banner="Average Value Weight Returns -- Monthly",
                ),
            ),
            "F-F_Research_Data_Factors_CSV.zip": (
                "french_us_ff3",
                _factor_file(
                    columns=("Mkt-RF", "SMB", "HML", "RF"),
                    keys=keys,
                    values=ff3,
                    preamble="Synthetic three factors.",
                ),
            ),
            "F-F_Research_Data_5_Factors_2x3_CSV.zip": (
                "french_us_ff5",
                _factor_file(
                    columns=ff5_columns,
                    keys=keys_1963,
                    values=ff5,
                    preamble="Synthetic five factors.",
                ),
            ),
            "F-F_Momentum_Factor_CSV.zip": (
                "french_us_momentum",
                _factor_file(
                    columns=("Mom",),
                    keys=keys_1927,
                    values=mom.reshape(-1, 1),
                    preamble="Synthetic momentum factor.",
                ),
            ),
            "Developed_ex_US_6_Portfolios_ME_BE-ME_CSV.zip": (
                "french_developed_ex_us_6_portfolios_2x3",
                _portfolio_file(
                    columns=VALUE_6,
                    keys=keys_1990,
                    values=six_dev,
                    preamble="Synthetic developed ex US 6 portfolios.",
                ),
            ),
            "Developed_ex_US_5_Factors_CSV.zip": (
                "french_developed_ex_us_ff5",
                _factor_file(
                    columns=ff5_columns,
                    keys=keys_1990,
                    values=dev_ff5,
                    preamble="Synthetic developed ex US five factors.",
                ),
            ),
            "Emerging_Markets_6_Portfolios_ME_BE-ME_CSV.zip": (
                "french_emerging_6_portfolios_2x3",
                _portfolio_file(
                    columns=VALUE_6,
                    keys=keys_1989,
                    values=six_emg,
                    preamble="Synthetic emerging 6 portfolios.",
                ),
            ),
            "Emerging_5_Factors_CSV.zip": (
                "french_emerging_ff5",
                _factor_file(
                    columns=ff5_columns,
                    keys=keys_1989,
                    values=emg_ff5,
                    preamble="Synthetic emerging five factors.",
                ),
            ),
        },
    }


@pytest.fixture(scope="module")
def built() -> dict[str, Any]:
    return _build()


@pytest.fixture
def workspace(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, Any],
) -> dict[str, Any]:
    """A throwaway cache, throwaway manifests, and a spec repointed at both."""
    root = tmp_path_factory.mktemp("exp007")
    monkeypatch.setenv(CACHE_ENV_VAR, str(root / "cache"))
    monkeypatch.setattr(module, "_workspace_root", lambda: root)

    cache = RawCache(root / "cache")
    pins: dict[str, str] = {}
    manifests: dict[str, Any] = {}
    for filename, (dataset_id, payload) in built["files"].items():
        dataset = french.get_dataset(dataset_id)
        entry = cache.store(
            f"{BASE}/{filename}",
            payload,
            headers={"content-type": "text/csv", "last-modified": "Mon, 03 Aug 2026 19:17:20 GMT"},
        )
        pins[dataset_id] = entry.sha256
        manifests[dataset_id] = (entry, french.parse(cache, entry, dataset=dataset))

    raw: Any = yaml.safe_load(REAL_SPEC.read_text(encoding="utf-8"))
    manifest_dir = root / "data-manifests"
    for series in raw["parameters"]["source_pin"]["series"]:
        dataset_id = series["dataset_id"]
        entry, parsed = manifests[dataset_id]
        table = parsed.table(series["table_id"])
        series["expected_sha256_raw"] = pins[dataset_id]
        manifest_from_table(
            dataset_id=series["manifest_dataset_id"],
            entry=entry,
            table=table,
            parser_version=french.PARSER_VERSION,
            availability_policy=french.get_dataset(dataset_id).availability_policy,
            revision_policy=french.get_dataset(dataset_id).revision_policy,
            license_or_terms_url=french.LICENSE_OR_TERMS_URL,
            extra_warnings=("synthetic fixture",),
        ).write(manifest_dir)
    raw["inference"]["resamples"] = 60
    # The sibling count and cap tables are read through the same cached bytes.
    (root / "experiments").mkdir(parents=True, exist_ok=True)
    (root / "experiments" / "exp_001_factor_decay.yaml").write_text(
        (SPEC_DIR / "exp_001_factor_decay.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return {
        "root": root,
        "raw": raw,
        "specification": specification_from_mapping(
            raw, source_path=REAL_SPEC
        ),
    }


def _context(root: Path) -> RunContext:
    return RunContext(
        run_id="fixture",
        seed=20260812,
        rng=np.random.default_rng(20260812),
        artifact_dir=root / "artifacts" / "fixture",
    )


def diagnostics(result: ExperimentResult) -> Any:
    """Navigate the diagnostics as plain data; its type is whatever JSON holds."""
    return result.diagnostics


def _cells_by_key(result: ExperimentResult) -> dict[str, Any]:
    return {
        f"{c['definition']}/{c['era']}": c for c in diagnostics(result)["capture_cells"]
    }


# --------------------------------------------------------------------------- #
# The happy path
# --------------------------------------------------------------------------- #


def test_the_experiment_runs_and_clause_zero_passes_on_genuine_rounding(
    workspace: dict[str, Any],
) -> None:
    """The synthetic factor columns are built by the identities and then rounded.

    So the residual the run measures is real two-decimal-place rounding, and
    clause (0) is exercised against exactly the thing it exists to bound.
    """
    result = run(workspace["specification"], _context(workspace["root"]))
    checks = {c["identity"]: c for c in diagnostics(result)["reconstruction_checks"]}

    hml = checks["hml_from_6_portfolios_2x3"]
    assert hml["passed"]
    assert 0.0 < hml["max_absolute_residual_percentage_points_per_month"] <= 0.015

    assert checks["smb_from_6_portfolios_2x3_against_three_factor"]["passed"]
    assert checks["umd_from_6_portfolios_me_prior_12_2"]["passed"]

    five = checks["smb_from_6_portfolios_2x3_against_five_factor"]
    assert not five["expected_to_pass"], "the two SMBs are different series"
    assert not five["passed"], "the fixture builds them differently on purpose"

    assert diagnostics(result)["verdict"]["clause_0_reconstruction_passed"] is True


def test_the_capture_fraction_matches_an_independent_computation(
    workspace: dict[str, Any], built: dict[str, Any]
) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    cell = _cells_by_key(result)["value_halves_vs_size_neutral/full_sample_since_1963"]

    arrays = built["arrays"]
    keys = arrays["keys"]
    first = keys.index("196307")
    last = keys.index("202512")
    six = arrays["six"][first : last + 1] / 100.0
    long_only = 0.5 * (six[:, 2] + six[:, 5])
    benchmark = six.mean(axis=1)
    spread = 0.5 * (six[:, 2] + six[:, 5]) - 0.5 * (six[:, 0] + six[:, 3])

    assert cell["months"] == six.shape[0] == 750
    assert cell["capture_fraction"] == pytest.approx(
        float(np.mean(long_only - benchmark)) / float(np.mean(spread))
    )
    assert cell["long_only_excess_spread_percent_per_year"] == pytest.approx(
        1200.0 * float(np.mean(long_only - benchmark))
    )
    assert cell["long_only_annualised_percent"] == pytest.approx(
        1200.0 * float(np.mean(long_only))
    )


def test_the_market_benchmark_is_a_total_return_not_the_market_factor(
    workspace: dict[str, Any], built: dict[str, Any]
) -> None:
    """Mkt-RF + RF, never Mkt-RF.

    Subtracting a market factor already net of the one-month bill from a
    long-only TOTAL return would understate the benchmark by the whole bill rate
    and flatter every capture fraction in the experiment.
    """
    result = run(workspace["specification"], _context(workspace["root"]))
    cell = _cells_by_key(result)["value_halves_vs_market/full_sample_since_1963"]

    arrays = built["arrays"]
    keys = arrays["keys"]
    first, last = keys.index("196307"), keys.index("202512")
    market = arrays["market"][first : last + 1] / 100.0
    assert cell["benchmark_annualised_percent"] == pytest.approx(
        1200.0 * float(np.mean(market))
    )


def test_the_long_and_short_leg_shares_sum_to_one_on_the_real_path(
    workspace: dict[str, Any],
) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    rows = diagnostics(result)["hostile_tests"]["long_and_short_leg_shares_sum_to_one"]["rows"]
    assert rows
    for row in rows:
        assert row["sum"] == pytest.approx(1.0, abs=1e-9), row["era"]


def test_the_holdout_is_never_read(workspace: dict[str, Any]) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    for cell in diagnostics(result)["capture_cells"]:
        assert cell["last_observation"] <= "2025-12", cell["definition"]
    policy = diagnostics(result)["sample_policy"]
    assert policy["held_out_after"] == "2025-12"
    assert policy["months_available_beyond_holdout"] == 6


def test_the_inherited_eras_are_checked_against_experiment_001(
    workspace: dict[str, Any],
) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    inherited = diagnostics(result)["inherited_era_check"]
    assert inherited["checked"] is True
    assert inherited["all_agree"] is True
    assert "hml_full_post_publication" in inherited["shared_eras"]


def test_the_microcap_shares_are_reported_and_sum_to_a_hundred(
    workspace: dict[str, Any],
) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    shares = diagnostics(result)["small_value_corner"][
        "capitalisation_and_firm_count_shares"
    ]
    assert sum(row["mean_share_of_firm_count_percent"] for row in shares["per_cell"]) == (
        pytest.approx(100.0)
    )
    assert sum(row["mean_share_of_market_cap_percent"] for row in shares["per_cell"]) == (
        pytest.approx(100.0)
    )
    # The fixture puts 600 firms of 200 average cap in every ME1 cell against
    # 40 firms of 200000 in every ME5 cell, so the smallest quintile is most of
    # the count and almost none of the money, as it is in the real file.
    quintile = shares["smallest_size_quintile"]
    assert quintile["mean_share_of_firm_count_percent"] > 40.0
    assert quintile["mean_share_of_market_cap_percent"] < 5.0


def test_the_cost_column_separates_measured_turnover_from_assumed_turnover(
    workspace: dict[str, Any],
) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    costs = diagnostics(result)["costs"]
    measured = costs["measured_component"]["rows"]
    assert measured
    for row in measured:
        assert row["measured_rebalance_cost_percent_per_year"] >= 0.0
        assert (
            row["net_geometric_annual_percent"] <= row["gross_geometric_annual_percent"]
        )
    assumed = costs["assumed_components"]["rows"]
    assert all(row["measured_or_assumed"] == "assumed" for row in assumed)
    # A monthly prior-return reconstitution at 900% a year is 75% a month, above
    # the 50% retail limit core.costs states.
    worst = max(row["assumed_one_sided_turnover_percent_per_year"] for row in assumed)
    assert any(
        row["retail_implementable_at_this_turnover"] is False
        for row in assumed
        if row["assumed_one_sided_turnover_percent_per_year"] == worst
    )


def test_the_regional_legs_use_the_ex_us_files_and_say_why(
    workspace: dict[str, Any],
) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    regional = diagnostics(result)["regional"]
    assert "INCLUDE the United States" in regional["why_not_the_developed_file"]
    assert "404" in regional["no_emerging_corner"]
    regions = {cell["definition"].split("/")[0] for cell in regional["cells"]}
    assert regions == {"developed_ex_us", "emerging"}


def test_every_estimate_carries_units_and_either_an_interval_or_a_reason(
    workspace: dict[str, Any],
) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    assert result.estimates
    for estimate in result.estimates:
        assert estimate.units.strip()
        assert estimate.interval is not None or estimate.uncertainty_unavailable_reason
    names = {estimate.name for estimate in result.estimates}
    assert any(name.startswith("capture fraction, ") for name in names)
    assert any(name.startswith("definitional spread") for name in names)


def test_the_result_status_is_closed_and_the_word_works_never_appears(
    workspace: dict[str, Any],
) -> None:
    result = run(workspace["specification"], _context(workspace["root"]))
    assert isinstance(result.status, ResultStatus)
    assert "works" not in result.summary.lower()
    assert result.caveats
    assert any("not products" in caveat for caveat in result.caveats)


# --------------------------------------------------------------------------- #
# The pins, which must abort rather than degrade
# --------------------------------------------------------------------------- #


def test_a_changed_raw_hash_aborts(workspace: dict[str, Any]) -> None:
    raw = workspace["raw"]
    raw["parameters"]["source_pin"]["series"][0]["expected_sha256_raw"] = "0" * 64
    specification = specification_from_mapping(raw, source_path=REAL_SPEC)
    with pytest.raises(LongOnlyCaptureError, match="new vintage"):
        run(specification, _context(workspace["root"]))


def test_a_missing_committed_manifest_aborts(workspace: dict[str, Any]) -> None:
    raw = workspace["raw"]
    raw["parameters"]["source_pin"]["series"][0]["committed_manifest"] = (
        "data-manifests/absent.json"
    )
    specification = specification_from_mapping(raw, source_path=REAL_SPEC)
    with pytest.raises(LongOnlyCaptureError, match="is missing"):
        run(specification, _context(workspace["root"]))


def test_a_manifest_recording_a_different_derived_table_aborts(
    workspace: dict[str, Any],
) -> None:
    """The raw bytes matching while the derived table does not is a parser change."""
    path = (
        workspace["root"]
        / "data-manifests"
        / "french_us_6_portfolios_2x3_value_weighted_monthly.json"
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["sha256_normalized"] != "1" * 64
    data["sha256_normalized"] = "1" * 64
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(LongOnlyCaptureError, match="parser changed behaviour"):
        run(workspace["specification"], _context(workspace["root"]))


def test_a_wrong_first_observation_aborts(workspace: dict[str, Any]) -> None:
    raw = workspace["raw"]
    raw["parameters"]["source_pin"]["series"][0]["expected_first_observation"] = "1900-01"
    specification = specification_from_mapping(raw, source_path=REAL_SPEC)
    with pytest.raises(LongOnlyCaptureError, match="but the specification pins"):
        run(specification, _context(workspace["root"]))


# --------------------------------------------------------------------------- #
# The runner and the ledger
# --------------------------------------------------------------------------- #


def test_the_runner_writes_artifacts_and_ledgers_the_attempt(
    workspace: dict[str, Any],
) -> None:
    root = workspace["root"]
    ledger = Ledger(root / "ledger.jsonl")
    outcome = run_experiment(
        workspace["specification"],
        registry=build_registry(),
        ledger=ledger,
        artifact_root=root / "artifacts",
        run_id="fixture-run",
    )
    assert outcome.status is RunStatus.SUCCEEDED
    assert outcome.result is not None
    written = {record.path.rsplit("/", 1)[-1] for record in outcome.artifacts}
    assert {"result.json", "summary.md", "manifest.json"} <= written
    assert any(record.path.endswith("capture_cells.parquet") for record in outcome.artifacts)
    for record in outcome.artifacts:
        assert len(record.sha256) == 64 and record.size_bytes > 0

    entries = ledger.read()
    assert [entry.event for entry in entries] == [
        LedgerEvent.STARTED,
        LedgerEvent.SUCCEEDED,
    ]
    assert entries[-1].spec_hash == workspace["specification"].spec_hash
    assert entries[-1].experiment_family == ENTRY_POINT


def test_a_failing_run_is_ledgered_before_the_error_propagates(
    workspace: dict[str, Any],
) -> None:
    raw = workspace["raw"]
    raw["parameters"]["source_pin"]["series"][0]["expected_sha256_raw"] = "f" * 64
    specification = specification_from_mapping(raw, source_path=REAL_SPEC)
    ledger = Ledger(workspace["root"] / "ledger.jsonl")
    with pytest.raises(LongOnlyCaptureError):
        run_experiment(
            specification,
            registry=build_registry(),
            ledger=ledger,
            artifact_root=workspace["root"] / "artifacts",
            run_id="fixture-failure",
        )
    events = [entry.event for entry in ledger.read()]
    assert events[-1] is LedgerEvent.FAILED
    assert ledger.read()[-1].failure_reason
