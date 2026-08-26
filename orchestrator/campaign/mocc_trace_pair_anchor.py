#!/usr/bin/env python3
"""Independently anchor a Mocc TRACE pair receipt to caller-held source pins."""
from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import contract_loader_binding  # noqa: E402


ANCHOR_SCHEMA = "mocc-trace-pair-anchor/v1"
EXTERNAL_PIN_SCHEMA = "mocc-trace-pair-external-pin/v1"
PAIR_V2_SCHEMA = "mocc-trace-pair-receipt/v2"
PAIR_V3_SCHEMA = "mocc-trace-pair-receipt/v3"
CHECKER_REPO_PATH = "orchestrator/campaign/mocc_trace_pair.py"
_ED25519_PUBLIC_KEY_DER_PREFIX = bytes.fromhex("302a300506032b6570032100")
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_GIT_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


class AnchorValidationError(ValueError):
    """A pair receipt cannot be independently anchored."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise AnchorValidationError(message)


@dataclass(frozen=True)
class InputDocument:
    path: Path
    raw: bytes
    sha256: str
    value: dict[str, Any]


@dataclass(frozen=True)
class GitBlobBinding:
    commit: str
    path: str
    oid: str
    sha256: str


@dataclass(frozen=True)
class ExternalPinEvidence:
    manifest: InputDocument
    signature_path: Path
    signature_sha256: str
    public_key_path: Path
    public_key_sha256: str


def _reject(message: str) -> None:
    raise AnchorValidationError(message)


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _reject(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    _reject(f"non-finite JSON number is forbidden: {value}")


def _read_json(path_text: str, label: str) -> InputDocument:
    path = Path(path_text)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise AnchorValidationError(f"{label} is unavailable: {path}") from exc
    try:
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            _reject(f"{label} is not a regular file: {path}")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read()
    finally:
        if fd >= 0:
            os.close(fd)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_pairs,
            parse_constant=_reject_constant,
        )
    except UnicodeDecodeError as exc:
        raise AnchorValidationError(f"{label} is not UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise AnchorValidationError(f"{label} is not strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        _reject(f"{label} top level is not an object")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise AnchorValidationError(f"{label} path cannot be resolved") from exc
    return InputDocument(
        path=resolved,
        raw=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        value=value,
    )


def _read_bytes(path_text: str, label: str) -> tuple[Path, bytes]:
    path = Path(path_text)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise AnchorValidationError(f"{label} is unavailable: {path}") from exc
    try:
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            _reject(f"{label} is not a regular file: {path}")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read()
    finally:
        if fd >= 0:
            os.close(fd)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise AnchorValidationError(f"{label} path cannot be resolved") from exc
    return resolved, raw


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _reject(f"{label} is not an object")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        _reject(f"{label} is not a nonempty string")
    return value


def _oid(value: Any, label: str) -> str:
    value = _string(value, label)
    if _HEX40.fullmatch(value) is None:
        _reject(f"{label} is not a full lowercase commit OID")
    return value


def _sha256(value: Any, label: str) -> str:
    value = _string(value, label)
    if _HEX64.fullmatch(value) is None:
        _reject(f"{label} is not a lowercase SHA-256")
    return value


def _true(value: Any, label: str) -> None:
    if type(value) is not bool or value is not True:
        _reject(f"{label} is not strict true")


def _git_bytes(repo_root: Path, arguments: Sequence[str], label: str) -> bytes:
    try:
        return contract_loader_binding._run_git(repo_root, *arguments)
    except contract_loader_binding.ContractLoaderBindingError as exc:
        raise AnchorValidationError(f"{label} failed") from exc


def _repository_root() -> Path:
    anchor_path = Path(__file__).resolve(strict=True)
    root_bytes = _git_bytes(
        anchor_path.parent,
        ["rev-parse", "--show-toplevel"],
        "anchor repository root lookup",
    )
    try:
        return Path(root_bytes.decode("utf-8").strip()).resolve(strict=True)
    except (UnicodeDecodeError, OSError) as exc:
        raise AnchorValidationError("anchor repository root is invalid") from exc


def _repository_internal_roots(repo_root: Path) -> tuple[Path, ...]:
    common_dir_bytes = _git_bytes(
        repo_root,
        ["rev-parse", "--git-common-dir"],
        "anchor Git common directory lookup",
    )
    try:
        common_dir_text = common_dir_bytes.decode("utf-8").strip()
        common_dir = Path(common_dir_text)
        if not common_dir.is_absolute():
            common_dir = repo_root / common_dir
        common_dir = common_dir.resolve(strict=True)
    except (UnicodeDecodeError, OSError) as exc:
        raise AnchorValidationError(
            "anchor Git common directory is invalid"
        ) from exc
    return tuple(dict.fromkeys((repo_root, common_dir)))


def _git_blob_binding(
    repo_root: Path,
    commit: str,
    expected_sha256: str,
    *,
    label: str,
) -> GitBlobBinding:
    commit = _oid(commit, f"{label} commit")
    expected_sha256 = _sha256(expected_sha256, f"{label} SHA-256")
    object_type = _git_bytes(
        repo_root,
        ["cat-file", "-t", commit],
        f"{label} commit lookup",
    ).decode("ascii", errors="replace").strip()
    if object_type != "commit":
        _reject(f"{label} commit pin does not name a commit")
    blob_oid = _git_bytes(
        repo_root,
        ["rev-parse", f"{commit}:{CHECKER_REPO_PATH}"],
        f"{label} checker blob lookup",
    ).decode("ascii", errors="replace").strip()
    if _GIT_OID.fullmatch(blob_oid) is None:
        _reject(f"{label} checker blob OID is invalid")
    blob_bytes = _git_bytes(
        repo_root,
        ["cat-file", "blob", blob_oid],
        f"{label} checker blob read",
    )
    blob_sha256 = hashlib.sha256(blob_bytes).hexdigest()
    if blob_sha256 != expected_sha256:
        _reject(f"{label} checker blob SHA-256 differs")
    return GitBlobBinding(
        commit=commit,
        path=CHECKER_REPO_PATH,
        oid=blob_oid,
        sha256=blob_sha256,
    )


def _require_outside_repository(
    path: Path,
    repository_roots: tuple[Path, ...],
    label: str,
) -> None:
    for root in repository_roots:
        try:
            path.relative_to(root)
        except ValueError:
            continue
        _reject(f"{label} must be held outside the Git repository")


def _validate_ed25519_public_key(raw: bytes) -> None:
    header = b"-----BEGIN PUBLIC KEY-----"
    footer = b"-----END PUBLIC KEY-----"
    lines = raw.strip().splitlines()
    if len(lines) < 3 or lines[0] != header or lines[-1] != footer:
        _reject("external pin public key is not a PEM public key")
    try:
        der = base64.b64decode(b"".join(lines[1:-1]), validate=True)
    except (ValueError, TypeError) as exc:
        raise AnchorValidationError(
            "external pin public key PEM body is invalid"
        ) from exc
    if (
        len(der) != len(_ED25519_PUBLIC_KEY_DER_PREFIX) + 32
        or not der.startswith(_ED25519_PUBLIC_KEY_DER_PREFIX)
    ):
        _reject("external pin public key is not Ed25519")


def _verify_ed25519_signature(
    manifest_raw: bytes,
    signature_raw: bytes,
    public_key_raw: bytes,
) -> None:
    if len(signature_raw) != 64:
        _reject("external pin Ed25519 signature length differs")
    _validate_ed25519_public_key(public_key_raw)
    openssl = shutil.which("openssl", path=os.defpath)
    if openssl is None:
        _reject("OpenSSL is unavailable for external pin signature verification")
    try:
        with tempfile.TemporaryDirectory(prefix="mocc-trace-anchor-") as temp_text:
            temp_root = Path(temp_text)
            manifest_path = temp_root / "manifest.json"
            signature_path = temp_root / "manifest.sig"
            public_key_path = temp_root / "public-key.pem"
            manifest_path.write_bytes(manifest_raw)
            signature_path.write_bytes(signature_raw)
            public_key_path.write_bytes(public_key_raw)
            completed = subprocess.run(
                [
                    openssl,
                    "pkeyutl",
                    "-verify",
                    "-pubin",
                    "-inkey",
                    str(public_key_path),
                    "-rawin",
                    "-in",
                    str(manifest_path),
                    "-sigfile",
                    str(signature_path),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                env={"LANG": "C", "LC_ALL": "C", "PATH": os.defpath},
                check=False,
                timeout=10,
            )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AnchorValidationError(
            "external pin signature verification could not run"
        ) from exc
    if completed.returncode != 0:
        _reject("external pin signature verification failed")


def _validate_external_pin(
    *,
    manifest_path: str,
    signature_path: str,
    public_key_path: str,
    document: InputDocument,
    binding: GitBlobBinding,
    repo_root: Path,
) -> ExternalPinEvidence:
    manifest = _read_json(manifest_path, "external pin manifest")
    resolved_signature, signature_raw = _read_bytes(
        signature_path, "external pin signature"
    )
    resolved_public_key, public_key_raw = _read_bytes(
        public_key_path, "external pin public key"
    )
    repository_roots = _repository_internal_roots(repo_root)
    for path, label in (
        (manifest.path, "external pin manifest"),
        (resolved_signature, "external pin signature"),
        (resolved_public_key, "external pin public key"),
    ):
        _require_outside_repository(path, repository_roots, label)

    value = manifest.value
    if set(value) != {"schema_version", "pair_receipt", "checker_source"}:
        _reject("external pin manifest fields differ")
    if value.get("schema_version") != EXTERNAL_PIN_SCHEMA:
        _reject("external pin manifest schema differs")
    pair_receipt = _dict(
        value.get("pair_receipt"), "external pin manifest pair receipt"
    )
    if set(pair_receipt) != {"schema_version", "sha256"}:
        _reject("external pin manifest pair receipt fields differ")
    if pair_receipt.get("schema_version") != PAIR_V3_SCHEMA:
        _reject("external pin manifest does not pin a v3 pair receipt")
    if pair_receipt.get("sha256") != document.sha256:
        _reject("external pin manifest pair receipt SHA-256 differs")
    checker_source = _dict(
        value.get("checker_source"), "external pin manifest checker source"
    )
    if set(checker_source) != {
        "expected_checker_commit",
        "expected_checker_sha256",
        "git_blob_path",
    }:
        _reject("external pin manifest checker source fields differ")
    if checker_source.get("expected_checker_commit") != binding.commit:
        _reject("external pin manifest checker commit differs")
    if checker_source.get("expected_checker_sha256") != binding.sha256:
        _reject("external pin manifest checker SHA-256 differs")
    if checker_source.get("git_blob_path") != binding.path:
        _reject("external pin manifest checker path differs")

    _verify_ed25519_signature(manifest.raw, signature_raw, public_key_raw)
    return ExternalPinEvidence(
        manifest=manifest,
        signature_path=resolved_signature,
        signature_sha256=hashlib.sha256(signature_raw).hexdigest(),
        public_key_path=resolved_public_key,
        public_key_sha256=hashlib.sha256(public_key_raw).hexdigest(),
    )


def _validate_v2(
    document: InputDocument,
    repo_root: Path,
) -> tuple[str, GitBlobBinding]:
    pair_receipt = document.value
    if pair_receipt.get("status") != "accepted":
        _reject("legacy v2 pair receipt is not accepted")
    checker = _dict(pair_receipt.get("checker"), "legacy v2 checker")
    if set(checker) != {
        "path",
        "sha256",
        "self_reported_not_external_trust_anchor",
    }:
        _reject("legacy v2 checker fields differ")
    if checker.get("path") != CHECKER_REPO_PATH:
        _reject("legacy v2 checker path differs")
    checker_sha256 = _sha256(checker.get("sha256"), "legacy v2 checker SHA-256")
    _true(
        checker.get("self_reported_not_external_trust_anchor"),
        "legacy v2 checker trust disclaimer",
    )
    outer_commit = _oid(
        _dict(pair_receipt.get("identity"), "legacy v2 identity").get(
            "outer_repo_commit"
        ),
        "legacy v2 outer repository commit",
    )
    internal_binding = _git_blob_binding(
        repo_root,
        outer_commit,
        checker_sha256,
        label="legacy v2 internal consistency",
    )
    return checker_sha256, internal_binding


def _validate_v3(
    document: InputDocument,
    repo_root: Path,
    expected_checker_commit: str,
    expected_checker_sha256: str,
) -> GitBlobBinding:
    pair_receipt = document.value
    if pair_receipt.get("status") != "accepted":
        _reject("v3 pair receipt is not accepted")
    checker = _dict(pair_receipt.get("checker"), "v3 checker")
    if set(checker) != {"generator", "source_binding"}:
        _reject("v3 checker fields differ")
    generator = _dict(checker.get("generator"), "v3 checker generator")
    if set(generator) != {
        "path",
        "sha256",
        "self_reported_not_external_trust_anchor",
    }:
        _reject("v3 checker generator fields differ")
    if generator.get("path") != CHECKER_REPO_PATH:
        _reject("v3 checker generator path differs")
    generator_sha256 = _sha256(
        generator.get("sha256"), "v3 checker generator SHA-256"
    )
    _true(
        generator.get("self_reported_not_external_trust_anchor"),
        "v3 checker generator trust disclaimer",
    )
    source_binding = _dict(checker.get("source_binding"), "v3 checker source binding")
    if set(source_binding) != {
        "expected_checker_commit",
        "expected_checker_sha256",
        "git_blob_path",
        "git_blob_oid",
        "git_blob_sha256",
        "live_checker_sha256",
        "expected_sha256_matches_git_blob",
        "live_checker_sha256_matches_git_blob",
    }:
        _reject("v3 checker source binding fields differ")
    if source_binding.get("expected_checker_commit") != expected_checker_commit:
        _reject("v3 checker commit differs from caller pin")
    if source_binding.get("expected_checker_sha256") != expected_checker_sha256:
        _reject("v3 checker SHA-256 differs from caller pin")
    if source_binding.get("git_blob_path") != CHECKER_REPO_PATH:
        _reject("v3 checker Git blob path differs")
    _true(
        source_binding.get("expected_sha256_matches_git_blob"),
        "v3 expected SHA matches Git blob",
    )
    _true(
        source_binding.get("live_checker_sha256_matches_git_blob"),
        "v3 live checker matches Git blob",
    )
    caller_binding = _git_blob_binding(
        repo_root,
        expected_checker_commit,
        expected_checker_sha256,
        label="caller-pinned",
    )
    if source_binding.get("git_blob_oid") != caller_binding.oid:
        _reject("v3 checker Git blob OID differs")
    if source_binding.get("git_blob_sha256") != caller_binding.sha256:
        _reject("v3 checker Git blob SHA-256 differs")
    if source_binding.get("live_checker_sha256") != caller_binding.sha256:
        _reject("v3 live checker SHA-256 differs from caller-pinned blob")
    if generator_sha256 != caller_binding.sha256:
        _reject("v3 checker generator SHA-256 differs from caller-pinned blob")
    return caller_binding


def _anchor_payload(
    document: InputDocument,
    pair_schema: str,
    binding: GitBlobBinding,
    external_pin: ExternalPinEvidence,
) -> dict[str, Any]:
    return {
        "schema_version": ANCHOR_SCHEMA,
        "status": "externally_anchored",
        "pair_receipt": {
            "path": str(document.path),
            "schema_version": pair_schema,
            "sha256": document.sha256,
        },
        "checker_source": {
            "expected_checker_commit": binding.commit,
            "expected_checker_sha256": binding.sha256,
            "git_blob_path": binding.path,
            "git_blob_oid": binding.oid,
            "git_blob_sha256": binding.sha256,
            "pair_checker_block_matches_caller_pin": True,
        },
        "external_pin": {
            "manifest": {
                "path": str(external_pin.manifest.path),
                "schema_version": EXTERNAL_PIN_SCHEMA,
                "sha256": external_pin.manifest.sha256,
            },
            "signature": {
                "algorithm": "Ed25519",
                "path": str(external_pin.signature_path),
                "sha256": external_pin.signature_sha256,
                "verified": True,
            },
            "public_key": {
                "format": "SubjectPublicKeyInfo PEM",
                "path": str(external_pin.public_key_path),
                "sha256": external_pin.public_key_sha256,
            },
            "manifest_values_match_pair_and_checker": True,
        },
        "trust_root": {
            "kind": "caller-supplied-external-ed25519-public-key",
            "statement": (
                "The trust root is the caller-supplied Ed25519 public key held "
                "outside this Git repository. Signature verification binds the "
                "exact external pin manifest bytes to that key."
            ),
            "source_store_assumption": (
                "The same Git repository is trusted as the source store for the "
                "pinned commit and blob."
            ),
            "same_git_repository_trusted_as_source_store": True,
            "does_not_attest": [
                "host",
                "runtime",
                "malicious anchor verifier itself",
                "signer identity or authorization",
                "private-key custody",
            ],
        },
    }


def verify(
    pair_receipt_path: str,
    *,
    expected_pair_receipt_sha256: str | None,
    expected_checker_commit: str | None,
    expected_checker_sha256: str | None,
    external_pin_manifest: str | None = None,
    external_pin_signature: str | None = None,
    external_pin_public_key: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    document = _read_json(pair_receipt_path, "pair receipt")
    if expected_pair_receipt_sha256 is not None:
        expected_pair_receipt_sha256 = _sha256(
            expected_pair_receipt_sha256,
            "--expected-pair-receipt-sha256",
        )
        if document.sha256 != expected_pair_receipt_sha256:
            _reject("pair receipt bytes SHA-256 differs from caller pin")
    if (expected_checker_commit is None) != (expected_checker_sha256 is None):
        _reject("checker commit and SHA-256 pins must be provided together")
    external_pin_arguments = (
        external_pin_manifest,
        external_pin_signature,
        external_pin_public_key,
    )
    if any(value is not None for value in external_pin_arguments) and not all(
        value is not None for value in external_pin_arguments
    ):
        _reject("external pin manifest, signature, and public key are all required")

    repo_root = _repository_root()
    pair_schema = document.value.get("schema_version")
    if pair_schema == PAIR_V2_SCHEMA:
        checker_sha256, internal_binding = _validate_v2(document, repo_root)
        assessment = {
            "schema_version": PAIR_V2_SCHEMA,
            "status": "consistency_checked_but_unanchored",
            "pair_receipt_sha256": document.sha256,
            "checker_internal_consistency": {
                "outer_repo_commit": internal_binding.commit,
                "git_blob_path": internal_binding.path,
                "git_blob_oid": internal_binding.oid,
                "git_blob_sha256": internal_binding.sha256,
                "self_reported_checker_sha256": checker_sha256,
                "matches": True,
            },
            "external_anchor_sidecar_issued": False,
        }
        return assessment, None
    if pair_schema == PAIR_V3_SCHEMA:
        if expected_checker_commit is None or expected_checker_sha256 is None:
            _reject("v3 anchoring requires caller-pinned checker commit and SHA-256")
        if expected_pair_receipt_sha256 is None:
            _reject("v3 anchoring requires --expected-pair-receipt-sha256")
        caller_binding = _validate_v3(
            document,
            repo_root,
            _oid(expected_checker_commit, "--expected-checker-commit"),
            _sha256(expected_checker_sha256, "--expected-checker-sha256"),
        )
        assessment = {
            "schema_version": PAIR_V3_SCHEMA,
            "status": "caller_supplied_consistency_checked",
            "pair_receipt_sha256": document.sha256,
            "checker_source_consistency": {
                "expected_checker_commit": caller_binding.commit,
                "expected_checker_sha256": caller_binding.sha256,
                "git_blob_path": caller_binding.path,
                "git_blob_oid": caller_binding.oid,
                "matches": True,
            },
            "external_anchor_sidecar_issued": False,
        }
        if external_pin_manifest is None:
            return assessment, None
        external_pin = _validate_external_pin(
            manifest_path=external_pin_manifest,
            signature_path=_string(
                external_pin_signature, "--external-pin-signature"
            ),
            public_key_path=_string(
                external_pin_public_key, "--external-pin-public-key"
            ),
            document=document,
            binding=caller_binding,
            repo_root=repo_root,
        )
        return assessment, _anchor_payload(
            document,
            pair_schema,
            caller_binding,
            external_pin,
        )
    _reject("pair receipt schema is neither explicit v2 nor explicit v3")


def _write_create_only(output: Path, payload: dict[str, Any]) -> None:
    raw = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    with open(output, "xb") as handle:
        handle.write(raw)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description=__doc__)
    parser.add_argument("--pair-receipt", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--expected-pair-receipt-sha256",
        "--pair-receipt-sha256",
        dest="expected_pair_receipt_sha256",
    )
    parser.add_argument("--expected-checker-commit")
    parser.add_argument("--expected-checker-sha256")
    parser.add_argument("--external-pin-manifest")
    parser.add_argument("--external-pin-signature")
    parser.add_argument("--external-pin-public-key")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        assessment, payload = verify(
            args.pair_receipt,
            expected_pair_receipt_sha256=args.expected_pair_receipt_sha256,
            expected_checker_commit=args.expected_checker_commit,
            expected_checker_sha256=args.expected_checker_sha256,
            external_pin_manifest=args.external_pin_manifest,
            external_pin_signature=args.external_pin_signature,
            external_pin_public_key=args.external_pin_public_key,
        )
        if payload is None:
            print(json.dumps(assessment, sort_keys=True, separators=(",", ":")))
            return 0
        _write_create_only(args.output, payload)
        return 0
    except (AnchorValidationError, FileExistsError, OSError) as exc:
        print(f"mocc_trace_pair_anchor: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
