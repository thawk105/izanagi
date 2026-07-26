# -*- coding: utf-8 -*-
"""dev-waves control ledger tests (pytest and plain-Python dual runner)."""
from __future__ import annotations

import errno
import importlib
import json
import os
import socket
import sys
import tempfile
import threading
import traceback
import types
from decimal import Decimal
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
_PKG = "_izanagi_unit_b1_dev_waves"
if _PKG not in sys.modules:
    package = types.ModuleType(_PKG)
    package.__path__ = [str(_ROOT / "tools" / "dev_waves")]
    package.__package__ = _PKG
    sys.modules[_PKG] = package
schema = importlib.import_module(f"{_PKG}.schema")
ledger = importlib.import_module(f"{_PKG}.ledger")


_BOOT_A = "11111111-1111-4111-8111-111111111111"
_BOOT_B = "22222222-2222-4222-8222-222222222222"


def _expect_error(fn, code=None):
    try:
        fn()
    except schema.DevWavesError as exc:
        if code is not None:
            assert exc.code is code, (exc.code, code, exc.detail)
        return exc
    raise AssertionError("DevWavesError が発生しなかった")


def _manifest(run_id="run-1"):
    return schema.RunManifest(
        schema.SCHEMA_VERSION,
        run_id,
        "a" * 64,
        "default",
        2,
        schema.ResourceLimits(
            10, 20, Decimal("1"), Decimal("2"), 4096, 65536,
        ),
        "2026-07-21T00:00:00Z",
        "b" * 64,
        "c" * 64,
        "d" * 64,
    )


def _layout(parent):
    return ledger.RuntimeLayout.create(Path(parent) / "runtime")


def _create(parent, run_id="run-1", **kwargs):
    layout = _layout(parent)
    control = ledger.ControlLedger.create(
        layout, run_id, _manifest(run_id), boot_id=_BOOT_A, **kwargs,
    )
    return layout, control


def _wal(layout, run_id="run-1"):
    return layout.run_dir(run_id) / ledger.EVENTS_NAME


def _records(layout, run_id="run-1"):
    return [json.loads(line) for line in _wal(layout, run_id).read_bytes().splitlines()]


def _write_records(layout, records, run_id="run-1"):
    raw = b"".join(schema.canonical_bytes(item) + b"\n" for item in records)
    _wal(layout, run_id).write_bytes(raw)


def test_bootstrap_stages_until_first_wal_fsync_and_discovery_lists_residue_invalid():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_stage_") as temp:
        layout = _layout(temp)
        calls = 0

        def fail_wal(fd):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError(errno.EIO, "injected WAL fsync")
            os.fsync(fd)

        _expect_error(
            lambda: ledger.ControlLedger.create(
                layout, "run-1", _manifest(), boot_id=_BOOT_A, fsync=fail_wal,
            ),
            schema.ReasonCode.RUNTIME_IO_FAILURE,
        )
        assert not layout.run_dir("run-1").exists()
        assert layout.staging_dir("run-1").is_dir()
        found = ledger.discover_runs(layout)
        assert [(item.run_id, item.reason) for item in found] == [
            ("run-1", schema.ReasonCode.INVALID_RUN),
        ]


def test_append_retries_short_write_until_one_complete_record():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_short_") as temp:
        layout, control = _create(temp)
        control.close()
        writes = 0

        def short_write(fd, payload):
            nonlocal writes
            writes += 1
            return os.write(fd, payload[: min(3, len(payload))])

        reopened = ledger.ControlLedger.open(
            layout.run_dir("run-1"), boot_id=_BOOT_A, write=short_write,
        )
        reopened.transition(schema.RunState.PREFLIGHT)
        reopened.close()
        assert writes > 2
        snapshot = ledger.replay_run(layout.run_dir("run-1"))
        assert snapshot.last_seq == 2
        assert snapshot.state is schema.RunState.PREFLIGHT


