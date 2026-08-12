# -*- coding: utf-8 -*-
"""T-181 schema v2 の閉包・supervisor・裁定・集計回帰。

DW-M08 expected mutation nodes:
M1 -> test_m1_snapshot_head_pin_is_independent
M2 -> test_m2_production_golden_requires_both_routes
M3 -> test_m3_snapshot_mode_change / test_m3_symbolic_head_is_required /
      test_m3_ignored_extra_and_missing /
      test_m3_focus_artifact_directions
M4 -> test_m4_session_identity_must_be_equal
M5 -> test_m5_generated_session_rows_require_set_equality /
      test_verify_replays_complete_fake_codex_experiment
M6 -> test_m6_verdict_packet_swap_restore_digest_layers_are_redundant
M7 -> test_m7_ledger_issues_propagate_to_failure
M8 -> test_m8_missing_turn_context_never_fills_requested_effort
M9 -> test_m9_post_treatment_failure_remains_in_denominator
M10 -> test_m10_historical_controls
M11 -> test_m11_tilde_fence_hides_summary
M12 -> test_m12_summary_500_byte_exact_boundary

変更前HEAD版では上記のうち旧nodeが存在する場合は同名、存在しない場合は未収集となる。
親のmutation harnessはこの一覧を期待node正本として新旧双方を突き合わせる。

DW-M08 old-HEAD comparison nodes:
M1 -> test_snapshot_git_object_closure_is_base_only
M2 -> test_production_golden_entrypoint_executes_route_comparison
M3 -> <none: mode/untracked/focus independent nodes were lost>
M4 -> <none: id/session_id negative was lost>
M5 -> test_verify_rejects_extra_session_row_even_with_duplicate_id
M6 -> test_verdict_row_swap_is_rejected
M7 -> <none: malformed-ledger propagation node was lost>
M8 -> <none: missing-context effort-fill node was lost>
M9 -> <none: post-treatment denominator node was lost>
M10 -> test_scorer_preserves_historical_controls
M11 -> test_tilde_fence_with_backtick_info_hides_fake_summary
M12 -> <none: 500-byte exact boundary node was lost>
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_TOOL_PATH = _ROOT / "tools" / "codex_reasoning_ab.py"
_SPEC = importlib.util.spec_from_file_location(
    "codex_reasoning_ab_under_test", _TOOL_PATH
)
assert _SPEC and _SPEC.loader
TOOL = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = TOOL
_SPEC.loader.exec_module(TOOL)

_HISTORICAL_SESSIONS = Path("/home/SFC/tanab/.codex/sessions")
_CONTROL_DIR = (
    _ROOT
    / "output"
    / "insights"
    / "2026-07-29_t153e-t15423-review-verbatim"
)
_FOCUS1_SHA = "901ad02256524bac35c56ae4e3a2b7c5fbc01a618670182885040c6912b82771"
_FOCUS2_SHA = "a738cd2979b3569dd90563e8f0931cd8badbc4b4cebe66129695bbb194fbe978"
_CERTIFIED_RERUN_DIR = (
    _ROOT
    / "output"
    / "insights"
    / "2026-08-09_t181-certified-rerun"
    / "run-outputs"
)
_S03_SHA = "393df3429fff61bb87d45350237a55ea3346ff9cbad0f7042eeb9ebf859b33ce"
_REAL_ROLLOUT = (
    _HISTORICAL_SESSIONS
    / "2026/07/29/"
    "rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl"
)
_REAL_TOKEN_SLICE = (
    '{"timestamp":"2026-07-29T06:49:36.776Z","type":"event_msg","payload":'
    '{"type":"token_count","info":{"total_token_usage":{"input_tokens":17295,'
    '"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":513,'
    '"reasoning_output_tokens":348,"total_tokens":17808},"last_token_usage":'
    '{"input_tokens":17295,"cached_input_tokens":0,"cache_write_input_tokens":0,'
    '"output_tokens":513,"reasoning_output_tokens":348,"total_tokens":17808},'
    '"model_context_window":258400},"rate_limits":{"limit_id":"codex",'
    '"limit_name":null,"primary":{"used_percent":9.0,"window_minutes":10080,'
    '"resets_at":1785902971},"secondary":null,"credits":{"has_credits":false,'
    '"unlimited":false,"balance":"0"},"individual_limit":null,'
    '"spend_control_reached":null,"plan_type":"pro",'
    '"rate_limit_reached_type":null}}}\n'
)
_REAL_TOKEN_SLICE_SHA = (
    "4491137b7bea866921f7b117d2302adc80cd58e82e70c531de83b3e7c3ad82c9"
)


def _canonical(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(TOOL._canonical_bytes(value))
    return path


def _rglob_filesystem_file_set_reference(snapshot: Path) -> set[str]:
    """変更前の実装を逐語で保つ、静止した test tree 用 oracle。"""
    found: set[str] = set()
    root_git = (snapshot / ".git").resolve()
    for path in snapshot.rglob("*"):
        resolved_parent = path.parent.resolve()
        if resolved_parent == root_git or root_git in resolved_parent.parents:
            continue
        metadata = path.lstat()
        if not stat.S_ISDIR(metadata.st_mode):
            found.add(path.relative_to(snapshot).as_posix())
    return found


def _descriptor(path: Path, root: Path) -> dict[str, str]:
    try:
        rendered = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rendered = str(path.resolve())
    return {
        "path": rendered,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _index_semantics(
    snapshot: Path,
) -> dict[str, list[tuple[str, str, str, str, str]]]:
    """Compare index entries and ls-files flags, but not index extensions."""
    snapshot = snapshot.resolve()
    repositories = [snapshot, *TOOL._submodule_repositories(snapshot)]
    semantics: dict[str, list[tuple[str, str, str, str, str]]] = {}
    for repository in repositories:
        entries: list[tuple[str, str, str, str, str]] = []
        raw = TOOL._git(repository, "ls-files", "--stage", "-v", "-z")
        for record in raw.split(b"\0"):
            if not record:
                continue
            metadata, separator, path_bytes = record.partition(b"\t")
            assert separator == b"\t"
            flag, mode, object_id, stage = metadata.split(b" ")
            assert len(flag) == 1
            relative = os.fsdecode(path_bytes)
            assert mode.decode("ascii") in {
                "100644",
                "100755",
                "120000",
                "160000",
            }
            assert stage.isdigit()
            entries.append(
                (
                    mode.decode("ascii"),
                    object_id.decode("ascii"),
                    stage.decode("ascii"),
                    relative,
                    flag.decode("ascii"),
                )
            )
        label = (
            "."
            if repository == snapshot
            else repository.relative_to(snapshot).as_posix()
        )
        semantics[label] = entries
    return semantics


def _assert_relocated_submodules(snapshot: Path) -> None:
    snapshot = snapshot.resolve()
    repositories = TOOL._submodule_repositories(snapshot)
    assert [
        repository.relative_to(snapshot).as_posix()
        for repository in repositories
    ] == ["deps/child", "deps/child/third_party/grandchild"]
    for repository in repositories:
        marker = repository / ".git"
        metadata = marker.lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not stat.S_ISLNK(metadata.st_mode)
        raw_marker = marker.read_bytes()
        assert raw_marker.startswith(b"gitdir: ")
        marker_value = os.fsdecode(raw_marker.removeprefix(b"gitdir: ").strip())
        assert not Path(marker_value).is_absolute()
        git_dir = (marker.parent / marker_value).resolve()
        assert git_dir == TOOL._git_dir(repository)
        assert git_dir == snapshot or snapshot in git_dir.parents

        worktree = TOOL._run(
            ("git", "config", "--get", "core.worktree"),
            cwd=repository,
            check=False,
        )
        assert worktree.returncode == 0
        worktree_value = worktree.stdout.decode("utf-8").strip()
        assert worktree_value
        assert not Path(worktree_value).is_absolute()
        assert (git_dir / worktree_value).resolve() == repository.resolve()


def _long_output(decision: str = "NO-GO") -> str:
    return (
        "検査本文。" * 160
        + "\n### R-1 canonical CAB parser\n"
        + "pre-policyでもcanonical CAB parserが実行され、従来rc=0の入力が"
        + "rc=2へ変わるためmust-fixである。\n"
        + "\n## 総括\n"
        + f"**{decision}。** "
        + "この総括節は裁定packetへ渡される十分に長い本文である。" * 40
    )


def _usage(zero: bool = False) -> dict[str, int]:
    input_tokens, output_tokens, reasoning = ((0, 0, 0) if zero else (20, 8, 3))
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": 0,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning,
        "total_tokens": input_tokens + output_tokens,
    }


def _zero_component_total_only(total_tokens: int = 12_661) -> dict[str, int]:
    return {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "cache_write_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": total_tokens,
    }


def _token_usage_observations(
    indexes: tuple[int, ...] = ()
) -> dict[str, dict[str, Any]]:
    return {
        TOOL.ZERO_COMPONENT_TOTAL_ONLY: {
            "usage": "last_token_usage",
            "count": len(indexes),
            "indexes": list(indexes),
        }
    }


def _iso(base: datetime, milliseconds: int) -> str:
    return (base + timedelta(milliseconds=milliseconds)).isoformat().replace(
        "+00:00", "Z"
    )


def _make_executable(path: Path, source: str) -> Path:
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


def _make_fake_codex(path: Path) -> Path:
    return _make_executable(
        path,
        """#!/usr/bin/env python3
import datetime, json, os, pathlib, sys, uuid
if "--version" in sys.argv:
    print("codex-cli 0.146.0")
    raise SystemExit(0)
args = sys.argv[1:]
output = pathlib.Path(args[args.index("-o") + 1])
effort = next(value.split("=", 1)[1] for value in args if value.startswith("model_reasoning_effort="))
prompt = sys.stdin.read()
thread = str(uuid.uuid4())
turn = "turn-" + thread
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
answer = ("検査本文。" * 160 + "\\n### R-1 canonical CAB parser\\n"
          "pre-policyでもcanonical CAB parserが実行され、従来rc=0の入力がrc=2へ変わるためmust-fix。"
          "\\n## 総括\\n**NO-GO。** " + "十分に長い総括本文。" * 80)
output.write_text(answer, encoding="utf-8")
usage = {"input_tokens": 20, "cached_input_tokens": 0, "output_tokens": 8,
         "reasoning_output_tokens": 3, "total_tokens": 28}
rows = [
 {"timestamp": now(), "type": "session_meta", "payload": {
  "id": thread, "session_id": thread, "timestamp": now(), "cwd": os.getcwd(),
  "cli_version": "0.146.0", "git": {"commit_hash": "8c8dc5e0a337677e213b4ebabbeff5ea188111ae"}}},
 {"timestamp": now(), "type": "event_msg", "payload": {"type": "task_started", "turn_id": turn}},
 {"timestamp": now(), "type": "turn_context", "payload": {
  "turn_id": turn, "cwd": os.getcwd(), "model": "gpt-5.6-sol", "effort": effort}},
 {"timestamp": now(), "type": "event_msg", "payload": {"type": "user_message", "message": prompt}},
 {"timestamp": now(), "type": "event_msg", "payload": {"type": "token_count", "info": {
  "total_token_usage": usage, "last_token_usage": usage}}},
 {"timestamp": now(), "type": "event_msg", "payload": {"type": "agent_message", "message": answer}},
 {"timestamp": now(), "type": "event_msg", "payload": {
  "type": "task_complete", "turn_id": turn, "duration_ms": 0}},
]
session_root = pathlib.Path(os.environ["CODEX_HOME"]) / "sessions"
session_root.mkdir(parents=True)
(session_root / ("rollout-" + thread + ".jsonl")).write_text(
 "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\\n" for row in rows),
 encoding="utf-8")
