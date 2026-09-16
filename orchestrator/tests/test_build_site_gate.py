# -*- coding: utf-8 -*-
"""実 cmake build の site gate と build jobs provenance の回帰テスト。"""
from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
import tempfile
from contextlib import ExitStack, nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH.parent))

from orchestrator.campaign import (  # noqa: E402
    buildcache,
    pipeline,
    s2_verify_calibration,
    s3_lock_coverage,
    s5_permutation_coverage,
    s8a_trigger_coverage,
    site_policy,
)
from orchestrator.campaign.env_contract import (  # noqa: E402
    CalibrationRef,
    ExecutionEnvironmentContract,
    IsolationPolicy,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SOURCE_EVIDENCE_SCHEMA,
    SourceEvidence,
)
from condition_gate_test_support import (  # noqa: E402
    TRIGGER_GATING_SOURCE,
    condition_gate_compilers,
    cxx_flag_owner_source,
    install_condition_gate_build_fixture,
)


_COVERAGE_MODULES = (
    s2_verify_calibration,
    s3_lock_coverage,
    s5_permutation_coverage,
    s8a_trigger_coverage,
)


def test_s2_verifier_run_passes_commit_witness_to_cli():
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "results": [{
                    "verdict": "serializable",
                    "certified": True,
                    "total_cycles": 0,
                    "stats": {"txns": 17, "edges": 0},
                }],
            }),
            stderr="Maximum resident set size (kbytes): 1024\n",
        )

    with patch.object(s2_verify_calibration.subprocess, "run", fake_run):
        result = s2_verify_calibration._verifier_run("/fixture/traces", 17)

    assert result["certified"] is True
    assert len(calls) == 1
    cmd = calls[0][0]
    assert cmd[-2:] == ["--expected-commits", "17"]


def _s2_run_once_with_stdout(stdout: str):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    with patch.object(s2_verify_calibration.subprocess, "run", fake_run):
        return s2_verify_calibration._run_once(
            "/fixture/ycsb_silo.exe", {}, 1, trace=False,
        )


def _assert_s2_run_once_rejects_stdout(stdout: str, message: str) -> None:
    caught = None
    try:
        _s2_run_once_with_stdout(stdout)
    except RuntimeError as exc:
        caught = exc
    assert caught is not None
    assert message in str(caught)


def test_s2_run_once_accepts_unique_zero_batch_commit_witness():
    result = _s2_run_once_with_stdout(
        "abort_counts_: 3\ncommit_counts_: 17\nbatch_commit_counts_: 0\n"
    )
    assert result["commits"] == 17
    assert result["aborts"] == 3


def test_s2_run_once_rejects_duplicate_main_commit_witness():
    _assert_s2_run_once_rejects_stdout(
        "abort_counts_: 3\ncommit_counts_: 1\ncommit_counts_: 17\n"
        "batch_commit_counts_: 0\n",
        "欠落または不正",
    )


def test_s2_run_once_rejects_duplicate_batch_commit_witness():
    _assert_s2_run_once_rejects_stdout(
        "abort_counts_: 3\ncommit_counts_: 17\nbatch_commit_counts_: 0\n"
        "batch_commit_counts_: 0\n",
        "欠落または不正",
    )


def test_s2_run_once_rejects_missing_main_commit_witness():
    _assert_s2_run_once_rejects_stdout(
        "abort_counts_: 3\nbatch_commit_counts_: 0\n",
        "欠落または不正",
    )


def test_s2_run_once_rejects_missing_batch_commit_witness():
    _assert_s2_run_once_rejects_stdout(
        "abort_counts_: 3\ncommit_counts_: 17\n",
        "欠落または不正",
    )


def test_s2_run_once_rejects_negative_commit_witness():
    _assert_s2_run_once_rejects_stdout(
        "abort_counts_: 3\ncommit_counts_: -1\nbatch_commit_counts_: 0\n",
        "欠落または不正",
    )


def test_s2_run_once_rejects_noninteger_commit_witness():
    _assert_s2_run_once_rejects_stdout(
        "abort_counts_: 3\ncommit_counts_: seventeen\n"
        "batch_commit_counts_: 0\n",
        "欠落または不正",
    )


def test_s2_run_once_rejects_nonzero_batch_commit_witness():
    _assert_s2_run_once_rejects_stdout(
        "abort_counts_: 3\ncommit_counts_: 17\nbatch_commit_counts_: 1\n",
        "batch_commit_counts_ が非 0",
    )


