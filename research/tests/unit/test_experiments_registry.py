"""Resolution failures are errors, never silent no-ops."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.experiments import registry as registry_module
from portfolio_edge.experiments.registry import (
    DuplicateRegistrationError,
    ExperimentRegistry,
    RegistryError,
    RunContext,
    UnknownExperimentError,
)
from portfolio_edge.experiments.result import ExperimentResult, ResultStatus
from portfolio_edge.experiments.specification import Specification
from tests.unit.test_experiments_support import build_spec, sample_result


def _experiment(_spec: Specification, _context: RunContext) -> ExperimentResult:
    return sample_result(ResultStatus.EXPLORATORY)


def test_decorator_registers_and_returns_the_function() -> None:
    registry = ExperimentRegistry()

    @registry.register("exp_test_family")
    def experiment(spec: Specification, context: RunContext) -> ExperimentResult:
        return sample_result()

    assert registry.resolve("exp_test_family") is experiment
    assert registry.names() == ("exp_test_family",)
    assert "exp_test_family" in registry
    assert len(registry) == 1
    assert list(registry) == ["exp_test_family"]


def test_resolving_an_unregistered_name_raises_and_lists_what_is_known() -> None:
    registry = ExperimentRegistry()
    registry.add("known", _experiment)
    with pytest.raises(UnknownExperimentError) as caught:
        registry.resolve("unknown")
    assert "unknown" in str(caught.value)
    assert "known" in str(caught.value)


def test_empty_registry_says_so() -> None:
    with pytest.raises(UnknownExperimentError, match="none registered"):
        ExperimentRegistry().resolve("anything")


def test_duplicate_registration_is_refused() -> None:
    registry = ExperimentRegistry()
    registry.add("dupe", _experiment)
    with pytest.raises(DuplicateRegistrationError, match="already registered"):
        registry.add("dupe", _experiment)


def test_empty_name_is_refused() -> None:
    with pytest.raises(RegistryError, match="non-empty name"):
        ExperimentRegistry().add("  ", _experiment)


def test_there_is_no_module_level_registry() -> None:
    """A process-wide registry would make what executes depend on import order."""
    globals_of_module = vars(registry_module)
    assert not [
        name
        for name, value in globals_of_module.items()
        if isinstance(value, ExperimentRegistry)
    ]


def test_registry_can_be_seeded_from_a_mapping_without_sharing_state() -> None:
    first = ExperimentRegistry({"a": _experiment})
    second = ExperimentRegistry(dict.fromkeys(["a"], _experiment))
    second.add("b", _experiment)
    assert first.names() == ("a",)
    assert second.names() == ("a", "b")


def test_run_context_carries_only_identity_and_a_seeded_generator(tmp_path: Path) -> None:
    spec = build_spec()
    context = RunContext(
        run_id="r",
        seed=7,
        rng=np.random.default_rng(7),
        artifact_dir=tmp_path,
    )
    assert context.rng.random() == np.random.default_rng(7).random()
    assert spec.seed == 7
