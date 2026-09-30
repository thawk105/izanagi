# -*- coding: utf-8 -*-
"""Synthetic-repository tests for the TRACE=0 normalized-preprocess/include-activity checker."""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from orchestrator.campaign import source_digest

_ROOT = Path(__file__).resolve().parents[2]
_CHECKER = _ROOT / "tools/check_trace0_preprocess_identity.py"
_SOURCE = Path("cc/silo/transaction.cc")
_MOCC_SOURCE = Path("cc/mocc/transaction.cc")
_CICADA_SOURCE = Path("cc/cicada/transaction.cc")
_EXTRA_SOURCE = Path("cc/silo/extra.cpp")
_MOCC_TRACE_INCLUDE = '#include "../../include/trace.hh"'
_GUARANTEE = (
    "選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、"
    "および include 活性の同一性"
)
_OPTIONS = """\
set(CCBENCH_BACK_OFF 0 CACHE STRING "test")
set(CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION 1 CACHE STRING "test")
set(CCBENCH_NO_WAIT_OF_TICTOC 0 CACHE STRING "test")
set(CCBENCH_WAL 0 CACHE STRING "test")
set(CCBENCH_TRACE 0 CACHE STRING "test")
set(CCBENCH_TEMPERATURE_RESET_OPT 1 CACHE STRING "test")
set(CCBENCH_INLINE_VERSION_OPT_CICADA 0 CACHE STRING "test")
set(CCBENCH_INLINE_VERSION_PROMOTION 1 CACHE STRING "test")
set(CCBENCH_SINGLE_EXEC 0 CACHE STRING "test")
set(CCBENCH_WORKER1_INSERT_DELAY_RPHASE 0 CACHE STRING "test")
function(ccbench_universal_definitions target)
  target_compile_definitions(${target} PRIVATE
    BACK_OFF=${CCBENCH_BACK_OFF}
    NO_WAIT_LOCKING_IN_VALIDATION=${CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION}
    NO_WAIT_OF_TICTOC=${CCBENCH_NO_WAIT_OF_TICTOC}
    WAL=${CCBENCH_WAL}
    TRACE=${CCBENCH_TRACE})
endfunction()
"""
_OLD_SOURCE = """\
#include <cstdint>
#ifdef GLOBAL_VALUE_DEFINE
int context_value() { return 11; }
#else
int context_value() { return 12; }
#endif
#if TRACE
int trace_value() { return 1; }
#endif
int steady_value() { return 7; }
"""
_TRACE_ONLY_NEW_SOURCE = _OLD_SOURCE.replace(
    "int trace_value() { return 1; }", "int trace_value() { return 2; }"
)
_MOCC_OWNER_CMAKE = """\
ccbench_add_protocol(mocc
  SOURCES transaction.cc
  WORKLOADS ycsb
  OPTIONS RWLOCK TEMPERATURE_RESET_OPT=${CCBENCH_TEMPERATURE_RESET_OPT})
"""
_CICADA_OWNER_CMAKE = """\
ccbench_add_protocol(cicada
  SOURCES transaction.cc
  WORKLOADS ycsb
  OPTIONS INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_CICADA}
          INLINE_VERSION_PROMOTION=${CCBENCH_INLINE_VERSION_PROMOTION}
          SINGLE_EXEC=${CCBENCH_SINGLE_EXEC}
          WORKER1_INSERT_DELAY_RPHASE=${CCBENCH_WORKER1_INSERT_DELAY_RPHASE})
"""
_CICADA_MACROS = (
    "INLINE_VERSION_OPT", "INLINE_VERSION_PROMOTION", "SINGLE_EXEC",
    "WORKER1_INSERT_DELAY_RPHASE",
)
_MQLOCK_OLD_SOURCE = """\
#include <cstdint>
#ifdef MQLOCK
int mqlock_value() { return 1; }
#endif
#if TRACE
int trace_value() { return 1; }
#endif
int steady_value() { return 7; }
"""
_MQLOCK_NEW_SOURCE = _MQLOCK_OLD_SOURCE.replace(
    "int trace_value() { return 1; }", "int trace_value() { return 2; }"
)


@dataclass(frozen=True)
class _Pair:
    repo: Path
    old: str
    new: str


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", os.fspath(repo), *args], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed rc={result.returncode}: {result.stderr}"
    )
    return result.stdout.strip()


def _write(repo: Path, rel: str | Path, content: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)
    oid = _git(repo, "rev-parse", "HEAD")
    assert len(oid) == 40 and oid == oid.lower()
    return oid


def _base_repo(
    tmp_path: Path,
    source: str = _OLD_SOURCE,
    *,
    source_rel: Path = _SOURCE,
    protocol_cmake_text: str = "# synthetic protocol file\n",
    write_owner_cmake: bool = True,
) -> tuple[Path, str]:
    repo = tmp_path / "ccbench"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Izanagi Test")
    _git(repo, "config", "user.email", "izanagi-test@example.invalid")
    _write(repo, "cmake/Options.cmake", _OPTIONS)
    _write(repo, "cc/silo/CMakeLists.txt", "# synthetic protocol file\n")
    owner_cmake_path = source_rel.parent / "CMakeLists.txt"
    if write_owner_cmake and owner_cmake_path != Path("cc/silo/CMakeLists.txt"):
        _write(repo, owner_cmake_path, protocol_cmake_text)
    _write(repo, source_rel, source)
    return repo, _commit(repo, "old")


def _modified_pair(tmp_path: Path, new_source: str, *, old_source: str = _OLD_SOURCE) -> _Pair:
    repo, old = _base_repo(tmp_path, old_source)
    _write(repo, _SOURCE, new_source)
    new = _commit(repo, "new")
    _git(repo, "checkout", "-q", "--detach", old)
    assert (repo / _SOURCE).read_text(encoding="utf-8") == old_source
    return _Pair(repo, old, new)


def _mocc_modified_pair(
    tmp_path: Path,
    new_source: str,
    *,
    old_source: str = _OLD_SOURCE,
    protocol_cmake_text: str = "# synthetic protocol file\n",
    write_owner_cmake: bool = True,
) -> _Pair:
    repo, old = _base_repo(
        tmp_path,
        old_source,
        source_rel=_MOCC_SOURCE,
        protocol_cmake_text=protocol_cmake_text,
        write_owner_cmake=write_owner_cmake,
    )
    _write(repo, _MOCC_SOURCE, new_source)
    new = _commit(repo, "new")
    _git(repo, "checkout", "-q", "--detach", old)
    assert (repo / _MOCC_SOURCE).read_text(encoding="utf-8") == old_source
    return _Pair(repo, old, new)


