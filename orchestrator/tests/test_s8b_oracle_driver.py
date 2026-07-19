# -*- coding: utf-8 -*-
"""8b oracle driver の gate、binding、budget、WAL 契約を検査する。"""
from __future__ import annotations

import ast
import contextlib
import copy
import dataclasses
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
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
from campaign import env_attestation  # noqa: E402
from campaign import execution_guard  # noqa: E402
from campaign import pipeline, s8b_budget, s8b_oracle_driver as driver, wal  # noqa: E402
from campaign import s8b_freeze_io  # noqa: E402
from campaign import s8b_materialization  # noqa: E402
from campaign import s8b_oracle_manifest as manifest_module  # noqa: E402
from campaign import s8b_oracle_report as report_module  # noqa: E402
from campaign import s8b_ratified_freeze  # noqa: E402
from campaign import s8b_run_marker  # noqa: E402
from campaign.layout import campaign_layout  # noqa: E402
from campaign.model import Genome  # noqa: E402
from campaign.s1_direct_comparison import PreparedCell  # noqa: E402
from test_schema_v2 import _valid_document as _valid_calibration_v2  # noqa: E402


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


def _source(path: str, *, root=ROOT) -> dict:
    source = Path(root) / path
    return {"path": path, "sha256": _sha256(source)}


def _write_manifest(tmp_path: Path, freeze_path: Path, prepare_fn,
                    *, source_root=ROOT, generator_paths=None,
                    contract=None) -> tuple[Path, dict]:
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
    if generator_paths is None:
        generator_paths = (
            "orchestrator/campaign/s1_direct_comparison.py",
            "orchestrator/campaign/s8b_oracle_report.py",
            "orchestrator/campaign/s8b_oracle_judge.py",
        )
    contract = contract or ec.lookup(V2_ENV_TAG)
    document = manifest_module.build_manifest(
        freeze_path=freeze_path,
        schedule=schedule,
        run_contract={
            "ccbench_pin": "fixture-pin", "env_tag": contract.env_tag,
            "clocks": contract.clocks_per_us, "reps": 5, "extime": 5,
            "verify": "legacy+s2", "screening": "off",
            "bench_max_rounds": 1,
            "contract_sha256": contract.contract_sha256,
        },
        binding_identity=bindings,
        campaign_ids={"b0": "s8b-oracle-fixture-b0"},
        allowed_excluded_reasons=["machine-failure"],
        generator_versions={
            role: _source(path, root=source_root)
            for role, path in zip(("materializer", "report", "judge"), generator_paths)
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
            "tps": [10.0, 11.0, 12.0, 13.0, 14.0], "median_tps": 12.0,
            "bench_wall_s": bench_wall_s,
        })
        wal.log(layout, variant, "commit", env_tag, {
            "fitness_tps": 12.0,
            "verify_configs": [pipeline.LEGACY_TAG, pipeline.S2_TAG],
        })
        return pipeline.EvalResult(
            genome=genome, variant=variant, certified=True, aborted=False,
            fitness_tps=12.0,
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


def _fake_launch_validated(freeze_path: Path, *, env_tag=None):
    """WAL/budget unit 用の LaunchValidatedFreeze 型境界 fixture。"""
    raw = Path(freeze_path).read_bytes()
    document = json.loads(raw)
    if env_tag is not None:
        document["env_tag"] = env_tag
    ratified = s8b_ratified_freeze.RatifiedFreeze(
        document=document, sha256=hashlib.sha256(raw).hexdigest(),
        generation_number=1, activation_head="f" * 40,
        generation_commit="e" * 40,
    )
    floor = s8b_ratified_freeze.VerifiedFloorArtifact(
        path="fixture/result.json", raw_bytes=b"{}",
        sha256=hashlib.sha256(b"{}").hexdigest(), document={},
    )
    return s8b_ratified_freeze.LaunchValidatedFreeze(
        ratified=ratified, activation_head=ratified.activation_head,
        search_digest="d" * 64, symlink_gitlink_inventory=(),
        floor_artifact=floor, binaries_by_cell={},
    )


def _required_contract(repo_root: Path):
    document = copy.deepcopy(_valid_calibration_v2())
    raw = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    artifact = repo_root / "calibration.json"
    artifact.write_bytes(raw)
    contract = ec.ExecutionEnvironmentContract(
        env_tag=document["env_tag"], clocks_per_us=document["clocks_per_us"],
        numactl=(), attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(
            path=artifact.name, sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    verified = env_attestation.load_verified_calibration(contract, repo_root)
    return contract, verified


def _reservation_env(*, requested_s: int = 100_000) -> dict[str, str]:
    started = time.time() - 10
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    return {
        "PBS_JOBID": "fixture.server",
        "IZANAGI_RESERVATION_JOB_ID": "fixture.server",
        "IZANAGI_RESERVATION_REQUESTED_S": str(requested_s),
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + requested_s),
        "IZANAGI_RESERVATION_HOST": "fixture-host",
        "IZANAGI_RESERVATION_BOOT_ID": boot_id,
        "IZANAGI_RESERVATION_SCRIPT_SHA256": "a" * 64,
        "IZANAGI_RESERVATION_NONCE": "fixture-nonce",
    }


def _durable_policy(path: Path):
    candidate = Path(path).absolute()
    approved = candidate
    while not approved.exists():
        approved = approved.parent
    return driver.DurableRootPolicy(
        approved_roots=(approved.resolve(),), forbidden_roots=(),
    )


def _run(tmp_path: Path, freeze_path: Path, manifest_path: Path,
         prepare_fn, evaluate_fn, *, output_root=None, budget_path=None,
         marker_root=None):
    # driver 内部の WAL/budget 契約テストは v2 gate/launch/store/env の実検査を迂回し、
    # future-approved gate + canned v2 plan を代入して WAL・budget・schedule 契約だけを
    # 突く (v2 gate/store/env の実発火は専用テストが git fixture で検査する)。
    validated = _fake_launch_validated(freeze_path)

    with mock.patch.object(
                driver, "_gate_check_validated",
                return_value=driver.GateDecision(True, [])), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "load_ratified_freeze",
                return_value=validated.ratified), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "launch_validate",
                return_value=validated), \
            mock.patch.object(driver, "_prepare_v2_execution", _canned_plan):
        return driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=output_root or (tmp_path / "out"),
            budget_path=budget_path or (tmp_path / "budget.json"),
            marker_root=marker_root or (tmp_path / "markers"),
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )


