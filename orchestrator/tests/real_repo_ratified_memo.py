# -*- coding: utf-8 -*-
"""実 repo の active 世代解決を pytest process 内で 1 回に畳む test 支援 ([T-117])。

**なぜ必要か (実測)**: `s8b_ratified_freeze.load_ratified_freeze(root=<実 repo>)` は
1 回 4.4 秒かかる。内訳は `resolve_active_generation` → `_collect_records` →
`_immutable_introductions` → `_blob_oid_by_commit` で、record path 16 本それぞれについて
`git cat-file --batch-check` を全 commit 分 (712 本) 流す 39 本の git subprocess である
(計算ノード bnode005 で cProfile 実測、`output/insights/2026-07-27_t117-real-repo-loadgroup.md`)。
receipt 解決 ([T-057]) と同じく **commit を積むほど遅くなる**構造で、real-repo loadgroup の
直列 69 秒のうち 4 node × 4.4 秒 = 17.6 秒がこの重複だった。

**受理集合を変えないための設計** (receipt memo `real_repo_receipt_memo` と同型):

- canned な `RatifiedFreeze` も canned な例外も作らない。最初の miss は必ず本番
  `load_ratified_freeze(ROOT)` へ委譲し、戻り値 (または送出された例外 object) を
  再構築せずそのまま返す/再送出する。したがってテストが観測する値・例外型・reason・
  message は memo 導入前と同一である。g1 発効後の実 repo では本番 loader が
  成功し `RatifiedFreeze` を返す (memo は成功値もそのまま cache する)。consumer 側の
  refusal は後続の launch validation 由来であり、その検証を memo は畳まない。
- `Exception` を型を問わず捕まえて同じ object を再送出する。本番 `gate_check` /
  `run_block` は `RatifiedFreezeError` と他 `Exception` で refusal 文字列を書き分ける
  ため、型を落とすと refusal が変わってしまう。
- ROOT 以外を渡されたら即 `AssertionError`。tmp repo / tamper 経路へ patch が漏れたとき
  「cached な実 repo 結果で偽緑」にせず赤で止める (fail-closed)。
- patch 先は**本番 driver が保持している module object** = `driver.s8b_ratified_freeze`。
  同じファイルでも `orchestrator.campaign.s8b_ratified_freeze` は別 module object で、
  そちらを patch すると memo が 1 度も発火しない静かな空振りになる ([T-057] で実測した罠)。
  この空振りは `test_s8b_binding_driftguards.py` の positive control が殺す。
- xdist の session 跨ぎ cache は**持たない**。opt-in する 4 node だけは shard marker に加えて
  最終 ``@real-repo`` suffix も保持し、単一 worker = 単一 process に居るので process memo で
  足りる。それ以外の real-repo resource node は suffix を外して worker 間へ分散する。
  receipt memo が session cache を要したのは consumer が 50〜75 node・多 worker に散るため。
  長寿命 fixture の ``s8c-preregistration-candidate``、``s8c-predicate-snapshot``、
  ``campaign-repository-scan`` はこの process memo 群へ統合しない。各 fixture の既存寿命を
  一 worker に閉じる別 loadgroup とし、resource 衝突は shard component の明示辺で同一 shard
  へ置く。したがって 4 node という process memo の exact 集合は変わらない。
- **正規注入 seam を使えないことの確認 (D78 / DW-O14)**: `gate_check` には
  `ratified=` / `ratified_error=` 引数があるが、`ratified_error` を渡す枝は
  `_make_gate_decision` で早期 return し `_gate_check_core` の floor/budget/manifest
  refusal を積まない別経路である。`run_block` には注入引数が無い (自身で解決する)。
  どちらも観測される refusal 集合が変わるため seam では代替できず、module 属性の
  差し替えが唯一の等価な畳み方である。

**使ってはいけない場所**: 実 repo の active 世代解決そのもの (履歴走査・record 連鎖・
承認検証・実解決成功後の launch validation 拒否翻訳) を検査対象にしているテスト。現在の該当は
`test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused` で、
この node は **memo を使わない正本 payer** として実解決を毎 session 必ず 1 回走らせる
(node 順序に依らず実走査の検出力を保つ)。この不変条件は
`test_real_repo_serialization.py::test_ratified_memo_has_a_real_resolution_payer` が機械固定する。
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path
from typing import Tuple
from unittest import mock

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_oracle_driver as driver  # noqa: E402

# import 時点の本番 loader を捕まえる。patch は `driver.s8b_ratified_freeze` の属性を
# 差し替えるが、ここで捕まえた参照は差し替え前の本番実装なので再帰しない。
_PRODUCTION_LOAD = driver.s8b_ratified_freeze.load_ratified_freeze


def new_outcome_cache(loader):
    """`loader(ROOT)` の結果 (値 or 例外) を 1 回だけ確定する cache を作る。

    positive control が共有 memo を evict しないための factory である。control は
    `_outcome` を stub 由来の**別 cache** へ差し替えて検査し (monkeypatch の復元で
    実 repo の warm entry がそのまま残る)、共有 cache を `cache_clear()` しない。
    clear してしまうと、同一 worker に居る opt-in node が 4.4 秒を再び払う。
    """
    @functools.lru_cache(maxsize=1)
    def outcome() -> Tuple[str, object]:
        try:
            return ("value", loader(ROOT))
        except Exception as exc:  # noqa: BLE001 (例外も観測値なのでそのまま保持する)
            return ("error", exc)

    return outcome


_outcome = new_outcome_cache(lambda root: _PRODUCTION_LOAD(root))


def real_repo_ratified():
    """実 repo の active 世代解決。実評価は 1 process 1 回。

    本番が返した object をそのまま返し、本番が送出した例外 object をそのまま再送出する。
    """
    kind, payload = _outcome()
    if kind == "error":
        raise payload
    return payload


def memo_loader(root=ROOT):
    """`load_ratified_freeze` と同じ signature の memo 経由 loader。"""
    assert Path(root).resolve() == ROOT.resolve(), (
        "real-repo active 世代 memo を実 repo 以外へ適用してはならない "
        f"(tmp / tamper 経路への漏れ): {root}"
    )
    return real_repo_ratified()


def patch_ratified_loader():
    """`driver.s8b_ratified_freeze.load_ratified_freeze` を memo へ差し替える CM。"""
    return mock.patch.object(
        driver.s8b_ratified_freeze, "load_ratified_freeze", side_effect=memo_loader,
    )
