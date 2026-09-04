#!/usr/bin/env python3
"""Reviewed reference issuer for repository-external deployment.

This module is not called by the production waiter or lander.  An operational
copy is expected to live with its key material outside the repository.  This
repository copy executes the caller-selected ``tested_main`` launcher blob and
performs only the comparisons listed below before signing the v5 result.

Claims bound to caller input:

| Receipt field/evidence | Binding performed by this issuer |
| --- | --- |
| ``acceptance_wave`` | exact equality with caller input |
| ``tested_main`` / ``tested_tip`` | caller-bound and Git-existing; no independent selection |
| ``lease_generation`` | caller-supplied identifier for one acquisition, or ``"not-acquired"`` when none was acquired; neither is independently derived from or checked against a live lease |

Expectations independently derived or read by this issuer:

| Receipt field/evidence | Expectation and limitation |
| --- | --- |
| ``lease_holder`` | derived from caller-bound ``acceptance_wave`` |
| launcher blob id and executed SHA-256 | from main launcher bytes executed by this copy |
| waiter blob id and executed SHA-256 | expected from tip waiter blob; process not observed |
| runner executed SHA-256 | expected from the main runner blob; process bytes are not observed |
| checker blob/content SHA-256 | expected from tip checker blob; process not observed |
| ``log_sha256`` | hash of the caller-selected regular file; authorship is not proved |

Claims not independently derived by this issuer:

| Receipt field/evidence | Remaining limitation |
| --- | --- |
| ``argv`` / ``resolved_runner_path`` / ``child_rc`` | preserved launcher/waiter claims |
| ``pre_fingerprint`` / ``post_fingerprint`` | waiter claims preserved for signing |
| ``env_projection`` / ``effective_scheduler`` | waiter claims preserved for signing |
| checker result fields | consistency-constrained claims; the checker is not rerun here |
| ``red_nodeids`` / ``flake_nodeids`` | waiter checker-result claims preserved for signing |

Signing therefore records approval by the configured key and prevents later
field modification.  It does not turn the remaining self-reports into
independently established facts, and it does not prove that this particular
reference program was the process that used the key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Mapping, Sequence

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError as exc:  # pragma: no cover - absence must stop issuance
    raise RuntimeError(
        "cryptography with Ed25519 support is required for receipt issuance"
    ) from exc

try:
    from tools.acceptance_receipt_signature import (
        ReceiptSignatureError,
        _require_lease_generation,
        attach_signature,
        canonical_json_bytes,
        canonical_signed_payload_bytes,
        load_configured_public_key,
        project_v5_receipt,
        public_key_id,
        verify_signed_receipt_signature,
    )
except ModuleNotFoundError:  # external colocated copies may not have a tools package
    from acceptance_receipt_signature import (  # type: ignore[no-redef]
        ReceiptSignatureError,
        _require_lease_generation,
        attach_signature,
        canonical_json_bytes,
        canonical_signed_payload_bytes,
        load_configured_public_key,
        project_v5_receipt,
        public_key_id,
        verify_signed_receipt_signature,
    )


PRIVATE_KEY_PATH = Path(
    "/work/1/SFC/tanab/dev-wave-authority/acceptance-issuer-private-key.pem"
)

_LAUNCHER_PATH = "tools/acceptance_launcher.py"
_WAITER_PATH = "tools/dev_wave_wait.py"
_RUNNER_PATH = "tools/run_tests.py"
_CHECKER_PATH = "tools/check_acceptance_reds.py"
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_MAX_RECEIPT_BYTES = 64 * 1024
_MAX_PRIVATE_KEY_BYTES = 16 * 1024
_GIT_EXE = "/usr/bin/git"
_GIT_CONFIG = (
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "credential.helper=",
)
_GIT_ENV_OVERRIDES = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_ATTR_NOSYSTEM": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_NO_LAZY_FETCH": "1",
    "LC_ALL": "C",
}

_LAUNCHER_BOOTSTRAP = (
    "import sys\n"
    "source = sys.stdin.buffer.read()\n"
    "namespace = {\n"
    "    '__name__': '_izanagi_external_acceptance_launcher',\n"
    "    '__file__': sys.argv[1],\n"
    "}\n"
    "exec(compile(source, namespace['__file__'], 'exec'), namespace)\n"
    "raise SystemExit(namespace['main'](sys.argv[2:]))\n"
)


class IssuerFailure(Exception):
    """A fail-closed reference-issuer error."""


def _git_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(_GIT_ENV_OVERRIDES)
    return environment


def _git(repo: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            (_GIT_EXE, *_GIT_CONFIG, "-C", str(repo), *args),
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_environment(),
        )
    except OSError as exc:
        raise IssuerFailure("cannot execute Git") from exc
    if result.returncode != 0:
        raise IssuerFailure("Git object verification failed")
    return result.stdout


def _require_sha1(value: str, label: str) -> None:
    if _SHA1_RE.fullmatch(value) is None:
        raise IssuerFailure(f"invalid {label}")


def _verify_commit(repo: Path, revision: str, label: str) -> None:
    _require_sha1(revision, label)
    resolved = _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    try:
        observed = resolved.decode("ascii").strip()
    except UnicodeError as exc:
        raise IssuerFailure(f"invalid {label} object id") from exc
    if observed != revision:
        raise IssuerFailure(f"{label} does not resolve exactly")


def _blob(repo: Path, revision: str, path: str) -> tuple[str, bytes]:
    object_id_raw = _git(repo, "rev-parse", "--verify", f"{revision}:{path}")
    try:
        object_id = object_id_raw.decode("ascii").strip()
    except UnicodeError as exc:
        raise IssuerFailure("Git blob id is not ASCII") from exc
    if _SHA_RE.fullmatch(object_id) is None:
        raise IssuerFailure("Git path did not resolve to a full blob id")
    object_type = _git(repo, "cat-file", "-t", object_id)
    if object_type != b"blob\n":
        raise IssuerFailure("Git path is not a blob")
    return object_id, _git(repo, "cat-file", "blob", object_id)


def _option_value(argv: Sequence[str], option: str) -> str:
    values: list[str] = []
    index = 0
    while index < len(argv):
        value = argv[index]
        if value == "--":
            break
        if value == option:
            if index + 1 >= len(argv):
                raise IssuerFailure(f"launcher option {option} has no value")
            values.append(argv[index + 1])
            index += 2
            continue
        if value.startswith(option + "="):
            values.append(value.split("=", 1)[1])
        index += 1
    if len(values) != 1:
        raise IssuerFailure(f"launcher option {option} must occur exactly once")
    return values[0]


def _validate_launcher_request(
    launcher_argv: Sequence[str],
    *,
    repo_root: Path,
    acceptance_wave: str,
    tested_main: str,
    tested_tip: str,
    log_file: Path,
    launcher_blob_sha: str,
    launcher_content_sha256: str,
) -> None:
    if any(
        value == "--receipt-file" or value.startswith("--receipt-file=")
        for value in launcher_argv
    ):
        raise IssuerFailure("the issuer owns the launcher receipt path")
    expected = {
        "--repo-root": str(repo_root),
        "--wave": acceptance_wave,
        "--tested-main": tested_main,
        "--tested-tip": tested_tip,
        "--launcher-source-revision": "tested-main",
        "--launcher-blob-sha": launcher_blob_sha,
        "--launcher-executed-sha256": launcher_content_sha256,
        "--log-file": str(log_file),
    }
    for option, value in expected.items():
        if _option_value(launcher_argv, option) != value:
            raise IssuerFailure(f"launcher option {option} is not issuer-bound")


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _parse_v5_receipt(raw: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicate_keys,
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise IssuerFailure("launcher receipt is not valid JSON") from exc
    if not isinstance(value, dict):
        raise IssuerFailure("launcher receipt is not an object")
    try:
        if canonical_json_bytes(value) != raw:
            raise IssuerFailure("launcher receipt is not canonical JSON")
    except ReceiptSignatureError as exc:
        raise IssuerFailure("launcher receipt is not canonicalizable") from exc
    return value


def _execute_tested_main_launcher(
    repo_root: Path,
    launcher_source: bytes,
    launcher_argv: Sequence[str],
    *,
    receipt_path: Path,
    pass_fds: Sequence[int],
) -> dict[str, object]:
    receipt_path.touch(mode=0o600, exist_ok=False)
    command_argv = (
        "--receipt-file",
        str(receipt_path),
        *launcher_argv,
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            (
                sys.executable,
                "-B",
                "-I",
                "-c",
                _LAUNCHER_BOOTSTRAP,
                str(repo_root / _LAUNCHER_PATH),
                *command_argv,
            ),
            check=False,
            input=launcher_source,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=repo_root,
            env=environment,
            pass_fds=tuple(pass_fds),
        )
    except OSError as exc:
        raise IssuerFailure("cannot execute tested-main launcher blob") from exc
    if completed.returncode != 0:
        raise IssuerFailure("tested-main launcher rejected the acceptance run")
    try:
        raw = receipt_path.read_bytes()
    except OSError as exc:
        raise IssuerFailure("cannot read tested-main launcher receipt") from exc
    if not raw or len(raw) > _MAX_RECEIPT_BYTES:
        raise IssuerFailure("tested-main launcher receipt size is invalid")
    return _parse_v5_receipt(raw)


def _read_log_hash(path: Path) -> str:
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise IssuerFailure("launcher log is not a regular file")
        raw = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise IssuerFailure("cannot read launcher log") from exc
    if (before.st_dev, before.st_ino, before.st_size) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
    ):
        raise IssuerFailure("launcher log changed while hashing")
    return hashlib.sha256(raw).hexdigest()


def _compare_issuer_derived_expectations(
    repo_root: Path,
    receipt: Mapping[str, object],
    *,
    acceptance_wave: str,
    tested_main: str,
    tested_tip: str,
    log_file: Path,
) -> str:
    """Compare the documented Git/log expectations and return checker hash."""

    if (
        receipt.get("acceptance_wave") != acceptance_wave
        or receipt.get("tested_main") != tested_main
        or receipt.get("tested_tip") != tested_tip
    ):
        raise IssuerFailure("launcher receipt context mismatch")
    expected_holder = hashlib.sha256(
        acceptance_wave.encode("utf-8")
    ).hexdigest()[:12]
    if receipt.get("lease_holder") != expected_holder:
        raise IssuerFailure("launcher receipt lease holder mismatch")

    launcher_id, launcher = _blob(repo_root, tested_main, _LAUNCHER_PATH)
    waiter_id, waiter = _blob(repo_root, tested_tip, _WAITER_PATH)
    _runner_id, runner = _blob(repo_root, tested_main, _RUNNER_PATH)
    checker_id, checker = _blob(repo_root, tested_tip, _CHECKER_PATH)
    launcher_sha256 = hashlib.sha256(launcher).hexdigest()
    waiter_sha256 = hashlib.sha256(waiter).hexdigest()
    runner_sha256 = hashlib.sha256(runner).hexdigest()
    checker_sha256 = hashlib.sha256(checker).hexdigest()
    if (
        receipt.get("launcher_source_revision") != "tested-main"
        or receipt.get("launcher_blob_sha") != launcher_id
        or receipt.get("launcher_executed_sha256") != launcher_sha256
        or receipt.get("waiter_blob_sha") != waiter_id
        or receipt.get("waiter_executed_sha256") != waiter_sha256
        or receipt.get("runner_executed_sha256") != runner_sha256
        or receipt.get("log_sha256") != _read_log_hash(log_file)
    ):
        raise IssuerFailure("launcher receipt issuer-derived expectation mismatch")

    verdict = receipt.get("verdict")
    checker_blob_claim = receipt.get("checker_blob_sha")
    if verdict == "child-green":
        if checker_blob_claim is not None:
            raise IssuerFailure(
                "child-green receipt unexpectedly claims checker execution"
            )
    elif verdict == "non-attributable-only":
        main_checker_id, main_checker = _blob(repo_root, tested_main, _CHECKER_PATH)
        if (
            main_checker_id != checker_id
            or main_checker != checker
            or checker_blob_claim != checker_id
        ):
            raise IssuerFailure("checker blob differs across the signed context")
    else:
        raise IssuerFailure("launcher receipt verdict is not receiptable")
    return checker_sha256


def _read_private_key() -> Ed25519PrivateKey:
    path = PRIVATE_KEY_PATH
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        before = path.lstat()
        fd = os.open(path, flags)
    except OSError as exc:
        raise IssuerFailure("issuer private key is unavailable") from exc
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
            or opened.st_size <= 0
            or opened.st_size > _MAX_PRIVATE_KEY_BYTES
            or opened.st_uid != os.getuid()
            or opened.st_nlink != 1
            or opened.st_mode & 0o077
        ):
            raise IssuerFailure("issuer private key file is invalid")
        raw = os.read(fd, _MAX_PRIVATE_KEY_BYTES + 1)
        if len(raw) > _MAX_PRIVATE_KEY_BYTES or os.read(fd, 1):
            raise IssuerFailure("issuer private key file is too large")
    except OSError as exc:
        raise IssuerFailure("issuer private key is unreadable") from exc
    finally:
        os.close(fd)
    try:
        key = serialization.load_pem_private_key(raw, password=None)
    except (TypeError, ValueError) as exc:
        raise IssuerFailure("issuer private key format is invalid") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise IssuerFailure("issuer private key is not Ed25519")
    return key


def issue_signed_receipt(
    *,
    repo_root: Path,
    acceptance_wave: str,
    tested_main: str,
    tested_tip: str,
    lease_generation: str,
    log_file: Path,
    launcher_argv: Sequence[str],
    pass_fds: Sequence[int] = (),
) -> bytes:
    """Execute the launcher, compare documented expectations, and sign v6.

    Caller-bound values and claims not independently derived here retain the
    provenance and limitations listed in the module documentation.
    """

    try:
        canonical_repo = repo_root.resolve(strict=True)
    except OSError as exc:
        raise IssuerFailure("repository root is unavailable") from exc
    if canonical_repo != repo_root or not canonical_repo.is_dir():
        raise IssuerFailure("repository root must be canonical and absolute")
    _verify_commit(canonical_repo, tested_main, "tested_main")
    _verify_commit(canonical_repo, tested_tip, "tested_tip")
    if not isinstance(acceptance_wave, str) or not acceptance_wave:
        raise IssuerFailure("invalid acceptance_wave")
    try:
        _require_lease_generation(lease_generation, "lease_generation")
    except ReceiptSignatureError as exc:
        raise IssuerFailure(str(exc)) from exc
    if not log_file.is_absolute():
        raise IssuerFailure("launcher log path must be absolute")

    launcher_id, launcher_source = _blob(canonical_repo, tested_main, _LAUNCHER_PATH)
    launcher_sha256 = hashlib.sha256(launcher_source).hexdigest()
    _validate_launcher_request(
        launcher_argv,
        repo_root=canonical_repo,
        acceptance_wave=acceptance_wave,
        tested_main=tested_main,
        tested_tip=tested_tip,
        log_file=log_file,
        launcher_blob_sha=launcher_id,
        launcher_content_sha256=launcher_sha256,
    )

    with tempfile.TemporaryDirectory(
        prefix="izanagi-acceptance-issuer-",
        dir="/tmp",
    ) as raw:
        receipt_path = Path(raw) / "launcher-v5.json"
        receipt = _execute_tested_main_launcher(
            canonical_repo,
            launcher_source,
            launcher_argv,
            receipt_path=receipt_path,
            pass_fds=pass_fds,
        )
    checker_content_sha256 = _compare_issuer_derived_expectations(
        canonical_repo,
        receipt,
        acceptance_wave=acceptance_wave,
        tested_main=tested_main,
        tested_tip=tested_tip,
        log_file=log_file,
    )

    private_key = _read_private_key()
    try:
        configured_key = load_configured_public_key()
        derived_key_id = public_key_id(private_key.public_key())
    except ReceiptSignatureError as exc:
        raise IssuerFailure("configured public-key verification failed") from exc
    if derived_key_id != configured_key.key_id:
        raise IssuerFailure(
            "issuer private key does not match the fixed configured public key"
        )
    try:
        payload = project_v5_receipt(
            receipt,
            lease_generation=lease_generation,
            checker_content_sha256=checker_content_sha256,
            issuer_key_id=derived_key_id,
        )
        signature = private_key.sign(canonical_signed_payload_bytes(payload))
        signed = attach_signature(payload, signature)
        verify_signed_receipt_signature(
            signed,
            configured_key,
            expected_acceptance_wave=acceptance_wave,
            expected_tested_main=tested_main,
            expected_tested_tip=tested_tip,
            expected_lease_generation=lease_generation,
        )
        return canonical_json_bytes(signed)
    except ReceiptSignatureError as exc:
        raise IssuerFailure("signed-v6 receipt construction failed") from exc
    except Exception as exc:
        raise IssuerFailure("Ed25519 receipt signing failed") from exc


def _write_new(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise IssuerFailure("cannot persist signed receipt") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="reference external acceptance issuer")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--acceptance-wave", required=True)
    parser.add_argument("--tested-main", required=True)
    parser.add_argument("--tested-tip", required=True)
    parser.add_argument("--lease-generation", required=True)
    parser.add_argument("--log-file", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--pass-fd", action="append", default=[], type=int)
    parser.add_argument("launcher_argv", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    launcher_argv = tuple(args.launcher_argv)
    if launcher_argv[:1] == ("--",):
        launcher_argv = launcher_argv[1:]
    try:
        payload = issue_signed_receipt(
            repo_root=args.repo_root,
            acceptance_wave=args.acceptance_wave,
            tested_main=args.tested_main,
            tested_tip=args.tested_tip,
            lease_generation=args.lease_generation,
            log_file=args.log_file,
            launcher_argv=launcher_argv,
            pass_fds=tuple(args.pass_fd),
        )
        _write_new(args.output, payload)
    except IssuerFailure as exc:
        print(f"acceptance issuer: {exc}", file=sys.stderr, flush=True)
        return 70
    return 0


if __name__ == "__main__":
    sys.exit(main())
