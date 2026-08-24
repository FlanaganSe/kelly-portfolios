"""Frozen, machine-readable experiment specifications.

A specification is committed *before* its result is examined. It is the unit that
the ledger counts, so it must be canonically serialisable and hashable: two
logically identical specifications hash identically regardless of YAML key order,
quoting, or comments, and any change to any load-bearing field changes the hash.

Every field on :class:`Specification` is load-bearing and enters the hash. Prose
fields are included deliberately -- changing a falsifier changes the experiment.
The only excluded field is ``source_path``, which records where the file was read
from and is not part of the specification's identity.

Types are load-bearing too. ``0.5`` and ``"0.5"`` are different specifications and
hash differently. YAML dates are normalised to ISO-8601 strings so that
``1963-07-01`` and ``"1963-07-01"`` agree.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Final, TypeAlias

import yaml

SPEC_SCHEMA_VERSION: Final = 1
"""Bumped only when the canonical form changes. It is part of every hash."""

JsonValue: TypeAlias = (  # noqa: UP040 - a PEP 695 alias here is not yet checkable by mypy
    "str | int | float | bool | Sequence[JsonValue] | Mapping[str, JsonValue] | None"
)


class SpecificationError(ValueError):
    """A specification is malformed, incomplete, or internally inconsistent."""


class ConfirmatoryGateError(SpecificationError):
    """A confirmatory run was attempted without the fields that make it confirmatory."""


class RunKind(StrEnum):
    """Whether a run searches (``exploratory``) or decides (``confirmatory``)."""

    EXPLORATORY = "exploratory"
    CONFIRMATORY = "confirmatory"


class EvidenceClass(StrEnum):
    """What kind of evidence a run can produce, at most.

    This is a claim about provenance, not about quality. Evaluating a vendor's
    published series is never an independent replication, however careful the
    evaluation is, so the distinction is recorded in the frozen specification
    rather than negotiated when the result is written up.
    """

    INDEPENDENT_REPLICATION = "independent-replication"
    SOURCE_REPRODUCTION = "source-reproduction"
    VENDOR_SERIES_EVALUATION = "vendor-series-evaluation"
    PUBLIC_SERIES_EVALUATION = "public-series-evaluation"
    FUND_IMPLEMENTATION_AUDIT = "fund-implementation-audit"
    POLICY_SIMULATION = "policy-simulation"


# --------------------------------------------------------------------------- #
# JSON normalisation
# --------------------------------------------------------------------------- #


def freeze_json(value: object, *, path: str = "$") -> JsonValue:
    """Deep-freeze a parsed YAML value into immutable, JSON-safe data.

    Mappings become :class:`~types.MappingProxyType`, sequences become tuples,
    dates become ISO-8601 strings. Anything else is an error, loudly, with the
    path at which it was found.
    """
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise SpecificationError(f"non-finite number at {path}: {value!r}")
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        frozen: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise SpecificationError(
                    f"mapping key at {path} must be a string, got {type(key).__name__}: {key!r}"
                )
            frozen[key] = freeze_json(item, path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return tuple(freeze_json(item, path=f"{path}[{i}]") for i, item in enumerate(value))
    raise SpecificationError(
        f"unsupported value type at {path}: {type(value).__name__}. "
        "Specifications hold only strings, numbers, booleans, null, lists and mappings."
    )


def _canonical(obj: object) -> JsonValue:
    """Convert to plain, JSON-serialisable data with no residual object identity."""
    if isinstance(obj, StrEnum):
        return obj.value
    if obj is None or isinstance(obj, bool | int | float | str):
        return obj
    if is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _canonical(getattr(obj, f.name))
            for f in fields(obj)
            if f.metadata.get("hashed", True)
        }
    if isinstance(obj, Mapping):
        return {str(key): _canonical(item) for key, item in obj.items()}
    if isinstance(obj, Sequence) and not isinstance(obj, str | bytes):
        return [_canonical(item) for item in obj]
    raise SpecificationError(f"cannot canonicalise {type(obj).__name__}: {obj!r}")


def plain_json(value: object) -> JsonValue:
    """Convert frozen specification data back to plain dicts and lists.

    Frozen values are ``MappingProxyType`` and tuples, which ``json`` cannot
    encode. Anything written out of this layer passes through here.
    """
    return _canonical(value)


def canonical_json(obj: object) -> str:
    """Order-independent JSON text: sorted keys, no insignificant whitespace."""
    return json.dumps(
        _canonical(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_present(value: object) -> bool:
    """Whether a field counts as frozen for the confirmatory gate.

    Empty strings, empty containers, whitespace and ``None`` are absent. A
    specification that names a benchmark ``""`` has not frozen a benchmark.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return len(value) > 0
    if isinstance(value, Sequence) and not isinstance(value, bytes):
        return len(value) > 0
    return True


