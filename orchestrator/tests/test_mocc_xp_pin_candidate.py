# -*- coding: utf-8 -*-
"""Portable candidate source, routing, and committed compute-result contracts."""
from __future__ import annotations

import argparse
import copy
from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest import mock

from orchestrator.campaign import s3_mocc_lock_coverage as driver
from orchestrator.tests import test_mocc_proof_surface as legacy


ROOT = Path(__file__).resolve().parents[2]
BASE = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
# Parent's mk-C-amend.log and verify-candidate.log; never derived from JSON.
C = "68106660686232781bca3be792a750d3e19d7a8a"
TREE = "6dc0883c5bcc854eb6425101508b81a36bd7bf45"
BASE_BLOB = "1f4e9453c39a42451e652b3a28d791b90844f184"
BLOB = "e393efbfd5fad7bbe05117b43669ccc0f44abb6a"
SOURCE_SHA256 = "712e31b5cbf2a3a63df442d50203c5c0787c98c83672d49a20210719bf32ebe4"
RAW = ":100644 100644 1f4e9453c39a42451e652b3a28d791b90844f184 e393efbfd5fad7bbe05117b43669ccc0f44abb6a M\tcc/mocc/transaction.cc"
PATCH = ROOT / "patches/instr-mocc-lock-coverage-pin-candidate.patch"
POLICY = ROOT / "tools/pegasus/mocc_trace_v1_policy.json"
RUN_NAMES = {"stock_single", "stock_high", "lockskip_single", "lockskip_high",
             "perm_erase_single", "early_unlock_single"}
PATCHES = {
    "instrumentation": "patches/instr-mocc-lock-coverage-pin-candidate.patch",
    "lockskip": "patches/broken-mocc-lockskip-validation.patch",
    "permutation_erase": "patches/broken-mocc-permutation-erase.patch",
    "early_unlock": "patches/broken-mocc-early-unlock.patch",
}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _candidate_bytes() -> bytes:
    with legacy._source_root(PATCH) as source:
        return (source / driver.SOURCE_REL).read_bytes()


def _reject(call, exception=RuntimeError, message=None):
    try:
        call()
    except exception as exc:
        if message is not None:
            assert message in str(exc), str(exc)
    else:
        raise AssertionError("invalid control was accepted")


def test_candidate_source_contract():
    candidate = _candidate_bytes()
    with legacy._source_root(legacy._INSTRUMENTATION) as source:
        old = (source / driver.SOURCE_REL).read_bytes()
    assert old.count(b"#include <set>\n") == 1
    assert old.count(b"std::multiset<const void*>") == 2
    assert candidate == old.replace(b"#include <set>\n", b"").replace(
        b"std::multiset<const void*>", b"std::unordered_multiset<const void*>")
    with legacy._source_root() as source:
        base = (source / driver.SOURCE_REL).read_bytes()
    includes = lambda data: re.findall(rb"(?m)^\s*#include[^\n]*", data)
    assert includes(candidate) == includes(base)
    assert len(includes(candidate)) == 11
    text = candidate.decode()
    assert text.count("std::unordered_multiset<const void*>") == 2
    assert "std::multiset" not in text and "#include <set>" not in text
    header = _git(legacy._CCBENCH, "show", f"{BASE}:include/trace.hh")
    assert "#include <unordered_set>" in header
    legacy._assert_instr_source_contract(text)
    legacy._assert_instr_x_p_structure(text)
    assert _blob(candidate) == BLOB
    assert hashlib.sha256(candidate).hexdigest() == SOURCE_SHA256
    for patch in (legacy._LOCKSKIP, legacy._PERMUTATION, legacy._EARLY_UNLOCK):
        with legacy._source_root(PATCH, patch):
            pass


def test_candidate_trace0_logical_rows():
    with legacy._source_root() as source:
        base = legacy._source(source)
    rows = lambda text: legacy._logical_nonempty_rows(legacy._preprocess_trace_zero(text))
    assert rows(base) == rows(_candidate_bytes().decode())


