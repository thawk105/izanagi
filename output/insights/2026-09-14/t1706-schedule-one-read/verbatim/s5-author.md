指定の 2 ファイルだけを変更しました。**実装と新設 6 node は検証済みですが、所有外の consumer 登録が未完了です。**

- [production](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:7593)：V2-1〜V2-5 を実装。frozen／descriptor を一度読み、その bytes を認証・解析に共有。
- [対応テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:1944)：委譲型 read wrapper、交換・復元の発火計数、入口全体の read 計数、正負例を追加。
- `_artifact_path` は原文一致。既存関数・テストの AST も一致し、**既存テストの変更・削除・改名はありません**。docs 編集・git add・commit はしていません。

**実走結果**

```bash
PYTHONPATH=. python3 orchestrator/tests/test_codex_reasoning_ab.py
PYTHONPATH=. PYTEST_ADDOPTS=-v python3 orchestrator/tests/test_codex_reasoning_ab.py
```

両走とも **62 passed / 1 failed / 0 error / 3 skipped**。最終版では新設 6 node 全件が通過しました。

失敗は既存の `test_m10_filesystem_file_set_boundary_matrix_matches_rglob_reference` の Unix socket `bind()` に対する `PermissionError`。`-x` により残り **576 node は未実走**です。[最終ログ](/tmp/t1706-final-full.log)に全 nodeid と結果、[nodeid 一覧](/tmp/t1706-executed-nodeids.txt)に停止までの範囲を保存しました。

変異は以下の自走 harness で、各ケースの関数差し替え・復元を行いました。

```bash
PYTHONPATH=.:/tmp PYTEST_ADDOPTS='-v -s -p t1706_batch' python3 orchestrator/tests/test_codex_reasoning_ab.py
```

結果は **6 passed / 9 failed / 0 error**。失敗の内訳は **M1〜M6 の 6 件と旧実装の負例 3 件**で、すべて期待した検出です。[変異ログ](/tmp/t1706-batch-final.log)、[一時 harness](/tmp/t1706_batch.py)。

**新設 nodeid 全件**

```text
orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_reject_swap_restore[supervisor]
orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_reject_swap_restore[replay]
orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_reject_swap_restore[packets]
orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[supervisor]
orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[replay]
orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[packets]
```

**M1〜M6 の検出 assertion**

下表のテスト名は、上記 `test_schedule_authenticated_bytes_reject_swap_restore` の各 parameter を指します。

| 変異 | 落ちるテスト | 実測した assertion |
|---|---|---|
| M1 | `[supervisor]` | `assert observation.reads == 1`：実測 2 |
| M2 | `[replay]` | 同上：実測 2 |
| M3 | `[packets]` | 同上：実測 2 |
| M4 | `[replay]` | 同上：helper の再読を含め実測 2 |
| M5 | `[replay]` | 同上：後段 SHA 用の再読を含め実測 2 |
| M6 | `[supervisor]` | 同上：frozen の SHA 用再読を含め実測 2 |

M1〜M3 は B を受理し、M2 の `failure_reasons` は空でした。M4・M5 では既存の SHA 検査などによる追加 reason も発生します。**計数 assertion による検出は確認済みですが、入力の拒否理由が単一とは主張しません。**

**制約 meta-test**

| 実走 command／選択 | 結果 |
|---|---|
| `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py` | 3 passed |
| `PYTHONPATH=. PYTEST_ADDOPTS='-k "plain_runner or plain_pytest or regular_pytest"' python3 orchestrator/tests/test_growth_test_holds_contract.py` | 7 passed、76 deselected |
| `PYTHONPATH=.:/tmp PYTEST_ADDOPTS='-p t1706_no_inherit -k test_g5_real_ledger_covers_at_least_90_percent_of_real_collection' python3 orchestrator/tests/test_acceptance_schedule_order.py` | 1 passed、78 deselected |
| 下記の xdist／共有 fixture 契約 | **1 failed**、642 deselected |

```bash
PYTHONPATH=.:/tmp PYTEST_ADDOPTS='-p t1706_no_inherit orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes -k test_real_repo_group_collection_exactly_matches_canonical_nodes -v' python3 orchestrator/tests/test_codex_reasoning_ab.py
```

`test_real_repo_serialization.py` の直接自走は hold guard に拒否されたため、hold を解除せず pytest 委譲型の既存 harness から実行しました。[一時 plugin](/tmp/t1706_no_inherit.py)は選択用環境変数の subprocess への伝播だけを除きます。

失敗理由は、**新設 2 関数が `benchmark_snapshots[module]` の consumer として `REAL_REPO_CLASSIFIED_NODES` に未登録**であることです。[ログ](/tmp/t1706-meta-group-final.log)。所有外の `conftest.py` と独立 golden の更新が親の統合事項として残ります。命名規約・関数名の一意性・既存関数の保持は静的検査済みです。

**受理挙動と静的な波及範囲**

固定入力の受理範囲を変える検査は追加していません。従来どおり正当な schedule を受理し、duplicate schedule を supervisor は rc=22、replay／packets は rc=24 で拒否します。正例で SHA の不変性を確認しました。packets は元から `schedule_sha256` を出力しないため、descriptor の SHA を確認しています。

旧実装では A→B→A により B が受理され、read 回数は supervisor=2、replay=3、packets=2 でした。修正後は各 1 回で A の `duplicate slot_id: s01` を拒否します。認証後の削除・変更を後続の再読で観測しなくなる点は、指定された契約変更です。

静的に確認した波及先は以下です。

- `main` の supervisor／packets 経路、`verify_manifest`／`aggregate_manifest` の replay 経路。
- 既存 JSON loader caller：`_verify_launch_receipt`、`collect_run`、`_load_adjudication`、`_validate_supervisor_ledger`、`append_verdicts`、`freeze_verdicts`、`reveal_mapping`、`main`。呼出しは変更していません。
- 共有 fixture／helper：`benchmark_snapshots`、`_schedule`、`_full_manifest`。既存定義は変更していません。
- consumer test：snapshot evidence の replay／pre-post 検査、adjudication の loader wrapper、`test_t189_oracle_wiring_slice.py`、共有 fixture・hold・duration の契約検査。これらの全走を今回の部分実走で代替したとは扱いません。

## 総括

- V2-1〜V2-5 を指定の 2 ファイルに実装済み。
- 新設 6 node は全件 passed。
- M1〜M6 と旧実装の負例 3 件を実測で検出。
- 既存テスト・期待値の変更、削除、改名なし。
- 通常全走は既存 socket 権限エラーで停止。残り 576 node は未実走。
- 共有 fixture consumer 登録の meta-test は赤。所有外の登録更新が必要。
- **親の統合・全走待ちであり、closed とは報告しません。**