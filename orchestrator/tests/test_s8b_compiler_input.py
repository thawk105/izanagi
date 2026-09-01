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
            "root": "snapshot",
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
        "root": "filesystem",
        "path": str(outside.resolve()).lstrip("/"),
        "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
    }]
    assert collected.manifest["evolve_block_sources"] == [{
        "path": "include/predicate.hh",
        "sha256": expected_sources["include/predicate.hh"],
    }]
    assert "include/predicate.hh" not in {
        entry["path"] for entry in collected.manifest["inputs"]
    }


def test_double_slash_input_matches_single_slash_manifest_and_digest(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    outside = tmp_path / "system" / "header.hh"
    outside.parent.mkdir()
    outside.write_bytes(b"#define SYSTEM_VALUE 9\n")
    canonical_build = tmp_path / "canonical-build"
    double_slash_build = tmp_path / "double-slash-build"
    double_slash_outside = Path(f"/{outside}")
    assert str(double_slash_outside) == f"/{outside}"
    _write_build_shape(canonical_build, snapshot, input_path=outside)
    _write_build_shape(
        double_slash_build, snapshot, input_path=double_slash_outside,
    )

    canonical = compiler_input.collect_compiler_input_manifest(
        canonical_build, snapshot, target=TARGET, allow_external_inputs=True,
    )
    double_slash = compiler_input.collect_compiler_input_manifest(
        double_slash_build, snapshot, target=TARGET, allow_external_inputs=True,
    )

    assert double_slash == canonical


def _fetchcontent_fixture(tmp_path: Path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    base_a = tmp_path / "base-a"
    base_b = tmp_path / "base-b"
    relative = Path("include") / "x.hh"
    for base in (base_a, base_b):
        source = base / "masstree-src"
        (source / relative).parent.mkdir(parents=True)
        (source / relative).write_bytes(b"portable masstree header\n")
    build = tmp_path / "build"
    _write_build_shape(
        build, snapshot, input_path=base_a / "masstree-src" / relative,
    )
    return snapshot, build, base_a, base_b, relative


def test_v2_manifest_classifies_fetchcontent_root_relative(tmp_path):
    snapshot, build, base_a, base_b, relative = _fetchcontent_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_fetchcontent_masstree_root=base_a / "masstree-src",
        current_fetchcontent_masstree_root=base_b / "masstree-src",
    )

    assert collected.manifest["schema_version"] == compiler_input.MANIFEST_SCHEMA
    assert collected.manifest["inputs"] == [{
        "root": "fetchcontent-masstree",
        "path": relative.as_posix(),
        "sha256": hashlib.sha256(b"portable masstree header\n").hexdigest(),
    }]
    assert str(base_a) not in repr(collected.manifest)
    assert str(base_b) not in repr(collected.manifest)


def test_v2_manifest_with_normal_relative_path_validates(tmp_path):
    snapshot, build = _fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )

    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=snapshot, target=TARGET,
        current_dependency_prefix_roots=(),
    ) == collected.manifest


def test_v2_manifest_rejects_dot_path_as_compiler_input_error(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    manifest = {
        "schema_version": compiler_input.MANIFEST_SCHEMA,
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": TARGET,
        "depfile_count": 1,
        "inputs": [{
            "root": "snapshot",
            "path": ".",
            "sha256": "0" * 64,
        }],
    }

    with pytest.raises(
            compiler_input.CompilerInputError,
            match="not normalized relative POSIX") as caught:
        compiler_input.validate_compiler_input_manifest(
            manifest, compiler_input.manifest_sha256(manifest),
            snapshot_root=snapshot, target=TARGET,
            current_dependency_prefix_roots=(),
        )
    assert type(caught.value) is compiler_input.CompilerInputError


def test_v2_validator_rebinds_fetchcontent_inputs_to_current_root(tmp_path):
    snapshot, build, base_a, base_b, _relative = _fetchcontent_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_fetchcontent_masstree_root=base_a / "masstree-src",
        current_fetchcontent_masstree_root=base_b / "masstree-src",
    )
    import shutil
    shutil.rmtree(base_a)

    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=snapshot, target=TARGET,
        current_fetchcontent_masstree_root=base_b / "masstree-src",
        current_dependency_prefix_roots=(),
    ) == collected.manifest


