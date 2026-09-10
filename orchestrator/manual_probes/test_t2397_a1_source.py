"""One-off compute probe; run through tools/run_tests.py --force-dispatch only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile

from orchestrator.campaign import paper_story_a1_paired as a1, pipeline
from orchestrator.campaign.layout import CampaignLayout


def test_t2397_a1_source(tmp_path, monkeypatch):
    assert socket.gethostname().split(".")[0].startswith("bnode")
    repo = Path(__file__).resolve().parents[2]
    job = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4")
    expected_head = (job / "probe-head.txt").read_text().strip()
    assert a1._run_git(repo, "rev-parse", "HEAD") == expected_head
    evidence = job / "source-probe" / os.environ["PBS_JOBID"].replace(":", "_")
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix="t2397-", dir="/scr"))
    source = scratch / "ccbench"
    subprocess.run(["git", "clone", "--quiet", str(repo / "external/ccbench"), str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "checkout", "--detach", a1.CANONICAL_CCBENCH_OID], check=True)
    # Execute the existing job's exact pinned gflags/glog staging block.
    shell = (repo / a1.JOB_RELATIVE_PATH).read_text()
    block = shell.split('DEPENDENCY_EVIDENCE_ROOT="$RAW_ROOT/dependency-staging"', 1)[1]
    block = 'DEPENDENCY_EVIDENCE_ROOT="$RAW_ROOT/dependency-staging"' + block.split('\nTHIRD_PARTY_ARGS=()', 1)[0]
    env = dict(os.environ, RAW_ROOT=str(evidence), REPO_ROOT=str(repo), PYTHON_BIN=sys.executable,
               PEGASUS_POLICY_RELATIVE="tools/pegasus/policy.json", DEPENDENCY_SCRATCH_PARENT=str(scratch),
               IZANAGI_SUBMISSION_NONCE="t2397-source-probe")
    suffix = '\nprintf "%s" "$DEPENDENCY_PREFIX" > "$RAW_ROOT/prefix.txt"\n'
    subprocess.run(["bash", "-c", 'set -euo pipefail\nrefuse() { echo "$*" >&2; exit 2; }\n' + block + suffix], env=env, check=True)
    prefix = (evidence / "prefix.txt").read_text()
    hydrated = Path(json.loads((job / "hydrate.json").read_text())["source_root"])
    base = scratch / "fetchcontent"
    base.mkdir()
    for name in ("masstree", "mimalloc", "googletest"):
        shutil.copytree(hydrated / name, base / f"{name}-src", symlinks=True)
    policy, _ = a1.load_policy(a1.V3_PILOT_STUDY_ID)
    site, contract, authorization = a1.p2_2.resolve_site_runtime()
    assert site == a1.site_policy.PEGASUS_COMPUTE
    cc, cxx = a1.buildcache.compilers_for_current_site()
    toolchain = a1.buildcache.observed_toolchain_manifest(cc, cxx)
    records = []
    for name in ("evaluate_define_supply_effectuation", "evaluate_define_runtime_meaning", "require_condition_gate_family"):
        original = getattr(a1.condition_meaning_gate, name)
        def observe(*args, _original=original, **kwargs):
            result = _original(*args, **kwargs)
            records.append(json.loads(result.canonical_json()))
            (evidence / "condition-records.json").write_text(json.dumps(records, indent=2))
            return result
        monkeypatch.setattr(a1.condition_meaning_gate, name, observe)
    with a1.a1_source.materialized(repo, base=source) as (context, stock):
        (evidence / "source.json").write_text(json.dumps({"root": str(context.root), "pin": context.pin,
            "expected_materialization_sha256": context.expected, "contract": a1.a1_source.load_contract(repo)}))
        options = a1.a1_source.prepare_dependencies(root=base, source=context.root, repo_root=repo,
                                                   dependency_prefix=prefix, toolchain=toolchain)
        original_build = a1.buildcache.build_v2
        def observe_build(genome, **kwargs):
            result = original_build(genome, **kwargs)
            assert result.ccbench_root == str(context.root)
            assert list(result.configure_argv[10:14]) == list(a1.a1_source.configure_dependencies(options))
            with (evidence / "builds.jsonl").open("a") as stream:
                stream.write(json.dumps({"trace": result.trace, "configure": result.configure_argv,
                    "build": result.build_argv, "binary_sha256": result.bin_sha256}) + "\n")
            return result
        monkeypatch.setattr(a1.buildcache, "build_v2", observe_build)
        for workload in a1.WORKLOAD_ORDER:
            a1._require_v3_backoff_fixed_condition_gate(repo_root=repo, policy=policy, workload=workload,
                cxx=cxx, cc=cc, evidence_root=evidence, source_root=context.root, stock_root=stock,
                dependency_prefix=prefix, dependency_options=options)
            build_context = a1.build_run_context(generator_id=a1.GeneratorId.BACKOFF_SWEEP)
            def capability(source_evidence):
                return a1.attest_generator_output(build_context, source_evidence,
                    generator_input_sha256=hashlib.sha256(workload.encode()).hexdigest())
            perf = a1.PerfConfig(records=policy["scale"]["records"], threads=policy["scale"]["threads"],
                workload=a1.workload_flags(policy, workload), extime=policy["scale"]["extime_s"],
                reps=a1._expected_reps(policy, workload))
            cfg = a1.campaign_config(policy, workload)
            layout = CampaignLayout(str(evidence / workload))
            layout.ensure()
            for genome in a1.genomes(policy, workload):
                prepared = pipeline._prepare_evaluation(genome, layout, contract.env_tag, context.pin,
                    perf, contract.clocks_per_us, numactl=contract.numactl, do_bench=False, do_settle=False,
                    ccbench_dir=str(context.root), cache_root=str(scratch / "cache"),
                    dependency_prefix=prefix, env_contract=contract, authorization_contract=authorization,
                    expected_toolchain_manifest=toolchain, build_context=build_context, capability_resolver=capability,
                    canonical_build_pin=context.pin, a1_source_context=context,
                    extra_correctness=a1.campaign_loop._closed_verify_workloads(cfg, perf), **options)
                assert isinstance(prepared, pipeline._PreparedEvaluation), prepared
                assert prepared.result.certified and not prepared.result.aborted
                context.validate(str(context.root), context.pin)
    (evidence / "completed.json").write_text(json.dumps({"head": expected_head, "host": socket.gethostname(),
        "workloads": list(a1.WORKLOAD_ORDER), "arms": 6, "bench": False}))