def _call_coverage_configure(module, root: Path, site: str) -> None:
    if module is s2_verify_calibration:
        module._broken_build_and_verify(
            "unused.patch", module.NORW_DEFINE, {}, site=site,
        )
    elif module is s3_lock_coverage:
        module._build_broken(
            "unused.patch", module.LOCKSKIP_DEFINE,
            str(root / "build"), site=site,
        )
    elif module is s5_permutation_coverage:
        module._build_broken(
            "unused.patch", module.ERASE_DEFINE,
            str(root / "build"), site=site,
        )
    elif module is s8a_trigger_coverage:
        module._build(str(root / "build"), site=site)
    else:
        raise AssertionError(f"未対応 coverage module: {module.__name__}")


def _contract() -> ExecutionEnvironmentContract:
    return ExecutionEnvironmentContract(
        env_tag="test-build-site-gate",
        clocks_per_us=1800,
        numactl=(),
        attestation_mode="none",
        isolation_policy=IsolationPolicy(single_process=False, allow_resume=True),
        calibration_ref=CalibrationRef(
            path="output/env/test-build-site-gate.json",
            sha256="1" * 64,
        ),
    )


def _stock_bundle(genome: Genome, ccbench_dir: Path):
    """現行 pin の clean stock evidence から fixture 用 capability を導出する。"""
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    evidence = SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=str(ccbench_dir.resolve()),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
        src_token="stock",
        source_bytes_sha256=hashlib.sha256(b"site-gate-stock-source").hexdigest(),
        tracked_clean=True,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
    )
    return context, evidence, derive_build_admission(context, evidence)


def _fake_v2_builds(root: Path, sites: tuple[str, ...]):
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _stock_bundle(genome, root / "ccbench")
    toolchain = {
        "cc": {
            "requested": "test-cc",
            "realpath": "/fake/test-cc",
            "version_first_line": "cc version",
        },
        "cxx": {
            "requested": "test-cxx",
            "realpath": "/fake/test-cxx",
            "version_first_line": "cxx version",
        },
        "cmake": {
            "requested": "cmake",
            "realpath": "/fake/cmake",
            "version_first_line": "cmake version",
        },
    }
    fake_source_digest = SimpleNamespace(
        STOCK="stock",
        assert_worktree_within_allowlist=lambda *a, **k: None,
        assert_trace_diff_matches_head=lambda *a, **k: None,
        resolve=lambda *a, **k: "stock",
        resolve_evidence=lambda *a, **k: evidence,
    )
    calls = []

    def fake_run(cmd, what, timeout_s=None, *, site=None):
        calls.append((tuple(cmd), what, timeout_s, site))
        if what == "build":
            bdir = Path(cmd[cmd.index("--build") + 1])
            binary = bdir / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(b"site-gate-v2-binary")

    results = []
    with ExitStack() as stack:
        stack.enter_context(patch.object(buildcache, "_toolchain_manifest",
                                         lambda *a, **k: toolchain))
        stack.enter_context(patch.object(buildcache, "_verify_ccbench_commit",
                                         lambda *a, **k: None))
        stack.enter_context(patch.object(buildcache, "source_digest",
                                         fake_source_digest))
        stack.enter_context(patch.object(buildcache, "_assert_no_trace_symbols",
                                         lambda *a, **k: None))
        stack.enter_context(patch.object(buildcache, "_run", fake_run))
        for site in sites:
            results.append(buildcache.build_v2(
                genome,
                admission=admission,
                build_context=context,
                source_evidence=evidence,
                contract=_contract(),
                ccbench_commit=CURRENT_PIN,
                trace=True,
                src_token="stock",
                cc="test-cc",
                cxx="test-cxx",
                cache_root=str(root / "cache"),
                ccbench_dir=str(root / "ccbench"),
                site=site,
            ))
    return results, calls


