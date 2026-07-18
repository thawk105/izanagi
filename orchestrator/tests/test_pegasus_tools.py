# -*- coding: utf-8 -*-
"""計算機 command を実行せずに job 資材の構造と Python entry を検証する。"""
from __future__ import annotations

import base64
import dataclasses
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO = Path(__file__).resolve().parents[2]
TOOL_DIR = REPO / "tools" / "pegasus"

# Exact bytes captured from certification job 867863's qstat-f.stdout.
QSTAT_NQSV_867863 = base64.b64decode("""
UmVxdWVzdCBJRDogODY3ODYzLm5xc3YKICAgIFJlcXVlc3QgTmFtZSA9IGNlcnRpZnlfY2FsaWJyYXRpb24uc2gKICAgIFVzZXIg
IE5hbWUgPSB0YW5hYgogICAgR3JvdXAgTmFtZSA9IFNGQwogICAgVXNlciAgSUQgICA9IDMxNjA5CiAgICBHcm91cCBJRCAgID0g
MzA0MTAKICAgIEN1cnJlbnQgU3RhdGUgICAgICAgICAgID0gUnVubmluZwogICAgUHJldmlvdXMgU3RhdGUgICAgICAgICAgPSBQ
cmUtcnVubmluZwogICAgU3RhdGUgVHJhbnNpdGlvbiBUaW1lICAgPSBTdW4gSnVsIDE5IDAyOjE1OjU3IDIwMjYKICAgIFN0YXRl
IFRyYW5zaXRpb24gUmVhc29uID0gUFJFUlVOX1NVQ0NFU1MKICAgIFF1ZXVlID0gZ2VuX1NAbnFzdiAoRXhlY3V0aW9uIFF1ZXVl
KQogICAgSm9iIFRvcG9sb2d5ID0gRGlzdHJpYnV0ZSBKb2IKICAgIFJlcXVlc3QgUHJpb3JpdHkgID0gMAogICAgUmVxdWVzdCBM
b2dsZXZlbCAgPSAwCiAgICBSZXJ1bmFibGUgICAgPSBObwogICAgSG9sZGFibGUgICAgID0gWWVzCiAgICBIb2xkIFR5cGUgICAg
PSAobm9uZSkKICAgIE1pZ3JhdGFibGUgICA9IFllcwogICAgU3VzcGVuZCBUeXBlID0gKG5vbmUpCiAgICBBY2NvdW50IENvZGUg
PSBTRkMKICAgIFN0ZG91dCA9IHBlZ2FzdXMwMjovaG9tZS9TRkMvdGFuYWIvZ2l0aHViL2l6YW5hZ2kvLmNsYXVkZS93b3JrdHJl
ZXMvczhiLWMyMi1sYXVuY2gtY2VydC9jZXJ0aWZ5X2NhbGlicmF0aW9uLnNoLm8lcwogICAgU3RkZXJyID0gcGVnYXN1czAyOi9o
b21lL1NGQy90YW5hYi9naXRodWIvaXphbmFnaS8uY2xhdWRlL3dvcmt0cmVlcy9zOGItYzIyLWxhdW5jaC1jZXJ0L2NlcnRpZnlf
Y2FsaWJyYXRpb24uc2guZSVzCiAgICBSZXFsb2cgPSAobm9uZSkKICAgIFNoZWxsID0gKG5vbmUpCiAgICBNYWlsIEFkZHJlc3Mg
PSB0YW5hYkBwZWdhc3VzMDIKICAgIE1haWwgT3B0aW9uICA9IChub25lKQogICAgSm9iIENvbmRpdGlvbjoKICAgICAgICBKb2Ig
Tk86IDAgIiIKICAgIE51bWJlciBvZiBKb2JzID0gMQogICAgQ3JlYXRlZCBSZXF1ZXN0IFRpbWUgPSBTdW4gSnVsIDE5IDAyOjE1
OjUwIDIwMjYKICAgIEVudGVyZWQgUXVldWUgVGltZSAgID0gU3VuIEp1bCAxOSAwMjoxNTo1MCAyMDI2CiAgICBQbGFubmVkIFN0
YXJ0IFRpbWUgICA9IFN1biBKdWwgMTkgMDI6MTY6MDIgMjAyNgogICAgRXhlY3V0ZSBSZXF1ZXN0IFRpbWUgPSAobm9uZSkKICAg
IFN0YXJ0ZWQgUmVxdWVzdCBUaW1lID0gU3VuIEp1bCAxOSAwMjoxNTo1NyAyMDI2CiAgICBFbmRlZCBSZXF1ZXN0IFRpbWUgICA9
IChub25lKQogICAgUmVxdWVzdGVkIFN0YXJ0IFRpbWUgPSAobm9uZSkKICAgIERlYWRsaW5lIFRpbWUgICAgICAgID0gKG5vbmUp
CiAgICBVTUFTSyA9IDAyMgogICAgUmVzZXJ2YXRpb24gSUQgICAgICA9IChub25lKQogICAgcWF0dGFjaCBjb21tYW5kID0gRW5h
YmxlCiAgICBBdHRhY2ggPSBObwogICAgQ2x1c3RlciBUeXBlIFNlbGVjdCA9IE5PTkUKICAgIFVzZXJQUCBTY3JpcHQgPSAobm9u
ZSkKICAgIEV4Y2x1c2l2ZSA9IChub25lKQogICAgSENBIE51bWJlciA9IChub25lKQogICAgQWNjZXB0IFNpZ3Rlcm0gPSBObwog
ICAgRW5hYmxlIENsb3VkIEJ1cnN0aW5nID0gTm8KICBDdXN0b20gUmVzb3VyY2VzOgogICAgU2hhcmUgICAgICAgICAgID0gMQog
IEV4ZWN1dGlvbiBIb3N0cyhKU1ZOTyk6CiAgICBibm9kZTAwMygzKQogIFJlc291cmNlcyBJbmZvcm1hdGlvbjoKICAgIE1lbW9y
eSAgICA9IDAuMDAwMDAwQgogICAgQ1BVIFRpbWUgID0gMC4wMDAwMDBTCiAgICBBY2N1bXVsYXRlZCBDUFUgVGltZSA9IDAuMDAw
MDAwUwogICAgRWxhcHNlICAgID0gMVMKICAgIFJlbWFpbmluZyBFbGFwc2UgPSA3MTk5UwogICAgVmlydHVhbCBNZW1vcnkgPSAw
LjAwMDAwMEIKICBMb2dpY2FsIEhvc3QgUmVzb3VyY2VzOgogICAgVkUgTm9kZSBOdW1iZXIgICAgICAgID0gTWF4OiAgICAgICAg
IDAgV2FybjogICAgICAgLS0tIAogICAgQ1BVIE51bWJlciAgICAgICAgICAgID0gTWF4OiAgICAgICAgNDggV2FybjogICAgICAg
LS0tIAogICAgR1BVIE51bWJlciAgICAgICAgICAgID0gTWF4OiAgICAgICAgIDAgV2FybjogICAgICAgLS0tIAogICAgQ1BVIFRp
bWUgICAgICAgICAgICAgID0gTWF4OiBVTkxJTUlURUQgV2FybjogVU5MSU1JVEVEIAogICAgTWVtb3J5IFNpemUgICAgICAgICAg
ID0gTWF4OiBVTkxJTUlURUQgV2FybjogVU5MSU1JVEVEIAogICAgVmlydHVhbCBNZW1vcnkgU2l6ZSAgID0gTWF4OiBVTkxJTUlU
RUQgV2FybjogVU5MSU1JVEVEIAogICAgVkUgQ1BVIFRpbWUgICAgICAgICAgID0gTWF4OiBVTkxJTUlURUQgV2FybjogVU5MSU1J
VEVEIAogICAgVkUgTWVtb3J5IFNpemUgICAgICAgID0gTWF4OiBVTkxJTUlURUQgV2FybjogVU5MSU1JVEVEIAogICAgU3Rkb3V0
IFNpemUgICAgICAgICAgID0gTWF4OiBVTkxJTUlURUQgV2FybjogVU5MSU1JVEVEIAogICAgU3RkZXJyIFNpemUgICAgICAgICAg
ID0gTWF4OiBVTkxJTUlURUQgV2FybjogVU5MSU1JVEVEIAogIFZFIE5vZGUgUmVzb3VyY2VzOgogICAgVkUgQ1BVIFRpbWUgICAg
ICAgICAgID0gTWF4OiBVTkxJTUlURUQgV2FybjogVU5MSU1JVEVEIAogICAgVkUgTWVtb3J5IFNpemUgICAgICAgID0gTWF4OiBV
TkxJTUlURUQgV2FybjogVU5MSU1JVEVEIAogIFJlc291cmNlcyBMaW1pdHM6CiAgICAoUGVyLVJlcSkgRWxhcHNlIFRpbWUgTGlt
aXQgICAgICAgPSBNYXg6ICAgICA3MjAwUyBXYXJuOiAgICAgNzIwMFMgCiAgICAoUGVyLUpvYikgQ1BVIFRpbWUgICAgICAgICAg
ICAgICAgPSBNYXg6IFVOTElNSVRFRCBXYXJuOiBVTkxJTUlURUQgCiAgICAoUGVyLUpvYikgQ1BVIE51bWJlciAgICAgICAgICAg
ICAgPSBNYXg6ICAgICAgICA0OCBXYXJuOiAgICAgICAtLS0gCiAgICAoUGVyLUpvYikgTWVtb3J5IFNpemUgICAgICAgICAgICAg
PSBNYXg6IFVOTElNSVRFRCBXYXJuOiBVTkxJTUlURUQgCiAgICAoUGVyLUpvYikgVmlydHVhbCBNZW1vcnkgU2l6ZSAgICAgPSBN
YXg6IFVOTElNSVRFRCBXYXJuOiBVTkxJTUlURUQgCiAgICAoUGVyLUpvYikgR1BVIE51bWJlciAgICAgICAgICAgICAgPSBNYXg6
ICAgICAgICAgMCBXYXJuOiAgICAgICAtLS0gCiAgICAoUGVyLVByYykgQ1BVIFRpbWUgICAgICAgICAgICAgICAgPSBNYXg6IFVO
TElNSVRFRCBXYXJuOiBVTkxJTUlURUQgCiAgICAoUGVyLVByYykgT3BlbiBGaWxlIE51bWJlciAgICAgICAgPSBNYXg6ICAgIDI2
MjE0NCBXYXJuOiAgICAgICAtLS0gCiAgICAoUGVyLVByYykgVmlydHVhbCBNZW1vcnkgU2l6ZSAgICAgPSBNYXg6IFVOTElNSVRF
RCBXYXJuOiBVTkxJTUlURUQgCiAgICAoUGVyLVByYykgRGF0YSBTZWdtZW50IFNpemUgICAgICAgPSBNYXg6IFVOTElNSVRFRCBX
YXJuOiBVTkxJTUlURUQgCiAgICAoUGVyLVByYykgU3RhY2sgU2VnbWVudCBTaXplICAgICAgPSBNYXg6IFVOTElNSVRFRCBXYXJu
OiBVTkxJTUlURUQgCiAgICAoUGVyLVByYykgQ29yZSBGaWxlIFNpemUgICAgICAgICAgPSBNYXg6IFVOTElNSVRFRCBXYXJuOiBV
TkxJTUlURUQgCiAgICAoUGVyLVByYykgUGVybWFuZW50IEZpbGUgU2l6ZSAgICAgPSBNYXg6IFVOTElNSVRFRCBXYXJuOiBVTkxJ
TUlURUQgCiAgICAoUGVyLVByYykgVkUgQ1BVIFRpbWUgICAgICAgICAgICAgPSBNYXg6IFVOTElNSVRFRCBXYXJuOiBVTkxJTUlU
RUQgCiAgICAoUGVyLVByYykgVkUgTWVtb3J5IFNpemUgICAgICAgICAgPSBNYXg6IFVOTElNSVRFRCBXYXJuOiBVTkxJTUlURUQg
CiAgS2VybmVsIFBhcmFtZXRlcjoKICAgIFJlc291cmNlIFNoYXJpbmcgR3JvdXAgICAgID0gMAogICAgTmljZSBWYWx1ZSAgICAg
ICAgICAgICAgICAgPSAwCiAgVXNlciBBdHRyaWJ1dGVzOgogICAgKG5vbmUpCgo=
""")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pbs_directives(path: Path) -> dict[str, str]:
    """shebang 後から最初の実行行までの active directive だけを読む。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].startswith("#!"), f"missing shebang: {path}"
    result = {}
    header_open = True
    commented = re.compile(r"^\s*(?:#{2,}\s*PBS|#\s+#PBS)(?:\s|$)")
    for line_number, line in enumerate(lines[1:], 2):
        if commented.match(line):
            raise AssertionError(f"commented-out PBS directive at {path}:{line_number}")
        if header_open and (not line.strip() or line.startswith("#")):
            if not line.startswith("#PBS "):
                continue
            option, value = line[len("#PBS "):].split(maxsplit=1)
            if option in result:
                raise AssertionError(f"duplicate PBS directive {option} at {path}:{line_number}")
            result[option] = value
            continue
        header_open = False
        if line.startswith("#PBS "):
            raise AssertionError(f"late PBS directive at {path}:{line_number}")
    return result


@pytest.mark.parametrize(
    "name", ["smoke_probe.sh", "submit_certify.sh", "certify_calibration.sh"],
)
def test_shell_syntax(name):
    result = subprocess.run(
        ["bash", "-n", str(TOOL_DIR / name)], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_pbs_directives_match_single_policy_source():
    policy = json.loads((TOOL_DIR / "policy.json").read_text(encoding="utf-8"))
    smoke = _pbs_directives(TOOL_DIR / "smoke_probe.sh")
    certify = _pbs_directives(TOOL_DIR / "certify_calibration.sh")
    for directives in (smoke, certify):
        assert directives["-A"] == policy["project"]
        assert directives["-q"] == policy["queue"]
        assert int(directives["-b"]) == policy["nodes"]
    assert smoke["-l"] == "elapstim_req=" + policy["smoke_walltime"]
    assert certify["-l"] == "elapstim_req=" + policy["certify_walltime"]


@pytest.mark.parametrize("body", [
    "#!/bin/bash\n#PBS -A one\n#PBS -A two\nset -e\n",
    "#!/bin/bash\nset -e\n#PBS -A late\n",
    "#!/bin/bash\n##PBS -A hidden\nset -e\n",
    "#!/bin/bash\n# #PBS -A hidden\nset -e\n",
])
def test_pbs_directive_parser_rejects_duplicate_late_or_commented(tmp_path, body):
    script = tmp_path / "bad.sh"
    script.write_text(body, encoding="utf-8")
    with pytest.raises(AssertionError):
        _pbs_directives(script)


def test_certify_uses_frozen_cli_names_and_reservation_exports():
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    for flag in (
        "--certify", "--receipt-json", "--binary-sha256",
        "--effective-clock-tolerance-pct",
    ):
        assert flag in source
    for field in (
        "JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
        "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE",
    ):
        assert "IZANAGI_RESERVATION_" + field in source
    assert '"required_s": frozen_required_s' in source
    assert "5 * 3 * 120 + 10 * 120 + 2 * 3 * 120 + 960" in source
    assert "build_cap(CCBench=900+gflags=60)(960)" in source
    assert "finalize_reserve(600)=6490" in source
    assert '--numactl "$NUMA_POLICY"' not in source


def test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench():
    policy = json.loads((TOOL_DIR / "policy.json").read_text(encoding="utf-8"))
    assert policy["gflags_source_path"] == "/home/SFC/tanab/github/gflags"
    assert policy["gflags_expected_head"] == (
        "e171aa2d15ed9eb17054558e0b3a6a413bb01067"
    )

    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    gflags_stage = source.index("# (iv-a) pinned-clean gflags")
    ccbench_stage = source.index("# (iv-b) pinned-clean CCBench")
    assert gflags_stage < ccbench_stage
    fragment = source[gflags_stage:ccbench_stage]
    for required in (
        '[[ ! -d "$GFLAGS_SOURCE_PATH" ]]',
        'GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD',
        '[[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]',
        'status --porcelain --untracked-files=all',
        'write_failure 2 gflags "gflags source HEAD mismatch"',
        '-DBUILD_SHARED_LIBS=OFF',
        '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
        '-DREGISTER_INSTALL_PREFIX=OFF',
        '"$ATTEMPT_DIR/gflags-configure.stdout"',
        '"$ATTEMPT_DIR/gflags-configure.stderr"',
        '"$ATTEMPT_DIR/gflags-build.stdout"',
        '"$ATTEMPT_DIR/gflags-build.stderr"',
        '"$ATTEMPT_DIR/gflags-install.stdout"',
        '"$ATTEMPT_DIR/gflags-install.stderr"',
    ):
        assert required in fragment
    configure = source[source.index("configure_argv=(", ccbench_stage):]
    assert '"-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"' in configure
    assert '"-DIZANAGI_GFLAGS_SRC_HEAD=$GFLAGS_SOURCE_HEAD"' in configure


def test_shell_jobs_normalize_qstat_id_and_capture_system_toolchain():
    smoke = (TOOL_DIR / "smoke_probe.sh").read_text(encoding="utf-8")
    certify = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    for source in (smoke, certify):
        assert "QSTAT_JOBID=${PBS_JOBID#0:}" in source
        assert 'qstat -f "$QSTAT_JOBID"' in source
        assert 'qstat -f "$PBS_JOBID"' not in source
    assert "which gcc g++ cmake" in smoke
    assert "toolchain_versions" in smoke
    assert "toolchain_realpaths" in smoke
    assert "proc2_comm cat /proc/2/comm" in smoke
    assert "/proc/1/ns/pid" not in smoke


def _qstat_parser_source() -> str:
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    match = re.search(
        r"readarray -t qstat_values .*?<<'PY'\n(.*?)\nPY\n\)", source, re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def _run_qstat_parser(
        tmp_path: Path, payload: bytes, *, observed: str = "absent-host") -> list[str]:
    fixture = tmp_path / "qstat-f.stdout"
    fixture.write_bytes(payload)
    env = os.environ.copy()
    env["TZ"] = "Asia/Tokyo"
    result = subprocess.run(
        [sys.executable, "-", str(fixture), observed, "0"],
        input=_qstat_parser_source(), capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines()


def test_qstat_parser_accepts_real_nqsv_867863_output(tmp_path):
    assert len(QSTAT_NQSV_867863) == 3872
    assert hashlib.sha256(QSTAT_NQSV_867863).hexdigest() == (
        "20f395d76af89b6a8d6261b6f92982bd374ee49c387141eebf34a13c9228a257"
    )
    assert _run_qstat_parser(tmp_path, QSTAT_NQSV_867863) == [
        "bnode003", "1784394957",
    ]


def test_qstat_parser_skips_none_and_tries_next_key(tmp_path):
    payload = b"""exec_host = (none)
