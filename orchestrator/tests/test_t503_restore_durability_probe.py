# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / "tools/pegasus/probes/t503_restore_durability_probe.py"
WRITER_PBS = ROOT / "tools/pegasus/probes/t503_restore_durability_probe.pbs"
RECOVERY_PBS = ROOT / "tools/pegasus/probes/t503_restore_durability_recover.pbs"
WRITER_PBS_SHA256 = hashlib.sha256(WRITER_PBS.read_bytes()).hexdigest()
RECOVERY_PBS_SHA256 = hashlib.sha256(RECOVERY_PBS.read_bytes()).hexdigest()
SPEC = importlib.util.spec_from_file_location("t503_restore_durability_probe", DRIVER)
assert SPEC is not None and SPEC.loader is not None
T503 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = T503
SPEC.loader.exec_module(T503)


def _classifications(root: Path, armed: dict) -> list[str]:
    values = []
    for item in armed["targets"]:
        digest = hashlib.sha256((root / item["rel"]).read_bytes()).hexdigest()
        values.append(T503.classify(digest, item["original_sha256"], item["mutated_sha256"]))
    return values


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _run_writer(root: Path, mode: str, *args, **kwargs):
    kwargs.setdefault("pbs_sha256", WRITER_PBS_SHA256)
    return T503.run_writer(root, mode, *args, **kwargs)


def _inspect_and_crash(root: Path, *, partial=False) -> None:
    result, rc = T503.run_inspect(
        root, WRITER_PBS_SHA256, allow_same_host=True,
        expect_partial_prefix=partial)
    assert rc == 0
    result["rc"] = rc
    output = root / "inspect.json"
    _write_json(output, result)
    _write_json(root / "inspect-receipt", T503._inspect_receipt(
        root, result, "recovery.1", output, RECOVERY_PBS_SHA256))
    T503.run_request_kill(root, "recovery.1")
    writer = json.loads((root / "writer-info").read_text())
    T503.run_record_crash(root, writer["pid"], 137)


def _fixed_identities(monkeypatch) -> None:
    def identity(writer=False):
        if writer:
            return {"host": "writer-node", "boot_id": "writer-boot", "pid": 101, "start_token": "5001"}
        return {"host": "recovery-node", "boot_id": "recovery-boot", "pid": 202}
    monkeypatch.setattr(T503, "_identity", identity)


def test_writer_fsyncs_armed_before_first_target_write(tmp_path):
    events = []
    _run_writer(tmp_path, "atomic", events.append, size=64)
    first_target = min(i for i, event in enumerate(events) if event.startswith("target_"))
    assert events.index("armed_fsync") < events.index("active_dir_fsync") < first_target


def test_partial_bytes_classify_as_other():
    original = hashlib.sha256(b"original").hexdigest()
    mutated = hashlib.sha256(b"mutated").hexdigest()
    partial = hashlib.sha256(b"muta").hexdigest()
    assert T503.classify(partial, original, mutated) == "OTHER"
    with pytest.raises(ValueError):
        T503.classify(original, original, original)