def test_candidate_identity_checks():
    good = dict(oid=C, resolved=C + "\n", parent_line=f"{C} {BASE}\n",
                raw_diff=RAW + "\n", tree=TREE + "\n", reconstructed_blob=BLOB)
    record = driver._candidate_identity(**good)
    assert record == dict(oid=C, parents=[BASE], raw_diff=[RAW], tree=TREE,
                          base_blob=BASE_BLOB, candidate_blob=BLOB, reconstructed_blob=BLOB)
    for key, value in (
        ("resolved", "0" * 40),
        ("parent_line", f"{C} {'1' * 40}"),
        ("parent_line", f"{C} {BASE} {'1' * 40}"),
        ("parent_line", C),
        ("raw_diff", RAW + "\n" + RAW.replace("transaction.cc", "lock.cc")),
        ("raw_diff", RAW.replace(":100644 100644", ":100644 100755")),
        ("raw_diff", RAW.replace(":100644 100644", ":100755 100644")),
        ("raw_diff", RAW.replace(" M\t", " A\t")),
        ("raw_diff", RAW.replace(" M\t", " D\t")),
        ("raw_diff", RAW.replace("transaction.cc", "lock.cc")),
        ("reconstructed_blob", "0" * 40),
        ("tree", "bad-tree"),
    ):
        _reject(lambda: driver._candidate_identity(**{**good, key: value}))
    for invalid in (C.upper(), C[:8], " " + C, C + "\n", "g" * 40, "HEAD"):
        _reject(lambda: driver._candidate_oid(invalid), argparse.ArgumentTypeError)


