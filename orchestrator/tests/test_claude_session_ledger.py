# -*- coding: utf-8 -*-
"""tools/claude_session_ledger.py の合成 transcript による回帰テスト。"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_LEDGER = _ROOT / "tools" / "claude_session_ledger.py"


def _load_ledger(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    original = sys.dont_write_bytecode
    try:
        # loader は module 本文より前に pyc を判断するため、呼出側で抑止する。
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = original
    return module


LEDGER = _load_ledger(_LEDGER, "claude_session_ledger_under_test")


def _usage(
    *, cache_read: int, cache_creation: int, input_tokens: int, output: int
) -> dict[str, int]:
    return {
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_creation,
        "input_tokens": input_tokens,
        "output_tokens": output,
    }


def _assistant(
    *,
    request_id: str | None = "req-1",
    message_id: str = "msg-1",
    timestamp: str | None = "2026-01-10T00:00:00Z",
    cwd: str | None = "/synthetic/izanagi",
    usage: Any = None,
    model: str = "claude-synthetic-test",
    tools: tuple[str, ...] = (),
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "id": message_id,
        "type": "message",
        "model": model,
        "content": [
            {
                "type": "tool_use",
                "id": tool_id,
                "name": "SyntheticTool",
                "input": {"value": tool_id},
            }
            for tool_id in tools
        ],
    }
    if usage is not None:
        message["usage"] = usage
    record: dict[str, Any] = {"type": "assistant", "message": message}
    if request_id is not None:
        record["requestId"] = request_id
    if timestamp is not None:
        record["timestamp"] = timestamp
    if cwd is not None:
        record["cwd"] = cwd
    return record


def _write_jsonl(
    projects_root: Path,
    slug: str,
    relative: str,
    records: list[Any],
    *,
    mtime: float = 1_768_003_200.0,
) -> Path:
    path = projects_root / slug / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"".join(
            (
                record
                if isinstance(record, bytes)
                else (
                    json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                    + "\n"
                ).encode("utf-8")
            )
            for record in records
        )
    )
    os.utime(path, (mtime, mtime))
    return path


def _run_json(
    capsys: pytest.CaptureFixture[str], projects_root: Path, *args: str
) -> tuple[int, dict[str, Any], str]:
    rc = LEDGER.main(["--projects-root", str(projects_root), "--json", *args])
    captured = capsys.readouterr()
    return rc, json.loads(captured.out), captured.err


def _run_text(
    capsys: pytest.CaptureFixture[str], projects_root: Path, *args: str
) -> tuple[int, str, str]:
    rc = LEDGER.main(["--projects-root", str(projects_root), *args])
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def _tree_snapshot(root: Path) -> dict[str, tuple[Any, ...]]:
    snapshot: dict[str, tuple[Any, ...]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        stat = path.lstat()
        if path.is_symlink():
            snapshot[relative] = ("symlink", os.readlink(path), stat.st_mtime_ns)
        elif path.is_dir():
            snapshot[relative] = ("directory", stat.st_mode, stat.st_mtime_ns)
        else:
            snapshot[relative] = (
                "file",
                stat.st_mode,
                stat.st_mtime_ns,
                path.read_bytes(),
            )
    return snapshot


def test_request_dedupe_uses_final_usage_and_all_three_input_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "root.jsonl",
        [
            _assistant(
                request_id="req-split",
                message_id="msg-split",
                timestamp="2026-01-10T00:00:01Z",
                usage=_usage(
                    cache_read=10, cache_creation=20, input_tokens=30, output=1
                ),
                tools=("tool-1",),
            ),
            _assistant(
                # requestId が欠けた split record も message.id alias で同じ応答になる。
                request_id=None,
                message_id="msg-split",
                timestamp="2026-01-10T00:00:02Z",
                usage=_usage(
                    cache_read=10,
                    cache_creation=20,
                    input_tokens=30,
                    output=247,
                ),
                tools=("tool-2",),
            ),
            _assistant(
                request_id=None,
                message_id="msg-fallback",
                timestamp="2026-01-10T00:00:03Z",
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                ),
            ),
        ],
    )

    rc, report, stderr = _run_json(capsys, projects, "--strict")

    assert rc == 0
    assert stderr == ""
    root = report["root"]
    assert root["model_calls"] == 2
    assert root["tool_calls"] == 2
    assert root["cache_read_input_tokens"] == 11
    assert root["cache_creation_input_tokens"] == 22
    assert root["input_tokens"] == 33
    assert root["raw_input_tokens"] == 11 + 22 + 33
    assert root["output_tokens"] == 247 + 4
    assert root["event_timestamp_model_calls"] == 2
    assert root["mtime_fallback_model_calls"] == 0
    assert report["population"]["request_identity"] == (
        "resolved_file_provenance_with_requestId_message.id_aliases"
    )


def test_synthetic_zero_usage_is_excluded_and_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "rate-limit.jsonl",
        [
            _assistant(
                request_id="rate-limit",
                model="<synthetic>",
                usage=_usage(
                    cache_read=0, cache_creation=0, input_tokens=0, output=0
                ),
            ),
            _assistant(
                request_id="real",
                message_id="real-message",
                usage=_usage(
                    cache_read=7, cache_creation=8, input_tokens=9, output=10
                ),
            ),
        ],
    )

    rc, report, _ = _run_json(capsys, projects, "--strict")

    assert rc == 0
    assert report["root"]["model_calls"] == 1
    assert report["root"]["raw_input_tokens"] == 24
    assert report["root"]["synthetic_zero_usage_excluded"] == 1


def test_recursive_sidechains_are_separate_and_only_explicitly_combined(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "root.jsonl",
        [
            _assistant(
                request_id="root-call",
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                ),
            )
        ],
    )
    _write_jsonl(
        projects,
        "project-a",
        "session/subagents/nested/agent.jsonl",
        [
            _assistant(
                request_id="side-call",
                message_id="side-message",
                usage=_usage(
                    cache_read=10, cache_creation=20, input_tokens=30, output=40
                ),
                tools=("side-tool-1", "side-tool-2"),
            )
        ],
    )

    rc, separate, _ = _run_json(capsys, projects, "--strict")
    assert rc == 0
    assert separate["root"]["model_calls"] == 1
    assert separate["root"]["raw_input_tokens"] == 6
    assert separate["sidechains"]["model_calls"] == 1
    assert separate["sidechains"]["tool_calls"] == 2
    assert separate["sidechains"]["raw_input_tokens"] == 60
    assert "combined" not in separate

    rc, included, _ = _run_json(
        capsys, projects, "--strict", "--include-sidechains"
    )
    assert rc == 0
    assert included["combined"]["model_calls"] == 2
    assert included["combined"]["raw_input_tokens"] == 66


def test_default_file_budget_is_balanced_before_unused_quota_is_reassigned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    for index in range(30):
        _write_jsonl(
            projects,
            "project-a",
            f"root-{index:02d}.jsonl",
            [
                _assistant(
                    request_id=f"root-{index}",
                    message_id=f"root-message-{index}",
                    usage=_usage(
                        cache_read=1, cache_creation=0, input_tokens=0, output=1
                    ),
                )
            ],
        )
    for index in range(4):
        _write_jsonl(
            projects,
            "project-a",
            f"session/subagents/agent-{index:02d}.jsonl",
            [
                _assistant(
                    request_id=f"side-{index}",
                    message_id=f"side-message-{index}",
                    usage=_usage(
                        cache_read=0, cache_creation=1, input_tokens=0, output=1
                    ),
                )
            ],
        )

    rc, report, stderr = _run_json(capsys, projects, "--strict")

    assert rc == 0
    assert stderr == ""
    assert report["population"]["max_files"] == 25
    assert report["population"]["files_scanned"] == 25
    assert report["population"]["limit_reached"] is True
    assert report["population"]["file_allocation"] == {
        "policy": "balanced_root_sidechain_with_unused_quota_reassigned",
        "root_base_quota": 13,
        "sidechain_base_quota": 12,
        "root_selected": 21,
        "sidechain_selected": 4,
    }
    assert report["root"]["model_calls"] == 21
    assert report["sidechains"]["model_calls"] == 4


@pytest.mark.parametrize("collision_kind", ["requestId", "message.id"])
def test_raw_ids_do_not_merge_across_file_or_sidechain_provenance(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collision_kind: str,
) -> None:
    projects = tmp_path / "projects"
    common_request = "collision" if collision_kind == "requestId" else "root-request"
    common_message = "collision" if collision_kind == "message.id" else "root-message"
    _write_jsonl(
        projects,
        "project-a",
        "root.jsonl",
        [
            _assistant(
                request_id=common_request,
                message_id=common_message,
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                ),
            )
        ],
    )
    _write_jsonl(
        projects,
        "project-a",
        "session/subagents/agent.jsonl",
        [
            _assistant(
                request_id=("collision" if collision_kind == "requestId" else "side-request"),
                message_id=("collision" if collision_kind == "message.id" else "side-message"),
                usage=_usage(
                    cache_read=10, cache_creation=20, input_tokens=30, output=40
                ),
            )
        ],
    )

    rc, report, stderr = _run_json(capsys, projects)

    category = (
        "request_id_collision" if collision_kind == "requestId" else "message_id_collision"
    )
    assert rc == 2
    assert category in stderr
    assert len(report["issues"][category]) == 1
    assert report["root"]["model_calls"] == 0
    assert report["sidechains"]["model_calls"] == 0


def test_conflicting_alias_graph_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "conflict.jsonl",
        [
            _assistant(
                request_id="request-a",
                message_id="message-a",
                usage=_usage(
                    cache_read=1, cache_creation=1, input_tokens=1, output=1
                ),
            ),
            _assistant(
                request_id="request-b",
                message_id="message-b",
                timestamp="2026-01-10T00:00:01Z",
                usage=_usage(
                    cache_read=2, cache_creation=2, input_tokens=2, output=2
                ),
            ),
            _assistant(
                request_id="request-a",
                message_id="message-b",
                timestamp="2026-01-10T00:00:02Z",
                usage=_usage(
                    cache_read=3, cache_creation=3, input_tokens=3, output=3
                ),
            ),
        ],
    )

    rc, report, stderr = _run_json(capsys, projects)

    assert rc == 2
    assert "alias_conflict" in stderr
    assert len(report["issues"]["alias_conflict"]) == 1
    assert report["root"]["model_calls"] == 0


def test_timestamp_reversal_is_reported_and_chronological_terminal_is_used(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    usage = _usage(cache_read=1, cache_creation=2, input_tokens=3, output=4)
    _write_jsonl(
        projects,
        "project-a",
        "reversed.jsonl",
        [
            _assistant(
                request_id="reversed",
                message_id="reversed-message",
                timestamp="2026-01-10T00:00:02Z",
                usage=usage,
            ),
            _assistant(
                request_id="reversed",
                message_id="reversed-message",
                timestamp="2026-01-10T00:00:01Z",
                usage=usage,
            ),
        ],
    )

    rc, report, stderr = _run_json(capsys, projects, "--strict")

    assert rc == 2
    assert "event_timestamp_out_of_order" in stderr
    assert report["root"]["model_calls"] == 1
    assert report["root"]["raw_input_tokens"] == 6
    assert report["root"]["output_tokens"] == 4


def test_terminal_assistant_record_without_usage_is_not_silently_aggregated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "missing-terminal-usage.jsonl",
        [
            _assistant(
                request_id="incomplete",
                message_id="incomplete-message",
                timestamp="2026-01-10T00:00:01Z",
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                ),
            ),
            _assistant(
                request_id="incomplete",
                message_id="incomplete-message",
                timestamp="2026-01-10T00:00:02Z",
                usage=None,
                tools=("terminal-tool",),
            ),
        ],
    )

    rc, report, stderr = _run_json(capsys, projects, "--strict")

    assert rc == 2
    assert "terminal_usage_missing" in stderr
    assert report["root"]["model_calls"] == 0
    assert report["root"]["tool_calls"] == 0


def test_partially_missing_event_timestamps_are_rejected_as_incomplete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "partial-timestamps.jsonl",
        [
            _assistant(
                request_id="partial",
                message_id="partial-message",
                timestamp="2026-01-10T00:00:01Z",
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                ),
            ),
            _assistant(
                request_id="partial",
                message_id="partial-message",
                timestamp=None,
                usage=_usage(
                    cache_read=5, cache_creation=6, input_tokens=7, output=8
                ),
            ),
        ],
    )

    rc, report, stderr = _run_json(capsys, projects, "--strict")

    assert rc == 2
    assert "incomplete_event_timestamps" in stderr
    assert report["root"]["model_calls"] == 0
    assert report["root"]["mtime_fallback_model_calls"] == 0


def test_descending_terminal_usage_is_used_instead_of_fieldwise_maximum(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "descending.jsonl",
        [
            _assistant(
                request_id="descending",
                message_id="descending-message",
                timestamp="2026-01-10T00:00:01Z",
                usage=_usage(
                    cache_read=100, cache_creation=200, input_tokens=300, output=400
                ),
            ),
            _assistant(
                request_id="descending",
                message_id="descending-message",
                timestamp="2026-01-10T00:00:02Z",
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                ),
            ),
        ],
    )

    rc, report, stderr = _run_json(capsys, projects)
    assert rc == 0
    assert stderr == ""
    assert report["root"]["raw_input_tokens"] == 6
    assert report["root"]["output_tokens"] == 4
    assert len(report["issues"]["usage_final_below_prior_max"]) == 1

    rc, strict_report, stderr = _run_json(capsys, projects, "--strict")
    assert rc == 2
    assert "usage_final_below_prior_max" in stderr
    assert strict_report["root"] == report["root"]


def test_window_uses_each_event_timestamp_then_reports_mtime_fallback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "crosses-window.jsonl",
        [
            _assistant(
                request_id="before",
                timestamp="2026-01-01T00:00:00Z",
                usage=_usage(
                    cache_read=100, cache_creation=100, input_tokens=100, output=1
                ),
            ),
            _assistant(
                request_id="inside",
                message_id="inside-message",
                timestamp="2026-01-10T00:00:00Z",
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                ),
            ),
            _assistant(
                request_id="at-until",
                message_id="until-message",
                timestamp="2026-01-15T00:00:00Z",
                usage=_usage(
                    cache_read=200, cache_creation=200, input_tokens=200, output=2
                ),
            ),
        ],
        # file mtime は窓外でも、event timestamp がある request では使わない。
        mtime=1_768_435_200.0,
    )
    _write_jsonl(
        projects,
        "project-a",
        "mtime-only.jsonl",
        [
            _assistant(
                request_id="mtime",
                message_id="mtime-message",
                timestamp=None,
                usage=_usage(
                    cache_read=5, cache_creation=6, input_tokens=7, output=8
                ),
            )
        ],
        mtime=datetime_timestamp("2026-01-12T00:00:00+00:00"),
    )

    rc, report, _ = _run_json(
        capsys,
        projects,
        "--since",
        "2026-01-05T00:00:00Z",
        "--until",
        "2026-01-15T00:00:00Z",
        "--strict",
    )

    assert rc == 0
    root = report["root"]
    assert root["model_calls"] == 2
    assert root["raw_input_tokens"] == 6 + 18
    assert root["output_tokens"] == 4 + 8
    assert root["event_timestamp_model_calls"] == 1
    assert root["mtime_fallback_model_calls"] == 1
    assert report["population"]["max_files"] == LEDGER.DEFAULT_MAX_FILES
    assert report["population"]["time_window"] == {
        "basis": "event_timestamp_then_file_mtime",
        "since_inclusive": "2026-01-05T00:00:00+00:00",
        "until_exclusive": "2026-01-15T00:00:00+00:00",
    }


def datetime_timestamp(value: str) -> float:
    from datetime import datetime

    return datetime.fromisoformat(value).timestamp()


def test_population_filters_corruption_and_file_limit_are_visible(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "selected-project",
        "a.jsonl",
        [
            b"not-json\n",
            _assistant(
                request_id="selected",
                message_id="selected-message",
                cwd="/wanted/checkout",
                usage=_usage(
                    cache_read=1, cache_creation=1, input_tokens=1, output=1
                ),
            ),
        ],
    )
    _write_jsonl(
        projects,
        "selected-project",
        "b.jsonl",
        [
            _assistant(
                request_id="wrong-cwd",
                message_id="wrong-cwd-message",
                cwd="/other/checkout",
                usage=_usage(
                    cache_read=9, cache_creation=9, input_tokens=9, output=9
                ),
            )
        ],
    )
    _write_jsonl(
        projects,
        "selected-project",
        "c.jsonl",
        [
            _assistant(
                request_id="beyond-limit",
                message_id="beyond-limit-message",
                cwd="/wanted/checkout",
                usage=_usage(
                    cache_read=8, cache_creation=8, input_tokens=8, output=8
                ),
            )
        ],
    )
    _write_jsonl(
        projects,
        "other-project",
        "ignored.jsonl",
        [
            _assistant(
                request_id="wrong-project",
                message_id="wrong-project-message",
                cwd="/wanted/checkout",
                usage=_usage(
                    cache_read=7, cache_creation=7, input_tokens=7, output=7
                ),
            )
        ],
    )

    rc, report, _ = _run_json(
        capsys,
        projects,
        "--project",
        "selected-project",
        "--cwd-contains",
        "/wanted/",
        "--max-files",
        "2",
    )

    assert rc == 0
    population = report["population"]
    assert population["projects_root"] == str(projects.resolve())
    assert population["project_filters"] == ["selected-project"]
    assert population["cwd_contains_filters"] == ["/wanted/"]
    assert population["files_scanned"] == 2
    assert population["limit_reached"] is True
    assert population["files_with_malformed_json"] == 1
    assert population["malformed_json_lines"] == 1
    assert len(report["issues"]["malformed_json"]) == 1
    assert report["root"]["model_calls"] == 1
    assert report["root"]["raw_input_tokens"] == 3

    rc, repeated, _ = _run_json(
        capsys,
        projects,
        "--project",
        "selected-project",
        "--cwd-contains",
        "/wanted/",
        "--max-files",
        "2",
    )
    assert rc == 0
    assert repeated == report


def test_unreadable_file_is_counted_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    projects = tmp_path / "projects"
    unreadable = _write_jsonl(
        projects,
        "project-a",
        "unreadable.jsonl",
        [
            _assistant(
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                )
            )
        ],
    )
    original_open = Path.open

    def refusing_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == unreadable:
            raise PermissionError("synthetic refusal")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", refusing_open)
    rc, report, _ = _run_json(capsys, projects)

    assert rc == 0
    assert report["population"]["files_scanned"] == 1
    assert report["population"]["files_unreadable"] == 1
    assert len(report["issues"]["unreadable_file"]) == 1


def test_default_text_report_is_an_exact_population_and_metric_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    projects = tmp_path / "projects"
    root = _write_jsonl(
        projects,
        "selected-project",
        "a-root.jsonl",
        [
            _assistant(
                request_id="root",
                message_id="root-message",
                cwd="/wanted/checkout",
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                ),
            )
        ],
    )
    unreadable = _write_jsonl(
        projects,
        "selected-project",
        "z-unreadable.jsonl",
        [
            _assistant(
                request_id="unreadable",
                message_id="unreadable-message",
                cwd="/wanted/checkout",
                usage=_usage(
                    cache_read=7, cache_creation=8, input_tokens=9, output=10
                ),
            )
        ],
    )
    sidechain = _write_jsonl(
        projects,
        "selected-project",
        "session/subagents/agent.jsonl",
        [
            _assistant(
                request_id="side",
                message_id="side-message",
                cwd="/wanted/checkout",
                usage=_usage(
                    cache_read=10, cache_creation=20, input_tokens=30, output=40
                ),
                tools=("side-tool-1", "side-tool-2"),
            )
        ],
    )
    original_open = Path.open

    def refusing_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == unreadable.resolve():
            raise PermissionError("synthetic refusal")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", refusing_open)
    rc, text, stderr = _run_text(
        capsys,
        projects,
        "--project",
        "selected-project",
        "--cwd-contains",
        "/wanted/",
        "--since",
        "2026-01-01T00:00:00Z",
        "--until",
        "2026-02-01T00:00:00Z",
        "--max-files",
        "3",
    )

    expected = f"""Claude session ledger (read-only)