# --------------------------------------------------------------------------- #
# Nested structures
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Era:
    """A frozen sample window with the reason it was chosen.

    ``rationale`` is required so that eras cannot be quietly moved to where the
    result looks better; the reason is committed with the boundary.
    """

    name: str
    start: str
    end: str
    rationale: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, JsonValue], *, path: str) -> Era:
        _reject_unknown(data, {"name", "start", "end", "rationale"}, path=path)
        return cls(
            name=_require_str(data, "name", path=path),
            start=_require_str(data, "start", path=path),
            end=_require_str(data, "end", path=path),
            rationale=_require_str(data, "rationale", path=path),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class SamplePolicy:
    """Sample boundaries, era definitions, and what is deliberately not looked at."""

    start: str
    end: str
    eras: tuple[Era, ...]
    held_out: str
    """What is withheld, and the condition under which it may be consumed."""
    embargo: str = ""
    """Gap imposed between training and evaluation windows; '' means none declared."""

    @classmethod
    def from_mapping(cls, data: Mapping[str, JsonValue], *, path: str) -> SamplePolicy:
        _reject_unknown(data, {"start", "end", "eras", "held_out", "embargo"}, path=path)
        raw_eras = data.get("eras", ())
        if not isinstance(raw_eras, Sequence) or isinstance(raw_eras, str):
            raise SpecificationError(f"{path}.eras must be a list of era mappings")
        eras: list[Era] = []
        for index, item in enumerate(raw_eras):
            if not isinstance(item, Mapping):
                raise SpecificationError(f"{path}.eras[{index}] must be a mapping")
            eras.append(Era.from_mapping(item, path=f"{path}.eras[{index}]"))
        names = [era.name for era in eras]
        if len(set(names)) != len(names):
            raise SpecificationError(f"{path}.eras contains duplicate era names: {names}")
        return cls(
            start=_require_str(data, "start", path=path),
            end=_require_str(data, "end", path=path),
            eras=tuple(eras),
            held_out=_require_str(data, "held_out", path=path),
            embargo=_optional_str(data, "embargo", path=path),
        )

    def is_frozen(self) -> bool:
        return is_present(self.start) and is_present(self.end) and len(self.eras) > 0


@dataclass(frozen=True, slots=True, kw_only=True)
class InferenceSpec:
    """How uncertainty is estimated and how the search is corrected for."""

    bootstrap: str
    """e.g. ``stationary-block``, ``circular-block``, ``none-declared``."""
    block_length_policy: str
    """How the block length is chosen, including whether it is tuned on the data."""
    multiple_testing_correction: str
    """e.g. ``benjamini-hochberg-fdr-0.10``, ``holm-fwer-0.05``, ``deflated-sharpe``."""
    confidence_level: float = 0.95
    resamples: int = 10_000
    notes: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, JsonValue], *, path: str) -> InferenceSpec:
        _reject_unknown(
            data,
            {
                "bootstrap",
                "block_length_policy",
                "multiple_testing_correction",
                "confidence_level",
                "resamples",
                "notes",
            },
            path=path,
        )
        confidence = data.get("confidence_level", 0.95)
        if not isinstance(confidence, float | int) or isinstance(confidence, bool):
            raise SpecificationError(f"{path}.confidence_level must be a number")
        if not 0.0 < float(confidence) < 1.0:
            raise SpecificationError(
                f"{path}.confidence_level must lie strictly between 0 and 1, got {confidence!r}"
            )
        resamples = data.get("resamples", 10_000)
        if not isinstance(resamples, int) or isinstance(resamples, bool) or resamples <= 0:
            raise SpecificationError(f"{path}.resamples must be a positive integer")
        return cls(
            bootstrap=_require_str(data, "bootstrap", path=path),
            block_length_policy=_require_str(data, "block_length_policy", path=path),
            multiple_testing_correction=_require_str(
                data, "multiple_testing_correction", path=path
            ),
            confidence_level=float(confidence),
            resamples=resamples,
            notes=_optional_str(data, "notes", path=path),
        )


# --------------------------------------------------------------------------- #
# The specification
# --------------------------------------------------------------------------- #

