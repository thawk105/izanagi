# -*- coding: utf-8 -*-
"""実 cmake build の site gate と build jobs provenance の回帰テスト。"""
from __future__ import annotations

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
sys.path.insert(0, str(_ORCH))

from campaign import (  # noqa: E402
    buildcache,
    s2_verify_calibration,
    s3_lock_coverage,
    s5_permutation_coverage,
    s8a_trigger_coverage,
    site_policy,
)
from campaign.env_contract import (  # noqa: E402
    CalibrationRef,
    ExecutionEnvironmentContract,
    IsolationPolicy,
)
from campaign.model import Genome  # noqa: E402


_COVERAGE_MODULES = (
    s2_verify_calibration,
    s3_lock_coverage,
    s5_permutation_coverage,
    s8a_trigger_coverage,
)


def _call_coverage_configure(module, root: Path, site: str) -> None:
    if module is s2_verify_calibration:
        module._broken_build_and_verify(
            "unused.patch", "UNUSED_DEFINE", {}, site=site,
        )
    elif module in (s3_lock_coverage, s5_permutation_coverage):
        module._build_broken(
            "unused.patch", "UNUSED_DEFINE", str(root / "build"), site=site,
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


def _fake_v2_builds(root: Path, sites: tuple[str, ...]):
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
                Genome("silo", {"BACK_OFF": 1}),
                contract=_contract(),
                ccbench_commit="a" * 40,
                trace=True,
                src_token="stock",
                cc="test-cc",
                cxx="test-cxx",
                cache_root=str(root / "cache"),
                ccbench_dir=str(root / "ccbench"),
                site=site,
            ))
    return results, calls


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


def test_other_and_compute_keep_buildcache_default_j16_and_do_not_refuse():
    assert inspect.signature(buildcache.build).parameters["jobs"].default == 16
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
    )
    assert build_cmd[-2:] == ["-j", "16"]

    for site in (site_policy.OTHER, site_policy.PEGASUS_COMPUTE):
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


def test_cache_hit_does_not_consult_real_build_gate_or_call_run_stub():
    with tempfile.TemporaryDirectory(prefix="izanagi_site_gate_hit_") as tmp:
        results, calls = _fake_v2_builds(
            Path(tmp),
            (site_policy.OTHER, site_policy.PEGASUS_LOGIN),
        )
    assert not results[0].cached
    assert results[1].cached
    assert [call[1] for call in calls] == ["configure", "build"]


def test_jobs_are_absent_from_cache_identity_and_v2_completion_manifest():
    assert "jobs" not in inspect.signature(buildcache.cache_key).parameters
    with tempfile.TemporaryDirectory(prefix="izanagi_site_gate_manifest_") as tmp:
        results, _ = _fake_v2_builds(Path(tmp), (site_policy.OTHER,))
        result = results[0]
        manifest = json.loads(
            (Path(result.build_dir) / "completion.json").read_text(encoding="utf-8")
        )
    assert "jobs" not in manifest
    assert "build_argv" not in manifest
    assert "build_cmd" not in manifest
    assert "jobs" not in manifest["preimage"]
    assert result.build_argv[-2:] == ("-j", "16")


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
    for module in _COVERAGE_MODULES:
        for site in (site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT):
            calls = []

            def fake_subprocess_run(*args, **kwargs):
                calls.append((args, kwargs))
                return SimpleNamespace(returncode=0)

            with tempfile.TemporaryDirectory(
                    prefix="izanagi_coverage_configure_gate_") as tmp:
                with ExitStack() as stack:
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