def test_v2_current_fetchcontent_bytes_drift_is_rejected(tmp_path):
    snapshot, build, base_a, base_b, relative = _fetchcontent_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_fetchcontent_masstree_root=base_a / "masstree-src",
        current_fetchcontent_masstree_root=base_b / "masstree-src",
    )
    (base_b / "masstree-src" / relative).write_bytes(b"drift\n")
    with pytest.raises(compiler_input.CompilerInputError, match="bytes differ"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
            current_fetchcontent_masstree_root=base_b / "masstree-src",
            current_dependency_prefix_roots=(),
        )


def test_v2_missing_current_fetchcontent_input_is_rejected(tmp_path):
    snapshot, build, base_a, base_b, relative = _fetchcontent_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_fetchcontent_masstree_root=base_a / "masstree-src",
        current_fetchcontent_masstree_root=base_b / "masstree-src",
    )
    (base_b / "masstree-src" / relative).unlink()
    with pytest.raises(compiler_input.CompilerInputError, match="unavailable"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
            current_fetchcontent_masstree_root=base_b / "masstree-src",
            current_dependency_prefix_roots=(),
        )


@pytest.mark.parametrize("symlink_kind", ["leaf", "component"])
def test_v2_current_fetchcontent_symlink_component_is_rejected(
        tmp_path, symlink_kind):
    snapshot, build, base_a, base_b, relative = _fetchcontent_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_fetchcontent_masstree_root=base_a / "masstree-src",
        current_fetchcontent_masstree_root=base_b / "masstree-src",
    )
    root = base_b / "masstree-src"
    if symlink_kind == "leaf":
        leaf = root / relative
        target = base_b / "leaf-target.hh"
        target.write_bytes(leaf.read_bytes())
        leaf.unlink()
        leaf.symlink_to(target)
        current = root
    elif symlink_kind == "component":
        include = root / "include"
        target = base_b / "include-target"
        include.rename(target)
        include.symlink_to(target, target_is_directory=True)
        current = root
    with pytest.raises(compiler_input.CompilerInputError, match="symlink|canonical"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
            current_fetchcontent_masstree_root=current,
            current_dependency_prefix_roots=(),
        )


def test_symlink_spelled_root_collects_and_validates_identically(tmp_path):
    snapshot, build = _fixture(tmp_path)
    alias = tmp_path / "snapshot-link"
    alias.symlink_to(snapshot, target_is_directory=True)

    canonical = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )
    through_alias = compiler_input.collect_compiler_input_manifest(
        build, alias, target=TARGET,
    )

    assert through_alias == canonical
    assert compiler_input.validate_compiler_input_manifest(
        through_alias.manifest, through_alias.manifest_sha256,
        snapshot_root=alias, target=TARGET,
        current_dependency_prefix_roots=(),
    ) == canonical.manifest


def test_symlink_component_beneath_root_remains_rejected(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    actual_include = snapshot / "actual-include"
    actual_include.mkdir()
    header = actual_include / "unrelated.hh"
    header.write_bytes(b"#define VALUE 7\n")
    (snapshot / "include").symlink_to(
        actual_include, target_is_directory=True,
    )
    build = tmp_path / "build"
    _write_build_shape(
        build, snapshot, input_path=snapshot / "include" / header.name,
    )

    with pytest.raises(compiler_input.CompilerInputError, match="symlink component"):
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET,
        )


def test_v2_current_fetchcontent_nonregular_leaf_is_rejected(tmp_path):
    snapshot, build, base_a, base_b, relative = _fetchcontent_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_fetchcontent_masstree_root=base_a / "masstree-src",
        current_fetchcontent_masstree_root=base_b / "masstree-src",
    )
    leaf = base_b / "masstree-src" / relative
    leaf.unlink()
    leaf.mkdir()
    with pytest.raises(compiler_input.CompilerInputError, match="regular file"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
            current_fetchcontent_masstree_root=base_b / "masstree-src",
            current_dependency_prefix_roots=(),
        )


