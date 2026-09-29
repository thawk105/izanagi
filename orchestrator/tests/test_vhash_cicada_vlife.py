"""Pure Cicada lifetime contracts and the default patch preprocessing witness."""
from __future__ import annotations

import json
import hashlib
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from contextlib import nullcontext

from orchestrator.campaign import vhash_cicada_vlife as V

ROOT = Path(__file__).resolve().parents[2]
TOUCHED = (
    "cc/cicada/include/transaction.hh",
    "cc/cicada/transaction.cc",
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


def _payload2():
    payload = _payload()
    payload["schema_version"] = 2
    payload["build"].update(izanagi_ronly_pct=-1, izanagi_long_kind=0)
    scalar_fields = ("readonly_reads", "gc_boundary_sum_us", "gc_boundary_count",
                     "gc_publish_sum_us", "gc_publish_count", "gc_publish_negative",
                     "gc_boundary_overflow", "gc_publish_overflow", "ro_snapshot_age_sum_us",
                     "ro_snapshot_age_count", "ro_snapshot_age_negative",
                     "ro_snapshot_age_overflow", "gc_same",
                     "dc_cf_wait_sum_us", "dc_ro_gap_sum_us", "dc_leader_wait_sum_us",
                     "dc_interval_sum_us",
                     "dc_count", "dc_first", "dc_missing", "dc_generation",
                     "dc_negative", "dc_leader_count", "holder_count", "holder_unresolved")
    for worker in payload["workers"]:
        worker.update({field: 0 for field in scalar_fields})
        worker.update(readonly_candidate=[0] * 5, ro_snapshot_age_us=[0] * 42,
                      dc_cf_kind_count=[0] * 5, dc_cf_kind_sum_us=[0] * 5,
                      holder_units=[0] * 5)
    return payload


def _payload2_tuned():
    payload = _payload2()
    payload["build"]["inline_version_opt"] = 1
    return payload


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


def test_schema2_required_fields_and_three_term_identity():
    p = _payload2()
    p["workers"][0].update(gc_boundary_count=2, gc_publish_count=1,
                            gc_publish_sum_us=10, dc_first=1, dc_count=1,
                            dc_cf_wait_sum_us=3, dc_ro_gap_sum_us=4,
                            dc_leader_wait_sum_us=3, dc_interval_sum_us=10)
    p["workers"][0]["gc_boundary_us"][0] = 2
    p["workers"][0]["gc_publish_us"][4] = 1
    p["workers"][0]["dc_cf_kind_count"][3] = 1
    p["workers"][0]["dc_cf_kind_sum_us"][3] = 3
    assert V.parse_vlife_line(_line(p)) == p
    for change in (
        lambda q: q["workers"][0].pop("readonly_reads"),
        lambda q: q["workers"][0].update(extra=0),
        lambda q: q["workers"][0].update(dc_ro_gap_sum_us=5),
        lambda q: q["workers"][0].update(readonly_candidate=[1, 0, 0, 0, 0]),
        lambda q: q["workers"][0].update(ro_snapshot_age_us=[0]),
        lambda q: q["workers"][0].update(gc_publish_sum_us=-1),
    ):
        q = json.loads(json.dumps(p))
        change(q)
        try:
            V.parse_vlife_line(_line(q))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid schema 2 payload accepted")


def test_schema2_readonly_denominator_and_holder_weights():
    p = _payload2()
    w = p["workers"][0]
    w["readonly_reads"] = 4
    w["readonly_deep"][0] = 2
    w["readonly_candidate"][0] = 1
    w["hops"][1][0] = 100
    w["gc_boundary_count"] = 1
    w["gc_boundary_us"][0] = 1
    w["holder_count"] = 1
    w["holder_units"][3] = 500000
    w["holder_units"][4] = 500000
    parsed = V.parse_vlife_line(_line(p))
    summary = V.summarize(parsed)
    assert summary["readonly_deep_rate"][0] == 0.5
    assert summary["readonly_candidate_rate"][0] == 0.5
    assert summary["holder_fraction"][3:5] == [0.5, 0.5]
    assert sum(summary["holder_fraction"]) == 1
    w["holder_units"][3] += 1
    try:
        V.parse_vlife_line(_line(p))
    except ValueError:
        pass
    else:
        raise AssertionError("holder weights exceed one publication")


def test_conditions_and_genome_binding():
    old = {f"{w}-{l}-gc{gc}" for w in ("A", "B")
           for l in ("none", "wait1ms", "wait10ms", "ops1000")
           for gc in (10, 1000, 100000)}
    assert V.OLD_CONDITIONS == old
    assert len(V.CONDITIONS) == 108  # old 24 + main 60 + skew-zero 12 + tuned 12
    assert len([x for x in V.CONDITIONS if x.startswith("R")]) == 60
    assert len([x for x in V.CONDITIONS if x.startswith("S")]) == 12
    assert len([x for x in V.CONDITIONS if x.startswith("T")]) == 12
    assert "R95-wait10msR-gc100000" in V.CONDITIONS
    assert V._flags("B-none-gc10", 1000000, 2100)["izanagi_ronly_pct"] == -1
    assert V._flags("B-none-gc10", 1000000, 2100)["izanagi_long_kind"] == 0
    assert V._flags("R50-wait10msR-gc10", 1000000, 2100)["izanagi_long_kind"] == 2
    assert V.CONDITIONS["T50-none-gc10"]["genome"] == "tuned"
    assert "-DCCBENCH_INLINE_VERSION_OPT_CICADA=1" in V.genome_args("tuned")


def test_df_interaction_sign():
    assert V.df_interaction(17, 8, 5, 2) == 6


def test_tuned_compile_commands_match_cicada_definitions():
    with tempfile.TemporaryDirectory(prefix="cvl-genome-") as td:
        path = Path(td) / "compile_commands.json"
        definitions = [f"-D{axis}={value}" for axis, value in V.TUNED_GENOME.items()]
        row = {"file": str(ROOT / "external/ccbench/cc/cicada/transaction.cc"),
               "arguments": ["c++", *definitions, "-c", "transaction.cc"]}
        path.write_text(json.dumps([row]))
        assert V.verify_genome_commands(path, "tuned")["genome"] == "tuned"
        row["arguments"].remove("-DINLINE_VERSION_OPT=1")
        path.write_text(json.dumps([row]))
        try:
            V.verify_genome_commands(path, "tuned")
        except ValueError:
            pass
        else:
            raise AssertionError("missing tuned inline version definition accepted")


def test_default_compile_commands_match_cmake_defaults():
    with tempfile.TemporaryDirectory(prefix="cvl-default-genome-") as td:
        path = Path(td) / "compile_commands.json"
        row = {"file": str(ROOT / "external/ccbench/cc/cicada/transaction.cc"),
               "arguments": ["c++", *[f"-D{k}={v}" for k, v in V.DEFAULT_GENOME.items()],
                             "-c", "transaction.cc"]}
        path.write_text(json.dumps([row]))
        assert V.verify_genome_commands(path, "default")["genome"] == "default"
        row["arguments"].remove("-DINLINE_VERSION_PROMOTION=1")
        row["arguments"].append("-DINLINE_VERSION_PROMOTION=0")
        path.write_text(json.dumps([row]))
        try:
            V.verify_genome_commands(path, "default")
        except ValueError:
            pass
        else:
            raise AssertionError("wrong default promotion accepted")


def test_readonly_figure_full_campaign_layout():
    script = ROOT / "tools/plotting/plot_vhash_readonly_share.py"
    spec = importlib.util.spec_from_file_location("plot_vhash_readonly_share", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="cvl-figure-grid-") as td:
        raw_path = Path(td) / "raw.json"
        out = Path(td) / "figures"
        ids = sorted(module.REQUIRED)
        assert len(ids) == 86
        runs = {}
        for cid in ids:
            reps = []
            for rep in range(3):
                payload = _payload2()
                payload["workers"] = [_payload2()["workers"][0] for _ in range(48)]
                payload["build"].update(
                    inline_version_opt=int(cid.startswith("T")),
                    izanagi_ronly_pct=V.CONDITIONS[cid].get("izanagi_ronly_pct", -1),
                    izanagi_long_kind=V.CONDITIONS[cid].get("izanagi_long_kind", 0))
                w = payload["workers"][0]
                w["readonly_reads"] = 10
                w["hops"][1][0] = 10
                w["hops"][0][0] = 10
                for i in range(5):
                    w["readonly_deep"][i] = 1
                    w["readonly_candidate"][i] = 1
                    w["deep"][i] = 1
                w["gc_boundary_count"] = 2
                w["gc_boundary_us"][6] = 2
                w["gc_boundary_sum_us"] = 128
                w["gc_publish_count"] = 1
                w["gc_publish_us"][7] = 1
                w["gc_publish_sum_us"] = 100 + rep
                w["ro_snapshot_age_count"] = 1
                w["ro_snapshot_age_us"][5] = 1
                w["ro_snapshot_age_sum_us"] = 32
                w["dc_first"] = 1
                w["dc_count"] = 1
                w["dc_cf_wait_sum_us"] = 30
                w["dc_ro_gap_sum_us"] = 40 + rep
                w["dc_leader_wait_sum_us"] = 30
                w["dc_interval_sum_us"] = 100 + rep
                w["dc_cf_kind_count"][3] = 1
                w["dc_cf_kind_sum_us"][3] = 30
                w["holder_count"] = 1
                w["holder_units"][3] = 1000000
                reps.append({"rc": 0, "stdout": _line(payload), "parsed": payload})
            runs[cid] = reps
        raw_path.write_text(json.dumps({
            "schema_version": 1, "command": "measure", "ccbench_commit": V.PIN,
            "patch_sha256": hashlib.sha256(V.PATCH.read_bytes()).hexdigest(),
            "records": 1000000,
            "conditions": {cid: V.CONDITIONS[cid] for cid in ids},
            "runs": runs}))
        module.render([raw_path], out)
        for stem in ("depth_share", "boundary_age", "decompositions", "opportunities"):
            assert all((out / f"{stem}.{suffix}").is_file()
                       for suffix in ("png", "pdf", "provenance.json"))
        for stem in ("depth_share", "boundary_age"):
            provenance = json.loads((out / f"{stem}.provenance.json").read_text())
            assert "T (tuned) vs R (default)" in provenance["caption"]


def test_patch_draw_guard_and_readonly_gc_observation():
    source = V.PATCH.read_text()
    begin = source.split("+  vlife_long_ =", 1)[1]
    guard = begin.split("+  if (vlife_new_procedure_) {", 1)[1].split(
        "+    vlife_new_procedure_ = false;", 1)[0]
    assert "FLAGS_izanagi_ronly_pct < -1" in begin
    assert "FLAGS_izanagi_ronly_pct > 100" in begin
    assert "FLAGS_izanagi_ronly_pct >= 0" in guard
    assert "draw.next()" in guard
    assert "pro.ope_ = Ope::READ" in guard
    assert guard.index("FLAGS_izanagi_ronly_pct >= 0") < guard.index("draw.next()")
    outside = begin.replace(guard, "")
    assert "draw.next()" not in outside
    assert "pro.ope_ = Ope::READ" not in outside
    commit = source.split(" bool TxExecutor::commit() {", 1)[1]
    ro = commit.split("   if (this->is_ronly_) {", 1)[1].split("+#line 935", 1)[0]
    assert "loadAcquire(GCFlag[thid_].obj_)" in ro
    assert "chkClkSpan(gcstart_, now" in ro
    assert not re.search(r"(?:store|exchange|fetch_\w+)\s*\([^;]*?(?:GCFlag|gcstart_)", ro)
    assert not re.search(r"(?:GCFlag\[[^]]+\](?:\.obj_)?|gcstart_)\s*=", ro)
    assert not re.search(r"(?:__atomic_store_n|storeRelease|\.store)\s*\([^;]*?(?:GCFlag|gcstart_)", ro)
    assert not re.search(r"GCFlag\[[^]]+\](?:\.obj_)?\.store\s*\(", ro)
    assert not re.search(r"(?:this->)?gcstart_\s*(?:=|\+=|-=|\+\+|--)", ro)


def test_mut11_event_generation_and_current_holder():
    source = V.PATCH.read_text()
    mainte = source.split("@@ -883", 1)[1].split(
        "bool TxExecutor::commit()", 1)[0]
    assert "vlife_epoch_.load(std::memory_order_acquire)" in mainte
    assert "vlife_slot_generation_" not in mainte
    leader = source.split("void TxExecutor::leaderWork()", 1)[1]
    assert "vlife_holders_[i]" in leader
    assert "holder_match[i]" in leader


def test_mut12_measure_fixed_one_million():
    assert V.MEASURE_RECORDS == 1000000
    source = Path(V.__file__).read_text()
    assert 'records = _smoke_records(args.smoke_json)' in source
    assert 'if probes[str(MEASURE_RECORDS)]["maxrss_kb"] * 1024 < 4 * l3_bytes' in source


def test_mut13_readonly_depth_and_reads_follow_deleted_guard():
    source = V.PATCH.read_text()
    read = source.split('if (ver->ldAcqStatus() == VersionStatus::deleted)', 1)[1]
    section = read.split('read_set_.emplace_back', 1)[1].split('vlife_lower_ =', 1)[0]
    assert '++vlife().readonly_reads' in section
    assert '++vlife().readonly_deep[i]' in section
    assert '++vlife().readonly_candidate[i]' in section
    before = source.split('if (ver->ldAcqStatus() == VersionStatus::deleted)', 1)[0]
    assert '++vlife().readonly_deep[i]' not in before


def test_mut15_tuned_comparison_panels_exist():
    script = (ROOT / "tools/plotting/plot_vhash_readonly_share.py").read_text()
    assert script.count('_draw_tuned(axes[2,') >= 2
    assert '"T (tuned) vs R (default)"' in script or 'T (tuned) vs R (default):' in script


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
               "witness": {"normalized_objdump_equal": True,
                           "normalized_rodata_equal": True,
                           "stock_absence": {"nm": True, "strings": ["izanagi stock"]},
                           "default_absence": {"nm": True, "strings": ["izanagi stock"]}},
               "short_run": {"rc": 0, "parsed": _payload2()},
               "tuned_short_run": {"rc": 0, "parsed": _payload2_tuned()},
               "time_budget": {"estimated_node_s": 3000},
               "calibration": {"l3_bytes": 1000000,
                               "probes": {str(n): {"rc": 0, "maxrss_kb": rss}
                                          for n, rss in ((1000000, 5000),
                                                         (2000000, 5000),
                                                         (4000000, 8000))},
                               "selected_records": 1000000}}
        path.write_text(json.dumps(raw))
        assert V._smoke_records(path) == 1000000
        raw["patch_sha256"] = "0" * 64
        path.write_text(json.dumps(raw))
        try:
            V._smoke_records(path)
        except ValueError:
            pass
        else:
            raise AssertionError("mismatched patch accepted")


