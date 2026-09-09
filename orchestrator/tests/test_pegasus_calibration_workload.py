"""Calibration workload/protocol selection is bound, finite, and shell-valid."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign.genome import SPACES


ROOT = Path(__file__).resolve().parents[2]
SUBMIT = ROOT / "tools/pegasus/submit_certify.sh"
JOB = ROOT / "tools/pegasus/certify_calibration.sh"
COST_PROBE = ROOT / "tools/pegasus/probes/t1683_rr5_cost_probe.py"
README = ROOT / "tools/pegasus/README.md"
THIRD_PARTY_NAMES = ("masstree", "mimalloc", "googletest")


def _load_cost_probe():
    spec = importlib.util.spec_from_file_location(
        "t1683_rr5_cost_probe_test", COST_PROBE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_submitter_exposes_only_the_calibration_whitelist() -> None:
    source = SUBMIT.read_text(encoding="utf-8")

    assert "[--job-script PATH] [--rratio 20|50|80]" in source
    assert "[--protocol silo|mocc|tictoc]" in source
    assert 'RRATIO=50' in source
    assert 'PROTOCOL=silo' in source
    assert 'PROTOCOL_EXPLICIT=0' in source
    assert 'RRATIO" != "20"' in source
    assert 'RRATIO" != "50"' in source
    assert 'RRATIO" != "80"' in source
    assert 'PROTOCOL" != "silo"' in source
    assert 'PROTOCOL" != "mocc"' in source
    assert 'PROTOCOL" != "tictoc"' in source
    protocol_gate = source[
        source.index('if [[ "$PROTOCOL" != "silo"'):
        source.index("\nfi", source.index('if [[ "$PROTOCOL" != "silo"'))
    ]
    assert re.findall(r'\$PROTOCOL" != "([^"]+)"', protocol_gate) == [
        "silo", "mocc", "tictoc",
    ]
    assert "IZANAGI_CALIBRATION_RRATIO=$RRATIO" in source
    assert 'export_spec+=",IZANAGI_CALIBRATION_PROTOCOL=$PROTOCOL"' in source
    assert '"calibration_rratio": int(rratio)' in source
    assert '"calibration_protocol": protocol' in source
    assert '"protocol": request["calibration_protocol"]' in source
    assert '"ycsb_rratio": str(request["calibration_rratio"])' in source
    assert "':(exclude)output'" in source


def test_job_rechecks_the_submission_workload_and_records_it() -> None:
    source = JOB.read_text(encoding="utf-8")

    assert 'CALIBRATION_RRATIO="$IZANAGI_CALIBRATION_RRATIO"' in source
    assert 'CALIBRATION_PROTOCOL=${IZANAGI_CALIBRATION_PROTOCOL-silo}' in source
    assert '"calibration_rratio": (' in source
    assert '"calibration_protocol": doc.get("calibration", {}).get("protocol") == protocol' in source
    assert 'ycsb_rratio=$CALIBRATION_RRATIO' in source
    assert '"protocol": protocol' in source
    assert '"workload": {"ycsb_rratio": rratio}' in source
    assert "ycsb_rratio=50" not in source
    assert source.index("condition_gate_argv=") < source.index("build_argv=")
    assert "--macro BACKOFF_FIXED" in source
    assert "--stock-comparison" in source
    assert "--meaning-case=-1:branch:stock-adaptive-backoff" in source
    assert "--use-class certified-selection" in source
    assert "-DCCBENCH_BACKOFF_FIXED=-1" in source
    assert '"-DCMAKE_CXX_FLAGS=-DBACKOFF_FIXED=-1"' not in source


def _certify_protocol_define_table() -> dict[str, dict[str, str]]:
    """Parse the shell-owned protocol table; do not derive it from SPACES."""
    source = JOB.read_text(encoding="utf-8")
    match = re.search(
        r'^case "\$CALIBRATION_PROTOCOL" in\n(?P<body>.*?)^esac$',
        source,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    branches = re.findall(
        r"^  ([a-z0-9_]+)\)\n(.*?)^    ;;$",
        match.group("body"),
        re.MULTILINE | re.DOTALL,
    )
    assert {protocol for protocol, _body in branches} == {
        "silo", "mocc", "tictoc",
    }
    table: dict[str, dict[str, str]] = {}
    for protocol, body in branches:
        pairs = re.findall(
            r"^      -DCCBENCH_([A-Z0-9_]+)=([^\s]+)$", body, re.MULTILINE,
        )
        assert len(pairs) == body.count("-DCCBENCH_")
        assert len(pairs) == len(dict(pairs))
        table[protocol] = dict(pairs)
    return table


def _protocol_shell_observation(
    protocol: str,
    *,
    fetchcontent_base_dir: str = "/fixture/fetchcontent-base",
    fetchcontent_source_root: str = "/fixture/fetchcontent-src",
) -> dict[str, object]:
    source = JOB.read_text(encoding="utf-8")
    define_case_start = source.index('case "$CALIBRATION_PROTOCOL" in')
    define_case_end = (
        source.index("\nesac", define_case_start) + len("\nesac")
    )
    configure_start = source.index("configure_argv=(", define_case_end)
    configure_end = source.index("\n# The current CCBench pin", configure_start)
    gate_start = source.index(
        'if [[ "$CALIBRATION_PROTOCOL" == "silo" ]]', configure_end,
    )
    gate_end = source.index("\nfi", gate_start) + len("\nfi")
    build_case_start = source.index('case "$CALIBRATION_PROTOCOL" in', gate_end)
    build_case_end = source.index("\nesac", build_case_start) + len("\nesac")
    binary_match = re.search(r'^BINARY=.*$', source[build_case_end:], re.MULTILINE)
    assert binary_match is not None
    binary_line = binary_match.group(0)
    fragment = "\n".join((
        source[define_case_start:define_case_end],
        source[configure_start:configure_end],
        source[gate_start:gate_end],
        source[build_case_start:build_case_end],
        binary_line,
    ))
    command = f"""set -Eeuo pipefail
