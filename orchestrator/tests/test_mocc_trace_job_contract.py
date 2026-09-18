"""Contract checks for the login-side Mocc trace pilot submitter."""

from __future__ import annotations

import ast
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import shlex
import stat
import subprocess
import shutil
import sys
import textwrap

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SUBMITTER = REPO_ROOT / "tools/pegasus/submit_mocc_trace.sh"
POLICY = REPO_ROOT / "tools/pegasus/mocc_trace_v1_policy.json"
PILOT = REPO_ROOT / "tools/pegasus/mocc_trace_pilot.sh"
CHECKER = REPO_ROOT / "tools/check_trace0_preprocess_identity.py"
VERIFIER = REPO_ROOT / "orchestrator/verifier/__main__.py"
FETCH_THIRD_PARTY = REPO_ROOT / "tools/pegasus/fetch_third_party.py"
NEW_OID = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
BASE_OID = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
EXPECTED_COMPILER_BODY_SHA256 = (
    "b713e6ab62b67126b772f6b0a8d9751070f0d0315c7017291cb5dde67747b9c0"
)
FIXTURE_COMPILER_BODY_SHA256 = (
    "40d20db9b7dd268057a5354e49e3f36d483be42b493ee7fa23a4d50c23d278ee"
)


def _make_executable(path: Path, contents: str) -> None:
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _run_in_process_group(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise
    return subprocess.CompletedProcess(
        process.args, process.returncode, stdout, stderr
    )


def test_mocc_trace_pilot_shell_syntax() -> None:
    result = subprocess.run(
        ["bash", "-n", str(PILOT)], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def _fake_git(
    bin_dir: Path,
    source_commit: str,
    *,
    status_path: Path | None = None,
    gitlink_oid: str = BASE_OID,
    new_oid_available: bool = True,
    status_restore: tuple[Path, Path] | None = None,
) -> None:
    status_commands = []
    if status_restore is not None:
        source, target = status_restore
        status_commands.append(
            f"cp {shlex.quote(str(source))} {shlex.quote(str(target))}"
        )
    status_commands.append(
        f"cat {shlex.quote(str(status_path))}" if status_path is not None else ":"
    )
    status_command = "\n".join(status_commands)
    new_oid_resolution = (
        f"printf '%s\\n' '{NEW_OID}'; exit 0"
        if new_oid_available
        else "exit 128"
    )
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
              {new_oid_resolution}
            fi
            ;;
          status)
            {status_command}
            exit 0
            ;;
          ls-tree)
            if [[ "$2" == "{source_commit}" && "$3" == "--" &&
                  "$4" == "external/ccbench" ]]; then
              printf '160000 commit %s\texternal/ccbench\n' '{gitlink_oid}'
              exit 0
            fi
            ;;
        esac
        echo "unexpected fake git argv: $*" >&2
        exit 97
        """,
    )


def _policy_bytes_with_non_finite_top_level() -> bytes:
    document = json.loads(POLICY.read_text(encoding="utf-8"))
    document["unreferenced_non_finite"] = float("nan")
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=True,
        )
        + "\n"
    ).encode("utf-8")


def _run_mocc_trace_submit_with_policy(
    tmp_path: Path,
    policy_bytes: bytes,
    *,
    replace_policy_with_writerless_fifo: bool = False,
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    repo_root = tmp_path / "repo"
    policy_path = repo_root / "tools/pegasus/mocc_trace_v1_policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_bytes(policy_bytes)
    (repo_root / "external/ccbench").mkdir(parents=True)
    attempts_root = tmp_path / "attempts"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(bin_dir, "7" * 40)

    if replace_policy_with_writerless_fifo:
        real_python = shutil.which("python3")
        assert real_python is not None
        swap_marker = tmp_path / "policy-swapped"
        saved_policy = tmp_path / "saved-policy.json"
        _make_executable(
            bin_dir / "python3",
            f"""
            #!/bin/bash
            if [[ ! -e {shlex.quote(str(swap_marker))} && "$#" -ge 2 &&
                  "$1" == "-" && "$2" == {shlex.quote(str(policy_path))} ]]; then
              : >{shlex.quote(str(swap_marker))}
              mv {shlex.quote(str(policy_path))} {shlex.quote(str(saved_policy))}
              mkfifo {shlex.quote(str(policy_path))}
            fi
            exec {shlex.quote(real_python)} "$@"
            """,
        )

    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    result = _run_in_process_group(
        [
            "bash",
            str(SUBMITTER),
            "--dry-run",
            "--repo-root",
            str(repo_root),
            "--attempts-root",
            str(attempts_root),
            "--job-script",
            str(PILOT),
        ],
        cwd=REPO_ROOT,
        env=environment,
        timeout=10,
    )
    return result, attempts_root, policy_path


def _pilot_policy_parser_source() -> str:
    source = PILOT.read_text(encoding="utf-8")
    prefix = 'readarray -t policy_values < <(python3 - "$POLICY" <<\'PY\'\n'
    start = source.index(prefix) + len(prefix)
    end = source.index("\nPY\n)\nif [[ ${#policy_values[@]} -ne ", start)
    return source[start:end]


def test_mocc_trace_policy_compiler_mapping_is_exact() -> None:
    document = json.loads(POLICY.read_text(encoding="utf-8"))
    expected = document["expected_compiler_version_body_sha256"]
    assert set(expected) == {"gcc", "g++"}
    assert expected == {
        "gcc": EXPECTED_COMPILER_BODY_SHA256,
        "g++": EXPECTED_COMPILER_BODY_SHA256,
    }


def test_mocc_trace_policy_parser_emits_16_values_and_rejects_duplicates(
        tmp_path: Path,
) -> None:
    parser = tmp_path / "policy_parser.py"
    parser.write_text(_pilot_policy_parser_source(), encoding="utf-8")
    assert "if [[ ${#policy_values[@]} -ne 16 ]]; then" in (
        PILOT.read_text(encoding="utf-8")
    )
    accepted = subprocess.run(
        [sys.executable, str(parser), str(POLICY)],
        capture_output=True, text=True, check=False,
    )
    assert accepted.returncode == 0, accepted.stderr
    values = accepted.stdout.splitlines()
    assert len(values) == 16
    assert json.loads(values[10]) == {
        "gcc": EXPECTED_COMPILER_BODY_SHA256,
        "g++": EXPECTED_COMPILER_BODY_SHA256,
    }
    assert values[15] == hashlib.sha256(POLICY.read_bytes()).hexdigest()

    raw = POLICY.read_text(encoding="utf-8")
    duplicate = tmp_path / "duplicate-policy.json"
    duplicate.write_text(
        '{"expected_cpu_model":"duplicate",' + raw[1:], encoding="utf-8",
    )
    rejected = subprocess.run(
        [sys.executable, str(parser), str(duplicate)],
        capture_output=True, text=True, check=False,
    )
    assert rejected.returncode != 0
    assert "duplicate JSON key: expected_cpu_model" in rejected.stderr


def test_mocc_trace_submit_rejects_writerless_fifo_policy_without_blocking(
    tmp_path: Path,
) -> None:
    result, attempts_root, policy_path = _run_mocc_trace_submit_with_policy(
        tmp_path,
        POLICY.read_bytes(),
        replace_policy_with_writerless_fifo=True,
    )
    assert result.returncode == 2, result.stderr
    assert stat.S_ISFIFO(policy_path.stat().st_mode)
    assert not (attempts_root / "submissions").exists()


def test_mocc_trace_submit_rejects_non_finite_policy(tmp_path: Path) -> None:
    result, attempts_root, _ = _run_mocc_trace_submit_with_policy(
        tmp_path, _policy_bytes_with_non_finite_top_level()
    )
    assert result.returncode == 2, result.stderr
    assert "Mocc trace policy parse failed" in result.stderr
    assert not (attempts_root / "submissions").exists()


def test_mocc_trace_submit_preserves_policy_pilot_walltime_type(
    tmp_path: Path,
) -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    policy["pilot_walltime"] = 37
    policy_bytes = (
        json.dumps(policy, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    result, attempts_root, _ = _run_mocc_trace_submit_with_policy(
        tmp_path, policy_bytes
    )
    assert result.returncode == 0, result.stderr
    submission_dirs = list((attempts_root / "submissions").iterdir())
    assert len(submission_dirs) == 1
    pre_submit = _load_json(submission_dirs[0] / "pre-submit.json")
    submit_receipt = _load_json(submission_dirs[0] / "submit-receipt.json")
    assert type(pre_submit["policy"]["pilot_walltime"]) is int
    assert pre_submit["policy"]["pilot_walltime"] == 37
    assert submit_receipt["policy"]["pilot_walltime"] == 37


def test_mocc_trace_policy_parser_rejects_non_finite_policy(tmp_path: Path) -> None:
    parser = tmp_path / "policy_parser.py"
    parser.write_text(_pilot_policy_parser_source(), encoding="utf-8")
    policy_path = tmp_path / "non-finite-policy.json"
    policy_path.write_bytes(_policy_bytes_with_non_finite_top_level())
    result = subprocess.run(
        [sys.executable, str(parser), str(policy_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode != 0
    assert "non-finite JSON constant: NaN" in result.stderr


def _compiler_gate_fragment() -> str:
    source = PILOT.read_text(encoding="utf-8")
    start = source.index("# BEGIN T1718 COMPILER VERSION BODY GATE")
    end_marker = "# END T1718 COMPILER VERSION BODY GATE"
    end = source.index(end_marker, start) + len(end_marker)
    return source[start:end]


def _run_compiler_gate(
        tmp_path: Path, *, gcc_version: str, gxx_version: str,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    tmp_path.mkdir(parents=True)
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "compiler-gcc.version").write_text(gcc_version, encoding="utf-8")
    (attempt / "compiler-gxx.version").write_text(gxx_version, encoding="utf-8")
    failure = tmp_path / "failure.txt"
    expected = json.dumps(
        {"gcc": FIXTURE_COMPILER_BODY_SHA256, "g++": FIXTURE_COMPILER_BODY_SHA256},
        sort_keys=True, separators=(",", ":"),
    )
    wrapper = tmp_path / "compiler-gate.sh"
    wrapper.write_text(
        "#!/bin/bash\nset -Eeuo pipefail\n"
        "write_failure() { printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" > \"$FAILURE\"; }\n"
        f"REPO_ROOT={shlex.quote(str(REPO_ROOT))}\n"
        f"ATTEMPT_DIR={shlex.quote(str(attempt))}\n"
        f"FAILURE={shlex.quote(str(failure))}\n"
        "EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON="
        f"{shlex.quote(expected)}\n"
        + _compiler_gate_fragment()
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["bash", str(wrapper)], capture_output=True, text=True, check=False,
    )
    return result, failure


@pytest.mark.parametrize("role", ("gcc", "g++"))
def test_mocc_trace_pilot_rejects_expected_compiler_version_body_mismatch(
        tmp_path: Path, role: str,
) -> None:
    matching = {
        "gcc": "gcc fixture compiler 11.4\nCopyright fixture\n",
        "g++": "g++ fixture compiler 11.4\nCopyright fixture\n",
    }
    accepted, accepted_failure = _run_compiler_gate(tmp_path / "accepted", **{
        "gcc_version": matching["gcc"], "gxx_version": matching["g++"],
    })
    assert accepted.returncode == 0, accepted.stderr
    assert not accepted_failure.exists()

    rejected_versions = dict(matching)
    rejected_versions[role] += "different body\n"
    rejected, rejected_failure = _run_compiler_gate(
        tmp_path / role.replace("+", "x"), **{
        "gcc_version": rejected_versions["gcc"],
        "gxx_version": rejected_versions["g++"],
    })
    assert rejected.returncode == 2
    failure = rejected_failure.read_text(encoding="utf-8")
    assert failure.startswith(f"2|compiler|{role} compiler version body mismatch")


def test_mocc_trace_gflags_and_glog_clear_compiler_launchers(
        tmp_path: Path,
) -> None:
    source = PILOT.read_text(encoding="utf-8")
    unset_line = (
        "unset CMAKE_C_COMPILER_LAUNCHER CMAKE_CXX_COMPILER_LAUNCHER "
        "RULE_LAUNCH_COMPILE"
    )
    assert unset_line in source
    assert source.count("  -DCMAKE_C_COMPILER_LAUNCHER=\n") == 3
    assert source.count("  -DCMAKE_CXX_COMPILER_LAUNCHER=\n") == 3
    assert source.count("  -DRULE_LAUNCH_COMPILE=\n") == 3
    probe = tmp_path / "launcher-env-probe.sh"
    probe.write_text(
        "#!/bin/bash\nset -Eeuo pipefail\n"
        "export CMAKE_C_COMPILER_LAUNCHER=attacker-c\n"
        "export CMAKE_CXX_COMPILER_LAUNCHER=attacker-cxx\n"
        "export RULE_LAUNCH_COMPILE=attacker-rule\n"
        f"{unset_line}\n"
        "[[ -z ${CMAKE_C_COMPILER_LAUNCHER+x} ]]\n"
        "[[ -z ${CMAKE_CXX_COMPILER_LAUNCHER+x} ]]\n"
        "[[ -z ${RULE_LAUNCH_COMPILE+x} ]]\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["bash", str(probe)], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_mocc_gflags_and_glog_toolchain_guards_block_environment_adoption(
        tmp_path: Path,
) -> None:
    pilot_source = PILOT.read_text(encoding="utf-8")

    def configured_toolchain_args(array_name: str) -> list[str]:
        start = pilot_source.index(f"{array_name}=(")
        end = pilot_source.index("\n)", start)
        return [
            line.strip()
            for line in pilot_source[start:end].splitlines()
            if line.strip().startswith("-DCMAKE_TOOLCHAIN_FILE=")
        ]

    project = tmp_path / "project"
    project.mkdir()
    marker = tmp_path / "attacker-toolchain-loaded"
    toolchain = tmp_path / "attacker-toolchain.cmake"
    toolchain.write_text(
        f'file(WRITE "{marker.as_posix()}" "loaded\\n")\n'
        'set(CMAKE_C_COMPILER_LAUNCHER "attacker-c" CACHE STRING "" FORCE)\n'
        'set(CMAKE_CXX_COMPILER_LAUNCHER "attacker-cxx" CACHE STRING "" FORCE)\n',
        encoding="utf-8",
    )
    (project / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.16)\nproject(toolchain_probe NONE)\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["CMAKE_TOOLCHAIN_FILE"] = str(toolchain)

    unguarded = subprocess.run(
        ["cmake", "-S", str(project), "-B", str(tmp_path / "unguarded")],
        env=environment, capture_output=True, text=True, check=False,
    )
    assert unguarded.returncode == 0, unguarded.stderr
    assert marker.is_file()
    marker.unlink()

    for array_name in ("gflags_configure_argv", "glog_configure_argv"):
        guarded = subprocess.run(
            [
                "cmake", "-S", str(project),
                "-B", str(tmp_path / f"guarded-{array_name}"),
                *configured_toolchain_args(array_name),
            ],
            env=environment, capture_output=True, text=True, check=False,
        )
        assert guarded.returncode == 0, guarded.stderr
        assert not marker.exists(), f"{array_name} adopted the environment toolchain"


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
    fixture_policy_path = repo_root / "tools/pegasus/mocc_trace_v1_policy.json"
    policy_bytes = fixture_policy_path.read_bytes()
    policy = json.loads(policy_bytes)
    policy_sha = hashlib.sha256(policy_bytes).hexdigest()

    for document in (pre_submit, receipt):
        assert document["schema_version"] in {
            "pegasus-pre-submit/v1",
            "pegasus-submit-receipt/v2",
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
        assert document["policy"]["raw_sha256"] == policy_sha
        assert document["policy"][
            "expected_compiler_version_body_sha256"
        ] == policy["expected_compiler_version_body_sha256"]

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
    qsub_argv = pre_submit["request"]["qsub_argv"]
    export_spec = qsub_argv[qsub_argv.index("-v") + 1]
    assert f"IZANAGI_MOCC_TRACE_ATTEMPTS_ROOT={attempts_root.resolve()}" in (
        export_spec.split(",")
    )
    assert f"IZANAGI_MOCC_POLICY_RAW_SHA256={policy_sha}" in export_spec.split(",")
    assert qsub_argv[qsub_argv.index("-o") + 1] == str(
        submission / "pbs-job.stdout"
    )
    assert qsub_argv[qsub_argv.index("-e") + 1] == str(
        submission / "pbs-job.stderr"
    )
    assert receipt["qsub"]["request_id"].startswith("dry-run-")
    assert receipt["qsub"]["argv"] == pre_submit["request"]["qsub_argv"]
    assert (submission / "qsub.rc").read_text(encoding="utf-8").strip() == "0"


def test_mocc_trace_submit_rejects_policy_change_between_parse_and_clean_gate(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    policy_path = repo_root / "tools/pegasus/mocc_trace_v1_policy.json"
    policy_path.parent.mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    pristine_policy = tmp_path / "pristine-policy.json"
    pristine_policy.write_bytes(POLICY.read_bytes())
    initial_policy = tmp_path / "initial-policy.json"
    initial_policy.write_bytes(POLICY.read_bytes() + b"\n")
    policy_path.write_bytes(initial_policy.read_bytes())
    attempts_root = tmp_path / "attempts"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(
        bin_dir,
        "3" * 40,
        status_restore=(pristine_policy, policy_path),
    )
    real_sha256sum = shutil.which("sha256sum")
    assert real_sha256sum is not None
    _make_executable(
        bin_dir / "sha256sum",
        f"""
        #!/bin/bash
        cp {shlex.quote(str(initial_policy))} {shlex.quote(str(policy_path))}
        exec {shlex.quote(real_sha256sum)} "$@"
        """,
    )
    qsub_marker = tmp_path / "qsub-called"
    _make_executable(
        bin_dir / "qsub",
        f"#!/bin/sh\ntouch {shlex.quote(str(qsub_marker))}\nexit 99\n",
    )
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))

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
            str(PILOT),
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    with pytest.raises(subprocess.CalledProcessError):
        result.check_returncode()
    assert result.returncode == 2
    assert "changed between initial parse and clean-tree gate" in result.stderr
    assert not (attempts_root / "submissions").exists()
    assert not qsub_marker.exists()


def test_mocc_trace_pilot_requires_policy_raw_sha256_env(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "PBS_JOBID": "fixture-job",
            "PBS_O_WORKDIR": str(tmp_path),
            "IZANAGI_SUBMISSION_NONCE": "fixture-nonce",
            "IZANAGI_MOCC_TRACE_MODE": "0",
        }
    )
    environment.pop("IZANAGI_MOCC_POLICY_RAW_SHA256", None)
    result = subprocess.run(
        ["bash", str(PILOT)],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "IZANAGI_MOCC_POLICY_RAW_SHA256 must be 64 lowercase hex" in result.stderr


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
        assert "t1943_g2_discriminator" not in document["mocc_trace"]
        assert document["mocc_trace"]["workload"] == policy["mocc_trace"]["workload"]
        assert document["mocc_trace"]["workload"]["ycsb_max_ope"] == 10

    assert pre_submit["source_commit"] == source_commit
    assert any(
        "IZANAGI_MOCC_TRACE_MODE=1" in argument
        for argument in pre_submit["request"]["qsub_argv"]
    )
    qsub_argv = pre_submit["request"]["qsub_argv"]
    export_spec = qsub_argv[qsub_argv.index("-v") + 1]
    assert f"IZANAGI_MOCC_TRACE_ATTEMPTS_ROOT={attempts_root.resolve()}" in (
        export_spec.split(",")
    )
    assert not any(
        item.startswith("IZANAGI_MOCC_G2_DISCRIMINATOR=")
        for item in export_spec.split(",")
    )
    assert qsub_argv[qsub_argv.index("-o") + 1] == str(
        submission / "pbs-job.stdout"
    )
    assert qsub_argv[qsub_argv.index("-e") + 1] == str(
        submission / "pbs-job.stderr"
    )
    assert receipt["qsub"]["request_id"].startswith("dry-run-")
    assert receipt["qsub"]["argv"] == pre_submit["request"]["qsub_argv"]
    assert (submission / "qsub.rc").read_text(encoding="utf-8").strip() == "0"


def test_t1943_submit_dry_run_has_dedicated_fields(
    tmp_path: Path,
) -> None:
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
        #!/bin/sh
        touch {shlex.quote(str(qsub_marker))}
        exit 99
        """,
    )
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    environment["IZANAGI_PEGASUS_THIRDPARTY_CACHE"] = str(tmp_path / "cache")
    command = [
        "bash",
        str(SUBMITTER),
        "--dry-run",
        "--repo-root",
        str(repo_root),
        "--attempts-root",
        str(attempts_root),
        "--job-script",
        str(PILOT),
        "--t1943-g2-discriminator",
    ]

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not qsub_marker.exists()
    submission = next((attempts_root / "submissions").iterdir())
    for name in ("pre-submit.json", "submit-receipt.json"):
        document = _load_json(submission / name)
        assert document["mocc_trace"]["t1943_g2_discriminator"] is True
    qsub_argv = _load_json(submission / "pre-submit.json")["request"]["qsub_argv"]
    export_spec = qsub_argv[qsub_argv.index("-v") + 1]
    assert "IZANAGI_MOCC_G2_DISCRIMINATOR=1" in export_spec.split(",")


