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
import base64
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
from typing import Any, Callable

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
model = args[args.index("-m") + 1]
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
  "turn_id": turn, "cwd": os.getcwd(), "model": model, "effort": effort}},
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


_STAGE2_HISTORICAL_PLAN_SOURCE = (
    "/work/1/SFC/tanab/dev-wave-jobs/"
    "dev-wave-t682-provenance-known-violations/s2-plan.md"
)
# Exact bytes copied from the real, non-T-181/T-182/T-189 artifact above.
_STAGE2_HISTORICAL_PLAN = (
    "必読ファイルを読めなかったため、指示どおり dev-wave 段 2 を即時停止しました。\n"
    "\n"
    "読めなかった path:\n"
    "\n"
    "`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/verbatim/README.md`\n"
    "\n"
    "ファイル更新・pytest 実行・プラン起草はいずれも行っていません。"
)


def _make_fake_stage2_downstream(path: Path) -> Path:
    return _make_executable(
        path,
        r'''#!/usr/bin/env python3
import base64
import os
from pathlib import Path
import sys
import time

if "--version" in sys.argv:
    print("stage2-fake-codex 1.0")
    raise SystemExit(0)

args = sys.argv[1:]
output = Path(args[args.index("-o") + 1])
payload = sys.stdin.buffer.read()
codex_home = Path(os.environ["CODEX_HOME"])
Path(os.environ["STAGE2_CODEX_HOME_RECORD"]).write_text(
    os.fspath(codex_home) + "\n" + (codex_home / "config.toml").read_text(),
    encoding="utf-8",
)
capture = Path(os.environ["STAGE2_CAPTURE"])
capture.parent.mkdir(parents=True, exist_ok=True)
with capture.open("ab") as stream:
    stream.write(base64.b64encode(payload) + b"\n")
counter = Path(os.environ["STAGE2_COUNTER"])
count = int(counter.read_text()) if counter.exists() else 0
count += 1
counter.write_text(str(count))
pid_file = Path(os.environ["STAGE2_PID"])
pid_file.write_text(f"{os.getpid()} {os.getpgrp()}\n")
mode = os.environ.get("STAGE2_MODE", "success")
if mode == "hang":
    time.sleep(30)
if mode in {"tamper-plan", "tamper-plan-fail"}:
    plan = Path(os.environ["STAGE2_PLAN_PATH"])
    moved = plan.with_name(plan.name + ".moved")
    if plan.exists() and not plan.is_symlink():
        plan.rename(moved)
        plan.write_bytes(b"replacement plan")
if mode == "tamper-contract":
    Path(os.environ["STAGE2_CONTRACT_PATH"]).write_bytes(b"tampered")
if mode in {"always-fail", "fail-once", "tamper-plan-fail"} and (
    mode == "always-fail" or count == 1
):
    raise SystemExit(7)
output.write_bytes(b"ack")
''',
    )


def _stage2_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str = "success",
    fix_pass_limit: int = 0,
    plan_bytes: bytes | None = None,
) -> dict[str, Any]:
    run_root = tmp_path / "stage2-run-root"
    run_root.mkdir(parents=True)
    plan = tmp_path / "historical-plan.md"
    plan.write_bytes(
        _STAGE2_HISTORICAL_PLAN.encode("utf-8")
        if plan_bytes is None
        else plan_bytes
    )
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    config = tmp_path / "config.toml"
    auth = tmp_path / "auth.json"
    config.write_text("model = 'gpt-5.6-sol'\n", encoding="utf-8")
    auth.write_text('{"token":"fixture"}\n', encoding="utf-8")
    codex = _make_fake_stage2_downstream(tmp_path / "fake-stage2-codex")
    capture = tmp_path / "stdin.b64"
    counter = tmp_path / "calls.txt"
    pid_file = tmp_path / "downstream.pid"
    codex_home_record = tmp_path / "codex-home.txt"
    monkeypatch.setenv("STAGE2_MODE", mode)
    monkeypatch.setenv("STAGE2_CAPTURE", os.fspath(capture))
    monkeypatch.setenv("STAGE2_COUNTER", os.fspath(counter))
    monkeypatch.setenv("STAGE2_PID", os.fspath(pid_file))
    monkeypatch.setenv(
        "STAGE2_CODEX_HOME_RECORD", os.fspath(codex_home_record)
    )
    contract_path = run_root / "stage2-contract.json"
    monkeypatch.setenv(
        "STAGE2_PLAN_PATH", os.fspath(run_root / "stage2-plan-input")
    )
    monkeypatch.setenv("STAGE2_CONTRACT_PATH", os.fspath(contract_path))
    contract = TOOL.freeze_stage2_plan_replayer(
        plan,
        contract_path,
        TOOL.MODEL,
        "max",
        fix_pass_limit,
        snapshot=snapshot,
        acceptance_kind="execution-receipt",
        acceptance_reason="fixture observes execution only",
        config_source=config,
        auth_source=auth,
        codex_binary=codex,
    )
    return {
        "run_root": run_root,
        "plan": plan,
        "snapshot": snapshot,
        "config": config,
        "auth": auth,
        "codex": codex,
        "capture": capture,
        "counter": counter,
        "pid_file": pid_file,
        "codex_home_record": codex_home_record,
        "contract_path": contract_path,
        "contract": contract,
        "result_path": run_root / "result.json",
    }


def _run_stage2_fixture(
    fixture: dict[str, Any],
    *,
    timeout_s: float = 1.0,
) -> tuple[dict[str, Any], int]:
    return TOOL.replay_stage2_plan(
        fixture["contract_path"],
        fixture["run_root"],
        fixture["result_path"],
        fixture["snapshot"],
        fixture["config"],
        fixture["auth"],
        fixture["codex"],
        wall_clock_timeout_s=timeout_s,
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
    mutate_launch: Callable[[dict[str, Any]], None] | None = None,
    mutate_launch_after_identity: Callable[[dict[str, Any]], None] | None = None,
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
        "-m",
        TOOL.MODEL,
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
        "requested_model": TOOL.MODEL,
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
        "normalized_argv": TOOL._normalized_exec_argv(
            argv, TOOL.MODEL, "max"
        ),
        "bwrap_binary": str(bwrap.resolve()),
        "bwrap_binary_sha256": TOOL._sha256(bwrap.read_bytes()),
        "bwrap_version": "bwrap 0.6.1",
        "bwrap_argv": bwrap_argv,
        "actual_process_argv": argv,
        "actual_process_argv_normalized": TOOL._normalized_exec_argv(
            argv, TOOL.MODEL, "max"
        ),
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
    if mutate_launch is not None:
        mutate_launch(launch)
    launch["treatment_identity_sha256"] = TOOL._launch_identity_value(launch)
    if mutate_launch_after_identity is not None:
        mutate_launch_after_identity(launch)
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
        expected_requested_model=TOOL.MODEL,
    )
    return {"receipt": receipt, "rc": rc, "rollout": rollout}


def _collect_manual_run(
    root: Path,
    expected_requested_model: str,
) -> tuple[dict[str, Any], int]:
    launch_path = next(root.rglob("launch.json"))
    launch = json.loads(launch_path.read_text(encoding="utf-8"))
    oracle = json.loads(
        Path(launch["snapshot_oracle"]["path"]).read_text(encoding="utf-8")
    )
    return TOOL.collect_run(
        run_id="r01",
        case="POS",
        requested_effort="max",
        events=Path(launch["events"]["path"]),
        done=Path(launch["done"]["path"]),
        output=Path(launch["output_path"]),
        prompt=Path(launch["prompt"]["path"]),
        sessions_root=root / "sessions",
        snapshot=Path(oracle["snapshot"]),
        launch_receipt=launch_path,
        expected_requested_model=expected_requested_model,
    )


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


def _direct_supervisor_launch(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    requested_model: str | None = None,
) -> dict[str, Any]:
    snapshot = root / "snapshot"
    snapshot.mkdir(parents=True)
    prompt = root / "prompt.txt"
    prompt.write_text("prompt", encoding="utf-8")
    config = root / "config-source.toml"
    config.write_text("model='gpt-5.6-sol'\n", encoding="utf-8")
    auth = root / "auth-source.json"
    auth.write_text('{"token":"synthetic"}\n', encoding="utf-8")
    codex = _make_fake_codex(root / "fake-codex")
    bwrap = _make_executable(
        root / "fake-bwrap",
        "#!/bin/sh\n[ \"$1\" = \"--version\" ] && printf 'bwrap 0.6.1\\n'\n",
    )
    monkeypatch.setattr(
        TOOL,
        "verify_snapshot",
        lambda actual_snapshot, case: {
            "schema_version": TOOL.SCHEMA_VERSION,
            "case": case,
            "snapshot": os.fspath(Path(actual_snapshot).resolve()),
            "valid": True,
        },
    )
    slot: dict[str, Any] = {
        "slot_id": "s01",
        "case": "POS",
        "arm": "max",
        "block_id": "b01",
        "block_order": 1,
    }
    if requested_model is not None:
        slot["requested_model"] = requested_model
    completion = TOOL._supervise_one(
        run_id="r01",
        slot=slot,
        attempt=1,
        parent_run_id=None,
        schedule_sha256="a" * 64,
        run_root=root / "run-root",
        snapshot=snapshot,
        prompt=prompt,
        config_source=config,
        auth_source=auth,
        codex_binary=codex,
        bwrap_binary=bwrap,
        dry_run=True,
    )
    return json.loads(
        Path(completion["launch_receipt"]).read_text(encoding="utf-8")
    )


def _identity_receipt_for_model(model: str) -> dict[str, Any]:
    base = "/fixture"
    run_dir = f"{base}/run"
    workspace = f"{base}/workspace"
    output = f"{workspace}/answer.md"
    stderr = f"{workspace}/stderr.log"
    codex_home = f"{workspace}/codex-home"
    events = f"{workspace}/events.jsonl"
    done = f"{run_dir}/.done"
    prompt = f"{base}/prompt.txt"
    oracle = f"{run_dir}/snapshot-before.json"
    normalized_argv = [
        "/usr/local/bin/codex",
        "exec",
        "-m",
        model,
        "-c",
        'model_reasoning_effort="<EFFORT>"',
        "-s",
        "read-only",
        "-C",
        f"{base}/snapshot",
        "--json",
        "-o",
        "<OUTPUT>",
        "-",
    ]
    return {
        "case": "POS",
        "requested_model": model,
        "arm": "max",
        "events": {"path": events},
        "done": {"path": done},
        "prompt": {"path": prompt, "sha256": "1" * 64},
        "snapshot_oracle": {"path": oracle, "sha256": "2" * 64},
        "run_dir": run_dir,
        "agent_workspace": workspace,
        "output_path": output,
        "stderr_path": stderr,
        "codex_home": codex_home,
        "codex_config_sha256": "3" * 64,
        "codex_auth_sha256": "4" * 64,
        "cli_binary": "/usr/local/bin/codex",
        "cli_binary_sha256": "5" * 64,
        "cli_version": "codex-cli 0.146.0",
        "argv": [
            "/usr/local/bin/codex",
            "exec",
            "-m",
            model,
            "-c",
            "model_reasoning_effort=max",
            "-s",
            "read-only",
            "-C",
            f"{base}/snapshot",
            "--json",
            "-o",
            output,
            "-",
        ],
        "normalized_argv": normalized_argv,
        "bwrap_binary_sha256": "6" * 64,
        "bwrap_version": "bwrap 0.6.1",
        "bwrap_argv": [
            "/usr/bin/bwrap",
            "--ro-bind",
            f"{base}/snapshot",
            f"{base}/snapshot",
            "--",
            *normalized_argv,
        ],
        "actual_process_argv_normalized": normalized_argv,
        "environment": {
            "CODEX_HOME": codex_home,
            "HOME": "/tmp/t181-home",
            "LANG": "C.UTF-8",
        },
        "sandbox": {
            "snapshot_mount": "read-only",
            "home_masked": True,
            "tmp_masked": True,
        },
        "world_state": {
            "snapshot_verified_before": True,
            "git_environment_cleared": True,
        },
        "schedule_sha256": "7" * 64,
        "dry_run": True,
    }


def test_model_argv_is_explicit_and_identity_is_model_bound() -> None:
    snapshot = Path("/fixture/snapshot")
    output = Path("/fixture/output.md")
    sol = "gpt-5.6-sol"
    luna = "gpt-5.6-luna"
    sol_argv = TOOL._codex_exec_argv(
        Path("/usr/local/bin/codex"), sol, "max", snapshot, output
    )
    luna_argv = TOOL._codex_exec_argv(
        Path("/usr/local/bin/codex"), luna, "max", snapshot, output
    )
    assert sol_argv[sol_argv.index("-m") + 1] == sol
    assert luna_argv[luna_argv.index("-m") + 1] == luna
    normalized_sol = TOOL._normalized_exec_argv(sol_argv, sol, "max")
    normalized_luna = TOOL._normalized_exec_argv(luna_argv, luna, "max")
    assert normalized_sol[sol_argv.index("-m") + 1] == sol
    assert normalized_luna[luna_argv.index("-m") + 1] == luna
    assert 'model_reasoning_effort="<EFFORT>"' in normalized_sol
    assert "model_reasoning_effort=max" not in normalized_sol

    missing_model = [value for value in sol_argv if value not in {"-m", sol}]
    with pytest.raises(TOOL.ValidationError, match="one -m model option"):
        TOOL._normalized_exec_argv(missing_model, sol, "max")
    duplicate_model = [*sol_argv, "-m", luna]
    with pytest.raises(TOOL.ValidationError, match="one -m model option"):
        TOOL._normalized_exec_argv(duplicate_model, sol, "max")
    unknown_model = list(sol_argv)
    unknown_model[unknown_model.index("-m") + 1] = "gpt-5.6-unknown"
    with pytest.raises(TOOL.ValidationError, match="model is not allowed"):
        TOOL._normalized_exec_argv(unknown_model, sol, "max")
    with pytest.raises(TOOL.ValidationError, match="does not match"):
        TOOL._normalized_exec_argv(sol_argv, luna, "max")

    sol_hash = TOOL._launch_identity_value(_identity_receipt_for_model(sol))
    luna_hash = TOOL._launch_identity_value(_identity_receipt_for_model(luna))
    assert sol_hash == (
        "d711b0e4cea31dfeff04273e768a3e3d3ba7f07c7478df00ec592ac4d34c4157"
    )
    assert luna_hash == (
        "687b58a3c7362fbc3c8e852be7376560e151240572960dc75a47af397b3d256c"
    )
    assert sol_hash != luna_hash


def test_supervisor_falls_back_to_default_model_without_requested_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launch = _direct_supervisor_launch(tmp_path, monkeypatch)
    assert launch["requested_model"] == TOOL.MODEL
    assert launch["argv"][launch["argv"].index("-m") + 1] == TOOL.MODEL
    assert launch["normalized_argv"] == TOOL._normalized_exec_argv(
        launch["argv"], TOOL.MODEL, "max"
    )
    assert launch["treatment_identity_sha256"] == TOOL._launch_identity_value(
        launch
    )


def test_supervisor_binds_requested_model_to_argv_receipt_and_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    luna = "gpt-5.6-luna"
    launch = _direct_supervisor_launch(tmp_path, monkeypatch, luna)
    assert launch["requested_model"] == luna
    assert launch["argv"][launch["argv"].index("-m") + 1] == luna
    assert launch["normalized_argv"] == TOOL._normalized_exec_argv(
        launch["argv"], luna, "max"
    )
    assert launch["actual_process_argv"] == launch["argv"]
    assert launch["actual_process_argv_normalized"] == launch["normalized_argv"]
    assert launch["treatment_identity_sha256"] == TOOL._launch_identity_value(
        launch
    )

    sol_receipt = copy.deepcopy(launch)
    for field in (
        "argv",
        "normalized_argv",
        "bwrap_argv",
        "actual_process_argv",
        "actual_process_argv_normalized",
    ):
        sol_receipt[field] = [
            TOOL.MODEL if value == luna else value for value in sol_receipt[field]
        ]
    sol_receipt["requested_model"] = TOOL.MODEL
    assert TOOL._launch_identity_value(sol_receipt) != launch[
        "treatment_identity_sha256"
    ]


