#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pytest runner を Pegasus gen_S 計算ノードへ同期 dispatch する。

dev harness 専用の薄い submitter であり、certification submitter は置き換えない。
親は scheduler 状態と永続 receipt を確定してから、会計照合済みの子 rc だけを返す。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence


INFRA_RC = 16
DEFAULT_PROJECT = "SFC"
DEFAULT_QUEUE = "gen_S"
DEFAULT_WALLTIME = "00:30:00"
DEFAULT_QUEUE_WAIT_TIMEOUT_S = 900.0
DEFAULT_OVERALL_GRACE_S = 300.0
DEFAULT_ACCOUNTING_GRACE_S = 60.0
DEFAULT_POLL_INTERVAL_S = 5.0
DEFAULT_LOG_LIMIT_BYTES = 2 * 1024 * 1024
DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS = 3

_TASK_RUN_ENV = "IZANAGI_TASK_RUN_ID"
_TASK_RUN_ROOT_ENV = "IZANAGI_TASK_RUNS_ROOT"
_TASK_RUN_SIDECAR_ENV = "IZANAGI_TASK_RUN_SIDECAR"
_COMPUTE_MARKER_NAME = "compute-visible.json"


@dataclass(frozen=True)
class _TaskSpec:
    """1 task 種別が計算ノードで必要とする実体・環境・interpreter 条件。"""

    child_script: tuple[str, ...]
    env_allowlist: frozenset[str]
    probe_imports: tuple[str, ...]