def test_v2_rejects_noncanonical_root_tag(tmp_path):
    snapshot, build, base_a, base_b, relative = _fetchcontent_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_fetchcontent_masstree_root=base_a / "masstree-src",
        current_fetchcontent_masstree_root=base_b / "masstree-src",
    )
    forged = copy.deepcopy(collected.manifest)
    forged["inputs"][0].update({
        "root": "filesystem",
        "path": str(base_b / "masstree-src" / relative).lstrip("/"),
    })
    digest = compiler_input.manifest_sha256(forged)
    with pytest.raises(compiler_input.CompilerInputError, match="root tag"):
        compiler_input.validate_compiler_input_manifest(
            forged, digest, snapshot_root=snapshot,
            current_fetchcontent_masstree_root=base_b / "masstree-src",
            current_dependency_prefix_roots=(),
        )


def test_v2_unknown_fetchcontent_root_is_not_classified_as_filesystem(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    base = tmp_path / "fetchcontent"
    masstree = base / "masstree-src"
    masstree.mkdir(parents=True)
    unknown = base / "mimalloc-src" / "include" / "mimalloc.h"
    unknown.parent.mkdir(parents=True)
    unknown.write_bytes(b"unknown fetchcontent\n")
    build = tmp_path / "build"
    _write_build_shape(build, snapshot, input_path=unknown)

    with pytest.raises(compiler_input.CompilerInputError, match="unsupported FetchContent"):
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET, allow_external_inputs=True,
            origin_fetchcontent_masstree_root=masstree,
            current_fetchcontent_masstree_root=masstree,
        )


def test_double_slash_unknown_fetchcontent_root_is_compiler_input_error(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    base = tmp_path / "fetchcontent"
    masstree = base / "masstree-src"
    masstree.mkdir(parents=True)
    unknown = base / "mimalloc-src" / "include" / "mimalloc.h"
    unknown.parent.mkdir(parents=True)
    unknown.write_bytes(b"unknown fetchcontent\n")
    build = tmp_path / "build"
    double_slash_unknown = Path(f"/{unknown}")
    assert str(double_slash_unknown) == f"/{unknown}"
    _write_build_shape(
        build, snapshot, input_path=double_slash_unknown,
    )

    with pytest.raises(
            compiler_input.CompilerInputError,
            match="unsupported FetchContent") as caught:
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET, allow_external_inputs=True,
            origin_fetchcontent_masstree_root=masstree,
            current_fetchcontent_masstree_root=masstree,
        )
    assert type(caught.value) is compiler_input.CompilerInputError


def _dependency_prefix_fixture(tmp_path: Path, name: str = "dependency"):
    snapshot = tmp_path / name / "snapshot"
    snapshot.mkdir(parents=True)
    relative = Path("include") / "portable.hh"
    origin_match = tmp_path / name / "origin" / "gflags-install"
    origin_other = tmp_path / name / "origin" / "glog-install"
    current_match = tmp_path / name / "current" / "renamed-a"
    current_other = tmp_path / name / "current" / "renamed-b"
    for root in (origin_match, origin_other, current_match, current_other):
        root.mkdir(parents=True)
    payload = b"portable dependency header\n"
    for root in (origin_match, current_match):
        (root / relative).parent.mkdir()
        (root / relative).write_bytes(payload)
    build = tmp_path / name / "build"
    _write_build_shape(build, snapshot, input_path=origin_match / relative)
    return (
        snapshot, build, origin_match, origin_other,
        current_match, current_other, relative, payload,
    )


def _snapshot_only_v3_fixture(tmp_path: Path, name: str):
    snapshot, build = _fixture(tmp_path, name)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )
    good_root = tmp_path / name / "dependency-good"
    good_root.mkdir()
    missing_root = tmp_path / name / "dependency-missing"
    return snapshot, collected, good_root, missing_root


def _collected_dependency_v3_fixture(tmp_path: Path, name: str):
    fixture = _dependency_prefix_fixture(tmp_path, name)
    collected = compiler_input.collect_compiler_input_manifest(
        fixture[1], fixture[0], target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(fixture[2], fixture[3]),
        current_dependency_prefix_roots=(fixture[4], fixture[5]),
    )
    missing_root = tmp_path / name / "current" / "dependency-missing"
    return fixture, collected, missing_root