def test_wal_fsync_failure_poison_blocks_following_effect_and_resume():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_poison_") as temp:
        layout, control = _create(temp)
        control.close()
        calls = 0

        def fail_once(fd):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError(errno.EIO, "injected")
            os.fsync(fd)

        reopened = ledger.ControlLedger.open(
            layout.run_dir("run-1"), boot_id=_BOOT_A, fsync=fail_once,
        )
        effects = []
        _expect_error(
            lambda: reopened.transition(schema.RunState.PREFLIGHT),
            schema.ReasonCode.RUNTIME_IO_FAILURE,
        )
        if not reopened.poisoned:
            effects.append("must-not-run")
        assert effects == []
        assert (layout.run_dir("run-1") / ledger.POISON_NAME).is_file()
        _expect_error(
            lambda: reopened.append("heartbeat"),
            schema.ReasonCode.RUNTIME_IO_FAILURE,
        )
        reopened.close()
        _expect_error(
            lambda: ledger.ControlLedger.open(
                layout.run_dir("run-1"), boot_id=_BOOT_A,
            ),
            schema.ReasonCode.POISONED,
        )


def test_partial_write_then_eio_poison_takes_precedence_over_torn_tail_on_resume():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_torn_poison_") as temp:
        layout, control = _create(temp)
        control.close()
        calls = 0

        def tear_write(fd, payload):
            nonlocal calls
            calls += 1
            if calls == 1:
                return os.write(fd, payload[:5])
            if calls == 2:
                raise OSError(errno.EIO, "injected after short write")
            return os.write(fd, payload)

        reopened = ledger.ControlLedger.open(
            layout.run_dir("run-1"), boot_id=_BOOT_A, write=tear_write,
        )
        _expect_error(
            lambda: reopened.transition(schema.RunState.PREFLIGHT),
            schema.ReasonCode.RUNTIME_IO_FAILURE,
        )
        reopened.close()
        _expect_error(
            lambda: ledger.ControlLedger.open(
                layout.run_dir("run-1"), boot_id=_BOOT_A,
            ),
            schema.ReasonCode.POISONED,
        )
        found = ledger.discover_runs(layout)
        assert [(item.run_id, item.reason) for item in found] == [
            ("run-1", schema.ReasonCode.POISONED),
        ]


def test_parent_directory_fsync_failure_is_terminal():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_parent_") as temp:
        count = 0

        def fail_parent(fd):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError(errno.EIO, "injected parent fsync")
            os.fsync(fd)

        _expect_error(
            lambda: ledger.RuntimeLayout.create(
                Path(temp) / "runtime", fsync=fail_parent,
            ),
            schema.ReasonCode.RUNTIME_IO_FAILURE,
        )


def test_publish_parent_fsync_failure_poison_marks_visible_run_nonresumable():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_publish_parent_") as temp:
        layout = _layout(temp)
        root_info = layout.root.stat()
        failed = False

        def fail_after_rename(fd):
            nonlocal failed
            info = os.fstat(fd)
            if (
                not failed
                and (info.st_dev, info.st_ino) == (root_info.st_dev, root_info.st_ino)
                and layout.run_dir("run-1").exists()
            ):
                failed = True
                raise OSError(errno.EIO, "injected publish parent fsync")
            os.fsync(fd)

        _expect_error(
            lambda: ledger.ControlLedger.create(
                layout, "run-1", _manifest(), boot_id=_BOOT_A,
                fsync=fail_after_rename,
            ),
            schema.ReasonCode.RUNTIME_IO_FAILURE,
        )
        assert failed
        assert (layout.run_dir("run-1") / ledger.POISON_NAME).is_file()
        found = ledger.discover_runs(layout)
        assert [(item.run_id, item.reason) for item in found] == [
            ("run-1", schema.ReasonCode.POISONED),
        ]


def test_status_and_summary_rebuild_only_from_wal():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_cache_") as temp:
        layout, control = _create(temp)
        control.transition(schema.RunState.PREFLIGHT, wave_index=1)
        run = layout.run_dir("run-1")
        (run / ledger.STATUS_NAME).write_text('{"state":"completed"}\n', encoding="utf-8")
        (run / ledger.SUMMARY_NAME).write_text("forged\n", encoding="utf-8")
        snapshot = control.rebuild_status()
        status = json.loads((run / ledger.STATUS_NAME).read_bytes())
        summary = (run / ledger.SUMMARY_NAME).read_text(encoding="utf-8")
        control.close()
        assert snapshot.state is schema.RunState.PREFLIGHT
        assert status["state"] == "preflight"
        assert status["seq"] == 2
        assert "state: preflight" in summary
        assert "forged" not in summary


