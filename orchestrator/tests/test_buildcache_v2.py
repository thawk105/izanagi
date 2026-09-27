# -*- coding: utf-8 -*-
"""buildcache v2 の contract namespace / 完成 manifest / 並行 claim 回帰。"""
from __future__ import annotations

import argparse
import contextlib
import ctypes
import errno
import hashlib
import inspect
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH.parent))

from orchestrator.campaign import buildcache  # noqa: E402
from orchestrator.campaign import sort_swo_dependency_material  # noqa: E402
from orchestrator.campaign import sort_swo_oracle  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    BuildAdmission,
    BuildAdmissionError,
    GeneratorId,
    ReviewId,
    add_coder_build_authority_argument,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
    verify_review_receipt,
)
from orchestrator.campaign.env_contract import (  # noqa: E402
    CalibrationRef,
    ExecutionEnvironmentContract,
    IsolationPolicy,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402
from orchestrator.campaign.source_digest import SourceEvidence  # noqa: E402
from orchestrator.tests.test_s8b_expected_materialization import (  # noqa: E402
    _SEALED_COMMAND_TIMEOUT_S,
)


_REQUIRED_SECURE_DIR_FD_FUNCTIONS = (
    "open", "stat", "mkdir", "rename", "unlink", "rmdir",
)


def _source_evidence(genome: Genome, commit: str, source_root: str) -> SourceEvidence:
    canonical = genome.canonical().encode("utf-8")
    return SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(Path(source_root).resolve()),
        ccbench_commit=commit,
        genome_sha256=hashlib.sha256(canonical).hexdigest(),
        src_token="stock",
        source_bytes_sha256=hashlib.sha256(b"stock-source").hexdigest(),
        tracked_clean=True,
        tracked_diff_sha256=hashlib.sha256(b"").hexdigest(),
        tracked_paths=(),
    )


def _admission_bundle(genome: Genome, commit: str, source_root: str):
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    evidence = _source_evidence(genome, commit, source_root)
    receipt = attest_generator_output(
        context, evidence, generator_input_sha256="1" * 64,
    )
    admission = derive_build_admission(
        context, evidence, generator_receipt=receipt,
    )
    return context, evidence, admission


def test_workload_identity_preserves_ycsb_golden_and_separates_tpcc():
    genome = Genome("silo", {"BACK_OFF": 1})
    _, _, admission = _admission_bundle(genome, "a" * 40, "/fixed/source")
    # Values from HEAD before workload support, using this fixed source root.
    legacy = buildcache.cache_key(genome, "a" * 40, False, admission=admission)
    assert legacy == "silo_c2d907920f_t0"
    assert buildcache.cache_key(
        genome, "a" * 40, False, admission=admission, workload="ycsb",
    ) == legacy
    assert buildcache.cache_key(
        genome, "a" * 40, False, admission=admission, workload="tpcc",
    ) != legacy
    args = (genome, "a" * 40, False, "stock", "test-cc", "test-cxx", {
        "cmake": {"realpath": "/cmake"},
        "cc": {"realpath": "/cc"},
        "cxx": {"realpath": "/cxx"},
    })
    kwargs = dict(site="other", dependency_prefix=[],
                  admission=dict(admission.as_cache_identity()))
    ycsb, ycsb_digest = buildcache._v2_identity(*args, **kwargs)
    assert ycsb_digest == (
        "f7da7e59a9c330609b86a8fae5a3dd3ae33ea0d33b3720729e1193eabf85ba5d"
    )
    assert buildcache._v2_identity(*args, workload="ycsb", **kwargs) == (
        ycsb, ycsb_digest,
    )
    assert "workload" not in ycsb
    tpcc, tpcc_digest = buildcache._v2_identity(
        *args, workload="tpcc", **kwargs,
    )
    assert tpcc["workload"] == "tpcc"
    assert tpcc_digest != ycsb_digest


@pytest.mark.parametrize("bad", ["TPCC", "", None, 1, True])
def test_invalid_build_workload_rejected(tmp_path, monkeypatch, bad):
    genome = Genome("silo", {"BACK_OFF": 1})
    _, _, admission = _admission_bundle(genome, "a" * 40, "/fixed/source")
    with pytest.raises(ValueError, match="workload"):
        buildcache.cache_key(genome, "a" * 40, False, admission=admission,
                             workload=bad)
    with pytest.raises(ValueError, match="workload"):
        buildcache._v2_identity(
            genome, "a" * 40, False, "stock", "cc", "cxx", {},
            site="other", dependency_prefix=[], admission={}, workload=bad,
        )
    with pytest.raises(ValueError, match="workload"):
        buildcache._v2_commands(
            genome, False, "/src", "/build", {}, workload=bad,
        )
    with pytest.raises(ValueError, match="workload"):
        _build(tmp_path, _contract(1), workload=bad)
    context, evidence, local_admission = _admission_bundle(
        genome, "a" * 40, str(tmp_path / "ccbench"),
    )
    with pytest.raises(ValueError, match="workload"):
        buildcache.build(
            genome, "a" * 40, False, workload=bad,
            admission=local_admission, build_context=context,
            source_evidence=evidence,
        )


def test_tpcc_fresh_hit_compiler_target_and_cross_workload_misses(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    collected = []
    real_collect = buildcache._collect_compiler_inputs

    def observe_collect(*args, **kwargs):
        collected.append(kwargs["target"])
        return real_collect(*args, **kwargs)

    monkeypatch.setattr(buildcache, "_collect_compiler_inputs", observe_collect)
    source = tmp_path / "ccbench"
    source.mkdir()
    (source / "compiler-input.hh").write_bytes(b"compiler input fixture\n")
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(source),
    )
    kwargs = dict(
        admission=admission, build_context=context, source_evidence=evidence,
        contract=_contract(1), ccbench_commit="a" * 40, trace=False,
        src_token="stock", cc="test-cc", cxx="test-cxx",
        cache_root=str(tmp_path / "cache"), ccbench_dir=str(source),
        source_snapshot_sha256=(
            buildcache.s8b_expected_materialization.snapshot_tree_digest(source)
        ),
    )
    tpcc = buildcache.build_v2(genome, workload="tpcc", **kwargs)
    assert not tpcc.cached
    assert Path(tpcc.binary).relative_to(tpcc.build_dir).as_posix() == (
        "cc/silo/tpcc_silo.exe"
    )
    assert tpcc.build_argv[tpcc.build_argv.index("--target") + 1] == "tpcc_silo.exe"
    assert tpcc.compiler_input_manifest["target"] == "tpcc_silo.exe"
    assert collected == ["tpcc_silo.exe"]
    hit_targets = []
    real_validate = buildcache.s8b_compiler_input.validate_compiler_input_manifest

    def observe_validate(*args, **kwargs):
        hit_targets.append(kwargs["target"])
        return real_validate(*args, **kwargs)

    monkeypatch.setattr(
        buildcache.s8b_compiler_input, "validate_compiler_input_manifest",
        observe_validate,
    )
    tpcc_hit = buildcache.build_v2(genome, workload="tpcc", **kwargs)
    assert tpcc_hit.cached and tpcc_hit.build_dir == tpcc.build_dir
    assert "tpcc_silo.exe" in hit_targets
    assert collected == ["tpcc_silo.exe"]
    ycsb = buildcache.build_v2(genome, **kwargs)
    assert not ycsb.cached and ycsb.build_dir != tpcc.build_dir
    assert ycsb.compiler_input_manifest["target"] == "ycsb_silo.exe"
    assert buildcache.build_v2(genome, **kwargs).cached
    assert buildcache.build_v2(genome, workload="tpcc", **kwargs).cached


def test_legacy_tpcc_target_and_cross_workload_misses(tmp_path, monkeypatch):
    _fake_build_environment(monkeypatch, tmp_path)
    source = tmp_path / "ccbench"
    source.mkdir()
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(source),
    )
    kwargs = dict(
        admission=admission, build_context=context, source_evidence=evidence,
        ccbench_dir=str(source), cache_root=str(tmp_path / "cache"),
        cc="test-cc", cxx="test-cxx",
    )
    tpcc = buildcache.build(genome, "a" * 40, False, workload="tpcc", **kwargs)
    assert not tpcc.cached
    assert Path(tpcc.binary).relative_to(tpcc.build_dir).as_posix() == (
        "cc/silo/tpcc_silo.exe"
    )
    assert tpcc.build_argv[tpcc.build_argv.index("--target") + 1] == "tpcc_silo.exe"
    assert buildcache.build(
        genome, "a" * 40, False, workload="tpcc", **kwargs,
    ).cached
    ycsb = buildcache.build(genome, "a" * 40, False, **kwargs)
    assert not ycsb.cached and ycsb.build_dir != tpcc.build_dir
    assert buildcache.build(genome, "a" * 40, False, **kwargs).cached


def _review_admission_bundle(
        genome: Genome, commit: str, source_root: str, *, input_sha256: str):
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    evidence = _source_evidence(genome, commit, source_root)
    unsigned = {
        "schema": "source-review/v1",
        "review_id": ReviewId.S8B_FLOOR.value,
        "source": evidence.as_receipt(),
        "input_sha256": input_sha256,
    }
    body = dict(unsigned)
    body["receipt_sha256"] = hashlib.sha256(json.dumps(
        unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()
    review = verify_review_receipt(
        ReviewId.S8B_FLOOR, evidence, receipt=body,
    )
    admission = derive_build_admission(
        context, evidence, review_receipt=review,
    )
    return context, evidence, admission


def _dirty_evidence(genome: Genome, commit: str, source_root: str) -> SourceEvidence:
    base = _source_evidence(genome, commit, source_root)
    return SourceEvidence(
        schema_version=base.schema_version,
        source_root=base.source_root,
        ccbench_commit=base.ccbench_commit,
        genome_sha256=base.genome_sha256,
        src_token="2" * 64,
        source_bytes_sha256="3" * 64,
        tracked_clean=False,
        tracked_diff_sha256="4" * 64,
        tracked_paths=("include/backoff.hh",),
    )


def _all_class_admissions(genome: Genome, source_root: str):
    stock_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    stock_evidence = _source_evidence(genome, CURRENT_PIN, source_root)
    stock = derive_build_admission(stock_context, stock_evidence)

    evidence = _dirty_evidence(genome, "a" * 40, source_root)
    machine_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    generator = attest_generator_output(
        machine_context, evidence, generator_input_sha256="1" * 64,
    )
    machine = derive_build_admission(
        machine_context, evidence, generator_receipt=generator,
    )

    review_unsigned = {
        "schema": "source-review/v1",
        "review_id": ReviewId.S1_KNOWN_AXES.value,
        "source": evidence.as_receipt(),
        "input_sha256": "5" * 64,
    }
    review_body = dict(review_unsigned)
    review_body["receipt_sha256"] = hashlib.sha256(
        json.dumps(
            review_unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    review = verify_review_receipt(
        ReviewId.S1_KNOWN_AXES, evidence, receipt=review_body,
    )
    human_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    human = derive_build_admission(human_context, evidence, review_receipt=review)

    parser = argparse.ArgumentParser()
    add_coder_build_authority_argument(parser)
    authority = parser.parse_args(["--allow-coder-derived-build"]).coder_build_authority
    coder_context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP, coder_authority=authority,
    )
    coder = derive_build_admission(coder_context, evidence)
    return stock, machine, human, coder


def _contract(seed: int) -> ExecutionEnvironmentContract:
    return ExecutionEnvironmentContract(
        env_tag=f"test-env-{seed}",
        clocks_per_us=1800 + seed,
        numactl=(),
        attestation_mode="none",
        isolation_policy=IsolationPolicy(single_process=False, allow_resume=True),
        calibration_ref=CalibrationRef(
            path=f"output/env/test-{seed}.json",
            sha256=f"{seed:064x}",
        ),
    )


def _write_tool(path: Path, first_line: str) -> None:
    path.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' {json.dumps(first_line)}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_multiline_tool(path: Path, lines: tuple[str, ...]) -> None:
    arguments = " ".join(json.dumps(line) for line in lines)
    path.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' {arguments}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _install_toolchain(tmp_path: Path, monkeypatch, *, cxx_version: str = "cxx version A") -> Path:
    bindir = tmp_path / "tools"
    bindir.mkdir(exist_ok=True)
    _write_tool(bindir / "test-cc", "cc version A")
    _write_tool(bindir / "test-cxx", cxx_version)
    _write_tool(bindir / "cmake", "cmake version A")
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    return bindir


def _expected_toolchain_manifest(bindir: Path) -> dict[str, object]:
    return {
        "cc": {
            "requested": "test-cc",
            "realpath": str((bindir / "test-cc").resolve()),
            "version_first_line": "cc version A",
            "version": "cc version A",
        },
        "cxx": {
            "requested": "test-cxx",
            "realpath": str((bindir / "test-cxx").resolve()),
            "version_first_line": "cxx version A",
            "version": "cxx version A",
        },
        "cmake": {
            "requested": "cmake",
            "realpath": str((bindir / "cmake").resolve()),
            "version_first_line": "cmake version A",
            "version": "cmake version A",
        },
    }


def _write_masstree_depend_info(
        build_dir: Path, pairs: tuple[tuple[Path | str, Path | str], ...]) -> None:
    target_dir = build_dir / "CMakeFiles" / "masstree_build.dir"
    target_dir.mkdir(parents=True, exist_ok=True)
    lines = ["set(CMAKE_MULTIPLE_OUTPUT_PAIRS\n"]
    lines.extend(f'  "{left}" "{right}"\n' for left, right in pairs)
    lines.append("  )\n")
    (target_dir / "DependInfo.cmake").write_text(
        "".join(lines), encoding="utf-8",
    )


def _fake_build_environment(
        monkeypatch, tmp_path: Path, payload: bytes = b"v2-binary", *,
        masstree_build_root: Path | str | None = None) -> None:
    monkeypatch.setattr(
        buildcache.site_policy, "current_site", lambda: buildcache.site_policy.OTHER,
    )
    monkeypatch.delenv("CMAKE_PREFIX_PATH", raising=False)
    monkeypatch.setattr(buildcache, "_ccbench_dir", lambda: str(tmp_path / "ccbench"))
    monkeypatch.setattr(buildcache, "_verify_ccbench_commit", lambda *a, **k: None)
    monkeypatch.setattr(
        buildcache,
        "source_digest",
        SimpleNamespace(
            STOCK="stock",
            assert_worktree_within_allowlist=lambda *a, **k: None,
            assert_trace_diff_matches_head=lambda *a, **k: None,
            resolve_evidence=lambda genome, commit, *, ccbench_dir, cxx: (
                _source_evidence(genome, commit, ccbench_dir)
            ),
        ),
    )
    monkeypatch.setattr(buildcache, "_assert_no_trace_symbols", lambda *a, **k: None)

    def fake_compiler_inputs(
            _build_dir, snapshot_root, *, target,
            allow_external_inputs=False,
            expected_evolve_block_sources=None,
            origin_fetchcontent_masstree_root=None,
            current_fetchcontent_masstree_root=None,
            origin_dependency_prefix_roots=(),
            current_dependency_prefix_roots=()):
        del expected_evolve_block_sources
        assert tuple(origin_dependency_prefix_roots) == tuple(
            current_dependency_prefix_roots
        )
        if allow_external_inputs:
            assert origin_fetchcontent_masstree_root is not None
            assert current_fetchcontent_masstree_root is not None
        else:
            assert origin_fetchcontent_masstree_root is None
            assert current_fetchcontent_masstree_root is None
        source = Path(snapshot_root).resolve() / "compiler-input.hh"
        payload = source.read_bytes()
        manifest = {
            "schema_version": buildcache.s8b_compiler_input.MANIFEST_SCHEMA,
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": target,
            "depfile_count": 1,
            "inputs": [{
                "root": "snapshot",
                "path": "compiler-input.hh",
                "sha256": hashlib.sha256(payload).hexdigest(),
            }],
        }
        if allow_external_inputs:
            manifest["input_policy"] = "snapshot-and-external-hashes/v1"
        return buildcache.s8b_compiler_input.CompilerInputManifest(
            manifest,
            buildcache.s8b_compiler_input.manifest_sha256(manifest),
        )

    monkeypatch.setattr(
        buildcache.s8b_compiler_input,
        "collect_compiler_input_manifest",
        fake_compiler_inputs,
    )

    def fake_run(cmd, what, timeout_s=None, *, site=None, env=None,
                 sealed_session=None, build_output=None):
        if sealed_session is not None:
            if what == "build":
                staging = Path(cmd[cmd.index("--build") + 1])
                assert build_output == str(staging / "cc" / "silo" / "ycsb_silo.exe")
            else:
                assert build_output is None
            # Run this existing synthetic compiler in the real sealed child,
            # including its metadata/binary writes to the shared staging tree.
            script = (
                "from pathlib import Path\n"
                + inspect.getsource(_write_masstree_depend_info)
                + f"\npayload = {payload!r}\n"
                + f"masstree_build_root = {str(masstree_build_root) if masstree_build_root is not None else None!r}\n"
                + textwrap.dedent(inspect.getsource(fake_run))
                + f"\nfake_run({cmd!r}, {what!r})\n"
            )
            completed = sealed_session.run(
                [sys.executable, "-I", "-B", "-c", script],
                cwd="/", env=env, timeout_s=(
                    _SEALED_COMMAND_TIMEOUT_S if timeout_s is None else timeout_s
                ),
                **({"build_output": build_output} if build_output is not None else {}),
            )
            assert completed.returncode == 0, completed.stderr
            return
        if what == "configure":
            bdir = Path(cmd[cmd.index("-B") + 1])
            bdir.mkdir(parents=True, exist_ok=True)
            base_tokens = [
                token for token in cmd
                if token.startswith("-DFETCHCONTENT_BASE_DIR=")
            ]
            if base_tokens:
                base = Path(base_tokens[0].split("=", 1)[1])
                masstree_tokens = [
                    token for token in cmd
                    if token.startswith("-DFETCHCONTENT_SOURCE_DIR_MASSTREE=")
                ]
                assert len(masstree_tokens) <= 1
                cache_lines = [
                    "CMAKE_GENERATOR:INTERNAL=Unix Makefiles\n",
                ]
                if masstree_tokens:
                    configured_root = Path(
                        masstree_tokens[0].split("=", 1)[1]
                    )
                    cache_lines.append(
                        "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH="
                        f"{configured_root}\n"
                    )
                else:
                    configured_root = base / "masstree-src"
                    cache_lines.append(
                        "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=\n"
                    )
                cache_lines.append(f"FETCHCONTENT_BASE_DIR:PATH={base}\n")
                if "-DFETCHCONTENT_FULLY_DISCONNECTED=ON" in cmd:
                    cache_lines.append(
                        "FETCHCONTENT_FULLY_DISCONNECTED:BOOL=ON\n"
                    )
            else:
                base = bdir / "_deps"
                configured_root = base / "masstree-src"
                cache_lines = [
                    "CMAKE_GENERATOR:INTERNAL=Unix Makefiles\n",
                    "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=\n",
                    f"FETCHCONTENT_BASE_DIR:PATH={base}\n",
                ]
            configured_root.mkdir(parents=True, exist_ok=True)
            (bdir / "CMakeCache.txt").write_text(
                "".join(cache_lines),
                encoding="utf-8",
            )
            generated_root = (
                Path(masstree_build_root)
                if masstree_build_root is not None
                else configured_root
            )
            _write_masstree_depend_info(
                bdir,
                ((
                    generated_root / "config.h",
                    generated_root / "libkohler_masstree_json.a",
                ),),
            )
        if what == "build":
            bdir = Path(cmd[cmd.index("--build") + 1])
            binary = bdir / "cc" / "silo" / cmd[cmd.index("--target") + 1]
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(payload)

    monkeypatch.setattr(buildcache, "_run", fake_run)


def _build(tmp_path: Path, contract: ExecutionEnvironmentContract, *, trace: bool = True,
           workload: str = "ycsb",
           ccbench_dir: str = "", timeout_s: int | None = None,
           source_snapshot_sha256: str | None = None,
           bind_source_snapshot: bool = False,
           expected_materialization_descriptor=None,
           dependency_prefix: str = "", site: str | None = None,
           expected_toolchain_manifest=None, fetchcontent_base_dir: str = "",
           fetchcontent_dependency_receipt=None, declared_use_class=None,
           fetchcontent_archive_sha256=None,
           post_oracle_dependency_binding=None,
           masstree_source_dir=None, mimalloc_source_dir=None,
           googletest_source_dir=None,
           current_compiler_input_masstree_root=None):
    genome = Genome("silo", {"BACK_OFF": 1})
    source_root = ccbench_dir or str(tmp_path / "ccbench")
    if bind_source_snapshot or source_snapshot_sha256 is not None:
        source_path = Path(source_root)
        source_path.mkdir(parents=True, exist_ok=True)
        snapshot_input = source_path / "compiler-input.hh"
        if not snapshot_input.exists():
            snapshot_input.write_bytes(b"compiler input fixture\n")
        if bind_source_snapshot:
            if source_snapshot_sha256 is not None:
                raise ValueError(
                    "bind_source_snapshot and source_snapshot_sha256 are exclusive"
                )
            source_snapshot_sha256 = (
                buildcache.s8b_expected_materialization.snapshot_tree_digest(
                    source_path.resolve(),
                )
            )
    if expected_materialization_descriptor is None:
        context, evidence, admission = _admission_bundle(
            genome, "a" * 40, source_root,
        )
    else:
        context, evidence, admission = _review_admission_bundle(
            genome, "a" * 40, source_root,
            input_sha256=(
                expected_materialization_descriptor.declaration_sha256
            ),
        )
    kwargs = dict(
        workload=workload,
        admission=admission,
        build_context=context,
        source_evidence=evidence,
        contract=contract,
        ccbench_commit="a" * 40,
        trace=trace,
        src_token="stock",
        cc="test-cc",
        cxx="test-cxx",
        cache_root=str(tmp_path / "cache"),
        ccbench_dir=ccbench_dir,
        timeout_s=timeout_s,
    )
    if source_snapshot_sha256 is not None:
        kwargs["source_snapshot_sha256"] = source_snapshot_sha256
    if expected_materialization_descriptor is not None:
        kwargs["expected_materialization_descriptor"] = (
            expected_materialization_descriptor
        )
    if dependency_prefix:
        kwargs["dependency_prefix"] = dependency_prefix
    if site is not None:
        kwargs["site"] = site
    if expected_toolchain_manifest is not None:
        kwargs["expected_toolchain_manifest"] = expected_toolchain_manifest
    if declared_use_class is not None:
        kwargs["declared_use_class"] = declared_use_class
    if fetchcontent_base_dir:
        kwargs["fetchcontent_base_dir"] = fetchcontent_base_dir
    if fetchcontent_dependency_receipt is not None:
        kwargs["fetchcontent_dependency_receipt"] = fetchcontent_dependency_receipt
    if fetchcontent_archive_sha256 is not None:
        kwargs["fetchcontent_archive_sha256"] = fetchcontent_archive_sha256
    if post_oracle_dependency_binding is not None:
        kwargs["post_oracle_dependency_binding"] = (
            post_oracle_dependency_binding
        )
    if masstree_source_dir is not None:
        kwargs["masstree_source_dir"] = masstree_source_dir
    if mimalloc_source_dir is not None:
        kwargs["mimalloc_source_dir"] = mimalloc_source_dir
    if googletest_source_dir is not None:
        kwargs["googletest_source_dir"] = googletest_source_dir
    if current_compiler_input_masstree_root is not None:
        kwargs["current_compiler_input_masstree_root"] = (
            current_compiler_input_masstree_root
        )
    return buildcache.build_v2(
        genome,
        **kwargs,
    )


def _dependency_receipt(*, config: str = "b") -> dict[str, str]:
    return {
        "masstree_head": "a" * 40,
        "config_sha256": config * 64,
    }


_FETCHCONTENT_FIXTURE_CONFIG_SHA256 = (
    "0026ab15b63efac9fe1189a05bc003de6583256ac00bab9fe54c11b76d60596f"
)
_FETCHCONTENT_FIXTURE_ARCHIVE_SHA256 = (
    "b82d14bd3717287c78a2e1351107a49a925192cae59c0f844437eed8a0d6caef"
)
_FETCHCONTENT_FIXTURE_FILES = {
    "config.h": b"fixture config\n",
    "libkohler_masstree_json.a": b"fixture archive\n",
    "tracked.hh": b"// pinned\n",
}


def _canonical_manifest(payloads: dict[str, bytes]) -> bytes:
    return b"".join(
        hashlib.sha256(payloads[relative]).hexdigest().encode("ascii")
        + b"  " + relative.encode("utf-8") + b"\n"
        for relative in sorted(payloads)
    )


def _write_fetchcontent_dependency(base: Path) -> dict[str, str]:
    source = base / "masstree-src"
    source.mkdir(parents=True)
    for relative, payload in _FETCHCONTENT_FIXTURE_FILES.items():
        path = source.joinpath(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(
        ["git", "-C", str(source), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(source), "config", "user.name", "Fixture"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(source), "add", "--", "tracked.hh"], check=True,
    )
    subprocess.run(
        ["git", "-C", str(source), "commit", "-qm", "fixture"], check=True,
    )
    head = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return {
        "masstree_head": head,
        "config_sha256": _FETCHCONTENT_FIXTURE_CONFIG_SHA256,
    }


def _post_oracle_binding(base: Path, receipt: dict[str, str]) -> dict[str, str]:
    source = base / "masstree-src"
    canonical = base / "oracle-canonical"
    canonical.mkdir()
    payloads = {
        "PIN": f"{receipt['masstree_head']}\n".encode("ascii"),
        "config.h": (source / "config.h").read_bytes(),
        "tracked.hh": (source / "tracked.hh").read_bytes(),
    }
    for relative, payload in payloads.items():
        (canonical / relative).write_bytes(payload)
    manifest = _canonical_manifest(payloads)
    (canonical / "SHA256SUMS").write_bytes(manifest)
    return {
        "fetchcontent_base_dir": str(base.resolve()),
        "oracle_dependency_root": str(canonical.resolve()),
        "dependency_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "masstree_head": receipt["masstree_head"],
        "config_sha256": receipt["config_sha256"],
        "archive_sha256": _FETCHCONTENT_FIXTURE_ARCHIVE_SHA256,
    }


def test_synthetic_production_dependency_series_uses_real_git_and_fails_closed(
        tmp_path):
    base = tmp_path / "fetchcontent"
    source = base / "masstree-src"
    source.mkdir(parents=True)
    fixture = _HERE / "fixtures" / "sort_swo_masstree"
    entries = tuple(
        line.split("  ", 1)[1]
        for line in (fixture / "SHA256SUMS").read_text(
            encoding="utf-8"
        ).splitlines()
    )
    tracked = tuple(sorted(set(entries) - {"PIN", "config.h"}))
    for relative in (*tracked, "config.h"):
        destination = source.joinpath(*relative.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fixture / relative, destination)
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(
        ["git", "-C", str(source), "add", "--", *tracked], check=True,
    )
    subprocess.run(
        [
            "git", "-C", str(source), "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid",
            "commit", "-qm", "synthetic production-series checkout",
        ],
        check=True,
    )
    head = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--verify", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    observed_tracked = subprocess.run(
        ["git", "-C", str(source), "ls-files", "--cached"],
        check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert head != "b3c5d054b66b08374d7a6ff5a0faeaf28b041a38"
    assert observed_tracked == list(tracked)

    with pytest.raises(
            sort_swo_dependency_material.CanonicalDependencyMaterialError
    ) as caught:
        sort_swo_dependency_material.materialize_canonical_dependency(
            source.resolve(), lease_parent=base.resolve(), expected_head=head,
        )
    error = caught.value
    assert error.detail_code == "canonical-manifest-mismatch"
    assert error.generated_manifest_sha256 is not None
    assert error.expected_manifest_sha256 == (
        sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256
    )
    assert error.generated_manifest_sha256 != error.expected_manifest_sha256
    assert error.generated_manifest_sha256 in str(error)
    assert error.expected_manifest_sha256 in str(error)
    assert list(base.glob(".sort-swo-dependency-*")) == []


def _write_cmake_cache(build_dir: Path, lines: tuple[str, ...]) -> None:
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "CMakeCache.txt").write_text(
        "".join(f"{line}\n" for line in lines), encoding="utf-8",
    )


def test_masstree_source_root_accepts_observed_source_dir_shape(tmp_path):
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent"
    root = base / "masstree-src"
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        f"FETCHCONTENT_BASE_DIR:PATH={base}",
        f"FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={root}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    assert "masstree_SOURCE_DIR" not in (
        build_dir / "CMakeCache.txt"
    ).read_text(encoding="utf-8")
    assert buildcache._masstree_source_root_from_cmake_cache(
        str(build_dir)
    ) == str(root.resolve())


def test_masstree_source_root_accepts_base_only_shape(tmp_path):
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent"
    root = base / "masstree-src"
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        f"FETCHCONTENT_BASE_DIR:PATH={base}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    assert buildcache._masstree_source_root_from_cmake_cache(
        str(build_dir)
    ) == str(root.resolve())


def test_masstree_source_root_accepts_observed_empty_source_dir_base_shape(
        tmp_path):
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent"
    root = base / "masstree-src"
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=",
        f"FETCHCONTENT_BASE_DIR:PATH={base}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    cache_lines = (build_dir / "CMakeCache.txt").read_text(
        encoding="utf-8",
    ).splitlines()
    assert cache_lines.count("FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=") == 1
    assert buildcache._masstree_source_root_from_cmake_cache(
        str(build_dir)
    ) == str(root.resolve())


