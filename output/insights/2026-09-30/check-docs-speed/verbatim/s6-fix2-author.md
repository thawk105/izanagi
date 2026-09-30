## 所見ごとの対応

- **F4: closed。** `_ArchiveWorklog.first_entry_ids` に保持する先頭 entry の ID だけを `sys.intern` で共有するよう変更しました。ID の比較値と判定は変わりません。メモリ削減量の再計測は未実施です。

## 変更点

[tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-impl/tools/check_docs.py:3190) の 1 行のみ変更しました。テストの期待値、docs、commit には触れていません。

## 実走結果

- 追加 `test_speed_*` と archive 境界系の **16 ケースを関数の直接呼び出しで実走し、全件通過**。
- pytest は **未実走**。`run_tests.py` 経由の起動は `qstat -Q` の事前確認で失敗し、子プロセスは起動しませんでした。
- `git diff --check` 通過。作業木の変更は `tools/check_docs.py` のみです。

## 総括

F4 の修正と指定範囲の動作確認は完了しました。性能と peak RSS の効果は未測定です。