assigned_host = bnode004
stime = (none)
start_time = 1784394957
"""
    assert _run_qstat_parser(tmp_path, payload) == ["bnode004", "1784394957"]


@pytest.mark.parametrize("payload", [
    b"""exec_host = (none)
exec_vnode = (none)
assigned_host = (none)
vnode = (none)
stime = (none)
start_time = (none)
start = (none)
Started Request Time = (none)
Execution Hosts(JSVNO):
    (none)
""",
    b"Request ID: 867863.nqsv\nCurrent State = Running\n",
])
def test_qstat_parser_keeps_unavailable_for_none_or_missing_fields(tmp_path, payload):
    assert _run_qstat_parser(tmp_path, payload) == ["unavailable", "unavailable"]


def test_smoke_toolchain_capture_detects_nonzero_gcc_version(tmp_path):
    """gcc --version の失敗を後続 tool 成功で上書きせず非 0 のまま返す。"""
    source = (TOOL_DIR / "smoke_probe.sh").read_text(encoding="utf-8")
    line = next(
        line for line in source.splitlines()
        if line.startswith("capture_shell toolchain_versions ")
    )
    argv = shlex.split(line)
    assert argv[:2] == ["capture_shell", "toolchain_versions"] and len(argv) == 3
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for tool, rc in (("gcc", 7), ("g++", 0), ("cmake", 0)):
        stub = bindir / tool
        stub.write_text(
            f"#!/bin/sh\nprintf '%s\\n' '{tool} fixture'\nexit {rc}\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = str(bindir)
    result = subprocess.run(
        ["/bin/bash", "-c", argv[2]], capture_output=True, text=True, env=env,
    )
    assert result.returncode == 7


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0:0:X", "0:X"),
        ("00:X", "00:X"),
        ("0:X", "X"),
        ("X", "X"),
    ],
)
def test_normalize_request_id_strips_only_one_exact_zero_prefix(raw, expected):
    if str(REPO / "orchestrator") not in sys.path:
        sys.path.insert(0, str(REPO / "orchestrator"))
    from calibrator.schema_v2 import normalize_request_id

    assert normalize_request_id(raw) == expected


def test_normalize_request_id_rejects_empty_string():
    if str(REPO / "orchestrator") not in sys.path:
        sys.path.insert(0, str(REPO / "orchestrator"))
    from calibrator.schema_v2 import CalibrationSchemaError, normalize_request_id

    with pytest.raises(CalibrationSchemaError):
        normalize_request_id("")


def test_certify_keeps_default_modules_and_uses_system_toolchain():
    certify = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    submit = (TOOL_DIR / "submit_certify.sh").read_text(encoding="utf-8")
    assert "module -t list" in certify
    assert "module purge" not in certify
    assert "module load" not in certify
    assert "PEGASUS_MODULES" not in certify
    assert "PEGASUS_MODULES" not in submit
    assert "--modules" not in submit
    for tool in ("gcc", "g++", "cmake"):
        assert f"command -v {tool}" in certify


@dataclasses.dataclass(frozen=True)
class _ProbeFixture:
    cores: int
    nested: dict


def test_run_probe_fixture_to_stdout_shape_and_file(tmp_path):
    module = _load("probe_entry_fixture", TOOL_DIR / "run_probe.py")
    fake = SimpleNamespace(probe=lambda: _ProbeFixture(cores=7, nested={"ok": True}))
    target = tmp_path / "observation.json"
    rc, payload = module.run(output=target, importer=lambda _: fake)
    assert rc == 0
    assert payload["ok"] is True
    assert payload["profile"] == {"cores": 7, "nested": {"ok": True}}
    assert json.loads(target.read_text(encoding="utf-8")) == payload


def test_run_probe_import_failure_is_structured_and_nonzero(tmp_path):
    module = _load("probe_entry_missing", TOOL_DIR / "run_probe.py")

    def missing(_):
        raise ModuleNotFoundError("fixture module is absent")

    target = tmp_path / "error.json"
    rc, payload = module.run(output=target, importer=missing)
    assert rc != 0
    assert payload["ok"] is False
    assert payload["error"]["stage"] == "import"
    assert json.loads(target.read_text(encoding="utf-8")) == payload


def _collector_fixture(tmp_path: Path, *, pbs_jobid: str | None = None):
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "calibration.json").write_text("{}\n", encoding="utf-8")
    staging = tmp_path / "staging"
    staging.mkdir()
    request_id = "12345.scheduler"
    raw_pbs_jobid = pbs_jobid or request_id
    (staging / "submit-receipt.json").write_text(json.dumps({
        "qsub": {"request_id": request_id},
    }), encoding="utf-8")
    (staging / "acquisition-receipt.json").write_text(json.dumps({
        "allocation": {"pbs_jobid": raw_pbs_jobid},
    }), encoding="utf-8")
    (staging / "job-result.json").write_text(json.dumps({
        "pbs_jobid": raw_pbs_jobid, "calibrate_rc": 0,
    }), encoding="utf-8")
    (staging / "stage.log").write_text("fixture\n", encoding="utf-8")
    file_id = request_id.split(".", 1)[0]
    stdout = tmp_path / ("job.o" + file_id)
    stderr = tmp_path / ("job.e" + file_id)
    stdout.write_text("job output\n", encoding="utf-8")
    stderr.write_text("diagnostic is allowed\nExit_status=0\nwalltime=1\n", encoding="utf-8")
    return attempt, staging, stdout, stderr


def test_collect_receipt_fixture_to_final_json(tmp_path):
    module = _load("collector_entry_fixture", TOOL_DIR / "collect_receipt.py")
    attempt, staging, stdout, stderr = _collector_fixture(tmp_path)
    target = module.collect(
        attempt_dir=attempt, job_staging=staging,
        stdout_path=stdout, stderr_path=stderr,
    )
    doc = json.loads(target.read_text(encoding="utf-8"))
    assert doc["cross_checks"] == {
        "submit_vs_allocation_job_id": True,
        "submit_vs_job_result_job_id": True,
        "scheduler_filenames_carry_job_id": True,
        "scheduler_accounting_present": True,
    }
    assert doc["scheduler_logs"]["accounting_summary_raw"][0] == "Exit_status=0"
    assert any(item["path"] == "stage.log" for item in doc["staging_manifest"])


def test_collect_receipt_accepts_raw_zero_subrequest_prefix(tmp_path):
    module = _load("collector_entry_zero_prefix", TOOL_DIR / "collect_receipt.py")
    attempt, staging, stdout, stderr = _collector_fixture(
        tmp_path, pbs_jobid="0:12345.scheduler")
    target = module.collect(
        attempt_dir=attempt, job_staging=staging,
        stdout_path=stdout, stderr_path=stderr,
    )
    assert target.exists()


@pytest.mark.parametrize("pbs_jobid", ["1:12345.scheduler", "other.scheduler"])
def test_collect_receipt_rejects_other_prefix_and_raw_mismatch(tmp_path, pbs_jobid):
    module = _load("collector_entry_bad_prefix", TOOL_DIR / "collect_receipt.py")
    attempt, staging, stdout, stderr = _collector_fixture(
        tmp_path, pbs_jobid=pbs_jobid)
    with pytest.raises(module.CollectionError, match="job ID mismatch"):
        module.collect(
            attempt_dir=attempt, job_staging=staging,
            stdout_path=stdout, stderr_path=stderr,
        )


def test_collect_receipt_missing_input_is_nonzero(tmp_path, capsys):
    module = _load("collector_entry_missing", TOOL_DIR / "collect_receipt.py")
    attempt, staging, stdout, stderr = _collector_fixture(tmp_path)
    (staging / "job-result.json").unlink()
    rc = module.main([
        "--attempt-dir", str(attempt), "--job-staging", str(staging),
        "--stdout", str(stdout), "--stderr", str(stderr),
    ])
    assert rc != 0
    error = json.loads(capsys.readouterr().err)
    assert error["ok"] is False
    assert not (attempt / "final-receipt.json").exists()


def test_make_acquisition_receipt_round_trip_and_field_drop(tmp_path):
    writer = _load("acquisition_writer_fixture", TOOL_DIR / "make_acquisition_receipt.py")
    if str(ORCHESTRATOR := REPO / "orchestrator") not in sys.path:
        sys.path.insert(0, str(ORCHESTRATOR))
    from calibrator import schema_v2
    from test_schema_v2 import _valid_document

    document = _valid_document()
    built = writer.build(document["acquisition_receipt"])
    document["acquisition_receipt"] = built
    assert schema_v2.validate_calibration_v2(document).quality.status == "accepted"

    dropped = json.loads(json.dumps(built))
    dropped["walltime"].pop("reserve_s")
    with pytest.raises((TypeError, ValueError)):
        writer.build(dropped)
    document["acquisition_receipt"] = dropped
    with pytest.raises(schema_v2.CalibrationSchemaError):
        schema_v2.validate_calibration_v2(document)


def _shell_failure_harness(fragment: str) -> str:
    return """set -Eeuo pipefail
