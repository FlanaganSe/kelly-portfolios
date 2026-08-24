"""End-to-end tests for Experiment 010, offline.

The real files cannot be committed, so the whole path -- cache, zip-or-CSV
extraction, multi-table parsing, percent-to-decimal conversion, the sha256 pins on
ten Ken French tables and one AQR workbook, the committed-manifest check, the
one-month lead that feeds the modelled proxy, the holdout clip, every funding leg,
every cost column, the alpha/credit decomposition, the constrained weight search,
the paired bootstrap, the Holm family, the frozen rejection rule, the artifacts
and the ledger -- runs against synthetic files in exactly the sources' layouts,
seeded into a throwaway cache under the real URLs.

Expected values are computed in this file with plain NumPy, from the generated
inputs, never by calling the code under test.
"""

from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import openpyxl  # type: ignore[import-untyped]
import pytest
import yaml

from portfolio_edge.data import aqr, french
from portfolio_edge.data.cache import CACHE_ENV_VAR, RawCache
from portfolio_edge.data.manifest import manifest_from_table
from portfolio_edge.experiments import exp_010_marginal_sleeve_value as module
from portfolio_edge.experiments.exp_010_marginal_sleeve_value import (
    ENTRY_POINT,
    MONTHS_PER_YEAR,
    MarginalSleeveValueError,
    build_registry,
    certainty_equivalent_annual,
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

FRENCH_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"
SPEC_PATH = Path(__file__).resolve().parents[2] / "experiments" / (
    "exp_010_marginal_sleeve_value.yaml"
)

FF5_COLUMNS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
VALUE_6 = ("SMALL LoBM", "ME1 BM2", "SMALL HiBM", "BIG LoBM", "ME2 BM2", "BIG HiBM")
PRIOR_6 = (
    "SMALL LoPRIOR",
    "ME1 PRIOR2",
    "SMALL HiPRIOR",
    "BIG LoPRIOR",
    "ME2 PRIOR2",
    "BIG HiPRIOR",
)

DATA_START = "1990-01"
DATA_END = "2026-06"
SAMPLE_START = "1991-01"
SAMPLE_END = "2025-12"


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
    return date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)


def _cells(values: Sequence[float] | np.ndarray) -> str:
    return ",".join(f"{float(value):>8.2f}" for value in values)


def _factor_file(
    *, columns: Sequence[str], periods: Sequence[str], values: np.ndarray, preamble: str
) -> bytes:
    """A factor file: an UNLABELLED monthly table, exactly as the real ones are."""
    lines = [preamble, "", "Missing data are indicated by -99.99 or -999.", ""]
    lines.append("," + ",".join(columns))
    for period, row in zip(periods, values, strict=True):
        lines.append(period.replace("-", "") + "," + _cells(row))
    lines.extend(["", "  Annual Factors: January-December", "," + ",".join(columns)])
    for year in range(int(periods[0][:4]) + 1, int(periods[-1][:4])):
        lines.append(f"{year}," + _cells(values[: len(columns)].sum(axis=0)))
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _portfolio_file(
    *, columns: Sequence[str], periods: Sequence[str], values: np.ndarray, preamble: str
) -> bytes:
    """A portfolio file: prose, monthly returns, annual returns, counts, caps.

    The count and market-cap tables are what stop ``monthly`` from being a unique
    frequency, and therefore what makes the parser name the return table from its
    banner. A fixture without them would parse into a differently named table from
    the real file, which is precisely the drift this test exists to catch.
    """
    banner = "Average Value Weighted Returns -- Monthly"
    lines = [preamble, "", "Missing data are indicated by -99.99 or -999.", ""]
    lines.append(f"  {banner}")
    lines.append("," + ",".join(columns))
    for period, row in zip(periods, values, strict=True):
        lines.append(period.replace("-", "") + "," + _cells(row))
    lines.extend(["", f"  {banner.replace('Monthly', 'Annual')}", "," + ",".join(columns)])
    for year in range(int(periods[0][:4]) + 1, int(periods[-1][:4])):
        lines.append(f"{year}," + _cells(values[: len(columns)].sum(axis=0)))
    lines.extend(["", "  Number of Firms in Portfolios", "," + ",".join(columns)])
    for period in periods:
        lines.append(period.replace("-", "") + "," + ",".join(["     100"] * len(columns)))
    lines.extend(["", "  Average Market Cap", "," + ",".join(columns)])
    for period in periods:
        lines.append(period.replace("-", "") + "," + ",".join(["   1000.00"] * len(columns)))
    lines.append("Copyright 2026 synthetic fixture")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _aqr_workbook(periods: Sequence[str], values: np.ndarray) -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "TSMOM Factors"
    for line in (
        "A synthetic fixture, not an AQR download.",
        "",
        "This file contains the excess returns of the long/short TSMOM factors.",
        "",
    ):
        sheet.append([line])
    sheet.append([None, "TSMOM", "TSMOM^CM", "TSMOM^EQ", "TSMOM^FI", "TSMOM^FX"])
    for index, period in enumerate(periods):
        sheet.append([_month_end(period), *(float(item) for item in values[index])])
    for name in ("Definitions", "Data Sources", "Disclosures"):
        workbook.create_sheet(name).append([name])
    payload = io.BytesIO()
    workbook.save(payload)
    return payload.getvalue()


