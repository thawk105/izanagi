# -*- coding: utf-8 -*-
"""Strict env attestation probe, comparator, and calibration admission tests."""
from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
if str(_ORCH) not in sys.path:
    sys.path.insert(0, str(_ORCH))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from calibrator import schema_v2 as sv2  # noqa: E402
from campaign import env_attestation as ea  # noqa: E402
from campaign import env_contract as ec  # noqa: E402
from campaign import execution_guard as eg  # noqa: E402
from test_schema_v2 import _valid_document  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _probe_tree(
    tmp_path: Path, *, cpu_ids: tuple[int, ...] = tuple(range(5)),
) -> ea.ProbeRoots:
    proc = tmp_path / "proc"
    sys_cpu = tmp_path / "sys/devices/system/cpu"
    sys_node = tmp_path / "sys/devices/system/node"
    proc.mkdir()
    cpuinfo_blocks = []
    for cpu in cpu_ids:
        mhz = f"{2390.0 + 5.0 * cpu:.3f}"
        cpuinfo_blocks.append(
            f"processor : {cpu}\n"
            "vendor_id : GenuineIntel\n"
            "cpu family : 6\n"
            "model : 143\n"
            "model name : Intel(R)  Xeon(TM) Test CPU @ 2.40GHz\n"
            f"cpu MHz : {mhz}\n"
        )
        cpu_root = sys_cpu / f"cpu{cpu}"
        _write(cpu_root / "topology/core_id", f"{cpu}\n")
        _write(cpu_root / "cpufreq/scaling_governor", "performance\n")
        cache = cpu_root / "cache/index0"
        _write(cache / "level", "1\n")
        _write(cache / "type", "Data\n")
        _write(cache / "size", "32K\n")
        _write(cache / "coherency_line_size", "64\n")
        _write(cache / "shared_cpu_list", f"{cpu}\n")
    _write(proc / "cpuinfo", "\n".join(cpuinfo_blocks))
    _write(proc / "mounts", "proc /proc proc rw,nosuid,nodev,noexec 0 0\n")
    _write(proc / "2/comm", "kthreadd\n")
    _write(sys_node / "node0/cpulist", ",".join(map(str, reversed(cpu_ids))) + "\n")
    return ea.ProbeRoots(proc=proc, sys_cpu=sys_cpu, sys_node=sys_node)


class _FakeCpuinfoRuntime:
    def __init__(
        self,
        roots: ea.ProbeRoots,
        *,
        original_affinity: set[int] | None = None,
        snapshots: list[tuple[dict[str, object], dict[int, float]]] | None = None,
        reader_outlier_from_actual_processor: bool = False,
    ) -> None:
        self.roots = roots
        self.original_affinity = set(
            original_affinity if original_affinity is not None else range(5)
        )
        self.affinity = set(self.original_affinity)
        self.snapshots = snapshots
        self.requested_targets: list[int] = []
        self.read_starts_ns: list[int] = []
        self.sleep_calls: list[float] = []
        self.events: list[tuple[str, object]] = []
        self.now_ns = 0
        self.last_target: int | None = None
        self.actual_processor = min(self.original_affinity, default=None)
        self.read_processor_history: list[int] = []
        self.emitted_vectors: list[dict[int, float]] = []
        self.reader_outlier_from_actual_processor = reader_outlier_from_actual_processor
        self.wrong_pre_processor = False
        self.wrong_post_processor = False
        self.widen_affinity_during_sleep = False
        self.noop_singleton_set = False
        self.fail_singleton_set = False
        self.fail_read_at: int | None = None
        self.fail_restore = False
        self.noop_restore = False
        self.get_call_count = 0
        self.fail_get_at: int | None = None
        self.read_delay_ns = 0
        self.runtime_read_calls = 0

    def get_affinity(self) -> set[int]:
        self.events.append(("get", tuple(sorted(self.affinity))))
        call_index = self.get_call_count
        self.get_call_count += 1
        if self.fail_get_at == call_index:
            raise OSError("get affinity failed")
        return set(self.affinity)

    def set_affinity(self, cpus: set[int]) -> None:
        requested = set(cpus)
        self.events.append(("set", tuple(sorted(requested))))
        if len(requested) == 1:
            self.last_target = next(iter(requested))
            self.requested_targets.append(self.last_target)
            if self.fail_singleton_set:
                raise OSError("pin failed")
            self.actual_processor = self.last_target
            if not self.noop_singleton_set:
                self.affinity = requested
            return
        if self.fail_restore:
            raise OSError("restore failed")
        if not self.noop_restore:
            self.affinity = requested

    def current_processor(self, proc_root: Path) -> int:
        phase = "post" if self.events and self.events[-1][0] == "read" else "pre"
        self.events.append((f"processor-{phase}", proc_root))
        if self.actual_processor is None:
            raise RuntimeError("processor requested before target")
        if ((phase == "pre" and self.wrong_pre_processor)
                or (phase == "post" and self.wrong_post_processor)):
            return 99
        return self.actual_processor

    def read_cpuinfo(
        self, path: Path,
    ) -> tuple[dict[str, object], dict[int, float]]:
        self.events.append(("read", path))
        self.read_starts_ns.append(self.now_ns)
        read_index = self.runtime_read_calls
        self.runtime_read_calls += 1
        if self.fail_read_at == read_index:
            raise OSError("scripted cpuinfo read failure")
        if self.snapshots is None:
            result = ea._parse_cpuinfo(path)
        else:
            result = self.snapshots[read_index]
        identity, mhz_by_cpu = result
        identity = dict(identity)
        mhz_by_cpu = dict(mhz_by_cpu)
        if self.reader_outlier_from_actual_processor:
            if self.actual_processor is None:
                raise RuntimeError("cpuinfo read before processor selection")
            self.read_processor_history.append(self.actual_processor)
            mhz_by_cpu = {
                cpu: (3000.0 if cpu == self.actual_processor else 2101.0)
                for cpu in mhz_by_cpu
            }
            self.emitted_vectors.append(dict(mhz_by_cpu))
        self.now_ns += self.read_delay_ns
        return identity, mhz_by_cpu

    def monotonic_ns(self) -> int:
        self.events.append(("clock", self.now_ns))
        return self.now_ns

    def sleep(self, seconds: float) -> None:
        self.events.append(("sleep", seconds))
        self.sleep_calls.append(seconds)
        self.now_ns += round(seconds * 1_000_000_000)
        if self.widen_affinity_during_sleep:
            self.affinity = set(self.original_affinity)


