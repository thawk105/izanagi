"""Pegasus balanced backoff profile の裁定 R1-R15 を固定する焦点テスト。"""
from __future__ import annotations

import ast
import contextlib
import inspect
import json
import os
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign import backoff_profile as subject  # noqa: E402
from orchestrator.campaign import pin  # noqa: E402
from orchestrator.tests import test_official_perf_closure as official_closure  # noqa: E402


def _workload() -> dict[str, str]:
    return {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}


def _runtime(**overrides) -> subject._ProfileRuntime:
    values = {
        "env_tag": "pegasus",
        "clocks_per_us": 2100,
        "numactl": ("numactl", "--interleave=all"),
        "profiler_executable": "/opt/checked/bin/perf",
        "cc": "gcc",
        "cxx": "g++",
        "site": "pegasus-compute",
        "contract_sha256": "a" * 64,
        "calibration_ref": "output/env/pegasus/calibration/registered/calibration.json",
        "calibration_sha256": "b" * 64,
        "hostname": "bnode-test",
        "pbs_jobid": "123.test",
        "ccbench_commit": "511c9538e4e8efa54b45cda62e72389ed3b706ec",
        "gflags_pin": "c" * 40,
        "glog_pin": "d" * 40,
        "dependency_prefix": "/scr/test/dependency-prefix",
        "build_cache_root": "/scr/test/ccbench-cache",
        "dependency_build_log": "/repo/output/insights/test/job-logs/123.test",
    }
    values.update(overrides)
    return subject._ProfileRuntime(**values)


def _raw_runs() -> list[dict[str, float | int]]:
    return [
        {
            "tps": 100.0,
            "abort": 0.10,
            "cycles": 1000,
            "instructions": 500,
            "spin_cyc_pct": 20.0,
            "spin_instr_pct": 10.0,
        },
        {
            "tps": 120.0,
            "abort": 0.20,
            "cycles": 1200,
            "instructions": 720,
            "spin_cyc_pct": 25.0,
            "spin_instr_pct": 20.0,
        },
        {
            "tps": 110.0,
            "abort": 0.15,
            "cycles": 1100,
            "instructions": 605,
            "spin_cyc_pct": 10.0,
            "spin_instr_pct": 5.0,
        },
    ]


