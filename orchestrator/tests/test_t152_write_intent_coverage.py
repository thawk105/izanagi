# -*- coding: utf-8 -*-
"""T-152 characterization driver unit tests (no C++ build or benchmark run)."""
from __future__ import annotations

import copy
import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ORCHESTRATOR = os.path.dirname(HERE)
ROOT = os.path.dirname(ORCHESTRATOR)
sys.path.insert(0, ROOT)

from orchestrator.campaign import t152_write_intent_coverage as driver  # noqa: E402


# Independent test-side literals: do not import the driver's reason constants.
MISSING_REASON = "intent-missing-from-write-set"
UNEXPECTED_REASON = "write-set-entry-without-intent"

# Independent mirror of result_to_dict's current integrity counters.
INTEGRITY_COUNTERS = (
    "orphan_reads",
    "version_dups",
    "dup_txids",
    "genesis_commits",
    "missing_txids",
    "write_version_mismatch",
    "malformed_keys",
    "framing_violations",
    "lock_coverage_violations",
    "write_intent_violations",
    "permutation_violations",
)


def _integrity(intent_total: int) -> dict:
    counters = {name: 0 for name in INTEGRITY_COUNTERS}
    counters["write_intent_violations"] = intent_total
    return {
        "clean": intent_total == 0,
        **counters,
        "notes": [],
    }


def _run(
    *,
    intent_reasons: dict[str, int] | None = None,
    write_ops: tuple[str, ...] = ("U",),
    aborts: int = 0,
    certified: bool = True,
) -> dict:
    reasons = dict(intent_reasons or {})
    intent_total = sum(reasons.values())
    return {
        "workload": "ycsb",
        "flags": {},
        "abort_exercised": aborts > 0,
        "trace": {
            "files": 1,
            "write_intent_total": intent_total,
            "write_intent_reasons": reasons,
            "lock_coverage_violations": 0,
            "permutation_violations": 0,
            "write_ops": list(write_ops),
        },
        "verifier": {
            "exit_code": 0 if intent_total == 0 else 3,
            "verdict": "serializable" if certified else "indeterminate",
            "certified": certified,
            "serializable": True,
            "total_cycles": 0,
            "txns": 1,
            "reads": 0,
            "writes": 10,
            "integrity": _integrity(intent_total),
        },
    }


def _passing_results() -> dict[str, dict]:
    return {
        "stock_single": _run(),
        "stock_abort": _run(aborts=1, write_ops=("U", "D")),
        "bomb_smoke": _run(write_ops=("U", "I", "D")),
        "erase": _run(
            intent_reasons={MISSING_REASON: 1},
            certified=False,
        ),
        "forge": _run(
            intent_reasons={UNEXPECTED_REASON: 1},
            certified=False,
        ),
        "opswap": _run(
            intent_reasons={MISSING_REASON: 1, UNEXPECTED_REASON: 1},
            certified=False,
        ),
        "ptrswap": _run(
            intent_reasons={MISSING_REASON: 2, UNEXPECTED_REASON: 2},
            certified=False,
        ),
    }


def _break_only(results: dict[str, dict], check_name: str) -> None:
    if check_name == "stock_silent":
        results["stock_single"]["trace"]["lock_coverage_violations"] = 1
    elif check_name == "abort_exercised":
        results["stock_abort"]["abort_exercised"] = False
    elif check_name == "bomb_ops":
        # stock_abort independently retains D, so producer_union stays true.
        results["bomb_smoke"]["trace"]["write_ops"] = ["U", "I"]
    elif check_name == "erase":
        results["erase"]["verifier"]["verdict"] = "serializable"
    elif check_name == "forge":
        results["forge"]["verifier"]["verdict"] = "serializable"
    elif check_name == "opswap":
        results["opswap"]["verifier"]["verdict"] = "serializable"
    elif check_name == "ptrswap":
        results["ptrswap"]["verifier"]["verdict"] = "serializable"
    elif check_name == "three_way_reconciliation":
        # Keep stock_abort's own predicate true while breaking only the
        # raw-I-dependent verifier exit-code reconciliation.
        results["stock_abort"]["verifier"]["exit_code"] = 3
    else:  # pragma: no cover - protects this test helper's closed registry.
        raise AssertionError(f"unknown check: {check_name}")