def test_collect_run_expected_requested_model_context_mismatch_is_routing(
    tmp_path: Path,
) -> None:
    run = _manual_run(tmp_path)
    rollout = run["rollout"]
    rows = [
        json.loads(line)
        for line in rollout.read_text(encoding="utf-8").splitlines()
    ]
    for row in rows:
        if row.get("type") == "turn_context":
            row["payload"]["model"] = "gpt-5.6-luna"
    rollout.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    receipt, rc = _collect_manual_run(tmp_path, TOOL.MODEL)
    assert rc == TOOL.RC_ROUTING
    assert receipt["failure_reasons"] == ["model mismatch"]


def test_collect_run_expected_requested_model_argv_mismatch_is_receipt_rc(
    tmp_path: Path,
) -> None:
    run = _manual_run(tmp_path)
    rollout = run["rollout"]
    rows = [
        json.loads(line)
        for line in rollout.read_text(encoding="utf-8").splitlines()
    ]
    for row in rows:
        if row.get("type") == "turn_context":
            row["payload"]["model"] = "gpt-5.6-luna"
    rollout.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    receipt, rc = _collect_manual_run(tmp_path, "gpt-5.6-luna")
    assert rc == TOOL.RC_RECEIPT
    assert receipt["failure_reasons"] == [
        "requested model does not match the -m argv value"
    ]


def test_collect_run_argv_model_mismatch_is_receipt_rc(
    tmp_path: Path,
) -> None:
    luna = "gpt-5.6-luna"

    def mutate_launch(launch: dict[str, Any]) -> None:
        launch["requested_model"] = luna
        model_position = launch["argv"].index("-m") + 1
        launch["argv"][model_position] = luna
        launch["normalized_argv"] = TOOL._normalized_exec_argv(
            launch["argv"], luna, "max"
        )
        launch["actual_process_argv"] = list(launch["argv"])
        launch["actual_process_argv_normalized"] = list(launch["normalized_argv"])
        launch["bwrap_argv"] = TOOL._bwrap_exec_argv(
            Path(launch["bwrap_binary"]),
            launch["argv"],
            Path(
                json.loads(
                    Path(launch["snapshot_oracle"]["path"]).read_text(
                        encoding="utf-8"
                    )
                )["snapshot"]
            ),
            Path(launch["codex_home"]),
            Path(launch["output_path"]),
            Path(launch["events"]["path"]),
            Path(launch["stderr_path"]),
            launch["environment"],
        )
        launch["treatment_identity_sha256"] = TOOL._launch_identity_value(launch)

    _manual_run(tmp_path, mutate_launch=mutate_launch)
    receipt, rc = _collect_manual_run(tmp_path, TOOL.MODEL)
    assert rc == TOOL.RC_RECEIPT
    assert receipt["failure_reasons"] == [
        "requested model does not match the -m argv value"
    ]


def test_collect_run_receipt_model_field_mismatch_is_receipt_rc(
    tmp_path: Path,
) -> None:
    def mutate_launch(launch: dict[str, Any]) -> None:
        launch["requested_model"] = "gpt-5.6-luna"

    _manual_run(tmp_path, mutate_launch_after_identity=mutate_launch)
    receipt, rc = _collect_manual_run(tmp_path, TOOL.MODEL)
    assert rc == TOOL.RC_RECEIPT
    assert receipt["failure_reasons"] == [
        "launch receipt requested model does not match argv"
    ]


def test_completed_ledger_row_records_launch_requested_model(tmp_path: Path) -> None:
    launch_path = tmp_path / "launch.json"
    launch_path.write_bytes(
        TOOL._canonical_bytes({"requested_model": "gpt-5.6-luna"})
    )
    ledger_path = tmp_path / "attempt-ledger.jsonl"
    row = {
        "phase": "completed",
        "launch_receipt": str(launch_path),
    }
    TOOL._append_jsonl(ledger_path, row)
    assert row["requested_model"] == "gpt-5.6-luna"
    assert json.loads(ledger_path.read_text(encoding="utf-8"))["requested_model"] == (
        "gpt-5.6-luna"
    )


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
            expected_requested_model=TOOL.MODEL,
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


def test_task_manifest_binds_frozen_provenance_to_literal_values() -> None:
    pos = TOOL.TASK_MANIFEST["tasks"]["POS"]
    assert TOOL.TASK_MANIFEST["schema_version"] == 3
    assert pos["benchmark_task_id"] == "POS"
    assert pos["legacy_case"] == "POS"
    assert pos["provenance"]["session_id"] == (
        "019faca2-6e1f-7601-bfc7-be27edcfb4ba"
    )
    assert pos["provenance"]["rollout_sha256"] == (
        "9b90d51079e6a2be4603b366d77283950fff79535f59dbb8b4f4eecb1374032b"
    )
    assert pos["provenance"]["prompt_source"]["sha256"] == (
        "511941738fd39a20ac9fb41ce2f4c3ed0039c35fca637ded0fa2fb6679667829"
    )
    assert pos["snapshot"]["numstat"] == [
        [3, 3, "docs/ai-provenance.md"],
        [45, 0, "docs/decisions.md"],
        [693, 0, "orchestrator/tests/test_check_ai_provenance.py"],
        [37, 0, "orchestrator/tests/test_check_docs.py"],
        [123, 10, "tools/check_ai_provenance.py"],
        [9, 1, "tools/check_docs.py"],
    ]
    assert TOOL.TASK_MANIFEST["shared_provenance"]["auxiliary_sessions"]["fix1"] == {
        "session_id": "019fac91-8cde-7f73-bce1-77a9d63b4269",
        "rollout_sha256": "f210f2e135f6cfdb2e6c2a40e81b784a2a8f4ac51135c353cf859365e17fb475",
    }


def test_v2_schedule_normalizer_is_explicit_and_non_mutating() -> None:
    legacy = {
        "schema_version": 2,
        "slots": [
            {"slot_id": "s01", "case": "POS", "arm": "max"},
            {"slot_id": "s02", "case": "NEG", "arm": "high"},
        ],
    }
    original = copy.deepcopy(legacy)
    normalized = TOOL.normalize_legacy_schedule(legacy)

    assert legacy == original
    assert normalized["schema_version"] == 3
    assert normalized["manifest_kind"] == "t181-task-manifest"
    assert normalized["slots"][0]["benchmark_task_id"] == "POS"
    assert normalized["slots"][0]["legacy_case"] == "POS"
    assert normalized["slots"][0]["cache_condition"] is None
    assert normalized["slots"][0]["price_version"] is None
    assert TOOL.expected_schedule_from_manifest(TOOL.TASK_MANIFEST, legacy) == {
        ("POS", "max"): 3,
        ("POS", "high"): 3,
        ("NEG", "max"): 2,
        ("NEG", "high"): 2,
    }


def test_expected_schedule_rejects_non_null_v2_cache_condition() -> None:
    legacy = {
        "schema_version": 2,
        "slots": [
            {
                "slot_id": "s01",
                "case": "POS",
                "arm": "max",
                "cache_condition": "cold",
                "price_version": None,
            }
        ],
    }
    with pytest.raises(TOOL.ValidationError, match="non-null values are not supported"):
        TOOL.expected_schedule_from_manifest(TOOL.TASK_MANIFEST, legacy)


def test_v3_nullable_dimensions_distinguish_missing_from_null() -> None:
    row = {
        "benchmark_task_id": "POS",
        "case": "POS",
        "cache_condition": None,
        "price_version": None,
    }
    assert TOOL.validate_nullable_dimensions(row) == row
    for field in ("cache_condition", "price_version"):
        missing = dict(row)
        del missing[field]
        with pytest.raises(TOOL.ValidationError, match=f"missing required field: {field}"):
            TOOL.normalize_schedule({"schema_version": 3, "slots": [missing]})


@pytest.mark.parametrize("field", ("cache_condition", "price_version"))
def test_non_null_nullable_dimension_is_fail_closed(field: str) -> None:
    row = {
        "benchmark_task_id": "POS",
        "case": "POS",
        "cache_condition": None,
        "price_version": None,
    }
    row[field] = "opaque-version-token"
    with pytest.raises(TOOL.ValidationError, match="non-null values are not supported"):
        TOOL.normalize_schedule({"schema_version": 3, "slots": [row]})


def test_benchmark_task_id_and_case_alias_conflict_is_rejected() -> None:
    with pytest.raises(TOOL.ValidationError, match="aliases conflict"):
        TOOL.normalize_schedule(
            {
                "schema_version": 3,
                "slots": [
                    {
                        "benchmark_task_id": "POS",
                        "case": "NEG",
                        "cache_condition": None,
                        "price_version": None,
                    }
                ],
            }
        )


def test_manifest_schedule_and_findings_are_dynamic() -> None:
    manifest = copy.deepcopy(TOOL.TASK_MANIFEST)
    manifest["tasks"] = {}
    for task_id, legacy_case, finding_id, source_case in (
        ("alpha", "legacy-alpha", "A-1", "POS"),
        ("beta", "legacy-beta", "B-9", "NEG"),
    ):
        task = copy.deepcopy(TOOL.TASK_MANIFEST["tasks"][source_case])
        task.update(
            {
                "benchmark_task_id": task_id,
                "legacy_case": legacy_case,
                "known_finding_ids": [finding_id],
            }
        )
        manifest["tasks"][task_id] = task
    schedule = {
        "schema_version": 3,
        "slots": [
            {
                "slot_id": "x01",
                "benchmark_task_id": "alpha",
                "legacy_case": "legacy-alpha",
                "arm": "low",
                "cache_condition": None,
                "price_version": None,
            },
            {
                "slot_id": "x02",
                "benchmark_task_id": "alpha",
                "case": "legacy-alpha",
                "arm": "low",
                "cache_condition": None,
                "price_version": None,
            },
            {
                "slot_id": "x03",
                "benchmark_task_id": "beta",
                "legacy_case": "legacy-beta",
                "arm": "high",
                "cache_condition": None,
                "price_version": None,
            },
        ],
    }
    assert TOOL.expected_schedule_from_manifest(manifest, schedule) == {
        ("alpha", "low"): 2,
        ("beta", "high"): 1,
    }
    assert TOOL.known_finding_ids_for_manifest(manifest) == {"A-1", "B-9"}


