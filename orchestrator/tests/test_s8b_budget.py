# -*- coding: utf-8 -*-
"""8b oracle 専用 budget 台帳の fail-closed 境界を検査する。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
_ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from campaign import s8b_budget  # noqa: E402


FREEZE_PATH = _ROOT / "output/s8b-freeze/holdout_freeze.json"
MANIFEST_SHA = "a" * 64
FREEZE_SHA = "c" * 64
SCHEDULE_SHA = "d" * 64
IDENTITY = {
    "manifest_sha256": MANIFEST_SHA,
    "freeze_sha256": FREEZE_SHA,
    "schedule_sha256": SCHEDULE_SHA,
}


def _limits(total=100.0, first=60.0, second=60.0):
    return {
        "total_bench_s": total,
        "per_holdout_bench_s": {"h-first": first, "h-second": second},
        "oracle_shared": True,
    }


def _entry(*, index=0, holdout_id="h-first", bench_s=1.5, wall_s=3.0):
    return {
        "campaign_id": "campaign-a", "block_id": "block-a",
        "schedule_index": index, "holdout_id": holdout_id,
        "configuration_id": "configuration-a", "attempt": 0,
        "outcome": "success", "bench_s": bench_s, "wall_s": wall_s,
        "started_iso": "2026-01-01T00:00:00+00:00",
        "finished_iso": "2026-01-01T00:00:03+00:00",
    }


def _create(tmp_path, *, limits=None):
    path = tmp_path / "time_ledger.json"
    s8b_budget.create_ledger(path, limits=limits or _limits(), **IDENTITY)
    return path


def _reserve(path, *, reserved=6.0, by_holdout=None, reserved_iso="2026-01-01T00:00:00+00:00"):
    return s8b_budget.reserve(
        path, reserved_bench_s=reserved,
        by_holdout_reserved=by_holdout or {"h-first": 3.0, "h-second": 3.0},
        reserved_iso=reserved_iso, **IDENTITY,
    )


def _rewrite(path, mutate):
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document), encoding="utf-8")


def test_current_freeze_null_budget_is_positive_control_rejection():
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    with pytest.raises(s8b_budget.BudgetError, match="null"):
        s8b_budget.load_oracle_limits(freeze)


def test_create_is_create_only(tmp_path):
    path = _create(tmp_path)
    with pytest.raises(s8b_budget.BudgetError, match="既に存在"):
        s8b_budget.create_ledger(path, limits=_limits(), **IDENTITY)


def test_schema_mismatch_is_rejected(tmp_path):
    path = _create(tmp_path)
    _rewrite(path, lambda document: document.update({"extra": True}))
    with pytest.raises(s8b_budget.BudgetError, match="schema"):
        s8b_budget.read_ledger(path, **IDENTITY)


def test_manifest_hash_mismatch_is_rejected(tmp_path):
    path = _create(tmp_path)
    with pytest.raises(s8b_budget.BudgetError, match="manifest_sha256"):
        s8b_budget.read_ledger(
            path, manifest_sha256="b" * 64,
            freeze_sha256=FREEZE_SHA, schedule_sha256=SCHEDULE_SHA,
        )


def test_freeze_hash_mismatch_is_rejected(tmp_path):
    path = _create(tmp_path)
    with pytest.raises(s8b_budget.BudgetError, match="freeze_sha256"):
        s8b_budget.read_ledger(
            path, manifest_sha256=MANIFEST_SHA,
            freeze_sha256="e" * 64, schedule_sha256=SCHEDULE_SHA,
        )


def test_schedule_hash_mismatch_is_rejected(tmp_path):
    path = _create(tmp_path)
    with pytest.raises(s8b_budget.BudgetError, match="schedule_sha256"):
        s8b_budget.read_ledger(
            path, manifest_sha256=MANIFEST_SHA,
            freeze_sha256=FREEZE_SHA, schedule_sha256="e" * 64,
        )


def test_spent_reaggregation_mismatch_is_rejected(tmp_path):
    path = _create(tmp_path)
    _rewrite(path, lambda document: document["spent"].update({"bench_s": 1.0}))
    with pytest.raises(s8b_budget.BudgetError, match="再集計"):
        s8b_budget.read_ledger(path, **IDENTITY)


def test_assert_available_detects_total_limit():
    ledger = {
        "limits": _limits(total=10.0, first=20.0),
        "spent": {"bench_s": 9.0, "wall_s": 9.0,
                  "by_holdout": {"h-first": 9.0}},
    }
    with pytest.raises(s8b_budget.BudgetError, match="総 bench 枠不足"):
        s8b_budget.assert_available(
            ledger, holdout_id="h-first", required_bench_s=2.0,
        )


def test_assert_available_detects_holdout_limit():
    ledger = {
        "limits": _limits(total=100.0, first=10.0),
        "spent": {"bench_s": 9.0, "wall_s": 9.0,
                  "by_holdout": {"h-first": 9.0}},
    }
    with pytest.raises(s8b_budget.BudgetError, match="holdout bench 枠不足"):
        s8b_budget.assert_available(
            ledger, holdout_id="h-first", required_bench_s=2.0,
        )


def test_append_entry_requires_held_reservation(tmp_path):
    path = _create(tmp_path)
    with pytest.raises(s8b_budget.BudgetError, match="held reservation なし"):
        s8b_budget.append_entry(path, entry=_entry(index=0), **IDENTITY)


def test_reserve_holds_full_envelope_and_charges_reserved(tmp_path):
    path = _create(tmp_path)
    held = _reserve(path, reserved=6.0)
    reservation = held["reservation"]
    assert reservation["status"] == "held"
    assert reservation["reserved_bench_s"] == 6.0
    # crash 非解放: held の間は全予約枠が計上される (charged==reserved)。
    assert reservation["charged_bench_s"] == 6.0
    assert reservation["actual_bench_s"] == 0.0
    assert not path.with_name(path.name + ".lock").exists()


def test_reserve_rejects_double_reservation(tmp_path):
    path = _create(tmp_path)
    _reserve(path)
    with pytest.raises(s8b_budget.BudgetError, match="再予約"):
        _reserve(path)


def test_reserve_insufficient_total_is_rejected(tmp_path):
    path = _create(tmp_path, limits=_limits(total=5.0, first=60.0, second=60.0))
    with pytest.raises(s8b_budget.BudgetError, match="総 bench 枠を一括予約できない"):
        _reserve(path, reserved=6.0)


def test_reserve_insufficient_holdout_is_rejected(tmp_path):
    path = _create(tmp_path, limits=_limits(total=100.0, first=2.0, second=60.0))
    with pytest.raises(s8b_budget.BudgetError, match="holdout bench 枠を一括予約できない"):
        _reserve(path, reserved=6.0, by_holdout={"h-first": 3.0, "h-second": 3.0})


def test_reserve_rejects_by_holdout_sum_mismatch(tmp_path):
    """所見5: by_holdout_reserved の合計が reserved_bench_s と食い違う入力を拒否する。

    driver は無矛盾に構築するため現経路では発火しないが、将来の別呼出者が
    不整合な reservation を作れてしまう API 表面を reserve の入口で塞ぐ。
    """
    path = _create(tmp_path)
    with pytest.raises(s8b_budget.BudgetError, match="合計"):
        _reserve(path, reserved=6.0, by_holdout={"h-first": 3.0, "h-second": 2.0})
    # 拒否された reservation は台帳に書き込まれない (create 直後のまま)。
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["reservation"] is None


def test_append_accumulates_within_envelope_and_settle_releases(tmp_path):
    path = _create(tmp_path)
    _reserve(path, reserved=6.0)
    first = s8b_budget.append_entry(
        path, entry=_entry(index=0, bench_s=1.5, wall_s=3.0), **IDENTITY,
    )
    assert first["spent"] == {
        "bench_s": 1.5, "wall_s": 3.0, "by_holdout": {"h-first": 1.5},
    }
    assert first["reservation"]["actual_bench_s"] == 1.5
    # held の間は charged は予約枠のまま (非解放)。
    assert first["reservation"]["charged_bench_s"] == 6.0
    second = s8b_budget.append_entry(
        path, entry=_entry(index=1, holdout_id="h-second", bench_s=2.0, wall_s=4.0),
        **IDENTITY,
    )
    assert second["spent"] == {
        "bench_s": 3.5, "wall_s": 7.0,
        "by_holdout": {"h-first": 1.5, "h-second": 2.0},
    }
    settled = s8b_budget.settle(
        path, settled_iso="2026-01-01T00:00:10+00:00", **IDENTITY,
    )
    # 精算後は charged==actual (未使用枠を解放)。reserved/actual を分離して残す。
    assert settled["reservation"]["status"] == "settled"
    assert settled["reservation"]["reserved_bench_s"] == 6.0
    assert settled["reservation"]["charged_bench_s"] == 3.5
    assert settled["reservation"]["actual_bench_s"] == 3.5
    assert s8b_budget.read_ledger(path, **IDENTITY) == settled
    assert not path.with_name(path.name + ".lock").exists()


def test_append_over_envelope_is_rejected(tmp_path):
    path = _create(tmp_path, limits=_limits(total=100.0, first=60.0, second=60.0))
    _reserve(path, reserved=6.0, by_holdout={"h-first": 3.0, "h-second": 3.0})
    with pytest.raises(s8b_budget.BudgetError, match="予約枠を超過"):
        s8b_budget.append_entry(
            path, entry=_entry(index=0, holdout_id="h-first", bench_s=5.0), **IDENTITY,
        )


def test_mark_exhausted_records_terminal_and_runs_nothing(tmp_path):
    path = _create(tmp_path, limits=_limits(total=5.0))
    document = s8b_budget.mark_exhausted(
        path, requested_bench_s=12.0,
        by_holdout_requested={"h-first": 6.0, "h-second": 6.0},
        reserved_iso="2026-01-01T00:00:00+00:00", **IDENTITY,
    )
    reservation = document["reservation"]
    assert reservation["status"] == "exhausted"
    assert reservation["reserved_bench_s"] == 12.0
    assert reservation["charged_bench_s"] == 0.0
    assert document["entries"] == []
    # exhausted 後は held reservation がないため entry を追記できない。
    with pytest.raises(s8b_budget.BudgetError, match="held reservation なし"):
        s8b_budget.append_entry(path, entry=_entry(index=0), **IDENTITY)
