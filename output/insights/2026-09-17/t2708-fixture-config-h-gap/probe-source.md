# probe 本体の逐語 (tools/t2708_fixture_gap_probe.py、repo へは残さない)

- 作成: Codex `role=author` (段 5、361 行) + Codex fix 子 (段 6、415 行)。親は編集していない。
- 保全先: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2708-fixture-config-h-gap/probe/tools/t2708_fixture_gap_probe.py`
- sha256: `8c8731cd2b9a49748bf7a0be5c9cec25245a1e040f031667e29c9219f30e581f` (415 行)。run2 はこの bytes で走った。
- run1 は fix 前の版 (sha256 `0becf77c803924fed2aa1f135ec66e9ee4b9ee16c2a9bb007dd0a8e429286cab`、361 行) で走り、growth hold の import 拒否で 6 秒 rc=1 だった。

```python
"""Disposable T-2708 probe. Full measurements belong on compute nodes.

Run with python3 -B -m tools.t2708_fixture_gap_probe. Never commit this file.
Durations are perf_counter_ns wall times, including Git subprocess startup.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import statistics
import subprocess
import sys
from time import perf_counter_ns

CONFIG = "orchestrator/tests/fixtures/sort_swo_masstree/config.h"
LIMITATIONS = [
    "発行 A/B ではない (B index は staged addition で M:1833 の clean 条件を満たさない)。",
    "取り込み費用の A index は commit 後で採用位置と cache 状態が違う。",
    "所要モデル「取り込み + 13 × scan 差」は部分モデル。",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def git_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    return env


def git(root, *args, data=None):
    return subprocess.run(["git", *args], cwd=root, input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=git_env(), check=False)


def checked_git(root, *args):
    result = git(root, *args)
    if result.returncode:
        raise RuntimeError(f"git {args}: rc={result.returncode}: "
                           + result.stderr.decode("utf-8", "replace"))
    return result.stdout


def regular_index(root):
    paths = set()
    for entry in checked_git(root, "ls-files", "-z", "-s").split(b"\0"):
        if not entry:
            continue
        meta, relative = entry.split(b"\t", 1)
        mode, _oid, stage = meta.split()
        if stage != b"0":
            raise ValueError("unmerged index entry")
        if mode in (b"100644", b"100755"):
            paths.add(os.fsdecode(relative))
        elif mode not in (b"120000", b"160000"):
            raise ValueError(f"unknown index mode: {mode!r}")
    return paths


def require(condition, failures, check, **details):
    if not condition:
        failures.append({"check": check, **details})
    return bool(condition)


def force_add(root, payload, failures, label):
    """Transfer exact NUL bytes, recording missing paths without dropping them."""
    missing = [os.fsdecode(p) for p in payload.split(b"\0")
               if p and not (root / os.fsdecode(p)).exists()]
    require(not missing, failures, label + ": missing paths", paths=missing)
    start = perf_counter_ns()
    result = git(root, "add", "-f", "--pathspec-from-file=-",
                 "--pathspec-file-nul", data=payload)
    duration = perf_counter_ns() - start
    require(result.returncode == 0, failures, label + ": git add",
            rc=result.returncode, stderr=result.stderr.decode("utf-8", "replace"))
    return duration, result.returncode, missing


def comparison(actual, expected):
    return {"count": len(actual), "expected_minus_actual": sorted(expected - actual),
            "actual_minus_expected": sorted(actual - expected)}


def summary(values):
    if not values:
        return {"n": 0, "median_ns": None}
    # Inclusive linear interpolation; defined for one sample too.
    q1, _, q3 = (statistics.quantiles(values, n=4, method="inclusive")
                 if len(values) > 1 else [values[0]] * 3)
    return {"n": len(values), "median_ns": statistics.median(values),
            "q1_ns": q1, "q3_ns": q3, "iqr_ns": q3 - q1,
            "min_ns": min(values), "max_ns": max(values),
            "positive": sum(v > 0 for v in values),
            "negative": sum(v < 0 for v in values), "zero": sum(v == 0 for v in values)}


def add_summary(rows, fields):
    return {group: {field: summary([r[field] for r in selected if r["ok"]])
                    for field in fields}
            for group, selected in (("first", rows[:1]), ("repeated", rows[1:]))}


def fingerprint(path):
    payload = path.read_bytes()
    return {"sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}


def expected_paths(source, builder, migration):
    paths = set()
    for directory, dirs, files in os.walk(source / "orchestrator", followlinks=False):
        dirs[:] = [d for d in dirs if d != "__pycache__" and not d.endswith(".pyc")
                   and not (Path(directory) / d).is_symlink()]
        for name in files:
            p = Path(directory) / name
            if (name != "__pycache__" and not name.endswith(".pyc")
                    and p.is_file() and not p.is_symlink()):
                paths.add(p.relative_to(source).as_posix())
    paths |= builder._git_visible_output_paths(source)
    paths -= {migration.RECEIPT_REL, migration.DRAFT_REL}
    known = json.loads((source / migration.KNOWN_AXES_REL).read_text())
    basis = set()

    def collect(value):
        if isinstance(value, dict):
            if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                if not value["path"].startswith("external/ccbench/"):
                    basis.add(value["path"])
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(known)
    # Static projection of the builder's operational set, not volatile payloads.
    operational = {migration.KNOWN_AXES_REL, migration.HOLDOUT_REL,
                   "orchestrator/campaign/s1_known_axes_freeze.py",
                   "orchestrator/campaign/s8b_holdout_freeze.py",
                   "docs/phase3-8b-descriptor-design.md", migration.POSITIVE_CONTROL_PATH}
    return paths | basis | operational | {".gitmodules"}, basis, operational


def selftest(work, output):
    root = work / "selftest"
    root.mkdir()  # Never overwrite an earlier synthetic repository.
    checked_git(root, "init", "-q")
    checked_git(root, "config", "user.name", "T2708 synthetic selftest")
    checked_git(root, "config", "user.email", "t2708@example.invalid")
    (root / ".gitignore").write_text("/ignored.txt\n")
    (root / "ignored.txt").write_text("ignored\n")
    (root / "kept.txt").write_text("kept\n")
    checked_git(root, "add", "-A")
    checked_git(root, "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                "commit", "-q", "-m", "Synthetic probe selftest", "-m", "AI-Agent: none")
    failures = output["failures"]
    a = regular_index(root)
    require(a == {".gitignore", "kept.txt"}, failures, "selftest A membership", paths=sorted(a))
    saved = work / "selftest-index-A"
    shutil.copyfile(root / ".git/index", saved)
    force_add(root, b"ignored.txt\0", failures, "selftest ignored add")
    b = regular_index(root)
    require(b - a == {"ignored.txt"} and not a - b, failures, "selftest B difference")
    shutil.copyfile(saved, root / ".git/index")
    restored = regular_index(root)
    require(restored == a, failures, "selftest restored membership")
    expected_failures = []
    _, rc, missing = force_add(root, b"does-not-exist.txt\0", expected_failures, "selftest missing add")
    require(rc != 0 and missing == ["does-not-exist.txt"] and len(expected_failures) == 2,
            failures, "selftest missing add must record failure", rc=rc)
    output["selftest"] = {"A": sorted(a), "B": sorted(b), "restored": sorted(restored),
                          "expected_failures": expected_failures, "missing_add_rc": rc}


def hold_session(source, work, output):
    """Load the held module through normal enforcement, without running tests."""
    import pytest

    module_name = "orchestrator.tests.test_s8b_oracle_driver"
    module_path = source / "orchestrator/tests/test_s8b_oracle_driver.py"
    argv = [str(module_path), "--collect-only", "-q", "-p", "no:cacheprovider",
            "-k", "t2708_no_such_node_zzz"]
    record = {"argv": argv, "rc": None}
    output["hold_session"] = record
    failures = output["failures"]

    class LoadBuilder:
        def pytest_sessionstart(self, session):
            # pytest_configure has registered the enforcing session by now.
            # Collection can use a short name for non-package test directories;
            # keep the canonical name required by the probe in sys.modules too.
            import importlib

            importlib.import_module(module_name)

    start = perf_counter_ns()
    try:
        record["rc"] = int(pytest.main(argv, plugins=[LoadBuilder()]))
    except Exception as exc:
        failures.append({"check": "hold session exception", "type": type(exc).__name__,
                         "message": str(exc)})
    finally:
        record["elapsed_ns"] = perf_counter_ns() - start
        record["temp_environment"] = {key: os.environ.get(key)
                                      for key in ("TMPDIR", "TEMP", "TMP")}
        record["git_environment_keys"] = sorted(key for key in os.environ
                                                 if key.startswith("GIT_"))
        record["environment_preserved"] = (
            all(value == str(work / "tmp") for value in record["temp_environment"].values())
            and not record["git_environment_keys"])
        require(record["environment_preserved"], failures,
                "hold session changed sanitized environment")
    require(record["rc"] in (0, 5), failures, "hold session pytest rc", rc=record["rc"])
    builder = sys.modules.get(module_name)
    record["module_loaded"] = builder is not None
    module_file = getattr(builder, "__file__", None)
    record["module_file"] = str(Path(module_file).resolve()) if module_file else None
    require(record["module_loaded"], failures, "hold session module missing")
    require(record["module_file"] == str(module_path.resolve()), failures,
            "hold session module does not match source-root", actual=record["module_file"])
    return None if failures else builder


def measure(args, source, work, output):
    # Environment and sys.path are prepared before any orchestrator import.
    builder = hold_session(source, work, output)
    if builder is None:
        return
    from orchestrator.campaign import s8b_holdout_freeze as scanner
    from orchestrator.campaign import t080_freeze_migration as migration

    output["module_files"] = {m.__name__: str(Path(m.__file__).resolve())
                              for m in (builder, scanner, migration)}
    if builder.ROOT.resolve() != source:
        raise ValueError("builder ROOT does not match source-root")
    build = work / "build"
    build.mkdir()
    indexes = {state: work / f"index-{state}" for state in "AB"}
    if any(p.exists() or p.is_symlink() for p in indexes.values()):
        raise ValueError("saved indexes already exist; use a fresh work-root")
    start = perf_counter_ns()
    try:
        root, _, _ = builder._build_t080_stub_free_e2e_repo(build, issue_receipt=False)
    finally:
        output["builder_ns_reference_only"] = perf_counter_ns() - start
    output["fixture_root"] = str(root)
    index = root / ".git/index"
    shutil.copyfile(index, indexes["A"])
    a = regular_index(root)
    enumerated = set(scanner.enumerate_repository_files(root))
    report = scanner.search_repository(root)
    expected, basis, operational = expected_paths(source, builder, migration)
    # Default production scan excludes these prefixes. No files= injection.
    scan_paths = {p for p in enumerated if not any(
        p.startswith(prefix) for prefix in report["search"]["excluded_paths"])}
    output["sets"] = {"expected_count": len(expected), "basis_paths": sorted(basis),
                      "operational_paths": sorted(operational),
                      "A_index": comparison(a, expected),
                      "A_enumerated": comparison(enumerated, expected),
                      "A_scan": comparison(scan_paths, expected), "A_search": report["search"]}
    failures = output["failures"]
    require(CONFIG in expected - a, failures, "config.h must be missing from A index")
    require(len(scan_paths) == report["search"]["file_count"], failures, "scan projection count")
    general, hard = [], []
    output["add"] = {"general": general, "hard_code": hard,
                     "order": "general then hard-code each repeat; shared object cache",
                     "total_includes": "enumeration, path validation, add, Python bookkeeping"}
    for repeat in range(args.add_repeats):
        shutil.copyfile(indexes["A"], index)
        start = perf_counter_ns()
        listed = git(source, "ls-files", "-z", "-ci", "--exclude-standard", "--", "orchestrator", "output")
        enumeration_ns = perf_counter_ns() - start
        row = {"repeat": repeat, "enumeration_ns": enumeration_ns,
               "enumeration_rc": listed.returncode,
               "paths": [os.fsdecode(p) for p in listed.stdout.split(b"\0") if p]}
        general.append(row)
        if listed.returncode:
            require(False, failures, "source ignored enumeration", repeat=repeat,
                    stderr=listed.stderr.decode("utf-8", "replace"), rc=listed.returncode)
            row.update(ok=False, add_ns=None, total_ns=perf_counter_ns() - start)
        else:
            add_ns, rc, missing = force_add(root, listed.stdout, failures, f"general repeat {repeat}")
            row.update(add_ns=add_ns, total_ns=perf_counter_ns() - start,
                       add_rc=rc, missing_paths=missing, ok=rc == 0 and not missing)
            if row["ok"] and not indexes["B"].exists():
                shutil.copyfile(index, indexes["B"])
        shutil.copyfile(indexes["A"], index)
        start = perf_counter_ns()
        added = git(root, "add", "-f", "--", CONFIG)
        elapsed = perf_counter_ns() - start
        ok = require(added.returncode == 0, failures, "hard-code add", repeat=repeat,
                     rc=added.returncode, stderr=added.stderr.decode("utf-8", "replace"))
        hard.append({"repeat": repeat, "add_ns": elapsed, "rc": added.returncode, "ok": ok})
    output["add"]["general_summary"] = add_summary(general, ("enumeration_ns", "add_ns", "total_ns"))
    output["add"]["hard_code_summary"] = add_summary(hard, ("add_ns",))
    if not require(indexes["B"].exists(), failures, "no successful general B index"):
        return
    shutil.copyfile(indexes["B"], index)
    b = regular_index(root)
    output["sets"].update(B_index=comparison(b, expected), B_minus_A=sorted(b - a), A_minus_B=sorted(a - b))
    require(b == a | {CONFIG}, failures, "B index must equal A plus config.h")
    require(len(expected - b) == len(expected - a) - 1, failures, "expected deficit decreases by one")
    rows = []
    output["scan"] = {"pairs": rows, "difference": "B_ns - A_ns"}
    for pair in range(args.warmup + args.pairs):
        order = "AB" if pair % 2 == 0 else "BA"
        row = {"pair": pair, "warmup": pair < args.warmup, "order": order}
        rows.append(row)
        reports = {}
        for state in order:
            shutil.copyfile(indexes[state], index)
            start = perf_counter_ns()
            reports[state] = scanner.search_repository(root)
            row[state + "_ns"] = perf_counter_ns() - start
        row["difference_ns"] = row["B_ns"] - row["A_ns"]
        row["hashes"] = {s: migration._live_scan_sha256(r) for s, r in reports.items()}
        row["file_counts"] = {s: r["search"]["file_count"] for s, r in reports.items()}
        row["semantic_equal"] = {key: reports["A"][key] == reports["B"][key]
                                 for key in ("match_convention", "holdouts", "positive_control")}
        row["valid"] = require(all(row["semantic_equal"].values())
                               and row["hashes"]["A"] == row["hashes"]["B"]
                               and row["file_counts"]["B"] == row["file_counts"]["A"] + 1,
                               failures, "scan pair invariants", pair=pair)
    measured = [r for r in rows if not r["warmup"]]
    output["scan"]["summary"] = {field: summary([r[field] for r in measured])
                                  for field in ("A_ns", "B_ns", "difference_ns")}
    output["scan"]["by_order"] = {order: summary([r["difference_ns"] for r in measured if r["order"] == order])
                                   for order in ("AB", "BA")}
    output["scan"]["statistics_valid"] = all(r["valid"] for r in rows)
    shutil.copyfile(indexes["A"], index)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--pairs", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--add-repeats", type=int, default=10)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--hold-session-only", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = {"started_at": now(), "hostname": socket.gethostname(),
              "python_version": sys.version, "probe_file": str(Path(__file__).resolve()),
              "argv": sys.argv, "limitations": LIMITATIONS, "failures": [],
              "parameters": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}}
    destination = None
    try:
        source, work = args.source_root.resolve(), args.work_root.resolve()
        candidate = args.out.resolve()
        # Validate destinations before any mkdir; never write into the source.
        if not args.source_root.is_absolute() or not args.work_root.is_absolute():
            raise ValueError("source-root and work-root must be absolute")
        if work.is_relative_to(source) or source.is_relative_to(work):
            raise ValueError("work-root must be outside and not contain source-root")
        if not candidate.is_relative_to(work) or candidate == work:
            raise ValueError("out must be a file beneath work-root")
        destination = candidate
        if Path.cwd().resolve() != source:
            raise ValueError("cwd must equal source-root")
        if args.pairs < 1 or args.warmup < 0 or args.add_repeats < 1:
            raise ValueError("pairs/add-repeats must be positive; warmup must be nonnegative")
        for key in list(os.environ):
            if key.startswith("GIT_") or key == "PYTEST_XDIST_TESTRUNUID":
                del os.environ[key]
        temp = work / "tmp"
        if temp.resolve() != temp:
            raise ValueError("tmp must not be a symlink")
        temp.mkdir(parents=True, exist_ok=True)
        for key in ("TMPDIR", "TEMP", "TMP"):
            os.environ[key] = str(temp)
        sys.path.insert(0, str(source))
        sys.dont_write_bytecode = True
        output["source_head"] = checked_git(source, "rev-parse", "HEAD").decode().strip()
        output["git_version"] = checked_git(source, "--version").decode().strip()
        fixture_dir = Path(CONFIG).parent
        output["source_files"] = {str(p): fingerprint(source / p) for p in
                                  (Path(CONFIG), fixture_dir / ".gitignore", fixture_dir / "doc/.gitignore")}
        if args.selftest:
            selftest(work, output)
        elif args.hold_session_only:
            hold_session(source, work, output)
        else:
            if socket.gethostname().split(".")[0].startswith("pegasus0"):
                raise ValueError("full measurement is forbidden on Pegasus login nodes")
            measure(args, source, work, output)
    except Exception as exc:
        output["failures"].append({"check": "probe exception", "type": type(exc).__name__, "message": str(exc)})
    output["finished_at"] = now()
    output["ok"] = not output["failures"]
    try:
        if destination is None:
            raise ValueError("unsafe output destination; JSON emitted to stdout only")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(output, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        output["failures"].append({"check": "write JSON", "message": str(exc)})
        output["ok"] = False
        print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```