@pytest.mark.parametrize("normalizer, schema_version", [
    (TOOL.normalize_schedule, 3),
    (TOOL.normalize_legacy_schedule, 2),
])
@pytest.mark.parametrize("bad_manifest", ["empty_tasks", "invalid_finding_id"])
def test_schedule_normalizers_reject_malformed_manifest(
    normalizer: Callable[..., dict[str, Any]],
    schema_version: int,
    bad_manifest: str,
) -> None:
    manifest = copy.deepcopy(TOOL.TASK_MANIFEST)
    if bad_manifest == "empty_tasks":
        manifest["tasks"] = {}
    else:
        task = copy.deepcopy(manifest["tasks"]["POS"])
        task["known_finding_ids"] = [1]
        manifest["tasks"] = {"POS": task}
    with pytest.raises(TOOL.ValidationError):
        normalizer(
            {"schema_version": schema_version, "slots": []},
            manifest=manifest,
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


def test_build_snapshot_base_pack_transfers_unreferenced_base_closure_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    TOOL._run(("git", "init", "--quiet"), cwd=source)
    tracked = source / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    TOOL._run(("git", "add", tracked.name), cwd=source)
    TOOL._run(
        (
            "git",
            "-c",
            "user.name=T989",
            "-c",
            "user.email=t989@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "base",
        ),
        cwd=source,
    )
    base_commit = TOOL._git(source, "rev-parse", "HEAD").decode().strip()
    tracked.write_text("integrated\n", encoding="utf-8")
    TOOL._run(("git", "add", tracked.name), cwd=source)
    TOOL._run(
        (
            "git",
            "-c",
            "user.name=T989",
            "-c",
            "user.email=t989@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "integrated",
        ),
        cwd=source,
    )
    integrated_commit = TOOL._git(source, "rev-parse", "HEAD").decode().strip()
    for ref in TOOL._git(
        source, "for-each-ref", "--format=%(refname)"
    ).decode().splitlines():
        TOOL._git(source, "update-ref", "-d", ref)
    assert TOOL._git(source, "for-each-ref", "--format=%(refname)") == b""

    monkeypatch.setattr(TOOL, "BASE_COMMIT", base_commit)
    monkeypatch.setattr(TOOL, "INTEGRATED_COMMIT", integrated_commit)
    monkeypatch.setattr(TOOL, "BRANCH", "snapshot-test")
    monkeypatch.setattr(TOOL, "TRACKED_PATHS", (tracked.name,))
    delegated_run = TOOL._run
    calls: list[tuple[tuple[str, ...], bytes | None]] = []

    def recording_run(argv: tuple[str, ...], **kwargs: Any) -> Any:
        calls.append((tuple(argv), kwargs.get("input_bytes")))
        completed = delegated_run(argv, **kwargs)
        if tuple(argv[:2]) == ("git", "index-pack"):
            transferred_git_dir = Path(kwargs["cwd"]) / ".git"
            object_info = transferred_git_dir / "objects/info"
            (object_info / "packs").write_text("P stale.pack\n", encoding="ascii")
            logs = transferred_git_dir / "logs"
            logs.mkdir(exist_ok=True)
            (logs / "seal-sentinel").write_bytes(b"")
            delegated_run(
                ("git", "hash-object", "-w", "--stdin"),
                cwd=kwargs["cwd"],
                input_bytes=b"unreachable seal sentinel\n",
            )
        return completed

    monkeypatch.setattr(TOOL, "_run", recording_run)
    snapshot = TOOL._build_snapshot_base(source, tmp_path / "snapshot")

    transfer_calls = [
        call
        for call in calls
        if len(call[0]) > 1
        and call[0][0] == "git"
        and call[0][1] in {"init", "pack-objects", "index-pack", "update-ref"}
    ]
    assert [argv for argv, _ in transfer_calls] == [
        ("git", "init", "--quiet", os.fspath(snapshot)),
        ("git", "pack-objects", "--revs", "--stdout"),
        ("git", "index-pack", "--stdin", "--fix-thin"),
        ("git", "update-ref", "refs/heads/snapshot-test", base_commit),
    ]
    assert transfer_calls[1][1] == (base_commit + "\n").encode("ascii")
    assert not any(
        len(argv) > 1 and argv[0] == "git" and argv[1] in {"clone", "fetch"}
        for argv, _ in calls
    )

    source_objects = {
        row.split(maxsplit=1)[0]
        for row in TOOL._git(source, "rev-list", "--objects", base_commit).splitlines()
    }
    snapshot_objects = set(
        TOOL._git(
            snapshot,
            "cat-file",
            "--batch-all-objects",
            "--batch-check=%(objectname)",
        ).splitlines()
    )
    assert snapshot_objects == source_objects
    assert TOOL._run(
        ("git", "cat-file", "-e", integrated_commit),
        cwd=snapshot,
        check=False,
    ).returncode != 0
    assert TOOL._git(
        snapshot, "for-each-ref", "--format=%(refname)"
    ).decode().splitlines() == ["refs/heads/snapshot-test"]
    assert TOOL._git(snapshot, "symbolic-ref", "HEAD").decode().strip() == (
        "refs/heads/snapshot-test"
    )
    git_dir = TOOL._git_dir(snapshot)
    assert not TOOL._path_lexists(git_dir / "logs")
    object_info = git_dir / "objects/info"
    assert object_info.is_dir()
    assert list(object_info.iterdir()) == []
    fsck = TOOL._run(
        ("git", "fsck", "--unreachable", "--no-reflogs"),
        cwd=snapshot,
    )
    unreachable_rows = [
        row
        for stream in (fsck.stdout, fsck.stderr)
        for row in stream.splitlines()
        if row.startswith(b"unreachable ")
    ]
    assert unreachable_rows == []
    for relative in ("shallow", "FETCH_HEAD", "packed-refs"):
        assert not TOOL._path_lexists(git_dir / relative)
    assert TOOL._git(snapshot, "remote") == b""
    remote_config = TOOL._run(
        ("git", "config", "--get-regexp", r"^remote\."),
        cwd=snapshot,
        check=False,
    )
    assert remote_config.returncode == 1
    assert remote_config.stdout == b""


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

    for repository in (snapshot, submodule):
        TOOL._git(repository, "commit-graph", "write", "--reachable")
        graph = TOOL._git_dir(repository) / "objects/info/commit-graph"
        assert graph.is_file()
        assert TOOL._run(
            ("git", "commit-graph", "verify"),
            cwd=repository,
            check=False,
        ).returncode == 0

    TOOL._seal_git_object_closure(snapshot)

    for repository in (snapshot, submodule):
        object_info = TOOL._git_dir(repository) / "objects/info"
        assert object_info.is_dir()
        assert list(object_info.iterdir()) == []


def test_git_closure_rejects_shallow_without_overrejecting_clean_snapshot(
    tmp_path: Path,
) -> None:
    snapshot, _, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    TOOL._seal_git_object_closure(snapshot)
    expected_refs = [f"refs/heads/{TOOL.BRANCH}"]
    reasons, _ = TOOL._one_git_closure_reasons(
        snapshot, snapshot, expected_refs
    )
    assert reasons == []

    git_dir = TOOL._git_dir(snapshot)
    head = TOOL._git(snapshot, "rev-parse", "HEAD").decode().strip()
    (git_dir / "shallow").write_text(head + "\n", encoding="ascii")
    reasons, _ = TOOL._one_git_closure_reasons(
        snapshot, snapshot, expected_refs
    )
    assert reasons == [".: shallow closure is not empty"]


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
    repositories, _ = TOOL._submodule_inventory(
        snapshot, allow_builder_transport=True
    )
    for repository in repositories:
        subprocess.run(
            ["git", "checkout", "--detach", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
    TOOL._seal_git_object_closure(snapshot)
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
    delegated_copytree = shutil.copytree

    def copy_with_absolute_worktree(
        src: Any,
        dst: Any,
        symlinks: bool = False,
        ignore: Any = None,
        copy_function: Callable[..., Any] = shutil.copy2,
        ignore_dangling_symlinks: bool = False,
        dirs_exist_ok: bool = False,
    ) -> Any:
        copied = delegated_copytree(
            src,
            dst,
            symlinks,
            ignore,
            copy_function,
            ignore_dangling_symlinks,
            dirs_exist_ok,
        )
        if Path(src).resolve() != base:
            return copied
        destination = Path(dst)
        submodule = destination / submodule_relative
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
        return copied

    monkeypatch.setattr(TOOL.shutil, "copytree", copy_with_absolute_worktree)
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


def test_derived_preflight_rejects_forbidden_includeif_config(
    tmp_path: Path,
) -> None:
    base = _synthetic_relocatable_nested_snapshot(tmp_path)
    derived = tmp_path / "derived"
    submodule = base / "deps/child"
    git_dir = TOOL._git_dir(submodule)
    derived_git_dir = derived / git_dir.relative_to(base)
    key = f"includeIf.gitdir:{derived_git_dir}.path"
    subprocess.run(
        [
            "git",
            "config",
            "--file",
            os.fspath(git_dir / "config"),
            key,
            "derived-only.conf",
        ],
        check=True,
        capture_output=True,
    )

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._preflight_snapshot_relocation(base)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        "snapshot repository local config is not allowlisted: "
        f"deps/child: {[key.lower()]}",
    )


def _synthetic_nested_submodule_snapshot(
    tmp_path: Path,
    *,
    seal: bool = False,
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
    if seal:
        TOOL._seal_git_object_closure(snapshot)
    return snapshot, submodule, nested_gitlink


def _synthetic_verify_snapshot_with_submodules(
    tmp_path: Path,
    submodules: tuple[tuple[str, bool], ...],
    *,
    source_setup: Callable[[Path, int], None] | None = None,
    initialized_setup: Callable[[Path, int], None] | None = None,
    ignore_all: bool = False,
) -> Path:
    source_rows: list[tuple[str, bool, Path, str]] = []
    for index, (relative, initialized) in enumerate(submodules):
        source = tmp_path / f"source-{index}"
        source.mkdir()
        subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
        (source / "child.txt").write_text(
            f"child {index}\n", encoding="utf-8"
        )
        if source_setup is not None:
            source_setup(source, index)
        subprocess.run(["git", "add", "--all"], cwd=source, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=T1223",
                "-c",
                "user.email=t1223@example.invalid",
                "commit",
                "-m",
                f"child {index}",
            ],
            cwd=source,
            check=True,
            capture_output=True,
        )
        head = TOOL._git(source, "rev-parse", "HEAD").decode().strip()
        source_rows.append((relative, initialized, source, head))

    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    subprocess.run(["git", "init"], cwd=snapshot, check=True, capture_output=True)
    (snapshot / "root.txt").write_text("root\n", encoding="utf-8")
    subprocess.run(["git", "add", "root.txt"], cwd=snapshot, check=True)
    if source_rows:
        modules = "".join(
            f'[submodule "child-{index}"]\n'
            f"\tpath = {relative}\n"
            f"\turl = {source}\n"
            + ("\tignore = all\n" if ignore_all else "")
            for index, (relative, _, source, _) in enumerate(source_rows)
        )
        (snapshot / ".gitmodules").write_text(modules, encoding="utf-8")
        subprocess.run(["git", "add", ".gitmodules"], cwd=snapshot, check=True)
        for relative, _, _, head in source_rows:
            subprocess.run(
                [
                    "git",
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    f"160000,{head},{relative}",
                ],
                cwd=snapshot,
                check=True,
                capture_output=True,
            )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=T1223",
            "-c",
            "user.email=t1223@example.invalid",
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
    for index, (relative, initialized, _, _) in enumerate(source_rows):
        if initialized:
            subprocess.run(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "update",
                    "--init",
                    "--",
                    relative,
                ],
                cwd=snapshot,
                check=True,
                capture_output=True,
            )
            if initialized_setup is not None:
                initialized_setup(snapshot / relative, index)
    TOOL._seal_git_object_closure(snapshot)
    return snapshot


def _synthetic_verify_snapshot_spec(
    snapshot: Path,
    *,
    enforce_closure: bool,
    pin_submodule_manifest: bool = False,
) -> dict[str, Any]:
    verified_paths = ["root.txt"]
    if (snapshot / ".gitmodules").is_file():
        verified_paths.append(".gitmodules")
    spec = {
        "case": "POS",
        "head": TOOL._git(snapshot, "rev-parse", "HEAD").decode().strip(),
        "branch": TOOL.BRANCH,
        "tracked_paths": [],
        "hashes": {
            relative: TOOL._sha256((snapshot / relative).read_bytes())
            for relative in verified_paths
        },
        "numstat": [],
        "untracked": [],
        "modes": {
            relative: stat.S_IFREG | 0o644 for relative in verified_paths
        },
        "forbidden": [],
        "git_object_closure": enforce_closure,
    }
    if pin_submodule_manifest:
        _, manifest = TOOL._submodule_inventory(snapshot)
        spec["submodule_manifest_sha256"] = TOOL._submodule_manifest_sha256(
            manifest
        )
    return spec


def _assert_uninitialized_submodule_reason(
    caught: pytest.ExceptionInfo[TOOL.ValidationError],
    relative: str,
) -> None:
    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert f"submodule is not initialized: {relative}" in caught.value.reasons


def _submodule_content_reasons(snapshot: Path) -> list[str]:
    preflight_cache: dict[Path, tuple[str, ...]] = {}
    root_reasons = TOOL._cached_repository_preflight_reasons(
        snapshot, snapshot, preflight_cache
    )
    if root_reasons:
        return list(root_reasons)
    repositories, _ = TOOL._submodule_inventory(
        snapshot, preflight_cache=preflight_cache
    )
    return TOOL._submodule_content_identity_reasons(
        snapshot,
        repositories,
        preflight_cache=preflight_cache,
    )


def _assert_snapshot_rejected_with_single_reason(
    snapshot: Path,
    spec: dict[str, Any],
    expected_reason: str,
) -> None:
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS", spec=spec)
    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (expected_reason,)


def _assert_snapshot_rejected_contains_reason(
    snapshot: Path,
    spec: dict[str, Any],
    expected_reason: str,
) -> None:
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS", spec=spec)
    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert expected_reason in caught.value.reasons


def _child_head(snapshot: Path, relative: str = "deps/child") -> str:
    return TOOL._git(
        snapshot, "--no-replace-objects", "rev-parse", f"HEAD:{relative}"
    ).decode().strip()


def _empty_submodule_index_and_worktree(snapshot: Path) -> str:
    child = snapshot / "deps/child"
    subprocess.run(
        ["git", "read-tree", "--empty"],
        cwd=child,
        check=True,
        capture_output=True,
    )
    (child / "child.txt").unlink()
    return "initialized submodule index/HEAD tree mismatch: deps/child"


def test_submodule_content_identity_reasons_rejects_empty_index_and_worktree(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _empty_submodule_index_and_worktree(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_verify_snapshot_submodule_content_gate_rejects_empty_index_and_worktree(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _empty_submodule_index_and_worktree(snapshot)

    # End-to-end closure also reports git fsck and object-store unreachable objects.
    _assert_snapshot_rejected_contains_reason(snapshot, spec, expected_reason)


def _mutate_child_bytes_preserving_stat(snapshot: Path) -> str:
    path = snapshot / "deps/child/child.txt"
    before = path.stat()
    payload = path.read_bytes()
    replacement = payload.swapcase()
    assert len(replacement) == len(payload)
    assert replacement != payload
    path.write_bytes(replacement)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    return (
        "initialized submodule worktree/index mismatch: "
        "deps/child: child.txt"
    )


def test_submodule_content_identity_reasons_rejects_worktree_blob_mismatch(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _mutate_child_bytes_preserving_stat(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_verify_snapshot_submodule_content_gate_rejects_worktree_blob_mismatch_with_preserved_stat(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _mutate_child_bytes_preserving_stat(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def _add_index_entry_absent_from_head(snapshot: Path) -> str:
    child = snapshot / "deps/child"
    payload = (child / "child.txt").read_bytes()
    object_id = TOOL._git(
        child, "ls-files", "--stage", "--", "child.txt"
    ).decode().split()[1]
    (child / "extra.txt").write_bytes(payload)
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{object_id},extra.txt",
        ],
        cwd=child,
        check=True,
        capture_output=True,
    )
    return "initialized submodule index/HEAD tree mismatch: deps/child"


def test_submodule_content_identity_reasons_rejects_index_entry_absent_from_head_tree(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _add_index_entry_absent_from_head(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_verify_snapshot_submodule_content_gate_rejects_index_entry_absent_from_head_tree(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _add_index_entry_absent_from_head(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def _bind_child_marker_to_rogue_admin(snapshot: Path) -> str:
    admin = snapshot / ".git/modules/child-0"
    rogue = snapshot / ".git/modules/rogue"
    shutil.copytree(admin, rogue)
    (snapshot / "deps/child/.git").write_text(
        "gitdir: ../../.git/modules/rogue\n", encoding="utf-8"
    )
    return "initialized submodule gitdir/admin mismatch: deps/child"


def test_submodule_worktree_state_rejects_marker_bound_to_rogue_admin_dir(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _bind_child_marker_to_rogue_admin(snapshot)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._submodule_worktree_state(
            snapshot,
            "child-0",
            "deps/child",
            _child_head(snapshot),
            snapshot,
        )
    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (expected_reason,)


def test_verify_snapshot_submodule_content_gate_rejects_git_marker_bound_to_rogue_admin_dir(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _bind_child_marker_to_rogue_admin(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def test_verify_snapshot_submodule_gate_rejects_custom_spec_without_closure(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", False),)
    )
    assert not (snapshot / "deps/child").exists()
    assert not (snapshot / ".git/modules/deps/child").exists()
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=False)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    _assert_uninitialized_submodule_reason(caught, "deps/child")


def test_verify_snapshot_submodule_gate_rejects_custom_spec_with_closure(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", False),)
    )
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=True)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    _assert_uninitialized_submodule_reason(caught, "deps/child")


def test_verify_snapshot_submodule_gate_checks_every_manifest_row(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/a-initialized", True), ("deps/z-uninitialized", False)),
    )
    _, manifest = TOOL._submodule_inventory(snapshot)
    assert [row["path"] for row in manifest] == [
        "deps/a-initialized",
        "deps/z-uninitialized",
    ]
    assert [row["initialization"] for row in manifest] == [
        "initialized",
        "uninitialized",
    ]
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=False)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    _assert_uninitialized_submodule_reason(caught, "deps/z-uninitialized")


def test_verify_snapshot_submodule_gate_rejects_default_spec_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """正規 seam の ``spec=`` では未指定経路を固定できないため差替える。"""
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", False),)
    )
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=True)
    monkeypatch.setattr(TOOL, "_snapshot_spec", lambda case: spec)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS")

    _assert_uninitialized_submodule_reason(caught, "deps/child")


def test_verify_snapshot_submodule_gate_accepts_all_initialized(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),)
    )
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=True)

    oracle = TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    assert set(oracle) == {
        "schema_version",
        "case",
        "snapshot",
        "head",
        "branch",
        "dirty",
        "untracked",
        "numstat",
        "files",
        "submodules",
        "submodule_manifest_sha256",
        "git_object_closure",
        "filesystem_files",
        "manifest_sha256",
    }
    assert [row["initialization"] for row in oracle["submodules"]] == [
        "initialized"
    ]


def test_verify_snapshot_oracle_and_submodule_row_key_sets_are_literal(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),)
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    oracle = TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    assert set(oracle) == {
        "schema_version",
        "case",
        "snapshot",
        "head",
        "branch",
        "dirty",
        "untracked",
        "numstat",
        "files",
        "submodules",
        "submodule_manifest_sha256",
        "git_object_closure",
        "filesystem_files",
        "manifest_sha256",
    }
    assert oracle["submodules"]
    assert all(
        set(row) == {"path", "gitlink_commit", "initialization"}
        for row in oracle["submodules"]
    )


def test_git_closure_reuses_precomputed_submodule_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),)
    )
    inventory = TOOL._submodule_inventory
    calls = 0

    def counted(candidate: Path) -> tuple[list[Path], list[dict[str, str]]]:
        nonlocal calls
        calls += 1
        return inventory(candidate)

    monkeypatch.setattr(TOOL, "_submodule_inventory", counted)

    reasons, _, _ = TOOL._git_closure_reasons(snapshot, ())

    assert reasons == []
    assert calls == 1


def _add_ignored_extra_file(snapshot: Path) -> str:
    (snapshot / "deps/child/payload.txt").write_text(
        "ignored but observable\n", encoding="utf-8"
    )
    return (
        "initialized submodule worktree file-set mismatch: deps/child: "
        "extra=['payload.txt'], missing=[]"
    )


def test_submodule_content_identity_reasons_rejects_ignored_extra_file(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _add_ignored_extra_file(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_submodule_content_identity_reasons_rejects_walk_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    child = snapshot / "deps/child"
    denied = child / "denied"
    denied.mkdir()
    (denied / "payload.txt").write_text("hidden bytes\n", encoding="utf-8")
    original_mode = stat.S_IMODE(denied.stat().st_mode)
    os.chmod(denied, 0o000)
    try:
        try:
            with os.scandir(denied) as entries:
                next(entries, None)
        except PermissionError:
            pass
        else:
            original_walk = TOOL.os.walk

            def injected_walk(
                top: Path,
                topdown: bool = True,
                onerror: Callable[[OSError], None] | None = None,
                followlinks: bool = False,
            ) -> Any:
                assert Path(top) == child
                assert onerror is not None
                onerror(
                    PermissionError(
                        13, "injected unreadable directory", os.fspath(denied)
                    )
                )
                yield from original_walk(
                    top,
                    topdown=topdown,
                    onerror=onerror,
                    followlinks=followlinks,
                )

            monkeypatch.setattr(TOOL.os, "walk", injected_walk)

        assert _submodule_content_reasons(snapshot) == [
            "initialized submodule content cannot be inspected: "
            "deps/child: PermissionError"
        ]
    finally:
        os.chmod(denied, original_mode)


def test_verify_snapshot_submodule_content_gate_rejects_ignored_extra_file_without_closure(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=False, pin_submodule_manifest=True
    )
    expected_reason = _add_ignored_extra_file(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def _install_replacement_tree(snapshot: Path) -> str:
    child = snapshot / "deps/child"
    original = _child_head(snapshot)
    (child / "child.txt").write_text("other 0\n", encoding="utf-8")
    subprocess.run(["git", "add", "child.txt"], cwd=child, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=T1262",
            "-c",
            "user.email=t1262@example.invalid",
            "commit",
            "-m",
            "replacement",
        ],
        cwd=child,
        check=True,
        capture_output=True,
    )
    replacement = TOOL._git(child, "rev-parse", "HEAD").decode().strip()
    replacement_tree = TOOL._git(
        child,
        "--no-replace-objects",
        "rev-parse",
        f"{replacement}^{{tree}}",
    ).decode().strip()
    subprocess.run(
        ["git", "checkout", "--detach", original],
        cwd=child,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "replace", original, replacement],
        cwd=child,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "--no-replace-objects", "read-tree", replacement_tree],
        cwd=child,
        check=True,
        capture_output=True,
    )
    (child / "child.txt").write_text("other 0\n", encoding="utf-8")
    assert TOOL._git(child, "rev-parse", "HEAD").decode().strip() == original
    return "initialized submodule index/HEAD tree mismatch: deps/child"


def test_submodule_content_identity_reasons_rejects_replacement_ref_tree(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _install_replacement_tree(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_verify_snapshot_submodule_content_gate_rejects_replacement_ref_without_closure(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=False, pin_submodule_manifest=True
    )
    expected_reason = _install_replacement_tree(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def _replace_admin_with_symlink(snapshot: Path) -> str:
    admin = snapshot / ".git/modules/child-0"
    rogue = snapshot / ".git/modules/rogue"
    admin.rename(rogue)
    admin.symlink_to("rogue", target_is_directory=True)
    return (
        "initialized submodule administrative path contains a symlink: "
        "deps/child"
    )


def test_submodule_worktree_state_rejects_symlinked_expected_admin_path(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _replace_admin_with_symlink(snapshot)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._submodule_worktree_state(
            snapshot,
            "child-0",
            "deps/child",
            _child_head(snapshot),
            snapshot,
        )
    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (expected_reason,)


def test_verify_snapshot_submodule_content_gate_rejects_symlinked_expected_admin_path(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _replace_admin_with_symlink(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def _redirect_child_common_dir(snapshot: Path) -> str:
    admin = snapshot / ".git/modules/child-0"
    rogue = snapshot / ".git/modules/rogue"
    shutil.copytree(admin, rogue)
    (admin / "commondir").write_text("../rogue\n", encoding="utf-8")
    return "initialized submodule common-dir/admin mismatch: deps/child"


def test_submodule_worktree_state_rejects_external_common_dir(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _redirect_child_common_dir(snapshot)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._submodule_worktree_state(
            snapshot,
            "child-0",
            "deps/child",
            _child_head(snapshot),
            snapshot,
        )
    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (expected_reason,)


def test_verify_snapshot_submodule_content_gate_rejects_external_common_dir(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _redirect_child_common_dir(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def _source_with_symlink(source: Path, _index: int) -> None:
    (source / "link.txt").symlink_to("target-one")


def _mutate_symlink_target(snapshot: Path) -> str:
    path = snapshot / "deps/child/link.txt"
    path.unlink()
    path.symlink_to("target-two")
    return (
        "initialized submodule worktree/index mismatch: "
        "deps/child: link.txt"
    )


def test_submodule_content_identity_reasons_rejects_symlink_target_mismatch(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_symlink,
        ignore_all=True,
    )
    expected_reason = _mutate_symlink_target(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_verify_snapshot_submodule_content_gate_rejects_symlink_target_mismatch(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_symlink,
        ignore_all=True,
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _mutate_symlink_target(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def _source_with_executable(source: Path, _index: int) -> None:
    executable = source / "run.sh"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)


def _mutate_executable_bit(snapshot: Path) -> str:
    path = snapshot / "deps/child/run.sh"
    path.chmod(path.stat().st_mode & ~stat.S_IXUSR)
    return (
        "initialized submodule worktree/index mode mismatch: "
        "deps/child: run.sh"
    )


def test_submodule_content_identity_reasons_rejects_executable_bit_mismatch(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_executable,
        ignore_all=True,
    )
    expected_reason = _mutate_executable_bit(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_verify_snapshot_submodule_content_gate_rejects_executable_bit_mismatch(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_executable,
        ignore_all=True,
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _mutate_executable_bit(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def _source_with_lf_attributes(source: Path, _index: int) -> None:
    (source / ".gitattributes").write_text(
        "*.txt text eol=lf\n", encoding="utf-8"
    )


def _checkout_child_as_crlf(submodule: Path, _index: int) -> None:
    path = submodule / "child.txt"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))


def test_submodule_content_identity_reasons_rejects_crlf_worktree_bytes(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_lf_attributes,
        initialized_setup=_checkout_child_as_crlf,
        ignore_all=True,
    )

    assert _submodule_content_reasons(snapshot) == [
        "initialized submodule worktree/index mismatch: "
        "deps/child: child.txt"
    ]


def test_verify_snapshot_submodule_content_gate_rejects_crlf_worktree_bytes(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_lf_attributes,
        initialized_setup=_checkout_child_as_crlf,
        ignore_all=True,
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )

    _assert_snapshot_rejected_with_single_reason(
        snapshot,
        spec,
        "initialized submodule worktree/index mismatch: "
        "deps/child: child.txt",
    )


def _source_with_nested_file(source: Path, _index: int) -> None:
    nested = source / "dir"
    nested.mkdir()
    (nested / "payload.txt").write_text("nested\n", encoding="utf-8")


def _replace_tracked_directory_with_symlink(
    snapshot: Path, tmp_path: Path
) -> str:
    directory = snapshot / "deps/child/dir"
    rogue = tmp_path / "rogue-tracked-directory"
    directory.rename(rogue)
    directory.symlink_to(rogue, target_is_directory=True)
    return (
        "initialized submodule tracked path crosses unsafe component: "
        "deps/child: dir/payload.txt"
    )


def test_submodule_content_identity_reasons_rejects_intermediate_directory_symlink(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_nested_file,
        ignore_all=True,
    )
    expected_reason = _replace_tracked_directory_with_symlink(snapshot, tmp_path)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_verify_snapshot_submodule_content_gate_rejects_intermediate_directory_symlink(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_nested_file,
        ignore_all=True,
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _replace_tracked_directory_with_symlink(snapshot, tmp_path)

    # End-to-end inventory also reports filesystem allowlist has extra files.
    _assert_snapshot_rejected_contains_reason(snapshot, spec, expected_reason)


def _add_forbidden_local_config(snapshot: Path) -> str:
    child = snapshot / "deps/child"
    subprocess.run(
        ["git", "config", "submodule.attack.url", "https://example.invalid"],
        cwd=child,
        check=True,
        capture_output=True,
    )
    return (
        "snapshot repository local config is not allowlisted: "
        "deps/child: ['submodule.attack.url']"
    )


def test_submodule_content_identity_reasons_rejects_post_seal_config(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    expected_reason = _add_forbidden_local_config(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("core.fsmonitor", "false"),
        ("core.autocrlf", "true"),
        ("filter.attack.clean", "false"),
        ("init.templateDir", "/tmp/template"),
        ("include.path", "missing-config"),
        ("extensions.worktreeConfig", "true"),
    ),
    ids=(
        "fsmonitor",
        "autocrlf",
        "filter",
        "template-dir",
        "include",
        "worktree-config",
    ),
)
def test_submodule_content_identity_reasons_rejects_forbidden_config_key(
    tmp_path: Path,
    key: str,
    value: str,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    child = snapshot / "deps/child"
    subprocess.run(
        ["git", "config", key, value],
        cwd=child,
        check=True,
        capture_output=True,
    )

    assert _submodule_content_reasons(snapshot) == [
        "snapshot repository local config is not allowlisted: "
        f"deps/child: ['{key.lower()}']"
    ]


def _local_config_keys(repository: Path) -> set[str]:
    output = subprocess.run(
        ["git", "config", "--local", "--name-only", "--list"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return set(output.splitlines())


def test_submodule_local_config_allowlist_matches_builder_outputs(
    tmp_path: Path,
) -> None:
    snapshot, child, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    assert _local_config_keys(snapshot) == {
        "core.repositoryformatversion",
        "core.filemode",
        "core.bare",
        "core.logallrefupdates",
        "submodule.deps/child.url",
        "submodule.deps/child.active",
    }
    child_keys = _local_config_keys(child)
    branch_keys = {key for key in child_keys if key.startswith("branch.")}
    assert {key.rsplit(".", 1)[1] for key in branch_keys} == {
        "remote",
        "merge",
    }
    assert len({key.rsplit(".", 1)[0] for key in branch_keys}) == 1
    assert child_keys - branch_keys == {
        "core.repositoryformatversion",
        "core.filemode",
        "core.bare",
        "core.logallrefupdates",
        "core.worktree",
        "remote.origin.url",
        "remote.origin.fetch",
    }
    assert TOOL._local_config_allowlist_reasons(
        snapshot,
        (snapshot, child),
        allow_builder_transport=True,
    ) == []

    TOOL._seal_git_object_closure(snapshot)

    assert _local_config_keys(snapshot) == {
        "core.repositoryformatversion",
        "core.filemode",
        "core.bare",
        "core.logallrefupdates",
    }
    assert _local_config_keys(child) == {
        "core.repositoryformatversion",
        "core.filemode",
        "core.bare",
        "core.logallrefupdates",
        "core.worktree",
    }


def test_seal_allows_preseal_transport_but_strict_inventory_rejects_postseal(
    tmp_path: Path,
) -> None:
    snapshot, child, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    assert "remote.origin.url" in _local_config_keys(child)

    TOOL._seal_git_object_closure(snapshot)

    subprocess.run(
        ["git", "config", "remote.postseal.url", "https://example.invalid"],
        cwd=child,
        check=True,
        capture_output=True,
    )
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._submodule_inventory(snapshot)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        "snapshot repository local config is not allowlisted: "
        "deps/child: ['remote.postseal.url']",
    )


def test_seal_preflight_rejects_forbidden_static_config(
    tmp_path: Path,
) -> None:
    snapshot, child, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    subprocess.run(
        ["git", "config", "core.fsmonitor", "false"],
        cwd=child,
        check=True,
        capture_output=True,
    )

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._seal_git_object_closure(snapshot)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        "snapshot repository local config is not allowlisted: "
        "deps/child: ['core.fsmonitor']",
    )


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("core.ignorecase", "true"),
        ("core.symlinks", "false"),
        ("core.precomposeunicode", "true"),
    ),
    ids=("ignorecase", "symlinks", "precomposeunicode"),
)
def test_submodule_content_identity_allows_filesystem_probe_config_keys(
    tmp_path: Path,
    key: str,
    value: str,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    subprocess.run(
        ["git", "config", key, value],
        cwd=snapshot / "deps/child",
        check=True,
        capture_output=True,
    )

    assert _submodule_content_reasons(snapshot) == []


def test_verify_snapshot_submodule_content_gate_rejects_post_seal_config(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _add_forbidden_local_config(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def test_submodule_content_identity_reasons_rejects_root_local_config(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    subprocess.run(
        ["git", "config", "core.autocrlf", "false"],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )

    assert _submodule_content_reasons(snapshot) == [
        "snapshot repository local config is not allowlisted: "
        ".: ['core.autocrlf']"
    ]


def test_verify_snapshot_submodule_content_gate_rejects_root_local_config(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=False, pin_submodule_manifest=True
    )
    subprocess.run(
        ["git", "config", "core.autocrlf", "false"],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )

    _assert_snapshot_rejected_with_single_reason(
        snapshot,
        spec,
        "snapshot repository local config is not allowlisted: "
        ".: ['core.autocrlf']",
    )


def test_verify_snapshot_root_preflight_precedes_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=False)
    subprocess.run(
        ["git", "config", "core.fsmonitor", "false"],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )
    inventory_calls = 0
    inventory = TOOL._submodule_inventory

    def counted_inventory(*args: Any, **kwargs: Any) -> Any:
        nonlocal inventory_calls
        inventory_calls += 1
        return inventory(*args, **kwargs)

    monkeypatch.setattr(TOOL, "_submodule_inventory", counted_inventory)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    assert caught.value.reasons == (
        "snapshot repository local config is not allowlisted: "
        ".: ['core.fsmonitor']",
    )
    assert inventory_calls == 0


def test_verify_snapshot_submodule_preflight_skips_worktree_git_and_aggregates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    child = snapshot / "deps/child"
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=False)
    spec["head"] = "0" * 40
    subprocess.run(
        ["git", "config", "core.fsmonitor", "false"],
        cwd=child,
        check=True,
        capture_output=True,
    )
    delegated = TOOL._run
    child_git_calls: list[tuple[str, ...]] = []

    def recording_run(argv: tuple[str, ...], **kwargs: Any) -> Any:
        if Path(kwargs["cwd"]).resolve() == child.resolve():
            child_git_calls.append(tuple(argv))
        return delegated(argv, **kwargs)

    monkeypatch.setattr(TOOL, "_run", recording_run)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    assert caught.value.reasons == (
        "HEAD mismatch: "
        f"{TOOL._git(snapshot, 'rev-parse', 'HEAD').decode().strip()} != "
        f"{'0' * 40}",
        "snapshot repository local config is not allowlisted: "
        "deps/child: ['core.fsmonitor']",
    )
    assert child_git_calls == [
        (
            "git",
            "--no-replace-objects",
            "rev-parse",
            "--show-object-format",
        ),
        (
            "git",
            "--no-replace-objects",
            "config",
            "--local",
            "--name-only",
            "--null",
            "--list",
        ),
    ]


def test_verify_snapshot_runs_each_repository_preflight_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),)
    )
    child = snapshot / "deps/child"
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=False)
    delegated = TOOL._run
    counts: dict[tuple[Path, str], int] = {}

    def recording_run(argv: tuple[str, ...], **kwargs: Any) -> Any:
        command = tuple(argv)
        kind = None
        if command[-2:] == ("rev-parse", "--show-object-format"):
            kind = "object-format"
        elif "config" in command and "--local" in command:
            kind = "local-config"
        if kind is not None:
            key = (Path(kwargs["cwd"]).resolve(), kind)
            counts[key] = counts.get(key, 0) + 1
        return delegated(argv, **kwargs)

    monkeypatch.setattr(TOOL, "_run", recording_run)

    oracle = TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    assert oracle["submodules"][0]["initialization"] == "initialized"
    assert counts == {
        (snapshot.resolve(), "object-format"): 1,
        (snapshot.resolve(), "local-config"): 1,
        (child.resolve(), "object-format"): 1,
        (child.resolve(), "local-config"): 1,
    }


def test_submodule_content_identity_reasons_rejects_non_sha1_object_format(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "sha256-repository"
    repository.mkdir()
    subprocess.run(
        ["git", "init", "--object-format=sha256"],
        cwd=repository,
        check=True,
        capture_output=True,
    )

    assert TOOL._submodule_content_identity_reasons(repository, ()) == [
        "snapshot repository object format is not sha1: .: sha256"
    ]


def test_submodule_content_identity_reasons_returns_reason_for_uninspectable_repo(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing"

    reasons = TOOL._submodule_content_identity_reasons(missing, ())

    assert reasons == [
        "snapshot repository object format cannot be inspected: .: "
        "FileNotFoundError"
    ]


def test_submodule_content_identity_reasons_returns_reason_for_escaped_repo(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "snapshot"
    outside = tmp_path / "outside"
    snapshot.mkdir()
    outside.mkdir()

    reasons = TOOL._submodule_content_identity_reasons(
        snapshot, (outside,)
    )

    assert reasons == [
        "initialized submodule repository escapes snapshot: "
        "<outside-snapshot>"
    ]


def test_submodule_content_identity_gate_uses_no_git_content_writer_or_filter(
) -> None:
    tree = ast.parse(_TOOL_PATH.read_text(encoding="utf-8"))
    selected = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        in {
            "_raw_blob_object_id",
            "_one_submodule_content_identity_reasons",
            "_submodule_content_identity_reasons",
        }
    }
    assert set(selected) == {
        "_raw_blob_object_id",
        "_one_submodule_content_identity_reasons",
        "_submodule_content_identity_reasons",
    }
    string_literals = {
        node.value
        for function in selected.values()
        for node in ast.walk(function)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "write-tree" not in string_literals
    assert "hash-object" not in string_literals


def test_submodule_identity_discovery_git_calls_disable_replace_objects() -> None:
    tree = ast.parse(_TOOL_PATH.read_text(encoding="utf-8"))
    selected = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"_git_dir", "_direct_submodules"}
    }
    assert set(selected) == {"_git_dir", "_direct_submodules"}
    for function in selected.values():
        literals = {
            node.value
            for node in ast.walk(function)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert "--no-replace-objects" in literals


def _clone_without_submodules(source: Path, destination: Path) -> Path:
    subprocess.run(
        ["git", "clone", "--no-local", os.fspath(source), os.fspath(destination)],
        check=True,
        capture_output=True,
    )
    return destination


def test_init_submodules_from_local_source_allows_dirty_source_content(
    tmp_path: Path,
) -> None:
    source = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),)
    )
    committed = (source / "deps/child/child.txt").read_bytes()
    (source / "deps/child/child.txt").write_bytes(b"dirty source only\n")
    destination = _clone_without_submodules(
        source, tmp_path / "destination"
    )

    TOOL._init_submodules_from_local_source(source, destination)

    assert (destination / "deps/child/child.txt").read_bytes() == committed
    assert (destination / "deps/child/child.txt").read_bytes() != (
        source / "deps/child/child.txt"
    ).read_bytes()


def test_init_submodules_from_local_source_rejects_forbidden_source_config(
    tmp_path: Path,
) -> None:
    source = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),)
    )
    subprocess.run(
        ["git", "config", "filter.attack.clean", "false"],
        cwd=source / "deps/child",
        check=True,
        capture_output=True,
    )
    destination = _clone_without_submodules(
        source, tmp_path / "destination"
    )

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._init_submodules_from_local_source(source, destination)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        "snapshot repository local config is not allowlisted: "
        "deps/child: ['filter.attack.clean']",
    )
    assert not (destination / "deps/child/.git").exists()


def test_init_submodules_from_local_source_allows_source_only_config_keys(
    tmp_path: Path,
) -> None:
    source = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),)
    )
    child = source / "deps/child"
    allowed = {
        "submodule.probe.update": "checkout",
        "submodule.probe.branch": "main",
        "submodule.probe.fetchRecurseSubmodules": "false",
        "submodule.probe.ignore": "dirty",
        "user.name": "T1262 Source",
        "user.email": "t1262-source@example.invalid",
    }
    for key, value in allowed.items():
        subprocess.run(
            ["git", "config", key, value],
            cwd=child,
            check=True,
            capture_output=True,
        )
    destination = _clone_without_submodules(
        source, tmp_path / "destination"
    )

    TOOL._init_submodules_from_local_source(source, destination)

    assert (destination / "deps/child/child.txt").read_bytes() == (
        child / "child.txt"
    ).read_bytes()


def test_init_submodules_from_local_source_rejects_unexpanded_source_key(
    tmp_path: Path,
) -> None:
    source = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),)
    )
    subprocess.run(
        ["git", "config", "core.fsmonitor", "false"],
        cwd=source / "deps/child",
        check=True,
        capture_output=True,
    )
    destination = _clone_without_submodules(
        source, tmp_path / "destination"
    )

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._init_submodules_from_local_source(source, destination)

    assert caught.value.reasons == (
        "snapshot repository local config is not allowlisted: "
        "deps/child: ['core.fsmonitor']",
    )
    assert not (destination / "deps/child/.git").exists()


