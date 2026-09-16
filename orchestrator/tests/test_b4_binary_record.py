"""B-4 glue tests; build spies prove wiring, never a successful real build."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import sys
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from orchestrator.campaign import b4_binary_record as b4
from orchestrator.campaign import s8b_binary_admission as admission
from orchestrator.campaign import s8b_floor_campaign as floor
from orchestrator.campaign.s1_direct_comparison import prepare_cell
from orchestrator.tests.test_s8b_floor_campaign import _honest_portable_built_record


@pytest.fixture
def runtime(tmp_path):
    # Existing durable-reader fixture: no live issuance/build claim and no
    # re-pinning working-tree hashes to satisfy a failing expectation.
    built = _honest_portable_built_record(tmp_path, configuration_id="stock_common")
    rec = built["cell"]
    rec.pop("store_path")
    rec["binary"] = str(tmp_path / "honest-portable.bin")
    rec["_ccbench_root"] = str(tmp_path / "portable-source")
    rec["configure_argv"] = ["cmake", "-S", rec["_ccbench_root"],
                             f"-DCMAKE_PREFIX_PATH={tmp_path}/dependency-install",
                             f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={tmp_path}/third-party/masstree"]
    rec["build_argv"] = ["cmake", "--build", str(tmp_path / "build")]
    return built


def publish(runtime, tmp_path):
    return b4.store_record(runtime, "cell", store_root=tmp_path,
                           output=tmp_path / "record.json", pin="1" * 40,
                           contract_sha256="2" * 64)


def test_real_store_projection_validation_and_single_json(runtime, tmp_path, monkeypatch):
    validator = Mock(wraps=admission.validate_portable_binary_record)
    monkeypatch.setattr(admission, "validate_portable_binary_record", validator)
    record = publish(runtime, tmp_path)
    assert json.loads((tmp_path / "record.json").read_text()) == record
    assert record["admission_receipt"]["schema"] == "s8b-binary-admission/v3"
    assert len(record) == 12
    assert os.access(tmp_path / record["binary"], os.X_OK)
    assert record["binary"] == record["store_path"]
    assert hashlib.sha256((tmp_path / record["binary"]).read_bytes()).hexdigest() == record["binary_sha256"]
    assert record["configure_argv"] == [
        "cmake", "-S", "${CCBENCH_ROOT}",
        "-DCMAKE_PREFIX_PATH=${OUT_ROOT}/dependency-install",
        "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=${OUT_ROOT}/third-party/masstree",
    ]
    assert record["build_argv"] == ["cmake", "--build", "${OUT_ROOT}/build"]
    assert any(call.kwargs == {"expected_policy": None} for call in validator.call_args_list)


def test_real_store_rejects_changed_binary_bytes(runtime, tmp_path):
    Path(runtime["cell"]["binary"]).write_bytes(b"changed actual bytes")
    with pytest.raises(floor.FloorCampaignError, match="sha256.*不一致"):
        publish(runtime, tmp_path)
    assert not (tmp_path / "record.json").exists()
    assert not (tmp_path / "binaries").exists()


def test_real_projection_rejects_before_store(runtime, tmp_path):
    with pytest.raises(floor.FloorCampaignError, match="exact key"):
        floor.project_built_records(runtime, out_root=tmp_path)


def test_create_only_preserves_existing_output(runtime, tmp_path):
    output = tmp_path / "record.json"
    output.write_bytes(b"existing record")
    with pytest.raises(FileExistsError):
        publish(runtime, tmp_path)
    assert output.read_bytes() == b"existing record"


def test_real_validator_rejects_corrupted_receipt(runtime, tmp_path):
    runtime["cell"]["admission_receipt"]["subject"]["trace"] = True
    with pytest.raises(floor.FloorCampaignError):
        publish(runtime, tmp_path)
    assert not (tmp_path / "record.json").exists()


def test_stock_selection_and_explicit_holdout():
    freeze = floor._load_verified_freeze(b4.ROOT / "output/s8b-freeze/holdout_freeze.json").document
    protocol = {"stock_configuration": "stock_common"}
    cells = floor.enumerate_cells(freeze, stock_configuration="stock_common")
    assert cells[0]["configuration_id"] != "stock_common"
    selected = b4.select_cell(freeze, protocol)
    assert selected == next(c for c in cells if c["configuration_id"] == "stock_common")
    last = sorted(freeze["holdouts"])[-1]
    assert b4.select_cell(freeze, protocol, last)["holdout_id"] == last
    with pytest.raises(ValueError, match="no stock cell"):
        b4.select_cell(freeze, protocol, "missing")


@pytest.mark.parametrize("fails", [False, True, "oracle"])
def test_production_wiring_and_environment_restore(tmp_path, monkeypatch, fails, capsys):
    protocol = {"stock_configuration": "stock_common", "ccbench_pin": "1" * 40,
                "freeze": {"path": "freeze.json", "sha256": "2" * 64}}
    contract = SimpleNamespace(contract_sha256="3" * 64)
    calibration = object()
    freeze = object()
    cell = {"cell_id": "cell"}
    monkeypatch.setattr(b4.site_policy, "current_site", lambda: b4.site_policy.PEGASUS_COMPUTE)
    resolver = Mock(return_value=SimpleNamespace(document=protocol))
    monkeypatch.setattr(floor, "resolve_current_floor_protocol", resolver)
    monkeypatch.setattr(floor, "_validate_protocol_against_current", lambda p: (p, contract))
    loader = Mock(return_value=SimpleNamespace(document=freeze))
    monkeypatch.setattr(floor, "_load_verified_freeze", loader)
    monkeypatch.setattr(b4, "select_cell", lambda f, p, h: cell)
    monkeypatch.setattr(b4.env_attestation, "load_verified_calibration", lambda c, r: calibration)
    prefixes = [str(tmp_path / "dependency-install")]
    sources = {name: str(tmp_path / name) for name in ("masstree", "mimalloc", "googletest")}
    monkeypatch.setattr(b4, "prepare_dependencies", lambda *a, **kw: (prefixes, sources))
    # No real build: prebuild spy creates config bytes, real observer hashes them.
    masstree = Path(sources["masstree"])
    masstree.mkdir()
    config = b"#define HAVE_CONFIG 1\n"
    def prebuild(**kw):
        assert kw["fetchcontent_base_dir"] == str(tmp_path)
        assert kw["masstree_source_dir"] == str(masstree)
        assert kw["dependency_prefix"] == prefixes[0]
        (masstree / "config.h").write_bytes(config)
    monkeypatch.setattr(b4.buildcache, "prepare_masstree_fetchcontent", prebuild)
    monkeypatch.setattr(b4.subprocess, "run", lambda *a, **kw: SimpleNamespace(
        returncode=0, stdout=f"{masstree}\n{'a' * 40}\n"))
    monkeypatch.setenv("CMAKE_PREFIX_PATH", "previous")
    result = object()
    builder = Mock(return_value=result)
    monkeypatch.setattr(b4.buildcache, "build_v2", builder)

    def build(f, cells, **kw):
        assert f is freeze and cells == [cell]
        assert kw["prepare_fn"] is prepare_cell
        assert kw["contract"] is contract
        assert kw["verified_calibration"] is calibration
        assert kw["phase_marker_root"].is_absolute()
        assert kw["phase_marker_root"].is_dir()
        assert os.environ["CMAKE_PREFIX_PATH"] == os.pathsep.join(prefixes)
        forwarded = dict(admission=object(), build_context=object(), source_evidence=object(),
                         expected_materialization_descriptor=object(), expected_toolchain_manifest=object(),
                         ccbench_dir=str(tmp_path / "ccbench"))
        assert kw["build_fn"]("genome", **forwarded) is result
        assert builder.call_args.kwargs == dict(
            forwarded, dependency_prefix=";".join(prefixes),
            fetchcontent_base_dir=str(tmp_path), fetchcontent_dependency_receipt={
                "masstree_head": "a" * 40, "config_sha256": hashlib.sha256(config).hexdigest()},
            masstree_source_dir=sources["masstree"], mimalloc_source_dir=sources["mimalloc"],
            googletest_source_dir=sources["googletest"])
        if fails == "oracle":
            error = floor._FloorOraclePreflightError(
                "toolchain mismatch", detail_code="floor-toolchain-receipt-mismatch",
                origin="calibration:toolchain-binding", outcome="invalid-path")
            raise floor._persist_floor_oracle_preflight_failure(
                kw["phase_marker_root"], error, verified_compiler=None)
        if fails:
            raise RuntimeError("build failure")
        return {"cell": {}}

    monkeypatch.setattr(floor, "build_cells", build)
    writer = Mock(return_value={})
    monkeypatch.setattr(b4, "store_record", writer)
    kwargs = dict(store_root=tmp_path / "durable", output=tmp_path / "record.json", repo_root=tmp_path)
    if fails == "oracle":
        assert b4.main(["--store-root", str(kwargs["store_root"]),
                        "--output", str(kwargs["output"])]) == 1
        diagnostic, = kwargs["store_root"].glob("b4-build-*/phases/sort-swo-oracle-preflight-failure.json")
        stderr = capsys.readouterr().err
        assert str(diagnostic.resolve()) in stderr
        assert diagnostic.read_text() in stderr
        assert "floor-toolchain-receipt-mismatch" in stderr
        assert "sort-swo-oracle-infrastructure-unavailable" in stderr
        writer.assert_not_called()
    elif fails:
        with pytest.raises(RuntimeError, match="build failure"):
            b4.produce_record(**kwargs)
        writer.assert_not_called()
    else:
        b4.produce_record(**kwargs)
        writer.assert_called_once()
    expected_root = b4.ROOT if fails == "oracle" else tmp_path
    resolver.assert_called_once_with(root=expected_root)
    loader.assert_called_once_with(expected_root / "freeze.json", expected_hash="2" * 64)
    assert os.environ["CMAKE_PREFIX_PATH"] == "previous"


def test_dependency_commands_use_verified_and_hydrated_paths(tmp_path, monkeypatch):
    calls = []
    (tmp_path / "third-party").mkdir()
    for name in ("masstree", "mimalloc", "googletest"):
        (tmp_path / "third-party" / name).mkdir()
    def run(argv, **kw):
        calls.append(argv)
        assert kw["check"] is True and kw["timeout"] > 0
        names = ("masstree", "mimalloc", "googletest", "gflags", "glog")
        return SimpleNamespace(stdout=json.dumps({"sources": [
            {"name": name, "resolved_path": str(tmp_path / "third-party" / name)} for name in names]}))
    monkeypatch.setattr(b4.subprocess, "run", run)
    monkeypatch.setattr(b4.buildcache, "compilers_for_current_site", lambda: ("/cc", "/cxx"))
    prefixes, sources = b4.prepare_dependencies(tmp_path, cache_root=tmp_path / "cache")
    assert "hydrate" in calls[0]
    assert calls[0][-2:] == ["--cache-root", str(tmp_path / "cache")]
    assert calls[0][-4:] == ["--staging-root", str(tmp_path / "third-party"), "--cache-root", str(tmp_path / "cache")]
    assert len(calls) == 7
    assert calls[1][2] == str(tmp_path / "third-party" / "gflags")
    assert calls[4][2] == str(tmp_path / "third-party" / "glog")
    assert f"-DCMAKE_PREFIX_PATH={prefixes[0]}" in calls[4]
    assert "-DCMAKE_CXX_COMPILER=/cxx" in calls[1]
    assert "-DWITH_GTEST=OFF" in calls[4]
    assert prefixes == [str(tmp_path / "dependency-install")]
    assert f"-DCMAKE_INSTALL_PREFIX={prefixes[0]}" in calls[1]
    assert f"-DCMAKE_INSTALL_PREFIX={prefixes[0]}" in calls[4]
    for name in ("masstree", "mimalloc", "googletest"):
        assert sources[name] == str(tmp_path / "third-party" / f"{name}-src")
        assert Path(sources[name]).is_dir()


@pytest.mark.parametrize("operation", ["hydrate"])
@pytest.mark.parametrize("timeout", [False, True])
def test_helper_failure_retains_command_rc_and_output(tmp_path, monkeypatch, operation, timeout):
    monkeypatch.setattr(b4, "_install_dependency", lambda *a, **kw: None)
    monkeypatch.setattr(b4.buildcache, "compilers_for_current_site", lambda: ("/cc", "/cxx"))
    def run(command, **kwargs):
        if operation in command:
            if timeout:
                raise subprocess.TimeoutExpired(command, 120, output=b"partial", stderr=b"cause")
            raise subprocess.CalledProcessError(2, command, output="partial", stderr="cause")
        return SimpleNamespace(stdout=json.dumps({"sources": [
            {"name": name, "resolved_path": str(tmp_path / name)} for name in ("gflags", "glog")]}))
    monkeypatch.setattr(b4.subprocess, "run", run)
    with pytest.raises(RuntimeError) as caught:
        b4.prepare_dependencies(tmp_path, cache_root=tmp_path / "cache")
    message = str(caught.value)
    assert operation in message and "cause" in message and "partial" in message
    assert ("rc=None" if timeout else "rc=2") in message
    assert ("timeout=120" if timeout else "timeout=None") in message


def test_cli_rejects_non_compute_without_build(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(b4.site_policy, "current_site", lambda: b4.site_policy.OTHER)
    builder = Mock()
    monkeypatch.setattr(b4, "prepare_dependencies", builder)
    assert b4.main(["--output", str(tmp_path / "record.json")]) == 1
    builder.assert_not_called()
    assert "compute node" in capsys.readouterr().err


@pytest.mark.parametrize("previous", [None, "", "/original/bin"])
@pytest.mark.parametrize("fails", [False, True])
def test_cli_path_prepend_and_restore(tmp_path, monkeypatch, previous, fails):
    if previous is None:
        monkeypatch.delenv("PATH", raising=False)
    else:
        monkeypatch.setenv("PATH", previous)
    directories = [tmp_path / "first", tmp_path / "second"]
    for directory in directories:
        directory.mkdir()
        tool = directory / "cmake"
        tool.write_text("#!/bin/sh\nexit 0\n")
        tool.chmod(0o700)
    observed = []
    def produce(**kwargs):
        observed.append(os.environ["PATH"])
        assert shutil.which("cmake") == str(directories[0] / "cmake")
        if fails:
            raise RuntimeError("build failure")
    monkeypatch.setattr(b4, "produce_record", produce)
    argv = ["--output", str(tmp_path / "record.json")]
    for directory in directories:
        argv += ["--path-prepend", str(directory)]
    assert b4.main(argv) == (1 if fails else 0)
    assert observed == [os.pathsep.join(
        [str(directory) for directory in directories]
        + ([] if previous is None else [previous]))]
    assert os.environ.get("PATH") == previous


@pytest.mark.parametrize("is_file", [False, True])
def test_cli_path_prepend_rejects_invalid_before_start(tmp_path, monkeypatch, capsys, is_file):
    invalid = tmp_path / "invalid"
    if is_file:
        invalid.write_text("not a directory")
    previous = os.environ.get("PATH")
    producer = Mock()
    monkeypatch.setattr(b4, "produce_record", producer)
    assert b4.main(["--output", str(tmp_path / "record.json"),
                    "--path-prepend", str(invalid)]) == 1
    producer.assert_not_called()
    assert "requires an existing directory" in capsys.readouterr().err
    assert os.environ.get("PATH") == previous


@pytest.fixture
def placement(runtime, tmp_path):
    record = publish(runtime, tmp_path)
    repo = tmp_path / "checkout"
    repo.mkdir()
    return record, dict(source_root=tmp_path, repo_root=repo, env_tag="pegasus")


def test_place_external_source_exact_path_bytes_and_execute(placement):
    record, kwargs = placement
    repo = kwargs["repo_root"]
    assert not (repo / "output").exists()
    assert not (kwargs["source_root"] / record["store_path"]).is_relative_to(repo)
    relpath = b4.place_record(record, **kwargs)
    assert relpath == f"output/env/pegasus/binaries/{record['binary_sha256']}"
    binary = b4.floor_pair_driver._resolve_regular(repo, relpath, label="placed binary")
    assert binary.is_file() and not binary.is_symlink()
    assert os.access(binary, os.X_OK)
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == record["binary_sha256"]


def test_place_idempotent(placement):
    record, kwargs = placement
    first = b4.place_record(record, **kwargs)
    binary = kwargs["repo_root"] / first
    before = binary.read_bytes()
    assert b4.place_record(record, **kwargs) == first
    assert binary.read_bytes() == before


def test_place_rejects_source_symlink(placement):
    record, kwargs = placement
    source = kwargs["source_root"] / record["store_path"]
    real = source.with_name("real-binary")
    source.rename(real)
    source.symlink_to(real)
    with pytest.raises(b4.floor_pair_driver.FloorPairBindingError, match="symlink"):
        b4.place_record(record, **kwargs)
    assert not (kwargs["repo_root"] / "output").exists()


def test_place_rejects_missing_binary_key(placement, monkeypatch):
    record, kwargs = placement
    del record["binary"]
    store = Mock(wraps=floor.store_binaries)
    monkeypatch.setattr(floor, "store_binaries", store)
    with pytest.raises(KeyError) as caught:
        b4.place_record(record, **kwargs)
    assert caught.value.args == ("binary",)
    store.assert_not_called()
    assert "binary" not in record
    assert not (kwargs["repo_root"] / "output").exists()


def test_place_returns_canonical_repo_relative_path(placement):
    record, kwargs = placement
    relpath = b4.place_record(record, **kwargs)
    assert not Path(relpath).is_absolute()
    assert b4.floor_pair_driver._relative_path(relpath, label="binary_relpath") == relpath


def test_place_preserves_original_record(placement):
    record, kwargs = placement
    before = json.dumps(record, ensure_ascii=True)
    b4.place_record(record, **kwargs)
    assert json.dumps(record, ensure_ascii=True) == before


def test_place_trace_elf_rejected_by_consumer(tmp_path):
    # Construct a trace-bearing ELF and a matching reader fixture from the start.
    # This is not a build admission issuance or a repaired corruption negative.
    record = _honest_portable_built_record(tmp_path, configuration_id="stock_common")["cell"]
    source = tmp_path / "trace.cc"
    source.write_text('extern "C" int izanagi_trace_probe() { return 0; }\n'
                      'int main() { return izanagi_trace_probe(); }\n')
    binary = tmp_path / "trace-elf"
    subprocess.run(["g++", "-O0", str(source), "-o", str(binary)],
                   check=True, capture_output=True, timeout=60)
    assert binary.read_bytes()[:4] == b"\x7fELF"
    sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    record.update(binary="trace-elf", store_path="trace-elf",
                  binary_sha256=sha, bin_hash_short=sha[:16])
    receipt = record["admission_receipt"]
    receipt["subject"]["binary_sha256"] = sha
    receipt["proof"]["source_protection"]["binary_sha256"] = sha
    del receipt["receipt_sha256"]
    receipt["receipt_sha256"] = hashlib.sha256(json.dumps(
        receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("utf-8")).hexdigest()
    repo = tmp_path / "checkout"
    repo.mkdir()
    relpath = b4.place_record(record, source_root=tmp_path, repo_root=repo, env_tag="pegasus")
    placed = b4.floor_pair_driver._resolve_regular(repo, relpath, label="trace binary")
    assert hashlib.sha256(placed.read_bytes()).hexdigest() == sha
    with pytest.raises(RuntimeError, match="izanagi_trace シンボルが漏れている"):
        b4.buildcache._assert_no_trace_symbols(str(placed))


def test_place_binary_is_git_ignored_and_untracked(placement):
    record, kwargs = placement
    repo = kwargs["repo_root"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    shutil.copyfile(b4.ROOT / ".gitignore", repo / ".gitignore")
    relpath = b4.place_record(record, **kwargs)
    ignored = subprocess.run(["git", "-C", str(repo), "check-ignore", "--", relpath],
                             check=True, capture_output=True, text=True)
    assert ignored.stdout.strip() == relpath
    subprocess.run(["git", "-C", str(repo), "add", "-A"],
                   check=True, capture_output=True)
    tracked = subprocess.run(["git", "-C", str(repo), "ls-files", "--", relpath],
                             check=True, capture_output=True, text=True)
    assert tracked.stdout == ""


def test_place_cli_success_and_failure(placement, tmp_path):
    record, kwargs = placement
    argv = [sys.executable, "-m", "orchestrator.campaign.b4_binary_record", "place",
            "--record", str(tmp_path / "record.json"),
            "--source-root", str(kwargs["source_root"]),
            "--repo-root", str(kwargs["repo_root"]), "--env-tag", kwargs["env_tag"]]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"output/env/pegasus/binaries/{record['binary_sha256']}\n"
    (kwargs["source_root"] / record["store_path"]).unlink()
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    assert result.returncode != 0
    assert result.stdout == ""


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
