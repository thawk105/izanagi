from __future__ import annotations

import ast
from collections import deque
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from orchestrator.campaign.t810_preregistration import (
    APPROVAL_RECEIPT_SCHEMA_VERSION,
    PREREG_PATH,
    ApprovalReceipt,
    load_t810_preregistration,
)
from tools.pegasus import t810_budget as B
from tools.pegasus import t810_coordinator as C
from tools.pegasus import t810_guard as G
from tools.pegasus import t810_harness_schema as S
from tools.pegasus import t810_pbs_wrapper as W
from tools.pegasus import t810_runner_policy as R


H = "a" * 64
H2 = "b" * 64
PREREG_SHA256 = "3052af20993481730a826ce08ee26289948f29836d43afb2d7c743cfdd12e404"
APPROVAL_ID = "fixture-stage1-review-t810-v1"
FIXTURE = Path(__file__).parent / "fixtures" / "t810" / "wrapper_qsub_cases.json"
REPO = Path(__file__).resolve().parents[2]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _preregistration():
    return load_t810_preregistration(
        PREREG_PATH,
        approval_receipt=ApprovalReceipt(
            artifact_sha256=PREREG_SHA256, approval_id=APPROVAL_ID,
            schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
        ),
    )


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _qsub_slot(root: Path) -> dict:
    return {
        "job_name": "t810-slot-00",
        "pbs_stdout_path": str(root / "output/slot-00/pbs.stdout.log"),
        "pbs_stderr_path": str(root / "output/slot-00/pbs.stderr.log"),
        "script_path": str(root / "work/slot-00.pbs"),
    }


def test_canonical_qsub_argv_matches_fixture_byte_for_byte(tmp_path):
    fixture = _fixture()
    actual = W.canonical_qsub_argv(
        _qsub_slot(tmp_path), admission_policy=fixture["ratified_policy"],
        run_kind="liveness", submission_cwd=tmp_path / "work", repo_root=REPO,
    )
    expected = tuple(token.replace("$ROOT", str(tmp_path))
                     for token in fixture["expected_liveness_argv"])
    assert actual == expected


def test_unratified_qsub_fields_deny_generation(tmp_path):
    with pytest.raises(W.T810WrapperError, match="unratified"):
        W.canonical_qsub_argv(
            _qsub_slot(tmp_path), admission_policy=_fixture()["unratified_policy"],
            run_kind="liveness", submission_cwd=tmp_path / "work", repo_root=REPO,
        )


@pytest.mark.parametrize("field", ["pbs_stdout_path", "pbs_stderr_path", "script_path"])
def test_qsub_output_and_script_paths_must_be_external_absolute(tmp_path, field):
    slot = _qsub_slot(tmp_path)
    slot[field] = "relative/path"
    with pytest.raises(W.T810WrapperError, match="absolute"):
        W.canonical_qsub_argv(
            slot, admission_policy=_fixture()["ratified_policy"], run_kind="main",
            submission_cwd=tmp_path / "work", repo_root=REPO,
        )


def test_rendered_script_pins_python_and_contains_no_repo_or_forbidden_entrypoint(tmp_path):
    script = W.render_pbs_script(
        {"wrapper_path": str(tmp_path / "package/wrapper.py"),
         "request_path": str(tmp_path / "control/request.json")},
        interpreter_realpath=tmp_path / "bin/python3.10", repo_root=REPO,
    ).decode()
    assert script.count("python3.10 -I -B") == 2
    assert "readlink -f" in script and "sys.version_info[:2] == (3, 10)" in script
    assert str(REPO) not in script
    assert all(word not in script.lower() for word in ("calibration", "certify", "oracle", "trace"))