def test_state_machine_accepts_exact_allowed_edge_set():
    edges = {
        ("created", "preflight"), ("preflight", "ready"),
        ("ready", "wave-prepared"), ("wave-prepared", "child-running"),
        ("child-running", "child-exited"), ("child-exited", "verifying"),
        ("verifying", "wave-accepted"), ("wave-accepted", "ready"),
        ("wave-accepted", "completed"), ("stopping", "completed"),
        ("stopping", "blocked"), ("stopping", "failed"),
        ("stopping", "interrupted"),
    }
    edges |= {(value, "stopping") for value in (
        "created", "preflight", "ready", "wave-prepared", "child-running",
        "child-exited", "verifying", "wave-accepted",
    )}
    for current in schema.RunState:
        for target in schema.RunState:
            allowed = (current.value, target.value) in edges
            if current is schema.RunState.STOPPING and target is schema.RunState.COMPLETED:
                if allowed:
                    ledger.validate_transition(
                        current, target,
                        reason=schema.ReasonCode.NO_ACTIONABLE_TASK,
                    )
                continue
            if allowed:
                ledger.validate_transition(current, target)
            else:
                _expect_error(
                    lambda current=current, target=target:
                    ledger.validate_transition(current, target),
                    schema.ReasonCode.INVALID_RUN,
                )


def test_state_machine_rejects_complement_edge_set():
    allowed_literals = {
        ("created", "preflight"), ("preflight", "ready"),
        ("ready", "wave-prepared"), ("wave-prepared", "child-running"),
        ("child-running", "child-exited"), ("child-exited", "verifying"),
        ("verifying", "wave-accepted"), ("wave-accepted", "ready"),
        ("wave-accepted", "completed"), ("stopping", "completed"),
        ("stopping", "blocked"), ("stopping", "failed"),
        ("stopping", "interrupted"),
    }
    allowed_literals |= {(value, "stopping") for value in (
        "created", "preflight", "ready", "wave-prepared", "child-running",
        "child-exited", "verifying", "wave-accepted",
    )}
    rejected = {
        (current, target)
        for current in schema.RunState
        for target in schema.RunState
        if (current.value, target.value) not in allowed_literals
    }
    observed = set()
    for current, target in rejected:
        _expect_error(
            lambda current=current, target=target:
            ledger.validate_transition(current, target),
            schema.ReasonCode.INVALID_RUN,
        )
        observed.add((current, target))
    assert observed == rejected


def test_terminal_states_have_no_outgoing_transition():
    for value in ("completed", "blocked", "failed", "interrupted"):
        terminal = schema.RunState(value)
        assert schema.ALLOWED_TRANSITIONS[terminal] == frozenset()
        for target in schema.RunState:
            _expect_error(
                lambda terminal=terminal, target=target:
                ledger.validate_transition(terminal, target),
                schema.ReasonCode.INVALID_RUN,
            )


def test_active_deadline_uses_boottime_during_wall_rollback():
    monotonic_values = iter((1_000_000_000, 4_000_000_000))
    wall_values = iter((1_000, 1))
    assert next(wall_values) == 1_000
    deadline = ledger.BoottimeDeadline.start(
        10, boot_id=_BOOT_A, boottime=lambda: next(monotonic_values),
    )
    assert next(wall_values) == 1  # wall clock rolled back after deadline start
    assert deadline.remaining_ns(
        boot_id=_BOOT_A, boottime=lambda: next(monotonic_values),
    ) == 7_000_000_000
    _expect_error(
        lambda: deadline.remaining_ns(boot_id=_BOOT_B, boottime=lambda: 5),
        schema.ReasonCode.AMBIGUOUS_RECOVERY,
    )
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_wall_") as temp:
        boot_values = iter((100, 200))
        utc_values = iter(("2026-07-21T00:00:10Z", "2026-07-20T23:59:59Z"))
        layout, control = _create(
            temp, boottime=lambda: next(boot_values), utc=lambda: next(utc_values),
        )
        control.transition(schema.RunState.PREFLIGHT)
        control.close()
        snapshot = ledger.replay_run(layout.run_dir("run-1"))
        assert snapshot.started_boottime_ns == 100
        assert snapshot.last_boottime_ns == 200


