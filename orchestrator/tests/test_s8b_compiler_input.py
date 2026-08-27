# -*- coding: utf-8 -*-
"""Strict compiler-input manifest collection and snapshot validation."""
from __future__ import annotations

import copy
import hashlib
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orchestrator.campaign import s8b_compiler_input as compiler_input  # noqa: E402


TARGET = "ycsb_silo.exe"


def _write_build_shape(
        root: Path, snapshot: Path, *, generator: str = "Unix Makefiles",
        input_path: Path | None = None, include_flags: bool = True) -> Path:
    target_dir = root / "cc" / "silo" / "CMakeFiles" / f"{TARGET}.dir"
    target_dir.mkdir(parents=True)
    (root / "CMakeCache.txt").write_text(
        f"CMAKE_GENERATOR:INTERNAL={generator}\n", encoding="utf-8",
    )
    if include_flags:
        (target_dir / "flags.make").write_text(
            "# CMAKE generated file: DO NOT EDIT!\n"
            "# compile CXX with /usr/bin/c++\n"
            "CXX_DEFINES = -DBACK_OFF=1\n"
            f"CXX_INCLUDES = -I{snapshot}\n"
            "CXX_FLAGS = -O3 -std=c++20\n",
            encoding="utf-8",
        )
    (target_dir / "link.txt").write_text(
        "/usr/bin/c++ cc/silo/CMakeFiles/ycsb_silo.exe.dir/src/txn.cc.o "
        "-o cc/silo/ycsb_silo.exe\n",
        encoding="utf-8",
    )
    selected = input_path or snapshot / "include" / "unrelated.hh"
    depfile = target_dir / "src" / "txn.cc.o.d"
    depfile.parent.mkdir()
    object_path = depfile.with_suffix("")
    depfile.write_text(
        f"{object_path}: \\\n {selected}\n",
        encoding="utf-8",
    )
    return target_dir


def _fixture(tmp_path: Path, name: str = "case") -> tuple[Path, Path]:
    snapshot = tmp_path / name / "snapshot"
    build = tmp_path / name / "build"
    (snapshot / "include").mkdir(parents=True)
    (snapshot / "include" / "unrelated.hh").write_bytes(b"#define VALUE 7\n")
    _write_build_shape(build, snapshot)
    return snapshot, build


def test_manifest_is_complete_canonical_and_root_independent(tmp_path):
    snapshot_a, build_a = _fixture(tmp_path, "a")
    snapshot_b, build_b = _fixture(tmp_path, "different-root")

    first = compiler_input.collect_compiler_input_manifest(
        build_a, snapshot_a, target=TARGET,
    )
    second = compiler_input.collect_compiler_input_manifest(
        build_b, snapshot_b, target=TARGET,
    )

    assert first == second
    assert first.manifest == {
        "schema_version": compiler_input.MANIFEST_SCHEMA,
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": TARGET,
        "depfile_count": 1,
        "inputs": [{
            "path": "include/unrelated.hh",
            "sha256": hashlib.sha256(b"#define VALUE 7\n").hexdigest(),
        }],
    }
    assert str(snapshot_a) not in repr(first.manifest)
    assert str(build_a) not in repr(first.manifest)


def test_target_subdirectory_working_directory_shape_is_supported(tmp_path):
    snapshot, build = _fixture(tmp_path)
    target_dir = build / "cc" / "silo" / "CMakeFiles" / f"{TARGET}.dir"
    (target_dir / "link.txt").write_text(
        f"/usr/bin/c++ CMakeFiles/{TARGET}.dir/src/txn.cc.o -o {TARGET}\n",
        encoding="utf-8",
    )
    depfile = target_dir / "src" / "txn.cc.o.d"
    depfile.write_text(
        f"CMakeFiles/{TARGET}.dir/src/txn.cc.o: "
        f"{snapshot / 'include' / 'unrelated.hh'}\n",
        encoding="utf-8",
    )

    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )
    assert collected.manifest["depfile_count"] == 1


