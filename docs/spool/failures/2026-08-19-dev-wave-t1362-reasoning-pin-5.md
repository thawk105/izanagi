---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1362-reasoning-pin
seq: 5
---

## 新規

### {{F:s8c-preregistration-batch-limit-history-growth}}. s8c_preregistration の MAX_BATCH_REQUESTS を repo 履歴成長が超過し、無関係な wave の受入を赤にした [ドリフト]

- 事象: T-1362 の受入全走で `test_s8c_preregistration_invariant.py` の2テスト
  (`test_candidate_freeze_matches_contract_and_generation_chain`、
  `test_repository_tip_binds_current_decider_version_without_activation`) が赤になった。
  `orchestrator/campaign/s8c_preregistration.py:_batch_oids` の
  `len(commits) * len(paths) > MAX_BATCH_REQUESTS` (`MAX_BATCH_REQUESTS = 50_000`) を
  実測50072で超過していた。T-1362 は `orchestrator/campaign/s8c_preregistration.py` や
  関連docsを一切変更していない。
- 根本原因: `commits` は repo 履歴 (候補commitからの範囲) に比例して増える。main単独
  (`b7f7d934`) では合格、T-1362 の tip (`b7fd16d8`、main比 commit 7件追加) では失敗を
  直接実測した — 内容でなく commit 数の増加だけで超過している。main は既に限界のごく
  近傍にあり、次にlandする**どの** wave もこの形で赤を踏みうる。
- 恒久対応: 未着手。ユーザー裁定へ返した (worklog {{T:s8c-batch-limit-blocks-land}})。
  候補: (a) `MAX_BATCH_REQUESTS` を引き上げる、(b) `_batch_oids` の呼び出し側で対象範囲を
  絞る、(c) `test-time-regression-rule` に従い当該2テストを成長比例costとして恒久保留する。
  いずれも本 fragment の時点では未選択。
- 再発検知: 未実装。この2テストが受入全走で赤になった時点で本エントリへ「再発」を追記する
  運用に留める (機械的な事前検知は恒久対応と併せて設計する)。

## 再発

### F383

- **再発: 2026-08-19** — `tools/check_acceptance_reds.py` の probe worktree dispatch が、
  変異走行や tree 編集を伴わない単発起動 (T-1362 の受入非帰属判定、3回試行) でも
  3/3 の頻度で同型の `orphan-hold` (`job-may-remain-without-terminal-evidence`) に到達した。
  F383 が記録した根本原因 (変異走行中の docs 編集による共有木 byte 変化検出) は今回のトリガー
  ではなく、単発 dispatch そのもので発生している。復旧手順 (`qstat` 出力内容で不在確認 →
  probe worktree の clean/HEAD 確認 → 手動 qdel を使わず hold を削除) は F383 と同じ形で機能した。
