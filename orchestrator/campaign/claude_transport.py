# -*- coding: utf-8 -*-
"""Fail-closed admission for the Pegasus Claude transport exception.

The evaluator is deliberately pure.  The public wrapper is the only function
that observes the current site or reads the committed policy.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from . import site_policy


TRANSPORT_POLICY_RELATIVE_PATH = PurePosixPath(
    "tools/pegasus/policies/transport_v1.json"
)
_POLICY_SCHEMA = "pegasus-claude-transport-policy/v1"
_RECEIPT_SCHEMA = "claude-transport-receipt/v1"
_MODE = "explicit-http-proxy-env"
_MAX_POLICY_BYTES = 16_384
_ADMITTED_PROXY_KEYS = ("http_proxy", "https_proxy")
_UNADMITTED_PROXY_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "ALL_PROXY",
    "FTP_PROXY",
    "no_proxy",
    "all_proxy",
    "ftp_proxy",
)
_TLS_TRUST_OVERRIDE_KEYS = (
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "NODE_EXTRA_CA_CERTS",
    "NODE_TLS_REJECT_UNAUTHORIZED",
    "SSLKEYLOGFILE",
)
_METERED_TRANSPORT_KEYS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
)
# Keep this stdlib-only leaf grammar byte-for-byte aligned with
# orchestrator.qualification.qsub_binding._JOB_ID_TEXT.  The qualification
# package is deliberately not imported across the production leaf boundary;
# the cross-package equality is pinned by test_claude_transport.py.
PBS_JOBID_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._-]*"
_PBS_JOBID_RE = re.compile(PBS_JOBID_PATTERN)


class ClaudeTransportError(RuntimeError):
    """A redacted, machine-classifiable transport admission rejection."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class ClaudeTransportReceipt:
    """Immutable run-level identity; ``as_dict`` is the journal projection."""

    schema_version: str
    mode: str
    site: str
    admitted_env_keys: tuple[str, ...]
    endpoint_values: tuple[tuple[str, str], ...]
    endpoint_values_sha256: str
    policy_path: str
    policy_sha256: str
    source_tls_trust_override_keys: tuple[str, ...]
    forwarded_tls_trust_override_keys: tuple[str, ...]
    pbs_jobid: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "site": self.site,
            "admitted_env_keys": list(self.admitted_env_keys),
            "endpoint_values": dict(self.endpoint_values),
            "endpoint_values_sha256": self.endpoint_values_sha256,
            "policy_path": self.policy_path,
            "policy_sha256": self.policy_sha256,
            "source_tls_trust_override_keys": list(
                self.source_tls_trust_override_keys
            ),
            "forwarded_tls_trust_override_keys": list(
                self.forwarded_tls_trust_override_keys
            ),
            "pbs_jobid": self.pbs_jobid,
        }


@dataclass(frozen=True)
class ClaudeTransportAdmission:
    """Immutable environment delta and the receipt derived from one snapshot."""

    transport_env: tuple[tuple[str, str], ...]
    receipt: ClaudeTransportReceipt

    def env_dict(self) -> dict[str, str]:
        return dict(self.transport_env)


class _DuplicateKey(ValueError):
    pass


def _reject(code: str, message: str) -> None:
    raise ClaudeTransportError(code, message)


def is_valid_pbs_jobid(value: object) -> bool:
    """Return whether ``value`` has the repository-authoritative raw job ID form."""

    return type(value) is str and _PBS_JOBID_RE.fullmatch(value) is not None


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _reject_nonfinite(_: str) -> None:
    raise ValueError("non-finite JSON number")


