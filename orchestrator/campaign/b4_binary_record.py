"""Build one stock binary for the B-4 identical candidate/reference pair.
Run through the existing generic dispatcher on Pegasus compute. Record paths
are relative to --store-root, which must remain available to consumers.
This CLI performs no measurement or spec issuance.
PATH prepends select the calibrated tools without relaxing toolchain matching.
"""
from __future__ import annotations

import argparse
from functools import partial
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

from orchestrator.campaign import buildcache, env_attestation, floor_pair_driver, site_policy
from orchestrator.campaign import s8b_binary_admission as admission
from orchestrator.campaign import s8b_floor_campaign as floor
from orchestrator.campaign.s1_direct_comparison import prepare_cell

ROOT = Path(__file__).resolve().parents[2]


def select_cell(freeze, protocol, holdout_id=None):
    """Choose the first enumerated stock cell, or the named stock holdout."""
    stock = protocol["stock_configuration"]
    cells = floor.enumerate_cells(freeze, stock_configuration=stock)
    for cell in cells:
        if (cell["configuration_id"] == stock
                and (holdout_id is None or cell["holdout_id"] == holdout_id)):
            return cell
    raise ValueError(f"no stock cell for holdout_id={holdout_id!r}")


def _install_dependency(source, work, prefix, *, cc, cxx, prefixes, glog):
    """Install policy-verified gflags/glog; produces no CCBench binary."""
    configure = [
        "cmake", "-S", str(source), "-B", str(work),
        "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        f"-DCMAKE_INSTALL_PREFIX={prefix}",
        f"-DCMAKE_C_COMPILER={cc}", f"-DCMAKE_CXX_COMPILER={cxx}",
    ]
    if glog:
        configure += ["-DWITH_GTEST=OFF", "-DBUILD_TESTING=OFF",
                      "-DWITH_UNWIND=OFF", f"-DCMAKE_PREFIX_PATH={prefixes}"]
    else:
        configure += ["-DREGISTER_INSTALL_PREFIX=OFF"]
    for command in (
        configure,
        ["cmake", "--build", str(work), "-j", str(site_policy.available_cpus())],
        ["cmake", "--install", str(work)],
    ):
        subprocess.run(command, check=True, timeout=120)


def _helper_failure(exc):
    return (f"helper command={exc.cmd!r} rc={getattr(exc, 'returncode', None)!r} "
            f"timeout={getattr(exc, 'timeout', None)!r} "
            f"stdout={exc.stdout!r} stderr={exc.stderr!r}")


def prepare_dependencies(work, *, repo_root=ROOT, cache_root=None):
    """Hydrate all five pinned source inputs before building dependencies."""
    helper = repo_root / "tools/pegasus/fetch_third_party.py"
    work = Path(work).resolve()
    configured_cache = cache_root or os.environ.get("IZANAGI_PEGASUS_THIRDPARTY_CACHE")
    if configured_cache is None:
        raise ValueError("cache root is required via --cache-root or IZANAGI_PEGASUS_THIRDPARTY_CACHE")
    cache_root = Path(configured_cache).resolve()
    base = [sys.executable, str(helper)]
    command = base + ["hydrate", "--repo-root", str(repo_root),
                      "--staging-root", str(work / "third-party")]
    command += ["--cache-root", str(cache_root)]
    try:
        hydrated = json.loads(subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=300,
        ).stdout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(_helper_failure(exc)) from exc
    third_party = {item["name"]: item["resolved_path"] for item in hydrated["sources"]}
    cc, cxx = buildcache.compilers_for_current_site()
    prefix = work / "dependency-install"
    prefixes = [str(prefix)]
    for name in ("gflags", "glog"):
        _install_dependency(
            third_party[name], work / f"{name}-build", prefix,
            cc=cc, cxx=cxx, prefixes=";".join(prefixes), glog=name == "glog",
        )
    # buildcache resolves these exact names under FETCHCONTENT_BASE_DIR.
    for name in ("masstree", "mimalloc", "googletest"):
        destination = work / "third-party" / f"{name}-src"
        source = Path(third_party[name])
        if source != destination:
            source.rename(destination)
        third_party[name] = str(destination)
    return prefixes, third_party