def test_observed_cmake_325_unix_makefiles_shape_is_collected(tmp_path):
    snapshot = tmp_path / "snapshot"
    source_dir = snapshot / "cc" / "silo"
    include_dir = snapshot / "include"
    source_dir.mkdir(parents=True)
    (source_dir / "include").mkdir()
    include_dir.mkdir()
    common_header = include_dir / "common.hh"
    common_header.write_bytes(b"#define COMMON_VALUE 7\n")
    noncanonical_common_header = (
        f"{source_dir}/include/../../../include/{common_header.name}"
    )

    build = tmp_path / "build"
    target_dir = build / "cc" / "silo" / "CMakeFiles" / f"{TARGET}.dir"
    target_dir.mkdir(parents=True)
    (build / "CMakeCache.txt").write_text(
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles\n",
        encoding="utf-8",
    )

    metadata_names = {
        "DependInfo.cmake",
        "build.make",
        "cmake_clean.cmake",
        "compiler_depend.make",
        "compiler_depend.ts",
        "depend.make",
        "flags.make",
        "link.txt",
        "progress.make",
    }
    for name in metadata_names - {"flags.make", "link.txt"}:
        (target_dir / name).write_text("# observed build metadata\n", encoding="utf-8")

    fetchcontent_base = tmp_path / "fetchcontent"
    dependency_prefix = tmp_path / "dependency-prefix"
    (target_dir / "flags.make").write_text(
        "# CMAKE generated file: DO NOT EDIT!\n"
        '# Generated by "Unix Makefiles" Generator, CMake Version 3.25\n'
        "\n"
        "# compile CXX with /usr/bin/g++\n"
        "CXX_DEFINES = -DADD_ANALYSIS=0 -DBACK_OFF=1 -DBOOST_ALL_NO_LIB "
        "-DBOOST_FILESYSTEM_DYN_LINK -DKEY_SIZE=8 -DLinux "
        "-DMASSTREE_USE=1 -DNO_WAIT_LOCKING_IN_VALIDATION=1 "
        "-DNO_WAIT_OF_TICTOC=0 -DPARTITION_TABLE=0 -DPROCEDURE_SORT=0 "
        "-DSLEEP_READ_PHASE=0 -DTRACE=0 -DVAL_SIZE=4 -DWAL=0\n"
        "\n"
        f"CXX_INCLUDES = -I{snapshot} "
        f"-I{fetchcontent_base / 'masstree-src'} "
        f"-I{fetchcontent_base / 'mimalloc-src' / 'include'} "
        f"-isystem {dependency_prefix / 'include'}\n"
        "\n"
        "CXX_FLAGS = -O3 -DNDEBUG -Wall -Wextra -Werror -std=c++20\n",
        encoding="utf-8",
    )

    object_names = (
        "ycsb_silo.cc.o",
        "transaction.cc.o",
        "util.cc.o",
    )
    source_names = (
        "ycsb_silo.cc",
        "transaction.cc",
        "util.cc",
    )
    expected_objects = set()
    depfiles = []
    for object_name, source_name in zip(object_names, source_names, strict=True):
        source = source_dir / source_name
        source.write_bytes(f"// {source_name}\n".encode("utf-8"))
        object_path = target_dir / object_name
        object_path.write_bytes(b"observed object fixture\n")
        expected_objects.add(object_path.resolve())
        depfile = target_dir / f"{object_name}.d"
        target = Path("cc") / "silo" / "CMakeFiles" / f"{TARGET}.dir" / object_name
        header_input = (
            noncanonical_common_header
            if object_name == "ycsb_silo.cc.o"
            else str(common_header.resolve())
        )
        depfile.write_text(
            f"{target}: \\\n"
            f" {source.resolve()} \\\n"
            f" {header_input}\n",
            encoding="utf-8",
        )
        depfiles.append(depfile)
    assert any(
        noncanonical_common_header in depfile.read_text(encoding="utf-8")
        for depfile in depfiles
    )

    link_relative_objects = (
        str(Path("CMakeFiles") / f"{TARGET}.dir" / object_name)
        for object_name in object_names
    )
    link_text = (
        "/usr/bin/g++ -O3 -DNDEBUG "
        f"{' '.join(link_relative_objects)} "
        f"-o {TARGET}  -Wl,-rpath,{dependency_prefix / 'lib'} "
        f"../../libccbench_common.a "
        f"{fetchcontent_base / 'mimalloc-build' / 'libmimalloc.a'} "
        "/usr/lib/x86_64-linux-gnu/libboost_filesystem.so.1.74.0 "
        f"{dependency_prefix / 'lib' / 'libgflags.a'} "
        f"{dependency_prefix / 'lib' / 'libglog.a'} "
        f"{fetchcontent_base / 'masstree-src' / 'libkohler_masstree_json.a'} "
        "-lpthread -lrt -latomic \n"
    )
    assert f"-o {TARGET}  -Wl," in link_text
    assert link_text.endswith("-latomic \n")
    (target_dir / "link.txt").write_text(link_text, encoding="utf-8")

    link_objects = {
        (build / "cc" / "silo" / token).resolve()
        for token in link_text.split()
        if token.endswith(".o")
    }
    depfile_objects = set()
    for depfile in depfiles:
        depfile_text = depfile.read_text(encoding="utf-8")
        target, dependencies = depfile_text.split(":", 1)
        assert not Path(target).is_absolute()
        assert target.startswith("cc/silo/")
        assert "\\\n" in dependencies
        dependency_tokens = dependencies.replace("\\\n", " ").split()
        assert dependency_tokens
        assert all(Path(token).is_absolute() for token in dependency_tokens)
        depfile_objects.add((build / target).resolve())
    assert len(link_objects) == 3
    assert link_objects == depfile_objects == expected_objects
    assert all((target_dir / name).is_file() for name in metadata_names)

    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )

    assert collected.manifest["depfile_count"] == 3
    collected_paths = [
        entry["path"] for entry in collected.manifest["inputs"]
    ]
    assert collected_paths.count("include/common.hh") == 1
    assert all("../" not in path for path in collected_paths)
    collected_basenames = {
        Path(entry["path"]).name for entry in collected.manifest["inputs"]
    }
    assert metadata_names.isdisjoint(collected_basenames)


