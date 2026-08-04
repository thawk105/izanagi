# -*- coding: utf-8 -*-
"""buildcache v2 の contract namespace / 完成 manifest / 並行 claim 回帰。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from unittest import mock
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH))

from campaign import buildcache, p3_s4_loop, source_digest  # noqa: E402
from campaign.build_admission import (  # noqa: E402
    BuildAdmission,
    BuildAdmissionError,
    GeneratorId,
    ReviewId,
    add_coder_build_authority_argument,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
    issue_trigger_gate_receipt,
    legacy_trigger_admission_projection,
    verify_review_receipt,
)
from campaign.env_contract import (  # noqa: E402
    CalibrationRef,
    ExecutionEnvironmentContract,
    IsolationPolicy,
)
from campaign.model import Genome  # noqa: E402
from campaign.pin import CURRENT_PIN  # noqa: E402
from campaign.source_digest import (  # noqa: E402
    SOURCE_EVIDENCE_SCHEMA_V2,
    SourceEvidence,
    TriggerGateSourceError,
)
from campaign.trigger_gate_language import (  # noqa: E402
    TRIGGER_GATE_LANGUAGE,
    GateLanguageRejectCode,
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


_TRIGGER_IMPLEMENTATION = b"  izanagi_gate_pass = true;"


def _write_trigger_source(root: Path, implementation: bytes = _TRIGGER_IMPLEMENTATION) -> None:
    path = root / source_digest.TRIGGER_GATE_SOURCE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
        b"#if BACKOFF_TRIGGER_GATING\n"
        + implementation
        + b"\n#else\n  Backoff::backoff(FLAGS_clocks_per_us);\n#endif\n"
        b"  // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n"
    )


def _trigger_admission_bundle(genome: Genome, commit: str, source_root: Path):
    _write_trigger_source(source_root)
    evidence = SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA_V2,
        source_root=str(source_root.resolve()),
        ccbench_commit=commit,
        genome_sha256=hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest(),
        src_token="7" * 64,
        source_bytes_sha256="8" * 64,
        tracked_clean=False,
        tracked_diff_sha256="9" * 64,
        tracked_paths=(source_digest.TRIGGER_GATE_SOURCE_REL,),
        trigger_gate_language=TRIGGER_GATE_LANGUAGE,
        trigger_gate_implementation_sha256=hashlib.sha256(
            _TRIGGER_IMPLEMENTATION
        ).hexdigest(),
    )
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    capability = attest_generator_output(
        context, evidence, generator_input_sha256="1" * 64,
    )
    with mock.patch.object(
        source_digest, "resolve_evidence", return_value=evidence,
    ):
        trigger_receipt = issue_trigger_gate_receipt(evidence, genome=genome)
    admission = derive_build_admission(
        context,
        evidence,
        generator_receipt=capability,
        trigger_gate_receipt=trigger_receipt,
    )
    return context, evidence, admission


def _actual_trigger_resolver(expected: SourceEvidence):
    def resolve(genome, commit, *, ccbench_dir, cxx):
        inspected = source_digest.inspect_trigger_gate_source(
            expected.source_root, required=True,
        )
        assert inspected is not None
        if inspected[1] == expected.trigger_gate_implementation_sha256:
            return expected
        body = expected.as_receipt()
        body["trigger_gate_implementation_sha256"] = inspected[1]
        return SourceEvidence.from_receipt(body)

    return resolve


def test_p1_p9_raw_and_indented_reach_quarantine_receipt_and_build_boundary(
        tmp_path, monkeypatch):
    controls = (
        Path(__file__).resolve().parents[2]
        / "output/insights/2026-08-04_t409-evolve-hole-allowlist/positive-controls.txt"
    ).read_text(encoding="utf-8").splitlines()
    expressions = [
        controls[line_number - 1][1:-1]
        for line_number in (1, 3, 5, 41, 43, 45, 47, 49, 51)
    ]
    genome = Genome("silo", {"BACKOFF_TRIGGER_GATING": 1})
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    reached: list[str] = []

    class BuildBoundaryReached(RuntimeError):
        pass

    def stop_at_build_boundary(sub, commit):
        reached.append(sub)
        raise BuildBoundaryReached

    monkeypatch.setattr(buildcache, "_verify_ccbench_commit", stop_at_build_boundary)
    for index, expression in enumerate(expressions):
        for form, implementation in (
            ("raw", expression), ("indented", "  " + expression),
        ):
            source_root = tmp_path / f"p{index + 1}-{form}"
            path = source_root / source_digest.TRIGGER_GATE_SOURCE_REL
            path.parent.mkdir(parents=True)
            path.write_text(
                "  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
                "#if BACKOFF_TRIGGER_GATING\n"
                "  izanagi_gate_pass = true;\n"
                "#else\n"
                "  Backoff::backoff(FLAGS_clocks_per_us);\n"
                "#endif\n"
                "  // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n",
                encoding="utf-8",
            )
            quarantine, _base, rendered, _diff = p3_s4_loop.quarantine(
                str(source_root), implementation,
                marker_id="silo-backoff-trigger-gating",
                source_rel=source_digest.TRIGGER_GATE_SOURCE_REL,
                write=True,
            )
            assert quarantine.passed
            assert rendered == path.read_text(encoding="utf-8")
            inspected = source_digest.inspect_trigger_gate_source(
                str(source_root), required=True,
            )
            assert inspected is not None
            evidence = SourceEvidence(
                schema_version=SOURCE_EVIDENCE_SCHEMA_V2,
                source_root=str(source_root.resolve()),
                ccbench_commit=CURRENT_PIN,
                genome_sha256=hashlib.sha256(
                    genome.canonical().encode("utf-8")
                ).hexdigest(),
                src_token=hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                source_bytes_sha256=hashlib.sha256(
                    path.read_bytes()
                ).hexdigest(),
                tracked_clean=False,
                tracked_diff_sha256="9" * 64,
                tracked_paths=(source_digest.TRIGGER_GATE_SOURCE_REL,),
                trigger_gate_language=TRIGGER_GATE_LANGUAGE,
                trigger_gate_implementation_sha256=inspected[1],
            )
            monkeypatch.setattr(
                source_digest, "resolve_evidence", lambda *a, _e=evidence, **k: _e,
            )
            capability = attest_generator_output(
                context, evidence, generator_input_sha256="1" * 64,
            )
            trigger = issue_trigger_gate_receipt(evidence, genome=genome)
            admission = derive_build_admission(
                context, evidence, generator_receipt=capability,
                trigger_gate_receipt=trigger,
            )
            with pytest.raises(BuildBoundaryReached):
                buildcache.build(
                    genome, CURRENT_PIN, trace=True,
                    ccbench_dir=str(source_root),
                    cache_root=str(tmp_path / "cache"),
                    admission=admission,
                    build_context=context,
                    source_evidence=evidence,
                    site="linux-baremetal",
                )
    assert len(reached) == 18


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


def _install_toolchain(tmp_path: Path, monkeypatch, *, cxx_version: str = "cxx version A") -> Path:
    bindir = tmp_path / "tools"
    bindir.mkdir(exist_ok=True)
    _write_tool(bindir / "test-cc", "cc version A")
    _write_tool(bindir / "test-cxx", cxx_version)
    _write_tool(bindir / "cmake", "cmake version A")
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    return bindir


def _fake_build_environment(monkeypatch, tmp_path: Path, payload: bytes = b"v2-binary") -> None:
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

    def fake_run(cmd, what, timeout_s=None, *, site=None, env=None):
        if what == "build":
            bdir = Path(cmd[cmd.index("--build") + 1])
            binary = bdir / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(payload)

    monkeypatch.setattr(buildcache, "_run", fake_run)


def _build(tmp_path: Path, contract: ExecutionEnvironmentContract, *, trace: bool = True,
           ccbench_dir: str = "", timeout_s: int | None = None,
           dependency_prefix: str = "", site: str | None = None):
    genome = Genome("silo", {"BACK_OFF": 1})
    source_root = ccbench_dir or str(tmp_path / "ccbench")
    context, evidence, admission = _admission_bundle(
        genome, "a" * 40, source_root,
    )
    kwargs = dict(
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
    if dependency_prefix:
        kwargs["dependency_prefix"] = dependency_prefix
    if site is not None:
        kwargs["site"] = site
    return buildcache.build_v2(
        genome,
        **kwargs,
    )


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


def test_trigger_cache_identity_binds_language_and_authoritative_receipt(tmp_path):
    genome = Genome("silo", {"BACK_OFF": 1, "BACKOFF_TRIGGER_GATING": 1})
    context, evidence, admission = _trigger_admission_bundle(
        genome, "a" * 40, tmp_path / "ccbench",
    )
    body = admission.as_cache_identity()
    trigger = body["trigger_gate_receipt"]
    key = buildcache.cache_key(
        genome, "a" * 40, False, evidence.src_token, admission=admission,
    )
    old_body, _ = legacy_trigger_admission_projection(
        body, expected_policy=context.policy,
    )
    old_key = buildcache._legacy_trigger_cache_key(
        genome, "a" * 40, False, evidence.src_token,
        buildcache.DEFAULT_CC, buildcache.DEFAULT_CXX,
        old_body["receipt_sha256"],
    )
    preimage, _ = buildcache._v2_identity(
        genome,
        "a" * 40,
        False,
        evidence.src_token,
        "cc",
        "cxx",
        {
            role: {
                "requested": role,
                "realpath": f"/tool/{role}",
                "version_first_line": "v1",
            }
            for role in ("cc", "cxx", "cmake")
        },
        site="test",
        dependency_prefix=[],
        admission=dict(body),
    )
    assert key != old_key
    assert preimage["trigger_gate_language"] == TRIGGER_GATE_LANGUAGE
    assert preimage["trigger_gate_receipt_sha256"] == trigger["receipt_sha256"]


def test_legacy_trigger_cache_entry_promotes_only_to_new_key(tmp_path, monkeypatch):
    _fake_build_environment(monkeypatch, tmp_path)
    genome = Genome("silo", {"BACK_OFF": 1, "BACKOFF_TRIGGER_GATING": 1})
    context, evidence, admission = _trigger_admission_bundle(
        genome, "a" * 40, tmp_path / "ccbench",
    )
    buildcache.source_digest.resolve_evidence = _actual_trigger_resolver(evidence)
    old_body, old_source = legacy_trigger_admission_projection(
        admission.as_cache_identity(), expected_policy=context.policy,
    )
    root = tmp_path / "cache"
    old_key = buildcache._legacy_trigger_cache_key(
        genome, "a" * 40, True, evidence.src_token,
        buildcache.DEFAULT_CC, buildcache.DEFAULT_CXX,
        old_body["receipt_sha256"],
    )
    old_dir = root / old_key
    old_binary = old_dir / "cc" / "silo" / "ycsb_silo.exe"
    old_binary.parent.mkdir(parents=True)
    old_binary.write_bytes(b"legacy-trigger-binary")
    (old_dir / "admission.json").write_text(
        json.dumps({
            "schema_version": "buildcache-legacy-admission/v1",
            "admission": old_body,
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        buildcache, "_run", lambda *a, **k: pytest.fail("promotion missed old cache"),
    )

    result = buildcache.build(
        genome,
        "a" * 40,
        True,
        cache_root=str(root),
        admission=admission,
        build_context=context,
        source_evidence=evidence,
    )
    new_key = buildcache.cache_key(
        genome, "a" * 40, True, evidence.src_token, admission=admission,
    )
    new_binary = root / new_key / "cc" / "silo" / "ycsb_silo.exe"
    new_sidecar = json.loads(
        (root / new_key / "admission.json").read_text(encoding="utf-8")
    )
    assert old_source.schema_version == "source-evidence/v1"
    assert result.cached and Path(result.binary) == new_binary
    assert new_binary.read_bytes() == b"legacy-trigger-binary"
    assert new_sidecar["admission"] == admission.as_cache_identity()
    assert old_binary.read_bytes() == b"legacy-trigger-binary"


def test_v2_legacy_trigger_entry_promotes_with_current_receipt(tmp_path, monkeypatch):
    _install_toolchain(tmp_path, monkeypatch)
    _fake_build_environment(monkeypatch, tmp_path)
    genome = Genome("silo", {"BACK_OFF": 1, "BACKOFF_TRIGGER_GATING": 1})
    context, evidence, admission = _trigger_admission_bundle(
        genome, "a" * 40, tmp_path / "ccbench",
    )
    buildcache.source_digest.resolve_evidence = _actual_trigger_resolver(evidence)
    old_body, old_source = legacy_trigger_admission_projection(
        admission.as_cache_identity(), expected_policy=context.policy,
    )
    toolchain = buildcache._toolchain_manifest("test-cc", "test-cxx")
    old_preimage, old_digest = buildcache._v2_identity(
        genome,
        "a" * 40,
        True,
        evidence.src_token,
        "test-cc",
        "test-cxx",
        toolchain,
        site=buildcache.site_policy.OTHER,
        dependency_prefix=[],
        admission=dict(old_body),
    )
    contract = _contract(1)
    old_dir = tmp_path / "cache" / "contracts" / contract.contract_sha256 / old_digest
    old_binary = old_dir / "cc" / "silo" / "ycsb_silo.exe"
    old_binary.parent.mkdir(parents=True)
    old_binary.write_bytes(b"legacy-v2-trigger-binary")
    (old_dir / "completion.json").write_text(
        json.dumps({
            "schema_version": "buildcache/v2",
            "completion_marker": "complete",
            "full_build_digest": old_digest,
            "contract_sha256": contract.contract_sha256,
            "preimage": old_preimage,
            "admission": old_body,
            "toolchain": toolchain,
            "binary": {
                "relative_path": "cc/silo/ycsb_silo.exe",
                "sha256": hashlib.sha256(b"legacy-v2-trigger-binary").hexdigest(),
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        buildcache, "_run", lambda *a, **k: pytest.fail("v2 promotion rebuilt"),
    )

    result = buildcache.build_v2(
        genome,
        admission=admission,
        build_context=context,
        source_evidence=evidence,
        contract=contract,
        ccbench_commit="a" * 40,
        trace=True,
        src_token=evidence.src_token,
        cc="test-cc",
        cxx="test-cxx",
        cache_root=str(tmp_path / "cache"),
        ccbench_dir=str(tmp_path / "ccbench"),
    )
    manifest = json.loads(
        (Path(result.build_dir) / "completion.json").read_text(encoding="utf-8")
    )
    assert old_source.schema_version == "source-evidence/v1"
    assert result.cached and Path(result.binary).read_bytes() == b"legacy-v2-trigger-binary"
    assert manifest["admission"] == admission.as_cache_identity()
    assert manifest["preimage"]["trigger_gate_language"] == TRIGGER_GATE_LANGUAGE
    assert old_binary.read_bytes() == b"legacy-v2-trigger-binary"


@pytest.mark.parametrize("mutation", ["source-unavailable", "rejected", "digest-mismatch"])
def test_legacy_trigger_cache_promotion_rejects_untrusted_source(
        tmp_path, monkeypatch, mutation):
    _fake_build_environment(monkeypatch, tmp_path)
    genome = Genome("silo", {"BACK_OFF": 1, "BACKOFF_TRIGGER_GATING": 1})
    context, evidence, admission = _trigger_admission_bundle(
        genome, "a" * 40, tmp_path / "ccbench",
    )
    old_body, _ = legacy_trigger_admission_projection(
        admission.as_cache_identity(), expected_policy=context.policy,
    )
    root = tmp_path / "cache"
    old_key = buildcache._legacy_trigger_cache_key(
        genome, "a" * 40, True, evidence.src_token,
        buildcache.DEFAULT_CC, buildcache.DEFAULT_CXX,
        old_body["receipt_sha256"],
    )
    old_dir = root / old_key
    old_binary = old_dir / "cc" / "silo" / "ycsb_silo.exe"
    old_binary.parent.mkdir(parents=True)
    old_binary.write_bytes(b"must-not-promote")
    (old_dir / "admission.json").write_text(
        json.dumps({
            "schema_version": "buildcache-legacy-admission/v1",
            "admission": old_body,
        }),
        encoding="utf-8",
    )
    source_path = Path(evidence.source_root) / source_digest.TRIGGER_GATE_SOURCE_REL
    if mutation == "source-unavailable":
        source_path.unlink()
    elif mutation == "rejected":
        _write_trigger_source(
            Path(evidence.source_root),
            b"  izanagi_gate_pass = true;\rSECRET_CANARY",
        )
    else:
        _write_trigger_source(
            Path(evidence.source_root), b"  izanagi_gate_pass = (true);",
        )
    buildcache.source_digest.resolve_evidence = _actual_trigger_resolver(evidence)
    monkeypatch.setattr(
        buildcache, "_run", lambda *a, **k: pytest.fail("rejected cache was rebuilt"),
    )

    with pytest.raises(
            (buildcache.BuildCacheError, TriggerGateSourceError, RuntimeError)) as caught:
        buildcache.build(
            genome,
            "a" * 40,
            True,
            cache_root=str(root),
            admission=admission,
            build_context=context,
            source_evidence=evidence,
        )
    new_key = buildcache.cache_key(
        genome, "a" * 40, True, evidence.src_token, admission=admission,
    )
    assert not (root / new_key).exists()
    assert old_binary.read_bytes() == b"must-not-promote"
    assert "SECRET_CANARY" not in repr(caught.value)


def test_m12_trigger_cache_hit_rereads_actual_source_without_leak(
        tmp_path, monkeypatch):
    _fake_build_environment(monkeypatch, tmp_path, payload=b"trigger-hit")
    genome = Genome("silo", {"BACK_OFF": 1, "BACKOFF_TRIGGER_GATING": 1})
    context, evidence, admission = _trigger_admission_bundle(
        genome, "a" * 40, tmp_path / "ccbench",
    )
    buildcache.source_digest.resolve_evidence = _actual_trigger_resolver(evidence)
    kwargs = {
        "cache_root": str(tmp_path / "cache"),
        "admission": admission,
        "build_context": context,
        "source_evidence": evidence,
    }
    fresh = buildcache.build(genome, "a" * 40, True, **kwargs)
    assert not fresh.cached

    original_validate = buildcache._validate_legacy_admission_sidecar

    def validate_then_swap(*args, **kwargs):
        original_validate(*args, **kwargs)
        _write_trigger_source(
            Path(evidence.source_root),
            b"  izanagi_gate_pass = true;\rSECRET_CANARY",
        )

    monkeypatch.setattr(
        buildcache, "_validate_legacy_admission_sidecar", validate_then_swap,
    )
    with pytest.raises(TriggerGateSourceError) as caught:
        buildcache.build(genome, "a" * 40, True, **kwargs)
    assert "SECRET_CANARY" not in repr(caught.value)


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
    assert manifest["binary"]["sha256"] == hashlib.sha256(b"manifest-payload").hexdigest()


_CHILD = r"""
import hashlib, json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])
from campaign import buildcache
from campaign.build_admission import (
    GeneratorId, attest_generator_output, build_run_context, derive_build_admission,
)
from campaign.env_contract import CalibrationRef, ExecutionEnvironmentContract, IsolationPolicy
from campaign.model import Genome
from campaign.source_digest import SourceEvidence

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
    argv = [sys.executable, "-c", textwrap.dedent(_CHILD), str(_ORCH), str(tmp_path), str(sync), str(tools)]
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


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