def test_smoke_recomputes_calibration_and_requires_success():
    with tempfile.TemporaryDirectory(prefix="cvl-smoke-selection-") as td:
        path = Path(td) / "smoke.json"
        raw = {"schema_version": 1, "command": "smoke", "ccbench_commit": V.PIN,
               "patch_sha256": hashlib.sha256(V.PATCH.read_bytes()).hexdigest(),
               "witness": {"normalized_objdump_equal": True,
                           "normalized_rodata_equal": True,
                           "stock_absence": {"nm": True, "strings": ["izanagi stock"]},
                           "default_absence": {"nm": True, "strings": ["izanagi stock"]}},
               "short_run": {"rc": 0, "parsed": _payload2()},
               "tuned_short_run": {"rc": 0, "parsed": _payload2_tuned()},
               "time_budget": {"estimated_node_s": 3000},
               "calibration": {"l3_bytes": 1000000,
                               "probes": {str(n): {"rc": 0, "maxrss_kb": rss}
                                          for n, rss in ((1000000, 1000),
                                                         (2000000, 5000),
                                                         (4000000, 8000))},
                               "selected_records": 4000000}}
        def rejected():
            path.write_text(json.dumps(raw))
            try:
                V._smoke_records(path)
            except ValueError:
                return
            raise AssertionError("invalid smoke accepted")
        rejected()  # Fixed 1M is the only permitted measure size.
        raw["calibration"]["selected_records"] = 1000000
        raw["calibration"]["probes"]["1000000"]["maxrss_kb"] = 5000
        path.write_text(json.dumps(raw))
        assert V._smoke_records(path) == 1000000
        raw["witness"]["normalized_rodata_equal"] = False
        rejected()
        raw["witness"]["normalized_rodata_equal"] = True
        raw["witness"]["default_absence"]["strings"].append("IZANAGI_NEW")
        rejected()
        raw["witness"]["default_absence"]["strings"].pop()
        raw["short_run"]["rc"] = 1
        rejected()
        raw["short_run"]["rc"] = 0
        raw["calibration"]["probes"]["2000000"]["rc"] = 1
        rejected()
        raw["calibration"]["probes"]["2000000"]["rc"] = 0
        raw["time_budget"]["estimated_node_s"] = 7200
        rejected()


