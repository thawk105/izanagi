# -*- coding: utf-8 -*-
"""S-1 直接比較 driver の positive control (実 build/bench・subprocess なし)。"""
from __future__ import annotations

import contextlib
import json
import sys
import types
from pathlib import Path

import pytest

ORCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCH))

from campaign import pipeline, wal  # noqa: E402
from campaign.layout import CampaignLayout  # noqa: E402
from campaign.model import Genome  # noqa: E402
from campaign.pipeline import EvalResult, PerfConfig  # noqa: E402
from campaign import s1_direct_comparison as S  # noqa: E402


def _freeze() -> dict:
    workloads = ("balanced", "write-heavy", "read-heavy")
    configs = ("system_gate", "ident_all", "p2_2_flag_opt",
               "backoff_fixed_best", "sort_best", "stock_common")
    cells = {}
    for workload in workloads:
        for config in configs:
            cell_id = f"{workload}:{config}"
            cells[cell_id] = {
                "workload": workload, "configuration": config,
                "variant": {"flags": {"BACK_OFF": 1}},
                "source_pointer": {"path": "fixture", "key": cell_id},
            }
    order = list(cells)
    return {
        "ccbench_pin": "d706650cdb31e442bef45b9b4216951d4fb40969",
        "schedule_hash": "a" * 64,
        "operating_point": {"RECORDS": 1_000_000, "THREADS": 48,
                            "EXTIME": 3, "REPS": 5},
        "workload_flags": {
            "balanced": {"ycsb_rratio": "50"},
            "write-heavy": {"ycsb_rratio": "5"},
            "read-heavy": {"ycsb_rratio": "95"},
        },
        "cells": cells,
        "schedule": {
            "floor": [order[:] for _ in range(8)],
            "test_block_1": [order[:] for _ in range(4)],
            "test_block_2": [order[:] for _ in range(4)],
        },
    }


def _write_freeze(tmp_path: Path, document: dict | None = None) -> Path:
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(document or _freeze()), encoding="utf-8")
    return path


@contextlib.contextmanager
def _prepared(cell, pin):
    yield S.PreparedCell(Genome("silo", {"BACK_OFF": 1}), "stock", "/ccbench", "/cache")


@contextlib.contextmanager
def _fixture_checkout(worktree: Path):
    yield str(worktree)


@contextlib.contextmanager
def _fixture_backoff_patch(backoff: Path):
    backoff.write_text("""// EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
#if BACKOFF_FIXED >= 0
double now_backoff = static_cast<double>(BACKOFF_FIXED);
#else
double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
// EVOLVE-BLOCK-END silo-backoff-magnitude
""", encoding="utf-8")
    yield []


class _Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        self.value += 0.01
        return self.value


def _run(tmp_path: Path, role: str, evaluate_fn, **kwargs) -> int:
    return S.run_role(
        role, freeze_path=_write_freeze(tmp_path),
        budget_path=tmp_path / "time_ledger.json",
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        evaluate_fn=evaluate_fn, prepare_cell_fn=_prepared,
        single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None,
        **kwargs)


def _green(genome, *args, **kwargs):
    return EvalResult(genome=genome, variant=pipeline.variant_id(genome),
                      certified=True, aborted=False, fitness_tps=100.0)


def test_modified_freeze_is_refused_before_campaign_start(tmp_path):
    from campaign.s1_measurement_freeze import FreezeError

    calls = []

    def reject(document):
        raise FreezeError("modified")

    with pytest.raises(FreezeError, match="modified"):
        S.run_role(
            "floor", freeze_path=_write_freeze(tmp_path),
            budget_path=tmp_path / "budget.json", output_root=str(tmp_path / "out"),
            verify_document=reject, evaluate_fn=lambda *a, **k: calls.append(1),
            prepare_cell_fn=_prepared, single_tenant_fn=lambda: None)
    assert calls == []


