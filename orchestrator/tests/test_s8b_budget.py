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
    s8b_budget.create_ledger(
        path, manifest_sha256=MANIFEST_SHA, limits=limits or _limits(),
    )
    return path


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
        s8b_budget.create_ledger(path, manifest_sha256=MANIFEST_SHA, limits=_limits())


def test_schema_mismatch_is_rejected(tmp_path):
    path = _create(tmp_path)
    _rewrite(path, lambda document: document.update({"extra": True}))
    with pytest.raises(s8b_budget.BudgetError, match="schema"):
        s8b_budget.read_ledger(path, manifest_sha256=MANIFEST_SHA)


def test_manifest_hash_mismatch_is_rejected(tmp_path):
    path = _create(tmp_path)
    with pytest.raises(s8b_budget.BudgetError, match="manifest_sha256"):
        s8b_budget.read_ledger(path, manifest_sha256="b" * 64)


def test_spent_reaggregation_mismatch_is_rejected(tmp_path):
    path = _create(tmp_path)
    _rewrite(path, lambda document: document["spent"].update({"bench_s": 1.0}))
    with pytest.raises(s8b_budget.BudgetError, match="再集計"):
        s8b_budget.read_ledger(path, manifest_sha256=MANIFEST_SHA)


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


def test_append_entry_accumulates_once_and_atomic_result_rereads(tmp_path):
    path = _create(tmp_path)
    first = s8b_budget.append_entry(
        path, manifest_sha256=MANIFEST_SHA,
        entry=_entry(index=0, bench_s=1.5, wall_s=3.0),
    )
    assert first["spent"] == {
        "bench_s": 1.5, "wall_s": 3.0, "by_holdout": {"h-first": 1.5},
    }
    second = s8b_budget.append_entry(
        path, manifest_sha256=MANIFEST_SHA,
        entry=_entry(index=1, holdout_id="h-second", bench_s=2.0, wall_s=4.0),
    )
    assert second["spent"] == {
        "bench_s": 3.5, "wall_s": 7.0,
        "by_holdout": {"h-first": 1.5, "h-second": 2.0},
    }
    assert s8b_budget.read_ledger(path, manifest_sha256=MANIFEST_SHA) == second
    assert not path.with_name(path.name + ".lock").exists()
