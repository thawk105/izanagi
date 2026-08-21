---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t425-floor-bounded-prep
seq: 1
title: between_run_floor.py の入力検証・receipt schema・screening接続を bounded 実装した (コード+テスト、branch worktree-dev-wave-t425-floor-bounded-prep、変異matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 段2 codex plan・段3 敵対レンズ2本 (レンズA=正確性、レンズB=設計論・DW-G03) が実装前の材料を
  提供した。レンズAが「`screening_driver.py` だけが実 consumer ではなく `layer3_report.py` も
  calibration JSON を直接走査する」という訂正を発見した (段4裁定・実装 commit 本文に反映済み。
  実測では新規キー追加はこの consumer を壊さないため production 変更は不要、回帰 test 1件のみ
  追加)。設計判断は {{D:t425-floor-schema-lightweight}}。
- 段6敵対レビュー2本が real 所見2件 (M2テストの辞書キー順序への過剰依存、M4のnull/空文字列
  schema_versionの直接test不足) を検出し、fix子がテストのみで是正した (production変更なし)。
  fix後の焦点再レビュー (DW-S06-C) で両所見とも closed を確認した。
- 変異matrix (M1, M2, M3a, M3b, M4, M5a, M5b の7件) は baseline PASSED・7/7 KILLED・
  SURVIVED 0・MISMATCH 0。DW-M08 (M5=テスト強化のみの項目の新旧両走証跡) は
  `tools/mutation_worktree.py` 経由の harness 本走 (pid 1941927) が原因不明で早期終了した
  (`.done` 未生成、システム全体のメモリは十分空きあり、二次確認のため深追いはしなかった)。
  代わりに worktree 内で旧commit (`4a2543f0`) の2ファイルへ一時差替え→M5相当の変異を注入→
  旧テスト一式を実走→`git checkout --` で復元、という軽量な直接検証で同等の証拠を得た:
  旧テスト一式 (3件、M5相当のtestを含まない) は `3 passed, 0 failed` = 変異を検出せず。
  新テストだけが検出する差分であることを実測で確認した。
- 親が実走した焦点走 (test_between_run_floor.py, test_screening_driver.py,
  test_layer3_report.py, test_campaign.py): 481 passed, 9 skipped, 0 failed
  (Pegasus dispatch, request 928678.nqsv)。`python3 tools/check_ai_provenance.py` は
  rc=0・新規違反なし (既知47件のみ)。
- T-424 (override実行bytes束縛・interpreter/perf node gate・将来consumer設計) と
  T-272 (certify/submit経路のinterpreter版数gate) の残余は未閉包のまま、本waveでは触れていない
  (2026-08-20監査を継承、job-result.jsonへのhash伝播部分だけは commit `4e90b767` で既に closed)。

## 次の一手差分

### 更新

- [T-425] **P1・bounded実装完了 (2026-08-21)**: between_run_floor.py の入力検証・receipt
  schema・screening接続を bounded 実装した (コード+テスト、branch
  worktree-dev-wave-t425-floor-bounded-prep、変異matrix = baseline PASSED・7/7 KILLED・
  SURVIVED0・MISMATCH0)。設計判断は {{D:t425-floor-schema-lightweight}}。公式H1/H2実験の起票は
  依然 T-424/T-272 の要求全体閉包または D145決定5 の明示的再訪裁定、かつ rr80/rr20 較正登録が
  揃うまで不可 — この結論自体は不変 (2026-08-20監査を継承)。次wave候補: T-424/T-272残余を閉じる
  専用wave、または D145決定5 再訪をユーザー裁定へ送る。一次資料 = 本wave (branch
  worktree-dev-wave-t425-floor-bounded-prep、job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t425-floor-bounded-prep/`)。
  base: 774d564bef980a477f939bd931e2b19dafcbaa6adb5da38380d0e47fa96ad7c9
