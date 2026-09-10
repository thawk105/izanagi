## 総括

**実装済み・未実走です。closed は申告しません。**

変更は所有2ファイルのみ、production **1行追加**、test **66行追加**です。

- PBS の `BOUND_PATHS` に `orchestrator/campaign/condition_meaning_gate.py` を追加しました。
- 既存契約領域に、独立 literal の5 pathそれぞれの unstaged/staged、clean、対象外 dirty を検証する局所 Bash／実 Git テストを追加しました。実 PBS から固定 anchor で検査部分を抽出し、exit code と後続 marker の到達を同時に検証します。配列一致 assert はありません。
- dirty 検査→blob/runtime 照合→probe 起動の順序契約も追加しました。既存 runtime spool テスト・期待値・fixture は変更していません。

編集前の静的確認では、shell は既存4 pathの dirty を拒否し、条件関門単独 dirty は通過する構造でした。今回の受理集合変更は指定された条件関門の拒否追加に限定しています。

`tools/run_tests.py` は修正前・修正後とも **qstat 事前確認失敗、rc=16、child_started=false** でした。実走した緑の node はありません。修正後に指定した範囲は `test_t316_sandbox_probe.py` と、静的調査で抽出した `test_pytest_collection_config.py`、`test_growth_test_holds_contract.py`、`test_acceptance_schedule_order.py`、`test_hooks.py` です。親 baseline 129 passed の代替ではありません。実機 PBS／benchmark／M1 も未実走です。`git diff --check` は成功しました。

所有外波及は、Python `_execution_binding`、PBS admission registry と `test_hooks.py`、収集・hold・duration ledger の consumer です。既存 helper の所有外 caller は検索で見つかりませんでした。追加15 nodeは ledger 未登録ですが、ledger は未知 node を扱う契約です。共有 fixture・所有外ファイルは変更していません。親 docs 依存の期待赤は **0件**です。

M1 の1行除去で挙動 assert が失敗する**期待 exact node 集合（未実測）**は以下の2件です。

```text
orchestrator/tests/test_t316_sandbox_probe.py::test_execution_binding_shell_dirty_gate[condition-unstaged]
orchestrator/tests/test_t316_sandbox_probe.py::test_execution_binding_shell_dirty_gate[condition-staged]
```

作業用ファイルは作成していません。runner が生成した退避対象は `output/pegasus-dispatch/{e59f1d4479f68c1c4cc68cd303c21190,3e8ef11c6b765b8ae742b49db38d248f}/receipt.json` です。commit・作業ツリーへの git add は行っていません。

なお、追加の構文確認コマンドは自動 PreToolUse hook に拒否されました。`bash -n` の対象 PBS が Pegasus の dispatch-required 実行体として判定されたためで、この構文確認も成功とは報告しません。