def _cicada_modified_pair(tmp_path: Path, new_source: str, *, old_source: str = _OLD_SOURCE) -> _Pair:
    repo, old = _base_repo(
        tmp_path, old_source, source_rel=_CICADA_SOURCE,
        protocol_cmake_text=_CICADA_OWNER_CMAKE,
    )
    _write(repo, _CICADA_SOURCE, new_source)
    new = _commit(repo, "new")
    return _Pair(repo, old, new)


def _cxx() -> str:
    compiler = shutil.which("g++") or shutil.which("g++-12") or shutil.which("g++-11")
    assert compiler is not None, "checker tests require a C++ preprocessor"
    return compiler


def _run(
    pair: _Pair,
    *,
    old: str | None = None,
    new: str | None = None,
    cxx: str | None = None,
    include_cxx: bool = True,
    expect_paths: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        os.fspath(_CHECKER),
        "--repo", os.fspath(pair.repo),
        "--old", old or pair.old,
        "--new", new or pair.new,
    ]
    if include_cxx:
        args += ["--cxx", cxx or _cxx()]
    if expect_paths is not None:
        args += ["--expect-paths", *expect_paths]
    return subprocess.run(args, cwd=_ROOT, capture_output=True, text=True)


def _assert_rejected(result: subprocess.CompletedProcess[str], message: str) -> None:
    assert result.returncode != 0
    assert result.stdout == ""
    assert _GUARANTEE in result.stderr
    assert message in result.stderr


def _two_source_pair(tmp_path: Path, extra_new: str) -> _Pair:
    extra_old = "#if TRACE\nint extra_trace = 1;\n#endif\nint extra_steady = 3;\n"
    repo, _initial = _base_repo(tmp_path)
    _write(repo, _EXTRA_SOURCE, extra_old)
    old = _commit(repo, "old with extra source")
    _write(repo, _SOURCE, _TRACE_ONLY_NEW_SOURCE)
    _write(repo, _EXTRA_SOURCE, extra_new)
    new = _commit(repo, "new with two modified sources")
    return _Pair(repo, old, new)


