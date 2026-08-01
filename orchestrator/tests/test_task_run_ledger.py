# -*- coding: utf-8 -*-
"""task-run/v1 core の writer/validator/CLI と M01〜M26 回帰。"""
from __future__ import annotations

import inspect
import json
import multiprocessing
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.task_runs import (  # noqa: E402
    SCHEMA_VERSION,
    DamagedRunError,
    LedgerError,
    append_event,
    discover_runs,
    finish_run,
    init_pilot,
    record_test_run,
    start_run,
    validate_root,
    validate_run,
)
from tools.task_runs import ledger  # noqa: E402
from tools.task_runs.schema import load_schema  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "task-run@example.invalid")
    _git(repo, "config", "user.name", "task-run-test")
    (repo / "seed").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed")
    _git(repo, "commit", "-qm", "seed")
    return repo


@pytest.fixture
def root(git_repo: Path) -> Path:
    value = git_repo / "output" / "task-runs"
    init_pilot(value)
    return value


@pytest.fixture
def run(root: Path) -> tuple[Path, str]:
    run_id = start_run(
        root,
        slug="ledger-test",
        objective="ledger core test",
        task_class=2,
        task_kind="implementation",
    )
    return root, run_id


def _events_path(root: Path, run_id: str) -> Path:
    return root / run_id / "events.jsonl"


def _read_events(root: Path, run_id: str) -> list[dict[str, object]]:
    raw = _events_path(root, run_id).read_text(encoding="utf-8")
    return [json.loads(line) for line in raw.splitlines()]


def _write_events(root: Path, run_id: str, events: list[dict[str, object]]) -> None:
    raw = "".join(
        json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for event in events
    )
    _events_path(root, run_id).write_text(raw, encoding="utf-8", newline="")


def _mutate_events(
    root: Path,
    run_id: str,
    mutate: Callable[[list[dict[str, object]]], None],
) -> None:
    events = _read_events(root, run_id)
    mutate(events)
    _write_events(root, run_id, events)


def _append_wait(root: Path, run_id: str, duration: float = 0.25) -> dict[str, object]:
    return dict(append_event(root, run_id, "wait", {"wait_kind": "tool", "duration_s": duration}))


def _null_agent_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "stage_id": None,
        "agent_run_id": "agent-1",
        "product": "codex",
        "model": "gpt-5",
        "reasoning": "high",
        "role": "author",
        "scope": None,
        "status": "completed",
        "duration_s": 1.0,
        "tokens": {
            "input_tokens": None,
            "output_tokens": None,
            "cached_tokens": None,
            "total_tokens": None,
        },
    }
    payload.update(overrides)
    return payload


def _append_worker(root_text: str, run_id: str, count: int) -> None:
    root = Path(root_text)
    for _ in range(count):
        append_event(root, run_id, "wait", {"wait_kind": "tool", "duration_s": 0.001})


def test_schema_document_is_valid_draft7_and_public_api_is_v3_closed():
    schema = load_schema()
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert SCHEMA_VERSION == "task-run/v1"
    assert "timestamp" not in inspect.signature(append_event).parameters
    assert "measurement_source" not in inspect.signature(append_event).parameters
    assert "base_commit" not in inspect.signature(start_run).parameters
    assert "started_at" not in inspect.signature(start_run).parameters
    assert "timestamp" not in inspect.signature(finish_run).parameters
    assert "timestamp" not in inspect.signature(record_test_run).parameters
    assert "measurement_source" not in inspect.signature(record_test_run).parameters


