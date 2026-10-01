# -*- coding: utf-8 -*-
"""ベンチ排他ロック (orchestrator-design.md I: Isolation)。

性能ベンチは同一マシンで並列実行すると CPU/cache/メモリ帯域を奪い合い測定が歪む
(観測者効果の延長、絶対規律1)。ロック設計:
  ビルド:     並列 OK (admission control 下)
  trace 検証: 並列 OK
  性能ベンチ: **排他**。実行中は他のベンチを止める

Phase 1 は直列実行なので自明に満たされるが、**Phase 2 で並列化する際にロックを入れる
前提でコードを構造化**する (orchestrator-design.md Phase1 反映 3)。既定ロックは
同一ノード・同一 UID の協調するプロセスが campaign / worktree / job を跨いで
共有する固定パスに置く。ノード専有・他ユーザー・異なる明示 override 間の排他は
保証しない。
"""
from __future__ import annotations

import errno
import fcntl
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional


def default_lock_path() -> str:
    """同一ノード・同一 UID の協調プロセス間のベンチ排他に使う固定パス。

    非空の IZANAGI_BENCH_LOCK はその値をそのまま返す。未設定・空文字なら
    /tmp/izanagi-bench-<uid>.lock。HOME や job ごとの TMPDIR に依存せず、
    ディレクトリも作成しない。ノード専有・他ユーザー・異なる明示 override
    間の排他は保証しない。
    """
    p = os.environ.get("IZANAGI_BENCH_LOCK")
    if p:
        return p
    return f"/tmp/izanagi-bench-{os.getuid()}.lock"


class BenchBusy(Exception):
    """非ブロッキング取得で、別プロセスがベンチ実行中だった。"""


@contextmanager
def bench_lock(path: Optional[str] = None, blocking: bool = True) -> Iterator[None]:
    """ベンチ critical section を排他で囲む。

    blocking=True なら他のベンチが終わるまで待つ。False なら取得できなければ
    即 BenchBusy (並列化後に「今ベンチ中だからビルドを先にやる」等の判断に使う)。
    fcntl.flock の advisory lock = 同じパスを flock する全プロセス間で相互排他。
    """
    path = path or default_lock_path()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o644)
    flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
    try:
        try:
            fcntl.flock(fd, flags)
        except OSError as e:
            if not blocking and e.errno in (errno.EAGAIN, errno.EACCES):
                raise BenchBusy(f"別プロセスがベンチ実行中: {path}")
            raise
        try:
            os.utime(fd)
        except OSError:
            pass
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


class CampaignBusy(Exception):
    """非ブロッキング取得で同一 campaign の実行中だった。"""


@dataclass
class HeldCampaignLock:
    path: str
    pid: int
    held: bool = True


@contextmanager
def campaign_lock(path: str, blocking: bool = False) -> Iterator[HeldCampaignLock]:
    """1 campaign の実行所有権を advisory flock で取得する。"""
    flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
    open_flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, open_flags, 0o644)
    try:
        try:
            fcntl.flock(fd, flags)
        except OSError as exc:
            if not blocking and exc.errno in (errno.EAGAIN, errno.EACCES):
                raise CampaignBusy(f"campaign lock が使用中: {path}")
            raise
        handle = HeldCampaignLock(path=path, pid=os.getpid())
        try:
            yield handle
        finally:
            handle.held = False
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