def _build_with_dependencies(genome, *, prefixes, sources, admission,
                             build_context, source_evidence, **kwargs):
    # Prebuild using the production-bound toolchain, then observe real config.h
    # and Git HEAD; hydration alone cannot supply the dependency receipt.
    base = str(Path(sources["masstree"]).parent)
    source_kwargs = {f"{name}_source_dir": sources[name]
                     for name in ("masstree", "mimalloc", "googletest")}
    buildcache.prepare_masstree_fetchcontent(
        ccbench_dir=kwargs["ccbench_dir"], fetchcontent_base_dir=base,
        expected_toolchain_manifest=kwargs["expected_toolchain_manifest"],
        configure_timeout_s=120, target_timeout_s=300,
        dependency_prefix=";".join(prefixes), **source_kwargs,
    )
    receipt = buildcache._observe_fetchcontent_dependency_receipt(sources["masstree"])
    # Preserve production admission/toolchain/descriptor arguments and result.
    return buildcache.build_v2(
        genome, admission=admission, build_context=build_context,
        source_evidence=source_evidence, dependency_prefix=";".join(prefixes),
        fetchcontent_base_dir=base, fetchcontent_dependency_receipt=receipt,
        **source_kwargs, **kwargs,
    )


def store_record(built, cell_id, *, store_root, output, pin, contract_sha256):
    """Use real store/projection/validation before create-only publication."""
    floor.store_binaries(
        built, store_root / "binaries", out_root=store_root,
        expected_ccbench_pin=pin, expected_contract_sha256=contract_sha256,
    )
    # Consumers use the durable copy even after build-cache housekeeping.
    durable = Path(built[cell_id]["store_path"])
    durable.chmod(stat.S_IMODE(durable.stat().st_mode) | stat.S_IXUSR)
    built[cell_id]["binary"] = str(durable)
    record = floor.project_built_records(
        built, out_root=store_root, expected_ccbench_pin=pin,
        expected_contract_sha256=contract_sha256,
    )[cell_id]
    admission.validate_portable_binary_record(record, expected_policy=None)
    payload = json.dumps(record, ensure_ascii=True, sort_keys=True,
                         indent=2, allow_nan=False) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(payload)
    return record


def place_record(record, *, source_root, env_tag, repo_root=ROOT) -> str:
    """Place procured bytes and return their canonical repository-relative path.

    source_root itself is resolved and trusted; only components beneath that
    root are checked for symlinks, and the source must be a regular file.
    The caller supplies the frozen spec's environment.env_tag; it is not
    cross-checked here. Restoration requires the receipt's current policy.
    """
    source_root = Path(source_root).resolve()
    source = floor_pair_driver._resolve_regular(
        source_root, floor_pair_driver._relative_path(
            record["store_path"], label="record.store_path"), label="source binary",
    )
    repo_root = Path(repo_root).resolve()
    destination_root = repo_root / "output" / "env" / env_tag / "binaries"
    destination = destination_root / record["binary_sha256"]
    record["binary"]  # Require the original key before replacing its path.
    placed = dict(record)
    placed["binary"] = str(source)
    placed["store_path"] = str(destination)
    receipt = record["admission_receipt"]
    floor.store_binaries(
        {record["cell_id"]: placed}, destination_root, out_root=repo_root,
        expected_ccbench_pin=receipt["admission"]["source"]["ccbench_commit"],
        expected_contract_sha256=receipt["subject"]["contract_sha256"],
    )
    destination.chmod(stat.S_IMODE(destination.stat().st_mode) | stat.S_IXUSR)
    return destination.relative_to(repo_root).as_posix()


