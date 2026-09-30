# -*- coding: utf-8 -*-
"""T-126 single-process FSM、driver 順序、exact pipeline opt-in を検査する。"""
from __future__ import annotations

import ast
import sys
import os
import json
import hashlib
import math
import statistics
import select
import signal
import subprocess
import time
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1]))

import test_campaign as campaign_fixtures  # noqa: E402
from orchestrator.calibrator import effective_clock_policy, schema_v2  # noqa: E402
from orchestrator.campaign import env_attestation, env_contract, pipeline  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    BuildProvenance,
    GeneratorId,
    build_run_context,
)
from orchestrator.campaign.calibration_verify import VerifiedCalibration  # noqa: E402
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.qualification.artifacts import (  # noqa: E402
    QualificationArtifactError,
    QualificationEventSink,
    QualificationLayout,
    QualificationRoot,
    create_attempt,
    load_jsonl_strict,
    validate_member_evidence,
)
from orchestrator.qualification.contract import load_protocol  # noqa: E402
from orchestrator.qualification.contract import (  # noqa: E402
    RESERVATION_POLICY_RELATIVE_PATH,
)
from orchestrator.qualification.series import SeriesFSM, SeriesStateError, replay_ledger  # noqa: E402
from orchestrator.qualification.t126_driver import (  # noqa: E402
    ActiveProcessGroups,
    AttestationError,
    MemberRunError,
    RC_ATTESTATION,
    MonotonicEnvelope,
    QualificationDriverError,
    _member_pipeline_perf_kwargs,
    _series_result_perf_fields,
    _verify_prologue_evidence,
    run_series,
)
from orchestrator.qualification import t126_driver  # noqa: E402
from test_schema_v2 import _valid_document  # noqa: E402

pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")


def _unavailable_receipt():
    events = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]
    return {
        "schema": "izanagi-perf-preflight/v1",
        "status": "unavailable",
        "available": False,
        "probe_argv": [
            "perf", "stat", "-x,", "-o", "<tmp>/perf.csv", "-e",
            ",".join(events), "--", "/bin/true",
        ],
        "rc": None,
        "parsed_events": [],
        "reason": "perf-not-found",
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }


def _degraded_observation():
    return {
        "use_perf": False,
        "counter_status": "not_required",
        "missing_leading_indicators": [],
        "preflight": _unavailable_receipt(),
        "claim_scope": {
            "throughput": "eligible",
            "perf_required": "unsupported",
        },
    }


def _prologue_value(toolchain_path: Path, *, perf_present: bool):
    code_identity = {
        "orchestrator/qualification/t126_control_v1.json": "1" * 64,
        "tools/pegasus/policy.json": "2" * 64,
        "orchestrator/qualification/t126_driver.py": "3" * 64,
    }
    script_identity = {
        RESERVATION_POLICY_RELATIVE_PATH: "4" * 64,
        "tools/pegasus/t126_qualification.sh": "5" * 64,
    }
    series_preimage = {
        "superproject_commit": "6" * 40,
        "superproject_tree": "7" * 40,
        "ccbench_gitlink": "8" * 40,
        "code_identity": code_identity,
        "script_identity": script_identity,
    }
    value = {
        "schema_version": "t126-source-stage-evidence/v1",
        "source_commit": series_preimage["superproject_commit"],
        "source_tree": series_preimage["superproject_tree"],
        "ccbench_gitlink": series_preimage["ccbench_gitlink"],
        "tracked_only": True,
        "immutable_mode": True,
        "protocol_sha256": code_identity[
            "orchestrator/qualification/t126_control_v1.json"],
        "policy_sha256": code_identity["tools/pegasus/policy.json"],
        "reservation_policy_sha256": script_identity[
            RESERVATION_POLICY_RELATIVE_PATH],
        "driver_sha256": code_identity[
            "orchestrator/qualification/t126_driver.py"],
        "job_script_sha256": script_identity[
            "tools/pegasus/t126_qualification.sh"],
        "toolchain_manifest_sha256": hashlib.sha256(
            toolchain_path.read_bytes()).hexdigest(),
    }
    if perf_present:
        value.update({
            "perf_smoke_returncode": 0,
            "perf_smoke_stdout": "",
            "perf_smoke_stderr": (
                "1,LLC-load-misses\n1,LLC-loads\n"
                "1,instructions\n1,cycles\n"
            ),
        })
    else:
        value["perf_observation"] = _degraded_observation()
    return value, series_preimage


def test_prologue_perf_present_and_degraded_exact_shapes(monkeypatch, tmp_path):
    toolchain_path = tmp_path / "toolchain.json"
    toolchain_path.write_bytes(b"{}\n")
    present, series_preimage = _prologue_value(
        toolchain_path, perf_present=True)
    monkeypatch.setattr(t126_driver, "load_json_strict", lambda _path: present)
    assert _verify_prologue_evidence(
        tmp_path / "evidence.json", series_preimage=series_preimage,
        toolchain_manifest_path=toolchain_path) is None

    degraded, series_preimage = _prologue_value(
        toolchain_path, perf_present=False)
    monkeypatch.setattr(t126_driver, "load_json_strict", lambda _path: degraded)
    assert _verify_prologue_evidence(
        tmp_path / "evidence.json", series_preimage=series_preimage,
        toolchain_manifest_path=toolchain_path) == _degraded_observation()

    degraded["perf_smoke_returncode"] = 0
    with pytest.raises(QualificationDriverError, match="consumer-verifiable"):
        _verify_prologue_evidence(
            tmp_path / "evidence.json", series_preimage=series_preimage,
            toolchain_manifest_path=toolchain_path)