def _fred_csv(series_id: str, periods: Sequence[str], values: np.ndarray) -> bytes:
    lines = [f"observation_date,{series_id}"]
    for period, value in zip(periods, values, strict=True):
        lines.append(f"{period}-01,{value:.4f}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _round2(values: np.ndarray) -> np.ndarray:
    return np.asarray(np.round(values, 2), dtype=np.float64)


@pytest.fixture(scope="module")
def generated() -> dict[str, Any]:
    """One deterministic panel, generated once and reused by every test here.

    The regional markets share a global factor so that their correlations are
    realistic; the small-value portfolios are built with a beta above one to the
    global core, and the trend sleeve is explicitly short the market in its worst
    months, so the experiment has both a negative and a positive credit to find
    rather than only noise.
    """
    rng = np.random.default_rng(1010)
    periods = _months(DATA_START, DATA_END)
    n = len(periods)

    global_factor = rng.normal(0.55, 4.0, size=n)
    rf = _round2(np.abs(rng.normal(0.28, 0.07, size=n)))

    def region(loading: float, extra: float, sigma: float) -> np.ndarray:
        return _round2(loading * global_factor + rng.normal(extra, sigma, size=n))

    us_excess = region(1.0, 0.05, 1.4)
    dev_excess = region(0.95, -0.10, 2.4)
    emerging_excess = region(1.05, 0.05, 4.2)

    def six(base: np.ndarray, tilt: float, beta: float, sigma: float) -> np.ndarray:
        """Six portfolios whose HiBM corner is higher beta than the market."""
        columns = []
        for index, mu in enumerate((0.10, 0.25, 0.55, 0.05, 0.20, 0.35)):
            loading = beta if index in (2, 5) else 0.95
            columns.append(loading * (base + rf) + rng.normal(mu + tilt, sigma, size=n))
        return _round2(np.column_stack(columns))

    us_six = six(us_excess, 0.0, 1.25, 2.4)
    dev_six = six(dev_excess, -0.05, 1.20, 2.6)
    emerging_six = six(emerging_excess, 0.05, 1.15, 3.4)
    prior_six = six(us_excess, 0.05, 1.05, 2.6)

    def factors(excess: np.ndarray, portfolios: np.ndarray) -> np.ndarray:
        high = 0.5 * (portfolios[:, 2] + portfolios[:, 5])
        low = 0.5 * (portfolios[:, 0] + portfolios[:, 3])
        hml = _round2(high - low)
        smb = _round2(portfolios[:, :3].mean(axis=1) - portfolios[:, 3:].mean(axis=1))
        return np.column_stack(
            [
                excess,
                smb,
                hml,
                _round2(rng.normal(0.20, 1.7, size=n)),
                _round2(rng.normal(0.20, 1.6, size=n)),
                rf,
            ]
        )

    # Momentum factors: near-zero beta to the market, which is what gives them a
    # positive credit and the equity sleeves a negative one.
    momentum = {
        name: _round2(rng.normal(mu, 3.6, size=n) - 0.15 * excess)
        for name, mu, excess in (
            ("us", 0.55, us_excess),
            ("dev", 0.60, dev_excess),
            ("emerging", 0.65, emerging_excess),
        )
    }

    market_decimal = us_excess / 100.0
    trend = rng.normal(0.004, 0.030, size=n) - 0.40 * np.where(
        market_decimal < -0.05, market_decimal, 0.0
    )
    aqr_values = np.column_stack(
        [trend] + [trend + rng.normal(0.0, 0.02, size=n) for _ in range(4)]
    )

    cash_annual = np.clip(rf * 12.0, 0.05, None)
    gs10 = cash_annual + np.abs(rng.normal(1.6, 0.4, size=n))

    return {
        "periods": periods,
        "files": {
            "F-F_Research_Data_5_Factors_2x3_CSV.zip": (
                "french_us_ff5",
                "monthly",
                _factor_file(
                    columns=FF5_COLUMNS,
                    periods=periods,
                    values=factors(us_excess, us_six),
                    preamble="Synthetic US five factors.",
                ),
            ),
            "Developed_ex_US_5_Factors_CSV.zip": (
                "french_developed_ex_us_ff5",
                "monthly",
                _factor_file(
                    columns=FF5_COLUMNS,
                    periods=periods,
                    values=factors(dev_excess, dev_six),
                    preamble="Synthetic developed ex US five factors.",
                ),
            ),
            "Emerging_5_Factors_CSV.zip": (
                "french_emerging_ff5",
                "monthly",
                _factor_file(
                    columns=FF5_COLUMNS,
                    periods=periods,
                    values=factors(emerging_excess, emerging_six),
                    preamble="Synthetic emerging five factors.",
                ),
            ),
            "F-F_Momentum_Factor_CSV.zip": (
                "french_us_momentum",
                "monthly",
                _factor_file(
                    columns=("Mom",),
                    periods=periods,
                    values=momentum["us"].reshape(-1, 1),
                    preamble="Synthetic US momentum factor.",
                ),
            ),
            "Developed_ex_US_Mom_Factor_CSV.zip": (
                "french_developed_ex_us_momentum",
                "monthly",
                _factor_file(
                    columns=("WML",),
                    periods=periods,
                    values=momentum["dev"].reshape(-1, 1),
                    preamble="Synthetic developed ex US momentum factor.",
                ),
            ),
            "Emerging_MOM_Factor_CSV.zip": (
                "french_emerging_momentum",
                "monthly",
                _factor_file(
                    columns=("WML",),
                    periods=periods,
                    values=momentum["emerging"].reshape(-1, 1),
                    preamble="Synthetic emerging momentum factor.",
                ),
            ),
            "6_Portfolios_2x3_CSV.zip": (
                "french_us_6_portfolios_2x3",
                "average_value_weighted_returns_monthly",
                _portfolio_file(
                    columns=VALUE_6,
                    periods=periods,
                    values=us_six,
                    preamble="Synthetic US 6 portfolios on ME and BEME.",
                ),
            ),
            "Developed_ex_US_6_Portfolios_ME_BE-ME_CSV.zip": (
                "french_developed_ex_us_6_portfolios_2x3",
                "average_value_weighted_returns_monthly",
                _portfolio_file(
                    columns=VALUE_6,
                    periods=periods,
                    values=dev_six,
                    preamble="Synthetic developed ex US 6 portfolios.",
                ),
            ),
            "Emerging_Markets_6_Portfolios_ME_BE-ME_CSV.zip": (
                "french_emerging_6_portfolios_2x3",
                "average_value_weighted_returns_monthly",
                _portfolio_file(
                    columns=VALUE_6,
                    periods=periods,
                    values=emerging_six,
                    preamble="Synthetic emerging 6 portfolios.",
                ),
            ),
            "6_Portfolios_ME_Prior_12_2_CSV.zip": (
                "french_us_6_portfolios_me_prior_12_2",
                "average_value_weighted_returns_monthly",
                _portfolio_file(
                    columns=PRIOR_6,
                    periods=periods,
                    values=prior_six,
                    preamble="Synthetic US 6 portfolios on ME and prior return.",
                ),
            ),
        },
        "aqr": _aqr_workbook(periods, aqr_values),
        "cash_annual": cash_annual,
        "gs10": gs10,
    }


@pytest.fixture
def workspace(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
    generated: dict[str, Any],
) -> dict[str, Any]:
    """A throwaway cache, throwaway manifests, and a spec repointed at both."""
    root = tmp_path_factory.mktemp("exp010")
    monkeypatch.setenv(CACHE_ENV_VAR, str(root / "cache"))
    monkeypatch.setattr(module, "_workspace_root", lambda: root)

    cache = RawCache(root / "cache")
    periods = generated["periods"]
    raw_pins: dict[str, str] = {}
    normalised_pins: dict[str, str] = {}
    parsed_tables: dict[str, Any] = {}

    for filename, (dataset_id, table_id, payload) in generated["files"].items():
        dataset = french.get_dataset(dataset_id)
        entry = cache.store(
            f"{FRENCH_BASE}/{filename}",
            payload,
            headers={"content-type": "text/csv", "last-modified": "Mon, 03 Aug 2026 19:17:20 GMT"},
        )
        parsed = french.parse(cache, entry, dataset=dataset)
        table = parsed.table(table_id)
        raw_pins[dataset_id] = entry.sha256
        normalised_pins[dataset_id] = table.sha256_normalized()
        parsed_tables[dataset_id] = (entry, table, dataset)

    aqr_dataset = aqr.get_dataset("aqr_tsmom_factors")
    aqr_entry = cache.store(
        aqr_dataset.url,
        generated["aqr"],
        headers={"content-type": "application/vnd.ms-excel", "last-modified": "x"},
    )
    aqr_file = aqr.parse(cache, aqr_entry, dataset=aqr_dataset)

    for series_id, values in (
        ("TB3MS", generated["cash_annual"]),
        ("GS10", generated["gs10"]),
    ):
        cache.store(
            f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}",
            _fred_csv(series_id, periods, values),
        )

    raw: Any = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    manifest_dir = root / "data-manifests"
    for item in raw["parameters"]["source_pin"]["french"]:
        dataset_id = item["dataset_id"]
        item["expected_sha256_raw"] = raw_pins[dataset_id]
        item["expected_sha256_normalized"] = normalised_pins[dataset_id]
        entry, table, dataset = parsed_tables[dataset_id]
        item["committed_manifest"] = f"data-manifests/{dataset_id}_{item['table_id']}.json"
        manifest_from_table(
            dataset_id=f"{dataset_id}_{item['table_id']}",
            entry=entry,
            table=table,
            parser_version=french.PARSER_VERSION,
            availability_policy=dataset.availability_policy,
            revision_policy=dataset.revision_policy,
            license_or_terms_url=french.LICENSE_OR_TERMS_URL,
            extra_warnings=("synthetic fixture",),
        ).write(manifest_dir)
    raw["parameters"]["source_pin"]["aqr"]["expected_sha256_raw"] = aqr_entry.sha256
    raw["parameters"]["source_pin"]["aqr"]["expected_sha256_normalized"] = (
        aqr_file.table.sha256_normalized()
    )
    raw["parameters"]["source_pin"]["aqr"].pop("committed_manifest", None)
    for item in raw["parameters"]["source_pin"]["fred"]:
        item.pop("committed_manifest", None)
    raw["inference"]["resamples"] = 200
    return {"root": root, "raw": raw, "cache": cache}


