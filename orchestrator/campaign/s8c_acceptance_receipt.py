# -*- coding: utf-8 -*-
"""Strict verifier for tracked Phase 3 8c acceptance receipt bytes.

This module deliberately has no dependency on ``trial_registry`` or
``layer3_report``.  It verifies the receipt artifact, every immutable byte
hash it names, and the recorded lifecycle prefix; it does not infer approval
authority or certify an experimental arm.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any


LEGACY_SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v1"
PREVIOUS_SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v2"
SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v3"
CROSS_BINDING_RECEIPT_SCHEMA_VERSION = "p3-8c-cross-binding-receipt/v1"
DEFAULT_RECEIPT_DIR = PurePosixPath("output/s8c-trial-registry/receipts")
LEGACY_MANDATORY_NON_CERTIFYING_REASONS = frozenset({
    "c02-arm-binding-unproven",
    "t468-approval-authority-absent",
})
MANDATORY_NON_CERTIFYING_REASONS = frozenset({
    "t468-approval-authority-absent",
})
C02_ARM_BINDING_UNPROVEN = "c02-arm-binding-unproven"

_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_TRIAL_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
_BASE_TOP_LEVEL_KEYS = frozenset({
    "schema_version",
    "manifest_path",
    "manifest_sha256",
    "prereg_commit",
    "activation_report_digest_sha256",
    "registry_path",
    "registry_blob_sha256",
    "registry_introduction_commit",
    "lifecycle_path",
    "lifecycle_prefix_bytes",
    "lifecycle_prefix_sha256",
    "certifying",
    "non_certifying_reason_codes",
    "trials",
})
_V1_TOP_LEVEL_KEYS = frozenset(_BASE_TOP_LEVEL_KEYS)
_V2_TOP_LEVEL_KEYS = frozenset(_BASE_TOP_LEVEL_KEYS)
_V3_TOP_LEVEL_KEYS = _BASE_TOP_LEVEL_KEYS | {
    "cross_binding_receipt_sha256",
}
_TOP_LEVEL_KEYS = _V3_TOP_LEVEL_KEYS
_V1_TRIAL_KEYS = frozenset({
    "trial_id",
    "arm",
    "holdout",
    "campaign_id",
    "status",
    "measurement_head",
    "report_path",
    "report_sha256",
    "attempt_journal_path",
    "attempt_journal_sha256",
})
_V2_TRIAL_KEYS = _V1_TRIAL_KEYS | {"arm_execution"}
_V2_TRIAL_KEYS_WITH_ORIGIN = _V2_TRIAL_KEYS | {"origin_terminal_projection"}
_V3_TRIAL_KEYS = _V2_TRIAL_KEYS | {"cross_binding_receipt_sha256"}
_V3_TRIAL_KEYS_WITH_ORIGIN = (
    _V3_TRIAL_KEYS | {"origin_terminal_projection"}
)
_ARM_EXECUTION_KEYS = frozenset({
    "input_schema_version",
    "content_digest_sha256",
    "arm_binding_digest_sha256",
})
_ARM_BINDING_DOMAIN_SEPARATOR_V1 = b"izanagi-s8c-arm-binding/v1\0"
_VERIFIED_RECEIPT_SEAL = object()
_GIT_ENV_ALLOW = frozenset({
    "LANG", "LC_ALL", "LC_CTYPE", "PATH", "SYSTEMROOT", "TMPDIR",
})


class AcceptanceReceiptError(RuntimeError):
    """A receipt or one of its referenced byte streams was rejected."""


def _fail(gate: str, message: str) -> None:
    raise AcceptanceReceiptError(f"[{gate}] {message}")


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceReceiptArmExecution:
    input_schema_version: str
    content_digest_sha256: str
    arm_binding_digest_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceReceiptTrial:
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    status: str
    measurement_head: str
    report_path: str
    report_sha256: str
    attempt_journal_path: str
    attempt_journal_sha256: str
    arm_execution: AcceptanceReceiptArmExecution | None
    cross_binding_receipt_sha256: str | None
    origin_terminal_projection: dict[str, Any] | None


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceReceipt:
    schema_version: str
    manifest_path: str
    manifest_sha256: str
    prereg_commit: str
    activation_report_digest_sha256: str
    registry_path: str
    registry_blob_sha256: str
    registry_introduction_commit: str
    lifecycle_path: str
    lifecycle_prefix_bytes: int
    lifecycle_prefix_sha256: str
    certifying: bool
    non_certifying_reason_codes: tuple[str, ...]
    cross_binding_receipt_sha256: str | None
    trials: tuple[AcceptanceReceiptTrial, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class VerifiedAcceptanceReceipt:
    """Sealed proof that tracked receipt and referenced working bytes matched."""

    repository_root: Path = dataclasses.field(repr=False, compare=False)
    path: Path
    relative_path: str
    raw_bytes: bytes = dataclasses.field(repr=False, compare=False)
    sha256: str
    receipt: AcceptanceReceipt
    _seal: object = dataclasses.field(repr=False, compare=False)

    @property
    def certifying(self) -> bool:
        return self.receipt.certifying

    @property
    def trials(self) -> tuple[AcceptanceReceiptTrial, ...]:
        return self.receipt.trials


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise AcceptanceReceiptError(
            f"[receipt-json] value is not canonical JSON: {exc}"
        ) from exc


def cross_binding_aggregate_sha256(
    trials: Sequence[Mapping[str, Any]],
) -> str:
    """Hash the sorted per-trial cross-binding leaves for receipt v3."""
    leaves: list[dict[str, str]] = []
    for index, trial in enumerate(trials):
        if not isinstance(trial, Mapping):
            _fail("receipt-cross-binding", f"leaf {index} is not an object")
        if set(trial) != {"trial_id", "receipt_sha256"}:
            _fail("receipt-cross-binding", f"leaf {index} exact keys differ")
        trial_id = trial.get("trial_id")
        if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
            _fail("receipt-cross-binding", f"leaf {index} trial_id is invalid")
        digest = _require_sha256(
            trial.get("receipt_sha256"),
            f"leaf {index}.receipt_sha256",
        )
        leaves.append({"trial_id": trial_id, "receipt_sha256": digest})
    if len({leaf["trial_id"] for leaf in leaves}) != len(leaves):
        _fail("receipt-cross-binding", "cross-binding leaves reuse a trial_id")
    payload = {
        "schema_version": CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
        "trials": sorted(leaves, key=lambda leaf: leaf["trial_id"]),
    }
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _reject_constant(value: str) -> None:
    _fail("receipt-json", f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("receipt-json", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except AcceptanceReceiptError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcceptanceReceiptError(
            f"[receipt-json] receipt is not strict UTF-8 JSON: {exc}"
        ) from exc


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        _fail(
            "receipt-schema",
            f"{label} key set differs: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}",
        )


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _fail("receipt-schema", f"{label} is not a SHA-256")
    return value


def _require_commit(value: Any, label: str) -> str:
    if not isinstance(value, str) or _COMMIT_RE.fullmatch(value) is None:
        _fail("receipt-schema", f"{label} is not a full lowercase commit ID")
    return value


def _require_posix_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        _fail("receipt-path", f"{label} is not a repository-relative POSIX path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or value in {".", ".."}
        or any(part in {"", ".", ".."} for part in path.parts)
        or ".git" in path.parts
    ):
        _fail("receipt-path", f"{label} is not canonical: {value!r}")
    return value


def _require_nonempty_reason_codes(value: Any) -> tuple[str, ...]:
    """Validate only the non-empty, sorted, unique reason-list shape."""
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(reason, str) or not reason for reason in value)
        or value != sorted(set(value))
    ):
        _fail(
            "receipt-reason-list",
            "reason codes must be a non-empty sorted unique string list",
        )
    return tuple(value)


def _require_mandatory_reason_codes(
    reasons: Sequence[str],
    required: frozenset[str] = MANDATORY_NON_CERTIFYING_REASONS,
) -> None:
    """Validate one schema generation's unresolved-authority reasons."""
    if not required.issubset(reasons):
        _fail(
            "receipt-mandatory-reasons",
            "mandatory unresolved-authority reason codes are absent",
        )