def test_evaluate_checks_accepts_complete_synthetic_characterization():
    evaluated = driver._evaluate_checks(_passing_results())
    assert evaluated["all_pass"] is True
    assert all(evaluated.values())


def test_bomb_flags_assign_exactly_one_s1_and_one_s3_worker():
    expected = {
        "thread_num": "2",
        "bomb_l1_thread_num": "0",
        "bomb_s1_thread_num": "1",
        "bomb_s2_thread_num": "0",
        "bomb_s3_thread_num": "1",
        "bomb_s4_thread_num": "0",
    }
    assert {
        name: driver._BOMB_FLAGS[name]
        for name in expected
    } == expected


@pytest.mark.parametrize(
    "check_name",
    [
        "stock_silent",
        "abort_exercised",
        "bomb_ops",
        "erase",
        "forge",
        "opswap",
        "ptrswap",
        "three_way_reconciliation",
    ],
)
def test_evaluate_checks_each_predicate_has_an_independent_negative(check_name):
    results = copy.deepcopy(_passing_results())
    _break_only(results, check_name)

    evaluated = driver._evaluate_checks(results)

    assert evaluated[check_name] is False
    assert evaluated["all_pass"] is False
    other_checks = {
        name: passed for name, passed in evaluated.items()
        if name not in {check_name, "all_pass"}
    }
    assert all(other_checks.values()), (
        f"{check_name} negative unexpectedly broke other predicates: {other_checks}"
    )


def _set_intent_reasons(run: dict, reasons: dict[str, int]) -> None:
    total = sum(reasons.values())
    run["trace"]["write_intent_reasons"] = dict(reasons)
    run["trace"]["write_intent_total"] = total
    run["verifier"]["integrity"]["write_intent_violations"] = total


def test_exit_code_negative_is_one():
    assert driver._exit_code(False) == 1


def test_main_routes_false_payload_through_exit_code(
    monkeypatch, tmp_path, capsys
):
    output_path = str(tmp_path / "result.json")
    payload = {"checks": {}, "all_pass": False}
    published = []
    exit_inputs = []
    monkeypatch.setattr(
        driver, "_collect_payload", lambda: (payload, output_path)
    )
    monkeypatch.setattr(
        driver, "_publish_json",
        lambda actual_payload, actual_path: published.append(
            (actual_payload, actual_path)
        ),
    )
    monkeypatch.setattr(
        driver, "_exit_code",
        lambda all_pass: exit_inputs.append(all_pass) or 17,
    )

    assert driver.main() == 17
    assert exit_inputs == [False]
    assert published == [(payload, output_path)]
    assert "all_pass=False" in capsys.readouterr().out


def test_producer_union_check_is_retained():
    evaluated = driver._evaluate_checks(_passing_results())
    assert evaluated["producer_union"] is True


def test_bomb_ops_requires_update_in_bomb_trace():
    results = _passing_results()
    results["bomb_smoke"]["trace"]["write_ops"] = ["I", "D"]

    evaluated = driver._evaluate_checks(results)

    assert evaluated["bomb_ops"] is False
    assert evaluated["producer_union"] is True
    assert evaluated["all_pass"] is False


def test_stock_writes_must_be_positive():
    results = _passing_results()
    results["stock_single"]["verifier"]["writes"] = 0
    evaluated = driver._evaluate_checks(results)
    assert evaluated["stock_silent"] is False
    assert evaluated["all_pass"] is False