@pytest.mark.parametrize(
    "missing_event",
    ["LLC-load-misses", "LLC-loads", "instructions", "cycles"],
)
def test_mg1_perf_present_prologue_requires_every_smoke_event(
        monkeypatch, tmp_path, missing_event):
    toolchain_path = tmp_path / "toolchain.json"
    toolchain_path.write_bytes(b"{}\n")
    value, series_preimage = _prologue_value(
        toolchain_path, perf_present=True)
    value["perf_smoke_stderr"] = "\n".join(
        event for event in (
            "LLC-load-misses", "LLC-loads", "instructions", "cycles")
        if event != missing_event)
    monkeypatch.setattr(t126_driver, "load_json_strict", lambda _path: value)
    with pytest.raises(QualificationDriverError, match="consumer-verifiable"):
        _verify_prologue_evidence(
            tmp_path / "evidence.json", series_preimage=series_preimage,
            toolchain_manifest_path=toolchain_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("perf_smoke_returncode", 1),
        ("perf_smoke_stdout", "<not supported>"),
        ("perf_smoke_stderr", "<not counted>"),
    ],
)
def test_perf_present_prologue_keeps_rc_and_counter_rejection(
        monkeypatch, tmp_path, field, value):
    toolchain_path = tmp_path / "toolchain.json"
    toolchain_path.write_bytes(b"{}\n")
    evidence, series_preimage = _prologue_value(
        toolchain_path, perf_present=True)
    evidence[field] = value
    monkeypatch.setattr(t126_driver, "load_json_strict", lambda _path: evidence)
    with pytest.raises(QualificationDriverError, match="consumer-verifiable"):
        _verify_prologue_evidence(
            tmp_path / "evidence.json", series_preimage=series_preimage,
            toolchain_manifest_path=toolchain_path)


def test_perf_present_call_and_series_result_keys_remain_exact():
    assert _member_pipeline_perf_kwargs(None) == {}
    assert _series_result_perf_fields(None) == {}

    observation = _degraded_observation()
    assert _member_pipeline_perf_kwargs(observation) == {
        "use_perf": False,
        "perf_preflight_receipt": observation["preflight"],
    }
    assert _series_result_perf_fields(observation) == {
        "perf_observation": observation,
    }


def test_m10_driver_binds_prologue_observation_at_every_member_callsite():
    source = (_ROOT / "orchestrator/qualification/t126_driver.py").read_text(
        encoding="utf-8")
    tree = ast.parse(source)
    member_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "validate_member_evidence"
    ]
    assert len(member_calls) == 2
    assert {
        ast.unparse(keyword.value)
        for call in member_calls for keyword in call.keywords
        if keyword.arg == "expected_perf_observation"
    } == {"self.perf_observation", "perf_observation"}

    prologue_assignments = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "_verify_prologue_evidence"
    ]
    assert len(prologue_assignments) == 2
    assert {
        ast.unparse(target)
        for assignment in prologue_assignments
        for target in assignment.targets
    } == {"perf_observation"}


