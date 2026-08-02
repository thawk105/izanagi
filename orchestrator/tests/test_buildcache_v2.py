# -*- coding: utf-8 -*-
"""buildcache v2 の contract namespace / 完成 manifest / 並行 claim 回帰。"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH))

from campaign import buildcache  # noqa: E402
from campaign.build_admission import (BuildAdmission, BuildAdmissionError,  # noqa: E402
                                      BuildProvenance)
from campaign.env_contract import (  # noqa: E402
    CalibrationRef,
    ExecutionEnvironmentContract,
    IsolationPolicy,
)
from campaign.model import Genome  # noqa: E402

_STOCK_ADMISSION = BuildAdmission(BuildProvenance.STOCK_OR_PINNED)


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
            resolve=lambda *a, **k: "stock",
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
    kwargs = dict(
        admission=_STOCK_ADMISSION,
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
        Genome("silo", {"BACK_OFF": 1}),
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

    def resolve(_genome, _commit, sub, _cxx):
        calls["resolve"].append(sub)
        return "stock"

    def trace_diff(_genome, _commit, sub, _cxx):
        calls["trace_diff"].append(sub)

    buildcache.source_digest.resolve = resolve
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
    custom = _build(
        tmp_path, _contract(1), trace=True,
        ccbench_dir=str(tmp_path / "same-content-prepared-tree"),
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
    legacy = tmp_path / "cache" / buildcache.cache_key(
        genome, "a" * 40, True, src_token="stock", cc="test-cc", cxx="test-cxx"
    ) / "cc" / "silo" / "ycsb_silo.exe"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(b"legacy")
    result = _build(tmp_path, _contract(1))
    assert not result.cached
    assert Path(result.binary).read_bytes() == b"v2"
    assert "/contracts/" in result.build_dir


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

    def resolved(*args, **kwargs):
        calls["resolve"] += 1
        return "stock"

    def trace_diff(*args, **kwargs):
        calls["trace_diff"] += 1

    def no_trace(*args, **kwargs):
        calls["nm"] += 1

    buildcache.source_digest.resolve = resolved
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
        "cc": "test-cc",
        "ccbench_commit": "a" * 40,
        "cxx": "test-cxx",
        "genome_canonical": "silo|BACK_OFF=1",
        "src_token": "stock",
        "toolchain_manifest_sha256": manifest["preimage"]["toolchain_manifest_sha256"],
        "trace": False,
    }
    assert len(manifest["preimage"]["toolchain_manifest_sha256"]) == 64
    assert manifest["toolchain"]["cxx"]["version_first_line"] == "cxx version A"
    assert manifest["binary"]["sha256"] == hashlib.sha256(b"manifest-payload").hexdigest()


_CHILD = r"""
import json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])
from campaign import buildcache
from campaign.build_admission import BuildAdmission, BuildProvenance
from campaign.env_contract import CalibrationRef, ExecutionEnvironmentContract, IsolationPolicy
from campaign.model import Genome

_STOCK_ADMISSION = BuildAdmission(BuildProvenance.STOCK_OR_PINNED)

root, sync, tools = map(Path, sys.argv[2:5])
os.environ["PATH"] = str(tools) + os.pathsep + os.environ.get("PATH", "")
buildcache._ccbench_dir = lambda: str(root / "ccbench")
buildcache._verify_ccbench_commit = lambda *a, **k: None
buildcache.source_digest = SimpleNamespace(
    STOCK="stock",
    assert_worktree_within_allowlist=lambda *a, **k: None,
    assert_trace_diff_matches_head=lambda *a, **k: None,
    resolve=lambda *a, **k: "stock",
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
        Genome("silo", {"BACK_OFF": 1}), admission=_STOCK_ADMISSION,
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
    kwargs = dict(
        admission=_STOCK_ADMISSION,
        ccbench_commit="a" * 40, trace=True, src_token="stock",
        cc="test-cc", cxx="test-cxx", cache_root=str(tmp_path / "cache"),
    )
    with pytest.raises(TypeError):
        buildcache.build_v2(Genome("silo", {}), **kwargs)
    with pytest.raises((TypeError, buildcache.BuildCacheError)):
        buildcache.build_v2(Genome("silo", {}), contract=None, **kwargs)


def _forged_unadmitted_coder():
    value = object.__new__(BuildAdmission)
    object.__setattr__(value, "provenance_class", BuildProvenance.CODER_DERIVED)
    object.__setattr__(value, "coder_derived_opt_in", False)
    return value


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
    with pytest.raises(BuildAdmissionError):
        if api == "legacy":
            buildcache.build(
                genome, "a" * 40, trace=True,
                admission=_forged_unadmitted_coder(),
            )
        else:
            buildcache.build_v2(
                genome, admission=_forged_unadmitted_coder(), contract=None,
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
