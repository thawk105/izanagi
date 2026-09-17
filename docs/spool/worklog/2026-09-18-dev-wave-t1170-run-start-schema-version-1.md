---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t1170-run-start-schema-version
seq: 1
title: [T-1170] 自律試行 journal `run-start` の版を完全性 consumer が独立に持つ世代定数で読むよう改版追随した — v5 へは上げず 4c6f03048 の v4 を既存の版境界として利用、拒否理由に記録版・世代・対応版を明示、受理集合は v4 のみで不変 (コード + テスト + docs、branch worktree-dev-wave-t1170-run-start-schema-version、焦点走 1638 passed、変異 matrix = baseline PASSED・負例 4/4 KILLED 期待 node 完全一致 (5 / 209 / 5 / 1)・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-1170] (D1898、ユーザー裁定) 自律試行 journal の `run-start` の schema 版を上げる改版追随を実装する — 記録済み artifact と現行 producer の世代を分け、consumer 6 本 (attempt_registry_core / autonomous_trial_completeness / p3_autonomous_workload_trial / s8b_attempt_profile / s8b_floor_attempt_launcher / s8b_attempt_registry) を追随させる。互換層は足さず、旧 record は旧版として読む。Codex author (D95) + 変異 matrix。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の改版追随だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-18/t1170-run-start-schema-version/README.md`。設計判断は {{D:run-start-consumer-owned-schema-generation}}、F332 の副次的所見へ supersede 追記。
- **依頼の前提を 2 点訂正した (段 1 実測、段 3 の 2 レンズが裏取り)。** (1) D1898 (09-09) が求めた版上げは、T-304 (09-16、4c6f03048) が role payload の key 改名で共有定数 `SCHEMA_VERSION` を v4 へ上げた際に run-start 側にも実体化しており、v4 の run-start は 1 つの形しか持たない。本 wave は v5 へ上げず、この v4 を既存の版境界として利用した (T-304 が本件を完了したとは記録しない)。(2) 依頼が挙げる 6 本のうち attempt_registry_core / s8b_attempt_profile / s8b_floor_attempt_launcher / s8b_attempt_registry の 4 本は lifecycle の `run_start_receipt_sha256` しか触らず、journal `run-start` の版を読む consumer ではない (6 本は `run-start|run_start` の grep hit の先頭 6 件と一致)。版を直接照合する consumer は `autonomous_trial_completeness._check_run_envelope` の 1 箇所で、trial_registry / s8c_acceptance_receipt は field を読むが版を見ない (版 gate の追加は仮想リスク向けとして scope 外)。
- 実装 (Codex author 1 本): consumer 所有の独立リテラル `_RUN_START_SCHEMA_VERSION` (v4) を追加し、producer の生きた定数との照合をやめた。拒否理由は `run-start.schema_version unsupported: recorded=…; generation=legacy|unknown; consumer_supported=…` (legacy は v3 の文字列 exact 一致だけ。例外文言内の明示であり機械可読属性の追加ではない)。受理集合は v4 のみで不変、旧版の変換・alias・decoder なし (v3 の記録済み artifact は repo 内に 1 本 = `output/insights/2026-08-15_t1097-s8c-live-abc/verbatim/attempts.jsonl` 13 key 旧形、直接参照の検索で読み手は確認できず D1669 条件不成立)。世代診断は版 gate に到達した記録に対する保証で、report 版・journal hash・event 順序の検査が先行する。producer・report 版検査は無変更。
- test: 既存 2 node の run-start 側期待を全文一致へ、新規 4 node (v4・binding 無し正例 = D1851 の正例、v3 旧形 13 key 負例、未知版負例、producer 定数を別値にしても v4 記録の判定が変わらない独立性正例)。独立性正例は段 3 レンズ B の must-fix (右辺を producer 定数へ戻す退行を変異が検出できない) で追加した。
- 段 3: レンズ A must-fix 0 / nit 3、レンズ B must-fix 1 / nit 4、すべて採用。段 6: レンズ A must-fix 0 / code nit 0 (台帳の書き方 3 点)、レンズ B must-fix 0 / nit 3 (docs fragment の表現訂正 = F332 追記の分類説明・D2064 決定 3 の適用範囲・読み手探索の範囲、すべて採用)。code の所見ゼロなので fix 子は起動せず、DW-M02 に従い変異で裏取りした。
- 実走: Codex author 自走 295 passed。親の焦点走 (completeness の importer 14 file、計算ノード dispatch 4989.nqsv) 1638 passed / 5 skipped。変異 matrix (container `.codex/worktrees/t1170-mutcontainer` HEAD 1941828e1、runner = completeness + producer の test 2 file を dispatch): probe 走 (全件 SURVIVED 登録) で観測 node を集め、本走で期待 node に写した。本走 = baseline PASSED、KILLED 4 (M1 版検査削除 5 node / M2 対応版を v3 へ 209 node / M3 legacy⇄unknown 5 node / M4 比較右辺を producer 定数へ戻す 1 node = 独立性 test)、等価対照 M0 (comment) SURVIVED、MISMATCH 0、期待 node 完全一致。M1 の旧形 v3 node は拒否理由が後段 (generation_driver) へ移ることの検出であって受理拡大の検出ではなく、M2 は複数の診断期待が同時に壊れる (単一理由に集約しない)。test 自体は 1 走 38〜48 秒、queue 待ち込みで最長 425 秒。受入全走は最終 tip で land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 0、全段 `gpt-6-astra` / `medium`)。計算ノード job: 焦点走 1 + 変異 12 走 (probe 6 + 本走 6)。受入全走は最終 tip で 1 回。

## 次の一手差分

### 完了

- [T-1170] 完全性 consumer の run-start 版検査を consumer 所有の世代定数へ替え、拒否理由に記録版・世代・対応版を明示した。v5 へは上げず 4c6f03048 の v4 を版境界として利用。詳細は {{D:run-start-consumer-owned-schema-generation}}。
  remaining: none
  base: 4e21b29c24408e44eec8d02b605948876d5fae9d968364654dc9247edfa9a49e