def test_t1943_submit_real_qsub_publishes_completed_receipt(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    attempts_root = tmp_path / "attempts"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(bin_dir, "2" * 40)
    for name in ("qstat", "pegasusinfo", "rbudgetcheck", "check_quota"):
        _make_executable(bin_dir / name, "#!/bin/sh\nexit 0\n")
    qsub_calls = tmp_path / "qsub-calls"
    _make_executable(
        bin_dir / "qsub",
        f"""
        #!/bin/sh
        printf '%s\n' called >>{shlex.quote(str(qsub_calls))}
        printf '%s\n' 'Request 12345.pegasus submitted.'
        """,
    )
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    environment["IZANAGI_PEGASUS_THIRDPARTY_CACHE"] = str(tmp_path / "cache")

    result = subprocess.run(
        [
            "bash",
            str(SUBMITTER),
            "--repo-root",
            str(repo_root),
            "--attempts-root",
            str(attempts_root),
            "--job-script",
            str(PILOT),
            "--t1943-g2-discriminator",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert qsub_calls.read_text(encoding="utf-8").splitlines() == ["called"]
    submission = next((attempts_root / "submissions").iterdir())
    receipt = _load_json(submission / "submit-receipt.json")
    assert receipt["dry_run"] is False
    assert receipt["qsub"]["request_id"] == "12345.pegasus"
    assert receipt["mocc_trace"]["t1943_g2_discriminator"] is True


def test_t1943_build_run_and_rc1_discriminator_order_is_fail_closed() -> None:
    source = PILOT.read_text(encoding="utf-8")
    dedicated_branch = source.index(
        'if [[ "$TRACE_MODE" -eq 0 || "$T1943_G2" -eq 1 ]]; then'
    )
    trace0_build = source.index("  build_mode 0", dedicated_branch)
    preprocess_gate = source.index(
        '"$REPO_ROOT/tools/check_trace0_preprocess_identity.py"', trace0_build
    )
    absence_gate = source.index(
        '"$ATTEMPT_DIR/trace0-watermark-absence.json"', preprocess_gate
    )
    absence_end = source.index("\nPY_T1943_TRACE0", absence_gate)
    absence_block = source[absence_gate:absence_end]
    for token in (
        "IZANAGI_MOCC_G2_WITNESS",
        "IZANAGI_MOCC_G2_WITNESS_DIR",
        "IZANAGI_MOCC_G2_WATERMARK_V1",
        "izanagi_mocc_g2",
        "witness_",
    ):
        assert token in absence_block
    assert "os.O_RDONLY | os.O_NOFOLLOW" in absence_block
    assert "pass_fds=(binary_fd,)" in absence_block
    assert '"binary_tokens_absent": not present_tokens' in absence_block
    trace1_build = source.index("    build_mode 1", absence_gate)
    workload_window = source.index("check_window before-workload", trace1_build)
    workload_start = source.index("RUN_START_NS=", workload_window)
    assert dedicated_branch < trace0_build < preprocess_gate < absence_gate
    assert absence_gate < trace1_build < workload_window < workload_start

    verifier_rc = source.index('VERIFIER_RC=$verifier_rc', workload_start)
    infra_stop = source.index(
        'if [[ "$VERIFIER_RC" -ne 0 && "$VERIFIER_RC" -ne 1 ]]; then',
        verifier_rc,
    )
    completed_json = source.index("\nPY_T1943_VERIFIER_COMPLETE", infra_stop)
    discriminator = source.index("DISCRIMINATOR_TOOL_PATH=", completed_json)
    assert verifier_rc < infra_stop < completed_json < discriminator

    submit_source = SUBMITTER.read_text(encoding="utf-8")
    qsub = submit_source.index('  "${qsub_cmd[@]}"')
    receipt_bytes = submit_source.index("receipt_bytes = (", qsub)
    fsync = submit_source.index("os.fsync(handle.fileno())", receipt_bytes)
    atomic_publish = submit_source.index(
        "os.link(temporary, target, follow_symlinks=False)", fsync
    )
    assert qsub < receipt_bytes < fsync < atomic_publish
    assert 'with open(target, "x"' not in submit_source

    pin_start = source.index("SUBMIT_RECEIPT_SHA=$(python3 -")
    no_follow = source.index("os.O_RDONLY | os.O_NOFOLLOW", pin_start)
    regular = source.index("stat.S_ISREG(source_info.st_mode)", no_follow)
    digest = source.index("hashlib.sha256(receipt_bytes).hexdigest()", regular)
    copy = source.index("target_fd = os.open(", digest)
    parse = source.index("receipt = json.loads(receipt_bytes.decode", digest)
    assert pin_start < no_follow < regular < digest < copy < parse
    assert 'cp "$SUBMIT_SOURCE"' not in source
    assert "submit_receipt_sha != pinned_submit_receipt_sha" in source

    assert 'ls-tree "$SOURCE_COMMIT"' not in submit_source
    assert 'ls-tree "$CURRENT_COMMIT"' not in source
    assert "OUTER_GITLINK_ADVANCED" not in source

    submit_resolution = submit_source.index(
        'rev-parse "$NEW_OID^{commit}"'
    )
    submit_exact = submit_source.index(
        'if [[ "$CCBENCH_RESOLVED" != "$NEW_OID" ]]', submit_resolution
    )
    submit_qsub = submit_source.index('  "${qsub_cmd[@]}"', submit_exact)
    job_resolution = source.index(
        'RESOLVED_NEW=$(git -C "$CCBENCH_BASE" rev-parse "$NEW_OID^{commit}")'
    )
    job_exact = source.index(
        'if [[ "$RESOLVED_NEW" != "$NEW_OID" ]]', job_resolution
    )
    materialize = source.index(
        'git -C "$CCBENCH_BASE" worktree add --detach "$BUILD_SOURCE" "$NEW_OID"',
        job_exact,
    )
    assert submit_resolution < submit_exact < submit_qsub
    assert job_resolution < job_exact < materialize
    assert '"outer_gitlink_advanced": False' in source


def test_t1943_submit_rejects_nonfixed_workload_before_submission(
    tmp_path: Path,
) -> None:
    for field, replacement in (("threads", 47), ("ycsb_rmw", 1)):
        case_root = tmp_path / field
        repo_root = case_root / "repo"
        (repo_root / "tools/pegasus").mkdir(parents=True)
        (repo_root / "external/ccbench").mkdir(parents=True)
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        policy["mocc_trace"]["workload"][field] = replacement
        (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_text(
            json.dumps(policy, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        bin_dir = case_root / "bin"
        bin_dir.mkdir()
        _fake_git(bin_dir, "1" * 40)
        environment = os.environ.copy()
        environment["PATH"] = os.pathsep.join(
            (str(bin_dir), environment["PATH"])
        )
        result = subprocess.run(
            [
                "bash",
                str(SUBMITTER),
                "--dry-run",
                "--repo-root",
                str(repo_root),
                "--attempts-root",
                str(case_root / "attempts"),
                "--job-script",
                str(PILOT),
                "--t1943-g2-discriminator",
            ],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "T-1943 workload tuple differs" in result.stderr
        assert not (case_root / "attempts/submissions").exists()


def test_t1943_submit_accepts_base_gitlink_with_available_new_object(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(bin_dir, "1" * 40, gitlink_oid=BASE_OID)
    modeled_gitlink = subprocess.run(
        [
            str(bin_dir / "git"),
            "-C",
            str(repo_root),
            "ls-tree",
            "1" * 40,
            "--",
            "external/ccbench",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert modeled_gitlink.returncode == 0, modeled_gitlink.stderr
    assert modeled_gitlink.stdout == (
        f"160000 commit {BASE_OID}\texternal/ccbench\n"
    )
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    attempts_root = tmp_path / "attempts"

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
            str(PILOT),
            "--t1943-g2-discriminator",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    submission = next((attempts_root / "submissions").iterdir())
    receipt = _load_json(submission / "submit-receipt.json")
    assert receipt["source_commit"] == "1" * 40
    assert receipt["mocc_trace"]["base_oid"] == BASE_OID
    assert receipt["mocc_trace"]["new_oid"] == NEW_OID


def test_t1943_submit_rejects_absent_new_oid_before_submission(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(
        bin_dir,
        "1" * 40,
        gitlink_oid=BASE_OID,
        new_oid_available=False,
    )
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    attempts_root = tmp_path / "attempts"

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
            str(PILOT),
            "--t1943-g2-discriminator",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "required Mocc trace commit is absent" in result.stderr
    assert not (attempts_root / "submissions").exists()


@pytest.mark.parametrize(
    ("case", "status_record", "kind", "expected_rc"),
    (
        (
            "owned-attempt-file",
            "?? output/env/pegasus/mocc-trace/attempts/old/receipt.json",
            "file",
            0,
        ),
        (
            "owned-job-staging-file",
            "?? output/env/pegasus/mocc-trace/job-staging/old/result.json",
            "file",
            0,
        ),
        (
            "owned-symlink",
            "?? output/env/pegasus/mocc-trace/attempts/old/receipt.json",
            "symlink",
            2,
        ),
        ("unowned-file", "?? dirty.txt", "file", 2),
        ("tracked-change", " M tools/pegasus/mocc_trace_pilot.sh", "none", 2),
    ),
)
def test_mocc_trace_submit_clean_gate_ignores_only_owned_regular_files(
    tmp_path: Path,
    case: str,
    status_record: str,
    kind: str,
    expected_rc: int,
) -> None:
    del case
    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    relative = status_record[3:] if status_record.startswith("?? ") else ""
    if relative:
        candidate = repo_root / relative
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if kind == "file":
            candidate.write_text("fixture\n", encoding="utf-8")
        elif kind == "symlink":
            target = tmp_path / "symlink-target"
            target.write_text("fixture\n", encoding="utf-8")
            candidate.symlink_to(target)
    status_path = tmp_path / "git-status.bin"
    status_path.write_bytes(status_record.encode("utf-8") + b"\0")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(
        bin_dir,
        "0123456789abcdef0123456789abcdef01234567",
        status_path=status_path,
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
            str(tmp_path / "attempts"),
            "--job-script",
            str(PILOT),
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected_rc, result.stderr


def test_mocc_trace_submit_reuses_custom_in_repo_attempts_root(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    attempts_root = repo_root / "custom-attempts"
    status_path = tmp_path / "git-status.bin"
    status_path.write_bytes(b"")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(
        bin_dir,
        "0123456789abcdef0123456789abcdef01234567",
        status_path=status_path,
    )
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))

    command = [
        "bash",
        str(SUBMITTER),
        "--dry-run",
        "--repo-root",
        str(repo_root),
        "--attempts-root",
        str(attempts_root),
        "--job-script",
        str(PILOT),
    ]
    first = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    first_submission = next((attempts_root / "submissions").iterdir())
    relative_receipt = (
        first_submission / "submit-receipt.json"
    ).relative_to(repo_root)
    status_path.write_bytes(f"?? {relative_receipt}".encode("utf-8") + b"\0")

    second = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert second.returncode == 0, second.stderr
    assert len(list((attempts_root / "submissions").iterdir())) == 2


def test_mocc_trace_submit_rejects_colon_in_attempts_root(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(bin_dir, "0123456789abcdef0123456789abcdef01234567")
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    attempts_root = tmp_path / "host:path"

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
            str(PILOT),
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "must not contain a colon" in result.stderr
    assert not attempts_root.exists()


def test_mocc_trace_submit_routes_pbs_streams_per_nonce(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "tools/pegasus").mkdir(parents=True)
    (repo_root / "external/ccbench").mkdir(parents=True)
    (repo_root / "tools/pegasus/mocc_trace_v1_policy.json").write_bytes(
        POLICY.read_bytes()
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_git(bin_dir, "0123456789abcdef0123456789abcdef01234567")
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    attempts_root = tmp_path / "attempts"
    for _ in range(2):
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
                str(PILOT),
            ],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    submissions = sorted((attempts_root / "submissions").iterdir())
    assert len(submissions) == 2
    stream_paths: set[str] = set()
    for submission in submissions:
        receipt = _load_json(submission / "submit-receipt.json")
        qsub_argv = receipt["qsub"]["argv"]
        stdout = qsub_argv[qsub_argv.index("-o") + 1]
        stderr = qsub_argv[qsub_argv.index("-e") + 1]
        assert stdout == str(submission / "pbs-job.stdout")
        assert stderr == str(submission / "pbs-job.stderr")
        assert stdout != stderr
        stream_paths.update((stdout, stderr))
    assert len(stream_paths) == 4


def test_mocc_trace_pilot_reads_exported_attempts_root() -> None:
    source = PILOT.read_text(encoding="utf-8")
    assert (
        'ATTEMPTS_ROOT=${IZANAGI_MOCC_TRACE_ATTEMPTS_ROOT:-"$REPO_ROOT/output/'
        'env/pegasus/mocc-trace/attempts"}'
    ) in source
    assert '"$WORKLOAD_JSON" "$ATTEMPTS_ROOT" "$SUBMISSION_DIR"' in source
    assert 'receipt.get("schema_version") == "pegasus-submit-receipt/v2"' in source
    assert 'f"IZANAGI_MOCC_TRACE_ATTEMPTS_ROOT={attempts_root}"' in source


def _load_fetch_third_party_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "fetch_third_party_mocc_contract", FETCH_THIRD_PARTY
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("explicit", (True, False))
def test_fetch_third_party_hydrate_staging_root_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], explicit: bool
) -> None:
    tool = _load_fetch_third_party_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    cache = tmp_path / "cache"
    chosen = tmp_path / "job-private" / "thirdparty-src"
    observed: dict[str, Path] = {}
    monkeypatch.setattr(
        tool,
        "_load_policy",
        lambda repo_root: ((), (), Path("legacy/staging")),
    )

    def fake_hydrate(
        repo_root: Path,
        cache_root: Path,
        sources: object,
        staging_relative: Path,
        *,
        staging_root: Path | None = None,
    ) -> list[dict[str, str]]:
        del repo_root, cache_root, sources, staging_relative
        assert staging_root is not None
        observed["root"] = staging_root
        return []

    monkeypatch.setattr(tool, "_hydrate", fake_hydrate)
    argv = [
        "hydrate",
        "--repo-root",
        str(repo),
        "--cache-root",
        str(cache),
    ]
    if explicit:
        argv.extend(("--staging-root", str(chosen)))
    assert tool.main(argv) == 0
    output = json.loads(capsys.readouterr().out)
    expected = chosen.resolve() if explicit else (repo / "legacy/staging").resolve()
    assert observed["root"] == expected
    assert output["source_root"] == str(expected)


def test_mocc_trace_pilot_uses_job_private_third_party_root() -> None:
    source = PILOT.read_text(encoding="utf-8")
    declaration = 'THIRD_PARTY_STAGING_ROOT="$TMPDIR/thirdparty-src"'
    option = '--staging-root "$THIRD_PARTY_STAGING_ROOT"'
    assert source.count(declaration) == 1
    assert source.count(option) == 1
    hydrate_index = source.index(option)
    for dependency in ("MASSTREE", "MIMALLOC", "GOOGLETEST"):
        cmake_option = f"-DFETCHCONTENT_SOURCE_DIR_{dependency}=$THIRD_PARTY_SOURCE_ROOT"
        assert source.count(cmake_option) == 1
        assert source.index(cmake_option) > hydrate_index


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


def test_mocc_trace_hydrate_interpreter_gate_selects_and_fails_closed(
    tmp_path: Path,
) -> None:
    source = PILOT.read_text(encoding="utf-8")
    begin = "# BEGIN T2780 HYDRATE INTERPRETER GATE"
    end = "# END T2780 HYDRATE INTERPRETER GATE"
    stop = 'THIRD_PARTY_SOURCE_ROOT=$(python3 - '
    for marker in (begin, end, stop):
        assert source.count(marker) == 1
    assert source.index(begin) < source.index(end) < source.index(stop)
    block = source[source.index(begin):source.index(stop)]
    candidates = ("python3", "python3.10", "python3.11", "python3.12")
    for case, selected in (("fallback", "python3.10"), ("first", "python3"),
                           ("rejected", None)):
        root = tmp_path / case
        repo = root / "repo"
        attempt = root / "attempt"
        bin_dir = root / "bin"
        for directory in (repo, attempt, bin_dir):
            directory.mkdir(parents=True)
        for command in ("realpath", "timeout"):
            real = shutil.which(command)
            assert real is not None
            (bin_dir / command).symlink_to(real)
        for name in candidates:
            stem = shlex.quote(str(root / name))
            _make_executable(bin_dir / name, f'''\
                #!/bin/sh
                if [ "$1" = -c ]; then
                  printf '%s\\n' "$@" >{stem}.probe
                  printf '%s\\n' "$PWD" "$PYTHONPATH" >{stem}.context
                  printf '%s\\n' {name} >>{shlex.quote(str(root / 'order'))}
                  exit {0 if name == selected else 1}
                fi
                printf '%s\\n' "$0" "$@" >{stem}.hydrate
                printf '%s\\n' "$PWD" >{stem}.cwd
                exit {3 if case == 'fallback' and name == 'python3' else 0}
            ''')
        variables = {
            "REPO_ROOT": repo, "TOOLS": repo / "tools", "ATTEMPT_DIR": attempt,
            "CACHE_ROOT": root / "cache", "TMPDIR": root,
            "THIRD_PARTY_CACHE_ENV": "IZANAGI_PEGASUS_THIRDPARTY_CACHE",
            "IZANAGI_PEGASUS_THIRDPARTY_CACHE": root / "cache",
            "PYTHONPATH": str(root / "inherited"),
        }
        prefix = "set -Eeuo pipefail\n" + "".join(
            f"{key}={shlex.quote(str(value))}\n" for key, value in variables.items()
        ) + '''THIRD_PARTY_STAGING_ROOT="$TMPDIR/thirdparty-src"
write_failure() { printf 'rc=%s\\nstage=%s\\nmessage=%s\\n' "$1" "$2" "$3" >"$ATTEMPT_DIR/failure"; }
'''
        result = subprocess.run(
            ["/bin/bash", "-c", prefix + block + "\nprintf 'reached\\n'\n"],
            cwd=root, env={"PATH": str(bin_dir)}, capture_output=True, text=True,
            check=False,
        )
        called = candidates if selected is None else candidates[:candidates.index(selected) + 1]
        assert (root / "order").read_text().splitlines() == list(called)
        for name in candidates:
            assert (root / f"{name}.probe").exists() == (name in called)
            if name in called:
                argv = (root / f"{name}.probe").read_text().splitlines()
                assert argv[0] == "-c"
                assert "import orchestrator.campaign.silo_ladder_rung1" in argv[1]
                assert "sys.version_info >= (3, 10)" in argv[1]
                assert argv[-1] == str(repo)
                context = (root / f"{name}.context").read_text().splitlines()
                assert context == [str(repo), f"{repo}/orchestrator:{repo}:{root}/inherited"]
        if selected is None:
            assert result.returncode == 2
            assert result.stdout == ""
            failure = (attempt / "failure").read_text()
            assert "rc=2\nstage=third_party\n" in failure
            diagnostic = (attempt / "third-party-hydrate.stderr").read_text()
            for name in candidates:
                rejection = f"{name}={(bin_dir / name).resolve()}"
                assert rejection in failure
                assert rejection in diagnostic
                assert not (root / f"{name}.hydrate").exists()
        else:
            assert result.returncode == 0, result.stderr
            assert result.stdout == "reached\n"
            assert not (attempt / "failure").exists()
            assert (root / f"{selected}.hydrate").read_text().splitlines() == [
                str((bin_dir / selected).resolve()), str(repo / "tools/fetch_third_party.py"),
                "hydrate", "--repo-root", str(repo), "--cache-root", str(root / "cache"),
                "--staging-root", str(root / "thirdparty-src"),
            ]
            assert (root / f"{selected}.cwd").read_text().strip() == str(root)
            for name in candidates:
                assert (root / f"{name}.hydrate").exists() == (name == selected)


def test_mocc_trace_instrumentation_patch_block_applies_and_binds(tmp_path: Path) -> None:
    source = PILOT.read_text(encoding="utf-8")
    begin = "# BEGIN T2780 INSTRUMENTATION PATCH"
    end = "# END T2780 INSTRUMENTATION PATCH"
    for marker in (begin, end, "build_mode() {"):
        assert source.count(marker) == 1
    assert source.index(begin) < source.index(end) < source.index("build_mode() {")
    block = source[source.index(begin):source.index(end)]
    postimage = b"patched transaction fixture\n"
    artifacts = ("instr-patch.sha256", "instr-patch.numstat", "instr-patch-source.sha256",
                 "instr-patch-apply.stdout", "instr-patch-apply.stderr")
    for case in ("success", "two-files", "wrong-path", "empty", "bad-count",
                 "check-fails", "apply-fails", "patch-changes", "general"):
        root = tmp_path / case
        repo = root / "repo"
        build = root / "build"
        attempt = root / "attempt"
        bin_dir = root / "bin"
        for directory in (repo / "patches", build / "cc/mocc", attempt, bin_dir):
            directory.mkdir(parents=True)
        patch = repo / "patches/instr-mocc-lock-coverage.patch"
        patch.write_bytes(b"fixture patch bytes\n")
        transaction = build / "cc/mocc/transaction.cc"
        transaction.write_bytes(b"preimage\n")
        for command in ("realpath", "sha256sum", "awk"):
            real = shutil.which(command)
            assert real is not None
            (bin_dir / command).symlink_to(real)
        numstat = {
            "two-files": "9\t1\tcc/mocc/transaction.cc\n1\t0\tcc/mocc/util.cc\n",
            "wrong-path": "9\t1\tcc/mocc/util.cc\n",
            "empty": "", "bad-count": "-\t1\tcc/mocc/transaction.cc\n",
        }.get(case, "9\t1\tcc/mocc/transaction.cc\n")
        calls = root / "git.jsonl"
        _make_executable(bin_dir / "git", f'''\
            #!{sys.executable}
            import json, sys
            from pathlib import Path
            with Path({str(calls)!r}).open("a") as stream:
                stream.write(json.dumps(sys.argv[1:]) + "\\n")
            if "--numstat" in sys.argv:
                print({numstat!r}, end="")
            elif "--check" in sys.argv:
                sys.exit({1 if case == 'check-fails' else 0})
            else:
                if {case == 'apply-fails'!r}:
                    sys.exit(1)
                Path(sys.argv[2], "cc/mocc/transaction.cc").write_bytes({postimage!r})
                if {case == 'patch-changes'!r}:
                    Path(sys.argv[-1]).write_bytes(b"changed patch")
        ''')
        variables = {"REPO_ROOT": repo, "BUILD_SOURCE": build, "ATTEMPT_DIR": attempt,
                     "T1943_G2": 0 if case == "general" else 1}
        prefix = "set -Eeuo pipefail\n" + "".join(
            f"{key}={shlex.quote(str(value))}\n" for key, value in variables.items()
        ) + '''write_failure() { printf 'rc=%s\\nstage=%s\\nmessage=%s\\n' "$1" "$2" "$3" >"$ATTEMPT_DIR/failure"; }
'''
        result = subprocess.run(
            ["/bin/bash", "-c", prefix + block + "\nprintf 'build-reached\\n'\n"],
            cwd=root, env={"PATH": str(bin_dir)}, capture_output=True, text=True,
            check=False,
        )
        recorded = [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []
        if case == "general":
            assert result.returncode == 0, result.stderr
            assert recorded == []
            assert transaction.read_bytes() == b"preimage\n"
            assert all(not (attempt / name).exists() for name in artifacts)
        elif case == "success":
            assert result.returncode == 0, result.stderr
            assert transaction.read_bytes() == postimage
            assert (attempt / "instr-patch-source.sha256").read_text() == hashlib.sha256(postimage).hexdigest() + "\n"
            assert (attempt / "instr-patch.sha256").read_text() == hashlib.sha256(patch.read_bytes()).hexdigest() + "\n"
            assert (attempt / "instr-patch.numstat").read_text() == numstat
            assert recorded == [
                ["-C", str(build), "apply", "--numstat", str(patch)],
                ["-C", str(build), "apply", "--check", str(patch)],
                ["-C", str(build), "apply", str(patch)],
            ]
            assert not (attempt / "failure").exists()
            assert all((attempt / name).is_file() for name in artifacts)
        else:
            assert result.returncode == 2, (case, result.stderr)
            assert result.stdout == ""
            failure = (attempt / "failure").read_text()
            assert "rc=2\nstage=instrumentation_patch\n" in failure
            if case in {"two-files", "wrong-path", "empty", "bad-count"}:
                assert "touch set differs" in failure
                assert len(recorded) == 1
                assert transaction.read_bytes() == b"preimage\n"
            elif case == "check-fails":
                assert "check failed" in failure
                assert len(recorded) == 2
            elif case == "apply-fails":
                assert "apply failed" in failure
                assert transaction.read_bytes() == b"preimage\n"
            else:
                assert "changed during application" in failure


def test_mocc_trace_verifier_source_root_follows_t1943_mode(tmp_path: Path) -> None:
    source = PILOT.read_text(encoding="utf-8")
    begin = '  VERIFIER_SOURCE_ROOT="$CCBENCH_BASE"'
    end = '  VERIFIER_RC=$verifier_rc'
    assert source.count(begin) == source.count(end) == 1
    assert source.index(begin) < source.index(end)
    block = source[source.index(begin):source.index(end)]
    verifier = tmp_path / "verifier"
    argv_path = tmp_path / "argv"
    _make_executable(verifier, f'''\
        #!/bin/sh
        printf '%s\\n' "$@" >{shlex.quote(str(argv_path))}
    ''')
    for mode in (1, 0):
        variables = {"REPO_ROOT": tmp_path, "ATTEMPT_DIR": tmp_path,
                     "CCBENCH_BASE": tmp_path / "base", "BUILD_SOURCE": tmp_path / "build",
                     "T1943_G2": mode, "VERIFIER_PY": verifier,
                     "TRACE_DIR": tmp_path / "trace", "COMMIT_COUNT": 17}
        prefix = "set -Eeuo pipefail\n" + "".join(
            f"{key}={shlex.quote(str(value))}\n" for key, value in variables.items()
        )
        result = subprocess.run(["/bin/bash", "-c", prefix + block],
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        argv = argv_path.read_text().splitlines()
        assert argv[:2] == ["-m", "orchestrator.verifier"]
        assert argv[argv.index("--ccbench-root") + 1] == str(
            tmp_path / ("build" if mode else "base")
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
            "verify_post_judgment_source_state() { return 0; }",
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
    prefix += 'CCBENCH_BASE="fixture-base"\nBUILD_SOURCE="fixture-build"\nT1943_G2=0\n'
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


def _mocc_trace_judgment_source_fragment() -> str:
    source = PILOT.read_text(encoding="utf-8")
    start_marker = "capture_judgment_source_state() {"
    end_marker = "\n\ncleanup_worktree() {"
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    fragment = source[start:end]
    assert fragment.count("--porcelain=v1") == 2
    assert fragment.count('with open(output, "xb") as handle:') == 1
    assert fragment.count("initialize_judgment_source_state() {") == 1
    assert fragment.count("verify_post_judgment_source_state() {") == 1
    return fragment


def _mocc_trace_marked_fragment(begin: str, end: str) -> str:
    source = PILOT.read_text(encoding="utf-8")
    assert source.count(begin) == 1
    assert source.count(end) == 1
    start = source.index(begin)
    finish = source.index(end, start) + len(end)
    return source[start:finish]


def _mocc_trace_policy_parse_fragment() -> str:
    return _mocc_trace_marked_fragment(
        "# BEGIN T2195 POLICY PARSE", "# END T2195 POLICY PARSE"
    )


def _mocc_trace_submit_receipt_pin_fragment() -> str:
    return _mocc_trace_marked_fragment(
        "# BEGIN T2195 SUBMIT RECEIPT PIN",
        "# END T2195 SUBMIT RECEIPT PIN",
    )


def _mocc_trace_policy_binding_fragment() -> str:
    return _mocc_trace_marked_fragment(
        "# BEGIN T2195 POLICY BINDING GATE",
        "# END T2195 POLICY BINDING GATE",
    )


def _policy_binding_receipt_bytes(
    policy_sha: object,
    mapping: object,
    exported_sha: str,
    *,
    duplicate_policy_key: bool = False,
    non_finite_top_level: bool = False,
) -> bytes:
    policy = {
        "raw_sha256": policy_sha,
        "expected_compiler_version_body_sha256": mapping,
    }
    document = {
        "schema_version": "pegasus-submit-receipt/v2",
        "policy": policy,
        "qsub": {
            "argv": [
                "qsub",
                "-v",
                f"IZANAGI_MOCC_POLICY_RAW_SHA256={exported_sha}",
                "fixture-job.sh",
            ]
        },
    }
    if non_finite_top_level:
        document["unreferenced_non_finite"] = float("nan")
    if not duplicate_policy_key:
        return (
            json.dumps(document, sort_keys=True, allow_nan=True) + "\n"
        ).encode("utf-8")
    encoded_policy = json.dumps(policy, sort_keys=True)
    return (
        "{"
        f'"policy":{encoded_policy},"policy":{encoded_policy},'
        '"qsub":{"argv":["qsub","-v",'
        f'"IZANAGI_MOCC_POLICY_RAW_SHA256={exported_sha}",'
        '"fixture-job.sh"]},'
        '"schema_version":"pegasus-submit-receipt/v2"}\n'
    ).encode("utf-8")


def _run_mocc_trace_policy_binding(
    tmp_path: Path,
    *,
    initial_policy_bytes: bytes | None = None,
    live_policy_bytes: bytes | None = None,
    receipt_policy_sha: object | None = None,
    receipt_mapping: object | None = None,
    exported_policy_sha: str | None = None,
    receipt_exported_sha: str | None = None,
    receipt_bytes: bytes | None = None,
    rebind_parsed_sha_to_live: bool = False,
    policy_kind: str = "regular",
    receipt_kind: str = "regular",
    policy_relative_path: str = "tools/pegasus/mocc_trace_v1_policy.json",
) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path]:
    repo_root = tmp_path / "repo"
    policy_path = repo_root / policy_relative_path
    policy_path.parent.mkdir(parents=True)
    if initial_policy_bytes is None:
        initial_policy_bytes = POLICY.read_bytes()
    if live_policy_bytes is None:
        live_policy_bytes = initial_policy_bytes
    policy_path.write_bytes(initial_policy_bytes)
    live_policy_path = tmp_path / "live-policy.json"
    live_policy_path.write_bytes(live_policy_bytes)
    live_sha = hashlib.sha256(live_policy_bytes).hexdigest()
    live_document = json.loads(live_policy_bytes)
    if receipt_policy_sha is None:
        receipt_policy_sha = live_sha
    if receipt_mapping is None:
        receipt_mapping = live_document[
            "expected_compiler_version_body_sha256"
        ]
    if exported_policy_sha is None:
        exported_policy_sha = live_sha
    if receipt_exported_sha is None:
        receipt_exported_sha = exported_policy_sha
    if receipt_bytes is None:
        receipt_bytes = _policy_binding_receipt_bytes(
            receipt_policy_sha, receipt_mapping, receipt_exported_sha
        )

    attempts_root = tmp_path / "attempts"
    submission_dir = attempts_root / "submissions/fixture-nonce"
    submission_dir.mkdir(parents=True)
    (submission_dir / "submit-receipt.json").write_bytes(receipt_bytes)
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    failure_path = attempt_dir / "failure.txt"
    bound_sha_path = attempt_dir / "bound-policy-sha.txt"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _make_executable(
        bin_dir / "git",
        """
        #!/bin/bash
        set -eu
        if [[ "$1" == "-C" ]]; then shift 2; fi
        case "$1" in
          rev-parse) printf '%s\n' 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' ;;
          status) exit 0 ;;
          *) exit 97 ;;
        esac
        """,
    )

    if policy_kind == "regular":
        replace_policy = (
            f"cp {shlex.quote(str(live_policy_path))} "
            f"{shlex.quote(str(policy_path))}"
        )
    elif policy_kind == "symlink":
        replace_policy = "\n".join(
            (
                f"rm {shlex.quote(str(policy_path))}",
                f"ln -s {shlex.quote(str(live_policy_path))} "
                f"{shlex.quote(str(policy_path))}",
            )
        )
    elif policy_kind in {"fifo", "writerless_fifo"}:
        replace_policy_lines = [
            f"rm {shlex.quote(str(policy_path))}",
            f"mkfifo {shlex.quote(str(policy_path))}",
        ]
        if policy_kind == "fifo":
            replace_policy_lines.extend(
                (
                    f"cat {shlex.quote(str(live_policy_path))} >"
                    f"{shlex.quote(str(policy_path))} &",
                    'BACKGROUND_PIDS+=("$!")',
                )
            )
        replace_policy = "\n".join(replace_policy_lines)
    else:
        raise AssertionError(policy_kind)

    if receipt_kind == "regular":
        replace_receipt = ":"
    else:
        saved_receipt = attempt_dir / "submit-receipt.saved.json"
        common = (
            f"mv \"$ATTEMPT_RECEIPT\" {shlex.quote(str(saved_receipt))}"
        )
        if receipt_kind == "symlink":
            replace_receipt = "\n".join(
                (
                    common,
                    f"ln -s {shlex.quote(str(saved_receipt))} "
                    '"$ATTEMPT_RECEIPT"',
                )
            )
        elif receipt_kind in {"fifo", "writerless_fifo"}:
            replace_receipt_lines = [common, 'mkfifo "$ATTEMPT_RECEIPT"']
            if receipt_kind == "fifo":
                replace_receipt_lines.extend(
                    (
                        f"cat {shlex.quote(str(saved_receipt))} >"
                        '"$ATTEMPT_RECEIPT" &',
                        'BACKGROUND_PIDS+=("$!")',
                    )
                )
            replace_receipt = "\n".join(replace_receipt_lines)
        else:
            raise AssertionError(receipt_kind)

    rebind_parse_sha = (
        f"POLICY_PARSE_RAW_SHA256={shlex.quote(live_sha)}"
        if rebind_parsed_sha_to_live
        else ":"
    )
    variables = {
        "REPO_ROOT": str(repo_root),
        "POLICY": str(policy_path),
        "ATTEMPTS_ROOT": str(attempts_root),
        "IZANAGI_SUBMISSION_NONCE": "fixture-nonce",
        "IZANAGI_MOCC_POLICY_RAW_SHA256": exported_policy_sha,
        "ATTEMPT_DIR": str(attempt_dir),
        "ATTEMPT_RECEIPT": "",
        "SUBMIT_RECEIPT_SHA": "",
        "POLICY_RAW_SHA256": "",
        "CURRENT_COMMIT": "",
        "JUDGMENT_PRE_CAPTURE": "",
        "JUDGMENT_PRE_SHA": "",
        "JUDGMENT_POST_CAPTURE": "",
        "JUDGMENT_POST_SHA": "",
        "FAILURE_PATH": str(failure_path),
    }
    prefix = ["set -Eeuo pipefail", "BACKGROUND_PIDS=()"]
    prefix.extend(
        f"{name}={shlex.quote(value)}" for name, value in variables.items()
    )
    prefix.extend(
        (
            "write_failure() {",
            "  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" >\"$FAILURE_PATH\"",
            "}",
            "cleanup_background() {",
            "  local pid",
            '  for pid in "${BACKGROUND_PIDS[@]}"; do',
            '    kill "$pid" 2>/dev/null || true',
            '    wait "$pid" 2>/dev/null || true',
            "  done",
            "}",
            "trap cleanup_background EXIT",
        )
    )
    script = "\n".join(
        (
            *prefix,
            _mocc_trace_policy_parse_fragment(),
            replace_policy,
            rebind_parse_sha,
            _mocc_trace_submit_receipt_pin_fragment(),
            replace_receipt,
            _mocc_trace_judgment_source_fragment(),
            "if ! initialize_judgment_source_state; then exit 2; fi",
            _mocc_trace_policy_binding_fragment(),
            f"printf '%s\\n' \"$POLICY_RAW_SHA256\" >"
            f"{shlex.quote(str(bound_sha_path))}",
            "",
        )
    )
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    result = _run_in_process_group(
        ["/bin/bash", "-c", script],
        cwd=REPO_ROOT,
        env=environment,
        timeout=10,
    )
    return result, attempt_dir, failure_path, bound_sha_path


def _assert_policy_binding_rejected(
    result: subprocess.CompletedProcess[str], failure_path: Path
) -> None:
    assert result.returncode == 2, result.stderr
    assert failure_path.read_text(encoding="utf-8").startswith(
        "2|policy_binding|"
    )


def test_mocc_trace_policy_binding_accepts_unchanged_policy(
    tmp_path: Path,
) -> None:
    result, attempt_dir, failure_path, bound_sha_path = (
        _run_mocc_trace_policy_binding(tmp_path)
    )
    assert result.returncode == 0, result.stderr
    assert not failure_path.exists()
    assert _load_json(attempt_dir / "judgment-source-pre.json")["clean"] is True
    assert bound_sha_path.read_text(encoding="ascii").strip() == hashlib.sha256(
        POLICY.read_bytes()
    ).hexdigest()


def test_mocc_trace_policy_binding_rejects_parse_restore_clean_attack(
    tmp_path: Path,
) -> None:
    mutated = json.loads(POLICY.read_text(encoding="utf-8"))
    mutated["expected_compiler_version_body_sha256"]["gcc"] = "1" * 64
    mutated_bytes = (
        json.dumps(mutated, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    for name, rebind_sha in (("attack", False), ("mapping-owner", True)):
        result, attempt_dir, failure_path, _ = _run_mocc_trace_policy_binding(
            tmp_path / name,
            initial_policy_bytes=mutated_bytes,
            live_policy_bytes=POLICY.read_bytes(),
            rebind_parsed_sha_to_live=rebind_sha,
        )
        assert _load_json(attempt_dir / "judgment-source-pre.json")[
            "clean"
        ] is True
        _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_rejects_parse_restore_clean_attack_raw(
    tmp_path: Path,
) -> None:
    canonical = json.dumps(
        json.loads(POLICY.read_text(encoding="utf-8")),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    result, attempt_dir, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path,
        initial_policy_bytes=b"\n" + canonical,
        live_policy_bytes=canonical,
    )
    assert _load_json(attempt_dir / "judgment-source-pre.json")["clean"] is True
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_rejects_submit_raw_sha_mismatch(
    tmp_path: Path,
) -> None:
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path, receipt_policy_sha="2" * 64
    )
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_rejects_submit_mapping_tamper(
    tmp_path: Path,
) -> None:
    mapping = dict(
        json.loads(POLICY.read_text(encoding="utf-8"))[
            "expected_compiler_version_body_sha256"
        ]
    )
    mapping["g++"] = "3" * 64
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path, receipt_mapping=mapping
    )
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_requires_submit_raw_sha256(
    tmp_path: Path,
) -> None:
    mapping = json.loads(POLICY.read_text(encoding="utf-8"))[
        "expected_compiler_version_body_sha256"
    ]
    policy_sha = hashlib.sha256(POLICY.read_bytes()).hexdigest()
    receipt = {
        "schema_version": "pegasus-submit-receipt/v2",
        "policy": {"expected_compiler_version_body_sha256": mapping},
        "qsub": {
            "argv": [
                "qsub",
                "-v",
                f"IZANAGI_MOCC_POLICY_RAW_SHA256={policy_sha}",
                "fixture-job.sh",
            ]
        },
    }
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path,
        receipt_bytes=(json.dumps(receipt, sort_keys=True) + "\n").encode(),
    )
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_rejects_env_binding_mismatch(
    tmp_path: Path,
) -> None:
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path, exported_policy_sha="4" * 64
    )
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_rejects_submit_raw_sha_export_tamper(
    tmp_path: Path,
) -> None:
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path, receipt_exported_sha="5" * 64
    )
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_rejects_noncanonical_policy_repo_path(
    tmp_path: Path,
) -> None:
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path, policy_relative_path="other/policy.json"
    )
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_rejects_symlink_policy(
    tmp_path: Path,
) -> None:
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path, policy_kind="symlink"
    )
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_rejects_non_regular_policy(
    tmp_path: Path,
) -> None:
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path, policy_kind="fifo"
    )
    _assert_policy_binding_rejected(result, failure_path)


@pytest.mark.parametrize(
    ("policy_kind", "receipt_kind"),
    (
        ("writerless_fifo", "regular"),
        ("regular", "writerless_fifo"),
    ),
)
def test_mocc_trace_policy_binding_rejects_writerless_fifo_without_blocking(
    tmp_path: Path,
    policy_kind: str,
    receipt_kind: str,
) -> None:
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path,
        policy_kind=policy_kind,
        receipt_kind=receipt_kind,
    )
    _assert_policy_binding_rejected(result, failure_path)


@pytest.mark.parametrize("receipt_kind", ("symlink", "fifo"))
def test_mocc_trace_policy_binding_rejects_symlink_or_non_regular_receipt_after_pin(
    tmp_path: Path, receipt_kind: str,
) -> None:
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path, receipt_kind=receipt_kind
    )
    _assert_policy_binding_rejected(result, failure_path)


@pytest.mark.parametrize("surface", ("policy", "receipt"))
def test_mocc_trace_policy_binding_rejects_non_finite_json(
    tmp_path: Path,
    surface: str,
) -> None:
    live_policy_bytes = _policy_bytes_with_non_finite_top_level()
    if surface == "policy":
        result, _, failure_path, _ = _run_mocc_trace_policy_binding(
            tmp_path,
            initial_policy_bytes=POLICY.read_bytes(),
            live_policy_bytes=live_policy_bytes,
            rebind_parsed_sha_to_live=True,
        )
    else:
        live_sha = hashlib.sha256(POLICY.read_bytes()).hexdigest()
        mapping = json.loads(POLICY.read_text(encoding="utf-8"))[
            "expected_compiler_version_body_sha256"
        ]
        receipt_bytes = _policy_binding_receipt_bytes(
            live_sha,
            mapping,
            live_sha,
            non_finite_top_level=True,
        )
        result, _, failure_path, _ = _run_mocc_trace_policy_binding(
            tmp_path,
            receipt_bytes=receipt_bytes,
        )
    _assert_policy_binding_rejected(result, failure_path)


@pytest.mark.parametrize(
    ("policy_sha", "mapping"),
    (
        (0, {"gcc": "5" * 64, "g++": "5" * 64}),
        ("5" * 64, None),
        ("5" * 64, {"gcc": "5" * 64}),
        ("5" * 64, {"gcc": "A" * 64, "g++": "5" * 64}),
    ),
)
def test_mocc_trace_policy_binding_rejects_malformed_receipt_policy(
    tmp_path: Path, policy_sha: object, mapping: object,
) -> None:
    live_sha = hashlib.sha256(POLICY.read_bytes()).hexdigest()
    result, _, failure_path, _ = _run_mocc_trace_policy_binding(
        tmp_path,
        receipt_bytes=_policy_binding_receipt_bytes(
            policy_sha, mapping, live_sha
        ),
    )
    _assert_policy_binding_rejected(result, failure_path)


@pytest.mark.parametrize("surface", ("policy", "receipt"))
def test_mocc_trace_policy_binding_rejects_duplicate_keys(
    tmp_path: Path, surface: str,
) -> None:
    live_sha = hashlib.sha256(POLICY.read_bytes()).hexdigest()
    mapping = json.loads(POLICY.read_text(encoding="utf-8"))[
        "expected_compiler_version_body_sha256"
    ]
    if surface == "receipt":
        result, _, failure_path, _ = _run_mocc_trace_policy_binding(
            tmp_path,
            receipt_bytes=_policy_binding_receipt_bytes(
                live_sha,
                mapping,
                live_sha,
                duplicate_policy_key=True,
            ),
        )
    else:
        duplicate = (
            '{"expected_cpu_model":"duplicate",'
            + POLICY.read_text(encoding="utf-8")[1:]
        ).encode("utf-8")
        duplicate_sha = hashlib.sha256(duplicate).hexdigest()
        result, _, failure_path, _ = _run_mocc_trace_policy_binding(
            tmp_path,
            initial_policy_bytes=POLICY.read_bytes(),
            live_policy_bytes=duplicate,
            exported_policy_sha=duplicate_sha,
            receipt_bytes=_policy_binding_receipt_bytes(
                duplicate_sha, mapping, duplicate_sha
            ),
            rebind_parsed_sha_to_live=True,
        )
    _assert_policy_binding_rejected(result, failure_path)


def test_mocc_trace_policy_binding_gate_order_and_markers() -> None:
    source = PILOT.read_text(encoding="utf-8")
    markers = (
        "# BEGIN T2195 POLICY PARSE",
        "# END T2195 POLICY PARSE",
        "# BEGIN T2195 SUBMIT RECEIPT PIN",
        "# END T2195 SUBMIT RECEIPT PIN",
        "# BEGIN T2195 POLICY BINDING GATE",
        "# END T2195 POLICY BINDING GATE",
        "# BEGIN T2195 POLICY FINALIZATION CHECK",
        "# END T2195 POLICY FINALIZATION CHECK",
        "# BEGIN T2780 HYDRATE INTERPRETER GATE",
        "# END T2780 HYDRATE INTERPRETER GATE",
        "# BEGIN T2780 INSTRUMENTATION PATCH",
        "# END T2780 INSTRUMENTATION PATCH",
    )
    assert {marker: source.count(marker) for marker in markers} == {
        marker: 1 for marker in markers
    }
    parse_begin = source.index("# BEGIN T2195 POLICY PARSE")
    parse_end = source.index("# END T2195 POLICY PARSE")
    receipt_pin_begin = source.index("# BEGIN T2195 SUBMIT RECEIPT PIN")
    receipt_pin_end = source.index("# END T2195 SUBMIT RECEIPT PIN")
    judgment = source.index("if ! initialize_judgment_source_state; then")
    binding_begin = source.index("# BEGIN T2195 POLICY BINDING GATE")
    binding_end = source.index("# END T2195 POLICY BINDING GATE")
    compiler = source.index("# BEGIN T1718 COMPILER VERSION BODY GATE")
    finalization_begin = source.index("# BEGIN T2195 POLICY FINALIZATION CHECK")
    finalization_end = source.index("# END T2195 POLICY FINALIZATION CHECK")
    receipt_writer = source.index("RECEIPT_WRITER_SHA=$(python3 -")
    assert (
        parse_begin
        < parse_end
        < receipt_pin_begin
        < receipt_pin_end
        < judgment
        < binding_begin
        < binding_end
        < compiler
        < finalization_begin
        < finalization_end
        < receipt_writer
    )


def test_mocc_trace_policy_binding_values_are_not_reassigned_before_finalization(
) -> None:
    source = PILOT.read_text(encoding="utf-8")
    binding_end_marker = "# END T2195 POLICY BINDING GATE"
    finalization_begin_marker = "# BEGIN T2195 POLICY FINALIZATION CHECK"
    start = source.index(binding_end_marker) + len(binding_end_marker)
    end = source.index(finalization_begin_marker, start)
    between = source[start:end]
    assert "POLICY_RAW_SHA256=" not in between
    assert "EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON=" not in between


def _make_judgment_git_stub(
    bin_dir: Path,
    tmp_path: Path,
    case: str,
    initial_head: str,
) -> None:
    changed_head = "b" * 40
    rev_count = tmp_path / "rev-count"
    status_count = tmp_path / "status-count"
    _make_executable(
        bin_dir / "git",
        f"""
        #!/bin/bash
        set -eu
        if [[ "$1" == "-C" ]]; then
          shift 2
        fi
        case "$1" in
          rev-parse)
            count=0
            [[ ! -f {shlex.quote(str(rev_count))} ]] || count=$(<{shlex.quote(str(rev_count))})
            count=$((count + 1))
            printf '%s\n' "$count" >{shlex.quote(str(rev_count))}
            if [[ "$count" -eq 2 && {shlex.quote(case)} == head_changed ]]; then
              printf '%s\n' {shlex.quote(changed_head)}
            else
              printf '%s\n' {shlex.quote(initial_head)}
            fi
            ;;
          status)
            count=0
            [[ ! -f {shlex.quote(str(status_count))} ]] || count=$(<{shlex.quote(str(status_count))})
            count=$((count + 1))
            printf '%s\n' "$count" >{shlex.quote(str(status_count))}
            printf '%s\n' "$@" >{shlex.quote(str(tmp_path / 'status-argv-'))}"$count"
            if [[ "$count" -eq 2 && {shlex.quote(case)} == dirty_after ]]; then
              printf ' M orchestrator/campaign/source.py\\0'
            elif [[ "$count" -eq 2 && {shlex.quote(case)} == capture_error ]]; then
              exit 31
            fi
            ;;
          *)
            exit 97
            ;;
        esac
        """,
    )


@pytest.mark.parametrize(
    "case",
    (
        pytest.param("head_changed", id="head_changed"),
        pytest.param("dirty_after", id="dirty_after"),
        pytest.param("capture_error", id="capture_error"),
        pytest.param("unchanged_clean", id="unchanged_clean"),
    ),
)
def test_mocc_trace_post_judgment_source_gate(tmp_path: Path, case: str) -> None:
    initial_head = "a" * 40
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _make_judgment_git_stub(bin_dir, tmp_path, case, initial_head)
    failure_path = attempt_dir / "failure.txt"
    completed_paths = (
        attempt_dir / "mocc-trace-pilot-receipt.json",
        attempt_dir / "mocc-trace-pilot-receipt.sha256",
        attempt_dir / "job-result.json",
    )
    prefix = "\n".join(
        (
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(tmp_path / 'repo'))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt_dir))}",
            f"FAILURE_PATH={shlex.quote(str(failure_path))}",
            'CURRENT_COMMIT=""',
            'JUDGMENT_PRE_CAPTURE=""',
            'JUDGMENT_PRE_SHA=""',
            'JUDGMENT_POST_CAPTURE=""',
            'JUDGMENT_POST_SHA=""',
            "failure_written=0",
            "write_failure() {",
            "  if [[ \"$failure_written\" -eq 0 ]]; then",
            "    failure_written=1",
            "    printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" >\"$FAILURE_PATH\"",
            "  fi",
            "}",
            "",
        )
    )
    suffix = "\n".join(
        (
            "",
            "if ! initialize_judgment_source_state; then exit 2; fi",
            "if ! verify_post_judgment_source_state; then exit 2; fi",
            *(f": >{shlex.quote(str(path))}" for path in completed_paths),
            "",
        )
    )
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            prefix + _mocc_trace_judgment_source_fragment() + suffix,
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    pre = _load_json(attempt_dir / "judgment-source-pre.json")
    post = _load_json(attempt_dir / "judgment-source-post.json")
    assert pre["capture_phase"] == "pre_judgment"
    assert post["capture_phase"] == "post_judgment"
    assert pre["pathspec"] == post["pathspec"] == [".", ":(exclude)output"]
    expected_status_argv = [
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        ".",
        ":(exclude)output",
    ]
    assert (tmp_path / "status-argv-1").read_text(
        encoding="utf-8"
    ).splitlines() == expected_status_argv
    assert (tmp_path / "status-argv-2").read_text(
        encoding="utf-8"
    ).splitlines() == expected_status_argv
    assert base64.b64decode(pre["status_bytes_base64"], validate=True) == b""
    if case == "unchanged_clean":
        assert result.returncode == 0, result.stderr
        assert post["capture_ok"] is True
        assert post["head"] == initial_head
        assert post["clean"] is True
        assert all(path.is_file() for path in completed_paths)
        assert not failure_path.exists()
    else:
        assert result.returncode == 2, result.stderr
        assert not any(path.exists() for path in completed_paths)
        failure = failure_path.read_text(encoding="utf-8")
        assert "|post_judgment_source|" in failure
        if case == "head_changed":
            assert post["capture_ok"] is True
            assert post["head"] == "b" * 40
            assert post["clean"] is True
        elif case == "dirty_after":
            assert post["capture_ok"] is True
            assert post["clean"] is False
            assert base64.b64decode(
                post["status_bytes_base64"], validate=True
            ).endswith(b"\0")
        else:
            assert post["capture_ok"] is False
            assert post["clean"] is False
            assert post["command_rc"]["status"] == 31