print(json.dumps({"type": "thread.started", "thread_id": thread}, separators=(",", ":")))
""",
    )


def _schedule(
    path: Path, benchmark: dict[str, Any]
) -> tuple[Path, list[dict[str, Any]]]:
    slots: list[dict[str, Any]] = []
    number = 0
    for case, blocks in (("POS", 3), ("NEG", 2)):
        for block in range(1, blocks + 1):
            order = ("max", "high") if block % 2 else ("high", "max")
            for block_order, arm in enumerate(order, 1):
                number += 1
                slots.append(
                    {
                        "slot_id": f"s{number:02d}",
                        "case": case,
                        "arm": arm,
                        "block_id": f"b{len(slots) // 2 + 1:02d}",
                        "block_order": block_order,
                        "prompt_sha256": hashlib.sha256(
                            benchmark[case]["prompt"].read_bytes()
                        ).hexdigest(),
                        "snapshot_manifest_sha256": hashlib.sha256(
                            benchmark[case]["oracle"].read_bytes()
                        ).hexdigest(),
                        "submodule_manifest_sha256": benchmark[case][
                            "oracle_value"
                        ]["submodule_manifest_sha256"],
                    }
                )
    return _canonical(path, {"slots": slots}), slots


@pytest.fixture(scope="module")
def benchmark_snapshots(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    if not _HISTORICAL_SESSIONS.is_dir():
        pytest.skip("historical rollout root is unavailable")
    root = tmp_path_factory.mktemp("t181-benchmark")
    base = root / "base"
    destinations = {case: root / case.lower() for case in ("POS", "NEG")}
    TOOL._resolve_snapshot_destination(_ROOT, base)
    resolved_destinations = {
        case: TOOL._resolve_snapshot_destination(_ROOT, snapshot)
        for case, snapshot in destinations.items()
    }
    prepared = {
        case: TOOL._prepare_snapshot_case(_ROOT, _HISTORICAL_SESSIONS, case)
        for case in ("POS", "NEG")
    }

    TOOL._build_snapshot_base(_ROOT, base)
    base_manifests = {"initial": TOOL._metadata_manifest(base)}
    result: dict[str, Any] = {
        "root": root,
        "_base": base,
        "_base_manifests": base_manifests,
    }
    for case in ("POS", "NEG"):
        snapshot = destinations[case]
        oracle = TOOL._derive_snapshot_from_base(
            _ROOT,
            base,
            snapshot,
            _HISTORICAL_SESSIONS,
            case,
            prepared_golden=prepared[case],
            prepared_destination=resolved_destinations[case],
        )
        base_manifests[f"after_{case.lower()}"] = TOOL._metadata_manifest(base)
        oracle_path = _canonical(root / f"{case.lower()}-oracle.json", oracle)
        prompt, prompt_receipt = TOOL.render_prompt(
            _HISTORICAL_SESSIONS, case, snapshot
        )
        prompt_path = root / f"{case.lower()}-prompt.txt"
        prompt_path.write_bytes(prompt)
        result[case] = {
            "snapshot": snapshot,
            "oracle": oracle_path,
            "oracle_value": oracle,
            "prompt": prompt_path,
            "prompt_receipt": prompt_receipt,
        }
    return result


def _manual_run(
    root: Path,
    *,
    id_mismatch: bool = False,
    missing_context: bool = False,
    malformed_rollout: bool = False,
    non_object_rollout: bool = False,
    partial_output: bool = False,
    empty_turn: bool = False,
    token_infos: list[Any] | None = None,
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / "r01"
    run_dir.mkdir()
    agent_workspace = root / "agent-workspaces" / "worker-opaque"
    agent_workspace.mkdir(parents=True)
    codex_home = agent_workspace / "codex-home"
    codex_home.mkdir()
    snapshot = root / "snapshot"
    snapshot.mkdir()
    sessions = root / "sessions"
    sessions.mkdir()
    prompt = root / "prompt.txt"
    prompt.write_text("prompt", encoding="utf-8")
    output = agent_workspace / "answer.md"
    output.write_text(
        "## 総括\nNO-GO。" if partial_output else _long_output(),
        encoding="utf-8",
    )
    events = agent_workspace / "events.jsonl"
    done = run_dir / ".done"
    stderr = agent_workspace / "stderr.log"
    events.write_bytes(b"")
    done.write_bytes(b"")
    stderr.write_bytes(b"")
    config = codex_home / "config.toml"
    auth = codex_home / "auth.json"
    cli = _make_executable(run_dir / "codex", "#!/bin/sh\nprintf 'codex 0.146.0\\n'\n")
    bwrap = _make_executable(run_dir / "bwrap", "#!/bin/sh\nexit 0\n")
    config.write_text("model='gpt-5.6-sol'\n", encoding="utf-8")
    auth.write_text("{}\n", encoding="utf-8")
    oracle = _canonical(run_dir / "snapshot-before.json", {"snapshot": str(snapshot)})
    environment = {
        "CODEX_HOME": str(codex_home),
        "HOME": "/tmp/t181-home",
        "LANG": "C.UTF-8",
    }
    argv = [
        str(cli),
        "exec",
        "-c",
        "model_reasoning_effort=max",
        "-o",
        str(output),
    ]
    bwrap_argv = TOOL._bwrap_exec_argv(
        bwrap,
        argv,
        snapshot,
        codex_home,
        output,
        events,
        stderr,
        environment,
    )
    started = datetime.now(timezone.utc)
    start_ns = time.monotonic_ns()
    launch = {
        "schema_version": TOOL.SCHEMA_VERSION,
        "run_id": "r01",
        "slot_id": "s01",
        "attempt": 1,
        "parent_run_id": None,
        "case": "POS",
        "arm": "max",
        "created_at": started.isoformat().replace("+00:00", "Z"),
        "process_start_monotonic_ns": start_ns,
        "process_pid": 1,
        "events": TOOL._regular_file_state(events, "events"),
        "done": TOOL._regular_file_state(done, "done"),
        "prompt": {"path": str(prompt.resolve()), "sha256": TOOL._sha256(prompt.read_bytes())},
        "snapshot_oracle": {"path": str(oracle.resolve()), "sha256": TOOL._sha256(oracle.read_bytes())},
        "run_dir": str(run_dir.resolve()),
        "agent_workspace": str(agent_workspace.resolve()),
        "output_path": str(output.resolve()),
        "stderr_path": str(stderr.resolve()),
        "codex_home": str(codex_home.resolve()),
        "codex_config": str(config.resolve()),
        "codex_config_sha256": TOOL._sha256(config.read_bytes()),
        "codex_auth": str(auth.resolve()),
        "codex_auth_sha256": TOOL._sha256(auth.read_bytes()),
        "cli_binary": str(cli.resolve()),
        "cli_binary_sha256": TOOL._sha256(cli.read_bytes()),
        "cli_version": "codex 0.146.0",
        "argv": argv,
        "normalized_argv": TOOL._normalized_exec_argv(argv, "max"),
        "bwrap_binary": str(bwrap.resolve()),
        "bwrap_binary_sha256": TOOL._sha256(bwrap.read_bytes()),
        "bwrap_version": "bwrap 0.6.1",
        "bwrap_argv": bwrap_argv,
        "actual_process_argv": argv,
        "actual_process_argv_normalized": TOOL._normalized_exec_argv(argv, "max"),
        "environment": environment,
        "sandbox": {
            "snapshot_mount": "read-only",
            "home_masked": True,
            "tmp_masked": True,
            "pid_namespace": True,
            "proc_mount": "fresh",
            "writable_binds": ["codex-home", "output", "stdout", "stderr"],
            "attempt_receipts_bound": False,
        },
        "world_state": {
            "snapshot_verified_before": True,
            "git_environment_cleared": True,
        },
        "schedule_sha256": "a" * 64,
        "dry_run": True,
    }
    launch["treatment_identity_sha256"] = TOOL._launch_identity_value(launch)
    launch_path = _canonical(run_dir / "launch.json", launch)
    thread = "019fac00-0000-7000-8000-000000000001"
    session_id = "different" if id_mismatch else thread
    turn = "" if empty_turn else "turn-1"
    rows: list[dict[str, Any]] = [
        {
            "timestamp": _iso(started, 1),
            "type": "session_meta",
            "payload": {
                "id": thread,
                "session_id": session_id,
                "timestamp": _iso(started, 1),
                "cwd": str(snapshot.resolve()),
                "cli_version": "0.146.0",
                "git": {"commit_hash": TOOL.BASE_COMMIT},
            },
        },
        {
            "timestamp": _iso(started, 2),
            "type": "event_msg",
            "payload": {"type": "task_started", "turn_id": turn},
        },
    ]
    if not missing_context:
        rows.append(
            {
                "timestamp": _iso(started, 3),
                "type": "turn_context",
                "payload": {
                    "turn_id": turn,
                    "cwd": str(snapshot.resolve()),
                    "model": TOOL.MODEL,
                    "effort": "max",
                },
            }
        )
    token_infos = token_infos if token_infos is not None else [
        {
            "total_token_usage": _usage(),
            "last_token_usage": _usage(),
        }
    ]
    rows.extend(
        [
            {
                "timestamp": _iso(started, 4),
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "prompt"},
            },
            *[
                {
                    "timestamp": _iso(started, 5),
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": info,
                    },
                }
                for info in token_infos
            ],
            {
                "timestamp": _iso(started, 6),
                "type": "event_msg",
                "payload": {
                    "type": "agent_message",
                    "message": output.read_text(encoding="utf-8"),
                },
            },
            {
                "timestamp": _iso(started, 7),
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "turn_id": turn,
                    "duration_ms": 5,
                },
            },
        ]
    )
    rollout = sessions / "rollout-r01.jsonl"
    rollout.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        + ("not-json\n" if malformed_rollout else "")
        + ("[]\n" if non_object_rollout else ""),
        encoding="utf-8",
    )
    events.write_text(
        json.dumps({"type": "thread.started", "thread_id": thread}) + "\n",
        encoding="utf-8",
    )
    done.write_bytes(
        TOOL._canonical_bytes(
            {
                "exit_code": 0,
                "exited_at": _iso(started, 9),
                "process_exit_monotonic_ns": start_ns + 9_000_000,
            }
        )
    )
    receipt, rc = TOOL.collect_run(
        run_id="r01",
        case="POS",
        requested_effort="max",
        events=events,
        done=done,
        output=output,
        prompt=prompt,
        sessions_root=sessions,
        snapshot=snapshot,
        launch_receipt=launch_path,
    )
    return {"receipt": receipt, "rc": rc, "rollout": rollout}


def _supervisor_pair(
    root: Path, benchmark: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], Path, list[dict[str, Any]]]:
    schedule_path, slots = _schedule(root / "schedule-source.json", benchmark)
    config = root / "config-source.toml"
    auth = root / "auth-source.json"
    config.write_text("model='gpt-5.6-sol'\n", encoding="utf-8")
    auth.write_text('{"token":"synthetic"}\n', encoding="utf-8")
    codex = _make_fake_codex(root / "fake-codex")
    bwrap = _make_executable(
        root / "fake-bwrap",
        "#!/bin/sh\n[ \"$1\" = \"--version\" ] && printf 'bwrap 0.6.1\\n'\n",
    )
    monkeypatch.setenv("GIT_ALTERNATE_OBJECT_DIRECTORIES", "/forbidden")
    result = TOOL.supervise_pair(
        schedule_path=schedule_path,
        run_root=root / "run-root",
        block_id="b01",
        attempt=1,
        snapshot=benchmark["POS"]["snapshot"],
        prompt=benchmark["POS"]["prompt"],
        config_source=config,
        auth_source=auth,
        codex_binary=codex,
        bwrap_binary=bwrap,
        dry_run=True,
    )
    return result, schedule_path, slots


def _full_manifest(
    root: Path,
    benchmark: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    schedule_source, slots = _schedule(root / "schedule-source.json", benchmark)
    run_root = root / "run-root"
    config = root / "config-source.toml"
    auth = root / "auth-source.json"
    config.write_text("model='gpt-5.6-sol'\n", encoding="utf-8")
    auth.write_text('{"token":"synthetic"}\n', encoding="utf-8")
    codex = _make_fake_codex(root / "fake-codex")
    bwrap = _make_executable(
        root / "fake-bwrap",
        "#!/bin/sh\n[ \"$1\" = \"--version\" ] && printf 'bwrap 0.6.1\\n'\n",
    )
    monkeypatch.setenv("GIT_DIR", "/forbidden")
    completions: list[dict[str, Any]] = []
    for block_id in ("b01", "b02", "b03", "b04", "b05"):
        slot = next(row for row in slots if row["block_id"] == block_id)
        result = TOOL.supervise_pair(
            schedule_path=schedule_source,
            run_root=run_root,
            block_id=block_id,
            attempt=1,
            snapshot=benchmark[slot["case"]]["snapshot"],
            prompt=benchmark[slot["case"]]["prompt"],
            config_source=config,
            auth_source=auth,
            codex_binary=codex,
            bwrap_binary=bwrap,
            dry_run=True,
        )
        completions.extend(result["runs"])
    attempts: list[dict[str, Any]] = []
    for completion in completions:
        launch_path = Path(completion["launch_receipt"])
        launch = json.loads(launch_path.read_text(encoding="utf-8"))
        attempt_dir = Path(launch["run_dir"])
        events = Path(launch["events"]["path"])
        done = Path(launch["done"]["path"])
        prompt = Path(launch["prompt"]["path"])
        oracle = Path(launch["snapshot_oracle"]["path"])
        oracle_value = json.loads(oracle.read_text(encoding="utf-8"))
        output = Path(launch["output_path"])
        thread_id = TOOL._thread_id_from_events(events)
        rollout = TOOL._find_rollout(run_root, thread_id)
        receipt, receipt_rc = TOOL.collect_run(
            run_id=completion["run_id"],
            case=completion["case"],
            requested_effort=completion["arm"],
            events=events,
            done=done,
            output=output,
            prompt=prompt,
            sessions_root=run_root,
            snapshot=Path(oracle_value["snapshot"]),
            launch_receipt=launch_path,
        )
        assert receipt_rc == 0
        score, score_rc = TOOL.score_run(output, completion["run_id"])
        assert score_rc == 0
        receipt_path = _canonical(attempt_dir / "receipt.json", receipt)
        score_path = _canonical(attempt_dir / "score.json", score)
        attempts.append(
            {
                "run_id": completion["run_id"],
                "slot_id": completion["slot_id"],
                "attempt": completion["attempt"],
                "parent_run_id": completion["parent_run_id"],
                "launch_receipt": _descriptor(launch_path, root),
                "events": _descriptor(events, root),
                "done": _descriptor(done, root),
                "rollout": _descriptor(rollout, root),
                "prompt": _descriptor(prompt, root),
                "output": _descriptor(output, root),
                "snapshot_oracle": _descriptor(oracle, root),
                "snapshot_after": _descriptor(
                    attempt_dir / "snapshot-after.json", root
                ),
                "receipt": _descriptor(receipt_path, root),
                "score": _descriptor(score_path, root),
            }
        )
    premanifest = _canonical(root / "premanifest.json", {"attempts": attempts})
    custodian_root = root / "mapping-custodian"
    packet_result = TOOL.make_packets(
        premanifest, root / "packets", custodian_root
    )
    packet_state = Path(packet_result["packet_state"])
    packet_rows = json.loads(packet_state.read_text(encoding="utf-8"))["packets"]
    verdict_rows = [
        {
            "packet_id": packet["packet_id"],
            "r1_detected": True,
            "findings": [],
        }
        for packet in packet_rows
    ]
    parent_input = _canonical(
        root / "parent-verdicts.json", {"verdicts": verdict_rows}
    )
    second_input = _canonical(
        root / "second-verdicts.json", {"verdicts": verdict_rows}
    )
    verdict_log = root / "verdicts.jsonl"
    TOOL.append_verdicts(
        packet_state, verdict_log, "parent", parent_input
    )
    TOOL.append_verdicts(
        packet_state, verdict_log, "second-reader", second_input
    )
    freeze = root / "verdict-freeze.json"
    TOOL.freeze_verdicts(packet_state, verdict_log, freeze)
    revealed = root / "revealed-map.json"
    TOOL.reveal_mapping(
        packet_state,
        custodian_root,
        verdict_log,
        freeze,
        revealed,
    )
    log_rows = [
        json.loads(line)
        for line in verdict_log.read_text(encoding="utf-8").splitlines()
    ]
    readers_by_packet: dict[str, dict[str, dict[str, Any]]] = {}
    for row in log_rows:
        readers_by_packet.setdefault(row["packet_id"], {})[row["reader"]] = row
    judgments = []
    for mapping in json.loads(revealed.read_text(encoding="utf-8"))["mapping"]:
        packet_id = mapping["packet_id"]
        run_id = mapping["run_id"]
        readers = readers_by_packet[packet_id]
        combined = {
            "r1_detected": (
                readers["parent"]["r1_detected"] is True
                and readers["second-reader"]["r1_detected"] is True
            ),
            "findings": [],
            "reader_agreement": True,
            "reader_rows_sha256": TOOL._sha256(
                TOOL._canonical_bytes(
                    [readers["parent"], readers["second-reader"]]
                )
            ),
        }
        judgments.append(
            {
                "slot_id": next(
                    row["slot_id"] for row in completions if row["run_id"] == run_id
                ),
                "packet_id": packet_id,
                "score_input_sha256": mapping["score_input_sha256"],
                "combined_verdict_sha256": TOOL._sha256(
                    TOOL._canonical_bytes(combined)
                ),
                "r1_detected": combined["r1_detected"],
                "reader_agreement": True,
            }
        )
    manifest = {
        "schema_version": TOOL.SCHEMA_VERSION,
        "run_root": str(run_root.relative_to(root)),
        "attempts_root": str((run_root / "attempts").relative_to(root)),
        "attempt_ledger": _descriptor(
            run_root / "attempt-ledger.jsonl", root
        ),
        "max_schedule_gap_ms": TOOL.MAX_SCHEDULE_GAP_MS,
        "max_inter_block_gap_ms": TOOL.MAX_INTER_BLOCK_GAP_MS,
        "schedule": _descriptor(run_root / "schedule.json", root),
        "schedule_sha256": TOOL._sha256(
            (run_root / "schedule.json").read_bytes()
        ),
        "attempts": attempts,
        "packet_state": _descriptor(packet_state, root),
        "verdict_log": _descriptor(verdict_log, root),
        "verdict_freeze": _descriptor(freeze, root),
        "revealed_map": _descriptor(revealed, root),
        "judgments": judgments,
    }
    return _canonical(root / "manifest.json", manifest), run_root


def test_corrected_case_allowlists_are_literal() -> None:
    assert TOOL.CASE_ARTIFACTS["POS"] == ("review-a.md", "review-b.md", "fix1.md")
    assert TOOL.CASE_ARTIFACTS["NEG"] == (
        "brief.md",
        "adjudication-plan-v2.md",
        "review-a.md",
        "review-b.md",
        "focus1.md",
        "fix2.md",
    )


def test_parent_numstat_controls_remain_pinned(
    benchmark_snapshots: dict[str, Any],
) -> None:
    pos = TOOL.verify_snapshot(benchmark_snapshots["POS"]["snapshot"], "POS")
    neg = TOOL.verify_snapshot(benchmark_snapshots["NEG"]["snapshot"], "NEG")
    assert next(row for row in pos["numstat"] if row[2].endswith("test_check_ai_provenance.py"))[:2] == [693, 0]
    assert next(row for row in pos["numstat"] if row[2].endswith("check_ai_provenance.py") and not row[2].startswith("orchestrator"))[:2] == [123, 10]
    assert next(row for row in neg["numstat"] if row[2].endswith("test_check_ai_provenance.py"))[:2] == [764, 0]
    assert next(row for row in neg["numstat"] if row[2].endswith("check_ai_provenance.py") and not row[2].startswith("orchestrator"))[:2] == [126, 10]


def test_forbidden_commits_are_unreachable_in_both_cases(
    benchmark_snapshots: dict[str, Any],
) -> None:
    for case in ("POS", "NEG"):
        snapshot = benchmark_snapshots[case]["snapshot"]
        for forbidden in (TOOL.INTEGRATED_COMMIT, TOOL.ARTIFACT_COMMIT):
            probe = subprocess.run(
                ["git", "cat-file", "-e", forbidden],
                cwd=snapshot,
                check=False,
                capture_output=True,
                env=TOOL._clean_environment(),
            )
            assert probe.returncode != 0
        assert TOOL._git(
            snapshot, "for-each-ref", "--format=%(refname)"
        ).decode().splitlines() == [f"refs/heads/{TOOL.BRANCH}"]


def test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure(
    benchmark_snapshots: dict[str, Any],
) -> None:
    for case in ("POS", "NEG"):
        snapshot = benchmark_snapshots[case]["snapshot"]
        oracle = TOOL.verify_snapshot(snapshot, case)
        repositories = oracle["git_object_closure"]["repositories"]
        assert repositories
        for repository in repositories:
            assert repository["commit_graph"] == {
                "present": False,
                "valid": None,
                "paths": [],
                "verify_returncode": None,
                "verify_stderr_first_line": None,
            }
            assert not any(
                row["path"].startswith("objects/info/")
                for row in repository["metadata"]
            )
        for forbidden in (TOOL.INTEGRATED_COMMIT, TOOL.ARTIFACT_COMMIT):
            assert subprocess.run(
                ["git", "cat-file", "-e", forbidden],
                cwd=snapshot,
                check=False,
                capture_output=True,
                env=TOOL._clean_environment(),
            ).returncode != 0
        assert TOOL._git(
            snapshot, "for-each-ref", "--format=%(refname)"
        ).decode().splitlines() == [f"refs/heads/{TOOL.BRANCH}"]
        for focus in ("focus1.md", "focus2.md"):
            relative = f"{TOOL.ARTIFACT_DIR}/{focus}"
            assert not TOOL._git(
                snapshot, "log", "--all", "--format=%H", "--", relative
            ).strip()


def test_object_info_derived_caches_are_removed_for_root_and_submodule(
    tmp_path: Path,
) -> None:
    snapshot, submodule, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    for repository in (snapshot, submodule):
        git_dir = TOOL._git_dir(repository)
        object_info = git_dir / "objects/info"
        split_graphs = object_info / "commit-graphs"
        split_graphs.mkdir(parents=True, exist_ok=True)
        (object_info / "commit-graph").write_bytes(b"stale monolithic graph")
        (split_graphs / "graph-stale.graph").write_bytes(b"stale split graph")
        (object_info / "packs").write_text("P stale.pack\n", encoding="ascii")
        TOOL._remove_git_object_info_caches(git_dir)
        assert object_info.is_dir()
        assert list(object_info.iterdir()) == []


def _install_stale_commit_graph(repository: Path) -> str:
    head = TOOL._git(repository, "rev-parse", "HEAD").decode().strip()
    tree = TOOL._git(repository, "rev-parse", "HEAD^{tree}").decode().strip()
    stale = TOOL._git(
        repository,
        "-c",
        "user.name=T181",
        "-c",
        "user.email=t181@example.invalid",
        "commit-tree",
        tree,
        "-p",
        head,
        input_bytes=b"pruned answer commit\n",
    ).decode().strip()
    TOOL._git(repository, "update-ref", "refs/heads/stale-answer", stale)
    TOOL._git(repository, "commit-graph", "write", "--reachable")
    TOOL._git(repository, "update-ref", "-d", "refs/heads/stale-answer")
    TOOL._run(
        (
            "git",
            "reflog",
            "expire",
            "--expire=now",
            "--expire-unreachable=now",
            "--all",
        ),
        cwd=repository,
    )
    TOOL._run(("git", "repack", "-Ad"), cwd=repository)
    TOOL._run(("git", "prune-packed"), cwd=repository)
    TOOL._run(("git", "prune", "--expire=now"), cwd=repository)
    assert TOOL._run(
        ("git", "cat-file", "-e", stale),
        cwd=repository,
        check=False,
    ).returncode != 0
    return stale


def test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
) -> None:
    snapshot = tmp_path / "stale-commit-graph"
    shutil.copytree(benchmark_snapshots["POS"]["snapshot"], snapshot)
    _install_stale_commit_graph(snapshot)

    reasons, manifests, _ = TOOL._git_closure_reasons(
        snapshot, TOOL._snapshot_spec("POS")["untracked"]
    )
    assert any("git commit-graph verify exited" in reason for reason in reasons)
    commit_graph = manifests[0]["commit_graph"]
    assert commit_graph["present"] is True
    assert commit_graph["valid"] is False
    assert commit_graph["verify_returncode"] != 0
    assert commit_graph["paths"]
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS")
    assert any(
        "git commit-graph verify exited" in reason
        for reason in caught.value.reasons
    )


def test_fsck_nonzero_reason_is_not_mislabeled_as_unreachable_objects() -> None:
    completed = subprocess.CompletedProcess(
        args=["git", "fsck"],
        returncode=17,
        stdout=b"",
        stderr=(
            b"error: Could not read 08a7e5f2fc08d57309a86ef70d00e9b050ebec9c\n"
            b"failed to parse commit from commit-graph\n"
        ),
    )
    reasons = TOOL._git_fsck_reasons(".", completed)
    assert reasons == [
        ".: git fsck exited 17: "
        "error: Could not read 08a7e5f2fc08d57309a86ef70d00e9b050ebec9c"
    ]
    assert all("unreachable objects" not in reason for reason in reasons)


def test_fsck_unreachable_stdout_reports_count_independently() -> None:
    completed = subprocess.CompletedProcess(
        args=["git", "fsck"],
        returncode=0,
        stdout=b"unreachable blob aaaa\nunreachable commit bbbb\n",
        stderr=b"",
    )
    assert TOOL._git_fsck_reasons("deps/child", completed) == [
        "deps/child: git object store contains unreachable objects (2)"
    ]


def test_m1_snapshot_head_pin_is_independent(
    benchmark_snapshots: dict[str, Any],
) -> None:
    spec = copy.deepcopy(TOOL._snapshot_spec("POS"))
    spec["head"] = "0" * 40
    with pytest.raises(TOOL.ValidationError, match="HEAD mismatch"):
        TOOL.verify_snapshot(benchmark_snapshots["POS"]["snapshot"], "POS", spec=spec)


def test_m2_production_golden_requires_both_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False
    original = TOOL._compare_golden_routes

    def observed(route_a: Any, route_b: Any) -> dict[str, bytes]:
        nonlocal called
        called = True
        return original(route_a, route_b)

    monkeypatch.setattr(TOOL, "_compare_golden_routes", observed)
    golden = TOOL.derive_independent_golden(_ROOT, _HISTORICAL_SESSIONS)
    assert called is True
    assert hashlib.sha256(golden[TOOL.PATCH_PATHS[0]]).hexdigest() == (
        "bc3f5f95f5c9c3f44955bbd1b2e3affbbafb6e62fda8e836173e1b9d5998c3af"
    )


def test_m3_snapshot_mode_change(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    for case in ("POS", "NEG"):
        snapshot = tmp_path / case.lower()
        shutil.copytree(benchmark_snapshots[case]["snapshot"], snapshot)
        target = snapshot / TOOL.TRACKED_PATHS[0]
        target.chmod(0o600)
        with pytest.raises(TOOL.ValidationError, match="st_mode mismatch"):
            TOOL.verify_snapshot(snapshot, case)


def test_m3_symbolic_head_is_required(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    snapshot = tmp_path / "detached"
    shutil.copytree(benchmark_snapshots["POS"]["snapshot"], snapshot)
    (snapshot / ".git/HEAD").write_text(TOOL.BASE_COMMIT + "\n", encoding="ascii")
    with pytest.raises(TOOL.ValidationError, match="symbolic HEAD mismatch"):
        TOOL.verify_snapshot(snapshot, "POS")


def test_m3_ignored_extra_and_missing(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    for case in ("POS", "NEG"):
        extra_snapshot = tmp_path / f"extra-{case.lower()}"
        shutil.copytree(benchmark_snapshots[case]["snapshot"], extra_snapshot)
        (extra_snapshot / ".answer-cache").write_text("leak", encoding="utf-8")
        with (extra_snapshot / ".git/info/exclude").open("a", encoding="utf-8") as stream:
            stream.write("\n.answer-cache\n")
        with pytest.raises(TOOL.ValidationError, match="filesystem allowlist has extra"):
            TOOL.verify_snapshot(extra_snapshot, case)
        missing_snapshot = tmp_path / f"missing-{case.lower()}"
        shutil.copytree(benchmark_snapshots[case]["snapshot"], missing_snapshot)
        missing_relative = (
            f"{TOOL.ARTIFACT_DIR}/focus1.md"
            if case == "NEG"
            else TOOL._snapshot_spec(case)["untracked"][0]
        )
        (missing_snapshot / missing_relative).unlink()
        with pytest.raises(TOOL.ValidationError, match="missing"):
            TOOL.verify_snapshot(missing_snapshot, case)


@pytest.mark.parametrize(
    ("case", "name"),
    [("POS", "focus1.md"), ("POS", "focus2.md"), ("NEG", "focus2.md")],
)
def test_m3_focus_artifact_directions(
    case: str,
    name: str,
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
) -> None:
    snapshot = tmp_path / f"{case.lower()}-{name}"
    shutil.copytree(benchmark_snapshots[case]["snapshot"], snapshot)
    target = snapshot / TOOL.ARTIFACT_DIR / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("forbidden", encoding="utf-8")
    with pytest.raises(TOOL.ValidationError, match="forbidden focus artifact"):
        TOOL.verify_snapshot(snapshot, case)


def test_snapshot_submodule_object_store_is_recursive(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    base = benchmark_snapshots["_base"]
    base_manifests = benchmark_snapshots["_base_manifests"]
    assert base_manifests["initial"] == base_manifests["after_pos"]
    assert base_manifests["initial"] == base_manifests["after_neg"]
    base_index = _index_semantics(base)
    for case in ("POS", "NEG"):
        assert _index_semantics(benchmark_snapshots[case]["snapshot"]) == base_index

    snapshot = tmp_path / "snapshot"
    shutil.copytree(
        benchmark_snapshots["POS"]["snapshot"],
        snapshot,
        symlinks=True,
        copy_function=shutil.copy2,
    )
    clean_oracle = TOOL.verify_snapshot(snapshot, "POS")
    assert clean_oracle["case"] == "POS"
    assert _index_semantics(snapshot) == base_index
    submodules = TOOL._submodule_repositories(snapshot)
    assert submodules
    git_dir = TOOL._git_dir(submodules[0])
    grafts = git_dir / "info/grafts"
    grafts.parent.mkdir(parents=True, exist_ok=True)
    head = TOOL._git(submodules[0], "rev-parse", "HEAD").decode().strip()
    grafts.write_text(head + "\n")
    with pytest.raises(TOOL.ValidationError, match="grafts closure"):
        TOOL.verify_snapshot(snapshot, "POS")


def test_ls_files_never_combines_stage_and_recurse_submodules() -> None:
    source = _TOOL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    ls_files_calls: list[set[str]] = []
    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        literals = {
            value.value
            for value in ast.walk(call)
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        }
        if "ls-files" in literals:
            ls_files_calls.append(literals)
    assert ls_files_calls
    assert any("--stage" in literals for literals in ls_files_calls)
    assert all(
        not {"--stage", "--recurse-submodules"} <= literals
        for literals in ls_files_calls
    )


def test_m10_filesystem_file_set_boundary_matrix_matches_rglob_reference(
    tmp_path: Path,
) -> None:
    """静止した木で non-directory と symlink の受理集合を旧実装へ束縛する。"""
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "regular.txt").write_text("regular\n", encoding="utf-8")
    directory = snapshot / "directory"
    directory.mkdir()
    (directory / "inside.txt").write_text("inside\n", encoding="utf-8")
    (snapshot / "file-link").symlink_to("regular.txt")
    (snapshot / "directory-link").symlink_to("directory", target_is_directory=True)
    (snapshot / "broken-link").symlink_to("missing-target")
    os.mkfifo(snapshot / "fifo")

    root_git = snapshot / ".git"
    (root_git / "objects").mkdir(parents=True)
    (root_git / "HEAD").write_text("ref: refs/heads/main\n", encoding="ascii")
    (root_git / "objects" / "hidden").write_bytes(b"hidden")

    nested_submodule = snapshot / "nested" / "submodule"
    nested_submodule.mkdir(parents=True)
    (nested_submodule / ".git").write_text(
        "gitdir: ../../.git/modules/nested/submodule\n", encoding="utf-8"
    )

    unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        unix_socket.bind(os.fspath(snapshot / "socket"))
        reference = _rglob_filesystem_file_set_reference(snapshot)
        actual = TOOL._filesystem_file_set(snapshot)
    finally:
        unix_socket.close()

    expected = {
        "regular.txt",
        "directory/inside.txt",
        "file-link",
        "directory-link",
        "broken-link",
        "fifo",
        "socket",
        "nested/submodule/.git",
    }
    assert reference == expected
    assert actual == reference
    assert "directory-link/inside.txt" not in actual


def test_filesystem_file_set_resolves_each_path_parent_per_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    parent = snapshot / "parent"
    parent.mkdir(parents=True)
    (snapshot / "empty").mkdir()
    (parent / "first").write_text("first\n", encoding="utf-8")
    (parent / "second").write_text("second\n", encoding="utf-8")
    resolve_calls: dict[Path, int] = {}
    original_resolve = Path.resolve

    def counted_resolve(path: Path, strict: bool = False) -> Path:
        resolve_calls[path] = resolve_calls.get(path, 0) + 1
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", counted_resolve)

    expected = {"parent/first", "parent/second"}
    assert TOOL._filesystem_file_set(snapshot) == expected
    assert resolve_calls[parent] == 2
    assert resolve_calls[snapshot] == 2


def test_filesystem_file_set_memoizes_resolved_parent_decision_per_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    resolved_parent = snapshot / "resolved-parent"
    resolved_parent.mkdir(parents=True)
    alias = snapshot / "alias"
    alias.symlink_to(resolved_parent, target_is_directory=True)
    first = resolved_parent / "first"
    second = alias / "second"
    first.write_text("first\n", encoding="utf-8")
    second.write_text("second\n", encoding="utf-8")
    selected_paths = (first, second)
    original_rglob = Path.rglob
    original_parents = Path.parents
    decision_calls: dict[Path, int] = {}

    def selected_rglob(path: Path, pattern: str):
        if path == snapshot and pattern == "*":
            return iter(selected_paths)
        return original_rglob(path, pattern)

    def counted_parents(path: Path):
        decision_calls[path] = decision_calls.get(path, 0) + 1
        return original_parents.__get__(path, type(path))

    monkeypatch.setattr(Path, "rglob", selected_rglob)
    monkeypatch.setattr(Path, "parents", property(counted_parents))

    expected = {"resolved-parent/first", "alias/second"}
    assert TOOL._filesystem_file_set(snapshot) == expected
    assert TOOL._filesystem_file_set(snapshot) == expected
    assert decision_calls[resolved_parent.resolve()] == 2


@pytest.mark.parametrize(
    "error_type", (OSError, RuntimeError), ids=("oserror", "symlink-loop")
)
def test_filesystem_file_set_parent_resolve_errors_propagate_per_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[Exception],
) -> None:
    snapshot = tmp_path / "snapshot"
    parent = snapshot / "parent"
    parent.mkdir(parents=True)
    (parent / "first").write_text("first\n", encoding="utf-8")
    (parent / "second").write_text("second\n", encoding="utf-8")
    original_resolve = Path.resolve
    parent_resolve_calls = 0

    def failing_resolve(path: Path, strict: bool = False) -> Path:
        nonlocal parent_resolve_calls
        if path == parent:
            parent_resolve_calls += 1
            if parent_resolve_calls == 2:
                raise error_type("parent resolve failed")
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", failing_resolve)

    with pytest.raises(error_type, match="parent resolve failed"):
        TOOL._filesystem_file_set(snapshot)
    assert parent_resolve_calls == 2


def test_filesystem_file_set_permission_error_directory_is_empty_subtree(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "snapshot"
    denied = snapshot / "denied"
    denied.mkdir(parents=True)
    (snapshot / "visible").write_text("visible\n", encoding="utf-8")
    (denied / "hidden").write_text("hidden\n", encoding="utf-8")
    denied_mode = stat.S_IMODE(denied.stat().st_mode)
    os.chmod(denied, 0o000)
    try:
        try:
            with os.scandir(denied) as entries:
                next(entries, None)
        except PermissionError:
            pass
        else:
            if os.geteuid() == 0:
                pytest.skip("running as root bypasses chmod(000) directory denial")
            pytest.fail("chmod(000) directory remained readable for a non-root user")

        reference = _rglob_filesystem_file_set_reference(snapshot)
        assert reference == {"visible"}
        assert TOOL._filesystem_file_set(snapshot) == reference
    finally:
        os.chmod(denied, denied_mode)


def test_m9_filesystem_file_set_skips_root_git_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    root_git = snapshot / ".git"
    root_git.mkdir(parents=True)
    poison = root_git / "poison"
    poison.write_bytes(b"unobservable stat failure")
    (snapshot / "visible").write_text("visible\n", encoding="utf-8")
    original_lstat = Path.lstat
    poison_lstat_calls = 0

    def fail_poison_lstat(path: Path):
        nonlocal poison_lstat_calls
        if path == poison:
            poison_lstat_calls += 1
            raise OSError("simulated NFS EIO")
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", fail_poison_lstat)

    assert TOOL._filesystem_file_set(snapshot) == {"visible"}
    assert poison_lstat_calls == 0


def _synthetic_relocatable_nested_snapshot(tmp_path: Path) -> Path:
    def initialize(repository: Path, filename: str) -> None:
        repository.mkdir()
        subprocess.run(
            ["git", "init"], cwd=repository, check=True, capture_output=True
        )
        (repository / filename).write_text(filename + "\n", encoding="utf-8")
        subprocess.run(["git", "add", filename], cwd=repository, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=T181",
                "-c",
                "user.email=t181@example.invalid",
                "commit",
                "-m",
                filename,
            ],
            cwd=repository,
            check=True,
            capture_output=True,
        )

    def add_submodule(repository: Path, source: Path, relative: str) -> None:
        subprocess.run(
            [
                "git",
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                os.fspath(source),
                relative,
            ],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=T181",
                "-c",
                "user.email=t181@example.invalid",
                "commit",
                "-m",
                f"add {relative}",
            ],
            cwd=repository,
            check=True,
            capture_output=True,
        )

    grandchild = tmp_path / "grandchild-source"
    initialize(grandchild, "grandchild.txt")
    child = tmp_path / "child-source"
    initialize(child, "child.txt")
    add_submodule(child, grandchild, "third_party/grandchild")
    snapshot = tmp_path / "base"
    initialize(snapshot, "root.txt")
    add_submodule(snapshot, child, "deps/child")
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "update",
            "--init",
            "--recursive",
        ],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "branch", "-M", TOOL.BRANCH],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )
    (snapshot / "mode-probe").write_bytes(b"mode\n")
    (snapshot / "mode-probe").chmod(0o750)
    (snapshot / "symlink-probe").symlink_to("root.txt")
    return snapshot


def test_shared_base_copy_preserves_metadata_and_relocates_submodules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _synthetic_relocatable_nested_snapshot(tmp_path)
    derived = tmp_path / "derived"
    child = base / "deps/child"
    subprocess.run(
        ["git", "update-index", "--skip-worktree", "root.txt"],
        cwd=base,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "update-index", "--assume-unchanged", "child.txt"],
        cwd=child,
        check=True,
        capture_output=True,
    )
    base_manifest_before = TOOL._metadata_manifest(base)
    base_paths_before = {
        path.relative_to(base).as_posix() for path in base.rglob("*")
    }
    assert base_paths_before
    base_index = _index_semantics(base)
    assert {
        relative: flag
        for *_, relative, flag in base_index["."]
    }["root.txt"] == "S"
    assert {
        relative: flag
        for *_, relative, flag in base_index["deps/child"]
    }["child.txt"].islower()
    observed = False

    def inspect_copy(
        repo: Path,
        snapshot: Path,
        case: str,
        golden: dict[str, bytes],
    ) -> dict[str, Any]:
        nonlocal observed
        assert repo == base.resolve()
        assert snapshot == derived.resolve()
        assert case == "NEG"
        assert golden == {}
        assert TOOL._metadata_manifest(snapshot) == base_manifest_before
        assert _index_semantics(snapshot) == base_index
        _assert_relocated_submodules(snapshot)
        observed = True
        return {"copied": True}

    monkeypatch.setattr(TOOL, "_finish_snapshot_case", inspect_copy)
    assert TOOL._derive_snapshot_from_base(
        base,
        base,
        derived,
        tmp_path,
        "NEG",
        prepared_golden={},
    ) == {"copied": True}
    assert observed is True
    assert TOOL._metadata_manifest(base) == base_manifest_before
    assert derived.is_dir()
    derived_paths = {
        path.relative_to(derived).as_posix() for path in derived.rglob("*")
    }
    assert derived_paths
    assert derived_paths == base_paths_before

    base_inodes = {
        (path.lstat().st_dev, path.lstat().st_ino)
        for path in base.rglob("*")
        if stat.S_ISREG(path.lstat().st_mode)
    }
    derived_inodes = {
        (path.lstat().st_dev, path.lstat().st_ino)
        for path in derived.rglob("*")
        if stat.S_ISREG(path.lstat().st_mode)
    }
    assert base_inodes.isdisjoint(derived_inodes)


def test_build_snapshot_public_path_delegates_in_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = (tmp_path / "repo").resolve()
    snapshot = (tmp_path / "snapshot").resolve()
    sessions_root = tmp_path / "sessions"
    golden = {"golden.txt": b"golden\n"}
    result = {"public": True}
    calls: list[tuple[Any, ...]] = []

    def resolve(candidate_repo: Path, candidate_snapshot: Path) -> tuple[Path, Path]:
        calls.append(("resolve", candidate_repo, candidate_snapshot))
        return repo, snapshot

    def prepare(
        candidate_repo: Path, candidate_sessions: Path, case: str
    ) -> dict[str, bytes]:
        calls.append(("prepare", candidate_repo, candidate_sessions, case))
        return golden

    def build(candidate_repo: Path, candidate_snapshot: Path) -> Path:
        calls.append(("build", candidate_repo, candidate_snapshot))
        return candidate_snapshot

    def finish(
        candidate_repo: Path,
        candidate_snapshot: Path,
        case: str,
        candidate_golden: dict[str, bytes],
    ) -> dict[str, bool]:
        calls.append(
            (
                "finish",
                candidate_repo,
                candidate_snapshot,
                case,
                candidate_golden,
            )
        )
        return result

    monkeypatch.setattr(TOOL, "_resolve_snapshot_destination", resolve)
    monkeypatch.setattr(TOOL, "_prepare_snapshot_case", prepare)
    monkeypatch.setattr(TOOL, "_build_snapshot_base", build)
    monkeypatch.setattr(TOOL, "_finish_snapshot_case", finish)

    assert TOOL.build_snapshot(repo, snapshot, sessions_root, "POS") is result
    assert calls == [
        ("resolve", repo, snapshot),
        ("prepare", repo, sessions_root, "POS"),
        ("build", repo, snapshot),
        ("finish", repo, snapshot, "POS", golden),
    ]


@pytest.mark.parametrize(
    "submodule_relative",
    ["deps/child", "deps/child/third_party/grandchild"],
)
def test_snapshot_relocation_preflight_rejects_absolute_gitdir(
    tmp_path: Path, submodule_relative: str,
) -> None:
    base = _synthetic_relocatable_nested_snapshot(tmp_path)
    TOOL._preflight_snapshot_relocation(base)
    submodule = base / submodule_relative
    git_dir = TOOL._git_dir(submodule)
    (submodule / ".git").write_text(
        f"gitdir: {git_dir}\n", encoding="utf-8"
    )

    with pytest.raises(
        TOOL.ValidationError, match="absolute submodule gitdir"
    ) as caught:
        TOOL._preflight_snapshot_relocation(base)
    assert caught.value.rc == TOOL.RC_SNAPSHOT


@pytest.mark.parametrize(
    "submodule_relative",
    ["deps/child", "deps/child/third_party/grandchild"],
)
def test_snapshot_relocation_preflight_rejects_absolute_core_worktree(
    tmp_path: Path, submodule_relative: str,
) -> None:
    base = _synthetic_relocatable_nested_snapshot(tmp_path)
    TOOL._preflight_snapshot_relocation(base)
    submodule = base / submodule_relative
    git_dir = TOOL._git_dir(submodule)
    subprocess.run(
        [
            "git",
            "config",
            "--file",
            os.fspath(git_dir / "config"),
            "core.worktree",
            os.fspath(submodule.resolve()),
        ],
        check=True,
        capture_output=True,
    )

    with pytest.raises(
        TOOL.ValidationError, match="absolute submodule core.worktree"
    ) as caught:
        TOOL._preflight_snapshot_relocation(base)
    assert caught.value.rc == TOOL.RC_SNAPSHOT


def test_derived_preflight_rejects_path_dependent_absolute_core_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _synthetic_relocatable_nested_snapshot(tmp_path)
    derived = tmp_path / "derived"
    submodule_relative = Path("deps/child")
    submodule = base / submodule_relative
    git_dir = TOOL._git_dir(submodule)
    derived_git_dir = derived / git_dir.relative_to(base)
    included = git_dir / "derived-only.conf"
    subprocess.run(
        [
            "git",
            "config",
            "--file",
            os.fspath(included),
            "core.worktree",
            os.fspath((derived / submodule_relative).resolve()),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "config",
            "--file",
            os.fspath(git_dir / "config"),
            f"includeIf.gitdir:{derived_git_dir}.path",
            included.name,
        ],
        check=True,
        capture_output=True,
    )
    TOOL._preflight_snapshot_relocation(base)
    monkeypatch.setattr(
        TOOL,
        "_finish_snapshot_case",
        lambda *_args: pytest.fail("derived preflight did not reject the snapshot"),
    )

    with pytest.raises(
        TOOL.ValidationError, match="absolute submodule core.worktree"
    ) as caught:
        TOOL._derive_snapshot_from_base(
            base,
            base,
            derived,
            tmp_path,
            "NEG",
            prepared_golden={},
        )
    assert caught.value.rc == TOOL.RC_SNAPSHOT


def _synthetic_nested_submodule_snapshot(
    tmp_path: Path,
) -> tuple[Path, Path, str]:
    child = tmp_path / "child-source"
    child.mkdir()
    subprocess.run(["git", "init"], cwd=child, check=True, capture_output=True)
    (child / "child.txt").write_text("child\n", encoding="utf-8")
    subprocess.run(["git", "add", "child.txt"], cwd=child, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=T181",
            "-c",
            "user.email=t181@example.invalid",
            "commit",
            "-m",
            "child",
        ],
        cwd=child,
        check=True,
        capture_output=True,
    )
    nested_gitlink = TOOL._git(child, "rev-parse", "HEAD").decode().strip()
    (child / ".gitmodules").write_text(
        '[submodule "third_party/grandchild"]\n'
        "\tpath = third_party/grandchild\n"
        "\turl = https://example.invalid/grandchild.git\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", ".gitmodules"], cwd=child, check=True)
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{nested_gitlink},third_party/grandchild",
        ],
        cwd=child,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=T181",
            "-c",
            "user.email=t181@example.invalid",
            "commit",
            "-m",
            "declare uninitialized nested submodule",
        ],
        cwd=child,
        check=True,
        capture_output=True,
    )

    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    subprocess.run(["git", "init"], cwd=snapshot, check=True, capture_output=True)
    (snapshot / "root.txt").write_text("root\n", encoding="utf-8")
    subprocess.run(["git", "add", "root.txt"], cwd=snapshot, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            os.fspath(child),
            "deps/child",
        ],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=T181",
            "-c",
            "user.email=t181@example.invalid",
            "commit",
            "-m",
            "snapshot",
        ],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "branch", "-M", TOOL.BRANCH],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )
    submodule = snapshot / "deps/child"
    subprocess.run(
        ["git", "checkout", "--detach", "HEAD"],
        cwd=submodule,
        check=True,
        capture_output=True,
    )
    return snapshot, submodule, nested_gitlink


def test_uninitialized_nested_submodule_is_manifested_and_accepted(
    tmp_path: Path,
) -> None:
    snapshot, submodule, nested_gitlink = _synthetic_nested_submodule_snapshot(
        tmp_path
    )

    TOOL._seal_git_object_closure(snapshot)
    reasons, manifests, submodules = TOOL._git_closure_reasons(snapshot, ())

    assert reasons == []
    assert [row["repository"] for row in manifests] == [".", "deps/child"]
    assert submodules == [
        {
            "path": "deps/child",
            "gitlink_commit": TOOL._git(
                snapshot, "rev-parse", "HEAD:deps/child"
            ).decode().strip(),
            "initialization": "initialized",
        },
        {
            "path": "deps/child/third_party/grandchild",
            "gitlink_commit": nested_gitlink,
            "initialization": "uninitialized",
        },
    ]
    assert TOOL._expected_filesystem_files(snapshot, ()) == {
        ".gitmodules",
        "root.txt",
        "deps/child/.git",
        "deps/child/.gitmodules",
        "deps/child/child.txt",
    }
    root_entries = TOOL._index_stage_entries(snapshot)
    child_entries = TOOL._index_stage_entries(submodule)
    assert any(
        mode == "160000" and stage == "0" and relative == "deps/child"
        for mode, _, stage, relative in root_entries
    )
    assert all(
        relative != "deps/child/child.txt"
        for _, _, _, relative in root_entries
    )
    assert any(
        mode == "100644" and stage == "0" and relative == "child.txt"
        for mode, _, stage, relative in child_entries
    )


def test_leading_dash_untracked_path_is_hashed_as_path(
    tmp_path: Path,
) -> None:
    snapshot, _, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    TOOL._seal_git_object_closure(snapshot)
    relative = "-answer"
    (snapshot / relative).write_bytes(b"t904 leading-dash untracked artifact\n")

    reasons, _, _ = TOOL._git_closure_reasons(snapshot, (relative,))
    assert reasons == []

    (snapshot / relative).write_bytes((snapshot / "root.txt").read_bytes())
    contaminated_reasons, _, _ = TOOL._git_closure_reasons(
        snapshot, (relative,)
    )
    assert contaminated_reasons == [
        "untracked artifact entered git object store: -answer"
    ]


def test_option_named_untracked_path_is_hashed_not_stdin(
    tmp_path: Path,
) -> None:
    """Without ``--``, Git hashes empty stdin and misses this reachable blob."""
    snapshot, _, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    TOOL._seal_git_object_closure(snapshot)
    relative = "--stdin"
    (snapshot / relative).write_bytes((snapshot / "root.txt").read_bytes())

    reasons, _, _ = TOOL._git_closure_reasons(snapshot, (relative,))
    assert reasons == ["untracked artifact entered git object store: --stdin"]


def test_uninitialized_nested_submodule_gitlink_pin_rejects_change(
    tmp_path: Path,
) -> None:
    snapshot, submodule, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    _, before = TOOL._submodule_inventory(snapshot)
    expected_sha256 = TOOL._submodule_manifest_sha256(before)
    replacement = TOOL._git(submodule, "rev-parse", "HEAD").decode().strip()
    subprocess.run(
        [
            "git",
            "update-index",
            "--cacheinfo",
            f"160000,{replacement},third_party/grandchild",
        ],
        cwd=submodule,
        check=True,
        capture_output=True,
    )
    _, after = TOOL._submodule_inventory(snapshot)
    with pytest.raises(
        TOOL.ValidationError,
        match="submodule initialization or gitlink state mismatch",
    ):
        TOOL._assert_submodule_manifest_sha256(after, expected_sha256)


def test_initialized_submodule_answer_object_injection_is_rejected(
    tmp_path: Path,
) -> None:
    snapshot, submodule, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    TOOL._seal_git_object_closure(snapshot)
    answer = tmp_path / "answer.md"
    answer.write_text("historical answer object\n", encoding="utf-8")
    subprocess.run(
        ["git", "hash-object", "-w", os.fspath(answer)],
        cwd=submodule,
        check=True,
        capture_output=True,
    )
    reasons, _, _ = TOOL._git_closure_reasons(snapshot, ())
    assert any(
        "deps/child: git object store contains unreachable objects" in reason
        for reason in reasons
    )


def test_pos_neg_submodule_initialization_state_mismatch_is_rejected(
    benchmark_snapshots: dict[str, Any],
    tmp_path: Path,
) -> None:
    _, slots = _schedule(tmp_path / "schedule.json", benchmark_snapshots)
    for slot in slots:
        if slot["case"] == "NEG":
            slot["submodule_manifest_sha256"] = "f" * 64
    _, reasons = TOOL._validate_schedule({"slots": slots})
    assert (
        "POS/NEG submodule initialization and gitlink state mismatch" in reasons
    )


def test_git_answer_object_reinjection_is_rejected(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    snapshot = tmp_path / "snapshot"
    shutil.copytree(benchmark_snapshots["NEG"]["snapshot"], snapshot)
    subprocess.run(
        ["git", "-c", "protocol.file.allow=always", "fetch", str(_ROOT), TOOL.ARTIFACT_COMMIT],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )
    with pytest.raises(TOOL.ValidationError, match="forbidden git object"):
        TOOL.verify_snapshot(snapshot, "NEG")


def test_find_rollout_session_meta_encoding_and_payload_field_equivalence(
    tmp_path: Path,
) -> None:
    session_id = "target-session"
    literal = (
        '{"type":"session_meta","payload":'
        '{"id":"target-session","session_id":"target-session"}}'
    )
    escaped_type = "".join(f"\\u00{ord(char):02x}" for char in "session_meta")
    variants = {
        "literal": literal.encode(),
        "unicode-escape": (
            f'{{"type":"{escaped_type}","payload":{{"id":"{session_id}"}}}}'
        ).encode(),
        "utf16-le": b"\xff\xfe" + literal.encode("utf-16-le"),
        "utf16-be": b"\xfe\xff" + literal.encode("utf-16-be"),
        "utf32-le": b"\xff\xfe\x00\x00" + literal.encode("utf-32-le"),
        "utf32-be": b"\x00\x00\xfe\xff" + literal.encode("utf-32-be"),
        "reordered-keys": (
            b'{"payload":{"session_id":"target-session"},'
            b'"type":"session_meta"}'
        ),
        "id-only": b'{"type":"session_meta","payload":{"id":"target-session"}}',
        "session-id-only": (
            b'{"type":"session_meta",'
            b'"payload":{"session_id":"target-session"}}'
        ),
        "distinct-fields": (
            b'{"type":"session_meta",'
            b'"payload":{"id":"other","session_id":"target-session"}}'
        ),
    }

    for name, content in variants.items():
        sessions_root = tmp_path / name
        sessions_root.mkdir()
        rollout = sessions_root / f"rollout-{name}.jsonl"
        rollout.write_bytes(content)

        assert TOOL._find_rollout(sessions_root, session_id) == rollout.resolve(), name


def test_find_rollout_checks_later_session_meta_in_same_file(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout-multiple-meta.jsonl"
    rollout.write_bytes(
        b'{"type":"session_meta","payload":{"id":"unrelated"}}\n'
        b'{"type":"session_meta","payload":{"id":"target-session"}}\n'
    )

    assert TOOL._find_rollout(tmp_path, "target-session") == rollout.resolve()


def test_find_rollout_preserves_zero_and_duplicate_failure(tmp_path: Path) -> None:
    session_id = "target-session"
    for match_count in (0, 2):
        sessions_root = tmp_path / f"matches-{match_count}"
        sessions_root.mkdir()
        for index in range(match_count):
            (sessions_root / f"rollout-{index}.jsonl").write_bytes(
                b'{"type":"session_meta","payload":{"id":"target-session"}}'
            )

        expected = (
            f"session {session_id} rollout count is {match_count}, expected 1"
        )
        with pytest.raises(TOOL.ValidationError) as excinfo:
            TOOL._find_rollout(sessions_root, session_id)
        assert str(excinfo.value) == expected, match_count
        assert excinfo.value.rc == 21, match_count


def test_find_rollout_session_meta_scanner_ignores_decode_errors_and_non_objects(
    tmp_path: Path,
) -> None:
    (tmp_path / "rollout-decoys.jsonl").write_bytes(
        b'{"type":"session_meta",}\n'
        b'{"type":"session_meta","payload":{}}\xff\n'
        b'"session_meta"\n'
    )
    rollout = tmp_path / "rollout-target.jsonl"
    rollout.write_bytes(
        b'{"type":"session_meta","payload":{"id":"target-session"}}\n'
    )

    assert TOOL._find_rollout(tmp_path, "target-session") == rollout.resolve()


def test_find_rollout_session_meta_scanner_parses_only_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate_lines = (
        b'{"type":"event_msg","payload":{"note":"session_meta"}}\n',
        b'{"type":"event_msg","payload":{"note":"\\u0061"}}\n',
        b'{"type":"session_meta","payload":{"id":"target-session"}}\n',
        b"\x00\n",
        b'{"type":"session_meta",}\n',
    )
    rollout = tmp_path / "rollout-candidates.jsonl"
    rollout.write_bytes(
        b'{"type":"event_msg","payload":{"note":"ordinary"}}\n' * 1000
        + b"".join(candidate_lines)
    )
    real_loads = TOOL.json.loads
    parse_count = 0

    def counted_loads(line: bytes) -> Any:
        nonlocal parse_count
        parse_count += 1
        return real_loads(line)

    monkeypatch.setattr(TOOL.json, "loads", counted_loads)

    assert TOOL._find_rollout(tmp_path, "target-session") == rollout.resolve()
    assert parse_count == len(candidate_lines)


def test_find_rollout_session_meta_scanner_propagates_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "rollout-candidate.jsonl").write_bytes(
        b'{"type":"session_meta","payload":{"id":"target-session"}}\n'
    )

    def raise_value_error(_: bytes) -> Any:
        raise ValueError("candidate sentinel")

    monkeypatch.setattr(TOOL.json, "loads", raise_value_error)

    with pytest.raises(ValueError, match="candidate sentinel"):
        TOOL._find_rollout(tmp_path, "target-session")


@pytest.mark.parametrize(
    "escape_index",
    range(len("session_meta")),
    ids=[f"{index}-{char}" for index, char in enumerate("session_meta")],
)
def test_find_rollout_session_meta_single_escape_variants(
    tmp_path: Path, escape_index: int
) -> None:
    type_name = "session_meta"
    escaped_type = (
        type_name[:escape_index]
        + f"\\u00{ord(type_name[escape_index]):02x}"
        + type_name[escape_index + 1 :]
    )
    rollout = tmp_path / f"rollout-single-escape-{escape_index}.jsonl"
    rollout.write_bytes(
        (
            f'{{"type":"{escaped_type}",'
            '"payload":{"id":"target-session"}}'
        ).encode()
    )

    assert TOOL._find_rollout(tmp_path, "target-session") == rollout.resolve()


@pytest.mark.parametrize(
    ("variant", "encoding"),
    (
        ("utf16-le", "utf-16-le"),
        ("utf16-be", "utf-16-be"),
        ("utf32-le", "utf-32-le"),
        ("utf32-be", "utf-32-be"),
    ),
)
def test_find_rollout_session_meta_bomless_utf_variants(
    tmp_path: Path, variant: str, encoding: str
) -> None:
    content = (
        '{"type":"session_meta","payload":{"id":"target-session"}}'
    ).encode(encoding)
    rollout = tmp_path / f"rollout-bomless-{variant}.jsonl"
    rollout.write_bytes(content)

    assert TOOL._find_rollout(tmp_path, "target-session") == rollout.resolve()


def test_find_rollout_continues_after_bad_candidate_in_same_file(
    tmp_path: Path,
) -> None:
    rollout = tmp_path / "rollout-same-file.jsonl"
    rollout.write_bytes(
        b'{"type":"session_meta",}\n'
        b'{"type":"session_meta","payload":{}}\xff\n'
        b'"session_meta"\n'
        b'{"type":"session_meta","payload":{"id":"target-session"}}\n'
    )

    assert TOOL._find_rollout(tmp_path, "target-session") == rollout.resolve()


def test_find_rollout_ignores_unreadable_file_before_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unreadable = tmp_path / "rollout-0-unreadable.jsonl"
    unreadable.write_bytes(b'{"type":"session_meta"}\n')
    rollout = tmp_path / "rollout-9-target.jsonl"
    rollout.write_bytes(
        b'{"type":"session_meta","payload":{"id":"target-session"}}\n'
    )
    real_open = Path.open

    def selective_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        mode = args[0] if args else kwargs.get("mode", "r")
        if path == unreadable and mode == "rb":
            raise PermissionError("unreadable rollout sentinel")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", selective_open)

    assert TOOL._find_rollout(tmp_path, "target-session") == rollout.resolve()


def test_find_rollout_ignores_empty_and_blank_rollouts(tmp_path: Path) -> None:
    (tmp_path / "rollout-0-empty.jsonl").write_bytes(b"")
    (tmp_path / "rollout-1-blank.jsonl").write_bytes(b"\n\r\n\n")
    rollout = tmp_path / "rollout-9-target.jsonl"
    rollout.write_bytes(
        b'{"type":"session_meta","payload":{"id":"target-session"}}\n'
    )

    assert TOOL._find_rollout(tmp_path, "target-session") == rollout.resolve()


def _session_meta_bytes(session_id: str, *, field: str = "id") -> bytes:
    return (
        json.dumps(
            {"type": "session_meta", "payload": {field: session_id}},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _write_rollout(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _install_rollout_pin(
    monkeypatch: pytest.MonkeyPatch,
    *,
    label: str,
    session_id: str,
    content: bytes,
) -> None:
    monkeypatch.setitem(TOOL.SESSION_IDS, label, session_id)
    monkeypatch.setitem(
        TOOL.ROLLOUT_SHA256, label, hashlib.sha256(content).hexdigest()
    )


def test_find_rollout_pinned_checks_content_before_returning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-content-check"
    session_id = "content-target"
    candidate_content = _session_meta_bytes("different-session")
    candidate = _write_rollout(
        tmp_path / f"rollout-named-{session_id}.jsonl", candidate_content
    )
    fallback = _write_rollout(
        tmp_path / "rollout-nontypical.jsonl", _session_meta_bytes(session_id)
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=candidate_content,
    )

    assert candidate != fallback
    assert (
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
        == fallback.resolve()
    )


def test_find_rollout_pinned_requires_exactly_one_named_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-candidate-count"
    session_id = "candidate-count-target"
    pinned_content = _session_meta_bytes(session_id)
    for branch in ("a", "b"):
        _write_rollout(
            tmp_path / branch / f"rollout-{branch}-{session_id}.jsonl",
            pinned_content,
        )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=pinned_content,
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        f"session {session_id} rollout count is 2, expected 1"
    )


def test_find_rollout_pinned_sha_mismatch_falls_back_to_duplicate_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-sha-fallback"
    session_id = "sha-fallback-target"
    candidate = _write_rollout(
        tmp_path / "candidate" / f"rollout-named-{session_id}.jsonl",
        _session_meta_bytes(session_id),
    )
    duplicate = _write_rollout(
        tmp_path / "duplicate" / "rollout-nontypical.jsonl",
        _session_meta_bytes(session_id),
    )
    monkeypatch.setitem(TOOL.SESSION_IDS, label, session_id)
    monkeypatch.setitem(
        TOOL.ROLLOUT_SHA256,
        label,
        hashlib.sha256(b"different pinned bytes").hexdigest(),
    )

    assert candidate != duplicate
    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        f"session {session_id} rollout count is 2, expected 1"
    )


def test_find_rollout_pinned_requires_sha_pin_eligibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-missing-sha-pin"
    session_id = "missing-sha-pin-target"
    content = _session_meta_bytes(session_id)
    _write_rollout(tmp_path / f"rollout-named-{session_id}.jsonl", content)
    _write_rollout(tmp_path / "rollout-nontypical.jsonl", content)
    monkeypatch.setitem(TOOL.SESSION_IDS, label, session_id)
    monkeypatch.delitem(TOOL.ROLLOUT_SHA256, label, raising=False)
    monkeypatch.setattr(
        TOOL, "_verify_rollout_sha", lambda *args, **kwargs: None
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
    assert excinfo.value.rc == TOOL.RC_SESSION


def test_find_rollout_pinned_requires_label_id_pairing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-cross-wired-label"
    label_session_id = "label-session"
    requested_session_id = "requested-session"
    content = _session_meta_bytes(requested_session_id)
    candidate = _write_rollout(
        tmp_path / f"rollout-named-{requested_session_id}.jsonl", content
    )
    _write_rollout(tmp_path / "rollout-nontypical.jsonl", content)
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=label_session_id,
        content=content,
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(
            tmp_path, requested_session_id, pinned_label=label
        )
    assert candidate.exists()
    assert excinfo.value.rc == TOOL.RC_SESSION


@pytest.mark.parametrize(
    "depth_parts",
    (
        pytest.param(("a",), id="depth-1"),
        pytest.param(("a", "b", "c", "d", "e"), id="depth-5"),
    ),
)
def test_find_rollout_pinned_rglob_reaches_arbitrary_depth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    depth_parts: tuple[str, ...],
) -> None:
    label = "test-arbitrary-depth"
    session_id = f"nested-{len(depth_parts)}"
    content = _session_meta_bytes(session_id)
    candidate = _write_rollout(
        tmp_path.joinpath(
            *depth_parts, f"rollout-deep-{session_id}.jsonl"
        ),
        content,
    )
    _write_rollout(
        tmp_path / "elsewhere" / "rollout-nontypical.jsonl", content
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )

    assert (
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
        == candidate.resolve()
    )


def test_find_rollout_pinned_returns_resolved_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-resolved-symlink"
    session_id = "resolved-symlink-target"
    content = _session_meta_bytes(session_id)
    target = _write_rollout(tmp_path / "outside" / "target.jsonl", content)
    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir()
    candidate = sessions_root / f"rollout-link-{session_id}.jsonl"
    candidate.symlink_to(target)
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )

    assert (
        TOOL._find_rollout(sessions_root, session_id, pinned_label=label)
        == target.resolve()
    )
    assert candidate != target.resolve()


def test_find_rollout_pinned_zero_named_candidates_uses_full_scan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-zero-named"
    session_id = "zero-named-target"
    content = _session_meta_bytes(session_id)
    fallback = _write_rollout(
        tmp_path / "rollout-nontypical.jsonl", content
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )

    assert (
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
        == fallback.resolve()
    )


@pytest.mark.parametrize("pinned_label", (None, "unknown-label"))
@pytest.mark.parametrize(
    "session_id_text",
    (
        pytest.param("../x*?[/e\u0301 trailing ", id="metacharacters"),
        pytest.param("Opaque]UPPER/Segment", id="bracket-upper-slash"),
    ),
)
def test_find_rollout_ineligible_pin_preserves_opaque_session_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pinned_label: str | None,
    session_id_text: str,
) -> None:
    separator_probes: list[str] = []

    class OpaqueSessionId(str):
        def __contains__(self, value: str) -> bool:
            separator_probes.append(value)
            return super().__contains__(value)

    session_id = OpaqueSessionId(session_id_text)
    rollout = _write_rollout(
        tmp_path / "rollout-opaque.jsonl", _session_meta_bytes(session_id)
    )
    patterns: list[str] = []
    escape_calls: list[str] = []
    real_rglob = TOOL.Path.rglob
    real_escape = TOOL.glob.escape

    def observe_rglob(path: Path, pattern: str) -> Any:
        patterns.append(pattern)
        return real_rglob(path, pattern)

    def observe_escape(value: str) -> str:
        escape_calls.append(value)
        return real_escape(value)

    monkeypatch.setattr(TOOL.Path, "rglob", observe_rglob)
    monkeypatch.setattr(TOOL.glob, "escape", observe_escape)

    assert (
        TOOL._find_rollout(
            tmp_path, session_id, pinned_label=pinned_label
        )
        == rollout.resolve()
    )
    assert patterns == ["rollout-*.jsonl"]
    assert escape_calls == []
    assert separator_probes == []


def test_find_rollout_pinned_glob_metacharacters_are_literal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-glob-escape"
    session_id = "literal*?x"
    content = _session_meta_bytes(session_id)
    candidate = _write_rollout(
        tmp_path / f"rollout-exact-{session_id}.jsonl", content
    )
    _write_rollout(
        tmp_path / "rollout-wild-literalZZx.jsonl", content
    )
    _write_rollout(tmp_path / "rollout-nontypical.jsonl", content)
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )

    assert (
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
        == candidate.resolve()
    )


def test_find_rollout_pinned_permission_error_is_speculative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-permission-fallback"
    session_id = "permission-fallback-target"
    content = _session_meta_bytes(session_id)
    candidate = _write_rollout(
        tmp_path / f"rollout-named-{session_id}.jsonl", content
    )
    fallback = _write_rollout(
        tmp_path / "rollout-nontypical.jsonl", content
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )
    real_matches = TOOL._rollout_matches_session
    chmod_applied = False

    def chmod_after_match(path: Path, requested_id: str) -> bool:
        nonlocal chmod_applied
        matched = real_matches(path, requested_id)
        if path == candidate and matched and not chmod_applied:
            os.chmod(candidate, 0o000)
            chmod_applied = True
        return matched

    monkeypatch.setattr(TOOL, "_rollout_matches_session", chmod_after_match)
    try:
        assert (
            TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
            == fallback.resolve()
        )
        assert chmod_applied
        with pytest.raises(PermissionError):
            candidate.read_bytes()
    finally:
        os.chmod(candidate, 0o600)


def test_find_rollout_pinned_memory_error_is_speculative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-memory-fallback"
    session_id = "memory-fallback-target"
    content = _session_meta_bytes(session_id)
    _write_rollout(
        tmp_path / f"rollout-named-{session_id}.jsonl", content
    )
    _write_rollout(tmp_path / "rollout-nontypical.jsonl", content)
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )

    def raise_memory_error(path: Path, requested_label: str) -> None:
        raise MemoryError("sha verification sentinel")

    monkeypatch.setattr(TOOL, "_verify_rollout_sha", raise_memory_error)

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
    assert excinfo.value.rc == TOOL.RC_SESSION


def test_find_rollout_pinned_does_not_catch_base_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-base-exception"
    session_id = "base-exception-target"
    content = _session_meta_bytes(session_id)
    _write_rollout(
        tmp_path / f"rollout-named-{session_id}.jsonl", content
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )
    real_matches = TOOL._rollout_matches_session
    calls = 0

    def interrupt(path: Path, requested_id: str) -> bool:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt("base exception sentinel")
        return real_matches(path, requested_id)

    monkeypatch.setattr(TOOL, "_rollout_matches_session", interrupt)

    with pytest.raises(KeyboardInterrupt, match="base exception sentinel"):
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
    assert calls == 1


@pytest.mark.parametrize("variant", ("unicode-escape", "utf16-le", "bad-prefix"))
def test_find_rollout_pinned_preserves_session_meta_encodings_and_bad_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    variant: str,
) -> None:
    label = f"test-{variant}"
    session_id = f"encoded-{variant}"
    literal = (
        f'{{"type":"session_meta","payload":{{"id":"{session_id}"}}}}'
    )
    if variant == "unicode-escape":
        escaped_type = "".join(
            f"\\u00{ord(char):02x}" for char in "session_meta"
        )
        content = literal.replace("session_meta", escaped_type).encode() + b"\n"
    elif variant == "utf16-le":
        content = literal.encode("utf-16-le")
    else:
        content = b'{"type":"session_meta",}\n' + literal.encode() + b"\n"
    candidate = _write_rollout(
        tmp_path / "a" / "b" / f"rollout-encoded-{session_id}.jsonl",
        content,
    )
    _write_rollout(
        tmp_path / "duplicate" / "rollout-nontypical.jsonl",
        _session_meta_bytes(session_id),
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )

    assert (
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
        == candidate.resolve()
    )


def test_find_rollout_pinned_candidate_value_error_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-value-error-propagation"
    session_id = "value-error-propagation-target"
    content = _session_meta_bytes(session_id)
    _write_rollout(
        tmp_path / f"rollout-named-{session_id}.jsonl", content
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )
    real_loads = TOOL.json.loads
    raised = False

    def raise_once(line: bytes) -> Any:
        nonlocal raised
        if not raised:
            raised = True
            raise ValueError("fast candidate sentinel")
        return real_loads(line)

    monkeypatch.setattr(TOOL.json, "loads", raise_once)

    with pytest.raises(ValueError, match="fast candidate sentinel"):
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
    assert raised


def test_find_rollout_pinned_parses_only_named_candidate_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-pinned-parse-count"
    session_id = "pinned-parse-count-target"
    candidate_lines = (
        b'{"type":"event_msg","payload":{"note":"session_meta"}}\n',
        b'{"type":"event_msg","payload":{"note":"\\u0061"}}\n',
        _session_meta_bytes(session_id),
    )
    content = b'{"type":"event_msg","payload":{}}\n' * 1000 + b"".join(
        candidate_lines
    )
    candidate = _write_rollout(
        tmp_path / f"rollout-named-{session_id}.jsonl", content
    )
    _write_rollout(
        tmp_path / "rollout-0-decoy.jsonl",
        _session_meta_bytes("unrelated") * 7,
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )
    real_loads = TOOL.json.loads
    parse_count = 0

    def counted_loads(line: bytes) -> Any:
        nonlocal parse_count
        parse_count += 1
        return real_loads(line)

    monkeypatch.setattr(TOOL.json, "loads", counted_loads)

    assert (
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
        == candidate.resolve()
    )
    assert parse_count == len(candidate_lines)


def test_find_rollout_pinned_skips_unrelated_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    label = "test-unrelated-value-error"
    session_id = "unrelated-value-error-target"
    content = _session_meta_bytes(session_id)
    candidate = _write_rollout(
        tmp_path / f"rollout-z-{session_id}.jsonl", content
    )
    _write_rollout(
        tmp_path / "rollout-0-poison.jsonl",
        b'{"type":"session_meta","payload":{"value":'
        + b"9" * 10_000
        + b"}}\n",
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=session_id,
        content=content,
    )

    with pytest.raises(ValueError):
        TOOL._find_rollout(tmp_path, session_id)
    assert (
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)
        == candidate.resolve()
    )


@pytest.mark.parametrize("verify_source_sha", (True, False))
def test_derive_independent_golden_wires_pins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    verify_source_sha: bool,
) -> None:
    calls: list[tuple[str, str | None]] = []

    def observe(
        sessions_root: Path,
        session_id: str,
        *,
        pinned_label: str | None = None,
    ) -> Path:
        calls.append((session_id, pinned_label))
        if len(calls) == 3:
            raise RuntimeError("wiring observed")
        return tmp_path / f"{pinned_label}.jsonl"

    monkeypatch.setattr(TOOL, "_find_rollout", observe)

    with pytest.raises(RuntimeError, match="wiring observed"):
        TOOL.derive_independent_golden(
            tmp_path, tmp_path, verify_source_sha=verify_source_sha
        )
    assert calls == [
        (TOOL.SESSION_IDS[label], label)
        for label in ("author", "fix1", "fix2")
    ]


@pytest.mark.parametrize("case", ("POS", "NEG"))
@pytest.mark.parametrize("verify_source", (True, False))
def test_render_prompt_wires_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    verify_source: bool,
) -> None:
    calls: list[tuple[str, str | None]] = []

    def observe(
        sessions_root: Path,
        session_id: str,
        *,
        pinned_label: str | None = None,
    ) -> Path:
        calls.append((session_id, pinned_label))
        raise RuntimeError("wiring observed")

    monkeypatch.setattr(TOOL, "_find_rollout", observe)

    with pytest.raises(RuntimeError, match="wiring observed"):
        TOOL.render_prompt(
            tmp_path,
            case,
            tmp_path / "new-root",
            verify_source=verify_source,
        )
    assert calls == [(TOOL.SESSION_IDS[case], case)]


@pytest.mark.parametrize("replacement_count", [0, 9, 10])
def test_prompt_replacement_count_zero_expected_and_excess(
    replacement_count: int,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_rollout = TOOL._find_rollout(
        _HISTORICAL_SESSIONS, TOOL.SESSION_IDS["POS"]
    )
    canonical_message = TOOL.extract_user_message(source_rollout)
    if replacement_count == 0:
        message = canonical_message.replace(TOOL.OLD_ROOT, "/neutral-old-root")
    elif replacement_count == 10:
        message = canonical_message + "\n" + TOOL.OLD_ROOT
    else:
        message = canonical_message
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        TOOL, "_find_rollout", lambda *args, **kwargs: rollout
    )
    monkeypatch.setattr(TOOL, "_verify_rollout_sha", lambda *_: None)
    monkeypatch.setattr(TOOL, "extract_user_message", lambda *_: message)
    if replacement_count == TOOL.PROMPT_SOURCE["POS"]["replacements"]:
        _, receipt = TOOL.render_prompt(
            tmp_path, "POS", tmp_path / "neutral-root", verify_source=True
        )
        assert receipt["replacement_count"] == 9
    else:
        with pytest.raises(TOOL.ValidationError, match="replacement count mismatch"):
            TOOL.render_prompt(
                tmp_path, "POS", tmp_path / "neutral-root", verify_source=True
            )


def test_real_rollout_collector_golden_is_source_bound() -> None:
    assert TOOL.ROLLOUT_SHA256["POS"] == hashlib.sha256(
        _REAL_ROLLOUT.read_bytes()
    ).hexdigest()
    assert hashlib.sha256(_REAL_TOKEN_SLICE.encode()).hexdigest() == _REAL_TOKEN_SLICE_SHA
    source_line = _REAL_ROLLOUT.read_text(encoding="utf-8").splitlines(keepends=True)[15]
    assert source_line == _REAL_TOKEN_SLICE
    payload = json.loads(_REAL_TOKEN_SLICE)["payload"]["info"]["total_token_usage"]
    validated, issues, cached_exceeds_input = TOOL.LEDGER._validated_usage(
        payload, location="golden"
    )
    assert issues == []
    assert cached_exceeds_input == []
    assert validated and validated["input_tokens"] == 17295


def test_supervisor_launches_pair_and_scrubs_git_environment(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _, _ = _supervisor_pair(tmp_path, benchmark_snapshots, monkeypatch)
    assert len(result["runs"]) == 2
    first, second = result["runs"]
    assert first["process_exit_monotonic_ns"] <= second["process_start_monotonic_ns"]
    assert {row["attempt"] for row in result["runs"]} == {1}
    identities = set()
    for row in result["runs"]:
        launch = json.loads(Path(row["launch_receipt"]).read_text(encoding="utf-8"))
        identities.add(launch["treatment_identity_sha256"])
        assert not any(key.startswith("GIT_") for key in launch["environment"])
        assert launch["sandbox"] == {
            "snapshot_mount": "read-only",
            "home_masked": True,
            "tmp_masked": True,
            "pid_namespace": True,
            "proc_mount": "fresh",
            "writable_binds": ["codex-home", "output", "stdout", "stderr"],
            "attempt_receipts_bound": False,
        }
        assert "--ro-bind" in launch["bwrap_argv"]
        assert launch["codex_auth_sha256"]
        assert launch["codex_config_sha256"]
        assert launch["bwrap_version"] == "bwrap 0.6.1"
    assert len(identities) == 1


def test_agent_sandbox_binds_exclude_attempt_receipt_directory(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _, _ = _supervisor_pair(tmp_path, benchmark_snapshots, monkeypatch)
    for row in result["runs"]:
        launch = json.loads(Path(row["launch_receipt"]).read_text(encoding="utf-8"))
        argv = launch["bwrap_argv"]
        binds = {
            (argv[index + 1], argv[index + 2])
            for index, value in enumerate(argv[:-2])
            if value == "--bind"
        }
        assert binds == {
            (launch["codex_home"], launch["codex_home"]),
            (launch["output_path"], launch["output_path"]),
            (launch["events"]["path"], launch["events"]["path"]),
            (launch["stderr_path"], launch["stderr_path"]),
        }
        assert all(launch["run_dir"] not in pair for pair in binds)
        assert Path(row["launch_receipt"]).parent == Path(launch["run_dir"])


def test_verify_replays_complete_fake_codex_experiment(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, run_root = _full_manifest(
        tmp_path, benchmark_snapshots, monkeypatch
    )
    result, rc = TOOL.verify_manifest(manifest, run_root)
    assert rc == 0
    assert result["valid"] is True
    assert result["experiment_complete"] is True
    assert result["primary_judgment_ledger"] == {
        "max": {"k": 3, "n": 3},
        "high": {"k": 3, "n": 3},
    }
    assert len(result["resource_ledger"]) == 10
    assert result["reader_agreement"] == {
        "agreed": 10,
        "total": 10,
        "rate": 1.0,
        "disagreement_policy": "conservative-miss",
    }
    assert result["decision"]["row"] == "POS_PRIMARY"
    first_rollout = next(run_root.rglob("rollout-*.jsonl"))
    first_meta = first_rollout.read_text(encoding="utf-8").splitlines()[0]
    (run_root / "rollout-extra.jsonl").write_text(
        first_meta + "\n", encoding="utf-8"
    )
    tampered, tampered_rc = TOOL.verify_manifest(manifest, run_root)
    assert tampered_rc == TOOL.RC_AGGREGATE
    assert "generated session row set mismatch" in "\n".join(
        tampered["failure_reasons"]
    )


def test_supervisor_cli_removed_caller_attestation_command() -> None:
    help_text = TOOL._parser().format_help()
    assert "supervise-pair" in help_text
    assert "create-launch" not in help_text
    assert "argv-json" not in help_text
    assert "environment-json" not in help_text


def _timing_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    slots = [
        {"slot_id": "s01", "case": "POS", "arm": "max", "block_id": "b01", "block_order": 1},
        {"slot_id": "s02", "case": "POS", "arm": "high", "block_id": "b01", "block_order": 2},
    ]
    completed = []
    attempts = []
    for index, slot in enumerate(slots, 1):
        completed.append(
            {
                **slot,
                "phase": "completed",
                "attempt": 1,
                "run_id": f"r{index}",
                "parent_run_id": None,
                "launch_receipt": "/nonexistent",
                "launch_receipt_sha256": "0" * 64,
                "process_start_monotonic_ns": index * 2_000_000,
                "process_exit_monotonic_ns": index * 2_000_000 + 1_000_000,
                "snapshot_unchanged": True,
            }
        )
        attempts.append({"slot_id": slot["slot_id"], "attempt": 1, "run_id": f"r{index}"})
    reserved = [
        {
            "phase": "reserved",
            "slot_id": row["slot_id"],
            "block_id": row["block_id"],
            "attempt": row["attempt"],
        }
        for row in completed
    ]
    return slots, attempts, [*reserved, *completed]


def _timing_reasons(
    rows: list[dict[str, Any]],
    slots: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    tmp_path: Path,
) -> list[str]:
    _, reasons = TOOL._validate_supervisor_ledger(
        rows,
        slots,
        attempts,
        tmp_path,
        TOOL.MAX_SCHEDULE_GAP_MS,
        TOOL.MAX_INTER_BLOCK_GAP_MS,
    )
    return reasons


def test_pair_timing_simultaneous_is_rejected(tmp_path: Path) -> None:
    slots, attempts, rows = _timing_rows()
    rows[-1]["process_start_monotonic_ns"] = rows[-2]["process_start_monotonic_ns"]
    assert "actual process schedule overlaps or reverses" in _timing_reasons(
        rows, slots, attempts, tmp_path
    )


def test_pair_timing_reverse_order_is_rejected(tmp_path: Path) -> None:
    slots, attempts, rows = _timing_rows()
    rows[-1]["process_start_monotonic_ns"] = 1
    assert "actual process schedule overlaps or reverses" in _timing_reasons(
        rows, slots, attempts, tmp_path
    )


def test_intra_block_timing_large_gap_is_rejected(tmp_path: Path) -> None:
    slots, attempts, rows = _timing_rows()
    rows[-1]["process_start_monotonic_ns"] = (
        rows[-2]["process_exit_monotonic_ns"]
        + (TOOL.MAX_SCHEDULE_GAP_MS + 1) * 1_000_000
    )
    rows[-1]["process_exit_monotonic_ns"] = rows[-1]["process_start_monotonic_ns"] + 1
    assert "actual process schedule gap exceeds bound" in _timing_reasons(
        rows, slots, attempts, tmp_path
    )


def _append_timing_block(
    slots: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    *,
    gap_ms: int,
) -> None:
    completed = [row for row in rows if row.get("phase") == "completed"]
    previous_exit = completed[-1]["process_exit_monotonic_ns"]
    block_slots = [
        {
            "slot_id": "s03",
            "case": "NEG",
            "arm": "max",
            "block_id": "b02",
            "block_order": 1,
        },
        {
            "slot_id": "s04",
            "case": "NEG",
            "arm": "high",
            "block_id": "b02",
            "block_order": 2,
        },
    ]
    slots.extend(block_slots)
    start_ns = previous_exit + gap_ms * 1_000_000
    new_rows = []
    for offset, slot in enumerate(block_slots):
        process_start = start_ns + offset * 2_000_000
        new_rows.append(
            {
                **slot,
                "phase": "completed",
                "attempt": 1,
                "run_id": f"r{offset + 3}",
                "parent_run_id": None,
                "launch_receipt": "/nonexistent",
                "launch_receipt_sha256": "0" * 64,
                "process_start_monotonic_ns": process_start,
                "process_exit_monotonic_ns": process_start + 1_000_000,
                "snapshot_unchanged": True,
            }
        )
        attempts.append(
            {
                "slot_id": slot["slot_id"],
                "attempt": 1,
                "run_id": f"r{offset + 3}",
            }
        )
    reservations = [
        {
            "phase": "reserved",
            "slot_id": row["slot_id"],
            "block_id": row["block_id"],
            "attempt": row["attempt"],
        }
        for row in new_rows
    ]
    rows[len(rows) // 2 : len(rows) // 2] = reservations
    rows.extend(new_rows)


def test_inter_block_timing_350980_ms_is_accepted(tmp_path: Path) -> None:
    slots, attempts, rows = _timing_rows()
    _append_timing_block(slots, attempts, rows, gap_ms=350_980)
    assert "actual process schedule gap exceeds bound" not in _timing_reasons(
        rows, slots, attempts, tmp_path
    )


def test_inter_block_timing_above_bound_is_rejected(tmp_path: Path) -> None:
    slots, attempts, rows = _timing_rows()
    _append_timing_block(
        slots,
        attempts,
        rows,
        gap_ms=TOOL.MAX_INTER_BLOCK_GAP_MS + 1,
    )
    assert "actual process schedule gap exceeds bound" in _timing_reasons(
        rows, slots, attempts, tmp_path
    )


def test_pair_retry_nonadjacent_is_rejected(tmp_path: Path) -> None:
    slots, attempts, rows = _timing_rows()
    completed = rows[2:]
    extra_slots = [
        {"slot_id": "s03", "case": "NEG", "arm": "max", "block_id": "b02", "block_order": 1},
        {"slot_id": "s04", "case": "NEG", "arm": "high", "block_id": "b02", "block_order": 2},
    ]
    slots.extend(extra_slots)
    for generation_slot, run_id in zip(extra_slots, ("r3", "r4")):
        completed.append(
            {
                **generation_slot,
                "phase": "completed",
                "attempt": 1,
                "run_id": run_id,
                "parent_run_id": None,
                "launch_receipt": "/nonexistent",
                "launch_receipt_sha256": "0" * 64,
                "process_start_monotonic_ns": len(completed) * 2_000_000,
                "process_exit_monotonic_ns": len(completed) * 2_000_000 + 1,
                "snapshot_unchanged": True,
            }
        )
        attempts.append({"slot_id": generation_slot["slot_id"], "attempt": 1, "run_id": run_id})
    for base, run_id in zip(rows[2:4], ("r5", "r6")):
        retry = {**base, "attempt": 2, "run_id": run_id}
        completed.append(retry)
        attempts.append({"slot_id": retry["slot_id"], "attempt": 2, "run_id": run_id})
    reserved = [
        {"phase": "reserved", "slot_id": row["slot_id"], "block_id": row["block_id"], "attempt": row["attempt"]}
        for row in completed
    ]
    reasons = _timing_reasons([*reserved, *completed], slots, attempts, tmp_path)
    assert "b01: retry pair is not adjacent" in reasons


def test_pair_one_sided_retry_is_rejected(tmp_path: Path) -> None:
    slots, attempts, rows = _timing_rows()
    retry = {**rows[-2], "attempt": 2, "run_id": "r3"}
    attempts.append({"slot_id": "s01", "attempt": 2, "run_id": "r3"})
    rows.insert(2, {"phase": "reserved", "slot_id": "s01", "block_id": "b01", "attempt": 2})
    rows.append(retry)
    reasons = _timing_reasons(rows, slots, attempts, tmp_path)
    assert "supervisor completion ledger has a one-sided pair" in reasons


def test_attempt_four_is_rejected_before_launch(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    schedule_path, _ = _schedule(tmp_path / "schedule.json", benchmark_snapshots)
    with pytest.raises(TOOL.ValidationError, match="attempt must be in 1..3"):
        TOOL.supervise_pair(
            schedule_path=schedule_path,
            run_root=tmp_path / "root",
            block_id="b01",
            attempt=4,
            snapshot=benchmark_snapshots["POS"]["snapshot"],
            prompt=benchmark_snapshots["POS"]["prompt"],
            config_source=tmp_path / "missing-config",
            auth_source=tmp_path / "missing-auth",
            codex_binary=tmp_path / "missing-codex",
            bwrap_binary=tmp_path / "missing-bwrap",
            dry_run=True,
        )


def test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schedule_path, slots = _schedule(
        tmp_path / "schedule.json", benchmark_snapshots
    )
    run_root = tmp_path / "run-root"

    def fail_prelaunch(**_: Any) -> dict[str, Any]:
        raise OSError("injected config copy failure")

    monkeypatch.setattr(TOOL, "_supervise_one", fail_prelaunch)
    with pytest.raises(TOOL.ValidationError, match="prelaunch OSError"):
        TOOL.supervise_pair(
            schedule_path=schedule_path,
            run_root=run_root,
            block_id="b01",
            attempt=1,
            snapshot=benchmark_snapshots["POS"]["snapshot"],
            prompt=benchmark_snapshots["POS"]["prompt"],
            config_source=tmp_path / "config.toml",
            auth_source=tmp_path / "auth.json",
            codex_binary=tmp_path / "codex",
            bwrap_binary=tmp_path / "bwrap",
            dry_run=True,
        )
    ledger_rows = TOOL._attempt_ledger_rows(
        run_root / "attempt-ledger.jsonl"
    )
    first_generation = [
        row
        for row in ledger_rows
        if row.get("phase") == "completed" and row.get("attempt") == 1
    ]
    assert len(first_generation) == 2
    assert first_generation[0]["failure_class"] == "technical-invalid"
    assert first_generation[0]["prelaunch_failure"] == {
        "kind": "prelaunch-exception",
        "exception_type": "OSError",
        "message": "injected config copy failure",
    }
    assert first_generation[0]["model_calls"] == 0
    assert first_generation[0]["input_tokens"] == 0
    assert first_generation[0]["wall_clock_ms"] >= 0
    assert first_generation[1]["failure_class"] == "pair-invalidated"
    assert first_generation[1]["not_launched"] is True
    assert first_generation[1]["pair_invalidation"]["technical_run_ids"] == [
        first_generation[0]["run_id"]
    ]

    base_ns = time.monotonic_ns()
    launched = 0

    def complete_retry(**kwargs: Any) -> dict[str, Any]:
        nonlocal launched
        launched += 1
        slot = kwargs["slot"]
        start_ns = base_ns + launched * 2_000_000
        return {
            "schema_version": TOOL.SCHEMA_VERSION,
            "phase": "completed",
            "run_id": kwargs["run_id"],
            "slot_id": slot["slot_id"],
            "block_id": slot["block_id"],
            "block_order": slot["block_order"],
            "attempt": kwargs["attempt"],
            "parent_run_id": kwargs["parent_run_id"],
            "case": slot["case"],
            "arm": slot["arm"],
            "process_start_monotonic_ns": start_ns,
            "process_exit_monotonic_ns": start_ns + 1_000_000,
            "process_wall_ms": 1,
            "exit_code": 0,
            "snapshot_unchanged": True,
        }

    monkeypatch.setattr(TOOL, "_supervise_one", complete_retry)
    retried = TOOL.supervise_pair(
        schedule_path=schedule_path,
        run_root=run_root,
        block_id="b01",
        attempt=2,
        snapshot=benchmark_snapshots["POS"]["snapshot"],
        prompt=benchmark_snapshots["POS"]["prompt"],
        config_source=tmp_path / "config.toml",
        auth_source=tmp_path / "auth.json",
        codex_binary=tmp_path / "codex",
        bwrap_binary=tmp_path / "bwrap",
        dry_run=True,
    )
    assert len(retried["runs"]) == 2
    assert {row["attempt"] for row in retried["runs"]} == {2}
    assert {
        row["parent_run_id"] for row in retried["runs"]
    } == {row["run_id"] for row in first_generation}
    assert [row["slot_id"] for row in retried["runs"]] == [
        row["slot_id"] for row in slots if row["block_id"] == "b01"
    ]


def test_m4_session_identity_must_be_equal(tmp_path: Path) -> None:
    run = _manual_run(tmp_path, id_mismatch=True)
    assert run["rc"] != 0
    assert "session id/session_id/thread_id mismatch" in "\n".join(
        run["receipt"]["failure_reasons"]
    )


def test_m7_ledger_issues_propagate_to_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = TOOL.LEDGER._stream_rollout

    def with_ledger_issue(path: Path) -> tuple[dict[str, Any], dict[str, list[str]]]:
        record, issues = original(path)
        return record, {**issues, "sentinel": ["ledger-only"]}

    monkeypatch.setattr(TOOL.LEDGER, "_stream_rollout", with_ledger_issue)
    run = _manual_run(tmp_path)
    assert run["rc"] != 0
    assert "ledger:sentinel:ledger-only" in "\n".join(
        run["receipt"]["failure_reasons"]
    )


def test_m8_missing_turn_context_never_fills_requested_effort(tmp_path: Path) -> None:
    run = _manual_run(tmp_path, missing_context=True)
    assert run["rc"] != 0
    assert run["receipt"]["effective_effort"] is None
    assert "turn_context count is 0" in "\n".join(run["receipt"]["failure_reasons"])


def test_turn_id_must_be_nonempty_and_events_are_ordered(tmp_path: Path) -> None:
    run = _manual_run(tmp_path, empty_turn=True)
    reasons = "\n".join(run["receipt"]["failure_reasons"])
    assert run["rc"] != 0
    assert "turn_id missing/empty" in reasons


def test_zero_component_total_only_per_turn_is_nonfatal_and_reported(
    tmp_path: Path,
) -> None:
    run = _manual_run(
        tmp_path,
        token_infos=[
            {
                "total_token_usage": _usage(),
                "last_token_usage": _zero_component_total_only(),
            },
            {
                "total_token_usage": _usage(),
                "last_token_usage": _usage(),
            },
        ],
    )
    assert run["rc"] == 0
    assert run["receipt"]["valid"] is True
    assert run["receipt"]["failure_reasons"] == []
    assert run["receipt"]["cli_reported"] == 28
    assert run["receipt"]["token_usage_observations"] == (
        _token_usage_observations((1,))
    )


def test_nonzero_component_last_usage_identity_mismatch_remains_fatal(
    tmp_path: Path,
) -> None:
    mismatched = _usage()
    mismatched["total_tokens"] += 1
    run = _manual_run(
        tmp_path,
        token_infos=[
            {
                "total_token_usage": _usage(),
                "last_token_usage": mismatched,
            }
        ],
    )
    assert run["rc"] == TOOL.RC_RECEIPT
    assert (
        "token[1].last_token_usage total token identity mismatch"
        in run["receipt"]["failure_reasons"]
    )
    assert run["receipt"]["token_usage_observations"] == (
        _token_usage_observations()
    )


def test_final_cumulative_zero_component_total_only_remains_fatal(
    tmp_path: Path,
) -> None:
    run = _manual_run(
        tmp_path,
        token_infos=[
            {
                "total_token_usage": _usage(),
                "last_token_usage": _usage(),
            },
            {
                "total_token_usage": _zero_component_total_only(),
                "last_token_usage": _usage(),
            },
        ],
    )
    assert run["rc"] == TOOL.RC_RECEIPT
    assert (
        "token[2].total_token_usage total token identity mismatch"
        in run["receipt"]["failure_reasons"]
    )


def test_all_null_token_info_is_rejected(tmp_path: Path) -> None:
    run = _manual_run(tmp_path, token_infos=[None])
    assert run["rc"] == TOOL.RC_RECEIPT
    reasons = "\n".join(run["receipt"]["failure_reasons"])
    assert "all token_count.info values are null/non-object" in reasons
    assert "final token_count.info is null/non-object" in reasons


def test_final_cumulative_usage_null_is_rejected(tmp_path: Path) -> None:
    run = _manual_run(
        tmp_path,
        token_infos=[
            {
                "total_token_usage": None,
                "last_token_usage": _usage(),
            }
        ],
    )
    assert run["rc"] == TOOL.RC_RECEIPT
    assert (
        "token[1].total_token_usage is not an object"
        in run["receipt"]["failure_reasons"]
    )


def test_non_object_rollout_row_is_rejected(tmp_path: Path) -> None:
    run = _manual_run(tmp_path, non_object_rollout=True)
    assert run["rc"] == TOOL.RC_RECEIPT
    assert "JSON value is not an object" in "\n".join(
        run["receipt"]["failure_reasons"]
    )


def test_all_zero_usage_is_distinct_and_rejected(tmp_path: Path) -> None:
    zero = _usage(zero=True)
    run = _manual_run(
        tmp_path,
        token_infos=[
            {
                "total_token_usage": zero,
                "last_token_usage": zero,
            }
        ],
    )
    assert run["rc"] == TOOL.RC_RECEIPT
    assert (
        "token usage is all zero for non-empty prompt/output"
        in run["receipt"]["failure_reasons"]
    )
    assert run["receipt"]["token_usage_observations"] == (
        _token_usage_observations()
    )


def _aggregate_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    slots: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    verdicts: dict[str, dict[str, Any]] = {}
    index = 0
    for case, count in (("POS", 6), ("NEG", 4)):
        for offset in range(count):
            index += 1
            arm = "max" if offset % 2 == 0 else "high"
            slot_id = f"s{index:02d}"
            block_id = f"b{(index + 1) // 2:02d}"
            block_order = 1 if offset % 2 == 0 else 2
            slots.append(
                {
                    "slot_id": slot_id,
                    "case": case,
                    "arm": arm,
                    "block_id": block_id,
                    "block_order": block_order,
                }
            )
            attempts.append(
                {
                    "run_id": f"r{index:02d}",
                    "slot_id": slot_id,
                    "attempt": 1,
                    "case": case,
                    "arm": arm,
                    "block_id": block_id,
                    "block_order": block_order,
                    "failure_class": None,
                    "input_tokens": 1,
                    "cached_input_tokens": 0,
                    "output_tokens": 1,
                    "reasoning_output_tokens": 0,
                    "cli_reported": 2,
                    "model_calls": 1,
                    "token_usage_observations": _token_usage_observations(),
                    "turn_protocol": "single-turn-required",
                    "wall_clock_ms": 100,
                    "rate_limited": False,
                    "retry": False,
                    "compaction_observed": False,
                }
            )
            verdicts[slot_id] = {
                "r1_detected": case == "POS",
                "findings": [],
                "reader_agreement": True,
            }
    return slots, attempts, verdicts


def test_zero_component_total_only_aggregate_counts_by_arm_and_case(
    tmp_path: Path,
) -> None:
    slots, attempts, verdicts = _aggregate_rows()
    attempts[6]["token_usage_observations"] = _token_usage_observations((1,))
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "manifest.json", {}),
        slots,
        attempts,
        verdicts,
        [],
    )
    assert result["valid"] is True
    assert result["token_usage_observations"] == {
        TOOL.ZERO_COMPONENT_TOTAL_ONLY: {
            "total_count": 1,
            "by_arm_case": {
                "max": {"POS": 0, "NEG": 1},
                "high": {"POS": 0, "NEG": 0},
            },
        }
    }


def test_zero_component_total_only_count_is_required_for_aggregate(
    tmp_path: Path,
) -> None:
    slots, attempts, verdicts = _aggregate_rows()
    del attempts[0]["token_usage_observations"][
        TOOL.ZERO_COMPONENT_TOTAL_ONLY
    ]["count"]
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "manifest.json", {}),
        slots,
        attempts,
        verdicts,
        [],
    )
    assert result["valid"] is False
    assert result["experiment_complete"] is False
    assert (
        "r01: zero_component_total_only count missing/non-int"
        in result["failure_reasons"]
    )


def test_m9_post_treatment_failure_remains_in_denominator(tmp_path: Path) -> None:
    slots, attempts, verdicts = _aggregate_rows()
    scored = TOOL._apply_score_failure(
        attempts[1],
        {"valid": False, "failure_reasons": ["score: partial output"]},
    )
    assert scored["failure_class"] == "post-treatment"
    attempts[1] = scored
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "manifest.json", {}), slots, attempts, verdicts, []
    )
    assert result["experiment_complete"] is True
    assert result["primary_judgment_ledger"]["high"] == {"k": 2, "n": 3}
    assert result["post_treatment_reliability"]["high"] == 1
    assert len(result["resource_ledger"]) == 10


def test_asymmetric_technical_pair_retry_marks_mate_and_keeps_resources(
    tmp_path: Path,
) -> None:
    slots, attempts, verdicts = _aggregate_rows()
    first, mate = attempts[0], attempts[1]
    first["failure_class"] = "technical-invalid"
    retry_rows = []
    for prior in (first, mate):
        retry_rows.append(
            {
                **prior,
                "run_id": prior["run_id"] + "-retry",
                "attempt": 2,
                "parent_run_id": prior["run_id"],
                "failure_class": None,
                "retry": True,
            }
        )
    attempts.extend(retry_rows)
    TOOL._apply_pair_invalidations(attempts)
    assert first["failure_class"] == "technical-invalid"
    assert mate["failure_class"] == "pair-invalidated"
    assert mate["individual_failure_class"] is None
    assert mate["pair_invalidation"]["technical_run_ids"] == [first["run_id"]]
    grouped = {
        slot["slot_id"]: [
            row for row in attempts if row["slot_id"] == slot["slot_id"]
        ]
        for slot in slots[:2]
    }
    assert TOOL._retry_lineage_reasons(grouped) == []

    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "manifest.json", {}),
        slots,
        attempts,
        verdicts,
        [],
    )
    assert result["experiment_complete"] is True
    assert len(result["resource_ledger"]) == 12
    assert result["resource_ledger"][1]["failure_class"] == "pair-invalidated"


def test_f3_2_pair_invalidated_post_treatment_occurrence_is_reliable(
    tmp_path: Path,
) -> None:
    slots, attempts, verdicts = _aggregate_rows()
    technical, partial = attempts[0], attempts[1]
    technical["failure_class"] = "technical-invalid"
    partial["failure_class"] = "post-treatment"
    partial["failure_classes"] = ["post-treatment"]
    attempts.extend(
        {
            **prior,
            "run_id": prior["run_id"] + "-retry",
            "attempt": 2,
            "parent_run_id": prior["run_id"],
            "failure_class": None,
            "failure_classes": [],
            "retry": True,
        }
        for prior in (technical, partial)
    )
    TOOL._apply_pair_invalidations(attempts)
    assert partial["failure_class"] == "pair-invalidated"
    assert partial["individual_failure_class"] == "post-treatment"

    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "manifest.json", {}),
        slots,
        attempts,
        verdicts,
        [],
    )
    assert result["experiment_complete"] is True
    assert result["primary_judgment_ledger"]["high"] == {"k": 3, "n": 3}
    assert result["post_treatment_reliability"]["high"] == 1
    assert result["online_max_escalation_candidate"] is True


@pytest.mark.parametrize("with_reason", [False, True])
def test_incomplete_or_verifier_reason_nulls_quality_ledgers(
    with_reason: bool, tmp_path: Path
) -> None:
    slots, attempts, verdicts = _aggregate_rows()
    if not with_reason:
        attempts[0]["failure_class"] = "technical-invalid"
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "manifest.json", {}),
        slots,
        attempts,
        verdicts,
        ["verifier reason"] if with_reason else [],
    )
    assert result["experiment_complete"] is False
    for field in (
        "primary_judgment_ledger",
        "new_finding_ledger",
        "post_treatment_reliability",
        "online_max_escalation_candidate",
        "reader_agreement",
        "decision",
    ):
        assert result[field] is None
    assert len(result["resource_ledger"]) == 10


def test_false_finding_is_derived_and_decision_fields_are_typed(tmp_path: Path) -> None:
    slots, attempts, verdicts = _aggregate_rows()
    neg_high = next(
        row for row in slots if row["case"] == "NEG" and row["arm"] == "high"
    )
    verdicts[neg_high["slot_id"]]["findings"] = [
        {
            "real": True,
            "equivalent_to": "R-1",
            "root_cause": None,
            "severity": "HIGH",
            "must_fix": True,
        }
    ]
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "manifest.json", {}), slots, attempts, verdicts, []
    )
    decision = result["decision"]
    assert decision["row"] == "NEG_ADJUDICATED_FALSE_FINDING"
    assert decision["neg_excluded_arms"] == ["high"]
    assert decision["adoption_eligibility"] == {"max": True, "high": False}


@pytest.mark.parametrize(
    ("max_k", "high_k", "pos_eligibility"),
    [
        (3, 3, {"max": True, "high": True}),
        (3, 2, {"max": True, "high": False}),
        (2, 3, {"max": False, "high": False}),
        (2, 2, {"max": False, "high": False}),
    ],
)
@pytest.mark.parametrize(
    ("neg_max", "neg_high"),
    [(False, False), (True, False), (False, True), (True, True)],
)
def test_pos_four_branches_cross_neg_arm_exclusions(
    max_k: int,
    high_k: int,
    pos_eligibility: dict[str, bool],
    neg_max: bool,
    neg_high: bool,
    tmp_path: Path,
) -> None:
    slots, attempts, verdicts = _aggregate_rows()
    for arm, detected in (("max", max_k), ("high", high_k)):
        arm_slots = [
            row
            for row in slots
            if row["case"] == "POS" and row["arm"] == arm
        ]
        for index, slot in enumerate(arm_slots):
            verdicts[slot["slot_id"]]["r1_detected"] = index < detected
    for arm, excluded in (("max", neg_max), ("high", neg_high)):
        if not excluded:
            continue
        slot = next(
            row
            for row in slots
            if row["case"] == "NEG" and row["arm"] == arm
        )
        verdicts[slot["slot_id"]]["findings"] = [
            {
                "real": True,
                "equivalent_to": "R-1",
                "root_cause": None,
                "severity": "HIGH",
                "must_fix": True,
            }
        ]
    result = TOOL._aggregate_verified(
        _canonical(
            tmp_path
            / f"manifest-{max_k}-{high_k}-{int(neg_max)}-{int(neg_high)}.json",
            {},
        ),
        slots,
        attempts,
        verdicts,
        [],
    )
    decision = result["decision"]
    assert decision["pos_adoption_eligibility"] == pos_eligibility
    assert decision["adoption_eligibility"] == {
        "max": pos_eligibility["max"] and not neg_max,
        "high": pos_eligibility["high"] and not neg_high,
    }


def test_m10_historical_controls() -> None:
    assert hashlib.sha256((_CONTROL_DIR / "focus1.md").read_bytes()).hexdigest() == _FOCUS1_SHA
    assert hashlib.sha256((_CONTROL_DIR / "focus2.md").read_bytes()).hexdigest() == _FOCUS2_SHA
    positive, positive_rc = TOOL.score_run(_CONTROL_DIR / "focus1.md", "p")
    negative, negative_rc = TOOL.score_run(_CONTROL_DIR / "focus2.md", "n")
    assert positive_rc == negative_rc == 0
    assert (positive["decision"], positive["r1_candidate"]) == ("NO-GO", True)
    assert (negative["decision"], negative["r1_candidate"]) == ("GO", False)


@pytest.mark.parametrize(
    "opening",
    [
        pytest.param("NO-GO。", id="plain"),
        pytest.param("NO-GO です。", id="spaced_desu"),
        pytest.param("**NO-GO**です。", id="emphasized_copula"),
        pytest.param("結論は NO-GO です。", id="conclusion_prefix"),
    ],
)
def test_f176_accepts_decision_statement_variants(opening: str) -> None:
    score = TOOL.score_text("## 総括\n" + opening + "総括本文。" * 100)
    assert score["valid"] is True
    assert score["decision"] == "NO-GO"


def test_f176_accepts_real_s03_artifact() -> None:
    path = _CERTIFIED_RERUN_DIR / "s03-POS-max.md"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == _S03_SHA
    score, rc = TOOL.score_run(path, "s03")
    assert rc == 0
    assert score["valid"] is True
    assert score["decision"] == "NO-GO"
    assert score["r1_candidate"] is True


@pytest.mark.parametrize(
    ("opening", "additional_opening"),
    [
        pytest.param("GO。しかしNO-GOでもある。", None, id="however"),
        pytest.param("GO。NO-GOです。", None, id="second_plain"),
        pytest.param(
            "GO。結論はNO-GOです。", None, id="conclusion_assertion"
        ),
        pytest.param(
            "GO。判断はNO-GOです。", None, id="embedded_assertion"
        ),
        pytest.param("GO。ただしNO-GOです。", None, id="but"),
        pytest.param(
            "GO。NO-GOと判断する。", None, id="judgment_statement"
        ),
        pytest.param(
            "NO-GO。しかしGOでもある。", None, id="reverse_however"
        ),
        pytest.param("NO-GO。GOです。", None, id="reverse_plain"),
        pytest.param(
            "NO-GO。結論はGOです。",
            None,
            id="reverse_conclusion_assertion",
        ),
        pytest.param(
            "NO-GO。判断はGOです。",
            None,
            id="reverse_embedded_assertion",
        ),
        pytest.param("NO-GO。ただしGOです。", None, id="reverse_but"),
        pytest.param(
            "NO-GOです。ただしGOです。", None, id="conflicting_copulas"
        ),
        pytest.param(
            "GO。NO-GO の理由は、未修正の正しさ欠陥が残るためです。",
            "GO。NO-GO の理由です。別の説は採らない。",
            id="reason_assertion",
        ),
        pytest.param(
            "GO。NO-GOの結論です。",
            "GO。NO-GOの結論にはならない。",
            id="nominal_conclusion",
        ),
    ],
)
def test_f176_rejects_conflicting_decision_claims(
    opening: str, additional_opening: str | None
) -> None:
    for candidate in (opening, additional_opening):
        if candidate is None:
            continue
        score = TOOL.score_text("## 総括\n" + candidate + "総括本文。" * 100)
        assert score["valid"] is False
        assert score["decision"] is None


@pytest.mark.parametrize(
    ("opening", "decision"),
    [
        pytest.param(
            "NO-GO。GOの条件を満たさない。", "NO-GO", id="go_condition"
        ),
        pytest.param(
            "GO。このfocused reviewのNO-GO理由にはなりません。",
            "GO",
            id="focused_review_reason",
        ),
    ],
)
def test_f176_preserves_decision_mentions(
    opening: str, decision: str
) -> None:
    score = TOOL.score_text("## 総括\n" + opening + "総括本文。" * 100)
    assert score["valid"] is True
    assert score["decision"] == decision


@pytest.mark.parametrize(
    ("opening", "decision"),
    [
        pytest.param(
            "NO-GO。GOの余地はあるが、結論はNO-GOである。",
            "NO-GO",
            id="go_possibility",
        ),
        pytest.param(
            "NO-GO。GOの条件を満たさない。",
            "NO-GO",
            id="go_condition_not_met",
        ),
        pytest.param(
            "NO-GO。GOへ倒す材料は見つからなかった。",
            "NO-GO",
            id="no_material_for_go",
        ),
        pytest.param(
            "NO-GO。前回のGO判定は本件に適用できない。",
            "NO-GO",
            id="prior_go_inapplicable",
        ),
        pytest.param(
            "NO-GO。GOの根拠として挙げられた3点はいずれも成立しない。",
            "NO-GO",
            id="go_reasons_invalid",
        ),
        pytest.param(
            "GO。NO-GO理由にはなりません。",
            "GO",
            id="not_no_go_reason",
        ),
        pytest.param(
            "GO。NO-GOの条件を満たす所見は無い。",
            "GO",
            id="no_no_go_finding",
        ),
        pytest.param(
            "GO。NO-GO側の懸念は解消済みである。",
            "GO",
            id="no_go_concerns_resolved",
        ),
        pytest.param(
            "GO。NO-GO寄りの解釈も検討したが採らない。",
            "GO",
            id="no_go_interpretation_rejected",
        ),
        pytest.param(
            "GO。NO-GO判定に必要な must-fix は残っていない。",
            "GO",
            id="no_no_go_must_fix",
        ),
    ],
)
def test_f176_preserves_legitimate_opposite_mentions(
    opening: str, decision: str
) -> None:
    score = TOOL.score_text("## 総括\n" + opening + "総括本文。" * 100)
    assert score["valid"] is True
    assert score["decision"] == decision


@pytest.mark.parametrize(
    "openings",
    [
        pytest.param(
            (
                "よってNO-GOです。",
                "したがってNO-GOです。",
                "以上よりNO-GOです。",
            ),
            id="discourse_connective",
        ),
        pytest.param(("結論は\nNO-GOです。",), id="newline_in_opening"),
    ],
)
def test_f176_rejects_open_grammar_beyond_closed_set(
    openings: tuple[str, ...],
) -> None:
    for opening in openings:
        score = TOOL.score_text("## 総括\n" + opening + "総括本文。" * 100)
        assert score["valid"] is False
        assert score["decision"] is None


@pytest.mark.parametrize(
    ("filename", "decision"),
    [
        pytest.param("s01-POS-high.md", "NO-GO", id="s01"),
        pytest.param("s02-POS-max.md", "NO-GO", id="s02"),
        pytest.param("s04-POS-high.md", "NO-GO", id="s04"),
        pytest.param("s05-POS-high.md", "NO-GO", id="s05"),
        pytest.param("s06-POS-max.md", "NO-GO", id="s06"),
        pytest.param("s07-NEG-max.md", "GO", id="s07"),
        pytest.param("s08-NEG-high.md", "GO", id="s08"),
        pytest.param("s09-NEG-high.md", "GO", id="s09"),
        pytest.param("s10-NEG-max.md", "GO", id="s10"),
    ],
)
def test_f176_preserves_other_certified_runs(
    filename: str, decision: str
) -> None:
    score, rc = TOOL.score_run(_CERTIFIED_RERUN_DIR / filename, filename)
    assert rc == 0
    assert score["valid"] is True
    assert score["decision"] == decision


@pytest.mark.parametrize(
    "opening",
    ["GOではない。", "GOか未裁定。", "GOだという説はrefuted。"],
)
def test_scorer_rejects_negated_or_unadjudicated_decisions(opening: str) -> None:
    score = TOOL.score_text("## 総括\n" + opening + "総括本文。" * 100)
    assert score["valid"] is False
    assert score["decision"] is None


@pytest.mark.parametrize(
    "opening",
    [
        "**GO** との判断は保留する。",
        "__NO-GO__ の判定を保留する。",
        "`GO`との結論は保留する。",
        "***NO-GO*** と決めかねる。",
    ],
)
def test_scorer_rejects_emphasized_ambiguous_decision_sentence(
    opening: str,
) -> None:
    score = TOOL.score_text("## 総括\n" + opening + "総括本文。" * 100)
    assert score["valid"] is False
    assert score["decision"] is None
    assert (
        "score: summary does not start with one GO/NO-GO decision"
        in score["failure_reasons"]
    )


def test_f3_3_scorer_rejects_decision_disclaimed_after_punctuation() -> None:
    score = TOOL.score_text(
        "## 総括\nGO。これは最終判断ではない。" + "総括本文。" * 100
    )
    assert score["summary_bytes"] >= 500
    assert score["valid"] is False
    assert score["decision"] is None
    assert (
        "score: summary does not start with one GO/NO-GO decision"
        in score["failure_reasons"]
    )


def test_single_turn_constant_is_not_emitted_as_resource_metric(
    tmp_path: Path,
) -> None:
    run = _manual_run(tmp_path / "run")
    assert "logical_turns" not in run["receipt"]
    assert run["receipt"]["turn_protocol"] == "single-turn-required"
    slots, attempts, verdicts = _aggregate_rows()
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "manifest.json", {}),
        slots,
        attempts,
        verdicts,
        [],
    )
    assert all("logical_turns" not in row for row in result["resource_ledger"])
    assert all("model_calls" in row for row in result["resource_ledger"])
    assert result["turn_accounting"] == {
        "protocol": "single-turn-required",
        "comparative_metric": "model_calls",
        "logical_turns_reported": False,
    }


def test_scorer_rejects_negated_r1_candidate() -> None:
    text = (
        "## R-1\npre-policyではcanonical CAB parserは実行されない。"
        "rc=0がrc=2になることはない。このNO-GO/must-fix説はrefuted。"
        "\n## 総括\n**NO-GO。** " + "十分な総括。" * 100
    )
    score = TOOL.score_text(text)
    assert score["valid"] is True
    assert score["r1_candidate"] is False


def test_m11_tilde_fence_hides_summary() -> None:
    text = (
        "~~~ lang`x\n## 総括\nNO-GO。" + "偽総括。" * 100 + "\n~~~\n"
        "本文のみ。"
    )
    score = TOOL.score_text(text)
    assert score["valid"] is False
    assert "summary count is 0" in "\n".join(score["failure_reasons"])


def test_m12_summary_500_byte_exact_boundary() -> None:
    prefix = "## 総括\nGO。"
    exact = prefix + "a" * (500 - len(prefix.encode("utf-8")))
    below = exact[:-1]
    exact_score = TOOL.score_text(exact)
    below_score = TOOL.score_text(below)
    assert exact_score["summary_bytes"] == 500
    assert exact_score["valid"] is True
    assert below_score["summary_bytes"] == 499
    assert below_score["valid"] is False


def _packet_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    packet_dir = tmp_path / "packets"
    packet_dir.mkdir()
    packet_id = "a" * 32
    packet = packet_dir / f"packet-{packet_id}.md"
    packet.write_text(_long_output(), encoding="utf-8")
    os.utime(packet, ns=(TOOL.PACKET_MTIME_NS, TOOL.PACKET_MTIME_NS))
    state = _canonical(
        packet_dir / "packet-state.json",
        {
            "schema_version": 2,
            "mask_strength": "same-owner-advisory",
            "packets": [
                {
                    "packet_id": packet_id,
                    "filename": packet.name,
                }
            ],
        },
    )
    parent = _canonical(
        tmp_path / "parent.json",
        {"verdicts": [{"packet_id": packet_id, "r1_detected": True, "findings": []}]},
    )
    second = _canonical(
        tmp_path / "second.json",
        {"verdicts": [{"packet_id": packet_id, "r1_detected": False, "findings": []}]},
    )
    return state, parent, second


def test_two_readers_required_before_mapping_reveal(tmp_path: Path) -> None:
    state, parent, second = _packet_fixture(tmp_path)
    log = tmp_path / "verdicts.jsonl"
    TOOL.append_verdicts(state, log, "parent", parent)
    with pytest.raises(TOOL.ValidationError, match="already appended"):
        TOOL.append_verdicts(state, log, "parent", parent)
    with pytest.raises(TOOL.ValidationError, match="both reader verdict sets"):
        TOOL.freeze_verdicts(state, log, tmp_path / "freeze.json")
    TOOL.append_verdicts(state, log, "second-reader", second)
    freeze = tmp_path / "freeze.json"
    TOOL.freeze_verdicts(state, log, freeze)
    assert freeze.exists()


def test_mapping_custodian_blocks_pre_freeze_reveal_and_packet_sha_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet_dir = tmp_path / "packets"
    custodian_root = tmp_path / "custodian"
    manifest = _canonical(
        tmp_path / "manifest.json",
        {
            "attempts": [
                {
                    "slot_id": f"s{index:02d}",
                    "attempt": 1,
                    "run_id": f"r{index:02d}",
                    "output": _descriptor(
                        _canonical(
                            tmp_path / f"output-{index:02d}.json",
                            {"index": index},
                        ),
                        tmp_path,
                    ),
                }
                for index in range(1, 11)
            ]
        },
    )
    with pytest.raises(TOOL.ValidationError, match="outside packet directory"):
        TOOL.make_packets(manifest, packet_dir, packet_dir / "secret")
    result = TOOL.make_packets(manifest, packet_dir, custodian_root)
    assert "mapping_secret" not in result
    assert "path" not in result["custodian_protocol"]
    assert "key" not in result
    assert stat.S_IMODE(custodian_root.stat().st_mode) == 0o700
    state = json.loads(Path(result["packet_state"]).read_text(encoding="utf-8"))
    assert all(set(row) == {"packet_id", "filename"} for row in state["packets"])
    mtimes = {
        (packet_dir / row["filename"]).stat().st_mtime_ns
        for row in state["packets"]
    }
    assert mtimes == {TOOL.PACKET_MTIME_NS}
    assert state["mask_strength"] == "same-owner-advisory"
    assert TOOL.PACKET_MTIME_NS == 946684800_000_000_000
    assert custodian_root != packet_dir

    verdict_log = tmp_path / "verdicts.jsonl"
    verdict_log.write_bytes(b"")
    invalid_freeze = _canonical(
        tmp_path / "invalid-freeze.json",
        {"packet_state_sha256": "0" * 64, "verdict_log_sha256": "0" * 64},
    )
    with monkeypatch.context() as guard:
        guard.setattr(
            TOOL,
            "_custodian_mapping_path",
            lambda *_: pytest.fail("custodian opened before freeze validation"),
        )
        with pytest.raises(TOOL.ValidationError, match="not frozen"):
            TOOL.reveal_mapping(
                Path(result["packet_state"]),
                custodian_root,
                verdict_log,
                invalid_freeze,
                tmp_path / "early-map.json",
            )
    assert not (tmp_path / "early-map.json").exists()

    verdicts = {
        "verdicts": [
            {
                "packet_id": row["packet_id"],
                "r1_detected": False,
                "findings": [],
            }
            for row in state["packets"]
        ]
    }
    parent = _canonical(tmp_path / "parent.json", verdicts)
    second = _canonical(tmp_path / "second.json", verdicts)
    verdict_log.unlink()
    TOOL.append_verdicts(
        Path(result["packet_state"]), verdict_log, "parent", parent
    )
    TOOL.append_verdicts(
        Path(result["packet_state"]), verdict_log, "second-reader", second
    )
    freeze = tmp_path / "freeze.json"
    TOOL.freeze_verdicts(Path(result["packet_state"]), verdict_log, freeze)
    revealed = tmp_path / "revealed.json"
    TOOL.reveal_mapping(
        Path(result["packet_state"]),
        custodian_root,
        verdict_log,
        freeze,
        revealed,
    )
    mapping = json.loads(revealed.read_text(encoding="utf-8"))["mapping"]
    assert all(
        set(row)
        == {
            "packet_id",
            "run_id",
            "packet_sha256",
            "score_input_sha256",
        }
        for row in mapping
    )


def test_f3_1_packet_swap_restore_is_rejected(tmp_path: Path) -> None:
    packet_ids = ("a" * 32, "b" * 32)
    packet_paths = [
        tmp_path / f"packet-{packet_id}.md" for packet_id in packet_ids
    ]
    original_bodies = [
        _long_output("NO-GO").encode("utf-8"),
        _long_output("GO").encode("utf-8"),
    ]
    for path, body in zip(packet_paths, original_bodies):
        path.write_bytes(body)
    state = _canonical(
        tmp_path / "packet-state.json",
        {
            "schema_version": TOOL.SCHEMA_VERSION,
            "mask_strength": "same-owner-advisory",
            "packets": [
                {"packet_id": packet_id, "filename": path.name}
                for packet_id, path in zip(packet_ids, packet_paths)
            ],
        },
    )
    custodian = tmp_path / "custodian"
    custodian.mkdir(mode=0o700)
    secret = _canonical(
        custodian / ("mapping-" + "c" * 48 + ".json"),
        {
            "schema_version": TOOL.SCHEMA_VERSION,
            "mask_strength": "same-owner-advisory",
            "mapping": [
                {
                    "packet_id": packet_id,
                    "run_id": f"r{index}",
                    "slot_id": f"s{index}",
                    "packet_sha256": TOOL._sha256(body),
                    "score_input_sha256": TOOL._sha256(body),
                }
                for index, (packet_id, body) in enumerate(
                    zip(packet_ids, original_bodies), 1
                )
            ],
        },
    )
    secret.chmod(0o600)
    packet_paths[0].write_bytes(original_bodies[1])
    packet_paths[1].write_bytes(original_bodies[0])
    verdict_input = _canonical(
        tmp_path / "verdict-input.json",
        {
            "verdicts": [
                {
                    "packet_id": packet_id,
                    "r1_detected": index == 0,
                    "findings": [],
                }
                for index, packet_id in enumerate(packet_ids)
            ]
        },
    )
    verdict_log = tmp_path / "verdicts.jsonl"
    TOOL.append_verdicts(
        state, verdict_log, "parent", verdict_input
    )
    TOOL.append_verdicts(
        state, verdict_log, "second-reader", verdict_input
    )
    freeze = tmp_path / "freeze.json"
    TOOL.freeze_verdicts(state, verdict_log, freeze)
    packet_paths[0].write_bytes(original_bodies[0])
    packet_paths[1].write_bytes(original_bodies[1])

    with pytest.raises(
        TOOL.ValidationError,
        match="frozen packet digest does not match revealed packet bytes",
    ):
        TOOL.reveal_mapping(
            state,
            custodian,
            verdict_log,
            freeze,
            tmp_path / "revealed.json",
        )


class _DigestComparisonBypass(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False

    __hash__ = str.__hash__


class _DigestMapComparisonBypass(dict[str, str]):
    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False

    def get(self, key: str, default: Any = None) -> Any:
        value = super().get(key, default)
        return (
            _DigestComparisonBypass(value)
            if isinstance(value, str)
            else value
        )


def _verdict_packet_swap_restore_fixture(
    tmp_path: Path,
) -> tuple[
    Path,
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    Path,
    Path,
]:
    packet_ids = ("a" * 32, "b" * 32)
    runs = ("r01", "r02")
    slots = [
        {"slot_id": "s01", "case": "POS", "arm": "max"},
        {"slot_id": "s02", "case": "POS", "arm": "high"},
    ]
    original_bodies = (
        _long_output("NO-GO").encode("utf-8"),
        _long_output("GO").encode("utf-8"),
    )
    packet_paths = [
        tmp_path / f"packet-{packet_id}.md" for packet_id in packet_ids
    ]
    for packet_path, body in zip(packet_paths, original_bodies):
        packet_path.write_bytes(body)
    packet_state = _canonical(
        tmp_path / "packet-state.json",
        {
            "schema_version": TOOL.SCHEMA_VERSION,
            "mask_strength": "same-owner-advisory",
            "packets": [
                {"packet_id": packet_id, "filename": packet_path.name}
                for packet_id, packet_path in zip(packet_ids, packet_paths)
            ],
        },
    )
    final_attempts = {
        slot["slot_id"]: {
            "run_id": run_id,
            "output_sha256": TOOL._sha256(body),
        }
        for slot, run_id, body in zip(slots, runs, original_bodies)
    }

    packet_paths[0].write_bytes(original_bodies[1])
    packet_paths[1].write_bytes(original_bodies[0])
    swapped_verdicts = _canonical(
        tmp_path / "swapped-verdicts.json",
        {
            "verdicts": [
                {
                    "packet_id": packet_ids[0],
                    "r1_detected": False,
                    "findings": [],
                },
                {
                    "packet_id": packet_ids[1],
                    "r1_detected": True,
                    "findings": [],
                },
            ]
        },
    )
    verdict_log = tmp_path / "verdicts.jsonl"
    TOOL.append_verdicts(
        packet_state, verdict_log, "parent", swapped_verdicts
    )
    TOOL.append_verdicts(
        packet_state, verdict_log, "second-reader", swapped_verdicts
    )
    verdict_freeze = tmp_path / "verdict-freeze.json"
    TOOL.freeze_verdicts(packet_state, verdict_log, verdict_freeze)

    packet_paths[0].write_bytes(original_bodies[0])
    packet_paths[1].write_bytes(original_bodies[1])
    revealed_map = _canonical(
        tmp_path / "revealed-map.json",
        {
            "schema_version": TOOL.SCHEMA_VERSION,
            "mask_strength": "same-owner-advisory",
            "verdict_freeze_sha256": TOOL._sha256(
                verdict_freeze.read_bytes()
            ),
            "mapping": [
                {
                    "packet_id": packet_id,
                    "run_id": run_id,
                    "packet_sha256": TOOL._sha256(body),
                    "score_input_sha256": TOOL._sha256(body),
                }
                for packet_id, run_id, body in zip(
                    packet_ids, runs, original_bodies
                )
            ],
        },
    )
    verdict_rows = [
        json.loads(line)
        for line in verdict_log.read_text(encoding="utf-8").splitlines()
    ]
    judgments = []
    for slot, packet_id, detected in zip(
        slots, packet_ids, (False, True)
    ):
        readers = {
            row["reader"]: row
            for row in verdict_rows
            if row["packet_id"] == packet_id
        }
        combined = {
            "r1_detected": detected,
            "findings": [],
            "reader_agreement": True,
            "reader_rows_sha256": TOOL._sha256(
                TOOL._canonical_bytes(
                    [readers["parent"], readers["second-reader"]]
                )
            ),
        }
        judgments.append(
            {
                "slot_id": slot["slot_id"],
                "packet_id": packet_id,
                "score_input_sha256": final_attempts[
                    slot["slot_id"]
                ]["output_sha256"],
                "combined_verdict_sha256": TOOL._sha256(
                    TOOL._canonical_bytes(combined)
                ),
                "r1_detected": detected,
                "reader_agreement": True,
            }
        )

    for index, artifact in enumerate(
        (packet_state, verdict_log, verdict_freeze, revealed_map), 1
    ):
        timestamp_ns = TOOL.PACKET_MTIME_NS + index * 1_000_000
        os.utime(artifact, ns=(timestamp_ns, timestamp_ns))
    manifest = {
        "packet_state": _descriptor(packet_state, tmp_path),
        "verdict_log": _descriptor(verdict_log, tmp_path),
        "verdict_freeze": _descriptor(verdict_freeze, tmp_path),
        "revealed_map": _descriptor(revealed_map, tmp_path),
        "judgments": judgments,
    }
    manifest_path = _canonical(tmp_path / "manifest.json", manifest)
    return (
        manifest_path,
        manifest,
        slots,
        final_attempts,
        verdict_log,
        verdict_freeze,
    )


def test_m6_verdict_packet_swap_restore_digest_layers_are_redundant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DW-M04 expected mutation node: M6 / M6p."""
    (
        manifest_path,
        manifest,
        slots,
        final_attempts,
        verdict_log,
        verdict_freeze,
    ) = _verdict_packet_swap_restore_fixture(tmp_path)

    joined, reasons = TOOL._load_adjudication(
        manifest_path, manifest, slots, final_attempts
    )
    assert joined["s01"]["r1_detected"] is False
    assert joined["s02"]["r1_detected"] is True
    assert any(
        "verdict read-time packet/output sha mismatch" in reason
        for reason in reasons
    )
    assert any(
        "frozen packet/output sha mismatch" in reason
        for reason in reasons
    )

    original_json_lines = TOOL._json_lines

    def without_read_digest_check(
        path: Path,
    ) -> tuple[list[Any], list[str]]:
        rows, issues = original_json_lines(path)
        if path.resolve() != verdict_log.resolve():
            return rows, issues
        return [
            {
                **row,
                "packet_sha256_at_read": _DigestComparisonBypass(
                    row["packet_sha256_at_read"]
                ),
            }
            for row in rows
        ], issues

    with monkeypatch.context() as read_layer_disabled:
        read_layer_disabled.setattr(
            TOOL, "_json_lines", without_read_digest_check
        )
        _, read_disabled_reasons = TOOL._load_adjudication(
            manifest_path, manifest, slots, final_attempts
        )
    assert not any(
        "verdict read-time packet/output sha mismatch" in reason
        for reason in read_disabled_reasons
    )
    assert any(
        "frozen packet/output sha mismatch" in reason
        for reason in read_disabled_reasons
    )

    original_load_json_object = TOOL._load_json_object

    def without_freeze_digest_check(path: Path) -> dict[str, Any]:
        value = original_load_json_object(path)
        if path.resolve() == verdict_freeze.resolve():
            value["packet_sha256_at_freeze"] = _DigestMapComparisonBypass(
                value["packet_sha256_at_freeze"]
            )
        return value

    with monkeypatch.context() as both_layers_disabled:
        both_layers_disabled.setattr(
            TOOL, "_json_lines", without_read_digest_check
        )
        both_layers_disabled.setattr(
            TOOL, "_load_json_object", without_freeze_digest_check
        )
        bypassed_join, bypassed_reasons = TOOL._load_adjudication(
            manifest_path, manifest, slots, final_attempts
        )
    assert bypassed_reasons == []
    assert bypassed_join["s01"]["r1_detected"] is False
    assert bypassed_join["s02"]["r1_detected"] is True