def test_deadline_exact_minus_one_equal_plus_one_nanosecond_boundaries():
    deadline = ledger.BoottimeDeadline.start(
        1, boot_id=_BOOT_A, boottime=lambda: 100,
    )
    assert deadline.remaining_ns(boot_id=_BOOT_A, boottime=lambda: deadline.deadline_ns - 1) == 1
    assert deadline.remaining_ns(boot_id=_BOOT_A, boottime=lambda: deadline.deadline_ns) == 0
    assert deadline.remaining_ns(boot_id=_BOOT_A, boottime=lambda: deadline.deadline_ns + 1) == 0


def test_recovery_on_changed_boot_id_stops_when_remaining_time_is_ambiguous():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_reboot_") as temp:
        layout, control = _create(temp)
        control.close()
        _expect_error(
            lambda: ledger.ControlLedger.open(
                layout.run_dir("run-1"), boot_id=_BOOT_B,
            ),
            schema.ReasonCode.AMBIGUOUS_RECOVERY,
        )


def test_replay_rejects_wal_tail_partial_line():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_tail_") as temp:
        layout, control = _create(temp)
        control.close()
        with _wal(layout).open("ab") as stream:
            stream.write(b'{"seq":2')
        _expect_error(
            lambda: ledger.replay_run(layout.run_dir("run-1")),
            schema.ReasonCode.INVALID_RUN,
        )


def test_replay_rejects_duplicate_seq():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_seq_") as temp:
        layout, control = _create(temp)
        control.transition(schema.RunState.PREFLIGHT)
        control.close()
        records = _records(layout)
        records[1]["seq"] = 1
        _write_records(layout, records)
        _expect_error(
            lambda: ledger.replay_run(layout.run_dir("run-1")),
            schema.ReasonCode.INVALID_RUN,
        )


def test_replay_maps_duplicate_json_key_to_invalid_run():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_duplicate_key_") as temp:
        layout, control = _create(temp)
        control.close()
        raw = _wal(layout).read_bytes().replace(
            b'"seq":1', b'"seq":1,"seq":1', 1,
        )
        _wal(layout).write_bytes(raw)
        _expect_error(
            lambda: ledger.replay_run(layout.run_dir("run-1")),
            schema.ReasonCode.INVALID_RUN,
        )


def test_replay_rejects_event_after_terminal():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_terminal_") as temp:
        layout, control = _create(temp)
        control.transition(schema.RunState.STOPPING)
        control.transition(
            schema.RunState.FAILED, reason=schema.ReasonCode.NONZERO_EXIT,
        )
        control.close()
        records = _records(layout)
        last = dict(records[-1])
        last.update({
            "seq": 4,
            "event": "heartbeat",
            "state": None,
            "reason": None,
            "boottime_ns": last["boottime_ns"] + 1,
        })
        records.append(last)
        _write_records(layout, records)
        _expect_error(
            lambda: ledger.replay_run(layout.run_dir("run-1")),
            schema.ReasonCode.INVALID_RUN,
        )


def test_replay_rejects_boot_id_change_inside_wal():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_boot_record_") as temp:
        layout, control = _create(temp)
        control.transition(schema.RunState.PREFLIGHT)
        control.close()
        records = _records(layout)
        records[1]["boot_id"] = _BOOT_B
        _write_records(layout, records)
        _expect_error(
            lambda: ledger.replay_run(layout.run_dir("run-1")),
            schema.ReasonCode.AMBIGUOUS_RECOVERY,
        )


def test_replay_rejects_noncanonical_or_invalid_event_matrix():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_matrix_") as temp:
        layout, control = _create(temp)
        control.close()
        valid = _wal(layout).read_bytes()
        bodies = (
            valid.replace(b'"seq":1', b'"seq": 1'),
            valid.replace(b'"event":"run_created"', b'"event":"unknown"'),
            valid.replace(b'"schema_version":1', b'"schema_version":2'),
            valid.replace(b'"operation_id":null', b'"operation_id":"unexpected"'),
        )
        for raw in bodies:
            _wal(layout).write_bytes(raw)
            _expect_error(
                lambda: ledger.replay_run(layout.run_dir("run-1")),
                schema.ReasonCode.INVALID_RUN,
            )
        _wal(layout).write_bytes(valid)
        assert ledger.replay_run(layout.run_dir("run-1")).last_seq == 1


