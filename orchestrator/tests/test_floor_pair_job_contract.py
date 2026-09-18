"""Shell contracts only: no scheduler, real driver, or complete job execution."""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.pegasus_admission_registry import load_admission_registry

JOB = REPO / "tools/pegasus/floor_pair_campaign.sh"
SUBMIT = REPO / "tools/pegasus/submit_floor_pair.sh"
SPEC_DIR = REPO / "output/env/pegasus/floor-pair/t2288-f1"


def _shell_function(source, name):
    start = source.index(f"{name}() {{")
    return source[start:source.index("\n}", start) + 2]


def _functions(path, *names):
    source = path.read_text()
    return "\n".join(_shell_function(source, name) for name in names)


def _bash(source, *args):
    return subprocess.run(["bash", "-c", "set -Eeuo pipefail\n" + source,
                           "floor-pair-contract", *map(str, args)],
                          capture_output=True, text=True, timeout=10)


def _ok(result):
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)


def _refused(result, gate, reason, rc=4):
    assert result.returncode == rc, (result.returncode, result.stdout, result.stderr)
    assert result.stderr == json.dumps(dict(gate=gate, reason=reason), separators=(",", ":")) + "\n"


def _specs():
    paths = sorted(SPEC_DIR.glob("spec__*.json"))
    assert len(paths) == 3
    return [(path, json.loads(path.read_text())) for path in paths]