def _patch_runtime_probe(
    monkeypatch,
    roots: ea.ProbeRoots,
    **runtime_kwargs,
) -> _FakeCpuinfoRuntime:
    monkeypatch.setattr(
        ea, "_measure_tsc_profile",
        lambda: sv2.TscProfile(
            raw_samples_mhz=[1800.0, 1800.1, 1799.9, 1800.0, 1800.0],
            median_mhz=1800.0,
            clocks_per_us_int=1800,
            source="clock_gettime-monotonic/rdtscp",
        ),
    )
    return _FakeCpuinfoRuntime(roots, **runtime_kwargs)


def test_probe_fixture_tree_returns_frozen_schema_profile(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    profile = ea.probe(roots, cpuinfo_runtime=runtime)
    assert isinstance(profile, sv2.ObservedAttestationProfile)
    assert profile.cpu == sv2.CpuProfile(
        vendor="GenuineIntel", family=6, model=143,
        model_name_raw="Intel(R)  Xeon(TM) Test CPU @ 2.40GHz",
        model_name_normalized="Intel Xeon Test CPU",
    )
    assert profile.cores == sv2.CoreProfile(
        physical=5, logical=5, smt_active=False, affinity_visible=5,
    )
    assert [item.shared_cpus for item in profile.cache_topology] == [
        [0], [1], [2], [3], [4],
    ]
    assert profile.numa == [sv2.NumaNode(node_id=0, cpulist=[0, 1, 2, 3, 4])]
    assert profile.tsc.clocks_per_us_int == 1800
    assert profile.effective_clock.samples_mhz == [2390.0, 2395.0, 2400.0, 2405.0, 2410.0]
    assert profile.effective_clock.method == (
        "proc-cpuinfo-rotating-min/k5/interval-ns50000000/"
        "sysfs-affinity-intersection-evenly-spaced-v1"
    )
    assert profile.effective_clock.governor == "performance"
    assert not hasattr(profile.effective_clock, "tolerance_pct")
    assert profile.visibility == sv2.VisibilityProfile(
        hidepid="0", pid_ns_shared_with_host=True,
        pid_ns_method="proc2-kthreadd",
    )
    assert ea.normalize_observed_profile(ea.observed_profile_to_dict(profile)) == profile


def test_probe_rejects_mixed_governors_across_visible_cpus(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    _write(roots.sys_cpu / "cpu1/cpufreq/scaling_governor", "powersave\n")
    with pytest.raises(ea.AttestationError, match="governor"):
        ea.probe(roots, cpuinfo_runtime=runtime)


@pytest.mark.parametrize("failure", [
    "cache-field", "cache-index", "cpuinfo", "hidepid",
])
def test_probe_rejects_partial_or_hidden_observation(tmp_path, monkeypatch, failure):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    if failure == "cache-field":
        (roots.sys_cpu / "cpu1/cache/index0/size").unlink()
    elif failure == "cache-index":
        cache = roots.sys_cpu / "cpu0/cache/index1"
        _write(cache / "level", "2\n")
        _write(cache / "type", "Unified\n")
        _write(cache / "size", "1M\n")
        _write(cache / "coherency_line_size", "64\n")
        _write(cache / "shared_cpu_list", "0\n")
    elif failure == "cpuinfo":
        text = (roots.proc / "cpuinfo").read_text(encoding="utf-8")
        (roots.proc / "cpuinfo").write_text(
            text.replace("model name :", "missing name :", 1), encoding="utf-8",
        )
    elif failure == "hidepid":
        (roots.proc / "mounts").write_text(
            "proc /proc proc rw,hidepid=2 0 0\n", encoding="utf-8",
        )
    with pytest.raises(ea.AttestationError):
        ea.probe(roots, cpuinfo_runtime=runtime)


@pytest.mark.parametrize("proc2_state", ["missing", "mismatch"])
def test_probe_records_non_host_pid_namespace_without_probe_error(
        tmp_path, monkeypatch, proc2_state):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    proc2_comm = roots.proc / "2/comm"
    if proc2_state == "missing":
        proc2_comm.unlink()
    else:
        proc2_comm.write_text("not-kthreadd\n", encoding="utf-8")
    visibility = ea.probe(roots, cpuinfo_runtime=runtime).visibility
    assert visibility.pid_ns_shared_with_host is False
    assert visibility.pid_ns_method == "proc2-kthreadd"


def test_probe_rejects_unexpected_proc2_comm_oserror(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    (roots.proc / "2/comm").unlink()
    (roots.proc / "2/comm").mkdir()
    with pytest.raises(ea.AttestationError, match="/proc/2/comm"):
        ea.probe(roots, cpuinfo_runtime=runtime)


def _snapshots(
    roots: ea.ProbeRoots, vectors: list[dict[int, float]],
) -> list[tuple[dict[str, object], dict[int, float]]]:
    identity, _ = ea._parse_cpuinfo(roots.proc / "cpuinfo")
    return [(dict(identity), dict(vector)) for vector in vectors]


def _clock_verdict(samples: list[float]) -> bool:
    return eg.effective_clock_comparison_passes(
        {"samples_mhz": [2100.0] * len(samples), "tolerance_pct": 2.0},
        {"samples_mhz": samples},
    )


def test_alpha_method_identity_and_target_selection_are_versioned():
    assert ea.EFFECTIVE_CLOCK_ALPHA_K == 5
    assert ea.EFFECTIVE_CLOCK_ALPHA_INTERVAL_NS == 50_000_000
    assert ea.EFFECTIVE_CLOCK_ALPHA_RULE_ID == (
        "sysfs-affinity-intersection-evenly-spaced-v1"
    )
    assert ea.EFFECTIVE_CLOCK_METHOD == (
        "proc-cpuinfo-rotating-min/k5/interval-ns50000000/"
        "sysfs-affinity-intersection-evenly-spaced-v1"
    )
    assert ea._select_evenly_spaced_cpu_ids(
        set(range(9)), ea.EFFECTIVE_CLOCK_ALPHA_K, ea.EFFECTIVE_CLOCK_ALPHA_RULE_ID,
    ) == [0, 2, 4, 6, 8]


def test_current_processor_reads_thread_self_stat(tmp_path):
    proc = tmp_path / "proc"
    thread_fields = ["S", *("0" for _ in range(35)), "7"]
    leader_fields = ["S", *("0" for _ in range(35)), "3"]
    _write(proc / "thread-self/stat", f"123 (worker thread) {' '.join(thread_fields)}\n")
    _write(proc / "self/stat", f"100 (leader) {' '.join(leader_fields)}\n")
    assert ea._current_processor(proc) == 7


def test_probe_alpha_accepts_quiet_in_band_reads(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    vectors = [
        {cpu: 2100.0 + cpu + read_index for cpu in range(5)}
        for read_index in range(5)
    ]
    runtime = _patch_runtime_probe(
        monkeypatch, roots, snapshots=_snapshots(roots, vectors),
    )
    profile = ea.probe(roots, cpuinfo_runtime=runtime)
    assert len({tuple(sorted(vector.items())) for vector in vectors}) == 5
    assert all(_clock_verdict(list(vector.values())) for vector in vectors)
    assert profile.effective_clock.samples_mhz == [
        2100.0, 2101.0, 2102.0, 2103.0, 2104.0,
    ]
    assert _clock_verdict(profile.effective_clock.samples_mhz)
    assert set(ea.observed_profile_to_dict(profile)["effective_clock"]) == {
        "samples_mhz", "method", "governor",
    }
    assert runtime.requested_targets == [0, 1, 2, 3, 4]
    assert runtime.affinity == runtime.original_affinity


def test_probe_alpha_rotating_min_accepts_migrating_reader_outlier(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path, cpu_ids=tuple(range(9)))
    runtime = _patch_runtime_probe(
        monkeypatch,
        roots,
        original_affinity=set(range(9)),
        reader_outlier_from_actual_processor=True,
    )
    profile = ea.probe(roots, cpuinfo_runtime=runtime)
    assert len(runtime.read_processor_history) == 5
    assert len(runtime.emitted_vectors) == 5
    assert all(
        vector[processor] == 3000.0
        for processor, vector in zip(
            runtime.read_processor_history, runtime.emitted_vectors,
        )
    )
    assert all(
        not _clock_verdict(list(vector.values()))
        for vector in runtime.emitted_vectors
    )
    assert profile.effective_clock.samples_mhz == [2101.0] * 9
    assert _clock_verdict(profile.effective_clock.samples_mhz)
    assert runtime.runtime_read_calls == 5
    assert runtime.affinity == set(range(9))


def test_probe_alpha_rotates_through_selected_targets(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path, cpu_ids=tuple(range(9)))
    runtime = _patch_runtime_probe(
        monkeypatch, roots, original_affinity=set(range(9)),
    )
    ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.requested_targets == [0, 2, 4, 6, 8]


def test_probe_alpha_rotating_min_keeps_persistent_outlier_rejected(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path, cpu_ids=tuple(range(9)))
    vectors = [
        {cpu: (3000.0 if cpu == 1 else 2101.0) for cpu in range(9)}
        for _ in range(5)
    ]
    runtime = _patch_runtime_probe(
        monkeypatch,
        roots,
        original_affinity=set(range(9)),
        snapshots=_snapshots(roots, vectors),
    )
    profile = ea.probe(roots, cpuinfo_runtime=runtime)
    assert profile.effective_clock.samples_mhz[1] == 3000.0
    assert not _clock_verdict(profile.effective_clock.samples_mhz)


def test_alpha_min_characterization_is_asymmetric():
    identity = {"vendor": "test"}
    high_then_in_band = [
        (identity, {0: value}) for value in [3000.0, 3000.0, 3000.0, 3000.0, 2100.0]
    ]
    in_band_then_low = [
        (identity, {0: value}) for value in [2100.0, 2100.0, 2100.0, 2100.0, 2000.0]
    ]
    _, accepted = ea._reduce_cpuinfo_reads(high_then_in_band, {0})
    _, rejected = ea._reduce_cpuinfo_reads(in_band_then_low, {0})
    assert accepted == {0: 2100.0}
    assert _clock_verdict([accepted[0]])
    assert rejected == {0: 2000.0}
    assert not _clock_verdict([rejected[0]])


def test_alpha_reducer_takes_per_cpu_minimum():
    identity = {"vendor": "test", "model": 1}
    reads = [
        (identity, {0: 2100.0 + index, 1: 2110.0 - index})
        for index in range(5)
    ]
    reduced_identity, minima = ea._reduce_cpuinfo_reads(reads, {0, 1})
    assert reduced_identity == identity
    assert minima == {0: 2100.0, 1: 2106.0}

    with pytest.raises(ea.AttestationError, match="read 数"):
        ea._reduce_cpuinfo_reads(reads[:-1], {0, 1})


def test_alpha_reducer_rejects_extra_cpu_set_drift():
    identity = {"vendor": "test", "model": 1}
    reads = [(identity, {0: 2100.0, 1: 2110.0}) for _ in range(5)]
    reads[1][1][99] = 2105.0
    with pytest.raises(ea.AttestationError, match="processor 集合"):
        ea._reduce_cpuinfo_reads(reads, {0, 1})


def test_alpha_reducer_rejects_identity_drift():
    identity = {"vendor": "test", "model": 1}
    reads = [(identity, {0: 2100.0, 1: 2110.0}) for _ in range(5)]
    reads[1] = ({"vendor": "other", "model": 1}, reads[1][1])
    with pytest.raises(ea.AttestationError, match="identity"):
        ea._reduce_cpuinfo_reads(reads, {0, 1})


def test_probe_alpha_rejects_fewer_than_k_affinity_without_read(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path, cpu_ids=(0, 1))
    runtime = _patch_runtime_probe(
        monkeypatch, roots, original_affinity={0, 1},
    )
    with pytest.raises(ea.AttestationError, match="affinity CPU が不足"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.requested_targets == []
    assert runtime.runtime_read_calls == 0


@pytest.mark.parametrize("failure,match", [
    ("error", "sched_getaffinity"),
    ("empty", "空の CPU 集合"),
])
def test_probe_alpha_rejects_unavailable_or_empty_original_affinity_without_read(
        tmp_path, monkeypatch, failure, match):
    roots = _probe_tree(tmp_path)
    original = set() if failure == "empty" else set(range(5))
    runtime = _patch_runtime_probe(
        monkeypatch, roots, original_affinity=original,
    )
    if failure == "error":
        runtime.fail_get_at = 0
    with pytest.raises(ea.AttestationError, match=match):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.requested_targets == []
    assert runtime.runtime_read_calls == 0


def test_probe_alpha_rejects_noop_set_by_mask_check_alone(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.noop_singleton_set = True
    with pytest.raises(ea.AttestationError, match="pin mask"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.runtime_read_calls == 0
    assert runtime.affinity == runtime.original_affinity


def test_probe_alpha_rejects_affinity_widened_during_interval_wait(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.widen_affinity_during_sleep = True
    with pytest.raises(ea.AttestationError, match="pin mask"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.runtime_read_calls == 1
    assert runtime.affinity == runtime.original_affinity


def test_probe_alpha_set_error_has_no_runtime_or_direct_parser_fallback(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    parsed = ea._parse_cpuinfo(roots.proc / "cpuinfo")
    runtime = _patch_runtime_probe(
        monkeypatch, roots, snapshots=[parsed for _ in range(5)],
    )
    runtime.fail_singleton_set = True
    direct_parser_calls = []

    def direct_parser_spy(path):
        direct_parser_calls.append(path)
        return parsed

    monkeypatch.setattr(ea, "_parse_cpuinfo", direct_parser_spy)
    with pytest.raises(ea.AttestationError, match="pin に失敗"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.runtime_read_calls == 0
    assert direct_parser_calls == []
    assert runtime.affinity == runtime.original_affinity


def test_probe_alpha_rejects_wrong_reader_cpu_at_pre_check(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.wrong_pre_processor = True
    with pytest.raises(ea.AttestationError, match="pre processor"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.affinity == runtime.original_affinity
    assert runtime.runtime_read_calls == 0


def test_probe_alpha_rejects_wrong_reader_cpu_at_post_check(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.wrong_post_processor = True
    with pytest.raises(ea.AttestationError, match="post processor"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.affinity == runtime.original_affinity
    assert runtime.runtime_read_calls == 1


def test_probe_alpha_rejects_partial_k_read_and_restores_affinity(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.fail_read_at = 2
    with pytest.raises(ea.AttestationError, match="read 2"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.runtime_read_calls == 3
    assert runtime.requested_targets == [0, 1, 2]
    assert runtime.affinity == runtime.original_affinity


def test_probe_alpha_rejects_extra_cpu_set_drift_between_reads(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    identity, _ = ea._parse_cpuinfo(roots.proc / "cpuinfo")
    snapshots = [
        (dict(identity), {cpu: 2100.0 for cpu in range(5)}) for _ in range(5)
    ]
    snapshots[1][1][99] = 2100.0
    runtime = _patch_runtime_probe(monkeypatch, roots, snapshots=snapshots)
    with pytest.raises(ea.AttestationError, match="processor 集合"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.runtime_read_calls == 5
    assert runtime.affinity == runtime.original_affinity


def test_probe_alpha_rejects_identity_drift_between_reads(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    identity, _ = ea._parse_cpuinfo(roots.proc / "cpuinfo")
    snapshots = [
        (dict(identity), {cpu: 2100.0 for cpu in range(5)}) for _ in range(5)
    ]
    snapshots[1][0]["model_name_raw"] = "drifted"
    runtime = _patch_runtime_probe(monkeypatch, roots, snapshots=snapshots)
    with pytest.raises(ea.AttestationError, match="identity"):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.runtime_read_calls == 5
    assert runtime.affinity == runtime.original_affinity


def test_probe_alpha_pin_failure_keeps_primary_when_restore_also_fails(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.fail_singleton_set = True
    runtime.fail_restore = True
    with pytest.raises(ea.AttestationError) as exc_info:
        ea.probe(roots, cpuinfo_runtime=runtime)
    message = str(exc_info.value)
    assert "pin に失敗" in message
    assert "復元設定に失敗" in message


def test_probe_alpha_read_failure_keeps_primary_when_restore_also_fails(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.fail_read_at = 2
    runtime.fail_restore = True
    with pytest.raises(ea.AttestationError) as exc_info:
        ea.probe(roots, cpuinfo_runtime=runtime)
    message = str(exc_info.value)
    assert "read 2" in message
    assert "復元設定に失敗" in message


@pytest.mark.parametrize("restore_mode,match", [
    ("error", "復元設定"),
    ("no-op", "復元が不一致"),
    ("get-error", "復元後再取得"),
])
def test_probe_alpha_restore_failure_is_fatal(
        tmp_path, monkeypatch, restore_mode, match):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.fail_restore = restore_mode == "error"
    runtime.noop_restore = restore_mode == "no-op"
    if restore_mode == "get-error":
        runtime.fail_get_at = 6
    with pytest.raises(ea.AttestationError, match=match):
        ea.probe(roots, cpuinfo_runtime=runtime)
    assert runtime.runtime_read_calls == 5


def test_probe_alpha_read_starts_are_at_least_interval_apart(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    ea.probe(roots, cpuinfo_runtime=runtime)
    assert len(runtime.read_starts_ns) == ea.EFFECTIVE_CLOCK_ALPHA_K
    assert all(
        later - earlier >= ea.EFFECTIVE_CLOCK_ALPHA_INTERVAL_NS
        for earlier, later in zip(runtime.read_starts_ns, runtime.read_starts_ns[1:])
    )
    assert runtime.read_starts_ns[-1] - runtime.read_starts_ns[0] >= (
        (ea.EFFECTIVE_CLOCK_ALPHA_K - 1) * ea.EFFECTIVE_CLOCK_ALPHA_INTERVAL_NS
    )


def test_probe_alpha_accepts_late_reads_without_shortening_horizon(
        tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _patch_runtime_probe(monkeypatch, roots)
    runtime.read_delay_ns = 80_000_000
    profile = ea.probe(roots, cpuinfo_runtime=runtime)
    assert profile.effective_clock.samples_mhz == [
        2390.0, 2395.0, 2400.0, 2405.0, 2410.0,
    ]
    assert runtime.sleep_calls == []
    assert all(
        later - earlier >= ea.EFFECTIVE_CLOCK_ALPHA_INTERVAL_NS
        for earlier, later in zip(runtime.read_starts_ns, runtime.read_starts_ns[1:])
    )


def test_probe_measures_tsc_only_after_exact_affinity_restore(tmp_path, monkeypatch):
    roots = _probe_tree(tmp_path)
    runtime = _FakeCpuinfoRuntime(roots)

    def measured_tsc():
        runtime.events.append(("tsc", tuple(sorted(runtime.affinity))))
        return sv2.TscProfile(
            raw_samples_mhz=[1800.0] * 5,
            median_mhz=1800.0,
            clocks_per_us_int=1800,
            source="clock_gettime-monotonic/rdtscp",
        )

    monkeypatch.setattr(ea, "_measure_tsc_profile", measured_tsc)
    ea.probe(roots, cpuinfo_runtime=runtime)
    tsc_index = runtime.events.index(("tsc", tuple(sorted(runtime.original_affinity))))
    restore_set_index = max(
        index for index, event in enumerate(runtime.events)
        if event == ("set", tuple(sorted(runtime.original_affinity)))
    )
    restore_get_index = max(
        index for index, event in enumerate(runtime.events[:tsc_index])
        if event == ("get", tuple(sorted(runtime.original_affinity)))
    )
    assert restore_set_index < restore_get_index < tsc_index


def test_required_tsc_probe_has_no_fallback(monkeypatch):
    monkeypatch.setattr(ea._tsc, "measure_tsc", lambda **_kwargs: None)
    with pytest.raises(ea.AttestationError, match="fallback 禁止"):
        ea._measure_tsc_profile()


def _profile() -> sv2.AttestationProfile:
    document = _valid_document()
    # U-2 の current issuer accepted set は policy 2.0 に縮小した。
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = 2.0
    return sv2.validate_calibration_v2(document).attestation_profile


def _observed(profile: sv2.AttestationProfile) -> sv2.ObservedAttestationProfile:
    raw = ea.profile_to_dict(profile)
    del raw["effective_clock"]["tolerance_pct"]
    return ea.normalize_observed_profile(raw)


def _observed_comparison_fixture(
    profile: sv2.AttestationProfile,
) -> sv2.ObservedAttestationProfile:
    """Build comparator input without applying raw parser invariants."""
    return sv2.ObservedAttestationProfile(
        cpu=profile.cpu,
        cores=profile.cores,
        cache_topology=profile.cache_topology,
        numa=profile.numa,
        tsc=profile.tsc,
        effective_clock=sv2.ObservedEffectiveClockProfile(
            samples_mhz=profile.effective_clock.samples_mhz,
            method=profile.effective_clock.method,
            governor=profile.effective_clock.governor,
        ),
        visibility=profile.visibility,
    )


def _replace_cpu(profile, **values):
    return dataclasses.replace(profile, cpu=dataclasses.replace(profile.cpu, **values))


def _replace_clock(profile, **values):
    return dataclasses.replace(
        profile,
        effective_clock=dataclasses.replace(profile.effective_clock, **values),
    )


@pytest.mark.parametrize("field,mutate", [
    ("cpu.vendor", lambda p: _replace_cpu(p, vendor="OtherVendor")),
    ("cpu.family", lambda p: _replace_cpu(p, family=7)),
    ("cpu.model", lambda p: _replace_cpu(p, model=144)),
    ("cpu.model_name_raw", lambda p: _replace_cpu(p, model_name_raw="Different CPU")),
    ("cpu.model_name_normalized", lambda p: _replace_cpu(p, model_name_normalized="Different CPU")),
    ("cores.physical", lambda p: dataclasses.replace(
        p, cores=sv2.CoreProfile(physical=1, logical=2, smt_active=True, affinity_visible=2),
    )),
    ("cores.logical", lambda p: dataclasses.replace(
        p, cores=sv2.CoreProfile(physical=1, logical=1, smt_active=False, affinity_visible=1),
    )),
    ("cores.smt_active", lambda p: dataclasses.replace(
        p, cores=sv2.CoreProfile(physical=1, logical=2, smt_active=True, affinity_visible=2),
    )),
    ("cores.affinity_visible", lambda p: dataclasses.replace(
        p, cores=dataclasses.replace(p.cores, affinity_visible=1),
    )),
    ("cache_topology", lambda p: dataclasses.replace(
        p, cache_topology=[
            p.cache_topology[0], dataclasses.replace(p.cache_topology[1], bytes=65536),
        ],
    )),
    ("numa", lambda p: dataclasses.replace(
        p, numa=[sv2.NumaNode(node_id=0, cpulist=[0])],
    )),
    ("tsc.clocks_per_us_int", lambda p: dataclasses.replace(
        p, tsc=sv2.TscProfile(
            raw_samples_mhz=[1900.0] * 5, median_mhz=1900.0,
            clocks_per_us_int=1900, source=p.tsc.source,
        ),
    )),
    ("tsc.raw_samples_mhz", lambda p: dataclasses.replace(
        p, tsc=sv2.TscProfile(
            raw_samples_mhz=[1900.0] * 5, median_mhz=1900.0,
            clocks_per_us_int=1900, source=p.tsc.source,
        ),
    )),
    ("tsc.median_mhz", lambda p: dataclasses.replace(
        p, tsc=sv2.TscProfile(
            raw_samples_mhz=[1900.0] * 5, median_mhz=1900.0,
            clocks_per_us_int=1900, source=p.tsc.source,
        ),
    )),
    ("tsc.source", lambda p: dataclasses.replace(
        p, tsc=dataclasses.replace(p.tsc, source="different-source"),
    )),
    ("effective_clock.samples_mhz", lambda p: _replace_clock(
        p, samples_mhz=[3000.0, 3010.0, 2990.0],
    )),
    ("effective_clock.method", lambda p: _replace_clock(p, method="different-method")),
    ("effective_clock.governor", lambda p: _replace_clock(p, governor="powersave")),
    ("visibility.hidepid", lambda p: dataclasses.replace(
        p, visibility=dataclasses.replace(p.visibility, hidepid="2"),
    )),
    ("visibility.pid_ns_shared_with_host", lambda p: dataclasses.replace(
        p, visibility=dataclasses.replace(p.visibility, pid_ns_shared_with_host=False),
    )),
])
def test_compare_profiles_reports_each_field_mismatch(field, mutate):
    expected = _profile()
    comparisons = ea.compare_profiles(
        expected,
        _observed_comparison_fixture(mutate(expected)),
        now_fn=lambda: "now",
    )
    failures = {item["field"] for item in comparisons if item["verdict"] == "fail"}
    assert field in failures


def test_compare_profiles_normalizes_raw_name_and_applies_expected_clock_tolerance():
    expected = _profile()
    observed_raw_name = "Intel Test CPU @ 2.10GHz"
    observed_expected_shape = _replace_cpu(
        expected,
        model_name_raw=observed_raw_name,
        model_name_normalized=ea.normalize_cpu_model_name(observed_raw_name),
    )
    observed_expected_shape = _replace_clock(
        observed_expected_shape, samples_mhz=[2440.0, 2448.0, 2430.0],
    )
    observed = _observed(observed_expected_shape)
    comparisons = ea.compare_profiles(expected, observed, now_fn=lambda: "now")
    by_field = {item["field"]: item["verdict"] for item in comparisons}
    assert by_field["cpu.model_name_raw"] == "pass"
    assert by_field["effective_clock.samples_mhz"] == "pass"

    outlier = _observed(_replace_clock(
        expected, samples_mhz=[2400.0, 2400.0, 3000.0],
    ))
    outlier_comparisons = ea.compare_profiles(expected, outlier, now_fn=lambda: "now")
    assert next(item for item in outlier_comparisons
                if item["field"] == "effective_clock.samples_mhz")["verdict"] == "fail"


def _probe_document(version: str) -> dict:
    profile = copy.deepcopy(_valid_document()["attestation_profile"])
    if version == ea.PEGASUS_PROBE_OUTPUT_V1:
        profile["effective_clock"]["tolerance_pct"] = 100.0
    else:
        del profile["effective_clock"]["tolerance_pct"]
    return {
        "schema_version": version,
        "ok": True,
        "observed_epoch": 1,
        "profile": profile,
    }


@pytest.mark.parametrize("sentinel", [100, 2.0, 99.0])
def test_probe_output_v1_accepts_only_exact_float_sentinel(sentinel):
    document = _probe_document(ea.PEGASUS_PROBE_OUTPUT_V1)
    document["profile"]["effective_clock"]["tolerance_pct"] = sentinel
    with pytest.raises(ea.AttestationError, match="sentinel"):
        ea.parse_probe_output(json.dumps(document))


@pytest.mark.parametrize("tolerance", [2.0, 100.0])
def test_probe_output_v2_rejects_tolerance_field(tolerance):
    document = _probe_document(ea.PEGASUS_PROBE_OUTPUT_V2)
    document["profile"]["effective_clock"]["tolerance_pct"] = tolerance
    with pytest.raises(ea.AttestationError, match="effective_clock"):
        ea.parse_probe_output(json.dumps(document))


@pytest.mark.parametrize("version", [
    ea.PEGASUS_PROBE_OUTPUT_V1,
    ea.PEGASUS_PROBE_OUTPUT_V2,
])
def test_probe_output_rejects_forged_cpu_name_pair(version):
    document = _probe_document(version)
    document["profile"]["cpu"].update({
        "model_name_raw": "Intel Xeon Platinum 8468H",
        "model_name_normalized": "Intel Xeon Platinum 8468",
    })

    with pytest.raises(ea.AttestationError, match="normalized name"):
        ea.parse_probe_output(json.dumps(document))


@pytest.mark.parametrize("version", [
    ea.PEGASUS_PROBE_OUTPUT_V1,
    ea.PEGASUS_PROBE_OUTPUT_V2,
])
@pytest.mark.parametrize("level", ["top", "profile", "effective_clock"])
def test_probe_output_rejects_duplicate_keys_at_every_raw_level(version, level):
    document = _probe_document(version)
    profile_text = json.dumps(document["profile"], separators=(",", ":"))
    if level == "profile":
        profile_text = profile_text.replace('"cpu":{', '"cpu":{},"cpu":{', 1)
    elif level == "effective_clock":
        profile_text = profile_text.replace(
            '"samples_mhz":[', '"samples_mhz":[1.0],"samples_mhz":[', 1,
        )
    raw = (
        '{"schema_version":' + json.dumps(version)
        + ',"ok":true,"observed_epoch":1,"profile":' + profile_text
        + (',"profile":' + profile_text if level == "top" else "")
        + "}"
    )
    with pytest.raises(ea.AttestationError, match="duplicate key"):
        ea.parse_probe_output(raw)


def test_observed_hash_projection_preserves_source_schema_preimage():
    v1_document = _probe_document(ea.PEGASUS_PROBE_OUTPUT_V1)
    v2_document = _probe_document(ea.PEGASUS_PROBE_OUTPUT_V2)
    parsed_v1 = ea.parse_probe_output(json.dumps(v1_document))
    parsed_v2 = ea.parse_probe_output(json.dumps(v2_document))

    def digest(profile):
        return hashlib.sha256(json.dumps(
            profile, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")).hexdigest()

    assert ea.observed_profile_sha256(parsed_v1) == digest(v1_document["profile"])
    assert ea.observed_profile_sha256(parsed_v2) == digest(v2_document["profile"])
    assert "tolerance_pct" in ea.observed_profile_projection(parsed_v1)["effective_clock"]
    assert "tolerance_pct" not in ea.observed_profile_projection(parsed_v2)["effective_clock"]


_V1_CORPUS_PAIRS = (
    ("calibration/job-staging/0:867865.nqsv/attestation-static.json", "calibration/job-staging/0:867865.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867866.nqsv/attestation-static.json", "calibration/job-staging/0:867866.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867867.nqsv/attestation-static.json", "calibration/job-staging/0:867867.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867868.nqsv/attestation-static.json", "calibration/job-staging/0:867868.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867869.nqsv/attestation-pre.json", "calibration/job-staging/0:867869.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867869.nqsv/attestation-static.json", "calibration/job-staging/0:867869.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867870.nqsv/attestation-pre.json", "calibration/job-staging/0:867870.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867870.nqsv/attestation-static.json", "calibration/job-staging/0:867870.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867872.nqsv/attestation-pre.json", "calibration/job-staging/0:867872.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867872.nqsv/attestation-static.json", "calibration/job-staging/0:867872.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867874.nqsv/attestation-pre.json", "calibration/job-staging/0:867874.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867874.nqsv/attestation-static.json", "calibration/job-staging/0:867874.nqsv/attestation-static.stdout"),
    ("calibration/job-staging/0:867876.nqsv/attestation-post.json", "calibration/job-staging/0:867876.nqsv/attestation-post.stdout"),
    ("calibration/job-staging/0:867876.nqsv/attestation-pre.json", "calibration/job-staging/0:867876.nqsv/attestation-pre.stdout"),
    ("calibration/job-staging/0:867876.nqsv/attestation-static.json", "calibration/job-staging/0:867876.nqsv/attestation-static.stdout"),
    ("smoke/0:867857.nqsv/observation.json", "smoke/0:867857.nqsv/run_probe.stdout"),
    ("smoke/0:867858.nqsv/observation.json", "smoke/0:867858.nqsv/run_probe.stdout"),
    ("smoke/0:867859.nqsv/observation.json", "smoke/0:867859.nqsv/run_probe.stdout"),
    ("smoke/0:867860.nqsv/observation.json", "smoke/0:867860.nqsv/run_probe.stdout"),
    ("smoke/0:867861.nqsv/observation.json", "smoke/0:867861.nqsv/run_probe.stdout"),
    ("smoke/0:867862.nqsv/observation.json", "smoke/0:867862.nqsv/run_probe.stdout"),
    ("silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/attestation-job.json", "silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/attestation-job.stdout"),
)
_V1_CORPUS_DOCS = {
    "calibration/attempts/0_867874.nqsv/calibration.md",
    "calibration/attempts/0_867876.nqsv/calibration.md",
    "calibration/attempts/0_892707.nqsv/calibration.md",
    "silo_ladder_rung1/README.md",
}
_V1_SUCCESS_JSONS = {
    "calibration/job-staging/0:867865.nqsv/attestation-static.json",
    "calibration/job-staging/0:867866.nqsv/attestation-static.json",
    "calibration/job-staging/0:867867.nqsv/attestation-static.json",
    "calibration/job-staging/0:867868.nqsv/attestation-static.json",
    "calibration/job-staging/0:867869.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867869.nqsv/attestation-static.json",
    "calibration/job-staging/0:867870.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867870.nqsv/attestation-static.json",
    "calibration/job-staging/0:867872.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867872.nqsv/attestation-static.json",
    "calibration/job-staging/0:867874.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867874.nqsv/attestation-static.json",
    "calibration/job-staging/0:867876.nqsv/attestation-post.json",
    "calibration/job-staging/0:867876.nqsv/attestation-pre.json",
    "calibration/job-staging/0:867876.nqsv/attestation-static.json",
    "smoke/0:867860.nqsv/observation.json",
    "smoke/0:867861.nqsv/observation.json",
    "smoke/0:867862.nqsv/observation.json",
    ("silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/"
     "attempts/1/attestation-job.json"),
}
_V1_FAILURE_JSONS = {
    "smoke/0:867857.nqsv/observation.json",
    "smoke/0:867858.nqsv/observation.json",
    "smoke/0:867859.nqsv/observation.json",
}


def test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies():
    root = _ORCH.parent / "output/env/pegasus"
    discovered_payloads = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.suffix in {".json", ".stdout"}
        and ea.PEGASUS_PROBE_OUTPUT_V1 in path.read_text(encoding="utf-8")
    }
    golden_payloads = {item for pair in _V1_CORPUS_PAIRS for item in pair}
    discovered_docs = {
        str(path.relative_to(root))
        for path in (
            *root.glob("calibration/attempts/*/calibration.md"),
            root / "silo_ladder_rung1/README.md",
        )
        if path.is_file()
    }
    assert discovered_payloads == golden_payloads
    assert discovered_docs == _V1_CORPUS_DOCS
    assert all((root / path).is_file() for path in _V1_CORPUS_DOCS)
    assert len(golden_payloads | discovered_docs) == 48
    assert _V1_SUCCESS_JSONS.isdisjoint(_V1_FAILURE_JSONS)
    assert _V1_SUCCESS_JSONS | _V1_FAILURE_JSONS == {
        pair[0] for pair in _V1_CORPUS_PAIRS
    }

    registered_ref = ec.lookup("pegasus").calibration_ref
    registered_raw = (_ORCH.parent / registered_ref.path).read_bytes()
    assert hashlib.sha256(registered_raw).hexdigest() == registered_ref.sha256
    registered = json.loads(registered_raw)
    expected_clock = {
        "samples_mhz": registered["attestation_profile"]["effective_clock"]["samples_mhz"],
        "tolerance_pct": 2.0,
    }
    observed_success = set()
    observed_failure = set()
    for json_rel, stdout_rel in _V1_CORPUS_PAIRS:
        json_raw = (root / json_rel).read_bytes()
        stdout_raw = (root / stdout_rel).read_bytes()
        assert json.loads(json_raw) == json.loads(stdout_raw)
        parsed = ea.parse_probe_output(json_raw)
        if not parsed.ok:
            observed_failure.add(json_rel)
            continue
        observed_success.add(json_rel)
        assert parsed.profile is not None
        observed_samples = parsed.profile.effective_clock.samples_mhz
        expected_median = statistics.median(expected_clock["samples_mhz"])
        observed_median = statistics.median(observed_samples)
        assert abs(observed_median - expected_median) <= expected_median * 0.02
        assert not eg.effective_clock_comparison_passes(
            expected_clock, {"samples_mhz": observed_samples},
        )
    assert observed_success == _V1_SUCCESS_JSONS
    assert observed_failure == _V1_FAILURE_JSONS


def _required_artifact(tmp_path: Path, doc: dict | None = None, *, raw: bytes | None = None):
    document = copy.deepcopy(doc if doc is not None else _valid_document())
    if doc is None:
        # U-2 の required-loader accepted set は policy 2.0 に縮小した。
        document["attestation_profile"]["effective_clock"]["tolerance_pct"] = 2.0
    artifact_raw = raw if raw is not None else json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    artifact = tmp_path / "calibration.json"
    artifact.write_bytes(artifact_raw)
    contract = ec.ExecutionEnvironmentContract(
        env_tag=document["env_tag"], clocks_per_us=document["clocks_per_us"],
        numactl=(), attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(
            path="calibration.json", sha256=hashlib.sha256(artifact_raw).hexdigest(),
        ),
    )
    return artifact, contract


def test_load_verified_calibration_accepts_result_to_dict_derived_v2(tmp_path):
    _, contract = _required_artifact(tmp_path)
    verified = ea.load_verified_calibration(contract, tmp_path)
    assert verified.schema_version == sv2.SCHEMA_VERSION
    assert verified.calibration is not None
    assert verified.calibration.env_tag == contract.env_tag
    assert verified.attestation_profile_sha256 == ea.profile_sha256(_profile())


@pytest.mark.parametrize("tolerance", [
    math.nextafter(2.0, math.inf),
    math.nextafter(2.0, -math.inf),
    2.5,
    2.9,
])
def test_loader_rejects_well_formed_nonpolicy_tolerance(tmp_path, tolerance):
    document = _valid_document()
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = tolerance
    _, contract = _required_artifact(tmp_path, document)
    with pytest.raises(ea.AttestationError, match="current policy"):
        ea.load_verified_calibration(contract, tmp_path)


@pytest.mark.parametrize("tolerance", [
    math.nextafter(2.0, math.inf),
    math.nextafter(2.0, -math.inf),
    2.5,
    2.9,
])
def test_issuer_rejects_every_nonpolicy_equality_edge(tolerance):
    expected = dataclasses.replace(
        _profile(),
        effective_clock=dataclasses.replace(
            _profile().effective_clock,
            samples_mhz=[100.0],
            tolerance_pct=tolerance,
        ),
    )
    observed = _observed(dataclasses.replace(
        _profile(),
        effective_clock=dataclasses.replace(
            _profile().effective_clock, samples_mhz=[100.0],
        ),
    ))
    comparisons = ea.compare_profiles(expected, observed, now_fn=lambda: "now")
    clock = next(row for row in comparisons
                 if row["field"] == "effective_clock.samples_mhz")
    assert clock["verdict"] == "fail"


def test_load_verified_calibration_rejects_sha_mismatch(tmp_path):
    _, contract = _required_artifact(tmp_path)
    bad = dataclasses.replace(
        contract,
        calibration_ref=dataclasses.replace(contract.calibration_ref, sha256="0" * 64),
    )
    with pytest.raises(ea.AttestationError, match="sha256 不一致"):
        ea.load_verified_calibration(bad, tmp_path)


def test_load_verified_calibration_hashes_and_parses_one_read(tmp_path, monkeypatch):
    artifact, contract = _required_artifact(tmp_path)
    original_read_bytes = Path.read_bytes
    reads = []

    def swapping_read(path):
        data = original_read_bytes(path)
        if path == artifact:
            reads.append(path)
            path.write_bytes(b'{"replaced":true}')
        return data

    monkeypatch.setattr(Path, "read_bytes", swapping_read)
    verified = ea.load_verified_calibration(contract, tmp_path)
    assert verified.calibration is not None
    assert reads == [artifact]
    assert artifact.read_text(encoding="utf-8") == '{"replaced":true}'


def test_load_verified_calibration_rejects_duplicate_key(tmp_path):
    raw = json.dumps(_valid_document(), ensure_ascii=False, separators=(",", ":"))
    duplicate = ('{"schema_version":"calibration/v2",' + raw[1:]).encode("utf-8")
    _, contract = _required_artifact(tmp_path, raw=duplicate)
    with pytest.raises(ea.AttestationError, match="duplicate key"):
        ea.load_verified_calibration(contract, tmp_path)


@pytest.mark.parametrize("field,value", [("env_tag", "other-env"), ("clocks_per_us", 1801)])
def test_load_verified_calibration_rejects_contract_cross_field(tmp_path, field, value):
    _, contract = _required_artifact(tmp_path)
    bad = dataclasses.replace(contract, **{field: value})
    with pytest.raises(ea.AttestationError, match=field):
        ea.load_verified_calibration(bad, tmp_path)


def test_load_verified_calibration_rejects_repo_escape(tmp_path):
    outside = tmp_path.parent / "outside-calibration.json"
    outside.write_text("{}", encoding="utf-8")
    contract = ec.ExecutionEnvironmentContract(
        env_tag="test-env", clocks_per_us=1800, numactl=(),
        attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(
            path="../outside-calibration.json",
            sha256=hashlib.sha256(b"{}").hexdigest(),
        ),
    )
    with pytest.raises(ea.AttestationError, match="repo_root 外"):
        ea.load_verified_calibration(contract, tmp_path)


def test_load_verified_calibration_accepts_exact_grandfathered_v1():
    repo_root = _ORCH.parent
    verified = ea.load_verified_calibration(ec.lookup("linux-baremetal"), repo_root)
    assert verified.schema_version == "calibration/v1"
    assert verified.sha256 == ea.GRANDFATHERED_V1_SHA256
    assert verified.calibration is None


def test_mode_none_rejects_hash_bound_but_non_grandfathered_v1(tmp_path):
    source = (_ORCH.parent / ec.lookup("linux-baremetal").calibration_ref.path).read_bytes()
    mutated = source + b"\n"
    artifact = tmp_path / "mutated-v1.json"
    artifact.write_bytes(mutated)
    base = ec.lookup("linux-baremetal")
    contract = dataclasses.replace(
        base,
        calibration_ref=ec.CalibrationRef(
            path=artifact.name,
            sha256=hashlib.sha256(mutated).hexdigest(),
        ),
    )
    with pytest.raises(ea.AttestationError, match="grandfathered"):
        ea.load_verified_calibration(contract, tmp_path)


def test_grandfathered_sha_is_module_constant_without_env_literal():
    source = Path(ea.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignments = [
        node for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name)
                and target.id == "GRANDFATHERED_V1_SHA256" for target in node.targets)
    ]
    assert len(assignments) == 1
    assert "linux-baremetal" not in source


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