write_failure() {
  python3 - "$ATTEMPT_DIR/failure.json" "$1" "$2" <<'PY'
import json, sys
with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump({"rc": int(sys.argv[2]), "stage": sys.argv[3]}, handle)
PY
}
on_err() {
  rc=$?
  trap - ERR
  write_failure "$rc" shell
  exit "$rc"
}
trap on_err ERR
""" + fragment


def _stub_timeout(tmp_path: Path, rc: int) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    timeout = bindir / "timeout"
    timeout.write_text(f"#!/bin/sh\nexit {rc}\n", encoding="utf-8")
    timeout.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    return env


def _gflags_stage_fragment() -> str:
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    start = source.index("# (iv-a) pinned-clean gflags")
    end = source.index("# (iv-b) pinned-clean CCBench", start)
    return source[start:end]


def test_gflags_missing_source_writes_gflags_failure(tmp_path):
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
GFLAGS_SOURCE_PATH={json.dumps(str(tmp_path / 'absent'))}
GFLAGS_EXPECTED_HEAD={'a' * 40}
"""
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(prefix + _gflags_stage_fragment())],
        capture_output=True, text=True,
    )
    assert result.returncode == 2, result.stderr
    assert json.loads((attempt / "failure.json").read_text())["stage"] == "gflags"