def _require_legacy_mandatory_reason_codes(reasons: Sequence[str]) -> None:
    _require_mandatory_reason_codes(
        reasons, LEGACY_MANDATORY_NON_CERTIFYING_REASONS,
    )


def _parse_arm_execution(
    value: Any, *, label: str,
) -> AcceptanceReceiptArmExecution:
    if not isinstance(value, Mapping):
        _fail("receipt-schema", f"{label} is not an object")
    _exact_keys(value, _ARM_EXECUTION_KEYS, label)
    input_schema_version = value["input_schema_version"]
    if input_schema_version != "8b-v1":
        _fail("receipt-arm-binding", f"{label}.input_schema_version differs")
    return AcceptanceReceiptArmExecution(
        input_schema_version=input_schema_version,
        content_digest_sha256=_require_sha256(
            value["content_digest_sha256"],
            f"{label}.content_digest_sha256",
        ),
        arm_binding_digest_sha256=_require_sha256(
            value["arm_binding_digest_sha256"],
            f"{label}.arm_binding_digest_sha256",
        ),
    )


def _parse_origin_terminal_projection(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail("receipt-schema", f"{label} is not an object")
    return dict(value)


def parse_acceptance_receipt_bytes(data: bytes) -> AcceptanceReceipt:
    """Strictly parse one canonical receipt line terminated by LF."""
    if not isinstance(data, bytes) or not data.endswith(b"\n"):
        _fail("receipt-canonical", "receipt must be one newline-terminated JSON line")
    if data.count(b"\n") != 1:
        _fail("receipt-canonical", "receipt must contain exactly one JSON line")
    value = _decode_json(data[:-1])
    if not isinstance(value, Mapping):
        _fail("receipt-schema", "receipt root is not an object")
    if _canonical_bytes(value) + b"\n" != data:
        _fail("receipt-canonical", "receipt bytes are not canonical JSON plus LF")
    if "schema_version" not in value:
        _fail("receipt-schema", "receipt.schema_version is missing")
    schema_version = value["schema_version"]
    if schema_version not in {
        LEGACY_SCHEMA_VERSION, PREVIOUS_SCHEMA_VERSION, SCHEMA_VERSION,
    }:
        _fail("receipt-schema", "unsupported schema_version")
    expected_top_keys = {
        LEGACY_SCHEMA_VERSION: _V1_TOP_LEVEL_KEYS,
        PREVIOUS_SCHEMA_VERSION: _V2_TOP_LEVEL_KEYS,
        SCHEMA_VERSION: _V3_TOP_LEVEL_KEYS,
    }[schema_version]
    _exact_keys(value, expected_top_keys, "receipt")

    manifest_path = _require_posix_path(value["manifest_path"], "manifest_path")
    manifest_sha256 = _require_sha256(value["manifest_sha256"], "manifest_sha256")
    prereg_commit = _require_commit(value["prereg_commit"], "prereg_commit")
    activation_digest = _require_sha256(
        value["activation_report_digest_sha256"],
        "activation_report_digest_sha256",
    )
    registry_path = _require_posix_path(value["registry_path"], "registry_path")
    registry_digest = _require_sha256(
        value["registry_blob_sha256"], "registry_blob_sha256"
    )
    introduction = _require_commit(
        value["registry_introduction_commit"], "registry_introduction_commit"
    )
    lifecycle_path = _require_posix_path(value["lifecycle_path"], "lifecycle_path")
    lifecycle_prefix_bytes = value["lifecycle_prefix_bytes"]
    if (
        isinstance(lifecycle_prefix_bytes, bool)
        or not isinstance(lifecycle_prefix_bytes, int)
        or lifecycle_prefix_bytes < 1
    ):
        _fail("receipt-schema", "lifecycle_prefix_bytes is not a positive int")
    lifecycle_prefix_digest = _require_sha256(
        value["lifecycle_prefix_sha256"], "lifecycle_prefix_sha256"
    )
    cross_binding_digest = (
        None
        if schema_version != SCHEMA_VERSION
        else _require_sha256(
            value["cross_binding_receipt_sha256"],
            "cross_binding_receipt_sha256",
        )
    )

    # Both generations structurally record unresolved approval authority.
    # No accepted bytes can turn either generation into a certifying receipt.
    if value["certifying"] is not False:
        _fail("receipt-certifying", "receipts are structurally non-certifying")
    reasons = _require_nonempty_reason_codes(value["non_certifying_reason_codes"])
    if schema_version == LEGACY_SCHEMA_VERSION:
        _require_legacy_mandatory_reason_codes(reasons)
    else:
        _require_mandatory_reason_codes(reasons)

    trials_value = value["trials"]
    if not isinstance(trials_value, list) or len(trials_value) != 6:
        _fail("receipt-schema", "trials must contain exactly six rows")
    trials: list[AcceptanceReceiptTrial] = []
    for index, raw in enumerate(trials_value):
        if not isinstance(raw, Mapping):
            _fail("receipt-schema", f"trials[{index}] is not an object")
        expected_trial_keys = (
            _V1_TRIAL_KEYS
            if schema_version == LEGACY_SCHEMA_VERSION
            else (
                (
                    _V3_TRIAL_KEYS_WITH_ORIGIN
                    if "origin_terminal_projection" in raw
                    else _V3_TRIAL_KEYS
                )
                if schema_version == SCHEMA_VERSION
                else (
                    _V2_TRIAL_KEYS_WITH_ORIGIN
                    if "origin_terminal_projection" in raw
                    else _V2_TRIAL_KEYS
                )
            )
        )
        _exact_keys(raw, expected_trial_keys, f"trials[{index}]")
        trial_id = raw["trial_id"]
        if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
            _fail("receipt-schema", f"trials[{index}].trial_id is invalid")
        arm = raw["arm"]
        holdout = raw["holdout"]
        campaign_id = raw["campaign_id"]
        status = raw["status"]
        if not isinstance(arm, str) or arm not in {"on", "off", "swapped"}:
            _fail("receipt-schema", f"trials[{index}].arm is invalid")
        if not isinstance(holdout, str) or holdout not in {"H1", "H2"}:
            _fail("receipt-schema", f"trials[{index}].holdout is invalid")
        if not isinstance(campaign_id, str) or not campaign_id:
            _fail("receipt-schema", f"trials[{index}].campaign_id is invalid")
        if not isinstance(status, str) or not status:
            _fail("receipt-schema", f"trials[{index}].status is invalid")
        trials.append(AcceptanceReceiptTrial(
            trial_id=trial_id,
            arm=arm,
            holdout=holdout,
            campaign_id=campaign_id,
            status=status,
            measurement_head=_require_commit(
                raw["measurement_head"], f"trials[{index}].measurement_head"
            ),
            report_path=_require_posix_path(
                raw["report_path"], f"trials[{index}].report_path"
            ),
            report_sha256=_require_sha256(
                raw["report_sha256"], f"trials[{index}].report_sha256"
            ),
            attempt_journal_path=_require_posix_path(
                raw["attempt_journal_path"],
                f"trials[{index}].attempt_journal_path",
            ),
            attempt_journal_sha256=_require_sha256(
                raw["attempt_journal_sha256"],
                f"trials[{index}].attempt_journal_sha256",
            ),
            arm_execution=(
                None
                if schema_version == LEGACY_SCHEMA_VERSION
                else _parse_arm_execution(
                    raw["arm_execution"], label=f"trials[{index}].arm_execution",
                )
            ),
            cross_binding_receipt_sha256=(
                None
                if schema_version != SCHEMA_VERSION
                else _require_sha256(
                    raw["cross_binding_receipt_sha256"],
                    f"trials[{index}].cross_binding_receipt_sha256",
                )
            ),
            origin_terminal_projection=(
                None
                if "origin_terminal_projection" not in raw
                else _parse_origin_terminal_projection(
                    raw["origin_terminal_projection"],
                    label=f"trials[{index}].origin_terminal_projection",
                )
            ),
        ))
    if [trial.trial_id for trial in trials] != sorted(
        trial.trial_id for trial in trials
    ):
        _fail("receipt-schema", "trials are not sorted by trial_id")
    if len({trial.trial_id for trial in trials}) != 6:
        _fail("receipt-schema", "receipt reuses a trial_id")
    if len({trial.campaign_id for trial in trials}) != 6:
        _fail("receipt-schema", "receipt reuses a campaign_id")
    if len({trial.measurement_head for trial in trials}) != 1:
        _fail(
            "receipt-measurement-head-coherence",
            "trials do not share one measurement_head",
        )
    if schema_version in {PREVIOUS_SCHEMA_VERSION, SCHEMA_VERSION}:
        expected_cells = {
            (holdout, arm)
            for holdout in ("H1", "H2")
            for arm in ("on", "off", "swapped")
        }
        actual_cells = {(trial.holdout, trial.arm) for trial in trials}
        if actual_cells != expected_cells:
            _fail("receipt-arm-binding", "current trials are not the closed six arm cells")
        for holdout in ("H1", "H2"):
            digests = [
                trial.arm_execution.content_digest_sha256
                for trial in trials
                if trial.holdout == holdout and trial.arm_execution is not None
            ]
            if len(set(digests)) != 3:
                _fail(
                    "receipt-arm-binding",
                    f"{holdout} content digests are not pairwise distinct",
                )

    return AcceptanceReceipt(
        schema_version=schema_version,
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
        prereg_commit=prereg_commit,
        activation_report_digest_sha256=activation_digest,
        registry_path=registry_path,
        registry_blob_sha256=registry_digest,
        registry_introduction_commit=introduction,
        lifecycle_path=lifecycle_path,
        lifecycle_prefix_bytes=lifecycle_prefix_bytes,
        lifecycle_prefix_sha256=lifecycle_prefix_digest,
        certifying=False,
        non_certifying_reason_codes=reasons,
        cross_binding_receipt_sha256=cross_binding_digest,
        trials=tuple(trials),
    )


def _git_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key in _GIT_ENV_ALLOW}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _git(root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", os.fspath(root), *args],
        env=_git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _repository_root(path: Path) -> Path:
    try:
        root = Path(path).resolve(strict=True)
    except OSError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-repo] repository root cannot be resolved: {path}"
        ) from exc
    result = _git(root, ("rev-parse", "--show-toplevel"))
    if result.returncode != 0:
        _fail("receipt-repo", "repository root is not a Git work tree")
    try:
        actual = Path(result.stdout.decode("utf-8").strip()).resolve(strict=True)
    except (OSError, UnicodeDecodeError) as exc:
        raise AcceptanceReceiptError("[receipt-repo] Git returned a bad root") from exc
    if actual != root:
        _fail("receipt-repo", "repository_root is not the Git top level")
    return root


