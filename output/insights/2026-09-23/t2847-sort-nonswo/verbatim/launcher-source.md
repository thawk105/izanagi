# 起動器 launch_sort_nonswo.py の逐語 (Codex author s5-author が作成、fix 2 巡 s6-fix1・s6-fix2 を経た投入版。repo 外 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py で実行、sha256 1e30c8c34c35105d9c1634b6fb5095f2c78a3d97ec6163636c2269271402a51d)

実装面の file を repo へ入れないため、source を `.md` の fenced block として逐語で残す (本文は下の block の後ろに cat で追記した)。

```python
#!/usr/bin/env python3
"""Preregistered V07 compute-node correctness launcher."""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

CLK = 2100
RUN_TIMEOUT_S = 120.0
FLAGS = {"thread_num": "1", "ycsb_tuple_num": "200", "ycsb_zipf_skew": "0",
         "ycsb_rratio": "0", "ycsb_rmw": "true", "extime": "1"}
INTEGRITY_FIELDS = ("orphan_reads", "version_dups", "dup_txids", "genesis_commits",
                    "missing_txids", "write_version_mismatch", "malformed_keys",
                    "framing_violations", "lock_coverage_violations",
                    "write_intent_violations", "permutation_violations")
A = "その他 (未実走)"
CONTROL = "期待どおり (対照)"
BAD_CONTROL = "その他 (対照不成立)"


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def exception_record(exc):
    return {"type": type(exc).__name__, "message": str(exc)}


def write_json(path, payload):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def checked(argv):
    return subprocess.run(argv, check=True, capture_output=True, text=True,
                          timeout=60).stdout.strip()


class Proxy:
    def __init__(self, original, **overrides):
        self._original = original
        self.__dict__.update(overrides)

    def __getattr__(self, name):
        return getattr(self._original, name)


class VerifierRecorder(Proxy):
    """Passive verifier output recording, preserving subprocess return/exception."""
    def __init__(self, original, out, meta):
        super().__init__(original)
        self.out, self.meta, self.sequence = out, meta, 0

    def save(self, argv, proc=None, exc=None):
        self.sequence += 1
        try:
            payload = {"argv": list(argv), "rc": None if proc is None else proc.returncode,
                       "stdout": getattr(exc if proc is None else proc, "stdout", None),
                       "stderr": getattr(exc if proc is None else proc, "stderr", None)}
            if exc is not None:
                payload["exception"] = exception_record(exc)
            for field in ("stdout", "stderr"):
                if isinstance(payload[field], bytes):
                    payload[field] = {"base64": base64.b64encode(payload[field]).decode("ascii")}
            self.out.mkdir(exist_ok=True)
            write_json(self.out / f"{self.sequence:04d}.json", payload)
        except Exception as error:
            self.meta["verifier_save_failures"].append(
                {"sequence": self.sequence, **exception_record(error)})

    def run(self, *args, **kwargs):
        argv = args[0] if args else kwargs.get("args")
        if not (isinstance(argv, (list, tuple)) and
                list(argv[:3]) == [sys.executable, "-m", "verifier"]):
            return self._original.run(*args, **kwargs)
        try:
            proc = self._original.run(*args, **kwargs)
        except BaseException as exc:
            self.save(argv, exc=exc)
            raise
        self.save(argv, proc=proc)
        return proc


def cmake_literal(path):
    value, equals = str(path), ""
    while "]" + equals + "]" in value:
        equals += "="
    return "[" + equals + "[" + value + "]" + equals + "]"


def _stage(verifier):
    if verifier is None or verifier.get("failure"):
        return None
    verdict = verifier.get("verdict")
    if verdict == "serializable" and verifier.get("certified") is True:
        return "S"
    if verdict == "indeterminate":
        return "I"
    if verdict == "non-serializable":
        return "N"
    return None


def classify(run_id, run, controls=None, foundation_ok=True):
    """prereg.md 段 A–D: first matching rule in the registered order."""
    if not foundation_ok:
        return A
    controls = controls or {}
    rc, timeout, verifier = run.get("rc"), run.get("timeout", False), run.get("verifier")
    stage = _stage(verifier)
    maximum = run.get("trace", {}).get("write_count_max")
    failed = verifier is None or bool(verifier.get("failure"))
    empty = not failed and verifier.get("stats", {}).get("txns") == 0
    if run_id in ("R1", "R2"):
        n = 16 if run_id == "R1" else 17
        if (not timeout and rc == 0 and not failed and not empty and stage == "S" and
                verifier.get("total_cycles") == 0 and verifier.get("x_count") == 0 and
                verifier.get("p_count") == 0 and
                verifier.get("integrity_all_zero") is True and maximum == n):
            return CONTROL
        if timeout or rc != 0 or failed or empty:
            return BAD_CONTROL
        if rc == 0 and stage in ("I", "N"):
            return "誤検出"
        return BAD_CONTROL
    if run_id == "R3":
        if controls.get("R1") != CONTROL:
            return BAD_CONTROL
        if timeout:
            return "その他 (16 要素で停止 = 記録の境界どおり、source 読みの予測外)"
        if rc is not None and rc < 0:
            return "別の層で検出 (process の異常終了)"
        if rc is not None and rc > 0:
            return "その他 (帰属不明の異常終了)"
        if rc == 0 and (failed or empty or stage is None):
            return "その他"
        if rc == 0 and stage in ("I", "N"):
            return "別の層で検出 (verifier)"
        if rc == 0 and stage == "S" and maximum == 16:
            return "期待どおり (16 要素では S)"
        if rc == 0 and stage == "S" and (maximum is None or maximum < 16):
            return "その他 (条件未到達)"
        return "その他"
    if run_id == "R4":
        if controls.get("R2") != CONTROL:
            return BAD_CONTROL
        if timeout:
            return "期待どおり (hang。verifier の判定は無く、止めたのは timeout = 盲点)"
        if rc is not None and rc < 0:
            return "別の層で検出 (process の異常終了)"
        if rc is not None and rc > 0:
            return "その他 (帰属不明の異常終了)"
        if rc == 0 and (failed or empty or stage is None):
            return "その他"
        if rc == 0 and stage in ("I", "N"):
            return "別の層で検出 (verifier)"
        if rc == 0 and stage == "S" and maximum is not None and maximum >= 17:
            return "未発生 (17 要素の取引が commit し S = 盲点の S)"
        if rc == 0 and stage == "S" and (maximum is None or maximum < 17):
            return "その他 (条件未到達)"
        return "その他"
    raise ValueError(f"unknown run: {run_id}")


def build_variant(s5, sub, out, value, builds):
    bdir = out / f"build-v{value}"
    defines = s5.STOCK_G.cmake_defines() + ["-DCCBENCH_TRACE=1",
                                            f"-DCCBENCH_SORT_VARIANT={value}"]
    cfg = ["cmake", "-S", str(sub), "-B", str(bdir),
           "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
           f"-DCMAKE_C_COMPILER={s5.buildcache.DEFAULT_CC}",
           f"-DCMAKE_CXX_COMPILER={s5.buildcache.DEFAULT_CXX}"] + defines
    record = {"value": value, "configure_argv": cfg, "build_dir": str(bdir)}
    builds[f"v{value}"] = record
    try:
        site = s5.site_policy.current_site()
        if s5.site_policy.refuses_heavy_work(site):
            raise s5.buildcache.BuildError(
                s5.site_policy.heavy_work_refusal(site, "cmake configure/build"))
        subprocess.run(cfg, check=True, capture_output=True, text=True)
        s5._run_cmake_build(["cmake", "--build", str(bdir), "--target", "ycsb_silo.exe"],
                            site=site)
        cache_lines = [line for line in (bdir / "CMakeCache.txt").read_text().splitlines()
                       if re.match(r"CCBENCH_SORT_VARIANT:[^=]+=", line)]
        record["cmake_cache_lines"] = cache_lines
        flags_path = bdir / "cc/silo/CMakeFiles/ycsb_silo.exe.dir/flags.make"
        if not flags_path.is_file():
            matches = list(bdir.rglob("ycsb_silo.exe.dir/flags.make"))
            if len(matches) != 1:
                raise RuntimeError(f"target flags.make missing/ambiguous: {matches}")
            flags_path = matches[0]
        record["flags_make_path"] = str(flags_path)
        lines = flags_path.read_text().splitlines()
        for field in ("CXX_DEFINES", "CXX_FLAGS"):
            found = [line for line in lines if line.startswith(field + " =")]
            record[field + "_lines"] = found
            if len(found) != 1:
                raise RuntimeError(f"{field} line missing/ambiguous in {flags_path}")
            record[field] = found[0]
        binary = bdir / "cc/silo/ycsb_silo.exe"
        record["binary"] = str(binary)
        if binary.is_file():
            record["binary_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        if len(cache_lines) != 1 or cache_lines[0].split("=", 1)[1] != str(value):
            raise RuntimeError(f"CMakeCache CCBENCH_SORT_VARIANT mismatch: {cache_lines}")
        record["cmake_cache_line"] = cache_lines[0]
        tokens = record["CXX_DEFINES"].split("=", 1)[1].split()
        variants = [item for item in tokens
                    if re.match(r"^-DSORT_VARIANT(?:=|$)", item)]
        if variants != [f"-DSORT_VARIANT={value}"]:
            raise RuntimeError(f"SORT_VARIANT definition mismatch: {variants}")
        if "binary_sha256" not in record:
            raise RuntimeError(f"binary missing: {binary}")
    except BaseException as exc:
        record["failure"] = exception_record(exc)
        # A failed configure/build can still leave useful provenance on disk.
        cache = bdir / "CMakeCache.txt"
        if "cmake_cache_lines" not in record and cache.is_file():
            try:
                record["cmake_cache_lines"] = [line for line in cache.read_text().splitlines()
                                               if re.match(r"CCBENCH_SORT_VARIANT:[^=]+=", line)]
            except OSError:
                pass
        if "cmake_cache_line" not in record and len(record.get("cmake_cache_lines", [])) == 1:
            record["cmake_cache_line"] = record["cmake_cache_lines"][0]
        flags = bdir / "cc/silo/CMakeFiles/ycsb_silo.exe.dir/flags.make"
        if not flags.is_file():
            matches = list(bdir.rglob("ycsb_silo.exe.dir/flags.make"))
            if len(matches) == 1:
                flags = matches[0]
        if flags.is_file():
            record["flags_make_path"] = str(flags)
            try:
                lines = flags.read_text().splitlines()
                for field in ("CXX_DEFINES", "CXX_FLAGS"):
                    found = [line for line in lines if line.startswith(field + " =")]
                    record[field + "_lines"] = found
                    if len(found) == 1:
                        record[field] = found[0]
            except OSError:
                pass
        binary = bdir / "cc/silo/ycsb_silo.exe"
        if binary.is_file():
            record["binary"] = str(binary)
            if "binary_sha256" not in record:
                try:
                    record["binary_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
                except OSError:
                    pass
        raise
    return record


def run_trace(binary, n, scratch):
    tdir = Path(tempfile.mkdtemp(prefix="izanagi_t2847_trace_", dir=scratch))
    (tdir / "log").mkdir()
    flags = dict(FLAGS, ycsb_max_ope=str(n))
    argv = [str(binary)] + [f"-{key}={value}" for key, value in flags.items()]
    argv += [f"-clocks_per_us={CLK}"]
    start = time.monotonic()
    observation = {"argv": argv, "flags": flags, "timeout": False, "rc": None,
                   "elapsed_seconds": None, "stderr_tail": ""}
    try:
        proc = subprocess.run(argv, env=dict(os.environ, IZANAGI_TRACE_DIR=str(tdir)),
                              capture_output=True, text=True, timeout=RUN_TIMEOUT_S, cwd=tdir)
        observation.update(rc=proc.returncode, stderr_tail=proc.stderr[-2000:])
    except subprocess.TimeoutExpired as exc:
        err = exc.stderr or b""
        observation.update(timeout=True, stderr_tail=(err.decode("utf-8", "replace")
                                                        if isinstance(err, bytes) else err)[-2000:])
    except (OSError, subprocess.SubprocessError) as exc:
        observation["run_error"] = exception_record(exc)
    finally:
        observation["elapsed_seconds"] = time.monotonic() - start
    return tdir, observation


def trace_stats(tdir):
    counts = {}
    c_count = 0
    malformed = []
    for path in sorted(tdir.glob("trace_*.log")):
        with path.open(errors="replace") as handle:
            for number, line in enumerate(handle, 1):
                if line.startswith("C "):
                    fields = line.split()
                    c_count += 1
                    if len(fields) not in (7, 10):
                        malformed.append(f"{path}:{number}: field count {len(fields)}")
                        continue
                    try:
                        value = int(fields[6])
                    except ValueError:
                        malformed.append(f"{path}:{number}: invalid write_count")
                        continue
                    counts[str(value)] = counts.get(str(value), 0) + 1
    return {"c_lines": c_count, "write_count_max": max(map(int, counts)) if counts else None,
            "write_count_distribution": counts, "malformed_c_lines": malformed}


def verify_once(s5, tdir, root):
    # The argv, cwd and timeout match s5._verify; exactly one invocation.
    cmd = [sys.executable, "-m", "verifier", str(tdir), "--json", "--quiet",
           "--protocol", "silo", "--ccbench-root", str(root / "external/ccbench")]
    try:
        proc = s5.subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=s5.VERIFIER_TIMEOUT_S,
                                 cwd=str(root / "orchestrator"))
        if proc.returncode not in (0, 1, 3):
            raise ValueError(f"verifier rc={proc.returncode}")
        results = json.loads(proc.stdout)["results"]
        if not isinstance(results, list) or len(results) != 1:
            raise ValueError("verifier results count != 1")
        row = results[0]
        verdict, certified = row["verdict"], row["certified"]
        expected = {"serializable": 0, "non-serializable": 1, "indeterminate": 3}
        if (verdict not in expected or proc.returncode != expected[verdict] or
                (verdict == "serializable" and certified is not True)):
            raise ValueError(f"verifier rc/verdict/certified mismatch: {proc.returncode}/{verdict}/{certified}")
        integrity, stats = row["integrity"], row["stats"]
        fields = {key: integrity[key] for key in INTEGRITY_FIELDS}
        if any(type(value) is not int or value < 0 for value in fields.values()):
            raise ValueError("integrity numeric fields malformed")
        if type(stats["txns"]) is not int or stats["txns"] < 0:
            raise ValueError("stats.txns malformed")
        p_reasons = s5._count_p_reasons(str(tdir))
        cross = s5._oracle_cross_check(p_reasons, integrity["permutation_violation_details"])
        return {"exit_code": proc.returncode, "verdict": verdict, "certified": certified,
                "total_cycles": row["total_cycles"], "integrity": integrity,
                "integrity_numeric_fields": fields,
                "integrity_all_zero": all(v == 0 for v in fields.values()),
                "stats": stats, "x_count": fields["lock_coverage_violations"],
                "p_count": fields["permutation_violations"], "p_reasons": p_reasons,
                "oracle_cross_check_matches": cross, "failure": None}
    except Exception as exc:
        return {"failure": exception_record(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("--third-party-cache", "--out-dir", "--repo-root"):
        parser.add_argument(option, type=Path, required=True)
    args = parser.parse_args()
    for name in ("third_party_cache", "out_dir", "repo_root"):
        if not getattr(args, name).is_absolute():
            parser.error("--" + name.replace("_", "-") + " must be absolute")
    out = args.out_dir
    meta = {"hostname": socket.gethostname(), "started_at": timestamp(),
            "finished_at": None, "pin": None, "ccbench_head": None,
            "python": sys.version, "python_executable": sys.executable,
            "cmake": None, "compiler": None, "argv": list(sys.argv),
            "repo_root": str(args.repo_root), "environment": {}, "exception": None,
            "replaced_names": [], "verifier_save_failures": [], "launcher_rc": None}
    result = {"gate": None, "builds": {}, "runs": {}, "classifications": {},
              "foundation_ok": False, "foundation_failure": None}
    phase, rc, out_ready = "preflight", 2, False
    try:
        out = out.resolve()
        out.mkdir(parents=True, exist_ok=True)
        if any(out.iterdir()):
            raise ValueError("--out-dir must be empty")
        out_ready = True
        (out / "verifier").mkdir()
        if sys.version_info < (3, 10):
            raise RuntimeError("Python >= 3.10 required")
        if re.fullmatch(r"pegasus0\d+(?:\..*)?", meta["hostname"]):
            raise RuntimeError("compute-node execution required; refusing login node")
        root = args.repo_root.resolve(strict=True)
        if not (root / "orchestrator/campaign").is_dir():
            raise RuntimeError("--repo-root does not contain orchestrator/campaign")
        if not args.third_party_cache.is_dir():
            raise RuntimeError("--third-party-cache must be an existing directory")
        scratch = out / "scratch"
        scratch.mkdir()
        os.environ["TMPDIR"] = str(scratch)
        meta["environment"]["TMPDIR"] = str(scratch)
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(root))
        compute = importlib.import_module("orchestrator.campaign.s3_mocc_lock_coverage")
        pin = importlib.import_module("orchestrator.campaign.pin")
        s5 = importlib.import_module("orchestrator.campaign.s5_permutation_coverage")
        silo = importlib.import_module("orchestrator.campaign.silo_policy_coverage")
        sub = root / "external/ccbench"
        meta["pin"] = checked(["git", "-C", str(sub), "rev-parse", pin.CURRENT_PIN + "^{commit}"])
        meta["ccbench_head"] = checked(["git", "-C", str(sub), "rev-parse", "HEAD"])
        if any(re.fullmatch(r"[0-9a-f]{40}", sha) is None
               for sha in (meta["pin"], meta["ccbench_head"])):
            raise RuntimeError("ccbench commit must be a 40-digit SHA")
        meta["cmake"] = checked(["cmake", "--version"])
        match = re.search(r"cmake version (\d+)\.(\d+)(?:\.(\d+))?", meta["cmake"])
        if match is None or tuple(int(part or 0) for part in match.groups()) < (3, 21, 0):
            raise RuntimeError("CMake >= 3.21 required")
        policy = compute._load_policy(root / "tools/pegasus/mocc_trace_v1_policy.json")
        toolchain = compute._resolve_toolchain(policy)
        meta["compiler"] = dict(toolchain)
        meta["compiler"]["cc_version"] = checked([toolchain["cc_path"], "--version"])
        meta["compiler"]["cxx_version"] = checked([toolchain["cxx_path"], "--version"])
        s5._assert_single_tenant()
        s5.assert_pinned_clean(str(sub), s5.PIN)
        phase = "foundation"
        deps = compute._prepare_dependencies(root, policy, args.third_party_cache, scratch, toolchain)
        meta["dependency_preparation"] = silo._prepare_build_dependencies(scratch, toolchain, deps)
        toolchain_file = out / "dependencies.cmake"
        toolchain_file.write_text("".join(
            "set(FETCHCONTENT_SOURCE_DIR_" + name.upper() + " " +
            cmake_literal(deps[name]) + ")\n"
            for name in ("masstree", "mimalloc", "googletest")), encoding="utf-8")
        environment = {"CMAKE_TOOLCHAIN_FILE": str(toolchain_file),
                       "CMAKE_PREFIX_PATH": str(deps["gflags"]) + ":" + str(deps["glog"])}
        os.environ.update(environment)
        meta["environment"].update(environment)
        s5.buildcache = Proxy(s5.buildcache, DEFAULT_CC=toolchain["cc_path"],
                              DEFAULT_CXX=toolchain["cxx_path"])
        meta["replaced_names"].extend(("buildcache.DEFAULT_CC", "buildcache.DEFAULT_CXX"))
        s5.subprocess = VerifierRecorder(s5.subprocess, out / "verifier", meta)
        meta["replaced_names"].append("subprocess.run(verifier passive recording)")
        with s5.applied(str(root / "patches/broken-silo-sort-nonswo.patch"), s5.PIN, str(sub)):
            result["gate"] = s5._require_condition_gate(str(sub), "SORT_VARIANT")
            build_variant(s5, sub, out, 1, result["builds"])
            build_variant(s5, sub, out, 0, result["builds"])
        result["foundation_ok"] = True
        phase = "runs"
        for run_id, value, n in (("R1", 0, 16), ("R2", 0, 17),
                                 ("R3", 1, 16), ("R4", 1, 17)):
            tdir, observation = run_trace(result["builds"][f"v{value}"]["binary"], n, scratch)
            observation.update(build=f"v{value}", workload=f"W({n})")
            if observation.get("run_error"):
                result["runs"][run_id] = observation
                shutil.rmtree(tdir, ignore_errors=True)
                raise RuntimeError(f"{run_id} could not start: {observation['run_error']}")
            try:
                try:
                    observation["trace"] = trace_stats(tdir)
                    observation["trace"]["timeout_prefix_reference_only"] = observation["timeout"]
                except (OSError, ValueError) as exc:
                    observation["trace_error"] = exception_record(exc)
                    observation["trace"] = {"c_lines": None, "write_count_max": None,
                                            "write_count_distribution": {},
                                            "timeout_prefix_reference_only": observation["timeout"]}
                observation["verifier"] = None if observation["timeout"] else verify_once(s5, tdir, root)
            finally:
                shutil.rmtree(tdir, ignore_errors=True)
            result["runs"][run_id] = observation
            result["classifications"][run_id] = classify(
                run_id, observation, result["classifications"])
            write_json(out / "result.json", result)
        rc = 0
    except BaseException as exc:
        meta["exception"] = exception_record(exc)
        if phase == "preflight":
            rc = 2
        elif phase == "foundation":
            rc = 1
            result["foundation_failure"] = exception_record(exc)
            result["foundation_ok"] = False
            result["classifications"] = {name: A for name in ("R1", "R2", "R3", "R4")}
        else:
            rc = 1
            result["run_failure"] = exception_record(exc)
        print("ERROR: " + str(exc), file=sys.stderr)
    finally:
        meta.update(finished_at=timestamp(), phase=phase, launcher_rc=rc)
        if out_ready:
            failures = []
            for name, payload in (("result.json", result), ("meta.json", meta)):
                try:
                    write_json(out / name, payload)
                except Exception as exc:
                    failures.append({"file": name, **exception_record(exc)})
                    if rc == 0:
                        rc = 1
                    meta["launcher_rc"] = rc
                    result["json_save_failures"] = failures
                    meta["json_save_failures"] = failures
                    print(f"ERROR: cannot write {name}: {exc}", file=sys.stderr)
            if failures and failures[-1]["file"] == "meta.json":
                # The first result save preceded the meta failure; update it.
                try:
                    write_json(out / "result.json", result)
                except Exception as exc:
                    print(f"ERROR: cannot update result.json: {exc}", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
```