def test_gflags_head_mismatch_writes_gflags_failure(tmp_path):
    source_repo = tmp_path / "gflags"
    source_repo.mkdir()
    subprocess.run(["git", "init", "-q", str(source_repo)], check=True)
    subprocess.run(
        ["git", "-C", str(source_repo), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(source_repo), "config", "user.name", "Fixture"], check=True,
    )
    (source_repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source_repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(source_repo), "commit", "-qm", "fixture"], check=True)

    actual_head = subprocess.run(
        ["git", "-C", str(source_repo), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    expected_head = "0" * 40
    assert actual_head != expected_head
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
GFLAGS_SOURCE_PATH={json.dumps(str(source_repo))}
GFLAGS_EXPECTED_HEAD={expected_head}
"""
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(prefix + _gflags_stage_fragment())],
        capture_output=True, text=True,
    )
    assert result.returncode == 2, result.stderr
    assert json.loads((attempt / "failure.json").read_text())["stage"] == "gflags"


def test_calibrate_failure_survives_err_trap_and_writes_job_result(tmp_path):
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    fragment = source.split("calibrate_rc=0\n", 1)[1]
    fragment = "calibrate_rc=0\n" + fragment.split(
        "# worktree metadata を clean に戻す。", 1)[0]
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
PBS_JOBID=123.server
remaining=30
REPO_ROOT={json.dumps(str(tmp_path))}
BINARY=/unused/binary
BINARY_SHA={'a' * 64}
PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT=5
"""
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(prefix + fragment)],
        capture_output=True, text=True, env=_stub_timeout(tmp_path, 7),
    )
    assert result.returncode == 7, result.stderr
    assert json.loads((attempt / "failure.json").read_text())["stage"] == "calibrate"
    assert json.loads((attempt / "job-result.json").read_text())["calibrate_rc"] == 7


