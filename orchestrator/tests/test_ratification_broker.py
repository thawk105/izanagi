from __future__ import annotations

import base64
from dataclasses import dataclass
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pty
import shutil
import stat
import subprocess
import sys
import termios
import tempfile
from types import SimpleNamespace
from typing import Any

import pytest

from orchestrator.campaign import campaign_lock
from orchestrator.campaign import enforcement_source_ratification_receipt as receipt_verifier


ROOT = Path(__file__).resolve().parents[2]
BROKER_FILE = ROOT / "tools" / "ratification_broker.py"
RUNNER_FILE = ROOT / "tools" / "run_tests.py"
SPEC = importlib.util.spec_from_file_location("ratification_broker", BROKER_FILE)
assert SPEC is not None and SPEC.loader is not None
broker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(broker)
REAL_OPENSSL = shutil.which("openssl")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", os.fspath(repo), *args],
        stdin=subprocess.DEVNULL,
    )


def _git_run(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", os.fspath(repo), *args],
        stdin=subprocess.DEVNULL,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _make_key(path: Path) -> bytes:
    if REAL_OPENSSL is None:
        pytest.skip("openssl is required for broker tests")
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [REAL_OPENSSL, "genpkey", "-algorithm", "ED25519", "-out", os.fspath(path)],
        stdin=subprocess.DEVNULL,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    path.chmod(0o600)
    der = subprocess.check_output(
        [REAL_OPENSSL, "pkey", "-in", os.fspath(path), "-pubout", "-outform", "DER"],
        stdin=subprocess.DEVNULL,
    )
    prefix = bytes.fromhex("302a300506032b6570032100")
    assert len(der) == len(prefix) + 32 and der.startswith(prefix)
    return der[len(prefix):]


def _private_material(key: Path) -> tuple[bytes, bytes]:
    assert REAL_OPENSSL is not None
    pem = key.read_bytes()
    der = subprocess.check_output(
        [REAL_OPENSSL, "pkey", "-in", os.fspath(key), "-outform", "DER"],
        stdin=subprocess.DEVNULL,
    )
    return pem, der[-32:]


def _private_encodings(key: Path) -> dict[str, bytes]:
    pem, seed = _private_material(key)
    return {
        "pem": pem,
        "seed": seed,
        "pem_base64": base64.b64encode(pem),
        "seed_base64": base64.b64encode(seed),
        "pem_hex": pem.hex().encode("ascii"),
        "seed_hex": seed.hex().encode("ascii"),
    }


def _trust_line(public_key: bytes) -> bytes:
    return _canonical({
        "public_key_ed25519_base64": base64.b64encode(public_key).decode("ascii"),
        "schema_version": broker.TRUST_SCHEMA,
    }) + b"\n"


def _lock_source(paths: tuple[str, ...]) -> bytes:
    members = b"".join(f"    {json.dumps(path)},\n".encode("ascii") for path in paths)
    return b"CONTRACT_LOADER_RELATIVE_PATHS = (\n" + members + b")\n"


@dataclass
class BrokerEnv:
    remote: Path
    key: Path
    public_key: bytes
    log: Path
    environ: dict[str, str]
    blobs: dict[str, bytes]
    initial_head: str

    @property
    def ledger(self) -> Path:
        return self.remote / broker.LEDGER_PATH

    @property
    def trust(self) -> Path:
        return self.remote / broker.TRUST_PATH


@pytest.fixture
def broker_env(tmp_path: Path) -> BrokerEnv:
    public_key_path = tmp_path / "keys" / "ratification-ed25519.key"
    public_key = _make_key(public_key_path)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log = tmp_path / "calls.jsonl"
    ssh = fake_bin / "ssh"
    ssh.write_text(
        """#!/usr/bin/env python3
import base64, json, os, subprocess, sys
data = sys.stdin.buffer.read()
with open(os.environ["BROKER_TEST_LOG"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps({"tool": "ssh", "argv": sys.argv[1:],
                             "stdin": base64.b64encode(data).decode("ascii"),
                             "environ": dict(os.environ)}) + "\\n")
result = subprocess.run(sys.argv[-1], shell=True, input=data,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
sys.stdout.buffer.write(result.stdout)
sys.stderr.buffer.write(result.stderr)
raise SystemExit(result.returncode)
""",
        encoding="utf-8",
    )
    ssh.chmod(0o755)
    openssl = fake_bin / "openssl"
    openssl.write_text(
        """#!/usr/bin/env python3
import base64, json, os, subprocess, sys
data = sys.stdin.buffer.read()
with open(os.environ["BROKER_TEST_LOG"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps({"tool": "openssl", "argv": sys.argv[1:],
                             "stdin": base64.b64encode(data).decode("ascii"),
                             "environ": dict(os.environ)}) + "\\n")
passed_fds = tuple(int(arg.rsplit("/", 1)[1]) for arg in sys.argv[1:]
                   if arg.startswith("/proc/self/fd/"))
result = subprocess.run([os.environ["BROKER_TEST_OPENSSL"], *sys.argv[1:]],
                        input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        pass_fds=passed_fds)
sys.stdout.buffer.write(result.stdout)
sys.stderr.buffer.write(result.stderr)
raise SystemExit(result.returncode)
""",
        encoding="utf-8",
    )
    openssl.chmod(0o755)

    remote = tmp_path / "remote"
    remote.mkdir()
    _git_run(remote, "init", "-q")
    _git_run(remote, "config", "user.name", "Trusted Operator")
    _git_run(remote, "config", "user.email", "operator@example.invalid")
    blobs = {path: f"blob for {path}\n".encode("ascii") for path in broker.CLOSURE_PATHS}
    blobs["orchestrator/campaign/campaign_lock.py"] = _lock_source(broker.CLOSURE_PATHS)
    for path, value in blobs.items():
        destination = remote / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(value)
    trust = remote / broker.TRUST_PATH
    trust.parent.mkdir(parents=True, exist_ok=True)
    trust.write_bytes(_trust_line(public_key))
    ledger = remote / broker.LEDGER_PATH
    ledger.write_bytes(b"")
    _git_run(remote, "add", ".")
    _git_run(remote, "commit", "-qm", "fixture bootstrap")
    initial_head = _git(remote, "rev-parse", "HEAD").strip().decode("ascii")

    environ = os.environ.copy()
    environ.update({
        "PATH": os.fspath(fake_bin) + os.pathsep + environ["PATH"],
        "BROKER_TEST_LOG": os.fspath(log),
        "BROKER_TEST_OPENSSL": REAL_OPENSSL or "",
    })
    return BrokerEnv(
        remote=remote,
        key=public_key_path,
        public_key=public_key,
        log=log,
        environ=environ,
        blobs=blobs,
        initial_head=initial_head,
    )


def _command(env: BrokerEnv, *extra: str) -> list[str | Path]:
    return [
        sys.executable,
        BROKER_FILE,
        "--target",
        f"fixture:{env.remote}",
        "--key-file",
        env.key,
        *extra,
    ]


def _run_without_tty(env: BrokerEnv, answer: str = "y\n") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _command(env),
        input=answer,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env.environ,
        check=False,
        start_new_session=True,
    )


