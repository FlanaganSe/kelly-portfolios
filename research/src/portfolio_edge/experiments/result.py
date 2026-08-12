"""Result artifacts: the closed status taxonomy and estimates that carry uncertainty.

Two rules are enforced by construction here rather than by review.

1. A result carries a :class:`ResultStatus` from a closed enum. There is no
   "works" and no "does not work"; an unlisted status cannot be represented.
2. An :class:`Estimate` carries its units and either an interval or an explicit,
   recorded reason why no interval could be computed. A bare point estimate is
   rejected at construction time.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

import pandas as pd

from portfolio_edge.experiments.specification import JsonValue, RunKind, plain_json


class ResultStatus(StrEnum):
    """The promotion ladder. Closed on purpose.

    Ordering is deliberately *not* defined arithmetically: ``rejected`` and
    ``unresolved`` are terminal outcomes, not low rungs.
    """

    EXPLORATORY = "exploratory"
    SOURCE_REPRODUCED = "source-reproduced"
    INDEPENDENTLY_REPRODUCED = "independently-reproduced"
    WALK_FORWARD_TESTED = "walk-forward-tested"
    SHADOW_LIVE = "shadow-live"
    PRODUCTION_ELIGIBLE = "production-eligible"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"


CONFIRMATORY_ONLY_STATUSES: frozenset[ResultStatus] = frozenset(
    {
        ResultStatus.WALK_FORWARD_TESTED,
        ResultStatus.SHADOW_LIVE,
        ResultStatus.PRODUCTION_ELIGIBLE,
    }
)
"""Statuses an exploratory run may not claim. Searching is not deciding."""


def statuses_available_to(run_kind: RunKind) -> frozenset[ResultStatus]:
    if run_kind is RunKind.CONFIRMATORY:
        return frozenset(ResultStatus)
    return frozenset(ResultStatus) - CONFIRMATORY_ONLY_STATUSES


class ResultError(ValueError):
    """A result is malformed: missing uncertainty, units, or a valid status."""


class CostBasis(StrEnum):
    """Which cost assumption produced a figure.

    Gross, net-optimistic and net-pessimistic are separate columns everywhere and
    are never averaged or collapsed. The spread between them *is* the visible
    model uncertainty in the cost assumption.
    """

    GROSS = "gross"
    NET_OPTIMISTIC = "net-optimistic"
    NET_PESSIMISTIC = "net-pessimistic"
    NOT_APPLICABLE = "not-applicable"


@dataclass(frozen=True, slots=True, kw_only=True)
class Estimate:
    """One reported statistic, with its units and its uncertainty.

    ``interval`` may be ``None`` only when ``uncertainty_unavailable_reason``
    states why. That is not an escape hatch for laziness: the reason is written
    into the artifact and rendered in the table.
    """

    name: str
    value: float
    units: str
    """e.g. ``percent per year``, ``ratio``, ``months``, ``percent of NAV``."""
    interval: tuple[float, float] | None = None
    interval_method: str = ""
    """e.g. ``stationary block bootstrap, 95%, mean block 12m, 10000 resamples``."""
    cost_basis: CostBasis = CostBasis.NOT_APPLICABLE
    n_obs: int | None = None
    notes: str = ""
    uncertainty_unavailable_reason: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ResultError("estimate name must be non-empty")
        if not self.units.strip():
            raise ResultError(
                f"estimate {self.name!r} must declare units; a unitless number is unreadable"
            )
        if self.interval is None:
            if not self.uncertainty_unavailable_reason.strip():
                raise ResultError(
                    f"estimate {self.name!r} has no interval and no stated reason. "
                    "A bare point estimate is a bug: supply an interval, or record "
                    "uncertainty_unavailable_reason explaining why none exists."
                )
            return
        low, high = self.interval
        if not (low <= high):
            raise ResultError(
                f"estimate {self.name!r} has an inverted interval: {low!r} > {high!r}"
            )
        if not self.interval_method.strip():
            raise ResultError(
                f"estimate {self.name!r} reports an interval without naming the method "
                "that produced it; an unattributed interval cannot be checked"
            )

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "value": self.value,
            "units": self.units,
            "interval": list(self.interval) if self.interval is not None else None,
            "interval_method": self.interval_method,
            "cost_basis": self.cost_basis.value,
            "n_obs": self.n_obs,
            "notes": self.notes,
            "uncertainty_unavailable_reason": self.uncertainty_unavailable_reason,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactRecord:
    """One written file, its hash, and its size. Ledger-ready."""

    path: str
    """Path relative to the artifact root, POSIX-separated."""
    sha256: str
    size_bytes: int
    kind: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "kind": self.kind,
        }

    @classmethod
    def from_json(cls, data: Mapping[str, JsonValue]) -> ArtifactRecord:
        path = data.get("path")
        sha256 = data.get("sha256")
        size = data.get("size_bytes")
        kind = data.get("kind", "unknown")
        if not isinstance(path, str) or not isinstance(sha256, str):
            raise ResultError(f"artifact record needs string path and sha256, got {data!r}")
        if not isinstance(size, int) or isinstance(size, bool):
            raise ResultError(f"artifact record needs an integer size_bytes, got {data!r}")
        return cls(path=path, sha256=sha256, size_bytes=size, kind=str(kind))


@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentResult:
    """What an experiment callable returns.

    ``frames`` are optional tabular payloads written to Parquet beside the JSON
    summary; they stay out of Git. ``caveats`` are rendered with the table, not
    filed away: the point of this layer is that the reader cannot miss them.
    """

    status: ResultStatus
    summary: str
    estimates: tuple[Estimate, ...] = ()
    diagnostics: Mapping[str, JsonValue] = field(default_factory=dict)
    caveats: tuple[str, ...] = ()
    frames: Mapping[str, pd.DataFrame] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, ResultStatus):
            raise ResultError(
                f"status must be a ResultStatus, got {self.status!r}. "
                f"Allowed: {', '.join(item.value for item in ResultStatus)}"
            )
        if not self.summary.strip():
            raise ResultError("a result must carry a summary sentence")
        seen: set[tuple[str, CostBasis]] = set()
        for estimate in self.estimates:
            key = (estimate.name, estimate.cost_basis)
            if key in seen:
                raise ResultError(
                    f"duplicate estimate {estimate.name!r} on cost basis "
                    f"{estimate.cost_basis.value!r}: two different numbers cannot share a cell"
                )
            seen.add(key)

    def estimates_named(self, name: str) -> tuple[Estimate, ...]:
        return tuple(estimate for estimate in self.estimates if estimate.name == name)

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "status": self.status.value,
            "summary": self.summary,
            "estimates": [estimate.to_json() for estimate in self.estimates],
            "diagnostics": plain_json(dict(self.diagnostics)),
            "caveats": list(self.caveats),
            "frame_names": sorted(self.frames),
        }


def check_status_allowed(status: ResultStatus, run_kind: RunKind) -> None:
    """Refuse a promotion claim that the run kind cannot support."""
    allowed = statuses_available_to(run_kind)
    if status not in allowed:
        raise ResultError(
            f"result status {status.value!r} requires run_kind "
            f"{RunKind.CONFIRMATORY.value!r}; this run is {run_kind.value!r}. "
            "An exploratory search cannot promote its own finding."
        )


def estimates_by_cost_basis(
    estimates: Sequence[Estimate],
) -> dict[str, dict[CostBasis, Estimate]]:
    """Group estimates by name, keeping cost bases in separate cells."""
    grouped: dict[str, dict[CostBasis, Estimate]] = {}
    for estimate in estimates:
        grouped.setdefault(estimate.name, {})[estimate.cost_basis] = estimate
    return grouped
