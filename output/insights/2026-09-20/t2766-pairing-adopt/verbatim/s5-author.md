## 変更前後の挙動

現行 X1 は旧 env が未設定・空なら従来順、exact token なら pairing を適用し、それ以外の非空値を拒否します。

変更後は旧 env を読まず pairing を既定で適用し、96 unit 未満の無変更・property 不在と、cardinality 不成立時の `pytest.UsageError` を維持します。

## 所有外への波及確認

- reorder の本番 caller は collection hook。テスト内の直接呼出し・G6/G10 tracer に加え、保存済み計測用 `output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py` に2引数 caller があります。既定付き署名を維持しています。
- `_OptionConfig`・scheduler harness・共有 fixture は変更していません。controller の `workerinput` 不在は `getattr(..., {})` で扱います。
- `TASKS["tests"]` の consumer は dispatch test、`test_hold_inventory.py`、`test_check_docs.py` に確認しました。hold inventory が検査する growth env・`PYTEST_ADDOPTS` は維持しています。
- dispatch 本体と対応テストは、primary checkout の同名ファイルと `cmp` で一致しました。指定 SHA 自体の照合は行っていません。

## 総括

**指定5ファイルの実装は完了しました。pytest は実装済み・未実走です。**

| 変更ファイル | 内容 |
|---|---|
| [conftest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-adopt-unit-impl/orchestrator/tests/conftest.py:1822) | env/token 定数と `_acceptance_pairing_opted_in` を削除。reorder の pairing 呼出しを無条件化し、collection hook を1呼出しに統合。pairing helper 本体・property 付与は維持 |
| [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-adopt-unit-impl/tools/pegasus/dispatch_compute.py:118) | `TASKS["tests"].env_allowlist` から旧 env を削除 |
| [test_acceptance_schedule_order.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-adopt-unit-impl/orchestrator/tests/test_acceptance_schedule_order.py:1169) | G6/G10 tracer の署名・引渡しを修正。G8、G12 を指定どおり変更 |
| [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-adopt-unit-impl/orchestrator/tests/test_pegasus_dispatch_compute.py:6260) | token 伝播テストを削除し、allowlist exact pin を戻した |
| [t2766_adopt_analyze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-adopt-unit-impl/probe-t2766-adopt/t2766_adopt_analyze.py) | 新規。`analyze_run`・`pair_runs`・`decision`・`analyze`・Markdown・CLI・`selftest` を採用 wave 用に改作。未ステージ |

G8 は **(b)** を採用しました。pairing helper を恒等関数に差し替え、元の「unknown は96位 known の直後」「空台帳では key 計算も置換もない」という assert を維持しています。cost 規則と pairing の検査を分けるためで、docstring に明記しました。

G12 は固定列 `_PAIRING_B_UNITS` を期待値とし、旧 env の4値でも順序・identity・selected・marker・既存 property・追加4 property を検査します。正例の対照 arm だけ恒等関数を使い、その用途をコメントしました。短 queue、cardinality 拒否、worker 数非依存、live JUnit、hold 保全、実配布の反例は残しています。G1〜G5・G7・G9・G11 の変更はありません。

検査結果：

| 実行範囲 | 結果 |
|---|---|
| 集計器 `--selftest` | **PASS 1、FAIL 0**。witness (1)〜(4)、A property 拒否、arm 別 tip 集合・更新、`main_moved`、判定全枝、compact 出力を検査 |
| 変更5ファイルの AST parse | **成功5、失敗0** |
| `test_acceptance_schedule_order.py`・`test_pegasus_dispatch_compute.py` 全件 | **未実走**。実走 nodeid なし、passed 0 / failed 0、収集前停止 |
| 関連メタテスト9ファイル | **未実走**。実走 nodeid なし、passed 0 / failed 0、収集前停止 |

メタテストとして runner に渡した範囲は `test_fold_gate_nodes_contract.py`、`test_hold_inventory.py`、`test_campaign_import_invariant.py`、`test_growth_test_holds_contract.py`、`test_flaky_test_holds_contract.py`、`test_pytest_collection_config.py`、`test_real_repo_serialization.py`、`test_run_tests_shards.py`、`test_run_tests_preflight.py` です。

残存参照検索では、本番 Python コードの旧 gate 関数・env/token 定数・旧 env 参照は **0件**でした。旧 env 名は要求された負例テストに1か所、さらに所有外の前 wave 保存資料に残っています。したがって **repo 全体で0件ではありません**。

既知の限界は、pytest・変異・実受入比較が未実走で、既存赤の有無も判定できていないことです。集計器は JUnit 出現順を復元し、全 worker の2個目が partner になるとは主張しません。docs 編集・commit・git 更新操作はしていません。runner は失敗 receipt を `output/pegasus-dispatch/` に自動生成しました。

指定の pytest 直接実行は PreToolUse hook が「Pegasus ログインノードでの pytest 起動」を理由に拒否しました。標準 runner による2回の実行も `qstat -Q preflight rc=1`、`child_started=false`、rc=16 で停止したため、テスト成功とは報告していません。