_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "experiment_family",
        "title",
        "hypothesis",
        "mechanism",
        "falsifier",
        "universe",
        "sample_policy",
        "benchmark",
        "primary_metric",
        "secondary_metrics",
        "cost_model",
        "rebalance_rule",
        "inference",
        "rejection_rule",
        "run_kind",
        "consumes_final_holdout",
        "parameters",
        "seed",
        "entry_point",
        "evidence_class",
    }
)

_OPTIONAL_KEYS: Final[frozenset[str]] = frozenset(
    {"hostile_tests", "data_sources", "reporting_requirements", "notes"}
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Specification:
    """A frozen experiment specification.

    Construct one through :func:`load_specification` or
    :func:`specification_from_mapping` so that validation cannot be skipped.
    """

    experiment_family: str
    title: str
    hypothesis: str
    mechanism: str
    falsifier: str
    """The observable result that rejects the hypothesis, stated before the run."""
    universe: JsonValue
    sample_policy: SamplePolicy
    benchmark: JsonValue
    primary_metric: JsonValue
    secondary_metrics: tuple[JsonValue, ...]
    cost_model: JsonValue
    rebalance_rule: JsonValue
    inference: InferenceSpec
    rejection_rule: JsonValue
    run_kind: RunKind
    consumes_final_holdout: bool
    parameters: JsonValue
    seed: int | None
    entry_point: str
    """Registry name of the callable that executes this specification."""
    evidence_class: EvidenceClass
    hostile_tests: tuple[JsonValue, ...] = ()
    data_sources: tuple[JsonValue, ...] = ()
    reporting_requirements: tuple[JsonValue, ...] = ()
    notes: str = ""
    source_path: Path | None = field(
        default=None, compare=False, metadata={"hashed": False}
    )
    """Where this specification was read from. Not part of its identity."""

    def canonical_form(self) -> dict[str, JsonValue]:
        form: dict[str, JsonValue] = {"schema_version": SPEC_SCHEMA_VERSION}
        body = _canonical(self)
        if not isinstance(body, Mapping):  # pragma: no cover - defensive
            raise SpecificationError("canonical form of a specification must be a mapping")
        form.update(body)
        return form

    def canonical_json(self) -> str:
        return canonical_json(self.canonical_form())

    @property
    def spec_hash(self) -> str:
        """SHA-256 of the canonical JSON. This is the unit the ledger counts."""
        return sha256_text(self.canonical_json())


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #


def _reject_unknown(data: Mapping[str, JsonValue], allowed: set[str], *, path: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise SpecificationError(
            f"unknown key(s) at {path}: {', '.join(unknown)}. "
            f"Allowed: {', '.join(sorted(allowed))}. "
            "A misspelled key would otherwise silently drop a load-bearing field."
        )


def _require_str(data: Mapping[str, JsonValue], key: str, *, path: str) -> str:
    if key not in data:
        raise SpecificationError(f"missing required key {path}.{key}")
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        raise SpecificationError(f"{path}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _optional_str(data: Mapping[str, JsonValue], key: str, *, path: str) -> str:
    value = data.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SpecificationError(f"{path}.{key} must be a string, got {value!r}")
    return value.strip()


def _sequence(data: Mapping[str, JsonValue], key: str, *, path: str) -> tuple[JsonValue, ...]:
    value = data.get(key, ())
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise SpecificationError(f"{path}.{key} must be a list, got {value!r}")
    return tuple(value)


def specification_from_mapping(
    raw: Mapping[str, object], *, source_path: Path | None = None
) -> Specification:
    """Validate and freeze a parsed specification mapping.

    Raises :class:`SpecificationError` on anything unexpected, including unknown
    keys. Raises :class:`ConfirmatoryGateError` when a confirmatory run is
    declared without the fields that make it confirmatory.
    """
    where = str(source_path) if source_path is not None else "<mapping>"
    frozen = freeze_json(dict(raw), path=where)
    if not isinstance(frozen, Mapping):  # pragma: no cover - defensive
        raise SpecificationError(f"{where}: specification must be a mapping")

    missing = sorted(_REQUIRED_KEYS - set(frozen))
    if missing:
        raise SpecificationError(f"{where}: missing required key(s): {', '.join(missing)}")
    _reject_unknown(frozen, set(_REQUIRED_KEYS | _OPTIONAL_KEYS), path=where)

    run_kind_raw = _require_str(frozen, "run_kind", path=where)
    try:
        run_kind = RunKind(run_kind_raw)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in RunKind)
        raise SpecificationError(
            f"{where}.run_kind must be one of {allowed}, got {run_kind_raw!r}"
        ) from exc

    evidence_raw = _require_str(frozen, "evidence_class", path=where)
    try:
        evidence_class = EvidenceClass(evidence_raw)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in EvidenceClass)
        raise SpecificationError(
            f"{where}.evidence_class must be one of {allowed}, got {evidence_raw!r}"
        ) from exc

    sample_policy_raw = frozen["sample_policy"]
    if not isinstance(sample_policy_raw, Mapping):
        raise SpecificationError(f"{where}.sample_policy must be a mapping")
    sample_policy = SamplePolicy.from_mapping(sample_policy_raw, path=f"{where}.sample_policy")

    inference_raw = frozen["inference"]
    if not isinstance(inference_raw, Mapping):
        raise SpecificationError(f"{where}.inference must be a mapping")
    inference = InferenceSpec.from_mapping(inference_raw, path=f"{where}.inference")

    consumes = frozen["consumes_final_holdout"]
    if not isinstance(consumes, bool):
        raise SpecificationError(
            f"{where}.consumes_final_holdout must be true or false, got {consumes!r}"
        )

    seed = frozen["seed"]
    if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
        raise SpecificationError(f"{where}.seed must be an integer or null, got {seed!r}")

    spec = Specification(
        experiment_family=_require_str(frozen, "experiment_family", path=where),
        title=_require_str(frozen, "title", path=where),
        hypothesis=_require_str(frozen, "hypothesis", path=where),
        mechanism=_require_str(frozen, "mechanism", path=where),
        falsifier=_require_str(frozen, "falsifier", path=where),
        universe=frozen["universe"],
        sample_policy=sample_policy,
        benchmark=frozen["benchmark"],
        primary_metric=frozen["primary_metric"],
        secondary_metrics=_sequence(frozen, "secondary_metrics", path=where),
        cost_model=frozen["cost_model"],
        rebalance_rule=frozen["rebalance_rule"],
        inference=inference,
        rejection_rule=frozen["rejection_rule"],
        run_kind=run_kind,
        consumes_final_holdout=consumes,
        parameters=frozen["parameters"],
        seed=seed,
        entry_point=_require_str(frozen, "entry_point", path=where),
        evidence_class=evidence_class,
        hostile_tests=_sequence(frozen, "hostile_tests", path=where),
        data_sources=_sequence(frozen, "data_sources", path=where),
        reporting_requirements=_sequence(frozen, "reporting_requirements", path=where),
        notes=_optional_str(frozen, "notes", path=where),
        source_path=source_path,
    )
    validate_specification(spec, where=where)
    return spec


def load_specification(path: Path | str) -> Specification:
    """Load and validate a specification from a YAML file."""
    resolved = Path(path)
    try:
        text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecificationError(f"cannot read specification {resolved}: {exc}") from exc
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SpecificationError(f"{resolved}: invalid YAML: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise SpecificationError(
            f"{resolved}: top level of a specification must be a mapping, "
            f"got {type(raw).__name__}"
        )
    return specification_from_mapping(raw, source_path=resolved)


# --------------------------------------------------------------------------- #
# Gates
# --------------------------------------------------------------------------- #

_CONFIRMATORY_REQUIRED: Final = ("benchmark", "primary_metric", "cost_model", "rejection_rule")


def validate_specification(spec: Specification, *, where: str | None = None) -> None:
    """Refuse specifications that claim more than they have frozen.

    A confirmatory run needs a frozen benchmark, primary metric, cost model,
    sample policy and rejection rule, and a seed. A run that consumes the final
    holdout must be confirmatory: looking once converts a holdout into training
    data, so it may not be spent exploring.
    """
    label = where or str(spec.source_path or spec.experiment_family)

    if spec.consumes_final_holdout and spec.run_kind is not RunKind.CONFIRMATORY:
        raise ConfirmatoryGateError(
            f"{label}: consumes_final_holdout is true but run_kind is "
            f"{spec.run_kind.value!r}. The final holdout may only be spent by a "
            "confirmatory run; looking once converts it into training data."
        )

    if spec.run_kind is not RunKind.CONFIRMATORY:
        return

    missing = [name for name in _CONFIRMATORY_REQUIRED if not is_present(getattr(spec, name))]
    if not spec.sample_policy.is_frozen():
        missing.append("sample_policy")
    if missing:
        raise ConfirmatoryGateError(
            f"{label}: a confirmatory run requires a frozen "
            f"{', '.join(sorted(missing))}. Declare run_kind: exploratory, or freeze "
            "the missing field(s) before running."
        )
    if spec.seed is None:
        raise ConfirmatoryGateError(
            f"{label}: a confirmatory run requires an explicit seed. A confirmatory "
            "result that cannot be reproduced bit-for-bit is not confirmatory."
        )
