# -*- coding: utf-8 -*-
"""実 repo の T-080 receipt を pytest session の固定 snapshot から読む支援。

receipt の production resolver は実 working tree と共有 submodule を走査する。pytest の
test body が走り始めてから最初の consumer が解決すると、並行 writer と観測時点が競合する。
この module は controller の collection barrier で一度だけ解決する ``prewarm`` 経路と、
その結果だけを読む consumer 経路を分離する。

受理集合は変えない。prewarm が保存するのは production resolver の戻り object そのもので、
canned 値や deepcopy は作らない。固定 snapshot X に対し、同じ pytest session の全 consumer
が同じ ``R(X)`` を観測する。prewarm 前の miss、cache/lock 障害、壊れた cache、store 障害は
production resolver へ倒さず ``ReceiptMemoError`` で fail-closed にする。

ROOT 以外は従来どおり拒否する。解決回数や epoch drift 自体を検査する test は
``memo_receipt=False`` でこの支援を使わない。
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import pickle
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
_CACHE_PREFIX = "izanagi-t057-receipt-"
_CACHE_STALE_S = 6 * 3600
_ERROR_PREFIX = "IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1 "
_MISSING = object()
_SESSION_UNBOUND = object()


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


def _cache_path_for(run_id: str, head: str) -> Path:
    """任意の xdist UID を拒否せず、内容 hash だけを安全な file 名へ使う。"""
    uid_hash = hashlib.sha256(
        run_id.encode("utf-8", errors="surrogatepass")
    ).hexdigest()
    return Path(tempfile.gettempdir()) / (
        f"{_CACHE_PREFIX}{uid_hash}-{head}.pickle"
    )


def _session_cache_path(
    *, run_id: Optional[str] = None, head: Optional[str] = None,
) -> Optional[Path]:
    """xdist session cache path。UID の内容は検査せず hash だけを使う。"""
    if run_id is None:
        run_id = os.environ.get(_RUN_ID_ENV)
    if run_id is None:
        return None
    if head is None:
        head = _repo_head()
    if head is None:
        return None
    return _cache_path_for(run_id, head)


def _cache_load(
    path: Path,
    *,
    run_id: Optional[str] = None,
    head: Optional[str] = None,
    prewarm: bool = False,
    process_prewarmed: bool = False,
):
    """cache を strict に読む。read、pickle、型不一致を構造化して拒否する。"""
    try:
        raw = path.read_bytes()
    except Exception as exc:
        raise ReceiptMemoError(
            "cache-read-failed", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    try:
        value = pickle.loads(raw)
    except Exception as exc:
        raise ReceiptMemoError(
            "cache-unpickle-failed", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed, cause=exc,
        ) from exc
    if not isinstance(value, migration.ReceiptResolution):
        raise ReceiptMemoError(
            "cache-type-invalid", cache_path=path, run_id=run_id, head=head,
            prewarm=prewarm, process_prewarmed=process_prewarmed,
        )
    return value


def _cache_store(path: Path, resolution) -> None:
    """同一 directory の tmp へ書き、replace 失敗を握り潰さない。"""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_bytes(pickle.dumps(resolution))
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
    """古い pickle cache だけを捨て、lock と現 session key は触らない。"""
    cutoff = time.time() - _CACHE_STALE_S
    try:
        entries = list(directory.glob(f"{_CACHE_PREFIX}*.pickle"))
    except OSError:
        return
    for entry in entries:
        if current_path is not None and entry == current_path:
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
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
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
        path = _session_cache_path(run_id=run_id, head=head)
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

    def get(self):
        """prewarm 済み process state または既存 session cache だけを読む。"""
        if self.process_prewarmed:
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

        def read_existing():
            if not path.exists():
                raise self._error(
                    "cache-missing", cache_path=path, run_id=run_id,
                    head=head, prewarm=False,
                )
            return _cache_load(
                path, run_id=run_id, head=head, prewarm=False,
                process_prewarmed=self.process_prewarmed,
            )

        resolution = self._locked(
            path, run_id=run_id, head=head, prewarm=False,
            operation=read_existing,
        )
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
