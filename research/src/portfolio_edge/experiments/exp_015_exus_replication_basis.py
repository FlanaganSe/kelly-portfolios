"""Experiment 015: how much of Experiment 009's clause (c) was the ex-US basis.

The debt this pays
------------------
Experiment 014 varied the US audit's clause (c) comparator and found two things.
Twenty-seven per cent of the systematic-value shortfall magnitude was the
comparator rather than the fund. And -- the larger finding -- two **placebo**
bases, ten columns each and adding no new size-by-style cell, moved 9 and 15
verdicts while the genuinely expressive bases moved 1, 5 and 5. Clause (c)
responds substantially to *how many columns a look-ahead fit is handed*, not only
to what they span, and decision record 0003 now requires a fitted comparator to
carry a placebo comparator beside it.

**Experiment 009's ex-US basis has never been varied.** That matters more than
the US case did. Experiments 005 and 006 located value at +4.7 pp/yr and momentum
at +7.3 pp/yr pooled across three regions, both carried by the two non-US
regions, so the ex-US products are the implementation path for the only premia
that reached ``exploratory`` at all. And the ex-US clause (c) rejections look
fragile on their face: ``GWX`` carries the largest intended loading in the whole
ex-US audit at **+0.856** and is rejected on clause (c) alone.

One variable
------------
The list of tickers in the replicating basis, and nothing else. The same
committed universe file and the same committed product facts by sha256, the same
25 audited funds and their windows, the same **regional** factor panels, HAC at 6
lags, mean block 6 months, 10,000 resamples, seed 20260812, the same regional
comparators ``VEA`` and ``VWO`` and the same four falsifier clauses at the same
thresholds. **Every loading, alpha, MDE, bootstrap interval and pedestal in this
run is identical to Experiment 009's by construction**, because the basis enters
nowhere except clauses (c) and (d).

Neither Experiment 002 nor Experiment 009 is modified. Both are asserted before
anything is fetched, and the control basis must reproduce Experiment 009's
published clause (c) column to **zero difference** or the run is abandoned rather
than reported: if the control does not reproduce, the difference is not the
basis.

Span is not coverage, and the ex-US shelf makes that concrete
-------------------------------------------------------------
Experiment 009 drops a basis constituent that does not cover a fund's own months,
so its basis silently varies fund by fund. ``GWX`` and ``RODM`` file from
2019-07, one month before every declared constituent except ``VEA``, ``EWX`` and
``MFEM``, so under the frozen basis **they were replicated by VEA alone** -- a
developed large-cap fund standing in for a developed small-cap fund. That is a
**coverage** artefact, not a **span** artefact. This module reports the columns
each fund's basis actually contained under every basis, names every reduced set,
and carries a separately labelled second-variable diagnostic that recomputes
GWX's and RODM's clause (c) on windows trimmed to 2019-08. That diagnostic moves
the window as well as the basis and therefore never produces a status.

The panel is named everywhere
-----------------------------
Experiment 009's fifth conclusion is that grading these funds on the US panel
instead of their own would put 16 of 25 below the 0.15 bar rather than 5, moving
individual loadings by up to 0.480. **An ex-US loading without its panel named is
not a number**, so every loading reported here carries the region whose French
file produced it.

Which direction this cuts
-------------------------
Every basis here is fitted **in sample**, so every one is a best case for the
replication and a hard test for the product. **A richer basis is a harder test,
not a fairer one in the investor's favour.** Twelve products reached
``exploratory`` in Experiment 009 and whether they survive matters more than
whether the five rejections are reversed.

Run it::

    uv run python -m portfolio_edge.experiments.exp_015_exus_replication_basis \\
        --view-results
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
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
)
from portfolio_edge.experiments.exp_002_universe import (
    ProductFacts,
    resolve_ticker,
    workspace_root,
)
from portfolio_edge.experiments.exp_009_exus_products import (
    _OPPOSITE_REGION,
    ExUsOutcome,
    FundWindow,
    RegionalFits,
    ReplicationResult,
    _bootstrap_interval,
    _era_windows,
    _exp_002_parameters,
    _fetch_all,
    _fit_all_specifications,
    _fit_on,
    _mapping,
    _net_expense,
    _pedestal,
    _replicate,
    _sequence,
    _slice_era,
    _validate_regional_path,
    _verdict,
    _window_for,
    load_regional_panel,
)
from portfolio_edge.experiments.exp_009_universe import (
    GRADED_REGIONS,
    ScreenedExUsFund,
    exp_002_screen_is_unmodified,
    load_extra_facts,
    load_product_facts,
    load_universe,
    product_facts_path,
    universe_path,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_index
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
    "BasisScore",
    "ExUsBasisVariationError",
    "build_registry",
    "declared_bases",
    "declared_coverage",
    "default_specification_path",
    "exp_009_is_unmodified",
    "frozen_basis_fixture",
    "frozen_basis_fixture_path",
    "main",
    "reproduction_differences",
    "run",
]

ENTRY_POINT: Final = "exp_015_exus_replication_basis"

CONTROL_BASIS_ID: Final = "A_frozen"

#: The five funds Experiment 009 rejected on clause (c), plus the two whose
#: clause (c) is the realised style return of a degenerate basis. Named in code
#: because the page names them, and named BEFORE any basis was scored: they are
#: the funds whose verdict clause (c) decided, not the funds that turned out to
#: move.
CLAUSE_C_TABLE: Final = ("GWX", "EFG", "DIHP", "RODM", "IMFL", "EFV", "SCZ")

#: Every emerging product in the audit. The question "can a basis that expresses
#: emerging move an emerging verdict" is asked of exactly these four.
EMERGING_PRODUCTS: Final = ("AVES", "DFEV", "JHEM", "MFEM")

#: The funds whose filed history begins one month before every basis constituent
#: except VEA, EWX and MFEM. Their clause (c) is decided by COVERAGE rather than
#: by span, and the second-variable diagnostic is computed for exactly these.
COVERAGE_DIAGNOSTIC_FUNDS: Final = ("GWX", "RODM")

#: The first month the coverage diagnostic trims to, so that every constituent of
#: every declared basis is available. Frozen here rather than derived from the
#: data, because a trim chosen after seeing a result is not a diagnostic.
COVERAGE_DIAGNOSTIC_FIRST_MONTH: Final = "2019-08"


class ExUsBasisVariationError(RuntimeError):
    """The basis comparison could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# The frozen inputs, asserted before anything is fetched
