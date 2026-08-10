# -*- coding: utf-8 -*-
"""実 repo の T-080 receipt 解決を pytest process 内で 1 回に畳む test 支援 ([T-057])。

**なぜ必要か (実測)**: `t080_freeze_migration.verify_receipt(root=<実 repo>)` は 1 回
22.4 秒かかる (git subprocess 1845 本。うち `cat-file blob` 1607 本は異なる oid が 52 個
しかない重複で、コストは repo の commit 数 = 712 に比例する)。oracle driver 系テストは
`root=ROOT` を渡してこれを 50〜75 回払っており、計算ノードでの全走 327 秒に対し
duration 合計 3694 秒の 90% がこの解決だった。commit を積むほど遅くなる構造のため、
7/20 の全走 11 秒が 7/26 に 1811 秒へ悪化していた。

**受理集合を変えないための設計**:

- canned な `ReceiptResolution` を作らない。最初の miss は必ず本番の
  `verify_receipt(root=ROOT)` へ委譲し、戻り値を再構築・deepcopy せずそのまま返す。
  したがってテストが観測する値は memo 導入前と同一である。
- xdist では worker ごとに process が分かれるので、process memo だけだと worker 数だけ
  実解決が走る。`-n 32` では 32 本が同時に走って 1 回 22 秒が **129 秒**へ膨らむのを実測した。
  そのため session 限定 (xdist run ID + HEAD で key 付け) の cache を repo 外の一時領域へ置き、
  flock 下で 1 セッション 1 回に落とす。cache が読めない・型が違う場合は実解決へ倒す。
- ROOT 以外を渡されたら即 `AssertionError`。tmp repo / tamper 検出系へ patch が漏れた
  場合に「cached な valid 値で偽緑」にせず赤で止める (fail-closed)。
- patch 先は**テストが実際に import する module object** = `campaign.s8b_oracle_driver`。
  同じファイルでも `orchestrator.campaign.s8b_oracle_driver` は別 module object で、
  そちらを patch すると memo が 1 度も発火しない静かな空振りになる (実測で踏んだ)。
  この空振りは `test_s8b_binding_driftguards.py` の positive control が殺す。
- `mock.patch.object(..., side_effect=...)` の spy にするので、
  `driver._resolve_t080_receipt` の**呼び出し回数を観測しているテストの計数は壊れない**。
  畳むのは内側の実 `verify_receipt` だけである。

**使ってはいけない場所**: 解決の回数・世代差 (epoch drift)・tamper 検出そのものを検査対象に
しているテスト。memo はその機序を消してしまう。現在の該当は
`test_s8b_oracle_driver.py` の
`test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result` と
`test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4` の 2 関数で、
どちらも `_run(..., memo_receipt=False)` で明示的に opt-out する。
"""
from __future__ import annotations

import fcntl
import functools
import os
import pickle
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional
from unittest import mock

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_oracle_driver as driver  # noqa: E402
from orchestrator.campaign import t080_freeze_migration as migration  # noqa: E402

# import 時点の本番実装を捕まえる。`migration.verify_receipt` を直接呼ぶのではなく
# **本番の resolver そのもの**を memo することで、MigrationError → 構造化 refusal の翻訳を含めて
# 挙動が完全に一致する (memo 経由と patch 前で観測される値が同一)。
# patch は `driver._resolve_t080_receipt` を差し替えるが、ここで捕まえた参照は差し替え前の
# 本番実装なので再帰しない。
_PRODUCTION_RESOLVE = driver._resolve_t080_receipt


_RUN_ID_ENV = "PYTEST_XDIST_TESTRUNUID"
_CACHE_PREFIX = "izanagi-t057-receipt-"
_CACHE_STALE_S = 6 * 3600


def _resolve_now():
    """本番 resolver をそのまま 1 回呼ぶ (memo なし)。"""
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


def _session_cache_path() -> Optional[Path]:
    """xdist の 1 セッションに閉じた cache パス。非 xdist なら None。

    xdist では worker ごとに process が分かれるため、process memo だけでは worker 数だけ
    実解決が走る。**-n 32 では 32 本の解決が同時に走って 1 回 22 秒が 129 秒へ膨らむ**
    (計算ノードで実測)。これを 1 セッション 1 回へ落とすため、repo 外の一時領域へ
    session 限定の cache を置く。key は xdist の run ID + HEAD なので、別セッション・
    別 commit と混ざらない。
    """
    run_id = os.environ.get(_RUN_ID_ENV, "")
    if not re.fullmatch(r"[0-9a-zA-Z]{8,64}", run_id):
        return None
    head = _repo_head()
    if head is None:
        return None
    return Path(tempfile.gettempdir()) / f"{_CACHE_PREFIX}{run_id}-{head}.pickle"


def _cache_load(path: Path):
    """cache を読む。読めない・型が違うなら None (呼び出し側が実解決へ倒す)。"""
    try:
        value = pickle.loads(path.read_bytes())
    except Exception:
        return None
    return value if isinstance(value, migration.ReceiptResolution) else None


def _cache_store(path: Path, resolution) -> None:
    """同一 dir 内の tmp へ書いてから rename する (部分書き込みを読ませない)。"""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_bytes(pickle.dumps(resolution))
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass


def _prune_stale_caches(directory: Path) -> None:
    """古い session cache を捨てる (一時領域へ無限に溜めない)。"""
    cutoff = time.time() - _CACHE_STALE_S
    try:
        entries = list(directory.glob(f"{_CACHE_PREFIX}*"))
    except OSError:
        return
    for entry in entries:
        try:
            if entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            pass


@functools.lru_cache(maxsize=1)
def real_repo_receipt():
    """実 repo の T-080 receipt 解決。実評価は 1 process 1 回、xdist では 1 session 1 回。"""
    path = _session_cache_path()
    if path is None:
        return _resolve_now()
    lock = path.with_name(f"{path.name}.lock")
    try:
        handle = open(lock, "a+b")
    except OSError:
        return _resolve_now()
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        cached = _cache_load(path) if path.exists() else None
        if cached is not None:
            return cached
        resolution = _resolve_now()
        _prune_stale_caches(path.parent)
        _cache_store(path, resolution)
        return resolution
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def memo_resolver(*, root):
    """`driver._resolve_t080_receipt` と同じ signature の memo 経由 resolver。"""
    assert Path(root).resolve() == ROOT.resolve(), (
        "real-repo receipt memo を実 repo 以外へ適用してはならない "
        f"(tmp / tamper 経路への漏れ): {root}"
    )
    return real_repo_receipt()


def patch_driver_resolver():
    """`driver._resolve_t080_receipt` を memo 経由 wrapper へ差し替える context manager。"""
    return mock.patch.object(
        driver, "_resolve_t080_receipt", side_effect=memo_resolver,
    )
