"""The specification is the unit the ledger counts, so its hash must be exact."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest
import yaml

from portfolio_edge.experiments.specification import (
    ConfirmatoryGateError,
    EvidenceClass,
    RunKind,
    SpecificationError,
    load_specification,
    specification_from_mapping,
)
from tests.unit.test_experiments_support import build_spec, valid_spec_mapping


def _confirmatory(**overrides: Any) -> dict[str, Any]:
    data = valid_spec_mapping(run_kind="confirmatory")
    data.update(overrides)
    return data


def test_minimal_specification_loads() -> None:
    spec = build_spec()
    assert spec.run_kind is RunKind.EXPLORATORY
    assert spec.evidence_class is EvidenceClass.POLICY_SIMULATION
    assert spec.sample_policy.eras[0].name == "full_sample"
    assert len(spec.spec_hash) == 64


def test_hash_is_independent_of_key_order() -> None:
    forward = valid_spec_mapping()
    backward = dict(reversed(list(forward.items())))
    sample = dict(backward["sample_policy"])
    backward["sample_policy"] = dict(reversed(list(sample.items())))
    assert (
        specification_from_mapping(forward).spec_hash
        == specification_from_mapping(backward).spec_hash
    )


def test_hash_is_independent_of_yaml_formatting(tmp_path: Path) -> None:
    mapping = valid_spec_mapping()
    flow = tmp_path / "flow.yaml"
    block = tmp_path / "block.yaml"
    flow.write_text(yaml.safe_dump(mapping, default_flow_style=True), encoding="utf-8")
    block.write_text(
        "# a comment that must not matter\n"
        + yaml.safe_dump(mapping, default_flow_style=False, sort_keys=True),
        encoding="utf-8",
    )
    assert load_specification(flow).spec_hash == load_specification(block).spec_hash


def test_source_path_is_not_part_of_identity(tmp_path: Path) -> None:
    mapping = valid_spec_mapping()
    path = tmp_path / "spec.yaml"
    path.write_text(yaml.safe_dump(mapping), encoding="utf-8")
    assert load_specification(path).spec_hash == specification_from_mapping(mapping).spec_hash


@pytest.mark.parametrize(
    "overrides",
    [
        {"falsifier": "The point estimate of the mean is below zero."},
        {"seed": 8},
        {"parameters": {"alpha": 2}},
        {"parameters": {"alpha": "1"}},
        {"cost_model": {"applied": True, "reason": "synthetic data has no costs"}},
        {"secondary_metrics": ["volatility", "drawdown"]},
        {"secondary_metrics": ["drawdown", "volatility"]},
        {"consumes_final_holdout": True, "run_kind": "confirmatory"},
        {"entry_point": "other_experiment"},
        {"evidence_class": "source-reproduction"},
        {"title": "Test experiment (revised)"},
    ],
    ids=lambda value: str(sorted(value)),
)
def test_any_load_bearing_change_changes_the_hash(overrides: dict[str, Any]) -> None:
    assert build_spec().spec_hash != build_spec(**overrides).spec_hash


def test_era_boundary_change_changes_the_hash() -> None:
    moved = valid_spec_mapping()
    moved["sample_policy"]["eras"][0]["end"] = "2019-12"
    assert build_spec().spec_hash != specification_from_mapping(moved).spec_hash


def test_yaml_dates_normalise_to_strings() -> None:
    dated = valid_spec_mapping()
    dated["sample_policy"]["eras"][0]["rationale"] = "1990-01-01"
    quoted = valid_spec_mapping()
    quoted["sample_policy"]["eras"][0]["rationale"] = dt.date(1990, 1, 1)
    assert (
        specification_from_mapping(dated).spec_hash
        == specification_from_mapping(quoted).spec_hash
    )


def test_confirmatory_refused_without_frozen_fields() -> None:
    with pytest.raises(ConfirmatoryGateError) as caught:
        specification_from_mapping(
            _confirmatory(benchmark={}, primary_metric="", cost_model=None, rejection_rule="  ")
        )
    message = str(caught.value)
    for field in ("benchmark", "primary_metric", "cost_model", "rejection_rule"):
        assert field in message


def test_confirmatory_refused_without_frozen_sample_policy() -> None:
    data = _confirmatory()
    data["sample_policy"] = {
        "start": "1990-01",
        "end": "2020-12",
        "held_out": "nothing",
        "eras": [],
    }
    with pytest.raises(ConfirmatoryGateError, match="sample_policy"):
        specification_from_mapping(data)


def test_confirmatory_refused_without_seed() -> None:
    with pytest.raises(ConfirmatoryGateError, match="explicit seed"):
        specification_from_mapping(_confirmatory(seed=None))


def test_confirmatory_with_every_field_frozen_is_accepted() -> None:
    spec = specification_from_mapping(_confirmatory())
    assert spec.run_kind is RunKind.CONFIRMATORY


def test_final_holdout_requires_confirmatory() -> None:
    with pytest.raises(ConfirmatoryGateError, match="final holdout"):
        specification_from_mapping(valid_spec_mapping(consumes_final_holdout=True))


def test_final_holdout_allowed_for_confirmatory() -> None:
    spec = specification_from_mapping(_confirmatory(consumes_final_holdout=True))
    assert spec.consumes_final_holdout is True


def test_unknown_key_is_refused() -> None:
    with pytest.raises(SpecificationError, match="falsifer"):
        specification_from_mapping(valid_spec_mapping(falsifer="typo"))


def test_missing_key_is_refused() -> None:
    data = valid_spec_mapping()
    del data["rejection_rule"]
    with pytest.raises(SpecificationError, match="rejection_rule"):
        specification_from_mapping(data)


def test_unknown_run_kind_is_refused() -> None:
    with pytest.raises(SpecificationError, match="run_kind"):
        specification_from_mapping(valid_spec_mapping(run_kind="pilot"))


def test_unknown_evidence_class_is_refused() -> None:
    with pytest.raises(SpecificationError, match="evidence_class"):
        specification_from_mapping(valid_spec_mapping(evidence_class="a-good-one"))


def test_non_boolean_holdout_flag_is_refused() -> None:
    with pytest.raises(SpecificationError, match="consumes_final_holdout"):
        specification_from_mapping(valid_spec_mapping(consumes_final_holdout="false"))


def test_duplicate_era_names_are_refused() -> None:
    data = valid_spec_mapping()
    era = dict(data["sample_policy"]["eras"][0])
    data["sample_policy"]["eras"] = [era, dict(era)]
    with pytest.raises(SpecificationError, match="duplicate era names"):
        specification_from_mapping(data)


def test_non_finite_number_is_refused() -> None:
    with pytest.raises(SpecificationError, match="non-finite"):
        specification_from_mapping(valid_spec_mapping(parameters={"alpha": float("inf")}))


def test_unsupported_value_type_is_refused() -> None:
    with pytest.raises(SpecificationError, match="unsupported value type"):
        specification_from_mapping(valid_spec_mapping(parameters={"alpha": {1, 2}}))


def test_specification_is_frozen() -> None:
    spec = build_spec()
    with pytest.raises(AttributeError):
        spec.title = "changed"  # type: ignore[misc]


def test_top_level_must_be_a_mapping(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("- not\n- a mapping\n", encoding="utf-8")
    with pytest.raises(SpecificationError, match="must be a mapping"):
        load_specification(path)


def test_missing_file_reports_its_path(tmp_path: Path) -> None:
    with pytest.raises(SpecificationError, match="cannot read specification"):
        load_specification(tmp_path / "absent.yaml")
