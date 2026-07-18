# -*- coding: utf-8 -*-
"""8b oracle driver の gate、binding、budget、WAL 契約を検査する。"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest import mock

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import s8b_v2_freeze_fixture as v2_fixture  # noqa: E402
import test_s8b_ratified_freeze as ratified_fixture  # noqa: E402
from campaign import env_contract as ec  # noqa: E402
from campaign import execution_guard  # noqa: E402
from campaign import pipeline, s8b_budget, s8b_oracle_driver as driver, wal  # noqa: E402
from campaign import s8b_freeze_io  # noqa: E402
from campaign import s8b_materialization  # noqa: E402
from campaign import s8b_oracle_manifest as manifest_module  # noqa: E402
from campaign import s8b_ratified_freeze  # noqa: E402
from campaign import s8b_run_marker  # noqa: E402
from campaign.layout import campaign_layout  # noqa: E402
from campaign.model import Genome  # noqa: E402
from campaign.s1_direct_comparison import PreparedCell  # noqa: E402


REAL_FREEZE = ROOT / "output/s8b-freeze/holdout_freeze.json"
CONFIGURATIONS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)
# driver v2 実走 fixture の env (env_contract registry の唯一の登録 env かつ
# p2_2.ENV_TAG と一致する = machine-pin を満たす)。
V2_ENV_TAG = "linux-baremetal"


def _contract_sha256() -> str:
    return ec.lookup(V2_ENV_TAG).contract_sha256


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
    # strict v2: per-pair floor + budget を共有 fixture で充填する (C3-4)。
    v2_fixture.fill(
        document, total_bench_s=total_bench_s, per_holdout_bench_s=total_bench_s,
    )
    path = tmp_path / "holdout_freeze.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def _floor_only_freeze(tmp_path: Path) -> Path:
    document = _real_document()
    design = ROOT / document["design_source"]["path"]
    document["design_source"]["sha256"] = _sha256(design)
    # floor だけ per-pair で充填し budget は null のまま (v2 refusal 経路の fixture)。
    document["floor"] = v2_fixture.per_pair_floor(document)
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
            identity = s8b_materialization.prepare_binding(
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
            "ccbench_pin": "fixture-pin", "env_tag": V2_ENV_TAG,
            "clocks": ec.lookup(V2_ENV_TAG).clocks_per_us, "reps": 1, "extime": 1,
            "verify": "legacy+s2", "screening": "off",
            "bench_max_rounds": 1,
            "contract_sha256": _contract_sha256(),
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


def _canned_plan(**kwargs) -> "driver._V2Plan":
    """WAL/budget 契約テスト用の canned v2 plan (git/store の実検査を迂回)。

    _prepare_v2_execution の差し替えとして使う。渡された ``schedule`` kwarg から cell を
    列挙するため manifest/freeze を再読しない (read カウント系テストを汚さない)。contract は
    実 env 契約 lookup (clocks/numactl の正本)、receipt は実 guard 生成、perf_sha_by_cell は
    全 cell を dummy 64hex で埋める (fake evaluate は expected_perf_sha256 を捕捉するだけ)。"""
    contract = ec.lookup(V2_ENV_TAG)
    perf = {
        (row["holdout_id"], row["configuration_id"]): "0" * 64
        for row in kwargs["schedule"]
    }
    return driver._V2Plan(
        contract=contract,
        receipt=execution_guard.build_receipt(contract),
        perf_sha_by_cell=perf,
    )


def _run(tmp_path: Path, freeze_path: Path, manifest_path: Path,
         prepare_fn, evaluate_fn, *, output_root=None, budget_path=None,
         marker_root=None):
    # driver 内部の WAL/budget 契約テストは v2 gate/launch/store/env の実検査を迂回し、
    # future-approved gate + canned v2 plan を代入して WAL・budget・schedule 契約だけを
    # 突く (v2 gate/store/env の実発火は専用テストが git fixture で検査する)。
    def fake_ratify(_root):
        raise s8b_ratified_freeze.RatifiedFreezeError("mocked", "canned plan 経路")

    with mock.patch.object(
                driver, "gate_check",
                return_value=driver.GateDecision(True, [])), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "load_ratified_freeze", fake_ratify), \
            mock.patch.object(driver, "_prepare_v2_execution", _canned_plan):
        return driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=output_root or (tmp_path / "out"),
            budget_path=budget_path or (tmp_path / "budget.json"),
            marker_root=marker_root or (tmp_path / "markers"),
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


def test_nonnull_floor_without_active_generation_is_refused(tmp_path):
    """v2 (floor 充填) freeze だが実 repo に承認束縛済み active 世代が無い場合、
    active 解決失敗を freeze-ratify refusal に翻訳し、一切書かずに倒す (RatifiedFreezeError
    を例外として漏らさない)。"""
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
    assert any(reason.startswith("freeze-ratify:")
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
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert len(ledger["entries"]) == len(document["schedule"]["rows"])
    assert ledger["spent"]["bench_s"] == pytest.approx(
        0.25 * len(document["schedule"]["rows"])
    )
    # terminal 後の精算: charged==actual==実測、reserved は分離して残る。
    reservation = ledger["reservation"]
    assert reservation["status"] == "settled"
    assert reservation["charged_bench_s"] == pytest.approx(
        0.25 * len(document["schedule"]["rows"])
    )
    assert reservation["actual_bench_s"] == pytest.approx(
        0.25 * len(document["schedule"]["rows"])
    )
    assert reservation["reserved_bench_s"] == pytest.approx(
        float(len(document["schedule"]["rows"]))
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


def test_v8_bulk_reservation_unavailable_runs_nothing(tmp_path):
    """V8: 残枠が全行最大費用未満なら一行も走らず budget_exhausted_before_attempt を耐久化。

    reservation 総額 = extime×reps×bench_max_rounds×行数。total_bench_s=0.0 では確保できず、
    driver は trial-start を一つも出さず terminal を budget ledger と WAL の双方へ書く。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=0.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "budget_exhausted_before_attempt"
    assert result["completed_trials"] == 0
    events = result["events"]
    assert [event["event"] for event in events] == [
        "campaign-start", "budget-exhausted-before-attempt",
    ]
    # 一行も走らせない: prepare も evaluate も trial-start も発火しない。
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not any(event["event"] == "trial-start" for event in events)
    # terminal は budget ledger にも耐久化される (reservation status=exhausted)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["reservation"]["status"] == "exhausted"
    assert ledger["reservation"]["reserved_bench_s"] == pytest.approx(
        float(len(document["schedule"]["rows"]))
    )
    assert ledger["entries"] == []