def _run_required_preflight(
        tmp_path: Path, *, receipt_issuer=None, verified_override=None,
        environ: dict[str, str] | None = None):
    """run_block production entry から required preflight を実発火する。"""
    contract, verified = _required_contract(tmp_path)
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, manifest_document = _write_manifest(
        tmp_path, freeze_path, prepare_fn, contract=contract,
    )
    verified_manifest = manifest_module.VerifiedManifest(
        document=manifest_document,
        sha256=manifest_module.manifest_sha256(manifest_document),
    )
    validated = _fake_launch_validated(freeze_path, env_tag=contract.env_tag)
    issuer = receipt_issuer
    if issuer is None:
        original = execution_guard.attest_and_build_receipt

        def issuer(receipt_contract, receipt_verified):
            return original(
                receipt_contract, receipt_verified,
                probe_fn=lambda: receipt_verified.attestation_profile,
            )

    env = _reservation_env() if environ is None else environ
    output_root = tmp_path / "required-out"
    budget_path = tmp_path / "required-budget.json"
    marker_root = tmp_path / "required-markers"
    with mock.patch.object(driver, "_gate_check_validated",
                           return_value=driver.GateDecision(True, [])), \
            mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze",
                              return_value=validated.ratified), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              return_value=validated), \
            mock.patch.object(driver, "verify_manifest", return_value=verified_manifest), \
            mock.patch.object(driver._env_contract, "lookup", return_value=contract), \
            mock.patch.object(driver, "MACHINE_ENV_TAG", contract.env_tag), \
            mock.patch.object(driver._env_attestation, "load_verified_calibration",
                              return_value=(verified_override or verified)), \
            mock.patch.object(driver.execution_guard, "attest_and_build_receipt",
                              side_effect=issuer), \
            mock.patch.dict(os.environ, env, clear=True):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=tmp_path, output_root=output_root, budget_path=budget_path,
            marker_root=marker_root, prepare_fn=prepare_fn,
            evaluate_fn=_fake_evaluate_factory(),
        )
    return result, output_root, budget_path, marker_root, contract, verified


def _required_plan(contract, verified, schedule, environ):
    original = execution_guard.attest_and_build_receipt
    receipt = original(
        contract, verified, probe_fn=lambda: verified.attestation_profile,
    )
    binding = driver._reservation.read_binding(environ)
    check = driver._reservation.check_reservation(
        binding, required_s=driver._reservation_required_s(schedule),
        safety_margin_s=driver.ORACLE_RESERVATION_SAFETY_MARGIN_S,
        environ=environ,
    )
    return driver._V2Plan(
        contract=contract, receipt=receipt,
        perf_sha_by_cell={
            (row["holdout_id"], row["configuration_id"]): "0" * 64
            for row in schedule
        },
        verified_calibration=verified, reservation_check=check,
    )


def _required_run_fixture(tmp_path: Path):
    contract, verified = _required_contract(tmp_path)
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, prepare_fn, contract=contract,
    )
    prepare_fn.calls.clear()
    validated = _fake_launch_validated(freeze_path, env_tag=contract.env_tag)
    verified_manifest = manifest_module.VerifiedManifest(
        document=document, sha256=manifest_module.manifest_sha256(document),
    )
    environ = _reservation_env()
    plan = _required_plan(contract, verified, document["schedule"]["rows"], environ)
    marker_root = tmp_path / "required-marker-root"
    marker_root.mkdir()
    output_root = tmp_path / "required-run-out"
    (output_root / "claims").mkdir(parents=True, mode=0o700)
    return {
        "root": tmp_path,
        "contract": contract, "verified": verified, "freeze_path": freeze_path,
        "manifest_path": manifest_path, "document": document,
        "prepare_fn": prepare_fn, "validated": validated,
        "verified_manifest": verified_manifest, "environ": environ, "plan": plan,
        "marker_root": marker_root, "output_root": output_root,
        "budget_path": tmp_path / "required-run-budget.json",
    }