def test_init_submodules_from_local_source_rejects_rogue_source_admin(
    tmp_path: Path,
) -> None:
    source = _synthetic_verify_snapshot_with_submodules(
        tmp_path, (("deps/child", True),), ignore_all=True
    )
    destination = _clone_without_submodules(
        source, tmp_path / "destination"
    )
    expected_reason = _bind_child_marker_to_rogue_admin(source)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._init_submodules_from_local_source(source, destination)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (expected_reason,)
    assert not (destination / "deps/child/.git").exists()


def _source_with_initialized_grandchild(source: Path, _index: int) -> None:
    grandchild = source.parent / "grandchild-source"
    grandchild.mkdir()
    subprocess.run(
        ["git", "init"], cwd=grandchild, check=True, capture_output=True
    )
    (grandchild / "grandchild.txt").write_text(
        "grandchild\n", encoding="utf-8"
    )
    subprocess.run(
        ["git", "add", "grandchild.txt"], cwd=grandchild, check=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=T1262",
            "-c",
            "user.email=t1262@example.invalid",
            "commit",
            "-m",
            "grandchild",
        ],
        cwd=grandchild,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            os.fspath(grandchild),
            "third_party/grandchild",
        ],
        cwd=source,
        check=True,
        capture_output=True,
    )


def _initialize_grandchild(submodule: Path, _index: int) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "update",
            "--init",
            "--",
            "third_party/grandchild",
        ],
        cwd=submodule,
        check=True,
        capture_output=True,
    )