def test_reservation_envelope_exceeded_is_fail_closed(tmp_path):
    """実測 bench が予約枠を超過したら fail-closed で error に倒す (protocol violation)。

    reservation 枠 = 行数×(extime×reps×rounds)=行数×1。1 行目の実測 1.5 で単 holdout 枠
    (6 行×1=6) は超えないが、全 12 行を 1.5 で回すと総枠 12 を超える経路がある。ここでは
    per-holdout 枠超過 (h の 6 行×1.5=9 > 予約 6) を fixture で発火させる。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    # 各 trial の実測 bench_wall_s=1.5 > per-row 予約 1.0。holdout 枠 (6 行×1=6) を
    # 5 行目 (実測累計 7.5) で超える。
    evaluate_fn = _fake_evaluate_factory(bench_wall_s=1.5)

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "error"
    deviation = next(event for event in result["events"]
                     if event["event"] == "deviation")
    assert deviation["kind"] == "reservation-envelope-exceeded"
    # error では精算しない (予約枠を非解放のまま残す)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["reservation"]["status"] == "held"
    # 所見4: entries 永続化状態を検査する。append_entry は _atomic_replace_json を
    # 呼ぶ前に BudgetError を raise するため、超過を起こした行の entry は台帳に
    # 一切残らない。超過より前に (schedule 順で) 成功した行の entry はそのまま
    # 残る。schedule は擬似乱数で shuffle 済みのため holdout ごとに連続しない
    # ので、実際の schedule 順で厳密に検査する (固定 index を仮定しない)。
    rows = document["schedule"]["rows"]
    failing_index = deviation["schedule_index"]
    failing_position = next(
        position for position, row in enumerate(rows)
        if row["schedule_index"] == failing_index
    )
    expected_persisted_indices = {
        row["schedule_index"] for row in rows[:failing_position]
    }
    persisted_indices = {entry["schedule_index"] for entry in ledger["entries"]}
    assert failing_position > 0  # 超過前に成功した行が実在する
    assert persisted_indices == expected_persisted_indices
    assert failing_index not in persisted_indices
    assert len(ledger["entries"]) == failing_position


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


@pytest.mark.parametrize("reason", ["bench-probe-error", "verify-probe-error"])
def test_probe_error_reason_is_fail_closed_unknown_abort(tmp_path, reason):
    """B-7 置換裁定 (D-4): probe 故障 abort reason (bench/verify-probe-error) が oracle
    driver に到達すると、_outcome_for の凍結バケツに無いため _UnknownAbortReason 経路で
    deviation (kind=unknown-abort-reason) + error_stopped になる (fail-closed)。oracle 側
    判定表は D-4 で不変ゆえ trial-result 化 (reservation 精算) しない。"""
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_abort_evaluate_factory(reason)

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "error"
    assert not any(event["event"] == "trial-result" for event in result["events"])
    deviation = next(event for event in result["events"]
                     if event["event"] == "deviation")
    assert deviation["kind"] == "unknown-abort-reason"
    assert deviation["abort_reason"] == reason
    assert len(evaluate_fn.calls) == 1


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


def test_exit_code_priority_table():
    """rc 優先順位表: internal-error(1) > protocol_violation(3) >
    budget-refused(2) > completed(0)。gate-refused も 2、未知 status は 1。"""
    assert driver._exit_code("completed") == 0
    assert driver._exit_code("error") == 1
    assert driver._exit_code("protocol_violation") == 3
    assert driver._exit_code("budget_exhausted_before_attempt") == 2
    assert driver._exit_code("refused") == 2
    # 未知・欠測 status は fail-closed で internal-error(1)。
    assert driver._exit_code("something-unexpected") == 1
    assert driver._exit_code(None) == 1


def test_v3_all_rows_binding_refused_is_protocol_violation(tmp_path):
    """V3 (in-process): 全行 binding-refused で evaluate 0 回、status=protocol_violation。

    現行契約では completed / rc 0 に潰れていた (全行 refused でも budget_stopped で
    なければ completed)。強い completed 定義の下では 1 行でも terminal outcome を
    得なければ protocol_violation に倒す。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, manifest_prepare,
    )
    # manifest とは異なる src_token を全行で作らせ、全 binding を不一致にする。
    prepare_fn = _prepare_factory(token_suffix="-changed")
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "protocol_violation"
    assert result["completed_trials"] == 0
    # 一行も evaluate に到達しない。
    assert evaluate_fn.calls == []
    # 全予定行が未解決として列挙される。
    rows = document["schedule"]["rows"]
    assert set(result["unresolved_rows"]) == {
        row["schedule_index"] for row in rows
    }
    # terminal event が耐久化される。
    events = [event["event"] for event in result["events"]]
    assert events[-1] == "protocol-violation"
    terminal = result["events"][-1]
    assert terminal["completed_trials"] == 0
    assert terminal["scheduled_rows"] == len(rows)
    # protocol_violation では精算しない (reservation は held のまま非解放)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["reservation"]["status"] == "held"
    assert ledger["entries"] == []