def test_control_leg_detects_partial_bytes(tmp_path):
    armed = _run_writer(tmp_path, "inplace-partial", size=64)
    result, rc = T503.run_inspect(
        tmp_path, WRITER_PBS_SHA256, allow_same_host=True,
        expect_partial_prefix=True)
    assert rc == 0
    assert result["all_partial_prefix"] is True
    for item, state in zip(armed["targets"], result["classifications"]):
        data = (tmp_path / item["rel"]).read_bytes()
        mutated = base64.b64decode(item["mutated_b64"])
        assert len(data) == len(mutated) // 2 == state["size"]
        assert data == mutated[:len(mutated) // 2]
        assert state["classification"] == "OTHER"


def test_control_rejects_arbitrary_full_length_other(tmp_path):
    armed = _run_writer(tmp_path, "inplace-partial", size=64)
    for item in armed["targets"]:
        (tmp_path / item["rel"]).write_bytes(b"z" * 64)
    result, rc = T503.run_inspect(
        tmp_path, WRITER_PBS_SHA256, allow_same_host=True,
        expect_partial_prefix=True)
    assert rc == 3
    assert result["all_partial_prefix"] is False


def test_repair_refuses_when_any_target_is_other():
    assert T503.repair_decision([]) == "QUARANTINE"
    assert T503.repair_decision(["ORIGINAL", "OTHER"]) == "QUARANTINE"
    assert T503.repair_decision(["MUTATED", "MUTATED"]) == "RESTORED"


def test_clean_is_recorded_only_after_restore_verification(tmp_path):
    events = []
    _run_writer(tmp_path, "atomic", size=64)
    _inspect_and_crash(tmp_path)
    result, rc = T503.run_repair(tmp_path, "receipt", allow_same_host=True, recorder=events.append)
    assert (result["result"], rc) == ("RESTORED", 0)
    assert events.index("restore_verify") < events.index("clean_append")


def test_writer_fsyncs_temp_before_replace(tmp_path, monkeypatch):
    actual_temp_fsyncs = []
    original_fsync = os.fsync

    def counted(fd):
        try:
            name = os.readlink(f"/proc/self/fd/{fd}")
        except OSError:
            name = ""
        if name.endswith(".t503-new"):
            actual_temp_fsyncs.append(name)
        return original_fsync(fd)

    monkeypatch.setattr(T503.os, "fsync", counted)
    events = []
    _run_writer(tmp_path, "atomic", events.append, size=64)
    assert len(actual_temp_fsyncs) == len(T503.TARGETS) == 2
    fsyncs = [i for i, event in enumerate(events) if event == "target_temp_fsync"]
    replaces = [i for i, event in enumerate(events) if event == "target_replace"]
    assert len(fsyncs) == len(replaces) == 2
    assert all(fsync < replace for fsync, replace in zip(fsyncs, replaces))


def test_cross_node_requirement_rejects_same_host():
    writer = {"host": "h", "boot_id": "boot-a"}
    with pytest.raises(T503.EvidenceError):
        T503.require_cross_client(writer, {"host": "h", "boot_id": "boot-b"})
    with pytest.raises(T503.EvidenceError):
        T503.require_cross_client(writer, {"host": "other", "boot_id": "boot-a"})
    with pytest.raises(T503.EvidenceError):
        T503.require_cross_client(writer, {"host": "other", "boot_id": None})
    T503.require_cross_client(writer, {"host": "h", "boot_id": None}, allow_same_host=True)


def test_cli_has_no_allow_same_host_escape():
    with pytest.raises(SystemExit):
        T503._parser().parse_args([
            "inspect", "--root", "/tmp/r", "--output", "/tmp/r/inspect.json",
            "--receipt", "/tmp/r/inspect-receipt", "--pbs-jobid", "1",
            "--expect-writer-pbs-sha256", WRITER_PBS_SHA256,
            "--recovery-pbs-sha256", RECOVERY_PBS_SHA256,
            "--allow-same-host",
        ])


def test_unknown_leg_never_counts_as_pass():
    assert T503.aggregate_verdict({"L-A": "PASS", "L-C": "UNKNOWN"}) == "NO-GO"
    assert T503.aggregate_verdict({}) == "NO-GO"


def test_inspect_requires_ready_and_mutated(tmp_path):
    _run_writer(tmp_path, "atomic", size=64)
    (tmp_path / "ready").unlink()
    assert T503.run_inspect(
        tmp_path, WRITER_PBS_SHA256, allow_same_host=True)[1] == 3
    armed_line = (tmp_path / "journal/attempt.jsonl").read_text().splitlines()[0]
    (tmp_path / "journal/attempt.jsonl").write_text(armed_line + "\n")
    assert T503.run_inspect(
        tmp_path, WRITER_PBS_SHA256, allow_same_host=True)[1] == 3


def test_inspect_records_mount_and_enforces_requested_fstype(tmp_path, monkeypatch):
    _run_writer(tmp_path, "atomic", size=64)
    monkeypatch.setattr(T503, "_mount_info", lambda root: {
        "st_dev": 42, "mount_point": "/fake", "fstype": "ext4"})
    result, rc = T503.run_inspect(
        tmp_path, WRITER_PBS_SHA256, allow_same_host=True)
    assert rc == 0
    assert result["mount"] == {"st_dev": 42, "mount_point": "/fake", "fstype": "ext4"}
    assert T503.run_inspect(
        tmp_path, WRITER_PBS_SHA256, allow_same_host=True,
        require_fstype="lustre")[1] == 3


def test_source_hash_binding_rejects_changed_writer_info(tmp_path):
    _run_writer(tmp_path, "atomic", size=64)
    info_path = tmp_path / "writer-info"
    info = json.loads(info_path.read_text())
    info["probe_sha256"] = "0" * 64
    _write_json(info_path, info)
    assert T503.run_inspect(
        tmp_path, WRITER_PBS_SHA256, allow_same_host=True)[1] == 3


def test_inspect_rejects_unreviewed_writer_pbs_hash(tmp_path):
    _run_writer(tmp_path, "atomic", size=64)
    assert T503.run_inspect(
        tmp_path, "0" * 64, allow_same_host=True)[1] == 3


def test_stale_go_kill_is_rejected_before_writer_starts(tmp_path):
    (tmp_path / "go-kill").write_text("stale\n")
    with pytest.raises(T503.EvidenceError):
        _run_writer(tmp_path, "atomic", size=64)
    assert not (tmp_path / "journal").exists()


def test_crash_receipt_must_match_writer_identity(tmp_path):
    _run_writer(tmp_path, "atomic", size=64)
    _inspect_and_crash(tmp_path)
    receipt_path = tmp_path / "crash-receipt"
    receipt = json.loads(receipt_path.read_text())
    receipt["start_token"] = "wrong"
    _write_json(receipt_path, receipt)
    result, rc = T503.run_repair(tmp_path, "receipt", allow_same_host=True)
    assert (result["result"], rc) == ("QUARANTINE", 4)


def test_repair_rejects_one_byte_inspect_output_rewrite(tmp_path):
    _run_writer(tmp_path, "atomic", size=64)
    _inspect_and_crash(tmp_path)
    output = tmp_path / "inspect.json"
    receipt = json.loads((tmp_path / "inspect-receipt").read_text())
    assert receipt["recovery_pbs_sha256"] == RECOVERY_PBS_SHA256
    assert receipt["inspect_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert receipt["mount"] == json.loads(output.read_text())["mount"]
    changed = bytearray(output.read_bytes())
    original = bytes(changed)
    start = changed.index(b'"mount_point":"') + len(b'"mount_point":"')
    changed[start] = ord("X") if changed[start] != ord("X") else ord("Y")
    assert sum(left != right for left, right in zip(original, changed)) == 1
    assert json.loads(changed)["mount"] != receipt["mount"]
    output.write_bytes(changed)
    result, rc = T503.run_repair(tmp_path, "receipt", allow_same_host=True)
    assert (result["result"], result["restored_targets"], rc) == (
        "QUARANTINE", [], 4)


def test_repair_rejects_receipt_from_different_mount(tmp_path, monkeypatch):
    mount = {"st_dev": 42, "mount_point": "/fake", "fstype": "lustre"}
    monkeypatch.setattr(T503, "_mount_info", lambda root: dict(mount))
    _run_writer(tmp_path, "atomic", size=64)
    _inspect_and_crash(tmp_path)
    mount["st_dev"] = 43
    result, rc = T503.run_repair(tmp_path, "receipt", allow_same_host=True)
    assert (result["result"], result["restored_targets"], rc) == (
        "QUARANTINE", [], 4)


def _prepare_scheduler_leg(root: Path, *, pbs_jobid: str = "0:890867.nqsv") -> None:
    _run_writer(root, "atomic", size=64, pbs_jobid=pbs_jobid)
    result, rc = T503.run_inspect(
        root, WRITER_PBS_SHA256, allow_same_host=True)
    assert rc == 0
    result["rc"] = rc
    _write_json(root / "inspect.json", result)
    _write_json(root / "inspect-receipt", T503._inspect_receipt(
        root, result, "recovery.18", root / "inspect.json",
        RECOVERY_PBS_SHA256))


def test_scheduler_evidence_is_proxy_and_requires_accounting(tmp_path):
    _prepare_scheduler_leg(tmp_path)
    (tmp_path / "scheduler-terminal.txt").write_text(
        "Request ID: 890867.nqsv\n"
        "%NQSV(INFO): Batch job received signal SIGKILL. "
        "(Exceeded per-req elapse time limit)\n")
    repaired, rc = T503.run_repair(tmp_path, "scheduler", allow_same_host=True)
    assert rc == 0
    assert repaired["crash_evidence"] == "scheduler-accounting"
    assert T503.SCHEDULER_PROXY in repaired["does_not_prove"]


def test_scheduler_evidence_accepts_nqsv_accounting_format(tmp_path):
    _prepare_scheduler_leg(tmp_path)
    (tmp_path / "scheduler-terminal.txt").write_text(
        "%NQSV(INFO): Batch job received signal SIGKILL. "
        "(Exceeded per-req elapse time limit)\n\n"
        "============================================================\n"
        "Request ID:             890867.nqsv\n"
        "Request Name:           t503_restore_durability_probe.pbs\n"
        "Queue:                  gen_S@nqsv\n")
    repaired, rc = T503.run_repair(tmp_path, "scheduler", allow_same_host=True)
    assert rc == 0
    assert repaired["crash_evidence"] == "scheduler-accounting"


@pytest.mark.parametrize("terminal", [
    "%NQSV(INFO): Batch job received signal SIGKILL. "
    "(Exceeded per-req elapse time limit)\nRequest ID: 890868.nqsv\n",
    "%NQSV(INFO): Batch job received signal SIGKILL. "
    "(Exceeded per-req elapse time limit)\nRequest ID: 1890867.nqsv\n",
    "%NQSV(INFO): Batch job received signal SIGKILL. "
    "(Exceeded per-req elapse time limit)\nRequest ID: 890867.nqsv.bak\n",
    "Exceeded per-req elapse time limit\nRequest ID: 890867.nqsv\n",
    "%NQSV(INFO): Batch job received signal SIGKILL.\nRequest ID: 890867.nqsv\n",
    "%NQSV(INFO): Batch job received signal SIGKILL.\n"
    "Exceeded per-req elapse time limit\nRequest ID: 890867.nqsv\n",
    "%NQSV(INFO): Batch job received signal SIGKILL. "
    "(Exceeded per-req elapse time limit)\nPBS request ID: 890867.nqsv\n",
], ids=[
    "different-request",
    "leading-partial-match",
    "trailing-partial-match",
    "missing-sigkill",
    "missing-walltime",
    "signal-and-walltime-on-different-lines",
    "missing-request-id",
])
def test_scheduler_evidence_rejects_invalid_accounting(tmp_path, terminal):
    _prepare_scheduler_leg(tmp_path)
    (tmp_path / "scheduler-terminal.txt").write_text(terminal)
    repaired, rc = T503.run_repair(tmp_path, "scheduler", allow_same_host=True)
    assert (repaired["result"], rc) == ("QUARANTINE", 4)
    assert repaired["error"] == "scheduler terminal accounting is invalid"


def test_scheduler_evidence_rejects_empty_normalized_request_id(tmp_path):
    _prepare_scheduler_leg(tmp_path, pbs_jobid="0:")
    (tmp_path / "scheduler-terminal.txt").write_text(
        "%NQSV(INFO): Batch job received signal SIGKILL. "
        "(Exceeded per-req elapse time limit)\nRequest ID: 890867.nqsv\n")
    repaired, rc = T503.run_repair(tmp_path, "scheduler", allow_same_host=True)
    assert (repaired["result"], rc) == ("QUARANTINE", 4)


def test_scheduler_evidence_rejects_nonzero_subrequest_prefix(tmp_path):
    _prepare_scheduler_leg(tmp_path, pbs_jobid="1:890867.nqsv")
    (tmp_path / "scheduler-terminal.txt").write_text(
        "%NQSV(INFO): Batch job received signal SIGKILL. "
        "(Exceeded per-req elapse time limit)\nRequest ID: 890867.nqsv\n")
    repaired, rc = T503.run_repair(tmp_path, "scheduler", allow_same_host=True)
    assert (repaired["result"], rc) == ("QUARANTINE", 4)


def test_scheduler_evidence_rejects_multiple_request_ids(tmp_path):
    _prepare_scheduler_leg(tmp_path)
    (tmp_path / "scheduler-terminal.txt").write_text(
        "%NQSV(INFO): Batch job received signal SIGKILL. "
        "(Exceeded per-req elapse time limit)\n"
        "Request ID: 890867.nqsv\nRequest ID: 890867.nqsv\n")
    repaired, rc = T503.run_repair(tmp_path, "scheduler", allow_same_host=True)
    assert (repaired["result"], rc) == ("QUARANTINE", 4)


@pytest.mark.parametrize("mutation", ["seq", "duplicate-armed", "bad-type", "clean-not-last"])
def test_repair_quarantines_invalid_journal_record_sequences(tmp_path, mutation):
    _run_writer(tmp_path, "atomic", size=64)
    _inspect_and_crash(tmp_path)
    journal = tmp_path / "journal/attempt.jsonl"
    records = [json.loads(line) for line in journal.read_text().splitlines()]
    if mutation == "seq":
        records[-1]["seq"] = 99
    elif mutation == "duplicate-armed":
        records.append(records[0] | {"seq": 2})
    elif mutation == "bad-type":
        records[-1]["seq"] = "1"
    else:
        records.extend([{"record": "clean", "seq": 2}, {"record": "recovering", "seq": 3}])
    journal.write_text("".join(json.dumps(value) + "\n" for value in records))
    before = journal.read_bytes()
    result, rc = T503.run_repair(tmp_path, "receipt", allow_same_host=True)
    assert (result["result"], rc) == ("QUARANTINE", 4)
    assert journal.read_bytes() == before


def test_unterminated_tail_quarantines_without_append(tmp_path):
    _run_writer(tmp_path, "atomic", size=64)
    _inspect_and_crash(tmp_path)
    journal = tmp_path / "journal/attempt.jsonl"
    with journal.open("ab") as stream:
        stream.write(b'{"record":"recovering","seq":2')
    before = journal.read_bytes()
    result, rc = T503.run_repair(tmp_path, "receipt", allow_same_host=True)
    assert (result["result"], rc) == ("QUARANTINE", 4)
    assert journal.read_bytes() == before


def test_restore_failure_after_first_replace_is_partial_restore(tmp_path, monkeypatch):
    _run_writer(tmp_path, "atomic", size=64)
    _inspect_and_crash(tmp_path)
    real_replace = T503.os.replace
    restore_replaces = 0

    def fail_second_restore(source, target):
        nonlocal restore_replaces
        if str(source).endswith(".restore"):
            restore_replaces += 1
            if restore_replaces == 2:
                raise OSError("injected second restore failure")
        return real_replace(source, target)

    monkeypatch.setattr(T503.os, "replace", fail_second_restore)
    result, rc = T503.run_repair(tmp_path, "receipt", allow_same_host=True)
    assert (result["result"], result["restored_targets"], rc) == (
        "PARTIAL-RESTORE", [T503.TARGETS[0]], 9)


def test_prewrite_refusal_remains_quarantine_without_writes(tmp_path):
    armed = _run_writer(tmp_path, "inplace-partial", size=64)
    _inspect_and_crash(tmp_path, partial=True)
    journal = tmp_path / "journal/attempt.jsonl"
    before_journal = journal.read_bytes()
    before_targets = [(tmp_path / item["rel"]).read_bytes()
                      for item in armed["targets"]]
    result, rc = T503.run_repair(tmp_path, "receipt", allow_same_host=True)
    assert (result["result"], result["restored_targets"], rc) == (
        "QUARANTINE", [], 4)
    assert journal.read_bytes() == before_journal
    assert [(tmp_path / item["rel"]).read_bytes()
            for item in armed["targets"]] == before_targets


def test_writer_records_each_new_ancestor_parent_fsync(tmp_path):
    root = tmp_path / "new-a" / "new-b"
    armed = _run_writer(root, "atomic", size=64)
    durability = armed["ancestor_fsync"]
    assert durability["created_directories"] == [str(tmp_path / "new-a"), str(root)]
    assert durability["fsynced_parents"] == [str(tmp_path), str(tmp_path / "new-a")]
    assert durability["existing_ancestor"] == str(tmp_path)


def _run_cli_leg(root: Path, mode: str, *, partial: bool) -> tuple[int, int]:
    _run_writer(root, mode, size=64, pbs_jobid="writer.1")
    inspect_argv = ["inspect", "--root", str(root), "--output", str(root / "inspect.json"),
                    "--receipt", str(root / "inspect-receipt"), "--pbs-jobid", "recovery.2",
                    "--expect-writer-pbs-sha256", WRITER_PBS_SHA256,
                    "--recovery-pbs-sha256", RECOVERY_PBS_SHA256]
    if partial:
        inspect_argv.append("--expect-partial-prefix")
    assert T503.main(inspect_argv) == 0
    assert T503.main(["request-kill", "--root", str(root), "--pbs-jobid", "recovery.2"]) == 0
    writer = json.loads((root / "writer-info").read_text())
    assert T503.main(["record-crash", "--root", str(root), "--pid", str(writer["pid"]),
                      "--wait-status", "137"]) == 0
    repair_rc = T503.main(["repair", "--root", str(root), "--output", str(root / "repair.json"),
                           "--crash-evidence", "receipt"])
    verify_rc = T503.main(["verify", "--root", str(root), "--output", str(root / "verify.json")])
    return repair_rc, verify_rc


def test_atomic_run_without_crash_verdicts_pass(tmp_path, monkeypatch):
    _fixed_identities(monkeypatch)
    monkeypatch.setattr(T503, "_mount_info", lambda root: {
        "st_dev": 42, "mount_point": "/fake-lustre", "fstype": "lustre"})
    atomic, control = tmp_path / "atomic", tmp_path / "control"
    atomic.mkdir(); control.mkdir()
    assert _run_cli_leg(atomic, "atomic", partial=False) == (0, 0)
    assert json.loads((atomic / "inspect.json").read_text())["rc"] == 0
    assert json.loads((atomic / "repair.json").read_text())["result"] == "RESTORED"
    assert json.loads((atomic / "verify.json").read_text())["result"] == "PASS"
    assert _run_cli_leg(control, "inplace-partial", partial=True) == (4, 5)
    verdict_root = tmp_path / "verdict"
    verdict_root.mkdir()
    rc = T503.main([
        "verdict", "--root", str(verdict_root), "--output", str(verdict_root / "verdict.json"),
        "--leg-root", f"L-A={atomic}", "--leg-root", f"L-C={control}",
    ])
    verdict = json.loads((verdict_root / "verdict.json").read_text())
    assert rc == 0
    assert verdict["verdict"] == "GO"
    assert verdict["legs"]["L-A"]["result"] == "PASS"
    assert verdict["legs"]["L-C"]["result"] == "PASS"
    assert verdict["legs"]["L-B"]["result"] == "UNKNOWN"


def test_partial_restore_repair_never_produces_go(tmp_path, monkeypatch):
    _fixed_identities(monkeypatch)
    monkeypatch.setattr(T503, "_mount_info", lambda root: {
        "st_dev": 42, "mount_point": "/fake-lustre", "fstype": "lustre"})
    atomic, control = tmp_path / "atomic", tmp_path / "control"
    atomic.mkdir(); control.mkdir()
    assert _run_cli_leg(atomic, "atomic", partial=False) == (0, 0)
    assert _run_cli_leg(control, "inplace-partial", partial=True) == (4, 5)
    repair_path = atomic / "repair.json"
    repair = json.loads(repair_path.read_text())
    repair.update(result="PARTIAL-RESTORE", rc=9)
    _write_json(repair_path, repair)
    verdict_root = tmp_path / "verdict"
    verdict_root.mkdir()
    rc = T503.main([
        "verdict", "--root", str(verdict_root),
        "--output", str(verdict_root / "verdict.json"),
        "--leg-root", f"L-A={atomic}", "--leg-root", f"L-C={control}",
    ])
    verdict = json.loads((verdict_root / "verdict.json").read_text())
    assert rc == 8
    assert verdict["verdict"] == "NO-GO"
    assert verdict["legs"]["L-A"]["result"] == "FAIL"


def test_verdict_no_go_returns_nonzero_and_required_set_is_not_cli_controlled(tmp_path):
    parser = T503._parser()
    assert "--leg" not in parser.format_help()
    assert "--required" not in parser.format_help()
    with pytest.raises(SystemExit):
        parser.parse_args(["verdict", "--root", "/tmp/v", "--output", "/tmp/v/verdict.json",
                           "--leg", "L-A=PASS", "--required", "L-A"])
    root = tmp_path / "verdict"
    root.mkdir()
    missing_a, missing_c = tmp_path / "missing-a", tmp_path / "missing-c"
    missing_a.mkdir(); missing_c.mkdir()
    rc = T503.main([
        "verdict", "--root", str(root), "--output", str(root / "verdict.json"),
        "--leg-root", f"L-A={missing_a}", "--leg-root", f"L-C={missing_c}",
    ])
    result = json.loads((root / "verdict.json").read_text())
    assert rc != 0
    assert result["verdict"] == "NO-GO"
    assert result["required"] == list(T503.REQUIRED_LEGS)


def test_pbs_scripts_bind_jobs_sources_clients_and_stage_processes():
    writer = WRITER_PBS.read_text()
    recovery = RECOVERY_PBS.read_text()
    assert recovery.index('while [[ ! -d "$T503_ROOT"') < recovery.index(
        'realpath -e -- "$T503_ROOT"'
    )
    assert "${PBS_JOBID:-}" in writer
    assert "go-kill" in writer and "record-crash" in writer and "WAIT_STATUS" in writer
    assert "--pbs-sha256" in writer and "root-durability.json" in writer
    assert "${PBS_JOBID:-}" in recovery and "--require-fstype lustre" in recovery
    assert "--expect-writer-pbs-sha256" in recovery
    assert "--recovery-pbs-sha256" in recovery
    assert 'sha256sum -- "$WRITER_PBS"' in recovery
    assert 'sha256sum -- "$RECOVERY_PBS"' in recovery
    assert "exit 7" in recovery and "CRASH_WAITED" in recovery
    assert recovery.count('"$PY" -I -B "$PROBE"') >= 4
    assert "物理ノード死" in recovery and "leg-summary.json" in recovery
    assert all(
        token in (ROOT / "tools/pegasus/probes/t503_restore_durability_verdict.pbs").read_text()
        for token in (
            '${PBS_JOBID:-}',
            '[[ ! -e "$T503_VERDICT_ROOT/verdict.json"',
            'VERDICT_RC=$?',
            'exit "$VERDICT_RC"',
        )
    )