def _fake_legacy_build(root: Path, *, site: str, jobs: int | None):
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = _stock_bundle(genome, root / "ccbench")
    fake_source_digest = SimpleNamespace(
        STOCK="stock",
        assert_worktree_within_allowlist=lambda *a, **k: None,
        assert_trace_diff_matches_head=lambda *a, **k: None,
        resolve=lambda *a, **k: "stock",
        resolve_evidence=lambda *a, **k: evidence,
    )
    calls = []

    def fake_run(cmd, what, timeout_s=None, *, site=None):
        calls.append((tuple(cmd), what, timeout_s, site))
        if what == "build":
            bdir = Path(cmd[cmd.index("--build") + 1])
            binary = bdir / "cc" / "silo" / "ycsb_silo.exe"
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(b"site-gate-legacy-binary")

    with ExitStack() as stack:
        stack.enter_context(patch.object(
            buildcache, "_verify_ccbench_commit", lambda *a, **k: None,
        ))
        stack.enter_context(patch.object(
            buildcache, "source_digest", fake_source_digest,
        ))
        stack.enter_context(patch.object(buildcache, "_run", fake_run))
        result = buildcache.build(
            genome,
            ccbench_commit=CURRENT_PIN,
            trace=True,
            cache_root=str(root / "cache"),
            ccbench_dir=str(root / "ccbench"),
            src_token="stock",
            jobs=jobs,
            admission=admission,
            build_context=context,
            source_evidence=evidence,
            site=site,
        )
    return result, calls


def test_m11_login_and_suspect_refuse_immediately_before_real_cmake_build():
    # Mutation M11: 実 cmake 直前の login 拒否 gate を削除すると、この test は
    # subprocess stub まで到達して赤になる。
    for site in (site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT):
        for cmd, what in (
                (["cmake", "-S", "/src", "-B", "/tmp/not-executed"], "configure"),
                (["cmake", "--build", "/tmp/not-executed", "-j", "16"], "build")):
            calls = []

            def fake_subprocess_run(*args, **kwargs):
                calls.append((args, kwargs))
                return SimpleNamespace(returncode=0, stderr="")

            with patch.object(buildcache.subprocess, "run", fake_subprocess_run):
                try:
                    buildcache._run(cmd, what, site=site)
                except buildcache.BuildError:
                    pass
                else:
                    raise AssertionError(
                        f"{site} で cmake {what} が拒否されなかった"
                    )
            assert calls == [], f"{site} で subprocess 起動前に拒否されていない"


def test_site_compiler_helper_uses_system_gcc_only_on_actual_compute():
    with patch.object(
            site_policy, "current_site", return_value=site_policy.PEGASUS_COMPUTE):
        assert buildcache.compilers_for_current_site() == ("gcc", "g++")
    for actual_site in (
            site_policy.OTHER, site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT):
        with patch.object(site_policy, "current_site", return_value=actual_site):
            assert buildcache.compilers_for_current_site() == (
                buildcache.DEFAULT_CC, buildcache.DEFAULT_CXX,
            )


def _v2_build_argv(*, site: str, jobs: int | None = None) -> tuple[str, ...]:
    toolchain = {
        role: {"realpath": "/fake/cmake" if role == "cmake" else f"/fake/{role}"}
        for role in ("cc", "cxx", "cmake")
    }
    _, build_cmd = buildcache._v2_commands(
        Genome("silo", {"BACK_OFF": 1}),
        True,
        "/ccbench",
        "/cache/build",
        toolchain,
        jobs=jobs,
        site=site,
    )
    return tuple(build_cmd)


def test_m15_compute_default_jobs_use_all_affinity_cpus():
    """期待赤 node:
    orchestrator/tests/test_build_site_gate.py::test_m15_compute_default_jobs_use_all_affinity_cpus

    M15 = jobs の None 解決を無効化して常に 16 にすると、計算ノードの
    affinity 全数 48 が build command に反映されず赤になる。
    """
    assert inspect.signature(buildcache.build).parameters["jobs"].default is None
    assert inspect.signature(
        buildcache._v2_commands,
    ).parameters["jobs"].default is None
    with patch.object(site_policy, "available_cpus", return_value=48):
        assert _v2_build_argv(
            site=site_policy.PEGASUS_COMPUTE,
        )[-2:] == ("-j", "48")
        with tempfile.TemporaryDirectory(
                prefix="izanagi_site_jobs_compute_") as tmp:
            result, calls = _fake_legacy_build(
                Path(tmp), site=site_policy.PEGASUS_COMPUTE, jobs=None,
            )
    assert result.build_argv[-2:] == ("-j", "48")
    assert calls[-1][0][-2:] == ("-j", "48")