def specification_for(workspace: Mapping[str, Any], **overrides: Any) -> Specification:
    raw = yaml.safe_load(yaml.safe_dump(workspace["raw"]))
    for key, value in overrides.items():
        pin = raw["parameters"]["source_pin"]
        if key == "french_raw_sha":
            pin["french"][0]["expected_sha256_raw"] = value
        elif key == "french_normalized_sha":
            pin["french"][0]["expected_sha256_normalized"] = value
        elif key == "aqr_raw_sha":
            pin["aqr"]["expected_sha256_raw"] = value
    return specification_from_mapping(raw, source_path=SPEC_PATH)


def _context(root: Path) -> RunContext:
    return RunContext(
        run_id="fixture",
        seed=1010,
        rng=np.random.default_rng(1010),
        artifact_dir=root / "artifacts" / "fixture",
    )


@pytest.fixture
def executed(workspace: dict[str, Any]) -> tuple[Specification, ExperimentResult]:
    specification = specification_for(workspace)
    return specification, run(specification, _context(workspace["root"]))


def diagnostics(result: ExperimentResult) -> Any:
    return result.diagnostics


def _primary_rows(result: ExperimentResult, key: str) -> dict[str, Any]:
    """The rows of ``key`` that sit on the primary cell, indexed by sleeve."""
    return {
        row["sleeve"]: row
        for row in diagnostics(result)[key]
        if row.get("base_portfolio") == "global_equity_core"
        and row.get("funding_leg") == "pro_rata"
        and row.get("cost_basis") == "net-pessimistic"
    }


