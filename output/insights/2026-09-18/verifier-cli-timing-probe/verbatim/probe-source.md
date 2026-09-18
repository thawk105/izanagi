# probe の逐語 — `verifier_cli_timing_probe.py` (Codex `role=author` 作、repo へは入れない) と `run-both.sh` (親の運転 script)

- `verifier_cli_timing_probe.py`: 544 行、sha256 `03a1efbc832329982b1a947d21adefaced2fdb0356ab6462d462ee8f8b3d52f8`
- `run-both.sh`: 26 行、sha256 `ebc6f755e165344c5a633d4af42829ff5f069b855bbe4163145c34fe871fe847`
- 原本: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-cli-timing-probe/probe/verifier_cli_timing_probe.py`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-cli-timing-probe/probe/run-both.sh`

## verifier_cli_timing_probe.py

```python
#!/usr/bin/env python3.10
"""Disposable, one-condition verifier CLI timing probe; configuration is argv-only."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from uuid import uuid4

PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
SCHEMA = "verifier-cli-timing-probe/v1"
DEFINES = ["-DCCBENCH_TRACE=1", "-DCCBENCH_BACK_OFF=0",
           "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
           "-DCCBENCH_NO_WAIT_OF_TICTOC=0", "-DCCBENCH_WAL=0"]
TIMING_KEYS = "t_popen_monotonic t_popen_returned_monotonic t_wait_monotonic wall_s communicate_window_s rusage rc started_epoch finished_epoch".split()
BINDING_KEYS = "repo_head ccbench_pin source_checkout source_pinned_clean configure_argv configure_defines binary binary_sha256 toolchain python_executable python_version verifier_module_sha256 pipeline_module_sha256 workload_argv numactl policy_sha256".split()
VERIFY_KEYS = "argv cwd json_path stderr_path verdict certified n_txns n_edges anomalies integrity proof_surfaces parse_ok".split()
TRACE_KEYS = "exceeded_pipeline_timeout_120s stdout_path stderr_path commit_witness batch_commit_witness abort_counts".split()


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def timing_record():
    return {**dict.fromkeys(TIMING_KEYS), "timed_out": False}


def new_result(label):
    return dict(schema_version=SCHEMA, label=label, status="running", hostname=None,
                cpu_model=None, affinity_cpus=None, verifier_default_workers=None,
                started_at=now(), finished_at=None, bindings=dict.fromkeys(BINDING_KEYS),
                trace={**timing_record(), **dict.fromkeys(TRACE_KEYS)},
                count=dict(wall_s=None, c_lines=None), files=[],
                verify={**timing_record(), **dict.fromkeys(VERIFY_KEYS), "parse_ok": False},
                copy=dict(wall_s=None, dest=None), error=None)


def bench_argv(binary, records, threads, extime):
    flags = dict(ycsb_tuple_num=records, thread_num=threads, ycsb_zipf_skew="0.9",
                 ycsb_rratio=95, ycsb_rmw=0, ycsb_max_ope=10, extime=extime)
    return [str(binary)] + [f"-{k}={v}" for k, v in flags.items()] + ["-clocks_per_us=2100"]


def verifier_argv(trace, witness, source):
    argv = [os.path.realpath(sys.executable), "-B", "-m", "orchestrator.verifier",
            str(trace), "--json"]
    if witness is not None:
        argv += ["--expected-commits", str(witness)]
    return argv + ["--protocol", "silo", "--ccbench-root", str(source)]


def configure_argv(source, build, policy, toolchain, dependencies):
    return ["cmake", "-S", str(source), "-B", str(build),
            "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF", *DEFINES,
            "-DCCBENCH_CCACHE=OFF", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
            "-DRULE_LAUNCH_COMPILE=", "-DCMAKE_TOOLCHAIN_FILE=",
            f"-DCMAKE_PREFIX_PATH={dependencies['gflags']};{dependencies['glog']}",
            f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={dependencies['masstree']}",
            f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={dependencies['mimalloc']}",
            f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={dependencies['googletest']}",
            f"-DIZANAGI_GFLAGS_SRC_HEAD={policy['gflags_expected_head']}",
            f"-DIZANAGI_GLOG_SRC_HEAD={policy['glog_expected_head']}",
            f"-DCMAKE_C_COMPILER={toolchain['cc_path']}",
            f"-DCMAKE_CXX_COMPILER={toolchain['cxx_path']}", "-DCMAKE_CXX_FLAGS="]


def timing_values(start, returned, end, epoch_start, epoch_end, status, usage):
    return dict(t_popen_monotonic=start, t_popen_returned_monotonic=returned,
                t_wait_monotonic=end, wall_s=end - start,
                communicate_window_s=end - returned, started_epoch=epoch_start,
                finished_epoch=epoch_end, rc=os.waitstatus_to_exitcode(status),
                rusage={k: getattr(usage, k) for k in ("ru_utime", "ru_stime", "ru_maxrss")})


def timed_process(argv, cwd, timeout, stdout, stderr, env=None):
    """wait4 is the sole reaper (no poll/wait/communicate consuming rusage).

    Watchdog kills only this child's new process group. Deadline includes Popen.
    Linux ru_maxrss is KiB. Output file opening is outside the measured interval.
    """
    record = timing_record()
    done = threading.Event()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        epoch_start = time.time()
        start = time.monotonic()
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=err,
                                start_new_session=True)
        returned = time.monotonic()

        def watchdog():
            if not done.wait(max(0.0, timeout - (time.monotonic() - start))):
                record["timed_out"] = True
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

        timer = threading.Thread(target=watchdog, daemon=True)
        timer.start()
        try:
            _, status, usage = os.wait4(proc.pid, 0)
            end = time.monotonic()
            epoch_end = time.time()
            done.set()
            proc.returncode = os.waitstatus_to_exitcode(status)
        except BaseException:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, status, _ = os.wait4(proc.pid, 0)
            proc.returncode = os.waitstatus_to_exitcode(status)
            raise
        finally:
            done.set()
            timer.join()
        record.update(timing_values(start, returned, end, epoch_start, epoch_end, status, usage))
    return record


def count_c_lines(trace_dir):
    # Exactly the counting loop/text I/O of pipeline._run_trace.
    n = 0
    if os.path.isdir(trace_dir):
        for fn in os.listdir(trace_dir):
            if fn.startswith("trace_") and fn.endswith(".log"):
                with open(os.path.join(trace_dir, fn)) as f:
                    n += sum(1 for line in f if line.startswith("C "))
    return n


def file_inventory(trace_dir):
    records = []
    for path in sorted(trace_dir.glob("trace_*.log")):
        with path.open() as handle:
            lines = sum(1 for _ in handle)
        records.append(dict(name=path.name, bytes=path.stat().st_size, lines=lines, sha256=sha(path)))
    return records


def project_verifier(rc, raw, timed_out=False):
    """Copy JSON values without interpreting the verifier's verdict."""
    keys = "verdict certified n_txns n_edges anomalies anomaly_count integrity proof_surfaces".split()
    result = {**dict.fromkeys(keys), "parse_ok": False, "classification": "failure"}
    try:
        payload = json.loads(raw)
        if payload["runs"] != 1 or len(payload["results"]) != 1:
            raise ValueError("expected one CLI result")
        v = payload["results"][0]
        result.update(verdict=v["verdict"], certified=v["certified"],
                      n_txns=v["stats"]["txns"], n_edges=v["stats"]["edges"],
                      anomalies=v["anomalies"], anomaly_count=v["anomaly_count"],
                      integrity=v["integrity"], proof_surfaces=v.get("proof_surfaces"),
                      proof_surfaces_present="proof_surfaces" in v, parse_ok=True)
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        result["parse_error"] = str(exc)
    if timed_out:
        result["classification"] = "failure"
    elif rc == 2:
        result["classification"] = "usage"
    elif not result["parse_ok"]:
        result["classification"] = "invalid-json"
    else:
        result["classification"] = {0: "certified", 1: "non-serializable",
                                    3: "indeterminate"}.get(rc, "failure")
    return result


def run(args):
    sys.path.insert(0, str(args.repo_root))
    output = scratch = None
    document = new_result(args.label)

    def flush(stage):
        document["last_completed_stage"] = stage
        write_json(output / "result.json", document)

    try:
        from orchestrator.campaign import s3_mocc_lock_coverage as driver, site_policy, pipeline
        from orchestrator.campaign.patchharness import checkout, assert_pinned_clean
        from orchestrator.campaign.p2_2 import _assert_single_tenant
        from orchestrator.verifier.parse import _effective_worker_count
        site = site_policy.current_site(require_evidence=True)
        if site_policy.refuses_heavy_work(site) or not site_policy.is_pegasus_compute(site):
            raise RuntimeError(f"run requires a Pegasus compute node: {site}")
        if not args.scratch_root.is_relative_to(Path('/scr')):
            raise ValueError("--scratch-root must be under /scr")
        candidate = args.output_dir
        try:
            candidate.mkdir(parents=True)
        except FileExistsError:
            candidate = candidate / f"verifier-timing-{uuid4().hex}"
            candidate.mkdir()
        output = candidate
        document.update(hostname=socket.gethostname(), affinity_cpus=len(os.sched_getaffinity(0)),
                        output_dir=str(output), site=site)
        with open('/proc/cpuinfo') as handle:
            document["cpu_model"] = next(line.partition(':')[2].strip() for line in handle
                                         if line.partition(':')[0].strip() == 'model name')
        flush("site-output")
        args.scratch_root.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix="verifier-timing-", dir=args.scratch_root))
        # No environment configuration reads. Inheritance below is required by _run_trace.
        os.environ["TMPDIR"] = str(scratch)
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        tempfile.tempdir = str(scratch)
        document["scratch"] = str(scratch)
        b = document["bindings"]
        b.update(repo_head=driver._run_checked(["git", "-C", str(args.repo_root), "rev-parse", "HEAD"]).stdout.strip(),
                 ccbench_pin=PIN, python_executable=os.path.realpath(sys.executable),
                 python_version=sys.version, numactl=[], configure_defines=list(DEFINES),
                 verifier_module_sha256={p.name: sha(p) for p in sorted(
                     (args.repo_root / "orchestrator/verifier").glob("*.py"))},
                 pipeline_module_sha256=sha(args.repo_root / "orchestrator/campaign/pipeline.py"))
        document["conditions"] = dict(protocol="silo", target="ycsb_silo.exe", records=args.records,
                                      threads=args.threads, extime=args.extime,
                                      run_timeout_s=args.run_timeout_s,
                                      verifier_timeout_s=args.verifier_timeout_s)
        flush("scratch-bindings")
        policy_path = args.repo_root / "tools/pegasus/mocc_trace_v1_policy.json"
        b["policy_sha256"] = sha(policy_path)
        # This required helper internally validates mocc_trace; no run settings use it.
        policy = driver._load_policy(policy_path)
        flush("policy")
        toolchain = driver._resolve_toolchain(policy)
        b["toolchain"] = toolchain
        flush("toolchain")
        dependencies = driver._prepare_dependencies(args.repo_root, policy, args.third_party_cache,
                                                   scratch, toolchain)
        flush("dependencies")
        with ExitStack() as stack:
            source = Path(stack.enter_context(checkout(PIN, base_dir=str(args.repo_root / "external/ccbench"))))
            assert_pinned_clean(str(source), PIN)
            b.update(source_checkout=str(source), source_pinned_clean=True)
            flush("checkout")
            jobs = site_policy.default_build_jobs(site)
            warm = scratch / "warmup"
            warm_argv = configure_argv(source, warm, policy, toolchain, dependencies)
            b["warmup_configure_argv"] = warm_argv
            driver._run_checked(warm_argv)
            flush("warmup-configure")
            driver._run_checked(["cmake", "--build", str(warm), "--target", "masstree_build",
                                 "-j", str(jobs)], timeout=1200)
            flush("warmup")
            build = scratch / "build"
            b["configure_argv"] = configure_argv(source, build, policy, toolchain, dependencies)
            driver._run_checked(b["configure_argv"])
            flush("configure")
            driver._run_checked(["cmake", "--build", str(build), "--target", "ycsb_silo.exe",
                                 "-j", str(jobs)], timeout=900)
            flush("build")
            binary = build / "cc/silo/ycsb_silo.exe"
            b.update(binary=str(binary), binary_sha256=sha(binary),
                     workload_argv=bench_argv(binary, args.records, args.threads, args.extime))
            trace_dir = scratch / "trace"
            (trace_dir / "log").mkdir(parents=True)
            t = document["trace"]
            t.update(stdout_path=str(output / "bench.stdout"), stderr_path=str(output / "bench.stderr"))
            flush("binary")
            _assert_single_tenant()
            t.update(timed_process(b["workload_argv"], trace_dir, args.run_timeout_s,
                                   Path(t["stdout_path"]), Path(t["stderr_path"]),
                                   env=dict(os.environ, IZANAGI_TRACE_DIR=str(trace_dir))))
            t["exceeded_pipeline_timeout_120s"] = t["wall_s"] > pipeline.TRACE_TIMEOUT_S
            t["communicate_window_exceeded_120s"] = t["communicate_window_s"] > pipeline.TRACE_TIMEOUT_S
            if t["timed_out"] or t["rc"] != 0:
                document.update(status="failure", error=f"bench rc={t['rc']} timed_out={t['timed_out']}")
            flush("trace-process")
            raw = Path(t["stdout_path"]).read_text(errors="replace")
            t["commit_witness"], t["batch_commit_witness"] = pipeline._parse_commit_witness(raw)
            t["abort_counts"] = pipeline._parse_abort_counts(raw)
            flush("witness")
            failures = []
            if t["timed_out"] or t["rc"] != 0:
                failures.append(f"bench rc={t['rc']} timed_out={t['timed_out']}")
            start = time.monotonic()
            c_lines = count_c_lines(trace_dir)
            document["count"] = dict(wall_s=time.monotonic() - start, c_lines=c_lines)
            flush("count")
            start = time.monotonic()
            document["files"] = file_inventory(trace_dir)
            document["files_wall_s"] = time.monotonic() - start
            document["verifier_default_workers"] = _effective_worker_count(len(document["files"]), None)
            flush("files")
            v = document["verify"]
            if not failures:
                v.update(argv=verifier_argv(trace_dir, t["commit_witness"], source),
                         cwd=str(args.repo_root), json_path=str(output / "verifier.json"),
                         stderr_path=str(output / "verifier.stderr"))
                v.update(timed_process(v["argv"], args.repo_root, args.verifier_timeout_s,
                                       Path(v["json_path"]), Path(v["stderr_path"])))
                if v["timed_out"] or v["rc"] not in (0, 1, 3):
                    document.update(status="failure", error=f"verifier rc={v['rc']} timed_out={v['timed_out']}")
                flush("verify-process")
                v.update(project_verifier(v["rc"], Path(v["json_path"]).read_text(), v["timed_out"]))
                if v["timed_out"] or v["rc"] not in (0, 1, 3) or not v["parse_ok"]:
                    failures.append(f"verifier classification={v['classification']} rc={v['rc']}")
                    document.update(status="failure", error=failures[-1])
                flush("verify-json")
            else:
                v["skipped_reason"] = "bench failed"
                flush("verify-skipped")
            dest = output / "trace"
            document["copy"]["dest"] = str(dest)
            start = time.monotonic()
            shutil.copytree(trace_dir, dest)
            document["copy"]["wall_s"] = time.monotonic() - start
            flush("copy")
            if failures:
                raise RuntimeError("; ".join(failures))
        flush("checkout-cleanup")
        document["status"] = "completed"
    except Exception as exc:
        document.update(status="failure", error=f"{type(exc).__name__}: {exc}")
        if output is not None:
            write_json(output / "result.json", document)
    finally:
        if scratch is not None:
            try:
                shutil.rmtree(scratch)
            except OSError as exc:
                document.update(status="failure", cleanup_error=str(exc))
                document["error"] = document["error"] or f"scratch cleanup: {exc}"
        document["finished_at"] = now()
        if output is not None:
            write_json(output / "result.json", document)
        else:
            print(json.dumps(document, ensure_ascii=False), file=sys.stderr)
    print(f"probe: {document['status']} output={output}")
    return 0 if document["status"] == "completed" else 1


def markdown(document):
    def cell(value, key):
        if value is None:
            return "null"
        if isinstance(value, float):
            return f"{value:.3f}"
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        elif isinstance(value, bool):
            value = str(value).lower()
        elif "sha256" in key and isinstance(value, str) and len(value) == 64:
            value = f"{value[:16]} ({value})"
        return str(value).replace('|', '&#124;').replace('\n', '<br>')

    def rows(value, prefix=""):
        if isinstance(value, dict) and value:
            for k, v in value.items():
                yield from rows(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            for i, v in enumerate(value):
                yield from rows(v, f"{prefix}[{i}]")
        else:
            yield f"| {prefix} | {cell(value, prefix)} |"

    sections = [("条件", document.get("conditions", {})),
                ("識別", {k: document[k] for k in ("schema_version", "label", "hostname", "cpu_model",
                                                    "affinity_cpus", "verifier_default_workers", "bindings")}),
                ("規模", dict(files=document['files'], c_lines=document['count']['c_lines'],
                              total_bytes=sum(f['bytes'] for f in document['files']),
                              total_lines=sum(f['lines'] for f in document['files']))),
                ("結果", {k: document.get(k) for k in ("status", "error", "trace", "verify")}),
                ("計時", {k: document.get(k) for k in ("started_at", "finished_at", "trace", "count",
                                                      "files_wall_s", "verify", "copy")})]
    parts = ["1 条件・1 反復・1 node の観測。2026-09-02 の並列化前 verifier とは code が違う。",
             "T_trace / T_verify: Popen 直前〜wait4 復帰。communicate_window_s は Popen 復帰後の近似窓。",
             "exceeded_pipeline_timeout_120s は主値 wall_s、communicate_window_exceeded_120s は近似窓と比較。T_count は C 行再計数のみ。",
             "総行数・bytes・sha256 は別 pass / 別計時。ru_maxrss は KiB。",
             "workload flags の順序の差は結果に影響しない。verdict は CLI JSON の値をそのまま転記。",
             "proof_surfaces が CLI JSON に無い場合は null、proof_surfaces_present=false。"]
    for title, values in sections:
        parts.extend([f"\n## {title}\n", "| 項目 | 値 |", "|---|---|", *rows(values)])
    return '\n'.join(parts) + '\n'


def selftest():
    # Relocated probes can import from the selected repository working directory.
    local_repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(local_repo if (local_repo / 'orchestrator').is_dir() else Path.cwd()))
    try:
        from orchestrator.campaign import pipeline
    except Exception as exc:
        print(f"pipeline-import: FAIL {exc}\nselftest: FAIL 0/1 cases")
        return 1
    checks = []

    def check(name, fn):
        try:
            ok = bool(fn())
        except Exception as exc:
            print(f"{name}: {type(exc).__name__}: {exc}")
            ok = False
        checks.append(ok)
        print(f"{name}: {'PASS' if ok else 'FAIL'}")

    check("pipeline-import", lambda: callable(pipeline._parse_commit_witness))
    check("bench-argv", lambda: bench_argv('/bin/b', 1000000, 48, 3) == [
        '/bin/b', '-ycsb_tuple_num=1000000', '-thread_num=48', '-ycsb_zipf_skew=0.9',
        '-ycsb_rratio=95', '-ycsb_rmw=0', '-ycsb_max_ope=10', '-extime=3', '-clocks_per_us=2100'])
    base = [os.path.realpath(sys.executable), '-B', '-m', 'orchestrator.verifier', '/trace', '--json']
    tail = ['--protocol', 'silo', '--ccbench-root', '/source']
    check("verifier-witness", lambda: verifier_argv('/trace', 0, '/source') == base + ['--expected-commits', '0'] + tail)
    check("verifier-no-witness", lambda: verifier_argv('/trace', None, '/source') == base + tail)
    configured = configure_argv('/source', '/build',
                                dict(gflags_expected_head='gf', glog_expected_head='gl'),
                                dict(cc_path='/gcc', cxx_path='/g++'),
                                {k: '/' + k for k in ('gflags', 'glog', 'masstree', 'mimalloc', 'googletest')})
    check('configure-defines', lambda: [x for x in configured if x.startswith('-DCCBENCH_')]
          == DEFINES + ['-DCCBENCH_CCACHE=OFF'] and '-DCMAKE_CXX_FLAGS=' in configured)
    for name, raw, expected in [
            ('normal', 'commit_counts_: 12\nbatch_commit_counts_: 2\n', (12, 2)),
            ('missing', 'other: 5\n', (None, None)),
            ('duplicate', 'commit_counts_: 1\ncommit_counts_: 2\n', (None, None)),
            ('comment', '#commit_counts_: 5\n', (None, None))]:
        check('witness-' + name, lambda raw=raw, expected=expected: pipeline._parse_commit_witness(raw) == expected)
    check('abort-counts', lambda: pipeline._parse_abort_counts('abort_counts_: 7\n') == 7)
    with tempfile.TemporaryDirectory(prefix='verifier-selftest-', dir='/tmp') as tmp:
        td = Path(tmp)
        for name, content in [('trace_0.log', 'C 1\nR 2\n'), ('trace_1.log', 'C 2\nC 3\n'),
                              ('trace_2.log', 'A 0\n C 4\n'), ('other.log', 'C 99\n')]:
            (td / name).write_text(content)
        check('count-three-files', lambda: count_c_lines(td) == 3)
        inventory = file_inventory(td)
        check('file-inventory', lambda: len(inventory) == 3 and sum(x['lines'] for x in inventory) == 6)
        doc = new_result('selftest')
        write_json(td / 'result.json', doc)
        check('schema-roundtrip', lambda: json.loads((td / 'result.json').read_text()) == doc)
    required = set('schema_version label status hostname cpu_model affinity_cpus verifier_default_workers started_at finished_at bindings trace count files verify copy error'.split())
    check('schema-keys', lambda: required <= doc.keys() and set(BINDING_KEYS) <= doc['bindings'].keys()
          and set(TIMING_KEYS + TRACE_KEYS) <= doc['trace'].keys()
          and set(TIMING_KEYS + VERIFY_KEYS) <= doc['verify'].keys()
          and {'wall_s', 'c_lines'} <= doc['count'].keys() and {'wall_s', 'dest'} <= doc['copy'].keys())
    for rc, verdict, expected in [(0, 'serializable', 'certified'), (1, 'non-serializable', 'non-serializable'),
                                  (3, 'indeterminate', 'indeterminate'), (2, 'usage', 'usage')]:
        v = dict(verdict=verdict, certified=rc == 0, stats=dict(txns=9, edges=4), anomalies=[],
                 anomaly_count=0, integrity={'clean': rc == 0}, proof_surfaces={'synthetic': True})
        raw = json.dumps({'runs': 1, 'results': [v]})
        p = project_verifier(rc, raw)
        check(f'verifier-rc-{rc}', lambda p=p, v=v, expected=expected:
              p['classification'] == expected and p['verdict'] == v['verdict']
              and p['certified'] == v['certified'] and p['proof_surfaces'] == v['proof_surfaces']
              and p['n_txns'] == 9 and p['n_edges'] == 4)
    check('invalid-json', lambda: project_verifier(0, '{')['classification'] == 'invalid-json')
    check('usage-no-json', lambda: project_verifier(2, '')['classification'] == 'usage')
    check('timeout', lambda: project_verifier(-9, '', True)['classification'] == 'failure')
    check('unexpected-rc', lambda: project_verifier(42, raw)['classification'] == 'failure')
    v.pop('proof_surfaces')
    check('absent-proof-surfaces', lambda: project_verifier(3, json.dumps({'runs': 1, 'results': [v]}))['proof_surfaces'] is None)
    from types import SimpleNamespace
    record = timing_values(10., 10.25, 12., 100., 102., 0,
                           SimpleNamespace(ru_utime=.1, ru_stime=.2, ru_maxrss=123))
    check('timing-monotonic', lambda: record['t_popen_monotonic'] <= record['t_popen_returned_monotonic'] <= record['t_wait_monotonic']
          and record['wall_s'] == 2. and record['communicate_window_s'] == 1.75)
    doc['bindings']['binary_sha256'] = 'a' * 64
    doc['count']['wall_s'] = 1.23456
    check('summary-format', lambda: '1.235' in markdown(doc) and 'a' * 16 + ' (' + 'a' * 64 + ')' in markdown(doc))
    passed = sum(checks)
    print(f"selftest: {'PASS' if all(checks) else 'FAIL'} {passed}/{len(checks)} cases")
    return 0 if all(checks) else 1


def absolute(value):
    path = Path(value)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError('must be an absolute path')
    return path.resolve()


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('selftest')
    p = sub.add_parser('run')
    for name in ('repo-root', 'third-party-cache', 'scratch-root', 'output-dir'):
        p.add_argument('--' + name, type=absolute, required=True)
    for name, default in [('records', 1000000), ('extime', 3), ('threads', 48),
                          ('run-timeout-s', 900), ('verifier-timeout-s', 3600)]:
        p.add_argument('--' + name, type=positive, default=default)
    p.add_argument('--label', required=True)
    p = sub.add_parser('summarize')
    p.add_argument('--input', type=absolute, required=True)
    p.add_argument('--output', type=absolute, required=True)
    args = parser.parse_args()
    if args.command == 'selftest':
        return selftest()
    if args.command == 'run':
        return run(args)
    if args.output.suffix != '.md':
        parser.error('--output must end in .md')
    document = json.loads(args.input.read_text())
    if document['schema_version'] != SCHEMA:
        parser.error('unsupported schema_version')
    with args.output.open('x', encoding='utf-8') as handle:
        handle.write(markdown(document))
    print(f'summarize: {args.output}')
    return 0


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    raise SystemExit(main())
```

## run-both.sh

```bash
#!/bin/bash
# 親専用の運転 script (計算ノード job の本体、generic dispatch の argv)。
# smoke (小規模 workload、同じ code path) を先に走らせ、rc=0 のときだけ本走 1 本を走らせる。
# 計測そのものは Codex author が書いた probe が行う。この file は順序と argv を固定するだけ。
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-cli-timing-probe
W=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verifier-cli-timing-probe
PY=python3.10
PROBE="$J/probe/verifier_cli_timing_probe.py"
CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache
echo "run-both: start $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)"
"$PY" -B "$PROBE" run --repo-root "$W" --third-party-cache "$CACHE" \
  --scratch-root /scr --output-dir "$J/run/smoke" \
  --label smoke --records 10000 --extime 1
rc=$?
echo "run-both: smoke rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [ "$rc" -ne 0 ]; then
  echo "run-both: smoke failed; main is not started"
  exit "$rc"
fi
"$PY" -B "$PROBE" run --repo-root "$W" --third-party-cache "$CACHE" \
  --scratch-root /scr --output-dir "$J/run/main" \
  --label main
rc=$?
echo "run-both: main rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit "$rc"
```
