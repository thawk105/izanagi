## 変更したファイル

- [enforcement_source_ratification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:274)
  - 到達可能 DAG 全体の検査へ変更。
  - shallow、実効 graft、非 regular blob、複数導入を拒否。
  - `_git` に `input_bytes` を追加。subprocess 起動口は既存の 1 か所を維持。
  - `_load_rows` は指定どおり `split(b"\n")[:-1]` だけ変更。
- [test_enforcement_source_ratification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:432)
  - 決定的な `write-tree` / `commit-tree -p` helper を追加。
  - 受理 6 件、拒否検出 9 件、過剰拒否検出 1 件を追加。

## 検査と裁定番号の対応

| # | 実装 |
|---|---|
| 1 | 既存 `_validated_root()` を維持 |
| 2 | shallow 状態が exact `false\n` 以外なら拒否 |
| 3 | graft file の空行・`#` 始まり以外を拒否。replace ref は拒否しない |
| 4 | HEAD を exact 40 桁 lowercase hex として取得 |
| 5 | `git log --format=%H %P <head>` 1 回で全 DAG と実親を取得 |
| 6 | 全 commit の ledger entryを 1 回の `cat-file --batch-check` で取得し、行数・OID・type・size を exact 検査 |
| 7 | symlink/gitlinkを拒否し、異なる ledger blobを 1 個ずつ取得。同一 OID は再利用 |
| 8 | 削除、導入行数、親集合の欠落、増分上限、単一実親の部分列を順番どおり検査 |
| 9 | 到達可能 DAG 全体で複数導入を拒否 |
| 10 | HEAD の行集合を `frozenset` で返却 |

commit 間の mode 比較は入れていません。symlinkを blob と誤認しないため、tree entry が regular blob modeであることだけを分類時に確認します。

## 足したテスト

| nodeid | 殺す誤実装 |
|---|---|
| `test_pre_ledger_branch_merge_with_unchanged_ledger_is_accepted` | F600 mergeを追記版として数える実装 |
| `test_concurrent_branch_appends_are_accepted_after_merge` | DAGを線形履歴として比較する実装 |
| `test_single_parent_middle_insertion_is_accepted` | 部分列ではなく末尾追記を強制する実装 |
| `test_opposite_branch_orders_are_accepted_after_merge` | mergeで全親の順序保存を要求する実装 |
| `test_octopus_branch_appends_are_accepted_after_merge` | 親数を 2 に固定する実装 |
| `test_repeated_pre_ledger_branch_merges_are_accepted` | ledgerなし枝との複数回合流を削除・再導入扱いする実装 |
| `test_two_independent_ledger_introductions_are_rejected` | 導入一意性を検査しない実装 |
| `test_merge_omitting_one_parent_row_is_rejected` | 親集合の片方だけを見る実装 |
| `test_merge_substituting_an_unknown_row_is_rejected` | 親行を落として未知行へ置換できる実装 |
| `test_merge_adding_two_new_rows_is_rejected` | 新規行上限を 2 以上へ緩和する実装 |
| `test_invalid_middle_history_transition_is_rejected` | HEAD と直親だけを見る実装 |
| `test_crlf_ratification_ledger_is_rejected` | `splitlines()` へ戻す実装 |
| `test_non_regular_ledger_entries_are_rejected` | symlink/gitlinkの type 検査を除く実装 |
| `test_shallow_repository_is_rejected` | shallow guardを除く実装 |
| `test_effective_graft_file_is_rejected` | graft guardを除く実装 |
| `test_empty_graft_and_unrelated_replace_ref_are_accepted` | 空 graftや replace ref の存在だけで過剰拒否する実装 |

裁定 3 節に従い、親の和集合を保存した mergeで新規行がちょうど 1 件なら受理されます。未知行テストは、親行を落として未知行へ置換する違反を対象にしています。

既存 12 node、既存の期待値、既存 `match=`、名称は変更していません。

## 受理・拒否の差分

変更後は、F600型合流、並行追記、途中挿入、逆順枝、octopus、ledgerなし枝との反復合流を受理します。

新たに CRLF、shallow、実効 graft、canonical内容を持つ symlink、複数の独立導入を明示的に拒否します。削除、欠落、置換、並べ替え、複数行追加は従来どおり拒否します。

台帳不在なら空集合を返し、公開 API は従来どおり `enforcement-source-closure-unratified` で拒否します。

## 波及

- `contract_loader_binding.py`: 公開 API と wrapper 文言は不変。履歴通過後は closure digest不一致が正直な unratified理由になります。
- `conftest.py` の `ratified_enforcement_source`: 1 commit・1 行導入なので新規則を満たします。fixture変更なし。
- `test_ccbench_spawn_sites.py`: productionの subprocess起動口は `_git` の 1 か所のままです。
- `campaign_lock.py`: 本 module自身が closure対象なので digestは変わり、既存批准行とは一致しません。
- `test_t671_source_binding.py` など共有 fixture利用 consumerは追加された read-only Git検査の影響を受ける可能性がありますが、API変更はありません。
- 射影された `conftest.py` と `test_ccbench_spawn_sites.py` には、この test fileやテスト名の列挙 registryはありませんでした。

## 未了・注意点

pytestは指示どおり実走していません。実装済み・未実走です。

静的確認では、両 fileのAST解析成功、production spawn site 1、既存 test関数 10、追加 test関数 16、99文字超過なし、禁止された結合文字なしを確認しました。commit、stage、docs編集、所有外 file編集は行っていません。

## 総括

裁定 3 節の評価順を実装し、5 節の全 16 シナリオを追加しました。既存 12 test契約と公開 APIを維持した状態で、親による実測待ちです。