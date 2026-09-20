## 実装と静的波及

所有 6 ファイルを実装しました。既存早期 memo テストの期待値、consumer registry、selected／hold／group／順序、L の同期経路は変更していません。docs 編集・commit・git 操作は行っていません。

静的に確認した波及先は次のとおりです。

- `_early_memo_selected`：本体の caller は `pytest_configure_node`。既存 parser test は configure を通らないため、環境に L token があっても従来の選択条件を使います。
- 実 `pytest_configure` の直接呼出し：追加テストと `test_pytest_collection_config.py`。
- `TASKS["tests"]`／allowlist：`test_pegasus_dispatch_compute.py`、`test_hold_inventory.py`、request を検査する `test_run_tests_preflight.py`、AST inventory を検査する `test_check_docs.py`。
- `hold_inventory`：既存の growth opt-in／PYTEST_ADDOPTS transport の検査を維持しています。

## 総括

変更ファイルと関数・定義：

| ファイル | 変更内容 |
|---|---|
| `orchestrator/tests/conftest.py` | 定数 3 個、`_early_memo_opted_out`、`_configure_early_memo_opt_out`、`_early_memo_selected`、`pytest_configure` |
| `tools/pegasus/dispatch_compute.py` | `TASKS["tests"].env_allowlist` に 1 key 追加 |
| `orchestrator/tests/test_real_repo_serialization.py` | `_early_memo_configure_probe` と `test_early_memo_opt_out_*` 4 関数。L の実 cache／reader、E unset・empty、UsageError と両 nonce 復元、属性経由を検査 |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | exact pin 更新、`test_early_memo_environment_request_and_child_overlay[token/empty]` 追加 |
| `probe-t2700/t2700_ab_analyze.py` | 入力検算、consumer AST 抽出、走・対集計、Wilcoxon／t／感度、失敗集計、記述的対照、JSON／Markdown 出力、selftest |
| `probe-t2700/t2700_history_estimate.py` | `number`、`distribution`、`extract`、`estimate`、`main` |

実走結果：

| 検査 | 結果 |
|---|---|
| `t2700_ab_analyze.py --selftest` | passed、rc=0。固定反例 5 件、合成走の各分類・取り直し・超過・未達・入力拒否、MC、出力生成を確認 |
| `--dump-consumers orchestrator/tests/conftest.py` | passed、rc=0。receipt 8、oracle 26 node を import せず抽出 |
| 履歴見積り `--e-limit 20` | passed、rc=0。5,487 stderr → 対象 197 shard → 適合 141 shard／130 session。除外 56 は `pytest_rc != 0` |
| Python 3.10 AST 構文検査 | 6 ファイル passed |
| pytest／関連 meta-test | **実走 nodeid なし。passed 0／failed 0、未起動** |

履歴成果物は [history.json](/tmp/t2700-history-author/history.json) と [history.md](/tmp/t2700-history-author/history.md) にあります。

E 経路は、未設定／空なら属性を置かず既存判定へ進むことを静的確認し、実 configure → 早期 job → cache のテストを追加しました。**動作テストは実装済み・未実走です。** 空文字は既存の `key in command_env` による採取で request に保持されますが、追加した伝播テストも未実走です。

既知の限界は、pytest・変異検査・実 A/B 成果物での解析が未実走なことです。また、親 launcher は receipt を SHA256SUMS に含めないため、receipt 自体の hash 保証はありません。集計器は receipt の job 番号と stderr 名を照合します。`run_tests.py` の試行で所有外の `output/pegasus-dispatch/20b273e01147bd5ea110b00d10d4b596/receipt.json` が自動生成されました。

実行制限：PreToolUse の `guard_bash` がログインノードでの直接 pytest を拒否しました。正規 runner 経由も `qstat -Q preflight rc=1` により rc=16、child 未起動で停止しました。これらを緑・closed とは扱っていません。