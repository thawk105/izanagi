#!/usr/bin/env python3
"""T-244 の事前登録済み変異を逐次注入し、検査後に復元する。"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import datetime as dt
import difflib
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any


WAVE = "T-244"
TARGET_REL = Path("orchestrator/campaign/p3_autonomous_workload_trial.py")
TEST_REL = Path("orchestrator/tests/test_p3_autonomous_workload_trial.py")
TEST_TIMEOUT_S = 1800
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
RECEIPT_LINE_RE = re.compile(
    r"^\[Pegasus dispatch\] receipt を (.+) へ保存しました \(child rc=(-?\d+)\)$"
)
JOB_STDOUT_RE = re.compile(r"^izdw-[A-Za-z0-9._-]+\.o\S+$")
LEDGER_SCHEMA = "izanagi-dev-wave-mutation/v2"


class HarnessError(RuntimeError):
    """変異検査の信頼性を維持できない場合の fail-closed 停止。"""


class SignalAbort(BaseException):
    """SIGINT/SIGTERM を通常の unwind に変換し、変異の finally を通す。"""

    def __init__(self, signum: int) -> None:
        self.signum = signum
        super().__init__(f"signal {signum}")


@dataclasses.dataclass(frozen=True)
class Mutation:
    id: str
    kind: str
    old: str
    new: str
    expected_nodes: tuple[str, ...]


def _node(name: str) -> str:
    return f"{TEST_REL.as_posix()}::{name}"


BOUNDARY = _node("test_generation_budget_boundary_at_ratified_launch")
CLI_DEFAULT = _node("test_main_default_generation_budget_is_one")
FIXTURE_ACCEPT = _node("test_fixture_trial_runs_ycsb_abc_and_binds_descriptor")
HEADLESS_BUILD_ACCEPT = _node("test_main_accepts_claude_headless_build_at_cli_gate")
HEADLESS_NO_BUILD_ACCEPT = _node(
    "test_main_accepts_claude_headless_no_build_at_cli_gate"
)
ACTUAL_EXISTING_STATE = _node(
    "test_run_workload_rejects_actual_existing_campaign_state"
)
MALFORMED_CHECKPOINT = _node("test_freshness_wraps_malformed_json_with_cause")
LEAKING_CHECKPOINT = _node("test_freshness_wraps_delta_pct_leak_with_cause")
ATTRIBUTE_ERROR_PASSTHROUGH = _node(
    "test_freshness_does_not_reclassify_attribute_error"
)


V11_OLD = '''    _assert_fresh_campaign_state(layout)
    perf = _perf_for(flags)
    result: dict[str, Any] = {
        "workload": workload,
        "workload_flags": dict(flags),
        "descriptor": descriptor,
        "descriptor_binding": descriptor_record,
        "campaign_id": str(trigger.ident.campaign_id(cfg)),
        "campaign_root": layout.root,
        "generations": [],
        "stop_reason": "fixed-generation-budget",
    }
    prior_reverse: bool | None = None
    current_metrics = {
        "throughput_ops_sec": None,
        "abort_rate_pct": None,
        "latency_ns": None,
        "llc_miss_rate": None,
        "ipc": None,
    }

    for generation in range(1, generations + 1):
        if time.monotonic() - started_monotonic >= max_wall_s:
            result["stop_reason"] = "supervisor-wall-budget"
            break
        generation_record: dict[str, Any] = {"generation": generation, "roles": {}}
        common = _common_payload(
            workload=workload,
            generation=generation,
            descriptor=descriptor,
            descriptor_record=descriptor_record,
        )
        whiteboard = _whiteboard(layout)
        planner_payload = {
            **common,
            "current_perf": dict(current_metrics),
            "leading_indicators": {
                "contention_level": descriptor["contention"]["label"],
                "cache_miss_rate_pct": current_metrics["llc_miss_rate"],
                "IPC_overall": current_metrics["ipc"],
            },
            "whiteboard": whiteboard,
        }
        planner, event = _invoke(
            role="planner",
            provider=providers["planner"],
            invocation_id=f"{workload}.g{generation}.planner",
            payload=planner_payload,
            raw_root=run_root / "raw",
            journal=journal,
            workload=workload,
            generation=generation,
        )
'''

V11_NEW = '''    perf = _perf_for(flags)
    result: dict[str, Any] = {
        "workload": workload,
        "workload_flags": dict(flags),
        "descriptor": descriptor,
        "descriptor_binding": descriptor_record,
        "campaign_id": str(trigger.ident.campaign_id(cfg)),
        "campaign_root": layout.root,
        "generations": [],
        "stop_reason": "fixed-generation-budget",
    }
    prior_reverse: bool | None = None
    current_metrics = {
        "throughput_ops_sec": None,
        "abort_rate_pct": None,
        "latency_ns": None,
        "llc_miss_rate": None,
        "ipc": None,
    }

    for generation in range(1, generations + 1):
        if time.monotonic() - started_monotonic >= max_wall_s:
            result["stop_reason"] = "supervisor-wall-budget"
            break
        generation_record: dict[str, Any] = {"generation": generation, "roles": {}}
        common = _common_payload(
            workload=workload,
            generation=generation,
            descriptor=descriptor,
            descriptor_record=descriptor_record,
        )
        whiteboard = _whiteboard(layout)
        planner_payload = {
            **common,
            "current_perf": dict(current_metrics),
            "leading_indicators": {
                "contention_level": descriptor["contention"]["label"],
                "cache_miss_rate_pct": current_metrics["llc_miss_rate"],
                "IPC_overall": current_metrics["ipc"],
            },
            "whiteboard": whiteboard,
        }
        planner, event = _invoke(
            role="planner",
            provider=providers["planner"],
            invocation_id=f"{workload}.g{generation}.planner",
            payload=planner_payload,
            raw_root=run_root / "raw",
            journal=journal,
            workload=workload,
            generation=generation,
        )
        _assert_fresh_campaign_state(layout)
'''


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        "V1",
        "negative",
        "    _validate_generation_budget(args.max_generations)\n",
        "",
        (_node("test_main_rejects_unapproved_budget_before_build_preparation"),),
    ),
    Mutation(
        "V2",
        "negative",
        '''    if _TRIAL_ID_RE.fullmatch(trial_id) is None:
        raise AutonomousTrialError(f"trial_id が安全な形式でない: {trial_id!r}")
    _validate_generation_budget(generations)
    if isinstance(max_wall_s, bool) or not isinstance(max_wall_s, int) or max_wall_s < 1:
''',
        '''    if _TRIAL_ID_RE.fullmatch(trial_id) is None:
        raise AutonomousTrialError(f"trial_id が安全な形式でない: {trial_id!r}")
    if isinstance(max_wall_s, bool) or not isinstance(max_wall_s, int) or max_wall_s < 1:
''',
        (_node("test_run_trial_rejects_unapproved_budget_before_artifact_creation"),),
    ),
    Mutation(
        "V3",
        "negative",
        "    _validate_generation_budget(generations)\n    flags = WORKLOADS[workload]\n",
        "    flags = WORKLOADS[workload]\n",
        (_node("test_run_workload_direct_call_rejects_unapproved_budget"),),
    ),
    Mutation(
        "V4",
        "negative",
        "    _assert_fresh_campaign_state(layout)\n    perf = _perf_for(flags)\n",
        "    perf = _perf_for(flags)\n",
        (_node("test_run_workload_rejects_existing_campaign_state"),),
    ),
    Mutation(
        "V5",
        "negative",
        "    if generations > MAX_APPROVED_GENERATIONS:\n",
        "    if generations >= MAX_APPROVED_GENERATIONS:\n",
        (BOUNDARY,),
    ),
    Mutation(
        "V6",
        "negative",
        '    parser.add_argument("--max-generations", type=int, default=1)\n',
        '    parser.add_argument("--max-generations", type=int, default=2)\n',
        (
            CLI_DEFAULT,
            FIXTURE_ACCEPT,
            HEADLESS_BUILD_ACCEPT,
            HEADLESS_NO_BUILD_ACCEPT,
        ),
    ),
    Mutation(
        "V7",
        "negative",
        "MAX_APPROVED_GENERATIONS = 1\n",
        "MAX_APPROVED_GENERATIONS = 2\n",
        (BOUNDARY,),
    ),
    Mutation(
        "V8",
        "negative",
        '    parser.add_argument("--max-generations", type=int, default=1)\n',
        '    parser.add_argument(\n'
        '        "--max-generations", type=int, default=MAX_APPROVED_GENERATIONS\n'
        '    )\n',
        (_node("test_cli_default_is_literal_one_by_ast"),),
    ),
    Mutation(
        "V9",
        "negative",
        "    if type(generations) is not int:\n",
        "    if not isinstance(generations, int):\n",
        (
            _node("test_generation_budget_rejects_bool"),
            _node("test_generation_budget_rejects_int_subclass_with_overridden_add"),
        ),
    ),
    Mutation(
        "V10a",
        "negative",
        "    if not 1 <= generations <= MAX_GENERATIONS:\n",
        "    if generations > MAX_GENERATIONS:\n",
        (_node("test_generation_budget_rejects_below_minimum"),),
    ),
    Mutation(
        "V10c",
        "negative",
        '''    if type(generations) is not int:
        raise AutonomousTrialError(f"generations は 1..{MAX_GENERATIONS} 必須")
''',
        "",
        (
            _node("test_generation_budget_rejects_bool"),
            _node("test_generation_budget_rejects_non_int_float"),
            _node("test_generation_budget_rejects_int_subclass_with_overridden_add"),
        ),
    ),
    Mutation(
        "V11",
        "negative",
        V11_OLD,
        V11_NEW,
        (_node("test_run_workload_rejects_existing_campaign_state"),),
    ),
    Mutation(
        "V12",
        "negative",
        '''        if planner is None:
            generation_record["outcome"] = "planner-invalid"
            result["generations"].append(generation_record)
            result["stop_reason"] = "role-invalid"
            break
''',
        '''        if planner is None:
            generation_record["outcome"] = "planner-invalid"
            result["generations"].append(generation_record)
            result["stop_reason"] = "role-invalid"
            continue
''',
        (_node("test_invalid_role_is_single_attempt_and_stops_cell"),),
    ),
    Mutation(
        "V13",
        "negative",
        '''def _assert_fresh_campaign_state(layout: CampaignLayout) -> None:
    try:
        state = loop_core.load_loop_state(layout)
    except (OSError, ValueError, KeyError, OverflowError) as exc:
        raise AutonomousTrialError(
            "campaign checkpoint の読取・decode・schema 検査に失敗"
        ) from exc
    if state is not None:
        raise AutonomousTrialError(
            "既存 campaign state は D106 残余 1 の裁定まで再利用不可"
        )
''',
        '''def _assert_fresh_campaign_state(layout: CampaignLayout) -> None:
    state = loop_core.load_loop_state(layout)
    if state is not None:
        raise AutonomousTrialError(
            "既存 campaign state は D106 残余 1 の裁定まで再利用不可"
        )
''',
        (MALFORMED_CHECKPOINT, LEAKING_CHECKPOINT),
    ),
    Mutation(
        "V15",
        "negative",
        "    except (OSError, ValueError, KeyError, OverflowError) as exc:\n",
        "    except Exception as exc:\n",
        (ATTRIBUTE_ERROR_PASSTHROUGH,),
    ),
    Mutation(
        "P1",
        "positive",
        "    if generations > MAX_APPROVED_GENERATIONS:\n",
        "    if generations >= MAX_APPROVED_GENERATIONS:\n",
        (BOUNDARY,),
    ),
    Mutation(
        "P2",
        "positive",
        '''def _assert_fresh_campaign_state(layout: CampaignLayout) -> None:
    try:
        state = loop_core.load_loop_state(layout)
    except (OSError, ValueError, KeyError, OverflowError) as exc:
        raise AutonomousTrialError(
            "campaign checkpoint の読取・decode・schema 検査に失敗"
        ) from exc
    if state is not None:
        raise AutonomousTrialError(
            "既存 campaign state は D106 残余 1 の裁定まで再利用不可"
        )
''',
        '''def _assert_fresh_campaign_state(layout: CampaignLayout) -> None:
    raise AutonomousTrialError(
        "既存 campaign state は D106 残余 1 の裁定まで再利用不可"
    )
''',
        (_node("test_run_workload_accepts_fresh_campaign_state"),),
    ),
    Mutation(
        "P3",
        "positive",
        "    if generations > MAX_APPROVED_GENERATIONS:\n",
        "    if isinstance(generations, int):\n",
        (
            FIXTURE_ACCEPT,
            HEADLESS_BUILD_ACCEPT,
            HEADLESS_NO_BUILD_ACCEPT,
            BOUNDARY,
        ),
    ),
    Mutation(
        "P4",
        "positive",
        '''    try:
        state = loop_core.load_loop_state(layout)
    except (OSError, ValueError, KeyError, OverflowError) as exc:
''',
        '''    try:
        fixed_empty_layout = CampaignLayout(
            str(Path(layout.root) / "__mutation_fixed_empty__")
        )
        state = loop_core.load_loop_state(fixed_empty_layout)
    except (OSError, ValueError, KeyError, OverflowError) as exc:
''',
        (ACTUAL_EXISTING_STATE,),
    ),
)


UNATTRIBUTABLE: tuple[dict[str, str], ...] = (
    {
        "id": "V10b",
        "kind": "negative",
        "mutation": "上限条件 <= MAX_GENERATIONS の削除",
        "reason": (
            "等価変異。2 以上は後続の承認上限判定が拒否するため受理集合が変わらず、"
            "変わるのは MAX_GENERATIONS 超過時の診断だけである"
        ),
    },
    {
        "id": "V14",
        "kind": "negative",
        "mutation": "exact int 型検査を isinstance に戻す",
        "reason": "V9 と同一の source 変更かつ同じ int サブクラス退行なので重複登録しない",
    },
)


def _validate_registration(target: Path, test_target: Path) -> dict[str, Any]:
    source = target.read_text(encoding="utf-8")
    test_source = test_target.read_text(encoding="utf-8")
    try:
        test_tree = ast.parse(test_source, filename=str(test_target))
    except SyntaxError as exc:
        raise HarnessError(f"期待 node 検査用 test AST を解析できない: {exc}") from exc
    defined_tests = {
        node.name
        for node in ast.walk(test_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }

    ids: set[str] = set()
    anchor_counts: dict[str, int] = {}
    expected_definitions: dict[str, bool] = {}
    for mutation in MUTATIONS:
        if mutation.id in ids:
            raise HarnessError(f"変異 ID が重複: {mutation.id}")
        ids.add(mutation.id)
        count = source.count(mutation.old)
        anchor_counts[mutation.id] = count
        if count != 1:
            raise HarnessError(
                f"{mutation.id}: fix 後 source の anchor count={count}; exactly one required"
            )
        for expected in mutation.expected_nodes:
            path_part, separator, test_part = expected.partition("::")
            function_name = re.sub(r"\[[^\]]*\]$", "", test_part)
            definition_anchor = f"def {function_name}("
            exists = (
                bool(separator)
                and path_part == TEST_REL.as_posix()
                and function_name in defined_tests
                and test_source.count(definition_anchor) == 1
            )
            expected_definitions[expected] = exists
            if not exists:
                raise HarnessError(f"{mutation.id}: 期待 node が test に実在しない: {expected}")
    return {
        "anchor_counts": anchor_counts,
        "expected_node_definitions": expected_definitions,
    }


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _validate_repo(repo: Path, target: Path) -> str:
    probe = _run_git(repo, "rev-parse", "--show-toplevel")
    if probe.returncode != 0:
        raise HarnessError(f"repo root を確認できない: {probe.stderr.strip()}")
    if Path(probe.stdout.strip()).resolve() != repo:
        raise HarnessError("--repo は git worktree root そのものを指定する必要がある")
    head = _run_git(repo, "rev-parse", "HEAD")
    if head.returncode != 0:
        raise HarnessError(f"repo HEAD を取得できない: {head.stderr.strip()}")
    committed = _run_git(repo, "show", f"HEAD:{TARGET_REL.as_posix()}")
    if committed.returncode != 0:
        raise HarnessError(f"対象の HEAD bytes を取得できない: {committed.stderr.strip()}")
    current = target.read_text(encoding="utf-8")
    if current != committed.stdout:
        raise HarnessError(
            f"対象 production が HEAD と不一致; 前回の変異が残っている可能性がある。"
            f"git checkout -- {TARGET_REL.as_posix()} で復元してから再実行せよ"
        )
    return head.stdout.strip()


def _strip_relay_prefix(line: str) -> str:
    line = ANSI_RE.sub("", line).lstrip()
    while line.startswith("|"):
        line = line[1:].lstrip()
    return line


def _normalize_node(node: str, repo: Path) -> str:
    value = node.strip().replace("\\", "/")
    repo_prefix = repo.as_posix().rstrip("/") + "/"
    if value.startswith(repo_prefix):
        value = value[len(repo_prefix) :]
    test_rel = TEST_REL.as_posix()
    if "::" not in value:
        value = f"{test_rel}::{value}"
    else:
        path_part, rest = value.split("::", 1)
        if path_part in {TEST_REL.name, f"./{test_rel}"}:
            path_part = test_rel
        value = f"{path_part.lstrip('./')}::{rest}"
    return value


def _match_key(node: str, repo: Path) -> str:
    normalized = _normalize_node(node, repo)
    path_part, test_part = normalized.split("::", 1)
    test_part = re.sub(r"\[[^\]]*\]$", "", test_part)
    return f"{path_part}::{test_part}"


def _failed_nodes(output: str, repo: Path) -> list[str]:
    found: list[str] = []
    for raw_line in output.splitlines():
        line = _strip_relay_prefix(raw_line)
        if not line.startswith("FAILED "):
            continue
        node_and_error = line[len("FAILED ") :]
        node, _separator, _error = node_and_error.partition(" - ")
        if not node.strip():
            continue
        normalized = _normalize_node(node, repo)
        if normalized not in found:
            found.append(normalized)
    return found


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _read_dispatch_artifact(
    console_output: str, repo: Path, rc: int,
) -> dict[str, Any]:
    """dispatcher receipt から full job stdout を特定して読み出す。"""

    matches: list[tuple[str, int]] = []
    for raw_line in console_output.splitlines():
        # receipt は dispatcher 自身の frame だけを認める。child の ``| `` は剥がさず、
        # child が同じ文言を出しても receipt と誤認しない。
        line = ANSI_RE.sub("", raw_line).strip()
        match = RECEIPT_LINE_RE.fullmatch(line)
        if match is not None:
            matches.append((match.group(1), int(match.group(2))))
    if len(matches) != 1:
        return {
            "artifact_error": f"receipt 表示行が exactly one でない: {len(matches)}",
        }

    receipt_text, reported_rc = matches[0]
    if reported_rc != rc:
        return {
            "artifact_error": (
                f"receipt 表示 child rc={reported_rc} と subprocess rc={rc} が不一致"
            ),
        }
    dispatch_root = (repo / "output" / "pegasus-dispatch").resolve()
    raw_receipt = Path(receipt_text)
    try:
        if raw_receipt.is_symlink():
            raise OSError("receipt が symlink")
        receipt_path = raw_receipt.resolve(strict=True)
    except OSError as exc:
        return {"artifact_error": f"receipt を開けない: {receipt_text}: {exc}"}
    if not receipt_path.is_file() or not _path_within(receipt_path, dispatch_root):
        return {"artifact_error": f"receipt が dispatch root 配下の通常ファイルでない: {receipt_path}"}
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"artifact_error": f"receipt JSON を読めない: {exc}"}
    if not isinstance(receipt, dict):
        return {"artifact_error": "receipt JSON の root が object でない"}

    submission_value = receipt.get("submission_dir")
    if not isinstance(submission_value, str):
        return {"artifact_error": "receipt.submission_dir が文字列でない"}
    try:
        submission_dir = Path(submission_value).resolve(strict=True)
    except OSError as exc:
        return {"artifact_error": f"submission_dir を開けない: {exc}"}
    if (
        not submission_dir.is_dir()
        or not _path_within(submission_dir, dispatch_root)
        or (
            receipt_path.name == "receipt.json"
            and receipt_path.parent != submission_dir
        )
    ):
        return {"artifact_error": "receipt と submission_dir の束縛が不正"}

    outcome = receipt.get("outcome")
    receipt_rc = outcome.get("rc") if isinstance(outcome, dict) else None
    if receipt_rc != rc:
        return {"artifact_error": f"receipt outcome rc={receipt_rc!r} と rc={rc} が不一致"}
    request = receipt.get("request")
    request_id = receipt.get("request_id")
    if not isinstance(request, dict) or not isinstance(request_id, str):
        return {"artifact_error": "receipt の request/request_id が不正"}
    job_name = request.get("job_name")
    if not isinstance(job_name, str) or re.fullmatch(r"izdw-[A-Za-z0-9._-]+", job_name) is None:
        return {"artifact_error": "receipt request.job_name が不正"}
    numeric_request_id = request_id.rstrip(".").split(".", 1)[0]
    expected_names = {
        f"{job_name}.o{numeric_request_id}",
        f"{job_name}.o{request_id.rstrip('.')}",
    }

    logs = receipt.get("scheduler_logs")
    stdout_record = logs.get("stdout") if isinstance(logs, dict) else None
    stdout_value = stdout_record.get("path") if isinstance(stdout_record, dict) else None
    if not isinstance(stdout_value, str):
        return {"artifact_error": "receipt scheduler_logs.stdout.path がない"}
    raw_stdout = Path(stdout_value)
    try:
        if raw_stdout.is_symlink():
            raise OSError("job stdout が symlink")
        stdout_path = raw_stdout.resolve(strict=True)
    except OSError as exc:
        return {"artifact_error": f"job stdout を開けない: {exc}"}
    if (
        not stdout_path.is_file()
        or stdout_path.parent != submission_dir
        or JOB_STDOUT_RE.fullmatch(stdout_path.name) is None
        or stdout_path.name not in expected_names
    ):
        return {"artifact_error": f"job stdout の path/name 束縛が不正: {stdout_path}"}
    try:
        job_stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"artifact_error": f"job stdout を読めない: {exc}"}
    return {
        "artifact_error": None,
        "receipt_path": str(receipt_path),
        "job_stdout_path": str(stdout_path),
        "job_stdout": job_stdout,
    }


def _test_mutation(repo: Path) -> dict[str, Any]:
    command = ["python3", "tools/run_tests.py", TEST_REL.as_posix(), "-rf"]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=TEST_TIMEOUT_S,
            check=False,
        )
        output = completed.stdout or ""
        result = {
            "rc": completed.returncode,
            "timed_out": False,
            "output": output,
            "duration_s": round(time.monotonic() - started, 3),
        }
        result.update(_read_dispatch_artifact(output, repo, completed.returncode))
        return result
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return {
            "rc": None,
            "timed_out": True,
            "output": output,
            "artifact_error": "subprocess timeout のため receipt 未確定",
            "duration_s": round(time.monotonic() - started, 3),
        }
    except OSError as exc:
        return {
            "rc": None,
            "timed_out": False,
            "output": f"{type(exc).__name__}: {exc}",
            "artifact_error": f"test runner を起動できない: {exc}",
            "duration_s": round(time.monotonic() - started, 3),
        }


def _status(
    *, rc: int | None, timed_out: bool, expected: Sequence[str],
    failed: Sequence[str], repo: Path, artifact_error: str | None,
) -> str:
    if timed_out or rc is None:
        return "MISMATCH"
    if artifact_error is not None:
        return "PARSE_ERROR"
    if rc != 0 and not failed:
        return "PARSE_ERROR"
    if rc == 4:
        return "MISMATCH"
    if rc == 0:
        return "SURVIVED" if not failed else "MISMATCH"
    expected_keys = {_match_key(node, repo) for node in expected}
    failed_keys = {_match_key(node, repo) for node in failed}
    return "KILLED" if expected_keys & failed_keys else "KILLED_OTHER"


def _restore(repo: Path, target: Path, original: str) -> None:
    checkout_result = _run_git(repo, "checkout", "--", TARGET_REL.as_posix())
    cache = target.parent / "__pycache__"
    try:
        if checkout_result.returncode != 0:
            raise HarnessError(
                "git checkout による復元に失敗: " + checkout_result.stderr.strip()
            )
        restored = target.read_text(encoding="utf-8")
        if restored != original:
            raise HarnessError("復元後 read_text() が変異前 source と完全一致しない")
    finally:
        if cache.exists():
            shutil.rmtree(cache)


def _apply_one(repo: Path, target: Path, mutation: Mutation) -> dict[str, Any]:
    original = target.read_text(encoding="utf-8")
    count = original.count(mutation.old)
    if count != 1:
        raise HarnessError(
            f"{mutation.id}: anchor count={count}; exactly one required"
        )
    mutated = original.replace(mutation.old, mutation.new, 1)
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            mutated.splitlines(keepends=True),
            fromfile=f"a/{TARGET_REL.as_posix()}",
            tofile=f"b/{TARGET_REL.as_posix()}",
        )
    )
    if mutated == original or not diff:
        raise HarnessError(f"{mutation.id}: 注入 diff が実在しない")

    restore_required = True
    try:
        target.write_text(mutated, encoding="utf-8")
        injected = target.read_text(encoding="utf-8")
        if injected != mutated or injected == original:
            raise HarnessError(f"{mutation.id}: 書込後の注入実在確認に失敗")
        test_result = _test_mutation(repo)
        job_stdout = test_result.get("job_stdout", "")
        failed = _failed_nodes(job_stdout, repo)
        expected = [_normalize_node(node, repo) for node in mutation.expected_nodes]
        status = _status(
            rc=test_result["rc"],
            timed_out=test_result["timed_out"],
            expected=expected,
            failed=failed,
            repo=repo,
            artifact_error=test_result.get("artifact_error"),
        )
        output_lines = job_stdout.splitlines()
        console_lines = test_result["output"].splitlines()
        return {
            "id": mutation.id,
            "kind": mutation.kind,
            "file": TARGET_REL.as_posix(),
            "old": mutation.old,
            "new": mutation.new,
            "expected_nodes": expected,
            "rc": test_result["rc"],
            "status": status,
            "failed_nodes": failed,
            "timed_out": test_result["timed_out"],
            "duration_s": test_result["duration_s"],
            "artifact_error": test_result.get("artifact_error"),
            "receipt_path": test_result.get("receipt_path"),
            "job_stdout_path": test_result.get("job_stdout_path"),
            "anchor_count": count,
            "injection_diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
            "test_output_sha256": hashlib.sha256(job_stdout.encode("utf-8")).hexdigest(),
            "console_output_sha256": hashlib.sha256(
                test_result["output"].encode("utf-8")
            ).hexdigest(),
            "test_output_tail": (
                output_lines[-80:] if status in {"MISMATCH", "PARSE_ERROR"} else []
            ),
            "console_output_tail": console_lines[-80:] if status == "PARSE_ERROR" else [],
        }
    finally:
        if restore_required:
            _restore(repo, target, original)


def _baseline(repo: Path) -> dict[str, Any]:
    test_result = _test_mutation(repo)
    job_stdout = test_result.get("job_stdout", "")
    failed = _failed_nodes(job_stdout, repo)
    artifact_error = test_result.get("artifact_error")
    rc = test_result["rc"]
    if test_result["timed_out"] or rc is None:
        status = "MISMATCH"
    elif artifact_error is not None or (rc != 0 and not failed):
        status = "PARSE_ERROR"
    elif rc == 0 and not failed:
        status = "PASSED"
    else:
        status = "FAILED"
    return {
        "status": status,
        "rc": rc,
        "failed_nodes": failed,
        "timed_out": test_result["timed_out"],
        "duration_s": test_result["duration_s"],
        "artifact_error": artifact_error,
        "receipt_path": test_result.get("receipt_path"),
        "job_stdout_path": test_result.get("job_stdout_path"),
        "test_output_sha256": hashlib.sha256(job_stdout.encode("utf-8")).hexdigest(),
        "console_output_sha256": hashlib.sha256(
            test_result["output"].encode("utf-8")
        ).hexdigest(),
        "test_output_tail": job_stdout.splitlines()[-80:] if status != "PASSED" else [],
        "console_output_tail": (
            test_result["output"].splitlines()[-80:]
            if status == "PARSE_ERROR" else []
        ),
    }


def _summary(records: Sequence[dict[str, Any]]) -> dict[str, int]:
    result = {
        "registered": len(MUTATIONS),
        "completed": len(records),
        "unattributable": len(UNATTRIBUTABLE),
        "KILLED": 0,
        "KILLED_OTHER": 0,
        "SURVIVED": 0,
        "MISMATCH": 0,
        "PARSE_ERROR": 0,
    }
    for record in records:
        status = record.get("status")
        if status not in result:
            raise HarnessError(f"ledger mutation status が未知: {status!r}")
        result[status] += 1
    return result


def _registration_sha256() -> str:
    projection = [dataclasses.asdict(mutation) for mutation in MUTATIONS]
    payload = json.dumps(
        projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _procedure(registration: dict[str, Any]) -> dict[str, Any]:
    return {
        "test_command": [
            "python3",
            "tools/run_tests.py",
            TEST_REL.as_posix(),
            "-rf",
        ],
        "timeout_s": TEST_TIMEOUT_S,
        "anchor_policy": "old exact count == 1 before every mutation",
        "injection_policy": "read-back equality plus non-empty unified diff",
        "restore_policy": "git checkout -- <file>, then exact read_text equality",
        "cache_policy": "remove target module __pycache__ after every restore",
        "node_policy": (
            "read full job stdout named by dispatch receipt; strip ANSI/relay prefix; "
            "normalize both sides"
        ),
        "resume_policy": "same repo_head + registration_sha256; skip completed mutation id",
        "registration_preflight": registration,
    }


def _new_ledger(
    *, head: str, registration: dict[str, Any], registration_sha256: str,
) -> dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    return {
        "schema": LEDGER_SCHEMA,
        "wave": WAVE,
        "date": now,
        "updated_at": now,
        "repo_head": head,
        "registration_sha256": registration_sha256,
        "procedure": _procedure(registration),
        "baseline": None,
        "summary": _summary(records),
        "mutations": records,
        "parse_error_history": [],
        "unattributable": list(UNATTRIBUTABLE),
    }


def _load_resume_ledger(
    path: Path, *, head: str, registration_sha256: str,
) -> dict[str, Any]:
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarnessError(f"resume ledger を読めない: {exc}") from exc
    if not isinstance(ledger, dict):
        raise HarnessError("resume ledger の root が object でない")
    expected = {
        "schema": LEDGER_SCHEMA,
        "wave": WAVE,
        "repo_head": head,
        "registration_sha256": registration_sha256,
    }
    for key, value in expected.items():
        if ledger.get(key) != value:
            raise HarnessError(
                f"resume ledger の {key} が現行 run と不一致: {ledger.get(key)!r}"
            )
    records = ledger.get("mutations")
    history = ledger.get("parse_error_history")
    if not isinstance(records, list) or not isinstance(history, list):
        raise HarnessError("resume ledger の mutations/parse_error_history が list でない")
    known_ids = {mutation.id for mutation in MUTATIONS}
    completed_ids: set[str] = set()
    kept: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or record.get("id") not in known_ids:
            raise HarnessError("resume ledger に未知または不正な mutation record がある")
        mutation_id = record["id"]
        status = record.get("status")
        if status == "PARSE_ERROR":
            history.append(record)
            continue
        if status not in {"KILLED", "KILLED_OTHER", "SURVIVED", "MISMATCH"}:
            raise HarnessError(f"resume ledger の {mutation_id} status が不正: {status!r}")
        if mutation_id in completed_ids:
            raise HarnessError(f"resume ledger の mutation ID が重複: {mutation_id}")
        completed_ids.add(mutation_id)
        kept.append(record)
    ledger["mutations"] = kept
    ledger["parse_error_history"] = history
    return ledger


def _write_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(ledger, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _lock_for(repo: Path) -> Any:
    key = hashlib.sha256(str(repo).encode("utf-8")).hexdigest()[:20]
    lock_path = Path(tempfile.gettempdir()) / f"izanagi-mutation-{key}.lock"
    stream = lock_path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        stream.close()
        raise HarnessError("別の mutation harness が同じ repo で走行中") from exc
    return stream


def _install_signal_handlers() -> dict[int, Any]:
    old_handlers: dict[int, Any] = {}

    def handler(signum: int, _frame: Any) -> None:
        # 二発目の signal が復元中の finally を中断しないよう、最初の signal で無視へ倒す。
        for guarded in (signal.SIGINT, signal.SIGTERM):
            signal.signal(guarded, signal.SIG_IGN)
        raise SignalAbort(signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        old_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, handler)
    return old_handlers


def _restore_signal_handlers(old_handlers: dict[int, Any]) -> None:
    for signum, old_handler in old_handlers.items():
        signal.signal(signum, old_handler)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="既存 --out と HEAD/spec を照合し、完了済み mutation ID を skip する",
    )
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    out = args.out.resolve()
    target = repo / TARGET_REL
    test_target = repo / TEST_REL
    lock_stream = _lock_for(repo)
    try:
        if not target.is_file() or target.is_symlink():
            raise HarnessError(f"対象 production が通常ファイルでない: {target}")
        if not test_target.is_file() or test_target.is_symlink():
            raise HarnessError(f"対象 test が通常ファイルでない: {test_target}")
        # lock 取得直後・registration/ledger/baseline より前に、SIGKILL 残留変異を遮断する。
        head = _validate_repo(repo, target)
        registration = _validate_registration(target, test_target)
        registration_sha256 = _registration_sha256()
        if args.resume:
            if not out.is_file() or out.is_symlink():
                raise HarnessError("--resume には既存の通常ファイル --out が必要")
            ledger = _load_resume_ledger(
                out, head=head, registration_sha256=registration_sha256
            )
        else:
            if out.exists():
                raise HarnessError("--out が既に存在する; 続行は --resume を明示せよ")
            ledger = _new_ledger(
                head=head,
                registration=registration,
                registration_sha256=registration_sha256,
            )

        old_handlers = _install_signal_handlers()
        try:
            records = ledger["mutations"]
            baseline = ledger.get("baseline")
            if baseline is None:
                if records:
                    raise HarnessError("baseline のない ledger に mutation record がある")
                baseline = _baseline(repo)
                ledger["baseline"] = baseline
                ledger["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                ledger["summary"] = _summary(records)
                _write_ledger(out, ledger)
            if not isinstance(baseline, dict) or baseline.get("status") != "PASSED":
                raise HarnessError(
                    "baseline が緑でないため mutation を開始しない: "
                    f"status={baseline.get('status') if isinstance(baseline, dict) else None}, "
                    f"rc={baseline.get('rc') if isinstance(baseline, dict) else None}"
                )
            if baseline.get("rc") != 0 or baseline.get("failed_nodes") != []:
                raise HarnessError("baseline PASSED record の rc/failed_nodes が不整合")

            completed_ids = {record["id"] for record in records}
            for mutation in MUTATIONS:
                if mutation.id in completed_ids:
                    continue
                record = _apply_one(repo, target, mutation)
                records.append(record)
                ledger["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                ledger["summary"] = _summary(records)
                # 1 変異ごとに atomic replace + file fsync + directory fsync。
                _write_ledger(out, ledger)
                if record["status"] == "PARSE_ERROR":
                    raise HarnessError(
                        f"{mutation.id}: rc={record['rc']} だが dispatch job stdout から "
                        "failed node を確実に抽出できないため停止"
                    )
        finally:
            _restore_signal_handlers(old_handlers)
    finally:
        lock_stream.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SignalAbort as exc:
        print(
            f"mutation harness interrupted by signal {exc.signum}; "
            "active mutation restore was attempted",
            file=sys.stderr,
        )
        raise SystemExit(128 + exc.signum)
    except HarnessError as exc:
        print(f"mutation harness aborted: {exc}", file=sys.stderr)
        raise SystemExit(2)
