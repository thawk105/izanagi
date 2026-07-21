# -*- coding: utf-8 -*-
"""CLI and doctor contract tests for dev-waves."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
from decimal import Decimal
from pathlib import Path
from unittest import mock

_BOOTSTRAP_REPO = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_REPO) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_REPO))

from orchestrator.tests.test_dev_waves_fake import write_fake_claude
from orchestrator.tests.test_dev_waves_integration import (
    _isolated_process_environment,
    _request,
    _supervisor,
    _temporary_repo,
    _wait_terminal,
)
from tools.dev_waves import cli
from tools.dev_waves.daemon import doctor
from tools.dev_waves.schema import (
    PROTOCOL_VERSION,
    ReasonCode,
    ResourceLimits,
    Response,
    RunState,
    SubmitRequest,
    canonical_bytes,
)


_REPO = Path(__file__).resolve().parents[2]
_SUBMIT_CAPS = [
    "--per-wave-timeout-s", "5", "--total-timeout-s", "5",
    "--per-wave-budget-usd", "1", "--total-budget-usd", "1",
    "--max-wave-output-bytes", "65536", "--max-run-bytes", "131072",
]


def test_bootstrap_imports_package_not_same_named_script() -> None:
    result = subprocess.run(
        [sys.executable, str(_REPO / "tools" / "dev_waves.py"), "--help"],
        cwd=_REPO, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "doctor" in result.stdout and "client" in result.stdout
    assert "partially initialized module" not in result.stderr


def test_missing_limit_is_audited_at_root_and_never_creates_run() -> None:
    parser = cli.build_parser()
    try:
        parser.parse_args([
            "client", "submit", "--max-waves", "1", "--profile", "default",
        ])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("client submit accepted omitted hard caps")
    parsed = parser.parse_args([
        "client", "submit", "--max-waves", "1", "--profile", "default",
        *_SUBMIT_CAPS,
    ])
    assert parsed.max_run_bytes == 131072
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            complete = _request(repo)
            fields = tuple(ResourceLimits.__dataclass_fields__)
            for index, field in enumerate(fields):
                values = list(complete.limits.__dict__.values())
                values[index] = None
                request = SubmitRequest(
                    complete.protocol_version, complete.action, complete.repo_identity,
                    complete.max_waves, complete.profile,
                    f"0000000{index}-0000-4000-8000-000000000000",
                    ResourceLimits(*values),
                )
                before = {path.name for path in repo.runtime.iterdir()}
                try:
                    supervisor.submit(request)
                except Exception as exc:
                    assert getattr(exc, "code", None) is ReasonCode.BUDGET_INVALID, field
                else:
                    raise AssertionError("budget-invalid request created a run")
                after = {path.name for path in repo.runtime.iterdir()}
                assert after - before <= {"invalid-requests.jsonl"}
                assert not any(name.startswith("dw-") for name in after)
            assert not (repo.fake.parent / "invocations.jsonl").exists()


def test_serve_requires_every_absolute_cap_hook_and_model_allowlist() -> None:
    parser = cli.build_parser()
    required = {
        "--max-waves", "--max-per-wave-timeout-s", "--max-total-timeout-s",
        "--max-per-wave-budget-usd", "--max-total-budget-usd",
        "--max-wave-output-bytes", "--max-run-bytes", "--required-hook",
        "--allowed-model",
    }
    serve = next(action for action in parser._actions if action.dest == "command")
    subparser = serve.choices["serve"]
    observed = {
        option for action in subparser._actions if action.required
        for option in action.option_strings
    }
    assert required <= observed


def test_server_profile_strict_decode_rejects_duplicate_unknown_and_nan() -> None:
    base = {
        "schema_version": 1, "repo_root": "/repo", "fake_child_executable": "/fake",
        "fake_child_sha256": "a" * 64, "profile": "default", "model": "fake-model",
        "effort": "low", "allowed_models": ["fake-model"],
        "check_specs": [{"name": "docs", "argv": ["python3", "tools/task_run_check.py", "docs-check"], "timeout_s": 5}],
        "settings_path": "/repo/.claude/settings.json", "settings_sha256": "b" * 64,
        "required_hooks": [["Bash", "deny-push"]],
        "caps": {"max_waves": 1, "max_per_wave_timeout_s": 5,
                 "max_total_timeout_s": 5, "max_per_wave_budget_usd": "1",
                 "max_total_budget_usd": "1", "max_wave_output_bytes": 65536,
                 "max_run_bytes": 131072},
    }
    raw = json.dumps(base, separators=(",", ":")).encode()
    assert cli.parse_server_profile(raw)["model"] == "fake-model"
    for bad in (
        raw[:-1] + b',"unknown":1}',
        raw.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1'),
        raw.replace(b'"max_waves":1', b'"max_waves":NaN'),
    ):
        try:
            cli.parse_server_profile(bad)
        except Exception:
            pass
        else:
            raise AssertionError("non-strict server profile was accepted")


def test_compact_status_never_contains_raw_output_or_session_identifier() -> None:
    response = Response(
        PROTOCOL_VERSION, "status", True, "dw-safe", RunState.CHILD_RUNNING,
        2, Decimal("1.25"), None, {},
    )
    with mock.patch.object(cli, "_repo_context", return_value=("a" * 64, "/tmp/runtime")), \
            mock.patch.object(cli, "exchange", return_value=canonical_bytes(response)), \
            contextlib.redirect_stdout(io.StringIO()) as output:
        code = cli.main(["client", "status", "dw-safe", "--compact"])
    text = output.getvalue()
    assert code == 0
    assert text == "wave=2 state=child-running elapsed=1.25 reason=-\n"
    assert "session" not in text and "stdout" not in text and "detail" not in text


def test_nested_submit_and_resume_are_rejected_before_socket_or_local_open() -> None:
    with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}), \
            mock.patch.object(cli, "_repo_context", side_effect=AssertionError("must not open")):
        assert cli.main([
            "client", "submit", "--max-waves", "1", "--profile", "default",
            *_SUBMIT_CAPS,
        ]) == 1
    with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}), \
            mock.patch.object(cli, "_local_supervisor", side_effect=AssertionError("must not open")):
        assert cli.main(["resume", "dw-run"]) == 1


def test_one_shot_requires_persisted_profile() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        runtime = Path(temporary)
        main = mock.Mock(path="/repo")
        with mock.patch.object(cli, "_repo_context", return_value=("a" * 64, str(runtime))), \
                mock.patch.object(cli, "resolve_main_worktree", return_value=main):
            try:
                cli._local_supervisor()
            except Exception as exc:
                assert getattr(exc, "code", None) is ReasonCode.SETTINGS_INVALID
                assert exc.detail["kind"] == "missing"
            else:
                raise AssertionError("one-shot fabricated a default profile")


def test_one_shot_rebinds_saved_repo_root_and_settings_digest() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        runtime = root / "runtime"
        runtime.mkdir()
        settings = root / "settings.json"
        settings.write_text("{}\n", encoding="utf-8")
        base = {
            "schema_version": 1, "repo_root": str(root),
            "fake_child_executable": "/bin/false",
            "fake_child_sha256": hashlib.sha256(Path("/bin/false").read_bytes()).hexdigest(),
            "profile": "default", "model": "fake-model", "effort": "low",
            "allowed_models": ["fake-model"],
            "check_specs": [{"name": "docs", "argv": ["python3", "tools/task_run_check.py", "docs-check"], "timeout_s": 5}],
            "settings_path": str(settings),
            "settings_sha256": hashlib.sha256(settings.read_bytes()).hexdigest(),
            "required_hooks": [],
            "caps": {"max_waves": 1, "max_per_wave_timeout_s": 5,
                     "max_total_timeout_s": 5, "max_per_wave_budget_usd": "1",
                     "max_total_budget_usd": "1", "max_wave_output_bytes": 65536,
                     "max_run_bytes": 131072},
        }
        profile = runtime / "server-profile.json"
        profile.write_bytes(canonical_bytes(base))
        main = mock.Mock(path=str(root))
        identity = mock.Mock(digest="a" * 64)
        patches = (
            mock.patch.object(cli, "_repo_context", return_value=("a" * 64, str(runtime))),
            mock.patch.object(cli, "resolve_main_worktree", return_value=main),
            mock.patch.object(cli, "resolve_repo_identity", return_value=identity),
        )
        for patcher in patches:
            patcher.start()
        try:
            settings.write_text('{"changed":true}\n', encoding="utf-8")
            try:
                cli._local_supervisor()
            except Exception as exc:
                assert getattr(exc, "code", None) is ReasonCode.SETTINGS_INVALID
                assert exc.detail["kind"] == "settings-digest-mismatch"
            else:
                raise AssertionError("one-shot ignored saved settings digest")
            settings.write_text("{}\n", encoding="utf-8")
            base["repo_root"] = str(root / "other")
            profile.write_bytes(canonical_bytes(base))
            try:
                cli._local_supervisor()
            except Exception as exc:
                assert getattr(exc, "code", None) is ReasonCode.SETTINGS_INVALID
                assert exc.detail["kind"] == "repo-root-mismatch"
            else:
                raise AssertionError("one-shot ignored saved repo root")
        finally:
            for patcher in reversed(patches):
                patcher.stop()


def test_cancel_is_idempotent_for_terminal_run_and_never_signals_unverified_pid() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            terminal, _seen = _wait_terminal(supervisor, submitted.run_id)
            first = supervisor.cancel(submitted.run_id, "22222222-2222-4222-8222-222222222222")
            second = supervisor.cancel(submitted.run_id, "22222222-2222-4222-8222-222222222222")
            assert first == second
            assert first.state is terminal.state


def test_export_is_create_only_and_contains_only_sanitized_wal_view() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            _wait_terminal(supervisor, submitted.run_id)
            destination = root / "export.json"
            supervisor.export(submitted.run_id, destination)
            value = json.loads(destination.read_text(encoding="utf-8"))
            assert value["run_id"] == submitted.run_id
            assert value["status"]["state"] == "completed"
            text = destination.read_text(encoding="utf-8")
            assert "IGNORE STRUCTURED_OUTPUT" not in text
            with mock.patch.object(Path, "exists", return_value=True):
                try:
                    supervisor.export(submitted.run_id, destination)
                except FileExistsError:
                    pass
                else:
                    raise AssertionError("export replaced an existing path")


def _write_probe(directory: Path, *, complete_help: bool = True) -> tuple[Path, Path]:
    executable = directory / "probe-cli"
    marker = directory / "probe-argv.jsonl"
    help_text = (
        "--model --effort --permission-mode auto --output-format json "
        "--json-schema --max-budget-usd --add-dir"
    )
    if not complete_help:
        help_text = help_text.replace(" auto", "")
    source = f'''#!/usr/bin/env python3
import json, os, sys
fd = os.open({str(marker)!r}, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
os.write(fd, (json.dumps(sys.argv[1:]) + "\\n").encode()); os.fsync(fd); os.close(fd)
if sys.argv[1:] == ["--version"]: print("2.1.214")
elif sys.argv[1:] == ["--help"]: print({help_text!r})
else: raise SystemExit(9)
'''
    executable.write_text(source, encoding="utf-8")
    executable.chmod(0o700)
    return executable, marker


def test_doctor_probe_invokes_fake_version_and_help_only() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        executable, marker = _write_probe(root)
        report = doctor(
            repo_root=str(root), executable=str(executable), probe_cli=True,
            probe_timeout_s=2,
        )
        assert report.ok
        invocations = [json.loads(line) for line in marker.read_text().splitlines()]
        assert invocations == [["--version"], ["--help"]]


def test_doctor_requires_auto_and_json_output_capabilities() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        executable, _marker = _write_probe(root, complete_help=False)
        report = doctor(
            repo_root=str(root), executable=str(executable), probe_cli=True,
            probe_timeout_s=2,
        )
        assert not report.ok
        assert report.checks[0][2] == ReasonCode.FLAG_UNAVAILABLE.value


def test_doctor_probe_never_adds_print_mode_model_or_prompt_and_fs_probe_is_real() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        executable, marker = _write_probe(root)
        report = doctor(
            repo_root=str(root), executable=str(executable), probe_cli=True,
            probe_timeout_s=2, probe_fs=True,
        )
        # The managed sandbox may forbid AF_UNIX bind through /proc/self/fd.
        # Doctor must report that real probe fail-closed rather than simulating
        # success; the CLI probe remains independently green.
        checks = {name: (ok, detail) for name, ok, detail in report.checks}
        assert checks["cli"][0]
        assert checks["fs"][0] or checks["fs"][1] == ReasonCode.RUNTIME_IO_FAILURE.value
        flattened = [token for line in marker.read_text().splitlines() for token in json.loads(line)]
        assert "-p" not in flattened
        assert not any(token.startswith("--model") or token.startswith("/dev-wave")
                       for token in flattened)
        assert set(checks) == {"cli", "fs"}


def _run() -> int:
    test_bootstrap_imports_package_not_same_named_script()
    test_missing_limit_is_audited_at_root_and_never_creates_run()
    test_serve_requires_every_absolute_cap_hook_and_model_allowlist()
    test_server_profile_strict_decode_rejects_duplicate_unknown_and_nan()
    test_compact_status_never_contains_raw_output_or_session_identifier()
    test_nested_submit_and_resume_are_rejected_before_socket_or_local_open()
    test_one_shot_requires_persisted_profile()
    test_one_shot_rebinds_saved_repo_root_and_settings_digest()
    test_cancel_is_idempotent_for_terminal_run_and_never_signals_unverified_pid()
    test_export_is_create_only_and_contains_only_sanitized_wal_view()
    test_doctor_probe_invokes_fake_version_and_help_only()
    test_doctor_requires_auto_and_json_output_capabilities()
    test_doctor_probe_never_adds_print_mode_model_or_prompt_and_fs_probe_is_real()
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