def produce_record(*, store_root, output, holdout_id=None, cache_root=None,
                   repo_root=ROOT):
    if not site_policy.is_pegasus_compute(site_policy.current_site()):
        raise RuntimeError("B-4 binary build requires a Pegasus compute node")
    if os.path.lexists(output):
        raise FileExistsError(output)
    protocol = floor.resolve_current_floor_protocol(root=repo_root).document
    protocol, contract = floor._validate_protocol_against_current(protocol)
    freeze_path = Path(protocol["freeze"]["path"])
    if not freeze_path.is_absolute():
        freeze_path = repo_root / freeze_path
    freeze = floor._load_verified_freeze(
        freeze_path, expected_hash=protocol["freeze"]["sha256"],
    ).document
    cell = select_cell(freeze, protocol, holdout_id)
    calibration = env_attestation.load_verified_calibration(contract, repo_root)
    store_root = Path(store_root).resolve()
    store_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="b4-build-", dir=store_root))
    markers = work / "phases"
    markers.mkdir()
    prefixes, sources = prepare_dependencies(work, repo_root=repo_root, cache_root=cache_root)
    previous = os.environ.get("CMAKE_PREFIX_PATH")
    os.environ["CMAKE_PREFIX_PATH"] = os.pathsep.join(prefixes)
    try:
        built = floor.build_cells(
            freeze, [cell], ccbench_pin=protocol["ccbench_pin"],
            out_root=work, prepare_fn=prepare_cell, contract=contract,
            verified_calibration=calibration, phase_marker_root=markers,
            repo_root=repo_root,
            build_fn=partial(_build_with_dependencies, prefixes=prefixes, sources=sources),
        )
    except floor.SortSwoOracleUnavailable as exc:
        exc.b4_diagnostic_path = markers / floor._FLOOR_PREFLIGHT_FAILURE_FILENAME
        raise
    finally:
        if previous is None:
            os.environ.pop("CMAKE_PREFIX_PATH", None)
        else:
            os.environ["CMAKE_PREFIX_PATH"] = previous
    return store_record(
        built, cell["cell_id"], store_root=store_root, output=Path(output),
        pin=protocol["ccbench_pin"], contract_sha256=contract.contract_sha256,
    )


def placement_main(argv=None):
    parser = argparse.ArgumentParser(
        description="Place an existing portable binary record in a checkout.",
        epilog="測定を投入する担当が、投入前に、使用する各 checkout へ配置する",
    )
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--env-tag", required=True,
                        help="caller must match frozen spec environment.env_tag; not checked here")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        relpath = place_record(record, source_root=args.source_root,
                               env_tag=args.env_tag, repo_root=args.repo_root)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(f"b4-binary-record: {exc}", file=sys.stderr)
        return 1
    print(relpath)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["place"]:
        return placement_main(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="create-only destination for one portable JSON record")
    parser.add_argument("--store-root", type=Path,
                        default=Path.home() / ".local/share/izanagi/b4-binaries",
                        help="durable binary root; record paths are relative to this root")
    parser.add_argument("--holdout-id")
    parser.add_argument("--cache-root", type=Path, help="verified third-party source cache")
    parser.add_argument("--path-prepend", type=Path, action="append", default=[],
                        help="prepend an existing tool directory to PATH (repeatable, in argument order)")
    args = parser.parse_args(argv)
    previous_path = os.environ.get("PATH")
    try:
        directories = [path.resolve() for path in args.path_prepend]
        for path in directories:
            if not path.is_dir():
                raise ValueError(f"--path-prepend requires an existing directory: {path}")
        if directories:
            os.environ["PATH"] = os.pathsep.join(
                [str(path) for path in directories]
                + ([] if previous_path is None else [previous_path]))
        del args.path_prepend
        produce_record(**vars(args))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"b4-binary-record: {exc}", file=sys.stderr)
        diagnostic_path = getattr(exc, "b4_diagnostic_path", None)
        if diagnostic_path is not None:
            print(f"b4-binary-record: diagnostic file: {diagnostic_path}", file=sys.stderr)
            try:
                print(diagnostic_path.read_text(encoding="utf-8"), file=sys.stderr)
            except (OSError, UnicodeError) as diagnostic_error:
                print(f"b4-binary-record: cannot read diagnostic: {diagnostic_error}", file=sys.stderr)
        return 1
    finally:
        if previous_path is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = previous_path
    return 0


if __name__ == "__main__":
    sys.exit(main())