def test_intent_manifest_producer_binds_prereg_policy_request_and_publication(tmp_path):
    prereg = _preregistration()
    package, work, output = tmp_path / "package", tmp_path / "work", tmp_path / "output"
    package.mkdir()
    source = package / "CCBench-Silo"
    source.write_bytes(b"production-route-fixture")
    source.chmod(0o700)
    dependency = package / "dependencies.json"
    dependency.write_bytes(b"dependencies")
    interpreter = tmp_path / "python3.10"
    interpreter.write_bytes(b"python")
    interpreter.chmod(0o700)
    policy = R.build_runner_policy(prereg, executable_sha256=_sha(source))
    policy_sha = S.canonical_sha256(policy)
    slots = []
    for index in range(13):
        slot_id = f"slot-{index:02d}"
        slot_output = output / slot_id
        script = work / slot_id / "job.pbs"
        request_path = work / slot_id / "wrapper-request.json"
        qsub = [
            "qsub", "-o", str(slot_output / "pbs.stdout.log"),
            "-e", str(slot_output / "pbs.stderr.log"), str(script),
        ]
        slots.append({
            "slot_id": slot_id, "logical_request_id": f"logical-{index:02d}",
            "job_name": f"t810-{index:02d}", "qsub_argv": qsub,
            "wrapper_argv": ["python3.10", str(package / "wrapper.py"),
                             "--request", str(request_path)],
            "pbs_stdout_path": str(slot_output / "pbs.stdout.log"),
            "pbs_stderr_path": str(slot_output / "pbs.stderr.log"),
            "binary_source_path": str(source), "binary_sha256": _sha(source),
            "wrapper_path": str(package / "wrapper.py"), "wrapper_sha256": H,
            "runner_policy_path": str(package / f"runner-policy-{index:02d}.json"),
            "runner_policy_sha256": policy_sha,
            "expected_dependency_manifest_sha256": _sha(dependency),
            "expected_module_list_sha256": H, "expected_numa_nodes": 4,
            "script_path": str(script),
        })
    intent = {
        "schema_version": S.LAUNCH_INTENT_SCHEMA, "group_id": "group-1",
        "run_kind": "liveness", "attempt_ordinal": 1,
        "policy_sha256": H2, "preregistration_sha256": PREREG_SHA256,
        "prereg_approval_id": APPROVAL_ID, "created_at": "2026-08-12T00:00:00Z",
        "node_count": 13, "round_count": 10, "ready_timeout_seconds": 1200,
        "start_spread_max_ns": 5_000_000_000, "work_root": str(work),
        "output_root": str(output), "slots": slots,
    }
    manifest = {
        "schema_version": S.GROUP_MANIFEST_SCHEMA, "group_id": "group-1",
        "created_at": "2026-08-12T00:00:01Z",
        "launch_intent_sha256": S.canonical_sha256(intent),
        "guard_receipt_sha256": H, "budget_receipt_sha256": H,
        "release_token_commitment": S.release_token_commitment("release-nonce"),
    }
    witness = {
        "schema_version": S.LAUNCH_AUTHORIZATION_SCHEMA, "approval_id": APPROVAL_ID,
        "preregistration_sha256": PREREG_SHA256, "policy_sha256": H2,
        "run_kinds": ["liveness"], "issued_on": "2026-08-12", "nonce": "fixture",
    }
    token = S.verify_launch_authorization(
        witness, run_kind="liveness", preregistration_sha256=PREREG_SHA256,
        policy_sha256=H2,
    )
    request = W.build_wrapper_request(
        intent, manifest, prereg, token, slot_id="slot-00", pbs_request_id="81000.server",
        assigned_hostname="node00", allocated_cpus=[0, 1],
        observed_submission_argv=slots[0]["qsub_argv"],
        dependency_manifest_path=dependency, interpreter_realpath=interpreter,
    )
    assert request.runner_policy_sha256 == slots[0]["runner_policy_sha256"]
    assert not hasattr(request, "canonical_benchmark_argv")
    assert not hasattr(request, "expected_binary_sha256")
    published = W.publish_wrapper_request(
        intent, manifest, prereg, token, slot_id="slot-00", pbs_request_id="81000.server",
        assigned_hostname="node00", allocated_cpus=[0, 1],
        observed_submission_argv=slots[0]["qsub_argv"],
        dependency_manifest_path=dependency, interpreter_realpath=interpreter,
    )
    assert published == request
    serialized = json.loads(request.request_path.read_text())
    assert serialized["runner_policy_sha256"] == policy_sha
    assert "canonical_benchmark_argv" not in serialized


@pytest.mark.parametrize("invalid_token", [None, {}, {"document": "not-a-token"}])
def test_wrapper_low_level_write_adapter_rejects_non_token(tmp_path, invalid_token):
    with pytest.raises(W.T810WrapperError, match="AuthorizationToken"):
        W._append_jsonl(invalid_token, tmp_path / "effect.jsonl", b"{}\n")
    with pytest.raises(W.T810WrapperError, match="AuthorizationToken"):
        W._copy_binary(invalid_token, tmp_path / "source", tmp_path / "destination")
    assert not (tmp_path / "effect.jsonl").exists()
    assert not (tmp_path / "destination").exists()


