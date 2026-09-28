"""Pure Cicada lifetime contracts and the default patch preprocessing witness."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from orchestrator.campaign import vhash_cicada_vlife as V

ROOT = Path(__file__).resolve().parents[2]
TOUCHED = (
    "cc/cicada/include/transaction.hh",
    "cc/cicada/transaction.cc",
    "cc/cicada/util.cc",
    "cc/cicada/ycsb_cicada.cc",
)


def _worker():
    return {
        "hops": [[0] * 18 for _ in V.SITES],
        "position": [[0] * 18 for _ in V.SITES],
        "no_scan": [0] * 8,
        "deep": [0] * 5, "candidate": [0] * 5, "readonly_deep": [0] * 5,
        "readonly_attempt": 0, "readonly_commit": 0,
        "deep_read_zero": [0] * 5, "candidate_read_zero": [0] * 5,
        "install": 0, "detach": 0, "gc_negative": 0,
        "gc_boundary_us": [0] * 42, "gc_publish_us": [0] * 42,
        "age_create_us": [0] * 42, "age_overwrite_us": [0] * 42,
        "attempts": [0] * 2, "commits": [0] * 2, "aborts": [0] * 2,
        "operations": [0] * 2, "cycles": [0] * 2,
    }


def _payload():
    return {"schema_version": 1, "clocks_per_us": 2100,
            "bucket_bounds": [0,1,2,3,4,5,6,7,8,16,32,64,128,256,512,1024,2048,
                              18446744073709551615],
            "time_bucket_bounds": V.TIME_BOUNDS,
            "position_origin": V.POSITION_ORIGIN,
            "sites": list(V.SITES),
            "build": {"reuse_version": 1, "inline_version_opt": 0, "longtx": 1},
            "workers": [_worker(), _worker()]}


def _line(payload):
    return V.PREFIX + json.dumps(payload)


def test_json_line_contract():
    payload = _payload()
    assert V.parse_vlife_line("noise\n" + _line(payload) + "\n") == payload
    for text in ("noise", _line(payload) + "\n" + _line(payload),
                 V.PREFIX + '{"schema_version":1,"schema_version":1}'):
        try:
            V.parse_vlife_line(text)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid JSON line accepted")
    for mutate in (
        lambda p: p.update(extra=1),
        lambda p: p.pop("workers"),
        lambda p: p["workers"][0].update(deep_read_zero=[-1,0,0,0,0]),
        lambda p: p["workers"][0].update(candidate=[1,0,0,0,0]),
    ):
        p = _payload()
        mutate(p)
        try:
            V.parse_vlife_line(_line(p))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid payload accepted")


def test_worker_sum_and_readonly_denominator():
    p = _payload()
    p["workers"][0]["deep"][0] = 2
    p["workers"][1]["deep"][0] = 3
    p["workers"][0]["hops"][0][0] = 2
    p["workers"][1]["hops"][0][0] = 3
    p["workers"][0]["candidate"][0] = 1
    p["workers"][0]["deep_read_zero"][0] = 1
    p["workers"][0]["candidate_read_zero"][0] = 1
    p["workers"][0]["readonly_deep"][0] = 100
    p["workers"][0]["hops"][1][0] = 100
    p["workers"][0]["install"] = 7
    p["workers"][1]["detach"] = 2
    parsed = V.parse_vlife_line(_line(p))
    summary = V.summarize(parsed)
    assert summary["deep"][0] == 5
    assert summary["candidate_rate"][0] == 0.2
    assert summary["deep_read_zero"][0] == 1
    assert summary["candidate_read_zero"][0] == 1
    assert summary["readonly_deep"][0] == 100
    assert summary["logical_version_delta"] == 5


def test_k_boundary_and_condition_subset():
    assert "+  for (size_t i=0; i<5; ++i) if (vlife_pos >= ks[i]) {" in (
        ROOT / "patches/instr-cicada-version-lifetime.patch").read_text()
    for k in V.K:
        assert not V.depth_at_k(k-1, k)
        assert V.depth_at_k(k, k)
    assert V.select_conditions("A-none-gc10,B-ops1000-gc100000") == (
        "A-none-gc10", "B-ops1000-gc100000")
    for value in ("A-none-gc10,A-none-gc10", "unknown", "", "A-none-gc10,"):
        try:
            V.select_conditions(value)
        except ValueError:
            pass
        else:
            raise AssertionError("bad condition list accepted")


def test_real_patch_define_registry_and_rejection():
    from orchestrator.campaign import condition_meaning_gate as gate
    patch = ROOT / "patches/instr-cicada-version-lifetime.patch"
    source = patch.read_text()
    for macro in V.MACROS:
        spec = gate.DEFINE_SPECS[macro]
        assert spec.patch_rel == "patches/instr-cicada-version-lifetime.patch"
        assert spec.target == "ycsb_cicada.exe"
        assert spec.route == gate.ROUTE_CMAKE_CXX_FLAGS
        assert ("+#if " + macro) in source
        request = gate.make_define_request(
            driver_id=V.DRIVER_ID, macro=macro,
            requested_value=1, default_value=0)
        assert gate._validate_define_request(request)[0] == spec
    try:
        gate._validate_define_request(gate.make_define_request(
            driver_id=V.DRIVER_ID, macro="IZANAGI_CICADA_UNREGISTERED",
            requested_value=1, default_value=0))
    except gate.ConditionMeaningGateError:
        pass
    else:
        raise AssertionError("unknown macro accepted")


def _rows(source: str):
    cxx = shutil.which("g++")
    if cxx is None:
        raise AssertionError("g++ required for preprocessing witness")
    includes = re.findall(r"(?m)^[ \t]*#[ \t]*include\b.*$", source)
    source = re.sub(r"(?m)^[ \t]*#[ \t]*include\b.*$", "", source)
    result = subprocess.run([cxx, "-E", "-nostdinc", "-x", "c++", "-"],
                            input=source, text=True, capture_output=True, check=True)
    logical = None
    filename = None
    rows = []
    for raw in result.stdout.splitlines():
        match = re.fullmatch(r'#\s+(\d+)\s+"([^"]+)"(?:\s+\d+)*', raw)
        if match:
            logical = int(match.group(1))
            filename = match.group(2)
        elif logical is not None:
            if raw.strip():
                rows.append((logical, filename, raw))
            logical += 1
    return includes, rows


def test_smoke_identity_binds_records():
    with tempfile.TemporaryDirectory(prefix="cvl-smoke-test-") as td:
        path = Path(td) / "smoke.json"
        raw = {"schema_version": 1, "command": "smoke", "ccbench_commit": V.PIN,
               "patch_sha256": hashlib.sha256(V.PATCH.read_bytes()).hexdigest(),
               "calibration": {"selected_records": 2000000}}
        path.write_text(json.dumps(raw))
        assert V._smoke_records(path) == 2000000
        raw["patch_sha256"] = "0" * 64
        path.write_text(json.dumps(raw))
        try:
            V._smoke_records(path)
        except ValueError:
            pass
        else:
            raise AssertionError("mismatched patch accepted")


def test_patch_default_preprocess_matches_stock():
    stock = ROOT / "external/ccbench"
    patch = ROOT / "patches/instr-cicada-version-lifetime.patch"
    with tempfile.TemporaryDirectory(prefix="cicada-preprocess-") as temporary:
        root = Path(temporary)
        for rel in TOUCHED:
            destination = root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((stock / rel).read_bytes())
        subprocess.run(["git", "-C", str(root), "apply", str(patch)],
                       check=True, capture_output=True)
        for rel in TOUCHED:
            assert _rows((stock / rel).read_text()) == _rows((root / rel).read_text()), rel


def _run():
    tests = (test_json_line_contract, test_worker_sum_and_readonly_denominator,
             test_k_boundary_and_condition_subset,
             test_real_patch_define_registry_and_rejection,
             test_patch_default_preprocess_matches_stock,
             test_smoke_identity_binds_records)
    failed = 0
    for test in tests:
        try:
            test()
            print("PASS", test.__name__)
        except Exception as exc:
            print("FAIL", test.__name__, type(exc).__name__, exc)
            failed += 1
    return int(bool(failed))


if __name__ == "__main__":
    sys.exit(_run())