def test_other_default_jobs_remain_j16():
    assert _v2_build_argv(site=site_policy.OTHER)[-2:] == ("-j", "16")
    with tempfile.TemporaryDirectory(
            prefix="izanagi_site_jobs_other_") as tmp:
        result, calls = _fake_legacy_build(
            Path(tmp), site=site_policy.OTHER, jobs=None,
        )
    assert result.build_argv[-2:] == ("-j", "16")
    assert calls[-1][0][-2:] == ("-j", "16")
    assert f"-DCMAKE_C_COMPILER={buildcache.DEFAULT_CC}" in result.configure_argv
    assert f"-DCMAKE_CXX_COMPILER={buildcache.DEFAULT_CXX}" in result.configure_argv
    assert Path(result.build_dir).name == buildcache.cache_key(
        Genome("silo", {"BACK_OFF": 1}), CURRENT_PIN, True, src_token="stock",
        admission=_stock_bundle(
            Genome("silo", {"BACK_OFF": 1}), Path(tmp) / "ccbench",
        )[2],
    )


def test_explicit_jobs_one_is_respected_for_every_site():
    with patch.object(
            site_policy, "default_build_jobs",
            side_effect=AssertionError("明示 jobs で既定値を解決してはならない")):
        for site in (site_policy.OTHER, site_policy.PEGASUS_COMPUTE):
            assert _v2_build_argv(site=site, jobs=1)[-2:] == ("-j", "1")
            with tempfile.TemporaryDirectory(
                    prefix="izanagi_site_jobs_explicit_") as tmp:
                result, calls = _fake_legacy_build(
                    Path(tmp), site=site, jobs=1,
                )
            assert result.build_argv[-2:] == ("-j", "1")
            assert calls[-1][0][-2:] == ("-j", "1")


def test_other_and_compute_do_not_refuse_buildcache_commands():
    for site in (site_policy.OTHER, site_policy.PEGASUS_COMPUTE):
        build_cmd = list(_v2_build_argv(site=site))
        calls = []

        def fake_subprocess_run(cmd, **kwargs):
            calls.append((tuple(cmd), kwargs))
            return SimpleNamespace(returncode=0, stderr="")

        with patch.object(buildcache.subprocess, "run", fake_subprocess_run):
            buildcache._run(build_cmd, "build", site=site)
        assert calls == [(tuple(build_cmd), {
            "capture_output": True,
            "text": True,
            "timeout": None,
        })]


def test_masstree_prebuild_routes_both_commands_through_heavy_site_gate():
    with tempfile.TemporaryDirectory(prefix="izanagi_masstree_prebuild_") as tmp:
        root = Path(tmp)
        base = root / "base"
        source = root / "ccbench"
        base.mkdir()
        source.mkdir()
        gates = []
        launches = []

        def gate(site, what):
            gates.append((site, what))
            return site

        def launch(cmd, **kwargs):
            launches.append((tuple(cmd), kwargs))
            return SimpleNamespace(returncode=0, stderr="")

        manifest = {
            role: {
                "requested": role,
                "realpath": f"/fixture/{role}",
                "version_first_line": "fixture v1",
                "version": "fixture v1",
            }
            for role in ("cc", "cxx", "cmake")
        }
        with patch.object(buildcache, "require_heavy_work_site", gate), patch.object(
                buildcache.subprocess, "run", launch):
            buildcache.prepare_masstree_fetchcontent(
                ccbench_dir=str(source.resolve()),
                fetchcontent_base_dir=str(base.resolve()),
                expected_toolchain_manifest=manifest,
                configure_timeout_s=17,
                target_timeout_s=19,
                site=site_policy.OTHER,
            )
        assert gates == [
            (site_policy.OTHER, "cmake configure"),
            (site_policy.OTHER, "cmake build"),
        ]
        assert len(launches) == 2


def test_cache_hit_does_not_consult_real_build_gate_or_call_run_stub():
    with tempfile.TemporaryDirectory(prefix="izanagi_site_gate_hit_") as tmp:
        results, calls = _fake_v2_builds(
            Path(tmp),
            (site_policy.OTHER, site_policy.PEGASUS_LOGIN),
        )
    assert not results[0].cached
    assert results[1].cached
    assert [call[1] for call in calls] == ["configure", "build"]