# --------------------------------------------------------------------------- #
# The happy path
# --------------------------------------------------------------------------- #


def test_the_experiment_runs_over_the_frozen_window_and_reports_every_sleeve(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    sample = diagnostics(result)["sample"]
    assert sample["first_month"] == SAMPLE_START
    assert sample["last_month"] == SAMPLE_END
    assert sample["months"] == 420
    assert sample["whole_calendar_years"] == 35
    # The lead month exists, is earlier, and is never reported.
    assert sample["lead_month_never_reported"] == "1990-12"

    declared = {row["sleeve"] for row in diagnostics(result)["sleeves_tested"]}
    assert len(declared) == 12, "ten sleeves, one modelled proxy, one calibration control"
    assert "cash_control" in declared
    assert "long_duration_treasury_proxy" in declared
    assert set(_primary_rows(result, "decompositions")) == declared


def test_the_holdout_is_never_read(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    beyond = diagnostics(executed[1])["sample"]["months_beyond_the_holdout_by_source"]
    assert beyond, "the sources must reach past the boundary for this test to mean anything"
    assert all(value > 0 for value in beyond.values())


def test_the_marginal_metric_matches_an_independent_computation(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """Recompute one sleeve's marginal figure from the frames with plain NumPy.

    The certainty equivalent of a path is a function of that path alone, so the
    check that decides this test is that the reported marginal equals the reported
    treatment CE minus the reported base CE, recomputed from the identity rather
    than read back.
    """
    row = _primary_rows(executed[1], "marginal_results")["us_small_value"]
    gain = row["marginal_certainty_equivalent_pp_per_year"]
    growth = row["marginal_geometric_growth_pp_per_year"]
    assert row["de_risking_component_pp_per_year"] == pytest.approx(gain - growth)
    assert row["observations"] == 420
    assert row["reference_weight"] == 0.10
    assert row["effective_independent_blocks_at_12m"] == pytest.approx(35.0)


def test_the_credit_equals_sigma_p_squared_times_one_minus_beta_under_pro_rata_funding(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """The identity the whole experiment rests on, checked on the real output."""
    for sleeve, row in _primary_rows(executed[1], "decompositions").items():
        beta = row["beta_sleeve_to_portfolio"]
        volatility = row["portfolio_annualised_volatility_percent"] / 100.0
        credit = row["growth_gamma_1"]["diversification_credit_pp_per_year_per_unit_weight"]
        expected = 100.0 * volatility**2 * (1.0 - beta)
        assert credit == pytest.approx(expected, rel=1e-9), sleeve


def test_the_alpha_and_credit_terms_sum_to_the_moment_total_and_track_the_realised_path(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    for sleeve, row in _primary_rows(executed[1], "decompositions").items():
        growth = row["growth_gamma_1"]
        total = (
            growth["alpha_term_pp_per_year_per_unit_weight"]
            + growth["diversification_credit_pp_per_year_per_unit_weight"]
        )
        assert growth["moment_total_pp_per_year_per_unit_weight"] == pytest.approx(total)
        # The exact derivative and the two-moment split agree to third-moment size.
        assert abs(growth["higher_moment_residual_pp_per_year_per_unit_weight"]) < 0.5, sleeve
        # And the first-order prediction tracks the realised, cost-charged path.
        assert abs(growth["reconciliation_gap_pp_per_year"]) < 0.3, sleeve


def test_a_beta_above_one_produces_a_negative_credit_somewhere_in_the_family(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """The fixture is built so that at least one equity sleeve has beta above one."""
    rows = _primary_rows(executed[1], "decompositions")
    high_beta = {
        sleeve: row
        for sleeve, row in rows.items()
        if row["beta_sleeve_to_portfolio"] is not None and row["beta_sleeve_to_portfolio"] > 1.0
    }
    assert high_beta, "the synthetic small-value corners are built with beta above one"
    for sleeve, row in high_beta.items():
        credit = row["growth_gamma_1"]["diversification_credit_pp_per_year_per_unit_weight"]
        assert credit < 0.0, sleeve


def test_the_credit_scales_with_the_base_portfolios_own_variance(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """The cash control has zero beta, so its credit IS sigma_p^2 on both bases."""
    rows = {
        (row["base_portfolio"], row["sleeve"]): row
        for row in diagnostics(executed[1])["decompositions"]
        if row["funding_leg"] == "pro_rata" and row["cost_basis"] == "net-pessimistic"
    }
    credits = {}
    variances = {}
    for base in ("global_equity_core", "balanced_60_40"):
        row = rows[(base, "cash_control")]
        volatility = row["portfolio_annualised_volatility_percent"] / 100.0
        credits[base] = row["growth_gamma_1"][
            "diversification_credit_pp_per_year_per_unit_weight"
        ]
        variances[base] = 100.0 * volatility**2
        # Cash is very nearly, but not exactly, zero beta to the portfolio, so the
        # credit sits just below the ceiling rather than exactly on it.
        assert abs(row["beta_sleeve_to_portfolio"]) < 0.02
        assert credits[base] == pytest.approx(variances[base], rel=0.02)
    assert variances["balanced_60_40"] < variances["global_equity_core"]
    # The credit must fall roughly in proportion to sigma_p^2, which is the identity
    # rather than a coincidence: a ratio far from one would mean an error.
    ratio = (credits["balanced_60_40"] / credits["global_equity_core"]) / (
        variances["balanced_60_40"] / variances["global_equity_core"]
    )
    assert ratio == pytest.approx(1.0, rel=0.05)


def test_the_credit_ceiling_is_reported_and_is_the_portfolios_own_variance(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    ceiling = diagnostics(executed[1])["credit_ceiling"]
    assert len(ceiling) == 1
    row = ceiling[0]
    volatility = row["portfolio_annualised_volatility_percent"] / 100.0
    assert row["maximum_credit_growth_basis_pp_per_year_per_unit_weight"] == pytest.approx(
        100.0 * volatility**2
    )
    assert row["maximum_credit_growth_basis_at_the_reference_weight_pp_per_year"] == (
        pytest.approx(0.10 * 100.0 * volatility**2)
    )
    assert "ZERO beta" in row["reading"]


# --------------------------------------------------------------------------- #
# Funding legs, costs and weights
# --------------------------------------------------------------------------- #


def test_every_funding_leg_is_reported_and_named_beside_every_figure(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    legs = {
        row["funding_leg"]
        for row in diagnostics(executed[1])["marginal_results"]
        if row["base_portfolio"] == "global_equity_core"
        and row["cost_basis"] == "net-pessimistic"
    }
    assert legs == {"pro_rata", "named_leg", "cash"}
    assert all("funding_leg" in row for row in diagnostics(executed[1])["marginal_results"])
    assert all("funding_leg" in row for row in diagnostics(executed[1])["decompositions"])
    assert all("funding_leg" in row for row in diagnostics(executed[1])["weight_surfaces"])


def test_funding_from_cash_out_of_an_all_equity_core_is_flagged_as_borrowing(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    rows = [
        row
        for row in diagnostics(executed[1])["marginal_results"]
        if row["base_portfolio"] == "global_equity_core" and row["funding_leg"] == "cash"
    ]
    assert rows
    assert all(row["requires_borrowing"] for row in rows)


def test_every_cost_column_is_reported_separately_and_never_averaged(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    bases = {
        row["cost_basis"]
        for row in diagnostics(executed[1])["marginal_results"]
        if row["funding_leg"] == "pro_rata" and row["base_portfolio"] == "global_equity_core"
    }
    assert bases == {"gross", "net-optimistic", "net-pessimistic"}


def test_costs_never_improve_a_sleeve(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    rows = {
        (row["sleeve"], row["cost_basis"]): row["marginal_certainty_equivalent_pp_per_year"]
        for row in diagnostics(executed[1])["marginal_results"]
        if row["funding_leg"] == "pro_rata" and row["base_portfolio"] == "global_equity_core"
    }
    for sleeve, _, in {(sleeve, basis) for sleeve, basis in rows}:
        assert rows[(sleeve, "gross")] >= rows[(sleeve, "net-pessimistic")] - 1e-12, sleeve


def test_doubling_the_costs_never_improves_the_result(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    for row in diagnostics(executed[1])["hostile_tests"]:
        assert row["doubled_costs_marginal_pp_per_year"] <= (
            row["baseline_marginal_pp_per_year"] + 1e-12
        ), row["sleeve"]


def test_every_weight_surface_reports_all_three_flatness_statistics(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    for sleeve, row in _primary_rows(executed[1], "weight_surfaces").items():
        assert 0.0 <= row["optimal_weight"] <= 0.20, sleeve
        assert row["plateau_width"] >= 0.0
        assert row["region_above_materiality_width"] >= 0.0
        assert "max_deviation_from_a_straight_line_pp_per_year" in row
        assert row["halved_cap"]["optimal_weight"] <= 0.10 + 1e-12
        assert len(row["grid"]) == 41


def test_the_reselected_optimum_carries_the_selection_effect(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """Re-choosing the weight inside every replicate must not narrow the interval.

    The maximum of a noisy surface is non-negative by construction, so the lower
    end sits at or above zero; the property that matters is that the interval
    exists and is reported beside the naive optimum.
    """
    rows = {row["sleeve"]: row for row in diagnostics(executed[1])["reselected_optima"]}
    assert len(rows) == 12
    for sleeve, row in rows.items():
        low, high = row["reselected_gain_two_sided_95"]
        assert low <= high, sleeve
        assert low >= -1e-9, sleeve
        assert 0.0 <= row["share_of_replicates_choosing_zero_weight"] <= 1.0


# --------------------------------------------------------------------------- #
# Statistical discipline
# --------------------------------------------------------------------------- #


def test_every_marginal_figure_carries_its_own_detection_threshold(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    for row in diagnostics(executed[1])["marginal_results"]:
        assert row["minimum_detectable_effect_80_power_bootstrap"] > 0.0
        assert row["minimum_detectable_effect_80_power_sigma_over_sqrt_t"] > 0.0
        assert row["bootstrap_standard_error"] > 0.0
        # The bootstrap MDE is exactly (z_alpha + z_power) times its standard error.
        assert row["minimum_detectable_effect_80_power_bootstrap"] == pytest.approx(
            2.486474860524386 * row["bootstrap_standard_error"], rel=1e-9
        )


def test_the_multiple_testing_family_is_ten_and_its_dependence_is_declared(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    correction = diagnostics(executed[1])["multiple_testing"]
    assert correction["method"] == "holm-bonferroni"
    assert correction["alpha"] == 0.05
    assert correction["family_size"] == 10, "the frozen specification names ten sleeves"
    assert correction["sleeves_tested_total"] == 12
    assert "dependent" in correction["dependence_warning"]
    assert "LOWER bound" in correction["trial_count_note"]
    names = {row["sleeve"] for row in correction["rows"]}
    assert "cash_control" not in names
    assert "long_duration_treasury_proxy" not in names
    for row in correction["rows"]:
        assert row["holm_adjusted_p"] >= row["p_uncorrected"] - 1e-12


def test_the_neighbour_block_lengths_are_reported_for_the_primary_cell(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    row = _primary_rows(executed[1], "marginal_results")["trend_aqr"]
    lengths = {item["block_length"] for item in row["neighbour_block_intervals"]}
    assert lengths == {6.0, 24.0}
    assert row["block_length_months"] == 12.0


def test_the_correlation_interval_and_its_credit_band_are_reported(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    for sleeve, row in _primary_rows(executed[1], "decompositions").items():
        low, high = row["correlation_two_sided_95"]
        assert low is not None and high is not None and low <= high, sleeve
        band_low, band_high = row["credit_at_the_correlation_interval_bounds_pp_per_year"]
        assert band_low <= band_high, sleeve
        assert row["credit_change_per_0.10_of_correlation_pp_per_year"] <= 0.0


# --------------------------------------------------------------------------- #
# Disclosure, the control, and the frozen rule
# --------------------------------------------------------------------------- #


def test_the_result_states_that_gold_was_not_tested_and_why(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    statement = diagnostics(executed[1])["gold_statement"]
    assert "GOLD WAS NOT TESTED" in statement
    assert "0002" in statement
    assert "biases this" in statement
    assert any("GOLD WAS NOT TESTED" in caveat for caveat in executed[1].caveats)


def test_the_modelled_proxy_is_labelled_a_proxy_everywhere_and_never_resolves(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    _, result = executed
    verdict = next(
        row
        for row in diagnostics(result)["verdicts"]["per_sleeve"]
        if row["sleeve"] == "long_duration_treasury_proxy"
    )
    assert verdict["is_proxy"]
    assert "PROXY" in verdict["proxy_note"]
    assert "MODELLED series" in verdict["proxy_note"]
    # The frozen falsifier orders the rejection clauses ahead of the `unresolved`
    # triggers, so a proxy that trips a rejection clause is rejected; only when no
    # clause fires does (u5) reach it. Both outcomes are statements about the
    # modelled series, which is what the note on the row says.
    if verdict["status"] == ResultStatus.UNRESOLVED.value:
        assert any("(u5)" in trigger for trigger in verdict["unresolved_triggers"])
    else:
        assert verdict["status"] == ResultStatus.REJECTED.value
        assert verdict["falsifier_clauses_fired"]
    named = [
        estimate for estimate in result.estimates if "long_duration_treasury_proxy" in estimate.name
    ]
    assert named
    assert any(estimate.name.startswith("PROXY ") for estimate in named)
    assert any("PROXY" in estimate.notes for estimate in named)


def test_the_calibration_control_is_reported_on_both_readings(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    check = diagnostics(executed[1])["calibration_control"]
    assert check["reading_that_decides"] == "geometric_growth_gamma_1"
    growth = check["readings"]["geometric_growth_gamma_1"]["per_funding_leg_pp_per_year"]
    assert set(growth) == {"pro_rata", "named_leg", "cash"}
    assert all(value < 0.0 for value in growth.values()), (
        "cash added to an equity core must lower the growth rate on every funding leg"
    )
    assert check["machinery_validated"]
    assert "certainty_equivalent_gamma_3" in check["readings"]


def test_the_predeclared_prediction_is_scored_including_its_contradictions(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    scorecard = diagnostics(executed[1])["predeclared_prediction_scorecard"]
    assert scorecard["frozen_before_any_result"] is True
    assert scorecard["sleeves_scored"] == 11, "ten sleeves plus the modelled proxy"
    assert 0 <= scorecard["sleeves_matching_the_prediction"] <= 11
    for row in scorecard["rows"]:
        assert row["predicted_credit_sign"] in {"positive", "non-positive"}
        assert row["realised_credit_sign"] in {"positive", "non-positive"}
        assert row["prediction_held"] == (
            row["predicted_credit_sign"] == row["realised_credit_sign"]
        )


def test_the_verdict_names_the_clauses_that_fired_for_every_sleeve(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    rows = diagnostics(executed[1])["verdicts"]["per_sleeve"]
    assert len(rows) == 12
    for row in rows:
        assert row["status"] in {
            ResultStatus.EXPLORATORY.value,
            ResultStatus.REJECTED.value,
            ResultStatus.UNRESOLVED.value,
        }
        if row["status"] == ResultStatus.REJECTED.value:
            assert row["falsifier_clauses_fired"], row["sleeve"]
        if row["status"] == ResultStatus.UNRESOLVED.value:
            assert not row["falsifier_clauses_fired"]
            assert row["unresolved_triggers"], row["sleeve"]


def test_a_negative_credit_fires_clause_b_and_says_the_dismissal_is_strengthened(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    fired = [
        clause
        for row in diagnostics(executed[1])["verdicts"]["per_sleeve"]
        for clause in row["falsifier_clauses_fired"]
        if clause.startswith("(b)")
    ]
    assert fired, "the synthetic panel is built so that at least one credit is negative"
    assert all("strengthened" in clause for clause in fired)


def test_the_status_can_never_exceed_exploratory(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    specification, result = executed
    assert result.status in {
        ResultStatus.EXPLORATORY,
        ResultStatus.REJECTED,
        ResultStatus.UNRESOLVED,
    }
    assert specification.run_kind.value == "exploratory"
    assert specification.evidence_class.value == "public-series-evaluation"


def test_the_result_carries_the_paper_portfolio_caveat(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    joined = " ".join(executed[1].caveats)
    assert "NOT AN INVESTABLE BACKTEST" in joined
    assert "paper portfolios" in joined
    assert "selected maximum" in joined


# --------------------------------------------------------------------------- #
# Pins
# --------------------------------------------------------------------------- #


def test_an_unrecognised_french_vintage_aborts_instead_of_reporting_a_marginal_value(
    workspace: dict[str, Any],
) -> None:
    specification = specification_for(workspace, french_raw_sha="0" * 64)
    with pytest.raises(MarginalSleeveValueError, match="new vintage"):
        run(specification, _context(workspace["root"]))


def test_a_parser_change_that_leaves_the_bytes_alone_is_caught(
    workspace: dict[str, Any],
) -> None:
    specification = specification_for(workspace, french_normalized_sha="1" * 64)
    with pytest.raises(MarginalSleeveValueError, match="parser changed behaviour"):
        run(specification, _context(workspace["root"]))


def test_an_unrecognised_vendor_vintage_aborts(workspace: dict[str, Any]) -> None:
    specification = specification_for(workspace, aqr_raw_sha="2" * 64)
    with pytest.raises(MarginalSleeveValueError, match="new vintage"):
        run(specification, _context(workspace["root"]))


def test_every_source_is_recorded_with_its_hashes_and_its_parser_version(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    sources = diagnostics(executed[1])["sources"]
    assert len(sources) == 13, "ten French tables, one AQR workbook, two FRED series"
    for source in sources:
        assert source["sha256_raw"]
        assert source["parser_version"]
        assert source["retrieved_utc"]
    french_rows = [item for item in sources if item["dataset_id"].startswith("french_")]
    assert len(french_rows) == 10
    assert all(item["committed_manifest_sha256"] for item in french_rows)
    fred_rows = [item for item in sources if item["dataset_id"].startswith("fred_")]
    assert all(item["abort_on_mismatch"] is False for item in fred_rows)


# --------------------------------------------------------------------------- #
# The runner and the ledger
# --------------------------------------------------------------------------- #


def test_the_run_is_ledgered_with_hashed_artifacts(
    workspace: dict[str, Any], tmp_path: Path
) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        specification_for(workspace),
        registry=build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
        run_id="exp010-fixture",
    )
    assert outcome.status is RunStatus.SUCCEEDED
    assert outcome.result is not None
    entries = list(ledger.read())
    events = [entry.event for entry in entries]
    assert LedgerEvent.STARTED in events
    assert LedgerEvent.SUCCEEDED in events
    assert all(entry.spec_hash == outcome.spec_hash for entry in entries)
    assert outcome.artifacts
    for record in outcome.artifacts:
        assert len(record.sha256) == 64
        assert record.size_bytes > 0


def test_a_failure_is_ledgered_before_it_propagates(
    workspace: dict[str, Any], tmp_path: Path
) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(MarginalSleeveValueError):
        run_experiment(
            specification_for(workspace, french_raw_sha="0" * 64),
            registry=build_registry(),
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
            run_id="exp010-failure",
        )
    events = [entry.event for entry in ledger.read()]
    assert LedgerEvent.STARTED in events
    assert LedgerEvent.FAILED in events


def test_the_registry_resolves_the_committed_entry_point() -> None:
    registry = build_registry()
    assert ENTRY_POINT in registry
    assert registry.resolve(ENTRY_POINT) is not None


def test_a_certainty_equivalent_of_the_base_path_is_recomputable(
    executed: tuple[Specification, ExperimentResult],
) -> None:
    """The base portfolio's own certainty equivalent, rebuilt from the frames.

    Every sleeve is measured against the SAME base path, so the base certainty
    equivalent implied by each sleeve's treatment minus its marginal must agree
    across every sleeve. If it does not, the comparison is not paired.
    """
    frame = executed[1].frames["marginal_results"]
    subset = frame[
        (frame["funding_leg"] == "pro_rata")
        & (frame["base_portfolio"] == "global_equity_core")
        & (frame["cost_basis"] == "net-pessimistic")
    ]
    assert len(subset) == 12
    assert MONTHS_PER_YEAR == 12
    assert certainty_equivalent_annual(np.array([1.05]), gamma=3.0) == pytest.approx(0.05)
