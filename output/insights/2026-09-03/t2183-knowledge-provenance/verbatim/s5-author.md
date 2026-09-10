## 実装結果

- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:933) に読み出し専用関数を追加しました。既存 receipt/WAL/lock 検証を再利用し、`declared_sources` と `injected_sources` を返します。
- [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:757) は knowledge-aware campaign のみ receipt を再検証し、top-level 欄を常時出力します。非対応 campaign は `null` で receipt を読みません。
- [layer3_schema.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:28) に exact nested schema を追加しました。v3 と top-level `required` は不変で、legacy v2 からは新 property を除外します。
- [autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/autonomous_trial_completeness.py:4702) に legacy 欠落補正を追加しました。
- 本文 `content_utf8` は投影していません。

## 受理・拒否境界

既存の K2、lowercase digest、exact 3-key WAL provenance、canonical receipt v1、`repo_artifact` 限定、verified/canonical source 完全一致、部分 lock 拒否を維持しました。

純増した拒否は、knowledge-aware 材料レポート生成時の receipt 再検証です。BUILD_START 後に digest を差し替えた receipt が具体的な負入力です。WAL record、receipt schema・bytes・producer、campaign identity は変更していません。

## テストと検査

M1/M3/M4/M6/M7 を個別に殺す新規テストを追加しました。M2 は等価変異、M5 は冗長 gate として追加していません。新規テストは合計10件で、各 docstring に単一の失敗理由を記載しています。

静的検査は成功しました。

- `git diff --check`
- 変更した6 Python file の AST parse
- schema JSON parse
- v3 literal、top-level `required` の HEAD 同一性
- 禁止ファイルの差分なし
- staged changes なし

pytest は未実走です。targeted 15 nodeid、単一 nodeid、collect-only、全走を `tools/run_tests.py` から試しましたが、すべて `rc=16` で pytest child が起動しませんでした。bounded-local 予約台帳を sandbox 内から更新できず、dispatch 側も `qstat -Q` の socket error で停止しています。

## 波及可能性

module 名の `rg` では consumer test が `layer3_report` 11 file、`autonomous_trial_completeness` 11 file、`wal` 63 file、重複除外で71 fileありました。直接影響が大きいのは変更した3 test fileのほか、`test_layer3_admission_diagnosis.py`、`test_trial_registry.py`、`test_p3_autonomous_workload_trial.py`、`test_t126_qualification_artifacts.py`、`test_role_session_isolation.py` です。いずれも未実走です。

共有 `_campaign` fixture には opt-in の knowledge 引数だけを追加し、既定経路は不変です。既存 assertion・例外期待は削除・反転・緩和していません。repo 外の古い v3 schema reader が新欄を拒否し得る既知限界は残ります。

## 総括

- 実装: 裁定2・3・4を指定7ファイルだけに実装。
- 実走した nodeid: なし。pytest child 未起動。
- 未実走: 新規10テスト、変更した3 test file、静的に抽出したconsumer 71 file、全受入。
- 波及可能性: named projection追加、legacy比較補正、v2 forward-field拒否、古いrepo外v3 reader。
- 判断点: 既存 reader が verified sources と canonical sources の一致を既に証明するため、その検証済み値を両段へ独立コピーしました。恒真な追加照合は設けていません。
- 禁止事項: commit・`git add`・docs編集・禁止module編集はいずれも行っていません。