"""A bare point estimate is a bug, and cost bases never share a column."""

from __future__ import annotations

import pytest

from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultError,
    ResultStatus,
)
from portfolio_edge.reporting.tables import (
    TableError,
    format_estimate,
    render_estimates_table,
    render_result,
)
from tests.unit.test_experiments_support import build_spec, sample_result


def _estimate(**overrides: object) -> Estimate:
    fields: dict[str, object] = {
        "name": "annualised premium",
        "value": 1.5,
        "units": "percentage points per year",
        "interval": (0.2, 2.8),
        "interval_method": "block bootstrap 95%",
        "cost_basis": CostBasis.GROSS,
    }
    fields.update(overrides)
    return Estimate(**fields)  # type: ignore[arg-type]


def test_point_estimate_without_an_interval_is_refused() -> None:
    with pytest.raises(ResultError, match="bare point estimate is a bug"):
        _estimate(interval=None, interval_method="")


def test_missing_uncertainty_is_allowed_only_with_a_recorded_reason() -> None:
    estimate = _estimate(
        interval=None,
        interval_method="",
        uncertainty_unavailable_reason="deterministic given the policy",
    )
    assert "no interval: deterministic given the policy" in format_estimate(estimate)


def test_units_are_required() -> None:
    with pytest.raises(ResultError, match="must declare units"):
        _estimate(units="  ")


def test_an_interval_must_name_its_method() -> None:
    with pytest.raises(ResultError, match="without naming the method"):
        _estimate(interval_method="")


def test_inverted_interval_is_refused() -> None:
    with pytest.raises(ResultError, match="inverted interval"):
        _estimate(interval=(2.0, 1.0))


def test_cost_bases_stay_in_separate_columns() -> None:
    estimates = (
        _estimate(value=5.0, cost_basis=CostBasis.GROSS),
        _estimate(value=4.0, cost_basis=CostBasis.NET_OPTIMISTIC),
        _estimate(value=2.0, cost_basis=CostBasis.NET_PESSIMISTIC),
    )
    table = render_estimates_table(estimates)
    header, _, row = table.splitlines()
    assert header.split("|")[3:6] == [" Gross ", " Net-optimistic ", " Net-pessimistic "]
    cells = [cell.strip() for cell in row.split("|")[1:-1]]
    assert cells[2].startswith("5")
    assert cells[3].startswith("4")
    assert cells[4].startswith("2")


def test_a_missing_cost_basis_renders_as_an_admission_not_a_blank() -> None:
    table = render_estimates_table((_estimate(cost_basis=CostBasis.GROSS),))
    row = table.splitlines()[-1]
    assert row.count("not reported") == 2


def test_two_units_in_one_row_are_refused() -> None:
    estimates = (
        _estimate(cost_basis=CostBasis.GROSS, units="percent per year"),
        _estimate(cost_basis=CostBasis.NET_PESSIMISTIC, units="ratio"),
    )
    with pytest.raises(TableError, match="more than one unit"):
        render_estimates_table(estimates)


def test_two_numbers_cannot_share_a_cell() -> None:
    with pytest.raises(ResultError, match="cannot share a cell"):
        ExperimentResult(
            status=ResultStatus.EXPLORATORY,
            summary="two numbers, one cell",
            estimates=(_estimate(value=1.0), _estimate(value=2.0)),
        )


def test_rendered_result_carries_status_provenance_and_caveats() -> None:
    spec = build_spec()
    rendered = render_result(sample_result(), specification=spec, run_id="run-123")
    assert "`exploratory`" in rendered
    assert "a search, not a finding" in rendered
    assert spec.spec_hash in rendered
    assert "run-123" in rendered
    assert spec.falsifier in rendered
    assert "Gross figures are an upper bound" in rendered
    assert "never collapsed" in rendered


def test_pipes_in_text_do_not_break_the_table() -> None:
    rendered = render_estimates_table((_estimate(name="a|b"),))
    assert r"a\|b" in rendered
    row = rendered.splitlines()[-1]
    assert len(row.split(" | ")) == 6  # the escaped pipe does not open a new column


def test_a_result_with_no_statistics_says_so() -> None:
    result = ExperimentResult(status=ResultStatus.UNRESOLVED, summary="nothing computed")
    rendered = render_result(result)
    assert "No statistics were reported." in rendered
    assert "cannot answer the question" in rendered


def test_uncosted_statistics_render_in_their_own_table() -> None:
    rendered = render_result(sample_result())
    assert "Statistics with no cost basis:" in rendered
    assert "one-sided turnover" in rendered


def test_a_summary_is_required() -> None:
    with pytest.raises(ResultError, match="summary"):
        ExperimentResult(status=ResultStatus.EXPLORATORY, summary="   ")


def test_status_must_be_a_member_of_the_taxonomy() -> None:
    with pytest.raises(ResultError, match="status must be a ResultStatus"):
        ExperimentResult(status="works", summary="s")  # type: ignore[arg-type]