def _attest_fixture(monkeypatch):
    document = _valid_document()
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = (
        effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT
    )
    calibration = schema_v2.validate_calibration_v2(document)
    expected_raw = document["attestation_profile"]
    expected_sha256 = hashlib.sha256(json.dumps(
        expected_raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()
    verified = VerifiedCalibration(
        schema_version=document["schema_version"],
        sha256=hashlib.sha256(json.dumps(document).encode("utf-8")).hexdigest(),
        calibration=calibration,
        attestation_profile_sha256=expected_sha256,
    )
    raw = json.loads(json.dumps(expected_raw))
    del raw["effective_clock"]["tolerance_pct"]
    monkeypatch.setattr(
        t126_driver.env_attestation, "load_verified_calibration",
        lambda _contract, _root: verified,
    )
    monkeypatch.setattr(
        t126_driver.env_attestation, "probe",
        lambda: env_attestation.normalize_observed_profile(raw),
    )
    return verified, raw


def test_t541_attest_accepts_matching_profile_with_v2_envelope(monkeypatch, tmp_path):
    """T-541/T-507: 実比較・parser・観測 hash を通して一致入力を受理する。"""
    verified, raw = _attest_fixture(monkeypatch)
    payload = t126_driver._attest(tmp_path, object())
    assert set(payload) == {
        "schema_version", "status", "expected_profile_sha256",
        "observed_profile_sha256", "observed_profile_projection_schema",
        "comparisons",
    }
    assert payload["schema_version"] == "t126-qualification-attestation/v2"
    assert payload["observed_profile_projection_schema"] == "pegasus-probe-output/v2"
    assert payload["status"] == "accepted"
    assert payload["expected_profile_sha256"] == verified.attestation_profile_sha256
    assert payload["observed_profile_sha256"] == hashlib.sha256(json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()
    comparisons = payload["comparisons"]
    assert len(comparisons) == 21
    assert {row["field"] for row in comparisons} == {
        "cpu.vendor", "cpu.family", "cpu.model", "cpu.model_name_raw",
        "cpu.model_name_normalized", "cores.physical", "cores.logical",
        "cores.smt_active", "cores.affinity_visible", "cache_topology", "numa",
        "tsc.raw_samples_mhz", "tsc.median_mhz", "tsc.clocks_per_us_int",
        "tsc.source", "effective_clock.samples_mhz", "effective_clock.method",
        "effective_clock.governor", "visibility.hidepid",
        "visibility.pid_ns_shared_with_host", "visibility.pid_ns_method",
    }
    assert all(row["verdict"] == "pass" for row in comparisons)


def test_t541_attest_rejects_governor_mismatch(monkeypatch, tmp_path):
    _, raw = _attest_fixture(monkeypatch)
    raw["effective_clock"]["governor"] = "powersave"
    with pytest.raises(QualificationDriverError, match="comparison contains a mismatch"):
        t126_driver._attest(tmp_path, object())


@pytest.mark.parametrize("side", ["lower", "upper"])
@pytest.mark.parametrize("outside", [False, True], ids=["endpoint", "just-outside"])
def test_t541_attest_clock_band_boundary(monkeypatch, tmp_path, side, outside):
    verified, raw = _attest_fixture(monkeypatch)
    clock = verified.calibration.attestation_profile.effective_clock
    median = float(statistics.median(clock.samples_mhz))
    delta = abs(median) * clock.tolerance_pct / 100.0
    endpoint = median - delta if side == "lower" else median + delta
    sample = math.nextafter(
        endpoint, -math.inf if side == "lower" else math.inf,
    ) if outside else endpoint
    # Only one sample moves; the median remains inside the allowed band.
    raw["effective_clock"]["samples_mhz"][0] = sample
    if outside:
        with pytest.raises(QualificationDriverError, match="comparison contains a mismatch"):
            t126_driver._attest(tmp_path, object())
    else:
        payload = t126_driver._attest(tmp_path, object())
        assert payload["status"] == "accepted"
        assert all(row["verdict"] == "pass" for row in payload["comparisons"])


def test_t541_attest_wraps_probe_exception(monkeypatch, tmp_path):
    _attest_fixture(monkeypatch)

    def fail_probe():
        raise OSError("probe unavailable")

    monkeypatch.setattr(t126_driver.env_attestation, "probe", fail_probe)
    with pytest.raises(QualificationDriverError, match="OSError: probe unavailable") as exc:
        t126_driver._attest(tmp_path, object())
    assert isinstance(exc.value.__cause__, OSError)


def test_t541_attest_rejects_empty_comparisons(monkeypatch, tmp_path):
    _attest_fixture(monkeypatch)
    monkeypatch.setattr(
        t126_driver.env_attestation, "compare_profiles", lambda *args, **kwargs: [],
    )
    with pytest.raises(QualificationDriverError, match="comparison contains a mismatch"):
        t126_driver._attest(tmp_path, object())


def _t2683_setup(monkeypatch, tmp_path, stage="pre-round", round_index=1):
    verified, raw = _attest_fixture(monkeypatch)
    protocol, capability, layout, fsm = _fsm(tmp_path)
    name = f"{stage}-{round_index if round_index is not None else 'final'}"
    accepted = layout.attempt_dir / "attestation" / f"{name}.json"
    kwargs = dict(repo_root=tmp_path, contract=object(), capability=capability,
                  relative=accepted.relative_to(capability.root).as_posix(),
                  stage=stage, round_index=round_index)
    return verified, raw, protocol, layout, fsm, accepted, kwargs


def _t2683_message(layout, kwargs):
    return t126_driver._attestation_rejection_message(
        capability=kwargs["capability"], relative=kwargs["relative"],
        attempt_dir=layout.attempt_dir)


def test_t2683_mismatch_preserves_all_comparison_rows(monkeypatch, tmp_path):
    verified, raw, _, _, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path)
    raw["effective_clock"]["governor"] = "powersave"
    with pytest.raises(t126_driver.AttestationMismatchError) as caught:
        t126_driver._attest(tmp_path, object())
    exc = caught.value
    assert isinstance(exc, QualificationDriverError)
    assert str(exc) == "attestation comparison contains a mismatch"
    assert exc.expected_profile_sha256 == verified.attestation_profile_sha256
    assert exc.observed_profile_sha256 == hashlib.sha256(json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    assert exc.observed_profile_projection_schema == "pegasus-probe-output/v2"
    assert t126_driver._run_attestation_child(**kwargs) == 31
    sidecar = accepted.with_suffix(".mismatch.json")
    assert sidecar.is_file()
    diagnostic = t126_driver.load_json_strict(sidecar)
    assert diagnostic == {
        "schema_version": "t126-qualification-attestation-mismatch/v1",
        "status": "rejected", "stage": "pre-round", "round_index": 1,
        "expected_profile_sha256": exc.expected_profile_sha256,
        "observed_profile_sha256": exc.observed_profile_sha256,
        "observed_profile_projection_schema": exc.observed_profile_projection_schema,
        "comparisons": exc.comparisons,
        "failed_fields": ["effective_clock.governor"],
    }
    rows = diagnostic["comparisons"]
    assert len(rows) == 21
    assert sum(row["verdict"] == "pass" for row in rows) == 20
    failed = [row for row in rows if row["verdict"] != "pass"]
    assert len(failed) == 1
    assert failed[0]["field"] == "effective_clock.governor"
    assert failed[0]["expected"] == "performance"
    assert failed[0]["observed"] == "powersave"
    assert not accepted.exists()
    assert list(sidecar.parent.iterdir()) == [sidecar]


@pytest.mark.parametrize("stage,round_index", [("pre-round", 1), ("post-series", None)])
def test_t2683_match_preserves_accepted_bytes_without_sidecar(monkeypatch, tmp_path, stage, round_index):
    verified, raw, _, _, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path, stage, round_index)
    # Construct the old payload contract independently of both driver helpers.
    expected = {
        "schema_version": "t126-qualification-attestation/v2", "status": "accepted",
        "expected_profile_sha256": verified.attestation_profile_sha256,
        "observed_profile_sha256": hashlib.sha256(json.dumps(
            raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest(),
        "observed_profile_projection_schema": "pegasus-probe-output/v2",
        "comparisons": env_attestation.compare_profiles(
            verified.calibration.attestation_profile,
            env_attestation.normalize_observed_profile(raw), now_fn=time.time),
        "stage": stage, "round_index": round_index,
    }
    assert t126_driver._run_attestation_child(**kwargs) == 0
    assert accepted.read_bytes() == json.dumps(
        expected, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
    assert not accepted.with_suffix(".mismatch.json").exists()
    assert list(accepted.parent.iterdir()) == [accepted]


def test_t2683_empty_comparisons_writes_rejected_sidecar(monkeypatch, tmp_path):
    _, _, _, _, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path)
    monkeypatch.setattr(env_attestation, "compare_profiles", lambda *a, **kw: [])
    with pytest.raises(t126_driver.AttestationMismatchError) as caught:
        t126_driver._attest(tmp_path, object())
    assert caught.value.comparisons == []
    assert t126_driver._run_attestation_child(**kwargs) == 31
    sidecar = accepted.with_suffix(".mismatch.json")
    assert sidecar.is_file()
    value = t126_driver.load_json_strict(sidecar)
    assert value["comparisons"] == value["failed_fields"] == []
    assert value["status"] == "rejected"
    assert value["schema_version"] == "t126-qualification-attestation-mismatch/v1"
    assert not accepted.exists()


@pytest.mark.parametrize("error", [OSError, QualificationArtifactError])
def test_t2683_sidecar_write_failure_preserves_rc(monkeypatch, tmp_path, error):
    _, raw, _, _, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path)
    raw["effective_clock"]["governor"] = "powersave"
    writer = t126_driver.create_json
    attempts = []

    def fail_sidecar(cap, rel, value):
        attempts.append(rel)
        if rel.endswith(".mismatch.json"):
            raise error("diagnostic unavailable")
        return writer(cap, rel, value)

    monkeypatch.setattr(t126_driver, "create_json", fail_sidecar)
    assert t126_driver._run_attestation_child(**kwargs) == 31
    assert attempts == [Path(kwargs["relative"]).with_suffix(".mismatch.json").as_posix()]
    assert not accepted.exists() and not accepted.with_suffix(".mismatch.json").exists()


def test_t2683_probe_failure_has_no_sidecar(monkeypatch, tmp_path):
    _, _, _, _, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path)

    def fail_probe():
        raise OSError("probe unavailable")

    monkeypatch.setattr(env_attestation, "probe", fail_probe)
    with pytest.raises(QualificationDriverError, match="attestation failed: OSError: probe unavailable") as caught:
        t126_driver._attest(tmp_path, object())
    assert not isinstance(caught.value, t126_driver.AttestationMismatchError)
    assert t126_driver._run_attestation_child(**kwargs) == 31
    assert not accepted.exists() and not accepted.with_suffix(".mismatch.json").exists()


def test_t2683_existing_sidecar_is_not_overwritten(monkeypatch, tmp_path):
    _, raw, _, _, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path)
    raw["effective_clock"]["governor"] = "powersave"
    sidecar = accepted.with_suffix(".mismatch.json")
    t126_driver.create_json(kwargs["capability"],
                           sidecar.relative_to(kwargs["capability"].root).as_posix(), {"prior": True})
    before = sidecar.read_bytes()
    assert t126_driver._run_attestation_child(**kwargs) == 31
    assert sidecar.read_bytes() == before
    assert not accepted.exists()
    assert list(sidecar.parent.iterdir()) == [sidecar]


@pytest.mark.parametrize("stage,round_index", [("pre-round", 1), ("post-series", None)])
def test_t2683_parent_message_names_sidecar_and_failed_fields(monkeypatch, tmp_path, stage, round_index):
    _, raw, _, layout, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path, stage, round_index)
    raw["effective_clock"]["governor"] = "powersave"
    assert t126_driver._run_attestation_child(**kwargs) == 31
    relative = accepted.with_suffix(".mismatch.json").relative_to(layout.attempt_dir).as_posix()
    assert _t2683_message(layout, kwargs) == (
        f"attestation child rejected; diagnostic={relative}; "
        'failed_fields=["effective_clock.governor"]')