def _run_with_tty(env: BrokerEnv, answer: bytes = b"y\n") -> subprocess.CompletedProcess[str]:
    if not hasattr(termios, "TIOCSCTTY"):
        pytest.skip("controlling PTY setup is unavailable")
    try:
        master, slave = pty.openpty()
    except OSError:
        pytest.skip("PTY allocation is unavailable")

    def attach_controlling_tty() -> None:
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

    try:
        process = subprocess.Popen(
            _command(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env.environ,
            pass_fds=(slave,),
            preexec_fn=attach_controlling_tty,
        )
    except (OSError, subprocess.SubprocessError):
        os.close(master)
        os.close(slave)
        pytest.skip("controlling PTY setup is unavailable")
    os.close(slave)
    try:
        os.write(master, answer)
        stdout, stderr = process.communicate(timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        process.kill()
        process.wait()
        pytest.skip("controlling PTY did not operate in this environment")
    finally:
        os.close(master)
    return subprocess.CompletedProcess(
        process.args,
        process.returncode,
        stdout.decode("utf-8", "replace"),
        stderr.decode("utf-8", "replace"),
    )


def _calls(env: BrokerEnv) -> list[dict[str, Any]]:
    if not env.log.exists():
        return []
    return [json.loads(line) for line in env.log.read_text(encoding="utf-8").splitlines()]


def _expected_digest(env: BrokerEnv) -> str:
    mapping = {
        path: hashlib.sha256(blob).hexdigest()
        for path, blob in env.blobs.items()
    }
    return hashlib.sha256(_canonical(mapping)).hexdigest()


def _sign(key: Path, message: bytes) -> bytes:
    assert REAL_OPENSSL is not None
    with tempfile.TemporaryDirectory(prefix="ratification-broker-test-sign-") as raw_dir:
        private_dir = Path(raw_dir)
        private_dir.chmod(0o700)
        message_path = private_dir / "message.bin"
        fd = os.open(
            message_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                fd = -1
                stream.write(message)
        finally:
            if fd >= 0:
                os.close(fd)
        try:
            signature = subprocess.check_output(
                [
                    REAL_OPENSSL,
                    "pkeyutl",
                    "-sign",
                    "-rawin",
                    "-inkey",
                    os.fspath(key),
                    "-in",
                    os.fspath(message_path),
                ],
                stdin=subprocess.DEVNULL,
            )
        finally:
            message_path.unlink(missing_ok=True)
    assert len(signature) == 64
    return signature


def _receipt(
    env: BrokerEnv,
    *,
    serial: int = 1,
    previous_hash: str | None = None,
    source_commit: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "closure_digest_sha256": _expected_digest(env),
        "closure_paths": list(broker.SORTED_PATHS),
        "closure_paths_sha256": hashlib.sha256(
            _canonical(list(broker.SORTED_PATHS))
        ).hexdigest(),
        "decision": "ratify",
        "previous_receipt_sha256": previous_hash,
        "ratification_serial": serial,
        "schema_version": broker.SCHEMA,
        "source_commit": source_commit or env.initial_head,
        "trust_root_sha256": hashlib.sha256(env.public_key).hexdigest(),
    }
    signature = _sign(env.key, broker.DOMAIN + _canonical(body))
    body["signature_ed25519_base64"] = base64.b64encode(signature).decode("ascii")
    return body


def _commit_ledger(env: BrokerEnv, raw: bytes, message: str = "ledger fixture") -> str:
    env.ledger.write_bytes(raw)
    _git_run(env.remote, "add", "--", broker.LEDGER_PATH)
    _git_run(env.remote, "commit", "-qm", message)
    return _git(env.remote, "rev-parse", "HEAD").strip().decode("ascii")


def test_cli_has_no_dead_approval_flag() -> None:
    destinations = {action.dest for action in broker._parser()._actions}
    assert destinations == {"help", "target", "key_file"}


def test_closure_paths_match_production_order_exactly() -> None:
    assert broker.CLOSURE_PATHS == campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS


def test_missing_private_key_fails_without_creating_it(broker_env: BrokerEnv) -> None:
    broker_env.key.unlink()
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "this broker never creates keys" in result.stderr
    assert "openssl genpkey -algorithm ED25519" in result.stderr
    assert not broker_env.key.exists()
    assert _calls(broker_env) == []


def test_private_key_must_not_be_group_or_other_readable(broker_env: BrokerEnv) -> None:
    broker_env.key.chmod(0o644)
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "must not be readable by group or other" in result.stderr
    assert _calls(broker_env) == []


def test_private_key_symlink_is_rejected(broker_env: BrokerEnv) -> None:
    real_key = broker_env.key.with_name("real.key")
    broker_env.key.rename(real_key)
    broker_env.key.symlink_to(real_key)
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "regular non-symlink" in result.stderr
    assert _calls(broker_env) == []


def test_private_key_non_regular_file_is_rejected(broker_env: BrokerEnv) -> None:
    broker_env.key.unlink()
    broker_env.key.mkdir()
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "regular non-symlink" in result.stderr
    assert _calls(broker_env) == []


def test_private_key_must_be_owned_by_current_user(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[int] = []
    monkeypatch.setattr(os, "open", lambda *_args, **_kwargs: 91)
    monkeypatch.setattr(
        os,
        "fstat",
        lambda _fd: SimpleNamespace(
            st_mode=stat.S_IFREG | 0o600,
            st_uid=os.geteuid() + 1,
        ),
    )
    monkeypatch.setattr(os, "close", closed.append)
    with pytest.raises(broker.BrokerError, match="owned by the broker user"):
        broker._open_private_key(Path("/not-opened"))
    assert closed == [91]


def test_private_key_fd_remains_bound_after_path_replacement(
    broker_env: BrokerEnv,
    tmp_path: Path,
) -> None:
    assert REAL_OPENSSL is not None
    key_fd = broker._open_private_key(broker_env.key)
    try:
        captured_public_key = broker._public_key(REAL_OPENSSL, key_fd)
        original = tmp_path / "original.key"
        broker_env.key.rename(original)
        replacement_public_key = _make_key(broker_env.key)
        message = b"fd-bound signing probe"
        signature = broker._sign(REAL_OPENSSL, key_fd, message)
    finally:
        os.close(key_fd)

    assert replacement_public_key != captured_public_key
    broker.verify(captured_public_key, message, signature)


def test_absent_committed_trust_root_never_writes(broker_env: BrokerEnv) -> None:
    _git_run(broker_env.remote, "rm", "-q", "--", broker.TRUST_PATH)
    _git_run(broker_env.remote, "commit", "-qm", "remove trust root")
    before_head = _git(broker_env.remote, "rev-parse", "HEAD")
    before_ledger = broker_env.ledger.read_bytes()

    result = _run_without_tty(broker_env)

    assert result.returncode != 0
    assert "committed trust root is absent" in result.stderr
    assert broker.TRUST_SCHEMA in result.stderr
    assert f"exclusive-create {broker.LEDGER_PATH} as a 0-byte file" in result.stderr
    assert not broker_env.trust.exists()
    assert broker_env.ledger.read_bytes() == before_ledger
    assert _git(broker_env.remote, "rev-parse", "HEAD") == before_head
    ssh_commands = [call["argv"][-1] for call in _calls(broker_env) if call["tool"] == "ssh"]
    assert not any(" add -- " in command or " commit " in command for command in ssh_commands)


def test_different_committed_trust_root_stops(broker_env: BrokerEnv, tmp_path: Path) -> None:
    other_key = tmp_path / "other.key"
    other_public = _make_key(other_key)
    broker_env.trust.write_bytes(_trust_line(other_public))
    _git_run(broker_env.remote, "add", "--", broker.TRUST_PATH)
    _git_run(broker_env.remote, "commit", "-qm", "different trust root")
    before = broker_env.ledger.read_bytes()
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "differs from this private key" in result.stderr
    assert broker_env.ledger.read_bytes() == before
    assert not any(
        call["tool"] == "openssl" and "pkeyutl" in call["argv"]
        for call in _calls(broker_env)
    )


def test_worktree_trust_root_is_not_read(broker_env: BrokerEnv, tmp_path: Path) -> None:
    other_key = tmp_path / "other.key"
    broker_env.trust.write_bytes(_trust_line(_make_key(other_key)))
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "cannot open /dev/tty" in result.stderr
    assert "trust root differs" not in result.stderr


def test_children_without_payload_receive_eof(broker_env: BrokerEnv) -> None:
    result = _run_without_tty(broker_env, "y\n")
    assert result.returncode != 0
    calls = _calls(broker_env)
    assert calls
    assert all(base64.b64decode(call["stdin"]) == b"" for call in calls)


def test_child_stdin_isolated_for_payload_and_no_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(
        argv: list[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[bytes]:
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, b"stdout", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with_payload = broker._run(["child", "payload"], data=b"signed bytes")
    without_payload = broker._run(["child", "no-payload"])

    assert with_payload.stdout == b"stdout"
    assert without_payload.stdout == b"stdout"
    assert calls[0][1]["input"] == b"signed bytes"
    assert "stdin" not in calls[0][1]
    assert calls[1][1]["stdin"] is subprocess.DEVNULL
    assert "input" not in calls[1][1]


def test_non_tty_cannot_approve(broker_env: BrokerEnv) -> None:
    before_head = _git(broker_env.remote, "rev-parse", "HEAD")
    result = _run_without_tty(broker_env, "y\n")
    assert result.returncode != 0
    assert "cannot open /dev/tty" in result.stderr
    assert _git(broker_env.remote, "rev-parse", "HEAD") == before_head
    assert broker_env.ledger.read_bytes() == b""
    assert not any(
        call["tool"] == "openssl" and "pkeyutl" in call["argv"]
        for call in _calls(broker_env)
    )


def test_control_bytes_are_escaped_before_prompt(capsys: pytest.CaptureFixture[str]) -> None:
    old = {path: b"unchanged\n" for path in broker.CLOSURE_PATHS}
    new = dict(old)
    changed_path = broker.CLOSURE_PATHS[0]
    old[changed_path] = b"old\x1b[2J\x00\tline\n"
    new[changed_path] = b"new\x1b[H\x01line\n"

    broker._show_diff(old, new)
    print("PROMPT-SENTINEL")
    output = capsys.readouterr().out

    assert "\x1b" not in output
    assert "\x00" not in output
    assert "\t" not in output
    assert "\\x1b" in output
    assert "\\x00" in output
    assert "\\x01" in output
    assert "\\t" in output
    assert output.index("\\x1b") < output.index("PROMPT-SENTINEL")


def test_c1_and_bidi_bytes_are_escaped_to_injective_ascii() -> None:
    raw = "left\\right\u009b\u202eright".encode("utf-8")
    escaped = broker._escape_control_bytes(raw)

    assert escaped.isascii()
    assert b"left\\\\right" in escaped
    assert b"\\xc2\\x9b" in escaped
    assert b"\\xe2\\x80\\xae" in escaped
    assert "\u009b".encode("utf-8") not in escaped
    assert "\u202e".encode("utf-8") not in escaped


def test_first_ratification_displays_all_closure_bytes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = broker.CLOSURE_PATHS[0]
    blob = b"first line\nlast\\line\xe2\x80\xae"

    broker._show_diff(None, {path: blob})
    output = capsys.readouterr().out

    assert f"bytes={len(blob)} path={path}" in output
    assert "+first line\n" in output
    assert "+last\\\\line\\xe2\\x80\\xae" in output
    assert "\\ No LF at end of blob" in output
    assert "\u202e" not in output


def test_invalid_signature_on_existing_row_stops_before_approval(broker_env: BrokerEnv) -> None:
    receipt = _receipt(broker_env)
    receipt["signature_ed25519_base64"] = base64.b64encode(b"x" * 64).decode("ascii")
    _commit_ledger(broker_env, _canonical(receipt) + b"\n", "invalid signed row")
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "signature failed at serial 1" in result.stderr
    assert "cannot open /dev/tty" not in result.stderr


def test_every_existing_signature_is_checked(broker_env: BrokerEnv) -> None:
    first = _receipt(broker_env)
    first["signature_ed25519_base64"] = base64.b64encode(b"z" * 64).decode("ascii")
    first_line = _canonical(first)
    first_commit = _commit_ledger(
        broker_env, first_line + b"\n", "bad earlier row"
    )
    second = _receipt(
        broker_env,
        serial=2,
        previous_hash=hashlib.sha256(first_line).hexdigest(),
        source_commit=first_commit,
    )
    _commit_ledger(
        broker_env, first_line + b"\n" + _canonical(second) + b"\n",
        "append later valid row",
    )
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "signature failed at serial 1" in result.stderr


def test_valid_existing_signature_reaches_approval(broker_env: BrokerEnv) -> None:
    receipt = _receipt(broker_env)
    _commit_ledger(broker_env, _canonical(receipt) + b"\n", "valid signed row")
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "cannot open /dev/tty" in result.stderr
    assert "signature failed" not in result.stderr


def test_rewritten_ledger_history_stops_before_approval(broker_env: BrokerEnv) -> None:
    receipt = _receipt(broker_env)
    _commit_ledger(broker_env, _canonical(receipt) + b"\n", "valid signed row")
    _commit_ledger(broker_env, b"", "rewrite ledger to empty")

    result = _run_without_tty(broker_env)

    assert result.returncode != 0
    assert "strict prefix extension" in result.stderr
    assert "cannot open /dev/tty" not in result.stderr
    assert not any(
        call["tool"] == "openssl" and "pkeyutl" in call["argv"]
        for call in _calls(broker_env)
    )


def test_nonempty_ledger_requires_one_final_lf(broker_env: BrokerEnv) -> None:
    receipt = _receipt(broker_env)
    _commit_ledger(broker_env, _canonical(receipt), "missing ledger LF")
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "must end with exactly one LF" in result.stderr


def test_sha256_head_is_rejected_before_signing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key_fd = os.open(os.devnull, os.O_RDONLY)
    sign_called = False

    monkeypatch.setattr(shutil, "which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(broker, "_open_private_key", lambda _path: key_fd)
    monkeypatch.setattr(broker, "_public_key", lambda _openssl, _fd: b"p" * 32)
    monkeypatch.setattr(broker, "_git", lambda *_args, **_kwargs: b"a" * 64 + b"\n")

    def forbidden_sign(*_args: Any, **_kwargs: Any) -> bytes:
        nonlocal sign_called
        sign_called = True
        return b"x" * 64

    monkeypatch.setattr(broker, "_sign", forbidden_sign)
    args = SimpleNamespace(
        target="fixture:/target",
        key_file=Path("/unused"),
    )
    with pytest.raises(broker.BrokerError, match="40-hex SHA-1"):
        broker.run(args)
    assert sign_called is False


def test_generated_signature_is_verified_before_approval(
    broker_env: BrokerEnv,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key, value in broker_env.environ.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(broker, "_require_approval_tty", lambda: None)
    monkeypatch.setattr(broker, "_sign", lambda *_args, **_kwargs: b"x" * 64)
    monkeypatch.setattr(
        broker,
        "_read_approval",
        lambda: pytest.fail("approval was requested before signature verification"),
    )

    args = SimpleNamespace(
        target=f"fixture:{broker_env.remote}",
        key_file=broker_env.key,
    )
    with pytest.raises(broker.BrokerError, match="failed self-verification"):
        broker.run(args)


def test_remote_path_list_mismatch_stops(broker_env: BrokerEnv) -> None:
    lock = broker_env.remote / "orchestrator/campaign/campaign_lock.py"
    lock.write_bytes(_lock_source(broker.CLOSURE_PATHS[:-1]))
    _git_run(broker_env.remote, "add", "--", os.fspath(lock.relative_to(broker_env.remote)))
    _git_run(broker_env.remote, "commit", "-qm", "closure mismatch")
    result = _run_without_tty(broker_env)
    assert result.returncode != 0
    assert "closure path mismatch" in result.stderr
    assert broker_env.ledger.read_bytes() == b""


def test_ledger_changed_between_read_and_append_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = "a" * 40
    observed = "b" * 40
    calls: list[tuple[Any, ...]] = []

    def changed_oid(*args: Any) -> str:
        calls.append(args)
        return observed

    monkeypatch.setattr(broker, "_committed_blob_oid", changed_oid)
    with pytest.raises(broker.BrokerError, match="committed ledger changed"):
        broker._require_ledger_cas("ssh", "host", "/repo", "c" * 40, expected)
    assert len(calls) == 1
    assert calls[0][-1] == broker.LEDGER_PATH


def test_worktree_ledger_drift_is_rejected_inside_transaction(broker_env: BrokerEnv) -> None:
    broker_env.ledger.write_bytes(b"uncommitted worktree bytes\n")
    before_head = _git(broker_env.remote, "rev-parse", "HEAD")
    result = _run_with_tty(broker_env)
    assert result.returncode != 0
    assert "worktree or index ledger differs" in result.stderr
    assert broker_env.ledger.read_bytes() == b"uncommitted worktree bytes\n"
    assert _git(broker_env.remote, "rev-parse", "HEAD") == before_head


def test_approved_receipt_is_signed_committed_and_records_provenance(
    broker_env: BrokerEnv,
) -> None:
    result = _run_with_tty(broker_env)
    assert result.returncode == 0, result.stderr

    new_head = _git(broker_env.remote, "rev-parse", "HEAD").strip().decode("ascii")
    assert new_head != broker_env.initial_head
    assert _git(broker_env.remote, "rev-parse", "HEAD^").strip().decode("ascii") == broker_env.initial_head
    committed = _git(
        broker_env.remote,
        "cat-file",
        "blob",
        f"HEAD:{broker.LEDGER_PATH}",
    )
    assert committed == broker_env.ledger.read_bytes()
    line = committed[:-1]
    receipt = json.loads(line)
    assert line == _canonical(receipt)
    assert set(receipt) == broker.RECEIPT_FIELDS
    assert receipt["ratification_serial"] == 1
    assert receipt["closure_digest_sha256"] == _expected_digest(broker_env)
    signature = base64.b64decode(receipt.pop("signature_ed25519_base64"), validate=True)
    broker.verify(
        broker_env.public_key,
        broker.DOMAIN + _canonical(receipt),
        signature,
    )

    message = _git(broker_env.remote, "log", "-1", "--pretty=%B").decode("utf-8")
    assert f"Ratification-Source-Commit: {broker_env.initial_head}" in message
    assert "Ratification-Serial: 1" in message
    assert f"Ratification-Closure-Digest-SHA256: {_expected_digest(broker_env)}" in message
    assert "AI-Agent:" not in message
    author = _git(broker_env.remote, "log", "-1", "--pretty=%an <%ae>").strip()
    assert author == b"Trusted Operator <operator@example.invalid>"
    assert _git(broker_env.remote, "status", "--porcelain") == b""
    assert f"commit={new_head}" in result.stdout
    verified_rows = receipt_verifier._committed_receipts(
        broker_env.remote, new_head
    )
    assert verified_rows[-1]["closure_digest_sha256"] == _expected_digest(
        broker_env
    )


def test_every_remote_git_call_uses_verifier_hardening(
    broker_env: BrokerEnv,
) -> None:
    result = _run_with_tty(broker_env)
    assert result.returncode == 0, result.stderr
    git_commands = [
        call["argv"][-1]
        for call in _calls(broker_env)
        if call["tool"] == "ssh" and "/usr/bin/git" in call["argv"][-1]
    ]
    assert git_commands
    for command in git_commands:
        assert "/usr/bin/env -i" in command
        assert "GIT_CONFIG_GLOBAL=/dev/null" in command
        assert "GIT_NO_REPLACE_OBJECTS=1" in command
        assert "core.useReplaceRefs=false" in command
        assert "core.commitGraph=false" in command
        assert "core.fsmonitor=false" in command
        assert "--no-replace-objects" in command


def test_private_key_bytes_are_not_written_to_output(broker_env: BrokerEnv) -> None:
    encodings = _private_encodings(broker_env.key)
    result = _run_without_tty(broker_env)
    output = result.stdout.encode("utf-8") + result.stderr.encode("utf-8")
    for label, encoded in encodings.items():
        assert encoded not in output, label


def test_private_key_bytes_are_not_sent_to_children(broker_env: BrokerEnv) -> None:
    encodings = _private_encodings(broker_env.key)
    result = _run_with_tty(broker_env)
    assert result.returncode == 0, result.stderr
    calls = _calls(broker_env)
    assert any(base64.b64decode(call["stdin"]) for call in calls)
    assert {call["tool"] for call in calls} == {"ssh", "openssl"}
    for call in calls:
        surfaces = {
            "stdin": base64.b64decode(call["stdin"]),
            "argv": "\0".join(call["argv"]).encode("utf-8"),
            "environment": "\0".join(
                f"{key}={value}"
                for key, value in sorted(call["environ"].items())
            ).encode("utf-8"),
        }
        for encoding_label, encoded in encodings.items():
            for surface_label, surface in surfaces.items():
                assert encoded not in surface, (
                    call["tool"], encoding_label, surface_label
                )


def test_private_key_bytes_are_not_present_in_remote_tree(broker_env: BrokerEnv) -> None:
    encodings = _private_encodings(broker_env.key)
    result = _run_with_tty(broker_env)
    assert result.returncode == 0, result.stderr
    for path in broker_env.remote.rglob("*"):
        if path.is_file():
            raw = path.read_bytes()
            for label, encoded in encodings.items():
                assert encoded not in raw, (label, path)

    object_history = _git(
        broker_env.remote,
        "cat-file",
        "--batch-all-objects",
        "--batch",
    )
    for label, encoded in encodings.items():
        assert encoded not in object_history, label


def _self_test() -> int:
    result = subprocess.run(
        [sys.executable, RUNNER_FILE, Path(__file__), "-q"],
        stdin=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode


def test_self_running_harness_invokes_repository_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}

    def fake_run(argv: list[Any], **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 23)

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert _self_test() == 23
    assert observed["argv"] == [sys.executable, RUNNER_FILE, Path(__file__), "-q"]
    assert observed["kwargs"]["stdin"] is subprocess.DEVNULL
    assert observed["kwargs"]["check"] is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
