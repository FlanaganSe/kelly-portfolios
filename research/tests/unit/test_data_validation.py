"""Validation must find every problem it claims to, and repair none of them."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table


def _table(
    periods: Sequence[str],
    values: Sequence[Sequence[float | None]],
    *,
    columns: Sequence[str] = ("x",),
    frequency: str = "monthly",
    units: str = "decimal",
    source_units: str = "percent",
    unit_transform: str = "value / 100",
) -> ParsedTable:
    return ParsedTable(
        table_id="t",
        banner="",
        columns=tuple(columns),
        periods=tuple(periods),
        values=tuple(tuple(row) for row in values),
        frequency=frequency,  # type: ignore[arg-type]
        source_units=source_units,
        units=units,
        unit_transform=unit_transform,
    )


def _months(count: int, start_year: int = 2000) -> list[str]:
    return [f"{start_year + i // 12:04d}-{i % 12 + 1:02d}" for i in range(count)]


def _clean(count: int = 24) -> ParsedTable:
    periods = _months(count)
    return _table(periods, [[0.01 + 0.001 * (i % 5)] for i in range(count)])


def test_a_clean_table_produces_no_errors() -> None:
    report = validate_table(_clean())
    assert report.ok
    assert not report.errors


def test_duplicate_periods_are_an_error() -> None:
    report = validate_table(_table(["2000-01", "2000-01"], [[0.01], [0.02]]))
    assert report.has("duplicate_period")
    assert not report.ok


def test_non_monotonic_periods_are_an_error() -> None:
    report = validate_table(_table(["2000-02", "2000-01"], [[0.01], [0.02]]))
    assert report.has("non_monotonic_period")
    assert not report.ok


def test_a_gap_against_the_declared_frequency_is_reported() -> None:
    report = validate_table(_table(["2000-01", "2000-02", "2000-06"], [[0.01]] * 3))
    gap = next(f for f in report.findings if f.code == "frequency_gap")
    assert gap.severity == "warning"
    assert "2000-02->2000-06" in gap.examples[0]


def test_a_long_daily_gap_is_reported_but_a_weekend_is_not() -> None:
    weekend = validate_table(
        _table(["2024-01-05", "2024-01-08", "2024-01-09"], [[0.01]] * 3, frequency="daily")
    )
    assert not weekend.has("frequency_gap")

    closure = validate_table(
        _table(["2024-01-05", "2024-01-25"], [[0.01]] * 2, frequency="daily")
    )
    assert closure.has("frequency_gap")


def test_missing_values_are_reported_and_not_imputed() -> None:
    table = _table(_months(3), [[0.01], [None], [0.02]])
    report = validate_table(table)

    finding = next(f for f in report.findings if f.code == "missing_value")
    assert finding.count == 1
    assert finding.examples == ("2000-02",)
    assert table.values[1][0] is None


def test_sentinel_leakage_is_an_error_after_the_unit_transform() -> None:
    """A -99.99 percent sentinel becomes -0.9999 in the decimal table."""
    report = validate_table(_table(_months(2), [[-0.9999], [0.01]]))

    assert report.has("sentinel_leakage")
    assert not report.ok


def test_sentinel_leakage_is_caught_in_untransformed_tables_too() -> None:
    report = validate_table(
        _table(
            _months(2),
            [[-99.99], [1.0]],
            units="count",
            source_units="count",
            unit_transform="identity",
        )
    )
    assert report.has("sentinel_leakage")


def test_a_decimal_column_above_one_is_implausible() -> None:
    report = validate_table(_table(_months(2), [[0.01], [5.08]]))

    finding = next(f for f in report.findings if f.code == "unit_implausible")
    assert finding.severity == "warning"
    assert "5.08" in finding.examples[0]


def test_a_percent_column_above_one_hundred_is_implausible() -> None:
    report = validate_table(
        _table(
            _months(2),
            [[3.0], [250.0]],
            units="percent",
            source_units="percent",
            unit_transform="identity",
        )
    )
    assert report.has("unit_implausible")


def test_plausible_values_do_not_trigger_the_unit_check() -> None:
    assert not validate_table(_clean()).has("unit_implausible")


def test_column_drift_is_an_error_when_a_schema_is_declared() -> None:
    table = _table(_months(2), [[0.01, 0.02]] * 2, columns=("Mkt-RF", "SMB"))
    report = validate_table(table, expected_columns=("Mkt-RF", "HML"))

    finding = next(f for f in report.findings if f.code == "column_drift")
    assert "missing=['HML']" in finding.message
    assert "unexpected=['SMB']" in finding.message


def test_reordered_columns_are_detected() -> None:
    table = _table(_months(2), [[0.01, 0.02]] * 2, columns=("SMB", "Mkt-RF"))
    report = validate_table(table, expected_columns=("Mkt-RF", "SMB"))

    assert "reordered=True" in next(
        f for f in report.findings if f.code == "column_drift"
    ).message


def test_no_schema_means_no_drift_detection() -> None:
    table = _table(_months(2), [[0.01, 0.02]] * 2, columns=("SMB", "Mkt-RF"))
    assert not validate_table(table).has("column_drift")


def test_frequency_drift_against_the_caller_expectation_is_an_error() -> None:
    report = validate_table(_clean(), expected_frequency="daily")
    assert report.has("frequency_drift")
    assert not report.ok


def test_a_decimal_point_shift_shows_up_as_a_discontinuity() -> None:
    periods = _months(24)
    values: list[list[float | None]] = [[0.01 + 0.002 * (i % 3)] for i in range(24)]
    values[12] = [1.4]  # the same return with the decimal point in the wrong place
    report = validate_table(_table(periods, values))

    finding = next(f for f in report.findings if f.code == "discontinuity")
    assert finding.severity == "warning"
    assert "2001-01" in " ".join(finding.examples)


def test_a_constant_series_does_not_produce_spurious_discontinuities() -> None:
    periods = _months(24)
    assert not validate_table(_table(periods, [[0.01]] * 24)).has("discontinuity")


def test_unknown_units_block_the_plausibility_check_loudly() -> None:
    report = validate_table(
        _table(
            _months(2),
            [[1e9], [2e9]],
            units="unknown",
            source_units="unknown",
            unit_transform="identity",
        )
    )
    assert report.has("units_unknown")
    assert not report.has("unit_implausible")


def test_an_empty_table_is_an_error() -> None:
    report = validate_table(_table([], []))
    assert report.has("empty_table")
    assert not report.ok


def test_validation_never_modifies_the_table() -> None:
    table = _table(
        ["2000-02", "2000-02"],
        [[-0.9999], [None]],
    )
    before = table.canonical_bytes()
    report = validate_table(table)

    assert not report.ok
    assert table.canonical_bytes() == before


def test_the_report_renders_readable_lines() -> None:
    report = validate_table(_table(["2000-01", "2000-01"], [[0.01], [0.02]]))
    assert any(line.startswith("[error] duplicate_period") for line in report.summary())


@pytest.mark.parametrize(
    "code",
    [
        "duplicate_period",
        "non_monotonic_period",
        "frequency_gap",
        "missing_value",
        "sentinel_leakage",
        "unit_implausible",
        "column_drift",
        "discontinuity",
    ],
)
def test_every_documented_check_can_fire(code: str) -> None:
    periods = ["2000-01", "2000-01", "2000-03", "2000-04", *_months(20, 2001)]
    tail: list[list[float | None]] = [
        [0.01 + 0.001 * (i % 3), 0.0] for i in range(20)
    ]
    values: list[list[float | None]] = [
        [0.01, 0.0],
        [-0.9999, 0.0],
        [None, 0.0],
        [5.0, 0.0],
        *tail,
    ]
    report = validate_table(
        _table(periods, values, columns=("x", "y")),
        expected_columns=("x", "z"),
    )
    assert report.has(code), report.codes()