@pytest.mark.parametrize(
    ("check_name", "run_name", "section", "field", "bad_value"),
    [
        ("stock_silent", "stock_single", "trace", "write_intent_total", 1),
        ("stock_silent", "stock_single", "trace", "lock_coverage_violations", 1),
        ("stock_silent", "stock_single", "trace", "permutation_violations", 1),
        ("stock_silent", "stock_single", "verifier", "total_cycles", 1),
        ("stock_silent", "stock_single", "verifier", "certified", False),
        ("stock_silent", "stock_single", "verifier", "verdict", "indeterminate"),
        ("stock_silent", "stock_single", "verifier", "txns", 0),
        ("stock_silent", "stock_single", "verifier", "writes", 0),
        ("abort_exercised", "stock_abort", "trace", "write_intent_total", 1),
        ("abort_exercised", "stock_abort", "verifier", "certified", False),
        ("bomb_ops", "bomb_smoke", "trace", "write_intent_total", 1),
        ("bomb_ops", "bomb_smoke", "verifier", "certified", False),
        ("erase", "erase", "trace", "write_intent_total", 0),
        ("erase", "erase", "verifier", "total_cycles", 1),
        ("erase", "erase", "verifier", "certified", True),
        ("erase", "erase", "verifier", "exit_code", 0),
        ("forge", "forge", "trace", "write_intent_total", 0),
        ("forge", "forge", "verifier", "total_cycles", 1),
        ("forge", "forge", "verifier", "certified", True),
        ("forge", "forge", "verifier", "exit_code", 0),
        ("opswap", "opswap", "trace", "write_intent_total", 1),
        ("opswap", "opswap", "verifier", "total_cycles", 1),
        ("opswap", "opswap", "verifier", "certified", True),
        ("opswap", "opswap", "verifier", "exit_code", 0),
        ("ptrswap", "ptrswap", "trace", "write_intent_total", 3),
        ("ptrswap", "ptrswap", "verifier", "total_cycles", 1),
        ("ptrswap", "ptrswap", "verifier", "certified", True),
        ("ptrswap", "ptrswap", "verifier", "exit_code", 0),
    ],
)
def test_remaining_evaluate_conjuncts_have_direct_negatives(
    check_name, run_name, section, field, bad_value
):
    results = _passing_results()
    results[run_name][section][field] = bad_value
    evaluated = driver._evaluate_checks(results)
    assert evaluated[check_name] is False
    assert evaluated["all_pass"] is False


def test_producer_union_negative_is_kept_despite_bomb_implication():
    results = _passing_results()
    for run_name in ("stock_single", "stock_abort", "bomb_smoke"):
        results[run_name]["trace"]["write_ops"] = []
    evaluated = driver._evaluate_checks(results)
    assert evaluated["producer_union"] is False
    # bomb_ops now requires the same U/I/D set and therefore implies this union.
    assert evaluated["bomb_ops"] is False


@pytest.mark.parametrize(
    ("run_name", "expected_reason", "other_reason"),
    [
        ("erase", MISSING_REASON, "independent-extra-reason"),
        ("forge", UNEXPECTED_REASON, "independent-extra-reason"),
    ],
)
def test_single_reason_controls_reject_an_extra_reason(
    run_name, expected_reason, other_reason
):
    results = _passing_results()
    _set_intent_reasons(
        results[run_name],
        {expected_reason: 1, other_reason: 1},
    )
    evaluated = driver._evaluate_checks(results)
    assert evaluated[run_name] is False
    assert evaluated["three_way_reconciliation"] is True


@pytest.mark.parametrize("run_name", ["erase", "forge", "opswap", "ptrswap"])
@pytest.mark.parametrize(
    "trace_counter",
    ["lock_coverage_violations", "permutation_violations"],
)
def test_broken_controls_reject_each_non_intent_trace_counter(
    run_name, trace_counter
):
    results = _passing_results()
    results[run_name]["trace"][trace_counter] = 1
    evaluated = driver._evaluate_checks(results)
    assert evaluated[run_name] is False


@pytest.mark.parametrize("run_name", ["erase", "forge", "opswap", "ptrswap"])
def test_broken_controls_reject_a_non_intent_verifier_counter(run_name):
    results = _passing_results()
    results[run_name]["verifier"]["integrity"]["orphan_reads"] = 1
    evaluated = driver._evaluate_checks(results)
    assert evaluated[run_name] is False


