# -*- coding: utf-8 -*-
"""Pegasus execution queue の現在状態を観測する stdlib-only leaf。"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass


QSTAT_TIMEOUT_S = 5.0


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
    columns = None

    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            if stripped.startswith("[EXECUTION QUEUE]"):
                in_execution = True
                columns = None
                continue
            if in_execution:
                break
            continue
        if not in_execution or not stripped:
            continue

        fields = stripped.split()
        if columns is None:
            if fields and fields[0] == "QueueName":
                required = ("QueueName", "ENA", "STS", "QUE", "RUN")
                if not all(name in fields for name in required):
                    return None
                columns = {name: fields.index(name) for name in required}
            continue

        if stripped.startswith("<TOTAL>") or set(stripped) <= {"-", " "}:
            continue
        queue_index = columns["QueueName"]
        if len(fields) <= queue_index or fields[queue_index] != target:
            continue
        if len(fields) <= max(columns.values()):
            return None

        ena = fields[columns["ENA"]]
        sts = fields[columns["STS"]]
        if ena not in {"ENA", "DIS"} or sts not in {"ACT", "INA"}:
            return None
        try:
            queued = int(fields[columns["QUE"]])
            running = int(fields[columns["RUN"]])
        except (TypeError, ValueError):
            return None
        if queued < 0 or running < 0:
            return None

        return QueueState(
            queue=target,
            enabled=ena == "ENA",
            active=sts == "ACT",
            queued=queued,
            running=running,
            raw_line=line,
            ena=ena,
            sts=sts,
        )

    return None


def queue_state(queue: str | None = None, *, runner=None) -> QueueState | None:
    """対象 execution queue を 1 回観測し、観測不能なら None を返す。"""
    try:
        target = _default_queue() if queue is None else queue
        if not isinstance(target, str) or not target:
            return None
        run = subprocess.run if runner is None else runner
        result = run(
            ["qstat", "-Q"],
            capture_output=True,
            text=True,
            timeout=QSTAT_TIMEOUT_S,
            check=False,
        )
        if result.returncode != 0 or not isinstance(result.stdout, str):
            return None
        return _parse_execution_queue(result.stdout, target)
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