def test_t2683_parent_message_without_sidecar_is_legacy(monkeypatch, tmp_path):
    _, _, _, layout, _, _, kwargs = _t2683_setup(monkeypatch, tmp_path)
    assert _t2683_message(layout, kwargs) == "attestation child rejected"


@pytest.mark.parametrize("damage", ["json", "shape", "read", "exists"])
def test_t2683_parent_message_unreadable_sidecar_is_best_effort(monkeypatch, tmp_path, damage):
    _, _, _, layout, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path)
    sidecar = accepted.with_suffix(".mismatch.json")
    t126_driver.create_json(kwargs["capability"],
                           sidecar.relative_to(kwargs["capability"].root).as_posix(), {"failed_fields": [1]})
    if damage == "json":
        sidecar.write_bytes(b"{\n")
    elif damage in {"read", "exists"}:
        def fail(*args):
            raise OSError("unreadable")
        if damage == "read":
            monkeypatch.setattr(t126_driver, "load_json_strict", fail)
    expected = "attestation child rejected"
    if damage != "exists":
        expected += "; diagnostic=attestation/pre-round-1.mismatch.json; failed_fields=unavailable"
    with monkeypatch.context() as patch:
        if damage == "exists":
            original_exists = Path.exists

            def fail_sidecar_exists(path):
                if str(path).endswith(".mismatch.json"):
                    raise OSError("unreadable")
                return original_exists(path)

            patch.setattr(Path, "exists", fail_sidecar_exists)
        assert _t2683_message(layout, kwargs) == expected