def _schema_event(event_type: str) -> dict[str, object]:
    sources = {
        "stage_start": ("not-applicable", "not-applicable", "not-applicable"),
        "stage_end": ("timestamp-delta", "not-applicable", "not-applicable"),
        "agent_run": ("caller-supplied", "caller-supplied", "product-reported"),
        "test_run": ("monotonic-clock", "tool-reported", "not-applicable"),
        "wait": ("caller-supplied", "not-applicable", "not-applicable"),
        "finding_summary": ("not-applicable", "caller-supplied", "not-applicable"),
        "commit": ("not-applicable", "git-observed", "not-applicable"),
        "rework": ("caller-supplied", "not-applicable", "not-applicable"),
        "task_end": ("not-applicable", "not-applicable", "not-applicable"),
    }
    payloads: dict[str, dict[str, object]] = {
        "stage_start": {"stage_id": "s", "stage": "test"},
        "stage_end": {"stage_id": "s", "stage": "test", "outcome": "completed", "duration_s": 1},
        "agent_run": _null_agent_payload(tokens={
            "input_tokens": 2, "output_tokens": 1, "cached_tokens": 1, "total_tokens": 3,
        }),
        "test_run": {
            "stage_id": None, "suite_id": "suite", "suite_kind": "targeted",
            "duration_s": 1, "collected": 1, "passed": 1, "failed": 0,
            "skipped": 0, "exit_status": 0, "trigger": "final",
            "collected_node_digest": "abcdef123456",
        },
        "wait": {"wait_kind": "tool", "duration_s": 1},
        "finding_summary": {
            "stage_id": None, "review_id": "review", "review_kind": "independent",
            "real": 1, "refuted": 0, "unresolved": 0,
        },
        "commit": {"commit_sha": "a" * 40, "relation": "referenced"},
        "rework": {
            "stage_id": None, "rework_id": "rework", "cause": "test-failure",
            "duration_s": 1,
        },
        "task_end": {"outcome": "completed"},
    }
    duration, metrics, tokens = sources[event_type]
    value: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "task_run_id": "20260720-schema-aaaaaaaa",
        "seq": 1,
        "timestamp": "2026-07-20T00:00:01Z",
        "event": event_type,
        "event_id": "a" * 16,
        "measurement_source": {
            "timestamp": "system-clock", "duration": duration,
            "metrics": metrics, "tokens": tokens,
        },
    }
    value.update(payloads[event_type])
    return value


def test_schema_direct_source_matrix_and_nested_unknown_fields():
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft7Validator(load_schema())
    invalid_sources = {
        "stage_start": ("duration", "caller-supplied"),
        "stage_end": ("duration", "caller-supplied"),
        "agent_run": ("duration", "not-applicable"),
        "test_run": ("duration", "timestamp-delta"),
        "wait": ("metrics", "caller-supplied"),
        "finding_summary": ("duration", "caller-supplied"),
        "commit": ("metrics", "caller-supplied"),
        "rework": ("metrics", "caller-supplied"),
        "task_end": ("metrics", "caller-supplied"),
    }
    for event_type, (field, invalid) in invalid_sources.items():
        valid = _schema_event(event_type)
        validator.validate(valid)
        broken = json.loads(json.dumps(valid))
        broken["measurement_source"][field] = invalid
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)

    nested_cases = []
    agent = _schema_event("agent_run")
    agent["tokens"]["unknown"] = 1  # type: ignore[index]
    nested_cases.append(agent)
    source = _schema_event("wait")
    source["measurement_source"]["unknown"] = "x"  # type: ignore[index]
    nested_cases.append(source)
    pilot = {
        "schema_version": SCHEMA_VERSION, "pilot_started_at": "2026-07-20T00:00:00Z",
        "max_task_runs": 10, "max_days": 14, "unknown": True,
    }
    nested_cases.append(pilot)
    task = {
        "schema_version": SCHEMA_VERSION,
        "task_run_id": "20260720-schema-aaaaaaaa", "objective": "schema",
        "task_class": 2, "task_kind": "implementation",
        "started_at": "2026-07-20T00:00:00Z", "base_commit": "a" * 40,
        "base_commit_source": "git-observed",
        "authority": "development-observation-not-evidence",
        "measurement_policy": dict(ledger.MEASUREMENT_POLICY), "unknown": True,
    }
    nested_cases.append(task)
    for broken in nested_cases:
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_init_and_start_publish_create_only_files_with_git_observed_head(root: Path, git_repo: Path):
    run_id = start_run(
        root, slug="core", objective="safe summary", task_class=3,
        task_kind="implementation",
    )
    run_dir = root / run_id
    task = json.loads((run_dir / "task.json").read_text(encoding="utf-8"))
    assert (run_dir / "events.jsonl").read_bytes() == b""
    assert task["base_commit"] == _git(git_repo, "rev-parse", "HEAD")
    assert task["base_commit_source"] == "git-observed"
    assert task["authority"] == "development-observation-not-evidence"
    assert validate_run(run_dir).events == ()


