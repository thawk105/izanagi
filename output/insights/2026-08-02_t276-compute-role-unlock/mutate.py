#!/usr/bin/env python3
"""T-276 mutation runner; execute only after the stage-7 integration commit."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_FAIL_RE = re.compile(r"(?:^|\s)(?:FAILED|ERROR)\s+(.+)$")
_ID_RE = re.compile(r"[A-Za-z0-9._-]+")
_DISPATCH_REQUEST_RE = re.compile(
    r"(?m)^\[Pegasus dispatch\] request ID (?P<request>[A-Za-z0-9][A-Za-z0-9._-]*) "
    r"を受理しました$"
)
_DISPATCH_SUBMIT_RE = re.compile(
    r"(?m)^\[Pegasus dispatch\] job を \S+ へ投入します \([A-Za-z0-9._-]+\)$"
)
_QSTAT_REQUEST_RE = re.compile(
    r"(?im)^\s*Request\s+ID\s*[:=]\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*$"
)
_QSTAT_ABSENT_MARKERS = (
    "does not exist",
    "not found",
    "unknown request",
    "unknown job",
)
_PROCESS_GROUP_GRACE_S = 5.0
_QSTAT_DISAPPEAR_TIMEOUT_S = 30.0
_QSTAT_POLL_S = 1.0


class MutationAbort(RuntimeError):
    pass


def _run(
    argv: list[str], *, cwd: Path, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout,
    )


def _write_json(path: Path, value: MappingLike) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


MappingLike = dict[str, Any]


def _normalize_node(value: str) -> str:
    value = _ANSI_RE.sub("", value).strip()
    if " - " in value:
        value = value.split(" - ", 1)[0].strip()
    return value


def _failed_nodes(output: str) -> list[str]:
    nodes: list[str] = []
    for raw_line in output.splitlines():
        line = _ANSI_RE.sub("", raw_line)
        match = _FAIL_RE.search(line)
        if match is None:
            continue
        node = _normalize_node(match.group(1))
        if "::" in node and node not in nodes:
            nodes.append(node)
    return nodes


def _process_group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError as exc:
        raise MutationAbort(
            f"process group {process_group} の消滅を権限上照合できない"
        ) from exc
    return True


def _wait_for_process_group_exit(process_group: int, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not _process_group_exists(process_group):
            return True
        time.sleep(0.05)
    return not _process_group_exists(process_group)


def _terminate_process_group(
    process: subprocess.Popen[str],
) -> tuple[str, MappingLike]:
    """Terminate the timed-out runner and every descendant before scheduler cleanup."""

    process_group = process.pid
    record: MappingLike = {
        "process_group": process_group,
        "sigterm_sent": False,
        "sigkill_sent": False,
        "gone": False,
    }
    try:
        os.killpg(process_group, signal.SIGTERM)
        record["sigterm_sent"] = True
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        raise MutationAbort(
            f"process group {process_group} へ SIGTERM を送れない"
        ) from exc
    try:
        output, _ = process.communicate(timeout=_PROCESS_GROUP_GRACE_S)
    except subprocess.TimeoutExpired:
        output = ""
    if _process_group_exists(process_group):
        try:
            os.killpg(process_group, signal.SIGKILL)
            record["sigkill_sent"] = True
        except ProcessLookupError:
            pass
        except PermissionError as exc:
            raise MutationAbort(
                f"process group {process_group} へ SIGKILL を送れない"
            ) from exc
        try:
            output, _ = process.communicate(timeout=_PROCESS_GROUP_GRACE_S)
        except subprocess.TimeoutExpired as exc:
            raise MutationAbort(
                f"process group {process_group} の leader を reap できない"
            ) from exc
    if not _wait_for_process_group_exit(process_group, _PROCESS_GROUP_GRACE_S):
        raise MutationAbort(f"process group {process_group} が timeout 後も生存")
    record["gone"] = True
    if isinstance(output, bytes):
        output = output.decode("utf-8", errors="replace")
    return output or "", record


def _qstat_confirms_absent(
    result: subprocess.CompletedProcess[str], request_id: str
) -> bool:
    output = result.stdout or ""
    observed = set(_QSTAT_REQUEST_RE.findall(output))
    if result.returncode == 0:
        return request_id not in observed
    folded = output.casefold()
    return any(marker in folded for marker in _QSTAT_ABSENT_MARKERS)


def _cancel_dispatched_requests(*, output: str, cwd: Path) -> MappingLike:
    """Cancel every logged request and prove qstat disappearance."""

    request_ids = sorted(set(_DISPATCH_REQUEST_RE.findall(output)))
    submission_started = _DISPATCH_SUBMIT_RE.search(output) is not None
    hostname = os.uname().nodename.split(".", 1)[0]
    on_login = re.fullmatch(r"pegasus0[0-9]+", hostname) is not None
    record: MappingLike = {
        "hostname": hostname,
        "pegasus_login": on_login,
        "submission_started": submission_started,
        "request_ids": request_ids,
        "requests": [],
        "all_gone": False,
    }
    if on_login and submission_started and not request_ids:
        raise MutationAbort(
            "timeout 後の dispatch log から request ID を一意に捕捉できない"
        )
    for request_id in request_ids:
        qdel = _run(["qdel", request_id], cwd=cwd, timeout=10.0)
        request_record: MappingLike = {
            "request_id": request_id,
            "qdel_rc": qdel.returncode,
            "qdel_output_sha256": hashlib.sha256(
                (qdel.stdout or "").encode("utf-8")
            ).hexdigest(),
            "qstat_attempts": [],
            "gone": False,
        }
        deadline = time.monotonic() + _QSTAT_DISAPPEAR_TIMEOUT_S
        while True:
            qstat = _run(["qstat", "-f", request_id], cwd=cwd, timeout=10.0)
            absent = _qstat_confirms_absent(qstat, request_id)
            request_record["qstat_attempts"].append({
                "rc": qstat.returncode,
                "output_sha256": hashlib.sha256(
                    (qstat.stdout or "").encode("utf-8")
                ).hexdigest(),
                "absent": absent,
            })
            if absent:
                request_record["gone"] = True
                break
            if time.monotonic() >= deadline:
                raise MutationAbort(
                    f"request {request_id} の qstat 消滅を照合できない"
                )
            time.sleep(_QSTAT_POLL_S)
        record["requests"].append(request_record)
    record["all_gone"] = all(
        request["gone"] for request in record["requests"]
    )
    return record


def _target(repo: Path, relative: str) -> Path:
    candidate = (repo / relative).resolve()
    try:
        candidate.relative_to(repo)
    except ValueError as exc:
        raise MutationAbort(f"repo 外の mutation target: {relative}") from exc
    if not candidate.is_file():
        raise MutationAbort(f"mutation target が regular file でない: {relative}")
    return candidate


def _validate_spec(repo: Path, entries: object) -> dict[str, int]:
    if not isinstance(entries, list) or not entries:
        raise MutationAbort("mutations.json は非空 array 必須")
    anchor_counts: dict[str, int] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {
            "id", "kind", "file", "old", "new", "nodes", "expect",
            "expect_timeout",
        }:
            raise MutationAbort(f"spec[{index}] key が exact でない")
        mutation_id = entry["id"]
        if not isinstance(mutation_id, str) or _ID_RE.fullmatch(mutation_id) is None:
            raise MutationAbort(f"spec[{index}].id が不正")
        kind = entry["kind"]
        if kind not in {"mutation", "diagnostic-pin", "positive"}:
            raise MutationAbort(f"{mutation_id}: kind が不正")
        if type(entry["expect_timeout"]) is not bool:
            raise MutationAbort(f"{mutation_id}: expect_timeout は bool 必須")
        if entry["expect_timeout"] and kind != "mutation":
            raise MutationAbort(
                f"{mutation_id}: timeout 受理は hang mutation だけ"
            )
        if not isinstance(entry["file"], str):
            raise MutationAbort(f"{mutation_id}: file は string 必須")
        target = _target(repo, entry["file"])
        if not isinstance(entry["nodes"], list) or not entry["nodes"] or any(
            not isinstance(node, str) or "::" not in node for node in entry["nodes"]
        ):
            raise MutationAbort(f"{mutation_id}: nodes が不正")
        if not isinstance(entry["expect"], list) or any(
            not isinstance(node, str) or "::" not in node for node in entry["expect"]
        ):
            raise MutationAbort(f"{mutation_id}: expect が不正")
        positive = kind == "positive"
        if positive != mutation_id.startswith("P"):
            raise MutationAbort(f"{mutation_id}: kind/id の positive 分類が不一致")
        if positive:
            if entry["old"] is not None or entry["new"] is not None or entry["expect"]:
                raise MutationAbort(f"{mutation_id}: positive spec が不正")
            anchor_counts[mutation_id] = 0
            continue
        if (
            not isinstance(entry["old"], str)
            or not entry["old"]
            or not isinstance(entry["new"], str)
            or not entry["expect"]
        ):
            raise MutationAbort(f"{mutation_id}: negative spec が不正")
        count = target.read_text(encoding="utf-8").count(entry["old"])
        anchor_counts[mutation_id] = count
        if count != 1:
            raise MutationAbort(
                f"{mutation_id}: fix 後 anchor count は 1 必須 (actual={count})"
            )
    return anchor_counts


def _test_entry(
    *, repo: Path, wave_dir: Path, entry: MappingLike, timeout_s: float
) -> MappingLike:
    mutation_id = entry["id"]
    kind = entry["kind"]
    positive = kind == "positive"
    target = _target(repo, entry["file"])
    original = target.read_text(encoding="utf-8")
    record: MappingLike = {
        "id": mutation_id,
        "kind": kind,
        "file": entry["file"],
        "nodes": list(entry["nodes"]),
        "expect": list(entry["expect"]),
        "positive": positive,
        "diff_stat": "",
        "rc": None,
        "failed_nodes": [],
        "status": None,
        "timed_out": False,
        "expect_timeout": entry["expect_timeout"],
        "process_cleanup": None,
        "scheduler_cleanup": None,
        "restored": None,
    }
    output = ""
    started = time.monotonic()
    safe_to_restore = True
    try:
        if not positive:
            mutated = original.replace(entry["old"], entry["new"], 1)
            target.write_text(mutated, encoding="utf-8")
            stat_result = _run(
                ["git", "diff", "--stat", "--", entry["file"]], cwd=repo
            )
            name_result = _run(
                ["git", "diff", "--name-only", "--", entry["file"]], cwd=repo
            )
            record["diff_stat"] = stat_result.stdout.strip()
            if (
                stat_result.returncode != 0
                or not record["diff_stat"]
                or name_result.returncode != 0
                or name_result.stdout.splitlines() != [entry["file"]]
            ):
                raise MutationAbort(
                    f"{mutation_id}: git diff --stat で単一注入を確認できない"
                )
        command = [
            sys.executable,
            "tools/run_tests.py",
            *entry["nodes"],
            "-rf",
        ]
        process = subprocess.Popen(
            command,
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            output, _ = process.communicate(timeout=timeout_s)
            record["rc"] = process.returncode
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
            record["rc"] = None
            safe_to_restore = False
            output, record["process_cleanup"] = _terminate_process_group(process)
            record["scheduler_cleanup"] = _cancel_dispatched_requests(
                output=output,
                cwd=repo,
            )
            safe_to_restore = True
            if entry["expect_timeout"]:
                record["status"] = "TIMEOUT"
            else:
                record["status"] = "UNEXPECTED-TIMEOUT"
                record["fail_closed_abort"] = (
                    f"{mutation_id}: expect_timeout=false の entry が timeout"
                )
    finally:
        if not positive and safe_to_restore:
            target.write_text(original, encoding="utf-8")
        record["restored"] = target.read_text(encoding="utf-8") == original
        if safe_to_restore and not record["restored"]:
            raise MutationAbort(f"{mutation_id}: read_text 内容比較で復元失敗")
        if not safe_to_restore:
            raise MutationAbort(
                f"{mutation_id}: live job 不在を照合できず source 復元を保留"
            )

    record["duration_s"] = round(time.monotonic() - started, 3)
    record["output_sha256"] = hashlib.sha256(output.encode("utf-8")).hexdigest()
    log_dir = wave_dir / "mutation-logs"
    log_dir.mkdir(exist_ok=True)
    (log_dir / f"{mutation_id}.log").write_text(output, encoding="utf-8")
    failed = _failed_nodes(output)
    record["failed_nodes"] = failed
    if record["timed_out"]:
        return record
    rc = record["rc"]
    if rc != 0 and not failed:
        record["status"] = "RED-BUT-UNEXPECTED-NODE"
        record["fail_closed_abort"] = (
            f"{mutation_id}: rc={rc} だが失敗 node を 1 件も抽出できない"
        )
        return record
    if positive:
        record["status"] = "POSITIVE-GREEN" if rc == 0 else "POSITIVE-RED"
    elif rc == 0:
        record["status"] = (
            "DIAGNOSTIC-SURVIVED" if kind == "diagnostic-pin" else "SURVIVED"
        )
    else:
        expected = {_normalize_node(node) for node in entry["expect"]}
        actual = set(failed)
        if expected.issubset(actual):
            record["status"] = (
                "DIAGNOSTIC-PINNED"
                if kind == "diagnostic-pin"
                else "KILLED"
            )
        else:
            record["status"] = "RED-BUT-UNEXPECTED-NODE"
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--timeout-seconds", type=float, default=900.0)
    args = parser.parse_args(argv)
    if args.timeout_seconds <= 0:
        raise MutationAbort("timeout は正数必須")
    repo = args.repo.resolve()
    wave_dir = Path(__file__).resolve().parent
    spec_path = wave_dir / "mutations.json"
    result_path = wave_dir / "mutation-results.json"
    if not (repo / "tools/run_tests.py").is_file() or not (repo / ".git").exists():
        raise MutationAbort(f"repo root でない: {repo}")

    lock_path = wave_dir / "mutate.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise MutationAbort("mutation harness の flock 取得に失敗") from exc

        status = _run(["git", "status", "--porcelain"], cwd=repo)
        if status.returncode != 0 or status.stdout.strip():
            raise MutationAbort("mutation 開始時の worktree は clean 必須")
        entries = json.loads(spec_path.read_text(encoding="utf-8"))
        anchor_counts = _validate_spec(repo, entries)
        head = _run(["git", "rev-parse", "HEAD"], cwd=repo)
        if head.returncode != 0:
            raise MutationAbort("HEAD を解決できない")
        results: MappingLike = {
            "schema_version": "t276-mutation-results/v1",
            "repo": str(repo),
            "head": head.stdout.strip(),
            "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "anchor_counts": anchor_counts,
            "entries": [],
        }
        _write_json(result_path, results)
        try:
            for entry in entries:
                record = _test_entry(
                    repo=repo,
                    wave_dir=wave_dir,
                    entry=entry,
                    timeout_s=args.timeout_seconds,
                )
                results["entries"].append(record)
                _write_json(result_path, results)
                if "fail_closed_abort" in record:
                    raise MutationAbort(record["fail_closed_abort"])
        except BaseException as exc:
            results["aborted"] = f"{type(exc).__name__}: {exc}"
            results["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            _write_json(result_path, results)
            raise
        results["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        results["aborted"] = None
        results["summary"] = {
            "killed": sum(
                entry["status"] == "KILLED" for entry in results["entries"]
            ),
            "diagnostic_pinned": sum(
                entry["status"] == "DIAGNOSTIC-PINNED"
                for entry in results["entries"]
            ),
            "positive_green": sum(
                entry["status"] == "POSITIVE-GREEN"
                for entry in results["entries"]
            ),
            "expected_timeout": sum(
                entry["status"] == "TIMEOUT" for entry in results["entries"]
            ),
        }
        _write_json(result_path, results)
    accepted = {"KILLED", "DIAGNOSTIC-PINNED", "POSITIVE-GREEN", "TIMEOUT"}
    return 1 if any(entry["status"] not in accepted for entry in results["entries"]) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MutationAbort as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        raise SystemExit(2)