@pytest.mark.parametrize(
    "invalid_source",
    (" ", "\t", '""'),
    ids=("space", "tab", "quoted-empty"),
)
def test_masstree_source_root_nonempty_empty_like_source_does_not_fallback(
        tmp_path, invalid_source):
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent"
    root = base / "masstree-src"
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        f"FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={invalid_source}",
        f"FETCHCONTENT_BASE_DIR:PATH={base}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(
            buildcache.BuildCacheError,
            match="FETCHCONTENT_SOURCE_DIR_MASSTREE .* NUL なし絶対 path"):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


def test_masstree_source_root_prefers_nonempty_source_over_base(tmp_path):
    build_dir = tmp_path / "build"
    source_root = tmp_path / "source-root"
    base = tmp_path / "fetchcontent"
    base_root = base / "masstree-src"
    assert source_root.resolve() != base_root.resolve()
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        f"FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={source_root}",
        f"FETCHCONTENT_BASE_DIR:PATH={base}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((source_root / "config.h"),
          (source_root / "libkohler_masstree_json.a")),),
    )

    assert buildcache._masstree_source_root_from_cmake_cache(
        str(build_dir)
    ) == str(source_root.resolve())


def test_masstree_source_root_rejects_base_depend_info_when_source_nonempty(
        tmp_path):
    build_dir = tmp_path / "build"
    source_root = tmp_path / "source-root"
    base = tmp_path / "fetchcontent"
    base_root = base / "masstree-src"
    assert source_root.resolve() != base_root.resolve()
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        f"FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={source_root}",
        f"FETCHCONTENT_BASE_DIR:PATH={base}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((base_root / "config.h"),
          (base_root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(buildcache.BuildCacheError, match="source root が一致しない"):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


@pytest.mark.parametrize(
    "base_kind",
    ("missing", "empty", "relative", "nul"),
    ids=("missing", "empty", "relative", "nul"),
)
def test_masstree_source_root_empty_source_requires_valid_base(
        tmp_path, base_kind):
    build_dir = tmp_path / "build"
    root = tmp_path / "expected" / "masstree-src"
    cache_entries = ["FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH="]
    if base_kind == "empty":
        cache_entries.append("FETCHCONTENT_BASE_DIR:PATH=")
    elif base_kind == "relative":
        cache_entries.append("FETCHCONTENT_BASE_DIR:PATH=relative")
    elif base_kind == "nul":
        cache_entries.append(
            f"FETCHCONTENT_BASE_DIR:PATH={tmp_path / 'base'}\0bad"
        )
    elif base_kind != "missing":  # pragma: no cover - parametrization contract
        raise AssertionError(base_kind)
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        *cache_entries,
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    match = (
        "解決 key がない"
        if base_kind == "missing"
        else "FETCHCONTENT_BASE_DIR .* NUL なし絶対 path"
    )
    with pytest.raises(buildcache.BuildCacheError, match=match):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


@pytest.mark.parametrize(
    "cache_entries",
    (
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=",
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=",
            "FETCHCONTENT_BASE_DIR:PATH={base}",
        ),
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=",
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={root}",
            "FETCHCONTENT_BASE_DIR:PATH={base}",
        ),
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=",
            "FETCHCONTENT_BASE_DIR:PATH={base}",
            "FETCHCONTENT_BASE_DIR:PATH={other_base}",
        ),
    ),
    ids=("double-empty-source", "mixed-source", "double-base"),
)
def test_masstree_source_root_empty_source_preserves_duplicate_rejection(
        tmp_path, cache_entries):
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent"
    root = base / "masstree-src"
    values = {
        "base": base,
        "root": root,
        "other_base": tmp_path / "other-fetchcontent",
    }
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        *(entry.format(**values) for entry in cache_entries),
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(buildcache.BuildCacheError, match="解決 key が一意"):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


def test_masstree_source_root_empty_source_rejects_depend_info_mismatch(
        tmp_path):
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent-a"
    other_root = tmp_path / "fetchcontent-b" / "masstree-src"
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=",
        f"FETCHCONTENT_BASE_DIR:PATH={base}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((other_root / "config.h"),
          (other_root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(buildcache.BuildCacheError, match="source root が一致しない"):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


@pytest.mark.parametrize(
    "generator_lines",
    (
        ("CMAKE_GENERATOR:INTERNAL=Ninja",),
        (),
        (
            "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
            "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        ),
    ),
    ids=("ninja", "missing", "duplicate"),
)
def test_masstree_source_root_rejects_unexpected_generator(
        tmp_path, generator_lines):
    build_dir = tmp_path / "build"
    root = tmp_path / "fetchcontent" / "masstree-src"
    _write_cmake_cache(
        build_dir,
        (*generator_lines, f"FETCHCONTENT_BASE_DIR:PATH={root.parent}"),
    )
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(buildcache.BuildCacheError, match="CMAKE_GENERATOR"):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


@pytest.mark.parametrize(
    "cache_entries",
    (
        (),
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=/first/masstree-src",
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=/second/masstree-src",
            "FETCHCONTENT_BASE_DIR:PATH=/expected",
        ),
        (
            "FETCHCONTENT_BASE_DIR:PATH=/first",
            "FETCHCONTENT_BASE_DIR:PATH=/second",
        ),
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=relative/masstree-src",
            "FETCHCONTENT_BASE_DIR:PATH=/expected",
        ),
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=",
            "FETCHCONTENT_BASE_DIR:PATH=/expected",
        ),
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=/expected/masstree-src\0bad",
            "FETCHCONTENT_BASE_DIR:PATH=/expected",
        ),
        ("FETCHCONTENT_BASE_DIR:PATH=relative",),
        ("FETCHCONTENT_BASE_DIR:PATH=/expected\0bad",),
    ),
    ids=(
        "missing", "duplicate-source", "duplicate-base", "relative-source",
        "empty-source", "nul-source", "relative-base", "nul-base",
    ),
)
def test_masstree_source_root_rejects_missing_duplicate_or_invalid_cache_key(
        tmp_path, cache_entries):
    build_dir = tmp_path / "build"
    root = tmp_path / "fetchcontent" / "masstree-src"
    _write_cmake_cache(
        build_dir,
        ("CMAKE_GENERATOR:INTERNAL=Unix Makefiles", *cache_entries),
    )
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(buildcache.BuildCacheError):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


@pytest.mark.parametrize(
    "cache_entries",
    (
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={root}",
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={other_root}",
            "FETCHCONTENT_BASE_DIR:PATH={base}",
        ),
        (
            "FETCHCONTENT_BASE_DIR:PATH={base}",
            "FETCHCONTENT_BASE_DIR:PATH={other_base}",
        ),
        (
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={root}",
            "FETCHCONTENT_BASE_DIR:PATH={base}",
            "FETCHCONTENT_BASE_DIR:PATH={other_base}",
        ),
    ),
    ids=("duplicate-source", "duplicate-base", "duplicate-unselected-base"),
)
def test_masstree_source_root_duplicate_cache_key_is_single_reason(
        tmp_path, cache_entries):
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent"
    root = base / "masstree-src"
    values = {
        "base": base,
        "root": root,
        "other_base": tmp_path / "other-fetchcontent",
        "other_root": tmp_path / "other-fetchcontent" / "masstree-src",
    }
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        *(entry.format(**values) for entry in cache_entries),
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(buildcache.BuildCacheError, match="解決 key が一意"):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


@pytest.mark.parametrize(
    "relative_surface",
    ("source-dir", "base-dir", "depend-info"),
    ids=("source-dir", "base-dir", "depend-info"),
)
def test_masstree_source_root_relative_path_is_single_reason(
        tmp_path, monkeypatch, relative_surface):
    monkeypatch.chdir(tmp_path)
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent"
    root = base / "masstree-src"
    cache_entries = []
    if relative_surface == "source-dir":
        cache_entries.append(
            "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=fetchcontent/masstree-src"
        )
    elif relative_surface == "base-dir":
        cache_entries.append("FETCHCONTENT_BASE_DIR:PATH=fetchcontent")
    else:
        cache_entries.append(f"FETCHCONTENT_BASE_DIR:PATH={base}")
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        *cache_entries,
    ))
    if relative_surface == "depend-info":
        generated_root: Path | str = "fetchcontent/masstree-src"
    else:
        generated_root = root
    _write_masstree_depend_info(
        build_dir,
        ((
            f"{generated_root}/config.h",
            f"{generated_root}/libkohler_masstree_json.a",
        ),),
    )

    with pytest.raises(buildcache.BuildCacheError, match="NUL なし絶対 path"):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


@pytest.mark.parametrize(
    "invalid_source",
    ("relative/masstree-src", "/invalid/masstree-src\0bad"),
    ids=("relative", "nul"),
)
def test_masstree_source_root_nonempty_invalid_source_does_not_fallback(
        tmp_path, invalid_source):
    build_dir = tmp_path / "build"
    base = tmp_path / "fetchcontent"
    root = base / "masstree-src"
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        f"FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={invalid_source}",
        f"FETCHCONTENT_BASE_DIR:PATH={base}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(
            buildcache.BuildCacheError,
            match="FETCHCONTENT_SOURCE_DIR_MASSTREE .* NUL なし絶対 path"):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


@pytest.mark.parametrize(
    "depend_shape",
    (
        "missing", "zero-pairs", "two-pairs", "different-parents", "relative",
        "wrong-basename", "nul",
    ),
)
def test_masstree_source_root_rejects_invalid_depend_info(
        tmp_path, depend_shape):
    build_dir = tmp_path / "build"
    root = tmp_path / "fetchcontent" / "masstree-src"
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        f"FETCHCONTENT_BASE_DIR:PATH={root.parent}",
    ))
    if depend_shape == "zero-pairs":
        _write_masstree_depend_info(build_dir, ())
    elif depend_shape == "two-pairs":
        pair = (root / "config.h", root / "libkohler_masstree_json.a")
        _write_masstree_depend_info(build_dir, (pair, pair))
    elif depend_shape == "different-parents":
        _write_masstree_depend_info(
            build_dir,
            (((root / "config.h"), (tmp_path / "other" / "libkohler_masstree_json.a")),),
        )
    elif depend_shape == "relative":
        _write_masstree_depend_info(
            build_dir,
            (("relative/config.h", "relative/libkohler_masstree_json.a"),),
        )
    elif depend_shape == "wrong-basename":
        _write_masstree_depend_info(
            build_dir,
            ((root / "not-config.h", root / "libkohler_masstree_json.a"),),
        )
    elif depend_shape == "nul":
        _write_masstree_depend_info(
            build_dir,
            ((f"{root / 'config.h'}\0bad", root / "libkohler_masstree_json.a"),),
        )
    elif depend_shape != "missing":  # pragma: no cover - parametrization contract
        raise AssertionError(depend_shape)

    with pytest.raises(buildcache.BuildCacheError):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


def test_masstree_source_root_rejects_legacy_lowercase_key_only(tmp_path):
    build_dir = tmp_path / "build"
    root = tmp_path / "fetchcontent" / "masstree-src"
    _write_cmake_cache(build_dir, (
        "CMAKE_GENERATOR:INTERNAL=Unix Makefiles",
        f"masstree_SOURCE_DIR:STATIC={root}",
    ))
    _write_masstree_depend_info(
        build_dir,
        (((root / "config.h"), (root / "libkohler_masstree_json.a")),),
    )

    with pytest.raises(buildcache.BuildCacheError):
        buildcache._masstree_source_root_from_cmake_cache(str(build_dir))


def test_v2_fetchcontent_dependency_receipt_requires_exact_head_config_schema():
    receipt = _dependency_receipt()
    assert buildcache._validate_fetchcontent_dependency_receipt(receipt) == receipt
    invalid = [
        {**receipt, "archive_sha256": "c" * 64},
        {"masstree_head": receipt["masstree_head"]},
        {**receipt, "config_sha256": "not-a-sha256"},
        {**receipt, "masstree_head": "not-a-head"},
    ]
    for candidate in invalid:
        with pytest.raises(buildcache.BuildCacheError):
            buildcache._validate_fetchcontent_dependency_receipt(candidate)


def test_v2_post_oracle_rejects_legacy_five_key_capability(tmp_path):
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)
    binding.pop("oracle_dependency_root")

    with pytest.raises(buildcache.BuildCacheError, match="exact key"):
        _build(
            tmp_path, _contract(1),
            post_oracle_dependency_binding=binding,
        )


def test_v2_post_oracle_cache_hit_rechecks_two_roots_before_return(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)
    first = _build(
        tmp_path, _contract(1), post_oracle_dependency_binding=binding,
    )
    assert first.cached is False

    original_validate = buildcache._validate_v2_entry

    def validate_then_drift(*args, **kwargs):
        result = original_validate(*args, **kwargs)
        (base / "masstree-src" / "tracked.hh").write_text(
            "// cache-hit drift\n", encoding="utf-8",
        )
        return result

    monkeypatch.setattr(buildcache, "_validate_v2_entry", validate_then_drift)
    with pytest.raises(buildcache.BuildCacheError, match="canonical-source-drift"):
        _build(
            tmp_path, _contract(1), post_oracle_dependency_binding=binding,
        )


def test_v2_post_oracle_canonical_path_is_not_cache_identity(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base_a = tmp_path / "fetchcontent-a"
    base_a.mkdir()
    receipt_a = _write_fetchcontent_dependency(base_a)
    binding_a = _post_oracle_binding(base_a, receipt_a)
    first = _build(
        tmp_path, _contract(1), post_oracle_dependency_binding=binding_a,
    )

    base_b = tmp_path / "fetchcontent-b"
    base_b.mkdir()
    shutil.copytree(base_a / "masstree-src", base_b / "masstree-src")
    receipt_b = {
        "masstree_head": receipt_a["masstree_head"],
        "config_sha256": receipt_a["config_sha256"],
    }
    binding_b = _post_oracle_binding(base_b, receipt_b)
    second = _build(
        tmp_path, _contract(1), post_oracle_dependency_binding=binding_b,
    )

    assert first.cached is False
    assert second.cached is True
    assert binding_a["oracle_dependency_root"] != (
        binding_b["oracle_dependency_root"]
    )
    assert first.build_dir == second.build_dir


def test_v2_post_oracle_flag_is_exact_one_and_generic_base_only_stays_zero(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)

    post_oracle = _build(
        tmp_path, _contract(1),
        post_oracle_dependency_binding=binding,
    )
    generic = _build(
        tmp_path, _contract(1),
        fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
    )

    flag = "-DFETCHCONTENT_FULLY_DISCONNECTED=ON"
    assert post_oracle.configure_argv.count(flag) == 1
    assert generic.configure_argv.count(flag) == 0
    assert not post_oracle.cached
    assert not generic.cached
    assert post_oracle.build_dir != generic.build_dir


def test_v2_post_oracle_policy_forces_miss_against_same_material_generic_entry(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)

    generic = _build(
        tmp_path, _contract(1),
        fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
        fetchcontent_archive_sha256=_FETCHCONTENT_FIXTURE_ARCHIVE_SHA256,
    )
    post_oracle = _build(
        tmp_path, _contract(1),
        fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
        fetchcontent_archive_sha256=_FETCHCONTENT_FIXTURE_ARCHIVE_SHA256,
        post_oracle_dependency_binding=binding,
    )

    assert not generic.cached
    assert not post_oracle.cached
    assert generic.build_dir != post_oracle.build_dir


def test_v2_post_oracle_rejects_self_consistent_rewritten_manifest_authority(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)
    canonical = Path(binding["oracle_dependency_root"])
    changed_tracked = b"// changed with self-consistent manifest\n"
    (canonical / "tracked.hh").write_bytes(changed_tracked)
    payloads = {
        relative: (canonical / relative).read_bytes()
        for relative in ("PIN", "config.h", "tracked.hh")
    }
    (canonical / "SHA256SUMS").write_bytes(_canonical_manifest(payloads))
    calls = []
    original_run = buildcache._run

    def record_run(*args, **kwargs):
        calls.append((args, kwargs))
        return original_run(*args, **kwargs)

    monkeypatch.setattr(buildcache, "_run", record_run)
    with pytest.raises(buildcache.BuildCacheError, match="canonical-manifest-mismatch"):
        _build(
            tmp_path, _contract(1),
            post_oracle_dependency_binding=binding,
        )
    assert calls == []


def test_v2_post_oracle_manifest_rejects_changed_declared_non_config_file(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)
    source = base / "masstree-src"
    (source / "tracked.hh").write_text(
        "// changed after oracle\n", encoding="utf-8",
    )

    assert buildcache._observe_fetchcontent_dependency_receipt(
        str(source.resolve())
    ) == receipt
    assert hashlib.sha256(
        (source / "config.h").read_bytes()
    ).hexdigest() == receipt["config_sha256"]
    with pytest.raises(buildcache.BuildCacheError, match="canonical-source-drift"):
        _build(
            tmp_path, _contract(1),
            post_oracle_dependency_binding=binding,
        )


def test_v2_post_oracle_config_mismatch_refuses_before_configure(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)
    (base / "masstree-src" / "config.h").write_bytes(
        b"changed after oracle\n"
    )
    calls = []
    original_run = buildcache._run

    def record_run(*args, **kwargs):
        calls.append((args, kwargs))
        return original_run(*args, **kwargs)

    monkeypatch.setattr(buildcache, "_run", record_run)
    with pytest.raises(buildcache.BuildCacheError, match="canonical-source-drift"):
        _build(
            tmp_path, _contract(1),
            post_oracle_dependency_binding=binding,
        )
    assert calls == []


def test_v2_post_oracle_effective_disconnected_off_refuses_before_build(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)
    calls = []
    original_run = buildcache._run

    def force_effective_off(cmd, what, **kwargs):
        calls.append(what)
        original_run(cmd, what, **kwargs)
        if what == "configure":
            staging = Path(cmd[cmd.index("-B") + 1])
            cache = staging / "CMakeCache.txt"
            cache.write_text(
                cache.read_text(encoding="utf-8").replace(
                    "FETCHCONTENT_FULLY_DISCONNECTED:BOOL=ON",
                    "FETCHCONTENT_FULLY_DISCONNECTED:BOOL=OFF",
                ),
                encoding="utf-8",
            )

    monkeypatch.setattr(buildcache, "_run", force_effective_off)
    with pytest.raises(buildcache.BuildCacheError, match="実効値.*exact ON"):
        _build(
            tmp_path, _contract(1),
            post_oracle_dependency_binding=binding,
        )
    assert calls == ["configure"]


def test_v2_post_oracle_effective_root_mismatch_never_starts_build(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    binding_base = tmp_path / "fetchcontent-binding"
    binding_base.mkdir()
    receipt = _write_fetchcontent_dependency(binding_base)
    binding = _post_oracle_binding(binding_base, receipt)
    configured_base = tmp_path / "fetchcontent-configured"
    configured_base.mkdir()
    shutil.copytree(
        binding_base / "masstree-src",
        configured_base / "masstree-src",
    )
    mimalloc = configured_base / "mimalloc-src"
    googletest = configured_base / "googletest-src"
    mimalloc.mkdir()
    googletest.mkdir()
    events = []
    original_run = buildcache._run

    def record_run(cmd, what, **kwargs):
        events.append(what)
        return original_run(cmd, what, **kwargs)

    monkeypatch.setattr(buildcache, "_run", record_run)
    with pytest.raises(Exception):
        _build(
            tmp_path, _contract(1),
            post_oracle_dependency_binding=binding,
            masstree_source_dir=(configured_base / "masstree-src").resolve(),
            mimalloc_source_dir=mimalloc.resolve(),
            googletest_source_dir=googletest.resolve(),
        )
    assert events == ["configure"]


def test_v2_post_oracle_build_cannot_rewrite_identical_material_bytes(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    binding = _post_oracle_binding(base, receipt)
    source = base / "masstree-src"
    targets = (
        source / "config.h",
        source / "libkohler_masstree_json.a",
    )
    rewrite_failures = []
    original_run = buildcache._run

    def attempt_identical_rewrite(cmd, what, **kwargs):
        original_run(cmd, what, **kwargs)
        if what == "build":
            for target in targets:
                payload = target.read_bytes()
                try:
                    target.write_bytes(payload)
                except PermissionError:
                    rewrite_failures.append(target.name)

    monkeypatch.setattr(buildcache, "_run", attempt_identical_rewrite)
    result = _build(
        tmp_path, _contract(1),
        site=buildcache.site_policy.OTHER,
        post_oracle_dependency_binding=binding,
    )

    assert result.cached is False
    assert rewrite_failures == [
        "config.h", "libkohler_masstree_json.a",
    ]


def test_v2_generic_build_does_not_enter_post_oracle_protection_or_change_argv(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)

    def unexpected_protection(*_args, **_kwargs):
        raise AssertionError("generic build entered post-oracle protection")

    monkeypatch.setattr(
        sort_swo_dependency_material,
        "protect_post_oracle_dependency_material",
        unexpected_protection,
    )
    result = _build(
        tmp_path, _contract(1),
        fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
    )
    expected_argv = (
        str((bindir / "cmake").resolve()),
        "-S", result.ccbench_root,
        "-B", result.build_dir,
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_SANITIZER=OFF",
        f"-DCMAKE_C_COMPILER={(bindir / 'test-cc').resolve()}",
        f"-DCMAKE_CXX_COMPILER={(bindir / 'test-cxx').resolve()}",
        f"-DFETCHCONTENT_BASE_DIR={base.resolve()}",
        *Genome("silo", {"BACK_OFF": 1}).cmake_defines(),
        "-DCCBENCH_TRACE=1",
    )

    assert result.configure_argv == expected_argv


def test_v2_post_oracle_policy_separates_only_bound_identity():
    genome = Genome("silo", {"BACK_OFF": 1})
    toolchain = {
        role: {
            "requested": role,
            "realpath": f"/tool/{role}",
            "version_first_line": "v1",
        }
        for role in ("cc", "cxx", "cmake")
    }
    common = dict(
        site="test", dependency_prefix=[], admission={"receipt": "fixture"},
    )
    unbound = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        **common,
    )
    explicit_unbound = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        fetchcontent_population_policy=None,
        fetchcontent_dependency_manifest_sha256=None,
        **common,
    )
    base_bound = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        fetchcontent_dependency_receipt=_dependency_receipt(),
        fetchcontent_archive_sha256="c" * 64,
        **common,
    )
    post_oracle = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        fetchcontent_dependency_receipt=_dependency_receipt(),
        fetchcontent_archive_sha256="c" * 64,
        fetchcontent_population_policy=(
            "post-oracle-fully-disconnected-manifest-bound/v1"
        ),
        fetchcontent_dependency_manifest_sha256="d" * 64,
        **common,
    )

    assert unbound == explicit_unbound
    assert base_bound[1] != post_oracle[1]
    assert "fetchcontent_population_policy" not in base_bound[0]
    assert post_oracle[0]["fetchcontent_population_policy"] == (
        "post-oracle-fully-disconnected-manifest-bound/v1"
    )


def test_v2_cache_and_generated_masstree_roots_must_match_before_publish(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    outside_root = tmp_path / "outside" / "masstree-src"
    _fake_build_environment(
        monkeypatch, tmp_path, masstree_build_root=outside_root,
    )
    expected_base = tmp_path / "fetchcontent"
    expected_base.mkdir()
    receipt = _write_fetchcontent_dependency(expected_base)

    with pytest.raises(
            buildcache.BuildCacheError,
            match="CMakeCache.txt .* DependInfo.cmake"):
        _build(
            tmp_path, _contract(1),
            fetchcontent_base_dir=str(expected_base.resolve()),
            fetchcontent_dependency_receipt=receipt,
        )
    assert list((tmp_path / "cache").rglob("completion.json")) == []


def test_v2_fetchcontent_base_is_canonical_single_define_and_receipt_in_preimage(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    result = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
    )
    hit = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
    )
    base_defines = [
        token for token in result.configure_argv
        if token.startswith("-DFETCHCONTENT_BASE_DIR=")
    ]
    assert base_defines == [f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"]
    assert not any(
        token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
        for token in result.configure_argv
    )
    assert not result.cached
    assert hit.cached
    assert hit.masstree_source_root_sha256 == result.masstree_source_root_sha256
    manifest = json.loads(
        (Path(result.build_dir) / "completion.json").read_text(encoding="utf-8")
    )
    assert manifest["preimage"]["fetchcontent_dependency_receipt"] == (
        receipt
    )
    assert "fetchcontent_transport_mode" not in manifest["preimage"]
    assert manifest["completion_marker"] == "complete"
    assert str(base.resolve()) not in json.dumps(
        manifest["preimage"], sort_keys=True,
    )


def test_v2_cache_hit_reuses_same_content_receipt_across_distinct_bases(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base_a = tmp_path / "fetchcontent-a"
    base_a.mkdir()
    receipt = _write_fetchcontent_dependency(base_a)
    first = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base_a.resolve()),
        fetchcontent_dependency_receipt=receipt,
    )
    base_b = tmp_path / "fetchcontent-b"
    base_b.mkdir()
    shutil.copytree(base_a / "masstree-src", base_b / "masstree-src")
    (base_b / "masstree-src" / "libkohler_masstree_json.a").write_bytes(
        b"different archive from another valid build path\n"
    )
    second = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base_b.resolve()),
        fetchcontent_dependency_receipt=receipt,
    )
    assert not first.cached
    assert second.cached
    assert second.build_dir == first.build_dir
    assert second.fetchcontent_base_dir == str(base_b.resolve())
    assert second.masstree_source_root_sha256 == hashlib.sha256(
        str(base_a.resolve() / "masstree-src").encode("utf-8")
    ).hexdigest()


