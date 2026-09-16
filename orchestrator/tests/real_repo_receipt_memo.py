# -*- coding: utf-8 -*-
"""実 repo の T-080 receipt を pytest session の固定 snapshot から読む支援。

receipt の production resolver は実 working tree と共有 submodule を走査する。pytest の
test body が走り始めてから最初の consumer が解決すると、並行 writer と観測時点が競合する。
この module は controller の collection barrier で一度だけ解決する ``prewarm`` 経路と、
その結果だけを読む consumer 経路を分離する。

受理集合は変えない。prewarm は production resolver の値を加工しない。固定 snapshot X に
対し、wire 往復後も値・型・bytes が意味的に同一な ``R(X)`` を同じ pytest session の全
consumer が観測する。prewarm 前の miss、cache/lock 障害、壊れた cache、store 障害は
production resolver へ倒さず ``ReceiptMemoError`` で fail-closed にする。report 経路には
到達するが、prewarm は本物の resolver を呼び、cache はロスレス往復するため、到達する値
自体は変わらない。

ROOT 以外は従来どおり拒否する。解決回数や epoch drift 自体を検査する test は
``memo_receipt=False`` でこの支援を使わない。
"""
from __future__ import annotations

import base64
import errno
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional
from unittest import mock

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_oracle_driver as driver  # noqa: E402
from orchestrator.campaign import t080_freeze_migration as migration  # noqa: E402

# import 時点の production resolver を捕まえる。patch 先と同じ参照を動的に読むと再帰する。
_PRODUCTION_RESOLVE = driver._resolve_t080_receipt

_RUN_ID_ENV = "PYTEST_XDIST_TESTRUNUID"
_SESSION_NONCE_ENV = "IZANAGI_RECEIPT_MEMO_NONCE"
_CACHE_PREFIX = "izanagi-t057-receipt-"
# Observed prewarm: 28.328 s (acceptance shard-0, n=1); 120 s is about
# 4.24 times that observation. With n=1 the tail is unknown. This is an
# upper bound we expect not to reach; reaching it is a failure.
_EARLY_WAIT_TIMEOUT_S = 120.0
_CACHE_STALE_S = 6 * 3600
_CACHE_MAX_BYTES = 8 * 1024 * 1024
_CACHE_SCHEMA_VERSION = 1
_CACHE_KEYS = frozenset({
    "schema_version",
    "state",
    "refusals",
    "t080_freeze_migration_observation",
    "validation_head",
    "introduction_commit",
    "receipt",
    "receipt_raw_b64",
    "held_checks",
})
_ERROR_PREFIX = "IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1 "
_MISSING = object()
_SESSION_UNBOUND = object()


class _CacheDecodeError(ValueError):
    """cache bytes are not strict UTF-8 JSON."""


class _CacheSchemaError(ValueError):
    """decoded cache JSON does not match the closed wire schema."""


class _CacheTooLarge(ValueError):
    """cache bytes exceed the bounded reader limit."""


class ReceiptMemoError(RuntimeError):
    """receipt memo の fail-closed 診断。message は canonical JSON。"""

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
        payload = {
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
                payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True,
            )
        )


def _resolve_now():
    """production resolver を呼ぶ唯一の低水準 seam。caller は prewarm だけ。"""
    return _PRODUCTION_RESOLVE(root=ROOT)


def _repo_head() -> Optional[str]:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, timeout=30, check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return out if re.fullmatch(r"[0-9a-f]{40}", out) else None


def _cache_path_for(run_id: str, head: str, session_id: str) -> Path:
    """UID と session nonce を拒否せず hash 化し、安全な JSON path を返す。"""
    uid_hash = hashlib.sha256(
        run_id.encode("utf-8", errors="surrogatepass")
    ).hexdigest()
    session_hash = hashlib.sha256(
        session_id.encode("utf-8", errors="surrogatepass")
    ).hexdigest()
    return Path(tempfile.gettempdir()) / (
        f"{_CACHE_PREFIX}{uid_hash}-{session_hash}-{head}.json"
    )