def _mutate_initialized_grandchild(snapshot: Path) -> str:
    path = snapshot / "deps/child/third_party/grandchild/grandchild.txt"
    path.write_text("changed!!!\n", encoding="utf-8")
    return (
        "initialized submodule worktree/index mismatch: "
        "deps/child/third_party/grandchild: grandchild.txt"
    )


def test_submodule_content_identity_reasons_rejects_initialized_grandchild_change(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_initialized_grandchild,
        initialized_setup=_initialize_grandchild,
        ignore_all=True,
    )
    expected_reason = _mutate_initialized_grandchild(snapshot)

    assert _submodule_content_reasons(snapshot) == [expected_reason]


def test_verify_snapshot_submodule_content_gate_rejects_initialized_grandchild_change(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(
        tmp_path,
        (("deps/child", True),),
        source_setup=_source_with_initialized_grandchild,
        initialized_setup=_initialize_grandchild,
        ignore_all=True,
    )
    spec = _synthetic_verify_snapshot_spec(
        snapshot, enforce_closure=True, pin_submodule_manifest=True
    )
    expected_reason = _mutate_initialized_grandchild(snapshot)

    _assert_snapshot_rejected_with_single_reason(snapshot, spec, expected_reason)


def test_verify_snapshot_submodule_gate_accepts_empty_manifest(
    tmp_path: Path,
) -> None:
    snapshot = _synthetic_verify_snapshot_with_submodules(tmp_path, ())
    spec = _synthetic_verify_snapshot_spec(snapshot, enforce_closure=True)

    oracle = TOOL.verify_snapshot(snapshot, "POS", spec=spec)

    assert oracle["submodules"] == []


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
    snapshot, submodule, _ = _synthetic_nested_submodule_snapshot(
        tmp_path, seal=True
    )
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
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._assert_submodule_manifest_sha256(after, expected_sha256)
    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        "scheduled submodule initialization or gitlink state mismatch",
    )


def test_submodule_inventory_rejects_initialized_submodule_with_unresolvable_head(
    tmp_path: Path,
) -> None:
    snapshot, submodule, _ = _synthetic_nested_submodule_snapshot(
        tmp_path, seal=True
    )
    (TOOL._git_dir(submodule) / "HEAD").write_text(
        "ref: refs/heads/missing\n", encoding="utf-8"
    )

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._submodule_inventory(snapshot)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        "initialized submodule HEAD cannot be resolved: deps/child",
    )


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


def _synthetic_task_manifest(
    task_specs: tuple[tuple[str, str, str, str], ...] = (
        ("alpha", "POS", "positive", "alpha-finding"),
        ("beta", "NEG", "negative", "beta-finding"),
        ("gamma", "POS", "positive", "gamma-finding"),
    ),
) -> dict[str, Any]:
    manifest = copy.deepcopy(TOOL.TASK_MANIFEST)
    tasks: dict[str, Any] = {}
    for task_id, source_case, oracle_kind, finding_id in task_specs:
        task = copy.deepcopy(TOOL.TASK_MANIFEST["tasks"][source_case])
        task["benchmark_task_id"] = task_id
        task["legacy_case"] = f"legacy-{task_id}"
        task["stage"] = "stage-1"
        task["oracle_kind"] = oracle_kind
        task["known_finding_ids"] = [finding_id]
        tasks[task_id] = task
    manifest["tasks"] = tasks
    return manifest


def _v3_slot(
    *,
    slot_id: str,
    task_id: str,
    block_id: str,
    block_order: int,
    arm: str,
    requested_model: str,
    stage: str = "stage-1",
) -> dict[str, Any]:
    return {
        "slot_id": slot_id,
        "benchmark_task_id": task_id,
        "legacy_case": f"legacy-{task_id}",
        "stage": stage,
        "requested_model": requested_model,
        "cache_condition": None,
        "price_version": None,
        "arm": arm,
        "block_id": block_id,
        "block_order": block_order,
        "prompt_sha256": "a" * 64,
        "snapshot_manifest_sha256": "b" * 64,
        "submodule_manifest_sha256": "c" * 64,
    }


def test_validate_schedule_accepts_same_arm_different_requested_model_pair() -> None:
    schedule = {
        "schema_version": TOOL.TASK_MANIFEST_SCHEMA_VERSION,
        "slots": [
            _v3_slot(
                slot_id="s01",
                task_id="alpha",
                block_id="b01",
                block_order=1,
                arm="max",
                requested_model=TOOL.MODEL,
            ),
            _v3_slot(
                slot_id="s02",
                task_id="alpha",
                block_id="b01",
                block_order=2,
                arm="max",
                requested_model="gpt-5.6-luna",
            ),
        ],
    }
    slots, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert reasons == []
    assert {row["requested_model"] for row in slots} == {
        TOOL.MODEL,
        "gpt-5.6-luna",
    }
    assert all(row["benchmark_task_id"] == "alpha" for row in slots)


@pytest.mark.parametrize("field", ("cache_condition", "price_version"))
def test_validate_schedule_rejects_live_non_null_cache_or_price(
    field: str,
) -> None:
    schedule = {
        "schema_version": TOOL.TASK_MANIFEST_SCHEMA_VERSION,
        "slots": [
            _v3_slot(
                slot_id="s01",
                task_id="alpha",
                block_id="b01",
                block_order=1,
                arm="max",
                requested_model=TOOL.MODEL,
            ),
            _v3_slot(
                slot_id="s02",
                task_id="alpha",
                block_id="b01",
                block_order=2,
                arm="max",
                requested_model="gpt-5.6-luna",
            ),
        ],
    }
    schedule["slots"][0][field] = "unattested"
    _, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert any("non-null values are not supported" in reason for reason in reasons)


def test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid(
    benchmark_snapshots: dict[str, Any], tmp_path: Path
) -> None:
    _, source_slots = _schedule(tmp_path / "legacy-schedule.json", benchmark_snapshots)
    source = {"slots": copy.deepcopy(source_slots)}
    slots, reasons = TOOL._validate_schedule(source)
    assert "schema_version" not in source
    assert reasons == []
    assert slots[0]["requested_model"] == TOOL.MODEL
    assert slots[0]["arm"] != slots[1]["arm"]


