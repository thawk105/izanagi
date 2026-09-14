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

DW acceptance-hotspots mutation nodes:
MUT-1 -> test_filesystem_file_set_parent_resolve_errors_propagate_per_call
MUT-2 -> test_filesystem_file_set_symlink_root_git_is_included
MUT-3 -> test_git_fsck_futures_are_consumed_and_gated_exactly_once
MUT-4 -> test_git_fsck_completion_order_does_not_reorder_reasons_or_manifests
MUT-5 -> test_git_fsck_executor_construction_failure_rejects
MUT-6 -> test_verify_snapshot_reuses_one_filesystem_observation_per_snapshot
MUT-7 -> test_filesystem_file_set_accepts_readable_static_tree

T-1263 certification-scope mutation nodes:
MUT-1/MUT-2/MUT-3 ->
    test_material_report_certification_scope_is_exact_on_all_return_paths
    (also killed by added assertions in test_verify_replays_complete_fake_codex_experiment)
MUT-4 -> test_replay_forwards_only_successful_snapshot_evidence_to_adjudication
MUT-5 -> test_material_packet_source_requires_replayed_snapshot_evidence
MUT-6 -> test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run
MUT-7 -> test_verify_replays_complete_fake_codex_experiment
    (the pre-existing positive-path assertion alone kills this mutation)

T-1434 task-manifest mutation nodes:
M11 -> test_m11_task_manifest_loader_rejects_invalid_utf8_before_json_recovery
M12 -> test_m12_task_manifest_loader_rejects_duplicate_key_with_equal_values
M13 -> test_m13_task_manifest_schema_version_requires_exact_int
M15 -> test_m15_packet_consumer_requires_exact_task_manifest_digest_once
M16 -> test_m16_cli_external_manifest_is_loaded_before_alias_resolution
M17 -> test_m17_m21_p05_unavailable_cost_is_noncertifying_and_denominators_are_explicit
M18 -> test_m18_prelaunch_marker_never_hides_nonzero_accounting
M19 -> test_m19_verify_snapshot_rejects_task_manifest_option_by_fallback
M20 -> test_m20_render_prompt_binds_external_task_manifest
M21 -> test_m17_m21_p05_unavailable_cost_is_noncertifying_and_denominators_are_explicit

T-1434 adjudication-oracle mutation nodes:
M1 -> test_load_adjudication_rejects_cross_task_equivalent_from_manifest_union[parent]
M2 -> test_load_adjudication_rejects_cross_task_equivalent_from_manifest_union[second-reader]
M3/M9 -> test_replay_manifest_forwards_external_task_manifest_to_real_adjudication_loader
M7 -> test_replay_manifest_forwards_external_task_manifest_digest_at_loader_boundary
M4/M5 -> test_aggregate_verified_rejects_adjudication_oracle_kind_mismatch
M6 -> test_aggregate_verified_rejects_cross_task_equivalent_from_manifest_union
M8 -> test_load_adjudication_dimension_join_failure_is_reasoned_and_not_joined

T-1434 oracle-wiring-slice mutation nodes:
OR-M1 -> test_or_m1_loader_pins_checked_in_slice_semantic_sha
OR-M2 -> test_or_m2_main_rejects_forbidden_slice_command_before_side_effect
OR-M3 -> test_or_m3_production_validator_rejects_projection_change
OR-M6 diagnostic -> test_or_m6_adjudication_reason_is_task_specific_for_checked_slice
OR-M6 dual-layer correctness -> test_or_m6_checked_slice_full_cli_rejects_cross_task_finding
OR-M7 -> test_or_m7_checked_slice_keeps_acceptance_unbound_when_valid
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
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_TOOL_PATH = _ROOT / "tools" / "codex_reasoning_ab.py"
_WIRING_SLICE_PATH = (
    _ROOT
    / "output/t189-routing-preregistration/task-oracle-wiring-slice-v1.json"
)
_WIRING_SLICE_SHA256 = (
    "96a39ee259f985525df0a1206665dd331eb23b24e365b84e4558bfe115e75767"
)
_WIRING_SLICE_PROFILE = "t189-oracle-wiring-slice-v1"
_WIRING_SLICE_TOOL_PATH = _ROOT / "tools/t189_oracle_wiring_slice.py"
_SPEC = importlib.util.spec_from_file_location(
    "codex_reasoning_ab_under_test", _TOOL_PATH
)
assert _SPEC and _SPEC.loader
TOOL = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = TOOL
_SPEC.loader.exec_module(TOOL)

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
_TEST_PRICE_SNAPSHOT_PATH = (
    "output/t189-routing-preregistration/price-snapshot-v1.json"
)
_TEST_PRICE_SNAPSHOT_SHA256 = (
    "a0b2c71654d2ba1c58ca2184f903c856e269de5d46f3a64a6148ec035db8b3b1"
)
_TEST_PRICE_VERSION = (
    "openai-pricing-standard-short-context:sha256:"
    "fca40df4ec205375f6751fb59d9770f9aa8234c25968a758a8b6b70c34e97675"
)
_TEST_PRICE_EXCERPT_PATH = (
    "output/t189-routing-preregistration/price-standard-table-excerpt.html"
)
_TEST_PRICE_EXCERPT_SHA256 = (
    "32d016abae45142697ed608fb56f43e35483e43715965fb7b935bdf7dc6a78d4"
)
_TEST_PRICE_EXCERPT_BYTES = 19_117


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


_STAGE5_AUTHOR_PATCH = b"""diff --git a/file.txt b/file.txt
--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-old
+new
"""


def _stage5_sources(tmp_path: Path) -> dict[str, Any]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    run_root = tmp_path / "stage5-run-root"
    run_root.mkdir()
    plan = tmp_path / "plan.md"
    plan.write_bytes(b"frozen stage5 plan\n")
    author_output = tmp_path / "author.diff"
    author_output.write_bytes(_STAGE5_AUTHOR_PATCH)
    snapshot = tmp_path / "snapshot"
    target = snapshot / "repo"
    target.mkdir(parents=True)
    (target / "file.txt").write_bytes(b"old\n")
    git_value = shutil.which("git")
    assert git_value is not None
    return {
        "run_root": run_root,
        "plan": plan,
        "author_output": author_output,
        "snapshot": snapshot,
        "target": target,
        "git": Path(git_value),
        "contract_path": run_root / "stage5-contract.json",
    }


def _stage5_fixture(tmp_path: Path) -> dict[str, Any]:
    fixture = _stage5_sources(tmp_path)
    fixture["contract"] = TOOL.freeze_stage5_author_replayer(
        fixture["plan"],
        fixture["author_output"],
        fixture["contract_path"],
        snapshot=fixture["snapshot"],
        application_root="repo",
        git_binary=fixture["git"],
        review_model=TOOL.MODEL,
        review_effort="high",
        fix_model="gpt-5.6-luna",
        fix_effort="max",
        fix_pass_limit=2,
    )
    return fixture


def _stage5_downstream_receipt(
    fixture: dict[str, Any], *, role: str, pass_index: int, name: str
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    contract = fixture["contract"]
    contract_raw = fixture["contract_path"].read_bytes()
    stdin_path = fixture["run_root"] / f"{name}.stdin"
    output_path = fixture["run_root"] / f"{name}.output"
    stdin_path.write_bytes(b"stage5 downstream stdin\n")
    output_path.write_bytes(b"stage5 downstream output\n")
    if role == "review":
        previous_receipt_path = fixture["run_root"] / f"{name}.application.json"
        TOOL.validate_stage5_author_application(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=previous_receipt_path,
        )
    else:
        previous_role = "review" if pass_index == 1 else "fix"
        previous_pass_index = 0 if pass_index == 1 else pass_index - 1
        previous_receipt_path = fixture["run_root"] / f"{name}.previous.json"
        previous_pin = {
            "review": {
                "requested_model": TOOL.MODEL,
                "requested_effort": "high",
            },
            "fix": {
                "requested_model": "gpt-5.6-luna",
                "requested_effort": "max",
            },
        }[previous_role]
        previous_output = b"previous downstream output\n"
        previous_output_sha256 = TOOL._sha256(previous_output)
        previous_receipt = {
            "schema_version": TOOL.STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
            "receipt_kind": "stage5-downstream-receipt",
            "contract_sha256": TOOL._sha256(contract_raw),
            "role": previous_role,
            "pass_index": previous_pass_index,
            "author_output_hash": contract["author_output_hash"],
            "application_target_sha256": TOOL._sha256(
                TOOL._canonical_bytes(contract["application_target"])
            ),
            "requested_model": previous_pin["requested_model"],
            "requested_effort": previous_pin["requested_effort"],
            "argv": [
                "codex",
                "exec",
                "-m",
                previous_pin["requested_model"],
                "-c",
                f"model_reasoning_effort={previous_pin['requested_effort']}",
                "-s",
                "read-only",
                "--json",
            ],
            "stdin_sha256": TOOL._sha256(b"previous stdin\n"),
            "output": {
                "regular": True,
                "bytes": len(previous_output),
                "sha256": previous_output_sha256,
            },
            "output_sha256": previous_output_sha256,
            "previous_receipt_sha256": "3" * 64,
            "exit_code": 0,
            "timed_out": False,
            "receipt_status": "mechanically-valid",
            "task_acceptance_status": "unbound",
            "fix_gate_eligible": False,
            "routing_evidence_eligible": False,
        }
        previous_receipt_path.write_bytes(
            TOOL._canonical_bytes(previous_receipt)
        )
    pin = {
        "review": {
            "requested_model": TOOL.MODEL,
            "requested_effort": "high",
        },
        "fix": {
            "requested_model": "gpt-5.6-luna",
            "requested_effort": "max",
        },
    }[role]
    stdin_sha256 = TOOL._sha256(stdin_path.read_bytes())
    output_sha256 = TOOL._sha256(output_path.read_bytes())
    previous_receipt_sha256 = TOOL._sha256(previous_receipt_path.read_bytes())
    receipt = {
        "schema_version": TOOL.STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
        "receipt_kind": "stage5-downstream-receipt",
        "contract_sha256": TOOL._sha256(contract_raw),
        "role": role,
        "pass_index": pass_index,
        "author_output_hash": contract["author_output_hash"],
        "application_target_sha256": TOOL._sha256(
            TOOL._canonical_bytes(contract["application_target"])
        ),
        "requested_model": pin["requested_model"],
        "requested_effort": pin["requested_effort"],
        "argv": [
            "codex",
            "exec",
            "-m",
            pin["requested_model"],
            "-c",
            f"model_reasoning_effort={pin['requested_effort']}",
            "-s",
            "read-only",
            "--json",
        ],
        "stdin_sha256": stdin_sha256,
        "output": {
            "regular": True,
            "bytes": output_path.stat().st_size,
            "sha256": output_sha256,
        },
        "output_sha256": output_sha256,
        "previous_receipt_sha256": previous_receipt_sha256,
        "exit_code": 0,
        "timed_out": False,
        "receipt_status": "mechanically-valid",
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }
    path = fixture["run_root"] / name
    path.write_bytes(TOOL._canonical_bytes(receipt))
    return path, receipt, {
        "expected_role": role,
        "expected_pass_index": pass_index,
        "stdin_path": stdin_path,
        "output_path": output_path,
        "previous_receipt_path": previous_receipt_path,
    }


def _nested_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return list(value) + [key for item in value.values() for key in _nested_keys(item)]
    if isinstance(value, list):
        return [key for item in value for key in _nested_keys(item)]
    return []


def _schedule(
    path: Path,
    benchmark: dict[str, Any],
    *,
    task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
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
    return _canonical(
        path,
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                task_manifest
            ),
            "slots": slots,
        },
    ), slots


def _missing_pinned_rollouts(
    sessions_root: Path,
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (label, session_id)
        for label, session_id in TOOL.SESSION_IDS.items()
        if next(
            sessions_root.rglob(f"rollout-*-{session_id}.jsonl"), None
        )
        is None
    )


def _require_pinned_rollouts(sessions_root: Path) -> None:
    missing = _missing_pinned_rollouts(sessions_root)
    if missing:
        detail = ", ".join(
            f"{label} session {session_id}" for label, session_id in missing
        )
        pytest.skip(f"pinned historical rollout is unavailable: {detail}")


def _write_pinned_rollout_stub(sessions_root: Path, label: str) -> Path:
    session_id = TOOL.SESSION_IDS[label]
    rollout = sessions_root / f"rollout-test-{session_id}.jsonl"
    rollout.write_text(
        json.dumps(
            {"type": "session_meta", "payload": {"id": session_id}}
        )
        + "\n",
        encoding="utf-8",
    )
    return rollout


def _synthetic_benchmark_message(case: str) -> str:
    task = TOOL.TASK_MANIFEST["tasks"][case]
    artifact_paths = [
        f"{TOOL.OLD_ROOT}/{TOOL.ARTIFACT_DIR}/{name}"
        for name in task["snapshot"]["artifact_names"]
    ]
    replacement_count = task["provenance"]["prompt_source"]["replacements"]
    root_references = [
        f"benchmark root reference {index}: {TOOL.OLD_ROOT}"
        for index in range(1, replacement_count - len(artifact_paths) + 1)
    ]
    return "\n".join(
        [
            f"Synthetic {case} benchmark prompt.",
            *artifact_paths,
            *root_references,
        ]
    )


def _write_synthetic_benchmark_rollout(
    sessions_root: Path,
    session_id: str,
    message: str,
) -> tuple[Path, str]:
    rollout = (
        sessions_root
        / "2026/07/29"
        / f"rollout-2026-07-29T00-00-00-{session_id}.jsonl"
    )
    content = b"".join(
        TOOL._canonical_bytes(row)
        for row in (
            {"type": "session_meta", "payload": {"id": session_id}},
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": message},
            },
        )
    )
    _write_rollout(rollout, content)
    return rollout, TOOL._sha256(content)


