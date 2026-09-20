## 変更の要約

- B04：`logical_sessions` を投入済み論理 slot 集合の件数に修正。
- A1：WAL 拒否による A のみ消費・retry 無し・系列継続と、CLI rc 0 をテストで固定。
- 指定 fixture に stock 履歴を追加し、終端 `score_sessions` も fitness に追従。

## 新 test 一覧

以下の nodeid を追加し、すべて実走で PASS。

```text
orchestrator/tests/test_b5_generator_contrast_report.py::test_logical_sessions_zero_before_allocation_start
orchestrator/tests/test_b5_generator_contrast_report.py::test_logical_sessions_stock_and_three_submitted_searches
orchestrator/tests/test_b5_generator_contrast_report.py::test_logical_sessions_zero_for_stock_pre_start_failure
orchestrator/tests/test_b5_generator_contrast.py::test_wal_diff_quarantine_without_rejection_sidecar_continues
orchestrator/tests/test_p3_s4_loop.py::test_b5_string_preflight_rejection_uses_wal_and_rc0
```

## 実走結果

指定コマンドの最終結果：

| 対象 | 結果 |
|---|---|
| report 全体 | 70 passed |
| driver 全体 | 108 passed |
| loop：`-k 'b5 or preflight or grammar'` | 81 passed、505 deselected |

合計 **259 passed**。report 初回の新規テスト 3 件は呼出し引数誤りで失敗しましたが、修正後の全体再実走で通過しています。`git diff --check` も通過。

## 未了・懸念

指定範囲の未了なし。変更は指定 4 ファイルのみ。読み取り専用の実装・tools・docs は変更せず、git のステージング・commit 等も実行していません。

## 総括

親裁定の B04・A1 残件・nit の対応を完了しました。