"""D297 header rule v2: real CMake and compiler fixtures."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign.genome import GenomeSpace

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("header_checker", ROOT / "tools/check_trace0_preprocess_identity.py")
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", os.fspath(repo), *args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _put(repo: Path, name: str, body: str) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def _supply(genome, src, build, toolchain, prefix, third):
    generated = third.get("generated", build / "generated")
    argv = [
        toolchain["cmake"]["realpath"], "-S", os.fspath(src), "-B", os.fspath(build),
        f"-DCMAKE_C_COMPILER={toolchain['cc']['realpath']}",
        f"-DCMAKE_CXX_COMPILER={toolchain['cxx']['realpath']}",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DCMAKE_BUILD_TYPE=Release",
        f"-DGENOME_FLAG={genome.flags.get('X', 0)}",
        f"-DGENERATED_DIR={generated}", "-DCCBENCH_TRACE=0",
    ]
    return argv, ["generated_header"], f"ycsb_{genome.protocol}.exe"


def _pair(tmp_path: Path, *, old_header: str, new_header: str,
          alpha: str = '#include "wrapper.hh"\nint main() { return VALUE; }\n',
          beta: str = 'int main() { return 0; }\n',
          wrapper: str = '#include "mod.hh"\n',
          generated: str = '#define GENERATED 1\n',
          extra_cmake: str = '', extra_files: dict[str, str] | None = None,
          include_genome_define: bool = True,
          gitlink_old: str | None = None, gitlink_new: str | None = None):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "fixture")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    cmake = """cmake_minimum_required(VERSION 3.18)
project(header_fixture LANGUAGES CXX)
set(GENOME_FLAG 0 CACHE STRING "")
set(GENERATED_DIR "${CMAKE_BINARY_DIR}/generated" CACHE PATH "")
configure_file("${CMAKE_SOURCE_DIR}/gen.in" "${CMAKE_BINARY_DIR}/gen.src" @ONLY)
add_custom_command(OUTPUT "${GENERATED_DIR}/gen.hh"
  COMMAND ${CMAKE_COMMAND} -E make_directory "${GENERATED_DIR}"
  COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_BINARY_DIR}/gen.src" "${GENERATED_DIR}/gen.hh"
  DEPENDS "${CMAKE_BINARY_DIR}/gen.src")
add_custom_target(generated_header DEPENDS "${GENERATED_DIR}/gen.hh")
add_executable(ycsb_alpha.exe alpha.cc)
add_executable(ycsb_beta.exe beta.cc)
add_executable(ycsb_gamma.exe gamma.cc)
foreach(t ycsb_alpha.exe ycsb_beta.exe)
  target_include_directories(${t} PRIVATE "${CMAKE_SOURCE_DIR}" "${GENERATED_DIR}")
  target_compile_options(${t} PRIVATE -Werror)
  target_compile_definitions(${t} PRIVATE TRACE=0
""" + ("    GENOME_FLAG=${GENOME_FLAG}\n" if include_genome_define else "") + """
  )