def _read_regular_bytes(path: Path, *, label: str) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-reference] {label} cannot be stated: {path}"
        ) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        _fail("receipt-reference", f"{label} is not a regular non-symlink file")
    flags = os.O_RDONLY | (getattr(os, "O_NOFOLLOW", 0))
    try:
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise AcceptanceReceiptError(
            f"[receipt-reference] {label} cannot be read: {path}"
        ) from exc
    if not stat.S_ISREG(opened.st_mode) or (
        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns
    ) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        _fail("receipt-reference", f"{label} changed while it was read")
    return b"".join(chunks)


def _blob_at_head(root: Path, relative_path: str) -> bytes | None:
    listing = _git(root, (
        "ls-tree", "-z", "--full-name", "HEAD", "--", relative_path,
    ))
    if listing.returncode != 0:
        _fail("receipt-tracked", "HEAD tree lookup failed")
    entries = [entry for entry in listing.stdout.split(b"\0") if entry]
    if not entries:
        return None
    if len(entries) != 1:
        _fail("receipt-tracked", "receipt path is not a single HEAD entry")
    metadata, separator, entry_path = entries[0].partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or len(fields) != 3:
        _fail("receipt-tracked", "HEAD tree entry is malformed")
    mode, object_type, object_id = fields
    if (
        entry_path != os.fsencode(relative_path)
        or object_type != b"blob"
        or mode not in {b"100644", b"100755"}
    ):
        _fail("receipt-tracked", "receipt HEAD entry is not the literal regular file")
    blob = _git(root, ("cat-file", "blob", object_id.decode("ascii")))
    if blob.returncode != 0:
        _fail("receipt-tracked", "receipt HEAD blob cannot be read")
    return blob.stdout


