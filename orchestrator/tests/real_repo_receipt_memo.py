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

import functools
import sys
from pathlib import Path
from unittest import mock

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
if str(ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR))

from campaign import s8b_oracle_driver as driver  # noqa: E402
from campaign import t080_freeze_migration as migration  # noqa: E402


@functools.lru_cache(maxsize=1)
def real_repo_receipt():
    """実 repo の T-080 receipt 解決。process 内で実評価はちょうど 1 回。"""
    return migration.verify_receipt(root=ROOT)


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
