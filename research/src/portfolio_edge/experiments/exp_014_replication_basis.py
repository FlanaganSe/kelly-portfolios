"""Experiment 014: how much of Experiment 013's clause (c) was the basis.

The defect this experiment measures
-----------------------------------
Experiment 013 audited the corrected US factor shelf and flagged a defect
against itself, in its own published page: the replicating basis it inherited
from Experiment 002 -- ``VTI, VUG, VTV, VB`` -- contains **no small-value fund**.
``VBR`` is an audited *product* in that experiment, never a building block. So
every small-value product was scored on clause (c) against a basis that
structurally cannot express small value, and part of every negative shortfall on
its systematic-value table is that limitation rather than the manager.

The basis was frozen before any of those funds was visible, so this is not a
thumb on the scale. But the magnitude was inflated by an unknown amount and
nobody had measured it. **A caveat standing next to a number is not a
correction.** This experiment replaces the caveat with the measurement.

One variable
------------
The list of tickers in the replicating basis, and nothing else. The same
committed universe file by sha256, the same 109 funds, the same
2020-01..2025-12 window, FF5+UMD from the same pinned French vintage, HAC at 6
lags, mean block 6 months, 10,000 resamples, seed 20260812, the same comparator
``VTI`` and the same four falsifier clauses at the same thresholds. **Every
loading, alpha, MDE, bootstrap interval and pedestal in this run is identical to
Experiment 013's by construction**, because the basis enters nowhere except
clauses (c) and (d).

Neither Experiment 002 nor Experiment 013 is modified. Both are asserted by
sha256 before anything is fetched, and the control basis must reproduce
Experiment 013's published clause (c) column to **zero difference** or the run
is abandoned rather than reported: if the control does not reproduce, the
difference is not the basis.

The placebos, which are the point
---------------------------------
A richer basis fits better because it can express more *and* because it has more
columns. Those are different explanations for the same movement and a basis
comparison that reports only expressive bases cannot separate them. So two of
the six bases add as many columns as the most expressive one while adding **no
size-by-style cell the frozen basis does not already carry**. Whatever they move
is what column count alone moves.

Which direction this cuts
-------------------------
Every basis here is fitted **in sample**, so every one is a best case for the
replication and a hard test for the product. **A richer basis is a harder test,
not a fairer one in the investor's favour.** The asymmetry matters: a product
that was losing to the frozen replication can be rescued by a richer basis, and
a product that was beating it can lose that advantage. Reading only the second
would be reading a comparator change as a fund result.

Run it::

    uv run python -m portfolio_edge.experiments.exp_014_replication_basis \\
        --view-results
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_002_fund_exposure import (
    PRIMARY_SPECIFICATION,
    ExposureFit,
    FundSeries,
    load_factor_panel,
)
from portfolio_edge.experiments.exp_002_universe import (
    ProductFacts,
    resolve_ticker,
    workspace_root,
)
from portfolio_edge.experiments.exp_009_exus_products import FundWindow
from portfolio_edge.experiments.exp_013_universe import (
    ScreenedUsFund,
    exp_002_screen_is_unmodified,
    load_extra_facts,
    load_product_facts,
    load_universe,
    universe_path,
)
from portfolio_edge.experiments.exp_013_us_products_union_frame import (
    ReplicationResult,
    UnionOutcome,
    UsWindowPolicy,
    _bootstrap_interval,
    _era_windows,
    _exp_002_parameters,
    _fetch_all,
    _fit_all_specifications,
    _fit_one,
    _mapping,
    _net_expense,
    _pedestal,
    _replicate,
    _sequence,
    _slice_era,
    _validate_data_path,
    _verdict,
    _window_key,
    window_for,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_count, month_index, period_from_index
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultStatus,
)
from portfolio_edge.experiments.runner import RunOutcome, run_experiment
from portfolio_edge.experiments.specification import (
    JsonValue,
    Specification,
    load_specification,
    plain_json,
)

__all__ = [
    "ENTRY_POINT",
    "BasisDeclaration",
    "BasisVariationError",
    "build_registry",
    "declared_bases",
    "default_specification_path",
    "exp_013_is_unmodified",
    "frozen_basis_fixture",
    "frozen_basis_fixture_path",
    "main",
    "reproduction_differences",
    "run",
]

ENTRY_POINT: Final = "exp_014_replication_basis"

CONTROL_BASIS_ID: Final = "A_frozen"

#: The nine products Experiment 013's caveat is about, plus the quality fund the
#: same table carries. Named in code because the page names them, and named
#: BEFORE any basis was scored: they are the funds the caveat identifies, not the
#: funds that turned out to move.
CAVEAT_TABLE: Final = (
    "AVSC",
    "DFAS",
    "RPV",
    "DFLV",
    "AVUV",
    "DFUV",
    "DFSV",
    "DFAT",
    "AVLV",
    "DUHP",
)


class BasisVariationError(RuntimeError):
    """The basis comparison could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# The frozen inputs, asserted before anything is fetched
# --------------------------------------------------------------------------- #


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frozen_inputs(specification: Specification) -> Mapping[str, JsonValue]:
    universe_block = _mapping(specification.universe, where="universe")
    return _mapping(universe_block["frozen_inputs"], where="universe.frozen_inputs")