# --------------------------------------------------------------------------- #


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frozen_inputs(specification: Specification) -> Mapping[str, JsonValue]:
    universe_block = _mapping(specification.universe, where="universe")
    return _mapping(universe_block["frozen_inputs"], where="universe.frozen_inputs")


def exp_009_is_unmodified(specification: Specification) -> dict[str, JsonValue]:
    """Refuse to run if Experiment 002 or Experiment 009 has moved.

    Five hashes, all declared in this experiment's own frozen YAML: the two
    specification files by raw bytes, Experiment 009's canonical specification
    hash, and its committed universe and product facts. The product facts are
    asserted as well as the universe because every basis constituent's fee is
    read from that file, so an edit there would change a clause (c) figure
    without changing a single ticker.
    """
    exp_002_screen_is_unmodified(_exp_002_parameters())
    declared = _frozen_inputs(specification)
    root = workspace_root()
    checked: dict[str, JsonValue] = {}
    files = {
        "exp_002_specification_sha256": root / "experiments" / "exp_002_fund_exposure.yaml",
        "exp_009_specification_sha256": (
            root / "experiments" / "exp_009_exus_factor_products.yaml"
        ),
        "exp_009_universe_sha256": universe_path(),
        "exp_009_product_facts_sha256": product_facts_path(),
    }
    for key, path in files.items():
        if not path.is_file():
            raise ExUsBasisVariationError(
                f"{key}: {path} is missing, so nothing can be asserted"
            )
        observed = _sha256_file(path)
        expected = declared[key]
        if observed != expected:
            raise ExUsBasisVariationError(
                f"{key} has changed: {path.name} hashes {observed} against the "
                f"{expected!r} this experiment froze. Experiment 015 varies ONLY the "
                "replicating basis, so a moved baseline makes every difference it "
                "reports uninterpretable. Re-freeze deliberately or revert the edit."
            )
        checked[key] = observed

    exp_009 = load_specification(root / "experiments" / "exp_009_exus_factor_products.yaml")
    expected_hash = declared["exp_009_specification_hash"]
    if exp_009.spec_hash != expected_hash:
        raise ExUsBasisVariationError(
            f"Experiment 009's canonical specification hash is {exp_009.spec_hash} "
            f"against the frozen {expected_hash!r}."
        )
    checked["exp_009_specification_hash"] = exp_009.spec_hash

    # The parameters this experiment promises not to touch, read from Experiment
    # 009's own file rather than restated here, so a restatement cannot drift.
    theirs = _mapping(exp_009.parameters, where="exp_009.parameters")
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
            raise ExUsBasisVariationError(
                f"parameter {key} is {ours[key]!r} here and {theirs[key]!r} in "
                "Experiment 009. Exactly one variable may move and it is the basis."
            )
    if specification.seed != exp_009.seed:
        raise ExUsBasisVariationError("the seed must be Experiment 009's")
    if specification.inference.resamples != exp_009.inference.resamples:
        raise ExUsBasisVariationError("the resample count must be Experiment 009's")
    if specification.sample_policy.start != exp_009.sample_policy.start:
        raise ExUsBasisVariationError("the window start must be Experiment 009's")
    if specification.sample_policy.end != exp_009.sample_policy.end:
        raise ExUsBasisVariationError("the window end must be Experiment 009's")
    if _era_windows(specification) != _era_windows(exp_009):
        raise ExUsBasisVariationError("every era must be Experiment 009's, unchanged")
    checked["parameters_asserted_against_exp_009"] = True
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

    @property
    def is_placebo(self) -> bool:
        return "placebo" in self.role

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "id": self.id,
            "role": self.role,
            "tickers": list(self.tickers),
            "columns": len(self.tickers),
            "distinct_cells": sorted(set(self.cells)),
            "why": self.why,
        }


def _comparators(specification: Specification) -> Mapping[str, JsonValue]:
    universe_block = _mapping(specification.universe, where="universe")
    return _mapping(universe_block["comparators"], where="universe.comparators")


def declared_bases(specification: Specification) -> tuple[BasisDeclaration, ...]:
    """Every basis this experiment froze, in the order the specification lists."""
    raw = _sequence(
        _comparators(specification)["bases"], where="universe.comparators.bases"
    )
    out: list[BasisDeclaration] = []
    for index, item in enumerate(raw):
        block = _mapping(item, where=f"universe.comparators.bases[{index}]")
        tickers = tuple(
            str(value) for value in _sequence(block["tickers"], where="bases[].tickers")
        )
        if len(set(tickers)) != len(tickers):
            raise ExUsBasisVariationError(f"basis {block['id']!r} repeats a ticker")
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
        raise ExUsBasisVariationError(
            f"the first declared basis must be the control {CONTROL_BASIS_ID!r}"
        )
    return tuple(out)


def declared_coverage(specification: Specification) -> dict[str, str]:
    """The first month each constituent is frozen to cover, before the run.

    Coverage decides which columns a fund's basis actually contained, and on this
    shelf that decides two of the five clause (c) rejections. Writing it down in
    the specification makes it part of the design; discovering it afterwards
    would make it a result.
    """
    block = _mapping(
        _comparators(specification)["coverage_is_frozen_not_discovered"],
        where="universe.comparators.coverage_is_frozen_not_discovered",
    )
    declared = _mapping(block["first_month_covered"], where="first_month_covered")
    return {ticker: str(value) for ticker, value in declared.items()}


def _assert_declared_coverage(
    specification: Specification, series: Mapping[str, FundSeries]
) -> dict[str, JsonValue]:
    """Check the frozen coverage against the filings actually retrieved."""
    declared = declared_coverage(specification)
    used = {ticker for basis in declared_bases(specification) for ticker in basis.tickers}
    missing = sorted(used - set(declared))
    if missing:
        raise ExUsBasisVariationError(
            f"these basis constituents have no frozen first month of coverage: {missing}"
        )
    disagreements: list[str] = []
    observed: dict[str, JsonValue] = {}
    for ticker in sorted(used):
        record = series.get(ticker)
        if record is None or not record.periods:
            disagreements.append(f"{ticker}: no filings retrieved at all")
            continue
        first = min(record.periods)
        observed[ticker] = first
        if first != declared[ticker]:
            disagreements.append(
                f"{ticker}: filings begin {first} against the frozen {declared[ticker]}"
            )
    if disagreements:
        raise ExUsBasisVariationError(
            "the frozen coverage does not describe the filings: "
            + "; ".join(disagreements)
            + ". Coverage decides which columns a fund's basis contained, so a "
            "surprise here changes what this experiment measures."
        )
    return {"declared": dict(declared), "observed": observed, "agree": True}


