# -*- coding: utf-8 -*-
"""Pegasus execution queue の現在状態を観測する stdlib-only leaf。"""
from __future__ import annotations

import os
import selectors
import subprocess
import time
from dataclasses import dataclass


QSTAT_TIMEOUT_S = 5.0
QSTAT_OUTPUT_LIMIT_BYTES = 256 * 1024


@dataclass(frozen=True)
class QueueState:
    """``qstat -Q`` から読んだ対象 execution queue の状態。"""

    queue: str
    enabled: bool
    active: bool
    queued: int
    running: int
    raw_line: str
    ena: str
    sts: str

    @property
    def available(self) -> bool:
        """投入を受理し、かつ実行を開始できるときだけ True。"""
        return self.enabled and self.active


def _default_queue() -> str | None:
    """dispatch 先の正本を遅延 import する。"""
    try:
        from tools.pegasus.dispatch_compute import DEFAULT_QUEUE
    except Exception:
        return None
    if not isinstance(DEFAULT_QUEUE, str) or not DEFAULT_QUEUE:
        return None
    return DEFAULT_QUEUE


def _parse_execution_queue(output: str, target: str) -> QueueState | None:
    in_execution = False
    execution_tables = 0
    columns: dict[str, int] | None = None
    column_count = 0
    matches: list[QueueState] = []
    invalid = False

    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            if stripped.startswith("[EXECUTION QUEUE]"):
                execution_tables += 1
                in_execution = True
                columns = None
                column_count = 0
                continue
            in_execution = False
            columns = None
            continue
        if not in_execution or not stripped:
            continue

        fields = stripped.split()
        if columns is None:
            if fields and fields[0] == "QueueName":
                required = ("QueueName", "ENA", "STS", "QUE", "RUN")
                if not all(fields.count(name) == 1 for name in required):
                    invalid = True
                    continue
                columns = {name: fields.index(name) for name in required}
                column_count = len(fields)
            continue

        if stripped.startswith("<TOTAL>") or set(stripped) <= {"-", " "}:
            continue
        if fields[0] == "QueueName":
            invalid = True
            continue
        queue_index = columns["QueueName"]
        if len(fields) <= queue_index or fields[queue_index] != target:
            continue
        if len(fields) != column_count:
            invalid = True
            continue

        ena = fields[columns["ENA"]]
        sts = fields[columns["STS"]]
        if ena not in {"ENA", "DIS"} or sts not in {"ACT", "INA"}:
            invalid = True
            continue
        try:
            queued = int(fields[columns["QUE"]])
            running = int(fields[columns["RUN"]])
        except (TypeError, ValueError):
            invalid = True
            continue
        if queued < 0 or running < 0:
            invalid = True
            continue

        matches.append(
            QueueState(
                queue=target,
                enabled=ena == "ENA",
                active=sts == "ACT",
                queued=queued,
                running=running,
                raw_line=line,
                ena=ena,
                sts=sts,
            )
        )

    if invalid or execution_tables != 1 or len(matches) != 1:
        return None
    return matches[0]


def _bounded_output(value: object) -> str | None:
    if isinstance(value, bytes):
        if len(value) > QSTAT_OUTPUT_LIMIT_BYTES:
            return None
        try:
            return value.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return None
    if isinstance(value, str):
        try:
            encoded = value.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            return None
        if len(encoded) > QSTAT_OUTPUT_LIMIT_BYTES:
            return None
        return value
    return None


def _run_qstat_bounded(command: list[str], *, timeout: float, env: dict[str, str]):
    """production の qstat を各 stream 上限+1 bytes までだけ読む。"""

    process = None
    selector = selectors.DefaultSelector()
    streams = []
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        assert process.stdout is not None and process.stderr is not None
        streams = [process.stdout, process.stderr]
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        deadline = time.monotonic() + timeout
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, timeout)
            events = selector.select(remaining)
            if not events:
                raise subprocess.TimeoutExpired(command, timeout)
            for key, _mask in events:
                buffer = buffers[key.data]
                read_size = min(65536, QSTAT_OUTPUT_LIMIT_BYTES + 1 - len(buffer))
                chunk = os.read(key.fd, read_size)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffer.extend(chunk)
                if len(buffer) > QSTAT_OUTPUT_LIMIT_BYTES:
                    return None
        remaining = max(0.0, deadline - time.monotonic())
        returncode = process.wait(timeout=remaining)
        return subprocess.CompletedProcess(
            command,
            returncode,
            bytes(buffers["stdout"]),
            bytes(buffers["stderr"]),
        )
    except Exception:
        return None
    finally:
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass
            try:
                process.wait(timeout=1.0)
            except Exception:
                pass
        for stream in streams:
            try:
                stream.close()
            except Exception:
                pass
        selector.close()


def queue_state(queue: str | None = None, *, runner=None) -> QueueState | None:
    """対象 execution queue を 1 回観測し、観測不能なら None を返す。"""
    try:
        target = _default_queue() if queue is None else queue
        if not isinstance(target, str) or not target:
            return None
        command = ["qstat", "-Q"]
        environment = {**os.environ, "LC_ALL": "C"}
        if runner is None:
            result = _run_qstat_bounded(
                command,
                timeout=QSTAT_TIMEOUT_S,
                env=environment,
            )
        else:
            result = runner(
                command,
                capture_output=True,
                text=False,
                timeout=QSTAT_TIMEOUT_S,
                check=False,
                env=environment,
            )
        if result is None:
            return None
        stdout = _bounded_output(result.stdout)
        stderr = _bounded_output(result.stderr)
        if result.returncode != 0 or stdout is None or stderr is None:
            return None
        return _parse_execution_queue(stdout, target)
    except Exception:
        return None


def dispatch_possible(
    queue: str | None = None,
    *,
    runner=None,
) -> tuple[bool, str]:
    """dispatch 可否と、そのまま表示できる日本語の根拠を返す。"""
    target = _default_queue() if queue is None else queue
    target_label = target if isinstance(target, str) and target else "対象キュー"
    state = queue_state(queue, runner=runner)
    if state is None:
        return (
            True,
            f"キュー {target_label} は ENA=不明、STS=不明、待ち数=不明、"
            "実行数=不明です（観測不能のため可用扱い）。",
        )

    reason = (
        f"キュー {state.queue} は ENA={state.ena}、STS={state.sts}、"
        f"待ち数={state.queued}、実行数={state.running}"
    )
    if state.available:
        return True, reason + "で、現在利用できます。"
    return False, reason + "で、現在利用できません。"


def main() -> int:
    possible, reason = dispatch_possible()
    print(reason)
    return 0 if possible else 1


if __name__ == "__main__":
    raise SystemExit(main())