def _canonical_endpoint_bytes(endpoint_values: Mapping[str, str]) -> bytes:
    return json.dumps(
        dict(endpoint_values),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _validate_endpoint_uri(value: object) -> None:
    if type(value) is not str or not value:
        _reject("policy-endpoint", "policy endpoint は空でない string 必須")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        _reject("policy-endpoint", "policy endpoint に control character を許可しない")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        _reject("policy-endpoint", "policy endpoint URI が不正")
    if (
        parsed.scheme != "http"
        or not parsed.hostname
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        _reject("policy-endpoint", "policy endpoint URI が許可形でない")


def _preflight_source_env(source_env: Mapping[str, str]) -> str:
    """Reject ambient transport controls before any policy filesystem I/O."""
    if not isinstance(source_env, Mapping):
        _reject("source-env-type", "source_env は Mapping 必須")
    pbs_jobid = source_env.get("PBS_JOBID")
    if type(pbs_jobid) is not str or not pbs_jobid:
        _reject("pbs-jobid-missing", "非空 PBS_JOBID witness が必要")
    if not is_valid_pbs_jobid(pbs_jobid):
        _reject("pbs-jobid-invalid", "PBS_JOBID witness の syntax が不正")
    if any(key in source_env for key in _TLS_TRUST_OVERRIDE_KEYS):
        _reject("tls-override-present", "TLS trust override env を許可しない")
    if any(key in source_env for key in _UNADMITTED_PROXY_KEYS):
        _reject("proxy-key-unadmitted", "未受理 proxy env 名を許可しない")
    if any(key in source_env for key in _METERED_TRANSPORT_KEYS):
        _reject("metered-transport-env-present", "従量 transport env を許可しない")
    for key in _ADMITTED_PROXY_KEYS:
        if key not in source_env or type(source_env[key]) is not str:
            _reject("proxy-pair-missing", "lowercase proxy pair は string 2 key 必須")
    return pbs_jobid


def evaluate_transport_admission(
    *,
    source_env: Mapping[str, str],
    policy_bytes: bytes,
    site: str,
    policy_path: str = "tools/pegasus/policies/transport_v1.json",
) -> ClaudeTransportAdmission:
    """Evaluate explicit inputs without filesystem, hostname, or env I/O."""
    pbs_jobid = _preflight_source_env(source_env)
    if type(policy_bytes) is not bytes:
        _reject("policy-bytes-type", "policy bytes は bytes 必須")
    if (
        type(policy_path) is not str
        or policy_path != "tools/pegasus/policies/transport_v1.json"
    ):
        _reject("policy-path", "transport policy path が固定値でない")
    if len(policy_bytes) > _MAX_POLICY_BYTES:
        _reject("policy-too-large", "transport policy が size 上限を超過")
    if site != site_policy.PEGASUS_COMPUTE:
        _reject("site-not-compute", "Pegasus compute site 以外では許可しない")

    try:
        policy_text = policy_bytes.decode("utf-8")
    except UnicodeError:
        _reject("policy-utf8", "transport policy は UTF-8 必須")
    try:
        policy = json.loads(
            policy_text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_nonfinite,
        )
    except _DuplicateKey:
        _reject("policy-duplicate-key", "transport policy に duplicate key がある")
    except (json.JSONDecodeError, ValueError):
        _reject("policy-json", "transport policy JSON が不正")
    if type(policy) is not dict:
        _reject("policy-schema", "transport policy top-level は object 必須")
    expected_top = {"schema_version", "site", "mode", "endpoint_values"}
    if set(policy) != expected_top:
        _reject("policy-schema", "transport policy top-level key が exact でない")
    if (
        policy["schema_version"] != _POLICY_SCHEMA
        or policy["site"] != site_policy.PEGASUS_COMPUTE
        or policy["mode"] != _MODE
    ):
        _reject("policy-contract", "transport policy contract が一致しない")
    endpoint_values = policy["endpoint_values"]
    if type(endpoint_values) is not dict or set(endpoint_values) != set(
        _ADMITTED_PROXY_KEYS
    ):
        _reject("policy-endpoint-shape", "endpoint_values key が exact でない")
    for key in endpoint_values:
        _validate_endpoint_uri(endpoint_values[key])

    for key in _ADMITTED_PROXY_KEYS:
        if source_env[key] != endpoint_values[key]:
            _reject("proxy-value-mismatch", "proxy endpoint が policy と一致しない")

    endpoint_digest = hashlib.sha256(
        _canonical_endpoint_bytes(endpoint_values)
    ).hexdigest()
    policy_digest = hashlib.sha256(policy_bytes).hexdigest()
    receipt = ClaudeTransportReceipt(
        schema_version=_RECEIPT_SCHEMA,
        mode=_MODE,
        site=site_policy.PEGASUS_COMPUTE,
        admitted_env_keys=_ADMITTED_PROXY_KEYS,
        endpoint_values=tuple(endpoint_values.items()),
        endpoint_values_sha256=endpoint_digest,
        policy_path=policy_path,
        policy_sha256=policy_digest,
        source_tls_trust_override_keys=(),
        forwarded_tls_trust_override_keys=(),
        pbs_jobid=pbs_jobid,
    )
    return ClaudeTransportAdmission(
        transport_env=tuple((key, source_env[key]) for key in _ADMITTED_PROXY_KEYS),
        receipt=receipt,
    )


def _read_policy_bytes(
    repository_root: Path,
    *,
    open_fd=os.open,
    read_fd=os.read,
) -> bytes:
    if not isinstance(repository_root, Path):
        _reject("repository-root-type", "repository_root は Path 必須")
    try:
        root_stat = repository_root.lstat()
    except OSError:
        _reject("repository-root", "repository_root を検査できない")
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        _reject("repository-root", "repository_root は symlink でない directory 必須")

    current = repository_root
    parts = TRANSPORT_POLICY_RELATIVE_PATH.parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            entry_stat = current.lstat()
        except OSError:
            _reject("policy-surface", "transport policy path を検査できない")
        if stat.S_ISLNK(entry_stat.st_mode):
            _reject("policy-surface", "transport policy path に symlink を許可しない")
        if index < len(parts) - 1 and not stat.S_ISDIR(entry_stat.st_mode):
            _reject("policy-surface", "transport policy ancestor は directory 必須")
    if not stat.S_ISREG(entry_stat.st_mode):
        _reject("policy-surface", "transport policy は regular file 必須")

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = open_fd(current, flags)
        try:
            opened_stat = os.fstat(fd)
            if not stat.S_ISREG(opened_stat.st_mode):
                _reject("policy-surface", "transport policy は regular file 必須")
            if opened_stat.st_size > _MAX_POLICY_BYTES:
                _reject("policy-too-large", "transport policy が size 上限を超過")
            if (
                opened_stat.st_dev != entry_stat.st_dev
                or opened_stat.st_ino != entry_stat.st_ino
            ):
                _reject("policy-surface", "transport policy identity が変化した")
            policy_bytes = read_fd(fd, _MAX_POLICY_BYTES + 1)
            if len(policy_bytes) != opened_stat.st_size:
                _reject("policy-read", "transport policy を完全に read-once できない")
        finally:
            os.close(fd)
    except ClaudeTransportError:
        raise
    except OSError:
        _reject("policy-read", "transport policy を read-once できない")
    if len(policy_bytes) > _MAX_POLICY_BYTES:
        _reject("policy-too-large", "transport policy が size 上限を超過")
    return policy_bytes


def admit_claude_transport(
    *, source_env: Mapping[str, str], repository_root: Path
) -> ClaudeTransportAdmission:
    """Resolve site exactly once, then read and evaluate the committed policy."""
    _preflight_source_env(source_env)
    if not isinstance(repository_root, Path):
        _reject("repository-root-type", "repository_root は Path 必須")
    site = site_policy.current_site()
    if site != site_policy.PEGASUS_COMPUTE:
        _reject("site-not-compute", "Pegasus compute site 以外では許可しない")
    policy_bytes = _read_policy_bytes(repository_root)
    return evaluate_transport_admission(
        source_env=source_env,
        policy_bytes=policy_bytes,
        site=site,
        policy_path=TRANSPORT_POLICY_RELATIVE_PATH.as_posix(),
    )
