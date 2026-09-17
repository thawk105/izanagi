## 所見ごとの対応表

以下、`C` は [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-f976-f977-lock-notify-a1/orchestrator/tests/conftest.py)、`T` は [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-f976-f977-lock-notify-a1/orchestrator/tests/test_real_repo_serialization.py) を表します。

| 所見 | 対応 | 根拠 |
|---|---|---|
| A-1 | closed | C:1362。gate open・登録を SH 解放前へ移動。T:2183 の両 parameter が通過し、旧順序では両方赤化 |
| B-1 | closed | T:4452、4502。P2 の実時間 assert と `started` を削除、watchdog を 30.0 秒へ変更 |
| B-2 | closed | A-1 と同一修正・負例で検証 |
| B-nit | closed | T:1981、2053。説明を限定し、回収処理が例外でも pipe close が走る finally を追加 |
| 親-nit | closed | T:2247。deadline test の `with` を括弧付き複数行へ整形 |

## F1 の差分 (conftest と負例)

編集したファイルは指定された 2 ファイルだけです。

C:1362 の順序を次のとおり変更しました。

1. gate open・`state.gate_fd` 登録
2. cleanup の `try/finally` 内で、昇格なら main SH を解放
3. gate EX → main EX
4. gate 解放・close・`gate_fd = None`

T:2183 に `test_real_repo_gate_open_rejection_preserves_outer_reader[legacy/common]` を追加しました。外側 read 取得後に対象 gate を `0o644` にし、内側 write が `permissions are too broad` で拒否されることを検査します。

両 key について、例外後の state 同一性、`mode == "read"`、fd、holders、参照数 1、`gate_fd is None` を検査します。別 open description の EX が `BlockingIOError`、SH が成功することも確認します。

common 拒否の直前には legacy が write・参照数 2 に昇格済みであることを観測し、例外後には元の read・参照数 1 に戻ることを検査しました。この挙動は docstring に明記しています。

旧順序へ一時的に戻すと、両 parameter が T:2233 の **`DID NOT RAISE BlockingIOError`** で失敗しました。修正版へ復元済みです。

## F2 / N1 / N2 の差分

- **F2:** P2 の `started` と実時間 2 秒未満の assert を削除。テスト内 timeout は 30.0、retry は 0.002。競合観測、SH 解放 probe、入れ子 reader の gate 回避、mode・fd・参照数 2→1・最終 state 空の assert は維持しました。
- **N1:** `_gate_actor` の kill・5 秒 wait を `try` に、pipe close を別の `finally` に配置。docstring は正常応答の readiness に対する 35 秒 watchdog と回収手順に限定しました。
- **N2:** deadline test の複数 context manager を括弧付き複数行へ整形しました。

production の 245.0／0.05、gate 意味論、安全検査、取得順は変更していません。既存期待値の変更は指定された F2 の範囲のみです。

## 実走結果 (nodeid と結果、未実走の列挙)

指定コマンドを実走し、**33 passed、75 deselected、27.16 秒**でした。旧順序の赤化確認・復元後、同じ選択条件を `-vv` で再実走し、**33 passed、75 deselected、7.70 秒**でした。skip／error はありません。

以下の接頭辞はすべて `orchestrator/tests/test_real_repo_serialization.py::`。列挙した各 node は **PASSED** です。

