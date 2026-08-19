---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t470-accepted-consumer
seq: 1
title: '[T-470] certified 選択結果の consumer writer API (render_accepted) を実装した (コード+テスト+記録、branch worktree-dev-wave-t470-accepted-consumer、変異matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0、受入 = local main 取り込み merge が provenance gate で新規違反検出・claim前 rc=70 で land 未達)'
---

## 本文

- 段3 敵対相談は2レンズ (sol/luna) とも NO-GO だった。核心所見 (両レンズ独立に収束):
  `render_accepted()` を追加するだけでは「production consumer」にはならない —
  production caller (`p3_autonomous_workload_trial.py`/`autonomous_trial_completeness.py`) は
  どちらも従来どおり非 certifying builder を呼び続け、新 API は test 以外から呼ばれない。
  親裁定 ({{D:layer3-accepted-writer-api-scope}} 参照) は、520b76cc wave 自身が同じ理由
  (C02 arm binding・T-468 approval authority 未解決、DW-G04 発火条件を書けない) で
  「certified selector の実結線」を後続タスクへ送った前例を踏襲し、本 wave は
  file scope 内で作れる「検証済み writer API」に限定した。「production consumer 実結線が
  完了した」という主張はしない。
- 段6 敵対レビュー: レンズA (実装差分の正確性) は所見なし・GO。レンズB (回帰・境界条件) は
  所見3件、総括 NO-GO。所見1 (production 未接続) と所見2 (同一 out_json の意味的競合) は
  段4裁定で既に裁定済みの論点の再確認であり対応不要。所見3 (`_write_report_atomic()` 内部の
  `os.link()` 排他性の実経路と親 directory 不在境界が変異 4 件では未検査) は real・採用し、
  fix (commit `2d111bfc`) で `_write_report_atomic()` を直接呼ぶ2テストを追加、対応する
  変異 m05/m06 を追加登録して 6/6 KILLED を確認した。
- **受入が land 不能**: main (`b8fceb8c`) を取り込む merge commit (`0e07ad03`) を作成したところ、
  main 側 (workload-policy-hint-impl wave) と本 wave の両方が
  `orchestrator/campaign/layer3_report.py`/`orchestrator/tests/test_layer3_report.py` を
  実装面として変更していたため (競合なしの和集合、`git merge` は "Automatic merge went well")、
  `tools/check_ai_provenance.py` の combined-path 判定 (`_intersection_path_set`、両親からの
  積集合が非空) が機械的に「実装面著作」と誤判定した。これは `docs/failures.md` の F365 が
  既に記録した既知パターン (40件以上の known-violation エントリが同型) と一致し、
  F365 の恒久対応 (`preclaim-history-provenance`: claim 前に無条件で全史監査) が
  意図どおり機能して、lease を一切消費せず (`claimed_main: null`) rc=70 で早期に land 不能を
  検出した (F365 への再発として failures fragment に記録した)。
  `tools/check_ai_provenance.py` ソース中に **「(ユーザー選択: known-violation 登録)」**
  と明記されており、台帳への新規登録は AI 単独で行ってはいけない。checker のソース変更自体も
  実装面変更で D95 により Codex role=author が要るため、この wave 内で即興対応しなかった。
- 変異事前登録の実績: m01〜m04 は段4裁定どおり登録し、初回本走で m04 が MISMATCH
  (期待 node 集合が不完全、`test_relative_and_absolute_campaign_paths_are_byte_identical` が
  同一理由で追加検出されたのに未登録だった) となり、expected_nodes を修正して再登録・
  再走し KILLED を確認した。単一理由の見立てそのものは正しかったが、影響範囲の網羅が
  1回目は不足していた。

## 次の一手差分

### 更新

- [T-470] **writer API (`render_accepted()`) は実装・検証 (変異6/6 KILLED) 済みだが、
  production caller 配線は未着手のまま {{T:layer3-accepted-report-production-caller}} へ
  分離し、本 wave 自体も上記 provenance gate で land 未達**: known-violation 登録の要否を
  ユーザーに確認してから、同じ wave branch (`worktree-dev-wave-t470-accepted-consumer`,
  最終 commit `2d111bfc` + merge `0e07ad03`) で受入を再試行する。
  base: 39984a2bad8c4612b6bb50279a459373aaf802ad25303432d2aceb7833578fc8

### 新規

- {{T:layer3-accepted-report-production-caller}} **P2**: `render_accepted()` を実際に呼ぶ
  production caller (`trial_registry.assert_trial_registry_acceptance()` 後、または
  certified selector / decisions consumer) を配線する。canonical 出力 path・所有権・
  `autonomous_trial_completeness.py` の certified variant 対応も同時に設計する必要がある
  (段6 レンズB 所見4)。C02 arm injective binding と T-295 approval authority
  ([T-468] の再訪条件) が解決するまで、`certifying=true` な正例は production に存在しない。