def _session_cache_path(
    *,
    run_id: Optional[str] = None,
    head: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Optional[Path]:
    """xdist session cache path。UID と nonce の内容は検査せず hash だけを使う。"""
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
    """JSON-native, finite, string-keyed tree only; no implicit repr/conversion."""
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


def _validate_cache_document(document: object) -> None:
    if not isinstance(document, dict) or set(document) != _CACHE_KEYS:
        raise _CacheSchemaError("cache envelope keys are not exact")
    schema_version = document["schema_version"]
    if type(schema_version) is not int or schema_version != _CACHE_SCHEMA_VERSION:
        raise _CacheSchemaError("cache schema_version is invalid")
    if not isinstance(document["state"], str):
        raise _CacheSchemaError("cache state is invalid")
    refusals = document["refusals"]
    if not isinstance(refusals, list) or not all(
        isinstance(value, str) for value in refusals
    ):
        raise _CacheSchemaError("cache refusals are invalid")
    validation_head = document["validation_head"]
    if not isinstance(validation_head, str):
        raise _CacheSchemaError("cache validation_head is invalid")
    introduction_commit = document["introduction_commit"]
    if introduction_commit is not None and not isinstance(introduction_commit, str):
        raise _CacheSchemaError("cache introduction_commit is invalid")
    for key in ("t080_freeze_migration_observation", "receipt"):
        value = document[key]
        if value is not None and (
            not isinstance(value, dict) or not _is_json_tree(value)
        ):
            raise _CacheSchemaError(f"cache {key} is invalid")
    raw_b64 = document["receipt_raw_b64"]
    if raw_b64 is not None:
        if not isinstance(raw_b64, str):
            raise _CacheSchemaError("cache receipt_raw_b64 is invalid")
        try:
            encoded = raw_b64.encode("ascii")
            decoded = base64.b64decode(encoded, validate=True)
        except (UnicodeError, ValueError) as exc:
            raise _CacheSchemaError("cache receipt_raw_b64 is invalid") from exc
        if base64.b64encode(decoded).decode("ascii") != raw_b64:
            raise _CacheSchemaError("cache receipt_raw_b64 is not canonical")
    held_checks = document["held_checks"]
    if not isinstance(held_checks, list) or any(
        not isinstance(value, dict) or not _is_json_tree(value)
        for value in held_checks
    ):
        raise _CacheSchemaError("cache held_checks are invalid")
    if not all(
        _is_json_tree(document[key])
        for key in ("state", "refusals", "validation_head", "introduction_commit")
    ):
        raise _CacheSchemaError("cache contains a non-JSON value")


def _cache_document(resolution) -> dict:
    if not isinstance(resolution, migration.ReceiptResolution):
        raise TypeError("receipt cache requires ReceiptResolution")
    receipt_raw = resolution.receipt_raw
    if receipt_raw is not None and not isinstance(receipt_raw, bytes):
        raise TypeError("receipt_raw must be bytes or None")
    raw_b64 = (
        base64.b64encode(receipt_raw).decode("ascii")
        if receipt_raw is not None else None
    )
    document = {
        "schema_version": _CACHE_SCHEMA_VERSION,
        "state": resolution.state,
        "refusals": list(resolution.refusals),
        "t080_freeze_migration_observation": (
            resolution.t080_freeze_migration_observation
        ),
        "validation_head": resolution.validation_head,
        "introduction_commit": resolution.introduction_commit,
        "receipt": resolution.receipt,
        "receipt_raw_b64": raw_b64,
        "held_checks": list(resolution.held_checks),
    }
    _validate_cache_document(document)
    return document


def _cache_resolution(document: dict):
    """Build the dataclass only after the complete envelope has been checked."""
    raw_b64 = document["receipt_raw_b64"]
    receipt_raw = (
        base64.b64decode(raw_b64.encode("ascii"), validate=True)
        if raw_b64 is not None else None
    )
    return migration.ReceiptResolution(
        state=document["state"],
        refusals=tuple(document["refusals"]),
        t080_freeze_migration_observation=(
            document["t080_freeze_migration_observation"]
        ),
        validation_head=document["validation_head"],
        introduction_commit=document["introduction_commit"],
        receipt=document["receipt"],
        receipt_raw=receipt_raw,
        held_checks=tuple(document["held_checks"]),
    )


def _cache_load(
    path: Path,
    *,
    run_id: Optional[str] = None,
    head: Optional[str] = None,
    prewarm: bool = False,
    process_prewarmed: bool = False,
):
    """bounded strict JSON cache を読み、wire 検証後にだけ resolution を構築する。"""
    try:
        if path.stat().st_size > _CACHE_MAX_BYTES:
            raise _CacheTooLarge(f"cache exceeds {_CACHE_MAX_BYTES} bytes")
        raw = path.read_bytes()
        if len(raw) > _CACHE_MAX_BYTES:
            raise _CacheTooLarge(f"cache exceeds {_CACHE_MAX_BYTES} bytes")
    except _CacheTooLarge as exc:
        raise ReceiptMemoError(
            "cache-size-limit", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    except Exception as exc:
        raise ReceiptMemoError(
            "cache-read-failed", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    try:
        text = raw.decode("utf-8", "strict")
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError, _CacheDecodeError, RecursionError) as exc:
        raise ReceiptMemoError(
            "cache-json-decode-failed", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    except ValueError as exc:
        raise ReceiptMemoError(
            "cache-json-decode-failed", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    try:
        _validate_cache_document(document)
    except (TypeError, _CacheSchemaError, RecursionError) as exc:
        raise ReceiptMemoError(
            "cache-schema-invalid", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed,
            cause=exc,
        ) from exc
    try:
        return _cache_resolution(document)
    except (TypeError, ValueError, UnicodeError) as exc:
        # This is defensive: all conversion inputs were validated above.
        raise ReceiptMemoError(
            "cache-schema-invalid", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc


def _cache_store(path: Path, resolution) -> None:
    """同一 directory の tmp へ書き、replace 失敗を握り潰さない。"""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
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
        tmp.write_bytes(raw)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def _prune_stale_caches(
    directory: Path, *, current_path: Optional[Path] = None,
) -> None:
    """古い JSON と旧 pickle residue を捨て、現 session key は触らない。"""
    cutoff = time.time() - _CACHE_STALE_S
    try:
        entries = {
            entry
            for pattern in (
                f"{_CACHE_PREFIX}*.json",
                f"{_CACHE_PREFIX}*.json.pending",
                f"{_CACHE_PREFIX}*.json.failed",
                f"{_CACHE_PREFIX}*.pickle",
                f"{_CACHE_PREFIX}*.pickle.lock",
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


class _ReceiptMemo:
    """prewarm writer と consumer reader を能力として分けた private memo。"""

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
    ) -> ReceiptMemoError:
        return ReceiptMemoError(
            reason, cache_path=cache_path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=self.process_prewarmed,
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
        lock = path.with_name(f"{path.name}.lock")
        try:
            handle = open(lock, "a+b")
        except OSError as exc:
            raise self._error(
                "lock-open-failed", cache_path=path, run_id=run_id,
                head=head, prewarm=prewarm, cause=exc,
            ) from exc
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

    def prewarm(
        self,
        *,
        run_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """production resolver を呼べる唯一の経路。成功後だけ process state を公開する。"""
        # pytest.main() は同じ process へ複数 session を再入できる。config ごとの
        # token が変わったら、前 session の snapshot を読める状態を先に捨てる。
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
                resolution = (
                    self._resolve_override()
                    if self._resolve_override is not None
                    else _resolve_now()
                )
            except Exception as exc:
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
                resolution = (
                    self._resolve_override()
                    if self._resolve_override is not None
                    else _resolve_now()
                )
            except Exception as exc:
                raise self._error(
                    "resolver-failed", cache_path=path, run_id=run_id,
                    head=head, prewarm=True, cause=exc,
                ) from exc
            _prune_stale_caches(path.parent, current_path=path)
            try:
                _cache_store(path, resolution)
            except Exception as exc:
                raise self._error(
                    "cache-store-failed", cache_path=path, run_id=run_id,
                    head=head, prewarm=True, cause=exc,
                ) from exc
            return resolution

        resolution = self._locked(
            path, run_id=run_id, head=head, prewarm=True,
            operation=write_once,
        )
        self._process_resolution = resolution
        return resolution

    def finish_session(self, *, session_id: Optional[str]) -> None:
        """終了 session の state を捨て、入れ子なら外側 session を復元する。"""
        if self._process_session_id != session_id:
            raise RuntimeError(
                "receipt memo pytest session finish mismatch: "
                f"current={self._process_session_id!r} finished={session_id!r}"
            )
        self._process_resolution = _MISSING
        self._process_session_id = _SESSION_UNBOUND
        if self._suspended_sessions:
            (
                self._process_session_id,
                self._process_resolution,
            ) = self._suspended_sessions.pop()

    def get(self, *, early_job: Optional[str] = None, deadline: Optional[float] = None):
        """prewarm 済み process state または既存 session cache だけを読む。"""
        if self.process_prewarmed and early_job is None:
            return self._process_resolution

        run_id = os.environ.get(_RUN_ID_ENV)
        if run_id is None:
            raise self._error(
                "cache-path-unavailable", cache_path=None, run_id=None,
                head=None, prewarm=False,
            )
        head = _repo_head()
        if head is None:
            raise self._error(
                "cache-path-unavailable", cache_path=None, run_id=run_id,
                head=None, prewarm=False,
            )
        path = _session_cache_path(run_id=run_id, head=head)
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
                path, run_id=run_id, head=head, prewarm=False,
                process_prewarmed=self.process_prewarmed,
            )

        while True:
            resolution = self._locked(
                path, run_id=run_id, head=head, prewarm=False,
                operation=read_existing, deadline=deadline if early_job is not None else None,
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
        self._process_resolution = resolution
        return resolution


def _make_receipt_memo(
    resolve: Optional[Callable[[], object]] = None,
) -> _ReceiptMemo:
    """共有 singleton を汚さず検査できる private memo factory。"""
    return _ReceiptMemo(resolve)


_RECEIPT_MEMO = _make_receipt_memo()


def prewarm_real_repo_receipt(
    *,
    run_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """pytest controller/serial collection barrier から呼ぶ writer endpoint。"""
    return _RECEIPT_MEMO.prewarm(run_id=run_id, session_id=session_id)


def finish_real_repo_receipt_session(*, session_id: Optional[str]) -> None:
    """pytest unconfigure から呼び、process state を session 境界で破棄する。"""
    _RECEIPT_MEMO.finish_session(session_id=session_id)


def real_repo_receipt():
    """test consumer 用 read-only endpoint。miss から実解決しない。"""
    return _RECEIPT_MEMO.get()


def memo_resolver(*, root):
    """``driver._resolve_t080_receipt`` と同じ signature の consumer endpoint。"""
    assert Path(root).resolve() == ROOT.resolve(), (
        "real-repo receipt memo を実 repo 以外へ適用してはならない "
        f"(tmp / tamper 経路への漏れ): {root}"
    )
    return real_repo_receipt()


def patch_driver_resolver():
    """test が import する canonical driver module を consumer endpoint へ差し替える。"""
    return mock.patch.object(
        driver, "_resolve_t080_receipt", side_effect=memo_resolver,
    )
