## 変更

[test_verifier.py:3399](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u4/orchestrator/tests/test_verifier.py:3399) の新規 v3 helper・試験だけを変更しました。

- 今回：追加6行・削除2行、計8行。
- R9 累計（`eef04f5a7` 起点）：追加490行・削除0行。上限800行以内。
- 既存試験・runner は変更前と bytes 一致。`git diff --check` 成功。
- docs・commit・branch 操作なし。

## B4 の充足

[test_verifier.py:3424](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u4/orchestrator/tests/test_verifier.py:3424) で、packed／tuple 設定はまず `_CompactTrace` を肯定 assertion し、その後に既存の表現検査を行います。

`expect_compact=True` を既定とし、[3614行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u4/orchestrator/tests/test_verifier.py:3614) の `epoch == 2**63` の overflow fixture だけ明示的に解除しました。`2**32` は compact を要求します。

## 一時退行での確認

`_parse_file_to_columns` が v3 を常に `_ParsedFileNeedsLegacy` に落とす一時変更を入れ、自走しました。終了コード1。追加 assertion で赤になった試験は次の10件です。

```text
test_v3_cycle_reports_tables_and_tx_types
test_v3_existence_unverified_and_v2_control
test_v3_framing_and_neutral_files
test_v3_last_winner_tx_type_in_cycle
test_v3_packed_mapping_and_read_bounds
test_v3_parallel_processes_and_pool_failure_fallback
test_v3_reasons_preserve_ww_wr_rw_identity
test_v3_same_version_table_duplicates_and_notes
test_v3_serial_tables_types_and_ops
test_v3_x_i_keep_table_and_make_indeterminate
```

加えて `test_v3_table_identity_separates_edges` が ERROR、`test_v3_tuple_and_legacy_fallback_preserve_metadata` が FAIL。

結果末尾（逐語）：

```text
120 passed, 12 failed, 0 skipped
```

production を元の bytes に復元し、`git diff -- orchestrator/verifier` が空であることを確認しました。[退行時ログ全文](/tmp/t2854-u4-b4-regression.log)

## 実走結果（逐語）

復元後の最終版で実行し、終了コード0：

```text
PYTHONPATH=. python3 orchestrator/tests/test_verifier.py
```

結果末尾：

```text
132 passed, 0 failed, 0 skipped
```

[最終版ログ全文](/tmp/t2854-u4-b4-final.log)。pytest・run_tests.py は使用していません。

## 未解決

今回の B4 修正に未解決事項はありません。受入全走・登録済み M1〜M15 の変異本走は今回の検証範囲外です。

## 総括

通常 fixture の packed／tuple 設定で compact 到達を必須にしました。
legacy fallback の許可は明示引数で overflow fixture に限定しました。
一時退行では追加 assertion により10件が失敗しました。
production は完全復元し、差分が空であることを確認しました。
最終自走は `132 passed, 0 failed, 0 skipped`、終了コード0です。
R9 累計490／800行で、既存試験・runner は変更していません。