def test_v3_probe_snapshot_only_accepts_one_existing_dependency_root(tmp_path):
    snapshot, collected, good_root, _missing_root = (
        _snapshot_only_v3_fixture(tmp_path, "snapshot-good")
    )

    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=snapshot,
        current_dependency_prefix_roots=(good_root,),
    ) == collected.manifest


def test_v3_probe_snapshot_only_accepts_existing_and_missing_roots(tmp_path):
    snapshot, collected, good_root, missing_root = (
        _snapshot_only_v3_fixture(tmp_path, "snapshot-good-missing")
    )

    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=snapshot,
        current_dependency_prefix_roots=(good_root, missing_root),
    ) == collected.manifest


def test_v3_probe_snapshot_only_accepts_only_missing_root(tmp_path):
    snapshot, collected, _good_root, missing_root = (
        _snapshot_only_v3_fixture(tmp_path, "snapshot-missing")
    )

    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=snapshot,
        current_dependency_prefix_roots=(missing_root,),
    ) == collected.manifest


def test_v3_probe_dependency_entry_accepts_one_matching_root(tmp_path):
    fixture, collected, _missing_root = _collected_dependency_v3_fixture(
        tmp_path, "dependency-good",
    )

    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=fixture[0],
        current_dependency_prefix_roots=(fixture[4],),
    ) == collected.manifest


def test_v3_probe_dependency_entry_accepts_matching_and_missing_roots(tmp_path):
    fixture, collected, missing_root = _collected_dependency_v3_fixture(
        tmp_path, "dependency-good-missing",
    )

    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=fixture[0],
        current_dependency_prefix_roots=(fixture[4], missing_root),
    ) == collected.manifest


def test_v3_dependency_entry_rejects_only_missing_root_as_zero_matches(tmp_path):
    fixture, collected, missing_root = _collected_dependency_v3_fixture(
        tmp_path, "dependency-missing",
    )

    with pytest.raises(compiler_input.CompilerInputError, match="one current root"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=fixture[0],
            current_dependency_prefix_roots=(missing_root,),
        )


def test_v3_probe_snapshot_only_accepts_explicit_empty_roots(tmp_path):
    snapshot, collected, _good_root, _missing_root = (
        _snapshot_only_v3_fixture(tmp_path, "snapshot-empty")
    )

    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=snapshot,
        current_dependency_prefix_roots=(),
    ) == collected.manifest


def test_v3_probe_snapshot_only_rejects_none_root_context(tmp_path):
    snapshot, collected, _good_root, _missing_root = (
        _snapshot_only_v3_fixture(tmp_path, "snapshot-none")
    )

    with pytest.raises(compiler_input.CompilerInputError, match="context"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
            current_dependency_prefix_roots=None,
        )


def test_v3_collector_ignores_missing_origin_and_current_root_elements(tmp_path):
    fixture = _dependency_prefix_fixture(tmp_path, "collector-missing")
    missing_origin = tmp_path / "collector-missing" / "origin" / "missing"
    missing_current = tmp_path / "collector-missing" / "current" / "missing"

    collected = compiler_input.collect_compiler_input_manifest(
        fixture[1], fixture[0], target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(missing_origin, fixture[2]),
        current_dependency_prefix_roots=(fixture[4], missing_current),
    )

    assert collected.manifest["inputs"] == [{
        "root": "dependency-prefix",
        "path": fixture[6].as_posix(),
        "sha256": hashlib.sha256(fixture[7]).hexdigest(),
    }]


@pytest.mark.parametrize(
    "invalid_root",
    [123, "", "relative/dependency", "/dependency\0root"],
    ids=["non-string", "empty", "relative", "nul"],
)
def test_v3_invalid_dependency_root_spelling_is_rejected_by_validator_and_collector(
        tmp_path, invalid_root):
    snapshot, collected, _good_root, _missing_root = (
        _snapshot_only_v3_fixture(tmp_path, "invalid-root")
    )

    with pytest.raises(compiler_input.CompilerInputError):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
            current_dependency_prefix_roots=(invalid_root,),
        )
    with pytest.raises(compiler_input.CompilerInputError):
        compiler_input.collect_compiler_input_manifest(
            tmp_path / "invalid-root" / "build", snapshot, target=TARGET,
            origin_dependency_prefix_roots=(invalid_root,),
            current_dependency_prefix_roots=(),
        )


