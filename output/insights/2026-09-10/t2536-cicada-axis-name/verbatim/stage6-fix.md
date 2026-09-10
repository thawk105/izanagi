## 変更

[test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2536-author/orchestrator/tests/test_pegasus_calibration_workload.py:35) のみ変更しました。production コード、docs、認定 protocol 集合には触れていません。

## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| C2 | partial | 表の全 entry で forward 一致と inverse 往復を検査 |
| C3 | partial | 4 protocol を parameterize し、表の copy 上の衝突を forward/inverse 双方で拒否 |
| C4 | partial | cicada の `REUSE_VERSION_CICADA` alias を拒否 |
| C5 | partial | silo/mocc/tictoc の実 cache 名受領証を表駆動で検査。silo の `BACKOFF_FIXED=-1` も受理 |
| C9 | partial | mocc `KEY_SORT` を Options/CMakeLists 双方で改名する負例を追加 |
| D-2 | partial | `parse_options_defaults()` と宣言 default assertion を除去し、空 default 正例を追加 |
| D-7 | partial | 件数 literal と cicada 1 件だけを固定する snapshot assertion を除去 |

すべて実装済みですが未実走のため、closed とは申告しません。regressed と確認された所見はありません。

## Nodeid

追加:

- `test_genome_axis_cache_mapping_roundtrips_every_declared_entry`
- `test_genome_axis_cache_table_accepts_empty_cache_default`
- `test_genome_axis_cache_table_rejects_non_cicada_ccbench_side_rename`
- `test_cicada_receipt_rejects_unmapped_cicada_suffix_alias`
- `test_receipt_accepts_real_cache_names_for_certification_protocols[silo]`
- `test_receipt_accepts_real_cache_names_for_certification_protocols[mocc]`
- `test_receipt_accepts_real_cache_names_for_certification_protocols[tictoc]`

改名:

- `test_genome_axis_cache_mapping_rejects_non_injective_copy_both_ways`
- → `test_genome_axis_cache_mapping_rejects_non_injective_copy_for_every_protocol[silo|mocc|tictoc|cicada]`

## 検証

`tools/run_tests.py` に焦点 nodeid 群を渡しましたが、`qstat -Q preflight rc=1` により rc=16 で終了し、`child_started=false` でした。実走した nodeid はありません。

静的確認は完了しています。

- Python AST parse: 成功
- `git diff --check HEAD`: 成功
- U+0300〜U+036F: 検出なし
- unstaged の変更先: 所有対象ファイル 1 本のみ

## 所有外への波及可能性

- `model.py` の表、forward、inverse の変更は往復・単射性検査へ波及します。
- `cli.py` の受領証逆変換変更は4 protocol の正例・負例へ波及します。
- `SPACES`、既存 CMake parser、CCBench Options/CMakeLists の変更は exact drift 検査へ波及します。
- 正当な軸追加は、SPACES・CCBench・宣言表が一致すれば件数 pin なしで通る設計です。
- screening 経路には新規検査を追加していません。親裁定どおり既存検査の担当範囲です。

## 総括

- 採用7所見を対象テスト1本だけで実装しました。
- runner 基盤障害のため未実走であり、全所見を partial と報告します。
- production、docs、commit、branch、認定受理集合は変更していません。