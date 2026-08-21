---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1414-dispatch-latch
seq: 1
title: '[T-1414] dispatch共有機構のorphan-hold latch条件を見直した (コード+テスト、branch worktree-dev-wave-t1414-dispatch-latch、変異matrix = baseline PASSED・6/6 KILLED (M2は訂正後2ノードで単一理由killと確認)・SURVIVED0・MISMATCH0)'
---

## 本文

- ユーザー裁定 (2026-08-19、推奨 (c) latch 条件自体を見直す) を実装した。段3 敵対相談
  (2レンズ) が段2 プランの前提を崩す real 所見を発見: メインループの `_scheduler_state()`
  が対象 request ID に束縛されない permissive parser であり、qstat が rc≠0 でも呼ばれる
  ため END を偶発誤判定しうる。段5 実装 (rc≠0 なら state 計算を一律抑制) は scope が
  広すぎ、既存テストの意図的な fault-tolerance 設計 (rc≠0 の RUN 状態文字列も
  bookkeeping では trust する) を回帰させた (親が実測で発見)。段6 fix1 で「END 判定結果
  だけ rc=0 を要求する」狭いガードへ差し替え、段6 敵対レビュー (2レンズ) が変異登録の
  精度不足を指摘、fix2 で補強した。
- 棄却 (refuted): T-1447 (別 ticket、3未防御 race) との相互作用悪化は段3・段6 で
  各々確認したが real ではない。`success-request-absent` の消極的性質 (対象不在の
  確証としては完全でない) は記録のみで対応せず — {{D:dispatch-latch-narrow-safe-relax}}。
- セッション異常: 段2 投入時、起動確認のタイミングを見誤り同一 job-id を二重投入。
  launcher の create-once 保護で実害なく回収 (foreign receipt を親が diff 監査で採択)。
  変異 matrix 実行中、queue 混雑 (`gen_S` 待ち40超・実行120超が持続) により orphan-hold
  2回・queue-wait-timeout 1回に遭遇、いずれも memory `mutation-harness-orphan-hold-recovery`
  の手順 (qstat 出力内容で不在確認・手動 qdel せず・hold 手動削除) で回収し、T-1414 の
  変更とは無関係な外乱と確認した。
- エージェント工数: codex 子 8体 (段2 plan×1, 段3 consult×2, 段5 author×1, 段6 fix×2,
  段6 review×2)。全て rc=0・`## 総括` 検査通過。

## 次の一手差分

### 完了

- [T-1414] dispatch 共有機構の orphan-hold latch 条件 (`_fresh_qstat_gated_qdel` の
  `denied()`) を、request-absent かつ terminal_history_end 確定済みの場合だけ緩める
  よう見直した。メインループの END 判定も rc=0 限定に補正し、既存 fault-tolerance
  設計 (RUN bookkeeping) は非破壊。変異matrix 6/6 期待どおり (M2 は実測に基づき
  expected_nodes を2件へ訂正)。受入は本 fragment 後に投入する。
  remaining: none
  base: 5d3de5b32ad530ab3f0b5cb1e1e8f3169cefe9e7e50096ce76eefa50ee53c35d