def exp_013_is_unmodified(specification: Specification) -> dict[str, JsonValue]:
    """Refuse to run if Experiment 002 or Experiment 013 has moved.

    Five hashes, all of them declared in this experiment's own frozen YAML: the
    two specification files by raw bytes, Experiment 013's canonical
    specification hash, and its committed universe and product facts. An edit to
    either earlier experiment must fail here loudly, because a basis comparison
    against a moved baseline measures the move rather than the basis.
    """
    exp_002_screen_is_unmodified(_exp_002_parameters())
    declared = _frozen_inputs(specification)
    root = workspace_root()
    checked: dict[str, JsonValue] = {}
    files = {
        "exp_002_specification_sha256": root / "experiments" / "exp_002_fund_exposure.yaml",
        "exp_013_specification_sha256": (
            root / "experiments" / "exp_013_us_products_union_frame.yaml"
        ),
        "exp_013_universe_sha256": root / "data-manifests" / "exp_013" / "product_universe.json",
        "exp_013_product_facts_sha256": (
            root / "data-manifests" / "exp_013" / "product_facts.json"
        ),
    }
    for key, path in files.items():
        if not path.is_file():
            raise BasisVariationError(f"{key}: {path} is missing, so nothing can be asserted")
        observed = _sha256_file(path)
        expected = declared[key]
        if observed != expected:
            raise BasisVariationError(
                f"{key} has changed: {path.name} hashes {observed} against the "
                f"{expected!r} this experiment froze. Experiment 014 varies ONLY the "
                "replicating basis, so a moved baseline makes every difference it "
                "reports uninterpretable. Re-freeze deliberately or revert the edit."
            )
        checked[key] = observed

    exp_013 = load_specification(root / "experiments" / "exp_013_us_products_union_frame.yaml")
    expected_hash = declared["exp_013_specification_hash"]
    if exp_013.spec_hash != expected_hash:
        raise BasisVariationError(
            f"Experiment 013's canonical specification hash is {exp_013.spec_hash} "
            f"against the frozen {expected_hash!r}."
        )
    checked["exp_013_specification_hash"] = exp_013.spec_hash

    # The parameters this experiment promises not to touch, read from Experiment
    # 013's own file rather than restated here, so a restatement cannot drift.
    theirs = _mapping(exp_013.parameters, where="exp_013.parameters")
    ours = _mapping(specification.parameters, where="parameters")
    for key in (
        "minimum_intended_loading",
        "materiality_threshold_annual_percent",
        "hac_lags",
        "minimum_monthly_observations",
        "power_target",
        "rolling_window_months",
        "cash_series",
    ):
        if ours[key] != theirs[key]:
            raise BasisVariationError(
                f"parameter {key} is {ours[key]!r} here and {theirs[key]!r} in "
                "Experiment 013. Exactly one variable may move and it is the basis."
            )
    if specification.seed != exp_013.seed:
        raise BasisVariationError("the seed must be Experiment 013's")
    if specification.inference.resamples != exp_013.inference.resamples:
        raise BasisVariationError("the resample count must be Experiment 013's")
    if specification.sample_policy.start != exp_013.sample_policy.start:
        raise BasisVariationError("the window start must be Experiment 013's")
    if specification.sample_policy.end != exp_013.sample_policy.end:
        raise BasisVariationError("the window end must be Experiment 013's")
    checked["parameters_asserted_against_exp_013"] = True
    return checked


# --------------------------------------------------------------------------- #
# The declared bases
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class BasisDeclaration:
    """One replicating basis, declared in the frozen specification."""

    id: str
    role: str
    tickers: tuple[str, ...]
    cells: tuple[str, ...]
    why: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "id": self.id,
            "role": self.role,
            "tickers": list(self.tickers),
            "columns": len(self.tickers),
            "distinct_cells": sorted(set(self.cells)),
            "why": self.why,
        }


def declared_bases(specification: Specification) -> tuple[BasisDeclaration, ...]:
    """Every basis this experiment froze, in the order the specification lists."""
    universe_block = _mapping(specification.universe, where="universe")
    comparators = _mapping(universe_block["comparators"], where="universe.comparators")
    raw = _sequence(comparators["bases"], where="universe.comparators.bases")
    out: list[BasisDeclaration] = []
    for index, item in enumerate(raw):
        block = _mapping(item, where=f"universe.comparators.bases[{index}]")
        tickers = tuple(
            str(value) for value in _sequence(block["tickers"], where="bases[].tickers")
        )
        if len(set(tickers)) != len(tickers):
            raise BasisVariationError(f"basis {block['id']!r} repeats a ticker")
        out.append(
            BasisDeclaration(
                id=str(block["id"]),
                role=str(block["role"]),
                tickers=tickers,
                cells=tuple(
                    str(value) for value in _sequence(block["cells"], where="bases[].cells")
                ),
                why=str(block["why"]),
            )
        )
    if not out or out[0].id != CONTROL_BASIS_ID:
        raise BasisVariationError(
            f"the first declared basis must be the control {CONTROL_BASIS_ID!r}"
        )
    return tuple(out)


# --------------------------------------------------------------------------- #
# Experiment 013's published clause (c), as a committed fixture
# --------------------------------------------------------------------------- #


def frozen_basis_fixture_path() -> Path:
    return workspace_root() / "tests" / "fixtures" / "exp_013_frozen_basis_clause_c.json"


