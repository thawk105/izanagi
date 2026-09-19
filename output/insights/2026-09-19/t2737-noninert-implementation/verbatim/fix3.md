## 総括

**実装済み・未実走です。** 変更は `orchestrator/tests/test_ccbench_spawn_sites.py` のみ、追加53・削除8の計61行です。

修正前は `SS2PL_WFG_HH`、`SS2PL_LOCK_HH`、`SS2PL_STUDY_LOCK_HH` が候補に入り、裁定記録では登録簿一致・件数検査の3テストが赤（38≠35、28≠25）でした。

| 所見 | 状態 | 結果 |
|---|---|---|
| include guard の構造的除外 | partial | (a)(b)(c)をすべて要求。除外を該当新規ファイル内に限定 |
| 正例1・負例2 | partial | `tmp_path` の実patchを読むテスト1本を追加。stub・揮発hashなし |
| 所有・変更規模・期待値維持 | closed | 所有外変更なし。既存期待値変更なし。`git diff --check` 成功 |
| 指定実走・メタテスト | partial | ともにdispatch失敗。pytest未起動 |
| 回帰判定 | partial | 未実走のため判定不能 |

指定コマンドは**1回**試行し、`qstat -Q preflight rc=1` によりrunnerが **rc=16 / child_started=false** で終了しました。

追加で実行を試みたメタテスト範囲も同じ理由で未起動です。

- `test_plain_runner_coverage.py` 全体
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`

静的波及確認では、所有外の直接caller・consumerは検索上ありません。直接consumerは同ファイル内の既存8テストです。共有fixtureは変更せず、新規テストは `tmp_path` を使用します。

**未実走境界:** 修正対象全体、新設node、上記メタテスト、親担当の変異検査・受入全走。緑・回帰解消は未確認です。親docs由来の期待赤はありません。docs編集・stage・commitは行っていません。