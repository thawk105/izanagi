# 起動器 launch_patch_verify.py の逐語 (Codex author s5-author が作成、repo 外 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/launch_patch_verify.py で実行、sha256 bc955855c2cb426b73023aa3d0f43b72262d952fb020499310689d861cc276cc)

実装面の file を repo へ入れないため、source を `.md` の fenced block として逐語で残す (本文は下の block の後ろに cat で追記した)。

```python
#!/usr/bin/env python3
"""Disposable correctness driver launcher; repository location is explicit."""

import argparse
import base64
import datetime
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys


DRIVERS = {
    "s2": "s2_verify_calibration",
    "s3": "s3_lock_coverage",
    "s5": "s5_permutation_coverage",
    "t152": "t152_write_intent_coverage",
}


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
    """Only the selected driver's local reference is replaced."""

    def __init__(self, original, **overrides):
        self._original = original
        self.__dict__.update(overrides)

    def __getattr__(self, name):
        return getattr(self._original, name)


class VerifierRecorder(Proxy):
    def __init__(self, original, out, meta):
        super().__init__(original)
        self.out = out
        self.meta = meta
        self.sequence = 0

    def save(self, argv, proc=None, exc=None):
        # Recording failures must not replace a result or a subprocess exception.
        self.sequence += 1
        try:
            payload = {"argv": list(argv), "rc": None if proc is None else proc.returncode,
                       "stdout": getattr(exc if proc is None else proc, "stdout", None),
                       "stderr": getattr(exc if proc is None else proc, "stderr", None)}
            if exc is not None:
                payload["exception"] = exception_record(exc)
            # TimeoutExpired can carry bytes even when text=True. Preserve them exactly.
            for field in ("stdout", "stderr"):
                if isinstance(payload[field], bytes):
                    payload[field] = {"base64": base64.b64encode(payload[field]).decode("ascii")}
            self.out.mkdir(exist_ok=True)
            write_json(self.out / ("%04d.json" % self.sequence), payload)
        except Exception as error:
            failure = {"sequence": self.sequence, **exception_record(error)}
            self.meta["verifier_save_failures"].append(failure)
            try:
                print("verifier save failed: " + str(failure), file=sys.stderr)
            except Exception:
                pass

    def run(self, *args, **kwargs):
        argv = args[0] if args else kwargs.get("args")
        # Exact prefixes used at s2:201, s3:164, s5:194, t152:535.
        verifier = isinstance(argv, (list, tuple)) and (
            list(argv[:3]) == [sys.executable, "-m", "verifier"]
            or list(argv[:5]) == ["/usr/bin/time", "-v", sys.executable, "-m", "verifier"]
        )
        if not verifier:
            return self._original.run(*args, **kwargs)
        try:
            proc = self._original.run(*args, **kwargs)
        except BaseException as exc:
            self.save(argv, exc=exc)
            raise
        self.save(argv, proc=proc)
        return proc


def configure_driver(driver, name, pin, toolchain, out, meta):
    def replace(attribute, value, names):
        setattr(driver, attribute, value)
        meta["replaced_names"].extend(name + "." + item for item in names)

    cc, cxx = toolchain["cc_path"], toolchain["cxx_path"]
    if name in ("s2", "s3", "s5"):
        original = driver.buildcache
        overrides = {"DEFAULT_CC": cc, "DEFAULT_CXX": cxx}
        names = ["buildcache.DEFAULT_CC", "buildcache.DEFAULT_CXX"]
        if name in ("s3", "s5"):
            cache = out / "buildcache"
            cache.mkdir()

            def build(*args, **kwargs):
                kwargs.update(cc=cc, cxx=cxx, cache_root=str(cache))
                return original.build(*args, **kwargs)

            overrides["build"] = build
            names.append("buildcache.build(cc,cxx,cache_root)")
        replace("buildcache", Proxy(original, **overrides), names)
    if name in ("s3", "s5"):
        source = driver.source_digest

        def resolve_evidence(*args, **kwargs):
            kwargs["cxx"] = cxx
            return source.resolve_evidence(*args, **kwargs)

        replace("source_digest", Proxy(source, resolve_evidence=resolve_evidence),
                ["source_digest.resolve_evidence(cxx)"])
        replace("ENV_TAG", "pegasus", ["ENV_TAG"])
    if name in ("s3", "s5", "t152"):
        replace("repo_output_root", lambda: str(out), ["repo_output_root"])
    if name == "s2":
        replace("PIN", pin.CURRENT_PIN, ["PIN"])
    replace("subprocess", VerifierRecorder(driver.subprocess, out / "verifier", meta),
            ["subprocess.run(verifier passive recording)"])


def run_s2(driver, root, scratch, out):
    sub = str(root / "external/ccbench")
    driver._assert_single_tenant()
    free_gb = driver._assert_free_disk(str(scratch))
    driver.assert_pinned_clean(sub, driver.PIN)
    gates = driver._preflight_condition_gates(str(root), sub)
    legacy_wl = driver.CorrectnessWorkload().flags
    legacy = ({k: v for k, v in legacy_wl.items() if k != "extime"},
              int(legacy_wl["extime"]))
    workloads = {"s2": (dict(driver.S2_FLAGS), 3), "legacy": legacy}
    result = {"pin": driver.PIN, "condition_gates": gates,
              "free_disk_gb_at_start": free_gb, "workloads": workloads}
    path = out / "s2_broken_at_pin.json"
    try:
        g3a = driver._broken_build_and_verify(driver.NORW_PATCH, driver.NORW_DEFINE, workloads)
        result["norw"] = g3a
        write_json(path, result)
        g3b = driver._broken_build_and_verify(driver.HIGHKEY_PATCH, driver.HIGHKEY_DEFINE, workloads)
        result["highkey"] = g3b
        a = g3a["runs"]["s2"]["verifier"]
        b_s2 = g3b["runs"]["s2"]["verifier"]
        b_leg = g3b["runs"]["legacy"]["verifier"]
        # Identical predicates to s2_verify_calibration.py:411-419.
        gate3 = {
            "norw_red": a["verdict"] == "non-serializable" and a["total_cycles"] >= 1
                        and a["exit_code"] == 1,
            "highkey_s2_red": b_s2["verdict"] == "non-serializable"
                              and b_s2["total_cycles"] >= 1,
            "highkey_legacy_green": b_leg["certified"],
            "pass": None,
        }
        gate3["pass"] = (gate3["norw_red"] and gate3["highkey_s2_red"]
                         and gate3["highkey_legacy_green"])
        result["gate3"] = gate3
        return 0 if gate3["pass"] else 1
    finally:
        write_json(path, result)


def cmake_literal(path):
    value = str(path)
    equals = ""
    while "]" + equals + "]" in value:
        equals += "="
    return "[" + equals + "[" + value + "]" + equals + "]"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", choices=tuple(DRIVERS))
    for option in ("--third-party-cache", "--out-dir", "--repo-root"):
        parser.add_argument(option, type=Path, required=True)
    args = parser.parse_args()
    for name in ("third_party_cache", "out_dir", "repo_root"):
        if not getattr(args, name).is_absolute():
            parser.error("--" + name.replace("_", "-") + " must be absolute")
    out = args.out_dir.resolve()
    try:
        out.mkdir(parents=True, exist_ok=True)
        if any(out.iterdir()):
            parser.error("--out-dir must be empty; existing contents are not overwritten")
    except OSError as exc:
        parser.error(str(exc))

    meta = {"hostname": socket.gethostname(), "started_at": timestamp(),
            "finished_at": None, "driver": args.driver, "pin": None,
            "python": sys.version, "python_executable": sys.executable,
            "cmake": None, "compiler": None, "argv": list(sys.argv),
            "repo_root": str(args.repo_root), "driver_rc": None,
            "exception": None, "replaced_names": [], "environment": {},
            "verifier_save_failures": []}
    phase = "preflight"
    rc = 2
    try:
        if sys.version_info < (3, 10):
            raise RuntimeError("Python >= 3.10 is required before repository imports")
        root = args.repo_root.resolve(strict=True)
        if not (root / "orchestrator/campaign").is_dir():
            raise RuntimeError("--repo-root does not contain orchestrator/campaign")
        if not args.third_party_cache.is_dir():
            raise RuntimeError("--third-party-cache must be an existing directory")
        if re.fullmatch(r"pegasus0\d+(?:\..*)?", meta["hostname"]):
            raise RuntimeError("compute-node execution required; refusing login node")
        scratch = out / "scratch"
        scratch.mkdir()
        os.environ["TMPDIR"] = str(scratch)
        meta["environment"]["TMPDIR"] = str(scratch)
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(root))
        compute = importlib.import_module("orchestrator.campaign.s3_mocc_lock_coverage")
        pin = importlib.import_module("orchestrator.campaign.pin")
        sub = root / "external/ccbench"
        meta["pin"] = checked(["git", "-C", str(sub), "rev-parse", pin.CURRENT_PIN + "^{commit}"])
        head = checked(["git", "-C", str(sub), "rev-parse", "HEAD"])
        if any(re.fullmatch(r"[0-9a-f]{40}", sha) is None for sha in (head, meta["pin"])):
            raise RuntimeError("ccbench commit must be a 40-digit SHA")
        meta["ccbench_head"] = head
        meta["cmake"] = checked(["cmake", "--version"])
        match = re.search(r"cmake version (\d+)\.(\d+)(?:\.(\d+))?", meta["cmake"])
        if match is None or tuple(int(n or 0) for n in match.groups()) < (3, 21, 0):
            raise RuntimeError("CMake >= 3.21 is required")
        policy = compute._load_policy(root / "tools/pegasus/mocc_trace_v1_policy.json")
        toolchain = compute._resolve_toolchain(policy)
        meta["compiler"] = dict(toolchain)
        meta["compiler"]["cc_version"] = checked([toolchain["cc_path"], "--version"])
        meta["compiler"]["cxx_version"] = checked([toolchain["cxx_path"], "--version"])
        if args.driver == "s2":
            if shutil.which("numactl") is None or not (
                    Path("/usr/bin/time").is_file() and os.access("/usr/bin/time", os.X_OK)):
                raise RuntimeError("s2 requires numactl and executable /usr/bin/time")
        driver = importlib.import_module("orchestrator.campaign." + DRIVERS[args.driver])
        silo = importlib.import_module("orchestrator.campaign.silo_policy_coverage")
        write_json(out / "preflight.json", {"ok": True})

        phase = "dependencies"
        deps = compute._prepare_dependencies(root, policy, args.third_party_cache, scratch, toolchain)
        meta["dependency_preparation"] = silo._prepare_build_dependencies(scratch, toolchain, deps)
        toolchain_file = out / "dependencies.cmake"
        toolchain_file.write_text("".join(
            "set(FETCHCONTENT_SOURCE_DIR_" + name.upper() + " "
            + cmake_literal(deps[name]) + ")\n"
            for name in ("masstree", "mimalloc", "googletest")), encoding="utf-8")
        environment = {"CMAKE_TOOLCHAIN_FILE": str(toolchain_file),
                       "CMAKE_PREFIX_PATH": str(deps["gflags"]) + ":" + str(deps["glog"])}
        if args.driver == "t152":
            environment.update(IZANAGI_T152_CCBENCH_SHA=head,
                               IZANAGI_T152_CC=toolchain["cc_path"],
                               IZANAGI_T152_CXX=toolchain["cxx_path"])
            meta["host_role_note"] = "driver host_role is fixed to login-node; use launcher hostname"
        os.environ.update(environment)
        meta["environment"].update(environment)
        configure_driver(driver, args.driver, pin, toolchain, out, meta)
        phase = "driver"
        if args.driver == "s2":
            rc = run_s2(driver, root, scratch, out)
        elif args.driver == "t152":
            # Same handler and return contract as _entrypoint, retaining exception metadata.
            try:
                rc = driver.main()
            except (RuntimeError, subprocess.SubprocessError, OSError, ValueError) as exc:
                meta["exception"] = exception_record(exc)
                print("ERROR: " + str(exc), file=sys.stderr)
                rc = 2
        else:
            rc = driver.main()
        meta["driver_rc"] = rc
    except BaseException as exc:
        meta["exception"] = exception_record(exc)
        rc = 2 if phase == "preflight" else 1
        if phase == "driver":
            meta["driver_rc"] = rc
        if phase == "preflight":
            write_json(out / "preflight.json", {"ok": False, "reason": meta["exception"]})
        print("ERROR: " + str(exc), file=sys.stderr)
    finally:
        meta.update(finished_at=timestamp(), phase=phase, launcher_rc=rc)
        write_json(out / "meta.json", meta)
    return rc


if __name__ == "__main__":
    sys.exit(main())
```