CALIBRATION_PROTOCOL={shlex.quote(protocol)}
CMAKE_PATH=/fixture/cmake
BUILD_SOURCE=/fixture/source
BUILD_DIR=/fixture/build
FETCHCONTENT_BASE_DIR={shlex.quote(fetchcontent_base_dir)}
FETCHCONTENT_SOURCE_ROOT={shlex.quote(fetchcontent_source_root)}
GFLAGS_INSTALL_DIR=/fixture/gflags
GLOG_INSTALL_DIR=/fixture/glog
GFLAGS_SOURCE_HEAD={'a' * 40}
GLOG_SOURCE_HEAD={'b' * 40}
CC_PATH=/bin/true
CXX_PATH=/bin/true
gate_calls=0
gate_configure_argv=()
run_condition_gate() {{
  gate_calls=$((gate_calls + 1))
  gate_configure_argv=("${{configure_argv[@]:5}}")
}}
{fragment}
printf 'gate=%s\n' "$gate_calls"
printf 'binary=%s\n' "$BINARY"
printf 'configure:'; printf ' %q' "${{configure_argv[@]}}"; printf '\n'
printf 'build:'; printf ' %q' "${{build_argv[@]}}"; printf '\n'
printf 'gate-configure:'
if (( ${{#gate_configure_argv[@]}} > 0 )); then
  printf ' %q' "${{gate_configure_argv[@]}}"
fi
printf '\n'
"""
    completed = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    lines = completed.stdout.splitlines()
    build_argv = shlex.split(lines[3].removeprefix("build:"))
    return {
        "gate_calls": int(lines[0].removeprefix("gate=")),
        "target": build_argv[build_argv.index("--target") + 1],
        "binary": lines[1].removeprefix("binary="),
        "configure_argv": shlex.split(lines[2].removeprefix("configure:")),
        "build_argv": build_argv,
        "gate_configure_argv": shlex.split(
            lines[4].removeprefix("gate-configure:"),
        ),
    }


def _calibrate_argv(binary: str) -> list[str]:
    source = JOB.read_text(encoding="utf-8")
    start = source.index("calibrate_argv=(")
    end = source.index("\n)", start) + len("\n)")
    assignment = source[start:end]
    binary_assignments = re.findall(
        r"(?<![A-Za-z0-9_])BINARY=", source[:start],
    )
    assert len(binary_assignments) == 1
    command = f"""set -Eeuo pipefail
CALIBRATE_PATH=/fixture/perf/bin:/usr/bin
CALIBRATE_PYTHON=/fixture/python3.10
REPO_ROOT=/fixture/repo
CALIBRATION_RRATIO=50
BINARY={shlex.quote(binary)}
BINARY_SHA={'c' * 64}
ATTEMPT_DIR=/fixture/attempt
{assignment}
printf 'calibrate:'; printf ' %q' "${{calibrate_argv[@]}}"; printf '\n'
"""
    completed = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return shlex.split(completed.stdout.removeprefix("calibrate:").strip())


def _offline_fetchcontent_tokens(
    *, source_root: Path | str, base_dir: Path | str,
) -> list[str]:
    return [
        f"-DFETCHCONTENT_BASE_DIR={base_dir}",
        "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={source_root}/masstree-src",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={source_root}/mimalloc-src",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={source_root}/googletest-src",
    ]


def _third_party_staging_root(repo_root: Path) -> Path:
    return (
        repo_root
        / "output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
    )


def _make_verified_third_party_fixture(
    tmp_path: Path, *, ignored_name: str | None = None,
) -> tuple[Path, Path]:
    fixture_repo = tmp_path / "repo"
    policy_path = fixture_repo / "tools/pegasus/policy.json"
    third_party_cmake = fixture_repo / "external/ccbench/cmake/ThirdParty.cmake"
    policy_path.parent.mkdir(parents=True)
    third_party_cmake.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "tools/pegasus/policy.json", policy_path)
    shutil.copy2(ROOT / "external/ccbench/cmake/ThirdParty.cmake", third_party_cmake)

    staging_root = _third_party_staging_root(fixture_repo)
    staging_root.mkdir(parents=True)
    heads: dict[str, str] = {}
    for name in THIRD_PARTY_NAMES:
        source = staging_root / name
        source.mkdir()
        (source / ".gitignore").write_text("ignored-artifact\n", encoding="utf-8")
        (source / "marker.txt").write_text(f"{name}-pristine\n", encoding="utf-8")
        (source / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.14)\n"
            f"project(fixture_{name} NONE)\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        subprocess.run(
            ["git", "-C", str(source), "config", "user.email", "fixture@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(source), "config", "user.name", "Fixture"],
            check=True,
        )
        subprocess.run(["git", "-C", str(source), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(source), "commit", "-qm", "fixture"], check=True,
        )
        heads[name] = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if name == ignored_name:
            (source / "ignored-artifact").write_text("dirty\n", encoding="utf-8")

    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    records = policy["silo_ladder_rung1"]["third_party_sources"]
    assert isinstance(records, list)
    records_by_name = {record["name"]: record for record in records}
    assert set(records_by_name) == set(THIRD_PARTY_NAMES)
    for name in THIRD_PARTY_NAMES:
        records_by_name[name]["pin"] = heads[name]
        for ref_key in ("ref", "declared_ref", "fetchcontent_ref", "tag"):
            if ref_key in records_by_name[name]:
                records_by_name[name][ref_key] = heads[name]
    policy_path.write_text(
        json.dumps(policy, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    cmake_text = third_party_cmake.read_text(encoding="utf-8")
    tag_variables = {
        "masstree": "CCBENCH_MASSTREE_TAG",
        "mimalloc": "CCBENCH_MIMALLOC_TAG",
        "googletest": "CCBENCH_GOOGLETEST_TAG",
    }
    for name, variable in tag_variables.items():
        cmake_text, count = re.subn(
            rf'(set\({variable}\s+")[^"]+("\))',
            rf"\g<1>{heads[name]}\g<2>",
            cmake_text,
        )
        assert count == 1
    third_party_cmake.write_text(cmake_text, encoding="utf-8")
    return fixture_repo, staging_root


def _job_copy_fragment() -> str:
    source = JOB.read_text(encoding="utf-8")
    anchor = "# (iv-c) pinned-clean CCBench + /scr の fresh worktree/build。"
    start = source.index(anchor) + len(anchor)
    end = source.index("\nCCBENCH_BASE=", start)
    return source[start:end]


def _run_job_copy_fragment(
    *, repo_root: Path, staging_root: Path, scratch_root: Path,
) -> tuple[subprocess.CompletedProcess[str], Path | None, Path | None]:
    attempt_dir = scratch_root / "attempt"
    command = f"""set -Eeuo pipefail
REPO_ROOT={shlex.quote(str(repo_root))}
TMPDIR={shlex.quote(str(scratch_root))}
THIRD_PARTY_SOURCE_ROOT={shlex.quote(str(staging_root))}
ATTEMPT_DIR={shlex.quote(str(attempt_dir))}
mkdir -p "$ATTEMPT_DIR"
write_failure() {{ printf 'failure:%s:%s\n' "$2" "$3" >&2; }}
{_job_copy_fragment()}
printf 'source-root=%s\n' "$FETCHCONTENT_SOURCE_ROOT"
printf 'base-dir=%s\n' "$FETCHCONTENT_BASE_DIR"
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    completed = subprocess.run(
        ["bash", "-c", command],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        verifier_stderr = attempt_dir / "third-party-source-verify.stderr"
        if verifier_stderr.is_file():
            completed.stderr += verifier_stderr.read_text(
                encoding="utf-8", errors="replace",
            )
        return completed, None, None
    values = dict(line.split("=", 1) for line in completed.stdout.splitlines())
    return completed, Path(values["source-root"]), Path(values["base-dir"])


def _job_third_party_precheck() -> str:
    source = JOB.read_text(encoding="utf-8")
    protocol_gate = source.index(
        'if [[ "$CALIBRATION_PROTOCOL" != "silo"',
    )
    start = source.index("THIRD_PARTY_SOURCE_ROOT=", protocol_gate)
    end = source.index(
        'if [[ -n "${PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT+x}"', start,
    )
    return source[start:end]


def _run_job_third_party_precheck(repo_root: Path) -> subprocess.CompletedProcess[str]:
    command = f"""set -Eeuo pipefail
REPO_ROOT={shlex.quote(str(repo_root))}
write_failure() {{ printf 'failure:%s:%s\n' "$2" "$3" >&2; }}
{_job_third_party_precheck()}
"""
    return subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, check=False,
    )


def test_certify_shell_protocol_axes_match_independent_genome_spaces() -> None:
    table = _certify_protocol_define_table()
    for protocol in ("silo", "mocc", "tictoc"):
        assert table[protocol]["TRACE"] == "0"
        excluded = {"TRACE"}
        if protocol == "silo":
            excluded.add("BACKOFF_FIXED")
        assert set(table[protocol]) - excluded == set(SPACES[protocol].axes)


def test_certify_shell_protocol_defines_match_exact_values() -> None:
    assert _certify_protocol_define_table() == {
        "silo": {
            "TRACE": "0",
            "BACK_OFF": "0",
            "BACKOFF_FIXED": "-1",
            "NO_WAIT_LOCKING_IN_VALIDATION": "1",
            "NO_WAIT_OF_TICTOC": "0",
            "WAL": "0",
        },
        "mocc": {
            "TRACE": "0",
            "BACK_OFF": "1",
            "KEY_SORT": "0",
            "TEMPERATURE_RESET_OPT": "1",
        },
        "tictoc": {
            "TRACE": "0",
            "BACK_OFF": "1",
            "NO_WAIT_LOCKING_IN_VALIDATION": "1",
            "NO_WAIT_OF_TICTOC": "0",
            "PREEMPTIVE_ABORTS": "1",
            "TIMESTAMP_HISTORY": "1",
        },
    }


def test_certify_shell_protocol_axis_values_satisfy_genome_spaces() -> None:
    table = _certify_protocol_define_table()
    for protocol in ("silo", "mocc", "tictoc"):
        excluded = {"TRACE"}
        if protocol == "silo":
            excluded.add("BACKOFF_FIXED")
        shell_axis_assignment = {
            name: int(value)
            for name, value in table[protocol].items()
            if name not in excluded
        }
        assert any(
            genome.flags == shell_axis_assignment
            for genome in SPACES[protocol].enumerate()
        )


@pytest.mark.parametrize("protocol", ["mocc", "tictoc"])
def test_certify_non_silo_defines_contain_no_axis_outsider(protocol: str) -> None:
    defines = set(_certify_protocol_define_table()[protocol])
    assert defines == {"TRACE", *SPACES[protocol].axes}
    configure_defines = {
        argument.removeprefix("-DCCBENCH_").split("=", 1)[0]
        for argument in _protocol_shell_observation(protocol)["configure_argv"]
        if argument.startswith("-DCCBENCH_")
    }
    assert configure_defines == defines
    assert "BACKOFF_FIXED" not in defines
    if protocol == "mocc":
        assert "WAL" not in defines
        assert "NO_WAIT_LOCKING_IN_VALIDATION" not in defines


@pytest.mark.parametrize("protocol", ["silo", "mocc", "tictoc"])
def test_certify_derives_protocol_target_and_binary_path(protocol: str) -> None:
    observed = _protocol_shell_observation(protocol)
    target = f"ycsb_{protocol}.exe"
    assert observed["target"] == target
    assert observed["binary"] == f"/fixture/build/cc/{protocol}/{target}"
    assert observed["build_argv"] == [
        "/fixture/cmake", "--build", "/fixture/build", "--target", target,
        "-j", "48",
    ]
    source = JOB.read_text(encoding="utf-8")
    assert "cc/silo" not in source
    build_case_start = source.index(
        'case "$CALIBRATION_PROTOCOL" in',
        source.index('case "$CALIBRATION_PROTOCOL" in') + 1,
    )
    build_case_end = source.index("\nesac", build_case_start)
    build_case = source[build_case_start:build_case_end]
    branches = dict(re.findall(
        r"^  (silo|mocc|tictoc)\)\s+build_argv=\((.*?)\)\s+;;$",
        build_case,
        re.MULTILINE,
    ))
    assert set(branches) == {"silo", "mocc", "tictoc"}
    for branch_protocol, branch in branches.items():
        branch_targets = re.findall(r"\bycsb_[A-Za-z0-9_.-]+", branch)
        assert branch_targets == [f"ycsb_{branch_protocol}.exe"]


@pytest.mark.parametrize("protocol", ["silo", "mocc", "tictoc"])
def test_certify_final_calibrate_binary_matches_built_binary(protocol: str) -> None:
    observed = _protocol_shell_observation(protocol)
    binary = observed["binary"]
    assert isinstance(binary, str)
    calibrate_argv = _calibrate_argv(binary)
    assert calibrate_argv[calibrate_argv.index("--binary") + 1] == binary


def test_certify_keeps_backoff_fixed_and_condition_gate_silo_only() -> None:
    table = _certify_protocol_define_table()
    assert table["silo"]["BACKOFF_FIXED"] == "-1"
    for protocol in ("mocc", "tictoc"):
        assert "BACKOFF_FIXED" not in table[protocol]
    assert _protocol_shell_observation("silo")["gate_calls"] == 1
    assert _protocol_shell_observation("mocc")["gate_calls"] == 0
    assert _protocol_shell_observation("tictoc")["gate_calls"] == 0
    source = JOB.read_text(encoding="utf-8")
    assert len(re.findall(r"(?m)^[ \t]*run_condition_gate[ \t]*$", source)) == 1


def test_default_silo_build_and_calibrate_argv_match_offline_contract() -> None:
    observed = _protocol_shell_observation("silo")
    true_path = str(Path("/bin/true").resolve())
    assert observed["configure_argv"] == [
        "/fixture/cmake", "-S", "/fixture/source", "-B", "/fixture/build",
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
        "-DFETCHCONTENT_BASE_DIR=/fixture/fetchcontent-base",
        "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
        "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=/fixture/fetchcontent-src/masstree-src",
        "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=/fixture/fetchcontent-src/mimalloc-src",
        "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/fixture/fetchcontent-src/googletest-src",
        "-DCCBENCH_TRACE=0", "-DCCBENCH_BACK_OFF=0",
        "-DCCBENCH_BACKOFF_FIXED=-1",
        "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
        "-DCCBENCH_NO_WAIT_OF_TICTOC=0", "-DCCBENCH_WAL=0",
        "-DCMAKE_PREFIX_PATH=/fixture/gflags;/fixture/glog",
        f"-DIZANAGI_GFLAGS_SRC_HEAD={'a' * 40}",
        f"-DIZANAGI_GLOG_SRC_HEAD={'b' * 40}",
        f"-DCMAKE_C_COMPILER={true_path}",
        f"-DCMAKE_CXX_COMPILER={true_path}",
    ]
    assert observed["build_argv"] == [
        "/fixture/cmake", "--build", "/fixture/build", "--target",
        "ycsb_silo.exe", "-j", "48",
    ]
    assert _calibrate_argv("/fixture/build/cc/silo/ycsb_silo.exe") == [
        "env", "PATH=/fixture/perf/bin:/usr/bin", "/fixture/python3.10",
        "/fixture/repo/orchestrator/calibrate.py", "--certify", "--env-tag",
        "pegasus", "--threads", "48", "--workload",
        "ycsb_zipf_skew=0.9,ycsb_rratio=50,ycsb_rmw=0", "--binary",
        "/fixture/build/cc/silo/ycsb_silo.exe", "--binary-sha256", "c" * 64,
        "--receipt-json", "/fixture/attempt/acquisition-receipt.json",
    ]


def test_certify_offline_fetchcontent_contract_is_identical_for_all_protocols() -> None:
    expected = _offline_fetchcontent_tokens(
        source_root="/fixture/fetchcontent-src",
        base_dir="/fixture/fetchcontent-base",
    )
    assert "for third_party_name in masstree mimalloc googletest; do" in (
        _job_copy_fragment()
    )
    for protocol in ("silo", "mocc", "tictoc"):
        observed = _protocol_shell_observation(protocol)
        assert [
            argument for argument in observed["configure_argv"]
            if argument.startswith("-DFETCHCONTENT_")
        ] == expected


def test_certify_condition_gate_receives_the_same_fetchcontent_tokens() -> None:
    expected = _offline_fetchcontent_tokens(
        source_root="/fixture/fetchcontent-src",
        base_dir="/fixture/fetchcontent-base",
    )
    silo = _protocol_shell_observation("silo")
    assert [
        argument for argument in silo["gate_configure_argv"]
        if argument.startswith("-DFETCHCONTENT_")
    ] == expected
    for protocol in ("mocc", "tictoc"):
        observed = _protocol_shell_observation(protocol)
        assert observed["gate_calls"] == 0
        assert observed["gate_configure_argv"] == []


def test_certify_offline_configure_resolves_three_local_sources_and_fails_without_each(
    tmp_path: Path,
) -> None:
    cmake = shutil.which("cmake")
    timeout_command = shutil.which("timeout")
    assert cmake is not None
    assert timeout_command is not None
    fixture_repo, staging_root = _make_verified_third_party_fixture(tmp_path)
    project = tmp_path / "cmake-project"
    project.mkdir()
    (project / "CMakeLists.txt").write_text(
        """cmake_minimum_required(VERSION 3.14)
project(offline_fetchcontent_contract NONE)
include(FetchContent)
if(NOT FETCHCONTENT_FULLY_DISCONNECTED)
  FetchContent_Declare(
    offline_connectivity_probe
    URL "https://offline-connectivity-probe.invalid/source.tar.gz"
  )
  FetchContent_MakeAvailable(offline_connectivity_probe)
endif()
foreach(dependency IN ITEMS masstree mimalloc googletest)
  FetchContent_Declare(
    ${dependency}
    URL "https://${dependency}.offline.invalid/source.tar.gz"
  )
  FetchContent_MakeAvailable(${dependency})
  FetchContent_GetProperties(${dependency})
  set(source_variable "${dependency}_SOURCE_DIR")
  set(resolved_source "${${source_variable}}")
  if(NOT EXISTS "${resolved_source}/CMakeLists.txt")
    message(FATAL_ERROR "${dependency} did not resolve to a local source")
  endif()
  file(WRITE "${CMAKE_BINARY_DIR}/resolved-${dependency}.txt" "${resolved_source}")
endforeach()
""",
        encoding="utf-8",
    )

    def run_configure(label: str, *, omitted_prefix: str | None = None) -> tuple[
        subprocess.CompletedProcess[str], Path, Path, Path,
    ]:
        scratch = tmp_path / f"scratch-{label}"
        copied, source_root, base_dir = _run_job_copy_fragment(
            repo_root=fixture_repo,
            staging_root=staging_root,
            scratch_root=scratch,
        )
        assert copied.returncode == 0, copied.stderr
        assert source_root is not None and base_dir is not None
        observed = _protocol_shell_observation(
            "mocc",
            fetchcontent_base_dir=str(base_dir),
            fetchcontent_source_root=str(source_root),
        )
        tokens = [
            argument for argument in observed["configure_argv"]
            if argument.startswith("-DFETCHCONTENT_")
        ]
        assert tokens == _offline_fetchcontent_tokens(
            source_root=source_root, base_dir=base_dir,
        )
        if omitted_prefix is not None:
            tokens = [
                argument for argument in tokens
                if not argument.startswith(omitted_prefix)
            ]
        build_dir = tmp_path / f"build-{label}"
        completed = subprocess.run(
            [
                timeout_command, "--kill-after=2", "5",
                cmake, "-S", str(project), "-B", str(build_dir), *tokens,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return completed, source_root, base_dir, build_dir

    positive, source_root, base_dir, build_dir = run_configure("positive")
    assert source_root != base_dir
    assert positive.returncode == 0, positive.stdout + positive.stderr
    for name in THIRD_PARTY_NAMES:
        resolved = (build_dir / f"resolved-{name}.txt").read_text(encoding="utf-8")
        assert Path(resolved).resolve() == (source_root / f"{name}-src").resolve()

    missing_tokens = (
        "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
        "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
        "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=",
        "-DFETCHCONTENT_FULLY_DISCONNECTED=",
    )
    for index, prefix in enumerate(missing_tokens):
        negative, _source_root, _base_dir, _build_dir = run_configure(
            f"negative-{index}", omitted_prefix=prefix,
        )
        assert negative.returncode != 0, prefix

    coupled_base = tmp_path / "coupled-base"
    coupled_base.mkdir()
    for name in THIRD_PARTY_NAMES:
        shutil.copytree(staging_root / name, coupled_base / f"{name}-src")
    coupled_tokens = _offline_fetchcontent_tokens(
        source_root=coupled_base, base_dir=coupled_base,
    )
    coupled_tokens = [
        argument for argument in coupled_tokens
        if not argument.startswith("-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=")
    ]
    coupled_build = tmp_path / "build-coupled-control"
    coupled = subprocess.run(
        [
            timeout_command, "--kill-after=2", "5",
            cmake, "-S", str(project), "-B", str(coupled_build), *coupled_tokens,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert coupled.returncode == 0, coupled.stdout + coupled.stderr
    coupled_mimalloc = (coupled_build / "resolved-mimalloc.txt").read_text(
        encoding="utf-8",
    )
    assert Path(coupled_mimalloc).resolve() == (coupled_base / "mimalloc-src").resolve()


def test_certify_job_copy_leaves_the_staging_sources_untouched_and_writable(
    tmp_path: Path,
) -> None:
    fixture_repo, staging_root = _make_verified_third_party_fixture(tmp_path)
    before = {
        name: (
            (staging_root / name / "marker.txt").read_bytes(),
            (staging_root / name / "marker.txt").stat().st_ino,
        )
        for name in THIRD_PARTY_NAMES
    }
    completed, source_root, base_dir = _run_job_copy_fragment(
        repo_root=fixture_repo,
        staging_root=staging_root,
        scratch_root=tmp_path / "scratch-copy",
    )
    assert completed.returncode == 0, completed.stderr
    assert source_root is not None and base_dir is not None
    assert source_root != base_dir
    for name in THIRD_PARTY_NAMES:
        upstream_marker = staging_root / name / "marker.txt"
        copied_marker = source_root / f"{name}-src" / "marker.txt"
        assert copied_marker.stat().st_ino != before[name][1]
        copied_marker.write_text(f"{name}-job-write\n", encoding="utf-8")
        assert upstream_marker.read_bytes() == before[name][0]
        assert upstream_marker.stat().st_ino == before[name][1]


def test_certify_job_rejects_a_staging_source_with_ignored_artifacts(
    tmp_path: Path,
) -> None:
    fixture_repo, staging_root = _make_verified_third_party_fixture(
        tmp_path, ignored_name="mimalloc",
    )
    completed, source_root, base_dir = _run_job_copy_fragment(
        repo_root=fixture_repo,
        staging_root=staging_root,
        scratch_root=tmp_path / "scratch-dirty",
    )
    assert completed.returncode == 2
    assert source_root is None and base_dir is None
    assert "failure:third_party_source:" in completed.stderr
    assert "pinned-pristine" in completed.stderr


def test_submitter_rejects_a_missing_or_malformed_third_party_staging_root(
    tmp_path: Path,
) -> None:
    submit_source = SUBMIT.read_text(encoding="utf-8")
    precheck_start = submit_source.index("THIRD_PARTY_SOURCE_ROOT=")
    precheck_end = submit_source.index('\nif [[ ! -f "$JOB_SCRIPT"', precheck_start)
    submit_precheck = submit_source[precheck_start:precheck_end]
    assert "silo_ladder_rung1/job-staging/thirdparty-src" in submit_precheck
    assert "git" not in submit_precheck
    assert "clone" not in submit_precheck
    assert "hydrate" not in submit_precheck

    malformed_repos: list[Path] = []

    missing_repo = tmp_path / "missing-repo"
    missing_repo.mkdir()
    malformed_repos.append(missing_repo)

    root_symlink_repo = tmp_path / "root-symlink-repo"
    root_symlink_repo.mkdir()
    root_symlink = _third_party_staging_root(root_symlink_repo)
    root_symlink.parent.mkdir(parents=True)
    root_symlink_target = tmp_path / "root-symlink-target"
    root_symlink_target.mkdir()
    for name in THIRD_PARTY_NAMES:
        (root_symlink_target / name).mkdir()
    root_symlink.symlink_to(root_symlink_target, target_is_directory=True)
    malformed_repos.append(root_symlink_repo)

    missing_child_repo = tmp_path / "missing-child-repo"
    missing_child_repo.mkdir()
    missing_child_root = _third_party_staging_root(missing_child_repo)
    missing_child_root.mkdir(parents=True)
    for name in ("masstree", "mimalloc"):
        (missing_child_root / name).mkdir()
    malformed_repos.append(missing_child_repo)

    child_symlink_repo = tmp_path / "child-symlink-repo"
    child_symlink_repo.mkdir()
    child_symlink_root = _third_party_staging_root(child_symlink_repo)
    child_symlink_root.mkdir(parents=True)
    child_target = tmp_path / "child-symlink-target"
    child_target.mkdir()
    for name in ("masstree", "mimalloc"):
        (child_symlink_root / name).mkdir()
    (child_symlink_root / "googletest").symlink_to(
        child_target, target_is_directory=True,
    )
    malformed_repos.append(child_symlink_repo)

    for repo_root in malformed_repos:
        completed = subprocess.run(
            [
                str(SUBMIT), "--repo-root", str(repo_root),
                "--job-script", str(repo_root / "missing-job.sh"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 2
        assert "pinned third-party staging" in completed.stderr

        job_completed = _run_job_third_party_precheck(repo_root)
        assert job_completed.returncode == 2
        assert "failure:third_party_source:" in job_completed.stderr

    valid_repo = tmp_path / "valid-repo"
    valid_repo.mkdir()
    valid_root = _third_party_staging_root(valid_repo)
    valid_root.mkdir(parents=True)
    for name in THIRD_PARTY_NAMES:
        (valid_root / name).mkdir()
    assert _run_job_third_party_precheck(valid_repo).returncode == 0


def test_calibration_shell_scripts_parse() -> None:
    for script in (SUBMIT, JOB):
        completed = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def test_cost_probe_condition_gate_dominates_first_buildcache_call() -> None:
    source = COST_PROBE.read_text(encoding="utf-8")
    main = source[source.index("def main()") :]
    assert main.index("_require_condition_gates") < main.index("buildcache.build(")
    assert 'int(adopted["BACKOFF_NOINLINE"])' in source


def test_cost_probe_requests_every_genome_value_and_inert_witness() -> None:
    probe = _load_cost_probe()
    for workload_id in ("rr5", "rr50"):
        workload = probe._load_workload(workload_id)
        cells = probe._condition_requests_by_genome(workload)
        assert [name for name, _defines, _requests in cells] == [
            name for name, _defines in workload["genomes"]
        ]
        assert {
            (name, request.macro, request.requested_value)
            for name, _defines, requests in cells
            for request, _declaration in requests
        } == {
            (name, macro, int(defines[macro]))
            for name, defines in workload["genomes"]
            for macro in ("BACKOFF_FIXED", "BACKOFF_NOINLINE")
        }
        stock_requests = {
            request.macro: (request, declaration)
            for name, _defines, requests in cells if name.endswith("-stock")
            for request, declaration in requests
        }
        assert stock_requests["BACKOFF_FIXED"][0].stock_comparison is True
        assert stock_requests["BACKOFF_FIXED"][1] is not None
        assert stock_requests["BACKOFF_NOINLINE"][0].stock_comparison is True


def test_cost_probe_uses_factory_noinline_and_legacy_backoff_declarations() -> None:
    probe = _load_cost_probe()
    workload = {
        "genomes": [(
            "synthetic-stock",
            {"BACKOFF_FIXED": -1, "BACKOFF_NOINLINE": 0},
        )],
    }

    cells = probe._condition_requests_by_genome(workload)
    requests = {
        request.macro: (request, declaration)
        for _name, _defines, rows in cells
        for request, declaration in rows
    }
    noinline_request, noinline_declaration = requests["BACKOFF_NOINLINE"]
    fixed_request, fixed_declaration = requests["BACKOFF_FIXED"]

    assert type(noinline_declaration) is (
        probe.condition_meaning_gate.ConditionalBranchMeaningDeclaration
    )
    assert noinline_declaration == (
        probe.condition_meaning_gate.declare_define_runtime_meaning(
            noinline_request,
        )
    )
    assert fixed_request.requested_value == -1
    assert type(fixed_declaration) is (
        probe.condition_meaning_gate.MeaningWitnessDeclaration
    )
    assert fixed_declaration.cases[0].expected_selected_branch == (
        probe.condition_meaning_gate.STOCK_ADAPTIVE_BRANCH
    )


def test_submitter_rejects_an_unregistered_ratio_before_side_effects(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            str(SUBMIT),
            "--rratio",
            "95",
            "--attempts-root",
            str(tmp_path / "attempts"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "--rratio must be exactly 20, 50, or 80" in completed.stderr
    assert not (tmp_path / "attempts").exists()


@pytest.mark.parametrize("protocol", ["cicada", "ermia"])
def test_submitter_rejects_unregistered_protocol_before_side_effects(
    tmp_path: Path, protocol: str,
) -> None:
    attempts = tmp_path / "attempts"
    completed = subprocess.run(
        [str(SUBMIT), "--protocol", protocol, "--attempts-root", str(attempts)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "--protocol must be exactly silo, mocc, or tictoc" in completed.stderr
    assert not attempts.exists()


def _run_submit_dry_run_in_clean_fixture(
    tmp_path: Path,
    *,
    protocol: str | None = None,
) -> tuple[Path, Path, Path, list[str]]:
    fixture_repo = tmp_path / "repo"
    fixture_tools = fixture_repo / "tools" / "pegasus"
    fixture_tools.parent.mkdir(parents=True)
    shutil.copytree(
        ROOT / "tools" / "pegasus",
        fixture_tools,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    subprocess.run(["git", "init", "-q", str(fixture_repo)], check=True)
    subprocess.run(
        ["git", "-C", str(fixture_repo), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(fixture_repo), "config", "user.name", "Fixture"],
        check=True,
    )
    subprocess.run(["git", "-C", str(fixture_repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(fixture_repo), "commit", "-qm", "fixture"],
        check=True,
    )
    staging_root = _third_party_staging_root(fixture_repo)
    staging_root.mkdir(parents=True)
    for name in THIRD_PARTY_NAMES:
        (staging_root / name).mkdir()

    command = [
        "bash",
        str(fixture_tools / "submit_certify.sh"),
        "--repo-root",
        str(fixture_repo),
        "--attempts-root",
        str(tmp_path / "attempts"),
        "--dry-run",
    ]
    if protocol is not None:
        command.extend(["--protocol", protocol])
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    command_lines = [
        line for line in completed.stdout.splitlines()
        if line.startswith("qsub command:")
    ]
    assert len(command_lines) == 1
    qsub_argv = shlex.split(command_lines[0].removeprefix("qsub command:"))

    git_common_dir = Path(subprocess.run(
        [
            "git",
            "-C",
            str(fixture_repo),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip())
    expected_root = (
        git_common_dir.parent.parent
        / "izanagi-job-evidence"
        / "calibration-certify"
    )
    return fixture_repo, git_common_dir.parent, expected_root, qsub_argv


@pytest.mark.parametrize("protocol", ["silo", "mocc", "tictoc"])
def test_submitter_accepts_exact_protocol_whitelist_and_records_it(
    tmp_path: Path, protocol: str,
) -> None:
    _repo, _common, _output, qsub_argv = _run_submit_dry_run_in_clean_fixture(
        tmp_path, protocol=protocol,
    )
    submissions = list((tmp_path / "attempts" / "submissions").iterdir())
    assert len(submissions) == 1
    pre_submit = json.loads(
        (submissions[0] / "pre-submit.json").read_text(encoding="utf-8"),
    )
    receipt = json.loads(
        (submissions[0] / "submit-receipt.json").read_text(encoding="utf-8"),
    )
    assert pre_submit["request"]["calibration_protocol"] == protocol
    assert receipt["calibration"]["protocol"] == protocol
    export_spec = qsub_argv[qsub_argv.index("-v") + 1]
    nonce = submissions[0].name
    assert export_spec == (
        f"IZANAGI_SUBMISSION_NONCE={nonce},IZANAGI_CALIBRATION_RRATIO=50,"
        f"IZANAGI_CALIBRATION_PROTOCOL={protocol}"
    )


def test_submitter_omitted_protocol_is_silo_without_changing_qsub_argv(
    tmp_path: Path,
) -> None:
    fixture_repo, _common, expected_root, qsub_argv = (
        _run_submit_dry_run_in_clean_fixture(tmp_path)
    )
    submissions = list((tmp_path / "attempts" / "submissions").iterdir())
    assert len(submissions) == 1
    nonce = submissions[0].name
    pre_submit = json.loads(
        (submissions[0] / "pre-submit.json").read_text(encoding="utf-8"),
    )
    receipt = json.loads(
        (submissions[0] / "submit-receipt.json").read_text(encoding="utf-8"),
    )
    assert pre_submit["request"]["calibration_protocol"] == "silo"
    assert receipt["calibration"]["protocol"] == "silo"
    assert qsub_argv == [
        "qsub", "-o", str(expected_root / f"{nonce}.scheduler.stdout"),
        "-e", str(expected_root / f"{nonce}.scheduler.stderr"),
        "-v", (
            f"IZANAGI_SUBMISSION_NONCE={nonce},"
            "IZANAGI_CALIBRATION_RRATIO=50"
        ),
        str(fixture_repo / "tools/pegasus/certify_calibration.sh"),
    ]


def test_submit_dry_run_passes_scheduler_file_paths_to_qsub(tmp_path: Path) -> None:
    _fixture_repo, _git_common_repo, expected_root, qsub_argv = (
        _run_submit_dry_run_in_clean_fixture(tmp_path)
    )

    assert qsub_argv[0] == "qsub"
    assert "-o" in qsub_argv
    assert "-e" in qsub_argv
    stdout_path = Path(qsub_argv[qsub_argv.index("-o") + 1])
    stderr_path = Path(qsub_argv[qsub_argv.index("-e") + 1])
    assert stdout_path.is_absolute()
    assert stderr_path.is_absolute()

    stdout_name = re.fullmatch(r"([0-9a-f]{32})\.scheduler\.stdout", stdout_path.name)
    stderr_name = re.fullmatch(r"([0-9a-f]{32})\.scheduler\.stderr", stderr_path.name)
    assert stdout_name is not None
    assert stderr_name is not None
    assert stdout_name.group(1) == stderr_name.group(1)
    assert stdout_path != expected_root
    assert stderr_path != expected_root
    assert stdout_path.parent == expected_root
    assert stderr_path.parent == expected_root
    assert expected_root.is_dir()


def test_submit_dry_run_keeps_scheduler_output_outside_the_repository(tmp_path: Path) -> None:
    """受理: 返り先が repo の外なら検査は通り、qsub argv はそのまま構築される。

    拒否: 返り先が repo root 自身またはその配下へ動いた瞬間、この検査は赤になる。
    """
    fixture_repo, git_common_repo, _expected_root, qsub_argv = (
        _run_submit_dry_run_in_clean_fixture(tmp_path)
    )

    assert "-o" in qsub_argv
    assert "-e" in qsub_argv
    stdout_path = Path(qsub_argv[qsub_argv.index("-o") + 1])
    stderr_path = Path(qsub_argv[qsub_argv.index("-e") + 1])
    for output_path in (stdout_path, stderr_path):
        assert output_path != fixture_repo
        assert fixture_repo not in output_path.parents
        assert output_path != git_common_repo
        assert git_common_repo not in output_path.parents


def test_runbook_shows_ai_driven_h1_h2_submission_path() -> None:
    source = README.read_text(encoding="utf-8")

    assert "submit_certify.sh --rratio 80" in source
    assert "submit_certify.sh --rratio 20" in source
    assert "--protocol mocc" in source
    assert "silo / mocc / tictoc" in source
    assert "INLINE_VERSION_OPT" in source
    assert "BACKOFF_FIXED" in source
    assert "人間が JSON を編集・登録する必要はなく" in source