# 閉じた task enum。任意 command 化は「tools/pegasus/* の glob 許可はしない」
# (D103 決定 5) と正面衝突するため、受理する task はここに列挙したものだけとする。
TASKS = {
    "tests": _TaskSpec(
        child_script=("tools", "run_tests.py"),
        env_allowlist=frozenset({
            "PYTEST_ADDOPTS",
            "IZANAGI_TEST_NPROC",
            "IZANAGI_TEST_TRIGGER",
            "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS",
        }),
        probe_imports=("pytest", "xdist", "packaging"),
    ),
    # provenance 履歴監査は stdlib + git だけで動き、GIT_* は checker 自身が隔離するので
    # 親の環境値を 1 つも必要としない。
    "provenance": _TaskSpec(
        child_script=("tools", "check_ai_provenance.py"),
        env_allowlist=frozenset(),
        probe_imports=(),
    ),
}
DEFAULT_TASK = "tests"
_REQUEST_SCHEMA = "pegasus-dispatch-request/v2"
# v1 も受理する: queue 待ちの in-flight job は投入時点の request を、起動時点の live repo の
# _job_run で読む。一方向 bump は待ち中に land した job を殺すので互換受理を持つ。
_LEGACY_REQUEST_SCHEMA = "pegasus-dispatch-request/v1"
_RECEIPT_SCHEMA = "pegasus-dispatch-receipt/v2"
_QSTAT_ERROR_MARKERS = {
    "permission": (
        "not permitted",
        "permission",
        "eacces",
        "not authorized",
        "unauthorized",
        "access denied",
        "not owner",
        "ownership",
    ),
    "transient": (
        "connection",
        "cannot connect",
        "timeout",
        "timed out",
        "server busy",
        "temporarily unavailable",
        "try again",
    ),
}
_NQSV_REQUEST_ID_RE = re.compile(
    r"(?m)^[ \t]*Request ID:[ \t]*(\S+)[ \t]*$"
)
_NQSV_STARTED_RE = re.compile(
    r"(?m)^[ \t]*Started Request Time:[ \t]*\S.*$"
)
_NQSV_ENDED_RE = re.compile(
    r"(?m)^[ \t]*Ended Request Time:[ \t]*\S.*$"
)
_NQSV_ELAPSE_RE = re.compile(r"(?m)^[ \t]*Elapse:[ \t]*\S.*$")
_STATE_RE = re.compile(
    r"(?im)^\s*(?:Request\s+)?State\s*=\s*(QUE|RUN|HLD|STG|EXT)\s*$"
)
_CURRENT_STATE_RE = re.compile(r"(?im)^\s*Current\s+State\s*=\s*([^\r\n]+?)\s*$")
_REQUEST_RE = re.compile(r"Request\s+(\S+)\s+submitted")
_QSTAT_REQUEST_ID_RE = re.compile(
    r"(?im)^\s*Request\s+ID\s*[:=]\s*(\S+)\s*$"
)
_QSTAT_REQUEST_NAME_RE = re.compile(
    r"(?im)^\s*Request\s+Name\s*[:=]\s*(\S+)\s*$"
)
_INTERPRETER_CANDIDATES = (
    "python3.10",
    "/usr/bin/python3.10",
    "/bin/python3.10",
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
Clock = Callable[[], float]
Sleeper = Callable[[float], None]


class DispatchError(RuntimeError):
    """scheduler / receipt infrastructure が成立しない。"""


class _SignalAbort(DispatchError):
    def __init__(self, signum: int):
        super().__init__(f"signal {signum}")
        self.signum = signum


def _walltime_seconds(value: str) -> int:
    match = re.fullmatch(r"([0-9]+):([0-5][0-9]):([0-5][0-9])", value)
    if match is None:
        raise ValueError("walltime は HH:MM:SS 形式で指定してください")
    hours, minutes, seconds = (int(part) for part in match.groups())
    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise ValueError("walltime は 0 より大きくしてください")
    return total


def _normalize_request_id(value: str) -> str:
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized:
        raise DispatchError("request ID が空です")
    return normalized


def _parse_request_id(stdout: str) -> str:
    match = _REQUEST_RE.search(stdout)
    if match is not None:
        return match.group(1).rstrip(".")
    tokens = stdout.split()
    if len(tokens) == 1:
        return tokens[0].rstrip(".")
    raise DispatchError("qsub 成功出力から request ID を一意に抽出できません")


def _qstat_mentions_request(stdout: str, request_id: str) -> bool:
    """qstat 成功応答が対象 request の構造化 ID field を含むか検査する。"""

    expected = _normalize_request_id(request_id)
    for observed in _QSTAT_REQUEST_ID_RE.findall(stdout):
        try:
            if _normalize_request_id(observed) == expected:
                return True
        except DispatchError:
            continue
    return False


def _classify_qstat_response(
    result: subprocess.CompletedProcess[str],
    request_id: str,
) -> str:
    """immediate qstat を F47 権限系・一時系・成功可視性へ分類する。"""

    if result.returncode == 0:
        return (
            "success-request-visible"
            if _qstat_mentions_request(result.stdout or "", request_id)
            else "success-request-absent"
        )
    response = "\n".join((result.stdout or "", result.stderr or "")).casefold()
    if any(marker in response for marker in _QSTAT_ERROR_MARKERS["permission"]):
        return "permission"
    if any(marker in response for marker in _QSTAT_ERROR_MARKERS["transient"]):
        return "transient"
    # 誤ラッチは harness を恒久停止するため、未知の非ゼロも一時系へ倒す。
    return "transient"


def _scheduler_state(stdout: str) -> Optional[str]:
    match = _STATE_RE.search(stdout)
    if match is not None:
        abbreviated = match.group(1).upper()
        if abbreviated == "STG":
            return "QUE"
        if abbreviated == "EXT":
            return "END"
        return abbreviated
    match = _CURRENT_STATE_RE.search(stdout)
    if match is None:
        return None
    value = match.group(1).strip().lower()
    if value in {"running", "pre-running", "run"}:
        return "RUN"
    if value in {"queued", "queue", "waiting", "wait", "staging", "stg"}:
        return "QUE"
    if value in {"held", "hold", "holding"}:
        return "HLD"
    if value in {
        "completed", "complete", "finished", "ended", "exited", "exit",
        "terminated", "exiting", "post-running", "ext",
    }:
        return "END"
    return None


def _progress(message: str) -> None:
    print(f"[Pegasus dispatch] {message}", flush=True)


def _capture(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "returncode": int(result.returncode),
        "stdout": (result.stdout or "")[-65536:],
        "stderr": (result.stderr or "")[-65536:],
    }


def _run(
    run_command: CommandRunner,
    command: Sequence[str],
    *,
    cwd: Path,
    environ: Mapping[str, str],
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        list(command),
        cwd=str(cwd),
        env=dict(environ),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _write_json_x(path: Path, payload: Mapping[str, Any], *, mode: int = 0o600) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _write_text_x(path: Path, text: str, *, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _interpreter_probe_source(task: str = DEFAULT_TASK) -> str:
    """各候補自身で版数と task 固有の importability を assert する短い probe。

    既定引数は省略できない — probe は job script 生成の外 (テスト) からも無引数で
    呼ばれる。版数検査は task に依らず常に置く (_job_run と二層冗長 gate をなす)。
    """

    spec = TASKS[task]
    head = (
        "import sys\n"
        "if sys.version_info < (3, 10):\n"
        "    raise SystemExit(1)\n"
    )
    if not spec.probe_imports:
        return head + "raise SystemExit(0)\n"
    imports = "".join(f"    import {name}\n" for name in spec.probe_imports)
    return (
        head
        + "try:\n"
        + imports
        + "except Exception:\n"
        "    raise SystemExit(1)\n"
        "raise SystemExit(0)\n"
    )


def _job_name(nonce: str) -> str:
    """submission nonce から PBS job name を一意に導く。"""

    return f"izdw-{nonce[:10]}"


def _job_script(
    *,
    repo_root: Path,
    submission_dir: Path,
    request_path: Path,
    probe_path: Path,
    walltime: str,
    dispatcher_path: Optional[Path] = None,
) -> str:
    result_path = submission_dir / "result.json"
    marker_path = submission_dir / _COMPUTE_MARKER_NAME
    job_name = _job_name(submission_dir.name)
    dispatcher = (
        repo_root / "tools" / "pegasus" / "dispatch_compute.py"
        if dispatcher_path is None else Path(dispatcher_path)
    )
    candidates = " ".join(shlex.quote(value) for value in _INTERPRETER_CANDIDATES)
    return f"""#!/bin/bash
#PBS -A {DEFAULT_PROJECT}
#PBS -q {DEFAULT_QUEUE}
#PBS -b 1
#PBS -l elapstim_req={walltime}
#PBS -N {job_name}
set -u

RESULT={shlex.quote(str(result_path))}
PROBE={shlex.quote(str(probe_path))}
REQUEST={shlex.quote(str(request_path))}
REPO={shlex.quote(str(repo_root))}
DISPATCHER={shlex.quote(str(dispatcher))}
MARKER={shlex.quote(str(marker_path))}

write_failure() {{
    local stage=$1
    local tmp="${{RESULT}}.tmp.$$"
    printf '{{"schema_version":"pegasus-dispatch-result/v1","stage":"%s","child_rc":16,"pbs_jobid":"%s"}}\\n' \
        "$stage" "${{PBS_JOBID:-unknown}}" >"$tmp"
    mv "$tmp" "$RESULT"
}}

host=$(hostname 2>/dev/null || true)
if [[ ! "$host" =~ ^bnode[0-9]+([.].*)?$ ]]; then
    write_failure hostname
    exit {INFRA_RC}
fi
marker_tmp="${{MARKER}}.tmp.$$"
printf '{{"schema_version":"pegasus-compute-visible/v1","pbs_jobid":"%s","hostname":"%s"}}\\n' \
    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"
mv "$marker_tmp" "$MARKER"

selected=""
for candidate in {candidates}; do
    resolved=$(command -v "$candidate" 2>/dev/null || true)
    if [[ -n "$resolved" ]] && "$resolved" "$PROBE" >/dev/null 2>&1; then
        selected=$resolved
        break
    fi
done
if [[ -z "$selected" ]]; then
    write_failure interpreter
    exit {INFRA_RC}
fi

if ! cd "$REPO"; then
    write_failure cwd
    exit {INFRA_RC}
fi

export PATH="$(dirname "$selected"):$PATH"
unset {_TASK_RUN_ENV} {_TASK_RUN_ROOT_ENV} {_TASK_RUN_SIDECAR_ENV}
exec "$selected" "$DISPATCHER" --job-run "$REQUEST"
"""


def _read_json_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise DispatchError(f"required JSON がありません: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise DispatchError(f"JSON を読めません: {path}: {exc}") from exc
    if type(value) is not dict:
        raise DispatchError(f"JSON object ではありません: {path}")
    return value


def _resolve_request(request: Mapping[str, Any]) -> tuple[str, Any]:
    """request payload を (task, argv) へ解決する。schema v1 / v2 の両方を受理する。

    v1 には task 概念が無く、投入できた唯一の task は ``tests`` であった。未知の
    schema_version だけを拒否することで、queue 待ち中に新 schema が land しても
    in-flight job を殺さない。
    """

    schema = request.get("schema_version")
    if schema == _LEGACY_REQUEST_SCHEMA:
        return DEFAULT_TASK, request["pytest_args"]
    if schema == _REQUEST_SCHEMA:
        task = request.get("task")
        if type(task) is not str:
            raise DispatchError("task は string でなければなりません")
        return task, request["args"]
    raise DispatchError(f"未知の request schema_version です: {schema!r}")


def _import_probe_modules(spec: _TaskSpec) -> None:
    """task が要求する module だけを子起動前に import 検査する。"""

    for name in spec.probe_imports:
        __import__(name)


def _job_run(request_path: Path) -> int:
    """計算ノード内でだけ呼ばれる child launcher。"""

    result_path = request_path.parent / "result.json"
    stage = "bootstrap"
    child_rc = INFRA_RC
    pbs_jobid = os.environ.get("PBS_JOBID", "unknown")
    interpreter = str(Path(sys.executable).resolve())
    hostname = ""
    try:
        if sys.version_info < (3, 10):
            raise DispatchError("interpreter version < 3.10")

        request = _read_json_object(request_path)
        task, argv = _resolve_request(request)
        # 親 (_dispatch_impl) と独立に子でも閉集合照合する二層 fail-closed。
        if task not in TASKS:
            raise DispatchError(f"未知の task です: {task!r}")
        spec = TASKS[task]
        _import_probe_modules(spec)

        repo_root = Path(request["repo_root"]).resolve()
        requested_env = request.get("environment", {})
        if type(argv) is not list or not all(type(value) is str for value in argv):
            raise DispatchError("args は string list でなければなりません")
        if type(requested_env) is not dict or not all(
            type(key) is str and type(value) is str
            for key, value in requested_env.items()
        ):
            raise DispatchError("environment は string mapping でなければなりません")
        hostname = os.uname().nodename
        if re.fullmatch(r"bnode[0-9]+(?:\..*)?", hostname) is None:
            raise DispatchError(f"計算ノード hostname ではありません: {hostname}")
        os.chdir(repo_root)
        child_env = os.environ.copy()
        child_env.update(requested_env)
        child_env.pop(_TASK_RUN_ENV, None)
        child_env.pop(_TASK_RUN_ROOT_ENV, None)
        child_env.pop(_TASK_RUN_SIDECAR_ENV, None)
        executable_dir = str(Path(sys.executable).resolve().parent)
        child_env["PATH"] = executable_dir + os.pathsep + child_env.get("PATH", "")
        stage = "child"
        child_rc = subprocess.call(
            [sys.executable, str(repo_root.joinpath(*spec.child_script)), *argv],
            cwd=str(repo_root),
            env=child_env,
        )
    except Exception as exc:
        stage = stage if stage != "child" else "child-launch"
        error = f"{type(exc).__name__}: {exc}"
        child_rc = INFRA_RC
    else:
        error = None

    payload = {
        "schema_version": "pegasus-dispatch-result/v1",
        "stage": stage,
        "child_rc": int(child_rc),
        "pbs_jobid": pbs_jobid,
        "hostname": hostname,
        "interpreter": interpreter,
        "error": error,
    }
    try:
        _write_json_x(result_path, payload)
    except OSError:
        return INFRA_RC
    return int(child_rc)


def _log_candidates(
    submission_dir: Path,
    *,
    stream: str,
    request_id: str,
) -> list[Path]:
    marker = ".o" if stream == "stdout" else ".e"
    raw = request_id.rstrip(".")
    normalized = _normalize_request_id(raw)
    forms = list(dict.fromkeys((
        normalized.split(".", 1)[0],
        normalized,
        raw.split(".", 1)[0],
        raw,
    )))
    stems = (_job_name(submission_dir.name), "dispatch.sh")
    return [
        submission_dir / f"{stem}{marker}{form}"
        for stem in stems
        for form in forms
        if form
    ]


def _find_log(
    submission_dir: Path,
    *,
    stream: str,
    request_id: str,
) -> Optional[Path]:
    found: list[Path] = []
    for path in _log_candidates(
        submission_dir, stream=stream, request_id=request_id,
    ):
        try:
            if path.is_file() and not path.is_symlink():
                resolved = path.resolve()
                if resolved not in found:
                    found.append(resolved)
        except OSError:
            continue
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        raise DispatchError(f"scheduler {stream} log が複数あります: {found}")
    return None


def _bounded_log(path: Path, *, limit: int) -> dict[str, Any]:
    if limit <= 0:
        raise ValueError("log limit は正でなければなりません")
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            omitted = max(0, size - limit)
            if omitted:
                handle.seek(omitted)
            raw = handle.read(limit)
    except OSError as exc:
        raise DispatchError(f"scheduler log を読めません: {path}: {exc}") from exc
    text = raw.decode("utf-8", errors="replace")
    if omitted:
        text = f"[先頭 {omitted} bytes を省略。末尾 {limit} bytes を収集]\\n" + text
    return {
        "path": str(path),
        "size": size,
        "omitted_bytes": omitted,
        "tail": text,
    }


def _accounting_present(
    stderr_record: Mapping[str, Any],
    request_id: str,
) -> bool:
    """NQSV 会計サマリを submit ID と必須 field の連言で束縛する。"""

    tail = stderr_record.get("tail")
    if type(tail) is not str:
        return False
    request_ids = _NQSV_REQUEST_ID_RE.findall(tail)
    if len(request_ids) != 1:
        return False
    try:
        observed = _normalize_request_id(request_ids[0])
        expected = _normalize_request_id(request_id)
    except DispatchError:
        return False
    return (
        observed == expected
        and _NQSV_STARTED_RE.search(tail) is not None
        and _NQSV_ENDED_RE.search(tail) is not None
        and _NQSV_ELAPSE_RE.search(tail) is not None
    )


def _compute_marker_evidence(
    submission_dir: Path,
    request_id: str,
) -> tuple[bool, dict[str, Any]]:
    """計算ノードが共有 submission dir へ書いた marker を検証する。"""

    marker = submission_dir / _COMPUTE_MARKER_NAME
    try:
        payload = _read_json_object(marker)
        observed_id = payload.get("pbs_jobid")
        hostname = payload.get("hostname")
        valid = (
            payload.get("schema_version") == "pegasus-compute-visible/v1"
            and type(observed_id) is str
            and _normalize_request_id(observed_id)
            == _normalize_request_id(request_id)
            and type(hostname) is str
            and re.fullmatch(r"bnode[0-9]+(?:\..*)?", hostname) is not None
        )
        return valid, {
            "path": str(marker),
            "present": True,
            "valid": valid,
            "pbs_jobid": observed_id,
            "hostname": hostname,
        }
    except (DispatchError, OSError) as exc:
        try:
            present = marker.is_file() and not marker.is_symlink()
        except OSError:
            present = False
        return False, {
            "path": str(marker),
            "present": present,
            "valid": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _discover_request_id(
    run_command: CommandRunner,
    *,
    job_name: str,
    submission_dir: Path,
    environ: Mapping[str, str],
) -> tuple[Optional[str], dict[str, Any]]:
    """qsub 応答解析不能時に、一意な job name から request ID を回収する。"""

    try:
        result = _run(
            run_command,
            ["qstat", "-f"],
            cwd=submission_dir,
            environ=environ,
        )
    except BaseException as exc:
        return None, {
            "attempted": True,
            "job_name": job_name,
            "submission_dir": str(submission_dir),
            "exception": f"{type(exc).__name__}: {exc}",
        }
    record = {
        "attempted": True,
        "job_name": job_name,
        "submission_dir": str(submission_dir),
        **_capture(result),
    }
    if result.returncode != 0:
        return None, record

    text = result.stdout or ""
    id_matches = list(_QSTAT_REQUEST_ID_RE.finditer(text))
    candidates: list[tuple[str, str]] = []
    for index, match in enumerate(id_matches):
        end = id_matches[index + 1].start() if index + 1 < len(id_matches) else len(text)
        block = text[match.start():end]
        names = _QSTAT_REQUEST_NAME_RE.findall(block)
        name_matched = names == [job_name]
        submission_dir_matched = str(submission_dir) in block
        if name_matched or submission_dir_matched:
            matched_by = "+".join(
                label for label, matched in (
                    ("request-name", name_matched),
                    ("submission-dir", submission_dir_matched),
                )
                if matched
            )
            candidates.append((match.group(1).rstrip("."), matched_by))
    unique = sorted({candidate for candidate, _ in candidates})
    record["candidates"] = unique
    if len(unique) == 1:
        record["matched_by"] = "+".join(sorted({
            matched_by
            for candidate, matched_by in candidates
            if candidate == unique[0]
        }))
        return unique[0], record
    return None, record


def _latch_submission_disabled(
    output_root: Path,
    *,
    reason: str,
    submission_dir: Path,
    request_id: Optional[str],
) -> Path:
    path = output_root / "submission-disabled.json"
    payload = {
        "schema_version": "pegasus-submission-disabled/v1",
        "reason": reason,
        "submission_dir": str(submission_dir),
        "request_id": request_id,
        "recovery": "ユーザー自身の端末から qsub し、有効性を確認してください",
    }
    try:
        _write_json_x(path, payload)
    except FileExistsError:
        pass
    return path


def _print_terminal_handoff(latch: Path, reason: str) -> None:
    print(
        f"Pegasus 自動投入を停止しました ({reason})。"
        f"ラッチ: {latch}。ユーザー自身の端末から qsub し、"
        "出力の永続・qstat 可視性・終了後会計を確認してください。",
        file=sys.stderr,
        flush=True,
    )


def _best_effort_qdel(
    run_command: CommandRunner,
    *,
    request_id: str,
    cwd: Path,
    environ: Mapping[str, str],
) -> dict[str, Any]:
    normalized = _normalize_request_id(request_id)
    try:
        result = _run(
            run_command,
            ["qdel", normalized],
            cwd=cwd,
            environ=environ,
        )
    except BaseException as exc:
        return {
            "attempted": True,
            "request_id": normalized,
            "exception": f"{type(exc).__name__}: {exc}",
        }
    return {
        "attempted": True,
        "request_id": normalized,
        **_capture(result),
    }


def _persist_receipt(
    submission_dir: Path,
    output_root: Path,
    payload: Mapping[str, Any],
) -> Optional[Path]:
    preferred = submission_dir / "receipt.json"
    try:
        _write_json_x(preferred, payload)
        return preferred
    except (FileExistsError, OSError):
        fallback = output_root / f"receipt-fallback-{submission_dir.name}.json"
        try:
            _write_json_x(fallback, payload)
            return fallback
        except (FileExistsError, OSError):
            return None


def _dispatch_impl(
    args: Sequence[str],
    *,
    task: str = DEFAULT_TASK,
    repo_root: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
    output_root: Optional[Path] = None,
    walltime: str = DEFAULT_WALLTIME,
    queue_wait_timeout_s: float = DEFAULT_QUEUE_WAIT_TIMEOUT_S,
    overall_grace_s: float = DEFAULT_OVERALL_GRACE_S,
    accounting_grace_s: float = DEFAULT_ACCOUNTING_GRACE_S,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    log_limit_bytes: int = DEFAULT_LOG_LIMIT_BYTES,
    immediate_qstat_attempts: int = DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS,
    run_command: CommandRunner = subprocess.run,
    clock: Clock = time.monotonic,
    sleep: Sleeper = time.sleep,
    nonce: Optional[str] = None,
) -> int:
    """1 invocation を 1 batch job として投入し、会計照合済み rc を返す。"""

    # 不正 task は scheduler へ 1 度も触れずに落とす (親側)。子側の照合は _job_run。
    if task not in TASKS:
        raise ValueError(f"未知の task です: {task!r}")
    spec = TASKS[task]

    repo = (
        Path(__file__).resolve().parents[2]
        if repo_root is None else Path(repo_root).resolve()
    )
    root = (
        repo / "output" / "pegasus-dispatch"
        if output_root is None else Path(output_root).resolve()
    )
    walltime_s = _walltime_seconds(walltime)
    if min(
        queue_wait_timeout_s,
        overall_grace_s,
        accounting_grace_s,
        poll_interval_s,
    ) < 0:
        raise ValueError("timeout / interval は負にできません")
    if poll_interval_s == 0:
        raise ValueError("poll interval は 0 にできません")
    if immediate_qstat_attempts <= 0:
        raise ValueError("immediate qstat attempts は正でなければなりません")

    command_env = dict(os.environ if environ is None else environ)
    request_env = {
        key: command_env[key]
        for key in spec.env_allowlist if key in command_env
    }
    command_env.pop(_TASK_RUN_ENV, None)
    command_env.pop(_TASK_RUN_ROOT_ENV, None)
    command_env.pop(_TASK_RUN_SIDECAR_ENV, None)

    root.mkdir(parents=True, exist_ok=True)
    latch = root / "submission-disabled.json"
    if latch.exists():
        _print_terminal_handoff(latch, "既存の F47 型ラッチ")
        return INFRA_RC

    nonce_value = nonce or secrets.token_hex(16)
    if re.fullmatch(r"[A-Za-z0-9._-]+", nonce_value) is None:
        raise ValueError("nonce は path separator を含まない leaf でなければなりません")
    submission_dir = root / nonce_value
    submission_dir.mkdir(mode=0o700)
    job_name = _job_name(submission_dir.name)
    receipt: dict[str, Any] = {
        "schema_version": _RECEIPT_SCHEMA,
        "submission_dir": str(submission_dir),
        "request": {
            "project": DEFAULT_PROJECT,
            "queue": DEFAULT_QUEUE,
            "nodes": 1,
            "walltime": walltime,
            "job_name": job_name,
            "task": task,
            "args": list(args),
        },
        "state_history": [],
        "qdel": {"attempted": False},
    }
    request_path = submission_dir / "request.json"
    probe_path = submission_dir / "interpreter_probe.py"
    script_path = submission_dir / "dispatch.sh"
    _write_json_x(request_path, {
        "schema_version": _REQUEST_SCHEMA,
        "repo_root": str(repo),
        "task": task,
        "args": list(args),
        "environment": request_env,
    })
    _write_text_x(probe_path, _interpreter_probe_source(task), mode=0o600)
    _write_text_x(
        script_path,
        _job_script(
            repo_root=repo,
            submission_dir=submission_dir,
            request_path=request_path,
            probe_path=probe_path,
            walltime=walltime,
        ),
        mode=0o700,
    )
    _fsync_dir(submission_dir)
    _fsync_dir(root)

    request_id: Optional[str] = None
    active = False
    request_was_visible = False
    run_seen = False
    old_handlers: dict[int, Any] = {}

    def abort_on_signal(signum, _frame):
        raise _SignalAbort(signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            old_handlers[signum] = signal.signal(signum, abort_on_signal)
        except (ValueError, OSError):
            pass

    started = 0.0
    submitted_at = 0.0
    try:
        started = clock()
        preflight = _run(
            run_command,
            ["qstat", "-Q"],
            cwd=submission_dir,
            environ=command_env,
        )
        receipt["preflight"] = {"qstat_Q": _capture(preflight)}
        if preflight.returncode != 0:
            raise DispatchError(f"qstat -Q preflight rc={preflight.returncode}")

        _progress(f"job を {DEFAULT_QUEUE} へ投入します ({job_name})")
        qsub = _run(
            run_command,
            [
                "qsub",
                "-A", DEFAULT_PROJECT,
                "-q", DEFAULT_QUEUE,
                "-b", "1",
                "-l", f"elapstim_req={walltime}",
                "-N", job_name,
                script_path.name,
            ],
            cwd=submission_dir,
            environ=command_env,
        )
        if qsub.returncode == 0:
            # qsub 成功を観測した瞬間から cleanup 対象。receipt capture 中の
            # SIGINT/SIGTERM でも discovery + qdel を通す。
            active = True
        receipt["qsub"] = _capture(qsub)
        if qsub.returncode != 0:
            raise DispatchError(f"qsub rc={qsub.returncode}")
        submitted_at = clock()
        request_id = _parse_request_id(qsub.stdout or "")
        normalized_id = _normalize_request_id(request_id)
        receipt["request_id"] = request_id
        receipt["normalized_request_id"] = normalized_id
        _progress(f"request ID {normalized_id} を受理しました")

        immediate_attempt_records: list[dict[str, Any]] = []
        visible: Optional[subprocess.CompletedProcess[str]] = None
        permission_error: Optional[dict[str, Any]] = None
        qstat_succeeded_without_request = False
        for attempt in range(1, immediate_qstat_attempts + 1):
            candidate = _run(
                run_command,
                ["qstat", "-f", normalized_id],
                cwd=submission_dir,
                environ=command_env,
            )
            classification = _classify_qstat_response(candidate, normalized_id)
            attempt_record = {
                "attempt": attempt,
                "classification": classification,
                **_capture(candidate),
            }
            immediate_attempt_records.append(attempt_record)
            if classification == "permission":
                permission_error = attempt_record
                break
            if classification.startswith("success-"):
                visible = candidate
                request_was_visible = classification == "success-request-visible"
                qstat_succeeded_without_request = not request_was_visible
                break
            if attempt < immediate_qstat_attempts:
                sleep(poll_interval_s)
        receipt["immediate_qstat_attempts"] = immediate_attempt_records
        receipt["immediate_qstat"] = (
            _capture(visible) if visible is not None else immediate_attempt_records[-1]
        )
        receipt["f49_immediate"] = {
            "qstat_succeeded": visible is not None,
            "qstat_visible": request_was_visible,
        }
        if permission_error is not None:
            reason = "qstat-permission-or-ownership-error"
            receipt["outcome"] = {"kind": "f47", "reason": reason, "rc": INFRA_RC}
            receipt["qdel"] = _best_effort_qdel(
                run_command,
                request_id=request_id,
                cwd=submission_dir if submission_dir.exists() else root,
                environ=command_env,
            )
            active = False
            latched = _latch_submission_disabled(
                root,
                reason=reason,
                submission_dir=submission_dir,
                request_id=request_id,
            )
            _persist_receipt(submission_dir, root, receipt)
            _print_terminal_handoff(latched, reason)
            return INFRA_RC
        if visible is None:
            raise DispatchError("immediate-qstat-unavailable-after-retries")
        if qstat_succeeded_without_request:
            reason = "qstat-success-request-not-visible"
            receipt["outcome"] = {"kind": "f47", "reason": reason, "rc": INFRA_RC}
            receipt["qdel"] = _best_effort_qdel(
                run_command,
                request_id=request_id,
                cwd=submission_dir if submission_dir.exists() else root,
                environ=command_env,
            )
            active = False
            latched = _latch_submission_disabled(
                root,
                reason=reason,
                submission_dir=submission_dir,
                request_id=request_id,
            )
            _persist_receipt(submission_dir, root, receipt)
            _print_terminal_handoff(latched, reason)
            return INFRA_RC

        current = visible
        queue_started = submitted_at
        total_deadline = submitted_at + walltime_s + overall_grace_s
        announced_state: Optional[str] = None
        terminal_at: Optional[float] = None
        while True:
            now = clock()
            request_absent = (
                request_was_visible
                and current.returncode == 0
                and not _qstat_mentions_request(current.stdout or "", normalized_id)
            )
            state = "END" if request_absent else _scheduler_state(current.stdout or "")
            shown_state = (
                "QSTAT_ERROR" if current.returncode != 0 else state or "UNKNOWN"
            )
            receipt["state_history"].append({
                "elapsed_s": max(0.0, now - started),
                "state": shown_state,
                "qstat_rc": int(current.returncode),
                "request_present": (
                    _qstat_mentions_request(current.stdout or "", normalized_id)
                    if current.returncode == 0 else None
                ),
            })
            if shown_state != announced_state:
                _progress(f"request {normalized_id} の状態: {shown_state}")
                announced_state = shown_state
            if state == "END":
                terminal_at = now
                receipt["terminal_reason"] = (
                    "request-disappeared-after-visibility"
                    if request_absent else "scheduler-end-state"
                )
                break
            if state == "RUN" and not run_seen:
                run_seen = True
                receipt["queue_wait_s"] = max(0.0, now - queue_started)
                receipt["queue_wait_observed"] = True
            if not run_seen and now - queue_started >= queue_wait_timeout_s:
                raise DispatchError("queue-wait-timeout")
            if now >= total_deadline:
                raise DispatchError("overall-timeout")
            sleep(poll_interval_s)
            current = _run(
                run_command,
                ["qstat", "-f", normalized_id],
                cwd=submission_dir,
                environ=command_env,
            )

        if not run_seen:
            assert terminal_at is not None
            receipt["queue_wait_s"] = max(0.0, terminal_at - queue_started)
            receipt["queue_wait_observed"] = False
        _progress(f"request {normalized_id} の成果物収集を開始します")
        collection_deadline = clock() + accounting_grace_s
        result: Optional[dict[str, Any]] = None
        stdout_record: Optional[dict[str, Any]] = None
        stderr_record: Optional[dict[str, Any]] = None
        marker_valid = False
        marker_record: dict[str, Any] = {}
        while True:
            result_path = submission_dir / "result.json"
            try:
                if result_path.is_file() and not result_path.is_symlink():
                    result = _read_json_object(result_path)
                stdout_path = _find_log(
                    submission_dir, stream="stdout", request_id=request_id,
                )
                stderr_path = _find_log(
                    submission_dir, stream="stderr", request_id=request_id,
                )
                if stdout_path is not None:
                    stdout_record = _bounded_log(
                        stdout_path, limit=log_limit_bytes,
                    )
                if stderr_path is not None:
                    stderr_record = _bounded_log(
                        stderr_path, limit=log_limit_bytes,
                    )
                marker_valid, marker_record = _compute_marker_evidence(
                    submission_dir, request_id,
                )
            except DispatchError:
                raise
            if (
                result is not None
                and stdout_record is not None
                and stderr_record is not None
                and _accounting_present(stderr_record, request_id)
                and marker_valid
            ):
                break
            if clock() >= collection_deadline:
                receipt["collection"] = {
                    "result_present": result is not None,
                    "stdout": stdout_record,
                    "stderr": stderr_record,
                    "accounting_present": (
                        stderr_record is not None
                        and _accounting_present(stderr_record, request_id)
                    ),
                    "compute_marker": marker_record,
                }
                if not marker_valid:
                    reason = "compute-marker-not-observed"
                    receipt["outcome"] = {
                        "kind": "f47",
                        "reason": reason,
                        "rc": INFRA_RC,
                    }
                    receipt["qdel"] = _best_effort_qdel(
                        run_command,
                        request_id=request_id,
                        cwd=submission_dir if submission_dir.exists() else root,
                        environ=command_env,
                    )
                    active = False
                    latched = _latch_submission_disabled(
                        root,
                        reason=reason,
                        submission_dir=submission_dir,
                        request_id=request_id,
                    )
                    _persist_receipt(submission_dir, root, receipt)
                    _print_terminal_handoff(latched, reason)
                    return INFRA_RC
                raise DispatchError("result/log/accounting-grace-expired")
            sleep(poll_interval_s)

        receipt["result"] = result
        receipt["scheduler_logs"] = {
            "stdout": stdout_record,
            "stderr": stderr_record,
            "accounting_present": True,
        }
        receipt["f49_compute_marker"] = marker_record
        result_id = result.get("pbs_jobid")
        child_rc = result.get("child_rc")
        if type(result_id) is not str or (
            _normalize_request_id(result_id) != normalized_id
        ):
            raise DispatchError("result の PBS job ID が submit receipt と不一致です")
        if result.get("stage") != "child":
            raise DispatchError(f"job bootstrap failure: stage={result.get('stage')}")
        if type(child_rc) is not int:
            raise DispatchError("result.child_rc が int ではありません")

        receipt["outcome"] = {
            "kind": "child",
            "rc": child_rc,
            "accounting_verified": True,
        }
        persisted = _persist_receipt(submission_dir, root, receipt)
        active = False
        if persisted is None:
            print(
                "Pegasus dispatch receipt を永続化できませんでした。",
                file=sys.stderr,
                flush=True,
            )
            return INFRA_RC
        _progress(f"receipt を {persisted} へ保存しました (child rc={child_rc})")
        return child_rc
    except BaseException as exc:
        receipt["outcome"] = {
            "kind": "infra",
            "reason": f"{type(exc).__name__}: {exc}",
            "rc": INFRA_RC,
        }
        if active:
            if request_id is None:
                discovered, discovery = _discover_request_id(
                    run_command,
                    job_name=job_name,
                    submission_dir=submission_dir,
                    environ=command_env,
                )
                receipt["request_id_discovery"] = discovery
                if discovered is not None:
                    request_id = discovered
                    receipt["request_id"] = discovered
                    receipt["normalized_request_id"] = _normalize_request_id(discovered)
            if request_id is not None:
                receipt["qdel"] = _best_effort_qdel(
                    run_command,
                    request_id=request_id,
                    cwd=submission_dir if submission_dir.exists() else root,
                    environ=command_env,
                )
            else:
                receipt["qdel"] = {
                    "attempted": False,
                    "reason": "qsub accepted but request ID discovery failed",
                    "job_name": job_name,
                    "submission_dir": str(submission_dir),
                }
        _persist_receipt(submission_dir, root, receipt)
        print(
            f"Pegasus dispatch infrastructure failure: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return INFRA_RC
    finally:
        for signum, handler in old_handlers.items():
            try:
                signal.signal(signum, handler)
            except (ValueError, OSError):
                pass


def dispatch(
    args: Sequence[str],
    *,
    task: str = DEFAULT_TASK,
    repo_root: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
    output_root: Optional[Path] = None,
    walltime: str = DEFAULT_WALLTIME,
    queue_wait_timeout_s: float = DEFAULT_QUEUE_WAIT_TIMEOUT_S,
    overall_grace_s: float = DEFAULT_OVERALL_GRACE_S,
    accounting_grace_s: float = DEFAULT_ACCOUNTING_GRACE_S,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    log_limit_bytes: int = DEFAULT_LOG_LIMIT_BYTES,
    immediate_qstat_attempts: int = DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS,
    run_command: CommandRunner = subprocess.run,
    clock: Clock = time.monotonic,
    sleep: Sleeper = time.sleep,
    nonce: Optional[str] = None,
) -> int:
    """setup 段の例外も含め、dispatcher infrastructure rc を 16 に畳む。"""

    old_handlers: dict[int, Any] = {}

    def abort_during_setup(signum, _frame):
        raise _SignalAbort(signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            old_handlers[signum] = signal.signal(signum, abort_during_setup)
        except (ValueError, OSError):
            pass
    try:
        return _dispatch_impl(
            args,
            task=task,
            repo_root=repo_root,
            environ=environ,
            output_root=output_root,
            walltime=walltime,
            queue_wait_timeout_s=queue_wait_timeout_s,
            overall_grace_s=overall_grace_s,
            accounting_grace_s=accounting_grace_s,
            poll_interval_s=poll_interval_s,
            log_limit_bytes=log_limit_bytes,
            immediate_qstat_attempts=immediate_qstat_attempts,
            run_command=run_command,
            clock=clock,
            sleep=sleep,
            nonce=nonce,
        )
    except (Exception, KeyboardInterrupt) as exc:
        repo = (
            Path(__file__).resolve().parents[2]
            if repo_root is None else Path(repo_root).resolve()
        )
        root = (
            repo / "output" / "pegasus-dispatch"
            if output_root is None else Path(output_root).resolve()
        )
        try:
            root.mkdir(parents=True, exist_ok=True)
            receipt_nonce = (
                nonce
                if nonce is not None
                and re.fullmatch(r"[A-Za-z0-9._-]+", nonce) is not None
                else secrets.token_hex(8)
            )
            setup_receipt = root / f"receipt-setup-{receipt_nonce}.json"
            _write_json_x(setup_receipt, {
                "schema_version": _RECEIPT_SCHEMA,
                "outcome": {
                    "kind": "infra",
                    "reason": f"{type(exc).__name__}: {exc}",
                    "rc": INFRA_RC,
                },
                "request": {"task": task, "args": list(args)},
            })
        except (Exception, KeyboardInterrupt):
            pass
        print(
            f"Pegasus dispatch setup failure: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return INFRA_RC
    finally:
        for signum, handler in old_handlers.items():
            try:
                signal.signal(signum, handler)
            except (ValueError, OSError):
                pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if len(values) == 2 and values[0] == "--job-run":
        return _job_run(Path(values[1]).resolve())

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--walltime", default=DEFAULT_WALLTIME)
    parser.add_argument(
        "--queue-wait-timeout",
        type=float,
        default=DEFAULT_QUEUE_WAIT_TIMEOUT_S,
    )
    parser.add_argument(
        "--overall-grace",
        type=float,
        default=DEFAULT_OVERALL_GRACE_S,
    )
    parser.add_argument(
        "--accounting-grace",
        type=float,
        default=DEFAULT_ACCOUNTING_GRACE_S,
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_S,
    )
    # CLI 面でも task を閉集合に固定する (親・子の二層 fail-closed の 3 点目)。
    parser.add_argument("--task", choices=tuple(TASKS), default=DEFAULT_TASK)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(values)
    child_args = list(parsed.args)
    if child_args[:1] == ["--"]:
        child_args = child_args[1:]
    return dispatch(
        child_args,
        task=parsed.task,
        walltime=parsed.walltime,
        queue_wait_timeout_s=parsed.queue_wait_timeout,
        overall_grace_s=parsed.overall_grace,
        accounting_grace_s=parsed.accounting_grace,
        poll_interval_s=parsed.poll_interval,
    )


if __name__ == "__main__":
    sys.exit(main())
