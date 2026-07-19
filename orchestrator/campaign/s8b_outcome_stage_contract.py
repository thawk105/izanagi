# -*- coding: utf-8 -*-
"""8b oracle outcome と WAL 段階証拠の stdlib-only 契約。

report から独立した leaf とし、段階の存在・順序・abort workload frontier を
単一の truth-table で照合する。他の campaign module は import しない。
"""
from __future__ import annotations

from dataclasses import dataclass


PIPELINE_STAGES: frozenset[str] = frozenset({
    "build_start", "build_done", "verify_done", "bench_done", "abort", "commit",
})

OUTCOMES: frozenset[str] = frozenset({
    "committed", "correctness-red", "build-failed", "timeout", "bench-failed",
    "verify-inconclusive", "binary-mismatch",
})

_ABORT_WORKLOAD_STATES = frozenset({"absent", "invalid", "legacy", "s2"})


@dataclass(frozen=True, slots=True)
class StageEvidence:
    """一つの trial window から射影した順序付き段階証拠。"""

    build_start: int
    build_done: int
    verify_sequence: tuple[tuple[str, str], ...]
    bench_done: int
    abort: int
    commit: int
    abort_workload: str

    def __post_init__(self) -> None:
        for name in ("build_start", "build_done", "bench_done", "abort", "commit"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} は 0 以上の整数でなければならない")
        if type(self.verify_sequence) is not tuple or any(
                type(item) is not tuple or len(item) != 2
                or any(type(value) is not str for value in item)
                for item in self.verify_sequence):
            raise ValueError("verify_sequence は (workload, state) の tuple でなければならない")
        if (type(self.abort_workload) is not str
                or self.abort_workload not in _ABORT_WORKLOAD_STATES):
            raise ValueError("abort_workload が閉集合外")


def _evidence(
        *, build_done: int, verify_sequence: tuple[tuple[str, str], ...],
        bench_done: int, abort: int, commit: int,
        abort_workload: str) -> StageEvidence:
    return StageEvidence(
        build_start=1,
        build_done=build_done,
        verify_sequence=verify_sequence,
        bench_done=bench_done,
        abort=abort,
        commit=commit,
        abort_workload=abort_workload,
    )


OUTCOME_STAGE_TRUTH_TABLE: dict[str, tuple[StageEvidence, ...]] = {
    "committed": (_evidence(
        build_done=1,
        verify_sequence=(("legacy", "pass"), ("s2", "pass")),
        bench_done=1, abort=0, commit=1, abort_workload="absent",
    ),),
    "correctness-red": (
        _evidence(
            build_done=1, verify_sequence=(("legacy", "red"),),
            bench_done=0, abort=1, commit=0, abort_workload="legacy",
        ),
        _evidence(
            build_done=1,
            verify_sequence=(("legacy", "pass"), ("s2", "red")),
            bench_done=0, abort=1, commit=0, abort_workload="s2",
        ),
    ),
    "build-failed": (_evidence(
        build_done=0, verify_sequence=(), bench_done=0,
        abort=1, commit=0, abort_workload="absent",
    ),),
    "timeout": (
        _evidence(
            build_done=1, verify_sequence=(), bench_done=0,
            abort=1, commit=0, abort_workload="legacy",
        ),
        _evidence(
            build_done=1, verify_sequence=(("legacy", "pass"),), bench_done=0,
            abort=1, commit=0, abort_workload="s2",
        ),
    ),
    "bench-failed": (_evidence(
        build_done=1,
        verify_sequence=(("legacy", "pass"), ("s2", "pass")),
        bench_done=0, abort=1, commit=0, abort_workload="absent",
    ),),
    "verify-inconclusive": (
        _evidence(
            build_done=1, verify_sequence=(), bench_done=0,
            abort=1, commit=0, abort_workload="legacy",
        ),
        _evidence(
            build_done=1, verify_sequence=(("legacy", "pass"),), bench_done=0,
            abort=1, commit=0, abort_workload="s2",
        ),
    ),
    "binary-mismatch": (_evidence(
        build_done=1, verify_sequence=(), bench_done=0,
        abort=1, commit=0, abort_workload="absent",
    ),),
}


def matches(outcome: str, evidence: StageEvidence) -> bool:
    """``outcome`` に許された段階証拠と完全一致するときだけ真を返す。"""
    if type(outcome) is not str or type(evidence) is not StageEvidence:
        return False
    return evidence in OUTCOME_STAGE_TRUTH_TABLE.get(outcome, ())