@pytest.mark.parametrize("run_name", ["stock_single", "stock_abort", "bomb_smoke"])
def test_each_stock_control_rejects_any_nonzero_integrity_counter(run_name):
    results = _passing_results()
    results[run_name]["verifier"]["integrity"]["orphan_reads"] = 1
    evaluated = driver._evaluate_checks(results)
    check_name = {
        "stock_single": "stock_silent",
        "stock_abort": "abort_exercised",
        "bomb_smoke": "bomb_ops",
    }[run_name]
    assert evaluated[check_name] is False


@pytest.mark.parametrize("counter", INTEGRITY_COUNTERS)
def test_stock_integrity_helper_checks_every_counter(counter):
    integrity = _integrity(0)
    integrity[counter] = 1
    assert driver._integrity_counters_zero(integrity) is False


@pytest.mark.parametrize(
    "counter",
    [name for name in INTEGRITY_COUNTERS if name != "write_intent_violations"],
)
def test_broken_integrity_helper_checks_every_non_intent_counter(counter):
    integrity = _integrity(1)
    integrity[counter] = 1
    assert driver._integrity_counters_zero(
        integrity, except_write_intent=True
    ) is False


@pytest.mark.parametrize(
    ("run_name", "reasons"),
    [
        ("opswap", {MISSING_REASON: 0, UNEXPECTED_REASON: 2}),
        ("opswap", {MISSING_REASON: 2, UNEXPECTED_REASON: 0}),
        ("ptrswap", {MISSING_REASON: 1, UNEXPECTED_REASON: 3}),
        ("ptrswap", {MISSING_REASON: 3, UNEXPECTED_REASON: 1}),
    ],
)
def test_swap_controls_require_both_directional_counts(run_name, reasons):
    results = _passing_results()
    _set_intent_reasons(results[run_name], reasons)
    evaluated = driver._evaluate_checks(results)
    assert evaluated[run_name] is False
    assert evaluated["three_way_reconciliation"] is True


def test_three_way_reconciliation_checks_verifier_exit_code():
    run = _run()
    assert driver._intent_reconciled(run) is True
    run["verifier"]["exit_code"] = 3
    assert driver._intent_reconciled(run) is False


def test_three_way_reconciliation_rejects_raw_verifier_count_mismatch():
    results = _passing_results()
    run = results["erase"]
    assert run["trace"]["write_intent_total"] == 1
    assert run["verifier"]["exit_code"] == 3
    run["verifier"]["integrity"]["write_intent_violations"] = 2

    evaluated = driver._evaluate_checks(results)

    assert evaluated["three_way_reconciliation"] is False
    assert evaluated["all_pass"] is False
    assert all(
        passed for name, passed in evaluated.items()
        if name not in {"three_way_reconciliation", "all_pass"}
    )