def test_reader_disagreement_is_conservative(tmp_path: Path) -> None:
    packet_ids = ("a" * 32, "b" * 32)
    runs = ("r01", "r02")
    slots = [
        {"slot_id": "s01", "case": "POS", "arm": "max"},
        {"slot_id": "s02", "case": "POS", "arm": "high"},
    ]
    packet_rows = []
    final_attempts = {}
    for packet_id, run_id, slot in zip(packet_ids, runs, slots):
        filename = f"packet-{packet_id}.md"
        body = _long_output().encode()
        (tmp_path / filename).write_bytes(body)
        packet_rows.append(
            {
                "packet_id": packet_id,
                "filename": filename,
            }
        )
        final_attempts[slot["slot_id"]] = {
            "run_id": run_id,
            "output_sha256": TOOL._sha256(body),
        }
    state = _canonical(
        tmp_path / "packet-state.json",
        {
            "schema_version": 2,
            "mask_strength": "same-owner-advisory",
            "packets": packet_rows,
        },
    )
    parent = _canonical(
        tmp_path / "parent.json",
        {
            "verdicts": [
                {"packet_id": packet_ids[0], "r1_detected": True, "findings": []},
                {"packet_id": packet_ids[1], "r1_detected": False, "findings": []},
            ]
        },
    )
    second = _canonical(
        tmp_path / "second.json",
        {
            "verdicts": [
                {"packet_id": packet_ids[0], "r1_detected": False, "findings": []},
                {"packet_id": packet_ids[1], "r1_detected": True, "findings": []},
            ]
        },
    )
    log = tmp_path / "verdicts.jsonl"
    TOOL.append_verdicts(state, log, "parent", parent)
    TOOL.append_verdicts(state, log, "second-reader", second)
    freeze = tmp_path / "freeze.json"
    TOOL.freeze_verdicts(state, log, freeze)
    custodian_root = tmp_path / "custodian"
    custodian_root.mkdir(mode=0o700)
    custodian_secret = _canonical(
        custodian_root / ("mapping-" + "c" * 48 + ".json"),
        {
            "mapping": [
                {
                    "packet_id": packet_id,
                    "run_id": run_id,
                    "slot_id": slot["slot_id"],
                    "packet_sha256": TOOL._sha256(
                        (tmp_path / f"packet-{packet_id}.md").read_bytes()
                    ),
                    "score_input_sha256": TOOL._sha256(
                        (tmp_path / f"packet-{packet_id}.md").read_bytes()
                    ),
                }
                for packet_id, run_id, slot in zip(packet_ids, runs, slots)
            ]
        },
    )
    custodian_secret.chmod(0o600)
    revealed = tmp_path / "revealed.json"
    TOOL.reveal_mapping(state, custodian_root, log, freeze, revealed)
    judgments = [
        {
            "slot_id": slot["slot_id"],
            "packet_id": packet_id,
            "score_input_sha256": final_attempts[slot["slot_id"]]["output_sha256"],
            "combined_verdict_sha256": "0" * 64,
            "r1_detected": expected,
            "reader_agreement": True,
        }
        for slot, packet_id, expected in zip(slots, packet_ids, (True, False))
    ]
    manifest = {
        "packet_state": _descriptor(state, tmp_path),
        "verdict_log": _descriptor(log, tmp_path),
        "verdict_freeze": _descriptor(freeze, tmp_path),
        "revealed_map": _descriptor(revealed, tmp_path),
        "judgments": judgments,
    }
    manifest_path = _canonical(tmp_path / "manifest.json", manifest)
    joined, reasons = TOOL._load_adjudication(
        manifest_path, manifest, slots, final_attempts
    )
    assert joined["s01"]["r1_detected"] is False
    assert joined["s01"]["reader_agreement"] is False
    assert any("adjudication r1_detected mismatch" in reason for reason in reasons)