# --------------------------------------------------------------------------- #
# Experiment 009's published verdict, as a committed fixture
# --------------------------------------------------------------------------- #


def frozen_basis_fixture_path() -> Path:
    return workspace_root() / "tests" / "fixtures" / "exp_009_frozen_basis_clause_c.json"


def frozen_basis_fixture() -> Mapping[str, JsonValue]:
    """Experiment 009's published clause (c) column, extracted from its artifact.

    ``artifacts/`` is not in Git, so the artifact itself cannot be an input to a
    test. This small committed file is the record of what it said, and it gets
    the same treatment as every other frozen fixture here: a disagreement with
    our own computation is a finding, never a tolerance to loosen.
    """
    payload = json.loads(frozen_basis_fixture_path().read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):  # pragma: no cover - defensive
        raise ExUsBasisVariationError("the Experiment 009 clause (c) fixture is not a mapping")
    return payload


def reproduction_differences(
    replications: Mapping[str, ReplicationResult],
    outcomes: Mapping[str, ExUsOutcome],
    fixture: Mapping[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    """Compare the control basis against Experiment 009's published figures.

    The tolerance is ZERO, deliberately. The same functions run over the same
    bytes on the same months, so any difference at all is a defect and not a
    rounding artefact. Statuses are compared for all 25 funds and clause (c)
    figures for the 24 that have a replication at all -- ``MFEM`` has none in any
    basis, because Experiment 009 requires the region's comparator to cover the
    window and ``VWO`` does not cover MFEM's first month.
    """
    payload = frozen_basis_fixture() if fixture is None else fixture
    funds = payload["funds"]
    if not isinstance(funds, Mapping):  # pragma: no cover - defensive
        raise ExUsBasisVariationError("the fixture's funds block is not a mapping")
    missing = sorted(set(funds) - set(outcomes))
    extra = sorted(set(outcomes) - set(funds))
    worst_shortfall = 0.0
    worst_tracking = 0.0
    worst_weight = 0.0
    status_changes: list[str] = []
    replication_presence_changes: list[str] = []
    compared = 0
    for ticker, expected in sorted(funds.items()):
        assert isinstance(expected, Mapping)
        outcome = outcomes.get(ticker)
        if outcome is not None and outcome.status != expected["status"]:
            status_changes.append(f"{ticker}: {expected['status']} -> {outcome.status}")
        observed = replications.get(ticker)
        if bool(expected["replication_fitted"]) != (observed is not None):
            replication_presence_changes.append(ticker)
            continue
        if observed is None:
            continue
        compared += 1
        worst_shortfall = max(
            worst_shortfall,
            abs(
                observed.implementation_shortfall
                - float(str(expected["implementation_shortfall_pp"]))
            ),
        )
        worst_tracking = max(
            worst_tracking,
            abs(
                observed.tracking_difference_vs_combination
                - float(str(expected["tracking_difference_vs_combination_pp"]))
            ),
        )
        weights = expected["weights"]
        basis_used = expected["basis_used"]
        assert isinstance(weights, Sequence) and isinstance(basis_used, Sequence)
        if list(observed.basis) != [str(name) for name in basis_used]:
            worst_weight = float("inf")
        else:
            pairs = zip(observed.weights, weights, strict=True)
            worst_weight = max(
                worst_weight,
                max((abs(a - float(str(b))) for a, b in pairs), default=0.0),
            )
    reproduced = (
        not missing
        and not extra
        and not status_changes
        and not replication_presence_changes
        and worst_shortfall == 0.0
        and worst_tracking == 0.0
        and worst_weight == 0.0
    )
    return {
        "reproduced_to_zero_difference": reproduced,
        "source_run_id": payload["source_run_id"],
        "source_spec_hash": payload["source_spec_hash"],
        "funds_in_fixture": len(funds),
        "clause_c_figures_compared": compared,
        "funds_in_fixture_absent_here": missing,
        "funds_here_absent_from_fixture": extra,
        "largest_absolute_shortfall_difference_pp": worst_shortfall,
        "largest_absolute_tracking_difference_difference_pp": worst_tracking,
        "largest_absolute_weight_difference": worst_weight,
        "status_changes": status_changes,
        "replication_presence_changes": replication_presence_changes,
        "tolerance": 0.0,
        "interpretation": (
            "The control basis IS Experiment 009's basis, run by Experiment 009's "
            "own functions over the same bytes and the same months, with the "
            "bootstrap consumed in the same order so the intervals that decide an "
            "`unresolved` status are reproduced bit for bit. Anything other than "
            "zero here means something moved that this experiment did not vary, "
            "and every difference it reports would be uninterpretable."
        ),
    }


# --------------------------------------------------------------------------- #
# Scoring one basis
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class BasisScore:
    """What one basis does to clause (c) across the whole audited ex-US shelf."""

    declaration: BasisDeclaration
    replications: dict[str, ReplicationResult]
    outcomes: dict[str, ExUsOutcome]

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

    def reduced(self) -> dict[str, list[str]]:
        """Funds whose basis lost a column because a constituent did not cover them.

        This is Experiment 009's own rule and it is the difference between "the
        basis could not express it" and "the basis was not there". On this shelf
        it decides GWX.
        """
        out: dict[str, list[str]] = {}
        for ticker, item in sorted(self.replications.items()):
            expected = [name for name in self.declaration.tickers if name != ticker]
            lost = [name for name in expected if name not in item.basis]
            if lost:
                out[ticker] = lost
        return out

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
            "funds_with_no_replication": sorted(set(self.outcomes) - set(self.replications)),
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
            "funds_whose_basis_lost_a_column_to_coverage": self.reduced(),
            "columns_actually_available_per_fund": {
                ticker: len(item.basis) for ticker, item in sorted(self.replications.items())
            },
            "per_fund": {
                ticker: {
                    "region": self.outcomes[ticker].region,
                    "panel": self.outcomes[ticker].region,
                    "implementation_shortfall_pp": item.implementation_shortfall,
                    "tracking_difference_vs_combination_pp": (
                        item.tracking_difference_vs_combination
                    ),
                    "tracking_error_vs_combination_pp": item.tracking_error_vs_combination,
                    "fee_premium_over_basis_pp": item.fee_premium_over_basis,
                    "columns_available": len(item.basis),
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
    usable: Sequence[ScreenedExUsFund],
    windows: Mapping[str, FundWindow],
    series: Mapping[str, FundSeries],
    panels: Mapping[str, object],
    region_comparator: Mapping[str, str],
    facts: Mapping[str, ProductFacts],
    all_fits: Mapping[str, RegionalFits],
    half_fits: Mapping[tuple[str, str], ExposureFit],
    intervals: Mapping[str, Mapping[str, list[float]]],
    minimum_loading: float,
    materiality: float,
) -> BasisScore:
    replications: dict[str, ReplicationResult] = {}
    for fund in usable:
        region = fund.derived_region or ""
        result = _replicate(
            fund=fund,
            window=windows[fund.ticker],
            series=series,
            panel=panels[region],  # type: ignore[arg-type]
            basis=declaration.tickers,
            comparator=region_comparator[region],
            facts=facts,
        )
        if result is not None:
            replications[fund.ticker] = result
    outcomes = {
        fund.ticker: _verdict(
            fund=fund,
            window=windows[fund.ticker],
            fits=all_fits[fund.ticker],
            halves={
                era: fit for (ticker, era), fit in half_fits.items() if ticker == fund.ticker
            },
            interval=intervals.get(fund.ticker, {}),
            replication=replications.get(fund.ticker),
            minimum_loading=minimum_loading,
            materiality=materiality,
        )
        for fund in usable
    }
    return BasisScore(declaration=declaration, replications=replications, outcomes=outcomes)


# --------------------------------------------------------------------------- #
# The decomposition, which is the deliverable
# --------------------------------------------------------------------------- #


def _pairings(scores: Sequence[BasisScore]) -> dict[str, str]:
    """Which placebo is matched to which expressive basis, on column count.

    The pairing is a property of the declared bases and is derived rather than
    restated, so a placebo cannot drift away from the partner it bounds.
    """
    placebos = {
        len(score.declaration.tickers): score.declaration.id
        for score in scores
        if score.declaration.is_placebo
    }
    return {
        score.declaration.id: placebos[len(score.declaration.tickers)]
        for score in scores[1:]
        if not score.declaration.is_placebo and len(score.declaration.tickers) in placebos
    }


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
            "is_placebo": score.declaration.is_placebo,
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
            "clause_c_table": {
                ticker: {
                    "frozen_basis_pp": base_shortfall[ticker],
                    "this_basis_pp": shortfalls[ticker],
                    "attributable_to_the_basis_pp": differences[ticker],
                    "status_frozen": base_status[ticker],
                    "status_here": statuses[ticker],
                }
                for ticker in CLAUSE_C_TABLE
                if ticker in differences
            },
        }
    pairs = _pairings(scores)
    columns = {score.declaration.id: len(score.declaration.tickers) for score in scores}

    def _changed(name: str) -> int:
        return int(str(_mapping(per_basis[name], where=name)["verdicts_changed"]))

    matched: dict[str, JsonValue] = {
        expressive: {
            "expressive_basis": expressive,
            "placebo_basis": placebo,
            "columns": columns[expressive],
            "verdicts_changed_by_the_expressive_basis": _changed(expressive),
            "verdicts_changed_by_its_placebo": _changed(placebo),
            "expressive_movement_beyond_the_placebo": _changed(expressive) - _changed(placebo),
        }
        for expressive, placebo in pairs.items()
    }
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
            "matched_pairs": matched,
            "reading": (
                "Each placebo has exactly as many columns as its partner and not "
                "one new region-by-style cell. Whatever it moves is what column "
                "count alone moves in a look-ahead fit, and it is the floor under "
                "any claim that an expressive basis 'corrected' something. If a "
                "placebo moves as many verdicts as its partner, clause (c) is "
                "responding to the number of free parameters and tells us nothing "
                "about this shelf."
            ),
        },
    }