@pytest.fixture(scope="module")
def benchmark_snapshots(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("t181-benchmark")
    sessions_root = root / "codex-home" / "sessions"
    task_manifest = copy.deepcopy(TOOL.TASK_MANIFEST)
    session_ids = {
        "POS": "00000000-0000-4000-8000-000000000181",
        "NEG": "00000000-0000-4000-8000-000000000182",
    }
    for case in ("POS", "NEG"):
        message = _synthetic_benchmark_message(case)
        source = message.encode("utf-8")
        _, rollout_sha256 = _write_synthetic_benchmark_rollout(
            sessions_root,
            session_ids[case],
            message,
        )
        provenance = task_manifest["tasks"][case]["provenance"]
        provenance["session_id"] = session_ids[case]
        provenance["rollout_sha256"] = rollout_sha256
        provenance["prompt_source"] = {
            "sha256": TOOL._sha256(source),
            "chars": len(message),
            "bytes": len(source),
            "replacements": message.count(TOOL.OLD_ROOT),
        }

    base_files = {
        path: TOOL._git(_ROOT, "show", f"{TOOL.BASE_COMMIT}:{path}")
        for path in TOOL.PATCH_PATHS
    }
    assert all(data.endswith(b"\n") for data in base_files.values())
    test_path = "orchestrator/tests/test_check_ai_provenance.py"
    tool_path = "tools/check_ai_provenance.py"
    prepared_pos = {
        test_path: base_files[test_path]
        + b"".join(
            f"# synthetic POS benchmark line {index:04d}\n".encode("ascii")
            for index in range(1, 694)
        ),
        tool_path: b"".join(base_files[tool_path].splitlines(keepends=True)[:-10])
        + b"".join(
            f"# synthetic POS tool line {index:04d}\n".encode("ascii")
            for index in range(1, 124)
        ),
    }
    for path, data in prepared_pos.items():
        task_manifest["tasks"]["POS"]["snapshot"]["hashes"][path] = (
            TOOL._sha256(data)
        )
    prepared = {"POS": prepared_pos, "NEG": {}}

    base = root / "base"
    destinations = {case: root / case.lower() for case in ("POS", "NEG")}
    TOOL._resolve_snapshot_destination(_ROOT, base)
    resolved_destinations = {
        case: TOOL._resolve_snapshot_destination(_ROOT, snapshot)
        for case, snapshot in destinations.items()
    }
    TOOL._build_snapshot_base(_ROOT, base)
    base_manifests = {"initial": TOOL._metadata_manifest(base)}
    result: dict[str, Any] = {
        "root": root,
        "sessions_root": sessions_root,
        "task_manifest": task_manifest,
        "_base": base,
        "_base_manifests": base_manifests,
    }
    for case in ("POS", "NEG"):
        snapshot = destinations[case]
        oracle = TOOL._derive_snapshot_from_base(
            _ROOT,
            base,
            snapshot,
            sessions_root,
            case,
            prepared_golden=prepared[case],
            prepared_destination=resolved_destinations[case],
            task_manifest=task_manifest,
        )
        base_manifests[f"after_{case.lower()}"] = TOOL._metadata_manifest(base)
        oracle_path = _canonical(root / f"{case.lower()}-oracle.json", oracle)
        prompt, prompt_receipt = TOOL.render_prompt(
            sessions_root,
            case,
            snapshot,
            task_manifest=task_manifest,
            snapshot_oracle=oracle,
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


def test_historical_rollout_guard_all_pins_present_does_not_skip(
    tmp_path: Path,
) -> None:
    for label in TOOL.SESSION_IDS:
        _write_pinned_rollout_stub(tmp_path, label)

    _require_pinned_rollouts(tmp_path)


def test_historical_rollout_guard_reports_missing_session(
    tmp_path: Path,
) -> None:
    missing_label = "author"
    for label in TOOL.SESSION_IDS:
        if label != missing_label:
            _write_pinned_rollout_stub(tmp_path, label)

    missing_session_id = TOOL.SESSION_IDS[missing_label]
    with pytest.raises(pytest.skip.Exception, match=missing_session_id):
        _require_pinned_rollouts(tmp_path)


def test_historical_rollout_guard_does_not_hide_sha_mismatch(
    tmp_path: Path,
) -> None:
    rollouts = {
        label: _write_pinned_rollout_stub(tmp_path, label)
        for label in TOOL.SESSION_IDS
    }

    _require_pinned_rollouts(tmp_path)
    with pytest.raises(TOOL.ValidationError, match="POS rollout sha mismatch"):
        TOOL._verify_rollout_sha(rollouts["POS"], "POS")


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
        "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
    task_manifest = benchmark["task_manifest"]
    schedule_path, slots = _schedule(
        root / "schedule-source.json",
        benchmark,
        task_manifest=task_manifest,
    )
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
        task_manifest=task_manifest,
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
        lambda actual_snapshot, case, **kwargs: {
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


def test_collect_run_rejects_launch_task_manifest_digest_exchange(
    tmp_path: Path,
) -> None:
    def mutate_launch(launch: dict[str, Any]) -> None:
        launch["task_manifest_sha256"] = "0" * 64

    run = _manual_run(
        tmp_path,
        mutate_launch_after_identity=mutate_launch,
    )
    assert run["rc"] == TOOL.RC_RECEIPT
    assert run["receipt"]["failure_reasons"] == [
        "launch receipt task_manifest_sha256 mismatch"
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
    *,
    memoize_construction_snapshots: bool = False,
) -> tuple[Path, Path]:
    task_manifest = benchmark["task_manifest"]
    schedule_source, slots = _schedule(
        root / "schedule-source.json",
        benchmark,
        task_manifest=task_manifest,
    )
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
    with monkeypatch.context() as construction_patch:
        if memoize_construction_snapshots:
            original_verify_snapshot = TOOL.verify_snapshot
            construction_snapshot_cache: dict[
                tuple[str, str], dict[str, Any]
            ] = {
                (
                    benchmark[case]["snapshot"].resolve().as_posix(),
                    case,
                ): copy.deepcopy(benchmark[case]["oracle_value"])
                for case in ("POS", "NEG")
            }

            def memoized_construction_verify_snapshot(
                snapshot: Path,
                case: str,
                *,
                spec: dict[str, Any] | None = None,
                task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
            ) -> dict[str, Any]:
                if spec is not None:
                    return original_verify_snapshot(
                        snapshot,
                        case,
                        spec=spec,
                        task_manifest=task_manifest,
                    )
                identity = (snapshot.resolve().as_posix(), case)
                if identity not in construction_snapshot_cache:
                    construction_snapshot_cache[identity] = (
                        original_verify_snapshot(
                            snapshot,
                            case,
                            task_manifest=task_manifest,
                        )
                    )
                return copy.deepcopy(construction_snapshot_cache[identity])

            construction_patch.setattr(
                TOOL,
                "verify_snapshot",
                memoized_construction_verify_snapshot,
            )
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
                task_manifest=task_manifest,
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
            task_manifest=task_manifest,
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
    premanifest = _canonical(
        root / "premanifest.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(task_manifest),
            "attempts": attempts,
        },
    )
    custodian_root = root / "mapping-custodian"
    packet_result = TOOL.make_packets(
        premanifest,
        root / "packets",
        custodian_root,
        task_manifest=task_manifest,
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
        packet_state,
        verdict_log,
        "parent",
        parent_input,
        task_manifest=task_manifest,
    )
    TOOL.append_verdicts(
        packet_state,
        verdict_log,
        "second-reader",
        second_input,
        task_manifest=task_manifest,
    )
    freeze = root / "verdict-freeze.json"
    TOOL.freeze_verdicts(
        packet_state,
        verdict_log,
        freeze,
        task_manifest=task_manifest,
    )
    revealed = root / "revealed-map.json"
    TOOL.reveal_mapping(
        packet_state,
        custodian_root,
        verdict_log,
        freeze,
        revealed,
        task_manifest=task_manifest,
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
        slot_id = next(
            row["slot_id"] for row in completions if row["run_id"] == run_id
        )
        slot = next(row for row in slots if row["slot_id"] == slot_id)
        combined = {
            "oracle_kind": TOOL._slot_dimensions(
                slot, task_manifest=task_manifest
            )["oracle_kind"],
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
                "slot_id": slot_id,
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
        "task_manifest_sha256": TOOL._task_manifest_sha256(task_manifest),
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


class _ScheduleReadObservation:
    """Delegate real reads and restore an A→B→A exchange, including teardown."""

    def __init__(self, path: Path, replacement: bytes | None = None):
        self.path = path.resolve()
        self.replacement = replacement
        self.reads = self.exchanges = self.restores = 0
        self.original_bytes: bytes | None = None
        self.original_stat: os.stat_result | None = None

    def __enter__(self):
        self.original_read = Path.read_bytes

        def observed(path: Path) -> bytes:
            data = self.original_read(path)
            if path.resolve() == self.path:
                self.reads += 1
                if self.reads == 1:
                    self.original_bytes = data
                    self.original_stat = path.stat()
                    if self.replacement is not None:
                        path.write_bytes(self.replacement)
                        self.exchanges += 1
                elif self.reads == 2 and self.replacement is not None:
                    self._restore()
            return data

        Path.read_bytes = observed
        return self

    def _restore(self):
        if self.restores == 0:
            assert self.original_bytes is not None
            assert self.original_stat is not None
            self.path.write_bytes(self.original_bytes)
            os.utime(self.path, ns=(
                self.original_stat.st_atime_ns, self.original_stat.st_mtime_ns,
            ))
            self.restores += 1

    def __exit__(self, *exc):
        try:
            if self.replacement is not None and self.exchanges:
                self._restore()
        finally:
            Path.read_bytes = self.original_read
        assert Path.read_bytes is self.original_read
        if self.original_bytes is not None:
            assert self.original_read(self.path) == self.original_bytes
            assert self.path.stat().st_mtime_ns == self.original_stat.st_mtime_ns


def _schedule_bytes_entry_fixture(root, benchmark, monkeypatch, entry, invalid):
    task_manifest = benchmark["task_manifest"]
    if entry == "replay":
        manifest_path, run_root = _full_manifest(
            root, benchmark, monkeypatch, memoize_construction_snapshots=True,
        )
        path = run_root / "schedule.json"
        manifest = json.loads(manifest_path.read_bytes())
    else:
        path, slots = _schedule(
            root / "schedule-source.json", benchmark, task_manifest=task_manifest,
        )
        run_root = root / "run-root"
    valid_bytes = path.read_bytes()
    if invalid:
        schedule = json.loads(valid_bytes)
        schedule["slots"][1]["slot_id"] = schedule["slots"][0]["slot_id"]
        metadata = path.stat()
        _canonical(path, schedule)
        os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
    expected_sha = TOOL._sha256(path.read_bytes())
    if entry == "supervisor":
        config = root / "config-source.toml"
        auth = root / "auth-source.json"
        config.write_text("model='gpt-5.6-sol'\n", encoding="utf-8")
        auth.write_text('{"token":"synthetic"}\n', encoding="utf-8")
        codex = _make_fake_codex(root / "fake-codex")
        bwrap = _make_executable(
            root / "fake-bwrap",
            "#!/bin/sh\n[ \"$1\" = \"--version\" ] && printf 'bwrap 0.6.1\\n'\n",
        )
        def invoke():
            return TOOL.supervise_pair(
                schedule_path=path, run_root=run_root, block_id="b01", attempt=1,
                snapshot=benchmark["POS"]["snapshot"], prompt=benchmark["POS"]["prompt"],
                config_source=config, auth_source=auth, codex_binary=codex,
                bwrap_binary=bwrap, dry_run=True, task_manifest=task_manifest,
            )
        observed_path = run_root / "schedule.json"
    elif entry == "replay":
        manifest["schedule"] = _descriptor(path, root)
        manifest["schedule_sha256"] = expected_sha
        if invalid:
            # Bind the synthetic receipts to A too: otherwise an unrelated
            # launch/SHA mismatch would conceal acceptance of B by old replay.
            ledger_path = run_root / "attempt-ledger.jsonl"
            ledger = [json.loads(line) for line in ledger_path.read_bytes().splitlines()]
            for row in manifest["attempts"]:
                launch_path = root / row["launch_receipt"]["path"]
                launch = json.loads(launch_path.read_bytes())
                launch["schedule_sha256"] = expected_sha
                launch["treatment_identity_sha256"] = TOOL._launch_identity_value(launch)
                metadata = launch_path.stat()
                _canonical(launch_path, launch)
                os.utime(launch_path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
                row["launch_receipt"] = _descriptor(launch_path, root)
                for completed in ledger:
                    if completed.get("run_id") == row["run_id"] and completed.get("phase") == "completed":
                        completed["launch_receipt_sha256"] = row["launch_receipt"]["sha256"]
                oracle = json.loads((root / row["snapshot_oracle"]["path"]).read_bytes())
                receipt, rc = TOOL.collect_run(
                    run_id=row["run_id"], case=launch["case"],
                    requested_effort=launch["arm"],
                    events=root / row["events"]["path"],
                    done=root / row["done"]["path"],
                    output=root / row["output"]["path"],
                    prompt=root / row["prompt"]["path"],
                    sessions_root=run_root, snapshot=Path(oracle["snapshot"]),
                    launch_receipt=launch_path, expected_requested_model=TOOL.MODEL,
                    task_manifest=task_manifest,
                )
                assert rc == 0, receipt.get("failure_reasons")
                receipt_path = root / row["receipt"]["path"]
                _canonical(receipt_path, receipt)
                row["receipt"] = _descriptor(receipt_path, root)
            ledger_path.write_bytes(b"".join(TOOL._canonical_bytes(row) for row in ledger))
            manifest["attempt_ledger"] = _descriptor(ledger_path, root)
        _canonical(manifest_path, manifest)
        def invoke():
            return TOOL.verify_manifest(manifest_path, run_root, task_manifest=task_manifest)
        observed_path = path
    else:
        output = root / "answer.md"
        output.write_text(_long_output(), encoding="utf-8")
        manifest_path = _canonical(root / "packet-source.json", {
            "task_manifest_sha256": TOOL._task_manifest_sha256(task_manifest),
            "schedule": _descriptor(path, root),
            "attempts": [
                {"slot_id": slot["slot_id"], "attempt": 1,
                 "run_id": slot["slot_id"], "output": _descriptor(output, root)}
                for slot in slots
            ],
        })
        def invoke():
            return TOOL.make_packets(
                manifest_path, root / "new-packets", root / "new-custodian",
                task_manifest=task_manifest,
            )
        observed_path = path
    return invoke, observed_path, valid_bytes, expected_sha


@pytest.mark.parametrize("entry", ("supervisor", "replay", "packets"))
def test_schedule_authenticated_bytes_reject_swap_restore(
    tmp_path: Path, benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch, entry: str,
) -> None:
    """固定 input に対する受理集合は不変。呼び出し中に変化する input に対しては挙動が変わり、
    それが本修正の目的である — 認証した bytes を、その後の file の状態から切り離す。
    確認した3入口の読みと解析の間に正規の resolver / injection point / テスト用 hook は無い。
    """
    invoke, path, valid_bytes, _ = _schedule_bytes_entry_fixture(
        tmp_path, benchmark_snapshots, monkeypatch, entry, True,
    )
    before = {p for p in tmp_path.rglob("*") if p.is_file()}
    error = None
    with _ScheduleReadObservation(path, valid_bytes) as observation:
        try:
            result = invoke()
        except TOOL.ValidationError as exc:
            error = exc
    assert observation.exchanges == 1
    assert observation.restores == 1
    assert observation.reads == 1
    if entry == "replay":
        assert error is None
        report, rc = result
        assert rc == TOOL.RC_AGGREGATE
        assert report["valid"] is False
        assert "duplicate slot_id: s01" in report["failure_reasons"]
        assert {p for p in tmp_path.rglob("*") if p.is_file()} == before
    else:
        assert error is not None
        assert "duplicate slot_id: s01" in error.reasons
        assert error.rc == (TOOL.RC_ROUTING if entry == "supervisor" else TOOL.RC_AGGREGATE)
        assert not (tmp_path / "new-packets").exists()
        assert not (tmp_path / "new-custodian").exists()
        assert not list((tmp_path / "run-root").rglob("launch.json"))
        assert not (tmp_path / "run-root" / "attempt-ledger.jsonl").exists()


@pytest.mark.parametrize("entry", ("supervisor", "replay", "packets"))
def test_schedule_authenticated_bytes_accept_static(
    tmp_path: Path, benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch, entry: str,
) -> None:
    invoke, path, valid_bytes, expected_sha = _schedule_bytes_entry_fixture(
        tmp_path, benchmark_snapshots, monkeypatch, entry, False,
    )
    with _ScheduleReadObservation(path) as observation:
        result = invoke()
    assert observation.reads == 1
    assert observation.exchanges == observation.restores == 0
    assert path.read_bytes() == valid_bytes
    assert TOOL._sha256(valid_bytes) == expected_sha
    if entry == "supervisor":
        assert len(result["runs"]) == 2
        for row in result["runs"]:
            launch = json.loads(Path(row["launch_receipt"]).read_bytes())
            assert launch["schedule_sha256"] == expected_sha
    elif entry == "replay":
        report, rc = result
        assert rc == 0
        assert report["valid"] is True
        assert report["failure_reasons"] == []
        assert len(report["resource_ledger"]) == 10
        manifest = json.loads((tmp_path / "manifest.json").read_bytes())
        assert manifest["schedule_sha256"] == expected_sha
    else:
        assert result["packet_count"] == 10
        manifest = json.loads((tmp_path / "packet-source.json").read_bytes())
        assert manifest["schedule"]["sha256"] == expected_sha


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
    task_manifest = benchmark_snapshots["task_manifest"]
    pos = TOOL.verify_snapshot(
        benchmark_snapshots["POS"]["snapshot"],
        "POS",
        task_manifest=task_manifest,
    )
    neg = TOOL.verify_snapshot(
        benchmark_snapshots["NEG"]["snapshot"],
        "NEG",
        task_manifest=task_manifest,
    )
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
    task_manifest = benchmark_snapshots["task_manifest"]
    for case in ("POS", "NEG"):
        snapshot = benchmark_snapshots[case]["snapshot"]
        oracle = TOOL.verify_snapshot(
            snapshot, case, task_manifest=task_manifest
        )
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


def _stub_git_closure_preparation(
    monkeypatch: pytest.MonkeyPatch,
    snapshot: Path,
    git_dir: Path,
) -> None:
    def fake_git(_repository: Path, *args: str, **_kwargs: Any) -> bytes:
        if args == ("for-each-ref", "--format=%(refname)"):
            return f"refs/heads/{TOOL.BRANCH}\n".encode()
        if args == ("remote",):
            return b""
        raise AssertionError(f"unexpected git call: {args}")

    monkeypatch.setattr(TOOL, "_git", fake_git)
    monkeypatch.setattr(TOOL, "_git_dir", lambda _repository: git_dir)
    monkeypatch.setattr(
        TOOL,
        "_commit_graph_manifest",
        lambda *_args: (
            [],
            {
                "present": False,
                "valid": None,
                "paths": [],
                "verify_returncode": None,
                "verify_stderr_first_line": None,
            },
        ),
    )


@pytest.mark.parametrize(
    "error_type", (PermissionError, OSError), ids=("permission", "io-error")
)
def test_git_closure_directory_enumeration_failure_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[OSError],
) -> None:
    snapshot = tmp_path / "snapshot"
    git_dir = snapshot / ".git"
    logs = git_dir / "logs"
    logs.mkdir(parents=True)
    (logs / "hidden").write_text("hidden\n", encoding="utf-8")
    _stub_git_closure_preparation(monkeypatch, snapshot, git_dir)
    original_scandir = os.scandir

    def failing_scandir(path: Any) -> Any:
        if Path(path) == logs:
            raise error_type("closure scan failed")
        return original_scandir(path)

    monkeypatch.setattr(TOOL.os, "scandir", failing_scandir)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._prepare_one_git_closure(
            snapshot, snapshot, [f"refs/heads/{TOOL.BRANCH}"]
        )

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert len(caught.value.reasons) == 1
    reason = caught.value.reasons[0].replace(os.fspath(logs), "<logs>")
    assert reason == (
        "git closure directory enumeration failed at <logs>: "
        f"{error_type.__name__}: closure scan failed"
    )


def test_git_closure_path_inspection_failure_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    git_dir = snapshot / ".git"
    logs = git_dir / "logs"
    logs.mkdir(parents=True)
    _stub_git_closure_preparation(monkeypatch, snapshot, git_dir)
    original_stat = Path.stat

    def failing_stat(
        path: Path, *, follow_symlinks: bool = True
    ) -> os.stat_result:
        if path == logs:
            raise OSError("closure stat failed")
        return original_stat(path, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, "stat", failing_stat)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._prepare_one_git_closure(
            snapshot, snapshot, [f"refs/heads/{TOOL.BRANCH}"]
        )

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert len(caught.value.reasons) == 1
    reason = caught.value.reasons[0].replace(os.fspath(logs), "<logs>")
    assert reason == (
        "git closure path inspection failed at <logs>: "
        "OSError: closure stat failed"
    )


def test_git_pseudo_ref_directory_enumeration_failure_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    git_dir = snapshot / ".git"
    git_dir.mkdir(parents=True)
    _stub_git_closure_preparation(monkeypatch, snapshot, git_dir)
    original_scandir = os.scandir

    def failing_scandir(path: Any) -> Any:
        if Path(path) == git_dir:
            raise PermissionError("pseudo-ref scan failed")
        return original_scandir(path)

    monkeypatch.setattr(TOOL.os, "scandir", failing_scandir)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._prepare_one_git_closure(
            snapshot, snapshot, [f"refs/heads/{TOOL.BRANCH}"]
        )

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert len(caught.value.reasons) == 1
    reason = caught.value.reasons[0].replace(os.fspath(git_dir), "<git-dir>")
    assert reason == (
        "git pseudo-ref directory enumeration failed at <git-dir>: "
        "PermissionError: pseudo-ref scan failed"
    )


def test_git_pseudo_ref_scan_preserves_regular_and_broken_symlink_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    git_dir = snapshot / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "MERGE_HEAD").write_text("head\n", encoding="ascii")
    (git_dir / "BISECT_HEAD").symlink_to("missing-target")
    _stub_git_closure_preparation(monkeypatch, snapshot, git_dir)

    state = TOOL._prepare_one_git_closure(
        snapshot, snapshot, [f"refs/heads/{TOOL.BRANCH}"]
    )

    assert state.reasons == [".: pseudo refs are present: ['MERGE_HEAD']"]
    assert [row["path"] for row in state.metadata] == [
        "BISECT_HEAD",
        "MERGE_HEAD",
    ]


def test_metadata_manifest_directory_enumeration_failure_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "metadata"
    denied = root / "denied"
    denied.mkdir(parents=True)
    (denied / "hidden").write_text("hidden\n", encoding="utf-8")
    original_scandir = os.scandir

    def failing_scandir(path: Any) -> Any:
        if Path(path) == denied:
            raise OSError("metadata scan failed")
        return original_scandir(path)

    monkeypatch.setattr(TOOL.os, "scandir", failing_scandir)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._metadata_manifest(root)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert len(caught.value.reasons) == 1
    reason = caught.value.reasons[0].replace(os.fspath(denied), "<denied>")
    assert reason == (
        "metadata directory enumeration failed at <denied>: "
        "OSError: metadata scan failed"
    )


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
    task_manifest = benchmark_snapshots["task_manifest"]
    snapshot = tmp_path / "stale-commit-graph"
    shutil.copytree(benchmark_snapshots["POS"]["snapshot"], snapshot)
    _install_stale_commit_graph(snapshot)

    reasons, manifests, _ = TOOL._git_closure_reasons(
        snapshot,
        TOOL._snapshot_spec(
            "POS", task_manifest=task_manifest
        )["untracked"],
    )
    assert any("git commit-graph verify exited" in reason for reason in reasons)
    commit_graph = manifests[0]["commit_graph"]
    assert commit_graph["present"] is True
    assert commit_graph["valid"] is False
    assert commit_graph["verify_returncode"] != 0
    assert commit_graph["paths"]
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.verify_snapshot(snapshot, "POS", task_manifest=task_manifest)
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


def _synthetic_git_closure_state(
    snapshot: Path,
    repository: Path,
    expected_refs: list[str],
) -> Any:
    label = (
        "."
        if repository == snapshot
        else repository.relative_to(snapshot).as_posix()
    )
    return TOOL._GitClosureState(
        repository=repository,
        label=label,
        reasons=[],
        refs=list(expected_refs),
        git_dir=repository / ".git",
        commit_graph={
            "present": False,
            "valid": None,
            "paths": [],
            "verify_returncode": None,
            "verify_stderr_first_line": None,
        },
        metadata=[{"path": f"metadata-{label}"}],
    )


def test_git_fsck_futures_are_consumed_and_gated_exactly_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    nested = snapshot / "deps/nested"
    futures: list[Any] = []
    executor_workers: list[int] = []
    executor_exited: list[bool] = []

    class TrackingFuture:
        def __init__(self, completed: subprocess.CompletedProcess[bytes]):
            self.completed = completed
            self.result_calls = 0

        def result(self) -> subprocess.CompletedProcess[bytes]:
            self.result_calls += 1
            return self.completed

    class TrackingExecutor:
        def __init__(self, *, max_workers: int):
            executor_workers.append(max_workers)

        def __enter__(self) -> Any:
            return self

        def submit(self, _callable: Any, _argv: Any, **kwargs: Any) -> Any:
            repository = Path(kwargs["cwd"])
            label = "." if repository == snapshot else "deps/nested"
            completed = subprocess.CompletedProcess(
                args=["git", "fsck"],
                returncode=7 if label == "." else 9,
                stdout=(f"unreachable blob {label}\n").encode(),
                stderr=(f"{label} stderr\n").encode(),
            )
            future = TrackingFuture(completed)
            futures.append(future)
            return future

        def __exit__(self, *args: Any) -> None:
            executor_exited.append(True)

    monkeypatch.setattr(TOOL, "ThreadPoolExecutor", TrackingExecutor)
    monkeypatch.setattr(
        TOOL,
        "_prepare_one_git_closure",
        lambda root, repository, refs: _synthetic_git_closure_state(
            root, repository, refs
        ),
    )
    monkeypatch.setattr(TOOL, "_git", lambda *_args, **_kwargs: b"head\n")

    reasons, manifests = TOOL._parallel_git_closure_reasons(
        snapshot,
        (
            (snapshot, [f"refs/heads/{TOOL.BRANCH}"]),
            (nested, []),
        ),
    )

    assert executor_workers == [2]
    assert executor_exited == [True]
    assert [future.result_calls for future in futures] == [1, 1]
    assert reasons == [
        ".: git fsck exited 7: . stderr",
        ".: git object store contains unreachable objects (1)",
        "deps/nested: git fsck exited 9: deps/nested stderr",
        "deps/nested: git object store contains unreachable objects (1)",
    ]
    assert [row["repository"] for row in manifests] == [".", "deps/nested"]


def test_git_fsck_missing_collected_result_is_structured_rejection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    nested = snapshot / "nested"

    class CompletedFuture:
        def result(self) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(["git", "fsck"], 0, b"", b"")

    class ImmediateExecutor:
        def __init__(self, *, max_workers: int):
            assert max_workers == 2

        def __enter__(self) -> Any:
            return self

        def submit(self, *_args: Any, **_kwargs: Any) -> CompletedFuture:
            return CompletedFuture()

        def __exit__(self, *_args: Any) -> None:
            return None

    monkeypatch.setattr(TOOL, "ThreadPoolExecutor", ImmediateExecutor)
    monkeypatch.setattr(
        TOOL,
        "_prepare_one_git_closure",
        lambda root, repository, refs: _synthetic_git_closure_state(
            root, repository, refs
        ),
    )
    monkeypatch.setattr(TOOL, "_git_fsck_reasons", lambda *_args: None)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._parallel_git_closure_reasons(
            snapshot, ((snapshot, []), (nested, []))
        )

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    normalized = tuple(
        reason.replace(os.fspath(snapshot), "<snapshot>")
        for reason in caught.value.reasons
    )
    assert normalized == (
        ".: git fsck result was not collected for <snapshot>",
    )


def test_git_fsck_completion_order_does_not_reorder_reasons_or_manifests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    middle = snapshot / "deps/middle"
    nested = snapshot / "deps/nested"
    repositories = (snapshot, nested)
    started = {repository: threading.Event() for repository in repositories}
    release = {repository: threading.Event() for repository in repositories}
    completed = {repository: threading.Event() for repository in repositories}
    completion_order: list[Path] = []
    controller_failures: list[BaseException] = []
    prepared: list[Path] = []

    def fake_prepare(
        root: Path, repository: Path, refs: list[str]
    ) -> Any:
        prepared.append(repository)
        return _synthetic_git_closure_state(root, repository, refs)

    def fake_run(argv: Any, *, cwd: Path, check: bool, **_kwargs: Any) -> Any:
        command = tuple(argv)
        if command != ("git", "fsck", "--unreachable", "--no-reflogs"):
            return subprocess.CompletedProcess(command, 1, b"", b"")
        repository = Path(cwd)
        started[repository].set()
        if not release[repository].wait(timeout=60):
            raise RuntimeError(f"release timeout for {repository}")
        completion_order.append(repository)
        completed[repository].set()
        if repository == snapshot:
            return subprocess.CompletedProcess(
                command, 11, b"unreachable blob root\n", b"root stderr\n"
            )
        return subprocess.CompletedProcess(
            command,
            12,
            b"unreachable blob nested\nunreachable tree nested\n",
            b"nested stderr\n",
        )

    def fake_git(repository: Path, *args: str, **_kwargs: Any) -> bytes:
        if args == ("rev-parse", "HEAD"):
            label = (
                "."
                if repository == snapshot
                else repository.relative_to(snapshot).as_posix()
            )
            return f"head-{label}\n".encode()
        return b""

    def coordinate() -> None:
        try:
            for repository in repositories:
                if not started[repository].wait(timeout=60):
                    raise AssertionError(f"worker did not start: {repository}")
            release[nested].set()
            if not completed[nested].wait(timeout=60):
                raise AssertionError("nested worker did not acknowledge completion")
            release[snapshot].set()
            if not completed[snapshot].wait(timeout=60):
                raise AssertionError("root worker did not acknowledge completion")
        except BaseException as exc:
            controller_failures.append(exc)
        finally:
            for event in release.values():
                event.set()

    monkeypatch.setattr(TOOL, "_prepare_one_git_closure", fake_prepare)
    monkeypatch.setattr(TOOL, "_run", fake_run)
    monkeypatch.setattr(TOOL, "_git", fake_git)
    monkeypatch.setattr(
        TOOL,
        "_submodule_content_identity_reasons",
        lambda *_args, **_kwargs: ["middle preflight failure"],
    )

    controller = threading.Thread(target=coordinate, daemon=True)
    controller.start()
    reasons, manifests, submodules = TOOL._git_closure_reasons(
        snapshot,
        (),
        inventory=(
            [middle, nested],
            [
                {"path": "deps/middle", "initialization": "initialized"},
                {"path": "deps/nested", "initialization": "initialized"},
            ],
        ),
        preflight_cache={middle: ("middle preflight failure",)},
    )
    controller.join(timeout=60)

    assert not controller.is_alive()
    assert controller_failures == []
    assert completion_order == [nested, snapshot]
    assert prepared == [snapshot, nested]
    assert [row["repository"] for row in manifests] == [".", "deps/nested"]
    assert all(
        list(manifest)
        == [
            "repository",
            "git_dir",
            "head",
            "refs",
            "commit_graph",
            "metadata",
        ]
        for manifest in manifests
    )
    assert reasons == [
        ".: git fsck exited 11: root stderr",
        ".: git object store contains unreachable objects (1)",
        "deps/nested: git fsck exited 12: nested stderr",
        "deps/nested: git object store contains unreachable objects (2)",
        "middle preflight failure",
    ]
    assert submodules == [
        {"path": "deps/middle", "initialization": "initialized"},
        {"path": "deps/nested", "initialization": "initialized"},
    ]


def test_git_fsck_worker_failure_drains_and_reasonizes_normal_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    nested = snapshot / "deps/nested"
    called: list[Path] = []
    gated_labels: list[str] = []
    original_gate = TOOL._git_fsck_reasons

    monkeypatch.setattr(
        TOOL,
        "_prepare_one_git_closure",
        lambda root, repository, refs: _synthetic_git_closure_state(
            root, repository, refs
        ),
    )

    def fake_run(_argv: Any, *, cwd: Path, **_kwargs: Any) -> Any:
        repository = Path(cwd)
        called.append(repository)
        if repository == snapshot:
            raise OSError("root spawn failed")
        return subprocess.CompletedProcess(
            ["git", "fsck"],
            0,
            b"unreachable blob nested\n",
            b"",
        )

    def observed_gate(label: str, result: Any) -> list[str]:
        gated_labels.append(label)
        return original_gate(label, result)

    monkeypatch.setattr(TOOL, "_run", fake_run)
    monkeypatch.setattr(TOOL, "_git_fsck_reasons", observed_gate)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._parallel_git_closure_reasons(
            snapshot,
            (
                (snapshot, [f"refs/heads/{TOOL.BRANCH}"]),
                (nested, []),
            ),
        )

    assert set(called) == {snapshot, nested}
    assert gated_labels == ["deps/nested"]
    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        "deps/nested: git object store contains unreachable objects (1)",
        f".: git fsck worker failed for {snapshot}: "
        "OSError: root spawn failed",
    )
    assert isinstance(caught.value.__cause__, OSError)


def test_git_fsck_all_failures_and_unsubmitted_prepare_reasons_are_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    repositories = (
        snapshot,
        snapshot / "first-success",
        snapshot / "second-worker-failure",
        snapshot / "submit-failure",
        snapshot / "not-submitted",
    )
    worker_failure = OSError("root worker failed")
    second_worker_failure = PermissionError("nested worker failed")
    submit_failure = RuntimeError("fourth submit failed")

    class WorkerFailureFuture:
        def __init__(self, failure: OSError):
            self.failure = failure

        def result(self) -> subprocess.CompletedProcess[bytes]:
            raise self.failure

    class SuccessfulFuture:
        def result(self) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(
                ["git", "fsck"],
                0,
                b"unreachable blob success\n",
                b"",
            )

    class MixedFailureExecutor:
        def __init__(self, *, max_workers: int):
            assert max_workers == len(repositories)
            self.submits = 0

        def __enter__(self) -> Any:
            return self

        def submit(self, *_args: Any, **_kwargs: Any) -> Any:
            self.submits += 1
            if self.submits == 1:
                return WorkerFailureFuture(worker_failure)
            if self.submits == 2:
                return SuccessfulFuture()
            if self.submits == 3:
                return WorkerFailureFuture(second_worker_failure)
            raise submit_failure

        def __exit__(self, *_args: Any) -> None:
            return None

    def prepare(root: Path, repository: Path, refs: list[str]) -> Any:
        state = _synthetic_git_closure_state(root, repository, refs)
        state.reasons.append(f"{state.label}: prepare reason")
        return state

    monkeypatch.setattr(TOOL, "ThreadPoolExecutor", MixedFailureExecutor)
    monkeypatch.setattr(TOOL, "_prepare_one_git_closure", prepare)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._parallel_git_closure_reasons(
            snapshot, tuple((repository, []) for repository in repositories)
        )

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    normalized = tuple(
        reason.replace(os.fspath(snapshot), "<snapshot>")
        for reason in caught.value.reasons
    )
    assert normalized == (
        ".: prepare reason",
        "first-success: prepare reason",
        "first-success: git object store contains unreachable objects (1)",
        "second-worker-failure: prepare reason",
        ".: git fsck worker failed for <snapshot>: "
        "OSError: root worker failed",
        "second-worker-failure: git fsck worker failed for "
        "<snapshot>/second-worker-failure: "
        "PermissionError: nested worker failed",
        "submit-failure: git fsck submit failed for <snapshot>/submit-failure: "
        "RuntimeError: fourth submit failed",
        "submit-failure: prepare reason",
        "not-submitted: prepare reason",
    )
    assert caught.value.__cause__ is worker_failure


def test_git_fsck_executor_construction_failure_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    nested = snapshot / "nested"
    monkeypatch.setattr(
        TOOL,
        "_prepare_one_git_closure",
        lambda root, repository, refs: _synthetic_git_closure_state(
            root, repository, refs
        ),
    )

    def fail_executor(*, max_workers: int) -> Any:
        assert max_workers == 2
        raise OSError("executor unavailable")

    monkeypatch.setattr(TOOL, "ThreadPoolExecutor", fail_executor)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._parallel_git_closure_reasons(
            snapshot,
            ((snapshot, []), (nested, [])),
        )

    assert caught.value.reasons == (
        f"git fsck executor failed for {snapshot}: "
        "OSError: executor unavailable",
    )


def test_git_fsck_executor_caps_workers_at_eight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    repositories = [snapshot, *[snapshot / f"nested-{index}" for index in range(8)]]
    observed_workers: list[int] = []
    result_calls = 0

    class ImmediateFuture:
        def result(self) -> subprocess.CompletedProcess[bytes]:
            nonlocal result_calls
            result_calls += 1
            return subprocess.CompletedProcess(["git", "fsck"], 0, b"", b"")

    class ImmediateExecutor:
        def __init__(self, *, max_workers: int):
            observed_workers.append(max_workers)

        def __enter__(self) -> Any:
            return self

        def submit(self, *_args: Any, **_kwargs: Any) -> Any:
            return ImmediateFuture()

        def __exit__(self, *args: Any) -> None:
            return None

    monkeypatch.setattr(TOOL, "ThreadPoolExecutor", ImmediateExecutor)
    monkeypatch.setattr(
        TOOL,
        "_prepare_one_git_closure",
        lambda root, repository, refs: _synthetic_git_closure_state(
            root, repository, refs
        ),
    )
    monkeypatch.setattr(TOOL, "_git", lambda *_args, **_kwargs: b"head\n")

    reasons, manifests = TOOL._parallel_git_closure_reasons(
        snapshot,
        [(repository, []) for repository in repositories],
    )

    assert observed_workers == [8]
    assert result_calls == len(repositories)
    assert reasons == []
    assert [row["repository"] for row in manifests] == [
        ".",
        *[f"nested-{index}" for index in range(8)],
    ]


def test_git_fsck_submit_failure_consumes_prior_future_before_rejecting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    nested = snapshot / "nested"
    result_calls: list[int] = []

    class FirstFuture:
        def result(self) -> subprocess.CompletedProcess[bytes]:
            result_calls.append(1)
            return subprocess.CompletedProcess(
                ["git", "fsck"],
                0,
                b"unreachable blob root\n",
                b"",
            )

    class SubmitFailureExecutor:
        def __init__(self, *, max_workers: int):
            assert max_workers == 2
            self.submits = 0

        def __enter__(self) -> Any:
            return self

        def submit(self, *_args: Any, **_kwargs: Any) -> Any:
            self.submits += 1
            if self.submits == 2:
                raise OSError("submit unavailable")
            return FirstFuture()

        def __exit__(self, *args: Any) -> None:
            return None

    monkeypatch.setattr(TOOL, "ThreadPoolExecutor", SubmitFailureExecutor)
    monkeypatch.setattr(
        TOOL,
        "_prepare_one_git_closure",
        lambda root, repository, refs: _synthetic_git_closure_state(
            root, repository, refs
        ),
    )

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._parallel_git_closure_reasons(
            snapshot,
            ((snapshot, []), (nested, [])),
        )

    assert result_calls == [1]
    assert caught.value.reasons == (
        ".: git object store contains unreachable objects (1)",
        f"nested: git fsck submit failed for {nested}: "
        "OSError: submit unavailable",
    )


def test_git_fsck_worker_uses_run_subprocess_environment_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    nested = snapshot / "nested"
    main_thread = threading.get_ident()
    calls: list[dict[str, Any]] = []

    monkeypatch.setenv("GIT_DIR", "/poison/git-dir")
    monkeypatch.setenv("GIT_ALTERNATE_OBJECT_DIRECTORIES", "/poison/objects")
    monkeypatch.setattr(
        TOOL,
        "_prepare_one_git_closure",
        lambda root, repository, refs: _synthetic_git_closure_state(
            root, repository, refs
        ),
    )
    monkeypatch.setattr(TOOL, "_git", lambda *_args, **_kwargs: b"head\n")

    def fake_subprocess_run(argv: Any, **kwargs: Any) -> Any:
        calls.append(
            {
                "thread": threading.get_ident(),
                "argv": tuple(argv),
                **kwargs,
            }
        )
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    monkeypatch.setattr(TOOL.subprocess, "run", fake_subprocess_run)

    reasons, manifests = TOOL._parallel_git_closure_reasons(
        snapshot,
        ((snapshot, []), (nested, [])),
    )

    assert reasons == []
    assert [row["repository"] for row in manifests] == [".", "nested"]
    assert len(calls) == 2
    assert {Path(call["cwd"]) for call in calls} == {snapshot, nested}
    for call in calls:
        assert call["thread"] != main_thread
        assert call["argv"] == (
            "git",
            "fsck",
            "--unreachable",
            "--no-reflogs",
        )
        assert call["env"]["HOME"] == "/nonexistent"
        assert not any(key.startswith("GIT_") for key in call["env"])
        assert call["capture_output"] is True
        assert call["check"] is False
        assert call["input"] is None


def test_m1_snapshot_head_pin_is_independent(
    benchmark_snapshots: dict[str, Any],
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    spec = copy.deepcopy(
        TOOL._snapshot_spec("POS", task_manifest=task_manifest)
    )
    spec["head"] = "0" * 40
    with pytest.raises(TOOL.ValidationError, match="HEAD mismatch"):
        TOOL.verify_snapshot(
            benchmark_snapshots["POS"]["snapshot"],
            "POS",
            spec=spec,
            task_manifest=task_manifest,
        )


def test_m2_production_golden_requires_both_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions_root = TOOL._sessions_default()
    _require_pinned_rollouts(sessions_root)
    called = False
    original = TOOL._compare_golden_routes

    def observed(route_a: Any, route_b: Any) -> dict[str, bytes]:
        nonlocal called
        called = True
        return original(route_a, route_b)

    monkeypatch.setattr(TOOL, "_compare_golden_routes", observed)
    golden = TOOL.derive_independent_golden(_ROOT, sessions_root)
    assert called is True
    assert hashlib.sha256(golden[TOOL.PATCH_PATHS[0]]).hexdigest() == (
        "bc3f5f95f5c9c3f44955bbd1b2e3affbbafb6e62fda8e836173e1b9d5998c3af"
    )


def test_m3_snapshot_mode_change(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    for case in ("POS", "NEG"):
        snapshot = tmp_path / case.lower()
        shutil.copytree(benchmark_snapshots[case]["snapshot"], snapshot)
        target = snapshot / TOOL.TRACKED_PATHS[0]
        target.chmod(0o600)
        with pytest.raises(TOOL.ValidationError, match="st_mode mismatch"):
            TOOL.verify_snapshot(snapshot, case, task_manifest=task_manifest)


def test_m3_symbolic_head_is_required(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    snapshot = tmp_path / "detached"
    shutil.copytree(benchmark_snapshots["POS"]["snapshot"], snapshot)
    (snapshot / ".git/HEAD").write_text(TOOL.BASE_COMMIT + "\n", encoding="ascii")
    with pytest.raises(TOOL.ValidationError, match="symbolic HEAD mismatch"):
        TOOL.verify_snapshot(snapshot, "POS", task_manifest=task_manifest)


def test_m3_ignored_extra_and_missing(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    for case in ("POS", "NEG"):
        extra_snapshot = tmp_path / f"extra-{case.lower()}"
        shutil.copytree(benchmark_snapshots[case]["snapshot"], extra_snapshot)
        (extra_snapshot / ".answer-cache").write_text("leak", encoding="utf-8")
        with (extra_snapshot / ".git/info/exclude").open("a", encoding="utf-8") as stream:
            stream.write("\n.answer-cache\n")
        with pytest.raises(TOOL.ValidationError, match="filesystem allowlist has extra"):
            TOOL.verify_snapshot(
                extra_snapshot, case, task_manifest=task_manifest
            )
        missing_snapshot = tmp_path / f"missing-{case.lower()}"
        shutil.copytree(benchmark_snapshots[case]["snapshot"], missing_snapshot)
        missing_relative = (
            f"{TOOL.ARTIFACT_DIR}/focus1.md"
            if case == "NEG"
            else TOOL._snapshot_spec(
                case, task_manifest=task_manifest
            )["untracked"][0]
        )
        (missing_snapshot / missing_relative).unlink()
        with pytest.raises(TOOL.ValidationError, match="missing"):
            TOOL.verify_snapshot(
                missing_snapshot, case, task_manifest=task_manifest
            )


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
    task_manifest = benchmark_snapshots["task_manifest"]
    snapshot = tmp_path / f"{case.lower()}-{name}"
    shutil.copytree(benchmark_snapshots[case]["snapshot"], snapshot)
    target = snapshot / TOOL.ARTIFACT_DIR / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("forbidden", encoding="utf-8")
    with pytest.raises(TOOL.ValidationError, match="forbidden focus artifact"):
        TOOL.verify_snapshot(snapshot, case, task_manifest=task_manifest)


def test_snapshot_submodule_object_store_is_recursive(
    tmp_path: Path, benchmark_snapshots: dict[str, Any]
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
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
    clean_oracle = TOOL.verify_snapshot(
        snapshot, "POS", task_manifest=task_manifest
    )
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
        TOOL.verify_snapshot(snapshot, "POS", task_manifest=task_manifest)


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
    snapshot = (
        tmp_path / ("a" * 32) / ("b" * 32) / ("c" * 32) / "snapshot"
    )
    snapshot.mkdir(parents=True)
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
    previous_cwd = Path.cwd()
    try:
        assert len(os.fsencode(snapshot / "socket")) >= 108
        os.chdir(snapshot)
        unix_socket.bind("socket")
        reference = _rglob_filesystem_file_set_reference(snapshot)
        actual = TOOL._filesystem_file_set(snapshot)
    finally:
        os.chdir(previous_cwd)
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
    """Legacy node name retained; the scanner must no longer resolve paths."""
    snapshot = tmp_path / "snapshot"
    parent = snapshot / "parent"
    parent.mkdir(parents=True)
    (snapshot / "empty").mkdir()
    (parent / "first").write_text("first\n", encoding="utf-8")
    (parent / "second").write_text("second\n", encoding="utf-8")

    def fail_resolve(_path: Path, strict: bool = False) -> Path:
        raise AssertionError(f"Path.resolve must not be called, strict={strict}")

    monkeypatch.setattr(Path, "resolve", fail_resolve)

    expected = {"parent/first", "parent/second"}
    assert TOOL._filesystem_file_set(snapshot) == expected


def test_filesystem_file_set_memoizes_resolved_parent_decision_per_call(
    tmp_path: Path,
) -> None:
    """Legacy node name retained; directory symlinks remain leaf entries."""
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    target = snapshot / "target"
    target.mkdir()
    (target / "inside.txt").write_text("inside\n", encoding="utf-8")
    alias = snapshot / "alias"
    alias.symlink_to(target, target_is_directory=True)

    actual = TOOL._filesystem_file_set(snapshot)

    assert actual == {"alias", "target/inside.txt"}
    assert "alias/inside.txt" not in actual


@pytest.mark.parametrize(
    "error_type", (PermissionError, OSError), ids=("permission", "io-error")
)
def test_filesystem_file_set_parent_resolve_errors_propagate_per_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[OSError],
) -> None:
    """Legacy node name retained; scandir errors replace resolve failures."""
    snapshot = tmp_path / "snapshot"
    denied = snapshot / "denied"
    denied.mkdir(parents=True)
    (denied / "hidden").write_text("hidden\n", encoding="utf-8")
    original_scandir = os.scandir

    def failing_scandir(path: Any) -> Any:
        if Path(path) == denied:
            raise error_type("directory scan failed")
        return original_scandir(path)

    monkeypatch.setattr(TOOL.os, "scandir", failing_scandir)

    # Enumeration errors are intentionally excluded from the rglob
    # differential: the ruling changes this error case to fail closed.
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._filesystem_file_set(snapshot)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        f"filesystem directory enumeration failed at {denied}: "
        f"{error_type.__name__}: directory scan failed",
    )


def test_filesystem_file_set_lstat_error_is_structured_rejection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    failed = snapshot / "failed"
    failed.write_text("payload\n", encoding="utf-8")
    original_lstat = Path.lstat

    def failing_lstat(path: Path) -> os.stat_result:
        if path == failed:
            raise OSError("entry stat failed")
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", failing_lstat)

    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._filesystem_file_set(snapshot)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        f"filesystem entry lstat failed at {failed}: "
        "OSError: entry stat failed",
    )


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

        # The legacy rglob oracle hides this failure as an empty subtree.  The
        # approved F363 ruling deliberately excludes this case from the
        # differential and reverses it to rejection.
        assert _rglob_filesystem_file_set_reference(snapshot) == {"visible"}
        with pytest.raises(TOOL.ValidationError) as caught:
            TOOL._filesystem_file_set(snapshot)
        assert caught.value.rc == TOOL.RC_SNAPSHOT
        assert os.fspath(denied) in caught.value.reasons[0]
        assert "PermissionError" in caught.value.reasons[0]
    finally:
        os.chmod(denied, denied_mode)


def test_filesystem_file_set_symlink_root_git_is_included(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    git_target = tmp_path / "git-target"
    git_target.mkdir()
    (git_target / "hidden").write_text("outside\n", encoding="utf-8")
    (snapshot / ".git").symlink_to(git_target, target_is_directory=True)
    (snapshot / "visible").write_text("visible\n", encoding="utf-8")

    actual = TOOL._filesystem_file_set(snapshot)

    assert actual == {".git", "visible"}
    assert actual == _rglob_filesystem_file_set_reference(snapshot)


def test_filesystem_file_set_scans_and_lstats_each_entry_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    child = snapshot / "child"
    empty = snapshot / "empty"
    root_git = snapshot / ".git"
    child.mkdir(parents=True)
    empty.mkdir()
    root_git.mkdir()
    visible = snapshot / "visible"
    nested = child / "nested"
    poison = root_git / "poison"
    visible.write_text("visible\n", encoding="utf-8")
    nested.write_text("nested\n", encoding="utf-8")
    poison.write_text("pruned\n", encoding="utf-8")
    scandir_calls: dict[Path, int] = {}
    lstat_calls: dict[Path, int] = {}
    events: list[tuple[str, Path]] = []
    original_scandir = os.scandir
    original_lstat = Path.lstat

    def counted_scandir(path: Any) -> Any:
        candidate = Path(path)
        scandir_calls[candidate] = scandir_calls.get(candidate, 0) + 1
        events.append(("scandir", candidate))
        return original_scandir(path)

    def counted_lstat(path: Path) -> os.stat_result:
        lstat_calls[path] = lstat_calls.get(path, 0) + 1
        events.append(("lstat", path))
        return original_lstat(path)

    monkeypatch.setattr(TOOL.os, "scandir", counted_scandir)
    monkeypatch.setattr(Path, "lstat", counted_lstat)

    assert TOOL._filesystem_file_set(snapshot) == {
        "visible",
        "child/nested",
    }
    assert scandir_calls == {snapshot: 1, child: 1, empty: 1}
    assert lstat_calls == {
        child: 1,
        empty: 1,
        root_git: 1,
        visible: 1,
        nested: 1,
    }
    assert poison not in lstat_calls
    first_recursive_scan = min(
        events.index(("scandir", child)),
        events.index(("scandir", empty)),
    )
    assert all(
        events.index(("lstat", path)) < first_recursive_scan
        for path in (child, empty, root_git, visible)
    )
    assert events.index(("scandir", child)) < events.index(("lstat", nested))


def test_filesystem_file_set_accepts_readable_static_tree(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "snapshot"
    nested = snapshot / "nested"
    nested.mkdir(parents=True)
    (snapshot / "visible").write_text("visible\n", encoding="utf-8")
    (nested / "payload").write_text("payload\n", encoding="utf-8")

    assert TOOL._filesystem_file_set(snapshot) == {
        "visible",
        "nested/payload",
    }


def test_filesystem_file_set_deep_tree_is_not_recursion_limited(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    directory = snapshot
    segments: list[str] = []
    for _ in range(180):
        segments.append("d")
        directory = directory / "d"
        directory.mkdir()
    payload = directory / "payload"
    payload.write_text("payload\n", encoding="utf-8")
    expected = "/".join([*segments, "payload"])
    previous_limit = sys.getrecursionlimit()

    try:
        sys.setrecursionlimit(128)
        actual = TOOL._filesystem_file_set(snapshot)
    finally:
        sys.setrecursionlimit(previous_limit)

    assert actual == {expected}


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


def test_verify_snapshot_reuses_one_filesystem_observation_per_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = (tmp_path / "first", tmp_path / "second")
    for snapshot in snapshots:
        (snapshot / ".git").mkdir(parents=True)
    scanner_calls: list[Path] = []
    closure_observations: list[tuple[Any, set[str]]] = []

    def fake_scanner(snapshot: Path) -> set[str]:
        scanner_calls.append(snapshot)
        return {f"{snapshot.name}.txt"}

    def fake_closure(
        snapshot: Path,
        _untracked: Any,
        **kwargs: Any,
    ) -> tuple[list[str], list[dict[str, Any]], list[dict[str, str]]]:
        observation = kwargs["filesystem_observation"]
        closure_observations.append(
            (observation, set(observation.read(snapshot)))
        )
        return [], [], []

    def fake_git(_repository: Path, *args: str, **_kwargs: Any) -> bytes:
        if args == ("rev-parse", "HEAD"):
            return b"head\n"
        return b""

    def fake_run(argv: Any, **_kwargs: Any) -> Any:
        assert tuple(argv) == ("git", "symbolic-ref", "--short", "HEAD")
        return subprocess.CompletedProcess(argv, 0, b"main\n", b"")

    monkeypatch.setattr(TOOL, "_filesystem_file_set", fake_scanner)
    monkeypatch.setattr(TOOL, "_git_closure_reasons", fake_closure)
    monkeypatch.setattr(TOOL, "_git", fake_git)
    monkeypatch.setattr(TOOL, "_run", fake_run)
    monkeypatch.setattr(TOOL, "_status_sets", lambda _snapshot: ([], []))
    monkeypatch.setattr(
        TOOL,
        "_cached_repository_preflight_reasons",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        TOOL, "_submodule_inventory", lambda *_args, **_kwargs: ([], [])
    )
    spec = {
        "head": "head",
        "branch": "main",
        "tracked_paths": [],
        "untracked": [],
        "numstat": [],
        "hashes": {},
        "forbidden": [],
        "git_object_closure": True,
    }

    oracles = [
        TOOL.verify_snapshot(snapshot, "POS", spec=spec)
        for snapshot in snapshots
    ]

    resolved = [snapshot.resolve() for snapshot in snapshots]
    assert scanner_calls == resolved
    assert closure_observations[0][0] is not closure_observations[1][0]
    assert [files for _, files in closure_observations] == [
        {"first.txt"},
        {"second.txt"},
    ]
    assert [oracle["filesystem_files"] for oracle in oracles] == [
        ["first.txt"],
        ["second.txt"],
    ]


def test_filesystem_observation_rejects_cross_snapshot_reuse(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    observation = TOOL._SnapshotFilesystemFiles(first)

    assert observation.read(first) == set()
    with pytest.raises(TOOL.ValidationError) as caught:
        observation.read(second)

    assert caught.value.rc == TOOL.RC_SNAPSHOT
    assert caught.value.reasons == (
        "filesystem observation snapshot mismatch: "
        f"{second.resolve()} != {first.resolve()}",
    )


def test_git_closure_preflight_failure_still_skips_allowlist_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    child = snapshot / "child"
    snapshot.mkdir()
    scanner_calls = 0

    def fake_scanner(_snapshot: Path) -> set[str]:
        nonlocal scanner_calls
        scanner_calls += 1
        return {"oracle-only"}

    monkeypatch.setattr(TOOL, "_filesystem_file_set", fake_scanner)
    monkeypatch.setattr(
        TOOL,
        "_one_git_closure_reasons",
        lambda *_args, **_kwargs: ([], {"repository": "."}),
    )
    monkeypatch.setattr(
        TOOL,
        "_submodule_content_identity_reasons",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        TOOL,
        "_run",
        lambda argv, **_kwargs: subprocess.CompletedProcess(argv, 1, b"", b""),
    )
    monkeypatch.setattr(TOOL, "_git", lambda *_args, **_kwargs: b"")
    observation = TOOL._SnapshotFilesystemFiles(snapshot)

    reasons, manifests, _ = TOOL._git_closure_reasons(
        snapshot,
        (),
        inventory=(
            [child],
            [{"path": "child", "initialization": "initialized"}],
        ),
        preflight_cache={child: ("preflight failed",)},
        filesystem_observation=observation,
    )

    assert reasons == []
    assert manifests == [{"repository": "."}]
    assert scanner_calls == 0
    assert observation.read(snapshot) == {"oracle-only"}
    assert scanner_calls == 1


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
        *,
        task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
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
        candidate_repo: Path,
        candidate_sessions: Path,
        case: str,
        *,
        task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
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
        *,
        task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
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
    expected_task_manifest = TOOL.TASK_MANIFEST

    def snapshot_spec(
        case: str,
        *,
        task_manifest: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        assert case == "POS"
        assert task_manifest is expected_task_manifest
        return spec

    monkeypatch.setattr(TOOL, "_snapshot_spec", snapshot_spec)

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
        "task_manifest_sha256",
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
        "task_manifest_sha256",
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
    task_manifest = benchmark_snapshots["task_manifest"]
    _, slots = _schedule(
        tmp_path / "schedule.json",
        benchmark_snapshots,
        task_manifest=task_manifest,
    )
    for slot in slots:
        if slot["case"] == "NEG":
            slot["submodule_manifest_sha256"] = "f" * 64
    _, reasons = TOOL._validate_schedule(
        {"slots": slots}, task_manifest=task_manifest
    )
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


def test_task_manifest_loader_accepts_only_strict_canonical_json_object(
    tmp_path: Path,
) -> None:
    manifest = _synthetic_task_manifest()
    path = _canonical(tmp_path / "task-manifest.json", manifest)
    loaded = TOOL._load_task_manifest(path)
    assert loaded == manifest
    assert TOOL._task_manifest_sha256(loaded) == TOOL._sha256(
        TOOL._canonical_bytes(manifest)
    )


def test_or_m1_loader_pins_checked_in_slice_semantic_sha(tmp_path: Path) -> None:
    assert TOOL._sha256(_WIRING_SLICE_PATH.read_bytes()) == _WIRING_SLICE_SHA256
    assert TOOL._WIRING_SLICE_MANIFEST_RAW_SHA256 == _WIRING_SLICE_SHA256
    assert TOOL.WIRING_SLICE.SLICE_SHA256 == _WIRING_SLICE_SHA256
    loaded = TOOL._load_task_manifest(
        _WIRING_SLICE_PATH,
        profile=_WIRING_SLICE_PROFILE,
    )
    assert loaded["manifest_kind"] == "t189-task-oracle-wiring-slice"
    assert TOOL._task_manifest_sha256(loaded) == _WIRING_SLICE_SHA256

    mutated = copy.deepcopy(loaded)
    mutated["tasks"]["T-1222-population-closure:plan:0"]["oracle_findings"][0][
        "detection_condition"
    ] += " A semantic mutation must not acquire the checked-in pin."
    path = _canonical(tmp_path / "mutated-slice.json", mutated)
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(path, profile=_WIRING_SLICE_PROFILE)
    assert caught.value.reasons == (
        "wiring_slice: semantic SHA-256 pin mismatch",
    )


def test_or_m3_production_validator_rejects_projection_change() -> None:
    value = json.loads(_WIRING_SLICE_PATH.read_bytes())
    value["tasks"]["T-1222-population-closure:plan:0"][
        "known_finding_ids"
    ] = ["wrong-finding"]
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._validate_task_manifest(value, profile=_WIRING_SLICE_PROFILE)
    assert caught.value.reasons == (
        "wiring_slice.tasks[T-1222-population-closure:plan:0]."
        "known_finding_ids: oracle finding projection mismatch",
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("unknown", "wiring_slice: field set mismatch"),
        (
            "status",
            "wiring_slice.tasks[T-1222-population-closure:plan:0]."
            "task_acceptance_status: must be unbound",
        ),
        (
            "kind-downgrade",
            "task manifest kind downgrade from oracle wiring slice",
        ),
    ),
)
def test_production_loader_rejects_slice_schema_and_kind_downgrades(
    mutation: str, expected: str,
) -> None:
    value = json.loads(_WIRING_SLICE_PATH.read_bytes())
    if mutation == "unknown":
        value["unknown"] = True
    elif mutation == "status":
        value["tasks"]["T-1222-population-closure:plan:0"][
            "task_acceptance_status"
        ] = "bound"
    else:
        value["manifest_kind"] = "t181-task-manifest"
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._validate_task_manifest(value, profile=_WIRING_SLICE_PROFILE)
    assert caught.value.reasons == (expected,)


def test_slice_loader_rejects_missing_lf_without_weakening_t181_loader(
    tmp_path: Path,
) -> None:
    slice_path = tmp_path / "slice-no-lf.json"
    slice_path.write_bytes(_WIRING_SLICE_PATH.read_bytes()[:-1])
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(slice_path, profile=_WIRING_SLICE_PROFILE)
    assert caught.value.reasons == (
        "oracle wiring slice bytes must be sorted compact UTF-8 with exactly one LF",
    )

    t181_path = tmp_path / "t181-without-lf.json"
    t181_path.write_bytes(TOOL._canonical_bytes(_synthetic_task_manifest())[:-1])
    assert TOOL._load_task_manifest(t181_path)["manifest_kind"] == (
        "t181-task-manifest"
    )


def test_slice_kind_requires_explicit_profile() -> None:
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(_WIRING_SLICE_PATH)
    assert caught.value.reasons == ("task manifest kind mismatch",)


def test_profile_rejects_complete_slice_field_removal_and_t181_envelope() -> None:
    value = json.loads(_WIRING_SLICE_PATH.read_bytes())
    for field in tuple(value):
        if field not in {"manifest_kind", "schema_version", "tasks"}:
            del value[field]
    value["manifest_kind"] = "t181-task-manifest"
    value["shared_provenance"] = copy.deepcopy(
        TOOL.TASK_MANIFEST["shared_provenance"]
    )
    slice_task_fields = {
        "fix_gate_eligible",
        "oracle_findings",
        "replay_artifact_sufficiency",
        "routing_evidence_eligible",
        "t189_stage_boundary",
        "task_acceptance_status",
    }
    for task in value["tasks"].values():
        for field in slice_task_fields:
            task.pop(field, None)

    TOOL._validate_task_manifest(value)
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._validate_task_manifest(value, profile=_WIRING_SLICE_PROFILE)
    assert caught.value.reasons == (
        "task manifest kind downgrade from oracle wiring slice",
    )


def test_t181_unknown_top_level_field_remains_accepted(tmp_path: Path) -> None:
    value = _synthetic_task_manifest()
    value["section8_complete"] = False
    path = _canonical(tmp_path / "t181-extension.json", value)
    assert TOOL._load_task_manifest(path) == value


def test_pinned_verifier_loader_accepts_the_authenticated_regular_file() -> None:
    loaded = TOOL._load_pinned_wiring_slice_module(_WIRING_SLICE_TOOL_PATH)
    assert loaded.SLICE_KIND == "t189-task-oracle-wiring-slice"


def test_pinned_verifier_loader_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ImportError, match="unavailable or unsafe"):
        TOOL._load_pinned_wiring_slice_module(tmp_path / "missing.py")


def test_pinned_verifier_loader_rejects_symlink(tmp_path: Path) -> None:
    path = tmp_path / "verifier.py"
    path.symlink_to(_WIRING_SLICE_TOOL_PATH)
    with pytest.raises(ImportError, match="unavailable or unsafe"):
        TOOL._load_pinned_wiring_slice_module(path)


def test_pinned_verifier_loader_rejects_one_byte_change(tmp_path: Path) -> None:
    raw = bytearray(_WIRING_SLICE_TOOL_PATH.read_bytes())
    raw[0] ^= 1
    path = tmp_path / "verifier.py"
    path.write_bytes(raw)
    with pytest.raises(ImportError, match="SHA-256 pin mismatch"):
        TOOL._load_pinned_wiring_slice_module(path)


def test_pinned_verifier_loader_rejects_constant_change(tmp_path: Path) -> None:
    original = (
        b'SLICE_KIND = "t189-task-oracle-wiring-slice"'
    )
    replacement = (
        b'SLICE_KIND = "t189-task-oracle-wiring-slicf"'
    )
    raw = _WIRING_SLICE_TOOL_PATH.read_bytes()
    assert raw.count(original) == 1
    path = tmp_path / "verifier.py"
    path.write_bytes(raw.replace(original, replacement, 1))
    with pytest.raises(ImportError, match="SHA-256 pin mismatch"):
        TOOL._load_pinned_wiring_slice_module(path)


def test_m11_task_manifest_loader_rejects_invalid_utf8_before_json_recovery(
    tmp_path: Path,
) -> None:
    raw = TOOL._canonical_bytes(_synthetic_task_manifest()).replace(
        b'"task_type":"t181-frozen"',
        b'"task_type":"t181-\xfffrozen"',
        1,
    )
    assert b"\xff" in raw
    path = tmp_path / "invalid-utf8.json"
    path.write_bytes(raw)
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(path)
    assert caught.value.rc == TOOL.RC_ROUTING
    assert len(caught.value.reasons) == 1
    assert caught.value.reasons[0].startswith(
        "task manifest is not strict UTF-8"
    )


def test_m12_task_manifest_loader_rejects_duplicate_key_with_equal_values(
    tmp_path: Path,
) -> None:
    raw = TOOL._canonical_bytes(_synthetic_task_manifest()).replace(
        b'{"manifest_kind":"t181-task-manifest",',
        (
            b'{"manifest_kind":"t181-task-manifest",'
            b'"manifest_kind":"t181-task-manifest",'
        ),
        1,
    )
    path = tmp_path / "duplicate-key.json"
    path.write_bytes(raw)
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(path)
    assert caught.value.rc == TOOL.RC_ROUTING
    assert caught.value.reasons == (
        "task manifest JSON is invalid: duplicate JSON key: manifest_kind",
    )


def test_m13_task_manifest_schema_version_requires_exact_int(
    tmp_path: Path,
) -> None:
    manifest = _synthetic_task_manifest()
    manifest["schema_version"] = 3.0
    path = _canonical(tmp_path / "float-version.json", manifest)
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(path)
    assert caught.value.rc == TOOL.RC_ROUTING
    assert caught.value.reasons == (
        "task manifest schema_version must be 3",
    )


@pytest.mark.parametrize(
    "value",
    (["not-an-object"], "not-an-object", None),
    ids=("array", "string", "null"),
)
def test_task_manifest_loader_rejects_non_object_top_level(
    tmp_path: Path,
    value: Any,
) -> None:
    path = _canonical(tmp_path / "non-object.json", value)
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(path)
    assert caught.value.rc == TOOL.RC_ROUTING
    assert caught.value.reasons == ("task manifest is not an object",)


@pytest.mark.parametrize("constant", ("NaN", "Infinity", "-Infinity"))
def test_task_manifest_loader_rejects_nonfinite_json_number(
    tmp_path: Path,
    constant: str,
) -> None:
    raw = TOOL._canonical_bytes(_synthetic_task_manifest()).replace(
        b'"stage":"stage-1"',
        f'"stage":{constant}'.encode("ascii"),
        1,
    )
    path = tmp_path / "nonfinite.json"
    path.write_bytes(raw)
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(path)
    assert caught.value.rc == TOOL.RC_ROUTING
    assert caught.value.reasons == (
        f"task manifest JSON is invalid: non-finite JSON number: {constant}",
    )


def test_task_manifest_loader_rejects_unreadable_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._load_task_manifest(missing)
    assert caught.value.rc == TOOL.RC_ROUTING
    assert len(caught.value.reasons) == 1
    assert caught.value.reasons[0].startswith("cannot read task manifest")


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


def _bound_price_schedule(
    *,
    task_id: str = "alpha",
    block_id: str = "b01",
) -> dict[str, Any]:
    return {
        "schema_version": 3,
        "price_snapshot": {
            "path": _TEST_PRICE_SNAPSHOT_PATH,
            "sha256": _TEST_PRICE_SNAPSHOT_SHA256,
        },
        "slots": [
            {
                **_v3_slot(
                    slot_id="s01",
                    task_id=task_id,
                    block_id=block_id,
                    block_order=1,
                    arm="max",
                    requested_model="gpt-5.6-sol",
                ),
                "price_version": _TEST_PRICE_VERSION,
            },
            {
                **_v3_slot(
                    slot_id="s02",
                    task_id=task_id,
                    block_id=block_id,
                    block_order=2,
                    arm="max",
                    requested_model="gpt-5.6-luna",
                ),
                "price_version": _TEST_PRICE_VERSION,
            },
        ],
    }


def _cross_arm_cost_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    task_manifest = _synthetic_task_manifest(
        (
            ("alpha", "POS", "positive", "alpha-finding"),
            ("beta", "POS", "positive", "beta-finding"),
        )
    )
    task_manifest["tasks"]["beta"]["stage"] = "stage-2"
    slot_specs = (
        ("s01", "alpha", "stage-1", "b02", 1, "max", "gpt-5.6-sol"),
        ("s02", "alpha", "stage-1", "b02", 2, "high", "gpt-5.6-luna"),
        ("s03", "alpha", "stage-1", "b01", 1, "max", "gpt-5.6-sol"),
        ("s04", "alpha", "stage-1", "b01", 2, "high", "gpt-5.6-luna"),
        ("s05", "beta", "stage-2", "b03", 1, "max", "gpt-5.6-sol"),
        ("s06", "beta", "stage-2", "b03", 2, "high", "gpt-5.6-luna"),
    )
    schedule = {
        "schema_version": 3,
        "price_snapshot": {
            "path": _TEST_PRICE_SNAPSHOT_PATH,
            "sha256": _TEST_PRICE_SNAPSHOT_SHA256,
        },
        "slots": [
            {
                **_v3_slot(
                    slot_id=slot_id,
                    task_id=task_id,
                    block_id=block_id,
                    block_order=block_order,
                    arm=arm,
                    requested_model=requested_model,
                    stage=stage,
                ),
                "price_version": _TEST_PRICE_VERSION,
            }
            for (
                slot_id,
                task_id,
                stage,
                block_id,
                block_order,
                arm,
                requested_model,
            ) in slot_specs
        ],
    }
    return task_manifest, schedule


def test_cli_real_import_loads_dataclass_price_verifier() -> None:
    completed = subprocess.run(
        [sys.executable, os.fspath(_TOOL_PATH), "--help"],
        cwd=_ROOT,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert b"supervise-pair" in completed.stdout


def test_frozen_price_test_literals_independently_pin_repo_bytes() -> None:
    snapshot_bytes = (_ROOT / _TEST_PRICE_SNAPSHOT_PATH).read_bytes()
    excerpt_bytes = (_ROOT / _TEST_PRICE_EXCERPT_PATH).read_bytes()
    assert hashlib.sha256(snapshot_bytes).hexdigest() == _TEST_PRICE_SNAPSHOT_SHA256
    assert hashlib.sha256(excerpt_bytes).hexdigest() == _TEST_PRICE_EXCERPT_SHA256
    assert len(excerpt_bytes) == _TEST_PRICE_EXCERPT_BYTES
    artifact = json.loads(snapshot_bytes)
    assert artifact["price_table_version"] == _TEST_PRICE_VERSION
    assert artifact["excerpt"] == {
        "storage": "repository",
        "path": _TEST_PRICE_EXCERPT_PATH,
        "relative_to": "repository-root",
        "sha256": _TEST_PRICE_EXCERPT_SHA256,
        "byte_offset": 275_792,
        "byte_length": _TEST_PRICE_EXCERPT_BYTES,
    }


def test_nullable_price_accepts_only_exact_frozen_expected_binding() -> None:
    row = {
        "benchmark_task_id": "POS",
        "case": "POS",
        "cache_condition": None,
        "price_version": _TEST_PRICE_VERSION,
    }
    assert TOOL.validate_nullable_dimensions(
        row,
        schema_version=3,
        expected_price_version=_TEST_PRICE_VERSION,
    ) == row


@pytest.mark.parametrize(
    ("price_version", "expected_price_version", "match"),
    (
        ("opaque-version-token", _TEST_PRICE_VERSION, "frozen price binding"),
        (
            "openai-pricing-standard-short-context:sha256:" + "0" * 64,
            _TEST_PRICE_VERSION,
            "frozen price binding",
        ),
        (_TEST_PRICE_VERSION, None, "non-null values are not supported"),
        ("", _TEST_PRICE_VERSION, "must be non-empty"),
        (7, _TEST_PRICE_VERSION, "must be a string or null"),
        (
            "openai-pricing-standard-short-context:sha256:" + "0" * 64,
            "openai-pricing-standard-short-context:sha256:" + "0" * 64,
            "frozen price binding",
        ),
    ),
    ids=(
        "opaque",
        "other-snapshot",
        "missing-expected",
        "empty",
        "non-string",
        "nonfrozen-expected",
    ),
)
def test_nullable_price_negative_matrix_is_fail_closed(
    price_version: Any,
    expected_price_version: str | None,
    match: str,
) -> None:
    row = {
        "benchmark_task_id": "POS",
        "case": "POS",
        "cache_condition": None,
        "price_version": price_version,
    }
    with pytest.raises(TOOL.ValidationError, match=match) as caught:
        TOOL.validate_nullable_dimensions(
            row,
            schema_version=3,
            expected_price_version=expected_price_version,
        )
    assert caught.value.rc == TOOL.RC_ROUTING


def test_slot_dimensions_direct_price_and_cache_gates_are_exposed() -> None:
    slot = _bound_price_schedule()["slots"][0]
    manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    dimensions = TOOL._slot_dimensions(
        slot,
        task_manifest=manifest,
        expected_price_version=_TEST_PRICE_VERSION,
    )
    assert dimensions["price_version"] == _TEST_PRICE_VERSION

    wrong = {**slot, "price_version": "opaque-version-token"}
    with pytest.raises(TOOL.ValidationError, match="frozen price binding") as caught:
        TOOL._slot_dimensions(
            wrong,
            task_manifest=manifest,
            expected_price_version=_TEST_PRICE_VERSION,
        )
    assert caught.value.rc == TOOL.RC_ROUTING

    cache = {**slot, "cache_condition": "cold"}
    with pytest.raises(
        TOOL.ValidationError,
        match="non-null values are not supported without attestation",
    ) as caught:
        TOOL._slot_dimensions(
            cache,
            task_manifest=manifest,
            expected_price_version=_TEST_PRICE_VERSION,
        )
    assert caught.value.rc == TOOL.RC_ROUTING


def test_validate_schedule_accepts_exact_bound_price_and_calls_verifier_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schedule = _bound_price_schedule()
    manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    reads: list[tuple[str, str]] = []
    delegated_read = TOOL._read_frozen_repo_file
    verifier_calls = 0
    delegated_validate = TOOL.PRICE_SNAPSHOT.validate_price_snapshot

    def observed_read(relative_path: str, label: str) -> bytes:
        reads.append((relative_path, label))
        return delegated_read(relative_path, label)

    def observed_validate(value: Any) -> dict[str, Any]:
        nonlocal verifier_calls
        verifier_calls += 1
        return delegated_validate(value)

    monkeypatch.setattr(TOOL, "_read_frozen_repo_file", observed_read)
    monkeypatch.setattr(
        TOOL.PRICE_SNAPSHOT, "validate_price_snapshot", observed_validate
    )
    slots, reasons = TOOL._validate_schedule(schedule, task_manifest=manifest)
    assert reasons == []
    assert {row["price_version"] for row in slots} == {_TEST_PRICE_VERSION}
    assert reads == [
        (_TEST_PRICE_SNAPSHOT_PATH, "frozen price snapshot"),
        (_TEST_PRICE_EXCERPT_PATH, "frozen price excerpt"),
    ]
    assert verifier_calls == 1


@pytest.mark.parametrize("schema_version", (2, None), ids=("v2", "missing"))
def test_non_null_price_binding_is_schema_v3_only(schema_version: int | None) -> None:
    schedule = _bound_price_schedule()
    if schema_version is None:
        del schedule["schema_version"]
    else:
        schedule["schema_version"] = schema_version
    _, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert any("non-null values are not supported" in reason for reason in reasons)


def test_non_null_price_binding_rejects_float_schema_v3() -> None:
    schedule = _bound_price_schedule()
    schedule["schema_version"] = 3.0
    _, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert any("non-null values are not supported" in reason for reason in reasons)


@pytest.mark.parametrize(
    ("slot_index", "block_order"),
    ((0, True), (1, 2.0)),
    ids=("bool", "float"),
)
def test_bound_price_requires_exact_integer_block_order(
    slot_index: int,
    block_order: Any,
) -> None:
    schedule = _bound_price_schedule()
    schedule["slots"][slot_index]["block_order"] = block_order
    _, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert any(
        "bound schedule block_order must be an exact integer" in reason
        for reason in reasons
    )


@pytest.mark.parametrize("stage", (True, 1.0), ids=("bool", "float"))
def test_bound_price_rejects_numeric_stage_type_confusion(stage: Any) -> None:
    schedule = _bound_price_schedule()
    manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    manifest["tasks"]["alpha"]["stage"] = 1
    for row in schedule["slots"]:
        row["stage"] = stage
    _, reasons = TOOL._validate_schedule(schedule, task_manifest=manifest)
    assert any(
        "bound schedule stage type does not match" in reason for reason in reasons
    )


def test_bound_price_accepts_exact_integer_block_order_and_stage() -> None:
    schedule = _bound_price_schedule()
    manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    manifest["tasks"]["alpha"]["stage"] = 1
    for row in schedule["slots"]:
        row["stage"] = 1
    slots, reasons = TOOL._validate_schedule(schedule, task_manifest=manifest)
    assert reasons == []
    assert [row["block_order"] for row in slots] == [1, 2]
    assert {row["stage"] for row in slots} == {1}


@pytest.mark.parametrize(
    "record",
    (
        None,
        [],
        {"path": _TEST_PRICE_SNAPSHOT_PATH},
        {"sha256": _TEST_PRICE_SNAPSHOT_SHA256},
        {
            "path": _TEST_PRICE_SNAPSHOT_PATH,
            "sha256": _TEST_PRICE_SNAPSHOT_SHA256,
            "extra": "forbidden",
        },
        {"path": "output/other.json", "sha256": _TEST_PRICE_SNAPSHOT_SHA256},
        {"path": _TEST_PRICE_SNAPSHOT_PATH, "sha256": "0" * 64},
    ),
    ids=(
        "missing",
        "non-object",
        "missing-sha",
        "missing-path",
        "extra-key",
        "wrong-path",
        "wrong-sha",
    ),
)
def test_price_snapshot_record_is_exact_and_pinned(record: Any) -> None:
    schedule = _bound_price_schedule()
    if record is None:
        del schedule["price_snapshot"]
    else:
        schedule["price_snapshot"] = record
    _, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert reasons
    assert any("price_snapshot" in reason for reason in reasons)


@pytest.mark.parametrize(
    "target", ("snapshot", "excerpt"), ids=("snapshot", "excerpt")
)
def test_bound_price_rejects_changed_snapshot_or_excerpt_bytes(
    target: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delegated = TOOL._read_frozen_repo_file

    def changed_bytes(relative_path: str, label: str) -> bytes:
        data = delegated(relative_path, label)
        if target in label:
            return data + b"changed"
        return data

    monkeypatch.setattr(TOOL, "_read_frozen_repo_file", changed_bytes)
    _, reasons = TOOL._validate_schedule(
        _bound_price_schedule(),
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert any(f"{target} bytes sha256 mismatch" in reason for reason in reasons)


@pytest.mark.parametrize(
    ("leaf", "replacement", "match"),
    (
        ("path", "output/wrong-excerpt.html", "excerpt path mismatch"),
        ("sha256", "0" * 64, "excerpt sha256 mismatch"),
        (
            "byte_length",
            _TEST_PRICE_EXCERPT_BYTES + 1,
            "excerpt byte length mismatch",
        ),
    ),
    ids=("path", "sha256", "byte-length"),
)
def test_bound_price_rejects_validated_excerpt_metadata_mismatch(
    leaf: str,
    replacement: Any,
    match: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delegated = TOOL.PRICE_SNAPSHOT.validate_price_snapshot

    def wrong_excerpt(value: Any) -> dict[str, Any]:
        validated = delegated(value)
        validated["excerpt"][leaf] = replacement
        return validated

    monkeypatch.setattr(
        TOOL.PRICE_SNAPSHOT, "validate_price_snapshot", wrong_excerpt
    )
    _, reasons = TOOL._validate_schedule(
        _bound_price_schedule(),
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert any(match in reason for reason in reasons)


def test_bound_price_rejects_validated_price_version_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delegated = TOOL.PRICE_SNAPSHOT.validate_price_snapshot

    def wrong_version(value: Any) -> dict[str, Any]:
        validated = delegated(value)
        validated["price_table_version"] = (
            "openai-pricing-standard-short-context:sha256:" + "0" * 64
        )
        return validated

    monkeypatch.setattr(
        TOOL.PRICE_SNAPSHOT, "validate_price_snapshot", wrong_version
    )
    _, reasons = TOOL._validate_schedule(
        _bound_price_schedule(),
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert "frozen price version mismatch" in reasons


@pytest.mark.parametrize(
    "kind", ("symlink", "directory"), ids=("symlink", "directory")
)
def test_frozen_repo_file_rejects_symlink_and_nonregular_targets(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "artifact"
    if kind == "symlink":
        source = tmp_path / "source"
        source.write_bytes(b"bytes")
        target.symlink_to(source)
        match = "symlink"
    else:
        target.mkdir()
        match = "not a regular file"
    monkeypatch.setattr(TOOL, "_ROOT", tmp_path)
    with pytest.raises(TOOL.ValidationError, match=match) as caught:
        TOOL._read_frozen_repo_file("artifact", "fixture artifact")
    assert caught.value.rc == TOOL.RC_ROUTING


def test_price_version_global_concentration_rejects_null_and_frozen_blocks() -> None:
    schedule = _bound_price_schedule()
    schedule["slots"].extend(
        [
            {
                **_v3_slot(
                    slot_id="s03",
                    task_id="alpha",
                    block_id="b02",
                    block_order=1,
                    arm="high",
                    requested_model="gpt-5.6-sol",
                ),
                "price_version": None,
            },
            {
                **_v3_slot(
                    slot_id="s04",
                    task_id="alpha",
                    block_id="b02",
                    block_order=2,
                    arm="high",
                    requested_model="gpt-5.6-luna",
                ),
                "price_version": None,
            },
        ]
    )
    _, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert reasons == [
        "schedule price_version concentration must be all null or all frozen"
    ]


def test_all_null_v3_schedule_ignores_unbound_price_snapshot_metadata() -> None:
    schedule = _bound_price_schedule()
    schedule["price_snapshot"] = {
        "malformed": "ignored for the legacy all-null acceptance set"
    }
    for row in schedule["slots"]:
        row["price_version"] = None
    slots, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert reasons == []
    assert {row["price_version"] for row in slots} == {None}


def test_all_null_float_schema_v3_remains_accepted() -> None:
    schedule = _bound_price_schedule()
    schedule["schema_version"] = 3.0
    for row in schedule["slots"]:
        row["price_version"] = None
    slots, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert reasons == []
    assert {row["price_version"] for row in slots} == {None}


@pytest.mark.parametrize(
    ("slot_index", "block_order"),
    ((0, True), (1, 2.0)),
    ids=("bool", "float"),
)
def test_all_null_numeric_equivalent_block_order_remains_accepted(
    slot_index: int,
    block_order: Any,
) -> None:
    schedule = _bound_price_schedule()
    schedule["slots"][slot_index]["block_order"] = block_order
    for row in schedule["slots"]:
        row["price_version"] = None
    slots, reasons = TOOL._validate_schedule(
        schedule,
        task_manifest=_synthetic_task_manifest(
            (("alpha", "POS", "positive", "alpha-finding"),)
        ),
    )
    assert reasons == []
    assert slots[slot_index]["block_order"] == block_order
    assert type(slots[slot_index]["block_order"]) is type(block_order)


@pytest.mark.parametrize("stage", (True, 1.0), ids=("bool", "float"))
def test_all_null_numeric_equivalent_stage_remains_accepted(stage: Any) -> None:
    schedule = _bound_price_schedule()
    manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    manifest["tasks"]["alpha"]["stage"] = 1
    for row in schedule["slots"]:
        row["price_version"] = None
        row["stage"] = stage
    slots, reasons = TOOL._validate_schedule(schedule, task_manifest=manifest)
    assert reasons == []
    assert {row["stage"] for row in slots} == {1}


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
    task_manifest = benchmark_snapshots["task_manifest"]
    _, source_slots = _schedule(
        tmp_path / "legacy-schedule.json",
        benchmark_snapshots,
        task_manifest=task_manifest,
    )
    source = {"slots": copy.deepcopy(source_slots)}
    slots, reasons = TOOL._validate_schedule(
        source, task_manifest=task_manifest
    )
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
    state, parent, _ = _packet_fixture(
        tmp_path, task_manifest=manifest
    )
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
    task_manifest = benchmark_snapshots["task_manifest"]
    snapshot = tmp_path / "snapshot"
    shutil.copytree(benchmark_snapshots["NEG"]["snapshot"], snapshot)
    subprocess.run(
        ["git", "-c", "protocol.file.allow=always", "fetch", str(_ROOT), TOOL.ARTIFACT_COMMIT],
        cwd=snapshot,
        check=True,
        capture_output=True,
    )
    with pytest.raises(TOOL.ValidationError, match="forbidden git object"):
        TOOL.verify_snapshot(snapshot, "NEG", task_manifest=task_manifest)


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
    expected_verification_sha256: str | None = None

    def record_successful_verification(
        path: Path,
        pin_label: str,
        *,
        expected_sha256: str | None = None,
    ) -> None:
        assert expected_sha256 == expected_verification_sha256
        real_verify(path, pin_label, expected_sha256=expected_sha256)
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
    expected_verification_sha256 = hashlib.sha256(
        verified_content
    ).hexdigest()

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


def test_find_rollout_pinned_memory_error_propagates(
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

    def raise_memory_error(
        path: Path,
        requested_label: str,
        *,
        expected_sha256: str | None = None,
    ) -> None:
        assert expected_sha256 == hashlib.sha256(content).hexdigest()
        raise MemoryError("sha verification sentinel")

    monkeypatch.setattr(TOOL, "_verify_rollout_sha", raise_memory_error)

    with pytest.raises(MemoryError, match="sha verification sentinel"):
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)


@pytest.mark.parametrize("error_type", (TypeError, AttributeError))
def test_find_rollout_pinned_verifier_contract_error_propagates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[Exception],
) -> None:
    label = "test-verifier-contract-error"
    session_id = "verifier-contract-error-target"
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

    def raise_contract_error(
        path: Path,
        requested_label: str,
        *,
        expected_sha256: str | None = None,
    ) -> None:
        assert expected_sha256 == hashlib.sha256(content).hexdigest()
        raise error_type("verifier contract sentinel")

    monkeypatch.setattr(TOOL, "_verify_rollout_sha", raise_contract_error)

    with pytest.raises(error_type, match="verifier contract sentinel"):
        TOOL._find_rollout(tmp_path, session_id, pinned_label=label)


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
    calls: list[tuple[str, str | None, str | None]] = []

    def observe(
        sessions_root: Path,
        session_id: str,
        *,
        pinned_label: str | None = None,
        pinned_sha256: str | None = None,
    ) -> Path:
        calls.append((session_id, pinned_label, pinned_sha256))
        if len(calls) == 3:
            raise RuntimeError("wiring observed")
        return tmp_path / f"{pinned_label}.jsonl"

    monkeypatch.setattr(TOOL, "_find_rollout", observe)

    with pytest.raises(RuntimeError, match="wiring observed"):
        TOOL.derive_independent_golden(
            tmp_path, tmp_path, verify_source_sha=verify_source_sha
        )
    assert calls == [
        (
            TOOL.SESSION_IDS[label],
            label,
            TOOL.ROLLOUT_SHA256[label],
        )
        for label in ("author", "fix1", "fix2")
    ]


def test_external_manifest_golden_does_not_read_module_session_or_rollout_pins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    auxiliary = manifest["shared_provenance"]["auxiliary_sessions"]
    for index, label in enumerate(("author", "fix1", "fix2"), 1):
        auxiliary[label] = {
            "session_id": f"external-{label}",
            "rollout_sha256": str(index) * 64,
        }
    monkeypatch.setattr(
        TOOL,
        "SESSION_IDS",
        {label: f"poison-{label}" for label in ("author", "fix1", "fix2")},
    )
    monkeypatch.setattr(
        TOOL,
        "ROLLOUT_SHA256",
        {label: "f" * 64 for label in ("author", "fix1", "fix2")},
    )
    calls: list[tuple[str, str | None, str | None]] = []

    def observe(
        sessions_root: Path,
        session_id: str,
        *,
        pinned_label: str | None = None,
        pinned_sha256: str | None = None,
    ) -> Path:
        calls.append((session_id, pinned_label, pinned_sha256))
        if len(calls) == 3:
            raise RuntimeError("wiring observed")
        return tmp_path / f"{pinned_label}.jsonl"

    monkeypatch.setattr(TOOL, "_find_rollout", observe)
    with pytest.raises(RuntimeError, match="wiring observed"):
        TOOL.derive_independent_golden(
            tmp_path,
            tmp_path,
            task_manifest=manifest,
        )
    assert calls == [
        (
            auxiliary[label]["session_id"],
            label,
            auxiliary[label]["rollout_sha256"],
        )
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
    calls: list[tuple[str, str | None, str | None]] = []

    def observe(
        sessions_root: Path,
        session_id: str,
        *,
        pinned_label: str | None = None,
        pinned_sha256: str | None = None,
    ) -> Path:
        calls.append((session_id, pinned_label, pinned_sha256))
        raise RuntimeError("wiring observed")

    monkeypatch.setattr(TOOL, "_find_rollout", observe)

    with pytest.raises(RuntimeError, match="wiring observed"):
        TOOL.render_prompt(
            tmp_path,
            case,
            tmp_path / "new-root",
            verify_source=verify_source,
        )
    assert calls == [
        (
            TOOL.SESSION_IDS[case],
            case,
            TOOL.ROLLOUT_SHA256[case],
        )
    ]


def test_m20_render_prompt_binds_external_task_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    task = manifest["tasks"]["alpha"]
    task["provenance"] = {
        **task["provenance"],
        "session_id": "external-prompt-session",
        "rollout_sha256": "7" * 64,
    }
    task["snapshot"]["artifact_names"] = []
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_bytes(b"external rollout bytes\n")
    observed: list[tuple[str, str | None, str | None]] = []

    def find_external(
        sessions_root: Path,
        session_id: str,
        *,
        pinned_label: str | None = None,
        pinned_sha256: str | None = None,
    ) -> Path:
        observed.append((session_id, pinned_label, pinned_sha256))
        return rollout

    monkeypatch.setattr(TOOL, "_find_rollout", find_external)
    monkeypatch.setattr(TOOL, "extract_user_message", lambda _: "prompt")
    snapshot_oracle = {
        "task_manifest_sha256": TOOL._task_manifest_sha256(manifest),
        "case": "legacy-alpha",
    }
    data, receipt = TOOL.render_prompt(
        tmp_path,
        "alpha",
        tmp_path / "neutral-root",
        verify_source=False,
        task_manifest=manifest,
        snapshot_oracle=snapshot_oracle,
    )
    assert data == b"prompt"
    assert observed == [
        ("external-prompt-session", "legacy-alpha", "7" * 64)
    ]
    assert receipt["task_manifest_sha256"] == TOOL._task_manifest_sha256(
        manifest
    )
    assert receipt["snapshot_manifest_sha256"] == TOOL._sha256(
        TOOL._canonical_bytes(snapshot_oracle)
    )

    with pytest.raises(
        TOOL.ValidationError,
        match="requires a snapshot oracle binding",
    ):
        TOOL.render_prompt(
            tmp_path,
            "alpha",
            tmp_path / "neutral-root",
            verify_source=False,
            task_manifest=manifest,
        )
    with pytest.raises(
        TOOL.ValidationError,
        match="prompt snapshot oracle task_manifest_sha256 mismatch",
    ):
        TOOL.render_prompt(
            tmp_path,
            "alpha",
            tmp_path / "neutral-root",
            verify_source=False,
            task_manifest=manifest,
            snapshot_oracle={
                "task_manifest_sha256": TOOL._task_manifest_sha256(),
                "case": "legacy-alpha",
            },
        )


@pytest.mark.parametrize("replacement_count", [0, 9, 10])
def test_prompt_replacement_count_zero_expected_and_excess(
    replacement_count: int,
    tmp_path: Path,
) -> None:
    canonical_message = _synthetic_benchmark_message("POS")
    if replacement_count == 0:
        message = canonical_message.replace(TOOL.OLD_ROOT, "/neutral-old-root")
    elif replacement_count == 10:
        message = canonical_message + "\n" + TOOL.OLD_ROOT
    else:
        message = canonical_message
    sessions_root = tmp_path / "sessions"
    session_id = "00000000-0000-4000-8000-000000000181"
    _, rollout_sha256 = _write_synthetic_benchmark_rollout(
        sessions_root,
        session_id,
        message,
    )
    task_manifest = copy.deepcopy(TOOL.TASK_MANIFEST)
    provenance = task_manifest["tasks"]["POS"]["provenance"]
    source = message.encode("utf-8")
    provenance["session_id"] = session_id
    provenance["rollout_sha256"] = rollout_sha256
    provenance["prompt_source"].update(
        {
            "sha256": TOOL._sha256(source),
            "chars": len(message),
            "bytes": len(source),
        }
    )
    snapshot_oracle = {
        "task_manifest_sha256": TOOL._task_manifest_sha256(task_manifest),
        "case": "POS",
    }
    if replacement_count == TOOL.PROMPT_SOURCE["POS"]["replacements"]:
        _, receipt = TOOL.render_prompt(
            sessions_root,
            "POS",
            tmp_path / "neutral-root",
            verify_source=True,
            task_manifest=task_manifest,
            snapshot_oracle=snapshot_oracle,
        )
        assert receipt["replacement_count"] == 9
    else:
        with pytest.raises(TOOL.ValidationError, match="replacement count mismatch"):
            TOOL.render_prompt(
                sessions_root,
                "POS",
                tmp_path / "neutral-root",
                verify_source=True,
                task_manifest=task_manifest,
                snapshot_oracle=snapshot_oracle,
            )


def test_real_rollout_collector_golden_is_source_bound() -> None:
    real_rollout = (
        TOOL._sessions_default()
        / "2026/07/29/"
        "rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl"
    )
    rollout_available = real_rollout.is_file()
    if rollout_available:
        assert TOOL.ROLLOUT_SHA256["POS"] == hashlib.sha256(
            real_rollout.read_bytes()
        ).hexdigest()
    assert hashlib.sha256(_REAL_TOKEN_SLICE.encode()).hexdigest() == _REAL_TOKEN_SLICE_SHA
    if rollout_available:
        source_line = real_rollout.read_text(encoding="utf-8").splitlines(
            keepends=True
        )[15]
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


def test_material_report_certification_scope_is_exact_on_all_return_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = {
        "certification_subject": "material-report",
        "certified_entrypoints": ["verify", "aggregate"],
        "certified_report_fields": ["valid"],
        "uncertified_artifact_universe": (
            "adjudication_intermediate_artifacts"
        ),
        "uncertified_artifact_kinds": [
            "packet",
            "packet_state",
            "verdict_log",
            "verdict_freeze",
            "revealed_map",
        ],
        "material_packet_requirement": (
            "mapped_final_run_snapshot_evidence_replayed"
        ),
        "closed_world": True,
    }
    manifest = _canonical(tmp_path / "manifest.json", {})

    missing_sessions, missing_rc = TOOL.verify_manifest(manifest)
    assert missing_rc == TOOL.RC_AGGREGATE
    assert missing_sessions["certification_scope"] == expected

    with monkeypatch.context() as aggregate_path:
        aggregate_path.setattr(
            TOOL,
            "_replay_manifest",
            lambda *args, **kwargs: ([], [], {}, []),
        )
        aggregated, aggregated_rc = TOOL.verify_manifest(
            manifest, tmp_path / "sessions"
        )
    assert aggregated_rc == 0
    assert aggregated["valid"] is True
    assert aggregated["certification_scope"] == expected

    def fail_replay(*args: Any, **kwargs: Any) -> None:
        raise TOOL.ValidationError("validation-path", TOOL.RC_AGGREGATE)

    with monkeypatch.context() as validation_path:
        validation_path.setattr(TOOL, "_replay_manifest", fail_replay)
        validation_failed, validation_rc = TOOL.verify_manifest(
            manifest, tmp_path / "sessions"
        )
    assert validation_rc == TOOL.RC_AGGREGATE
    assert validation_failed["certification_scope"] == expected

    direct = TOOL._aggregate_verified(manifest, [], [], {}, [])
    assert direct["valid"] is True
    assert "certification_scope" not in direct
    assert missing_sessions["certification_scope"] is not aggregated[
        "certification_scope"
    ]
    assert aggregated["certification_scope"] is not validation_failed[
        "certification_scope"
    ]
    missing_sessions["certification_scope"]["certified_entrypoints"].append(
        "mutated"
    )
    fresh, _ = TOOL.verify_manifest(manifest)
    assert fresh["certification_scope"] == expected


def test_certification_scope_closes_adjudication_descriptor_universe() -> None:
    module = ast.parse(_TOOL_PATH.read_text(encoding="utf-8"), _TOOL_PATH.name)
    functions = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_load_adjudication"
    ]
    assert len(functions) == 1
    artifact_calls = [
        node
        for node in ast.walk(functions[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_artifact_path"
    ]
    descriptor_keys: set[str] = set()
    malformed_calls: list[int] = []
    for call in artifact_calls:
        descriptor = call.args[1] if len(call.args) >= 2 else None
        if not (
            isinstance(descriptor, ast.Call)
            and isinstance(descriptor.func, ast.Attribute)
            and isinstance(descriptor.func.value, ast.Name)
            and descriptor.func.value.id == "manifest"
            and descriptor.func.attr == "get"
            and len(descriptor.args) == 1
            and isinstance(descriptor.args[0], ast.Constant)
            and isinstance(descriptor.args[0].value, str)
        ):
            malformed_calls.append(call.lineno)
            continue
        descriptor_keys.add(descriptor.args[0].value)

    assert artifact_calls
    assert malformed_calls == []
    scope = TOOL._certification_scope()
    assert scope["uncertified_artifact_universe"] == (
        "adjudication_intermediate_artifacts"
    )
    declared_descriptor_kinds = set(scope["uncertified_artifact_kinds"]) - {
        "packet"
    }
    assert descriptor_keys == declared_descriptor_kinds


def test_verify_replays_complete_fake_codex_experiment(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    manifest, run_root = _full_manifest(
        tmp_path,
        benchmark_snapshots,
        monkeypatch,
        memoize_construction_snapshots=True,
    )
    result, rc = TOOL.verify_manifest(
        manifest, run_root, task_manifest=task_manifest
    )
    assert rc == 0
    assert result["valid"] is True
    assert result["task_manifest_sha256"] == TOOL._task_manifest_sha256(
        task_manifest
    )
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
    assert result["certification_scope"] == {
        "certification_subject": "material-report",
        "certified_entrypoints": ["verify", "aggregate"],
        "certified_report_fields": ["valid"],
        "uncertified_artifact_universe": (
            "adjudication_intermediate_artifacts"
        ),
        "uncertified_artifact_kinds": [
            "packet",
            "packet_state",
            "verdict_log",
            "verdict_freeze",
            "revealed_map",
        ],
        "material_packet_requirement": (
            "mapped_final_run_snapshot_evidence_replayed"
        ),
        "closed_world": True,
    }
    assert result["decision"]["row"] == "POS_PRIMARY"
    first_rollout = next(run_root.rglob("rollout-*.jsonl"))
    first_meta = first_rollout.read_text(encoding="utf-8").splitlines()[0]
    (run_root / "rollout-extra.jsonl").write_text(
        first_meta + "\n", encoding="utf-8"
    )
    tampered, tampered_rc = TOOL.verify_manifest(
        manifest, run_root, task_manifest=task_manifest
    )
    assert tampered_rc == TOOL.RC_AGGREGATE
    assert "generated session row set mismatch" in "\n".join(
        tampered["failure_reasons"]
    )


def test_material_replay_rejects_task_manifest_exchange_at_digest_consumers(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    manifest_path, run_root = _full_manifest(
        tmp_path,
        benchmark_snapshots,
        monkeypatch,
        memoize_construction_snapshots=True,
    )
    alternate = copy.deepcopy(task_manifest)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    result, rc = TOOL.verify_manifest(
        manifest_path,
        run_root,
        task_manifest=alternate,
    )
    assert rc == TOOL.RC_AGGREGATE
    assert result["valid"] is False
    assert result["failure_reasons"] == [
        "material manifest task_manifest_sha256 mismatch"
    ]


def test_material_replay_rejects_schedule_task_manifest_exchange_at_digest_consumers(
    tmp_path: Path,
) -> None:
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    schedule = _canonical(
        tmp_path / "schedule.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(alternate),
            "slots": [],
        },
    )
    material = _canonical(
        tmp_path / "material.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "schedule": _descriptor(schedule, tmp_path),
        },
    )
    result, rc = TOOL.verify_manifest(material, tmp_path / "sessions")
    assert rc == TOOL.RC_AGGREGATE
    assert result["failure_reasons"] == [
        "schedule task_manifest_sha256 mismatch"
    ]


def test_material_replay_rejects_ledger_task_manifest_exchange_at_digest_consumers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root = tmp_path / "run"
    attempts_root = run_root / "attempts"
    attempts_root.mkdir(parents=True)
    schedule = _canonical(
        run_root / "schedule.json",
        {"task_manifest_sha256": TOOL._task_manifest_sha256(), "slots": []},
    )
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    ledger = run_root / "attempt-ledger.jsonl"
    TOOL._append_jsonl(
        ledger,
        {
            "phase": "reserved",
            "task_manifest_sha256": TOOL._task_manifest_sha256(alternate),
        },
    )
    material = _canonical(
        tmp_path / "material.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "schedule": _descriptor(schedule, tmp_path),
            "schedule_sha256": TOOL._sha256(schedule.read_bytes()),
            "attempts": [],
            "run_root": "run",
            "attempts_root": "run/attempts",
            "attempt_ledger": _descriptor(ledger, tmp_path),
            "max_schedule_gap_ms": TOOL.MAX_SCHEDULE_GAP_MS,
            "max_inter_block_gap_ms": TOOL.MAX_INTER_BLOCK_GAP_MS,
            "judgments": [],
        },
    )
    monkeypatch.setattr(
        TOOL,
        "_validate_schedule",
        lambda *args, **kwargs: (TOOL._ValidatedScheduleSlots(), []),
    )
    _, _, _, reasons = TOOL._replay_manifest(material, tmp_path / "sessions")
    assert "attempt ledger task_manifest_sha256 mismatch" in reasons


def test_bound_price_reaches_supervisor_replay_verify_and_aggregate_consumers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt = tmp_path / "supervisor-prompt.txt"
    prompt.write_bytes(b"bound supervisor prompt")
    snapshot = tmp_path / "supervisor-snapshot"
    snapshot.mkdir()
    submodule_sha256 = TOOL._submodule_manifest_sha256([])
    supervisor_oracles = {
        case: {
            "case": case,
            "snapshot": os.fspath(snapshot.resolve()),
            "submodules": [],
            "submodule_manifest_sha256": submodule_sha256,
        }
        for case in ("POS", "NEG")
    }
    supervisor_slots: list[dict[str, Any]] = []
    slot_number = 0
    for case, block_count in (("POS", 3), ("NEG", 2)):
        for block in range(block_count):
            order = ("max", "high") if block % 2 == 0 else ("high", "max")
            block_id = f"b{len(supervisor_slots) // 2 + 1:02d}"
            for block_order, arm in enumerate(order, 1):
                slot_number += 1
                supervisor_slots.append(
                    {
                        "slot_id": f"s{slot_number:02d}",
                        "case": case,
                        "arm": arm,
                        "block_id": block_id,
                        "block_order": block_order,
                        "cache_condition": None,
                        "price_version": _TEST_PRICE_VERSION,
                        "prompt_sha256": TOOL._sha256(prompt.read_bytes()),
                        "snapshot_manifest_sha256": TOOL._sha256(
                            TOOL._canonical_bytes(supervisor_oracles[case])
                        ),
                        "submodule_manifest_sha256": submodule_sha256,
                    }
                )
    supervisor_schedule = _canonical(
        tmp_path / "supervisor-schedule.json",
        {
            "schema_version": 3,
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "price_snapshot": {
                "path": _TEST_PRICE_SNAPSHOT_PATH,
                "sha256": _TEST_PRICE_SNAPSHOT_SHA256,
            },
            "slots": supervisor_slots,
        },
    )
    clock = 0

    def complete_supervisor_slot(**kwargs: Any) -> dict[str, Any]:
        nonlocal clock
        clock += 2_000_000
        slot = kwargs["slot"]
        return {
            "schema_version": TOOL.SCHEMA_VERSION,
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                kwargs["task_manifest"]
            ),
            "phase": "completed",
            "run_id": kwargs["run_id"],
            "slot_id": slot["slot_id"],
            "block_id": slot["block_id"],
            "block_order": slot["block_order"],
            "attempt": kwargs["attempt"],
            "parent_run_id": kwargs["parent_run_id"],
            "case": slot["case"],
            "arm": slot["arm"],
            "process_start_monotonic_ns": clock,
            "process_exit_monotonic_ns": clock + 1_000_000,
            "process_wall_ms": 1,
            "exit_code": 0,
            "snapshot_unchanged": True,
        }

    monkeypatch.setattr(
        TOOL,
        "verify_snapshot",
        lambda _snapshot, case, **kwargs: copy.deepcopy(
            supervisor_oracles[case]
        ),
    )
    monkeypatch.setattr(TOOL, "_supervise_one", complete_supervisor_slot)
    supervised = TOOL.supervise_pair(
        schedule_path=supervisor_schedule,
        run_root=tmp_path / "supervisor-run",
        block_id="b01",
        attempt=1,
        snapshot=snapshot,
        prompt=prompt,
        config_source=tmp_path / "unused-config",
        auth_source=tmp_path / "unused-auth",
        codex_binary=tmp_path / "unused-codex",
        bwrap_binary=tmp_path / "unused-bwrap",
        dry_run=True,
    )
    assert len(supervised["runs"]) == 2

    replay_root = tmp_path / "replay-run"
    attempts_root = replay_root / "attempts"
    sessions_root = tmp_path / "sessions"
    attempts_root.mkdir(parents=True)
    sessions_root.mkdir()
    task_manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    replay_schedule = _bound_price_schedule()
    replay_schedule["task_manifest_sha256"] = TOOL._task_manifest_sha256(
        task_manifest
    )
    replay_prompt = tmp_path / "replay-prompt.txt"
    replay_prompt.write_bytes(b"bound replay prompt")
    replay_snapshot = tmp_path / "replay-snapshot"
    replay_snapshot.mkdir()
    replay_oracle = {
        "snapshot": os.fspath(replay_snapshot.resolve()),
        "submodule_manifest_sha256": "c" * 64,
    }
    oracle_path = _canonical(tmp_path / "replay-oracle.json", replay_oracle)
    oracle_sha256 = TOOL._sha256(oracle_path.read_bytes())
    for slot in replay_schedule["slots"]:
        slot["case"] = "legacy-alpha"
        slot["prompt_sha256"] = TOOL._sha256(replay_prompt.read_bytes())
        slot["snapshot_manifest_sha256"] = oracle_sha256
    replay_schedule_path = _canonical(
        replay_root / "schedule.json", replay_schedule
    )
    replay_schedule_sha256 = TOOL._sha256(replay_schedule_path.read_bytes())
    ledger_path = _canonical(replay_root / "attempt-ledger.jsonl", {})
    attempt_descriptors: list[dict[str, Any]] = []
    replay_receipts: dict[str, dict[str, Any]] = {}
    replay_scores: dict[str, dict[str, Any]] = {}
    supervisor_completions: list[dict[str, Any]] = []
    for index, slot in enumerate(replay_schedule["slots"], 1):
        run_id = f"r{index:02d}"
        attempt_root = attempts_root / run_id
        attempt_root.mkdir()
        events = _canonical(attempt_root / "events.jsonl", {"events": index})
        done = _canonical(attempt_root / "done.json", {"done": index})
        output = attempt_root / "answer.md"
        output.write_text(_long_output(), encoding="utf-8")
        rollout = _canonical(
            sessions_root / f"rollout-{run_id}.jsonl", {"rollout": index}
        )
        launch = _canonical(
            attempt_root / "launch.json",
            {
                "run_id": run_id,
                "slot_id": slot["slot_id"],
                "attempt": 1,
                "parent_run_id": None,
                "case": slot["case"],
                "arm": slot["arm"],
                "requested_model": slot["requested_model"],
                "schedule_sha256": replay_schedule_sha256,
                "prompt": {"sha256": slot["prompt_sha256"]},
                "snapshot_oracle": {
                    "sha256": slot["snapshot_manifest_sha256"]
                },
                "treatment_identity_sha256": "bound-price-identity",
            },
        )
        receipt = {
            "run_id": run_id,
            "rollout_path": os.fspath(rollout.resolve()),
            "wall_clock_ms": 0,
            "failure_reasons": [],
            "failure_class": None,
            "valid": True,
            "input_tokens": 1,
            "cached_input_tokens": 0,
            "output_tokens": 1,
            "reasoning_output_tokens": 0,
            "cli_reported": 2,
            "model_calls": 1,
            "token_usage_observations": _token_usage_observations(),
            "turn_protocol": "single-turn-required",
            "rate_limited": False,
            "retry": False,
            "compaction_observed": False,
        }
        score = {
            "valid": True,
            "r1_candidate": True,
            "decision": "NO-GO",
        }
        receipt_path = _canonical(attempt_root / "receipt.json", receipt)
        score_path = _canonical(attempt_root / "score.json", score)
        replay_receipts[run_id] = receipt
        replay_scores[run_id] = score
        supervisor_completions.append(
            {
                "run_id": run_id,
                "process_started": True,
                "process_wall_ms": 0,
            }
        )
        attempt_descriptors.append(
            {
                "run_id": run_id,
                "slot_id": slot["slot_id"],
                "attempt": 1,
                "parent_run_id": None,
                "launch_receipt": _descriptor(launch, tmp_path),
                "events": _descriptor(events, tmp_path),
                "done": _descriptor(done, tmp_path),
                "prompt": _descriptor(replay_prompt, tmp_path),
                "output": _descriptor(output, tmp_path),
                "snapshot_oracle": _descriptor(oracle_path, tmp_path),
                "snapshot_after": _descriptor(oracle_path, tmp_path),
                "rollout": _descriptor(rollout, tmp_path),
                "receipt": _descriptor(receipt_path, tmp_path),
                "score": _descriptor(score_path, tmp_path),
            }
        )
    manifest_path = _canonical(
        tmp_path / "replay-manifest.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                task_manifest
            ),
            "run_root": replay_root.name,
            "attempts_root": f"{replay_root.name}/attempts",
            "attempt_ledger": _descriptor(ledger_path, tmp_path),
            "max_schedule_gap_ms": TOOL.MAX_SCHEDULE_GAP_MS,
            "max_inter_block_gap_ms": TOOL.MAX_INTER_BLOCK_GAP_MS,
            "schedule": _descriptor(replay_schedule_path, tmp_path),
            "schedule_sha256": replay_schedule_sha256,
            "attempts": attempt_descriptors,
        },
    )

    monkeypatch.setattr(
        TOOL,
        "_validate_supervisor_ledger",
        lambda *args, **kwargs: (supervisor_completions, []),
    )
    monkeypatch.setattr(
        TOOL,
        "verify_snapshot",
        lambda _snapshot, _case, **kwargs: copy.deepcopy(replay_oracle),
    )
    monkeypatch.setattr(
        TOOL,
        "collect_run",
        lambda **kwargs: (copy.deepcopy(replay_receipts[kwargs["run_id"]]), 0),
    )
    monkeypatch.setattr(
        TOOL,
        "score_run",
        lambda _path, run_id: (copy.deepcopy(replay_scores[run_id]), 0),
    )
    verdicts = {
        slot["slot_id"]: {
            "oracle_kind": task_manifest["tasks"][
                slot["benchmark_task_id"]
            ]["oracle_kind"],
            "r1_detected": True,
            "findings": [],
            "reader_agreement": True,
        }
        for slot in replay_schedule["slots"]
    }
    monkeypatch.setattr(
        TOOL,
        "_load_adjudication",
        lambda *args, **kwargs: (copy.deepcopy(verdicts), []),
    )

    result, rc = TOOL.verify_manifest(
        manifest_path,
        sessions_root,
        task_manifest=task_manifest,
    )
    assert rc == 0
    assert result["valid"] is True
    assert result["experiment_complete"] is True
    assert len(result["resource_ledger"]) == 2
    assert {
        row["price_version"] for row in result["resource_ledger"]
    } == {_TEST_PRICE_VERSION}
    assert {
        row["cache_condition"] for row in result["resource_ledger"]
    } == {None}
    assert {
        row["price_version"]
        for row in result["primary_judgment_axis_ledger"]
    } == {_TEST_PRICE_VERSION}
    aggregated, aggregate_rc = TOOL.aggregate_manifest(
        manifest_path,
        sessions_root=sessions_root,
        task_manifest=task_manifest,
    )
    assert aggregate_rc == 0
    assert aggregated["resource_ledger"] == result["resource_ledger"]


def test_replay_forwards_only_successful_snapshot_evidence_to_adjudication(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    manifest_path, run_root = _full_manifest(
        tmp_path,
        benchmark_snapshots,
        monkeypatch,
        memoize_construction_snapshots=True,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schedule = json.loads((run_root / "schedule.json").read_text(encoding="utf-8"))
    case_by_slot = {
        row["slot_id"]: row["case"] for row in schedule["slots"]
    }
    expected_verified = {
        row["run_id"]
        for row in manifest["attempts"]
        if case_by_slot[row["slot_id"]] == "POS"
    }
    expected_mismatched = {
        row["run_id"]
        for row in manifest["attempts"]
        if case_by_slot[row["slot_id"]] == "NEG"
    }
    verified_attempts = [
        row
        for row in manifest["attempts"]
        if row["run_id"] in expected_verified
    ]
    for row in verified_attempts[1:]:
        row["snapshot_oracle"] = copy.deepcopy(
            verified_attempts[0]["snapshot_oracle"]
        )
    mismatched_attempts = [
        row
        for row in manifest["attempts"]
        if row["run_id"] in expected_mismatched
    ]
    first_mismatch, second_mismatch = mismatched_attempts[:2]
    second_mismatch["snapshot_oracle"] = copy.deepcopy(
        first_mismatch["snapshot_oracle"]
    )
    assert second_mismatch["snapshot_oracle"] == first_mismatch[
        "snapshot_oracle"
    ]
    _canonical(manifest_path, manifest)
    shared_oracle_path = Path(first_mismatch["snapshot_oracle"]["path"])
    if not shared_oracle_path.is_absolute():
        shared_oracle_path = manifest_path.parent / shared_oracle_path
    shared_oracle_path = shared_oracle_path.resolve()
    captured: set[str] = set()
    active_oracle_path: Path | None = None
    shared_mismatch_replay_calls = 0
    original_verify_snapshot = TOOL.verify_snapshot
    original_load_adjudication = TOOL._load_adjudication
    original_artifact_path = TOOL._artifact_path

    def track_artifact_path(
        manifest_path: Path,
        descriptor: Any,
        label: str,
        *,
        root: Path | None = None,
    ) -> Path:
        nonlocal active_oracle_path
        path = original_artifact_path(
            manifest_path, descriptor, label, root=root
        )
        if label.endswith(":snapshot_oracle"):
            active_oracle_path = path.resolve()
        return path

    def selective_verify_snapshot(
        snapshot: Path,
        case: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        nonlocal shared_mismatch_replay_calls
        replay = original_verify_snapshot(snapshot, case, **kwargs)
        if active_oracle_path == shared_oracle_path:
            shared_mismatch_replay_calls += 1
        if case == "NEG":
            return {**replay, "forced_canonical_mismatch": True}
        return replay

    def capture_snapshot_evidence(
        manifest_path: Path,
        manifest: dict[str, Any],
        slots: list[dict[str, Any]],
        final_attempts: dict[str, dict[str, Any]],
        *,
        snapshot_verified_run_ids: set[str],
        task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
    ) -> tuple[dict[str, dict[str, Any]], list[str]]:
        captured.update(snapshot_verified_run_ids)
        return original_load_adjudication(
            manifest_path,
            manifest,
            slots,
            final_attempts,
            snapshot_verified_run_ids=snapshot_verified_run_ids,
            task_manifest=task_manifest,
        )

    monkeypatch.setattr(TOOL, "_artifact_path", track_artifact_path)
    monkeypatch.setattr(TOOL, "verify_snapshot", selective_verify_snapshot)
    monkeypatch.setattr(
        TOOL, "_load_adjudication", capture_snapshot_evidence
    )
    _, _, _, reasons = TOOL._replay_manifest(
        manifest_path,
        run_root,
        task_manifest=task_manifest,
    )

    assert captured == expected_verified
    assert shared_mismatch_replay_calls == 2
    for run_id in expected_mismatched:
        assert f"{run_id}: snapshot oracle replay mismatch" in reasons
    for run_id in expected_verified:
        assert f"{run_id}: snapshot oracle replay mismatch" not in reasons


def test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    manifest_path, run_root = _full_manifest(
        tmp_path,
        benchmark_snapshots,
        monkeypatch,
        memoize_construction_snapshots=True,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schedule = json.loads((run_root / "schedule.json").read_text(encoding="utf-8"))
    case_by_slot = {
        row["slot_id"]: row["case"] for row in schedule["slots"]
    }
    shared_case = schedule["slots"][0]["case"]
    shared_attempts = [
        row
        for row in manifest["attempts"]
        if case_by_slot[row["slot_id"]] == shared_case
    ]
    first, second = shared_attempts[:2]
    shared_oracles_by_case: dict[str, dict[str, Any]] = {}
    for row in manifest["attempts"]:
        case = case_by_slot[row["slot_id"]]
        if case not in shared_oracles_by_case:
            shared_oracles_by_case[case] = copy.deepcopy(
                row["snapshot_oracle"]
            )
        row["snapshot_oracle"] = copy.deepcopy(
            shared_oracles_by_case[case]
        )
    assert second["snapshot_oracle"] == first["snapshot_oracle"]
    _canonical(manifest_path, manifest)
    shared_oracle_path = Path(first["snapshot_oracle"]["path"])
    if not shared_oracle_path.is_absolute():
        shared_oracle_path = manifest_path.parent / shared_oracle_path
    shared_oracle_path = shared_oracle_path.resolve()
    active_oracle_path: Path | None = None
    shared_replay_calls = 0
    original_artifact_path = TOOL._artifact_path
    original_verify_snapshot = TOOL.verify_snapshot

    def track_artifact_path(
        manifest_path: Path,
        descriptor: Any,
        label: str,
        *,
        root: Path | None = None,
    ) -> Path:
        nonlocal active_oracle_path
        path = original_artifact_path(
            manifest_path, descriptor, label, root=root
        )
        if label.endswith(":snapshot_oracle"):
            active_oracle_path = path.resolve()
        return path

    def count_verify_snapshot(
        snapshot: Path,
        case: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        nonlocal shared_replay_calls
        if active_oracle_path == shared_oracle_path:
            shared_replay_calls += 1
        return original_verify_snapshot(snapshot, case, **kwargs)

    monkeypatch.setattr(TOOL, "_artifact_path", track_artifact_path)
    monkeypatch.setattr(TOOL, "verify_snapshot", count_verify_snapshot)

    accepted, accepted_rc = TOOL.verify_manifest(
        manifest_path,
        run_root,
        task_manifest=task_manifest,
    )
    assert accepted_rc == 0
    assert accepted["valid"] is True
    assert shared_replay_calls == 1
    accepted_reasons = set(accepted.get("failure_reasons", []))

    after_path = Path(second["snapshot_after"]["path"])
    if not after_path.is_absolute():
        after_path = tmp_path / after_path
    after_value = json.loads(after_path.read_text(encoding="utf-8"))
    after_value["forced_post_mismatch"] = True
    _canonical(after_path, after_value)
    second["snapshot_after"] = _descriptor(after_path, tmp_path)
    _canonical(manifest_path, manifest)

    shared_replay_calls = 0
    rejected, rejected_rc = TOOL.verify_manifest(
        manifest_path,
        run_root,
        task_manifest=task_manifest,
    )
    expected_reason = (
        f"{second['run_id']}: pre/post snapshot oracle mismatch"
    )
    assert rejected_rc == TOOL.RC_AGGREGATE
    assert rejected["valid"] is False
    assert rejected["failure_reasons"].count(expected_reason) == 1
    assert shared_replay_calls == 1
    revealed_path = Path(manifest["revealed_map"]["path"])
    if not revealed_path.is_absolute():
        revealed_path = manifest_path.parent / revealed_path
    revealed = json.loads(revealed_path.read_text(encoding="utf-8"))
    packet_id = next(
        row["packet_id"]
        for row in revealed["mapping"]
        if row["run_id"] == second["run_id"]
    )
    membership_reason = (
        f"{packet_id}: material packet source run lacks replayed "
        f"snapshot evidence: {second['run_id']}"
    )
    # This one tamper adds exactly two reasons: the binding failure and its
    # deliberately redundant material-packet membership failure.
    assert set(rejected["failure_reasons"]) - accepted_reasons == {
        expected_reason,
        membership_reason,
    }


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
    schedule_path = _canonical(
        run_root / "schedule.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "slots": [slot],
        },
    )
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
        "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
    monkeypatch.setattr(
        TOOL,
        "verify_snapshot",
        lambda actual, case, **kwargs: oracle_value,
    )
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
    monkeypatch.setattr(
        TOOL, "build_snapshot", lambda *args, **kwargs: {"ok": True}
    )
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


def test_task_manifest_cli_option_surface_is_closed() -> None:
    root_parser = TOOL._parser()
    subparsers_action = next(
        action
        for action in root_parser._actions
        if isinstance(action, TOOL.argparse._SubParsersAction)
    )
    option_verbs = {
        name
        for name, parser in subparsers_action.choices.items()
        if any(
            "--task-manifest" in action.option_strings
            for action in parser._actions
        )
    }
    profile_verbs = {
        name
        for name, parser in subparsers_action.choices.items()
        if any(
            "--task-manifest-profile" in action.option_strings
            for action in parser._actions
        )
    }
    assert option_verbs == {
        "build-snapshot",
        "render-prompt",
        "collect-run",
        "supervise-pair",
        "aggregate",
        "verify",
        "make-packets",
        "append-verdicts",
        "freeze-verdicts",
        "reveal-mapping",
    }
    assert "verify-snapshot" not in option_verbs
    assert profile_verbs == option_verbs
    assert not option_verbs & {
        "freeze-stage2-plan-replayer",
        "replay-stage2-plan",
        "freeze-stage5-author-replayer",
        "validate-stage5-author-application",
        "validate-stage5-downstream-receipt",
        "score-run",
    }


def test_m19_verify_snapshot_rejects_task_manifest_option_by_fallback(
    tmp_path: Path,
) -> None:
    with pytest.raises(SystemExit) as caught:
        TOOL._parser().parse_args(
            [
                "verify-snapshot",
                "--snapshot",
                os.fspath(tmp_path / "snapshot"),
                "--case",
                "POS",
                "--task-manifest",
                os.fspath(tmp_path / "external.json"),
            ]
        )
    assert caught.value.code == 2


def test_m16_cli_external_manifest_is_loaded_before_alias_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    manifest_path = _canonical(tmp_path / "external-manifest.json", manifest)
    path = os.fspath(tmp_path / "artifact")
    invocations = {
        "build-snapshot": (
            "build_snapshot",
            ["--snapshot", path, "--benchmark-task-id", "alpha"],
        ),
        "render-prompt": (
            "render_prompt",
            ["--benchmark-task-id", "alpha", "--new-root", path],
        ),
        "collect-run": (
            "collect_run",
            [
                "--run-id", "r01", "--benchmark-task-id", "alpha",
                "--requested-effort", "max", "--events", path,
                "--done", path, "--output", path, "--prompt", path,
                "--sessions-root", path, "--snapshot", path,
                "--launch-receipt", path,
            ],
        ),
        "supervise-pair": (
            "supervise_pair",
            [
                "--schedule", path, "--run-root", path,
                "--block-id", "b01", "--attempt", "1",
                "--snapshot", path, "--prompt", path,
                "--config-source", path, "--auth-source", path,
                "--codex-bin", path,
            ],
        ),
        "aggregate": (
            "aggregate_manifest",
            ["--manifest", path, "--sessions-root", path],
        ),
        "verify": (
            "verify_manifest",
            ["--manifest", path, "--sessions-root", path],
        ),
        "make-packets": (
            "make_packets",
            ["--manifest", path, "--packet-dir", path, "--custodian-root", path],
        ),
        "append-verdicts": (
            "append_verdicts",
            [
                "--packet-state", path, "--verdict-log", path,
                "--reader", "parent", "--input", path,
            ],
        ),
        "freeze-verdicts": (
            "freeze_verdicts",
            ["--packet-state", path, "--verdict-log", path, "--output", path],
        ),
        "reveal-mapping": (
            "reveal_mapping",
            [
                "--packet-state", path, "--custodian-root", path,
                "--verdict-log", path, "--verdict-freeze", path,
                "--output", path,
            ],
        ),
    }
    for verb, (function_name, arguments) in invocations.items():
        def observe_forwarding(
            *args: Any,
            _verb: str = verb,
            **kwargs: Any,
        ) -> Any:
            assert kwargs["task_manifest"] == manifest
            raise RuntimeError(f"forwarded:{_verb}")

        monkeypatch.setattr(TOOL, function_name, observe_forwarding)
        with pytest.raises(RuntimeError, match=f"forwarded:{verb}"):
            TOOL.main(
                [
                    verb,
                    *arguments,
                    "--task-manifest",
                    os.fspath(manifest_path),
                ]
            )


def test_default_and_explicit_default_task_manifest_cli_results_are_equal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    manifest_path = _canonical(
        tmp_path / "default-manifest.json", TOOL.TASK_MANIFEST
    )

    def fake_build_snapshot(
        repo: Path,
        snapshot: Path,
        sessions_root: Path,
        case: str,
        *,
        task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
    ) -> dict[str, Any]:
        return {
            "case": case,
            "task_manifest_sha256": TOOL._task_manifest_sha256(task_manifest),
        }

    monkeypatch.setattr(TOOL, "build_snapshot", fake_build_snapshot)
    common = [
        "build-snapshot",
        "--snapshot",
        os.fspath(tmp_path / "snapshot"),
        "--benchmark-task-id",
        "POS",
    ]
    assert TOOL.main(common) == 0
    implicit = capfd.readouterr().out
    assert TOOL.main(
        [*common, "--task-manifest", os.fspath(manifest_path)]
    ) == 0
    explicit = capfd.readouterr().out
    assert explicit == implicit

    external_manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    external_path = _canonical(
        tmp_path / "external-manifest.json", external_manifest
    )
    assert TOOL.main(
        [
            "build-snapshot",
            "--snapshot",
            os.fspath(tmp_path / "snapshot"),
            "--benchmark-task-id",
            "alpha",
            "--task-manifest",
            os.fspath(external_path),
        ]
    ) == 0
    external = json.loads(capfd.readouterr().out)
    assert external["case"] == "alpha"
    assert external["task_manifest_sha256"] == TOOL._task_manifest_sha256(
        external_manifest
    )
    assert external["task_manifest_sha256"] != json.loads(implicit)[
        "task_manifest_sha256"
    ]


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


def test_stage5_freeze_registers_seven_items_create_only_and_unbound(
    tmp_path: Path,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    contract = fixture["contract"]
    integrity_path = fixture["contract_path"].with_name(
        fixture["contract_path"].name + ".integrity.json"
    )
    integrity = json.loads(integrity_path.read_text(encoding="utf-8"))

    assert contract["schema_version"] == TOOL.STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION
    assert contract["schema_version"] != TOOL.STAGE2_REPLAYER_SCHEMA_VERSION
    assert contract["contract_kind"] == "stage5-author-replayer-contract"
    assert contract["source_descriptors"] == {
        "plan": TOOL._stage5_file_descriptor(fixture["plan"], "source plan"),
        "author_output": TOOL._stage5_file_descriptor(
            fixture["author_output"], "source author output"
        ),
        "snapshot": TOOL._stage5_snapshot_descriptor(
            fixture["snapshot"], "source snapshot"
        ),
        "git": TOOL._stage5_file_descriptor(fixture["git"], "source Git"),
    }
    assert integrity["source_plan"] == contract["source_descriptors"]["plan"]
    assert integrity["source_author_output"] == contract["source_descriptors"][
        "author_output"
    ]
    assert integrity["source_snapshot"] == contract["source_descriptors"][
        "snapshot"
    ]
    assert integrity["source_git"] == contract["source_descriptors"]["git"]
    assert contract["frozen_plan"]["sha256"] == TOOL._sha256(
        fixture["plan"].read_bytes()
    )
    assert contract["plan_input_hash"] == contract["frozen_plan"]["sha256"]
    assert contract["author_output_hash"] == TOOL._sha256(_STAGE5_AUTHOR_PATCH)
    assert contract["frozen_author_output"]["format"] == "git-diff-v1"
    assert contract["application_target"]["relative_root"] == "repo"
    assert contract["downstream_pins"] == {
        "review": {"requested_model": TOOL.MODEL, "requested_effort": "high"},
        "fix": {
            "requested_model": "gpt-5.6-luna",
            "requested_effort": "max",
        },
    }
    assert contract["fix_pass_limit"] == 2
    assert contract["receipt_policy"]["argv_match"] == "exact"
    assert contract["application_apparatus"]["check_argv"][1:] == [
        "apply",
        "--check",
        "--whitespace=nowarn",
        "-",
    ]
    registered = {
        fixture["contract_path"],
        integrity_path,
        Path(contract["frozen_plan"]["path"]),
        Path(contract["frozen_author_output"]["artifact"]["path"]),
        Path(contract["application_target"]["snapshot"]["path"]),
        Path(contract["application_apparatus"]["git"]["path"]).parent,
        Path(contract["application_apparatus"]["git"]["path"]),
    }
    assert len(registered) == 7
    assert all(path.exists() and not path.is_symlink() for path in registered)
    assert set(fixture["run_root"].iterdir()) == {
        fixture["contract_path"],
        integrity_path,
        Path(contract["frozen_plan"]["path"]),
        Path(contract["frozen_author_output"]["artifact"]["path"]),
        Path(contract["application_target"]["snapshot"]["path"]),
        Path(contract["application_apparatus"]["git"]["path"]).parent,
    }
    assert set(
        Path(contract["application_apparatus"]["git"]["path"]).parent.iterdir()
    ) == {Path(contract["application_apparatus"]["git"]["path"])}
    for artifact in (contract, integrity):
        assert artifact["task_acceptance_status"] == "unbound"
        assert artifact["fix_gate_eligible"] is False
        assert artifact["routing_evidence_eligible"] is False
        assert not {"accepted", "success", "passed"} & set(_nested_keys(artifact))

    before = {
        path: path.read_bytes()
        for path in fixture["run_root"].rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    before_tree = TOOL._stage5_snapshot_descriptor(
        fixture["run_root"], "stage5 test run root"
    )["sha256"]
    with pytest.raises(TOOL.ValidationError, match="already exists"):
        TOOL.freeze_stage5_author_replayer(
            fixture["plan"],
            fixture["author_output"],
            fixture["contract_path"],
            snapshot=fixture["snapshot"],
            application_root="repo",
            git_binary=fixture["git"],
            review_model=TOOL.MODEL,
            review_effort="high",
            fix_model="gpt-5.6-luna",
            fix_effort="max",
            fix_pass_limit=2,
        )
    assert {
        path: path.read_bytes() for path in before
    } == before
    assert TOOL._stage5_snapshot_descriptor(
        fixture["run_root"], "stage5 test run root"
    )["sha256"] == before_tree


def test_stage5_freeze_rolls_back_after_git_probe_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _stage5_sources(tmp_path)

    def fail_probe(*args: Any, **kwargs: Any) -> str:
        raise TOOL.ValidationError("injected Git probe failure", TOOL.RC_ROUTING)

    monkeypatch.setattr(TOOL, "_stage5_version_probe", fail_probe)
    with pytest.raises(TOOL.ValidationError, match="injected Git probe failure"):
        TOOL.freeze_stage5_author_replayer(
            fixture["plan"],
            fixture["author_output"],
            fixture["contract_path"],
            snapshot=fixture["snapshot"],
            application_root="repo",
            git_binary=fixture["git"],
            review_model=TOOL.MODEL,
            review_effort="high",
            fix_model="gpt-5.6-luna",
            fix_effort="max",
            fix_pass_limit=2,
        )
    assert list(fixture["run_root"].iterdir()) == []


def test_stage5_freeze_rollback_preserves_competing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _stage5_sources(tmp_path)
    competing = fixture["run_root"] / "stage5-plan-input"
    competing_bytes = b"competing create-only owner\n"
    delegated = TOOL._stage5_create_only_bytes

    def inject_competitor(
        path: Path, data: bytes, *, mode: int = 0o600
    ) -> None:
        if path == competing:
            competing.write_bytes(competing_bytes)
        delegated(path, data, mode=mode)

    monkeypatch.setattr(TOOL, "_stage5_create_only_bytes", inject_competitor)
    with pytest.raises(TOOL.ValidationError, match="already exists"):
        TOOL.freeze_stage5_author_replayer(
            fixture["plan"],
            fixture["author_output"],
            fixture["contract_path"],
            snapshot=fixture["snapshot"],
            application_root="repo",
            git_binary=fixture["git"],
            review_model=TOOL.MODEL,
            review_effort="high",
            fix_model="gpt-5.6-luna",
            fix_effort="max",
            fix_pass_limit=2,
        )
    assert competing.read_bytes() == competing_bytes


def test_stage5_freeze_rollback_uses_identity_saved_at_create_barrier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _stage5_sources(tmp_path)
    competing = fixture["run_root"] / "stage5-plan-input"
    competing_bytes = b"replacement after successful create\n"
    delegated = TOOL._stage5_create_only_bytes

    def replace_after_create(
        path: Path, data: bytes, *, mode: int = 0o600
    ) -> Any:
        owned = delegated(path, data, mode=mode)
        if path == competing:
            path.unlink()
            path.write_bytes(competing_bytes)
        return owned

    monkeypatch.setattr(TOOL, "_stage5_create_only_bytes", replace_after_create)
    with pytest.raises(TOOL.ValidationError, match="copy sha mismatch"):
        TOOL.freeze_stage5_author_replayer(
            fixture["plan"],
            fixture["author_output"],
            fixture["contract_path"],
            snapshot=fixture["snapshot"],
            application_root="repo",
            git_binary=fixture["git"],
            review_model=TOOL.MODEL,
            review_effort="high",
            fix_model="gpt-5.6-luna",
            fix_effort="max",
            fix_pass_limit=2,
        )
    assert competing.read_bytes() == competing_bytes


def test_stage5_snapshot_rollback_uses_identity_saved_at_mkdir_barrier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _stage5_sources(tmp_path)
    competing = fixture["run_root"] / "stage5-snapshot"
    marker = competing / "competing-owner"
    delegated = TOOL._stage5_create_owned_directory

    def replace_after_mkdir(path: Path, *, mode: int) -> Any:
        owned = delegated(path, mode=mode)
        if path == competing:
            path.rmdir()
            path.mkdir(mode=mode)
            marker.write_bytes(b"replacement directory identity\n")
        return owned

    monkeypatch.setattr(
        TOOL, "_stage5_create_owned_directory", replace_after_mkdir
    )
    with pytest.raises(TOOL.ValidationError, match="copy sha mismatch"):
        TOOL.freeze_stage5_author_replayer(
            fixture["plan"],
            fixture["author_output"],
            fixture["contract_path"],
            snapshot=fixture["snapshot"],
            application_root="repo",
            git_binary=fixture["git"],
            review_model=TOOL.MODEL,
            review_effort="high",
            fix_model="gpt-5.6-luna",
            fix_effort="max",
            fix_pass_limit=2,
        )
    assert marker.read_bytes() == b"replacement directory identity\n"


def test_stage5_create_only_write_failure_preserves_replacement_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "owned"
    competing_bytes = b"replacement during fsync\n"

    def replace_then_fail(_descriptor: int) -> None:
        target.unlink()
        target.write_bytes(competing_bytes)
        raise OSError("injected fsync failure")

    monkeypatch.setattr(TOOL.os, "fsync", replace_then_fail)
    with pytest.raises(OSError, match="injected fsync failure"):
        TOOL._stage5_create_only_bytes(target, b"created bytes\n")
    assert target.read_bytes() == competing_bytes


def test_stage5_create_only_wrapper_rejects_overwrite_and_preserves_bytes(
    tmp_path: Path,
) -> None:
    target = tmp_path / "owned"
    target.write_bytes(b"competitor\n")
    with pytest.raises(TOOL.ValidationError, match="already exists"):
        TOOL._stage5_create_only_bytes(target, b"replacement\n")
    assert target.read_bytes() == b"competitor\n"


def test_stage5_isolated_validation_is_deterministic_and_leaves_live_tree(
    tmp_path: Path,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    first = TOOL.validate_stage5_author_application(
        contract_path=fixture["contract_path"],
        run_root=fixture["run_root"],
        receipt_path=fixture["run_root"] / "application-1.json",
    )
    second = TOOL.validate_stage5_author_application(
        contract_path=fixture["contract_path"],
        run_root=fixture["run_root"],
        receipt_path=fixture["run_root"] / "application-2.json",
    )
    assert first["pre_tree_sha256"] == second["pre_tree_sha256"]
    assert first["post_tree_sha256"] == second["post_tree_sha256"]
    assert first["post_tree_sha256"] != first["pre_tree_sha256"]
    assert fixture["target"].joinpath("file.txt").read_bytes() == b"old\n"
    assert list(fixture["run_root"].glob(".stage5-application-*")) == []
    assert first["receipt_status"] == "mechanically-valid"
    assert first["task_acceptance_status"] == "unbound"
    assert first["fix_gate_eligible"] is False
    assert first["routing_evidence_eligible"] is False
    assert not {"accepted", "success", "passed"} & set(_nested_keys(first))


@pytest.mark.parametrize("artifact", ("plan", "author"))
def test_stage5_frozen_single_leaf_tamper_is_rejected(
    tmp_path: Path, artifact: str
) -> None:
    fixture = _stage5_fixture(tmp_path)
    contract = fixture["contract"]
    path = (
        Path(contract["frozen_plan"]["path"])
        if artifact == "plan"
        else Path(contract["frozen_author_output"]["artifact"]["path"])
    )
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(TOOL.ValidationError, match=f"stage5 frozen {artifact}"):
        TOOL.validate_stage5_author_application(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=fixture["run_root"] / "application.json",
        )


@pytest.mark.parametrize(
    ("case", "message"),
    (
        ("namespace", "schema version mismatch"),
        ("kind_namespace", "contract kind mismatch"),
        ("plan_hash", "plan input hash mismatch"),
        ("author_hash", "author output hash mismatch"),
        ("acceptance", "task acceptance must remain unbound"),
    ),
)
def test_stage5_contract_mutation_guards_reject_direct_changes(
    tmp_path: Path, case: str, message: str
) -> None:
    fixture = _stage5_fixture(tmp_path)
    contract = copy.deepcopy(fixture["contract"])
    if case == "namespace":
        contract["schema_version"] = TOOL.STAGE2_REPLAYER_SCHEMA_VERSION
    elif case == "kind_namespace":
        contract["contract_kind"] = "stage2-plan-replayer"
    elif case == "plan_hash":
        contract["plan_input_hash"] = "f" * 64
    elif case == "author_hash":
        contract["author_output_hash"] = "e" * 64
    else:
        contract["task_acceptance_status"] = "accepted"
    with pytest.raises(TOOL.ValidationError, match=message):
        TOOL._stage5_validate_contract(
            contract, run_root=fixture["run_root"]
        )


@pytest.mark.parametrize(
    ("source", "leaf", "replacement", "message"),
    (
        ("source_plan", "sha256", "f" * 64, "sha256 mismatch"),
        ("source_author_output", "bytes", 0, "bytes mismatch"),
        ("source_snapshot", "path", "relative", "path is not absolute"),
        ("source_git", "bytes", False, "nonnegative integer"),
        ("source_git", "device", "1", "nonnegative integer"),
        ("source_git", "inode", None, "nonnegative integer"),
    ),
)
def test_stage5_integrity_source_descriptor_single_leaf_tamper_is_rejected(
    tmp_path: Path,
    source: str,
    leaf: str,
    replacement: Any,
    message: str,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    integrity_path = fixture["contract_path"].with_name(
        fixture["contract_path"].name + ".integrity.json"
    )
    integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
    integrity[source][leaf] = replacement
    with pytest.raises(TOOL.ValidationError, match=message):
        TOOL._stage5_validate_integrity(
            integrity,
            contract_path=fixture["contract_path"],
            contract=fixture["contract"],
            contract_raw=fixture["contract_path"].read_bytes(),
        )


@pytest.mark.parametrize(
    ("source", "leaf"),
    (
        ("source_plan", "path"),
        ("source_plan", "kind"),
        ("source_git", "mode"),
        ("source_author_output", "device"),
        ("source_snapshot", "inode"),
    ),
)
def test_stage5_integrity_valid_source_provenance_leaf_change_is_rejected(
    tmp_path: Path, source: str, leaf: str
) -> None:
    fixture = _stage5_fixture(tmp_path)
    integrity_path = fixture["contract_path"].with_name(
        fixture["contract_path"].name + ".integrity.json"
    )
    integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
    if leaf == "path":
        integrity[source][leaf] = os.fspath(fixture["author_output"].resolve())
    elif leaf == "kind":
        integrity[source][leaf] = "directory"
    else:
        integrity[source][leaf] += 1
    with pytest.raises(TOOL.ValidationError, match=rf"{leaf} mismatch"):
        TOOL._stage5_validate_integrity(
            integrity,
            contract_path=fixture["contract_path"],
            contract=fixture["contract"],
            contract_raw=fixture["contract_path"].read_bytes(),
        )


@pytest.mark.parametrize(
    ("value", "valid", "message"),
    (
        ("repo", True, ""),
        ("repo/nested", True, ""),
        ("/repo", False, "POSIX relative"),
        ("", False, "empty or dot"),
        (".", False, "empty or dot"),
        ("repo\\nested", False, "POSIX relative"),
    ),
)
def test_stage5_application_root_posix_relative_matrix(
    value: str, valid: bool, message: str
) -> None:
    if valid:
        assert TOOL._stage5_relative_root(value) == value
    else:
        with pytest.raises(TOOL.ValidationError, match=message):
            TOOL._stage5_relative_root(value)


@pytest.mark.parametrize("case", ("parent", "symlink"))
def test_stage5_application_root_escape_or_symlink_is_rejected(
    tmp_path: Path, case: str
) -> None:
    fixture = _stage5_sources(tmp_path)
    application_root = "../repo"
    match = "escape"
    if case == "symlink":
        fixture["snapshot"].joinpath("link").symlink_to(
            "repo", target_is_directory=True
        )
        with pytest.raises(TOOL.ValidationError, match="symlink"):
            TOOL._stage5_application_root(fixture["snapshot"], "link")
        return
    with pytest.raises(TOOL.ValidationError, match=match):
        TOOL.freeze_stage5_author_replayer(
            fixture["plan"],
            fixture["author_output"],
            fixture["contract_path"],
            snapshot=fixture["snapshot"],
            application_root=application_root,
            git_binary=fixture["git"],
            review_model=TOOL.MODEL,
            review_effort="high",
            fix_model="gpt-5.6-luna",
            fix_effort="max",
            fix_pass_limit=2,
        )


def test_stage5_application_receipt_post_tree_tamper_is_rejected(
    tmp_path: Path,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    receipt = TOOL.validate_stage5_author_application(
        contract_path=fixture["contract_path"],
        run_root=fixture["run_root"],
        receipt_path=fixture["run_root"] / "application.json",
    )
    tampered = copy.deepcopy(receipt)
    tampered["post_tree_sha256"] = "f" * 64
    with pytest.raises(TOOL.ValidationError, match="post_tree_sha256 mismatch"):
        TOOL._stage5_validate_application_receipt(
            tampered,
            contract=fixture["contract"],
            contract_sha256=receipt["contract_sha256"],
            expected_post_tree_sha256=receipt["post_tree_sha256"],
        )


def test_stage5_downstream_receipt_validator_binds_role_specific_pins(
    tmp_path: Path,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    for role, pass_index, name in (
        ("review", 0, "review.json"),
        ("fix", 1, "fix-1.json"),
        ("fix", 2, "fix-2.json"),
    ):
        path, receipt, expected = _stage5_downstream_receipt(
            fixture,
            role=role,
            pass_index=pass_index,
            name=name,
        )
        observed = TOOL.validate_stage5_downstream_receipt(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=path,
            **expected,
        )
        assert observed == receipt
        assert observed["requested_model"] == fixture["contract"][
            "downstream_pins"
        ][role]["requested_model"]
        assert observed["task_acceptance_status"] == "unbound"
        assert observed["fix_gate_eligible"] is False
        assert observed["routing_evidence_eligible"] is False
        assert not {"accepted", "success", "passed"} & set(
            _nested_keys(observed)
        )


@pytest.mark.parametrize(
    ("leaf_path", "replacement", "role", "message"),
    (
        (("contract_sha256",), "f" * 64, "review", "contract_sha256 mismatch"),
        (("author_output_hash",), "e" * 64, "review", "author_output_hash mismatch"),
        (
            ("application_target_sha256",),
            "d" * 64,
            "review",
            "application_target_sha256 mismatch",
        ),
        (("requested_model",), "gpt-5.6-luna", "review", "requested_model mismatch"),
        (("requested_effort",), "max", "review", "requested_effort mismatch"),
        (("argv",), ["codex", "wrong"], "review", "argv mismatch"),
        (("output", "regular"), False, "review", "output mismatch"),
        (("output", "bytes"), 0, "review", "output mismatch"),
        (("exit_code",), 1, "review", "exit_code mismatch"),
        (("timed_out",), True, "review", "timed_out mismatch"),
        (
            ("receipt_status",),
            "invalid",
            "review",
            "receipt_status mismatch",
        ),
        (
            ("task_acceptance_status",),
            "accepted",
            "review",
            "task_acceptance_status mismatch",
        ),
        (
            ("fix_gate_eligible",),
            True,
            "review",
            "fix_gate_eligible mismatch",
        ),
        (
            ("routing_evidence_eligible",),
            True,
            "review",
            "routing_evidence_eligible mismatch",
        ),
    ),
)
def test_stage5_downstream_receipt_single_leaf_mismatch_is_rejected(
    tmp_path: Path,
    leaf_path: tuple[str, ...],
    replacement: Any,
    role: str,
    message: str,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    pass_index = 0 if role == "review" else 2
    path, receipt, expected = _stage5_downstream_receipt(
        fixture, role=role, pass_index=pass_index, name=f"{role}.json"
    )
    target = receipt
    for part in leaf_path[:-1]:
        target = target[part]
    target[leaf_path[-1]] = replacement
    path.write_bytes(TOOL._canonical_bytes(receipt))
    with pytest.raises(TOOL.ValidationError, match=message):
        TOOL.validate_stage5_downstream_receipt(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=path,
            **expected,
        )


@pytest.mark.parametrize(
    ("leaf_path", "replacement", "message"),
    (
        (("stdin_sha256",), "1" * 64, "stdin_sha256 mismatch"),
        (("output", "sha256"), "2" * 64, "output mismatch"),
        (("output_sha256",), "2" * 64, "output_sha256 mismatch"),
    ),
)
def test_stage5_downstream_receipt_rejects_single_caller_digest_leaf(
    tmp_path: Path,
    leaf_path: tuple[str, ...],
    replacement: str,
    message: str,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    path, receipt, expected = _stage5_downstream_receipt(
        fixture, role="review", pass_index=0, name="review.json"
    )
    target = receipt
    for part in leaf_path[:-1]:
        target = target[part]
    target[leaf_path[-1]] = replacement
    path.write_bytes(TOOL._canonical_bytes(receipt))
    with pytest.raises(TOOL.ValidationError, match=message):
        TOOL.validate_stage5_downstream_receipt(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=path,
            **expected,
        )


def test_stage5_fix_pass_cap_guard_is_single_reason() -> None:
    with pytest.raises(TOOL.ValidationError, match="fix pass index exceeds cap"):
        TOOL._stage5_validate_role_pass("fix", 3, 2, "stage5 cap mutation")


@pytest.mark.parametrize("case", ("tampered", "empty"))
def test_stage5_downstream_receipt_rejects_tampered_or_empty_output(
    tmp_path: Path, case: str
) -> None:
    fixture = _stage5_fixture(tmp_path)
    path, _, expected = _stage5_downstream_receipt(
        fixture, role="review", pass_index=0, name="review.json"
    )
    expected["output_path"].write_bytes(
        b"" if case == "empty" else b"tampered output\n"
    )
    message = "is empty" if case == "empty" else "output mismatch"
    with pytest.raises(TOOL.ValidationError, match=message):
        TOOL.validate_stage5_downstream_receipt(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=path,
            **expected,
        )


def test_stage5_downstream_receipt_rejects_previous_receipt_mismatch(
    tmp_path: Path,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    path, _, expected = _stage5_downstream_receipt(
        fixture, role="review", pass_index=0, name="review.json"
    )
    previous = json.loads(
        expected["previous_receipt_path"].read_text(encoding="utf-8")
    )
    previous["post_tree_sha256"] = "f" * 64
    expected["previous_receipt_path"].write_bytes(
        TOOL._canonical_bytes(previous)
    )
    with pytest.raises(
        TOOL.ValidationError, match="previous_receipt_sha256 mismatch"
    ):
        TOOL.validate_stage5_downstream_receipt(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=path,
            **expected,
        )


def test_stage5_downstream_receipt_rejects_previous_topology_mismatch(
    tmp_path: Path,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    path, receipt, expected = _stage5_downstream_receipt(
        fixture, role="review", pass_index=0, name="review.json"
    )
    previous = json.loads(
        expected["previous_receipt_path"].read_text(encoding="utf-8")
    )
    previous["receipt_kind"] = "stage5-downstream-receipt"
    expected["previous_receipt_path"].write_bytes(
        TOOL._canonical_bytes(previous)
    )
    receipt["previous_receipt_sha256"] = TOOL._sha256(
        expected["previous_receipt_path"].read_bytes()
    )
    path.write_bytes(TOOL._canonical_bytes(receipt))
    with pytest.raises(TOOL.ValidationError, match="topology mismatch"):
        TOOL.validate_stage5_downstream_receipt(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=path,
            **expected,
        )


def test_stage5_downstream_receipt_rejects_outside_root_and_trusted_role_pass(
    tmp_path: Path,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    path, _, expected = _stage5_downstream_receipt(
        fixture, role="review", pass_index=0, name="review.json"
    )
    for argument, source in (
        ("receipt_path", path),
        ("stdin_path", expected["stdin_path"]),
        ("output_path", expected["output_path"]),
        ("previous_receipt_path", expected["previous_receipt_path"]),
    ):
        outside = tmp_path / f"outside-{argument}"
        outside.write_bytes(source.read_bytes())
        kwargs = {
            "contract_path": fixture["contract_path"],
            "run_root": fixture["run_root"],
            "receipt_path": path,
            **expected,
            argument: outside,
        }
        with pytest.raises(
            TOOL.ValidationError, match="outside the stage5 run root"
        ):
            TOOL.validate_stage5_downstream_receipt(**kwargs)
    with pytest.raises(TOOL.ValidationError, match="role mismatch"):
        TOOL.validate_stage5_downstream_receipt(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=path,
            **{
                **expected,
                "expected_role": "fix",
                "expected_pass_index": 1,
            },
        )
    with pytest.raises(TOOL.ValidationError, match="review pass index must be zero"):
        TOOL.validate_stage5_downstream_receipt(
            contract_path=fixture["contract_path"],
            run_root=fixture["run_root"],
            receipt_path=path,
            **{**expected, "expected_pass_index": 1},
        )


def test_stage5_generic_correctness_keys_are_recursively_rejected(
    tmp_path: Path,
) -> None:
    fixture = _stage5_fixture(tmp_path)
    for forbidden in ("accepted", "success", "passed"):
        contract = copy.deepcopy(fixture["contract"])
        contract["receipt_policy"][forbidden] = False
        with pytest.raises(TOOL.ValidationError, match="forbidden correctness key"):
            TOOL._stage5_validate_contract(contract, run_root=fixture["run_root"])


def test_stage5_cli_verbs_parse_dispatch_and_keep_unbound_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    freeze_args = [
        "freeze-stage5-author-replayer",
        "--plan-input",
        os.fspath(tmp_path / "plan"),
        "--author-output",
        os.fspath(tmp_path / "author.diff"),
        "--output",
        os.fspath(tmp_path / "contract.json"),
        "--snapshot",
        os.fspath(tmp_path / "snapshot"),
        "--application-root",
        "repo",
        "--git-bin",
        os.fspath(tmp_path / "git"),
        "--review-model",
        TOOL.MODEL,
        "--review-effort",
        "high",
        "--fix-model",
        "gpt-5.6-luna",
        "--fix-effort",
        "max",
        "--fix-pass-limit",
        "2",
    ]
    frozen = {
        "schema_version": TOOL.STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
        "contract_kind": "stage5-author-replayer-contract",
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }
    calls: list[tuple[str, dict[str, Any]]] = []

    def capture_freeze(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls.append(("freeze", {"args": args, **kwargs}))
        return frozen

    monkeypatch.setattr(TOOL, "freeze_stage5_author_replayer", capture_freeze)
    assert TOOL._parser().parse_args(freeze_args).command == freeze_args[0]
    assert TOOL.main(freeze_args) == 0
    assert json.loads(capsys.readouterr().out) == frozen

    application_args = [
        "validate-stage5-author-application",
        "--contract",
        os.fspath(tmp_path / "contract.json"),
        "--run-root",
        os.fspath(tmp_path),
        "--receipt",
        os.fspath(tmp_path / "application.json"),
    ]
    application = {
        "schema_version": TOOL.STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
        "receipt_kind": TOOL._STAGE5_APPLICATION_RECEIPT_KIND,
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }

    def capture_application(**kwargs: Any) -> dict[str, Any]:
        calls.append(("application", kwargs))
        return application

    monkeypatch.setattr(
        TOOL, "validate_stage5_author_application", capture_application
    )
    assert TOOL.main(application_args) == 0
    assert json.loads(capsys.readouterr().out) == application

    receipt_args = [
        "validate-stage5-downstream-receipt",
        "--contract",
        os.fspath(tmp_path / "contract.json"),
        "--run-root",
        os.fspath(tmp_path),
        "--receipt",
        os.fspath(tmp_path / "receipt.json"),
        "--expected-role",
        "review",
        "--expected-pass-index",
        "0",
        "--stdin-file",
        os.fspath(tmp_path / "stdin.txt"),
        "--output-file",
        os.fspath(tmp_path / "output.txt"),
        "--previous-receipt",
        os.fspath(tmp_path / "previous.json"),
    ]
    downstream = {
        "schema_version": TOOL.STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
        "receipt_kind": TOOL._STAGE5_DOWNSTREAM_RECEIPT_KIND,
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }

    def capture_receipt(**kwargs: Any) -> dict[str, Any]:
        calls.append(("receipt", kwargs))
        return downstream

    monkeypatch.setattr(TOOL, "validate_stage5_downstream_receipt", capture_receipt)
    assert TOOL.main(receipt_args) == 0
    assert json.loads(capsys.readouterr().out) == downstream
    assert [name for name, _ in calls] == ["freeze", "application", "receipt"]
    assert calls[0][1]["args"] == (
        tmp_path / "plan",
        tmp_path / "author.diff",
        tmp_path / "contract.json",
    )
    assert calls[0][1]["application_root"] == "repo"
    assert calls[0][1]["review_model"] == TOOL.MODEL
    assert calls[0][1]["fix_model"] == "gpt-5.6-luna"
    assert calls[0][1]["fix_pass_limit"] == 2
    assert calls[1][1] == {
        "contract_path": tmp_path / "contract.json",
        "run_root": tmp_path,
        "receipt_path": tmp_path / "application.json",
    }
    assert calls[2][1] == {
        "contract_path": tmp_path / "contract.json",
        "run_root": tmp_path,
        "receipt_path": tmp_path / "receipt.json",
        "expected_role": "review",
        "expected_pass_index": 0,
        "stdin_path": tmp_path / "stdin.txt",
        "output_path": tmp_path / "output.txt",
        "previous_receipt_path": tmp_path / "previous.json",
    }
    for value in (frozen, application, downstream):
        assert value["task_acceptance_status"] == "unbound"
        assert value["fix_gate_eligible"] is False
        assert value["routing_evidence_eligible"] is False
        assert not {"accepted", "success", "passed"} & set(_nested_keys(value))

    def reject_freeze(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise TOOL.ValidationError("injected stage5 CLI rejection", TOOL.RC_ROUTING)

    monkeypatch.setattr(TOOL, "freeze_stage5_author_replayer", reject_freeze)
    assert TOOL.main(freeze_args) == TOOL.RC_ROUTING
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["task_acceptance_status"] == "unbound"
    assert rejected["fix_gate_eligible"] is False
    assert rejected["routing_evidence_eligible"] is False
    assert not {"accepted", "success", "passed"} & set(_nested_keys(rejected))


def test_stage5_git_failure_cli_does_not_echo_patch_controlled_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fixture = _stage5_sources(tmp_path)
    secret = "PATCH_CONTROLLED_SECRET_PATH"
    fixture["author_output"].write_text(
        "diff --git a/{0} b/{0}\n"
        "--- a/{0}\n"
        "+++ b/{0}\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n".format(secret),
        encoding="utf-8",
    )
    rc = TOOL.main(
        [
            "freeze-stage5-author-replayer",
            "--plan-input",
            os.fspath(fixture["plan"]),
            "--author-output",
            os.fspath(fixture["author_output"]),
            "--output",
            os.fspath(fixture["contract_path"]),
            "--snapshot",
            os.fspath(fixture["snapshot"]),
            "--application-root",
            "repo",
            "--git-bin",
            os.fspath(fixture["git"]),
            "--review-model",
            TOOL.MODEL,
            "--review-effort",
            "high",
            "--fix-model",
            "gpt-5.6-luna",
            "--fix-effort",
            "max",
            "--fix-pass-limit",
            "2",
        ]
    )
    rendered = capsys.readouterr().out
    result = json.loads(rendered)
    assert rc == TOOL.RC_RECEIPT
    assert secret not in rendered
    assert len(result["failure_reasons"]) == 1
    reason = result["failure_reasons"][0]
    assert reason.startswith("stage5 Git apply check failed; exit_code=")
    assert "; stderr_bytes=" in reason
    assert "; stderr_sha256=" in reason
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False


def test_stage5_runtime_block_has_no_stage2_helper_or_constant_dependency() -> None:
    source = _TOOL_PATH.read_text(encoding="utf-8")
    stage5_start = source.index(
        "@dataclass(frozen=True)\nclass Stage5AuthorReplayerContract"
    )
    block = source[stage5_start : source.index("def _supervise_one", stage5_start)]
    assert "_stage2_" not in block
    assert "STAGE2_" not in block


@pytest.mark.parametrize(
    ("mutation", "function_start", "function_end", "exact_old", "masked_old"),
    (
        (
            "M1",
            "def _stage5_validate_contract",
            "def _stage5_run_git_apply",
            'value.get("contract_kind") != _STAGE5_CONTRACT_KIND',
            'if value.get("contract_kind") != _STAGE5_CONTRACT_KIND:\n'
            '        raise ValidationError("stage5 contract kind mismatch", RC_ROUTING)',
        ),
        (
            "M8",
            "def _stage5_validate_acceptance",
            "def _stage5_validate_git_pin",
            'value.get("task_acceptance_status") != "unbound"',
            'if value.get("task_acceptance_status") != "unbound":\n'
            "        raise ValidationError(f\"{label} task acceptance must remain "
            "unbound\", RC_ROUTING)",
        ),
        (
            "M9",
            "def _stage5_create_only_bytes",
            "def _stage5_create_only_json",
            "flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL",
            "flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL\n"
            '    if hasattr(os, "O_NOFOLLOW"):\n'
            "        flags |= os.O_NOFOLLOW",
        ),
    ),
)
def test_stage5_mutation_exact_old_and_context_mask_are_unique(
    mutation: str,
    function_start: str,
    function_end: str,
    exact_old: str,
    masked_old: str,
) -> None:
    source = _TOOL_PATH.read_text(encoding="utf-8")
    start = source.index(function_start)
    block = source[start : source.index(function_end, start)]
    assert block.count(exact_old) == 1, mutation
    assert block.count(masked_old) == 1, mutation


def test_stage2_source_block_has_no_wave_d_reachability_names() -> None:
    # M8: forbidden Wave-D reachability names must be absent from new stage2 code.
    source = _TOOL_PATH.read_text(encoding="utf-8")
    stage2_start = source.index("class Stage2PlanReplayerContract")
    stage5_start = source.index(
        "@dataclass(frozen=True)\nclass Stage5AuthorReplayerContract",
        stage2_start,
    )
    block = source[stage2_start:stage5_start]
    assert "Stage5AuthorReplayerContract" not in block
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


@pytest.mark.parametrize("row_index", (0, 1), ids=("technical", "pair-mate"))
@pytest.mark.parametrize("field", (*TOOL._COST_TOKEN_FIELDS, "model_calls"))
def test_f1_supervisor_ledger_rejects_nonzero_not_launched_accounting(
    tmp_path: Path,
    row_index: int,
    field: str,
) -> None:
    slots = [
        {
            "slot_id": "s01",
            "case": "POS",
            "arm": "max",
            "block_id": "b01",
            "block_order": 1,
        },
        {
            "slot_id": "s02",
            "case": "POS",
            "arm": "high",
            "block_id": "b01",
            "block_order": 2,
        },
    ]
    completions: list[dict[str, Any]] = []
    for index, slot in enumerate(slots):
        row = {
            **slot,
            "phase": "completed",
            "attempt": 1,
            "run_id": f"r{index + 1:02d}",
            "process_started": False,
            "not_launched": True,
            "supervision_start_monotonic_ns": 10,
            "supervision_end_monotonic_ns": 20,
            "supervision_wall_ms": 0,
            "launch_receipt": None,
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
            "model_calls": 0,
        }
        if index == 0:
            row.update(
                {
                    "failure_class": "technical-invalid",
                    "prelaunch_failure": {
                        "kind": "prelaunch-exception",
                        "exception_type": "OSError",
                        "message": "fixture",
                    },
                }
            )
        else:
            row.update(
                {
                    "failure_class": "pair-invalidated",
                    "individual_failure_class": None,
                    "pair_invalidation": {"technical_run_ids": ["r01"]},
                }
            )
        completions.append(row)
    completions[row_index][field] = 1
    reserved = [
        {
            "phase": "reserved",
            "slot_id": row["slot_id"],
            "block_id": row["block_id"],
            "attempt": 1,
        }
        for row in completions
    ]
    attempts = [
        {"slot_id": row["slot_id"], "attempt": 1, "run_id": row["run_id"]}
        for row in completions
    ]
    _, reasons = TOOL._validate_supervisor_ledger(
        [*reserved, *completions],
        slots,
        attempts,
        tmp_path,
        TOOL.MAX_SCHEDULE_GAP_MS,
        TOOL.MAX_INTER_BLOCK_GAP_MS,
    )
    assert any(field in reason and "not-launched" in reason for reason in reasons)


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
    task_manifest = benchmark_snapshots["task_manifest"]
    schedule_path, _ = _schedule(
        tmp_path / "schedule.json",
        benchmark_snapshots,
        task_manifest=task_manifest,
    )
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
            task_manifest=task_manifest,
        )


def test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation(
    tmp_path: Path,
    benchmark_snapshots: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_manifest = benchmark_snapshots["task_manifest"]
    schedule_path, slots = _schedule(
        tmp_path / "schedule.json",
        benchmark_snapshots,
        task_manifest=task_manifest,
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
            task_manifest=task_manifest,
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
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                kwargs["task_manifest"]
            ),
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
        task_manifest=task_manifest,
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
                "oracle_kind": TOOL._manifest_task(case=case)["oracle_kind"],
                "r1_detected": case == "POS",
                "findings": [],
                "reader_agreement": True,
            }
    return slots, attempts, verdicts


def _task_specific_aggregate_rows() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
]:
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
        verdicts[slot["slot_id"]]["oracle_kind"] = task_manifest["tasks"][
            task_id
        ]["oracle_kind"]
    return task_manifest, slots, attempts, verdicts


def test_aggregate_verified_uses_oracle_kind_and_keeps_task_model_axes_separate(
    tmp_path: Path,
) -> None:
    task_manifest, slots, attempts, verdicts = _task_specific_aggregate_rows()
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


def test_aggregate_verified_rejects_cross_task_equivalent_from_manifest_union(
    tmp_path: Path,
) -> None:
    task_manifest, slots, attempts, verdicts = _task_specific_aggregate_rows()
    beta_slot = next(
        row for row in slots if row["benchmark_task_id"] == "beta"
    )
    assert "alpha-finding" in TOOL.known_finding_ids_for_manifest(task_manifest)
    assert "alpha-finding" not in TOOL.known_finding_ids_for_manifest(
        task_manifest, benchmark_task_id="beta"
    )
    verdicts[beta_slot["slot_id"]]["findings"] = [
        {
            "real": False,
            "equivalent_to": "alpha-finding",
            "root_cause": None,
            "severity": "LOW",
            "must_fix": False,
        }
    ]
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "cross-task-aggregate.json", {}),
        slots,
        attempts,
        verdicts,
        [],
        task_manifest=task_manifest,
    )
    expected_reason = f"{beta_slot['slot_id']}: unknown equivalent finding id"
    assert result["failure_reasons"].count(expected_reason) == 1
    assert result["valid"] is False
    assert result["experiment_complete"] is False


@pytest.mark.parametrize("oracle_kind", ("wrong", "missing"))
def test_aggregate_verified_rejects_adjudication_oracle_kind_mismatch(
    oracle_kind: str,
    tmp_path: Path,
) -> None:
    task_manifest, slots, attempts, verdicts = _task_specific_aggregate_rows()
    beta_slot = next(
        row for row in slots if row["benchmark_task_id"] == "beta"
    )
    beta_verdict = verdicts[beta_slot["slot_id"]]
    if oracle_kind == "wrong":
        beta_verdict["oracle_kind"] = "positive"
    else:
        del beta_verdict["oracle_kind"]
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / f"oracle-kind-{oracle_kind}.json", {}),
        slots,
        attempts,
        verdicts,
        [],
        task_manifest=task_manifest,
    )
    expected_reason = (
        f"{beta_slot['slot_id']}: adjudication oracle_kind does not match "
        "scheduled slot"
    )
    assert result["failure_reasons"].count(expected_reason) == 1
    assert result["valid"] is False
    assert result["experiment_complete"] is False


def test_bound_price_aggregate_rejects_attempt_price_mismatch(
    tmp_path: Path,
) -> None:
    task_manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    slots, schedule_reasons = TOOL._validate_schedule(
        _bound_price_schedule(), task_manifest=task_manifest
    )
    assert schedule_reasons == []
    attempts: list[dict[str, Any]] = []
    verdicts: dict[str, dict[str, Any]] = {}
    for index, slot in enumerate(slots, 1):
        attempts.append(
            {
                **slot,
                "run_id": f"r{index:02d}",
                "attempt": 1,
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
        verdicts[slot["slot_id"]] = {
            "oracle_kind": slot["oracle_kind"],
            "r1_detected": True,
            "findings": [],
            "reader_agreement": True,
        }
    attempts[0]["price_version"] = None
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "bound-aggregate-manifest.json", {}),
        slots,
        attempts,
        verdicts,
        [],
        task_manifest=task_manifest,
    )
    assert result["valid"] is False
    assert result["experiment_complete"] is False
    assert "r01: attempt price_version does not match scheduled slot" in result[
        "failure_reasons"
    ]


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


def _packet_fixture(
    tmp_path: Path,
    *,
    task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
) -> tuple[Path, Path, Path]:
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
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                task_manifest
            ),
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


def test_m15_packet_consumer_requires_exact_task_manifest_digest_once(
    tmp_path: Path,
) -> None:
    state, _, _ = _packet_fixture(tmp_path)
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    assert TOOL._task_manifest_sha256(alternate) != TOOL._task_manifest_sha256()
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.freeze_verdicts(
            state,
            tmp_path / "not-read-before-digest-mismatch.jsonl",
            tmp_path / "not-created.json",
            task_manifest=alternate,
        )
    assert caught.value.rc == TOOL.RC_AGGREGATE
    assert caught.value.reasons == (
        "packet state task_manifest_sha256 mismatch",
    )


def test_m15_append_verdicts_rejects_packet_state_manifest_exchange(
    tmp_path: Path,
) -> None:
    state, _, second = _packet_fixture(tmp_path)
    state_value = json.loads(state.read_text(encoding="utf-8"))
    packet_id = state_value["packets"][0]["packet_id"]
    packet_path = state.parent / state_value["packets"][0]["filename"]
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    expected = TOOL._task_manifest_sha256()
    alternate_digest = TOOL._task_manifest_sha256(alternate)
    assert alternate_digest != expected
    state_value["task_manifest_sha256"] = alternate_digest
    _canonical(state, state_value)

    log = tmp_path / "verdicts.jsonl"
    TOOL._append_jsonl(
        log,
        {
            "packet_id": packet_id,
            "reader": "parent",
            "task_manifest_sha256": expected,
            "packet_sha256_at_read": TOOL._sha256(packet_path.read_bytes()),
            "r1_detected": True,
            "findings": [],
        },
    )
    before = log.read_bytes()
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.append_verdicts(state, log, "second-reader", second)
    assert caught.value.rc == TOOL.RC_AGGREGATE
    assert caught.value.reasons == (
        "packet state task_manifest_sha256 mismatch",
    )
    assert log.read_bytes() == before


def test_m15_supervise_pair_rejects_schedule_manifest_exchange(
    tmp_path: Path,
) -> None:
    schedule = _canonical(
        tmp_path / "schedule.json",
        {"task_manifest_sha256": TOOL._task_manifest_sha256(), "slots": []},
    )
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.supervise_pair(
            schedule_path=schedule,
            run_root=tmp_path / "run",
            block_id="b01",
            attempt=1,
            snapshot=tmp_path / "snapshot",
            prompt=tmp_path / "prompt",
            config_source=tmp_path / "config",
            auth_source=tmp_path / "auth",
            codex_binary=tmp_path / "codex",
            bwrap_binary=tmp_path / "bwrap",
            dry_run=True,
            task_manifest=alternate,
        )
    assert caught.value.reasons == ("schedule task_manifest_sha256 mismatch",)


@pytest.mark.parametrize(
    "entrypoint",
    (TOOL.aggregate_manifest, TOOL.verify_manifest),
    ids=("aggregate", "verify"),
)
def test_m15_material_entrypoints_reject_manifest_exchange(
    tmp_path: Path,
    entrypoint: Any,
) -> None:
    material = _canonical(
        tmp_path / "material.json",
        {"task_manifest_sha256": TOOL._task_manifest_sha256()},
    )
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    result, rc = entrypoint(
        material,
        sessions_root=tmp_path / "sessions",
        task_manifest=alternate,
    )
    assert rc == TOOL.RC_AGGREGATE
    assert result["failure_reasons"] == [
        "material manifest task_manifest_sha256 mismatch"
    ]


def test_m15_make_packets_rejects_schedule_manifest_exchange(
    tmp_path: Path,
) -> None:
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    source = _canonical(
        tmp_path / "source.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "attempts": [],
            "schedule": {
                "task_manifest_sha256": TOOL._task_manifest_sha256(alternate),
                "slots": [],
            },
        },
    )
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.make_packets(
            source, tmp_path / "packets", tmp_path / "custodian"
        )
    assert caught.value.reasons == ("schedule task_manifest_sha256 mismatch",)


def test_f3_m15_append_verdicts_rejects_existing_log_manifest_exchange(
    tmp_path: Path,
) -> None:
    state, _, second = _packet_fixture(tmp_path)
    state_value = json.loads(state.read_text(encoding="utf-8"))
    packet_id = state_value["packets"][0]["packet_id"]
    packet_path = state.parent / state_value["packets"][0]["filename"]
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    log = tmp_path / "verdicts.jsonl"
    TOOL._append_jsonl(
        log,
        {
            "packet_id": packet_id,
            "reader": "parent",
            "task_manifest_sha256": TOOL._task_manifest_sha256(alternate),
            "packet_sha256_at_read": TOOL._sha256(packet_path.read_bytes()),
            "r1_detected": True,
            "findings": [],
        },
    )
    before = log.read_bytes()
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.append_verdicts(state, log, "second-reader", second)
    assert caught.value.reasons == ("verdict row task_manifest_sha256 mismatch",)
    assert log.read_bytes() == before


def test_m15_freeze_verdicts_rejects_log_manifest_exchange(
    tmp_path: Path,
) -> None:
    state, parent, _ = _packet_fixture(tmp_path)
    state_value = json.loads(state.read_text(encoding="utf-8"))
    packet_id = state_value["packets"][0]["packet_id"]
    packet_path = state.parent / state_value["packets"][0]["filename"]
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    log = tmp_path / "verdicts.jsonl"
    parent_value = json.loads(parent.read_text(encoding="utf-8"))["verdicts"][0]
    TOOL._append_jsonl(
        log,
        {
            **parent_value,
            "reader": "parent",
            "task_manifest_sha256": TOOL._task_manifest_sha256(alternate),
            "packet_sha256_at_read": TOOL._sha256(packet_path.read_bytes()),
        },
    )
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.freeze_verdicts(state, log, tmp_path / "freeze.json")
    assert caught.value.reasons == ("verdict row task_manifest_sha256 mismatch",)


def test_task_manifest_digest_is_recorded_through_packet_freeze_and_reveal(
    tmp_path: Path,
) -> None:
    task_manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    output = tmp_path / "answer.md"
    output.write_text(_long_output(), encoding="utf-8")
    premanifest = _canonical(
        tmp_path / "premanifest.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(task_manifest),
            "attempts": [
                {
                    "slot_id": "s01",
                    "attempt": 1,
                    "run_id": "r01",
                    "output": _descriptor(output, tmp_path),
                }
            ]
        },
    )
    custodian = tmp_path / "custodian"
    packet_result = TOOL.make_packets(
        premanifest,
        tmp_path / "packets",
        custodian,
        task_manifest=task_manifest,
    )
    expected = TOOL._task_manifest_sha256(task_manifest)
    assert packet_result["task_manifest_sha256"] == expected
    state_path = Path(packet_result["packet_state"])
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["task_manifest_sha256"] == expected
    private_path = TOOL._custodian_mapping_path(custodian)
    private = json.loads(private_path.read_text(encoding="utf-8"))
    assert private["task_manifest_sha256"] == expected

    packet_id = state["packets"][0]["packet_id"]
    verdict = {
        "verdicts": [
            {"packet_id": packet_id, "r1_detected": True, "findings": []}
        ]
    }
    parent = _canonical(tmp_path / "parent.json", verdict)
    second = _canonical(tmp_path / "second.json", verdict)
    log = tmp_path / "verdicts.jsonl"
    parent_result = TOOL.append_verdicts(
        state_path, log, "parent", parent, task_manifest=task_manifest
    )
    second_result = TOOL.append_verdicts(
        state_path, log, "second-reader", second, task_manifest=task_manifest
    )
    assert parent_result["task_manifest_sha256"] == expected
    assert second_result["task_manifest_sha256"] == expected
    freeze_path = tmp_path / "freeze.json"
    freeze = TOOL.freeze_verdicts(
        state_path, log, freeze_path, task_manifest=task_manifest
    )
    assert freeze["task_manifest_sha256"] == expected
    revealed_path = tmp_path / "revealed.json"
    revealed = TOOL.reveal_mapping(
        state_path,
        custodian,
        log,
        freeze_path,
        revealed_path,
        task_manifest=task_manifest,
    )
    assert revealed["task_manifest_sha256"] == expected


def _task_specific_adjudication_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    cross_task_reader: str | None = None,
    external_transport: bool = False,
    fixed_task_manifest_path: Path | None = None,
) -> dict[str, Any]:
    if fixed_task_manifest_path is None:
        task_manifest_value = _synthetic_task_manifest(
            (
                ("alpha", "POS", "positive", "alpha-finding"),
                ("beta", "NEG", "negative", "beta-finding"),
            )
        )
        task_manifest_path = (
            _canonical(tmp_path / "task-manifest.json", task_manifest_value)
            if external_transport
            else None
        )
        task_manifest = (
            TOOL._load_task_manifest(task_manifest_path)
            if task_manifest_path is not None
            else task_manifest_value
        )
    else:
        assert not external_transport
        task_manifest_path = fixed_task_manifest_path
        task_manifest = TOOL._load_task_manifest(
            task_manifest_path,
            profile=_WIRING_SLICE_PROFILE,
        )
    task_ids = tuple(task_manifest["tasks"])
    assert len(task_ids) == 2
    source_task_id, target_task_id = task_ids
    source_finding_id = task_manifest["tasks"][source_task_id][
        "known_finding_ids"
    ][0]
    task_manifest_sha256 = TOOL._task_manifest_sha256(task_manifest)
    schedule_rows: list[dict[str, Any]] = []
    for task_number, task_id in enumerate(task_ids, 1):
        block_id = f"task-block-{task_number:02d}"
        for block_order, (arm, model) in enumerate(
            (("max", "gpt-5.6-sol"), ("high", "gpt-5.6-luna")),
            1,
        ):
            schedule_rows.append(
                _v3_slot(
                    slot_id=f"s{(task_number - 1) * 2 + block_order:02d}",
                    task_id=task_id,
                    block_id=block_id,
                    block_order=block_order,
                    arm=arm,
                    requested_model=model,
                )
            )
            schedule_rows[-1]["legacy_case"] = task_manifest["tasks"][task_id][
                "legacy_case"
            ]
            schedule_rows[-1]["stage"] = task_manifest["tasks"][task_id][
                "stage"
            ]
    schedule = {
        "schema_version": TOOL.TASK_MANIFEST_SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "slots": schedule_rows,
    }
    run_root = tmp_path / "replay-run"
    attempts_root = run_root / "attempts"
    sessions_root = tmp_path / "sessions"
    attempts_root.mkdir(parents=True)
    sessions_root.mkdir()
    schedule_path = run_root / "schedule.json"
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    snapshot_oracle = {
        "snapshot": os.fspath(snapshot.resolve()),
        "submodule_manifest_sha256": "c" * 64,
    }
    snapshot_oracle_path = _canonical(
        tmp_path / "snapshot-oracle.json", snapshot_oracle
    )
    snapshot_oracle_sha256 = TOOL._sha256(snapshot_oracle_path.read_bytes())
    prompt = tmp_path / "prompt.txt"
    prompt.write_bytes(b"task-specific adjudication prompt")
    prompt_sha256 = TOOL._sha256(prompt.read_bytes())
    for slot in schedule_rows:
        slot["case"] = slot["legacy_case"]
        slot["prompt_sha256"] = prompt_sha256
        slot["snapshot_manifest_sha256"] = snapshot_oracle_sha256
    schedule_path = _canonical(schedule_path, schedule)
    schedule_sha256 = TOOL._sha256(schedule_path.read_bytes())
    attempt_descriptors: list[dict[str, Any]] = []
    packet_attempts: list[dict[str, Any]] = []
    receipts: dict[str, dict[str, Any]] = {}
    scores: dict[str, dict[str, Any]] = {}
    supervisor_completions: list[dict[str, Any]] = []
    final_attempts: dict[str, dict[str, Any]] = {}
    for index, slot in enumerate(schedule_rows, 1):
        run_id = f"r{index:02d}"
        attempt_root = attempts_root / run_id
        attempt_root.mkdir()
        events = _canonical(attempt_root / "events.jsonl", {"events": index})
        done = _canonical(attempt_root / "done.json", {"done": index})
        output = attempt_root / "answer.md"
        output.write_text(_long_output(), encoding="utf-8")
        output_sha256 = TOOL._sha256(output.read_bytes())
        rollout = _canonical(
            sessions_root / f"rollout-{run_id}.jsonl", {"rollout": index}
        )
        launch = _canonical(
            attempt_root / "launch.json",
            {
                "run_id": run_id,
                "slot_id": slot["slot_id"],
                "attempt": 1,
                "parent_run_id": None,
                "case": slot["case"],
                "arm": slot["arm"],
                "requested_model": slot["requested_model"],
                "schedule_sha256": schedule_sha256,
                "prompt": {"sha256": prompt_sha256},
                "snapshot_oracle": {"sha256": snapshot_oracle_sha256},
                "treatment_identity_sha256": f"identity-{slot['benchmark_task_id']}",
            },
        )
        receipt = {
            "run_id": run_id,
            "rollout_path": os.fspath(rollout.resolve()),
            "wall_clock_ms": 0,
            "failure_reasons": [],
            "failure_class": None,
            "valid": True,
            "input_tokens": 1,
            "cached_input_tokens": 0,
            "output_tokens": 1,
            "reasoning_output_tokens": 0,
            "cli_reported": 2,
            "model_calls": 1,
            "token_usage_observations": _token_usage_observations(),
            "turn_protocol": "single-turn-required",
            "rate_limited": False,
            "retry": False,
            "compaction_observed": False,
        }
        score = {"valid": True, "r1_candidate": True, "decision": "NO-GO"}
        receipt_path = _canonical(attempt_root / "receipt.json", receipt)
        score_path = _canonical(attempt_root / "score.json", score)
        attempts_row = {
            "run_id": run_id,
            "slot_id": slot["slot_id"],
            "attempt": 1,
            "parent_run_id": None,
            "launch_receipt": _descriptor(launch, tmp_path),
            "events": _descriptor(events, tmp_path),
            "done": _descriptor(done, tmp_path),
            "prompt": _descriptor(prompt, tmp_path),
            "output": _descriptor(output, tmp_path),
            "snapshot_oracle": _descriptor(snapshot_oracle_path, tmp_path),
            "snapshot_after": _descriptor(snapshot_oracle_path, tmp_path),
            "rollout": _descriptor(rollout, tmp_path),
            "receipt": _descriptor(receipt_path, tmp_path),
            "score": _descriptor(score_path, tmp_path),
        }
        attempt_descriptors.append(attempts_row)
        packet_attempts.append(
            {
                "slot_id": slot["slot_id"],
                "attempt": 1,
                "run_id": run_id,
                "output": _descriptor(output, tmp_path),
            }
        )
        receipts[run_id] = receipt
        scores[run_id] = score
        supervisor_completions.append(
            {"run_id": run_id, "process_started": True, "process_wall_ms": 0}
        )
        final_attempts[slot["slot_id"]] = {
            "run_id": run_id,
            "output_sha256": output_sha256,
        }

    # The schedule descriptor is deliberately part of the packet source.  This
    # fixture must exercise the v3 paired-schedule path, not compatibility mode.
    packet_source = _canonical(
        tmp_path / "packet-source.json",
        {
            "task_manifest_sha256": task_manifest_sha256,
            "schedule": _descriptor(schedule_path, tmp_path),
            "attempts": packet_attempts,
        },
    )
    custodian = tmp_path / "custodian"
    packet_result = TOOL.make_packets(
        packet_source,
        tmp_path / "packets",
        custodian,
        task_manifest=task_manifest,
    )
    packet_state_path = Path(packet_result["packet_state"])
    packet_state = json.loads(packet_state_path.read_text(encoding="utf-8"))
    private_path = TOOL._custodian_mapping_path(custodian)
    private = json.loads(private_path.read_text(encoding="utf-8"))
    private_by_packet = {
        row["packet_id"]: row for row in private["mapping"]
    }
    slot_by_id = {row["slot_id"]: row for row in schedule_rows}
    cross_task_packet_id = next(
        row["packet_id"]
        for row in private["mapping"]
        if slot_by_id[row["slot_id"]]["benchmark_task_id"] == target_task_id
    )

    verdict_inputs: dict[str, Path] = {}
    for reader in ("parent", "second-reader"):
        verdict_rows: list[dict[str, Any]] = []
        for packet in packet_state["packets"]:
            packet_id = packet["packet_id"]
            mapped_slot = slot_by_id[
                private_by_packet[packet_id]["slot_id"]
            ]
            task_id = mapped_slot["benchmark_task_id"]
            finding_id = task_manifest["tasks"][task_id]["known_finding_ids"][0]
            if reader == cross_task_reader and packet_id == cross_task_packet_id:
                finding_id = source_finding_id
            verdict_rows.append(
                {
                    "packet_id": packet_id,
                    "r1_detected": True,
                    "findings": [
                        {
                            "real": True,
                            "equivalent_to": finding_id,
                            "root_cause": None,
                            "severity": "LOW",
                            "must_fix": False,
                        }
                    ],
                }
            )
        verdict_inputs[reader] = _canonical(
            tmp_path / f"{reader}-verdicts.json", {"verdicts": verdict_rows}
        )
    verdict_log = tmp_path / "verdicts.jsonl"
    append_results = {
        reader: TOOL.append_verdicts(
            packet_state_path,
            verdict_log,
            reader,
            verdict_inputs[reader],
            task_manifest=task_manifest,
        )
        for reader in ("parent", "second-reader")
    }
    freeze_path = tmp_path / "verdict-freeze.json"
    freeze = TOOL.freeze_verdicts(
        packet_state_path,
        verdict_log,
        freeze_path,
        task_manifest=task_manifest,
    )
    revealed_path = tmp_path / "revealed-map.json"
    revealed = TOOL.reveal_mapping(
        packet_state_path,
        custodian,
        verdict_log,
        freeze_path,
        revealed_path,
        task_manifest=task_manifest,
    )
    for index, artifact in enumerate(
        (packet_state_path, verdict_log, freeze_path, revealed_path), 1
    ):
        timestamp_ns = TOOL.PACKET_MTIME_NS + index * 1_000_000
        os.utime(artifact, ns=(timestamp_ns, timestamp_ns))

    logged_rows = [
        json.loads(line)
        for line in verdict_log.read_text(encoding="utf-8").splitlines()
    ]
    readers_by_packet: dict[str, dict[str, dict[str, Any]]] = {}
    for row in logged_rows:
        readers_by_packet.setdefault(row["packet_id"], {})[row["reader"]] = row
    slot_by_run = {
        attempt["run_id"]: slot_by_id[slot_id]
        for slot_id, attempt in final_attempts.items()
    }
    judgments: list[dict[str, Any]] = []
    for mapping in revealed["mapping"]:
        packet_id = mapping["packet_id"]
        slot = slot_by_run[mapping["run_id"]]
        readers = readers_by_packet[packet_id]
        parent_finding = readers["parent"]["findings"][0]
        second_finding = readers["second-reader"]["findings"][0]
        finding_fields = ("equivalent_to", "root_cause", "severity", "must_fix")
        conservative_findings = (
            [parent_finding]
            if all(
                parent_finding[field] == second_finding[field]
                for field in finding_fields
            )
            else []
        )
        combined = {
            "oracle_kind": TOOL._slot_dimensions(
                slot, task_manifest=task_manifest
            )["oracle_kind"],
            "r1_detected": True,
            "findings": conservative_findings,
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
                "score_input_sha256": mapping["score_input_sha256"],
                "combined_verdict_sha256": TOOL._sha256(
                    TOOL._canonical_bytes(combined)
                ),
                "r1_detected": combined["r1_detected"],
                "reader_agreement": combined["reader_agreement"],
            }
        )

    ledger_path = _canonical(run_root / "attempt-ledger.jsonl", {})
    material = {
        "schema_version": TOOL.SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "run_root": run_root.name,
        "attempts_root": f"{run_root.name}/attempts",
        "attempt_ledger": _descriptor(ledger_path, tmp_path),
        "max_schedule_gap_ms": TOOL.MAX_SCHEDULE_GAP_MS,
        "max_inter_block_gap_ms": TOOL.MAX_INTER_BLOCK_GAP_MS,
        "schedule": _descriptor(schedule_path, tmp_path),
        "schedule_sha256": schedule_sha256,
        "attempts": attempt_descriptors,
        "packet_state": _descriptor(packet_state_path, tmp_path),
        "verdict_log": _descriptor(verdict_log, tmp_path),
        "verdict_freeze": _descriptor(freeze_path, tmp_path),
        "revealed_map": _descriptor(revealed_path, tmp_path),
        "judgments": judgments,
    }
    material_path = _canonical(tmp_path / "material.json", material)
    slots, schedule_reasons = TOOL._validate_schedule(
        schedule, task_manifest=task_manifest
    )
    assert schedule_reasons == []

    monkeypatch.setattr(
        TOOL,
        "_validate_supervisor_ledger",
        lambda *args, **kwargs: (copy.deepcopy(supervisor_completions), []),
    )
    monkeypatch.setattr(
        TOOL,
        "verify_snapshot",
        lambda *args, **kwargs: copy.deepcopy(snapshot_oracle),
    )
    monkeypatch.setattr(
        TOOL,
        "collect_run",
        lambda **kwargs: (copy.deepcopy(receipts[kwargs["run_id"]]), 0),
    )
    monkeypatch.setattr(
        TOOL,
        "score_run",
        lambda _path, run_id: (copy.deepcopy(scores[run_id]), 0),
    )
    return {
        "append_results": append_results,
        "cross_task_packet_id": cross_task_packet_id,
        "final_attempts": final_attempts,
        "freeze": freeze,
        "logged_rows": logged_rows,
        "manifest": material,
        "manifest_path": material_path,
        "packet_state": packet_state,
        "packet_source": packet_source,
        "private": private,
        "revealed": revealed,
        "schedule": schedule,
        "sessions_root": sessions_root,
        "slots": slots,
        "task_manifest": task_manifest,
        "task_manifest_path": task_manifest_path,
        "source_finding_id": source_finding_id,
        "source_task_id": source_task_id,
        "target_task_id": target_task_id,
    }


def test_or_m2_main_rejects_forbidden_slice_command_before_side_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    snapshot = tmp_path / "must-not-exist"
    sentinel_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def side_effect_sentinel(*args: Any, **kwargs: Any) -> dict[str, Any]:
        sentinel_calls.append((args, kwargs))
        raise AssertionError("build_snapshot side-effect sentinel reached")

    monkeypatch.setattr(TOOL, "build_snapshot", side_effect_sentinel)
    rc = TOOL.main(
        [
            "build-snapshot",
            "--snapshot", os.fspath(snapshot),
            "--benchmark-task-id", "T-1222-population-closure:plan:0",
            "--task-manifest", os.fspath(_WIRING_SLICE_PATH),
            "--task-manifest-profile", _WIRING_SLICE_PROFILE,
        ]
    )
    result = json.loads(capfd.readouterr().out)
    assert rc == TOOL.RC_ROUTING
    assert result["valid"] is False
    assert result["failure_reasons"] == [
        "oracle wiring slice command is not allowed: build-snapshot"
    ]
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"
    assert result["experiment_complete"] is False
    assert result["decision"] is None
    assert sentinel_calls == []
    assert not snapshot.exists()


def test_profile_pin_failure_full_cli_keeps_conservative_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(TOOL, "_WIRING_SLICE_MANIFEST_RAW_SHA256", "0" * 64)
    rc = TOOL.main(
        [
            "verify",
            "--manifest", os.fspath(tmp_path / "unused-material.json"),
            "--sessions-root", os.fspath(tmp_path / "sessions"),
            "--task-manifest", os.fspath(_WIRING_SLICE_PATH),
            "--task-manifest-profile", _WIRING_SLICE_PROFILE,
        ]
    )
    result = json.loads(capfd.readouterr().out)
    assert rc == TOOL.RC_ROUTING
    assert result["valid"] is False
    assert result["failure_reasons"] == [
        "oracle wiring slice raw SHA-256 pin mismatch"
    ]
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"
    assert result["experiment_complete"] is False
    assert result["decision"] is None


def test_tampered_slice_semantic_pin_failure_full_cli_is_conservative(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    value = json.loads(_WIRING_SLICE_PATH.read_bytes())
    value["tasks"]["T-1222-population-closure:plan:0"]["oracle_findings"][0][
        "detection_condition"
    ] += " Tampered."
    path = _canonical(tmp_path / "tampered-slice.json", value)
    rc = TOOL.main(
        [
            "verify",
            "--manifest", os.fspath(tmp_path / "unused-material.json"),
            "--sessions-root", os.fspath(tmp_path / "sessions"),
            "--task-manifest", os.fspath(path),
            "--task-manifest-profile", _WIRING_SLICE_PROFILE,
        ]
    )
    result = json.loads(capfd.readouterr().out)
    assert rc == TOOL.RC_ROUTING
    assert result["valid"] is False
    assert result["failure_reasons"] == [
        "wiring_slice: semantic SHA-256 pin mismatch"
    ]
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"
    assert result["experiment_complete"] is False
    assert result["decision"] is None


@pytest.mark.parametrize("mutation", ("missing", "schema"))
def test_profile_hint_normalizes_load_and_schema_failures(
    mutation: str,
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "slice.json"
    if mutation == "schema":
        value = json.loads(_WIRING_SLICE_PATH.read_bytes())
        value["unknown"] = True
        _canonical(path, value)
    rc = TOOL.main(
        [
            "verify",
            "--manifest", os.fspath(tmp_path / "unused-material.json"),
            "--sessions-root", os.fspath(tmp_path / "sessions"),
            "--task-manifest", os.fspath(path),
            "--task-manifest-profile", _WIRING_SLICE_PROFILE,
        ]
    )
    result = json.loads(capfd.readouterr().out)
    assert rc == TOOL.RC_ROUTING
    assert result["valid"] is False
    if mutation == "missing":
        assert result["failure_reasons"][0].startswith(
            "cannot read profiled task manifest"
        )
    else:
        assert result["failure_reasons"] == [
            "wiring_slice: field set mismatch"
        ]
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"
    assert result["experiment_complete"] is False
    assert result["decision"] is None


def test_slice_verify_early_failure_is_incomplete_and_undecided(
    tmp_path: Path,
) -> None:
    task_manifest = TOOL._load_task_manifest(
        _WIRING_SLICE_PATH,
        profile=_WIRING_SLICE_PROFILE,
    )
    result, rc = TOOL.verify_manifest(
        tmp_path / "unused-material.json",
        sessions_root=None,
        task_manifest=task_manifest,
    )
    assert rc == TOOL.RC_AGGREGATE
    assert result["valid"] is False
    assert result["failure_reasons"] == ["sessions-root is required"]
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"
    assert result["experiment_complete"] is False
    assert result["decision"] is None


@pytest.mark.parametrize("entrypoint", ("verify", "aggregate"))
def test_or_m7_checked_slice_keeps_acceptance_unbound_when_valid(
    entrypoint: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _task_specific_adjudication_fixture(
        tmp_path,
        monkeypatch,
        fixed_task_manifest_path=_WIRING_SLICE_PATH,
    )
    assert all(
        result["appended"] == 4
        for result in fixture["append_results"].values()
    )
    rc = TOOL.main(
        [
            entrypoint,
            "--manifest", os.fspath(fixture["manifest_path"]),
            "--sessions-root", os.fspath(fixture["sessions_root"]),
            "--task-manifest", os.fspath(_WIRING_SLICE_PATH),
            "--task-manifest-profile", _WIRING_SLICE_PROFILE,
        ]
    )
    result = json.loads(capfd.readouterr().out)
    assert rc == 0
    assert result["valid"] is True
    assert result["experiment_complete"] is True
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"


def test_slice_material_digest_mismatch_full_cli_is_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _task_specific_adjudication_fixture(
        tmp_path,
        monkeypatch,
        fixed_task_manifest_path=_WIRING_SLICE_PATH,
    )
    material = copy.deepcopy(fixture["manifest"])
    material["task_manifest_sha256"] = "0" * 64
    fixture["manifest_path"].write_bytes(TOOL._canonical_bytes(material))

    rc = TOOL.main(
        [
            "verify",
            "--manifest", os.fspath(fixture["manifest_path"]),
            "--sessions-root", os.fspath(fixture["sessions_root"]),
            "--task-manifest", os.fspath(_WIRING_SLICE_PATH),
            "--task-manifest-profile", _WIRING_SLICE_PROFILE,
        ]
    )
    result = json.loads(capfd.readouterr().out)
    assert rc == TOOL.RC_AGGREGATE
    assert result["valid"] is False
    assert "material manifest task_manifest_sha256 mismatch" in result[
        "failure_reasons"
    ]
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"
    assert result["experiment_complete"] is False
    assert result["decision"] is None


@pytest.mark.parametrize("entrypoint", ("verify", "aggregate"))
def test_or_m6_checked_slice_full_cli_rejects_cross_task_finding(
    entrypoint: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _task_specific_adjudication_fixture(
        tmp_path,
        monkeypatch,
        cross_task_reader="parent",
        fixed_task_manifest_path=_WIRING_SLICE_PATH,
    )
    assert all(
        result["appended"] == 4
        for result in fixture["append_results"].values()
    )
    target = next(
        row
        for row in fixture["logged_rows"]
        if row["packet_id"] == fixture["cross_task_packet_id"]
        and row["reader"] == "parent"
    )
    assert target["findings"][0]["equivalent_to"] == fixture[
        "source_finding_id"
    ]

    rc = TOOL.main(
        [
            entrypoint,
            "--manifest", os.fspath(fixture["manifest_path"]),
            "--sessions-root", os.fspath(fixture["sessions_root"]),
            "--task-manifest", os.fspath(_WIRING_SLICE_PATH),
            "--task-manifest-profile", _WIRING_SLICE_PROFILE,
        ]
    )
    result = json.loads(capfd.readouterr().out)
    assert rc == TOOL.RC_AGGREGATE
    assert result["valid"] is False
    assert result["experiment_complete"] is False
    assert result["decision"] is None
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"
    assert any(
        "finding equivalent_to is unknown for benchmark task "
        f"{fixture['target_task_id']}" in reason
        for reason in result["failure_reasons"]
    )


def test_or_m6_adjudication_reason_is_task_specific_for_checked_slice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _task_specific_adjudication_fixture(
        tmp_path,
        monkeypatch,
        cross_task_reader="parent",
        fixed_task_manifest_path=_WIRING_SLICE_PATH,
    )
    joined, reasons = TOOL._load_adjudication(
        fixture["manifest_path"],
        fixture["manifest"],
        fixture["slots"],
        fixture["final_attempts"],
        snapshot_verified_run_ids={
            attempt["run_id"]
            for attempt in fixture["final_attempts"].values()
        },
        task_manifest=fixture["task_manifest"],
    )
    expected_reason = (
        f"{fixture['cross_task_packet_id']}: parent finding equivalent_to "
        "is unknown "
        f"for benchmark task {fixture['target_task_id']}: "
        f"{fixture['source_finding_id']}"
    )
    assert reasons.count(expected_reason) == 1
    assert len(joined) == 4


def test_replay_manifest_forwards_external_task_manifest_to_real_adjudication_loader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    fixture = _task_specific_adjudication_fixture(
        tmp_path, monkeypatch, external_transport=True
    )
    task_manifest = fixture["task_manifest"]
    expected_digest = TOOL._task_manifest_sha256(task_manifest)
    task_manifest_path = fixture["task_manifest_path"]
    assert isinstance(task_manifest_path, Path)
    assert task_manifest_path.read_bytes() == TOOL._canonical_bytes(
        task_manifest
    )
    packet_source = json.loads(
        fixture["packet_source"].read_text(encoding="utf-8")
    )
    assert set(packet_source["schedule"]) == {"path", "sha256"}
    assert len(packet_source["attempts"]) == 4
    assert {
        (slot["benchmark_task_id"], slot["block_id"])
        for slot in fixture["slots"]
    } == {("alpha", "task-block-01"), ("beta", "task-block-02")}
    assert all(
        result["appended"] == 4
        and result["task_manifest_sha256"] == expected_digest
        for result in fixture["append_results"].values()
    )
    for artifact in (
        packet_source,
        fixture["schedule"],
        fixture["packet_state"],
        fixture["private"],
        fixture["freeze"],
        fixture["revealed"],
        fixture["manifest"],
    ):
        assert artifact["task_manifest_sha256"] == expected_digest
    assert all(
        row["task_manifest_sha256"] == expected_digest
        for row in fixture["logged_rows"]
    )

    slots, _, verdicts, reasons = TOOL._replay_manifest(
        fixture["manifest_path"],
        fixture["sessions_root"],
        task_manifest=task_manifest,
    )
    assert reasons == []
    assert len(slots) == len(verdicts) == 4
    for slot in slots:
        task_id = slot["benchmark_task_id"]
        verdict = verdicts[slot["slot_id"]]
        assert verdict["oracle_kind"] == task_manifest["tasks"][task_id][
            "oracle_kind"
        ]
        assert [
            finding["equivalent_to"] for finding in verdict["findings"]
        ] == [f"{task_id}-finding"]

    rc = TOOL.main(
        [
            "verify",
            "--manifest",
            os.fspath(fixture["manifest_path"]),
            "--sessions-root",
            os.fspath(fixture["sessions_root"]),
            "--task-manifest",
            os.fspath(task_manifest_path),
        ]
    )
    verified = json.loads(capfd.readouterr().out)
    assert rc == 0
    assert verified["valid"] is True
    assert verified["experiment_complete"] is True


def test_replay_manifest_forwards_external_task_manifest_digest_at_loader_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _task_specific_adjudication_fixture(
        tmp_path, monkeypatch, external_transport=True
    )
    task_manifest = fixture["task_manifest"]
    captured_task_manifests: list[dict[str, Any]] = []
    original_load_adjudication = TOOL._load_adjudication

    def capture_task_manifest(
        manifest_path: Path,
        manifest: dict[str, Any],
        slots: list[dict[str, Any]],
        final_attempts: dict[str, dict[str, Any]],
        *,
        snapshot_verified_run_ids: set[str],
        task_manifest: dict[str, Any] = TOOL.TASK_MANIFEST,
    ) -> tuple[dict[str, dict[str, Any]], list[str]]:
        captured_task_manifests.append(task_manifest)
        return original_load_adjudication(
            manifest_path,
            manifest,
            slots,
            final_attempts,
            snapshot_verified_run_ids=snapshot_verified_run_ids,
            task_manifest=task_manifest,
        )

    monkeypatch.setattr(TOOL, "_load_adjudication", capture_task_manifest)
    TOOL._replay_manifest(
        fixture["manifest_path"],
        fixture["sessions_root"],
        task_manifest=task_manifest,
    )

    assert TOOL._task_manifest_sha256(
        captured_task_manifests[-1]
    ) == TOOL._task_manifest_sha256(task_manifest)


@pytest.mark.parametrize("reader", ("parent", "second-reader"))
def test_load_adjudication_rejects_cross_task_equivalent_from_manifest_union(
    reader: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _task_specific_adjudication_fixture(
        tmp_path, monkeypatch, cross_task_reader=reader
    )
    task_manifest = fixture["task_manifest"]
    assert "alpha-finding" in TOOL.known_finding_ids_for_manifest(task_manifest)
    assert "alpha-finding" not in TOOL.known_finding_ids_for_manifest(
        task_manifest, benchmark_task_id="beta"
    )
    assert all(
        result["appended"] == 4
        for result in fixture["append_results"].values()
    )
    target_row = next(
        row
        for row in fixture["logged_rows"]
        if row["packet_id"] == fixture["cross_task_packet_id"]
        and row["reader"] == reader
    )
    assert target_row["findings"][0]["equivalent_to"] == "alpha-finding"

    # Direct _load_adjudication calls validate artifact digests, but the
    # material manifest's own exact digest is an entrypoint-level D931 gate.
    joined, reasons = TOOL._load_adjudication(
        fixture["manifest_path"],
        fixture["manifest"],
        fixture["slots"],
        fixture["final_attempts"],
        snapshot_verified_run_ids={
            attempt["run_id"]
            for attempt in fixture["final_attempts"].values()
        },
        task_manifest=task_manifest,
    )
    expected_reason = (
        f"{fixture['cross_task_packet_id']}: {reader} finding equivalent_to "
        "is unknown for benchmark task beta: alpha-finding"
    )
    assert reasons.count(expected_reason) == 1
    assert len(joined) == 4


def test_load_adjudication_dimension_join_failure_is_reasoned_and_not_joined(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _task_specific_adjudication_fixture(tmp_path, monkeypatch)
    malformed_slots = copy.deepcopy(fixture["slots"])
    malformed_slot = malformed_slots[0]
    malformed_slot["stage"] = "malformed-stage"
    target_run_id = fixture["final_attempts"][malformed_slot["slot_id"]][
        "run_id"
    ]
    target_packet_id = next(
        row["packet_id"]
        for row in fixture["revealed"]["mapping"]
        if row["run_id"] == target_run_id
    )

    # Direct _load_adjudication calls do not perform the material manifest's
    # own exact digest check; verify/aggregate entrypoints own that D931 gate.
    joined, reasons = TOOL._load_adjudication(
        fixture["manifest_path"],
        fixture["manifest"],
        malformed_slots,
        fixture["final_attempts"],
        snapshot_verified_run_ids={
            attempt["run_id"]
            for attempt in fixture["final_attempts"].values()
        },
        task_manifest=fixture["task_manifest"],
    )
    expected_reason = (
        f"{target_packet_id}: schedule slot dimension join failed: "
        f"{malformed_slot['slot_id']}"
    )
    assert reasons.count(expected_reason) == 1
    assert malformed_slot["slot_id"] not in joined
    assert len(joined) == 3


def test_m15_reveal_mapping_rejects_private_manifest_exchange(
    tmp_path: Path,
) -> None:
    output = tmp_path / "answer.md"
    output.write_text(_long_output(), encoding="utf-8")
    source = _canonical(
        tmp_path / "source.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "attempts": [
                {
                    "slot_id": "s01",
                    "attempt": 1,
                    "run_id": "r01",
                    "output": _descriptor(output, tmp_path),
                }
            ],
        },
    )
    custodian = tmp_path / "custodian"
    packets = TOOL.make_packets(source, tmp_path / "packets", custodian)
    state = Path(packets["packet_state"])
    state_value = json.loads(state.read_text(encoding="utf-8"))
    packet_id = state_value["packets"][0]["packet_id"]
    verdict = _canonical(
        tmp_path / "verdict.json",
        {
            "verdicts": [
                {"packet_id": packet_id, "r1_detected": True, "findings": []}
            ]
        },
    )
    log = tmp_path / "verdicts.jsonl"
    TOOL.append_verdicts(state, log, "parent", verdict)
    TOOL.append_verdicts(state, log, "second-reader", verdict)
    freeze = tmp_path / "freeze.json"
    TOOL.freeze_verdicts(state, log, freeze)
    private_path = TOOL._custodian_mapping_path(custodian)
    private = json.loads(private_path.read_text(encoding="utf-8"))
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    private["task_manifest_sha256"] = TOOL._task_manifest_sha256(alternate)
    _canonical(private_path, private)
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.reveal_mapping(
            state,
            custodian,
            log,
            freeze,
            tmp_path / "revealed.json",
        )
    assert caught.value.reasons == (
        "private packet mapping task_manifest_sha256 mismatch",
    )


def test_m15_reveal_mapping_rejects_packet_state_manifest_exchange(
    tmp_path: Path,
) -> None:
    output = tmp_path / "answer.md"
    output.write_text(_long_output(), encoding="utf-8")
    expected = TOOL._task_manifest_sha256()
    source = _canonical(
        tmp_path / "source.json",
        {
            "task_manifest_sha256": expected,
            "attempts": [
                {
                    "slot_id": "s01",
                    "attempt": 1,
                    "run_id": "r01",
                    "output": _descriptor(output, tmp_path),
                }
            ],
        },
    )
    custodian = tmp_path / "custodian"
    packets = TOOL.make_packets(source, tmp_path / "packets", custodian)
    state = Path(packets["packet_state"])
    state_value = json.loads(state.read_text(encoding="utf-8"))
    packet_id = state_value["packets"][0]["packet_id"]
    verdict = _canonical(
        tmp_path / "verdict.json",
        {
            "verdicts": [
                {"packet_id": packet_id, "r1_detected": True, "findings": []}
            ]
        },
    )
    log = tmp_path / "verdicts.jsonl"
    TOOL.append_verdicts(state, log, "parent", verdict)
    TOOL.append_verdicts(state, log, "second-reader", verdict)
    freeze = tmp_path / "freeze.json"
    TOOL.freeze_verdicts(state, log, freeze)

    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["task_type"] = "alternate-valid-task-type"
    alternate_digest = TOOL._task_manifest_sha256(alternate)
    assert alternate_digest != expected
    state_value["task_manifest_sha256"] = alternate_digest
    _canonical(state, state_value)

    freeze_value = json.loads(freeze.read_text(encoding="utf-8"))
    freeze_value["packet_state_sha256"] = TOOL._sha256(state.read_bytes())
    _canonical(freeze, freeze_value)
    private = json.loads(
        TOOL._custodian_mapping_path(custodian).read_text(encoding="utf-8")
    )
    verdict_rows = [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
    ]
    assert freeze_value["task_manifest_sha256"] == expected
    assert private["task_manifest_sha256"] == expected
    assert all(row["task_manifest_sha256"] == expected for row in verdict_rows)

    revealed = tmp_path / "revealed.json"
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.reveal_mapping(state, custodian, log, freeze, revealed)
    assert caught.value.rc == TOOL.RC_AGGREGATE
    assert caught.value.reasons == (
        "packet state task_manifest_sha256 mismatch",
    )
    assert not revealed.exists()


def test_make_packets_rejects_task_manifest_exchange_before_publication(
    tmp_path: Path,
) -> None:
    source = _canonical(
        tmp_path / "source.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "attempts": [],
        },
    )
    alternate = copy.deepcopy(TOOL.TASK_MANIFEST)
    alternate["tasks"]["POS"]["oracle_kind"] = "negative"
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL.make_packets(
            source,
            tmp_path / "packets",
            tmp_path / "custodian",
            task_manifest=alternate,
        )
    assert caught.value.rc == TOOL.RC_AGGREGATE
    assert caught.value.reasons == (
        "packet source manifest task_manifest_sha256 mismatch",
    )
    assert not (tmp_path / "packets").exists()
    assert not (tmp_path / "custodian").exists()


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
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "packet_state_sha256": "0" * 64,
            "verdict_log_sha256": "0" * 64,
        },
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
        {
            "schema_version": TOOL.TASK_MANIFEST_SCHEMA_VERSION,
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                task_manifest
            ),
            "slots": schedule_rows,
        },
    )
    manifest_path = _canonical(
        tmp_path / "manifest.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                task_manifest
            ),
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


def _bound_packet_manifest(tmp_path: Path, *, leak_literal: bool) -> tuple[Path, dict[str, Any]]:
    task_manifest = _synthetic_task_manifest()
    schedule_rows: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    for index, task_id in enumerate(("alpha", "beta", "gamma"), 1):
        for order, model in enumerate(("gpt-5.6-sol", "gpt-5.6-luna"), 1):
            slot_id = f"s{(index - 1) * 2 + order:02d}"
            schedule_rows.append(
                {
                    **_v3_slot(
                        slot_id=slot_id,
                        task_id=task_id,
                        block_id=f"b{index:02d}",
                        block_order=order,
                        arm="max",
                        requested_model=model,
                    ),
                    "price_version": _TEST_PRICE_VERSION,
                }
            )
            output = tmp_path / f"bound-output-{slot_id}.md"
            output.write_text(
                _long_output()
                + (
                    "\n" + _TEST_PRICE_VERSION
                    if leak_literal and slot_id == "s01"
                    else ""
                ),
                encoding="utf-8",
            )
            attempts.append(
                {
                    "slot_id": slot_id,
                    "attempt": 1,
                    "run_id": f"r{(index - 1) * 2 + order:02d}",
                    "price_version": _TEST_PRICE_VERSION,
                    "output": _descriptor(output, tmp_path),
                }
            )
    schedule_path = _canonical(
        tmp_path / "bound-packet-schedule.json",
        {
            "schema_version": 3,
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                task_manifest
            ),
            "price_snapshot": {
                "path": _TEST_PRICE_SNAPSHOT_PATH,
                "sha256": _TEST_PRICE_SNAPSHOT_SHA256,
            },
            "slots": schedule_rows,
        },
    )
    manifest_path = _canonical(
        tmp_path / "bound-packet-manifest.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(
                task_manifest
            ),
            "schedule": _descriptor(schedule_path, tmp_path),
            "attempts": attempts,
        },
    )
    return manifest_path, task_manifest


def test_make_packets_with_bound_non_null_price_keeps_value_out_of_public_packets(
    tmp_path: Path,
) -> None:
    manifest_path, task_manifest = _bound_packet_manifest(
        tmp_path, leak_literal=False
    )
    result = TOOL.make_packets(
        manifest_path,
        tmp_path / "bound-packets",
        tmp_path / "bound-custodian",
        task_manifest=task_manifest,
    )
    state_path = Path(result["packet_state"])
    public_bytes = state_path.read_bytes() + b"".join(
        path.read_bytes()
        for path in sorted(state_path.parent.glob("packet-*.md"))
    )
    assert b"price_version" not in public_bytes
    assert _TEST_PRICE_VERSION.encode("utf-8") not in public_bytes
    assert result["packet_count"] == 6


def test_make_packets_rejects_bound_price_literal_before_publication(
    tmp_path: Path,
) -> None:
    manifest_path, task_manifest = _bound_packet_manifest(
        tmp_path, leak_literal=True
    )
    packet_dir = tmp_path / "bound-packets"
    custodian = tmp_path / "bound-custodian"
    with pytest.raises(TOOL.ValidationError, match="literal") as caught:
        TOOL.make_packets(
            manifest_path,
            packet_dir,
            custodian,
            task_manifest=task_manifest,
        )
    assert caught.value.rc == TOOL.RC_AGGREGATE
    assert not packet_dir.exists()
    assert not custodian.exists()


def test_make_packets_all_null_legacy_schedule_allows_incidental_frozen_literal(
    tmp_path: Path,
) -> None:
    schedule_rows: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    slot_number = 0
    for case, block_count in (("POS", 3), ("NEG", 2)):
        for _ in range(block_count):
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
                output = tmp_path / f"legacy-output-{slot_id}.md"
                output.write_text(
                    _long_output()
                    + ("\n" + _TEST_PRICE_VERSION if slot_id == "s01" else ""),
                    encoding="utf-8",
                )
                attempts.append(
                    {
                        "slot_id": slot_id,
                        "attempt": 1,
                        "run_id": f"r{slot_number:02d}",
                        "output": _descriptor(output, tmp_path),
                    }
                )
    schedule_path = _canonical(
        tmp_path / "legacy-null-schedule.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "slots": schedule_rows,
        },
    )
    manifest_path = _canonical(
        tmp_path / "legacy-null-manifest.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "schedule": _descriptor(schedule_path, tmp_path),
            "attempts": attempts,
        },
    )
    result = TOOL.make_packets(
        manifest_path,
        tmp_path / "legacy-packets",
        tmp_path / "legacy-custodian",
    )
    assert result["packet_count"] == 10
    public_bodies = b"".join(
        path.read_bytes()
        for path in Path(result["packet_state"]).parent.glob("packet-*.md")
    )
    assert _TEST_PRICE_VERSION.encode("utf-8") in public_bodies


def test_make_packets_rejects_empty_packet_only_manifest(tmp_path: Path) -> None:
    manifest_path = _canonical(
        tmp_path / "manifest.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "attempts": [],
        },
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
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
            "slots": schedule_rows,
        },
    )
    manifest_path = _canonical(
        tmp_path / "manifest.json",
        {
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
            "oracle_kind": TOOL._slot_dimensions(slot)["oracle_kind"],
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


def test_material_packet_source_requires_replayed_snapshot_evidence(
    tmp_path: Path,
) -> None:
    (
        manifest_path,
        manifest,
        slots,
        final_attempts,
        _,
        _,
    ) = _verdict_packet_swap_restore_fixture(tmp_path)
    revealed_path = Path(manifest["revealed_map"]["path"])
    if not revealed_path.is_absolute():
        revealed_path = tmp_path / revealed_path
    mapping = json.loads(revealed_path.read_text(encoding="utf-8"))[
        "mapping"
    ]
    target = mapping[0]
    all_run_ids = {
        str(attempt["run_id"]) for attempt in final_attempts.values()
    }
    expected_reason = (
        f"{target['packet_id']}: material packet source run lacks replayed "
        f"snapshot evidence: {target['run_id']}"
    )

    _, complete_reasons = TOOL._load_adjudication(
        manifest_path,
        manifest,
        slots,
        final_attempts,
        snapshot_verified_run_ids=all_run_ids,
    )
    assert expected_reason not in complete_reasons

    _, missing_reasons = TOOL._load_adjudication(
        manifest_path,
        manifest,
        slots,
        final_attempts,
        snapshot_verified_run_ids=all_run_ids - {target["run_id"]},
    )
    assert missing_reasons.count(expected_reason) == 1


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
    snapshot_verified_run_ids = {
        str(attempt["run_id"]) for attempt in final_attempts.values()
    }

    joined, reasons = TOOL._load_adjudication(
        manifest_path,
        manifest,
        slots,
        final_attempts,
        snapshot_verified_run_ids=snapshot_verified_run_ids,
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
            manifest_path,
            manifest,
            slots,
            final_attempts,
            snapshot_verified_run_ids=snapshot_verified_run_ids,
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
            manifest_path,
            manifest,
            slots,
            final_attempts,
            snapshot_verified_run_ids=snapshot_verified_run_ids,
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
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
            "task_manifest_sha256": TOOL._task_manifest_sha256(),
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
        manifest_path,
        manifest,
        slots,
        final_attempts,
        snapshot_verified_run_ids={
            str(attempt["run_id"]) for attempt in final_attempts.values()
        },
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


def _cost_attempt(**overrides: Any) -> dict[str, Any]:
    attempt: dict[str, Any] = {
        "run_id": "cost-run",
        "slot_id": "s01",
        "attempt": 1,
        "input_tokens": 100,
        "cached_input_tokens": 25,
        "output_tokens": 10,
        "reasoning_output_tokens": 4,
        "model_calls": 1,
        "failure_class": None,
        "token_usage_observations": _token_usage_observations(),
        "turn_protocol": "single-turn-required",
        "wall_clock_ms": 100,
        "rate_limited": False,
        "retry": False,
        "compaction_observed": False,
    }
    attempt.update(overrides)
    return attempt


def _bound_cost_aggregate(
    tmp_path: Path,
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    task_manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    slots, schedule_reasons = TOOL._validate_schedule(
        _bound_price_schedule(), task_manifest=task_manifest
    )
    assert schedule_reasons == []
    assert len(attempts) == len(slots)
    verdicts: dict[str, dict[str, Any]] = {}
    for index, (slot, attempt) in enumerate(zip(slots, attempts), 1):
        attempt.update(
            {
                "run_id": f"cost-r{index:02d}",
                "slot_id": slot["slot_id"],
                "attempt": 1,
                "benchmark_task_id": slot["benchmark_task_id"],
                "legacy_case": slot["legacy_case"],
                "case": slot["case"],
                "stage": slot["stage"],
                "requested_model": slot["requested_model"],
                "cache_condition": slot["cache_condition"],
                "price_version": slot["price_version"],
                "oracle_kind": slot["oracle_kind"],
                "arm": slot["arm"],
                "block_id": slot["block_id"],
                "block_order": slot["block_order"],
            }
        )
        verdicts[slot["slot_id"]] = {
            "oracle_kind": slot["oracle_kind"],
            "r1_detected": True,
            "findings": [],
            "reader_agreement": True,
        }
    manifest = _canonical(
        tmp_path / "bound-cost-manifest.json",
        {"schedule": {"path": "schedule.json", "sha256": "0" * 64}},
    )
    return TOOL._aggregate_verified(
        manifest,
        slots,
        attempts,
        verdicts,
        [],
        task_manifest=task_manifest,
        has_schedule_descriptor=True,
        validated_price_snapshot=slots.price_snapshot,
    )


def _cross_arm_cost_aggregate(
    tmp_path: Path,
    attempts: list[dict[str, Any]],
    *,
    has_schedule_descriptor: bool = True,
    material_manifest_sha256: str | None = "d" * 64,
) -> dict[str, Any]:
    task_manifest, schedule = _cross_arm_cost_fixture()
    slots, schedule_reasons = TOOL._validate_schedule(
        schedule, task_manifest=task_manifest
    )
    assert schedule_reasons == []
    assert len(attempts) == len(slots)
    verdicts: dict[str, dict[str, Any]] = {}
    for index, (slot, attempt) in enumerate(zip(slots, attempts), 1):
        attempt.update(
            {
                "run_id": f"cross-arm-cost-r{index:02d}",
                "slot_id": slot["slot_id"],
                "benchmark_task_id": slot["benchmark_task_id"],
                "legacy_case": slot["legacy_case"],
                "case": slot["case"],
                "stage": slot["stage"],
                "requested_model": slot["requested_model"],
                "cache_condition": slot["cache_condition"],
                "price_version": slot["price_version"],
                "oracle_kind": slot["oracle_kind"],
                "arm": slot["arm"],
                "block_id": slot["block_id"],
                "block_order": slot["block_order"],
            }
        )
        verdicts[slot["slot_id"]] = {
            "oracle_kind": slot["oracle_kind"],
            "r1_detected": True,
            "findings": [],
            "reader_agreement": True,
        }
    manifest = _canonical(
        tmp_path / "cross-arm-cost-manifest.json",
        {"schedule": {"path": "schedule.json", "sha256": "0" * 64}},
    )
    return TOOL._aggregate_verified(
        manifest,
        slots,
        attempts,
        verdicts,
        [],
        task_manifest=task_manifest,
        has_schedule_descriptor=has_schedule_descriptor,
        validated_price_snapshot=slots.price_snapshot,
        material_manifest_sha256=material_manifest_sha256,
    )


def _axis_cost(
    result: dict[str, Any],
    *,
    benchmark_task_id: str,
    arm: str,
) -> dict[str, Any]:
    return next(
        row
        for row in result["normalized_cost_axis_ledger"]
        if row["benchmark_task_id"] == benchmark_task_id and row["arm"] == arm
    )


def test_m10_cost_snapshot_loader_reads_and_validates_one_byte_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delegated = TOOL._read_frozen_repo_file
    reads: list[str] = []
    validated_trees: list[dict[str, Any]] = []
    cost_tree_ids: list[int] = []
    delegated_validate = TOOL.PRICE_SNAPSHOT.validate_price_snapshot
    delegated_cost = TOOL._normalized_cost_for_attempt

    def observed_read(relative_path: str, label: str) -> bytes:
        reads.append(relative_path)
        return delegated(relative_path, label)

    def observed_validate(value: Any) -> dict[str, Any]:
        validated = delegated_validate(value)
        validated_trees.append(validated)
        return validated

    def observed_cost(*args: Any, **kwargs: Any) -> dict[str, Any]:
        cost_tree_ids.append(id(kwargs["price_snapshot"]))
        return delegated_cost(*args, **kwargs)

    monkeypatch.setattr(TOOL, "_read_frozen_repo_file", observed_read)
    monkeypatch.setattr(
        TOOL.PRICE_SNAPSHOT, "validate_price_snapshot", observed_validate
    )
    monkeypatch.setattr(TOOL, "_normalized_cost_for_attempt", observed_cost)
    result = _bound_cost_aggregate(
        tmp_path, [_cost_attempt(), _cost_attempt()]
    )
    assert result["valid"] is True
    assert reads.count(_TEST_PRICE_SNAPSHOT_PATH) == 1
    assert reads.count(_TEST_PRICE_EXCERPT_PATH) == 1
    assert len(validated_trees) == 1
    assert cost_tree_ids == [id(validated_trees[0]), id(validated_trees[0])]


def test_p01_bound_cost_is_mapping_driven_decimal_partial_and_uncertified(
    tmp_path: Path,
) -> None:
    result = _bound_cost_aggregate(
        tmp_path,
        [_cost_attempt(), _cost_attempt()],
    )
    assert result["valid"] is True
    sol, luna = [
        row["normalized_cost"] for row in result["resource_ledger"]
    ]
    assert sol["accounted_amount"] == "0.00051000"
    assert luna["accounted_amount"] == "0.00002750"
    for cost in (sol, luna):
        assert cost["status"] == "partial"
        assert cost["token_availability"] == "observed"
        assert cost["currency"] == "USD"
        assert cost["price_unit"] == "per-million-tokens"
        assert cost["price_version"] == _TEST_PRICE_VERSION
        assert cost["coverage_status"] == "partial"
        assert cost["certification_status"] == "not-certified"
        assert cost["unaccounted_token_categories"] == ["cache_write"]
        assert "cache_write" in cost["unit_prices"]
        assert "cache_write" not in cost["components"]
        assert not any(
            isinstance(value, float)
            for value in _walk_json_values(cost)
        )
    assert sol["components"] == {
        "input": {
            "tokens": 75,
            "unit_price": "4",
            "amount": "0.00030000",
        },
        "cached_input": {
            "tokens": 25,
            "unit_price": "0.4",
            "amount": "0.00001000",
        },
        "output": {
            "tokens": 10,
            "unit_price": "20",
            "amount": "0.00020000",
        },
    }
    assert luna["components"] == {
        "input": {
            "tokens": 75,
            "unit_price": "0.2",
            "amount": "0.00001500",
        },
        "cached_input": {
            "tokens": 25,
            "unit_price": "0.02",
            "amount": "0.00000050",
        },
        "output": {
            "tokens": 10,
            "unit_price": "1.2",
            "amount": "0.00001200",
        },
    }
    assert {
        row["requested_model"]: (
            row["attempt_count"],
            row["unavailable_count"],
            row["not_incurred_count"],
            row["scheduled_attempt_count"],
        )
        for row in result["normalized_cost_axis_ledger"]
    } == {
        "gpt-5.6-sol": (1, 0, 0, 1),
        "gpt-5.6-luna": (1, 0, 0, 1),
    }
    assert all(
        isinstance(row["accounted_amount"], str)
        and row["coverage_status"] == "partial"
        and row["certification_status"] == "not-certified"
        for row in result["normalized_cost_axis_ledger"]
    )
    assert {
        row["requested_model"]: row["accounted_amount"]
        for row in result["normalized_cost_axis_ledger"]
    } == {
        "gpt-5.6-sol": "0.00051000",
        "gpt-5.6-luna": "0.00002750",
    }


def _walk_json_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        return [value, *[item for child in value.values() for item in _walk_json_values(child)]]
    if isinstance(value, list):
        return [value, *[item for child in value for item in _walk_json_values(child)]]
    return [value]


def test_cross_arm_comparability_is_self_describing_and_model_normalized(
    tmp_path: Path,
) -> None:
    result = _cross_arm_cost_aggregate(
        tmp_path, [_cost_attempt() for _ in range(6)]
    )
    assert result["valid"] is True
    resources = result["resource_ledger"]
    assert {(row["benchmark_task_id"], row["stage"]) for row in resources} == {
        ("alpha", "stage-1"),
        ("beta", "stage-2"),
    }
    assert {
        (
            row["normalized_cost"]["comparability"]["basis_key"][
                "comparison_scope"
            ]["benchmark_task_id"],
            row["normalized_cost"]["comparability"]["basis_key"][
                "comparison_scope"
            ]["stage"],
        )
        for row in resources
    } == {("alpha", "stage-1"), ("beta", "stage-2")}

    alpha_max = resources[0]
    alpha_high = resources[1]
    assert (alpha_max["arm"], alpha_high["arm"]) == ("max", "high")
    max_cost = alpha_max["normalized_cost"]
    high_cost = alpha_high["normalized_cost"]
    max_comparability = max_cost["comparability"]
    high_comparability = high_cost["comparability"]
    assert max_cost["unit_prices"] != high_cost["unit_prices"]
    assert max_comparability["basis_key"] == high_comparability["basis_key"]
    assert (
        max_comparability["accounted_total_key"]
        == high_comparability["accounted_total_key"]
    )
    assert max_comparability["accounted_total_key"] == {
        "attempt_count": 1,
        "unavailable_count": 0,
        "not_incurred_count": 0,
        "scheduled_attempt_count": 1,
        "pair_units_by_status": {
            "observed": [{"block_id": "b02", "attempt": 1}],
            "unavailable": [],
            "not-incurred": [],
        },
    }
    basis_key = max_comparability["basis_key"]
    assert basis_key["comparison_scope"] == {
        "benchmark_task_id": "alpha",
        "stage": "stage-1",
        "cache_condition": None,
    }
    assert basis_key["comparison_universe"] == {
        "material_manifest_sha256": "d" * 64,
    }
    basis_tree_keys = {
        key
        for value in _walk_json_values(basis_key)
        if isinstance(value, dict)
        for key in value
    }
    assert {
        "requested_model",
        "unit_prices",
        "arm",
        "accounted_amount",
    }.isdisjoint(basis_tree_keys)
    assert "partial accounted component totals" in max_comparability["rule"]
    assert "per-attempt averages" in max_comparability["rule"]
    assert "complete costs" in max_comparability["rule"]
    assert "actual billed amounts" in max_comparability["rule"]

    max_axis = _axis_cost(result, benchmark_task_id="alpha", arm="max")
    high_axis = _axis_cost(result, benchmark_task_id="alpha", arm="high")
    assert max_axis["comparability"]["basis_key"] == high_axis["comparability"][
        "basis_key"
    ]
    assert (
        max_axis["comparability"]["accounted_total_key"]
        == high_axis["comparability"]["accounted_total_key"]
    )
    for axis in (max_axis, high_axis):
        total_key = axis["comparability"]["accounted_total_key"]
        assert total_key == {
            "attempt_count": 2,
            "unavailable_count": 0,
            "not_incurred_count": 0,
            "scheduled_attempt_count": 2,
            "pair_units_by_status": {
                "observed": [
                    {"block_id": "b01", "attempt": 1},
                    {"block_id": "b02", "attempt": 1},
                ],
                "unavailable": [],
                "not-incurred": [],
            },
        }
        assert {
            key: axis[key]
            for key in (
                "attempt_count",
                "unavailable_count",
                "not_incurred_count",
                "scheduled_attempt_count",
            )
        } == {
            key: total_key[key]
            for key in (
                "attempt_count",
                "unavailable_count",
                "not_incurred_count",
                "scheduled_attempt_count",
            )
        }


def test_equal_counts_with_swapped_pair_units_are_not_comparable(
    tmp_path: Path,
) -> None:
    unavailable = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    attempts = [
        _cost_attempt(),
        _cost_attempt(**unavailable),
        _cost_attempt(**unavailable),
        _cost_attempt(),
        _cost_attempt(),
        _cost_attempt(),
    ]
    result = _cross_arm_cost_aggregate(tmp_path, attempts)
    max_axis = _axis_cost(result, benchmark_task_id="alpha", arm="max")
    high_axis = _axis_cost(result, benchmark_task_id="alpha", arm="high")
    max_comparability = max_axis["comparability"]
    high_comparability = high_axis["comparability"]
    assert max_comparability["basis_key"] == high_comparability["basis_key"]
    max_total = max_comparability["accounted_total_key"]
    high_total = high_comparability["accounted_total_key"]
    assert (
        max_total["attempt_count"],
        max_total["unavailable_count"],
        max_total["not_incurred_count"],
        max_total["scheduled_attempt_count"],
    ) == (1, 1, 0, 2)
    assert (
        high_total["attempt_count"],
        high_total["unavailable_count"],
        high_total["not_incurred_count"],
        high_total["scheduled_attempt_count"],
    ) == (1, 1, 0, 2)
    assert max_total["pair_units_by_status"] == {
        "observed": [{"block_id": "b02", "attempt": 1}],
        "unavailable": [{"block_id": "b01", "attempt": 1}],
        "not-incurred": [],
    }
    assert high_total["pair_units_by_status"] == {
        "observed": [{"block_id": "b01", "attempt": 1}],
        "unavailable": [{"block_id": "b02", "attempt": 1}],
        "not-incurred": [],
    }
    assert max_total != high_total
    assert all(
        "comparability" in row["normalized_cost"]
        for row in result["resource_ledger"]
    )


def test_attempt_number_distinguishes_equal_count_pair_unit_identities(
    tmp_path: Path,
) -> None:
    unavailable = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    result = _cross_arm_cost_aggregate(
        tmp_path,
        [
            _cost_attempt(attempt=2),
            _cost_attempt(attempt=1),
            _cost_attempt(attempt=1, **unavailable),
            _cost_attempt(attempt=2, **unavailable),
            _cost_attempt(),
            _cost_attempt(),
        ],
    )
    max_total = _axis_cost(
        result, benchmark_task_id="alpha", arm="max"
    )["comparability"]["accounted_total_key"]
    high_total = _axis_cost(
        result, benchmark_task_id="alpha", arm="high"
    )["comparability"]["accounted_total_key"]
    count_keys = (
        "attempt_count",
        "unavailable_count",
        "not_incurred_count",
        "scheduled_attempt_count",
    )
    assert tuple(max_total[key] for key in count_keys) == (1, 1, 0, 2)
    assert tuple(high_total[key] for key in count_keys) == (1, 1, 0, 2)
    assert max_total["pair_units_by_status"] == {
        "observed": [{"block_id": "b02", "attempt": 2}],
        "unavailable": [{"block_id": "b01", "attempt": 1}],
        "not-incurred": [],
    }
    assert high_total["pair_units_by_status"] == {
        "observed": [{"block_id": "b02", "attempt": 1}],
        "unavailable": [{"block_id": "b01", "attempt": 2}],
        "not-incurred": [],
    }
    assert max_total != high_total


def test_distinct_non_null_manifest_digests_propagate_to_every_cost_row(
    tmp_path: Path,
) -> None:
    first = _cross_arm_cost_aggregate(
        tmp_path,
        [_cost_attempt() for _ in range(6)],
        material_manifest_sha256="d" * 64,
    )
    second = _cross_arm_cost_aggregate(
        tmp_path,
        [_cost_attempt() for _ in range(6)],
        material_manifest_sha256="e" * 64,
    )

    first_universes = [
        row["normalized_cost"]["comparability"]["basis_key"][
            "comparison_universe"
        ]
        for row in first["resource_ledger"]
    ] + [
        row["comparability"]["basis_key"]["comparison_universe"]
        for row in first["normalized_cost_axis_ledger"]
    ]
    second_universes = [
        row["normalized_cost"]["comparability"]["basis_key"][
            "comparison_universe"
        ]
        for row in second["resource_ledger"]
    ] + [
        row["comparability"]["basis_key"]["comparison_universe"]
        for row in second["normalized_cost_axis_ledger"]
    ]
    assert first_universes
    assert second_universes
    assert all(
        universe == {"material_manifest_sha256": "d" * 64}
        for universe in first_universes
    )
    assert all(
        universe == {"material_manifest_sha256": "e" * 64}
        for universe in second_universes
    )
    assert first_universes[0] != second_universes[0]


def test_comparability_rule_preserves_polarity_and_null_locality_branch(
    tmp_path: Path,
) -> None:
    non_null = _cross_arm_cost_aggregate(
        tmp_path,
        [_cost_attempt() for _ in range(6)],
        material_manifest_sha256="e" * 64,
    )
    null = _bound_cost_aggregate(
        tmp_path, [_cost_attempt(), _cost_attempt()]
    )
    base_rule = (
        "basis_key and accounted_total_key must both match exactly to compare "
        "partial accounted component totals; this does not establish "
        "comparability of per-attempt averages, complete costs, or actual "
        "billed amounts"
    )
    null_locality = (
        "; when comparison_universe.material_manifest_sha256 is null, "
        "comparison is limited to rows in the same aggregate result"
    )
    non_null_rules = {
        row["normalized_cost"]["comparability"]["rule"]
        for row in non_null["resource_ledger"]
    } | {
        row["comparability"]["rule"]
        for row in non_null["normalized_cost_axis_ledger"]
    }
    null_rules = {
        row["normalized_cost"]["comparability"]["rule"]
        for row in null["resource_ledger"]
    } | {
        row["comparability"]["rule"]
        for row in null["normalized_cost_axis_ledger"]
    }
    assert non_null_rules == {base_rule}
    assert null_rules == {base_rule + null_locality}


def test_comparability_presence_and_mismatch_do_not_change_acceptance(
    tmp_path: Path,
) -> None:
    observed_attempts = [_cost_attempt() for _ in range(6)]
    matching = _cross_arm_cost_aggregate(tmp_path, observed_attempts)

    zero_tokens = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    mismatching = _cross_arm_cost_aggregate(
        tmp_path,
        [_cost_attempt(**zero_tokens)]
        + [_cost_attempt() for _ in range(5)],
    )
    not_incurred = _cross_arm_cost_aggregate(
        tmp_path,
        [
            _cost_attempt(
                **zero_tokens,
                model_calls=0,
                prelaunch_failure={"kind": "prelaunch-exception"},
            )
        ]
        + [_cost_attempt() for _ in range(5)],
    )
    without_declaration = _cross_arm_cost_aggregate(
        tmp_path,
        [_cost_attempt() for _ in range(6)],
        has_schedule_descriptor=False,
    )

    assert all(
        "comparability" in row["normalized_cost"]
        for row in matching["resource_ledger"]
    )
    assert (
        _axis_cost(mismatching, benchmark_task_id="alpha", arm="max")[
            "comparability"
        ]["accounted_total_key"]
        != _axis_cost(mismatching, benchmark_task_id="alpha", arm="high")[
            "comparability"
        ]["accounted_total_key"]
    )
    not_incurred_cost = not_incurred["resource_ledger"][0]["normalized_cost"]
    assert not_incurred_cost["token_availability"] == "not-incurred"
    assert not_incurred_cost["comparability"]["accounted_total_key"] == {
        "attempt_count": 0,
        "unavailable_count": 0,
        "not_incurred_count": 1,
        "scheduled_attempt_count": 1,
        "pair_units_by_status": {
            "observed": [],
            "unavailable": [],
            "not-incurred": [{"block_id": "b02", "attempt": 1}],
        },
    }
    not_incurred_axis = _axis_cost(
        not_incurred, benchmark_task_id="alpha", arm="max"
    )["comparability"]["accounted_total_key"]
    assert not_incurred_axis == {
        "attempt_count": 1,
        "unavailable_count": 0,
        "not_incurred_count": 1,
        "scheduled_attempt_count": 2,
        "pair_units_by_status": {
            "observed": [{"block_id": "b01", "attempt": 1}],
            "unavailable": [],
            "not-incurred": [{"block_id": "b02", "attempt": 1}],
        },
    }
    assert "normalized_cost_axis_ledger" not in without_declaration
    assert all(
        "normalized_cost" not in row
        for row in without_declaration["resource_ledger"]
    )
    assert [
        (
            result["valid"],
            result["failure_reasons"],
            result["experiment_complete"],
        )
        for result in (
            matching,
            mismatching,
            not_incurred,
            without_declaration,
        )
    ] == [(True, [], True)] * 4

    malformed = _cross_arm_cost_aggregate(
        tmp_path,
        [_cost_attempt(input_tokens=-1)]
        + [_cost_attempt() for _ in range(5)],
    )
    assert "comparability" in malformed["resource_ledger"][0]["normalized_cost"]
    assert (
        malformed["valid"],
        malformed["failure_reasons"],
        malformed["experiment_complete"],
    ) == (
        False,
        [
            "cross-arm-cost-r01: normalized cost unavailable: "
            "normalized cost input_tokens is negative"
        ],
        False,
    )


def test_final_cost_artifact_comparability_contains_no_float_and_keeps_rounding(
    tmp_path: Path,
) -> None:
    result = _cross_arm_cost_aggregate(
        tmp_path, [_cost_attempt() for _ in range(6)]
    )
    final_values = _walk_json_values(result)
    comparability_trees = [
        value
        for value in final_values
        if isinstance(value, dict)
        and set(value) == {"rule", "basis_key", "accounted_total_key"}
    ]
    assert len(comparability_trees) == (
        len(result["resource_ledger"])
        + len(result["normalized_cost_axis_ledger"])
    )
    assert not any(
        isinstance(value, float)
        for tree in comparability_trees
        for value in _walk_json_values(tree)
    )
    for resource in result["resource_ledger"]:
        cost = resource["normalized_cost"]
        assert cost["rounding"] == {
            "decimal_places": 8,
            "mode": "ROUND_HALF_EVEN",
        }
        assert type(cost["rounding"]["decimal_places"]) is int
        nested_rounding = cost["comparability"]["basis_key"][
            "accounting_basis"
        ]["rounding"]
        assert nested_rounding == cost["rounding"]
        assert type(nested_rounding["decimal_places"]) is int


def test_null_comparison_universe_is_limited_to_same_aggregate_result(
    tmp_path: Path,
) -> None:
    result = _bound_cost_aggregate(
        tmp_path, [_cost_attempt(), _cost_attempt()]
    )
    comparability_trees = [
        row["normalized_cost"]["comparability"]
        for row in result["resource_ledger"]
    ] + [row["comparability"] for row in result["normalized_cost_axis_ledger"]]
    for comparability in comparability_trees:
        assert comparability["basis_key"]["comparison_universe"] == {
            "material_manifest_sha256": None,
        }
        assert "same aggregate result" in comparability["rule"]


def test_m01_unavailable_zero_tokens_never_enter_cost_denominator(
    tmp_path: Path,
) -> None:
    unavailable = _cost_attempt(
        input_tokens=0,
        cached_input_tokens=0,
        output_tokens=0,
        reasoning_output_tokens=0,
    )
    result = _bound_cost_aggregate(tmp_path, [unavailable, _cost_attempt()])
    first = result["resource_ledger"][0]["normalized_cost"]
    assert first["token_availability"] == "unavailable"
    assert "accounted_amount" not in first
    assert {
        row["requested_model"]: (
            row["attempt_count"],
            row["unavailable_count"],
            row["not_incurred_count"],
            row["scheduled_attempt_count"],
        )
        for row in result["normalized_cost_axis_ledger"]
    } == {
        "gpt-5.6-sol": (0, 1, 0, 1),
        "gpt-5.6-luna": (1, 0, 0, 1),
    }
    assert result["valid"] is True
    assert result["failure_reasons"] == []


def test_m02_prelaunch_zero_tokens_are_not_incurred_and_not_counted(
    tmp_path: Path,
) -> None:
    prelaunch = _cost_attempt(
        input_tokens=0,
        cached_input_tokens=0,
        output_tokens=0,
        reasoning_output_tokens=0,
        model_calls=0,
        prelaunch_failure={"kind": "prelaunch-exception"},
    )
    result = _bound_cost_aggregate(tmp_path, [prelaunch, _cost_attempt()])
    first = result["resource_ledger"][0]["normalized_cost"]
    assert first["token_availability"] == "not-incurred"
    assert "accounted_amount" not in first
    assert {
        row["requested_model"]: (
            row["attempt_count"],
            row["unavailable_count"],
            row["not_incurred_count"],
            row["scheduled_attempt_count"],
        )
        for row in result["normalized_cost_axis_ledger"]
    } == {
        "gpt-5.6-sol": (0, 0, 1, 1),
        "gpt-5.6-luna": (1, 0, 0, 1),
    }


@pytest.mark.parametrize("field", (*TOOL._COST_TOKEN_FIELDS, "model_calls"))
def test_m18_prelaunch_marker_never_hides_nonzero_accounting(
    tmp_path: Path,
    field: str,
) -> None:
    prelaunch = _cost_attempt(
        input_tokens=0,
        cached_input_tokens=0,
        output_tokens=0,
        reasoning_output_tokens=0,
        model_calls=0,
        prelaunch_failure={"kind": "prelaunch-exception"},
    )
    prelaunch[field] = 1
    result = _bound_cost_aggregate(tmp_path, [prelaunch, _cost_attempt()])
    first = result["resource_ledger"][0]["normalized_cost"]
    assert first["token_availability"] == "unavailable"
    assert "accounted_amount" not in first
    assert result["valid"] is False
    assert len(result["failure_reasons"]) == 1
    assert "not-launched" in result["failure_reasons"][0]
    assert field in result["failure_reasons"][0]


def test_replay_failure_tokens_are_unavailable_and_not_counted(
    tmp_path: Path,
) -> None:
    replay_failed = _cost_attempt(
        input_tokens=None,
        cached_input_tokens=None,
        output_tokens=None,
        reasoning_output_tokens=None,
        failure_reasons=["replay failed: frozen receipt mismatch"],
    )
    result = _bound_cost_aggregate(
        tmp_path, [replay_failed, _cost_attempt()]
    )
    first = result["resource_ledger"][0]["normalized_cost"]
    assert first["token_availability"] == "unavailable"
    assert first["failure_reason"] == "receipt replay failed"
    assert "accounted_amount" not in first
    assert {
        row["requested_model"]: (
            row["attempt_count"], row["unavailable_count"]
        )
        for row in result["normalized_cost_axis_ledger"]
    } == {"gpt-5.6-sol": (0, 1), "gpt-5.6-luna": (1, 0)}
    assert result["valid"] is True
    assert result["failure_reasons"] == []


def test_m17_m21_p05_unavailable_cost_is_noncertifying_and_denominators_are_explicit(
    tmp_path: Path,
) -> None:
    unavailable = _cost_attempt(
        input_tokens=0,
        cached_input_tokens=0,
        output_tokens=0,
        reasoning_output_tokens=0,
    )
    result = _bound_cost_aggregate(tmp_path, [unavailable, _cost_attempt()])
    assert result["valid"] is True
    assert result["failure_reasons"] == []
    assert "accounted_amount" not in result["resource_ledger"][0][
        "normalized_cost"
    ]
    assert {
        row["requested_model"]: {
            key: row[key]
            for key in (
                "attempt_count",
                "unavailable_count",
                "not_incurred_count",
                "scheduled_attempt_count",
            )
        }
        for row in result["normalized_cost_axis_ledger"]
    } == {
        "gpt-5.6-sol": {
            "attempt_count": 0,
            "unavailable_count": 1,
            "not_incurred_count": 0,
            "scheduled_attempt_count": 1,
        },
        "gpt-5.6-luna": {
            "attempt_count": 1,
            "unavailable_count": 0,
            "not_incurred_count": 0,
            "scheduled_attempt_count": 1,
        },
    }


def test_f7_malformed_cost_input_remains_materially_invalid(
    tmp_path: Path,
) -> None:
    malformed = _cost_attempt(input_tokens=-1)
    result = _bound_cost_aggregate(tmp_path, [malformed, _cost_attempt()])
    first = result["resource_ledger"][0]["normalized_cost"]
    assert first["token_availability"] == "unavailable"
    assert "accounted_amount" not in first
    assert result["valid"] is False
    assert result["failure_reasons"] == [
        "cost-r01: normalized cost unavailable: "
        "normalized cost input_tokens is negative"
    ]


@pytest.mark.parametrize("field", TOOL._COST_TOKEN_FIELDS)
@pytest.mark.parametrize(
    "replacement",
    (pytest.param(None, id="missing"), pytest.param(True, id="bool"),
     pytest.param("1", id="string"), pytest.param(-1, id="negative")),
)
def test_cost_token_field_unavailable_matrix(
    field: str,
    replacement: Any,
) -> None:
    snapshot = TOOL._load_frozen_price_snapshot_for_cost()
    attempt = _cost_attempt()
    if replacement is None:
        del attempt[field]
    else:
        attempt[field] = replacement
    with pytest.raises(TOOL.ValidationError, match=field):
        TOOL._normalized_cost_for_attempt(
            attempt,
            requested_model="gpt-5.6-sol",
            price_version=_TEST_PRICE_VERSION,
            price_snapshot=snapshot,
        )


def test_m03_cost_json_tree_contains_no_float() -> None:
    snapshot = TOOL._load_frozen_price_snapshot_for_cost()
    for category in snapshot["sku_mapping"]["gpt-5.6-sol"]["prices"]:
        snapshot["sku_mapping"]["gpt-5.6-sol"]["prices"][category] = "1"
    cost = TOOL._normalized_cost_for_attempt(
        _cost_attempt(
            input_tokens=9_007_199_254_740_993,
            cached_input_tokens=0,
            output_tokens=1,
            reasoning_output_tokens=0,
        ),
        requested_model="gpt-5.6-sol",
        price_version=_TEST_PRICE_VERSION,
        price_snapshot=snapshot,
    )
    assert cost["components"]["input"]["amount"] == "9007199254.74099300"
    assert cost["accounted_amount"] == "9007199254.74099400"
    assert not any(isinstance(value, float) for value in _walk_json_values(cost))


def test_m04_cost_rounding_is_eight_place_half_even() -> None:
    assert TOOL._format_cost_amount(TOOL.Decimal("0.000000005")) == "0.00000000"
    assert TOOL._format_cost_amount(TOOL.Decimal("0.000000015")) == "0.00000002"
    assert TOOL._format_cost_amount(TOOL.Decimal("1")) == "1.00000000"
    snapshot = TOOL._load_frozen_price_snapshot_for_cost()
    for category in snapshot["sku_mapping"]["gpt-5.6-sol"]["prices"]:
        snapshot["sku_mapping"]["gpt-5.6-sol"]["prices"][category] = "0.005"
    cost = TOOL._normalized_cost_for_attempt(
        _cost_attempt(
            input_tokens=1,
            cached_input_tokens=0,
            output_tokens=1,
            reasoning_output_tokens=0,
        ),
        requested_model="gpt-5.6-sol",
        price_version=_TEST_PRICE_VERSION,
        price_snapshot=snapshot,
    )
    assert cost["components"]["input"]["amount"] == "0.00000000"
    assert cost["components"]["output"]["amount"] == "0.00000000"
    assert cost["accounted_amount"] == "0.00000001"


def test_m05_reasoning_tokens_are_validated_but_never_added_to_output_cost() -> None:
    snapshot = TOOL._load_frozen_price_snapshot_for_cost()
    costs = [
        TOOL._normalized_cost_for_attempt(
            _cost_attempt(reasoning_output_tokens=reasoning),
            requested_model="gpt-5.6-sol",
            price_version=_TEST_PRICE_VERSION,
            price_snapshot=snapshot,
        )
        for reasoning in (0, 10)
    ]
    assert costs[0]["accounted_amount"] == costs[1]["accounted_amount"]
    assert costs[0]["components"]["output"]["tokens"] == 10
    with pytest.raises(
        TOOL.ValidationError, match="reasoning_output_tokens exceeds output_tokens"
    ):
        TOOL._normalized_cost_for_attempt(
            _cost_attempt(reasoning_output_tokens=11),
            requested_model="gpt-5.6-sol",
            price_version=_TEST_PRICE_VERSION,
            price_snapshot=snapshot,
        )


def test_m06_cached_input_cannot_exceed_input_for_cost() -> None:
    snapshot = TOOL._load_frozen_price_snapshot_for_cost()
    with pytest.raises(
        TOOL.ValidationError, match="cached_input_tokens exceeds input_tokens"
    ) as caught:
        TOOL._normalized_cost_for_attempt(
            _cost_attempt(input_tokens=100, cached_input_tokens=101),
            requested_model="gpt-5.6-sol",
            price_version=_TEST_PRICE_VERSION,
            price_snapshot=snapshot,
        )
    assert caught.value.reasons == (
        "normalized cost cached_input_tokens exceeds input_tokens",
    )


def test_m07_cache_write_is_unaccounted_and_never_a_zero_component() -> None:
    snapshot = TOOL._load_frozen_price_snapshot_for_cost()
    costs = {
        model: TOOL._normalized_cost_for_attempt(
            _cost_attempt(),
            requested_model=model,
            price_version=_TEST_PRICE_VERSION,
            price_snapshot=snapshot,
        )
        for model in ("gpt-5.6-sol", "gpt-5.6-luna")
    }
    assert costs["gpt-5.6-sol"]["unit_prices"]["cache_write"] == "5"
    assert costs["gpt-5.6-luna"]["unit_prices"]["cache_write"] == "0.25"
    assert (
        TOOL.Decimal(costs["gpt-5.6-sol"]["unit_prices"]["cache_write"])
        / TOOL.Decimal(costs["gpt-5.6-luna"]["unit_prices"]["cache_write"])
    ) == 20
    for cost in costs.values():
        assert cost["unaccounted_token_categories"] == ["cache_write"]
        assert "cache_write" not in cost["components"]
        assert set(cost["components"]) == {"input", "cached_input", "output"}


def test_m08_p02_p04_null_v3_and_legacy_emit_no_cost_keys(
    tmp_path: Path,
) -> None:
    task_manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    schedule = _bound_price_schedule()
    for slot in schedule["slots"]:
        slot["price_version"] = None
    slots, reasons = TOOL._validate_schedule(schedule, task_manifest=task_manifest)
    assert reasons == []
    attempts = [_cost_attempt(), _cost_attempt()]
    for slot, attempt in zip(slots, attempts):
        attempt.update({"slot_id": slot["slot_id"], "run_id": slot["slot_id"]})
    v3 = TOOL._aggregate_verified(
        _canonical(tmp_path / "null-v3.json", {"schedule": {}}),
        slots,
        attempts,
        {
            slot["slot_id"]: {"oracle_kind": slot["oracle_kind"]}
            for slot in slots
        },
        [],
        task_manifest=task_manifest,
    )
    legacy_slots, legacy_attempts, legacy_verdicts = _aggregate_rows()
    legacy = TOOL._aggregate_verified(
        _canonical(tmp_path / "legacy-v2.json", {"schedule": {}}),
        legacy_slots,
        legacy_attempts,
        legacy_verdicts,
        [],
    )
    for result in (v3, legacy):
        assert "normalized_cost_axis_ledger" not in result
        assert all(
            "normalized_cost" not in row for row in result["resource_ledger"]
        )

    def packet_source(
        name: str,
        source_schedule: dict[str, Any],
        source_slots: list[dict[str, Any]],
        source_manifest: dict[str, Any],
    ) -> Path:
        attempts: list[dict[str, Any]] = []
        for index, slot in enumerate(source_slots, 1):
            output = tmp_path / f"{name}-output-{index:02d}.md"
            output.write_text(_long_output(), encoding="utf-8")
            attempts.append(
                {
                    "slot_id": slot["slot_id"],
                    "attempt": 1,
                    "run_id": f"{name}-r{index:02d}",
                    "output": _descriptor(output, tmp_path),
                }
            )
        source_schedule["task_manifest_sha256"] = TOOL._task_manifest_sha256(
            source_manifest
        )
        return _canonical(
            tmp_path / f"{name}-source.json",
            {
                "task_manifest_sha256": TOOL._task_manifest_sha256(
                    source_manifest
                ),
                "schedule": source_schedule,
                "attempts": attempts,
            },
        )

    null_schedule = copy.deepcopy(schedule)
    null_source = packet_source(
        "null-v3", null_schedule, null_schedule["slots"], task_manifest
    )
    null_packets = TOOL.make_packets(
        null_source,
        tmp_path / "null-v3-packets",
        tmp_path / "null-v3-custodian",
        task_manifest=task_manifest,
    )
    assert null_packets["packet_count"] == 2

    legacy_rows: list[dict[str, Any]] = []
    slot_number = 0
    block_number = 0
    for case, pairs in (("POS", 3), ("NEG", 2)):
        for _ in range(pairs):
            block_number += 1
            for block_order, arm in enumerate(("max", "high"), 1):
                slot_number += 1
                legacy_rows.append(
                    {
                        "slot_id": f"legacy-s{slot_number:02d}",
                        "case": case,
                        "arm": arm,
                        "block_id": f"legacy-b{block_number:02d}",
                        "block_order": block_order,
                        "prompt_sha256": "a" * 64,
                        "snapshot_manifest_sha256": "b" * 64,
                        "submodule_manifest_sha256": "c" * 64,
                    }
                )
    legacy_schedule = {"schema_version": 2, "slots": legacy_rows}
    legacy_source = packet_source(
        "legacy-v2", legacy_schedule, legacy_rows, TOOL.TASK_MANIFEST
    )
    legacy_packets = TOOL.make_packets(
        legacy_source,
        tmp_path / "legacy-v2-packets",
        tmp_path / "legacy-v2-custodian",
    )
    assert legacy_packets["packet_count"] == 10

    snapshot = TOOL._load_frozen_price_snapshot_for_cost()
    with pytest.raises(TOOL.ValidationError, match="price_version"):
        TOOL._normalized_cost_for_attempt(
            _cost_attempt(),
            requested_model="gpt-5.6-sol",
            price_version=None,
            price_snapshot=snapshot,
        )


def test_schedule_descriptor_absence_emits_no_cost_keys(tmp_path: Path) -> None:
    task_manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    slots, reasons = TOOL._validate_schedule(
        _bound_price_schedule(), task_manifest=task_manifest
    )
    assert reasons == []
    attempts = [_cost_attempt(), _cost_attempt()]
    for slot, attempt in zip(slots, attempts):
        attempt.update({"slot_id": slot["slot_id"], "run_id": slot["slot_id"]})
    result = TOOL._aggregate_verified(
        _canonical(tmp_path / "descriptorless.json", {}),
        slots,
        attempts,
        {
            slot["slot_id"]: {"oracle_kind": slot["oracle_kind"]}
            for slot in slots
        },
        [],
        task_manifest=task_manifest,
    )
    assert "normalized_cost_axis_ledger" not in result
    assert all("normalized_cost" not in row for row in result["resource_ledger"])


def test_f4_aggregate_uses_loaded_descriptor_state_without_manifest_reread(
    tmp_path: Path,
) -> None:
    task_manifest = _synthetic_task_manifest(
        (("alpha", "POS", "positive", "alpha-finding"),)
    )
    slots, reasons = TOOL._validate_schedule(
        _bound_price_schedule(), task_manifest=task_manifest
    )
    assert reasons == []
    attempts = [_cost_attempt(), _cost_attempt()]
    for slot, attempt in zip(slots, attempts):
        attempt.update({"slot_id": slot["slot_id"], "run_id": slot["slot_id"]})
    manifest = _canonical(tmp_path / "material.json", {"schedule": {}})
    initial_manifest_sha256 = TOOL._sha256(manifest.read_bytes())
    slots.has_material_schedule_descriptor = True
    slots.material_manifest_sha256 = initial_manifest_sha256
    # Simulate a later path observation with the descriptor gone.  The
    # aggregate must use the already validated state and tree.
    _canonical(manifest, {})
    result = TOOL._aggregate_verified(
        manifest,
        slots,
        attempts,
        {
            slot["slot_id"]: {"oracle_kind": slot["oracle_kind"]}
            for slot in slots
        },
        [],
        task_manifest=task_manifest,
    )
    assert result["valid"] is True
    assert result["manifest_sha256"] == initial_manifest_sha256
    assert len(result["normalized_cost_axis_ledger"]) == 2
    assert all(
        "normalized_cost" in row for row in result["resource_ledger"]
    )


def test_m09_unknown_model_has_one_direct_cost_rejection() -> None:
    snapshot = TOOL._load_frozen_price_snapshot_for_cost()
    with pytest.raises(TOOL.ValidationError) as caught:
        TOOL._normalized_cost_for_attempt(
            _cost_attempt(),
            requested_model="gpt-5.6-unknown",
            price_version=_TEST_PRICE_VERSION,
            price_snapshot=snapshot,
        )
    assert caught.value.reasons == (
        "normalized cost requested model has no frozen SKU: gpt-5.6-unknown",
    )


@pytest.mark.parametrize(
    "mutation",
    ("operation", "reasoning-field", "nonpositive-price"),
)
def test_cost_constant_false_rejections_are_owned_by_snapshot_validator(
    mutation: str,
) -> None:
    value = json.loads((_ROOT / _TEST_PRICE_SNAPSHOT_PATH).read_bytes())
    sol = value["sku_mapping"]["gpt-5.6-sol"]
    if mutation == "operation":
        sol["receipt_token_mapping"]["output"]["operation"] = "unsupported"
    elif mutation == "reasoning-field":
        sol["receipt_token_mapping"]["output"]["receipt_fields"] = [
            "reasoning_output_tokens"
        ]
    else:
        sol["prices"]["input"] = "0"
    with pytest.raises(TOOL.PRICE_SNAPSHOT.PriceSnapshotError):
        TOOL.PRICE_SNAPSHOT.validate_price_snapshot(value)


from orchestrator.tests.growth_test_holds import enforce_held_functions  # noqa: E402
enforce_held_functions(globals(), __file__, plain_runner="pytest-delegating")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