@pytest.mark.parametrize("failure_stage", ["pre-round", "post-series"])
@pytest.mark.parametrize("diagnostic", ["present", "missing", "unreadable"])
def test_t2683_diagnostic_rejection_preserves_ledger_contract(monkeypatch, tmp_path, failure_stage, diagnostic):
    _, raw, protocol, layout, fsm, _, kwargs = _t2683_setup(monkeypatch, tmp_path)
    messages = []

    def attest(stage, round_index):
        if stage == failure_stage:
            raw["effective_clock"]["governor"] = "powersave"
        name = f"{stage}-{round_index if round_index is not None else 'final'}"
        accepted = layout.attempt_dir / "attestation" / f"{name}.json"
        kwargs.update(stage=stage, round_index=round_index,
                      relative=accepted.relative_to(kwargs["capability"].root).as_posix())
        rc = t126_driver._run_attestation_child(**kwargs)
        if rc:
            assert rc == 31
            sidecar = accepted.with_suffix(".mismatch.json")
            if diagnostic == "missing":
                sidecar.unlink()
            elif diagnostic == "unreadable":
                sidecar.write_bytes(b"{\n")
            message = _t2683_message(layout, kwargs)
            messages.append(message)
            raise AttestationError(message)
        return t126_driver.load_json_strict(accepted)

    with pytest.raises(AttestationError) as caught:
        run_series(
            fsm=fsm, protocol=protocol,
            member_runner=lambda _, role: {
                "median_tps": 90.0 if role == "subject" else 100.0,
                "evidence_ref": _evidence(role), "terminal_monotonic": 0.0},
            attestation_fn=attest, reservation_recheck=lambda _: None,
            sleep_fn=lambda _: None, monotonic_fn=lambda: 1800.0)
    assert caught.value.rc == 31
    events = load_jsonl_strict(kwargs["capability"].root / layout.ledger_relpath)
    assert replay_ledger(events, protocol).state == fsm.replay.state == "rejected"
    evidence = {"stage": failure_stage, "type": "AttestationError", "message": messages[0]}
    canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assert events[-1]["payload"] == {
        "reason": "attestation", "evidence_canonical_json": canonical,
        "evidence_sha256": hashlib.sha256(canonical.encode()).hexdigest()}


def test_t2683_run_attest_closure_wires_child_helper_and_rejection_message():
    tree = ast.parse(Path(t126_driver.__file__).read_text(encoding="utf-8"))
    run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
    attest = next(node for node in run.body if isinstance(node, ast.FunctionDef) and node.name == "attest")
    exits = [node for node in ast.walk(attest) if isinstance(node, ast.Call)
             and ast.unparse(node.func) == "os._exit" and len(node.args) == 1
             and isinstance(node.args[0], ast.Call)
             and ast.unparse(node.args[0].func) == "_run_attestation_child"]
    raises = [node for node in ast.walk(attest) if isinstance(node, ast.Raise)
              and isinstance(node.exc, ast.Call) and ast.unparse(node.exc.func) == "AttestationError"
              and len(node.exc.args) == 1 and isinstance(node.exc.args[0], ast.Call)
              and ast.unparse(node.exc.args[0].func) == "_attestation_rejection_message"]
    assert len(exits) == 1
    assert len(raises) == 1
    assert any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Name) and node.test.id == "is_child"
        and any(isinstance(stmt, ast.Expr) and stmt.value is exits[0]
                for stmt in node.body)
        for node in ast.walk(attest)
    )
    child_call = exits[0].args[0]
    assert {kw.arg: ast.unparse(kw.value) for kw in child_call.keywords} == {
        "repo_root": "source_root", "contract": "contract",
        "capability": "capability", "relative": "relative",
        "stage": "stage", "round_index": "round_index",
    }
    assert any(
        isinstance(node, ast.If)
        and ast.unparse(node.test) == "os.waitstatus_to_exitcode(status) != 0"
        and raises[0] in node.body
        for node in ast.walk(attest)
    )
    message_call = raises[0].exc.args[0]
    assert {kw.arg: ast.unparse(kw.value) for kw in message_call.keywords} == {
        "capability": "capability", "relative": "relative",
        "attempt_dir": "layout.attempt_dir",
    }


def test_t2683_forked_child_writes_sidecar_visible_to_parent(monkeypatch, tmp_path):
    _, raw, _, layout, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path)
    raw["effective_clock"]["governor"] = "powersave"
    pid = os.fork()
    if pid == 0:
        try:
            os._exit(t126_driver._run_attestation_child(**kwargs))
        except BaseException:
            os._exit(99)
    waited, status = os.waitpid(pid, 0)
    assert waited == pid
    assert os.waitstatus_to_exitcode(status) == 31
    assert accepted.with_suffix(".mismatch.json").is_file() and not accepted.exists()
    assert _t2683_message(layout, kwargs) == (
        'attestation child rejected; diagnostic=attestation/pre-round-1.mismatch.json; '
        'failed_fields=["effective_clock.governor"]')


def test_t2683_mismatch_sidecar_is_listed_in_collector_closure(monkeypatch, tmp_path):
    from orchestrator.qualification.collector import _manifest

    _, raw, _, layout, _, accepted, kwargs = _t2683_setup(monkeypatch, tmp_path)
    raw["effective_clock"]["governor"] = "powersave"
    assert t126_driver._run_attestation_child(**kwargs) == 31
    record = t126_driver.file_record(accepted.with_suffix(".mismatch.json"), relative_to=layout.attempt_dir)
    assert record["path"] == "attestation/pre-round-1.mismatch.json"
    assert record in _manifest(layout.attempt_dir, exclude=set())


def test_qualification_entry_constructs_run_context_for_live_member_build():
    source = (_ROOT / "orchestrator/qualification/t126_driver.py").read_text(
        encoding="utf-8"
    )
    assert "build_run_context(" in source
    assert "build_context=build_context" in source
    assert "BuildAdmission(" not in source


