"""The committed manifests must stay loadable and internally consistent.

Offline by design. This does not re-download anything and does not check that a
manifest still describes the current file at its URL: a Ken French rebuild
changes ``sha256_raw`` by design, and a test that failed on that would be
punishing the source for behaving as documented. What it checks is that every
committed manifest parses, carries the full schema, and makes the provenance
claims this repository requires it to make.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_edge.data.manifest import MANIFEST_SCHEMA_VERSION, read_manifest

MANIFEST_DIR = Path(__file__).resolve().parents[2] / "data-manifests"


def _manifest_paths() -> list[Path]:
    return sorted(MANIFEST_DIR.glob("*.json"))


def test_manifests_have_been_committed() -> None:
    assert _manifest_paths(), f"no manifests under {MANIFEST_DIR}"


@pytest.mark.parametrize("path", _manifest_paths(), ids=lambda p: p.stem)
def test_a_committed_manifest_is_complete(path: Path) -> None:
    manifest = read_manifest(path)

    assert manifest.schema_version == MANIFEST_SCHEMA_VERSION
    assert manifest.dataset_id == path.stem
    assert manifest.source_url.startswith("https://")
    assert len(manifest.sha256_raw) == 64
    assert len(manifest.sha256_normalized) == 64
    assert manifest.rows > 0
    assert manifest.first_observation and manifest.last_observation
    assert manifest.first_observation <= manifest.last_observation
    assert manifest.parser_version
    assert manifest.units and manifest.source_units and manifest.unit_transform
    assert manifest.license_or_terms_url.startswith("https://")


@pytest.mark.parametrize("path", _manifest_paths(), ids=lambda p: p.stem)
def test_a_committed_manifest_states_its_revision_and_availability_policy(
    path: Path,
) -> None:
    manifest = read_manifest(path)

    # Every source in this repository is a rebuilt-in-place series, so every
    # manifest must say so rather than leaving a reader to assume otherwise.
    assert "not point-in-time" in manifest.revision_policy.lower()
    assert len(manifest.availability_policy) > 40


@pytest.mark.parametrize("path", _manifest_paths(), ids=lambda p: p.stem)
def test_a_committed_manifest_carries_its_warnings(path: Path) -> None:
    manifest = read_manifest(path)
    assert manifest.warnings, "a manifest with no warnings has probably lost them"


@pytest.mark.parametrize("path", _manifest_paths(), ids=lambda p: p.stem)
def test_a_percent_source_records_the_conversion(path: Path) -> None:
    manifest = read_manifest(path)
    if manifest.source_units.startswith("percent"):
        assert manifest.unit_transform == "value / 100"
        assert manifest.units.startswith("decimal")


def test_the_three_cash_rates_are_recorded_as_distinct_datasets() -> None:
    ids = {read_manifest(p).dataset_id for p in _manifest_paths()}
    assert {"fred_tb3ms", "fred_dgs3mo", "fred_dff"} <= ids

    frequencies = {
        read_manifest(MANIFEST_DIR / f"{name}.json").frequency
        for name in ("fred_tb3ms", "fred_dgs3mo", "fred_dff")
    }
    assert frequencies == {"monthly", "daily"}
