---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: worktree-dev-wave-t1433-collection-cost
seq: 2
title: '[T-1433] xdist collection固定費 — controller-only/manifest共有はいずれも低リスク案なしと結論した (docsのみ、branch worktree-dev-wave-t1433-collection-cost)'
---

## 本文

- command 引数「48 workerが各12951件をcollectionする約26秒の固定費について、worker数変更以外の
  collection manifest共有またはcontroller-only案を、現行xdist契約を壊さない範囲で調査する」を受け、
  重複確認 (agent roster 20本・worktree一覧・handoff・T-870系列) では該当する稼働中/未land作業を
  検出しなかった (T-870系列は dispatch queue-wait/lease/nproc が対象で本件と無関係、
  T-1434 の `collect_run` は model軸実験の収集関数で pytest xdist collection とは無関係)。
- 親が xdist 3.8.0 のソース (`dsession.py`/`remote.py`/`workermanage.py`/
  `scheduler/{load,loadscope,loadgroup}.py`) を実地に読み、controller が
  `pytest_collection` hook で自身の collection を明示的に禁止していること
  (「controller-only」は現行実装の逆)、worker が実行時に worker-local `session.items` を
  必要とすること、`--dist loadgroup` の scheduler が全 worker の collected id 一覧の完全一致を
  要求することを確認し、両技法とも低リスクでは実現できないという暫定結論 (P1) を立てた。
- 段2 codex plan (read-only) が独立に file:line を再検証し、親の初回引用の一部が
  「後発 worker の照合」であり「初回全 worker 照合」の本体は別行 (load.py:309-335 等) だったと
  訂正したが、P1 の結論自体は支持した。BLOCKER 0。
- 段3 敵対相談 2 レンズ (レンズA=sol・正しさ境界、レンズB=luna・整合性/実効性/scope) はいずれも
  BLOCKER 0。レンズAは gateway 起動方式・collection-equality の型を独立に再検査し「抜け道なし」
  と補強。レンズBは MUST-FIX 3件 (file:line引用の訂正反映、D532の22〜25%は歴史的基準値と明示、
  DW-S04の段7前受入全走の明記) を検出し、いずれも採用・反映した。scope 逸脱
  (worker数変更・`IZANAGI_TEST_NPROC`・D585再提案) は無いと確認された。
- 段4裁定: **実装しない** ({{D:t1433-collection-manifest-no-low-risk}} 参照)。実装差分ゼロのため
  変異matrixは免除 (DW-S04)。受入全走は免除せず本fragment群のcommit後に親が投入する。
- 新発見: 現在のテスト collection 件数は 14104 件 (D532当時2026-08-18の12951件から+8.9%)。
  同日 serial collection (単発・Pegasus dispatch・cluster混雑下) は21.84秒で、D532当時の
  単一process 4.08秒から約5.4倍。件数増だけでは説明がつかないが、原因 (cluster混雑ノイズか
  conftest.py側の重量化か) は未確定であり、本waveのscope外として次の一手へ切り出す。
- dev-wave改善候補1件 (DW-S04の「受入全走は免除せず、実repoを読むテストは段7の記録前に実走」が
  1文に2手順を畳み込んでおり読み落としやすい。本wave自身も当初brief には言及がなく段3レンズBが
  検出) を記録のみに留めユーザー裁定へ返す (dev-wave docs 3層は予算満杯のため)。

## 次の一手差分

### 完了

- [T-1433] controller-only / collection manifest 共有はいずれも低リスク案なしと結論し記録した。
  worker数変更・`IZANAGI_TEST_NPROC`変更・D585再提案はいずれも行っていない。
  remaining: none
  base: 49fc520206cd545fe6383d78dfa06d7d9a58567e5ff34ed1aa2464fc19e4d4f8

### 新規

- {{T:collection-cost-current-remeasure}} **P3・新規**: 受入全走の xdist collection 固定費の
  現在値を再測定する。2026-08-18時点 (12951件・単一process 4.08秒・固定費約26秒/wall22〜25%、
  D532) から 2026-08-21時点 (14104件・serial 21.84秒、単発・混雑下・未確定) への変化が、
  cluster 混雑ノイズか `orchestrator/tests/conftest.py` 側の重量化 (top-level import・
  全item走査等) かを切り分ける。{{D:t1433-collection-manifest-no-low-risk}} が確定した
  「controller-only/manifest共有は低リスク案なし」は本項の結果によらず変わらない。