def test_single_writer_queue_serializes_concurrent_sequences():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_queue_") as temp:
        layout, control = _create(temp)
        errors = []

        def append(index):
            try:
                control.append(
                    "client_request_recorded",
                    data={"action": "status", "wave_index": index + 1},
                )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=append, args=(index,)) for index in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        control.close()
        assert errors == []
        records = _records(layout)
        assert [item["seq"] for item in records] == list(range(1, 14))
        assert ledger.replay_run(layout.run_dir("run-1")).event_count == 13


def test_second_control_ledger_writer_is_rejected_while_first_is_open():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_double_writer_") as temp:
        layout, control = _create(temp)
        _expect_error(
            lambda: ledger.ControlLedger.open(
                layout.run_dir("run-1"), boot_id=_BOOT_A,
            ),
            schema.ReasonCode.DAEMON_BUSY,
        )
        control.transition(schema.RunState.PREFLIGHT)
        control.close()
        reopened = ledger.ControlLedger.open(layout, "run-1", boot_id=_BOOT_A)
        reopened.close()


def test_observation_and_side_effect_types_enforce_prepared_discipline():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_effect_") as temp:
        layout, control = _create(temp)
        intent = ledger.SideEffectIntent(
            "spawn-1", "spawn", "e" * 64, {"path": "/tmp/w001"},
        )
        observation = ledger.Observation(
            "git-status-1", "git-status", {"status": "clean"},
        )
        control.record_observation(observation)
        control.record_observation(observation)
        missing = ledger.SideEffectIntent(
            "missing", "spawn", "f" * 64, {"path": "/tmp/w002"},
        )
        _expect_error(
            lambda: control.observe_side_effect(missing, {"status": "done"}),
            schema.ReasonCode.INVALID_RUN,
        )
        try:
            control.append("side_effect_prepared")
        except TypeError:
            pass
        else:
            raise AssertionError("raw side-effect event bypass was accepted")
        control.prepare_side_effect(intent)
        control.observe_side_effect(intent, {"status": "done"})
        _expect_error(
            lambda: control.prepare_side_effect(intent),
            schema.ReasonCode.INVALID_RUN,
        )
        snapshot = control.snapshot
        control.close()
        assert snapshot.prepared_operations == frozenset({"spawn-1"})
        assert snapshot.observed_operations == frozenset({"spawn-1"})
        assert ledger.replay_run(layout.run_dir("run-1")) == snapshot


def test_signal_relay_only_notifies_self_pipe_until_normal_context_drains():
    with ledger.SignalRelay() as relay:
        relay.notify(2)
        relay.notify(15)
        assert relay.drain() == (2, 15)
        assert relay.drain() == ()


def test_repository_lease_binds_host_boot_and_rechecks_inode():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_lease_") as temp:
        layout = _layout(temp)
        real_boot = ledger.read_boot_id()
        host = socket.gethostname()
        first = ledger.RepositoryLease.acquire(
            layout, hostname=host, boot_id=real_boot,
        )
        first.assert_valid()
        first.release()
        _expect_error(
            lambda: ledger.RepositoryLease.acquire(
                layout, hostname=host, boot_id=_BOOT_A,
            ),
            schema.ReasonCode.FOREIGN_LEASE,
        )
        active = ledger.RepositoryLease.acquire(
            layout, hostname=host, boot_id=real_boot,
        )
        old = layout.root / "old-control.lock"
        layout.control_lock.rename(old)
        layout.control_lock.write_bytes(old.read_bytes())
        _expect_error(active.assert_valid, schema.ReasonCode.FOREIGN_LEASE)
        active.release()


def test_line_and_total_wal_limits_fail_before_oversized_append():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_caps_") as temp:
        layout, control = _create(temp)
        control.close()
        initial = _wal(layout).stat().st_size
        reopened = ledger.ControlLedger.open(
            layout.run_dir("run-1"),
            boot_id=_BOOT_A,
            max_total_bytes=initial + 1,
        )
        _expect_error(
            lambda: reopened.append("heartbeat"),
            schema.ReasonCode.INVALID_RUN,
        )
        reopened.close()
        assert _wal(layout).stat().st_size == initial


