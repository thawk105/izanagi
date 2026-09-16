# -*- coding: utf-8 -*-
"""Fixed-session memo for the sort-SWO oracle environment.

The controller binds the production resolver to the canonical test-owned
Masstree fixture.  This module gives the controller/serial collection barrier
the sole resolver call and gives test consumers a read-only, fail-closed
snapshot.  It is intentionally a sibling of ``real_repo_receipt_memo``: the
two memos have different production resolvers and different wire schemas.
"""
from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

from orchestrator.campaign import sort_swo_oracle as oracle


ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
CCBENCH = ROOT / "external" / "ccbench"
MASSTREE_FIXTURE = (
    ORCHESTRATOR / "tests" / "fixtures" / "sort_swo_masstree"
)

# Capture the production seam once.  The consumer path below never calls this
# seam; keeping it as a private value also makes tests able to prove the
# resolver call count without patching a dynamically recursive reference.
_PRODUCTION_RESOLVE = oracle.resolve_oracle_environment

_RUN_ID_ENV = "PYTEST_XDIST_TESTRUNUID"
_SESSION_NONCE_ENV = "IZANAGI_ORACLE_ENVIRONMENT_MEMO_NONCE"
_CACHE_PREFIX = "izanagi-sort-swo-oracle-"
# Observed prewarm: 28.328 s (acceptance shard-0, n=1); 120 s is about
# 4.24 times that observation. With n=1 the tail is unknown. This is an
# upper bound we expect not to reach; reaching it is a failure.
_EARLY_WAIT_TIMEOUT_S = 120.0
_CACHE_STALE_S = 6 * 3600
_CACHE_MAX_BYTES = 8 * 1024 * 1024
_CACHE_SCHEMA_VERSION = 1
_CACHE_KEYS = frozenset({"schema_version", "state", "environment", "failure"})
_ERROR_PREFIX = "IZANAGI_ORACLE_ENVIRONMENT_MEMO_FAIL_CLOSED_V1 "
_MISSING = object()
_SESSION_UNBOUND = object()


class _CacheDecodeError(ValueError):
    """Cache bytes are not strict UTF-8 JSON."""


class _CacheSchemaError(ValueError):
    """Decoded cache JSON does not match the closed wire schema."""


class _CacheTooLarge(ValueError):
    """Cache bytes exceed the bounded reader limit."""


class OracleEnvironmentMemoError(RuntimeError):
    """Structured fail-closed diagnostic for the oracle environment memo."""

    def __init__(
        self,
        reason: str,
        *,
        cache_path: Optional[Path],
        run_id: Optional[str],
        head: Optional[str],
        prewarm: bool,
        process_prewarmed: bool,
        cause: Optional[BaseException] = None,
    ) -> None:
        payload: dict[str, object] = {
            "cache_path": str(cache_path) if cache_path is not None else None,
            "head": head,
            "prewarm": prewarm,
            "process_prewarmed": process_prewarmed,
            "reason": reason,
            "run_id": run_id,
        }
        if cause is not None:
            payload["errno"] = getattr(cause, "errno", None)
            payload["exception_type"] = type(cause).__name__
        self.payload = payload
        super().__init__(
            _ERROR_PREFIX
            + json.dumps(
                payload,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            )
        )


# Short aliases make the endpoint's error type discoverable without coupling
# callers to the implementation wording.
OracleMemoError = OracleEnvironmentMemoError


def _resolve_now():
    """Call the production resolver; callers are limited to ``prewarm``."""
    return _PRODUCTION_RESOLVE(
        CCBENCH, dependency_root=MASSTREE_FIXTURE,
    )


def _repo_head() -> Optional[str]:
    try:
        output = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=30,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return output if re.fullmatch(r"[0-9a-f]{40}", output) else None


def _cache_path_for(run_id: str, head: str, session_id: str) -> Path:
    run_hash = hashlib.sha256(
        run_id.encode("utf-8", errors="surrogatepass")
    ).hexdigest()
    session_hash = hashlib.sha256(
        session_id.encode("utf-8", errors="surrogatepass")
    ).hexdigest()
    return Path(tempfile.gettempdir()) / (
        f"{_CACHE_PREFIX}{run_hash}-{session_hash}-{head}.json"
    )