def test_git_observation_ignores_inherited_repository_overrides(
    root: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch,
):
    foreign = git_repo.parent / "foreign"
    foreign.mkdir()
    _git(foreign, "init", "-q")
    _git(foreign, "config", "user.email", "foreign@example.invalid")
    _git(foreign, "config", "user.name", "foreign")
    (foreign / "seed").write_text("foreign\n", encoding="utf-8")
    _git(foreign, "add", "seed")
    _git(foreign, "commit", "-qm", "foreign")
    expected = _git(git_repo, "rev-parse", "HEAD")
    foreign_head = _git(foreign, "rev-parse", "HEAD")
    monkeypatch.setenv("GIT_DIR", str(foreign / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(foreign))
    run_id = start_run(
        root, slug="clean-git-env", objective="clean git env", task_class=2,
        task_kind="implementation",
    )
    task = json.loads((root / run_id / "task.json").read_text(encoding="utf-8"))
    assert task["base_commit"] == expected
    assert task["base_commit"] != foreign_head


def test_start_is_create_only_and_byte_preserving(root: Path, monkeypatch: pytest.MonkeyPatch):
    fixed = datetime.now(timezone.utc)
    monkeypatch.setattr(ledger, "_utc_now", lambda: fixed)
    monkeypatch.setattr(ledger.secrets, "token_hex", lambda size: "a" * (size * 2))
    run_id = start_run(
        root, slug="same-id", objective="first", task_class=2,
        task_kind="implementation",
    )
    task_before = (root / run_id / "task.json").read_bytes()
    events_before = _events_path(root, run_id).read_bytes()
    with pytest.raises(LedgerError):
        start_run(
            root, slug="same-id", objective="replacement", task_class=2,
            task_kind="implementation",
        )
    assert (root / run_id / "task.json").read_bytes() == task_before
    assert _events_path(root, run_id).read_bytes() == events_before


def test_task_publish_helper_rejects_existing_task_bytes_directly(
    run: tuple[Path, str],
):
    root, run_id = run
    run_fd = ledger._open_directory(root / run_id)
    before = (root / run_id / "task.json").read_bytes()
    try:
        with pytest.raises(LedgerError):
            ledger._create_file_at(run_fd, "task.json", b"replacement\n", label="task.json")
    finally:
        os.close(run_fd)
    assert (root / run_id / "task.json").read_bytes() == before


def test_append_preserves_exact_prefix_and_writer_envelope(run: tuple[Path, str]):
    root, run_id = run
    before = _events_path(root, run_id).read_bytes()
    record = _append_wait(root, run_id)
    after = _events_path(root, run_id).read_bytes()
    assert after.startswith(before)
    assert after[:len(before)] == before
    assert record["seq"] == 1
    assert len(str(record["event_id"])) == 16
    assert str(record["timestamp"]).endswith("Z")
    assert record["measurement_source"] == {
        "timestamp": "system-clock",
        "duration": "caller-supplied",
        "metrics": "not-applicable",
        "tokens": "not-applicable",
    }


def test_append_prevalidation_failure_preserves_exact_bytes(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    before = _events_path(root, run_id).read_bytes()
    with pytest.raises(DamagedRunError):
        append_event(root, run_id, "wait", {"wait_kind": "tool", "duration_s": -1})
    assert _events_path(root, run_id).read_bytes() == before


def test_writer_rounds_caller_duration_to_millisecond_precision(run: tuple[Path, str]):
    root, run_id = run
    record = _append_wait(root, run_id, 1.23456)
    assert record["duration_s"] == 1.235
    assert validate_run(root / run_id).events[0]["duration_s"] == 1.235


def test_duration_above_realistic_cap_is_rejected_without_write(run: tuple[Path, str]):
    root, run_id = run
    before = _events_path(root, run_id).read_bytes()
    with pytest.raises(DamagedRunError):
        _append_wait(root, run_id, 10_000_000.001)
    assert _events_path(root, run_id).read_bytes() == before


def test_append_rejects_reserved_writer_fields_without_touching_bytes(run: tuple[Path, str]):
    root, run_id = run
    before = _events_path(root, run_id).read_bytes()
    with pytest.raises(DamagedRunError):
        append_event(root, run_id, "wait", {
            "wait_kind": "tool", "duration_s": 1, "timestamp": "2000-01-01T00:00:00Z",
        })
    assert _events_path(root, run_id).read_bytes() == before


def test_concurrent_append_keeps_all_records_and_exact_sequence(run: tuple[Path, str]):
    root, run_id = run
    context = multiprocessing.get_context("fork")
    processes = [context.Process(target=_append_worker, args=(str(root), run_id, 12)) for _ in range(4)]
    for process in processes:
        process.start()
    for process in processes:
        process.join(20)
        assert process.exitcode == 0
    validated = validate_run(root / run_id)
    assert len(validated.events) == 48
    assert [event["seq"] for event in validated.events] == list(range(1, 49))
    assert len({event["event_id"] for event in validated.events}) == 48


def test_append_calls_exclusive_flock(run: tuple[Path, str], monkeypatch: pytest.MonkeyPatch):
    root, run_id = run
    calls: list[int] = []
    real_flock = ledger.fcntl.flock

    def spy(fd: int, operation: int) -> None:
        calls.append(operation)
        real_flock(fd, operation)

    monkeypatch.setattr(ledger.fcntl, "flock", spy)
    _append_wait(root, run_id)
    assert any(operation & ledger.fcntl.LOCK_EX for operation in calls)


def test_ambiguous_fsync_failure_recognizes_same_event_id_once(
    run: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
):
    root, run_id = run
    real_fsync = ledger.os.fsync
    failed = False

    def fail_once(fd: int) -> None:
        nonlocal failed
        if not failed and Path(f"/proc/self/fd/{fd}").resolve() == _events_path(root, run_id):
            failed = True
            raise OSError("injected ambiguous fsync")
        real_fsync(fd)

    monkeypatch.setattr(ledger.os, "fsync", fail_once)
    record = _append_wait(root, run_id)
    events = validate_run(root / run_id).events
    assert failed
    assert len(events) == 1
    assert events[0]["event_id"] == record["event_id"]


def test_validate_rejects_truncated_final_line(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    path = _events_path(root, run_id)
    path.write_bytes(path.read_bytes()[:-2])
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_valid_json_without_final_newline(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    path = _events_path(root, run_id)
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_seq_gap(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _append_wait(root, run_id)
    _mutate_events(root, run_id, lambda events: events[1].update(seq=3))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_duplicate_seq(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _append_wait(root, run_id)
    _mutate_events(root, run_id, lambda events: events[1].update(seq=1))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_unknown_schema(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _mutate_events(root, run_id, lambda events: events[0].update(schema_version="task-run/v999"))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_task_id_mismatch_and_unknown_task_schema(run: tuple[Path, str]):
    root, run_id = run
    task_path = root / run_id / "task.json"
    original = json.loads(task_path.read_text(encoding="utf-8"))
    mismatch = dict(original)
    mismatch["task_run_id"] = "20260720-other-aaaaaaaa"
    task_path.write_text(json.dumps(mismatch, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)
    original["schema_version"] = "task-run/v2"
    task_path.write_text(json.dumps(original, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_unknown_event(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _mutate_events(root, run_id, lambda events: events[0].update(event="arbitrary"))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_extra_event_field(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _mutate_events(root, run_id, lambda events: events[0].update(raw_command="pytest secret"))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_timestamp_regression(
    run: tuple[Path, str], monkeypatch: pytest.MonkeyPatch,
):
    root, run_id = run
    task = json.loads((root / run_id / "task.json").read_text(encoding="utf-8"))
    started = datetime.fromisoformat(str(task["started_at"]).replace("Z", "+00:00"))
    clock = iter((started + timedelta(seconds=20), started + timedelta(seconds=40)))
    monkeypatch.setattr(ledger, "_utc_now", lambda: next(clock))
    _append_wait(root, run_id)
    _append_wait(root, run_id)
    regressed = ledger._format_timestamp(started + timedelta(seconds=10))
    _mutate_events(root, run_id, lambda events: events[1].update(timestamp=regressed))
    events = _read_events(root, run_id)
    assert events[0]["timestamp"] > events[1]["timestamp"] >= task["started_at"]
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_naive_timestamp(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _mutate_events(root, run_id, lambda events: events[0].update(timestamp="2026-07-20T00:00:00"))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_negative_duration(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _mutate_events(root, run_id, lambda events: events[0].update(duration_s=-0.001))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_negative_test_and_finding_counts(run: tuple[Path, str]):
    root, run_id = run
    root2_id = start_run(
        root, slug="finding-count", objective="finding count", task_class=2,
        task_kind="audit-review",
    )
    record_test_run(
        root, run_id, suite_id="suite", suite_kind="targeted", duration_s=1,
        exit_status=1,
        counts={"collected": 1, "passed": 0, "failed": 1, "skipped": 0},
        trigger="after-change", collected_node_digest=None,
    )
    _mutate_events(root, run_id, lambda events: events[0].update(failed=-1))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)

    append_event(root, root2_id, "finding_summary", {
        "stage_id": None, "review_id": "review", "review_kind": "independent",
        "real": 0, "refuted": 0, "unresolved": 0,
    })
    _mutate_events(root, root2_id, lambda events: events[0].update(real=-1))
    with pytest.raises(DamagedRunError):
        validate_run(root / root2_id)


def test_validate_rejects_inconsistent_total_tokens(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "agent_run", _null_agent_payload(tokens={
        "input_tokens": 10, "output_tokens": 5, "cached_tokens": 2, "total_tokens": 15,
    }))
    _mutate_events(root, run_id, lambda events: events[0]["tokens"].update(total_tokens=16))  # type: ignore[union-attr]
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_accepts_cached_tokens_without_double_addition(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "agent_run", _null_agent_payload(tokens={
        "input_tokens": 10, "output_tokens": 5, "cached_tokens": 4, "total_tokens": 15,
    }))
    assert validate_run(root / run_id).events[0]["tokens"]["total_tokens"] == 15  # type: ignore[index]


def test_validate_rejects_cached_above_input(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "agent_run", _null_agent_payload(tokens={
        "input_tokens": 2, "output_tokens": 1, "cached_tokens": 1, "total_tokens": 3,
    }))
    _mutate_events(
        root, run_id,
        lambda events: events[0]["tokens"].update(cached_tokens=3),  # type: ignore[union-attr]
    )
    event = _read_events(root, run_id)[0]
    assert event["measurement_source"]["tokens"] == "product-reported"  # type: ignore[index]
    assert event["tokens"] == {  # type: ignore[index]
        "input_tokens": 2, "output_tokens": 1, "cached_tokens": 3, "total_tokens": 3,
    }
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_value_with_unexposed_tokens(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "agent_run", _null_agent_payload())

    def mutate(events: list[dict[str, object]]) -> None:
        events[0]["tokens"]["input_tokens"] = 1  # type: ignore[index]

    _mutate_events(root, run_id, mutate)
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_agent_all_null_tokens_is_valid(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "agent_run", _null_agent_payload())
    event = validate_run(root / run_id).events[0]
    assert event["measurement_source"]["tokens"] == "not-exposed"  # type: ignore[index]


def test_validate_rejects_duplicate_event_id(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _append_wait(root, run_id)
    _mutate_events(root, run_id, lambda events: events[1].update(event_id=events[0]["event_id"]))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_unknown_stage_reference(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "agent_run", _null_agent_payload())
    _mutate_events(root, run_id, lambda events: events[0].update(stage_id="never-started"))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_validate_rejects_stage_overlap(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "stage_start", {"stage_id": "one", "stage": "implementation"})

    def mutate(events: list[dict[str, object]]) -> None:
        second = dict(events[0])
        second.update(seq=2, event_id="bbbbbbbbbbbbbbbb", stage_id="two")
        events.append(second)

    _mutate_events(root, run_id, mutate)
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_writer_rejects_wrong_stage_end_and_stage_id_reuse_without_writes(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "stage_start", {"stage_id": "one", "stage": "implementation"})
    before = _events_path(root, run_id).read_bytes()
    with pytest.raises(DamagedRunError):
        append_event(root, run_id, "stage_end", {
            "stage_id": "other", "stage": "implementation", "outcome": "completed",
        })
    assert _events_path(root, run_id).read_bytes() == before
    append_event(root, run_id, "stage_end", {
        "stage_id": "one", "stage": "implementation", "outcome": "completed",
    })
    before = _events_path(root, run_id).read_bytes()
    with pytest.raises(DamagedRunError):
        append_event(root, run_id, "stage_start", {"stage_id": "one", "stage": "review"})
    assert _events_path(root, run_id).read_bytes() == before


def test_validate_rejects_work_after_task_end(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    finish_run(root, run_id, "completed")

    def mutate(events: list[dict[str, object]]) -> None:
        wait, end = events
        end.update(seq=1, timestamp=wait["timestamp"])
        wait.update(seq=2, timestamp=events[1]["timestamp"] if False else wait["timestamp"])
        events[:] = [end, wait]

    _mutate_events(root, run_id, mutate)
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_writer_rejects_work_after_task_end_without_writes(run: tuple[Path, str]):
    root, run_id = run
    finish_run(root, run_id, "completed")
    before = _events_path(root, run_id).read_bytes()
    with pytest.raises(DamagedRunError):
        _append_wait(root, run_id)
    assert _events_path(root, run_id).read_bytes() == before


def test_validate_rejects_task_end_with_open_stage(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "stage_start", {"stage_id": "open", "stage": "implementation"})

    def mutate(events: list[dict[str, object]]) -> None:
        start = events[0]
        events.append({
            "schema_version": SCHEMA_VERSION,
            "task_run_id": run_id,
            "seq": 2,
            "timestamp": start["timestamp"],
            "event": "task_end",
            "event_id": "cccccccccccccccc",
            "measurement_source": {
                "timestamp": "system-clock", "duration": "not-applicable",
                "metrics": "not-applicable", "tokens": "not-applicable",
            },
            "recording_duration_s": 0.0,
            "outcome": "completed",
        })

    _mutate_events(root, run_id, mutate)
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_unfinished_open_stage_is_valid_unless_finished_required(run: tuple[Path, str]):
    root, run_id = run
    append_event(root, run_id, "stage_start", {"stage_id": "open", "stage": "review"})
    assert validate_run(root / run_id).open_stage_id == "open"
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id, require_finished=True)


def test_stage_end_duration_is_writer_timestamp_delta(
    root: Path, monkeypatch: pytest.MonkeyPatch,
):
    moments = iter([
        datetime(2026, 7, 20, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 20, 0, 0, 1, 100_000, tzinfo=timezone.utc),
        datetime(2026, 7, 20, 0, 0, 3, 345_000, tzinfo=timezone.utc),
    ])
    monkeypatch.setattr(ledger, "_utc_now", lambda: next(moments))
    run_id = start_run(
        root, slug="clock", objective="clock test", task_class=2,
        task_kind="implementation",
    )
    append_event(root, run_id, "stage_start", {"stage_id": "s", "stage": "test"})
    event = append_event(root, run_id, "stage_end", {
        "stage_id": "s", "stage": "test", "outcome": "completed",
    })
    assert event["duration_s"] == 2.245
    assert event["measurement_source"]["duration"] == "timestamp-delta"  # type: ignore[index]


def test_task_end_allows_zero_commits_and_post_end_existing_commits(run: tuple[Path, str], git_repo: Path):
    root, run_id = run
    finish_run(root, run_id, "completed")
    assert validate_run(root / run_id, require_finished=True).is_finished
    sha = _git(git_repo, "rev-parse", "HEAD")
    append_event(root, run_id, "commit", {"commit_sha": sha, "relation": "authored"})
    append_event(root, run_id, "commit", {"commit_sha": sha, "relation": "referenced"})
    assert len(validate_run(root / run_id).events) == 3


def test_events_before_first_commit_are_valid(run: tuple[Path, str], git_repo: Path):
    root, run_id = run
    _append_wait(root, run_id)
    append_event(root, run_id, "finding_summary", {
        "stage_id": None, "review_id": "review-1", "review_kind": "self",
        "real": 1, "refuted": 0, "unresolved": 0,
    })
    append_event(root, run_id, "commit", {
        "commit_sha": _git(git_repo, "rev-parse", "HEAD"), "relation": "authored",
    })
    assert len(validate_run(root / run_id).events) == 3


def test_commit_writer_rejects_nonexistent_sha_without_touching_bytes(run: tuple[Path, str]):
    root, run_id = run
    before = _events_path(root, run_id).read_bytes()
    with pytest.raises(LedgerError):
        append_event(root, run_id, "commit", {
            "commit_sha": "f" * 40, "relation": "referenced",
        })
    assert _events_path(root, run_id).read_bytes() == before


def test_record_test_run_uses_wrapper_only_strong_sources(run: tuple[Path, str]):
    root, run_id = run
    record = record_test_run(
        root, run_id, suite_id="pytest-targeted-abcdef123456", suite_kind="targeted",
        duration_s=1.25, exit_status=0,
        counts={"collected": 2, "passed": 2, "failed": 0, "skipped": 0},
        trigger="final", collected_node_digest="abcdef123456",
    )
    assert record["measurement_source"] == {
        "timestamp": "system-clock", "duration": "monotonic-clock",
        "metrics": "tool-reported", "tokens": "not-applicable",
    }


def test_privacy_slug_rejects_raw_command_like_suite_id_before_append(run: tuple[Path, str]):
    root, run_id = run
    valid = dict(record_test_run(
        root, run_id, suite_id="pytest-targeted-abcdef123456", suite_kind="targeted",
        duration_s=1, exit_status=0, counts=None, trigger="unspecified",
        collected_node_digest=None,
    ))
    try:
        import jsonschema
    except ImportError:
        # Runtime validator は下の assertion で依存不在でも同じ負例を拒否する。
        pass
    else:
        invalid_schema_instance = dict(valid)
        invalid_schema_instance["suite_id"] = "pytest -k secret/test.py"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_schema_instance, load_schema())
    before = _events_path(root, run_id).read_bytes()
    with pytest.raises(DamagedRunError):
        record_test_run(
            root, run_id, suite_id="pytest -k secret/test.py", suite_kind="targeted",
            duration_s=1, exit_status=0, counts=None, trigger="unspecified",
            collected_node_digest=None,
        )
    assert _events_path(root, run_id).read_bytes() == before


def test_incomplete_start_without_publish_marker_is_classified_not_counted(root: Path):
    incomplete = root / "20260720-incomplete-aaaaaaaa"
    incomplete.mkdir()
    (incomplete / "events.jsonl").write_bytes(b"")
    report = validate_root(root)
    assert report.incomplete == (incomplete,)
    assert incomplete not in discover_runs(root)


def test_start_publishes_events_before_task_marker_on_injected_interruption(
    root: Path, monkeypatch: pytest.MonkeyPatch,
):
    fixed = datetime.now(timezone.utc)
    monkeypatch.setattr(ledger, "_utc_now", lambda: fixed)
    monkeypatch.setattr(ledger.secrets, "token_hex", lambda size: "d" * (size * 2))
    real_create = ledger._create_file_at

    def interrupt_task(parent_fd: int, name: str, payload: bytes, *, label: str) -> None:
        if name == "task.json":
            raise LedgerError("injected interruption before publish marker")
        real_create(parent_fd, name, payload, label=label)

    monkeypatch.setattr(ledger, "_create_file_at", interrupt_task)
    with pytest.raises(LedgerError, match="injected interruption"):
        start_run(
            root, slug="interrupted", objective="interrupted start", task_class=2,
            task_kind="implementation",
        )
    run_id = f"{fixed:%Y%m%d}-interrupted-{'d' * 8}"
    assert (root / run_id / "events.jsonl").read_bytes() == b""
    assert not (root / run_id / "task.json").exists()
    assert validate_root(root).incomplete == (root / run_id,)


def test_validate_root_classifies_damaged_and_unknown(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    _events_path(root, run_id).write_bytes(b"{\n")
    (root / "surprise.txt").write_text("x", encoding="utf-8")
    report = validate_root(root)
    assert [item.path.name for item in report.damaged] == [run_id]
    assert [path.name for path in report.unknown] == ["surprise.txt"]
    assert discover_runs(root) == (root / run_id,)


def test_validate_root_accepts_documented_readme(run: tuple[Path, str]):
    """root 直下の README.md は文書化 layout の一部 — unknown/damaged にしない (dogfooding 実測欠陥の回帰)。"""
    root, run_id = run
    (root / "README.md").write_text("# doc\n", encoding="utf-8")
    report = validate_root(root)
    assert report.unknown == ()
    assert report.damaged == ()
    assert [path.name for path in report.published] == [run_id]


def test_validate_root_rejects_missing_root_or_manifest(tmp_path: Path):
    with pytest.raises(LedgerError):
        validate_root(tmp_path / "missing")
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(LedgerError):
        validate_root(empty)


def test_pilot_cap_rejects_eleventh_published_run(root: Path):
    for index in range(10):
        start_run(
            root, slug=f"run-{index}", objective=f"run {index}", task_class=2,
            task_kind="implementation",
        )
    with pytest.raises(LedgerError):
        start_run(
            root, slug="run-10", objective="eleventh", task_class=2,
            task_kind="implementation",
        )


def test_pilot_age_cap_uses_manifest_clock(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    root = git_repo / "task-runs"
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(ledger, "_utc_now", lambda: start)
    init_pilot(root)
    monkeypatch.setattr(ledger, "_utc_now", lambda: start + timedelta(days=14))
    with pytest.raises(LedgerError):
        start_run(
            root, slug="late", objective="late", task_class=2,
            task_kind="implementation",
        )


@pytest.mark.parametrize(
    "namespace",
    ["campaigns", "env", "exploration", "s1-freeze", "s8b-freeze", "s6-rounds", "runs"],
)
def test_evidence_namespace_root_is_rejected(tmp_path: Path, namespace: str):
    with pytest.raises(LedgerError):
        init_pilot(tmp_path / "output" / namespace / "task-runs")


def test_task_run_namespace_root_remains_accepted(git_repo: Path):
    """M17: `_assert_safe_root` を output 全体拒否へ変異すると単独で赤。"""
    root = git_repo / "output" / "task-runs"
    init_pilot(root)
    assert validate_root(root).is_valid


def test_path_traversal_and_symlink_are_rejected(run: tuple[Path, str], tmp_path: Path):
    root, run_id = run
    with pytest.raises(LedgerError):
        append_event(root, "../escape", "wait", {"wait_kind": "tool", "duration_s": 1})
    path = _events_path(root, run_id)
    target = tmp_path / "outside"
    target.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(target)
    with pytest.raises((LedgerError, DamagedRunError)):
        validate_run(root / run_id)


def test_append_is_anchored_to_open_run_fd_during_symlink_swap(
    run: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    root, run_id = run
    outside = tmp_path / "outside-run"
    outside.mkdir()
    outside_events = outside / "events.jsonl"
    outside_events.write_bytes(b"outside\n")
    moved = root / f"{run_id}.moved"
    real_open = ledger._open_regular_at
    swapped = False

    def swap_then_open(parent_fd, name, flags, *, label, mode=0o600):
        nonlocal swapped
        if name == "events.jsonl" and not swapped:
            swapped = True
            (root / run_id).rename(moved)
            (root / run_id).symlink_to(outside, target_is_directory=True)
        return real_open(parent_fd, name, flags, label=label, mode=mode)

    monkeypatch.setattr(ledger, "_open_regular_at", swap_then_open)
    _append_wait(root, run_id)
    assert swapped
    assert outside_events.read_bytes() == b"outside\n"
    assert len(_read_events(root, moved.name)) == 1


def test_task_bom_and_non_nfc_objective_are_rejected(run: tuple[Path, str], root: Path):
    run_root, run_id = run
    task_path = run_root / run_id / "task.json"
    task_path.write_bytes(b"\xef\xbb\xbf" + task_path.read_bytes())
    with pytest.raises(DamagedRunError):
        validate_run(run_root / run_id)
    with pytest.raises(DamagedRunError):
        start_run(
            root, slug="nfc", objective="e\u0301", task_class=2,
            task_kind="implementation",
        )


@pytest.mark.parametrize(
    ("name", "corrupt"),
    [
        ("empty-line", lambda raw: raw + b"\n"),
        ("bom", lambda raw: b"\xef\xbb\xbf" + raw),
        ("nul", lambda raw: raw.replace(b"{", b"{\x00", 1)),
        ("cr", lambda raw: raw.replace(b"\n", b"\r\n", 1)),
        ("invalid-utf8", lambda raw: b"\xff" + raw),
        ("nan", lambda raw: raw.replace(b'"duration_s":0.25', b'"duration_s":NaN')),
    ],
)
def test_strict_jsonl_corruption_is_rejected(
    run: tuple[Path, str], name: str, corrupt: Callable[[bytes], bytes],
):
    del name
    root, run_id = run
    _append_wait(root, run_id)
    path = _events_path(root, run_id)
    path.write_bytes(corrupt(path.read_bytes()))
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_duplicate_json_key_and_oversized_line_are_rejected(run: tuple[Path, str]):
    root, run_id = run
    _append_wait(root, run_id)
    path = _events_path(root, run_id)
    raw = path.read_bytes().replace(b'"event":"wait"', b'"event":"wait","event":"wait"', 1)
    path.write_bytes(raw)
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)
    path.write_bytes(b'{"padding":"' + (b"x" * (16 * 1024)) + b'"}\n')
    with pytest.raises(DamagedRunError):
        validate_run(root / run_id)


def test_cli_typed_flow_and_validate_all(root: Path):
    script = _REPO / "tools" / "task_run.py"
    start = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "start", "--slug", "cli",
         "--objective", "cli flow", "--task-class", "2", "--task-kind", "implementation"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    run_id = start.stdout.strip()
    event = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "event", run_id, "wait",
         "--wait-kind", "tool", "--duration-s", "0.1"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert json.loads(event.stdout)["measurement_source"]["duration"] == "caller-supplied"
    validation = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "validate", "--all"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert run_id in json.loads(validation.stdout)["published"]


def test_selfcheck_uses_root_and_leaves_no_unknown_entries(root: Path):
    ledger.selfcheck(root)
    assert validate_root(root).unknown == ()


@pytest.mark.parametrize("failure", ["o_excl", "flock", "o_append", "fsync"])
def test_selfcheck_positive_controls_detect_required_primitive_failure(
    root: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
):
    if failure == "o_excl":
        real_create = ledger._create_file

        def no_exclusive_collision(path, payload, *, label):
            if "O_EXCL collision" in label:
                return None
            return real_create(path, payload, label=label)

        monkeypatch.setattr(ledger, "_create_file", no_exclusive_collision)
    elif failure == "flock":
        monkeypatch.setattr(ledger.fcntl, "flock", lambda *args: None)
    elif failure == "o_append":
        real_write = ledger._write_all

        def drop_append(fd, payload):
            if payload.startswith((b"a-", b"b-")):
                return None
            return real_write(fd, payload)

        monkeypatch.setattr(ledger, "_write_all", drop_append)
    else:
        monkeypatch.setattr(
            ledger.os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("injected fsync")),
        )
    with pytest.raises((LedgerError, OSError)):
        ledger.selfcheck(root)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
