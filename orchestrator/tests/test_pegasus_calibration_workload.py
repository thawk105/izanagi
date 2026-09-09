"""Calibration workload/protocol selection is bound, finite, and shell-valid."""

from __future__ import annotations

import importlib.util
import json
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
                "-DCCBENCH_BACKOFF_FIXED=-1",
                "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=22",
                "-DCCBENCH_NO_WAIT_OF_TICTOC=33",
                "-DCCBENCH_WAL=44",
            ],
            "silo|BACKOFF_FIXED=-1,BACK_OFF=11,"
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


def _protocol_shell_observation(protocol: str) -> dict[str, object]:
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
GFLAGS_INSTALL_DIR=/fixture/gflags
GLOG_INSTALL_DIR=/fixture/glog
GFLAGS_SOURCE_HEAD={'a' * 40}
GLOG_SOURCE_HEAD={'b' * 40}
CC_PATH=/bin/true
CXX_PATH=/bin/true
gate_calls=0
run_condition_gate() {{ gate_calls=$((gate_calls + 1)); }}
{fragment}
printf 'gate=%s\n' "$gate_calls"
printf 'binary=%s\n' "$BINARY"
printf 'configure:'; printf ' %q' "${{configure_argv[@]}}"; printf '\n'
printf 'build:'; printf ' %q' "${{build_argv[@]}}"; printf '\n'
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


def test_default_silo_build_and_calibrate_argv_are_byte_compatible() -> None:
    observed = _protocol_shell_observation("silo")
    true_path = str(Path("/bin/true").resolve())
    assert observed["configure_argv"] == [
        "/fixture/cmake", "-S", "/fixture/source", "-B", "/fixture/build",
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
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
