## 所見ごとの対応表

| 所見 | 状態 | 対応箇所 |
|---|---|---|
| F1 | partial — 実装済み・pytest 未実走 | [p3_b4_material_report.py:980](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/campaign/p3_b4_material_report.py:980) |
| F2 | partial — 実装済み・pytest 未実走 | [p3_b4_raw_record_producer.py:633](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/campaign/p3_b4_raw_record_producer.py:633) |
| F3 | partial — 実装済み・pytest 未実走 | [p3_b4_raw_record_producer.py:723](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/campaign/p3_b4_raw_record_producer.py:723) |
| F4 | partial — 検査追加済み・pytest 未実走 | [test_p3_b4_raw_record_producer.py:1976](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:1976) |
| F5 | partial — 検査追加済み・pytest 未実走 | [test_p3_b4_raw_record_producer.py:1067](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:1067)、[同:1093](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:1093) |
| F6 | partial — 検査追加済み・pytest 未実走 | [test_p3_b4_raw_record_producer.py:1010](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:1010) |
| F7 | partial — 検査追加済み・pytest 未実走 | [test_p3_b4_raw_record_producer.py:861](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:861) |
| F8 | partial — 分離済み・pytest 未実走 | [test_p3_b4_raw_record_producer.py:1153](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:1153)、[同:1165](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:1165) |

## 実装した内容

- F1: `producer_rejections` を `.get()` で取得し、旧 renderer-only 入力では新しい履歴行を省略するようにしました。
- F2: tail 切り捨て時、`attempt_id=null` と `IO_ERROR` issue を持つ既存 schema の修復 eventを、本来の rejection event より先に追記します。
- F3: file または directory の `fsync` 失敗時、同じ lock 内で追記開始 offset へ `ftruncate` し、rollback も同期します。失敗は従来どおり `IO_ERROR` 付き rejection になります。
- F4: 既存 certified 201-block 正例の publication と証拠をそのまま再利用し、invalid ledger があっても complete assembly が成功する検査を追加しました。
- F5〜F7: batch pre-scan、per-item 一般例外、ledger symlink、公開 schema literal の検査を追加しました。
- F8: N06 と N07 の assertion を別 node へ移し、共有 module fixture で同じ安価な report を再利用します。

## 受理集合の変更前後

- `producer_rejections` のない旧 renderer 入力は、変更前の `KeyError` から再び描画可能になります。
- producer の成功公開条件と既存 rejection 条件は変えていません。
- tail 修復時だけ、修復 event が追加で ledger に残ります。attempt に対応する rejection event は従来どおり別 event です。
- `fsync` 失敗時は、可視化された未確認 event を残さず、元の rejection に `IO_ERROR` を加えて返します。
- 新しい issuer gate や publication rejection は追加していません。

## 追加・変更したテスト

変更した既存 node:

- `test_m09_renderer_only_future_compatibility_preserves_four_verdict_wire_values` 全4 parameter
- `test_validated_rejection_is_appended_as_one_canonical_event`
- `test_unterminated_tail_is_truncated_before_the_next_single_write`
- `test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings`
- `test_m01_m02_assembly_rejection_still_reports_201_blocks_and_missing_leaf`

新設 node:

- `test_rejection_fsync_failure_rolls_back_to_preappend_length`
- `test_rejection_ledger_symlink_is_rejected_without_touching_target`
- `test_batch_prescan_rejection_is_durably_recorded`
- `test_batch_per_item_unexpected_exception_is_durably_recorded`
- `test_unresolved_absent_attempts_exclude_matching_recorded_rejection`
- `test_unresolved_absence_retains_current_reason_non_guarantee`

適用される meta-test／制約:

- `test_mutation_node_mapping_is_complete_and_one_to_one`: M01〜M18 の名前・一対一対応は静的確認済み。新設名は M 系ではありません。
- `test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_shard_assignment_preserves_live_xdist_group_components_and_split_control`: material-report 側の test 関数名集合は変更していません。
- `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`: 新設6 node は duration ledger 未登録です。docs 編集禁止のため ledger は変更していません。

## 実走の有無

実装済み・pytest 未実走です。

`tools/run_tests.py` で安価な対象16 nodeと、F4 の201-block正例を別々に開始しましたが、両方とも `qstat -Q preflight rc=1`、`child_started=false`、runner `rc=16` でした。したがって緑は主張しません。

受入外の局所 probe では renderer 互換、修復 event 順序と材料レポート投影、fsync rollback、batch 2経路、symlink 拒否を確認しました。AST parse、`git diff --check`、変更対象、禁止対象の静的検査も成功しています。

## 契約から外れた点

- 実装契約からの意図的な逸脱はありません。
- `_publish_exact` と `B4_RAW_RECORD_NON_GUARANTEES` は commit `44dc1d1f6` から同一であることを静的確認しました。
- hash chain、Deferred 記録、batch collection 型不正の記録は追加していません。
- wave 追加分の N06／N07 assertion は別 node へ移動しました。既存 M01／M02 assertion は維持しています。
- docs、commit、add、merge、rebase、push は実行していません。

## 総括

- F1〜F8 はすべて実装または検査追加済みです。
- 変更は許可された4 fileだけです。
- complete 201-block fixture の新規生成経路は追加していません。
- 局所 probe と静的検査は成功しました。
- pytest は dispatch infrastructure failure により未開始です。
- このため全所見を `partial` として引き渡します。