def _resolved_reference(root: Path, relative_path: str, label: str) -> Path:
    lexical = root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise AcceptanceReceiptError(
            f"[receipt-reference] {label} escapes or is absent from repository"
        ) from exc
    if resolved != lexical:
        _fail("receipt-reference", f"{label} traverses a symlink component")
    return resolved


def _assert_digest(
    root: Path, relative_path: str, expected: str, label: str,
) -> bytes:
    data = _read_regular_bytes(
        _resolved_reference(root, relative_path, label), label=label,
    )
    if hashlib.sha256(data).hexdigest() != expected:
        _fail("receipt-reference-hash", f"{label} bytes differ from receipt")
    return data


def _arm_execution_record(
    arm_execution: AcceptanceReceiptArmExecution,
) -> dict[str, str]:
    return {
        "input_schema_version": arm_execution.input_schema_version,
        "content_digest_sha256": arm_execution.content_digest_sha256,
        "arm_binding_digest_sha256": arm_execution.arm_binding_digest_sha256,
    }


def _arm_binding_digest(
    *, holdout: str, arm: str, content_digest: str,
) -> str:
    return hashlib.sha256(
        _ARM_BINDING_DOMAIN_SEPARATOR_V1
        + holdout.encode("utf-8")
        + arm.encode("utf-8")
        + content_digest.encode("ascii")
    ).hexdigest()