# --------------------------------------------------------------------------- #
# The coverage diagnostic, which is a second variable and never a verdict
# --------------------------------------------------------------------------- #


def _coverage_diagnostic(
    *,
    scores: Sequence[BasisScore],
    usable: Sequence[ScreenedExUsFund],
    windows: Mapping[str, FundWindow],
    series: Mapping[str, FundSeries],
    panels: Mapping[str, object],
    region_comparator: Mapping[str, str],
    facts: Mapping[str, ProductFacts],
    threshold: float,
) -> dict[str, JsonValue]:
    """What GWX's and RODM's clause (c) would be with the whole basis available.

    THIS MOVES TWO VARIABLES -- the basis and the window -- so it produces no
    status and decides nothing. It exists because GWX carries the largest
    intended loading in the entire ex-US audit at +0.856 and is rejected on cost
    alone, against a replication that consisted of ONE developed large-cap fund,
    and a reader is entitled to know whether that rejection is a property of the
    fund or of one month of filed history.
    """
    by_ticker = {fund.ticker: fund for fund in usable}
    rows: dict[str, JsonValue] = {}
    for ticker in COVERAGE_DIAGNOSTIC_FUNDS:
        fund = by_ticker.get(ticker)
        if fund is None:
            continue
        window = windows[ticker]
        trimmed_periods = tuple(
            period
            for period in window.periods
            if month_index(period) >= month_index(COVERAGE_DIAGNOSTIC_FIRST_MONTH)
        )
        trimmed = replace(window, periods=trimmed_periods)
        region = fund.derived_region or ""
        per_basis: dict[str, JsonValue] = {}
        for score in scores:
            frozen_result = score.replications.get(ticker)
            result = _replicate(
                fund=fund,
                window=trimmed,
                series=series,
                panel=panels[region],  # type: ignore[arg-type]
                basis=score.declaration.tickers,
                comparator=region_comparator[region],
                facts=facts,
            )
            if result is None:
                continue
            per_basis[score.declaration.id] = {
                "columns_on_the_full_window": (
                    None if frozen_result is None else len(frozen_result.basis)
                ),
                "columns_on_the_trimmed_window": len(result.basis),
                "shortfall_on_the_full_window_pp": (
                    None if frozen_result is None else frozen_result.implementation_shortfall
                ),
                "shortfall_on_the_trimmed_window_pp": result.implementation_shortfall,
                "clause_c_would_fire": result.implementation_shortfall > threshold,
                "weights": {
                    name: weight
                    for name, weight in zip(result.basis, result.weights, strict=True)
                    if weight > 1e-6
                },
            }
        rows[ticker] = {
            "months_on_the_full_window": window.months,
            "months_on_the_trimmed_window": len(trimmed_periods),
            "first_month_full": window.first,
            "first_month_trimmed": COVERAGE_DIAGNOSTIC_FIRST_MONTH,
            "by_basis": per_basis,
        }
    return {
        "what_this_is": (
            "A SECOND-VARIABLE DIAGNOSTIC. The window is trimmed by one month so "
            "that every declared basis constituent covers it, which changes the "
            "basis AND the sample. It produces no status and reverses no verdict. "
            "It answers one question: is the clause (c) rejection a property of "
            "the fund, or of the fact that its filed history begins one month "
            "before every constituent except VEA?"
        ),
        "trimmed_to": COVERAGE_DIAGNOSTIC_FIRST_MONTH,
        "clause_c_threshold_pp": threshold,
        "funds": rows,
    }


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_015_exus_replication_basis.yaml"


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Re-score Experiment 009's clause (c) under every declared basis."""
    frozen = exp_009_is_unmodified(specification)
    bases = declared_bases(specification)

    parameters = _mapping(specification.parameters, where="parameters")
    comparators = _comparators(specification)
    developed_comparator = str(
        _mapping(comparators["developed_ex_us_market"], where="comparators")["ticker"]
    )
    emerging_comparator = str(
        _mapping(comparators["emerging_market"], where="comparators")["ticker"]
    )
    us_comparator = str(_mapping(comparators["us_pedestal"], where="comparators")["ticker"])
    region_comparator = {
        "developed_ex_us": developed_comparator,
        "emerging": emerging_comparator,
    }

    minimum_loading = float(str(parameters["minimum_intended_loading"]))
    materiality = float(str(parameters["materiality_threshold_annual_percent"]))
    clause_c_threshold = float(str(parameters["clause_c_threshold_annual_percent"]))
    hac_lags = int(str(parameters["hac_lags"]))
    minimum_months = int(str(parameters["minimum_monthly_observations"]))
    power = float(str(parameters["power_target"]))

    exp_009 = load_specification(
        workspace_root() / "experiments" / "exp_009_exus_factor_products.yaml"
    )
    dispersion = float(
        str(
            _mapping(
                _mapping(exp_009.parameters, where="exp_009.parameters")["alpha_shrinkage"],
                where="alpha_shrinkage",
            )["sigma_true_annual_percent"]
        )
    )

    universe = load_universe()
    facts = load_product_facts()
    extras = load_extra_facts()
    cache = RawCache()

    eras = _era_windows(specification)
    window_start, window_end = eras["common_period"]

    panels = {
        region: load_regional_panel(cache, region=region, start=window_start, end=window_end)
        for region in (*GRADED_REGIONS, "us")
    }

    basis_tickers = sorted({ticker for basis in bases for ticker in basis.tickers})
    wanted: dict[str, tuple[str, str]] = {
        fund.ticker: (fund.series_id, fund.class_id) for fund in universe.passing
    }
    for ticker in (developed_comparator, emerging_comparator, us_comparator, *basis_tickers):
        if ticker not in wanted:
            series_id, class_id, _name = resolve_ticker(cache, ticker)
            wanted[ticker] = (series_id, class_id)
    series, fetch_failures = _fetch_all(
        cache, tickers=wanted, start=window_start, end=window_end
    )
    coverage_check = _assert_declared_coverage(specification, series)

    gates = [
        _validate_regional_path(
            ticker=developed_comparator,
            region="developed_ex_us",
            series=series,
            panel=panels["developed_ex_us"],
            minimum_correlation=0.97,
            beta_tolerance=0.10,
            minimum_r_squared=0.93,
        ),
        _validate_regional_path(
            ticker=emerging_comparator,
            region="emerging",
            series=series,
            panel=panels["emerging"],
            minimum_correlation=0.95,
            beta_tolerance=0.10,
            minimum_r_squared=0.93,
        ),
        _validate_regional_path(
            ticker=us_comparator,
            region="us",
            series=series,
            panel=panels["us"],
            minimum_correlation=0.99,
            beta_tolerance=0.05,
            minimum_r_squared=0.98,
        ),
    ]

    windows: dict[str, FundWindow] = {}
    usable: list[ScreenedExUsFund] = []
    coverage: list[dict[str, JsonValue]] = []
    for fund in universe.passing:
        record = series.get(fund.ticker)
        region = fund.derived_region or ""
        if record is None or region not in panels:
            coverage.append(
                {
                    "ticker": fund.ticker,
                    "usable": False,
                    "reason": "no filings retrieved" if record is None else "no panel",
                }
            )
            continue
        inception = None if fund.facts is None else fund.facts.inception_date
        window = _window_for(
            record,
            panels[region],
            region=region,
            start=window_start,
            end=window_end,
            inception=inception,
        )
        windows[fund.ticker] = window
        coverage.append(
            {
                "ticker": fund.ticker,
                "region": region,
                "panel": region,
                "usable": window.months >= minimum_months,
                "months_usable": window.months,
                "first_month": window.first,
                "last_month": window.last,
                "converted_from_mutual_fund": (
                    extras[fund.ticker].converted_from_mutual_fund
                    if fund.ticker in extras
                    else None
                ),
                "used_in_a_basis": fund.ticker in basis_tickers,
            }
        )
        if window.months >= minimum_months:
            usable.append(fund)

    # Exposures, halves, intervals and pedestals are BASIS-INVARIANT: the basis
    # enters nowhere except clauses (c) and (d). They are computed once and
    # reused across every basis, which is not an optimisation but the claim
    # itself -- if they were recomputed per basis they could differ, and the
    # experiment would no longer be varying one thing. Every fit is on the fund's
    # OWN region's panel, and the wrong-panel and US-panel fits are reproduced
    # beside them because an ex-US loading without its panel named is not a
    # number.
    all_fits: dict[str, RegionalFits] = {}
    half_fits: dict[tuple[str, str], ExposureFit] = {}
    flat_fits: list[ExposureFit] = []
    for fund in usable:
        region = fund.derived_region or ""
        window = windows[fund.ticker]
        record = series[fund.ticker]
        own = _fit_all_specifications(
            ticker=fund.ticker,
            era="common_period",
            series=record,
            panel=panels[region],
            periods=window.periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        flat_fits.extend(own.values())
        wrong = _fit_on(
            record,
            panels[_OPPOSITE_REGION[region]],
            window.periods,
            ticker=fund.ticker,
            era=f"wrong_panel_{_OPPOSITE_REGION[region]}",
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        on_us = _fit_on(
            record,
            panels["us"],
            window.periods,
            ticker=fund.ticker,
            era="us_panel",
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        all_fits[fund.ticker] = RegionalFits(own_panel=own, wrong_panel=wrong, us_panel=on_us)
        for era_name in ("first_half", "second_half"):
            era_periods = _slice_era(window.periods, eras[era_name])
            if len(era_periods) <= 12:
                continue
            fit = _fit_on(
                record,
                panels[region],
                era_periods,
                ticker=fund.ticker,
                era=era_name,
                hac_lags=hac_lags,
                dispersion=dispersion,
                power=power,
            )
            if fit is not None:
                half_fits[(fund.ticker, era_name)] = fit

    # The bootstrap is consumed in EXACTLY Experiment 009's order over exactly
    # its fund list, so the interval that decides an `unresolved` status is
    # reproduced bit for bit rather than approximately.
    intervals: dict[str, dict[str, list[float]]] = {}
    for fund in usable:
        if fund.intended_factor is None:
            continue
        intervals[fund.ticker] = _bootstrap_interval(
            series=series[fund.ticker],
            panel=panels[fund.derived_region or ""],
            periods=windows[fund.ticker].periods,
            factor=fund.intended_factor,
            rng=context.rng,
            resamples=specification.inference.resamples,
            confidence=specification.inference.confidence_level,
        )

    pedestals = {
        region: _pedestal(
            ticker=ticker,
            region=region,
            series=series,
            panel=panels[region],
            periods=panels[region].periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
            facts=facts,
        )
        for region, ticker in (
            ("developed_ex_us", developed_comparator),
            ("emerging", emerging_comparator),
            ("us", us_comparator),
        )
    }

    scores = [
        _score_basis(
            declaration,
            usable=usable,
            windows=windows,
            series=series,
            panels=panels,
            region_comparator=region_comparator,
            facts=facts,
            all_fits=all_fits,
            half_fits=half_fits,
            intervals=intervals,
            minimum_loading=minimum_loading,
            materiality=materiality,
        )
        for declaration in bases
    ]

    control = scores[0]
    reproduction = reproduction_differences(control.replications, control.outcomes)
    if not reproduction["reproduced_to_zero_difference"]:
        raise ExUsBasisVariationError(
            "the control basis did not reproduce Experiment 009 to zero "
            f"difference: {json.dumps(plain_json(reproduction))}. Something other "
            "than the basis moved, so no difference this experiment reports is "
            "interpretable. Abandon the run and find what moved."
        )

    decomposition = _decomposition(scores)
    by_basis = _mapping(decomposition["by_basis"], where="by_basis")
    matched = _mapping(
        _mapping(decomposition["placebo_control"], where="placebo_control")["matched_pairs"],
        where="matched_pairs",
    )

    diagnostic = _coverage_diagnostic(
        scores=scores,
        usable=usable,
        windows=windows,
        series=series,
        panels=panels,
        region_comparator=region_comparator,
        facts=facts,
        threshold=clause_c_threshold,
    )

    # Which clause decides each emerging product, and whether a basis could ever
    # move it. Clauses (a) and (b) read the LOADING and are basis-invariant, so a
    # product rejected on (a) cannot be rescued by any comparator whatsoever.
    emerging: dict[str, JsonValue] = {
        ticker: {
            "region": control.outcomes[ticker].region,
            "panel": control.outcomes[ticker].region,
            "months": control.outcomes[ticker].months,
            "intended_factor": control.outcomes[ticker].intended_factor,
            "intended_loading_on_its_own_panel": control.outcomes[ticker].intended_loading,
            "intended_loading_on_the_us_panel": (
                control.outcomes[ticker].intended_loading_us_panel
            ),
            "alpha_annual_percent": control.outcomes[ticker].alpha_annual_percent,
            "alpha_mde_80pc_power_percent": control.outcomes[ticker].alpha_mde_percent,
            "status_by_basis": {
                score.declaration.id: score.statuses()[ticker] for score in scores
            },
            "shortfall_by_basis_pp": {
                score.declaration.id: score.shortfalls().get(ticker) for score in scores
            },
            "clauses_fired_under_the_frozen_basis": list(
                control.outcomes[ticker].clauses_fired
            ),
            "decided_by_a_basis_invariant_clause": any(
                clause.startswith(("(a)", "(b)"))
                for clause in control.outcomes[ticker].clauses_fired
            ),
        }
        for ticker in EMERGING_PRODUCTS
        if ticker in control.outcomes
    }

    incumbents = sorted(
        ticker for ticker, status in control.statuses().items() if status == "exploratory"
    )
    incumbent_survival = {
        ticker: {
            score.declaration.id: score.statuses()[ticker] for score in scores
        }
        for ticker in incumbents
    }
    lost_status = sorted(
        ticker
        for ticker in incumbents
        if any(score.statuses()[ticker] != "exploratory" for score in scores[1:])
    )

    placebo_ids = [score.declaration.id for score in scores if score.declaration.is_placebo]
    expressive_ids = [
        score.declaration.id
        for score in scores[1:]
        if not score.declaration.is_placebo
    ]
    expressive_moves = [
        int(str(_mapping(by_basis[name], where=name)["verdicts_changed"]))
        for name in expressive_ids
    ]
    placebo_moves = [
        int(str(_mapping(by_basis[name], where=name)["verdicts_changed"]))
        for name in placebo_ids
    ]
    gwx = {
        score.declaration.id: score.shortfalls().get("GWX", float("nan")) for score in scores
    }

    summary = (
        f"Experiment 009's clause (c) re-scored under {len(scores)} replicating "
        f"bases over the same {len(usable)} ex-US funds, the same windows, the same "
        "regional panels and the same falsifier, varying only the basis. The "
        "control basis reproduced Experiment 009 to zero difference in every "
        "shortfall, weight and status. Across the shelf the expressive bases "
        f"change {expressive_moves} verdicts and their column-count-matched "
        f"placebos -- no new region-by-style cell -- change {placebo_moves}. "
        f"GWX's implementation shortfall moves from {gwx[CONTROL_BASIS_ID]:+.2f} "
        f"pp/yr on the frozen basis to "
        f"{gwx.get('D_expressive_ex_us', float('nan')):+.2f} on the maximally "
        "expressive ex-US basis; under the frozen basis its replication was VEA "
        "ALONE, a developed large-cap fund standing in for a developed small-cap "
        f"fund. Of the {len(incumbents)} products at `exploratory`, "
        f"{len(lost_status)} lose that status under some basis. No emerging "
        "product reaches `exploratory` under any basis, and that is not a basis "
        "question: every emerging verdict is decided by clause (a) or by an "
        "interval, both of which read the loading and are basis-invariant. Every "
        "basis is fitted in sample, so a richer one is a HARDER test of the "
        "product. Nothing is promoted."
    )

    diagnostics: dict[str, JsonValue] = {
        "relationship_to_experiment_009": {
            "what_changed": (
                "The replicating basis, and nothing else. Experiment 009's "
                "specification, committed universe and committed product facts "
                "were asserted by sha256 before anything was fetched, and its "
                "published clause (c) column and every status are reproduced to "
                "zero difference by the control basis."
            ),
            "frozen_inputs_asserted": dict(frozen),
            "basis_invariant_quantities": [
                "every FF5+UMD loading on the fund's own regional panel and its standard error",
                "every wrong-panel and US-panel loading",
                "every raw and shrunk alpha and its MDE at 80% power",
                "every bootstrap interval on the intended loading",
                "every regional model-misfit pedestal",
                "clause (a) and clause (b), which do not read the basis",
            ],
            "alpha_family": (
                f"Experiment 009's fund-by-specification alpha tests, reproduced "
                f"here as {len(flat_fits)} fits and NOT re-corrected. Re-running an "
                "identical test under a different comparator does not create a new "
                "hypothesis about alpha, and reporting a second correction over the "
                "same p-values would double-count the search."
            ),
            "reproduction_of_the_control_basis": reproduction,
        },
        "bases_declared": [basis.to_json() for basis in bases],
        "basis_scores": {score.declaration.id: score.to_json() for score in scores},
        "decomposition": decomposition,
        "placebo_beside_expressive": dict(matched),
        "coverage_diagnostic": diagnostic,
        "declared_coverage_check": coverage_check,
        "emerging_products": {
            "funds": emerging,
            "reading": (
                "Clause (a) is a test on the intended LOADING and clause (b) on its "
                "sign across the fixed halves. Neither reads the basis, so an "
                "emerging product rejected on (a), or left `unresolved` because its "
                "interval contains 0.15, CANNOT be moved to `exploratory` by any "
                "comparator. That is a different problem from the basis and it is a "
                "different problem again from the short windows AVES and DFEV have. "
                "The three must not be conflated."
            ),
        },
        "incumbent_survival": {
            "products_at_exploratory_under_the_frozen_basis": incumbents,
            "status_by_basis": incumbent_survival,
            "products_losing_exploratory_under_some_basis": lost_status,
            "reading": (
                "A richer basis is a HARDER test. Whether the incumbents survive it "
                "matters more than whether any rejection is reversed."
            ),
        },
        "regional_model_misfit_pedestals": pedestals,
        "panel_discipline": {
            "rule": (
                "Every loading here is estimated on the fund's OWN region's French "
                "panel and is reported with that panel named. Experiment 009 "
                "measured that grading these funds on the US panel instead would "
                "put 16 of 25 below the 0.15 bar rather than 5, moving individual "
                "loadings by up to 0.480."
            ),
            "panels_used": dict.fromkeys(GRADED_REGIONS, "own region")
            | {"us": "the VTI pedestal only"},
        },
        "coverage": coverage,
        "fetch_failures": fetch_failures,
        "validation_gates": gates,
        "factor_provenance": {
            region: dict(panel.provenance) for region, panel in panels.items()
        },
        "universe": {
            "committed_file": str(universe_path().relative_to(workspace_root())),
            "sha256": _sha256_file(universe_path()),
            "product_facts_sha256": _sha256_file(product_facts_path()),
            "inherited_from": "exp_009_exus_factor_products",
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
                "Weights fitted on a PRIOR window, which these windows -- 44 to 78 "
                "months -- cannot support without shortening the estimation window "
                "further. That remains the open question Experiments 013 and 014 "
                "named, and this experiment does not answer it."
            ),
        },
        "unobservable": {
            "out_of_sample_replication": (
                "NOT COMPUTED. Every basis here is fitted on the same months it is "
                "scored on."
            ),
            "foreign_withholding_tax": (
                "NOT SEPARABLE, exactly as in Experiment 009. Every basis "
                "constituent is a US-domiciled 1940-Act fund paying the same treaty "
                "rates as the product, so a difference between them cannot be "
                "foreign tax -- but the level is inside every return here and no "
                "basis change touches it."
            ),
            "realised_taxable_distributions": (
                "NOT AVAILABLE from Form N-PORT, so clause (d) is evaluated without "
                "the distribution term the falsifier names, under every basis alike."
            ),
        },
    }

    estimates: list[Estimate] = []
    for ticker in CLAUSE_C_TABLE:
        if ticker not in control.replications:
            continue
        fit = all_fits[ticker].own_panel[PRIMARY_SPECIFICATION]
        frozen_value = control.shortfalls()[ticker]
        region = control.outcomes[ticker].region
        for score in scores[1:]:
            if ticker not in score.replications:
                continue
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
                        "this construction identifies. The column-count-matched "
                        "placebo bases bound it instead."
                    ),
                    cost_basis=CostBasis.NET_OPTIMISTIC,
                    n_obs=fit.n_observations,
                    notes=(
                        f"panel {region}; frozen basis {frozen_value:+.2f} pp/yr, "
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
        "SPAN IS NOT COVERAGE. Experiment 009 drops a basis constituent that does "
        "not cover a fund's months, so a fund whose filed history starts earlier "
        "than the basis sees fewer columns. GWX and RODM file from 2019-07 and "
        "were replicated by VEA ALONE under the frozen basis. The columns each "
        "fund actually saw are reported per basis, and the trimmed-window "
        "diagnostic moves TWO variables and decides nothing.",
        "EVERY LOADING NAMES ITS PANEL. Grading these funds on the US panel rather "
        "than their own would put 16 of 25 below the 0.15 bar rather than 5.",
        "ALPHA IS UNMEASURABLE HERE. The median ex-US MDE at 80% power is 3.23 "
        "pp/yr and alpha is not a criterion in either direction.",
        "Clauses (a) and (b) read the LOADING and are basis-invariant, so no "
        "comparator can move a product that fails them. That is why no emerging "
        "product can reach `exploratory` by a change of basis, and it must not be "
        "conflated with the separate fact that AVES and DFEV have short windows.",
        "The set of funds excluded from their own basis GROWS with the basis, and "
        "for those funds the shortfall is the realised style return of 2019-2025 "
        "rather than an implementation cost. A status change on such a fund is a "
        "change in what is being measured.",
        "The placebo bases add columns without adding a region-by-style cell. Each "
        "is matched on column count to one expressive basis and must be read "
        "BESIDE it rather than after it.",
        "EWX at 0.65% is above the 0.60% expense cap this audit applies to graded "
        "products. It is admitted as a building block because it is the only "
        "emerging small-cap fund with a usable window, and the consequence -- a "
        "dearer basis lowers the fee premium and pushes shortfalls slightly "
        "negative -- is reported separately from the tracking-difference term.",
        "No new alpha test is performed and no alpha is re-corrected. Every alpha, "
        "MDE, loading and interval is Experiment 009's, reproduced.",
        "Item B.5 returns remain fund-reported, unaudited and uncorroborated by any "
        "independent source, in every basis alike.",
        "Every figure is PRETAX, and foreign withholding is inside every return "
        "here and is not separable by any construction in this experiment.",
    ]

    difference_rows: list[dict[str, object]] = []
    for ticker in sorted(control.outcomes):
        row: dict[str, object] = {
            "ticker": ticker,
            "region_panel": control.outcomes[ticker].region,
            "months": control.outcomes[ticker].months,
            "intended_loading": control.outcomes[ticker].intended_loading,
            "alpha_mde_80pc_power_percent": control.outcomes[ticker].alpha_mde_percent,
            "status_frozen_basis": control.statuses()[ticker],
        }
        for score in scores:
            row[f"shortfall_{score.declaration.id}"] = score.shortfalls().get(ticker)
            row[f"status_{score.declaration.id}"] = score.statuses()[ticker]
            if score.declaration.id != CONTROL_BASIS_ID:
                control_value = control.shortfalls().get(ticker)
                basis_value = score.shortfalls().get(ticker)
                row[f"difference_{score.declaration.id}"] = (
                    None
                    if control_value is None or basis_value is None
                    else basis_value - control_value
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


def _show(value: float | None, width: int, places: int, *, signed: bool = False) -> str:
    if value is None or not math.isfinite(value):
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
    by_basis = _mapping(decomposition["by_basis"], where="by_basis")
    lines: list[str] = [result.summary, ""]

    reproduction = _mapping(
        _mapping(diagnostics["relationship_to_experiment_009"], where="rel")[
            "reproduction_of_the_control_basis"
        ],
        where="reproduction",
    )
    lines.append(
        f"control reproduces Experiment 009: "
        f"{reproduction['reproduced_to_zero_difference']} over "
        f"{reproduction['funds_in_fixture']} funds "
        f"({reproduction['clause_c_figures_compared']} with a replication), largest "
        f"shortfall difference {reproduction['largest_absolute_shortfall_difference_pp']}"
    )
    lines.append("")
    lines.append(
        f"{'basis':30s} {'cols':>4s} {'cells':>5s} {'expl':>5s} {'rej':>5s} "
        f"{'unres':>6s} {'(c)':>4s} {'(d)':>4s} {'med sf':>8s} {'changed':>8s}"
    )
    for name, block in scores.items():
        assert isinstance(block, Mapping)
        basis = _mapping(block["basis"], where="basis")
        counts = _mapping(block["status_counts"], where="counts")
        changed = "-"
        if name in by_basis:
            changed = str(_mapping(by_basis[name], where=name)["verdicts_changed"])
        cells = basis["distinct_cells"]
        assert isinstance(cells, Sequence)
        lines.append(
            f"{name:30s} {basis['columns']:>4} {len(cells):>5} "
            f"{counts['exploratory']:>5} {counts['rejected']:>5} "
            f"{counts['unresolved']:>6} {block['clause_c_fired']:>4} "
            f"{block['clause_d_fired']:>4} "
            f"{_show(float(str(block['median_implementation_shortfall_pp'])), 8, 2, signed=True)} "
            f"{changed:>8s}"
        )

    lines.append("")
    lines.append("placebo beside expressive, matched on column count")
    matched = _mapping(diagnostics["placebo_beside_expressive"], where="matched")
    for name, block in matched.items():
        pair = _mapping(block, where=name)
        lines.append(
            f"  {name:30s} {pair['columns']:>3} cols  expressive moved "
            f"{pair['verdicts_changed_by_the_expressive_basis']}, placebo "
            f"{pair['placebo_basis']} moved {pair['verdicts_changed_by_its_placebo']}"
        )

    lines.append("")
    lines.append("clause (c) table: shortfall by basis, pp/yr")
    ids = list(scores)
    lines.append(f"{'ticker':8s}" + "".join(f"{name[:12]:>14s}" for name in ids))
    control_block = _mapping(scores[CONTROL_BASIS_ID], where="control")
    control_funds = _mapping(control_block["per_fund"], where="per_fund")
    for ticker in CLAUSE_C_TABLE:
        if ticker not in control_funds:
            continue
        row = f"{ticker:8s}"
        for name in ids:
            block = _mapping(scores[name], where=name)
            funds = _mapping(block["per_fund"], where="per_fund")
            value = (
                float(str(_mapping(funds[ticker], where=ticker)["implementation_shortfall_pp"]))
                if ticker in funds
                else None
            )
            row += _show(value, 14, 2, signed=True)
        lines.append(row)

    lines.append("")
    lines.append("verdict changes, by basis")
    for name in by_basis:
        block = _mapping(by_basis[name], where=name)
        changes = block["verdict_changes"]
        assert isinstance(changes, Sequence)
        label = "placebo " if block["is_placebo"] else ""
        lines.append(f"  {label}{name}: {list(changes) or 'none'}")

    lines.append("")
    lines.append("coverage diagnostic (second variable; decides nothing)")
    diagnostic = _mapping(diagnostics["coverage_diagnostic"], where="diagnostic")
    funds_block = _mapping(diagnostic["funds"], where="funds")
    for ticker, block in funds_block.items():
        row_block = _mapping(block, where=ticker)
        per_basis = _mapping(row_block["by_basis"], where="by_basis")
        lines.append(
            f"  {ticker}: {row_block['months_on_the_full_window']} months -> "
            f"{row_block['months_on_the_trimmed_window']}"
        )
        for name, entry in per_basis.items():
            item = _mapping(entry, where=name)
            lines.append(
                f"    {name:30s} cols {item['columns_on_the_full_window']} -> "
                f"{item['columns_on_the_trimmed_window']}  shortfall "
                f"{_show(item['shortfall_on_the_full_window_pp'], 7, 2, signed=True)} -> "  # type: ignore[arg-type]
                f"{_show(item['shortfall_on_the_trimmed_window_pp'], 7, 2, signed=True)}  "  # type: ignore[arg-type]
                f"(c) would fire: {item['clause_c_would_fire']}"
            )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 015 through the runner and the ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_015_exus_replication_basis",
        description=(
            "Re-score Experiment 009's clause (c) under every declared replicating "
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
                "exp_015_exus_replication_basis"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