母集団:
  projects root: {projects.resolve()}
  project filter (OR): ['selected-project']
  cwd filter (OR): ['/wanted/']
  時間窓: [2026-01-01T00:00:00+00:00, 2026-02-01T00:00:00+00:00)
  時間判定: record の event timestamp を優先し、全欠損 request だけ file mtime へ退避
  走査 file: 3 / 上限 3 (打切り=no)
  file 配分 (root/sidechain): 2/1 (基準枠 2/1; 未使用枠は再配分)
  読取 bytes: {root.stat().st_size + sidechain.stat().st_size} / 上限 536870912
  読めなかった file: 1
  読めなかった directory: 0
  壊れた JSONL file/行: 0/0
root:
  model call (応答数): 1
  tool 呼び出し数: 0
  生入力トークン: 6
    cache read 入力トークン: 1
    cache creation 入力トークン: 2
    通常入力トークン (input_tokens): 3
  出力トークン: 4
  時間判定 (event timestamp/mtime): 1/0
  除外した synthetic 全ゼロ応答: 0
  compaction 境界: 0
sidechain:
  model call (応答数): 1
  tool 呼び出し数: 2
  生入力トークン: 60
    cache read 入力トークン: 10
    cache creation 入力トークン: 20
    通常入力トークン (input_tokens): 30
  出力トークン: 40
  時間判定 (event timestamp/mtime): 1/0
  除外した synthetic 全ゼロ応答: 0
  compaction 境界: 0