def test_reader_disagreement_uses_conservative_miss() -> None:
    source = _TOOL_PATH.read_text(encoding="utf-8")
    assert 'parent_verdict.get("r1_detected") is True' in source
    assert 'second_verdict.get("r1_detected") is True' in source
    assert '"disagreement_policy": "conservative-miss"' in source


def test_attempt_root_escape_is_rejected(tmp_path: Path) -> None:
    slots, attempts, rows = _timing_rows()
    reasons = _timing_reasons(rows, slots, attempts, tmp_path / "expected-root")
    assert any("outside run root" in reason for reason in reasons)


def test_m5_generated_session_rows_require_set_equality() -> None:
    source = _TOOL_PATH.read_text(encoding="utf-8")
    assert "sorted(actual_sessions) != sorted(expected_sessions)" in source
    assert "generated session row set mismatch" in source


def test_tool_import_reuses_ledger_token_and_outcome_definitions() -> None:
    source = _TOOL_PATH.read_text(encoding="utf-8")
    assert TOOL.LEDGER.OUTCOME_PRECEDENCE == (
        "aborted_turn",
        "incomplete",
        "fragment",
        "completed",
    )
    assert "def _billable" not in source
    assert "OUTCOME_PRECEDENCE =" not in source
    assert 'model_reasoning_effort = "max"' not in source


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