def test_v3_manifest_classifies_dependency_prefix_root_relative_and_rebinds_setwise(
        tmp_path):
    (
        snapshot, build, origin_match, origin_other,
        current_match, current_other, relative, payload,
    ) = _dependency_prefix_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(origin_other, origin_match),
        current_dependency_prefix_roots=(current_match, current_other),
    )

    assert collected.manifest["inputs"] == [{
        "root": "dependency-prefix",
        "path": relative.as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }]
    assert all(
        str(root) not in repr(collected.manifest)
        for root in (origin_match, origin_other, current_match, current_other)
    )

    import shutil
    shutil.rmtree(origin_match.parent)
    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=snapshot, target=TARGET,
        current_dependency_prefix_roots=(current_other, current_match),
    ) == collected.manifest


def test_v3_dependency_prefix_unit_binding_ignores_root_order_and_basename(
        tmp_path):
    first = _dependency_prefix_fixture(tmp_path, "first")
    second = _dependency_prefix_fixture(tmp_path, "second")
    renamed_second_current = second[4].with_name("different-prefix-name")
    second[4].rename(renamed_second_current)
    first_collected = compiler_input.collect_compiler_input_manifest(
        first[1], first[0], target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(first[3], first[2]),
        current_dependency_prefix_roots=(first[4], first[5]),
    )
    second_collected = compiler_input.collect_compiler_input_manifest(
        second[1], second[0], target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(second[2], second[3]),
        current_dependency_prefix_roots=(second[5], renamed_second_current),
    )

    assert first_collected == second_collected


@pytest.mark.parametrize("mutation", ["missing", "drift", "symlink", "directory"])
def test_v3_dependency_prefix_rejects_missing_drift_symlink_and_nonregular(
        tmp_path, mutation):
    (
        snapshot, build, origin_match, origin_other,
        current_match, current_other, relative, _payload,
    ) = _dependency_prefix_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(origin_match, origin_other),
        current_dependency_prefix_roots=(current_match, current_other),
    )
    leaf = current_match / relative
    if mutation == "missing":
        leaf.unlink()
    elif mutation == "drift":
        leaf.write_bytes(b"different dependency bytes\n")
    elif mutation == "symlink":
        replacement = current_match / "replacement.hh"
        replacement.write_bytes(leaf.read_bytes())
        leaf.unlink()
        leaf.symlink_to(replacement)
    else:
        leaf.unlink()
        leaf.mkdir()

    with pytest.raises(compiler_input.CompilerInputError):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
            current_dependency_prefix_roots=(current_match, current_other),
        )


def test_v3_dependency_prefix_rejects_ambiguous_current_root(tmp_path):
    (
        snapshot, build, origin_match, origin_other,
        current_match, current_other, relative, payload,
    ) = _dependency_prefix_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(origin_match, origin_other),
        current_dependency_prefix_roots=(current_match, current_other),
    )
    (current_other / relative).parent.mkdir()
    (current_other / relative).write_bytes(payload)

    with pytest.raises(compiler_input.CompilerInputError, match="one current root"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
            current_dependency_prefix_roots=(current_match, current_other),
        )


def test_v3_dependency_prefix_rejects_ambiguous_origin_without_filesystem_fallback(
        tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    outer = tmp_path / "prefix"
    inner = outer / "nested"
    header = inner / "include" / "portable.hh"
    header.parent.mkdir(parents=True)
    header.write_bytes(b"ambiguous origin\n")
    build = tmp_path / "build"
    _write_build_shape(build, snapshot, input_path=header)

    with pytest.raises(compiler_input.CompilerInputError, match="overlap|ambiguous"):
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET, allow_external_inputs=True,
            origin_dependency_prefix_roots=(outer, inner),
            current_dependency_prefix_roots=(outer, inner),
        )


def test_v3_filesystem_tag_cannot_alias_current_dependency_prefix_root(tmp_path):
    (
        snapshot, build, origin_match, origin_other,
        current_match, current_other, relative, _payload,
    ) = _dependency_prefix_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(origin_match, origin_other),
        current_dependency_prefix_roots=(current_match, current_other),
    )
    forged = copy.deepcopy(collected.manifest)
    forged["inputs"][0].update({
        "root": "filesystem",
        "path": str(current_match / relative).lstrip("/"),
    })

    with pytest.raises(compiler_input.CompilerInputError, match="root tag"):
        compiler_input.validate_compiler_input_manifest(
            forged, compiler_input.manifest_sha256(forged),
            snapshot_root=snapshot,
            current_dependency_prefix_roots=(current_match, current_other),
        )


