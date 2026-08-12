"""Structured validation of a derived table. Reports; never repairs.

Every check here returns a finding. None of them changes a value, drops a row,
forward-fills a gap or renames a column. That is the whole design: a validator
that quietly fixes data destroys the evidence that the source has a problem, and
the resulting table looks clean for a reason nobody can reconstruct later. If a
table needs repair, the repair belongs in a named, versioned transform whose
assumptions are visible, not inside a function called ``validate``.

The checks
----------
``duplicate_period``
    The same period appears twice. Usually a table boundary that was missed.
``non_monotonic_period``
    Periods are not strictly increasing. Ordering is assumed by every rolling
    statistic downstream.
``frequency_gap``
    A step larger than the declared frequency implies. Daily series are checked
    against a calendar-day tolerance because weekends and holidays are real; the
    tolerance is a heuristic and the finding says so.
``missing_value``
    Counts and locates ``None``. Reported, never imputed.
``sentinel_leakage``
    A sentinel such as -99.99 or -999 survived parsing and is sitting in the
    table as data. This is the check that would have caught a percent table read
    with the wrong missing-value convention.
``unit_implausible``
    A column declared ``percent`` holding values beyond ±100, or ``decimal``
    holding values beyond ±1. A factor return divided by 100 twice, or not at
    all, shows up here and nowhere else.
``column_drift``
    Column names differ from a declared expectation. Ken French renames columns
    and reorders them between file versions.
``discontinuity``
    A period-to-period change exceeding ``mad_threshold`` robust MADs of that
    column's changes. Catches a decimal-point shift or a spliced series; it also
    fires on genuine crashes, which is why it is a warning and not an error.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final, Literal

from portfolio_edge.data.table import ParsedTable, period_to_date

__all__ = [
    "DEFAULT_MAD_THRESHOLD",
    "DEFAULT_SENTINELS",
    "Severity",
    "ValidationFinding",
    "ValidationReport",
    "validate_table",
]

Severity = Literal["info", "warning", "error"]

#: The Ken French sentinels, plus the FRED "." token's numeric cousins. A value
#: equal to one of these in a parsed table means the parser missed it.
DEFAULT_SENTINELS: Final = (-99.99, -999.0, -9999.0)

#: Robust-MAD multiple beyond which a period-to-period change is flagged. Eight
#: is loose on purpose: monthly equity factors have fat tails and a threshold
#: tuned to fire rarely on real crashes still catches decimal-point errors, which
#: are off by a factor of ten or a hundred.
DEFAULT_MAD_THRESHOLD: Final = 8.0

#: Calendar-day step above which a daily series is flagged. Four covers weekends
#: and a Monday or Friday holiday; longer runs (Christmas plus a weekend, an
#: exchange closure) are worth a human look.
_DAILY_MAX_STEP_DAYS: Final = 4

_MAD_SCALE: Final = 1.4826

#: Consistency factor for the mean absolute deviation, used only when the MAD
#: collapses to zero because most changes are identical.
_MEAN_AD_SCALE: Final = 1.2533


@dataclass(frozen=True)
class ValidationFinding:
    """One problem, with enough detail to go and look at it.

    Attributes:
        code: Stable machine-readable identifier.
        count: How many cells or rows triggered it.
        examples: Up to a handful of locations, so the finding is actionable
            without re-running the check.
    """

    code: str
    severity: Severity
    message: str
    column: str | None = None
    count: int = 1
    examples: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationReport:
    """The outcome of validating one table.

    ``ok`` means no finding reached ``error`` severity. It does not mean the table
    is fit for a given purpose: a table full of warnings can still be ``ok``, and
    reading the warnings is the caller's job.
    """

    dataset_id: str
    rows: int
    findings: tuple[ValidationFinding, ...] = field(default=())

    @property
    def errors(self) -> tuple[ValidationFinding, ...]:
        return tuple(f for f in self.findings if f.severity == "error")

    @property
    def warnings(self) -> tuple[ValidationFinding, ...]:
        return tuple(f for f in self.findings if f.severity == "warning")

    @property
    def ok(self) -> bool:
        return not self.errors

    def codes(self) -> tuple[str, ...]:
        return tuple(f.code for f in self.findings)

    def has(self, code: str) -> bool:
        return any(f.code == code for f in self.findings)

    def summary(self) -> tuple[str, ...]:
        """Render the findings as lines, for a report or a manifest warning list."""
        return tuple(
            f"[{f.severity}] {f.code}"
            + (f" ({f.column})" if f.column else "")
            + f": {f.message}"
            for f in self.findings
        )


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    size = len(ordered)
    middle = size // 2
    if size % 2 == 1:
        return ordered[middle]
    return 0.5 * (ordered[middle - 1] + ordered[middle])


def _expected_step_months(frequency: str) -> int | None:
    if frequency == "monthly":
        return 1
    if frequency == "annual":
        return 12
    return None


def _check_periods(table: ParsedTable) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    periods = table.periods
    if not periods:
        return [
            ValidationFinding(
                code="empty_table",
                severity="error",
                message="the table has no rows",
                count=0,
            )
        ]

    duplicates = [period for period, n in Counter(periods).items() if n > 1]
    if duplicates:
        findings.append(
            ValidationFinding(
                code="duplicate_period",
                severity="error",
                message=(
                    f"{len(duplicates)} period labels appear more than once; "
                    "the table probably spans a boundary between two source "
                    "tables"
                ),
                count=len(duplicates),
                examples=tuple(sorted(duplicates)[:5]),
            )
        )

    try:
        dates = [period_to_date(period) for period in periods]
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                code="unparsable_period",
                severity="error",
                message=f"a period label could not be interpreted as a date: {exc}",
            )
        )
        return findings

    descending = [
        f"{periods[i]}->{periods[i + 1]}"
        for i in range(len(dates) - 1)
        if dates[i + 1] <= dates[i]
    ]
    if descending:
        findings.append(
            ValidationFinding(
                code="non_monotonic_period",
                severity="error",
                message=(
                    f"{len(descending)} steps are not strictly increasing; every "
                    "rolling and lagging calculation downstream assumes they are"
                ),
                count=len(descending),
                examples=tuple(descending[:5]),
            )
        )

    step_months = _expected_step_months(table.frequency)
    if step_months is not None:
        gaps: list[str] = []
        for i in range(len(dates) - 1):
            months = (dates[i + 1].year - dates[i].year) * 12 + (
                dates[i + 1].month - dates[i].month
            )
            if months > step_months:
                gaps.append(f"{periods[i]}->{periods[i + 1]} ({months} months)")
        if gaps:
            findings.append(
                ValidationFinding(
                    code="frequency_gap",
                    severity="warning",
                    message=(
                        f"{len(gaps)} gaps exceed the declared {table.frequency} "
                        "step; the missing periods are absent from the table "
                        "rather than present and empty"
                    ),
                    count=len(gaps),
                    examples=tuple(gaps[:5]),
                )
            )
    elif table.frequency == "daily":
        gaps = [
            f"{periods[i]}->{periods[i + 1]} ({(dates[i + 1] - dates[i]).days} days)"
            for i in range(len(dates) - 1)
            if (dates[i + 1] - dates[i]).days > _DAILY_MAX_STEP_DAYS
        ]
        if gaps:
            findings.append(
                ValidationFinding(
                    code="frequency_gap",
                    severity="warning",
                    message=(
                        f"{len(gaps)} steps exceed {_DAILY_MAX_STEP_DAYS} calendar "
                        "days. Weekends and single holidays are expected, so this "
                        "is a heuristic; a long run may be an exchange closure, a "
                        "series splice, or missing rows"
                    ),
                    count=len(gaps),
                    examples=tuple(gaps[:5]),
                )
            )
    else:
        findings.append(
            ValidationFinding(
                code="frequency_unknown",
                severity="warning",
                message=(
                    f"frequency is {table.frequency!r}, so no gap check was "
                    "performed. An unchecked series is not a clean series."
                ),
            )
        )
    return findings


def _plausibility_bound(units: str) -> float | None:
    lowered = units.lower()
    if lowered == "percent" or lowered.startswith("percent"):
        return 100.0
    if lowered == "decimal" or lowered.startswith("decimal"):
        return 1.0
    return None


def _check_column(
    table: ParsedTable,
    column: str,
    values: Sequence[float | None],
    sentinels: Sequence[float],
    mad_threshold: float,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    periods = table.periods

    missing = [periods[i] for i, v in enumerate(values) if v is None or (v != v)]
    if missing:
        findings.append(
            ValidationFinding(
                code="missing_value",
                severity="warning",
                message=(
                    f"{len(missing)} of {len(values)} observations are missing. "
                    "They are reported, not imputed; decide explicitly how the "
                    "experiment treats them"
                ),
                column=column,
                count=len(missing),
                examples=tuple(missing[:5]),
            )
        )

    scale = 0.01 if table.unit_transform == "value / 100" else 1.0
    leaks = [
        f"{periods[i]}={v!r}"
        for i, v in enumerate(values)
        if v is not None
        and v == v
        and any(abs(v - sentinel * scale) < 1e-9 for sentinel in sentinels)
    ]
    if leaks:
        findings.append(
            ValidationFinding(
                code="sentinel_leakage",
                severity="error",
                message=(
                    f"{len(leaks)} values equal a missing-data sentinel "
                    f"{list(sentinels)} (after the declared unit transform) and "
                    "are being carried as data. Fix the parser; do not filter "
                    "them here"
                ),
                column=column,
                count=len(leaks),
                examples=tuple(leaks[:5]),
            )
        )

    present = [(periods[i], v) for i, v in enumerate(values) if v is not None and v == v]
    bound = _plausibility_bound(table.units)
    if bound is not None:
        implausible = [f"{p}={v!r}" for p, v in present if abs(v) > bound]
        if implausible:
            findings.append(
                ValidationFinding(
                    code="unit_implausible",
                    severity="warning",
                    message=(
                        f"{len(implausible)} values exceed ±{bound:g} for a column "
                        f"declared {table.units!r}. Either the unit transform "
                        f"({table.unit_transform!r}) is wrong or these are "
                        "genuine extremes; a factor return scaled by the wrong "
                        "power of ten looks exactly like this"
                    ),
                    column=column,
                    count=len(implausible),
                    examples=tuple(implausible[:5]),
                )
            )

    numbers = [v for _, v in present]
    labels = [p for p, _ in present]
    if len(numbers) >= 8:
        diffs = [numbers[i + 1] - numbers[i] for i in range(len(numbers) - 1)]
        centre = _median(diffs)
        deviations = [abs(d - centre) for d in diffs]
        scale = _median(deviations) * _MAD_SCALE
        if scale == 0.0:
            # More than half the changes are identical, which drives the MAD to
            # zero and would switch this check off exactly where a single spliced
            # value is most visible. Fall back to the mean absolute deviation,
            # scaled for consistency with the standard deviation under normality.
            scale = (sum(deviations) / len(deviations)) * _MEAN_AD_SCALE
        jumps: list[str] = []
        if scale > 0.0 and math.isfinite(scale):
            jumps = [
                f"{labels[i]}->{labels[i + 1]} "
                f"(delta={diffs[i]:.6g}, {abs(diffs[i] - centre) / scale:.1f} MAD)"
                for i in range(len(diffs))
                if abs(diffs[i] - centre) > mad_threshold * scale
            ]
        # scale == 0 here means every change is identical, so there is no
        # discontinuity to find, not that the check was skipped.
        if jumps:
            findings.append(
                ValidationFinding(
                    code="discontinuity",
                    severity="warning",
                    message=(
                        f"{len(jumps)} period-to-period changes exceed "
                        f"{mad_threshold:g} robust MADs of this column's changes. "
                        "Real crises look like this too, so check before "
                        "concluding anything; a splice, a decimal shift or a "
                        "units change also looks like this"
                    ),
                    column=column,
                    count=len(jumps),
                    examples=tuple(jumps[:5]),
                )
            )
    return findings


def validate_table(
    table: ParsedTable,
    *,
    dataset_id: str | None = None,
    expected_columns: Sequence[str] | None = None,
    expected_frequency: str | None = None,
    sentinels: Sequence[float] = DEFAULT_SENTINELS,
    mad_threshold: float = DEFAULT_MAD_THRESHOLD,
) -> ValidationReport:
    """Validate ``table`` and return a report. The table is never modified.

    Args:
        expected_columns: The schema the caller believes it is reading. Supplying
            it turns a silent source rename into a finding; omitting it means
            column drift cannot be detected at all.
        expected_frequency: The frequency the caller believes it asked for.
        sentinels: Values that must not appear as data. Compared after the
            table's own unit transform, so -99.99 in a percent file is caught as
            -0.9999 in the decimal table.
        mad_threshold: Robust-MAD multiple for the discontinuity check.

    Returns:
        A :class:`ValidationReport`. ``report.ok`` is ``False`` if any finding is
        an error.
    """
    findings: list[ValidationFinding] = []

    if expected_frequency is not None and table.frequency != expected_frequency:
        findings.append(
            ValidationFinding(
                code="frequency_drift",
                severity="error",
                message=(
                    f"table frequency is {table.frequency!r} but "
                    f"{expected_frequency!r} was expected"
                ),
            )
        )

    if expected_columns is not None:
        expected = tuple(expected_columns)
        if tuple(table.columns) != expected:
            missing = [c for c in expected if c not in table.columns]
            unexpected = [c for c in table.columns if c not in expected]
            reordered = (
                not missing
                and not unexpected
                and tuple(table.columns) != expected
            )
            findings.append(
                ValidationFinding(
                    code="column_drift",
                    severity="error",
                    message=(
                        "column names differ from the expected schema: "
                        f"missing={missing}, unexpected={unexpected}, "
                        f"reordered={reordered}. Expected {list(expected)}, "
                        f"found {list(table.columns)}"
                    ),
                    count=len(missing) + len(unexpected) + int(reordered),
                )
            )

    if table.units == "unknown":
        findings.append(
            ValidationFinding(
                code="units_unknown",
                severity="warning",
                message=(
                    "the parser could not classify this table's units, so no "
                    "plausibility check could run and no arithmetic on these "
                    "values is safe yet"
                ),
            )
        )

    findings.extend(_check_periods(table))
    if table.periods:
        for index, column in enumerate(table.columns):
            values = [row[index] for row in table.values]
            findings.extend(
                _check_column(table, column, values, sentinels, mad_threshold)
            )

    return ValidationReport(
        dataset_id=dataset_id or table.table_id,
        rows=table.rows,
        findings=tuple(findings),
    )
