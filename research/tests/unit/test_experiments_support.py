"""Shared builders for the experiment-governance tests.

This module holds no tests. It is named ``test_experiments_support`` so that it
sits inside the same collection glob as the modules that import it.
"""

from __future__ import annotations

from typing import Any

from portfolio_edge.experiments.ledger import LedgerEntry, LedgerEvent, RunStatus, utc_now
from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultStatus,
)
from portfolio_edge.experiments.specification import Specification, specification_from_mapping


def valid_spec_mapping(**overrides: Any) -> dict[str, Any]:
    """A minimal specification mapping that passes every gate."""
    data: dict[str, Any] = {
        "experiment_family": "exp_test_family",
        "title": "Test experiment",
        "hypothesis": "A synthetic series has a positive mean.",
        "mechanism": "None; the series is generated, so there is no mechanism to claim.",
        "falsifier": "The point estimate of the mean is at or below zero.",
        "universe": {"description": "one synthetic monthly series"},
        "sample_policy": {
            "start": "1990-01",
            "end": "2020-12",
            "held_out": "Nothing after 2020-12 is read.",
            "eras": [
                {
                    "name": "full_sample",
                    "start": "1990-01",
                    "end": "2020-12",
                    "rationale": "The whole synthetic sample.",
                }
            ],
        },
        "benchmark": {"policy": "zero mean"},
        "primary_metric": {"name": "arithmetic mean", "units": "percent per year"},
        "secondary_metrics": ["volatility"],
        "cost_model": {"applied": False, "reason": "synthetic data has no costs"},
        "rebalance_rule": {"policy": "none"},
        "inference": {
            "bootstrap": "stationary block bootstrap",
            "block_length_policy": "frozen at 12 months, not tuned",
            "multiple_testing_correction": "holm family-wise error rate at 0.05",
        },
        "rejection_rule": "Mark rejected when the falsifier fires.",
        "run_kind": "exploratory",
        "consumes_final_holdout": False,
        "parameters": {"alpha": 1},
        "seed": 7,
        "entry_point": "test_experiment",
        "evidence_class": "policy-simulation",
    }
    data.update(overrides)
    return data


def build_spec(**overrides: Any) -> Specification:
    return specification_from_mapping(valid_spec_mapping(**overrides))


def make_entry(**overrides: Any) -> LedgerEntry:
    fields: dict[str, Any] = {
        "run_id": "run-1",
        "experiment_family": "exp_test_family",
        "timestamp_utc": utc_now().isoformat(),
        "event": LedgerEvent.STARTED,
        "status": RunStatus.STARTED,
    }
    fields.update(overrides)
    return LedgerEntry(**fields)


def sample_result(status: ResultStatus = ResultStatus.EXPLORATORY) -> ExperimentResult:
    return ExperimentResult(
        status=status,
        summary="A synthetic result used to exercise the reporting layer.",
        estimates=(
            Estimate(
                name="annualised premium",
                value=3.21,
                units="percentage points per year",
                interval=(0.4, 6.0),
                interval_method="stationary block bootstrap, 95%, 12m blocks",
                cost_basis=CostBasis.GROSS,
                n_obs=372,
            ),
            Estimate(
                name="annualised premium",
                value=2.1,
                units="percentage points per year",
                interval=(-0.7, 4.9),
                interval_method="stationary block bootstrap, 95%, 12m blocks",
                cost_basis=CostBasis.NET_PESSIMISTIC,
                n_obs=372,
            ),
            Estimate(
                name="one-sided turnover",
                value=14.0,
                units="percent per year",
                interval=None,
                uncertainty_unavailable_reason="turnover is deterministic given the policy",
            ),
        ),
        caveats=("Gross figures are an upper bound of unknown tightness.",),
        diagnostics={"months": 372},
    )
