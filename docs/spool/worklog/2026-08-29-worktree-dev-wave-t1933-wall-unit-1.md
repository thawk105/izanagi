---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: worktree-dev-wave-t1933-wall-unit
seq: 1
title: [T-1933] 受入 wall を決める単体処理は存在しないと確定した (docs-only、branch worktree-dev-wave-t1933-wall-unit、変異matrix免除)
---

## 本文

- ユーザー指示は「fixed-tip full artifact の critical worker で wall を実際に決める単体処理を先に同定し、
  同定結果が具体的な処理を 1 つ指し示した場合にだけその処理に閉じて短縮を実装する」。
  **同定は負で確定し、条件が成立しないので短縮は実装していない。** 実装面の差分は 0。
- 新しい受入走行は同定のために 1 本も投入していない。他 wave が過去に流した受入 artifact
  548 group を走査し、full 走 484 本を事後解析した。解析 script は repo 外の job dir に置き、
  生出力だけを insight へ保存した。
- 確定した結論は `makespan >= 最長 unit の所要` という定理だけに依存する。hold 有効の 4 走
  (同一 tip 2 組、tested_main `93fcb4663` と `c9f868ba`) で、critical shard の最長 unit を
  無料にしても makespan は次の unit を下回れず、差は 2.7〜19.3 秒。97 秒以上の unit が 10〜11 本、
  77 秒以上が 11〜22 本ある。D1260 の +0.37% はこの frontier の幅の帰結である。詳細は
  {{D:acceptance-wall-frontier}}。
- 上位 unit は 3 機構である。`test_s8c_preregistration_invariant.py` の module fixture
  (pathspec なし `git add -A`)、`test_s8c_preregistration_predicates.py` の C06 到達可能性探索、
  `test_s8b_oracle_driver.py` の T-080 stub-free e2e。最後のものは共有処理ではなく、
  同じコード経路を 10 本が独立に実行している (毎回 `shutil.copytree` で実体コピーを作る)。
- 結論は growth hold 有効という条件付きである。2026-08-29 01:52 を境に regime が交代しており、
  交代前の 26 走では `s8c-preregistration-candidate` loadgroup を無料にすると LPT makespan が
  中央値 57.9 秒縮んだ。hold 状態はどの同値キーにも入っていない。{{D:acceptance-wall-claims-need-hold-state}}。
- `wall − max_occ` は全 worker 非実行時間の**上界**である。この残差は universe 件数に対し
  1,000 件あたり 2.45 秒で伸びる (非 critical shard 675 本、universe 15,063〜18,895 件、r 0.490)。
  内訳は現 artifact では分解できない。login node の read-only 実測では単一 process の全件 collection が
  冷 42.78 秒 / 温 11.37 秒で、48 worker が独立に全 18,895 item を収集していることは
  `worker_collection_digests` が 48 要素同一 digest であることで裏取りした。
- 段 3 の 2 レンズが親の主張 9 件を反証し、親が実測で確認して撤回した。境界の向きの取り違え 2 件は
  {{F:bound-direction-unchecked}}、道具の切り詰め出力を分布として引用した件は F473 の再発として記録した。
- 段 2 プランが提案した report v2 の phase timeline と session milestone は不採用にした。
  本 wave の負結論を変えず、`brief.md` の scope と絶対規律 5 に反するためである。
  最小形 (`node_to_worker` 1 field) と、段 2 が独自定義した `0.9 <= ΔW/ΔU <= 1.1` gate の可否は
  裁定パッケージとしてユーザーへ返す。
- 実行しない方がよいこととして 3 件を記録した。現 regime での `s8c-preregistration-candidate` の
  `git add -A` 短縮 (group は 0.0 秒)、T-080 の一部 grouping (D1260 が不採用を確定)、
  x-for-x 比率を同定の必要条件にすること。
- 一次資料は `output/insights/2026-08-29_t1933-wall-unit/`。

## 次の一手差分

### 更新

- [T-1933] **P1**: 現行 tip・hold 有効では wall を決める単体処理は存在しない。97 秒以上の unit が
  10〜11 本並ぶ frontier であり、単一 node の短縮は makespan を動かさない ({{D:acceptance-wall-frontier}})。
  次に進めるなら 2 つの手番がある。(a) frontier 全体へ同時に効く短縮、すなわち T-080 stub-free e2e
  10 本が独立に払う実体コピーと verify の共通コード経路を、受理集合を変えずに安くする案を作る。
  (b) `wall − max_occ` の残差 (shard あたり 55 秒、1,000 item あたり 2.45 秒で成長) を分解する。
  (b) には report への nodeid → worker 対応の追加が要り、その可否はユーザー裁定待ちである。
  base: 4333dce802ed2290e1e385b3333079dad9293549e201dbb0ca660d49b83c07e2