def test_qstat_failure_reaches_allocation_unavailable_path(tmp_path):
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    fragment = source.split("qstat_rc=0\n", 1)[1]
    fragment = "qstat_rc=0\n" + fragment.split(
        'if [[ "$ASSIGNED_HOST" == "$HOSTNAME_SHORT" ]]', 1)[0]
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    prefix = f"ATTEMPT_DIR={json.dumps(str(attempt))}\nPBS_JOBID=0:123.server\n"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    timeout = bindir / "timeout"
    timeout.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$*" >"$STUB_TIMEOUT_ARGS"\nexit 6\n',
        encoding="utf-8",
    )
    timeout.chmod(0o755)
    stub_args = tmp_path / "timeout.args"
    env = os.environ.copy()
    env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    env["STUB_TIMEOUT_ARGS"] = str(stub_args)
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(prefix + fragment)],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 2, result.stderr
    assert stub_args.read_text(encoding="utf-8").strip() == "30 qstat -f 123.server"
    unavailable = json.loads((attempt / "allocation-unavailable.json").read_text())
    assert unavailable["qstat_rc"] == 6
    assert unavailable["pbs_jobid"] == "0:123.server"
    assert json.loads((attempt / "failure.json").read_text())["stage"] == "allocation"


@pytest.mark.parametrize("qsub_id,pbs_jobid,accepted", [
    ("123.server", "0:123.server", True),
    ("123.server", "1:123.server", False),
    ("123.server", "124.server", False),
])
def test_certify_submit_binding_uses_narrow_request_id_normalization(
        tmp_path, qsub_id, pbs_jobid, accepted):
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    start = source.index('python3 - "$ATTEMPT_DIR/submit-receipt.json"')
    end = source.index("\n\n# (ii) allocation receipt", start)
    fragment = source[start:end]
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    commit = "a" * 40
    script_sha = "b" * 64
    receipt = {
        "dry_run": False,
        "source_commit": commit,
        "job_script_sha256": script_sha,
        "qsub": {
            "request_id": qsub_id, "project": "SFC", "queue": "gen_S",
            "nodes": 1, "elapstim_req_s": 7200,
        },
    }
    (attempt / "submit-receipt.json").write_text(
        json.dumps(receipt), encoding="utf-8")
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
CURRENT_COMMIT={commit}
CURRENT_SCRIPT_SHA={script_sha}
PBS_JOBID={pbs_jobid}
PROJECT=SFC
QUEUE=gen_S
NODES=1
REQUESTED_S=7200
REPO_ROOT={json.dumps(str(REPO))}
"""
    result = subprocess.run(
        ["bash", "-c", prefix + fragment], capture_output=True, text=True,
    )
    assert (result.returncode == 0) is accepted, result.stderr


def test_submit_dry_run_does_not_resolve_cluster_commands(tmp_path):
    # clean temporary git fixture を使い、実 repository/output と scheduler に触れない。
    fixture_repo = tmp_path / "repo"
    fixture_tools = fixture_repo / "tools" / TOOL_DIR.name
    fixture_tools.parent.mkdir(parents=True)
    shutil.copytree(TOOL_DIR, fixture_tools)
    subprocess.run(["git", "init", "-q", str(fixture_repo)], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "config", "user.email", "fixture@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "config", "user.name", "Fixture"], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "commit", "-qm", "fixture"], check=True)
    attempts = tmp_path / "attempts"
    env = os.environ.copy()
    # qstat 等が PATH に存在しても dry-run が起動しないことは capture 内容で確認する。
    result = subprocess.run([
        "bash", str(fixture_tools / "submit_certify.sh"),
        "--repo-root", str(fixture_repo),
        "--attempts-root", str(attempts),
        "--effective-clock-tolerance-pct", "1.5",
        "--dry-run",
    ], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    assert "qsub command:" in result.stdout
    receipts = list((attempts / "submissions").glob("*/submit-receipt.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert receipt["dry_run"] is True
    assert all(item["rc"] == 0 for item in receipt["preflight"].values())


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