class FakeClock:
    def __init__(self):
        self.ns = 0
        self.sleeps = []

    def monotonic_ns(self):
        return self.ns

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.ns += int(seconds * 1_000_000_000)


def _quiet(values):
    clock = FakeClock()
    queue = deque(values)
    samples, passed = W.wait_for_quiet(
        load1_reader=lambda: queue.popleft() if queue else values[-1],
        sleep=clock.sleep, monotonic_ns=clock.monotonic_ns,
        wall_clock=lambda: f"t-{clock.ns}",
    )
    return clock, samples, passed


def test_quiet_gate_accepts_exact_1_point_0_boundary():
    clock, samples, passed = _quiet([1.0, 1.0, 1.0])
    assert passed is True and len(samples) == 3
    assert clock.sleeps == [30.0, 30.0]


def test_quiet_gate_requires_consecutive_samples():
    _, samples, passed = _quiet([0.5, 1.01, 0.5, 0.5, 0.5])
    assert passed is True and len(samples) == 5


def test_quiet_gate_times_out_at_1200_seconds_without_real_sleep():
    clock, samples, passed = _quiet([1.01])
    assert passed is False and clock.ns == 1_200_000_000_000
    assert len(samples) == 41


def _write_proc(proc: Path, pid: int, *, parent: int, status: str | None, command: bytes | None):
    root = proc / str(pid)
    root.mkdir(parents=True)
    (root / "stat").write_text(f"{pid} (fixture) S {parent} 0 0 0\n", encoding="utf-8")
    if status is not None:
        (root / "status").write_text(status, encoding="utf-8")
    if command is not None:
        (root / "cmdline").write_bytes(command)


def test_process_scan_observes_other_uid_and_intersecting_affinity(tmp_path):
    proc = tmp_path / "proc"
    _write_proc(proc, 100, parent=1, status="Uid:\t1000\nCpus_allowed_list:\t0-3\n", command=b"wrapper\0")
    _write_proc(proc, 200, parent=1, status="Uid:\t2000\nCpus_allowed_list:\t2-5\n", command=b"other\0")
    scan = W.scan_competing_processes(frozenset({0, 1, 2, 3}), proc_root=proc, own_pid=100)
    assert [item["pid"] for item in scan.competing_processes] == [200]
    assert scan.unreadable == ()


def test_process_scan_records_uid_affinity_or_command_unreadability_fail_closed(tmp_path):
    proc = tmp_path / "proc"
    _write_proc(proc, 100, parent=1, status="Uid:\t1000\nCpus_allowed_list:\t0\n", command=b"wrapper\0")
    _write_proc(proc, 200, parent=1, status=None, command=None)
    scan = W.scan_competing_processes(frozenset({0}), proc_root=proc, own_pid=100)
    assert scan.competing_processes == ()
    assert scan.unreadable[0]["pid"] == 200
    assert set(scan.unreadable[0]["fields"]) == {"uid", "cpu_affinity", "command"}