def test_v2_run_local_archive_observations_allow_distinct_build_bytes_across_runs(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    ccbench = tmp_path / "ccbench"
    ccbench.mkdir()
    generated_archives = {}
    prebuild_targets = []
    original_run = buildcache._run

    def generate_archive_from_prebuild(cmd, what, **kwargs):
        original_run(cmd, what, **kwargs)
        if what == "build" and cmd[cmd.index("--target") + 1] == "masstree_build":
            build_dir = Path(cmd[cmd.index("--build") + 1])
            base = build_dir.parent.resolve()
            (base / "masstree-src" / "libkohler_masstree_json.a").write_bytes(
                generated_archives[base]
            )
            prebuild_targets.append(base)

    monkeypatch.setattr(buildcache, "_run", generate_archive_from_prebuild)

    def prebuild(base, payload):
        generated_archives[base.resolve()] = payload
        buildcache.prepare_masstree_fetchcontent(
            ccbench_dir=str(ccbench.resolve()),
            fetchcontent_base_dir=str(base.resolve()),
            expected_toolchain_manifest=_expected_toolchain_manifest(bindir),
            configure_timeout_s=11, target_timeout_s=13,
        )

    base_a = tmp_path / "fetchcontent-a"
    base_a.mkdir()
    receipt = _write_fetchcontent_dependency(base_a)
    prebuild(base_a, b"archive produced by valid prebuild run A\n")
    archive_a = base_a / "masstree-src" / "libkohler_masstree_json.a"
    hash_a = hashlib.sha256(archive_a.read_bytes()).hexdigest()
    first = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base_a.resolve()),
        fetchcontent_dependency_receipt=receipt,
        fetchcontent_archive_sha256=hash_a,
    )

    base_b = tmp_path / "fetchcontent-b"
    base_b.mkdir()
    shutil.copytree(base_a / "masstree-src", base_b / "masstree-src")
    archive_b = base_b / "masstree-src" / "libkohler_masstree_json.a"
    prebuild(base_b, b"archive produced by valid prebuild run B\n")
    hash_b = hashlib.sha256(archive_b.read_bytes()).hexdigest()
    second = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base_b.resolve()),
        fetchcontent_dependency_receipt=receipt,
        fetchcontent_archive_sha256=hash_b,
    )

    assert hash_a != hash_b
    assert prebuild_targets == [base_a.resolve(), base_b.resolve()]
    assert not first.cached and not second.cached
    assert first.build_dir != second.build_dir
    for result, expected in ((first, hash_a), (second, hash_b)):
        manifest = json.loads(
            (Path(result.build_dir) / "completion.json").read_text(
                encoding="utf-8"
            )
        )
        assert manifest["preimage"]["fetchcontent_archive_sha256"] == expected
        assert manifest["fetchcontent_dependency"]["archive_sha256"] == expected


def test_v2_run_local_archive_replacement_during_fresh_build_is_rejected(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    archive = base / "masstree-src" / "libkohler_masstree_json.a"
    expected_archive_sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()
    original_run = buildcache._run

    def replace_archive_after_build(cmd, what, **kwargs):
        original_run(cmd, what, **kwargs)
        if what == "build":
            archive.write_bytes(b"same-run replacement after build\n")

    monkeypatch.setattr(buildcache, "_run", replace_archive_after_build)
    with pytest.raises(
            buildcache.BuildCacheError,
            match="archive が build 中に変化"):
        _build(
            tmp_path, _contract(1),
            fetchcontent_base_dir=str(base.resolve()),
            fetchcontent_dependency_receipt=receipt,
            fetchcontent_archive_sha256=expected_archive_sha256,
        )
    assert list((tmp_path / "cache").rglob("completion.json")) == []


def test_v2_run_local_archive_replacement_during_cache_hit_is_rejected(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    archive = base / "masstree-src" / "libkohler_masstree_json.a"
    expected_archive_sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()
    first = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
        fetchcontent_archive_sha256=expected_archive_sha256,
    )
    assert not first.cached

    original_recheck = buildcache._recheck_source_evidence

    def replace_archive_during_hit(*args, **kwargs):
        original_recheck(*args, **kwargs)
        archive.write_bytes(b"same-run replacement during cache hit\n")

    monkeypatch.setattr(
        buildcache, "_recheck_source_evidence", replace_archive_during_hit,
    )
    with pytest.raises(
            buildcache.BuildCacheError,
            match="archive が cache hit 中に変化"):
        _build(
            tmp_path, _contract(1),
            fetchcontent_base_dir=str(base.resolve()),
            fetchcontent_dependency_receipt=receipt,
            fetchcontent_archive_sha256=expected_archive_sha256,
        )


def test_v2_dependency_drift_before_publish_leaves_no_completed_cache_entry(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    config = base / "masstree-src" / "config.h"
    original_run = buildcache._run
    mutate = True

    def drift_after_build(cmd, what, **kwargs):
        nonlocal mutate
        original_run(cmd, what, **kwargs)
        if what == "build" and mutate:
            config.write_bytes(b"drifted config\n")

    monkeypatch.setattr(buildcache, "_run", drift_after_build)
    with pytest.raises(
            buildcache.BuildCacheError,
            match="dependency 内容が build 中に変化"):
        _build(
            tmp_path, _contract(1), fetchcontent_base_dir=str(base.resolve()),
            fetchcontent_dependency_receipt=receipt,
        )
    assert list((tmp_path / "cache").rglob("completion.json")) == []

    config.write_bytes(b"fixture config\n")
    mutate = False
    claims = list((tmp_path / "cache").rglob("*.building"))
    assert len(claims) == 1
    assert claims[0].is_dir()
    assert (claims[0] / "owner.json").is_file()
    shutil.rmtree(claims[0])
    rebuilt = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
    )
    assert not rebuilt.cached


def test_v2_wrong_effective_root_never_publishes_or_hits_same_key(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    expected_base = tmp_path / "fetchcontent-expected"
    expected_base.mkdir()
    receipt = _write_fetchcontent_dependency(expected_base)
    wrong_base = tmp_path / "fetchcontent-wrong"
    wrong_base.mkdir()
    shutil.copytree(
        expected_base / "masstree-src", wrong_base / "masstree-src",
    )
    original_run = buildcache._run
    inject_wrong_root = True

    def replace_effective_root_after_configure(cmd, what, **kwargs):
        original_run(cmd, what, **kwargs)
        if what == "configure" and inject_wrong_root:
            staging = Path(cmd[cmd.index("-B") + 1])
            (staging / "CMakeCache.txt").write_text(
                "CMAKE_GENERATOR:INTERNAL=Unix Makefiles\n"
                f"FETCHCONTENT_BASE_DIR:PATH={expected_base.resolve()}\n"
                "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH="
                f"{wrong_base.resolve() / 'masstree-src'}\n",
                encoding="utf-8",
            )
            wrong_root = wrong_base.resolve() / "masstree-src"
            _write_masstree_depend_info(
                staging,
                (((wrong_root / "config.h"),
                  (wrong_root / "libkohler_masstree_json.a")),),
            )

    monkeypatch.setattr(buildcache, "_run", replace_effective_root_after_configure)
    with pytest.raises(
            buildcache.BuildCacheError,
            match="実効 source root が期待値と不一致"):
        _build(
            tmp_path, _contract(1),
            fetchcontent_base_dir=str(expected_base.resolve()),
            fetchcontent_dependency_receipt=receipt,
        )
    assert list((tmp_path / "cache").rglob("completion.json")) == []

    claims = list((tmp_path / "cache").rglob("*.building"))
    assert len(claims) == 1
    shutil.rmtree(claims[0])
    inject_wrong_root = False
    rebuilt = _build(
        tmp_path, _contract(1),
        fetchcontent_base_dir=str(expected_base.resolve()),
        fetchcontent_dependency_receipt=receipt,
    )
    assert not rebuilt.cached


def test_v2_fetchcontent_receipt_change_misses_and_empty_default_preserves_identity(
        tmp_path):
    genome = Genome("silo", {"BACK_OFF": 1})
    toolchain = {
        role: {"requested": role, "realpath": f"/tool/{role}", "version_first_line": "v1"}
        for role in ("cc", "cxx", "cmake")
    }
    kwargs = dict(
        site="test", dependency_prefix=[], admission={"receipt": "fixture"},
    )
    legacy = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain, **kwargs,
    )
    explicit_empty = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        fetchcontent_dependency_receipt=None, **kwargs,
    )
    changed = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        fetchcontent_dependency_receipt=_dependency_receipt(config="d"), **kwargs,
    )
    baseline = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        fetchcontent_dependency_receipt=_dependency_receipt(), **kwargs,
    )
    assert legacy == explicit_empty
    assert changed[1] != baseline[1]


def test_prepare_masstree_fetchcontent_configures_then_builds_exact_target(
        tmp_path, monkeypatch):
    base = tmp_path / "base"
    source = tmp_path / "ccbench"
    base.mkdir()
    source.mkdir()
    calls = []
    monkeypatch.setattr(buildcache, "_run", lambda cmd, what, **kwargs: calls.append((cmd, what, kwargs)))
    monkeypatch.setattr(
        buildcache.site_policy, "current_site", lambda: buildcache.site_policy.OTHER,
    )
    result = buildcache.prepare_masstree_fetchcontent(
        ccbench_dir=str(source.resolve()),
        fetchcontent_base_dir=str(base.resolve()),
        expected_toolchain_manifest={
            role: {
                "requested": role, "realpath": f"/tool/{role}",
                "version_first_line": "v1", "version": "v1",
            }
            for role in ("cc", "cxx", "cmake")
        },
        configure_timeout_s=11, target_timeout_s=13,
    )
    assert [what for _cmd, what, _kwargs in calls] == ["configure", "build"]
    assert calls[1][0][calls[1][0].index("--target") + 1] == "masstree_build"
    assert calls[0][2]["timeout_s"] == 11
    assert calls[1][2]["timeout_s"] == 13
    assert result.fetchcontent_base_dir == str(base.resolve())


def test_prepare_masstree_fetchcontent_never_emits_source_dir_override(
        tmp_path, monkeypatch):
    base = tmp_path / "base"
    source = tmp_path / "ccbench"
    base.mkdir()
    source.mkdir()
    calls = []
    monkeypatch.setattr(buildcache, "_run", lambda cmd, what, **kwargs: calls.append(cmd))
    monkeypatch.setattr(
        buildcache.site_policy, "current_site", lambda: buildcache.site_policy.OTHER,
    )
    buildcache.prepare_masstree_fetchcontent(
        ccbench_dir=str(source.resolve()),
        fetchcontent_base_dir=str(base.resolve()),
        expected_toolchain_manifest={
            role: {
                "requested": role, "realpath": f"/tool/{role}",
                "version_first_line": "v1", "version": "v1",
            }
            for role in ("cc", "cxx", "cmake")
        },
        configure_timeout_s=11, target_timeout_s=13,
    )
    assert [
        token for token in calls[0]
        if token.startswith("-DFETCHCONTENT_BASE_DIR=")
    ] == [f"-DFETCHCONTENT_BASE_DIR={base.resolve()}"]
    assert not any(
        token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
        for command in calls for token in command
    )


def test_prepare_masstree_fetchcontent_emits_all_three_staged_source_dirs(
        tmp_path, monkeypatch):
    base = tmp_path / "base"
    source = tmp_path / "ccbench"
    base.mkdir()
    source.mkdir()
    staged = {
        name: tmp_path / f"{name}-src"
        for name in ("masstree", "mimalloc", "googletest")
    }
    for path in staged.values():
        path.mkdir()
    calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda cmd, what, **kwargs: calls.append((cmd, what, kwargs)),
    )
    monkeypatch.setattr(
        buildcache.site_policy, "current_site", lambda: buildcache.site_policy.OTHER,
    )
    result = buildcache.prepare_masstree_fetchcontent(
        ccbench_dir=str(source.resolve()),
        fetchcontent_base_dir=str(base.resolve()),
        expected_toolchain_manifest={
            role: {
                "requested": role, "realpath": f"/tool/{role}",
                "version_first_line": "v1", "version": "v1",
            }
            for role in ("cc", "cxx", "cmake")
        },
        configure_timeout_s=11, target_timeout_s=13,
        masstree_source_dir=staged["masstree"].resolve(),
        mimalloc_source_dir=staged["mimalloc"].resolve(),
        googletest_source_dir=staged["googletest"].resolve(),
    )
    configure = list(result.configure_argv)
    assert [
        token for token in configure
        if token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
    ] == [
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={staged['masstree'].resolve()}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={staged['mimalloc'].resolve()}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={staged['googletest'].resolve()}",
    ]
    assert calls[0][1] == "configure"
    assert calls[1][1] == "build"


def test_prepare_masstree_fetchcontent_rejects_partial_staged_source_dirs(
        tmp_path):
    base = tmp_path / "base"
    source = tmp_path / "ccbench"
    masstree = tmp_path / "masstree-src"
    base.mkdir()
    source.mkdir()
    masstree.mkdir()
    with pytest.raises(buildcache.BuildCacheError, match="3本同時指定"):
        buildcache.prepare_masstree_fetchcontent(
            ccbench_dir=str(source.resolve()),
            fetchcontent_base_dir=str(base.resolve()),
            expected_toolchain_manifest={
                role: {
                    "requested": role, "realpath": f"/tool/{role}",
                    "version_first_line": "v1", "version": "v1",
                }
                for role in ("cc", "cxx", "cmake")
            },
            configure_timeout_s=11, target_timeout_s=13,
            masstree_source_dir=masstree.resolve(),
        )


def test_v2_fetchcontent_transport_mode_separates_base_and_source_identity():
    genome = Genome("silo", {"BACK_OFF": 1})
    toolchain = {
        role: {"requested": role, "realpath": f"/tool/{role}", "version_first_line": "v1"}
        for role in ("cc", "cxx", "cmake")
    }
    kwargs = dict(
        site="test", dependency_prefix=[], admission={"receipt": "fixture"},
        fetchcontent_dependency_receipt=_dependency_receipt(),
    )
    legacy = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        fetchcontent_transport_mode=None, **kwargs,
    )
    source = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        fetchcontent_transport_mode="source-dir", **kwargs,
    )
    assert "fetchcontent_transport_mode" not in legacy[0]
    assert source[0]["fetchcontent_transport_mode"] == "source-dir"
    assert legacy[1] != source[1]


def test_v2_source_dir_transport_reaches_configure_and_completion_identity(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    base = tmp_path / "fetchcontent"
    base.mkdir()
    receipt = _write_fetchcontent_dependency(base)
    staged = {
        name: base / f"{name}-src"
        for name in ("mimalloc", "googletest")
    }
    for path in staged.values():
        path.mkdir()
    source = _build(
        tmp_path, _contract(1), fetchcontent_base_dir=str(base.resolve()),
        fetchcontent_dependency_receipt=receipt,
        masstree_source_dir=str((base / "masstree-src").resolve()),
        mimalloc_source_dir=str(staged["mimalloc"].resolve()),
        googletest_source_dir=str(staged["googletest"].resolve()),
    )
    assert [
        token for token in source.configure_argv
        if token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
    ] == [
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={base.resolve() / 'masstree-src'}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={staged['mimalloc'].resolve()}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={staged['googletest'].resolve()}",
    ]
    manifest = json.loads(
        (Path(source.build_dir) / "completion.json").read_text(encoding="utf-8")
    )
    assert manifest["preimage"]["fetchcontent_transport_mode"] == "source-dir"


def _call_copyout_api(tmp_path: Path, api: str, *, trace: bool = True):
    genome = Genome("silo", {"BACK_OFF": 1})
    if api == "v2":
        return _build(tmp_path, _contract(1), trace=trace)
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(tmp_path / "ccbench"),
    )
    return buildcache.build(
        genome, "a" * 40, trace,
        cache_root=str(tmp_path / "cache"), admission=admission,
        build_context=context, source_evidence=evidence,
    )


def _install_staging_artifacts(monkeypatch, *, leaf_kind: str, payload: bytes):
    calls = []

    def fake_run(cmd, what, timeout_s=None, *, site=None, env=None):
        calls.append(what)
        if what != "build":
            return
        staging = Path(cmd[cmd.index("--build") + 1])
        binary = staging / "cc" / "silo" / "ycsb_silo.exe"
        binary.parent.mkdir(parents=True, exist_ok=True)
        (staging / "CMakeCache.txt").write_text("untrusted-cache\n", encoding="utf-8")
        obj = staging / "objects" / "variant.o"
        obj.parent.mkdir()
        obj.write_bytes(b"untrusted-object")
        (staging / "completion.json").write_text('{"forged":true}\n', encoding="utf-8")
        (staging / "admission.json").write_text('{"forged":true}\n', encoding="utf-8")
        (staging / "ignored-link").symlink_to("CMakeCache.txt")
        os.mkfifo(staging / "ignored-fifo")
        if leaf_kind == "regular":
            binary.write_bytes(payload)
        elif leaf_kind == "symlink":
            target = staging / "unallowlisted-real-binary"
            target.write_bytes(payload)
            binary.symlink_to(target)
        elif leaf_kind == "fifo":
            os.mkfifo(binary)
        elif leaf_kind == "directory":
            binary.mkdir()
        elif leaf_kind == "hardlink":
            target = staging / "unallowlisted-hardlink-target"
            target.write_bytes(payload)
            os.link(target, binary)
        else:  # pragma: no cover - test helper contract
            raise AssertionError(leaf_kind)

    monkeypatch.setattr(buildcache, "_run", fake_run)
    return calls


def _published_non_directory_members(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if not path.is_dir()
    }


