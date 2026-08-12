"""Render a result as a compact Markdown table for a research synthesis.

Three rules are enforced here, because a table is where a hedged result quietly
becomes a headline number.

1. **Every statistic carries its uncertainty and its units.** A point estimate
   with neither an interval nor a recorded reason for its absence cannot be
   constructed (see :class:`~portfolio_edge.experiments.result.Estimate`), and a
   missing interval renders as a visible admission, not a blank.
2. **Gross, net-optimistic and net-pessimistic stay in separate columns.** They
   are never averaged, never collapsed, and a missing one renders as
   ``not reported`` rather than as an empty cell.
3. **The status is printed with the table.** There is no rendering path that
   produces numbers without the status taxonomy attached.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final

from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultStatus,
    estimates_by_cost_basis,
)
from portfolio_edge.experiments.specification import Specification

_MISSING: Final = "not reported"
_COST_COLUMNS: Final = (CostBasis.GROSS, CostBasis.NET_OPTIMISTIC, CostBasis.NET_PESSIMISTIC)

_STATUS_MEANING: Final[Mapping[ResultStatus, str]] = {
    ResultStatus.EXPLORATORY: (
        "a search, not a finding; it may not be quoted as evidence that anything works"
    ),
    ResultStatus.SOURCE_REPRODUCED: (
        "a published table was reproduced from the author's own distributed data"
    ),
    ResultStatus.INDEPENDENTLY_REPRODUCED: (
        "reproduced from an independent data path and an independent implementation"
    ),
    ResultStatus.WALK_FORWARD_TESTED: (
        "survived nested walk-forward evaluation with the search corrected for"
    ),
    ResultStatus.SHADOW_LIVE: "tracked on a frozen shadow portfolio, no capital at risk",
    ResultStatus.PRODUCTION_ELIGIBLE: (
        "eligible for capital under the declared policy; not a prediction of returns"
    ),
    ResultStatus.REJECTED: "the predeclared falsifier fired",
    ResultStatus.UNRESOLVED: (
        "the available evidence cannot answer the question; this is not a negative result"
    ),
}


class TableError(ValueError):
    """A result cannot be rendered honestly."""


def format_number(value: float) -> str:
    return f"{value:.4g}"


def format_estimate(estimate: Estimate) -> str:
    """``value [low, high]``, or the recorded reason no interval exists."""
    point = format_number(estimate.value)
    if estimate.interval is None:
        return f"{point} (no interval: {estimate.uncertainty_unavailable_reason})"
    low, high = estimate.interval
    return f"{point} [{format_number(low)}, {format_number(high)}]"


def _escape(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", " ").strip()


def _row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render_estimates_table(estimates: Sequence[Estimate]) -> str:
    """Render the cost-basis table: one row per statistic, one column per basis."""
    costed = [item for item in estimates if item.cost_basis is not CostBasis.NOT_APPLICABLE]
    if not costed:
        return ""
    grouped = estimates_by_cost_basis(costed)
    header = ["Statistic", "Units", "Gross", "Net-optimistic", "Net-pessimistic", "Interval method"]
    lines = [_row(header), _row(["---"] * len(header))]
    for name, by_basis in grouped.items():
        units = {item.units for item in by_basis.values()}
        if len(units) > 1:
            raise TableError(
                f"statistic {name!r} is reported in more than one unit: {sorted(units)}. "
                "Two units in one row would be read as one number."
            )
        cells = [_escape(name), _escape(next(iter(units)))]
        methods: list[str] = []
        for basis in _COST_COLUMNS:
            estimate = by_basis.get(basis)
            if estimate is None:
                cells.append(_MISSING)
                continue
            cells.append(_escape(format_estimate(estimate)))
            if estimate.interval_method and estimate.interval_method not in methods:
                methods.append(estimate.interval_method)
        cells.append(_escape("; ".join(methods)) if methods else _MISSING)
        lines.append(_row(cells))
    return "\n".join(lines)


def render_uncosted_table(estimates: Sequence[Estimate]) -> str:
    """Render statistics for which a cost basis does not apply."""
    plain = [item for item in estimates if item.cost_basis is CostBasis.NOT_APPLICABLE]
    if not plain:
        return ""
    header = ["Statistic", "Units", "Value", "Interval method", "Observations"]
    lines = [_row(header), _row(["---"] * len(header))]
    for estimate in plain:
        lines.append(
            _row(
                [
                    _escape(estimate.name),
                    _escape(estimate.units),
                    _escape(format_estimate(estimate)),
                    _escape(estimate.interval_method) if estimate.interval_method else _MISSING,
                    str(estimate.n_obs) if estimate.n_obs is not None else _MISSING,
                ]
            )
        )
    return "\n".join(lines)


def render_result(
    result: ExperimentResult,
    *,
    specification: Specification | None = None,
    run_id: str | None = None,
) -> str:
    """Render a complete, paste-ready block: heading, provenance, tables, caveats."""
    title = specification.title if specification is not None else result.summary
    lines: list[str] = [f"### {_escape(title)}", ""]

    provenance: list[tuple[str, str]] = [
        ("Status", f"`{result.status.value}` — {_STATUS_MEANING[result.status]}"),
    ]
    if run_id is not None:
        provenance.append(("Run", f"`{run_id}`"))
    if specification is not None:
        provenance.extend(
            [
                ("Experiment family", f"`{specification.experiment_family}`"),
                ("Specification hash", f"`{specification.spec_hash}`"),
                ("Run kind", f"`{specification.run_kind.value}`"),
                ("Evidence class", f"`{specification.evidence_class.value}`"),
                ("Falsifier", _escape(specification.falsifier)),
            ]
        )
    lines.extend(f"- **{label}:** {value}" for label, value in provenance)
    lines.extend(["", _escape(result.summary), ""])

    costed = render_estimates_table(result.estimates)
    if costed:
        lines.extend(
            [
                "Gross, net-optimistic and net-pessimistic are separate columns and are "
                "never collapsed; the spread between them is the cost-model uncertainty.",
                "",
                costed,
                "",
            ]
        )
    uncosted = render_uncosted_table(result.estimates)
    if uncosted:
        lines.extend(["Statistics with no cost basis:", "", uncosted, ""])
    if not costed and not uncosted:
        lines.extend(["No statistics were reported.", ""])

    if result.caveats:
        lines.append("**Caveats.**")
        lines.extend(f"- {_escape(caveat)}" for caveat in result.caveats)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
