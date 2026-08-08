from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROBE_PATH = ROOT / "tools/pegasus/probes/t139_r4_env_probe.py"
CONTRACT_PATH = ROOT / "tools/pegasus/probes/t139_r4_env_probe_contract.json"
SH_PATH = ROOT / "tools/pegasus/probes/t139_r4_env_probe.sh"
PBS_PATH = ROOT / "tools/pegasus/probes/t139_r4_env_probe.pbs"

SPEC = importlib.util.spec_from_file_location("t139_r4_env_probe", PROBE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROBE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROBE
SPEC.loader.exec_module(PROBE)


def _line(values: list[object], label: str = "cpu") -> str:
    return label + " " + " ".join(str(value) for value in values)


def _window(window_id: str, busy: int, total: int, status: str = "valid") -> dict[str, object]:
    assert 0 <= busy <= total
    start = [100] * 8
    deltas = [busy, 0, 0, total - busy, 0, 0, 0, 0]
    end = [value + delta for value, delta in zip(start, deltas)]
    analyzed = PROBE.analyze_window(
        _line(start),
        _line(end),
        10_000_000_000,
        0,
    )
    analyzed.update(window_id=window_id, observed=True, status=status)
    if status != "valid":
        analyzed["failure_reasons"] = ["test_malformed_window"]
    return analyzed


def _decision_windows(busy: int, total: int) -> tuple[list[dict[str, object]], list[str]]:
    ids = ["preflight", *[f"post-{index:02d}" for index in range(1, 13)]]
    return [_window(window_id, busy, total) for window_id in ids], ids


def _decision(
    windows: list[dict[str, object]],
    ids: list[str],
    *,
    runs_ok: bool = True,
    trace0_build_ok: bool = True,
    trace1_build_witness: str = "present",
    compiler_witness: str = "present",
) -> object:
    return PROBE.derive_decision(
        windows,
        ids,
        runs_ok=runs_ok,
        trace0_build_ok=trace0_build_ok,
        trace1_build_witness=trace1_build_witness,
        compiler_witness=compiler_witness,
    )


def _new_state(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    loaded = PROBE.hash_then_parse_contract(CONTRACT_PATH.read_bytes())
    state = PROBE.new_state(
        loaded,
        commit="a" * 40,
        jobid="test.1",
        expected_contract_sha256=loaded.sha256,
    )
    output = tmp_path / "attempt"
    output.mkdir()
    state_path = output / "state.json"
    PROBE._write_json_atomic(state_path, state)
    return state_path, output, state


def _successful_rechecks() -> list[dict[str, object]]:
    return [
        {"label": f"{position}-{kind}", "compiler": compiler, "match": True}
        for kind in ("trace0", "trace1")
        for position in ("before-configure", "before-build", "after-build")
        for compiler in ("gcc", "gxx")
    ]


def _make_state_feasible(state: dict[str, object]) -> None:
    windows = state["windows"]
    assert isinstance(windows, list)
    for window in windows:
        window.update(_window(str(window["window_id"]), 0, 48))
    runs = state["runs"]
    assert isinstance(runs, list)
    for run in runs:
        run.update(status="success", returncode=0, flags_match=True)
    builds = state["builds"]
    assert isinstance(builds, list)
    for build in builds:
        build.update(status="success", returncode=0)
    compilers = state["compilers"]
    assert isinstance(compilers, dict)
    compilers["gcc"] = {"identity": "gcc"}
    compilers["gxx"] = {"identity": "gxx"}
    compilers["identity_rechecks"] = _successful_rechecks()


def _compile_commands(trace: int, analysis: int) -> list[dict[str, object]]:
    common = ["/usr/bin/g++", f"-DTRACE={trace}", f"-DADD_ANALYSIS={analysis}"]
    return [
        {
            "directory": "/build/cc/silo",
            "file": "/source/cc/silo/transaction.cc",
            "arguments": common
            + ["-o", "CMakeFiles/ycsb_silo.exe.dir/transaction.cc.o", "-c", "/source/cc/silo/transaction.cc"],
        },
        {
            "directory": "/build",
            "file": "/source/common/result.cc",
            "arguments": common + ["-o", "result.o", "-c", "/source/common/result.cc"],
        },
        {
            "directory": "/build",
            "file": "/source/common/util.cc",
            "arguments": common + ["-o", "util.o", "-c", "/source/common/util.cc"],
        },
    ]


def _cache(trace: int, analysis: int) -> str:
    return f"CCBENCH_TRACE:STRING={trace}\nCCBENCH_ADD_ANALYSIS:STRING={analysis}\n"


def _assert_all_objects_have_metadata(value: object) -> None:
    if isinstance(value, dict):
        assert value["study_eligible"] is False
        assert value["probe_series_id"] == "t139-r4-env-probe"
        assert value["purpose"] == "non_study_environment_probe"
        for child in value.values():
            _assert_all_objects_have_metadata(child)
    elif isinstance(value, list):
        for child in value:
            _assert_all_objects_have_metadata(child)


def test_parse_aggregate_cpu_line_ignores_cpu0() -> None:
    parsed = PROBE.parse_aggregate_cpu_line(
        _line([1, 2, 3, 4, 5, 6, 7, 8])
        + "\n"
        + _line([100] * 8, "cpu0")
        + "\n"
    )
    assert parsed.first_eight == (1, 2, 3, 4, 5, 6, 7, 8)


def test_parse_aggregate_cpu_line_rejects_cpu0_only() -> None:
    with pytest.raises(ValueError, match="found 0"):
        PROBE.parse_aggregate_cpu_line(_line([1] * 8, "cpu0"))


@pytest.mark.parametrize(
    "text, message",
    [
        (_line([1] * 7), "fewer than 8"),
        (_line([1, 1, 1, "x", 1, 1, 1, 1]), "non-integer"),
    ],
)
def test_parse_aggregate_cpu_line_rejects_short_and_noninteger(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        PROBE.parse_aggregate_cpu_line(text)


def test_extra_guest_columns_are_retained_but_not_counted() -> None:
    result = PROBE.analyze_window(
        _line([100] * 8 + [900, 901]),
        _line([101, 101, 101, 105, 101, 101, 101, 101, 999, 1000]),
        10_000_000_000,
        5_000_000_000,
    )
    assert result["status"] == "valid"
    assert result["start_extra_values"] == [900, 901]
    assert result["end_extra_values"] == [999, 1000]
    assert result["total"] == 12
    assert result["busy"] == 7


def test_negative_delta_is_malformed_and_preserved() -> None:
    result = PROBE.analyze_window(
        _line([100] * 8),
        _line([99, 101, 101, 101, 101, 101, 101, 101]),
        10_000_000_000,
        0,
    )
    assert result["status"] == "malformed"
    assert "counter_decreased" in result["failure_reasons"]
    assert result["deltas"][0] == -1


def test_total_zero_is_malformed() -> None:
    result = PROBE.analyze_window(
        _line([100] * 8), _line([100] * 8), 10_000_000_000, 0
    )
    assert result["status"] == "malformed"
    assert "total_not_positive" in result["failure_reasons"]


def test_total_zero_is_independently_rejected_by_decision_layer() -> None:
    windows, ids = _decision_windows(0, 48)
    windows[0]["total"] = 0
    decision = _decision(windows, ids)
    assert decision.window_verdict == "incomplete"
    assert decision.window_verdict_reasons == ("window_raw_counter_mismatch:preflight",)


def test_decision_rejects_saved_busy_total_that_disagree_with_raw_counters() -> None:
    windows, ids = _decision_windows(0, 48)
    windows[4]["busy"] = 1
    decision = _decision(windows, ids)
    assert decision.window_verdict == "incomplete"
    assert decision.window_verdict_reasons == (
        "window_raw_counter_mismatch:post-04",
    )


def test_iowait_is_counted_as_busy() -> None:
    result = PROBE.analyze_window(
        _line([100] * 8),
        _line([100, 100, 100, 109, 101, 100, 100, 100]),
        10_000_000_000,
        0,
    )
    assert result["total"] == 10
    assert result["busy"] == 1


@pytest.mark.parametrize("duration", [9_900_000_000, 10_100_000_000])
def test_window_duration_inclusive_boundaries(duration: int) -> None:
    assert PROBE.validate_window_duration(duration)


@pytest.mark.parametrize("duration", [9_899_999_999, 10_100_000_001])
def test_window_duration_rejects_one_nanosecond_outside(duration: int) -> None:
    assert not PROBE.validate_window_duration(duration)


def test_run_adjacency_five_second_boundary() -> None:
    assert PROBE.validate_run_adjacency(5_000_000_000)
    assert not PROBE.validate_run_adjacency(5_000_000_001)
    assert not PROBE.validate_run_adjacency(-1)


def test_decision_exactly_one_point_zero() -> None:
    windows, ids = _decision_windows(1, 48)
    assert _decision(windows, ids).window_verdict == "feasible"


def test_decision_one_point_zero_one_violates_fixed_upper() -> None:
    windows, ids = _decision_windows(101, 4800)
    assert _decision(windows, ids).window_verdict == "not_feasible"


def test_decision_above_two_point_zero() -> None:
    windows, ids = _decision_windows(1, 23)
    assert _decision(windows, ids).window_verdict == "not_feasible"


def test_decision_malformed_mix_is_incomplete() -> None:
    windows, ids = _decision_windows(0, 48)
    windows[7]["status"] = "malformed"
    assert _decision(windows, ids).window_verdict == "incomplete"


def test_diagnostics_do_not_change_positive_decision() -> None:
    windows, ids = _decision_windows(0, 48)
    low_diagnostics = {"load1": "0.01", "foreign_count": 0, "cgroup": "quiet"}
    high_diagnostics = {"load1": "999", "foreign_count": 999, "cgroup": "different"}
    receipt_a = {"windows": copy.deepcopy(windows), "diagnostics": low_diagnostics}
    receipt_b = {"windows": copy.deepcopy(windows), "diagnostics": high_diagnostics}
    decision_a = _decision(receipt_a["windows"], ids)
    decision_b = _decision(receipt_b["windows"], ids)
    assert decision_a == decision_b
    assert decision_a.window_verdict == "feasible"


def test_analyze_window_call_site_duration_gate_reaches_decision() -> None:
    windows, ids = _decision_windows(0, 48)
    analyzed = PROBE.analyze_window(
        _line([100] * 8),
        _line([100, 100, 100, 148, 100, 100, 100, 100]),
        10_100_000_001,
        0,
    )
    analyzed["window_id"] = ids[0]
    windows[0] = analyzed
    decision = _decision(windows, ids)
    assert decision.window_verdict == "incomplete"
    assert decision.window_verdict_reasons == (
        "window_duration_out_of_tolerance:preflight",
    )


def test_contract_exact_schema_types_lengths_and_metadata() -> None:
    loaded = PROBE.hash_then_parse_contract(CONTRACT_PATH.read_bytes())
    contract = loaded.value
    assert set(contract) == PROBE.TOP_LEVEL_KEYS
    assert len(contract["windows"]) == 13
    assert len(contract["runs"]) == 13
    assert len(contract["counter_names"]) == 8
    assert contract["fixed_upper"] == "1.0"
    assert contract["phase_budget"]["adjacency_budget_s"] == 12 * 5 + 5 == 65
    assert contract["terminal_attempt_policy"]["resubmissions_after_observation"] == 0
    assert contract["terminal_attempt_policy"]["namespace_observed_attempt_gate_required"] is True
    assert contract["terminal_attempt_policy"]["scheduler_backed_pre_submit_ledger"] is False
    assert contract["phase_budget"]["sample_cap_s"] == 960
    assert contract["phase_budget"]["driver_cap_s"] == 2045
    assert contract["phase_budget"]["serial_noncontingency_s"] == 2948
    assert contract["phase_budget"]["serial_with_termination_grace_s"] == 3068
    _assert_all_objects_have_metadata(contract)


def test_contract_rejects_extra_key_wrong_type_and_array_length() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    extra = copy.deepcopy(contract)
    extra["unexpected"] = 1
    with pytest.raises(PROBE.ContractError, match="keys differ"):
        PROBE.validate_contract(extra)
    wrong_type = copy.deepcopy(contract)
    wrong_type["runs"] = tuple(wrong_type["runs"])
    with pytest.raises(PROBE.ContractError, match="runs must be list"):
        PROBE.validate_contract(wrong_type)
    short = copy.deepcopy(contract)
    short["windows"].pop()
    with pytest.raises(PROBE.ContractError, match="exactly 13"):
        PROBE.validate_contract(short)


def test_contract_rejects_duplicate_json_key() -> None:
    payload = CONTRACT_PATH.read_bytes().replace(
        b'{\n  "schema_version":',
        b'{\n  "schema_version": "duplicate",\n  "schema_version":',
        1,
    )
    with pytest.raises(PROBE.DuplicateKeyError, match="schema_version"):
        PROBE.hash_then_parse_contract(payload)


def test_contract_reader_is_called_once_and_same_buffer_is_retained() -> None:
    payload = CONTRACT_PATH.read_bytes()
    calls: list[object] = []

    def reader() -> bytes:
        calls.append(object())
        return payload

    loaded = PROBE.load_contract_from_reader(reader)
    assert len(calls) == 1
    assert loaded.buffer is payload
    assert loaded.sha256 == __import__("hashlib").sha256(payload).hexdigest()


def test_git_contract_loader_issues_one_cat_file_read(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = CONTRACT_PATH.read_bytes()
    calls: list[list[str]] = []

    class Completed:
        stdout = payload
        stderr = b""

    def fake_run(argv: list[str], **kwargs: object) -> Completed:
        calls.append(argv)
        assert kwargs["stdout"] == subprocess.PIPE
        return Completed()

    monkeypatch.setattr(PROBE.subprocess, "run", fake_run)
    loaded = PROBE.load_contract_from_git(Path("/repo"), "a" * 40)
    assert loaded.buffer is payload
    assert calls == [[
        "git",
        "--no-replace-objects",
        "-C",
        "/repo",
        "cat-file",
        "blob",
        f"{'a' * 40}:{PROBE.CONTRACT_PATH}",
    ]]


def test_schedule_has_preflight_wait_strata_and_thirteen_runs() -> None:
    contract = PROBE.hash_then_parse_contract(CONTRACT_PATH.read_bytes()).value
    strata = [window["stratum"] for window in contract["windows"]]
    assert strata.count("preflight") == 1
    assert strata.count("wait30") == 6
    assert strata.count("wait60") == 6
    assert len(contract["runs"]) == 13
    assert [run["run_id"] for run in contract["runs"]] == [
        f"R{index:02d}" for index in range(1, 14)
    ]
    assert contract["workloads"]["W1"] == list(PROBE.W1_ARGV)
    assert contract["workloads"]["W2"] == list(PROBE.W2_ARGV)


@pytest.mark.parametrize(
    "cache_text",
    [
        "CCBENCH_TRACE:STRING=0\n",
        "CCBENCH_TRACE:STRING=0\nCCBENCH_TRACE:STRING=0\nCCBENCH_ADD_ANALYSIS:STRING=0\n",
        "CCBENCH_TRACE:STRING=1\nCCBENCH_ADD_ANALYSIS:STRING=0\n",
    ],
)
def test_cmake_cache_missing_duplicate_and_value_mismatch(cache_text: str) -> None:
    with pytest.raises(ValueError):
        PROBE.parse_cmake_cache_exact(
            cache_text, {"CCBENCH_TRACE": "0", "CCBENCH_ADD_ANALYSIS": "0"}
        )


def test_compile_argv_trace_analysis_exactness() -> None:
    PROBE.validate_build_artifacts(_cache(0, 0), _compile_commands(0, 0), trace=0, analysis=0)
    PROBE.validate_build_artifacts(_cache(1, 1), _compile_commands(1, 1), trace=1, analysis=1)
    with pytest.raises(ValueError, match="TRACE"):
        PROBE.validate_build_artifacts(_cache(0, 0), _compile_commands(1, 0), trace=0, analysis=0)
    duplicated = _compile_commands(0, 0)
    duplicated[0]["arguments"].append("-DTRACE=0")
    with pytest.raises(ValueError, match="TRACE"):
        PROBE.validate_build_artifacts(_cache(0, 0), duplicated, trace=0, analysis=0)


def test_stock_compile_argv_rejects_mode_macro() -> None:
    commands = _compile_commands(0, 0)
    commands[0]["arguments"].append("-DIZANAGI_T139_PC_MODE1=1")
    with pytest.raises(ValueError, match="MODE1"):
        PROBE.validate_build_artifacts(_cache(0, 0), commands, trace=0, analysis=0)


def test_compiler_identity_drift_fields() -> None:
    baseline = {
        "command_v": "/usr/bin/gcc",
        "realpath": "/usr/bin/gcc-11",
        "version_stdout_b64": "YQ==",
        "version_stderr_b64": "",
        "version_stdout_sha256": "a" * 64,
        "version_stderr_sha256": "b" * 64,
        "executable_sha256": "c" * 64,
        "size_bytes": 100,
    }
    assert PROBE.compare_compiler_identity(baseline, dict(baseline)) == []
    for field in ("command_v", "realpath", "version_stdout_b64", "executable_sha256", "size_bytes"):
        drifted = dict(baseline)
        drifted[field] = 101 if field == "size_bytes" else "different"
        assert field in PROBE.compare_compiler_identity(baseline, drifted)


def test_configure_argv_uses_absolute_compiler_paths_and_trace_split() -> None:
    common = {
        "source": "/source",
        "build": "/build",
        "prefix": "/gflags;/glog",
        "third_party": "/third",
        "gflags_pin": "a" * 40,
        "glog_pin": "b" * 40,
        "gcc_realpath": "/usr/bin/gcc-11",
        "gxx_realpath": "/usr/bin/g++-11",
    }
    trace0 = PROBE.expected_configure_argv(**common, trace=0, analysis=0)
    trace1 = PROBE.expected_configure_argv(**common, trace=1, analysis=1)
    assert trace0.count("-DCCBENCH_TRACE=0") == 1
    assert trace1.count("-DCCBENCH_TRACE=1") == 1
    assert trace0[-2:] == ["-DCCBENCH_ADD_ANALYSIS=0", "-DCMAKE_CXX_FLAGS="]
    assert trace1[-2:] == ["-DCCBENCH_ADD_ANALYSIS=1", "-DCMAKE_CXX_FLAGS="]
    assert "-DCMAKE_C_COMPILER=/usr/bin/gcc-11" in trace0
    assert "-DCMAKE_CXX_COMPILER=/usr/bin/g++-11" in trace0


def test_trace1_build_failure_finalizes_all_expected_rows(tmp_path: Path) -> None:
    state_path, output, _state = _new_state(tmp_path)
    argv_path = output / "configure-trace1.argv.json"
    argv_path.write_text("[]\n", encoding="utf-8")
    configure_log = output / "configure-trace1.log"
    build_log = output / "build-trace1.log"
    configure_log.write_text("configured\n", encoding="utf-8")
    build_log.write_text("failed\n", encoding="utf-8")
    PROBE.record_build(
        state_path,
        kind="trace1",
        status="failed",
        returncode=7,
        configure_elapsed_ns=1,
        build_elapsed_ns=2,
        configure_argv=[],
        configure_log=configure_log,
        build_log=build_log,
        cache_path=None,
        compile_commands_path=None,
        binary_path=None,
    )

    assert PROBE.finalize(state_path, output, exit_rc=7) == "incomplete"
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["terminal_status"] == "incomplete"
    assert receipt["trace1_build_witness"] == "failed"
    assert receipt["compiler_witness"] == "not_attempted"
    assert receipt["builds"][1]["status"] == "failed"
    assert receipt["builds"][1]["returncode"] == 7
    for name, expected_rows in (("windows.tsv", 13), ("runs.tsv", 13), ("builds.tsv", 2)):
        with (output / name).open(encoding="utf-8", newline="") as handle:
            assert len(list(csv.DictReader(handle, delimiter="\t"))) == expected_rows
    assert (output / "COMPLETED").read_text(encoding="ascii") == "incomplete\n"


def test_not_feasible_window_verdict_survives_trace1_build_failure(tmp_path: Path) -> None:
    state_path, output, state = _new_state(tmp_path)
    _make_state_feasible(state)
    windows = state["windows"]
    assert isinstance(windows, list)
    windows[5].update(_window(str(windows[5]["window_id"]), 101, 4800))
    builds = state["builds"]
    assert isinstance(builds, list)
    builds[1].update(status="failed", returncode=7)
    PROBE._write_json_atomic(state_path, state)

    assert PROBE.finalize(state_path, output) == "incomplete"
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["window_verdict"] == "not_feasible"
    assert receipt["trace1_build_witness"] == "failed"
    assert receipt["compiler_witness"] == "present"
    assert receipt["terminal_status"] == "incomplete"


@pytest.mark.parametrize(("exit_rc", "signal_name"), [(143, "TERM"), (130, "INT")])
def test_signal_finalization_records_origin_and_stays_incomplete(
    tmp_path: Path, exit_rc: int, signal_name: str
) -> None:
    state_path, output, state = _new_state(tmp_path)
    _make_state_feasible(state)
    PROBE._write_json_atomic(state_path, state)

    assert PROBE.finalize(state_path, output, exit_rc=exit_rc) == "incomplete"
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["terminal_status"] == "incomplete"
    assert receipt["driver_exit"]["returncode"] == exit_rc
    assert receipt["driver_exit"]["signal"] == signal_name
    assert f"driver_signal:{signal_name}" in receipt["failure_reasons"]


def test_run_failure_records_first_row_without_consuming_remaining_waits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path, output, _state = _new_state(tmp_path)
    binary = output / "fake-ycsb"
    binary.write_bytes(b"fake")
    calls: list[list[str]] = []
    schedule_events: list[str] = []
    original_write_json = PROBE._write_json_atomic

    def fake_samples(start_target: int, end_target: int) -> tuple[dict[str, object], dict[str, object]]:
        start = {
            "begin_ns": start_target,
            "end_ns": start_target,
            "sample_ns": start_target,
            "text": _line([100] * 8),
            "load1": "999",
            "foreign_count": 999,
        }
        end = {
            "begin_ns": end_target,
            "end_ns": end_target,
            "sample_ns": end_target,
            "text": _line([100, 100, 100, 148, 100, 100, 100, 100]),
            "load1": "999",
            "foreign_count": 999,
        }
        return start, end

    class FailedProcess:
        def __init__(self, argv: list[str], **_kwargs: object) -> None:
            calls.append(argv)
            schedule_events.append("popen")

        def wait(self, timeout: int | None = None) -> int:
            assert timeout == 15
            return 7

        def poll(self) -> int:
            return 7

    def track_state_write(path: Path, value: object) -> None:
        schedule_events.append("state-write")
        original_write_json(path, value)

    monkeypatch.setattr(PROBE, "_sample_window_targets", fake_samples)
    monkeypatch.setattr(PROBE.subprocess, "Popen", FailedProcess)
    monkeypatch.setattr(PROBE, "_write_json_atomic", track_state_write)
    assert PROBE.run_schedule(state_path, binary, output) == 12
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(calls) == 1
    assert schedule_events[0] == "popen"
    assert "state-write" in schedule_events[1:]
    assert state["runs"][0]["status"] == "failed"
    assert all(run["status"] == "not_observed" for run in state["runs"][1:])
    assert state["windows"][0]["observed"] is True
    assert all(window["observed"] is False for window in state["windows"][1:])
    assert PROBE.finalize(state_path, output, exit_rc=12) == "incomplete"
    assert (output / "COMPLETED").is_file()


def test_sigterm_path_can_only_complete_after_all_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path, output, _state = _new_state(tmp_path)
    binary = output / "fake-ycsb"
    binary.write_bytes(b"fake")

    def terminate_during_sample(_start: int, _end: int) -> tuple[dict[str, object], dict[str, object]]:
        os.kill(os.getpid(), signal.SIGTERM)
        raise AssertionError("signal handler did not interrupt the sampler")

    monkeypatch.setattr(PROBE, "_sample_window_targets", terminate_during_sample)
    assert PROBE.run_schedule(state_path, binary, output) == 143
    assert not (output / "COMPLETED").exists()
    assert PROBE.finalize(state_path, output, exit_rc=143) == "incomplete"
    assert all((output / name).is_file() for name in ("windows.tsv", "runs.tsv", "builds.tsv"))
    assert (output / "receipt.json").is_file()
    assert (output / "COMPLETED").is_file()


def test_shell_sigterm_trap_finalizes_before_reporting_completion(tmp_path: Path) -> None:
    output = tmp_path / "attempt"
    output.mkdir()
    stage = tmp_path / "stage"
    stage.mkdir()
    required_dirs = [
        tmp_path / name for name in ("snapshot", "third", "gflags", "glog")
    ]
    for directory in required_dirs:
        directory.mkdir()
    (required_dirs[0] / "snapshot-witness").write_text("fixture\n", encoding="utf-8")

    loaded = PROBE.hash_then_parse_contract(CONTRACT_PATH.read_bytes())
    contract = tmp_path / "contract.json"
    contract.write_bytes(loaded.buffer)
    contract_metadata = tmp_path / "contract-metadata.json"
    contract_metadata.write_text(
        json.dumps({"validated_contract": loaded.value}) + "\n", encoding="utf-8"
    )

    phase_marker = tmp_path / "copy-phase-entered"
    wait_fifo = tmp_path / "copy-phase-wait"
    os.mkfifo(wait_fifo)
    stub_bin = tmp_path / "stub-bin"
    stub_bin.mkdir()
    cp_stub = stub_bin / "cp"
    cp_stub.write_text(
        """#!/bin/bash
set -u
: > "$IZANAGI_TEST_PHASE_MARKER"
exec 3<> "$IZANAGI_TEST_WAIT_FIFO"
read -r _ <&3
""",
        encoding="utf-8",
    )
    cp_stub.chmod(0o755)

    driver_wrapper = tmp_path / "driver-wrapper.py"
    driver_wrapper.write_text(
        """import importlib.util
import os
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location(
    "t139_r4_env_probe_wrapped", os.environ["IZANAGI_TEST_PROBE"]
)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = probe
spec.loader.exec_module(probe)

if sys.argv[1] == "finalize":
    order = Path(os.environ["IZANAGI_TEST_PUBLISH_ORDER"])

    def record(name):
        with order.open("a", encoding="utf-8") as handle:
            handle.write(name + "\\n")

    original_tsv = probe._write_tsv_atomic
    original_json = probe._write_json_atomic
    original_marker = probe._create_completed_marker

    def write_tsv(path, *args, **kwargs):
        result = original_tsv(path, *args, **kwargs)
        record(Path(path).name)
        return result

    def write_json(path, *args, **kwargs):
        result = original_json(path, *args, **kwargs)
        if Path(path).name == "receipt.json":
            record(Path(path).name)
        return result

    def create_marker(path, *args, **kwargs):
        result = original_marker(path, *args, **kwargs)
        record(Path(path).name)
        return result

    probe._write_tsv_atomic = write_tsv
    probe._write_json_atomic = write_json
    probe._create_completed_marker = create_marker

raise SystemExit(probe.main())
""",
        encoding="utf-8",
    )
    order_log = output / "order.log"
    environment = {
        **os.environ,
        "PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}",
        "IZANAGI_T139_R4_PYTHON": str(driver_wrapper),
        "IZANAGI_T139_R4_INTERPRETER": sys.executable,
        "IZANAGI_T139_R4_CONTRACT_BLOB": str(contract),
        "IZANAGI_T139_R4_CONTRACT_METADATA": str(contract_metadata),
        "IZANAGI_T139_R4_CONTRACT_SHA256": loaded.sha256,
        "IZANAGI_CCBENCH_SNAPSHOT": str(required_dirs[0]),
        "IZANAGI_THIRDPARTY_SOURCE_ROOT": str(required_dirs[1]),
        "IZANAGI_GFLAGS_INSTALL": str(required_dirs[2]),
        "IZANAGI_GLOG_INSTALL": str(required_dirs[3]),
        "IZANAGI_GFLAGS_SRC_HEAD": "b" * 40,
        "IZANAGI_GLOG_SRC_HEAD": "c" * 40,
        "IZANAGI_RUN_COMMIT": "d" * 40,
        "IZANAGI_PROBE_STAGE": str(stage),
        "IZANAGI_TEST_PHASE_MARKER": str(phase_marker),
        "IZANAGI_TEST_WAIT_FIFO": str(wait_fifo),
        "IZANAGI_TEST_PROBE": str(PROBE_PATH),
        "IZANAGI_TEST_PUBLISH_ORDER": str(order_log),
        "PBS_JOBID": "signal.1",
    }
    process = subprocess.Popen(
        ["bash", str(SH_PATH), str(output)],
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    stdout = stderr = ""
    try:
        deadline = time.monotonic() + 5
        while (
            not phase_marker.exists()
            and process.poll() is None
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        if not phase_marker.exists():
            if process.poll() is not None:
                stdout, stderr = process.communicate()
            raise AssertionError(
                "driver did not reach copy phase: "
                f"rc={process.poll()} stdout={stdout!r} stderr={stderr!r}"
            )

        state = json.loads((output / "state.json").read_text(encoding="utf-8"))
        assert (stage / "ccbench-stock").is_dir()
        assert all(build["status"] == "not_observed" for build in state["builds"])
        assert process.poll() is None
        assert not (output / "COMPLETED").exists()

        os.killpg(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=5)

    assert process.returncode is not None, f"stdout={stdout!r} stderr={stderr!r}"
    assert order_log.read_text(encoding="utf-8").splitlines() == [
        "windows.tsv",
        "runs.tsv",
        "builds.tsv",
        "receipt.json",
        "COMPLETED",
    ]
    expected_tsv_rows = (("windows.tsv", 13), ("runs.tsv", 13), ("builds.tsv", 2))
    for name, expected_rows in expected_tsv_rows:
        with (output / name).open(encoding="utf-8", newline="") as handle:
            assert len(list(csv.DictReader(handle, delimiter="\t"))) == expected_rows
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["terminal_status"] == "incomplete"
    assert receipt["window_verdict"] == "incomplete"
    assert receipt["trace1_build_witness"] == "not_attempted"
    assert receipt["compiler_witness"] == "not_attempted"
    assert (output / "COMPLETED").read_text(encoding="ascii") == "incomplete\n"


def _run_shell_with_timeout_stub(
    tmp_path: Path, *, child_rc: int
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    output = tmp_path / "attempt"
    output.mkdir()
    stage = tmp_path / "stage"
    stage.mkdir()
    required_dirs = [
        tmp_path / name for name in ("snapshot", "third", "gflags", "glog")
    ]
    for directory in required_dirs:
        directory.mkdir()

    loaded = PROBE.hash_then_parse_contract(CONTRACT_PATH.read_bytes())
    contract = tmp_path / "contract.json"
    contract.write_bytes(loaded.buffer)
    contract_metadata = tmp_path / "contract-metadata.json"
    contract_metadata.write_text(
        json.dumps({"validated_contract": loaded.value}) + "\n", encoding="utf-8"
    )

    timeout_marker = tmp_path / f"timeout-returned-{child_rc}"
    stub_bin = tmp_path / "stub-bin"
    stub_bin.mkdir()
    timeout_stub = stub_bin / "timeout"
    timeout_stub.write_text(
        f"""#!/bin/bash
set -u
: > "$IZANAGI_TEST_TIMEOUT_MARKER"
exit {child_rc}
""",
        encoding="utf-8",
    )
    timeout_stub.chmod(0o755)

    environment = {
        **os.environ,
        "PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}",
        "IZANAGI_T139_R4_PYTHON": str(PROBE_PATH),
        "IZANAGI_T139_R4_INTERPRETER": sys.executable,
        "IZANAGI_T139_R4_CONTRACT_BLOB": str(contract),
        "IZANAGI_T139_R4_CONTRACT_METADATA": str(contract_metadata),
        "IZANAGI_T139_R4_CONTRACT_SHA256": loaded.sha256,
        "IZANAGI_CCBENCH_SNAPSHOT": str(required_dirs[0]),
        "IZANAGI_THIRDPARTY_SOURCE_ROOT": str(required_dirs[1]),
        "IZANAGI_GFLAGS_INSTALL": str(required_dirs[2]),
        "IZANAGI_GLOG_INSTALL": str(required_dirs[3]),
        "IZANAGI_GFLAGS_SRC_HEAD": "b" * 40,
        "IZANAGI_GLOG_SRC_HEAD": "c" * 40,
        "IZANAGI_RUN_COMMIT": "d" * 40,
        "IZANAGI_PROBE_STAGE": str(stage),
        "IZANAGI_TEST_TIMEOUT_MARKER": str(timeout_marker),
        "PBS_JOBID": "cap.1",
    }
    result = subprocess.run(
        ["bash", str(SH_PATH), str(output)],
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        check=False,
    )

    return result, output, timeout_marker


def test_shell_phase_cap_124_is_not_recorded_as_signal_termination(tmp_path: Path) -> None:
    result, output, timeout_marker = _run_shell_with_timeout_stub(tmp_path, child_rc=124)

    assert timeout_marker.is_file()
    assert result.returncode == 8, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["terminal_status"] == "incomplete"
    assert receipt["driver_exit"] == {
        **PROBE.metadata(),
        "returncode": 8,
        "signal": None,
        "signal_identity_best_effort": True,
        "signal_identity_limitation": (
            "group-TERM may be recorded as the current stage failure code"
        ),
    }
    assert all(
        not reason.startswith("driver_signal:") for reason in receipt["failure_reasons"]
    )
    assert (output / "COMPLETED").read_text(encoding="ascii") == "incomplete\n"


def test_shell_child_normal_exit_143_is_not_recorded_as_term(tmp_path: Path) -> None:
    result, output, timeout_marker = _run_shell_with_timeout_stub(tmp_path, child_rc=143)

    assert timeout_marker.is_file()
    assert result.returncode == 8, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["terminal_status"] == "incomplete"
    assert receipt["driver_exit"] == {
        **PROBE.metadata(),
        "returncode": 8,
        "signal": None,
        "signal_identity_best_effort": True,
        "signal_identity_limitation": (
            "group-TERM may be recorded as the current stage failure code"
        ),
    }
    assert all(
        not reason.startswith("driver_signal:") for reason in receipt["failure_reasons"]
    )
    assert (output / "COMPLETED").read_text(encoding="ascii") == "incomplete\n"


def test_driver_receipt_pins_group_term_signal_identity_limit(tmp_path: Path) -> None:
    state_path, output, _state = _new_state(tmp_path)
    assert PROBE.finalize(state_path, output, exit_rc=8) == "incomplete"

    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["driver_exit"]["signal_identity_best_effort"] is True
    assert receipt["driver_exit"]["signal_identity_limitation"] == (
        "group-TERM may be recorded as the current stage failure code"
    )
    shell = SH_PATH.read_text(encoding="utf-8")
    assert "Bash may defer a pending TERM trap" in shell
    assert "child can die first and make wait return normally" in shell


def test_finalize_exception_never_marks_partial_publish_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path, output, _state = _new_state(tmp_path)
    original = PROBE._write_json_atomic

    def fail_receipt(path: Path, value: object) -> None:
        if path.name == "receipt.json":
            raise OSError("injected receipt publish failure")
        original(path, value)

    monkeypatch.setattr(PROBE, "_write_json_atomic", fail_receipt)
    with pytest.raises(OSError, match="injected receipt"):
        PROBE.finalize(state_path, output, exit_rc=12)
    assert all((output / name).is_file() for name in ("windows.tsv", "runs.tsv", "builds.tsv"))
    assert not (output / "receipt.json").exists()
    assert not (output / "COMPLETED").exists()


def test_publish_order_is_atomic_tsv_then_receipt_then_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path, output, _state = _new_state(tmp_path)
    published: list[str] = []
    original_replace = PROBE.os.replace
    original_marker = PROBE._create_completed_marker

    def record_replace(source: Path, destination: Path) -> None:
        original_replace(source, destination)
        if Path(destination).parent == output:
            published.append(Path(destination).name)

    def record_marker(path: Path, decision: str) -> None:
        original_marker(path, decision)
        published.append(path.name)

    monkeypatch.setattr(PROBE.os, "replace", record_replace)
    monkeypatch.setattr(PROBE, "_create_completed_marker", record_marker)
    assert PROBE.finalize(state_path, output, exit_rc=12) == "incomplete"
    assert published[-5:] == [
        "windows.tsv",
        "runs.tsv",
        "builds.tsv",
        "receipt.json",
        "COMPLETED",
    ]


def test_staged_contract_replacement_trips_init_digest_comparison(tmp_path: Path) -> None:
    payload = CONTRACT_PATH.read_bytes()
    expected_digest = hashlib.sha256(payload).hexdigest()
    loaded = PROBE.hash_then_parse_contract(payload)
    staged = tmp_path / "contract.json"
    staged.write_bytes(payload + b"\n")
    metadata_path = tmp_path / "contract-metadata.json"
    metadata_path.write_text(
        json.dumps({"validated_contract": loaded.value}), encoding="utf-8"
    )
    state_path = tmp_path / "state.json"
    assert PROBE.main(
        [
            "init-state",
            "--contract",
            str(staged),
            "--state",
            str(state_path),
            "--commit",
            "a" * 40,
            "--jobid",
            "test.1",
            "--expected-contract-sha256",
            expected_digest,
            "--contract-metadata",
            str(metadata_path),
        ]
    ) == 14
    state = json.loads(state_path.read_text(encoding="utf-8"))
    reads = state["contract_digest_reads"]
    assert reads["contract_load_sha256"] == expected_digest
    assert reads["init_state_sha256"] == hashlib.sha256(staged.read_bytes()).hexdigest()
    assert reads["exact_match"] is False
    assert "contract_digest_mismatch:contract-load:init-state" in state["failure_reasons"]


def test_init_state_exception_still_creates_all_expected_state_rows(tmp_path: Path) -> None:
    payload = CONTRACT_PATH.read_bytes()
    loaded = PROBE.hash_then_parse_contract(payload)
    staged = tmp_path / "contract.json"
    staged.write_bytes(b"not-json")
    metadata_path = tmp_path / "contract-metadata.json"
    metadata_path.write_text(
        json.dumps({"validated_contract": loaded.value}), encoding="utf-8"
    )
    state_path = tmp_path / "state.json"
    assert not PROBE.initialize_state(
        staged,
        state_path,
        commit="a" * 40,
        jobid="test.1",
        expected_contract_sha256=loaded.sha256,
        contract_metadata_path=metadata_path,
    )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(state["windows"]) == 13
    assert len(state["runs"]) == 13
    assert len(state["builds"]) == 2
    assert state["failure_reasons"][0].startswith("init_state_exception:ContractError:")


def test_finalize_call_site_does_not_forward_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path, output, state = _new_state(tmp_path)
    _make_state_feasible(state)
    state["environment"] = {
        "load1": "999",
        "foreign_process_count": 999,
        "cgroup_text": "diagnostic-only",
    }
    PROBE._write_json_atomic(state_path, state)
    original = PROBE.derive_decision
    calls: list[tuple[int, bool, bool, str, str, bool]] = []

    def exact_decision_signature(
        windows: list[dict[str, object]],
        expected_ids: list[str],
        *,
        runs_ok: bool,
        trace0_build_ok: bool,
        trace1_build_witness: str,
        compiler_witness: str,
        driver_signaled: bool = False,
    ) -> object:
        calls.append(
            (
                len(windows),
                runs_ok,
                trace0_build_ok,
                trace1_build_witness,
                compiler_witness,
                driver_signaled,
            )
        )
        return original(
            windows,
            expected_ids,
            runs_ok=runs_ok,
            trace0_build_ok=trace0_build_ok,
            trace1_build_witness=trace1_build_witness,
            compiler_witness=compiler_witness,
            driver_signaled=driver_signaled,
        )

    monkeypatch.setattr(PROBE, "derive_decision", exact_decision_signature)
    assert PROBE.finalize(state_path, output) == "feasible"
    assert calls == [(13, True, True, "present", "present", False)]


def test_compiler_rechecks_require_build_immediate_and_post_build_labels() -> None:
    compilers = {
        "gcc": {},
        "gxx": {},
        "identity_rechecks": _successful_rechecks(),
    }
    assert PROBE.compiler_rechecks_ok(compilers)
    compilers["identity_rechecks"] = [
        row for row in compilers["identity_rechecks"] if row["label"] != "before-build-trace1"
    ]
    assert not PROBE.compiler_rechecks_ok(compilers)


def test_attempt_gate_rejects_observed_receipt_and_tsv_rows(tmp_path: Path) -> None:
    namespace = tmp_path / "probe"
    attempt = namespace / "job-1"
    attempt.mkdir(parents=True)
    (attempt / "receipt.json").write_text(
        json.dumps({"windows": [{"observed": False} for _ in range(13)]}), encoding="utf-8"
    )
    assert PROBE.attempt_namespace_allows_start(namespace)
    (attempt / "receipt.json").write_text(
        json.dumps({"windows": [{"observed": index == 0} for index in range(13)]}),
        encoding="utf-8",
    )
    assert not PROBE.attempt_namespace_allows_start(namespace)
    (attempt / "receipt.json").unlink()
    (attempt / "windows.tsv").write_text(
        "window_id\tobserved\n"
        + "\n".join(
            f"{'preflight' if index == 0 else f'post-{index:02d}'}\t"
            f"{'true' if index == 0 else 'false'}"
            for index in range(13)
        )
        + "\n",
        encoding="utf-8",
    )
    assert not PROBE.attempt_namespace_allows_start(namespace)
    assert PROBE.main(["attempt-gate", "--namespace", str(namespace)]) == 14


@pytest.mark.parametrize("path", [SH_PATH, PBS_PATH])
def test_shell_artifacts_pass_bash_n(path: Path) -> None:
    completed = subprocess.run(
        ["bash", "-n", str(path)], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")


def test_driver_static_caps_order_and_finalizer_contract() -> None:
    shell = SH_PATH.read_text(encoding="utf-8")
    assert "DRIVER_CAP_NS=2045000000000" in shell
    assert "driver_run 960" in shell
    assert "record_one_build trace0 0 0 60 180" in shell
    assert "record_one_build trace1 1 1 90 420" in shell
    assert shell.index("record_one_build trace0") < shell.index("sample --state")
    assert shell.index("trap finalize_driver EXIT") < shell.index("monotonic-ns")
    assert "before-build-$kind" in shell
    assert "after-build-$kind" in shell
    assert shell.index("before-build-$kind") < shell.index("cmake --build")
    assert shell.index("cmake --build") < shell.index("after-build-$kind")
    assert "if [[ -e $OUT/COMPLETED ]]; then FINALIZED=1; fi" in shell
    assert "SIGKILL cannot run a trap" in shell
    assert "rc > 128" not in shell
    assert "rc <= 192" not in shell
    assert "time.monotonic_ns" not in shell  # delegated to the Python monotonic clock
    assert "monotonic-ns" in shell


def test_pbs_contract_blob_namespace_and_phase_budget_are_static() -> None:
    pbs = PBS_PATH.read_text(encoding="utf-8")
    assert "output/env/pegasus/t139-r4-env-probe" in pbs
    assert "contract-load" in pbs
    assert "cat-file blob" in pbs
    assert "rev-parse --show-toplevel" in pbs
    assert "rev-parse --absolute-git-dir" in pbs
    assert "rev-parse --git-common-dir" in pbs
    assert "IZANAGI_T139_EXPECTED_WORKTREE_ROOT" in pbs
    assert "attempt-gate" in pbs
    assert "mkdir -p" not in pbs
    assert "12 * 5 + preflight 5 = 65" in pbs
    assert "deadline_run 2045" in pbs
    assert "903 + 2045 + 120 = 3068 <= deadline 3300 < walltime 3600" in pbs
    assert "date +%s" not in pbs


def _run() -> int:
    """Keep this new file inside the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
