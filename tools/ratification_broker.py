#!/usr/bin/env python3
"""Reference broker for enforcement-source ratification receipts.

This repository copy is a reference implementation.  The operational copy,
including its reviewed Ed25519 verifier dependency, is installed on and run
from a host that AI cannot reach.  Running the repository copy directly as the
operational broker would let any principal able to edit the repository falsify
both the displayed review material and the bytes selected for signing, which
would remove the mechanism's intended distinction.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from contextlib import contextmanager
import difflib
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import IO, Any, Iterator, cast

_INSTALL_ROOT = Path(__file__).resolve().parents[1]
if os.fspath(_INSTALL_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(_INSTALL_ROOT))

from orchestrator.campaign import enforcement_source_ratification_receipt as _receipt_verifier
from orchestrator.campaign.ed25519_verify import Ed25519VerifyError, verify
from orchestrator.campaign.enforcement_source_ratification import (
    _FORBIDDEN_AMBIENT_GIT_ENV,
    _GIT_ENV_ALLOWLIST,
    _GIT_EXECUTABLE,
    _GIT_HARDEN,
)


CLOSURE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/enforcement_source_ratification.py",
    "orchestrator/campaign/ed25519_verify.py",
    "orchestrator/campaign/enforcement_source_ratification_receipt.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
)
SORTED_PATHS = tuple(sorted(CLOSURE_PATHS))
LEDGER_PATH = _receipt_verifier.RECEIPT_LEDGER_RELATIVE_PATH
TRUST_PATH = _receipt_verifier.TRUST_ROOT_RELATIVE_PATH
SCHEMA = _receipt_verifier.RECEIPT_SCHEMA_VERSION
TRUST_SCHEMA = _receipt_verifier._TRUST_ROOT_SCHEMA_VERSION
DOMAIN = _receipt_verifier._DOMAIN_PREFIX
RECEIPT_FIELDS = _receipt_verifier._ROW_KEYS
TRUST_FIELDS = _receipt_verifier._TRUST_ROOT_KEYS
_LOCK_PATH = "orchestrator/campaign/campaign_lock.py"
_HEX40_RE = _receipt_verifier._HEX40_RE


class BrokerError(RuntimeError):
    """The broker cannot safely finish the requested transaction."""


def _canonical(value: object) -> bytes:
    try:
        return _receipt_verifier._canonical_json_bytes(value)
    except _receipt_verifier.EnforcementSourceRatificationReceiptError as exc:
        raise BrokerError("value cannot be represented as canonical JSON") from exc


def _exact_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BrokerError("duplicate JSON key in ratification metadata")
        result[key] = value
    return result


def _load_json(raw: bytes, *, label: str) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=_exact_object)
    except BrokerError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise BrokerError(f"{label} is not valid JSON") from exc


def _run(
    argv: list[str],
    *,
    data: bytes | None = None,
    pass_fds: tuple[int, ...] = (),
) -> subprocess.CompletedProcess[bytes]:
    try:
        if data is None:
            return subprocess.run(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                pass_fds=pass_fds,
            )
        return subprocess.run(
            argv,
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            pass_fds=pass_fds,
        )
    except OSError as exc:
        raise BrokerError(f"cannot execute {Path(argv[0]).name}") from exc


def _openssl(
    executable: str,
    args: list[str],
    *,
    data: bytes | None = None,
    pass_fds: tuple[int, ...] = (),
) -> bytes:
    result = _run([executable, *args], data=data, pass_fds=pass_fds)
    if result.returncode:
        raise BrokerError("openssl operation failed")
    return result.stdout


def _private_key_absent_message(path: Path) -> str:
    return (
        "private key is absent; this broker never creates keys. On a trusted "
        "host and account that AI cannot reach, run:\n"
        "  umask 077\n"
        f"  install -d -m 0700 {shlex.quote(os.fspath(path.parent))}\n"
        f"  openssl genpkey -algorithm ED25519 -out {shlex.quote(os.fspath(path))}"
    )


def _open_private_key(path: Path) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(path, flags)
    except FileNotFoundError as exc:
        raise BrokerError(_private_key_absent_message(path)) from exc
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise BrokerError("private key must be a regular non-symlink file") from exc
        raise BrokerError("cannot open private key") from exc
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise BrokerError("private key must be a regular non-symlink file")
        if metadata.st_uid != os.geteuid():
            raise BrokerError("private key must be owned by the broker user")
        if stat.S_IMODE(metadata.st_mode) & (stat.S_IRGRP | stat.S_IROTH):
            raise BrokerError("private key must not be readable by group or other")
    except BaseException:
        os.close(fd)
        raise
    return fd


def _fd_path(fd: int) -> str:
    return f"/proc/self/fd/{fd}"


def _public_key(executable: str, key_fd: int) -> bytes:
    der = _openssl(
        executable,
        ["pkey", "-in", _fd_path(key_fd), "-pubout", "-outform", "DER"],
        pass_fds=(key_fd,),
    )
    prefix = bytes.fromhex("302a300506032b6570032100")
    if len(der) != len(prefix) + 32 or not der.startswith(prefix):
        raise BrokerError("openssl did not return an Ed25519 public key")
    return der[len(prefix):]


def _sign(executable: str, key_fd: int, message: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="izanagi-ratification-sign-") as raw_dir:
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
            signature = _openssl(
                executable,
                [
                    "pkeyutl",
                    "-sign",
                    "-rawin",
                    "-inkey",
                    _fd_path(key_fd),
                    "-in",
                    os.fspath(message_path),
                ],
                pass_fds=(key_fd,),
            )
        finally:
            message_path.unlink(missing_ok=True)
    if len(signature) != 64:
        raise BrokerError("openssl did not return an Ed25519 signature")
    return signature


def _ssh_result(
    executable: str,
    spec: str,
    command: str,
    *,
    data: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return _run(
        [
            executable,
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            spec,
            command,
        ],
        data=data,
    )


def _ssh(
    executable: str,
    spec: str,
    command: str,
    *,
    data: bytes | None = None,
) -> bytes:
    result = _ssh_result(executable, spec, command, data=data)
    if result.returncode:
        raise BrokerError("ssh operation failed")
    return result.stdout


def _remote_git_environment() -> tuple[str, ...]:
    contaminated = sorted(
        key for key in _FORBIDDEN_AMBIENT_GIT_ENV if key in os.environ
    )
    if contaminated:
        raise BrokerError(
            "ratification git environment has repository/object overrides: "
            f"{contaminated!r}"
        )
    allowed = tuple(
        f"{key}={os.environ[key]}"
        for key in _GIT_ENV_ALLOWLIST
        if key in os.environ
    )
    return (*allowed, "GIT_CONFIG_GLOBAL=/dev/null", "GIT_CONFIG_NOSYSTEM=1",
            "GIT_NO_REPLACE_OBJECTS=1", "GIT_OPTIONAL_LOCKS=0",
            "GIT_TERMINAL_PROMPT=0")


def _git_prefix(repo: str, *, commit: bool = False) -> str:
    if not _GIT_EXECUTABLE.is_absolute():
        raise BrokerError("ratification git executable is not an absolute path")
    extra = (
        ("-c", "core.hooksPath=/dev/null", "-c", "commit.gpgSign=false")
        if commit
        else ()
    )
    return shlex.join([
        "/usr/bin/env",
        "-i",
        *_remote_git_environment(),
        os.fspath(_GIT_EXECUTABLE),
        *_GIT_HARDEN,
        "--no-replace-objects",
        *extra,
        "-C",
        repo,
    ])


def _git_command(repo: str, args: list[str]) -> str:
    return f"{_git_prefix(repo)} {shlex.join(args)}"


def _git(executable: str, spec: str, repo: str, args: list[str]) -> bytes:
    return _ssh(executable, spec, _git_command(repo, args))


def _git_blob(
    executable: str,
    spec: str,
    repo: str,
    commit: str,
    relative: str,
    *,
    missing_ok: bool = False,
) -> bytes | None:
    command = _git_command(repo, ["cat-file", "blob", f"{commit}:{relative}"])
    result = _ssh_result(executable, spec, command)
    if result.returncode == 0:
        return result.stdout
    if missing_ok and result.returncode == 128:
        return None
    raise BrokerError(f"cannot read committed blob {relative}")


def _committed_blob_oid(
    executable: str,
    spec: str,
    repo: str,
    commit: str,
    relative: str,
) -> str:
    raw = _git(
        executable,
        spec,
        repo,
        ["rev-parse", "--verify", f"{commit}:{relative}"],
    ).strip()
    try:
        oid = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise BrokerError("committed ledger blob id is not ASCII") from exc
    if _HEX40_RE.fullmatch(oid) is None:
        raise BrokerError("committed ledger blob id is malformed")
    return oid


def _head(executable: str, spec: str, repo: str) -> str:
    raw = _git(
        executable,
        spec,
        repo,
        ["rev-parse", "--verify", "HEAD^{commit}"],
    ).strip()
    try:
        head = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise BrokerError("remote HEAD is not ASCII") from exc
    if _HEX40_RE.fullmatch(head) is None:
        raise BrokerError(
            "remote HEAD is not a 40-hex SHA-1 commit id; the receipt verifier "
            "does not accept this target object format"
        )
    return head


def _remote_paths(lock_blob: bytes) -> tuple[str, ...]:
    marker = b"CONTRACT_LOADER_RELATIVE_PATHS = (\n"
    if lock_blob.count(marker) != 1:
        raise BrokerError("remote closure path table is not a plain tuple")
    body = lock_blob.split(marker, 1)[1].split(b"\n)", 1)[0]
    try:
        paths = tuple(
            json.loads(line.strip().removesuffix(b","))
            for line in body.splitlines()
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BrokerError("remote closure path table is not a plain tuple") from exc
    return cast(tuple[str, ...], paths)


def _parse_trust_root(raw: bytes) -> bytes:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\n" in raw[:-1]:
        raise BrokerError("committed trust root must be one canonical line with one final LF")
    line = raw[:-1]
    value = _load_json(line, label="committed trust root")
    if (
        type(value) is not dict
        or set(value) != TRUST_FIELDS
        or value.get("schema_version") != TRUST_SCHEMA
        or _canonical(value) != line
        or type(value.get("public_key_ed25519_base64")) is not str
    ):
        raise BrokerError("committed trust root is not canonical trust-root/v1")
    try:
        public_key = base64.b64decode(
            value["public_key_ed25519_base64"],
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise BrokerError("committed trust root public key is not canonical base64") from exc
    if len(public_key) != 32 or base64.b64encode(public_key).decode("ascii") != value[
        "public_key_ed25519_base64"
    ]:
        raise BrokerError("committed trust root does not contain a raw Ed25519 public key")
    return public_key


def _missing_trust_root_message(public_key: bytes) -> str:
    trust_line = _canonical({
        "public_key_ed25519_base64": base64.b64encode(public_key).decode("ascii"),
        "schema_version": TRUST_SCHEMA,
    }).decode("ascii")
    trust_q = shlex.quote(TRUST_PATH)
    ledger_q = shlex.quote(LEDGER_PATH)
    line_q = shlex.quote(trust_line)
    return (
        "committed trust root is absent; this broker never writes the trust root "
        "or creates the ledger. From the repository root on the trusted bootstrap "
        f"account, exclusive-create {TRUST_PATH} with exactly this line and one final LF:\n"
        f"{trust_line}\n"
        f"and exclusive-create {LEDGER_PATH} as a 0-byte file by running:\n"
        f"  (umask 022; set -C; printf '%s\\n' {line_q} > {trust_q})\n"
        f"  (umask 022; set -C; : > {ledger_q})\n"
        "  git add -- " + TRUST_PATH + " " + LEDGER_PATH + "\n"
        "  git commit -m 'Bootstrap enforcement-source ratification trust root'"
    )


def _escape_control_bytes(raw: bytes) -> bytes:
    escaped = bytearray()
    named = {
        0x08: b"\\b",
        0x09: b"\\t",
        0x0A: b"\n",
        0x0C: b"\\f",
        0x0D: b"\\r",
    }
    for byte in raw:
        if byte in named:
            escaped.extend(named[byte])
        elif byte == 0x5C:
            escaped.extend(b"\\\\")
        elif byte < 0x20 or byte >= 0x7F:
            escaped.extend(f"\\x{byte:02x}".encode("ascii"))
        else:
            escaped.append(byte)
    return bytes(escaped)


def _display_lines(raw: bytes) -> list[str]:
    safe = _escape_control_bytes(raw)
    return safe.decode("ascii").splitlines(keepends=True)


def _diff_lines(raw: bytes) -> list[str]:
    lines = _display_lines(raw)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
        lines.append("\\ No LF at end of blob\n")
    return lines


def _show_initial_blob(path: str, blob: bytes) -> None:
    print(f"--- /dev/null\n+++ {path} (current)")
    lines = _display_lines(blob)
    if not lines:
        print("[0 bytes]")
        return
    for line in lines:
        sys.stdout.write("+" + line)
        if not line.endswith("\n"):
            sys.stdout.write("\n\\ No LF at end of blob\n")


def _show_diff(old: dict[str, bytes] | None, new: dict[str, bytes]) -> None:
    if old is None:
        print("no previous receipt; full current closure bytes follow:")
        for path, blob in new.items():
            print(
                f"sha256={hashlib.sha256(blob).hexdigest()} "
                f"bytes={len(blob)} path={path}"
            )
            _show_initial_blob(path, blob)
        return
    changed = False
    for path in CLOSURE_PATHS:
        if old[path] == new[path]:
            continue
        changed = True
        sys.stdout.writelines(difflib.unified_diff(
            _diff_lines(old[path]),
            _diff_lines(new[path]),
            fromfile=f"{path} (previous)",
            tofile=f"{path} (current)",
        ))
    if not changed:
        print("no closure changes since the previous receipt")


def _preflight_error(exc: Exception) -> BrokerError:
    message = str(exc)
    signature_match = re.search(r"signature is invalid: ([0-9]+)\Z", message)
    if signature_match is not None:
        return BrokerError(
            "receipt ledger signature failed at serial "
            f"{signature_match.group(1)}"
        )
    if "ledger is not newline terminated" in message:
        return BrokerError("receipt ledger must end with exactly one LF")
    return BrokerError(f"target receipt verifier preflight failed: {message}")


def _write_private_file(path: Path, raw: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            stream.write(raw)
    finally:
        if fd >= 0:
            os.close(fd)


def _assert_remote_full_history(
    executable: str,
    spec: str,
    repo: str,
) -> None:
    shallow = _git(
        executable, spec, repo, ["rev-parse", "--is-shallow-repository"]
    )
    if shallow != b"false\n":
        raise BrokerError("ratification history requires a non-shallow repository")

    raw_grafts = _git(
        executable, spec, repo, ["rev-parse", "--git-path", "info/grafts"]
    )
    try:
        grafts = raw_grafts.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BrokerError("ratification history cannot use Git grafts") from exc
    if not grafts.endswith("\n") or "\n" in grafts[:-1] or not grafts[:-1]:
        raise BrokerError("ratification history cannot use Git grafts")
    grafts_path = grafts[:-1]
    if not grafts_path.startswith("/"):
        grafts_path = repo.rstrip("/") + "/" + grafts_path
    path_q = shlex.quote(grafts_path)
    result = _ssh_result(
        executable,
        spec,
        f"if test -e {path_q}; then /bin/cat -- {path_q}; fi",
    )
    if result.returncode != 0 or any(
        line and not line.startswith(b"#")
        for line in result.stdout.split(b"\n")
    ):
        raise BrokerError("ratification history cannot use Git grafts")


@contextmanager
def _target_snapshot(
    executable: str,
    spec: str,
    repo: str,
    expected_head: str,
) -> Iterator[Path]:
    _assert_remote_full_history(executable, spec, repo)
    bundle = _git(executable, spec, repo, ["bundle", "create", "-", "HEAD"])
    with tempfile.TemporaryDirectory(prefix="izanagi-ratification-preflight-") as raw_dir:
        private_dir = Path(raw_dir)
        private_dir.chmod(0o700)
        bundle_path = private_dir / "target.bundle"
        mirror = private_dir / "mirror"
        _write_private_file(bundle_path, bundle)
        try:
            _receipt_verifier._require_git(
                private_dir,
                "clone",
                "--quiet",
                "--no-checkout",
                os.fspath(bundle_path),
                os.fspath(mirror),
            )
            observed_head = _receipt_verifier._head_commit(mirror)
        except _receipt_verifier.EnforcementSourceRatificationReceiptError as exc:
            raise _preflight_error(exc) from exc
        if observed_head != expected_head:
            raise BrokerError(
                "remote HEAD changed while the verifier snapshot was being captured"
            )
        yield mirror


def _snapshot_blob(
    root: Path,
    commit: str,
    relative: str,
    *,
    missing_ok: bool = False,
) -> bytes | None:
    try:
        result = _receipt_verifier._git(
            root, "cat-file", "blob", f"{commit}:{relative}"
        )
    except _receipt_verifier.EnforcementSourceRatificationReceiptError as exc:
        raise _preflight_error(exc) from exc
    if result.returncode == 0:
        return result.stdout
    if missing_ok and result.returncode == 128:
        return None
    raise BrokerError(f"cannot read committed blob {relative}")


def _snapshot_blob_oid(root: Path, commit: str, relative: str) -> str:
    try:
        raw = _receipt_verifier._require_git(
            root, "rev-parse", "--verify", f"{commit}:{relative}"
        ).strip()
    except _receipt_verifier.EnforcementSourceRatificationReceiptError as exc:
        raise _preflight_error(exc) from exc
    try:
        oid = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise BrokerError("committed ledger blob id is not ASCII") from exc
    if _HEX40_RE.fullmatch(oid) is None:
        raise BrokerError("committed ledger blob id is malformed")
    return oid


def _preflight_committed_rows(
    root: Path,
    head: str,
) -> tuple[dict[str, object], ...]:
    try:
        return _receipt_verifier._committed_receipts(root, head)
    except _receipt_verifier.EnforcementSourceRatificationReceiptError as exc:
        raise _preflight_error(exc) from exc


def _replace_snapshot_ledger(root: Path, head: str, ledger: bytes) -> str:
    relative = root / LEDGER_PATH
    try:
        _receipt_verifier._require_git(
            root, "checkout", head, "--", LEDGER_PATH
        )
        fd = os.open(relative, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
        try:
            with os.fdopen(fd, "wb") as stream:
                fd = -1
                stream.write(ledger)
        finally:
            if fd >= 0:
                os.close(fd)
        _receipt_verifier._require_git(root, "add", "--", LEDGER_PATH)
        _receipt_verifier._require_git(
            root,
            "-c", "user.name=Ratification Broker Preflight",
            "-c", "user.email=preflight@example.invalid",
            "-c", "core.hooksPath=/dev/null",
            "-c", "commit.gpgSign=false",
            "commit", "--quiet", "--only", "-m",
            "Prospective ratification receipt preflight",
            "--", LEDGER_PATH,
        )
        return _receipt_verifier._head_commit(root)
    except (OSError, _receipt_verifier.EnforcementSourceRatificationReceiptError) as exc:
        raise _preflight_error(exc) from exc


def _preflight_prospective_ledger(
    root: Path,
    head: str,
    ledger: bytes,
    receipt: dict[str, Any],
) -> None:
    prospective_head = _replace_snapshot_ledger(root, head, ledger)
    rows = _preflight_committed_rows(root, prospective_head)
    if not rows or rows[-1] != receipt:
        raise BrokerError(
            "target receipt verifier did not return the prospective final row"
        )


def _approval_stream() -> IO[str]:
    # A TTY prevents accidental piped approval; it is not authentication.
    fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    try:
        raw = io.FileIO(fd, "w+")
    except BaseException:
        os.close(fd)
        raise
    try:
        return io.TextIOWrapper(
            raw,
            encoding="utf-8",
            errors="replace",
            line_buffering=True,
        )
    except BaseException:
        raw.close()
        raise


def _require_approval_tty() -> None:
    """Confirm the approval channel exists without asking for a decision."""
    try:
        stream = _approval_stream()
    except OSError as exc:
        raise BrokerError("cannot open /dev/tty; ratification is not approved") from exc
    stream.close()


def _read_approval() -> None:
    try:
        stream = _approval_stream()
    except OSError as exc:
        raise BrokerError("cannot open /dev/tty; ratification is not approved") from exc
    try:
        stream.write("ratify? [y/N] ")
        stream.flush()
        answer = stream.readline()
    except OSError as exc:
        raise BrokerError("cannot read approval from /dev/tty") from exc
    finally:
        if stream is not sys.stdin:
            stream.close()
    if answer != "y\n":
        raise BrokerError("ratification declined")


def _require_ledger_cas(
    executable: str,
    spec: str,
    repo: str,
    head: str,
    expected_oid: str,
) -> None:
    observed_oid = _committed_blob_oid(executable, spec, repo, head, LEDGER_PATH)
    if observed_oid != expected_oid:
        raise BrokerError("committed ledger changed while ratification was being prepared")


def _transaction_command(
    repo: str,
    *,
    expected_head: str,
    expected_ledger_oid: str,
    commit_message: str,
) -> str:
    relative_q = shlex.quote(LEDGER_PATH)
    ledger_q = shlex.quote(repo.rstrip("/") + "/" + LEDGER_PATH)
    head_q = shlex.quote(expected_head)
    oid_q = shlex.quote(expected_ledger_oid)
    message_q = shlex.quote(commit_message)
    git_prefix = _git_prefix(repo)
    commit_prefix = _git_prefix(repo, commit=True)
    return "\n".join([
        "set -eu",
        "tmp=''",
        "replaced=0",
        "committed=0",
        f"git_dir=$({git_prefix} rev-parse --absolute-git-dir) || exit 79",
        "lock=$git_dir/izanagi-ratification-broker.lock",
        "mkdir -- \"$lock\" || exit 70",
        "cleanup() {",
        "  status=$?",
        "  trap - EXIT HUP INT TERM",
        "  if test \"$replaced\" = 1 && test \"$committed\" = 0; then",
        "    rollback=$git_dir/izanagi-ratification-rollback.tmp",
        f"    {git_prefix} cat-file blob {oid_q} > \"$rollback\" 2>/dev/null || true",
        f"    if test -f \"$rollback\"; then mv -f -- \"$rollback\" {ledger_q}; fi",
        f"    {git_prefix} reset -q HEAD -- {relative_q} >/dev/null 2>&1 || true",
        "  fi",
        "  if test -n \"$tmp\"; then rm -f -- \"$tmp\"; fi",
        "  rmdir -- \"$lock\" >/dev/null 2>&1 || true",
        "  exit \"$status\"",
        "}",
        "trap cleanup EXIT HUP INT TERM",
        f"current_head=$({git_prefix} rev-parse --verify 'HEAD^{{commit}}') || exit 79",
        f"test \"$current_head\" = {head_q} || exit 71",
        f"current_oid=$({git_prefix} rev-parse --verify 'HEAD:{LEDGER_PATH}') || exit 79",
        f"test \"$current_oid\" = {oid_q} || exit 72",
        f"test -f {ledger_q} && test ! -L {ledger_q} || exit 74",
        f"{git_prefix} diff --cached --quiet HEAD -- {relative_q} || exit 73",
        f"{git_prefix} cat-file blob {oid_q} | cmp - {ledger_q} >/dev/null || exit 73",
        f"tmp=$(mktemp {ledger_q}.tmp.XXXXXX) || exit 79",
        "cat > \"$tmp\" || exit 79",
        "chmod 0644 \"$tmp\" || exit 79",
        "python3 -c 'import os,sys; f=os.open(sys.argv[1], os.O_RDONLY); os.fsync(f); os.close(f)' \"$tmp\" || exit 79",
        f"mv -f -- \"$tmp\" {ledger_q} || exit 79",
        "tmp=''",
        "replaced=1",
        f"python3 -c 'import os,sys; f=os.open(os.path.dirname(sys.argv[1]), os.O_RDONLY | os.O_DIRECTORY); os.fsync(f); os.close(f)' {ledger_q} || exit 79",
        f"{git_prefix} add -- {relative_q} || exit 76",
        f"{git_prefix} diff --cached --quiet HEAD -- {relative_q} && exit 76",
        f"staged_oid=$({git_prefix} rev-parse --verify ':{LEDGER_PATH}') || exit 76",
        f"{git_prefix} cat-file blob \"$staged_oid\" | cmp - {ledger_q} >/dev/null || exit 76",
        f"{commit_prefix} commit -q --only -m {message_q} -- {relative_q} || exit 76",
        "committed=1",
        f"new_head=$({git_prefix} rev-parse --verify 'HEAD^{{commit}}') || exit 79",
        f"parent=$({git_prefix} rev-parse --verify 'HEAD^{{commit}}^') || exit 79",
        f"test \"$parent\" = {head_q} || exit 77",
        f"new_oid=$({git_prefix} rev-parse --verify 'HEAD:{LEDGER_PATH}') || exit 79",
        f"{git_prefix} cat-file blob \"$new_oid\" | cmp - {ledger_q} >/dev/null || exit 77",
        "printf '%s\\n%s\\n' \"$new_head\" \"$new_oid\"",
    ])


def _commit_receipt(
    executable: str,
    spec: str,
    repo: str,
    *,
    expected_head: str,
    expected_ledger_oid: str,
    ledger: bytes,
    receipt: dict[str, Any],
) -> str:
    commit_message = "\n".join([
        "Ratify enforcement source closure",
        "",
        f"Ratification-Schema: {SCHEMA}",
        f"Ratification-Source-Commit: {expected_head}",
        f"Ratification-Serial: {receipt['ratification_serial']}",
        f"Ratification-Trust-Root-SHA256: {receipt['trust_root_sha256']}",
        f"Ratification-Closure-Digest-SHA256: {receipt['closure_digest_sha256']}",
    ])
    result = _ssh_result(
        executable,
        spec,
        _transaction_command(
            repo,
            expected_head=expected_head,
            expected_ledger_oid=expected_ledger_oid,
            commit_message=commit_message,
        ),
        data=ledger,
    )
    errors = {
        70: "another ratification transaction holds the remote lock",
        71: "remote HEAD changed while ratification was being prepared",
        72: "committed ledger changed while ratification was being prepared",
        73: "worktree or index ledger differs from the committed ledger",
        74: "worktree ledger is not a regular non-symlink file",
        76: "could not stage and commit the ratification receipt",
        77: "ratification commit did not preserve the expected transaction",
        79: "remote ratification transaction failed",
    }
    if result.returncode:
        raise BrokerError(errors.get(result.returncode, "ssh ratification transaction failed"))
    try:
        new_head, new_oid = result.stdout.decode("ascii").splitlines()
    except (UnicodeDecodeError, ValueError) as exc:
        raise BrokerError("ratification transaction returned malformed provenance") from exc
    if _HEX40_RE.fullmatch(new_head) is None or _HEX40_RE.fullmatch(new_oid) is None:
        raise BrokerError("ratification transaction returned malformed object ids")
    return new_head


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "--key-file",
        type=Path,
        default=Path("~/.config/izanagi/ratification-ed25519.key"),
    )
    return parser


def run(args: argparse.Namespace) -> str:
    ssh = shutil.which("ssh")
    openssl = shutil.which("openssl")
    if not ssh or not openssl:
        raise BrokerError("ssh and an Ed25519-capable openssl are required")
    spec, separator, repo = args.target.rpartition(":")
    if not separator or not spec or not repo.startswith("/") or spec.startswith("-"):
        raise BrokerError("target must be <ssh-spec>:<absolute-repo-path>")

    key = args.key_file.expanduser()
    key_fd = _open_private_key(key)
    try:
        public_key = _public_key(openssl, key_fd)
        fingerprint = hashlib.sha256(public_key).hexdigest()
        head = _head(ssh, spec, repo)

        with _target_snapshot(ssh, spec, repo, head) as snapshot:
            trust_raw = _snapshot_blob(
                snapshot, head, TRUST_PATH, missing_ok=True
            )
            if trust_raw is None:
                raise BrokerError(_missing_trust_root_message(public_key))
            trusted_public_key = _parse_trust_root(trust_raw)
            if trusted_public_key != public_key:
                raise BrokerError("committed trust root differs from this private key")

            ledger = cast(
                bytes, _snapshot_blob(snapshot, head, LEDGER_PATH)
            )
            ledger_oid = _snapshot_blob_oid(snapshot, head, LEDGER_PATH)
            rows = _preflight_committed_rows(snapshot, head)
            latest = rows[-1] if rows else None
            previous_hash = (
                None
                if latest is None
                else hashlib.sha256(_canonical(latest)).hexdigest()
            )

            blobs = {
                path: cast(bytes, _snapshot_blob(snapshot, head, path))
                for path in CLOSURE_PATHS
            }
            remote_paths = _remote_paths(blobs[_LOCK_PATH])
            if remote_paths != CLOSURE_PATHS:
                print("closure path mismatch:", file=sys.stderr)
                for line in difflib.unified_diff(
                    list(remote_paths),
                    list(CLOSURE_PATHS),
                    fromfile="remote",
                    tofile="broker",
                    lineterm="",
                ):
                    print(line, file=sys.stderr)
                raise BrokerError(
                    "remote closure path list differs from broker table"
                )

            blob_hashes = {
                path: hashlib.sha256(blob).hexdigest()
                for path, blob in blobs.items()
            }
            digest = hashlib.sha256(_canonical(blob_hashes)).hexdigest()
            paths_hash = hashlib.sha256(
                _canonical(list(SORTED_PATHS))
            ).hexdigest()
            old = None
            if latest is not None:
                source_commit = cast(str, latest["source_commit"])
                old = {
                    path: cast(
                        bytes,
                        _snapshot_blob(snapshot, source_commit, path),
                    )
                    for path in CLOSURE_PATHS
                }

            _require_approval_tty()
            receipt: dict[str, Any] = {
                "closure_digest_sha256": digest,
                "closure_paths": list(SORTED_PATHS),
                "closure_paths_sha256": paths_hash,
                "decision": "ratify",
                "previous_receipt_sha256": previous_hash,
                "ratification_serial": (
                    1
                    if latest is None
                    else cast(int, latest["ratification_serial"]) + 1
                ),
                "schema_version": SCHEMA,
                "source_commit": head,
                "trust_root_sha256": fingerprint,
            }
            signed_payload = DOMAIN + _canonical(receipt)
            signature = _sign(openssl, key_fd, signed_payload)
            try:
                verify(trusted_public_key, signed_payload, signature)
            except Ed25519VerifyError as exc:
                raise BrokerError(
                    "generated Ed25519 signature failed self-verification"
                ) from exc
            os.close(key_fd)
            key_fd = -1

            receipt["signature_ed25519_base64"] = base64.b64encode(
                signature
            ).decode("ascii")
            next_ledger = ledger + _canonical(receipt) + b"\n"
            _preflight_prospective_ledger(
                snapshot, head, next_ledger, receipt
            )
            _show_diff(old, blobs)
    finally:
        if key_fd >= 0:
            os.close(key_fd)

    _read_approval()

    if _head(ssh, spec, repo) != head:
        raise BrokerError("remote HEAD changed while ratification was being prepared")
    _require_ledger_cas(ssh, spec, repo, head, ledger_oid)
    committed_head = _commit_receipt(
        ssh,
        spec,
        repo,
        expected_head=head,
        expected_ledger_oid=ledger_oid,
        ledger=next_ledger,
        receipt=receipt,
    )
    return (
        f"trust_root_sha256={fingerprint} serial={receipt['ratification_serial']} "
        f"closure_digest_sha256={digest} commit={committed_head}"
    )


def main() -> int:
    try:
        print(run(_parser().parse_args()))
        return 0
    except BrokerError as exc:
        print(f"ratification broker: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
