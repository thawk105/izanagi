"""Contract checks for the login-side Mocc trace pilot submitter."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import shutil
import textwrap

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SUBMITTER = REPO_ROOT / "tools/pegasus/submit_mocc_trace.sh"
POLICY = REPO_ROOT / "tools/pegasus/mocc_trace_v1_policy.json"
PILOT = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
NEW_OID = "058d0c4e5f237d88ec1c2ebe0739113d82906e47"
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


def test_mocc_trace_checker_interpreter_gate_selects_first_importable_candidate(
    tmp_path: Path,
) -> None:
    pilot = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
    source = pilot.read_text(encoding="utf-8")
    start_marker = '  CHECKER_PY=""'
    end_marker = "\n  CHECKER_RC=0"
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker)
    assert start < end
    checker_gate = source[start:end]

    assert "python3 python3.10 python3.11 python3.12" in checker_gate
    assert "-I" not in checker_gate
    assert "import orchestrator.campaign.source_digest" in checker_gate
    assert "sys.version_info >= (3, 10)" in checker_gate

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    real_realpath = shutil.which("realpath")
    assert real_realpath is not None
    (bin_dir / "realpath").symlink_to(real_realpath)

    paths: dict[str, Path] = {}
    argv_paths: dict[str, Path] = {}
    for name, gate_rc in {
        "python3": 1,
        "python3.10": 0,
        "python3.11": 0,
        "python3.12": 0,
    }.items():
        stub = bin_dir / name
        argv_path = tmp_path / f"{name}.argv"
        cwd_path = tmp_path / f"{name}.cwd"
        _make_executable(
            stub,
            f"""
            #!/bin/sh
            printf '%s\\n' "$@" >{shlex.quote(str(argv_path))}
            printf '%s\\n' "$PWD" >{shlex.quote(str(cwd_path))}
            exit {gate_rc}
            """,
        )
        paths[name] = stub
        argv_paths[name] = argv_path

    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo_root))}",
            "",
        ]
    )
    suffix = '\nprintf \'%s\\n\' "$CHECKER_PY"\n'
    result = subprocess.run(
        ["/bin/bash", "-c", prefix + checker_gate + suffix],
        cwd=REPO_ROOT,
        env={"PATH": str(bin_dir)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    selected = os.path.realpath(paths["python3.10"])
    assert result.stdout.strip() == selected
    assert argv_paths["python3"].exists()
    assert argv_paths["python3.10"].exists()
    assert not argv_paths["python3.11"].exists()
    assert not argv_paths["python3.12"].exists()
    selected_argv = argv_paths["python3.10"].read_text(
        encoding="utf-8"
    ).splitlines()
    assert selected_argv[0] == "-c"
    assert "import orchestrator.campaign.source_digest" in selected_argv[1]
    assert selected_argv[-1] == str(repo_root)
    assert (tmp_path / "python3.10.cwd").read_text(encoding="utf-8").strip() == str(
        repo_root
    )


def test_mocc_trace_checker_uses_selected_interpreter_for_actual_argv(
    tmp_path: Path,
) -> None:
    pilot = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
    source = pilot.read_text(encoding="utf-8")
    start_marker = "  CHECKER_RC=0"
    end_marker = '\n  printf \'%s\\n\' "$CHECKER_RC"'
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker)
    assert start < end
    checker_invocation = source[start:end]

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    selected_argv_path = tmp_path / "selected.argv"
    selected_cwd_path = tmp_path / "selected.cwd"
    selected = tmp_path / "selected-python"
    _make_executable(
        selected,
        f"""
        #!/bin/sh
        printf '%s\\n' "$@" >{shlex.quote(str(selected_argv_path))}
        printf '%s\\n' "$PWD" >{shlex.quote(str(selected_cwd_path))}
        exit 0
        """,
    )
    fallback_marker = tmp_path / "fallback-called"
    _make_executable(
        bin_dir / "python3",
        f"""
        #!/bin/sh
        touch {shlex.quote(str(fallback_marker))}
        exit 99
        """,
    )

    build_source = tmp_path / "build-source"
    cxx_path = tmp_path / "g++"
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"CHECKER_PY={shlex.quote(str(selected))}",
            f"REPO_ROOT={shlex.quote(str(repo_root))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt_dir))}",
            f"BUILD_SOURCE={shlex.quote(str(build_source))}",
            "BASE_OID=base-oid",
            "NEW_OID=new-oid",
            f"CXX_PATH={shlex.quote(str(cxx_path))}",
            "",
        ]
    )
    suffix = '\nprintf \'checker_rc=%s\\n\' "$CHECKER_RC"\n'
    result = subprocess.run(
        ["/bin/bash", "-c", prefix + checker_invocation + suffix],
        cwd=REPO_ROOT,
        env={"PATH": str(bin_dir)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "checker_rc=0\n"
    assert not fallback_marker.exists()
    assert selected_cwd_path.read_text(encoding="utf-8").strip() == str(repo_root)
    assert selected_argv_path.read_text(encoding="utf-8").splitlines() == [
        str(repo_root / "tools/check_trace0_preprocess_identity.py"),
        "--repo",
        str(build_source),
        "--old",
        "base-oid",
        "--new",
        "new-oid",
        "--cxx",
        str(cxx_path),
        "--expect-paths",
        "cc/mocc/transaction.cc",
    ]


def test_mocc_trace_checker_resolver_success_path_uses_resolved_interpreter_once(
    tmp_path: Path,
) -> None:
    """Resolver fallthrough and checker launch remain one connected success path."""

    pilot = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
    source = pilot.read_text(encoding="utf-8")
    start_marker = '  CHECKER_PY=""'
    end_marker = '\n  printf \'%s\\n\' "$CHECKER_RC"'
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker)
    assert start < end
    checker_success_path = source[start:end]

    repo_root = tmp_path / "repo"
    package_dir = repo_root / "orchestrator/campaign"
    package_dir.mkdir(parents=True)
    (repo_root / "orchestrator/__init__.py").write_text("", encoding="utf-8")
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "source_digest.py").write_text("", encoding="utf-8")
    external_pythonpath = tmp_path / "external-pythonpath"
    external_package_dir = external_pythonpath / "orchestrator/campaign"
    external_package_dir.mkdir(parents=True)
    (external_pythonpath / "orchestrator/__init__.py").write_text(
        "", encoding="utf-8"
    )
    (external_package_dir / "__init__.py").write_text("", encoding="utf-8")
    (external_package_dir / "source_digest.py").write_text(
        "raise RuntimeError('external orchestrator must not win')\n", encoding="utf-8"
    )
    inherited_pythonpath = os.pathsep.join((str(external_pythonpath), str(repo_root)))
    expected_pythonpath = os.pathsep.join((str(repo_root), inherited_pythonpath))
    checker_path = repo_root / "tools/check_trace0_preprocess_identity.py"
    checker_path.parent.mkdir()
    checker_path.write_text("# checker argv target\n", encoding="utf-8")

    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    build_source = tmp_path / "build-source"
    cxx_path = tmp_path / "g++"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    real_realpath = shutil.which("realpath")
    real_python = shutil.which("python3")
    assert real_realpath is not None
    assert real_python is not None

    realpath_order_path = tmp_path / "realpath-order"
    realpath_failure_path = bin_dir / "python3.10"
    realpath_failure_invoked_path = tmp_path / "realpath-failure-invoked"
    _make_executable(
        bin_dir / "realpath",
        f"""
        #!/bin/bash
        target=${{!#}}
        printf '%s\\n' "$target" >>"$REALPATH_ORDER_PATH"
        if [[ "$target" == "$REALPATH_FAILURE_PATH" ]]; then
          exit 1
        fi
        exec {shlex.quote(real_realpath)} "$@"
        """,
    )
    _make_executable(
        realpath_failure_path,
        """
        #!/bin/bash
        touch "$REALPATH_FAILURE_INVOKED_PATH"
        exit 96
        """,
    )

    probe_failure_path = bin_dir / "python3.11"
    probe_failure_calls_path = tmp_path / "probe-failure-calls"
    probe_failure_checker_path = tmp_path / "probe-failure-checker"
    _make_executable(
        probe_failure_path,
        """
        #!/bin/bash
        if [[ "${1:-}" == "-c" ]]; then
          printf '%s\\n' probe >>"$PROBE_FAILURE_CALLS_PATH"
          exit 1
        fi
        touch "$PROBE_FAILURE_CHECKER_PATH"
        exit 95
        """,
    )

    selected_real = tmp_path / "selected-python"
    selected_calls_path = tmp_path / "selected-calls"
    selected_argv_path = tmp_path / "selected.argv"
    selected_cwd_path = tmp_path / "selected.cwd"
    selected_probe_pythonpath_path = tmp_path / "selected-probe.pythonpath"
    selected_checker_pythonpath_path = tmp_path / "selected-checker.pythonpath"
    _make_executable(
        selected_real,
        f"""
        #!/bin/bash
        if [[ "${{1:-}}" == "-c" ]]; then
          printf '%s\\n' probe >>"$SELECTED_CALLS_PATH"
          printf '%s\\n' "$PYTHONPATH" >"$SELECTED_PROBE_PYTHONPATH_PATH"
          exec {shlex.quote(real_python)} "$@"
        fi
        if [[ "${{1:-}}" == "$CHECKER_PATH" ]]; then
          printf '%s\\n' checker >>"$SELECTED_CALLS_PATH"
          printf '%s\\n' "$@" >"$SELECTED_ARGV_PATH"
          printf '%s\\n' "$PWD" >"$SELECTED_CWD_PATH"
          printf '%s\\n' "$PYTHONPATH" >"$SELECTED_CHECKER_PYTHONPATH_PATH"
          exit 0
        fi
        exit 94
        """,
    )
    selected_link = bin_dir / "python3.12"
    selected_link.symlink_to(selected_real)
    assert not (bin_dir / "python3").exists()

    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo_root))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt_dir))}",
            f"BUILD_SOURCE={shlex.quote(str(build_source))}",
            "BASE_OID=base-oid",
            "NEW_OID=new-oid",
            f"CXX_PATH={shlex.quote(str(cxx_path))}",
            "",
        ]
    )
    suffix = '\nprintf \'selected=%s\\nchecker_rc=%s\\n\' "$CHECKER_PY" "$CHECKER_RC"\n'
    result = subprocess.run(
        ["/bin/bash", "-c", prefix + checker_success_path + suffix],
        cwd=REPO_ROOT,
        env={
            "PATH": str(bin_dir),
            "REALPATH_ORDER_PATH": str(realpath_order_path),
            "REALPATH_FAILURE_PATH": str(realpath_failure_path),
            "REALPATH_FAILURE_INVOKED_PATH": str(realpath_failure_invoked_path),
            "PROBE_FAILURE_CALLS_PATH": str(probe_failure_calls_path),
            "PROBE_FAILURE_CHECKER_PATH": str(probe_failure_checker_path),
            "SELECTED_CALLS_PATH": str(selected_calls_path),
            "SELECTED_ARGV_PATH": str(selected_argv_path),
            "SELECTED_CWD_PATH": str(selected_cwd_path),
            "SELECTED_PROBE_PYTHONPATH_PATH": str(selected_probe_pythonpath_path),
            "SELECTED_CHECKER_PYTHONPATH_PATH": str(
                selected_checker_pythonpath_path
            ),
            "CHECKER_PATH": str(checker_path),
            "PYTHONPATH": inherited_pythonpath,
        },
        capture_output=True,
        text=True,
        check=False,
    )

    selected_resolved = os.path.realpath(selected_link)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"selected={selected_resolved}\nchecker_rc=0\n"
    assert realpath_order_path.read_text(encoding="utf-8").splitlines() == [
        str(realpath_failure_path),
        str(probe_failure_path),
        str(selected_link),
    ]
    assert not realpath_failure_invoked_path.exists()
    assert probe_failure_calls_path.read_text(encoding="utf-8").splitlines() == [
        "probe"
    ]
    assert not probe_failure_checker_path.exists()
    assert selected_calls_path.read_text(encoding="utf-8").splitlines() == [
        "probe",
        "checker",
    ]
    assert selected_probe_pythonpath_path.read_text(encoding="utf-8").strip() == (
        expected_pythonpath
    )
    assert selected_checker_pythonpath_path.read_text(encoding="utf-8").strip() == (
        expected_pythonpath
    )
    assert selected_cwd_path.read_text(encoding="utf-8").strip() == str(repo_root)
    assert selected_argv_path.read_text(encoding="utf-8").splitlines() == [
        str(checker_path),
        "--repo",
        str(build_source),
        "--old",
        "base-oid",
        "--new",
        "new-oid",
        "--cxx",
        str(cxx_path),
        "--expect-paths",
        "cc/mocc/transaction.cc",
    ]


def test_mocc_trace_checker_interpreter_gate_fails_closed_with_skip_artifacts(
    tmp_path: Path,
) -> None:
    pilot = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
    source = pilot.read_text(encoding="utf-8")
    start_marker = '  CHECKER_PY=""'
    end_marker = "\nelse\n  build_mode 1"
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker)
    assert start < end
    checker_block = source[start:end]

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    failure_path = attempt_dir / "failure.json"
    order_path = tmp_path / "probe-order"
    checker_called_path = tmp_path / "checker-called"
    workload_called_path = tmp_path / "workload-called"
    checker_path = repo_root / "tools/check_trace0_preprocess_identity.py"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    real_realpath = shutil.which("realpath")
    real_python = shutil.which("python3")
    assert real_realpath is not None
    assert real_python is not None
    (bin_dir / "realpath").symlink_to(real_realpath)

    candidate_names = ("python3", "python3.10", "python3.11", "python3.12")
    candidate_paths: dict[str, Path] = {}
    for name in candidate_names:
        stub = bin_dir / name
        _make_executable(
            stub,
            f"""
            #!/bin/bash
            if [[ "${{1:-}}" == "-c" ]]; then
              printf '%s\\n' {shlex.quote(name)} >>"$ORDER_PATH"
              exit 1
            fi
            if [[ "${{1:-}}" == "$CHECKER_PATH" ]]; then
              touch "$CHECKER_CALLED_PATH"
              exit 98
            fi
            exec {shlex.quote(real_python)} "$@"
            """,
        )
        candidate_paths[name] = stub

    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo_root))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt_dir))}",
            f"FAILURE_PATH={shlex.quote(str(failure_path))}",
            "write_failure() {",
            '  printf \'rc=%s\\nstage=%s\\nmessage=%s\\n\' "$1" "$2" "$3" >"$FAILURE_PATH"',
            "}",
            "",
        ]
    )
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            prefix + checker_block + '\ntouch "$WORKLOAD_CALLED_PATH"\n',
        ],
        cwd=REPO_ROOT,
        env={
            "PATH": str(bin_dir),
            "ORDER_PATH": str(order_path),
            "CHECKER_PATH": str(checker_path),
            "CHECKER_CALLED_PATH": str(checker_called_path),
            "WORKLOAD_CALLED_PATH": str(workload_called_path),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2, result.stderr
    assert order_path.read_text(encoding="utf-8").splitlines() == list(
        candidate_names
    )
    assert not checker_called_path.exists()
    assert not workload_called_path.exists()
    for name in candidate_names:
        resolved = os.path.realpath(candidate_paths[name])
        assert f"{name}={resolved}" in (
            attempt_dir / "trace0-preprocess-identity.stderr"
        ).read_text(encoding="utf-8")
    assert (attempt_dir / "trace0-preprocess-identity.rc").read_text(
        encoding="utf-8"
    ) == "2\n"
    skipped = json.loads(
        (attempt_dir / "trace0-execution.json").read_text(encoding="utf-8")
    )
    assert skipped == {
        "schema_version": "mocc-trace0-execution/v1",
        "status": "skipped",
        "reason": "TRACE=0 preprocess identity checker failed closed",
        "checker_rc": 2,
    }
    failure = failure_path.read_text(encoding="utf-8")
    assert "rc=2\n" in failure
    assert "stage=trace0_preprocess_identity\n" in failure
    assert "TRACE=0 workload skipped" in failure


def test_mocc_trace_verifier_interpreter_gate_selects_first_importable_candidate(
    tmp_path: Path,
) -> None:
    pilot = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
    source = pilot.read_text(encoding="utf-8")
    start_marker = '  VERIFIER_PY=""'
    end_marker = "\n  verifier_rc=0"
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker)
    assert start < end
    verifier_gate = source[start:end]

    assert "python3 python3.10 python3.11 python3.12" in verifier_gate
    assert "-I" not in verifier_gate
    assert "import orchestrator.verifier" in verifier_gate
    assert "sys.version_info >= (3, 10)" in verifier_gate

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    failure_path = tmp_path / "failure"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    real_realpath = shutil.which("realpath")
    assert real_realpath is not None
    (bin_dir / "realpath").symlink_to(real_realpath)

    paths: dict[str, Path] = {}
    argv_paths: dict[str, Path] = {}
    for name, gate_rc in {
        "python3": 1,
        "python3.10": 0,
        "python3.11": 0,
        "python3.12": 0,
    }.items():
        stub = bin_dir / name
        argv_path = tmp_path / f"{name}.argv"
        cwd_path = tmp_path / f"{name}.cwd"
        _make_executable(
            stub,
            f"""
            #!/bin/sh
            printf '%s\\n' "$@" >{shlex.quote(str(argv_path))}
            printf '%s\\n' "$PWD" >{shlex.quote(str(cwd_path))}
            exit {gate_rc}
            """,
        )
        paths[name] = stub
        argv_paths[name] = argv_path

    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo_root))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt_dir))}",
            f"FAILURE_PATH={shlex.quote(str(failure_path))}",
            "write_failure() {",
            '  printf \'rc=%s\\nstage=%s\\nmessage=%s\\n\' "$1" "$2" "$3" >"$FAILURE_PATH"',
            "}",
            "",
        ]
    )
    suffix = '\nprintf \'%s\\n\' "$VERIFIER_PY"\n'
    result = subprocess.run(
        ["/bin/bash", "-c", prefix + verifier_gate + suffix],
        cwd=REPO_ROOT,
        env={"PATH": str(bin_dir)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    selected = os.path.realpath(paths["python3.10"])
    assert result.stdout.strip() == selected
    assert argv_paths["python3"].exists()
    assert argv_paths["python3.10"].exists()
    assert not argv_paths["python3.11"].exists()
    assert not argv_paths["python3.12"].exists()
    selected_argv = argv_paths["python3.10"].read_text(encoding="utf-8").splitlines()
    assert selected_argv[0] == "-c"
    assert "import orchestrator.verifier" in selected_argv[1]
    assert selected_argv[-1] == str(repo_root)
    assert (tmp_path / "python3.10.cwd").read_text(encoding="utf-8").strip() == str(
        repo_root
    )
    assert not failure_path.exists()
    assert not (attempt_dir / "verifier.rc").exists()


def test_mocc_trace_verifier_interpreter_gate_fails_closed_and_records_rejections(
    tmp_path: Path,
) -> None:
    pilot = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
    source = pilot.read_text(encoding="utf-8")
    start_marker = '  VERIFIER_PY=""'
    end_marker = "\n  verifier_rc=0"
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker)
    assert start < end
    verifier_gate = source[start:end]

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    failure_path = tmp_path / "failure"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    real_realpath = shutil.which("realpath")
    assert real_realpath is not None
    (bin_dir / "realpath").symlink_to(real_realpath)

    paths: dict[str, Path] = {}
    argv_paths: dict[str, Path] = {}
    candidate_names = ("python3", "python3.10", "python3.11", "python3.12")
    for name in candidate_names:
        stub = bin_dir / name
        argv_path = tmp_path / f"{name}.argv"
        cwd_path = tmp_path / f"{name}.cwd"
        _make_executable(
            stub,
            f"""
            #!/bin/sh
            printf '%s\\n' "$@" >{shlex.quote(str(argv_path))}
            printf '%s\\n' "$PWD" >{shlex.quote(str(cwd_path))}
            exit 1
            """,
        )
        paths[name] = stub
        argv_paths[name] = argv_path

    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo_root))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt_dir))}",
            f"FAILURE_PATH={shlex.quote(str(failure_path))}",
            "write_failure() {",
            '  printf \'rc=%s\\nstage=%s\\nmessage=%s\\n\' "$1" "$2" "$3" >"$FAILURE_PATH"',
            "}",
            "",
        ]
    )
    result = subprocess.run(
        ["/bin/bash", "-c", prefix + verifier_gate],
        cwd=REPO_ROOT,
        env={"PATH": str(bin_dir)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2, result.stderr
    failure = failure_path.read_text(encoding="utf-8")
    assert "stage=verifier\n" in failure
    assert "rc=2\n" in failure
    assert "no python3 >= 3.10 candidate can import orchestrator.verifier" in failure
    for name in candidate_names:
        resolved = os.path.realpath(paths[name])
        assert f"{name}={resolved}" in failure
        argv = argv_paths[name].read_text(encoding="utf-8").splitlines()
        assert argv[0] == "-c"
        assert argv[-1] == str(repo_root)
        assert (tmp_path / f"{name}.cwd").read_text(
            encoding="utf-8"
        ).strip() == str(repo_root)
    assert (attempt_dir / "verifier.rc").read_text(encoding="utf-8") == "2\n"


def _mocc_trace_finalization_fragment() -> str:
    source = PILOT.read_text(encoding="utf-8")
    start_marker = 'python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"'
    git_marker = '\ngit -C "$CCBENCH_BASE" worktree remove'
    end_marker = '\nBUILD_SOURCE=""'
    assert source.count(start_marker) == 1
    assert source.count(git_marker) == 1
    start = source.index(start_marker)
    git_start = source.index(git_marker, start)
    end = source.index(end_marker, git_start)
    assert start < git_start < end
    fragment = source[start:end]
    assert 'RECEIPT_SHA=$(sha256sum "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"' in fragment
    assert 'python3 - "$ATTEMPT_DIR/job-result.json"' in fragment
    assert git_marker.lstrip("\n") in fragment
    return fragment


def _valid_trace0_report(
    build_source: Path,
    cxx_path: Path,
    *,
    schema: str = "izanagi-trace0-preprocess-identity/v2",
    guarantee: str = "fixture-specific preprocess and include guarantee",
) -> dict[str, object]:
    return {
        "schema": schema,
        "guarantee": guarantee,
        "result": "pass",
        "old_oid": BASE_OID,
        "new_oid": NEW_OID,
        "repo": os.path.realpath(build_source),
        "compiler": {"path": os.path.realpath(cxx_path), "version": "fixture-cxx"},
        "expected_paths": ["cc/mocc/transaction.cc"],
    }


def _encoded_report(report: object, encoding: str = "compact") -> bytes:
    if encoding == "compact":
        text = json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    elif encoding == "indent":
        text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    else:
        raise AssertionError(f"unsupported report encoding: {encoding}")
    return (text + "\n").encode("utf-8")


def _run_mocc_trace_finalization(
    tmp_path: Path,
    *,
    trace_mode: int = 0,
    report_changes: dict[str, object] | None = None,
    report_bytes: bytes | None = None,
    report_encoding: str = "compact",
    report_mode: str = "file",
    checker_report_sha: str | None = None,
    realpath_aliases: bool = False,
    tamper_receipt_after_write: bool = False,
    current_script_sha: str = "fixture-script-sha",
) -> tuple[subprocess.CompletedProcess[str], Path, bytes]:
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir(parents=True)
    real_python = shutil.which("python3")
    assert real_python is not None
    interpreter = Path(os.path.realpath(real_python))

    if realpath_aliases:
        build_source_real = tmp_path / "build-source-real"
        build_source_real.mkdir()
        build_source = tmp_path / "build-source-link"
        build_source.symlink_to(build_source_real, target_is_directory=True)
        cxx_path = tmp_path / "cxx-link"
        cxx_path.symlink_to(interpreter)
    else:
        build_source = tmp_path / "build-source"
        build_source.mkdir()
        cxx_path = interpreter

    report = _valid_trace0_report(build_source, cxx_path)
    if report_changes:
        report.update(report_changes)
    if report_bytes is None:
        report_bytes = _encoded_report(report, report_encoding)

    report_path = attempt_dir / "trace0-preprocess-identity.json"
    if report_mode == "file":
        if trace_mode == 0 or report_changes is not None or report_bytes is not None:
            report_path.write_bytes(report_bytes)
    elif report_mode == "symlink":
        target = tmp_path / "valid-report-target.json"
        target.write_bytes(report_bytes)
        report_path.symlink_to(target)
    elif report_mode == "missing":
        pass
    elif report_mode == "directory":
        report_path.mkdir()
    else:
        raise AssertionError(f"unsupported report mode: {report_mode}")

    submit_receipt_path = attempt_dir / "submit-receipt.json"
    submit_receipt_path.write_text(
        json.dumps(
            {
                "mocc_trace": {},
                "policy": {"expected_cpu_model": "fixture cpu"},
            }
        ),
        encoding="utf-8",
    )
    (attempt_dir / "topology.json").write_text("{}\n", encoding="utf-8")
    (attempt_dir / "run-argv.json").write_text(
        json.dumps({"argv": ["fixture-binary"], "argv_source": "fixture"}),
        encoding="utf-8",
    )
    (attempt_dir / "compiler-used.version").write_text(
        "fixture compiler version\n", encoding="utf-8"
    )

    if checker_report_sha is None:
        checker_report_sha = (
            hashlib.sha256(report_bytes).hexdigest() if trace_mode == 0 else ""
        )
    checker_py = str(interpreter) if trace_mode == 0 else ""
    verifier_py = str(interpreter) if trace_mode == 1 else ""
    checker_rc = "0" if trace_mode == 0 else "not-run"
    verifier_rc = "not-run" if trace_mode == 0 else "0"
    failure_path = attempt_dir / "fragment-failure.txt"

    variables = {
        "ATTEMPT_DIR": str(attempt_dir),
        "ATTEMPT_RECEIPT": str(submit_receipt_path),
        "CURRENT_COMMIT": "fixture-outer-commit",
        "CURRENT_SCRIPT_SHA": current_script_sha,
        "PBS_JOBID": "fixture-job",
        "HOSTNAME_SHORT": "fixture-host",
        "HOSTNAME_FQDN": "fixture-host.example",
        "CPU_MODEL": "fixture cpu",
        "TRACE_MODE": str(trace_mode),
        "CXX_PATH": str(cxx_path),
        "BASE_OID": BASE_OID,
        "NEW_OID": NEW_OID,
        "BUILD_DIR": str(tmp_path / "build"),
        "BINARY": str(tmp_path / "fixture-binary"),
        "BINARY_SHA": "fixture-binary-sha",
        "RUN_DIR": str(tmp_path / "run"),
        "TRACE_DIR": str(tmp_path / "run/trace"),
        "RUN_ARGV_JSON": str(attempt_dir / "run-argv.json"),
        "COMMIT_COUNT": "7",
        "RUN_ELAPSED_NS": "1000",
        "CHECKER_RC": checker_rc,
        "VERIFIER_RC": verifier_rc,
        "RUN_RC": "0",
        "qstat_final_rc": "0",
        "qstat_accounting_rc": "0",
        "WORKLOAD_JSON": json.dumps({"records": 7}),
        "CMAKE_TARGET": "mocc",
        "BUILD_SOURCE": str(build_source),
        "CHECKER_PY": checker_py,
        "VERIFIER_PY": verifier_py,
        "CHECKER_REPORT_SHA": checker_report_sha,
        "CCBENCH_BASE": str(tmp_path / "ccbench-base"),
        "FAILURE_PATH": str(failure_path),
    }
    prefix_lines = ["set -Eeuo pipefail"]
    prefix_lines.extend(
        f"{name}={shlex.quote(value)}" for name, value in variables.items()
    )
    prefix_lines.extend(
        [
            "write_failure() {",
            "  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" >\"$FAILURE_PATH\"",
            "}",
            "git() { return 0; }",
            "",
        ]
    )
    fragment = _mocc_trace_finalization_fragment()
    if tamper_receipt_after_write:
        tamper = """
python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" <<'PY_TAMPER'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = json.load(handle)
payload["created_epoch"] += 1
with open(path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\\n")
PY_TAMPER
"""
        receipt_sha_marker = "\nRECEIPT_SHA="
        assert fragment.count(receipt_sha_marker) == 1
        fragment = fragment.replace(
            receipt_sha_marker,
            tamper + receipt_sha_marker,
            1,
        )
    result = subprocess.run(
        ["/bin/bash", "-c", "\n".join(prefix_lines) + fragment],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result, attempt_dir, report_bytes


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _assert_receipt_binding_rejected(
    result: subprocess.CompletedProcess[str], attempt_dir: Path
) -> None:
    assert result.returncode == 2, result.stderr
    assert not (attempt_dir / "mocc-trace-pilot-receipt.json").exists()
    assert not (attempt_dir / "mocc-trace-pilot-receipt.sha256").exists()
    assert not (attempt_dir / "job-result.json").exists()
    failure = (attempt_dir / "fragment-failure.txt").read_text(encoding="utf-8")
    assert failure == (
        "2|trace0_preprocess_identity_report_binding|"
        "preprocess identity report binding failed\n"
    )


def test_mocc_trace_report_binding_markers_remain_unique() -> None:
    source = PILOT.read_text(encoding="utf-8")
    markers = (
        "CPU_MODEL=$(awk",
        "\nmodule_rc=0",
        '  CHECKER_PY=""',
        "  CHECKER_RC=0",
        '\n  printf \'%s\\n\' "$CHECKER_RC"',
        "\nelse\n  build_mode 1",
        '  VERIFIER_PY=""',
        "\n  verifier_rc=0",
        'python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"',
        "\nRECEIPT_SHA=",
        'python3 - "$ATTEMPT_DIR/job-result.json"',
        '\ngit -C "$CCBENCH_BASE" worktree remove',
    )
    assert {marker: source.count(marker) for marker in markers} == {
        marker: 1 for marker in markers
    }


def test_mocc_trace_report_binding_uses_one_python_report_read() -> None:
    source = PILOT.read_text(encoding="utf-8")
    start = source.index('python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"')
    python_start = source.index("\nimport hashlib\n", start)
    python_end = source.index(
        "\nPY\n  write_failure 2 trace0_preprocess_identity_report_binding",
        python_start,
    )
    writer = source[python_start:python_end]
    outside_writer = source[:python_start] + source[python_end:]
    assert writer.count('open(checker_report_path, "rb")') == 1
    assert writer.count("report_bytes = handle.read()") == 1
    assert writer.count('json.loads(report_bytes.decode("utf-8"))') == 1
    assert writer.count('report.get("schema")') == 1
    assert writer.count('report.get("guarantee")') == 1
    assert 'report.get("schema")' not in outside_writer
    assert 'report.get("guarantee")' not in outside_writer
    assert "REPORT_SCHEMA" not in source
    assert "REPORT_GUARANTEE" not in source


def test_mocc_trace_binding_m01_sha_tracks_exact_report_bytes(tmp_path: Path) -> None:
    compact, compact_dir, compact_bytes = _run_mocc_trace_finalization(
        tmp_path / "compact",
        report_encoding="compact",
        current_script_sha="volatile-script-sha-a",
    )
    indented, indented_dir, indented_bytes = _run_mocc_trace_finalization(
        tmp_path / "indented",
        report_encoding="indent",
        current_script_sha="volatile-script-sha-b",
    )
    assert compact.returncode == 0, compact.stderr
    assert indented.returncode == 0, indented.stderr
    compact_binding = _load_json(
        compact_dir / "mocc-trace-pilot-receipt.json"
    )["trace0_preprocess_identity_report"]
    indented_binding = _load_json(
        indented_dir / "mocc-trace-pilot-receipt.json"
    )["trace0_preprocess_identity_report"]
    assert isinstance(compact_binding, dict)
    assert isinstance(indented_binding, dict)
    assert compact_binding["sha256"] == hashlib.sha256(compact_bytes).hexdigest()
    assert indented_binding["sha256"] == hashlib.sha256(indented_bytes).hexdigest()
    assert compact_binding["sha256"] != indented_binding["sha256"]


def test_mocc_trace_binding_m02_copies_schema_v1(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        report_changes={"schema": "izanagi-trace0-preprocess-identity/v1"},
    )
    assert result.returncode == 0, result.stderr
    binding = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")[
        "trace0_preprocess_identity_report"
    ]
    assert isinstance(binding, dict)
    assert binding["schema"] == "izanagi-trace0-preprocess-identity/v1"


def test_mocc_trace_binding_m03_copies_fixture_guarantee(tmp_path: Path) -> None:
    guarantee = "fixture guarantee with a distinct payload"
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_changes={"guarantee": guarantee}
    )
    assert result.returncode == 0, result.stderr
    binding = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")[
        "trace0_preprocess_identity_report"
    ]
    assert isinstance(binding, dict)
    assert binding["guarantee"] == guarantee


def test_mocc_trace_binding_m04_rejects_unrelated_schema_family(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_changes={"schema": "unrelated-check/v1"}
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m05_rejects_non_pass_result(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_changes={"result": "fail"}
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m06_rejects_old_oid_mismatch(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_changes={"old_oid": "0" * 40}
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m07_rejects_new_oid_mismatch(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_changes={"new_oid": "f" * 40}
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m08_rejects_repo_mismatch(tmp_path: Path) -> None:
    wrong_repo = tmp_path / "wrong-repo"
    wrong_repo.mkdir()
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_changes={"repo": str(wrong_repo)}
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m09_rejects_compiler_mismatch(tmp_path: Path) -> None:
    wrong_compiler = tmp_path / "wrong-compiler"
    wrong_compiler.write_text("fixture\n", encoding="utf-8")
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        report_changes={"compiler": {"path": str(wrong_compiler)}},
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m10_rejects_expected_paths_mismatch(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_changes={"expected_paths": ["cc/mocc/other.cc"]}
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m11_rejects_valid_report_symlink(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_mode="symlink"
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m12_rejects_post_checker_report_swap(tmp_path: Path) -> None:
    real_python = shutil.which("python3")
    assert real_python is not None
    report_before_swap = _valid_trace0_report(
        tmp_path / "build-source", Path(os.path.realpath(real_python))
    )
    report_before_swap["guarantee"] = "valid report before swap"
    early_sha = hashlib.sha256(_encoded_report(report_before_swap)).hexdigest()
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        report_changes={"guarantee": "valid report after swap"},
        checker_report_sha=early_sha,
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m13_rejects_receipt_replaced_before_shell_hash(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, tamper_receipt_after_write=True
    )
    assert result.returncode == 2, result.stderr
    assert (attempt_dir / "mocc-trace-pilot-receipt.json").exists()
    assert (attempt_dir / "mocc-trace-pilot-receipt.sha256").exists()
    assert not (attempt_dir / "job-result.json").exists()
    failure = (attempt_dir / "fragment-failure.txt").read_text(encoding="utf-8")
    assert failure == "2|job_result_report_binding|job result report binding failed\n"


def test_mocc_trace_binding_m14_rejects_trace1_report_presence(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        trace_mode=1,
        report_changes={"guarantee": "present during TRACE=1"},
    )
    _assert_receipt_binding_rejected(result, attempt_dir)


def test_mocc_trace_binding_m15_trace1_fields_are_null(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, trace_mode=1, report_mode="missing"
    )
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    expected = {"path": None, "sha256": None, "schema": None, "guarantee": None}
    assert receipt["trace0_preprocess_identity_report"] == expected


def test_mocc_trace_binding_m16_uses_v2_document_schemas(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(tmp_path)
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    job_result = _load_json(attempt_dir / "job-result.json")
    assert receipt["schema_version"] == "mocc-trace-pilot-receipt/v2"
    assert job_result["schema_version"] == "mocc-trace-pilot-job-result/v2"


def test_mocc_trace_binding_m17_records_verifier_interpreter(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, trace_mode=1, report_mode="missing"
    )
    assert result.returncode == 0, result.stderr
    environment = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")[
        "environment"
    ]
    assert isinstance(environment, dict)
    verifier_path = environment["verifier_interpreter_path"]
    assert isinstance(verifier_path, str)
    assert os.path.isabs(verifier_path)
    assert os.path.realpath(verifier_path) == verifier_path


def test_mocc_trace_binding_m18_records_checker_interpreter(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(tmp_path)
    assert result.returncode == 0, result.stderr
    environment = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")[
        "environment"
    ]
    assert isinstance(environment, dict)
    checker_path = environment[
        "trace0_preprocess_identity_checker_interpreter_path"
    ]
    assert isinstance(checker_path, str)
    assert os.path.isabs(checker_path)
    assert os.path.realpath(checker_path) == checker_path


def test_mocc_trace_binding_m19_globals_precede_receipt_writer() -> None:
    source = PILOT.read_text(encoding="utf-8")
    receipt_start = source.index(
        'python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"'
    )
    lines = source.splitlines()
    for declaration in ('CHECKER_PY=""', 'VERIFIER_PY=""', 'CHECKER_REPORT_SHA=""'):
        assert lines.count(declaration) == 1
        assert source.index(declaration) < receipt_start


def test_mocc_trace_binding_m20_job_result_copies_only_four_scalars(
    tmp_path: Path,
) -> None:
    sentinel = "raw-report-payload-must-not-be-copied"
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        report_changes={
            "files": [{"sentinel": sentinel}],
            "diff": [{"sentinel": sentinel}],
            "raw_json": sentinel,
        },
    )
    assert result.returncode == 0, result.stderr
    receipt_path = attempt_dir / "mocc-trace-pilot-receipt.json"
    job_result_path = attempt_dir / "job-result.json"
    receipt = _load_json(receipt_path)
    job_result = _load_json(job_result_path)
    receipt_binding = receipt["trace0_preprocess_identity_report"]
    job_binding = job_result["trace0_preprocess_identity_report"]
    assert isinstance(receipt_binding, dict)
    assert isinstance(job_binding, dict)
    assert set(receipt_binding) == {"path", "sha256", "schema", "guarantee"}
    assert set(job_binding) == {"path", "sha256", "schema", "guarantee"}
    assert all(isinstance(value, str) for value in receipt_binding.values())
    assert job_binding == receipt_binding
    assert sentinel not in receipt_path.read_text(encoding="utf-8")
    assert sentinel not in job_result_path.read_text(encoding="utf-8")


def test_mocc_trace_binding_p01_accepts_aligned_schema_v1_report(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        report_changes={"schema": "izanagi-trace0-preprocess-identity/v1"},
    )
    assert result.returncode == 0, result.stderr
    assert (attempt_dir / "mocc-trace-pilot-receipt.json").is_file()
    assert (attempt_dir / "job-result.json").is_file()


def test_mocc_trace_binding_p02_accepts_aligned_schema_v2_realpath_report(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        report_changes={
            "guarantee": (
                "選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、"
                "および include 活性の同一性"
            ),
            "context_matrix": {
                "expected_context_count_per_file": 16,
                "genome_count": 8,
                "overlay_count": 2,
            }
        },
        realpath_aliases=True,
    )
    assert result.returncode == 0, result.stderr
    assert (attempt_dir / "mocc-trace-pilot-receipt.json").is_file()
    assert (attempt_dir / "job-result.json").is_file()


def test_mocc_trace_binding_p03_accepts_normal_trace1_without_report(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, trace_mode=1, report_mode="missing"
    )
    assert result.returncode == 0, result.stderr
    assert (attempt_dir / "mocc-trace-pilot-receipt.json").is_file()
    assert (attempt_dir / "job-result.json").is_file()


@pytest.mark.parametrize(
    ("case", "report_mode", "report_bytes", "report_changes"),
    (
        pytest.param("missing", "missing", None, None, id="missing"),
        pytest.param("directory", "directory", None, None, id="directory"),
        pytest.param("invalid-json", "file", b"not-json\n", None, id="invalid-json"),
        pytest.param("array", "file", b"[]\n", None, id="array-top-level"),
        pytest.param(
            "empty-guarantee",
            "file",
            None,
            {"guarantee": "   "},
            id="empty-guarantee",
        ),
    ),
)
def test_mocc_trace_binding_rejects_other_invalid_report_forms(
    tmp_path: Path,
    case: str,
    report_mode: str,
    report_bytes: bytes | None,
    report_changes: dict[str, object] | None,
) -> None:
    del case
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        report_mode=report_mode,
        report_bytes=report_bytes,
        report_changes=report_changes,
        checker_report_sha="0" * 64 if report_mode != "file" else None,
    )
    _assert_receipt_binding_rejected(result, attempt_dir)