def test_mocc_trace_post_gate_precedes_mode_verdict_exit() -> None:
    source = PILOT.read_text(encoding="utf-8")
    assert source.count("if ! verify_post_judgment_source_state; then") == 2
    trace0_rc = source.index(
        'printf \'%s\\n\' "$CHECKER_RC" >"$ATTEMPT_DIR/trace0-preprocess-identity.rc"'
    )
    trace0_post = source.index(
        "if ! verify_post_judgment_source_state; then", trace0_rc
    )
    trace0_skip = source.index(
        'python3 - "$ATTEMPT_DIR/trace0-execution.json"', trace0_rc
    )
    trace0_exit = source.index('if [[ "$CHECKER_RC" -ne 0 ]]; then', trace0_post)
    verifier_rc = source.index(
        'printf \'%s\\n\' "$VERIFIER_RC" >"$ATTEMPT_DIR/verifier.rc"'
    )
    verifier_post = source.index(
        "if ! verify_post_judgment_source_state; then", verifier_rc
    )
    verifier_exit = source.index(
        'if [[ "$VERIFIER_RC" -ne 0 ]]; then', verifier_post
    )
    assert trace0_rc < trace0_skip < trace0_post < trace0_exit
    assert verifier_rc < verifier_post < verifier_exit


def _mocc_trace_finalization_fragment() -> str:
    source = PILOT.read_text(encoding="utf-8")
    start_marker = "# BEGIN T2195 POLICY FINALIZATION CHECK"
    writer_marker = (
        'RECEIPT_WRITER_SHA=$(python3 - '
        '"$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"'
    )
    git_marker = '\ngit -C "$CCBENCH_BASE" worktree remove'
    end_marker = '\nBUILD_SOURCE=""'
    assert source.count(start_marker) == 1
    assert source.count(writer_marker) == 1
    assert source.count(git_marker) == 1
    start = source.index(start_marker)
    git_start = source.index(git_marker, start)
    end = source.index(end_marker, git_start)
    assert start < git_start < end
    fragment = source[start:end]
    assert writer_marker in fragment
    assert 'RECEIPT_SHA=$(sha256sum "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"' in fragment
    assert 'python3 - "$ATTEMPT_DIR/job-result.json"' in fragment
    assert git_marker.lstrip("\n") in fragment
    return fragment