def _session_cache_path(
    *,
    run_id: Optional[str] = None,
    head: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Optional[Path]:
    if run_id is None:
        run_id = os.environ.get(_RUN_ID_ENV)
    if run_id is None:
        return None
    if session_id is None:
        session_id = os.environ.get(_SESSION_NONCE_ENV)
    if not isinstance(session_id, str) or not session_id:
        return None
    if head is None:
        head = _repo_head()
    if head is None:
        return None
    return _cache_path_for(run_id, head, session_id)


def _reject_duplicate_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _CacheDecodeError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(token: str):
    raise _CacheDecodeError(f"non-finite JSON constant: {token}")


def _is_json_tree(value) -> bool:
    if value is None or isinstance(value, (bool, int, str)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_tree(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_json_tree(item)
            for key, item in value.items()
        )
    return False


def _validate_candidate_document(document: object) -> None:
    if not isinstance(document, dict) or set(document) != {
        "origin", "path", "outcome",
    }:
        raise _CacheSchemaError("candidate keys are not exact")
    if (
        type(document["origin"]) is not str
        or not document["origin"]
        or len(document["origin"]) > 128
    ):
        raise _CacheSchemaError("candidate origin is invalid")
    if type(document["outcome"]) is not str:
        raise _CacheSchemaError("candidate outcome is invalid")
    path = document["path"]
    if path is not None and (type(path) is not str or not path):
        raise _CacheSchemaError("candidate path is invalid")
    if not _is_json_tree(document):
        raise _CacheSchemaError("candidate contains a non-JSON value")


def _validate_cache_document(document: object) -> None:
    if not isinstance(document, dict) or set(document) != _CACHE_KEYS:
        raise _CacheSchemaError("cache envelope keys are not exact")
    if (
        type(document["schema_version"]) is not int
        or document["schema_version"] != _CACHE_SCHEMA_VERSION
    ):
        raise _CacheSchemaError("cache schema_version is invalid")
    state = document["state"]
    if state not in {"success", "failure"}:
        raise _CacheSchemaError("cache state is invalid")
    environment = document["environment"]
    failure = document["failure"]
    if state == "success":
        if not isinstance(environment, dict) or set(environment) != {
            "compiler", "ccbench_dir", "dependency_root",
        }:
            raise _CacheSchemaError("cache environment is invalid")
        if any(
            type(environment[key]) is not str or not environment[key]
            for key in ("compiler", "ccbench_dir", "dependency_root")
        ):
            raise _CacheSchemaError("cache environment paths are invalid")
        if failure is not None:
            raise _CacheSchemaError("successful cache has a failure")
    else:
        if environment is not None:
            raise _CacheSchemaError("failed cache has an environment")
        if not isinstance(failure, dict) or set(failure) != {
            "detail_code", "compiler_candidates", "dependency_candidates",
        }:
            raise _CacheSchemaError("cache failure is invalid")
        if type(failure["detail_code"]) is not str:
            raise _CacheSchemaError("cache failure detail_code is invalid")
        for key in ("compiler_candidates", "dependency_candidates"):
            candidates = failure[key]
            if not isinstance(candidates, list) or not candidates:
                raise _CacheSchemaError("cache failure candidates are invalid")
            for candidate in candidates:
                _validate_candidate_document(candidate)
    if not _is_json_tree(document):
        raise _CacheSchemaError("cache contains a non-JSON value")


def _candidate_document(candidate) -> dict[str, object]:
    if type(candidate) is not oracle.OracleEnvironmentCandidate:
        raise TypeError("oracle cache requires OracleEnvironmentCandidate")
    return {
        "origin": candidate.origin,
        "path": None if candidate.path is None else os.fspath(candidate.path),
        "outcome": candidate.outcome,
    }


def _cache_document(resolution) -> dict[str, object]:
    if type(resolution) is oracle.OracleEnvironment:
        document: dict[str, object] = {
            "schema_version": _CACHE_SCHEMA_VERSION,
            "state": "success",
            "environment": {
                "compiler": os.fspath(resolution.compiler),
                "ccbench_dir": os.fspath(resolution.ccbench_dir),
                "dependency_root": os.fspath(resolution.dependency_root),
            },
            "failure": None,
        }
    elif type(resolution) is oracle.OracleEnvironmentResolutionFailure:
        document = {
            "schema_version": _CACHE_SCHEMA_VERSION,
            "state": "failure",
            "environment": None,
            "failure": {
                "detail_code": resolution.detail_code,
                "compiler_candidates": [
                    _candidate_document(item)
                    for item in resolution.compiler_candidates
                ],
                "dependency_candidates": [
                    _candidate_document(item)
                    for item in resolution.dependency_candidates
                ],
            },
        }
    else:
        raise TypeError("oracle cache requires an environment resolution union")
    _validate_cache_document(document)
    return document


def _candidate_from_document(document: object):
    _validate_candidate_document(document)
    assert isinstance(document, dict)
    path = document["path"]
    return oracle.OracleEnvironmentCandidate(
        document["origin"],
        None if path is None else Path(path),
        document["outcome"],
    )


def _cache_resolution(document: dict):
    _validate_cache_document(document)
    if document["state"] == "success":
        environment = document["environment"]
        assert isinstance(environment, dict)
        return oracle.OracleEnvironment(
            Path(environment["compiler"]),
            Path(environment["ccbench_dir"]),
            Path(environment["dependency_root"]),
        )
    failure = document["failure"]
    assert isinstance(failure, dict)
    return oracle.OracleEnvironmentResolutionFailure(
        failure["detail_code"],
        tuple(_candidate_from_document(item) for item in failure["compiler_candidates"]),
        tuple(_candidate_from_document(item) for item in failure["dependency_candidates"]),
    )


def _cache_load(
    path: Path,
    *,
    run_id: Optional[str],
    head: Optional[str],
    prewarm: bool,
    process_prewarmed: bool,
):
    try:
        if path.stat().st_size > _CACHE_MAX_BYTES:
            raise _CacheTooLarge(f"cache exceeds {_CACHE_MAX_BYTES} bytes")
        raw = path.read_bytes()
        if len(raw) > _CACHE_MAX_BYTES:
            raise _CacheTooLarge(f"cache exceeds {_CACHE_MAX_BYTES} bytes")
    except _CacheTooLarge as exc:
        raise OracleEnvironmentMemoError(
            "cache-size-limit", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    except Exception as exc:
        raise OracleEnvironmentMemoError(
            "cache-read-failed", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    try:
        document = json.loads(
            raw.decode("utf-8", "strict"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError, _CacheDecodeError, RecursionError, ValueError) as exc:
        raise OracleEnvironmentMemoError(
            "cache-json-decode-failed", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    try:
        return _cache_resolution(document)
    except (TypeError, ValueError, _CacheSchemaError, RecursionError) as exc:
        raise OracleEnvironmentMemoError(
            "cache-schema-invalid", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc


def _cache_store(path: Path, resolution) -> None:
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        raw = json.dumps(
            _cache_document(resolution),
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        if len(raw) > _CACHE_MAX_BYTES:
            raise _CacheTooLarge(f"cache exceeds {_CACHE_MAX_BYTES} bytes")
        temporary.write_bytes(raw)
        os.replace(temporary, path)
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def _prune_stale_caches(directory: Path, *, current_path: Optional[Path]) -> None:
    cutoff = time.time() - _CACHE_STALE_S
    try:
        entries = {
            entry
            for pattern in (
                f"{_CACHE_PREFIX}*.json",
                f"{_CACHE_PREFIX}*.json.pending",
                f"{_CACHE_PREFIX}*.json.failed",
                f"{_CACHE_PREFIX}*.json.lock",
            )
            for entry in directory.glob(pattern)
        }
    except OSError:
        return
    protected = {current_path} if current_path is not None else set()
    if current_path is not None:
        for suffix in (".lock", ".pending", ".failed"):
            protected.add(current_path.with_name(f"{current_path.name}{suffix}"))
    for entry in entries:
        if entry in protected:
            continue
        try:
            if entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            pass


class _OracleEnvironmentMemo:
    """Private capability object separating writer and reader endpoints."""

    def __init__(self, resolve: Optional[Callable[[], object]] = None) -> None:
        self._resolve_override = resolve
        self._process_resolution = _MISSING
        self._process_session_id = _SESSION_UNBOUND
        self._suspended_sessions: list[tuple[object, object]] = []
        self._early_ready_paths: set[str] = set()

    @property
    def process_prewarmed(self) -> bool:
        return self._process_resolution is not _MISSING

    def _error(
        self,
        reason: str,
        *,
        cache_path: Optional[Path],
        run_id: Optional[str],
        head: Optional[str],
        prewarm: bool,
        cause: Optional[BaseException] = None,
    ) -> OracleEnvironmentMemoError:
        return OracleEnvironmentMemoError(
            reason,
            cache_path=cache_path,
            run_id=run_id,
            head=head,
            prewarm=prewarm,
            process_prewarmed=self.process_prewarmed,
            cause=cause,
        )

    def _locked(
        self,
        path: Path,
        *,
        run_id: str,
        head: str,
        prewarm: bool,
        operation: Callable[[], object],
        deadline: Optional[float] = None,
    ):
        lock_path = path.with_name(f"{path.name}.lock")
        try:
            handle = open(lock_path, "a+b")
        except OSError as exc:
            raise self._error(
                "lock-open-failed", cache_path=path, run_id=run_id, head=head,
                prewarm=prewarm, cause=exc,
            ) from exc
        try:
            try:
                if deadline is None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                else:
                    while True:
                        if time.monotonic() >= deadline:
                            raise TimeoutError(errno.ETIMEDOUT, "memo publication timeout")
                        try:
                            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                            break
                        except OSError as exc:
                            if exc.errno not in (errno.EAGAIN, errno.EACCES):
                                raise
                            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
            except OSError as exc:
                try:
                    handle.close()
                except OSError:
                    pass
                raise self._error(
                    "lock-acquire-failed", cache_path=path, run_id=run_id,
                    head=head, prewarm=prewarm, cause=exc,
                ) from exc
            try:
                result = operation()
            except BaseException:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
                try:
                    handle.close()
                except OSError:
                    pass
                raise
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError as exc:
                try:
                    handle.close()
                except OSError:
                    pass
                raise self._error(
                    "lock-release-failed", cache_path=path, run_id=run_id,
                    head=head, prewarm=prewarm, cause=exc,
                ) from exc
            try:
                handle.close()
            except OSError as exc:
                raise self._error(
                    "lock-close-failed", cache_path=path, run_id=run_id,
                    head=head, prewarm=prewarm, cause=exc,
                ) from exc
            return result
        except OracleEnvironmentMemoError:
            raise

    def _resolve(self):
        return (
            self._resolve_override()
            if self._resolve_override is not None
            else _resolve_now()
        )

    def prewarm(
        self,
        *,
        run_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        if self._process_session_id is _SESSION_UNBOUND:
            self._process_session_id = session_id
        elif self._process_session_id != session_id:
            self._suspended_sessions.append((
                self._process_session_id,
                self._process_resolution,
            ))
            self._process_resolution = _MISSING
            self._process_session_id = session_id
        if self.process_prewarmed:
            return self._process_resolution

        if run_id is None:
            try:
                resolution = self._resolve()
                _cache_document(resolution)
            except BaseException as exc:
                if isinstance(exc, OracleEnvironmentMemoError):
                    raise
                raise self._error(
                    "resolver-failed", cache_path=None, run_id=None, head=None,
                    prewarm=True, cause=exc,
                ) from exc
            self._process_resolution = resolution
            return resolution

        run_id = str(run_id)
        head = _repo_head()
        if head is None:
            raise self._error(
                "cache-path-unavailable", cache_path=None, run_id=run_id,
                head=None, prewarm=True,
            )
        path = _session_cache_path(
            run_id=run_id, head=head, session_id=session_id,
        )
        if path is None:
            raise self._error(
                "cache-path-unavailable", cache_path=None, run_id=run_id,
                head=head, prewarm=True,
            )

        def write_once():
            if self.process_prewarmed:
                return self._process_resolution
            if path.exists():
                raise self._error(
                    "cache-preexists-before-prewarm", cache_path=path,
                    run_id=run_id, head=head, prewarm=True,
                )
            try:
                resolution = self._resolve()
            except BaseException as exc:
                if isinstance(exc, OracleEnvironmentMemoError):
                    raise
                raise self._error(
                    "resolver-failed",
                    cache_path=path,
                    run_id=run_id,
                    head=head,
                    prewarm=True,
                    cause=exc,
                ) from exc
            _prune_stale_caches(path.parent, current_path=path)
            try:
                _cache_store(path, resolution)
            except BaseException as exc:
                if isinstance(exc, OracleEnvironmentMemoError):
                    raise
                raise self._error(
                    "cache-store-failed",
                    cache_path=path,
                    run_id=run_id,
                    head=head,
                    prewarm=True,
                    cause=exc,
                ) from exc
            return resolution

        try:
            resolution = self._locked(
                path,
                run_id=run_id,
                head=head,
                prewarm=True,
                operation=write_once,
            )
        except OracleEnvironmentMemoError:
            raise
        except BaseException as exc:
            raise self._error(
                "cache-store-failed", cache_path=path, run_id=run_id,
                head=head, prewarm=True, cause=exc,
            ) from exc
        self._process_resolution = resolution
        return resolution

    def finish_session(self, *, session_id: Optional[str]) -> None:
        if self._process_session_id != session_id:
            raise RuntimeError(
                "oracle environment memo pytest session finish mismatch: "
                f"current={self._process_session_id!r} finished={session_id!r}"
            )
        self._process_resolution = _MISSING
        self._process_session_id = _SESSION_UNBOUND
        if self._suspended_sessions:
            self._process_session_id, self._process_resolution = (
                self._suspended_sessions.pop()
            )

    def get(self, *, early_job: Optional[str] = None, deadline: Optional[float] = None):
        """Read only the prewarmed process state or an existing cache document."""
        if self.process_prewarmed and early_job is None:
            return self._process_resolution

        run_id = os.environ.get(_RUN_ID_ENV)
        if run_id is None:
            raise self._error(
                "cache-path-unavailable", cache_path=None, run_id=None,
                head=None, prewarm=False,
            )
        session_id = os.environ.get(_SESSION_NONCE_ENV)
        if not isinstance(session_id, str) or not session_id:
            raise self._error(
                "cache-path-unavailable", cache_path=None, run_id=run_id,
                head=None, prewarm=False,
            )
        head = _repo_head()
        if head is None:
            raise self._error(
                "cache-path-unavailable", cache_path=None, run_id=run_id,
                head=None, prewarm=False,
            )
        path = _session_cache_path(
            run_id=run_id, head=head, session_id=session_id,
        )
        if path is None:
            raise self._error(
                "cache-path-unavailable", cache_path=None, run_id=run_id,
                head=head, prewarm=False,
            )

        pending = path.with_name(f"{path.name}.pending")
        failed = path.with_name(f"{path.name}.failed")
        if early_job is not None:
            if early_job != str(path):
                raise self._error(
                    "early-job-identity-mismatch", cache_path=path, run_id=run_id,
                    head=head, prewarm=False,
                )
            limit = time.monotonic() + _EARLY_WAIT_TIMEOUT_S
            deadline = limit if deadline is None else min(deadline, limit)

        def read_existing():
            if failed.exists():
                raise self._error(
                    "prewarm-failed", cache_path=path, run_id=run_id,
                    head=head, prewarm=False,
                )
            if early_job is not None and pending.exists():
                # Only reachable when a caller reuses this early reader. Production
                # waiting creates a reader and calls get once, so this branch cannot
                # protect that path. If the body disappears after publication, the
                # separate consumer reader fails via cache-missing below.
                if early_job in self._early_ready_paths:
                    raise self._error(
                        "publication-regressed", cache_path=path, run_id=run_id,
                        head=head, prewarm=False,
                    )
                return _MISSING
            if not path.exists():
                raise self._error(
                    "cache-missing", cache_path=path, run_id=run_id,
                    head=head, prewarm=False,
                )
            return _cache_load(
                path,
                run_id=run_id,
                head=head,
                prewarm=False,
                process_prewarmed=self.process_prewarmed,
            )

        while True:
            resolution = self._locked(
                path, run_id=run_id, head=head, prewarm=False,
                operation=read_existing, deadline=deadline if early_job is not None else None,
            )
            # Include read, unlock and close in the shared early-job deadline.
            if early_job is not None and time.monotonic() >= deadline:
                raise self._error(
                    "publication-timeout", cache_path=path, run_id=run_id,
                    head=head, prewarm=False,
                )
            if resolution is not _MISSING:
                if early_job is not None:
                    self._early_ready_paths.add(early_job)
                break
            if time.monotonic() >= deadline:
                raise self._error(
                    "publication-timeout", cache_path=path, run_id=run_id,
                    head=head, prewarm=False,
                )
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
        return resolution


def _make_oracle_environment_memo(
    resolve: Optional[Callable[[], object]] = None,
) -> _OracleEnvironmentMemo:
    """Create an isolated memo for unit tests without changing the singleton."""
    return _OracleEnvironmentMemo(resolve)


_ORACLE_ENVIRONMENT_MEMO = _make_oracle_environment_memo()


def prewarm_oracle_environment(
    *,
    run_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """Controller/serial collection-barrier writer endpoint."""
    return _ORACLE_ENVIRONMENT_MEMO.prewarm(
        run_id=run_id,
        session_id=session_id,
    )


def finish_oracle_environment_session(*, session_id: Optional[str]) -> None:
    """Discard process state at pytest session end."""
    _ORACLE_ENVIRONMENT_MEMO.finish_session(session_id=session_id)


def get_oracle_environment():
    """Consumer getter; cache miss and corruption never invoke the resolver."""
    return _ORACLE_ENVIRONMENT_MEMO.get()