def _load_checker_module():
    spec = importlib.util.spec_from_file_location("trace0_checker_under_test", _CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_trace_only_change_passes_with_deterministic_required_evidence(tmp_path: Path) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    first = _run(pair)
    second = _run(pair)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout

    report = json.loads(first.stdout)
    assert report["schema"] == "izanagi-trace0-preprocess-identity/v2"
    assert report["guarantee"] == _GUARANTEE
    assert report["result"] == "pass"
    assert report["repo"] == os.fspath(pair.repo.resolve())
    assert report["old_oid"] == pair.old
    assert report["new_oid"] == pair.new
    assert report["old_is_ancestor_of_new"] is True
    assert report["expected_paths"] is None
    assert report["context_matrix"] == {
        "genome_count": 8,
        "overlay_count": 2,
        "expected_context_count_per_file": 16,
    }
    assert report["expected_context_count_by_path"] == {_SOURCE.as_posix(): 16}
    assert [(entry["status"], entry["path"]) for entry in report["diff"]] == [
        ("M", _SOURCE.as_posix())
    ]
    assert Path(report["compiler"]["path"]).is_absolute()
    assert report["compiler"]["version"]
    assert len(report["files"]) == 1
    file_evidence = report["files"][0]
    assert file_evidence["path"] == _SOURCE.as_posix()
    assert file_evidence["include_line_count"] == 1
    assert len(file_evidence["include_lines_sha256"]) == 64
    assert file_evidence["result"] == "match"
    assert len(file_evidence["contexts"]) == 16
    assert {item["context"] for item in file_evidence["contexts"]} == {
        "base", "GLOBAL_VALUE_DEFINE=1"
    }
    assert len({item["genome"] for item in file_evidence["contexts"]}) == 8
    for context in file_evidence["contexts"]:
        normalized = context["normalized_preprocess"]
        activity = context["include_activity"]
        assert context["defines"]["old"]["TRACE"] == "0"
        assert context["defines"]["new"]["TRACE"] == "0"
        assert context["defines"]["old"] == context["defines"]["new"]
        assert normalized["identical"] is True
        assert normalized["old_sha256"] == normalized["new_sha256"]
        assert len(normalized["old_sha256"]) == 64
        assert activity["identical"] is True
        assert activity["old_sha256"] == activity["new_sha256"]
        assert activity["old_active_markers"] == ["IZANAGI_TRACE0_INCLUDE_MARKER_00000000"]
        assert activity["new_active_markers"] == ["IZANAGI_TRACE0_INCLUDE_MARKER_00000000"]


def test_trace_output_outside_trace_branch_is_rejected(tmp_path: Path) -> None:
    pair = _modified_pair(tmp_path, _OLD_SOURCE + "int leaked_trace_output = 1;\n")
    _assert_rejected(_run(pair), "TRACE=0 正規化 preprocess 出力が不一致")


def test_cicada_trace_only_change_covers_exact_binary_matrix(tmp_path: Path) -> None:
    new = _OLD_SOURCE.replace("#if TRACE\n", "#if TRACE\n// trace-only comment\n")
    pair = _cicada_modified_pair(tmp_path, new)
    result = _run(pair)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    evidence = report["files"][0]
    assert evidence["path"] == _CICADA_SOURCE.as_posix()
    assert evidence["expected_context_count"] == evidence["actual_context_count"] == 32
    assert report["expected_context_count_by_path"][_CICADA_SOURCE.as_posix()] == 32
    contexts = evidence["contexts"]
    assert len(contexts) == 32
    assert (
        "INLINE_VERSION_OPT=0,INLINE_VERSION_PROMOTION=1,SINGLE_EXEC=0,"
        "WORKER1_INSERT_DELAY_RPHASE=0;base"
    ) in {context["context"] for context in contexts}
    actual = [
        (tuple(context["defines"]["old"][name] for name in _CICADA_MACROS),
         tuple(sorted(context["overlay"].items())))
        for context in contexts
    ]
    expected = [
        (values, tuple(sorted(overlay.items())))
        for values in itertools.product("01", repeat=4)
        for overlay in ({}, {"GLOBAL_VALUE_DEFINE": "1"})
    ]
    assert sorted(actual) == sorted(expected)
    assert (("0", "1", "0", "0"), ()) in actual
    assert all(c["defines"]["old"] == c["defines"]["new"] for c in contexts)


@pytest.mark.parametrize(
    ("condition", "name"),
    [
        ("SINGLE_EXEC", "single_exec"),
        ("WORKER1_INSERT_DELAY_RPHASE", "worker_delay"),
        ("INLINE_VERSION_OPT", "inline_opt"),
        ("INLINE_VERSION_OPT && !INLINE_VERSION_PROMOTION", "promotion"),
    ],
)
def test_cicada_opposite_default_branch_is_rejected(
    tmp_path: Path, condition: str, name: str,
) -> None:
    old = _OLD_SOURCE + f"#if {condition}\nint {name} = 1;\n#endif\n"
    new = old.replace(f"int {name} = 1;", f"int {name} = 2;")
    result = _run(_cicada_modified_pair(tmp_path, new, old_source=old))
    _assert_rejected(result, "TRACE=0 正規化 preprocess 出力が不一致")
    if name == "single_exec":
        assert (
            "INLINE_VERSION_OPT=0,INLINE_VERSION_PROMOTION=0,SINGLE_EXEC=1,"
            "WORKER1_INSERT_DELAY_RPHASE=0"
        ) in result.stderr


def test_cicada_unknown_macro_remains_rejected(tmp_path: Path) -> None:
    pair = _cicada_modified_pair(
        tmp_path, _OLD_SOURCE + "#if NEW_CICADA_MACRO\nint hidden = 1;\n#endif\n"
    )
    _assert_rejected(_run(pair), "未知マクロ")


def test_cicada_include_activity_error_identifies_values(tmp_path: Path) -> None:
    old = "#include <required.hh>\n#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    new = "#if TRACE\n#include <required.hh>\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    result = _run(_cicada_modified_pair(tmp_path, new, old_source=old))
    _assert_rejected(result, "include 活性（順序込み）が不一致")
    assert (
        "INLINE_VERSION_OPT=0,INLINE_VERSION_PROMOTION=0,SINGLE_EXEC=0,"
        "WORKER1_INSERT_DELAY_RPHASE=0"
    ) in result.stderr


def test_cicada_comparison_count_cannot_be_derived_from_actual(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    new = _OLD_SOURCE.replace("#if TRACE\n", "#if TRACE\n// trace-only comment\n")
    pair = _cicada_modified_pair(tmp_path, new)
    checker = _load_checker_module()
    original = checker._compare_file

    def compare_with_one_fewer_overlay(
        repo, old_oid, new_oid, path, compiler, old_known_absent,
        new_known_absent, genomes, overlays, expected_context_count,
    ):
        return original(
            repo, old_oid, new_oid, path, compiler, old_known_absent,
            new_known_absent, genomes, overlays[:-1], expected_context_count,
        )

    monkeypatch.setattr(checker, "_compare_file", compare_with_one_fewer_overlay)
    with pytest.raises(checker.CheckError, match="context 比較件数が列挙元から導出した期待数と一致しない"):
        checker.check(pair.repo, pair.old, pair.new, _cxx())


def test_mocc_trace_include_addition_passes_with_expected_path(tmp_path: Path) -> None:
    new = _OLD_SOURCE.replace("#if TRACE\n", f"#if TRACE\n{_MOCC_TRACE_INCLUDE}\n", 1)
    pair = _mocc_modified_pair(tmp_path, new)
    result = _run(pair, expect_paths=[_MOCC_SOURCE.as_posix()])
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["expected_paths"] == [_MOCC_SOURCE.as_posix()]
    assert report["files"][0]["path"] == _MOCC_SOURCE.as_posix()
    assert report["files"][0]["include_line_count"] == 1


def test_registered_mocc_source_uses_owner_protocol_defines(tmp_path: Path) -> None:
    old_source = """\
#if RWLOCK
int rwlock_enabled = 1;
#endif
#if TEMPERATURE_RESET_OPT
int temperature_reset_enabled = 1;
#endif
#if TRACE
int trace_value = 1;
#endif
int steady_value = 7;
"""
    new_source = old_source.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _mocc_modified_pair(
        tmp_path,
        new_source,
        old_source=old_source,
        protocol_cmake_text=_MOCC_OWNER_CMAKE,
    )
    result = _run(pair, expect_paths=[_MOCC_SOURCE.as_posix()])
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    contexts = report["files"][0]["contexts"]
    assert contexts
    for context in contexts:
        assert context["defines"]["old"]["RWLOCK"] == "1"
        assert context["defines"]["new"]["RWLOCK"] == "1"
        assert context["defines"]["old"]["TEMPERATURE_RESET_OPT"] == "1"
        assert context["defines"]["new"]["TEMPERATURE_RESET_OPT"] == "1"


def test_unregistered_cpp_source_keeps_genome_protocol_defines(tmp_path: Path) -> None:
    repo, old = _base_repo(tmp_path, _OLD_SOURCE, source_rel=_EXTRA_SOURCE)
    _write(repo, _EXTRA_SOURCE, _TRACE_ONLY_NEW_SOURCE)
    new = _commit(repo, "new")
    pair = _Pair(repo, old, new)
    result = _run(pair, expect_paths=[_EXTRA_SOURCE.as_posix()])
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["files"][0]["path"] == _EXTRA_SOURCE.as_posix()


def test_registered_source_owner_cmake_failure_is_not_downgraded(
    tmp_path: Path,
) -> None:
    pair = _mocc_modified_pair(
        tmp_path,
        _TRACE_ONLY_NEW_SOURCE,
        write_owner_cmake=False,
    )
    _assert_rejected(_run(pair), "cc/mocc/CMakeLists.txt")


def test_trace_include_addition_is_rejected_for_non_mocc_path(tmp_path: Path) -> None:
    new = _OLD_SOURCE.replace("#if TRACE\n", f"#if TRACE\n{_MOCC_TRACE_INCLUDE}\n", 1)
    pair = _modified_pair(tmp_path, new)
    _assert_rejected(_run(pair), "include 行文字列（順序込み）が不一致")


def test_mocc_trace_include_without_trace_guard_is_rejected(tmp_path: Path) -> None:
    pair = _mocc_modified_pair(tmp_path, f"{_MOCC_TRACE_INCLUDE}\n{_OLD_SOURCE}")
    _assert_rejected(_run(pair), "include 行文字列（順序込み）が不一致")


def test_mocc_trace_include_addition_cannot_hide_another_include(tmp_path: Path) -> None:
    new = _OLD_SOURCE.replace(
        "#if TRACE\n",
        f"#if TRACE\n#include \"other.hh\"\n{_MOCC_TRACE_INCLUDE}\n",
        1,
    )
    pair = _mocc_modified_pair(tmp_path, new)
    _assert_rejected(_run(pair), "include 行文字列（順序込み）が不一致")


def test_ifdef_trace_is_rejected_when_trace_is_explicitly_zero(tmp_path: Path) -> None:
    old = "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    new = "#ifdef TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "TRACE=0 正規化 preprocess 出力が不一致")


def test_include_moved_inside_trace_branch_is_rejected_by_activity(tmp_path: Path) -> None:
    old = "#include <required.hh>\n#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    new = "#if TRACE\n#include <required.hh>\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "include 活性（順序込み）が不一致")


def test_every_modified_cpp_source_is_checked_without_expected_paths(tmp_path: Path) -> None:
    extra_new = "#if TRACE\nint extra_trace = 2;\n#endif\nint extra_steady = 99;\n"
    pair = _two_source_pair(tmp_path, extra_new)
    result = _run(pair)
    _assert_rejected(result, "TRACE=0 正規化 preprocess 出力が不一致")
    assert _EXTRA_SOURCE.as_posix() in result.stderr


def test_expected_paths_match_is_order_independent_and_recorded(tmp_path: Path) -> None:
    extra_new = "#if TRACE\nint extra_trace = 2;\n#endif\nint extra_steady = 3;\n"
    pair = _two_source_pair(tmp_path, extra_new)
    expected = [_SOURCE.as_posix(), _EXTRA_SOURCE.as_posix()]
    result = _run(pair, expect_paths=expected)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["expected_paths"] == sorted(expected)
    assert {item["path"] for item in report["files"]} == set(expected)


def test_known_absent_is_rejected_from_comparison_commit_tree(tmp_path: Path) -> None:
    repo, checkout_oid = _base_repo(tmp_path, _MQLOCK_OLD_SOURCE)
    _write(repo, "include/mqlock_supply.hh", "#define MQLOCK 1\n")
    old = _commit(repo, "comparison old with supply")
    _write(repo, _SOURCE, _MQLOCK_NEW_SOURCE)
    new = _commit(repo, "comparison new with supply")
    _git(repo, "checkout", "-q", "--detach", checkout_oid)
    assert _git(repo, "diff", "--name-only", old, new) == _SOURCE.as_posix()
    _assert_rejected(
        _run(_Pair(repo, old, new)),
        "PROVEN_REPO_ABSENT_MACROS が stale",
    )


def test_known_absent_is_rejected_from_checkout_when_commit_is_specified(
    tmp_path: Path,
) -> None:
    pair = _modified_pair(tmp_path, _MQLOCK_NEW_SOURCE, old_source=_MQLOCK_OLD_SOURCE)
    _write(pair.repo, "include/checkout-only-supply.hh", "#define MQLOCK 1\n")
    for commit in (pair.old, pair.new):
        assert "include/checkout-only-supply.hh" not in _git(
            pair.repo, "ls-tree", "-r", "--name-only", commit
        ).splitlines()
    _assert_rejected(
        _run(pair),
        "PROVEN_REPO_ABSENT_MACROS が stale",
    )


def test_known_absent_old_only_supply_is_rejected_from_old_commit(
    tmp_path: Path,
) -> None:
    repo, checkout_oid = _base_repo(tmp_path, _MQLOCK_OLD_SOURCE)
    _write(repo, _SOURCE, _MQLOCK_OLD_SOURCE + "#define MQLOCK 1\n")
    old = _commit(repo, "comparison old with supply")
    _write(repo, _SOURCE, _MQLOCK_NEW_SOURCE)
    new = _commit(repo, "comparison new without supply")
    _git(repo, "checkout", "-q", "--detach", checkout_oid)
    assert _git(repo, "diff", "--name-only", old, new) == _SOURCE.as_posix()
    _assert_rejected(
        _run(_Pair(repo, old, new)),
        "PROVEN_REPO_ABSENT_MACROS が stale",
    )


def test_known_absent_new_only_supply_is_rejected_from_new_commit(
    tmp_path: Path,
) -> None:
    repo, old = _base_repo(tmp_path, _MQLOCK_OLD_SOURCE)
    _write(repo, _SOURCE, _MQLOCK_NEW_SOURCE + "#define MQLOCK 1\n")
    new = _commit(repo, "comparison new with supply")
    _git(repo, "checkout", "-q", "--detach", old)
    assert _git(repo, "diff", "--name-only", old, new) == _SOURCE.as_posix()
    _assert_rejected(
        _run(_Pair(repo, old, new)),
        "PROVEN_REPO_ABSENT_MACROS が stale",
    )


def test_known_absent_validation_receives_both_comparison_oids_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    checker = _load_checker_module()
    calls: list[tuple[str, str | None]] = []

    def record_absence(repo: str = "", *, commit: str | None = None) -> frozenset[str]:
        calls.append((repo, commit))
        return frozenset({"MQLOCK"})

    monkeypatch.setattr(checker, "_assert_proven_repo_absent_macros", record_absence)
    report = checker.check(pair.repo, pair.old, pair.new, _cxx())
    assert report["result"] == "pass"
    assert calls == [
        (os.fspath(pair.repo.resolve()), pair.old),
        (os.fspath(pair.repo.resolve()), pair.new),
    ]


def test_commit_tree_symlink_entry_is_rejected(tmp_path: Path) -> None:
    repo, _initial = _base_repo(tmp_path)
    (repo / "include").mkdir()
    os.symlink("../cc/silo/transaction.cc", repo / "include/supply-link.hh")
    old = _commit(repo, "comparison old with symlink")
    _write(repo, _SOURCE, _TRACE_ONLY_NEW_SOURCE)
    new = _commit(repo, "comparison new with symlink")
    assert _git(repo, "diff", "--name-only", old, new) == _SOURCE.as_posix()
    _assert_rejected(_run(_Pair(repo, old, new)), "symlink entry")


def test_checkout_walk_directory_enumeration_error_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _old = _base_repo(tmp_path)
    walk_error = PermissionError(13, "permission denied", os.fspath(repo / "blocked"))

    def failing_walk(_root: str, *, onerror=None):
        assert onerror is not None
        onerror(walk_error)
        yield "", [], []

    monkeypatch.setattr(source_digest.os, "walk", failing_walk)
    with pytest.raises(RuntimeError, match="checkout directory の列挙に失敗"):
        list(source_digest._repo_supply_files(os.fspath(repo)))


def test_uninitialized_gitlink_directory_is_not_asked_to_resolve_parent_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _old = _base_repo(tmp_path)
    (repo / "third_party/fixture").mkdir(parents=True)

    def reject_git_call(*_args, **_kwargs):
        raise AssertionError("non-repository gitlink directory must not invoke git")

    monkeypatch.setattr(source_digest.subprocess, "run", reject_git_call)
    assert source_digest._checkout_gitlink_oid(
        os.fspath(repo), "third_party/fixture"
    ) is None


def test_commit_tree_with_matching_initialized_gitlink_is_accepted(
    tmp_path: Path,
) -> None:
    child = tmp_path / "gitlink-source"
    child.mkdir()
    _git(child, "init", "-q")
    _git(child, "config", "user.name", "Izanagi Test")
    _git(child, "config", "user.email", "izanagi-test@example.invalid")
    _write(child, "include/fixture.hh", "#pragma once\n")
    child_oid = _commit(child, "gitlink source")

    repo, _initial = _base_repo(tmp_path)
    _git(
        repo,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-q",
        os.fspath(child),
        "third_party/fixture",
    )
    assert _git(repo / "third_party/fixture", "rev-parse", "HEAD") == child_oid
    old = _commit(repo, "comparison old with gitlink")
    _write(repo, _SOURCE, _TRACE_ONLY_NEW_SOURCE)
    new = _commit(repo, "comparison new with gitlink")
    assert _git(repo, "diff", "--name-only", old, new) == _SOURCE.as_posix()
    result = _run(_Pair(repo, old, new))
    assert result.returncode == 0, result.stderr


def test_commit_tree_with_uninitialized_gitlink_worktree_is_accepted(
    tmp_path: Path,
) -> None:
    """親裁定により、計算 job と同じ未初期化 gitlink は coverage 対象外として通す。"""
    child = tmp_path / "gitlink-source"
    child.mkdir()
    _git(child, "init", "-q")
    _git(child, "config", "user.name", "Izanagi Test")
    _git(child, "config", "user.email", "izanagi-test@example.invalid")
    _write(child, "include/fixture.hh", "#pragma once\n")
    _commit(child, "gitlink source")

    repo, _initial = _base_repo(tmp_path)
    _git(
        repo,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-q",
        os.fspath(child),
        "third_party/fixture",
    )
    old = _commit(repo, "comparison old with gitlink")
    _write(repo, _SOURCE, _TRACE_ONLY_NEW_SOURCE)
    new = _commit(repo, "comparison new with gitlink")

    detached = tmp_path / "detached-checkout"
    _git(repo, "worktree", "add", "-q", "--detach", os.fspath(detached), new)
    gitlink_checkout = detached / "third_party/fixture"
    gitlink_checkout.mkdir(parents=True, exist_ok=True)
    assert gitlink_checkout.is_dir()
    assert not (gitlink_checkout / ".git").exists()
    assert _git(detached, "rev-parse", "HEAD") == new

    result = _run(_Pair(detached, old, new))
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "expected",
    [
        [_SOURCE.as_posix()],
        [_SOURCE.as_posix(), _EXTRA_SOURCE.as_posix(), "cc/silo/missing.cpp"],
    ],
)
def test_expected_paths_rejects_actual_or_expected_superset(
    tmp_path: Path, expected: list[str]
) -> None:
    extra_new = "#if TRACE\nint extra_trace = 2;\n#endif\nint extra_steady = 3;\n"
    pair = _two_source_pair(tmp_path, extra_new)
    _assert_rejected(
        _run(pair, expect_paths=expected),
        "diff path 集合が --expect-paths と厳密一致しない",
    )


def test_expected_paths_rejects_duplicates(tmp_path: Path) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    duplicate = [_SOURCE.as_posix(), _SOURCE.as_posix()]
    _assert_rejected(_run(pair, expect_paths=duplicate), "--expect-paths に重複 path")


def test_help_documents_expected_paths_exact_set_contract() -> None:
    result = subprocess.run(
        [sys.executable, os.fspath(_CHECKER), "--help"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--expect-paths PATH [PATH ...]" in result.stdout
    assert "順不同で厳密一致" in result.stdout


@pytest.mark.parametrize("suffix", [".h", ".hh", ".hpp", ".hxx", ".ipp"])
def test_modified_header_is_rejected_as_outside_checker_guarantee(
    tmp_path: Path, suffix: str
) -> None:
    header = Path(f"cc/silo/consumer{suffix}")
    repo, old = _base_repo(tmp_path, "#define VALUE 1\n", source_rel=header)
    _write(repo, header, "#define VALUE 2\n")
    new = _commit(repo, "modify header")
    _assert_rejected(
        _run(_Pair(repo, old, new)),
        "header の変更は consumer TU での解析が必要であり、この checker の保証範囲外なので "
        "fail-closed で拒否する",
    )


def test_empty_context_enumeration_is_rejected_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    checker = _load_checker_module()
    monkeypatch.setattr(checker.SILO_SPACE, "enumerate", lambda: [])
    with pytest.raises(checker.CheckError, match="context 列挙が空で比較 0 件"):
        checker.check(pair.repo, pair.old, pair.new, _cxx())


def test_context_count_mismatch_is_rejected_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    checker = _load_checker_module()
    compare_file = checker._compare_file

    def compare_with_one_fewer_genome(
        repo,
        old_oid,
        new_oid,
        path,
        compiler,
        old_known_absent,
        new_known_absent,
        genomes,
        overlays,
        expected_context_count,
    ):
        assert expected_context_count > 0
        assert len(genomes) > 1
        return compare_file(
            repo,
            old_oid,
            new_oid,
            path,
            compiler,
            old_known_absent,
            new_known_absent,
            genomes[:-1],
            overlays,
            expected_context_count,
        )

    monkeypatch.setattr(checker, "_compare_file", compare_with_one_fewer_genome)
    with pytest.raises(
        checker.CheckError,
        match="context 比較件数が列挙元から導出した期待数と一致しない",
    ):
        checker.check(pair.repo, pair.old, pair.new, _cxx())


def test_old_and_new_digests_are_computed_by_independent_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker_module()
    calls: list[bytes] = []

    def fake_sha256(value: bytes) -> str:
        calls.append(value)
        return f"digest-{len(calls)}"

    monkeypatch.setattr(checker, "_sha256", fake_sha256)
    assert checker._independent_sha256_pair(b"same", b"same") == (
        "digest-1",
        "digest-2",
    )
    assert calls == [b"same", b"same"]


@pytest.mark.parametrize("operation", ["add", "delete", "rename"])
def test_add_delete_and_rename_are_rejected_as_unsupported_status(
    tmp_path: Path, operation: str
) -> None:
    """この gate は blob 取得でも拒否される冗長 gate で、単独変異の kill 証拠には使えない。"""
    repo, old = _base_repo(tmp_path)
    if operation == "add":
        _write(repo, "cc/silo/extra.hh", "int extra = 1;\n")
    elif operation == "delete":
        (repo / _SOURCE).unlink()
    else:
        (repo / _SOURCE).rename(repo / "cc/silo/renamed.cc")
    new = _commit(repo, operation)
    pair = _Pair(repo, old, new)
    _assert_rejected(_run(pair), "未対応の diff status")


def test_mode_change_is_rejected(tmp_path: Path) -> None:
    repo, old = _base_repo(tmp_path)
    _git(repo, "update-index", "--chmod=+x", _SOURCE.as_posix())
    _git(repo, "commit", "-qm", "mode")
    new = _git(repo, "rev-parse", "HEAD")
    _assert_rejected(_run(_Pair(repo, old, new)), "mode/type change は未対応")


def test_non_cpp_changed_path_is_rejected(tmp_path: Path) -> None:
    """この gate は preprocess 不一致でも拒否される冗長 gate で、単独変異の kill 証拠には使えない。"""
    repo, old = _base_repo(tmp_path, "old text\n", source_rel=Path("notes.txt"))
    _write(repo, "notes.txt", "new text\n")
    new = _commit(repo, "new text")
    _assert_rejected(_run(_Pair(repo, old, new)), "C/C++ regular source/header 以外")


def test_preprocess_failure_is_not_downgraded_to_pass(tmp_path: Path) -> None:
    pair = _modified_pair(tmp_path, _OLD_SOURCE + "#if TRACE\nint unterminated = 1;\n")
    _assert_rejected(_run(pair), "preprocess 失敗")


def test_nonexistent_compiler_is_rejected(tmp_path: Path) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    missing = os.fspath(tmp_path / "compiler-does-not-exist")
    _assert_rejected(_run(pair, cxx=missing), "compiler が存在しない")


def test_missing_required_cxx_argument_is_rejected(tmp_path: Path) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    _assert_rejected(_run(pair, include_cxx=False), "--cxx")


def test_same_commit_empty_diff_is_rejected(tmp_path: Path) -> None:
    """この gate は対象 0 件を二重に拒否する冗長 gate で、単独変異の kill 証拠には使えない。"""
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    _assert_rejected(_run(pair, old=pair.old, new=pair.old), "差分が空で対象 0 件")


@pytest.mark.parametrize("bad_ref", ["short", "symbolic"])
def test_short_sha_and_symbolic_ref_are_rejected(tmp_path: Path, bad_ref: str) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    old = pair.old[:12] if bad_ref == "short" else "HEAD"
    _assert_rejected(_run(pair, old=old), "40 桁 lowercase hex commit OID")


def test_missing_commit_object_is_rejected(tmp_path: Path) -> None:
    pair = _modified_pair(tmp_path, _TRACE_ONLY_NEW_SOURCE)
    _assert_rejected(_run(pair, new="f" * 40), "rev-parse --verify")


def test_nonancestor_commit_relation_is_rejected(tmp_path: Path) -> None:
    repo, base = _base_repo(tmp_path)
    _write(repo, _SOURCE, _TRACE_ONLY_NEW_SOURCE)
    left = _commit(repo, "left")
    _git(repo, "checkout", "-q", "--detach", base)
    sibling = _OLD_SOURCE.replace("int trace_value() { return 1; }", "int trace_value() { return 3; }")
    _write(repo, _SOURCE, sibling)
    right = _commit(repo, "right")
    _assert_rejected(_run(_Pair(repo, left, right)), "old commit は new commit の祖先でない")


def test_include_line_spelling_change_is_rejected(tmp_path: Path) -> None:
    new = _TRACE_ONLY_NEW_SOURCE.replace("#include <cstdint>", "#include <cstdlib>")
    pair = _modified_pair(tmp_path, new)
    _assert_rejected(_run(pair), "include 行文字列（順序込み）が不一致")


@pytest.mark.parametrize(
    ("new_tail", "message"),
    [
        ("#ifdef UNKNOWN_BUILD_MACRO\nint hidden = 1;\n#endif\n", "未知マクロ"),
        ("#if __has_include(<hidden.hh>)\nint hidden = 1;\n#endif\n", "__has_include"),
    ],
)
def test_existing_conditional_macro_guard_remains_fail_closed(
    tmp_path: Path, new_tail: str, message: str
) -> None:
    pair = _modified_pair(tmp_path, _OLD_SOURCE + new_tail)
    _assert_rejected(_run(pair), message)


def test_difference_visible_only_in_nonbase_context_is_rejected(tmp_path: Path) -> None:
    new = _OLD_SOURCE.replace(
        "int context_value() { return 11; }", "int context_value() { return 99; }"
    )
    pair = _modified_pair(tmp_path, new)
    result = _run(pair)
    _assert_rejected(result, "TRACE=0 正規化 preprocess 出力が不一致")
    assert "context='GLOBAL_VALUE_DEFINE=1'" in result.stderr


def test_comment_only_drift_outside_trace_is_accepted(tmp_path: Path) -> None:
    pair = _modified_pair(tmp_path, "// normalized-away drift control\n" + _OLD_SOURCE)
    result = _run(pair)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["result"] == "pass"


def test_known_absent_set_indirect_target_definition_is_rejected_from_new_commit_only(
    tmp_path: Path,
) -> None:
    repo, old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        "set(MODE MQLOCK)\ntarget_compile_definitions(silo PRIVATE ${MODE})\n",
    )
    new = _commit(repo, "new-only indirect supply")
    _git(repo, "checkout", "-q", "--detach", old)
    assert "MQLOCK" not in (repo / "cc/silo/CMakeLists.txt").read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo), commit=new)