def _reference_object(data: bytes, *, label: str) -> Mapping[str, Any]:
    value = _decode_json(data)
    if not isinstance(value, Mapping):
        _fail("receipt-arm-binding", f"{label} root is not an object")
    return value


def _journal_events(data: bytes) -> tuple[Mapping[str, Any], ...]:
    if not data or not data.endswith(b"\n"):
        _fail("receipt-arm-binding", "attempt journal is not newline terminated")
    events = []
    for index, line in enumerate(data.splitlines(), 1):
        value = _decode_json(line)
        if not isinstance(value, Mapping):
            _fail(
                "receipt-arm-binding",
                f"attempt journal line {index} is not an object",
            )
        events.append(value)
    return tuple(events)


def _verify_v2_trial_arm_execution(
    trial: AcceptanceReceiptTrial,
    *,
    report_bytes: bytes,
    journal_bytes: bytes,
) -> bool:
    """Verify summary equality and rederive content from named report bytes.

    ``False`` means the report has no executed cell descriptor, so the legacy
    C02 reason cannot be dropped.  Any contradictory bytes fail closed.
    """
    arm_execution = trial.arm_execution
    if arm_execution is None:
        _fail("receipt-arm-binding", "v2 trial arm_execution is absent")
    expected_arm_execution = _arm_execution_record(arm_execution)
    report = _reference_object(report_bytes, label="trial report")

    if report.get("trial_id") != trial.trial_id:
        _fail("receipt-arm-binding", "trial report trial_id differs from receipt")
    if report.get("measurement_head") != trial.measurement_head:
        _fail(
            "receipt-arm-binding",
            "trial report measurement_head differs from receipt",
        )
    if report.get("status") != trial.status:
        _fail("receipt-arm-binding", "trial report status differs from receipt")
    report_has_origin = "origin_terminal_projection" in report
    receipt_has_origin = trial.origin_terminal_projection is not None
    if report_has_origin != receipt_has_origin:
        _fail(
            "receipt-origin-projection",
            "trial report origin_terminal_projection presence differs from receipt",
        )
    if receipt_has_origin:
        report_origin = report.get("origin_terminal_projection")
        if not isinstance(report_origin, Mapping):
            _fail(
                "receipt-origin-projection",
                "trial report origin_terminal_projection is not an object",
            )
        if _canonical_bytes(report_origin) != _canonical_bytes(
            trial.origin_terminal_projection
        ):
            _fail(
                "receipt-origin-projection",
                "trial report origin_terminal_projection differs from receipt",
            )
    launch = report.get("launch_admission")
    binding = launch.get("binding") if isinstance(launch, Mapping) else None
    if not isinstance(binding, Mapping) or any(
        binding.get(field) != expected
        for field, expected in (
            ("arm", trial.arm),
            ("holdout", trial.holdout),
            ("campaign_id", trial.campaign_id),
        )
    ):
        _fail("receipt-arm-binding", "trial report arm cell differs from receipt")

    cells = report.get("cells")
    if not isinstance(cells, list) or len(cells) > 1:
        _fail("receipt-arm-binding", "trial report cells are not a zero/one list")
    descriptor_proven = False
    if cells:
        cell = cells[0]
        descriptor = cell.get("descriptor") if isinstance(cell, Mapping) else None
        if not isinstance(descriptor, Mapping):
            _fail("receipt-arm-binding", "trial report cell descriptor is absent")
        workload = binding.get("workload")
        if cell.get("workload") != workload:
            _fail("receipt-arm-binding", "trial report descriptor cell is not bound")
        actual_content_digest = hashlib.sha256(
            _canonical_bytes(descriptor)
        ).hexdigest()
        if actual_content_digest != arm_execution.content_digest_sha256:
            _fail(
                "receipt-arm-binding",
                "cell descriptor content digest differs from receipt",
            )
        descriptor_proven = True

    if report.get("arm_execution") != expected_arm_execution:
        _fail(
            "receipt-arm-binding",
            "trial report arm_execution differs from receipt",
        )
    expected_binding_digest = _arm_binding_digest(
        holdout=trial.holdout,
        arm=trial.arm,
        content_digest=arm_execution.content_digest_sha256,
    )
    if arm_execution.arm_binding_digest_sha256 != expected_binding_digest:
        _fail("receipt-arm-binding", "arm binding digest differs from receipt inputs")

    starts = [
        event for event in _journal_events(journal_bytes)
        if event.get("event") == "run-start"
    ]
    if len(starts) != 1:
        _fail("receipt-arm-binding", "attempt journal run-start is not unique")
    if starts[0].get("arm_execution") != expected_arm_execution:
        _fail(
            "receipt-arm-binding",
            "run-start arm_execution differs from report and receipt",
        )
    return descriptor_proven