def test_m18_real_legacy_cache_hit_login_refuses_trace_producer():
    """実 legacy entry の hit 後でも LOGIN では trace subprocess を起動しない。"""
    with tempfile.TemporaryDirectory(prefix="izanagi_m18_legacy_hit_") as tmp:
        root = Path(tmp)
        fresh, fresh_calls = _fake_legacy_build(
            root, site=site_policy.OTHER, jobs=1,
        )
        hit, hit_calls = _fake_legacy_build(
            root, site=site_policy.PEGASUS_LOGIN, jobs=1,
        )
        assert not fresh.cached and hit.cached
        assert fresh_calls and hit_calls == []

        subprocess_calls = []

        def forbidden_subprocess(*args, **kwargs):
            subprocess_calls.append((args, kwargs))
            raise AssertionError("LOGIN で cached trace binary を起動してはならない")

        with patch.object(
                pipeline, "_resolve_site",
                lambda _site=None: site_policy.PEGASUS_LOGIN), patch.object(
                    pipeline.subprocess, "run", forbidden_subprocess):
            try:
                pipeline._run_trace(
                    hit.binary, str(root / "trace-output"), {}, clocks_per_us=1800,
                )
            except buildcache.BuildError:
                pass
            else:
                raise AssertionError("legacy cache hit 後の trace producer が拒否されなかった")
        assert subprocess_calls == []
        assert not (root / "trace-output" / "log").exists()


def test_jobs_are_absent_from_cache_identity_and_v2_completion_manifest():
    assert "jobs" not in inspect.signature(buildcache.cache_key).parameters
    with tempfile.TemporaryDirectory(prefix="izanagi_site_gate_manifest_") as tmp:
        root = Path(tmp)
        with patch.object(site_policy, "available_cpus", return_value=48):
            legacy_j1, _ = _fake_legacy_build(
                root / "legacy", site=site_policy.OTHER, jobs=1,
            )
            legacy_j48, legacy_hit_calls = _fake_legacy_build(
                root / "legacy", site=site_policy.PEGASUS_COMPUTE, jobs=48,
            )
            first_results, _ = _fake_v2_builds(
                root / "v2", (site_policy.OTHER,),
            )
            first = first_results[0]
            manifest_path = Path(first.build_dir) / "completion.json"
            manifest_before = manifest_path.read_bytes()
            second_results, v2_hit_calls = _fake_v2_builds(
                root / "v2", (site_policy.PEGASUS_COMPUTE,),
            )
            second = second_results[0]
            manifest_after = manifest_path.read_bytes()
        manifest = json.loads(manifest_after.decode("utf-8"))
    assert legacy_j48.cached
    assert legacy_hit_calls == []
    assert legacy_j1.build_dir == legacy_j48.build_dir
    assert legacy_j1.bin_sha256 == legacy_j48.bin_sha256
    assert legacy_j1.build_argv[-2:] == ("-j", "1")
    assert legacy_j48.build_argv[-2:] == ("-j", "48")
    assert second.cached
    assert v2_hit_calls == []
    assert first.build_dir == second.build_dir
    assert first.contract_sha256 == second.contract_sha256
    assert first.bin_sha256 == second.bin_sha256
    assert first.build_argv[-2:] == ("-j", "16")
    assert second.build_argv[-2:] == ("-j", "48")
    assert manifest_before == manifest_after
    assert "jobs" not in manifest
    assert "build_argv" not in manifest
    assert "build_cmd" not in manifest
    assert "jobs" not in manifest["preimage"]


def test_coverage_builds_use_site_jobs_and_refuse_login_and_suspect():
    base_cmd = ["cmake", "--build", "/tmp/not-executed", "--target", "target"]
    for module in _COVERAGE_MODULES:
        for site in (site_policy.OTHER, site_policy.PEGASUS_COMPUTE):
            calls = []

            def fake_subprocess_run(cmd, **kwargs):
                calls.append((tuple(cmd), kwargs))
                return SimpleNamespace(returncode=0)

            with patch.object(module.subprocess, "run", fake_subprocess_run):
                module._run_cmake_build(base_cmd, site=site)
            expected_jobs = site_policy.default_build_jobs(site)
            assert calls == [(
                tuple(base_cmd + ["-j", str(expected_jobs)]),
                {"check": True, "capture_output": True, "text": True},
            )]

        for site in (site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT):
            calls = []
            with patch.object(
                    module.subprocess, "run",
                    lambda *a, **k: calls.append((a, k))):
                try:
                    module._run_cmake_build(base_cmd, site=site)
                except buildcache.BuildError:
                    pass
                else:
                    raise AssertionError(
                        f"{module.__name__}: {site} で build を拒否しなかった"
                    )
            assert calls == []