def test_known_absent_set_indirect_cxx_flags_is_rejected_from_old_commit_only(
    tmp_path: Path,
) -> None:
    repo, _initial = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        'set(MODE MQLOCK)\nset(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D${MODE}")\n',
    )
    old = _commit(repo, "old-only indirect flags")
    _write(repo, "cc/silo/CMakeLists.txt", "# supply removed\n")
    _write(repo, _SOURCE, _TRACE_ONLY_NEW_SOURCE)
    _commit(repo, "new without supply")
    assert "MQLOCK" not in (repo / "cc/silo/CMakeLists.txt").read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo), commit=old)


def test_known_absent_string_concat_indirect_is_rejected(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        "string(CONCAT MODE MQ LOCK)\ntarget_compile_definitions(silo PRIVATE ${MODE})\n",
    )
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_known_absent_supply_hidden_by_cmake_bracket_argument_is_rejected(
    tmp_path: Path,
) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        'set(a [=[" ]=])\nset(MODE MQLOCK)\n'
        'target_compile_definitions(silo PRIVATE ${MODE})\nset(b [=[" ]=])\n',
    )
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_cmake_bracket_inside_quoted_argument_does_not_hide_supply(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        'set(CXX_ATTRIBUTE "[[maybe_unused]]")\n'
        'set(QUOTED_BRACKET_PREFIX "[[")\n'
        "target_compile_definitions(silo PRIVATE OTHER_MACRO)\n",
    )
    assert source_digest._assert_proven_repo_absent_macros(
        os.fspath(repo)
    ) == source_digest.PROVEN_REPO_ABSENT_MACROS