def test_qualification_policy_rejects_unadmitted_coder_before_build_spy(tmp_path):
    protocol, capability, layout, _ = _fsm(tmp_path)
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
    )
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    genome = Genome("silo", {"BACK_OFF": 1})
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    dirty = campaign_fixtures._source_evidence(
        genome, "d706650", src_token="2" * 64,
        source_root=str(tmp_path / "dirty-coder-source"),
    )
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    builds = []
    original_source_digest = pipeline.source_digest
    monkey_source_digest = type("SourceDigestSpy", (), {
        "STOCK": pipeline.source_digest.STOCK,
        "resolve_evidence": staticmethod(lambda *_args, **_kwargs: dirty),
    })
    original_build_v2 = pipeline.buildcache.build_v2
    pipeline.source_digest = monkey_source_digest
    pipeline.buildcache.build_v2 = lambda *_args, **_kwargs: builds.append(_kwargs)
    try:
        result = pipeline.evaluate(
            genome, layout, "pegasus", "d706650", perf, 2100, numactl=(),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=True, do_settle=True, src_token=dirty.src_token,
            cache_root=str(tmp_path / "cache"), bench_max_rounds=1,
            env_contract=pegasus, authorization_contract=pegasus_authorization,
            record_rep_returncodes=True,
            qualification_policy=policy, log=lambda *_: None,
            build_context=context,
        )
    finally:
        pipeline.source_digest = original_source_digest
        pipeline.buildcache.build_v2 = original_build_v2
    assert result.aborted and not result.certified
    assert builds == []
    records = load_jsonl_strict(
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    )
    assert [row["evaluation_stage"] for row in records] == [
        "qualification_build_start",
        "qualification_evaluation_rejected",
    ]
    abort_payload = json.loads(records[-1]["payload"]["canonical_json"])
    assert abort_payload["reason"] == "admission-error"
    assert abort_payload["error"].startswith("BuildAdmissionError:")


def test_qualification_policy_missing_context_is_separate_signature_error(tmp_path):
    protocol, capability, layout, _ = _fsm(tmp_path)
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(
        QualificationEventSink(
            capability, layout, round_index=1, role="subject",
            source_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
        )
    )
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
    )
    with pytest.raises(TypeError, match="build_context"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout, "pegasus", "deadbeef",
            perf, 2100, numactl=(), env_contract=pegasus,
            authorization_contract=pegasus_authorization,
            qualification_policy=policy, build_context=None,
        )
    assert not (
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    ).exists()


def test_qualification_stock_source_reaches_build_with_exact_class(
        tmp_path, monkeypatch):
    protocol, capability, layout, _ = _fsm(tmp_path)
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(
        QualificationEventSink(
            capability, layout, round_index=1, role="subject",
            source_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
        )
    )
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    genome = Genome("silo", {"BACK_OFF": 1})
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    stock = campaign_fixtures._source_evidence(
        genome, "25898d0", source_root=str(tmp_path / "clean-stock-source"),
    )
    seen = []

    monkeypatch.setattr(
        pipeline.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: stock,
    )

    def stop_at_build(*_args, **kwargs):
        seen.append(kwargs["admission"].provenance)
        raise RuntimeError("stop after stock admission")

    monkeypatch.setattr(pipeline.buildcache, "build_v2", stop_at_build)
    # resolve_evidence seam は下の任意 token を読まず、stock evidence の commit だけが
    # build_admission.CURRENT_PIN 比較へ届く。
    result = pipeline.evaluate(
        genome, layout, "pegasus", "d706650", perf, 2100, numactl=(),
        extra_correctness=[
            (pipeline.S2_TAG, pipeline.s2_correctness_workload())
        ],
        do_bench=True, do_settle=True, src_token=stock.src_token,
        cache_root=str(tmp_path / "cache"), bench_max_rounds=1,
        env_contract=pegasus, authorization_contract=pegasus_authorization,
        record_rep_returncodes=True,
        qualification_policy=policy, log=lambda *_: None,
        build_context=build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP),
    )
    assert result.aborted and not result.certified
    assert seen == [BuildProvenance.STOCK_BASELINE]