def _run_required_fixture(fixture, *, receipt_side_effect=None, durable_policy=None):
    original_issuer = execution_guard.attest_and_build_receipt

    def default_issuer(contract, verified):
        return original_issuer(
            contract, verified, probe_fn=lambda: verified.attestation_profile,
        )

    issuer = receipt_side_effect or default_issuer
    with mock.patch.object(driver, "_gate_check_validated",
                           return_value=driver.GateDecision(True, [])), \
            mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze",
                              return_value=fixture["validated"].ratified), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              return_value=fixture["validated"]), \
            mock.patch.object(driver, "verify_manifest",
                              return_value=fixture["verified_manifest"]), \
            mock.patch.object(driver, "_prepare_v2_execution",
                              return_value=fixture["plan"]), \
            mock.patch.object(driver.execution_guard, "attest_and_build_receipt",
                              side_effect=issuer), \
            mock.patch.dict(os.environ, fixture["environ"], clear=True):
        return driver.run_block(
            manifest_path=fixture["manifest_path"], block_id="b0",
            freeze_path=fixture["freeze_path"], root=fixture["root"],
            output_root=fixture["output_root"], budget_path=fixture["budget_path"],
            marker_root=fixture["marker_root"], prepare_fn=fixture["prepare_fn"],
            evaluate_fn=_fake_evaluate_factory(),
            durable_root_policy=(durable_policy
                                 or _durable_policy(fixture["output_root"])),
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


def _assert_required_refusal_has_zero_side_effects(result, output_root, budget_path,
                                                    marker_root):
    assert result["status"] == "refused" and result["allowed"] is False, result
    assert not output_root.exists()
    assert not budget_path.exists()
    assert not marker_root.exists()


def test_required_binding_missing_refuses_at_production_entry_without_side_effects(tmp_path):
    result, out, budget, markers, _contract, _verified = _run_required_preflight(
        tmp_path, environ={},
    )
    _assert_required_refusal_has_zero_side_effects(result, out, budget, markers)
    assert "reservation binding" in result["refusals"][0]


def test_required_v1_receipt_refuses_at_production_entry_without_side_effects(tmp_path):
    def v1_issuer(contract, _verified):
        return execution_guard.build_receipt(contract)

    result, out, budget, markers, _contract, _verified = _run_required_preflight(
        tmp_path, receipt_issuer=v1_issuer,
    )
    _assert_required_refusal_has_zero_side_effects(result, out, budget, markers)
    assert "receipt" in result["refusals"][0]


def test_required_verified_calibration_from_other_contract_is_refused_without_side_effects(
        tmp_path):
    _contract, verified = _required_contract(tmp_path)
    wrong_verified = dataclasses.replace(verified, sha256="b" * 64)
    result, out, budget, markers, _contract, _verified = _run_required_preflight(
        tmp_path, verified_override=wrong_verified,
    )
    _assert_required_refusal_has_zero_side_effects(result, out, budget, markers)
    assert "verified calibration" in result["refusals"][0]


def test_required_secondary_calibration_identity_recheck_fires_with_monkeypatched_loader(
        tmp_path):
    contract, verified = _required_contract(tmp_path)
    assert verified.calibration is not None
    drifted = dataclasses.replace(
        verified,
        calibration=dataclasses.replace(verified.calibration, env_tag="drifted-env"),
    )
    result, out, budget, markers, _contract, _verified = _run_required_preflight(
        tmp_path, verified_override=drifted,
    )
    _assert_required_refusal_has_zero_side_effects(result, out, budget, markers)
    assert "別 contract" in result["refusals"][0]


def test_required_missing_preprovisioned_oracle_claim_root_is_fail_closed(tmp_path):
    fixture = _required_run_fixture(tmp_path)
    (fixture["output_root"] / "claims").rmdir()
    before = _tree_file_snapshot(fixture["output_root"])

    result = _run_required_fixture(fixture)

    assert result["status"] == "refused" and result["allowed"] is False
    assert "provisioning" in result["refusals"][0]
    assert _tree_file_snapshot(fixture["output_root"]) == before
    assert not fixture["budget_path"].exists()


def test_required_oracle_claim_root_outside_durable_approval_is_fail_closed(tmp_path):
    fixture = _required_run_fixture(tmp_path)
    unrelated = tmp_path / "unrelated-approved-root"
    unrelated.mkdir()
    policy = driver.DurableRootPolicy(
        approved_roots=(unrelated.resolve(),), forbidden_roots=(),
    )
    before = _tree_file_snapshot(fixture["output_root"])

    result = _run_required_fixture(fixture, durable_policy=policy)

    assert result["status"] == "refused" and result["allowed"] is False
    assert "approved root" in result["refusals"][0]
    assert _tree_file_snapshot(fixture["output_root"]) == before
    assert not fixture["budget_path"].exists()


def test_required_existing_claim_refuses_production_entry_without_new_side_effects(tmp_path):
    fixture = _required_run_fixture(tmp_path)
    identity = driver._execution_identity(fixture["plan"])
    driver._acquire_g12_claim(
        plan=fixture["plan"], claim_root=fixture["output_root"] / "claims",
        manifest_sha256=fixture["verified_manifest"].sha256,
        freeze_sha256=fixture["validated"].ratified.sha256,
        schedule_sha256=fixture["document"]["schedule_sha256"],
        campaign_id=fixture["document"]["campaign_ids"]["b0"], identity=identity,
    )
    before = _tree_file_snapshot(fixture["output_root"])

    result = _run_required_fixture(fixture)

    assert result["status"] == "refused" and result["allowed"] is False
    assert "claim" in result["refusals"][0]
    assert _tree_file_snapshot(fixture["output_root"]) == before
    assert not fixture["budget_path"].exists()


def test_required_recheck_real_reservation_shortfall_writes_aborted_terminal(tmp_path):
    fixture = _required_run_fixture(tmp_path)
    fixture["plan"].reservation_check = dataclasses.replace(
        fixture["plan"].reservation_check,
        monotonic_deadline=time.monotonic() + 1.0,
    )
    result = _run_required_fixture(fixture)

    assert result["status"] == "error"
    deviation = next(event for event in result["events"] if event["event"] == "deviation")
    assert deviation["kind"] == "execution-guard-lost"
    assert "reservation" in deviation["message"]
    terminals = [event for event in result["events"]
                 if event["event"] == "campaign-terminal"]
    assert len(terminals) == 1
    assert terminals[0]["status"] == "aborted"
    assert terminals[0]["completed_rows"] == 0
    assert terminals[0]["scheduled_rows"] == len(fixture["document"]["schedule"]["rows"])


def test_required_recheck_real_receipt_validation_catches_midcampaign_drift(tmp_path):
    fixture = _required_run_fixture(tmp_path)
    valid = execution_guard.attest_and_build_receipt(
        fixture["contract"], fixture["verified"],
        probe_fn=lambda: fixture["verified"].attestation_profile,
    )
    drifted = copy.deepcopy(valid)
    drifted["contract_sha256"] = "0" * 64

    result = _run_required_fixture(
        fixture, receipt_side_effect=mock.Mock(return_value=drifted),
    )

    assert result["status"] == "error"
    deviation = next(event for event in result["events"] if event["event"] == "deviation")
    assert deviation["kind"] == "execution-guard-lost"
    assert "attestation receipt" in deviation["message"]
    terminal = result["events"][-1]
    assert terminal["event"] == "campaign-terminal"
    assert terminal["status"] == "aborted" and terminal["completed_rows"] == 0


def test_two_real_subprocess_oracle_submissions_only_one_acquires_g12_claim(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    shared_out_root = tmp_path / "shared-oracle-output-root"
    claim_root = shared_out_root / "claims"
    claim_root.mkdir(parents=True)
    marker_root = tmp_path / "shared-oracle-marker-root"
    marker_root.mkdir()
    script = textwrap.dedent(
        f"""
        import dataclasses, hashlib, json, sys, time
        from pathlib import Path
        from unittest import mock
        sys.path.insert(0, {str(ORCHESTRATOR)!r})
        from campaign import env_contract, execution_guard
        from campaign.durable_root import DurableRootPolicy
        from campaign import s8b_oracle_driver as driver
        from campaign import s8b_oracle_manifest, s8b_ratified_freeze

        freeze_path = Path({str(freeze_path)!r})
        raw = freeze_path.read_bytes()
        ratified = s8b_ratified_freeze.RatifiedFreeze(
            document=json.loads(raw), sha256=hashlib.sha256(raw).hexdigest(),
            generation_number=1, activation_head="f" * 40, generation_commit="e" * 40)
        floor = s8b_ratified_freeze.VerifiedFloorArtifact(
            path="fixture/result.json", raw_bytes=b"{{}}",
            sha256=hashlib.sha256(b"{{}}").hexdigest(), document={{}})
        validated = s8b_ratified_freeze.LaunchValidatedFreeze(
            ratified=ratified, activation_head=ratified.activation_head,
            search_digest="d" * 64, symlink_gitlink_inventory=(),
            floor_artifact=floor, binaries_by_cell={{}})
        manifest = json.loads(Path({str(manifest_path)!r}).read_bytes())
        verified_manifest = s8b_oracle_manifest.VerifiedManifest(
            document=manifest, sha256=s8b_oracle_manifest.manifest_sha256(manifest))
        base = env_contract.lookup("linux-baremetal")
        required = dataclasses.replace(
            base, attestation_mode="required",
            isolation_policy=env_contract.IsolationPolicy(
                single_process=True, allow_resume=False))
        plan = driver._V2Plan(
            contract=required, receipt=execution_guard.build_receipt(required),
            perf_sha_by_cell={{}})

        def won_claim_then_stop(*_args, **_kwargs):
            time.sleep(0.25)
            raise driver.OracleDriverError("fixture stop after global claim")

        try:
            with mock.patch.object(driver, "_gate_check_validated",
                                   return_value=driver.GateDecision(True, [])), \
                    mock.patch.object(driver.s8b_ratified_freeze,
                                      "load_ratified_freeze", return_value=ratified), \
                    mock.patch.object(driver.s8b_ratified_freeze,
                                      "launch_validate", return_value=validated), \
                    mock.patch.object(driver, "verify_manifest",
                                      return_value=verified_manifest), \
                    mock.patch.object(driver, "_prepare_v2_execution",
                                      return_value=plan), \
                    mock.patch.object(driver, "_ensure_campaign",
                                      side_effect=won_claim_then_stop):
                result = driver.run_block(
                    manifest_path={str(manifest_path)!r}, block_id="b0",
                    freeze_path={str(freeze_path)!r}, root={str(ROOT)!r},
                    output_root={str(shared_out_root)!r},
                    budget_path={str(tmp_path / 'subprocess-budget.json')!r},
                    marker_root={str(marker_root)!r},
                    durable_root_policy=DurableRootPolicy(
                        approved_roots=(Path({str(shared_out_root)!r}).resolve(),),
                        forbidden_roots=()))
            print(json.dumps(result, sort_keys=True))
        except driver.OracleDriverError as exc:
            print(json.dumps({{"status": "claim-won", "error": str(exc)}}, sort_keys=True))
        """
    )
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        for _ in range(2)
    ]
    results = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stderr
        results.append(json.loads(stdout))

    assert sorted(result["status"] for result in results) == ["claim-won", "refused"]
    assert len(list(claim_root.glob("*.claim"))) == 1


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


def test_active_resolution_and_manifest_structure_refusals_are_aggregated(tmp_path):
    """active 解決失敗時も独立 manifest 構造検査の refusal を落とさない。"""
    freeze_path = _floor_only_freeze(tmp_path)
    manifest_freeze = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, manifest_freeze, prepare_fn)
    prepare_fn.calls.clear()
    document["unexpected_top_level_key"] = True
    manifest_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    evaluate_fn = _fake_evaluate_factory()
    output_root = tmp_path / "aggregate-refused-out"
    budget_path = tmp_path / "aggregate-refused-budget.json"

    result = driver.run_block(
        manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
        root=ROOT, output_root=output_root, budget_path=budget_path,
        prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
    )

    assert result["status"] == "refused" and result["allowed"] is False
    assert len(result["refusals"]) == 2, result["refusals"]
    assert any(reason.startswith("freeze-ratify:") for reason in result["refusals"])
    assert any(reason.startswith("manifest-verify:") for reason in result["refusals"])
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
    ), "campaign-terminal"]
    terminal = result["events"][-1]
    assert terminal["status"] == "completed"
    assert terminal["scheduled_rows"] == terminal["completed_rows"] == len(
        document["schedule"]["rows"]
    )
    assert set(terminal["execution_identity"]) == {
        "job", "host", "boot", "pid", "starttime",
    }
    assert len(evaluate_fn.calls) == len(document["schedule"]["rows"])
    for call in evaluate_fn.calls:
        kwargs = call["kwargs"]
        assert kwargs["do_bench"] is True
        assert kwargs["screening"] is None
        assert kwargs["env_contract"] is ec.lookup(V2_ENV_TAG)
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
        25.0 * len(document["schedule"]["rows"])
    )
    assert not list((tmp_path / "markers").glob("*.claim"))  # mode=none 回帰


