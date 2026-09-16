# probe test の逐語 (probe branch tip e35fb7c4e の orchestrator/tests/test_t2630_scan_boundary_reach.py、sha256 55504495456d808e54ee9845e688c753948032827830ad4a653a7ae27af5c771、17695 bytes。repo には .py を残さない)

```python
"""Temporary T-2630 probe. Run on compute with -n 0; no product gate changes."""
from __future__ import annotations

import difflib
import functools
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import traceback
from datetime import datetime, timezone

from orchestrator.campaign import (
    buildcache, condition_meaning_gate as gate, model, p3_s4_loop,
    patchharness, site_policy, source_digest,
)

PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
REPO = Path(__file__).resolve().parents[2]
CARRIER = "patches/silo-backoff-fixed.patch"
EVIDENCE_ROOT = Path(
    "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2630-scan-boundary-reach/evidence"
)
CACHE = Path("/work/1/SFC/tanab/izanagi-thirdparty-cache")
CACHE_NAMES = ("masstree", "mimalloc", "googletest")
PREFIX = (
    "/work/SFC/tanab/ss2pl-study-deps/gflags-install;"
    "/work/SFC/tanab/ss2pl-study-deps/glog-install"
)
GENOMES = {"stock": model.Genome("silo", {"BACKOFF_FIXED": -1}),
           "variant": model.Genome("silo", {"BACKOFF_FIXED": 1})}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json_value(value):
    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": _sha(value)}
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


class _Observation:
    def __init__(self):
        self.results = {}
        self.evidence = None

    def save(self, name, raw):
        path = self.evidence / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        print(f"T2630 bytes={path} size={len(raw)} sha256={_sha(raw)}", flush=True)
        return raw

    def stage(self, key, action):
        try:
            value = action()
            self.results[key] = {"ok": True, "value": value}
            return value
        except Exception as exc:
            self.results[key] = {"ok": False, "stage": key,
                                 "exception": type(exc).__name__, "detail": str(exc),
                                 "traceback": traceback.format_exc()}
            print(f"T2630 failure stage={key} {type(exc).__name__}: {exc}", flush=True)
            return None

    def require(self, key):
        result = self.results.get(key)
        assert result is not None, f"unobserved stage={key}; evidence={self.evidence}"
        assert result["ok"], f"evidence={self.evidence}; {result}"
        return result["value"]

    def command(self, key, argv, cwd=None):
        argv = [str(arg) for arg in argv]
        metadata = {"argv": argv, "cwd": str(cwd or Path.cwd()), "rc": None}
        self.save(key + ".command.json", json.dumps(metadata, indent=2).encode())
        try:
            proc = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=300)
        except subprocess.TimeoutExpired as exc:
            self.save(key + ".stdout", exc.stdout or b"")
            self.save(key + ".stderr", exc.stderr or b"")
            raise
        self.save(key + ".stdout", proc.stdout)
        self.save(key + ".stderr", proc.stderr)
        self.save(key + ".command.json", json.dumps({
            "argv": argv, "cwd": str(cwd or Path.cwd()), "rc": proc.returncode,
        }, indent=2).encode())
        if proc.returncode:
            raise RuntimeError(f"{key}: rc={proc.returncode}: "
                               + proc.stderr.decode(errors="replace"))
        return proc.stdout

    def manifest(self):
        self.save("observations.json", json.dumps(
            self.results, indent=2, sort_keys=True, default=_json_value,
        ).encode())


def _inventory(obs, label):
    inventory = {}
    for name in CACHE_NAMES:
        root = CACHE / name
        if not root.is_dir():
            raise FileNotFoundError(root)
        # Include ignored/untracked files and symlink targets; never write here.
        for path in sorted(root.rglob("*")):
            relative = f"{name}/{path.relative_to(root)}"
            if path.is_symlink():
                inventory[relative] = {"link": os.readlink(path),
                                       "sha256": _sha(path.read_bytes())
                                       if path.is_file() else None}
            elif path.is_file():
                inventory[relative] = {"sha256": _sha(path.read_bytes())}
    obs.save(f"cache-{label}.json", json.dumps(inventory, sort_keys=True).encode())
    return inventory


def _compilers(obs):
    paths = []
    for label, name in zip(("cc", "cxx"), buildcache.compilers_for_current_site()):
        found = shutil.which(name)
        if found is None:
            raise FileNotFoundError(f"site compiler {label}={name} unavailable")
        path = Path(found).resolve(strict=True)
        version = obs.command(f"compiler-{label}", [path, "--version"])
        obs.save(f"compiler-{label}.json", json.dumps({
            "requested": name, "path": str(path),
            "executable_sha256": _sha(path.read_bytes()),
            "version_sha256": _sha(version),
        }, indent=2).encode())
        paths.append(path)
    return tuple(paths)


def _resolve(obs, key, genome, wt, cxx):
    token = source_digest.resolve(genome, PIN, ccbench_dir=str(wt), cxx=str(cxx))
    obs.save(key + "/token.txt", token.encode("utf-8"))
    return token


def _resolve_evidence(obs, key, genome, wt, cxx):
    evidence = source_digest.resolve_evidence(
        genome, PIN, ccbench_dir=str(wt), cxx=str(cxx),
    )
    receipt = evidence.as_receipt()
    receipt["verification_variant"] = evidence.verification_variant
    obs.save(key + "/source-evidence.json", json.dumps(receipt, indent=2).encode())
    return receipt


def _object_argv(argv, object_path, dependency_path):
    """Keep the real compilation flags; relocate output destinations only."""
    result = [argv[0]]
    destinations = {"-o": object_path, "-MF": dependency_path,
                    "-MJ": object_path.with_suffix(".json"),
                    "--serialize-diagnostics": object_path.with_suffix(".dia")}
    index = 1
    output_seen = False
    while index < len(argv):
        arg = argv[index]
        if arg in destinations:
            result.extend((arg, str(destinations[arg])))
            output_seen |= arg == "-o"
            index += 2
            continue
        prefix = next((p for p in ("-o", "-MF", "-MJ")
                       if arg.startswith(p) and arg != p), None)
        if prefix:
            result.append(prefix + str(destinations[prefix]))
            output_seen |= prefix == "-o"
        else:
            result.append(arg)
        index += 1
    assert "-c" in result, "owner command is not a compilation"
    assert output_seen, "owner command lacks object output"
    return result


def _observe_object(obs, key, argv, cwd, build):
    # Identical object path prevents objdump banners from manufacturing a diff.
    obj = build / "t2630-owner.o"
    obj.unlink(missing_ok=True)
    obs.command(key + "/compile", _object_argv(argv, obj, build / "t2630-object.d"), cwd)
    raw = obj.read_bytes()
    assert raw, "empty object"
    obs.save(key + "/owner.o", raw)
    dump = obs.command(key + "/objdump", ["objdump", "-drC", obj], cwd)
    assert dump, "empty objdump"
    return dump


def _observe_tu(obs, key, genome, wt, scratch, cc, cxx):
    build = scratch / ("build-" + key.split("/")[1])
    build.mkdir(exist_ok=True)
    for name in CACHE_NAMES:
        if not (CACHE / name).is_dir():
            raise FileNotFoundError(CACHE / name)
    cmake = shutil.which("cmake")
    if cmake is None:
        raise FileNotFoundError("cmake unavailable")
    args = p3_s4_loop._condition_gate_offline_configure_args(
        dependency_prefix=PREFIX, fetchcontent_base_dir=str(scratch / "fetchcontent"),
        masstree_source_dir=str(CACHE / "masstree"),
        mimalloc_source_dir=str(CACHE / "mimalloc"),
        googletest_source_dir=str(CACHE / "googletest"),
    ) + ("-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
         f"-DCMAKE_C_COMPILER={cc}", "-DCCBENCH_TRACE=0", *genome.cmake_defines())
    obs.save(key + "/configure-input.json", json.dumps(args).encode())
    captured = gate.capture_define_inputs(wt, configure_args=args)
    request = gate.make_define_request(
        driver_id="t2630-scan-boundary-reach", macro="BACKOFF_FIXED",
        requested_value=genome.flags["BACKOFF_FIXED"], default_value=-1,
    )
    configured = obs.stage(key + "/configure", lambda: gate._configure_compile_commands(
        captured=captured, request=request, source_root=wt, build_root=build,
        value=str(genome.flags["BACKOFF_FIXED"]), companions=(),
        compiler=cxx, cmake=Path(cmake).resolve(),
    ))
    if configured is None:
        obs.require(key + "/configure")
    # Retain the actual argv and database, rather than serializing an internal object.
    obs.results[key + "/configure"]["value"] = {
        "configure_argv": configured.configure_argv, "commands": configured.commands,
    }
    entry, owner = gate._select_owner_entry(configured.commands, source_root=wt, request=request)
    assert owner == wt / "cc/silo/transaction.cc"
    argv = gate._entry_argv(entry)
    assert Path(argv[0]).resolve() == cxx, (argv[0], cxx)
    defines = []
    for index, arg in enumerate(argv):
        if arg == "-D":
            defines.append(argv[index + 1])
        elif arg.startswith("-D"):
            defines.append(arg[2:])
    for name, value in (("BACKOFF_FIXED", genome.flags["BACKOFF_FIXED"]), ("TRACE", 0)):
        assert [d for d in defines if d.partition("=")[0] == name] == [f"{name}={value}"]
    obs.save(key + "/owner-command.json", json.dumps(dict(entry), indent=2).encode())
    dep = build / "t2630-preprocess.d"
    pp, _ = gate._preprocess_argv(argv, source_root=wt, build_root=build,
                                 dependency_path=dep, allowed_defines=frozenset())

    def preprocess():
        raw = obs.command(key + "/preprocess", pp, entry["directory"])
        assert raw.strip(), "empty owner TU preprocessing stdout"
        obs.save(key + "/owner.ii", raw)
        obs.save(key + "/dependencies.txt", dep.read_bytes())
        return raw

    raw = obs.stage(key + "/preprocess", preprocess)
    obs.stage(key + "/object", lambda: _observe_object(
        obs, key, argv, entry["directory"], build,
    ))
    if raw is None:
        obs.require(key + "/preprocess")
    return raw


def _compare_bytes(obs, name, before, after):
    different = before != after
    if different:
        diff = b"".join(difflib.diff_bytes(
            difflib.unified_diff, before.splitlines(keepends=True),
            after.splitlines(keepends=True), fromfile=b"reference", tofile=b"current",
        ))
        obs.save(name + ".diff.txt", diff)
    return {"different": different, "reference_sha256": _sha(before),
            "current_sha256": _sha(after)}


def _run(obs):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    obs.evidence = EVIDENCE_ROOT / f"{socket.gethostname()}-{stamp}-{os.getpid()}"
    obs.evidence.mkdir(parents=True, exist_ok=False)
    print(f"T2630 evidence dir={obs.evidence}", flush=True)
    scratch = Path(tempfile.mkdtemp(prefix="t2630-", dir=os.environ.get("TMPDIR") or "/tmp"))
    old_tmpdir = os.environ.get("TMPDIR")
    os.environ["TMPDIR"] = str(scratch)
    try:
        obs.save("environment.json", json.dumps({
            "hostname": socket.gethostname(), "repo": str(REPO),
            "site": site_policy.current_site(),
            "scratch": str(scratch), "evidence": str(obs.evidence), "pin": PIN,
            "genomes": {k: g.canonical() for k, g in GENOMES.items()},
        }, indent=2).encode())
        obs.stage("filesystems", lambda: obs.command(
            "filesystems", ["df", "-PT", scratch, obs.evidence, CACHE]))
        head = obs.command("superproject-head", ["git", "rev-parse", "HEAD"], REPO).decode().strip()
        patches = {
            "reference": obs.command("reference-patch", ["git", "show", f"{head}:{CARRIER}"], REPO),
            "current": (REPO / CARRIER).read_bytes(),
        }
        for side, raw in patches.items():
            obs.save(side + "/carrier.txt", raw)
        compilers = obs.stage("compilers", lambda: _compilers(obs))
        clone = scratch / "clone"
        obs.command("clone", ["git", "clone", "--no-hardlinks", "--no-checkout",
                              REPO / "external/ccbench", clone])
        obs.command("pin", ["git", "cat-file", "-e", PIN + "^{commit}"], clone)
        obs.command("pin-tree", ["git", "rev-parse", PIN + "^{tree}"], clone)
        shared_id = patchharness._git_repository_identity(str(REPO / "external/ccbench"))
        clone_id = patchharness._git_repository_identity(str(clone))
        assert clone_id[0] != shared_id[0] and clone_id[1] != shared_id[1]
        patchharness._guard_real_shared_checkout(str(clone))
        obs.save("common-dirs.json", json.dumps({"shared": shared_id, "clone": clone_id}).encode())
        before = obs.stage("cache/before", lambda: _inventory(obs, "before"))
        try:
            with patchharness.checkout(PIN, base_dir=str(clone)) as root:
                wt = Path(root)
                obs.save("worktree.txt", str(wt).encode())
                obs.stage("worktree-filesystem", lambda: obs.command(
                    "worktree-filesystem", ["df", "-PT", wt]))
                for side, raw in patches.items():
                    carrier = scratch / f"{side}.txt"
                    carrier.write_bytes(raw)

                    def observe_side():
                        with patchharness.applied(str(carrier), PIN, ccbench_dir=str(wt)):
                            if compilers is None:
                                return
                            cc, cxx = compilers
                            for name, genome in GENOMES.items():
                                key = f"{side}/{name}"
                                obs.stage(key + "/resolve", lambda: _resolve(
                                    obs, key, genome, wt, cxx))
                                obs.stage(key + "/preimage", lambda: obs.save(
                                    key + "/preimage.bin", source_digest.canonical_source_preimage_bytes(
                                        genome, ccbench_dir=str(wt), cxx=str(cxx))))
                                obs.stage(key + "/evidence", lambda: _resolve_evidence(
                                    obs, key, genome, wt, cxx))
                                if side == "current":
                                    obs.stage(key + "/trace", lambda: source_digest.assert_trace_diff_matches_head(
                                        genome, PIN, str(wt), str(cxx)))
                                obs.stage(key + "/tu", lambda: _observe_tu(
                                    obs, key, genome, wt, scratch, cc, cxx))

                    obs.stage(side + "/apply-restore", observe_side)
        finally:
            after = obs.stage("cache/after", lambda: _inventory(obs, "after"))
            if before is not None and after is not None:
                obs.results["cache/change"] = {"ok": True, "value": {
                    "different": before != after,
                    "changed_paths": sorted(k for k in before.keys() | after.keys()
                                            if before.get(k) != after.get(k)),
                }}
        for name in GENOMES:
            for stage in ("tu", "object", "preimage"):
                records = [obs.results.get(f"{side}/{name}/{stage}")
                           for side in ("reference", "current")]
                if all(r is not None and r["ok"] for r in records):
                    obs.stage(f"comparison/{name}/{stage}", lambda: _compare_bytes(
                        obs, f"{name}-{stage}", records[0]["value"], records[1]["value"]))
    finally:
        if old_tmpdir is None:
            os.environ.pop("TMPDIR", None)
        else:
            os.environ["TMPDIR"] = old_tmpdir
        shutil.rmtree(scratch)


@functools.lru_cache(maxsize=1)
def _observations():
    # Called inside test bodies, never in fixture setup: failures produce FAILED.
    obs = _Observation()
    obs.stage("run", lambda: _run(obs))
    if obs.evidence is not None and obs.evidence.is_dir():
        obs.stage("manifest", obs.manifest)
    return obs


def _pair(capsys, name, stage):
    with capsys.disabled():
        obs = _observations()
    obs.require("run")
    obs.require("manifest")
    obs.require("compilers")
    values = []
    for side in ("reference", "current"):
        obs.require(side + "/apply-restore")
        # TU equality requires successful resolution, not token equality.
        token = obs.require(f"{side}/{name}/resolve")
        values.append(token if stage == "resolve" else obs.require(f"{side}/{name}/{stage}"))
    return values


def test_stock_identity(capsys, _detect_site_under_test):
    reference, current = _pair(capsys, "stock", "resolve")
    assert reference == "stock"
    assert current == "stock"


def test_variant_identity(capsys, _detect_site_under_test):
    reference, current = _pair(capsys, "variant", "resolve")
    assert reference != "stock"
    assert current == reference


def test_stock_owner_tu(capsys, _detect_site_under_test):
    reference, current = _pair(capsys, "stock", "tu")
    assert current == reference, "stock TU differs; see stock-tu.diff.txt in evidence dir"


def test_variant_owner_tu(capsys, _detect_site_under_test):
    reference, current = _pair(capsys, "variant", "tu")
    assert current == reference, "variant TU differs; see variant-tu.diff.txt in evidence dir"
```