def test_m11_coverage_configure_gates_are_independent():
    """期待赤 node:
    orchestrator/tests/test_build_site_gate.py::test_m11_coverage_configure_gates_are_independent

    coverage 各 module の configure 直前 gate を単独で削除した場合、後段 build gate
    が拒否しても configure subprocess 到達を観測して赤にする。
    """
    compilers = condition_gate_compilers()
    if compilers is None:
        raise AssertionError(
            "condition gate fixture requires real compilers and CMake"
        )
    real_subprocess_run = subprocess.run
    for module in _COVERAGE_MODULES:
        for site in (site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT):
            calls = []

            def fake_subprocess_run(*args, **kwargs):
                command = tuple(args[0])
                if (
                        Path(command[0]).resolve() == Path(compilers[1]).resolve()
                        or any("izanagi_condition_supply_" in item
                               or "izanagi_compile_time_branch_" in item
                               for item in command)):
                    return real_subprocess_run(*args, **kwargs)
                calls.append((args, kwargs))
                return SimpleNamespace(returncode=0)

            with tempfile.TemporaryDirectory(
                    prefix="izanagi_coverage_configure_gate_") as tmp:
                repo_root = Path(tmp) / "repo"
                source_root = install_condition_gate_build_fixture(
                    repo_root / "external" / "ccbench",
                )
                if module is s8a_trigger_coverage:
                    owner_source = TRIGGER_GATING_SOURCE
                elif module is s2_verify_calibration:
                    owner_source = cxx_flag_owner_source(module.NORW_DEFINE)
                elif module is s3_lock_coverage:
                    owner_source = cxx_flag_owner_source(module.LOCKSKIP_DEFINE)
                else:
                    assert module is s5_permutation_coverage
                    owner_source = cxx_flag_owner_source(module.ERASE_DEFINE)
                (source_root / "cc" / "silo" / "transaction.cc").write_text(
                    owner_source, encoding="utf-8",
                )
                with ExitStack() as stack:
                    stack.enter_context(patch.object(
                        module, "_repo_root", lambda: str(repo_root),
                    ))
                    stack.enter_context(patch.object(
                        module.buildcache, "DEFAULT_CXX", compilers[1],
                    ))
                    if hasattr(module, "applied"):
                        stack.enter_context(patch.object(
                            module, "applied",
                            lambda *a, **k: nullcontext(),
                        ))
                    stack.enter_context(patch.object(
                        module.subprocess, "run", fake_subprocess_run,
                    ))
                    try:
                        _call_coverage_configure(module, Path(tmp), site)
                    except buildcache.BuildError:
                        pass
                    else:
                        raise AssertionError(
                            f"{module.__name__}: {site} で configure gate が拒否しない"
                        )
            assert calls == [], \
                f"{module.__name__}: {site} で configure subprocess が起動した"


def test_m11_coverage_build_gates_are_independent():
    """期待赤 node:
    orchestrator/tests/test_build_site_gate.py::test_m11_coverage_build_gates_are_independent

    configure 経路を通さず build helper を直接叩き、各 module の build 直前 gate
    を単独で削除したときだけ subprocess 到達を観測して赤にする。
    """
    cmd = ["cmake", "--build", "/tmp/not-executed", "--target", "target"]
    for module in _COVERAGE_MODULES:
        for site in (site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT):
            calls = []
            with patch.object(
                    module.subprocess, "run",
                    lambda *a, **k: calls.append((a, k))):
                try:
                    module._run_cmake_build(cmd, site=site)
                except buildcache.BuildError:
                    pass
                else:
                    raise AssertionError(
                        f"{module.__name__}: {site} で build gate が拒否しない"
                    )
            assert calls == [], \
                f"{module.__name__}: {site} で build subprocess が起動した"


def test_coverage_build_keeps_called_process_error_contract():
    base_cmd = ["cmake", "--build", "/tmp/not-executed", "--target", "target"]
    for module in _COVERAGE_MODULES:
        expected = subprocess.CalledProcessError(2, base_cmd)

        def fail(*args, **kwargs):
            raise expected

        with patch.object(module.subprocess, "run", fail):
            try:
                module._run_cmake_build(base_cmd, site=site_policy.OTHER)
            except subprocess.CalledProcessError as actual:
                assert actual is expected
            else:
                raise AssertionError(
                    f"{module.__name__}: CalledProcessError が伝播しなかった"
                )


def _run() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