def test_v3_partial_binding_refused_is_protocol_violation(tmp_path):
    """1 行だけ binding-refused でも強い completed 定義を満たさず protocol_violation。"""
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, manifest_prepare,
    )
    # 1 行目だけ src_token を変えて binding を不一致にする。
    prepare_fn = _prepare_factory(token_suffix="-changed", suffix_first_only=True)
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    rows = document["schedule"]["rows"]
    assert result["status"] == "protocol_violation"
    assert result["completed_trials"] == len(rows) - 1
    assert len(result["unresolved_rows"]) == 1
    # held のまま (精算しない)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["reservation"]["status"] == "held"


def test_v3_cli_subprocess_returns_rc_3_on_protocol_violation(tmp_path):
    """V3 (subprocess): 全行 binding-refused の CLI 実行が rc 3 を返す。

    in-process だけでなく実プロセス起動で rc を固定する。gate は strict v2
    verifier 未実装のため子プロセス内で future-approved に差し替え、canonical
    budget path も tmp に退避して repo 出力を汚さない。現行 CLI は completed 以外を
    一律 rc 2 (gate-refused/非 completed) に潰し、この経路は rc 0 だった。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, manifest_prepare)
    output_root = tmp_path / "cli-out"
    budget_path = tmp_path / "cli-budget.json"

    # 全行 binding-refused を CLI 経路で再現するため、driver.prepare_cell を
    # manifest とは異なる src_token を返す fixture に差し替える。
    script = textwrap.dedent(
        f"""
        import contextlib, hashlib, json, sys
        from unittest import mock
        sys.path.insert(0, {str(ORCHESTRATOR)!r})
        from campaign import s8b_oracle_driver as driver
        from campaign import env_contract as ec
        from campaign import execution_guard
        from campaign import s8b_ratified_freeze
        from campaign.model import Genome
        from campaign.s1_direct_comparison import PreparedCell

        @contextlib.contextmanager
        def fake_prepare(cell, ccbench_pin):
            entry = cell["variant"]
            genome = Genome("silo", dict(entry["flags"]))
            token = "fixture-" + hashlib.sha256(
                json.dumps(entry, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
            ).hexdigest() + "-changed"
            yield PreparedCell(
                genome=genome, src_token=token,
                ccbench_dir="/tmp/fixture-ccbench",
                cache_root="/tmp/fixture-cache",
            )

        def fake_ratify(_root):
            raise s8b_ratified_freeze.RatifiedFreezeError("mocked", "x")

        def fake_plan(**kwargs):
            contract = ec.lookup("linux-baremetal")
            perf = {{(r["holdout_id"], r["configuration_id"]): "0" * 64
                     for r in kwargs["schedule"]}}
            return driver._V2Plan(
                contract=contract,
                receipt=execution_guard.build_receipt(contract),
                perf_sha_by_cell=perf)

        driver.DEFAULT_BUDGET_PATH = {str(budget_path)!r}
        with mock.patch.object(
                driver, "gate_check",
                return_value=driver.GateDecision(True, [])), \\
             mock.patch.object(driver.s8b_ratified_freeze,
                               "load_ratified_freeze", fake_ratify), \\
             mock.patch.object(driver, "_prepare_v2_execution", fake_plan), \\
             mock.patch.object(driver, "prepare_cell", fake_prepare):
            rc = driver.main([
                "run-block", "--manifest", {str(manifest_path)!r},
                "--block-id", "b0", "--freeze", {str(freeze_path)!r},
                "--root", {str(ROOT)!r}, "--output-root", {str(output_root)!r},
            ])
        sys.exit(rc)
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 3, (proc.returncode, proc.stdout, proc.stderr)
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["status"] == "protocol_violation"
    assert payload["completed_trials"] == 0


def test_cli_subprocess_returns_rc_2_on_gate_refused(tmp_path):
    """gate 拒否 (real freeze の floor/budget null) は CLI 実行で rc 2。"""
    manifest_freeze = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, manifest_freeze, manifest_prepare)
    output_root = tmp_path / "gate-out"
    budget_path = tmp_path / "gate-budget.json"

    script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(ORCHESTRATOR)!r})
        from campaign import s8b_oracle_driver as driver
        driver.DEFAULT_BUDGET_PATH = {str(budget_path)!r}
        rc = driver.main([
            "run-block", "--manifest", {str(manifest_path)!r},
            "--block-id", "b0", "--freeze", {str(REAL_FREEZE)!r},
            "--root", {str(ROOT)!r}, "--output-root", {str(output_root)!r},
        ])
        sys.exit(rc)
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
    assert not output_root.exists() and not budget_path.exists()


def test_load_verified_freeze_single_read_hash_and_strict_parse(tmp_path):
    """loader 単体 (中立 leaf s8b_freeze_io) は byte sha256 を返し、expected_hash
    不一致と非 strict JSON を拒否する (単一 read の hash 束縛と strict parse の直接
    検査)。loader 単体の例外型は FreezeIOError で固定する。"""
    freeze_path = _synthetic_freeze(tmp_path)
    expected = _sha256(freeze_path)

    verified = s8b_freeze_io.load_verified_freeze(freeze_path)
    assert verified.sha256 == expected
    assert verified.document == json.loads(freeze_path.read_text(encoding="utf-8"))

    # expected_hash と一致すれば同じ object を返す。
    assert s8b_freeze_io.load_verified_freeze(
        freeze_path, expected_hash=expected).sha256 == expected
    # 不一致は fail-closed (loader 単体経路は FreezeIOError)。
    with pytest.raises(s8b_freeze_io.FreezeIOError) as mismatch:
        s8b_freeze_io.load_verified_freeze(freeze_path, expected_hash="0" * 64)
    assert "expected_hash" in str(mismatch.value)

    # strict parse: NaN 等の非数値定数を拒否する。
    bad = tmp_path / "bad_freeze.json"
    bad.write_text('{"floor": NaN}', encoding="utf-8")
    with pytest.raises(s8b_freeze_io.FreezeIOError) as strict:
        s8b_freeze_io.load_verified_freeze(bad)
    assert "strict parse" in str(strict.value) or "非数値定数" in str(strict.value)


