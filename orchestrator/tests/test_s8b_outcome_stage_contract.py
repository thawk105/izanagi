# -*- coding: utf-8 -*-
"""oracle outcome 段階 truth-table の独立 golden 検査。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ORCHESTRATOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_outcome_stage_contract as contract  # noqa: E402


def _row(
        *, build_done: int, verify_sequence: tuple[tuple[str, str], ...],
        bench_done: int, abort: int, commit: int,
        abort_workload: str) -> contract.StageEvidence:
    return contract.StageEvidence(
        build_start=1, build_done=build_done,
        verify_sequence=verify_sequence, bench_done=bench_done,
        abort=abort, commit=commit, abort_workload=abort_workload,
    )


_GOLDEN = {
    "committed": (_row(
        build_done=1, verify_sequence=(("legacy", "pass"), ("s2", "pass")),
        bench_done=1, abort=0, commit=1, abort_workload="absent",
    ),),
    "correctness-red": (
        _row(
            build_done=1, verify_sequence=(("legacy", "red"),), bench_done=0,
            abort=1, commit=0, abort_workload="legacy",
        ),
        _row(
            build_done=1, verify_sequence=(("legacy", "pass"), ("s2", "red")),
            bench_done=0, abort=1, commit=0, abort_workload="s2",
        ),
    ),
    "build-failed": (_row(
        build_done=0, verify_sequence=(), bench_done=0,
        abort=1, commit=0, abort_workload="absent",
    ),),
    "timeout": (
        _row(
            build_done=1, verify_sequence=(), bench_done=0,
            abort=1, commit=0, abort_workload="legacy",
        ),
        _row(
            build_done=1, verify_sequence=(("legacy", "pass"),), bench_done=0,
            abort=1, commit=0, abort_workload="s2",
        ),
    ),
    "bench-failed": (_row(
        build_done=1, verify_sequence=(("legacy", "pass"), ("s2", "pass")),
        bench_done=0, abort=1, commit=0, abort_workload="absent",
    ),),
    "verify-inconclusive": (
        _row(
            build_done=1, verify_sequence=(), bench_done=0,
            abort=1, commit=0, abort_workload="legacy",
        ),
        _row(
            build_done=1, verify_sequence=(("legacy", "pass"),), bench_done=0,
            abort=1, commit=0, abort_workload="s2",
        ),
    ),
    "binary-mismatch": (_row(
        build_done=1, verify_sequence=(), bench_done=0,
        abort=1, commit=0, abort_workload="absent",
    ),),
}


def test_outcome_stage_truth_table_matches_independent_golden():
    assert contract.PIPELINE_STAGES == frozenset({
        "build_start", "build_done", "verify_done", "bench_done", "abort", "commit",
    })
    assert contract.OUTCOMES == frozenset(_GOLDEN)
    assert set(contract.OUTCOME_STAGE_TRUTH_TABLE) == set(_GOLDEN)
    for outcome, rows in _GOLDEN.items():
        assert contract.OUTCOME_STAGE_TRUTH_TABLE[outcome] == rows
        assert all(contract.matches(outcome, evidence) for evidence in rows)


def test_leaf_import_loads_no_other_campaign_module():
    script = f"""
import json
import sys
sys.path.insert(0, {str(ORCHESTRATOR.parent)!r})
import orchestrator.campaign.s8b_outcome_stage_contract
print(json.dumps(sorted(
    name for name in sys.modules
    if name.startswith('orchestrator.campaign.')
    and name != 'orchestrator.campaign.s8b_outcome_stage_contract'
)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert json.loads(completed.stdout) == []


@pytest.mark.parametrize(("outcome", "evidence"), (
    (
        "committed",
        _row(
            build_done=1, verify_sequence=(("s2", "pass"), ("legacy", "pass")),
            bench_done=1, abort=0, commit=1, abort_workload="absent",
        ),
    ),
    (
        "correctness-red",
        _row(
            build_done=1, verify_sequence=(("s2", "red"), ("legacy", "pass")),
            bench_done=0, abort=1, commit=0, abort_workload="s2",
        ),
    ),
    (
        "timeout",
        _row(
            build_done=1, verify_sequence=(("s2", "pass"), ("legacy", "pass")),
            bench_done=0, abort=1, commit=0, abort_workload="s2",
        ),
    ),
))
def test_reversed_or_post_frontier_verify_sequence_never_matches(outcome, evidence):
    assert not contract.matches(outcome, evidence)


def test_invalid_abort_workload_state_matches_no_row():
    evidence = _row(
        build_done=1, verify_sequence=(("legacy", "pass"), ("s2", "pass")),
        bench_done=1, abort=0, commit=1, abort_workload="invalid",
    )
    assert all(not contract.matches(outcome, evidence) for outcome in contract.OUTCOMES)


def test_invalid_verify_state_matches_no_row():
    evidence = _row(
        build_done=1, verify_sequence=(("legacy", "invalid"),),
        bench_done=0, abort=1, commit=0, abort_workload="legacy",
    )
    assert all(not contract.matches(outcome, evidence) for outcome in contract.OUTCOMES)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