def _request(tmp_path: Path, *, expected_hash: str | None = None) -> W.WrapperRequest:
    work, output, control = tmp_path / "work", tmp_path / "output", tmp_path / "work/control"
    package = tmp_path / "package"
    for path in (work, output, control, package, tmp_path / "bin"):
        path.mkdir(parents=True, exist_ok=True)
    source = package / "CCBench-Silo"
    source.write_bytes(b"benchmark-fixture")
    source.chmod(0o700)
    runner_policy_path = package / "runner-policy.json"
    policy = R.build_runner_policy(
        _preregistration(), executable_sha256=expected_hash or _sha(source),
    )
    runner_policy_path.write_bytes(S.canonical_json_bytes(policy) + b"\n")
    dependency = package / "dependencies.json"
    dependency.write_bytes(b"dependencies")
    interpreter = tmp_path / "bin/python3.10"
    interpreter.write_bytes(b"python")
    interpreter.chmod(0o700)
    slots = []
    for index in range(13):
        slot_id = f"slot-{index:02d}"
        slot_output, slot_work = output / slot_id, work / slot_id
        slot_work.mkdir(parents=True)
        qsub = [
            "qsub", "-o", str(slot_output / "pbs.stdout.log"),
            "-e", str(slot_output / "pbs.stderr.log"), str(slot_work / "job.pbs"),
        ]
        slots.append({
            "slot_id": slot_id, "logical_request_id": f"logical-{index:02d}",
            "job_name": f"t810-{index:02d}", "qsub_argv": qsub,
            "wrapper_argv": ["python3.10", str(package / "wrapper.py"), "--request",
                             str(slot_work / "wrapper-request.json")],
            "pbs_stdout_path": str(slot_output / "pbs.stdout.log"),
            "pbs_stderr_path": str(slot_output / "pbs.stderr.log"),
            "binary_source_path": str(source),
            "binary_sha256": expected_hash or _sha(source),
            "wrapper_path": str(package / "wrapper.py"), "wrapper_sha256": H,
            "runner_policy_path": str(runner_policy_path),
            "runner_policy_sha256": S.canonical_sha256(policy),
            "expected_dependency_manifest_sha256": _sha(dependency),
            "expected_module_list_sha256": H, "expected_numa_nodes": 4,
            "script_path": str(slot_work / "job.pbs"),
        })
    intent = {
        "schema_version": S.LAUNCH_INTENT_SCHEMA, "group_id": "group-1",
        "run_kind": "liveness", "attempt_ordinal": 1, "policy_sha256": H2,
        "preregistration_sha256": PREREG_SHA256, "prereg_approval_id": APPROVAL_ID,
        "created_at": "2026-08-12T00:00:00Z", "node_count": 13, "round_count": 10,
        "ready_timeout_seconds": 1200, "start_spread_max_ns": 5_000_000_000,
        "work_root": str(work), "output_root": str(output), "slots": slots,
    }
    manifest = {
        "schema_version": S.GROUP_MANIFEST_SCHEMA, "group_id": "group-1",
        "created_at": "2026-08-12T00:00:00Z",
        "launch_intent_sha256": S.canonical_sha256(intent),
        "guard_receipt_sha256": H, "budget_receipt_sha256": H,
        "release_token_commitment": S.release_token_commitment("release-nonce"),
    }
    manifest_sha = S.canonical_sha256(manifest)
    (control / "launch-intent.json").write_bytes(S.canonical_json_bytes(intent) + b"\n")
    (output / "group-manifest.json").write_bytes(S.canonical_json_bytes(manifest) + b"\n")
    release = {
        "schema_version": S.CONTROL_MARKER_SCHEMA,
        "group_manifest_sha256": manifest_sha, "group_id": "group-1", "kind": "release",
        "published_at": "2026-08-12T00:00:00Z", "nonce": "release-nonce",
    }
    (control / "release.json").write_bytes(S.canonical_json_bytes(release) + b"\n")
    witness = {
        "schema_version": S.LAUNCH_AUTHORIZATION_SCHEMA,
        "approval_id": APPROVAL_ID, "preregistration_sha256": PREREG_SHA256,
        "policy_sha256": H2, "run_kinds": ["liveness"],
        "issued_on": "2026-08-12", "nonce": "fixture-witness",
    }
    return W.WrapperRequest(
        group_manifest_sha256=manifest_sha, group_id="group-1", slot_id="slot-00",
        logical_request_id="logical-00", pbs_request_id="81000.server",
        run_kind="liveness", preregistration_sha256=PREREG_SHA256,
        prereg_approval_id=APPROVAL_ID, admission_policy_sha256=H2,
        launch_authorization=witness,
        release_token_commitment=S.release_token_commitment("release-nonce"),
        release_marker_path=control / "release.json",
        cancel_marker_path=control / "cancel.json",
        node_receipt_path=work / "slot-00/node-receipt.jsonl",
        request_path=work / "slot-00/wrapper-request.json",
        assigned_hostname="node00", allocated_cpus=frozenset({0, 1}),
        expected_submission_argv=tuple(slots[0]["qsub_argv"]),
        observed_submission_argv=tuple(slots[0]["qsub_argv"]), work_root=work,
        output_root=output, control_root=control, pbs_workdir=work / "slot-00",
        binary_source_path=source, binary_copy_path=work / "slot-00/CCBench-Silo",
        runner_policy_path=runner_policy_path,
        runner_policy_sha256=S.canonical_sha256(policy),
        dependency_manifest_path=dependency,
        expected_dependency_manifest_sha256=_sha(dependency),
        expected_module_list_sha256=H, expected_numa_nodes=4,
        round_count=10, interpreter_realpath=interpreter,
    )


