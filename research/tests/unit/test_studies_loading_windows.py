"""Tests for :mod:`portfolio_edge.studies.loading_windows`.

The module has no data dependency and no randomness, so a failure here is a changed input
or a bug, never noise. Four kinds of test, kept apart:

* **Recovery against a generated fixture**, where the true coefficients are known because
  the test wrote them, so the estimator is checked against arithmetic rather than itself.
* **The refusals** — the whole point of the module is that it will not rank loadings from
  unequal windows, and that guard is worth more than any number it produces.
* **Window algebra**, including the derivation that recovers a published window from a
  published month count.
* **Independently computed fixtures** for the minimum detectable loading and the interval,
  written out longhand in the test.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.loading_windows import (
    MDE_MULTIPLIER,
    IncomparableWindowsError,
    LoadingEstimate,
    Window,
    common_window,
    estimate_loadings,
    minimum_detectable_loading,
    month_index,
    period_from_index,
    rank,
    require_contiguous,
    rolling_windows,
    window_ending,
)


def _estimate(
    ticker: str,
    value: float,
    window: Window,
    *,
    standard_error: float = 0.1,
    factor: str = "HML",
    benchmark: str = "french-us",
) -> LoadingEstimate:
    return LoadingEstimate(
        ticker=ticker,
        factor=factor,
        benchmark=benchmark,
        value=value,
        standard_error=standard_error,
        window=window,
    )


class TestMonthArithmetic:
    def test_round_trips_a_period_through_its_index(self) -> None:
        for period in ("1963-07", "1999-12", "2000-01", "2026-04"):
            assert period_from_index(month_index(period)) == period

    def test_indexes_adjacent_months_one_apart_across_a_year_end(self) -> None:
        assert month_index("2024-01") - month_index("2023-12") == 1

    def test_refuses_a_period_that_is_not_yyyy_mm(self) -> None:
        for bad in ("2024-1", "2024/01", "202401", "2024-01-31"):
            with pytest.raises(ValueError, match="YYYY-MM"):
                month_index(bad)


class TestWindow:
    def test_counts_both_endpoints(self) -> None:
        assert Window("2023-01", "2025-12").months == 36
        assert Window("2023-01", "2023-01").months == 1

    def test_refuses_a_window_that_ends_before_it_begins(self) -> None:
        with pytest.raises(ValueError, match="ends before it begins"):
            Window("2025-12", "2023-01")

    def test_lists_every_month_it_contains(self) -> None:
        window = Window("2023-11", "2024-02")
        assert window.periods() == ("2023-11", "2023-12", "2024-01", "2024-02")

    def test_overlap_is_the_months_both_windows_hold(self) -> None:
        assert Window("2020-01", "2025-12").overlap(Window("2023-01", "2026-04")) == Window(
            "2023-01", "2025-12"
        )

    def test_overlap_of_disjoint_windows_is_none(self) -> None:
        assert Window("2019-01", "2019-12").overlap(Window("2020-01", "2020-12")) is None


class TestWindowEnding:
    """The derivation that recovers a published window from a published month count.

    Experiments 008, 009 and 013 all freeze a common period ending 2025-12 and estimate
    each fund on the longest contiguous run of its own filed months inside it, so a fund
    reported at ``n`` months has the trailing ``n``. These are the counts the shelf
    publishes; ``_loading_windows_tables`` checks the same rule by reproducing twenty
    published loadings from it.
    """

    @pytest.mark.parametrize(
        ("months", "first"),
        [(72, "2020-01"), (54, "2021-07"), (51, "2021-10"), (46, "2022-03"), (36, "2023-01")],
    )
    def test_recovers_the_published_windows(self, months: int, first: str) -> None:
        window = window_ending("2025-12", months)
        assert window == Window(first, "2025-12")
        assert window.months == months

    def test_refuses_an_empty_window(self) -> None:
        with pytest.raises(ValueError, match="at least one month"):
            window_ending("2025-12", 0)


class TestContiguity:
    def test_accepts_a_gapless_run(self) -> None:
        require_contiguous(("2024-11", "2024-12", "2025-01"))

    def test_names_the_gap_it_found(self) -> None:
        with pytest.raises(ValueError, match=r"2024-12->2025-03"):
            require_contiguous(("2024-11", "2024-12", "2025-03"))

    def test_refuses_months_out_of_order(self) -> None:
        with pytest.raises(ValueError, match="contiguous"):
            require_contiguous(("2025-01", "2024-12"))

    def test_rolling_windows_tile_the_run(self) -> None:
        months = Window("2020-01", "2020-12").periods()
        windows = rolling_windows(months, 10)
        assert len(windows) == 3
        assert windows[0] == Window("2020-01", "2020-10")
        assert windows[-1] == Window("2020-03", "2020-12")

    def test_rolling_windows_are_empty_when_the_run_is_too_short(self) -> None:
        assert rolling_windows(("2020-01", "2020-02"), 36) == ()


class TestCommonWindow:
    def test_intersects_the_published_us_value_windows(self) -> None:
        """The nine US value funds' published windows meet on 36 months, DFLV's own."""
        published = [
            window_ending("2025-12", months) for months in (72, 51, 36, 43, 72, 46, 54, 72, 72)
        ]
        assert common_window(published) == Window("2023-01", "2025-12")

    def test_refuses_windows_that_never_overlap(self) -> None:
        with pytest.raises(IncomparableWindowsError, match="do not all overlap"):
            common_window([Window("2019-01", "2019-12"), Window("2021-01", "2021-12")])

    def test_refuses_an_empty_set(self) -> None:
        with pytest.raises(ValueError, match="no windows"):
            common_window([])


class TestRankRefusesIncomparableWindows:
    """The guard this module exists for.

    A ranking across unequal windows orders launch dates as well as funds, and the
    published US value shelf is exactly such a set: VTV has 72 months, AVLV 51, DFLV 36.
    """

    def test_refuses_a_mixed_window_set_and_names_the_windows(self) -> None:
        estimates = [
            _estimate("VTV", 0.337, window_ending("2025-12", 72)),
            _estimate("AVLV", 0.322, window_ending("2025-12", 51)),
            _estimate("DFLV", 0.637, window_ending("2025-12", 36)),
        ]
        with pytest.raises(IncomparableWindowsError) as caught:
            rank(estimates)
        message = str(caught.value)
        assert "VTV 2020-01..2025-12 (72m)" in message
        assert "AVLV 2021-10..2025-12 (51m)" in message

    def test_sorts_a_matched_set_largest_first(self) -> None:
        matched = Window("2023-01", "2025-12")
        ranked = rank(
            [
                _estimate("AVLV", 0.413, matched),
                _estimate("RPV", 0.836, matched),
                _estimate("VTV", 0.520, matched),
            ]
        )
        assert [item.ticker for item in ranked] == ["RPV", "VTV", "AVLV"]

    def test_refuses_to_rank_across_two_different_factors(self) -> None:
        matched = Window("2023-01", "2025-12")
        with pytest.raises(IncomparableWindowsError, match="different quantities"):
            rank(
                [
                    _estimate("AVUV", 0.467, matched, factor="HML"),
                    _estimate("AVUV", 0.880, matched, factor="SMB"),
                ]
            )

    def test_refuses_to_rank_across_two_panels(self) -> None:
        matched = Window("2023-01", "2025-12")
        with pytest.raises(IncomparableWindowsError, match="different quantities"):
            rank(
                [
                    _estimate("AVES", 0.237, matched, benchmark="french-emerging"),
                    _estimate("AVES", -0.074, matched, benchmark="french-us"),
                ]
            )

    def test_an_empty_set_ranks_to_nothing_rather_than_raising(self) -> None:
        assert rank([]) == ()


class TestEstimateReporting:
    def test_interval_is_the_point_estimate_plus_or_minus_1_96_standard_errors(self) -> None:
        estimate = _estimate("RSST", 0.681, Window("2023-10", "2026-04"), standard_error=0.14)
        low, high = estimate.interval95
        assert low == pytest.approx(0.681 - 1.959963985 * 0.14, abs=1e-6)
        assert high == pytest.approx(0.681 + 1.959963985 * 0.14, abs=1e-6)

    def test_minimum_detectable_loading_is_2_802_standard_errors(self) -> None:
        """``z_{0.975} + z_{0.80} = 1.9599640 + 0.8416212``, written out rather than read."""
        expected = 1.9599639845 + 0.8416212336
        assert pytest.approx(expected, abs=1e-9) == MDE_MULTIPLIER
        assert minimum_detectable_loading(0.14) == pytest.approx(expected * 0.14, abs=1e-9)

    def test_a_wider_window_is_not_assumed_to_be_a_better_estimate(self) -> None:
        """The MDE tracks the standard error alone; month count enters only through it."""
        tight = _estimate("A", 0.5, Window("2023-01", "2025-12"), standard_error=0.05)
        loose = _estimate("B", 0.5, Window("2020-01", "2025-12"), standard_error=0.30)
        assert tight.minimum_detectable_loading < loose.minimum_detectable_loading

    def test_excludes_reports_whether_the_interval_clears_a_bar(self) -> None:
        estimate = _estimate("DBMF", 0.671, Window("2021-07", "2025-12"), standard_error=0.075)
        assert estimate.excludes(0.50) is True
        assert estimate.excludes(0.60) is False

    def test_refuses_a_negative_standard_error(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            _estimate("X", 0.5, Window("2023-01", "2025-12"), standard_error=-0.1)

    def test_months_comes_from_the_window_and_cannot_disagree_with_it(self) -> None:
        estimate = _estimate("RSST", 0.681, Window("2023-10", "2026-04"))
        assert estimate.months == 31


class TestEstimateLoadings:
    """Recovery against a fixture whose true coefficients the test chose."""

    @staticmethod
    def _panel(months: int, seed: int = 20260823) -> tuple[tuple[str, ...], dict[str, list[float]]]:
        rng = np.random.default_rng(seed)
        periods = Window("2019-01", period_from_index(month_index("2019-01") + months - 1))
        design = {
            "MKT": list(rng.normal(0.008, 0.045, months)),
            "TSMOM": list(rng.normal(0.003, 0.030, months)),
        }
        return periods.periods(), design

    def test_recovers_a_known_stacked_wrapper(self) -> None:
        """One dollar of market plus 0.7 of trend, built by hand, read back off the fit."""
        periods, design = self._panel(400)
        truth = {"MKT": 1.0, "TSMOM": 0.7}
        rng = np.random.default_rng(7)
        excess = [
            truth["MKT"] * market + truth["TSMOM"] * trend + noise
            for market, trend, noise in zip(
                design["MKT"], design["TSMOM"], rng.normal(0.0, 0.004, len(periods)), strict=True
            )
        ]
        fitted = estimate_loadings(
            ticker="FIXTURE",
            benchmark="synthetic",
            periods=periods,
            excess_returns=excess,
            design=design,
            n_lags=6,
        )
        assert fitted["MKT"].value == pytest.approx(1.0, abs=0.01)
        assert fitted["TSMOM"].value == pytest.approx(0.7, abs=0.02)
        assert fitted["TSMOM"].window == Window(periods[0], periods[-1])

    def test_recovers_a_known_zero_loading(self) -> None:
        """The negative control's shape: a fund with no exposure must not read one."""
        periods, design = self._panel(400)
        rng = np.random.default_rng(11)
        excess = [
            1.0 * market + noise
            for market, noise in zip(
                design["MKT"], rng.normal(0.0, 0.004, len(periods)), strict=True
            )
        ]
        fitted = estimate_loadings(
            ticker="CONTROL",
            benchmark="synthetic",
            periods=periods,
            excess_returns=excess,
            design=design,
            n_lags=6,
        )
        low, high = fitted["TSMOM"].interval95
        assert low < 0.0 < high

    def test_refuses_a_gap_in_the_months(self) -> None:
        periods, design = self._panel(40)
        broken = (*periods[:20], *periods[21:])
        for name in design:
            design[name] = design[name][: len(broken)]
        with pytest.raises(ValueError, match="contiguous"):
            estimate_loadings(
                ticker="FIXTURE",
                benchmark="synthetic",
                periods=broken,
                excess_returns=[0.0] * len(broken),
                design=design,
                n_lags=6,
            )

    def test_refuses_returns_that_do_not_align_with_the_months(self) -> None:
        periods, design = self._panel(40)
        with pytest.raises(ValueError, match="they must align"):
            estimate_loadings(
                ticker="FIXTURE",
                benchmark="synthetic",
                periods=periods,
                excess_returns=[0.0] * (len(periods) - 1),
                design=design,
                n_lags=6,
            )

    def test_refuses_a_design_with_no_regressors(self) -> None:
        periods, _ = self._panel(40)
        with pytest.raises(ValueError, match="no regressors"):
            estimate_loadings(
                ticker="FIXTURE",
                benchmark="synthetic",
                periods=periods,
                excess_returns=[0.0] * len(periods),
                design={},
                n_lags=6,
            )

    def test_standard_errors_shrink_as_the_window_lengthens(self) -> None:
        """Why a 31-month wrapper estimate is wide and a 72-month one is not."""
        errors = []
        for months in (36, 144):
            periods, design = self._panel(months, seed=5)
            rng = np.random.default_rng(3)
            excess = [
                1.0 * market + 0.7 * trend + noise
                for market, trend, noise in zip(
                    design["MKT"], design["TSMOM"], rng.normal(0.0, 0.02, months), strict=True
                )
            ]
            fitted = estimate_loadings(
                ticker="FIXTURE",
                benchmark="synthetic",
                periods=periods,
                excess_returns=excess,
                design=design,
                n_lags=6,
            )
            errors.append(fitted["TSMOM"].standard_error)
        assert errors[1] < errors[0]
        assert math.isfinite(errors[0])
