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
SHARED_POLICY = TOOL_DIR / "policy.json"
CALIBRATION_POLICY = TOOL_DIR / "policies" / "calibration_v1.json"

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


def _hms_seconds(value: str) -> int:
    parts = value.split(":")
    assert len(parts) == 3, value
    hours, minutes, seconds = (int(part) for part in parts)
    assert hours >= 0 and 0 <= minutes < 60 and 0 <= seconds < 60, value
    return hours * 3600 + minutes * 60 + seconds


@pytest.mark.parametrize(
    "name", ["smoke_probe.sh", "submit_certify.sh", "certify_calibration.sh"],
)
def test_shell_syntax(name):
    result = subprocess.run(
        ["bash", "-n", str(TOOL_DIR / name)], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_pbs_directives_match_shared_and_calibration_policies():
    shared_policy = json.loads(SHARED_POLICY.read_text(encoding="utf-8"))
    calibration_policy = json.loads(
        CALIBRATION_POLICY.read_text(encoding="utf-8")
    )
    smoke = _pbs_directives(TOOL_DIR / "smoke_probe.sh")
    certify = _pbs_directives(TOOL_DIR / "certify_calibration.sh")
    for directives in (smoke, certify):
        assert directives["-A"] == shared_policy["project"]
        assert directives["-q"] == shared_policy["queue"]
        assert int(directives["-b"]) == shared_policy["nodes"]
    assert (
        smoke["-l"]
        == "elapstim_req=" + calibration_policy["smoke_walltime"]
    )
    assert (
        certify["-l"]
        == "elapstim_req=" + calibration_policy["certify_walltime"]
    )
    assert (
        _hms_seconds(calibration_policy["smoke_walltime"])
        == calibration_policy["smoke_walltime_s"]
    )
    assert (
        _hms_seconds(calibration_policy["certify_walltime"])
        == calibration_policy["certify_walltime_s"]
    )
    certify_source = (TOOL_DIR / "certify_calibration.sh").read_text(
        encoding="utf-8"
    )
    formula_reserves = {
        int(value)
        for value in re.findall(r"finalize_reserve\((\d+)\)", certify_source)
    }
    assert formula_reserves
    assert formula_reserves == {calibration_policy["finalize_reserve_s"]}
    assert (
        calibration_policy["finalize_reserve_s"]
        < calibration_policy["certify_walltime_s"]
    )


@pytest.mark.parametrize(
    "name", ["certify_calibration.sh", "submit_certify.sh"],
)
def test_certify_calibration_policy_check_rejects_symlinks(name):
    source = (TOOL_DIR / name).read_text(encoding="utf-8")
    assert (
        'if [[ ! -f "$CALIBRATION_POLICY" || -L "$CALIBRATION_POLICY" ]]; then'
        in source
    )


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
    for flag in ("--certify", "--receipt-json", "--binary-sha256"):
        assert flag in source
    assert "--effective-clock-tolerance-pct" not in source
    assert "legacy effective clock tolerance input is forbidden" in source
    for field in (
        "JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
        "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE",
    ):
        assert "IZANAGI_RESERVATION_" + field in source
    assert '"required_s": frozen_required_s' in source
    assert (
        "frozen_required_s = 10 + 1200 + 5 * 3 * 120 + 10 * 120 "
        "+ 2 * 3 * 120 + 1080 + int(reserve_s)"
    ) in source
    assert '''walltime_formula = (
    "TSC(10)+cooldown_max(1200)+points(5)*sweep_reps(3)*120+"
    "noise_reps(10)*120+2*sweep_reps(3)*120+"
    "reservation_allocation(1080)+finalize_reserve(600)=6610; "
    "1080 is a reservation allocation, not a sequential bound. "
    "The former build_cap breakdown does not match the commands: "
    "gflags configure/build/install=3*60=180s; "
    "glog configure/build/install=3*120=360s; "
    "CCBench configure+build=2*900=1800s. "
    "This allocation excludes third-party copy(360), pristine verification(120), "
    "attestation probes(240), qstat(30), binary hash+nm(120), perf(40). "
    "Pre-measurement timeout values sum to 3250s; with CLI reservation(4990) "
    "and finalize reserve: 3250 + 4990 + 600 = 8840 > 7200; "
    "completion of the maximum path is not guaranteed. "
    "8840 itself is not an upper bound: it excludes operations without timeout "
    "(git status, git worktree add, full /proc scan, worktree removal, "
    "receipt I/O and fsync, submit receipt wait of up to 60 sleep 1 calls). "
    "CLI 2*sweep_reps*120 is a reservation constant not executed in certify "
    "(orchestrator/calibrator/sweep.py returns before scale measurement). "
    "An attempt interrupted before measurement completion does not newly "
    "assemble accepted output from partial samples; however, TERM after "
    "publication can leave accepted published artifacts while the wrapper "
    "exits nonzero. This is an existing limitation, not introduced by this change."
)''' in source
    assert "finalize_reserve(600)=6610" in source
    assert '--numactl "$NUMA_POLICY"' not in source


def test_exec_calibrate_execs_valid_argv(tmp_path):
    argv_path = tmp_path / "argv.json"
    argv_path.write_text(
        json.dumps(["/bin/echo", "safe", "argv with spaces"]), encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(TOOL_DIR / "exec_calibrate.py"), str(argv_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "safe argv with spaces\n"


@pytest.mark.parametrize("fixture", ["missing", "invalid"])
def test_exec_calibrate_rejects_missing_or_invalid_json(tmp_path, fixture):
    argv_path = tmp_path / "argv.json"
    if fixture == "invalid":
        argv_path.write_text("{not-json\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(TOOL_DIR / "exec_calibrate.py"), str(argv_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def _calibrate_timeout_command(source: str) -> str:
    match = re.search(
        r"^timeout --signal=TERM .*?(?=\n\s*\|\| calibrate_rc=\$\?)",
        source,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match.group(0)


def _calibrate_interpreter_fragment() -> str:
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    selection_start = source.index('CALIBRATE_PYTHON=""')
    failure_start = source.index(
        'if [[ -z "$CALIBRATE_PYTHON" ]]; then', selection_start,
    )
    selection_end = source.index("\nfi", failure_start) + len("\nfi")
    selection = source[selection_start:selection_end]
    shim_start = source.index(
        'CALIBRATE_PATH="$TMPDIR/bin:$(dirname "$CALIBRATE_PYTHON"):$PATH"',
        selection_end,
    )
    shim_end = source.index("\n", shim_start)
    return selection + "\n" + source[shim_start:shim_end] + "\n"


def test_certify_calibrator_resolves_and_shims_versioned_interpreter(tmp_path):
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    fragment = _calibrate_interpreter_fragment()
    for unrelated in (
        "GFLAGS_SOURCE_PATH",
        "GLOG_SOURCE_PATH",
        "run_condition_gate",
        "PERF_EVENTS",
    ):
        assert unrelated not in fragment
    assert source.index("python3.10 /usr/bin/python3.10 /bin/python3.10") < source.index(
        'CALIBRATE_PATH="$TMPDIR/bin:$(dirname "$CALIBRATE_PYTHON"):$PATH"'
    )
    assert (
        'if "$resolved" -I -B -c \\\n'
        "      'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)'"
        in fragment
    )
    assert 'write_failure 2 interpreter \\\n' in fragment
    assert 'python3 "$REPO_ROOT/orchestrator/calibrate.py"' not in source
    assert '"$CALIBRATE_PYTHON" "$REPO_ROOT/orchestrator/calibrate.py"' in source

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_python = fake_bin / "python3.10"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_python.chmod(0o755)
    scratch = tmp_path / "scratch"
    prefix = f"""ATTEMPT_DIR={shlex.quote(str(tmp_path / 'attempt'))}
TMPDIR={shlex.quote(str(scratch))}
PATH={shlex.quote(str(fake_bin) + os.pathsep + '/usr/bin')}
CALIBRATE_PATH="$TMPDIR/bin:$PATH"
"""
    (tmp_path / "attempt").mkdir()
    suffix = "printf '%s\\n' \"$CALIBRATE_PYTHON\" \"$CALIBRATE_PATH\"\n"
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(prefix + fragment + suffix)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    selected, path = result.stdout.splitlines()
    assert selected == str(fake_python)
    assert path.split(os.pathsep)[:2] == [str(scratch / "bin"), str(fake_bin)]


def test_certify_calibrator_interpreter_resolution_fails_closed(tmp_path):
    fragment = _calibrate_interpreter_fragment()
    missing_usr = tmp_path / "missing-usr-python3.10"
    missing_bin = tmp_path / "missing-bin-python3.10"
    fragment = fragment.replace("/usr/bin/python3.10", str(missing_usr))
    fragment = fragment.replace("/bin/python3.10", str(missing_bin))

    writer_bin = tmp_path / "writer-bin"
    writer_bin.mkdir()
    writer_python = shutil.which("python3")
    assert writer_python is not None
    (writer_bin / "python3").symlink_to(writer_python)
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    prefix = f"""ATTEMPT_DIR={shlex.quote(str(attempt))}
TMPDIR={shlex.quote(str(tmp_path / 'scratch'))}
PATH={shlex.quote(str(writer_bin))}
"""
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(prefix + fragment)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2, result.stderr
    assert json.loads((attempt / "failure.json").read_text()) == {
        "rc": 2,
        "stage": "interpreter",
    }


def test_certify_calibrate_timeout_argv_cannot_self_match_ycsb_probe():
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    command = _calibrate_timeout_command(source)
    assert 'python3 "$TOOLS/exec_calibrate.py" "$CALIBRATE_ARGV_JSON"' in command
    assert re.search(r"ycsb", command, re.IGNORECASE) is None
    assert '"$BINARY"' not in command


def test_certify_perf_stage_is_policy_driven_fail_closed_and_precedes_calibrate():
    policy = json.loads((TOOL_DIR / "policy.json").read_text(encoding="utf-8"))
    assert policy["perf_candidates"] == [
        "/usr/lib/linux-tools/5.15.0-135-generic/perf",
        "/usr/lib/linux-tools/5.15.0-100-generic/perf",
    ]
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    perf_stage = source.index("# (vii) policy-pinned perf dispatcher bypass")
    calibrate_stage = source.index("CALIBRATE_ARGV_JSON=", perf_stage)
    assert perf_stage < calibrate_stage
    fragment = source[perf_stage:calibrate_stage]
    for required in (
        'PERF_CANDIDATES=("${policy_values[@]:9}")',
        'target.id == "PERF_EVENTS"',
        'stat -e "$PERF_EVENTS" -- sleep 0.1',
        "grep -Eqi '<not (supported|counted)>'",
        'ln -s "$PERF_SELECTED_REAL" "$TMPDIR/bin/perf"',
    ):
        assert required in source
    assert 'env "PATH=$CALIBRATE_PATH"' in source[calibrate_stage:]
    selected = fragment.index('if [[ -n "$PERF_SELECTED" ]]; then')
    selected_end = fragment.index('\nfi', selected)
    for output in ('"$ATTEMPT_DIR/perf-selection.json"',
                   'ln -s "$PERF_SELECTED_REAL" "$TMPDIR/bin/perf"'):
        assert selected < fragment.index(output) < selected_end
    final_path = fragment.rindex('CALIBRATE_PATH=')
    probe = fragment.index('receipt = probe_perf_availability(')
    decision = fragment.index('print(int(use_perf_from_receipt(receipt)))')
    assert selected_end < probe < decision
    assert final_path < fragment.index('env "PATH=$CALIBRATE_PATH"') < probe
    assert fragment.count('receipt = probe_perf_availability(') == 1
    assert '); then\n  write_failure 2 perf "canonical perf preflight failed"\n  exit 2\nfi' in fragment
    argv_fragment = source[calibrate_stage:source.index('\ncalibrate_rc=0', calibrate_stage)]
    assert ('if [[ "$USE_PERF" == 0 ]]; then\n'
            '  calibrate_argv+=(--perf-preflight-json "$PERF_PREFLIGHT_RECEIPT")\nfi') in argv_fragment


def _perf_stage_fragment() -> str:
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    start = source.index("# (vii) policy-pinned perf dispatcher bypass")
    end = source.index("\ncalibrate_rc=0", start)
    return source[start:end]


def _run_perf_stage(tmp_path: Path, candidates: list[Path], literal_status: str):
    """Run certify_calibration.sh selection, canonical probe and argv generation."""
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    base = tmp_path / "base"
    base.mkdir()
    # Isolate Python's directory too, so host perf cannot enter the final PATH.
    for name in ("python3", "dirname", "timeout", "grep", "realpath", "cat", "mkdir", "ln", "env"):
        executable = sys.executable if name == "python3" else shutil.which(name)
        assert executable is not None
        (base / name).symlink_to(executable)
    literal = base / "perf"
    literal.write_text(
        f"#!{sys.executable}\n"
        "import os, signal, sys\n"
        f"status = {literal_status!r}\n"
        "if status == 'probe_error':\n"
        "    # SIGKILL cannot inherit an ignored or blocked signal disposition.\n"
        "    os.kill(os.getpid(), signal.SIGKILL)\n"
        "if status == 'unavailable':\n"
        "    sys.exit(2)\n"
        "if '--version' in sys.argv:\n"
        "    print('perf version fixture')\n"
        "elif '-o' in sys.argv:\n"
        "    events = sys.argv[sys.argv.index('-e') + 1].split(',')\n"
        "    with open(sys.argv[sys.argv.index('-o') + 1], 'w') as out:\n"
        "        out.write(''.join('1,,' + event + '\\n' for event in events))\n",
        encoding="utf-8",
    )
    literal.chmod(0o755)
    quoted_candidates = " ".join(shlex.quote(str(path)) for path in candidates)
    prefix = f"""ATTEMPT_DIR={shlex.quote(str(attempt))}
TMPDIR={shlex.quote(str(scratch))}
REPO_ROOT={shlex.quote(str(REPO))}
CALIBRATE_PYTHON={shlex.quote(str(base / 'python3'))}
export PATH={shlex.quote(str(base))}
CALIBRATION_RRATIO=50
BINARY=/unused/binary
BINARY_SHA={'a' * 64}
PERF_CANDIDATES=({quoted_candidates})
"""
    result = subprocess.run(
        ["/bin/bash", "-c", _shell_failure_harness(prefix + _perf_stage_fragment())],
        capture_output=True, text=True,
    )
    return result, attempt


@pytest.mark.parametrize("literal_status", ["unavailable", "available", "probe_error"])
def test_perf_stage_all_candidates_failed_uses_canonical_receipt(tmp_path, literal_status):
    result, attempt = _run_perf_stage(
        tmp_path, [tmp_path / "missing-one", tmp_path / "missing-two"], literal_status,
    )
    assert result.returncode == (2 if literal_status == "probe_error" else 0), result.stderr
    assert json.loads((attempt / "perf-preflight.json").read_text())["status"] == literal_status
    assert not (attempt / "perf-selection.json").exists()
    assert not (tmp_path / "scratch/bin/perf").is_symlink()
    assert not (tmp_path / "scratch/bin/perf").exists()
    if literal_status == "probe_error":
        assert json.loads((attempt / "failure.json").read_text()) == {"rc": 2, "stage": "perf"}
        assert not (attempt / "calibrate-argv.json").exists()
        return
    assert not (attempt / "failure.json").exists()
    argv = json.loads((attempt / "calibrate-argv.json").read_text())
    if literal_status == "unavailable":
        assert argv[-2:] == ["--perf-preflight-json", str(attempt / "perf-preflight.json")]
    else:
        assert "--perf-preflight-json" not in argv


@pytest.mark.parametrize("literal_status", ["unavailable", "available"])
def test_perf_stage_rejects_not_supported_smoke_output(tmp_path, literal_status):
    unsupported = tmp_path / "unsupported-perf"
    unsupported.write_text(
        """#!/bin/sh
if [ "$1" = "--version" ]; then
  echo 'perf version fixture'
  exit 0
fi
echo '<not supported>' >&2
exit 0
""",
        encoding="utf-8",
    )
    unsupported.chmod(0o755)
    result, attempt = _run_perf_stage(
        tmp_path, [unsupported, tmp_path / "missing-second"], literal_status,
    )
    assert result.returncode == 0, result.stderr
    assert not (attempt / "failure.json").exists()
    assert "<not supported>" in (attempt / "perf-candidate-0.smoke").read_text()
    assert not (attempt / "perf-selection.json").exists()
    assert not (tmp_path / "scratch/bin/perf").is_symlink()
    assert not (tmp_path / "scratch/bin/perf").exists()
    assert json.loads((attempt / "perf-preflight.json").read_text())["status"] == literal_status
    argv = json.loads((attempt / "calibrate-argv.json").read_text())
    if literal_status == "unavailable":
        assert argv[-2:] == ["--perf-preflight-json", str(attempt / "perf-preflight.json")]
    else:
        assert "--perf-preflight-json" not in argv


def test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench():
    # Every shell consumer resolves the hydrated source before passing it to
    # git/build. Keep this alongside the existing configure/prefix contract.
    for name, repo_var, source_var in (
        ("a5_second_boot_backoff_sweep.sh", "REPO_BASE", "SOURCE"),
        ("b10_backoff_grid.sh", "REPO_ROOT", "SOURCE"),
        ("certify_calibration.sh", "REPO_ROOT", "SOURCE_PATH"),
        ("floor_campaign.sh", "REPO_ROOT", "SOURCE_PATH"),
        ("floor_scoping.sh", "REPO_ROOT", "SOURCE_PATH"),
        ("mocc_trace_pilot.sh", "REPO_ROOT", "SOURCE_PATH"),
        ("oracle_n_pilot.sh", "REPO_ROOT", "SOURCE_PATH"),
        ("p3_s4_loop_pegasus.sh", "repo", "SOURCE_PATH"),
        ("paper_story_a1_paired.sh", "REPO_ROOT", "SOURCE_PATH"),
        ("silo_ladder_rung1.sh", "REPO_ROOT", "SOURCE"),
        ("t126_qualification.sh", "REPO_ROOT", "SOURCE"),
        ("t141_region_profile.sh", "IZANAGI_ROOT", "SOURCE_PATH"),
        ("probes/t1683_rr5_cost_probe.pbs", "REPO_ROOT", "SOURCE_PATH"),
        ("probes/t2187_adaptive_const_probe.pbs", "REPO_ROOT", "SOURCE_PATH"),
        ("probes/t2228_driver_gate_liveness_probe.pbs", "REPO_ROOT", "SOURCE_PATH"),
    ):
        job = (TOOL_DIR / name).read_text(encoding="utf-8")
        resolution = (
            'THIRDPARTY_SOURCE_ROOT="$THIRD_PARTY_SOURCE_ROOT"'
            if name == "mocc_trace_pilot.sh" else
            'THIRDPARTY_SOURCE_ROOT="$IZANAGI_S4_THIRDPARTY_SOURCE_ROOT"'
            if name == "p3_s4_loop_pegasus.sh" else
            'THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$'
            + repo_var + '/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"'
        )
        assert job.count(resolution) == 1, name
        if name == "mocc_trace_pilot.sh":
            hydrate = 'timeout 20 "$HYDRATE_PY" "$TOOLS/fetch_third_party.py" hydrate --repo-root "$REPO_ROOT"'
            assert job.count(hydrate) == 1
            cache_check = (
                'CACHE_ROOT=${!THIRD_PARTY_CACHE_ENV:-}\n'
                'if [[ -z "$CACHE_ROOT" ]]; then\n'
                '  write_failure 2 third_party "$THIRD_PARTY_CACHE_ENV is missing"\n'
                '  exit 2\nfi'
            )
            assert cache_check in job
            root_read = 'THIRD_PARTY_SOURCE_ROOT=$(python3 - "$ATTEMPT_DIR/third-party-hydrate.json"'
            hydrate_body = job[job.index(cache_check):job.index(resolution)]
            for required in (
                'THIRD_PARTY_STAGING_ROOT="$TMPDIR/thirdparty-src"',
                '--cache-root "$CACHE_ROOT" --staging-root "$THIRD_PARTY_STAGING_ROOT"',
                '>"$ATTEMPT_DIR/third-party-hydrate.json"',
                '2>"$ATTEMPT_DIR/third-party-hydrate.stderr"',
                'value = payload.get("source_root")',
                'if type(value) is not str or not os.path.isabs(value):',
                '    raise SystemExit("hydrate output .source_root is not an absolute path")',
                'print(value)',
                'if [[ ! -d "$THIRD_PARTY_SOURCE_ROOT" ]]; then\n'
                '  write_failure 2 third_party "hydrate source_root is missing"\n'
                '  exit 2\nfi',
            ):
                assert hydrate_body.count(required) == 1, required
            assert (job.index("# END T1718 COMPILER VERSION BODY GATE")
                    < job.index(cache_check)
                    < job.index("# BEGIN T2780 HYDRATE INTERPRETER GATE")
                    < job.index("# END T2780 HYDRATE INTERPRETER GATE")
                    < job.index(hydrate)
                    < job.index(root_read) < job.index(resolution))
            assert "IZANAGI_THIRDPARTY_SOURCE_ROOT" not in job
            assert "job-staging/thirdparty-src" not in job
        for dep in ("gflags", "glog"):
            assignment = f'{dep.upper()}_{source_var}="$THIRDPARTY_SOURCE_ROOT/{dep}"'
            assert job.count(assignment) == 1, name
            assert job.index(resolution) < job.index(assignment), name
            if name == "mocc_trace_pilot.sh":
                assert (job.index(assignment)
                        < job.index(f'if [[ ! -d "${dep.upper()}_SOURCE_PATH" ]]; then')
                        < job.index(f'git -C "${dep.upper()}_SOURCE_PATH" rev-parse HEAD'))
            assert f'"{dep}_source_path"' not in job, name
            if name == "t126_qualification.sh":
                archive = f'git -C "${dep.upper()}_SOURCE" archive --format=tar'
                staged = f'{dep.upper()}_SOURCE="${dep.upper()}_STAGE"'
                configure = f'"$CMAKE_REAL" -S "${dep.upper()}_SOURCE"'
                assert (job.index(assignment) < job.index(archive)
                        < job.index(staged) < job.index(configure)), name
            else:
                configure = f'cmake -S "${dep.upper()}_{source_var}"'
                if name in ("certify_calibration.sh", "t141_region_profile.sh"):
                    configure = f'"$CMAKE_PATH" -S "${dep.upper()}_{source_var}"'
                assert job.index(assignment) < job.index(configure), name
    policy = json.loads((TOOL_DIR / "policy.json").read_text(encoding="utf-8"))
    assert policy["gflags_source_url"] == "https://github.com/gflags/gflags.git"
    assert policy["gflags_expected_head"] == (
        "e171aa2d15ed9eb17054558e0b3a6a413bb01067"
    )

    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    gflags_stage = source.index("# (iv-a) pinned-clean gflags")
    glog_stage = source.index("# (iv-b) pinned-clean glog")
    assert gflags_stage < glog_stage
    fragment = source[gflags_stage:glog_stage]
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
    configure = source[source.index("configure_argv=(", glog_stage):]
    assert '"-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"' in configure
    assert '"-DIZANAGI_GFLAGS_SRC_HEAD=$GFLAGS_SOURCE_HEAD"' in configure


def test_certify_glog_stage_is_pinned_fail_closed_and_precedes_ccbench():
    policy = json.loads((TOOL_DIR / "policy.json").read_text(encoding="utf-8"))
    assert policy["glog_source_url"] == "https://github.com/google/glog.git"
    assert policy["glog_expected_head"] == (
        "8f9ccfe770add9e4c64e9b25c102658e3c763b73"
    )

    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    gflags_stage = source.index("# (iv-a) pinned-clean gflags")
    glog_stage = source.index("# (iv-b) pinned-clean glog")
    ccbench_stage = source.index("# (iv-c) pinned-clean CCBench")
    assert gflags_stage < glog_stage < ccbench_stage
    fragment = source[glog_stage:ccbench_stage]
    for required in (
        '[[ ! -d "$GLOG_SOURCE_PATH" ]]',
        'GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD',
        '[[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]',
        'status --porcelain --untracked-files=all',
        'write_failure 2 glog "glog source HEAD mismatch"',
        '-DBUILD_SHARED_LIBS=OFF',
        '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
        '-DWITH_GTEST=OFF',
        '-DBUILD_TESTING=OFF',
        '-DWITH_UNWIND=OFF',
        '"-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"',
        '"$ATTEMPT_DIR/glog-configure.stdout"',
        '"$ATTEMPT_DIR/glog-configure.stderr"',
        '"$ATTEMPT_DIR/glog-build.stdout"',
        '"$ATTEMPT_DIR/glog-build.stderr"',
        '"$ATTEMPT_DIR/glog-install.stdout"',
        '"$ATTEMPT_DIR/glog-install.stderr"',
    ):
        assert required in fragment
    configure = source[source.index("configure_argv=(", ccbench_stage):]
    assert '"-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"' in configure
    assert '"-DIZANAGI_GLOG_SRC_HEAD=$GLOG_SOURCE_HEAD"' in configure


def test_certify_cmake_paths_derive_from_colon_free_job_tmpdir():
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    assert 'export TMPDIR="/scr/${PBS_JOBID//:/_}"' in source
    assert 'export TMPDIR="/scr/$PBS_JOBID"' not in source
    assert 'ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"' in source

    cmake_paths = {
        "GFLAGS_BUILD_DIR": "$TMPDIR/gflags-build",
        "GFLAGS_INSTALL_DIR": "$TMPDIR/gflags-install",
        "GLOG_BUILD_DIR": "$TMPDIR/glog-build",
        "GLOG_INSTALL_DIR": "$TMPDIR/glog-install",
        "BUILD_SOURCE": "$TMPDIR/ccbench-source",
        "BUILD_DIR": "$TMPDIR/ccbench-build",
    }
    for name, value in cmake_paths.items():
        assert f'{name}="{value}"' in source
    expected_cmake_arrays = {
        "gflags_configure_argv",
        "gflags_build_argv",
        "gflags_install_argv",
        "glog_configure_argv",
        "glog_build_argv",
        "glog_install_argv",
        "configure_argv",
        "build_argv",
    }
    cmake_path_arrays = re.findall(
        r'(?m)^[ \t]*([a-z_]+_argv)=\("\$CMAKE_PATH"(?=[ \n])', source,
    )
    # build_argv has one assignment in each of the three protocol branches.
    assert len(cmake_path_arrays) == 10
    assert set(cmake_path_arrays) == expected_cmake_arrays
    assert not re.findall(
        r"(?m)^[ \t]*([a-z_]+_argv)=\(cmake(?=[ \n])", source,
    )
    for required in (
        '"-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"',
        '"-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"',
        '"-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"',
    ):
        assert required in source


def test_certify_colon_job_id_creates_colon_free_job_tmpdir(tmp_path):
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    fragment = source[:source.index("\nREPO_ROOT=")]
    scr_root = tmp_path / "scr"
    scr_root.mkdir()
    fragment = fragment.replace("/scr/", str(scr_root) + "/")
    fragment += '\nprintf "%s\\n" "$TMPDIR"\n'
    env = os.environ.copy()
    env.update({
        "PBS_JOBID": "0:1234.nqsv",
        "PBS_O_WORKDIR": str(tmp_path),
    })
    result = subprocess.run(
        ["bash", "-c", fragment], capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stderr
    job_tmpdir = Path(result.stdout.strip())
    assert job_tmpdir == scr_root / "0_1234.nqsv"
    assert ":" not in str(job_tmpdir)
    assert job_tmpdir.is_dir()


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
    env["PYTHONDONTWRITEBYTECODE"] = "1"
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
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from orchestrator.calibrator.schema_v2 import normalize_request_id

    assert normalize_request_id(raw) == expected


def test_normalize_request_id_rejects_empty_string():
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from orchestrator.calibrator.schema_v2 import (
        CalibrationSchemaError,
        normalize_request_id,
    )

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


def _acquisition_candidate_source() -> str:
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    match = re.search(
        r"python3 - \"\$ATTEMPT_DIR\" .*? <<'PY'\n(.*?)\nPY\n",
        source,
        re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def test_known_values_cpu_policy_and_comparison_use_normalized_exact_match():
    policy = json.loads((TOOL_DIR / "policy.json").read_text(encoding="utf-8"))
    expected_cpu = policy["expected_cpu_model"]
    assert expected_cpu == "Intel Xeon Platinum 8468"
    assert "(R)" not in expected_cpu
    assert "(TM)" not in expected_cpu

    source = _acquisition_candidate_source()
    assert "known_passed = (expected_cpu == model and" in source
    assert "expected_cpu in model" not in source


def _acquisition_probe_document(model: str) -> dict:
    registered = next(
        (REPO / "output/env/pegasus/calibration/registered").glob(
            "calibration-*.json"
        )
    )
    calibration = json.loads(registered.read_text(encoding="utf-8"))
    profile = calibration["attestation_profile"]
    del profile["effective_clock"]["tolerance_pct"]
    profile["cpu"]["model_name_raw"] = model
    profile["cpu"]["model_name_normalized"] = model
    return {
        "schema_version": "pegasus-probe-output/v2",
        "ok": True,
        "observed_epoch": 1,
        "profile": profile,
    }


def _write_acquisition_fixture(attempt: Path, model: str) -> None:
    attempt.mkdir()
    (attempt / "submit-receipt.json").write_text(
        json.dumps({"qsub": {"request_id": "fixture.server"}}), encoding="utf-8",
    )
    (attempt / "topology.json").write_text(
        json.dumps({"cpuset_size": 48, "ht_off": True}), encoding="utf-8",
    )
    (attempt / "attestation-pre.json").write_text(
        json.dumps(_acquisition_probe_document(model)), encoding="utf-8",
    )
    (attempt / "module-list.stdout").write_text(
        "intelpython/2022.3.1\n", encoding="utf-8",
    )
    (attempt / "module-list.stderr").write_text("", encoding="utf-8")
    for name, value in (
        ("compiler.path", "/usr/bin/g++"),
        ("compiler.version", "g++ fixture"),
        ("cmake.version", "cmake fixture"),
    ):
        (attempt / name).write_text(value + "\n", encoding="utf-8")


def _acquisition_argv(attempt: Path) -> list[str]:
    policy = json.loads((TOOL_DIR / "policy.json").read_text(encoding="utf-8"))
    return [
        sys.executable, "-", str(attempt), "a" * 40, "b" * 64, "c" * 64,
        "bnode003", "bnode003", policy["expected_cpu_model"], "48", "7200",
        "600", "cmake -S source -B build", "cmake --build build", str(REPO),
    ]


@pytest.mark.parametrize(
    "model,expected_passed",
    [
        ("Intel Xeon Platinum 8468", True),
        ("Intel Xeon Platinum 8468H", False),
    ],
)
def test_known_values_cpu_check_rejects_nearby_sku(
        tmp_path, model, expected_passed):
    attempt = tmp_path / "attempt"
    _write_acquisition_fixture(attempt, model)
    env = os.environ.copy()
    env["PBS_JOBID"] = "0:fixture.server"
    result = subprocess.run(
        _acquisition_argv(attempt),
        input=_acquisition_candidate_source(),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    candidate = json.loads(
        (attempt / "acquisition-candidate.json").read_text(encoding="utf-8"),
    )
    assert candidate["known_values_check"]["passed"] is expected_passed


def test_acquisition_candidate_rejects_schema_valid_duplicate_probe_key(tmp_path):
    policy = json.loads((TOOL_DIR / "policy.json").read_text(encoding="utf-8"))
    attempt = tmp_path / "attempt"
    _write_acquisition_fixture(attempt, policy["expected_cpu_model"])
    probe_path = attempt / "attestation-pre.json"
    duplicate = probe_path.read_text(encoding="utf-8").replace(
        '{"schema_version": "pegasus-probe-output/v2",',
        ('{"schema_version": "pegasus-probe-output/v2", '
         '"schema_version": "pegasus-probe-output/v2",'),
        1,
    )
    probe_path.write_text(duplicate, encoding="utf-8")
    env = os.environ.copy()
    env["PBS_JOBID"] = "0:fixture.server"

    result = subprocess.run(
        _acquisition_argv(attempt),
        input=_acquisition_candidate_source(),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "duplicate key" in result.stderr
    assert not (attempt / "acquisition-candidate.json").exists()


@dataclasses.dataclass(frozen=True)
class _ProbeFixture:
    marker: str


def _probe_profile_payload():
    return {
        "cpu": {}, "cores": {}, "cache_topology": [], "numa": [], "tsc": {},
        "effective_clock": {
            "samples_mhz": [2101.0],
            "method": "proc-cpuinfo",
            "governor": "performance",
        },
        "visibility": {},
    }


def _assert_probe_payload(payload, *, ok, stage=None):
    assert set(payload) == {
        "schema_version", "ok", "observed_epoch", "profile" if ok else "error",
    }
    assert payload["schema_version"] == "pegasus-probe-output/v2"
    assert type(payload["ok"]) is bool and payload["ok"] is ok
    assert type(payload["observed_epoch"]) is int
    assert not isinstance(payload["observed_epoch"], bool)
    if ok:
        assert set(payload["profile"]["effective_clock"]) == {
            "samples_mhz", "method", "governor",
        }
    else:
        assert set(payload["error"]) == {"stage", "type", "message"}
        assert payload["error"]["stage"] == stage
        assert all(type(payload["error"][key]) is str and payload["error"][key]
                   for key in ("stage", "type", "message"))


def test_run_probe_fixture_to_stdout_shape_and_file(tmp_path, monkeypatch, capsys):
    module = _load("probe_entry_fixture", TOOL_DIR / "run_probe.py")
    token = _ProbeFixture(marker="observed")
    fake = SimpleNamespace(
        probe=lambda: token,
        observed_profile_to_dict=lambda value: (
            _probe_profile_payload() if value is token else pytest.fail("wrong profile")
        ),
    )
    target = tmp_path / "observation.json"
    rc, payload = module.run(output=target, importer=lambda _: fake)
    assert rc == 0
    _assert_probe_payload(payload, ok=True)
    assert json.loads(target.read_text(encoding="utf-8")) == payload
    monkeypatch.setattr(module, "run", lambda **_kwargs: (rc, payload))
    assert module.main([]) == rc
    assert json.loads(capsys.readouterr().out) == payload


def test_run_probe_import_failure_is_structured_and_nonzero(tmp_path, monkeypatch, capsys):
    module = _load("probe_entry_missing", TOOL_DIR / "run_probe.py")

    def missing(_):
        raise ModuleNotFoundError()

    target = tmp_path / "error.json"
    rc, payload = module.run(output=target, importer=missing)
    assert rc != 0
    _assert_probe_payload(payload, ok=False, stage="import")
    assert json.loads(target.read_text(encoding="utf-8")) == payload
    monkeypatch.setattr(module, "run", lambda **_kwargs: (rc, payload))
    assert module.main([]) == rc
    assert json.loads(capsys.readouterr().out) == payload


def test_run_probe_probe_failure_is_structured_in_file_and_stdout(
        tmp_path, monkeypatch, capsys):
    module = _load("probe_entry_probe_failure", TOOL_DIR / "run_probe.py")

    def fail_probe():
        raise RuntimeError()

    fake = SimpleNamespace(
        probe=fail_probe,
        observed_profile_to_dict=lambda _value: pytest.fail("serializer must not run"),
    )
    target = tmp_path / "error.json"
    rc, payload = module.run(output=target, importer=lambda _: fake)
    assert rc == 3
    _assert_probe_payload(payload, ok=False, stage="probe")
    assert json.loads(target.read_text(encoding="utf-8")) == payload
    monkeypatch.setattr(module, "run", lambda **_kwargs: (rc, payload))
    assert module.main([]) == rc
    assert json.loads(capsys.readouterr().out) == payload


def test_run_probe_write_failure_is_structured_for_stdout(tmp_path, monkeypatch, capsys):
    module = _load("probe_entry_write_failure", TOOL_DIR / "run_probe.py")
    token = _ProbeFixture(marker="observed")
    fake = SimpleNamespace(
        probe=lambda: token,
        observed_profile_to_dict=lambda _value: _probe_profile_payload(),
    )
    target = tmp_path / "already-exists.json"
    target.write_text("preserved\n", encoding="utf-8")
    rc, payload = module.run(output=target, importer=lambda _: fake)
    assert rc == 4
    _assert_probe_payload(payload, ok=False, stage="write")
    assert target.read_text(encoding="utf-8") == "preserved\n"
    monkeypatch.setattr(module, "run", lambda **_kwargs: (rc, payload))
    assert module.main([]) == rc
    assert json.loads(capsys.readouterr().out) == payload


def test_run_probe_write_failure_has_nonempty_message_for_empty_exception(
        tmp_path, monkeypatch):
    module = _load("probe_entry_empty_write_failure", TOOL_DIR / "run_probe.py")
    fake = SimpleNamespace(
        probe=lambda: _ProbeFixture(marker="observed"),
        observed_profile_to_dict=lambda _value: _probe_profile_payload(),
    )

    def fail_write(_path, _payload):
        raise OSError()

    monkeypatch.setattr(module, "_write_create_only", fail_write)
    rc, payload = module.run(
        output=tmp_path / "unwritten.json", importer=lambda _: fake,
    )
    assert rc == 4
    _assert_probe_payload(payload, ok=False, stage="write")


def test_smoke_probe_calls_v2_producer_and_preserves_stdout_copy():
    source = (TOOL_DIR / "smoke_probe.sh").read_text(encoding="utf-8")
    assert 'run_probe.py" --output "$probe_file"' in source
    assert '>"$RUN_DIR/run_probe.stdout"' in source


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


def test_collect_receipt_preserves_job_script_sha256(tmp_path):
    module = _load("collector_entry_job_script_sha", TOOL_DIR / "collect_receipt.py")
    attempt, staging, stdout, stderr = _collector_fixture(tmp_path)
    expected = "c" * 64
    (staging / "job-result.json").write_text(json.dumps({
        "pbs_jobid": "12345.scheduler",
        "calibrate_rc": 0,
        "job_script_sha256": expected,
    }), encoding="utf-8")

    target = module.collect(
        attempt_dir=attempt, job_staging=staging,
        stdout_path=stdout, stderr_path=stderr,
    )
    doc = json.loads(target.read_text(encoding="utf-8"))
    assert doc["job_result"]["job_script_sha256"] == expected


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
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from orchestrator.calibrator import schema_v2
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
    end = source.index("# (iv-b) pinned-clean glog", start)
    return source[start:end]


def _glog_stage_fragment() -> str:
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    start = source.index("# (iv-b) pinned-clean glog")
    end = source.index("# (iv-c) pinned-clean CCBench", start)
    return source[start:end]


def _certify_toolchain_fragment() -> str:
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    start = source.index("CC_PATH=$(command -v gcc)")
    end = source.index('\n\n# calibrator は Python 3.10 構文を使う。', start)
    return source[start:end]


def _certify_trace_symbol_fragment() -> str:
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    start = source.index('timeout 60 "$NM_PATH" -C "$BINARY"')
    end = source.index("\n\n# (v) synchronous build return", start)
    return source[start:end]


def _compile_symbol_probe(tmp_path: Path, *, trace: bool) -> Path:
    compiler = Path("/usr/bin/gcc").resolve(strict=True)
    assert compiler.is_file() and os.access(compiler, os.X_OK)
    source_path = tmp_path / ("trace.c" if trace else "trace-free.c")
    binary = tmp_path / ("trace.exe" if trace else "trace-free.exe")
    if trace:
        source_text = """void izanagi_trace_probe(void) {}
int main(void) { izanagi_trace_probe(); return 0; }
"""
    else:
        source_text = """int ordinary_probe(void) { return 0; }
int main(void) { return ordinary_probe(); }
"""
    source_path.write_text(source_text, encoding="utf-8")
    subprocess.run(
        [str(compiler), "-O0", str(source_path), "-o", str(binary)],
        check=True, capture_output=True, text=True,
    )
    assert binary.is_file() and os.access(binary, os.X_OK)
    return binary


def _real_nm_symbols(binary: Path) -> str:
    nm_path = Path("/usr/bin/nm").resolve(strict=True)
    assert nm_path.is_file() and os.access(nm_path, os.X_OK)
    result = subprocess.run(
        [str(nm_path), "-C", str(binary)],
        check=True, capture_output=True, text=True,
    )
    return result.stdout


def _run_certify_trace_symbol_fragment(
        attempt: Path, binary: Path) -> subprocess.CompletedProcess[str]:
    nm_path = Path("/usr/bin/nm").resolve(strict=True)
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
NM_PATH={json.dumps(str(nm_path))}
BINARY={json.dumps(str(binary))}
"""
    return subprocess.run(
        [
            "bash", "-c",
            _shell_failure_harness(prefix + _certify_trace_symbol_fragment()),
        ],
        capture_output=True, text=True,
    )


def test_certify_records_real_cmake_and_fixed_nm_identity(tmp_path):
    fragment = _certify_toolchain_fragment()
    assert 'CMAKE_PATH=$(realpath "$(command -v cmake)")' in fragment
    assert "if ! NM_PATH=$(realpath /usr/bin/nm); then" in fragment
    assert '[[ ! -f "$NM_PATH" || ! -x "$NM_PATH" ]]' in fragment
    assert 'realpath "$NM_PATH" >"$ATTEMPT_DIR/nm.path"' in fragment
    assert '"$NM_PATH" --version >"$ATTEMPT_DIR/nm.version"' in fragment
    assert "command -v nm" not in fragment

    attempt = tmp_path / "attempt"
    attempt.mkdir()
    wrapper_dir = tmp_path / "wrapper-bin"
    wrapper_dir.mkdir()
    wrapper_marker = tmp_path / "path-nm-ran"
    nm_wrapper = wrapper_dir / "nm"
    nm_wrapper.write_text(
        "#!/bin/sh\n" + f": > {shlex.quote(str(wrapper_marker))}\nexit 97\n",
        encoding="utf-8",
    )
    nm_wrapper.chmod(0o755)
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
"""
    command = (
        prefix + fragment
        + '\nprintf "%s\\n" "$CMAKE_PATH" >"$ATTEMPT_DIR/cmake.path.observed"\n'
    )
    env = os.environ.copy()
    env["PATH"] = str(wrapper_dir) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(command)],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stderr
    assert not wrapper_marker.exists()
    cmake_path = Path(
        (attempt / "cmake.path.observed").read_text(encoding="utf-8").strip()
    )
    expected_cmake = shutil.which("cmake", path=env["PATH"])
    assert expected_cmake is not None
    assert cmake_path == Path(expected_cmake).resolve(strict=True)
    assert cmake_path.is_absolute()
    nm_path = Path((attempt / "nm.path").read_text(encoding="utf-8").strip())
    assert nm_path == Path("/usr/bin/nm").resolve(strict=True)
    assert (attempt / "nm.version").read_text(encoding="utf-8").strip()


def test_certify_trace_symbol_stage_accepts_real_unstripped_trace_free_binary(
        tmp_path):
    binary = _compile_symbol_probe(tmp_path, trace=False)
    symbols = _real_nm_symbols(binary)
    assert symbols
    assert "izanagi_trace" not in symbols.lower()
    attempt = tmp_path / "positive-attempt"
    attempt.mkdir()

    result = _run_certify_trace_symbol_fragment(attempt, binary)

    assert result.returncode == 0, result.stderr
    assert (attempt / "binary.symbols").read_text(encoding="utf-8") == symbols
    assert not (attempt / "failure.json").exists()


def test_certify_trace_symbol_stage_rejects_real_unstripped_trace_binary(
        tmp_path):
    binary = _compile_symbol_probe(tmp_path, trace=True)
    symbols = _real_nm_symbols(binary)
    assert symbols
    assert "izanagi_trace" in symbols.lower()
    attempt = tmp_path / "trace-attempt"
    attempt.mkdir()

    result = _run_certify_trace_symbol_fragment(attempt, binary)

    assert result.returncode == 2, result.stderr
    failure = json.loads((attempt / "failure.json").read_text(encoding="utf-8"))
    assert failure["stage"] == "trace_separation"
    assert (attempt / "binary.symbols").read_text(encoding="utf-8") == symbols


def test_certify_trace_symbol_stage_rejects_real_empty_stripped_binary(tmp_path):
    binary = _compile_symbol_probe(tmp_path, trace=True)
    before_strip = _real_nm_symbols(binary)
    assert before_strip
    assert "izanagi_trace" in before_strip.lower()
    strip_path = Path("/usr/bin/strip").resolve(strict=True)
    assert strip_path.is_file() and os.access(strip_path, os.X_OK)
    subprocess.run(
        [str(strip_path), "--strip-all", str(binary)],
        check=True, capture_output=True, text=True,
    )
    assert _real_nm_symbols(binary) == ""
    attempt = tmp_path / "stripped-attempt"
    attempt.mkdir()

    result = _run_certify_trace_symbol_fragment(attempt, binary)

    assert result.returncode == 2, result.stderr
    failure = json.loads((attempt / "failure.json").read_text(encoding="utf-8"))
    assert failure["stage"] == "trace_separation"
    assert (attempt / "binary.symbols").read_text(encoding="utf-8") == ""


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


def test_glog_head_mismatch_writes_glog_failure(tmp_path):
    source_repo = tmp_path / "glog"
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
GLOG_SOURCE_PATH={json.dumps(str(source_repo))}
GLOG_EXPECTED_HEAD={expected_head}
"""
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(prefix + _glog_stage_fragment())],
        capture_output=True, text=True,
    )
    assert result.returncode == 2, result.stderr
    assert json.loads((attempt / "failure.json").read_text())["stage"] == "glog"


def test_calibrate_failure_survives_err_trap_and_writes_job_result(tmp_path):
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    fragment = source.split('CALIBRATE_ARGV_JSON="$ATTEMPT_DIR/calibrate-argv.json"\n', 1)[1]
    fragment = 'CALIBRATE_ARGV_JSON="$ATTEMPT_DIR/calibrate-argv.json"\n' + fragment.split(
        "# worktree metadata を clean に戻す。", 1)[0]
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
PBS_JOBID=123.server
remaining=30
CALIBRATION_RRATIO=50
CALIBRATION_PROTOCOL=silo
REPO_ROOT={json.dumps(str(tmp_path))}
TOOLS={json.dumps(str(TOOL_DIR))}
BINARY=/unused/binary
BINARY_SHA={'a' * 64}
CURRENT_SCRIPT_SHA={'b' * 64}
CALIBRATE_PATH=/fixture/perf/bin:/usr/bin
CALIBRATE_PYTHON=/fixture/python3.10
USE_PERF=1
"""
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(prefix + fragment)],
        capture_output=True, text=True, env=_stub_timeout(tmp_path, 7),
    )
    assert result.returncode == 7, result.stderr
    assert json.loads((attempt / "failure.json").read_text())["stage"] == "calibrate"
    assert json.loads((attempt / "job-result.json").read_text())["calibrate_rc"] == 7
    assert json.loads((attempt / "job-result.json").read_text())["job_script_sha256"] == "b" * 64
    assert json.loads((attempt / "job-result.json").read_text())["calibration"] == {
        "protocol": "silo", "workload": {"ycsb_rratio": "50"},
    }
    argv = json.loads((attempt / "calibrate-argv.json").read_text())
    assert argv[:3] == [
        "env", "PATH=/fixture/perf/bin:/usr/bin", "/fixture/python3.10",
    ]
    assert argv[3] == str(tmp_path / "orchestrator" / "calibrate.py")
    assert argv[argv.index("--binary") + 1] == "/unused/binary"
    assert "--perf-preflight-json" not in argv

    no_perf = tmp_path / "no-perf"
    no_perf.mkdir()
    no_perf_attempt = no_perf / "attempt"
    no_perf_attempt.mkdir()
    receipt = no_perf_attempt / "perf-preflight.json"
    no_perf_prefix = prefix + (
        f"ATTEMPT_DIR={shlex.quote(str(no_perf_attempt))}\n"
        "USE_PERF=0\n"
        f"PERF_PREFLIGHT_RECEIPT={shlex.quote(str(receipt))}\n"
    )
    result = subprocess.run(
        ["bash", "-c", _shell_failure_harness(no_perf_prefix + fragment)],
        capture_output=True, text=True, env=_stub_timeout(no_perf, 1),
    )
    assert result.returncode == 1, result.stderr
    assert json.loads((no_perf_attempt / "failure.json").read_text()) == {
        "rc": 1, "stage": "calibrate",
    }
    assert json.loads((no_perf_attempt / "job-result.json").read_text())["calibrate_rc"] == 1
    no_perf_argv = json.loads((no_perf_attempt / "calibrate-argv.json").read_text())
    expected = [str(no_perf_attempt / "acquisition-receipt.json")
                if arg == str(attempt / "acquisition-receipt.json") else arg for arg in argv]
    assert no_perf_argv == expected + ["--perf-preflight-json", str(receipt)]


def test_certify_job_rejects_legacy_tolerance_environment():
    source = (TOOL_DIR / "certify_calibration.sh").read_text(encoding="utf-8")
    start = source.index('if [[ -n "${PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT+x}" ]]')
    end = source.index("\n\n# submit receipt", start)
    fragment = source[start:end]
    command = (
        'write_failure() { printf "%s:%s:%s\\n" "$1" "$2" "$3"; }\n'
        + fragment
    )
    env = os.environ.copy()
    env["PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT"] = "2.0"
    result = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, env=env,
    )
    assert result.returncode == 2
    assert "2:submit_binding:legacy effective clock tolerance input is forbidden" in result.stdout


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
    env.pop("PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT", None)
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
        "calibration": {
            "protocol": "silo", "workload": {"ycsb_rratio": "50"},
        },
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
CALIBRATION_RRATIO=50
CALIBRATION_PROTOCOL=silo
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


def test_certify_submit_binding_requires_matching_calibration_rratio(tmp_path):
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
        "calibration": {
            "protocol": "silo", "workload": {"ycsb_rratio": "50"},
        },
        "qsub": {
            "request_id": "123.server", "project": "SFC", "queue": "gen_S",
            "nodes": 1, "elapstim_req_s": 7200,
        },
    }
    receipt_path = attempt / "submit-receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
CURRENT_COMMIT={commit}
CURRENT_SCRIPT_SHA={script_sha}
PBS_JOBID=0:123.server
PROJECT=SFC
QUEUE=gen_S
NODES=1
REQUESTED_S=7200
CALIBRATION_PROTOCOL=silo
REPO_ROOT={json.dumps(str(REPO))}
"""
    mismatch = subprocess.run(
        ["bash", "-c", prefix + "CALIBRATION_RRATIO=80\n" + fragment],
        capture_output=True, text=True,
    )
    assert mismatch.returncode == 1
    assert mismatch.stderr == (
        "submit binding mismatch: {'dry_run': True, 'source_commit': True, "
        "'job_script_sha256': True, 'request_id': True, 'project': True, "
        "'queue': True, 'nodes': True, 'walltime': True, "
        "'calibration_rratio': False, 'calibration_protocol': True}\n"
    )

    receipt["calibration"]["workload"]["ycsb_rratio"] = "80"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    match = subprocess.run(
        ["bash", "-c", prefix + "CALIBRATION_RRATIO=80\n" + fragment],
        capture_output=True, text=True,
    )
    assert match.returncode == 0, match.stderr


def test_certify_submit_binding_requires_matching_calibration_protocol(tmp_path):
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
        "calibration": {
            "protocol": "mocc", "workload": {"ycsb_rratio": "50"},
        },
        "qsub": {
            "request_id": "123.server", "project": "SFC", "queue": "gen_S",
            "nodes": 1, "elapstim_req_s": 7200,
        },
    }
    receipt_path = attempt / "submit-receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    prefix = f"""ATTEMPT_DIR={json.dumps(str(attempt))}
CURRENT_COMMIT={commit}
CURRENT_SCRIPT_SHA={script_sha}
PBS_JOBID=0:123.server
CALIBRATION_RRATIO=50
PROJECT=SFC
QUEUE=gen_S
NODES=1
REQUESTED_S=7200
REPO_ROOT={json.dumps(str(REPO))}
"""
    mismatch = subprocess.run(
        ["bash", "-c", prefix + "CALIBRATION_PROTOCOL=tictoc\n" + fragment],
        capture_output=True, text=True,
    )
    assert mismatch.returncode == 1
    assert mismatch.stderr == (
        "submit binding mismatch: {'dry_run': True, 'source_commit': True, "
        "'job_script_sha256': True, 'request_id': True, 'project': True, "
        "'queue': True, 'nodes': True, 'walltime': True, "
        "'calibration_rratio': True, 'calibration_protocol': False}\n"
    )

    match = subprocess.run(
        ["bash", "-c", prefix + "CALIBRATION_PROTOCOL=mocc\n" + fragment],
        capture_output=True, text=True,
    )
    assert match.returncode == 0, match.stderr


def test_submit_dry_run_does_not_resolve_cluster_commands(tmp_path):
    # clean temporary git fixture を使い、実 repository/output と scheduler に触れない。
    fixture_repo = tmp_path / "repo"
    fixture_tools = fixture_repo / "tools" / TOOL_DIR.name
    fixture_tools.parent.mkdir(parents=True)
    # [T-057] `__pycache__` を除外する。並列 worker が同じ module を import すると CPython が
    # `x.cpython-310.pyc.<tmp>` を作って rename するため、それを拾った copytree が
    # 「途中で消えた」で落ちる (計算ノードの全走で実測した flake)。
    shutil.copytree(TOOL_DIR, fixture_tools,
                    ignore=shutil.ignore_patterns("__pycache__"))
    subprocess.run(["git", "init", "-q", str(fixture_repo)], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "config", "user.email", "fixture@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "config", "user.name", "Fixture"], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "commit", "-qm", "fixture"], check=True)
    staging_root = (
        fixture_repo
        / "output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
    )
    staging_root.mkdir(parents=True)
    for name in ("masstree", "mimalloc", "googletest"):
        (staging_root / name).mkdir()
    attempts = tmp_path / "attempts"
    env = os.environ.copy()
    # qstat 等が PATH に存在しても dry-run が起動しないことは capture 内容で確認する。
    result = subprocess.run([
        "bash", str(fixture_tools / "submit_certify.sh"),
        "--repo-root", str(fixture_repo),
        "--attempts-root", str(attempts),
        "--dry-run",
    ], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    assert "qsub command:" in result.stdout
    receipts = list((attempts / "submissions").glob("*/submit-receipt.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert receipt["dry_run"] is True
    assert all(item["rc"] == 0 for item in receipt["preflight"].values())
    assert "PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT" not in result.stdout

    base = [
        "bash", str(fixture_tools / "submit_certify.sh"),
        "--repo-root", str(fixture_repo),
        "--attempts-root", str(attempts),
    ]
    before = set((attempts / "submissions").iterdir())
    for hostile in (
        ["--effective-clock-tolerance-pct", "2.0"],
        ["--effective-clock-tolerance-pct", "100.0"],
        ["--clock-window", "2.0"],
    ):
        rejected = subprocess.run(
            base + hostile + ["--dry-run"], capture_output=True, text=True, env=env,
        )
        assert rejected.returncode == 2
        assert set((attempts / "submissions").iterdir()) == before

    legacy_env = dict(env, PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT="2.0")
    rejected = subprocess.run(
        base + ["--dry-run"], capture_output=True, text=True, env=legacy_env,
    )
    assert rejected.returncode == 2
    assert set((attempts / "submissions").iterdir()) == before


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