def test_cli_without_required_ccbench_sha_fails_closed():
    env = os.environ.copy()
    env.pop("IZANAGI_T152_CCBENCH_SHA", None)
    proc = subprocess.run(
        [
            sys.executable,
            os.path.join(
                ROOT, "orchestrator", "campaign",
                "t152_write_intent_coverage.py",
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode != 0
    assert "IZANAGI_T152_CCBENCH_SHA is required (no default)" in proc.stderr


def _dependency_prefix(
    base: Path,
    name: str,
    header: str,
    library: str,
) -> Path:
    prefix = base / name
    header_path = prefix / header
    library_path = prefix / library
    header_path.parent.mkdir(parents=True)
    library_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.touch()
    library_path.touch()
    return prefix


def test_dependency_contract_records_header_and_library_realpaths(tmp_path):
    gflags = _dependency_prefix(
        tmp_path,
        "gflags-prefix",
        "include/gflags/gflags.h",
        "lib/libgflags.a",
    )
    glog = _dependency_prefix(
        tmp_path,
        "glog-prefix",
        "include/glog/logging.h",
        "lib/libglog.a",
    )

    record, effective = driver._dependency_contract(
        f"{gflags}{os.pathsep}{glog}"
    )

    assert record == {
        "cmake_prefix_path": [str(gflags.resolve()), str(glog.resolve())],
        "gflags": {
            "headers": [
                str((gflags / "include/gflags/gflags.h").resolve()),
            ],
            "libraries": [
                str((gflags / "lib/libgflags.a").resolve()),
            ],
        },
        "glog": {
            "headers": [
                str((glog / "include/glog/logging.h").resolve()),
            ],
            "libraries": [
                str((glog / "lib/libglog.a").resolve()),
            ],
        },
    }
    assert effective == f"{gflags.resolve()};{glog.resolve()}"


def test_dependency_contract_accepts_shared_only_libraries(tmp_path):
    gflags = _dependency_prefix(
        tmp_path,
        "gflags-prefix",
        "include/gflags/gflags.h",
        "lib/libgflags.so",
    )
    glog = _dependency_prefix(
        tmp_path,
        "glog-prefix",
        "include/glog/logging.h",
        "lib/libglog.so",
    )
    record, _ = driver._dependency_contract(f"{gflags}{os.pathsep}{glog}")
    assert record["gflags"]["libraries"] == [
        str((gflags / "lib/libgflags.so").resolve()),
    ]
    assert record["glog"]["libraries"] == [
        str((glog / "lib/libglog.so").resolve()),
    ]


def test_dependency_contract_records_all_static_and_shared_candidates(tmp_path):
    gflags = _dependency_prefix(
        tmp_path,
        "gflags-prefix",
        "include/gflags/gflags.h",
        "lib/libgflags.a",
    )
    glog = _dependency_prefix(
        tmp_path,
        "glog-prefix",
        "include/glog/logging.h",
        "lib/libglog.a",
    )
    (gflags / "lib/libgflags.so").touch()
    (glog / "lib/libglog.so").touch()

    record, _ = driver._dependency_contract(f"{gflags}{os.pathsep}{glog}")

    assert record["gflags"]["libraries"] == [
        str((gflags / "lib/libgflags.so").resolve()),
        str((gflags / "lib/libgflags.a").resolve()),
    ]
    assert record["glog"]["libraries"] == [
        str((glog / "lib/libglog.so").resolve()),
        str((glog / "lib/libglog.a").resolve()),
    ]


@pytest.mark.parametrize(
    ("missing_dependency", "expected_fragment"),
    [
        ("gflags", "gflags header/library not found"),
        ("glog", "glog header/library not found"),
    ],
)
def test_dependency_contract_fails_closed_without_library(
    tmp_path, missing_dependency, expected_fragment
):
    gflags = _dependency_prefix(
        tmp_path,
        "gflags-prefix",
        "include/gflags/gflags.h",
        "lib/libgflags.a",
    )
    glog = _dependency_prefix(
        tmp_path,
        "glog-prefix",
        "include/glog/logging.h",
        "lib/libglog.a",
    )
    missing = {
        "gflags": gflags / "lib/libgflags.a",
        "glog": glog / "lib/libglog.a",
    }[missing_dependency]
    missing.unlink()

    with pytest.raises(RuntimeError, match=expected_fragment):
        driver._dependency_contract(f"{gflags}{os.pathsep}{glog}")


def _dependency_fixture(tmp_path: Path) -> tuple[dict, Path, Path]:
    gflags = _dependency_prefix(
        tmp_path,
        "gflags-prefix",
        "include/gflags/gflags.h",
        "lib/libgflags.a",
    )
    glog = _dependency_prefix(
        tmp_path,
        "glog-prefix",
        "include/glog/logging.h",
        "lib/libglog.a",
    )
    record, _ = driver._dependency_contract(f"{gflags}{os.pathsep}{glog}")
    return record, gflags, glog


def test_linked_dependency_contract_accepts_recorded_prefix_resolution(tmp_path):
    record, gflags, glog = _dependency_fixture(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / "CMakeCache.txt").write_text(
        "gflags_LIBRARY_FILE:FILEPATH="
        f"{gflags / 'lib/libgflags.a'}\n"
        "glog_LIBRARY_FILE:FILEPATH="
        f"{glog / 'lib/libglog.a'}\n",
        encoding="utf-8",
    )

    assert driver._linked_dependency_contract(str(build), record) == {
        "gflags_LIBRARY_FILE": str(
            (gflags / "lib/libgflags.a").resolve()
        ),
        "glog_LIBRARY_FILE": str((glog / "lib/libglog.a").resolve()),
    }


def test_linked_dependency_contract_rejects_prefix_mismatch(tmp_path):
    record, _, glog = _dependency_fixture(tmp_path)
    wrong_prefix = tmp_path / "wrong"
    wrong_library = wrong_prefix / "lib/libgflags.a"
    wrong_library.parent.mkdir(parents=True)
    wrong_library.touch()
    build = tmp_path / "build"
    build.mkdir()
    (build / "CMakeCache.txt").write_text(
        f"gflags_LIBRARY_FILE:FILEPATH={wrong_library}\n"
        f"glog_LIBRARY_FILE:FILEPATH={glog / 'lib/libglog.a'}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError, match="resolved outside recorded CMAKE_PREFIX_PATH"
    ):
        driver._linked_dependency_contract(str(build), record)


@pytest.mark.parametrize("missing_key", ["gflags_LIBRARY_FILE", "glog_LIBRARY_FILE"])
def test_linked_dependency_contract_rejects_missing_cache_key(
    tmp_path, missing_key
):
    record, gflags, glog = _dependency_fixture(tmp_path)
    values = {
        "gflags_LIBRARY_FILE": gflags / "lib/libgflags.a",
        "glog_LIBRARY_FILE": glog / "lib/libglog.a",
    }
    del values[missing_key]
    build = tmp_path / "build"
    build.mkdir()
    (build / "CMakeCache.txt").write_text(
        "".join(f"{key}:FILEPATH={value}\n" for key, value in values.items()),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="must contain exactly one"):
        driver._linked_dependency_contract(str(build), record)


def test_stock_build_wires_cmake_dependency_probe(monkeypatch, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    build = tmp_path / "build"
    calls = []

    @contextlib.contextmanager
    def fake_checkout(_sha, *, base_dir):
        assert base_dir == str(source)
        yield str(source)

    def fake_run(argv, **_kwargs):
        calls.append(argv)
        if "--build" in argv:
            binary = build / "cc/silo/ycsb_silo.exe"
            binary.parent.mkdir(parents=True)
            binary.touch(mode=0o755)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(driver, "checkout", fake_checkout)
    monkeypatch.setattr(driver, "_run_process", fake_run)

    driver._build(
        sha="a" * 40,
        ccbench_base=str(source),
        build_dir=str(build),
        cmake="/usr/bin/cmake",
        cc="/usr/bin/gcc",
        cxx="/usr/bin/g++",
        cmake_prefix_path="/deps",
        jobs=1,
        targets=("ycsb_silo.exe",),
        record_dependency_links=True,
    )

    project_include = [
        argument
        for argument in calls[0]
        if argument.startswith("-DCMAKE_PROJECT_INCLUDE=")
    ]
    assert len(project_include) == 1
    probe = Path(project_include[0].split("=", 1)[1])
    source_text = probe.read_text(encoding="utf-8")
    assert 'set("${_dep}_LIBRARY_FILE" "${_location}" CACHE FILEPATH' in source_text
    assert "cmake_language(DEFER CALL" in source_text


@pytest.mark.parametrize("with_static", [False, True])
def test_cmake_dependency_probe_accepts_actual_shared_resolution(
    tmp_path, with_static
):
    gflags = tmp_path / "gflags-prefix"
    glog = tmp_path / "glog-prefix"
    for prefix, header in (
        (gflags, "include/gflags/gflags.h"),
        (glog, "include/glog/logging.h"),
    ):
        header_path = prefix / header
        header_path.parent.mkdir(parents=True)
        header_path.touch()
        library_dir = prefix / "lib"
        library_dir.mkdir()
        dependency = "gflags" if prefix == gflags else "glog"
        (library_dir / f"lib{dependency}.so").touch()
        if with_static:
            (library_dir / f"lib{dependency}.a").touch()
    deps_record, effective = driver._dependency_contract(
        f"{gflags}{os.pathsep}{glog}"
    )
    source = tmp_path / "source"
    source.mkdir()
    build = tmp_path / "build"
    probe = driver._write_cmake_dependency_probe(str(build))
    (source / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.19)\n"
        "project(t152_dependency_probe NONE)\n"
        "find_library(gflags_LIBRARY_FILE NAMES gflags REQUIRED)\n"
        "find_library(glog_LIBRARY_FILE NAMES glog REQUIRED)\n"
        "add_library(gflags::gflags UNKNOWN IMPORTED)\n"
        "set_target_properties(gflags::gflags PROPERTIES IMPORTED_LOCATION "
        '"${gflags_LIBRARY_FILE}")\n'
        "add_library(glog::glog UNKNOWN IMPORTED)\n"
        "set_target_properties(glog::glog PROPERTIES IMPORTED_LOCATION "
        '"${glog_LIBRARY_FILE}")\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            "cmake",
            "-S", str(source),
            "-B", str(build),
            f"-DCMAKE_PROJECT_INCLUDE={probe}",
            f"-DCMAKE_PREFIX_PATH={effective}",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    assert driver._linked_dependency_contract(
        str(build), deps_record
    ) == {
        "gflags_LIBRARY_FILE": str(
            (gflags / "lib/libgflags.so").resolve()
        ),
        "glog_LIBRARY_FILE": str((glog / "lib/libglog.so").resolve()),
    }


def test_verify_preserves_complete_integrity_dict(monkeypatch, tmp_path):
    integrity = {
        "clean": False,
        "orphan_reads": 1,
        "version_dups": 2,
        "dup_txids": 3,
        "genesis_commits": 4,
        "missing_txids": 5,
        "write_version_mismatch": 6,
        "malformed_keys": 7,
        "framing_violations": 8,
        "lock_coverage_violations": 9,
        "write_intent_violations": 10,
        "permutation_violations": 11,
        "notes": ["independent-note"],
    }
    verifier_payload = {
        "results": [{
            "verdict": "indeterminate",
            "certified": False,
            "serializable": True,
            "total_cycles": 0,
            "stats": {"txns": 2, "reads": 3, "writes": 4},
            "integrity": integrity,
        }],
    }
    monkeypatch.setattr(
        driver.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 3, json.dumps(verifier_payload), ""
        ),
    )

    result = driver._verify(str(tmp_path))

    assert result["integrity"] == integrity
    assert "write_intent_violations" not in {
        name for name in result if name != "integrity"
    }


def test_payload_records_semantics_links_limitations_and_no_stdout_counts():
    linked = {
        "gflags_LIBRARY_FILE": "/deps/gflags/lib/libgflags.a",
        "glog_LIBRARY_FILE": "/deps/glog/lib/libglog.a",
    }
    payload = driver._make_payload(
        sha="a" * 40,
        cc_record={"realpath": "/usr/bin/gcc", "version": "gcc test"},
        cxx_record={"realpath": "/usr/bin/g++", "version": "g++ test"},
        deps_record={"cmake_prefix_path": ["/deps/gflags", "/deps/glog"]},
        linked_dependencies=linked,
        jobs=3,
        runs=_passing_results(),
    )

    assert payload["runs_meta"] == {
        "cmake_cache_linked_dependencies": linked,
        "performance_semantics": (
            "none (trace-enabled correctness run; counts must not be compared "
            "as throughput)"
        ),
    }
    assert payload["build_admission"]["admission_status"] == "non-admissible"
    assert payload["known_limitations"] == [
        "delete_record cancel-previous-write mirroring is not exercised by this "
        "characterization: BOMB does not execute update->delete for the same key "
        "in the same transaction; detection-coverage claims exclude it.",
        "patchharness internal git subprocesses have no timeout (existing shared "
        "infrastructure behavior).",
    ]
    for run in payload["runs"].values():
        assert "stdout_counts" not in run
        assert type(run["abort_exercised"]) is bool


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
