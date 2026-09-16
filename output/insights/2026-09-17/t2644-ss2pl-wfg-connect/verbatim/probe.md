# probe 本体の逐語 (tools/t2644_wfg_probe.py、Codex role=author が段 5 + 段 6 fix 2 巡で作成、repo へは commit しない。sha256 8ed60cbaf3b89684cd919272c9b8c0e11652a23fb35297249ff3b113b6734587、16,218 bytes)

```python
#!/usr/bin/env python3.10
"""Single production phase1 trial; selftest uses synthetic stdout only.

この probe は D790 の inert 性を証明しない。
plain の不在性は condition gate を通していない (stock 対照の既存不整合のため)。
phase1 の plain も condition gate を通していない (依存閉包・argv の drift は patch の設計由来)。
study 全体 (controls mode) の代用ではない。
Run with python3.10 -B; retain scratch and receipts for the parent to inspect.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import time
from uuid import uuid4


def load_driver(repo_root):
    path = repo_root / "tools/pegasus/run_ss2pl_lock_study.py"
    spec = importlib.util.spec_from_file_location("ss2pl_lock_study_driver", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load runner: {path}")
    driver = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = driver
    spec.loader.exec_module(driver)
    return driver


def synthetic_stdout(*, held_locks=True):
    """Synthetic serializer-shaped fixture, not output from a C++ run."""
    lines = [
        "#ShowOptParameters(): ADD_ANALYSIS 0: BACK_OFF 1: DLR0 : "
        "SS2PL_LOCK_IMPL 1: SS2PL_LOCK_KIND 0: SS2PL_DLR 0: "
        "SS2PL_WFG_DIAG 1: MASSTREE_USE 1: KEY_SIZE 8: KEY_SORT 0: VAL_SIZE 8",
        "#FLAGS_ycsb_tuple_num:\t100",
        "#FLAGS_ycsb_rratio:\t50",
        "#FLAGS_ycsb_rmw:\t0",
        "#FLAGS_ycsb_zipf_skew:\t0",
        "#FLAGS_ycsb_max_ope:\t10",
    ]
    for tick in (1, 2, 3):
        nodes = [
            {"thread_id": 0, "attempt": 7, "wait_lock_id": "0x20",
             "request_mode": "write", "commit_count": 6, "abort_count": 0,
             "held_locks": [{"lock_id": "0x10", "mode": "write"}]},
            {"thread_id": 1, "attempt": 9, "wait_lock_id": "0x10",
             "request_mode": "write", "commit_count": 8, "abort_count": 0,
             "held_locks": [{"lock_id": "0x20", "mode": "write"}]},
        ]
        if not held_locks:
            for node in nodes:
                del node["held_locks"]
        event = {
            "schema": "ss2pl-wfg/v2", "event": "wfg_snapshot", "tick": tick,
            "cycle_found": True, "conflict_count": 2, "no_wait_failure_count": 0,
            "nodes": nodes,
            "edges": [
                {"waiter_thread_id": 0, "holder_thread_id": 1,
                 "lock_id": "0x20", "request_mode": "write",
                 "holder_mode": "write", "compatible": False},
                {"waiter_thread_id": 1, "holder_thread_id": 0,
                 "lock_id": "0x10", "request_mode": "write",
                 "holder_mode": "write", "compatible": False},
            ],
        }
        lines.append(json.dumps(event, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def selftest(driver):
    passed = True
    for present in (True, False):
        name = "held_locks_positive" if present else "missing_held_locks_negative"
        try:
            events = driver._json_events(synthetic_stdout(held_locks=present))
            snapshots = driver._extract_snapshots(events)
            result = driver.validate_deadlock_evidence(snapshots, timed_out=True)
            if present:
                ok = result is not None and result["snapshot_indexes"] == [0, 1, 2]
            else:
                ok = result is None
            detail = (f"snapshot_indexes={result['snapshot_indexes']}"
                      if result is not None else "accepted_cycle=None")
            print(f"{name}: {'PASS' if ok else 'FAIL'} {detail}")
        except Exception as exc:
            ok = False
            print(f"{name}: FAIL {type(exc).__name__}: {exc}")
        passed = passed and ok
    return 0 if passed else 1


def discover_pbs_jobid(repo_root, hostname):
    jobid = os.environ.get("PBS_JOBID")
    if jobid:
        return jobid, {"kind": "environment", "key": "PBS_JOBID"}
    candidates = []
    for path in (repo_root / "output/pegasus-dispatch").glob("*/compute-visible.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if (isinstance(record, dict)
                    and record.get("schema_version") == "pegasus-compute-visible/v1"
                    and record.get("hostname") == hostname
                    and isinstance(record.get("pbs_jobid"), str)
                    and record["pbs_jobid"]):
                candidates.append((path.stat().st_mtime_ns, str(path), record["pbs_jobid"]))
        except (OSError, ValueError):
            continue
    if candidates:
        mtime, path, jobid = max(candidates)
        return jobid, {"kind": "compute-visible", "path": path, "mtime_ns": mtime}
    return "unknown", {"kind": "unknown"}


@contextmanager
def stage(document, name):
    document["stage"] = name
    started = time.monotonic()
    try:
        yield
    finally:
        document["stage_seconds"][name] = time.monotonic() - started


def write_result(output, document):
    # Serialize first so a bad value cannot leave a partial receipt or temp file.
    json.dumps(document, allow_nan=False)
    temporary = output.with_name(f".{output.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(document, handle, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def run(args, hostname):
    document = {
        "schema": "t2644-wfg-probe/v1", "hostname": hostname,
        "stage": "inputs", "stage_seconds": {}, "status": "running",
        "scratch_root": str(args.scratch_root), "scratch_path": None,
        "inputs": {key: str(value) if isinstance(value, Path) else value
                   for key, value in vars(args).items()},
    }
    output = args.output.absolute()
    cache = None
    rc = 0
    try:
        with stage(document, "inputs"):
            repo_root = args.repo_root.resolve(strict=True)
            output = args.output.resolve()
            paths = {name: getattr(args, name).resolve(strict=True) for name in
                     ("patch", "gflags_prefix", "glog_prefix", "thirdparty_root")}
            scratch_root = args.scratch_root.resolve()
            document["scratch_root"] = str(scratch_root)
            document["inputs"].update({key: str(value) for key, value in paths.items()})
            document["inputs"].update(repo_root=str(repo_root),
                                      scratch_root=str(scratch_root), output=str(output))
            if args.clocks_per_us <= 0 or not 1 <= args.jobs <= 48:
                raise ValueError("clocks-per-us must be positive; jobs must be in 1..48")
        with stage(document, "import_driver"):
            driver = load_driver(repo_root)
            for name, path in {
                "patch": paths["patch"], "probe": Path(__file__).resolve(),
                "runner": repo_root / "tools/pegasus/run_ss2pl_lock_study.py",
                "policy": repo_root / "tools/pegasus/policy.json",
            }.items():
                document["inputs"][name] = str(path)
                document["inputs"][f"{name}_sha256"] = driver.sha256_file(path)
        with stage(document, "pbs_jobid"):
            jobid, source = discover_pbs_jobid(repo_root, hostname)
            document.update(pbs_jobid=jobid, pbs_jobid_source=source)
        with stage(document, "required_commands"):
            document["required_commands"] = driver.validate_required_commands()
        with stage(document, "thirdparty"):
            policy = json.loads((repo_root / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
            document["thirdparty"] = driver._validate_thirdparty(paths["thirdparty_root"], policy)
        with stage(document, "canonical"):
            canonical = driver.verify_canonical_submodule(repo_root)
            document["canonical"] = canonical
        with stage(document, "scratch"):
            attempt_id = f"t2644-{uuid4().hex}"
            attempt_root = scratch_root / attempt_id
            document["scratch_path"] = str(attempt_root)
            attempt_root.mkdir(parents=True)
            stock = attempt_root / "condition-gate-stock"
            clone = attempt_root / "ccbench"
            build_root = attempt_root / "builds"
            build_root.mkdir()
        with stage(document, "clone_stock"):
            driver.clone_network_free(Path(canonical["path"]), stock)
            document["clone_stock"] = str(stock)
        with stage(document, "clone_patched"):
            driver.clone_network_free(Path(canonical["path"]), clone)
            document["clone_patched"] = str(clone)
        with stage(document, "apply_patch"):
            driver._apply_patch(clone, paths["patch"], reverse=False)
            document["patch_applied"] = True
        with stage(document, "abort_ownership"):
            document["abort_counter_ownership"] = driver.validate_abort_counter_ownership(clone)
        patch_sha256 = document["inputs"]["patch_sha256"]
        source_sha = driver._sha256_bytes(f"patched\0{canonical['head']}\0{patch_sha256}".encode())
        document["patched_source_state_sha256"] = source_sha
        cache = driver.PreprocessCache()
        configure_args = {key: paths[key] for key in
                          ("gflags_prefix", "glog_prefix", "thirdparty_root")}
        configure_args["backoff"] = 1
        common = dict(configure_args, jobs=args.jobs, preprocess_cache=cache,
                      source_state_sha256=source_sha)

        def plain_build(arm, build_id):
            p_build = build_root / f"{build_id}-plain"
            expected = driver._configure(clone, p_build, arm=arm, **configure_args)
            driver._run_checked(
                ["cmake", "--build", str(p_build), "--target", "ycsb_ss2pl.exe",
                 "--parallel", str(args.jobs)], timeout=1800)
            binary = driver._find_binary(p_build, "ycsb_ss2pl.exe")
            entries = driver._target_compile_entries(p_build, "ycsb_ss2pl.exe")
            definitions = driver._validate_compile_definitions(entries, expected)
            observed = driver._cmake_cache(p_build / "CMakeCache.txt")
            return {
                "build_id": build_id, "arm": arm, "backoff": 1,
                "requested_cache": expected,
                "observed_cache": {key: observed[key] for key in expected},
                "compile_definitions": definitions, "binary": str(binary),
                "binary_sha256": driver.sha256_file(binary), "target": "ycsb_ss2pl.exe",
            }, entries

        if args.warm_masstree:
            with stage(document, "warm_masstree"):
                warm = build_root / "warmup"
                document["warm_masstree"] = {"build_dir": str(warm)}
                try:
                    driver._configure(clone, warm, arm="phase1", **configure_args)
                    driver._run_checked(
                        ["cmake", "--build", str(warm), "--target", "masstree_build",
                         "--parallel", str(args.jobs)], timeout=1200)
                finally:
                    masstree = paths["thirdparty_root"] / "masstree"
                    document["warm_masstree"].update(
                        config_h_exists_after=(masstree / "config.h").is_file(),
                        archive_exists_after=(masstree / "libkohler_masstree_json.a").is_file())
        if args.absence_mode != "none":
            with stage(document, "absence_S"):
                record = {"mode": args.absence_mode}
                document["absence_S"] = record
                try:
                    if args.absence_mode == "gate":
                        record.update(driver.build_target(
                            clone, stock, build_root, build_id="S", arm="S", **common))
                    else:
                        record["condition_gates"] = (
                            "skipped: stock-tree owner TU unresolved (pre-existing, see facts)")
                        plain_record, entries = plain_build("S", "S")
                        record.update(plain_record)
                        record["wfg_absence"] = driver._wfg_absence_evidence(
                            Path(record["binary"]), entries, preprocess_cache=cache,
                            source_state_sha256=source_sha)
                except Exception as exc:
                    record["error"] = {"type": type(exc).__name__, "message": str(exc)}
                    if args.absence_mode == "plain":
                        rc = 1
        with stage(document, "build_phase1"):
            if args.phase1_mode == "gate":
                document["build_phase1"] = driver.build_target(
                    clone, stock, build_root, build_id="phase1", arm="phase1",
                    target="ycsb_ss2pl.exe", **common)
            else:
                document["build_phase1"], _ = plain_build("phase1", "phase1")
                document["build_phase1"]["condition_gates"] = (
                    "skipped: dependency-closure-drift / compile-command-drift "
                    "(pre-existing, see facts)")
        with stage(document, "trial"):
            document["trial"] = driver._run_phase_trial(
                phase="phase1", build=document["build_phase1"],
                workload={**driver.WORKLOAD_DEFAULT, "ycsb_tuple_num": 100, "ycsb_zipf_skew": 0},
                trial=0, point="high-contention", clocks_per_us=args.clocks_per_us,
                occasion={"occasion_id": attempt_id, "pbs_jobid": jobid, "node": hostname})
        # Completion means the validator returned a verdict, even if no cycle was observed.
        document.update(status="error" if rc else "completed", stage="completed")
    except Exception as exc:
        document["error"] = {"type": type(exc).__name__, "message": str(exc),
                             "stage": document["stage"]}
        document["status"] = "error"
        rc = 1
    if cache is not None:
        document["preprocess_cache"] = cache.summary()
    try:
        write_result(output, document)
    except Exception as exc:
        print(f"receipt write failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(json.dumps(document, sort_keys=True), file=sys.stderr)
        return 1
    print(f"probe: {document['status']} output={output}")
    return rc


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    for name in ("patch", "scratch-root", "gflags-prefix", "glog-prefix",
                 "thirdparty-root", "output"):
        parser.add_argument(f"--{name}", type=Path)
    parser.add_argument("--clocks-per-us", type=int, default=2100)
    parser.add_argument("--jobs", type=int, default=48)
    parser.add_argument("--absence-mode", choices=("gate", "plain", "none"), default="plain")
    parser.add_argument("--phase1-mode", choices=("gate", "plain"), default="plain")
    parser.add_argument("--no-warm-masstree", dest="warm_masstree", action="store_false")
    parser.add_argument("--selftest", action="store_true")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        try:
            return selftest(load_driver(args.repo_root))
        except Exception as exc:
            print(f"selftest: FAIL {type(exc).__name__}: {exc}")
            return 1
    hostname = socket.gethostname()
    if not hostname.startswith("bnode"):
        print(f"login では走らせない: hostname={hostname} (bnode required)", file=sys.stderr)
        return 2
    missing = [f"--{name.replace('_', '-')}" for name in
               ("patch", "scratch_root", "gflags_prefix", "glog_prefix", "thirdparty_root", "output")
               if getattr(args, name) is None]
    if missing:
        parser.error("required for a live run: " + ", ".join(missing))
    return run(args, hostname)


if __name__ == "__main__":
    sys.exit(main())
```