def _hardware(numa=4):
    return {"cpu_model": "fixture", "physical_cores": 48, "hyperthreading": False,
            "memory": "128GiB", "numa_nodes": numa, "cache": ["L3"],
            "frequency_policy": "performance"}


def _probes(request: W.WrapperRequest, *, loads=None, scans=None, hardware=None,
            modules=None, traces=None, isolations=None):
    clock = FakeClock()
    loads = deque(loads or [0.5, 0.5, 0.5])
    scans = deque(scans or [W.ProcessScan((), ()), W.ProcessScan((), ())])
    hardware = deque(hardware or [_hardware(), _hardware()])
    modules = deque(modules or [H, H])
    traces = deque(traces or [(), ()])
    isolations = deque(isolations or [
        {"inventory_sha256": H, "competing_processes_sha256": H},
        {"inventory_sha256": H, "competing_processes_sha256": H},
    ])

    def take(queue):
        value = queue.popleft()
        if not queue:
            queue.append(value)
        return value

    probes = W.WrapperProbes(
        actual_hostname=lambda: "node00", hardware=lambda: take(hardware),
        interpreter=lambda: {"executable": str(request.interpreter_realpath),
                             "version": "3.10.12"},
        process_scan=lambda cpus: take(scans),
        load1_reader=lambda: take(loads), sleep=clock.sleep,
        monotonic_ns=clock.monotonic_ns, wall_clock=lambda: f"time-{clock.ns}",
        module_list_sha256=lambda: take(modules),
        trace_symbols=lambda path: take(traces), isolation=lambda: take(isolations),
        effective_clock=lambda: 2100,
    )
    return probes


def _measurement(request, *, mutate_after=False):
    calls = []

    def run(policy, executable, argv, token, *, cwd):
        lines = request.node_receipt_path.read_text(encoding="utf-8").splitlines()
        assert json.loads(lines[-1])["event"] == "start_ack" or calls
        assert isinstance(token, S.AuthorizationToken)
        calls.append((policy, executable, argv, token, cwd))
        if mutate_after and len(calls) == request.round_count:
            request.binary_copy_path.write_bytes(b"tampered-after-measurement")
        return subprocess.CompletedProcess(argv, 0, "123.5\n", "")

    return calls, run


def test_valid_wrapper_writes_ack_then_immediately_uses_single_measurement_seam(tmp_path):
    request = _request(tmp_path)
    calls, run = _measurement(request)
    result = W._run_wrapper(request, probes=_probes(request), measurement_run=run)
    assert result.state == "valid" and len(calls) == request.round_count
    assert [event["event"] for event in result.events] == [
        "preflight", "start_ack", "measurement", "terminal",
    ]
    assert all(event["limitations"] == W.LIMITATIONS for event in result.events)
    assert result.events[1]["payload"]["release_marker_sha256"] == S.canonical_sha256(
        S.validate_control_marker(json.loads(request.release_marker_path.read_text()))
    )
    measurements = request.output_root / request.slot_id / "measurements.jsonl"
    rows = [json.loads(line) for line in measurements.read_text().splitlines()]
    assert [row["index"] for row in rows] == list(range(1, 11))
    assert all("throughput" in row and "effective_clock" in row for row in rows)


def test_runner_policy_digest_must_remain_bound_to_published_intent(tmp_path):
    request = _request(tmp_path)
    forged = replace(request, runner_policy_sha256="f" * 64)
    with pytest.raises(W.T810WrapperError, match="intent or manifest"):
        W._run_wrapper(
            forged, probes=_probes(forged), measurement_run=_measurement(forged)[1],
        )
    assert not forged.node_receipt_path.exists()


