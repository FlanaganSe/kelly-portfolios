"""The ledger is append-only, concurrent, and never repaired in place."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from portfolio_edge.experiments.ledger import (
    TRIALS_CAVEAT,
    Ledger,
    LedgerEntry,
    LedgerError,
    LedgerEvent,
    LedgerFormatError,
    Origin,
    RunStatus,
    environment_snapshot,
    fold_runs,
    search_counts,
)
from portfolio_edge.experiments.result import ArtifactRecord, ResultStatus
from portfolio_edge.experiments.specification import RunKind
from tests.unit.test_experiments_support import make_entry

WORKER = textwrap.dedent(
    """
    import sys

    from portfolio_edge.experiments.ledger import (
        Ledger, LedgerEntry, LedgerEvent, RunStatus, utc_now,
    )

    path, tag, count = sys.argv[1], sys.argv[2], int(sys.argv[3])
    ledger = Ledger(path)
    padding = "x" * 8000
    for index in range(count):
        ledger.append(
            LedgerEntry(
                run_id=f"{tag}-{index}",
                experiment_family="concurrency",
                timestamp_utc=utc_now().isoformat(),
                event=LedgerEvent.STARTED,
                status=RunStatus.STARTED,
                notes=padding,
            )
        )
    """
)


def test_append_and_read_round_trip(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    written = ledger.append(make_entry(spec_hash="a" * 64, seed=11))
    (read_back,) = ledger.read()
    assert read_back == written


def test_every_line_is_one_complete_json_object(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    for index in range(5):
        ledger.append(make_entry(run_id=f"run-{index}", notes="multi\nline\nnotes"))
    lines = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5
    for line in lines:
        assert isinstance(json.loads(line), dict)


def test_environment_records_python_and_numeric_dependencies() -> None:
    snapshot = environment_snapshot()
    assert snapshot["python_version"]
    packages = snapshot["packages"]
    assert isinstance(packages, dict)
    for name in ("numpy", "pandas", "pyarrow", "PyYAML"):
        assert packages[name] != "not-installed"


def test_failed_entry_must_state_a_reason() -> None:
    with pytest.raises(LedgerFormatError, match="failure_reason"):
        make_entry(event=LedgerEvent.FAILED, status=RunStatus.FAILED)


def test_event_and_status_must_agree() -> None:
    with pytest.raises(LedgerFormatError, match="must carry status"):
        make_entry(event=LedgerEvent.SUCCEEDED, status=RunStatus.STARTED)


def test_results_viewed_flag_belongs_to_the_viewed_event() -> None:
    with pytest.raises(LedgerFormatError, match="results_viewed"):
        make_entry(results_viewed=True)


def test_there_is_no_update_in_place_api() -> None:
    for forbidden in ("update", "replace", "delete", "rewrite", "set_status"):
        assert not hasattr(Ledger, forbidden)


def test_viewing_results_is_a_new_entry_that_leaves_earlier_lines_untouched(
    tmp_path: Path,
) -> None:
    path = tmp_path / "ledger.jsonl"
    ledger = Ledger(path)
    ledger.append(make_entry(run_id="r1", spec_hash="a" * 64))
    ledger.append(
        make_entry(
            run_id="r1",
            event=LedgerEvent.SUCCEEDED,
            status=RunStatus.SUCCEEDED,
            spec_hash="a" * 64,
            result_status=ResultStatus.EXPLORATORY,
        )
    )
    before = path.read_bytes()

    viewed = ledger.record_results_viewed("r1", origin=Origin.HUMAN, notes="read in synthesis")

    after = path.read_bytes()
    assert after.startswith(before)
    assert viewed.event is LedgerEvent.RESULTS_VIEWED
    assert viewed.status is None
    assert viewed.run_id == "r1"

    entries = ledger.read()
    assert len(entries) == 3
    state = ledger.runs()["r1"]
    assert state.results_viewed is True
    assert state.status is RunStatus.SUCCEEDED
    assert state.entry_count == 3


def test_abandoning_a_run_is_a_new_entry(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.append(make_entry(run_id="r2"))
    ledger.record_abandoned("r2", reason="superseded by a corrected specification")
    state = ledger.runs()["r2"]
    assert state.status is RunStatus.ABANDONED
    assert state.failure_reason == "superseded by a corrected specification"


def test_abandoning_without_a_reason_is_refused(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.append(make_entry(run_id="r3"))
    with pytest.raises(LedgerError, match="state why"):
        ledger.record_abandoned("r3", reason="  ")


def test_viewing_an_unknown_run_is_an_error(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(LedgerError, match="no run"):
        ledger.record_results_viewed("nobody")


def test_fold_reconstructs_state_from_events() -> None:
    entries = (
        make_entry(run_id="r", spec_hash="h", seed=3),
        make_entry(
            run_id="r",
            event=LedgerEvent.FAILED,
            status=RunStatus.FAILED,
            failure_reason="boom",
            artifacts=(
                ArtifactRecord(path="r/result.json", sha256="0" * 64, size_bytes=10, kind="json"),
            ),
        ),
    )
    state = fold_runs(entries)["r"]
    assert state.status is RunStatus.FAILED
    assert state.is_terminal
    assert state.spec_hash == "h"
    assert state.seed == 3
    assert state.failure_reason == "boom"
    assert state.artifacts[0].path == "r/result.json"


def test_distinct_specifications_and_total_invocations_are_different_numbers() -> None:
    entries = (
        *(make_entry(run_id=f"run-{index}", spec_hash="a" * 64) for index in range(4)),
        make_entry(run_id="run-4", spec_hash="b" * 64),
    )
    counts = search_counts(entries)
    assert counts.total_invocations == 5
    assert counts.distinct_spec_hashes == 2
    assert counts.upper_bound_on_independent_trials == 2
    assert counts.distinct_spec_hashes_by_family == {"exp_test_family": 2}
    assert "UPPER BOUND" in counts.caveat
    assert "not solved by counting" in TRIALS_CAVEAT


def test_search_counts_filters_by_family_and_flags_unhashed_runs() -> None:
    entries = (
        make_entry(run_id="a", spec_hash="a" * 64),
        make_entry(run_id="b", experiment_family="other", spec_hash="b" * 64),
        make_entry(run_id="c", spec_hash=None),
    )
    counts = search_counts(entries, experiment_family="exp_test_family")
    assert counts.total_invocations == 2
    assert counts.distinct_spec_hashes == 1
    assert counts.runs_without_spec_hash == 1


def test_malformed_line_names_its_line_number(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    ledger = Ledger(path)
    ledger.append(make_entry())
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("{not json}\n")
    with pytest.raises(LedgerFormatError, match=r":2:"):
        ledger.read()


def test_unknown_event_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    ledger = Ledger(path)
    payload = make_entry().to_json()
    payload["event"] = "worked"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(LedgerFormatError, match="unknown ledger event"):
        ledger.read()


def test_reading_an_absent_ledger_returns_nothing(tmp_path: Path) -> None:
    assert Ledger(tmp_path / "never-written.jsonl").read() == ()


def _append_many(path: Path, tag: str, count: int) -> None:
    ledger = Ledger(path)
    padding = "y" * 8000
    for index in range(count):
        ledger.append(
            make_entry(
                run_id=f"{tag}-{index}",
                experiment_family="concurrency",
                notes=padding,
                run_kind=RunKind.EXPLORATORY,
            )
        )


def test_concurrent_threads_never_lose_or_interleave_a_line(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    threads, per_thread = 8, 50
    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = [
            pool.submit(_append_many, path, f"thread{index}", per_thread)
            for index in range(threads)
        ]
        for future in futures:
            future.result()

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == threads * per_thread
    entries = Ledger(path).read()
    assert len({entry.entry_id for entry in entries}) == threads * per_thread
    assert len({entry.run_id for entry in entries}) == threads * per_thread


def test_concurrent_processes_never_lose_or_interleave_a_line(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    script = tmp_path / "worker.py"
    script.write_text(WORKER, encoding="utf-8")
    processes, per_process = 6, 40

    source_root = Path(__file__).resolve().parents[2] / "src"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(source_root), *([env["PYTHONPATH"]] if "PYTHONPATH" in env else [])]
    )

    running = [
        subprocess.Popen(
            [sys.executable, str(script), str(path), f"proc{index}", str(per_process)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for index in range(processes)
    ]
    for process in running:
        _, errors = process.communicate(timeout=120)
        assert process.returncode == 0, errors

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == processes * per_process
    for number, line in enumerate(lines, start=1):
        payload = json.loads(line)
        assert isinstance(payload, dict), number
        assert len(payload["notes"]) == 8000

    entries = Ledger(path).read()
    assert len(entries) == processes * per_process
    assert len({entry.entry_id for entry in entries}) == processes * per_process
    counts = search_counts(entries, experiment_family="concurrency")
    assert counts.total_invocations == processes * per_process


def test_entry_round_trips_through_json() -> None:
    entry = LedgerEntry(
        run_id="r",
        experiment_family="fam",
        timestamp_utc="2026-08-11T00:00:00+00:00",
        event=LedgerEvent.SUCCEEDED,
        status=RunStatus.SUCCEEDED,
        git_commit="deadbeef",
        worktree_dirty=True,
        diff_sha256="c" * 64,
        spec_hash="d" * 64,
        dataset_manifest_hashes=("e" * 64,),
        code_version="0.1.0",
        environment=environment_snapshot(),
        parameters={"alpha": 1},
        seed=5,
        artifacts=(
            ArtifactRecord(path="r/result.json", sha256="f" * 64, size_bytes=3, kind="json"),
        ),
        run_kind=RunKind.CONFIRMATORY,
        parent_run_id="p",
        origin=Origin.HUMAN,
        consumes_final_holdout=True,
        result_status=ResultStatus.UNRESOLVED,
    )
    assert LedgerEntry.from_json(json.loads(entry.to_line())) == entry