def test_known_absent_spliced_define_is_rejected_from_new_commit_only(
    tmp_path: Path,
) -> None:
    repo, old = _base_repo(tmp_path)
    _write(repo, "include/spliced.hh", "#defi\\\nne MQLOCK 1\n")
    new = _commit(repo, "new-only spliced define")
    _git(repo, "checkout", "-q", "--detach", old)
    assert not (repo / "include/spliced.hh").exists()
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo), commit=new)


def test_known_absent_define_after_raw_string_is_rejected(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "include/raw-string-supply.hh",
        'const char* text = R"tag(" /*\n)tag";\n#define MQLOCK 1\n// */\n',
    )
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_identifier_suffix_before_raw_opener_does_not_hide_define(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "include/raw-string-token-boundary.hh",
        '#define UNUSED fooR"(x"\n#define MQLOCK 1\nconst char *tail = ")";\n',
    )
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_bracket_payload_legacy_rejection_is_preserved(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        "set(DOC [[target_compile_definitions(t PRIVATE MQLOCK)]])\n",
    )
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


@pytest.mark.parametrize(
    "supply",
    [
        "\ufeff#define MQLOCK 1\n",
        "%:define MQLOCK 1\n",
    ],
)
def test_bom_or_digraph_define_is_rejected(tmp_path: Path, supply: str) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(repo, "include/alternate-directive.hh", supply)
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_duplicate_bom_supply_file_is_rejected_fail_closed(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(repo, "include/duplicate-bom.hh", "\ufeff\ufeff#define MQLOCK 1\n")
    with pytest.raises(RuntimeError, match="先頭 UTF-8 BOM が重複"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_set_property_compile_definitions_is_rejected(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        "set_property(TARGET bench PROPERTY COMPILE_DEFINITIONS MQLOCK)\n",
    )
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_space_separated_dash_d_macro_in_cxx_flags_is_rejected(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(repo, "cc/silo/CMakeLists.txt", 'set(CMAKE_CXX_FLAGS "-D MQLOCK")\n')
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_known_absent_list_append_indirect_is_rejected(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        "list(APPEND MODES MQLOCK)\n"
        "target_compile_definitions(t PRIVATE ${MODES})\n",
    )
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_physical_line_supply_rejection_is_not_weakened_by_splicing(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "include/legacy-physical-view.hh",
        "// phase-2 joins this comment \\\n#define MQLOCK 1\n",
    )
    with pytest.raises(RuntimeError, match="PROVEN_REPO_ABSENT_MACROS が stale"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_generator_expression_supply_remains_rejected_before_expansion(
    tmp_path: Path,
) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        'target_compile_definitions(silo PRIVATE "-DOTHER=$<IF:$<BOOL:1>,MQLOCK,0>")\n',
    )
    with pytest.raises(RuntimeError, match="generator expression"):
        source_digest._assert_proven_repo_absent_macros(os.fspath(repo))


def test_macro_include_operand_is_rejected_fail_closed(tmp_path: Path) -> None:
    old = '#define TRACE_HEADER "old.hh"\n#include TRACE_HEADER\nint steady = 7;\n'
    new = '#define TRACE_HEADER "new.hh"\n#include TRACE_HEADER\nint steady = 7;\n'
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "#include operand が literal header token でない")


def test_import_directive_is_rejected_fail_closed(tmp_path: Path) -> None:
    old = '#if TRACE\n#import "never-used.hh"\nint trace_value = 1;\n#endif\nint steady = 7;\n'
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "#import directive は未対応")


def test_digraph_include_directive_is_rejected_fail_closed(tmp_path: Path) -> None:
    old = '#if TRACE\n%:include "never-used.hh"\nint trace_value = 1;\n#endif\nint steady = 7;\n'
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "digraph directive (%:) は未対応")