def _install_profile_point_spies(monkeypatch, runs=None) -> dict:
    observed: dict[str, object] = {}
    pending = iter(runs or _raw_runs())
    context = object()
    evidence = object()
    receipt = object()
    admission = object()

    monkeypatch.setattr(subject, "assert_holdout_observation_admitted", lambda **kwargs: None)

    def fake_context(*, generator_id):
        observed["generator_id"] = generator_id
        return context

    def fake_evidence(genome, commit, *, cxx):
        observed["evidence_commit"] = commit
        observed["evidence_cxx"] = cxx
        return evidence

    def fake_attest(got_context, got_evidence, *, generator_input_sha256):
        observed["attest"] = (got_context, got_evidence, generator_input_sha256)
        return receipt

    def fake_admission(got_context, got_evidence, *, generator_receipt):
        observed["admission"] = (got_context, got_evidence, generator_receipt)
        return admission

    def fake_build(genome, ccbench_commit, trace, **kwargs):
        observed["build_commit"] = ccbench_commit
        observed["trace"] = trace
        observed["build_kwargs"] = kwargs
        build_number = observed.get("build_number", 0) + 1
        observed["build_number"] = build_number
        return SimpleNamespace(
            binary=f"/tmp/fake-ccbench-{build_number}",
            bin_sha256=f"{build_number:064x}",
        )

    def fake_run(binary, workload, tmp, runtime, backoff_us):
        observed.setdefault("run_runtimes", []).append(runtime)
        observed.setdefault("run_points", []).append(backoff_us)
        return next(pending)

    monkeypatch.setattr(subject, "build_run_context", fake_context)
    monkeypatch.setattr(subject.source_digest, "resolve_evidence", fake_evidence)
    monkeypatch.setattr(subject, "attest_generator_output", fake_attest)
    monkeypatch.setattr(subject, "derive_build_admission", fake_admission)
    monkeypatch.setattr(subject.buildcache, "build", fake_build)
    monkeypatch.setattr(
        subject.patchharness,
        "applied",
        lambda *args: contextlib.nullcontext(),
    )
    monkeypatch.setattr(subject, "_assert_backoff_symbol_present", lambda *args: None)
    monkeypatch.setattr(subject, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(subject, "_profile_run", fake_run)
    return observed


def _complete_report(include_symbols=True, entry="Backoff::backoff") -> str:
    line = f"   20.00%  ccbench  [.] {entry}\n" if include_symbols else ""
    return (
        "# Samples: 10 of event 'cycles'\n"
        "# Event count (approx.): 1000\n"
        f"{line}"
        "# Samples: 10 of event 'instructions'\n"
        "# Event count (approx.): 500\n"
        f"{line}"
    )


def _install_process_spy(
    monkeypatch, report_text: str, observed: dict | None = None,
) -> list[list[str]]:
    calls: list[list[str]] = []
    if observed is None:
        observed = {}
    observed["kwargs"] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        observed["kwargs"].append(dict(kwargs))
        if "record" in argv:
            data = Path(argv[argv.index("-o") + 1])
            data.write_bytes(b"data")
            return SimpleNamespace(returncode=0, stdout="bench-output", stderr="")
        return SimpleNamespace(returncode=0, stdout=report_text, stderr="")

    monkeypatch.setattr(subject.subprocess, "run", fake_run)
    monkeypatch.setattr(subject, "parse_bench_stdout", lambda text: [object()])
    monkeypatch.setattr(subject, "throughput_tps", lambda metrics: 123.0)
    monkeypatch.setattr(subject, "parse_abort", lambda metrics: 0.25)
    return calls


def _rows() -> list[dict[str, object]]:
    rows = []
    for index, amount in enumerate((0, 2, 5, 10)):
        total = 1.0 - index * 0.1
        useful = 1.0 - index * 0.01
        rows.append({
            "backoff_us": amount,
            "is_none": amount == 0,
            "genome": f"g{index}",
            "tps_median": 1000.0 + index,
            "abort": 0.1,
            "total_ipc": total,
            "useful_ipc": useful,
            "spin_cyc_pct": float(index),
            "spin_instr_pct": float(index) / 2,
            "k_total": 100.0,
            "k_useful": 101.0,
            "tps_all": [1000.0 + index] * 3,
            "reps": [{
                "tps": 1000.0 + index,
                "abort": 0.1,
                "cycles": 1000,
                "instructions": 500,
                "spin_cyc_pct": float(index),
                "spin_instr_pct": float(index) / 2,
                "total_ipc": total,
                "useful_ipc": useful,
                "k_total": 100.0,
                "k_useful": 101.0,
            }],
        })
    return rows


def _write_artifact(monkeypatch, tmp_path, *, tag="balanced", workload=None, rows=None):
    seen_tags: list[str] = []

    def fake_scope(env_tag):
        seen_tags.append(env_tag)
        return str(tmp_path / env_tag)

    monkeypatch.setattr(subject, "env_scope_dir", fake_scope)
    monkeypatch.setattr(
        subject,
        "_comparison_receipt",
        lambda: {"path": "output/reference.json", "sha256": "e" * 64},
    )
    selected_workload = _workload() if workload is None else workload
    selected_rows = _rows() if rows is None else rows
    result = Path(subject._write_out(
        tag, selected_workload, selected_rows, "pegasus", _runtime(), log=lambda _: None,
    ))
    return (
        json.loads(result.read_text(encoding="utf-8")),
        result.with_suffix(".md").read_text(encoding="utf-8"),
        seen_tags,
        result,
    )


def test_m01_write_out_requires_and_uses_resolved_env_tag(monkeypatch, tmp_path):
    payload, _, seen_tags, result = _write_artifact(monkeypatch, tmp_path)

    env_parameter = inspect.signature(subject._write_out).parameters["env_tag"]
    assert env_parameter.default is inspect.Parameter.empty
    assert seen_tags == ["pegasus"]
    assert result.parent == tmp_path / "pegasus" / "profile"
    assert payload["env_tag"] == "pegasus"


def test_m02_profile_run_uses_runtime_clock(monkeypatch, tmp_path):
    calls = _install_process_spy(monkeypatch, _complete_report())

    subject._profile_run("/tmp/bin", _workload(), str(tmp_path), _runtime(), 2)

    assert "-clocks_per_us=2100" in calls[0]
    assert "-clocks_per_us=1800" not in calls[0]


def test_m03_record_and_report_use_same_resolved_executable(monkeypatch, tmp_path):
    calls = _install_process_spy(monkeypatch, _complete_report())
    runtime = _runtime()

    subject._profile_run("/tmp/bin", _workload(), str(tmp_path), runtime, 2)

    assert calls[0][len(runtime.numactl)] == runtime.profiler_executable
    assert calls[1][0] == runtime.profiler_executable


def test_fx6_record_and_report_both_have_finite_timeouts(monkeypatch, tmp_path):
    observed = {}
    _install_process_spy(monkeypatch, _complete_report(), observed)

    subject._profile_run("/tmp/bin", _workload(), str(tmp_path), _runtime(), 2)

    assert [entry["timeout"] for entry in observed["kwargs"]] == [180, 180]


def test_m04_resolver_preserves_policy_order(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    first.chmod(0o755)
    second.chmod(0o755)

    resolved = subject._resolve_profiler_executable({
        "perf_candidates": [str(first), str(second)],
    })

    assert resolved == str(first.resolve())


def test_m05_resolver_fails_closed_without_executable_candidate(monkeypatch, tmp_path):
    missing = tmp_path / "missing"
    non_executable = tmp_path / "non-executable"
    non_executable.write_text("x", encoding="utf-8")
    non_executable.chmod(0o644)
    fallback = Path("/usr/bin/perf")
    original_is_file = Path.is_file
    original_access = os.access

    def fake_is_file(path):
        return path == fallback or original_is_file(path)

    def fake_access(path, mode):
        return Path(path) == fallback or original_access(path, mode)

    monkeypatch.setattr(Path, "is_file", fake_is_file)
    monkeypatch.setattr(subject.os, "access", fake_access)

    with pytest.raises(RuntimeError, match="実行可能"):
        subject._resolve_profiler_executable({
            "perf_candidates": [str(missing), str(non_executable)],
        })


def test_m06_backoff_point_requires_symbol_entries(monkeypatch, tmp_path):
    _install_process_spy(monkeypatch, _complete_report(include_symbols=False))

    with pytest.raises(RuntimeError, match="Backoff::backoff entry"):
        subject._profile_run("/tmp/bin", _workload(), str(tmp_path), _runtime(), 2)

    accepted = subject._profile_run(
        "/tmp/bin", _workload(), str(tmp_path), _runtime(), None,
    )
    assert accepted["spin_cyc_pct"] == 0.0
    assert accepted["spin_instr_pct"] == 0.0


def test_fx1_different_symbol_cannot_satisfy_completeness(monkeypatch, tmp_path):
    _install_process_spy(
        monkeypatch, _complete_report(entry="NotBackoff::backoff_helper"),
    )

    with pytest.raises(RuntimeError, match="Backoff::backoff entry"):
        subject._profile_run("/tmp/bin", _workload(), str(tmp_path), _runtime(), 2)


def test_report_totals_are_required_for_both_events(monkeypatch, tmp_path):
    report = (
        "# Samples: 10 of event 'cycles'\n"
        "# Event count (approx.): 1000\n"
        "   20.00%  ccbench  [.] Backoff::backoff\n"
    )
    _install_process_spy(monkeypatch, report)

    with pytest.raises(RuntimeError, match="total が欠落"):
        subject._profile_run("/tmp/bin", _workload(), str(tmp_path), _runtime(), None)


def test_m07_profile_point_saves_each_rep_raw_and_derived_values(monkeypatch):
    _install_profile_point_spies(monkeypatch)

    row = subject.profile_point(2, _workload(), log=lambda _: None, runtime=_runtime())

    assert len(row["reps"]) == 3
    assert set(row["reps"][0]) == {
        "tps", "abort", "cycles", "instructions", "spin_cyc_pct",
        "spin_instr_pct", "total_ipc", "useful_ipc", "k_total", "k_useful",
    }
    for saved, raw in zip(row["reps"], _raw_runs(), strict=True):
        for key in (
            "tps", "abort", "cycles", "instructions", "spin_cyc_pct",
            "spin_instr_pct",
        ):
            assert saved[key] == raw[key]
        expected_total = raw["instructions"] / raw["cycles"]
        expected_useful = (
            raw["instructions"] * (1 - raw["spin_instr_pct"] / 100)
            / (raw["cycles"] * (1 - raw["spin_cyc_pct"] / 100))
        )
        assert saved["total_ipc"] == pytest.approx(expected_total)
        assert saved["useful_ipc"] == pytest.approx(expected_useful)
        assert saved["k_total"] == pytest.approx(
            raw["tps"] / ((1 - raw["abort"]) * expected_total)
        )
        assert saved["k_useful"] == pytest.approx(
            raw["tps"] / ((1 - raw["abort"]) * expected_useful)
        )


def test_fx2_dependency_pins_require_present_matching_actual_checkout(tmp_path):
    directory = tmp_path / "logs"
    directory.mkdir()
    first = "c" * 40
    second = "d" * 40
    document = {
        "gflags_expected_head": first,
        "glog_expected_head": second,
    }
    path = directory / "dependency-provenance.json"
    base = {
        "gflags_pin": first,
        "glog_pin": second,
        "dependency_prefix": "/scr/test/prefix",
        "ccbench_cache_root": "/scr/test/cache",
    }
    path.write_text(json.dumps(base), encoding="utf-8")

    assert subject._read_dependency_pins(
        str(directory), document, "/scr/test/prefix", "/scr/test/cache",
    ) == (first, second)

    path.write_text(json.dumps({**base, "gflags_pin": "e" * 40}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="policy pin と不一致"):
        subject._read_dependency_pins(
            str(directory), document, "/scr/test/prefix", "/scr/test/cache",
        )

    path.unlink()
    with pytest.raises(RuntimeError, match="provenance を読めない"):
        subject._read_dependency_pins(
            str(directory), document, "/scr/test/prefix", "/scr/test/cache",
        )


def test_fx2_missing_provenance_stops_before_measurement_or_artifact(monkeypatch):
    contract = object()
    touched = {"profiles": 0, "writes": 0}
    monkeypatch.setattr(subject, "resolve_site_runtime", lambda: ("site", contract, object()))
    monkeypatch.setattr(subject, "_assert_matches_calibration", lambda got: object())
    monkeypatch.setattr(subject, "_load_policy_document", lambda: {})
    monkeypatch.setattr(
        subject, "_build_profile_runtime",
        lambda *args: (_ for _ in ()).throw(RuntimeError("provenance を読めない")),
    )
    monkeypatch.setattr(
        subject, "profile_workload",
        lambda *args, **kwargs: touched.__setitem__("profiles", touched["profiles"] + 1),
    )
    monkeypatch.setattr(
        subject, "_write_out",
        lambda *args, **kwargs: touched.__setitem__("writes", touched["writes"] + 1),
    )

    with pytest.raises(RuntimeError, match="provenance を読めない"):
        subject.main(["backoff_profile.py", "balanced"])
    assert touched == {"profiles": 0, "writes": 0}


def test_fx2_runtime_records_pins_returned_from_actual_provenance(monkeypatch):
    first = "1" * 40
    second = "2" * 40
    contract = SimpleNamespace(
        attestation_mode="required",
        env_tag="pegasus",
        clocks_per_us=2100,
        numactl=("numactl", "--interleave=all"),
        contract_sha256="a" * 64,
        calibration_ref=SimpleNamespace(path="output/calibration.json"),
    )
    loaded = SimpleNamespace(verified=SimpleNamespace(sha256="b" * 64))
    monkeypatch.setenv("CMAKE_PREFIX_PATH", "/scr/test/prefix")
    monkeypatch.setenv(subject._CACHE_ROOT_ENV, "/scr/test/cache")
    monkeypatch.setenv(subject._DEPENDENCY_LOG_ENV, "/repo/.logs.staging")
    monkeypatch.setenv(subject._DEPENDENCY_PUBLISH_LOG_ENV, "/repo/logs/final")
    monkeypatch.setattr(
        subject, "_read_dependency_pins", lambda *args: (first, second),
    )
    monkeypatch.setattr(
        subject.buildcache, "compilers_for_current_site", lambda: ("gcc", "g++"),
    )
    monkeypatch.setattr(subject, "_resolve_profiler_executable", lambda document: "/perf")
    monkeypatch.setattr(subject, "_resolve_full_ccbench_commit", lambda: "3" * 40)
    monkeypatch.setattr(subject.socket, "gethostname", lambda: "bnode-test")

    runtime = subject._build_profile_runtime("site", contract, loaded, {})

    assert runtime.gflags_pin == first
    assert runtime.glog_pin == second
    assert runtime.dependency_build_log == "/repo/logs/final"


def test_m08_writer_marks_d20_profile_ineligible(monkeypatch, tmp_path):
    payload, markdown, _, _ = _write_artifact(monkeypatch, tmp_path)

    assert payload["diagnostic_only"] is True
    assert payload["headline_eligible"] is False
    assert payload["diagnostic_notice"] == subject.D20_DIAGNOSTIC_NOTICE
    assert markdown.count(subject.D20_DIAGNOSTIC_NOTICE) == 2


def test_m09_main_does_not_write_any_artifact_after_measurement_failure(monkeypatch):
    runtime = _runtime()
    writes: list[object] = []
    contract = object()
    loaded = object()
    monkeypatch.setattr(subject, "resolve_site_runtime", lambda: ("site", contract, object()))
    monkeypatch.setattr(subject, "_assert_matches_calibration", lambda got: loaded)
    monkeypatch.setattr(subject, "_load_policy_document", lambda: {})
    monkeypatch.setattr(subject, "_build_profile_runtime", lambda *args: runtime)
    monkeypatch.setattr(subject, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        subject,
        "profile_workload",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("record failed")),
    )
    monkeypatch.setattr(subject, "_write_out", lambda *args, **kwargs: writes.append(args))

    with pytest.raises(RuntimeError, match="record failed"):
        subject.main(["backoff_profile.py", "balanced"])
    assert writes == []


def test_m10_profile_point_drives_current_pin_through_evidence_and_build(monkeypatch):
    observed = _install_profile_point_spies(monkeypatch)

    subject.profile_point(2, _workload(), log=lambda _: None, runtime=_runtime())

    assert observed["evidence_commit"] == pin.CURRENT_PIN
    assert observed["build_commit"] == pin.CURRENT_PIN


def test_m11_profile_point_drives_trace_disabled_build(monkeypatch):
    observed = _install_profile_point_spies(monkeypatch)

    subject.profile_point(2, _workload(), log=lambda _: None, runtime=_runtime())

    assert observed["trace"] is False
    assert observed["generator_id"] is subject.GeneratorId.BACKOFF_PROFILE
    assert observed["build_kwargs"]["cache_root"] == _runtime().build_cache_root


def test_m12_profile_workload_drives_the_frozen_seven_point_grid(monkeypatch):
    calls: list[tuple[object, object]] = []
    runtime = _runtime()
    build_count = 0

    def fake_point(amount, workload, log=print, *, runtime=None):
        calls.append((amount, runtime))
        return {"backoff_us": 0 if amount is None else amount}

    def fake_build(amount, got_runtime):
        nonlocal build_count
        build_count += 1
        return subject._BuiltProfilePoint(
            amount,
            subject._genome(amount),
            SimpleNamespace(
                binary=f"/tmp/fake-ccbench-{build_count}",
                bin_sha256=f"{build_count:064x}",
            ),
        )

    monkeypatch.setattr(subject, "profile_point", fake_point)
    monkeypatch.setattr(subject, "assert_holdout_observation_admitted", lambda **kwargs: None)
    monkeypatch.setattr(subject, "_build_profile_point_in_patch", fake_build)
    monkeypatch.setattr(subject, "_assert_backoff_symbol_present", lambda binary: None)
    monkeypatch.setattr(
        subject.patchharness,
        "applied",
        lambda *args: contextlib.nullcontext(),
    )

    subject.profile_workload("balanced", _workload(), log=lambda _: None, runtime=runtime)

    assert [amount for amount, _ in calls] == [None, 2, 5, 10, 25, 50, 100]
    assert all(seen is runtime for _, seen in calls)


def test_fx11_workload_resolves_builds_and_measures_inside_one_patch_scope(
    monkeypatch,
):
    events = []
    runtime = _runtime()

    @contextlib.contextmanager
    def fake_applied(patch_path, pin_commit, ccbench_dir):
        events.append(("enter", patch_path, pin_commit, ccbench_dir))
        try:
            yield
        finally:
            events.append(("exit",))

    monkeypatch.setattr(subject.patchharness, "applied", fake_applied)
    monkeypatch.setattr(
        subject, "assert_holdout_observation_admitted", lambda **kwargs: None,
    )
    monkeypatch.setattr(
        subject, "build_run_context", lambda **kwargs: object(),
    )

    def fake_evidence(*args, **kwargs):
        events.append(("resolve", args[0].canonical()))
        return object()

    def fake_build(*args, **kwargs):
        build_number = sum(event[0] == "build" for event in events) + 1
        events.append(("build", args[0].canonical()))
        return SimpleNamespace(
            binary=f"/tmp/fake-ccbench-{build_number}",
            bin_sha256=f"{build_number:064x}",
        )

    real_hash_check = subject._assert_distinct_backoff_binary_hashes

    def fake_hash_check(built_points):
        events.append(("hash-check", tuple(
            point.backoff_us for point in built_points
        )))
        real_hash_check(built_points)

    checked_binaries = []

    def fake_symbol_check(built_point):
        binary = built_point.result.binary
        events.append(("symbol-check", binary))
        checked_binaries.append(binary)

    def fake_run(binary, workload, tmp, got_runtime, backoff_us):
        events.append(("measure", backoff_us))
        return _raw_runs()[0]

    monkeypatch.setattr(subject.source_digest, "resolve_evidence", fake_evidence)
    monkeypatch.setattr(
        subject, "attest_generator_output", lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        subject, "derive_build_admission", lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(subject.buildcache, "build", fake_build)
    monkeypatch.setattr(
        subject, "_assert_distinct_backoff_binary_hashes", fake_hash_check,
    )
    monkeypatch.setattr(
        subject, "_assert_profile_point_backoff_symbol", fake_symbol_check,
    )
    monkeypatch.setattr(subject, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(subject, "_profile_run", fake_run)

    subject.profile_workload(
        "balanced", _workload(), log=lambda _: None, runtime=runtime,
    )

    assert [event[0] for event in events].count("enter") == 1
    assert [event[0] for event in events].count("exit") == 1
    assert events[0] == (
        "enter",
        str(REPO_ROOT / "patches/silo-backoff-fixed.patch"),
        pin.CURRENT_PIN,
        str(REPO_ROOT / "external/ccbench"),
    )
    assert events[-1] == ("exit",)
    build_phases = [
        phase
        for _amount in (None, 2, 5, 10, 25, 50, 100)
        for phase in ("resolve", "build")
    ]
    gate_phases = ["hash-check", *("symbol-check" for _ in range(7))]
    measure_phases = ["measure" for _ in range(7 * 3)]
    assert [event[0] for event in events[1:-1]] == [
        *build_phases, *gate_phases, *measure_phases,
    ]
    assert events[15] == (
        "hash-check", (None, 2, 5, 10, 25, 50, 100),
    )
    assert checked_binaries == [f"/tmp/fake-ccbench-{index}" for index in range(1, 8)]


def _built_points(digests) -> list[subject._BuiltProfilePoint]:
    return [
        subject._BuiltProfilePoint(
            amount,
            subject._genome(amount),
            SimpleNamespace(binary=f"/binary/{index}", bin_sha256=digest),
        )
        for index, (amount, digest) in enumerate(
            zip([None, *subject.BACKOFF_US], digests, strict=True)
        )
    ]


def _write_synthetic_elf(
    path: Path,
    symbols: list[str],
    *,
    dynamic_only: bool = False,
    binding: int = 1,
    broken_section_names: bool = False,
) -> None:
    strings_name = ".dynstr" if dynamic_only else ".strtab"
    symbols_name = ".dynsym" if dynamic_only else ".symtab"
    symbol_section_type = 11 if dynamic_only else 2
    section_names = (
        f"\0.shstrtab\0{strings_name}\0{symbols_name}\0".encode("ascii")
    )
    string_table = bytearray(b"\0")
    symbol_entries = [bytes(24)]
    for symbol in symbols:
        name_offset = len(string_table)
        string_table.extend(symbol.encode("ascii") + b"\0")
        symbol_entries.append(struct.pack(
            "<IBBHQQ", name_offset, (binding << 4) | 2, 0, 1, 0, 1,
        ))
    symbols_data = b"".join(symbol_entries)

    section_names_offset = 64
    string_table_offset = section_names_offset + len(section_names)
    symbols_offset = string_table_offset + len(string_table)
    section_headers_offset = (symbols_offset + len(symbols_data) + 7) & ~7
    header = struct.pack(
        "<16sHHIQQQIHHHHHH",
        b"\x7fELF" + bytes((2, 1, 1)) + bytes(9),
        2,
        62,
        1,
        0,
        0,
        section_headers_offset,
        0,
        64,
        0,
        0,
        64,
        4,
        9 if broken_section_names else 1,
    )

    def section_header(
        name, section_type, offset, size, *, link=0, info=0, align=1, entry_size=0,
    ):
        return struct.pack(
            "<IIQQQQIIQQ",
            name, section_type, 0, 0, offset, size, link, info, align, entry_size,
        )

    section_headers = b"".join((
        bytes(64),
        section_header(
            section_names.index(b".shstrtab"), 3,
            section_names_offset, len(section_names),
        ),
        section_header(
            section_names.index(strings_name.encode("ascii")), 3,
            string_table_offset, len(string_table),
        ),
        section_header(
            section_names.index(symbols_name.encode("ascii")), symbol_section_type,
            symbols_offset, len(symbols_data), link=2, info=1,
            align=8, entry_size=24,
        ),
    ))
    padding = bytes(section_headers_offset - symbols_offset - len(symbols_data))
    path.write_bytes(
        header + section_names + bytes(string_table) + symbols_data
        + padding + section_headers
    )


def test_fx12a_seven_distinct_buildresult_binary_hashes_pass():
    subject._assert_distinct_backoff_binary_hashes(
        _built_points(f"{index:064x}" for index in range(1, 8)),
    )


def test_fx12a_duplicate_binary_hash_names_colliding_points():
    digests = [f"{index:064x}" for index in range(1, 8)]
    digests[4] = digests[1]

    with pytest.raises(RuntimeError, match=r"2us.*25us"):
        subject._assert_distinct_backoff_binary_hashes(_built_points(digests))


def test_fx12b_synthetic_elf_with_backoff_symbol_passes(tmp_path):
    binary = tmp_path / "with-symbol"
    _write_synthetic_elf(binary, [
        "_ZN10NotBackoff7backoffEv",
        "_ZN3foo7Backoff7backoffEv.isra.0",
    ])

    subject._assert_backoff_symbol_present(str(binary))


def test_fx12b_synthetic_elf_without_backoff_symbol_fails(tmp_path):
    binary = tmp_path / "without-symbol"
    _write_synthetic_elf(binary, ["_ZN3foo3barEv"])

    with pytest.raises(RuntimeError, match="Backoff::backoff symbol がない") as exc_info:
        subject._assert_backoff_symbol_present(str(binary))

    message = str(exc_info.value)
    assert f"binary size={binary.stat().st_size} bytes" in message
    assert "ELF class=64" in message
    assert "endian=little" in message
    assert "解析できた symbol の総数=1" in message
    assert "参照した section=.symtab -> .strtab" in message
    assert ".symtab found=yes; .strtab found=yes" in message
    assert "ackoff 候補=0 件" in message


def test_symbol_gate_allows_none_point_without_backoff_symbol(tmp_path):
    binary = tmp_path / "none-without-symbol"
    _write_synthetic_elf(binary, ["_ZN3foo3barEv"])
    point = subject._BuiltProfilePoint(
        None,
        subject._genome(None),
        SimpleNamespace(binary=str(binary), bin_sha256="1" * 64),
    )

    subject._assert_profile_point_backoff_symbol(point)


def test_symbol_gate_requires_backoff_symbol_at_enabled_point(tmp_path):
    binary = tmp_path / "enabled-without-symbol"
    _write_synthetic_elf(binary, ["_ZN3foo3barEv"])
    point = subject._BuiltProfilePoint(
        2,
        subject._genome(2),
        SimpleNamespace(binary=str(binary), bin_sha256="2" * 64),
    )

    with pytest.raises(RuntimeError, match="Backoff::backoff symbol がない"):
        subject._assert_profile_point_backoff_symbol(point)


def test_fx12b_similar_symbols_do_not_satisfy_binary_gate(tmp_path):
    binary = tmp_path / "similar-symbols"
    similar = [
        "_ZN10NotBackoff7backoffEv",
        "_ZN7Backoff14backoff_helperEv",
    ]
    _write_synthetic_elf(binary, similar)
    point = subject._BuiltProfilePoint(
        2,
        subject._genome(2),
        SimpleNamespace(binary=str(binary), bin_sha256="3" * 64),
    )

    assert all(not subject._is_backoff_function_symbol(name) for name in similar)
    with pytest.raises(RuntimeError, match="Backoff::backoff symbol がない") as exc_info:
        subject._assert_profile_point_backoff_symbol(point)

    message = str(exc_info.value)
    assert similar[0] in message
    assert similar[1] in message
    assert "ackoff 候補=2 件" in message


def test_fx12b_local_binding_backoff_symbol_passes(tmp_path):
    binary = tmp_path / "local-symbol"
    _write_synthetic_elf(binary, ["_ZN7Backoff7backoffEm"], binding=0)

    subject._assert_backoff_symbol_present(str(binary))


def test_fx12b_dynsym_only_backoff_symbol_passes(tmp_path):
    binary = tmp_path / "dynamic-symbol"
    _write_synthetic_elf(
        binary, ["_ZN7Backoff7backoffEm"], dynamic_only=True,
    )

    subject._assert_backoff_symbol_present(str(binary))


def test_fx12b_dynsym_only_failure_lists_missing_sections(tmp_path):
    binary = tmp_path / "dynamic-without-symbol"
    _write_synthetic_elf(binary, ["_ZN3foo3barEv"], dynamic_only=True)

    with pytest.raises(RuntimeError, match="Backoff::backoff symbol がない") as exc_info:
        subject._assert_backoff_symbol_present(str(binary))

    message = str(exc_info.value)
    assert "参照した section=.dynsym -> .dynstr" in message
    assert ".symtab found=no; .strtab found=no" in message
    assert "section 一覧 (最大 40)=" in message
    assert ".shstrtab" in message
    assert ".dynstr" in message
    assert ".dynsym" in message


def test_fx12b_broken_section_name_table_does_not_hide_symbol(tmp_path):
    binary = tmp_path / "broken-section-names"
    _write_synthetic_elf(
        binary, ["_ZN7Backoff7backoffEm"], broken_section_names=True,
    )

    subject._assert_backoff_symbol_present(str(binary))


def test_fx12b_ackoff_diagnostics_are_capped_at_twenty_names(tmp_path):
    binary = tmp_path / "many-similar-symbols"
    symbols = [f"plain_ackoff_{index:02d}" for index in range(25)]
    _write_synthetic_elf(binary, symbols)

    with pytest.raises(RuntimeError, match="Backoff::backoff symbol がない") as exc_info:
        subject._assert_backoff_symbol_present(str(binary))

    message = str(exc_info.value)
    assert "ackoff 候補=25 件 (先頭 20 件)" in message
    assert symbols[19] in message
    assert symbols[20] not in message


def test_fx12c_cmake_staging_cache_probe_is_gone():
    production = Path(subject.__file__).read_text(encoding="utf-8")

    assert "CMakeCache.txt" not in production


def test_fx12_does_not_add_process_launch_sites():
    tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
    counts = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        count = sum(
            isinstance(candidate, ast.Call)
            and isinstance(candidate.func, ast.Attribute)
            and isinstance(candidate.func.value, ast.Name)
            and candidate.func.value.id == "subprocess"
            and candidate.func.attr == "run"
            for candidate in ast.walk(node)
        )
        if count:
            counts[node.name] = count

    assert counts == {"_profile_run": 2}


def test_m13_resolver_policy_path_is_independent_of_cwd(monkeypatch, tmp_path):
    policy = json.loads(
        (REPO_ROOT / "tools/pegasus/policy.json").read_text(encoding="utf-8")
    )
    expected = Path(policy["perf_candidates"][0])
    original_is_file = Path.is_file
    original_access = os.access

    def fake_is_file(path):
        return path == expected or original_is_file(path)

    def fake_access(path, mode):
        return Path(path) == expected or original_access(path, mode)

    monkeypatch.setattr(Path, "is_file", fake_is_file)
    monkeypatch.setattr(subject.os, "access", fake_access)
    monkeypatch.chdir(tmp_path)

    assert subject._resolve_profiler_executable() == str(expected.resolve())


def test_main_resolves_contract_once_and_shares_one_runtime_object(monkeypatch):
    runtime = _runtime()
    contract = object()
    loaded = object()
    calls = {"resolve": 0, "calibration": 0, "profiles": [], "writes": []}

    def fake_resolve():
        calls["resolve"] += 1
        return "site", contract, object()

    def fake_calibration(got):
        calls["calibration"] += 1
        assert got is contract
        return loaded

    def fake_profile(tag, workload, log=print, *, runtime=None):
        calls["profiles"].append((tag, runtime))
        return _rows()

    def fake_write(tag, workload, rows, env_tag, runtime, log=print):
        calls["writes"].append((tag, env_tag, runtime))

    monkeypatch.setattr(subject, "resolve_site_runtime", fake_resolve)
    monkeypatch.setattr(subject, "_assert_matches_calibration", fake_calibration)
    monkeypatch.setattr(subject, "_load_policy_document", lambda: {"document": True})
    monkeypatch.setattr(
        subject,
        "_build_profile_runtime",
        lambda site, got_contract, got_loaded, document: runtime,
    )
    monkeypatch.setattr(subject, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(subject, "profile_workload", fake_profile)
    monkeypatch.setattr(subject, "_write_out", fake_write)

    assert subject.main(["backoff_profile.py", "balanced"]) == 0
    assert calls["resolve"] == 1
    assert calls["calibration"] == 1
    assert calls["profiles"] == [("balanced", runtime)]
    assert calls["writes"] == [("balanced", "pegasus", runtime)]


def test_writer_records_provenance_comparison_and_scope_limits(monkeypatch, tmp_path):
    payload, markdown, _, _ = _write_artifact(monkeypatch, tmp_path)

    assert payload["site"] == "pegasus-compute"
    assert payload["contract_sha256"] == "a" * 64
    assert payload["calibration_ref"].startswith("output/env/pegasus/")
    assert payload["calibration_sha256"] == "b" * 64
    assert payload["hostname"] == "bnode-test"
    assert payload["pbs_jobid"] == "123.test"
    assert len(payload["ccbench_commit"]) == 40
    assert payload["gflags_pin"] == "c" * 40
    assert payload["glog_pin"] == "d" * 40
    assert payload["dependency_prefix"] == "/scr/test/dependency-prefix"
    assert payload["perf_executable"] == "/opt/checked/bin/perf"
    assert payload["clocks_per_us"] == 2100
    assert payload["comparison"] == {
        "path": "output/reference.json", "sha256": "e" * 64,
    }
    assert payload["comparison_confounds"] == ["environment", "ccbench_commit"]
    assert payload["backoff_time_live_verified"] is False
    assert payload["dependency_prefix_cache_identity_bound"] is False
    assert payload["preregistered_decision"]["replication_bar"] == 0.044
    assert subject.BACKOFF_TIME_NOTICE in markdown
    assert subject.DEPENDENCY_IDENTITY_NOTICE in markdown


def test_fx3_missing_frozen_band_point_is_reasoned_inconclusive(monkeypatch, tmp_path):
    incomplete = [row for row in _rows() if row["backoff_us"] != 5]

    payload, markdown, _, _ = _write_artifact(
        monkeypatch, tmp_path, rows=incomplete,
    )

    decision = payload["decision"]
    assert decision["status"] == "inconclusive"
    assert decision["spin_dilution_condition_met"] is None
    assert "凍結4点" in decision["inconclusive_reason"]
    assert "判定を出さない" in markdown
    assert "凍結4点" in markdown


def test_fx4_publish_failure_cannot_leave_one_final_artifact(monkeypatch, tmp_path):
    target_dir = tmp_path / "pegasus" / "profile"
    original_replace = subject.os.replace
    calls = []

    monkeypatch.setattr(subject, "env_scope_dir", lambda env_tag: str(tmp_path / env_tag))
    monkeypatch.setattr(
        subject,
        "_comparison_receipt",
        lambda: {"path": "output/reference.json", "sha256": "e" * 64},
    )

    def fail_second(source, destination):
        source = Path(source)
        destination = Path(destination)
        calls.append((source, destination))
        if len(calls) == 1:
            assert (source.parent / destination.with_suffix(".json").name).is_file()
            assert (source.parent / destination.with_suffix(".md").name).is_file()
            return original_replace(source, destination)
        raise OSError("injected second publish failure")

    monkeypatch.setattr(subject.os, "replace", fail_second)

    with pytest.raises(OSError, match="second publish failure"):
        subject._write_out(
            "balanced", _workload(), _rows(), "pegasus", _runtime(),
            log=lambda _: None,
        )

    assert not (target_dir / "backoff_profile_t48_skew0p9_rr50.json").exists()
    assert not (target_dir / "backoff_profile_t48_skew0p9_rr50.md").exists()
    assert not list(target_dir.glob(".backoff_profile_t48_skew0p9_rr50.*"))


def test_fx9_workload_claims_are_derived_from_tag(monkeypatch, tmp_path):
    workload = {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}

    payload, markdown, _, _ = _write_artifact(
        monkeypatch, tmp_path, tag="write-heavy", workload=workload,
    )

    assert "balanced" not in markdown
    assert "+11.3%" not in markdown
    assert "write-heavy の headline 利得" in markdown
    assert "+11.3%" not in " ".join(payload["remaining_limitations"])


def test_production_has_no_name_based_perf_predicate_and_negative_control_does():
    rel_path = "orchestrator/campaign/backoff_profile.py"
    source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    negative = "def choose():\n    if use_perf:\n        return True\n    return False\n"

    assert official_closure._python_has_perf_predicate(rel_path, source) is False
    assert official_closure._python_has_perf_predicate("negative.py", negative) is True


def test_reproduction_body_freezes_dependencies_cache_and_walltime():
    path = (
        REPO_ROOT
        / "output/insights/2026-08-26_b10-balanced-profile/job-body.sh"
    )
    source = path.read_text(encoding="utf-8")
    active = [
        line.strip() for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    submit_example = (
        "# python3 tools/pegasus/dispatch_compute.py --task generic "
        "--walltime 05:00:00 \\\n"
        "#   /bin/bash output/insights/2026-08-26_b10-balanced-profile/"
        "job-body.sh <JOB_TOKEN>"
    )
    assert submit_example in source
    assert "PBS_JOBID" not in source
    assert (
        "JOB_TOKEN=${1:?JOB_TOKEN argument is required for the job-specific build roots}"
        in active
    )
    assert "JOB_TOKEN=${JOB_TOKEN//[^A-Za-z0-9._-]/_}" in active
    assert "DISPATCH_WALLTIME=05:00:00" in active
    assert "WALLTIME_SECONDS=18000" in active
    assert "FETCH_PROXY=http://10.120.96.1:8080" in active
    assert source.count("http://10.120.96.1:8080") == 1
    assert "DEPENDENCY_BUILD_BUDGET_SECONDS=540" in active
    assert "CCBENCH_BUILD_BUDGET_SECONDS=$((7 * 900))" in active
    assert "RECORD_BUDGET_SECONDS=$((7 * 3 * 180))" in active
    assert "REPORT_BUDGET_SECONDS=$((7 * 3 * 180))" in active
    assert "SHUTDOWN_MARGIN_SECONDS=600" in active
    assert "separate 900 seconds" in source
    assert source.count("-DBUILD_SHARED_LIBS=OFF") == 2
    assert "gflags_expected_head" in source
    assert "glog_expected_head" in source
    assert "export CMAKE_PREFIX_PATH=" in source
    assert 'export http_proxy="$FETCH_PROXY"' in active
    assert 'export https_proxy="$FETCH_PROXY"' in active
    assert "export IZANAGI_BACKOFF_PROFILE_CACHE_ROOT=" in source
    assert "export TMPDIR" in active
    assert "dependency-provenance.json" in source
    assert '"build_time_network_fetch": True' in source
    assert '"build_time_network_fetch_integrity": (' in source
    assert "fixes masstree content by a SHA pin" in source
    assert '"fetch_proxy": sys.argv[20]' in source
    assert '"$TOTAL_BUDGET_SECONDS" "$FETCH_PROXY" <<\'PY\'' in active
    assert "backoff_profile.py balanced" in source
    assert 'test "$TOTAL_BUDGET_SECONDS" -lt "$WALLTIME_SECONDS"' in active
    assert 'DEPENDENCY_BUILD_LOG="$DEPENDENCY_LOG_PARENT/.$JOB_TOKEN.staging"' in active
    assert 'DEPENDENCY_PUBLISH_LOG="$DEPENDENCY_LOG_PARENT/$JOB_TOKEN"' in active
    assert 'test ! -e "$JOB_ROOT"' in active
    assert 'test ! -e "$DEPENDENCY_BUILD_LOG"' in active
    assert 'test ! -e "$DEPENDENCY_PUBLISH_LOG"' in active
    assert 'mkdir "$JOB_ROOT"' in active
    assert 'mkdir "$DEPENDENCY_PREFIX" "$CCBENCH_CACHE_ROOT" "$TMPDIR"' in active
    assert 'mkdir "$GFLAGS_BUILD" "$GLOG_BUILD"' in active
    assert not any(
        line.startswith("mkdir -p")
        and any(name in line for name in (
            "JOB_ROOT", "DEPENDENCY_PREFIX", "CCBENCH_CACHE_ROOT",
            "GFLAGS_BUILD", "GLOG_BUILD",
        ))
        for line in active
    )
    assert 'GFLAGS_ACTUAL_HEAD=$(verify_pinned_clean_source gflags "$GFLAGS_SOURCE" "$GFLAGS_PIN")' in active
    assert 'GLOG_ACTUAL_HEAD=$(verify_pinned_clean_source glog "$GLOG_SOURCE" "$GLOG_PIN")' in active
    assert '"$GFLAGS_SOURCE" "$GFLAGS_ACTUAL_HEAD" "$GFLAGS_PIN" \\' in active
    assert '"$GLOG_SOURCE" "$GLOG_ACTUAL_HEAD" "$GLOG_PIN" \\' in active

    first_build = active.index('timeout 60 cmake -S "$GFLAGS_SOURCE" -B "$GFLAGS_BUILD" \\')
    second_build = active.index('timeout 120 cmake -S "$GLOG_SOURCE" -B "$GLOG_BUILD" \\')
    last_dependency_step = active.index('timeout 120 cmake --install "$GLOG_BUILD" \\')
    prefix_export = active.index('export CMAKE_PREFIX_PATH="$DEPENDENCY_PREFIX"')
    http_proxy_export = active.index('export http_proxy="$FETCH_PROXY"')
    https_proxy_export = active.index('export https_proxy="$FETCH_PROXY"')
    source_log_export = active.index(
        'export IZANAGI_BACKOFF_PROFILE_DEPENDENCY_LOG="$DEPENDENCY_BUILD_LOG"'
    )
    final_log_export = active.index(
        'export IZANAGI_BACKOFF_PROFILE_DEPENDENCY_PUBLISH_LOG="$DEPENDENCY_PUBLISH_LOG"'
    )
    profile = active.index('python3.10 orchestrator/campaign/backoff_profile.py balanced \\')
    publish = active.index('mv -T "$DEPENDENCY_BUILD_LOG" "$DEPENDENCY_PUBLISH_LOG"')
    assert (
        first_build < second_build < last_dependency_step < prefix_export
        < http_proxy_export < https_proxy_export < source_log_export
        < final_log_export < profile < publish
    )


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
