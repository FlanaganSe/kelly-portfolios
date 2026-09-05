"""The site's series are the artifacts' series, and the summaries are arithmetic.

Two kinds of test. The summary statistics are checked on a path built by hand, so the
expected values here come from plain arithmetic and never from the code under test.
The committed JSON files are then checked for shape and against the worst falls the
committed artifact tables print for the two controls, which the emitter rebuilds
exactly. No test here needs the raw data cache.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.experiments.exp_016_construction_tournament import FundMapping
from portfolio_edge.reporting.site_series import (
    EXP_024_RUN,
    EXP_025_RUN,
    PRIMARY_CHECKS,
    SITE_PORTFOLIOS,
    TOURNAMENT_CHECKS,
    SitePortfolio,
    SiteSeriesError,
    calendar_years,
    default_output_dir,
    primary_targets,
    summarise,
    tournament_targets,
    wealth_path,
    worst_fall,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = REPO_ROOT / "research" / "artifacts"

# --------------------------------------------------------------------------- #
# A path built by hand: 2007 up 1% a month, 2008 six months of -10% then flat, 2009 +8%
# --------------------------------------------------------------------------- #

PERIODS = [f"{year}-{month:02d}" for year in (2007, 2008, 2009) for month in range(1, 13)]
RETURNS = np.array([0.01] * 12 + [-0.10] * 6 + [0.0] * 6 + [0.08] * 12, dtype=np.float64)

PEAK = 10_000.0 * 1.01**12
TROUGH = PEAK * 0.9**6
FINAL = TROUGH * 1.08**12


def test_wealth_path_starts_at_ten_thousand_and_compounds() -> None:
    values = wealth_path(RETURNS)
    assert values.size == 37
    assert values[0] == 10_000.0
    assert values[12] == pytest.approx(PEAK)
    assert values[-1] == pytest.approx(FINAL)


def test_worst_fall_reads_peak_trough_and_recovery_months() -> None:
    values = wealth_path(RETURNS)
    dates = ["2006-12", *PERIODS]
    fall = worst_fall(values, dates)
    assert fall["peak"] == "2007-12"
    assert fall["trough"] == "2008-06"
    # 1.08**k >= 1 / 0.9**6 first holds at k = 9, so September 2009; 21 months after the peak.
    assert fall["recovered"] == "2009-09"
    assert fall["monthsToRecover"] == 21
    assert fall["pct"] == round((0.9**6 - 1.0) * 100.0, 1) == -46.9
    assert fall["dollarsAtTrough"] == round(10_000.0 * 0.9**6) == 5314


def test_a_fall_still_open_at_the_end_has_no_recovery() -> None:
    values = np.array([10_000.0, 11_000.0, 9_000.0, 9_500.0])
    fall = worst_fall(values, ["2020-01", "2020-02", "2020-03", "2020-04"])
    assert fall["peak"] == "2020-02"
    assert fall["trough"] == "2020-03"
    assert fall["recovered"] is None
    assert fall["monthsToRecover"] is None


def test_calendar_years_only_for_years_held_in_full() -> None:
    years = calendar_years(RETURNS[6:], PERIODS[6:])
    assert "2007" not in years
    assert years["2008"] == round((0.9**6 - 1.0) * 100.0, 1)
    assert years["2009"] == round((1.08**12 - 1.0) * 100.0, 1)


def test_summarise_by_hand() -> None:
    summary = summarise(RETURNS, PERIODS)
    assert summary["final"] == round(FINAL)
    assert summary["cagrPct"] == round(((FINAL / 10_000.0) ** (12 / 36) - 1.0) * 100.0, 2)
    assert summary["bestYear"] == {"year": 2009, "pct": round((1.08**12 - 1.0) * 100.0, 1)}
    assert summary["worstYear"] == {"year": 2008, "pct": round((0.9**6 - 1.0) * 100.0, 1)}
    episodes = summary["episodes"]
    assert isinstance(episodes, dict)
    assert episodes["gfc-2008"] == round((0.9**6 - 1.0) * 100.0, 1)
    assert episodes["covid-2020"] is None
    assert episodes["dotcom-2000-02"] is None
    since = summary["since2009"]
    assert isinstance(since, dict)
    assert since["start"] == "2009-01"
    assert since["final"] == round(10_000.0 * 1.08**12)
    assert since["cagrPct"] == round((1.08**12 - 1.0) * 100.0, 2)
    assert since["worstFallPct"] == 0.0


def test_summarise_refuses_mismatched_lengths() -> None:
    with pytest.raises(SiteSeriesError):
        summarise(RETURNS[:-1], PERIODS)


# --------------------------------------------------------------------------- #
# Weight vectors and their translation to each panel's tickers
# --------------------------------------------------------------------------- #


def test_every_printed_vector_sums_to_one_hundred() -> None:
    for portfolio in SITE_PORTFOLIOS:
        assert sum(portfolio.weights.values()) == pytest.approx(100.0)
    ids = [p.id for p in SITE_PORTFOLIOS]
    assert ids[:4] == ["one-fund", "value-lean", "with-trend", "cautious"]


def test_the_cautious_vector_holds_nine_and_a_half_points_of_vti() -> None:
    """The page once printed 9.6 and summed to 100.1; the emitter scores what is printed."""
    cautious = next(p for p in SITE_PORTFOLIOS if p.id == "cautious")
    assert cautious.weights["VTI"] == 9.5
    assert cautious.weights["RSST"] == 15


def test_a_vector_that_does_not_sum_to_one_hundred_is_refused() -> None:
    with pytest.raises(SiteSeriesError, match=r"100\.1000"):
        SitePortfolio(id="bad", label="Bad", weights={"VTI": 50, "VXUS": 50.1})


def _mapping(ticker: str) -> FundMapping:
    return FundMapping(
        ticker=ticker,
        coefficients={"us_mkt": 1.0},
        expense_ratio_bp=3.0,
        futures_notional=0.0,
        spread_region="us_equity",
        alpha_less_pedestal_pp_yr=None,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=False,
        fee_assumed=False,
    )


MAPPINGS = {t: _mapping(t) for t in ("VTI", "VXUS", "VTV", "AVDV", "IDMO", "AVES", "RSST", "TSY10")}
PROXY = {"VTI": 0.65, "VXUS": 0.35}


def test_tournament_targets_proxy_vt_and_map_schp_to_the_ten_year() -> None:
    tickers, targets = tournament_targets({"VT": 100}, mappings=MAPPINGS, vt_proxy=PROXY)
    assert dict(zip(tickers, targets.tolist(), strict=True)) == pytest.approx(PROXY)
    tickers, targets = tournament_targets(
        {"SCHP": 40, "VTI": 39, "VXUS": 21}, mappings=MAPPINGS, vt_proxy=PROXY
    )
    assert dict(zip(tickers, targets.tolist(), strict=True)) == pytest.approx(
        {"TSY10": 0.40, "VTI": 0.39, "VXUS": 0.21}
    )
    assert targets.sum() == pytest.approx(1.0)


def test_tournament_targets_refuse_an_unmapped_ticker() -> None:
    with pytest.raises(SiteSeriesError, match="no ticker 'BND'"):
        tournament_targets({"BND": 100}, mappings=MAPPINGS, vt_proxy=PROXY)


def test_primary_targets_collapse_every_stock_fund_into_core() -> None:
    cautious = next(p for p in SITE_PORTFOLIOS if p.id == "cautious")
    tickers, targets = primary_targets(cautious.weights)
    assert dict(zip(tickers, targets.tolist(), strict=True)) == pytest.approx(
        {"TSY10": 0.50, "RSST_LIKE": 0.15, "CORE": 0.35}
    )
    with pytest.raises(SiteSeriesError):
        primary_targets({"GLD": 100})


# --------------------------------------------------------------------------- #
# The committed files
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def files() -> dict[str, dict[str, object]]:
    out_dir = default_output_dir()
    assert out_dir == REPO_ROOT / "src" / "content" / "series"
    return {
        window: json.loads((out_dir / f"portfolios-{window}.json").read_text(encoding="utf-8"))
        for window in ("1990", "1929")
    }


def _items(payload: dict[str, object]) -> list[dict[str, object]]:
    items = payload["series"]
    assert isinstance(items, list)
    for item in items:
        assert isinstance(item, dict)
    return items


def _series(payload: dict[str, object], series_id: str) -> dict[str, object]:
    for item in _items(payload):
        if item["id"] == series_id:
            return item
    raise AssertionError(f"no series {series_id!r}")


def test_committed_files_have_the_schema_shape(files: dict[str, dict[str, object]]) -> None:
    for window, payload in files.items():
        assert payload["start"] == 10_000
        meta = payload["window"]
        assert isinstance(meta, dict)
        assert meta["start"].startswith(window)
        assert "simulated" in str(payload["basis"])
        assert "RSST" in str(payload["basis"]) and "September 2023" in str(payload["basis"])
        provenance = payload["provenance"]
        assert isinstance(provenance, dict)
        assert "exp_025" in provenance["experiments"]
        assert EXP_025_RUN in provenance["artifacts"] and EXP_024_RUN in provenance["artifacts"]
        assert provenance["manifests"]
        items = payload["series"]
        assert isinstance(items, list)
        for item in items:
            assert isinstance(item, dict)
            values, dates = item["values"], item["dates"]
            assert isinstance(values, list) and isinstance(dates, list)
            assert len(values) == len(dates) == int(str(meta["months"])) + 1
            assert values[0] == 10_000
            summary = item["summary"]
            assert isinstance(summary, dict)
            assert summary["final"] == values[-1]
            weights = item["weights"]
            assert isinstance(weights, dict)
            assert sum(weights.values()) == pytest.approx(100.0)


def test_the_1990_file_holds_every_printed_portfolio(files: dict[str, dict[str, object]]) -> None:
    ids = {item["id"] for item in _items(files["1990"])}
    assert ids == {p.id for p in SITE_PORTFOLIOS}
    for portfolio in SITE_PORTFOLIOS:
        assert _series(files["1990"], portfolio.id)["weights"] == dict(portfolio.weights)


def test_the_1929_file_omits_the_value_lean(files: dict[str, dict[str, object]]) -> None:
    ids = {item["id"] for item in _items(files["1929"])}
    assert "value-lean" not in ids
    assert {"one-fund", "with-trend", "cautious", "market"} <= ids
    assert "value lean cannot be shown" in str(files["1929"]["basis"])


def _fall(payload: dict[str, object], series_id: str) -> dict[str, object]:
    summary = _series(payload, series_id)["summary"]
    assert isinstance(summary, dict)
    fall = summary["worstFall"]
    assert isinstance(fall, dict)
    return fall


def test_the_controls_fall_as_the_artifact_tables_print(
    files: dict[str, dict[str, object]],
) -> None:
    """The two controls are the same vectors the artifacts scored, so they must agree."""
    cheap_1990 = next(c for c in TOURNAMENT_CHECKS if c.arm == "control_cheap")
    mix_1990 = next(c for c in TOURNAMENT_CHECKS if c.arm == "control_cheap60_40")
    cheap_1929 = next(c for c in PRIMARY_CHECKS if c.arm == "control_cheap")
    assert _fall(files["1990"], "market")["pct"] == round(cheap_1990.max_drawdown_pct, 1)
    assert _fall(files["1990"], "one-fund")["pct"] == round(cheap_1990.max_drawdown_pct, 1)
    assert _fall(files["1990"], "sixty-forty")["pct"] == round(mix_1990.max_drawdown_pct, 1)
    assert _fall(files["1929"], "market")["pct"] == round(cheap_1929.max_drawdown_pct, 1)
    market = _fall(files["1990"], "market")
    assert (market["peak"], market["trough"], market["recovered"]) == (
        "2007-10",
        "2009-02",
        "2013-01",
    )
    assert market["monthsToRecover"] == 63


# --------------------------------------------------------------------------- #
# The check constants are what the committed tables say
# --------------------------------------------------------------------------- #

ROW = re.compile(r"^\|\s*`?(?P<name>[^`|]+)`?\s*\|")


def _era_rows(tables: str, heading: str) -> dict[str, tuple[float, int]]:
    """``arm -> (worst fall, months)`` from the ``full`` row under a drawdown-by-era heading."""
    lines = tables.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    header = next(line for line in lines[start:] if line.startswith("| era |"))
    names = [c.strip().strip("`") for c in header.strip("|").split("|")]
    full = next(line for line in lines[start:] if line.startswith("| full |"))
    cells = [c.strip() for c in full.strip("|").split("|")]
    out: dict[str, tuple[float, int]] = {}
    for name, cell in zip(names, cells, strict=True):
        match = re.fullmatch(r"(-?\d+(?:\.\d+)?) \((\d+)\)", cell)
        if match:
            out[name] = (float(match.group(1)), int(match.group(2)))
    return out


def _arm_rows(tables: str, arm: str) -> set[tuple[float, int]]:
    """Every ``(max DD %, months under water)`` an arms table prints for ``arm``."""
    out: set[tuple[float, int]] = set()
    dd = months = None
    for line in tables.splitlines():
        if line.startswith("| arm |"):
            names = [c.strip() for c in line.strip("|").split("|")]
            dd = months = None
            if "max DD %" in names and "months under water" in names:
                dd, months = names.index("max DD %"), names.index("months under water")
            continue
        match = ROW.match(line)
        if match and match.group("name").strip() == arm and dd is not None and months is not None:
            cells = [c.strip() for c in line.strip("|").split("|")]
            out.add((float(cells[dd]), int(cells[months])))
    return out


def test_check_constants_match_the_committed_tables() -> None:
    tables_025 = (ARTIFACTS / EXP_025_RUN / "tables.md").read_text(encoding="utf-8")
    tables_024 = (ARTIFACTS / EXP_024_RUN / "tables.md").read_text(encoding="utf-8")
    tournament = _era_rows(tables_025, "### Drawdown by era, tournament panel")
    primary = _era_rows(tables_025, "### Drawdown by era, primary panel")
    for check in TOURNAMENT_CHECKS:
        expected = (
            _arm_rows(tables_024, "working_default")
            if check.arm == "working_default"
            else {tournament[check.arm]}
        )
        assert (check.max_drawdown_pct, check.months_under_water) in expected, check
    for check in PRIMARY_CHECKS:
        expected = (
            _arm_rows(tables_024, "working_default")
            if check.arm == "working_default"
            else {primary[check.arm]}
        )
        assert (check.max_drawdown_pct, check.months_under_water) in expected, check
