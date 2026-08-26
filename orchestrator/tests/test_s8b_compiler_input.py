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