endforeach()
target_compile_options(ycsb_gamma.exe PRIVATE -Werror)
""" + extra_cmake
    _put(repo, "CMakeLists.txt", cmake)
    _put(repo, "alpha.cc", alpha)
    _put(repo, "beta.cc", beta)
    _put(repo, "gamma.cc", "int gamma() { return 0; }\n")
    _put(repo, "wrapper.hh", wrapper)
    _put(repo, "gen.in", generated)
    for name, body in (extra_files or {}).items():
        _put(repo, name, body)
    _put(repo, "mod.hh", old_header)
    _git(repo, "add", ".")
    if gitlink_old is not None:
        _git(repo, "update-index", "--add", "--cacheinfo",
             f"160000,{gitlink_old},third_party/shirakami")
    _git(repo, "commit", "-qm", "old")
    old = _git(repo, "rev-parse", "HEAD")
    _put(repo, "mod.hh", new_header)
    _git(repo, "add", "mod.hh")
    if gitlink_new is not None:
        _git(repo, "update-index", "--add", "--cacheinfo",
             f"160000,{gitlink_new},third_party/shirakami")
    _git(repo, "commit", "-qm", "new")
    new = _git(repo, "rev-parse", "HEAD")
    return repo, old, new


def _check(pair, tmp_path: Path, *, partial: bool = False, spaces=None):
    cc = shutil.which("gcc")
    cxx = shutil.which("g++")
    assert cc and cxx and shutil.which("cmake")
    cache = tmp_path / "cache"
    prefix = tmp_path / "prefix"
    scratch = tmp_path / "scratch"
    for path in (cache, prefix, scratch):
        path.mkdir(exist_ok=True)
    return checker.check(
        *pair, cxx, header_cc=cc,
        third_party_cache=None if partial else cache,
        dependency_prefix=prefix, scratch_root=scratch,
        configure_supply=_supply,
        genome_spaces=spaces or {"alpha": GenomeSpace("alpha", {"X": [0]})},
    )


def test_v3_v4_v9_generated_header_and_trace_one_consumer(tmp_path: Path) -> None:
    pair = _pair(tmp_path,
                 old_header="#if TRACE\n#define VALUE 7\n#else\n#define VALUE 1\n#endif\n",
                 new_header="#if TRACE\n#define VALUE 8\n#else\n#define VALUE 1\n#endif\n",
                 beta='#if TRACE\n#include "mod.hh"\n#endif\nint beta() { return 0; }\n',
                 alpha='#include "gen.hh"\n#include "wrapper.hh"\nint alpha() { return VALUE + GENERATED; }\n')
    report = _check(pair, tmp_path)
    rule = report["header_rule"]
    assert rule["planned_count"] == rule["executed_count"]
    assert {(row["file"], row["target"]) for row in rule["consumers"] if row["configure"] == "stock"} == {
        ("<SOURCE>/alpha.cc", "ycsb_alpha.exe"), ("<SOURCE>/beta.cc", "ycsb_beta.exe")}
    assert not any(row["target"] == "ycsb_gamma.exe" for row in rule["consumers"])


def test_matching_gitlink_is_reported_and_header_compared(tmp_path: Path) -> None:
    gitlink_oid = "a" * 40
    pair = _pair(tmp_path, old_header="#define VALUE 1\n",
                 new_header="#define VALUE 1 /* changed */\n",
                 gitlink_old=gitlink_oid)
    report = _check(pair, tmp_path)
    assert report["header_rule"]["gitlinks"] == [
        {"path": "third_party/shirakami", "commit_oid": gitlink_oid}]
    assert report["header_rule"]["planned_count"] == report["header_rule"]["executed_count"]


def test_changed_gitlink_oid_is_rejected_by_diff_validation(tmp_path: Path) -> None:
    pair = _pair(tmp_path, old_header="#define VALUE 1\n",
                 new_header="#define VALUE 1 /* changed */\n",
                 gitlink_old="a" * 40, gitlink_new="b" * 40)
    with pytest.raises(checker.CheckError, match=r"regular file でない C/C\+\+ path は未対応"):
        _check(pair, tmp_path)


def test_discovery_only_checks_production_target(tmp_path: Path) -> None:
    pair = _pair(tmp_path, old_header="#define VALUE 1\n",
                 new_header="#define VALUE 1 /* changed */\n")
    spaces = {"alpha": GenomeSpace("alpha", {"X": [0]}),
              "beta": GenomeSpace("beta", {"X": [0, 1]})}
    original = checker._h_dep
    discovery_calls = []

    def counted(entry, argv, trace, depfile):
        if depfile.name.startswith("dep-discover-beta-"):
            discovery_calls.append(depfile.name)
        return original(entry, argv, trace, depfile)

    checker._h_dep = counted
    try:
        report = _check(pair, tmp_path, spaces=spaces)
    finally:
        checker._h_dep = original
    assert report["header_rule"]["unselected_genomes_checked"]["beta"] == 2
    assert len(discovery_calls) == 8  # two genomes, old/new, TRACE=0/1, beta only


def test_v1_indirect_consumer_value_change(tmp_path: Path) -> None:
    pair = _pair(
        tmp_path,
        old_header="#if ALPHA_ONLY\n#define VALUE 1\n#else\n#define VALUE 0\n#endif\n",
        new_header="#if ALPHA_ONLY\n#define VALUE 2\n#else\n#define VALUE 0\n#endif\n",
        beta='#include "mod.hh"\nint beta() { return VALUE; }\n',
        extra_cmake='target_compile_definitions(ycsb_alpha.exe PRIVATE ALPHA_ONLY=1)\n'
                    'target_compile_definitions(ycsb_beta.exe PRIVATE ALPHA_ONLY=0)\n',
    )
    with pytest.raises(checker.CheckError, match="expanded 不一致"):
        _check(pair, tmp_path)


def test_v10_trace_zero_value_change(tmp_path: Path) -> None:
    pair = _pair(tmp_path, old_header="#define VALUE 1\n", new_header="#define VALUE 3\n",
                 alpha='#include "mod.hh"\nint alpha() { return VALUE; }\n')
    with pytest.raises(checker.CheckError, match="expanded 不一致"):
        _check(pair, tmp_path)


def test_v11_include_activity_change(tmp_path: Path) -> None:
    pair = _pair(tmp_path,
                 old_header='#if !TRACE\n#include "empty.hh"\n#endif\n#define VALUE 1\n',
                 new_header='#if TRACE\n#include "empty.hh"\n#endif\n#define VALUE 1\n',
                 extra_files={"empty.hh": ""})
    with pytest.raises(checker.CheckError, match="include_activity 不一致"):
        _check(pair, tmp_path)


def test_v12_partial_header_inputs_rejected(tmp_path: Path) -> None:
    pair = _pair(tmp_path, old_header="#define VALUE 1\n", new_header="#define VALUE 1 /* changed */\n")
    with pytest.raises(checker.CheckError, match="header の変更は consumer TU"):
        _check(pair, tmp_path, partial=True)


def test_v2_generated_header_hides_changed_header_without_build(tmp_path: Path) -> None:
    pair = _pair(
        tmp_path,
        old_header="#if ALPHA_ONLY\n#define VALUE 1\n#else\n#define VALUE 0\n#endif\n",
        new_header="#if ALPHA_ONLY\n#define VALUE 2\n#else\n#define VALUE 0\n#endif\n",
        alpha='#include "gen.hh"\nint alpha() { return VALUE; }\n',
        beta='#include "mod.hh"\nint beta() { return VALUE; }\n',
        generated='#include "mod.hh"\n',
        extra_cmake='target_compile_definitions(ycsb_alpha.exe PRIVATE ALPHA_ONLY=1)\n'
                    'target_compile_definitions(ycsb_beta.exe PRIVATE ALPHA_ONLY=0)\n',
    )
    with pytest.raises(checker.CheckError, match="expanded 不一致"):
        _check(pair, tmp_path)


def test_v5_genome_only_production_consumer(tmp_path: Path) -> None:
    pair = _pair(
        tmp_path,
        old_header="#if GENOME_FLAG\n#define VALUE 1\n#else\n#define VALUE 0\n#endif\n",
        new_header="#if GENOME_FLAG\n#define VALUE 2\n#else\n#define VALUE 0\n#endif\n",
        alpha='#if GENOME_FLAG\n#include "mod.hh"\n#else\n#define VALUE 0\n#endif\n'
              'int alpha() { return VALUE; }\n',
        beta='#include "mod.hh"\nint beta() { return VALUE; }\n',
    )
    spaces = {"alpha": GenomeSpace("alpha", {"X": [0, 1]})}
    with pytest.raises(checker.CheckError, match="expanded 不一致"):
        _check(pair, tmp_path, spaces=spaces)


def test_v6_other_protocol_consumer_under_selected_genome(tmp_path: Path) -> None:
    pair = _pair(
        tmp_path,
        old_header="#if BETA_SPECIAL\n#define VALUE 1\n#else\n#define VALUE 0\n#endif\n",
        new_header="#if BETA_SPECIAL\n#define VALUE 2\n#else\n#define VALUE 0\n#endif\n",
        beta='#include "mod.hh"\nint beta() { return VALUE; }\n',
        extra_cmake='target_compile_definitions(ycsb_alpha.exe PRIVATE BETA_SPECIAL=0)\n'
                    'target_compile_definitions(ycsb_beta.exe PRIVATE BETA_SPECIAL=${GENOME_FLAG})\n',
    )
    spaces = {"alpha": GenomeSpace("alpha", {"X": [0, 1]}),
              "beta": GenomeSpace("beta", {"X": [0]})}
    with pytest.raises(checker.CheckError, match="expanded 不一致"):
        _check(pair, tmp_path, spaces=spaces)


def test_v7_aggregate_requires_dependency_content(tmp_path: Path) -> None:
    pair = _pair(
        tmp_path,
        old_header="#if GENVAL == 1\n#define VALUE 1\n#else\n#define VALUE 0\n#endif\n",
        new_header="#if GENVAL == 1\n#define VALUE 2\n#else\n#define VALUE 0\n#endif\n",
        alpha='#include "gen.hh"\n#include "mod.hh"\nint alpha() { return VALUE; }\n',
        generated="#define GENVAL @GENOME_FLAG@\n",
        include_genome_define=False,
    )
    spaces = {"alpha": GenomeSpace("alpha", {"X": [0, 1]})}
    with pytest.raises(checker.CheckError, match="expanded 不一致"):
        _check(pair, tmp_path, spaces=spaces)


def test_v8_trace_effective_value_is_checked(tmp_path: Path) -> None:
    pair = _pair(
        tmp_path,
        old_header="#if !TRACE\n#define VALUE 1\n#else\n#define VALUE 0\n#endif\n",
        new_header="#if !TRACE\n#define VALUE 2\n#else\n#define VALUE 0\n#endif\n",
        alpha='#include "mod.hh"\nint alpha() { return VALUE; }\n',
        extra_files={"forced.hh": "#undef TRACE\n#define TRACE 1\n"},
        extra_cmake='target_compile_options(ycsb_alpha.exe PRIVATE -include "${CMAKE_SOURCE_DIR}/forced.hh")\n',
    )
    with pytest.raises(checker.CheckError, match="TRACE=0 の実効値"):
        _check(pair, tmp_path)


def test_volatile_builtin_in_expansion_is_rejected(tmp_path: Path) -> None:
    pair = _pair(
        tmp_path, old_header="#define VALUE 1\n",
        new_header="#define VALUE 1 /* changed */\n",
        alpha='#include "wrapper.hh"\nconst char* d = __DATE__; int alpha() { return VALUE; }\n',
    )
    with pytest.raises(checker.CheckError, match="volatile builtin"):
        _check(pair, tmp_path)
