---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: worktree-quizzical-discovering-quasar
seq: 1
---

## 新規

### {{F:real-corpus-active-task-fixture-drift}}. real-corpus テストがアクティブな task_id を fixture anchor にすると、その task の実体更新で追随なしに陳腐化する [ドリフト] [手順漏れ]

- 事象: `orchestrator/tests/test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`
  が全体走で赤化した (13769 passed, 96 skipped 中でこの1件だけ FAILED)。テストは実 repo コーパスから
  直接 raw bytes を読んで `[T-139]` の実質的な (carry を遡った) 根 entry を独立に特定し、
  そのハッシュを期待値としていたが、テスト作成時点 (2026-08-13頃) 以降に `[T-139]` が実体更新され
  (2026-08-20、ordinal 720、D574 land)、根 entry が `docs/archive/worklog-phase3-0813-537.md` から
  `docs/archive/worklog-phase3-0820-720-721.md` へ移動したため、テストの固定ポインタ (ファイル名・
  開始マーカー文字列) が追随なしで陳腐化した。
- 根本原因: real-corpus テストが「まだ完了していない (`### 次の一手` で carry され続けている)」
  task_id を fixture anchor に選ぶと、そのアンカーは定義上いつ実体更新 (単純 carry でなく新しい
  実質的な書き直し) を受けてもおかしくない。実装 (`_extract_latest_active`/`substantive_digest`
  の carry chain 解決) は無変更で正しく動作しており、バグはテスト側の fixture ポインタにあった。
- 恒久対応: なし (機械検査は未整備。規律5 に基づき今回は追加機構を作らず、修正
  (commit `2b56f5ae`) は独立 raw byte 再計算による fixture ポインタの追随に留めた — 独立オラクル
  設計 (テストのロジックを再利用しない直接 byte 比較) は維持し、比較ロジック自体は変更していない)。
  当面は同種の real-corpus テストが赤化した際、まず「実装のバグ」でなく「fixture ポインタの陳腐化」
  を疑い、対象 archive ファイル内の該当 entry を独立 raw byte 計算で確認してから追随修正する。
  恒久対応の候補 (今回は実装しない、DW-G03 の独立2例未充足): fixture anchor に、既に完了して
  archive され二度と実体更新されない task_id を選ぶ設計へ変更する。
- 再発検知: 同型は、real-corpus テストがまだアクティブな task_id を fixture anchor に使っている
  場合に、その task_id が実体更新されるたびに顕在化しうる (lint 化は未整備、目視)。
