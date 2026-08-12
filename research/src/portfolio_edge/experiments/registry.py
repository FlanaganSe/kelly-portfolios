"""Name to experiment-callable resolution.

There is deliberately **no module-level default registry**. A process-wide
mutable dictionary is exactly the kind of hidden state that makes a run
irreproducible: what executed would then depend on which modules happened to be
imported. Construct a registry, register into it, and hand it to the runner.

The registry is also the only coupling point between this governance layer and
the code that computes anything. The runner never imports an experiment module;
it resolves ``specification.entry_point`` against the registry it was given.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import numpy as np

from portfolio_edge.experiments.result import ExperimentResult
from portfolio_edge.experiments.specification import Specification


class RegistryError(Exception):
    """Base class for registration and resolution failures."""


class UnknownExperimentError(RegistryError, LookupError):
    """A specification named an entry point that is not registered."""


class DuplicateRegistrationError(RegistryError):
    """Two callables claimed the same name."""


@dataclass(frozen=True, slots=True, kw_only=True)
class RunContext:
    """Everything an experiment callable may know beyond its specification.

    It carries identity and a seeded generator, nothing else. Parameters live in
    the specification so that they are hashed and ledgered; anything smuggled
    through here would escape both. The generator is passed explicitly rather
    than seeded globally so that two runs in one process cannot draw from each
    other's stream.
    """

    run_id: str
    seed: int
    """The seed actually used. Recorded in the ledger even when the spec left it null."""
    rng: np.random.Generator
    artifact_dir: Path


ExperimentFunction: TypeAlias = Callable[  # noqa: UP040 - kept consistent with specification.py
    [Specification, RunContext], ExperimentResult
]


class ExperimentRegistry:
    """A name -> callable mapping with no silent behaviour."""

    __slots__ = ("_entries",)

    def __init__(self, entries: Mapping[str, ExperimentFunction] | None = None) -> None:
        self._entries: dict[str, ExperimentFunction] = dict(entries or {})

    def register(self, name: str) -> Callable[[ExperimentFunction], ExperimentFunction]:
        """Decorator form: ``@registry.register("exp_001_factor_decay")``."""

        def decorate(function: ExperimentFunction) -> ExperimentFunction:
            self.add(name, function)
            return function

        return decorate

    def add(self, name: str, function: ExperimentFunction) -> None:
        if not name or not name.strip():
            raise RegistryError("an experiment entry point needs a non-empty name")
        if name in self._entries:
            raise DuplicateRegistrationError(
                f"experiment {name!r} is already registered to "
                f"{getattr(self._entries[name], '__qualname__', self._entries[name])!r}. "
                "Registering twice would make the executed code depend on import order."
            )
        self._entries[name] = function

    def resolve(self, name: str) -> ExperimentFunction:
        """Return the callable registered under ``name`` or raise."""
        try:
            return self._entries[name]
        except KeyError as exc:
            known = ", ".join(sorted(self._entries)) or "<none registered>"
            raise UnknownExperimentError(
                f"no experiment registered as {name!r}. Registered: {known}"
            ) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def __contains__(self, name: object) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self._entries))
