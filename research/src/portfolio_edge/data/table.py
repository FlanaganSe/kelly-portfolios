"""The derived-table type shared by every reader in this package.

A :class:`ParsedTable` is the normalised form of one table found inside one raw
artifact. It is deliberately not a ``DataFrame``: it is immutable, it carries the
units and the exact unit transform that produced its values, it keeps the source
banner text that describes it, and it serialises canonically so that
``sha256_normalized`` is reproducible across machines and pandas versions. Call
:meth:`ParsedTable.to_frame` at the point of analysis.

Missing values are ``None``, never a sentinel and never a silently substituted
zero. A sentinel that survived parsing is a bug, and
:mod:`portfolio_edge.data.validation` looks for exactly that.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:  # pragma: no cover - import cost only
    import pandas as pd

__all__ = [
    "CANONICAL_FORM_VERSION",
    "Frequency",
    "ParsedTable",
    "period_to_date",
]

#: Bump when the canonical serialisation changes, because every previously
#: recorded ``sha256_normalized`` becomes incomparable when it does.
CANONICAL_FORM_VERSION: Final = "1"

Frequency = Literal["daily", "monthly", "annual", "unknown"]

_UNIT_SEPARATOR: Final = "\x1f"


def period_to_date(period: str) -> date:
    """Map a period label to the date of its first day.

    Accepts ``YYYY``, ``YYYY-MM`` and ``YYYY-MM-DD``. Using the first day makes
    gap arithmetic well defined without pretending to know an intra-period
    observation time, which these sources do not publish.
    """
    parts = period.split("-")
    if len(parts) == 1:
        return date(int(parts[0]), 1, 1)
    if len(parts) == 2:
        return date(int(parts[0]), int(parts[1]), 1)
    if len(parts) == 3:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    raise ValueError(f"unrecognised period label: {period!r}")


def _canonical_number(value: float | None) -> str:
    if value is None:
        return ""
    if value != value:  # NaN
        return "nan"
    # ``repr`` is the shortest string that round-trips a Python float, so the
    # canonical form is both stable and lossless.
    return repr(float(value))


@dataclass(frozen=True)
class ParsedTable:
    """One normalised table extracted from one raw artifact.

    Attributes:
        table_id: Stable identifier within the source file.
        banner: The source's own description of this table, preserved verbatim.
            The French files carry their column semantics only in this prose.
        columns: Column names exactly as the source wrote them.
        periods: Period labels, one per row, in source order.
        values: Row-major values; ``None`` means missing.
        frequency: Inferred from the width of the source date key.
        source_units: Units of the numbers as they appear in the raw file.
        units: Units of the numbers in :attr:`values`.
        unit_transform: The exact operation taking ``source_units`` to ``units``.
        warnings: Everything the parser had to infer, guess, or drop.
    """

    table_id: str
    banner: str
    columns: tuple[str, ...]
    periods: tuple[str, ...]
    values: tuple[tuple[float | None, ...], ...]
    frequency: Frequency
    source_units: str
    units: str
    unit_transform: str
    warnings: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        width = len(self.columns)
        if len(self.periods) != len(self.values):
            raise ValueError("periods and values must have the same length")
        for row in self.values:
            if len(row) != width:
                raise ValueError(f"row width {len(row)} does not match {width} columns")

    @property
    def rows(self) -> int:
        return len(self.periods)

    @property
    def first_observation(self) -> str | None:
        return self.periods[0] if self.periods else None

    @property
    def last_observation(self) -> str | None:
        return self.periods[-1] if self.periods else None

    def column(self, name: str) -> tuple[float | None, ...]:
        index = self.columns.index(name)
        return tuple(row[index] for row in self.values)

    def canonical_bytes(self) -> bytes:
        """Serialise deterministically for hashing.

        The form is version-tagged, unit-tagged and row-ordered: two tables hash
        alike only if they carry the same numbers *in the same units* under the
        same transform. That is the point — a percent table and the decimal table
        derived from it must not share a digest.
        """
        lines: list[str] = [
            f"canonical_form={CANONICAL_FORM_VERSION}",
            f"table_id={self.table_id}",
            f"frequency={self.frequency}",
            f"source_units={self.source_units}",
            f"units={self.units}",
            f"unit_transform={self.unit_transform}",
            _UNIT_SEPARATOR.join(("period", *self.columns)),
        ]
        for period, row in zip(self.periods, self.values, strict=True):
            lines.append(
                _UNIT_SEPARATOR.join((period, *(_canonical_number(v) for v in row)))
            )
        return ("\n".join(lines) + "\n").encode("utf-8")

    def sha256_normalized(self) -> str:
        """Digest of :meth:`canonical_bytes`."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def with_warnings(self, extra: Sequence[str]) -> ParsedTable:
        """Return a copy carrying additional warnings.

        Warnings are only ever added. A parser or validator that could remove one
        would be able to hide a data problem, which this package treats as the
        primary failure mode.
        """
        if not extra:
            return self
        merged = (*self.warnings, *extra)
        return ParsedTable(
            table_id=self.table_id,
            banner=self.banner,
            columns=self.columns,
            periods=self.periods,
            values=self.values,
            frequency=self.frequency,
            source_units=self.source_units,
            units=self.units,
            unit_transform=self.unit_transform,
            warnings=merged,
        )

    def to_frame(self) -> pd.DataFrame:
        """Return a ``DataFrame`` indexed by period label, missing values as NaN."""
        import pandas as pd

        return pd.DataFrame(
            [[float("nan") if v is None else v for v in row] for row in self.values],
            index=pd.Index(list(self.periods), name="period"),
            columns=list(self.columns),
            dtype="float64",
        )