def test_v2_custom_ccbench_tree_drives_commit_allowlist_identity_and_trace_checks(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    custom = tmp_path / "prepared-cell-tree"
    calls = {"commit": [], "allowlist": [], "resolve": [], "trace_diff": []}
    monkeypatch.setattr(
        buildcache, "_verify_ccbench_commit",
        lambda sub, commit: calls["commit"].append((sub, commit)),
    )
    buildcache.source_digest.assert_worktree_within_allowlist = (
        lambda sub: calls["allowlist"].append(sub)
    )

    def resolve_evidence(genome, commit, *, ccbench_dir, cxx):
        calls["resolve"].append(ccbench_dir)
        return _source_evidence(genome, commit, ccbench_dir)

    def trace_diff(_genome, _commit, sub, _cxx):
        calls["trace_diff"].append(sub)

    buildcache.source_digest.resolve_evidence = resolve_evidence
    buildcache.source_digest.assert_trace_diff_matches_head = trace_diff

    fresh = _build(tmp_path, _contract(1), trace=False, ccbench_dir=str(custom))
    hit = _build(tmp_path, _contract(1), trace=False, ccbench_dir=str(custom))

    assert not fresh.cached and hit.cached
    assert Path(fresh.ccbench_root) == custom.absolute()
    assert calls["commit"] == [(str(custom), "a" * 40)] * 2
    assert calls["allowlist"] == [str(custom)] * 2
    assert calls["resolve"] == [str(custom)] * 2
    assert calls["trace_diff"] == [str(custom)] * 2


def test_v2_custom_ccbench_tree_allowlist_rejection_precedes_build(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    custom = tmp_path / "outside-allowlist"
    ran = []
    buildcache.source_digest.assert_worktree_within_allowlist = (
        lambda sub: (_ for _ in ()).throw(RuntimeError(f"allowlist rejected: {sub}"))
    )
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: ran.append((args, kwargs)),
    )
    with pytest.raises(RuntimeError, match="allowlist rejected"):
        _build(tmp_path, _contract(1), ccbench_dir=str(custom))
    assert ran == []
    assert not (tmp_path / "cache").exists()


def test_v2_ccbench_path_is_not_cache_preimage_when_src_token_is_identical(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    default = _build(tmp_path, _contract(1), trace=True)
    # Different lexical paths to the same canonical source root keep the exact
    # SourceEvidence/receipt identical.  A genuinely different prepared root is
    # intentionally a different T-343 admission identity even if its bytes match.
    alias = tmp_path / "same-content-prepared-tree"
    alias.symlink_to(tmp_path / "ccbench", target_is_directory=True)
    custom = _build(
        tmp_path, _contract(1), trace=True,
        ccbench_dir=str(alias),
    )
    assert not default.cached and custom.cached
    assert custom.build_dir == default.build_dir


def test_v2_timeout_is_applied_to_configure_and_build(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    calls = []

    def fake_run(cmd, what, timeout_s=None):
        calls.append((what, timeout_s))
        if what == "build":
            bdir = Path(cmd[cmd.index("--build") + 1])
            binary = bdir / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(b"timeout-pinned")

    monkeypatch.setattr(buildcache, "_run", fake_run)
    result = _build(tmp_path, _contract(1), timeout_s=17)
    assert Path(result.binary).is_file()
    assert calls == [("configure", 17), ("build", 17)]


def test_v2_run_helper_enforces_subprocess_timeout_behavior():
    with pytest.raises(subprocess.TimeoutExpired):
        buildcache._run(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            "timeout-control", timeout_s=0.05,
        )


@pytest.mark.parametrize("bad", [0, -1, True, 1.5])
def test_v2_timeout_rejects_nonpositive_or_noninteger(tmp_path, monkeypatch, bad):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    with pytest.raises(TypeError, match="timeout_s"):
        _build(tmp_path, _contract(1), timeout_s=bad)


def test_v2_contract_changes_namespace_only(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    a, b = _build(tmp_path, _contract(1)), _build(tmp_path, _contract(2))
    assert a.contract_sha256 == _contract(1).contract_sha256
    assert b.contract_sha256 == _contract(2).contract_sha256
    assert a.build_dir != b.build_dir
    assert Path(a.build_dir).parent.name == _contract(1).contract_sha256
    assert Path(b.build_dir).parent.name == _contract(2).contract_sha256
    assert Path(a.build_dir).name == Path(b.build_dir).name
    assert len(Path(a.build_dir).name) == 64


def test_v2_copied_entry_cannot_cross_contract_namespace(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    first = _build(tmp_path, _contract(1))
    forged = (
        tmp_path / "cache" / "contracts" / _contract(2).contract_sha256
        / Path(first.build_dir).name
    )
    forged.parent.mkdir(parents=True)
    shutil.copytree(first.build_dir, forged)
    with pytest.raises(buildcache.BuildCacheError, match="contract namespace"):
        _build(tmp_path, _contract(2))
    assert (forged / "completion.json").exists()  # 不一致 entry を上書き・修復しない


def test_v2_toolchain_version_change_is_cache_miss(tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch, cxx_version="cxx version A")
    _fake_build_environment(monkeypatch, tmp_path)
    first = _build(tmp_path, _contract(1))
    assert not first.cached
    _write_tool(bindir / "test-cxx", "cxx version B")
    second = _build(tmp_path, _contract(1))
    assert not second.cached
    assert first.build_dir != second.build_dir


def test_v2_expected_toolchain_manifest_exact_match_is_accepted(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    expected = _expected_toolchain_manifest(bindir)
    result = _build(
        tmp_path, _contract(1),
        expected_toolchain_manifest=expected,
    )
    assert not result.cached
    assert result.toolchain_manifest == expected
    assert result.toolchain_manifest_sha256 == hashlib.sha256(
        json.dumps(expected, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_v2_official_requires_expected_toolchain_manifest_before_cache_claim(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    with pytest.raises(buildcache.BuildCacheError, match="expected_toolchain_manifest"):
        _build(tmp_path, _contract(1), declared_use_class="official")
    assert not (tmp_path / "cache").exists()


def test_v2_expected_toolchain_manifest_mismatch_refuses_before_cache_claim(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    expected = _expected_toolchain_manifest(bindir)
    expected["cc"] = dict(expected["cc"], version_first_line="cc version stale")
    with pytest.raises(buildcache.BuildCacheError, match="caller の事前観測"):
        _build(
            tmp_path, _contract(1),
            expected_toolchain_manifest=expected,
        )
    assert not (tmp_path / "cache").exists()


def test_v2_expected_toolchain_realpath_mismatch_refuses_before_cache_claim(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    expected = _expected_toolchain_manifest(bindir)
    expected["cc"] = dict(expected["cc"], realpath=str(tmp_path / "other-cc"))
    with pytest.raises(buildcache.BuildCacheError, match="caller の事前観測"):
        _build(
            tmp_path, _contract(1),
            expected_toolchain_manifest=expected,
        )
    assert not (tmp_path / "cache").exists()


def test_v2_expected_toolchain_version_lower_line_drift_refuses_before_cache_claim(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    _write_multiline_tool(
        bindir / "test-cc", ("cc version A", "Copyright stable"),
    )
    expected = _expected_toolchain_manifest(bindir)
    expected["cc"] = dict(
        expected["cc"], version="cc version A\nCopyright stable",
    )
    _write_multiline_tool(
        bindir / "test-cc", ("cc version A", "Copyright changed"),
    )
    observed = subprocess.run(
        [bindir / "test-cc", "--version"], capture_output=True, text=True, check=True,
    )
    assert (observed.stdout + observed.stderr).strip() == "cc version A\nCopyright changed"
    with pytest.raises(buildcache.BuildCacheError, match="version 全文"):
        _build(
            tmp_path, _contract(1),
            expected_toolchain_manifest=expected,
        )
    assert not (tmp_path / "cache").exists()


def test_v2_cache_hit_rejects_complete_toolchain_version_drift(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    _write_multiline_tool(
        bindir / "test-cxx", ("cxx version A", "Copyright stable"),
    )
    expected_a = _expected_toolchain_manifest(bindir)
    expected_a["cxx"] = dict(
        expected_a["cxx"], version="cxx version A\nCopyright stable",
    )
    first = _build(
        tmp_path, _contract(1), expected_toolchain_manifest=expected_a,
        declared_use_class="official",
    )
    manifest = json.loads(
        (Path(first.build_dir) / "completion.json").read_text(encoding="utf-8")
    )
    assert manifest["complete_toolchain_manifest"] == expected_a
    assert manifest["complete_toolchain_manifest_sha256"] == hashlib.sha256(
        json.dumps(expected_a, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    _write_multiline_tool(
        bindir / "test-cxx", ("cxx version A", "Copyright changed"),
    )
    expected_b = dict(
        expected_a,
        cxx=dict(expected_a["cxx"], version="cxx version A\nCopyright changed"),
    )
    build_calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: build_calls.append((args, kwargs)),
    )
    with pytest.raises(
            buildcache.BuildCacheError,
            match="complete toolchain manifest 完全一致検査に失敗",
    ):
        _build(
            tmp_path, _contract(1), expected_toolchain_manifest=expected_b,
            declared_use_class="official",
        )
    assert build_calls == []


def test_v2_official_hit_rejects_legacy_entry_without_complete_manifest(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    first = _build(tmp_path, _contract(1))
    manifest_path = Path(first.build_dir) / "completion.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "complete_toolchain_manifest" not in manifest
    assert "complete_toolchain_manifest_sha256" not in manifest

    build_calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: build_calls.append((args, kwargs)),
    )
    with pytest.raises(
            buildcache.BuildCacheError,
            match="complete toolchain manifest 完全一致検査に失敗",
    ):
        _build(
            tmp_path, _contract(1),
            expected_toolchain_manifest=_expected_toolchain_manifest(bindir),
            declared_use_class="official",
        )
    assert build_calls == []


def test_v2_nonofficial_hit_accepts_entry_with_complete_manifest(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    expected = _expected_toolchain_manifest(bindir)
    first = _build(
        tmp_path, _contract(1),
        expected_toolchain_manifest=expected,
        declared_use_class="official",
    )
    manifest = json.loads(
        (Path(first.build_dir) / "completion.json").read_text(encoding="utf-8")
    )
    assert manifest["complete_toolchain_manifest"] == expected
    assert manifest["complete_toolchain_manifest_sha256"] == hashlib.sha256(
        json.dumps(expected, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    build_calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: build_calls.append((args, kwargs)),
    )
    hit = _build(tmp_path, _contract(1))
    assert not first.cached
    assert hit.cached
    assert hit.build_dir == first.build_dir
    assert hit.toolchain_manifest is None
    assert hit.toolchain_manifest_sha256 is None
    assert build_calls == []


def test_v2_expected_manifest_gate_fires_without_official_declared_use_class(
        tmp_path, monkeypatch):
    bindir = _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    expected_a = _expected_toolchain_manifest(bindir)
    first = _build(
        tmp_path, _contract(1), expected_toolchain_manifest=expected_a,
    )
    manifest = json.loads(
        (Path(first.build_dir) / "completion.json").read_text(encoding="utf-8")
    )
    assert manifest["complete_toolchain_manifest"] == expected_a
    assert manifest["complete_toolchain_manifest_sha256"] == hashlib.sha256(
        json.dumps(expected_a, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    _write_multiline_tool(
        bindir / "test-cxx", ("cxx version A", "Copyright changed"),
    )
    expected_b = dict(
        expected_a,
        cxx=dict(expected_a["cxx"], version="cxx version A\nCopyright changed"),
    )
    build_calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: build_calls.append((args, kwargs)),
    )
    with pytest.raises(
            buildcache.BuildCacheError,
            match="complete toolchain manifest 完全一致検査に失敗",
    ):
        _build(
            tmp_path, _contract(1), expected_toolchain_manifest=expected_b,
        )
    assert build_calls == []


def test_m7_v2_actual_site_change_is_cache_miss(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    first = _build(tmp_path, _contract(1))
    monkeypatch.setattr(
        buildcache.site_policy,
        "current_site",
        lambda: buildcache.site_policy.PEGASUS_COMPUTE,
    )
    second = _build(tmp_path, _contract(1))
    assert not first.cached and not second.cached
    assert first.build_dir != second.build_dir


def test_m8_v2_explicit_dependency_prefix_change_is_cache_miss(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    first = _build(tmp_path, _contract(1), dependency_prefix="/deps/gflags")
    second = _build(tmp_path, _contract(1), dependency_prefix="/deps/glog")
    assert not first.cached and not second.cached
    assert first.build_dir != second.build_dir


def test_b10_binary_path_policy_emits_only_macro_map_and_rpath_suppression(
        tmp_path):
    source = tmp_path / "checkout"
    toolchain = {
        role: {"realpath": f"/tool/{role}"}
        for role in ("cc", "cxx", "cmake")
    }
    common = dict(
        genome=Genome("silo", {"BACK_OFF": 1}), trace=False,
        sub=str(source), bdir=str(tmp_path / "build"), toolchain=toolchain,
        site="test",
    )
    default_configure, _ = buildcache._v2_commands(**common)
    configured, _ = buildcache._v2_commands(
        **common, binary_path_policy=buildcache.B10_BINARY_PATH_POLICY,
    )
    macro_map = (
        "-DCMAKE_CXX_FLAGS=-fmacro-prefix-map="
        f"{source.resolve()}={buildcache.B10_LOGICAL_SOURCE_ROOT}"
    )
    additions = [token for token in configured if token not in default_configure]

    assert additions == [macro_map, "-DCMAKE_SKIP_RPATH=ON"]
    assert "-DCMAKE_BUILD_TYPE=Release" in configured
    assert not any("-O" in token for token in additions)
    assert not any("-flto" in token for token in additions)
    assert not any("CMAKE_SKIP_RPATH" in token for token in default_configure)
    with pytest.raises(buildcache.BuildCacheError, match="binary path policy"):
        buildcache._v2_commands(**common, binary_path_policy="unknown/v1")


def test_b10_binary_path_policy_maps_exact_staging_root_only_for_policy(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    fake_run = buildcache._run
    configure_calls = []

    def record_run(cmd, what, timeout_s=None, *, site=None, env=None):
        if what == "configure":
            configure_calls.append(tuple(cmd))
        return fake_run(cmd, what, timeout_s, site=site, env=env)

    monkeypatch.setattr(buildcache, "_run", record_run)
    monkeypatch.setenv(
        buildcache.B10_BINARY_PATH_POLICY_ENV,
        buildcache.B10_BINARY_PATH_POLICY,
    )
    _build(tmp_path, _contract(1))
    monkeypatch.delenv(buildcache.B10_BINARY_PATH_POLICY_ENV)
    _build(tmp_path, _contract(1))

    assert len(configure_calls) == 2
    configured, default_configure = configure_calls
    staging = Path(configured[configured.index("-B") + 1]).resolve()
    default_staging = Path(
        default_configure[default_configure.index("-B") + 1]
    ).resolve()
    source = (tmp_path / "ccbench").resolve()
    expected_cxx_flags = (
        "-DCMAKE_CXX_FLAGS="
        f"-fmacro-prefix-map={source}="
        f"{buildcache.B10_LOGICAL_SOURCE_ROOT} "
        f"-fdebug-prefix-map={staging}="
        f"{buildcache.B10_LOGICAL_BUILD_ROOT}"
    )

    assert staging.name.startswith(".staging-")
    assert default_staging.name.startswith(".staging-")
    assert [
        token for token in configured if "-fdebug-prefix-map=" in token
    ] == [expected_cxx_flags]
    assert [
        token for token in default_configure if "-fdebug-prefix-map=" in token
    ] == []
    assert "-DCMAKE_SKIP_RPATH=ON" in configured


def test_b10_macro_prefix_map_real_compiler_normalizes_bytes_without_text_change(
        tmp_path):
    cxx = shutil.which("g++")
    objcopy = shutil.which("objcopy")
    assert cxx is not None
    assert objcopy is not None
    roots = (tmp_path / "checkout-a", tmp_path / "checkout-b")
    binaries = {}
    text_sections = {}
    source_bytes = (
        b"extern void consume(const char*);\n"
        b"int main() { consume(__FILE__); }\n"
    )
    sink = tmp_path / "sink.cc"
    sink.write_bytes(b"void consume(const char*) {}\n")

    for root in roots:
        root.mkdir()
        source = root / "probe.cc"
        source.write_bytes(source_bytes)
        for mapped in (False, True):
            label = (root.name, mapped)
            binary = root / ("mapped.exe" if mapped else "plain.exe")
            command = [cxx, "-O3", "-DNDEBUG"]
            if mapped:
                command.append(
                    f"-fmacro-prefix-map={root.resolve()}="
                    f"{buildcache.B10_LOGICAL_SOURCE_ROOT}"
                )
            command.extend([
                str(source.resolve()), str(sink.resolve()), "-o", str(binary),
            ])
            completed = subprocess.run(
                command, capture_output=True, text=True,
            )
            assert completed.returncode == 0, completed.stdout + completed.stderr
            binaries[label] = binary.read_bytes()
            text_path = root / ("mapped.text" if mapped else "plain.text")
            dumped = subprocess.run(
                [objcopy, "--dump-section", f".text={text_path}", str(binary)],
                capture_output=True, text=True,
            )
            assert dumped.returncode == 0, dumped.stdout + dumped.stderr
            text_sections[label] = text_path.read_bytes()

    assert binaries[("checkout-a", False)] != binaries[("checkout-b", False)]
    assert str(roots[0].resolve()).encode() in binaries[("checkout-a", False)]
    assert str(roots[1].resolve()).encode() in binaries[("checkout-b", False)]
    assert binaries[("checkout-a", True)] == binaries[("checkout-b", True)]
    assert buildcache.B10_LOGICAL_SOURCE_ROOT.encode() in binaries[
        ("checkout-a", True)
    ]
    assert str(roots[0].resolve()).encode() not in binaries[("checkout-a", True)]
    assert str(roots[1].resolve()).encode() not in binaries[("checkout-b", True)]
    assert len(set(text_sections.values())) == 1


def test_b10_binary_path_policy_environment_binds_identity_and_preserves_default(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    monkeypatch.setenv(
        buildcache.B10_BINARY_PATH_POLICY_ENV,
        buildcache.B10_BINARY_PATH_POLICY,
    )
    dependencies = ";".join((
        str(tmp_path / "gflags-install"), str(tmp_path / "glog-install"),
    ))
    normalized = _build(
        tmp_path, _contract(1), dependency_prefix=dependencies,
    )
    normalized_manifest = json.loads(
        (Path(normalized.build_dir) / "completion.json").read_text(
            encoding="utf-8",
        )
    )
    expected_map = (
        "-DCMAKE_CXX_FLAGS=-fmacro-prefix-map="
        f"{(tmp_path / 'ccbench').resolve()}="
        f"{buildcache.B10_LOGICAL_SOURCE_ROOT}"
    )

    assert expected_map in normalized.configure_argv
    assert "-DCMAKE_SKIP_RPATH=ON" in normalized.configure_argv
    assert normalized_manifest["preimage"]["binary_path_policy"] == (
        buildcache.B10_BINARY_PATH_POLICY
    )
    assert normalized_manifest["preimage"]["admission"]["source"][
        "source_root"
    ] == str((tmp_path / "ccbench").resolve())
    assert normalized_manifest["preimage"]["dependency_prefix"] == [
        str((tmp_path / "gflags-install").resolve()),
        str((tmp_path / "glog-install").resolve()),
    ]

    monkeypatch.delenv(buildcache.B10_BINARY_PATH_POLICY_ENV)
    default = _build(
        tmp_path, _contract(1), dependency_prefix=dependencies,
    )
    default_manifest = json.loads(
        (Path(default.build_dir) / "completion.json").read_text(
            encoding="utf-8",
        )
    )
    assert default.build_dir != normalized.build_dir
    assert expected_map not in default.configure_argv
    assert "-DCMAKE_SKIP_RPATH=ON" not in default.configure_argv
    assert "binary_path_policy" not in default_manifest["preimage"]


def test_b10_binary_path_policy_environment_rejects_unknown_value(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    monkeypatch.setenv(buildcache.B10_BINARY_PATH_POLICY_ENV, "unknown/v1")
    with pytest.raises(
            buildcache.BuildCacheError,
            match=buildcache.B10_BINARY_PATH_POLICY_ENV):
        _build(tmp_path, _contract(1))


def test_ambient_dependency_prefix_canonicalization_rule(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = os.pathsep.join(("deps/../gflags", "", "./glog"))
    assert buildcache._canonical_ambient_dependency_prefix(raw) == [
        str((tmp_path / "gflags").resolve()), str(tmp_path.resolve()),
        str((tmp_path / "glog").resolve()),
    ]


def test_m9_v2_ambient_dependency_prefix_change_is_cache_miss(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    monkeypatch.setenv(
        "CMAKE_PREFIX_PATH",
        os.pathsep.join((str(tmp_path / "gflags"), str(tmp_path / "glog"))),
    )
    first = _build(tmp_path, _contract(1))
    first_manifest = json.loads(
        (Path(first.build_dir) / "completion.json").read_text(encoding="utf-8")
    )
    assert first_manifest["preimage"]["dependency_prefix"] == [
        str((tmp_path / "gflags").resolve()), str((tmp_path / "glog").resolve()),
    ]

    monkeypatch.setenv(
        "CMAKE_PREFIX_PATH",
        os.pathsep.join((str(tmp_path / "gflags"), str(tmp_path / "other-glog"))),
    )
    second = _build(tmp_path, _contract(1))
    assert not first.cached and not second.cached
    assert first.build_dir != second.build_dir


def test_ambient_prefix_path_list_encoding_is_injective(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("CMAKE_PREFIX_PATH", "/tmp/p:/tmp/q")
    split_paths = _build(tmp_path, _contract(1))
    monkeypatch.setenv("CMAKE_PREFIX_PATH", "/tmp/p;/tmp/q")
    semicolon_path = _build(tmp_path, _contract(1))
    assert Path(split_paths.build_dir).name != Path(semicolon_path.build_dir).name
    first = json.loads(
        (Path(split_paths.build_dir) / "completion.json").read_text(encoding="utf-8")
    )["preimage"]["dependency_prefix"]
    second = json.loads(
        (Path(semicolon_path.build_dir) / "completion.json").read_text(encoding="utf-8")
    )["preimage"]["dependency_prefix"]
    assert first == ["/tmp/p", "/tmp/q"]
    assert second == ["/tmp/p;/tmp/q"]


def test_m10_explicit_prefix_is_one_argv_token_and_removes_ambient_env(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("CMAKE_PREFIX_PATH", "/ambient/must-not-compete")
    calls = []

    def fake_run(cmd, what, timeout_s=None, *, site=None, env=None):
        calls.append((what, tuple(cmd), env))
        if what == "build":
            bdir = Path(cmd[cmd.index("--build") + 1])
            binary = bdir / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(b"prefix-env")

    monkeypatch.setattr(buildcache, "_run", fake_run)
    explicit = "/deps/gflags;/deps/glog"
    with_prefix = _build(
        tmp_path, _contract(1), dependency_prefix=explicit,
    )
    without_prefix = _build(tmp_path, _contract(2))

    explicit_tokens = [
        token for token in with_prefix.configure_argv
        if token.startswith("-DCMAKE_PREFIX_PATH=")
    ]
    inherited_tokens = [
        token for token in without_prefix.configure_argv
        if token.startswith("-DCMAKE_PREFIX_PATH=")
    ]
    assert explicit_tokens == [f"-DCMAKE_PREFIX_PATH={explicit}"]
    assert inherited_tokens == []
    assert all(
        env is not None and "CMAKE_PREFIX_PATH" not in env
        for _, _, env in calls[:2]
    )
    assert all(env is None for _, _, env in calls[2:])


def test_explicit_relative_prefix_is_bound_to_effective_cwd(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    result = _build(tmp_path, _contract(1), dependency_prefix="deps")
    expected = str((tmp_path / "deps").resolve())
    assert f"-DCMAKE_PREFIX_PATH={expected}" in result.configure_argv
    manifest = json.loads(
        (Path(result.build_dir) / "completion.json").read_text(encoding="utf-8")
    )
    assert manifest["preimage"]["dependency_prefix"] == [expected]


def test_m13_caller_injected_site_does_not_change_v2_identity(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    first = _build(tmp_path, _contract(1), site=buildcache.site_policy.OTHER)
    second = _build(
        tmp_path, _contract(1), site=buildcache.site_policy.PEGASUS_COMPUTE,
    )
    assert not first.cached and second.cached
    assert first.build_dir == second.build_dir


def test_v2_toolchain_probe_failure_is_build_error_without_cache(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    monkeypatch.setattr(
        buildcache.shutil, "which",
        lambda requested: None if requested == "test-cxx" else "/bin/true",
    )
    with pytest.raises(buildcache.BuildError, match="test-cxx"):
        _build(tmp_path, _contract(1))
    assert not (tmp_path / "cache").exists()


def test_v2_never_hits_legacy_entry(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path, payload=b"v2")
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(tmp_path / "ccbench"),
    )
    legacy = tmp_path / "cache" / buildcache.cache_key(
        genome, "a" * 40, True, src_token="stock", cc="test-cc", cxx="test-cxx",
        admission=admission,
    ) / "cc" / "silo" / "ycsb_silo.exe"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(b"legacy")
    result = _build(tmp_path, _contract(1))
    assert not result.cached
    assert Path(result.binary).read_bytes() == b"v2"
    assert "/contracts/" in result.build_dir


def test_legacy_key_binds_admission_for_all_classes(tmp_path):
    genome = Genome("silo", {"BACK_OFF": 1})
    admissions = _all_class_admissions(genome, str(tmp_path / "ccbench"))
    keys = {
        buildcache.cache_key(
            genome, "a" * 40, False, src_token="stock", admission=admission,
        )
        for admission in admissions
    }
    assert len(keys) == 4


def test_legacy_hit_requires_exact_admission_sidecar(tmp_path, monkeypatch):
    _fake_build_environment(monkeypatch, tmp_path)
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(tmp_path / "ccbench"),
    )
    key = buildcache.cache_key(
        genome, "a" * 40, True, admission=admission,
    )
    binary = tmp_path / "cache" / key / "cc" / "silo" / "ycsb_silo.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"old-entry-under-new-key")
    build_calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: build_calls.append((args, kwargs)),
    )
    with pytest.raises(buildcache.BuildCacheError, match="legacy admission sidecar"):
        buildcache.build(
            genome,
            "a" * 40,
            True,
            cache_root=str(tmp_path / "cache"),
            admission=admission,
            build_context=context,
            source_evidence=evidence,
        )
    assert build_calls == []
    assert binary.read_bytes() == b"old-entry-under-new-key"


def test_legacy_fresh_publish_includes_sidecar_and_remains_a_hit(tmp_path, monkeypatch):
    _fake_build_environment(monkeypatch, tmp_path, payload=b"legacy-fresh")
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(tmp_path / "ccbench"),
    )
    kwargs = {
        "cache_root": str(tmp_path / "cache"),
        "admission": admission,
        "build_context": context,
        "source_evidence": evidence,
    }
    fresh = buildcache.build(genome, "a" * 40, True, **kwargs)
    hit = buildcache.build(genome, "a" * 40, True, **kwargs)
    sidecar = json.loads(
        (Path(fresh.build_dir) / "admission.json").read_text(encoding="utf-8")
    )
    assert not fresh.cached and hit.cached
    assert set(sidecar) == {"schema_version", "admission"}
    assert sidecar["admission"] == admission.as_cache_identity()


def test_v2_preimage_binds_exact_admission(tmp_path):
    genome = Genome("silo", {"BACK_OFF": 1})
    admissions = _all_class_admissions(genome, str(tmp_path / "ccbench"))
    toolchain = {
        role: {"requested": role, "realpath": f"/tool/{role}", "version_first_line": "v1"}
        for role in ("cc", "cxx", "cmake")
    }
    digests = {
        buildcache._v2_identity(
            genome,
            "a" * 40,
            False,
            "stock",
            "cc",
            "cxx",
            toolchain,
            site="test",
            dependency_prefix=[],
            admission=dict(admission.as_cache_identity()),
        )[1]
        for admission in admissions
    }
    assert len(digests) == 4


def test_v2_identity_optional_snapshot_preserves_legacy_digest_and_separates_proof():
    genome = Genome("silo", {"BACK_OFF": 1})
    toolchain = {
        role: {
            "requested": role,
            "realpath": f"/tool/{role}",
            "version_first_line": "v1",
        }
        for role in ("cc", "cxx", "cmake")
    }
    common = dict(
        site="test", dependency_prefix=[], admission={"receipt": "fixture"},
    )
    legacy = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        **common,
    )
    explicit_none = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        source_snapshot_sha256=None, **common,
    )
    first = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        source_snapshot_sha256="1" * 64, **common,
    )
    second = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        source_snapshot_sha256="2" * 64, **common,
    )
    assert legacy == explicit_none
    assert "source_snapshot_sha256" not in legacy[0]
    assert legacy[1] == (
        "e65e196014c1b0f6bac649bc33b07ad201388a7d9f4ef637a7a5bf03fdcb0c88"
    )
    assert first[0]["source_snapshot_sha256"] == "1" * 64
    assert first[0]["compiler_input_manifest_schema"] == (
        buildcache.s8b_compiler_input.MANIFEST_SCHEMA
    )
    assert first[1] != second[1]


def test_v2_schema_pin_separates_legacy_completion_without_fallback(
        tmp_path, monkeypatch):
    """受理: v2 schema は旧v1と別identityでfresh v2を発行する。

    拒否: 選択済みinvalid entryをfreshへ降格しない契約はM9の別nodeで検査する。
    """
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    genome = Genome("silo", {"BACK_OFF": 1})
    contract = _contract(1)
    source_root = (tmp_path / "ccbench").resolve()
    source_root.mkdir()
    source = source_root / "compiler-input.hh"
    source.write_bytes(b"compiler input fixture\n")
    source_snapshot_sha256 = (
        buildcache.s8b_expected_materialization.snapshot_tree_digest(
            source_root,
        )
    )
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(source_root),
    )
    toolchain = buildcache._toolchain_manifest("test-cc", "test-cxx")
    request_preimage, request_digest = buildcache._v2_identity(
        genome, "a" * 40, True, "stock", "test-cc", "test-cxx",
        toolchain,
        source_snapshot_sha256=source_snapshot_sha256,
        site=buildcache._resolve_site(None), dependency_prefix=[],
        admission=dict(admission.as_cache_identity()),
    )
    legacy_preimage = dict(request_preimage)
    pinned_schema = legacy_preimage.pop(
        "compiler_input_manifest_schema", None,
    )
    legacy_digest = hashlib.sha256(
        json.dumps(
            legacy_preimage, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()

    legacy_input_manifest = {
        "schema_version": "s8b-compiler-input/v1",
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": "ycsb_silo.exe",
        "depfile_count": 1,
        "inputs": [{
            "path": "compiler-input.hh",
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }],
    }
    legacy_input_digest = (
        buildcache.s8b_compiler_input.manifest_sha256(
            legacy_input_manifest,
        )
    )
    assert buildcache.s8b_compiler_input.validate_compiler_input_manifest(
        legacy_input_manifest,
        legacy_input_digest,
        snapshot_root=source_root,
        target="ycsb_silo.exe",
    ) == legacy_input_manifest

    legacy_entry = (
        tmp_path / "cache" / "contracts" / contract.contract_sha256
        / legacy_digest
    )
    legacy_binary = legacy_entry / "cc" / "silo" / "ycsb_silo.exe"
    legacy_binary.parent.mkdir(parents=True)
    legacy_payload = b"legacy-v1-binary"
    legacy_binary.write_bytes(legacy_payload)
    legacy_completion = {
        "schema_version": "buildcache/v2",
        "completion_marker": "complete",
        "full_build_digest": legacy_digest,
        "contract_sha256": contract.contract_sha256,
        "preimage": legacy_preimage,
        "admission": dict(admission.as_cache_identity()),
        "toolchain": toolchain,
        "binary": {
            "relative_path": "cc/silo/ycsb_silo.exe",
            "sha256": hashlib.sha256(legacy_payload).hexdigest(),
        },
        "compiler_input_manifest": legacy_input_manifest,
        "compiler_input_manifest_sha256": legacy_input_digest,
    }
    (legacy_entry / "completion.json").write_text(
        json.dumps(legacy_completion), encoding="utf-8",
    )

    run_phases = []
    original_run = buildcache._run

    def record_run(cmd, what, **kwargs):
        run_phases.append(what)
        return original_run(cmd, what, **kwargs)

    monkeypatch.setattr(buildcache, "_run", record_run)
    fresh = buildcache.build_v2(
        genome,
        admission=admission,
        build_context=context,
        source_evidence=evidence,
        source_snapshot_sha256=source_snapshot_sha256,
        contract=contract,
        ccbench_commit="a" * 40,
        trace=True,
        src_token="stock",
        cc="test-cc",
        cxx="test-cxx",
        cache_root=str(tmp_path / "cache"),
        ccbench_dir=str(source_root),
    )
    published = json.loads(
        (Path(fresh.build_dir) / "completion.json").read_text(
            encoding="utf-8",
        )
    )

    assert pinned_schema == buildcache.s8b_compiler_input.MANIFEST_SCHEMA
    assert request_digest != legacy_digest
    assert fresh.cached is False
    assert run_phases == ["configure", "build"]
    assert Path(fresh.build_dir).name == request_digest
    assert Path(fresh.build_dir) != legacy_entry
    assert published["preimage"]["compiler_input_manifest_schema"] == (
        buildcache.s8b_compiler_input.MANIFEST_SCHEMA
    )
    assert published["compiler_input_manifest"]["schema_version"] == (
        buildcache.s8b_compiler_input.MANIFEST_SCHEMA
    )


def test_descriptor_compiler_input_policy_has_distinct_v2_identity():
    genome = Genome("silo", {"BACK_OFF": 1})
    toolchain = {
        role: {
            "requested": role,
            "realpath": f"/tool/{role}",
            "version_first_line": "v1",
        }
        for role in ("cc", "cxx", "cmake")
    }
    common = dict(
        source_snapshot_sha256="1" * 64,
        site="test", dependency_prefix=[], admission={"receipt": "fixture"},
    )
    legacy_snapshot = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        **common,
    )
    descriptor_snapshot = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        compiler_input_policy="snapshot-and-external-hashes/v1", **common,
    )

    assert descriptor_snapshot[0]["compiler_input_policy"] == (
        "snapshot-and-external-hashes/v1"
    )
    assert descriptor_snapshot[1] != legacy_snapshot[1]


def test_v3_external_policy_rejects_collector_without_dependency_root_keywords(
        monkeypatch):
    def old_collector(
            _build_dir, _snapshot_root, *, target, allow_external_inputs,
            expected_evolve_block_sources,
            origin_fetchcontent_masstree_root,
            current_fetchcontent_masstree_root):
        raise AssertionError("incomplete collector must not be called")

    monkeypatch.setattr(
        buildcache.s8b_compiler_input,
        "collect_compiler_input_manifest",
        old_collector,
    )
    with pytest.raises(buildcache.BuildCacheError, match="root binding"):
        buildcache._collect_compiler_inputs(
            "/unused/build", "/unused/snapshot", target="ycsb_silo.exe",
            allow_external_inputs=True,
            expected_evolve_block_sources=None,
            origin_fetchcontent_masstree_root="/unused/masstree",
            current_fetchcontent_masstree_root="/unused/masstree",
            origin_dependency_prefix_roots=("/unused/dependency",),
            current_dependency_prefix_roots=("/unused/dependency",),
        )


def test_v2_without_source_snapshot_preserves_legacy_completion_and_skips_manifest(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    collector_calls = []
    snapshot_checks = []
    monkeypatch.setattr(
        buildcache.s8b_compiler_input,
        "collect_compiler_input_manifest",
        lambda *args, **kwargs: collector_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        buildcache,
        "_assert_source_snapshot_sha256",
        lambda *args, **kwargs: snapshot_checks.append((args, kwargs)),
    )
    monkeypatch.setattr(
        buildcache.s8b_expected_materialization,
        "admitted_build_snapshot",
        lambda **_kwargs: pytest.fail(
            "descriptor-less build must not enter the declaration gate"
        ),
    )

    fresh = _build(tmp_path, _contract(1))
    hit = _build(tmp_path, _contract(1))
    completion = json.loads(
        (Path(fresh.build_dir) / "completion.json").read_text(encoding="utf-8")
    )

    assert not fresh.cached and hit.cached
    assert "source_snapshot_sha256" not in completion["preimage"]
    assert "compiler_input_manifest" not in completion
    assert "compiler_input_manifest_sha256" not in completion
    assert fresh.compiler_input_manifest is None
    assert fresh.compiler_input_manifest_sha256 is None
    assert hit.compiler_input_manifest is None
    assert hit.compiler_input_manifest_sha256 is None
    assert fresh.source_snapshot_sha256 is None
    assert fresh.expected_materialization_sha256 is None
    assert hit.source_snapshot_sha256 is None
    assert hit.expected_materialization_sha256 is None
    assert collector_calls == []
    assert snapshot_checks == []


def test_v2_descriptor_runs_gate_inside_build_and_returns_both_digests(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_v2_descriptor_runs_gate_inside_build_and_returns_both_digests_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _v2_descriptor_runs_gate_inside_build_and_returns_both_digests_case(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    source_root = tmp_path / "ccbench"
    source_root.mkdir()
    (source_root / "compiler-input.hh").write_bytes(
        b"compiler input fixture\n"
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    declaration = {
        "configuration": "stock_common",
        "flags": {"BACK_OFF": 1},
    }
    descriptor = (
        buildcache.s8b_expected_materialization.
        expected_materialization_descriptor(
            ccbench_commit="a" * 40,
            configuration="stock_common",
            declaration=declaration,
        )
    )
    context, evidence, admission = _review_admission_bundle(
        genome, "a" * 40, str(source_root),
        input_sha256=descriptor.declaration_sha256,
    )
    digest = buildcache.s8b_expected_materialization.snapshot_tree_digest(
        source_root
    )
    events = []

    @contextlib.contextmanager
    def fake_gate(**kwargs):
        assert kwargs["ccbench_commit"] == descriptor.ccbench_commit
        assert kwargs["configuration"] == descriptor.configuration
        assert kwargs["declaration"] == descriptor.declaration
        # Production must prepare this before admission; this mock must not
        # hide an absent cache branch from the sealed worker (M-D).
        assert (tmp_path / "cache").is_dir()
        events.append("gate-enter")
        yield buildcache.s8b_expected_materialization.AdmittedBuildSnapshot(
            source_snapshot_sha256=digest,
            expected_materialization_sha256=digest,
            source_evidence=evidence,
        )
        events.append("gate-exit")

    monkeypatch.setattr(
        buildcache.s8b_expected_materialization,
        "admitted_build_snapshot",
        fake_gate,
    )
    kwargs = dict(
        admission=admission,
        build_context=context,
        source_evidence=evidence,
        expected_materialization_descriptor=descriptor,
        contract=_contract(1),
        ccbench_commit="a" * 40,
        trace=False,
        src_token="stock",
        cc="test-cc",
        cxx="test-cxx",
        cache_root=str(tmp_path / "cache"),
        ccbench_dir=str(source_root),
    )
    assert not (tmp_path / "cache").exists()
    fresh = buildcache.build_v2(genome, **kwargs)
    assert Path(fresh.binary).read_bytes() == b"v2-binary"
    hit = buildcache.build_v2(genome, **kwargs)

    assert not fresh.cached and hit.cached
    assert fresh.source_snapshot_sha256 == digest
    assert fresh.expected_materialization_sha256 == digest
    assert hit.source_snapshot_sha256 == digest
    assert hit.expected_materialization_sha256 == digest
    assert events == ["gate-enter", "gate-exit", "gate-enter", "gate-exit"]


def test_v2_descriptor_rejects_rederived_evidence_before_build(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_v2_descriptor_rejects_rederived_evidence_before_build_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _v2_descriptor_rejects_rederived_evidence_before_build_case(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    source_root = tmp_path / "ccbench"
    source_root.mkdir()
    (source_root / "compiler-input.hh").write_bytes(
        b"compiler input fixture\n"
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    descriptor = (
        buildcache.s8b_expected_materialization.
        expected_materialization_descriptor(
            ccbench_commit="a" * 40,
            configuration="stock_common",
            declaration={
                "configuration": "stock_common",
                "flags": {"BACK_OFF": 1},
            },
        )
    )
    context, evidence, admission = _review_admission_bundle(
        genome, "a" * 40, str(source_root),
        input_sha256=descriptor.declaration_sha256,
    )
    digest = buildcache.s8b_expected_materialization.snapshot_tree_digest(
        source_root
    )
    different = _dirty_evidence(genome, "a" * 40, str(source_root))

    @contextlib.contextmanager
    def fake_gate(**_kwargs):
        yield buildcache.s8b_expected_materialization.AdmittedBuildSnapshot(
            source_snapshot_sha256=digest,
            expected_materialization_sha256=digest,
            source_evidence=different,
        )

    monkeypatch.setattr(
        buildcache.s8b_expected_materialization,
        "admitted_build_snapshot",
        fake_gate,
    )
    calls = []
    monkeypatch.setattr(
        buildcache, "_run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(buildcache.BuildCacheError, match="SourceEvidence"):
        buildcache.build_v2(
            genome,
            admission=admission,
            build_context=context,
            source_evidence=evidence,
            expected_materialization_descriptor=descriptor,
            contract=_contract(1),
            ccbench_commit="a" * 40,
            trace=False,
            src_token="stock",
            cc="test-cc",
            cxx="test-cxx",
            cache_root=str(tmp_path / "cache"),
            ccbench_dir=str(source_root),
        )
    assert calls == []


def test_v2_fresh_completion_and_result_expose_compiler_input_manifest(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)

    result = _build(tmp_path, _contract(1), bind_source_snapshot=True)
    completion = json.loads(
        (Path(result.build_dir) / "completion.json").read_text(encoding="utf-8")
    )

    assert result.compiler_input_manifest == completion["compiler_input_manifest"]
    assert result.compiler_input_manifest_sha256 == completion[
        "compiler_input_manifest_sha256"
    ]
    assert result.compiler_input_manifest_sha256 == (
        buildcache.s8b_compiler_input.manifest_sha256(
            result.compiler_input_manifest
        )
    )
    assert completion["preimage"]["source_snapshot_sha256"] == (
        buildcache.s8b_expected_materialization.snapshot_tree_digest(
            tmp_path / "ccbench"
        )
    )


def test_v3_result_exposes_runtime_dependency_roots_without_new_durable_field(
        tmp_path, monkeypatch):
    run, dependency_input = _v3_dependency_prefix_build_fixture(
        tmp_path, monkeypatch,
    )
    fresh = run()
    hit = run()
    expected_roots = (str(dependency_input.parents[1].resolve()),)
    completion = json.loads(
        (Path(fresh.build_dir) / "completion.json").read_text(encoding="utf-8")
    )

    assert fresh.compiler_input_dependency_prefix_roots == expected_roots
    assert hit.compiler_input_dependency_prefix_roots == expected_roots
    assert "compiler_input_dependency_prefix_roots" not in completion
    assert "dependency_prefix_roots" not in completion["compiler_input_manifest"]
    assert completion["preimage"]["dependency_prefix"] == list(expected_roots)


def test_v3_schema_pin_uses_distinct_entry_from_v2_completion(monkeypatch):
    genome = Genome("silo", {"BACK_OFF": 1})
    toolchain = {
        role: {
            "requested": role,
            "realpath": f"/tool/{role}",
            "version_first_line": "v1",
        }
        for role in ("cc", "cxx", "cmake")
    }
    kwargs = dict(
        source_snapshot_sha256="1" * 64,
        site="test", dependency_prefix=["/job/dependency"],
        admission={"receipt": "fixture"},
        compiler_input_policy="snapshot-and-external-hashes/v1",
    )
    current = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        **kwargs,
    )
    monkeypatch.setattr(
        buildcache.s8b_compiler_input,
        "MANIFEST_SCHEMA",
        buildcache.s8b_compiler_input.PREVIOUS_MANIFEST_SCHEMA,
    )
    previous = buildcache._v2_identity(
        genome, "a" * 40, False, "stock", "cc", "cxx", toolchain,
        **kwargs,
    )

    assert current[0]["dependency_prefix"] == previous[0]["dependency_prefix"]
    assert current[0]["compiler_input_manifest_schema"] == (
        "s8b-compiler-input/v3"
    )
    assert previous[0]["compiler_input_manifest_schema"] == (
        "s8b-compiler-input/v2"
    )
    assert current[1] != previous[1]


def _v3_dependency_prefix_build_fixture(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    source_root = tmp_path / "ccbench"
    source_root.mkdir()
    (source_root / "compiler-input.hh").write_bytes(
        b"snapshot compiler input\n"
    )
    dependency_root = tmp_path / "dependency-install"
    dependency_input = dependency_root / "include" / "dependency.hh"
    dependency_input.parent.mkdir(parents=True)
    dependency_input.write_bytes(b"dependency compiler input\n")

    def collect(
            _build_dir, _snapshot_root, *, target, allow_external_inputs,
            expected_evolve_block_sources,
            origin_fetchcontent_masstree_root,
            current_fetchcontent_masstree_root,
            origin_dependency_prefix_roots,
            current_dependency_prefix_roots):
        assert allow_external_inputs is True
        assert expected_evolve_block_sources is None
        assert origin_fetchcontent_masstree_root is not None
        assert current_fetchcontent_masstree_root is not None
        expected_roots = (str(dependency_root.resolve()),)
        assert tuple(origin_dependency_prefix_roots) == expected_roots
        assert tuple(current_dependency_prefix_roots) == expected_roots
        manifest = {
            "schema_version": buildcache.s8b_compiler_input.MANIFEST_SCHEMA,
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": target,
            "depfile_count": 1,
            "input_policy": "snapshot-and-external-hashes/v1",
            "inputs": [{
                "root": "dependency-prefix",
                "path": "include/dependency.hh",
                "sha256": hashlib.sha256(
                    dependency_input.read_bytes()
                ).hexdigest(),
            }],
        }
        return buildcache.s8b_compiler_input.CompilerInputManifest(
            manifest,
            buildcache.s8b_compiler_input.manifest_sha256(manifest),
        )

    monkeypatch.setattr(
        buildcache.s8b_compiler_input,
        "collect_compiler_input_manifest",
        collect,
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(source_root),
    )
    snapshot_sha256 = (
        buildcache.s8b_expected_materialization.snapshot_tree_digest(source_root)
    )

    def run():
        return buildcache._build_v2_impl(
            genome,
            admission=admission,
            build_context=context,
            source_evidence=evidence,
            source_snapshot_sha256=snapshot_sha256,
            allow_external_compiler_inputs=True,
            expected_evolve_block_sources=None,
            contract=_contract(1),
            ccbench_commit="a" * 40,
            trace=True,
            src_token="stock",
            cc="test-cc",
            cxx="test-cxx",
            cache_root=str(tmp_path / "cache"),
            ccbench_dir=str(source_root),
            dependency_prefix=str(dependency_root),
        )

    return run, dependency_input


def test_v3_dependency_prefix_hit_revalidates_same_identity_without_rebuild(
        tmp_path, monkeypatch):
    run, _dependency_input = _v3_dependency_prefix_build_fixture(
        tmp_path, monkeypatch,
    )
    fresh = run()
    calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    hit = run()

    assert fresh.cached is False
    assert hit.cached is True
    assert hit.build_dir == fresh.build_dir
    assert calls == []


def _install_real_compiler_input_build_without_masstree_resolution(
        monkeypatch, tmp_path: Path, *, input_path: Path) -> list[str]:
    real_collector = (
        buildcache.s8b_compiler_input.collect_compiler_input_manifest
    )
    _fake_build_environment(monkeypatch, tmp_path)
    monkeypatch.setattr(
        buildcache.s8b_compiler_input,
        "collect_compiler_input_manifest",
        real_collector,
    )
    events = []

    def run_without_masstree_keys(
            cmd, what, timeout_s=None, *, site=None, env=None):
        del timeout_s, site, env
        events.append(what)
        if what == "configure":
            staging = Path(cmd[cmd.index("-B") + 1])
            target_dir = (
                staging / "cc" / "silo" / "CMakeFiles"
                / "ycsb_silo.exe.dir"
            )
            target_dir.mkdir(parents=True)
            (staging / "CMakeCache.txt").write_text(
                "CMAKE_GENERATOR:INTERNAL=Unix Makefiles\n",
                encoding="utf-8",
            )
            (target_dir / "flags.make").write_text(
                "# compile CXX with /usr/bin/c++\n"
                "CXX_DEFINES = -DBACK_OFF=1\n"
                "CXX_INCLUDES =\n"
                "CXX_FLAGS = -O3 -std=c++20\n",
                encoding="utf-8",
            )
            (target_dir / "link.txt").write_text(
                "/usr/bin/c++ "
                "cc/silo/CMakeFiles/ycsb_silo.exe.dir/compiler-input.cc.o "
                "-o cc/silo/ycsb_silo.exe\n",
                encoding="utf-8",
            )
            (target_dir / "compiler-input.cc.o.d").write_text(
                "cc/silo/CMakeFiles/ycsb_silo.exe.dir/compiler-input.cc.o: "
                f"{input_path.resolve()}\n",
                encoding="utf-8",
            )
        elif what == "build":
            staging = Path(cmd[cmd.index("--build") + 1])
            binary = staging / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(b"snapshot-bound binary\n")

    monkeypatch.setattr(buildcache, "_run", run_without_masstree_keys)
    return events


def test_v2_snapshot_only_bound_build_collects_without_masstree_keys(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    source_root = tmp_path / "ccbench"
    source_root.mkdir()
    compiler_header = source_root / "compiler-input.hh"
    compiler_header.write_bytes(b"snapshot compiler input\n")
    events = _install_real_compiler_input_build_without_masstree_resolution(
        monkeypatch, tmp_path, input_path=compiler_header,
    )

    result = _build(
        tmp_path, _contract(1), ccbench_dir=str(source_root),
        source_snapshot_sha256=(
            buildcache.s8b_expected_materialization.snapshot_tree_digest(
                source_root
            )
        ),
    )

    assert events == ["configure", "build"]
    assert result.compiler_input_manifest["inputs"] == [{
        "root": "snapshot",
        "path": "compiler-input.hh",
        "sha256": hashlib.sha256(compiler_header.read_bytes()).hexdigest(),
    }]


def test_v2_external_input_policy_still_requires_masstree_resolution_root(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    source_root = tmp_path / "ccbench"
    source_root.mkdir()
    (source_root / "compiler-input.hh").write_bytes(b"snapshot sentinel\n")
    outside = tmp_path / "external" / "compiler-input.hh"
    outside.parent.mkdir()
    outside.write_bytes(b"external compiler input\n")
    events = _install_real_compiler_input_build_without_masstree_resolution(
        monkeypatch, tmp_path, input_path=outside,
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(source_root),
    )

    with pytest.raises(buildcache.BuildCacheError, match="masstree 解決 key"):
        buildcache._build_v2_impl(
            genome,
            admission=admission,
            build_context=context,
            source_evidence=evidence,
            source_snapshot_sha256=(
                buildcache.s8b_expected_materialization.snapshot_tree_digest(
                    source_root
                )
            ),
            allow_external_compiler_inputs=True,
            expected_evolve_block_sources=None,
            contract=_contract(1),
            ccbench_commit="a" * 40,
            trace=True,
            src_token="stock",
            cc="test-cc",
            cxx="test-cxx",
            cache_root=str(tmp_path / "cache"),
            ccbench_dir=str(source_root),
        )
    assert events == ["configure", "build"]
    assert list((tmp_path / "cache").rglob("completion.json")) == []


def test_v2_collects_manifest_before_staging_discard(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    events = []
    original_collect = (
        buildcache.s8b_compiler_input.collect_compiler_input_manifest
    )
    original_discard = buildcache._discard_build_dir

    def observe_collect(build_dir, snapshot_root, **kwargs):
        assert Path(build_dir).is_dir()
        events.append("collect")
        return original_collect(build_dir, snapshot_root, **kwargs)

    def observe_discard(path):
        if ".staging-" in str(path):
            events.append("discard")
        return original_discard(path)

    monkeypatch.setattr(
        buildcache.s8b_compiler_input,
        "collect_compiler_input_manifest",
        observe_collect,
    )
    monkeypatch.setattr(buildcache, "_discard_build_dir", observe_discard)

    _build(tmp_path, _contract(1), bind_source_snapshot=True)
    assert events == ["collect", "discard"]


def test_v2_hit_revalidates_compiler_input_bytes_without_rebuilding(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    result = _build(tmp_path, _contract(1), bind_source_snapshot=True)
    completion_path = Path(result.build_dir) / "completion.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    completion["compiler_input_manifest"]["inputs"][0]["sha256"] = "0" * 64
    completion["compiler_input_manifest_sha256"] = (
        buildcache.s8b_compiler_input.manifest_sha256(
            completion["compiler_input_manifest"]
        )
    )
    completion_path.write_text(json.dumps(completion), encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(buildcache.BuildCacheError, match="compiler input manifest"):
        _build(tmp_path, _contract(1), bind_source_snapshot=True)
    assert calls == []


def _install_fetchcontent_compiler_manifest_collector(monkeypatch):
    def collect(
            _build_dir, _snapshot_root, *, target, allow_external_inputs,
            expected_evolve_block_sources,
            origin_fetchcontent_masstree_root,
            current_fetchcontent_masstree_root,
            origin_dependency_prefix_roots,
            current_dependency_prefix_roots):
        assert allow_external_inputs is True
        assert expected_evolve_block_sources is None
        assert tuple(origin_dependency_prefix_roots) == tuple(
            current_dependency_prefix_roots
        )
        origin = Path(origin_fetchcontent_masstree_root)
        current = Path(current_fetchcontent_masstree_root)
        relative = Path("tracked.hh")
        digest = hashlib.sha256((origin / relative).read_bytes()).hexdigest()
        assert hashlib.sha256((current / relative).read_bytes()).hexdigest() == digest
        manifest = {
            "schema_version": buildcache.s8b_compiler_input.MANIFEST_SCHEMA,
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": target,
            "depfile_count": 1,
            "inputs": [{
                "root": "fetchcontent-masstree",
                "path": relative.as_posix(),
                "sha256": digest,
            }],
            "input_policy": "snapshot-and-external-hashes/v1",
        }
        return buildcache.s8b_compiler_input.CompilerInputManifest(
            manifest,
            buildcache.s8b_compiler_input.manifest_sha256(manifest),
        )

    monkeypatch.setattr(
        buildcache.s8b_compiler_input,
        "collect_compiler_input_manifest",
        collect,
    )


def _v2_fetchcontent_rebind_fixture(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    _install_fetchcontent_compiler_manifest_collector(monkeypatch)
    source_root = tmp_path / "ccbench"
    source_root.mkdir()
    (source_root / "compiler-input.hh").write_bytes(
        b"compiler input fixture\n"
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    descriptor = (
        buildcache.s8b_expected_materialization.
        expected_materialization_descriptor(
            ccbench_commit="a" * 40,
            configuration="stock_common",
            declaration={
                "configuration": "stock_common",
                "flags": {"BACK_OFF": 1},
            },
        )
    )
    evidence = _source_evidence(genome, "a" * 40, str(source_root))
    snapshot_sha256 = (
        buildcache.s8b_expected_materialization.snapshot_tree_digest(
            source_root
        )
    )

    @contextlib.contextmanager
    def admitted_snapshot(**kwargs):
        assert kwargs["ccbench_commit"] == descriptor.ccbench_commit
        assert kwargs["configuration"] == descriptor.configuration
        assert kwargs["declaration"] == descriptor.declaration
        assert (tmp_path / "cache").is_dir()
        yield buildcache.s8b_expected_materialization.AdmittedBuildSnapshot(
            source_snapshot_sha256=snapshot_sha256,
            expected_materialization_sha256=snapshot_sha256,
            source_evidence=evidence,
        )

    monkeypatch.setattr(
        buildcache.s8b_expected_materialization,
        "admitted_build_snapshot",
        admitted_snapshot,
    )
    base_a = tmp_path / "fetchcontent-a"
    base_a.mkdir()
    receipt = _write_fetchcontent_dependency(base_a)
    first = _build(
        tmp_path, _contract(1),
        expected_materialization_descriptor=descriptor,
        fetchcontent_base_dir=str(base_a.resolve()),
        fetchcontent_dependency_receipt=receipt,
        current_compiler_input_masstree_root=(
            base_a.resolve() / "masstree-src"
        ),
    )
    base_b = tmp_path / "fetchcontent-b"
    base_b.mkdir()
    shutil.copytree(base_a / "masstree-src", base_b / "masstree-src")
    shutil.rmtree(base_a)
    return first, base_b, receipt, descriptor


def test_v2_hit_rebinds_fetchcontent_inputs_to_current_root(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_v2_hit_rebinds_fetchcontent_inputs_to_current_root_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _v2_hit_rebinds_fetchcontent_inputs_to_current_root_case(
        tmp_path, monkeypatch):
    first, base_b, receipt, descriptor = _v2_fetchcontent_rebind_fixture(
        tmp_path, monkeypatch,
    )
    calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    hit = _build(
        tmp_path, _contract(1),
        expected_materialization_descriptor=descriptor,
        fetchcontent_base_dir=str(base_b.resolve()),
        fetchcontent_dependency_receipt=receipt,
        current_compiler_input_masstree_root=(
            base_b.resolve() / "masstree-src"
        ),
    )

    assert first.cached is False
    assert hit.cached is True
    assert hit.build_dir == first.build_dir
    assert calls == []


@pytest.mark.parametrize("mutation", ["missing", "hash", "symlink"])
def test_v2_hit_validation_failure_never_rebuilds(tmp_path, mutation):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_v2_hit_validation_failure_never_rebuilds_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path, mutation=mutation,
    )
    assert result == {"case": case, "completed": True}


def _v2_hit_validation_failure_never_rebuilds_case(
        tmp_path, monkeypatch, mutation):
    _first, base_b, receipt, descriptor = _v2_fetchcontent_rebind_fixture(
        tmp_path, monkeypatch,
    )
    header = base_b / "masstree-src" / "tracked.hh"
    if mutation == "missing":
        header.unlink()
    elif mutation == "hash":
        header.write_bytes(b"current bytes drift\n")
    else:
        target = base_b / "replacement.hh"
        target.write_bytes(header.read_bytes())
        header.unlink()
        header.symlink_to(target)
    calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(buildcache.BuildCacheError, match="compiler input manifest"):
        _build(
            tmp_path, _contract(1),
            expected_materialization_descriptor=descriptor,
            fetchcontent_base_dir=str(base_b.resolve()),
            fetchcontent_dependency_receipt=receipt,
            current_compiler_input_masstree_root=(
                base_b.resolve() / "masstree-src"
            ),
        )
    assert calls == []


def test_v2_hit_rejects_completion_without_compiler_input_proof(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    result = _build(tmp_path, _contract(1), bind_source_snapshot=True)
    completion_path = Path(result.build_dir) / "completion.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    completion.pop("compiler_input_manifest")
    completion.pop("compiler_input_manifest_sha256")
    completion_path.write_text(json.dumps(completion), encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(buildcache.BuildCacheError, match="field 集合"):
        _build(tmp_path, _contract(1), bind_source_snapshot=True)
    assert calls == []


def test_v2_rejects_source_snapshot_digest_mismatch_before_build(
        tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(buildcache.BuildCacheError, match="tree digest"):
        _build(
            tmp_path, _contract(1), source_snapshot_sha256="0" * 64,
        )
    assert calls == []


def test_v2_rejects_snapshot_changed_during_build(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    original_run = buildcache._run

    def mutate_after_build(cmd, what, **kwargs):
        original_run(cmd, what, **kwargs)
        if what == "build":
            (tmp_path / "ccbench" / "compiler-input.hh").write_bytes(
                b"mutated during build\n"
            )

    monkeypatch.setattr(buildcache, "_run", mutate_after_build)
    with pytest.raises(buildcache.BuildCacheError, match="tree digest"):
        _build(tmp_path, _contract(1), bind_source_snapshot=True)
    assert list((tmp_path / "cache").rglob("completion.json")) == []


def test_completion_manifest_rejects_missing_receipt(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    result = _build(tmp_path, _contract(1))
    manifest_path = Path(result.build_dir) / "completion.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("admission")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    build_calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: build_calls.append((args, kwargs)),
    )
    with pytest.raises(buildcache.BuildCacheError, match="field 集合"):
        _build(tmp_path, _contract(1))
    assert build_calls == []


def test_v2_contract_trace_four_quadrants_are_distinct(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    paths = {
        _build(tmp_path, contract, trace=trace).build_dir
        for contract in (_contract(1), _contract(2))
        for trace in (False, True)
    }
    assert len(paths) == 4


def test_v2_missing_manifest_and_binary_mismatch_fail_closed(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path, payload=b"original")
    first = _build(tmp_path, _contract(1))
    manifest = Path(first.build_dir) / "completion.json"
    manifest.unlink()
    with pytest.raises(buildcache.BuildCacheError, match="manifest"):
        _build(tmp_path, _contract(1))
    assert Path(first.binary).read_bytes() == b"original"

    # 別 contract で正常 entry を作り、manifest が束縛した binary bytes だけを壊す。
    second = _build(tmp_path, _contract(2))
    Path(second.binary).chmod(0o700)  # same-UID owner は publish 後も chmod できる残余。
    Path(second.binary).write_bytes(b"tampered")
    with pytest.raises(buildcache.BuildCacheError, match="sha256"):
        _build(tmp_path, _contract(2))
    assert Path(second.binary).read_bytes() == b"tampered"  # 上書き・自動修復しない


@pytest.mark.parametrize("mutation", ["partial-marker", "missing-commit"])
def test_v2_tampered_manifest_fails_closed_without_touching_binary(
        tmp_path, monkeypatch, mutation):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path, payload=b"immutable-binary")
    result = _build(tmp_path, _contract(1))
    manifest_path = Path(result.build_dir) / "completion.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if mutation == "partial-marker":
        manifest["completion_marker"] = "partial"
    else:
        manifest["preimage"].pop("ccbench_commit")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(buildcache.BuildCacheError):
        _build(tmp_path, _contract(1))
    assert Path(result.binary).read_bytes() == b"immutable-binary"


def test_v2_stale_claim_blocks_even_a_complete_hit(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    result = _build(tmp_path, _contract(1))
    claim = Path(result.build_dir).with_name(Path(result.build_dir).name + ".building")
    claim.mkdir()
    (claim / "owner.json").write_text(
        json.dumps({"pid": 999999, "host": "stale", "starttime": 0}),
        encoding="utf-8",
    )
    with pytest.raises(buildcache.BuildCacheError, match="stale|手動回収"):
        _build(tmp_path, _contract(1))
    assert claim.exists()  # stale 自動削除・retry はしない


def test_v2_runs_all_observer_and_identity_checks_on_fresh_and_hit(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    calls = {"resolve": 0, "trace_diff": 0, "nm": 0}

    def resolved(genome, commit, *, ccbench_dir, cxx):
        calls["resolve"] += 1
        return _source_evidence(genome, commit, ccbench_dir)

    def trace_diff(*args, **kwargs):
        calls["trace_diff"] += 1

    def no_trace(*args, **kwargs):
        calls["nm"] += 1

    buildcache.source_digest.resolve_evidence = resolved
    buildcache.source_digest.assert_trace_diff_matches_head = trace_diff
    monkeypatch.setattr(buildcache, "_assert_no_trace_symbols", no_trace)
    fresh = _build(tmp_path, _contract(1), trace=False)
    hit = _build(tmp_path, _contract(1), trace=False)
    assert not fresh.cached and hit.cached
    assert calls == {"resolve": 2, "trace_diff": 2, "nm": 2}


def test_v2_manifest_records_complete_identity(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path, payload=b"manifest-payload")
    result = _build(tmp_path, _contract(1), trace=False)
    manifest = json.loads((Path(result.build_dir) / "completion.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "buildcache/v2"
    assert manifest["completion_marker"] == "complete"
    assert manifest["contract_sha256"] == _contract(1).contract_sha256
    preimage = dict(manifest["preimage"])
    preimage.pop("site", None)  # M7 は専用 cache-miss node だけへ帰属させる。
    preimage.pop("dependency_prefix", None)  # M8 も専用 node だけへ帰属させる。
    assert preimage == {
        "admission": manifest["admission"],
        "cc": "test-cc",
        "ccbench_commit": "a" * 40,
        "cxx": "test-cxx",
        "genome_canonical": "silo|BACK_OFF=1",
        "src_token": "stock",
        "toolchain_manifest_sha256": manifest["preimage"]["toolchain_manifest_sha256"],
        "trace": False,
    }
    assert manifest["admission"] == manifest["preimage"]["admission"]
    assert set(manifest["admission"]) == {
        "schema", "class", "policy_sha256", "source", "generator_id",
        "review_id", "input_sha256", "generator_receipt", "review_receipt",
        "authority_kind", "receipt_sha256",
    }
    assert len(manifest["preimage"]["toolchain_manifest_sha256"]) == 64
    assert manifest["toolchain"]["cxx"]["version_first_line"] == "cxx version A"
    assert all(
        set(entry) == {"requested", "realpath", "version_first_line"}
        for entry in manifest["toolchain"].values()
    )
    assert manifest["binary"]["sha256"] == hashlib.sha256(b"manifest-payload").hexdigest()


@pytest.mark.parametrize("api,metadata", [("legacy", "admission.json"), ("v2", "completion.json")])
def test_copyout_fresh_publishes_exact_host_set_and_hit_is_executable(
        tmp_path, monkeypatch, api, metadata):
    """M6/M12/M13: extras stay untrusted; a normal nlink=1 binary remains accepted."""
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    payload = b"#!/bin/sh\nexit 0\n"
    _fake_build_environment(monkeypatch, tmp_path, payload=payload)
    calls = _install_staging_artifacts(
        monkeypatch, leaf_kind="regular", payload=payload,
    )
    fresh = _call_copyout_api(tmp_path, api)
    hit = _call_copyout_api(tmp_path, api)

    final_root = Path(fresh.build_dir)
    expected_binary = "cc/silo/ycsb_silo.exe"
    assert _published_non_directory_members(final_root) == {expected_binary, metadata}
    assert Path(fresh.binary).read_bytes() == payload
    independent = hashlib.sha256(payload).hexdigest()
    assert fresh.bin_sha256 == independent == hit.bin_sha256
    assert json.loads((final_root / metadata).read_text(encoding="utf-8")) != {"forged": True}
    stat_mode = Path(fresh.binary).stat().st_mode & 0o777
    assert stat_mode == 0o500
    executed = subprocess.run(
        [fresh.binary], capture_output=True, check=False, timeout=_SEALED_COMMAND_TIMEOUT_S,
    )
    assert executed.returncode == 0
    assert not fresh.cached and hit.cached
    assert calls == ["configure", "build"]


@pytest.mark.parametrize("api,metadata", [("legacy", "admission.json"), ("v2", "completion.json")])
def test_m6_host_metadata_never_uses_staging_bytes(
        tmp_path, monkeypatch, api, metadata):
    """M6 single-reason anchor: only the forged metadata byte source differs."""
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)

    def fake_run(cmd, what, timeout_s=None, *, site=None, env=None):
        if what == "build":
            staging = Path(cmd[cmd.index("--build") + 1])
            binary = staging / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"metadata-source-anchor")
            (staging / metadata).write_text('{"forged":true}\n', encoding="utf-8")

    monkeypatch.setattr(buildcache, "_run", fake_run)
    result = _call_copyout_api(tmp_path, api)
    actual = json.loads((Path(result.build_dir) / metadata).read_text(encoding="utf-8"))
    assert actual != {"forged": True}


def test_m13_v2_rejects_non_allowlisted_member_in_clean_candidate(tmp_path, monkeypatch):
    """M13: one non-allowlisted member copied into clean is the single failure reason."""
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)

    def fake_run(cmd, what, timeout_s=None, *, site=None, env=None):
        if what == "build":
            staging = Path(cmd[cmd.index("--build") + 1])
            binary = staging / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"m13-anchor")
            (staging / "CMakeCache.txt").write_bytes(b"cache")

    monkeypatch.setattr(buildcache, "_run", fake_run)
    result = _call_copyout_api(tmp_path, "v2")
    assert _published_non_directory_members(Path(result.build_dir)) == {
        "cc/silo/ycsb_silo.exe", "completion.json",
    }


@pytest.mark.parametrize("api", ["legacy", "v2"])
@pytest.mark.parametrize("leaf_kind", ["symlink", "fifo", "directory", "hardlink"])
def test_copyout_rejects_unsafe_allowlisted_leaf_without_completed_entry(
        tmp_path, monkeypatch, api, leaf_kind):
    """M1/M2/M3: M2 evidence is FIFO only; directory read(EISDIR) can pre-empt it."""
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    calls = _install_staging_artifacts(
        monkeypatch, leaf_kind=leaf_kind, payload=b"unsafe-leaf",
    )
    with pytest.raises((buildcache.BuildError, buildcache.BuildCacheError)):
        _call_copyout_api(tmp_path, api)
    assert calls == ["configure", "build"]
    assert not list((tmp_path / "cache").rglob("*staging-*"))
    assert not list((tmp_path / "cache").rglob(".publish-*"))
    if api == "v2":
        parent = next((tmp_path / "cache" / "contracts").iterdir())
        assert len(list(parent.glob("*.building"))) == 1
        assert not [path for path in parent.iterdir() if not path.name.endswith(".building")]
    else:
        assert not [path for path in (tmp_path / "cache").iterdir() if path.name.startswith("silo_")]


@pytest.mark.parametrize("api", ["legacy", "v2"])
def test_copyout_destination_swap_after_hash_is_rejected_on_same_fd(
        tmp_path, monkeypatch, api):
    """M5: disabling verify_destination_entry alone lets the post-hash swap survive."""
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    _install_staging_artifacts(
        monkeypatch, leaf_kind="regular", payload=b"#!/bin/sh\nexit 0\n",
    )
    observed = {}

    def observe_nm(binary, *, binary_fd=None):
        assert binary_fd is not None
        observed["nm"] = os.fstat(binary_fd).st_ino

    real_hash = buildcache._full_sha256_fd

    def swap_after_hash(fd, path):
        digest = real_hash(fd, path)
        assert "sha" not in observed
        observed["sha"] = os.fstat(fd).st_ino
        observed["hashed_fd"] = fd
        clean_binary = Path(os.readlink(f"/proc/self/fd/{fd}"))
        assert clean_binary.name == "ycsb_silo.exe"
        assert clean_binary.parent.parent.parent.name.startswith(".publish-")
        held_name = clean_binary.with_name("held-original")
        clean_binary.rename(held_name)
        clean_binary.write_bytes(b"replacement-path-bytes")
        clean_binary.chmod(0o500)
        return digest

    real_fsync = buildcache.os.fsync

    def observe_fsync(fd):
        if fd == observed.get("hashed_fd"):
            assert "fsync" not in observed
            observed["fsync"] = os.fstat(fd).st_ino
        return real_fsync(fd)

    monkeypatch.setattr(buildcache, "_assert_no_trace_symbols", observe_nm)
    monkeypatch.setattr(buildcache, "_full_sha256_fd", swap_after_hash)
    monkeypatch.setattr(buildcache.os, "fsync", observe_fsync)
    with pytest.raises(buildcache.BuildCacheError, match="destination entry"):
        _call_copyout_api(tmp_path, api, trace=False)
    assert observed["nm"] == observed["sha"] == observed["fsync"]
    assert not list((tmp_path / "cache").rglob(".publish-*"))
    assert not list((tmp_path / "cache").rglob("ycsb_silo.exe"))


@pytest.mark.parametrize("api", ["legacy", "v2"])
def test_copyout_sha_fd_inode_is_the_published_binary_inode(
        tmp_path, monkeypatch, api):
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    _install_staging_artifacts(
        monkeypatch, leaf_kind="regular", payload=b"published-inode",
    )
    observed = []
    real_hash = buildcache._full_sha256_fd

    def observe_hash(fd, path):
        observed.append(os.fstat(fd).st_ino)
        return real_hash(fd, path)

    monkeypatch.setattr(buildcache, "_full_sha256_fd", observe_hash)
    result = _call_copyout_api(tmp_path, api)
    assert observed == [Path(result.binary).stat().st_ino]


@pytest.mark.parametrize("api", ["legacy", "v2"])
def test_cache_hit_keeps_legacy_extra_member_compatibility(tmp_path, monkeypatch, api):
    """A-6 residual; this compatibility test is not fresh-gate call-site evidence."""
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    fresh = _call_copyout_api(tmp_path, api)
    (Path(fresh.build_dir) / "old-extra-member").write_bytes(b"legacy-extra")
    hit = _call_copyout_api(tmp_path, api)
    assert hit.cached


@pytest.mark.parametrize("api", ["legacy", "v2"])
@pytest.mark.parametrize("attack", ["binary-intermediate", "metadata"])
def test_cache_hit_rejects_symlinked_member_without_running_build(
        tmp_path, monkeypatch, api, attack):
    """M8 uses binary-intermediate; legacy swaps only after its lexists precheck."""
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    first = _call_copyout_api(tmp_path, api)
    bdir = Path(first.build_dir)
    swapped = False
    if attack == "binary-intermediate":
        def swap_intermediate():
            nonlocal swapped
            real_cc = bdir / "cc.real"
            (bdir / "cc").rename(real_cc)
            (bdir / "cc").symlink_to(real_cc, target_is_directory=True)
            swapped = True

        if api == "legacy":
            real_lexists = buildcache._relative_entry_lexists

            def lexists_then_swap(root_fd, relpath, *, label):
                exists = real_lexists(root_fd, relpath, label=label)
                if exists and not swapped:
                    swap_intermediate()
                return exists

            monkeypatch.setattr(
                buildcache, "_relative_entry_lexists", lexists_then_swap,
            )
        else:
            swap_intermediate()
    else:
        metadata = bdir / ("completion.json" if api == "v2" else "admission.json")
        real_metadata = metadata.with_suffix(".real")
        metadata.rename(real_metadata)
        metadata.symlink_to(real_metadata)
    build_calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: build_calls.append((args, kwargs)),
    )
    error_match = (
        "no-follow open"
        if api == "legacy" and attack == "binary-intermediate" else None
    )
    with pytest.raises(buildcache.BuildCacheError, match=error_match):
        _call_copyout_api(tmp_path, api)
    if attack == "binary-intermediate":
        assert swapped
    assert build_calls == []


def test_legacy_hit_rejects_broken_binary_leaf_symlink_without_build(
        tmp_path, monkeypatch):
    _fake_build_environment(monkeypatch, tmp_path)
    first = _call_copyout_api(tmp_path, "legacy")
    binary = Path(first.binary)
    binary.unlink()
    binary.symlink_to(binary.with_name("missing-target"))
    build_calls = []
    monkeypatch.setattr(
        buildcache, "_run", lambda *args, **kwargs: build_calls.append((args, kwargs)),
    )
    with pytest.raises(buildcache.BuildCacheError):
        _call_copyout_api(tmp_path, "legacy")
    assert build_calls == []


@pytest.mark.parametrize("entry_kind", ["symlink", "file"])
def test_clear_stale_build_dir_rejects_symlink_and_non_directory(
        tmp_path, entry_kind):
    """Helper contract only; this is not proof that a production call-site invokes it."""
    bdir = tmp_path / "cache-entry"
    if entry_kind == "symlink":
        target = tmp_path / "target"
        target.mkdir()
        bdir.symlink_to(target, target_is_directory=True)
    else:
        bdir.write_bytes(b"not-a-directory")
    with pytest.raises(buildcache.BuildCacheError, match="symlink|非 directory"):
        buildcache._clear_stale_build_dir(
            str(bdir), str(bdir / "cc" / "silo" / "ycsb_silo.exe"),
        )
    assert bdir.exists() or bdir.is_symlink()


@pytest.mark.parametrize("api", ["legacy", "v2"])
def test_copyout_gate_order_is_exact_through_rename(tmp_path, monkeypatch, api):
    """Auxiliary exact-order evidence, not evidence from a real C++ publish path."""
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    _install_staging_artifacts(
        monkeypatch, leaf_kind="regular", payload=b"#!/bin/sh\nexit 0\n",
    )
    events = []
    monkeypatch.setattr(buildcache, "_recheck_source_evidence", lambda *a, **k: events.append("recheck"))
    monkeypatch.setattr(buildcache, "_assert_trace_diff", lambda *a, **k: events.append("trace-diff"))
    monkeypatch.setattr(
        buildcache, "_assert_no_trace_symbols",
        lambda *a, **k: events.append("nm"),
    )
    real_hash = buildcache._full_sha256_fd

    def observed_hash(fd, path):
        events.append("sha")
        return real_hash(fd, path)

    real_fsync = buildcache.os.fsync

    def observed_fsync(fd):
        info = os.fstat(fd)
        if (stat.S_ISREG(info.st_mode) and (info.st_mode & 0o777) == 0o500
                and "fsync" not in events):
            events.append("fsync")
        return real_fsync(fd)

    real_rename = buildcache.os.rename

    def observed_rename(src, dst, *args, **kwargs):
        if str(src).startswith(".publish-"):
            events.append("rename")
        return real_rename(src, dst, *args, **kwargs)

    monkeypatch.setattr(buildcache, "_full_sha256_fd", observed_hash)
    monkeypatch.setattr(buildcache.os, "fsync", observed_fsync)
    monkeypatch.setattr(buildcache.os, "rename", observed_rename)
    _call_copyout_api(tmp_path, api, trace=False)
    assert events == ["recheck", "trace-diff", "nm", "sha", "fsync", "rename"]


def test_no_trace_symbols_uses_held_fd_and_keeps_path_compatibility(
        tmp_path, monkeypatch):
    """Helper contract only; production call-site firing is covered separately."""
    binary = tmp_path / "display-binary"
    binary.write_bytes(b"bytes")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(buildcache.subprocess, "run", fake_run)
    fd = os.open(binary, os.O_RDONLY)
    try:
        buildcache._assert_no_trace_symbols(str(binary), binary_fd=fd)
    finally:
        os.close(fd)
    buildcache._assert_no_trace_symbols(str(binary))
    assert calls[0][0] == ["nm", "-C", f"/proc/self/fd/{fd}"]
    assert calls[0][1]["pass_fds"] == (fd,)
    assert calls[1][0] == ["nm", "-C", str(binary)]
    assert "pass_fds" not in calls[1][1]


@pytest.mark.parametrize("constant", buildcache._SECURE_FLAG_NAMES)
def test_secure_copyout_environment_contract_missing_constant_fails_closed(
        monkeypatch, constant):
    """M7 helper contract; alone this is not production call-site firing evidence."""
    monkeypatch.delattr(buildcache.os, constant)
    with pytest.raises(buildcache.BuildCacheError, match="constant"):
        buildcache._require_secure_fs_contract()


@pytest.mark.parametrize("set_name", ["supports_dir_fd", "supports_follow_symlinks"])
def test_secure_copyout_environment_contract_missing_capability_set_fails_closed(
        monkeypatch, set_name):
    """M7 helper contract: a missing capability set is rejected at preflight."""
    monkeypatch.delattr(buildcache.os, set_name)
    with pytest.raises(buildcache.BuildCacheError, match="capability set"):
        buildcache._require_secure_fs_contract()


def test_secure_copyout_required_dir_fd_functions_match_literal_contract():
    """M7: production cannot shrink the independently fixed six-member test set."""
    assert buildcache._SECURE_DIR_FD_FUNCTIONS == _REQUIRED_SECURE_DIR_FD_FUNCTIONS


@pytest.mark.parametrize("function_name", _REQUIRED_SECURE_DIR_FD_FUNCTIONS)
def test_secure_copyout_environment_contract_missing_dir_fd_member_fails_closed(
        monkeypatch, function_name):
    """M7 single-reason anchor: removing one dir_fd membership is sufficient."""
    original = set(buildcache.os.supports_dir_fd)
    required = buildcache._ORIGINAL_SECURE_DIR_FD_CALLABLES[function_name]
    assert required in original
    monkeypatch.setattr(buildcache.os, "supports_dir_fd", original - {required})
    with pytest.raises(buildcache.BuildCacheError, match=function_name):
        buildcache._require_secure_fs_contract()


def test_secure_copyout_environment_contract_missing_follow_symlinks_member_fails_closed(
        monkeypatch):
    """M7 single-reason anchor: stat follow_symlinks membership is mandatory."""
    original = set(buildcache.os.supports_follow_symlinks)
    assert buildcache._ORIGINAL_OS_STAT in original
    monkeypatch.setattr(
        buildcache.os, "supports_follow_symlinks",
        original - {buildcache._ORIGINAL_OS_STAT},
    )
    with pytest.raises(buildcache.BuildCacheError, match="follow_symlinks=False"):
        buildcache._require_secure_fs_contract()


def test_secure_copyout_environment_contract_missing_proc_self_fd_fails_closed(
        monkeypatch):
    """M7 single-reason anchor: held-fd reopen requires usable /proc/self/fd."""
    monkeypatch.setattr(buildcache, "_PROC_SELF_FD_AVAILABLE", False)
    with pytest.raises(buildcache.BuildCacheError, match="/proc/self/fd"):
        buildcache._require_secure_fs_contract()


@pytest.mark.parametrize("function_name", _REQUIRED_SECURE_DIR_FD_FUNCTIONS)
def test_secure_copyout_environment_contract_accepts_delegate_wrappers(
        monkeypatch, function_name):
    """Capability is an import-time platform fact, not current callable identity."""
    original = getattr(buildcache.os, function_name)

    def delegate(*args, **kwargs):
        return original(*args, **kwargs)

    monkeypatch.setattr(buildcache.os, function_name, delegate)
    buildcache._require_secure_fs_contract()


_KCMP_FILE = 0
_KCMP_SYSCALL_BY_MACHINE = {
    "aarch64": 272,
    "arm64": 272,
    "armv7l": 378,
    "i386": 349,
    "i686": 349,
    "ppc64": 354,
    "ppc64le": 354,
    "riscv64": 272,
    "s390x": 343,
    "x86_64": 312,
}


def _fd_kernel_identities(
        *, exclude: frozenset[int] = frozenset(),
) -> tuple[tuple[int, int, int, int, int], ...]:
    """Enumerate live fds, or explicitly reject an unusable procfs view."""
    try:
        names = os.listdir("/proc/self/fd")
    except OSError as exc:
        raise RuntimeError(
            "fd open-description guard unavailable: cannot enumerate "
            "/proc/self/fd"
        ) from exc
    identities = []
    for name in names:
        if not name.isdecimal():
            continue
        fd = int(name)
        if fd in exclude:
            continue
        try:
            info = os.fstat(fd)
        except OSError:
            continue
        identities.append((
            fd,
            info.st_dev,
            info.st_ino,
            stat.S_IFMT(info.st_mode),
            info.st_rdev,
        ))
    if not identities:
        raise RuntimeError(
            "fd open-description guard unavailable: /proc/self/fd exposed "
            "no live descriptors"
        )
    return tuple(sorted(identities))


def _same_open_description(left_fd: int, right_fd: int) -> bool:
    machine = platform.machine().lower()
    syscall_number = _KCMP_SYSCALL_BY_MACHINE.get(machine)
    if syscall_number is None:
        raise RuntimeError(
            "fd open-description guard unavailable: no kcmp syscall number "
            f"for architecture {machine!r}"
        )
    syscall = ctypes.CDLL(None, use_errno=True).syscall
    syscall.restype = ctypes.c_long
    ctypes.set_errno(0)
    result = syscall(
        syscall_number,
        os.getpid(),
        os.getpid(),
        _KCMP_FILE,
        left_fd,
        right_fd,
    )
    if result < 0:
        error_number = ctypes.get_errno()
        raise RuntimeError(
            "fd open-description guard unavailable: "
            f"kcmp(KCMP_FILE) failed with errno {error_number} "
            f"({os.strerror(error_number)})"
        )
    return result == 0


def _capture_fd_description_snapshot():
    """Keep one duplicate of every baseline open description for comparison."""
    kernel_identities = _fd_kernel_identities()
    keepers: dict[int, int] = {}
    try:
        for identity in kernel_identities:
            fd = identity[0]
            keepers[fd] = os.dup(fd)
        for fd, keeper_fd in keepers.items():
            if not _same_open_description(fd, keeper_fd):
                raise RuntimeError(
                    "fd open-description guard unavailable: dup did not retain "
                    f"open description for fd {fd}"
                )
    except BaseException:
        for keeper_fd in keepers.values():
            os.close(keeper_fd)
        raise
    before = tuple((*identity, 0) for identity in kernel_identities)
    return before, keepers


def _fd_identities_against_snapshot(before, keepers):
    """Assign generation 0 only to fds retaining their baseline description."""
    before_by_fd = {identity[0]: identity for identity in before}
    after = []
    for identity in _fd_kernel_identities(
            exclude=frozenset(keepers.values()),
    ):
        fd = identity[0]
        generation = 1
        if fd in before_by_fd and _same_open_description(fd, keepers[fd]):
            generation = 0
        after.append((*identity, generation))
    return tuple(after)


def _close_fd_description_snapshot(keepers) -> None:
    for keeper_fd in keepers.values():
        os.close(keeper_fd)


def _fd_identity_delta(before, after):
    before_set = set(map(tuple, before))
    after_set = set(map(tuple, after))
    return (
        tuple(sorted(before_set - after_set)),
        tuple(sorted(after_set - before_set)),
    )


def _same_inode_open_description_swap_probe() -> dict[str, object]:
    """Replace /dev/null at the same fd number and expose the generation change."""
    target_fd = os.open(os.devnull, os.O_RDONLY)
    before = ()
    keepers = {}
    replacement_fd = None
    try:
        before, keepers = _capture_fd_description_snapshot()
        os.close(target_fd)
        replacement_fd = os.open(os.devnull, os.O_RDONLY)
        if replacement_fd != target_fd:
            raise AssertionError(
                "same-inode swap probe did not reuse the closed fd number"
            )
        after = _fd_identities_against_snapshot(before, keepers)
        before_identity = next(row for row in before if row[0] == target_fd)
        after_identity = next(row for row in after if row[0] == target_fd)
        removed, added = _fd_identity_delta(before, after)
        return {
            "before_count": len(before),
            "after_count": len(after),
            "before_identity": before_identity,
            "after_identity": after_identity,
            "removed": removed,
            "added": added,
        }
    finally:
        if replacement_fd is not None:
            os.close(replacement_fd)
        elif not keepers:
            os.close(target_fd)
        _close_fd_description_snapshot(keepers)


def _exception_record(action):
    try:
        action()
    except BaseException as exc:
        return {"type": type(exc).__name__, "message": str(exc)}
    return None


def _proc_unavailable_guard_probe() -> dict[str, str] | None:
    """Prove that an unavailable procfs view is diagnosed instead of ignored."""
    patch = pytest.MonkeyPatch()
    original_listdir = os.listdir

    def deny_proc_fd(path):
        if os.fspath(path) == "/proc/self/fd":
            raise PermissionError("injected procfs denial")
        return original_listdir(path)

    try:
        patch.setattr(os, "listdir", deny_proc_fd)
        return _exception_record(_capture_fd_description_snapshot)
    finally:
        patch.undo()


def _clean_fd_identity_case(case: str, tmp_path: Path) -> dict[str, object]:
    """Run one fd-ownership fault in a fresh interpreter and report its full delta."""
    patch = pytest.MonkeyPatch()
    report: dict[str, object] = {}
    cleanup_fds: list[int] = []
    before = ()
    keepers = {}
    try:
        if case == "close-fds-best-effort":
            before, keepers = _capture_fd_description_snapshot()
            fds = [os.open(os.devnull, os.O_RDONLY) for _ in range(3)]
            cleanup_fds.extend(fds)
            real_close = buildcache.os.close
            calls = []

            def close_then_report_error(fd):
                real_close(fd)
                calls.append(fd)
                if len(calls) in {1, 2}:
                    raise OSError(f"injected-close-{len(calls)}")

            patch.setattr(buildcache.os, "close", close_then_report_error)
            error = _exception_record(
                lambda: buildcache._close_fds_best_effort(fds)
            )
            report.update(error=error, calls=calls, expected=fds)
        elif case == "copied-binary":
            before, keepers = _capture_fd_description_snapshot()
            source_fd = os.open(os.devnull, os.O_RDONLY)
            destination_fd = os.open(os.devnull, os.O_RDONLY)
            first_dir_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
            parent_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
            cleanup_fds.extend((
                source_fd, destination_fd, first_dir_fd, parent_fd,
            ))
            copied = buildcache._CopiedBinary(
                source_fd=source_fd,
                destination_fd=destination_fd,
                destination_parent_fd=parent_fd,
                destination_name="unused",
                directory_fds=[first_dir_fd, parent_fd],
                destination_path="unused",
            )
            expected = copied._owned_fds()
            real_close = buildcache.os.close
            calls = []

            def close_then_report_error(fd):
                real_close(fd)
                calls.append(fd)
                if len(calls) == 1:
                    raise OSError("injected-copied-close")

            patch.setattr(buildcache.os, "close", close_then_report_error)
            error = _exception_record(copied.close)
            report.update(error=error, calls=calls, expected=expected)
        elif case == "directory-traversal":
            before, keepers = _capture_fd_description_snapshot()
            real_close = buildcache.os.close
            injected = False

            def close_then_report_error(fd):
                nonlocal injected
                real_close(fd)
                if not injected:
                    injected = True
                    raise OSError("injected-traversal-close")

            patch.setattr(buildcache.os, "close", close_then_report_error)
            error = _exception_record(
                lambda: buildcache._open_or_create_directory_path(
                    str(tmp_path / "child")
                )
            )
            report.update(error=error, injected=injected)
        elif case.startswith("leaf:"):
            opener_name = case.partition(":")[2]
            leaf = tmp_path / "leaf"
            leaf.write_bytes(b"leaf")
            root_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
            cleanup_fds.append(root_fd)
            before, keepers = _capture_fd_description_snapshot()
            real_close = buildcache.os.close
            injected = False

            def close_then_report_error(fd):
                nonlocal injected
                real_close(fd)
                if not injected:
                    injected = True
                    raise OSError("injected-leaf-parent-close")

            patch.setattr(buildcache.os, "close", close_then_report_error)
            opener = getattr(buildcache, opener_name)
            error = _exception_record(
                lambda: opener(root_fd, "leaf", label="test leaf")
            )
            report.update(error=error, injected=injected)
        elif case == "v2-validation":
            _install_toolchain(tmp_path, patch)
            _fake_build_environment(patch, tmp_path)
            first = _call_copyout_api(tmp_path, "v2")
            bdir_identity = buildcache._stat_identity(os.stat(first.build_dir))
            before, keepers = _capture_fd_description_snapshot()
            real_open_regular = buildcache._open_regular_at
            real_close = buildcache.os.close
            binary_opened = False
            injected = False

            def observe_binary_open(root_fd, relpath, *, label):
                nonlocal binary_opened
                result = real_open_regular(root_fd, relpath, label=label)
                if label.startswith("v2 cached binary "):
                    binary_opened = True
                return result

            def close_then_report_error(fd):
                nonlocal injected
                is_bdir = buildcache._stat_identity(os.fstat(fd)) == bdir_identity
                real_close(fd)
                if binary_opened and is_bdir and not injected:
                    injected = True
                    raise OSError("injected-v2-bdir-close")

            patch.setattr(buildcache, "_open_regular_at", observe_binary_open)
            patch.setattr(buildcache.os, "close", close_then_report_error)
            error = _exception_record(
                lambda: _call_copyout_api(tmp_path, "v2")
            )
            report.update(
                error=error,
                binary_opened=binary_opened,
                injected=injected,
            )
        elif case == "mkdir-open-at":
            parent_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
            cleanup_fds.append(parent_fd)
            before, keepers = _capture_fd_description_snapshot()

            def fail_fchmod(fd, mode):
                raise OSError("injected-fchmod")

            patch.setattr(buildcache.os, "fchmod", fail_fchmod)
            error = _exception_record(
                lambda: buildcache._mkdir_open_at(
                    parent_fd, "half-created", label="test directory"
                )
            )
            report.update(
                error=error,
                entry_exists=(tmp_path / "half-created").exists(),
            )
        else:
            raise AssertionError(f"unknown clean fd identity case: {case}")
    finally:
        patch.undo()
    try:
        after = _fd_identities_against_snapshot(before, keepers)
        removed, added = _fd_identity_delta(before, after)
        report.update(
            before=before,
            after=after,
            removed=removed,
            added=added,
            same_inode_swap=_same_inode_open_description_swap_probe(),
            proc_unavailable=_proc_unavailable_guard_probe(),
        )
        return report
    finally:
        _close_fd_description_snapshot(keepers)
        for fd in cleanup_fds:
            try:
                os.close(fd)
            except OSError:
                pass


def _run_clean_fd_identity_case(case: str, tmp_path: Path) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json, sys; from pathlib import Path; "
                "from orchestrator.tests import test_buildcache_v2 as tests; "
                "print(json.dumps(tests._clean_fd_identity_case("
                "sys.argv[1], Path(sys.argv[2])), sort_keys=True))"
            ),
            case,
            str(tmp_path),
        ],
        cwd=_ORCH.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def _assert_full_fd_identity_guard(probe: dict[str, object]) -> None:
    """Accept equality and reject a same-fd, same-inode description swap."""
    before = probe["before"]
    after = probe["after"]
    assert before
    assert _fd_identity_delta(before, before) == ((), ())
    swap = probe["same_inode_swap"]
    assert swap["before_count"] == swap["after_count"]
    assert swap["before_identity"][:5] == swap["after_identity"][:5]
    assert swap["before_identity"][5] == 0
    assert swap["after_identity"][5] == 1
    assert swap["removed"] == [swap["before_identity"]]
    assert swap["added"] == [swap["after_identity"]]
    assert probe["proc_unavailable"] == {
        "type": "RuntimeError",
        "message": (
            "fd open-description guard unavailable: cannot enumerate "
            "/proc/self/fd"
        ),
    }
    assert _fd_identity_delta(before, after) == ((), ())


def test_close_fds_best_effort_closes_all_and_reraises_first_error(
        tmp_path, monkeypatch):
    """Returning to parent-process fd counts misses a count-preserving leaked identity."""
    probe = _run_clean_fd_identity_case("close-fds-best-effort", tmp_path)
    assert probe["error"] == {
        "type": "OSError",
        "message": "injected-close-1",
    }
    assert probe["calls"] == probe["expected"]
    _assert_full_fd_identity_guard(probe)
    assert probe["after"] == probe["before"]


def test_copied_binary_close_error_does_not_leak_later_fds(tmp_path, monkeypatch):
    """Returning to parent-process fd counts misses a count-preserving copied-fd leak."""
    probe = _run_clean_fd_identity_case("copied-binary", tmp_path)
    assert probe["error"] == {
        "type": "OSError",
        "message": "injected-copied-close",
    }
    assert probe["calls"] == probe["expected"]
    _assert_full_fd_identity_guard(probe)
    assert probe["after"] == probe["before"]


def test_directory_traversal_close_error_does_not_lose_child_fd(tmp_path, monkeypatch):
    """Returning to parent-process fd counts misses a count-preserving traversal leak."""
    probe = _run_clean_fd_identity_case("directory-traversal", tmp_path)
    assert probe["error"] == {
        "type": "OSError",
        "message": "injected-traversal-close",
    }
    assert probe["injected"] is True
    _assert_full_fd_identity_guard(probe)
    assert probe["after"] == probe["before"]


@pytest.mark.parametrize("opener_name", ["_open_regular_at", "_open_source_regular_at"])
def test_leaf_open_parent_close_error_does_not_lose_leaf_fd(
        tmp_path, monkeypatch, opener_name):
    """Returning to parent-process fd counts misses a count-preserving leaf-fd leak."""
    probe = _run_clean_fd_identity_case(f"leaf:{opener_name}", tmp_path)
    assert probe["error"] == {
        "type": "OSError",
        "message": "injected-leaf-parent-close",
    }
    assert probe["injected"] is True
    _assert_full_fd_identity_guard(probe)
    assert probe["after"] == probe["before"]


def test_v2_validation_parent_close_error_does_not_lose_result_fd(
        tmp_path, monkeypatch):
    """Returning to parent-process fd counts misses a count-preserving v2 result leak."""
    probe = _run_clean_fd_identity_case("v2-validation", tmp_path)
    assert probe["error"] == {
        "type": "OSError",
        "message": "injected-v2-bdir-close",
    }
    assert probe["binary_opened"] is True
    assert probe["injected"] is True
    _assert_full_fd_identity_guard(probe)
    assert probe["after"] == probe["before"]


def test_mkdir_open_at_removes_created_entry_when_post_mkdir_step_fails(
        tmp_path, monkeypatch):
    """Returning to parent-process fd counts misses a count-preserving mkdir-fd leak."""
    probe = _run_clean_fd_identity_case("mkdir-open-at", tmp_path)
    assert probe["error"]["type"] == "BuildCacheError"
    assert "injected-fchmod" in probe["error"]["message"]
    assert probe["entry_exists"] is False
    _assert_full_fd_identity_guard(probe)
    assert probe["after"] == probe["before"]


def test_mkdir_open_at_reports_original_and_rmdir_cleanup_failures(
        tmp_path, monkeypatch):
    """G-4: a leftover nonce candidate is surfaced with both failure causes."""
    parent_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)

    def fail_fchmod(fd, mode):
        raise OSError("injected-fchmod")

    def fail_rmdir(name, *, dir_fd):
        raise OSError("injected-rmdir")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(buildcache.os, "fchmod", fail_fchmod)
            patch.setattr(buildcache.os, "rmdir", fail_rmdir)
            with pytest.raises(buildcache.BuildCacheError) as raised:
                buildcache._mkdir_open_at(
                    parent_fd, "leftover", label="test directory",
                )
        message = str(raised.value)
        assert "injected-fchmod" in message
        assert "cleanup 失敗" in message
        assert "injected-rmdir" in message
        assert (tmp_path / "leftover").is_dir()
    finally:
        os.close(parent_fd)


@pytest.mark.parametrize("api", ["legacy", "v2"])
def test_gate_failure_discards_staging_and_clean_but_v2_keeps_claim(
        tmp_path, monkeypatch, api):
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    _install_staging_artifacts(
        monkeypatch, leaf_kind="regular", payload=b"gate-failure",
    )
    monkeypatch.setattr(
        buildcache, "_recheck_source_evidence",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("gate failure")),
    )
    with pytest.raises(RuntimeError, match="gate failure"):
        _call_copyout_api(tmp_path, api)
    assert not list((tmp_path / "cache").rglob("*staging-*"))
    assert not list((tmp_path / "cache").rglob(".publish-*"))
    if api == "v2":
        parent = next((tmp_path / "cache" / "contracts").iterdir())
        assert len(list(parent.glob("*.building"))) == 1
        assert not [path for path in parent.iterdir() if not path.name.endswith(".building")]
    else:
        assert not [path for path in (tmp_path / "cache").iterdir() if path.name.startswith("silo_")]


@pytest.mark.parametrize("api", ["legacy", "v2"])
def test_copyout_rejects_staging_entry_swap_while_retaining_held_fd(
        tmp_path, monkeypatch, api):
    """F-3: parent/name must still identify the held staging fd before copy-out."""
    if api == "v2":
        _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)

    def swap_staging_after_build(cmd, what, timeout_s=None, *, site=None, env=None):
        if what != "build":
            return
        staging = Path(cmd[cmd.index("--build") + 1])
        binary = staging / "cc" / "silo" / "ycsb_silo.exe"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b"held-staging-binary")
        detached = staging.with_name(staging.name + ".detached")
        staging.rename(detached)
        replacement = staging / "cc" / "silo" / "ycsb_silo.exe"
        replacement.parent.mkdir(parents=True)
        replacement.write_bytes(b"replacement-staging-binary")

    monkeypatch.setattr(buildcache, "_run", swap_staging_after_build)
    with pytest.raises(buildcache.BuildCacheError, match="staging copy source identity"):
        _call_copyout_api(tmp_path, api)
    assert not list((tmp_path / "cache").rglob(".publish-*"))
    assert not list((tmp_path / "cache").rglob("completion.json"))
    assert not list((tmp_path / "cache").rglob("admission.json"))


def test_clean_parent_creation_rejects_symlink_component(tmp_path):
    """M4: destination parents are mkdirat/openat components, never path-based makedirs."""
    staging = tmp_path / "staging"
    source = staging / "cc" / "silo" / "ycsb_silo.exe"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"binary")
    clean = tmp_path / "clean"
    clean.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (clean / "cc").symlink_to(outside, target_is_directory=True)
    clean_fd = os.open(clean, os.O_RDONLY | os.O_DIRECTORY)
    staging_fd = os.open(staging, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(buildcache.BuildCacheError, match="no-follow open"):
            buildcache._secure_copy_binary(
                staging_fd, clean_fd, "cc/silo/ycsb_silo.exe", str(clean),
            )
    finally:
        os.close(staging_fd)
        os.close(clean_fd)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize(
    "relpath", ["", "/absolute", "a//b", "a/./b", "a/../b", "a\\b", "a\x00b"],
)
def test_secure_copyout_rejects_invalid_relative_paths(relpath):
    """Helper contract only; this is not proof that a production call-site invokes it."""
    with pytest.raises(buildcache.BuildCacheError):
        buildcache._validated_relpath(relpath)


_CHILD = r"""
import hashlib, json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])
from orchestrator.campaign import buildcache
from orchestrator.campaign.build_admission import (
    GeneratorId, attest_generator_output, build_run_context, derive_build_admission,
)
from orchestrator.campaign.env_contract import CalibrationRef, ExecutionEnvironmentContract, IsolationPolicy
from orchestrator.campaign.model import Genome
from orchestrator.campaign.source_digest import SourceEvidence

root, sync, tools = map(Path, sys.argv[2:5])
os.environ["PATH"] = str(tools) + os.pathsep + os.environ.get("PATH", "")
buildcache._ccbench_dir = lambda: str(root / "ccbench")
buildcache._verify_ccbench_commit = lambda *a, **k: None
genome = Genome("silo", {"BACK_OFF": 1})
source_root = str((root / "ccbench").resolve())
evidence = SourceEvidence(
    schema_version="source-evidence/v1", source_root=source_root,
    ccbench_commit="a" * 40,
    genome_sha256=hashlib.sha256(genome.canonical().encode()).hexdigest(),
    src_token="stock", source_bytes_sha256=hashlib.sha256(b"stock-source").hexdigest(),
    tracked_clean=True, tracked_diff_sha256=hashlib.sha256(b"").hexdigest(),
    tracked_paths=(),
)
context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
generator_receipt = attest_generator_output(
    context, evidence, generator_input_sha256="1" * 64,
)
admission = derive_build_admission(
    context, evidence, generator_receipt=generator_receipt,
)
buildcache.source_digest = SimpleNamespace(
    STOCK="stock",
    assert_worktree_within_allowlist=lambda *a, **k: None,
    assert_trace_diff_matches_head=lambda *a, **k: None,
    resolve_evidence=lambda *a, **k: evidence,
)
buildcache._assert_no_trace_symbols = lambda *a, **k: None

real_write_fsynced_json = buildcache._write_fsynced_json
def write_receipt_without_secondary_exclusion(path, value):
    if str(path).endswith("owner.json"):
        Path(path).write_text(json.dumps(value))
    else:
        real_write_fsynced_json(path, value)
buildcache._write_fsynced_json = write_receipt_without_secondary_exclusion

real_mkdir = os.mkdir
def synchronized_mkdir(path, mode=0o777, *args, **kwargs):
    if str(path).endswith(".building"):
        (sync / ("claim-ready-" + str(os.getpid()))).write_text("ready")
        deadline = time.monotonic() + 15
        while not (sync / "claim-go").exists():
            if time.monotonic() > deadline:
                raise RuntimeError("claim barrier timeout")
            time.sleep(0.01)
    return real_mkdir(path, mode, *args, **kwargs)
buildcache.os.mkdir = synchronized_mkdir

def fake_run(cmd, what, timeout_s=None):
    if what == "configure":
        (sync / ("claimed-" + str(os.getpid()))).write_text("claimed")
        deadline = time.monotonic() + 15
        while not (sync / "finish").exists():
            if time.monotonic() > deadline:
                raise RuntimeError("finish barrier timeout")
            time.sleep(0.01)
    if what == "build":
        bdir = Path(cmd[cmd.index("--build") + 1])
        binary = bdir / "cc" / "silo" / "ycsb_silo.exe"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b"concurrent")
buildcache._run = fake_run

contract = ExecutionEnvironmentContract(
    env_tag="test-env-1", clocks_per_us=1801, numactl=(), attestation_mode="none",
    isolation_policy=IsolationPolicy(single_process=False, allow_resume=True),
    calibration_ref=CalibrationRef(path="output/env/test-1.json", sha256=f"{1:064x}"),
)
(sync / ("ready-" + str(os.getpid()))).write_text("ready")
deadline = time.monotonic() + 15
while not (sync / "go").exists():
    if time.monotonic() > deadline:
        raise SystemExit("go barrier timeout")
    time.sleep(0.01)
try:
    result = buildcache.build_v2(
        genome, admission=admission, build_context=context, source_evidence=evidence,
        contract=contract, ccbench_commit="a" * 40,
        trace=True, src_token="stock", cc="test-cc", cxx="test-cxx",
        cache_root=str(root / "cache"),
    )
    outcome = {"status": "ok", "cached": result.cached}
except Exception as exc:
    outcome = {"status": "error", "type": type(exc).__name__, "message": str(exc)}
(sync / ("result-" + str(os.getpid()))).write_text(json.dumps(outcome))
"""


def _wait_for_count(directory: Path, prefix: str, count: int, timeout: float = 15.0) -> list[Path]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = list(directory.glob(prefix + "*"))
        if len(found) >= count:
            return found
        time.sleep(0.01)
    raise AssertionError(f"barrier timeout: {prefix} expected={count}")


def test_v2_two_real_processes_only_one_claims(tmp_path):
    tools = tmp_path / "tools"
    tools.mkdir()
    _write_tool(tools / "test-cc", "cc version A")
    _write_tool(tools / "test-cxx", "cxx version A")
    _write_tool(tools / "cmake", "cmake version A")
    sync = tmp_path / "sync"
    sync.mkdir()
    argv = [
        sys.executable,
        "-c",
        textwrap.dedent(_CHILD),
        str(_ORCH.parent),
        str(tmp_path),
        str(sync),
        str(tools),
    ]
    children = [subprocess.Popen(argv) for _ in range(2)]
    try:
        _wait_for_count(sync, "ready-", 2)
        (sync / "go").write_text("go")
        _wait_for_count(sync, "claim-ready-", 2)
        (sync / "claim-go").write_text("claim-go")
        _wait_for_count(sync, "claimed-", 1)
        # 勝者を configure barrier で保持したまま、敗者が claim 競合を報告する。
        results = _wait_for_count(sync, "result-", 1)
        loser = json.loads(results[0].read_text())
        assert loser["status"] == "error"
        assert loser["type"] == "BuildCacheError"
        assert "claim" in loser["message"]
        (sync / "finish").write_text("finish")
        results = _wait_for_count(sync, "result-", 2)
        outcomes = [json.loads(path.read_text()) for path in results]
        assert sorted(item["status"] for item in outcomes) == ["error", "ok"]
        assert next(item for item in outcomes if item["status"] == "ok")["cached"] is False
    finally:
        (sync / "finish").write_text("finish")
        for child in children:
            child.wait(timeout=20)
        assert [child.returncode for child in children] == [0, 0]


def test_v2_contract_is_required(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    genome = Genome("silo", {})
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, str(tmp_path / "ccbench"),
    )
    kwargs = dict(
        admission=admission, build_context=context, source_evidence=evidence,
        ccbench_commit="a" * 40, trace=True, src_token="stock",
        cc="test-cc", cxx="test-cxx", cache_root=str(tmp_path / "cache"),
    )
    with pytest.raises(TypeError):
        buildcache.build_v2(genome, **kwargs)
    with pytest.raises((TypeError, buildcache.BuildCacheError)):
        buildcache.build_v2(genome, contract=None, **kwargs)


def _forged_unadmitted_coder():
    return object.__new__(BuildAdmission)


@pytest.mark.parametrize("api", ["legacy", "v2"])
def test_materializer_rejects_unadmitted_coder_before_identity_spy(
        monkeypatch, api):
    """F1/M1: materializer 自身の最初の gate だけを検査する。"""
    identity_calls = []
    monkeypatch.setattr(
        buildcache, "_verify_ccbench_commit",
        lambda *_args, **_kwargs: identity_calls.append("identity"),
    )
    genome = Genome("silo", {})
    context, evidence, _ = _admission_bundle(
        genome, "a" * 40, str(Path(buildcache._ccbench_dir()).resolve()),
    )
    with pytest.raises(BuildAdmissionError):
        if api == "legacy":
            buildcache.build(
                genome, "a" * 40, trace=True,
                admission=_forged_unadmitted_coder(),
                build_context=context, source_evidence=evidence,
            )
        else:
            buildcache.build_v2(
                genome, admission=_forged_unadmitted_coder(), contract=None,
                build_context=context, source_evidence=evidence,
                ccbench_commit="a" * 40, trace=True, src_token="stock",
                cc="cc", cxx="cxx", cache_root="/not-reached",
            )
    assert identity_calls == []


def test_legacy_materializer_admission_argument_is_mandatory_before_identity_spy(
        monkeypatch):
    identity_calls = []
    monkeypatch.setattr(
        buildcache, "_verify_ccbench_commit",
        lambda *_args, **_kwargs: identity_calls.append("identity"),
    )
    with pytest.raises(TypeError, match="admission"):
        buildcache.build(Genome("silo", {}), "a" * 40, trace=True)
    assert identity_calls == []


def test_descriptor_identity_binds_sealed_contract_without_changing_generic():
    genome = Genome("silo", {"BACK_OFF": 1})
    toolchain = {
        role: {"requested": role, "realpath": f"/tool/{role}", "version_first_line": "v1"}
        for role in ("cc", "cxx", "cmake")
    }
    args = (genome, "a" * 40, False, "stock", "cc", "cxx", toolchain)
    kwargs = dict(site="test", dependency_prefix=[], admission={"receipt": "fixture"})
    generic, generic_sha = buildcache._v2_identity(*args, **kwargs)
    assert set(generic) == {
        "genome_canonical", "ccbench_commit", "trace", "src_token", "cc", "cxx",
        "toolchain_manifest_sha256", "site", "dependency_prefix", "admission",
    }
    explicit_none = buildcache._v2_identity(
        *args, expected_materialization_sha256=None, **kwargs,
    )
    assert explicit_none == (generic, generic_sha)
    snapshot_args = dict(source_snapshot_sha256="1" * 64, **kwargs)
    old = buildcache._v2_identity(*args, **snapshot_args)
    sealed, sealed_sha = buildcache._v2_identity(
        *args, expected_materialization_sha256="1" * 64, **snapshot_args,
    )
    assert sealed["source_protection_contract"] == buildcache._SEALED_SOURCE_CONTRACT
    assert sealed["expected_materialization_sha256"] == "1" * 64
    assert sealed_sha != old[1]
    assert set(sealed) - set(old[0]) == {
        "source_protection_contract", "expected_materialization_sha256",
    }


def test_descriptor_impl_requires_session_before_any_build(tmp_path):
    # No replacement type or mock session: exercise the real private entry gate.
    with pytest.raises(buildcache.BuildCacheError, match="exact sealed session"):
        buildcache._build_v2_impl(
            Genome("silo", {"BACK_OFF": 1}),
            admission=None, build_context=None, source_evidence=None,
            contract=_contract(1), ccbench_commit="a" * 40, trace=False,
            cc="cc", cxx="cxx", cache_root=str(tmp_path),
            source_snapshot_sha256="1" * 64,
            expected_materialization_sha256="1" * 64,
        )


def _real_pending_publication(tmp_path):
    """Real directory descriptors, copy-out, claim and candidate; no OS stubs."""
    parent = tmp_path / "cache"
    parent.mkdir()
    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    staging_fd, _ = buildcache._mkdir_open_at(parent_fd, "staging", label="test staging")
    clean_fd, clean_identity = buildcache._mkdir_open_at(
        parent_fd, ".candidate", label="test candidate",
    )
    source = parent / "staging" / "binary"
    source.write_bytes(b"candidate binary A")
    source.chmod(0o755)
    clean = parent / ".candidate"
    copied = buildcache._secure_copy_binary(staging_fd, clean_fd, "binary", str(clean))
    os.close(staging_fd)
    claim = parent / ".entry.claim"
    buildcache._acquire_v2_claim(str(claim), str(parent), "test", parent_fd=parent_fd)
    binary = parent / "entry" / "binary"
    result = buildcache.BuildResult(
        Genome("silo", {"BACK_OFF": 1}), False, str(binary),
        hashlib.sha256(source.read_bytes()).hexdigest(), str(binary.parent), False,
    )
    return buildcache._PendingV2Publication(
        result, {}, parent_fd, clean_fd, clean_identity, copied,
        str(parent), str(clean), clean.name, "entry", str(claim),
    )


def test_pending_session_failure_discards_unpublished_candidate_and_keeps_claim(tmp_path):
    pending = _real_pending_publication(tmp_path)
    candidate = Path(pending.clean)
    final = Path(pending.result.build_dir)
    assert (candidate / "binary").read_bytes() == b"candidate binary A"
    assert not (candidate / "completion.json").exists()
    assert not final.exists()
    pending.close()  # build_v2's finally after session exit/issue failure
    assert not candidate.exists()
    assert not final.exists()
    parent_fd = os.open(pending.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # The next attempt cannot reuse the failed candidate. Existing claim
        # semantics require explicit recovery before a new build of this key.
        with pytest.raises(buildcache.BuildCacheError, match="claim"):
            buildcache._acquire_v2_claim(
                pending.claim, pending.parent, "second", parent_fd=parent_fd,
            )
    finally:
        os.close(parent_fd)


def test_pending_binary_drift_is_rejected_before_protection_record_or_rename(tmp_path):
    pending = _real_pending_publication(tmp_path)
    candidate_binary = Path(pending.clean) / "binary"
    try:
        # Control: the owner really can change this unsealed candidate.
        candidate_binary.chmod(0o755)
        candidate_binary.write_bytes(b"candidate binary B")
        assert candidate_binary.read_bytes() == b"candidate binary B"
        with pytest.raises(buildcache.BuildCacheError, match="pending binary changed"):
            pending.publish(None)
        assert not (Path(pending.clean) / "completion.json").exists()
        assert not Path(pending.result.build_dir).exists()
    finally:
        pending.close()


def test_pending_close_recovers_candidate_moved_to_another_parent(tmp_path):
    pending = _real_pending_publication(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    displaced = elsewhere / "displaced"
    clean = Path(pending.clean)
    try:
        clean.rename(displaced)
        clean.mkdir()
        # Control: without held-inode cleanup the same successful rename leaves
        # the original binary outside the pathname that close used to remove.
        assert (displaced / "binary").read_bytes() == b"candidate binary A"
        with pytest.raises(buildcache.BuildCacheError, match="identity"):
            pending.publish(None)
        pending.close()
        assert not displaced.exists()
        assert not Path(pending.result.build_dir).exists()
        assert Path(pending.claim).exists()
    finally:
        pending.close()


def test_pending_close_never_closes_a_reused_descriptor(tmp_path):
    pending = _real_pending_publication(tmp_path)
    old_fd = pending.copied.destination_fd
    pending.close()
    replacement = os.open(tmp_path / "unrelated", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        os.dup2(replacement, old_fd)
        identity = os.fstat(old_fd)
        pending.close()
        assert os.fstat(old_fd) == identity
        assert pending.clean_fd == pending.parent_fd == -1
        assert pending.copied._owned_fds() == [-1, -1]
    finally:
        os.close(old_fd)
        if replacement != old_fd:
            os.close(replacement)


def test_pending_return_interrupt_recovers_registered_fds_and_candidate(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_pending_return_interrupt_recovers_registered_fds_and_candidate_case"
    result = _run_sealed_case("orchestrator.tests.test_buildcache_v2", case, tmp_path)
    assert result == {"case": case, "completed": True}


def _pending_return_interrupt_recovers_registered_fds_and_candidate_case(tmp_path, monkeypatch):
    seen = []
    protected = False
    source, first = inspect.getsourcelines(buildcache._build_v2_impl)
    boundary = first + next(i for i, line in enumerate(source)
                            if line.strip() == "return pending")

    def interrupt(frame, event, arg):
        if (frame.f_code is buildcache._build_v2_impl.__code__
                and event == "line" and frame.f_lineno == boundary):
            assert frame.f_locals["transferred"] is True
            pending = frame.f_locals["pending"]
            fds = pending.copied._owned_fds() + [pending.clean_fd, pending.parent_fd]
            # The callee has relinquished these live descriptors, while its
            # caller has not received the result. Hit the reviewed signal gap.
            assert all(os.fstat(fd) for fd in fds)
            if not protected:
                # Mutation control: remove the real caller's ownership, without
                # replacing the session, close, fd operations, or signal seam.
                owners = frame.f_locals.get("pending_publications")
                if owners is not None:
                    owners.clear()
            seen.append((fds, pending))
            raise KeyboardInterrupt("pending return boundary")
        return interrupt

    for protected in (False, True):
        directory = tmp_path / ("protected" if protected else "control")
        directory.mkdir()
        previous = sys.gettrace()
        try:
            with monkeypatch.context() as patch:
                sys.settrace(interrupt)
                with pytest.raises(KeyboardInterrupt, match="pending return boundary"):
                    _v2_descriptor_runs_gate_inside_build_and_returns_both_digests_case(directory, patch)
        finally:
            sys.settrace(previous)
        assert len(seen) == (2 if protected else 1)
        fds, pending = seen[-1]
        try:
            for fd in fds:
                if protected:
                    with pytest.raises(OSError):
                        os.fstat(fd)
                else:
                    assert os.fstat(fd)  # The same interrupt really leaks without an owner.
            if protected:
                assert not Path(pending.clean).exists()
            assert not Path(pending.result.build_dir).exists()
            assert Path(pending.claim).exists()
        finally:
            pending.close()


def test_qualification_source_attack_starts_and_is_blocked(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_qualification_source_attack_starts_and_is_blocked_case"
    result = _run_sealed_case("orchestrator.tests.test_buildcache_v2", case, tmp_path)
    assert result == {"case": case, "completed": True}


def _qualification_source_attack_starts_and_is_blocked_case(tmp_path):
    from orchestrator.manual_probes.t1994_readonly_snapshot_qualification import ParentSourceSubstitution

    root = _publication_source(tmp_path)
    target = root / "input.cpp"
    target.write_bytes(b"A")
    observation = {}
    attack = ParentSourceSubstitution(root, observation)
    command = [sys.executable, "-I", "-B", "-c",
               "from pathlib import Path; import sys; print(Path(sys.argv[1]).read_text())",
               str(target)]
    try:
        with _publication_session(root) as session:
            try:
                attack.start()
                assert observation["status"] == "started"
                assert observation["source_renamed"] and observation["ancestor_renamed"]
                # Same reader and pathname outside the protected namespace see B.
                control = subprocess.run(
                    command, capture_output=True, text=True, check=True,
                    timeout=_SEALED_COMMAND_TIMEOUT_S,
                )
                assert "T1994_ORIGINAL_TREE_B" in control.stdout
                protected = session.run(
                    command, cwd="/", env=None, timeout_s=_SEALED_COMMAND_TIMEOUT_S,
                )
                assert protected.returncode == 0, protected.stderr
                attack.record_protection(protected.stdout.strip() == "A")
                assert observation["status"] == "blocked"
            finally:
                attack.restore()
        assert target.read_bytes() == b"A"
    finally:
        attack.restore()


@pytest.mark.parametrize("check", ["receipt", "archive", "no-post-oracle", "sources", "no-cxx", "order", "base-only"])
def test_qualification_stock_build_case_dependency_options(tmp_path, check):
    from orchestrator.manual_probes import t1994_readonly_snapshot_qualification as driver
    from orchestrator.campaign import (
        axis_trigger_gating, s8b_expected_materialization as em, s8b_floor_campaign as floor,
        s8b_materialization as mat, source_digest,
    )
    from orchestrator.tests.test_s1_direct_comparison import (
        _qualification_direct_checkout, _QualificationObserved,
    )

    base = tmp_path / "base"
    base.mkdir()
    source_dirs = {} if check == "base-only" else {
        name: str(base / (name + "-src"))
        for name in ("masstree", "mimalloc", "googletest")
    }
    flags = {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
             "NO_WAIT_OF_TICTOC": 1, "WAL": 0}
    freeze = {"holdouts": {"test": {"variant_binding": {
        "entries": {"stock_common": {"flags": flags}},
    }}}}
    toolchain = buildcache.observed_toolchain_manifest("gcc", "g++")
    cc, cxx = buildcache.toolchain_compilers_from_manifest(toolchain)
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    observed = {}
    with _qualification_direct_checkout(tmp_path) as (direct, pin):
        # Only this test's private checkout needs to reach real build admission.
        # Preserve the surrounding function/declaration and both markers; the
        # complete frozen block and adjacent epilogue must match the axis bytes.
        checkout = tmp_path / "external/ccbench"
        source = checkout / axis_trigger_gating.SOURCE_REL
        raw = source.read_bytes()
        # The borrowed checkout has Transaction::abort(), not the pinned
        # TxExecutor::abort(). Replace its whole declaration and function so
        # the canonical prefix, block, and epilogue form one closed source.
        old_class = b"class Transaction {\n"
        assert raw.count(old_class) == 1
        assert raw.endswith(b"};\n")
        source.write_bytes(
            raw[:raw.index(old_class)]
            + b"class TxExecutor { public: void abort(); };\n"
            + axis_trigger_gating.FROZEN_TEMPLATE_ABORT_HEAD_BYTES
            + axis_trigger_gating.FROZEN_TEMPLATE_PROLOGUE_BYTES
            + axis_trigger_gating.FROZEN_TEMPLATE_BLOCK_BYTES
            + axis_trigger_gating.FROZEN_TEMPLATE_EPILOGUE_BYTES
            + b"#endif\n}\n"
        )
        # The canonical head tests ADD_ANALYSIS. Supply the same TU macro as
        # CCBench so source_digest can classify this private checkout.
        options = checkout / "cmake" / "Options.cmake"
        cmake = options.read_text(encoding="utf-8")
        options.write_text(
            cmake.replace(
                "function(ccbench_universal_definitions out_var)\n",
                "set(CCBENCH_ADD_ANALYSIS 0 CACHE STRING \"extra per-tx analysis counters\")\n"
                "function(ccbench_universal_definitions out_var)\n",
            ).replace(
                "  set(${out_var}\n",
                "  set(${out_var}\n    ADD_ANALYSIS=${CCBENCH_ADD_ANALYSIS}\n",
            ),
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(checkout), "add",
                        axis_trigger_gating.SOURCE_REL, "cmake/Options.cmake"],
                       capture_output=True, text=True, check=True)
        subprocess.run(["git", "-C", str(checkout), "commit", "-q", "-m",
                        "canonical qualification trigger material"],
                       capture_output=True, text=True, check=True)
        pin = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        # Real binding type/method; values are observations of temporary bytes.
        config = base / "config.h"
        archive = base / "libmasstree.a"
        config.write_bytes(b"qualification config\n")
        archive.write_bytes(b"qualification archive\n")
        binding = floor._FloorOracleDependencyBinding(
            source_root=base, expected_head=pin, observed_head=pin,
            config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
            archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            archive_nondebug_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            expected_toolchain_manifest_sha256=floor._floor_toolchain_manifest_sha256(toolchain),
            source_st_dev=base.stat().st_dev, source_st_ino=base.stat().st_ino,
        )

        def trace(frame, event, value):
            if event == "call" and frame.f_code is direct.prepare_cell.__wrapped__.__code__:
                observed["configure"] = frame.f_locals["condition_configure_args"]
            if (event == "line" and frame.f_code is driver.build_case.__code__
                    and "original_run" in frame.f_locals):
                observed["build"] = dict(frame.f_locals["build_options"])
                raise _QualificationObserved
            return trace

        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            with pytest.raises(_QualificationObserved):
                driver.build_case(
                    "stock_common", "aba", "stock_common:aba", {}, {},
                    SimpleNamespace(holdout="test"), freeze, pin, toolchain, cc, cxx,
                    context, None, base, source_dirs, base / "shared", binding,
                    tmp_path, None, buildcache, em, mat, floor, direct, source_digest,
                    em.SealedBuildSession, em.SealedSnapshotProtectionKind,
                    derive_build_admission, ReviewId,
                )
        finally:
            sys.settrace(previous)

    options, injected = observed["build"], observed["configure"]
    if check == "receipt":
        assert options["fetchcontent_dependency_receipt"] == binding.cache_receipt()
    elif check == "archive":
        assert options["fetchcontent_archive_sha256"] == binding.archive_sha256
    elif check == "no-post-oracle":
        # Retain the old M5 gate; new M5 moves only the compiler-input root
        # into common build_options, so the second assert is its sole failure.
        assert "post_oracle_dependency_binding" not in options
        assert "current_compiler_input_masstree_root" not in options
    elif check == "sources":
        # M6 removes MASSTREE from the returned defines, not source_dirs.
        # The order case is a redundant gate, not independent mutation evidence.
        for name, path in source_dirs.items():
            assert f"-DFETCHCONTENT_SOURCE_DIR_{name.upper()}={path}" in injected
    elif check == "no-cxx":
        # M7 adds one CXX_FLAGS argument; capture's duplicate gate needs > 1.
        # Order/base-only also reject it, but are redundant mutation gates.
        assert not any(arg.startswith(("-DCMAKE_CXX_FLAGS", "-DCMAKE_CXX_COMPILER"))
                       for arg in injected)
    else:
        expected = (
            "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
            "-DCMAKE_C_COMPILER=" + toolchain["cc"]["realpath"],
            "-DFETCHCONTENT_BASE_DIR=" + str(base),
        )
        if check == "order":
            expected += tuple(f"-DFETCHCONTENT_SOURCE_DIR_{name.upper()}={path}"
                              for name, path in source_dirs.items())
        assert injected == expected


@pytest.mark.parametrize("write_error,chmod_error,accepted", [
    pytest.param(errno.EROFS, errno.EROFS, True, id="erofs"),
    pytest.param(errno.EACCES, errno.EROFS, True, id="dac-before-ro"),
    pytest.param(0, errno.EROFS, False, id="M8-write-succeeded"),
    pytest.param(errno.EACCES, 0, False, id="M9-chmod-succeeded"),
    pytest.param(errno.EACCES, errno.EACCES, False, id="chmod-dac-only"),
    pytest.param(errno.EPERM, errno.EROFS, False, id="unapproved-write-errno"),
])
def test_qualification_seal_require_errno_conjunction(write_error, chmod_error, accepted):
    """Execute the driver's complete require, without duplicating its predicate.

    This is a predicate test, not a mount qualification. Synthetic observations
    vary one conjunct at a time; the production require itself is unchanged.
    """
    import ast
    import inspect
    from types import SimpleNamespace
    from orchestrator.manual_probes import t1994_readonly_snapshot_qualification as driver

    tree = ast.parse(inspect.getsource(driver.build_case))
    calls = [node for node in ast.walk(tree)
             if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "require"
             and len(node.args) >= 3
             and isinstance(node.args[1], ast.BinOp)
             and isinstance(node.args[1].right, ast.Constant)
             and node.args[1].right.value == ":seal"]
    assert len(calls) == 1
    code = compile(ast.Expression(calls[0]), driver.__file__, "eval")
    inventory = {"files": 1}
    observation = {
        "chmod_errno": chmod_error, "write_errno": write_error,
        "read_unchanged": True, "git_absent": True, "inventory": inventory,
        "source_mounts": ["1 0 0:1 / /source ro,relatime - tmpfs tmpfs rw"],
    }
    checks = {}
    inputs = dict(vars(driver), checks=checks, label="test",
                  observed=SimpleNamespace(returncode=0), observation=observation,
                  inventory=inventory)
    if accepted:
        eval(code, inputs)
    else:
        with pytest.raises(RuntimeError, match="^test:seal$"):
            eval(code, inputs)
    assert checks["test:seal"]["result"] is accepted


def test_qualification_never_credits_an_attack_that_could_not_start(tmp_path):
    from orchestrator.manual_probes.t1994_readonly_snapshot_qualification import ParentSourceSubstitution

    root = _publication_source(tmp_path)
    (root / "input.cpp").write_bytes(b"A")
    observation = {}
    attack = ParentSourceSubstitution(root, observation)
    # Real rename obstruction, with the same attack code (no syscall stub).
    attack.renamed_source.mkdir()
    (attack.renamed_source / "occupied").touch()
    try:
        with pytest.raises(OSError):
            attack.start()
        assert observation["status"] == "could-not-start"
        with pytest.raises(RuntimeError, match="cannot credit protection"):
            attack.record_protection(True)
    finally:
        attack.restore()


def test_run_without_session_executes_real_command_even_when_named_build(tmp_path):
    marker = tmp_path / "ran"
    buildcache._run(
        [os.sys.executable, "-c",
         "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran')",
         str(marker)],
        "build", site=buildcache.site_policy.OTHER,
    )
    assert marker.read_text() == "ran"


def _publication_source(tmp_path):
    parent = tmp_path / "source-parent"
    parent.mkdir()
    root = parent / "source"
    root.mkdir()
    (root / "input").write_bytes(b"A")
    return root


@contextlib.contextmanager
def _publication_session(root, *, shared_directories=()):
    """Exercise S1's real lifecycle on fixed input, without replaying CCBench.

    Only the admitted input is a fixture. Mounts, command transport, cleanup,
    waitpid, root checks, permission restoration and issuance are not replaced.
    No private capability seal or issuance registry is accessed.
    """
    materialization = buildcache.s8b_expected_materialization
    digest = materialization.snapshot_tree_digest(root)
    session = materialization.SealedBuildSession(
        materialization.AdmittedBuildSnapshot(
            source_snapshot_sha256=digest,
            expected_materialization_sha256=digest,
            source_evidence=_source_evidence(
                Genome("silo", {"BACK_OFF": 1}), "a" * 40, str(root),
            ),
        ),
    )
    try:
        session._start(root, shared_directories=shared_directories)
        yield session
    finally:
        session._finish()


def _publication_capability(session, pending, *, cached=False):
    kinds = buildcache.s8b_expected_materialization.SealedSnapshotProtectionKind
    return session.issue(
        kinds.SEALED_CACHE_HIT if cached else kinds.SEALED_BUILD,
        binary_sha256=pending.result.bin_sha256,
        compiler_input_manifest_sha256=hashlib.sha256(b"fixture manifest").hexdigest(),
    )


def test_real_session_publish_then_hit_issues_distinct_capabilities(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_real_session_publish_then_hit_issues_distinct_capabilities_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _real_session_publish_then_hit_issues_distinct_capabilities_case(tmp_path):
    root = _publication_source(tmp_path)
    pending = _real_pending_publication(tmp_path)
    fds = pending.copied._owned_fds() + [pending.clean_fd, pending.parent_fd]
    try:
        with _publication_session(root, shared_directories=(Path(pending.parent),)) as fresh:
            # The production command seam executes in the actual sealed child.
            buildcache._run(
                [sys.executable, "-I", "-B", "-c",
                 "from pathlib import Path; import sys; "
                 "assert Path(sys.argv[1]).read_bytes() == b'A'", str(root / "input")],
                "configure", site=buildcache.site_policy.OTHER,
                sealed_session=fresh, timeout_s=_SEALED_COMMAND_TIMEOUT_S,
            )
            # Produce the actual pending bytes in this session. A successful
            # configure/read command alone cannot justify SEALED_BUILD (M-E).
            output = Path(pending.parent) / "staging" / "fresh-binary"
            buildcache._run(
                [sys.executable, "-I", "-B", "-c",
                 "from pathlib import Path; import sys; "
                 "output = Path(sys.argv[2]); "
                 "output.write_bytes(b'candidate binary ' + Path(sys.argv[1]).read_bytes()); "
                 "output.chmod(0o500)",
                 str(root / "input"), str(output)],
                "build", site=buildcache.site_policy.OTHER, sealed_session=fresh,
                timeout_s=_SEALED_COMMAND_TIMEOUT_S,
                build_output=str(output),
            )
            assert output.read_bytes() == (Path(pending.clean) / "binary").read_bytes()
            assert not Path(pending.result.build_dir).exists()
            assert not (Path(pending.clean) / "completion.json").exists()
            with pytest.raises(
                    buildcache.s8b_expected_materialization.ExpectedMaterializationError,
                    match="not complete"):
                _publication_capability(fresh, pending)
        capability = _publication_capability(fresh, pending)
        result = pending.publish(capability)
        assert Path(result.binary).read_bytes() == b"candidate binary A"
        assert not Path(pending.claim).exists()
        completion = json.loads((Path(result.build_dir) / "completion.json").read_text())
        assert completion["source_protection"]["kind"] == "sealed-build"
        with _publication_session(root) as hit:
            buildcache._assert_source_snapshot_sha256(root, hit.source_snapshot_sha256)
        hit_capability = _publication_capability(hit, pending, cached=True)
        assert hit_capability.kind.value == "sealed-cache-hit"
        assert hit_capability.binary_sha256 == capability.binary_sha256
        assert hit_capability is not capability
        with pytest.raises(buildcache.s8b_expected_materialization.ExpectedMaterializationError):
            _publication_capability(hit, pending)
    finally:
        pending.close()
    for fd in fds:
        with pytest.raises(OSError):
            os.fstat(fd)


@pytest.mark.parametrize("attack", ["persistent-drift"])
def test_real_session_parent_drift_or_exit_failure_never_publishes(tmp_path, attack):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_real_session_parent_drift_or_exit_failure_never_publishes_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path, attack=attack,
    )
    assert result == {"case": case, "completed": True}


def _real_session_parent_drift_or_exit_failure_never_publishes_case(tmp_path, attack):
    root = _publication_source(tmp_path)
    pending = _real_pending_publication(tmp_path)
    fds = pending.copied._owned_fds() + [pending.clean_fd, pending.parent_fd]
    error = (buildcache.BuildCacheError if attack == "persistent-drift"
             else buildcache.s8b_expected_materialization.ExpectedMaterializationError)
    reason = "source snapshot tree digest" if attack == "persistent-drift" else "root-identity-after-build"
    try:
        with pytest.raises(error, match=reason):
            with _publication_session(root) as session:
                # Control: the same owner really can replace the original tree.
                if attack == "root-replacement":
                    root.parent.chmod(0o700)
                    root.rename(root.with_name("displaced"))
                    root.mkdir()
                    (root / "input").write_bytes(b"B")
                else:
                    (root / "input").chmod(0o600)
                    (root / "input").write_bytes(b"B")
                assert (root / "input").read_bytes() == b"B"
                buildcache._run(
                    [sys.executable, "-I", "-B", "-c",
                     "from pathlib import Path; import sys; "
                     "assert Path(sys.argv[1]).read_bytes() == b'A'", str(root / "input")],
                    "build", site=buildcache.site_policy.OTHER, sealed_session=session,
                    timeout_s=_SEALED_COMMAND_TIMEOUT_S,
                )
                if attack == "persistent-drift":
                    # The real parent gate reads B even though the child reads A.
                    buildcache._assert_source_snapshot_sha256(root, session.source_snapshot_sha256)
            pending.publish(_publication_capability(session, pending))
    finally:
        pending.close()
    assert not Path(pending.clean).exists()
    assert not Path(pending.result.build_dir).exists()
    for fd in fds:
        with pytest.raises(OSError):
            os.fstat(fd)
    # A second attempt is blocked by the real stale-claim gate, not a hit on A.
    parent_fd = os.open(pending.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(buildcache.BuildCacheError, match="claim"):
            buildcache._acquire_v2_claim(pending.claim, pending.parent, "retry", parent_fd=parent_fd)
    finally:
        os.close(parent_fd)


@pytest.mark.parametrize("entry", ["binary", "candidate", "destination"])
def test_pending_final_rename_rechecks_real_entries(tmp_path, entry):
    _pending_final_rename_rechecks_real_entries_case(tmp_path, entry)


def _pending_final_rename_rechecks_real_entries_case(tmp_path, entry):
    pending = _real_pending_publication(tmp_path)
    try:
        # Real-fd positive control before attacking the same entries. Issuance
        # is covered by the real-session integration case, not repeated here.
        pending._verify_publish_entries()
        clean = Path(pending.clean)
        if entry == "binary":
            (clean / "binary").unlink()
            (clean / "binary").write_bytes(b"replacement")
        elif entry == "candidate":
            clean.rename(clean.with_name("displaced-candidate"))
            clean.mkdir()
            assert (clean.with_name("displaced-candidate") / "binary").read_bytes() == b"candidate binary A"
        else:
            Path(pending.result.build_dir).mkdir()
        with pytest.raises(buildcache.BuildCacheError):
            pending.publish(None)  # Rejected before capability consumption.
        assert not (Path(pending.result.build_dir) / "binary").exists()
    finally:
        pending.close()
    assert not clean.with_name("displaced-candidate").exists()


def test_sealed_child_obeys_parent_d1755_protection_without_freezing_base(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_child_obeys_parent_d1755_protection_without_freezing_base_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_child_obeys_parent_d1755_protection_without_freezing_base_case(tmp_path):
    root = _publication_source(tmp_path)
    base = tmp_path / "base"
    dependency = base / "masstree-src"
    dependency.mkdir(parents=True)
    target = dependency / "input"
    target.write_bytes(b"A")
    command = [sys.executable, "-I", "-B", "-c", textwrap.dedent("""
        import errno, sys
        from pathlib import Path
        target, marker = map(Path, sys.argv[1:3])
        denied = sys.argv[3] == 'denied'
        try:
            target.write_bytes(b'B')
        except OSError as exc:
            assert denied and exc.errno == errno.EACCES
        else:
            assert not denied
        marker.write_bytes(b'writable base')
    """), str(target), str(base / "new-entry")]
    with _publication_session(root, shared_directories=(base,)) as session:
        # Same child, same attempted write: succeeds without the D1755 context.
        buildcache._run(command + ["allowed"], "build",
                        site=buildcache.site_policy.OTHER, sealed_session=session,
                        timeout_s=_SEALED_COMMAND_TIMEOUT_S)
        assert target.read_bytes() == b"B"
        target.write_bytes(b"A")
        (base / "new-entry").unlink()
        base_mode = stat.S_IMODE(base.stat().st_mode)
        with sort_swo_dependency_material.protect_post_oracle_dependency_material(
                dependency, fetchcontent_base_dir=base):
            buildcache._run(command + ["denied"], "build",
                            site=buildcache.site_policy.OTHER, sealed_session=session,
                            timeout_s=_SEALED_COMMAND_TIMEOUT_S)
            assert target.read_bytes() == b"A"
            assert (base / "new-entry").read_bytes() == b"writable base"
            assert stat.S_IMODE(base.stat().st_mode) == base_mode
        target.write_bytes(b"restored")


def test_descriptorless_build_never_enters_sealed_session(tmp_path, monkeypatch):
    def forbidden(**kwargs):
        pytest.fail("descriptor-less build entered sealed session")

    monkeypatch.setattr(buildcache.s8b_expected_materialization,
                        "sealed_build_session", forbidden, raising=False)
    test_v2_without_source_snapshot_preserves_legacy_completion_and_skips_manifest(
        tmp_path, monkeypatch,
    )


def test_descriptor_build_result_carries_real_fresh_and_hit_capabilities(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_descriptor_build_result_carries_real_fresh_and_hit_capabilities_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def test_descriptor_build_prepares_missing_cache_root(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_descriptor_build_prepares_missing_cache_root_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def test_descriptor_build_from_hidden_sibling_cwd(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_descriptor_build_from_hidden_sibling_cwd_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _descriptor_build_from_hidden_sibling_cwd_case(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "cwd-input").write_bytes(b"parent cwd")
    monkeypatch.chdir(project)
    source = tmp_path / "ccbench"
    assert project.parts[1] == source.parts[1]
    assert project not in source.parents and source not in project.parents
    real_run = buildcache._run
    setup = _fake_build_environment
    calls = []

    def setup_with_real_cwd_check(patch, directory, *args, **kwargs):
        setup(patch, directory, *args, **kwargs)
        synthetic_build = buildcache._run

        def run(cmd, what, timeout_s=None, **options):
            # The existing synthetic compiler avoids CMake cost. This probe
            # goes through the production cwd/transport before that compiler;
            # neither _run nor SealedBuildSession.run is stubbed for the probe.
            session = options["sealed_session"]
            program = (
                "from pathlib import Path; import subprocess, sys; "
                "assert Path.cwd() == Path(sys.argv[1]); "
                "assert Path('cwd-input').read_bytes() == b'parent cwd'; "
                "subprocess.run([sys.argv[2], '--version'], check=True)"
            )
            real_run(
                [sys.executable, "-I", "-B", "-c", program,
                 str(project), cmd[0]], what,
                timeout_s=_SEALED_COMMAND_TIMEOUT_S,
                site=buildcache.site_policy.OTHER, sealed_session=session,
            )
            calls.append(what)
            return synthetic_build(cmd, what, timeout_s, **options)

        patch.setattr(buildcache, "_run", run)

    monkeypatch.setattr(sys.modules[__name__], "_fake_build_environment",
                        setup_with_real_cwd_check)
    # Keeps all existing binary, cache-hit, digest and lifecycle assertions.
    _v2_descriptor_runs_gate_inside_build_and_returns_both_digests_case(
        tmp_path, monkeypatch,
    )
    assert calls == ["configure", "build"]
    completions = list((tmp_path / "cache").rglob("completion.json"))
    assert len(completions) == 1


def test_descriptor_named_input_branches_visible_in_real_child(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_descriptor_named_input_branches_visible_in_real_child_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _descriptor_named_input_branches_visible_in_real_child_case(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", os.defpath)
    root = _publication_source(tmp_path)
    base, cache, prefix = (tmp_path / name for name in ("base", "cache", "prefix"))
    for path in (base, cache, prefix):
        path.mkdir()
    source_dirs = {}
    for name in ("masstree", "mimalloc", "googletest"):
        path = tmp_path / (name + "-override")
        path.mkdir()
        (path / "input").write_text(name)
        source_dirs[name] = str(path)
    (prefix / "input").write_text("prefix")
    tools = tmp_path / "real-tools"
    tools.mkdir()
    compiler = tools / "compiler"
    _write_tool(compiler, "realpath compiler")
    link = cache / "compiler-link"
    link.symlink_to(compiler)
    # A spine cwd needs no sharing; a source input must stay the sealed copy.
    monkeypatch.chdir(root.parent)
    shared = buildcache._descriptor_shared_directories(
        root, cache, base, cc=str(link), cxx=str(link),
        source_dirs={**source_dirs, "snapshot": str(root)},
        dependency_prefix=str(prefix),
    )
    assert set(map(Path, shared)) == {cache, base, prefix, tools,
                                    *(Path(p) for p in source_dirs.values())}
    assert all(root != Path(p) and root not in Path(p).parents
               and Path(p) not in root.parents for p in shared)
    program = textwrap.dedent("""
        import subprocess, sys
        from pathlib import Path
        compiler, base, cache, prefix, *dependencies = map(Path, sys.argv[1:])
        result = subprocess.run([str(compiler)], capture_output=True, text=True, check=True)
        assert result.stdout.strip() == 'realpath compiler'
        assert (prefix / 'input').read_text() == 'prefix'
        for path, name in zip(dependencies, ('masstree', 'mimalloc', 'googletest')):
            assert (path / 'input').read_text() == name
        (base / 'new-entry').write_bytes(b'writable base')
        (cache / 'binary').write_bytes(b'built from named inputs')
    """)
    with _publication_session(root, shared_directories=shared) as session:
        buildcache._run(
            [sys.executable, "-I", "-B", "-c", program, str(compiler),
             str(base), str(cache), str(prefix), *source_dirs.values()],
            "build", site=buildcache.site_policy.OTHER, sealed_session=session,
            timeout_s=_SEALED_COMMAND_TIMEOUT_S,
            build_output=str(cache / "binary"),
        )
    assert (cache / "binary").read_bytes() == b"built from named inputs"
    assert (base / "new-entry").read_bytes() == b"writable base"


def _descriptor_build_prepares_missing_cache_root_case(tmp_path, monkeypatch):
    assert not (tmp_path / "cache").exists()
    _v2_descriptor_runs_gate_inside_build_and_returns_both_digests_case(tmp_path, monkeypatch)


def test_configure_only_session_cannot_issue_sealed_build(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_configure_only_session_cannot_issue_sealed_build_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _configure_only_session_cannot_issue_sealed_build_case(tmp_path):
    root = _publication_source(tmp_path)
    binary = tmp_path / "preexisting-binary"
    binary.write_bytes(b"not built in this session")
    with _publication_session(root) as session:
        buildcache._run(
            [sys.executable, "-I", "-B", "-c", "pass"],
            "configure", site=buildcache.site_policy.OTHER, sealed_session=session,
            timeout_s=_SEALED_COMMAND_TIMEOUT_S,
        )
    with pytest.raises(
            buildcache.s8b_expected_materialization.ExpectedMaterializationError,
            match="kind differs from execution"):
        session.issue(
            buildcache.s8b_expected_materialization.SealedSnapshotProtectionKind.SEALED_BUILD,
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            compiler_input_manifest_sha256=hashlib.sha256(b"fixture manifest").hexdigest(),
        )


def _descriptor_build_result_carries_real_fresh_and_hit_capabilities_case(tmp_path, monkeypatch):
    # Reuse the existing admission/compiler fixture and all its expectations.
    # The sealed context, run/issue, cache validator and publication stay real.
    original = buildcache.build_v2
    results = []

    def observe(*args, **kwargs):
        result = original(*args, **kwargs)
        results.append(result)
        return result

    monkeypatch.setattr(buildcache, "build_v2", observe)
    _v2_descriptor_runs_gate_inside_build_and_returns_both_digests_case(tmp_path, monkeypatch)
    fresh, hit = results
    materialization = buildcache.s8b_expected_materialization
    assert fresh.source_protection.kind is materialization.SealedSnapshotProtectionKind.SEALED_BUILD
    assert hit.source_protection.kind is materialization.SealedSnapshotProtectionKind.SEALED_CACHE_HIT
    for result in results:
        assert materialization.validate_sealed_snapshot_capability(
            result.source_protection,
            source_snapshot_sha256=result.source_snapshot_sha256,
            expected_materialization_sha256=result.expected_materialization_sha256,
            binary_sha256=result.bin_sha256,
            compiler_input_manifest_sha256=result.compiler_input_manifest_sha256,
        ) is result.source_protection


@pytest.mark.parametrize("attack", ["root-replacement"])
def test_descriptor_build_failure_cannot_become_second_build_hit(tmp_path, attack):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_descriptor_build_failure_cannot_become_second_build_hit_case"
    result = _run_sealed_case(
        "orchestrator.tests.test_buildcache_v2", case, tmp_path, attack=attack,
    )
    assert result == {"case": case, "completed": True}


def _descriptor_build_failure_cannot_become_second_build_hit_case(tmp_path, monkeypatch, attack):
    # These observers inject a filesystem attack at an actual production seam;
    # they call the original operation and do not replace any protection gate.
    original_build = buildcache.build_v2
    original_result = buildcache._v2_result
    original_collect = buildcache._collect_compiler_inputs
    request = []
    attacked = []

    def observe_build(*args, **kwargs):
        request.append((args, kwargs))
        return original_build(*args, **kwargs)

    def replace_root(*args, **kwargs):
        result = original_result(*args, **kwargs)
        root = Path(result.ccbench_root)
        root.parent.chmod(0o700)
        displaced = root.with_name("displaced-source")
        root.rename(displaced)
        shutil.copytree(displaced, root)
        attacked.append(displaced)
        assert root.stat().st_ino != displaced.stat().st_ino
        return result

    def leave_drift(*args, **kwargs):
        result = original_collect(*args, **kwargs)
        root = tmp_path / "ccbench"
        root.chmod(0o700)
        extra = root / "persistent-B"
        extra.write_bytes(b"B")
        assert extra.read_bytes() == b"B"
        attacked.append(extra)
        return result

    monkeypatch.setattr(buildcache, "build_v2", observe_build)
    if attack == "root-replacement":
        monkeypatch.setattr(buildcache, "_v2_result", replace_root)
        reason = "root-identity-after-build"
    else:
        monkeypatch.setattr(buildcache, "_collect_compiler_inputs", leave_drift)
        reason = "source snapshot tree digest"
    with pytest.raises(buildcache.BuildCacheError, match=reason):
        _v2_descriptor_runs_gate_inside_build_and_returns_both_digests_case(tmp_path, monkeypatch)
    assert len(attacked) == 1
    cache = tmp_path / "cache"
    assert not list(cache.rglob("completion.json"))
    assert not list(cache.rglob("ycsb_silo.exe"))
    assert not list(cache.rglob(".publish-*"))
    assert not list(cache.rglob(".staging-*"))
    assert len(list(cache.rglob("*.building"))) == 1
    monkeypatch.setattr(buildcache, "_v2_result", original_result)
    monkeypatch.setattr(buildcache, "_collect_compiler_inputs", original_collect)
    root = tmp_path / "ccbench"
    if attack == "root-replacement":
        root.parent.chmod(0o700)
        # copytree preserved the protected modes on the attacker's copy.
        # Session restoration follows held fds to displaced-source, not this
        # replacement inode. This fixture has only compiler-input.hh inside;
        # unlinking it needs write permission on the copied root directory.
        assert stat.S_IMODE(attacked[0].stat().st_mode) & stat.S_IWUSR
        copied_mode = stat.S_IMODE(root.stat().st_mode)
        assert not copied_mode & 0o222
        root.chmod(copied_mode | stat.S_IWUSR)
        buildcache._discard_build_dir(str(root))
        attacked[0].rename(root)
    else:
        root.chmod(0o700)
        attacked[0].unlink()
    args, kwargs = request[0]
    # Restore A to make the second request identical. It must reach the claim
    # gate, so a source mismatch cannot hide accidental publication of A.
    with pytest.raises(buildcache.BuildCacheError, match="claim"):
        original_build(*args, **kwargs)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
