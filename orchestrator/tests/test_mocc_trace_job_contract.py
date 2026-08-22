"""Contract checks for the login-side Mocc trace pilot submitter."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import textwrap


REPO_ROOT = Path(__file__).resolve().parents[2]
SUBMITTER = REPO_ROOT / "tools/pegasus/submit_mocc_trace.sh"
POLICY = REPO_ROOT / "tools/pegasus/mocc_trace_v1_policy.json"
NEW_OID = "ef9328a35d49b1b9b610f244bee22ad7f10b8b66"
BASE_OID = "511c9538e4e8efa54b45cda62e72389ed3b706ec"


def _make_executable(path: Path, contents: str) -> None:
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _fake_git(bin_dir: Path, source_commit: str) -> None:
    _make_executable(
        bin_dir / "git",
        f"""
        #!/bin/bash
        # Hermetic git surface for the submitter contract: no repository mutation.
        if [[ "$1" == "-C" ]]; then
          repo="$2"
          shift 2
        fi
        case "$1" in
          rev-parse)
            if [[ "$2" == "HEAD" && "$repo" != *"external/ccbench" ]]; then
              printf '%s\\n' '{source_commit}'
              exit 0
            fi
            if [[ "$2" == "{NEW_OID}^{{commit}}" && "$repo" == *"external/ccbench" ]]; then
              printf '%s\\n' '{NEW_OID}'
              exit 0
            fi
            ;;
          status)
            exit 0
            ;;
        esac
        echo "unexpected fake git argv: $*" >&2
        exit 97
        """,
    )


def test_mocc_trace_submit_dry_run_contract(tmp_path: Path) -> None:
    """Dry-run emits both receipts and never invokes qsub."""

    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    attempts_root = tmp_path / "attempts"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    source_commit = "0123456789abcdef0123456789abcdef01234567"
    _fake_git(bin_dir, source_commit)
    qsub_marker = tmp_path / "qsub-called"
    _make_executable(
        bin_dir / "qsub",
        f"""
        touch '{qsub_marker}'
        exit 99
        """,
    )

    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    environment["IZANAGI_PEGASUS_THIRDPARTY_CACHE"] = str(tmp_path / "third-party-cache")
    result = subprocess.run(
        [
            "bash",
            str(SUBMITTER),
            "--dry-run",
            "--repo-root",
            str(repo_root),
            "--attempts-root",
            str(attempts_root),
            "--job-script",
            str(REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"),
            "--trace-mode",
            "0",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not qsub_marker.exists(), result.stdout

    submissions = sorted((attempts_root / "submissions").iterdir())
    assert len(submissions) == 1
    submission = submissions[0]
    pre_submit = json.loads((submission / "pre-submit.json").read_text(encoding="utf-8"))
    receipt = json.loads((submission / "submit-receipt.json").read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))

    for document in (pre_submit, receipt):
        assert document["schema_version"] in {
            "pegasus-pre-submit/v1",
            "pegasus-submit-receipt/v1",
        }
        assert document["dry_run"] is True
        mocc_trace = document["mocc_trace"]
        assert mocc_trace["base_oid"] == BASE_OID
        assert mocc_trace["new_oid"] == NEW_OID
        assert mocc_trace["trace_mode"] == 0
        assert mocc_trace["workload"] == policy["mocc_trace"]["workload"]
        assert mocc_trace["workload_note"] == (
            "parent-selected pilot workload; not a reproduction of historical T-816 measurements"
        )

    assert pre_submit["source_commit"] == source_commit
    assert pre_submit["request"]["project"] == "SFC"
    assert pre_submit["request"]["queue"] == "gen_S"
    assert pre_submit["request"]["nodes"] == 1
    assert pre_submit["request"]["elapstim_req_s"] == 3600
    assert any(
        "IZANAGI_MOCC_TRACE_MODE=0" in argument
        for argument in pre_submit["request"]["qsub_argv"]
    )
    assert any(
        "IZANAGI_SUBMISSION_NONCE=" in argument
        for argument in pre_submit["request"]["qsub_argv"]
    )
    assert receipt["qsub"]["request_id"].startswith("dry-run-")
    assert receipt["qsub"]["argv"] == pre_submit["request"]["qsub_argv"]
    assert (submission / "qsub.rc").read_text(encoding="utf-8").strip() == "0"


def test_mocc_trace_submit_trace_mode_one_dry_run_contract(tmp_path: Path) -> None:
    """Trace-mode=1 dry-run carries the mode and policy workload without qsub."""

    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    attempts_root = tmp_path / "attempts"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    source_commit = "fedcba9876543210fedcba9876543210fedcba98"
    _fake_git(bin_dir, source_commit)
    qsub_marker = tmp_path / "qsub-called"
    _make_executable(
        bin_dir / "qsub",
        f"""
        touch '{qsub_marker}'
        exit 99
        """,
    )

    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    environment["IZANAGI_PEGASUS_THIRDPARTY_CACHE"] = str(
        tmp_path / "third-party-cache"
    )
    result = subprocess.run(
        [
            "bash",
            str(SUBMITTER),
            "--dry-run",
            "--repo-root",
            str(repo_root),
            "--attempts-root",
            str(attempts_root),
            "--job-script",
            str(REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"),
            "--trace-mode",
            "1",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not qsub_marker.exists(), result.stdout

    submissions = sorted((attempts_root / "submissions").iterdir())
    assert len(submissions) == 1
    submission = submissions[0]
    pre_submit = json.loads((submission / "pre-submit.json").read_text(encoding="utf-8"))
    receipt = json.loads((submission / "submit-receipt.json").read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))

    for document in (pre_submit, receipt):
        assert document["dry_run"] is True
        assert document["mocc_trace"]["trace_mode"] == 1
        assert document["mocc_trace"]["workload"] == policy["mocc_trace"]["workload"]
        assert document["mocc_trace"]["workload"]["ycsb_max_ope"] == 10

    assert pre_submit["source_commit"] == source_commit
    assert any(
        "IZANAGI_MOCC_TRACE_MODE=1" in argument
        for argument in pre_submit["request"]["qsub_argv"]
    )
    assert receipt["qsub"]["request_id"].startswith("dry-run-")
    assert receipt["qsub"]["argv"] == pre_submit["request"]["qsub_argv"]
    assert (submission / "qsub.rc").read_text(encoding="utf-8").strip() == "0"


def test_mocc_trace_cpu_model_gate_normalizes_and_rejects_true_mismatch(
    tmp_path: Path,
) -> None:
    """The job-side CPU gate absorbs notation drift but remains fail-closed."""

    pilot = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
    source = pilot.read_text(encoding="utf-8")
    start_marker = "CPU_MODEL=$(awk"
    end_marker = "\nmodule_rc=0"
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker)
    assert start < end
    cpu_gate = source[start:end]

    cpuinfo_marker = "/proc/cpuinfo"
    assert cpu_gate.count(cpuinfo_marker) == 1
    cpu_gate = cpu_gate.replace(cpuinfo_marker, '"$CPUINFO_PATH"', 1)
    assert cpu_gate.count(cpuinfo_marker) == 0
    assert cpu_gate.count('"$CPUINFO_PATH"') == 1

    assert r"s/\((R|TM)\)//g" in cpu_gate
    assert "observed_normalized=" in cpu_gate
    assert '"cpu_model": cpu_model' in source
    assert (
        '"expected_cpu_model": submit_receipt["policy"]["expected_cpu_model"]'
        in source
    )
    assert '"cpu_model_normalized"' not in source

    cpuinfo_path = tmp_path / "cpuinfo"
    raw_model = "Intel(R) Xeon(R)   Platinum(TM)\t8468"
    cpuinfo_path.write_text(
        f"  model name : {raw_model}\n",
        encoding="utf-8",
    )

    def run_gate(
        expected: str, attempt_dir: Path, failure_path: Path
    ) -> subprocess.CompletedProcess[str]:
        attempt_dir.mkdir()
        environment = os.environ.copy()
        environment.update(
            {
                "ATTEMPT_DIR": str(attempt_dir),
                "CPUINFO_PATH": str(cpuinfo_path),
                "EXPECTED_CPU": expected,
                "FAILURE_PATH": str(failure_path),
            }
        )
        return subprocess.run(
            [
                "bash",
                "-c",
                "write_failure() {\n"
                '  printf \'%s\\n\' "$3" >"$FAILURE_PATH"\n'
                "}\n"
                f"{cpu_gate}\n",
            ],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    success_failure = tmp_path / "success-failure"
    success_attempt = tmp_path / "success-attempt"
    success = run_gate(
        "Intel Xeon Platinum 8468",
        success_attempt,
        success_failure,
    )
    assert success.returncode == 0, success.stderr
    assert not success_failure.exists()
    assert (success_attempt / "cpu-model.stdout").read_text(
        encoding="utf-8"
    ) == f"{raw_model}\n"

    mismatch_failure = tmp_path / "mismatch-failure"
    mismatch_attempt = tmp_path / "mismatch-attempt"
    mismatch = run_gate(
        "Intel Xeon Platinum 8488",
        mismatch_attempt,
        mismatch_failure,
    )
    assert mismatch.returncode == 2, mismatch.stderr
    assert mismatch_failure.read_text(encoding="utf-8") == (
        "CPU model mismatch: expected=Intel Xeon Platinum 8488 "
        "observed_normalized=Intel Xeon Platinum 8468\n"
    )
