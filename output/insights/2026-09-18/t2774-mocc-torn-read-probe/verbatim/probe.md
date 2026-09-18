# runner v4 の逐語 (job dir probe/t2774_probe.py、Codex role=author が段 5 + fix 3 巡で作成、repo へは commit しない)

sha256 `2e2ddea834f782abb7a671b42d8a57f82ac8b82d7ac90d23965ad3ca3fd41c00`、36746 byte。

```python
#!/usr/bin/env python3.10
"""T-2774 paired/round fixed-cell probe. Selftest/summarize use only the stdlib.

Run takes configuration only from argv. Discriminator results do not prove root
cause; diagnostic-arm conclusions are observational only.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

PIN = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
SOURCE = "cc/mocc/transaction.cc"
ARMS = ("instr", "diag")
CONCLUSIONS = ("supported", "contradicted", "indeterminate", "no-g2")
WORKLOAD_ARGV = ["-ycsb_tuple_num=10000", "-thread_num=48", "-ycsb_zipf_skew=0.9",
                 "-ycsb_rratio=50", "-ycsb_rmw=0", "-ycsb_max_ope=10", "-extime=3"]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    """Atomic, flushed receipts within the create-only run directory."""
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def command(argv, cwd, timeout, stdout, stderr, env=None):
    started = time.monotonic()
    result = {"argv": list(map(str, argv)), "cwd": str(cwd), "rc": None,
              "timeout": False, "error": None}
    with stdout.open("xb") as out, stderr.open("xb") as err:
        try:
            with subprocess.Popen(result["argv"], cwd=cwd, env=env, stdout=out,
                                  stderr=err, start_new_session=True) as proc:
                try:
                    result["rc"] = proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    result["timeout"] = True
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                    result["rc"] = proc.returncode
        except OSError as exc:
            result["error"] = str(exc)
    result["elapsed_s"] = time.monotonic() - started
    return result


def commit_count(text):
    patterns = (r"(?im)^\s*#?\s*commit_counts?[_ ]*[:=]\s*(\d+)\s*$",
                r"(?im)^\s*#?\s*committed[_ ]+(?:transactions?|txns?|count)[_ ]*[:=]\s*(\d+)\s*$")
    matches = [m for pattern in patterns for m in re.finditer(pattern, text)]
    return int(matches[0].group(1)) if len(matches) == 1 else None


def classify(rc, raw, *, timeout=False, empty_trace=False, run_ok=True):
    result = {"status": "failure", "reason": None, "rc": rc, "verdict": None,
              "certified": None, "total_cycles": None, "integrity": None,
              "anomaly_count": None}
    try:
        payload = json.loads(raw)
        if (not isinstance(payload, dict) or type(payload.get("runs")) is not int
                or payload["runs"] != 1 or not isinstance(payload["results"], list)
                or len(payload["results"]) != 1):
            raise ValueError("expected one verifier result")
        v = payload["results"][0]
        for key in ("verdict", "certified", "total_cycles", "integrity", "anomaly_count"):
            result[key] = v[key]
        cycles, count = v["total_cycles"], v["anomaly_count"]
        if (type(cycles) is not int or cycles < 0 or type(count) is not int or count < 0
                or not isinstance(v["anomalies"], list) or count != len(v["anomalies"])
                or type(v["certified"]) is not bool or type(v["serializable"]) is not bool
                or not isinstance(v["integrity"], dict)):
            raise ValueError("invalid verifier fields")
        expected = {0: ("serializable", True, True, (1, 0, 0)),
                    1: ("non-serializable", False, False, (0, 1, 0)),
                    3: ("indeterminate", False, True, (0, 0, 1))}
        if rc not in expected:
            raise ValueError("unexpected verifier rc")
        verdict, certified, serializable, counters = expected[rc]
        values = tuple(payload[k] for k in ("certified_serializable", "non_serializable", "indeterminate"))
        if (any(type(x) is not int for x in values) or values != counters
                or v["verdict"] != verdict or v["certified"] != certified
                or v["serializable"] != serializable
                or (rc in (0, 3) and (cycles or count))
                or (rc == 1 and (cycles == 0 or count == 0))
                or (rc == 3 and not (v["integrity"].get("clean") is False
                                    or (isinstance(v.get("stats"), dict)
                                        and v["stats"].get("txns") == 0)))):
            raise ValueError("rc/verdict/aggregate contradiction")
        if timeout or empty_trace or not run_ok:
            raise ValueError("timeout" if timeout else "empty trace" if empty_trace else "benchmark failed")
        result["status"] = "g2" if cycles > 0 else "indeterminate" if rc == 3 else "no-g2"
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        result["reason"] = "timeout" if timeout else str(exc)
    return result


def discriminator_result(rc, stdout, stderr, raw=None):
    result = {"rc": rc, "status": "input-rejected", "stderr": stderr,
              "blockers": [], "comparisons": []}
    if rc != 0:
        return result
    try:
        value = json.loads(raw)
        conclusion = stdout.strip()
        if (conclusion not in CONCLUSIONS or value["conclusion"] != conclusion
                or value["schema_version"] != "mocc-g2-payload-discriminator/v1"
                or not isinstance(value["blockers"], list) or not isinstance(value["comparisons"], list)):
            raise ValueError("discriminator stdout/result mismatch")
        result.update(status="completed", conclusion=conclusion,
                      blockers=value["blockers"], comparisons=value["comparisons"])
    except (ValueError, TypeError, KeyError) as exc:
        result["stderr"] += f"\n{exc}"
    return result


def clopper_pearson(k, n):
    """Invert binomial tails in log space: equal-tail two-sided 95% interval."""
    if not 0 <= k <= n:
        raise ValueError("invalid binomial counts")
    if n == 0:
        return [None, None]

    def tail(p, lo, hi):
        logs = [math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                + i * math.log(p) + (n - i) * math.log1p(-p) for i in range(lo, hi + 1)]
        largest = max(logs)
        return math.exp(largest) * math.fsum(math.exp(x - largest) for x in logs)

    def invert(lo, hi, increasing):
        left, right = 0.0, 1.0
        for _ in range(70):
            middle = (left + right) / 2
            if middle in (0.0, 1.0):
                break
            if (tail(middle, lo, hi) < 0.025) == increasing:
                left = middle
            else:
                right = middle
        return (left + right) / 2

    return [0.0 if k == 0 else invert(k, n, True),
            1.0 if k == n else invert(0, k, False)]


def summarize(blocks):
    answer = {"schema_version": "t2774-summary/v1", "arms": {},
              "denominator": "m counts valid verifier verdicts, including indeterminate; "
              "decisive_m excludes zero-cycle indeterminate; neither failure nor indeterminate is no-g2",
              "interval_assumption": "independent Bernoulli trials; node dependence not modeled"}
    for arm in dict.fromkeys(r["arm"] for b in blocks for r in b["runs"]):
        runs = [r for b in blocks for r in b["runs"] if r["arm"] == arm]
        valid = [r for r in runs if r["verifier"]["status"] != "failure"]
        k = sum(r["verifier"]["total_cycles"] > 0 for r in valid)
        m, n = len(valid), len(runs)
        decisive = sum(r["verifier"]["status"] in ("g2", "no-g2") for r in valid)
        counts = dict.fromkeys((*CONCLUSIONS, "input-rejected", "not-run"), 0)
        comparisons = []
        for r in runs:
            d = r["discriminator"]
            key = d.get("conclusion") if d["status"] == "completed" else d["status"]
            counts[key] += 1
            comparisons.extend({"block_id": r.get("block_id"), "ordinal": r["ordinal"],
                                "arm": arm, "comparison": c} for c in d.get("comparisons", []))
        identified = sum(r["verifier"]["status"] != "failure" and r["verifier"]["total_cycles"] > 0
                         and r["discriminator"].get("conclusion") in ("supported", "contradicted")
                         for r in runs)
        answer["arms"][arm] = {
            "N": n, "m": m, "k": k, "failure": n - m, "indeterminate": m - decisive,
            "decisive_m": decisive, "k_over_m": k / m if m else None, "cp95": clopper_pearson(k, m),
            "k_over_decisive_m": k / decisive if decisive else None,
            "decisive_cp95": clopper_pearson(k, decisive),
            "all_submitted_rate_bounds": [k / n, (k + n - decisive) / n] if n else [None, None],
            "discriminator_counts": counts, "comparisons": comparisons,
            "identification": {"g2_runs": k, "identified_g2_runs": identified,
                               "rate": identified / k if k else None}}
    return answer


def reclassify_block(block, path):
    """Rebuild verdicts in memory from saved artifacts; never write inputs."""
    changes = []
    for record in block["runs"]:
        before = record["verifier"]["status"]
        dest = path.parent / "runs" / f"{record['ordinal']:03d}-{record['arm']}"
        try:
            saved = json.loads((dest / "run.json").read_text())
            raw = (dest / "verifier.json").read_text(errors="replace")
            run, verify = saved["run_process"], saved["verifier_process"]
            empty_trace = False
            try:
                empty_trace = json.loads(raw)["results"][0]["stats"]["txns"] == 0
            except (ValueError, KeyError, TypeError, IndexError):
                pass  # classify handles invalid verifier JSON/fields.
            classified = classify(verify["rc"], raw,
                timeout=verify["timeout"] or run["timeout"], empty_trace=empty_trace,
                run_ok=run["rc"] == 0 and run["error"] is None and verify["error"] is None)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            classified = classify(None, "")
            classified["reason"] = f"saved artifact unavailable or invalid: {exc}"
        record["verifier"] = classified
        if before != classified["status"]:
            changes.append({"block": block.get("block_id", record.get("block_id")),
                            "ordinal": record["ordinal"], "arm": record["arm"],
                            "before": before, "after": classified["status"]})
    return changes


def manifest(root, kind, binary_sha, workload, pin):
    witness = kind == "payload-witness"
    files = []
    for path in sorted(root.glob(("witness" if witness else "trace") + "_*.log")):
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"non-regular artifact: {path}")
        files.append({"name": path.name, "sha256": sha(path), "size_bytes": info.st_size})
    if not files:
        raise ValueError(f"empty {kind} manifest")
    return {"schema_version": "mocc-g2-payload-witness-manifest/v1" if witness
            else "mocc-g2-standard-trace-manifest/v1", "artifact_kind": kind,
            "root_dir": str(root), "source_oid": pin, "binary_sha256": binary_sha,
            "workload": dict(workload), "files": files}


def run_one(args, output, scratch, arm, ordinal, cycle, order, binding, driver, workload):
    dest = output / "runs" / f"{ordinal:03d}-{arm}"
    dest.mkdir(parents=True)
    raw = scratch / f"run-{ordinal:03d}-{arm}"
    raw.mkdir()
    trace, witness = raw / "trace", raw / "witness"
    trace.mkdir()
    if binding["witness"]:
        witness.mkdir()
    saved_trace, saved_witness = dest / "trace", dest / "witness"
    record = {"block_id": args.block_id, "hostname": socket.gethostname(), "arm": arm,
              "ordinal": ordinal, "round" if args.arms_json else "pair": cycle,
              "order": order, "started_at": now(),
              "rc": None, "elapsed": {}, "commit_count": None, "verifier": classify(None, ""),
              "discriminator": {"status": "not-run", "rc": None},
              "observational_only": binding["observational_only"],
              "pin": binding["pin"], "witness": binding["witness"]}
    write_json(dest / "run.json", record)
    try:
        driver._assert_single_tenant()
        # Explicit environment: no custom or ambient variable is read by the probe.
        env = {"PATH": os.defpath, "LANG": "C.UTF-8", "TMPDIR": str(scratch),
               "IZANAGI_TRACE_DIR": str(trace), "PYTHONDONTWRITEBYTECODE": "1"}
        if binding["witness"]:
            env.update(IZANAGI_MOCC_G2_WITNESS="1", IZANAGI_MOCC_G2_WITNESS_DIR=str(witness))
        run = command([binding["binary"], *WORKLOAD_ARGV], trace, args.run_timeout_s,
                      dest / "run.stdout", dest / "run.stderr", env)
        record.update(rc=run["rc"], run_process=run)
        record["elapsed"]["run_s"] = run["elapsed_s"]
        record["commit_count"] = commit_count((dest / "run.stdout").read_text(errors="replace"))
        # Verify at the durable root: manifest root and verifier trace_dir remain
        # identical after scratch cleanup, without rewriting verifier JSON.
        for src, dst, pattern in ((trace, saved_trace, "trace_*.log"),
                                  (witness, saved_witness, "witness_*.log")):
            if src == witness and not binding["witness"]:
                continue
            dst.mkdir()
            for path in sorted(src.glob(pattern)):
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise ValueError(f"non-regular raw artifact: {path}")
                shutil.move(str(path), dst / path.name)
        nonempty = any(p.stat().st_size for p in saved_trace.glob("trace_*.log"))
        argv = [sys.executable, "-B", "-m", "orchestrator.verifier", str(saved_trace),
                "--json", "--protocol", "mocc", "--ccbench-root", binding["source"]]
        if record["commit_count"] is not None:
            argv += ["--expected-commits", str(record["commit_count"])]
        verify = command(argv, args.repo_root, args.verifier_timeout_s,
                         dest / "verifier.json", dest / "verifier.stderr", env)
        record["verifier_process"] = verify
        record["elapsed"]["verify_s"] = verify["elapsed_s"]
        record["verifier"] = classify(verify["rc"], (dest / "verifier.json").read_text(errors="replace"),
            timeout=verify["timeout"] or run["timeout"], empty_trace=not nonempty,
            run_ok=run["rc"] == 0 and run["error"] is None and verify["error"] is None)
        write_json(dest / "run.json", record)
        cycles = record["verifier"]["total_cycles"]
        if type(cycles) is int and cycles > 0:
            try:
                write_json(dest / "trace-manifest.json",
                           manifest(saved_trace, "standard-trace", binding["binary_sha256"], workload, binding["pin"]))
                reason = ("witness-off" if not binding["witness"] else
                          "pin-outside-t1943" if binding["pin"] != PIN else None)
                if reason:
                    record["discriminator"] = {"status": "not-run", "reason": reason}
                    return record  # finally still flushes the run and retains G2 raw.
                write_json(dest / "witness-manifest.json",
                           manifest(saved_witness, "payload-witness", binding["binary_sha256"], workload, binding["pin"]))
                d = command([sys.executable, "-B", "-m", "orchestrator.campaign.mocc_g2_discriminator",
                             "--trace-manifest", str(dest / "trace-manifest.json"),
                             "--witness-manifest", str(dest / "witness-manifest.json"),
                             "--verifier", str(dest / "verifier.json"),
                             "--output", str(dest / "discriminator.json")], args.repo_root,
                            args.verifier_timeout_s, dest / "discriminator.stdout", dest / "discriminator.stderr", env)
                record["elapsed"]["discriminator_s"] = d["elapsed_s"]
                record["discriminator"] = discriminator_result(d["rc"],
                    (dest / "discriminator.stdout").read_text(errors="replace"),
                    (dest / "discriminator.stderr").read_text(errors="replace"),
                    (dest / "discriminator.json").read_text(errors="replace") if (dest / "discriminator.json").exists() else None)
                record["discriminator"]["process"] = d
            except Exception as exc:
                record["discriminator"] = {"status": "input-rejected", "rc": None, "stderr": str(exc)}
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        cycles = record["verifier"]["total_cycles"]
        if not (type(cycles) is int and cycles > 0):
            for directory in (saved_trace, saved_witness):
                if directory.exists():
                    shutil.rmtree(directory)
        record["discriminator"]["observational_only"] = binding["observational_only"]
        record["finished_at"] = now()
        for name in ("run.stdout", "run.stderr", "verifier.stderr"):
            if not (dest / name).exists():
                (dest / name).touch(exist_ok=False)
        if not (dest / "verifier.json").exists():
            write_json(dest / "verifier.json", None)
        if not (dest / "discriminator.json").exists():
            write_json(dest / "discriminator.json", record["discriminator"])
        write_json(dest / "run.json", record)
    return record


def validate_arms(value):
    """Validate JSON data before site/build/checkout work; preserve patch order."""
    if not isinstance(value, list) or not value:
        raise ValueError("arms-json must be a nonempty list")
    arms, names = [], set()
    required = {"name", "pin", "patches", "witness"}
    for entry in value:
        if (not isinstance(entry, dict) or not required <= entry.keys()
                or entry.keys() - required - {"observational_only"}):
            raise ValueError("invalid arm fields")
        name, pin, patches = entry["name"], entry["pin"], entry["patches"]
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9_-]+", name) is None:
            raise ValueError("invalid arm name")
        if name in names:
            raise ValueError(f"duplicate arm name: {name}")
        if not isinstance(pin, str) or re.fullmatch(r"[0-9a-fA-F]{40}", pin) is None:
            raise ValueError(f"invalid arm pin: {name}")
        if not isinstance(patches, list) or any(
                not isinstance(p, str) or not Path(p).is_absolute() for p in patches):
            raise ValueError(f"arm patches must be absolute paths: {name}")
        if type(entry["witness"]) is not bool or type(entry.get("observational_only", False)) is not bool:
            raise ValueError(f"arm flags must be booleans: {name}")
        names.add(name)
        arms.append({"name": name, "pin": pin.lower(), "patches": list(patches),
                     "witness": entry["witness"], "observational_only": entry.get("observational_only", False)})
    return arms


def run_arms(args):
    legacy = (args.instr_patch, args.diag_patch, args.pairs)
    if args.arms_json is not None:
        if any(v is not None for v in legacy) or args.rounds is None:
            raise ValueError("--arms-json requires --rounds and excludes --instr-patch/--diag-patch/--pairs")
        raw = args.arms_json.read_bytes()
        arms = validate_arms(json.loads(raw))
        args.arms_json_sha256 = hashlib.sha256(raw).hexdigest()
        return arms
    if args.rounds is not None or any(v is None for v in legacy):
        raise ValueError("require --instr-patch/--diag-patch/--pairs or --arms-json/--rounds")
    return validate_arms([
        {"name": arm, "pin": PIN, "patches": [str(args.instr_patch)] +
         ([str(args.diag_patch)] if arm == "diag" else []),
         "witness": True, "observational_only": arm == "diag"} for arm in ARMS])


def round_order(names, cycle):
    offset = (cycle - 1) % len(names)
    return names[offset:] + names[:offset]


def configure_argv(source, build, policy, toolchain, dependencies):
    """Pilot T-1943 argv, with runtime paths and policy/toolchain bindings."""
    return [
        "cmake", "-S", str(source), "-B", str(build),
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
        "-DCCBENCH_TRACE=1", "-DCCBENCH_BACK_OFF=0", "-DCCBENCH_BACKOFF_FIXED=-1",
        "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1", "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
        "-DCCBENCH_WAL=0", "-DCCBENCH_CCACHE=OFF", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
        "-DRULE_LAUNCH_COMPILE=", "-DCMAKE_TOOLCHAIN_FILE=",
        f"-DCMAKE_PREFIX_PATH={dependencies['gflags']};{dependencies['glog']}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={dependencies['masstree']}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={dependencies['mimalloc']}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={dependencies['googletest']}",
        f"-DIZANAGI_GFLAGS_SRC_HEAD={policy['gflags_expected_head']}",
        f"-DIZANAGI_GLOG_SRC_HEAD={policy['glog_expected_head']}",
        f"-DCMAKE_C_COMPILER={toolchain['cc_path']}",
        f"-DCMAKE_CXX_COMPILER={toolchain['cxx_path']}", "-DCMAKE_CXX_FLAGS=",
    ]


def build_variant(argv, build, driver, jobs):
    driver._run_checked(argv)
    driver._run_checked(["cmake", "--build", str(build), "--target", "ycsb_mocc.exe",
                         "-j", str(jobs)], timeout=900)
    binary = build / "cc/mocc/ycsb_mocc.exe"
    if not binary.is_file():
        raise RuntimeError("mocc build did not produce ycsb_mocc.exe")
    return binary


def run(args):
    arms = args.arm_definitions
    names = [arm["name"] for arm in arms]
    cycles = args.rounds if args.arms_json else args.pairs
    sys.path.insert(0, str(args.repo_root))
    from orchestrator.campaign import s3_mocc_lock_coverage as driver
    from orchestrator.campaign import site_policy
    from orchestrator.campaign.patchharness import checkout, apply_patch, patch_files, assert_pinned_clean
    from orchestrator.campaign.mocc_g2_discriminator import EXACT_WORKLOAD

    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site) or not site_policy.is_pegasus_compute(site):
        raise RuntimeError(f"run requires a Pegasus compute node: {site}")
    driver._assert_single_tenant()
    output = args.output_dir
    try:
        output.mkdir(parents=True)
    except FileExistsError:
        output = output / f"t2774-{uuid4().hex}"
        output.mkdir()
    document = {"schema_version": "t2774-probe/v1", "block_id": args.block_id,
                "hostname": socket.gethostname(), "started_at": now(),
                "rounds" if args.arms_json else "pairs": cycles,
                "planned_runs": len(arms) * cycles, "status": "running", "runs": [],
                "bindings": {}, "output_dir": str(output)}
    scratch = None
    try:
        args.scratch_root.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix="t2774-", dir=args.scratch_root))
        os.environ["TMPDIR"] = str(scratch)
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        document["scratch"] = str(scratch)
        bindings = document["bindings"]
        bindings.update(repo_head=driver._run_checked(["git", "-C", str(args.repo_root), "rev-parse", "HEAD"]).stdout.strip(),
                        workload=dict(EXACT_WORKLOAD), workload_argv=WORKLOAD_ARGV, arms={})
        if args.arms_json is None:
            bindings.update(source_oid=PIN, instr_patch_sha256=sha(args.instr_patch),
                            diag_patch_sha256=sha(args.diag_patch))
        else:
            bindings.update(arms_json_path=str(args.arms_json), arms_json_sha256=args.arms_json_sha256)
        policy_path = args.policy or args.repo_root / "tools/pegasus/mocc_trace_v1_policy.json"
        bindings["policy_path"] = str(policy_path)
        bindings["policy_sha256"] = sha(policy_path)
        policy = driver._load_policy(policy_path)
        toolchain = driver._resolve_toolchain(policy)
        bindings["toolchain"] = toolchain
        dependencies = driver._prepare_dependencies(args.repo_root, policy, args.third_party_cache, scratch, toolchain)
        base = args.repo_root / "external/ccbench"
        bindings["base_dir"] = str(base.resolve(strict=True))
        bindings["base_git_dir"] = driver._run_checked(["git", "-C", str(base), "rev-parse", "--absolute-git-dir"]).stdout.strip()
        with ExitStack() as stack:
            sources = {}
            for definition in arms:
                arm, pin = definition["name"], definition["pin"]
                if driver._run_checked(["git", "-C", str(base), "rev-parse", pin + "^{commit}"]).stdout.strip() != pin:
                    raise ValueError(f"source OID differs: {arm}")
                source = Path(stack.enter_context(checkout(pin, base_dir=str(base))))
                assert_pinned_clean(str(source), pin)
                sources[arm] = source
                patches = []
                for patch in definition["patches"]:
                    if patch_files(patch, str(source)) != [SOURCE]:
                        raise ValueError(f"patch touches files outside {SOURCE}: {patch}")
                    digest = sha(patch)
                    apply_patch(patch, str(source))
                    if sha(patch) != digest:
                        raise ValueError(f"patch changed during application: {patch}")
                    patches.append({"path": patch, "sha256": digest})
                bindings["arms"][arm] = {
                    "pin": pin, "patches": patches, "witness": definition["witness"],
                    "observational_only": definition["observational_only"],
                    "source": str(source), "source_file_sha256": sha(source / SOURCE)}
            warm = scratch / "warmup"
            warm_argv = configure_argv(sources[names[0]], warm, policy, toolchain, dependencies)
            bindings["warmup_configure_argv"] = warm_argv
            bindings["configure_defines"] = [v for v in warm_argv if v.startswith("-DCCBENCH_")]
            driver._run_checked(warm_argv)
            jobs = site_policy.default_build_jobs(site)
            driver._run_checked(["cmake", "--build", str(warm), "--target", "masstree_build",
                                 "-j", str(jobs)], timeout=1200)
            for arm in names:
                build = scratch / f"build-{arm}"
                binding = bindings["arms"][arm]
                binding["configure_argv"] = configure_argv(sources[arm], build, policy, toolchain, dependencies)
                binding["configure_defines"] = list(bindings["configure_defines"])
                binary = build_variant(binding["configure_argv"], build, driver, jobs)
                binding.update(binary=str(binary), binary_sha256=sha(binary))
            write_json(output / "result.json", document)
            ordinal = 0
            for cycle in range(1, cycles + 1):
                order = round_order(names, cycle)
                for arm in order:
                    ordinal += 1
                    record = run_one(args, output, scratch, arm, ordinal, cycle, order,
                                     bindings["arms"][arm], driver, EXACT_WORKLOAD)
                    document["runs"].append(record)
                    document["summary"] = summarize([document])
                    write_json(output / "result.json", document)
            document["status"] = "completed"
    except Exception as exc:
        document.update(status="failure", error=f"{type(exc).__name__}: {exc}")
    finally:
        if scratch is not None:
            try:
                shutil.rmtree(scratch)
            except OSError as exc:
                document.update(status="failure", cleanup_error=str(exc))
        document["finished_at"] = now()
        document["summary"] = summarize([document])
        document["not_started"] = document["planned_runs"] - len(document["runs"])
        write_json(output / "result.json", document)
    print(f"probe: {document['status']} output={output / 'result.json'}")
    return 0 if document["status"] == "completed" else 1


def selftest():
    def fixture(rc):
        verdict = {0: "serializable", 1: "non-serializable", 3: "indeterminate"}[rc]
        v = {"verdict": verdict, "certified": rc == 0, "serializable": rc != 1,
             "total_cycles": int(rc == 1), "integrity": {"clean": rc != 3},
             "stats": {"txns": 1}, "anomaly_count": int(rc == 1),
             "anomalies": [{}] if rc == 1 else []}
        return json.dumps({"runs": 1, "certified_serializable": int(rc == 0),
                           "non_serializable": int(rc == 1), "indeterminate": int(rc == 3), "results": [v]})

    def dfixture(conclusion):
        return json.dumps({"schema_version": "mocc-g2-payload-discriminator/v1",
                           "conclusion": conclusion, "blockers": [], "comparisons": []})

    cases = [("no-g2", 0, fixture(0), {}, None, "no-g2"),
             ("g2", 1, fixture(1), {}, "supported", "g2"),
             ("g2-indeterminate", 1, fixture(1), {}, "indeterminate", "g2"),
             ("g2-input-rejected", 1, fixture(1), {}, "reject", "g2"),
             ("rc-contradiction", 0, fixture(1), {}, None, "failure"),
             ("invalid-json", 0, "{", {}, None, "failure"),
             ("timeout", None, "", {"timeout": True}, None, "failure"),
             ("empty-trace", 0, fixture(0), {"empty_trace": True}, None, "failure"),
             ("verifier-indeterminate", 3, fixture(3), {}, None, "indeterminate")]
    passed, records = 0, []
    for index, (name, rc, raw, opts, dc, expected) in enumerate(cases, 1):
        v = classify(rc, raw, **opts)
        d = ({"status": "not-run"} if dc is None else discriminator_result(2, "", "synthetic rejection")
             if dc == "reject" else discriminator_result(0, dc, "", dfixture(dc)))
        record = {"arm": "instr", "ordinal": index, "verifier": v, "discriminator": d}
        records.append(record)
        summary = summarize([{"runs": [record]}])["arms"]["instr"]
        ok = (v["status"] == expected and summary["k"] == int(expected == "g2")
              and summary["failure"] == int(expected == "failure")
              and summary["decisive_m"] == int(expected in ("g2", "no-g2"))
              and (dc != "reject" or summary["discriminator_counts"]["input-rejected"] == 1))
        passed += ok
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
    summary = summarize([{"runs": records}])["arms"]["instr"]
    checks = [summary["N"] == 9, summary["m"] == 5, summary["k"] == 3, summary["failure"] == 4,
              summary["identification"]["identified_g2_runs"] == 1,
              abs(clopper_pearson(0, 24)[1] - (1 - 0.025 ** (1 / 24))) < 1e-12,
              abs(clopper_pearson(24, 24)[0] - 0.025 ** (1 / 24)) < 1e-12,
              abs(clopper_pearson(1, 2)[0] - (1 - math.sqrt(0.975))) < 1e-12,
              clopper_pearson(0, 0) == [None, None], commit_count('#commit_counts_: 123\n') == 123,
              commit_count('commit_count: 1\ncommit_count: 2\n') is None]
    aggregate_ok = all(checks)
    print(f"aggregate-and-cp: {'PASS' if aggregate_ok else 'FAIL'}")
    passed += aggregate_ok
    dynamic = summarize([{"runs": [{**records[0], "arm": "pilot_058"},
                                   {**records[1], "arm": "custom-B"}]}])["arms"]
    ok = (set(dynamic) == {"pilot_058", "custom-B"}
          and [dynamic["pilot_058"][k] for k in ("N", "m", "k")] == [1, 1, 0]
          and [dynamic["custom-B"][k] for k in ("N", "m", "k")] == [1, 1, 1])
    passed += ok
    print(f"dynamic-arms: {'PASS' if ok else 'FAIL'}")
    entry = {"name": "A", "pin": PIN, "patches": [], "witness": False}
    invalid = [[entry, entry], [{**entry, "pin": "bad"}],
               [{**entry, "patches": ["relative.patch"]}]]
    rejected = 0
    for value in invalid:
        try:
            validate_arms(value)
        except ValueError:
            rejected += 1
    ok = (rejected == 3 and validate_arms([entry]) == [{**entry, "observational_only": False}])
    passed += ok
    print(f"arms-json-validation: {'PASS' if ok else 'FAIL'}")
    regression = json.loads(fixture(3))
    regression["results"][0].update(serializable=True, certified=False, total_cycles=0,
                                     verdict="indeterminate")
    v = classify(3, json.dumps(regression))
    ok = v["status"] == "indeterminate" and v["reason"] is None
    passed += ok
    print(f"acyclic-unclean-indeterminate: {'PASS' if ok else 'FAIL'}")
    print(f"selftest: {'PASS' if passed == 13 else 'FAIL'} {passed}/13 cases")
    return 0 if passed == 13 else 1


def absolute(text):
    path = Path(text)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("must be an absolute path")
    return path.resolve()


def positive(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest")
    run_parser = sub.add_parser("run")
    for name in ("repo-root", "third-party-cache", "scratch-root", "output-dir"):
        run_parser.add_argument("--" + name, type=absolute, required=True)
    run_parser.add_argument("--policy", type=absolute,
                            help="default: <repo-root>/tools/pegasus/mocc_trace_v1_policy.json")
    for name in ("instr-patch", "diag-patch", "arms-json"):
        run_parser.add_argument("--" + name, type=absolute)
    run_parser.add_argument("--pairs", type=positive)
    run_parser.add_argument("--rounds", type=positive)
    run_parser.add_argument("--block-id", required=True)
    run_parser.add_argument("--verifier-timeout-s", type=positive, default=300)
    run_parser.add_argument("--run-timeout-s", type=positive, default=120)
    summary_parser = sub.add_parser("summarize")
    summary_parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    summary_parser.add_argument("--output", type=absolute, required=True)
    summary_parser.add_argument("--reclassify", action="store_true",
                                help="reclassify saved verifier/run JSON without modifying inputs")
    args = parser.parse_args()
    if args.command == "selftest":
        return selftest()
    if args.command == "summarize":
        paths = [p.resolve(strict=True) for p in args.inputs]
        if len(paths) != len(set(paths)):
            parser.error("duplicate input block paths")
        snapshots = [p.read_bytes() for p in paths]
        blocks = [json.loads(raw) for raw in snapshots]
        inputs = [{"path": str(p), "sha256": hashlib.sha256(raw).hexdigest()}
                  for p, raw in zip(paths, snapshots)]
        if args.reclassify:
            for block, path, metadata in zip(blocks, paths, inputs):
                metadata.update(reclassified=True, status_changes=reclassify_block(block, path))
        value = summarize(blocks)
        value["inputs"] = inputs
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        print(f"summarize: {args.output}")
        return 0
    try:
        args.arm_definitions = run_arms(args)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return run(args)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
```