def test_driver_boundary_wraps_freeze_io_error_as_oracle_driver_error(tmp_path):
    """driver 境界 adapter (_load_verified_freeze) は leaf の FreezeIOError を
    OracleDriverError へ因果付き変換し、message 本文を維持する (driver 経路の
    例外型は OracleDriverError で固定)。"""
    bad = tmp_path / "bad_freeze.json"
    bad.write_text('{"floor": NaN}', encoding="utf-8")
    with pytest.raises(driver.OracleDriverError) as wrapped:
        driver._load_verified_freeze(bad)
    assert isinstance(wrapped.value.__cause__, s8b_freeze_io.FreezeIOError)
    assert "非数値定数" in str(wrapped.value)


def test_run_block_loads_freeze_once_and_passes_same_object_to_gate(tmp_path):
    """run_block は freeze bytes を厳密 1 回だけ読み、その単一 VerifiedFreeze object
    を gate_check(verified=...) へ渡す (verify-use 間 TOCTOU 遮断の実発火)。

    恒真回避: 常時 allowed の gate mock を使わず、gate_check を identity 記録付き
    wrapper に差し替えて渡された object を捕捉し、run_block が load した同一 object
    との identity と freeze byte read=1 を同時に固定する。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, _document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    real_read_bytes = Path.read_bytes
    freeze_reads: list[Path] = []

    def counting_read_bytes(self):
        if Path(self) == Path(freeze_path):
            freeze_reads.append(Path(self))
        return real_read_bytes(self)

    loaded: dict = {}
    real_loader = driver._load_verified_freeze

    def recording_loader(path, expected_hash=None):
        obj = real_loader(path, expected_hash)
        loaded["obj"] = obj
        return obj

    captured: dict = {}

    def recording_gate(*, freeze_path, manifest_path, root, verified=None,
                       verified_manifest=None, ratified=None, ratified_error=None):
        captured["verified"] = verified
        captured["verified_manifest"] = verified_manifest
        return driver.GateDecision(True, [])

    def fake_ratify(_root):
        raise s8b_ratified_freeze.RatifiedFreezeError("mocked", "x")

    with mock.patch.object(Path, "read_bytes", counting_read_bytes), \
            mock.patch.object(driver, "_load_verified_freeze", recording_loader), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "load_ratified_freeze", fake_ratify), \
            mock.patch.object(driver, "_prepare_v2_execution", _canned_plan), \
            mock.patch.object(driver, "gate_check", recording_gate):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=tmp_path / "out", budget_path=tmp_path / "budget.json",
            marker_root=tmp_path / "markers",
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "completed"
    # freeze byte read はちょうど 1 回 (run_block 冒頭の単一 load。gate/manifest verify
    # は単一 object を使い回し freeze を再読しない)。
    assert len(freeze_reads) == 1
    # gate_check に渡った verified は run_block が load したまさに同一 object。
    assert isinstance(captured["verified"], s8b_freeze_io.VerifiedFreeze)
    assert captured["verified"] is loaded["obj"]
    # C2-9: gate_check には検証済み VerifiedManifest が渡り (再検証させない)、
    # run_block はそれを本体でも使い回す (再読込しない)。
    assert isinstance(captured["verified_manifest"], manifest_module.VerifiedManifest)


def test_run_block_verifies_manifest_once_and_reuses_object(tmp_path):
    """C2-9 / A3-6 (manifest 側): run_block は manifest を厳密 1 回だけ verify し、
    その単一 VerifiedManifest object を gate と本体で共有する (verify->use 間の
    再読込・再検証をしない)。freeze 側の read=1 + 同一 object 固定
    (test_run_block_loads_freeze_once...) の manifest 版。

    恒真回避: verify_manifest 呼び出し数・manifest byte read 数・gate へ渡った
    object の identity を同時に固定する。本体が manifest を disk から再読込する
    (raw re-read) か再検証する (verify_manifest 再呼び出し) 退行はどちらも
    read>1 / verify>1 で kill される。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, _document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    real_read_text = Path.read_text
    manifest_reads: list[Path] = []

    def counting_read_text(self, *args, **kwargs):
        if Path(self) == Path(manifest_path):
            manifest_reads.append(Path(self))
        return real_read_text(self, *args, **kwargs)

    real_verify = driver.verify_manifest
    verify_calls: list[Path] = []
    captured: dict = {}

    def counting_verify(path, **kwargs):
        verify_calls.append(Path(path))
        result = real_verify(path, **kwargs)
        captured["verified_manifest"] = result
        return result

    def recording_gate(*, freeze_path, manifest_path, root, verified=None,
                       verified_manifest=None, ratified=None, ratified_error=None):
        captured["gate_manifest"] = verified_manifest
        return driver.GateDecision(True, [])

    def fake_ratify(_root):
        raise s8b_ratified_freeze.RatifiedFreezeError("mocked", "x")

    with mock.patch.object(Path, "read_text", counting_read_text), \
            mock.patch.object(driver, "verify_manifest", counting_verify), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "load_ratified_freeze", fake_ratify), \
            mock.patch.object(driver, "_prepare_v2_execution", _canned_plan), \
            mock.patch.object(driver, "gate_check", recording_gate):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=tmp_path / "out", budget_path=tmp_path / "budget.json",
            marker_root=tmp_path / "markers",
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "completed"
    # manifest は厳密 1 回だけ verify され (本体は再検証しない)。
    assert len(verify_calls) == 1
    # manifest byte read もちょうど 1 回 (本体は verified object を使い再読込しない)。
    assert len(manifest_reads) == 1
    # gate へ渡った VerifiedManifest は verify_manifest が返したまさに同一 object。
    assert isinstance(captured["verified_manifest"], manifest_module.VerifiedManifest)
    assert captured["gate_manifest"] is captured["verified_manifest"]