def test_delay_compile_selects_unique_ycsb_target():
    with tempfile.TemporaryDirectory(prefix="cvl-commands-") as td:
        build = Path(td)
        source = build / "source"
        rows = [
            {"directory": td, "file": str(source / "cc/cicada/transaction.cc"),
             "arguments": ["c++", "-c", "transaction.cc", "-o", f"{name}.dir/transaction.cc.o"]}
            for name in ("tpcc_cicada.exe", "ycsb_cicada.exe", "bomb_cicada.exe")
        ]
        for row, name in zip(rows, ("tpcc", "ycsb", "bomb")):
            row["arguments"].insert(1, "-DTARGET=" + name)
        def write(value):
            (build / "compile_commands.json").write_text(json.dumps(value))
        with patch.object(V.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = ""
            run.return_value.stderr = ""
            write(rows)
            result = V._delay_compile(source, build)
            assert result["rc"] == 0
            assert "ycsb_cicada.exe.dir/transaction.cc.o" not in result["argv"]
            assert "-DTARGET=ycsb" in run.call_args.args[0]
            assert run.call_count == 1
            run.reset_mock()
            output_row = {**rows[1], "output": "ycsb_cicada.exe.dir/transaction.cc.o",
                          "arguments": ["c++", "-DTARGET=ycsb", "-c", "transaction.cc"]}
            write([rows[0], output_row])
            assert V._delay_compile(source, build)["rc"] == 0
            assert "-DTARGET=ycsb" in run.call_args.args[0]
            run.reset_mock()
            write([rows[0], rows[2]])
            for value in (None, [rows[1], {**rows[1], "output": "ycsb_cicada.exe.dir/other.o"}]):
                if value is not None:
                    write(value)
                try:
                    V._delay_compile(source, build)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("non-unique ycsb command accepted")
            assert run.call_count == 0


def test_smoke_delay_failure_preserves_other_stages_and_rejects_measure():
    with tempfile.TemporaryDirectory(prefix="cvl-failed-smoke-") as td:
        root = Path(td)
        out = root / "smoke.json"
        binaries = {name: root / name for name in ("stock", "default", "enabled", "tuned_enabled")}
        def build(_source, location, _toolchain, _dependencies, _macros, genome="default"):
            name = location.name.removesuffix("-build")
            return binaries[name], {"sha256": name, "elapsed_s": 1.0}
        calibration = {"l3_bytes": 1000000,
                       "probes": {str(n): {"rc": 0, "maxrss_kb": rss}
                                  for n, rss in ((1000000, 5000), (2000000, 5000),
                                                 (4000000, 8000))},
                       "selected_records": 1000000}
        with (patch.object(V.site_policy, "current_site", return_value="compute"),
              patch.object(V.site_policy, "refuses_heavy_work", return_value=False),
              patch.object(V, "_assert_single_tenant"),
              patch.object(V.compute, "_load_policy", return_value={}),
              patch.object(V.compute, "_resolve_toolchain", return_value={}),
              patch.object(V.compute, "_prepare_dependencies", return_value={}),
              patch.object(V, "checkout", return_value=nullcontext(str(root))),
              patch.object(V, "applied", return_value=nullcontext()),
              patch.object(V, "_build_variant", side_effect=build),
              patch.object(V, "_delay_compile", side_effect=RuntimeError("delay broke")),
              patch.object(V, "_normalized_disassembly", return_value="text"),
              patch.object(V, "_normalized_rodata", return_value="rodata"),
              patch.object(V, "_absence", return_value={"nm": True, "strings": []}),
              patch.object(V, "_calibrate", return_value=calibration),
              patch.object(V, "_run", side_effect=lambda *a, **kw: {
                  "rc": 0, "wall_s": 1.0,
                  "parsed": _payload2_tuned() if kw.get("genome") == "tuned"
                  else _payload2()})):
            assert V.main(["smoke", "--third-party-cache", td, "--policy", str(root),
                           "--out", str(out)]) == 1
        raw = json.loads(out.read_text())
        assert "delay broke" in raw["delay_compile"]["error"]
        assert raw["delay_compile"]["stderr_tail"] == ""
        assert set(raw["builds"]) == {"stock", "default", "enabled", "tuned_enabled"}
        assert raw["witness"]["normalized_objdump_equal"]
        assert raw["calibration"]["selected_records"] == 1000000
        assert raw["short_run"]["rc"] == 0
        assert "error" in raw
        try:
            V._smoke_records(out)
        except ValueError:
            pass
        else:
            raise AssertionError("failed smoke accepted by measure")
        measure = root / "measure.json"
        with (patch.object(V.site_policy, "current_site", return_value="compute"),
              patch.object(V.site_policy, "refuses_heavy_work", return_value=False)):
            assert V.main(["measure", "--third-party-cache", td,
                           "--smoke-json", str(out), "--out", str(measure)]) == 1
        assert "failed smoke JSON" in json.loads(measure.read_text())["error"]


def test_smoke_records_failed_delay_compile_without_failing():
    with tempfile.TemporaryDirectory(prefix="cvl-stock-delay-") as td:
        root = Path(td)
        binaries = {name: root / name for name in ("stock", "default", "enabled", "tuned_enabled")}
        def build(_source, location, _toolchain, _dependencies, _macros, genome="default"):
            name = location.name.removesuffix("-build")
            return binaries[name], {"sha256": name, "elapsed_s": 1.0}
        calibration = {"l3_bytes": 1000000,
                       "probes": {str(n): {"rc": 0, "maxrss_kb": rss}
                                  for n, rss in ((1000000, 5000), (2000000, 5000),
                                                 (4000000, 8000))},
                       "selected_records": 1000000}
        with (patch.object(V, "checkout", return_value=nullcontext(str(root))),
              patch.object(V, "applied", return_value=nullcontext()),
              patch.object(V, "_build_variant", side_effect=build),
              patch.object(V, "_delay_compile", return_value={"rc": 1, "stdout": "", "stderr": "stock defect"}),
              patch.object(V, "_normalized_disassembly", return_value="text"),
              patch.object(V, "_normalized_rodata", return_value="rodata"),
              patch.object(V, "_absence", return_value={"nm": True, "strings": ["izanagi stock"]}),
              patch.object(V, "_calibrate", return_value=calibration),
              patch.object(V, "_run", side_effect=lambda *a, **kw: {
                  "rc": 0, "wall_s": 1.0,
                  "parsed": _payload2_tuned() if kw.get("genome") == "tuned"
                  else _payload2()})):
            raw = V._smoke(root, {}, {})
        assert raw["delay_compile"] == {"rc": 1, "stdout": "", "stderr": "stock defect"}
        assert V._smoke_success(raw)
        path = root / "smoke.json"
        raw.update(schema_version=1, command="smoke", ccbench_commit=V.PIN,
                   patch_sha256=hashlib.sha256(V.PATCH.read_bytes()).hexdigest())
        path.write_text(json.dumps(raw))
        assert V._smoke_records(path) == 1000000


def test_batch_extension_stays_in_begin_and_retries_same_procedure():
    patch_text = V.PATCH.read_text()
    begin = patch_text.split("+  if (thid_ >= FLAGS_thread_num) {", 1)[1].split(
        "+#if IZANAGI_CICADA_VLIFE\n+  vlife_long_", 1)[0]
    assert "if (pro_set_.size() < FLAGS_batch_max_ope)" in begin
    assert "if (pro_set_.size() < FLAGS_batch_max_ope)" in begin
    assert "while (pro_set_.size() < FLAGS_batch_max_ope)" in begin
    for flag in ("FLAGS_ycsb_zipf_skew", "FLAGS_ycsb_tuple_num",
                 "FLAGS_ycsb_rratio", "FLAGS_ycsb_rmw"):
        assert flag in patch_text
    assert "pro_set_.front().ronly_ = ronly;" in begin
    assert "pro_set_.front().wonly_ = wonly;" in begin
    run = (ROOT / "external/ccbench/include/ycsb.hh").read_text()
    assert run.index("tx.begin();") < run.index("SimpleKey<8> key[tx.pro_set_.size()]")


def test_leader_publication_counts_same_value_store():
    patch_text = V.PATCH.read_text()
    leader = patch_text.split(" void TxExecutor::leaderWork() {", 1)[1]
    before, after = leader.split("   cicadaLeaderWork();", 1)
    flag = "__atomic_load_n(&(GCFlag[0].obj_), __ATOMIC_ACQUIRE)"
    assert "+  const bool leader_ready =\n+      " + flag + " == 1;" in before
    assert "+  if (leader_ready &&\n+      " + flag + " == 0) {" in after
    assert "+    const uint64_t published = MinRts.load(memory_order_acquire);" in after
    assert "if (published != previous)" not in leader


def test_worker_limit_checked_at_construction():
    patch_text = V.PATCH.read_text()
    constructor = patch_text.split("         backoff_(backoff), thid_(thid) {", 1)[1].split(
        "     // wait to initialize MinWts", 1)[0]
    assert "+    if (TotalThreadNum > sizeof(vlife_stats_) / sizeof(vlife_stats_[0])) {" in constructor
    assert "+      exit(1);" in constructor


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
             test_schema2_required_fields_and_three_term_identity,
             test_schema2_readonly_denominator_and_holder_weights,
             test_conditions_and_genome_binding, test_df_interaction_sign,
             test_tuned_compile_commands_match_cicada_definitions,
             test_default_compile_commands_match_cmake_defaults,
             test_readonly_figure_full_campaign_layout,
             test_patch_draw_guard_and_readonly_gc_observation,
             test_mut11_event_generation_and_current_holder,
             test_mut12_measure_fixed_one_million,
             test_mut13_readonly_depth_and_reads_follow_deleted_guard,
             test_mut15_tuned_comparison_panels_exist,
             test_k_boundary_and_condition_subset,
             test_real_patch_define_registry_and_rejection,
             test_patch_default_preprocess_matches_stock,
             test_smoke_identity_binds_records,
             test_smoke_recomputes_calibration_and_requires_success,
             test_delay_compile_selects_unique_ycsb_target,
             test_smoke_delay_failure_preserves_other_stages_and_rejects_measure,
             test_smoke_records_failed_delay_compile_without_failing,
             test_batch_extension_stays_in_begin_and_retries_same_procedure,
             test_leader_publication_counts_same_value_store,
             test_worker_limit_checked_at_construction)
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
