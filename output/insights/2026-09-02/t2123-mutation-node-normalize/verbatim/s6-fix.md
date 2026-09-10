## 修正 1 の変更前と変更後

変更前は `MISMATCH` fixture の `test_output_tail` が空で、完全一致判定の検査前に tail 不一致で停止していました。

変更後は `MISMATCH` / `PARSE_ERROR` の場合だけ stdout 末尾80行を設定します。[test_mutation_fanout_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2123-fix1/orchestrator/tests/test_mutation_fanout_contract.py:285)

補助 probe では、対象 fixture が完全一致なら `MISMATCH`、包含へ緩めると `KILLED` になる集合関係と、tail が stdout 2行に一致することを確認しました。production の tail 要求は変更していません。

## 修正 2 の変更前と変更後

変更前は M3・M4・M9 の敵対入力が harness 側にしか届いていませんでした。

変更後は fanout の `_match_key` を直接呼ぶ次の3テストを追加しました。[test_mutation_fanout_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2123-fix1/orchestrator/tests/test_mutation_fanout_contract.py:587)

- 実在する arxiv parametrize ID 内の `@` を保持
- 入れ子角括弧後の group 接尾辞だけを除去
- `tests@left` と `tests@right` を異なる key として保持

harness 側の既存3テストは変更していません。

## 修正 3 の変更前と変更後

変更前は spec の重複判定が `_match_key` と `_normalize_node` を経由し、contract 自身の `__file__` 由来 root に依存していました。

変更後は repo 非依存の `_strip_group_suffix` を切り出し、spec 重複判定と `_match_key` から共有しています。[mutation_fanout_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2123-fix1/tools/mutation_fanout_contract.py:297)

- spec 重複判定では `_normalize_node` を呼ばない
- raw 文字列重複検査を先に維持
- `[one]` と `[one]@group` の alias 重複だけを追加拒否
- `_observed_status` と collection 再照合は、正しい checkout を渡す従来の `_match_key` 経路を維持

補助 probe では、別 checkout の絶対 path 1件が spec 検証を通り、その base/group alias 対は重複拒否されることを確認しました。

## 追加・変更したテスト

追加:

- `test_fanout_match_key_preserves_real_parametrize_id_containing_at`
- `test_fanout_match_key_removes_only_group_after_nested_real_parametrize_id`
- `test_fanout_match_key_does_not_collapse_at_in_realistic_paths`

fixture 修正:

- `_build_group` の `test_output_tail` を status 契約どおり生成

既存の期待値、skip、xfail、テスト名は変更していません。

## 実走した nodeid と結果

pytest child が実際に開始した nodeidは0件です。

次の8 nodeidを `tools/run_tests.py` へ渡しましたが、`qstat -Q` の sandbox 制約により wrapper rc=16、`child_started=false` で停止しました。

- `::test_split_rejects_group_suffix_alias_as_expected_node_duplicate`
- `::test_split_still_rejects_raw_expected_node_duplicate`
- 追加した fanout `_match_key` テスト3件
- `::test_merge_matches_group_suffixed_failure_and_preserves_raw_nodes`
- `::test_merge_accepts_group_suffixed_expected_against_base_collection`
- `::test_merge_keeps_group_normalized_strict_superset_as_mismatch`

collect-only も同じ理由で child 未起動でした。したがって緑とは申告しません。

非pytestの補助検査結果:

- 対象2ファイルの AST parse: 2/2成功
- 敵対 literal の helper probe: 3/3成功
- repo非依存 spec probe: 2/2成功
- `git diff --check`: 成功

## 未実走のもの

- 上記8 nodeidのpytest実走
- strict-superset テストに対する実際の包含変異走
- `test_mutation_fanout_contract.py` 全体
- 制約 meta-test:
  `test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact`
- 段6で列挙された直接 consumer・内容走査テストの修正後回帰走

## 波及可能性の静的列挙

- 所有外 caller: `tools/mutation_fanout.py` が `derive_split` と `merge_group` を使用します。編集していません。
- 内部 caller: `_validate_spec_document` は split、merge、CLI経路から呼ばれます。絶対 path の新規拒否が解消されます。
- 比較 consumer: `_observed_status` と collection 再照合は helper 化後も同じ `_match_key` 意味論です。
- 共有 fixture: `_build_group` の tail 修正は status override を使う同ファイル内テストへ波及します。現時点の該当は strict-superset fixtureです。
- consumer test: `test_mutation_fanout.py`、`test_mutation_fanout_contract.py`、全 tracked Python を走査する `test_p3_build_authority_cli.py` が直接または静的 consumerです。
- 段5全体の親回帰対象として、harness、flaky-hold、worktree、failure-digest、および既報の内容・AST走査テスト群が残ります。

## 総括

指定された3修正を、許可された2ファイルだけへ適用しました。`_normalize_node`、`tools/mutation_fanout.py`、既存期待値、文書、禁止ファイルは変更しておらず、commitも作成していません。

pytest実走はインフラ制約で child 0件のため、実装済み・未実走であり、closedとは申告しません。