def _production_selected_tool_path(variable: str) -> Path:
    source = PILOT.read_text(encoding="utf-8")
    assignments = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(f"{variable}=$(realpath -e -- ")
    ]
    assert len(assignments) == 1
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            (
                "set -Eeuo pipefail\n"
                "REPO_ROOT=$1\n"
                f"{assignments[0]}\n"
                f'printf "%s\\n" "${variable}"\n'
            ),
            "mocc-tool-path",
            str(REPO_ROOT),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return Path(result.stdout.strip())


def _mocc_trace_checker_report_sha_fragment() -> str:
    source = PILOT.read_text(encoding="utf-8")
    start_marker = "  checker_report_sha_rc=0"
    end_marker = "\nelse\n  build_mode 1"
    assert source.count(start_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


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


def _receipt_tamper_fragment(*, update_sidecar: bool) -> str:
    update_sidecar_value = "1" if update_sidecar else "0"
    return f"""
python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" \
  "$ATTEMPT_DIR/mocc-trace-pilot-receipt.sha256" \
  {update_sidecar_value} <<'PY_TAMPER'
import hashlib
import json
import sys

path, sidecar_path, update_sidecar = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    payload = json.load(handle)
payload["created_epoch"] += 1
receipt_bytes = (
    json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\\n"
).encode("utf-8")
with open(path, "wb") as handle:
    handle.write(receipt_bytes)
if update_sidecar == "1":
    with open(sidecar_path, "w", encoding="ascii") as handle:
        handle.write(hashlib.sha256(receipt_bytes).hexdigest() + "\\n")
PY_TAMPER
"""


def _receipt_sidecar_tamper_fragment() -> str:
    return """
python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.sha256" \
  "$RECEIPT_WRITER_SHA" <<'PY_TAMPER_SIDECAR'
import sys

sidecar_path, writer_sha = sys.argv[1:]
with open(sidecar_path, encoding="ascii") as handle:
    sidecar_sha = handle.read().strip()
assert sidecar_sha == writer_sha
replacement_prefix = "0" if writer_sha[0] != "0" else "1"
with open(sidecar_path, "w", encoding="ascii") as handle:
    handle.write(replacement_prefix + writer_sha[1:] + "\\n")
PY_TAMPER_SIDECAR
"""


def _receipt_schema_tamper_and_rebind_fragment(
    target_schema: str = "mocc-trace-pilot-receipt/v3",
) -> str:
    fragment = """
python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" \
  "$ATTEMPT_DIR/mocc-trace-pilot-receipt.sha256" <<'PY_TAMPER_SCHEMA'
import hashlib
import json
import sys

receipt_path, sidecar_path = sys.argv[1:]
with open(receipt_path, encoding="utf-8") as handle:
    payload = json.load(handle)
payload["schema_version"] = "mocc-trace-pilot-receipt/v3"
receipt_bytes = (
    json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\\n"
).encode("utf-8")
with open(receipt_path, "wb") as handle:
    handle.write(receipt_bytes)
with open(sidecar_path, "w", encoding="ascii") as handle:
    handle.write(hashlib.sha256(receipt_bytes).hexdigest() + "\\n")
PY_TAMPER_SCHEMA
RECEIPT_WRITER_SHA=$(sha256sum \
  "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" | awk '{print $1}')
"""
    return fragment.replace('"mocc-trace-pilot-receipt/v3"', repr(target_schema))


def _run_mocc_trace_finalization(
    tmp_path: Path,
    *,
    trace_mode: int = 0,
    t1943_g2: bool = False,
    report_changes: dict[str, object] | None = None,
    report_bytes: bytes | None = None,
    report_encoding: str = "compact",
    report_mode: str = "file",
    checker_report_sha: str | None = None,
    realpath_aliases: bool = False,
    tamper_receipt_after_write: bool = False,
    tamper_receipt_and_sidecar_after_write: bool = False,
    tamper_sidecar_after_write: bool = False,
    tamper_receipt_after_shell_hash: bool = False,
    tamper_schema_and_rebind_after_write: bool = False,
    target_receipt_schema: str = "mocc-trace-pilot-receipt/v3",
    swap_report_to_symlink_before_open: bool = False,
    tamper_trace0_binary_after_absence: bool = False,
    tamper_manifest_leaf_after_discriminator: str | None = None,
    current_script_sha: str = "fixture-script-sha",
    post_gate_policy_state: str | None = None,
    receipt_kind: str = "regular",
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
        if (
            trace_mode == 0
            or t1943_g2
            or report_changes is not None
            or report_bytes is not None
        ):
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

    current_commit = "a" * 40
    submission_nonce = "fixture-nonce"
    submit_epoch = 1234567890
    fixture_policy_bytes = POLICY.read_bytes()
    fixture_policy_sha = hashlib.sha256(fixture_policy_bytes).hexdigest()
    fixture_policy_mapping = json.loads(fixture_policy_bytes)[
        "expected_compiler_version_body_sha256"
    ]
    fixture_workload = (
        {
            "extime_s": 3,
            "records": 10000,
            "threads": 48,
            "ycsb_max_ope": 10,
            "ycsb_rmw": 0,
            "ycsb_rratio": 50,
            "zipf_skew": 0.9,
        }
        if t1943_g2
        else {"records": 7}
    )
    submit_mocc_trace: dict[str, object] = {
        "base_oid": BASE_OID,
        "new_oid": NEW_OID,
        "trace_mode": trace_mode,
        "workload": fixture_workload,
    }
    if t1943_g2:
        submit_mocc_trace["t1943_g2_discriminator"] = True
    submit_receipt_path = attempt_dir / "submit-receipt.json"
    submit_receipt_path.write_text(
        json.dumps(
            {
                "schema_version": "pegasus-submit-receipt/v2",
                "submission_nonce": submission_nonce,
                "source_commit": current_commit,
                "qsub": {
                    "submit_epoch": submit_epoch,
                    "argv": [
                        "qsub",
                        "-v",
                        "IZANAGI_MOCC_POLICY_RAW_SHA256="
                        + fixture_policy_sha,
                        "fixture-job.sh",
                    ],
                },
                "mocc_trace": submit_mocc_trace,
                "policy": {
                    "expected_cpu_model": "fixture cpu",
                    "raw_sha256": fixture_policy_sha,
                    "expected_compiler_version_body_sha256": (
                        fixture_policy_mapping
                    ),
                },
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
    judgment_capture_paths: dict[str, Path] = {}
    judgment_capture_shas: dict[str, str] = {}
    for short_phase, capture_phase in (
        ("pre", "pre_judgment"),
        ("post", "post_judgment"),
    ):
        capture_path = attempt_dir / f"judgment-source-{short_phase}.json"
        capture_bytes = (
            json.dumps(
                {
                    "schema_version": "mocc-trace-judgment-source-capture/v1",
                    "capture_phase": capture_phase,
                    "capture_ok": True,
                    "head": current_commit,
                    "clean": True,
                    "pathspec": [".", ":(exclude)output"],
                    "status_format": (
                        "git status --porcelain=v1 -z --untracked-files=all"
                    ),
                    "status_bytes_base64": "",
                    "command_rc": {"head": 0, "status": 0},
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
        capture_path.write_bytes(capture_bytes)
        judgment_capture_paths[short_phase] = capture_path
        judgment_capture_shas[short_phase] = hashlib.sha256(
            capture_bytes
        ).hexdigest()
    commit_count_bytes = (
        json.dumps(
            {
                "schema_version": "mocc-commit-counter-witness/v1",
                "count": 7,
                "matched_line": "commit_counts_: 7",
                "source": "CCBench stdout commit_counts_ witness",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")
    (attempt_dir / "commit-count.json").write_bytes(commit_count_bytes)
    evidence_name = "throughput.json" if trace_mode == 0 else "verifier.json"
    evidence_bytes = (f'{{"fixture_mode":{trace_mode}}}\n').encode("utf-8")
    (attempt_dir / evidence_name).write_bytes(evidence_bytes)
    fixture_binary = tmp_path / "fixture-binary"
    fixture_binary.write_bytes(b"executed fixture binary\n")
    fixture_binary_sha = hashlib.sha256(fixture_binary.read_bytes()).hexdigest()

    if checker_report_sha is None:
        checker_report_sha = (
            hashlib.sha256(report_bytes).hexdigest()
            if trace_mode == 0 or t1943_g2
            else ""
        )
    checker_selected = _production_selected_tool_path("CHECKER_TOOL_PATH")
    verifier_selected = _production_selected_tool_path("VERIFIER_TOOL_PATH")
    checker_py = str(interpreter) if trace_mode == 0 or t1943_g2 else ""
    verifier_py = str(interpreter) if trace_mode == 1 else ""
    checker_tool_path = (
        str(checker_selected) if trace_mode == 0 or t1943_g2 else ""
    )
    verifier_tool_path = str(verifier_selected) if trace_mode == 1 else ""
    checker_tool_sha = (
        hashlib.sha256(checker_selected.read_bytes()).hexdigest()
        if checker_tool_path
        else ""
    )
    verifier_tool_sha = (
        hashlib.sha256(verifier_selected.read_bytes()).hexdigest()
        if verifier_tool_path
        else ""
    )
    checker_rc = "0" if trace_mode == 0 or t1943_g2 else "not-run"
    verifier_rc = "1" if t1943_g2 else ("not-run" if trace_mode == 0 else "0")
    trace_manifest_sha = witness_manifest_sha = ""
    discriminator_tool_path = discriminator_tool_sha = ""
    discriminator_result_sha = ""
    discriminator_result = discriminator_rc = "not-run"
    trace0_absence_sha = ""
    patch_path = patch_sha = patched_source_sha = ""
    if t1943_g2:
        patch = tmp_path / "fixture-repo/patches/instr-mocc-lock-coverage.patch"
        patch.parent.mkdir(parents=True)
        patch.write_bytes(b"fixture instrumentation patch\n")
        patched_source = build_source / "cc/mocc/transaction.cc"
        patched_source.parent.mkdir(parents=True)
        patched_source.write_bytes(b"fixture patched transaction source\n")
        patch_path = str(patch)
        patch_sha = hashlib.sha256(patch.read_bytes()).hexdigest()
        patched_source_sha = hashlib.sha256(patched_source.read_bytes()).hexdigest()
        (attempt_dir / "instr-patch.sha256").write_text(patch_sha + "\n")
        (attempt_dir / "instr-patch-source.sha256").write_text(patched_source_sha + "\n")
        (attempt_dir / "instr-patch.numstat").write_text("9\t1\tcc/mocc/transaction.cc\n")
        (attempt_dir / "instr-patch-apply.stdout").write_bytes(b"")
        (attempt_dir / "instr-patch-apply.stderr").write_bytes(b"")
        run_dir = tmp_path / "run"
        trace_root = run_dir / "trace"
        witness_root = run_dir / "witness"
        trace_root.mkdir(parents=True)
        witness_root.mkdir()
        trace_leaf = trace_root / "trace_0.log"
        witness_leaf = witness_root / "witness_0.log"
        trace_leaf.write_bytes(b"fixture trace leaf\n")
        witness_leaf.write_bytes(b"fixture witness leaf\n")
        trace_manifest = attempt_dir / "trace-manifest.json"
        witness_manifest = attempt_dir / "witness-manifest.json"
        for manifest_path, root, leaf, schema, kind in (
            (
                trace_manifest,
                trace_root,
                trace_leaf,
                "mocc-g2-standard-trace-manifest/v1",
                "standard-trace",
            ),
            (
                witness_manifest,
                witness_root,
                witness_leaf,
                "mocc-g2-payload-witness-manifest/v1",
                "payload-witness",
            ),
        ):
            leaf_bytes = leaf.read_bytes()
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": schema,
                        "artifact_kind": kind,
                        "root_dir": str(root),
                        "source_oid": NEW_OID,
                        "binary_sha256": fixture_binary_sha,
                        "workload": fixture_workload,
                        "files": [
                            {
                                "name": leaf.name,
                                "sha256": hashlib.sha256(leaf_bytes).hexdigest(),
                                "size_bytes": len(leaf_bytes),
                            }
                        ],
                    },
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        trace_manifest_sha = hashlib.sha256(trace_manifest.read_bytes()).hexdigest()
        witness_manifest_sha = hashlib.sha256(witness_manifest.read_bytes()).hexdigest()
        trace0_binary = (
            Path(str(build_source) + "-build-trace0") / "cc/mocc/mocc"
        )
        trace0_binary.parent.mkdir(parents=True)
        trace0_binary.write_bytes(b"fixture TRACE=0 binary\n")
        trace0_binary_sha = hashlib.sha256(trace0_binary.read_bytes()).hexdigest()
        (attempt_dir / "binary-trace0.sha256").write_text(
            trace0_binary_sha + "\n", encoding="ascii"
        )
        absence = attempt_dir / "trace0-watermark-absence.json"
        absence.write_text(
            json.dumps(
                {
                    "schema_version": "mocc-g2-trace0-watermark-absence/v1",
                    "binary_sha256": trace0_binary_sha,
                    "marker_absent": True,
                    "symbol_absent": True,
                    "binary_tokens_absent": True,
                    "present_binary_tokens": [],
                    "forbidden_binary_tokens": [
                        "directory_env",
                        "enable_env",
                        "marker",
                        "symbol",
                        "witness_file_prefix",
                    ],
                    "nm_rc": 0,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        trace0_absence_sha = hashlib.sha256(absence.read_bytes()).hexdigest()
        if tamper_trace0_binary_after_absence:
            trace0_binary.write_bytes(b"swapped TRACE=0 binary\n")
        discriminator_tool = (
            REPO_ROOT / "orchestrator/campaign/mocc_g2_discriminator.py"
        ).resolve(strict=True)
        discriminator_tool_path = str(discriminator_tool)
        discriminator_tool_sha = hashlib.sha256(
            discriminator_tool.read_bytes()
        ).hexdigest()
        discriminator_payload = {
            "schema_version": "mocc-g2-payload-discriminator/v1",
            "conclusion": "supported",
            "bindings": {
                "source_oid": NEW_OID,
                "binary_sha256": fixture_binary_sha,
                "workload": fixture_workload,
                "trace_manifest_sha256": trace_manifest_sha,
                "witness_manifest_sha256": witness_manifest_sha,
                "verifier_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            },
        }
        discriminator_path = attempt_dir / "discriminator.json"
        discriminator_path.write_text(
            json.dumps(discriminator_payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        discriminator_result_sha = hashlib.sha256(
            discriminator_path.read_bytes()
        ).hexdigest()
        discriminator_result = "supported"
        discriminator_rc = "0"
        if tamper_manifest_leaf_after_discriminator == "trace":
            trace_leaf.write_bytes(b"swapped trace leaf\n")
        elif tamper_manifest_leaf_after_discriminator == "witness":
            witness_leaf.write_bytes(b"swapped witness leaf\n")
        elif tamper_manifest_leaf_after_discriminator == "trace-file-set":
            (trace_root / "trace_1.log").write_bytes(b"unexpected trace leaf\n")
        elif tamper_manifest_leaf_after_discriminator == "witness-file-set":
            (witness_root / "witness_1.log").write_bytes(
                b"unexpected witness leaf\n"
            )
        elif tamper_manifest_leaf_after_discriminator is not None:
            raise AssertionError(tamper_manifest_leaf_after_discriminator)
    failure_path = attempt_dir / "fragment-failure.txt"
    fixture_repo_root = tmp_path / "fixture-repo"
    fixture_policy_path = (
        fixture_repo_root / "tools/pegasus/mocc_trace_v1_policy.json"
    )
    fixture_policy_path.parent.mkdir(parents=True)
    fixture_policy_path.write_bytes(fixture_policy_bytes)

    variables = {
        "REPO_ROOT": str(fixture_repo_root),
        "POLICY": str(fixture_policy_path),
        "ATTEMPT_DIR": str(attempt_dir),
        "ATTEMPT_RECEIPT": str(submit_receipt_path),
        "SUBMIT_RECEIPT_SHA": hashlib.sha256(
            submit_receipt_path.read_bytes()
        ).hexdigest(),
        "POLICY_RAW_SHA256": fixture_policy_sha,
        "POLICY_PARSE_RAW_SHA256": fixture_policy_sha,
        "IZANAGI_MOCC_POLICY_RAW_SHA256": fixture_policy_sha,
        "EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON": json.dumps(
            fixture_policy_mapping, sort_keys=True, separators=(",", ":")
        ),
        "CURRENT_COMMIT": current_commit,
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
        "BINARY": str(fixture_binary),
        "BINARY_SHA": fixture_binary_sha,
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
        "WORKLOAD_JSON": json.dumps(fixture_workload),
        "CMAKE_TARGET": "mocc",
        "BUILD_SOURCE": str(build_source),
        "CHECKER_PY": checker_py,
        "VERIFIER_PY": verifier_py,
        "CHECKER_REPORT_SHA": checker_report_sha,
        "CHECKER_TOOL_PATH": checker_tool_path,
        "CHECKER_TOOL_SHA": checker_tool_sha,
        "VERIFIER_TOOL_PATH": verifier_tool_path,
        "VERIFIER_TOOL_SHA": verifier_tool_sha,
        "JUDGMENT_PRE_CAPTURE": str(judgment_capture_paths["pre"]),
        "JUDGMENT_PRE_SHA": judgment_capture_shas["pre"],
        "JUDGMENT_POST_CAPTURE": str(judgment_capture_paths["post"]),
        "JUDGMENT_POST_SHA": judgment_capture_shas["post"],
        "CCBENCH_BASE": str(tmp_path / "ccbench-base"),
        "FAILURE_PATH": str(failure_path),
        "T1943_G2": "1" if t1943_g2 else "0",
        "TRACE_MANIFEST_SHA": trace_manifest_sha,
        "WITNESS_MANIFEST_SHA": witness_manifest_sha,
        "DISCRIMINATOR_TOOL_PATH": discriminator_tool_path,
        "DISCRIMINATOR_TOOL_SHA": discriminator_tool_sha,
        "DISCRIMINATOR_RESULT_SHA": discriminator_result_sha,
        "DISCRIMINATOR_RESULT": discriminator_result,
        "DISCRIMINATOR_RC": discriminator_rc,
        "TRACE0_WATERMARK_ABSENCE_SHA": trace0_absence_sha,
        "PATCH_PATH": patch_path,
        "PATCH_SHA": patch_sha,
        "PATCHED_SOURCE_SHA": patched_source_sha,
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
    policy_gate_prefix = ""
    if post_gate_policy_state is not None:
        if post_gate_policy_state == "mapping":
            changed_mapping = dict(fixture_policy_mapping)
            changed_mapping["gcc"] = "6" * 64
            mutation = (
                "EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON="
                + shlex.quote(
                    json.dumps(
                        changed_mapping, sort_keys=True, separators=(",", ":")
                    )
                )
            )
        elif post_gate_policy_state == "raw_sha":
            mutation = "POLICY_RAW_SHA256=" + "6" * 64
        else:
            raise AssertionError(post_gate_policy_state)
        policy_gate_prefix = (
            "\n"
            + _mocc_trace_policy_binding_fragment()
            + "\n"
            + mutation
            + "\n"
        )
    if swap_report_to_symlink_before_open:
        swapped_target = tmp_path / "swapped-report-target.json"
        swapped_target.write_bytes(report_bytes)
        report_open_marker = "        checker_report_path = os.open(\n"
        assert fragment.count(report_open_marker) == 1
        report_swap = (
            "        os.unlink(checker_report_path)\n"
            f"        os.symlink({str(swapped_target)!r}, checker_report_path)\n"
        )
        fragment = fragment.replace(
            report_open_marker,
            report_swap + report_open_marker,
            1,
        )
    prehash_tamper_count = sum(
        (
            tamper_receipt_after_write,
            tamper_receipt_and_sidecar_after_write,
            tamper_sidecar_after_write,
            tamper_schema_and_rebind_after_write,
        )
    )
    assert prehash_tamper_count <= 1
    if prehash_tamper_count:
        tamper = (
            _receipt_schema_tamper_and_rebind_fragment(target_receipt_schema)
            if tamper_schema_and_rebind_after_write
            else (
                _receipt_sidecar_tamper_fragment()
                if tamper_sidecar_after_write
                else _receipt_tamper_fragment(
                    update_sidecar=tamper_receipt_and_sidecar_after_write
                )
            )
        )
        receipt_sha_marker = "\nRECEIPT_SHA="
        assert fragment.count(receipt_sha_marker) == 1
        fragment = fragment.replace(
            receipt_sha_marker,
            tamper + receipt_sha_marker,
            1,
        )
    if tamper_receipt_after_shell_hash:
        tamper = _receipt_tamper_fragment(update_sidecar=False)
        job_writer_marker = '\npython3 - "$ATTEMPT_DIR/job-result.json"'
        assert fragment.count(job_writer_marker) == 1
        fragment = fragment.replace(
            job_writer_marker,
            tamper + job_writer_marker,
            1,
        )
    if receipt_kind == "writerless_fifo":
        submit_receipt_path.unlink()
        os.mkfifo(submit_receipt_path)
    elif receipt_kind != "regular":
        raise AssertionError(receipt_kind)
    result = _run_in_process_group(
        [
            "/bin/bash",
            "-c",
            "\n".join(prefix_lines) + policy_gate_prefix + fragment,
        ],
        cwd=REPO_ROOT,
        timeout=10,
    )
    return result, attempt_dir, report_bytes


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_mocc_trace_finalization_records_bound_policy(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(tmp_path)
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert receipt["policy"] == {
        "repo_path": "tools/pegasus/mocc_trace_v1_policy.json",
        "raw_sha256": hashlib.sha256(POLICY.read_bytes()).hexdigest(),
        "expected_compiler_version_body_sha256": policy[
            "expected_compiler_version_body_sha256"
        ],
    }


def test_mocc_trace_finalization_rejects_mapping_changed_after_gate(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, post_gate_policy_state="mapping"
    )
    assert result.returncode == 2, result.stderr
    assert not (attempt_dir / "mocc-trace-pilot-receipt.json").exists()
    failure = (attempt_dir / "fragment-failure.txt").read_text(encoding="utf-8")
    assert failure.startswith("2|policy_binding|")
    assert "at finalization" in failure


def test_mocc_trace_finalization_rejects_raw_sha_changed_after_gate(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, post_gate_policy_state="raw_sha"
    )
    assert result.returncode == 2, result.stderr
    assert not (attempt_dir / "mocc-trace-pilot-receipt.json").exists()
    failure = (attempt_dir / "fragment-failure.txt").read_text(encoding="utf-8")
    assert failure.startswith("2|policy_binding|")
    assert "at finalization" in failure


def test_mocc_trace_finalization_rejects_writerless_fifo_receipt_without_blocking(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, receipt_kind="writerless_fifo"
    )
    assert result.returncode == 2, result.stderr
    assert not (attempt_dir / "mocc-trace-pilot-receipt.json").exists()
    failure = (attempt_dir / "fragment-failure.txt").read_text(encoding="utf-8")
    assert failure.startswith("2|policy_binding|")


def _mocc_trace_artifact_manifest_fragment(*, write_manifest: bool) -> str:
    source = PILOT.read_text(encoding="utf-8")
    start_marker = "write_artifact_classification_manifest() {"
    call_marker = "\nwrite_artifact_classification_manifest\n"
    end_marker = "\ncapture_judgment_source_state() {"
    assert source.count(start_marker) == 1
    assert source.count(call_marker) == 1
    assert source.count(end_marker) == 1
    start = source.index(start_marker)
    call = source.index(call_marker, start)
    end = source.index(end_marker, call)
    assert start < call < end
    return source[start:end] if write_manifest else source[start:call]


def _run_mocc_trace_artifact_manifest_fragment(
    attempt_dir: Path,
    trace_mode: int,
    *,
    t1943_g2: bool = False,
    write_manifest: bool,
    validate_manifest: bool,
) -> subprocess.CompletedProcess[str]:
    fragment = _mocc_trace_artifact_manifest_fragment(
        write_manifest=write_manifest
    )
    suffix = (
        "\nvalidate_artifact_classification_manifest\n"
        if validate_manifest
        else ""
    )
    return subprocess.run(
        [
            "/bin/bash",
            "-c",
            "\n".join(
                (
                    "set -Eeuo pipefail",
                    f"ATTEMPT_DIR={shlex.quote(str(attempt_dir))}",
                    f"TRACE_MODE={trace_mode}",
                    f"T1943_G2={1 if t1943_g2 else 0}",
                    fragment,
                    suffix,
                )
            ),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _artifact_manifest_entries(
    manifest: dict[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, list)
    entries: dict[tuple[str, str], dict[str, object]] = {}
    for value in artifacts:
        assert isinstance(value, dict)
        scope = value.get("scope")
        path_pattern = value.get("path_pattern")
        assert isinstance(scope, str)
        assert isinstance(path_pattern, str)
        identity = (scope, path_pattern)
        assert identity not in entries
        entries[identity] = value
    return entries


def _pilot_durable_output_path_patterns() -> set[tuple[str, str]]:
    source = PILOT.read_text(encoding="utf-8")
    root_prefix = {
        "ATTEMPT_DIR": "",
        "RUN_DIR": "run/",
        "TRACE_DIR": "run/trace/",
    }
    patterns: set[tuple[str, str]] = set()
    for match in re.finditer(
        r'"\$(ATTEMPT_DIR|RUN_DIR|TRACE_DIR)/([^"\n]+)"', source
    ):
        root_name, relative = match.groups()
        relative = re.sub(
            r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*", "*", relative
        )
        relative = re.sub(r"[*]+", "*", relative)
        normalized = root_prefix[root_name] + relative
        if normalized not in {"run", "run/trace"}:
            patterns.add(("attempt_dir", normalized))

    trace_globs = re.findall(r'trace_dir\.glob\("([^"\n]+)"\)', source)
    assert trace_globs == ["trace_*.log"]
    patterns.add(("attempt_dir", f"run/trace/{trace_globs[0]}"))

    witness_globs = re.findall(r'root\.glob\("(witness_[^"\n]+)"\)', source)
    assert witness_globs == ["witness_*.log"]
    patterns.add(("attempt_dir", f"run/witness/{witness_globs[0]}"))

    submission_outputs = re.findall(
        r'os\.path\.join\(submission_dir, "(pbs-job\.(?:stdout|stderr))"\)',
        source,
    )
    assert set(submission_outputs) == {"pbs-job.stdout", "pbs-job.stderr"}
    patterns.update(("submission_dir", value) for value in submission_outputs)

    return patterns


@pytest.mark.parametrize(
    "trace_mode",
    (
        pytest.param(0, id="trace0"),
        pytest.param(1, id="trace1"),
    ),
)
def test_mocc_trace_artifact_manifest_schema_and_create_only(
    tmp_path: Path, trace_mode: int
) -> None:
    attempt_dir = tmp_path / f"attempt-{trace_mode}"
    attempt_dir.mkdir()
    result = _run_mocc_trace_artifact_manifest_fragment(
        attempt_dir,
        trace_mode,
        write_manifest=True,
        validate_manifest=True,
    )
    assert result.returncode == 0, result.stderr
    path = attempt_dir / "artifact-classification-manifest.json"
    original_bytes = path.read_bytes()
    manifest = _load_json(path)
    assert manifest["schema_version"] == (
        "mocc-trace-artifact-classification-manifest/v1"
    )
    assert manifest["trace_mode"] == trace_mode
    assert set(manifest["classification_enum"]) == {
        "correctness_evidence",
        "performance_evidence",
        "operational_diagnostic",
    }
    entries = _artifact_manifest_entries(manifest)
    assert entries
    for entry in entries.values():
        assert entry["classification"] in manifest["classification_enum"]
        assert entry["trace1_performance_use_forbidden"] is (trace_mode == 1)
        reason = entry["reason"]
        assert isinstance(reason, str) and reason
        assert "\n" not in reason and "\r" not in reason
        if trace_mode == 1 and entry["classification"] == "performance_evidence":
            assert entry["trace1_performance_use_forbidden"] is True

    second = _run_mocc_trace_artifact_manifest_fragment(
        attempt_dir,
        trace_mode,
        write_manifest=True,
        validate_manifest=False,
    )
    assert second.returncode != 0
    assert path.read_bytes() == original_bytes


def test_mocc_trace_artifact_manifest_covers_job_output_path_set(
    tmp_path: Path,
) -> None:
    manifest_patterns: set[tuple[str, str]] = set()
    for trace_mode in (0, 1):
        attempt_dir = tmp_path / f"attempt-{trace_mode}"
        attempt_dir.mkdir()
        result = _run_mocc_trace_artifact_manifest_fragment(
            attempt_dir,
            trace_mode,
            write_manifest=True,
            validate_manifest=True,
        )
        assert result.returncode == 0, result.stderr
        manifest_patterns.update(
            _artifact_manifest_entries(
                _load_json(attempt_dir / "artifact-classification-manifest.json")
            )
        )
    t1943_attempt = tmp_path / "attempt-t1943"
    (t1943_attempt / "run/witness").mkdir(parents=True)
    result = _run_mocc_trace_artifact_manifest_fragment(
        t1943_attempt,
        1,
        t1943_g2=True,
        write_manifest=True,
        validate_manifest=True,
    )
    assert result.returncode == 0, result.stderr
    manifest_patterns.update(
        _artifact_manifest_entries(
            _load_json(t1943_attempt / "artifact-classification-manifest.json")
        )
    )
    assert manifest_patterns == _pilot_durable_output_path_patterns()


def test_t1943_artifact_paths_are_absent_from_general_manifests(
    tmp_path: Path,
) -> None:
    general_attempt = tmp_path / "general"
    general_attempt.mkdir()
    general = _run_mocc_trace_artifact_manifest_fragment(
        general_attempt,
        1,
        write_manifest=True,
        validate_manifest=True,
    )
    assert general.returncode == 0, general.stderr
    general_entries = _artifact_manifest_entries(
        _load_json(general_attempt / "artifact-classification-manifest.json")
    )
    dedicated_paths = {
        "instr-patch.sha256",
        "instr-patch.numstat",
        "instr-patch-source.sha256",
        "instr-patch-apply.stdout",
        "instr-patch-apply.stderr",
        "run/witness",
        "run/witness/witness_*.log",
        "witness-manifest.json",
        "trace0-watermark-absence.json",
        "discriminator.json",
        "discriminator.stderr",
        "discriminator.rc",
    }
    assert not any(path in dedicated_paths for _scope, path in general_entries)

    t1943_attempt = tmp_path / "t1943"
    (t1943_attempt / "run/witness").mkdir(parents=True)
    dedicated = _run_mocc_trace_artifact_manifest_fragment(
        t1943_attempt,
        1,
        t1943_g2=True,
        write_manifest=True,
        validate_manifest=True,
    )
    assert dedicated.returncode == 0, dedicated.stderr
    dedicated_entries = _artifact_manifest_entries(
        _load_json(t1943_attempt / "artifact-classification-manifest.json")
    )
    assert dedicated_paths <= {path for _scope, path in dedicated_entries}
    for name in ("instr-patch.sha256", "instr-patch.numstat", "instr-patch-source.sha256"):
        assert dedicated_entries[("attempt_dir", name)]["classification"] == "correctness_evidence"
    for name in ("instr-patch-apply.stdout", "instr-patch-apply.stderr"):
        assert dedicated_entries[("attempt_dir", name)]["classification"] == "operational_diagnostic"
        assert "normally empty" in dedicated_entries[("attempt_dir", name)]["reason"]


@pytest.mark.parametrize(
    ("witness_root_kind", "expected_rc"),
    (
        pytest.param("directory", 0, id="real-directory"),
        pytest.param("symlink", 1, id="symlink"),
        pytest.param("file", 1, id="non-directory"),
    ),
)
def test_t1943_artifact_manifest_requires_real_witness_directory(
    tmp_path: Path, witness_root_kind: str, expected_rc: int
) -> None:
    source = PILOT.read_text(encoding="utf-8")
    assert ".stat(follow_symlinks=False)" not in source
    assert "witness_info = os.lstat(witness_root)" in source

    case_root = tmp_path / witness_root_kind
    attempt_dir = case_root / "attempt"
    run_dir = attempt_dir / "run"
    run_dir.mkdir(parents=True)
    witness_root = run_dir / "witness"
    if witness_root_kind == "directory":
        witness_root.mkdir()
    elif witness_root_kind == "symlink":
        target = case_root / "witness-target"
        target.mkdir()
        witness_root.symlink_to(target, target_is_directory=True)
    elif witness_root_kind == "file":
        witness_root.write_bytes(b"not a directory\n")
    else:
        raise AssertionError(witness_root_kind)

    result = _run_mocc_trace_artifact_manifest_fragment(
        attempt_dir,
        1,
        t1943_g2=True,
        write_manifest=True,
        validate_manifest=True,
    )
    if expected_rc == 0:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode != 0
        assert "witness" in result.stderr


def test_mocc_trace_artifact_manifest_names_performance_derivation_routes(
    tmp_path: Path,
) -> None:
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    result = _run_mocc_trace_artifact_manifest_fragment(
        attempt_dir,
        1,
        write_manifest=True,
        validate_manifest=True,
    )
    assert result.returncode == 0, result.stderr
    entries = _artifact_manifest_entries(
        _load_json(attempt_dir / "artifact-classification-manifest.json")
    )
    reasons = {
        path_pattern: entry["reason"]
        for (scope, path_pattern), entry in entries.items()
        if scope == "attempt_dir"
    }
    assert "commit-count witness" in reasons["run/workload.stdout"]
    assert "derive throughput" in reasons["run/workload.elapsed_ns"]
    assert "derive throughput" in reasons["commit-count.json"]
    assert "timing or transaction-count" in reasons["run/trace/trace_*.log"]
    assert "stats.txns" in reasons["verifier.json"]


def test_mocc_trace_artifact_manifest_trace0_allows_same_performance_files(
    tmp_path: Path,
) -> None:
    manifests = {}
    for trace_mode in (0, 1):
        attempt_dir = tmp_path / f"attempt-{trace_mode}"
        attempt_dir.mkdir()
        result = _run_mocc_trace_artifact_manifest_fragment(
            attempt_dir,
            trace_mode,
            write_manifest=True,
            validate_manifest=True,
        )
        assert result.returncode == 0, result.stderr
        manifests[trace_mode] = _artifact_manifest_entries(
            _load_json(attempt_dir / "artifact-classification-manifest.json")
        )

    shared_performance_paths = {
        ("attempt_dir", "run/workload.stdout"),
        ("attempt_dir", "run/workload.elapsed_ns"),
        ("attempt_dir", "commit-count.json"),
    }
    for identity in shared_performance_paths:
        trace0_entry = manifests[0][identity]
        trace1_entry = manifests[1][identity]
        assert trace0_entry["classification"] == "performance_evidence"
        assert trace1_entry["classification"] == "performance_evidence"
        assert trace0_entry["trace1_performance_use_forbidden"] is False
        assert trace1_entry["trace1_performance_use_forbidden"] is True


def test_mocc_trace_artifact_manifest_rejects_non_derivable_claim(
    tmp_path: Path,
) -> None:
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    written = _run_mocc_trace_artifact_manifest_fragment(
        attempt_dir,
        1,
        write_manifest=True,
        validate_manifest=False,
    )
    assert written.returncode == 0, written.stderr
    path = attempt_dir / "artifact-classification-manifest.json"
    manifest = _load_json(path)
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, list) and artifacts
    assert isinstance(artifacts[0], dict)
    artifacts[0]["reason"] = "Performance values are not derivable from this file."
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    rejected = _run_mocc_trace_artifact_manifest_fragment(
        attempt_dir,
        1,
        write_manifest=False,
        validate_manifest=True,
    )
    assert rejected.returncode != 0
    assert "manifest overstates performance redaction" in rejected.stderr


def test_mocc_trace_artifact_manifest_rejects_unclassified_real_file(
    tmp_path: Path,
) -> None:
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    written = _run_mocc_trace_artifact_manifest_fragment(
        attempt_dir,
        0,
        write_manifest=True,
        validate_manifest=False,
    )
    assert written.returncode == 0, written.stderr
    unexpected = attempt_dir / "new-unclassified-output.bin"
    unexpected.write_bytes(b"fixture\n")
    rejected = _run_mocc_trace_artifact_manifest_fragment(
        attempt_dir,
        0,
        write_manifest=False,
        validate_manifest=True,
    )
    assert rejected.returncode != 0
    assert unexpected.name in rejected.stderr


def test_mocc_trace_artifact_manifest_validation_follows_final_output() -> None:
    source = PILOT.read_text(encoding="utf-8")
    job_result = source.index('python3 - "$ATTEMPT_DIR/job-result.json"')
    worktree_remove = source.index(
        'git -C "$CCBENCH_BASE" worktree remove --force "$BUILD_SOURCE"',
        job_result,
    )
    validation = source.index(
        "if ! validate_artifact_classification_manifest; then",
        worktree_remove,
    )
    final_exit = source.index("\nexit 0", validation)
    assert job_result < worktree_remove < validation < final_exit


def test_t1943_artifact_classification_precedes_durable_completed_json() -> None:
    source = PILOT.read_text(encoding="utf-8")
    t1943_branch = source.index('if [[ "$T1943_G2" -eq 1 ]]; then', source.index(
        'printf \'%s\\n\' "$qstat_accounting_rc"'
    ))
    early_validation = source.index(
        "if ! validate_artifact_classification_manifest; then", t1943_branch
    )
    receipt = source.index(
        'RECEIPT_WRITER_SHA=$(python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"',
        early_validation,
    )
    job_result = source.index('python3 - "$ATTEMPT_DIR/job-result.json"', receipt)
    assert t1943_branch < early_validation < receipt < job_result


def test_t1943_artifact_classification_failure_leaves_no_completed_json(
    tmp_path: Path,
) -> None:
    attempt = tmp_path / "attempt"
    (attempt / "run/witness").mkdir(parents=True)
    written = _run_mocc_trace_artifact_manifest_fragment(
        attempt,
        1,
        t1943_g2=True,
        write_manifest=True,
        validate_manifest=False,
    )
    assert written.returncode == 0, written.stderr
    (attempt / "unclassified-after-discriminator.bin").write_bytes(b"bad\n")
    rejected = _run_mocc_trace_artifact_manifest_fragment(
        attempt,
        1,
        t1943_g2=True,
        write_manifest=False,
        validate_manifest=True,
    )
    assert rejected.returncode != 0
    assert not (attempt / "mocc-trace-pilot-receipt.json").exists()
    assert not (attempt / "job-result.json").exists()


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
        "# BEGIN T2780 HYDRATE INTERPRETER GATE",
        "# END T2780 HYDRATE INTERPRETER GATE",
        "# BEGIN T2780 INSTRUMENTATION PATCH",
        "# END T2780 INSTRUMENTATION PATCH",
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
        "\nPY\n) || {\n  write_failure 2 "
        "trace0_preprocess_identity_report_binding",
        python_start,
    )
    writer = source[python_start:python_end]
    outside_writer = source[:python_start] + source[python_end:]
    assert writer.count('open(checker_report_path, "rb")') == 1
    assert writer.count("report_bytes = handle.read()") == 1
    assert writer.count("os.fstat(checker_report_path)") == 1
    assert writer.count("checker_report_path, os.O_RDONLY | os.O_NOFOLLOW") == 1
    assert writer.count('json.loads(report_bytes.decode("utf-8"))') == 1
    assert writer.count('report.get("schema")') == 1
    assert writer.count('report.get("guarantee")') == 1
    assert 'report.get("schema")' not in outside_writer
    assert 'report.get("guarantee")' not in outside_writer
    assert "REPORT_SCHEMA" not in source
    assert "REPORT_GUARANTEE" not in source
    assert source.count(
        "fd = os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW)"
    ) == 1
    assert source.count("candidate_stat = os.fstat(fd)") == 1
    assert source.count(
        "receipt_bytes = read_regular_file_no_follow(receipt_path)"
    ) == 1
    assert source.count("read_regular_file_no_follow(receipt_sha_path)") == 1


@pytest.mark.parametrize(
    ("sha256sum_body", "expected_rc", "expected_reason"),
    (
        pytest.param(
            "exit 23\n",
            2,
            "failed to hash TRACE=0 preprocess identity report after checker success",
            id="sha256sum-failure",
        ),
        pytest.param(
            "printf '%s\\n' not-a-sha\n",
            2,
            "TRACE=0 preprocess identity report hash is not 64 lowercase hex",
            id="malformed-digest",
        ),
    ),
)
def test_mocc_trace_binding_f5_early_report_sha_failure_uses_binding_stage(
    tmp_path: Path,
    sha256sum_body: str,
    expected_rc: int,
    expected_reason: str,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _make_executable(bin_dir / "sha256sum", f"#!/bin/bash\n{sha256sum_body}")
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    (attempt_dir / "trace0-preprocess-identity.json").write_text(
        "{}\n", encoding="utf-8"
    )
    failure_path = attempt_dir / "failure.txt"
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(bin_dir), environment["PATH"]))
    environment["ATTEMPT_DIR"] = str(attempt_dir)
    environment["FAILURE_PATH"] = str(failure_path)
    script = "\n".join(
        (
            "set -Eeuo pipefail",
            "write_failure() {",
            "  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" >\"$FAILURE_PATH\"",
            "}",
            "trap 'rc=$?; write_failure \"$rc\" shell \"ERR trap\"; exit \"$rc\"' ERR",
            _mocc_trace_checker_report_sha_fragment(),
        )
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected_rc, result.stderr
    assert failure_path.read_text(encoding="utf-8") == (
        f"{expected_rc}|trace0_preprocess_identity_report_binding|"
        f"{expected_reason}\n"
    )


def test_mocc_trace_binding_g1_avoids_realpath_strict_keyword() -> None:
    source = PILOT.read_text(encoding="utf-8")
    assert re.search(
        r"os\.path\.realpath\s*\([^)]*\bstrict\s*=", source, flags=re.DOTALL
    ) is None


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


@pytest.mark.parametrize("identity", ("repo", "compiler"))
def test_mocc_trace_binding_f3_rejects_nonexistent_identity_parent_paths(
    tmp_path: Path, identity: str
) -> None:
    real_python = shutil.which("python3")
    assert real_python is not None
    if identity == "repo":
        report_changes = {
            "repo": str(tmp_path / "build-source" / "does-not-exist" / "..")
        }
    else:
        report_changes = {
            "compiler": {
                "path": str(
                    Path(os.path.realpath(real_python)) / "does-not-exist" / ".."
                )
            }
        }
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, report_changes=report_changes
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


def test_mocc_trace_binding_f2_rejects_report_symlink_swap_before_fd_open(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, swap_report_to_symlink_before_open=True
    )
    _assert_receipt_binding_rejected(result, attempt_dir)
    assert (attempt_dir / "trace0-preprocess-identity.json").is_symlink()


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


def test_mocc_trace_binding_f1_rejects_receipt_and_sidecar_replaced_together(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, tamper_receipt_and_sidecar_after_write=True
    )
    assert result.returncode == 2, result.stderr
    receipt_path = attempt_dir / "mocc-trace-pilot-receipt.json"
    sidecar_path = attempt_dir / "mocc-trace-pilot-receipt.sha256"
    assert sidecar_path.read_text(encoding="ascii").strip() == hashlib.sha256(
        receipt_path.read_bytes()
    ).hexdigest()
    assert not (attempt_dir / "job-result.json").exists()
    failure = (attempt_dir / "fragment-failure.txt").read_text(encoding="utf-8")
    assert failure == "2|job_result_report_binding|job result report binding failed\n"


def test_mocc_trace_binding_h1_rejects_sidecar_only_tamper(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, tamper_sidecar_after_write=True
    )
    assert result.returncode == 2, result.stderr
    receipt_path = attempt_dir / "mocc-trace-pilot-receipt.json"
    sidecar_path = attempt_dir / "mocc-trace-pilot-receipt.sha256"
    receipt_sha = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    tampered_sidecar_sha = sidecar_path.read_text(encoding="ascii").strip()
    assert re.fullmatch(r"[0-9a-f]{64}", tampered_sidecar_sha)
    assert tampered_sidecar_sha != receipt_sha
    assert not (attempt_dir / "job-result.json").exists()
    failure = (attempt_dir / "fragment-failure.txt").read_text(encoding="utf-8")
    assert failure == "2|job_result_report_binding|job result report binding failed\n"


def test_mocc_trace_binding_f4_rejects_receipt_replaced_after_shell_hash(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, tamper_receipt_after_shell_hash=True
    )
    assert result.returncode == 2, result.stderr
    assert (attempt_dir / "mocc-trace-pilot-receipt.json").is_file()
    assert (attempt_dir / "mocc-trace-pilot-receipt.sha256").is_file()
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


def test_mocc_trace_binding_uses_v4_pilot_and_v2_job_result_schemas(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(tmp_path)
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    job_result = _load_json(attempt_dir / "job-result.json")
    assert receipt["schema_version"] == "mocc-trace-pilot-receipt/v4"
    assert job_result["schema_version"] == "mocc-trace-pilot-job-result/v2"


def test_t1943_receipt_binds_trace_witness_discriminator_and_trace0_absence(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        trace_mode=1,
        t1943_g2=True,
    )
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    assert receipt["schema_version"] == "mocc-trace-pilot-receipt/t1943-g2-v2"
    binding = receipt["t1943_g2_discriminator"]
    assert (attempt_dir / "job-result.json").is_file()
    assert binding["instrumentation_patch"] == {
        "repo_path": "patches/instr-mocc-lock-coverage.patch",
        "sha256": hashlib.sha256(
            (tmp_path / "fixture-repo/patches/instr-mocc-lock-coverage.patch").read_bytes()
        ).hexdigest(),
        "touched_paths": ["cc/mocc/transaction.cc"],
        "patched_source_sha256": hashlib.sha256(
            (tmp_path / "build-source/cc/mocc/transaction.cc").read_bytes()
        ).hexdigest(),
        "trace0_built_from_patched_source": True,
    }
    for name in ("instr-patch.sha256", "instr-patch.numstat", "instr-patch-source.sha256",
                 "instr-patch-apply.stdout", "instr-patch-apply.stderr"):
        assert name in receipt["artifacts"].values()
    assert binding["discriminator_result"]["conclusion"] == "supported"
    for name, artifact in (
        ("trace-manifest.json", binding["trace_manifest"]),
        ("witness-manifest.json", binding["witness_manifest"]),
        (
            "trace0-watermark-absence.json",
            binding["trace0_watermark_absence"],
        ),
        ("discriminator.json", binding["discriminator_result"]),
    ):
        assert artifact["path"] == name
        assert artifact["sha256"] == hashlib.sha256(
            (attempt_dir / name).read_bytes()
        ).hexdigest()
    assert receipt["artifacts"]["submit_receipt_sha256"] == hashlib.sha256(
        (attempt_dir / "submit-receipt.json").read_bytes()
    ).hexdigest()
    assert receipt["source"]["outer_gitlink_advanced"] is False
    tools = receipt["correctness_tools"]
    assert set(tools) == {
        "trace0_preprocess_identity_checker",
        "verifier",
        "payload_discriminator",
    }
    assert receipt["gates"]["verifier_rc"] == "1"
    assert receipt["gates"]["discriminator_rc"] == "0"
    assert receipt["gates"]["discriminator_conclusion"] == "supported"


def test_t1943_receipt_rejects_trace0_binary_swap_after_absence(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        trace_mode=1,
        t1943_g2=True,
        tamper_trace0_binary_after_absence=True,
    )
    assert result.returncode == 2, result.stderr
    assert not (attempt_dir / "mocc-trace-pilot-receipt.json").exists()
    assert not (attempt_dir / "job-result.json").exists()


@pytest.mark.parametrize(
    "leaf_kind", ("trace", "witness", "trace-file-set", "witness-file-set")
)
def test_t1943_receipt_rejects_leaf_swap_after_discriminator(
    tmp_path: Path, leaf_kind: str
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        trace_mode=1,
        t1943_g2=True,
        tamper_manifest_leaf_after_discriminator=leaf_kind,
    )
    assert result.returncode == 2, result.stderr
    assert not (attempt_dir / "mocc-trace-pilot-receipt.json").exists()
    assert not (attempt_dir / "job-result.json").exists()


def test_mocc_trace_job_result_rejects_rebound_non_v4_receipt(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, tamper_schema_and_rebind_after_write=True
    )
    assert result.returncode == 2, result.stderr
    receipt_path = attempt_dir / "mocc-trace-pilot-receipt.json"
    sidecar_path = attempt_dir / "mocc-trace-pilot-receipt.sha256"
    receipt = _load_json(receipt_path)
    assert receipt["schema_version"] == "mocc-trace-pilot-receipt/v3"
    assert sidecar_path.read_text(encoding="ascii").strip() == hashlib.sha256(
        receipt_path.read_bytes()
    ).hexdigest()
    assert not (attempt_dir / "job-result.json").exists()
    failure = (attempt_dir / "fragment-failure.txt").read_text(encoding="utf-8")
    assert failure == "2|job_result_report_binding|job result report binding failed\n"


def test_t1943_job_result_rejects_rebound_v1_receipt(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, trace_mode=1, t1943_g2=True,
        tamper_schema_and_rebind_after_write=True,
        target_receipt_schema="mocc-trace-pilot-receipt/t1943-g2-v1",
    )
    assert result.returncode == 2, result.stderr
    receipt_path = attempt_dir / "mocc-trace-pilot-receipt.json"
    assert _load_json(receipt_path)["schema_version"] == "mocc-trace-pilot-receipt/t1943-g2-v1"
    assert (attempt_dir / "mocc-trace-pilot-receipt.sha256").read_text().strip() == hashlib.sha256(
        receipt_path.read_bytes()
    ).hexdigest()
    assert "exact admitted pilot receipt schema" in result.stderr
    assert not (attempt_dir / "job-result.json").exists()


def test_mocc_trace_job_result_accepts_exact_v4_receipt(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(tmp_path)
    assert result.returncode == 0, result.stderr
    receipt_path = attempt_dir / "mocc-trace-pilot-receipt.json"
    receipt = _load_json(receipt_path)
    job_result = _load_json(attempt_dir / "job-result.json")
    assert receipt["schema_version"] == "mocc-trace-pilot-receipt/v4"
    assert receipt["source"]["outer_gitlink_advanced"] is False
    assert "t1943_g2_discriminator" not in receipt
    assert "t1943_g2_discriminator" not in receipt["mocc_trace"]
    assert "submit_receipt_sha256" not in receipt["artifacts"]
    assert job_result["receipt_sha256"] == hashlib.sha256(
        receipt_path.read_bytes()
    ).hexdigest()
    assert not (attempt_dir / "fragment-failure.txt").exists()


def _nested_key_paths(
    value: object,
    key: str,
    path: tuple[str, ...] = (),
) -> list[tuple[str, ...]]:
    matches: list[tuple[str, ...]] = []
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            child_path = (*path, str(child_key))
            if child_key == key:
                matches.append(child_path)
            matches.extend(_nested_key_paths(child_value, key, child_path))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            matches.extend(
                _nested_key_paths(child_value, key, (*path, str(index)))
            )
    return matches


def test_mocc_trace_receipt_trace1_recursively_omits_performance_fields(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, trace_mode=1, report_mode="missing"
    )
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    for key in ("completed_txns", "elapsed_ns", "elapsed_s"):
        assert _nested_key_paths(receipt, key) == []


def test_mocc_trace_receipt_trace0_retains_performance_fields(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(tmp_path)
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    workload = receipt["workload"]
    assert isinstance(workload, dict)
    for key in ("completed_txns", "elapsed_ns", "elapsed_s"):
        assert key in workload
        assert _nested_key_paths(receipt, key) != []


def test_mocc_trace_receipt_binds_commit_count_witness(tmp_path: Path) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, trace_mode=1, report_mode="missing"
    )
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    artifacts = receipt["artifacts"]
    assert isinstance(artifacts, dict)
    assert artifacts["commit_count_json"] == "commit-count.json"
    assert artifacts["commit_count_sha256"] == hashlib.sha256(
        (attempt_dir / "commit-count.json").read_bytes()
    ).hexdigest()


def test_mocc_trace_receipt_binds_endpoint_consistency_with_residual_windows(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(tmp_path)
    assert result.returncode == 0, result.stderr
    source = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")["source"]
    assert isinstance(source, dict)
    state = source["judgment_source_state"]
    assert isinstance(state, dict)
    assert state["guarantee_name"] == "pre/post endpoint consistency"
    assert state["head_unchanged"] is True
    assert state["pre"]["head"] == state["post"]["head"]
    assert state["pre"]["clean"] is True
    assert state["post"]["clean"] is True
    for phase, name in (
        ("pre", "judgment-source-pre.json"),
        ("post", "judgment-source-post.json"),
    ):
        binding = state[phase]
        assert binding["capture_path"] == name
        assert binding["capture_sha256"] == hashlib.sha256(
            (attempt_dir / name).read_bytes()
        ).hexdigest()
    assert state["residual_windows"] == [
        "temporary source changes between captures can be missed",
        "source changes after the post_judgment capture can be missed",
    ]


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


@pytest.mark.parametrize(
    ("trace_mode", "artifact_name", "sha_field"),
    (
        (1, "verifier.json", "verifier_sha256"),
        (0, "throughput.json", "throughput_sha256"),
    ),
)
def test_mocc_trace_receipt_binds_mode_evidence_bytes(
    tmp_path: Path, trace_mode: int, artifact_name: str, sha_field: str
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, trace_mode=trace_mode, report_mode="missing" if trace_mode == 1 else "file"
    )
    assert result.returncode == 0, result.stderr
    receipt = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")
    artifacts = receipt["artifacts"]
    assert isinstance(artifacts, dict)
    assert artifacts[sha_field] == hashlib.sha256(
        (attempt_dir / artifact_name).read_bytes()
    ).hexdigest()


@pytest.mark.parametrize(
    ("trace_mode", "tool_key", "other_key"),
    (
        (1, "verifier", "trace0_preprocess_identity_checker"),
        (0, "trace0_preprocess_identity_checker", "verifier"),
    ),
)
def test_mocc_trace_receipt_records_executed_correctness_tool(
    tmp_path: Path, trace_mode: int, tool_key: str, other_key: str
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path, trace_mode=trace_mode, report_mode="missing" if trace_mode == 1 else "file"
    )
    assert result.returncode == 0, result.stderr
    tools = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")[
        "correctness_tools"
    ]
    assert isinstance(tools, dict)
    assert tools[other_key] is None
    bound = tools[tool_key]
    assert isinstance(bound, dict)
    path = Path(bound["path"])
    expected_path = (VERIFIER if trace_mode == 1 else CHECKER).resolve(strict=True)
    assert _production_selected_tool_path(
        "VERIFIER_TOOL_PATH" if trace_mode == 1 else "CHECKER_TOOL_PATH"
    ) == expected_path
    assert path == expected_path
    assert path.is_absolute()
    assert path.resolve(strict=True) == path
    assert bound["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_mocc_trace_binding_m19_globals_precede_receipt_writer() -> None:
    source = PILOT.read_text(encoding="utf-8")
    receipt_start = source.index(
        'python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json"'
    )
    lines = source.splitlines()
    for declaration in (
        'CHECKER_PY=""',
        'CHECKER_TOOL_PATH=""',
        'CHECKER_TOOL_SHA=""',
        'VERIFIER_PY=""',
        'VERIFIER_TOOL_PATH=""',
        'VERIFIER_TOOL_SHA=""',
        'CHECKER_REPORT_SHA=""',
    ):
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


def test_mocc_trace_binding_f6_receipt_lists_sha_sidecar_artifact(
    tmp_path: Path,
) -> None:
    result, attempt_dir, _ = _run_mocc_trace_finalization(tmp_path)
    assert result.returncode == 0, result.stderr
    artifacts = _load_json(attempt_dir / "mocc-trace-pilot-receipt.json")[
        "artifacts"
    ]
    assert isinstance(artifacts, dict)
    assert artifacts["receipt_sha256_sidecar"] == (
        "mocc-trace-pilot-receipt.sha256"
    )


def test_mocc_trace_binding_f7_synthetic_fixture_keys_match_checker_contract() -> None:
    checker_tree = ast.parse(CHECKER.read_text(encoding="utf-8"))
    check_functions = [
        node
        for node in checker_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "check"
    ]
    assert len(check_functions) == 1
    payload_returns = [
        node.value
        for node in ast.walk(check_functions[0])
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
    ]
    assert len(payload_returns) == 1
    checker_payload_keys = {
        key.value
        for key in payload_returns[0].keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    compiler_values = [
        value
        for key, value in zip(payload_returns[0].keys, payload_returns[0].values)
        if isinstance(key, ast.Constant) and key.value == "compiler"
    ]
    assert len(compiler_values) == 1
    assert isinstance(compiler_values[0], ast.Dict)
    checker_compiler_keys = {
        key.value
        for key in compiler_values[0].keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    fixture = _valid_trace0_report(Path("fixture-repo"), Path("fixture-cxx"))
    fixture_gate_keys = set(fixture)
    assert fixture_gate_keys == {
        "schema",
        "guarantee",
        "result",
        "old_oid",
        "new_oid",
        "repo",
        "compiler",
        "expected_paths",
    }
    assert fixture_gate_keys <= checker_payload_keys
    fixture_compiler = fixture["compiler"]
    assert isinstance(fixture_compiler, dict)
    assert set(fixture_compiler) == {"path", "version"}
    assert set(fixture_compiler) == checker_compiler_keys


def test_mocc_trace_binding_p01_accepts_synthetic_aligned_schema_v1_report(
    tmp_path: Path,
) -> None:
    """Accept a synthetic gate-aligned schema-v1 report fixture."""

    result, attempt_dir, _ = _run_mocc_trace_finalization(
        tmp_path,
        report_changes={"schema": "izanagi-trace0-preprocess-identity/v1"},
    )
    assert result.returncode == 0, result.stderr
    assert (attempt_dir / "mocc-trace-pilot-receipt.json").is_file()
    assert (attempt_dir / "job-result.json").is_file()


def test_mocc_trace_binding_p02_accepts_synthetic_aligned_schema_v2_realpath_report(
    tmp_path: Path,
) -> None:
    """Accept a synthetic gate-aligned schema-v2 report with realpath aliases."""

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