def test_prepare_backoff_fixed_best_preserves_evolve_block(tmp_path, monkeypatch):
    """固定値は flag だけで選び、backoff EVOLVE-BLOCK を置換しない。"""
    from campaign import patchharness
    from campaign import p3_s4_loop as loop_axis

    worktree = tmp_path / "worktree"
    include = worktree / "include"
    include.mkdir(parents=True)
    backoff = include / "backoff.hh"
    backoff.write_text("// stock fixture\n", encoding="utf-8")
    applied = []
    monkeypatch.setattr(
        patchharness, "checkout", lambda *args, **kwargs: _fixture_checkout(worktree))
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *args, **kwargs: applied.append(args) or _fixture_backoff_patch(backoff))
    monkeypatch.setattr(S.source_digest, "resolve", lambda *args: "fixture-source")
    monkeypatch.setattr(loop_axis, "quarantine", lambda *args, **kwargs: pytest.fail("hole を置換してはならない"))
    cell = {
        "configuration": "backoff_fixed_best",
        "variant": {"backoff_us": 5, "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 5}},
    }

    with S.prepare_cell(cell, "d706650cdb31e442bef45b9b4216951d4fb40969") as prepared:
        assert prepared.genome.flags["BACKOFF_FIXED"] == 5
        content = backoff.read_text(encoding="utf-8")
        assert "EVOLVE-BLOCK-BEGIN silo-backoff-magnitude" in content
        assert "EVOLVE-BLOCK-END silo-backoff-magnitude" in content
        assert "#if BACKOFF_FIXED >= 0" in content
        assert "static_cast<double>(BACKOFF_FIXED)" in content
        assert "Backoff_.load" in content
        assert "\n5\n" not in content

    assert applied == [(str(S.ROOT / loop_axis.TEMPLATE_PATCH),
                        "d706650cdb31e442bef45b9b4216951d4fb40969")]


def test_prepare_backoff_fixed_best_refuses_flag_value_mismatch(tmp_path, monkeypatch):
    from campaign import patchharness

    worktree = tmp_path / "worktree"
    monkeypatch.setattr(patchharness, "checkout", lambda *args, **kwargs: _fixture_checkout(worktree))
    cell = {
        "configuration": "backoff_fixed_best",
        "variant": {"backoff_us": 5, "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 4}},
    }

    with pytest.raises(S.DriverError, match="backoff_us と flags.BACKOFF_FIXED が不一致"):
        with S.prepare_cell(cell, "d706650cdb31e442bef45b9b4216951d4fb40969"):
            pass


def test_s1_v2_trial_does_not_reuse_v1_campaign_id():
    campaign_id = str(S.ident.campaign_id(S.config_for(_freeze(), "develop")))
    assert campaign_id != "s1-direct-develop-direct-comparison-7bccdf1a"


def test_schedule_mutation_refused_and_deviation_recorded(tmp_path):
    document = _freeze()
    freeze_path = _write_freeze(tmp_path, document)
    layout = S.layout_for(document, "floor", output_root=str(tmp_path / "out"))
    layout.ensure()
    schedule = S.schedule_for_role(document, "floor")
    S._append_event(layout, S._base_event(schedule[0], "v0", 0))
    S._append_event(layout, S._base_event(schedule[0], "v0-duplicate", 0))

    with pytest.raises(S.ScheduleDeviation):
        S.run_role(
            "floor", freeze_path=freeze_path, budget_path=tmp_path / "budget.json",
            output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
            evaluate_fn=_green, prepare_cell_fn=_prepared,
            single_tenant_fn=lambda: None, monotonic=_Clock())
    events = S.read_session_ledger(layout)
    assert any(e.get("event") == "deviation" for e in events)
    budget = S.read_budget(tmp_path / "budget.json")
    assert any(e["note"].startswith("schedule-deviation:") for e in budget["entries"])


def test_budget_shortage_does_not_start_session(tmp_path):
    budget_path = tmp_path / "time_ledger.json"
    S.append_budget_entry(
        budget_path, role="floor", started_iso="2026-07-15T00:00:00+00:00",
        wall_s=43_199.0, phase="floor", note="existing non-retry work")
    calls = []
    rc = S.run_role(
        "floor", freeze_path=_write_freeze(tmp_path), budget_path=budget_path,
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        evaluate_fn=lambda *a, **k: calls.append(1), prepare_cell_fn=_prepared,
        single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None)
    assert rc == S.EXIT_BUDGET
    assert calls == []
    document = _freeze()
    layout = S.layout_for(document, "floor", output_root=str(tmp_path / "out"))
    assert any(e.get("event") == "budget-refused" for e in S.read_session_ledger(layout))


def test_budget_preflight_uses_conservative_upper_bound(tmp_path):
    budget_path = tmp_path / "time_ledger.json"
    # 性能実行の下限15秒は残るが、保守上界15分には足りない通常枠残額。
    S.append_budget_entry(
        budget_path, role="floor", started_iso="2026-07-15T00:00:00+00:00",
        wall_s=35_900.0, phase="floor", note="existing non-retry work")
    calls = []
    rc = S.run_role(
        "floor", freeze_path=_write_freeze(tmp_path), budget_path=budget_path,
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        evaluate_fn=lambda *a, **k: calls.append(1), prepare_cell_fn=_prepared,
        single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None)
    assert rc == S.EXIT_BUDGET
    assert calls == []


def test_retry_limit_abandons_session_and_continues(tmp_path):
    calls = []

    def evaluate(genome, *args, **kwargs):
        calls.append(1)
        if len(calls) <= 3:
            raise RuntimeError("machine failure")
        return _green(genome)

    rc = _run(tmp_path, "block1", evaluate)
    assert rc == S.EXIT_INCOMPLETE
    assert len(calls) == 3 + 71  # 先頭を3 attempt、残り71 session は1回ずつ。
    document = _freeze()
    layout = S.layout_for(document, "block1", output_root=str(tmp_path / "out"))
    events = S.read_session_ledger(layout)
    assert any(e.get("event") == "session-result" and e.get("schedule_index") == 0
               and e.get("status") == "abandoned" for e in events)
    assert any(e.get("event") == "session-start" and e.get("schedule_index") == 1
               for e in events)


def test_prepare_transient_failure_retries_twice_then_succeeds(tmp_path):
    prepare_calls = []
    evaluate_calls = []

    @contextlib.contextmanager
    def flaky_prepare(cell, pin):
        prepare_calls.append(1)
        if len(prepare_calls) <= 2:
            raise OSError("temporary checkout failure")
        yield S.PreparedCell(
            Genome("silo", {"BACK_OFF": 1}), "stock", "/ccbench", "/cache")

    def evaluate(genome, *args, **kwargs):
        evaluate_calls.append(1)
        return _green(genome)

    rc = S.run_role(
        "develop", freeze_path=_write_freeze(tmp_path),
        budget_path=tmp_path / "time_ledger.json", output_root=str(tmp_path / "out"),
        verify_document=lambda doc: None, evaluate_fn=evaluate,
        prepare_cell_fn=flaky_prepare, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=lambda msg: None)
    assert rc == S.EXIT_OK
    assert len(prepare_calls) == 20
    assert len(evaluate_calls) == 18
    layout = S.layout_for(_freeze(), "develop", output_root=str(tmp_path / "out"))
    events = S.read_session_ledger(layout)
    assert S.validate_session_ledger(layout, S.schedule_for_role(_freeze(), "develop")) == 18
    first_starts = [e for e in events if e.get("event") == "session-start"
                    and e.get("schedule_index") == 0]
    assert [e["attempt"] for e in first_starts] == [0, 1, 2]
    assert len([e for e in events if e.get("event") == "retry"
                and e.get("retry_of") == 0]) == 2
    budget = S.read_budget(tmp_path / "time_ledger.json")
    assert len([e for e in budget["entries"]
                if e["note"].startswith("machine-failure-retry:")]) == 2


def test_prepare_freeze_contract_error_aborts_without_retry(tmp_path):
    prepare_calls = []
    evaluate_calls = []

    @contextlib.contextmanager
    def invalid_prepare(cell, pin):
        prepare_calls.append(1)
        raise S.DriverError("freeze gate_predicate が構文契約違反")
        yield  # pragma: no cover

    with pytest.raises(S.DriverError, match="構文契約違反"):
        S.run_role(
            "develop", freeze_path=_write_freeze(tmp_path),
            budget_path=tmp_path / "time_ledger.json",
            output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
            evaluate_fn=lambda *a, **k: evaluate_calls.append(1),
            prepare_cell_fn=invalid_prepare, single_tenant_fn=lambda: None,
            monotonic=_Clock(), log=lambda msg: None)
    assert prepare_calls == [1]
    assert evaluate_calls == []
    layout = S.layout_for(_freeze(), "develop", output_root=str(tmp_path / "out"))
    assert not any(e.get("event") == "retry" for e in S.read_session_ledger(layout))


def test_verifier_red_stops_without_retry(tmp_path):
    calls = []

    def red(genome, *args, **kwargs):
        calls.append(1)
        return EvalResult(genome=genome, variant=pipeline.variant_id(genome),
                          certified=False, aborted=True, verdict="non-serializable")

    rc = _run(tmp_path, "floor", red)
    assert rc == S.EXIT_VERIFIER_RED
    assert len(calls) == 1
    document = _freeze()
    layout = S.layout_for(document, "floor", output_root=str(tmp_path / "out"))
    assert not any(e.get("event") == "retry" for e in S.read_session_ledger(layout))


def test_trace_timeout_retries_but_verify_payload_does_not(tmp_path):
    timeout_calls = []

    def timeout_then_green(genome, layout, *args, **kwargs):
        timeout_calls.append(1)
        variant = pipeline.variant_id(genome)
        if len(timeout_calls) == 1:
            wal.log(layout, variant, "abort", S.ENV_TAG, {"reason": "trace-timeout"})
            return EvalResult(genome=genome, variant=variant,
                              certified=False, aborted=True)
        return _green(genome)

    assert _run(tmp_path, "develop", timeout_then_green) == S.EXIT_OK
    assert len(timeout_calls) == 19

    red_root = tmp_path / "red"
    red_root.mkdir()
    red_calls = []

    def verifier_red(genome, layout, *args, **kwargs):
        red_calls.append(1)
        variant = pipeline.variant_id(genome)
        wal.log(layout, variant, "abort", S.ENV_TAG,
                {"reason": "trace-timeout", "verify": {"verdict": "red"}})
        return EvalResult(genome=genome, variant=variant,
                          certified=False, aborted=True)

    assert _run(red_root, "develop", verifier_red) == S.EXIT_VERIFIER_RED
    assert red_calls == [1]


def test_driver_uses_workload_flags_from_freeze(tmp_path):
    document = _freeze()
    document["workload_flags"]["balanced"]["ycsb_rratio"] = "42"
    captured = []

    def evaluate(genome, layout, env, pin, perf, clocks, **kwargs):
        captured.append(dict(perf.workload))
        return _green(genome)

    rc = S.run_role(
        "develop", freeze_path=_write_freeze(tmp_path, document),
        budget_path=tmp_path / "time_ledger.json", output_root=str(tmp_path / "out"),
        verify_document=lambda doc: None, evaluate_fn=evaluate,
        prepare_cell_fn=_prepared, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=lambda msg: None)
    assert rc == S.EXIT_OK
    assert [flags["ycsb_rratio"] for flags in captured[:6]] == ["42"] * 6


def test_driver_refuses_freeze_without_workload_flags(tmp_path):
    document = _freeze()
    del document["workload_flags"]
    with pytest.raises(S.DriverError, match="workload_flags"):
        S.run_role(
            "develop", freeze_path=_write_freeze(tmp_path, document),
            budget_path=tmp_path / "time_ledger.json",
            output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
            evaluate_fn=_green, prepare_cell_fn=_prepared,
            single_tenant_fn=lambda: None, monotonic=_Clock(), log=lambda msg: None)


def test_verifier_red_in_one_campaign_blocks_other_campaign(tmp_path):
    calls = []

    def red(genome, *args, **kwargs):
        calls.append("red")
        return EvalResult(genome=genome, variant=pipeline.variant_id(genome),
                          certified=False, aborted=True, verdict="non-serializable")

    freeze_path = _write_freeze(tmp_path)
    common = dict(
        freeze_path=freeze_path, budget_path=tmp_path / "time_ledger.json",
        output_root=str(tmp_path / "out"), verify_document=lambda doc: None,
        prepare_cell_fn=_prepared, single_tenant_fn=lambda: None,
        monotonic=_Clock(), log=lambda msg: None)
    assert S.run_role("floor", evaluate_fn=red, **common) == S.EXIT_VERIFIER_RED
    assert S.run_role(
        "block1", evaluate_fn=lambda *a, **k: calls.append("unexpected"),
        **common) == S.EXIT_VERIFIER_RED
    assert calls == ["red"]


def test_develop_calls_legacy_plus_s2_without_bench_18_times(tmp_path):
    calls = []

    def evaluate(genome, *args, **kwargs):
        calls.append(kwargs)
        return _green(genome)

    rc = _run(tmp_path, "develop", evaluate)
    assert rc == S.EXIT_OK
    assert len(calls) == 18
    for kwargs in calls:
        assert kwargs["do_bench"] is False
        assert kwargs["screening"] is None
        assert kwargs["numactl"] == S.NUMACTL
        assert kwargs["bench_max_rounds"] == 1
        assert [(tag, wl.flags) for tag, wl in kwargs["extra_correctness"]] == [
            (pipeline.S2_TAG, pipeline.s2_correctness_workload().flags)]


def test_s1_session_unknown_stage_is_safe_for_existing_wal_consumers(tmp_path):
    layout = CampaignLayout(str(tmp_path / "campaign")).ensure()
    wal.log(layout, "v1", S.SESSION_STAGE, S.ENV_TAG, {"event": "session-start"})
    states = wal.replay(layout)
    assert states["v1"].stages_seen == [S.SESSION_STAGE]
    assert not states["v1"].terminal
    assert wal.records_by_stage(layout, "v1")[S.SESSION_STAGE] == {
        "event": "session-start"}


def test_completed_campaign_resume_does_not_evaluate_again(tmp_path):
    assert _run(tmp_path, "develop", _green) == S.EXIT_OK
    calls = []
    assert _run(tmp_path, "develop", lambda *a, **k: calls.append(1)) == S.EXIT_OK
    assert calls == []


def test_pipeline_bench_rounds_default_three_and_opt_in_one(tmp_path, monkeypatch):
    """未指定は従来3、S-1 opt-inだけ1を remeasure_until_stable へ渡す。"""
    captured = []

    @contextlib.contextmanager
    def unlocked():
        yield

    def fake_build(genome, commit, trace, **kwargs):
        return types.SimpleNamespace(
            bin_hash="t" if trace else "p", binary="/fake/ycsb", cached=True,
            configure_cmd="cfg", build_cmd="build")

    def fake_remeasure(measure_fn, settle_fn=None, max_rounds=3):
        captured.append(max_rounds)
        point = measure_fn()
        floor = types.SimpleNamespace(median=100.0, cv=0.01, high_variance=False)
        return types.SimpleNamespace(point=point, nf=floor, rounds=1,
                                     unstable=False, cv_history=[0.01])

    monkeypatch.setattr(pipeline, "buildcache", types.SimpleNamespace(build=fake_build))
    monkeypatch.setattr(pipeline.source_digest, "resolve", lambda *a, **k: "stock")
    monkeypatch.setattr(pipeline, "_run_trace", lambda *a, **k: (10, 0, 1))
    monkeypatch.setattr(pipeline, "verify_trace_dir", lambda path: types.SimpleNamespace(
        verdict="serializable", certified=True, anomalies=[]))
    monkeypatch.setattr(pipeline, "bench_lock", unlocked)
    monkeypatch.setattr(pipeline, "competing_bench_pids", lambda: [])
    monkeypatch.setattr(pipeline, "settle", lambda: {"settled": True})
    monkeypatch.setattr(pipeline, "measure_point", lambda *a, **k: types.SimpleNamespace(
        throughputs=[100.0] * 5, run_cmd="run", notes=[],
        leading_indicators=lambda: {}))
    monkeypatch.setattr(pipeline, "remeasure_until_stable", fake_remeasure)
    genome = Genome("silo", {"BACK_OFF": 1})
    perf = PerfConfig(records=1000, threads=2)

    for max_rounds in (None, 1):
        layout = CampaignLayout(str(tmp_path / f"c-{max_rounds}")).ensure()
        kwargs = {} if max_rounds is None else {"bench_max_rounds": max_rounds}
        result = pipeline.evaluate(
            genome, layout, "test-env", "deadbeef", perf, 1800,
            log=lambda msg: None, **kwargs)
        assert result.certified
    assert captured == [3, 1]