def _arm_execution_authorizes_reason_drop(
    descriptor_proofs: Sequence[bool],
) -> bool:
    """The only v2 gate allowed to remove the legacy C02 reason."""
    return len(descriptor_proofs) == 6 and all(descriptor_proofs)


def _assert_prefix_digest(
    root: Path,
    relative_path: str,
    prefix_bytes: int,
    expected: str,
    label: str,
) -> None:
    data = _read_regular_bytes(
        _resolved_reference(root, relative_path, label), label=label,
    )
    if len(data) < prefix_bytes:
        _fail("receipt-reference-prefix", f"{label} is shorter than receipt prefix")
    prefix = data[:prefix_bytes]
    if hashlib.sha256(prefix).hexdigest() != expected:
        _fail("receipt-reference-prefix", f"{label} prefix bytes differ from receipt")


def _assert_git_history_append_only(
    root: Path,
    relative_path: str,
    *,
    label: str,
) -> None:
    """Reject deletion/recreation and non-prefix edits within this repository."""
    history = _git(root, (
        "log", "--format=%H", "--reverse", "--full-history", "HEAD", "--",
        relative_path,
    ))
    if history.returncode != 0:
        _fail("receipt-history", f"{label} history walk failed")
    previous: bytes | None = None
    for raw_commit in history.stdout.splitlines():
        try:
            commit_id = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise AcceptanceReceiptError(
                f"[receipt-history] {label} history returned non-ASCII"
            ) from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("receipt-history", f"{label} history returned an invalid commit ID")
        blob = _blob_at_commit(root, commit_id, relative_path)
        if blob is None:
            _fail("receipt-history", f"{label} was deleted in committed history")
        if previous is not None and (
            not blob.startswith(previous) or len(blob) <= len(previous)
        ):
            _fail("receipt-history", f"{label} history is not a strict prefix extension")
        previous = blob
    if previous is not None:
        current = _read_regular_bytes(
            _resolved_reference(root, relative_path, label), label=label,
        )
        if not current.startswith(previous):
            _fail(
                "receipt-history",
                f"working {label} does not extend committed history",
            )