def _fsm(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    root = QualificationRoot(repo)
    capability = root.issue()
    layout = create_attempt(
        root, capability, series_id="a" * 64, attempt_id="b" * 64)
    identity = {
        "qualification_series_id": "a" * 64,
        "qualification_attempt_id": "b" * 64,
        "pbs_job_id": "123.server",
        "host": "pegasus",
        "boot_id": "boot",
        "controller_pid": 123,
    }
    protocol = load_protocol()
    return protocol, capability, layout, SeriesFSM(
        capability, layout.ledger_relpath, identity, protocol,
        wall_clock_ns=iter(range(1000, 2000)).__next__,
        monotonic_ns=iter(range(2000, 3000)).__next__,
    )


def _evidence(role: str):
    return {"path": f"{role}.jsonl", "size": 1, "sha256": "c" * 64}


def test_fsm_replay_rejects_mixed_identity_and_terminal_suffix(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)
    fsm.open()
    order = fsm.open_round(1)
    for role in order:
        fsm.member_terminal(
            1, role, 90.0 if role == "subject" else 100.0, _evidence(role))
    assert fsm.round_terminal(
        1, subject_median_tps=90.0, reference_median_tps=100.0) == "continuing"
    events = list(fsm.events)
    mixed = [dict(row) for row in events]
    mixed[-1] = dict(mixed[-1])
    mixed[-1]["identity"] = dict(mixed[-1]["identity"], host="other")
    with pytest.raises(SeriesStateError, match="mixed"):
        replay_ledger(mixed, protocol)

    fsm.wait_satisfied(1, 1800.0)
    order = fsm.open_round(2)
    for role in order:
        fsm.member_terminal(
            2, role, 90.0 if role == "subject" else 100.0, _evidence(role))
    assert fsm.round_terminal(
        2, subject_median_tps=90.0, reference_median_tps=100.0
    ) == "lower_boundary"
    fsm.terminal(2)
    with pytest.raises(SeriesStateError, match="suffix"):
        fsm.terminal(2)


def test_driver_enforces_round_gap_attestation_and_reservation_order(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)
    calls = []

    def member(round_index, role):
        calls.append(("member", round_index, role))
        return {
            "median_tps": 90.0 if role == "subject" else 100.0,
            "evidence_ref": _evidence(role),
            "terminal_monotonic": 0.0,
        }

    monotonic = iter((0.0, 1800.0))
    outcome = run_series(
        fsm=fsm, protocol=protocol, member_runner=member,
        attestation_fn=lambda stage, round_index: calls.append(
            ("attest", stage, round_index)) or {"status": "accepted"},
        reservation_recheck=lambda required: calls.append(("reserve", required)),
        sleep_fn=lambda seconds: calls.append(("sleep", seconds)),
        monotonic_fn=monotonic.__next__,
    )
    assert outcome["terminal"] == "lower_boundary"
    assert outcome["bits"] == [0, 0]
    assert ("sleep", 1800.0) in calls
    assert [row for row in calls if row[0] == "attest"] == [
        ("attest", "pre-round", 1),
        ("attest", "pre-round", 2),
        ("attest", "post-series", None),
    ]
    assert len([row for row in calls if row[0] == "reserve"]) == 2


def test_driver_rejects_immediately_without_running_second_member(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)
    roles = []

    def reject_first(round_index, role):
        roles.append(role)
        raise MemberRunError("anomaly", {"anomalies": 1})

    with pytest.raises(MemberRunError, match="anomaly"):
        run_series(
            fsm=fsm, protocol=protocol, member_runner=reject_first,
            attestation_fn=lambda *_: {"status": "accepted"},
            reservation_recheck=lambda _: None,
        )
    assert len(roles) == 1
    assert fsm.replay.state == "rejected"
    assert fsm.replay.observations_recorded == 0


@pytest.mark.parametrize(
    ("bits", "terminal"),
    [
        ((0, 0), "lower_boundary"),
        ((1, 1, 1, 1), "upper_boundary"),
        ((0, 1, 1, 0, 1, 1, 1, 0), "indeterminate"),
    ],
)
def test_fsm_clean_terminal_positive_controls(tmp_path, bits, terminal):
    protocol, _, _, fsm = _fsm(tmp_path)

    def member(round_index, role):
        bit = bits[round_index - 1]
        return {
            "median_tps": (104.0 if bit else 100.0)
            if role == "subject" else 100.0,
            "evidence_ref": _evidence(role),
            "terminal_monotonic": 0.0,
        }

    outcome = run_series(
        fsm=fsm, protocol=protocol, member_runner=member,
        attestation_fn=lambda *_: {"status": "accepted"},
        reservation_recheck=lambda _: None,
        sleep_fn=lambda _: None,
        monotonic_fn=lambda: 1800.0,
    )
    assert outcome["terminal"] == terminal
    assert outcome["bits"] == list(bits)
    assert fsm.replay.state == "terminal"


def test_attestation_failure_is_terminal_reject_with_exact_rc(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)

    def reject_attestation(*_):
        raise AttestationError("mismatch")

    with pytest.raises(AttestationError) as exc_info:
        run_series(
            fsm=fsm, protocol=protocol,
            member_runner=lambda *_: pytest.fail("member must not start"),
            attestation_fn=reject_attestation,
            reservation_recheck=lambda _: None,
        )
    assert exc_info.value.rc == RC_ATTESTATION
    assert fsm.replay.state == "rejected"
    assert fsm.replay.observations_recorded == 0


def test_exact_pegasus_empty_numactl_opt_in_emits_nonformal_evidence(tmp_path):
    protocol, capability, layout, _ = _fsm(tmp_path)
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
    )
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
        extime=3, reps=5,
    )
    with campaign_fixtures._mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout, "pegasus", "deadbeef",
            perf, 2100, numactl=(),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=True, do_settle=True, src_token="stock",
            cache_root=str(tmp_path / "cache"), bench_max_rounds=1,
            env_contract=pegasus, authorization_contract=pegasus_authorization,
            record_rep_returncodes=True,
            qualification_policy=policy, log=lambda *_: None,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    assert result.certified and not result.aborted
    records = load_jsonl_strict(
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl")
    admitted = validate_member_evidence(
        records, expected_role="subject", expected_round=1,
        expected_perf_observation=None,
        expected_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
    )
    assert admitted["verify_order"] == ["legacy", "s2"]
    assert calls.lock_enters == 2
    assert calls.competition_probes == 2
    assert not (layout.attempt_dir / "runs/wal.jsonl").exists()


def test_m4a_producer_settled_gate_rejects_before_terminal_commit(
        tmp_path, monkeypatch):
    protocol, capability, layout, _ = _fsm(tmp_path)
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
    )
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    with campaign_fixtures._mock_pipeline(certified=True):
        monkeypatch.setattr(pipeline, "settle", lambda: {"settled": False})
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout, "pegasus", "deadbeef",
            perf, 2100, numactl=(),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=True, do_settle=True, src_token="stock",
            cache_root=str(tmp_path / "cache"), bench_max_rounds=1,
            env_contract=pegasus, authorization_contract=pegasus_authorization,
            record_rep_returncodes=True,
            qualification_policy=policy, log=lambda *_: None,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    assert result.aborted is True
    stages = [
        row["evaluation_stage"] for row in load_jsonl_strict(
            layout.attempt_dir
            / "rounds/0001/subject/evaluation-events.jsonl")
    ]
    assert "qualification_evaluation_terminal" not in stages
    assert stages[-1] == "qualification_evaluation_rejected"


