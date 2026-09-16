## 総括

**Python consumer 5 本を付け替えましたが、想定外のメタテスト赤 3 件により停止しました。closed ではありません。** 編集は所有する 7 file のみ。commit は作っていません。

B-4／S3 は hydrate → build に変更し、qualification／silo は staging root 配下を参照します。指定された検証処理・identity 対象集合・policy golden・歴史 binding は変更していません。

実走はすべて自走 harness です。以下の file nodeid は、そのファイルの全 node を表します。

| nodeid（`orchestrator/tests/` 配下） | 結果 |
|---|---|
| `test_b4_binary_record.py` | 21 passed、rc=0 |
| `test_silo_ladder_rung1_driver.py` | 91 passed、rc=0 |
| `test_silo_ladder_rung1_evidence.py` | 2 passed、rc=0 |
| `test_plain_runner_coverage.py` | 3 passed、rc=0 |
| `test_t126_pegasus_tools.py` | 276 中 110 passed を記録後、中断 rc=130 |
| `test_ccbench_spawn_sites.py` | 全走は中断 rc=130。下記 3 node の限定実走は rc=1 |

想定外の赤は、`orchestrator/tests/test_ccbench_spawn_sites.py::` 配下の次の 3 node です。

- `test_reviewed_process_launch_inventory_is_recursive_and_exact`：B-4 の subprocess 箇所数が期待 2／実際 1。
- `test_define_sink_cross_product_has_no_unreviewed_ungated_member`：build 呼出しが 127 → 118 行へ移動し、台帳との対応が外れる。
- `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`：同じ行番号固定により一致 0 件。

親指定の期待赤 5 file には含まれないため、**回帰として報告します**。期待値は変更していません。指定の期待赤 5 file 自体は未実走です。[診断ログ](/tmp/t548-c-spawn-findings.log)

削除した **test 関数は 0 件**。廃止命令に対応する B-4 の `verify-deps` パラメータケース 2 件は除去しました。

変更前は旧 locator を参照し、単位 A 適用後には旧 key／命令が欠落して失敗します。変更後は hydrate 済み source を参照します。既存の HEAD・dirty・symlink・commit/tree 検証ロジックは変わりません。新しい identity は変わり、過去成果物は変更していません。

静的な波及先は、qualification の `t126_driver.py`／`collector.py`、T-126 submit/job shell、共有 fixture `_attempt()`／`_submit_fixture()`、`test_ccbench_spawn_sites.py`、S3 consumer を検査する `test_mocc_proof_surface.py` です。

未完了は、上記メタテストとの整合、T-126 残り 166 node、新経路の実体による正例・負例検証です。既存 B-4 の spy テストを実調達の証明には数えていません。GitHub clone・実 build・計算ノード走行は**実装済み・未実走**です。