def test_validate_verdict_accepts_manifest_finding_union_while_blind_and_rejects_unknown(
    tmp_path: Path,
) -> None:
    manifest = _synthetic_task_manifest(
        (
            ("alpha", "POS", "positive", "alpha-finding"),
            ("beta", "NEG", "negative", "beta-finding"),
        )
    )
    state, parent, _ = _packet_fixture(tmp_path)
    parent_value = json.loads(parent.read_text(encoding="utf-8"))
    parent_value["verdicts"][0]["findings"] = [
        {
            "real": True,
            "equivalent_to": "alpha-finding",
            "root_cause": None,
            "severity": "HIGH",
            "must_fix": True,
        }
    ]
    parent.write_bytes(TOOL._canonical_bytes(parent_value))
    log = tmp_path / "blind-verdicts.jsonl"
    result = TOOL.append_verdicts(
        state,
        log,
        "parent",
        parent,
        task_manifest=manifest,
    )
    assert result["appended"] == 1
    packet_id = json.loads(state.read_text(encoding="utf-8"))["packets"][0][
        "packet_id"
    ]
    row = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    TOOL._validate_verdict_row(
        row,
        {packet_id},
        task_manifest=manifest,
    )
    bad = _canonical(
        tmp_path / "bad.json",
        {
            "verdicts": [
                {
                    "packet_id": packet_id,
                    "r1_detected": False,
                    "findings": [
                        {
                            "real": True,
                            "equivalent_to": "not-in-manifest",
                            "root_cause": None,
                            "severity": "HIGH",
                            "must_fix": True,
                        }
                    ],
                }
            ]
        },
    )
    with pytest.raises(TOOL.ValidationError, match="unknown"):
        TOOL.append_verdicts(
            state,
            tmp_path / "bad-verdicts.jsonl",
            "second-reader",
            bad,
            task_manifest=manifest,
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


def test_find_rollout_session_meta_encoding_and_payload_identity_semantics(
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

        if name == "distinct-fields":
            with pytest.raises(TOOL.ValidationError) as excinfo:
                TOOL._find_rollout(sessions_root, session_id)
            assert excinfo.value.rc == TOOL.RC_SESSION
            assert str(excinfo.value) == (
                "session target-session rollout count is 0, expected 1"
            )
            continue

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


def _identity_session_meta_bytes(
    payload_id: Any,
    root_session_id: str,
    *,
    fork_marker: bool = False,
) -> bytes:
    payload: dict[str, Any] = {
        "id": payload_id,
        "session_id": root_session_id,
    }
    if fork_marker:
        payload["source"] = {"subagent": {"thread_spawn": {}}}
        payload["forked_from_id"] = root_session_id
    return (
        json.dumps(
            {"type": "session_meta", "payload": payload},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def test_find_rollout_disambiguates_parent_from_child_root_reference(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    child_id = "child-session"
    parent = _write_rollout(
        tmp_path / "rollout-0.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id),
    )
    child = _write_rollout(
        tmp_path / "rollout-1.jsonl",
        _identity_session_meta_bytes(child_id, parent_id),
    )

    assert TOOL._find_rollout(tmp_path, parent_id) == parent.resolve()
    assert TOOL._find_rollout(tmp_path, child_id) == child.resolve()


def test_find_rollout_disambiguates_fork_with_copied_parent_meta(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    child_id = "child-session"
    parent = _write_rollout(
        tmp_path / "rollout-0.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id),
    )
    child = _write_rollout(
        tmp_path / "rollout-1.jsonl",
        _identity_session_meta_bytes(
            child_id, parent_id, fork_marker=True
        )
        + _identity_session_meta_bytes(parent_id, parent_id),
    )

    assert TOOL._find_rollout(tmp_path, parent_id) == parent.resolve()
    assert TOOL._find_rollout(tmp_path, child_id) == child.resolve()


def test_find_rollout_fork_with_parent_meta_first_remains_ambiguous(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    child_id = "child-session"
    _write_rollout(
        tmp_path / "rollout-0.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id),
    )
    child = _write_rollout(
        tmp_path / "rollout-1.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id)
        + _identity_session_meta_bytes(
            child_id, parent_id, fork_marker=True
        ),
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, parent_id)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        "session parent-session rollout count is 2, expected 1"
    )
    assert TOOL._find_rollout(tmp_path, child_id) == child.resolve()


def test_find_rollout_appended_child_reference_does_not_promote_duplicate(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    parent_content = _identity_session_meta_bytes(parent_id, parent_id)
    _write_rollout(tmp_path / "rollout-0.jsonl", parent_content)
    _write_rollout(
        tmp_path / "rollout-1.jsonl",
        parent_content
        + _identity_session_meta_bytes("child-session", parent_id),
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, parent_id)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        "session parent-session rollout count is 2, expected 1"
    )


@pytest.mark.parametrize(
    ("payload_id", "variant"),
    (
        pytest.param(None, "null", id="null"),
        pytest.param(0, "zero", id="zero"),
        pytest.param(False, "false", id="false"),
        pytest.param("", "empty-string", id="empty-string"),
    ),
)
def test_find_rollout_non_string_id_does_not_fall_back_to_root_session(
    tmp_path: Path, payload_id: Any, variant: str
) -> None:
    session_id = "target-session"
    sessions_root = tmp_path / variant
    _write_rollout(
        sessions_root / "rollout-0.jsonl",
        _identity_session_meta_bytes(payload_id, session_id),
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(sessions_root, session_id)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        "session target-session rollout count is 0, expected 1"
    )


def test_find_rollout_true_duplicate_parent_identity_remains_rejected(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    parent_content = _identity_session_meta_bytes(parent_id, parent_id)
    _write_rollout(tmp_path / "rollout-0.jsonl", parent_content)
    _write_rollout(tmp_path / "rollout-1.jsonl", parent_content)

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, parent_id)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        "session parent-session rollout count is 2, expected 1"
    )


@pytest.mark.parametrize("fork_marker", (False, True), ids=("type-a", "type-b"))
def test_find_rollout_non_dict_leader_uses_first_determinable_identity(
    tmp_path: Path,
    fork_marker: bool,
) -> None:
    parent_id = "parent-session"
    candidate_content = (
        b'{"type":"session_meta","payload":["not-an-object"]}\n'
        + _identity_session_meta_bytes(parent_id, parent_id)
        + _identity_session_meta_bytes(
            "child-session", parent_id, fork_marker=fork_marker
        )
    )
    _write_rollout(tmp_path / "rollout-0.jsonl", candidate_content)
    _write_rollout(
        tmp_path / "rollout-1.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id),
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, parent_id)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        "session parent-session rollout count is 2, expected 1"
    )


def test_find_rollout_late_descendant_declaration_vetoes_parent_identity(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    child_id = "child-session"
    parent = _write_rollout(
        tmp_path / "rollout-0.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id),
    )
    child = _write_rollout(
        tmp_path / "rollout-1.jsonl",
        _identity_session_meta_bytes(child_id, child_id)
        + _identity_session_meta_bytes(parent_id, parent_id)
        + _identity_session_meta_bytes(child_id, parent_id),
    )

    assert TOOL._find_rollout(tmp_path, parent_id) == parent.resolve()
    assert TOOL._find_rollout(tmp_path, child_id) == child.resolve()


@pytest.mark.parametrize("fork_marker", (False, True), ids=("type-a", "type-b"))
def test_find_rollout_ineligible_pin_uses_identity_predicate_on_full_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fork_marker: bool,
) -> None:
    label = "test-ineligible-identity-predicate"
    parent_id = "parent-session"
    child_id = "child-session"
    parent_content = _identity_session_meta_bytes(parent_id, parent_id)
    child_content = _identity_session_meta_bytes(
        child_id, parent_id, fork_marker=fork_marker
    )
    if fork_marker:
        child_content += parent_content
    parent = _write_rollout(tmp_path / "rollout-0.jsonl", parent_content)
    child = _write_rollout(tmp_path / "rollout-1.jsonl", child_content)
    monkeypatch.setitem(TOOL.SESSION_IDS, label, parent_id)
    monkeypatch.delitem(TOOL.ROLLOUT_SHA256, label, raising=False)

    assert (
        TOOL._find_rollout(tmp_path, parent_id, pinned_label=label)
        == parent.resolve()
    )
    assert (
        TOOL._find_rollout(tmp_path, child_id, pinned_label=label)
        == child.resolve()
    )


def test_find_rollout_undetermined_identity_does_not_promote_duplicate(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    _write_rollout(
        tmp_path / "rollout-0.jsonl",
        _identity_session_meta_bytes(None, parent_id)
        + _identity_session_meta_bytes(parent_id, parent_id),
    )
    _write_rollout(
        tmp_path / "rollout-1.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id),
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, parent_id)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        "session parent-session rollout count is 2, expected 1"
    )


def test_find_rollout_empty_payload_leader_does_not_promote_duplicate(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    candidate_content = (
        b'{"type":"session_meta","payload":{}}\n'
        + _identity_session_meta_bytes(parent_id, parent_id)
        + _identity_session_meta_bytes("child-session", parent_id)
    )
    _write_rollout(tmp_path / "rollout-0.jsonl", candidate_content)
    _write_rollout(
        tmp_path / "rollout-1.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id),
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, parent_id)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        "session parent-session rollout count is 2, expected 1"
    )


def test_find_rollout_non_string_session_id_leader_does_not_promote_duplicate(
    tmp_path: Path,
) -> None:
    parent_id = "parent-session"
    candidate_content = (
        b'{"type":"session_meta","payload":{"session_id":7}}\n'
        + _identity_session_meta_bytes(parent_id, parent_id)
        + _identity_session_meta_bytes("child-session", parent_id)
    )
    _write_rollout(tmp_path / "rollout-0.jsonl", candidate_content)
    _write_rollout(
        tmp_path / "rollout-1.jsonl",
        _identity_session_meta_bytes(parent_id, parent_id),
    )

    with pytest.raises(TOOL.ValidationError) as excinfo:
        TOOL._find_rollout(tmp_path, parent_id)
    assert excinfo.value.rc == TOOL.RC_SESSION
    assert str(excinfo.value) == (
        "session parent-session rollout count is 2, expected 1"
    )


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


@pytest.mark.parametrize("fork_marker", (False, True), ids=("type-a", "type-b"))
def test_find_rollout_pinned_rejects_child_candidate_before_full_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fork_marker: bool,
) -> None:
    label = "test-parent-child-disambiguation"
    parent_id = "parent-session"
    child_id = "child-session"
    parent_content = _identity_session_meta_bytes(parent_id, parent_id)
    child_content = _identity_session_meta_bytes(
        child_id, parent_id, fork_marker=fork_marker
    )
    if fork_marker:
        child_content += parent_content
    child = _write_rollout(
        tmp_path / f"rollout-child-{parent_id}.jsonl", child_content
    )
    parent = _write_rollout(
        tmp_path / "rollout-parent.jsonl", parent_content
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=parent_id,
        content=child_content,
    )
    real_verify = TOOL._verify_rollout_sha
    verified: list[tuple[Path, str]] = []

    def record_successful_verification(path: Path, pin_label: str) -> None:
        real_verify(path, pin_label)
        verified.append((path, pin_label))

    monkeypatch.setattr(
        TOOL, "_verify_rollout_sha", record_successful_verification
    )

    assert child != parent
    assert (
        TOOL._find_rollout(tmp_path, parent_id, pinned_label=label)
        == parent.resolve()
    )
    assert verified == []

    verified_root = tmp_path / "verified"
    verified_id = f"verified-{fork_marker}"
    verified_content = _identity_session_meta_bytes(verified_id, verified_id)
    verified_candidate = _write_rollout(
        verified_root / f"rollout-parent-{verified_id}.jsonl",
        verified_content,
    )
    _install_rollout_pin(
        monkeypatch,
        label=label,
        session_id=verified_id,
        content=verified_content,
    )

    assert (
        TOOL._find_rollout(
            verified_root, verified_id, pinned_label=label
        )
        == verified_candidate.resolve()
    )
    assert verified == [(verified_candidate.resolve(), label)]


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


def test_collect_run_cli_binds_expected_model_to_requested_dest(
    tmp_path: Path,
) -> None:
    parsed = TOOL._parser().parse_args(
        [
            "collect-run",
            "--run-id",
            "r01",
            "--case",
            "POS",
            "--requested-effort",
            "max",
            "--events",
            os.fspath(tmp_path / "events.jsonl"),
            "--done",
            os.fspath(tmp_path / "done.json"),
            "--output",
            os.fspath(tmp_path / "answer.md"),
            "--prompt",
            os.fspath(tmp_path / "prompt.txt"),
            "--sessions-root",
            os.fspath(tmp_path / "sessions"),
            "--snapshot",
            os.fspath(tmp_path / "snapshot"),
            "--launch-receipt",
            os.fspath(tmp_path / "launch.json"),
            "--expected-model",
            "gpt-5.6-luna",
        ]
    )
    assert parsed.expected_requested_model == "gpt-5.6-luna"
    assert not hasattr(parsed, "expected_model")


def test_replay_passes_schedule_requested_model_to_collect_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    luna = "gpt-5.6-luna"
    root = tmp_path
    run_root = root / "run-root"
    attempts_root = run_root / "attempts"
    sessions_root = root / "sessions"
    snapshot = root / "snapshot"
    attempts_root.mkdir(parents=True)
    sessions_root.mkdir()
    snapshot.mkdir()
    slot = {
        "slot_id": "s01",
        "case": "POS",
        "arm": "max",
        "requested_model": luna,
        "block_id": "b01",
        "block_order": 1,
        "prompt_sha256": "1" * 64,
        "snapshot_manifest_sha256": "2" * 64,
        "submodule_manifest_sha256": "3" * 64,
    }
    schedule_path = _canonical(run_root / "schedule.json", {"slots": [slot]})
    schedule_sha = TOOL._sha256(schedule_path.read_bytes())
    prompt = _canonical(root / "prompt.txt", {"prompt": True})
    output = _canonical(root / "output.md", {"output": True})
    events = _canonical(root / "events.jsonl", {"events": True})
    done = _canonical(root / "done.json", {"done": True})
    oracle_value = {
        "snapshot": os.fspath(snapshot.resolve()),
        "submodule_manifest_sha256": slot["submodule_manifest_sha256"],
    }
    oracle = _canonical(root / "oracle.json", oracle_value)
    oracle_after = _canonical(root / "oracle-after.json", oracle_value)
    rollout = _canonical(sessions_root / "rollout-r01.jsonl", {"rollout": True})
    launch = _canonical(
        attempts_root / "launch.json",
        {
            "run_id": "r01",
            "slot_id": "s01",
            "attempt": 1,
            "parent_run_id": None,
            "case": "POS",
            "arm": "max",
            "requested_model": luna,
            "schedule_sha256": schedule_sha,
            "prompt": {"sha256": slot["prompt_sha256"]},
            "snapshot_oracle": {
                "sha256": slot["snapshot_manifest_sha256"]
            },
        },
    )
    receipt = _canonical(
        root / "receipt.json",
        {"rollout_path": os.fspath(rollout.resolve()), "wall_clock_ms": 0},
    )
    score = _canonical(root / "score.json", {})
    ledger = _canonical(run_root / "attempt-ledger.jsonl", {})
    attempts = [
        {
            "run_id": "r01",
            "slot_id": "s01",
            "attempt": 1,
            "parent_run_id": None,
            "launch_receipt": _descriptor(launch, root),
            "events": _descriptor(events, root),
            "done": _descriptor(done, root),
            "prompt": _descriptor(prompt, root),
            "output": _descriptor(output, root),
            "snapshot_oracle": _descriptor(oracle, root),
            "snapshot_after": _descriptor(oracle_after, root),
            "rollout": _descriptor(rollout, root),
            "receipt": _descriptor(receipt, root),
            "score": _descriptor(score, root),
        }
    ]
    manifest = {
        "schedule": _descriptor(schedule_path, root),
        "schedule_sha256": schedule_sha,
        "run_root": "run-root",
        "attempts_root": "run-root/attempts",
        "attempt_ledger": _descriptor(ledger, root),
        "max_schedule_gap_ms": TOOL.MAX_SCHEDULE_GAP_MS,
        "max_inter_block_gap_ms": TOOL.MAX_INTER_BLOCK_GAP_MS,
        "attempts": attempts,
    }
    manifest_path = _canonical(root / "manifest.json", manifest)
    captured: list[str] = []

    def fake_validate_schedule(
        schedule: dict[str, Any],
        *,
        task_manifest: Any = TOOL.TASK_MANIFEST,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        assert schedule["slots"][0]["requested_model"] == luna
        return schedule["slots"], []

    def fake_collect_run(**kwargs: Any) -> tuple[dict[str, Any], int]:
        captured.append(kwargs["expected_requested_model"])
        return (
            {
                "rollout_path": os.fspath(rollout.resolve()),
                "wall_clock_ms": 0,
            },
            0,
        )

    monkeypatch.setattr(TOOL, "_validate_schedule", fake_validate_schedule)
    monkeypatch.setattr(
        TOOL,
        "_validate_supervisor_ledger",
        lambda *args, **kwargs: (
            [
                {
                    "run_id": "r01",
                    "process_started": True,
                    "process_wall_ms": 0,
                }
            ],
            [],
        ),
    )
    monkeypatch.setattr(
        TOOL,
        "_load_adjudication",
        lambda *args, **kwargs: ({}, []),
    )
    monkeypatch.setattr(TOOL, "_apply_pair_invalidations", lambda attempts: None)
    monkeypatch.setattr(TOOL, "_retry_lineage_reasons", lambda grouped: [])
    monkeypatch.setattr(TOOL, "verify_snapshot", lambda actual, case: oracle_value)
    monkeypatch.setattr(TOOL, "collect_run", fake_collect_run)
    monkeypatch.setattr(TOOL, "score_run", lambda *args: ({}, 0))

    TOOL._replay_manifest(manifest_path, sessions_root)
    assert captured == [luna]


def test_cli_benchmark_task_id_is_parsed_and_resolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed = TOOL._parser().parse_args(
        [
            "build-snapshot",
            "--snapshot",
            os.fspath(tmp_path / "snapshot"),
            "--benchmark-task-id",
            "POS",
        ]
    )
    assert parsed.benchmark_task_id == "POS"
    assert parsed.case is None

    observed: dict[str, Any] = {}

    def fake_resolve(
        benchmark_task_id: str | None = None,
        *,
        case: str | None = None,
        legacy_case: str | None = None,
        manifest: Any = TOOL.TASK_MANIFEST,
    ) -> str:
        observed.update(
            {
                "benchmark_task_id": benchmark_task_id,
                "case": case,
            }
        )
        return "POS"

    monkeypatch.setattr(TOOL, "resolve_benchmark_task_id", fake_resolve)
    monkeypatch.setattr(TOOL, "build_snapshot", lambda *args: {"ok": True})
    rc = TOOL.main(
        [
            "build-snapshot",
            "--snapshot",
            os.fspath(tmp_path / "snapshot"),
            "--benchmark-task-id",
            "POS",
        ]
    )
    assert rc == 0
    assert observed == {"benchmark_task_id": "POS", "case": None}


def test_cli_case_and_benchmark_task_id_conflict_is_fail_closed(
    tmp_path: Path,
) -> None:
    rc = TOOL.main(
        [
            "build-snapshot",
            "--snapshot",
            os.fspath(tmp_path / "snapshot"),
            "--case",
            "POS",
            "--benchmark-task-id",
            "NEG",
        ]
    )
    assert rc == TOOL.RC_ROUTING


def test_stage2_historical_fixture_is_copied_from_real_artifact() -> None:
    # Independent: F29 real-artifact provenance for the replay fixture.
    assert Path(_STAGE2_HISTORICAL_PLAN_SOURCE).read_bytes() == (
        _STAGE2_HISTORICAL_PLAN.encode("utf-8")
    )


def test_stage2_freeze_is_create_only_and_pins_raw_plan_and_apparatus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # M1: create-only freeze must reject a second registration at the same path.
    fixture = _stage2_fixture(tmp_path, monkeypatch)
    contract = fixture["contract"]
    plan_descriptor = contract["plan_input"]
    assert Path(plan_descriptor["path"]).is_relative_to(fixture["run_root"])
    assert plan_descriptor["sha256"] == TOOL._sha256(
        fixture["plan"].read_bytes()
    )
    assert plan_descriptor["bytes"] == fixture["plan"].stat().st_size
    apparatus = contract["apparatus_pin"]
    assert Path(apparatus["snapshot"]["path"]).is_relative_to(
        fixture["run_root"]
    )
    assert apparatus["snapshot_sha256"] == apparatus["snapshot"]["sha256"]
    assert Path(apparatus["config"]["path"]).is_relative_to(fixture["run_root"])
    assert Path(apparatus["auth"]["path"]).is_relative_to(fixture["run_root"])
    assert Path(apparatus["binary"]["path"]).is_relative_to(fixture["run_root"])
    assert stat.S_IMODE(Path(apparatus["config"]["path"]).stat().st_mode) == 0o600
    assert stat.S_IMODE(Path(apparatus["auth"]["path"]).stat().st_mode) == 0o600
    assert Path(apparatus["binary"]["path"]).stat().st_mode & stat.S_IXUSR
    assert apparatus["config_sha256"] == TOOL._sha256(
        fixture["config"].read_bytes()
    )
    assert apparatus["auth_sha256"] == TOOL._sha256(fixture["auth"].read_bytes())
    assert apparatus["binary_sha256"] == TOOL._sha256(
        fixture["codex"].read_bytes()
    )
    assert apparatus["binary_version"] == "stage2-fake-codex 1.0"
    assert contract["task_acceptance_status"] == "unbound"
    assert contract["fix_gate_eligible"] is False
    assert contract["routing_evidence_eligible"] is False
    with pytest.raises(TOOL.ValidationError, match="already exists"):
        TOOL.freeze_stage2_plan_replayer(
            fixture["plan"],
            fixture["contract_path"],
            TOOL.MODEL,
            "max",
            0,
            snapshot=fixture["snapshot"],
            acceptance_kind="execution-receipt",
            acceptance_reason="second freeze",
            config_source=fixture["config"],
            auth_source=fixture["auth"],
            codex_binary=fixture["codex"],
        )


def test_stage2_freeze_rolls_back_staging_after_binary_probe_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # fix2b: a failed freeze must not leave replay apparatus or partial staging behind.
    run_root = tmp_path / "stage2-run-root"
    run_root.mkdir()
    plan = tmp_path / "historical-plan.md"
    plan.write_bytes(_STAGE2_HISTORICAL_PLAN.encode("utf-8"))
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    config = tmp_path / "config.toml"
    auth = tmp_path / "auth.json"
    config.write_text("model = 'gpt-5.6-sol'\n", encoding="utf-8")
    auth.write_text('{"token":"fixture"}\n', encoding="utf-8")
    codex = _make_fake_stage2_downstream(tmp_path / "fake-stage2-codex")

    def fail_probe(*args: Any, **kwargs: Any) -> str:
        raise TOOL.ValidationError("injected version probe failure", TOOL.RC_ROUTING)

    monkeypatch.setattr(TOOL, "_stage2_version_probe", fail_probe)
    contract_path = run_root / "stage2-contract.json"
    with pytest.raises(TOOL.ValidationError, match="injected version probe failure"):
        TOOL.freeze_stage2_plan_replayer(
            plan,
            contract_path,
            TOOL.MODEL,
            "max",
            0,
            snapshot=snapshot,
            config_source=config,
            auth_source=auth,
            codex_binary=codex,
        )

    assert list(run_root.iterdir()) == []
    assert not (run_root / "stage2-apparatus" / "config.toml").exists()
    assert not (run_root / "stage2-apparatus" / "auth.json").exists()
    assert not (run_root / "stage2-apparatus" / "codex").exists()


@pytest.mark.parametrize("missing", ("snapshot", "config_source", "auth_source", "codex_binary"))
def test_stage2_freeze_requires_every_apparatus_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    fixture = _stage2_fixture(tmp_path, monkeypatch)
    kwargs: dict[str, Any] = {
        "snapshot": fixture["snapshot"],
        "config_source": fixture["config"],
        "auth_source": fixture["auth"],
        "codex_binary": fixture["codex"],
    }
    kwargs[missing] = None
    with pytest.raises(TOOL.ValidationError, match="required"):
        TOOL.freeze_stage2_plan_replayer(
            fixture["plan"],
            tmp_path / "missing-contract.json",
            TOOL.MODEL,
            "max",
            0,
            **kwargs,
        )


@pytest.mark.parametrize("replacement", ("symlink", "rename"))
def test_stage2_frozen_copy_rejects_prelaunch_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replacement: str,
) -> None:
    # M2: a prelaunch symlink or rename replacement must not reach downstream.
    fixture = _stage2_fixture(tmp_path, monkeypatch)
    frozen = Path(fixture["contract"]["plan_input"]["path"])
    if replacement == "symlink":
        frozen.unlink()
        frozen.symlink_to(fixture["plan"])
    else:
        frozen.rename(frozen.with_name(frozen.name + ".moved"))
    with pytest.raises(TOOL.ValidationError):
        _run_stage2_fixture(fixture)
    assert not fixture["counter"].exists()


@pytest.mark.parametrize("field", ("snapshot", "config", "auth", "binary"))
def test_stage2_frozen_apparatus_replacement_is_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    # F1/F9: replacing any frozen apparatus after freeze cannot reach launch.
    fixture = _stage2_fixture(tmp_path, monkeypatch)
    target = Path(fixture["contract"]["apparatus_pin"][field]["path"])
    if field == "snapshot":
        (target / "replacement.txt").write_bytes(b"replacement")
    else:
        target.write_bytes(b"replacement")
    with pytest.raises(TOOL.ValidationError):
        _run_stage2_fixture(fixture)
    assert not fixture["counter"].exists()


def test_stage2_live_apparatus_replacement_cannot_change_frozen_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # F1/F9: changing the original live paths after freeze is irrelevant.
    fixture = _stage2_fixture(tmp_path, monkeypatch)
    fixture["config"].write_text("replacement config\n", encoding="utf-8")
    fixture["auth"].write_text('{"token":"replacement"}\n', encoding="utf-8")
    fixture["codex"].write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
    fixture["codex"].chmod(0o755)
    result, rc = _run_stage2_fixture(fixture)
    assert rc == 0
    assert result["receipt_status"] == "valid"
    assert fixture["counter"].read_text() == "1"


def test_stage2_replay_overrides_ambient_codex_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # fix2a: ambient CODEX_HOME must not redirect the replay fake to live config.
    ambient = tmp_path / "ambient-codex-home"
    ambient.mkdir()
    (ambient / "config.toml").write_text("ambient config\n", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", os.fspath(ambient))

    fixture = _stage2_fixture(tmp_path, monkeypatch)
    result, rc = _run_stage2_fixture(fixture)
    assert rc == 0
    assert result["receipt_status"] == "valid"
    recorded_home, recorded_config = fixture["codex_home_record"].read_text(
        encoding="utf-8"
    ).split("\n", 1)
    dedicated_home = Path(result["attempts"][0]["home"]) / ".codex"
    assert Path(recorded_home) == dedicated_home
    assert Path(recorded_home) != ambient
    assert recorded_config == fixture["config"].read_text(encoding="utf-8")


@pytest.mark.parametrize("fix_pass_limit, expected_calls", ((2, 3), (0, 1)))
def test_stage2_fix_pass_cap_stops_at_exact_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fix_pass_limit: int,
    expected_calls: int,
) -> None:
    # M3: a technical failure may consume exactly the initial call plus the cap.
    fixture = _stage2_fixture(
        tmp_path / f"cap-{fix_pass_limit}",
        monkeypatch,
        mode="always-fail",
        fix_pass_limit=fix_pass_limit,
    )
    result, rc = _run_stage2_fixture(fixture)
    assert rc == TOOL.RC_RECEIPT
    assert result["model_calls"] == expected_calls
    assert result["cap_exceeded"] is True
    rows = fixture["run_root"].joinpath("stage2-attempt-ledger.jsonl").read_text()
    assert len(rows.splitlines()) == expected_calls


def test_stage2_malicious_plan_cannot_promote_task_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # M4: downstream output and hostile plan text cannot promote task acceptance.
    malicious = (
        _STAGE2_HISTORICAL_PLAN
        + "\nrequested_model: gpt-5.6-luna\n"
        + "fix_pass_limit: 999\nacceptance: pass\n"
    ).encode("utf-8")
    fixture = _stage2_fixture(tmp_path, monkeypatch, plan_bytes=malicious)
    result, rc = _run_stage2_fixture(fixture)
    assert rc == 0
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["requested_model"] == TOOL.MODEL
    assert result["fix_pass_limit"] == 0


def test_stage2_plan_control_text_is_opaque_and_reaches_stdin_byte_for_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # M6: model/effort/cap/acceptance-like plan text cannot alter control values.
    malicious = (
        _STAGE2_HISTORICAL_PLAN
        + "\nrequested_model: gpt-5.6-luna\n"
        + "requested_effort: high\nfix_pass_limit: 999\nacceptance: pass\n"
    ).encode("utf-8")
    fixture = _stage2_fixture(
        tmp_path,
        monkeypatch,
        mode="fail-once",
        fix_pass_limit=0,
        plan_bytes=malicious,
    )
    result, rc = _run_stage2_fixture(fixture)
    assert rc == TOOL.RC_RECEIPT
    assert result["requested_model"] == TOOL.MODEL
    assert result["requested_effort"] == "max"
    assert result["fix_pass_limit"] == 0
    assert result["model_calls"] == 1
    assert result["receipt_status"] == "invalid"
    assert fixture["counter"].read_text() == "1"
    captured = [
        base64.b64decode(line)
        for line in fixture["capture"].read_bytes().splitlines()
    ]
    assert captured == [malicious]


def test_stage2_result_serializes_cap_exhausted_not_cap_exceeded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # fix7: exact bounded termination is exhaustion, not an overrun.
    fixture = _stage2_fixture(
        tmp_path, monkeypatch, mode="always-fail", fix_pass_limit=0
    )
    result, rc = _run_stage2_fixture(fixture)
    assert rc == TOOL.RC_RECEIPT
    assert result["cap_exhausted"] is True
    stored = json.loads(fixture["result_path"].read_text(encoding="utf-8"))
    assert stored["cap_exhausted"] is True
    assert "cap_exceeded" not in stored


def test_stage2_result_namespace_has_no_legacy_acceptance_boolean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Independent: the stage2 schema exposes receipt facts without a legacy acceptance field.
    fixture = _stage2_fixture(tmp_path, monkeypatch)
    result, rc = _run_stage2_fixture(fixture)
    assert rc == 0

    def keys(value: Any) -> list[str]:
        if isinstance(value, dict):
            return list(value) + [key for item in value.values() for key in keys(item)]
        if isinstance(value, list):
            return [key for item in value for key in keys(item)]
        return []

    assert "accepted" not in keys(result)
    assert "accepted" not in keys(json.loads(fixture["result_path"].read_text()))


def test_stage2_freeze_and_replay_use_a_distinct_schema_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # M7: a legacy SCHEMA_VERSION alias must not silently become the stage2 schema.
    fixture = _stage2_fixture(tmp_path, monkeypatch)
    result, rc = _run_stage2_fixture(fixture)
    assert rc == 0
    contract = json.loads(fixture["contract_path"].read_text(encoding="utf-8"))
    stored_result = json.loads(fixture["result_path"].read_text(encoding="utf-8"))
    assert TOOL.STAGE2_REPLAYER_SCHEMA_VERSION != TOOL.SCHEMA_VERSION
    assert contract["schema_version"] == TOOL.STAGE2_REPLAYER_SCHEMA_VERSION
    assert result["schema_version"] == TOOL.STAGE2_REPLAYER_SCHEMA_VERSION
    assert stored_result["schema_version"] == TOOL.STAGE2_REPLAYER_SCHEMA_VERSION


@pytest.mark.parametrize(
    "timeout_s",
    (float("inf"), float("nan"), 0.0, -1.0, TOOL.STAGE2_REPLAYER_MAX_WALL_CLOCK_TIMEOUT_S + 1),
)
def test_stage2_wall_timeout_rejects_nonfinite_and_out_of_bound_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    timeout_s: float,
) -> None:
    fixture = _stage2_fixture(tmp_path, monkeypatch)
    with pytest.raises(TOOL.ValidationError, match="wall timeout"):
        _run_stage2_fixture(fixture, timeout_s=timeout_s)
    assert not fixture["counter"].exists()


def test_stage2_version_probe_timeout_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "codex"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)

    class TimeoutProcess:
        pid = 12345
        returncode: int | None = None

        def communicate(self, *, timeout: float) -> tuple[bytes, bytes]:
            assert timeout == TOOL.STAGE2_REPLAYER_VERSION_PROBE_TIMEOUT_S
            raise subprocess.TimeoutExpired([os.fspath(binary), "--version"], timeout)

        def poll(self) -> int | None:
            return self.returncode

    process = TimeoutProcess()

    def timeout_popen(*args: Any, **kwargs: Any) -> TimeoutProcess:
        assert kwargs["start_new_session"] is True
        return process

    def stop_process_tree(stopped: TimeoutProcess) -> tuple[bytes, bytes]:
        assert stopped is process
        process.returncode = -15
        return b"", b""

    monkeypatch.setattr(TOOL.subprocess, "Popen", timeout_popen)
    monkeypatch.setattr(TOOL, "_stage2_stop_process_tree", stop_process_tree)
    with pytest.raises(TOOL.ValidationError, match="version probe timed out"):
        TOOL._stage2_version_probe(binary, cwd=tmp_path, label="fixture")


def test_stage2_version_probe_timeout_kills_process_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    child_pid_file = tmp_path / "version-child.pid"
    binary = _make_executable(
        tmp_path / "codex",
        r"""#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from pathlib import Path

if "--version" in sys.argv:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    Path("version-child.pid").write_text(
        f"{child.pid} {os.getpgid(child.pid)}\n", encoding="utf-8"
    )
    time.sleep(30)
""",
    )

    with pytest.raises(TOOL.ValidationError, match="version probe timed out"):
        TOOL._stage2_version_probe(binary, cwd=tmp_path, label="fixture")

    child_pid, process_group = (
        int(value) for value in child_pid_file.read_text(encoding="utf-8").split()
    )
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        try:
            os.kill(child_pid, 0)
            child_gone = False
        except ProcessLookupError:
            child_gone = True
        try:
            os.killpg(process_group, 0)
            group_gone = False
        except ProcessLookupError:
            group_gone = True
        if child_gone and group_gone:
            break
        time.sleep(0.01)
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)
    with pytest.raises(ProcessLookupError):
        os.killpg(process_group, 0)


