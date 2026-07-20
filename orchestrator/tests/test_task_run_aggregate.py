# -*- coding: utf-8 -*-
"""task-run 集計・publish の V11〜V26 回帰。"""
from __future__ import annotations

import hashlib
import json
import fcntl
import multiprocessing
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.task_runs import (  # noqa: E402
    DamagedRunError,
    LedgerError,
    start_run,
    validate_root,
    validate_run,
)
import tools.task_runs.aggregate as aggregate_module  # noqa: E402
from tools.task_runs.aggregate import (  # noqa: E402
    RATE_DEFINITIONS,
    ReportError,
    aggregate_run,
    aggregate_runs,
    publish_report,
    render_report,
)


def _publish_while_partial(path_text: str, payload: bytes, ready) -> None:
    fd = os.open(path_text, os.O_WRONLY | os.O_APPEND)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        split = len(payload) // 2
        os.write(fd, payload[:split])
        os.fsync(fd)
        ready.set()
        time.sleep(0.25)
        os.write(fd, payload[split:])
        os.fsync(fd)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _source(duration: str, metrics: str, tokens: str = "not-applicable") -> dict[str, str]:
    return {
        "timestamp": "system-clock",
        "duration": duration,
        "metrics": metrics,
        "tokens": tokens,
    }


def _event(run_id: str, seq: int, timestamp: str, event: str, **payload: object) -> dict[str, object]:
    sources = {
        "stage_start": _source("not-applicable", "not-applicable"),
        "stage_end": _source("timestamp-delta", "not-applicable"),
        "agent_run": _source("caller-supplied", "caller-supplied", "product-reported"),
        "test_run": _source("monotonic-clock", "wrapper-observed"),
        "wait": _source("caller-supplied", "not-applicable"),
        "finding_summary": _source("not-applicable", "caller-supplied"),
        "rework": _source("caller-supplied", "not-applicable"),
        "commit": _source("not-applicable", "git-observed"),
        "task_end": _source("not-applicable", "not-applicable"),
    }
    value: dict[str, object] = {
        "schema_version": "task-run/v1",
        "task_run_id": run_id,
        "seq": seq,
        "timestamp": timestamp,
        "event": event,
        "event_id": f"{seq:016x}",
        "measurement_source": sources[event],
        "recording_duration_s": 0.01,
    }
    value.update(payload)
    return value


def _write_run(
    root: Path,
    run_id: str,
    events: list[dict[str, object]],
    *,
    started_at: str = "2026-07-01T00:00:00Z",
    task_kind: str = "implementation",
) -> Path:
    run_dir = root / run_id
    run_dir.mkdir(parents=True)
    task = {
        "schema_version": "task-run/v1",
        "task_run_id": run_id,
        "objective": "aggregate fixture",
        "task_class": 2,
        "task_kind": task_kind,
        "started_at": started_at,
        "base_commit": "a" * 40,
        "base_commit_source": "git-observed",
        "authority": "development-observation-not-evidence",
        "measurement_policy": {
            "mode": "pilot",
            "max_task_runs": 10,
            "max_days": 14,
            "writer_failure": "fail-open",
            "token_values": "actual-or-null",
            "token_estimates": "prohibited",
            "sensitive_content": "prohibited",
            "test_recording": "explicit-opt-in",
        },
    }
    (run_dir / "task.json").write_text(_canonical(task) + "\n", encoding="utf-8", newline="")
    (run_dir / "events.jsonl").write_text(
        "".join(_canonical(event) + "\n" for event in events),
        encoding="utf-8", newline="",
    )
    return run_dir