@pytest.mark.parametrize(("phase", "expected_reason"), [
    ("source", "binary_copy_hash_mismatch"),
    ("copy", "binary_copy_hash_mismatch"),
    ("after", "binary_after_hash_mismatch"),
])
def test_binary_hash_mismatch_at_each_of_three_points_maps_to_frozen_state(
    tmp_path, monkeypatch, phase, expected_reason,
):
    request = _request(tmp_path, expected_hash=H if phase == "source" else None)
    if phase == "copy":
        expected = json.loads(request.runner_policy_path.read_text())["executable_sha256"]
        monkeypatch.setattr(
            W, "_copy_binary", lambda token, source, destination: (expected, H),
        )
    calls, run = _measurement(request, mutate_after=phase == "after")
    result = W._run_wrapper(request, probes=_probes(request), measurement_run=run)
    assert expected_reason in result.reason_codes
    assert result.state == ("incomplete_after_start" if phase == "after" else "pre_release_invalid")
    assert len(calls) == (request.round_count if phase == "after" else 0)


def test_second_cancel_check_observes_cancel_created_after_ack(tmp_path, monkeypatch):
    request = _request(tmp_path)
    original_append = W._append_event

    def append_then_cancel(token, bound_request, events, event, payload, observed_at):
        if event in {"preflight", "start_ack"}:
            assert not request.cancel_marker_path.exists()
        result = original_append(
            token, bound_request, events, event, payload, observed_at,
        )
        if event == "start_ack":
            request.cancel_marker_path.write_text("cancel-after-ack", encoding="utf-8")
        return result

    monkeypatch.setattr(W, "_append_event", append_then_cancel)
    calls, run = _measurement(request)
    result = W._run_wrapper(request, probes=_probes(request), measurement_run=run)
    assert result.state == "post_release_pre_measurement_invalid"
    assert result.reason_codes == ("cancel_marker_observed",) and calls == []
    assert [event["event"] for event in result.events] == [
        "preflight", "start_ack", "terminal",
    ]


def test_bad_release_recheck_never_measures(tmp_path):
    request = _request(tmp_path)
    value = json.loads(request.release_marker_path.read_text())
    value["nonce"] = "not-the-committed-nonce"
    request.release_marker_path.write_text(json.dumps(value), encoding="utf-8")
    calls, run = _measurement(request)
    result = W._run_wrapper(request, probes=_probes(request), measurement_run=run)
    assert result.state == "post_release_pre_measurement_invalid"
    assert result.reason_codes == ("release_marker_mismatch",) and calls == []


@pytest.mark.parametrize(("scan", "reason"), [
    (W.ProcessScan(({"pid": 9, "uid": 2, "cpu_affinity": [0], "command": "other"},), ()),
     "competing_process_detected"),
    (W.ProcessScan((), ({"pid": 9, "fields": ["uid"]},)),
     "process_observation_unreadable"),
])
def test_measurement_immediate_process_rescan_is_recorded_and_fail_closed(tmp_path, scan, reason):
    request = _request(tmp_path)
    probes = _probes(request, scans=[W.ProcessScan((), ()), scan])
    calls, run = _measurement(request)
    result = W._run_wrapper(request, probes=probes, measurement_run=run)
    assert result.state == "post_release_pre_measurement_invalid" and reason in result.reason_codes
    assert [event["event"] for event in result.events] == ["preflight", "terminal"]
    assert calls == []


def test_initial_uid_or_affinity_unreadability_is_pre_release_fail_closed(tmp_path):
    request = _request(tmp_path)
    unreadable = W.ProcessScan((), ({"pid": 9, "fields": ["uid", "cpu_affinity"]},))
    result = W._run_wrapper(
        request, probes=_probes(request, scans=[unreadable, W.ProcessScan((), ())]),
        measurement_run=_measurement(request)[1],
    )
    assert result.state == "pre_release_invalid"
    evidence = result.events[0]["payload"]["competing_processes"]
    assert evidence == [{"pid": 9, "uid": None, "cpu_affinity": None,
                         "command": "<unreadable:uid,cpu_affinity>"}]


@pytest.mark.parametrize("kind", ["dependency", "module", "trace", "numa"])
def test_post_release_inventory_and_trace_rechecks_map_to_state_two(tmp_path, kind):
    request = _request(tmp_path)
    kwargs = {}
    if kind == "module":
        kwargs["modules"] = [H, H2]
    elif kind == "trace":
        kwargs["traces"] = [(), ("trace_symbol",)]
    elif kind == "numa":
        kwargs["hardware"] = [_hardware(), _hardware(2)]
    elif kind == "dependency":
        first, second = W.ProcessScan((), ()), W.ProcessScan((), ())
        calls = 0

        def scan(cpus):
            nonlocal calls
            calls += 1
            if calls == 2:
                request.dependency_manifest_path.write_bytes(b"changed")
            return first if calls == 1 else second

        probes = _probes(request)
        probes = replace(probes, process_scan=scan)
    probes = probes if kind == "dependency" else _probes(request, **kwargs)
    result = W._run_wrapper(request, probes=probes, measurement_run=_measurement(request)[1])
    reason = {"dependency": "dependency_manifest_mismatch", "module": "module_list_mismatch",
              "trace": "trace_symbols_present", "numa": "numa_nodes_mismatch"}[kind]
    assert result.state == "post_release_pre_measurement_invalid" and reason in result.reason_codes
    assert [event["event"] for event in result.events] == ["preflight", "terminal"]


