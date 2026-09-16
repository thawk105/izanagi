# -*- coding: utf-8 -*-
"""floor 専用 PBS 資材を、実 scheduler と実 repository/output に触れず検査する。"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from orchestrator.campaign import (
    floor_job_checkpoint,
    floor_liveness,
    reservation,
    s8b_floor_campaign,
)
from orchestrator.qualification import artifacts


TOOL_DIR = REPO / "tools" / "pegasus"
SUBMIT = TOOL_DIR / "submit_floor.sh"
JOB = TOOL_DIR / "floor_campaign.sh"
PEGASUS_README = TOOL_DIR / "README.md"
GENERATOR = TOOL_DIR / "generate_floor_masstree_payload_policy.py"
SHARED_POLICY = TOOL_DIR / "policy.json"
FLOOR_POLICY = TOOL_DIR / "policies" / "floor_v1.json"
PROTOCOL = REPO / "output" / "s8b-freeze" / "floor_protocol.json"
FREEZE = REPO / "output" / "s8b-freeze" / "holdout_freeze.json"
PREFLIGHT_HELPER_RELATIVE = (
    "orchestrator/campaign/certified_writer_preflight.py"
)

PRE_KEYS = {
    "schema_version",
    "source_commit",
    "job_script_path",
    "job_script_sha256",
    "nonce",
    "prepared_at",
    "request",
    "preflight",
    "dry_run",
}
RECEIPT_KEYS = {
    "schema_version",
    "source_commit",
    "job_script_path",
    "job_script_sha256",
    "job_id",
    "nonce",
    "submitted_at",
    "request",
    "preflight",
    "dry_run",
}
REQUEST_KEYS = {"project", "queue", "nodes", "elapstim_req_s"}
PREFLIGHT_KEYS = {"qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota"}
CAPTURE_KEYS = {"rc", "stdout_raw", "stderr_raw"}
JOB_RESULT_KEYS = {
    "schema_version",
    "pbs_jobid",
    "driver_rc",
    "mode",
    "protocol_path",
    "source_commit",
    "job_script_sha256",
    "executing_script_sha256",
    "nonce",
    "reservation_requested_s",
    "completed_epoch",
}
RESERVATION_KEYS = {
    "job_id",
    "requested_s",
    "scheduler_started_epoch",
    "deadline_epoch",
    "host",
    "boot_id",
    "script_sha256",
    "nonce",
    "recorded_epoch",
}


def _pbs_directives(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].startswith("#!")
    directives: dict[str, str] = {}
    header_open = True
    commented = re.compile(r"^\s*(?:#{2,}\s*PBS|#\s+#PBS)(?:\s|$)")
    for line_number, line in enumerate(lines[1:], 2):
        if commented.match(line):
            raise AssertionError(f"commented-out PBS directive at {path}:{line_number}")
        if header_open and (not line.strip() or line.startswith("#")):
            if not line.startswith("#PBS "):
                continue
            fields = line[len("#PBS ") :].split(maxsplit=1)
            if len(fields) == 1:
                option, separator, value = fields[0].partition("=")
                assert option.startswith("--") and separator and value, (
                    f"malformed PBS directive at {path}:{line_number}"
                )
            else:
                option, value = fields
            assert option not in directives, (
                f"duplicate PBS directive {option} at {path}:{line_number}"
            )
            directives[option] = value
            continue
        header_open = False
        assert not line.startswith("#PBS "), (
            f"late PBS directive at {path}:{line_number}"
        )
    return directives


def _hms_seconds(value: str) -> int:
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def _derived_floor_reservation_budget() -> tuple[int, int]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    cells = s8b_floor_campaign.enumerate_cells(
        freeze, stock_configuration=protocol["stock_configuration"]
    )
    schedule = s8b_floor_campaign.build_schedule(
        cells=cells,
        master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    return s8b_floor_campaign._floor_reservation_budget(
        protocol=protocol, cells=cells, schedule=schedule
    )


def _git_env(repo: Path) -> dict[str, str]:
    home = repo.parent / "git-home"
    home.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.pop("GIT_CONFIG_PARAMETERS", None)
    env.pop("GIT_TEMPLATE_DIR", None)
    for name in tuple(env):
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            env.pop(name)
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / "xdg"),
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.hooksPath",
            "GIT_CONFIG_VALUE_0": "",
        }
    )
    return env


def _git_command(repo: Path, *args: str) -> list[str]:
    return [
        "git",
        "-c",
        "core.hooksPath=",
        "-C",
        str(repo),
        *args,
    ]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _git_command(repo, *args),
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(repo),
    )


def _git_bytes(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        _git_command(repo, *args),
        check=True,
        capture_output=True,
        env=_git_env(repo),
    ).stdout


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    tools = repo / "tools" / "pegasus"
    tools.mkdir(parents=True)
    for source in (SUBMIT, JOB, SHARED_POLICY):
        shutil.copy2(source, tools / source.name)
    policies = tools / "policies"
    policies.mkdir()
    shutil.copy2(FLOOR_POLICY, policies / FLOOR_POLICY.name)
    calibrator = repo / "orchestrator" / "calibrator"
    calibrator.mkdir(parents=True)
    for name in ("__init__.py", "schema_v2.py"):
        shutil.copy2(REPO / "orchestrator" / "calibrator" / name, calibrator / name)
    campaign = repo / "orchestrator" / "campaign"
    campaign.mkdir()
    shutil.copy2(
        REPO / "orchestrator" / "campaign" / "__init__.py",
        campaign / "__init__.py",
    )
    shutil.copy2(
        REPO / "orchestrator" / "campaign" / "floor_job_checkpoint.py",
        campaign / "floor_job_checkpoint.py",
    )
    output = repo / "output"
    output.mkdir()
    (output / ".tracked-fixture").write_text("clean\n", encoding="utf-8")
    subprocess.run(
        ["git", "-c", "core.hooksPath=", "init", "-q", str(repo)],
        check=True,
        env=_git_env(repo),
    )
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")
    return repo


def _fixture_preflight_source() -> str:
    return (
        "import argparse,json,os,sys\n"
        "parser=argparse.ArgumentParser()\n"
        "parser.add_argument('mode',choices=('floor','t126'))\n"
        "parser.add_argument('--repo-root',required=True)\n"
        "parser.add_argument('--receipt',required=True)\n"
        "args=parser.parse_args()\n"
        "expected=os.path.join(args.repo_root,'output','env','pegasus',"
        "'floor','attempts','submissions',os.environ["
        "'IZANAGI_SUBMISSION_NONCE'],'submit-receipt.json')\n"
        "if args.mode!='floor' or args.receipt!=expected:\n"
        "    raise SystemExit(4)\n"
        "rc=int(os.environ.get('IZANAGI_TEST_PREFLIGHT_RC','0'))\n"
        "if rc not in (0,3,4): raise SystemExit(4)\n"
        "if rc:\n"
        "    print(json.dumps({'gate':'fixture','reason':'rejected'},"
        "sort_keys=True,separators=(',',':')),file=sys.stderr)\n"
        "raise SystemExit(rc)\n"
    )


def _install_fixture_preflight(repo: Path) -> str:
    helper = repo / PREFLIGHT_HELPER_RELATIVE
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(_fixture_preflight_source(), encoding="utf-8")
    _git(repo, "add", PREFLIGHT_HELPER_RELATIVE)
    _git(repo, "commit", "-qm", "fixture committed admission helper")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _path_tree_snapshot(root: Path) -> object:
    if not os.path.lexists(root):
        return None
    paths = [root]
    if root.is_dir() and not root.is_symlink():
        paths.extend(sorted(root.rglob("*")))
    snapshot = []
    for path in paths:
        info = path.lstat()
        relative = "." if path == root else path.relative_to(root).as_posix()
        if path.is_symlink():
            payload = ("symlink", os.readlink(path))
        elif path.is_file():
            payload = ("file", path.read_bytes())
        elif path.is_dir():
            payload = ("directory", None)
        else:
            payload = ("other", None)
        snapshot.append((relative, stat.S_IMODE(info.st_mode), payload))
    return tuple(snapshot)


def _checkpoint_records(path: Path) -> tuple[list[dict[str, object]], bool]:
    payload = path.read_bytes()
    incomplete = bool(payload) and not payload.endswith(b"\n")
    complete = payload if not incomplete else payload[: payload.rfind(b"\n") + 1]
    return [json.loads(line) for line in complete.splitlines()], incomplete


def _mkdir_shim_text(*, scratch: Path, marker: Path) -> str:
    return (
        "#!/bin/bash\n"
        f"if [[ \"${{!#}}\" == {shlex.quote(str(scratch))} ]]; then\n"
        f"    : > {shlex.quote(str(marker))}\n"
        "    exit 1\n"
        "fi\n"
        "if [[ \"${IZANAGI_MKDIR_SHIM_PROBE_ONLY:-}\" == 1 ]]; then exit 0; fi\n"
        "exec /bin/mkdir \"$@\"\n"
    )


def _run_floor_admission_fixture(
    tmp_path: Path, *, preflight_rc: int
) -> tuple[
    subprocess.CompletedProcess[str], Path, Path, Path, Path, Path, object, object,
]:
    repo = _fixture_repo(tmp_path)
    source_commit = _install_fixture_preflight(repo)
    # The floor wrapper's existing source-identity gate requires current HEAD
    # to equal the commit recorded by the submission receipt.
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == source_commit
    nonce = "a" * 32
    receipt = (
        repo / "output/env/pegasus/floor/attempts/submissions"
        / nonce / "submit-receipt.json"
    )
    receipt.parent.mkdir(parents=True)
    receipt.write_text(
        json.dumps({"source_commit": source_commit}) + "\n", encoding="utf-8"
    )
    bin_dir = tmp_path / "job-bin"
    bin_dir.mkdir()
    mkdir_marker = tmp_path / "mkdir-invoked"
    driver_marker = tmp_path / "driver-invoked"
    job_number = int(
        hashlib.sha256(str(tmp_path).encode("utf-8")).hexdigest()[:12], 16
    )
    job_id = f"0:{job_number}.nqsv"
    scratch = Path("/scr") / job_id.replace(":", "_")
    (bin_dir / "mkdir").write_text(
        _mkdir_shim_text(scratch=scratch, marker=mkdir_marker), encoding="utf-8"
    )
    (bin_dir / "mkdir").chmod(0o755)
    real_python = str(Path(sys.executable).resolve(strict=True))
    (bin_dir / "python3").write_text(
        "#!/bin/sh\n"
        "case \" $* \" in\n"
        f"  *s8b_floor_campaign.py*) : > {shlex.quote(str(driver_marker))} ;;\n"
        "esac\n"
        f"exec {shlex.quote(real_python)} \"$@\"\n",
        encoding="utf-8",
    )
    (bin_dir / "python3").chmod(0o755)
    evidence_root = tmp_path / "job-evidence"
    evidence_job_id = job_id.removeprefix("0:")
    checkpoint = (
        evidence_root / "pegasus" / evidence_job_id / nonce / "checkpoint.jsonl"
    )
    output_before = _path_tree_snapshot(repo / "output")
    scratch_before = _path_tree_snapshot(scratch)
    env = _git_env(repo)
    env.update(
        {
            "PATH": str(bin_dir) + os.pathsep + env["PATH"],
            "PBS_JOBID": job_id,
            "PBS_O_WORKDIR": str(repo),
            "IZANAGI_SUBMISSION_NONCE": nonce,
            "IZANAGI_TEST_PREFLIGHT_RC": str(preflight_rc),
            "IZANAGI_FLOOR_JOB_EVIDENCE_ROOT": str(evidence_root),
        }
    )
    completed = subprocess.run(
        ["bash", str(repo / "tools/pegasus/floor_campaign.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return (
        completed,
        repo,
        scratch,
        mkdir_marker,
        driver_marker,
        checkpoint,
        output_before,
        scratch_before,
    )


def test_floor_mkdir_shim_matches_only_normalized_exact_scratch(
    tmp_path: Path,
) -> None:
    shim = tmp_path / "mkdir"
    marker = tmp_path / "marker"
    raw_job_id = "fixture:123.nqsv"
    scratch = Path("/scr") / raw_job_id.replace(":", "_")
    shim.write_text(
        _mkdir_shim_text(scratch=scratch, marker=marker), encoding="utf-8"
    )
    shim.chmod(0o755)
    env = {**os.environ, "IZANAGI_MKDIR_SHIM_PROBE_ONLY": "1"}

    exact = subprocess.run(
        [str(shim), "-p", str(scratch)], env=env, check=False
    )
    assert exact.returncode == 1
    assert marker.is_file()
    marker.unlink()

    pytest_tmp_like_path = Path("/scr") / "pytest-of-fixture" / tmp_path.name
    unrelated = subprocess.run(
        [str(shim), "-p", str(pytest_tmp_like_path)], env=env, check=False
    )
    assert unrelated.returncode == 0
    assert not marker.exists()


def _sentinel_bin(tmp_path: Path, *, failures: dict[str, int] | None = None) -> tuple[Path, Path]:
    failures = failures or {}
    bin_dir = tmp_path / "sentinel-bin"
    bin_dir.mkdir(exist_ok=True)
    log = tmp_path / "sentinel.log"
    for name in ("qstat", "pegasusinfo", "rbudgetcheck", "check_quota", "qsub"):
        script = bin_dir / name
        script.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' {shlex.quote(name)} >> {shlex.quote(str(log))}\n"
            f"printf '%s stdout\\n' {shlex.quote(name)}\n"
            f"printf '%s stderr\\n' {shlex.quote(name)} >&2\n"
            f"exit {failures.get(name, 99)}\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
    return bin_dir, log


def _successful_bin(tmp_path: Path) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "successful-bin"
    bin_dir.mkdir(exist_ok=True)
    for name in ("qstat", "pegasusinfo", "rbudgetcheck", "check_quota"):
        script = bin_dir / name
        script.write_text(
            "#!/bin/sh\n"
            f"printf '%s stdout\\n' {shlex.quote(name)}\n"
            f"printf '%s stderr\\n' {shlex.quote(name)} >&2\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
    qsub_args = tmp_path / "qsub.args"
    qsub_cwd = tmp_path / "qsub.cwd"
    qsub = bin_dir / "qsub"
    qsub.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\0' \"$@\" > {shlex.quote(str(qsub_args))}\n"
        f"printf '%s\\n' \"$PWD\" > {shlex.quote(str(qsub_cwd))}\n"
        "printf '%s\\n' 'Request 98765.nqsv submitted.'\n",
        encoding="utf-8",
    )
    qsub.chmod(0o755)
    return bin_dir, qsub_args, qsub_cwd


def _install_floor_third_party_sources(repo: Path) -> Path:
    """Install clean fixture checkouts and bind their pins into fixture policy."""
    policy_path = repo / "tools" / "pegasus" / "policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    source_root = (
        repo / "output" / "env" / "pegasus" / "silo_ladder_rung1"
        / "job-staging" / "thirdparty-src"
    )
    source_root.mkdir(parents=True)
    for item in policy["silo_ladder_rung1"]["third_party_sources"]:
        source = source_root / item["source_name"]
        source.mkdir()
        subprocess.run(
            ["git", "-c", "core.hooksPath=", "init", "-q", str(source)],
            check=True, env=_git_env(source),
        )
        _git(source, "config", "user.email", "fixture@example.invalid")
        _git(source, "config", "user.name", "fixture")
        (source / "fixture-source.txt").write_text(
            item["name"] + "\n", encoding="utf-8",
        )
        _git(source, "add", ".")
        _git(source, "commit", "-qm", "fixture source")
        item["pin"] = _git(source, "rev-parse", "HEAD").stdout.strip()
    policy_path.write_text(
        json.dumps(policy, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "tools/pegasus/policy.json")
    _git(repo, "commit", "-qm", "fixture floor third-party pins")
    return source_root


def _submit(
    repo: Path,
    bin_dir: Path,
    *arguments: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = _git_env(repo)
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    if extra_env is not None:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(repo / "tools" / "pegasus" / "submit_floor.sh"), *arguments],
        capture_output=True,
        text=True,
        env=env,
    )


def _only_submission(repo: Path, attempts_relative: str) -> Path:
    submissions = repo / attempts_relative / "submissions"
    found = list(submissions.glob("*"))
    assert len(found) == 1
    return found[0]


def _assert_capture_schema(preflight: object, *, dry_run: bool) -> None:
    assert type(preflight) is dict and set(preflight) == PREFLIGHT_KEYS
    for capture in preflight.values():
        assert type(capture) is dict and set(capture) == CAPTURE_KEYS
        assert type(capture["rc"]) is int
        assert type(capture["stdout_raw"]) is str
        assert type(capture["stderr_raw"]) is str
        if dry_run:
            assert capture == {
                "rc": 0,
                "stdout_raw": "not run (--dry-run)\n",
                "stderr_raw": "",
            }


@pytest.mark.parametrize("script", [SUBMIT, JOB], ids=lambda path: path.name)
def test_floor_shell_syntax(script: Path) -> None:
    result = subprocess.run(
        ["bash", "-n", str(script)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_floor_masstree_policy_generator_is_independent_and_has_both_cli_inputs() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    assert '"--source-dir"' in source
    assert '"--output"' in source
    assert 'SCHEMA_VERSION = "s8b-floor-masstree-payload/v3"' in source
    assert "s8b_floor_campaign" not in source
    assert "buildcache" not in source
    assert '"config_sha256"' in source
    assert '"archive_sha256"' not in source
    assert '"archive_nondebug_sha256"' in source
    assert '["make", "-j", "CXXFLAGS=-g -W -Wall -O3 -fPIC"]' in source
    assert '["ar", "cr", archive.name, *MASSTREE_MEMBERS]' in source
    assert '["ranlib", archive.name]' in source
    assert '["objcopy"' not in source
    assert '["strip"' not in source
    assert "readelf" not in source


def test_floor_masstree_policy_generator_requires_force_to_replace_output(
        tmp_path: Path, monkeypatch) -> None:
    spec = importlib.util.spec_from_file_location(
        "floor_masstree_payload_generator_fixture", GENERATOR,
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    output = tmp_path / "policy.json"
    output.write_bytes(b"existing policy bytes\n")
    source = tmp_path / "masstree-src"
    source.mkdir()
    monkeypatch.setattr(
        generator, "_load_policy", lambda _path: ("fixture-url", "a" * 40),
    )
    monkeypatch.setattr(
        generator, "_prepare_source", lambda source_dir, **_kwargs: source_dir,
    )
    monkeypatch.setattr(generator, "_build_and_hash", lambda _source: (
        generator._BuildDigests("b" * 64, "c" * 64, "d" * 64)
    ))

    assert generator.main([
        "--source-dir", str(source), "--output", str(output),
    ]) == 2
    assert output.read_bytes() == b"existing policy bytes\n"

    assert generator.main([
        "--source-dir", str(source), "--output", str(output), "--force",
    ]) == 0
    generated = json.loads(output.read_text(encoding="utf-8"))
    assert set(generated) == {
        "schema_version", "name", "pin", "config_sha256",
        "archive_projection", "archive_nondebug_sha256",
    }
    assert generated["schema_version"] == "s8b-floor-masstree-payload/v3"
    assert generated["config_sha256"] == "b" * 64
    assert generated["archive_projection"] == "gnu-ar-elf-nondebug/v1"
    assert generated["archive_nondebug_sha256"] == "d" * 64


def _fixture_generator_source_repo(tmp_path: Path) -> tuple[Path, str]:
    source = (tmp_path / "generator-source").resolve()
    source.mkdir()
    (source / "bootstrap.sh").write_text(
        "#!/bin/sh\nset -eu\nexit 0\n", encoding="utf-8",
    )
    (source / "configure").write_text(
        """#!/bin/sh
