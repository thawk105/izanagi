---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1476-verify-state-committed
seq: 1
title: '[T-1476] verify_done の committed attempt 束縛を追加し、非committed attemptの誤採用をfail-closedにした (コード+テスト、branch worktree-dev-wave-t1476-verify-state-committed)'
---

## 本文

- 起票文 (command 引数) は「`_verify_state` 周辺だけ」「digest.py 等の別 consumer へ
  scope を広げない」と明示しており、段2 codex plan・段3 敵対相談2レンズ (sol/luna) が
  `build_done`/`bench_done`/`abort`/`commit` にも同型の attempt_id 不問の脆弱性がある
  と指摘したが、これらは scope 外の real 所見として次task候補へ回した (段4裁定、
  {{D:verify-done-attempt-binding-scope}})。
- 段6 敵対レビュー2本が、`s8b_oracle_report.py` の bytes 変更で
  `test_s8b_oracle_manifest.py` の golden fixture `PIN_GATE_SPEC_RAW`
  (`generator_versions.report.sha256`) が stale になる regression を発見した。fix で
  inner/outer 両 hash を実 bytes から機械的に再計算して更新した (fix子・親・段6焦点
  再レビューの3者が独立に同一値へ収束、手動転記による誤りを避けるため計算スクリプトの
  出力をそのまま採用)。
- 受入投入時に main 上の commit `09ce607b` (ユーザー thawk105 が canonical main
  worktree で `external/ccbench` の MOCC correctness trace v2 hook 追加作業を行い、
  submodule pin 511c9538→ef9328a3 を dev-wave プロセス外で直接進めた human-only commit)
  に `AI-Agent:` trailer が無いことを preclaim provenance 監査が新規違反として検出し、
  受入がブロックされた。本 wave の欠陥ではないため親は amend も自己登録もせず、
  ユーザーへ状況を説明して known-violation 登録の承認を得た (2026-08-21、本セッション内)。
  `tools/check_ai_provenance.py` へ登録し、追随して赤化した exhaustive meta-test
  (`test_check_ai_provenance.py::test_known_violation_ledger_matches_literal_entries`)
  も Codex `role=author` で修正した (317 passed)。
- 受入投入前に、main 取り込み (`dev_wave_wait.py acceptance` 自身の自動 merge を含む)
  で submodule pointer が進んだが working tree が追随しない事象 (DW-O20 の既知挙動) に
  遭遇し、`git -c protocol.file.allow=always submodule update --init --recursive` で
  解消した (`dev_wave_submodule_init.py` の `update-no-fetch` は対象 commit 未fetch時に
  失敗、素の `git submodule update` は `protocol.file.allow` 無指定で失敗)。DW-O20 への
  反映を試みたが単節予算 (1000 bytes) に対し原文が既に983 bytesで17 bytesしか余裕が
  無く、意味を保った圧縮ができなかったため revert し、本記録と次の一手候補への記載に
  留めた。
- 変異事前登録 (DW-M01) どおり `_verify_state` の ID 不一致検査を無効化する変異 m01 を
  実装後の実 file:line で確定して本走し、baseline PASSED・m01 KILLED
  (matches_expectation=true) を確認した。
- 親が実走: `test_s8b_oracle_report.py` 237 passed (新設回帰テスト含む)、
  consumer 9ファイル (fix前 2 failed/412 passed/19 skipped、fix後 651 passed/19 skipped)、
  `test_check_ai_provenance.py` 317 passed。いずれも `tools/run_tests.py` 経由。

## 次の一手差分

### 完了

- [T-1476] `s8b_oracle_report.py::_verify_state`/`_assess_window` に committed attempt
  (`build_attempt_id`) 束縛を追加し、非 committed attempt の verify_done が certified
  として誤採用されないよう fail-closed 化した。回帰テスト
  `test_verify_done_attempt_id_mismatch_is_a_protocol_violation` を新設し、変異 m01
  (KILLED) で検出力を確認した。
  remaining: none
  base: 3227cec84e55447bc57958b4280a5c4347a67ef4e6e2542f8ba44f14ba5ec1dc

### 新規

- {{T:s8b-oracle-report-full-stage-binding}} **P2**: `s8b_oracle_report.py::_assess_window`
  の `build_done`/`bench_done`/`abort`/`commit` payload も verify_done と同型の
  attempt_id 不問脆弱性を持つ (段3 sol が bench/commit 混結合・stale abort reason 誤受理の
  具体例を提示)。T-1476 は verify_done のみを scope としたため未着手。
