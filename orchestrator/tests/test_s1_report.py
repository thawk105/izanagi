# -*- coding: utf-8 -*-
"""S-1 report hard gate の自己完結 positive/negative control。"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

ORCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCH.parent))

from orchestrator.campaign import model, pipeline, s1_direct_comparison as driver, wal  # noqa: E402
from orchestrator.campaign import s1_report as report  # noqa: E402
from orchestrator.campaign import t080_freeze_migration as T080  # noqa: E402


WORKLOADS = ("balanced", "write-heavy", "read-heavy")
CONFIGS = ("system_gate", "ident_all", "p2_2_flag_opt",
           "backoff_fixed_best", "sort_best", "stock_common")


def _freeze() -> dict:
    cells = {}
    for workload in WORKLOADS:
        for config in CONFIGS:
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
        "cells": cells,
        "schedule": {
            "floor": [order[:] for _ in range(8)],
            "test_block_1": [order[:] for _ in range(4)],
            "test_block_2": [order[:] for _ in range(4)],
        },
        "comparisons": [
            {
                "comparison_id": "S-1a:balanced:p2_2_flag_opt",
                "family": "S-1a", "workload": "balanced",
                "left_cell": "balanced:system_gate",
                "right_cell": "balanced:p2_2_flag_opt",
                "alternative": "greater", "note": "fixture",
            },
            {
                "comparison_id": "S-1b:balanced:gate_on_vs_gate_off",
                "family": "S-1b", "workload": "balanced",
                "left_cell": "balanced:system_gate",
                "right_cell": "balanced:ident_all",
                "alternative": "greater", "note": "fixture",
            },
        ],
    }


def _fitness(role: str, cell_id: str, lap: int, *, small_effect: bool) -> float:
    config = cell_id.split(":", 1)[1]
    if config == "system_gate":
        base = 102.0 if small_effect else 120.0
    elif config in {"p2_2_flag_opt", "ident_all"}:
        base = 100.0
    else:
        base = 90.0
    # floor/test とも穏当な微小変動を持たせるが、完全分離は壊さない。
    return base + (lap - 1) * 0.05


def _write_session(layout, item, role: str, *, fitness: float,
                   verify_configs: list[str], commit: bool = True,
                   status: str = "success", mutate_order: bool = False) -> None:
    variant = f"variant-{item.freeze_cell_id}"
    cell_display = item.cell_id
    if mutate_order:
        cell_display = "tampered/order"
    common = {
        "schedule_index": item.schedule_index, "campaign_role": role,
        "lap": item.lap, "cell_id": cell_display, "variant": variant,
        "ts": "2026-07-15T00:00:00+00:00", "attempt": 0,
    }
    wal.log(layout, variant, driver.SESSION_STAGE, driver.ENV_TAG,
            {"event": "session-start", **common})
    wal.log(layout, variant, "build_start", driver.ENV_TAG,
            {"genome": "silo|BACK_OFF=1", "src_token": f"src-{item.freeze_cell_id}"})
    if commit:
        payload = {
            "fitness_tps": None if role == "develop" else fitness,
            "verify_configs": verify_configs,
        }
        if role != "develop":
            payload.update({"cv": 0.01, "high_variance": False, "unstable": False})
        wal.log(layout, variant, "commit", driver.ENV_TAG, payload)
    else:
        wal.log(layout, variant, "bench_done", driver.ENV_TAG,
                {"fitness_tps": fitness})
    if status != "success":
        wal.log(layout, variant, "abort", driver.ENV_TAG, {"reason": "fixture-failure"})
    wal.log(layout, variant, driver.SESSION_STAGE, driver.ENV_TAG,
            {"event": "session-result", **common, "status": status,
             "reason": "fixture"})


def _fixture(
        tmp_path: Path, *, missing_develop_s2: bool = False,
        missing_commit: bool = False, mutate_schedule: bool = False,
        floor_missing: bool = False, small_effect: bool = False,
        stop_block2: bool = False, over_budget: bool = False,
) -> tuple[dict, Path, Path]:
    document = _freeze()
    freeze_path = tmp_path / "measurement_freeze.json"
    freeze_path.write_text(json.dumps(document), encoding="utf-8")
    output_root = tmp_path / "output"
    target = "balanced:system_gate"

    for role in report.ROLES:
        layout = driver.layout_for(document, role, output_root=str(output_root)).ensure()
        schedule = driver.schedule_for_role(document, role)
        wal.log(layout, "s1-campaign", driver.SESSION_STAGE, driver.ENV_TAG, {
            "event": "campaign-start", "campaign_role": role,
            "ts": "2026-07-15T00:00:00+00:00",
        })
        for item in schedule:
            if stop_block2 and role == "block2" and item.schedule_index >= 1:
                break
            develop_verify = [pipeline.LEGACY_TAG, pipeline.S2_TAG]
            if missing_develop_s2 and role == "develop" and item.freeze_cell_id == target:
                develop_verify = [pipeline.LEGACY_TAG]
            omit_commit = (missing_commit and role == "floor"
                           and item.freeze_cell_id == target and item.lap == 1)
            abandoned = (floor_missing and role == "floor"
                         and item.freeze_cell_id == target and item.lap == 8)
            tampered = mutate_schedule and role == "block1" and item.schedule_index == 1
            _write_session(
                layout, item, role,
                fitness=_fitness(role, item.freeze_cell_id, item.lap,
                                 small_effect=small_effect),
                verify_configs=(develop_verify if role == "develop"
                                else [pipeline.LEGACY_TAG]),
                commit=not omit_commit and not abandoned,
                status="abandoned" if abandoned else "success",
                mutate_order=tampered,
            )
        if stop_block2 and role == "block2":
            item = schedule[1]
            wal.log(layout, "not-started", driver.SESSION_STAGE, driver.ENV_TAG, {
                "event": "budget-refused", "schedule_index": item.schedule_index,
                "campaign_role": role, "lap": item.lap, "cell_id": item.cell_id,
                "variant": "not-started", "ts": "2026-07-15T00:00:00+00:00",
                "reason": "fixture budget refusal",
            })

    budget_path = tmp_path / "time_ledger.json"
    spent = 43_201.0 if over_budget else 0.0
    entries = []
    if over_budget:
        entries.append({
            "campaign_role": "block2", "started_iso": "2026-07-15T00:00:00+00:00",
            "wall_s": spent, "phase": "block2", "note": "fixture overspend",
        })
    budget_path.write_text(json.dumps({
        "total_budget_s": 43_200, "spent_s": spent, "entries": entries,
    }), encoding="utf-8")
    return document, freeze_path, budget_path


def _generate(tmp_path: Path, document: dict, freeze_path: Path,
              budget_path: Path) -> dict:
    result, json_path, md_path = report.generate_report(
        freeze_path=freeze_path, budget_path=budget_path,
        output_root=str(tmp_path / "output"),
        freeze_verify=lambda path: document,
        generated_at_head="a" * 40,
    )
    assert json.loads(json_path.read_text(encoding="utf-8")) == result
    assert "独立な検証相を持たない" in md_path.read_text(encoding="utf-8")
    return result


def _comparison(result: dict, comparison_id: str =
                "S-1a:balanced:p2_2_flag_opt") -> dict:
    return next(item for item in result["comparisons"]
                if item["comparison_id"] == comparison_id)


def test_floor_cmp_is_preregistered_pure_function():
    assert report.floor_cmp(0.01, 0.02) == 0.03
    assert report.floor_cmp(0.04, 0.02) == 0.04
    with pytest.raises(ValueError):
        report.floor_cmp(float("nan"), 0.01)


def test_session_event_uses_shared_model_authority(monkeypatch):
    monkeypatch.setattr(model, "STAGE_S1_SESSION", "shared-session-fixture")
    canonical = model.WalRecord(
        "v", "shared-session-fixture", "test", 1,
        {"event": "session-start"},
    )
    reliteralized = model.WalRecord(
        "v", "s1-session", "test", 1, {"event": "session-start"},
    )

    assert report._event(canonical, "session-start")
    assert not report._event(reliteralized, "session-start")


def test_left_system_greater_is_bound_to_target_left():
    comparison = _freeze()["comparisons"][0]
    observations = {
        "block1": {"balanced:system_gate": [10, 11, 12, 13],
                   "balanced:p2_2_flag_opt": [1, 2, 3, 4]},
        "block2": {"balanced:system_gate": [20, 21, 22, 23],
                   "balanced:p2_2_flag_opt": [5, 6, 7, 8]},
    }
    target, control, alternative = report.bind_left_target(comparison, observations)
    assert target == ((10, 11, 12, 13), (20, 21, 22, 23))
    assert control == ((1, 2, 3, 4), (5, 6, 7, 8))
    assert alternative == "greater"
    assert report.s1_stats.stratified_test(target, control, alternative).p_perm == 1 / 4900


def test_missing_develop_s2_certification_is_structured_indeterminate(tmp_path):
    args = _fixture(tmp_path, missing_develop_s2=True)
    result = _generate(tmp_path, *args)
    comparison = _comparison(result)
    assert comparison["judgment"] == report.INDETERMINATE
    assert any(reason["code"] == "develop_certified_missing"
               for reason in comparison["reasons"])
    assert result["hard_gates"]["certified"]["status"] == "fail"
    # 判定には使わないが、信頼できる性能 WAL の記述統計は黙って落とさない。
    assert comparison["comparison_id"] in result["effect_sizes"]
    assert comparison["p_star"] is None


def test_bench_value_without_commit_is_rejected_as_sample(tmp_path):
    args = _fixture(tmp_path, missing_commit=True)
    result = _generate(tmp_path, *args)
    comparison = _comparison(result)
    assert comparison["judgment"] == report.INDETERMINATE
    assert any(reason["code"] == "certified_commit_missing"
               for reason in comparison["reasons"])
    assert result["hard_gates"]["certified"]["rejected_or_unbound_commits"]["floor"] == 0


def test_schedule_order_mutation_invalidates_campaign_comparisons(tmp_path):
    args = _fixture(tmp_path, mutate_schedule=True)
    result = _generate(tmp_path, *args)
    assert result["hard_gates"]["schedule"]["block1"]["status"] == "fail"
    assert all(item["judgment"] == report.INDETERMINATE
               for item in result["comparisons"])
    assert any(reason["code"] == "schedule_ledger_invalid"
               for reason in _comparison(result)["reasons"])


def test_unframed_wal_tail_fails_but_keeps_completed_prefix_evidence(tmp_path):
    document, freeze_path, budget_path = _fixture(tmp_path)
    layout = driver.layout_for(
        document, "block1", output_root=str(tmp_path / "output"),
    )
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"variant":"unframed"')

    result = _generate(tmp_path, document, freeze_path, budget_path)

    gate = result["hard_gates"]["schedule"]["block1"]
    expected = len(driver.schedule_for_role(document, "block1"))
    assert gate["status"] == "fail"
    assert [reason["code"] for reason in gate["reasons"]] == [
        "wal_truncated_tail",
    ]
    assert gate["expected_sessions"] == expected
    assert gate["recorded_attempt_starts"] == expected
    assert gate["recorded_initial_starts"] == expected
    assert gate["next_index"] == expected
    assert result["hard_gates"]["certified"]["accepted_samples"]["block1"] == expected
    assert result["hard_gates"]["certified"]["rejected_or_unbound_commits"]["block1"] == 0
    assert all(item["judgment"] == report.INDETERMINATE
               for item in result["comparisons"])


def test_line_issue_and_unframed_tail_are_both_reported_with_prefix_kept(tmp_path):
    document, freeze_path, budget_path = _fixture(tmp_path)
    layout = driver.layout_for(
        document, "block1", output_root=str(tmp_path / "output"),
    )
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"variant":}\n{"variant":"unframed"')

    result = _generate(tmp_path, document, freeze_path, budget_path)

    gate = result["hard_gates"]["schedule"]["block1"]
    expected = len(driver.schedule_for_role(document, "block1"))
    assert gate["status"] == "fail"
    assert [reason["code"] for reason in gate["reasons"]] == [
        "wal_truncated_tail", "wal_line_issues",
    ]
    line_reason = gate["reasons"][1]
    assert line_reason["count"] == 1
    assert len(line_reason["first_issues"]) == 1
    assert line_reason["first_issues"][0]["reason"].startswith("JSONDecodeError: ")
    assert gate["expected_sessions"] == expected
    assert gate["recorded_attempt_starts"] == expected
    assert gate["next_index"] == expected
    assert result["hard_gates"]["certified"]["accepted_samples"]["block1"] == expected


def test_floor_cell_with_seven_sessions_makes_comparison_indeterminate(tmp_path):
    args = _fixture(tmp_path, floor_missing=True)
    result = _generate(tmp_path, *args)
    comparison = _comparison(result)
    assert comparison["judgment"] == report.INDETERMINATE
    assert any(reason["code"] == "sample_n_mismatch"
               and reason["campaign"] == "floor" and reason["actual_n"] == 7
               for reason in comparison["reasons"])


def test_complete_separation_passes_gates_with_one_over_4900(tmp_path):
    args = _fixture(tmp_path)
    result = _generate(tmp_path, *args)
    comparison = _comparison(result)
    assert comparison["gates"]["gate1"]["passed"] is True
    assert comparison["gates"]["gate2"]["passed"] is True
    assert comparison["p_perm"] == 1 / 4900
    assert comparison["p_star"] == 1 / 4900
    assert comparison["judgment"] == report.ESTABLISHED
    assert result["families"]["s1a"]["judgment"] == report.ESTABLISHED
    assert set(result) == {
        "freeze_ref", "hard_gates", "comparisons", "families", "effect_sizes",
        "budget", "generated_at_head",
    }
    effects = result["effect_sizes"][comparison["comparison_id"]]
    assert effects["median_difference"] > 0
    assert effects["probability_superiority_stratified"] == 1.0
    assert comparison["block_effects"] is not None
    assert comparison["unstable_counts"]["floor"] == {"left": 0, "right": 0}


def test_gate1_failure_sets_p_star_one_and_not_established(tmp_path):
    args = _fixture(tmp_path, small_effect=True)
    result = _generate(tmp_path, *args)
    comparison = _comparison(result)
    assert comparison["gates"]["gate1"]["passed"] is False
    assert comparison["p_star"] == 1.0
    assert comparison["judgment"] == report.NOT_ESTABLISHED


def test_over_budget_refusal_is_symmetric_for_unfinished_comparisons(tmp_path):
    args = _fixture(tmp_path, stop_block2=True, over_budget=True)
    result = _generate(tmp_path, *args)
    assert result["hard_gates"]["budget"]["status"] == "fail"
    assert {item["judgment"] for item in result["comparisons"]} == {
        report.INDETERMINATE}
    for item in result["comparisons"]:
        codes = {reason["code"] for reason in item["reasons"]}
        assert "budget_exceeded" in codes
        assert "budget_preflight_refused" in codes


def test_complete_samples_over_budget_invalidates_all_comparisons(tmp_path):
    args = _fixture(tmp_path, over_budget=True)
    result = _generate(tmp_path, *args)
    assert result["hard_gates"]["budget"]["status"] == "fail"
    assert all(item["judgment"] == report.INDETERMINATE
               for item in result["comparisons"])
    for item in result["comparisons"]:
        codes = {reason["code"] for reason in item["reasons"]}
        assert "budget_exceeded" in codes
        assert "budget_preflight_refused" not in codes


def test_budget_public_validation_failure_invalidates_all_comparisons(
        tmp_path, monkeypatch):
    args = _fixture(tmp_path)

    def reject_public_validation(_path):
        raise driver.DriverError("公開 validator: 予算を超過済み")

    monkeypatch.setattr(report, "read_budget", reject_public_validation)
    result = _generate(tmp_path, *args)
    assert result["hard_gates"]["budget"]["status"] == "fail"
    assert all(item["judgment"] == report.INDETERMINATE
               for item in result["comparisons"])
    for item in result["comparisons"]:
        codes = {reason["code"] for reason in item["reasons"]}
        assert codes == {"budget_public_validation_failed"}


def test_preflight_refusal_always_has_global_schedule_failure(tmp_path):
    args = _fixture(tmp_path, stop_block2=True)
    result = _generate(tmp_path, *args)
    assert result["hard_gates"]["budget"]["status"] == "fail"
    assert result["hard_gates"]["schedule"]["block2"]["status"] == "fail"
    assert all(item["judgment"] == report.INDETERMINATE
               for item in result["comparisons"])
    for item in result["comparisons"]:
        codes = {reason["code"] for reason in item["reasons"]}
        assert "schedule_incomplete" in codes
        assert "budget_preflight_refused" in codes


def test_missing_freeze_still_generates_structured_report(tmp_path):
    budget_path = tmp_path / "time_ledger.json"
    budget_path.write_text(json.dumps({
        "total_budget_s": 43_200, "spent_s": 0.0, "entries": [],
    }), encoding="utf-8")
    result, json_path, md_path = report.generate_report(
        freeze_path=tmp_path / "missing-freeze.json", budget_path=budget_path,
        output_root=str(tmp_path / "output"), generated_at_head="b" * 40)
    assert json_path.is_file() and md_path.is_file()
    assert result["hard_gates"]["freeze"]["status"] == "fail"
    assert result["comparisons"] == []
    assert result["families"]["s1a"]["judgment"] == report.INDETERMINATE


def test_receipt_exists_but_report_freeze_gate_stays_legacy_strict(
        tmp_path, monkeypatch):
    receipt = tmp_path / T080.RECEIPT_REL
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(T080, "ROOT", tmp_path)

    def adapter_must_not_run(*_args, **_kwargs):
        pytest.fail("report legacy 経路が T-080 adapter を呼んだ")

    monkeypatch.setattr(T080, "verify_receipt", adapter_must_not_run)
    monkeypatch.setattr(T080, "static_gate_adapter", adapter_must_not_run)
    assert (T080.ROOT / T080.RECEIPT_REL).is_file()

    document, freeze_path, budget_path = _fixture(tmp_path)
    result = report.build_report(
        freeze_path=freeze_path,
        budget_path=budget_path,
        output_root=str(tmp_path / "output"),
        freeze_verify=lambda _path: document,
        generated_at_head="a" * 40,
    )
    freeze_gate = result["hard_gates"]["freeze"]
    assert freeze_gate == {"status": "pass", "reasons": []}
    assert result["comparisons"]


def test_report_production_module_does_not_import_t080_adapter():
    source = Path(report.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
            imports.extend(alias.name for alias in node.names)
    assert not [name for name in imports if "t080_freeze_migration" in name]
    assert "verify_receipt" not in source and "static_gate_adapter" not in source
