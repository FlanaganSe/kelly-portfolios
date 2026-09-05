"""No-data checks for audit execution boundaries and source identities."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.experiments import exp_028_tilt_estimand_audit as audit
from portfolio_edge.experiments.registry import RunContext
from portfolio_edge.experiments.specification import load_specification


def test_audit_refuses_changed_emitter_before_data_access(monkeypatch, tmp_path) -> None:
    specification = load_specification(Path("experiments/exp_028_tilt_estimand_audit.yaml"))
    specification = replace(specification, parameters={"emitter_sha256": "wrong"})

    def forbidden():
        pytest.fail("a source mismatch must fail before constructing a cache")

    monkeypatch.setattr(audit, "RecordingCache", forbidden)
    context = RunContext(run_id="test", seed=1, rng=np.random.default_rng(1), artifact_dir=tmp_path)
    with pytest.raises(ValueError, match="registered emitter changed"):
        audit.run(specification, context)


def test_audit_captures_output_and_read_sources(monkeypatch, tmp_path, capsys):
    specification = load_specification(Path("experiments/exp_028_tilt_estimand_audit.yaml"))

    def emit(*, cache):
        cache.sources[("source", "abc")] = {"url": "source", "sha256": "abc"}
        print("priced edge differs from residual alpha")

    monkeypatch.setattr(audit._untested_tilts_tables, "main", emit)
    context = RunContext(run_id="test", seed=1, rng=np.random.default_rng(1), artifact_dir=tmp_path)
    result = audit.run(specification, context)
    assert capsys.readouterr().out == ""
    assert result.diagnostics["source_artifacts"] == [{"url": "source", "sha256": "abc"}]
    assert result.diagnostics["raw_table_output"] == "priced edge differs from residual alpha\n"