def _write_pilot(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    pilot = {
        "schema_version": "task-run/v1",
        "pilot_started_at": "2026-07-01T00:00:00Z",
        "max_task_runs": 10,
        "max_days": 14,
    }
    (root / "pilot.json").write_text(_canonical(pilot) + "\n", encoding="utf-8", newline="")


def _completed_events(run_id: str, *, task_end: bool = True) -> list[dict[str, object]]:
    events = [
        _event(run_id, 1, "2026-07-01T00:01:00Z", "stage_start", stage_id="implementation", stage="implementation"),
        _event(run_id, 2, "2026-07-01T00:15:00Z", "stage_end", stage_id="implementation", stage="implementation", outcome="completed", duration_s=840.0),
        _event(run_id, 3, "2026-07-01T00:16:00Z", "wait", wait_kind="tool", duration_s=60.0),
        _event(run_id, 4, "2026-07-01T00:16:10Z", "test_run", stage_id="implementation", suite_id="pytest-targeted-a", suite_kind="targeted", duration_s=100.0, collected=10, passed=8, failed=2, skipped=0, exit_status=1, trigger="after-change", collected_node_digest="abc123abc123"),
        _event(run_id, 5, "2026-07-01T00:16:20Z", "test_run", stage_id="implementation", suite_id="pytest-targeted-a", suite_kind="targeted", duration_s=80.0, collected=10, passed=9, failed=1, skipped=0, exit_status=1, trigger="after-failure", collected_node_digest="abc123abc123"),
        _event(run_id, 6, "2026-07-01T00:16:30Z", "test_run", stage_id="implementation", suite_id="pytest-targeted-a", suite_kind="targeted", duration_s=2.0, collected=None, passed=None, failed=None, skipped=None, exit_status=5, trigger="unspecified", collected_node_digest="abc123abc123"),
        _event(run_id, 7, "2026-07-01T00:16:40Z", "test_run", stage_id="implementation", suite_id="pytest-targeted-a", suite_kind="targeted", duration_s=90.0, collected=10, passed=10, failed=0, skipped=0, exit_status=0, trigger="after-failure", collected_node_digest="abc123abc123"),
        _event(run_id, 8, "2026-07-01T00:17:00Z", "test_run", stage_id=None, suite_id="pytest-targeted-b", suite_kind="full", duration_s=10.0, collected=1, passed=0, failed=1, skipped=0, exit_status=1, trigger="final", collected_node_digest=None),
        _event(run_id, 9, "2026-07-01T00:17:10Z", "agent_run", stage_id="implementation", agent_run_id="agent-1", product="codex", model="gpt-5", reasoning="high", role="author", scope=None, status="completed", duration_s=300.0, tokens={"input_tokens": 100, "output_tokens": 20, "cached_tokens": 10, "total_tokens": 120}),
        _event(run_id, 10, "2026-07-01T00:17:20Z", "finding_summary", stage_id="implementation", review_id="review-1", review_kind="independent", real=2, refuted=1, unresolved=3),
        _event(run_id, 11, "2026-07-01T00:17:30Z", "rework", stage_id="implementation", rework_id="rework-1", cause="test-failure", duration_s=30.0),
    ]
    if task_end:
        events.append(_event(run_id, 12, "2026-07-01T00:20:00Z", "task_end", outcome="completed"))
    return events


@pytest.fixture
def healthy_root(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "task-runs"
    _write_pilot(root)
    run_id = "20260701-manual-aaaaaaaa"
    run_dir = _write_run(root, run_id, _completed_events(run_id))
    return root, run_dir


def test_hand_calculated_fixture_exact_values(healthy_root: tuple[Path, Path]):
    _, run_dir = healthy_root
    result = aggregate_run(validate_run(run_dir))
    assert result["lead_time_s"] == 1200.0
    assert result["recorded_stage_time_s"] == 840.0
    assert result["active_time_s"] == 840.0
    assert result["wait_time_s"] == 60.0
    assert result["unclassified_time_s"] == 300.0
    assert result["unclassified_rate"] == 0.25
    assert result["test_duration_s"] == 282.0
    assert result["test_time_ratio"] == 282.0 / 840.0
    assert result["operation_count"] == 12
    assert result["recording_overhead_s"] == 0.12
    assert result["findings"] == {"real": 2, "refuted": 1, "unresolved": 3}
    assert result["finding_effective_rate"] == 2 / 3


def test_red_green_is_rc1_only_and_digest_aware(healthy_root: tuple[Path, Path]):
    _, run_dir = healthy_root
    outcomes = aggregate_run(validate_run(run_dir))["test_outcomes"]
    assert outcomes == {
        "red_to_green_cycles": 1,
        "open_red": 1,
        "green_runs": 1,
        "red_runs": 3,
        "infra_runs": 1,
        "digest_missing_pairings": 0,
    }


def test_negative_unclassified_is_not_clamped_and_rate_is_null(tmp_path: Path):
    root = tmp_path / "root"
    run_id = "20260701-negative-bbbbbbbb"
    events = [
        _event(run_id, 1, "2026-07-01T00:00:00Z", "stage_start", stage_id="s", stage="test"),
        _event(run_id, 2, "2026-07-01T00:01:40Z", "stage_end", stage_id="s", stage="test", outcome="completed", duration_s=100.0),
        _event(run_id, 3, "2026-07-01T00:01:50Z", "wait", wait_kind="tool", duration_s=20.0),
        _event(run_id, 4, "2026-07-01T00:01:50Z", "task_end", outcome="completed"),
    ]
    result = aggregate_run(validate_run(_write_run(root, run_id, events)))
    assert result["lead_time_s"] == 110.0
    assert result["unclassified_time_s"] == -10.0
    assert result["time_inconsistency"] is True
    assert result["unclassified_rate"] is None


def test_zero_denominators_are_null_and_rate_definitions_are_fixed(tmp_path: Path):
    root = tmp_path / "root"
    run_id = "20260701-empty-cccccccc"
    result = aggregate_run(validate_run(_write_run(root, run_id, [])))
    missing = result["missingness"]
    assert result["test_time_ratio"] is None
    assert result["finding_effective_rate"] is None
    assert missing["stage_id"]["rate"] is None
    assert missing["test_count_fields"]["rate"] is None
    assert missing["token_fields"]["rate"] is None
    assert missing["trigger_unspecified"]["rate"] is None
    assert len(RATE_DEFINITIONS) >= 8


def test_right_censored_is_separate_and_single_completed_has_no_comparison(tmp_path: Path):
    root = tmp_path / "root"
    completed_id = "20260701-done-dddddddd"
    censored_id = "20260701-open-eeeeeeee"
    completed = validate_run(_write_run(root, completed_id, _completed_events(completed_id)))
    censored_events = [_event(censored_id, 1, "2026-07-01T00:02:00Z", "wait", wait_kind="user", duration_s=120.0)]
    censored = validate_run(_write_run(root, censored_id, censored_events))
    result = aggregate_runs((completed, censored))
    layer = result["task_kind_layers"][0]
    assert layer["completed_count"] == 1
    assert layer["right_censored_count"] == 1
    assert layer["comparison"] is None
    open_run = next(run for run in result["runs"] if not run["is_finished"])
    assert open_run["right_censored_lower_bound_s"] == 120.0
    assert open_run["lead_time_s"] is None


def test_comparison_and_token_sums_never_cross_task_kind(tmp_path: Path):
    root = tmp_path / "root"
    first_id = "20260701-first-11111111"
    second_id = "20260701-second-22222222"
    audit_id = "20260701-audit-33333333"
    runs = (
        validate_run(_write_run(root, first_id, _completed_events(first_id))),
        validate_run(_write_run(root, second_id, _completed_events(second_id))),
        validate_run(_write_run(root, audit_id, _completed_events(audit_id), task_kind="audit-review")),
    )
    result = aggregate_runs(runs)
    layers = {layer["task_kind"]: layer for layer in result["task_kind_layers"]}
    assert layers["implementation"]["comparison"]["mean_lead_time_s"] == 1200.0
    assert layers["audit-review"]["comparison"] is None
    cohorts = result["token_cohorts"]
    assert len(cohorts) == 2
    implementation = next(c for c in cohorts if c["task_kind"] == "implementation")
    audit = next(c for c in cohorts if c["task_kind"] == "audit-review")
    assert implementation["fields"]["total_tokens"]["sum"] == 240
    assert audit["fields"]["total_tokens"]["sum"] == 120


def test_render_is_deterministic_and_contains_only_observation_tables(healthy_root: tuple[Path, Path]):
    _, run_dir = healthy_root
    run = validate_run(run_dir)
    first = render_report((run,))
    second = render_report((run,))
    assert first == second
    text = first.decode("utf-8")
    assert "記録された event のみ" in text
    assert "非排他的" in text
    assert "recording_overhead_s" in text
    assert "final_seq" in text
    assert "token/commit" not in text
    assert "行数/token" not in text


def test_publish_binds_hashes_and_refuses_overwrite(healthy_root: tuple[Path, Path]):
    root, run_dir = healthy_root
    destination = root / "reports" / "pilot.md"
    task_hash = hashlib.sha256((run_dir / "task.json").read_bytes()).hexdigest()
    event_hash = hashlib.sha256((run_dir / "events.jsonl").read_bytes()).hexdigest()
    assert publish_report(root, destination) == destination
    text = destination.read_text(encoding="utf-8")
    assert task_hash in text
    assert event_hash in text
    assert "| `20260701-manual-aaaaaaaa` | 12 |" in text
    before = destination.read_bytes()
    with pytest.raises(ReportError, match="上書きしない"):
        publish_report(root, destination)
    assert destination.read_bytes() == before


def test_publish_waits_for_locked_partial_append_and_validates_same_fd(tmp_path: Path):
    root = tmp_path / "task-runs"
    _write_pilot(root)
    run_id = "20260701-partial-11111111"
    run_dir = _write_run(root, run_id, [])
    event = _event(
        run_id, 1, "2026-07-01T00:00:01Z", "wait",
        wait_kind="tool", duration_s=1.0,
    )
    payload = (_canonical(event) + "\n").encode("utf-8")
    ready = multiprocessing.get_context("fork").Event()
    process = multiprocessing.get_context("fork").Process(
        target=_publish_while_partial,
        args=(str(run_dir / "events.jsonl"), payload, ready),
    )
    process.start()
    assert ready.wait(5)
    destination = root / "reports" / "cohort.md"
    assert publish_report(root, destination) == destination
    process.join(5)
    assert process.exitcode == 0
    assert "healthy_runs: 1" in destination.read_text(encoding="utf-8")


def test_manifest_hashes_stay_bound_when_paths_are_replaced_after_validation(
    healthy_root: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
):
    root, run_dir = healthy_root
    original_task_hash = hashlib.sha256((run_dir / "task.json").read_bytes()).hexdigest()
    original_event_hash = hashlib.sha256((run_dir / "events.jsonl").read_bytes()).hexdigest()
    real_manifest = aggregate_module._manifest

    def replace_paths(run):
        manifest = real_manifest(run)
        (run.path / "task.json").rename(run.path / "task.original")
        (run.path / "events.jsonl").rename(run.path / "events.original")
        (run.path / "task.json").write_bytes(b"replacement-task\n")
        (run.path / "events.jsonl").write_bytes(b"replacement-events\n")
        return manifest

    monkeypatch.setattr(aggregate_module, "_manifest", replace_paths)
    destination = root / "reports" / "binding.md"
    publish_report(root, destination)
    text = destination.read_text(encoding="utf-8")
    assert original_task_hash in text
    assert original_event_hash in text
    assert hashlib.sha256(b"replacement-task\n").hexdigest() not in text


def test_diagnostic_persists_only_closed_reason_codes_and_safe_entry_labels(
    healthy_root: tuple[Path, Path],
):
    root, _ = healthy_root
    damaged_id = "20260701-damaged-22222222"
    damaged = _write_run(root, damaged_id, _completed_events(damaged_id))
    (damaged / "events.jsonl").write_text(
        '{"suite_id":"TOP_SECRET"}\n', encoding="utf-8",
    )
    unsafe_name = "TOP_SECRET|unknown"
    (root / unsafe_name).write_text("x", encoding="utf-8")
    destination = root / "reports" / "diagnostic-safe.md"
    publish_report(root, destination, diagnostic=True)
    text = destination.read_text(encoding="utf-8")
    assert "TOP_SECRET" not in text
    assert "invalid-run" in text
    assert "unknown-root-entry" in text
    assert "sha256-" in text


def test_aggregate_rejects_nonfinite_ratio_output():
    with pytest.raises(ReportError, match="non-finite"):
        aggregate_module._ratio(1e308, 1e-308)


def test_report_always_discloses_published_cap_state(tmp_path: Path):
    root = tmp_path / "task-runs"
    _write_pilot(root)
    for index in range(11):
        run_id = f"20260701-cap-{index}-{index:08x}"
        _write_run(root, run_id, [])
    report = validate_root(root)
    assert report.published_run_count == 11
    assert report.cap_exceeded is True
    assert report.cap_excess == 1
    destination = root / "reports" / "over-cap.md"
    publish_report(root, destination)
    text = destination.read_text(encoding="utf-8")
    assert "published_runs: 11" in text
    assert "pilot_max_task_runs: 10" in text
    assert "cap_exceeded: yes" in text
    assert "cap_excess: 1" in text


def test_final_publish_creates_marker_and_freezes_new_start(healthy_root: tuple[Path, Path]):
    root, _ = healthy_root
    destination = root / "reports" / "final.md"
    assert publish_report(root, destination, final=True) == destination
    marker = root / "pilot-final.json"
    marker_before = marker.read_bytes()
    assert json.loads(marker_before)["final_report"] == "final.md"
    with pytest.raises(LedgerError, match="凍結済み"):
        start_run(
            root, slug="after-final", objective="must reject", task_class=2,
            task_kind="implementation",
        )
    assert marker.read_bytes() == marker_before


def test_damaged_run_default_refuses_without_output_and_diagnostic_is_explicit(healthy_root: tuple[Path, Path]):
    root, run_dir = healthy_root
    damaged_id = "20260701-damaged-ffffffff"
    damaged = _write_run(root, damaged_id, _completed_events(damaged_id))
    raw = (damaged / "events.jsonl").read_bytes()
    (damaged / "events.jsonl").write_bytes(raw[:-1])
    with pytest.raises(DamagedRunError):
        validate_run(damaged)

    normal = root / "reports" / "normal.md"
    with pytest.raises(ReportError, match="report を生成しない"):
        publish_report(root, normal)
    assert not normal.exists()

    diagnostic = root / "reports" / "diagnostic.md"
    publish_report(root, diagnostic, diagnostic=True)
    text = diagnostic.read_text(encoding="utf-8")
    assert text.startswith("# 不完全")
    assert damaged_id in text
    assert "20260701-manual-aaaaaaaa" in text
    assert "healthy_runs: 1" in text


def test_cli_uses_create_only_publish_and_nonzero_on_damage(healthy_root: tuple[Path, Path]):
    root, _ = healthy_root
    destination = root / "reports" / "cli.md"
    result = subprocess.run(
        [
            sys.executable, str(_REPO / "tools" / "task_run_report.py"), "--final",
            str(root), str(destination),
        ],
        cwd=_REPO, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert destination.exists()
    assert (root / "pilot-final.json").exists()
    again = subprocess.run(
        [sys.executable, str(_REPO / "tools" / "task_run_report.py"), str(root), str(destination)],
        cwd=_REPO, capture_output=True, text=True,
    )
    assert again.returncode != 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
