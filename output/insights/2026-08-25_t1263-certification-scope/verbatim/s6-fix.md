## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F-1 | partial | 宣言と AST 閉世界検査を実装。assertion 本体は rc=0 だが pytest node は基盤障害で未実走。 |
| F-2 | partial | 二重台帳へ最終 node 名を登録し、AST 上は 20 fixture consumer の閉包を確認。collection メタテストは未実走。 |
| F-3 | partial | 構築段を短縮したが、変更後秒数を計算ノードで実測できず 30 秒以下を未証明。 |
| F-4 | partial | 成功 identity は 1 回、mismatch identity は 2 回という assertion を実装。対象 node は未実走。 |
| F-5 | partial | 改竄で増える 2 reason の exact 集合 assertion を実装。対象 node は未実走。 |
| F-6 | closed | 旧名 0 件、新名 5 件を AST で確認。挙動は変更していない。 |
| F-7 | closed | MUT-1〜3 と MUT-7 の重複検出力を各 1 行で明記。 |

## 実装した内容

- [tools/codex_reasoning_ab.py:9996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/tools/codex_reasoning_ab.py:9996)
  - `snapshot_checks_passed` を `snapshot_replay_bindings_passed` へ改名。
  - 10228 行付近で `uncertified_artifact_universe` と `verdict_freeze` を宣言へ追加。

- [test_codex_reasoning_ab.py:1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/orchestrator/tests/test_codex_reasoning_ab.py:1430)
  - `_full_manifest` の構築段だけ、module fixture の canonical oracle を `(resolved path, case)` memo に事前登録。
  - 未知 identity は実 verifier へ fallback。context 終了後の replay は実 verifier のまま。
  - 7601 行に `_load_adjudication` の `_artifact_path(manifest_path, manifest.get(KEY), ...)` を AST 導出する閉世界 node を追加。
  - 7702 行と 7819 行の既存 2 nodeへ cache 回数、共有 descriptor、2 reason exact assertionを追加。
  - 冒頭の変異対応表へ重複検出力を追記。

- [conftest.py:414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/orchestrator/tests/conftest.py:414)
  - 新規 2 node を `REAL_REPO_SERIAL_NODES` へ登録。

- [test_real_repo_serialization.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/orchestrator/tests/test_real_repo_serialization.py:107)
  - 同じ 2 node を独立 golden へ同順で登録。

`SCHEMA_VERSION=2`、既存 `failure_reasons`、`make_packets`、`_write_frozen_json` は変更していません。

## 実行時間の実測

変更前は親実測値です。

| node | 変更前 call | 変更後 |
|---|---:|---:|
| `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication` | 72.34 秒 | 実装済み・未実走 |
| `test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run` | 88.75 秒 | 実装済み・未実走 |
| 合計 | 161.09 秒 | 未実測 |

短縮内容は以下です。

- manifest 構築段のみ、既存 canonical oracle で memo を事前充填。
- replay 段は wrapper から本物の `verify_snapshot` を呼ぶ。
- 成功側 descriptor を case 内で共有し、実装 cache hit を利用。
- 静的な呼出し設計では、対象 2 node 合計の replay 実 verifier 呼出しは 9 回です。

計算ノードは `qstat -Q` が `NQSconnect: Can't create socket` で失敗し、runner child が一度も起動しなかったため、変更後の秒数と 30 秒以下は証明できていません。

## 走らせた検査

- 親の変更前実走: 対象 2 node、1 passed 相当の各 assertion、72.34 秒と 88.75 秒。
- 対象 2 nodeの計算ノード実走試行: rc=16、1 秒未満、child 未起動。
- F-1 の pytest 2 node実走試行: rc=16、1 秒未満、child 未起動。
- `test_certification_scope_closes_adjudication_descriptor_universe` と `test_material_report_certification_scope_is_exact_on_all_return_paths` の assertion 本体直接実行: rc=0、内部 0.228 秒。
- 許可 4 file の組込み `compile()` 構文検査: rc=0、0.6 秒。
- AST 静的検査: rc=0、0.9 秒。71 serial nodes、20 `benchmark_snapshots` consumer、二重正本完全一致、欠落 0、schema 2、旧 flag 0 件を確認。
- 初回 AST 診断スクリプト: rc=1、0.8 秒。`SCHEMA_VERSION` の alias 解決を診断側が扱わなかったためで、修正版は上記 rc=0。

洗い出した同型メタテストは、基盤障害によりすべて実装済み・未実走です。

- `test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_canonical_real_repo_nodes_have_no_handwritten_xdist_group_decorator`
- `test_receipt_memo_consumer_inventory_and_optouts_are_complete`
- `test_oracle_environment_consumer_inventory_and_registry_are_complete`
- `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
- `test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`
- `test_plain_runner_coverage.py` の file 集合メタテスト範囲

## 波及可能性

- 公開 `verify` / `aggregate` の `certification_scope` と直列化 bytes が変わるため、report 全体を exact 比較する所有外 caller に影響し得ます。
- `_full_manifest` は 3 caller。既存 end-to-end callerは既定値 `False` のままで、新規 2 nodeだけ短縮を有効化しています。
- `benchmark_snapshots` は静的に 20 direct consumers。全 consumer が serial registryに含まれることを AST で確認しました。
- `REAL_REPO_SERIAL_NODES` は collection marker、fixture closure、実行順、duration ledger、plain-runner coverage の consumer testへ波及し得ます。
- 射影外ファイルは読んでいないため、上記以外の所有外 consumer は未監査です。

## 守れなかったこと

- runner が失敗時に禁止対象の `output/pegasus-dispatch/` へ receipt を 2 回一時生成しました。生成された一意な 2 ディレクトリは除去済みで、再生成可能な診断だけでした。
- 直接 `py_compile` が許可外の `__pycache__` 4 fileを生成しました。該当 cache fileは除去済みです。
- 計算ノード障害により、変更後の対象 node、メタテスト、30 秒上限を実走確認できませんでした。
- commit、add、stash、checkout、merge、branch操作、docs編集は行っていません。

## 総括

F-1〜F-7 のコード修正は許可された 4 file内へ実装しました。  
宣言閉世界、直列台帳、cache回帰、2 reason、flag名、変異注記は静的に整合しています。  
ただし計算ノード child が未起動のため、F-1〜F-5は partialです。  
特に F-3 の変更後 30 秒以下は未証明であり、land前に対象 2 nodeと同型メタテストの実走が必要です。