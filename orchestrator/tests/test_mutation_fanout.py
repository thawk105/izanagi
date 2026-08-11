"""Mutation fan-out driver の admission・待機・残渣・qdel 契約を検査する。"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


_REPO = Path(__file__).resolve().parents[2]
_TOOLS = _REPO / "tools"
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from orchestrator.campaign import login_headroom  # noqa: E402

_TOOL = _TOOLS / "mutation_fanout.py"
_SPEC = importlib.util.spec_from_file_location("mutation_fanout_under_test", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
MF = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = MF
_SPEC.loader.exec_module(MF)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _mutation(index: int, *, hang: bool = False) -> dict[str, Any]:
    return {
        "id": f"M{index}",
        "category": "negative",
        "replacements": [
            {"file": "target.py", "old": f"M{index} = 0", "new": f"M{index} = 1"}
        ],
        "expected_nodes": [f"tests/test_gate.py::test_m{index}"],
        "expected_status": "KILLED",
        "hang_risk": hang,
    }


def _parent_bytes() -> bytes:
    return (
        json.dumps(
            {
                "schema": "izanagi-dev-wave-mutation-spec/v1",
                "estimated_run_seconds": 30,
                "timeout_seconds": 120,
                "hang_timeout_seconds": 360,
                "mutations": [
                    _mutation(1, hang=True),
                    _mutation(2),
                    _mutation(3, hang=True),
                    _mutation(4),
                ],
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode()


def _fake_wrapper_source() -> str:
    return r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
out = Path(args[args.index("--out") + 1])
shard_id = out.parent.name
root = out.parents[2]
report = json.loads((root / "driver-report.json").read_text(encoding="utf-8"))
group = json.loads((root / "group.json").read_text(encoding="utf-8"))
assignment = json.loads((root / "assignment.json").read_text(encoding="utf-8"))
assert len(report["shards"]) == report["shard_count"]
assert all(item["pid"] is not None and item["starttime"] is not None for item in report["shards"])
assert len(group["shards"]) == report["shard_count"]
assert len(assignment["shards"]) == report["shard_count"]
assert all(Path(item["spec_path"]).is_file() for item in group["shards"])
marker = os.environ.get("IZANAGI_FANOUT_RESERVATION_MARKER")
assert marker is None or Path(marker).is_file()
calls = root / "wrapper-calls.txt"
descriptor = os.open(calls, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
    stream.write(shard_id + "\n")
rcs = [int(item) for item in os.environ.get("IZANAGI_FANOUT_FAKE_RCS", "0,0").split(",")]
raise SystemExit(rcs[int(shard_id.rsplit("-", 1)[1])])
'''


@pytest.fixture
def source_repo(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "source"
    (source / "tools").mkdir(parents=True)
    (source / "tools" / "mutation_worktree.py").write_text(
        _fake_wrapper_source(), encoding="utf-8"
    )
    (source / "tools" / "mutation_fanout.py").write_bytes(_TOOL.read_bytes())
    (source / "target.py").write_text("M1 = 0\n", encoding="utf-8")
    _git(source, "init", "-q")
    _git(source, "config", "user.email", "fanout@example.invalid")
    _git(source, "config", "user.name", "Fanout Test")
    _git(source, "add", ".")
    _git(source, "commit", "-qm", "fixture")
    return source, _git(source, "rev-parse", "HEAD")


def _binding(
    tmp_path: Path,
    source_repo: tuple[Path, str],
    *,
    runner_argv: tuple[str, ...] = ("python3", "tools/run_tests.py", "tests/test_gate.py", "-q"),
    shard_count: int = 2,
) -> tuple[MF.FanoutConfig, dict[str, Any], SimpleNamespace]:
    source, commit = source_repo
    parent = tmp_path / "parent.json"
    parent_bytes = _parent_bytes()
    parent.write_bytes(parent_bytes)
    parent_sha = hashlib.sha256(parent_bytes).hexdigest()
    assignment, shards = MF.derive_split(
        parent_bytes,
        expected_parent_sha256=parent_sha,
        shard_count=shard_count,
    )
    assignment_sha = hashlib.sha256(MF.canonical_json_bytes(assignment)).hexdigest()
    input_bytes, input_count = MF._input_binding(assignment, shards)
    receipt_path = tmp_path / "admission.json"
    config = MF.FanoutConfig(
        source_repo=source,
        commit=commit,
        parent_spec=parent,
        expected_parent_sha256=parent_sha,
        shard_count=shard_count,
        group_root=tmp_path / "fanout-group",
        admission_receipt=receipt_path,
        runner_argv=runner_argv,
        poll_interval_s=0.005,
        barrier_timeout_s=10,
    )
    group_shards, _driver_shards = MF._shard_documents(config.group_root, assignment)
    outer_argv = [
        MF._wrapper_argv(
            config,
            commit=commit,
            assignment_shard=assignment_shard,
            group_shard=group_shard,
        )
        for assignment_shard, group_shard in zip(
            assignment["shards"], group_shards, strict=True
        )
    ]
    peak = 20_000_000
    certified = peak + MF.CERTIFICATION_MIN_MARGIN_BYTES
    memory_max = login_headroom.CEILING_BYTES
    identity = {
        "repo_path": "tools/mutation_fanout.py",
        "path": str(_TOOL.resolve()),
        "sha256": hashlib.sha256(_TOOL.read_bytes()).hexdigest(),
        "head_blob_sha256": hashlib.sha256(_TOOL.read_bytes()).hexdigest(),
    }
    log_refs = []
    for repetition, sample_peak in enumerate((18_000_000, 19_000_000, peak), 1):
        log = {
            "schema": MF.MEASUREMENT_SCHEMA,
            "repetition": repetition,
            "commit": commit,
            "cgroup_path": f"/sys/fs/cgroup/user.slice/calibration-{repetition}.scope",
            "memory_max_bytes": memory_max,
            "outer_argv": outer_argv,
            "input_bytes": input_bytes,
            "input_count": input_count,
            "samples": [
                {"monotonic_ns": 1, "memory_current_bytes": sample_peak - 1},
                {"monotonic_ns": 2, "memory_current_bytes": sample_peak},
            ],
            "child_returncodes": [0] * shard_count,
        }
        log_path = tmp_path / f"measurement-{repetition}.json"
        log_bytes = json.dumps(log, sort_keys=True).encode()
        log_path.write_bytes(log_bytes)
        log_refs.append(
            {"path": str(log_path), "sha256": hashlib.sha256(log_bytes).hexdigest()}
        )
    receipt = {
        "schema": MF.ADMISSION_SCHEMA,
        "measured_at": "2026-08-11T12:00:00+09:00",
        "commit": commit,
        "parent_spec_sha256": parent_sha,
        "assignment_sha256": assignment_sha,
        "shard_count": shard_count,
        "outer_argv_sha256": hashlib.sha256(
            MF.canonical_json_bytes(outer_argv)
        ).hexdigest(),
        "input_bytes": input_bytes,
        "input_count": input_count,
        "memory_max_bytes": memory_max,
        "producer_identity": identity,
        "sampler_identity": identity,
        "measurement_logs": log_refs,
        "certified_peak_bytes": certified,
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    observation = SimpleNamespace(
        memory_max_bytes=receipt["memory_max_bytes"],
        cgroup_path=tmp_path / "fake-cgroup",
    )
    return config, receipt, observation


@contextlib.contextmanager
def _local_reservation(estimate: int, *, scope_cgroup: Path):
    assert estimate > 0
    assert scope_cgroup.name == "fake-cgroup"
    yield (SimpleNamespace(value="local"), "fixture reservation")


def _merger(result_rc: int, calls: list[list[int]]):
    def merge(_parent: Path, **kwargs: Any) -> dict[str, Any]:
        group = json.loads(kwargs["group_manifest_path"].read_text(encoding="utf-8"))
        rcs = [shard["wrapper_rc"] for shard in group["shards"]]
        calls.append(rcs)
        kwargs["output_path"].write_text("{}\n", encoding="utf-8")
        return {"result_rc": result_rc}

    return merge


def test_run_persists_complete_invocation_set_before_barrier_and_keeps_rc1_terminal(
    tmp_path: Path,
    source_repo: tuple[Path, str],
    monkeypatch: pytest.MonkeyPatch,
):
    config, _receipt, observation = _binding(tmp_path, source_repo)
    monkeypatch.setenv("IZANAGI_FANOUT_FAKE_RCS", "0,1")
    marker = config.group_root / "reservation-held"
    monkeypatch.setenv("IZANAGI_FANOUT_RESERVATION_MARKER", str(marker))
    merge_calls: list[list[int]] = []

    @contextlib.contextmanager
    def held_reservation(estimate: int, *, scope_cgroup: Path):
        assert estimate > 0 and scope_cgroup.name == "fake-cgroup"
        marker.write_text("held\n", encoding="utf-8")
        try:
            yield (SimpleNamespace(value="local"), "held fixture reservation")
        finally:
            marker.unlink()

    rc = MF.run_fanout(
        config,
        observation=lambda: observation,
        reserve_factory=held_reservation,
        scope_attestation=lambda _cap: observation.cgroup_path,
        measurement_attestation=lambda _path, _peak, _maximum: True,
        merger=_merger(1, merge_calls),
    )

    assert rc == 1
    assert not marker.exists()
    assert merge_calls == [[0, 1]]
    root = config.group_root
    report = json.loads((root / "driver-report.json").read_text(encoding="utf-8"))
    assignment = json.loads((root / "assignment.json").read_text(encoding="utf-8"))
    calls = (root / "wrapper-calls.txt").read_text(encoding="utf-8").splitlines()
    assert sorted(calls) == ["shard-000", "shard-001"]
    assert report["state"] == "finished"
    assert report["expected_invocation_count"] == 4 + 2 * 2
    assert len(report["expected_invocations"]) == report["expected_invocation_count"]
    assert Counter(item["phase"] for item in report["expected_invocations"]) == {
        "collection": 2,
        "baseline": 2,
        "mutation": 4,
    }
    assert assignment["shard_count"] == 2
    assert [item["rc"] for item in report["shards"]] == [0, 1]
    assert all(Path(item["rc_path"]).is_file() for item in report["shards"])
    assert all(Path(item["done_path"]).is_file() for item in report["shards"])
    group = json.loads((root / "group.json").read_text(encoding="utf-8"))
    scratch = [item["expected_paths"]["scratch_root"] for item in group["shards"]]
    ledgers = [item["ledger_path"] for item in group["shards"]]
    receipts = [item["wrapper_receipt_path"] for item in group["shards"]]
    evidence = [str(Path(item["ledger_path"] + ".dispatch-evidence")) for item in group["shards"]]
    locks = [item["expected_paths"]["lock_path"] for item in group["shards"]]
    for paths in (scratch, ledgers, receipts, evidence, locks):
        assert len(paths) == len(set(paths)) == 2


def test_nonterminal_shard_does_not_retry_or_merge(
    tmp_path: Path,
    source_repo: tuple[Path, str],
    monkeypatch: pytest.MonkeyPatch,
):
    config, _receipt, observation = _binding(tmp_path, source_repo)
    monkeypatch.setenv("IZANAGI_FANOUT_FAKE_RCS", "0,125")
    merge_calls: list[list[int]] = []

    rc = MF.run_fanout(
        config,
        observation=lambda: observation,
        reserve_factory=_local_reservation,
        scope_attestation=lambda _cap: observation.cgroup_path,
        measurement_attestation=lambda _path, _peak, _maximum: True,
        merger=_merger(0, merge_calls),
    )

    assert rc == 2
    assert merge_calls == []
    calls = (config.group_root / "wrapper-calls.txt").read_text(encoding="utf-8").splitlines()
    assert Counter(calls) == {"shard-000": 1, "shard-001": 1}
    report = json.loads((config.group_root / "driver-report.json").read_text(encoding="utf-8"))
    assert [item["rc"] for item in report["shards"]] == [0, 125]
    assert "successful shards were not retried" in report["failure"]


def test_scope_reexec_applies_one_memory_limit_to_the_driver_and_all_descendants():
    captured: dict[str, Any] = {}

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        captured.update({"command": command, **kwargs})
        return subprocess.CompletedProcess(command, 0)

    assert MF._run_in_bounded_scope(["run", "--sentinel"], 123456, run_command=run) == 0
    command = captured["command"]
    assert command[:4] == ["systemd-run", "--user", "--scope", "-q"]
    assert "MemoryAccounting=yes" in command
    assert "MemoryMax=123456" in command
    assert "MemorySwapMax=0" in command
    unit = captured["env"][MF._BOUNDED_SCOPE_UNIT_ENV]
    assert f"--unit={unit}" in command
    assert captured["env"][MF._BOUNDED_SCOPE_CAP_ENV] == "123456"


def test_receipt_for_another_n_is_unknown_and_never_launches_or_clips(
    tmp_path: Path,
    source_repo: tuple[Path, str],
):
    config, receipt, observation = _binding(tmp_path, source_repo)
    receipt["shard_count"] = 1
    config.admission_receipt.write_text(json.dumps(receipt), encoding="utf-8")
    launches: list[Any] = []

    rc = MF.run_fanout(
        config,
        observation=lambda: observation,
        reserve_factory=_local_reservation,
        scope_attestation=lambda _cap: observation.cgroup_path,
        measurement_attestation=lambda _path, _peak, _maximum: True,
        popen_factory=lambda *args, **kwargs: launches.append((args, kwargs)),
    )

    assert rc == 2
    assert launches == []
    assignment = json.loads((config.group_root / "assignment.json").read_text(encoding="utf-8"))
    report = json.loads((config.group_root / "driver-report.json").read_text(encoding="utf-8"))
    assert assignment["shard_count"] == report["shard_count"] == 2
    assert report["admission"]["decision"] == "unknown"
    assert "shard_count" in report["failure"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("commit", "0" * 40),
        ("outer_argv_sha256", "0" * 64),
        ("input_bytes", 1),
        ("input_count", 1),
        ("memory_max_bytes", 1),
        ("measurement_logs", "drop-one"),
        ("producer_identity", "wrong-producer"),
    ],
)
def test_admission_rejects_unmeasured_or_mismatched_receipt(
    tmp_path: Path,
    source_repo: tuple[Path, str],
    field: str,
    value: Any,
):
    config, receipt, observation = _binding(tmp_path, source_repo)
    if value == "drop-one":
        receipt[field] = receipt[field][:2]
    elif value == "wrong-producer":
        receipt[field] = {**receipt[field], "sha256": "0" * 64}
    else:
        receipt[field] = value
    assignment, shards = MF.derive_split(
        config.parent_spec.read_bytes(),
        expected_parent_sha256=config.expected_parent_sha256,
        shard_count=config.shard_count,
    )
    input_bytes, input_count = MF._input_binding(assignment, shards)
    group_shards, _ = MF._shard_documents(config.group_root, assignment)
    outer_argv = [
        MF._wrapper_argv(
            config,
            commit=config.commit,
            assignment_shard=assignment_shard,
            group_shard=group_shard,
        )
        for assignment_shard, group_shard in zip(
            assignment["shards"], group_shards, strict=True
        )
    ]
    identity = MF._execution_identities(config.source_repo, config.commit)["driver"]
    with pytest.raises(MF.FanoutDriverError):
        MF.validate_admission_receipt(
            receipt,
            commit=config.commit,
            parent_spec_sha256=config.expected_parent_sha256,
            assignment_sha256=hashlib.sha256(MF.canonical_json_bytes(assignment)).hexdigest(),
            shard_count=config.shard_count,
            outer_argv=outer_argv,
            input_bytes=input_bytes,
            input_count=input_count,
            memory_max_bytes=observation.memory_max_bytes,
            producer_identity=identity,
            cgroup_attestation=lambda _path, _peak, _maximum: True,
        )


def test_admission_rejects_when_measurement_scope_is_not_live_kernel_evidence(
    tmp_path: Path,
    source_repo: tuple[Path, str],
):
    config, _receipt, observation = _binding(tmp_path, source_repo)
    launches: list[Any] = []

    rc = MF.run_fanout(
        config,
        observation=lambda: observation,
        reserve_factory=_local_reservation,
        scope_attestation=lambda _cap: observation.cgroup_path,
        measurement_attestation=lambda _path, _peak, _maximum: False,
        popen_factory=lambda *args, **kwargs: launches.append((args, kwargs)),
    )

    assert rc == 2
    assert launches == []
    report = json.loads(
        (config.group_root / "driver-report.json").read_text(encoding="utf-8")
    )
    assert "kernel" in report["failure"]


def test_missing_bounded_scope_stops_before_any_wrapper_launch(
    tmp_path: Path,
    source_repo: tuple[Path, str],
):
    config, _receipt, observation = _binding(tmp_path, source_repo)
    launches: list[Any] = []

    rc = MF.run_fanout(
        config,
        observation=lambda: observation,
        reserve_factory=_local_reservation,
        scope_attestation=lambda _cap: None,
        measurement_attestation=lambda _path, _peak, _maximum: True,
        popen_factory=lambda *args, **kwargs: launches.append((args, kwargs)),
    )

    assert rc == 2
    assert launches == []
    report = json.loads(
        (config.group_root / "driver-report.json").read_text(encoding="utf-8")
    )
    assert "bounded cgroup scope" in report["failure"]


def test_dirty_wrapper_is_rejected_against_fixed_head_before_group_creation(
    tmp_path: Path,
    source_repo: tuple[Path, str],
):
    config, _receipt, observation = _binding(tmp_path, source_repo)
    wrapper = config.source_repo / "tools" / "mutation_worktree.py"
    wrapper.write_text(wrapper.read_text(encoding="utf-8") + "# dirty\n", encoding="utf-8")

    with pytest.raises(MF.FanoutDriverError, match="固定 HEAD blob"):
        MF.run_fanout(
            config,
            observation=lambda: observation,
            reserve_factory=_local_reservation,
            scope_attestation=lambda _cap: observation.cgroup_path,
            measurement_attestation=lambda _path, _peak, _maximum: True,
        )
    assert not config.group_root.exists()


def test_dirty_driver_copy_cannot_claim_the_fixed_head_identity(
    tmp_path: Path,
    source_repo: tuple[Path, str],
):
    source, commit = source_repo
    dirty = tmp_path / "dirty" / "mutation_fanout.py"
    dirty.parent.mkdir()
    dirty.write_bytes(_TOOL.read_bytes() + b"# dirty driver\n")
    spec = importlib.util.spec_from_file_location("dirty_mutation_fanout", dirty)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    with pytest.raises(module.FanoutDriverError, match="固定 HEAD blob"):
        module._execution_identities(source, commit)


def test_group_root_inside_registered_worktree_is_rejected_before_creation(
    tmp_path: Path,
    source_repo: tuple[Path, str],
):
    config, _receipt, observation = _binding(tmp_path, source_repo)
    source, _commit = source_repo
    forbidden = source / "fanout-group"
    config = MF.dataclasses.replace(config, group_root=forbidden)

    with pytest.raises(MF.FanoutDriverError, match="registered worktree"):
        MF.run_fanout(
            config,
            observation=lambda: observation,
            reserve_factory=_local_reservation,
            scope_attestation=lambda _cap: observation.cgroup_path,
            measurement_attestation=lambda _path, _peak, _maximum: True,
        )
    assert not forbidden.exists()


def test_unexpected_registered_worktree_is_reported_without_merge_or_removal(
    tmp_path: Path,
    source_repo: tuple[Path, str],
    monkeypatch: pytest.MonkeyPatch,
):
    config, _receipt, observation = _binding(tmp_path, source_repo)
    source, _commit = source_repo
    initial = (str(source.resolve()),)
    extra = str((tmp_path / "other-session-worktree").resolve())
    snapshots = iter(((initial, "initial\n"), ((initial[0], extra), "final\n")))
    merge_calls: list[list[int]] = []
    monkeypatch.setenv("IZANAGI_FANOUT_FAKE_RCS", "0,0")

    rc = MF.run_fanout(
        config,
        observation=lambda: observation,
        reserve_factory=_local_reservation,
        scope_attestation=lambda _cap: observation.cgroup_path,
        measurement_attestation=lambda _path, _peak, _maximum: True,
        snapshot=lambda _source: next(snapshots),
        merger=_merger(0, merge_calls),
    )

    assert rc == 2
    assert merge_calls == []
    report = json.loads((config.group_root / "driver-report.json").read_text(encoding="utf-8"))
    assert report["unexpected_worktrees"] == [extra]
    assert "worktree registry residue/change" in report["failure"]
    source_text = _TOOL.read_text(encoding="utf-8")
    assert "worktree remove" not in source_text
    assert "worktree prune" not in source_text


def _request_attempt(
    tmp_path: Path, name: str, ordinal: int, *, receipt_id: str | None = None
) -> dict[str, Any]:
    submission = tmp_path / f"submission-{ordinal}"
    receipt = submission / "receipt.json"
    submission.mkdir(parents=True)
    job_name = f"izdw-{submission.name[:10]}"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": "pegasus-dispatch-receipt/v2",
                "request_id": receipt_id or name,
                "submission_dir": str(submission),
                "request": {"job_name": job_name},
            }
        ),
        encoding="utf-8",
    )
    return {
        "run_attempt_ordinal": ordinal,
        "wrapper_attempt_ordinal": 1,
        "phase": "mutation",
        "mutation_id": f"M{ordinal}",
        "state": "finished",
        "started_at": "2026-08-11T00:00:00+00:00",
        "finished_at": "2026-08-11T00:00:01+00:00",
        "rc": 2,
        "timed_out": False,
        "artifact_error": None,
        "console_sha256": "0" * 64,
        "request": {
            "request_id": name,
            "submission_dir": str(submission),
            "receipt_path": str(receipt),
            "job_stdout_path": None,
            "outcome_rc": None,
        },
    }


def test_qdel_is_limited_to_receipt_bound_owned_que_or_hld(tmp_path: Path):
    names = [
        "que.server",
        "hld.server",
        "run.server",
        "foreign.server",
        "missing.server",
        "mismatch.server",
        "wrongname.server",
    ]
    attempt_path = tmp_path / "attempts.json"
    attempts = [
        _request_attempt(
            tmp_path,
            name,
            ordinal,
            receipt_id="other.server" if name == "mismatch.server" else None,
        )
        for ordinal, name in enumerate(names, 1)
    ]
    attempt_path.write_text(
        json.dumps(
            {
                "schema": MF.ATTEMPT_SCHEMA,
                "repo_head": "a" * 40,
                "spec_sha256": "1" * 64,
                "runner_sha256": "2" * 64,
                "tool_sha256": "3" * 64,
                "expected_initial_requests": len(attempts),
                "attempts": attempts,
            }
        ),
        encoding="utf-8",
    )
    group = {
        "schema": MF.GROUP_SCHEMA,
        "parent_spec_sha256": "4" * 64,
        "assignment_sha256": "5" * 64,
        "shards": [
            {
                "index": 0,
                "shard_id": "shard-000",
                "spec_path": str(tmp_path / "spec.json"),
                "ledger_path": str(tmp_path / "ledger.json"),
                "wrapper_receipt_path": str(tmp_path / "wrapper.json"),
                "attempt_path": str(attempt_path),
                "wrapper_attempt_ordinal": 1,
                "wrapper_rc": 2,
                "expected_paths": {},
            }
        ]
    }
    commands: list[list[str]] = []

    def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        assert cwd == tmp_path
        commands.append(command)
        request_id = command[-1]
        if command[0] == "qdel":
            return subprocess.CompletedProcess(command, 0, "", "")
        if request_id == "missing.server":
            return subprocess.CompletedProcess(command, 153, "", "Unknown Job Id")
        state = {
            "que.server": "Q",
            "hld.server": "H",
            "run.server": "R",
            "foreign.server": "Q",
            "wrongname.server": "Q",
        }[request_id]
        owner = "other" if request_id == "foreign.server" else "tester"
        observed_name = "other-session" if request_id == "wrongname.server" else "izdw-submission"
        stdout = (
            f"Job Id: {request_id}\n"
            f"    Job_Owner = {owner}@login\n"
            f"    job_state = {state}\n"
            f"    Job_Name = {observed_name}\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout, "")

    actions = MF.inspect_or_cancel_owned_requests(
        group,
        cwd=tmp_path,
        cancel=True,
        expected_group_authority=MF._group_authority_sha256(group),
        expected_commit="a" * 40,
        expected_owner="tester",
        run_command=run,
    )

    assert [command for command in commands if command[0] == "qdel"] == [
        ["qdel", "que.server"],
        ["qdel", "hld.server"],
    ]
    by_id = {item["request_id"]: item for item in actions}
    assert by_id["run.server"]["qdel_attempted"] is False
    assert by_id["foreign.server"]["reason"] == "owner-unknown-or-mismatch"
    assert by_id["missing.server"]["reason"] == "request-not-visible"
    assert by_id["missing.server"]["scheduler_state"] == "unknown"
    assert by_id["mismatch.server"]["reason"] == "receipt-request-id-mismatch"
    assert by_id["wrongname.server"]["reason"] == "job-name-unknown-or-mismatch"
    assert [command for command in commands if command[-1] == "mismatch.server"] == []

    commands.clear()
    unauthorized = MF.inspect_or_cancel_owned_requests(
        group,
        cwd=tmp_path,
        cancel=True,
        expected_group_authority="0" * 64,
        expected_commit="a" * 40,
        expected_owner="tester",
        run_command=run,
    )
    assert [command for command in commands if command[0] == "qdel"] == []
    unauthorized_by_id = {
        item["request_id"]: item for item in unauthorized if "request_id" in item
    }
    assert unauthorized_by_id["que.server"]["scheduler_state"] == "QUE"
    assert unauthorized_by_id["que.server"]["reason"] == "group-or-attempt-authority-unproven"


def test_null_attempt_and_orphan_receipt_remain_in_remote_job_report(tmp_path: Path):
    attempt_path = tmp_path / "attempts.json"
    attempt_path.write_text(
        json.dumps(
            {
                "schema": MF.ATTEMPT_SCHEMA,
                "repo_head": "a" * 40,
                "spec_sha256": "1" * 64,
                "runner_sha256": "2" * 64,
                "tool_sha256": "3" * 64,
                "expected_initial_requests": 1,
                "attempts": [
                    {
                        "run_attempt_ordinal": 1,
                        "wrapper_attempt_ordinal": 1,
                        "phase": "mutation",
                        "mutation_id": "M1",
                        "state": "finished",
                        "started_at": "2026-08-11T00:00:00+00:00",
                        "finished_at": "2026-08-11T00:00:01+00:00",
                        "rc": None,
                        "timed_out": True,
                        "artifact_error": "timeout",
                        "console_sha256": "0" * 64,
                        "request": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    evidence = tmp_path / "relocated-evidence"
    submission = evidence / "nonce-orphan"
    submission.mkdir(parents=True)
    receipt = submission / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": "pegasus-dispatch-receipt/v2",
                "request_id": "orphan.server",
                "submission_dir": "/old/checkout/output/pegasus-dispatch/nonce-orphan",
                "request": {"job_name": "izdw-nonce-orph"},
            }
        ),
        encoding="utf-8",
    )
    wrapper_path = tmp_path / "wrapper.json"
    wrapper_path.write_text(
        json.dumps(
            {
                "dispatch_evidence": {
                    "original_path": "/old/checkout/output/pegasus-dispatch",
                    "relocated_path": str(evidence),
                }
            }
        ),
        encoding="utf-8",
    )
    group = {
        "schema": MF.GROUP_SCHEMA,
        "parent_spec_sha256": "4" * 64,
        "assignment_sha256": "5" * 64,
        "shards": [
            {
                "index": 0,
                "shard_id": "shard-000",
                "spec_path": str(tmp_path / "spec.json"),
                "ledger_path": str(tmp_path / "ledger.json"),
                "wrapper_receipt_path": str(wrapper_path),
                "attempt_path": str(attempt_path),
                "wrapper_attempt_ordinal": 1,
                "wrapper_rc": 2,
                "expected_paths": {},
            }
        ],
    }
    commands: list[list[str]] = []

    def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            "Job Id: orphan.server\n"
            "    Job_Owner = tester@login\n"
            "    job_state = R\n"
            "    Job_Name = izdw-nonce-orph\n",
            "",
        )

    actions = MF.inspect_or_cancel_owned_requests(
        group,
        cwd=tmp_path,
        cancel=True,
        expected_group_authority=MF._group_authority_sha256(group),
        expected_commit="a" * 40,
        expected_owner="tester",
        run_command=run,
    )

    null_action = next(item for item in actions if item.get("mutation_id") == "M1")
    orphan_action = next(item for item in actions if item.get("request_id") == "orphan.server")
    assert null_action["reason"] == "request-unresolved"
    assert null_action["qstat_attempted"] is False
    assert orphan_action["scheduler_state"] == "RUN"
    assert orphan_action["reason"] == "state-not-cancellable"
    assert [command for command in commands if command[0] == "qdel"] == []


def test_preserved_container_report_names_shard_and_human_owner(tmp_path: Path):
    container = tmp_path / "scratch" / MF.CONTAINER_NAME
    container.mkdir(parents=True)
    wrapper = tmp_path / "ledger.json.wrapper-receipt.json"
    wrapper.write_text(json.dumps({"container_preserved": True}), encoding="utf-8")
    group = {
        "shards": [
            {
                "shard_id": "shard-003",
                "wrapper_receipt_path": str(wrapper),
                "expected_paths": {"container_path": str(container)},
            }
        ]
    }

    assert MF._preserved_containers(group) == [
        {
            "shard_id": "shard-003",
            "container_path": str(container),
            "exists": True,
            "wrapper_receipt_container_preserved": True,
            "owner": "human-direction-required",
        }
    ]


def test_driver_source_has_no_shell_waiter_or_pattern_pid_detection():
    source = _TOOL.read_text(encoding="utf-8")
    for forbidden in ("pgrep", "xargs", "dev_wave_wait", "shell=True"):
        assert forbidden not in source
    assert source.count("while remaining:") == 1
    assert "child.process.poll()" in source
    assert "_process_identity_alive(child.pid, child.starttime)" in source


def _run() -> int:
    """新規 test file を repository の plain-runner 契約へ含める。"""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
