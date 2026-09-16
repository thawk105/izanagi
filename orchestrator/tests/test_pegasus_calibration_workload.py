"""Calibration workload/protocol selection is bound, finite, and shell-valid."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Mapping

import pytest

from orchestrator.calibrator.cli import (
    CertificationError,
    _canonical_genome_from_receipt,
)
from orchestrator.campaign import source_digest
from orchestrator.campaign.genome import SPACES
from orchestrator.campaign.model import (
    GENOME_AXIS_CMAKE_CACHE_VARIABLES,
    Genome,
    cmake_cache_variable_for_axis,
    genome_axis_from_cmake_cache_variable,
)


ROOT = Path(__file__).resolve().parents[2]
SUBMIT = ROOT / "tools/pegasus/submit_certify.sh"
JOB = ROOT / "tools/pegasus/certify_calibration.sh"
COST_PROBE = ROOT / "tools/pegasus/probes/t1683_rr5_cost_probe.py"
README = ROOT / "tools/pegasus/README.md"
CCBENCH_ROOT = ROOT / "external/ccbench"
THIRD_PARTY_NAMES = ("masstree", "mimalloc", "googletest")


def _ccbench_axis_cache_table(
    ccbench_root: Path,
) -> dict[tuple[str, str], str]:
    """Read the independent CCBench macro-to-cache mapping with its parser."""
    options_text = (ccbench_root / "cmake/Options.cmake").read_text(
        encoding="utf-8",
    )
    table: dict[tuple[str, str], str] = {}
    for protocol, space in SPACES.items():
        protocol_cmake_text = (
            ccbench_root / f"cc/{protocol}/CMakeLists.txt"
        ).read_text(encoding="utf-8")
        supplied, bare, cache_by_macro = (
            source_digest._parse_supplied_macro_details(
                options_text, protocol_cmake_text,
            )
        )
        for axis in space.axes:
            assert axis in supplied
            assert axis not in bare
            cache_name = cache_by_macro.get(axis)
            assert cache_name is not None
            table[(protocol, axis)] = f"CCBENCH_{cache_name}"
    return table


def _assert_axis_cache_table_matches_ccbench(
    ccbench_root: Path,
    declared: Mapping[tuple[str, str], str],
) -> None:
    assert _ccbench_axis_cache_table(ccbench_root) == dict(declared)


def _copy_ccbench_axis_cache_sources(destination: Path) -> Path:
    fixture_root = destination / "ccbench"
    options_target = fixture_root / "cmake/Options.cmake"
    options_target.parent.mkdir(parents=True)
    shutil.copy2(CCBENCH_ROOT / "cmake/Options.cmake", options_target)
    for protocol in SPACES:
        protocol_target = fixture_root / f"cc/{protocol}/CMakeLists.txt"
        protocol_target.parent.mkdir(parents=True)
        shutil.copy2(
            CCBENCH_ROOT / f"cc/{protocol}/CMakeLists.txt",
            protocol_target,
        )
    return fixture_root


def _receipt(protocol: str, configure_defines: list[str]) -> dict:
    return {
        "ccbench": {
            "build_argv": [
                "cmake", "-S", "/fixture/source", "-B", "/fixture/build",
                *configure_defines,
                "&&",
                "cmake", "--build", "/fixture/build", "--target",
                f"ycsb_{protocol}.exe", "-j", "48",
            ],
        },
    }


def test_genome_axis_cache_table_matches_ccbench_sources() -> None:
    _assert_axis_cache_table_matches_ccbench(
        CCBENCH_ROOT, GENOME_AXIS_CMAKE_CACHE_VARIABLES,
    )


def test_genome_axis_cache_mapping_roundtrips_every_declared_entry() -> None:
    for (protocol, axis), cache_variable in (
        GENOME_AXIS_CMAKE_CACHE_VARIABLES.items()
    ):
        assert cmake_cache_variable_for_axis(protocol, axis) == cache_variable
        assert genome_axis_from_cmake_cache_variable(
            protocol, cache_variable,
        ) == axis


def test_genome_axis_cache_table_accepts_empty_cache_default(
    tmp_path: Path,
) -> None:
    fixture_root = _copy_ccbench_axis_cache_sources(tmp_path)
    options_path = fixture_root / "cmake/Options.cmake"
    source = options_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(set\(\s*CCBENCH_INLINE_VERSION_OPT_CICADA\s+)"
        r'(?:"[^"]*"|\S+)(\s+CACHE\s+STRING\b)',
    )
    source, replacements = pattern.subn(r'\1""\2', source, count=1)
    assert replacements == 1
    options_path.write_text(source, encoding="utf-8")

    _assert_axis_cache_table_matches_ccbench(
        fixture_root, GENOME_AXIS_CMAKE_CACHE_VARIABLES,
    )


def test_genome_axis_cache_table_rejects_ccbench_side_rename(
    tmp_path: Path,
) -> None:
    fixture_root = _copy_ccbench_axis_cache_sources(tmp_path)
    old = "CCBENCH_INLINE_VERSION_OPT_CICADA"
    new = "CCBENCH_INLINE_VERSION_OPT_CICADA_RENAMED"
    for relative in ("cmake/Options.cmake", "cc/cicada/CMakeLists.txt"):
        path = fixture_root / relative
        source = path.read_text(encoding="utf-8")
        assert old in source
        path.write_text(source.replace(old, new), encoding="utf-8")

    with pytest.raises(AssertionError):
        _assert_axis_cache_table_matches_ccbench(
            fixture_root, GENOME_AXIS_CMAKE_CACHE_VARIABLES,
        )


def test_genome_axis_cache_table_rejects_non_cicada_ccbench_side_rename(
    tmp_path: Path,
) -> None:
    fixture_root = _copy_ccbench_axis_cache_sources(tmp_path)
    old = "CCBENCH_KEY_SORT"
    new = "CCBENCH_KEY_SORT_RENAMED"
    for relative in ("cmake/Options.cmake", "cc/mocc/CMakeLists.txt"):
        path = fixture_root / relative
        source = path.read_text(encoding="utf-8")
        assert old in source
        path.write_text(source.replace(old, new), encoding="utf-8")

    with pytest.raises(AssertionError):
        _assert_axis_cache_table_matches_ccbench(
            fixture_root, GENOME_AXIS_CMAKE_CACHE_VARIABLES,
        )


def test_genome_axis_cache_table_rejects_izanagi_side_rename() -> None:
    declared = dict(GENOME_AXIS_CMAKE_CACHE_VARIABLES)
    declared[("cicada", "INLINE_VERSION_OPT")] = (
        "CCBENCH_INLINE_VERSION_OPT_CICADA_RENAMED"
    )

    with pytest.raises(AssertionError):
        _assert_axis_cache_table_matches_ccbench(CCBENCH_ROOT, declared)


@pytest.mark.parametrize("protocol", ["silo", "mocc", "tictoc", "cicada"])
def test_genome_axis_cache_mapping_rejects_non_injective_copy_for_every_protocol(
    protocol: str,
) -> None:
    mapping = dict(GENOME_AXIS_CMAKE_CACHE_VARIABLES)
    entries = [
        (axis, cache_variable)
        for (entry_protocol, axis), cache_variable in mapping.items()
        if entry_protocol == protocol
    ]
    assert len(entries) >= 2
    (_first_axis, first_cache_variable), (second_axis, _second_cache_variable) = (
        entries[:2]
    )
    mapping[(protocol, second_axis)] = first_cache_variable

    with pytest.raises(ValueError, match="単射でない"):
        cmake_cache_variable_for_axis(
            protocol, second_axis, mapping=mapping,
        )
    with pytest.raises(ValueError, match="単射でない"):
        genome_axis_from_cmake_cache_variable(
            protocol, first_cache_variable, mapping=mapping,
        )


def test_genome_axis_cache_mapping_keeps_unknown_axis_identity_fallback() -> None:
    assert cmake_cache_variable_for_axis(
        "silo", "BACKOFF_FIXED",
    ) == "CCBENCH_BACKOFF_FIXED"
    assert genome_axis_from_cmake_cache_variable(
        "silo", "CCBENCH_BACKOFF_FIXED",
    ) == "BACKOFF_FIXED"


def test_cicada_cmake_defines_preserve_distinct_axis_values() -> None:
    genome = Genome("cicada", {
        "BACK_OFF": 11,
        "INLINE_VERSION_OPT": 22,
        "INLINE_VERSION_PROMOTION": 33,
        "REUSE_VERSION": 44,
        "WRITE_LATEST_ONLY": 55,
    })

    assert genome.canonical() == (
        "cicada|BACK_OFF=11,INLINE_VERSION_OPT=22,"
        "INLINE_VERSION_PROMOTION=33,REUSE_VERSION=44,WRITE_LATEST_ONLY=55"
    )
    assert genome.cmake_defines() == [
        "-DCCBENCH_BACK_OFF=11",
        "-DCCBENCH_INLINE_VERSION_OPT_CICADA=22",
        "-DCCBENCH_INLINE_VERSION_PROMOTION=33",
        "-DCCBENCH_REUSE_VERSION=44",
        "-DCCBENCH_WRITE_LATEST_ONLY=55",
    ]


def test_cicada_receipt_accepts_real_cache_name_with_distinct_axis_values() -> None:
    receipt = _receipt("cicada", [
        "-DCCBENCH_TRACE=0",
        "-DCCBENCH_BACK_OFF=11",
        "-DCCBENCH_INLINE_VERSION_OPT_CICADA=22",
        "-DCCBENCH_INLINE_VERSION_PROMOTION=33",
        "-DCCBENCH_REUSE_VERSION=44",
        "-DCCBENCH_WRITE_LATEST_ONLY=55",
    ])

    assert _canonical_genome_from_receipt(
        receipt, "/fixture/build/cc/cicada/ycsb_cicada.exe",
    ) == (
        "cicada|BACK_OFF=11,INLINE_VERSION_OPT=22,"
        "INLINE_VERSION_PROMOTION=33,REUSE_VERSION=44,WRITE_LATEST_ONLY=55"
    )


def test_cicada_receipt_rejects_generic_cache_name() -> None:
    receipt = _receipt("cicada", [
        "-DCCBENCH_TRACE=0",
        "-DCCBENCH_BACK_OFF=11",
        "-DCCBENCH_INLINE_VERSION_OPT=22",
        "-DCCBENCH_INLINE_VERSION_PROMOTION=33",
        "-DCCBENCH_REUSE_VERSION=44",
        "-DCCBENCH_WRITE_LATEST_ONLY=55",
    ])

    with pytest.raises(CertificationError) as caught:
        _canonical_genome_from_receipt(
            receipt, "/fixture/build/cc/cicada/ycsb_cicada.exe",
        )
    assert caught.value.code == "receipt-genome-invalid"


def test_cicada_receipt_rejects_unmapped_cicada_suffix_alias() -> None:
    configure_defines = [
        "-DCCBENCH_TRACE=0",
        "-DCCBENCH_BACK_OFF=11",
        "-DCCBENCH_INLINE_VERSION_OPT_CICADA=22",
        "-DCCBENCH_INLINE_VERSION_PROMOTION=33",
        "-DCCBENCH_REUSE_VERSION=44",
        "-DCCBENCH_WRITE_LATEST_ONLY=55",
    ]
    correct = "-DCCBENCH_REUSE_VERSION=44"
    alias = "-DCCBENCH_REUSE_VERSION_CICADA=44"
    configure_defines = [
        alias if token == correct else token for token in configure_defines
    ]
    assert correct not in configure_defines
    assert alias in configure_defines
    receipt = _receipt("cicada", configure_defines)

    with pytest.raises(CertificationError) as caught:
        _canonical_genome_from_receipt(
            receipt, "/fixture/build/cc/cicada/ycsb_cicada.exe",
        )
    assert caught.value.code == "receipt-genome-invalid"


@pytest.mark.parametrize(
    ("protocol", "configure_defines", "expected"),
    [
        (
            "silo",
            [
                "-DCCBENCH_TRACE=0",
                "-DCCBENCH_BACK_OFF=11",
                "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=22",
                "-DCCBENCH_NO_WAIT_OF_TICTOC=33",
                "-DCCBENCH_WAL=44",
            ],
            "silo|BACK_OFF=11,"
            "NO_WAIT_LOCKING_IN_VALIDATION=22,NO_WAIT_OF_TICTOC=33,WAL=44",
        ),
        (
            "mocc",
            [
                "-DCCBENCH_TRACE=0",
                "-DCCBENCH_BACK_OFF=11",
                "-DCCBENCH_KEY_SORT=22",
                "-DCCBENCH_TEMPERATURE_RESET_OPT=33",
            ],
            "mocc|BACK_OFF=11,KEY_SORT=22,TEMPERATURE_RESET_OPT=33",
        ),
        (
            "tictoc",
            [
                "-DCCBENCH_TRACE=0",
                "-DCCBENCH_BACK_OFF=11",
                "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=22",
                "-DCCBENCH_NO_WAIT_OF_TICTOC=33",
                "-DCCBENCH_PREEMPTIVE_ABORTS=44",
                "-DCCBENCH_TIMESTAMP_HISTORY=55",
            ],
            "tictoc|BACK_OFF=11,NO_WAIT_LOCKING_IN_VALIDATION=22,"
            "NO_WAIT_OF_TICTOC=33,PREEMPTIVE_ABORTS=44,TIMESTAMP_HISTORY=55",
        ),
    ],
    ids=["silo", "mocc", "tictoc"],
)
def test_receipt_accepts_real_cache_names_for_certification_protocols(
    protocol: str,
    configure_defines: list[str],
    expected: str,
) -> None:
    receipt = _receipt(protocol, configure_defines)

    assert _canonical_genome_from_receipt(
        receipt, f"/fixture/build/cc/{protocol}/ycsb_{protocol}.exe",
    ) == expected


def _load_cost_probe():
    spec = importlib.util.spec_from_file_location(
        "t1683_rr5_cost_probe_test", COST_PROBE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rratio_gate_values(source: str, variable: str) -> list[str]:
    comparison = f'"${variable}" != "'
    comparison_start = source.index(comparison)
    gate_start = source.rfind("if [[", 0, comparison_start)
    gate_end = source.index("\nfi", comparison_start)
    assert gate_start >= 0
    gate = source[gate_start:gate_end]
    return re.findall(rf'\${re.escape(variable)}" != "([^"]+)"', gate)


def test_submitter_exposes_only_the_calibration_whitelist() -> None:
    source = SUBMIT.read_text(encoding="utf-8")

    assert "[--job-script PATH] [--rratio 5|20|50|80|95]" in source
    assert "[--protocol silo|mocc|tictoc]" in source
    assert 'RRATIO=50' in source
    assert 'PROTOCOL=silo' in source
    assert 'PROTOCOL_EXPLICIT=0' in source
    assert 'RRATIO" != "5"' in source
    assert 'RRATIO" != "20"' in source
    assert 'RRATIO" != "50"' in source
    assert 'RRATIO" != "80"' in source
    assert 'RRATIO" != "95"' in source
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


def test_job_rechecks_the_submission_workload_and_records_it(
    tmp_path: Path,
) -> None:
    source = JOB.read_text(encoding="utf-8")
    expected_rratios = ["5", "20", "50", "80", "95"]

    submit_rratios = _rratio_gate_values(
        SUBMIT.read_text(encoding="utf-8"), "RRATIO",
    )
    job_rratios = _rratio_gate_values(source, "IZANAGI_CALIBRATION_RRATIO")
    assert submit_rratios == expected_rratios
    assert job_rratios == expected_rratios
    assert submit_rratios == job_rratios
    assert 'CALIBRATION_RRATIO="$IZANAGI_CALIBRATION_RRATIO"' in source
    assert 'CALIBRATION_PROTOCOL=${IZANAGI_CALIBRATION_PROTOCOL-silo}' in source
    assert '"calibration_rratio": (' in source
    assert '"calibration_protocol": doc.get("calibration", {}).get("protocol") == protocol' in source
    assert 'ycsb_rratio=$CALIBRATION_RRATIO' in source
    assert '"protocol": protocol' in source
    assert '"workload": {"ycsb_rratio": rratio}' in source
    assert "ycsb_rratio=50" not in source

    fixture_repo = tmp_path / "job-repo"
    fixture_tools = fixture_repo / "tools" / "pegasus"
    fixture_tools.parent.mkdir(parents=True)
    shutil.copytree(
        ROOT / "tools" / "pegasus",
        fixture_tools,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    real_mkdir = shutil.which("mkdir")
    assert real_mkdir is not None
    mkdir_shim = fake_bin / "mkdir"
    mkdir_shim.write_text(
        "#!/bin/bash\n"
        'if [[ "${1:-}" == /scr/* ]]; then\n'
        "  exit 0\n"
        "fi\n"
        f'exec {shlex.quote(real_mkdir)} "$@"\n',
        encoding="utf-8",
    )
    mkdir_shim.chmod(0o755)
    rratio_failure = (
        "IZANAGI_CALIBRATION_RRATIO must be exactly 5, 20, 50, 80, or 95"
    )
    protocol_failure = (
        "IZANAGI_CALIBRATION_PROTOCOL must be exactly silo, mocc, or tictoc"
    )
    base_env = os.environ.copy()
    base_env.update({
        "PATH": f"{fake_bin}:{base_env['PATH']}",
        "PBS_O_WORKDIR": str(fixture_repo),
        "IZANAGI_SUBMISSION_NONCE": "fixture-nonce",
        # Stop immediately after the rratio gate, before the receipt wait.
        "IZANAGI_CALIBRATION_PROTOCOL": "invalid-fixture-protocol",
    })

    for index, rratio in enumerate(expected_rratios):
        job_id = f"accepted-rratio-{index}"
        env = base_env | {
            "PBS_JOBID": job_id,
            "IZANAGI_CALIBRATION_RRATIO": rratio,
        }
        completed = subprocess.run(
            ["bash", str(fixture_tools / "certify_calibration.sh")],
            cwd=fixture_repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 2, completed.stderr
        failure = json.loads((
            fixture_repo
            / "output/env/pegasus/calibration/job-staging"
            / job_id
            / "failure.json"
        ).read_text(encoding="utf-8"))
        assert (failure["stage"], failure["message"]) != (
            "submit_binding", rratio_failure,
        )
        assert failure["stage"] == "submit_binding"
        assert failure["message"] == protocol_failure

    for index, rratio in enumerate(("+5", "05", " 5", "5 ", "５", "51")):
        job_id = f"rejected-rratio-{index}"
        env = base_env | {
            "PBS_JOBID": job_id,
            "IZANAGI_CALIBRATION_RRATIO": rratio,
        }
        completed = subprocess.run(
            ["bash", str(fixture_tools / "certify_calibration.sh")],
            cwd=fixture_repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 2, completed.stderr
        failure = json.loads((
            fixture_repo
            / "output/env/pegasus/calibration/job-staging"
            / job_id
            / "failure.json"
        ).read_text(encoding="utf-8"))
        assert failure["stage"] == "submit_binding"
        assert failure["message"] == rratio_failure


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
    build_case_start = source.index(
        'case "$CALIBRATION_PROTOCOL" in', configure_start,
    )
    configure_end = build_case_start
    build_case_end = source.index("\nesac", build_case_start) + len("\nesac")
    binary_match = re.search(r'^BINARY=.*$', source[build_case_end:], re.MULTILINE)
    assert binary_match is not None
    binary_line = binary_match.group(0)
    fragment = "\n".join((
        source[define_case_start:define_case_end],
        source[configure_start:configure_end],
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
{fragment}
printf 'binary=%s\n' "$BINARY"
printf 'configure:'; printf ' %q' "${{configure_argv[@]}}"; printf '\n'
printf 'build:'; printf ' %q' "${{build_argv[@]}}"; printf '\n'
"""
    completed = subprocess.run(
        ["bash", "-c", command],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    lines = completed.stdout.splitlines()
    build_argv = shlex.split(lines[2].removeprefix("build:"))
    return {
        "target": build_argv[build_argv.index("--target") + 1],
        "binary": lines[0].removeprefix("binary="),
        "configure_argv": shlex.split(lines[1].removeprefix("configure:")),
        "build_argv": build_argv,
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


@pytest.mark.parametrize("mode", [
    "unavailable", "probe_error", "selected", "literal_available",
])
def test_certify_perf_preflight_argv(tmp_path, mode):
    """Execute production selection/preflight/argv only, not exec or job finalization."""
    import sys

    attempt = tmp_path / "attempt"
    attempt.mkdir()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    base = tmp_path / "base"
    base.mkdir()
    # Isolate PATH from host perf, including the selected Python's directory.
    for name in ("python3", "dirname", "timeout", "grep", "realpath", "cat", "mkdir", "ln", "env"):
        (base / name).symlink_to(sys.executable if name == "python3" else shutil.which(name))
    log = tmp_path / "perf-calls.jsonl"

    def perf_fixture(path, behavior):
        path.write_text(
            f"#!{sys.executable}\n"
            "import json, os, signal, sys\n"
            f"with open({str(log)!r}, 'a') as out:\n"
            "    out.write(json.dumps([sys.argv[0], sys.argv[1:]]) + '\\n')\n"
            f"behavior = {behavior!r}\n"
            "if behavior == 'probe_error':\n"
            "    os.kill(os.getpid(), signal.SIGTERM)\n"
            "if behavior == 'unavailable':\n"
            "    sys.exit(2)\n"
            "if '--version' in sys.argv:\n"
            "    print('fixture perf')\n"
            "elif '-o' in sys.argv:\n"
            "    events = sys.argv[sys.argv.index('-e') + 1].split(',')\n"
            "    with open(sys.argv[sys.argv.index('-o') + 1], 'w') as out:\n"
            "        out.write(''.join('1,,' + event + '\\n' for event in events))\n",
            encoding="utf-8",
        )
        path.chmod(0o755)

    failed = tmp_path / "failed-perf"
    perf_fixture(failed, "unavailable")
    candidates = [failed]
    if mode == "selected":
        selected = tmp_path / "selected-perf"
        perf_fixture(selected, "available")
        candidates.append(selected)
    else:
        perf_fixture(base / "perf", "available" if mode == "literal_available" else mode)

    source = JOB.read_text(encoding="utf-8")
    fragment = source[source.index("# (vii) policy-pinned perf"):source.index("\ncalibrate_rc=0")]
    values = {
        "REPO_ROOT": str(ROOT), "ATTEMPT_DIR": str(attempt), "TMPDIR": str(scratch),
        "CALIBRATE_PYTHON": str(base / "python3"), "PATH": str(base),
        "CALIBRATION_RRATIO": "50", "BINARY": str(tmp_path / "ycsb_silo.exe"),
        "BINARY_SHA": "c" * 64,
    }
    command = "set -Eeuo pipefail\n"
    command += "\n".join(f"{key}={shlex.quote(value)}" for key, value in values.items())
    command += "\nexport PATH\n"
    command += "PERF_CANDIDATES=(" + " ".join(shlex.quote(str(p)) for p in candidates) + ")\n"
    command += 'write_failure() { printf "%s\\n" "$*" > "$ATTEMPT_DIR/fixture-failure"; }\n'
    completed = subprocess.run(
        ["/bin/bash", "-c", command + fragment], capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    receipt = json.loads((attempt / "perf-preflight.json").read_text())
    if mode == "probe_error":
        assert completed.returncode == 2, completed.stderr
        assert receipt["status"] == "probe_error"
        assert receipt["reason"] == "probe-signal"
        assert not (attempt / "calibrate-argv.json").exists()
        assert (attempt / "fixture-failure").read_text().startswith("2 perf ")
        return

    assert completed.returncode == 0, completed.stderr
    argv = json.loads((attempt / "calibrate-argv.json").read_text())
    expected_path = f"{base}:{base}"
    if mode == "selected":
        expected_path = f"{scratch}/bin:{base}:{base}"
        assert (scratch / "bin/perf").resolve() == selected
        selection = json.loads((attempt / "perf-selection.json").read_text())
        assert selection["path"] == str(selected)
    else:
        assert not (scratch / "bin/perf").exists()
        assert not (attempt / "perf-selection.json").exists()

    expected = [
        "env", f"PATH={expected_path}", str(base / "python3"), str(ROOT / "orchestrator/calibrate.py"),
        "--certify", "--env-tag", "pegasus", "--threads", "48",
        "--workload", "ycsb_zipf_skew=0.9,ycsb_rratio=50,ycsb_rmw=0",
        "--binary", values["BINARY"], "--binary-sha256", "c" * 64,
        "--receipt-json", str(attempt / "acquisition-receipt.json"),
    ]
    if mode == "unavailable":
        assert receipt["status"] == "unavailable"
        expected += ["--perf-preflight-json", str(attempt / "perf-preflight.json")]
    else:
        assert receipt["status"] == "available"
    assert argv == expected
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    literal = str(scratch / "bin/perf") if mode == "selected" else str(base / "perf")
    assert sum(path == literal and "-o" in args for path, args in calls) == 1
    if mode == "selected":
        assert calls[0] == [str(failed), ["--version"]]


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
        (source / "nested").mkdir()
        (source / "nested/source.txt").write_text(
            f"{name}-nested-pristine\n", encoding="utf-8",
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


def _third_party_verify_interpreter_fragment() -> str:
    fragment = _job_copy_fragment()
    start = fragment.index('THIRD_PARTY_VERIFY_PYTHON=""')
    end = fragment.index("\nfor third_party_name in", start)
    return fragment[start:end]


def _configure_invocation_fragment() -> str:
    source = JOB.read_text(encoding="utf-8")
    matches = re.findall(
        r'^timeout 900 .*configure_argv.*$', source, re.MULTILINE,
    )
    assert len(matches) == 1
    return matches[0]


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
        assert set(table[protocol]) - excluded == set(SPACES[protocol].axes)


def test_certify_shell_protocol_defines_match_exact_values() -> None:
    assert _certify_protocol_define_table() == {
        "silo": {
            "TRACE": "0",
            "BACK_OFF": "0",
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


def test_calibrator_uses_smoke_checked_interpreter_selected_before_call() -> None:
    source = JOB.read_text(encoding="utf-8")
    selection_start = source.index('CALIBRATE_PYTHON=""')
    failure_start = source.index(
        'if [[ -z "$CALIBRATE_PYTHON" ]]; then', selection_start,
    )
    selection_end = source.index("\nfi", failure_start) + len("\nfi")
    selection = source[selection_start:selection_end]

    assert (
        'if "$resolved" -I -B -c \\\n'
        "      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \\\n"
        '      >/dev/null 2>&1; then\n'
        '    CALIBRATE_PYTHON="$resolved"'
    ) in selection
    assert (
        'if [[ -z "$CALIBRATE_PYTHON" ]]; then\n'
        '  write_failure 2 interpreter \\\n'
        '    "no python3.10 interpreter passed smoke check '
        '(rejected: ${calibrate_python_rejected:-none})"\n'
        '  exit 2\n'
        'fi'
    ) in selection

    assert (
        source.index('ATTEMPT_DIR=')
        < source.index("trap on_err ERR")
        < selection_start
    )
    calibrate_start = source.index("calibrate_argv=(")
    calibrate_end = source.index("\n)", calibrate_start) + len("\n)")
    assert selection_end < calibrate_start
    assert (
        '"$CALIBRATE_PYTHON" "$REPO_ROOT/orchestrator/calibrate.py"'
    ) in source[calibrate_start:calibrate_end]


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


def test_certify_configure_use_site_passes_the_complete_configure_argv(
    tmp_path: Path,
) -> None:
    configure_argv = _protocol_shell_observation("silo")["configure_argv"]
    assert isinstance(configure_argv, list)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_timeout = fake_bin / "timeout"
    fake_timeout.write_text(
        "#!/bin/sh\n"
        ": \"${TIMEOUT_ARGV_PATH:?}\"\n"
        "printf '%s\\n' \"$@\" >\"$TIMEOUT_ARGV_PATH\"\n",
        encoding="utf-8",
    )
    fake_timeout.chmod(0o755)
    attempt_dir = tmp_path / "attempt"
    attempt_dir.mkdir()
    timeout_argv_path = tmp_path / "timeout.argv"
    command = f"""set -Eeuo pipefail
ATTEMPT_DIR={shlex.quote(str(attempt_dir))}
configure_argv=({shlex.join(configure_argv)})
{_configure_invocation_fragment()}
"""
    env = dict(os.environ)
    env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
    env["TIMEOUT_ARGV_PATH"] = str(timeout_argv_path)
    completed = subprocess.run(
        ["bash", "-c", command],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
    assert timeout_argv_path.read_text(encoding="utf-8").splitlines() == [
        "900", *configure_argv,
    ]


def test_certify_third_party_verifier_uses_version_checked_interpreter() -> None:
    source = JOB.read_text(encoding="utf-8")
    fragment = _job_copy_fragment()
    resolver = _third_party_verify_interpreter_fragment()
    assert source.index('THIRD_PARTY_VERIFY_PYTHON=""') < source.index(
        "for third_party_name in masstree mimalloc googletest; do",
        source.index("# (iv-c)"),
    )
    assert "python3.10 /usr/bin/python3.10 /bin/python3.10" in resolver
    assert (
        'if "$resolved" -I -B -c \\\n'
        "      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)'"
        in resolver
    )
    assert 'write_failure 2 interpreter \\\n' in resolver
    assert 'timeout 120 "$THIRD_PARTY_VERIFY_PYTHON" - \\\n' in fragment
    assert "timeout 120 python3 -" not in fragment


def test_certify_third_party_verifier_interpreter_resolution_fails_closed(
    tmp_path: Path,
) -> None:
    fragment = _third_party_verify_interpreter_fragment()
    fragment = fragment.replace(
        "/usr/bin/python3.10", str(tmp_path / "missing-usr-python3.10"),
    )
    fragment = fragment.replace(
        "/bin/python3.10", str(tmp_path / "missing-bin-python3.10"),
    )
    writer_bin = tmp_path / "writer-bin"
    writer_bin.mkdir()
    writer_python = shutil.which("python3")
    assert writer_python is not None
    (writer_bin / "python3").symlink_to(writer_python)
    failure_path = tmp_path / "failure.txt"
    command = f"""set -Eeuo pipefail
PATH={shlex.quote(str(writer_bin))}
write_failure() {{ printf '%s:%s:%s\\n' "$1" "$2" "$3" >{shlex.quote(str(failure_path))}; }}
{fragment}
"""
    completed = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 2, completed.stderr
    failure = failure_path.read_text(encoding="utf-8")
    assert failure.startswith("2:interpreter:")
    assert "no python3.10 interpreter passed smoke check" in failure


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
    before_trees = {
        name: {
            path.relative_to(staging_root / name): path.read_bytes()
            for path in (staging_root / name).rglob("*")
            if path.is_file()
        }
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
        after_tree = {
            path.relative_to(staging_root / name): path.read_bytes()
            for path in (staging_root / name).rglob("*")
            if path.is_file()
        }
        assert after_tree == before_trees[name]


@pytest.mark.parametrize("ignored_name", THIRD_PARTY_NAMES)
def test_certify_job_rejects_a_staging_source_with_ignored_artifacts(
    tmp_path: Path, ignored_name: str,
) -> None:
    fixture_repo, staging_root = _make_verified_third_party_fixture(
        tmp_path, ignored_name=ignored_name,
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

    regular_file_child_repo = tmp_path / "regular-file-child-repo"
    regular_file_child_repo.mkdir()
    regular_file_child_root = _third_party_staging_root(regular_file_child_repo)
    regular_file_child_root.mkdir(parents=True)
    for name in ("masstree", "mimalloc"):
        (regular_file_child_root / name).mkdir()
    (regular_file_child_root / "googletest").write_text(
        "not a directory\n", encoding="utf-8",
    )
    malformed_repos.append(regular_file_child_repo)

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


@pytest.mark.parametrize(
    "rratio",
    ["0", "51", "100", "05", "+5", " 5", "5 ", "５"],
)
def test_submitter_rejects_an_unregistered_ratio_before_side_effects(
    tmp_path: Path, rratio: str,
) -> None:
    # Empty is intentionally omitted: `${2:?}` rejects it before this gate, and
    # the contract does not require that earlier rejection to use the same rc.
    _repo, _common, _output, qsub_argv, completed = (
        _run_submit_dry_run_in_clean_fixture(
            tmp_path,
            rratio=rratio,
            expected_returncode=2,
        )
    )

    assert completed.returncode == 2
    assert "--rratio must be exactly 5, 20, 50, 80, or 95" in completed.stderr
    assert qsub_argv == []
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


def _make_submit_clean_fixture(tmp_path: Path) -> Path:
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

    return fixture_repo


def _run_submit_dry_run_in_clean_fixture(
    tmp_path: Path,
    *,
    protocol: str | None = None,
    rratio: str | None = None,
    expected_returncode: int = 0,
) -> tuple[
    Path, Path, Path, list[str], subprocess.CompletedProcess[str],
]:
    fixture_repo = _make_submit_clean_fixture(tmp_path)
    fixture_tools = fixture_repo / "tools" / "pegasus"

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
    if rratio is not None:
        command.extend(["--rratio", rratio])
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == expected_returncode, completed.stderr
    command_lines = [
        line for line in completed.stdout.splitlines()
        if line.startswith("qsub command:")
    ]
    if expected_returncode == 0:
        assert len(command_lines) == 1
        qsub_argv = shlex.split(command_lines[0].removeprefix("qsub command:"))
    else:
        assert command_lines == []
        qsub_argv = []

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
    return (
        fixture_repo,
        git_common_dir.parent,
        expected_root,
        qsub_argv,
        completed,
    )


@pytest.mark.parametrize("protocol", ["silo", "mocc", "tictoc"])
def test_submitter_accepts_exact_protocol_whitelist_and_records_it(
    tmp_path: Path, protocol: str,
) -> None:
    _repo, _common, _output, qsub_argv, _completed = (
        _run_submit_dry_run_in_clean_fixture(tmp_path, protocol=protocol)
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
    fixture_repo, _common, expected_root, qsub_argv, _completed = (
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


@pytest.mark.parametrize("rratio", ["5", "20", "50", "80", "95"])
def test_submit_dry_run_passes_scheduler_file_paths_to_qsub(
    tmp_path: Path, rratio: str,
) -> None:
    _fixture_repo, _git_common_repo, expected_root, qsub_argv, _completed = (
        _run_submit_dry_run_in_clean_fixture(tmp_path, rratio=rratio)
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
    assert pre_submit["request"]["calibration_rratio"] == int(rratio)
    assert receipt["calibration"]["workload"]["ycsb_rratio"] == rratio
    export_spec = qsub_argv[qsub_argv.index("-v") + 1]
    assert export_spec == (
        f"IZANAGI_SUBMISSION_NONCE={nonce},"
        f"IZANAGI_CALIBRATION_RRATIO={rratio}"
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
    fixture_repo, git_common_repo, _expected_root, qsub_argv, _completed = (
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


def _run_submit_with_fake_qsub(
    tmp_path: Path,
    repo_root: Path,
    caller: Path,
    *,
    attempts_root: Path | None = None,
    job_script: Path | None = None,
    qsub_rc: int = 0,
    bash_quoted_display: bool = False,
) -> tuple[subprocess.CompletedProcess[str], dict, Path]:
    fake_bin = (tmp_path / "fake-bin").resolve()
    fake_bin.mkdir()
    observation_path = (tmp_path / "qsub-observation.json").resolve()
    for name in ("qstat", "pegasusinfo", "rbudgetcheck", "check_quota"):
        stub = fake_bin / name
        stub.write_text("#!/bin/sh\nprintf 'preflight ok\\n'\n", encoding="utf-8")
        stub.chmod(0o755)
    qsub = fake_bin / "qsub"
    qsub.write_text(
        "#!/usr/bin/env python3\n"
        "import hashlib, json, os, sys\n"
        "from pathlib import Path\n"
        "script = Path(sys.argv[-1]).read_bytes()\n"
        "observation = {'cwd': os.getcwd(), 'argv': ['qsub', *sys.argv[1:]],\n"
        "               'script_hex': script.hex(),\n"
        "               'script_sha256': hashlib.sha256(script).hexdigest()}\n"
        "Path(os.environ['QSUB_OBSERVATION']).write_text(json.dumps(observation))\n"
        "rc = int(os.environ['QSUB_RC'])\n"
        "if rc:\n"
        "    print('fake qsub failure', file=sys.stderr)\n"
        "else:\n"
        "    print('Request 12345.server submitted')\n"
        "sys.exit(rc)\n",
        encoding="utf-8",
    )
    qsub.chmod(0o755)
    command = [
        "bash", str(repo_root / "tools/pegasus/submit_certify.sh"),
        "--repo-root", str(repo_root),
    ]
    if attempts_root is not None:
        command.extend(["--attempts-root", str(attempts_root)])
    if job_script is not None:
        command.extend(["--job-script", str(job_script)])
    env = os.environ | {
        "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
        "QSUB_OBSERVATION": str(observation_path),
        "QSUB_RC": str(qsub_rc),
    }
    completed = subprocess.run(
        command, cwd=caller, env=env, capture_output=True, text=True,
        check=False, timeout=30,
    )
    assert completed.returncode == qsub_rc, completed.stdout + completed.stderr
    observed = json.loads(observation_path.read_text(encoding="utf-8"))
    if bash_quoted_display:
        # shlex cannot decode Bash's ANSI-C quoting for newline-containing paths.
        expected_display = subprocess.run(
            ["bash", "-c", "printf 'qsub command:'; printf ' %q' \"$@\"",
             "qsub-display", *observed["argv"]],
            capture_output=True, text=True, check=True,
        ).stdout
        assert [
            line for line in completed.stdout.splitlines()
            if line.startswith("qsub command:")
        ] == [expected_display]
    else:
        displayed = [
            shlex.split(line.removeprefix("qsub command:"))
            for line in completed.stdout.splitlines()
            if line.startswith("qsub command:")
        ]
        assert displayed == [observed["argv"]]
    attempts = attempts_root or repo_root / "output/env/pegasus/calibration/attempts"
    if not attempts.is_absolute():
        attempts = caller / attempts
    submissions = list((attempts / "submissions").iterdir())
    assert len(submissions) == 1
    submission = submissions[0]
    pre = json.loads((submission / "pre-submit.json").read_text(encoding="utf-8"))
    assert pre["dry_run"] is False
    assert pre["job_script_sha256"] == observed["script_sha256"]
    assert (submission / "qsub.rc").read_text() == f"{qsub_rc}\n"
    if qsub_rc == 0:
        receipt = json.loads(
            (submission / "submit-receipt.json").read_text(encoding="utf-8"),
        )
        assert receipt["qsub"]["request_id"] == "12345.server"
        assert receipt["dry_run"] is False
        assert receipt["job_script_sha256"] == observed["script_sha256"]
        assert (submission / "qsub.stdout").read_text() == (
            "Request 12345.server submitted\n"
        )
    return completed, observed, submission


@pytest.mark.parametrize("outside_repo", [False, True], ids=["repo", "outside"])
def test_submitter_runs_qsub_in_repo_root(tmp_path: Path, outside_repo: bool) -> None:
    repo = _make_submit_clean_fixture(tmp_path)
    caller = tmp_path / "caller" if outside_repo else repo
    caller.mkdir(exist_ok=True)
    _completed, observed, _submission = _run_submit_with_fake_qsub(
        tmp_path, repo, caller,
    )
    assert observed["cwd"] == str(repo)
    if outside_repo:
        assert observed["cwd"] != str(caller)
    script = repo / "tools/pegasus/certify_calibration.sh"
    assert observed["argv"][-1] == str(script)
    assert bytes.fromhex(observed["script_hex"]) == script.read_bytes()


def test_submitter_keeps_relative_attempts_in_caller(tmp_path: Path) -> None:
    repo = _make_submit_clean_fixture(tmp_path)
    caller = tmp_path / "caller"
    caller.mkdir()
    attempts = Path("new attempts")
    _completed, observed, submission = _run_submit_with_fake_qsub(
        tmp_path, repo, caller, attempts_root=attempts,
    )
    assert observed["cwd"] == str(repo)
    assert submission.parent == caller / attempts / "submissions"
    assert not (repo / attempts).exists()
    capture_names = ("qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota", "qsub")
    assert {path.name for path in submission.iterdir()} == {
        *(f"{name}.{suffix}" for name in capture_names
          for suffix in ("stdout", "stderr", "rc")),
        "pre-submit.json", "submit-receipt.json",
    }
    for name in capture_names:
        assert (submission / f"{name}.rc").read_text() == "0\n"
        assert (submission / f"{name}.stderr").read_text() == ""
        assert (submission / f"{name}.stdout").read_text()


@pytest.mark.parametrize(
    "payload", [b"#!/bin/sh\necho caller\n", b"#!/bin/sh\necho changed\n"],
    ids=["original", "changed"],
)
def test_submitter_keeps_relative_job_script_bytes_from_caller(
    tmp_path: Path, payload: bytes,
) -> None:
    repo = _make_submit_clean_fixture(tmp_path)
    caller = tmp_path / "caller"
    (caller / "output").mkdir(parents=True)
    relative_script = Path("output/custom script.sh")
    (caller / relative_script).write_bytes(payload)
    (repo / relative_script).write_bytes(b"#!/bin/sh\necho wrong-repo-script\n")
    _completed, observed, _submission = _run_submit_with_fake_qsub(
        tmp_path, repo, caller, job_script=relative_script,
    )
    assert observed["cwd"] == str(repo)
    assert observed["argv"][-1] == str(caller / relative_script)
    assert bytes.fromhex(observed["script_hex"]) == payload
    assert observed["script_sha256"] == hashlib.sha256(payload).hexdigest()


def test_submitter_keeps_relative_job_script_bytes_from_newline_caller(
    tmp_path: Path,
) -> None:
    repo = _make_submit_clean_fixture(tmp_path)
    caller = repo / "output" / "caller\n"
    sibling = repo / "output" / "caller"
    caller.mkdir()
    sibling.mkdir()
    relative_script = Path("custom.sh")
    payload = b"#!/bin/sh\necho newline-caller\n"
    wrong_payload = b"#!/bin/sh\necho wrong-sibling\n"
    (caller / relative_script).write_bytes(payload)
    (sibling / relative_script).write_bytes(wrong_payload)

    _completed, observed, _submission = _run_submit_with_fake_qsub(
        tmp_path, repo, caller, job_script=relative_script,
        bash_quoted_display=True,
    )

    assert observed["cwd"] == str(repo)
    assert observed["argv"][-1] == str(caller / relative_script)
    assert bytes.fromhex(observed["script_hex"]) == payload
    assert bytes.fromhex(observed["script_hex"]) != wrong_payload
    assert observed["script_sha256"] == hashlib.sha256(payload).hexdigest()


def test_submitter_preserves_qsub_failure_and_captures(tmp_path: Path) -> None:
    repo = _make_submit_clean_fixture(tmp_path)
    caller = tmp_path / "caller"
    caller.mkdir()
    completed, observed, submission = _run_submit_with_fake_qsub(
        tmp_path, repo, caller, qsub_rc=7,
    )
    assert observed["cwd"] == str(repo)
    assert completed.returncode == 7
    assert "qsub failed" in completed.stderr
    assert (submission / "qsub.stderr").read_text() == "fake qsub failure\n"
    assert (submission / "qsub.stdout").read_text() == ""
    assert not (submission / "submit-receipt.json").exists()


def test_runbook_shows_ai_driven_h1_h2_submission_path() -> None:
    source = README.read_text(encoding="utf-8")

    assert "submit_certify.sh --rratio 80" in source
    assert "submit_certify.sh --rratio 20" in source
    assert "submit_certify.sh --rratio 95" in source
    assert "submit_certify.sh --rratio 5" in source
    assert "5 / 20 / 50 / 80 / 95 の固定 whitelist" in source
    assert "skew0p9_rr{5|20|50|80|95}_rmw0" in source
    assert "--protocol mocc" in source
    assert "silo / mocc / tictoc" in source
    assert "INLINE_VERSION_OPT" in source
    assert "供給されていない BACKOFF_FIXED=-1 の指定と専用" in source
    assert "人間が JSON を編集・登録する必要はなく" in source
