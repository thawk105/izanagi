## 変更と波及

所有テストに、2変数の出現領域・順序・行内容を集合で固定する静的検査と、代入・unset・export・read の注入例8件を追加しました。既存テスト・期待値は変更していません。

所有外 caller・共有 fixture・consumer test の変更は不要です。shell に対象変数の出現を追加・削除した場合、新検査が失敗します。shell・docs の編集、commit、git 状態変更操作はしていません。ランナーが診断 receipt を生成しました。

## 総括

- **直した内容:** 中間区間を含む shell 全文の対象変数出現を固定。test 本体に静的検査である旨を明記しました。
- **実走:** テスト0件。対象は `orchestrator/tests/test_b10_backoff_grid_job.py` 全体ですが、`qstat -Q` 失敗で起動前に rc=16。新規 nodeid `::test_job_formal_variable_occurrences_are_fixed`（1件）、`::test_job_formal_variable_invariant_rejects_overwrites`（8件）とも未実走です。構文検査・差分空白検査は成功しました。
- **裁定との差:** 実装は裁定どおりです。ただし指定の unset 注入による赤は未確認のため、**実装済み・未実走**です。