def test_manifest_run_binding_rejected_before_staging_creation():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_manifest_") as temp:
        layout = _layout(temp)
        _expect_error(
            lambda: ledger.ControlLedger.create(
                layout, "run-1", _manifest("run-2"), boot_id=_BOOT_A,
            ),
            schema.ReasonCode.INVALID_RUN,
        )
        assert ledger.discover_runs(layout) == ()


def test_discovery_excludes_root_audit_and_server_profile_namespaces():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_root_names_") as temp:
        layout = _layout(temp)
        (layout.root / "invalid-requests.jsonl").write_text("{}\n", encoding="utf-8")
        (layout.root / "server-profile.json").write_text("{}\n", encoding="utf-8")
        assert ledger.discover_runs(layout) == ()


def test_open_revalidates_immutable_manifest_binding():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_manifest_open_") as temp:
        layout, control = _create(temp)
        control.close()
        path = layout.run_dir("run-1") / ledger.MANIFEST_NAME
        value = json.loads(path.read_bytes())
        value["run_id"] = "run-2"
        path.write_bytes(schema.canonical_bytes(value) + b"\n")
        _expect_error(
            lambda: ledger.ControlLedger.open(
                layout.run_dir("run-1"), boot_id=_BOOT_A,
            ),
            schema.ReasonCode.INVALID_RUN,
        )


def test_cache_transient_names_round_trip_and_exclude_create_only_artifacts():
    """A reader can tell this module's rewrite scratch from a real artifact.

    The recognizer is the inverse of the writer, so a cached name added to one
    side without the other cannot silently make a create-only artifact look
    disposable, nor a scratch file look like a loss.
    """
    assert ledger.CACHED_NAMES == frozenset({ledger.STATUS_NAME, ledger.SUMMARY_NAME})
    for name in ledger.CACHED_NAMES:
        transient = ledger.cache_transient_name(name)
        assert transient.startswith(name + ".tmp.")
        assert ledger.is_cache_transient_name(transient)
        assert not ledger.is_cache_transient_name(name)
    # Create-only artifacts never have a transient form, in either direction.
    for name in (ledger.EVENTS_NAME, ledger.MANIFEST_NAME, ledger.POISON_NAME):
        assert not ledger.is_cache_transient_name(f"{name}.tmp.1.2")
        try:
            ledger.cache_transient_name(name)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{name} was given a transient form")
    # Shapes that only resemble the writer's output are not accepted.
    for forged in (
        f"{ledger.STATUS_NAME}.tmp.1",
        f"{ledger.STATUS_NAME}.tmp.x.2",
        f"{ledger.STATUS_NAME}.tmp.1.2.3.extra",
        f"{ledger.STATUS_NAME}.tmp.1.2 ",
        f"evil/{ledger.STATUS_NAME}.tmp.1.2",
    ):
        assert not ledger.is_cache_transient_name(forged), forged


def test_atomic_cache_writes_only_the_recognized_transient_name():
    with tempfile.TemporaryDirectory(prefix="izanagi_ledger_transient_") as temp:
        root = Path(temp)
        run_fd = os.open(str(root), os.O_RDONLY | os.O_DIRECTORY)
        seen = []
        try:
            def watching_write(fd, payload):
                seen.extend(
                    name for name in os.listdir(str(root))
                    if name != ledger.STATUS_NAME
                )
                return os.write(fd, payload)

            ledger._atomic_cache_at(
                run_fd, ledger.STATUS_NAME, b"{}\n",
                write=watching_write, fsync=os.fsync,
            )
        finally:
            os.close(run_fd)
        assert seen and all(ledger.is_cache_transient_name(name) for name in seen), seen
        assert (root / ledger.STATUS_NAME).read_bytes() == b"{}\n"
        assert os.listdir(str(root)) == [ledger.STATUS_NAME]


def _run():
    functions = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = errors = 0
    for function in functions:
        try:
            function()
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {function.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {function.__name__}:")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed, {errors} errors (of {len(functions)})")
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