set -eu
value=7
if [ -n "${MASSTREE_FIXTURE_COUNTER:-}" ]; then
  count=0
  if [ -f "$MASSTREE_FIXTURE_COUNTER" ]; then read count < "$MASSTREE_FIXTURE_COUNTER"; fi
  count=$((count + 1))
  printf '%s\n' "$count" > "$MASSTREE_FIXTURE_COUNTER"
  value=$count
fi
printf '#define FIXTURE_CONFIG 1\n' > config.h
sed "s/@VALUE@/$value/g" GNUmakefile.in > GNUmakefile
printf '%s\n' "$PWD" >> "$MASSTREE_FIXTURE_BUILD_LOG"
""",
        encoding="utf-8",
    )
    (source / "GNUmakefile.in").write_text(
        """CXX = g++
OBJECTS = json.o string.o straccum.o str.o msgpack.o clp.o kvrandom.o compiler.o memdebug.o kvthread.o misc.o
.PHONY: all
all: $(OBJECTS)
%.o: fixture.cc config.h
	$(CXX) $(CXXFLAGS) -DFIXTURE_VALUE=@VALUE@ -c -o $@ $<
""",
        encoding="utf-8",
    )
    (source / "fixture.cc").write_text(
        """#ifndef FIXTURE_VALUE