def test_candidate_mode_source_routing():
    # Clone only BASE history into a disposable repo. No C object/ref is required.
    candidate = _candidate_bytes()
    expected = {None: candidate}
    for macro, patch in ((driver.LOCKSKIP_DEFINE, legacy._LOCKSKIP),
                         (driver.PERMUTATION_DEFINE, legacy._PERMUTATION),
                         (driver.EARLY_UNLOCK_DEFINE, legacy._EARLY_UNLOCK)):
        with legacy._source_root(PATCH, patch) as source:
            expected[macro] = (source / driver.SOURCE_REL).read_bytes()
    with tempfile.TemporaryDirectory(prefix="mocc-candidate-routing-") as raw:
        root = Path(raw)
        repo = root / "external" / "ccbench"
        repo.parent.mkdir()
        _git(root, "clone", "--quiet", "--no-checkout", str(legacy._CCBENCH), str(repo))
        _git(repo, "checkout", "--quiet", "--detach", BASE)
        legacy._apply_patch(repo, PATCH)
        _git(repo, "add", driver.SOURCE_REL)
        _git(repo, "-c", "user.name=Routing fixture", "-c", "user.email=fixture@example.invalid",
             "commit", "--quiet", "-m", "Portable routing fixture")
        oid = _git(repo, "rev-parse", "HEAD")
        assert _git(repo, "rev-parse", f"HEAD:{driver.SOURCE_REL}") == BLOB
        (root / "patches").mkdir()
        for relative in (*PATCHES.values(), driver.INSTRUMENTATION_PATCH):
            shutil.copyfile(ROOT / relative, root / relative)
        policy = json.loads(POLICY.read_text())
        toolchain = {"version_body_sha256": policy["expected_compiler_version_body_sha256"],
                     "cc_path": "/fixture/gcc", "cxx_path": "/fixture/g++"}
        builds, verifications, traces = {}, [], {}

        def build(source, build_root, *, trace, macro=None, **kwargs):
            head = _git(source, "rev-parse", "HEAD")
            data = (source / driver.SOURCE_REL).read_bytes()
            if build_root.name == "trace0-pin0":
                assert head == BASE and trace == 0 and macro is None
                assert _blob(data) == BASE_BLOB
            else:
                assert head == oid
                assert data == expected[macro]
                assert trace == (0 if build_root.name == "trace0-cand" else 1)
            build_root.mkdir()
            binary = build_root / "ycsb_mocc.exe"
            # Real nm/strings/objdump can inspect this harmless stand-in.
            shutil.copyfile("/bin/true", binary)
            builds[binary] = (source, trace, macro)
            return binary, ({"macro": macro} if macro else None)

        def run_trace(binary, flags):
            source, trace, macro = builds[binary]
            assert trace == 1
            assert flags in (driver.SINGLE_FLAGS, driver.HIGH_FLAGS)
            directory = Path(tempfile.mkdtemp(dir=root))
            reasons = []
            if macro in (driver.LOCKSKIP_DEFINE, driver.EARLY_UNLOCK_DEFINE):
                reasons = ["lock-lost-before-write", "lock-lost-before-publish"]
                if macro == driver.LOCKSKIP_DEFINE:
                    reasons.insert(0, "not-locked-at-entry")
            p = int(macro == driver.PERMUTATION_DEFINE)
            (directory / "trace_0.log").write_text(
                "W 1 01 U\n" + "".join(f"X 1 01 {r}\n" for r in reasons)
                + ("P size-changed\n" if p else ""))
            traces[directory] = (source, len(reasons), p)
            return directory

        actual_run = driver._run_checked

        def process(argv, **kwargs):
            if len(argv) > 2 and argv[1:3] == ["-m", "verifier"]:
                directory = Path(argv[3])
                source, x, p = traces[directory]
                assert Path(argv[argv.index("--ccbench-root") + 1]) == source
                assert argv[argv.index("--protocol") + 1] == "mocc"
                assert source.is_dir()
                verifications.append(source)
                integrity = dict.fromkeys(("orphan_reads", "version_dups", "dup_txids",
                    "genesis_commits", "missing_txids", "write_version_mismatch", "malformed_keys",
                    "framing_violations", "framing_violation_details", "write_intent_violations"), 0)
                integrity.update(lock_coverage_violations=x, permutation_violations=p)
                record = dict(verdict="indeterminate" if x or p else "serializable",
                              certified=not (x or p), total_cycles=0, integrity=integrity,
                              stats={"txns": 1})
                return subprocess.CompletedProcess(argv, 0, json.dumps({"results": [record]}), "")
            return actual_run(argv, **kwargs)

        argv = ["--candidate-oid", oid, "--third-party-cache", str(root), "--policy", str(POLICY)]
        with ExitStack() as stack:
            for obj, name, options in (
                (driver, "_repo_root", dict(return_value=root)),
                (driver.site_policy, "current_site", dict(return_value="PEGASUS_COMPUTE")),
                (driver.site_policy, "refuses_heavy_work", dict(return_value=False)),
                (driver, "_assert_single_tenant", dict(return_value=None)),
                (driver, "_prepare_dependencies", dict(return_value={})),
                (driver, "_resolve_toolchain", dict(return_value=toolchain)),
                (driver, "_build_variant", dict(side_effect=build)),
                (driver, "_run_trace", dict(side_effect=run_trace)),
                (driver, "_run_checked", dict(side_effect=process)),
            ):
                stack.enter_context(mock.patch.object(obj, name, **options))
            with redirect_stdout(io.StringIO()):
                assert driver.main(argv) == 0
            payload = json.loads((root / driver.CANDIDATE_OUTPUT).read_text())
            assert set(payload["runs"]) == RUN_NAMES
            assert all(r["other_integrity_clean"] is True for r in payload["runs"].values())
            assert len(builds) == 6 and len(verifications) == 6
            assert {b.parent.name for b in builds} == {
                "stock-trace1", "lockskip-trace1", "perm-trace1", "early-trace1",
                "trace0-pin0", "trace0-cand"}
            assert len("trace0-pin0") == len("trace0-cand")
            for name in ("s3_mocc_lock_coverage.json", "s3_mocc_mutation_proof.json",
                         "s3_mocc_template_proof.json"):
                out = root / "output/env/pegasus/calibration" / name
                _reject(lambda: driver.main(argv + ["--out", str(out)]), message="legacy JSON")
                assert not out.exists()
            # A real BASE child with a different blob must stop before ANY build.
            (repo / driver.SOURCE_REL).write_bytes(candidate + b"\n")
            _git(repo, "add", driver.SOURCE_REL)
            _git(repo, "-c", "user.name=Routing fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "--amend", "--no-edit")
            bad_oid = _git(repo, "rev-parse", "HEAD")
            bad_argv = [bad_oid if item == oid else item for item in argv]
            builds.clear()
            _reject(lambda: driver.main(bad_argv), message="reconstructed blob differs")
            assert not builds


def _consume(payload: dict, reconstructed: bytes) -> None:
    assert payload["schema_version"] == "s3-mocc-xp-pin-candidate/v1"
    assert payload["ccbench_commit"] == C and payload["base_commit"] == BASE
    assert payload["all_pass"] is True
    assert set(payload["checks"]) == set(legacy._CHECK_KEYS) == set(driver.CHECK_KEYS)
    assert all(value is True for value in payload["checks"].values())
    candidate = payload["candidate"]
    for key, expected in dict(oid=C, parents=[BASE], tree=TREE, raw_diff=[RAW],
                              base_blob=BASE_BLOB, candidate_blob=BLOB,
                              reconstructed_blob=BLOB, candidate_source_sha256=SOURCE_SHA256).items():
        assert candidate[key] == expected, key
    assert _blob(reconstructed) == BLOB
    assert hashlib.sha256(reconstructed).hexdigest() == SOURCE_SHA256
    assert set(payload["patches"]) == set(PATCHES)
    for name, relative in PATCHES.items():
        assert payload["patches"][name] == {
            "path": relative, "sha256": hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}
    assert candidate["patch"] == payload["patches"]["instrumentation"]
    assert set(payload["runs"]) == RUN_NAMES
    assert all(type(run["other_integrity_clean"]) is bool for run in payload["runs"].values())
    assert payload["diagnostic_build_admission"] == driver.non_admissible_materializer(
        "orchestrator.campaign.s3_mocc_lock_coverage._build_variant")
    policy = json.loads(POLICY.read_text())
    assert payload["policy"]["sha256"] == hashlib.sha256(POLICY.read_bytes()).hexdigest()
    assert payload["toolchain"]["version_body_sha256"] == policy["expected_compiler_version_body_sha256"]
    assert all(Path(payload["toolchain"][role]).is_absolute() for role in ("cc_path", "cxx_path"))


def test_candidate_json_is_bound():
    reconstructed = _candidate_bytes()
    # Independent positive fixture permits rejection controls even before compute JSON exists.
    control = dict(schema_version="s3-mocc-xp-pin-candidate/v1", ccbench_commit=C,
        base_commit=BASE, all_pass=True, checks=dict.fromkeys(legacy._CHECK_KEYS, True),
        candidate=dict(oid=C, parents=[BASE], tree=TREE, raw_diff=[RAW], base_blob=BASE_BLOB,
            candidate_blob=BLOB, reconstructed_blob=BLOB, candidate_source_sha256=SOURCE_SHA256),
        patches={name: dict(path=relative, sha256=hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
                 for name, relative in PATCHES.items()},
        runs={name: {"other_integrity_clean": True} for name in RUN_NAMES},
        diagnostic_build_admission=driver.non_admissible_materializer(
            "orchestrator.campaign.s3_mocc_lock_coverage._build_variant"),
        policy={"sha256": hashlib.sha256(POLICY.read_bytes()).hexdigest()},
        toolchain=dict(cc_path="/fixture/gcc", cxx_path="/fixture/g++",
            version_body_sha256=json.loads(POLICY.read_text())["expected_compiler_version_body_sha256"]))
    control["candidate"]["patch"] = copy.deepcopy(control["patches"]["instrumentation"])
    _consume(control, reconstructed)
    for path in (("ccbench_commit",), ("candidate", "reconstructed_blob"),
                 ("candidate", "oid"), ("candidate", "tree"), ("candidate", "base_blob"),
                 ("candidate", "candidate_blob"), ("candidate", "candidate_source_sha256")):
        changed = copy.deepcopy(control)
        target = changed
        for key in path[:-1]:
            target = target[key]
        value = target[path[-1]]
        target[path[-1]] = ("0" if value[0] != "0" else "1") + value[1:]
        _reject(lambda: _consume(changed, reconstructed), AssertionError)
    payload = json.loads((ROOT / driver.CANDIDATE_OUTPUT).read_text(encoding="utf-8"))
    _consume(payload, reconstructed)


def _run() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001 - fail-closed plain harness
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
