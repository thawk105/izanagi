## 総括

item 数を手書き literal `5` で検査する独立 assert を追加しました。
指定 3 nodeid は dispatch 障害により全て未実走です。
`git diff --check` は通過しました。
状態は「実装済み・未実走」です。

## 直した内容

[orchestrator/tests/test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1619-shared-setup/orchestrator/tests/test_real_repo_serialization.py:1045) だけを変更しました。

- 対象 group の収集 entry を list として保持。
- 従来の canonical set 完全一致を維持。
- `len(s8c_predicate_snapshot_entries) == 5` を追加。
- 失敗メッセージに `actual` と `expected=5` を含めました。
- golden の `len()` からは導出していません。

item が 6 件になった場合、parametrize により canonical set が同じ 5 名のままでも、件数 assert が `actual=6 expected=5` で失敗します。

## 実走結果

以下はすべて `python3 tools/run_tests.py` 経由で実行を試みましたが、`qstat -Q preflight rc=1`、`child_started=false` となり未実走です。

- `test_real_repo_group_collection_exactly_matches_canonical_nodes`: 未実走
- `test_xdist_group_audit_rejects_synthetic_negative_controls`: 未実走
- `test_xdist_group_name_set_audit_rejects_isolated_negative_controls`: 未実走

緑と申告できる nodeid はありません。

## 波及の静的列挙

- 対象 5 test の将来の parametrizationや重複 collectionは、item 数の増加として検出されます。
- canonical node の追加、削除、改名は従来の set 一致検査で引き続き検出されます。
- `test_s8c_preregistration_predicates.py`、`conftest.py`、`REAL_REPO_SERIAL_NODES` は未変更です。
- production code、`docs/`、所要台帳、既存期待値、負の対照は未変更です。
- commit、add、stash、branch 操作は行っていません。