def test_stage2_identity_copy_is_create_only_and_born0600(tmp_path: Path) -> None:
    source = tmp_path / "auth.json"
    source.write_text('{"token":"fixture"}\n', encoding="utf-8")
    source.chmod(0o644)
    target = tmp_path / "home" / ".codex" / "auth.json"
    assert TOOL._copy_identity_file(source, target, "fixture auth") == TOOL._sha256(
        source.read_bytes()
    )
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    with pytest.raises(TOOL.ValidationError, match="already exists"):
        TOOL._copy_identity_file(source, target, "fixture auth")


def test_stage2_timeout_consumes_one_pass_and_returns_bounded_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # M5: a hanging pass must be terminated within its wall-clock bound.
    fixture = _stage2_fixture(tmp_path, monkeypatch, mode="hang")
    started = time.monotonic()
    result, rc = _run_stage2_fixture(fixture, timeout_s=0.1)
    elapsed = time.monotonic() - started
    assert elapsed < 5
    assert rc == TOOL.RC_RECEIPT
    assert result["model_calls"] == 1
    assert result["attempts"][0]["timed_out"] is True
    assert result["attempts"][0]["receipt_status"] == "invalid"
    pid, process_group = (
        int(value) for value in fixture["pid_file"].read_text().split()
    )
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    with pytest.raises(ProcessLookupError):
        os.killpg(process_group, 0)
    assert not Path(result["attempts"][0]["home"]).exists()