def test_campaign_terminal_driver_guard_rejects_second_terminal(tmp_path):
    layout = campaign_layout("oracle-terminal-double", output_root=str(tmp_path)).ensure()
    identity = {
        "job": "j", "host": "h", "boot": "b", "pid": 1, "starttime": 2,
    }
    driver._append_campaign_terminal(
        layout, V2_ENV_TAG, status="completed", scheduled_rows=1,
        completed_rows=1, execution_identity=identity,
    )
    with pytest.raises(driver.OracleDriverError, match="二重"):
        driver._append_campaign_terminal(
            layout, V2_ENV_TAG, status="aborted", scheduled_rows=1,
            completed_rows=0, execution_identity=identity,
        )
    terminals = [event for event in driver._session_events(layout)
                 if event["event"] == "campaign-terminal"]
    assert len(terminals) == 1 and terminals[0]["status"] == "completed"


def test_oracle_pipeline_contract_keyword_is_mandatory_positive_control(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    base = _fake_evaluate_factory()

    def requires_contract(genome, layout, env_tag, ccbench_commit, perf,
                          clocks_per_us, *, env_contract, **kwargs):
        assert env_contract is ec.lookup(V2_ENV_TAG)
        return base(
            genome, layout, env_tag, ccbench_commit, perf, clocks_per_us,
            env_contract=env_contract, **kwargs,
        )

    result = _run(
        tmp_path, freeze_path, manifest_path, prepare_fn, requires_contract,
    )
    assert result["status"] == "completed"


def test_build_result_contract_mismatch_aborts_campaign_before_measurement(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    guard_failures = []

    def fake_evaluate(genome, *_args, **_kwargs):
        # driver の production evaluate 境界内で build_v2 result guard を発火する。
        try:
            pipeline.buildcache.build_v2()
        except AssertionError as exc:
            guard_failures.append(str(exc))
            raise
        raise AssertionError("contract guard did not reject")

    wrong = pipeline.buildcache.BuildResult(
        genome=Genome("silo", {}), trace=True, binary="/tmp/not-run",
        bin_sha256="0" * 64, build_dir="/tmp/not-run", cached=True,
        contract_sha256="f" * 64,
    )
    with mock.patch.object(pipeline.buildcache, "build_v2", return_value=wrong):
        result = _run(
            tmp_path, freeze_path, manifest_path, prepare_fn, fake_evaluate,
        )

    assert result["status"] == "error"
    assert guard_failures and "BuildResult.contract_sha256" in guard_failures[0]
    terminal = next(event for event in result["events"]
                    if event["event"] == "campaign-terminal")
    assert terminal["status"] == "aborted"
    assert terminal["completed_rows"] == 0


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
        "campaign-start", "budget-exhausted-before-attempt", "campaign-terminal",
    ]
    assert events[-1]["status"] == "aborted"
    assert events[-1]["scheduled_rows"] == len(document["schedule"]["rows"])
    assert events[-1]["completed_rows"] == 0
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
        25.0 * len(document["schedule"]["rows"])
    )
    assert ledger["entries"] == []


