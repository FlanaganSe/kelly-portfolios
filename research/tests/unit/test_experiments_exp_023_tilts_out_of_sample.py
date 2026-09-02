"""Unit tests for Experiment 023, the tilt complex out of sample on VME.

Every expected value is computed here by hand or with plain NumPy, never by
calling the code under test on the same inputs. The basis-mapping fixture is
the load-bearing one: it derives the net active exposure of the complex over
the control from 016e's coefficients, fund by fund, and the module must agree.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pytest

from portfolio_edge.experiments.exp_016_construction_tournament import MDE_MULTIPLIER
from portfolio_edge.experiments.exp_023_tilts_out_of_sample import (
    Arm,
    ArmResult,
    GapSummary,
    SeriesStore,
    TiltsOutOfSampleError,
    active_exposure,
    aligned,
    apply_falsifier,
    cost_difference_bp,
    default_specification_path,
    gap_summary,
    read_arms,
    read_mappings,
)
from portfolio_edge.experiments.specification import Specification, load_specification
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(default_specification_path())


# --------------------------------------------------------------------------- #
# The basis mapping, by hand
# --------------------------------------------------------------------------- #

# 016e's coefficients, transcribed independently of the specification file.
VTI_HML = 0.0247
VTV_HML = 0.337
AVDV = {
    "dxus_hml": 0.510,
    "dxus_smb": 0.671,
    "dxus_rmw": 0.386,
    "dxus_cma": -0.114,
    "dxus_umd": 0.008,
}
IDMO = {
    "dxus_umd": 0.540,
    "dxus_hml": 0.218,
    "dxus_smb": -0.164,
    "dxus_rmw": 0.040,
    "dxus_cma": -0.394,
}
AVES_EM_HML = 0.237

# Complex VTI 49 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5; control VTI 65 / VXUS 35.
US_VALUE = 0.15 * VTV_HML + (0.49 - 0.65) * VTI_HML  # 0.05055 - 0.003952
DEV_VALUE = 0.10 * AVDV["dxus_hml"] + 0.05 * IDMO["dxus_hml"]  # 0.0510 + 0.0109
DEV_MOMENTUM = 0.05 * IDMO["dxus_umd"] + 0.10 * AVDV["dxus_umd"]  # 0.0270 + 0.0008
AVES_VALUE = 0.05 * AVES_EM_HML  # 0.01185
DEV_SMB = 0.10 * AVDV["dxus_smb"] + 0.05 * IDMO["dxus_smb"]
DEV_RMW = 0.10 * AVDV["dxus_rmw"] + 0.05 * IDMO["dxus_rmw"]
DEV_CMA = 0.10 * AVDV["dxus_cma"] + 0.05 * IDMO["dxus_cma"]
# Market residual: complex 64 / 27 / 9 against control 65 / 26.25 / 8.75.
RESIDUAL_US = (0.49 + 0.15) - 0.65
RESIDUAL_DXUS = (0.16 * 0.75 + 0.10 + 0.05) - 0.35 * 0.75
RESIDUAL_EM = (0.16 * 0.25 + 0.05) - 0.35 * 0.25


def test_hand_fixture_is_what_the_freeze_note_says() -> None:
    assert pytest.approx(0.046598, abs=1e-6) == US_VALUE
    assert pytest.approx(0.0619, abs=1e-6) == DEV_VALUE
    assert pytest.approx(0.0278, abs=1e-6) == DEV_MOMENTUM
    assert pytest.approx(-0.01, abs=1e-9) == RESIDUAL_US
    assert pytest.approx(0.0075, abs=1e-9) == RESIDUAL_DXUS
    assert pytest.approx(0.0025, abs=1e-9) == RESIDUAL_EM


def test_vme_exposure_aves_dropped_matches_the_hand_fixture(specification: Specification) -> None:
    mappings = read_mappings(specification)
    exposure = active_exposure(mappings, basis="vme", aves="dropped")
    assert set(exposure) == {"us_val", "dev_val", "dev_mom"}
    assert exposure["us_val"] == pytest.approx(US_VALUE, abs=1e-9)
    assert exposure["dev_val"] == pytest.approx(DEV_VALUE, abs=1e-9)
    assert exposure["dev_mom"] == pytest.approx(DEV_MOMENTUM, abs=1e-9)


def test_vme_exposure_aves_on_developed_value_adds_its_leg(specification: Specification) -> None:
    mappings = read_mappings(specification)
    exposure = active_exposure(mappings, basis="vme", aves="developed_value")
    assert exposure["dev_val"] == pytest.approx(DEV_VALUE + AVES_VALUE, abs=1e-9)
    assert exposure["us_val"] == pytest.approx(US_VALUE, abs=1e-9)
    assert exposure["dev_mom"] == pytest.approx(DEV_MOMENTUM, abs=1e-9)


def test_bridged_exposure_scales_each_leg_by_its_pinned_slope(specification: Specification) -> None:
    mappings = read_mappings(specification)
    bridged = active_exposure(mappings, basis="vme", aves="dropped", scaling="bridged")
    assert bridged["us_val"] == pytest.approx(US_VALUE * 0.532, abs=1e-9)
    assert bridged["dev_val"] == pytest.approx(DEV_VALUE * 0.564, abs=1e-9)
    assert bridged["dev_mom"] == pytest.approx(DEV_MOMENTUM * 0.876, abs=1e-9)


def test_french_mapped_only_exposure_carries_the_three_legs_and_aves(
    specification: Specification,
) -> None:
    mappings = read_mappings(specification)
    exposure = active_exposure(mappings, basis="french", aves="emerging_value")
    assert set(exposure) == {"us_hml", "dxus_hml", "dxus_umd"}
    assert exposure["us_hml"] == pytest.approx(US_VALUE, abs=1e-9)
    assert exposure["dxus_hml"] == pytest.approx(DEV_VALUE, abs=1e-9)
    assert exposure["dxus_umd"] == pytest.approx(DEV_MOMENTUM, abs=1e-9)


def test_french_complete_exposure_adds_unmapped_legs_and_the_residual(
    specification: Specification,
) -> None:
    mappings = read_mappings(specification)
    exposure = active_exposure(mappings, basis="french", aves="emerging_value", complete=True)
    assert exposure["em_hml"] == pytest.approx(AVES_VALUE, abs=1e-9)
    assert exposure["dxus_smb"] == pytest.approx(DEV_SMB, abs=1e-9)
    assert exposure["dxus_rmw"] == pytest.approx(DEV_RMW, abs=1e-9)
    assert exposure["dxus_cma"] == pytest.approx(DEV_CMA, abs=1e-9)
    assert exposure["us_mkt"] == pytest.approx(RESIDUAL_US, abs=1e-9)
    assert exposure["dxus_mkt"] == pytest.approx(RESIDUAL_DXUS, abs=1e-9)
    assert exposure["em_mkt"] == pytest.approx(RESIDUAL_EM, abs=1e-9)


def test_loading_delta_moves_magnitudes_and_keeps_signs(specification: Specification) -> None:
    mappings = read_mappings(specification)
    up = active_exposure(mappings, basis="vme", aves="dropped", loading_delta=0.15)
    # US value: VTV 0.15 * (0.337 + 0.15) + (0.49 - 0.65) * (0.0247 + 0.15).
    assert up["us_val"] == pytest.approx(0.15 * 0.487 - 0.16 * 0.1747, abs=1e-9)
    # Developed momentum: IDMO 0.05 * 0.690 + AVDV 0.10 * 0.158.
    assert up["dev_mom"] == pytest.approx(0.05 * 0.690 + 0.10 * 0.158, abs=1e-9)


def test_illegal_basis_and_aves_combinations_raise(specification: Specification) -> None:
    mappings = read_mappings(specification)
    with pytest.raises(TiltsOutOfSampleError):
        active_exposure(mappings, basis="vme", aves="emerging_value")
    with pytest.raises(TiltsOutOfSampleError):
        active_exposure(mappings, basis="french", aves="developed_value")
    with pytest.raises(TiltsOutOfSampleError):
        active_exposure(mappings, basis="vme", aves="dropped", scaling="fitted")


def test_cost_difference_by_hand(specification: Specification) -> None:
    mappings = read_mappings(specification)
    complex_fee = 0.49 * 3 + 0.15 * 3 + 0.16 * 5 + 0.10 * 36 + 0.05 * 25 + 0.05 * 30
    control_fee = 0.65 * 3 + 0.35 * 5
    assert complex_fee == pytest.approx(9.07) and control_fee == pytest.approx(3.70)
    assert cost_difference_bp(mappings, aves="emerging_value") == pytest.approx(5.37 + 0.002)
    assert cost_difference_bp(mappings, aves="developed_value") == pytest.approx(5.37 + 0.002)
    # Dropped: AVES's 5% pays VXUS's 5 bp instead of 30.
    assert cost_difference_bp(mappings, aves="dropped") == pytest.approx(5.37 - 0.05 * 25 + 0.002)


# --------------------------------------------------------------------------- #
# The specification freezes what it says it freezes
# --------------------------------------------------------------------------- #


def test_primary_arm_is_the_out_of_sample_window_with_aves_dropped(
    specification: Specification,
) -> None:
    arms = read_arms(specification)
    parameters = specification.parameters
    assert isinstance(parameters, Mapping)
    primary = arms[str(parameters["primary_arm"])]
    assert primary.name == "tilts_oos"
    assert (primary.start, primary.end) == ("1981-07", "1990-10")
    assert primary.basis == "vme" and primary.scaling == "unscaled" and primary.aves == "dropped"
    assert specification.seed == 20260902
    assert specification.run_kind.value == "exploratory"


def test_every_out_of_sample_arm_drops_aves_and_ends_before_the_french_panels(
    specification: Specification,
) -> None:
    for arm in read_arms(specification).values():
        if arm.window == "primary_out_of_sample":
            assert arm.end == "1990-10"
            assert arm.aves in {"dropped", "developed_value"}
            assert arm.basis == "vme"


def test_the_spec_pins_the_vme_file_and_reads_no_asset_allocation_column(
    specification: Specification,
) -> None:
    parameters = specification.parameters
    assert isinstance(parameters, Mapping)
    pin = parameters["source_pin"]
    assert isinstance(pin, Mapping)
    files = pin["files"]
    assert isinstance(files, Sequence)
    vme = next(f for f in files if isinstance(f, Mapping) and f["id"] == "aqr_vme_factors")
    assert str(vme["expected_sha256_raw"]).startswith("a2351d03")
    columns = vme["columns"]
    assert isinstance(columns, Sequence)
    assert all("90" in str(c) for c in columns), "only the stock-selection columns are read"
    assert not any(str(c).endswith(("_EQ", "_FX", "_FI", "_COM")) for c in columns)


# --------------------------------------------------------------------------- #
# Series alignment
# --------------------------------------------------------------------------- #


def _store() -> SeriesStore:
    months = [f"1981-{m:02d}" for m in range(1, 13)]
    return SeriesStore(
        series={
            "a": {m: float(i) for i, m in enumerate(months)},
            "b": {m: 1.0 for m in months[3:]},
        }
    )


def test_aligned_returns_the_window_in_order() -> None:
    periods, matrix = aligned(_store(), ["a"], start="1981-03", end="1981-05")
    assert periods == ("1981-03", "1981-04", "1981-05")
    assert matrix[:, 0].tolist() == [2.0, 3.0, 4.0]


def test_aligned_refuses_a_window_with_a_missing_month() -> None:
    with pytest.raises(TiltsOutOfSampleError, match="missing 3 month"):
        aligned(_store(), ["a", "b"], start="1981-01", end="1981-06")


# --------------------------------------------------------------------------- #
# Statistics on a synthetic paired difference
# --------------------------------------------------------------------------- #


def test_gap_summary_mean_floor_and_tracking_error_by_numpy() -> None:
    rng = np.random.default_rng(7)
    difference = rng.normal(0.0005, 0.003, size=240)
    indices = stationary_bootstrap_indices(240, 12.0, 2000, np.random.default_rng(1))
    summary = gap_summary(difference, indices=indices, confidence=0.95)
    assert summary.gap_pp_yr == pytest.approx(float(np.mean(difference)) * 1200.0)
    sd = float(np.std(difference, ddof=1))
    assert summary.tracking_error_pct == pytest.approx(sd * math.sqrt(12) * 100.0)
    # 2.801585 * 1200 * sd / sqrt(T) is the same number as 2.801585 * annual sd / sqrt(years).
    assert summary.mde_iid_pp_yr == pytest.approx(MDE_MULTIPLIER * 1200.0 * sd / math.sqrt(240))
    assert summary.hac_interval[0] < summary.gap_pp_yr < summary.hac_interval[1]
    assert summary.bootstrap_interval[0] < summary.gap_pp_yr < summary.bootstrap_interval[1]
    assert summary.months == 240
    assert summary.years_to_distinguish == pytest.approx(
        (MDE_MULTIPLIER * sd * math.sqrt(12) * 100.0 / abs(summary.gap_pp_yr)) ** 2
    )


def _result(gap: float, floor: float, *, lo: float, halves: tuple[float, float]) -> ArmResult:
    summary = GapSummary(
        gap_pp_yr=gap,
        hac_interval=(lo, gap + (gap - lo)),
        hac_se_pp_yr=0.1,
        hac_t=3.0,
        hac_p=0.01,
        hac_lags=3,
        bootstrap_interval=(lo, gap + (gap - lo)),
        bootstrap_p=0.01,
        mde_iid_pp_yr=floor,
        mde_hac_pp_yr=floor,
        mde_bootstrap_pp_yr=floor,
        tracking_error_pct=1.0,
        years_to_distinguish=10.0,
        months=112,
    )
    arm = Arm(
        name="x",
        role="r",
        window="w",
        start="1981-07",
        end="1990-10",
        basis="vme",
        scaling="unscaled",
        aves="dropped",
    )
    return ArmResult(
        arm=arm,
        exposure={},
        cost_bp=0.0,
        summary=summary,
        contributions={},
        sub_periods={"h1": {"gap_pp_yr": halves[0]}, "h2": {"gap_pp_yr": halves[1]}},
        perturbation_range=(gap - 0.1, gap + 0.1),
    )


def test_falsifier_clauses_fire_in_order() -> None:
    negative = _result(-0.2, 0.5, lo=-0.6, halves=(-0.1, -0.3))
    apply_falsifier(negative)
    assert negative.status == "rejected" and negative.clause.startswith("(a)")

    inside_floor = _result(0.4, 0.9, lo=0.1, halves=(0.3, 0.5))
    apply_falsifier(inside_floor)
    assert inside_floor.status == "unresolved" and inside_floor.clause.startswith("(b)")

    interval_crosses_zero = _result(1.0, 0.9, lo=-0.1, halves=(0.9, 1.1))
    apply_falsifier(interval_crosses_zero)
    assert interval_crosses_zero.clause.startswith("(c)")

    half_flips = _result(1.0, 0.9, lo=0.2, halves=(1.8, -0.2))
    apply_falsifier(half_flips)
    assert half_flips.status == "unresolved" and half_flips.clause.startswith("(d)")

    survives = _result(1.0, 0.9, lo=0.2, halves=(0.9, 1.1))
    apply_falsifier(survives)
    assert survives.status == "exploratory" and survives.clause.startswith("(e)")