def frozen_basis_fixture() -> Mapping[str, JsonValue]:
    """Experiment 013's published clause (c) column, extracted from its artifact.

    ``artifacts/`` is not in Git, so the artifact itself cannot be an input to a
    test. This small committed file is the record of what it said, and it gets
    the same treatment as every other frozen fixture here: a disagreement with
    our own computation is a finding, never a tolerance to loosen.
    """
    payload = json.loads(frozen_basis_fixture_path().read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):  # pragma: no cover - defensive
        raise BasisVariationError("the Experiment 013 clause (c) fixture is not a mapping")
    return payload


def reproduction_differences(
    replications: Mapping[str, ReplicationResult],
    outcomes: Mapping[str, UnionOutcome],
    fixture: Mapping[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    """Compare the control basis against Experiment 013's published figures.

    The tolerance is ZERO, deliberately. The same functions run over the same
    bytes on the same months, so any difference at all is a defect and not a
    rounding artefact.
    """
    payload = frozen_basis_fixture() if fixture is None else fixture
    funds = payload["funds"]
    if not isinstance(funds, Mapping):  # pragma: no cover - defensive
        raise BasisVariationError("the fixture's funds block is not a mapping")
    missing = sorted(set(funds) - set(replications))
    extra = sorted(set(replications) - set(funds))
    worst_shortfall = 0.0
    worst_tracking = 0.0
    worst_weight = 0.0
    status_changes: list[str] = []
    for ticker, expected in sorted(funds.items()):
        if ticker not in replications:
            continue
        assert isinstance(expected, Mapping)
        observed = replications[ticker]
        expected_shortfall = float(str(expected["implementation_shortfall_pp"]))
        worst_shortfall = max(
            worst_shortfall, abs(observed.implementation_shortfall - expected_shortfall)
        )
        worst_tracking = max(
            worst_tracking,
            abs(
                observed.tracking_difference_vs_combination
                - float(str(expected["tracking_difference_vs_combination_pp"]))
            ),
        )
        weights = expected["weights"]
        assert isinstance(weights, Sequence)
        if len(weights) == len(observed.weights):
            pairs = zip(observed.weights, weights, strict=True)
            worst_weight = max(
                worst_weight,
                max((abs(a - float(str(b))) for a, b in pairs), default=0.0),
            )
        else:
            worst_weight = float("inf")
        outcome = outcomes.get(ticker)
        if outcome is not None and outcome.status != expected["status"]:
            status_changes.append(f"{ticker}: {expected['status']} -> {outcome.status}")
    reproduced = (
        not missing
        and not extra
        and not status_changes
        and worst_shortfall == 0.0
        and worst_tracking == 0.0
        and worst_weight == 0.0
    )
    return {
        "reproduced_to_zero_difference": reproduced,
        "source_run_id": payload["source_run_id"],
        "source_spec_hash": payload["source_spec_hash"],
        "funds_compared": len(funds),
        "funds_in_fixture_absent_here": missing,
        "funds_here_absent_from_fixture": extra,
        "largest_absolute_shortfall_difference_pp": worst_shortfall,
        "largest_absolute_tracking_difference_difference_pp": worst_tracking,
        "largest_absolute_weight_difference": worst_weight,
        "status_changes": status_changes,
        "tolerance": 0.0,
        "interpretation": (
            "The control basis IS Experiment 013's basis, run by Experiment 013's "
            "own functions over the same bytes and the same months. Anything other "
            "than zero here means something moved that this experiment did not "
            "vary, and every difference it reports would be uninterpretable."
        ),
    }


# --------------------------------------------------------------------------- #
# Scoring one basis
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class BasisScore:
    """What one basis does to clause (c) across the whole audited shelf."""

    declaration: BasisDeclaration
    replications: dict[str, ReplicationResult]
    outcomes: dict[str, UnionOutcome]

    def statuses(self) -> dict[str, str]:
        return {ticker: outcome.status for ticker, outcome in self.outcomes.items()}

    def shortfalls(self) -> dict[str, float]:
        return {
            ticker: item.implementation_shortfall for ticker, item in self.replications.items()
        }

    def degenerate(self) -> list[str]:
        """Funds excluded from their own basis, whose shortfall is a style return."""
        return sorted(
            ticker for ticker in self.replications if ticker in self.declaration.tickers
        )

    def to_json(self) -> dict[str, JsonValue]:
        shortfalls = list(self.shortfalls().values())
        clause_c = sum(
            1
            for outcome in self.outcomes.values()
            if any(clause.startswith("(c)") for clause in outcome.clauses_fired)
        )
        clause_d = sum(
            1
            for outcome in self.outcomes.values()
            if any(clause.startswith("(d)") for clause in outcome.clauses_fired)
        )
        weights_used = [
            sum(1 for weight in item.weights if weight > 1e-6)
            for item in self.replications.values()
        ]
        return {
            "basis": self.declaration.to_json(),
            "funds_scored": len(self.replications),
            "status_counts": {
                status: sum(1 for item in self.outcomes.values() if item.status == status)
                for status in ("exploratory", "rejected", "unresolved")
            },
            "clause_c_fired": clause_c,
            "clause_d_fired": clause_d,
            "median_implementation_shortfall_pp": float(np.median(shortfalls)),
            "mean_implementation_shortfall_pp": float(np.mean(shortfalls)),
            "negative_shortfalls": sum(1 for value in shortfalls if value < 0.0),
            "median_tracking_error_pp": float(
                np.median(
                    [item.tracking_error_vs_combination for item in self.replications.values()]
                )
            ),
            "median_non_zero_weights": float(np.median(weights_used)),
            "maximum_non_zero_weights": int(max(weights_used)) if weights_used else 0,
            "funds_replicated_at_a_corner": sum(1 for count in weights_used if count == 1),
            "median_fee_premium_pp": float(
                np.median([item.fee_premium_over_basis for item in self.replications.values()])
            ),
            "degenerate_funds_excluded_from_their_own_basis": self.degenerate(),
            "per_fund": {
                ticker: {
                    "implementation_shortfall_pp": item.implementation_shortfall,
                    "tracking_difference_vs_combination_pp": (
                        item.tracking_difference_vs_combination
                    ),
                    "tracking_error_vs_combination_pp": item.tracking_error_vs_combination,
                    "fee_premium_over_basis_pp": item.fee_premium_over_basis,
                    "weights": {
                        name: weight
                        for name, weight in zip(item.basis, item.weights, strict=True)
                        if weight > 1e-6
                    },
                    "status": self.outcomes[ticker].status,
                    "falsifier_clauses_fired": list(self.outcomes[ticker].clauses_fired),
                }
                for ticker, item in sorted(self.replications.items())
            },
        }


def _score_basis(
    declaration: BasisDeclaration,
    *,
    usable: Sequence[ScreenedUsFund],
    windows: Mapping[str, FundWindow],
    series: Mapping[str, FundSeries],
    comparator: str,
    facts: Mapping[str, ProductFacts],
    all_fits: Mapping[str, Mapping[str, ExposureFit]],
    half_fits: Mapping[tuple[str, str], ExposureFit],
    intervals: Mapping[str, Mapping[str, list[float]]],
    pedestals: Mapping[str, float],
    minimum_loading: float,
    materiality: float,
) -> BasisScore:
    replications: dict[str, ReplicationResult] = {}
    for fund in usable:
        result = _replicate(
            fund=fund,
            window=windows[fund.ticker],
            series=series,
            comparator=comparator,
            basis=declaration.tickers,
            facts=facts,
        )
        if result is not None:
            replications[fund.ticker] = result
    outcomes = {
        fund.ticker: _verdict(
            fund=fund,
            window=windows[fund.ticker],
            audited_by_exp_002=False,
            fits=all_fits[fund.ticker],
            halves={
                era: fit for (ticker, era), fit in half_fits.items() if ticker == fund.ticker
            },
            interval=intervals.get(fund.ticker, {}),
            replication=replications.get(fund.ticker),
            series=series,
            pedestal=pedestals.get(_window_key(windows[fund.ticker]), float("nan")),
            minimum_loading=minimum_loading,
            materiality=materiality,
        )
        for fund in usable
    }
    return BasisScore(declaration=declaration, replications=replications, outcomes=outcomes)


# --------------------------------------------------------------------------- #
# The decomposition, which is the deliverable
# --------------------------------------------------------------------------- #


def _decomposition(scores: Sequence[BasisScore]) -> dict[str, JsonValue]:
    control = scores[0]
    base_shortfall = control.shortfalls()
    base_status = control.statuses()
    per_basis: dict[str, JsonValue] = {}
    for score in scores[1:]:
        shortfalls = score.shortfalls()
        statuses = score.statuses()
        differences = {
            ticker: shortfalls[ticker] - base_shortfall[ticker]
            for ticker in sorted(shortfalls)
            if ticker in base_shortfall
        }
        values = list(differences.values())
        changed = [
            f"{ticker}: {base_status[ticker]} -> {statuses[ticker]}"
            for ticker in sorted(statuses)
            if statuses[ticker] != base_status[ticker]
        ]
        per_basis[score.declaration.id] = {
            "role": score.declaration.role,
            "columns": len(score.declaration.tickers),
            "distinct_cells": len(set(score.declaration.cells)),
            "median_difference_pp": float(np.median(values)),
            "mean_difference_pp": float(np.mean(values)),
            "largest_positive_difference_pp": float(max(values)),
            "largest_negative_difference_pp": float(min(values)),
            "funds_whose_shortfall_rose": sum(1 for value in values if value > 0.0),
            "funds_whose_shortfall_fell": sum(1 for value in values if value < 0.0),
            "verdicts_changed": len(changed),
            "verdict_changes": changed,
            "per_fund_difference_pp": differences,
            "caveat_table": {
                ticker: {
                    "frozen_basis_pp": base_shortfall[ticker],
                    "this_basis_pp": shortfalls[ticker],
                    "attributable_to_the_basis_pp": differences[ticker],
                    "status_frozen": base_status[ticker],
                    "status_here": statuses[ticker],
                }
                for ticker in CAVEAT_TABLE
                if ticker in differences
            },
        }
    placebos = [
        score.declaration.id for score in scores[1:] if "placebo" in score.declaration.role
    ]
    expressive = [
        score.declaration.id
        for score in scores[1:]
        if "placebo" not in score.declaration.role
    ]

    def _changed(ids: Sequence[str]) -> list[int]:
        return [int(str(_mapping(per_basis[name], where=name)["verdicts_changed"])) for name in ids]

    return {
        "control_basis": control.declaration.id,
        "sign_convention": (
            "A POSITIVE difference means the frozen basis made the product look "
            "BETTER than a basis that can express its exposure does: that part of "
            "its advantage was the comparator rather than the fund. A NEGATIVE "
            "difference means the opposite, and both occur."
        ),
        "by_basis": per_basis,
        "placebo_control": {
            "expressive_bases": expressive,
            "placebo_bases": placebos,
            "verdicts_changed_by_expressive_bases": _changed(expressive),
            "verdicts_changed_by_placebo_bases": _changed(placebos),
            "reading": (
                "The placebos add as many columns as the most expressive basis and "
                "not one new size-by-style cell. Whatever they move is what column "
                "count alone moves in a look-ahead fit, and it is the floor under "
                "any claim that an expressive basis 'corrected' something."
            ),
        },
    }


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_014_replication_basis.yaml"


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Re-score Experiment 013's clause (c) under every declared basis."""
    frozen = exp_013_is_unmodified(specification)
    bases = declared_bases(specification)

    parameters = _mapping(specification.parameters, where="parameters")
    universe_block = _mapping(specification.universe, where="universe")
    comparators = _mapping(universe_block["comparators"], where="universe.comparators")
    comparator = str(
        _mapping(comparators["broad_market"], where="comparators.broad_market")["ticker"]
    )
    minimum_loading = float(str(parameters["minimum_intended_loading"]))
    materiality = float(str(parameters["materiality_threshold_annual_percent"]))
    hac_lags = int(str(parameters["hac_lags"]))
    minimum_months = int(str(parameters["minimum_monthly_observations"]))
    power = float(str(parameters["power_target"]))

    exp_013 = load_specification(
        workspace_root() / "experiments" / "exp_013_us_products_union_frame.yaml"
    )
    dispersion = float(
        str(
            _mapping(
                _mapping(exp_013.parameters, where="exp_013.parameters")["alpha_shrinkage"],
                where="alpha_shrinkage",
            )["sigma_true_annual_percent"]
        )
    )

    universe = load_universe()
    facts = load_product_facts()
    extras = load_extra_facts()
    panel = load_factor_panel(specification)
    cache = RawCache()

    eras = _era_windows(specification)
    window_start, window_end = eras["common_period"]
    policy = UsWindowPolicy(start=window_start, end=window_end)
    full_periods = tuple(
        period_from_index(index)
        for index in range(month_index(window_start), month_index(window_end) + 1)
    )

    basis_tickers = sorted({ticker for basis in bases for ticker in basis.tickers})
    wanted: dict[str, tuple[str, str]] = {
        fund.ticker: (fund.series_id, fund.class_id) for fund in universe.passing
    }
    for ticker in (comparator, *basis_tickers):
        if ticker not in wanted:
            series_id, class_id, _name = resolve_ticker(cache, ticker)
            wanted[ticker] = (series_id, class_id)
    series, fetch_failures = _fetch_all(
        cache, tickers=wanted, start=window_start, end=window_end
    )
    gates = _validate_data_path(
        comparator=comparator, series=series, panel=panel, periods=full_periods
    )

    # Every basis constituent must cover the WHOLE frozen window. A basis fund
    # that does not is dropped per product by the replication, which would make
    # the basis silently vary fund by fund and reintroduce the confound this
    # experiment exists to remove.
    short_constituents = {
        ticker: len(series[ticker].periods) if ticker in series else 0
        for ticker in basis_tickers
        if ticker not in series
        or sorted(set(full_periods) - set(series[ticker].periods))
    }
    if short_constituents:
        raise BasisVariationError(
            "these declared basis constituents do not cover the whole frozen "
            f"window and would make the basis vary fund by fund: {short_constituents}"
        )

    windows: dict[str, FundWindow] = {}
    usable: list[ScreenedUsFund] = []
    coverage: list[dict[str, JsonValue]] = []
    for fund in universe.passing:
        record = series.get(fund.ticker)
        if record is None:
            coverage.append(
                {"ticker": fund.ticker, "usable": False, "reason": "no filings retrieved"}
            )
            continue
        extra = extras.get(fund.ticker)
        inception = None
        if extra is not None and extra.etf_inception_date is not None:
            inception = extra.etf_inception_date
        elif fund.facts is not None:
            inception = fund.facts.inception_date
        window = window_for(record, panel, policy=policy, inception=inception)
        windows[fund.ticker] = window
        coverage.append(
            {
                "ticker": fund.ticker,
                "usable": window.months >= minimum_months,
                "months_usable": window.months,
                "first_month": window.first,
                "last_month": window.last,
                "used_in_a_basis": fund.ticker in basis_tickers,
            }
        )
        if window.months >= minimum_months:
            usable.append(fund)

    # Exposures, halves, intervals and pedestals are BASIS-INVARIANT: the basis
    # enters nowhere except clauses (c) and (d). They are computed once and
    # reused across all six bases, which is not an optimisation but the claim
    # itself -- if they were recomputed per basis they could differ, and the
    # experiment would no longer be varying one thing.
    all_fits: dict[str, dict[str, ExposureFit]] = {}
    half_fits: dict[tuple[str, str], ExposureFit] = {}
    flat_fits: list[ExposureFit] = []
    for fund in usable:
        window = windows[fund.ticker]
        own = _fit_all_specifications(
            ticker=fund.ticker,
            era="common_period",
            series=series[fund.ticker],
            panel=panel,
            periods=window.periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        all_fits[fund.ticker] = own
        flat_fits.extend(own.values())
        for era_name in ("first_half", "second_half"):
            era_start, era_end = eras[era_name]
            era_periods = _slice_era(window.periods, (era_start, era_end))
            if len(era_periods) != month_count(era_start, era_end):
                continue
            fit = _fit_one(
                series[fund.ticker],
                panel,
                era_periods,
                ticker=fund.ticker,
                era=era_name,
                hac_lags=hac_lags,
                dispersion=dispersion,
                power=power,
            )
            if fit is not None:
                half_fits[(fund.ticker, era_name)] = fit

    intervals: dict[str, dict[str, list[float]]] = {}
    for fund in usable:
        if fund.intended_factor is None:
            continue
        intervals[fund.ticker] = _bootstrap_interval(
            series=series[fund.ticker],
            panel=panel,
            periods=windows[fund.ticker].periods,
            factor=fund.intended_factor,
            rng=context.rng,
            resamples=specification.inference.resamples,
            confidence=specification.inference.confidence_level,
        )

    pedestals: dict[str, float] = {}
    for fund in usable:
        key = _window_key(windows[fund.ticker])
        if key in pedestals:
            continue
        block = _pedestal(
            comparator=comparator,
            series=series,
            panel=panel,
            periods=windows[fund.ticker].periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
            facts=facts,
        )
        if block.get("available"):
            pedestals[key] = float(str(block["pedestal_annual_percent"]))

    scores = [
        _score_basis(
            declaration,
            usable=usable,
            windows=windows,
            series=series,
            comparator=comparator,
            facts=facts,
            all_fits=all_fits,
            half_fits=half_fits,
            intervals=intervals,
            pedestals=pedestals,
            minimum_loading=minimum_loading,
            materiality=materiality,
        )
        for declaration in bases
    ]

    control = scores[0]
    reproduction = reproduction_differences(control.replications, control.outcomes)
    if not reproduction["reproduced_to_zero_difference"]:
        raise BasisVariationError(
            "the control basis did not reproduce Experiment 013 to zero "
            f"difference: {json.dumps(plain_json(reproduction))}. Something other "
            "than the basis moved, so no difference this experiment reports is "
            "interpretable. Abandon the run and find what moved."
        )

    decomposition = _decomposition(scores)
    by_basis = _mapping(decomposition["by_basis"], where="by_basis")

    expressive_changes = [
        int(str(_mapping(by_basis[name], where=name)["verdicts_changed"]))
        for name in ("B_plus_small_value", "C_style_grid", "D_expressive")
        if name in by_basis
    ]
    placebo_changes = [
        int(str(_mapping(by_basis[name], where=name)["verdicts_changed"]))
        for name in by_basis
        if "placebo" in str(_mapping(by_basis[name], where=name)["role"])
    ]
    avuv = {
        score.declaration.id: score.shortfalls().get("AVUV", float("nan")) for score in scores
    }

    summary = (
        f"Experiment 013's clause (c) re-scored under {len(scores)} replicating "
        f"bases over the same {len(usable)} funds, the same window and the same "
        "falsifier, varying only the basis. The control basis reproduced "
        "Experiment 013 to zero difference in every shortfall, weight and status. "
        f"AVUV's implementation shortfall moves from "
        f"{avuv[CONTROL_BASIS_ID]:+.2f} pp/yr on the frozen basis to "
        f"{avuv.get('C_style_grid', float('nan')):+.2f} on the complete cheap style "
        "grid, so the missing small-value building block accounts for "
        f"{avuv.get('C_style_grid', float('nan')) - avuv[CONTROL_BASIS_ID]:+.2f} pp/yr "
        "of it and the rest survives. Across all 109 funds the expressive bases "
        f"change {expressive_changes} verdicts and the placebos -- same column "
        f"count, no new style cell -- change {placebo_changes}. Every basis is "
        "fitted in sample, so a richer one is a HARDER test of the product and "
        "not a fairer one in the investor's favour. Nothing is promoted."
    )

    diagnostics: dict[str, JsonValue] = {
        "relationship_to_experiment_013": {
            "what_changed": (
                "The replicating basis, and nothing else. Experiment 013's "
                "specification, committed universe and product facts were asserted "
                "by sha256 before anything was fetched, and its published clause "
                "(c) column is reproduced to zero difference by the control basis."
            ),
            "frozen_inputs_asserted": dict(frozen),
            "basis_invariant_quantities": [
                "every FF5+UMD loading and its standard error",
                "every raw and shrunk alpha and its MDE at 80% power",
                "every bootstrap interval on the intended loading",
                "every model-misfit pedestal",
                "clause (a) and clause (b), which do not read the basis",
            ],
            "alpha_family": (
                "Experiment 013's 327 fund-by-specification alpha tests, "
                f"reproduced here as {len(flat_fits)} fits and NOT re-corrected. "
                "Re-running an identical test under a different comparator does "
                "not create a new hypothesis about alpha, and reporting a second "
                "correction over the same p-values would double-count the search."
            ),
            "reproduction_of_the_control_basis": reproduction,
        },
        "bases_declared": [basis.to_json() for basis in bases],
        "basis_scores": {score.declaration.id: score.to_json() for score in scores},
        "decomposition": decomposition,
        "coverage": coverage,
        "fetch_failures": fetch_failures,
        "validation_gates": gates,
        "factor_provenance": dict(panel.provenance),
        "universe": {
            "committed_file": str(universe_path().relative_to(workspace_root())),
            "sha256": _sha256_file(universe_path()),
            "inherited_from": "exp_013_us_products_union_frame",
            "funds_audited": len(usable),
            "rebuilt_here": False,
        },
        "basis_constituent_fees": {
            ticker: _net_expense(facts.get(ticker)) for ticker in basis_tickers
        },
        "look_ahead": {
            "every_basis_is_fitted_in_sample": True,
            "direction": (
                "A richer basis is a HARDER test of the product, because the "
                "hindsight combination is handed more columns. It is not a fairer "
                "comparison in the investor's favour and no weight vector here "
                "describes a portfolio anybody could have held."
            ),
            "asymmetry": (
                "The same change rescues a product that was LOSING to its "
                "replication and removes the advantage of one that was BEATING it. "
                "Both movements are look-ahead and neither is a fund result."
            ),
            "what_would_settle_it": (
                "Weights fitted on a PRIOR window, which 72 months cannot support "
                "without shortening the estimation window further. That remains "
                "the open question Experiment 013 named, and this experiment does "
                "not answer it."
            ),
        },
        "unobservable": {
            "out_of_sample_replication": (
                "NOT COMPUTED. Every basis here is fitted on the same months it is "
                "scored on."
            ),
            "realised_taxable_distributions": (
                "NOT AVAILABLE from Form N-PORT, exactly as in Experiments 002 and "
                "013, so clause (d) is evaluated without the distribution term the "
                "falsifier names, under every basis alike."
            ),
        },
    }

    estimates: list[Estimate] = []
    for ticker in CAVEAT_TABLE:
        if ticker not in control.replications:
            continue
        fit = all_fits[ticker][PRIMARY_SPECIFICATION]
        frozen_value = control.shortfalls()[ticker]
        for score in scores[1:]:
            value = score.shortfalls()[ticker]
            estimates.append(
                Estimate(
                    name=(
                        f"{ticker} implementation shortfall attributable to the "
                        f"basis, {score.declaration.id}"
                    ),
                    value=value - frozen_value,
                    units="percentage points per year",
                    interval=None,
                    uncertainty_unavailable_reason=(
                        "Both shortfalls are look-ahead fits on the same months, so "
                        "their difference is a deterministic property of the two "
                        "bases over this window and has no sampling distribution "
                        "this construction identifies. The placebo bases bound it "
                        "instead."
                    ),
                    cost_basis=CostBasis.NET_OPTIMISTIC,
                    n_obs=fit.n_observations,
                    notes=(
                        f"frozen basis {frozen_value:+.2f} pp/yr, "
                        f"{score.declaration.id} {value:+.2f}; status "
                        f"{control.statuses()[ticker]} -> {score.statuses()[ticker]}; "
                        f"alpha {fit.alpha_annual_percent:+.2f} pp/yr against an "
                        f"MDE at 80% power of "
                        f"{fit.minimum_detectable_alpha_percent:.2f}, which is not "
                        "a promotion criterion in either direction"
                    ),
                )
            )

    caveats = [
        "EXPLORATORY. Decision 0002 stands: nothing here may promote a sleeve and "
        "nothing here may appear in the app as a finding. A change of comparator "
        "cannot lift that ceiling.",
        "EVERY basis is fitted IN SAMPLE. A richer basis is a HARDER test of the "
        "product, not a fairer one in the investor's favour, and no fitted weight "
        "vector here describes a portfolio anybody could have held.",
        "This experiment cannot make a product better or worse. It says only how "
        "much of a published number was a property of the thing it was compared "
        "against.",
        "The set of funds excluded from their own basis GROWS with the basis, and "
        "for those funds the shortfall is the realised style return of 2020-2025 "
        "rather than an implementation cost. A status change on such a fund is a "
        "change in what is being measured.",
        "The placebo bases add columns without adding a size-by-style cell. They "
        "are the floor under any claim that an expressive basis corrected "
        "something, and they must be read beside the expressive bases rather than "
        "after them.",
        "No new alpha test is performed and no alpha is re-corrected. Every alpha, "
        "MDE, loading and interval is Experiment 013's, reproduced.",
        "Item B.5 returns remain fund-reported, unaudited and uncorroborated by any "
        "independent source, in every basis alike.",
        "Every figure is PRETAX.",
    ]

    difference_rows: list[dict[str, object]] = []
    for ticker in sorted(control.replications):
        row: dict[str, object] = {
            "ticker": ticker,
            "months": control.replications[ticker].months,
            "status_frozen_basis": control.statuses()[ticker],
        }
        for score in scores:
            row[f"shortfall_{score.declaration.id}"] = score.shortfalls()[ticker]
            row[f"status_{score.declaration.id}"] = score.statuses()[ticker]
            if score.declaration.id != CONTROL_BASIS_ID:
                row[f"difference_{score.declaration.id}"] = (
                    score.shortfalls()[ticker] - control.shortfalls()[ticker]
                )
        difference_rows.append(row)

    frames = {
        "basis_decomposition": pd.DataFrame(difference_rows),
        "basis_summary": pd.DataFrame(
            [
                {
                    "basis": score.declaration.id,
                    "role": score.declaration.role,
                    "columns": len(score.declaration.tickers),
                    "distinct_cells": len(set(score.declaration.cells)),
                    "tickers": " ".join(score.declaration.tickers),
                    **{
                        f"n_{status}": sum(
                            1 for item in score.outcomes.values() if item.status == status
                        )
                        for status in ("exploratory", "rejected", "unresolved")
                    },
                    "median_shortfall_pp": float(np.median(list(score.shortfalls().values()))),
                }
                for score in scores
            ]
        ),
        "coverage": pd.DataFrame(list(coverage)),
    }

    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=summary,
        estimates=tuple(estimates),
        diagnostics=diagnostics,
        caveats=tuple(caveats),
        frames=frames,
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _show(value: float, width: int, places: int, *, signed: bool = False) -> str:
    if not math.isfinite(value):
        return "-".rjust(width)
    return f"{value:>+{width}.{places}f}" if signed else f"{value:>{width}.{places}f}"


def _render_console_report(outcome: RunOutcome) -> str:
    result = outcome.result
    if result is None:
        return "no result"
    diagnostics = result.diagnostics
    scores = diagnostics["basis_scores"]
    decomposition = diagnostics["decomposition"]
    assert isinstance(scores, Mapping) and isinstance(decomposition, Mapping)
    lines: list[str] = [result.summary, ""]

    reproduction = _mapping(
        _mapping(diagnostics["relationship_to_experiment_013"], where="rel")[
            "reproduction_of_the_control_basis"
        ],
        where="reproduction",
    )
    lines.append(
        f"control reproduces Experiment 013: "
        f"{reproduction['reproduced_to_zero_difference']} over "
        f"{reproduction['funds_compared']} funds, largest shortfall difference "
        f"{reproduction['largest_absolute_shortfall_difference_pp']}"
    )
    lines.append("")
    lines.append(
        f"{'basis':24s} {'cols':>4s} {'cells':>5s} {'expl':>5s} {'rej':>5s} "
        f"{'unres':>6s} {'(c)':>4s} {'(d)':>4s} {'med sf':>8s} {'changed':>8s}"
    )
    for name, block in scores.items():
        assert isinstance(block, Mapping)
        basis = _mapping(block["basis"], where="basis")
        counts = _mapping(block["status_counts"], where="counts")
        changed = "-"
        by_basis = _mapping(decomposition["by_basis"], where="by_basis")
        if name in by_basis:
            changed = str(_mapping(by_basis[name], where=name)["verdicts_changed"])
        cells = basis["distinct_cells"]
        assert isinstance(cells, Sequence)
        lines.append(
            f"{name:24s} {basis['columns']:>4} {len(cells):>5} "
            f"{counts['exploratory']:>5} {counts['rejected']:>5} "
            f"{counts['unresolved']:>6} {block['clause_c_fired']:>4} "
            f"{block['clause_d_fired']:>4} "
            f"{_show(float(str(block['median_implementation_shortfall_pp'])), 8, 2, signed=True)} "
            f"{changed:>8s}"
        )

    lines.append("")
    lines.append("the caveat table: shortfall by basis, pp/yr")
    ids = list(scores)
    lines.append(f"{'ticker':8s}" + "".join(f"{name[:12]:>14s}" for name in ids))
    control_block = _mapping(scores[CONTROL_BASIS_ID], where="control")
    control_funds = _mapping(control_block["per_fund"], where="per_fund")
    for ticker in CAVEAT_TABLE:
        if ticker not in control_funds:
            continue
        row = f"{ticker:8s}"
        for name in ids:
            block = _mapping(scores[name], where=name)
            funds = _mapping(block["per_fund"], where="per_fund")
            value = float(str(_mapping(funds[ticker], where=ticker)["implementation_shortfall_pp"]))
            row += _show(value, 14, 2, signed=True)
        lines.append(row)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 014 through the runner and the ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_014_replication_basis",
        description=(
            "Re-score Experiment 013's clause (c) under every declared replicating "
            "basis, writing a ledger entry for the attempt."
        ),
    )
    parser.add_argument("--specification", type=Path, default=default_specification_path())
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--artifact-root", type=Path, default=None)
    parser.add_argument(
        "--origin", choices=[item.value for item in Origin], default=Origin.AI.value
    )
    parser.add_argument(
        "--view-results",
        action="store_true",
        help=(
            "print the computed numbers AND append a results_viewed entry to the "
            "ledger. Looking is an event with consequences, so it is recorded."
        ),
    )
    arguments = parser.parse_args(argv)
    specification = load_specification(arguments.specification)

    ledger = Ledger(arguments.ledger)
    manifest_hashes: list[str] = []
    for source in specification.data_sources:
        if not isinstance(source, Mapping):
            continue
        location = source.get("manifest")
        if isinstance(location, str):
            path = workspace_root() / location
            if path.is_file():
                manifest_hashes.append(read_manifest(path).sha256_manifest())

    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=arguments.artifact_root,
        origin=Origin(arguments.origin),
        dataset_manifest_hashes=tuple(manifest_hashes),
    )

    print(f"run_id       {outcome.run_id}")
    print(f"spec_hash    {outcome.spec_hash}")
    print(f"status       {outcome.status.value}")
    print(f"result       {outcome.result.status.value if outcome.result else 'none'}")
    print(f"git_commit   {outcome.git_state.commit} (dirty={outcome.git_state.dirty})")
    for record in outcome.artifacts:
        print(f"artifact     {record.path}  {record.sha256}  {record.size_bytes}B")

    if arguments.view_results:
        print()
        print(_render_console_report(outcome))
        ledger.record_results_viewed(
            outcome.run_id,
            origin=Origin(arguments.origin),
            notes=(
                "numbers printed to the console by the --view-results flag of "
                "exp_014_replication_basis"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