def _blob_at_commit(root: Path, commit_id: str, relative_path: str) -> bytes | None:
    listing = _git(root, (
        "ls-tree", "-z", "--full-name", commit_id, "--", relative_path,
    ))
    if listing.returncode != 0:
        _fail("receipt-history", "history tree lookup failed")
    entries = [entry for entry in listing.stdout.split(b"\0") if entry]
    if not entries:
        return None
    if len(entries) != 1:
        _fail("receipt-history", "history path is not a single entry")
    metadata, separator, entry_path = entries[0].partition(b"\t")
    fields = metadata.split()
    if (
        separator != b"\t"
        or len(fields) != 3
        or entry_path != os.fsencode(relative_path)
        or fields[1] != b"blob"
        or fields[0] not in {b"100644", b"100755"}
    ):
        _fail("receipt-history", "history entry is not a literal regular file")
    blob = _git(root, ("cat-file", "blob", fields[2].decode("ascii")))
    if blob.returncode != 0:
        _fail("receipt-history", "history blob cannot be read")
    return blob.stdout


def verify_acceptance_receipt(
    receipt_path: Path,
    *,
    repository_root: Path,
) -> VerifiedAcceptanceReceipt:
    """Freshly hash every immutable reference and the lifecycle prefix."""
    root = _repository_root(repository_root)
    supplied = Path(receipt_path)
    lexical = Path(os.path.abspath(os.fspath(
        supplied if supplied.is_absolute() else root / supplied
    )))
    try:
        relative = lexical.relative_to(root).as_posix()
        path = lexical.resolve(strict=True)
        path.relative_to(root)
    except (OSError, ValueError) as exc:
        raise AcceptanceReceiptError(
            "[receipt-path] receipt is absent or outside repository"
        ) from exc
    if path != lexical:
        _fail("receipt-path", "receipt path traverses a symlink component")
    raw = _read_regular_bytes(path, label="receipt")
    receipt = parse_acceptance_receipt_bytes(raw)
    expected_relative = (
        DEFAULT_RECEIPT_DIR / f"{receipt.manifest_sha256}.json"
    ).as_posix()
    if relative != expected_relative:
        _fail("receipt-path", "receipt path does not match manifest_sha256")
    committed = _blob_at_head(root, relative)
    if committed is None:
        _fail("receipt-untracked", "receipt is not tracked at Git HEAD")
    if committed != raw:
        _fail("receipt-head-mismatch", "working receipt bytes differ from Git HEAD")

    _assert_digest(root, receipt.manifest_path, receipt.manifest_sha256, "manifest")
    _assert_digest(root, receipt.registry_path, receipt.registry_blob_sha256, "registry")
    _assert_git_history_append_only(root, receipt.lifecycle_path, label="lifecycle")
    _assert_prefix_digest(
        root,
        receipt.lifecycle_path,
        receipt.lifecycle_prefix_bytes,
        receipt.lifecycle_prefix_sha256,
        "lifecycle",
    )
    descriptor_proofs: list[bool] = []
    for trial in receipt.trials:
        report_bytes = _assert_digest(
            root, trial.report_path, trial.report_sha256, "trial report",
        )
        journal_bytes = _assert_digest(
            root,
            trial.attempt_journal_path,
            trial.attempt_journal_sha256,
            "attempt journal",
        )
        if receipt.schema_version in {PREVIOUS_SCHEMA_VERSION, SCHEMA_VERSION}:
            descriptor_proofs.append(_verify_v2_trial_arm_execution(
                trial,
                report_bytes=report_bytes,
                journal_bytes=journal_bytes,
            ))
    if (
        receipt.schema_version in {PREVIOUS_SCHEMA_VERSION, SCHEMA_VERSION}
        and C02_ARM_BINDING_UNPROVEN not in receipt.non_certifying_reason_codes
        and not _arm_execution_authorizes_reason_drop(descriptor_proofs)
    ):
        _fail(
            "receipt-mandatory-reasons",
            "c02-arm-binding-unproven was dropped without descriptor proof",
        )
    if receipt.schema_version == SCHEMA_VERSION:
        aggregate = cross_binding_aggregate_sha256([
            {
                "trial_id": trial.trial_id,
                "receipt_sha256": trial.cross_binding_receipt_sha256,
            }
            for trial in receipt.trials
        ])
        if receipt.cross_binding_receipt_sha256 != aggregate:
            _fail(
                "receipt-cross-binding",
                "top-level cross-binding aggregate differs from trial leaves",
            )
    return VerifiedAcceptanceReceipt(
        repository_root=root,
        path=path,
        relative_path=relative,
        raw_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        receipt=receipt,
        _seal=_VERIFIED_RECEIPT_SEAL,
    )


def require_current_verified_receipt(
    verified: VerifiedAcceptanceReceipt,
) -> VerifiedAcceptanceReceipt:
    """Reverify a sealed capability so later byte changes cannot reuse it."""
    if (
        not isinstance(verified, VerifiedAcceptanceReceipt)
        or verified._seal is not _VERIFIED_RECEIPT_SEAL
    ):
        _fail("receipt-capability", "receipt was not issued by the verifier")
    current = verify_acceptance_receipt(
        verified.path, repository_root=verified.repository_root,
    )
    if current.sha256 != verified.sha256 or current.raw_bytes != verified.raw_bytes:
        _fail("receipt-capability", "receipt changed after capability issuance")
    return current
