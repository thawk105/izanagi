# -*- coding: utf-8 -*-
"""S-1 measurement freeze v2 の統合テストと改竄 positive control。"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import s1_known_axes_freeze as K  # noqa: E402
from campaign import s1_measurement_freeze as M  # noqa: E402


@pytest.fixture
def freeze_env(tmp_path, monkeypatch):
    """実 freeze の安全性契約だけを保った最小の同型 fixture を作る。

    known-axes の本番材料や s1_stats.py 本体をテストに焼き込むと、
    並行タスクの正当な変更で B1 のテストまで腐るため tmp に隔離する。
    """
    material_source = tmp_path / "known-material.txt"
    material_source.write_text("fixture material\n", encoding="utf-8")
    source_rel = "fixture/known-material.txt"
    source = {
        "path": source_rel,
        "sha256": K._sha256(material_source),
        "key": "minimal fixture source",
    }

    entries = {}
    for workload in M.WORKLOADS:
        common_flags = {
            "BACK_OFF": 1,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0,
            "BACKOFF_TRIGGER_GATING": 1,
        }
        entries[workload] = {
            "system_gate": {
                "name": {"balanced": "g_rl", "write-heavy": "g_rt",
                         "read-heavy": "g_rl"}[workload],
                "flags": copy.deepcopy(common_flags),
                "gate_predicate": f"gate predicate for {workload}",
                "sources": [copy.deepcopy(source)],
            },
            "ident_all": {
                "name": "ident_all",
                "flags": copy.deepcopy(common_flags),
                "gate_predicate": "ident_all predicate",
                "sources": [copy.deepcopy(source)],
            },
            "p2_2_flag_opt": {
                "variant": f"fixture-p2-{workload}",
                "flags": {"BACK_OFF": 0},
                "sources": [copy.deepcopy(source)],
            },
            "backoff_fixed_best": {
                "backoff_us": 5,
                "flags": {"BACK_OFF": 1, "BACKOFF_FIXED": 5},
                "sources": [copy.deepcopy(source)],
            },
            "sort_best": {
                "name": "fixture_sort",
                "flags": {"SORT_VARIANT": 1},
                "comparator": "a < b",
                "sources": [copy.deepcopy(source)],
            },
            "stock_common": {
                "flags": {"BACK_OFF": 1},
                "sources": [copy.deepcopy(source)],
            },
        }

    pairings = [
        {
            "workload": workload,
            "gate_on": entries[workload]["system_gate"]["name"],
            "gate_off": "ident_all",
            "flags_identical": True,
        }
        for workload in M.WORKLOADS
    ]
    known_doc = {
        "what": "minimal known-axes fixture",
        "frozen_at_head": K._run_git(["rev-parse", "HEAD"]),
        "ccbench_pin": K._run_git(
            ["rev-parse", "HEAD"], K.ROOT / "external/ccbench"),
        "generator": {
            "path": K.SCRIPT_REL,
            "sha256": K._sha256(K.ROOT / K.SCRIPT_REL),
        },
        "python_version": sys.version,
        "selection_rules": {
            "p2_2": "fixture", "backoff_fixed": "fixture", "sort": "fixture",
            "system_gate": "fixture", "stock_common": "fixture",
        },
        "entries": entries,
        "s1b_pairing": pairings,
        "reference_values_note": "fixture",
    }
    known_path = tmp_path / "known_axes_freeze.json"
    known_path.write_text(
        json.dumps(known_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # known_axes.verify_document の最終機械再構成も通した上で、
    # 本番の長大な WAL 選定を fixture に混ぜない。
    monkeypatch.setattr(
        K, "build_document", lambda **_kwargs: copy.deepcopy(known_doc))

    stats_path = tmp_path / "s1_stats.py"
    stats_path.write_text("# dummy stats implementation\n", encoding="utf-8")

    def known_resolver(path_rel: str) -> Path:
        if path_rel == source_rel:
            return material_source
        return K.ROOT / path_rel

    def resolver(path_rel: str) -> Path:
        return {
            M.KNOWN_AXES_REL: known_path,
            M.STATS_REL: stats_path,
            M.SCRIPT_REL: M.SCRIPT_PATH,
        }.get(path_rel, M.ROOT / path_rel)

    return {
        "known_path": known_path,
        "stats_path": stats_path,
        "known_resolver": known_resolver,
        "resolver": resolver,
    }


def _build(env) -> dict:
    return M.build_document(
        known_axes_path=env["known_path"],
        stats_path=env["stats_path"],
        known_source_resolver=env["known_resolver"],
    )


def _generate(path: Path, env) -> dict:
    return M.generate(
        path,
        known_axes_path=env["known_path"],
        stats_path=env["stats_path"],
        known_source_resolver=env["known_resolver"],
    )


def _verify(path: Path, env) -> dict:
    return M.verify(
        path,
        source_resolver=env["resolver"],
        known_source_resolver=env["known_resolver"],
    )


def test_generate_builds_registered_cells_comparisons_and_schedule(freeze_env):
    doc = _build(freeze_env)
    assert len(doc["cells"]) == 18
    assert len(doc["comparisons"]) == 12
    assert sum(c["family"] == "S-1a" for c in doc["comparisons"]) == 9
    assert sum(c["family"] == "S-1b" for c in doc["comparisons"]) == 3
    assert {c["alternative"] for c in doc["comparisons"]} == {"greater"}
    assert sum(len(order) for rounds in doc["schedule"].values()
               for order in rounds) == 288
    assert doc["operating_point"] == {
        "RECORDS": 1_000_000, "THREADS": 48, "EXTIME": 3, "REPS": 5,
    }


def test_generate_refuses_existing_freeze(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    with pytest.raises(M.FreezeError, match="既に存在"):
        _generate(path, freeze_env)


def test_verify_rejects_one_byte_freeze_tamper(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    original = path.read_bytes()
    tampered = original.replace(b'"what": "S-1', b'"what": "X-1', 1)
    assert tampered != original
    assert len(tampered) == len(original)
    path.write_bytes(tampered)
    with pytest.raises(M.FreezeError):
        _verify(path, freeze_env)


def test_verify_rejects_stats_implementation_tamper(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    freeze_env["stats_path"].write_text(
        "# dummy stats implementation changed\n", encoding="utf-8")
    with pytest.raises(M.FreezeError, match="implementation_hashes.s1_stats"):
        _verify(path, freeze_env)


def test_verify_rejects_known_axes_material_tamper(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    freeze_env["known_path"].write_bytes(
        freeze_env["known_path"].read_bytes() + b" ")
    with pytest.raises(M.FreezeError, match="implementation_hashes.known_axes_freeze"):
        _verify(path, freeze_env)


def test_schedule_is_balanced_and_reproducible(freeze_env):
    first = _build(freeze_env)
    second = _build(freeze_env)
    expected_cells = set(first["cells"])
    total = 0
    for campaign, rounds in first["schedule"].items():
        assert len(rounds) == M.CAMPAIGN_ROUNDS[campaign]
        for order in rounds:
            assert len(order) == 18
            assert len(set(order)) == 18
            assert set(order) == expected_cells
            total += len(order)
    assert total == 288
    assert first["schedule"] == second["schedule"]
    assert first["schedule_hash"] == second["schedule_hash"]


def test_s1b_pairing_rejects_mismatched_flags(freeze_env):
    doc = _build(freeze_env)
    forged = copy.deepcopy(doc)
    forged["cells"]["balanced:ident_all"]["variant"]["flags"]["BACK_OFF"] = 0
    with pytest.raises(M.FreezeError, match="flags 不一致"):
        M.verify_document(
            forged,
            source_resolver=freeze_env["resolver"],
            known_source_resolver=freeze_env["known_resolver"],
        )
