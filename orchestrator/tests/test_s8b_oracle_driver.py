# -*- coding: utf-8 -*-
"""8b oracle driver の gate、binding、budget、WAL 契約を検査する。"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR))

from campaign import pipeline, s8b_budget, s8b_oracle_driver as driver, wal  # noqa: E402
from campaign import s8b_oracle_manifest as manifest_module  # noqa: E402
from campaign.layout import campaign_layout  # noqa: E402
from campaign.model import Genome  # noqa: E402
from campaign.s1_direct_comparison import PreparedCell  # noqa: E402


REAL_FREEZE = ROOT / "output/s8b-freeze/holdout_freeze.json"
CONFIGURATIONS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_document() -> dict:
    return json.loads(REAL_FREEZE.read_text(encoding="utf-8"))


def _holdout_ids() -> tuple[str, ...]:
    return tuple(_real_document()["holdouts"])


def _synthetic_freeze(tmp_path: Path, *, total_bench_s: float = 1000.0) -> Path:
    document = _real_document()
    # 並行中の設計再凍結 draft は freeze 生成後の未コミット差分なので、fixture は
    # 現在の source byte を記録して provenance 検査を通す。
    design = ROOT / document["design_source"]["path"]
    document["design_source"]["sha256"] = _sha256(design)
    holdout_ids = tuple(document["holdouts"])
    document["floor"] = {
        "by_holdout": {holdout_id: 0.01 for holdout_id in holdout_ids},
    }
    document["budget"] = {
        "total_bench_s": total_bench_s,
        "per_holdout_bench_s": {
            holdout_id: total_bench_s for holdout_id in holdout_ids
        },
        "oracle_shared": True,
    }
    path = tmp_path / "holdout_freeze.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def _floor_only_freeze(tmp_path: Path) -> Path:
    document = _real_document()
    design = ROOT / document["design_source"]["path"]
    document["design_source"]["sha256"] = _sha256(design)
    document["floor"] = {
        "by_holdout": {holdout_id: 0.01 for holdout_id in document["holdouts"]},
    }
    path = tmp_path / "holdout_freeze_floor_only.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def _prepare_factory(
    *, fail_first: bool = False, token_suffix: str = "",
    suffix_first_only: bool = False,
):
    calls: list[dict] = []

    @contextlib.contextmanager
    def fake_prepare(cell, ccbench_pin):
        calls.append({"cell": cell, "ccbench_pin": ccbench_pin})
        if fail_first and len(calls) == 1:
            raise OSError("transient checkout failure")
        entry = cell["variant"]
        genome = Genome("silo", dict(entry["flags"]))
        token = "fixture-" + hashlib.sha256(
            json.dumps(entry, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if not suffix_first_only or len(calls) == 1:
            token += token_suffix
        yield PreparedCell(
            genome=genome, src_token=token,
            ccbench_dir="/tmp/fixture-ccbench", cache_root="/tmp/fixture-cache",
        )

    fake_prepare.calls = calls
    return fake_prepare


def _schedule() -> dict:
    return manifest_module.build_schedule(
        n=1, master_seed="driver-fixture", block_sizes={"b0": 1},
        holdout_ids=_holdout_ids(), configuration_ids=CONFIGURATIONS,
    )


def _source(path: str) -> dict:
    source = ROOT / path
    return {"path": path, "sha256": _sha256(source)}


def _write_manifest(tmp_path: Path, freeze_path: Path, prepare_fn,
                    ) -> tuple[Path, dict]:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    schedule = _schedule()
    bindings = []
    for holdout_id in _holdout_ids():
        for configuration_id in CONFIGURATIONS:
            identity = driver.prepare_binding(
                freeze=freeze, holdout_id=holdout_id,
                configuration_id=configuration_id,
                ccbench_pin="fixture-pin", prepare_fn=prepare_fn,
            )
            bindings.append({
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                **identity,
            })
    document = manifest_module.build_manifest(
        freeze_path=freeze_path,
        schedule=schedule,
        run_contract={
            "ccbench_pin": "fixture-pin", "env_tag": "fixture-env",
            "clocks": 1800, "reps": 1, "extime": 1,
            "verify": "legacy+s2", "screening": "off",
            "bench_max_rounds": 1,
        },
        binding_identity=bindings,
        campaign_ids={"b0": "s8b-oracle-fixture-b0"},
        allowed_excluded_reasons=["machine-failure"],
        generator_versions={
            "materializer": _source("orchestrator/campaign/s1_direct_comparison.py"),
            "report": _source("orchestrator/campaign/s8b_oracle_report.py"),
            "judge": _source("orchestrator/campaign/s8b_oracle_judge.py"),
        },
    )
    path = tmp_path / "oracle_manifest.json"
    manifest_module.write_manifest(path, document)
    return path, document


def _fake_evaluate_factory(*, bench_wall_s: float = 0.25):
    calls: list[dict] = []

    def fake_evaluate(genome, layout, env_tag, ccbench_commit, perf,
                      clocks_per_us, **kwargs):
        calls.append({
            "genome": genome, "layout": layout, "env_tag": env_tag,
            "ccbench_commit": ccbench_commit, "perf": perf,
            "clocks_per_us": clocks_per_us, "kwargs": kwargs,
        })
        variant = pipeline.variant_id(genome, kwargs["src_token"])
        wal.log(layout, variant, "build_start", env_tag, {
            "genome": genome.canonical(), "src_token": kwargs["src_token"],
        })
        wal.log(layout, variant, "build_done", env_tag, {
            "trace_bin": "trace", "perf_bin": "perf",
        })
        for tag in (pipeline.LEGACY_TAG, pipeline.S2_TAG):
            wal.log(layout, variant, "verify_done", env_tag, {
                "verdict": "serializable", "certified": True,
                "workload": {"tag": tag},
            })
        wal.log(layout, variant, "bench_done", env_tag, {
            "tps": [10.0, 12.0], "median_tps": 11.0,
            "bench_wall_s": bench_wall_s,
        })
        wal.log(layout, variant, "commit", env_tag, {
            "fitness_tps": 11.0,
            "verify_configs": [pipeline.LEGACY_TAG, pipeline.S2_TAG],
        })
        return pipeline.EvalResult(
            genome=genome, variant=variant, certified=True, aborted=False,
            fitness_tps=11.0,
        )

    fake_evaluate.calls = calls
    return fake_evaluate


def _fake_abort_evaluate_factory(reason: str):
    calls: list[dict] = []

    def fake_evaluate(genome, layout, env_tag, ccbench_commit, perf,
                      clocks_per_us, **kwargs):
        calls.append({"reason": reason})
        variant = pipeline.variant_id(genome, kwargs["src_token"])
        wal.log(layout, variant, "build_start", env_tag, {
            "genome": genome.canonical(), "src_token": kwargs["src_token"],
        })
        wal.log(layout, variant, "build_done", env_tag, {
            "trace_bin": "trace", "perf_bin": "perf",
        })
        wal.log(layout, variant, "abort", env_tag, {
            "reason": reason, "workload": {"tag": pipeline.LEGACY_TAG},
        })
        return pipeline.EvalResult(
            genome=genome, variant=variant, certified=False, aborted=True,
        )

    fake_evaluate.calls = calls
    return fake_evaluate


def _run(tmp_path: Path, freeze_path: Path, manifest_path: Path,
         prepare_fn, evaluate_fn):
    # strict v2 verifier 導入前の run gate は意図どおり常に閉じる。
    # driver 内部の WAL/budget 契約テストだけ future-approved gate を代入する。
    with mock.patch.object(
            driver, "gate_check", return_value=driver.GateDecision(True, [])):
        return driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=tmp_path / "out", budget_path=tmp_path / "budget.json",
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )


def test_real_freeze_gate_lists_floor_and_budget_null():
    decision = driver.gate_check(freeze_path=REAL_FREEZE, root=ROOT)
    assert not decision.allowed
    assert any(reason.startswith("floor-null:") for reason in decision.refusals)
    assert any(reason.startswith("budget-null:") for reason in decision.refusals)


def test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing(tmp_path):
    manifest_freeze = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, manifest_freeze, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()
    output_root = tmp_path / "refused-out"
    budget_path = tmp_path / "refused-budget.json"

    result = driver.run_block(
        manifest_path=manifest_path, block_id="b0", freeze_path=REAL_FREEZE,
        root=ROOT, output_root=output_root, budget_path=budget_path,
        prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
    )

    assert result["status"] == "refused" and result["allowed"] is False
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not output_root.exists() and not budget_path.exists()


def test_nonnull_floor_requires_v2_verifier_and_run_block_writes_nothing(tmp_path):
    freeze_path = _floor_only_freeze(tmp_path)
    manifest_freeze = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, manifest_freeze, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()
    output_root = tmp_path / "v2-refused-out"
    budget_path = tmp_path / "v2-refused-budget.json"

    result = driver.run_block(
        manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
        root=ROOT, output_root=output_root, budget_path=budget_path,
        prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
    )

    assert result["status"] == "refused"
    assert any(reason.startswith("freeze-v2-verifier-not-implemented:")
               for reason in result["refusals"])
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not output_root.exists() and not budget_path.exists()


def test_success_wal_order_budget_and_evaluate_contract(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "completed"
    assert result["completed_trials"] == len(document["schedule"]["rows"])
    session_events = [event["event"] for event in result["events"]]
    assert session_events == ["campaign-start", *(
        event for _row in document["schedule"]["rows"]
        for event in ("trial-start", "trial-result")
    )]
    assert len(evaluate_fn.calls) == len(document["schedule"]["rows"])
    for call in evaluate_fn.calls:
        kwargs = call["kwargs"]
        assert kwargs["do_bench"] is True
        assert kwargs["screening"] is None
        assert len(kwargs["extra_correctness"]) == 1
        tag, workload = kwargs["extra_correctness"][0]
        assert tag == pipeline.S2_TAG
        assert workload.flags == pipeline.s2_correctness_workload().flags
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json", manifest_sha256=result["manifest_sha256"],
    )
    assert len(ledger["entries"]) == len(document["schedule"]["rows"])
    assert ledger["spent"]["bench_s"] == pytest.approx(
        0.25 * len(document["schedule"]["rows"])
    )


def test_binding_mismatch_refuses_only_that_row_before_evaluate(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, manifest_prepare,
    )
    prepare_fn = _prepare_factory(token_suffix="-changed", suffix_first_only=True)
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert [event["event"] for event in result["events"][:3]] == [
        "campaign-start", "trial-start", "binding-refused",
    ]
    assert len(evaluate_fn.calls) == len(document["schedule"]["rows"]) - 1


def test_budget_refusal_stops_block_and_marks_all_remaining_skipped(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=0.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "budget-refused"
    events = result["events"]
    assert [event["event"] for event in events[:3]] == [
        "campaign-start", "trial-start", "budget-refused",
    ]
    skipped = [event for event in events if event["event"] == "trial-skipped"]
    assert len(skipped) == len(document["schedule"]["rows"]) - 1
    assert evaluate_fn.calls == []


def test_postflight_budget_debit_refusal_keeps_result_and_skips_remaining(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory(bench_wall_s=1.5)

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "budget-refused"
    assert result["completed_trials"] == 1
    events = result["events"]
    assert [event["event"] for event in events[:5]] == [
        "campaign-start", "trial-start", "trial-result", "deviation",
        "budget-refused",
    ]
    deviation = next(event for event in events if event["event"] == "deviation")
    assert deviation["kind"] == "budget-debit-refused"
    skipped = [event for event in events if event["event"] == "trial-skipped"]
    assert len(skipped) == len(document["schedule"]["rows"]) - 1
    assert len(evaluate_fn.calls) == 1
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json", manifest_sha256=result["manifest_sha256"],
    )
    assert ledger["entries"] == []


def test_verify_inconclusive_and_unknown_abort_reasons_are_fail_closed(tmp_path):
    trace_root = tmp_path / "trace"
    trace_root.mkdir()
    freeze_path = _synthetic_freeze(trace_root)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(trace_root, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    trace_empty = _fake_abort_evaluate_factory("trace-empty")

    trace_result = _run(
        trace_root, freeze_path, manifest_path, prepare_fn, trace_empty,
    )

    trace_outcomes = [event["outcome"] for event in trace_result["events"]
                      if event["event"] == "trial-result"]
    assert trace_outcomes and set(trace_outcomes) == {"verify-inconclusive"}

    unknown_root = tmp_path / "unknown"
    unknown_root.mkdir()
    unknown_freeze = _synthetic_freeze(unknown_root)
    unknown_prepare = _prepare_factory()
    unknown_manifest, _ = _write_manifest(
        unknown_root, unknown_freeze, unknown_prepare,
    )
    unknown_prepare.calls.clear()
    unknown_evaluate = _fake_abort_evaluate_factory("future-unclassified-abort")

    unknown_result = _run(
        unknown_root, unknown_freeze, unknown_manifest,
        unknown_prepare, unknown_evaluate,
    )

    assert unknown_result["status"] == "error"
    assert not any(event["event"] == "trial-result"
                   for event in unknown_result["events"])
    deviation = next(event for event in unknown_result["events"]
                     if event["event"] == "deviation")
    assert deviation["kind"] == "unknown-abort-reason"
    assert deviation["abort_reason"] == "future-unclassified-abort"
    assert len(unknown_evaluate.calls) == 1


def test_transient_prepare_failure_retries_once(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    stable_prepare = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, stable_prepare)
    retrying_prepare = _prepare_factory(fail_first=True)
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path,
                  retrying_prepare, evaluate_fn)

    prefix = [event["event"] for event in result["events"][:5]]
    assert prefix == [
        "campaign-start", "trial-start", "retry", "trial-start", "trial-result",
    ]
    assert result["events"][2]["attempt"] == 2
    assert len(evaluate_fn.calls) == len(document["schedule"]["rows"])


def test_tampered_freeze_fails_source_verification(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    document = json.loads(freeze_path.read_text(encoding="utf-8"))
    document["floor"] = None
    document["budget"] = None
    document["confirmed_by"] = document["confirmed_by"] + "-tampered"
    freeze_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")

    decision = driver.gate_check(freeze_path=freeze_path, root=ROOT)

    assert not decision.allowed
    assert any(reason.startswith("holdout-freeze-verify:")
               for reason in decision.refusals)


def test_layer3_strict_consumer_accepts_optional_bench_wall_s():
    schema = json.loads(
        (ORCHESTRATOR / "campaign/layer3_schema.json").read_text(encoding="utf-8")
    )
    runs = schema["properties"]["runs"]["items"]
    assert runs["additionalProperties"] is False
    assert runs["properties"]["bench_wall_s"] == {
        "type": "number", "minimum": 0,
    }
    assert "bench_wall_s" not in runs["required"]