def test_comment_formed_include_directive_is_rejected_fail_closed(tmp_path: Path) -> None:
    directive = '#/* comment across\n*/include "never-used.hh"\n'
    old = "#if TRACE\n" + directive + "int trace_value = 1;\n#endif\nint steady = 7;\n"
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "comment 除去後にだけ現れる include directive")


def test_line_spliced_include_is_rejected_and_was_green_before_fix(tmp_path: Path) -> None:
    old = '#if TRACE\n#inclu\\\nde "/dev/null"\nint trace_value = 1;\n#endif\nint steady = 7;\n'
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "include directive は未対応")


def test_comment_decoy_cannot_forge_raw_logical_include_correspondence(
    tmp_path: Path,
) -> None:
    empty_header = tmp_path / "empty.hh"
    empty_header.write_text("", encoding="utf-8")
    directive = f'#/**/include "{empty_header}"\n'
    decoy = f'/*\n#include "{empty_header}"\n*/\n'
    old = (
        decoy + directive
        + "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    )
    new = (
        decoy + "#if TRACE\n" + directive
        + "int trace_value = 2;\n#endif\nint steady = 7;\n"
    )
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "raw と logical で同じ位置・綴りに対応しない")


def test_two_comment_decoys_cannot_forge_raw_logical_include_correspondence(
    tmp_path: Path,
) -> None:
    directive = '#/**/include "never-used.hh"\n'
    decoys = (
        '/*\n#include "first-decoy.hh"\n*/\n'
        '/*\n#include "second-decoy.hh"\n*/\n'
    )
    old = (
        decoys + "#if TRACE\n" + directive
        + "int trace_value = 1;\n#endif\nint steady = 7;\n"
    )
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "include directive 件数が一致しない")


