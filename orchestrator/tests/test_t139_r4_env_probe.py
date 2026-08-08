from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

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
    return {"window_id": window_id, "busy": busy, "total": total, "status": status}


def _decision_windows(busy: int, total: int) -> tuple[list[dict[str, object]], list[str]]:
    ids = ["preflight", *[f"post-{index:02d}" for index in range(1, 13)]]
    return [_window(window_id, busy, total) for window_id in ids], ids


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
    assert PROBE.derive_decision(
        windows, ids, runs_ok=True, builds_ok=True, compiler_ok=True
    ) == "confirmed_1.0"


def test_decision_exactly_two_point_zero() -> None:
    windows, ids = _decision_windows(1, 24)
    assert PROBE.derive_decision(
        windows, ids, runs_ok=True, builds_ok=True, compiler_ok=True
    ) == "escalated_2.0"


def test_decision_above_two_point_zero() -> None:
    windows, ids = _decision_windows(1, 23)
    assert PROBE.derive_decision(
        windows, ids, runs_ok=True, builds_ok=True, compiler_ok=True
    ) == "not_feasible"


def test_decision_malformed_mix_is_incomplete() -> None:
    windows, ids = _decision_windows(0, 48)
    windows[7]["status"] = "malformed"
    assert PROBE.derive_decision(
        windows, ids, runs_ok=True, builds_ok=True, compiler_ok=True
    ) == "incomplete"


def test_diagnostics_do_not_change_positive_decision() -> None:
    windows, ids = _decision_windows(0, 48)
    low_diagnostics = {"load1": "0.01", "foreign_count": 0, "cgroup": "quiet"}
    high_diagnostics = {"load1": "999", "foreign_count": 999, "cgroup": "different"}
    receipt_a = {"windows": copy.deepcopy(windows), "diagnostics": low_diagnostics}
    receipt_b = {"windows": copy.deepcopy(windows), "diagnostics": high_diagnostics}
    decision_a = PROBE.derive_decision(
        receipt_a["windows"], ids, runs_ok=True, builds_ok=True, compiler_ok=True
    )
    decision_b = PROBE.derive_decision(
        receipt_b["windows"], ids, runs_ok=True, builds_ok=True, compiler_ok=True
    )
    assert decision_a == decision_b == "confirmed_1.0"


def test_contract_exact_schema_types_lengths_and_metadata() -> None:
    loaded = PROBE.hash_then_parse_contract(CONTRACT_PATH.read_bytes())
    contract = loaded.value
    assert set(contract) == PROBE.TOP_LEVEL_KEYS
    assert len(contract["windows"]) == 13
    assert len(contract["runs"]) == 13
    assert len(contract["counter_names"]) == 8
    assert contract["thresholds"] == ["1.0", "2.0"]
    assert contract["phase_budget"]["adjacency_budget_s"] == 12 * 5 + 5 == 65
    assert contract["terminal_attempt_policy"]["resubmissions_after_observation"] == 0
    assert contract["terminal_attempt_policy"]["pre_submit_ledger_create_only"] is True
    assert contract["terminal_attempt_policy"]["pre_measurement_resubmission_limit"] == 1
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


@pytest.mark.parametrize("path", [SH_PATH, PBS_PATH])
def test_shell_artifacts_pass_bash_n(path: Path) -> None:
    completed = subprocess.run(
        ["bash", "-n", str(path)], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")


def test_driver_static_caps_order_and_finalizer_contract() -> None:
    shell = SH_PATH.read_text(encoding="utf-8")
    assert "DRIVER_CAP_NS=1895000000000" in shell
    assert "record_one_build trace0 0 0 60 180" in shell
    assert "record_one_build trace1 1 1 90 420" in shell
    assert shell.index("record_one_build trace0") < shell.index("sample --state")
    assert "trap finalize_driver EXIT" in shell
    assert "time.monotonic_ns" not in shell  # delegated to the Python monotonic clock
    assert "monotonic-ns" in shell


def test_pbs_contract_blob_namespace_and_phase_budget_are_static() -> None:
    pbs = PBS_PATH.read_text(encoding="utf-8")
    assert "output/env/pegasus/t139-r4-env-probe" in pbs
    assert "contract-load" in pbs
    assert "cat-file blob" in pbs
    assert "12 * 5 + preflight 5 = 65" in pbs
    assert "deadline_run 1895" in pbs
    assert "2798 <= deadline 3300 < walltime 3600" in pbs


def _run() -> int:
    """Keep this new file inside the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