def test_reservation_envelope_exceeded_is_fail_closed(tmp_path):
    """実測 bench が予約枠を超過したら fail-closed で error に倒す (protocol violation)。

    reservation 枠 = 行数×(extime×reps×rounds)=行数×25。1 行目の実測 26 で単 holdout 枠
    (6 行×25=150) は超えないが、全 12 行を 26 で回すと総枠 300 を超える経路がある。ここでは
    per-holdout 枠超過 (h の 6 行×26=156 > 予約 150) を fixture で発火させる。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    # 各 trial の実測 bench_wall_s=26 > per-row 予約 25。holdout 枠 (6 行×25=150) を
    # 同一 holdout の 6 行目 (実測累計 156) で超える。
    evaluate_fn = _fake_evaluate_factory(bench_wall_s=26.0)

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
    assert events[-2:] == ["protocol-violation", "campaign-terminal"]
    terminal = result["events"][-1]
    assert terminal["status"] == "aborted"
    assert terminal["completed_rows"] == 0
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
        from pathlib import Path
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

        freeze_raw = Path({str(freeze_path)!r}).read_bytes()
        ratified = s8b_ratified_freeze.RatifiedFreeze(
            document=json.loads(freeze_raw),
            sha256=hashlib.sha256(freeze_raw).hexdigest(), generation_number=1,
            activation_head="f" * 40, generation_commit="e" * 40)
        floor = s8b_ratified_freeze.VerifiedFloorArtifact(
            path="fixture/result.json", raw_bytes=b"{{}}",
            sha256=hashlib.sha256(b"{{}}").hexdigest(), document={{}})
        validated = s8b_ratified_freeze.LaunchValidatedFreeze(
            ratified=ratified, activation_head=ratified.activation_head,
            search_digest="d" * 64, symlink_gitlink_inventory=(),
            floor_artifact=floor, binaries_by_cell={{}})

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
                driver, "_gate_check_validated",
                return_value=driver.GateDecision(True, [])), \\
             mock.patch.object(driver.s8b_ratified_freeze,
                               "load_ratified_freeze", return_value=ratified), \\
             mock.patch.object(driver.s8b_ratified_freeze,
                               "launch_validate", return_value=validated), \\
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


def test_run_block_reuses_launch_validated_and_legacy_loader_is_dead(tmp_path):
    """同一 LaunchValidatedFreeze を gate / plan へ渡し、旧 loader は呼ばない。"""
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

    validated = _fake_launch_validated(freeze_path)
    captured: dict = {}

    def recording_gate(*, freeze_path, manifest_path, root, verified=None,
                       verified_manifest=None, launch_validated=None,
                       ratified=None, ratified_error=None):
        captured["launch_validated"] = launch_validated
        captured["verified_manifest"] = verified_manifest
        return driver.GateDecision(True, [])

    def recording_plan(**kwargs):
        captured["plan_validated"] = kwargs["validated"]
        return _canned_plan(**kwargs)

    with mock.patch.object(Path, "read_bytes", counting_read_bytes), \
            mock.patch.object(
                driver, "_load_verified_freeze",
                side_effect=AssertionError("legacy freeze loader called")), \
            mock.patch.object(
                driver._freeze_io, "load_verified_freeze",
                side_effect=AssertionError("legacy freeze leaf loader called")), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "load_ratified_freeze",
                              return_value=validated.ratified), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "launch_validate", return_value=validated), \
            mock.patch.object(driver, "_prepare_v2_execution", recording_plan), \
            mock.patch.object(driver, "_gate_check_validated", recording_gate):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=tmp_path / "out", budget_path=tmp_path / "budget.json",
            marker_root=tmp_path / "markers",
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "completed"
    # freeze_path は active bytes hash 照合 1 回だけ。document は別 loader で読まない。
    assert len(freeze_reads) == 1
    assert captured["launch_validated"] is validated
    assert captured["plan_validated"] is validated
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
    validated = _fake_launch_validated(freeze_path)

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
                       verified_manifest=None, launch_validated=None,
                       ratified=None, ratified_error=None):
        captured["gate_manifest"] = verified_manifest
        return driver.GateDecision(True, [])

    with mock.patch.object(Path, "read_text", counting_read_text), \
            mock.patch.object(driver, "verify_manifest", counting_verify), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "load_ratified_freeze",
                              return_value=validated.ratified), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "launch_validate", return_value=validated), \
            mock.patch.object(driver, "_prepare_v2_execution", _canned_plan), \
            mock.patch.object(driver, "_gate_check_validated", recording_gate):
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
    """layer3_schema.json の runs 定義で bench_wall_s の型と非必須性を構造として pin する。layer3_report._validate_schema / build_report は呼ばない。"""
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
# E3a の production-emitter fixture が生成した official result bytes と store をそのまま
# 使い、gate / launch_validate / env 契約 / store 消費 / receipt 伝搬を発火させる。
# ===========================================================================

def _build_v2_repo(tmp_path: Path, *, floor_extime_s: int = 5):
    """E3a production-emitter bytes から oracle 実走 fixture を返す。"""
    def fill_execution_snapshot(g1):
        v2_fixture.fill(
            g1, total_bench_s=1000.0, per_holdout_bench_s=1000.0,
        )

    mutate = None
    if floor_extime_s != 5:
        def mutate(state):
            # production emitter が正式 bytes を生成した後の protocol だけを変更する。
            # raw hash と generation record は emitter 自身が再構築するため、static
            # ratified loader は通り、full launch validation の数値 pin だけを攻撃できる。
            state["protocol"]["extime_s"] = floor_extime_s

    root, ratified, topology = ratified_fixture.load_emitter_g1(
        tmp_path, mutate=mutate, mutate_g1=fill_execution_snapshot,
    )
    return (
        root, root / topology["generation_path"], ratified.sha256,
        topology["result"]["binaries"], topology,
    )


def _emitter_manifest(tmp_path: Path, root: Path, freeze_path: Path):
    freeze = json.loads(freeze_path.read_bytes())
    generator_paths = (
        freeze["design_source"]["path"], freeze["generator"]["path"],
        freeze["known_axes_freeze"]["path"],
    )
    with mock.patch.object(manifest_module, "ROOT", root):
        return _write_manifest(
            tmp_path, freeze_path, _prepare_factory(), source_root=root,
            generator_paths=generator_paths,
        )


def _tree_file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in root.rglob("*") if path.is_file()
    }


def _v2_refusal_reason(result: dict) -> str:
    assert result["status"] == "refused", result
    assert len(result["refusals"]) == 1, result["refusals"]
    prefix = "v2-execution: ["
    refusal = result["refusals"][0]
    assert refusal.startswith(prefix) and "]" in refusal[len(prefix):], refusal
    return refusal[len(prefix):].split("]", 1)[0]


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


def _assert_extime_launch_refusal(decision):
    assert not decision.allowed
    assert len(decision.refusals) == 1
    refusal = decision.refusals[0]
    assert refusal.startswith("v2-execution: launch-validate:")
    assert "protocol.extime_s" in refusal
    assert "受領 3" in refusal and "承認 5" in refusal


def test_v2_standalone_gate_check_requires_full_floor_validation(tmp_path):
    """standalone v2 gate は self-load / injected static freeze を full validate する。"""
    real_load = driver.s8b_ratified_freeze.load_ratified_freeze
    real_launch = driver.s8b_ratified_freeze.launch_validate

    valid_root, valid_freeze, _sha, _bins, _topology = _build_v2_repo(
        tmp_path / "valid", floor_extime_s=5,
    )
    load_results = []
    launch_calls = []

    def recording_load(root):
        loaded = real_load(root)
        load_results.append(loaded)
        return loaded

    def recording_launch(candidate, root):
        launch_calls.append((candidate, root))
        return real_launch(candidate, root)

    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None), \
            mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze",
                              side_effect=recording_load), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              side_effect=recording_launch):
        valid = driver.gate_check(freeze_path=valid_freeze, root=valid_root)
    assert valid.allowed, valid.refusals
    assert len(load_results) == 1 and len(launch_calls) == 1
    assert launch_calls[0][0] is load_results[0]
    assert launch_calls[0][1] == valid_root

    bad_root, bad_freeze, _sha, _bins, _topology = _build_v2_repo(
        tmp_path / "bad", floor_extime_s=3,
    )
    load_results.clear()
    launch_calls.clear()
    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None), \
            mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze",
                              side_effect=recording_load), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              side_effect=recording_launch):
        bad_self_load = driver.gate_check(
            freeze_path=bad_freeze, root=bad_root,
        )
    _assert_extime_launch_refusal(bad_self_load)
    assert len(load_results) == 1 and len(launch_calls) == 1
    assert launch_calls[0][0] is load_results[0]
    assert launch_calls[0][1] == bad_root

    injected = real_load(bad_root)
    launch_calls.clear()
    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "load_ratified_freeze",
                side_effect=AssertionError("injected RatifiedFreeze を再 load した")), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              side_effect=recording_launch):
        bad_injected = driver.gate_check(
            freeze_path=bad_freeze, root=bad_root, ratified=injected,
        )
    _assert_extime_launch_refusal(bad_injected)
    assert launch_calls == [(injected, bad_root)]


def test_private_validated_gate_has_only_run_block_as_production_caller():
    """public gate に validated bypass を再導入せず、private caller を本線だけに固定。"""
    assert "launch_validated" not in inspect.signature(driver.gate_check).parameters
    tree = ast.parse(inspect.getsource(driver))
    callers = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "_gate_check_validated"
                for child in ast.walk(node)):
            callers.append(node.name)
    assert callers == ["run_block"]


def test_v2_gate_happy_path_completes_and_binds_env_store_receipt(tmp_path):
    """v2 正常系: freeze==active 世代 + launch_validate 成立 + store 全一致 →
    gate 通過・completed。expected_perf_sha256 が cell の store binary sha と一致して
    evaluate に伝搬し、clocks/numactl は env 契約由来 (NUMACTL ハードコード撤去)、
    campaign-start に execution receipt が記録される。"""
    root, freeze_path, _gen_sha, binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
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
        attestation_mode="none",
    )


def test_v2_completed_driver_campaign_is_accepted_by_report(tmp_path):
    """driver の completed WAL は report で 5 個の bench 証拠として読める。"""
    root, freeze_path, _gen_sha, _binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
    result = _run_v2(
        root, freeze_path, manifest_path, _prepare_factory(),
        _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path,
    )
    assert result["status"] == "completed", result

    observations_path = tmp_path / "observations.json"
    assert report_module.main([
        "report", "--manifest", str(manifest_path),
        "--output-root", str(out_root), "--out", str(observations_path),
    ]) == 0
    observations = json.loads(observations_path.read_bytes())
    assert len(observations["rows"]) == len(document["schedule"]["rows"])
    assert all(row["status"] == "completed" for row in observations["rows"])
    assert all(row["bench_values"] == [10.0, 11.0, 12.0, 13.0, 14.0]
               for row in observations["rows"])


@pytest.mark.skipif(
    not ((ROOT / "external" / "ccbench" / ".git").exists()
         and all(shutil.which(tool) for tool in ("cmake", "gcc-13", "g++-13", "nm"))),
    reason="slow oracle real-build v2 control: initialized ccbench + pinned toolchain が必要",
)
def test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2(tmp_path):
    """oracle evaluate 境界で fake build を使わず trace/perf の実 build_v2 を通す。"""
    from test_campaign import _green_vr  # 局所 import: verifier fixture のみ共有

    freeze = _real_document()
    holdout_id = next(iter(freeze["holdouts"]))
    configuration_id = "stock_common"
    pin = subprocess.run(
        ["git", "-C", str(ROOT / "external" / "ccbench"), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    contract = ec.lookup(V2_ENV_TAG)
    built = []
    real_build_v2 = pipeline.buildcache.build_v2

    def recording_build_v2(*args, **kwargs):
        result = real_build_v2(*args, **kwargs)
        built.append(result)
        return result

    with driver._prepared_binding(
            freeze=freeze, holdout_id=holdout_id,
            configuration_id=configuration_id, ccbench_pin=pin,
            prepare_fn=driver.prepare_cell) as (_identity, prepared), \
            mock.patch.object(pipeline.buildcache, "build_v2", recording_build_v2), \
            mock.patch.object(pipeline, "_run_trace", return_value=(1, 0, 1)), \
            mock.patch.object(pipeline, "verify_trace_dir", side_effect=lambda _p: _green_vr()), \
            driver._assert_v2_build_contract(contract):
        layout = campaign_layout(
            "oracle-real-v2-build-control", output_root=str(tmp_path / "wal"),
        ).ensure()
        result = pipeline.evaluate(
            prepared.genome, layout, contract.env_tag, pin,
            pipeline.PerfConfig(records=1000, threads=2),
            contract.clocks_per_us, do_bench=False,
            src_token=prepared.src_token, ccbench_dir=prepared.ccbench_dir,
            cache_root=str(tmp_path / "cache"), env_contract=contract,
            log=lambda _message: None,
        )

    assert result.certified and not result.aborted
    assert len(built) == 2 and {item.trace for item in built} == {False, True}
    assert all(Path(item.binary).is_file() for item in built)
    assert all(item.contract_sha256 == contract.contract_sha256 for item in built)
    assert all(Path(item.ccbench_root) == Path(prepared.ccbench_dir).absolute()
               for item in built)


def test_v2_floor_disk_swap_after_launch_uses_same_validated_object(tmp_path):
    """launch 後の floor disk 差替えを無視し、旧 blob reader も呼ばない。"""
    root, freeze_path, _gen_sha, _binaries, topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    result_path = root / topology["paths"]["result"]
    original_raw = result_path.read_bytes()
    real_launch = driver.s8b_ratified_freeze.launch_validate
    real_prepare = driver._prepare_v2_execution
    captured = {}

    def launch_then_swap(ratified, launch_root):
        validated = real_launch(ratified, launch_root)
        captured["launched"] = validated
        result_path.write_bytes(b'{"poisoned-after-launch":true}\n')
        return validated

    def record_prepare(**kwargs):
        captured["consumed"] = kwargs["validated"]
        return real_prepare(**kwargs)

    with mock.patch.object(
            driver.s8b_ratified_freeze, "launch_validate", launch_then_swap), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "read_floor_source_blob",
                side_effect=AssertionError("legacy floor blob reader called")), \
            mock.patch.object(driver, "_prepare_v2_execution", record_prepare):
        result = _run_v2(
            root, freeze_path, manifest_path, _prepare_factory(),
            _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path,
        )

    assert result["status"] == "completed", result
    assert captured["consumed"] is captured["launched"]
    assert captured["launched"].floor_artifact.raw_bytes == original_raw
    assert result_path.read_bytes() != original_raw


def test_v2_freeze_bytes_not_active_generation_is_refused(tmp_path):
    """与えられた freeze bytes が active 世代と 1 byte でも違えば
    freeze-not-active-generation で拒否 (何も書かない)。"""
    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
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
    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
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

    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)

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
    root, freeze_path, _gen_sha, binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    baseline = s8b_ratified_freeze.launch_validate(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    assert isinstance(baseline, s8b_ratified_freeze.LaunchValidatedFreeze)
    # 1 cell の store 実体を消す。
    victim = next(iter(binaries.values()))
    (out_root / victim["store_path"]).unlink()
    before = _tree_file_snapshot(out_root)
    prepare_fn = _prepare_factory()
    evaluate_fn = _fake_evaluate_factory()

    result = _run_v2(root, freeze_path, manifest_path, prepare_fn,
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)
    assert _v2_refusal_reason(result) == "store-missing"
    assert _tree_file_snapshot(out_root) == before
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not (tmp_path / "v2-budget.json").exists()
    assert not (tmp_path / "v2-markers").exists()


def test_v2_store_hash_mismatch_is_refused(tmp_path):
    """store 実体の bytes が floor receipt の binary_sha256 と不一致なら refusal。"""
    root, freeze_path, _gen_sha, binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    baseline = s8b_ratified_freeze.launch_validate(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    assert isinstance(baseline, s8b_ratified_freeze.LaunchValidatedFreeze)
    victim = next(iter(binaries.values()))
    (out_root / victim["store_path"]).write_bytes(b"corrupted-binary-bytes")
    before = _tree_file_snapshot(out_root)
    prepare_fn = _prepare_factory()
    evaluate_fn = _fake_evaluate_factory()

    result = _run_v2(root, freeze_path, manifest_path, prepare_fn,
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)
    assert _v2_refusal_reason(result) == "store-hash-mismatch"
    assert _tree_file_snapshot(out_root) == before
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not (tmp_path / "v2-budget.json").exists()
    assert not (tmp_path / "v2-markers").exists()


def test_v2_contract_sha256_mismatch_is_refused(tmp_path):
    """run_contract.contract_sha256 が env 契約 lookup 結果と不一致なら refusal。"""
    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
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
    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    evaluate_fn = _fake_abort_evaluate_factory("bench-binary-mismatch")

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)
    outcomes = [e["outcome"] for e in result["events"] if e["event"] == "trial-result"]
    assert outcomes and set(outcomes) == {"binary-mismatch"}, result