def test_comment_decoy_after_formed_directive_cannot_forge_correspondence(
    tmp_path: Path,
) -> None:
    directive = '#/**/include "never-used.hh"\n'
    decoy = '/*\n#include "decoy.hh"\n*/\n'
    old = (
        "#if TRACE\n" + directive
        + "int trace_value = 1;\n#endif\n" + decoy + "int steady = 7;\n"
    )
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "raw と logical で同じ位置・綴りに対応しない")


def test_comment_decoy_only_pair_preserves_raw_logical_count_rejection(
    tmp_path: Path,
) -> None:
    decoy = '/*\n#include "decoy.hh"\n*/\n'
    old = decoy + "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "include directive 件数が一致しない")


def test_new_side_comment_decoy_is_rejected_by_raw_logical_count_gate(
    tmp_path: Path,
) -> None:
    decoy = '/*\n#include "decoy.hh"\n*/\n'
    old = "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    new = decoy + old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "include directive 件数が一致しない")


def test_bom_prefixed_include_spelling_change_is_rejected(tmp_path: Path) -> None:
    old_header = tmp_path / "empty-old.hh"
    new_header = tmp_path / "empty-new.hh"
    old_header.write_text("", encoding="utf-8")
    new_header.write_text("", encoding="utf-8")
    old = (
        f'\ufeff#include "{old_header}"\n'
        "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    )
    new = (
        f'\ufeff#include "{new_header}"\n'
        "#if TRACE\nint trace_value = 2;\n#endif\nint steady = 7;\n"
    )
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "include 行文字列（順序込み）が不一致")