def test_stage2_execution_receipt_invalid_empty_and_hash_mismatch_are_invalid() -> None:
    # Independent: receipt status must be derived from invalid, empty, and hash facts.
    expected_contract = "a" * 64
    expected_plan = "b" * 64
    base = {
        "contract_sha256": expected_contract,
        "plan_sha256": expected_plan,
        "exit_code": 0,
        "timed_out": False,
        "output": {"regular": True, "bytes": 3, "sha256": "c" * 64},
        "output_sha256": "c" * 64,
    }
    variants = []
    invalid = dict(base)
    invalid["exit_code"] = 1
    variants.append(invalid)
    empty = copy.deepcopy(base)
    empty["output"]["bytes"] = 0
    variants.append(empty)
    mismatch = copy.deepcopy(base)
    mismatch["output_sha256"] = "d" * 64
    variants.append(mismatch)
    for receipt in variants:
        observed = TOOL._stage2_acceptance(
            receipt,
            {"kind": "execution-receipt", "reason": "mechanical only"},
            expected_contract_sha256=expected_contract,
            expected_plan_sha256=expected_plan,
        )
        assert observed["receipt_status"] == "invalid"
        assert observed["task_acceptance_status"] == "unbound"
        assert observed["fix_gate_eligible"] is False
        assert observed["routing_evidence_eligible"] is False


def test_stage2_between_pass_tamper_is_detected_before_next_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # M2: a between-pass replacement must stop before the next downstream launch.
    fixture = _stage2_fixture(
        tmp_path, monkeypatch, mode="fail-once", fix_pass_limit=1
    )
    original_append = TOOL._append_jsonl
    append_count = 0

    def append_then_tamper(path: Path, row: dict[str, Any]) -> None:
        nonlocal append_count
        original_append(path, row)
        append_count += 1
        if append_count == 1:
            plan = Path(fixture["contract"]["plan_input"]["path"])
            plan.rename(plan.with_name(plan.name + ".moved"))

    monkeypatch.setattr(TOOL, "_append_jsonl", append_then_tamper)
    with pytest.raises(TOOL.ValidationError):
        _run_stage2_fixture(fixture)
    assert fixture["counter"].read_text() == "1"


def test_stage2_post_run_tamper_is_detected_after_downstream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # M2: a post-run replacement must invalidate the observed pass.
    fixture = _stage2_fixture(tmp_path, monkeypatch, mode="tamper-plan")
    with pytest.raises(TOOL.ValidationError):
        _run_stage2_fixture(fixture)
    assert fixture["counter"].read_text() == "1"


def test_stage2_cli_verbs_parse_and_dispatch_without_legacy_schema_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Independent: both new CLI verbs dispatch while preserving their dedicated schema.
    freeze_args = [
        "freeze-stage2-plan-replayer",
        "--plan-input",
        os.fspath(tmp_path / "plan"),
        "--requested-model",
        TOOL.MODEL,
        "--requested-effort",
        "max",
        "--fix-pass-limit",
        "0",
        "--acceptance-kind",
        "unbound",
        "--acceptance-reason",
        "dispatch",
        "--output",
        os.fspath(tmp_path / "contract.json"),
        "--snapshot",
        os.fspath(tmp_path / "snapshot"),
        "--config-source",
        os.fspath(tmp_path / "config.toml"),
        "--auth-source",
        os.fspath(tmp_path / "auth.json"),
        "--codex-bin",
        os.fspath(tmp_path / "codex"),
    ]
    parsed_freeze = TOOL._parser().parse_args(freeze_args)
    assert parsed_freeze.command == "freeze-stage2-plan-replayer"
    freeze_result = {
        "schema_version": TOOL.STAGE2_REPLAYER_SCHEMA_VERSION,
        "contract_kind": "stage2-plan-replayer",
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }
    freeze_calls: dict[str, Any] = {}

    def capture_freeze(*args: Any, **kwargs: Any) -> dict[str, Any]:
        freeze_calls["args"] = args
        freeze_calls["kwargs"] = kwargs
        return freeze_result

    monkeypatch.setattr(TOOL, "freeze_stage2_plan_replayer", capture_freeze)
    assert TOOL.main(freeze_args) == 0
    assert capsys.readouterr().out.encode() == TOOL._canonical_bytes(freeze_result)
    assert freeze_calls == {
        "args": (
            tmp_path / "plan",
            tmp_path / "contract.json",
            TOOL.MODEL,
            "max",
            0,
        ),
        "kwargs": {
            "snapshot": tmp_path / "snapshot",
            "acceptance_kind": "unbound",
            "acceptance_reason": "dispatch",
            "config_source": tmp_path / "config.toml",
            "auth_source": tmp_path / "auth.json",
            "codex_binary": tmp_path / "codex",
        },
    }

    replay_args = [
        "replay-stage2-plan",
        "--contract",
        os.fspath(tmp_path / "contract.json"),
        "--run-root",
        os.fspath(tmp_path),
        "--result",
        os.fspath(tmp_path / "result.json"),
        "--snapshot",
        os.fspath(tmp_path),
        "--config-source",
        os.fspath(tmp_path / "config.toml"),
        "--auth-source",
        os.fspath(tmp_path / "auth.json"),
        "--codex-bin",
        os.fspath(tmp_path / "codex"),
        "--dry-run",
        "--wall-clock-timeout-s",
        "2.5",
    ]
    parsed_replay = TOOL._parser().parse_args(replay_args)
    assert parsed_replay.command == "replay-stage2-plan"
    replay_result = {
        "schema_version": TOOL.STAGE2_REPLAYER_SCHEMA_VERSION,
        "result_kind": "stage2-plan-replayer-result",
        "receipt_status": "invalid",
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }
    replay_calls: dict[str, Any] = {}

    def capture_replay(*args: Any, **kwargs: Any) -> tuple[dict[str, Any], int]:
        replay_calls["args"] = args
        replay_calls["kwargs"] = kwargs
        return replay_result, 7

    monkeypatch.setattr(TOOL, "replay_stage2_plan", capture_replay)
    assert TOOL.main(replay_args) == 7
    assert capsys.readouterr().out.encode() == TOOL._canonical_bytes(replay_result)
    assert replay_calls == {
        "args": (),
        "kwargs": {
            "contract_path": tmp_path / "contract.json",
            "run_root": tmp_path,
            "result_path": tmp_path / "result.json",
            "snapshot": tmp_path,
            "config_source": tmp_path / "config.toml",
            "auth_source": tmp_path / "auth.json",
            "codex_binary": tmp_path / "codex",
            "dry_run": True,
            "wall_clock_timeout_s": 2.5,
        },
    }


def test_stage2_source_block_has_no_wave_d_reachability_names() -> None:
    # M8: forbidden Wave-D reachability names must be absent from new stage2 code.
    source = _TOOL_PATH.read_text(encoding="utf-8")
    block = source[
        source.index("class Stage2PlanReplayerContract") : source.index(
            "def _supervise_one", source.index("class Stage2PlanReplayerContract")
        )
    ]
    for forbidden in (
        "_validate_schedule",
        "_load_adjudication",
        "_aggregate_verified",
        "_replay_manifest",
        "make_packets",
        "supervise_pair",
        "_validate_supervisor_ledger",
    ):
        assert forbidden not in block


def test_existing_score_cli_schema_output_is_byte_exact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # M7: an existing CLI verb must retain its legacy byte-exact serializer.
    missing = tmp_path / "missing-output.md"
    expected, expected_rc = TOOL.score_run(missing)
    assert TOOL.main(["score-run", "--output", os.fspath(missing)]) == expected_rc
    assert capsys.readouterr().out.encode() == TOOL._canonical_bytes(expected)
    assert expected["schema_version"] == TOOL.SCHEMA_VERSION


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


def test_aggregate_verified_uses_oracle_kind_and_keeps_task_model_axes_separate(
    tmp_path: Path,
) -> None:
    task_manifest = _synthetic_task_manifest(
        (
            ("alpha", "POS", "positive", "alpha-finding"),
            ("beta", "NEG", "negative", "beta-finding"),
        )
    )
    slots, attempts, verdicts = _aggregate_rows()
    for slot, attempt in zip(slots, attempts):
        task_id = "alpha" if slot["case"] == "POS" else "beta"
        legacy_case = f"legacy-{task_id}"
        for row in (slot, attempt):
            row.update(
                {
                    "benchmark_task_id": task_id,
                    "legacy_case": legacy_case,
                    "case": legacy_case,
                    "stage": "stage-1",
                    "requested_model": TOOL.MODEL,
                    "cache_condition": None,
                    "price_version": None,
                }
            )
    beta_slot = next(row for row in slots if row["benchmark_task_id"] == "beta")
    verdicts[beta_slot["slot_id"]]["findings"] = [
        {
            "real": True,
            "equivalent_to": "beta-finding",
            "root_cause": None,
            "severity": "HIGH",
            "must_fix": True,
        }
    ]
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "dynamic-manifest.json", {}),
        slots,
        attempts,
        verdicts,
        [],
        task_manifest=task_manifest,
    )
    assert result["valid"] is True
    assert result["experiment_complete"] is True
    assert isinstance(result["primary_judgment_ledger"], list)
    assert {
        row["benchmark_task_id"] for row in result["primary_judgment_axis_ledger"]
    } == {"alpha"}
    assert {
        row["benchmark_task_id"] for row in result["resource_ledger"]
    } == {"alpha", "beta"}
    assert all(
        row["requested_model"] == TOOL.MODEL
        and row["stage"] == "stage-1"
        and row["cache_condition"] is None
        and row["price_version"] is None
        for row in result["resource_ledger"]
    )
    assert "by_arm_case" not in result["token_usage_observations"][
        TOOL.ZERO_COMPONENT_TOTAL_ONLY
    ]
    assert result["decision"]["by_axis"]


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
    observation = result["token_usage_observations"][
        TOOL.ZERO_COMPONENT_TOTAL_ONLY
    ]
    assert observation["total_count"] == 1
    assert observation["by_arm_case"] == {
        "max": {"POS": 0, "NEG": 1},
        "high": {"POS": 0, "NEG": 0},
    }
    assert [row for row in observation["by_axis"] if row["count"]] == [
        {
            "benchmark_task_id": "NEG",
            "stage": None,
            "requested_model": TOOL.MODEL,
            "cache_condition": None,
            "price_version": None,
            "arm": "max",
            "count": 1,
        }
    ]


def test_zero_component_total_only_mixed_models_omit_legacy_projection() -> None:
    slots, attempts, _ = _aggregate_rows()
    slots[0]["requested_model"] = "gpt-5.6-luna"
    attempts[0]["requested_model"] = "gpt-5.6-luna"
    reasons: list[str] = []
    result = TOOL._aggregate_token_usage_observations(
        attempts,
        reasons,
        slots=slots,
    )
    assert reasons == []
    assert "by_arm_case" not in result[TOOL.ZERO_COMPONENT_TOTAL_ONLY]


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


def test_make_packets_uses_dynamic_schedule_count_and_keeps_public_state_blind(
    tmp_path: Path,
) -> None:
    task_manifest = _synthetic_task_manifest()
    schedule_rows: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    for index, task_id in enumerate(("alpha", "beta", "gamma"), 1):
        block_id = f"b{index:02d}"
        for order, model in enumerate((TOOL.MODEL, "gpt-5.6-luna"), 1):
            slot_id = f"s{(index - 1) * 2 + order:02d}"
            schedule_rows.append(
                _v3_slot(
                    slot_id=slot_id,
                    task_id=task_id,
                    block_id=block_id,
                    block_order=order,
                    arm="max",
                    requested_model=model,
                )
            )
            output = tmp_path / f"output-{slot_id}.md"
            output.write_text(_long_output(), encoding="utf-8")
            attempts.append(
                {
                    "slot_id": slot_id,
                    "attempt": 1,
                    "run_id": f"r{(index - 1) * 2 + order:02d}",
                    "output": _descriptor(output, tmp_path),
                }
            )
    schedule_path = _canonical(
        tmp_path / "schedule.json",
        {"schema_version": TOOL.TASK_MANIFEST_SCHEMA_VERSION, "slots": schedule_rows},
    )
    manifest_path = _canonical(
        tmp_path / "manifest.json",
        {
            "schedule": _descriptor(schedule_path, tmp_path),
            "attempts": attempts,
        },
    )
    result = TOOL.make_packets(
        manifest_path,
        tmp_path / "packets",
        tmp_path / "custodian",
        task_manifest=task_manifest,
    )
    assert result["packet_count"] == 6
    state_path = Path(result["packet_state"])
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["mask_strength"] == "same-owner-advisory"
    assert all(set(row) == {"packet_id", "filename"} for row in state["packets"])
    public_state = state_path.read_text(encoding="utf-8")
    for forbidden in (
        "benchmark_task_id",
        "requested_model",
        "stage",
        "cache_condition",
        "price_version",
    ):
        assert forbidden not in public_state


def test_make_packets_rejects_empty_packet_only_manifest(tmp_path: Path) -> None:
    manifest_path = _canonical(
        tmp_path / "manifest.json",
        {"attempts": []},
    )
    with pytest.raises(
        TOOL.ValidationError,
        match="packets require at least one logical slot",
    ):
        TOOL.make_packets(
            manifest_path,
            tmp_path / "packets",
            tmp_path / "custodian",
        )


def test_make_packets_accepts_legacy_schedule_descriptor_without_schema_version(
    tmp_path: Path,
) -> None:
    schedule_rows: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    slot_number = 0
    for case, block_count in (("POS", 3), ("NEG", 2)):
        for _ in range(1, block_count + 1):
            block_id = f"b{len(schedule_rows) // 2 + 1:02d}"
            for block_order, arm in enumerate(("max", "high"), 1):
                slot_number += 1
                slot_id = f"s{slot_number:02d}"
                schedule_rows.append(
                    {
                        "slot_id": slot_id,
                        "case": case,
                        "arm": arm,
                        "block_id": block_id,
                        "block_order": block_order,
                        "prompt_sha256": "a" * 64,
                        "snapshot_manifest_sha256": "b" * 64,
                        "submodule_manifest_sha256": "c" * 64,
                    }
                )
                output = tmp_path / f"output-{slot_id}.md"
                output.write_text(_long_output(), encoding="utf-8")
                attempts.append(
                    {
                        "slot_id": slot_id,
                        "attempt": 1,
                        "run_id": f"r{slot_number:02d}",
                        "output": _descriptor(output, tmp_path),
                    }
                )
    schedule_path = _canonical(
        tmp_path / "legacy-schedule.json",
        {"slots": schedule_rows},
    )
    manifest_path = _canonical(
        tmp_path / "manifest.json",
        {
            "schedule": _descriptor(schedule_path, tmp_path),
            "attempts": attempts,
        },
    )
    result = TOOL.make_packets(
        manifest_path,
        tmp_path / "packets",
        tmp_path / "custodian",
    )
    assert result["packet_count"] == 10


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


from orchestrator.tests.growth_test_holds import enforce_held_functions  # noqa: E402
enforce_held_functions(globals(), __file__, plain_runner="pytest-delegating")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