#error FIXTURE_VALUE is required
#endif
extern "C" int fixture_symbol(void) { return FIXTURE_VALUE; }
""",
        encoding="utf-8",
    )
    for executable in (source / "bootstrap.sh", source / "configure"):
        executable.chmod(0o755)
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    subprocess.run(
        [
            "git", "-C", str(source), "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid", "commit", "-qm", "pin",
        ],
        check=True,
    )
    pin = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return source, pin


def _load_floor_masstree_generator(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, GENERATOR)
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    return generator


def _write_generator_shared_policy(path: Path, *, source: Path, pin: str) -> None:
    path.write_text(
        json.dumps({
            "silo_ladder_rung1": {
                "third_party_sources": [
                    {"name": "masstree", "url": str(source), "pin": pin},
                ],
            },
        }),
        encoding="utf-8",
    )


def test_floor_masstree_generator_direct_cli_bootstraps_repo_root(
        tmp_path: Path,
) -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--help"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--source-dir" in result.stdout


def test_floor_masstree_generator_main_builds_two_distinct_clones_before_write(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _load_floor_masstree_generator(
        "floor_masstree_payload_generator_two_build_fixture"
    )
    source, pin = _fixture_generator_source_repo(tmp_path)
    shared_policy = tmp_path / "shared-policy.json"
    _write_generator_shared_policy(shared_policy, source=source, pin=pin)
    output = tmp_path / "policy.json"
    build_log = tmp_path / "build-roots.log"
    monkeypatch.setenv("MASSTREE_FIXTURE_BUILD_LOG", str(build_log))
    monkeypatch.delenv("MASSTREE_FIXTURE_COUNTER", raising=False)
    monkeypatch.setattr(generator, "_policy_path", lambda: shared_policy)

    assert generator.main([
        "--source-dir", str(source), "--output", str(output),
    ]) == 0
    roots = build_log.read_text(encoding="utf-8").splitlines()
    assert len(roots) == 2
    assert roots[0] != roots[1]
    assert {Path(root).parent.name for root in roots} == {"build-a", "build-b"}
    document = json.loads(output.read_text(encoding="utf-8"))
    assert set(document) == {
        "schema_version", "name", "pin", "config_sha256",
        "archive_projection", "archive_nondebug_sha256",
    }
    assert document["archive_projection"] == "gnu-ar-elf-nondebug/v1"
    assert re.fullmatch(r"[0-9a-f]{64}", document["archive_nondebug_sha256"])


def test_floor_masstree_generator_main_preserves_output_when_two_builds_differ(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _load_floor_masstree_generator(
        "floor_masstree_payload_generator_mismatch_fixture"
    )
    source, pin = _fixture_generator_source_repo(tmp_path)
    shared_policy = tmp_path / "shared-policy.json"
    _write_generator_shared_policy(shared_policy, source=source, pin=pin)
    output = tmp_path / "policy.json"
    output.write_bytes(b"existing approved policy\n")
    build_log = tmp_path / "build-roots.log"
    counter = tmp_path / "build-counter"
    monkeypatch.setenv("MASSTREE_FIXTURE_BUILD_LOG", str(build_log))
    monkeypatch.setenv("MASSTREE_FIXTURE_COUNTER", str(counter))
    monkeypatch.setattr(generator, "_policy_path", lambda: shared_policy)

    assert generator.main([
        "--source-dir", str(source), "--output", str(output), "--force",
    ]) == 2
    assert output.read_bytes() == b"existing approved policy\n"
    roots = build_log.read_text(encoding="utf-8").splitlines()
    assert len(roots) == 2 and roots[0] != roots[1]


def test_floor_masstree_policy_generator_clones_source_before_configure(
        tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "floor_masstree_payload_generator_clone_fixture", GENERATOR,
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    source = (tmp_path / "input-source").resolve()
    source.mkdir()
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    tracked = source / "bootstrap.sh"
    tracked.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "bootstrap.sh"], check=True)
    subprocess.run(
        [
            "git", "-C", str(source), "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid", "commit", "-qm", "pin",
        ],
        check=True,
    )
    pin = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    before = tracked.read_bytes()
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    prepared = generator._prepare_source(
        source, url="unused", pin=pin, work_dir=work_dir,
    )

    assert prepared == work_dir / "masstree-src"
    assert prepared != source
    assert tracked.read_bytes() == before
    assert subprocess.run(
        [
            "git", "-C", str(source), "status", "--porcelain=v1",
            "--untracked-files=all", "--ignored=matching",
        ],
        check=True, capture_output=True, text=True,
    ).stdout == ""


def test_floor_masstree_policy_generator_keeps_input_index_bytes_unchanged(
        tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "floor_masstree_payload_generator_index_fixture", GENERATOR,
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    source = (tmp_path / "input-source").resolve()
    source.mkdir()
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    tracked = source / "bootstrap.sh"
    tracked.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "bootstrap.sh"], check=True)
    subprocess.run(
        [
            "git", "-C", str(source), "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid", "commit", "-qm", "pin",
        ],
        check=True,
    )
    pin = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    index = source / ".git" / "index"
    index_before = index.read_bytes()
    tracked_stat = tracked.stat()
    os.utime(
        tracked,
        ns=(tracked_stat.st_atime_ns, tracked_stat.st_mtime_ns + 2_000_000_000),
    )
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    prepared = generator._prepare_source(
        source, url="unused", pin=pin, work_dir=work_dir,
    )

    assert prepared == work_dir / "masstree-src"
    assert generator._git_environment()["GIT_OPTIONAL_LOCKS"] == "0"
    assert index.read_bytes() == index_before


def test_floor_wrapper_preflight_rejection_is_nonmutating_and_starts_no_driver(
    tmp_path: Path,
) -> None:
    (
        completed,
        repo,
        scratch,
        mkdir_marker,
        driver_marker,
        checkpoint,
        output_before,
        scratch_before,
    ) = _run_floor_admission_fixture(tmp_path, preflight_rc=3)

    assert completed.returncode == 3
    assert completed.stdout == ""
    assert completed.stderr == '{"gate":"fixture","reason":"rejected"}\n'
    assert _path_tree_snapshot(repo / "output") == output_before
    assert _path_tree_snapshot(scratch) == scratch_before
    assert not mkdir_marker.exists()
    assert not driver_marker.exists()
    records, incomplete = _checkpoint_records(checkpoint)
    assert incomplete is False
    assert [
        (record["stage"], record["transition"], record["durability"], record["rc"])
        for record in records
    ] == [
        ("bootstrap", "entered", "process-kill", None),
        ("static-admission", "entered", "fsynced", None),
        ("static-admission", "rejected", "fsynced", 3),
    ]
    assert not list((repo / "output").rglob("failure.json"))
    assert not list((repo / "output").rglob("failure-interpreter.txt"))
    assert not list((repo / "output").rglob("floor-driver.launch-attempted"))


def test_floor_wrapper_accepting_source_commit_preflight_reaches_first_write(
    tmp_path: Path,
) -> None:
    (
        completed,
        repo,
        scratch,
        mkdir_marker,
        driver_marker,
        checkpoint,
        output_before,
        scratch_before,
    ) = _run_floor_admission_fixture(tmp_path, preflight_rc=0)

    # The mkdir sentinel is the first non-diagnostic scratch mutation attempt.
    # It deliberately fails so the test does not create real /scr state.
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "TMPDIR already exists or cannot be created" in completed.stderr
    assert mkdir_marker.is_file()
    assert not driver_marker.exists()
    records, incomplete = _checkpoint_records(checkpoint)
    assert incomplete is False
    assert records[-1]["stage"] == "attempt-setup"
    assert records[-1]["transition"] == "failed"
    assert records[-1]["rc"] == 2
    assert _path_tree_snapshot(repo / "output") == output_before
    assert _path_tree_snapshot(scratch) == scratch_before


def test_floor_wrapper_streams_helper_blob_without_hash_literal() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert (
        'git -C "$REPO_ROOT" cat-file blob "$PREFLIGHT_HELPER_SPEC"'
        in source
    )
    assert (
        '| "$PREFLIGHT_PY" -I -B - floor --repo-root "$REPO_ROOT"'
        in source
    )
    preflight = source[:source.index('export TMPDIR="/scr/')]
    assert not re.search(r"[0-9a-f]{64}", preflight)


def test_fixture_git_environment_ignores_external_config_and_hooks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    external_home = tmp_path / "external-home"
    hooks = external_home / "hooks"
    hooks.mkdir(parents=True)
    sentinel = tmp_path / "external-hook-ran"
    pre_commit = hooks / "pre-commit"
    pre_commit.write_text(
        "#!/bin/sh\n"
        f"printf ran > {shlex.quote(str(sentinel))}\n"
        "exit 91\n",
        encoding="utf-8",
    )
    pre_commit.chmod(0o755)
    external_config = external_home / "gitconfig"
    external_config.write_text(
        "[core]\n"
        f"\thooksPath = {hooks}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(external_home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(external_config))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(external_config))

    repo = _fixture_repo(tmp_path)
    assert (repo / ".git").is_dir()
    assert not sentinel.exists()


def test_floor_pbs_directives_match_shared_and_floor_policies() -> None:
    shared_policy = json.loads(SHARED_POLICY.read_text(encoding="utf-8"))
    floor_policy = json.loads(FLOOR_POLICY.read_text(encoding="utf-8"))
    directives = _pbs_directives(JOB)
    assert directives.pop("--accept-sigterm") == "yes"
    assert directives == {
        "-A": shared_policy["project"],
        "-q": shared_policy["queue"],
        "-l": "elapstim_req=" + floor_policy["floor_walltime"],
        "-b": str(shared_policy["nodes"]),
    }
    assert (
        _hms_seconds(floor_policy["floor_walltime"])
        == floor_policy["floor_walltime_s"]
    )


def test_floor_policy_covers_derived_reservation_envelope() -> None:
    floor_policy = json.loads(FLOOR_POLICY.read_text(encoding="utf-8"))
    required_s, finalize_s = _derived_floor_reservation_budget()
    assert floor_policy["floor_walltime_s"] > required_s + finalize_s
    assert (
        _hms_seconds(floor_policy["floor_walltime"])
        == floor_policy["floor_walltime_s"]
    )


def test_floor_job_budget_comments_preserve_m1_m2_labeled_relationships() -> None:
    source = JOB.read_text(encoding="utf-8")
    block_start = source.index("# 12-cell subtotal")
    block_end = source.index("\nset -Eeuo pipefail", block_start)
    budget_block = source[block_start:block_end]
    subtotal = 12 * (900 + (8 + 2) * (5 * 5 + 120))
    prebuild = 900 + 900
    required_s, finalize_s = _derived_floor_reservation_budget()
    assert subtotal == 28200
    assert subtotal + prebuild == required_s
    minimum = required_s + finalize_s
    floor_policy = json.loads(FLOOR_POLICY.read_text(encoding="utf-8"))
    request = floor_policy["floor_walltime_s"]
    raw = request - minimum
    prologue = 900
    residual = raw - prologue
    assert residual == 4500
    assert re.fullmatch(
        rf"# 12-cell subtotal\s*=\s*"
        rf"12 \* \(900 \+ \(8\+2\) \* \(5\*5 \+ 120\)\) = {subtotal}\n"
        rf"# shared dependency prebuild\s*=\s*900 \+ 900 = {prebuild}\n"
        rf"# driver required_s\s*=\s*{subtotal} \+ {prebuild} = {required_s}\n"
        rf"# driver finalize reserve\s*=\s*{finalize_s}\n"
        rf"# driver preflight minimum envelope\s*=\s*"
        rf"{required_s} \+ {finalize_s} = {minimum}\n"
        rf"# PBS request\s*=\s*{request}\s+"
        rf"\(= {re.escape(floor_policy['floor_walltime'])},[^\n]*\)\n"
        rf"# raw headroom\s*=\s*{request} - {minimum} = {raw}\n"
        rf"# job prologue \([^\n]*\) 見積\s*≈\s*{prologue}\n"
        rf"# estimated residual headroom\s*≈\s*"
        rf"{raw} - {prologue} = {residual} \(保証値・実測値ではない\)",
        budget_block,
    )


def test_floor_readme_section_5_preserves_m3_labeled_envelope() -> None:
    source = PEGASUS_README.read_text(encoding="utf-8")
    section_match = re.search(
        r"(?ms)^## 5\..*?(?=^## \d|\Z)",
        source,
    )
    assert section_match is not None
    bullet_match = re.search(
        r"(?ms)^- scheduler への walltime 要求宣言.*?(?=^- |\Z)",
        section_match.group(0),
    )
    assert bullet_match is not None
    required_s, finalize_s = _derived_floor_reservation_budget()
    floor_policy = json.loads(FLOOR_POLICY.read_text(encoding="utf-8"))
    request = floor_policy["floor_walltime_s"]
    subtotal = 12 * (900 + (8 + 2) * (5 * 5 + 120))
    prebuild = 900 + 900
    assert subtotal + prebuild == required_s
    minimum = required_s + finalize_s
    assert re.fullmatch(
        rf"- scheduler への walltime 要求宣言は job script の "
        rf"`{re.escape(floor_policy['floor_walltime'])}` \({request} 秒\)。"
        rf"policy の\s+`floor_walltime_s={request}` は期待値・submit receipt 値で、"
        rf"job は qstat の実効\s+`\(Per-Req\) Elapse Time Limit` との一致を "
        rf"fail-closed で検査する。現行 driver の\s+minimum envelope は "
        rf"required {required_s} \(12-cell subtotal {subtotal} \+ "
        rf"shared prebuild {prebuild}\) \+\s+finalize reserve {finalize_s} = "
        rf"{minimum} 秒である。",
        bullet_match.group(0).strip(),
    )


def test_floor_job_binds_executing_script_bytes() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert 'EXECUTING_SCRIPT_SHA256=$(sha256sum "$0"' in source
    assert (
        '[[ "$EXECUTING_SCRIPT_SHA256" != "$RECEIPT_SCRIPT_SHA256" ]]' in source
    )
    assert "executing job script hash differs from submit receipt" in source


def _source_identity_fragment() -> str:
    source = JOB.read_text(encoding="utf-8")
    start = source.index('SCRIPT_RELATIVE_PATH="tools/pegasus/floor_campaign.sh"')
    end = source.index("# 出典: certify_calibration.sh:210-318", start)
    return source[start:end]


def test_floor_job_binds_repo_blob_hash(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    repo_job = repo / "tools" / "pegasus" / "floor_campaign.sh"
    spooled_job = tmp_path / "spooled-floor_campaign.sh"
    shutil.copy2(repo_job, spooled_job)
    source_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    blob_sha = hashlib.sha256(
        _git_bytes(
            repo,
            "cat-file",
            "blob",
            source_commit + ":tools/pegasus/floor_campaign.sh",
        )
    ).hexdigest()
    _git(repo, "update-index", "--assume-unchanged", "tools/pegasus/floor_campaign.sh")
    repo_job.write_text(
        repo_job.read_text(encoding="utf-8") + "\n# hidden working-tree mutation\n",
        encoding="utf-8",
    )
    assert _git(repo, "status", "--porcelain").stdout == ""

    attempt = tmp_path / "attempt"
    attempt.mkdir()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (attempt / "submit-receipt.json").write_text(
        json.dumps(
            {
                "source_commit": source_commit,
                "job_script_sha256": blob_sha,
            }
        ),
        encoding="utf-8",
    )
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"TMPDIR={shlex.quote(str(scratch))}",
            f"PY={shlex.quote(sys.executable)}",
            "checkpoint_event() { return 0; }",
            "write_failure() { return 0; }",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _source_identity_fragment(), str(spooled_job)],
        capture_output=True,
        text=True,
        env=_git_env(repo),
    )
    assert result.returncode == 0, result.stderr


def test_floor_job_rejects_working_tree_script_that_differs_from_blob(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    relative = "tools/pegasus/floor_campaign.sh"
    repo_job = repo / relative
    source_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "update-index", "--assume-unchanged", relative)
    repo_job.write_text(
        repo_job.read_text(encoding="utf-8") + "\n# hidden spooled mutation\n",
        encoding="utf-8",
    )
    assert _git(repo, "status", "--porcelain").stdout == ""
    spooled_job = tmp_path / "spooled-floor_campaign.sh"
    shutil.copy2(repo_job, spooled_job)
    mutated_sha = hashlib.sha256(spooled_job.read_bytes()).hexdigest()

    attempt = tmp_path / "attempt"
    attempt.mkdir()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (attempt / "submit-receipt.json").write_text(
        json.dumps(
            {
                "source_commit": source_commit,
                "job_script_sha256": mutated_sha,
            }
        ),
        encoding="utf-8",
    )
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"TMPDIR={shlex.quote(str(scratch))}",
            f"PY={shlex.quote(sys.executable)}",
            "checkpoint_event() { return 0; }",
            "write_failure() { return 0; }",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _source_identity_fragment(), str(spooled_job)],
        capture_output=True,
        text=True,
        env=_git_env(repo),
    )
    assert result.returncode == 2, result.stderr


def test_floor_job_binds_scheduler_elapse_limit() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert r"\s*\(Per-Req\)\s+Elapse Time Limit" in source
    assert "SCHEDULER_ELAPSE_LIMIT_S" in source
    assert (
        '[[ "$SCHEDULER_ELAPSE_LIMIT_S" -ne "$REQUESTED_S_POLICY" ]]' in source
    )
    assert "scheduler Elapse Time Limit differs from floor policy" in source


def test_floor_job_uses_scheduler_requested_seconds() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert 'REQUESTED_S="$SCHEDULER_ELAPSE_LIMIT_S"' in source
    assert (
        'export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"' in source
    )


def _shell_interpreter_invocations(source: str) -> Counter[tuple[str, str, str]]:
    lexer = shlex.shlex(source, posix=True, punctuation_chars=True)
    lexer.commenters = "#"
    lexer.whitespace_split = True
    tokens = list(lexer)
    candidates: list[tuple[str, str, str]] = []
    for index, token in enumerate(tokens[:-2]):
        variable = re.fullmatch(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?", token)
        executable = re.fullmatch(r"(?:.*/)?python(?:3(?:\.\d+)?)?", token)
        if (
            tokens[index + 1:index + 3] == ["-I", "-B"]
            and (variable is not None or executable is not None)
        ):
            candidates.append((token, "-I", "-B"))
    return Counter(candidates)


def test_floor_job_hardens_interpreter() -> None:
    source = JOB.read_text(encoding="utf-8")
    submit = SUBMIT.read_text(encoding="utf-8")
    assert "unset PYTHONPATH PYTHONHOME PYTHONSTARTUP" in source
    assert 'py_resolved=$(realpath -e -- "$py_cmd")' in source
    assert "sys.version_info[:2] >= (3, 10)" in source
    assert '"$py_resolved" -I -B -c' in source
    assert '"$PY" -I -B --version' in source
    assert '"$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_floor_campaign.py"' in source
    assert "-E -s -B" not in source
    role_anchors = (
        '"$PY" -I -B - "$ATTEMPT_DIR/failure.json"',
        '"$PY" -I -B --version',
        '"$PY" -I -B - "$POLICY" "$FLOOR_POLICY"',
        '"$PY" -I -B - "$SUBMIT_SOURCE"',
        '"$PY" -I -B - "$ATTEMPT_DIR/submit-receipt.json" "$IZANAGI_SUBMISSION_NONCE"',
        'RECEIPT_SCRIPT_SHA256=$("$PY" -I -B',
        'RECEIPT_SOURCE_COMMIT=$("$PY" -I -B',
        'qstat_output=$("$PY" -I -B',
        '"$PY" -I -B - "$ATTEMPT_DIR/allocation-unavailable.json"',
        '"$PY" -I -B - "$ATTEMPT_DIR/scheduler-elapse.json"',
        '"$PY" -I -B - "$ATTEMPT_DIR/reservation.json"',
        '"$PY" -I -B - "$ATTEMPT_DIR/cmake-prefix-path.json"',
        'protocol_resolution_output=$(\n  "$PY" -I -B',
        'driver_argv=(\n  "$PY" -I -B',
        '"$PY" -I -B - "$ATTEMPT_DIR/floor-driver.stdout"',
        '"$PY" -I -B - "$ATTEMPT_DIR/job-result.json"',
    )
    assert all(source.count(anchor) == 1 for anchor in role_anchors)
    invocation_counts = {
        "interpreter-version-gates": source.count('"$py_resolved" -I -B -c'),
        "preflight-checkpoint-and-admission": source.count(
            '"$PREFLIGHT_PY" -I -B'
        ),
        "runtime-driver-and-records": len(role_anchors),
    }
    assert invocation_counts == {
        "interpreter-version-gates": 2,
        "preflight-checkpoint-and-admission": 3,
        "runtime-driver-and-records": 16,
    }
    assert sum(invocation_counts.values()) == 21
    assert _shell_interpreter_invocations(source) == Counter({
        ("$py_resolved", "-I", "-B"): 2,
        ("$PREFLIGHT_PY", "-I", "-B"): 3,
        ("$PY", "-I", "-B"): 16,
    })
    assert _shell_interpreter_invocations(submit) == Counter({
        ("python3", "-I", "-B"): 7,
    })
    normal_checkpoint_stages = re.findall(
        r'^CURRENT_STAGE=([^\n]+)\nif ! checkpoint_event "\$CURRENT_STAGE" entered',
        source,
        re.MULTILINE,
    )
    assert normal_checkpoint_stages == [
        "static-admission", "attempt-setup", "policy", "submit-binding",
        "source-identity", "allocation-reservation", "gflags-build",
        "glog-build", "protocol-resolution", "floor-driver", "job-result",
    ]
    assert len(re.findall(r"(?<![A-Za-z0-9_])python3(?=\s)", submit)) == 7
    assert submit.count("python3 -I -B") == 7
    assert re.search(r"(?<![A-Za-z0-9_])python3\s+(?!-I -B)", submit) is None


@pytest.mark.parametrize(
    ("extra", "signature"),
    [
        ('\nOTHER_PY="$PY"\n"$OTHER_PY" -I -B -c pass\n', "$OTHER_PY"),
        ("\nenv python3 -I -B -c pass\n", "python3"),
        ("\n/usr/bin/python3 -I -B -c pass\n", "/usr/bin/python3"),
    ],
)
def test_floor_interpreter_inventory_rejects_every_unregistered_spelling(
    extra: str, signature: str,
) -> None:
    source = JOB.read_text(encoding="utf-8")
    expected = _shell_interpreter_invocations(source)
    observed = _shell_interpreter_invocations(source + extra)
    assert observed != expected
    assert observed[(signature, "-I", "-B")] == (
        expected[(signature, "-I", "-B")] + 1
    )


def _append_fixture_checkpoint(
    root: Path,
    *,
    job_id: str = "0:98765.nqsv",
    nonce: str = "a" * 32,
    stage: str = "bootstrap",
    transition: str = "entered",
    rc: int | None = None,
    command: str | None = None,
    run_dir: str | None = None,
    journal_path: str | None = None,
    bounded_timeout_s: float | None = None,
) -> bool:
    writer = (
        floor_job_checkpoint.try_append_checkpoint
        if bounded_timeout_s is None
        else floor_job_checkpoint.try_append_checkpoint_bounded
    )
    return writer(
        **({"timeout_s": bounded_timeout_s} if bounded_timeout_s is not None else {}),
        path=floor_job_checkpoint.checkpoint_path(root, job_id, nonce),
        job_id=job_id,
        nonce=nonce,
        producer=(
            "s8b_floor_campaign.py"
            if transition == "run-linked" else "floor_campaign.sh"
        ),
        stage=stage,
        transition=transition,
        rc=rc,
        command=command,
        durability="fsynced",
        repo_root="/fixture/repo",
        attempt_dir="/fixture/attempt",
        run_dir=run_dir,
        journal_path=journal_path,
    )


def test_floor_driver_consumes_checkpoint_environment_before_core_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = floor_job_checkpoint.checkpoint_path(
        tmp_path / "evidence", "0:98765.nqsv", "a" * 32,
    )
    monkeypatch.setenv(floor_job_checkpoint.CHECKPOINT_ENV, str(path))
    monkeypatch.setenv(
        floor_job_checkpoint.EVIDENCE_ROOT_ENV, str(tmp_path / "evidence"),
    )
    monkeypatch.setenv("IZANAGI_RESERVATION_JOB_ID", "0:98765.nqsv")
    monkeypatch.setenv("IZANAGI_RESERVATION_NONCE", "a" * 32)

    def reject_mode(_mode: object) -> str:
        assert floor_job_checkpoint.CHECKPOINT_ENV not in os.environ
        assert floor_job_checkpoint.EVIDENCE_ROOT_ENV not in os.environ
        observed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                "import json,os; print(json.dumps(sorted(k for k in os.environ "
                "if k.startswith('IZANAGI_FLOOR_JOB_'))))",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(observed.stdout) == []
        raise s8b_floor_campaign.FloorCampaignError("core dispatch sentinel")

    monkeypatch.setattr(s8b_floor_campaign, "_validate_mode", reject_mode)
    with pytest.raises(
        s8b_floor_campaign.FloorCampaignError, match="core dispatch sentinel",
    ):
        s8b_floor_campaign._run_campaign_core(
            {}, object(), out_root=tmp_path / "out", mode="pilot",
        )


def test_floor_driver_links_fresh_run_before_build_with_bounded_diagnostic_child() -> None:
    source = Path(s8b_floor_campaign.__file__).read_text(encoding="utf-8")
    fresh_start = source.index("if resume_dir is None:", source.index("def _run_campaign_core"))
    journal_index = source.index('journal_path = run_dir / "journal.jsonl"', fresh_start)
    link_index = source.index(
        "floor_job_checkpoint.try_append_checkpoint_bounded(", journal_index,
    )
    build_index = source.index("runtime_built = build_cells(", link_index)
    assert journal_index < link_index < build_index
    link_block = source[link_index:build_index]
    assert 'transition="run-linked"' in link_block
    assert 'journal_path=str(journal_path)' in link_block
    assert not re.search(r"subprocess|Popen|system\(", link_block)
    helper_source = Path(floor_job_checkpoint.__file__).read_text(encoding="utf-8")
    bounded_start = helper_source.index("def _bounded_boolean_child(")
    bounded_end = helper_source.index("def normalize_job_id(", bounded_start)
    bounded = helper_source[bounded_start:bounded_end]
    assert "select.select(" in bounded
    assert "os.kill(child, signal.SIGALRM)" in bounded
    assert "os.waitpid(child, os.WNOHANG)" in bounded


@pytest.mark.parametrize(
    "fault_name", ["open", "mkdir", "write", "fsync"],
)
def test_floor_checkpoint_writer_faults_never_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault_name: str,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()

    def fail(*_args: object, **_kwargs: object) -> object:
        raise OSError(f"injected {fault_name} failure")

    monkeypatch.setattr(floor_job_checkpoint.os, fault_name, fail)
    assert _append_fixture_checkpoint(
        root, bounded_timeout_s=0.04,
    ) is False


@pytest.mark.parametrize("fault_name", ["open", "write", "fsync"])
def test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault_name: str,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    monkeypatch.setattr(floor_job_checkpoint, "_DIAGNOSTIC_IO_TIMEOUT_S", 0.02)

    def hang(*_args: object, **_kwargs: object) -> object:
        time.sleep(5)
        raise AssertionError("diagnostic timeout did not interrupt the syscall")

    monkeypatch.setattr(floor_job_checkpoint.os, fault_name, hang)
    started = time.monotonic()
    assert _append_fixture_checkpoint(
        root, bounded_timeout_s=0.04,
    ) is False
    assert time.monotonic() - started < 0.5


def test_floor_checkpoint_writer_reopens_after_transient_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    real_write = floor_job_checkpoint.os.write
    calls = 0

    def fail_once(descriptor: int, payload: bytes) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("transient write failure")
        return real_write(descriptor, payload)

    monkeypatch.setattr(floor_job_checkpoint.os, "write", fail_once)
    assert _append_fixture_checkpoint(root) is True
    records, incomplete, _path = floor_job_checkpoint.read_checkpoint(
        root, "98765.nqsv", "a" * 32,
    )
    assert len(records) == 1
    assert incomplete is False


def test_floor_checkpoint_short_write_is_bounded_and_never_escapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    assert _append_fixture_checkpoint(root) is True
    checkpoint = floor_job_checkpoint.checkpoint_path(
        root, "98765.nqsv", "a" * 32,
    )
    existing = checkpoint.read_bytes()
    real_write = floor_job_checkpoint.os.write
    calls = 0

    def write_prefix_then_fail(descriptor: int, payload: bytes) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_write(descriptor, payload[:-1])
        raise OSError("injected failure after a real short write")

    monkeypatch.setattr(
        floor_job_checkpoint.os, "write", write_prefix_then_fail,
    )
    assert _append_fixture_checkpoint(root, stage="policy") is False
    assert checkpoint.read_bytes() == existing
    monkeypatch.setattr(floor_job_checkpoint.os, "write", real_write)
    assert _append_fixture_checkpoint(root, stage="policy") is True
    records, incomplete, _path = floor_job_checkpoint.read_checkpoint(
        root, "98765.nqsv", "a" * 32,
    )
    assert incomplete is False
    assert [record["stage"] for record in records] == ["bootstrap", "policy"]


def test_floor_checkpoint_failure_does_not_disable_later_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    real_write = floor_job_checkpoint.os.write
    monkeypatch.setattr(
        floor_job_checkpoint.os, "write",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("offline")),
    )
    assert _append_fixture_checkpoint(root) is False
    monkeypatch.setattr(floor_job_checkpoint.os, "write", real_write)
    assert _append_fixture_checkpoint(root, stage="policy") is True
    source = JOB.read_text(encoding="utf-8")
    assert source.count("CHECKPOINT_ENABLED=0") == 1
    assert "for writer_attempt in 1 2; do" in source


@pytest.mark.parametrize("symlink_level", ["root", "intermediate", "leaf"])
def test_floor_checkpoint_rejects_symlink_at_every_namespace_level(
    tmp_path: Path, symlink_level: str,
) -> None:
    protected = tmp_path / "repo-output"
    protected.mkdir()
    sentinel = protected / "sentinel"
    sentinel.write_text("unchanged\n", encoding="utf-8")
    root = tmp_path / "evidence"
    job = "98765.nqsv"
    nonce = "a" * 32
    if symlink_level == "root":
        root.symlink_to(protected, target_is_directory=True)
    else:
        root.mkdir()
        if symlink_level == "intermediate":
            (root / "pegasus").symlink_to(protected, target_is_directory=True)
        else:
            leaf_parent = root / "pegasus" / job / nonce
            leaf_parent.mkdir(parents=True)
            (leaf_parent / "checkpoint.jsonl").symlink_to(sentinel)

    assert _append_fixture_checkpoint(root) is False
    assert sentinel.read_text(encoding="utf-8") == "unchanged\n"
    assert not list(protected.rglob("checkpoint.jsonl"))


def test_floor_checkpoint_dirfd_contains_post_validation_root_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    moved = tmp_path / "evidence-opened"
    protected = tmp_path / "repo-output"
    protected.mkdir()
    real_open_root = floor_job_checkpoint._open_absolute_directory

    def swap_after_open(path: Path) -> int:
        descriptor = real_open_root(path)
        path.rename(moved)
        path.symlink_to(protected, target_is_directory=True)
        return descriptor

    monkeypatch.setattr(
        floor_job_checkpoint, "_open_absolute_directory", swap_after_open,
    )
    assert _append_fixture_checkpoint(root) is True
    assert not list(protected.rglob("checkpoint.jsonl"))
    assert list(moved.rglob("checkpoint.jsonl"))


def _run_floor_bootstrap(
    repo: Path, evidence_root: Path, *, path_prefix: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    source = JOB.read_text(encoding="utf-8")
    bootstrap = source[:source.index('PREFLIGHT_PY=""')]
    environment = dict(os.environ)
    environment.update({
        "PBS_JOBID": "0:98765.nqsv",
        "PBS_O_WORKDIR": str(repo),
        "IZANAGI_SUBMISSION_NONCE": "c" * 32,
        floor_job_checkpoint.EVIDENCE_ROOT_ENV: str(evidence_root),
    })
    if path_prefix is not None:
        environment["PATH"] = f"{path_prefix}:{environment['PATH']}"
    return subprocess.run(
        ["/bin/bash", "-c", bootstrap],
        capture_output=True,
        text=True,
        env=environment,
    )


@pytest.mark.parametrize("symlink_level", ["root", "intermediate", "leaf"])
def test_floor_bootstrap_w1_rejects_each_symlink_level(
    tmp_path: Path, symlink_level: str,
) -> None:
    repo = _fixture_repo(tmp_path)
    protected = repo / "output" / "w1-protected"
    protected.mkdir()
    sentinel = protected / "sentinel"
    sentinel.write_text("unchanged\n", encoding="utf-8")
    root = tmp_path / "w1-evidence"
    nonce = "c" * 32
    if symlink_level == "root":
        root.symlink_to(protected, target_is_directory=True)
    else:
        root.mkdir()
        if symlink_level == "intermediate":
            (root / "pegasus").symlink_to(protected, target_is_directory=True)
        else:
            parent = root / "pegasus" / "98765.nqsv" / nonce
            parent.mkdir(parents=True)
            (parent / "checkpoint.jsonl").symlink_to(sentinel)

    completed = _run_floor_bootstrap(repo, root)
    assert completed.returncode == 0, completed.stderr
    assert sentinel.read_text(encoding="utf-8") == "unchanged\n"
    assert not list(protected.rglob("checkpoint.jsonl"))


def test_floor_bootstrap_w1_parent_fd_rejects_post_validation_swap(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    root = tmp_path / "w1-evidence"
    protected = repo / "output" / "w1-swap-target"
    protected.mkdir()
    nonce = "c" * 32
    parent = root / "pegasus" / "98765.nqsv" / nonce
    moved = parent.with_name(nonce + "-opened")
    marker = tmp_path / "stat-swap-fired"
    bin_dir = tmp_path / "swap-bin"
    bin_dir.mkdir()
    real_stat = shutil.which("stat")
    assert real_stat is not None
    (bin_dir / "stat").write_text(
        "#!/bin/bash\n"
        f"target={shlex.quote(str(parent))}\n"
        f"moved={shlex.quote(str(moved))}\n"
        f"protected={shlex.quote(str(protected))}\n"
        f"marker={shlex.quote(str(marker))}\n"
        f"real_stat={shlex.quote(real_stat)}\n"
        "if [[ ! -e \"$marker\" && \"${!#}\" == \"$target\" ]]; then\n"
        "  observed=$(\"$real_stat\" \"$@\") || exit $?\n"
        "  : >\"$marker\"\n"
        "  mv -- \"$target\" \"$moved\" || exit $?\n"
        "  ln -s -- \"$protected\" \"$target\" || exit $?\n"
        "  printf '%s\\n' \"$observed\"\n"
        "  exit 0\n"
        "fi\n"
        "exec \"$real_stat\" \"$@\"\n",
        encoding="utf-8",
    )
    (bin_dir / "stat").chmod(0o755)

    completed = _run_floor_bootstrap(repo, root, path_prefix=bin_dir)
    assert completed.returncode == 0, completed.stderr
    assert marker.exists()
    assert not (protected / "checkpoint.jsonl").exists()
    assert not (moved / "checkpoint.jsonl").exists()
    source = JOB.read_text(encoding="utf-8")
    assert '"/proc/self/fd/$CHECKPOINT_BOOTSTRAP_PARENT_FD"' in source
    assert 'exec {CHECKPOINT_BOOTSTRAP_FD}>"$checkpoint_fd_leaf"' in source


def test_floor_checkpoint_shell_helper_preserves_original_rc_when_stderr_is_closed(
    tmp_path: Path,
) -> None:
    source = JOB.read_text(encoding="utf-8")
    start = source.index("checkpoint_event() {")
    end = source.index("CURRENT_STAGE=static-admission", start)
    checkpoint = tmp_path / "checkpoint.jsonl"
    checkpoint.write_text("sentinel\n", encoding="utf-8")
    prefix = "\n".join([
        "set -Eeuo pipefail",
        "CHECKPOINT_ENABLED=1",
        f"PREFLIGHT_PY={shlex.quote('/bin/false')}",
        f"REPO_ROOT={shlex.quote(str(tmp_path))}",
        f"CHECKPOINT_PATH={shlex.quote(str(checkpoint))}",
        "PBS_JOBID=0:98765.nqsv",
        f"IZANAGI_SUBMISSION_NONCE={'a' * 32}",
        "ATTEMPT_DIR=/fixture/attempt",
        "",
    ])
    result = subprocess.run(
        [
            "bash", "-c",
            prefix + source[start:end]
            + "\nexec 2>&-\ncheckpoint_event floor-driver failed 7 injected\nexit 7\n",
        ],
    )
    assert result.returncode == 7
    assert checkpoint.read_text(encoding="utf-8") == "sentinel\n"


@pytest.mark.parametrize(
    ("trigger", "expected_rc"),
    [("false", 1), ("kill -TERM $$", 143)],
)
def test_floor_checkpoint_failure_in_err_and_signal_traps_preserves_evidence(
    tmp_path: Path, trigger: str, expected_rc: int,
) -> None:
    source = JOB.read_text(encoding="utf-8")
    assert source.index("#PBS --accept-sigterm=yes") < source.index(
        "set -Eeuo pipefail"
    )
    start = source.index("failure_written=0")
    end = source.index("CURRENT_STAGE=policy", start)
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    failure = attempt / "failure.json"
    original = b'{"existing":"authority"}\n'
    failure.write_bytes(original)
    prefix = "\n".join([
        "set -Eeuo pipefail",
        f"PY={shlex.quote(sys.executable)}",
        f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
        "PBS_JOBID=0:98765.nqsv",
        "CURRENT_STAGE=floor-driver",
        "checkpoint_event() { return 1; }",
        "",
    ])
    command = [
        "bash", "-c", prefix + source[start:end] + "\n" + trigger + "\n",
    ]
    if trigger == "kill -TERM $$":
        # A batch/xdist parent may leave TERM ignored or blocked.  Normalize it
        # in an exec launcher so this test controls the signal-delivery premise.
        signal_reset_launcher = (
            "import os,signal,sys\n"
            "signal.signal(signal.SIGTERM,signal.SIG_DFL)\n"
            "signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM})\n"
            "os.execvp(sys.argv[1],sys.argv[1:])\n"
        )
        command = [
            sys.executable, "-I", "-S", "-B", "-c", signal_reset_launcher,
            *command,
        ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == expected_rc
    assert failure.read_bytes() == original


def test_floor_checkpoint_stage_machine_and_completed_boundaries_are_fixed() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert source.index("CURRENT_STAGE=bootstrap") < source.index("trap on_err ERR")
    assert 'local command=${BASH_COMMAND:-unknown}' in source
    assert (
        'checkpoint_event "$CURRENT_STAGE" failed "$rc" "$command"' in source
    )
    write_failure = source[
        source.index("write_failure() {"):source.index("write_interpreter_failure() {")
    ]
    assert 'checkpoint_event "$stage" "$checkpoint_transition"' in write_failure
    assert 'checkpoint_event "$CURRENT_STAGE" "$checkpoint_transition"' not in write_failure
    transitions = re.findall(
        r'checkpoint_event "\$CURRENT_STAGE" ([a-z-]+)', source,
    )
    assert "completed" not in transitions
    assert {"entered", "failed", "signalled"}.issubset(transitions)
    assert '\\"durability\\":\\"process-kill\\"' in source
    bootstrap_line = next(
        line for line in source.splitlines() if "process-kill" in line
    )
    assert "fsynced" not in bootstrap_line


def test_floor_evidence_index_is_create_only_and_time_bounded(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    nonce = "a" * 32
    assert floor_job_checkpoint.try_create_index(
        root=root,
        job_id="98765.nqsv",
        nonce=nonce,
        submitted_at=1700000000,
        requested_root=None,
        login_probe_status="default-readable",
    ) is True
    job_path, time_path = floor_job_checkpoint.index_paths(
        root, "98765.nqsv", nonce, 1700000000,
    )
    before = (job_path.read_bytes(), time_path.read_bytes())
    assert floor_job_checkpoint.try_create_index(
        root=root,
        job_id="0:98765.nqsv",
        nonce=nonce,
        submitted_at=1700000000,
        requested_root=None,
        login_probe_status="default-readable",
    ) is True
    assert (job_path.read_bytes(), time_path.read_bytes()) == before
    assert floor_job_checkpoint.try_create_index(
        root=root,
        job_id="98765.nqsv",
        nonce=nonce,
        submitted_at=1700000000,
        requested_root="/different",
        login_probe_status="override-readable",
    ) is False
    assert (job_path.read_bytes(), time_path.read_bytes()) == before
    resolved = floor_job_checkpoint.resolve_indices_by_time(
        root, earliest=1699999999, latest=1700000001, max_entries=1,
    )
    assert [record["submission_nonce"] for record in resolved] == [nonce]


@pytest.mark.parametrize("fault_name", ["open", "write", "fsync"])
def test_floor_evidence_index_recovers_each_second_leaf_fault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault_name: str,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    nonce = "b" * 32
    real_operation = getattr(floor_job_checkpoint.os, fault_name)
    injected = False

    def is_time_leaf(descriptor: int) -> bool:
        try:
            return "/index/by-time/" in os.readlink(f"/proc/self/fd/{descriptor}")
        except OSError:
            return False

    if fault_name == "open":
        def fail_second_open(
            path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None,
        ) -> int:
            nonlocal injected
            if (
                not injected
                and type(path) is str
                and path.endswith(".json")
                and dir_fd is not None
                and is_time_leaf(dir_fd)
            ):
                injected = True
                raise OSError("injected second index create failure")
            return real_operation(path, flags, mode, dir_fd=dir_fd)

        monkeypatch.setattr(floor_job_checkpoint.os, "open", fail_second_open)
    elif fault_name == "write":
        def fail_second_write(descriptor: int, payload: bytes) -> int:
            nonlocal injected
            if not injected and is_time_leaf(descriptor):
                injected = True
                raise OSError("injected second index write failure")
            return real_operation(descriptor, payload)

        monkeypatch.setattr(floor_job_checkpoint.os, "write", fail_second_write)
    else:
        def fail_second_fsync(descriptor: int) -> None:
            nonlocal injected
            if not injected and is_time_leaf(descriptor):
                injected = True
                raise OSError("injected second index fsync failure")
            real_operation(descriptor)

        monkeypatch.setattr(floor_job_checkpoint.os, "fsync", fail_second_fsync)

    arguments = {
        "root": root,
        "job_id": "98765.nqsv",
        "nonce": nonce,
        "submitted_at": 1700000001,
        "requested_root": None,
        "login_probe_status": "default-readable",
    }
    assert floor_job_checkpoint.try_create_index(**arguments) is False
    assert injected is True
    monkeypatch.setattr(floor_job_checkpoint.os, fault_name, real_operation)
    assert floor_job_checkpoint.try_create_index(**arguments) is True
    job_path, time_path = floor_job_checkpoint.index_paths(
        root, "98765.nqsv", nonce, 1700000001,
    )
    assert job_path.read_bytes() == time_path.read_bytes()
    assert floor_job_checkpoint.resolve_indices_by_time(
        root, earliest=1700000001, latest=1700000001, max_entries=1,
    )[0]["submission_nonce"] == nonce


def test_floor_time_resolver_bound_counts_matches_not_lifetime_history(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    for ordinal in range(129):
        assert floor_job_checkpoint.try_create_index(
            root=root,
            job_id=f"old-{ordinal}.nqsv",
            nonce=f"{ordinal:032x}",
            submitted_at=1690000000 + ordinal,
            requested_root=None,
            login_probe_status="default-readable",
        )
    target_nonce = "f" * 32
    assert floor_job_checkpoint.try_create_index(
        root=root,
        job_id="target.nqsv",
        nonce=target_nonce,
        submitted_at=1700000000,
        requested_root=None,
        login_probe_status="default-readable",
    )
    resolved = floor_job_checkpoint.resolve_indices_by_time(
        root, earliest=1700000000, latest=1700000000, max_entries=1,
    )
    assert [record["submission_nonce"] for record in resolved] == [target_nonce]


def test_floor_job_records_interpreter_resolution_failure_after_attempt_creation(
    tmp_path: Path,
) -> None:
    source = JOB.read_text(encoding="utf-8")
    attempt_index = source.index('ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"')
    writer_index = source.index("write_failure() {")
    resolution_index = source.index("for py_name in python3 python3.10")
    assert attempt_index < writer_index < resolution_index

    start = source.index("write_interpreter_failure() {")
    end = source.index("on_err() {", start)
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    empty_path = tmp_path / "empty-bin"
    empty_path.mkdir()
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            "set -o noclobber",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            "CURRENT_STAGE=attempt-setup",
            "checkpoint_event() { return 0; }",
            "",
        ]
    )
    result = subprocess.run(
        ["/bin/bash", "-c", prefix + source[start:end]],
        capture_output=True,
        text=True,
        env={"PATH": str(empty_path)},
    )
    assert result.returncode == 2
    assert (attempt / "failure-interpreter.txt").read_text(
        encoding="utf-8"
    ) == (
        "stage=interpreter\n"
        "rc=2\n"
        "message=no python3 >= 3.10 (rejected: none)\n"
    )


def _run_interpreter_selection(
    tmp_path: Path, stubs: dict[str, int]
) -> tuple["subprocess.CompletedProcess[str]", Path, dict[str, Path]]:
    source = JOB.read_text(encoding="utf-8")
    start = source.index("write_interpreter_failure() {")
    end = source.index("on_err() {", start)
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    bin_dir = tmp_path / "stub-bin"
    bin_dir.mkdir()
    real_realpath = shutil.which("realpath")
    assert real_realpath is not None
    (bin_dir / "realpath").symlink_to(real_realpath)
    paths: dict[str, Path] = {}
    for name, gate_rc in stubs.items():
        stub = bin_dir / name
        stub.write_text(f"#!/bin/sh\nexit {gate_rc}\n", encoding="utf-8")
        stub.chmod(0o755)
        paths[name] = stub
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            "set -o noclobber",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            "CURRENT_STAGE=attempt-setup",
            "checkpoint_event() { return 0; }",
            "",
        ]
    )
    suffix = '\nprintf \'%s\\n\' "$PY"\n'
    result = subprocess.run(
        ["/bin/bash", "-c", prefix + source[start:end] + suffix],
        capture_output=True,
        text=True,
        env={"PATH": str(bin_dir)},
    )
    return result, attempt, paths


def test_floor_job_interpreter_gate_rejects_pre_310_python(tmp_path: Path) -> None:
    result, attempt, paths = _run_interpreter_selection(tmp_path, {"python3": 1})
    assert result.returncode == 2
    rejected = os.path.realpath(paths["python3"])
    assert (attempt / "failure-interpreter.txt").read_text(encoding="utf-8") == (
        "stage=interpreter\n"
        "rc=2\n"
        f"message=no python3 >= 3.10 (rejected: python3={rejected})\n"
    )


def test_floor_job_interpreter_gate_falls_back_to_versioned_python(
    tmp_path: Path,
) -> None:
    result, _attempt, paths = _run_interpreter_selection(
        tmp_path, {"python3": 1, "python3.10": 0}
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == os.path.realpath(paths["python3.10"])


def test_floor_job_interpreter_gate_prefers_default_python3(tmp_path: Path) -> None:
    result, _attempt, paths = _run_interpreter_selection(
        tmp_path, {"python3": 0, "python3.10": 0}
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == os.path.realpath(paths["python3"])


def _dependency_build_fragment() -> str:
    source = JOB.read_text(encoding="utf-8")
    start = source.index('if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]')
    end = source.index("protocol_resolution_rc=0", start)
    return source[start:end]


def _read_stub_calls(path: Path) -> list[list[str]]:
    payload = path.read_bytes()
    assert payload.endswith(b"\x1e")
    return [
        [argument.decode("utf-8") for argument in record.split(b"\0") if argument]
        for record in payload[:-1].split(b"\x1e")
    ]


def test_floor_job_builds_and_exports_dependency_prefixes(tmp_path: Path) -> None:
    attempt = tmp_path / "attempt"
    scratch = tmp_path / "scratch"
    repo = tmp_path / "repo"
    staging = repo / "output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
    staging.mkdir(parents=True)
    gflags_source = staging / "gflags"
    glog_source = staging / "glog"
    for path in (attempt, scratch, gflags_source, glog_source):
        path.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    head = "a" * 40
    git_log = tmp_path / "git-calls.bin"
    cmake_log = tmp_path / "cmake-calls.bin"
    timeout_log = tmp_path / "timeout-calls.bin"
    git_stub = bin_dir / "git"
    git_stub.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\0' \"$@\" >> {shlex.quote(str(git_log))}\n"
        f"printf '\\036' >> {shlex.quote(str(git_log))}\n"
        "case \" $* \" in\n"
        f"  *' rev-parse HEAD '*) printf '%s\\n' {head} ;;\n"
        "  *' status --porcelain --untracked-files=all '*) : ;;\n"
        "  *) exit 91 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    git_stub.chmod(0o755)
    cmake_stub = bin_dir / "cmake"
    cmake_stub.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\0' \"$@\" >> {shlex.quote(str(cmake_log))}\n"
        f"printf '\\036' >> {shlex.quote(str(cmake_log))}\n",
        encoding="utf-8",
    )
    cmake_stub.chmod(0o755)
    timeout_stub = bin_dir / "timeout"
    timeout_stub.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\0' \"$@\" >> {shlex.quote(str(timeout_log))}\n"
        f"printf '\\036' >> {shlex.quote(str(timeout_log))}\n"
        "shift\n"
        "\"$@\"\n",
        encoding="utf-8",
    )
    timeout_stub.chmod(0o755)
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"TMPDIR={shlex.quote(str(scratch))}",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            "unset IZANAGI_THIRDPARTY_SOURCE_ROOT",
            *[
                line for line in (TOOL_DIR / "floor_campaign.sh").read_text(
                    encoding="utf-8").splitlines()
                if line.startswith(("THIRDPARTY_SOURCE_ROOT=", "GFLAGS_SOURCE_PATH=",
                                    "GLOG_SOURCE_PATH="))
            ],
            f"GFLAGS_EXPECTED_HEAD={head}",
            f"GLOG_EXPECTED_HEAD={head}",
            f"PY={shlex.quote(sys.executable)}",
            "CC_PATH=/bin/true",
            "CXX_PATH=/bin/true",
            "checkpoint_event() { return 0; }",
            "write_failure() { return 0; }",
            "",
        ]
    )
    env = _git_env(tmp_path / "repo")
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    result = subprocess.run(
        [
            "bash",
            "-c",
            prefix
            + _dependency_build_fragment()
            + '\n[[ "$CMAKE_PREFIX_PATH" == "$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR" ]]\n',
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    prefix_record = json.loads(
        (attempt / "cmake-prefix-path.json").read_text(encoding="utf-8")
    )
    assert prefix_record["effective_value"] == (
        str(scratch / "gflags-install") + ":" + str(scratch / "glog-install")
    )
    compiler = str(Path("/bin/true").resolve())
    gflags_configure = [
        "-S",
        str(gflags_source),
        "-B",
        str(scratch / "gflags-build"),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        "-DREGISTER_INSTALL_PREFIX=OFF",
        "-DCMAKE_INSTALL_PREFIX=" + str(scratch / "gflags-install"),
        "-DCMAKE_C_COMPILER=" + compiler,
        "-DCMAKE_CXX_COMPILER=" + compiler,
    ]
    gflags_build = ["--build", str(scratch / "gflags-build"), "-j", "48"]
    gflags_install = ["--install", str(scratch / "gflags-build")]
    glog_configure = [
        "-S",
        str(glog_source),
        "-B",
        str(scratch / "glog-build"),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        "-DWITH_GTEST=OFF",
        "-DBUILD_TESTING=OFF",
        "-DWITH_UNWIND=OFF",
        "-DCMAKE_PREFIX_PATH=" + str(scratch / "gflags-install"),
        "-DCMAKE_INSTALL_PREFIX=" + str(scratch / "glog-install"),
        "-DCMAKE_C_COMPILER=" + compiler,
        "-DCMAKE_CXX_COMPILER=" + compiler,
    ]
    glog_build = ["--build", str(scratch / "glog-build"), "-j", "48"]
    glog_install = ["--install", str(scratch / "glog-build")]
    cmake_calls = [
        gflags_configure,
        gflags_build,
        gflags_install,
        glog_configure,
        glog_build,
        glog_install,
    ]
    assert _read_stub_calls(cmake_log) == cmake_calls
    assert _read_stub_calls(timeout_log) == [
        [limit, "cmake", *call]
        for limit, call in zip(
            ("60", "60", "60", "120", "120", "120"),
            cmake_calls,
            strict=True,
        )
    ]
    assert _read_stub_calls(git_log) == [
        ["-C", str(gflags_source), "rev-parse", "HEAD"],
        [
            "-C",
            str(gflags_source),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        ["-C", str(glog_source), "rev-parse", "HEAD"],
        [
            "-C",
            str(glog_source),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
    ]


def test_floor_job_exports_exact_reservation_fields() -> None:
    source = JOB.read_text(encoding="utf-8")
    actual = set(
        re.findall(
            r"^export (IZANAGI_RESERVATION_[A-Z0-9_]+)=", source, re.MULTILINE
        )
    )
    assert actual == set(reservation._ENV_FIELDS.values())


def test_floor_job_has_nonce_bound_official_confirmation_dataflow_and_keeps_admission_order() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert "IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT" not in source
    assert "--confirm-irreversible-pilot-holdout" not in source
    assert "if [[ ${IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN+x} == x ]]" in source
    assert (
        '[[ "$IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN" '
        '!= "$IZANAGI_SUBMISSION_NONCE" ]]' in source
    )
    assert "export -n IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN" in source

    unset_targets: list[str] = []
    for line in source.splitlines():
        if not line.lstrip().startswith("unset "):
            continue
        tokens = shlex.split(line, comments=True, posix=True)
        assert tokens[0] == "unset"
        unset_targets.extend(tokens[1:])
    assert len(unset_targets) == 3
    assert set(unset_targets) == {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"}

    ordered_anchors = (
        'git -C "$REPO_ROOT" cat-file blob "$PREFLIGHT_HELPER_SPEC"',
        "OFFICIAL_APPROVAL_BOUND=0",
        "export -n IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN",
        "receipt_rc=0",
        'timeout 60 "${gflags_configure_argv[@]}"',
        '"${driver_argv[@]}" \\',
    )
    assert all(source.count(anchor) == 1 for anchor in ordered_anchors)
    anchor_indexes = tuple(source.index(anchor) for anchor in ordered_anchors)
    assert anchor_indexes == tuple(sorted(anchor_indexes))


def _official_approval_binding_fragment() -> str:
    source = JOB.read_text(encoding="utf-8")
    start = source.index("CURRENT_STAGE=submit-binding")
    end = source.index('SUBMISSION_DIR="$ATTEMPTS_ROOT/submissions/', start)
    return source[start:end]


def _run_official_approval_binding(
    tmp_path: Path, *, approval: str | None,
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    failure_call = tmp_path / "failure-call.txt"
    downstream_marker = tmp_path / "downstream"
    nonce = "d" * 32
    prefix_lines = [
        "set -Eeuo pipefail",
        "CURRENT_STAGE=bootstrap",
        f"IZANAGI_SUBMISSION_NONCE={nonce}",
        "checkpoint_event() { return 0; }",
        "write_failure() {",
        f"  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" > {shlex.quote(str(failure_call))}",
        "}",
    ]
    if approval is not None:
        prefix_lines.append(
            "export IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=" + shlex.quote(approval)
        )
    suffix = "\n".join([
        (
            f"{shlex.quote(sys.executable)} -c \"import os; "
            "assert 'IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN' not in os.environ\""
        ),
        f"printf '%s\\n' \"$OFFICIAL_APPROVAL_BOUND\" > {shlex.quote(str(downstream_marker))}",
        "",
    ])
    result = subprocess.run(
        [
            "bash", "-c",
            "\n".join([*prefix_lines, ""])
            + _official_approval_binding_fragment()
            + suffix,
        ],
        capture_output=True,
        text=True,
    )
    return result, failure_call, downstream_marker


def test_floor_job_official_approval_binding_accepts_exact_nonce(
        tmp_path: Path) -> None:
    result, failure_call, downstream = _run_official_approval_binding(
        tmp_path, approval="d" * 32,
    )
    assert result.returncode == 0, result.stderr
    assert downstream.read_text(encoding="utf-8") == "1\n"
    assert not failure_call.exists()


def test_floor_job_official_approval_binding_leaves_flag_absent_when_env_unset(
        tmp_path: Path) -> None:
    result, failure_call, downstream = _run_official_approval_binding(
        tmp_path, approval=None,
    )
    assert result.returncode == 0, result.stderr
    assert downstream.read_text(encoding="utf-8") == "0\n"
    assert not failure_call.exists()


def test_floor_job_official_approval_binding_rejects_empty_before_downstream(
        tmp_path: Path) -> None:
    result, failure_call, downstream = _run_official_approval_binding(
        tmp_path, approval="",
    )
    assert result.returncode == 2
    assert failure_call.read_text(encoding="utf-8") == (
        "2|submit_binding|"
        "IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN is set but empty\n"
    )
    assert not downstream.exists()


def test_floor_job_official_approval_binding_rejects_mismatch_before_downstream(
        tmp_path: Path) -> None:
    result, failure_call, downstream = _run_official_approval_binding(
        tmp_path, approval="e" * 32,
    )
    assert result.returncode == 2
    assert failure_call.read_text(encoding="utf-8") == (
        "2|submit_binding|"
        "IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN must exactly match "
        "IZANAGI_SUBMISSION_NONCE\n"
    )
    assert not downstream.exists()


def _run_floor_driver_tail(
    tmp_path: Path, *, approval_bound: bool,
) -> tuple[str, list[str]]:
    source = JOB.read_text(encoding="utf-8")
    repo = tmp_path / "repo"
    driver = repo / "orchestrator" / "campaign" / "s8b_floor_campaign.py"
    driver.parent.mkdir(parents=True)
    argv_record = tmp_path / "driver-argv.json"
    driver.write_text(
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "if sys.argv[1:] != ['resolve-current-protocol']:\n"
        f"    Path({str(argv_record)!r}).write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n"
        + _floor_driver_stub_source(),
        encoding="utf-8",
    )
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    prefix_lines = [
        "set -Eeuo pipefail",
        f"REPO_ROOT={shlex.quote(str(repo))}",
        f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
        f"PY={shlex.quote(sys.executable)}",
        f"OFFICIAL_APPROVAL_BOUND={int(approval_bound)}",
        "PBS_JOBID=0:fixture.nqsv",
        f"CURRENT_COMMIT={'a' * 40}",
        f"JOB_SCRIPT_SHA256={'b' * 64}",
        f"EXECUTING_SCRIPT_SHA256={'c' * 64}",
        f"IZANAGI_SUBMISSION_NONCE={'d' * 32}",
        "REQUESTED_S=36000",
        "export STUB_DRIVER_RC=0",
        "checkpoint_event() { return 0; }",
        "write_failure() { return 0; }",
    ]
    prefix = "\n".join([*prefix_lines, ""])
    result = subprocess.run(
        [
            "bash",
            "-c",
            prefix + _driver_tail(),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    actual_argv = json.loads(argv_record.read_text(encoding="utf-8"))
    return source, actual_argv


def test_floor_job_unset_approval_omits_flag_from_actual_argv(tmp_path: Path) -> None:
    _source, actual_argv = _run_floor_driver_tail(
        tmp_path, approval_bound=False,
    )
    assert actual_argv == [
        "--mode",
        "official",
        "--protocol",
        str(tmp_path / "repo/output/s8b-freeze/floor_protocol.json"),
    ]


def test_floor_job_exact_approval_appends_flag_once_in_actual_argv(
        tmp_path: Path) -> None:
    source, actual_argv = _run_floor_driver_tail(
        tmp_path, approval_bound=True,
    )
    assert actual_argv.count("--confirm-official-floor-run") == 1
    assert actual_argv[-1] == "--confirm-official-floor-run"
    assert shlex.split(
        source, comments=True, posix=True,
    ).count("--confirm-official-floor-run") == 1


def test_floor_job_driver_mode_is_fixed_official_in_tokens_and_actual_argv(
        tmp_path: Path) -> None:
    source, actual_argv = _run_floor_driver_tail(
        tmp_path, approval_bound=False,
    )
    assert actual_argv[:2] == ["--mode", "official"]

    source_tokens = shlex.split(source, comments=True, posix=True)
    driver_path = "orchestrator/campaign/s8b_floor_campaign.py"
    driver_tokens = [
        token
        for token in source_tokens
        if token == driver_path or token.endswith("/" + driver_path)
    ]
    assert len(driver_tokens) == 2
    assert source_tokens.count("resolve-current-protocol") == 1
    assert source_tokens.count("--mode") == 1
    source_mode_index = source_tokens.index("--mode")
    assert source_tokens[source_mode_index + 1] == "official"
    assert 'export IZANAGI_FLOOR_JOB_STAGING="$ATTEMPT_DIR"' in source
    resolver_index = source.index("resolve-current-protocol")
    driver_argv_index = source.index("driver_argv=(")
    driver_launch_index = source.index(
        '"$REPO_ROOT/orchestrator/campaign/s8b_floor_campaign.py"',
        driver_argv_index,
    )
    assert resolver_index < source.index(
        'export IZANAGI_FLOOR_JOB_STAGING="$ATTEMPT_DIR"'
    )
    assert source.index('export IZANAGI_FLOOR_JOB_STAGING="$ATTEMPT_DIR"') < (
        driver_launch_index
    )
    assert "IZANAGI_FLOOR_MODE" not in source
    assert "--resume" not in source
    assert "eval " not in source


def test_floor_job_does_not_swallow_driver_rc() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert "|| true" not in source
    assert "|| driver_rc=$?" in source
    assert 'exit "$driver_rc"' in source
    assert not re.search(
        r'if \[\[ "\$driver_rc" -eq (?:2|7) \]\]; then\s+exit 0', source
    )


def test_submit_floor_qsub_exports_nonce_and_stages_third_party_payload() -> None:
    source = SUBMIT.read_text(encoding="utf-8")
    match = re.search(r'^export_spec="([^"]+)"$', source, re.MULTILINE)
    assert match is not None
    assert match.group(1) == "IZANAGI_SUBMISSION_NONCE=$NONCE"
    assert (
        'export_spec+=",IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=$NONCE"'
        in source
    )
    assert (
        'qsub -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR"\n'
        '  -v "$export_spec" "$JOB_SCRIPT"'
    ) in source
    assert "IZANAGI_RESERVATION_" not in match.group(1)
    assert "FLOOR_THIRD_PARTY_PERSISTENT_ROOT" in source
    assert "masstree-payload" in source
    stage_call = re.search(
        r"^\s*stage_floor_third_party_payload\s*\|\|", source, re.MULTILINE,
    )
    assert stage_call is not None
    assert stage_call.start() < source.index(
        "qsub_cmd=("
    )


def test_submit_floor_uses_silo_third_party_source_contract() -> None:
    source = SUBMIT.read_text(encoding="utf-8")
    assert "silo_ladder_rung1/job-staging/thirdparty-src" in source
    assert "verify_third_party_pinned_clean" in source
    assert "cp -a -- \"$source\" \"$destination\"" in source


def test_floor_scripts_use_create_only_leaves_and_json() -> None:
    submit = SUBMIT.read_text(encoding="utf-8")
    job = JOB.read_text(encoding="utf-8")
    assert 'mkdir "$SUBMISSION_DIR"' in submit
    assert 'mkdir -p "$SUBMISSION_DIR"' not in submit
    assert 'mkdir "$ATTEMPT_DIR"' in job
    assert 'mkdir -p "$ATTEMPT_DIR"' not in job
    assert "set -o noclobber" in submit
    assert "set -o noclobber" in job
    assert submit.count('"x", encoding="utf-8"') >= 2
    assert job.count('"x", encoding="utf-8"') >= 4
    assert '"xb"' in job


def test_submit_floor_dry_run_is_scheduler_free_and_writes_exact_receipts(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    attempts = repo / "output" / "dry-attempts"
    job = repo / "tools" / "pegasus" / "floor_campaign.sh"
    result = _submit(
        repo,
        bin_dir,
        "--dry-run",
        "--repo-root",
        str(repo),
        "--attempts-root",
        str(attempts),
        "--job-script",
        str(job),
    )
    assert result.returncode == 0, result.stderr
    assert not sentinel.exists()
    submission = _only_submission(repo, "output/dry-attempts")
    pre = json.loads((submission / "pre-submit.json").read_text(encoding="utf-8"))
    receipt = json.loads(
        (submission / "submit-receipt.json").read_text(encoding="utf-8")
    )
    assert set(pre) == PRE_KEYS
    assert set(receipt) == RECEIPT_KEYS
    assert pre["schema_version"] == "pegasus-floor-pre-submit/v1"
    assert receipt["schema_version"] == "pegasus-floor-submit-receipt/v1"
    assert type(pre["schema_version"]) is str
    assert type(receipt["schema_version"]) is str
    assert pre["dry_run"] is True and receipt["dry_run"] is True
    assert type(pre["prepared_at"]) is int and pre["prepared_at"] > 0
    assert type(receipt["submitted_at"]) is int and receipt["submitted_at"] > 0
    assert type(pre["nonce"]) is str and type(receipt["nonce"]) is str
    assert re.fullmatch(r"[0-9a-f]{32}", pre["nonce"])
    assert receipt["nonce"] == pre["nonce"]
    assert type(receipt["job_id"]) is str
    assert receipt["job_id"] == "dry-run-" + pre["nonce"]
    assert type(pre["source_commit"]) is str
    assert type(receipt["source_commit"]) is str
    assert re.fullmatch(r"[0-9a-f]{40}", pre["source_commit"])
    assert receipt["source_commit"] == pre["source_commit"]
    assert type(pre["job_script_path"]) is str
    assert type(receipt["job_script_path"]) is str
    assert pre["job_script_path"] == "tools/pegasus/floor_campaign.sh"
    assert type(pre["job_script_sha256"]) is str
    assert type(receipt["job_script_sha256"]) is str
    committed_job = _git_bytes(
        repo,
        "cat-file",
        "blob",
        pre["source_commit"] + ":tools/pegasus/floor_campaign.sh",
    )
    assert pre["job_script_sha256"] == hashlib.sha256(committed_job).hexdigest()
    assert receipt["job_script_path"] == pre["job_script_path"]
    assert receipt["job_script_sha256"] == pre["job_script_sha256"]
    assert type(pre["request"]) is dict and set(pre["request"]) == REQUEST_KEYS
    assert type(pre["request"]["project"]) is str
    assert type(pre["request"]["queue"]) is str
    assert type(pre["request"]["nodes"]) is int
    assert type(pre["request"]["elapstim_req_s"]) is int
    assert pre["request"] == {
        "project": "SFC",
        "queue": "gen_S",
        "nodes": 1,
        "elapstim_req_s": 36000,
    }
    assert receipt["request"] == pre["request"]
    _assert_capture_schema(pre["preflight"], dry_run=True)
    assert receipt["preflight"] == pre["preflight"]
    assert (submission / "qsub.stdout").read_text(encoding="utf-8") == (
        "dry-run: qsub was not executed\n"
    )
    claims = repo / "output" / "claims"
    assert claims.is_dir() and not claims.is_symlink()
    assert stat.S_IMODE(claims.stat().st_mode) == 0o700
    assert "authorization" not in result.stdout.lower()


def test_submit_floor_dry_run_stages_payload_when_pinned_sources_are_available(
        tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    _install_floor_third_party_sources(repo)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    result = _submit(repo, bin_dir, "--dry-run")
    assert result.returncode == 0, result.stderr
    assert not sentinel.exists()
    submission = _only_submission(repo, "output/env/pegasus/floor/attempts")
    payload_root = submission / "masstree-payload"
    assert {
        path.name for path in payload_root.iterdir()
    } == {"masstree-src", "mimalloc-src", "googletest-src"}


def test_submit_floor_failed_payload_staging_cleans_temp_and_skips_qsub(
        tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    source_root = _install_floor_third_party_sources(repo)
    policy = json.loads(
        (repo / "tools/pegasus/policy.json").read_text(encoding="utf-8")
    )
    masstree = next(
        item for item in policy["silo_ladder_rung1"]["third_party_sources"]
        if item["name"] == "masstree"
    )
    drifted = source_root / masstree["source_name"]
    (drifted / "head-drift.txt").write_text("drift\n", encoding="utf-8")
    _git(drifted, "add", "head-drift.txt")
    _git(drifted, "commit", "-qm", "head drift")

    bin_dir, sentinel = _sentinel_bin(
        tmp_path,
        failures={
            "qstat": 0,
            "pegasusinfo": 0,
            "rbudgetcheck": 0,
            "check_quota": 0,
            "qsub": 99,
        },
    )
    result = _submit(repo, bin_dir, "--confirm-official-floor-run")
    assert result.returncode == 2
    submission = _only_submission(repo, "output/env/pegasus/floor/attempts")
    assert not (submission / "masstree-payload").exists()
    assert not (submission / "masstree-payload.tmp").exists()
    assert sentinel.read_text(encoding="utf-8").splitlines() == [
        "qstat", "pegasusinfo", "rbudgetcheck", "check_quota",
    ]


def test_submit_floor_rejects_hidden_worktree_job_script_drift(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    relative = "tools/pegasus/floor_campaign.sh"
    job = repo / relative
    _git(repo, "update-index", "--assume-unchanged", relative)
    job.write_text(
        job.read_text(encoding="utf-8") + "\n# hidden working-tree mutation\n",
        encoding="utf-8",
    )
    assert _git(repo, "status", "--porcelain").stdout == ""
    result = _submit(repo, bin_dir, "--dry-run")
    assert result.returncode == 2
    assert not (repo / "output" / "env").exists()
    assert not (repo / "output" / "claims").exists()
    assert not sentinel.exists()


def _successful_submission(
    tmp_path: Path,
    *arguments: str,
    extra_env: dict[str, str] | None = None,
) -> tuple[Path, Path, Path, Path]:
    repo = _fixture_repo(tmp_path)
    _install_floor_third_party_sources(repo)
    bin_dir, qsub_args, qsub_cwd = _successful_bin(tmp_path)
    result = _submit(
        repo, bin_dir, "--confirm-official-floor-run", *arguments,
        extra_env=extra_env,
    )
    assert result.returncode == 0, result.stderr
    submission = _only_submission(
        repo, "output/env/pegasus/floor/attempts"
    )
    return repo, submission, qsub_args, qsub_cwd


def test_submit_floor_non_dry_run_success_writes_real_submission_record(
    tmp_path: Path,
) -> None:
    repo, submission, qsub_args_path, qsub_cwd_path = _successful_submission(
        tmp_path
    )
    receipt = json.loads(
        (submission / "submit-receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["dry_run"] is False
    assert receipt["job_id"] == "98765.nqsv"
    assert artifacts.load_json_strict(submission / "submit-receipt.json") == receipt
    qsub_args = [
        item.decode("utf-8")
        for item in qsub_args_path.read_bytes().split(b"\0")
        if item
    ]
    assert qsub_args == [
        "-o",
        str(submission / "scheduler.stdout"),
        "-e",
        str(submission / "scheduler.stderr"),
        "-v",
        (
            "IZANAGI_SUBMISSION_NONCE=" + receipt["nonce"]
            + ",IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=" + receipt["nonce"]
        ),
        str(repo / "tools" / "pegasus" / "floor_campaign.sh"),
    ]
    for option in ("-o", "-e"):
        scheduler_path = Path(qsub_args[qsub_args.index(option) + 1])
        assert scheduler_path.parent == submission
        assert scheduler_path.is_relative_to(repo / "output")
        assert scheduler_path.suffix in {".stdout", ".stderr"}
    assert qsub_cwd_path.read_text(encoding="utf-8").strip() == str(repo)
    claims = repo / "output" / "claims"
    assert claims.is_dir() and not claims.is_symlink()
    assert stat.S_IMODE(claims.stat().st_mode) == 0o700


def test_submit_floor_copies_and_reverifies_all_floor_third_party_sources(
    tmp_path: Path,
) -> None:
    repo, submission, _qsub_args_path, _qsub_cwd_path = _successful_submission(
        tmp_path,
    )
    payload_root = submission / "masstree-payload"
    assert payload_root.is_dir() and not payload_root.is_symlink()
    for name in ("masstree", "mimalloc", "googletest"):
        source = payload_root / f"{name}-src"
        assert source.is_dir() and not source.is_symlink()
        head = _git(source, "rev-parse", "--verify", "HEAD").stdout.strip()
        status = _git(
            source, "status", "--porcelain", "--untracked-files=all",
        ).stdout
        assert re.fullmatch(r"[0-9a-f]{40}", head)
        assert status == ""


def test_floor_job_leaves_fetchcontent_staging_to_driver_default() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert "stage_floor_fetchcontent_payload" not in source
    assert "FETCHCONTENT_STAGING" not in source
    assert "fetchcontent-staging" not in source
    assert "--fetchcontent-base-dir" not in source


def test_submit_floor_probes_and_indexes_explicit_external_evidence_root(
    tmp_path: Path,
) -> None:
    evidence_root = tmp_path / "shared-evidence"
    repo, submission, qsub_args_path, _qsub_cwd = _successful_submission(
        tmp_path,
        extra_env={
            floor_job_checkpoint.EVIDENCE_ROOT_ENV: str(evidence_root),
        },
    )
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    catalog_root = repo.parent / "izanagi-job-evidence"
    index = floor_job_checkpoint.load_bound_index(
        catalog_root,
        job_id=receipt["job_id"],
        nonce=receipt["nonce"],
        submitted_at=receipt["submitted_at"],
    )
    assert index["login_probe_status"] == "override-readable"
    assert index["requested_evidence_root"] == str(evidence_root)
    assert index["catalog_root"] == str(catalog_root)
    assert index["evidence_root"] == str(evidence_root)
    qsub_args = [
        item.decode("utf-8")
        for item in qsub_args_path.read_bytes().split(b"\0")
        if item
    ]
    export_spec = qsub_args[qsub_args.index("-v") + 1]
    assert export_spec == (
        f"IZANAGI_SUBMISSION_NONCE={receipt['nonce']},"
        f"IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN={receipt['nonce']},"
        f"IZANAGI_FLOOR_JOB_EVIDENCE_ROOT={evidence_root}"
    )
    assert not list(repo.rglob("checkpoint.jsonl"))


def test_submit_floor_unreadable_override_falls_back_and_records_probe(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    _install_floor_third_party_sources(repo)
    bin_dir, qsub_args_path, _qsub_cwd = _successful_bin(tmp_path)
    unsafe = repo / "output" / "inside-repository"
    result = _submit(
        repo, bin_dir, "--confirm-official-floor-run",
        extra_env={floor_job_checkpoint.EVIDENCE_ROOT_ENV: str(unsafe)},
    )
    assert result.returncode == 0, result.stderr
    assert "using default" in result.stderr
    submission = _only_submission(
        repo, "output/env/pegasus/floor/attempts",
    )
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    default_root = repo.parent / "izanagi-job-evidence"
    index = floor_job_checkpoint.load_bound_index(
        default_root,
        job_id=receipt["job_id"],
        nonce=receipt["nonce"],
        submitted_at=receipt["submitted_at"],
    )
    assert index["login_probe_status"] == "override-unreadable-fallback"
    assert index["requested_evidence_root"] == str(unsafe)
    qsub_args = [
        item.decode("utf-8")
        for item in qsub_args_path.read_bytes().split(b"\0")
        if item
    ]
    assert floor_job_checkpoint.EVIDENCE_ROOT_ENV not in (
        qsub_args[qsub_args.index("-v") + 1]
    )


def test_submit_floor_unreadable_default_persists_sidecar_for_consumer(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    _install_floor_third_party_sources(repo)
    bin_dir, _qsub_args_path, _qsub_cwd = _successful_bin(tmp_path)
    default_root = repo.parent / "izanagi-job-evidence"
    default_root.symlink_to(repo / "output", target_is_directory=True)
    result = _submit(repo, bin_dir, "--confirm-official-floor-run")
    assert result.returncode == 0, result.stderr
    assert "default floor evidence root is not login-readable" in result.stderr
    assert "external floor evidence index create-only write failed" in result.stderr
    submission = _only_submission(repo, "output/env/pegasus/floor/attempts")
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    status_path = submission / "evidence-index-status.json"
    status = floor_job_checkpoint.load_index_status(
        status_path,
        job_id=receipt["job_id"],
        nonce=receipt["nonce"],
        submitted_at=receipt["submitted_at"],
    )
    assert status["login_probe_status"] == "default-unreadable"
    assert status["index_write_status"] == "failed"

    classified = floor_liveness.classify(
        receipt["job_id"], receipt["nonce"], timeout_s=5,
        repo_root=repo,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )
    external = next(
        item for item in classified["evidence"]
        if item["kind"] == "external-job-index-status"
    )
    assert external["index_status_path"] == str(status_path)
    assert external["index_probe_status"] == "default-unreadable"
    assert external["index_write_status"] == "failed"


def test_submit_floor_without_option_ignores_ambient_confirmation_env_in_dry_run(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    result = _submit(
        repo, bin_dir, "--dry-run",
        extra_env={
            "IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT": "1",
            "IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN": "ambient",
        },
    )
    assert result.returncode == 0, result.stderr
    assert not sentinel.exists()
    submission = _only_submission(repo, "output/env/pegasus/floor/attempts")
    receipt = json.loads(
        (submission / "submit-receipt.json").read_text(encoding="utf-8")
    )
    assert "IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT" not in result.stdout
    assert "IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN" not in result.stdout
    assert f"IZANAGI_SUBMISSION_NONCE={receipt['nonce']}" in result.stdout
    submit_source = SUBMIT.read_text(encoding="utf-8")
    export_start = submit_source.index(
        'export_spec="IZANAGI_SUBMISSION_NONCE=$NONCE"'
    )
    export_end = submit_source.index('SCHEDULER_STDOUT=', export_start)
    assert "IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT" not in submit_source[
        export_start:export_end
    ]
    assert set(receipt) == RECEIPT_KEYS


def test_submit_floor_real_run_requires_approval_before_staging_and_qsub(
        tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    result = _submit(repo, bin_dir)
    assert result.returncode == 2
    assert result.stderr == (
        "real official floor submission requires "
        "--confirm-official-floor-run\n"
    )
    assert not (repo / "output/env").exists()
    assert not (repo / "output/claims").exists()
    assert not sentinel.exists()

    source = SUBMIT.read_text(encoding="utf-8")
    guard = source.index(
        'if [[ "$DRY_RUN" -eq 0 && "$CONFIRM_OFFICIAL_FLOOR_RUN" -ne 1 ]]'
    )
    assert guard < source.index('SUBMISSIONS_ROOT="$ATTEMPTS_ROOT/submissions"')
    assert guard < source.index('mkdir "$SUBMISSION_DIR"')
    assert guard < source.index("stage_floor_third_party_payload ||")
    assert guard < source.index("provision_claim_root || exit 2")
    assert guard < source.index("qsub_cmd=(")


def test_submit_floor_rejects_removed_confirmation_option_without_artifacts(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    result = _submit(
        repo, bin_dir, "--confirm-irreversible-pilot-holdout",
    )
    assert result.returncode == 2
    assert (
        "unknown argument: --confirm-irreversible-pilot-holdout"
        in result.stderr
    )
    assert not sentinel.exists()
    assert not (repo / "output/env").exists()


def test_floor_submit_receipt_pretty_json_is_rejected_by_strict_loader(
    tmp_path: Path,
) -> None:
    _repo, submission, _qsub_args, _qsub_cwd = _successful_submission(tmp_path)
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    pretty = tmp_path / "pretty-submit-receipt.json"
    pretty.write_text(
        json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        artifacts.QualificationArtifactError,
        match="not canonical",
    ):
        artifacts.load_json_strict(pretty)


def _qstat_result(
    request_id: str,
    *,
    state: str | None = None,
    present: bool = True,
    rc: int = 0,
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    stdout = (
        f"Request ID: {request_id}\nRequest State = {state}\n"
        if present
        else f"Batch Request: {request_id} does not exist on nqsv.\n"
    )
    return subprocess.CompletedProcess(
        ["qstat", "-f", request_id], rc, stdout, stderr,
    )


def test_floor_liveness_classifies_queue_wait_without_success_claim(
    tmp_path: Path,
) -> None:
    repo, submission, _qsub_args, _qsub_cwd = _successful_submission(tmp_path)
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")

    result = floor_liveness.classify(
        receipt["job_id"],
        receipt["nonce"],
        timeout_s=5,
        repo_root=repo,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], state="QUE",
        ),
    )

    assert result["classification"] == "queue-waiting"
    assert result["scheduler_state"] == "QUE"
    assert result["request_disappeared_is_success"] is False


def test_floor_liveness_cli_resolves_evidence_by_job_id_and_time(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    repo, submission, _qsub_args, _qsub_cwd = _successful_submission(tmp_path)
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    catalog_root = repo.parent / "izanagi-job-evidence"

    assert floor_liveness.main([
        "--resolve-job-id", "0:" + receipt["job_id"],
        "--evidence-root", str(catalog_root),
    ]) == 0
    by_job = json.loads(capsys.readouterr().out)
    assert by_job["query"] == {
        "kind": "job-id", "job_id": "0:" + receipt["job_id"],
    }
    assert [item["submission_nonce"] for item in by_job["matches"]] == [
        receipt["nonce"],
    ]
    assert Path(by_job["matches"][0]["checkpoint_path"]).is_absolute()

    assert floor_liveness.main([
        "--resolve-time", str(receipt["submitted_at"]),
        str(receipt["submitted_at"]),
        "--max-index-results", "1",
        "--evidence-root", str(catalog_root),
    ]) == 0
    by_time = json.loads(capsys.readouterr().out)
    assert by_time["query"] == {
        "kind": "submitted-at",
        "earliest": receipt["submitted_at"],
        "latest": receipt["submitted_at"],
    }
    assert [item["submission_nonce"] for item in by_time["matches"]] == [
        receipt["nonce"],
    ]


def test_floor_liveness_requires_bound_compute_marker_for_running(
    tmp_path: Path,
) -> None:
    repo, submission, _qsub_args, _qsub_cwd = _successful_submission(tmp_path)
    receipt_path = submission / "submit-receipt.json"
    receipt = artifacts.load_json_strict(receipt_path)
    staging = (
        repo / "output/env/pegasus/floor/job-staging"
        / ("0:" + receipt["job_id"])
    )
    staging.mkdir(parents=True)
    (staging / "submit-receipt.json").write_bytes(receipt_path.read_bytes())
    (staging / "hostname.stdout").write_text("bnode314\n", encoding="utf-8")

    result = floor_liveness.classify(
        receipt["job_id"],
        receipt["nonce"],
        timeout_s=5,
        repo_root=repo,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], state="RUN",
        ),
    )

    assert result["classification"] == "running"
    assert result["compute_marker"] == {
        "path": str(staging / "hostname.stdout"),
        "present": True,
        "valid": True,
        "hostname": "bnode314",
        "receipt_bound": True,
    }


def test_floor_liveness_disappearance_is_terminal_not_success_and_reads_stderr(
    tmp_path: Path,
) -> None:
    repo, submission, _qsub_args, _qsub_cwd = _successful_submission(tmp_path)
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    (submission / "scheduler.stderr").write_text(
        '{"gate":"admission","reason":"floor receipt strict read failed"}\n',
        encoding="utf-8",
    )

    result = floor_liveness.classify(
        receipt["job_id"],
        receipt["nonce"],
        timeout_s=5,
        repo_root=repo,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )

    assert result["classification"] == "finished"
    assert result["request_disappeared"] is True
    assert result["job_success"] is None
    assert result["request_disappeared_is_success"] is False
    evidence_root = tmp_path / "izanagi-job-evidence"
    assert result["evidence"] == [
        {
            "path": str(submission / "scheduler.stderr"),
            "kind": "structured-stderr",
            "fields": {
                "gate": "admission",
                "reason": "floor receipt strict read failed",
            },
            "accounting_present": False,
        },
        {
            "kind": "external-job-index",
            "index_path": str(
                evidence_root / "index" / "by-job" / "98765.nqsv"
                / f"{receipt['nonce']}.json"
            ),
            "checkpoint_path": str(
                evidence_root / "pegasus" / "98765.nqsv"
                / receipt["nonce"] / "checkpoint.jsonl"
            ),
            "index_probe_status": "default-readable",
            "index_write_status": "published",
            "last_observed_stage": None,
            "cause": "unknown",
            "rerun_eligible": None,
        },
    ]


def test_floor_liveness_nonzero_unknown_job_is_also_finished(
    tmp_path: Path,
) -> None:
    repo, submission, _qsub_args, _qsub_cwd = _successful_submission(tmp_path)
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")

    result = floor_liveness.classify(
        receipt["job_id"],
        receipt["nonce"],
        timeout_s=5,
        repo_root=repo,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False, rc=153,
            stderr="Unknown Job Id",
        ),
    )

    assert result["classification"] == "finished"
    assert result["request_disappeared"] is True
    assert result["job_success"] is None


def test_floor_liveness_terminal_reads_job_staging_failure_json(
    tmp_path: Path,
) -> None:
    repo, submission, _qsub_args, _qsub_cwd = _successful_submission(tmp_path)
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    staging = (
        repo / "output/env/pegasus/floor/job-staging"
        / ("0:" + receipt["job_id"])
    )
    staging.mkdir(parents=True)
    (staging / "failure.json").write_text(
        json.dumps({
            "schema_version": "pegasus-job-failure/v1",
            "pbs_jobid": "0:" + receipt["job_id"],
            "rc": 2,
            "stage": "floor_driver",
            "message": "official floor driver returned nonzero",
            "recorded_epoch": 1,
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    result = floor_liveness.classify(
        receipt["job_id"],
        receipt["nonce"],
        timeout_s=5,
        repo_root=repo,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )

    assert result["classification"] == "finished"
    assert result["evidence"][0] == {
        "path": str(staging / "failure.json"),
        "kind": "failure-json",
        "fields": {
            "stage": "floor_driver",
            "message": "official floor driver returned nonzero",
            "rc": 2,
        },
    }


def _external_liveness_fixture(
    tmp_path: Path,
    *,
    journal_nonce: str | None = None,
    incomplete_checkpoint: bool = False,
    incomplete_journal: bool = False,
) -> tuple[Path, dict[str, object], Path, Path]:
    evidence_root = tmp_path / "external-evidence"
    repo, submission, _qsub_args, _qsub_cwd = _successful_submission(
        tmp_path,
        extra_env={
            floor_job_checkpoint.EVIDENCE_ROOT_ENV: str(evidence_root),
        },
    )
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    job_id = receipt["job_id"]
    nonce = receipt["nonce"]
    run_dir = tmp_path / "external-run"
    run_dir.mkdir()
    journal = run_dir / "journal.jsonl"
    binding_nonce = nonce if journal_nonce is None else journal_nonce
    journal.write_text(
        json.dumps({
            "event": "reservation-preflight",
            "required_s": 28800,
            "safety_margin_s": 600,
            "formula": "fixed floor reservation formula",
            "build_cap_per_cell_s": 900,
            "shared_dependency_prebuild": True,
            "dependency_configure_cap_s": 900,
            "dependency_target_cap_s": 900,
            "verify_cap_per_attempt_s": 120,
            "finalize_reserve_s": 600,
            "pbs_jobid": "0:" + job_id,
            "submission_nonce": binding_nonce,
        }, sort_keys=True)
        + "\n"
        + json.dumps({
            "event": "session-start",
            "seq": 0,
            "kind": "planned",
            "cell_id": "rr79/candidate",
            "round": 1,
            "retry_ordinal": None,
            "attempt_id": "rr79/candidate::seq0",
            "trigger": None,
            "started_iso": "2026-08-18T00:00:00+00:00",
        }, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    assert _append_fixture_checkpoint(
        evidence_root, job_id=job_id, nonce=nonce,
    )
    assert _append_fixture_checkpoint(
        evidence_root,
        job_id=job_id,
        nonce=nonce,
        stage="floor-driver",
        transition="run-linked",
        run_dir=str(run_dir),
        journal_path=str(journal),
    )
    checkpoint = floor_job_checkpoint.checkpoint_path(
        evidence_root, job_id, nonce,
    )
    if incomplete_checkpoint:
        with checkpoint.open("ab") as handle:
            handle.write(b'{"schema_version":')
    if incomplete_journal:
        with journal.open("ab") as handle:
            handle.write(b'{"event":')
    catalog_root = repo.parent / "izanagi-job-evidence"
    return repo, receipt, catalog_root, journal


def test_floor_liveness_consumes_external_checkpoint_and_incomplete_prefix(
    tmp_path: Path,
) -> None:
    repo, receipt, evidence_root, journal = _external_liveness_fixture(
        tmp_path, incomplete_checkpoint=True, incomplete_journal=True,
    )

    result = floor_liveness.classify(
        receipt["job_id"],
        receipt["nonce"],
        timeout_s=5,
        repo_root=repo,
        evidence_root=evidence_root,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )

    external = next(
        item for item in result["evidence"]
        if item["kind"] == "external-job-checkpoint"
    )
    assert external["incomplete_tail"] is True
    assert external["last_observed_stage"] == "floor-driver"
    assert external["last_transition"] == "run-linked"
    assert external["cause"] == "unknown"
    assert external["rerun_eligible"] is None
    assert external["run_link"] == {
        "present": True,
        "valid": True,
        "run_dir": str(journal.parent),
        "journal_path": str(journal),
        "journal_incomplete_tail": True,
        "last_session_cell_id": "rr79/candidate",
    }
    with pytest.raises(
        s8b_floor_campaign.FloorCampaignError, match="truncated crash",
    ):
        s8b_floor_campaign._read_journal(journal)


def test_floor_liveness_rejects_run_link_with_mismatched_nonce(
    tmp_path: Path,
) -> None:
    repo, receipt, evidence_root, _journal = _external_liveness_fixture(
        tmp_path, journal_nonce="b" * 32,
    )
    result = floor_liveness.classify(
        receipt["job_id"],
        receipt["nonce"],
        timeout_s=5,
        repo_root=repo,
        evidence_root=evidence_root,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )
    external = next(
        item for item in result["evidence"]
        if item["kind"].startswith("external-job-checkpoint")
    )
    assert external["kind"] == "external-job-checkpoint-unusable"
    assert "bindings disagree" in external["reason"]


def test_floor_liveness_rejects_binding_fields_on_an_arbitrary_event(
    tmp_path: Path,
) -> None:
    repo, receipt, catalog_root, journal = _external_liveness_fixture(tmp_path)
    journal.write_text(
        json.dumps({
            "event": "session",
            "pbs_jobid": receipt["job_id"],
            "submission_nonce": receipt["nonce"],
        }) + "\n",
        encoding="utf-8",
    )
    result = floor_liveness.classify(
        receipt["job_id"], receipt["nonce"], timeout_s=5,
        repo_root=repo, evidence_root=catalog_root,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )
    external = next(
        item for item in result["evidence"]
        if item["kind"].startswith("external-job-checkpoint")
    )
    assert external["kind"] == "external-job-checkpoint-unusable"
    assert "non-binding event" in external["reason"]


def test_floor_liveness_campaign_start_binding_requires_exact_shape_and_agreement() -> None:
    job_id = "98765.nqsv"
    nonce = "a" * 32
    campaign_start = {
        "event": "campaign-start",
        "schema": "s8b-floor-journal/v3",
        "protocol_sha256": "1" * 64,
        "freeze_sha256": "2" * 64,
        "manifest_sha256": "3" * 64,
        "hostname": "bnode1",
        "boot_id": None,
        "job_id": "0:" + job_id,
        "cpuset": "0-47",
        "utc": "2026-08-18T00:00:00+00:00",
        "pid": 123,
        "starttime": 456,
        "execution_uuid": "4" * 32,
        "pbs_jobid": job_id,
        "submission_nonce": nonce,
    }
    assert floor_liveness._validate_journal_binding(
        [campaign_start], job_id="0:" + job_id, nonce=nonce,
    ) == (None, False)
    with pytest.raises(
        floor_job_checkpoint.CheckpointError, match="campaign-start binding shape",
    ):
        floor_liveness._validate_journal_binding(
            [{**campaign_start, "unexpected": True}],
            job_id=job_id,
            nonce=nonce,
        )
    reservation = {
        "event": "reservation-preflight",
        "required_s": 28800,
        "safety_margin_s": 600,
        "formula": "fixed floor reservation formula",
        "build_cap_per_cell_s": 900,
        "shared_dependency_prebuild": True,
        "dependency_configure_cap_s": 900,
        "dependency_target_cap_s": 900,
        "verify_cap_per_attempt_s": 120,
        "finalize_reserve_s": 600,
        "pbs_jobid": job_id,
        "submission_nonce": "b" * 32,
    }
    with pytest.raises(
        floor_job_checkpoint.CheckpointError, match="bindings disagree",
    ):
        floor_liveness._validate_journal_binding(
            [campaign_start, reservation], job_id=job_id, nonce=nonce,
        )


def test_floor_liveness_rejects_duplicate_binding_and_noncanonical_session(
    tmp_path: Path,
) -> None:
    repo, receipt, catalog_root, journal = _external_liveness_fixture(tmp_path)
    records = [json.loads(line) for line in journal.read_text().splitlines()]
    journal.write_text(
        "\n".join(json.dumps(record) for record in [records[0], records[0]])
        + "\n",
        encoding="utf-8",
    )
    duplicated = floor_liveness.classify(
        receipt["job_id"], receipt["nonce"], timeout_s=5,
        repo_root=repo, evidence_root=catalog_root,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )
    duplicate_evidence = next(
        item for item in duplicated["evidence"]
        if item["kind"].startswith("external-job-checkpoint")
    )
    assert "not unique" in duplicate_evidence["reason"]

    malformed_session = dict(records[1])
    malformed_session.pop("started_iso")
    journal.write_text(
        "\n".join(json.dumps(record) for record in [records[0], malformed_session])
        + "\n",
        encoding="utf-8",
    )
    malformed = floor_liveness.classify(
        receipt["job_id"], receipt["nonce"], timeout_s=5,
        repo_root=repo, evidence_root=catalog_root,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )
    malformed_evidence = next(
        item for item in malformed["evidence"]
        if item["kind"].startswith("external-job-checkpoint")
    )
    assert "session-start exact shape" in malformed_evidence["reason"]


def test_floor_liveness_external_index_uses_receipt_job_id_after_normalized_match(
    tmp_path: Path,
) -> None:
    repo, receipt, catalog_root, _journal = _external_liveness_fixture(tmp_path)
    result = floor_liveness.classify(
        "0:" + receipt["job_id"], receipt["nonce"], timeout_s=5,
        repo_root=repo, evidence_root=catalog_root,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )
    external = next(
        item for item in result["evidence"]
        if item["kind"] == "external-job-checkpoint"
    )
    assert external["run_link"]["valid"] is True


def test_floor_liveness_reports_signal_observation_without_scheduler_cause(
    tmp_path: Path,
) -> None:
    repo, receipt, catalog_root, _journal = _external_liveness_fixture(tmp_path)
    index = floor_job_checkpoint.load_bound_index(
        catalog_root,
        job_id=receipt["job_id"],
        nonce=receipt["nonce"],
        submitted_at=receipt["submitted_at"],
    )
    assert _append_fixture_checkpoint(
        Path(index["evidence_root"]),
        job_id=receipt["job_id"],
        nonce=receipt["nonce"],
        stage="floor-driver",
        transition="signalled",
        rc=143,
        command="signal TERM",
    )
    result = floor_liveness.classify(
        receipt["job_id"], receipt["nonce"], timeout_s=5,
        repo_root=repo, evidence_root=catalog_root,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], present=False,
        ),
    )
    external = next(
        item for item in result["evidence"]
        if item["kind"] == "external-job-checkpoint"
    )
    assert external["last_transition"] == "signalled"
    assert external["cause"] == "unknown"
    assert external["observed_signal"] == "TERM"


def test_floor_liveness_running_without_marker_times_out_indeterminate(
    tmp_path: Path,
) -> None:
    repo, submission, _qsub_args, _qsub_cwd = _successful_submission(tmp_path)
    receipt = artifacts.load_json_strict(submission / "submit-receipt.json")
    now = [0.0]

    def clock() -> float:
        return now[0]

    def sleep(seconds: float) -> None:
        now[0] += seconds

    result = floor_liveness.classify(
        receipt["job_id"],
        receipt["nonce"],
        timeout_s=2,
        poll_interval_s=1,
        repo_root=repo,
        run_command=lambda _command, **_kwargs: _qstat_result(
            receipt["job_id"], state="RUN",
        ),
        clock=clock,
        sleep=sleep,
    )

    assert result["classification"] == "indeterminate"
    assert result["reason"] == "overall timeout expired before a conclusive state"
    assert result["last_qstat"]["state"] == "RUN"
    assert result["last_qstat"]["compute_marker"] == {
        "present": False,
        "valid": False,
    }


def test_floor_liveness_cli_finished_is_nonzero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        floor_liveness,
        "classify",
        lambda *_args, **_kwargs: {
            "schema_version": "pegasus-floor-liveness/v1",
            "classification": "finished",
        },
    )

    rc = floor_liveness.main([
        "98765.nqsv",
        "a" * 32,
        "--timeout-seconds",
        "5",
    ])

    assert rc == 3
    assert json.loads(capsys.readouterr().out)["classification"] == "finished"


def test_submit_floor_second_dry_run_uses_distinct_create_only_nonce(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    for _ in range(2):
        result = _submit(repo, bin_dir, "--dry-run")
        assert result.returncode == 0, result.stderr
    assert not sentinel.exists()
    submissions = list(
        (repo / "output" / "env" / "pegasus" / "floor" / "attempts" / "submissions").glob("*")
    )
    assert len(submissions) == 2
    nonces = {path.name for path in submissions}
    assert len(nonces) == 2
    assert all(re.fullmatch(r"[0-9a-f]{32}", nonce) for nonce in nonces)
    assert all((path / "pre-submit.json").is_file() for path in submissions)
    assert all((path / "submit-receipt.json").is_file() for path in submissions)


def test_submit_floor_dirty_source_fails_before_side_effects(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    job = repo / "tools" / "pegasus" / "floor_campaign.sh"
    job.write_text(job.read_text(encoding="utf-8") + "\n# dirty\n", encoding="utf-8")
    result = _submit(repo, bin_dir, "--dry-run")
    assert result.returncode == 2
    assert "tracked working tree bytes are dirty" in result.stderr
    assert not (repo / "output" / "env").exists()
    assert not (repo / "output" / "claims").exists()
    assert not sentinel.exists()


def test_submit_floor_tracked_output_mutation_fails_before_side_effects(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    tracked = repo / "output" / ".tracked-fixture"
    tracked.write_text("mutated\n", encoding="utf-8")
    result = _submit(repo, bin_dir, "--dry-run")
    assert result.returncode == 2
    assert "tracked working tree bytes are dirty" in result.stderr
    assert not (repo / "output" / "env").exists()
    assert not (repo / "output" / "claims").exists()
    assert not sentinel.exists()


def test_submit_floor_untracked_outside_output_fails_before_side_effects(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    (repo / "unexpected.txt").write_text("untracked\n", encoding="utf-8")
    result = _submit(repo, bin_dir, "--dry-run")
    assert result.returncode == 2
    assert "untracked content outside output/" in result.stderr
    assert not (repo / "output" / "env").exists()
    assert not (repo / "output" / "claims").exists()
    assert not sentinel.exists()


def test_submit_floor_git_untracked_scan_failure_is_fail_closed(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    real_git = shutil.which("git")
    assert real_git is not None
    git_stub = bin_dir / "git"
    git_stub.write_text(
        "#!/bin/sh\n"
        "case \" $* \" in\n"
        "  *' ls-files --others --exclude-standard -z '*) exit 73 ;;\n"
        "esac\n"
        f"exec {shlex.quote(real_git)} \"$@\"\n",
        encoding="utf-8",
    )
    git_stub.chmod(0o755)

    result = _submit(repo, bin_dir, "--dry-run")
    assert result.returncode == 73
    assert "cannot inspect untracked repository content" in result.stderr
    assert not (repo / "output" / "env").exists()
    assert not (repo / "output" / "claims").exists()
    assert not sentinel.exists()


@pytest.mark.parametrize(
    "kind", ["symlink", "regular-file", "mode-0755"], ids=str
)
def test_submit_floor_rejects_unsafe_existing_claim_root(
    tmp_path: Path, kind: str
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    claims = repo / "output" / "claims"
    if kind == "symlink":
        # containment 自体は満たし、symlink component 拒否だけを発火させる。
        target = repo / "output" / "claim-target"
        target.mkdir(mode=0o700)
        target.chmod(0o700)
        claims.symlink_to(target, target_is_directory=True)
    elif kind == "regular-file":
        claims.write_text("sentinel\n", encoding="utf-8")
    else:
        claims.mkdir(mode=0o755)
        claims.chmod(0o755)
    result = _submit(repo, bin_dir, "--dry-run")
    assert result.returncode == 2
    assert not sentinel.exists()
    receipts = list((repo / "output").glob("**/submit-receipt.json"))
    assert receipts == []
    if kind == "symlink":
        assert claims.is_symlink()
    elif kind == "regular-file":
        assert claims.read_text(encoding="utf-8") == "sentinel\n"
    else:
        assert stat.S_IMODE(claims.stat().st_mode) == 0o755


@pytest.mark.parametrize(
    "protected_relative",
    ["output/s8b-freeze/floor-attempts", "output/campaigns/floor-attempts"],
    ids=["freeze", "campaigns"],
)
def test_submit_floor_rejects_protected_output_namespaces(
    tmp_path: Path, protected_relative: str
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    result = _submit(
        repo,
        bin_dir,
        "--dry-run",
        "--repo-root",
        str(repo),
        "--attempts-root",
        str(repo / protected_relative),
    )
    assert result.returncode == 2
    assert not (repo / protected_relative).exists()
    assert not sentinel.exists()


def test_submit_floor_rejects_symlink_invocation(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    link = tmp_path / "submit-floor-link"
    link.symlink_to(repo / "tools" / "pegasus" / "submit_floor.sh")
    env = _git_env(repo)
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    result = subprocess.run(
        ["bash", str(link), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 2
    assert not sentinel.exists()
    assert not (repo / "output" / "env").exists()


def test_submit_floor_real_submission_requires_fixed_repo_script(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    relocated_dir = repo / "tools" / "other"
    relocated_dir.mkdir()
    relocated = relocated_dir / "submit_floor.sh"
    shutil.copy2(repo / "tools" / "pegasus" / "submit_floor.sh", relocated)
    _git(repo, "add", "tools/other/submit_floor.sh")
    _git(repo, "commit", "-qm", "track relocated submit script")
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    env = _git_env(repo)
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    result = subprocess.run(
        ["bash", str(relocated)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 2
    assert not sentinel.exists()
    assert not (repo / "output" / "env").exists()


@pytest.mark.parametrize(
    "option",
    ["--repo-root", "--attempts-root", "--job-script"],
    ids=["repo-root", "attempts-root", "job-script"],
)
def test_submit_floor_rejects_overrides_in_real_submission(
    tmp_path: Path, option: str
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    values = {
        "--repo-root": str(repo),
        "--attempts-root": str(repo / "output" / "alternate"),
        "--job-script": str(repo / "tools" / "pegasus" / "floor_campaign.sh"),
    }
    result = _submit(repo, bin_dir, option, values[option])
    assert result.returncode == 2
    assert "overrides require --dry-run" in result.stderr
    assert not sentinel.exists()
    assert not (repo / "output" / "env").exists()
    assert not (repo / "output" / "claims").exists()


def test_submit_floor_preflight_failure_records_and_stops_before_qsub(
    tmp_path: Path,
) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(
        tmp_path,
        failures={
            "qstat": 0,
            "pegasusinfo": 0,
            "rbudgetcheck": 9,
            "check_quota": 0,
            "qsub": 99,
        },
    )
    result = _submit(repo, bin_dir, "--confirm-official-floor-run")
    assert result.returncode == 3
    assert "preflight captures failed" in result.stderr
    calls = sentinel.read_text(encoding="utf-8").splitlines()
    assert calls == ["qstat", "pegasusinfo", "rbudgetcheck", "check_quota"]
    submission = _only_submission(
        repo, "output/env/pegasus/floor/attempts"
    )
    pre = json.loads((submission / "pre-submit.json").read_text(encoding="utf-8"))
    assert pre["preflight"]["rbudgetcheck"]["rc"] == 9
    assert not (submission / "submit-receipt.json").exists()
    assert not (repo / "output" / "claims").exists()


def test_submit_floor_rejects_symlinked_staging_ancestor(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    bin_dir, sentinel = _sentinel_bin(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / "output" / "env").symlink_to(outside, target_is_directory=True)
    result = _submit(repo, bin_dir, "--dry-run")
    assert result.returncode == 2
    assert "unsafe submission path" in result.stderr
    assert list(outside.iterdir()) == []
    assert not sentinel.exists()


def _qstat_parser_code() -> str:
    source = JOB.read_text(encoding="utf-8")
    marker = (
        'qstat_output=$("$PY" -I -B - "$ATTEMPT_DIR/qstat-f.stdout" '
        '"$qstat_rc" <<\'PY\'\n'
    )
    start = source.index(marker) + len(marker)
    end = source.index("\nPY\n) || qstat_parse_rc=$?", start)
    return source[start:end]


def test_floor_job_qstat_parser_accepts_real_nqsv_fields(tmp_path: Path) -> None:
    # 実 job 0:867874.nqsv の qstat-f.stdout から必要 field を抜粋した fixture。
    fixture = tmp_path / "qstat-f.stdout"
    fixture.write_text(
        "    Started Request Time = Sun Jul 19 04:40:27 2026\n"
        "  Execution Hosts(JSVNO):\n"
        "    bnode048(48)\n"
        "    Remaining Elapse = 7199S\n"
        "    (Per-Req) Elapse Time Limit       = Max:     7200S Warn:     7200S \n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-", str(fixture), "0"],
        input=_qstat_parser_code(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    host, started, limit_s, remaining_s = result.stdout.splitlines()
    assert host == "bnode048"
    assert started.isdigit() and int(started) > 1_000_000_000
    assert limit_s == "7200"
    assert remaining_s == "7199"


def _qstat_policy_fragment() -> str:
    source = JOB.read_text(encoding="utf-8")
    start = source.index("qstat_parse_rc=0")
    end = source.index(
        'if [[ "$ASSIGNED_HOST" == "$HOSTNAME_SHORT" ]]', start
    )
    return source[start:end]


@pytest.mark.parametrize(
    ("scheduler_limit_s", "expected_rc"),
    [(36000, 0), (35999, 2)],
    ids=["policy-match-36000", "policy-mismatch"],
)
def test_floor_job_qstat_value_drives_policy_check(
    tmp_path: Path, scheduler_limit_s: int, expected_rc: int
) -> None:
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "qstat-f.stdout").write_text(
        "    Started Request Time = 1784412345\n"
        "  Execution Hosts(JSVNO):\n"
        "    bnode048(48)\n"
        "    Remaining Elapse = 35000S\n"
        "    (Per-Req) Elapse Time Limit       = "
        f"Max: {scheduler_limit_s}S Warn: {scheduler_limit_s}S\n",
        encoding="utf-8",
    )
    floor_policy = json.loads(FLOOR_POLICY.read_text(encoding="utf-8"))
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"PY={shlex.quote(sys.executable)}",
            "qstat_rc=0",
            "PBS_JOBID=0:fixture.nqsv",
            f"REQUESTED_S_POLICY={floor_policy['floor_walltime_s']}",
            "write_failure() { return 0; }",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _qstat_policy_fragment()],
        capture_output=True,
        text=True,
    )
    assert result.returncode == expected_rc, result.stderr
    scheduler_record = json.loads(
        (attempt / "scheduler-elapse.json").read_text(encoding="utf-8")
    )
    assert scheduler_record["scheduler_elapse_limit_s"] == scheduler_limit_s
    assert scheduler_record["policy_floor_walltime_s"] == 36000
    assert scheduler_record["policy_match"] is (expected_rc == 0)


def _receipt_validator_fragment() -> str:
    source = JOB.read_text(encoding="utf-8")
    start = source.index("receipt_rc=0")
    end = source.index("CURRENT_STAGE=source-identity", start)
    return source[start:end]


@pytest.mark.parametrize(
    ("pbs_jobid", "accepted"),
    [("0:98765.nqsv", True), ("0:98766.nqsv", False)],
    ids=["producer-receipt-accepted", "different-job-rejected"],
)
def test_submit_receipt_round_trips_through_job_validator(
    tmp_path: Path, pbs_jobid: str, accepted: bool
) -> None:
    repo, submission, _, _ = _successful_submission(tmp_path)
    receipt = json.loads(
        (submission / "submit-receipt.json").read_text(encoding="utf-8")
    )
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"ATTEMPT_DIR={shlex.quote(str(submission))}",
            f"PY={shlex.quote(sys.executable)}",
            f"IZANAGI_SUBMISSION_NONCE={receipt['nonce']}",
            f"PBS_JOBID={shlex.quote(pbs_jobid)}",
            "PROJECT=SFC",
            "QUEUE=gen_S",
            "NODES=1",
            "REQUESTED_S_POLICY=36000",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            "write_failure() { return 0; }",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _receipt_validator_fragment()],
        capture_output=True,
        text=True,
    )
    assert (result.returncode == 0) is accepted, result.stderr


def _driver_tail() -> str:
    source = JOB.read_text(encoding="utf-8")
    return (
        "CHECKPOINT_PATH=${CHECKPOINT_PATH:-}\n"
        "OFFICIAL_APPROVAL_BOUND=${OFFICIAL_APPROVAL_BOUND:-1}\n"
        + source[
        source.index("protocol_resolution_rc=0") :
        ]
    )


def _floor_driver_stub_source(*, invalid_metric: str | None = None) -> str:
    invalid_assignment = ""
    if invalid_metric == "holdout_missing":
        invalid_assignment = (
            'result["holdouts"] = []\n'
            'result["floors"] = {}\n'
        )
    elif invalid_metric == "pair_missing":
        invalid_assignment = 'result["floors"]["rr79"]["pairs"] = {}\n'
    elif invalid_metric == "pairs":
        invalid_assignment = (
            'result["floors"]["rr79"]["pairs"] = {"candidate": None}\n'
        )
    elif invalid_metric == "nonfinite":
        invalid_assignment = (
            'result["floors"]["rr79"]["scale_ref"] = float("nan")\n'
        )
    elif invalid_metric is not None:
        invalid_assignment = (
            f'result["floors"]["rr79"][{invalid_metric!r}] = None\n'
        )
    return (
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "call_log = os.environ.get('STUB_CALL_LOG')\n"
        "if call_log:\n"
        "    with Path(call_log).open('a', encoding='utf-8') as handle:\n"
        "        handle.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if sys.argv[1:] == ['resolve-current-protocol']:\n"
        "    sys.stdout.write(os.environ.get(\n"
        "        'STUB_RESOLVER_OUTPUT',\n"
        "        'output/s8b-freeze/floor_protocol.json\\n',\n"
        "    ))\n"
        "    raise SystemExit(int(os.environ.get('STUB_RESOLVER_RC', '0')))\n"
        "rc = int(os.environ['STUB_DRIVER_RC'])\n"
        "if rc == 0:\n"
        "    repo = Path(__file__).resolve().parents[2]\n"
        "    protocol_path = Path(sys.argv[sys.argv.index('--protocol') + 1])\n"
        "    freeze_dir = protocol_path.parent\n"
        "    freeze_dir.mkdir(parents=True)\n"
        "    freeze_path = freeze_dir / 'holdout_freeze.json'\n"
        "    freeze = {\n"
        "        'holdouts': {'rr79': {\n"
        "            'variant_binding': {'entries': {\n"
        "                'stock_common': {}, 'candidate': {},\n"
        "            }},\n"
        "        }},\n"
        "    }\n"
        "    freeze_path.write_text(\n"
        "        json.dumps(freeze), encoding='utf-8')\n"
        "    protocol = {\n"
        "        'freeze': {'path': freeze_path.relative_to(repo).as_posix()},\n"
        "        'stock_configuration': 'stock_common',\n"
        "    }\n"
        "    protocol_path.write_text(\n"
        "        json.dumps(protocol), encoding='utf-8')\n"
        "    run_dir = repo / 'output' / 'fixture-run'\n"
        "    run_dir.mkdir(parents=True)\n"
        "    result = {\n"
        "        'holdouts': ['rr79'],\n"
        "        'floors': {'rr79': {\n"
        "            'scale_ref': 1000.0,\n"
        "            'scalar_alt': 30.0,\n"
        "            'pairs': {'candidate': 30.0},\n"
        "        }},\n"
        "    }\n"
        + ("".join(f"    {line}\n" for line in invalid_assignment.splitlines())
           if invalid_assignment else "")
        + "    (run_dir / 'result.json').write_text(\n"
        "        json.dumps(result), encoding='utf-8')\n"
        "    print(json.dumps({'status': 'completed', 'run_dir': str(run_dir)}))\n"
        "raise SystemExit(rc)\n"
    )


def _run_driver_tail_with_resolver(
    tmp_path: Path, *, resolver_output: str, resolver_rc: int = 0
) -> tuple[subprocess.CompletedProcess[str], Path, list[list[str]], Path]:
    repo = tmp_path / "repo"
    driver = repo / "orchestrator" / "campaign" / "s8b_floor_campaign.py"
    driver.parent.mkdir(parents=True)
    driver.write_text(_floor_driver_stub_source(), encoding="utf-8")
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    call_log = tmp_path / "driver-calls.jsonl"
    failure_call = attempt / "failure-call.txt"
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"PY={shlex.quote(sys.executable)}",
            "PBS_JOBID=0:fixture.nqsv",
            f"CURRENT_COMMIT={'a' * 40}",
            f"JOB_SCRIPT_SHA256={'b' * 64}",
            f"EXECUTING_SCRIPT_SHA256={'c' * 64}",
            f"IZANAGI_SUBMISSION_NONCE={'d' * 32}",
            "REQUESTED_S=36000",
            "export STUB_DRIVER_RC=0",
            f"export STUB_CALL_LOG={shlex.quote(str(call_log))}",
            "export STUB_RESOLVER_OUTPUT=" + shlex.quote(resolver_output),
            f"export STUB_RESOLVER_RC={resolver_rc}",
            "checkpoint_event() { return 0; }",
            "write_failure() {",
            f"  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" > {shlex.quote(str(failure_call))}",
            "}",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _driver_tail()],
        capture_output=True,
        text=True,
    )
    calls = []
    if call_log.exists():
        calls = [
            json.loads(line)
            for line in call_log.read_text(encoding="utf-8").splitlines()
        ]
    return result, attempt, calls, failure_call


def test_floor_protocol_resolution_is_shared_by_all_consumers(
    tmp_path: Path,
) -> None:
    protocol_path = (
        "output/s8b-freeze/protocols/"
        + "a" * 64
        + "/"
        + "b" * 40
        + "/floor_protocol.json"
    )
    result, attempt, calls, failure_call = _run_driver_tail_with_resolver(
        tmp_path, resolver_output=protocol_path + "\n"
    )

    assert result.returncode == 0, result.stderr
    assert calls == [
        ["resolve-current-protocol"],
        [
            "--mode",
            "official",
            "--protocol",
            str(tmp_path / "repo" / protocol_path),
            "--confirm-official-floor-run",
        ],
    ]
    job_result = json.loads(
        (attempt / "job-result.json").read_text(encoding="utf-8")
    )
    assert job_result["protocol_path"] == protocol_path
    assert (tmp_path / "repo" / protocol_path).is_file()
    assert not (
        tmp_path / "repo" / "output/s8b-freeze/floor_protocol.json"
    ).exists()
    assert (attempt / "floor-driver.launch-attempted").is_file()
    assert not failure_call.exists()


@pytest.mark.parametrize(
    ("resolver_output", "resolver_rc", "expected_rc"),
    [
        ("output/s8b-freeze/floor_protocol.json\n", 7, 7),
        ("", 0, 2),
        (
            "output/s8b-freeze/floor_protocol.json\n"
            "output/s8b-freeze/other.json\n",
            0,
            2,
        ),
        ("/tmp/floor_protocol.json\n", 0, 2),
    ],
    ids=["nonzero", "empty", "multiple-lines", "absolute"],
)
def test_floor_protocol_resolution_failure_stops_before_driver_launch(
    tmp_path: Path,
    resolver_output: str,
    resolver_rc: int,
    expected_rc: int,
) -> None:
    result, attempt, calls, failure_call = _run_driver_tail_with_resolver(
        tmp_path,
        resolver_output=resolver_output,
        resolver_rc=resolver_rc,
    )

    assert result.returncode == expected_rc, result.stderr
    assert calls == [["resolve-current-protocol"]]
    assert failure_call.read_text(encoding="utf-8").split("|", 2)[:2] == [
        str(expected_rc),
        "floor_protocol_resolution",
    ]
    assert not (attempt / "floor-driver.launch-attempted").exists()
    assert not (attempt / "job-result.json").exists()


def _reservation_writer_fragment() -> str:
    source = JOB.read_text(encoding="utf-8")
    start = source.index(
        'export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"'
    )
    end = source.index("# 出典: certify_calibration.sh:347-357", start)
    return source[start:end]


def test_floor_reservation_record_has_exact_schema(tmp_path: Path) -> None:
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    script_sha = "b" * 64
    nonce = "d" * 32
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"PY={shlex.quote(sys.executable)}",
            "PBS_JOBID=0:fixture.nqsv",
            "REQUESTED_S=36000",
            "SCHEDULER_STARTED_EPOCH=1784412345",
            "DEADLINE_EPOCH=1784448345",
            "HOSTNAME_OBSERVED=bnode048",
            "BOOT_ID=11111111-2222-3333-4444-555555555555",
            f"JOB_SCRIPT_SHA256={script_sha}",
            f"IZANAGI_SUBMISSION_NONCE={nonce}",
            "checkpoint_event() { return 0; }",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _reservation_writer_fragment()],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    record = json.loads(
        (attempt / "reservation.json").read_text(encoding="utf-8")
    )
    assert set(record) == RESERVATION_KEYS
    assert record == {
        "job_id": "0:fixture.nqsv",
        "requested_s": 36000,
        "scheduler_started_epoch": 1784412345,
        "deadline_epoch": 1784448345,
        "host": "bnode048",
        "boot_id": "11111111-2222-3333-4444-555555555555",
        "script_sha256": script_sha,
        "nonce": nonce,
        "recorded_epoch": record["recorded_epoch"],
    }
    assert type(record["recorded_epoch"]) is int and record["recorded_epoch"] > 0


@pytest.mark.parametrize("driver_rc", [0, 2, 7], ids=lambda rc: f"rc-{rc}")
def test_floor_driver_failure_propagates_rc(
    tmp_path: Path, driver_rc: int
) -> None:
    repo = tmp_path / "repo"
    driver = repo / "orchestrator" / "campaign" / "s8b_floor_campaign.py"
    driver.parent.mkdir(parents=True)
    driver.write_text(_floor_driver_stub_source(), encoding="utf-8")
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    failure_call = attempt / "failure-call.txt"
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"PY={shlex.quote(sys.executable)}",
            "PBS_JOBID=0:fixture.nqsv",
            f"CURRENT_COMMIT={'a' * 40}",
            f"JOB_SCRIPT_SHA256={'b' * 64}",
            f"EXECUTING_SCRIPT_SHA256={'c' * 64}",
            f"IZANAGI_SUBMISSION_NONCE={'d' * 32}",
            "REQUESTED_S=36000",
            "export STUB_DRIVER_RC=" + str(driver_rc),
            "checkpoint_event() { return 0; }",
            "write_failure() {",
            f"  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" > {shlex.quote(str(failure_call))}",
            "}",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _driver_tail()],
        capture_output=True,
        text=True,
    )
    assert result.returncode == driver_rc, result.stderr
    job_result = json.loads((attempt / "job-result.json").read_text(encoding="utf-8"))
    assert set(job_result) == JOB_RESULT_KEYS
    assert job_result == {
        "schema_version": "pegasus-floor-job-result/v1",
        "pbs_jobid": "0:fixture.nqsv",
        "driver_rc": driver_rc,
        "mode": "official",
        "protocol_path": "output/s8b-freeze/floor_protocol.json",
        "source_commit": "a" * 40,
        "job_script_sha256": "b" * 64,
        "executing_script_sha256": "c" * 64,
        "nonce": "d" * 32,
        "reservation_requested_s": 36000,
        "completed_epoch": job_result["completed_epoch"],
    }
    assert (
        type(job_result["completed_epoch"]) is int
        and job_result["completed_epoch"] > 0
    )
    if driver_rc == 0:
        assert not failure_call.exists()
    else:
        assert failure_call.read_text(encoding="utf-8") == (
            f"{driver_rc}|floor_driver|official floor driver returned nonzero\n"
        )


@pytest.mark.parametrize(
    "invalid_metric", [
        "scale_ref", "scalar_alt", "pairs", "nonfinite",
        "holdout_missing", "pair_missing",
    ],
)
def test_floor_driver_zero_rc_rejects_missing_w2_floor_metric(
    tmp_path: Path, invalid_metric: str
) -> None:
    repo = tmp_path / "repo"
    driver = repo / "orchestrator" / "campaign" / "s8b_floor_campaign.py"
    driver.parent.mkdir(parents=True)
    driver.write_text(
        _floor_driver_stub_source(invalid_metric=invalid_metric), encoding="utf-8",
    )
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    failure_call = attempt / "failure-call.txt"
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"PY={shlex.quote(sys.executable)}",
            "PBS_JOBID=0:fixture.nqsv",
            f"CURRENT_COMMIT={'a' * 40}",
            f"JOB_SCRIPT_SHA256={'b' * 64}",
            f"EXECUTING_SCRIPT_SHA256={'c' * 64}",
            f"IZANAGI_SUBMISSION_NONCE={'d' * 32}",
            "REQUESTED_S=36000",
            "export STUB_DRIVER_RC=0",
            "checkpoint_event() { return 0; }",
            "write_failure() {",
            f"  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" > {shlex.quote(str(failure_call))}",
            "}",
            "",
        ]
    )

    result = subprocess.run(
        ["bash", "-c", prefix + _driver_tail()],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 3, result.stderr
    job_result = json.loads(
        (attempt / "job-result.json").read_text(encoding="utf-8")
    )
    assert job_result["driver_rc"] == 3
    assert failure_call.read_text(encoding="utf-8") == (
        "3|floor_result_metrics|"
        "official floor result is missing finite W-2 floor metrics\n"
    )


def test_floor_driver_fd_setup_failure_does_not_mark_launch(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    driver = repo / "orchestrator" / "campaign" / "s8b_floor_campaign.py"
    driver.parent.mkdir(parents=True)
    driver_ran = tmp_path / "driver-ran"
    driver.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "if sys.argv[1:] == ['resolve-current-protocol']:\n"
        "    print('output/s8b-freeze/floor_protocol.json')\n"
        "    raise SystemExit(0)\n"
        f"Path({str(driver_ran)!r}).write_text('ran', encoding='utf-8')\n"
        "raise SystemExit(7)\n",
        encoding="utf-8",
    )
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    stdout_sentinel = "preexisting stdout\n"
    (attempt / "floor-driver.stdout").write_text(
        stdout_sentinel, encoding="utf-8"
    )
    failure_call = attempt / "failure-call.txt"
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            "set -o noclobber",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"PY={shlex.quote(sys.executable)}",
            "PBS_JOBID=0:fixture.nqsv",
            f"CURRENT_COMMIT={'a' * 40}",
            f"JOB_SCRIPT_SHA256={'b' * 64}",
            f"EXECUTING_SCRIPT_SHA256={'c' * 64}",
            f"IZANAGI_SUBMISSION_NONCE={'d' * 32}",
            "REQUESTED_S=36000",
            "checkpoint_event() { return 0; }",
            "write_failure() {",
            f"  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" > {shlex.quote(str(failure_call))}",
            "}",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _driver_tail()],
        capture_output=True,
        text=True,
    )
    assert result.returncode not in {0, 7}
    assert failure_call.read_text(encoding="utf-8").split("|", 2)[:2] == [
        str(result.returncode),
        "floor_driver_setup",
    ]
    assert (attempt / "floor-driver.stdout").read_text(
        encoding="utf-8"
    ) == stdout_sentinel
    assert not (attempt / "floor-driver.launch-attempted").exists()
    assert not (attempt / "job-result.json").exists()
    assert not driver_ran.exists()


def test_floor_job_result_writer_failure_preserves_driver_rc(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    driver = repo / "orchestrator" / "campaign" / "s8b_floor_campaign.py"
    driver.parent.mkdir(parents=True)
    driver.write_text(
        "import sys\n"
        "if sys.argv[1:] == ['resolve-current-protocol']:\n"
        "    print('output/s8b-freeze/floor_protocol.json')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(7)\n",
        encoding="utf-8",
    )
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    sentinel = '{"preexisting": true}\n'
    (attempt / "job-result.json").write_text(sentinel, encoding="utf-8")
    failure_call = attempt / "failure-call.txt"
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"PY={shlex.quote(sys.executable)}",
            "PBS_JOBID=0:fixture.nqsv",
            f"CURRENT_COMMIT={'a' * 40}",
            f"JOB_SCRIPT_SHA256={'b' * 64}",
            f"EXECUTING_SCRIPT_SHA256={'c' * 64}",
            f"IZANAGI_SUBMISSION_NONCE={'d' * 32}",
            "REQUESTED_S=36000",
            "checkpoint_event() { return 0; }",
            "write_failure() {",
            f"  printf '%s|%s|%s\\n' \"$1\" \"$2\" \"$3\" >> {shlex.quote(str(failure_call))}",
            "}",
            "",
        ]
    )
    result = subprocess.run(
        ["bash", "-c", prefix + _driver_tail()],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 7, result.stderr
    assert (attempt / "job-result.json").read_text(encoding="utf-8") == sentinel
    failures = failure_call.read_text(encoding="utf-8").splitlines()
    assert failures[0].split("|", 2)[:2] == ["1", "job_result"]
    assert failures[1].split("|", 2)[:2] == ["7", "floor_driver"]


def test_floor_job_result_writer_failure_with_successful_driver_keeps_rc_zero(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    driver = repo / "orchestrator" / "campaign" / "s8b_floor_campaign.py"
    driver.parent.mkdir(parents=True)
    driver.write_text(_floor_driver_stub_source(), encoding="utf-8")
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    sentinel = '{"preexisting": true}\n'
    (attempt / "job-result.json").write_text(sentinel, encoding="utf-8")
    prefix = "\n".join(
        [
            "set -Eeuo pipefail",
            f"REPO_ROOT={shlex.quote(str(repo))}",
            f"ATTEMPT_DIR={shlex.quote(str(attempt))}",
            f"PY={shlex.quote(sys.executable)}",
            "PBS_JOBID=0:fixture.nqsv",
            f"CURRENT_COMMIT={'a' * 40}",
            f"JOB_SCRIPT_SHA256={'b' * 64}",
            f"EXECUTING_SCRIPT_SHA256={'c' * 64}",
            f"IZANAGI_SUBMISSION_NONCE={'d' * 32}",
            "REQUESTED_S=36000",
            "export STUB_DRIVER_RC=0",
            "failure_written=0",
            "",
        ]
    )
    source = JOB.read_text(encoding="utf-8")
    writer_start = source.index("write_failure() {")
    writer_end = source.index("write_interpreter_failure()", writer_start)
    result = subprocess.run(
        [
            "bash",
            "-c",
            prefix + source[writer_start:writer_end] + _driver_tail(),
        ],
        capture_output=True,
        text=True,
    )

    # この rc=0 は裁定待ちの既知の穴であり、望ましい挙動として承認したものではない。
    # production の exit code は本 wave では変えない。
    assert result.returncode == 0, result.stderr
    assert (attempt / "job-result.json").read_text(encoding="utf-8") == sentinel
    failure = json.loads((attempt / "failure.json").read_text(encoding="utf-8"))
    assert failure == {
        "schema_version": "pegasus-job-failure/v1",
        "pbs_jobid": "0:fixture.nqsv",
        "rc": 1,
        "stage": "job_result",
        "message": "cannot write floor job result create-only",
        "recorded_epoch": failure["recorded_epoch"],
    }
    assert type(failure["recorded_epoch"]) is int and failure["recorded_epoch"] > 0


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