def test_leading_whitespace_before_include_remains_accepted(tmp_path: Path) -> None:
    old = (
        " \t#include <cstdint>\n"
        "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    )
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    result = _run(pair)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["result"] == "pass"


def test_bom_followed_by_whitespace_before_include_remains_accepted(
    tmp_path: Path,
) -> None:
    old = (
        "\ufeff \t#include <cstdint>\n"
        "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    )
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    result = _run(pair)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["result"] == "pass"


def test_duplicate_leading_bom_is_rejected_fail_closed(tmp_path: Path) -> None:
    old = (
        "\ufeff\ufeff#include <cstdint>\n"
        "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    )
    new = old.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "先頭 UTF-8 BOM が重複")


def test_asymmetric_leading_bom_is_rejected_fail_closed(tmp_path: Path) -> None:
    body = (
        "#include <cstdint>\n"
        "#if TRACE\nint trace_value = 1;\n#endif\nint steady = 7;\n"
    )
    old = "\ufeff" + body
    new = body.replace("int trace_value = 1;", "int trace_value = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "old/new の先頭 UTF-8 BOM 有無が不一致")


def test_literal_include_operand_trace_only_change_passes(tmp_path: Path) -> None:
    old = '#include <cstdint>\n#include "local.hh"\n#if TRACE\nint trace = 1;\n#endif\n'
    new = old.replace("int trace = 1;", "int trace = 2;")
    pair = _modified_pair(tmp_path, new, old_source=old)
    result = _run(pair)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["result"] == "pass"


def test_marker_name_split_by_line_continuation_is_rejected(tmp_path: Path) -> None:
    collision = "#define IZANAGI_TRACE0_INCLU\\\nDE_MARKER_00000000 0\n"
    old = collision + '#include <required.hh>\n#if TRACE\nint trace = 1;\n#endif\n'
    new = collision + '#if TRACE\n#include <required.hh>\nint trace = 2;\n#endif\n'
    pair = _modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "include marker 識別子が source と衝突")


def test_mocc_nonfinal_permitted_include_reports_nonidentical_policy_pass(
    tmp_path: Path,
) -> None:
    old = (
        '#include <first.hh>\n#include <second.hh>\n'
        '#if TRACE\nint trace = 1;\n#endif\nint steady = 7;\n'
    )
    new = (
        '#include <first.hh>\n#if TRACE\n'
        f'{_MOCC_TRACE_INCLUDE}\nint trace = 2;\n#endif\n'
        '#include <second.hh>\nint steady = 7;\n'
    )
    pair = _mocc_modified_pair(tmp_path, new, old_source=old)
    result = _run(pair)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    for context in report["files"][0]["contexts"]:
        normalized = context["normalized_preprocess"]
        activity = context["include_activity"]
        policy = activity["policy_comparison"]
        assert normalized["identical"] is True
        assert activity["old_sha256"] != activity["new_sha256"]
        assert activity["identical"] is False
        assert activity["old_active_markers"] == [
            "IZANAGI_TRACE0_INCLUDE_MARKER_00000000",
            "IZANAGI_TRACE0_INCLUDE_MARKER_00000001",
        ]
        assert activity["new_active_markers"] == [
            "IZANAGI_TRACE0_INCLUDE_MARKER_00000000",
            "IZANAGI_TRACE0_INCLUDE_MARKER_00000002",
        ]
        assert policy["accepted"] is True
        assert policy["basis"] == "permitted_mocc_trace_include_addition"
        assert policy["permitted_addition"] == {
            "new_include_index": 1,
            "new_marker": "IZANAGI_TRACE0_INCLUDE_MARKER_00000001",
            "active_at_trace0": False,
        }


def test_mocc_permitted_addition_cannot_deactivate_another_include(
    tmp_path: Path,
) -> None:
    old = (
        '#include <first.hh>\n#include <second.hh>\n'
        '#if TRACE\nint trace = 1;\n#endif\nint steady = 7;\n'
    )
    new = (
        '#include <first.hh>\n#if TRACE\n'
        f'{_MOCC_TRACE_INCLUDE}\n#include <second.hh>\nint trace = 2;\n'
        '#endif\nint steady = 7;\n'
    )
    pair = _mocc_modified_pair(tmp_path, new, old_source=old)
    _assert_rejected(_run(pair), "include 活性（順序込み）が不一致")


def test_comparison_evidence_rejects_value_digest_disagreement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker_module()
    evidence = checker._comparison_evidence(b"old-value", b"new-value")
    assert evidence["identical"] is False
    assert evidence["old_sha256"] != evidence["new_sha256"]
    monkeypatch.setattr(
        checker,
        "_independent_sha256_pair",
        lambda _old, _new: ("same-digest", "same-digest"),
    )
    with pytest.raises(checker.CheckError, match="値と digest の同一性が不整合"):
        checker._comparison_evidence(b"old-value", b"new-value")


def test_unresolved_indirect_cmake_value_is_not_a_rejection_reason(tmp_path: Path) -> None:
    repo, _old = _base_repo(tmp_path)
    _write(
        repo,
        "cc/silo/CMakeLists.txt",
        "target_compile_definitions(silo PRIVATE ${CONFIGURE_TIME_VALUE})\n",
    )
    assert source_digest._assert_proven_repo_absent_macros(
        os.fspath(repo)
    ) == source_digest.PROVEN_REPO_ABSENT_MACROS


def test_repo_supply_files_is_enumerated_once_per_absence_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str | None]] = []

    def one_snapshot(root: str, *, commit: str | None = None):
        calls.append((root, commit))
        yield "CMakeLists.txt", "target_compile_definitions(t PRIVATE OTHER_MACRO)\n"

    monkeypatch.setattr(source_digest, "_repo_supply_files", one_snapshot)
    assert source_digest._assert_proven_repo_absent_macros(
        os.fspath(tmp_path), commit="a" * 40
    ) == source_digest.PROVEN_REPO_ABSENT_MACROS
    assert calls == [(os.fspath(tmp_path), "a" * 40)]


def test_marker_prefix_is_rejected_even_without_generated_marker_name() -> None:
    checker = _load_checker_module()
    with pytest.raises(checker.CheckError, match="include marker prefix"):
        checker._mark_includes("int IZANAGI_TRACE0_INCLUDE_MARKER_custom = 0;\n")


def test_exact_include_activity_policy_report_shape() -> None:
    checker = _load_checker_module()
    decision = checker._compare_include_activity(
        "cc/silo/transaction.cc", ["M0"], ["M0"], ["M0"], ["M0"], None
    )
    assert decision == {
        "accepted": True,
        "basis": "exact_identity",
        "permitted_addition": None,
    }


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