context 曲線: compaction 境界を跨ぐ単調曲線は算出しない
ISSUE\tunreadable_file\t{unreadable.resolve()}: PermissionError
"""
    assert rc == 0
    assert stderr == ""
    assert text == expected


def test_compaction_boundaries_are_reported_without_a_monotonic_curve(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "compacted.jsonl",
        [
            _assistant(
                request_id="before-compact",
                timestamp="2026-01-10T00:00:00Z",
                usage=_usage(
                    cache_read=100, cache_creation=1, input_tokens=1, output=1
                ),
            ),
            {
                "type": "system",
                "subtype": "compact_boundary",
                "timestamp": "2026-01-10T00:01:00Z",
                "cwd": "/synthetic/izanagi",
            },
            _assistant(
                request_id="after-compact",
                message_id="after-message",
                timestamp="2026-01-10T00:02:00Z",
                usage=_usage(
                    cache_read=20, cache_creation=2, input_tokens=2, output=2
                ),
            ),
        ],
    )

    rc, report, _ = _run_json(capsys, projects, "--strict")
    assert rc == 0
    assert report["root"]["compaction_boundaries"] == 1
    assert "context_curve" not in report["root"]

    rc = LEDGER.main(["--projects-root", str(projects)])
    text = capsys.readouterr().out
    assert rc == 0
    assert "compaction 境界: 1" in text
    assert "compaction 境界を跨ぐ単調曲線は算出しない" in text
    assert "費用" not in text
    assert "課金" not in text
    assert "枠消費" not in text


def test_missing_fields_are_reported_and_strict_mode_fails_cleanly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    missing_key = _assistant(
        request_id=None,
        message_id="",
        usage=_usage(cache_read=1, cache_creation=2, input_tokens=3, output=4),
        tools=("orphan-tool",),
    )
    malformed_usage = _assistant(
        request_id="malformed-usage",
        message_id="malformed-message",
        usage={
            "cache_read_input_tokens": 1,
            "cache_creation_input_tokens": 2,
            "output_tokens": 4,
        },
    )
    _write_jsonl(
        projects,
        "project-a",
        "missing.jsonl",
        [missing_key, malformed_usage, {"type": "user"}],
    )

    rc, report, stderr = _run_json(capsys, projects, "--strict")

    assert rc == 2
    assert "missing_request_key" in stderr
    assert "malformed_usage" in stderr
    assert report["population"]["missing_request_key_records"] == 1
    assert report["population"]["malformed_usage_records"] == 1
    assert report["root"]["model_calls"] == 0


def test_missing_root_returns_a_population_report_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "does-not-exist"
    rc, report, stderr = _run_json(capsys, missing)

    assert rc == 2
    assert report["population"]["projects_root"] == str(missing.resolve())
    assert report["population"]["files_scanned"] == 0
    assert report["root"]["model_calls"] == 0
    assert report["issues"]["root_missing"] == [str(missing.resolve())]
    assert "Traceback" not in stderr


def test_default_literals_and_all_hard_limits_are_independently_pinned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()

    rc, report, stderr = _run_json(capsys, projects)

    assert rc == 0
    assert stderr == ""
    assert LEDGER.DEFAULT_PROJECTS_ROOT == "~/.claude/projects"
    assert LEDGER.DEFAULT_MAX_FILES == 25
    assert report["population"]["max_files"] == 25
    assert report["population"]["hard_limits"] == {
        "max_files": 1_000,
        "total_bytes": 512 * 1024 * 1024,
        "line_bytes": 16 * 1024 * 1024,
        "records": 1_000_000,
        "requests": 250_000,
        "tool_identities": 500_000,
        "discovery_entries": 100_000,
        "issue_details_per_category": 100,
    }
    with pytest.raises(SystemExit) as raised:
        LEDGER.main(
            ["--projects-root", str(projects), "--max-files", "1001", "--json"]
        )
    assert raised.value.code == 2
    capsys.readouterr()


@pytest.mark.parametrize(
    ("bound", "value", "records", "category"),
    [
        ("MAX_TOTAL_BYTES", 1, [b"{}\n"], "total_bytes_limit_exceeded"),
        ("MAX_LINE_BYTES", 4, [b"12345\n"], "line_too_long"),
        ("MAX_RECORDS", 1, [b"{}\n", b"{}\n"], "record_limit_exceeded"),
    ],
)
def test_stream_resource_bounds_fail_closed_before_unbounded_parsing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    bound: str,
    value: int,
    records: list[bytes],
    category: str,
) -> None:
    projects = tmp_path / "projects"
    _write_jsonl(projects, "project-a", "bounded.jsonl", records)
    monkeypatch.setattr(LEDGER, bound, value)

    rc, report, stderr = _run_json(capsys, projects)

    assert rc == 2
    assert category in stderr
    assert len(report["issues"][category]) == 1


def test_issue_detail_retention_is_hard_bounded() -> None:
    issues: dict[str, list[str]] = {}
    for index in range(LEDGER.MAX_ISSUE_DETAILS + 50):
        LEDGER._issue(issues, "malformed_json", f"line-{index}")

    assert len(issues["malformed_json"]) == LEDGER.MAX_ISSUE_DETAILS + 1
    assert issues["malformed_json"][-1] == (
        "<additional malformed_json details omitted>"
    )


def test_walk_errors_are_reported_through_onerror_and_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()

    def failing_walk(
        root: Path, *, followlinks: bool, onerror: Any
    ) -> list[tuple[str, list[str], list[str]]]:
        assert root == projects.resolve()
        assert followlinks is False
        assert onerror is not None
        error = PermissionError("synthetic scandir refusal")
        error.filename = str(projects / "denied")
        onerror(error)
        return []

    monkeypatch.setattr(LEDGER.os, "walk", failing_walk)
    rc, report, stderr = _run_json(capsys, projects)

    assert rc == 2
    assert "unreadable_directory" in stderr
    assert report["population"]["directories_unreadable"] == 1
    assert len(report["issues"]["unreadable_directory"]) == 1


@pytest.mark.parametrize(
    ("target_location", "category"),
    [("inside", "non_regular_file"), ("outside", "path_outside_root")],
)
def test_symlink_jsonl_is_rejected_as_non_regular_or_outside_declared_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target_location: str,
    category: str,
) -> None:
    projects = tmp_path / "projects"
    project = projects / "project-a"
    project.mkdir(parents=True)
    if target_location == "inside":
        target = _write_jsonl(
            projects,
            "project-a",
            "target.data",
            [
                _assistant(
                    usage=_usage(
                        cache_read=1, cache_creation=2, input_tokens=3, output=4
                    )
                )
            ],
        )
    else:
        target = tmp_path / "outside.data"
        target.write_text("{}\n", encoding="utf-8")
    (project / "linked.jsonl").symlink_to(target)

    rc, report, stderr = _run_json(capsys, projects)

    assert rc == 2
    assert category in stderr
    assert len(report["issues"][category]) == 1
    assert report["population"]["files_scanned"] == 0


def test_strict_issue_matrix_covers_every_classification(
    tmp_path: Path,
) -> None:
    expected = {
        "alias_conflict",
        "discovery_limit_exceeded",
        "event_timestamp_out_of_order",
        "incomplete_event_timestamps",
        "invalid_timestamp",
        "line_too_long",
        "malformed_json",
        "malformed_usage",
        "message_id_collision",
        "missing_cwd",
        "missing_project",
        "missing_request_key",
        "non_regular_file",
        "path_outside_root",
        "record_limit_exceeded",
        "request_id_collision",
        "request_limit_exceeded",
        "root_missing",
        "terminal_usage_missing",
        "tool_identity_limit_exceeded",
        "total_bytes_limit_exceeded",
        "unreadable_directory",
        "unreadable_file",
        "usage_final_below_prior_max",
    }
    assert LEDGER.STRICT_ISSUES == expected
    report = LEDGER._empty_report(
        projects_root=tmp_path,
        project_filters=[],
        cwd_filters=[],
        since_text=None,
        until_text=None,
        max_files=25,
    )
    for category in sorted(expected):
        report["issues"] = {category: ["synthetic issue"]}
        assert LEDGER._exit_code(report, strict=True) == 2, category
        expected_non_strict = 2 if category in LEDGER.FATAL_ISSUES else 0
        assert LEDGER._exit_code(report, strict=False) == expected_non_strict, category


def test_cli_has_no_write_destination_argument() -> None:
    options = {
        option
        for action in LEDGER._parser()._actions
        for option in action.option_strings
    }
    assert options == {
        "-h",
        "--help",
        "--projects-root",
        "--project",
        "--cwd-contains",
        "--since",
        "--until",
        "--max-files",
        "--include-sidechains",
        "--json",
        "--strict",
    }


def test_test_loader_suppresses_bytecode_before_importing_ledger(
    tmp_path: Path,
) -> None:
    isolated = tmp_path / "import-tree"
    isolated.mkdir()
    copied_ledger = shutil.copy2(_LEDGER, isolated / _LEDGER.name)
    before = _tree_snapshot(isolated)

    module = _load_ledger(copied_ledger, "claude_session_ledger_import_probe")

    assert module.DEFAULT_MAX_FILES == 25
    assert _tree_snapshot(isolated) == before
    assert not (isolated / "__pycache__").exists()


def test_read_only_run_preserves_entire_isolated_tree_and_makes_no_bytecode(
    tmp_path: Path,
) -> None:
    isolated = tmp_path / "isolated"
    projects = isolated / "projects"
    _write_jsonl(
        projects,
        "project-a",
        "readonly.jsonl",
        [
            _assistant(
                usage=_usage(
                    cache_read=1, cache_creation=2, input_tokens=3, output=4
                )
            )
        ],
    )
    copied_tools = isolated / "tools"
    copied_tools.mkdir()
    copied_ledger = shutil.copy2(_LEDGER, copied_tools / _LEDGER.name)
    before = _tree_snapshot(isolated)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            str(copied_ledger),
            "--projects-root",
            str(projects),
            "--strict",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert completed.returncode == 0, completed.stderr
    assert _tree_snapshot(isolated) == before
    assert not (copied_tools / "__pycache__").exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