@pytest.mark.parametrize(
    "bad_numactl",
    [None, [], ("numactl", "--interleave=all")],
)
def test_qualification_opt_in_rejects_nonexact_numactl_before_writes(
        tmp_path, bad_numactl):
    protocol, capability, layout, _ = _fsm(tmp_path)
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(
        QualificationEventSink(
            capability, layout, round_index=1, role="subject",
            source_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
        ))
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
    )
    with pytest.raises(ValueError, match="exactly match"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout, "pegasus", "deadbeef",
            perf, 2100, numactl=bad_numactl,
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            src_token="stock", bench_max_rounds=1, env_contract=pegasus,
            authorization_contract=pegasus_authorization,
            record_rep_returncodes=True, qualification_policy=policy,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    assert not (
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    ).exists()


def test_exact_sink_layout_capability_chain_rejects_laundering_before_write(
        tmp_path):
    protocol, capability, layout, _ = _fsm(tmp_path)

    class DuckSink:
        def emit(self, *_args):
            raise AssertionError("duck sink must never receive a write")

    with pytest.raises(TypeError, match="exact QualificationEventSink"):
        pipeline.QualificationPipelinePolicy.t126_pegasus(DuckSink())
    with pytest.raises(TypeError, match="issued"):
        QualificationLayout(layout.root, layout.attempt_id, (1, 2), object(), object())
    with pytest.raises(AttributeError, match="immutable"):
        capability._root = tmp_path / "laundered"

    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
    )
    for name, value in (
            ("_capability", object()), ("_layout", object()),
            ("_round_index", 2), ("_role", "reference"),
            ("_relative", "attempts/other/evaluation-events.jsonl")):
        with pytest.raises(AttributeError, match="immutable"):
            setattr(sink, name, value)
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    with pytest.raises(QualificationArtifactError, match="layout"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), object(), "pegasus", "deadbeef",
            perf, 2100, numactl=(),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=True, do_settle=True, src_token="stock",
            bench_max_rounds=1, env_contract=pegasus,
            authorization_contract=pegasus_authorization,
            record_rep_returncodes=True, qualification_policy=policy,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    assert not (
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    ).exists()


def test_sink_rejects_capability_ancestor_replacement_before_first_write(
        tmp_path):
    protocol, capability, layout, _ = _fsm(tmp_path)
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256=protocol["source"]["campaign_lock_sha256"],
    )
    env_dir = layout.root.parents[2]
    moved = layout.root.parents[4] / "moved-env"
    env_dir.rename(moved)
    env_dir.symlink_to(moved, target_is_directory=True)
    with pytest.raises(QualificationArtifactError, match="ancestor"):
        sink.emit(
            layout, "variant", "build_start", "pegasus", {"genome": "g"})
    assert not (
        moved / "pegasus/qualification/t126/attempts"
        / layout.attempt_id / "rounds").exists()


def test_active_process_group_cleanup_kills_real_child_and_grandchild():
    pid = os.fork()
    if pid == 0:
        os.setsid()
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        grandchild = os.fork()
        if grandchild == 0:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            time.sleep(30)
            os._exit(0)
        time.sleep(30)
        os._exit(0)
    supervisor = ActiveProcessGroups(1.0)
    with pytest.raises(RuntimeError, match="fault"):
        with supervisor:
            supervisor.add(pid)
            time.sleep(0.05)
            raise RuntimeError("fault")
    with pytest.raises(ProcessLookupError):
        os.killpg(pid, 0)


@pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGHUP])
def test_actual_term_hup_handler_cleans_descendant_process_group(sig):
    code = """
import os,signal,sys,time
from orchestrator.qualification.t126_driver import ActiveProcessGroups
signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGHUP})
ready_fd=int(sys.argv[2])
with ActiveProcessGroups(0.2) as groups:
    child=os.fork()
    if child==0:
        os.setsid()
        grandchild=os.fork()
        if grandchild==0:
            time.sleep(30)
            os._exit(0)
        os.write(ready_fd,b'1')
        time.sleep(30)
        os._exit(0)
    groups.add(child)
    print(child,flush=True)
    signal.pause()
"""
    ready_read, ready_write = os.pipe()
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(int(sig)), str(ready_write)],
        cwd=_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(_ROOT),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        pass_fds=(ready_write,), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    os.close(ready_write)
    pgid = None
    cleanup_verified = False
    try:
        readable, _, _ = select.select([ready_read], [], [], 5.0)
        assert readable, "process group readiness handshake timed out"
        assert os.read(ready_read, 1) == b"1"
        assert process.stdout is not None
        pgid = int(process.stdout.readline().strip())
        os.kill(process.pid, sig)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode != 0, stderr
        assert stdout == ""
        with pytest.raises(ProcessLookupError):
            os.killpg(pgid, 0)
        cleanup_verified = True
    finally:
        os.close(ready_read)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
        if not cleanup_verified and pgid is not None:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_single_monotonic_envelope_rejects_gap_that_exceeds_wmax(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)
    now = {"ns": 0}
    envelope = MonotonicEnvelope(
        started_ns=0, deadline_ns=29100 * 1_000_000_000,
        wmax_s=29100, monotonic_ns=lambda: now["ns"])

    def member(_round_index, role):
        now["ns"] = (29100 - 600 - 10) * 1_000_000_000
        return {
            "median_tps": 90.0 if role == "subject" else 100.0,
            "evidence_ref": _evidence(role),
            "terminal_monotonic": 0.0,
        }

    with pytest.raises(QualificationDriverError, match="gap|deadline"):
        run_series(
            fsm=fsm, protocol=protocol, member_runner=member,
            attestation_fn=lambda *_: {"status": "accepted"},
            reservation_recheck=lambda _: None,
            sleep_fn=lambda _: pytest.fail("sleep must not exceed Wmax"),
            monotonic_fn=lambda: 0.0,
            envelope=envelope,
        )


def test_live_envelope_cannot_be_reissued_by_driver_and_rejects_overrun():
    with pytest.raises(QualificationDriverError, match="external"):
        MonotonicEnvelope.from_environ({}, 29100)
    envelope = MonotonicEnvelope(
        started_ns=1, deadline_ns=29100 * 1_000_000_000 + 1,
        wmax_s=29100,
        monotonic_ns=lambda: 29100 * 1_000_000_000 + 2)
    with pytest.raises(QualificationDriverError, match="exceeded"):
        envelope.receipt()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
