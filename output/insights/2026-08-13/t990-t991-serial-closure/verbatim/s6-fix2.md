## 実装した内容

- [orchestrator/tests/conftest.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/conftest.py:314)
  - real-repo 印を `user_properties` から非公開属性 `_izanagi_real_repo_serial_node` へ移動。
  - collection 時に正本 node ID を属性へ設定。
  - runtime guard は同属性の値が実行 node ID と一致する場合だけ `stamped=True` とするため、破損時は fail-closed。

- [orchestrator/tests/test_real_repo_serialization.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:456)
  - 注入 plugin の `real_repo_stamps` を同じ非公開属性から抽出。
  - 属性の有無を検査して従来と同じ監査 payload を生成するため、親側の完全一致期待は未変更。
  - 正本 instance は印がちょうど 1 個、正本外は 0 個という監査を維持。

`REAL_REPO_SERIAL_NODES`、既存期待値、growth-hold 契約テストは変更していません。

## なぜ growth-hold 契約テストが編集なしで通るか

対象 node は両方の集合に属しますが、処理経路は次のようになります。

1. real-repo 分岐は非公開属性だけを設定し、従来どおり `xdist_group("real-repo")` を付ける。
2. `user_properties` には何も追加しない。
3. growth-hold 分岐が既存の 4 key だけを `user_properties` へ追加する。
4. したがって `dict(item.user_properties)` は、未編集の期待どおり以下の 4 key だけになる。
   - `growth_hold_node_id`
   - `growth_hold_axis`
   - `growth_hold_correctness_gate`
   - `growth_hold_release_condition`

注入 plugin は親テストとは別 subprocess ですが、その subprocess 内で suite の `pytest_collection_modifyitems` と plugin の `pytest_collection_finish` が同じ pytest session・同じ item を扱います。属性は process をまたがず、その後 JSON report だけが親へ返ります。`item.stash` は使っていないため、`StashKey` の object 同一性問題もありません。

## 実走結果

以下を同一 runner invocation で指定しました。

| nodeid | rc | 結果 |
|---|---:|---|
| `orchestrator/tests/test_growth_test_holds_contract.py::test_collection_hook_attaches_skip_metadata_and_prints_early_summary` | 16 | 未実走 |
| `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes` | 16 | 未実走 |

原因は `qstat -Q preflight rc=1` による Pegasus dispatch infrastructure failure です。pytest 本体は起動していません。よって状態は**実装済み・未実走**です。

静的検査では以下を確認しました。

- 両変更ファイルの `ast.parse`: OK
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

## 波及可能性の静的列挙

- JUnit XML / `user_properties`
  - real-repo 内部印は公開出力から除去されます。これは意図した変更です。
  - growth-hold の 4 key は従来どおり残ります。
  - `orchestrator/` 内検索では、旧 real-repo property の consumer は更新済み注入 plugin だけでした。

- `orchestrator.campaign.patchharness`
  - 引き続き `(node_id, stamped)` の bool を受け取るため interface 変更はありません。
  - 属性値が node ID と一致しない場合は `False` となり、実共有 checkout は拒否側へ倒れます。

- xdist
  - `xdist_group("real-repo")` の付与条件と正本集合は不変です。
  - runtime protocol は collection と同じ worker process の item 属性を読みます。

- `test_real_repo_serialization.py` の注入 plugin
  - suite conftest が読み込まれる収集 subprocess 内で属性を読み、親へは従来形の JSON stamp を返します。
  - 正本外属性、欠落、誤った node ID は既存の完全一致 assert で赤になります。

- `test_dev_waves_isolation_contract.py`
  - `REAL_REPO_SERIAL_NODES` の集合だけを読むため影響しません。

- `test_campaign.py`
  - `_pytest_node_context` を直接検査しており、その interface は不変です。

## やり残し

- 上記 2 node の実走は親環境で必要です。
- 親が担当する変異検査・受入全走・統合確認は未実施です。
- commit は作成していません。

## 総括

指定された 2 ファイルだけを変更し、real-repo 内部印を公開 `user_properties` から非公開属性へ移しました。growth-hold の公開 4 key、直列化集合、runtime guard、stamp 完全一致監査はいずれも弱めていません。公式 runner は `rc=16` で dispatch 前に停止したため、実装済み・未実走として親への再走を残します。