def test_node_repo_absence_never_claims_unprovable_positive(tmp_path):
    request = _request(tmp_path)
    assert W.inspect_repository_absence(request, repo_root=REPO) == {
        "package_repo_free": False,
        "roots_repo_external": False,
        "git_ancestor_absent": False,
        "pbs_workdir_repo_external": False,
    }
    assert W.LIMITATIONS["shared_mount_repository_reachability_not_eliminated"] is True
    assert W.LIMITATIONS["repository_absence_not_proven_from_node"] is True


@pytest.mark.parametrize("marker_kind", ["directory", "worktree-file"])
def test_git_directory_and_git_worktree_file_are_denied_before_release(tmp_path, marker_kind):
    request = _request(tmp_path)
    marker = request.pbs_workdir / ".git"
    if marker_kind == "directory":
        marker.mkdir()
    else:
        marker.write_text("gitdir: /external/worktree-meta\n", encoding="utf-8")
    result = W._run_wrapper(
        request, probes=_probes(request), measurement_run=_measurement(request)[1],
    )
    assert result.state == "pre_release_invalid" and "preflight_failed" in result.reason_codes


def test_repo_alias_and_repo_internal_pbs_workdir_are_denied(tmp_path):
    request = replace(_request(tmp_path), pbs_workdir=REPO / "tools")
    absence = W.inspect_repository_absence(request, repo_root=REPO)
    assert absence["roots_repo_external"] is False
    assert absence["pbs_workdir_repo_external"] is False
    assert W._repository_hazard_observed(request) is True


@pytest.mark.parametrize("change", ["missing", "extra"])
def test_hardware_schema_requires_exact_seven_fields(change):
    hardware = _hardware()
    if change == "missing":
        hardware.pop("cache")
    else:
        hardware["unexpected"] = "x"
    with pytest.raises(W.T810WrapperError, match="exact seven"):
        W._validate_hardware(hardware)


def test_ccbench_stdout_throughput_parser_accepts_primary_and_exact_fallback():
    assert W._parse_throughput("throughput[tps]:\t123.5\n") == 123.5
    assert W._parse_throughput("commit_counts_:\t500\nactual_extime:\t2.0\n") == 250.0
    with pytest.raises(W.T810WrapperError):
        W._parse_throughput("throughput unavailable\n")


def test_ast_tripwire_allows_subprocess_only_in_fixed_policy_runner():
    module_paths = {
        "schema": Path(S.__file__), "coordinator": Path(C.__file__),
        "wrapper": Path(W.__file__), "runner": Path(R.__file__),
        "guard": Path(G.__file__), "budget": Path(B.__file__),
    }

    def subprocess_calls(tree):
        parents = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent
        found = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            owner = node.func.value
            if isinstance(owner, ast.Name) and (
                (owner.id == "subprocess" and node.func.attr in {"run", "Popen", "call", "check_call", "check_output"})
                or (owner.id == "os" and node.func.attr in {"system", "popen", "spawnl", "spawnv"})
            ):
                current = node
                while current in parents and not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    current = parents[current]
                found.append((node.func.attr, getattr(current, "name", None)))
        return found

    actual = {
        name: subprocess_calls(ast.parse(path.read_text(encoding="utf-8")))
        for name, path in module_paths.items()
    }
    assert actual == {
        "schema": [], "coordinator": [("run", "_subprocess_scheduler")],
        "wrapper": [], "runner": [("run", "_subprocess_runner")],
        "guard": [], "budget": [],
    }
    source = module_paths["wrapper"].read_text(encoding="utf-8")
    assert source.count("measurement_run(") == 1
    assert source.count("measurement_run=runner_policy.run_allowed_measurement") == 1