def test_registry_entries():
    entries = load_admission_registry(REPO)
    assert entries["tools/pegasus/floor_pair_campaign.sh"] == {
        "class": "dispatch-required",
        "reason": "PBS floor-pair window and finalize job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }
    assert entries["tools/pegasus/submit_floor_pair.sh"] == {
        "class": "local-ok",
        "reason": "login-side PBS floor-pair submitter",
        "primary_gate": "qsub submission; compute work stays in job body",
        "evidence": "static login-side submitter classification",
    }


def test_frozen_spec_pins():
    decisions = (REPO / "docs/decisions.md").read_text()
    section = decisions.split("## D2138.", 1)[1].split("\n## D", 1)[0]
    rows = re.findall(r"\| `spec__(.*?)` \| `([0-9a-f]{64})` \|", section)
    assert len(rows) == 3
    for short, sha in rows:
        name = "spec__" + short.replace("…", "env-pegasus__protocol-silo__threads-48")
        path = SPEC_DIR / name
        wl = re.search(r"workload-(rr\d+)-", name)[1]
        result = _bash(_functions(SUBMIT, "select_pin") +
                       '\nWORKLOAD=$1; select_pin; printf "%s\\n" "$SPEC_RELPATH" "$SPEC_SHA256"', wl)
        _ok(result)
        assert result.stdout.splitlines() == [str(path.relative_to(REPO)), sha]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha


def test_pbs_and_walltime_binding():
    source = JOB.read_text()
    assert source.startswith("#!/bin/bash\n")
    assert [line for line in source.splitlines() if line.startswith("#PBS")] == [
        "#PBS -A SFC", "#PBS -q gen_S", "#PBS -b 1", "#PBS --accept-sigterm=yes"]
    for path in (JOB, SUBMIT):
        assert path.stat().st_mode & 0o777 == 0o755
    result = _bash(_functions(SUBMIT, "build_qsub_argv") + '''
NONCE=n HEAD=h SPEC_RELPATH=spec SPEC_SHA256=sha MODE=window WINDOW_ID=rr95-w1
EVIDENCE_DIR=/evidence ELAPSTIM_REQ=24:00:00 WORKLOAD=rr95 WINDOW=w1
build_qsub_argv
printf '%s\n' "${qsub_cmd[@]}"
''')
    _ok(result)
    assert result.stdout.splitlines() == ["qsub", "-l", "elapstim_req=24:00:00", "-N", "fp-rr95-w1", "-v",
        "FP_NONCE=n,FP_EXPECTED_HEAD=h,FP_SPEC_RELPATH=spec,FP_SPEC_SHA256=sha,FP_MODE=window,FP_WINDOW_ID=rr95-w1,FP_EVIDENCE_DIR=/evidence,FP_ELAPSTIM_REQ=24:00:00",
        "-o", "/evidence/scheduler.stdout", "-e", "/evidence/scheduler.stderr", "tools/pegasus/floor_pair_campaign.sh"]


def test_walltime_values():
    for mode, value, seconds in (("window", "24:00:00", 86400), ("finalize", "00:30:00", 1800)):
        result = _bash(_functions(SUBMIT, "fail", "walltime_seconds", "select_walltime") +
                       '\nMODE=$1; select_walltime; printf "%s %s" "$ELAPSTIM_REQ" "$DURATION"', mode)
        _ok(result)
        assert result.stdout == f"{value} {seconds}"
        assert SUBMIT.read_text().count("ELAPSTIM_REQ=" + value) == 1
    assert not any("elapstim_req" in line for line in JOB.read_text().splitlines() if line.startswith("#PBS"))


def test_submitter_argument_set():
    prefix = _functions(SUBMIT, "fail", "parse_args") + '\nparse_args "$@"'
    valid = [("--workload", wl, *mode, "--dry-run") for wl in ("rr95", "rr50", "rr5")
             for mode in (("--window", "w1"), ("--window", "w2"), ("--finalize",))]
    for args in valid:
        _ok(_bash(prefix, *args))
    invalid = [(), ("--workload",), ("--workload", "rr20", "--finalize"),
               ("--workload", "rr95", "--window", "w3"),
               ("--workload", "rr95", "--window", "w1", "--finalize"),
               ("--workload", "rr95", "--finalize", "--finalize"),
               ("--workload", "rr95", "--workload", "rr50", "--finalize"),
               ("--workload", "rr95", "--finalize", "--dry-run", "--dry-run")]
    invalid += [("--workload", "rr95", "--finalize", arg, "x")
                for arg in ("--spec", "--head", "--evidence-root", "--walltime", "--assume-now", "--unknown")]
    for args in invalid:
        result = _bash(prefix, *args)
        assert result.returncode == 2 and json.loads(result.stderr)["gate"] == "arguments"
    for flag in ("-h", "--help"):
        _ok(_bash(prefix, flag))


def test_window_id_and_fields():
    for path, spec in _specs():
        for window in spec["windows"]:
            result = _bash(_functions(JOB, "fail", "read_window_bounds") +
                           '\nPY=$1; read_window_bounds "$2" "$3"; printf "%s %s" "$NOT_BEFORE" "$NOT_AFTER"',
                           sys.executable, path, window["window_id"])
            _ok(result)
            assert result.stdout == " ".join(str(int(datetime.fromisoformat(window[k].replace("Z", "+00:00")).timestamp()))
                                             for k in ("not_before", "not_after"))
    result = _bash(_functions(JOB, "fail", "read_window_bounds") +
                   '\nPY=$1; read_window_bounds "$2" w1', sys.executable, _specs()[0][0])
    _refused(result, "window", "invalid_window")


def test_window_gate_boundaries():
    # Observe all 30 cases per implementation in one shell, each in a subshell.
    cases = []
    expected = []
    for _, spec in _specs():
        for window in spec["windows"]:
            before, after = [int(datetime.fromisoformat(window[k].replace("Z", "+00:00")).timestamp())
                             for k in ("not_before", "not_after")]
            for now, reason in ((before-1, "before_window"), (before, None), (after-86400, None),
                                (after-86400+1, "insufficient_remaining_time"), (after, "insufficient_remaining_time")):
                cases.extend(map(str, (now, before, after, 86400)))
                expected.append((4 if reason else 0, reason))
    for path in (JOB, SUBMIT):
        result = _bash(_functions(path, "fail", "window_gate") + '''
while (( $# )); do
  rc=0
  message=$( (window_gate "$1" "$2" "$3" "$4") 2>&1) || rc=$?
  printf '%s|%s\n' "$rc" "$message"
  shift 4
done
''', *cases)
        _ok(result)
        assert result.stdout.splitlines() == [str(rc) + "|" +
            (json.dumps(dict(gate="window", reason=reason), separators=(",", ":")) if reason else "")
            for rc, reason in expected]


def test_hostname_gate():
    for host in ("bnode009", "bnode009.pegasus.local", "BNODE009", "pegasus02", "bnode009evil", ""):
        result = _bash(_functions(JOB, "fail", "require_compute_hostname") + '\nrequire_compute_hostname "$1"', host)
        if host in ("bnode009", "bnode009.pegasus.local", "BNODE009"):
            _ok(result)
        else:
            _refused(result, "site", "compute_node_required")


def test_gate_order_and_calls():
    # These stubs observe wiring only; the real gates are exercised above.
    snippet = _functions(JOB, "admit_and_run") + '''
trace() { printf '%s\n' "$1" >>"$TRACE"; }
require_compute_hostname() { trace site; if [[ "$STOP" == site ]]; then exit 4; fi; }
read_window_bounds() { trace bounds; }
check_time() { trace time; if [[ "$STOP" == time ]]; then exit 4; fi; }
prepare_scratch() { trace scratch; }
run_driver() { trace driver; }
TRACE=$1 STOP=$2 FP_MODE=window HOST_OBSERVED=unused FP_SPEC_RELPATH=unused FP_WINDOW_ID=unused
admit_and_run
'''
    for stop, trace in (("none", ["site", "bounds", "time", "scratch", "time", "driver"]),
                        ("site", ["site"]), ("time", ["site", "bounds", "time"])):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace"
            result = _bash(snippet, path, stop)
            assert result.returncode == (0 if stop == "none" else 4)
            assert path.read_text().splitlines() == trace


def test_driver_argv():
    bootstrap = "import sys; sys.path.insert(0, sys.argv.pop(1)); from orchestrator.campaign.floor_pair_driver import main; raise SystemExit(main())"
    for mode, tail in (("window", ["--execute-window", "rr95-w1"]), ("finalize", ["--finalize"])):
        result = _bash(_functions(JOB, "build_driver_argv") + '''
PY=/python REPO_ROOT=/checkout FP_SPEC_RELPATH=spec FP_SPEC_SHA256=sha FP_WINDOW_ID=rr95-w1 FP_MODE=$1
build_driver_argv
printf '%s\n' "${driver_argv[@]}"
''', mode)
        _ok(result)
        assert result.stdout.splitlines() == ["/python", "-I", "-B", "-c", bootstrap,
            "/checkout", "--repo-root", "/checkout", "--spec", "spec", "--expected-sha256", "sha", *tail]


def test_checkout_and_input_binding():
    for path in (JOB, SUBMIT):
        source = path.read_text()
        for text in ("rev-parse --show-toplevel", "realpath -e", "rev-parse --verify HEAD^{commit}",
                     'check_binaries "$REPO_ROOT"', "sha256sum --", "python3.10 python3.11 python3.12 python3",
                     "unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD LD_LIBRARY_PATH", "${!GIT_@}"):
            assert text in source
    source = SUBMIT.read_text()
    for text in ("symbolic-ref -q HEAD", "1) ;;", "status --porcelain --untracked-files=no",
                 'show "HEAD:$SPEC_RELPATH"', '"${blob_hash%% *}" == "$SPEC_SHA256"'):
        assert text in source
    # Exercise real byte/executable checks with synthetic bytes, never a benchmark.
    for path in (JOB, SUBMIT):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "binary"
            binary.write_bytes(b"contract-only")
            binary.chmod(0o700)
            spec = {"artifacts": [{"binary_relpath": "binary", "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest()}]}
            (root / "spec").write_text(json.dumps(spec))
            snippet = _functions(path, "fail", "check_binaries") + '\nPY=$1; check_binaries "$2" spec'
            _ok(_bash(snippet, sys.executable, root))
            binary.write_bytes(b"changed")
            _refused(_bash(snippet, sys.executable, root), "binary", "missing_or_mismatch")
            binary.chmod(0o600)
            _refused(_bash(snippet, sys.executable, root), "binary", "missing_or_mismatch")


def test_evidence_and_receipts():
    source = SUBMIT.read_text()
    assert "BASE=/work/1/SFC/tanab/izanagi-job-evidence/floor-pair" in source
    assert 'mkdir -m 0700 -- "$EVIDENCE_DIR"' in source
    assert 'import secrets; print(secrets.token_hex(16))' in source
    with tempfile.TemporaryDirectory() as directory:
        snippet = _functions(JOB, "write_result") + '''
PY=$1 FP_EVIDENCE_DIR=$2 PBS_JOBID=0:123.nqsv HOST_OBSERVED=bnode009
FP_NONCE=nonce FP_EXPECTED_HEAD=head FP_SPEC_RELPATH=spec FP_SPEC_SHA256=sha
FP_MODE=finalize FP_WINDOW_ID=none DRIVER_RC= STARTED_EPOCH=1 GATE=site REASON=compute_node_required
write_result 4
'''
        _ok(_bash(snippet, sys.executable, directory))
        payload = json.loads((Path(directory) / "job-result.json").read_text())
        assert set(payload) == set("schema_version pbs_jobid hostname nonce expected_head spec_relpath spec_sha256 mode window_id driver_rc driver_stdout_sha256 started_epoch completed_epoch job_rc gate reason".split())
        assert payload["window_id"] is None and payload["driver_rc"] is None and payload["driver_stdout_sha256"] is None
        assert payload["job_rc"] == 4 and payload["schema_version"] == "pegasus-floor-pair-job-result/v1"
        before = (Path(directory) / "job-result.json").read_bytes()
        assert _bash(snippet, sys.executable, directory).returncode != 0
        assert (Path(directory) / "job-result.json").read_bytes() == before


def test_dry_run_has_no_execution():
    snippet = _functions(SUBMIT, "fail", "build_qsub_argv", "write_pre_submit", "write_submit_receipt", "submit_or_dry_run") + '''
qsub() { printf '%s\n' called >>"$TRACE"; printf 'Request 0:123.nqsv submitted.\n'; }
PY=$1 EVIDENCE_DIR=$2 REPO_ROOT=$2 TRACE=$2/trace DRY_RUN=$3
NONCE=n HEAD=h SPEC_RELPATH=spec SPEC_SHA256=sha MODE=window WINDOW_ID=rr95-w1
ELAPSTIM_REQ=24:00:00 DURATION=86400 WORKLOAD=rr95 WINDOW=w1 PREPARED_EPOCH=1
build_qsub_argv
write_pre_submit
submit_or_dry_run
'''
    for dry in (0, 1):
        with tempfile.TemporaryDirectory() as directory:
            _ok(_bash(snippet, sys.executable, directory, dry))
            receipt = json.loads((Path(directory) / "submit-receipt.json").read_text())
            assert (Path(directory) / "trace").exists() == (not dry)
            assert receipt["status"] == ("dry_run" if dry else "submitted")
            assert receipt["qsub_rc"] == (None if dry else 0)
            assert receipt["pbs_jobid"] == (None if dry else "0:123.nqsv")
            assert receipt["schema_version"] == "pegasus-floor-pair-submit-receipt/v1"
            assert receipt["request"] == dict(project="SFC", queue="gen_S", nodes=1, elapstim_req="24:00:00", elapstim_req_s=86400)


def test_child_rc_collection():
    for child in ("exit 7", 'kill -TERM "$PPID"; sleep 0.1; exit 7'):
        with tempfile.TemporaryDirectory() as directory:
            result = _bash(_functions(JOB, "fail", "record_signal", "run_driver", "write_result") + '''
PY=$1 FP_EVIDENCE_DIR=$2 SIGNAL_RC=0
trap 'fail 4 driver unexpected_err_trap' ERR
driver_argv=(sh -c "$3")
run_driver
PBS_JOBID=0:123.nqsv HOST_OBSERVED=bnode009 FP_NONCE=n FP_EXPECTED_HEAD=h
FP_SPEC_RELPATH=spec FP_SPEC_SHA256=sha FP_MODE=window FP_WINDOW_ID=rr95-w1 STARTED_EPOCH=1
write_result "$JOB_RC"
exit "$JOB_RC"
''', sys.executable, directory, child)
            assert result.returncode == 7, result.stderr
            payload = json.loads((Path(directory) / "job-result.json").read_text())
            assert payload["driver_rc"] == payload["job_rc"] == 7
            assert payload["driver_stdout_sha256"] == hashlib.sha256(b"").hexdigest()
            assert payload["reason"] == ("completed" if child == "exit 7" else "signal_observed")


def test_scratch_name_normalizes_colon():
    # Extract the assignment only; never create a real /scr directory.
    assignment = next(line for line in _shell_function(JOB.read_text(), "prepare_scratch").splitlines()
                      if line.strip().startswith("export TMPDIR="))
    result = _bash('PBS_JOBID=$1\n' + assignment + '\nprintf "%s" "$TMPDIR"', "0:123.nqsv")
    _ok(result)
    assert result.stdout == "/scr/0_123.nqsv"


def _output_case(root, spec, mode="window"):
    (root / "spec").write_text(json.dumps(spec))
    return _bash(_functions(SUBMIT, "check_outputs") + '''
PY=$1 REPO_ROOT=$2 SPEC_RELPATH=spec MODE=$3 WINDOW_ID=rr95-w1 HEAD=expected
check_outputs
''', sys.executable, root, mode)


def test_submitter_head_consistency_preflight():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = dict(windows=[dict(window_id="rr95-w1", artifact_relpath="one"),
                             dict(window_id="rr95-w2", artifact_relpath="two")])
        _ok(_output_case(root, spec))
        (root / "two").write_text('{"loaded_head":"different"}\n')
        _refused(_output_case(root, spec), "outputs", "loaded_head_mismatch")
        (root / "two").write_text('{"loaded_head":"expected"}\n')
        _ok(_output_case(root, spec))
        (root / "one").symlink_to(root / "absent")
        _refused(_output_case(root, spec), "outputs", "window_exists")


def test_finalize_preflight_requires_terminal():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = dict(outputs=dict(summary_relpath="summary"), windows=[
            dict(window_id="rr95-w1", artifact_relpath="one"), dict(window_id="rr95-w2", artifact_relpath="two")])
        _refused(_output_case(root, spec, "finalize"), "outputs", "window_missing")
        for name in ("one", "two"):
            (root / name).write_text('{"loaded_head":"expected"}\n{"event":"terminal","status":"incomplete"}\n')
        _ok(_output_case(root, spec, "finalize"))
        (root / "two").write_text('{"loaded_head":"expected"}\n{"event":"measurement"}\n')
        _refused(_output_case(root, spec, "finalize"), "outputs", "terminal_missing")
        (root / "summary").symlink_to(root / "absent")
        _refused(_output_case(root, spec, "finalize"), "outputs", "summary_exists")


def test_no_build_or_output_replacement():
    for path in (JOB, SUBMIT):
        source = path.read_text()
        for forbidden in ("cmake --build", "--validate-only", "--assume-now", "rm -", "unlink(", "shutil.rmtree", "kill ", "qsub -V"):
            assert forbidden not in source
        assert "set -Eeuo pipefail" in source and "umask 077" in source
    assert "git nm pgrep sha256sum hostname date realpath mkdir env" in JOB.read_text()


def _run():
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
                passed += 1
            except Exception as exc:
                print("FAIL", name, type(exc).__name__, str(exc))
                failed += 1
    print(f"{passed} passed, {failed} failed")
    return int(bool(failed))


if __name__ == "__main__":
    sys.exit(_run())