def test_v2_does_not_accept_v3_dependency_prefix_tag(tmp_path):
    fixture = _dependency_prefix_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        fixture[1], fixture[0], target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(fixture[2], fixture[3]),
        current_dependency_prefix_roots=(fixture[4], fixture[5]),
    )
    old_schema = copy.deepcopy(collected.manifest)
    old_schema["schema_version"] = compiler_input.PREVIOUS_MANIFEST_SCHEMA

    with pytest.raises(compiler_input.CompilerInputError, match="root"):
        compiler_input.validate_compiler_input_manifest(
            old_schema, compiler_input.manifest_sha256(old_schema),
            snapshot_root=fixture[0],
        )


def test_v2_existing_snapshot_masstree_and_filesystem_roots_remain_accepted(
        tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot_input = snapshot / "include" / "snapshot.hh"
    snapshot_input.parent.mkdir(parents=True)
    snapshot_input.write_bytes(b"v2 snapshot\n")
    masstree = tmp_path / "fetchcontent" / "masstree-src"
    masstree_input = masstree / "include" / "masstree.hh"
    masstree_input.parent.mkdir(parents=True)
    masstree_input.write_bytes(b"v2 masstree\n")
    filesystem_input = tmp_path / "system" / "external.hh"
    filesystem_input.parent.mkdir()
    filesystem_input.write_bytes(b"v2 filesystem\n")
    manifest = {
        "schema_version": compiler_input.PREVIOUS_MANIFEST_SCHEMA,
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": TARGET,
        "depfile_count": 1,
        "input_policy": "snapshot-and-external-hashes/v1",
        "inputs": [
            {
                "root": "fetchcontent-masstree",
                "path": "include/masstree.hh",
                "sha256": hashlib.sha256(
                    masstree_input.read_bytes()
                ).hexdigest(),
            },
            {
                "root": "filesystem",
                "path": str(filesystem_input.resolve()).lstrip("/"),
                "sha256": hashlib.sha256(
                    filesystem_input.read_bytes()
                ).hexdigest(),
            },
            {
                "root": "snapshot",
                "path": "include/snapshot.hh",
                "sha256": hashlib.sha256(
                    snapshot_input.read_bytes()
                ).hexdigest(),
            },
        ],
    }

    assert compiler_input.validate_compiler_input_manifest(
        manifest, compiler_input.manifest_sha256(manifest),
        snapshot_root=snapshot,
        current_fetchcontent_masstree_root=masstree,
    ) == manifest


def test_v3_none_dependency_context_is_rejected_but_explicit_empty_is_accepted(
        tmp_path):
    snapshot, build = _fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        build, snapshot, target=TARGET,
    )

    with pytest.raises(compiler_input.CompilerInputError, match="context"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=snapshot,
        )
    assert compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=snapshot,
        current_dependency_prefix_roots=(),
    ) == collected.manifest


@pytest.mark.parametrize("path", [".", "//include/portable.hh"])
def test_v3_dependency_prefix_rejects_noncanonical_relative_paths(
        tmp_path, path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    manifest = {
        "schema_version": compiler_input.MANIFEST_SCHEMA,
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": TARGET,
        "depfile_count": 1,
        "input_policy": "snapshot-and-external-hashes/v1",
        "inputs": [{
            "root": "dependency-prefix",
            "path": path,
            "sha256": "0" * 64,
        }],
    }

    with pytest.raises(compiler_input.CompilerInputError, match="relative POSIX"):
        compiler_input.validate_compiler_input_manifest(
            manifest, compiler_input.manifest_sha256(manifest),
            snapshot_root=snapshot,
            current_dependency_prefix_roots=(),
        )


def test_v3_symlink_spelled_dependency_root_rebinds_identically(tmp_path):
    fixture = _dependency_prefix_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        fixture[1], fixture[0], target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(fixture[2], fixture[3]),
        current_dependency_prefix_roots=(fixture[4], fixture[5]),
    )
    alias = tmp_path / "current-root-alias"
    alias.symlink_to(fixture[4], target_is_directory=True)

    canonical = compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=fixture[0],
        current_dependency_prefix_roots=(fixture[4], fixture[5]),
    )
    through_alias = compiler_input.validate_compiler_input_manifest(
        collected.manifest, collected.manifest_sha256,
        snapshot_root=fixture[0],
        current_dependency_prefix_roots=(alias, fixture[5]),
    )
    assert through_alias == canonical