```text
test_real_repo_writer_drains_overlapping_reader_stream[legacy]
test_real_repo_writer_drains_overlapping_reader_stream[common]
test_real_repo_upgrade_writer_drains_overlapping_reader_stream[legacy]
test_real_repo_upgrade_writer_drains_overlapping_reader_stream[common]
test_real_repo_readers_overlap_without_writer
test_real_repo_gate_timeout_closes_fds[gate-timeout]
test_real_repo_gate_timeout_closes_fds[main-timeout]
test_real_repo_gate_timeout_closes_fds[open-rejected]
test_real_repo_gate_open_rejection_preserves_outer_reader[legacy]
test_real_repo_gate_open_rejection_preserves_outer_reader[common]
test_real_repo_gate_and_main_share_deadline[writer]
test_real_repo_gate_and_main_share_deadline[reader]
test_real_repo_fork_reset_closes_inflight_gate_fd
test_real_repo_priority_order_is_literal_and_writers_follow_barrier
test_oracle_environment_memo_nonce_is_propagated_to_workers_and_restored
test_current_snapshot_reader_upgrades_for_same_process_candidate_fixture
test_real_repo_closure_mutations[t810-live-reader-unregistered]
test_real_repo_closure_mutations[invariant-candidate-write-downgraded]
test_real_repo_closure_mutations[predicate-candidate-lock-removed]
test_real_repo_closure_mutations[campaign-scan-lock-removed]
test_real_repo_closure_mutations[parent-key-uses-worktree-root]
test_real_repo_closure_mutations[legacy-key-not-acquired]
test_real_repo_closure_mutations[conflict-edge-removed]
test_real_repo_closure_mutations[prewarm-lock-removed]
test_real_repo_closure_mutations[nested-collection-node-unregistered]
test_memo_barrier_propagates_single_exception[collection_finish-RuntimeError-receipt]
test_memo_barrier_propagates_single_exception[collection_finish-RuntimeError-oracle]
test_memo_barrier_propagates_single_exception[collection_finish-SystemExit-receipt]
test_memo_barrier_propagates_single_exception[collection_finish-SystemExit-oracle]
test_memo_barrier_propagates_single_exception[xdist_node_collection_finished-RuntimeError-receipt]
test_memo_barrier_propagates_single_exception[xdist_node_collection_finished-RuntimeError-oracle]
test_memo_barrier_propagates_single_exception[xdist_node_collection_finished-SystemExit-receipt]
test_memo_barrier_propagates_single_exception[xdist_node_collection_finished-SystemExit-oracle]
```

旧順序の変異実走は、新設 `[legacy]`／`[common]` の **2 failed、106 deselected、2.04 秒、pytest rc=1**。修正版の復元後に上記 33 件が通過しています。

未実走：選択外 75 件、ファイル全走、所有外 consumer test、受入全走、`test_protocol_builder_repo_tree_guard_is_wired_to_real_root`、M0〜M6 の再変異実走。pipe cleanup の wait 例外注入テストも未実走です。

## 変異 anchor の更新

C の行数は変わらず、既存 anchor の行番号・逐語は維持されています。ただし昇格 UN は C:1367–1368 の gate fd 存在分岐内へ移りました。

| 変異 | 現在の `old` 候補 | killer node |
|---|---|---|
| M0 | C:1360 `# Writers hold the gate only while acquiring main; fresh readers` | 等価変異 |
| M1 | C:1491 `if not _REAL_REPO_PROCESS_LOCKS:` | writer drains 両 parameter |
| M2 | C:1362 `if target_mode == "write":` | writer drains 両 parameter、priority test |
| M3 | C:1362 `if target_mode == "write":` | upgrade writer drains 両 parameter、P2 |
| M4 | C:1378 の `state.fd,` に続く C:1379 `deadline=deadline,` | deadline 両 parameter |
| M5 | C:1387 `os.close(state.gate_fd)` | cleanup `[main-timeout]` |
| M6 | C:1491 `if not _REAL_REPO_PROCESS_LOCKS:` | P2 |

M2 の `and not created`、M3 の `and created` は、gate open を省くと `state.gate_fd is not None` 内の UN も省かれる構造です。今回の表は静的確認であり、前巡の M0〜M6 実測を今回の再実測とは扱っていません。

## 未完・懸念

本段の指定修正に未完はありません。README の保証範囲・common path 事前解決の注記は親担当として残しています。docs 編集・git コマンド実行はしていません。

静的に確認した波及先は次のとおりです。

- `_real_repo_locks`：receipt／oracle prewarm、timed locks、fixture context、protocol 登録 node、serialization／shards test。
- `_real_repo_file_lock`：`_real_repo_locks` と serialization test。
- `_RealRepoProcessLockState`：同 process 互換判定、取得・解放、fork reset、状態検査。
- `real_repo_fixture_lock`：preregistration invariant／predicates の candidate・snapshot fixture、campaign の `repository_scan` と各 consumer。
- `tools/acceptance_shards.py::record_real_repo_lock_interval`：呼出し・記録形式に変更なし。所有外テストの通過は未確認です。

修正前は、昇格時の gate open 拒否だけで外側 reader の SH が失われました。修正後は、拒否された key の SH を保持して例外を伝え、common 拒否時の legacy は既存の巻き戻し処理で read に戻ります。

gate 取得前の公平性と、SH 解放後の一般的な昇格 timeout の state 回復は、裁定どおり対象外です。

## 総括

**F1／F2／N1／N2 は修正済みです。** 新設負例は旧順序で両方赤化し、復元後の焦点走は **33 件通過**。指定 2 ファイルに修正を残しました。