def test_v6_freeze_swap_after_verify_is_not_observed(tmp_path):
    """V6: gate/manifest 検証後に freeze bytes を差し替えても、単一 object 使い回し
    (load_verified_freeze) により差替え後の値 (budget limits・perf 三軸) が一切
    使われない。

    verify_manifest 直後に freeze ファイルを悪性 bytes (holdout records を +777、
    budget を 0.0) へ差し替える。単一 object を使う実装では driver は元の verified
    値だけを使い completed になる。もし verify 後に freeze を再読込する構造なら、
    差替え後の budget=0 で budget_exhausted に倒れ、perf.records も +777 に汚染
    されるため FAIL する (verify-use 間 TOCTOU の再現を kill する)。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, _document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    original = json.loads(freeze_path.read_text(encoding="utf-8"))
    original_records = {
        holdout_id: original["holdouts"][holdout_id]["records"]
        for holdout_id in _holdout_ids()
    }
    poisoned_records = {value + 777 for value in original_records.values()}
    real_verify = manifest_module.verify_manifest

    def swapping_verify(path, **kwargs):
        result = real_verify(path, **kwargs)
        # 検証が通った直後に freeze ファイルを悪性 bytes へ差し替える。
        malicious = json.loads(freeze_path.read_text(encoding="utf-8"))
        for holdout_id in _holdout_ids():
            malicious["holdouts"][holdout_id]["records"] = (
                original_records[holdout_id] + 777
            )
        malicious["budget"]["total_bench_s"] = 0.0
        malicious["budget"]["per_holdout_bench_s"] = {
            holdout_id: 0.0 for holdout_id in _holdout_ids()
        }
        freeze_path.write_text(
            json.dumps(malicious, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result

    with mock.patch.object(driver, "verify_manifest", swapping_verify):
        result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    # 差替え後の budget=0 が使われていれば budget_exhausted。単一 object なら completed。
    assert result["status"] == "completed"
    # perf 三軸: records は元の値で、+777 の汚染値を一切含まない。
    assert evaluate_fn.calls
    for call in evaluate_fn.calls:
        assert call["perf"].records in original_records.values()
        assert call["perf"].records not in poisoned_records
    # budget limits も元の 1000.0 (差替え後の 0.0 でない)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["limits"]["total_bench_s"] == pytest.approx(1000.0)


def test_v7_manifest_swap_after_verify_is_not_observed(tmp_path):
    """V7: gate/本体で共有する VerifiedManifest により、verify 後に manifest bytes を
    差し替えても差替え後の値 (campaign_id) が一切使われない (C2-9 の manifest 版)。

    verify_manifest 直後に manifest ファイルの campaign_ids を悪性値へ差し替える。
    単一 object を使う実装では driver は元の verified document だけを使い、
    result["campaign_id"] は差替え前の値のまま completed になる。もし verify 後に
    manifest を再読込 (raw) または再検証する構造なら差替え後の campaign_id を観測して
    FAIL する (verify-use 間 TOCTOU の再現を kill する)。V6 が freeze に対して行うのと
    同型。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    original_campaign_id = manifest_module.config_for_block(
        document, "b0")["campaign_id"]
    poisoned_campaign_id = original_campaign_id + "-POISONED"
    real_verify = manifest_module.verify_manifest

    def swapping_verify(path, **kwargs):
        result = real_verify(path, **kwargs)
        # 検証が通った直後に manifest の campaign_ids を悪性値へ差し替える。
        malicious = json.loads(manifest_path.read_text(encoding="utf-8"))
        malicious["campaign_ids"]["b0"] = poisoned_campaign_id
        manifest_path.write_text(
            json.dumps(malicious, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result

    with mock.patch.object(driver, "verify_manifest", swapping_verify):
        result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    # 単一 object 実装なら差替え前の campaign_id で completed。再読込/再検証する退行は
    # 差替え後の POISONED を観測する。
    assert result["status"] == "completed"
    assert result["campaign_id"] == original_campaign_id
    assert result["campaign_id"] != poisoned_campaign_id


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


# ---- R6: resume 拒否の強化 (原子的 lock + 実走済みマーカー + truncated WAL 閉鎖) ----

def _campaign_id(manifest_path: Path) -> str:
    # campaign_id の抽出だけが目的なので verify (freeze_document 必須) は経由せず、
    # plain load + config_for_block で射影する。
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest_module.config_for_block(document, "b0")["campaign_id"]


def test_v2_resume_rejected_at_s1_s2_s3_boundaries(tmp_path):
    """V2 (択 a): S1/S2/S3 各境界直後の crash を模擬し、再起動が全拒否されること。

    S1 = 実走済みマーカー + lock 生成済み・WAL なし、S2 = ledger も生成済み・WAL なし、
    S3 = campaign-start が WAL に耐久化済み。いずれの境界でも新プロセスの resume は
    構造化拒否 (OracleDriverError) で倒れ、prepare/evaluate に一切到達しない。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    output_root = tmp_path / "out"
    marker_root = tmp_path / "markers"
    identity = s8b_run_marker.freeze_identity(freeze_path)
    layout = campaign_layout(_campaign_id(manifest_path), output_root=str(output_root))

    def attempt():
        return _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn,
                    output_root=output_root, marker_root=marker_root)

    # S1: マーカー + lock 生成済み、WAL/ledger なし。
    layout.ensure()
    assert wal.acquire_lock_atomic(layout, "s1-preimage") is True
    s8b_run_marker.create_run_marker(marker_root, identity, {"stage": "s1"})
    with pytest.raises(driver.OracleDriverError) as s1:
        attempt()
    assert "マーカー" in str(s1.value)

    # S2: ledger 生成済みでも WAL がまだ無い段階。境界は S1 と同じくマーカーが捕捉する。
    s8b_budget.create_ledger(
        tmp_path / "budget.json", manifest_sha256="deadbeef",
        freeze_sha256=identity, schedule_sha256="cafebabe",
        limits={"total_bench_s": 1.0,
                "per_holdout_bench_s": {h: 1.0 for h in _holdout_ids()},
                "oracle_shared": True},
    )
    with pytest.raises(driver.OracleDriverError) as s2:
        attempt()
    assert "マーカー" in str(s2.value)

    # S3: campaign-start が WAL に耐久化済み (実走中 crash)。WAL byte 存在で拒否。
    driver._append_session(layout, "fixture-env", "campaign-start", {
        "campaign_id": layout.root, "block_id": "b0",
    })
    assert wal.wal_bytes_present(layout) is True
    with pytest.raises(driver.OracleDriverError) as s3:
        attempt()
    assert "WAL byte" in str(s3.value)

    assert prepare_fn.calls == [] and evaluate_fn.calls == []


def test_atomic_one_shot_lock_rejects_second_start(tmp_path):
    """既存 campaign.lock (マーカー無し) の resume/並行起動を原子的 lock が拒否する。

    O_CREAT|O_EXCL による one-shot lock の獲得失敗 = 着手済み/並行として fail-closed。
    非原子の write_lock (exists→上書きなし) では二重通過しうる経路を閉じる。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()

    output_root = tmp_path / "out"
    layout = campaign_layout(_campaign_id(manifest_path), output_root=str(output_root))
    layout.ensure()
    assert wal.acquire_lock_atomic(layout, "prior-holder") is True
    # 同じ lock の二度目の原子的獲得は False。
    assert wal.acquire_lock_atomic(layout, "second-holder") is False

    with pytest.raises(driver.OracleDriverError) as excinfo:
        _run(tmp_path, freeze_path, manifest_path, prepare_fn,
             _fake_evaluate_factory(), output_root=output_root,
             marker_root=tmp_path / "markers-lock")
    assert "campaign.lock" in str(excinfo.value)
    assert prepare_fn.calls == []


def test_v4_marker_fires_across_output_root_change(tmp_path):
    """V4: 実走済みマーカーが --output-root 非依存に発火し、別 output-root での再走を拒否。"""
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    marker_root = tmp_path / "freeze-side"

    # 1 回目: output-root A で完走。マーカーは marker_root (output-root 非依存) に残る。
    result_a = _run(
        tmp_path, freeze_path, manifest_path,
        _prepare_factory(), _fake_evaluate_factory(),
        output_root=tmp_path / "out-a", budget_path=tmp_path / "budget-a.json",
        marker_root=marker_root,
    )
    assert result_a["status"] == "completed"
    identity = s8b_run_marker.freeze_identity(freeze_path)
    assert s8b_run_marker.marker_exists(marker_root, identity)

    # 2 回目: 別 output-root・別 budget (WAL も lock も無い新出力先)。マーカーが
    # output-root 非依存で残るため再走を全拒否する。マーカーを output_root 配下に
    # 置く実装ならここは素通りしてしまう (迂回) — その変異を kill する。
    prepare_b = _prepare_factory()
    with pytest.raises(driver.OracleDriverError) as excinfo:
        _run(
            tmp_path, freeze_path, manifest_path,
            prepare_b, _fake_evaluate_factory(),
            output_root=tmp_path / "out-b", budget_path=tmp_path / "budget-b.json",
            marker_root=marker_root,
        )
    assert "マーカー" in str(excinfo.value)
    assert prepare_b.calls == []


def test_v5_truncated_wal_rejects_resume_even_with_zero_parseable_records(tmp_path):
    """V5: campaign-start 1 行だけの途中切断 WAL (parse 可能 record 0 件) でも拒否。

    read_records は末尾切れの 1 行を捨てて [] を返す。resume 判定を「parse 可能 record」
    でなく「byte の存在」で行うことで、この truncated WAL 迂回を閉じる (fail-closed)。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()

    output_root = tmp_path / "out"
    layout = campaign_layout(_campaign_id(manifest_path), output_root=str(output_root))
    layout.ensure()
    # campaign-start 1 行だけの途中切断 (JSON 未完 = parse 不能) を書き込む。
    with open(layout.wal_file, "w", encoding="utf-8") as stream:
        stream.write('{"variant":"oracle-session","stage":"s8b-oracle-session"')
    assert wal.read_records(layout) == []          # parse 可能 record 0 件
    assert os.path.getsize(layout.wal_file) > 0     # だが byte は存在する

    with pytest.raises(driver.OracleDriverError) as excinfo:
        _run(tmp_path, freeze_path, manifest_path, prepare_fn,
             _fake_evaluate_factory(), output_root=output_root,
             marker_root=tmp_path / "markers-v5")
    assert "WAL byte" in str(excinfo.value)
    assert prepare_fn.calls == []


# ===========================================================================
# W4: v2 実走 gate (承認束縛 active 世代) の実発火テスト (git fixture)
#
# build_valid_semantic_g1 (RV fixture) を拡張し、g1 世代 doc に per-pair floor +
# budget を充填し、floor_source を「binaries section を持つ floor artifact」に
# 差し替え、content-addressed store を out_root に組む。root=git repo で run_block を
# 実行し、gate (freeze==active 世代) / launch_validate / env 契約 / store 消費 /
# receipt / expected_perf_sha256 伝搬を実際に発火させる。
# ===========================================================================

_V2_GENERATORS = (
    "orchestrator/campaign/s1_direct_comparison.py",
    "orchestrator/campaign/s8b_oracle_report.py",
    "orchestrator/campaign/s8b_oracle_judge.py",
)


def _collect_source_paths(value, out: set) -> None:
    if isinstance(value, dict):
        path = value.get("path")
        if isinstance(path, str) and isinstance(value.get("sha256"), str):
            out.add(path)
        for child in value.values():
            _collect_source_paths(child, out)
    elif isinstance(value, list):
        for child in value:
            _collect_source_paths(child, out)


def _install_repo_sources(root: Path, freeze_document: dict) -> None:
    """gate (known_axes verify) と manifest (generator_versions) が repo root でも解決
    できるよう、known_axes freeze が参照する実 source + generator 実 source を複製する。

    複製先を .gitignore に載せ、launch_validate の search が untracked 複製を走査しない
    ようにする (verify は disk 直読みなので ignored でも sha 照合は成立する)。"""
    paths: set = set(_V2_GENERATORS)
    ka_rel = freeze_document["known_axes_freeze"]["path"]
    ka_doc = json.loads((ROOT / ka_rel).read_text(encoding="utf-8"))
    _collect_source_paths(ka_doc, paths)
    gitignore_lines = []
    for rel in sorted(paths):
        src = ROOT / rel
        if not src.is_file():
            continue
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        gitignore_lines.append(rel + "\n")
    (root / ".gitignore").write_text("".join(gitignore_lines), encoding="utf-8")


def _floor_artifact_and_store(document: dict, out_root: Path):
    """全 (holdout, configuration) cell 分の store bytes を out_root へ書き、floor artifact
    (binaries section) bytes と cell→binary_sha256 を返す。"""
    store_root = out_root / "env" / V2_ENV_TAG / "binaries"
    store_root.mkdir(parents=True, exist_ok=True)
    binaries: dict = {}
    for holdout_id in document["holdouts"]:
        for configuration_id in CONFIGURATIONS:
            content = f"perf-binary::{holdout_id}::{configuration_id}".encode("utf-8")
            sha = hashlib.sha256(content).hexdigest()
            (store_root / sha).write_bytes(content)
            binaries[f"{holdout_id}::{configuration_id}"] = {
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "binary_sha256": sha,
                "bin_hash_short": sha[:16],
                "store_path": f"env/{V2_ENV_TAG}/binaries/{sha}",
            }
    artifact = {"schema_version": "s8b-floor-result/v2", "binaries": binaries}
    return (json.dumps(artifact, ensure_ascii=False, sort_keys=True).encode("utf-8"),
            binaries)


def _build_v2_repo(tmp_path: Path, out_root: Path, *, mutate_floor_source=None):
    """承認束縛済み active v2 世代 (floor/budget 充填 + floor_source artifact + store) を
    git repo に組む。(root, freeze_path, gen_sha, binaries) を返す。"""
    if not REAL_FREEZE.is_file():
        pytest.fail("実 v1 freeze が無い (trust root 不在 — skip すると攻撃 matrix が緑化する。failures F9 型)")
    document = _real_document()
    v2_fixture.fill(document, total_bench_s=1000.0, per_holdout_bench_s=1000.0)
    floor_bytes, binaries = _floor_artifact_and_store(document, out_root)
    if mutate_floor_source is not None:
        floor_bytes = mutate_floor_source(floor_bytes, binaries)

    def fill_g1(g1):
        v2_fixture.fill(g1, total_bench_s=1000.0, per_holdout_bench_s=1000.0)

    root, gen_sha, gen_rel, _g1 = ratified_fixture.build_valid_semantic_g1(
        tmp_path, mutate_g1=fill_g1, floor_source_bytes=floor_bytes,
    )
    _install_repo_sources(root, document)
    return root, root / gen_rel, gen_sha, binaries


def _run_v2(root: Path, freeze_path: Path, manifest_path: Path, prepare_fn,
            evaluate_fn, *, out_root: Path, tmp_path: Path):
    """v2 実走 (承認束縛 gate/launch/env/store を実発火)。

    known_axes freeze の source provenance 検査だけは orthogonal な legacy 検査で、実 repo の
    external/ccbench submodule (この環境では未初期化) を要求するため tmp repo では成立しない。
    本レーンの検査対象 (v2 承認束縛 gate + launch_validate + env 契約 + store 消費) を分離する
    ため、この 1 検査だけ no-op に差し替える (ccbench 未初期化はこの環境の制約)。"""
    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None):
        return driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=root, output_root=out_root,
            budget_path=tmp_path / "v2-budget.json",
            marker_root=tmp_path / "v2-markers",
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )


def test_v2_gate_happy_path_completes_and_binds_env_store_receipt(tmp_path):
    """v2 正常系: freeze==active 世代 + launch_validate 成立 + store 全一致 →
    gate 通過・completed。expected_perf_sha256 が cell の store binary sha と一致して
    evaluate に伝搬し、clocks/numactl は env 契約由来 (NUMACTL ハードコード撤去)、
    campaign-start に execution receipt が記録される。"""
    out_root = tmp_path / "out"
    root, freeze_path, _gen_sha, binaries = _build_v2_repo(tmp_path, out_root)
    manifest_path, document = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    evaluate_fn = _fake_evaluate_factory()

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)

    assert result["status"] == "completed", result
    assert result["completed_trials"] == len(document["schedule"]["rows"])
    # expected_perf_sha256 が各 cell の store binary sha と一致して伝搬する。
    contract = ec.lookup(V2_ENV_TAG)
    for call in evaluate_fn.calls:
        assert call["clocks_per_us"] == contract.clocks_per_us  # env 契約由来
        assert call["kwargs"]["numactl"] == list(contract.numactl)  # NUMACTL 撤去
        assert call["kwargs"]["expected_perf_sha256"] in {
            rec["binary_sha256"] for rec in binaries.values()
        }
    # execution receipt が campaign-start に記録され manifest と整合する。
    start = next(e for e in result["events"] if e["event"] == "campaign-start")
    receipt = start["execution_receipt"]
    assert execution_guard.receipt_matches_contract(
        receipt, env_tag=V2_ENV_TAG, contract_sha256=contract.contract_sha256,
    )


def test_v2_freeze_bytes_not_active_generation_is_refused(tmp_path):
    """与えられた freeze bytes が active 世代と 1 byte でも違えば
    freeze-not-active-generation で拒否 (何も書かない)。"""
    out_root = tmp_path / "out"
    root, freeze_path, _gen_sha, _bin = _build_v2_repo(tmp_path, out_root)
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    # active 世代とは別 bytes の freeze を渡す (floor/budget は充填済み = v2 経路)。
    tampered = tmp_path / "tampered_freeze.json"
    doc = json.loads(freeze_path.read_text(encoding="utf-8"))
    doc["refreeze_note"] = str(doc.get("refreeze_note")) + " tampered"
    tampered.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    result = driver.run_block(
        manifest_path=manifest_path, block_id="b0", freeze_path=tampered,
        root=root, output_root=out_root, budget_path=tmp_path / "b.json",
        marker_root=tmp_path / "m", prepare_fn=_prepare_factory(),
        evaluate_fn=_fake_evaluate_factory(),
    )
    assert result["status"] == "refused"
    assert any(r.startswith("freeze-not-active-generation")
               for r in result["refusals"]), result["refusals"]


def test_v2_launch_validate_failure_is_refused(tmp_path):
    """launch_validate 失敗 (closure 外の未申告 hit) は v2-execution refusal に翻訳。"""
    out_root = tmp_path / "out"
    root, freeze_path, _gen_sha, _bin = _build_v2_repo(tmp_path, out_root)
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    # closure 外の untracked ファイルに rr80 params を仕込む → 未申告 hit で launch_validate 落ち。
    (root / "sneaky.txt").write_bytes(ratified_fixture._RR80_PARAMS)

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path)
    assert result["status"] == "refused"
    assert any("launch-validate" in r for r in result["refusals"]), result["refusals"]


def test_v2_launch_validate_non_ratified_error_is_refused(tmp_path):
    """launch_validate が RatifiedFreezeError 以外 (内部 _hf の git/os 走査由来の
    FreezeError 等) を投げても、stack trace を漏らさず v2-execution refusal に翻訳する
    (run_block の refusal 契約を破らない・fail-closed で何も書かない)。"""
    from campaign import s8b_holdout_freeze  # noqa: PLC0415

    out_root = tmp_path / "out"
    root, freeze_path, _gen_sha, _bin = _build_v2_repo(tmp_path, out_root)
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, _prepare_factory())

    def _boom(*_a, **_k):
        # _hf.search_repository / enumerate_repository_files が git/os 失敗を包む型。
        raise s8b_holdout_freeze.FreezeError("git enumerate 失敗 (模擬)")

    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate", _boom):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=root, output_root=out_root,
            budget_path=tmp_path / "v2-budget.json",
            marker_root=tmp_path / "v2-markers",
            prepare_fn=_prepare_factory(), evaluate_fn=_fake_evaluate_factory(),
        )

    assert result["status"] == "refused", result
    assert any("launch-validate" in r and "FreezeError" in r
               for r in result["refusals"]), result["refusals"]
    # fail-closed: run marker / WAL / budget を一切書いていない。
    assert not (tmp_path / "v2-budget.json").exists()
    assert not (tmp_path / "v2-markers").exists()


def test_v2_store_missing_is_refused(tmp_path):
    """store 実体が欠落していれば refusal (再ビルド fallback は書かない)。"""
    out_root = tmp_path / "out"
    root, freeze_path, _gen_sha, binaries = _build_v2_repo(tmp_path, out_root)
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    # 1 cell の store 実体を消す。
    victim = next(iter(binaries.values()))
    (out_root / victim["store_path"]).unlink()

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path)
    assert result["status"] == "refused"
    assert any("store 実体が無い" in r for r in result["refusals"]), result["refusals"]


def test_v2_store_hash_mismatch_is_refused(tmp_path):
    """store 実体の bytes が floor receipt の binary_sha256 と不一致なら refusal。"""
    out_root = tmp_path / "out"
    root, freeze_path, _gen_sha, binaries = _build_v2_repo(tmp_path, out_root)
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    victim = next(iter(binaries.values()))
    (out_root / victim["store_path"]).write_bytes(b"corrupted-binary-bytes")

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path)
    assert result["status"] == "refused"
    assert any("floor receipt と不一致" in r for r in result["refusals"]), \
        result["refusals"]


def test_v2_contract_sha256_mismatch_is_refused(tmp_path):
    """run_contract.contract_sha256 が env 契約 lookup 結果と不一致なら refusal。"""
    out_root = tmp_path / "out"
    root, freeze_path, _gen_sha, _bin = _build_v2_repo(tmp_path, out_root)
    manifest_path, document = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    # manifest の run_contract.contract_sha256 を別 64hex に差し替えて封を再作成する。
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    document["run_contract"]["contract_sha256"] = "1" * 64
    document["manifest_id"] = manifest_module._manifest_id(
        {k: v for k, v in document.items() if k != "manifest_id"})
    bad_manifest = tmp_path / "bad_manifest.json"
    bad_manifest.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")

    result = _run_v2(root, freeze_path, bad_manifest, _prepare_factory(),
                     _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path)
    # contract_sha256 改竄は manifest 検証 (freeze snapshot 不変) では捕まらず driver の
    # env 導出で捕捉されるか、あるいは manifest 検証段で捕捉される。いずれも refused。
    assert result["status"] == "refused", result


def test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome(tmp_path):
    """pipeline の bench-binary-mismatch abort (TOCTOU 第二防壁) が driver の
    binary-mismatch terminal outcome に射影される。"""
    out_root = tmp_path / "out"
    root, freeze_path, _gen_sha, _bin = _build_v2_repo(tmp_path, out_root)
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    evaluate_fn = _fake_abort_evaluate_factory("bench-binary-mismatch")

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)
    outcomes = [e["outcome"] for e in result["events"] if e["event"] == "trial-result"]
    assert outcomes and set(outcomes) == {"binary-mismatch"}, result