@pytest.mark.parametrize(
    "case",
    [
        "origin-snapshot", "current-snapshot",
        "origin-masstree", "current-masstree",
    ],
)
def test_v3_collector_rejects_all_dependency_root_class_overlaps(
        tmp_path, case):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    origin_masstree = tmp_path / "origin-masstree"
    current_masstree = tmp_path / "current-masstree"
    origin_masstree.mkdir()
    current_masstree.mkdir()
    safe_origin = tmp_path / "safe-origin"
    safe_current = tmp_path / "safe-current"
    safe_origin.mkdir()
    safe_current.mkdir()
    origin_dependency = safe_origin
    current_dependency = safe_current
    if case == "origin-snapshot":
        origin_dependency = snapshot
    elif case == "current-snapshot":
        current_dependency = snapshot
    elif case == "origin-masstree":
        origin_dependency = origin_masstree
    else:
        current_dependency = current_masstree
    build = tmp_path / "build"
    (snapshot / "include").mkdir()
    (snapshot / "include" / "unrelated.hh").write_bytes(b"overlap fixture\n")
    _write_build_shape(build, snapshot)

    with pytest.raises(compiler_input.CompilerInputError, match="overlap"):
        compiler_input.collect_compiler_input_manifest(
            build, snapshot, target=TARGET, allow_external_inputs=True,
            origin_fetchcontent_masstree_root=origin_masstree,
            current_fetchcontent_masstree_root=current_masstree,
            origin_dependency_prefix_roots=(origin_dependency,),
            current_dependency_prefix_roots=(current_dependency,),
        )


@pytest.mark.parametrize("case", ["snapshot", "masstree"])
def test_v3_validator_rejects_dependency_root_overlap_with_other_live_roots(
        tmp_path, case):
    fixture = _dependency_prefix_fixture(tmp_path)
    collected = compiler_input.collect_compiler_input_manifest(
        fixture[1], fixture[0], target=TARGET, allow_external_inputs=True,
        origin_dependency_prefix_roots=(fixture[2], fixture[3]),
        current_dependency_prefix_roots=(fixture[4], fixture[5]),
    )
    if case == "snapshot":
        roots = (fixture[0],)
        masstree = None
    else:
        masstree = tmp_path / "current-masstree"
        masstree.mkdir()
        roots = (masstree,)

    with pytest.raises(compiler_input.CompilerInputError, match="overlap"):
        compiler_input.validate_compiler_input_manifest(
            collected.manifest, collected.manifest_sha256,
            snapshot_root=fixture[0],
            current_fetchcontent_masstree_root=masstree,
            current_dependency_prefix_roots=roots,
        )


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
            current_dependency_prefix_roots=(),
        )


def test_legacy_v1_missing_absolute_input_remains_fail_closed(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    outside = tmp_path / "legacy-staging" / "header.hh"
    outside.parent.mkdir()
    outside.write_bytes(b"legacy external bytes\n")
    manifest = {
        "schema_version": compiler_input.LEGACY_MANIFEST_SCHEMA,
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": TARGET,
        "depfile_count": 1,
        "inputs": [{
            "path": str(outside.resolve()),
            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
        }],
        "input_policy": "snapshot-and-external-hashes/v1",
    }
    digest = compiler_input.manifest_sha256(manifest)
    outside.unlink()

    with pytest.raises(compiler_input.CompilerInputError, match="unavailable"):
        compiler_input.validate_compiler_input_manifest(
            manifest, digest, snapshot_root=snapshot, target=TARGET,
            current_fetchcontent_masstree_root=tmp_path / "unused-current-root",
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
            current_dependency_prefix_roots=(),
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
            current_dependency_prefix_roots=(),
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
