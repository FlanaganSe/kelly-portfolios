"""Write result artifacts and hash every file.

Artifacts live in ``research/artifacts/<run_id>/``. ``summary.md`` and
``manifest.json`` are committed; ``frames/`` and ``result.json`` are not, because
they are large and regenerable. The hashes returned here are the durable record:
the ledger keeps them, the bytes may be regenerated.

This split is load-bearing. Until 2026-08-22 the whole directory was ignored, so a
fresh clone held the ledger -- what was run -- and no results at all. Every measured
number reached a reader only by being retyped into ``docs/research/``, which is why
that corpus grew into an archive. A result's numbers belong in its summary; prose
cites the summary rather than retyping it.

Nothing is overwritten. A run identifier is unique, so an existing directory
means either a reused identifier or a rerun pretending to be the first run, and
both are errors rather than silent replacements.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from portfolio_edge.experiments.result import ArtifactRecord, ExperimentResult
from portfolio_edge.experiments.specification import JsonValue, Specification, plain_json
from portfolio_edge.reporting.tables import render_result

_SAFE_NAME: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_HASH_CHUNK: Final = 1 << 20


class ArtifactError(Exception):
    """An artifact could not be written, or would have overwritten another."""


def default_artifact_root() -> Path:
    """``research/artifacts``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3] / "artifacts"


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_HASH_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _write_bytes(path: Path, payload: bytes) -> None:
    """Write via a temporary file and rename, so a reader never sees a partial file."""
    temporary = path.with_name(path.name + ".partial")
    with open(temporary, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _record(root: Path, path: Path, kind: str) -> ArtifactRecord:
    return ArtifactRecord(
        path=path.relative_to(root).as_posix(),
        sha256=hash_file(path),
        size_bytes=path.stat().st_size,
        kind=kind,
    )


def write_result_artifacts(
    result: ExperimentResult,
    *,
    run_id: str,
    artifact_root: Path | str | None = None,
    specification: Specification | None = None,
    extra_json: Mapping[str, JsonValue] | None = None,
    write_parquet: bool = True,
) -> tuple[ArtifactRecord, ...]:
    """Write ``result.json``, optional Parquet frames, a Markdown table and a manifest.

    Returns one :class:`ArtifactRecord` per file, hashed, with paths relative to
    the artifact root. The manifest is written last and is itself recorded, so the
    returned tuple hashes every byte the run produced.
    """
    root = Path(artifact_root) if artifact_root is not None else default_artifact_root()
    if not _SAFE_NAME.match(run_id):
        raise ArtifactError(f"run_id {run_id!r} is not a safe directory name")
    run_directory = root / run_id
    if run_directory.exists() and any(run_directory.iterdir()):
        raise ArtifactError(
            f"artifact directory {run_directory} already exists and is not empty. "
            "Run identifiers are unique; refusing to overwrite another run's evidence."
        )
    run_directory.mkdir(parents=True, exist_ok=True)

    records: list[ArtifactRecord] = []

    payload: dict[str, JsonValue] = {
        "run_id": run_id,
        "spec_hash": specification.spec_hash if specification is not None else None,
        "experiment_family": (
            specification.experiment_family if specification is not None else None
        ),
        "result": result.to_json(),
    }
    if extra_json:
        payload["extra"] = plain_json(dict(extra_json))
    result_path = run_directory / "result.json"
    _write_bytes(
        result_path,
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode(
            "utf-8"
        )
        + b"\n",
    )
    records.append(_record(root, result_path, "json"))

    table_path = run_directory / "summary.md"
    _write_bytes(
        table_path,
        render_result(result, specification=specification, run_id=run_id).encode("utf-8"),
    )
    records.append(_record(root, table_path, "markdown"))

    if write_parquet and result.frames:
        frames_directory = run_directory / "frames"
        frames_directory.mkdir(exist_ok=True)
        for name, frame in sorted(result.frames.items()):
            if not _SAFE_NAME.match(name):
                raise ArtifactError(f"frame name {name!r} is not a safe file name")
            frame_path = frames_directory / f"{name}.parquet"
            try:
                frame.to_parquet(frame_path)
            except (ImportError, ValueError, OSError) as exc:
                raise ArtifactError(f"cannot write frame {name!r} to {frame_path}: {exc}") from exc
            records.append(_record(root, frame_path, "parquet"))

    manifest_path = run_directory / "manifest.json"
    manifest: dict[str, JsonValue] = {
        "run_id": run_id,
        "spec_hash": specification.spec_hash if specification is not None else None,
        "status": result.status.value,
        "files": [record.to_json() for record in records],
    }
    _write_bytes(
        manifest_path,
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n",
    )
    records.append(_record(root, manifest_path, "manifest"))
    return tuple(records)


def verify_artifacts(
    records: tuple[ArtifactRecord, ...], *, artifact_root: Path | str | None = None
) -> tuple[str, ...]:
    """Return the paths whose bytes no longer match their recorded hash."""
    root = Path(artifact_root) if artifact_root is not None else default_artifact_root()
    mismatched: list[str] = []
    for record in records:
        path = root / record.path
        if not path.exists() or hash_file(path) != record.sha256:
            mismatched.append(record.path)
    return tuple(mismatched)
