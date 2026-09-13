"""Formal-tail probes. Only process/build boundaries supply saved fixtures.

UNLANDED_FINDINGS (not xfail): integer API/persistence in benchparse/runner/
pipeline; correctness forwarding in loop; new caller inventories and test ledger.
The T-139 replay is deliberately separate from the low-CV cohort construction.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0,str(Path(__file__).parent))

from orchestrator.campaign import b10_backoff_static_tail_formal as formal
from orchestrator.campaign import pipeline, wal, ident
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.calibrator import runner, benchparse


@pytest.fixture
def spec():
    return formal.parse_preregistration((ROOT/formal.DOCUMENT_PATH).read_bytes())


def _document(data):
    return formal._BEGIN+b"```json\n"+json.dumps(data,ensure_ascii=False,indent=2).encode()+b"\n```\n"+formal._END+b"\n"


def test_probe_1_spec_binding_and_production_configuration(spec):
    binding = formal.load_preregistration(ROOT,"HEAD")
    raw = (ROOT/formal.DOCUMENT_PATH).read_bytes()
    lines = raw.splitlines(keepends=True)
    first = lines.index(formal._BEGIN)+2
    last = lines.index(formal._END+b"\n")-1
    expected = b"".join(lines[first:last])
    assert binding.document_blob_sha256 == hashlib.sha256(raw).hexdigest()
    assert binding.spec_sha256 == hashlib.sha256(expected).hexdigest()
    assert binding.spec_sha256 == "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"
    from orchestrator.campaign import env_contract
    for workload in ("write-heavy","balanced","read-heavy"):
        cfg = formal.config_for(spec,binding,workload,contract=env_contract.GENERATIONS["linux-baremetal"][0].contract,ccbench_source_digest=formal.ccbench_checkout_digest(ROOT/"external/ccbench"),toolchain={"fixture":"compiler"},correctness_mode="legacy")
        perf = formal.performance_config(spec,workload)
        assert (perf.records,perf.threads,perf.extime,perf.reps) == (1000000,48,3,5)
        assert cfg.search_config["correctness_reps_per_cell"] == 5
        assert cfg.search_config["run_kind"] == "t2500-tail-formal"
        assert sorted(b for b,g in formal.registered_points(spec,workload)) == [1000,1250,1768,2500,3535,5000,7070,9999]


@pytest.mark.parametrize("change",[
    lambda raw: raw+formal._BEGIN,
    lambda raw: raw+formal._END+b"\n",
    lambda raw: raw+raw,
    lambda raw: raw.replace(formal._BEGIN,b""),
    lambda raw: raw.replace(b"```json\n",b"```\n",1),
    lambda raw: raw.replace(b"{\n",b"not-json\n",1),
    lambda raw: raw.replace(b"\n",b"\r\n"),
])
def test_spec_rejects_marker_fence_json_bytes(change):
    with pytest.raises(ValueError):
        formal.parse_preregistration(change((ROOT/formal.DOCUMENT_PATH).read_bytes()))


@pytest.mark.parametrize("mutation",["section","duplicate","nonfinite","type","order","grid","rule","policy"])
def test_spec_rejects_unsupported_shapes_and_rules(spec,mutation):
    data = copy.deepcopy(spec.data)
    if mutation == "section": data.pop("study")
    if mutation == "type": data["execution"]["records"] = True
    if mutation == "order": data["workloads"][0]["measurement_order_us"].reverse()
    if mutation == "grid": data["grid"]["formal_tail_values_us"][0] += 1
    if mutation == "rule": data["grid"]["generation_rule"] = "eval(9999)"
    if mutation == "policy": data["analysis_input_contract"]["fallback_to_printed_abort_rate_allowed"] = True
    raw = _document(data)
    if mutation == "duplicate": raw = raw.replace(b'"records": 1000000',b'"records": 1000000, "records": 1000000')
    if mutation == "nonfinite": raw = raw.replace(b'"records": 1000000',b'"records": NaN')
    with pytest.raises(ValueError): formal.parse_preregistration(raw)


def test_binding_rejects_noncanonical_path_and_symlink(tmp_path):
    with pytest.raises(ValueError,match="noncanonical document"):
        formal.load_preregistration(ROOT,"HEAD",document_path="./"+formal.DOCUMENT_PATH)
    root = tmp_path/"alias"
    root.symlink_to(ROOT,target_is_directory=True)
    with pytest.raises(ValueError,match="symlink"):
        formal.load_preregistration(root,"HEAD")


def test_binding_rejects_blob_mismatch_and_nonancestor():
    # Existing historical ancestor has different document bytes; no working tree edit.
    history = formal._git(ROOT,"log","--format=%H","--",formal.DOCUMENT_PATH).decode().splitlines()
    candidate = next(commit for commit in history if formal._git(ROOT,"show",f"{commit}:{formal.DOCUMENT_PATH}") != (ROOT/formal.DOCUMENT_PATH).read_bytes())
    with pytest.raises(ValueError,match="blob mismatch"):
        formal.load_preregistration(ROOT,candidate)
    with pytest.raises(ValueError,match="git"):
        formal.load_preregistration(ROOT,"f"*40)


def _payload(n=5):
    return dict(tps=[1000000]*n,reps=[dict(rep_index=i,abort_counts_=100,commit_counts_=900,throughput_tps=1000000) for i in range(n)],leading_indicators={"abort_rate":0.9})


def test_integer_ratio_ignores_printed_rate(spec):
    payload = _payload()
    payload["reps"][0].update(abort_counts_=24435129,commit_counts_=2270481)
    before = formal.performance_reps(spec,payload)
    payload["leading_indicators"]["abort_rate"] = 0.0
    assert formal.performance_reps(spec,payload) == before
    assert before[0]["abort_rate_recomputed"] == 24435129/(24435129+2270481)
    assert before[0]["abort_rate_recomputed"] != 0.9150


@pytest.mark.parametrize("mutation",["four","six","duplicate","missing","float","bool","negative","zero","nan","inf","nonpositive","mismatch","extra"])
def test_performance_rejections(spec,mutation):
    payload = _payload()
    if mutation == "four": payload = _payload(4)
    if mutation == "six": payload = _payload(6)
    if mutation == "duplicate": payload["reps"][1]["rep_index"] = 0
    if mutation == "missing": payload["reps"][1].pop("rep_index")
    if mutation == "float": payload["reps"][0]["abort_counts_"] = 1.0
    if mutation == "bool": payload["reps"][0]["abort_counts_"] = True
    if mutation == "negative": payload["reps"][0]["abort_counts_"] = -1
    if mutation == "zero": payload["reps"][0].update(abort_counts_=0,commit_counts_=0)
    if mutation == "nan": payload["reps"][0]["throughput_tps"] = math.nan
    if mutation == "inf": payload["tps"][0] = math.inf
    if mutation == "nonpositive": payload["reps"][0]["throughput_tps"] = 0
    if mutation == "mismatch": payload["reps"][0]["throughput_tps"] += 1
    if mutation == "extra": payload["reps"][0]["invented"] = 1
    with pytest.raises(ValueError): formal.performance_reps(spec,payload)


def test_correctness_accepts_serializable_certified_and_rejects_bad_records(spec):
    good = [SimpleNamespace(payload=dict(certified=True,verdict="serializable",anomalies=0,workload={"tag":"legacy"})) for _ in range(5)]
    formal.correctness_records(spec,good,"legacy")
    with pytest.raises(ValueError,match="count"): formal.correctness_records(spec,good[:4],"legacy")
    for key,value in (("certified",False),("anomalies",1),("workload",{"tag":"s2"}),("workload",{})):
        bad = copy.deepcopy(good)
        bad[2].payload[key] = value
        with pytest.raises(ValueError): formal.correctness_records(spec,bad,"legacy")


# df=7.5: independent t-density quadrature and bisection at CDF=0.99.
@pytest.mark.parametrize("p,df,expected",[(0.975,1,12.706204736432095),(0.975,4,2.7764451051977987),(0.975,8,2.306004135204166),(0.99,7.5,2.9430993234069955)] )
def test_student_t_independent_reference(p,df,expected):
    assert formal.student_t_quantile(p,df) == pytest.approx(expected,rel=2e-10)


def test_interval_zero_and_dispersion_precedence(spec):
    zero = formal.cell_statistics(spec,[0]*5,[1000]*5)
    positive = formal.cell_statistics(spec,[0.1]*5,[1000]*5)
    both = formal.analyze_interval(spec,1250,1768,zero,zero)
    assert both["state"] == "saturated" and all(both[k] == 0 for k in ("qhat","qL","qU","U","L","U_flat"))
    decline = formal.analyze_interval(spec,1250,1768,positive,zero)
    assert decline["state"] == "declining" and all(decline[k] is None for k in ("qhat","qL","qU","U","L","U_flat"))
    assert formal.analyze_interval(spec,1250,1768,positive,positive)["state"] == "indeterminate"
    with pytest.raises(ValueError,match="zero-to-positive"):
        formal.analyze_interval(spec,1250,1768,zero,positive)


def test_spec_cv_threshold_causally_changes_same_observations(spec):
    rates = [0.098,0.099,0.100,0.101,0.102]
    assert formal.cell_statistics(spec,rates,[1000]*5)["gate_passed"] is True
    changed = copy.deepcopy(spec.data)
    changed["variability"]["maximum_cv_exclusive"] = 0.01
    tighter = formal.parse_preregistration(_document(changed))
    assert formal.cell_statistics(tighter,rates,[1000]*5)["gate_passed"] is False


def _saved_stdout():
    return [(ROOT/f"output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/run-R{i:02d}.log").read_bytes() for i in range(1,6)]


def _subprocess_replay(raws,seen):
    iterator = iter(raws)
    def run(argv,**kwargs):
        raw = next(iterator)
        seen.append(dict(argv=list(argv),sha256=hashlib.sha256(raw).hexdigest(),text=kwargs["text"]))
        # Supply only the process output and perf file, keeping both parsers real.
        if "-o" in argv:
            Path(argv[argv.index("-o")+1]).write_bytes(b"11,,LLC-load-misses,0,100.00,,\n22,,LLC-loads,0,100.00,,\n33,,instructions,0,100.00,,\n44,,cycles,0,100.00,,\n")
        return subprocess.CompletedProcess(argv,0,stdout=raw.decode() if kwargs["text"] else raw,stderr="" if kwargs["text"] else b"")
    return run


def test_spec_records_reaches_real_measure_point_argv(spec):
    seen = []
    for records in (1000000,1234567):
        changed = copy.deepcopy(spec.data)
        changed["execution"]["records"] = records
        config = formal.performance_config(formal.parse_preregistration(_document(changed)),"balanced")
        runner.measure_point("/fixture/ycsb.exe",config.records,config.threads,1800,extime=config.extime,reps=config.reps,workload=config.workload,require_all_reps=True,subprocess_runner=_subprocess_replay(_saved_stdout(),seen))
    assert len(seen) == 10
    assert all("-ycsb_tuple_num=1000000" in r["argv"] for r in seen[:5])
    assert all("-ycsb_tuple_num=1234567" in r["argv"] for r in seen[5:])


def test_probe_2_deferred_integer_capture_opens_saved_bytes(spec):
    sink,seen = [],[]
    token = runner.capture_measure_point("/fixture/ycsb.exe",1000000,48,1800,reps=5,rep_observations=sink,record_rep_integer_counters=True,subprocess_runner=_subprocess_replay(_saved_stdout(),seen))
    assert sink == [] and all(r["text"] is False for r in seen)
    token.open()
    assert len(sink) == 5
    assert (sink[0]["abort_counts_"],sink[0]["commit_counts_"]) == (24435129,2270481)


def _emit_campaign(spec,tmp_path,workload,stdout=None, *, through_loop=False):
    # test_campaign's external build/trace fixtures are retained; restore actual
    # measurement and stability functions before invoking the writer pipeline.
    import test_campaign as fixture
    from orchestrator.calibrator.stability import remeasure_until_stable
    from orchestrator.calibrator.perf_preflight import probe_perf_availability
    # Exercise the real unavailable-perf probe in an empty executable search
    # path. Only this probe sees the PATH change; no perf receipt is fabricated.
    with pytest.MonkeyPatch.context() as environment:
        environment.setenv("PATH", "")
        perf_receipt = probe_perf_availability()
    assert perf_receipt["status"] == "unavailable"
    fixture._refresh_certified_writer_authority()
    binding = formal.load_preregistration(ROOT,"HEAD")
    cfg = formal.config_for(spec,binding,workload,contract=fixture._AUTH_CONTRACT,ccbench_source_digest=formal.ccbench_checkout_digest(ROOT/"external/ccbench"),toolchain={"fixture":"compiler"},correctness_mode="legacy")
    cfg = ident.bind_admission_policy(cfg,fixture._BUILD_CONTEXT.policy)
    layout = CampaignLayout(root=str(tmp_path/"campaigns"/str(ident.campaign_id(cfg)))).ensure()
    fixture._write_certified_lock(layout,cfg)
    trace = (Path(__file__).parent/"fixtures/g1_serial/trace_0.log").read_text()
    seen = []
    raw = (b"abort_counts_:\t100\ncommit_counts_:\t900\nabort_rate:\t0.1000\nthroughput[tps]:\t1000000\nlatency[ns]:\t100\n")
    for amount,genome in formal.registered_points(spec,workload):
        with fixture._mock_pipeline(trace_content=trace,ncommit=2) as calls:
            original_build = pipeline.buildcache.build_v2
            def build(*args,**kwargs):
                result = original_build(*args,**kwargs)
                result.bin_sha256 = hashlib.sha256((genome.canonical()+str(kwargs["trace"])).encode()).hexdigest()
                result.bin_hash = result.bin_sha256[:16]
                return result
            pipeline.buildcache.build_v2 = build
            def measure(*args,**kwargs):
                return runner.measure_point(*args,**kwargs,subprocess_runner=_subprocess_replay(stdout or [raw]*5,seen))
            pipeline.measure_point = measure
            pipeline.remeasure_until_stable = remeasure_until_stable
            if through_loop:
                from orchestrator.campaign import loop
                with pytest.MonkeyPatch.context() as mp:
                    # External source/build fixture only; loop, evaluate,
                    # verifier, and WAL writer remain real.
                    mp.setattr(loop, "source_digest", pipeline.source_digest)
                    result = loop.run_campaign(
                        cfg, [genome], formal.performance_config(spec, workload),
                        fixture._AUTH_CONTRACT.env_tag, fixture._AUTH_CONTRACT.clocks_per_us,
                        numactl=fixture._AUTH_CONTRACT.numactl,
                        env_contract=fixture._AUTH_CONTRACT,
                        authorization_contract=fixture._AUTHORIZATION,
                        build_context=fixture._BUILD_CONTEXT, declared_use_class="official",
                        output_root=str(tmp_path), log=lambda *_: None,
                        correctness=pipeline.CorrectnessWorkload(reps=5),
                        record_rep_integer_counters=True, bench_max_rounds=1)
                    assert result.committed == 1 and result.aborted == 0, result
                    assert result.layout_root == layout.root
            else:
                result = pipeline.evaluate(genome,layout,fixture._AUTH_CONTRACT.env_tag,pin_commit(spec),formal.performance_config(spec,workload),clocks_per_us=fixture._AUTH_CONTRACT.clocks_per_us,numactl=fixture._AUTH_CONTRACT.numactl,env_contract=fixture._AUTH_CONTRACT,authorization_contract=fixture._AUTHORIZATION,build_context=fixture._BUILD_CONTEXT,correctness=pipeline.CorrectnessWorkload(reps=spec["execution"]["correctness_reps_per_cell"]),record_rep_integer_counters=True,use_perf=False,perf_preflight_receipt=perf_receipt,bench_max_rounds=1,log=lambda *_:None)
                assert result.certified, result
            assert len(calls.trace) == 5
    formal._create_json(Path(layout.root)/"reports"/(spec["future_driver_binding"]["artifact_stem"]+"-execution.json"),dict(status="complete",sweep_elapsed_s=10,job_elapsed_s=20,wal_sha256=hashlib.sha256(Path(layout.wal_file).read_bytes()).hexdigest(),campaign_lock_sha256=hashlib.sha256(Path(layout.lock_file).read_bytes()).hexdigest()))
    return binding,layout,seen


def pin_commit(spec):
    from orchestrator.campaign.pin import CURRENT_PIN
    return CURRENT_PIN


def test_probe_2_integer_counters_production_wal_roundtrip(spec,tmp_path):
    binding,layout,seen = _emit_campaign(spec,tmp_path,"balanced",_saved_stdout())
    loaded = formal.load_formal_campaign(spec,binding,layout,correctness_mode="legacy")
    first = loaded["points"][0]["reps"][0]
    assert (first["abort_counts_"],first["commit_counts_"],first["throughput_tps"]) == (24435129,2270481,756827)
    assert first["abort_rate_recomputed"] == 24435129/(24435129+2270481)
    assert len(seen) == 40


def _positive_cohort(spec,tmp_path):
    campaigns = []
    for workload in ("write-heavy","balanced","read-heavy"):
        binding,layout,_ = _emit_campaign(spec,tmp_path,workload)
        campaigns.append(formal.load_formal_campaign(spec,binding,layout,correctness_mode="legacy"))
    return campaigns


def _assert_positive(spec,campaigns,analyzer=formal.analyze_cohort):
    result = analyzer(spec,campaigns)
    assert result["verdict"] == "indeterminate-in-region", result["failures"]
    assert len(result["workloads"]) == 3
    assert all(len(w["intervals"]) == 6 for w in result["workloads"])
    return result


def test_analyze_cohort_complete_production_positive_and_two_mutants(spec,tmp_path):
    campaigns = _positive_cohort(spec,tmp_path)
    _assert_positive(spec,campaigns)
    def always_invalid(s,c):
        result = formal.analyze_cohort(s,c)
        result["verdict"] = "invalid"
        return result
    # Mutate the actual function's identity field source, without editing files.
    changed = copy.deepcopy(spec)
    changed.data["cohort_identity"]["must_match_across_all_three_campaign_locks"].append("workload_coordinates")
    with pytest.raises(AssertionError): _assert_positive(spec,campaigns,always_invalid)
    with pytest.raises(AssertionError): _assert_positive(changed,campaigns)
    report = formal.materialize_report(spec,campaigns,tmp_path/"cohort")
    assert report["verdict"] == "indeterminate-in-region"
    with pytest.raises(ValueError,match="create-only"):
        formal.materialize_report(spec,campaigns,tmp_path/"cohort")


def test_probe_3_provenance_uses_stored_physical_wal_lines(spec,tmp_path):
    binding,layout,_ = _emit_campaign(spec,tmp_path,"balanced")
    loaded = formal.load_formal_campaign(spec,binding,layout,correctness_mode="legacy")
    frames = Path(layout.wal_file).read_bytes().splitlines(keepends=True)
    for point in loaded["points"]:
        for rep in point["reps"]:
            frame = next(f for f in frames if json.loads(f)["stage"] == "bench_done" and json.loads(f)["payload"]["build_attempt_id"] == rep["attempt_id"])
            assert rep["wal_record_digest"] == hashlib.sha256(frame).hexdigest()
            assert rep["campaign_id"] == Path(layout.root).name
            assert rep["source_measurement"] == "trace_disabled"


def test_probe_4_five_real_verifier_records_and_loop_forwarding(spec,tmp_path):
    from orchestrator.campaign.loop import run_campaign
    assert "correctness" in inspect.signature(run_campaign).parameters, "UNLANDED: loop correctness forwarding"
    binding,layout,_ = _emit_campaign(spec,tmp_path,"balanced",through_loop=True)
    loaded = formal.load_formal_campaign(spec,binding,layout,correctness_mode="legacy")
    assert all(len(p["correctness"]) == 5 and all(v["payload"]["certified"] is True for v in p["correctness"]) for p in loaded["points"])


def _explore():
    root = Path("/work/1/SFC/tanab/b10-backoff-grid-t2418-explore")
    candidates = sorted(root.glob("**/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-*/campaign.lock"))
    assert len(candidates) == 1
    return candidates[0].parent


def test_probe_5_explore_mode_and_formal_report_comparison(spec,tmp_path):
    mode = formal.load_explore_correctness_mode(_explore())
    assert mode == "legacy"
    binding,layout,_ = _emit_campaign(spec,tmp_path,"balanced")
    loaded = formal.load_formal_campaign(spec,binding,layout,correctness_mode=mode)
    assert all(v["payload"]["workload"]["tag"] == mode for p in loaded["points"] for v in p["correctness"])
    with pytest.raises(ValueError,match="mode"):
        formal.load_formal_campaign(spec,binding,layout,correctness_mode="s2")


def test_formal_loader_rejects_real_exploration(spec):
    binding = formal.load_preregistration(ROOT,"HEAD")
    with pytest.raises(ValueError,match="not formal"):
        formal.load_formal_campaign(spec,binding,_explore(),correctness_mode="legacy")


def test_checkout_source_identity_is_shared_by_real_driver_configs(spec):
    binding = formal.load_preregistration(ROOT, "HEAD")
    from orchestrator.campaign import env_contract
    identities, first_points = [], []
    for workload in ("write-heavy", "balanced", "read-heavy"):
        first_points.append(formal.registered_points(spec, workload)[0][0])
        cfg = formal.config_for(
            spec, binding, workload,
            contract=env_contract.GENERATIONS["linux-baremetal"][0].contract,
            ccbench_source_digest=formal.ccbench_checkout_digest(ROOT/"external/ccbench"),
            toolchain={"fixture": "compiler"}, correctness_mode="legacy")
        identities.append(cfg.search_config["ccbench_source_digest"])
    assert first_points == [2500, 1250, 3535]
    assert len(set(identities)) == 1 and len(identities[0]) == 64


def test_scheduler_parses_saved_nqsv_and_strips_job_prefix(monkeypatch):
    import time
    raw = (ROOT/"output/env/pegasus/smoke/0:867860.nqsv/qstat_job.stdout").read_text()
    parsed = formal.parse_scheduler_coordinates(raw, "0:867860.nqsv")
    assert parsed["reserved_walltime_s"] == 600
    assert time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(parsed["job_start_epoch"])) == "2026-07-19 00:53:45"
    seen = []
    def replay(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout=raw, stderr="")
    monkeypatch.setenv("PBS_JOBID", "0:867860.nqsv")
    monkeypatch.setattr(formal.subprocess, "run", replay)
    assert formal.scheduler_coordinates() == parsed
    assert seen == [["qstat", "-f", "867860.nqsv"]]
    for bad in ("NQSV field selection help", raw.replace("600S", "UNLIMITED"),
                raw.replace("867860.nqsv", "867861.nqsv")):
        with pytest.raises(ValueError):
            formal.parse_scheduler_coordinates(bad, "0:867860.nqsv")


@pytest.mark.parametrize("damage", ["missing-cell", "missing-counter", "timeout"])
def test_rejected_campaign_report_preserves_every_observed_wal_value(spec, tmp_path, damage):
    binding, layout, _ = _emit_campaign(spec, tmp_path, "balanced")
    path = Path(layout.wal_file)
    records = [json.loads(line) for line in path.read_text().splitlines()]
    if damage == "missing-cell":
        variant = records[0]["variant"]
        records = [r for r in records if r["variant"] != variant]
    elif damage == "missing-counter":
        bench = next(r for r in records if r["stage"] == "bench_done")
        del bench["payload"]["reps"][0]["abort_counts_"]
    path.write_text("".join(json.dumps(r)+"\n" for r in records))
    observed = path.read_text()
    if damage == "timeout":
        import time
        with pytest.raises(formal.SweepDeadline):
            with formal._deadline(0.01, on_timeout=lambda exc: formal.report_sweep_timeout(spec, tmp_path, "balanced", exc)):
                time.sleep(0.1)
        report_path = tmp_path/"reports"/"balanced"/(spec["future_driver_binding"]["artifact_stem"]+".json")
        report = json.loads(report_path.read_text())
        assert any("deadline" in reason for reason in report["failures"])
    else:
        with pytest.raises(Exception):
            formal.load_formal_campaign(spec, binding, layout, correctness_mode="legacy")
        rejected = formal.load_formal_campaign_for_report(spec, binding, layout, correctness_mode="legacy")
        report = formal.materialize_report(spec, [rejected], tmp_path/"rejected-report")
    assert report["verdict"] == "invalid" and report["failures"]
    assert report["campaigns"][0]["descriptive_only"] is True
    assert report["campaigns"][0]["raw_wal"] == observed
    assert "1000000" in observed and "commit_counts_" in observed


def test_balanced_integer_opt_in_is_rejected_before_work(spec, tmp_path):
    import test_campaign as fixture
    from orchestrator.campaign import loop
    fixture._refresh_certified_writer_authority()
    config = pipeline.BalancedScheduleConfig("balanced", "0"*64, ("left", "right"))
    with pytest.raises(ValueError, match="does not support record_rep_integer_counters"):
        loop.run_campaign(
            fixture._cfg(), [], formal.performance_config(spec, "balanced"),
            fixture._AUTH_CONTRACT.env_tag, fixture._AUTH_CONTRACT.clocks_per_us,
            authorization_contract=fixture._AUTHORIZATION,
            build_context=fixture._BUILD_CONTEXT, declared_use_class="official",
            balanced_schedule=config, record_rep_integer_counters=True,
            output_root=str(tmp_path))
    arms = [fixture._balanced_prepared_fixture(CampaignLayout(root=str(tmp_path)), arm)[0]
            for arm in ("A", "B")]
    arms[0].record_rep_integer_counters = True
    with pytest.raises(ValueError, match="does not support record_rep_integer_counters"):
        pipeline._run_balanced_schedule(arms, config)
    assert not list(tmp_path.iterdir())


def test_anomaly_maximum_is_consumed_consistently(spec, tmp_path):
    campaigns = _positive_cohort(spec, tmp_path)
    campaigns[0]["points"][0]["correctness"][0]["payload"]["anomalies"] = 1
    assert formal.analyze_cohort(spec, campaigns)["verdict"] == "invalid"
    changed = copy.deepcopy(spec.data)
    changed["correctness"]["maximum_anomalies_per_rep"] = 1
    alternate = formal.parse_preregistration(_document(changed))
    for campaign in campaigns:
        campaign["identity"]["spec_sha256"] = alternate.spec_sha256
    records = [SimpleNamespace(payload=v["payload"]) for v in campaigns[0]["points"][0]["correctness"]]
    formal.correctness_records(alternate, records, "legacy")
    assert formal.analyze_cohort(alternate, campaigns)["verdict"] == "indeterminate-in-region"


def test_no_perf_cohort_and_strict_receipt_json_shape(spec, tmp_path):
    from orchestrator.calibrator import perf_preflight
    campaigns = _positive_cohort(spec, tmp_path)
    for campaign in campaigns:
        for point in campaign["points"]:
            assert point["use_perf"] is False
            observation = point["perf_observation"]
            receipt = observation["preflight"]
            assert type(receipt["probe_argv"]) is list
            assert perf_preflight.use_perf_from_receipt(receipt) is False
            broken = copy.deepcopy(receipt)
            broken["probe_argv"] = tuple(broken["probe_argv"])
            with pytest.raises(perf_preflight.PerfPreflightError):
                perf_preflight.validate_perf_preflight_receipt(broken)
    _assert_positive(spec, campaigns)


def _run():
    return pytest.main([__file__,"-v"])


if __name__ == "__main__":
    sys.exit(_run())
