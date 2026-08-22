"""Artifacts are hashed on the way out and never overwritten."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from portfolio_edge.experiments.result import ExperimentResult, ResultStatus
from portfolio_edge.reporting.artifacts import (
    ArtifactError,
    default_artifact_root,
    hash_file,
    verify_artifacts,
    write_result_artifacts,
)
from tests.unit.test_experiments_support import build_spec, sample_result


def test_writes_json_summary_and_manifest_with_matching_hashes(tmp_path: Path) -> None:
    spec = build_spec()
    records = write_result_artifacts(
        sample_result(),
        run_id="run1",
        artifact_root=tmp_path,
        specification=spec,
    )
    paths = {record.path for record in records}
    assert paths == {
        "run1/result.json",
        "run1/summary.md",
        "run1/manifest.json",
    }
    for record in records:
        written = tmp_path / record.path
        assert written.exists()
        assert record.sha256 == hash_file(written)
        assert record.size_bytes == written.stat().st_size

    payload = json.loads((tmp_path / "run1" / "result.json").read_text(encoding="utf-8"))
    assert payload["spec_hash"] == spec.spec_hash
    assert payload["result"]["status"] == "exploratory"
    assert payload["result"]["estimates"][0]["units"]

    manifest = json.loads((tmp_path / "run1" / "manifest.json").read_text(encoding="utf-8"))
    assert {entry["path"] for entry in manifest["files"]} == {
        "run1/result.json",
        "run1/summary.md",
    }
    assert verify_artifacts(records, artifact_root=tmp_path) == ()


def test_parquet_frames_are_written_and_hashed(tmp_path: Path) -> None:
    frame = pd.DataFrame({"month": ["1990-01", "1990-02"], "ret": [0.01, -0.02]})
    result = ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary="with a frame",
        frames={"monthly_returns": frame},
    )
    records = write_result_artifacts(result, run_id="run2", artifact_root=tmp_path)
    parquet = [record for record in records if record.kind == "parquet"]
    assert [record.path for record in parquet] == ["run2/frames/monthly_returns.parquet"]
    round_tripped = pd.read_parquet(tmp_path / parquet[0].path)
    pd.testing.assert_frame_equal(round_tripped, frame)


def test_tampering_is_detected(tmp_path: Path) -> None:
    records = write_result_artifacts(sample_result(), run_id="run3", artifact_root=tmp_path)
    (tmp_path / "run3" / "summary.md").write_text("edited by hand\n", encoding="utf-8")
    assert verify_artifacts(records, artifact_root=tmp_path) == ("run3/summary.md",)


def test_an_existing_run_directory_is_never_overwritten(tmp_path: Path) -> None:
    write_result_artifacts(sample_result(), run_id="run4", artifact_root=tmp_path)
    with pytest.raises(ArtifactError, match="refusing to overwrite"):
        write_result_artifacts(sample_result(), run_id="run4", artifact_root=tmp_path)


def test_unsafe_names_are_refused(tmp_path: Path) -> None:
    with pytest.raises(ArtifactError, match="safe directory name"):
        write_result_artifacts(sample_result(), run_id="../escape", artifact_root=tmp_path)

    result = ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary="bad frame name",
        frames={"../escape": pd.DataFrame({"a": [1]})},
    )
    with pytest.raises(ArtifactError, match="safe file name"):
        write_result_artifacts(result, run_id="run5", artifact_root=tmp_path)


def test_no_partial_files_are_left_behind(tmp_path: Path) -> None:
    write_result_artifacts(sample_result(), run_id="run6", artifact_root=tmp_path)
    assert not list((tmp_path / "run6").glob("*.partial"))


def test_default_artifact_root_is_the_research_artifacts_directory() -> None:
    root = default_artifact_root()
    assert root.name == "artifacts"
    assert root.parent.name == "research"