def test_external_compiler_input_is_rejected(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    outside = tmp_path / "outside.hh"
    outside.write_bytes(b"outside\n")
    build = tmp_path / "build"
    _write_build_shape(build, snapshot, input_path=outside)

    with pytest.raises(compiler_input.CompilerInputError, match="outside"):
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET,
        )


def test_descriptor_policy_hashes_external_input_without_snapshot_membership(
        tmp_path):
    snapshot = tmp_path / "snapshot"
    evolve_source = snapshot / "include" / "predicate.hh"
    evolve_source.parent.mkdir(parents=True)
    evolve_source.write_bytes(b"bool predicate = true;\n")
    outside = tmp_path / "system" / "header.hh"
    outside.parent.mkdir()
    outside.write_bytes(b"#define SYSTEM_VALUE 9\n")
    build = tmp_path / "build"
    _write_build_shape(build, snapshot, input_path=outside)
    expected_sources = {
        "include/predicate.hh": hashlib.sha256(
            evolve_source.read_bytes()
        ).hexdigest(),
    }

    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        expected_evolve_block_sources=expected_sources,
    )

    assert collected.manifest["input_policy"] == (
        "snapshot-and-external-hashes/v1"
    )
    assert collected.manifest["inputs"] == [{
        "path": str(outside.resolve()),
        "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
    }]
    assert collected.manifest["evolve_block_sources"] == [{
        "path": "include/predicate.hh",
        "sha256": expected_sources["include/predicate.hh"],
    }]
    assert "include/predicate.hh" not in {
        entry["path"] for entry in collected.manifest["inputs"]
    }


def test_external_input_bytes_drift_is_rejected_by_validator(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    outside = tmp_path / "outside.hh"
    outside.write_bytes(b"outside-v1\n")
    build = tmp_path / "build"
    _write_build_shape(build, snapshot, input_path=outside)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
    )
    outside.write_bytes(b"outside-v2\n")

    with pytest.raises(compiler_input.CompilerInputError, match="external.*bytes"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot, target=TARGET,
        )


def test_evolve_block_source_requires_prebuild_snapshot_bytes(tmp_path):
    snapshot, build = _fixture(tmp_path)
    source = snapshot / "include" / "predicate.hh"
    source.write_bytes(b"predicate-v1\n")
    expected_sources = {
        "include/predicate.hh": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    source.write_bytes(b"predicate-v2\n")

    with pytest.raises(
            compiler_input.CompilerInputError,
            match="EVOLVE-BLOCK source bytes differ"):
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET, allow_external_inputs=True,
            expected_evolve_block_sources=expected_sources,
        )


def test_missing_depfile_for_linked_object_is_rejected(tmp_path):
    snapshot, build = _fixture(tmp_path)
    target_dir = build / "cc" / "silo" / "CMakeFiles" / f"{TARGET}.dir"
    (target_dir / "link.txt").write_text(
        "/usr/bin/c++ "
        "cc/silo/CMakeFiles/ycsb_silo.exe.dir/src/txn.cc.o "
        "cc/silo/CMakeFiles/ycsb_silo.exe.dir/src/missing.cc.o "
        "-o cc/silo/ycsb_silo.exe\n",
        encoding="utf-8",
    )

    with pytest.raises(compiler_input.CompilerInputError, match="exact set"):
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET,
        )


def test_validator_rejects_snapshot_bytes_changed_after_collection(tmp_path):
    snapshot, build = _fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )
    (snapshot / "include" / "unrelated.hh").write_bytes(b"changed\n")

    with pytest.raises(compiler_input.CompilerInputError, match="bytes differ"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot, target=TARGET,
        )


@pytest.mark.parametrize(
    ("generator", "include_flags", "match"),
    [
        ("Ninja", True, "CMAKE_GENERATOR"),
        ("Unix Makefiles", False, "flags.make"),
    ],
)
def test_unsupported_generator_or_metadata_shape_is_fail_closed(
        tmp_path, generator, include_flags, match):
    snapshot = tmp_path / "snapshot"
    (snapshot / "include").mkdir(parents=True)
    (snapshot / "include" / "unrelated.hh").write_bytes(b"header\n")
    build = tmp_path / "build"
    _write_build_shape(
        build, snapshot, generator=generator, include_flags=include_flags,
    )

    with pytest.raises(compiler_input.CompilerInputError, match=match):
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET,
        )


def test_manifest_digest_and_exact_shape_are_enforced(tmp_path):
    snapshot, build = _fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )
    tampered = copy.deepcopy(collected.manifest)
    tampered["inputs"][0]["sha256"] = "0" * 64

    with pytest.raises(compiler_input.CompilerInputError, match="sha256 mismatch"):
        compiler_input.validate_compiler_input_manifest(
            tampered, collected.manifest_sha256,
            snapshot_root=snapshot, target=TARGET,
        )


def test_no_particular_declared_source_membership_is_required(tmp_path):
    """The only dependency may have an unrelated name; no tautological source gate exists."""
    snapshot, build = _fixture(tmp_path)
    result = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )
    assert [entry["path"] for entry in result.manifest["inputs"]] == [
        "include/unrelated.hh"
    ]


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
